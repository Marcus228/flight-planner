The agent should allow us to search for one-way or round-trip flight options based
on a flexible departure date range and a flexible return date range.
from datetime import date

For example, we should be able to input a departure window from date X to date Y,
and a return window from date A to date B, and the agent should search across all
valid combinations within those ranges only within the airline list we provide below
and return the available fare options from those airlines:

* Virgin Atlantic
* Swiss
* Lufthansa
* Turkish
* KLM
* Air France
* British Airways
* Air India
* Emirates
* Etihad

It should also provide us with the details about departure airport, arrival airport, return airport and flight class.

The results should be shown in a clear format so we can easily compare options across airlines and dates.