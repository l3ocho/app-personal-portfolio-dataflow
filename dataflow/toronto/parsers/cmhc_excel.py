"""Parser for CMHC Excel files (RMR - Rental Market Reports).

Extracts rental market data from CMHC Excel files including:
- Table 3.1.3: Universe (total rental units) by zone and bedroom type
- Table 3.1.1: Vacancy rates by zone and bedroom type
- Table 3.1.2: Average rents by zone and bedroom type
- Table 3.1.5: % change in average rent by zone and bedroom type
- Table 3.1.6: Turnover rates by zone and bedroom type

These Excel files are published annually by CMHC and contain detailed
zone-level data not available through the StatCan API.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class CMHCUniverseRecord:
    """Universe (total rental units) record from CMHC Excel file."""

    year: int
    zone_code: str
    zone_name: str
    bedroom_type: str
    universe: int


@dataclass
class CMHCExcelRentalRecord:
    """Full rental market record from CMHC Excel file.

    Combines data from multiple RMR tables into a single record per
    zone, bedroom type, and year. Fields not available in the Excel
    files (median_rent, availability_rate) are omitted.
    """

    year: int
    zone_code: str
    zone_name: str
    bedroom_type: str
    universe: int | None = None
    avg_rent: float | None = None
    avg_rent_reliability: str | None = None
    vacancy_rate: float | None = None
    turnover_rate: float | None = None
    rent_change_pct: float | None = None


class CMHCExcelParser:
    """Parser for CMHC Rental Market Report Excel files.

    CMHC publishes annual Rental Market Reports (RMR) as Excel files with
    multiple tables. This parser extracts:
    - Table 3.1.3: Universe (total rental units) by zone and bedroom type
    - Table 3.1.1: Vacancy rates
    - Table 3.1.2: Average rents (with reliability codes)
    - Table 3.1.5: % change in average rent
    - Table 3.1.6: Turnover rates

    File naming convention: rmr-toronto-{year}-en.xlsx
    """

    # Bedroom type mappings (handle both old and new formats)
    BEDROOM_MAP = {
        "Studio": "bachelor",  # Newer format (2025+)
        "Bachelor": "bachelor",  # Older format (2021-2024)
        "1 Bedroom": "1bed",
        "2 Bedroom": "2bed",
        "3 Bedroom +": "3bed",
    }

    def __init__(self, excel_path: Path) -> None:
        """Initialize parser with path to Excel file.

        Args:
            excel_path: Path to CMHC RMR Excel file (e.g., rmr-toronto-2025-en.xlsx).
        """
        self.excel_path = excel_path
        self.year = self._extract_year_from_filename()
        self._validate_path()

    def _validate_path(self) -> None:
        """Validate that the Excel path exists and is readable."""
        if not self.excel_path.exists():
            raise FileNotFoundError(f"Excel file not found: {self.excel_path}")
        if self.excel_path.suffix.lower() not in [".xlsx", ".xls"]:
            raise ValueError(
                f"Expected Excel file (.xlsx/.xls), got: {self.excel_path.suffix}"
            )

    def _extract_year_from_filename(self) -> int:
        """Extract year from filename (rmr-toronto-2025-en.xlsx -> 2025)."""
        stem = self.excel_path.stem  # "rmr-toronto-2025-en"
        parts = stem.split("-")
        for part in parts:
            if part.isdigit() and len(part) == 4:
                return int(part)
        raise ValueError(f"Could not extract year from filename: {self.excel_path.name}")

    def _find_header_row(self, df: pd.DataFrame) -> int | None:
        """Find the row index containing bedroom type headers.

        Args:
            df: DataFrame of a table sheet (read with header=None).

        Returns:
            Row index of the bedroom type header, or None if not found.
        """
        for idx in range(len(df)):
            row = df.iloc[idx]
            row_str = " ".join(str(val) for val in row if pd.notna(val))
            if ("Studio" in row_str or "Bachelor" in row_str) and "Bedroom" in row_str:
                logger.debug(f"Found header row at index {idx}")
                return idx
        return None

    def _find_bedroom_cols(self, df: pd.DataFrame, header_row_idx: int) -> dict[int, str]:
        """Extract bedroom type column positions from the header row.

        Args:
            df: DataFrame of a table sheet.
            header_row_idx: Row index of the bedroom type header.

        Returns:
            Dict mapping column index to bedroom type string.
        """
        header_row = df.iloc[header_row_idx]
        bedroom_cols: dict[int, str] = {}
        for col_idx in range(1, len(header_row)):
            val = header_row.iloc[col_idx]
            if pd.notna(val) and val in self.BEDROOM_MAP:
                bedroom_cols[col_idx] = self.BEDROOM_MAP[val]
        logger.debug(f"Found bedroom columns: {bedroom_cols}")
        return bedroom_cols

    def _parse_universe_table(self, df: pd.DataFrame) -> list[CMHCUniverseRecord]:
        """Parse Table 3.1.3 from DataFrame.

        Expected structure:
        - Row with "Studio" header (bedroom types)
        - Row with years (Oct-24, Oct-25)
        - Rows with zone names and universe values

        Args:
            df: DataFrame of the sheet containing Table 3.1.3.

        Returns:
            List of CMHCUniverseRecord objects.
        """
        records: list[CMHCUniverseRecord] = []

        header_row_idx = self._find_header_row(df)
        if header_row_idx is None:
            logger.warning(f"Could not find bedroom type header in {self.excel_path.name}")
            return records

        bedroom_cols = self._find_bedroom_cols(df, header_row_idx)
        data_start_idx = header_row_idx + 2  # skip header + year sub-header rows

        for idx in range(data_start_idx, len(df)):
            row = df.iloc[idx]
            zone_name = row.iloc[0]

            if pd.isna(zone_name):
                continue
            zone_name = str(zone_name).strip()
            if not zone_name or "total" in zone_name.lower():
                continue

            zone_code = self._extract_zone_code(zone_name)

            for col_idx, bedroom_type in bedroom_cols.items():
                if col_idx >= len(row):
                    continue

                value = row.iloc[col_idx]
                if pd.isna(value):
                    continue

                try:
                    universe_value = int(str(value).replace(",", ""))
                except (ValueError, AttributeError):
                    logger.debug(
                        f"Could not parse value: {value} for {zone_name} {bedroom_type}"
                    )
                    continue

                records.append(
                    CMHCUniverseRecord(
                        year=self.year,
                        zone_code=zone_code,
                        zone_name=zone_name,
                        bedroom_type=bedroom_type,
                        universe=universe_value,
                    )
                )

        logger.info(f"Parsed {len(records)} universe records from {self.excel_path.name}")
        return records

    def _parse_metric_table(
        self, df: pd.DataFrame, table_id: str
    ) -> dict[str, dict[str, tuple[float | None, str | None]]]:
        """Parse a Pattern A or Pattern B metric table.

        Handles tables where each bedroom type group has 4 or 5 columns:
          col_idx + 0: previous year value
          col_idx + 1: previous year reliability code
          col_idx + 2: current year value   <-- extracted
          col_idx + 3: current year reliability code  <-- extracted
          col_idx + 4: YoY change indicator (Pattern A only, ignored)

        Suppressed values ("**") are returned as None.

        Args:
            df: DataFrame of the target sheet (read with header=None).
            table_id: Table identifier used only for debug logging.

        Returns:
            Dict mapping zone_code -> bedroom_type -> (value, reliability_code).
            Also stores "zone_name" key inside the inner dict.
        """
        header_row_idx = self._find_header_row(df)
        if header_row_idx is None:
            logger.warning(
                f"Could not find bedroom type header in table {table_id} "
                f"of {self.excel_path.name}"
            )
            return {}

        bedroom_cols = self._find_bedroom_cols(df, header_row_idx)
        if not bedroom_cols:
            logger.warning(f"No bedroom columns found in table {table_id}")
            return {}

        data_start_idx = header_row_idx + 2
        results: dict[str, dict[str, Any]] = {}

        for idx in range(data_start_idx, len(df)):
            row = df.iloc[idx]
            zone_name = row.iloc[0]

            if pd.isna(zone_name):
                continue
            zone_name = str(zone_name).strip()
            if not zone_name or "total" in zone_name.lower():
                continue

            zone_code = self._extract_zone_code(zone_name)
            if zone_code not in results:
                results[zone_code] = {"zone_name": zone_name}

            for col_idx, bedroom_type in bedroom_cols.items():
                value_col = col_idx + 2
                rel_col = col_idx + 3

                raw_value = row.iloc[value_col] if value_col < len(row) else None
                raw_rel = row.iloc[rel_col] if rel_col < len(row) else None

                value = self._parse_float(raw_value)
                rel = self._parse_reliability(raw_rel)

                results[zone_code][bedroom_type] = (value, rel)

        logger.debug(
            f"Parsed {len(results)} zones from table {table_id} in {self.excel_path.name}"
        )
        return results

    def _parse_float(self, raw: object) -> float | None:
        """Convert a raw cell value to float, returning None for suppressed/missing data."""
        if raw is None:
            return None
        if isinstance(raw, float) and pd.isna(raw):
            return None
        s = str(raw).strip()
        if s in ("**", "++", "n/a", "n.a.", "--", ""):
            return None
        try:
            return float(s.replace(",", ""))
        except ValueError:
            logger.debug(f"Could not parse float: {raw!r}")
            return None

    def _parse_reliability(self, raw: object) -> str | None:
        """Extract a reliability code (a/b/c/d) from a raw cell value."""
        if raw is None:
            return None
        if isinstance(raw, float) and pd.isna(raw):
            return None
        s = str(raw).strip().lower()
        if s in ("a", "b", "c", "d"):
            return s
        return None

    def _extract_zone_code(self, zone_name: str) -> str:
        """Extract zone code from zone name.

        Examples:
        - "Zone 1 - Toronto (Central)" -> "01"
        - "Zone 2 - Toronto (East)" -> "02"
        - "Zone 15 - North York (Southwest)" -> "15"

        Args:
            zone_name: Full zone name string.

        Returns:
            Standardized zone code (2-digit string).
        """
        match = re.search(r"Zone\s+(\d+)", zone_name, re.IGNORECASE)
        if match:
            zone_num = int(match.group(1))
            return f"{zone_num:02d}"

        # Fallback: use sanitized zone name
        return zone_name.replace(" ", "_").replace("-", "_").upper()

    def _load_sheet(
        self, excel_file: pd.ExcelFile, table_id: str
    ) -> pd.DataFrame | None:
        """Find and load a sheet by its table ID string.

        Args:
            excel_file: Open ExcelFile object.
            table_id: Substring to match in sheet name (e.g. "3.1.1").

        Returns:
            DataFrame if the sheet is found, None otherwise.
        """
        for name in excel_file.sheet_names:
            if isinstance(name, str) and table_id in name:
                return pd.read_excel(excel_file, sheet_name=name, header=None)
        logger.warning(
            f"Sheet '{table_id}' not found in {self.excel_path.name}. "
            f"Available: {excel_file.sheet_names}"
        )
        return None

    def get_universe_data(self) -> list[CMHCUniverseRecord]:
        """Extract universe (total rental units) data from Excel file.

        Returns:
            List of CMHCUniverseRecord objects with zone, bedroom type, and unit count.
        """
        try:
            excel_file = pd.ExcelFile(self.excel_path, engine="openpyxl")
            df = self._load_sheet(excel_file, "3.1.3")
            if df is None:
                return []
            return self._parse_universe_table(df)
        except Exception as e:
            import traceback
            logger.error(f"Failed to parse {self.excel_path.name}: {e}")
            logger.debug(traceback.format_exc())
            return []

    def get_rental_data(self) -> list[CMHCExcelRentalRecord]:
        """Extract all available rental metrics from the Excel file.

        Parses tables 3.1.1, 3.1.2, 3.1.3, 3.1.5, and 3.1.6 and merges
        results into one record per zone and bedroom type.

        Returns:
            List of CMHCExcelRentalRecord objects with all available metrics.
        """
        try:
            excel_file = pd.ExcelFile(self.excel_path, engine="openpyxl")

            # Parse each metric table
            vacancy_data: dict[str, dict[str, Any]] = {}
            avg_rent_data: dict[str, dict[str, Any]] = {}
            rent_change_data: dict[str, dict[str, Any]] = {}
            turnover_data: dict[str, dict[str, Any]] = {}

            for table_id, target in [
                ("3.1.1", vacancy_data),
                ("3.1.2", avg_rent_data),
                ("3.1.5", rent_change_data),
                ("3.1.6", turnover_data),
            ]:
                df = self._load_sheet(excel_file, table_id)
                if df is not None:
                    target.update(self._parse_metric_table(df, table_id))

            # Build universe lookup from existing method
            universe_lookup: dict[tuple[str, str], int] = {}
            for rec in self.get_universe_data():
                universe_lookup[(rec.zone_code, rec.bedroom_type)] = rec.universe

            # Collect all zone codes seen across any table
            all_zones: dict[str, str] = {}  # zone_code -> zone_name
            for data in (vacancy_data, avg_rent_data, rent_change_data, turnover_data):
                for zone_code, inner in data.items():
                    if zone_code not in all_zones:
                        all_zones[zone_code] = inner.get("zone_name", zone_code)

            records: list[CMHCExcelRentalRecord] = []
            bedroom_types = list(self.BEDROOM_MAP.values())
            # Deduplicate while preserving order
            seen: set[str] = set()
            unique_bedroom_types = [
                bt for bt in bedroom_types if not (bt in seen or seen.add(bt))  # type: ignore[func-returns-value]
            ]

            for zone_code, zone_name in all_zones.items():
                for bedroom_type in unique_bedroom_types:
                    vacancy = vacancy_data.get(zone_code, {}).get(bedroom_type, (None, None))
                    avg_rent = avg_rent_data.get(zone_code, {}).get(bedroom_type, (None, None))
                    rent_change = rent_change_data.get(zone_code, {}).get(
                        bedroom_type, (None, None)
                    )
                    turnover = turnover_data.get(zone_code, {}).get(
                        bedroom_type, (None, None)
                    )
                    universe = universe_lookup.get((zone_code, bedroom_type))

                    # Skip records with no data at all
                    if all(
                        v is None
                        for v in [universe, avg_rent[0], vacancy[0], turnover[0], rent_change[0]]
                    ):
                        continue

                    records.append(
                        CMHCExcelRentalRecord(
                            year=self.year,
                            zone_code=zone_code,
                            zone_name=zone_name,
                            bedroom_type=bedroom_type,
                            universe=universe,
                            avg_rent=avg_rent[0],
                            avg_rent_reliability=avg_rent[1],
                            vacancy_rate=vacancy[0],
                            turnover_rate=turnover[0],
                            rent_change_pct=rent_change[0],
                        )
                    )

            logger.info(
                f"Parsed {len(records)} rental records from {self.excel_path.name}"
            )
            return records

        except Exception as e:
            import traceback
            logger.error(f"Failed to parse rental data from {self.excel_path.name}: {e}")
            logger.debug(traceback.format_exc())
            return []


def parse_cmhc_excel_directory(
    data_dir: Path,
    start_year: int = 2021,
    end_year: int | None = None,
) -> dict[int, list[CMHCUniverseRecord]]:
    """Parse all CMHC Excel files in a directory.

    Args:
        data_dir: Directory containing CMHC Excel files.
        start_year: First year to include.
        end_year: Last year to include (defaults to latest available).

    Returns:
        Dictionary mapping year to list of universe records.
    """
    import datetime

    if end_year is None:
        end_year = datetime.date.today().year + 1

    results: dict[int, list[CMHCUniverseRecord]] = {}

    excel_files = sorted(data_dir.glob("rmr-toronto-*.xlsx"))

    for excel_file in excel_files:
        parser = CMHCExcelParser(excel_file)

        if parser.year < start_year or parser.year > end_year:
            continue

        logger.info(f"Processing {excel_file.name}...")
        records = parser.get_universe_data()

        if records:
            results[parser.year] = records

    logger.info(
        f"Parsed {len(results)} years of universe data "
        f"({sum(len(r) for r in results.values())} records)"
    )
    return results


def parse_cmhc_excel_rental_directory(
    data_dir: Path,
    start_year: int = 2021,
    end_year: int | None = None,
) -> dict[int, list[CMHCExcelRentalRecord]]:
    """Parse all available rental metrics from CMHC Excel files in a directory.

    Extracts vacancy rates, average rents, rent change %, turnover rates,
    and universe from tables 3.1.1, 3.1.2, 3.1.3, 3.1.5, 3.1.6.

    Args:
        data_dir: Directory containing CMHC RMR Excel files.
        start_year: First year to include.
        end_year: Last year to include (defaults to latest available).

    Returns:
        Dictionary mapping year to list of CMHCExcelRentalRecord objects.
    """
    import datetime

    if end_year is None:
        end_year = datetime.date.today().year + 1

    results: dict[int, list[CMHCExcelRentalRecord]] = {}

    excel_files = sorted(data_dir.glob("rmr-toronto-*.xlsx"))

    for excel_file in excel_files:
        parser = CMHCExcelParser(excel_file)

        if parser.year < start_year or parser.year > end_year:
            continue

        logger.info(f"Processing {excel_file.name} for rental metrics...")
        records = parser.get_rental_data()

        if records:
            results[parser.year] = records

    total_records = sum(len(r) for r in results.values())
    logger.info(
        f"Parsed {len(results)} years of rental data ({total_records} records)"
    )
    return results


if __name__ == "__main__":
    # Test the parser
    logging.basicConfig(level=logging.INFO)

    data_dir = Path(__file__).parent.parent.parent.parent / "data" / "raw" / "cmhc"
    results = parse_cmhc_excel_directory(data_dir, start_year=2021)

    print(f"\nParsed {len(results)} years")
    for year, records in results.items():
        total_units = sum(r.universe for r in records)
        print(f"  {year}: {len(records)} records, {total_units:,} total units")

        by_bedroom: dict[str, int] = {}
        for r in records:
            if r.bedroom_type not in by_bedroom:
                by_bedroom[r.bedroom_type] = 0
            by_bedroom[r.bedroom_type] += r.universe

        print(f"    By bedroom type: {by_bedroom}")
