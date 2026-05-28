from typing import Literal
from enum import Enum

# allowed airlines to infer the information from
AllowedAirlines = Literal["Virgin Atlantic", "Swiss", "Lufthansa", "Turkish", "KLM", "Air France",
                          "British Airways", "Air India", "Emirates", "Etihad"]

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