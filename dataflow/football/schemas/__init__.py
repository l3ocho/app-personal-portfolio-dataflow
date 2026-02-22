"""Pydantic schemas for football data validation."""

from .salimt import (
    ClubRecord,
    PlayerRecord,
    LeagueRecord,
    PlayerMarketValueRecord,
    TransferHistoryRecord,
    ClubSeasonRecord,
)
from .mlspa import MLSPASalaryRecord
from .deloitte import ClubFinanceRecord

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
