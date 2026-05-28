from langchain_google_genai import ChatGoogleGenerativeAI

# returns a structured LLM compatible with LangChain technology
# choice of llm can be done by altering the imports and llm variable
# NOTE: the respective API key has to be present in .env file: LLM_API_KEY=YOUR_API_KEY_GOES_HERE
def get_structured_llm(schema, temperature: float = 0.0):
    """
    Centralized factory for instantiating the LLM and binding it to a schema.
    Easily hot-swappable for different models or providers.
    """
    # If you change models in the future, you only change this line
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=temperature)

    return llm.with_structured_output(schema, method="json_schema")