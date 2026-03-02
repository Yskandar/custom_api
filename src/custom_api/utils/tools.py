import os

from dotenv import load_dotenv


def get_default_llm_config(
    constants_path: str = "/home/yska/Projets/new_skills/module_1/custom_api/constants.env",
):

    load_dotenv(constants_path)
    config = {
        "model": os.environ.get("MODEL_NAME"),
        "base_url": os.environ.get("MODEL_ENDPOINT"),
    }

    return config
