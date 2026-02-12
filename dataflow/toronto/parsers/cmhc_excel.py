"""Parser for CMHC Excel files (RMR - Rental Market Reports).

Extracts rental market data from CMHC Excel files including:
- Table 3.1.3: Universe (total rental units) by zone and bedroom type

These Excel files are published annually by CMHC and contain detailed
zone-level data not available through the StatCan API.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

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


class CMHCExcelParser:
    """Parser for CMHC Rental Market Report Excel files.

    CMHC publishes annual Rental Market Reports (RMR) as Excel files with
    multiple tables. This parser extracts:
    - Table 3.1.3: Universe (total rental units) by zone and bedroom type

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
        if not self.excel_path.suffix.lower() in [".xlsx", ".xls"]:
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
        records = []

        # Find header row (contains "Studio"/"Bachelor", "1 Bedroom", etc.)
        header_row_idx = None
        for idx in range(len(df)):
            row = df.iloc[idx]
            row_str = " ".join(str(val) for val in row if pd.notna(val))
            # Check for either "Studio" (new format) or "Bachelor" (old format)
            if ("Studio" in row_str or "Bachelor" in row_str) and "Bedroom" in row_str:
                header_row_idx = idx
                logger.debug(f"Found header row at index {idx}")
                break

        if header_row_idx is None:
            logger.warning(f"Could not find bedroom type header in {self.excel_path.name}")
            return records

        # Extract bedroom types from header row
        header_row = df.iloc[header_row_idx]
        bedroom_cols = {}  # column_idx -> bedroom_type
        for col_idx in range(1, len(header_row)):
            val = header_row.iloc[col_idx]
            if pd.notna(val) and val in self.BEDROOM_MAP:
                bedroom_cols[col_idx] = self.BEDROOM_MAP[val]

        logger.debug(f"Found bedroom columns: {bedroom_cols}")

        # Year row is typically right after header row
        year_row_idx = header_row_idx + 1

        # Data rows start after year row
        data_start_idx = year_row_idx + 1

        # Parse data rows
        for idx in range(data_start_idx, len(df)):
            row = df.iloc[idx]
            zone_name = row.iloc[0]

            # Skip if no zone name or aggregate rows
            if pd.isna(zone_name):
                continue
            zone_name = str(zone_name).strip()
            if not zone_name or "total" in zone_name.lower():
                continue

            # Extract zone code from name (e.g., "Zone 1 - Toronto (Central)" -> "ZONE_1")
            zone_code = self._extract_zone_code(zone_name)

            # Extract universe values for each bedroom type
            for col_idx, bedroom_type in bedroom_cols.items():
                if col_idx >= len(row):
                    continue

                value = row.iloc[col_idx]
                if pd.isna(value):
                    continue

                # Parse value (handle strings like "7,103" -> 7103)
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
        # Try to extract "Zone N" pattern
        match = re.search(r"Zone\s+(\d+)", zone_name, re.IGNORECASE)
        if match:
            zone_num = int(match.group(1))
            # Return as 2-digit zero-padded string (e.g., "01", "02", "15")
            return f"{zone_num:02d}"

        # Fallback: use sanitized zone name
        return zone_name.replace(" ", "_").replace("-", "_").upper()

    def get_universe_data(self) -> list[CMHCUniverseRecord]:
        """Extract universe (total rental units) data from Excel file.

        Returns:
            List of CMHCUniverseRecord objects with zone, bedroom type, and unit count.
        """
        try:
            excel_file = pd.ExcelFile(self.excel_path, engine="openpyxl")

            # Find sheet "Table 3.1.3"
            sheet_name = None
            for name in excel_file.sheet_names:
                if "3.1.3" in name:
                    sheet_name = name
                    break

            if not sheet_name:
                logger.warning(
                    f"Could not find Table 3.1.3 sheet in {self.excel_path.name}"
                )
                return []

            # Read the sheet
            df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)

            # Parse the table
            return self._parse_universe_table(df)

        except Exception as e:
            import traceback
            logger.error(f"Failed to parse {self.excel_path.name}: {e}")
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

    # Find Excel files
    excel_files = sorted(data_dir.glob("rmr-toronto-*.xlsx"))

    for excel_file in excel_files:
        parser = CMHCExcelParser(excel_file)

        # Skip if year is out of range
        if parser.year < start_year or parser.year > end_year:
            continue

        logger.info(f"Processing {excel_file.name}...")
        records = parser.get_universe_data()

        if records:
            results[parser.year] = records

    logger.info(
        f"Parsed {len(results)} years of universe data ({sum(len(r) for r in results.values())} records)"
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

        # Group by bedroom type to show totals
        by_bedroom = {}
        for r in records:
            if r.bedroom_type not in by_bedroom:
                by_bedroom[r.bedroom_type] = 0
            by_bedroom[r.bedroom_type] += r.universe

        print(f"    By bedroom type: {by_bedroom}")
