"""Loaders for football data to raw_football schema."""

from .base import bulk_insert, get_session, upsert_by_key
from .loaders import (
    load_club_finances,
    load_club_seasons,
    load_clubs,
    load_leagues,
    load_mls_salaries,
    load_player_competitions,
    load_player_market_values,
    load_players,
    load_transfers,
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
