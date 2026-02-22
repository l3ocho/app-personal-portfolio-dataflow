"""Loaders for football data to raw_football schema."""

from .base import get_session, bulk_insert, upsert_by_key
from .loaders import (
    load_leagues,
    load_clubs,
    load_players,
    load_player_market_values,
    load_transfers,
    load_club_seasons,
    load_mls_salaries,
    load_club_finances,
    load_player_competitions,
)

__all__ = [
    "get_session",
    "bulk_insert",
    "upsert_by_key",
    "load_leagues",
    "load_clubs",
    "load_players",
    "load_player_market_values",
    "load_transfers",
    "load_club_seasons",
    "load_mls_salaries",
    "load_club_finances",
    "load_player_competitions",
]
