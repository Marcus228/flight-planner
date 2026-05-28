import os
import asyncio
import aiohttp
from core.state import FlightAgentState
from core.config import BATCH_SIZE
from dotenv import load_dotenv

# loading the environment variables.
load_dotenv()

# SerpApi Endpoint for Google Flights
SERPAPI_URL = "https://serpapi.com/search"

# determines how many top results to retrieve per API call
# 2 is recommended to ensure state is manageable
TOP_RESULTS = 2

def extract_essential_flight_data(pre_processed_flight: dict) -> dict:
    """
    Strips down the massive Google Flights JSON object into a lightweight dictionary
    to protect the LangGraph state memory constraints.
    """
    try:
        flights_info = pre_processed_flight.get("flights", [{}])[0]
        return {
            "airline": flights_info.get("airline", "Unknown"),
            "departure_airport": flights_info.get("departure_airport", {}).get("id", "Unknown"),
            "arrival_airport": flights_info.get("arrival_airport", {}).get("id", "Unknown"),
            "departure_time": flights_info.get("departure_airport", {}).get("time", "Unknown"),
            "arrival_time": flights_info.get("arrival_airport", {}).get("time", "Unknown"),
            "duration": pre_processed_flight.get("total_duration", 0),
            "price": pre_processed_flight.get("price", 0),
            "booking_token": pre_processed_flight.get("booking_token", "")
        }
    except Exception:
        return {}


async def fetch_single_query(session: aiohttp.ClientSession, query: dict, api_key: str) -> list:
    """Executes a single HTTP request to SerpApi."""
    # Map friendly internal strings to SerpApi's structural integers
    api_type = "1" if query.get("type") == "round_trip" else "2"

    params = {
        "engine": "google_flights",
        "departure_id": query["origin"],
        "arrival_id": query["destination"],
        "outbound_date": query["departure_date"],
        "type": api_type,  # Use integer strings '1' or '2'
        "currency": "USD",
        "hl": "en",
        "api_key": api_key
    }

    if query.get("type") == "round_trip" and "return_date" in query:
        params["return_date"] = query["return_date"]

    async with session.get(SERPAPI_URL, params=params) as response:
        if response.status != 200:
            # Print response text for debugging clear error explanations
            error_text = await response.text()
            print(f"API Error {response.status} for {query['departure_date']}: {error_text}")
            return []

        data = await response.json()
        best_flights = data.get("best_flights", [])
        cleaned_results = [extract_essential_flight_data(f) for f in best_flights[:2]]
        return [f for f in cleaned_results if f]


async def fetcher_node(state: FlightAgentState) -> dict:
    """
    Takes the planned API queries, batches them, executes them asynchronously,
    and returns the aggregated results.
    """
    api_queries = state.get("api_queries", [])
    if not api_queries:
        print("Warning: Fetcher node executed with an empty query list.")
        return {"flight_results": []}

    # get the API key from the .env file
    api_key = os.environ.get("SERPAPI_API_KEY")
    if not api_key:
        raise ValueError("CRITICAL: SERPAPI_API_KEY environment variable is not set.")

    all_results = []

    print(f"[Fetcher Node] Executing {len(api_queries)} queries in batches of {BATCH_SIZE}...")

    async with aiohttp.ClientSession() as session:
        for i in range(0, len(api_queries), BATCH_SIZE):
            batch = api_queries[i:i + BATCH_SIZE]

            # Create a list of asynchronous tasks for the current batch
            tasks = [fetch_single_query(session, query, api_key) for query in batch]

            # Execute them all simultaneously and wait for the batch to finish
            batch_results = await asyncio.gather(*tasks)

            # Flatten the list of lists into a single array
            for res_list in batch_results:
                all_results.extend(res_list)

            # Optional: Short sleep between batches to respect rate limits
            if i + BATCH_SIZE < len(api_queries):
                await asyncio.sleep(1.0)

    # Sort results purely by price before returning to state
    sorted_results = sorted(all_results, key=lambda x: x.get("price", float('inf')))

    print(f"[Fetcher Node] Successfully retrieved and cleaned {len(sorted_results)} flight options.")

    return {
        "flight_results": sorted_results
    }