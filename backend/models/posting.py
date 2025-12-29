from typing_extensions import Annotated
from beanie import Document, Indexed
from pydantic import Field, ConfigDict
from datetime import datetime, timezone
from typing import Optional
from enum import Enum

from models.boat import Boat
from models.address import Address


class BoatType(str, Enum):
    SAILBOAT = "sailboat"
    MOTORBOAT = "motorboat"
    YACHT = "yacht"
    KAYAK = "kayak"
    CANOE = "canoe"
    CATAMARAN = "catamaran"
    SPEEDBOAT = "speedboat"
    FISHING_BOAT = "fishing_boat"
    OTHER = "other"


class PostingStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class Posting(Document):
    # Owner information
    owner_id: Annotated[
        str,
        Field(description="Reference to the owner User ID"),
        Indexed(),
    ]

    # Boat details
    boat: Boat

    # Location
    location: Annotated[Address, Field(description="Location of the boat")]

    # Pricing
    price_per_day: Annotated[
        float, Field(gt=0, description="Rental price per day in USD")
    ]
    price_per_hour: Annotated[
        Optional[float], Field(gt=0, description="Rental price per hour in USD")
    ] = None
    deposit: Annotated[
        Optional[float], Field(ge=0, description="Security deposit required in USD")
    ] = None

    # Availability & booking
    available_from: Annotated[
        Optional[datetime], Field(description="Date boat becomes available")
    ] = None
    available_until: Annotated[
        Optional[datetime], Field(description="Date boat is available until")
    ] = None
    minimum_rental_days: Annotated[
        int, Field(ge=1, description="Minimum number of days for rental")
    ] = 1

    # Posting metadata
    status: Annotated[
        PostingStatus, Field(description="Status of the posting"), Indexed()
    ] = PostingStatus.ACTIVE
    created_at: Annotated[
        datetime,
        Field(default_factory=lambda: datetime.now(timezone.utc)),
        Indexed(),
    ]
    updated_at: Annotated[
        datetime,
        Field(default_factory=lambda: datetime.now(timezone.utc)),
        Indexed(),
    ]

    # Ratings & reviews
    average_rating: Annotated[
        Optional[float], Field(ge=0, le=5, description="Average rating from reviews")
    ] = None
    total_reviews: Annotated[
        int, Field(ge=0, description="Total number of reviews")
    ] = 0

    # Additional features
    features: Annotated[
        list[str],
        Field(
            description="List of boat features (e.g., 'GPS', 'Life Jackets', 'Cooler')"
        ),
    ] = []
    images: Annotated[
        list[str],
        Field(description="List of image URLs for the boat"),
    ] = []

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "owner_id": "507f1f77bcf86cd799439011",
                "boat": {
                    "description": "Well-maintained 30ft sailboat with recent updates",
                    "boat_type": "sailboat",
                    "license_required": False,
                    "length_feet": 30.0,
                    "length_meters": 9.14,
                    "capacity": 6,
                    "year_built": 2015,
                    "color": {
                        "primary": "black",
                        "secondary": ["white", "red"],
                    },
                    "color_tags": ["black", "white", "red"],
                    "condition": "excellent",
                    "fuel_type": "Diesel",
                    "max_speed_knots": 12.5,
                    "has_bathroom": True,
                    "has_kitchen": True,
                    "has_sleeping_quarters": True,
                    "sleeping_capacity": 4,
                },
                "location": {
                    "address_line1": "123 Marina Way",
                    "address_line2": None,
                    "unit": None,
                    "city": "Key West",
                    "state_province": "FL",
                    "postal_code": "33040",
                    "country": "US",
                    "latitude": "24.5551",
                    "longitude": "-81.7826",
                    "is_primary": True,
                    "address_type": "other",
                },
                "price_per_day": 250.0,
                "price_per_hour": 50.0,
                "deposit": 500.0,
                "available_from": "2025-01-01T00:00:00Z",
                "available_until": "2025-12-31T23:59:59Z",
                "minimum_rental_days": 1,
                "status": "active",
                "created_at": "2023-01-01T12:00:00Z",
                "updated_at": "2023-01-10T08:30:00Z",
                "average_rating": 4.8,
                "total_reviews": 12,
                "features": ["GPS", "Life Jackets", "Cooler", "Fishing Rod"],
                "images": ["https://example.com/boat1.jpg", "https://example.com/boat2.jpg"],
            }
        },
    )

    class Settings:
        name = "postings"  # Collection name in MongoDB
        indexes = [
            [("location.latitude", "2dsphere"), ("location.longitude", "2dsphere")],
            [("owner_id", 1)],
            [("status", 1), ("created_at", -1)],
            [("boat_type", 1), ("price_per_day", 1)],
        ]

    def __str__(self):
        return f"Posting(owner_id={self.owner_id}, status={self.status}, created_at={self.created_at})"

    def get_availability_status(self) -> bool:
        """Check if the boat is currently available for booking."""
        now = datetime.now(timezone.utc)
        if self.available_from and now < self.available_from:
            return False
        if self.available_until and now > self.available_until:
            return False
        return self.status == PostingStatus.ACTIVE

    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now(timezone.utc)
