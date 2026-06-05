from core.llm import get_structured_llm
from core.state import FlightAgentState
from core.config import MAX_EXTRACT_RETRIES
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

    # bind the LLM to the Pydantic schema
    structured_llm = get_structured_llm(FlightSearchIntent)

    try:
        extracted_object = structured_llm.invoke([
            ("system", system_prompt),
            ("human", user_prompt)
        ])
        print(f"Extracted: {extracted_object.model_dump()}")
        return {
            "parsed_parameters": extracted_object.model_dump(),
            "error_message": None,
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

    # happy path: Valid data generated, no errors
    if state.get("parsed_parameters") and not error_message:
        return "mcp_fetcher"

    # timeout guard: if errors persist past threshold, break execution hard
    if retry_count >= MAX_EXTRACT_RETRIES:
        raise TimeoutError(
            f"Agent Execution Halted: Extractor stuck in infinite correction loop. "
            f"Exceeded maximum threshold of {MAX_EXTRACT_RETRIES} attempts. "
            f"Final validation trace: {error_message}"
        )

    # feedback loop path: errors exist but budget remains -> route back to extractor
    print(f"Validation failure detected on attempt {retry_count}. Retrying Extraction...")
    return "extractor"