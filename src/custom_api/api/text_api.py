import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from src.custom_api.api.users import User, load_user_db, update_user_db
from src.custom_api.core.text_processor import Task, TextProcessor
from src.custom_api.utils.tools import get_default_llm_config, initialize_environment

# Setup environment and retrieve important environment variables
initialize_environment()
SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES"))
USER_DB = load_user_db()

assert SECRET_KEY, "SECRET_KEY variable missing from constants.env"
assert ALGORITHM, "ALGORITHM variable missing from constants.env"
assert (
    ACCESS_TOKEN_EXPIRE_MINUTES
), "ACCESS_TOKEN_EXPIRE_MINUTES variable missing from constants.env"


app = FastAPI()
llm_config = get_default_llm_config()
processor = TextProcessor(llm_config)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
password_hash = PasswordHash.recommended()


def identify_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """
    Identify the user using the user registry
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        decoded_json = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = decoded_json.get("sub")
        exp_date = datetime.strptime(
            decoded_json.get("exp_date"), "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=timezone.utc)

        if username is None:
            raise credentials_exception

        if datetime.now(timezone.utc) > exp_date:
            raise HTTPException(
                status_code=400, detail="Expired token, please login again"
            )

    except InvalidTokenError:
        raise credentials_exception

    user = get_user(username=username)

    if user is None:
        raise HTTPException(status_code=400, detail="User does not exist")
    elif user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    else:
        return user


def create_access_token(data: dict, expire_delay: timedelta | None = None):
    """
    This function creates a JSON Web Token from the input JSON data
    """

    copied_data = data.copy()
    if expire_delay:
        expiration_date = datetime.now(timezone.utc) + expire_delay
    else:
        expiration_date = datetime.now(timezone.utc) + timedelta(minutes=15)

    # Integrate the expiration date in the json data
    copied_data.update({"exp_date": expiration_date.strftime("%Y-%m-%d %H:%M:%S")})

    # Encode
    encoded_jwt = jwt.encode(copied_data, key=SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def hash_user_password(userpassword: str):
    """
    Hash the password
    """
    return password_hash.hash(userpassword)


def get_user(username: str):
    return User.model_validate_json(USER_DB.get(username))


def create_user(username: str, userpassword: str):
    """
    Create a User object and register it in the user_db
    """
    global USER_DB

    if USER_DB.get(username) is not None:
        raise HTTPException(status_code=400, detail="User already exists")
    else:
        user = User(username=username, hashed_password=hash_user_password(userpassword))
        update_user_db(user_db=USER_DB, user=user)
        USER_DB = load_user_db()


def authenticate_user(username: str, userpassword: str):
    """
    Authenticates the user in the user_registry using username and password
    """

    if not USER_DB.get(username):
        print("User does not exist, creating user with provided username & password")
        create_user(username, userpassword)

    user = get_user(username=username)

    if password_hash.verify(userpassword, user.hashed_password):
        return user
    else:
        raise HTTPException(status_code=401, detail="Wrond username or password")


@app.get("/")
def root():
    return {
        "message": "This API allows you to perform summarization or sentiment analyzis on a text."
    }


@app.post("/token")
def login(login_form: Annotated[OAuth2PasswordRequestForm, Depends()]):

    user = authenticate_user(
        username=login_form.username, userpassword=login_form.password
    )

    if user.disabled:
        raise HTTPException(status_code=400, detail="Disabled User")

    # Create access token once user is authenticated
    exp_delay = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expire_delay=exp_delay
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me")
def get_current_user(current_user: Annotated[User, Depends(identify_user)]):
    return current_user


@app.post("/text_processing/")
def perform_task(
    task: Task, current_user: Annotated[User, Depends(identify_user)]
) -> Task:
    processor.perform_task(task)

    if task.result is None:
        task.result = "Something wrong happened. Please try again later."

    elif task.result == "TIMEOUT":
        task.result = (
            "Timeout exceeded, LLM server is most probably busy. Try again later."
        )

    return task


@app.get("/text_processing/summarize/{text}")
def summarize_text(text: str, current_user: Annotated[User, Depends(identify_user)]):
    return processor.text_summary(text=text)


@app.get("/text_processing/analyze/{text}")
def analyze_text(text: str, current_user: Annotated[User, Depends(identify_user)]):
    return processor.sentiment_analyzis(text=text)
