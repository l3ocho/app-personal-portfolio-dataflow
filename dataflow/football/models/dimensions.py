"""SQLAlchemy models for football dimension tables."""

from datetime import date

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

# Schema constant
RAW_FOOTBALL_SCHEMA = "raw_football"


class DimLeague(Base):
    """Football league dimension.

    Grain: One row per league (static).
    """

    __tablename__ = "dim_league"
    __table_args__ = {"schema": RAW_FOOTBALL_SCHEMA}

    league_id: Mapped[str] = mapped_column(String(10), primary_key=True, nullable=False)
    league_name: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(50), nullable=False)
    season_start_year: Mapped[int] = mapped_column(Integer, nullable=False)


class DimClub(Base):
    """Football club dimension.

    Grain: One row per club (static).
    All IDs are varchar (Transfermarkt string identifiers).
    Additional columns sourced from team_details.csv.
    """

    __tablename__ = "dim_club"
    __table_args__ = {"schema": RAW_FOOTBALL_SCHEMA}

    club_id: Mapped[str] = mapped_column(String(20), primary_key=True, nullable=False)
    club_name: Mapped[str] = mapped_column(String(150), nullable=False)
    club_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    country: Mapped[str | None] = mapped_column(String(50), nullable=True)
    founded_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    club_slug: Mapped[str | None] = mapped_column(String(150), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(255), nullable=True)


class DimPlayer(Base):
    """Football player dimension.

    Grain: One row per player (static).
    All IDs are varchar (Transfermarkt string identifiers).
    Height in cm, parsed from '1,85 m' or '1.80 m' formats.
    """

    __tablename__ = "dim_player"
    __table_args__ = {"schema": RAW_FOOTBALL_SCHEMA}

    player_id: Mapped[str] = mapped_column(String(20), primary_key=True, nullable=False)
    player_name: Mapped[str] = mapped_column(String(150), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(nullable=True)
    nationality: Mapped[str | None] = mapped_column(String(50), nullable=True)
    height_cm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    position: Mapped[str | None] = mapped_column(String(50), nullable=True)
    preferred_foot: Mapped[str | None] = mapped_column(String(10), nullable=True)
