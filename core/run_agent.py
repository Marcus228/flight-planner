import asyncio
from core.graph import build_graph
from core.state import FlightAgentState
from nodes.formatter.node import OUTPUT_FILE


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