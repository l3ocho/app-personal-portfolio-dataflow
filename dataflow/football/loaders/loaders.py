"""Loaders for football domain tables."""

import logging
from sqlalchemy.orm import Session

from dataflow.football.models import (
    DimLeague,
    DimClub,
    DimPlayer,
    FactPlayerMarketValue,
    FactTransfer,
    FactClubSeason,
    FactMLSSalary,
    FactClubFinance,
    BridgePlayerCompetition,
)
from dataflow.football.schemas.salimt import (
    LeagueRecord,
    ClubRecord,
    PlayerRecord,
    PlayerMarketValueRecord,
    TransferHistoryRecord,
    ClubSeasonRecord,
)
from dataflow.football.schemas.mlspa import MLSPASalaryRecord
from dataflow.football.schemas.deloitte import ClubFinanceRecord

from .base import get_session, bulk_insert, upsert_by_key

logger = logging.getLogger(__name__)


def load_leagues(
    records: list[LeagueRecord],
    session: Session | None = None,
) -> int:
    """Load league records to dim_league table (upsert for idempotency)."""

    def _load(sess: Session) -> int:
        models = [
            DimLeague(
                league_id=r.league_id,
                league_name=r.league_name,
                country=r.country,
                season_start_year=r.season_start_year,
            )
            for r in records
        ]
        # Use upsert_by_key so ETL can run idempotently when Phase 1 data exists
        inserted, updated = upsert_by_key(sess, DimLeague, models, ["league_id"])
        logger.info(f"Leagues: {inserted} inserted, {updated} updated")
        return inserted + updated

    if session:
        return _load(session)
    with get_session() as sess:
        return _load(sess)


def load_clubs(
    records: list[ClubRecord],
    session: Session | None = None,
) -> int:
    """Load club records to dim_club table (upsert for idempotency)."""

    def _load(sess: Session) -> int:
        models = [
            DimClub(
                club_id=r.club_id,
                club_name=r.club_name,
                country=r.country,
                club_slug=r.club_slug,
                logo_url=r.logo_url,
                source_url=r.source_url,
            )
            for r in records
        ]
        # Use upsert_by_key so ETL can run idempotently when Phase 1 data exists
        inserted, updated = upsert_by_key(sess, DimClub, models, ["club_id"])
        logger.info(f"Clubs: {inserted} inserted, {updated} updated")
        return inserted + updated

    if session:
        return _load(session)
    with get_session() as sess:
        return _load(sess)


def load_players(
    records: list[PlayerRecord],
    session: Session | None = None,
) -> int:
    """Load player records to dim_player table (upsert for idempotency)."""

    def _load(sess: Session) -> int:
        models = [
            DimPlayer(
                player_id=r.player_id,
                player_name=r.player_name,
                date_of_birth=r.date_of_birth,
                nationality=r.nationality,
                height_cm=r.height_cm,
                position=r.position,
                preferred_foot=r.preferred_foot,
            )
            for r in records
        ]
        # Use upsert_by_key so ETL can run idempotently when Phase 1 data exists
        inserted, updated = upsert_by_key(sess, DimPlayer, models, ["player_id"])
        logger.info(f"Players: {inserted} inserted, {updated} updated")
        return inserted + updated

    if session:
        return _load(session)
    with get_session() as sess:
        return _load(sess)


def load_player_market_values(
    records: list[PlayerMarketValueRecord],
    session: Session | None = None,
    chunk_size: int = 10000,
) -> int:
    """Load player market value records to fact_player_market_value table.

    Note: Can contain millions of rows. Loaded in chunks to manage memory.

    Args:
        records: List of PlayerMarketValueRecord schemas.
        session: Optional existing session.
        chunk_size: Number of records per chunk (default 10k).

    Returns:
        Total number of records loaded.
    """

    def _load(sess: Session) -> int:
        total = 0
        for i in range(0, len(records), chunk_size):
            chunk = records[i : i + chunk_size]
            models = [
                FactPlayerMarketValue(
                    player_id=r.player_id,
                    club_id=r.club_id,
                    value_eur=r.value_eur,
                    market_value_date=r.market_value_date,
                    season=r.season,
                )
                for r in chunk
            ]
            inserted, updated = upsert_by_key(
                sess, FactPlayerMarketValue, models, ["player_id", "market_value_date"]
            )
            loaded = inserted + updated
            total += loaded
            logger.info(f"Market values chunk {i//chunk_size + 1}: {loaded} records")

        return total

    if session:
        return _load(session)
    with get_session() as sess:
        return _load(sess)


def load_transfers(
    records: list[TransferHistoryRecord],
    session: Session | None = None,
) -> int:
    """Load transfer records to fact_transfer table."""

    def _load(sess: Session) -> int:
        models = [
            FactTransfer(
                player_id=r.player_id,
                from_club_id=r.from_club_id,
                to_club_id=r.to_club_id,
                transfer_date=r.transfer_date,
                fee_eur=r.fee_eur,
                is_loan=r.is_loan,
                season=r.season,
            )
            for r in records
        ]
        inserted, updated = upsert_by_key(
            sess, FactTransfer, models, ["player_id", "transfer_date", "to_club_id"]
        )
        logger.info(f"Transfers: {inserted} inserted, {updated} updated")
        return inserted + updated

    if session:
        return _load(session)
    with get_session() as sess:
        return _load(sess)


def load_club_seasons(
    records: list[ClubSeasonRecord],
    session: Session | None = None,
) -> int:
    """Load club season records to fact_club_season table."""

    def _load(sess: Session) -> int:
        models = [
            FactClubSeason(
                club_id=r.club_id,
                league_id=r.league_id,
                season=r.season,
                position=r.position,
                matches_played=r.matches_played,
                wins=r.wins,
                draws=r.draws,
                losses=r.losses,
                goals_for=r.goals_for,
                goals_against=r.goals_against,
                points=r.points,
            )
            for r in records
        ]
        inserted, updated = upsert_by_key(
            sess, FactClubSeason, models, ["club_id", "league_id", "season"]
        )
        logger.info(f"Club seasons: {inserted} inserted, {updated} updated")
        return inserted + updated

    if session:
        return _load(session)
    with get_session() as sess:
        return _load(sess)


def load_mls_salaries(
    records: list[MLSPASalaryRecord],
    session: Session | None = None,
) -> int:
    """Load MLS salary records to fact_mls_salary table."""

    def _load(sess: Session) -> int:
        models = [
            FactMLSSalary(
                player_id=r.player_id,
                player_name=r.player_name,
                club_id=r.club_id,
                club_name=r.club_name,
                season=r.season,
                salary_usd=r.salary_usd,
                guaranteed_compensation_usd=r.guaranteed_compensation_usd,
            )
            for r in records
        ]
        inserted, updated = upsert_by_key(
            sess, FactMLSSalary, models, ["player_id", "club_id", "season"]
        )
        logger.info(f"MLS salaries: {inserted} inserted, {updated} updated")
        return inserted + updated

    if session:
        return _load(session)
    with get_session() as sess:
        return _load(sess)


def load_club_finances(
    records: list[ClubFinanceRecord],
    session: Session | None = None,
) -> int:
    """Load club finance records to fact_club_finance table."""

    def _load(sess: Session) -> int:
        models = [
            FactClubFinance(
                club_id=r.club_id,
                club_name=r.club_name,
                season=r.season,
                revenue_eur=r.revenue_eur,
                operating_profit_eur=r.operating_profit_eur,
            )
            for r in records
        ]
        inserted, updated = upsert_by_key(
            sess, FactClubFinance, models, ["club_id", "season"]
        )
        logger.info(f"Club finances: {inserted} inserted, {updated} updated")
        return inserted + updated

    if session:
        return _load(session)
    with get_session() as sess:
        return _load(sess)


def load_player_competitions(
    records: list[dict],
    session: Session | None = None,
) -> int:
    """Load player-competition bridge records to bridge_player_competition table.

    Args:
        records: List of dicts with keys: player_id, league_id, season, appearances, goals, assists
        session: Optional existing session.

    Returns:
        Number of records loaded.
    """

    def _load(sess: Session) -> int:
        models = [
            BridgePlayerCompetition(
                player_id=r["player_id"],
                league_id=r["league_id"],
                season=r["season"],
                appearances=r.get("appearances"),
                goals=r.get("goals"),
                assists=r.get("assists"),
            )
            for r in records
        ]
        inserted, updated = upsert_by_key(
            sess, BridgePlayerCompetition, models, ["player_id", "league_id", "season"]
        )
        logger.info(f"Player competitions: {inserted} inserted, {updated} updated")
        return inserted + updated

    if session:
        return _load(session)
    with get_session() as sess:
        return _load(sess)
