from typing import TypedDict, Optional, List, Dict, Any

# global state
class FlightAgentState(TypedDict):
    # inputs
    user_input: str

    # control state / metadata
    retry_count: int
    error_message: Optional[str]

    # outputs of extractor node
    parsed_parameters: Optional[dict]

    # used locally in mcp_fetcher node
    api_queries: List[Dict[str, Any]]

    # outputs of the mcp_fetcher node
    flight_results: List[Dict[str, Any]]
