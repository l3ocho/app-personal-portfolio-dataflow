"""Pydantic schemas for MLSPA salary data."""


from pydantic import BaseModel, Field


class MLSPASalaryRecord(BaseModel):
    """Schema for MLS player salary fact table.

    Parsed from MLSPA cleaned CSV files.
    """

    player_id: str = Field(max_length=20, description="Transfermarkt player ID if available, else CSV ID")
    player_name: str = Field(max_length=150)
    club_id: str = Field(max_length=20, description="MLS club ID")
    club_name: str = Field(max_length=100)
    season: int = Field(ge=2000, le=2100)
    salary_usd: int | None = Field(default=None, ge=0, description="Annual salary in USD")
    guaranteed_compensation_usd: int | None = Field(default=None, ge=0)
