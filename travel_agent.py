# The agent should allow us to search for one-way or round-trip flight options based
# on a flexible departure date range and a flexible return date range.
from datetime import date

# For example, we should be able to input a departure window from date X to date Y,
# and a return window from date A to date B, and the agent should search across all
# valid combinations within those ranges only within the airline list we provide below
# and return the available fare options from those airlines:

# * Virgin Atlantic
# * Swiss
# * Lufthansa
# * Turkish
# * KLM
# * Air France
# * British Airways
# * Air India
# * Emirates
# * Etihad

# It should also provide us with the details about departure airport, arrival airport, return airport and flight class.

# The results should be shown in a clear format so we can easily compare options across airlines and dates.

from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from typing_extensions import Literal
from datetime import datetime

AllowedAirlines = Literal["Virgin Atlantic", "Swiss", "Lufthansa", "Turkish", "KLM", "Air France",
                          "British Airways", "Air India", "Emirates", "Etihad"]

class DateWindow(BaseModel):
    start_date: str = Field(
        description="The earliest acceptable date in format YYYY-MM-DD"
    )
    end_date: str = Field(
        description="The latest acceptable date in format YYYY-MM-DD"
    )

    @model_validator(mode='after')
    def validate_internal_chronology(self) -> 'DateWindow':
        # try parsing the inputs as date and time
        # if the parse fails, ValueError is raised
        try:
            start = datetime.strptime(self.start_date, "%Y-%m-%d")
            end = datetime.strptime(self.end_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Dates must be strictly in YYYY-MM-DD format.")

        # check whether the start and end dates are chronologically correct
        if end < start:
            raise ValueError(
                f"Window error: The end date ({self.end_date}) "
                f"cannot be earlier than the start date ({self.start_date})."
            )

        return self


class FlightExtraction(BaseModel):
    origin: str
    destination: str
    departure_window: DateWindow = Field(
        description="The date range when user wants to depart.",
    )
    return_window: Optional[DateWindow] = Field(
        description="The date range when user wants to return. "
                    "Leave null if the flight type specified by the user is one-way.",
        default = None,
    )
    airlines: List[AllowedAirlines] = Field(
        description="The list of airlines explicitly requested by the user.",
    )

    @model_validator(mode = 'after')
    def validate_chronology(self) -> 'FlightExtraction':
        # 1. If it's a one-way flight, there is nothing to compare.
        if not self.return_window:
            return self

        # 2. Parse the ISO strings into comparable datetime objects
        try:
            dep_start = datetime.strptime(self.departure_window.start_date, "%Y-%m-%d")
            ret_start = datetime.strptime(self.return_window.start_date, "%Y-%m-%d")
        except ValueError:
            # If the LLM output something weird like "next tuesday", standard validation
            # or this block will catch it.
            raise ValueError("Dates must be strictly in YYYY-MM-DD format.")

        # 3. The actual logic check
        if ret_start < dep_start:
            raise ValueError(
                f"Logical error: The return start date ({self.return_window.start_date}) "
                f"cannot be earlier than the departure start date ({self.departure_window.start_date})."
            )

        # 4. If all checks pass, return the instance
        return self
