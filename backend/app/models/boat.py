from enum import Enum
from typing import Optional
from datetime import date
from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import Annotated
from beanie import Document, Indexed


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


class BoatColor(str, Enum):
    """Pre-defined list of available boat colors for selection"""

    BLACK = "black"
    WHITE = "white"
    RED = "red"
    BLUE = "blue"
    NAVY = "navy"
    GRAY = "gray"
    GREY = "grey"
    GREEN = "green"
    YELLOW = "yellow"
    ORANGE = "orange"
    BROWN = "brown"
    GOLD = "gold"
    SILVER = "silver"
    CREAM = "cream"
    BEIGE = "beige"


class BoatColorScheme(BaseModel):
    """Nested model for structured boat color information"""

    primary: Annotated[
        BoatColor,
        Field(description="Primary color of the boat"),
    ]
    secondary: Annotated[
        list[BoatColor],
        Field(
            min_length=0,
            max_length=5,
            description="List of secondary colors on the boat",
        ),
    ] = []

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "primary": "black",
                "secondary": ["white", "red"],
            }
        },
    )


class BoatCondition(str, Enum):
    """Condition rating of the boat"""

    LIKE_NEW = "like_new"
    EXCELLENT = "excellent"
    VERY_GOOD = "very_good"
    GOOD = "good"
    FAIR = "fair"


class EngineType(str, Enum):
    """Engine type classification"""

    TWO_STROKE = "2_stroke"
    FOUR_STROKE = "4_stroke"
    ELECTRIC = "electric"


class Engine(BaseModel):
    """Engine specifications and maintenance details"""

    brand: Annotated[
        str,
        Field(min_length=1, max_length=100, description="Engine manufacturer brand"),
    ]
    model: Annotated[
        str, Field(min_length=1, max_length=100, description="Engine model name")
    ]
    engine_type: Annotated[
        EngineType,
        Field(description="Type of engine (2-stroke, 4-stroke, or electric)"),
    ]
    horsepower: Annotated[float, Field(gt=0, description="Engine horsepower (HP)")]
    year_built: Annotated[
        int, Field(ge=1900, le=2100, description="Year the engine was manufactured")
    ]

    # Engine usage metrics
    hours_on_engine: Annotated[
        float, Field(ge=0, description="Total hours the engine has been run")
    ] = 0.0

    # Maintenance
    last_serviced: Annotated[
        Optional[date],
        Field(description="Date of last engine service/maintenance"),
    ] = None
    service_notes: Annotated[
        Optional[str],
        Field(max_length=500, description="Notes about engine service history"),
    ] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "brand": "Yamaha",
                "model": "F250",
                "engine_type": "4_stroke",
                "horsepower": 250.0,
                "year_built": 2018,
                "hours_on_engine": 850.5,
                "last_serviced": "2024-06-15",
                "service_notes": "Oil change, filter replacement, and routine inspection completed",
            }
        },
    )


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
