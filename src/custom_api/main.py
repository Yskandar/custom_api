# The launch script for the application. It initializes the application and starts the main loop.
import os

from dotenv import load_dotenv

from custom_api.core.llm_handler import LangchainLLMHandler

if __name__ == "__main__":
    load_dotenv("/home/yska/Projets/new_skills/module_1/custom_api/constants.env")

    config = {
        "model": os.environ.get("MODEL_NAME"),
        "base_url": os.environ.get("MODEL_ENDPOINT"),
    }
    # Create handler
    langchain_client = LangchainLLMHandler(config)

    # Simple query
    query = "Que sais-tu faire ?"
    answer = langchain_client.generate_response(message=query)
    print(answer)
