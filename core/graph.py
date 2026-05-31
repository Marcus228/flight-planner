from langgraph.graph import StateGraph, START, END
from core.state import FlightAgentState
from nodes.extractor.node import extractor_node, route_after_extraction
from nodes.formatter.node import formatter_node, OUTPUT_FILE
from nodes.mcp_fetcher.node import mcp_fetcher_node

# program control
import asyncio

def build_graph():
    workflow = StateGraph(FlightAgentState)
    workflow.add_node("extractor", extractor_node)
    workflow.add_node("mcp_fetcher", mcp_fetcher_node)
    workflow.add_node("formatter", formatter_node)

    workflow.add_edge(START, "extractor")
    workflow.add_edge("mcp_fetcher", "formatter")
    workflow.add_edge("formatter", END)

    workflow.add_conditional_edges(
        "extractor",
        route_after_extraction,
        [
            # loop back on failure
            "extractor",
            # move forward on success
            "mcp_fetcher",
        ]
    )

    app = workflow.compile()
    print("Graph successfully created.")
    return app

async def main():
    app = build_graph()

    user_prompt : str = input("Please enter the required flight details:")
    print(f"\n[USER INPUT] {user_prompt}\n" + "-" * 50)

    initial_state: FlightAgentState = {
        "user_input": user_prompt,
        "parsed_parameters": None,
        "api_queries": [],
        "flight_results": [],
        "error_message": None,
        "retry_count": 0,
    }

    # execute the graph asynchronously
    try:
        await app.ainvoke(initial_state)
        print("\n" + "=" * 50)
        print("AGENT EXECUTION COMPLETE")
        print(f"Results saved to: {OUTPUT_FILE}")
        print("=" * 50)

    except Exception as e:
        print(f"\nCRITICAL PIPELINE FAILURE: {e}")

if __name__ == "__main__":
    asyncio.run(main())