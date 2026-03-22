from typing import Literal

from pydantic import BaseModel, Field

from custom_api.core.llm_handler import LangchainLLMHandler
from custom_api.utils.prompts import SENTIMENT_PROMPT, SUMMARIZE_PROMPT


class Text(BaseModel):
    """
    Describes the text model
    """

    text_name: str = Field("default", description="the name of the text")
    content: str = Field(description="the content of the text")


class Task(BaseModel):
    """
    Task: the basetask + the text to process
    """

    text: Text = Field(description="the text object to process")
    task_name: Literal["summary", "sentiment"] = Field(
        "summary", description="The selected task"
    )


class TextProcessor:
    """
    This class creates helper function to adjust score the sentiment or resume a text.
    """

    def __init__(
        self,
        llm_config: dict,
        summarize_prompt: str = SUMMARIZE_PROMPT,
        sentiment_prompt: str = SENTIMENT_PROMPT,
    ):

        self.llm = LangchainLLMHandler(llm_config)
        self.summarize_prompt = summarize_prompt
        self.sentiment_prompt = sentiment_prompt

    def perform_task(self, task: Task):
        """
        Performs the demanded task
        """

        if task.task_name == "sentiment":
            return self.sentiment_analyzis(task.text.content)
        elif task.task_name == "summary":
            return self.text_summary(task.text.content)
        else:
            raise NotImplementedError(
                "Only the summary and sentiment tasks are supported"
            )

    def sentiment_analyzis(self, text: str):
        """
        Requests the LLM Client for a sentiment analyzis of the given text.
        """

        return self.llm.generate_response(
            message=text, system_prompt=self.sentiment_prompt
        )

    def text_summary(self, text: str):
        """
        Requests the LLM Client for a summary of the given text.
        """

        return self.llm.generate_response(
            message=text, system_prompt=self.summarize_prompt
        )
