Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "Installing flight agent dependencies..."

pip install `
    pydantic `
    langgraph `
    langchain-google-genai `
    python-dotenv `
    httpx

Write-Host "All dependencies installed."