import asyncio
from core.config import MAX_CONCURRENT_API_CALLS
from core.state import FlightAgentState
from core.mcp_client import get_mcp_client
from langchain_mcp_adapters.tools import load_mcp_tools
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

    mcp_client = get_mcp_client()
    flight_results = []
    async with mcp_client.session("serpapi") as mcp_session:
        tools = await load_mcp_tools(mcp_session)
        search_tool = tools[0]  # assuming SerpApi flight search is the first tool based on the docs
        # API rate limiter. Necessary to ensure API provides requests back
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_API_CALLS)
        tasks = [
            execute_single_flight_search(search_tool, q, semaphore)
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