import csv
import os
from core.config import allowedAirlines
from core.state import FlightAgentState

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
# the OUTPUT_DIR assumes that the formatter is called in core directory.
OUTPUT_DIR = os.path.join(CURRENT_DIR, "..", "..", "output")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "flight_results.csv")

def formatter_node(state: FlightAgentState):
    """
    Takes the aggregated flight results from the Fetcher node and
    formats them into a clean, structured CSV file.
    """
    flight_results = state.get("flight_results", [])

    # check output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # define the schema
    headers = [
        "Airlines",
        "Outbound Date",
        "Departure Airport",
        "Arrival Airport",
        "Return Date",
        "Return Airport",
        "Flight Class",
        "Total Cost"
    ]

    with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)

        for flight in flight_results:
            flight_codes = {a.strip() for a in flight.get("airline_codes", "").split(",")}
            if not (flight_codes & set(allowedAirlines)):
                continue
            # parse the outbound date from the SerpApi departure_time string (e.g., "2026-06-01 10:00")
            dep_time_str = flight.get("departure_time", "")
            outbound_date = dep_time_str.split(" ")[0] if dep_time_str and dep_time_str != "N/A" else "N/A"

            # parse the return date (if it's a one-way flight, this safely defaults to N/A)
            ret_time_str = flight.get("return_time", "N/A")
            return_date = ret_time_str.split(" ")[0] if ret_time_str != "N/A" else "N/A"

            # format the price safely (handling None if the API dropped the price)
            price = flight.get("price")
            price_str = f"${price}" if price is not None else "N/A"

            # build the row matching the schema
            row = [
                flight.get("airlines", "N/A"),
                outbound_date,
                flight.get("departure_airport", "N/A"),
                flight.get("arrival_airport", "N/A"),
                return_date,
                flight.get("return_airport", "N/A"),
                flight.get("flight_class", "N/A"),
                price_str
            ]

            writer.writerow(row)
        print("[Formatter Node] Formatting flight results into CSV...")