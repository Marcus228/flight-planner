from typing import TypedDict, Optional

# global state
class FlightAgentState(TypedDict):
    # Inputs
    user_input: str

    # Control State / Metadata
    retry_count: int
    error_message: Optional[str]

    # Outputs of this stage
    parsed_parameters: Optional[dict]  # Will store FlightExtraction.model_dump()