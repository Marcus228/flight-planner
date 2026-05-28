from typing import Literal
# airline configuration
AllowedAirlines = Literal["Virgin Atlantic", "Swiss", "Lufthansa", "Turkish", "KLM", "Air France",
                          "British Airways", "Air India", "Emirates", "Etihad"]

# max retry threshold configuration for extractor node
#   if the model fails to provide the reply after MAX_EXTRACT_REPLIES,
#   the timeout is declared
MAX_EXTRACT_RETRIES = 3

# BATCHING LOGIC for SerpAPI in fetcher node.
# The API allows concurrency, but batching is defaulted to size 5 to be safe
BATCH_SIZE = 5