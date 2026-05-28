from typing import Literal
# airline configuration
AllowedAirlines = Literal["Virgin Atlantic", "Swiss", "Lufthansa", "Turkish", "KLM", "Air France",
                          "British Airways", "Air India", "Emirates", "Etihad"]

# max retry threshold configuration
MAX_EXTRACT_RETRIES = 3

# SerpApi Endpoint for Google Flights
SERPAPI_URL = "https://serpapi.com/search"