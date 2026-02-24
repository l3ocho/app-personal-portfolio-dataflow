"""Parser for MLSPA salary data.

Reads MLSPA cleaned CSV files from data/raw/football/mlspa/
"""

import logging
from pathlib import Path

import pandas as pd

from dataflow.football.schemas.mlspa import MLSPASalaryRecord

logger = logging.getLogger(__name__)


class MLSPAParser:
    """Parser for MLSPA salary CSV files.

    MLSPA (Major League Soccer Players Association) publishes cleaned salary data.
    Expects CSV files in data/raw/football/mlspa/ directory.
    """

    def __init__(self, data_root: Path) -> None:
        """Initialize parser with data root directory.

        Args:
            data_root: Path to data/raw/football/ directory
        """
        self.data_root = Path(data_root)
        self.mlspa_root = self.data_root / "mlspa"

    def parse_salary_files(self) -> list[MLSPASalaryRecord]:
        """Parse all MLSPA CSV files in mlspa directory.

        Returns:
            List of MLSPASalaryRecord objects
        """
        if not self.mlspa_root.exists():
            logger.warning(f"MLSPA directory not found at {self.mlspa_root}")
            return []

        csv_files = list(self.mlspa_root.glob("*.csv"))
        if not csv_files:
            logger.warning(f"No CSV files found in {self.mlspa_root}")
            return []

        records = []
        for csv_path in csv_files:
            records.extend(self._parse_csv(csv_path))

        logger.info(f"Parsed {len(records)} MLS salary records from {len(csv_files)} files")
        return records

    def _parse_csv(self, csv_path: Path) -> list[MLSPASalaryRecord]:
        """Parse single MLSPA CSV file.

        Expected columns: player_id, player_name, club_id, club_name, season, salary_usd, guaranteed_compensation_usd
        """
        try:
            df = pd.read_csv(csv_path)
            records = []

            for _, row in df.iterrows():
                try:
                    record = MLSPASalaryRecord(
                        player_id=str(row.get("player_id", "")),
                        player_name=str(row.get("player_name", "")),
                        club_id=str(row.get("club_id", "")),
                        club_name=str(row.get("club_name", "")),
                        season=int(row.get("season", 2023)),
                        salary_usd=row.get("salary_usd"),
                        guaranteed_compensation_usd=row.get("guaranteed_compensation_usd"),
                    )
                    records.append(record)
                except Exception as e:
                    logger.warning(f"Could not parse MLS salary row from {csv_path.name}: {row.to_dict()}: {e}")

            logger.info(f"Parsed {len(records)} records from {csv_path.name}")
            return records

        except Exception as e:
            logger.error(f"Error reading MLSPA CSV {csv_path}: {e}")
            return []
