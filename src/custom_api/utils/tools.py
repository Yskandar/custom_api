import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


current_dir = Path(__file__).parent
env_file = current_dir.parent.parent.parent / "constants.env"


def initialize_environment(
    constants_path: str = env_file,
):
    load_dotenv(constants_path)


def get_default_llm_config():
    config = {
        "model": os.environ.get("MODEL_NAME"),
        "base_url": os.environ.get("MODEL_ENDPOINT"),
    }

    return config
