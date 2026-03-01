from enum import Enum
from typing import Optional
from datetime import date
from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import Annotated


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
