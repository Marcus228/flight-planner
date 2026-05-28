from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
from core.config import AllowedAirlines
from datetime import datetime

# base model for storing the date window for departure/return
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

# base model for tracking the user search intent
class FlightSearchIntent(BaseModel):
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
    def validate_chronology(self) -> 'FlightSearchIntent':
        # if it's a one-way flight, return the instance
        if not self.return_window:
            return self

        # parse the ISO strings into comparable datetime objects
        # if the parse fails, ValueError is raised
        try:
            dep_start = datetime.strptime(self.departure_window.start_date, "%Y-%m-%d")
            ret_start = datetime.strptime(self.return_window.start_date, "%Y-%m-%d")
        except ValueError:
            # If the LLM output something weird like "next tuesday", standard validation
            # or this block will catch it.
            raise ValueError("Dates must be strictly in YYYY-MM-DD format.")

        # check dates are chronological
        if ret_start < dep_start:
            raise ValueError(
                f"Logical error: The return start date ({self.return_window.start_date}) "
                f"cannot be earlier than the departure start date ({self.departure_window.start_date})."
            )

        # if all checks pass, return the instance
        return self