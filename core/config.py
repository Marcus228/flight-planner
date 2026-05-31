from typing import Literal, List
from enum import Enum

type AirlineShortcode = str

# allowed airlines to infer the information about
# the shortcodes were taken from https://www.iata.org/en/publications/directories/code-search?
allowedAirlines: List[AirlineShortcode] = [
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
]

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
MAX_EXTRACT_RETRIES = 3

# BATCHING LOGIC for SerpAPI in fetcher node.
# The API allows concurrency, but batching is defaulted to size 5 to be safe
BATCH_SIZE = 5

# determines how many top results to retrieve per API call
# 2 is recommended to ensure state is manageable
TOP_RESULTS = 2