from custom_api.core.llm_handler import LangchainLLMHandler
from custom_api.utils.prompts import SENTIMENT_PROMPT, SUMMARIZE_PROMPT


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
