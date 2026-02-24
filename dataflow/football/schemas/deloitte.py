"""Pydantic schemas for Deloitte revenue data.

Note: PDF extraction not yet implemented (Phase 2+).
"""


from pydantic import BaseModel, Field


class ClubFinanceRecord(BaseModel):
    """Schema for club annual revenue fact table (Deloitte Money League).

    Stub for Phase 2+ implementation. PDF extraction skipped in Phase 1.
    """

    club_id: str = Field(max_length=20)
    club_name: str = Field(max_length=150)
    season: int = Field(ge=1900, le=2100)
    revenue_eur: int | None = Field(default=None, ge=0, description="Annual revenue in EUR")
    operating_profit_eur: int | None = Field(default=None, description="Can be negative")
