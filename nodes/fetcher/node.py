import os
import asyncio
import aiohttp
from core.state import FlightAgentState
from core.config import BATCH_SIZE
from dotenv import load_dotenv

# loading the environment variables.
load_dotenv()

# SerpApi endpoint for Google Flights
SERPAPI_URL = "https://serpapi.com/search"

# determines how many top results to retrieve per API call
# 2 is recommended to ensure state is manageable
TOP_RESULTS = 2

# flight classes specification as governed by the SerpAPI library
FLIGHT_CLASS_MAPPING: dict[str, int] = {
    "Economy": 1,
    "Premium Economy": 2,
    "Business": 3,
    "First": 4,
}

def extract_essential_flight_data(pre_processed_flight: dict, requested_class: str) -> dict:
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
            "duration": pre_processed_flight.get("total_duration"),
            "price": pre_processed_flight.get("price"),
            "booking_token": pre_processed_flight.get("booking_token", ""),
            "flight_class": requested_class,
        }
    except Exception:
        return {}

async def fetch_single_query(session: aiohttp.ClientSession, query: dict, api_key: str) -> list:
    """Executes a single HTTP request to SerpApi."""
    # map friendly internal strings to SerpApi's structural integers
    api_type = "1" if query.get("type") == "round_trip" else "2"

    requested_flight_class_str = query["flight_class"]
    requested_flight_class_id = FLIGHT_CLASS_MAPPING[requested_flight_class_str]

    params = {
        "engine": "google_flights",
        "departure_id": query["origin"],
        "arrival_id": query["destination"],
        "outbound_date": query["departure_date"],
        "type": api_type,
        "travel_class": requested_flight_class_id,
        "currency": "USD",
        "hl": "en",
        "api_key": api_key,
    }

    if query.get("type") == "round_trip" and "return_date" in query:
        params["return_date"] = query["return_date"]

    async with session.get(SERPAPI_URL, params=params) as response:
        if response.status != 200:
            # print response text for debugging clear error explanations
            error_text = await response.text()
            print(f"API Error {response.status} for {query['departure_date']}: {error_text}")
            return []

        data = await response.json()
        best_flights = data.get("best_flights", [])
        cleaned_results = [extract_essential_flight_data(f, requested_flight_class_str) for f in best_flights[:TOP_RESULTS]]
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

            # create a list of asynchronous tasks for the current batch
            tasks = [fetch_single_query(session, query, api_key) for query in batch]

            # execute tasks simultaneously and wait for the batch to finish
            batch_results = await asyncio.gather(*tasks)

            # flatten the list of lists into a single array
            for res_list in batch_results:
                all_results.extend(res_list)

            # short sleep between batches to respect rate limits
            if i + BATCH_SIZE < len(api_queries):
                await asyncio.sleep(1.0)

    # sort results by airline
    # the get defaults to zzzzz to place the unknown airlines last.
    sorted_results = sorted(all_results, key=lambda x: x.get("airline", "zzzzzz"))

    print(f"[Fetcher Node] Successfully retrieved and cleaned {len(sorted_results)} flight options.")

    return {
        "flight_results": sorted_results
    }