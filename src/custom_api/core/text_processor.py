import threading
from typing import Union

from custom_api.api.tasks import Task
from custom_api.core.llm_handler import LangchainLLMHandler
from custom_api.utils.prompts import SENTIMENT_PROMPT, SUMMARIZE_PROMPT


class TextProcessor:
    """
    This class creates helper function to score the sentiment or resume a text.
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
            method = self.sentiment_analyzis
        elif task.task_name == "summary":
            method = self.text_summary

        else:
            raise NotImplementedError(
                "Only the summary and sentiment tasks are supported"
            )

        thread = threading.Thread(target=method, kwargs={"text": task})

        thread.start()
        thread.join(timeout=10)
        if thread.is_alive():
            task.result = "TIMEOUT"

    def sentiment_analyzis(self, text: Union[Task, str]):
        """
        Requests the LLM Client for a sentiment analyzis of the given text.
        """

        if isinstance(text, Task):
            text.result = self.llm.generate_response(
                message=text.text.content, system_prompt=self.sentiment_prompt
            )

        else:

            return self.llm.generate_response(
                message=text, system_prompt=self.sentiment_prompt
            )

    def text_summary(self, text: Union[Task, str]):
        """
        Requests the LLM Client for a summary of the given text.
        """

        if isinstance(text, Task):
            text.result = self.llm.generate_response(
                message=text.text.content, system_prompt=self.summarize_prompt
            )

        else:

            return self.llm.generate_response(
                message=text, system_prompt=self.summarize_prompt
            )
