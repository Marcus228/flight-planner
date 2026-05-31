import ast
import json

def extract_essential_flight_data(outward_flight_json: dict, return_flight_json: dict, requested_class: str) -> dict:
    """Strips down the Google Flights JSON object into a lightweight dictionary."""
    try:
        #  TODO outward_flight_json contains flights with changes, so return_leg is not necessarily 2nd element
        outward_flights = outward_flight_json.get("flights", [])
        return_flights = return_flight_json.get("flights", [])

        if not outward_flights:
            return {}

        departure_leg = outward_flights[0]
        arrival_leg = outward_flights[-1]

        extracted_airlines = []
        for flight in outward_flights:
            extracted_airlines.append(flight["airline"])
        flight_airlines = ",".join(extracted_airlines)

        return {
            "airlines": flight_airlines,
            "departure_airport": departure_leg.get("departure_airport", {}).get("name", "Unknown"),
            "arrival_airport": arrival_leg.get("arrival_airport", {}).get("name", "Unknown"),
            "departure_time": departure_leg.get("departure_airport", {}).get("time", "Unknown"),
            # TODO return date and airport are wrong. They must be explicitly injected
            "return_time": arrival_leg.get("arrival_airport", {}).get("time", "N/A"),
            "return_airport": arrival_leg.get("arrival_airport", {}).get("name", "N/A"),
            "duration": outward_flight_json.get("total_duration"),
            "price": outward_flight_json.get("price"),
            "flight_class": requested_class,
        }
    except Exception:
        return {}

async def execute_single_flight_search(mcp_tool, query_params, requested_class) -> list:
    """Executes a single MCP tool call, downloads the CDN payload, and extracts data."""
    try:
        print("Entering execute_single_flight_search...")
        # 1. Execute the LangChain-wrapped MCP tool directly
        tool_response = await mcp_tool.ainvoke({"params": query_params})

        # 2. Safely parse the response (handling stringified JSON)
        if isinstance(tool_response, str):
            tool_response = tool_response.strip()
            if tool_response.startswith('"') and tool_response.endswith('"'):
                tool_response = ast.literal_eval(tool_response)
            tool_data = json.loads(tool_response)
        else:
            tool_data = tool_response

        # 3. Check for CDN Endpoint
        serpapi_response = json.loads(tool_data[0].get("text", ""))
        all_flights = serpapi_response.get("best_flights", []) + serpapi_response.get("other_flights", [])

        # 5. Extract using highly optimized list comprehension (solves Issue 7)
        return [
            extracted for flight in all_flights
            if (extracted := extract_essential_flight_data(flight, requested_class))
        ]

    except Exception as e:
        print(f"Query Failed for {query_params.get('outbound_date')}: {e}")
        return []