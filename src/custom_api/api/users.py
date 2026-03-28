import json
from pathlib import Path

from pydantic import BaseModel


class User(BaseModel):
    username: str
    hashed_password: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


current_dir = Path(__file__).parent
JSON_PATH = current_dir / "users.json"


def initialize_json():
    with open(JSON_PATH, "x") as f:
        json.dump({}, f)


def load_user_db() -> dict:

    try:
        with open(JSON_PATH, "r") as f:
            user_db = json.load(f)
    except OSError:
        initialize_json()
        with open(JSON_PATH, "r") as f:
            user_db = json.load(f)

    return user_db


def update_user_db(user_db: dict, user: User):
    user_db[user.username] = user.model_dump_json()

    with open(JSON_PATH, "w") as f:
        json.dump(user_db, f)
