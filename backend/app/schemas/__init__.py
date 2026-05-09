"""
Data models for the Rent This Boat application.

This module exports all document models and related enums for easy importing.
"""

# Address models
from .address import Address, CountryCode

# Boat models
from .boat import (
    BoatType,
    BoatColor,
    BoatColorScheme,
    BoatCondition,
    Engine,
    EngineType,
)

# Posting models
from .posting import PostingStatus

__all__ = [
    # Address
    "Address",
    "CountryCode",
    # Boat
    "Boat",
    "BoatType",
    "BoatColor",
    "BoatColorScheme",
    "BoatCondition",
    "Engine",
    "EngineType",
    # Posting
    "Posting",
    "PostingStatus",
]
