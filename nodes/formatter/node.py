import csv
import os
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
        "Airline",
        "Flight Class",
        "Outbound Date",
        "Departure Airport",
        "Arrival Airport",
        "Return Date",
        "Return Airport",
        "Total Cost"
    ]

    with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)

        for flight in flight_results:
            # safely parse the outbound date and time
            dep_time_str = flight.get("departure_time", "N/A")
            if dep_time_str != "N/A":
                dep_time_str = " ".join(dep_time_str.split("T")[::-1])

            # safely parse the return date (if it's a one-way flight, this safely defaults to N/A)
            ret_time_str = flight.get("return_time", "N/A")
            if ret_time_str != "N/A":
                ret_time_str = " ".join(ret_time_str.split("T")[::-1])

            # build the row matching the schema
            row = [
                flight.get("airlines", "N/A"),
                flight.get("flight_class", "N/A"),
                dep_time_str,
                flight.get("departure_airport", "N/A"),
                flight.get("arrival_airport", "N/A"),
                ret_time_str,
                flight.get("return_airport", "N/A"),
                flight.get("price")
            ]

            writer.writerow(row)
        print("[Formatter Node] Formatting flight results into CSV...")