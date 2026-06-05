import sys
from typing import Set
from enum import Enum

type AirlineShortcode = str

# allowed airlines to infer the information about
# the shortcodes were taken from https://www.iata.org/en/publications/directories/code-search?
allowedAirlines: Set[AirlineShortcode] = {
    # Virgin Atlantic Airways Ltd
    "VS",
    # SWISS International Air Lines Ltd.
    "LX",
    # Lufthansa and Lufthansa Cargo AG
    "LH",
    # Turkish Airlines Inc
    "TK",
    # KLM
    "KL",
    # Air France
    "AF",
    # British Airways PLC
    "BA",
    # Air India dba Air India
    "AI",
    # Emirates
    "EK",
    # Etihad Airways Dba Etihad Airways PJSC
    "EY"
}

# travel classification enum class
# used to extract flights of the specific class
class TravelClass(str, Enum):
    ECONOMY = "Economy"
    PREMIUM_ECONOMY = "Premium Economy"
    BUSINESS = "Business"
    FIRST = "First"

# max retry threshold configuration for extractor node
#   if the model fails to provide the reply after MAX_EXTRACT_REPLIES,
#   the timeout is declared
MAX_EXTRACT_RETRIES: int= 3

# used for prevention of SerpAPI gateway closure in mcp_fetcher
# The API allows concurrent calls, and recommended cap is 25% of
#     the current rate. Uncapped to increase speed of response.
MAX_CONCURRENT_API_CALLS: int = sys.maxsize