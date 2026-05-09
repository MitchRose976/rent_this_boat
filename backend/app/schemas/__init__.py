"""
Data models for the Rent This Boat application.

This module exports all document models and related enums for easy importing.
"""

# User models
from .user import User, UserRole

# Address models
from .address import Address, CountryCode

# Boat models
from .boat import (
    Boat,
    BoatType,
    BoatColor,
    BoatColorScheme,
    BoatCondition,
    Engine,
    EngineType,
)

# Posting models
from .posting import Posting, PostingStatus

__all__ = [
    # User
    "User",
    "UserRole",
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
