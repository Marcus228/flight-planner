Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "Installing flight agent dependencies..."

pip install `
    pydantic `
    langgraph `
    langchain-google-genai `
    langchain-mcp-adapters `
    python-dotenv `
    aiohttp

Write-Host "All dependencies installed."