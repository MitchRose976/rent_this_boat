from typing import Optional
from pydantic import ConfigDict, Field
from typing_extensions import Annotated
from beanie import Document, Indexed
from ...schemas.boat import BoatType, BoatCondition, BoatColor, BoatColorScheme


class Boat(Document):
    description: Annotated[
        str, Field(max_length=5000, description="Detailed description of the boat")
    ]
    boat_type: Annotated[BoatType, Field(description="Type of boat"), Indexed()]
    license_required: Annotated[
        bool, Field(description="Is a license required to operate the boat?")
    ] = False

    # Physical characteristics
    length_feet: Annotated[float, Field(gt=0, description="Length of boat in feet")]
    length_meters: Annotated[float, Field(gt=0, description="Length of boat in meters")]
    capacity: Annotated[int, Field(gt=0, description="Maximum number of passengers")]
    year_built: Annotated[
        Optional[int], Field(ge=1900, le=2100, description="Year boat was built")
    ] = None

    # Color - structured for flexible querying
    color: Annotated[
        BoatColorScheme,
        Field(description="Color scheme of the boat with primary and secondary colors"),
    ]

    # All color values flattened for simple color filter queries
    color_tags: Annotated[
        list[BoatColor],
        Field(
            description="Flattened list of all colors (primary + secondary) for simple color filtering"
        ),
        Indexed(),
    ] = []

    # Condition, maintenance, and engine details
    condition: Annotated[
        BoatCondition, Field(description="Overall condition of the boat"), Indexed()
    ] = BoatCondition.GOOD
    fuel_type: Annotated[
        Optional[str],
        Field(
            max_length=50,
            description="Type of fuel (e.g., 'Diesel', 'Gasoline', 'Electric', 'Hybrid')",
        ),
    ] = None
    engine: Annotated[
        Optional[Engine],
        Field(
            description="Engine specifications (not applicable for manually powered boats)"
        ),
    ] = None

    # Amenities & equipment
    has_bathroom: Annotated[
        bool, Field(description="Does the boat have a bathroom?")
    ] = False
    has_kitchen: Annotated[
        bool, Field(description="Does the boat have a kitchen/galley?")
    ] = False
    has_sleeping_quarters: Annotated[
        bool, Field(description="Does the boat have sleeping quarters/cabins?")
    ] = False
    sleeping_capacity: Annotated[
        Optional[int],
        Field(ge=0, description="Number of people that can sleep on the boat"),
    ] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
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
                "engine": {
                    "brand": "Tohatsu",
                    "model": "MFS50A",
                    "engine_type": "4_stroke",
                    "horsepower": 50.0,
                    "year_built": 2024,
                    "hours_on_engine": 25.0,
                    "last_serviced": "2024-06-15",
                    "service_notes": "Oil change, filter replacement, and routine inspection completed",
                },
                "has_bathroom": True,
                "has_kitchen": True,
                "has_sleeping_quarters": True,
                "sleeping_capacity": 4,
            }
        },
    )

    class Settings:
        name = "boats"  # Collection name in MongoDB

    def __str__(self):
        return f"Boat(type={self.boat_type}, length={self.length_feet}ft, colors={self.color.primary})"

    def set_color_tags(self):
        """Update color_tags to include primary and all secondary colors."""
        self.color_tags = [self.color.primary] + self.color.secondary
