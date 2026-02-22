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
    load_leagues,
    load_clubs,
    load_players,
    load_player_market_values,
    load_transfers,
    load_club_seasons,
    load_mls_salaries,
)
from dataflow.football.parsers import (  # noqa: E402
    SalimtParser,
    MLSPAParser,
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
            datalake_root = PROJECT_ROOT / "data" / "raw" / "football" / "salimt"
            salimt_parser = SalimtParser(datalake_root.parent)
            mlspa_parser = MLSPAParser(self.data_root)

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
