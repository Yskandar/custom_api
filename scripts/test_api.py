import requests

if __name__ == "__main__":

    example_path = "research/examples/example_text.md"

    with open(example_path, encoding="utf-8") as f:
        query = f.read()

    query_url = f"http://127.0.0.1:8000/text_processing/summarize/{query}"

    print("Sending API request...")
    content = requests.get(query_url).content.decode("utf-8")

    print("Here is the API response: ")
    print(content)
