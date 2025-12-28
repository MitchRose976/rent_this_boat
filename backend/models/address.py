from enum import Enum
from typing import Optional, Literal

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

    # Free-form address lines
    address_line1: str = Field(min_length=1, max_length=200)
    address_line2: Optional[str] = Field(
        None, max_length=200, description="Apartment, suite, unit, etc."
    )
    unit: Optional[str] = Field(
        None,
        max_length=50,
        description="Short unit identifier (alternate to address_line2)",
    )

    # Structured locality
    city: str = Field(min_length=1, max_length=100)
    state_province: str = Field(min_length=1, max_length=50)
    postal_code: str = Field(min_length=2, max_length=20)
    country: CountryCode = Field(description="ISO country code")

    # Optional extras useful for mapping/search
    latitude: Optional[float] = Field(None, description="Decimal degrees")
    longitude: Optional[float] = Field(None, description="Decimal degrees")

    # Metadata
    is_primary: bool = Field(
        default=False, description="If true this is the user's primary address"
    )
    address_type: Literal["home", "work", "billing", "shipping", "other"] = Field(
        default="home", description="Semantic address type"
    )

    @field_validator("postal_code")
    def validate_postal_code(cls, v, info):
        """Validate postal code format based on country (if provided)."""
        country = info.data.get("country")
        if country == CountryCode.US:
            # US ZIP code: 12345 or 12345-6789
            import re

            if not re.match(r"^\d{5}(-\d{4})?$", v):
                raise ValueError("US ZIP code must be in format 12345 or 12345-6789")
        elif country == CountryCode.CA:
            # Canadian postal code: A1A 1A1 or A1A1A1
            import re

            if not re.match(r"^[A-Za-z]\d[A-Za-z]\s?\d[A-Za-z]\d$", v):
                raise ValueError("Canadian postal code must be in format A1A 1A1")
            return v.upper()
        return v

    @field_validator("state_province")
    def validate_state_province(cls, v, info):
        """Validate and normalize state/province based on country."""
        country = info.data.get("country")
        value = v.upper()
        if country == CountryCode.US:
            if value not in STATES:
                # Allow full names? You could implement a mapping, but keep strict for now.
                raise ValueError(f"Invalid US state code: {v}")
        elif country == CountryCode.CA:
            if value not in PROVINCES:
                raise ValueError(f"Invalid Canadian province code: {v}")
        return value

    def formatted(self) -> str:
        """Return a simple single-line formatted address for display."""
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        if self.unit:
            parts.append(self.unit)
        locality = ", ".join(p for p in (self.city, self.state_province) if p)
        if locality:
            parts.append(locality)
        if self.postal_code:
            parts.append(self.postal_code)
        country = "USA" if self.country == CountryCode.US else "Canada"
        parts.append(country)
        return ", ".join(parts)
