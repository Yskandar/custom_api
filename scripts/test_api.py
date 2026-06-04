import json
import os
import time

import requests
from dotenv import load_dotenv

from custom_api.api.tasks import TaskRecord

if __name__ == "__main__":

    # Load environment variables
    load_dotenv("constants.env")

    # Load config
    config = {
        "model": os.environ.get("MODEL_NAME"),
        "base_url": os.environ.get("MODEL_ENDPOINT"),
        "model_kwargs": {"chat_template_kwargs": {"enable_thinking": False}},
    }

    # Acquire access token
    print("Logging...")
    token_url = "http://127.0.0.1:8000/token"
    user = os.environ.get("USERNAME")
    password = os.environ.get("PASSWORD")

    login_form = {
        "username": user,
        "password": password,
    }

    res = requests.post(token_url, login_form)
    content = json.loads(res.content.decode("utf-8"))
    access_token = content["access_token"]

    auth_header = {"Authorization": f"Bearer {access_token}"}

    # Build example
    example_path = "research/examples/example_text.md"

    with open(example_path, encoding="utf-8") as f:
        text = f.read()

    request_body = {
        "text": {"text_name": "Tech News", "content": f"{text}"},
        "task_name": "summary",
    }

    # posting request
    print("Sending the request...")
    query_url = "http://127.0.0.1:8000/tasks"
    response = requests.post(query_url, json=request_body, headers=auth_header).content

    resp_dict = json.loads(response.decode("utf-8"))
    task_id = resp_dict["task_id"]
    print(f"The following task id was sent by the API: {task_id}")

    # Retrieving the result
    print("Waiting for the result...")
    time.sleep(10)
    task_url = f"http://127.0.0.1:8000/tasks/{task_id}"
    response = requests.get(task_url, headers=auth_header).content
    decoded_response = json.loads(response.decode("utf-8"))

    try:
        tr = TaskRecord.model_validate_json(response)
        print("For the given task_id, we got the following result: \n")
        print(tr.task.result)

    except Exception:
        print("Something went wrong. \n")
        print("API response: \n")
        print(decoded_response)
