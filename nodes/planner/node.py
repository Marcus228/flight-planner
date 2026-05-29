from datetime import datetime, timedelta
from core.state import FlightAgentState


def generate_date_range(start_str: str, end_str: str) -> list[str]:
    """Helper function to expand a YYYY-MM-DD window into individual daily strings."""
    start_dt = datetime.strptime(start_str, "%Y-%m-%d")
    end_dt = datetime.strptime(end_str, "%Y-%m-%d")

    delta = (end_dt - start_dt).days
    return [(start_dt + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(delta + 1)]


def planner_node(state: FlightAgentState) -> dict:
    """
    Generates the complete set of valid API permutations.
    """
    params = state.get("parsed_parameters")
    if not params:
        raise ValueError("Planner node executed without parsed_parameters in the state.")

    origin = params["origin"]
    destination = params["destination"]
    airlines = params["airlines"]
    departure_dates = params["departure_window"]
    requested_class = params["flight_class"]

    # Optional fields should still use .get()
    ret_window = params.get("return_window")

    api_queries = []

    # permutation logic for round-trip
    if ret_window:
        return_dates = generate_date_range(ret_window["start_date"], ret_window["end_date"])

        for dep in departure_dates:
            for ret in return_dates:
                # chronological safety check
                if ret >= dep:
                    api_queries.append({
                        "origin": origin,
                        "destination": destination,
                        "departure_date": dep,
                        "return_date": ret,
                        "airlines": airlines,
                        "type": "round_trip",
                        "flight_class": requested_class
                    })

    # permutation logic for one-way
    else:
        for dep in departure_dates:
            api_queries.append({
                "origin": origin,
                "destination": destination,
                "departure_date": dep,
                "airlines": airlines,
                "type": "one_way",
                "flight_class": requested_class
            })

    print(f"[Planner Node] Generated the complete set of {len(api_queries)} API queries.")

    # return the list of API queries
    return {
        "api_queries": api_queries
    }