import os
import json
import aiohttp

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.tools import load_mcp_tools
from core.state import FlightAgentState
from core.mcp_client import get_mcp_client


def extract_essential_flight_data(pre_processed_flight: dict, requested_class: str) -> dict:
    """Strips down the Google Flights JSON object into a lightweight dictionary."""
    try:
        flights = pre_processed_flight.get("flights", [])
        outbound = flights[0] if len(flights) > 0 else {}
        return_leg = flights[1] if len(flights) > 1 else {}

        return {
            "airline": outbound.get("airline", "Unknown"),
            "departure_airport": outbound.get("departure_airport", {}).get("id", "Unknown"),
            "arrival_airport": outbound.get("arrival_airport", {}).get("id", "Unknown"),
            "departure_time": outbound.get("departure_airport", {}).get("time", "Unknown"),
            "return_time": return_leg.get("departure_airport", {}).get("time", "N/A"),
            "return_airport": return_leg.get("departure_airport", {}).get("id", "N/A"),
            "duration": pre_processed_flight.get("total_duration"),
            "price": pre_processed_flight.get("price"),
            "flight_class": requested_class,
        }
    except Exception:
        return {}


async def mcp_fetcher_node(state: FlightAgentState) -> dict:
    """
    Acts as an autonomous sub-agent. Loads tools via MCP,
    calculates permutations internally, and executes the queries.
    """

    print(state.get("parsed_parameters"))

    params = state.get("parsed_parameters")
    if not params:
        raise ValueError("MCP Fetcher executed without parsed_parameters.")

    print("[MCP Fetcher] Connecting to remote MCP server and loading tools...")
    mcp_client = get_mcp_client()

    async with mcp_client.session("serpapi") as session:
        # the adapter automatically converts MCP tools into LangChain-compatible tools
        tools = await load_mcp_tools(session)

        print(f"[MCP Fetcher] Loaded {len(tools)} tools. Delegating to Agent...")

        # initialize the LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash",
            temperature=0,
            api_key=os.environ.get("LLM_API_KEY")
        )

        # use LangGraph's prebuilt ReAct agent to handle the tool execution loop
        agent_executor = create_agent(llm, tools)

        agent_prompt = f"""
        You are an autonomous flight fetching agent. Use the available flight search tool 
        to retrieve flight data based on these user parameters:
    
        {json.dumps(params, indent=2)}
    
        1. Identify all exact departure dates within the departure_window.
        2. Identify all exact return dates within the return_window (if applicable).
        3. Execute the tool for EVERY valid combination of those dates.
        4. Once you have successfully called the tool for all required dates, reply "Task Complete".
        """

        # Run the prebuilt agent
        agent_response = await agent_executor.ainvoke({"messages": [("user", agent_prompt)]})

    flight_results = []
    requested_class = params.get("flight_class", "Economy")


    # The agent stored the raw API JSON responses inside its message history.
    # We loop through to extract them and pass them into your existing formatter logic.
    for message in agent_response["messages"]:

        if message.type == "ai":
            if message.content:
                print(f"\n[AI Reasoning]: {message.content}")
            if hasattr(message, "tool_calls") and message.tool_calls:
                print(f"\n[AI Calling Tool]: {json.dumps(message.tool_calls, indent=2)}")
        if message.type == "tool":
            print(f"\n[Tool Response Raw]: {str(message.content)[:500]}...")

            try:
                raw_content = message.content
                if isinstance(raw_content, list) and len(raw_content) > 0:
                    raw_content = raw_content[0].get("text", "{}")

                if isinstance(raw_content, str):
                    raw_content = raw_content.strip()
                    if raw_content.startswith('"') and raw_content.endswith('"'):
                        import ast
                        raw_content = ast.literal_eval(raw_content)

                # print some raw_content
                print(raw_content[:500])

                # The SerpApi tool output is typically a JSON string
                tool_data = json.loads(raw_content)

                if "error" in tool_data:
                    print(f"\n[SerpApi Error]: {tool_data['error']}")
                    continue

                if "best_flights" not in tool_data:
                    print("\n[Warning] 'best_flights' array not found in this response.")

                search_metadata = tool_data.get("search_metadata", {})
                json_endpoint = search_metadata.get("json_endpoint")

                best_flights = []

                if json_endpoint:
                    print(f"\n[Downloading Full Payload]: {json_endpoint}")

                    # Open a quick HTTP session to grab the complete JSON file
                    async with aiohttp.ClientSession() as session:
                        async with session.get(json_endpoint) as response:
                            if response.status == 200:
                                full_data = await response.json()
                                if isinstance(full_data, str):
                                    full_data = json.loads(full_data)
                                best_flights = full_data.get("best_flights", [])
                            else:
                                print(f"\n[Download Failed]: HTTP {response.status}")
                else:
                    # Fallback just in case the data was included in the direct response
                    best_flights = tool_data.get("best_flights", [])

                if not best_flights:
                    print("\n[Warning] No 'best_flights' found for this date combo.")

                for f in best_flights:
                    cleaned_flight = extract_essential_flight_data(f, requested_class)
                    if cleaned_flight:
                        flight_results.append(cleaned_flight)

            except Exception as e:
                print(f"\n[Extraction Parsing Error]: {e}")
    print("=" * 63 + "\n")
    # Sort results by airline
    sorted_results = sorted(flight_results, key=lambda x: x.get("airline", "zzzzzz"))

    print(f"[MCP Fetcher] Agent successfully retrieved and extracted {len(sorted_results)} flights.")

    return {
        "flight_results": sorted_results
    }