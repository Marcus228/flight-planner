import os
from contextlib import asynccontextmanager
import httpx

@asynccontextmanager
async def get_api_client():
    """
    Establishes a pre-configured HTTPX client for the Duffel API.
    Replaces the old SerpAPI MultiServerMCPClient.
    """
    duffel_token = os.environ.get("DUFFEL_ACCESS_TOKEN")
    if not duffel_token:
        raise ValueError("CRITICAL: DUFFEL_ACCESS_TOKEN environment variable is not set.")

    headers = {
        "Duffel-Version": "v2",
        "Authorization": f"Bearer {duffel_token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        yield client