from typing import TypedDict, Optional, List, Dict, Any

# global state
class FlightAgentState(TypedDict):
    # Inputs
    user_input: str

    # Control State / Metadata
    retry_count: int
    error_message: Optional[str]

    # Outputs of Extractor Stage
    parsed_parameters: Optional[dict]

    # Outputs of the Planner stage
    api_queries: List[Dict[str, Any]]