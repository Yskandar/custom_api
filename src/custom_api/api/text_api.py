from fastapi import FastAPI

from src.custom_api.core.text_processor import Task, TextProcessor
from src.custom_api.utils.tools import get_default_llm_config

app = FastAPI()
llm_config = get_default_llm_config()
processor = TextProcessor(llm_config)


@app.get("/")
def root():
    return {
        "message": "This API allows you to perform summarization or sentiment analyzis on a text."
    }


@app.post("/text_processing/")
def perform_task(task: Task) -> Task:
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
