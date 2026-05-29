from typing import Literal
from enum import Enum

# allowed airlines to infer the information about
class AllowedAirlines(str, Enum):
    VIRGIN_ATLANTIC = "Virgin Atlantic"
    SWISS = "Swiss"
    LUFTHANSA = "Lufthansa"
    TURKISH = "Turkish"
    KLM = "KLM"
    AIR_FRANCE = "Air France"
    BRITISH_AIRWAYS = "British Airways"
    AIR_INDIA = "Air India"
    EMIRATES = "Emirates"
    ETIHAD = "Etihad"
    ALL = "All"

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