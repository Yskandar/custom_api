import requests

from custom_api.core.text_processor import Task

if __name__ == "__main__":

    example_path = "research/examples/example_text.md"

    with open(example_path, encoding="utf-8") as f:
        text = f.read()

    request_body = {
        "text": {"text_name": "Tech News", "content": f"{text}"},
        "task_name": "summary",
    }

    query_url = "http://127.0.0.1:8000/text_processing"

    print("Sending API request...")
    content = requests.post(query_url, json=request_body).content.decode("utf-8")
    task = Task.model_validate_json(content)

    print("Here is the API response: ")
    print(content)

    print("Recovered python object:")
    print(task)
