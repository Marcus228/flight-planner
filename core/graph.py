from langgraph.graph import StateGraph, START, END
from core.state import FlightAgentState
from nodes.extractor.node import extractor_node, route_after_extraction
from nodes.formatter.node import formatter_node, OUTPUT_FILE
from nodes.mcp_fetcher.node import mcp_fetcher_node

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