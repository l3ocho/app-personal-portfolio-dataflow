"""SQLAlchemy models for football fact tables."""

from datetime import date

from sqlalchemy import Date, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .dimensions import RAW_FOOTBALL_SCHEMA


class FactPlayerMarketValue(Base):
    """Player market value fact table.

    Grain: One row per player per market value snapshot date.
    Note: Can contain millions of rows. Loaded in chunks.
    """

    __tablename__ = "fact_player_market_value"
    __table_args__ = (
        Index("ix_fact_pmv_player_date", "player_id", "market_value_date"),
        Index("ix_fact_pmv_club", "club_id"),
        Index("ix_fact_pmv_season", "season"),
        {"schema": RAW_FOOTBALL_SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[str] = mapped_column(String(20), nullable=False)
    club_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    value_eur: Mapped[int | None] = mapped_column(Integer, nullable=True)
    market_value_date: Mapped[date] = mapped_column(Date, nullable=False)
    season: Mapped[int | None] = mapped_column(Integer, nullable=True)


class FactTransfer(Base):
    """Transfer history fact table.

    Grain: One row per transfer event.
    Handles multiple fee formats: '€12.5m', 'free transfer', 'Loan', '?', '-', None
    Unparseable values set fee_eur=NULL, is_loan=False
    """

    __tablename__ = "fact_transfer"
    __table_args__ = (
        Index("ix_fact_transfer_player_date", "player_id", "transfer_date"),
        Index("ix_fact_transfer_from_club", "from_club_id"),
        Index("ix_fact_transfer_to_club", "to_club_id"),
        Index("ix_fact_transfer_season", "season"),
        {"schema": RAW_FOOTBALL_SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[str] = mapped_column(String(20), nullable=False)
    from_club_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    to_club_id: Mapped[str] = mapped_column(String(20), nullable=False)
    transfer_date: Mapped[date] = mapped_column(Date, nullable=False)
    fee_eur: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_loan: Mapped[bool] = mapped_column(default=False)
    season: Mapped[int | None] = mapped_column(Integer, nullable=True)


class FactClubSeason(Base):
    """Club season statistics fact table.

    Grain: One row per club per league per season.
    E.g., final league position, points, goals.
    """

    __tablename__ = "fact_club_season"
    __table_args__ = (
        Index("ix_fact_cs_club_season", "club_id", "season"),
        Index("ix_fact_cs_league_season", "league_id", "season"),
        {"schema": RAW_FOOTBALL_SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    club_id: Mapped[str] = mapped_column(String(20), nullable=False)
    league_id: Mapped[str] = mapped_column(String(10), nullable=False)
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    matches_played: Mapped[int | None] = mapped_column(Integer, nullable=True)
    wins: Mapped[int | None] = mapped_column(Integer, nullable=True)
    draws: Mapped[int | None] = mapped_column(Integer, nullable=True)
    losses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    goals_for: Mapped[int | None] = mapped_column(Integer, nullable=True)
    goals_against: Mapped[int | None] = mapped_column(Integer, nullable=True)
    points: Mapped[int | None] = mapped_column(Integer, nullable=True)


class FactMLSSalary(Base):
    """MLS player salary fact table.

    Grain: One row per player per MLS club per season.
    """

    __tablename__ = "fact_mls_salary"
    __table_args__ = (
        Index("ix_fact_mls_player_season", "player_id", "season"),
        Index("ix_fact_mls_club_season", "club_id", "season"),
        {"schema": RAW_FOOTBALL_SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[str] = mapped_column(String(20), nullable=False)
    player_name: Mapped[str] = mapped_column(String(150), nullable=False)
    club_id: Mapped[str] = mapped_column(String(20), nullable=False)
    club_name: Mapped[str] = mapped_column(String(100), nullable=False)
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    salary_usd: Mapped[int | None] = mapped_column(Integer, nullable=True)
    guaranteed_compensation_usd: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )


class FactClubFinance(Base):
    """Club annual revenue fact table (Deloitte Money League).

    Grain: One row per club per season.
    Note: Stub for Phase 2+ implementation. PDF extraction skipped in Phase 1.
    """

    __tablename__ = "fact_club_finance"
    __table_args__ = (
        Index("ix_fact_cf_club_season", "club_id", "season"),
        {"schema": RAW_FOOTBALL_SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    club_id: Mapped[str] = mapped_column(String(20), nullable=False)
    club_name: Mapped[str] = mapped_column(String(150), nullable=False)
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    revenue_eur: Mapped[int | None] = mapped_column(Integer, nullable=True)
    operating_profit_eur: Mapped[int | None] = mapped_column(Integer, nullable=True)


class BridgePlayerCompetition(Base):
    """Bridge table for player-to-competition (league) participation.

    Grain: One row per player per league per season.
    Enables tracking which players appeared in which competitions.
    """

    __tablename__ = "bridge_player_competition"
    __table_args__ = (
        Index("ix_bridge_pc_player_season", "player_id", "season"),
        Index("ix_bridge_pc_league_season", "league_id", "season"),
        {"schema": RAW_FOOTBALL_SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[str] = mapped_column(String(20), nullable=False)
    league_id: Mapped[str] = mapped_column(String(10), nullable=False)
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    appearances: Mapped[int | None] = mapped_column(Integer, nullable=True)
    goals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    assists: Mapped[int | None] = mapped_column(Integer, nullable=True)
