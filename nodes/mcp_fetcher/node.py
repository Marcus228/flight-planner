import ast
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
from core.state import FlightAgentState
from core.mcp_client import get_mcp_client
from langchain_mcp_adapters.tools import load_mcp_tools


def extract_essential_flight_data(pre_processed_flight: dict, requested_class: str) -> dict:
    """Strips down the Google Flights JSON object into a lightweight dictionary."""
    try:
        flights = pre_processed_flight.get("flights", [])
        outbound = flights[0] if len(flights) > 0 else {}
        return_leg = flights[1] if len(flights) > 1 else {}

        return {
            "airline": outbound.get("airline", "Unknown"),
            "departure_airport": outbound.get("departure_airport", {}).get("name", "Unknown"),
            "arrival_airport": outbound.get("arrival_airport", {}).get("name", "Unknown"),
            "departure_time": outbound.get("departure_airport", {}).get("time", "Unknown"),
            "return_time": return_leg.get("departure_airport", {}).get("time", "N/A"),
            "return_airport": return_leg.get("departure_airport", {}).get("name", "N/A"),
            "duration": pre_processed_flight.get("total_duration"),
            "price": pre_processed_flight.get("price"),
            "flight_class": requested_class,
        }
    except Exception:
        return {}


def generate_date_range(start_str: str, end_str: str) -> list[str]:
    """Helper function to expand a YYYY-MM-DD window into individual daily strings."""
    start_dt = datetime.strptime(start_str, "%Y-%m-%d")
    end_dt = datetime.strptime(end_str, "%Y-%m-%d")
    delta = (end_dt - start_dt).days
    return [(start_dt + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(delta + 1)]


async def execute_single_flight_search(mcp_tool, aio_session, query_params, requested_class) -> list:
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
        best_flights = serpapi_response.get("best_flights")

        # 5. Extract using highly optimized list comprehension (solves Issue 7)
        return [
            extracted for f in best_flights
            if (extracted := extract_essential_flight_data(f, requested_class))
        ]

    except Exception as e:
        print(f"⚠️ Query Failed for {query_params.get('outbound_date')}: {e}")
        return []


async def mcp_fetcher_node(state: FlightAgentState) -> dict:
    """
    Highly optimized programmatic fetcher. Replaces the LLM with
    upfront permutations and concurrent execution.
    """
    print("Entering mcp_fetcher_node...")
    params = state.get("parsed_parameters")
    if not params:
        raise ValueError("MCP Fetcher executed without parsed_parameters.")
    # Generate Permutations (Solves Issue 4)
    origin = params["origin"]
    destination = params["destination"]

    requested_class = params["flight_class"]
    dep_dates = generate_date_range(params["departure_window"]["start_date"], params["departure_window"]["end_date"])

    queries = []
    if params.get("return_window"):
        ret_dates = generate_date_range(params["return_window"]["start_date"], params["return_window"]["end_date"])
        for dep in dep_dates:
            for ret in ret_dates:
                if ret >= dep:  # Chronology check
                    queries.append({
                        "departure_id": origin, "arrival_id": destination,
                        "outbound_date": dep, "return_date": ret,
                        "engine": "google_flights"
                    })
    else:
        for dep in dep_dates:
            queries.append({
                "departure_id": origin, "arrival_id": destination,
                "outbound_date": dep, "engine": "google_flights"
            })

    print(f"[MCP Fetcher] Generated {len(queries)} exact permutations. Executing concurrently...")

    mcp_client = get_mcp_client()
    flight_results = []

    # Connect to MCP server
    async with mcp_client.session("serpapi") as mcp_session:
        tools = await load_mcp_tools(mcp_session)
        search_tool = tools[0]  # Assuming SerpApi flight search is the first tool

        # Solves Issue 5 & 6: Single shared aiohttp session, concurrent execution
        async with aiohttp.ClientSession() as aio_session:
            # Create a list of asynchronous tasks
            tasks = [
                execute_single_flight_search(search_tool, aio_session, q, requested_class)
                for q in queries
            ]

            # Execute all tasks in parallel
            batch_results = await asyncio.gather(*tasks)

            # Flatten the results
            for result_list in batch_results:
                flight_results.extend(result_list)

    # Sort results by airline
    sorted_results = sorted(flight_results, key=lambda x: x.get("airline", "zzzzzz"))

    print(f"[MCP Fetcher] Programmatic execution complete. Extracted {len(sorted_results)} flights.")

    return {
        "flight_results": sorted_results
    }