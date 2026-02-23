"""Pydantic schemas for Toronto housing data validation."""

from .amenities import AmenityCount, AmenityRecord, AmenityType
from .cmhc import BedroomType, CMHCAnnualSurvey, CMHCRentalRecord, ReliabilityCode
from .dimensions import (
    CMHCZone,
    Confidence,
    ExpectedDirection,
    Neighbourhood,
    PolicyCategory,
    PolicyEvent,
    PolicyLevel,
    TimeDimension,
)
from .neighbourhood import CensusRecord, CrimeRecord, CrimeType, NeighbourhoodRecord
from .census_extended import CensusExtendedRecord
from .profile import VALID_CATEGORIES, ProfileRecord

__all__ = [
    # CMHC
    "CMHCRentalRecord",
    "CMHCAnnualSurvey",
    "BedroomType",
    "ReliabilityCode",
    # Dimensions
    "TimeDimension",
    "CMHCZone",
    "Neighbourhood",
    "PolicyEvent",
    # Enums
    "PolicyLevel",
    "PolicyCategory",
    "ExpectedDirection",
    "Confidence",
    # Neighbourhood data (Phase 3)
    "NeighbourhoodRecord",
    "CensusRecord",
    "CrimeRecord",
    "CrimeType",
    # Amenities (Phase 3)
    "AmenityType",
    "AmenityRecord",
    "AmenityCount",
    # Profile (Neighbourhood community profile data)
    "ProfileRecord",
    "VALID_CATEGORIES",
    # Census extended (Path B wide-format scalar indicators)
    "CensusExtendedRecord",
]
