import os
import asyncio
import httpx
from core.config import MAX_CONCURRENT_API_CALLS
from core.state import FlightAgentState
from nodes.mcp_fetcher.helpers import generate_queries
from nodes.mcp_fetcher.flight_processing import execute_single_flight_search

async def mcp_fetcher_node(state: FlightAgentState) -> dict:
    """
    Highly optimized programmatic fetcher. Replaces the LLM with
    upfront permutations and concurrent execution.
    """
    print("Entering mcp_fetcher_node...")

    params = state.get("parsed_parameters")
    if not params:
        raise ValueError("MCP Fetcher executed without parsed_parameters.")
    queries = generate_queries(params)

    print(f"[MCP Fetcher] Generated {len(queries)} exact permutations. Executing concurrently...")

    duffel_token = os.environ.get("DUFFEL_ACCESS_TOKEN")
    if not duffel_token:
        raise ValueError("DUFFEL_ACCESS_TOKEN not found in environment variables.")

    headers = {
        "Duffel-Version": "v2",
        "Authorization": f"Bearer {duffel_token}",
        "Content-Type": "application/json"
    }

    flight_results = []
    
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_API_CALLS)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [
            execute_single_flight_search(client, headers, q, semaphore)
            for q in queries
        ]
        batch_results = await asyncio.gather(*tasks)
        for result_list in batch_results:
            flight_results.extend(result_list)

    # deduplicate the flights
    seen = set()
    unique_results = []
    for flight in flight_results:
        key = (
            flight.get("airlines"),
            flight.get("departure_time"),
            flight.get("return_time"),
            flight.get("price")
        )
        if key not in seen:
            seen.add(key)
            unique_results.append(flight)

    sorted_results = sorted(unique_results, key=lambda x: x.get("airlines", "zzzzzz"))

    print(f"[MCP Fetcher] Programmatic execution complete. Extracted {len(sorted_results)} flights.")

    return {
        "flight_results": sorted_results
    }