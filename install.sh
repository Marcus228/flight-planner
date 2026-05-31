#!/bin/bash
set -e

echo "Installing flight agent dependencies..."

pip install \
    pydantic \
    langgraph \
    langchain-google-genai \
    langchain-mcp-adapters \
    python-dotenv \
    aiohttp \

echo "All dependencies installed."
