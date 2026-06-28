from core.config import allowedAirlines
from datetime import datetime, timedelta

def generate_date_range(start_str: str, end_str: str) -> list[str]:
    """Helper function to expand a YYYY-MM-DD window into individual daily strings."""
    start_dt = datetime.strptime(start_str, "%Y-%m-%d")
    end_dt = datetime.strptime(end_str, "%Y-%m-%d")
    delta = (end_dt - start_dt).days
    return [(start_dt + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(delta + 1)]

def generate_queries(params: dict) -> list[dict]:
    origin = params["origin"]
    destination = params["destination"]

    dep_dates = generate_date_range(params["departure_window"]["start_date"], params["departure_window"]["end_date"])

    class_mapping = {
        "Economy": "economy",
        "Premium Economy": "premium_economy",
        "Business": "business",
        "First": "first"
    }
    cabin_class = class_mapping.get(params["flight_class"], "economy")

    queries = []
    if params.get("return_window"):
        ret_dates = generate_date_range(params["return_window"]["start_date"], params["return_window"]["end_date"])
        for dep in dep_dates:
            for ret in ret_dates:
                if ret >= dep:
                    queries.append({
                        "data": {
                            "cabin_class": cabin_class,
                            "passengers": [{"type": "adult"}],
                            "slices": [
                                {
                                    "origin": origin,
                                    "destination": destination,
                                    "departure_date": dep
                                },
                                {
                                    "origin": destination,
                                    "destination": origin,
                                    "departure_date": ret
                                }
                            ]
                        }
                    })
    else:
        for dep in dep_dates:
            queries.append({
                "data": {
                    "cabin_class": cabin_class,
                    "passengers": [{"type": "adult"}],
                    "slices": [
                        {
                            "origin": origin,
                            "destination": destination,
                            "departure_date": dep
                        }
                    ]
                }
            })
    return queries
