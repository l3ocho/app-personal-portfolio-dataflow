"""Parser for salimt Transfermarkt-scraped football data.

Reads CSV files from datalake directory structure, filters to target leagues,
and handles type conversions for Transfermarkt data quirks.
"""

import contextlib
import logging
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from dataflow.football.schemas.salimt import (
    ClubRecord,
    ClubSeasonRecord,
    LeagueRecord,
    PlayerMarketValueRecord,
    PlayerRecord,
    TransferHistoryRecord,
)

logger = logging.getLogger(__name__)

# Target leagues for extraction
TARGET_LEAGUES = {"GB1", "ES1", "L1", "IT1", "FR1", "BRA1", "MLS1"}

# CSV file paths relative to datalake/transfermarkt/raw/
SALIMT_TABLES = {
    "leagues": "leagues/leagues.csv",
    "clubs": "clubs/clubs.csv",
    "players": "players/players.csv",
    "player_market_values": "player_market_values/player_market_values.csv",
    "transfers": "transfers/transfers.csv",
    "club_season_stats": "club_season_stats/club_season_stats.csv",
}


def parse_transfer_fee(fee_str: str | None) -> tuple[int | None, bool]:
    """Parse transfer fee string to EUR and loan flag.

    Handles: '€12.5m', '€500k', 'free transfer', 'Loan', '?', '-', None
    Returns: (fee_eur, is_loan)
    Unparseable values return (None, False)
    """
    if fee_str is None or fee_str == "" or fee_str == "-" or fee_str == "?":
        return None, False

    fee_str = fee_str.strip()

    if fee_str.lower() == "loan":
        return None, True

    if fee_str.lower() == "free transfer":
        return 0, False

    # Parse €X.Xm or €Xk format
    try:
        fee_str = fee_str.replace("€", "").strip()

        if fee_str.lower().endswith("m"):
            value = float(fee_str[:-1]) * 1_000_000
            return int(value), False
        elif fee_str.lower().endswith("k"):
            value = float(fee_str[:-1]) * 1_000
            return int(value), False
        else:
            return None, False
    except (ValueError, AttributeError):
        logger.warning(f"Could not parse transfer fee: {fee_str}")
        return None, False


def parse_date_unix(unix_timestamp: int | float | str | None) -> date | None:
    """Convert Unix timestamp or ISO date string to date.

    Args:
        unix_timestamp: Seconds since epoch, ISO date string, or None

    Returns:
        Parsed date or None if unparseable
    """
    if unix_timestamp is None:
        return None

    try:
        # Try ISO date format first (YYYY-MM-DD)
        if isinstance(unix_timestamp, str):
            return datetime.fromisoformat(unix_timestamp).date()
        # Try Unix timestamp
        return datetime.fromtimestamp(int(unix_timestamp)).date()
    except (ValueError, OSError, OverflowError, TypeError):
        logger.debug(f"Could not parse date: {unix_timestamp}")
        return None


def parse_height(height_str: str | None) -> int | None:
    """Parse height string to centimeters.

    Handles: '1,85 m', '1.80 m', '185', etc.
    Returns: Height in cm or None if unparseable
    """
    if height_str is None or height_str == "":
        return None

    try:
        height_str = str(height_str).strip()

        # Already in cm as int
        if height_str.isdigit():
            return int(height_str)

        # Remove ' m' suffix if present
        if height_str.lower().endswith(" m"):
            height_str = height_str[:-2].strip()

        # Replace comma with period (European format)
        height_str = height_str.replace(",", ".")

        # Parse as float meters and convert to cm
        height_m = float(height_str)
        height_cm = int(height_m * 100)

        return height_cm if 100 <= height_cm <= 250 else None
    except (ValueError, AttributeError):
        logger.warning(f"Could not parse height: {height_str}")
        return None


def parse_season(season_str: str | None) -> int | None:
    """Parse season string to start year.

    Handles: '23/24' → 2023, '2023/24' → 2023, '92/93' → 1992, etc.
    """
    if season_str is None or season_str == "":
        return None

    try:
        season_str = str(season_str).strip()
        start_year = season_str.split("/")[0]

        # If 2-digit year, expand using 30-year cutoff
        # 00-30 → 2000-2030, 31-99 → 1931-1999
        if len(start_year) == 2:
            year_int = int(start_year)
            if year_int <= 30:
                return 2000 + year_int
            else:
                return 1900 + year_int
        else:
            return int(start_year)
    except (ValueError, IndexError):
        logger.debug(f"Could not parse season: {season_str}")
        return None


class SalimtParser:
    """Parser for salimt Transfermarkt CSV datalake.

    Reads from datalake/transfermarkt/raw/{table}/{table}.csv
    Filters to TARGET_LEAGUES
    """

    def __init__(self, datalake_root: Path) -> None:
        """Initialize parser with datalake root directory.

        Args:
            datalake_root: Path to datalake/ directory or parent of salimt/ directory
        """
        datalake_root = Path(datalake_root)

        # Support both structures:
        # 1. If datalake_root points to salimt/, use that
        if (datalake_root / "datalake").exists():
            self.salimt_root = datalake_root / "datalake" / "transfermarkt"
        elif (datalake_root / "transfermarkt").exists():
            self.salimt_root = datalake_root / "transfermarkt"
        else:
            self.salimt_root = datalake_root

        self._validate_paths()

    def _validate_paths(self) -> None:
        """Validate that salimt directory structure exists."""
        if not self.salimt_root.exists():
            raise FileNotFoundError(
                f"Salimt datalake not found at {self.salimt_root}. "
                f"Expected structure: datalake/transfermarkt/ with table subdirectories"
            )

    def parse_leagues(self) -> list[LeagueRecord]:
        """Extract leagues from team_competitions_seasons.csv."""
        csv_path = (
            self.salimt_root
            / "team_competitions_seasons"
            / "team_competitions_seasons.csv"
        )
        if not csv_path.exists():
            logger.warning(f"Team competitions CSV not found at {csv_path}")
            return []

        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            logger.error(f"Error reading team_competitions_seasons: {e}")
            return []

        # Extract unique leagues using 'competition_id' column
        if "competition_id" not in df.columns:
            logger.warning(
                "'competition_id' column not found in team_competitions_seasons"
            )
            return []

        # Filter to target competitions
        df = df[df["competition_id"].isin(TARGET_LEAGUES)]

        # Get unique competition IDs (keep first occurrence of each)
        unique_leagues = df[["competition_id", "competition_name"]].drop_duplicates(
            subset=["competition_id"], keep="first"
        )

        # Map league IDs to countries
        league_countries = {
            "GB1": "England",
            "ES1": "Spain",
            "IT1": "Italy",
            "FR1": "France",
            "L1": "Germany",
            "BRA1": "Brazil",
            "MLS1": "United States",
        }

        records = []
        for _, row in unique_leagues.iterrows():
            try:
                comp_id = str(row.get("competition_id", ""))
                comp_name = str(row.get("competition_name", comp_id))
                record = LeagueRecord(
                    league_id=comp_id,
                    league_name=comp_name,
                    country=league_countries.get(comp_id, ""),
                    season_start_year=2023,
                )
                records.append(record)
            except Exception as e:
                logger.warning(f"Could not parse league {comp_id}: {e}")

        logger.info(
            f"Parsed {len(records)} unique leagues from competitions (filtered to {TARGET_LEAGUES})"
        )
        return records

    def parse_clubs(self) -> list[ClubRecord]:
        """Parse team_details.csv."""
        csv_path = self.salimt_root / "team_details" / "team_details.csv"
        if not csv_path.exists():
            logger.warning(f"Team details CSV not found at {csv_path}")
            return []

        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            logger.error(f"Error reading team_details: {e}")
            return []

        records = []

        for _, row in df.iterrows():
            try:
                record = ClubRecord(
                    club_id=str(row.get("club_id", "")),
                    club_name=str(row.get("club_name", "")),
                    club_code=None,  # Not in team_details.csv
                    country=row.get(
                        "country_name"
                    ),  # CSV has country_name, not country
                    founded_year=None,  # Not in team_details.csv
                    city=None,  # Not in team_details.csv
                    club_slug=row.get("club_slug"),
                    logo_url=row.get("logo_url"),
                    source_url=row.get("source_url"),
                )
                records.append(record)
            except Exception as e:
                logger.warning(f"Could not parse club row: {row.to_dict()}: {e}")

        logger.info(f"Parsed {len(records)} clubs")
        return records

    def parse_players(self) -> list[PlayerRecord]:
        """Parse player_profiles.csv with height conversion."""
        csv_path = self.salimt_root / "player_profiles" / "player_profiles.csv"
        if not csv_path.exists():
            logger.warning(f"Player profiles CSV not found at {csv_path}")
            return []

        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            logger.error(f"Error reading player_profiles: {e}")
            return []

        records = []

        for _, row in df.iterrows():
            try:
                # Handle NaN values by converting to None
                import pandas as pd_lib

                dob = row.get("date_of_birth")
                if pd_lib.isna(dob):
                    dob = None
                nationality = row.get("citizenship")
                if pd_lib.isna(nationality):
                    nationality = None
                pref_foot = row.get("foot")
                if pd_lib.isna(pref_foot):
                    pref_foot = None
                position = row.get("position")
                if pd_lib.isna(position):
                    position = None

                record = PlayerRecord(
                    player_id=str(row.get("player_id", "")),
                    player_name=str(row.get("player_name", "")),
                    date_of_birth=dob,
                    nationality=nationality,
                    height_cm=parse_height(row.get("height")),
                    position=position,
                    preferred_foot=pref_foot,
                )
                records.append(record)
            except Exception as e:
                logger.debug(f"Could not parse player: {e}")

        logger.info(f"Parsed {len(records)} players")
        return records

    def _build_player_club_mapping(self) -> dict[str, str | None]:
        """Build player_id -> current_club_id mapping from player_profiles.csv.

        Returns:
            Dictionary mapping player_id (str) to current_club_id (str or None)
        """
        csv_path = self.salimt_root / "player_profiles" / "player_profiles.csv"
        if not csv_path.exists():
            logger.warning(
                f"Player profiles CSV not found for club mapping at {csv_path}"
            )
            return {}

        try:
            df = pd.read_csv(csv_path, usecols=["player_id", "current_club_id"])
        except Exception as e:
            logger.error(f"Error reading player_profiles for club mapping: {e}")
            return {}

        mapping = {}
        for _, row in df.iterrows():
            player_id = str(row.get("player_id", ""))
            club_id = row.get("current_club_id")
            # Convert to string if present, keep None if missing
            club_id = str(club_id) if pd.notna(club_id) else None
            mapping[player_id] = club_id

        logger.info(
            f"Built player-club mapping with {len(mapping)} entries ({sum(1 for v in mapping.values() if v is not None)} with clubs)"
        )
        return mapping

    def parse_player_market_values(self) -> list[PlayerMarketValueRecord]:
        """Parse player_market_value.csv with date_unix conversion and club_id mapping.

        Populates club_id from player_profiles.csv current_club_id.
        Note: Can return millions of rows. Call with chunking if needed.
        """
        csv_path = self.salimt_root / "player_market_value" / "player_market_value.csv"
        if not csv_path.exists():
            logger.warning(f"Player market value CSV not found at {csv_path}")
            return []

        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            logger.error(f"Error reading player_market_value: {e}")
            return []

        # Build player-club mapping for lookup
        logger.info("Building player-club mapping from profiles...")
        player_club_mapping = self._build_player_club_mapping()

        records = []
        row_count = 0

        for _, row in df.iterrows():
            row_count += 1
            try:
                market_value_date = parse_date_unix(row.get("date_unix"))
                if market_value_date is None:
                    continue

                # Parse value (may be float, convert to int)
                value_eur = None
                raw_value = row.get("value")
                if raw_value is not None:
                    with contextlib.suppress(ValueError, TypeError):
                        value_eur = int(float(raw_value))

                # Extract season from market_value_date year
                season = None
                if market_value_date:
                    season = market_value_date.year

                # Look up club_id from player_profiles mapping
                player_id = str(row.get("player_id", ""))
                club_id = player_club_mapping.get(player_id)

                record = PlayerMarketValueRecord(
                    player_id=player_id,
                    club_id=club_id,
                    value_eur=value_eur,
                    market_value_date=market_value_date,
                    season=season,
                )
                records.append(record)

                if row_count % 100000 == 0:
                    logger.info(f"  Parsed {row_count} market value records...")
            except Exception as e:
                logger.debug(f"Could not parse market value row {row_count}: {e}")

        logger.info(f"Parsed {len(records)} player market values total")
        return records

    def parse_transfers(self) -> list[TransferHistoryRecord]:
        """Parse transfer_history.csv with fee parsing.

        Note: transfer_history.csv is stored in Git LFS and may not be available.
        """
        csv_path = self.salimt_root / "transfer_history" / "transfer_history.csv"
        if not csv_path.exists():
            logger.warning(f"Transfer history CSV not found at {csv_path}")
            return []

        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            logger.error(f"Error reading transfer_history: {e}")
            return []

        records = []

        for _, row in df.iterrows():
            try:
                transfer_date = row.get("transfer_date")
                # Skip rows with missing transfer_date (e.g., Git LFS pointer files)
                if transfer_date is None or (
                    isinstance(transfer_date, float) and transfer_date != transfer_date
                ):  # NaN check
                    continue

                fee_eur, is_loan = parse_transfer_fee(row.get("transfer_fee"))

                record = TransferHistoryRecord(
                    player_id=str(row.get("player_id", "")),
                    from_club_id=row.get("from_club_id"),
                    to_club_id=str(row.get("to_club_id", "")),
                    transfer_date=transfer_date,
                    fee_eur=fee_eur,
                    is_loan=is_loan,
                    season=parse_season(row.get("season")),
                )
                records.append(record)
            except Exception as e:
                logger.debug(f"Could not parse transfer row: {e}")

        logger.info(f"Parsed {len(records)} transfers")
        return records

    def parse_club_season_stats(self) -> list[ClubSeasonRecord]:
        """Parse team_competitions_seasons.csv for club season stats."""
        csv_path = (
            self.salimt_root
            / "team_competitions_seasons"
            / "team_competitions_seasons.csv"
        )
        if not csv_path.exists():
            logger.warning(f"Team competitions CSV not found at {csv_path}")
            return []

        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            logger.error(f"Error reading team_competitions_seasons: {e}")
            return []

        # Filter to target leagues only
        df = df[df["competition_id"].isin(TARGET_LEAGUES)]

        records = []

        def _int_or_none(val) -> int | None:
            """Convert pandas NaN/None to None, otherwise int."""
            if val is None:
                return None
            try:
                if pd.isna(val):
                    return None
            except (TypeError, ValueError):
                pass
            return int(val)

        for _, row in df.iterrows():
            try:
                record = ClubSeasonRecord(
                    club_id=str(row.get("club_id", "")),
                    league_id=str(row.get("competition_id", "")),
                    season=parse_season(row.get("season_season")),
                    position=_int_or_none(row.get("season_rank")),
                    matches_played=_int_or_none(row.get("season_total_matches")),
                    wins=_int_or_none(row.get("season_wins")),
                    draws=_int_or_none(row.get("season_draws")),
                    losses=_int_or_none(row.get("season_losses")),
                    goals_for=_int_or_none(row.get("season_goals_for")),
                    goals_against=_int_or_none(row.get("season_goals_against")),
                    points=_int_or_none(row.get("season_points")),
                )
                records.append(record)
            except Exception as e:
                logger.debug(f"Could not parse club season row: {e}")

        logger.info(
            f"Parsed {len(records)} club seasons (from {len(TARGET_LEAGUES)} target leagues)"
        )
        return records
