from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from src.custom_api.api.users import User, user_registry
from src.custom_api.core.text_processor import Task, TextProcessor
from src.custom_api.utils.tools import get_default_llm_config

app = FastAPI()
llm_config = get_default_llm_config()
processor = TextProcessor(llm_config)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def identify_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """
    Identify the user using the user registry
    """
    if user_registry.get(token):
        user = User.model_validate_json(user_registry.get(token))
    else:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    if user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    else:
        return user


def hash_user_info(username, userpassword):
    """
    Hash the username+password
    """

    return username + userpassword


@app.get("/")
def root():
    return {
        "message": "This API allows you to perform summarization or sentiment analyzis on a text."
    }


@app.post("/token")
def login(login_form: Annotated[OAuth2PasswordRequestForm, Depends()]):
    hash = hash_user_info(
        username=login_form.username, userpassword=login_form.password
    )
    if not user_registry.get(hash):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": hash, "token_type": "bearer"}


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
def summarize_text(text: str):
    return processor.text_summary(text=text)


@app.get("/text_processing/analyze/{text}")
def analyze_text(text: str):
    return processor.sentiment_analyzis(text=text)
