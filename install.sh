#!/bin/bash
set -e

echo "Installing flight agent dependencies..."

pip install \
    pydantic \
    langgraph \
    langchain-google-genai \
    python-dotenv \
    httpx

echo "All dependencies installed."