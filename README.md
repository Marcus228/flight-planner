# Flight Search Agent

An autonomous agentic system that searches for flight options across a configurable set of airlines, supporting flexible departure and return date windows for both one-way and round-trip itineraries.

---

## Specification

The agent searches for one-way or round-trip flight options based on flexible date ranges. A departure window (date X to date Y) and an optional return window (date A to date B) can be provided, and the agent searches across all valid date combinations.

Results are filtered to the following airlines only:

| Airline          | IATA Code |
|------------------|-----------|
| Virgin Atlantic  | VS        |
| Swiss            | LX        |
| Lufthansa        | LH        |
| Turkish Airlines | TK        |
| KLM              | KL        |
| Air France       | AF        |
| British Airways  | BA        |
| Air India        | AI        |
| Emirates         | EK        |
| Etihad           | EY        |

Each result includes: departure airport, arrival airport, return airport, flight class, airlines, outbound date, return date, and total cost. Results are written to a CSV file for easy comparison across airlines and dates.

---

## Architecture

The agent is implemented as a LangGraph state machine. State flows through four nodes in sequence:

```
START → Extractor → MCP Fetcher → Formatter → END
```

### Extractor Node
Accepts a natural language user query and uses a structured LLM (Gemini) to extract a typed `FlightSearchIntent` object containing origin, destination, departure window, return window, and flight class. Retries up to `MAX_EXTRACT_RETRIES` on validation failure.

### MCP Fetcher Node
Generates all valid date permutations from the extracted parameters and executes them concurrently against the SerpApi Google Flights MCP tool.

For **round-trip** searches the node performs a two-stage fetch per outbound flight:
1. First call returns outbound legs, each carrying a `departure_token`
2. Second call uses that token to retrieve the matched return legs

For **one-way** searches only a single call is made per date.

An `asyncio.Semaphore` caps concurrent requests to avoid rate-limiting. Results from `best_flights` and `other_flights` are merged before extraction.

### Formatter Node
Takes the aggregated flight results from state and writes them to `output/flight_results.csv` with a clean, human-readable schema.

---

## Setup

### Environment Variables

Create a `.env` file in the project root with the following keys:

```env
LLM_KEY=your_llm_api_key
SERPAPI_API_KEY=your_serpapi_api_key
```

`LLM_KEY` is consumed by the LLM factory — a modular abstraction in the Extractor node that allows different language models to be swapped in without changing the rest of the pipeline. By default this is configured for Gemini, but the factory can be pointed at any supported model by updating the relevant configuration. The SerpApi key is used by the MCP Fetcher node to query Google Flights data.

### Installation

```bash
bash install.sh
```

---

## Notes

### Codeshare Flights
Some results may display airline names that are not in the configured allowed list (e.g. `JAL,British Airways`). This occurs because airlines operate codeshare agreements — a flight may be sold and ticketed by one carrier (e.g. British Airways) but physically operated by a partner carrier (e.g. JAL). SerpApi returns both airline names on the leg. These results are valid — the ticket is issued by an allowed carrier — and are retained intentionally.

### Output
Results are written to `output/flight_results.csv` relative to the project root on each run. The file is overwritten on each execution.
