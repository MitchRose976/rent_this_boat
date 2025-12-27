from enum import Enum

from beanie import Document
from pydantic import BaseModel, ConfigDict, Field, field_validator

PROVINCES = {
    "AB",
    "BC",
    "MB",
    "NB",
    "NL",
    "NS",
    "NT",
    "NU",
    "ON",
    "PE",
    "QC",
    "SK",
    "YT",
}

STATES = {
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DE",
    "FL",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
}


class CountryCode(str, Enum):
    US = "US"
    CA = "CA"


class Address(BaseModel):
    """Address model that handles both US and Canadian formats"""

    street_address: str = Field(..., min_length=1, max_length=200)
    city: str = Field(..., min_length=1, max_length=100)
    state_province: str = Field(
        ..., min_length=1, max_length=50
    )  # State for US, Province for Canada
    postal_code: str = Field(
        ..., min_length=3, max_length=10
    )  # ZIP for US, Postal Code for Canada
    country: CountryCode = Field(..., description="US or CA")
    model_config = ConfigDict(
        extra="allow",
    )

    @field_validator("postal_code")
    def validate_postal_code(cls, v, values):
        """Validate postal code format based on country"""
        country = values.get("country")
        if country == CountryCode.US:
            # US ZIP code: 12345 or 12345-6789
            import re

            if not re.match(r"^\d{5}(-\d{4})?$", v):
                raise ValueError("US ZIP code must be in format 12345 or 12345-6789")
        elif country == CountryCode.CA:
            # Canadian postal code: A1A 1A1
            import re

            if not re.match(r"^[A-Za-z]\d[A-Za-z] \d[A-Za-z]\d$", v):
                raise ValueError("Canadian postal code must be in format A1A 1A1")
        return v.upper() if country == CountryCode.CA else v

    @field_validator("state_province")
    def validate_state_province(cls, v, values):
        """Validate state/province based on country"""
        country = values.get("country")
        if country == CountryCode.US:
            if v.upper() not in STATES:
                raise ValueError(f"Invalid US state code: {v}")
        elif country == CountryCode.CA:
            if v.upper() not in PROVINCES:
                raise ValueError(f"Invalid Canadian province code: {v}")
        return v.upper()

    def get_formatted_address(self) -> str:
        """Get formatted address string"""
        if self.country == CountryCode.US:
            return f"{self.street_address}, {self.city}, {self.state_province} {self.postal_code}, USA"
        else:  # Canada
            return f"{self.street_address}, {self.city}, {self.state_province} {self.postal_code}, Canada"
