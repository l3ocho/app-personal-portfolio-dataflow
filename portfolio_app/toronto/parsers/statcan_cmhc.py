"""Parser for CMHC rental data via Statistics Canada API.

Downloads rental market data (average rent, vacancy rates, universe)
from Statistics Canada's Web Data Service.

Data Sources:
- Table 34-10-0127: Vacancy rates
- Table 34-10-0129: Rental universe (total units)
- Table 34-10-0133: Average rent by bedroom type
"""

import contextlib
import io
import logging
import zipfile
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx
import pandas as pd

logger = logging.getLogger(__name__)

# StatCan Web Data Service endpoints
STATCAN_API_BASE = "https://www150.statcan.gc.ca/t1/wds/rest"
STATCAN_DOWNLOAD_BASE = "https://www150.statcan.gc.ca/n1/tbl/csv"

# CMHC table IDs
CMHC_TABLES = {
    "vacancy": "34100127",
    "universe": "34100129",
    "rent": "34100133",
}

# Toronto CMA identifier in StatCan data
TORONTO_DGUID = "2011S0503535"
TORONTO_GEO_NAME = "Toronto, Ontario"


@dataclass
class CMHCRentalRecord:
    """Rental market record for database loading."""

    year: int
    month: int  # CMHC surveys in October, so month=10
    zone_name: str
    bedroom_type: str
    avg_rent: Decimal | None
    vacancy_rate: Decimal | None
    universe: int | None


class StatCanCMHCParser:
    """Parser for CMHC rental data from Statistics Canada.

    Downloads and processes rental market survey data including:
    - Average rents by bedroom type
    - Vacancy rates
    - Rental universe (total units)

    Data is available from 1987 to present, updated annually in January.
    """

    BEDROOM_TYPE_MAP = {
        "Bachelor units": "bachelor",
        "One bedroom units": "1bed",
        "Two bedroom units": "2bed",
        "Three bedroom units": "3bed",
        "Total": "total",
    }

    STRUCTURE_FILTER = "Apartment structures of six units and over"

    def __init__(
        self,
        cache_dir: Path | None = None,
        timeout: float = 60.0,
    ) -> None:
        """Initialize parser.

        Args:
            cache_dir: Optional directory for caching downloaded files.
            timeout: HTTP request timeout in seconds.
        """
        self._cache_dir = cache_dir
        self._timeout = timeout
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        """Lazy-initialize HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                timeout=self._timeout,
                follow_redirects=True,
            )
        return self._client

    def close(self) -> None:
        """Close HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "StatCanCMHCParser":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def _get_download_url(self, table_id: str) -> str:
        """Get CSV download URL for a StatCan table.

        Args:
            table_id: StatCan table ID (e.g., "34100133").

        Returns:
            Direct download URL for the CSV zip file.
        """
        api_url = f"{STATCAN_API_BASE}/getFullTableDownloadCSV/{table_id}/en"
        response = self.client.get(api_url)
        response.raise_for_status()

        data = response.json()
        if data.get("status") != "SUCCESS":
            raise ValueError(f"StatCan API error: {data}")

        return str(data["object"])

    def _download_table(self, table_id: str) -> pd.DataFrame:
        """Download and extract a StatCan table as DataFrame.

        Args:
            table_id: StatCan table ID.

        Returns:
            DataFrame with table data.
        """
        # Check cache first
        if self._cache_dir:
            cache_file = self._cache_dir / f"{table_id}.csv"
            if cache_file.exists():
                logger.debug(f"Loading {table_id} from cache")
                return pd.read_csv(cache_file)

        # Get download URL and fetch
        download_url = self._get_download_url(table_id)
        logger.info(f"Downloading StatCan table {table_id}...")

        response = self.client.get(download_url)
        response.raise_for_status()

        # Extract CSV from zip
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            csv_name = f"{table_id}.csv"
            with zf.open(csv_name) as f:
                df = pd.read_csv(f)

        # Cache if directory specified
        if self._cache_dir:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            df.to_csv(self._cache_dir / f"{table_id}.csv", index=False)

        logger.info(f"Downloaded {len(df)} records from table {table_id}")
        return df

    def _filter_toronto(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter DataFrame to Toronto CMA only.

        Args:
            df: Full StatCan DataFrame.

        Returns:
            DataFrame filtered to Toronto.
        """
        # Try DGUID first, then GEO name
        if "DGUID" in df.columns:
            toronto_df = df[df["DGUID"] == TORONTO_DGUID]
            if len(toronto_df) > 0:
                return toronto_df

        if "GEO" in df.columns:
            return df[df["GEO"] == TORONTO_GEO_NAME]

        raise ValueError("Could not identify Toronto data in DataFrame")

    def get_vacancy_rates(
        self,
        years: list[int] | None = None,
    ) -> dict[int, Decimal]:
        """Fetch Toronto vacancy rates by year.

        Args:
            years: Optional list of years to filter.

        Returns:
            Dictionary mapping year to vacancy rate.
        """
        df = self._download_table(CMHC_TABLES["vacancy"])
        df = self._filter_toronto(df)

        # Filter years if specified
        if years:
            df = df[df["REF_DATE"].isin(years)]

        # Extract year -> rate mapping
        rates = {}
        for _, row in df.iterrows():
            year = int(row["REF_DATE"])
            value = row.get("VALUE")
            if pd.notna(value):
                rates[year] = Decimal(str(value))

        logger.info(f"Fetched vacancy rates for {len(rates)} years")
        return rates

    def get_rental_universe(
        self,
        years: list[int] | None = None,
    ) -> dict[tuple[int, str], int]:
        """Fetch Toronto rental universe (total units) by year and bedroom type.

        Args:
            years: Optional list of years to filter.

        Returns:
            Dictionary mapping (year, bedroom_type) to unit count.
        """
        df = self._download_table(CMHC_TABLES["universe"])
        df = self._filter_toronto(df)

        # Filter to standard apartment structures
        if "Type of structure" in df.columns:
            df = df[df["Type of structure"] == self.STRUCTURE_FILTER]

        if years:
            df = df[df["REF_DATE"].isin(years)]

        universe = {}
        for _, row in df.iterrows():
            year = int(row["REF_DATE"])
            bedroom_raw = row.get("Type of unit", "Total")
            bedroom = self.BEDROOM_TYPE_MAP.get(bedroom_raw, "other")
            value = row.get("VALUE")

            if pd.notna(value) and value is not None:
                universe[(year, bedroom)] = int(str(value))

        logger.info(
            f"Fetched rental universe for {len(universe)} year/bedroom combinations"
        )
        return universe

    def get_average_rents(
        self,
        years: list[int] | None = None,
    ) -> dict[tuple[int, str], Decimal]:
        """Fetch Toronto average rents by year and bedroom type.

        Args:
            years: Optional list of years to filter.

        Returns:
            Dictionary mapping (year, bedroom_type) to average rent.
        """
        df = self._download_table(CMHC_TABLES["rent"])
        df = self._filter_toronto(df)

        # Filter to standard apartment structures (most reliable data)
        if "Type of structure" in df.columns:
            df = df[df["Type of structure"] == self.STRUCTURE_FILTER]

        if years:
            df = df[df["REF_DATE"].isin(years)]

        rents = {}
        for _, row in df.iterrows():
            year = int(row["REF_DATE"])
            bedroom_raw = row.get("Type of unit", "Total")
            bedroom = self.BEDROOM_TYPE_MAP.get(bedroom_raw, "other")
            value = row.get("VALUE")

            if pd.notna(value) and str(value) not in ("F", ".."):
                with contextlib.suppress(Exception):
                    rents[(year, bedroom)] = Decimal(str(value))

        logger.info(f"Fetched average rents for {len(rents)} year/bedroom combinations")
        return rents

    def get_all_rental_data(
        self,
        start_year: int = 2014,
        end_year: int | None = None,
    ) -> list[CMHCRentalRecord]:
        """Fetch all Toronto rental data and combine into records.

        Args:
            start_year: First year to include.
            end_year: Last year to include (defaults to current year + 1).

        Returns:
            List of CMHCRentalRecord objects ready for database loading.
        """
        import datetime

        if end_year is None:
            end_year = datetime.date.today().year + 1

        years = list(range(start_year, end_year + 1))

        logger.info(
            f"Fetching CMHC rental data for Toronto ({start_year}-{end_year})..."
        )

        # Fetch all data types
        vacancy_rates = self.get_vacancy_rates(years)
        rents = self.get_average_rents(years)
        universe = self.get_rental_universe(years)

        # Combine into records
        records = []
        bedroom_types = ["bachelor", "1bed", "2bed", "3bed"]

        for year in years:
            vacancy = vacancy_rates.get(year)

            for bedroom in bedroom_types:
                avg_rent = rents.get((year, bedroom))
                units = universe.get((year, bedroom))

                # Skip if no rent data for this year/bedroom
                if avg_rent is None:
                    continue

                records.append(
                    CMHCRentalRecord(
                        year=year,
                        month=10,  # CMHC surveys in October
                        zone_name="Toronto CMA",
                        bedroom_type=bedroom,
                        avg_rent=avg_rent,
                        vacancy_rate=vacancy,
                        universe=units,
                    )
                )

        logger.info(f"Created {len(records)} CMHC rental records")
        return records


def fetch_toronto_rental_data(
    start_year: int = 2014,
    end_year: int | None = None,
    cache_dir: Path | None = None,
) -> list[CMHCRentalRecord]:
    """Convenience function to fetch Toronto rental data.

    Args:
        start_year: First year to include.
        end_year: Last year to include.
        cache_dir: Optional cache directory.

    Returns:
        List of CMHCRentalRecord objects.
    """
    with StatCanCMHCParser(cache_dir=cache_dir) as parser:
        return parser.get_all_rental_data(start_year, end_year)


if __name__ == "__main__":
    # Test the parser
    logging.basicConfig(level=logging.INFO)

    records = fetch_toronto_rental_data(start_year=2020)

    print(f"\nFetched {len(records)} records")
    print("\nSample records:")
    for r in records[:10]:
        print(
            f"  {r.year} {r.bedroom_type}: ${r.avg_rent} rent, {r.vacancy_rate}% vacancy"
        )
