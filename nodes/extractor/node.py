# model of choice
from langchain_google_genai import ChatGoogleGenerativeAI
# some crucial imports
from core.state import FlightAgentState
from core.config import MAX_EXTRACT_RETRIES
# this TypedDict is the binder of the node
from nodes.extractor.schema import FlightSearchIntent


def extractor_node(state: FlightAgentState) -> dict:
    """
    Executes a single stochastic extraction pass.
    """
    user_input = state["user_input"]
    error_message = state.get("error_message")
    retry_count = state.get("retry_count", 0)

    system_prompt = (
        "You are a strict data extraction engine. Analyze the user flight request "
        "and map it exactly to the provided JSON schema. Ensure dates are parsed "
        "as strict YYYY-MM-DD windows."
    )

    if error_message:
        user_prompt = (
            f"Your previous attempt failed validation.\n"
            f"Original User Intent: '{user_input}'\n"
            f"Validation Error Encountered: {error_message}\n"
            f"Analyze the error, correct your structural or logical mistakes, and output a valid structure."
        )
    else:
        user_prompt = f"User Input Request: '{user_input}'"

    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.0)

    # Bind the LLM to the Pydantic schema
    structured_llm = llm.with_structured_output(FlightSearchIntent, method="json_schema")

    try:
        extracted_object = structured_llm.invoke([
            ("system", system_prompt),
            ("human", user_prompt)
        ])

        return {
            "parsed_parameters": extracted_object.model_dump(),
            "error_message": None,  # Clear prior errors
            "retry_count": retry_count + 1
        }

    except Exception as validation_exception:
        return {
            "parsed_parameters": None,
            "error_message": str(validation_exception),
            "retry_count": retry_count + 1
        }

# feedback loop
def route_after_extraction(state: FlightAgentState) -> str:
    retry_count = state.get("retry_count", 0)
    error_message = state.get("error_message")

    # Happy Path: Valid data generated, no errors
    if state.get("parsed_parameters") and not error_message:
        return "planner"

    # Timeout Guard: If errors persist past threshold, break execution hard
    if retry_count >= MAX_EXTRACT_RETRIES:
        raise TimeoutError(
            f"Agent Execution Halted: Extractor stuck in infinite correction loop. "
            f"Exceeded maximum threshold of {MAX_EXTRACT_RETRIES} attempts. "
            f"Final validation trace: {error_message}"
        )

    # Feedback Loop Path: Errors exist but budget remains. Route back to extractor
    print(f"⚠️ Validation failure detected on attempt {retry_count}. Retrying Extraction...")
    return "extractor"