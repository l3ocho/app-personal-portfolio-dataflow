"""SQLAlchemy models for Toronto housing data."""

from .base import Base, create_tables, get_engine, get_session_factory
from .dimensions import (
    DimCMHCZone,
    DimNeighbourhood,
    DimPolicyEvent,
    DimTime,
)
from .facts import (
    BridgeCMHCNeighbourhood,
    FactAmenities,
    FactCensus,
    FactCrime,
    FactRentals,
)
from .profile import FactNeighbourhoodProfile

__all__ = [
    # Base
    "Base",
    "get_engine",
    "get_session_factory",
    "create_tables",
    # Dimensions
    "DimTime",
    "DimCMHCZone",
    "DimNeighbourhood",
    "DimPolicyEvent",
    # Facts
    "FactRentals",
    "FactCensus",
    "FactCrime",
    "FactAmenities",
    "FactNeighbourhoodProfile",
    # Bridge tables
    "BridgeCMHCNeighbourhood",
]
