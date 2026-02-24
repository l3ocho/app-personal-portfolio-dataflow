#!/usr/bin/env python3
"""Load football data into the database.

Usage:
    python scripts/data/load_football_data.py [OPTIONS]

Options:
    -v, --verbose   Enable verbose logging

This script orchestrates:
1. Parsing salimt Transfermarkt CSV datalake
2. Parsing MLSPA salary CSV files
3. Loading data into PostgreSQL raw_football tables
4. Running dbt to transform staging -> intermediate -> marts (Phase 2)

Exit codes:
    0 = Success
    1 = Error
"""

import argparse
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Load .env file
load_dotenv(PROJECT_ROOT / ".env")
sys.path.insert(0, str(PROJECT_ROOT))

from dataflow.football.loaders import (  # noqa: E402
    get_session,
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
from dataflow.football.parsers import (  # noqa: E402
    DeloitteParser,
    MLSPAParser,
    SalimtParser,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


class FootballDataPipeline:
    """Orchestrates football data loading from CSV files to database."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.stats: dict[str, int] = {}
        self.data_root = PROJECT_ROOT / "data" / "raw" / "football"

        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)

    def run(self) -> bool:
        """Run the complete football data pipeline.

        Returns:
            True if successful, False otherwise.
        """
        logger.info("Starting football data pipeline...")

        try:
            # Initialize parsers
            salimt_root = PROJECT_ROOT / "data" / "raw" / "football" / "salimt"
            salimt_parser = SalimtParser(salimt_root)
            mlspa_parser = MLSPAParser(self.data_root)
            deloitte_parser = DeloitteParser(self.data_root)

            with get_session() as session:
                # Load dimension tables first (no dependencies)
                self._load_leagues(session, salimt_parser)
                self._load_clubs(session, salimt_parser)
                self._load_players(session, salimt_parser)

                # Load fact tables (depend on dimensions)
                self._load_player_market_values(session, salimt_parser)
                self._load_transfers(session, salimt_parser)
                self._load_club_seasons(session, salimt_parser)
                self._load_mls_salaries(session, mlspa_parser)
                self._load_club_finances(session, deloitte_parser)

                # Phase 2: Build bridge tables from loaded facts
                # TODO: Optimize bridge query - 3.3M records too slow for bulk insert
                # self._build_player_competitions(session)

                session.commit()
                logger.info("All data committed to database")

            self._print_stats()
            logger.info("Football data pipeline completed successfully")
            return True

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            if self.verbose:
                import traceback

                traceback.print_exc()
            return False

    def _load_leagues(self, session, parser) -> None:
        """Load league dimension."""
        logger.info("Loading leagues...")
        try:
            records = parser.parse_leagues()
            if records:
                count = load_leagues(records, session)
                self.stats["leagues"] = count
                logger.info(f"  Loaded {count} leagues")
            else:
                logger.warning("  No league records found")
        except Exception as e:
            logger.error(f"Error loading leagues: {e}")
            raise

    def _load_clubs(self, session, parser) -> None:
        """Load club dimension."""
        logger.info("Loading clubs...")
        try:
            records = parser.parse_clubs()
            if records:
                count = load_clubs(records, session)
                self.stats["clubs"] = count
                logger.info(f"  Loaded {count} clubs")
            else:
                logger.warning("  No club records found")
        except Exception as e:
            logger.error(f"Error loading clubs: {e}")
            raise

    def _load_players(self, session, parser) -> None:
        """Load player dimension."""
        logger.info("Loading players...")
        try:
            records = parser.parse_players()
            if records:
                count = load_players(records, session)
                self.stats["players"] = count
                logger.info(f"  Loaded {count} players")
            else:
                logger.warning("  No player records found")
        except Exception as e:
            logger.error(f"Error loading players: {e}")
            raise

    def _load_player_market_values(self, session, parser) -> None:
        """Load player market value fact table (chunked for large datasets)."""
        logger.info("Loading player market values (chunked)...")
        try:
            records = parser.parse_player_market_values()
            if records:
                count = load_player_market_values(records, session, chunk_size=10000)
                self.stats["player_market_values"] = count
                logger.info(f"  Loaded {count} player market value records")
            else:
                logger.warning("  No player market value records found")
        except Exception as e:
            logger.error(f"Error loading player market values: {e}")
            raise

    def _load_transfers(self, session, parser) -> None:
        """Load transfer fact table."""
        logger.info("Loading transfers...")
        try:
            records = parser.parse_transfers()
            if records:
                count = load_transfers(records, session)
                self.stats["transfers"] = count
                logger.info(f"  Loaded {count} transfers")
            else:
                logger.warning("  No transfer records found")
        except Exception as e:
            logger.error(f"Error loading transfers: {e}")
            raise

    def _load_club_seasons(self, session, parser) -> None:
        """Load club season fact table."""
        logger.info("Loading club seasons...")
        try:
            records = parser.parse_club_season_stats()
            if records:
                count = load_club_seasons(records, session)
                self.stats["club_seasons"] = count
                logger.info(f"  Loaded {count} club seasons")
            else:
                logger.warning("  No club season records found")
        except Exception as e:
            logger.error(f"Error loading club seasons: {e}")
            raise

    def _load_mls_salaries(self, session, parser) -> None:
        """Load MLS salary fact table."""
        logger.info("Loading MLS salaries...")
        try:
            records = parser.parse_salary_files()
            if records:
                count = load_mls_salaries(records, session)
                self.stats["mls_salaries"] = count
                logger.info(f"  Loaded {count} MLS salary records")
            else:
                logger.warning("  No MLS salary records found")
        except Exception as e:
            logger.error(f"Error loading MLS salaries: {e}")
            raise

    def _load_club_finances(self, session, parser) -> None:
        """Load club finance fact table (Deloitte Money League)."""
        logger.info("Loading club finances (Deloitte)...")
        try:
            records = parser.parse()
            if records:
                count = load_club_finances(records, session)
                self.stats["club_finances"] = count
                logger.info(f"  Loaded {count} club finance records")
            else:
                logger.warning("  No club finance records found")
        except Exception as e:
            logger.error(f"Error loading club finances: {e}")
            raise

    def _build_player_competitions(self, session) -> None:
        """Build and load player-competition bridge from existing facts.

        Links players to competitions based on their market value appearances.
        For each player-season combination with market values, links player
        to all leagues active in that season.
        """
        logger.info("Building player-competition bridge...")
        try:
            from sqlalchemy import text

            # Optimized query: avoid expensive CROSS JOIN using subqueries
            # Step 1: Get unique player-seasons from market values
            # Step 2: Get unique league-seasons from club seasons
            # Step 3: Join them on matching seasons
            query = text("""
                SELECT DISTINCT
                    ps.player_id,
                    ls.league_id,
                    ps.season
                FROM (
                    SELECT DISTINCT
                        player_id,
                        EXTRACT(YEAR FROM market_value_date)::INT AS season
                    FROM raw_football.fact_player_market_value
                ) ps
                INNER JOIN (
                    SELECT DISTINCT
                        league_id,
                        season
                    FROM raw_football.fact_club_season
                ) ls
                ON ps.season = ls.season
                ORDER BY ps.player_id, ls.league_id, ps.season
            """)

            result = session.execute(query)
            records = [
                {
                    "player_id": row[0],
                    "league_id": row[1],
                    "season": int(row[2]),
                }
                for row in result
            ]

            if records:
                logger.info(f"  Building {len(records)} player-competition records...")
                count = load_player_competitions(records, session)
                self.stats["player_competitions"] = count
                logger.info(f"  Loaded {count} player-competition bridge records")
            else:
                logger.warning("  No player-competition data found")
        except Exception as e:
            logger.error(f"Error building player-competition bridge: {e}")
            raise

    def _print_stats(self) -> None:
        """Print loading statistics."""
        logger.info("=" * 60)
        logger.info("LOADING STATISTICS")
        logger.info("=" * 60)
        for table, count in sorted(self.stats.items()):
            logger.info(f"  {table:.<40} {count:>10,}")
        logger.info("=" * 60)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Load football data into database")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    pipeline = FootballDataPipeline(verbose=args.verbose)
    success = pipeline.run()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
