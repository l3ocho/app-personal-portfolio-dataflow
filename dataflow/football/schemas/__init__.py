"""Pydantic schemas for football data validation."""

from .deloitte import ClubFinanceRecord
from .mlspa import MLSPASalaryRecord
from .salimt import (
    ClubRecord,
    ClubSeasonRecord,
    LeagueRecord,
    PlayerMarketValueRecord,
    PlayerRecord,
    TransferHistoryRecord,
)

__all__ = [
    "ClubRecord",
    "PlayerRecord",
    "LeagueRecord",
    "PlayerMarketValueRecord",
    "TransferHistoryRecord",
    "ClubSeasonRecord",
    "MLSPASalaryRecord",
    "ClubFinanceRecord",
]
