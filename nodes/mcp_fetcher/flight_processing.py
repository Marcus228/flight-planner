import ast
import asyncio
import json

from core.config import allowedAirlines


def extract_essential_flight_data(outward_flight_json: dict, return_flight_json: dict) -> dict:
    """Strips down the Google Flights JSON object into a lightweight dictionary."""
    try:
        outward_flights = outward_flight_json.get("flights", [])
        return_flights = return_flight_json.get("flights", [])

        if not outward_flights:
            return {}

        departure_leg = outward_flights[0]
        arrival_leg = outward_flights[-1]

        extracted_airlines = set()
        extracted_codes = []
        for flight in outward_flights + return_flights:
            extracted_airlines.add(flight["airline"])
            flight_number = flight.get("flight_number", "")
            extracted_codes.append(flight_number.split(" ")[0] if flight_number else "")


        flight_information = {
                "airlines": ",".join(extracted_airlines),
                "airline_codes": ",".join(c for c in extracted_codes if c),
                "departure_time": departure_leg.get("departure_airport", {}).get("time", "N/A"),
                "departure_airport": departure_leg.get("departure_airport", {}).get("name", "N/A"),
                "arrival_airport": arrival_leg.get("arrival_airport", {}).get("name", "N/A"),
                "flight_class": departure_leg.get("travel_class", "N/A"),
                "price": outward_flight_json.get("price"),
        }

        if return_flights:
            return_leg = return_flights[-1]
            flight_information.update({
                    "return_time": return_leg.get("arrival_airport", {}).get("time", "N/A"),
                    "return_airport": return_leg.get("arrival_airport", {}).get("name", "N/A"),
                })

        return flight_information
    except Exception:
        return {}

async def execute_single_flight_search(mcp_tool, query_params, semaphore: asyncio.Semaphore) -> list:
    """Executes outbound search, then fans out to fetch return flights per departure_token."""
    try:
        print("Entering execute_single_flight_search...")

        # first API call get outbound flights
        async with semaphore:
            outbound_response = await mcp_tool.ainvoke({"params": query_params})

        outbound_json = convert_tool_response_to_json(outbound_response)
        serpapi_response = json.loads(outbound_json[0].get("text", ""))

        all_outbound = filter_by_allowed_airlines(
            (serpapi_response.get("best_flights", []) or [])
            + (serpapi_response.get("other_flights", []) or [])
        )

        is_round_trip = "return_date" in query_params

        # one-way: no second call needed
        if not is_round_trip:
            return [
                extracted for flight in all_outbound
                if (extracted := extract_essential_flight_data(flight, {}))
            ]

        # round-trip: second call per outbound flight
        results = []
        for outbound_flight in all_outbound:
            departure_token = outbound_flight.get("departure_token")
            if not departure_token:
                continue

            return_query = {**query_params, "departure_token": departure_token}

            async with semaphore:
                return_response = await mcp_tool.ainvoke({"params": return_query})

            return_json = convert_tool_response_to_json(return_response)
            return_serpapi = json.loads(return_json[0].get("text", ""))

            all_return = filter_by_allowed_airlines(
                (return_serpapi.get("best_flights", []) or []) + (return_serpapi.get("other_flights", []) or [])
            )

            for return_flight in all_return:
                extracted = extract_essential_flight_data(outbound_flight, return_flight)
                if extracted:
                    results.append(extracted)

        return results

    except Exception as e:
        print(f"Query Failed for {query_params.get('outbound_date')}: {e}")
        return []

def convert_tool_response_to_json(tool_response):
    if isinstance(tool_response, str):
        tool_response = tool_response.strip()
        if tool_response.startswith('"') and tool_response.endswith('"'):
            tool_response = ast.literal_eval(tool_response)
        return json.loads(tool_response)
    else:
        return tool_response

def filter_by_allowed_airlines(flights: list) -> list:
    return [
        flight for flight in flights
        if any(
            # extracts the airline code
            flight_leg.get("flight_number", "").split(" ")[0] in allowedAirlines
            for flight_leg in flight.get("flights", [])
        )
    ]