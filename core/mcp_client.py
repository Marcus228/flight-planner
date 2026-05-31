import os
from langchain_mcp_adapters.client import MultiServerMCPClient


def get_mcp_client() -> MultiServerMCPClient:
    """
    Establishes a connection to SerpApi's official hosted MCP server.
    We pass the API key directly in the URL path, acting as our authentication.
    """
    api_key = os.environ.get("SERPAPI_API_KEY")
    if not api_key:
        raise ValueError("CRITICAL: SERPAPI_API_KEY environment variable is not set.")

    client = MultiServerMCPClient({
        "serpapi": {
            "transport": "http",
            "url": f"https://mcp.serpapi.com/{api_key}/mcp"
        }
    })

    return client