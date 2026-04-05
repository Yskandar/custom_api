import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from src.custom_api.api.users import (
    User,
    UserRequests,
    load_user_db,
    load_users_requests_db,
    update_user_db,
    update_users_requests_db,
)
from src.custom_api.core.text_processor import Task, TextProcessor, TreatedRequest
from src.custom_api.utils.tools import get_default_llm_config, initialize_environment

# Setup environment and retrieve important environment variables
initialize_environment()
SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES"))
MAX_REQ_PER_MIN = 5
USER_DB = load_user_db()
USERS_REQUESTS_DB = load_users_requests_db()

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
    if USER_DB.get(username):
        return User.model_validate_json(USER_DB.get(username))


def get_user_requests(username: str):
    if USERS_REQUESTS_DB.get(username):
        return UserRequests.model_validate_json(USERS_REQUESTS_DB.get(username))


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


def register_user_request(user: User, treated_request: TreatedRequest):
    """
    Register the treated request in the users_requests_db & update the database
    """

    global USERS_REQUESTS_DB
    user_requests = get_user_requests(user.username)
    if user_requests is None:
        USERS_REQUESTS_DB[user.username] = UserRequests.create_new_user_requests(
            user=user, tr=treated_request
        ).model_dump_json()
    else:
        user_requests.add_new_request(treated_request)
        USERS_REQUESTS_DB[user.username] = user_requests.model_dump_json()

    # Update the database accordingly
    update_users_requests_db(USERS_REQUESTS_DB)
    USERS_REQUESTS_DB = load_users_requests_db()


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

    # If user exists in the database, apply max request rate
    user_requests = get_user_requests(current_user.username)
    if user_requests is not None and not user_requests.is_request_allowed(
        max_req_per_min=MAX_REQ_PER_MIN
    ):
        raise HTTPException(
            status_code=400,
            detail="You are exceeding the max request rate. Try again later.",
        )

    reception_time = datetime.now()
    processor.perform_task(task)
    process_time = datetime.now() - reception_time

    if task.result is None:
        task.result = "Something wrong happened. Please try again later."

    elif task.result == "TIMEOUT":
        task.result = (
            "Timeout exceeded, LLM server is most probably busy. Try again later."
        )

    else:
        tr = TreatedRequest(
            treated_task=task,
            reception_timestamp=reception_time,
            process_time=process_time,
        )

        # Register user request
        register_user_request(user=current_user, treated_request=tr)

    return task
