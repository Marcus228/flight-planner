from core.config import allowedAirlines
from datetime import datetime, timedelta


ROUND_TRIP = 1
ONE_WAY_TRIP = 2
NON_STOP_ONLY = 1

def generate_date_range(start_str: str, end_str: str) -> list[str]:
    """Helper function to expand a YYYY-MM-DD window into individual daily strings."""
    start_dt = datetime.strptime(start_str, "%Y-%m-%d")
    end_dt = datetime.strptime(end_str, "%Y-%m-%d")
    delta = (end_dt - start_dt).days
    return [(start_dt + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(delta + 1)]

def generate_queries(params: dict) -> list[str]:
    origin = params["origin"]
    destination = params["destination"]

    requested_airlines = ",".join(allowedAirlines)
    dep_dates = generate_date_range(params["departure_window"]["start_date"], params["departure_window"]["end_date"])

    class_mapping = {"Economy": 1, "Premium Economy": 2, "Business": 3, "First": 4}
    travel_class_num = class_mapping[params["flight_class"]]

    queries = []
    if params.get("return_window"):
        ret_dates = generate_date_range(params["return_window"]["start_date"], params["return_window"]["end_date"])
        for dep in dep_dates:
            for ret in ret_dates:
                if ret >= dep:  # chronology check
                    queries.append({
                        "departure_id": origin,
                        "arrival_id": destination,
                        "outbound_date": dep,
                        "return_date": ret,
                        "stops": NON_STOP_ONLY,
                        "include_airlines": requested_airlines,
                        "travel_class": travel_class_num,
                        "type" : ROUND_TRIP,
                        "engine": "google_flights"
                    })
    else:
        for dep in dep_dates:
            queries.append({
                "departure_id": origin,
                "arrival_id": destination,
                "outbound_date": dep,
                "stops": NON_STOP_ONLY,
                "include_airlines": requested_airlines,
                "travel_class": travel_class_num,
                "type": ONE_WAY_TRIP,
                "engine": "google_flights"
            })
    return queries

