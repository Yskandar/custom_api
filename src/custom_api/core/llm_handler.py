from abc import ABC, abstractmethod

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

# Abstract class for llm handlers.


class LLMHandler(ABC):
    def __init__(self, config: dict):
        self.config = config
        print(config)
        self.client = self.create_client(**config)

    @abstractmethod
    def create_client(self, model: str, base_url: str, **completion_kwargs):
        pass

    @abstractmethod
    def generate_response(self, system_prompt: str, message: str, history: dict):
        pass


class LangchainLLMHandler(LLMHandler):
    """This class instantiates a langchain open-ai client"""

    def create_client(self, model: str, base_url: str, **completion_kwargs):

        # Create the client
        try:
            client = ChatOpenAI(
                model=model, base_url=base_url, api_key="lm-studio", **completion_kwargs
            )
        except Exception as e:
            print(f"Failed to create a Langchain OPENAI client: {e}")
            raise e

        # Return the client
        return client

    def generate_response(
        self,
        message: str,
        system_prompt: str = "Tu es un assistant expert.",
        history: list = [],
    ):
        """Generates the response using the langchain_openai client"""

        # Build messages
        system_prompt_msg = SystemMessage(content=system_prompt)
        user_message = HumanMessage(content=message)

        # Build message list
        messages = history + [system_prompt_msg, user_message]

        # Invoke client
        result = self.client.invoke(messages)

        return result.content
