"""CMHC CSV processor for rental market survey data.

This module provides the structure for processing CMHC (Canada Mortgage and Housing
Corporation) rental market survey data from CSV exports.
"""

from pathlib import Path
from typing import Any, cast

import pandas as pd

from dataflow.toronto.schemas import CMHCAnnualSurvey, CMHCRentalRecord


class CMHCParser:
    """Parser for CMHC Rental Market Survey CSV data.

    CMHC conducts annual rental market surveys and publishes data including:
    - Average and median rents by zone and bedroom type
    - Vacancy rates
    - Universe (total rental units)
    - Year-over-year rent changes

    Data is available via the Housing Market Information Portal as CSV exports.
    """

    # Expected columns in CMHC CSV exports
    REQUIRED_COLUMNS = {
        "zone_code",
        "zone_name",
        "bedroom_type",
        "survey_year",
    }

    # Column name mappings from CMHC export format
    COLUMN_MAPPINGS = {
        "Zone Code": "zone_code",
        "Zone Name": "zone_name",
        "Bedroom Type": "bedroom_type",
        "Survey Year": "survey_year",
        "Universe": "universe",
        "Average Rent ($)": "avg_rent",
        "Median Rent ($)": "median_rent",
        "Vacancy Rate (%)": "vacancy_rate",
        "Availability Rate (%)": "availability_rate",
        "Turnover Rate (%)": "turnover_rate",
        "% Change in Rent": "rent_change_pct",
        "Reliability Code": "reliability_code",
    }

    def __init__(self, csv_path: Path) -> None:
        """Initialize parser with path to CSV file.

        Args:
            csv_path: Path to the CMHC CSV export file.
        """
        self.csv_path = csv_path
        self._validate_path()

    def _validate_path(self) -> None:
        """Validate that the CSV path exists and is readable."""
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV not found: {self.csv_path}")
        if not self.csv_path.suffix.lower() == ".csv":
            raise ValueError(f"Expected CSV file, got: {self.csv_path.suffix}")

    def parse(self) -> CMHCAnnualSurvey:
        """Parse the CSV and return structured data.

        Returns:
            CMHCAnnualSurvey containing all extracted records.

        Raises:
            ValueError: If required columns are missing.
        """
        df = self._load_csv()
        df = self._normalize_columns(df)
        self._validate_columns(df)
        records = self._convert_to_records(df)
        survey_year = self._infer_survey_year(df)

        return CMHCAnnualSurvey(survey_year=survey_year, records=records)

    def _load_csv(self) -> pd.DataFrame:
        """Load CSV file into DataFrame.

        Returns:
            Raw DataFrame from CSV.
        """
        return pd.read_csv(self.csv_path)

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names to standard format.

        Args:
            df: DataFrame with original column names.

        Returns:
            DataFrame with normalized column names.
        """
        rename_map = {k: v for k, v in self.COLUMN_MAPPINGS.items() if k in df.columns}
        return df.rename(columns=rename_map)

    def _validate_columns(self, df: pd.DataFrame) -> None:
        """Validate that all required columns are present.

        Args:
            df: DataFrame to validate.

        Raises:
            ValueError: If required columns are missing.
        """
        missing = self.REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    def _convert_to_records(self, df: pd.DataFrame) -> list[CMHCRentalRecord]:
        """Convert DataFrame rows to validated schema records.

        Args:
            df: Normalized DataFrame.

        Returns:
            List of validated CMHCRentalRecord objects.
        """
        records = []
        for _, row in df.iterrows():
            record_data = row.to_dict()
            # Handle NaN values
            record_data = {
                k: (None if pd.isna(v) else v) for k, v in record_data.items()
            }
            records.append(CMHCRentalRecord(**cast(dict[str, Any], record_data)))
        return records

    def _infer_survey_year(self, df: pd.DataFrame) -> int:
        """Infer survey year from data.

        Args:
            df: DataFrame with survey_year column.

        Returns:
            Survey year as integer.
        """
        if "survey_year" in df.columns:
            return int(df["survey_year"].iloc[0])
        raise ValueError("Cannot infer survey year from data.")
