"""Parser for Toronto Police crime data via CKAN API.

Fetches neighbourhood crime rates and major crime indicators from the
Toronto Police Service data hosted on Toronto Open Data Portal.

Data Sources:
- Neighbourhood Crime Rates: Annual crime rates by neighbourhood
- Major Crime Indicators (MCI): Detailed incident-level data
"""

import contextlib
import logging
from decimal import Decimal
from typing import Any

import httpx

from portfolio_app.toronto.schemas import CrimeRecord, CrimeType

logger = logging.getLogger(__name__)


# Mapping from Toronto Police crime categories to CrimeType enum
CRIME_TYPE_MAPPING: dict[str, CrimeType] = {
    "assault": CrimeType.ASSAULT,
    "assaults": CrimeType.ASSAULT,
    "auto theft": CrimeType.AUTO_THEFT,
    "autotheft": CrimeType.AUTO_THEFT,
    "auto_theft": CrimeType.AUTO_THEFT,
    "break and enter": CrimeType.BREAK_AND_ENTER,
    "breakenter": CrimeType.BREAK_AND_ENTER,
    "break_and_enter": CrimeType.BREAK_AND_ENTER,
    "homicide": CrimeType.HOMICIDE,
    "homicides": CrimeType.HOMICIDE,
    "robbery": CrimeType.ROBBERY,
    "robberies": CrimeType.ROBBERY,
    "shooting": CrimeType.SHOOTING,
    "shootings": CrimeType.SHOOTING,
    "theft over": CrimeType.THEFT_OVER,
    "theftover": CrimeType.THEFT_OVER,
    "theft_over": CrimeType.THEFT_OVER,
    "theft from motor vehicle": CrimeType.THEFT_FROM_MOTOR_VEHICLE,
    "theftfrommv": CrimeType.THEFT_FROM_MOTOR_VEHICLE,
    "theft_from_mv": CrimeType.THEFT_FROM_MOTOR_VEHICLE,
}


def _normalize_crime_type(crime_str: str) -> CrimeType:
    """Normalize crime type string to CrimeType enum.

    Args:
        crime_str: Raw crime type string from data source.

    Returns:
        Matched CrimeType enum value, or CrimeType.OTHER if no match.
    """
    normalized = crime_str.lower().strip().replace("-", " ").replace("_", " ")
    return CRIME_TYPE_MAPPING.get(normalized, CrimeType.OTHER)


class TorontoPoliceParser:
    """Parser for Toronto Police crime data via CKAN API.

    Crime data is hosted on Toronto Open Data Portal but sourced from
    Toronto Police Service.
    """

    BASE_URL = "https://ckan0.cf.opendata.inter.prod-toronto.ca"
    API_PATH = "/api/3/action"

    # Dataset package IDs
    DATASETS = {
        "crime_rates": "neighbourhood-crime-rates",
        "mci": "major-crime-indicators",
        "shootings": "shootings-firearm-discharges",
    }

    def __init__(self, timeout: float = 30.0) -> None:
        """Initialize parser.

        Args:
            timeout: HTTP request timeout in seconds.
        """
        self._timeout = timeout
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        """Lazy-initialize HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.BASE_URL,
                timeout=self._timeout,
                headers={"Accept": "application/json"},
            )
        return self._client

    def close(self) -> None:
        """Close HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "TorontoPoliceParser":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def _get_package(self, package_id: str) -> dict[str, Any]:
        """Fetch package metadata from CKAN."""
        response = self.client.get(
            f"{self.API_PATH}/package_show",
            params={"id": package_id},
        )
        response.raise_for_status()
        result = response.json()

        if not result.get("success"):
            raise ValueError(f"CKAN API error: {result.get('error', 'Unknown error')}")

        return dict(result["result"])

    def _fetch_datastore_records(
        self,
        package_id: str,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch records from CKAN datastore.

        Args:
            package_id: CKAN package ID.
            filters: Optional filters to apply.

        Returns:
            List of records as dictionaries.
        """
        package = self._get_package(package_id)
        resources = package.get("resources", [])

        # Find datastore-enabled resource
        resource_id = None
        for resource in resources:
            if resource.get("datastore_active"):
                resource_id = resource["id"]
                break

        if not resource_id:
            raise ValueError(f"No datastore resource in {package_id}")

        # Fetch all records
        records: list[dict[str, Any]] = []
        offset = 0
        limit = 1000

        while True:
            params: dict[str, Any] = {
                "id": resource_id,
                "limit": limit,
                "offset": offset,
            }
            if filters:
                params["filters"] = str(filters)

            response = self.client.get(
                f"{self.API_PATH}/datastore_search",
                params=params,
            )
            response.raise_for_status()
            result = response.json()

            if not result.get("success"):
                raise ValueError(f"Datastore error: {result.get('error')}")

            batch = result["result"]["records"]
            records.extend(batch)

            if len(batch) < limit:
                break
            offset += limit

        return records

    def get_crime_rates(
        self,
        years: list[int] | None = None,
    ) -> list[CrimeRecord]:
        """Fetch neighbourhood crime rates.

        The crime rates dataset contains annual counts and rates per 100k
        population for each neighbourhood.

        Args:
            years: Optional list of years to filter. If None, fetches all.

        Returns:
            List of validated CrimeRecord objects.
        """
        try:
            raw_records = self._fetch_datastore_records(self.DATASETS["crime_rates"])
        except (httpx.HTTPError, ValueError) as e:
            logger.warning(f"Could not fetch crime rates: {e}")
            return []

        records = []

        for row in raw_records:
            # Extract neighbourhood ID (Hood_ID maps to AREA_ID)
            hood_id = row.get("HOOD_ID") or row.get("Hood_ID") or row.get("hood_id")
            if not hood_id:
                continue

            try:
                neighbourhood_id = int(hood_id)
            except (ValueError, TypeError):
                continue

            # Crime rate data typically has columns like:
            # ASSAULT_2019, ASSAULT_RATE_2019, AUTOTHEFT_2020, etc.
            # We need to parse column names to extract crime type and year

            for col_name, value in row.items():
                if value is None or col_name in (
                    "_id",
                    "HOOD_ID",
                    "Hood_ID",
                    "hood_id",
                    "AREA_NAME",
                    "NEIGHBOURHOOD",
                ):
                    continue

                # Try to parse column name for crime type and year
                # Pattern: CRIMETYPE_YEAR or CRIMETYPE_RATE_YEAR
                parts = col_name.upper().split("_")
                if len(parts) < 2:
                    continue

                # Check if last part is a year
                try:
                    year = int(parts[-1])
                    if year < 2014 or year > 2030:
                        continue
                except ValueError:
                    continue

                # Filter by years if specified
                if years and year not in years:
                    continue

                # Check if this is a rate column
                is_rate = "RATE" in parts

                # Extract crime type (everything before RATE/year)
                if is_rate:
                    rate_idx = parts.index("RATE")
                    crime_type_str = "_".join(parts[:rate_idx])
                else:
                    crime_type_str = "_".join(parts[:-1])

                crime_type = _normalize_crime_type(crime_type_str)

                try:
                    numeric_value = Decimal(str(value))
                except (ValueError, TypeError):
                    continue

                if is_rate:
                    # This is a rate column - look for corresponding count
                    # We'll skip rate-only entries and create records from counts
                    continue

                # Find corresponding rate if available
                rate_col = f"{crime_type_str}_RATE_{year}"
                rate_value = row.get(rate_col)
                rate_per_100k = None
                if rate_value is not None:
                    with contextlib.suppress(ValueError, TypeError):
                        rate_per_100k = Decimal(str(rate_value))

                records.append(
                    CrimeRecord(
                        neighbourhood_id=neighbourhood_id,
                        year=year,
                        crime_type=crime_type,
                        count=int(numeric_value),
                        rate_per_100k=rate_per_100k,
                    )
                )

        logger.info(f"Parsed {len(records)} crime rate records")
        return records

    def get_major_crime_indicators(
        self,
        years: list[int] | None = None,
    ) -> list[CrimeRecord]:
        """Fetch major crime indicators (detailed MCI data).

        MCI data contains incident-level records that need to be aggregated
        by neighbourhood and year.

        Args:
            years: Optional list of years to filter.

        Returns:
            List of aggregated CrimeRecord objects.
        """
        try:
            raw_records = self._fetch_datastore_records(self.DATASETS["mci"])
        except (httpx.HTTPError, ValueError) as e:
            logger.warning(f"Could not fetch MCI data: {e}")
            return []

        # Aggregate counts by neighbourhood, year, and crime type
        aggregates: dict[tuple[int, int, CrimeType], int] = {}

        for row in raw_records:
            # Extract neighbourhood ID
            hood_id = (
                row.get("HOOD_158")
                or row.get("HOOD_140")
                or row.get("HOOD_ID")
                or row.get("Hood_ID")
            )
            if not hood_id:
                continue

            try:
                neighbourhood_id = int(hood_id)
            except (ValueError, TypeError):
                continue

            # Extract year from occurrence date
            occ_year = row.get("OCC_YEAR") or row.get("REPORT_YEAR")
            if not occ_year:
                continue

            try:
                year = int(occ_year)
                if year < 2014 or year > 2030:
                    continue
            except (ValueError, TypeError):
                continue

            # Filter by years if specified
            if years and year not in years:
                continue

            # Extract crime type
            mci_category = row.get("MCI_CATEGORY") or row.get("OFFENCE") or ""
            crime_type = _normalize_crime_type(str(mci_category))

            # Aggregate count
            key = (neighbourhood_id, year, crime_type)
            aggregates[key] = aggregates.get(key, 0) + 1

        # Convert aggregates to CrimeRecord objects
        records = [
            CrimeRecord(
                neighbourhood_id=neighbourhood_id,
                year=year,
                crime_type=crime_type,
                count=count,
                rate_per_100k=None,  # Would need population data to calculate
            )
            for (neighbourhood_id, year, crime_type), count in aggregates.items()
        ]

        logger.info(f"Parsed {len(records)} MCI records (aggregated)")
        return records
