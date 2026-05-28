from langchain_google_genai import ChatGoogleGenerativeAI

# returns a structured LLM compatible with LangChain technology
def get_structured_llm(schema, temperature: float = 0.0):
    """
    Centralized factory for instantiating the LLM and binding it to a schema.
    Easily hot-swappable for different models or providers.
    """
    # If you change models in the future, you only change this line
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=temperature)

    return llm.with_structured_output(schema, method="json_schema")