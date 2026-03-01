from decimal import Decimal
from enum import Enum
import re
from typing import Annotated, Optional, Literal
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
    address_line1: Annotated[
        str, Field(min_length=1, max_length=200, description="Street address line 1")
    ]
    address_line2: Annotated[
        str | None, Field(max_length=200, description="Apartment, suite, unit, etc.")
    ] = None
    unit: Annotated[
        str | None,
        Field(
            max_length=10,
            description="Short unit identifier (alternate to address_line2)",
        ),
    ] = None

    # Structured locality
    city: Annotated[str, Field(min_length=1, max_length=100, description="City")]
    state_province: Annotated[
        str, Field(min_length=1, max_length=20, description="State or Province")
    ]
    postal_code: Annotated[
        str, Field(min_length=5, max_length=10, description="ZIP or Postal Code")
    ]
    country: Annotated[CountryCode, Field(description="ISO country code")]

    # Optional extras useful for mapping/search
    latitude: Annotated[
        Optional[Decimal], Field(description="Latitude - Decimal degrees")
    ] = None
    longitude: Annotated[
        Optional[Decimal], Field(description="Longitude - Decimal degrees")
    ] = None

    # Metadata
    is_primary: Annotated[
        bool,
        Field(description="If true this is the user's primary address"),
    ] = False
    address_type: Annotated[
        Literal["home", "work", "billing", "shipping", "other"],
        Field(description="Semantic address type"),
    ] = "home"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "address_line1": "123 Main St",
                "address_line2": "Suite 200",
                "unit": "APT-5",
                "city": "Toronto",
                "state_province": "ON",
                "postal_code": "M4B 1B3",
                "country": "CA",
                "latitude": "43.7182",
                "longitude": "-79.2957",
                "is_primary": True,
                "address_type": "home",
            }
        },
    )

    # ------------------------------------------------ Validators ------------------------------------------------ #
    @field_validator("postal_code")
    def validate_postal_code(cls, v, info):
        """Validate postal code format based on country (if provided)."""
        country = info.data.get("country")
        if country == CountryCode.US:
            # US ZIP code: 12345 or 12345-6789
            if not re.match(r"^\d{5}(-\d{4})?$", v):
                raise ValueError("US ZIP code must be in format 12345 or 12345-6789")
        elif country == CountryCode.CA:
            # Canadian postal code: A1A 1A1 or A1A1A1
            if not re.match(r"^[A-Za-z]\d[A-Za-z]\s?\d[A-Za-z]\d$", v):
                raise ValueError("Canadian postal code must be in format A1A 1A1")
            return v.upper()
        return v

    @field_validator("state_province", mode="before")
    def normalize_state_province(cls, v):
        return v.upper() if isinstance(v, str) else v

    @field_validator("state_province")
    def validate_state_province(cls, v, info):
        """Validate and normalize state/province based on country."""
        country = info.data.get("country")
        if country == CountryCode.US:
            if v not in STATES:
                # Allow full names? You could implement a mapping, but keep strict for now.
                raise ValueError(f"Invalid US state code: {v}")
        elif country == CountryCode.CA:
            if v not in PROVINCES:
                raise ValueError(f"Invalid Canadian province code: {v}")
        return v

    # ------------------------------------------------ Methods ------------------------------------------------ #
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
