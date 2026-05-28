from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

# fetch API keys
load_dotenv()

# returns a structured LLM compatible with LangChain technology
# choice of llm can be done by altering the imports and llm variable
# NOTE: the respective API key has to be present in .env file: LLM_API_KEY=YOUR_API_KEY_GOES_HERE
def get_structured_llm(schema, temperature: float = 0.0):
    """
    Centralized factory for instantiating the LLM and binding it to a schema.
    Easily hot-swappable for different models or providers.
    """
    # Fetch the LLM API key from .env
    custom_key = os.environ.get("LLM_API_KEY")

    if not custom_key:
        raise ValueError("CRITICAL: LLM_API_KEY environment variable is not set.")

    # Inject the key explicitly using the api_key parameter
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=temperature,
        api_key=custom_key
    )

    return llm.with_structured_output(schema, method="json_schema")