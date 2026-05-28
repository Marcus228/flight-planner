from typing import TypedDict, Optional, List, Dict, Any

# global state
class FlightAgentState(TypedDict):
    # inputs
    user_input: str

    # control state / metadata
    retry_count: int
    error_message: Optional[str]

    # outputs of extractor stage
    parsed_parameters: Optional[dict]

    # outputs of the planner stage
    api_queries: List[Dict[str, Any]]

    # outputs of the fetcher stage
    flight_results: List[Dict[str, Any]]