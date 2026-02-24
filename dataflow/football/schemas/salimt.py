"""Pydantic schemas for salimt Transfermarkt-scraped football data."""

from datetime import date

from pydantic import BaseModel, Field


class LeagueRecord(BaseModel):
    """Schema for football league dimension."""

    league_id: str = Field(max_length=10, description="Transfermarkt league code (e.g., GB1, ES1)")
    league_name: str = Field(max_length=100)
    country: str = Field(max_length=50)
    season_start_year: int = Field(ge=1900, le=2100)


class ClubRecord(BaseModel):
    """Schema for football club dimension."""

    club_id: str = Field(max_length=20, description="Transfermarkt club ID (varchar)")
    club_name: str = Field(max_length=150)
    country: str | None = Field(default=None, max_length=50)
    club_slug: str | None = Field(default=None, max_length=150, description="URL-friendly slug")
    logo_url: str | None = Field(default=None, max_length=255)
    source_url: str | None = Field(default=None, max_length=255, description="Transfermarkt URL")


class PlayerRecord(BaseModel):
    """Schema for football player dimension."""

    player_id: str = Field(max_length=20, description="Transfermarkt player ID (varchar)")
    player_name: str = Field(max_length=150)
    date_of_birth: date | None = None
    nationality: str | None = Field(default=None, max_length=50)
    height_cm: int | None = Field(default=None, ge=100, le=250, description="Height in cm, parsed from '1,85 m' format")
    position: str | None = Field(default=None, max_length=50)
    preferred_foot: str | None = Field(default=None, max_length=10)


class PlayerMarketValueRecord(BaseModel):
    """Schema for player market value fact table.

    Note: Can contain millions of rows. date_unix is bigint from Transfermarkt.
    """

    player_id: str = Field(max_length=20)
    club_id: str | None = Field(default=None, max_length=20)
    value_eur: int | None = Field(default=None, ge=0, description="Market value in EUR")
    market_value_date: date = Field(description="Parsed from date_unix (bigint)")
    season: int | None = Field(default=None, ge=1900, le=2100, description="Season start year (e.g., 2023 for 2023/24)")


class TransferHistoryRecord(BaseModel):
    """Schema for transfer fact table.

    Handles multiple fee formats: '€12.5m', 'free transfer', 'Loan', '?', '-', None
    Unparseable values set fee_eur=NULL, is_loan=False
    Note: transfer_date is optional since transfer_history.csv is stored in Git LFS
    """

    player_id: str = Field(max_length=20)
    from_club_id: str | None = Field(default=None, max_length=20)
    to_club_id: str = Field(max_length=20)
    transfer_date: date | None = Field(default=None)
    fee_eur: int | None = Field(default=None, ge=0, description="Parsed fee in EUR or NULL if unparseable")
    is_loan: bool = Field(default=False, description="True if 'Loan' in original, False if free or unparseable")
    season: int | None = Field(default=None, ge=1900, le=2100)


class ClubSeasonRecord(BaseModel):
    """Schema for club season fact table (e.g., final league position, points)."""

    club_id: str = Field(max_length=20)
    league_id: str = Field(max_length=10)
    season: int = Field(ge=1900, le=2100)
    position: int | None = Field(default=None, ge=1, le=50, description="Final league position")
    matches_played: int | None = Field(default=None, ge=0)
    wins: int | None = Field(default=None, ge=0)
    draws: int | None = Field(default=None, ge=0)
    losses: int | None = Field(default=None, ge=0)
    goals_for: int | None = Field(default=None, ge=0)
    goals_against: int | None = Field(default=None, ge=0)
    points: int | None = Field(default=None, ge=0)
