import csv
import os
from core.state import FlightAgentState

# define the output directory and filename
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
# the OUTPUT_DIR assumes that the formatter is called in core directory.
OUTPUT_DIR = os.path.join(CURRENT_DIR, "..", "..", "output")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "flight_results.csv")


def formatter_node(state: FlightAgentState) -> dict:
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
        "Outbound Date",
        "Departure Airport",
        "Arrival Airport",
        "Return Date",
        "Return Airport",
        "Flight Class",
        "Total Cost"
    ]

    print(f"[Formatter Node] Formatting {len(flight_results)} flights into CSV...")

    with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)

        for flight in flight_results:
            # parse the outbound date from the SerpApi departure_time string (e.g., "2026-06-01 10:00")
            dep_time_str = flight.get("departure_time", "")
            outbound_date = dep_time_str.split(" ")[0] if dep_time_str and dep_time_str != "Unknown" else "Unknown"

            # parse the return date (if it's a one-way flight, this safely defaults to N/A)
            ret_time_str = flight.get("return_time", "N/A")
            return_date = ret_time_str.split(" ")[0] if ret_time_str != "N/A" else "N/A"

            # format the price safely (handling None if the API dropped the price)
            price = flight.get("price")
            price_str = f"${price}" if price is not None else "Unknown"

            # build the row matching the schema
            row = [
                flight.get("airline", "Unknown"),  # 1. Airline
                outbound_date,  # 2. Outbound Date
                flight.get("departure_airport", "Unknown"),  # 3. Departure Airport
                flight.get("arrival_airport", "Unknown"),  # 4. Arrival Airport
                return_date,  # 5. Return Date
                flight.get("return_airport", "N/A"),  # 6. Return Airport
                flight.get("flight_class", "Unknown"),  # 7. Flight Class
                price_str  # 8. Total Cost
            ]

            writer.writerow(row)

    print(f"[Formatter Node] Successfully saved results to {OUTPUT_FILE}")

    # return the file path to the state so the graph knows where the final output lives
    return {
        "csv_file_path": OUTPUT_FILE
    }