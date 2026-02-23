"""Parser for Deloitte Money League revenue data from Wikipedia.

Scrapes https://en.wikipedia.org/wiki/Deloitte_Football_Money_League for club revenue data.
"""

import json
import logging
import re
from io import StringIO
from pathlib import Path

import httpx
import pandas as pd
from bs4 import BeautifulSoup

from dataflow.football.schemas.deloitte import ClubFinanceRecord

logger = logging.getLogger(__name__)

WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/Deloitte_Football_Money_League"


class DeloitteParser:
    """Parser for Deloitte Money League data from Wikipedia."""

    def __init__(self, data_root: Path) -> None:
        """Initialize parser.

        Args:
            data_root: Path to data root (for cache and mapping files)
        """
        self.data_root = Path(data_root)
        self.cache_dir = self.data_root / "deloitte"
        self.cache_file = self.cache_dir / "wikipedia_cache.html"
        self.mapping_file = self.cache_dir / "club_name_mapping.json"

    def _fetch_html(self) -> str:
        """Fetch Wikipedia HTML, using local cache if available.

        Returns:
            HTML content as string
        """
        # Return cached version if it exists
        if self.cache_file.exists():
            logger.debug(f"Using cached Wikipedia HTML from {self.cache_file}")
            return self.cache_file.read_text()

        # Fetch from Wikipedia
        logger.info(f"Fetching {WIKIPEDIA_URL}...")
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"  # noqa: E501
            }
            response = httpx.get(
                WIKIPEDIA_URL, headers=headers, follow_redirects=True, timeout=30.0
            )
            response.raise_for_status()
            html = response.text

            # Cache locally
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.cache_file.write_text(html)
            logger.info(f"Cached Wikipedia HTML to {self.cache_file}")

            return html
        except Exception as e:
            logger.error(f"Failed to fetch Wikipedia page: {e}")
            raise

    def _load_mapping(self) -> dict[str, str]:
        """Load club name → club_id mapping from JSON.

        Returns:
            Mapping dict. Empty dict if file not found.
        """
        if not self.mapping_file.exists():
            logger.warning(f"Club name mapping not found at {self.mapping_file}")
            return {}

        try:
            return json.loads(self.mapping_file.read_text())
        except Exception as e:
            logger.error(f"Failed to load club mapping: {e}")
            return {}

    def _extract_season(self, heading_text: str) -> int | None:
        """Extract season year from section heading.

        Handles patterns like:
        - "2025 (29th edition)" → 2025-2 = 2023 (season 2023/24)
        - "2023-24" or "2023/24" → 2023 (season 2023/24)

        Args:
            heading_text: Wikipedia heading text

        Returns:
            Season start year, or None if not found
        """
        # First try season range pattern (e.g., "2023-24" or "2023/24")
        season_range = re.search(r"(20\d{2})[-/]", heading_text)
        if season_range:
            try:
                return int(season_range.group(1))
            except ValueError:
                pass

        # Then try edition year pattern (e.g., "2025 edition")
        edition_year = re.search(r"(20\d{2}|199\d)", heading_text)
        if edition_year:
            try:
                year = int(edition_year.group(1))
                # Edition year is 2 years after season start
                # (2025 edition covers 2023/24 season → season 2023)
                return year - 2
            except ValueError:
                pass

        return None

    def _normalize_club_name(self, raw: str) -> str:
        """Normalize club name by stripping footnotes and extra whitespace.

        Args:
            raw: Raw club name from Wikipedia table

        Returns:
            Normalized name
        """
        # Remove footnote markers like [1], [a], etc.
        cleaned = re.sub(r"\[\w+\]", "", str(raw))
        # Strip extra whitespace
        return cleaned.strip()

    def _parse_revenue_eur(self, value: str) -> int | None:
        """Parse revenue value from table cell.

        Wikipedia shows revenue in €m. Convert to EUR integer.
        E.g., "659.9" → 659,900,000 EUR (multiply by 1,000,000)

        Args:
            value: Revenue value (e.g., "659.9" or "1,042.3")

        Returns:
            Revenue in EUR as integer, or None if unparseable
        """
        try:
            # Remove any non-numeric characters except decimal point
            clean = re.sub(r"[^\d.]", "", str(value))
            if not clean:
                return None
            # Convert from €m to EUR integer
            return int(float(clean) * 1_000_000)
        except (ValueError, TypeError):
            return None

    def _find_tables_with_seasons(
        self, html: str
    ) -> list[tuple[int, BeautifulSoup]]:
        """Find all revenue tables and associate with their season years.

        Walks DOM to pair section headings with following tables.

        Args:
            html: HTML content

        Returns:
            List of (season_year, table_soup) tuples
        """
        soup = BeautifulSoup(html, "lxml")
        tables_with_seasons: list[tuple[int, BeautifulSoup]] = []

        # Find all heading tags (h2, h3)
        for heading in soup.find_all(["h2", "h3"]):
            heading_text = heading.get_text()

            # Skip non-revenue sections
            if (
                "ranking" in heading_text.lower()
                or "summary" in heading_text.lower()
                or "contents" in heading_text.lower()
                or "see also" in heading_text.lower()
                or "reference" in heading_text.lower()
            ):
                continue

            # Try to extract season from heading
            season = self._extract_season(heading_text)
            if season is None:
                continue

            # Find next table after this heading
            next_table = heading.find_next("table")
            if next_table is not None:
                tables_with_seasons.append((season, next_table))

        logger.info(f"Found {len(tables_with_seasons)} revenue tables in Wikipedia")
        return tables_with_seasons

    def _parse_table(
        self, season: int, table_soup: BeautifulSoup, mapping: dict[str, str]
    ) -> list[ClubFinanceRecord]:
        """Parse a single revenue table.

        Args:
            season: Season year for this table
            table_soup: BeautifulSoup table element
            mapping: Club name → club_id mapping

        Returns:
            List of ClubFinanceRecord
        """
        records: list[ClubFinanceRecord] = []

        try:
            # Convert table to HTML string and parse with pandas
            table_html = str(table_soup)
            df_list = pd.read_html(StringIO(table_html))
            if not df_list:
                logger.debug(f"No dataframes found in table for season {season}")
                return records

            df = df_list[0]
            logger.debug(
                f"Parsed season {season} table: {df.shape[0]} rows, columns: {df.columns.tolist()}"
            )

            # Normalize column names to lowercase
            df.columns = [str(col).lower() for col in df.columns]

            # Find club and revenue columns
            club_col = None
            revenue_col = None

            for col in df.columns:
                if "club" in col:
                    club_col = col
                    break
            # If no club column found, try second column (often club name)
            if club_col is None and len(df.columns) > 1:
                club_col = df.columns[1]

            for col in df.columns:
                if "revenue" in col or "income" in col:
                    revenue_col = col
                    break

            if club_col is None or revenue_col is None:
                logger.warning(
                    f"Season {season}: Could not find club/revenue columns. "
                    f"Columns: {list(df.columns)}"
                )
                return records

            # Parse each row
            unmatched_clubs: set[str] = set()

            for _, row in df.iterrows():
                try:
                    club_name_raw = row[club_col]
                    revenue_raw = row[revenue_col]

                    if pd.isna(club_name_raw) or pd.isna(revenue_raw):
                        continue

                    # Normalize club name
                    club_name = self._normalize_club_name(club_name_raw)
                    if not club_name:
                        continue

                    # Look up club_id in mapping
                    club_id = mapping.get(club_name)
                    if club_id is None:
                        unmatched_clubs.add(club_name)
                        continue

                    # Parse revenue
                    revenue_eur = self._parse_revenue_eur(revenue_raw)

                    # Create record
                    record = ClubFinanceRecord(
                        club_id=club_id,
                        club_name=club_name,
                        season=season,
                        revenue_eur=revenue_eur,
                        operating_profit_eur=None,
                    )
                    records.append(record)

                except Exception as e:
                    logger.debug(f"Failed to parse row in season {season}: {e}")

            if unmatched_clubs:
                logger.warning(
                    f"Season {season}: {len(unmatched_clubs)} unmatched clubs: "
                    f"{sorted(unmatched_clubs)}"
                )

            logger.info(f"Season {season}: Parsed {len(records)} club records")

        except Exception as e:
            logger.warning(f"Failed to parse season {season} table: {e}")

        return records

    def parse(self) -> list[ClubFinanceRecord]:
        """Parse Deloitte Money League data from Wikipedia.

        Returns:
            List of ClubFinanceRecord
        """
        logger.info("Starting Deloitte Money League parser...")

        try:
            # Load mapping
            mapping = self._load_mapping()
            if not mapping:
                logger.warning(
                    "No club name mapping available. Cannot parse without mapping."
                )
                return []

            # Fetch HTML
            html = self._fetch_html()

            # Find tables
            tables_with_seasons = self._find_tables_with_seasons(html)
            if not tables_with_seasons:
                logger.warning("No revenue tables found in Wikipedia page")
                return []

            # Parse each table
            all_records: list[ClubFinanceRecord] = []
            for season, table_soup in tables_with_seasons:
                records = self._parse_table(season, table_soup, mapping)
                all_records.extend(records)

            logger.info(
                f"Deloitte parser completed: {len(all_records)} total club records"
            )
            return all_records

        except Exception as e:
            logger.error(f"Deloitte parser failed: {e}")
            if logger.isEnabledFor(logging.DEBUG):
                import traceback

                traceback.print_exc()
            return []
