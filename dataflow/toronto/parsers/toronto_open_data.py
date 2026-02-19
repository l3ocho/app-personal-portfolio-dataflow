"""Parser for Toronto Open Data CKAN API.

Fetches neighbourhood boundaries, census profiles, and amenities data
from the City of Toronto's Open Data Portal.

API Documentation: https://open.toronto.ca/dataset/
"""

import contextlib
import csv
import io
import json
import logging
import zipfile
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx

from dataflow.toronto.schemas import (
    AmenityRecord,
    AmenityType,
    CensusRecord,
    NeighbourhoodRecord,
    ProfileRecord,
)

logger = logging.getLogger(__name__)


class TorontoOpenDataParser:
    """Parser for Toronto Open Data CKAN API.

    Provides methods to fetch and parse neighbourhood boundaries, census profiles,
    and amenities (parks, schools, childcare) from the Toronto Open Data portal.
    """

    BASE_URL = "https://ckan0.cf.opendata.inter.prod-toronto.ca"
    API_PATH = "/api/3/action"

    # Dataset package IDs
    DATASETS = {
        "neighbourhoods": "neighbourhoods",
        "neighbourhood_profiles": "neighbourhood-profiles",
        "parks": "parks-and-recreation-facilities",
        "schools": "school-locations-all-types",
        "childcare": "licensed-child-care-centres",
        "transit_stops": "b811ead4-6eaf-4adb-8408-d389fb5a069c",
    }

    # Known continent names from Statistics Canada 2021 XLSX
    # Used to distinguish place_of_birth continent-level from country-level rows
    _POB_CONTINENTS: frozenset[str] = frozenset({
        "africa",
        "americas",
        "asia",
        "europe",
        "oceania",
    })

    # Section metadata for profile data parsing
    # Maps category to start/stop anchors for identifying data sections
    # Anchors use substring matching on normalized characteristic text
    _PROFILE_SECTIONS: list[dict[str, str]] = [
        {
            "category": "immigration_status",
            "start_anchor": "immigration status",
            "stop_anchor": "place of birth",
        },
        {
            "category": "place_of_birth",
            "start_anchor": "place of birth",
            "stop_anchor": "citizenship",
        },
        {
            "category": "place_of_birth_recent",
            "start_anchor": "place of birth of recent",
            "stop_anchor": "citizenship status",
        },
        {
            "category": "citizenship",
            "start_anchor": "citizenship status",
            "stop_anchor": "generation status",
        },
        {
            "category": "generation_status",
            "start_anchor": "generation status",
            "stop_anchor": "visible minority",
        },
        {
            "category": "admission_category",
            "start_anchor": "admission category",
            "stop_anchor": "visible minority",
        },
        {
            "category": "visible_minority",
            "start_anchor": "visible minority",
            "stop_anchor": "ethnic origin",
        },
        {
            "category": "ethnic_origin",
            "start_anchor": "ethnic origin",
            "stop_anchor": "mother tongue",
        },
        {
            "category": "mother_tongue",
            "start_anchor": "mother tongue",
            "stop_anchor": "official language",
        },
        {
            "category": "official_language",
            "start_anchor": "official language",
            "stop_anchor": "total population by religion",
        },
    ]

    def __init__(
        self,
        cache_dir: Path | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize parser.

        Args:
            cache_dir: Optional directory for caching API responses.
            timeout: HTTP request timeout in seconds.
        """
        self._cache_dir = cache_dir
        self._timeout = timeout
        self._client: httpx.Client | None = None
        self._neighbourhood_name_map: dict[str, int] | None = None
        self._spatial_index: tuple[Any, list[Any], list[int]] | None = None

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

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize a neighbourhood name for matching.

        Handles common variations: hyphens vs spaces, smart quotes vs ASCII,
        dot-space vs dot (e.g. "St. James" vs "St.James").
        """
        n = name.lower().strip()
        # Normalize quotes/backticks to ASCII apostrophe
        n = n.replace("\u2019", "'").replace("\u2018", "'").replace("`", "'")
        # Normalize hyphens to spaces
        n = n.replace("-", " ")
        # Normalize "st. " to "st." (remove space after dots)
        n = n.replace(". ", ".")
        # Collapse multiple spaces
        return " ".join(n.split())

    def _get_neighbourhood_name_map(self) -> dict[str, int]:
        """Build and cache a mapping of neighbourhood names to IDs.

        Returns:
            Dictionary mapping normalized neighbourhood names to area_id.
        """
        if self._neighbourhood_name_map is not None:
            return self._neighbourhood_name_map

        neighbourhoods = self.get_neighbourhoods()
        self._neighbourhood_name_map = {}

        for n in neighbourhoods:
            # Add multiple variations of the name for flexible matching
            name_lower = n.area_name.lower().strip()
            self._neighbourhood_name_map[name_lower] = n.area_id

            # Add normalized version for cross-format matching
            normalized = self._normalize_name(n.area_name)
            self._neighbourhood_name_map[normalized] = n.area_id

            # Also add without common suffixes/prefixes
            for suffix in [" neighbourhood", " area", "-"]:
                if suffix in name_lower:
                    alt_name = name_lower.replace(suffix, "").strip()
                    self._neighbourhood_name_map[alt_name] = n.area_id

        logger.debug(
            f"Built neighbourhood name map with {len(self._neighbourhood_name_map)} entries"
        )
        return self._neighbourhood_name_map

    def _match_neighbourhood_id(self, name: str) -> int | None:
        """Match a neighbourhood name to its ID.

        Args:
            name: Neighbourhood name from census data.

        Returns:
            Neighbourhood ID or None if not found.
        """
        name_map = self._get_neighbourhood_name_map()
        name_lower = name.lower().strip()

        # Direct match
        if name_lower in name_map:
            return name_map[name_lower]

        # Try normalized match (handles hyphens/spaces/quotes/dots)
        normalized = self._normalize_name(name)
        if normalized in name_map:
            return name_map[normalized]

        # Try removing parenthetical content
        if "(" in name_lower:
            base_name = name_lower.split("(")[0].strip()
            if base_name in name_map:
                return name_map[base_name]

        # Try fuzzy matching with first few chars
        for key, area_id in name_map.items():
            if key.startswith(name_lower[:10]) or name_lower.startswith(key[:10]):
                return area_id

        return None

    def __enter__(self) -> "TorontoOpenDataParser":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def _get_package(self, package_id: str) -> dict[str, Any]:
        """Fetch package metadata from CKAN.

        Args:
            package_id: The package/dataset ID.

        Returns:
            Package metadata dictionary.
        """
        response = self.client.get(
            f"{self.API_PATH}/package_show",
            params={"id": package_id},
        )
        response.raise_for_status()
        result = response.json()

        if not result.get("success"):
            raise ValueError(f"CKAN API error: {result.get('error', 'Unknown error')}")

        return dict(result["result"])

    def _get_resource_url(
        self,
        package_id: str,
        format_filter: str = "geojson",
    ) -> str:
        """Get the download URL for a resource in a package.

        Args:
            package_id: The package/dataset ID.
            format_filter: Resource format to filter by (e.g., 'geojson', 'csv').

        Returns:
            Resource download URL.

        Raises:
            ValueError: If no matching resource is found.
        """
        package = self._get_package(package_id)
        resources = package.get("resources", [])

        for resource in resources:
            resource_format = resource.get("format", "").lower()
            if format_filter.lower() in resource_format:
                return str(resource["url"])

        available = [r.get("format") for r in resources]
        raise ValueError(
            f"No {format_filter} resource in {package_id}. Available: {available}"
        )

    def _fetch_geojson(self, package_id: str) -> dict[str, Any]:
        """Fetch GeoJSON data from a package.

        Handles both pure GeoJSON responses and CSV responses with embedded
        geometry columns (common in Toronto Open Data).

        Args:
            package_id: The package/dataset ID.

        Returns:
            GeoJSON FeatureCollection.
        """
        # Check cache first
        if self._cache_dir:
            cache_file = self._cache_dir / f"{package_id}.geojson"
            if cache_file.exists():
                logger.debug(f"Loading {package_id} from cache")
                with open(cache_file, encoding="utf-8") as f:
                    return dict(json.load(f))

        url = self._get_resource_url(package_id, format_filter="geojson")
        logger.info(f"Fetching GeoJSON from {url}")

        response = self.client.get(url)
        response.raise_for_status()

        # Try to parse as JSON first
        try:
            data = response.json()
            # If it's already a valid GeoJSON FeatureCollection, return it
            if isinstance(data, dict) and data.get("type") == "FeatureCollection":
                if self._cache_dir:
                    self._cache_dir.mkdir(parents=True, exist_ok=True)
                    cache_file = self._cache_dir / f"{package_id}.geojson"
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(data, f)
                return dict(data)
        except json.JSONDecodeError:
            pass

        # If JSON parsing failed, it's likely CSV with embedded geometry
        # Parse CSV and convert to GeoJSON FeatureCollection
        logger.info("Response is CSV format, converting to GeoJSON...")

        # Increase field size limit for large geometry columns
        csv.field_size_limit(10 * 1024 * 1024)  # 10 MB

        csv_text = response.text
        reader = csv.DictReader(io.StringIO(csv_text))

        features = []
        for row in reader:
            # Extract geometry from the 'geometry' column if present
            geometry = None
            if "geometry" in row and row["geometry"]:
                with contextlib.suppress(json.JSONDecodeError):
                    geometry = json.loads(row["geometry"])

            # Build properties from all other columns
            properties = {k: v for k, v in row.items() if k != "geometry"}

            features.append(
                {
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": properties,
                }
            )

        geojson_data: dict[str, Any] = {
            "type": "FeatureCollection",
            "features": features,
        }

        # Cache the converted response
        if self._cache_dir:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file = self._cache_dir / f"{package_id}.geojson"
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(geojson_data, f)

        return geojson_data

    def _fetch_csv_as_json(self, package_id: str) -> list[dict[str, Any]]:
        """Fetch CSV data as JSON records via CKAN datastore.

        Args:
            package_id: The package/dataset ID.

        Returns:
            List of records as dictionaries.
        """
        package = self._get_package(package_id)
        resources = package.get("resources", [])

        # Find a datastore-enabled resource
        for resource in resources:
            if resource.get("datastore_active"):
                resource_id = resource["id"]
                break
        else:
            raise ValueError(f"No datastore resource in {package_id}")

        # Fetch all records via datastore_search
        records: list[dict[str, Any]] = []
        offset = 0
        limit = 1000

        while True:
            response = self.client.get(
                f"{self.API_PATH}/datastore_search",
                params={"id": resource_id, "limit": limit, "offset": offset},
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

    def _fetch_xlsx_as_records(
        self, package_id: str, name_filter: str = ""
    ) -> list[dict[str, Any]]:
        """Fetch XLSX resource and convert to list of dicts.

        The XLSX format has indicators as rows and neighbourhoods as columns.
        Converts to the same dict format as datastore_search for compatibility.

        Args:
            package_id: The package/dataset ID.
            name_filter: Optional substring to match in resource name.

        Returns:
            List of records as dictionaries with "Characteristic" key.

        Raises:
            ValueError: If no matching XLSX resource is found.
        """
        import openpyxl

        package = self._get_package(package_id)
        resources = package.get("resources", [])

        # Find XLSX resource matching the name filter
        resource_url = None
        for resource in resources:
            if resource.get("format", "").upper() == "XLSX" and (
                not name_filter or name_filter in resource.get("name", "")
            ):
                resource_url = resource["url"]
                break

        if not resource_url:
            raise ValueError(f"No XLSX resource in {package_id}")

        logger.info(f"Downloading XLSX from {resource_url}")
        response = self.client.get(resource_url, timeout=120.0)
        response.raise_for_status()

        wb = openpyxl.load_workbook(
            io.BytesIO(response.content), read_only=True, data_only=True
        )
        ws = wb.active

        rows_iter = ws.iter_rows(values_only=True)
        headers = list(next(rows_iter))

        # Convert to list of dicts with "Characteristic" as the indicator key
        records: list[dict[str, Any]] = []
        for row in rows_iter:
            record: dict[str, Any] = {"Characteristic": ""}
            for i, header in enumerate(headers):
                if i == 0:
                    record["Characteristic"] = (
                        str(row[i]).strip() if row[i] is not None else ""
                    )
                else:
                    # Store neighbourhood values; convert None to empty string
                    col_name = str(header).strip() if header else f"col_{i}"
                    record[col_name] = row[i] if row[i] is not None else ""
            records.append(record)

        wb.close()
        logger.info(f"Parsed {len(records)} rows from XLSX")
        return records

    def _fetch_gtfs_stops(self, package_id: str) -> list[dict[str, str]]:
        """Fetch and parse stops.txt from a GTFS ZIP archive.

        Args:
            package_id: CKAN package ID containing the GTFS ZIP resource.

        Returns:
            List of stop records as dictionaries from stops.txt CSV.
        """
        # Check cache for extracted stops data
        if self._cache_dir:
            cache_file = self._cache_dir / f"{package_id}_stops.json"
            if cache_file.exists():
                logger.debug(f"Loading GTFS stops from cache: {cache_file}")
                with open(cache_file, encoding="utf-8") as f:
                    return list(json.load(f))

        url = self._get_resource_url(package_id, format_filter="zip")
        logger.info(f"Downloading GTFS ZIP from {url}")

        response = self.client.get(url, timeout=120.0)
        response.raise_for_status()

        zip_buffer = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_buffer) as zf:
            if "stops.txt" not in zf.namelist():
                raise ValueError(
                    f"stops.txt not found in GTFS ZIP. Contents: {zf.namelist()}"
                )
            with zf.open("stops.txt") as stops_file:
                reader = csv.DictReader(
                    io.TextIOWrapper(stops_file, encoding="utf-8-sig")
                )
                records = [dict(row) for row in reader]

        logger.info(f"Extracted {len(records)} stop records from GTFS stops.txt")

        # Cache extracted stops as JSON (small vs 82MB ZIP)
        if self._cache_dir:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file = self._cache_dir / f"{package_id}_stops.json"
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(records, f)

        return records

    def get_neighbourhoods(self) -> list[NeighbourhoodRecord]:
        """Fetch 158 Toronto neighbourhood boundaries.

        Returns:
            List of validated NeighbourhoodRecord objects.
        """
        geojson = self._fetch_geojson(self.DATASETS["neighbourhoods"])
        features = geojson.get("features", [])

        records = []
        for feature in features:
            props = feature.get("properties", {})
            geometry = feature.get("geometry")

            # Use AREA_SHORT_CODE as the primary ID (1-158 range)
            # AREA_ID is a large internal identifier not useful for our schema
            short_code = props.get("AREA_SHORT_CODE") or props.get(
                "area_short_code", ""
            )
            if short_code:
                area_id = int("".join(c for c in str(short_code) if c.isdigit()) or "0")
            else:
                # Fallback to _id (row number) if AREA_SHORT_CODE not available
                area_id = int(props.get("_id", 0))

            if area_id == 0:
                logger.warning(f"Skipping neighbourhood with no valid ID: {props}")
                continue

            area_name = (
                props.get("AREA_NAME")
                or props.get("area_name")
                or f"Neighbourhood {area_id}"
            )

            records.append(
                NeighbourhoodRecord(
                    area_id=area_id,
                    area_name=str(area_name),
                    area_short_code=str(short_code) if short_code else None,
                    geometry=geometry,
                )
            )

        logger.info(f"Parsed {len(records)} neighbourhoods")
        return records

    # Mapping of indicator names to CensusRecord fields
    # Keys are partial matches (case-insensitive) found in the "Characteristic" column
    # Order matters - first match wins, so more specific patterns come first
    # Supports both 2016 datastore and 2021 XLSX indicator names
    # Note: owner/renter counts are raw numbers, not percentages - calculated in dbt
    CENSUS_INDICATOR_MAPPING: dict[str, str] = {
        "population, 2021": "population",
        "population, 2016": "population",
        "total - age groups of the population": "population",  # 2021 XLSX
        "population density per square kilometre": "population_density",
        "median total income of household in": "median_household_income",  # 2021 singular
        "median total income of households in": "median_household_income",  # 2016 plural
        "average total income of household in": "average_household_income",  # 2021 singular
        "average total income of households in": "average_household_income",  # 2016 plural
        "median age of the population": "median_age",  # 2021 XLSX direct
        "unemployment rate": "unemployment_rate",
        "average value of dwellings": "average_dwelling_value",
        # Note: bachelor's degree is handled separately (count -> percentage computation)
    }

    # Age group patterns for computing median age from distribution data.
    # Maps characteristic substring -> (age_lower, age_upper) for midpoint calc.
    # Uses broad age groups from the "Age characteristics" topic.
    _AGE_GROUP_PATTERNS: list[tuple[str, int, int]] = [
        ("children (0-14 years)", 0, 14),
        ("youth (15-24 years)", 15, 24),
        ("working age (25-54 years)", 25, 54),
        ("pre-retirement (55-64 years)", 55, 64),
        ("seniors (65+ years)", 65, 90),
    ]

    def get_census_profiles(self, year: int = 2021) -> list[CensusRecord]:
        """Fetch neighbourhood census profiles.

        The Toronto Open Data neighbourhood profiles dataset is pivoted:
        - Rows are demographic indicators (e.g., "Population", "Median Income")
        - Columns are neighbourhoods (e.g., "Agincourt North", "Alderwood")

        This method transposes the data to create one CensusRecord per neighbourhood.
        Prefers the 2021 XLSX resource (158 neighbourhoods, complete data) over the
        2016 CKAN datastore (140 neighbourhoods, incomplete income data).

        Args:
            year: Census year (2016 or 2021).

        Returns:
            List of validated CensusRecord objects.
        """
        raw_records: list[dict[str, Any]] = []

        # Try 2021 XLSX first (158 neighbourhoods, complete data)
        if year == 2021:
            try:
                raw_records = self._fetch_xlsx_as_records(
                    self.DATASETS["neighbourhood_profiles"],
                    name_filter="2021",
                )
            except (ValueError, Exception) as e:
                logger.warning(
                    f"Could not fetch 2021 XLSX, falling back to datastore: {e}"
                )

        # Fall back to CKAN datastore (2016 format)
        if not raw_records:
            try:
                raw_records = self._fetch_csv_as_json(
                    self.DATASETS["neighbourhood_profiles"]
                )
            except ValueError as e:
                logger.warning(f"Could not fetch census profiles: {e}")
                return []

        if not raw_records:
            logger.warning("Census profiles dataset is empty")
            return []

        logger.info(f"Fetched {len(raw_records)} census profile rows")

        # Find the characteristic/indicator column name
        # Prioritize "Characteristic" over "Category" since both may exist
        sample_row = raw_records[0]
        char_col = None

        # First try exact match for Characteristic
        if "Characteristic" in sample_row:
            char_col = "Characteristic"
        else:
            # Fall back to pattern matching
            for col in sample_row:
                col_lower = col.lower()
                if "characteristic" in col_lower:
                    char_col = col
                    break

            # Last resort: try Category
            if not char_col:
                for col in sample_row:
                    if "category" in col.lower():
                        char_col = col
                        break

        if not char_col:
            # Try other common column names
            for candidate in ["Topic", "_id"]:
                if candidate in sample_row:
                    char_col = candidate
                    break

        if not char_col:
            logger.warning("Could not find characteristic column in census data")
            return []

        # Identify neighbourhood columns (exclude metadata columns)
        exclude_cols = {
            char_col,
            "_id",
            "Topic",
            "Data Source",
            "Characteristic",
            "Category",
        }
        neighbourhood_cols = [col for col in sample_row if col not in exclude_cols]

        logger.info(f"Found {len(neighbourhood_cols)} neighbourhood columns")

        # Build a lookup: neighbourhood_name -> {field: value}
        neighbourhood_data: dict[str, dict[str, Decimal | int | None]] = {
            col: {} for col in neighbourhood_cols
        }

        # Collect age group counts per neighbourhood for median age computation
        age_group_data: dict[str, list[tuple[int, int, int]]] = {
            col: [] for col in neighbourhood_cols
        }

        # Collect tenure counts per neighbourhood for owner/renter percentage
        # Keys: "total", "owner", "renter" -> count per neighbourhood
        tenure_data: dict[str, dict[str, int]] = {col: {} for col in neighbourhood_cols}

        # Collect education counts for bachelor's percentage computation
        # Keys: "total", "bachelors" -> count per neighbourhood
        education_data: dict[str, dict[str, int]] = {
            col: {} for col in neighbourhood_cols
        }

        # Process each row to extract indicator values
        # Track position for XLSX format (no Topic column)
        in_tenure_section = False
        in_education_section = False

        for row in raw_records:
            characteristic = str(row.get(char_col, "")).lower().strip()
            # Normalize smart quotes to ASCII for consistent pattern matching
            characteristic = characteristic.replace("\u2019", "'").replace(
                "\u2018", "'"
            )
            topic = str(row.get("Topic", "")).lower().strip()

            # Check for tenure rows
            # Supports both Topic-based matching (2016 datastore) and
            # positional matching (2021 XLSX which has no Topic column)
            tenure_key = None
            if "private households by tenure" in characteristic:
                tenure_key = "total"
                in_tenure_section = True
            elif topic == "household characteristics" or in_tenure_section:
                if characteristic == "owner":
                    tenure_key = "owner"
                elif characteristic == "renter":
                    tenure_key = "renter"
                    in_tenure_section = False  # Reset after renter
                elif in_tenure_section:
                    in_tenure_section = False  # Non-tenure row encountered

            if tenure_key:
                for col in neighbourhood_cols:
                    value = row.get(col)
                    if value is not None and value != "":
                        try:
                            str_val = str(value).replace(",", "").strip()
                            if str_val and str_val not in ("x", "X", "F", ".."):
                                tenure_data[col][tenure_key] = int(Decimal(str_val))
                        except (ValueError, TypeError):
                            pass

            # Check for education rows (bachelor's degree percentage)
            # Track the "15 years and over" education section (first occurrence)
            edu_key = None
            if (
                "highest certificate, diploma or degree"
                " for the population aged 15" in characteristic
            ):
                edu_key = "total"
                in_education_section = True
            elif in_education_section:
                if "bachelor's degree or higher" in characteristic:
                    edu_key = "bachelors"
                    in_education_section = False
                elif (
                    "total - highest certificate" in characteristic
                    or "total - major field" in characteristic
                ):
                    # Hit next section, reset
                    in_education_section = False

            if edu_key:
                for col in neighbourhood_cols:
                    value = row.get(col)
                    if value is not None and value != "":
                        try:
                            str_val = str(value).replace(",", "").strip()
                            if str_val and str_val not in (
                                "x",
                                "X",
                                "F",
                                "..",
                            ):
                                education_data[col][edu_key] = int(Decimal(str_val))
                        except (ValueError, TypeError):
                            pass

            # Check for age group rows (for median age computation)
            for pattern, age_lo, age_hi in self._AGE_GROUP_PATTERNS:
                if pattern in characteristic:
                    for col in neighbourhood_cols:
                        value = row.get(col)
                        if value is not None and value != "":
                            try:
                                str_val = str(value).replace(",", "").strip()
                                if str_val and str_val not in ("x", "X", "F", ".."):
                                    count = int(Decimal(str_val))
                                    age_group_data[col].append((age_lo, age_hi, count))
                            except (ValueError, TypeError):
                                pass
                    break

            # Check if this row matches any indicator we care about
            for indicator_pattern, field_name in self.CENSUS_INDICATOR_MAPPING.items():
                if indicator_pattern in characteristic:
                    # Extract values for each neighbourhood
                    for col in neighbourhood_cols:
                        value = row.get(col)
                        if value is not None and value != "":
                            try:
                                # Clean and convert value
                                str_val = str(value).replace(",", "").replace("$", "")
                                str_val = str_val.replace("%", "").strip()
                                if str_val and str_val not in ("x", "X", "F", ".."):
                                    numeric_val = Decimal(str_val)
                                    # Only store if not already set (first match wins)
                                    if field_name not in neighbourhood_data[col]:
                                        neighbourhood_data[col][
                                            field_name
                                        ] = numeric_val
                            except (ValueError, TypeError):
                                pass
                    break  # Move to next row after matching

        # Compute median age from age group distributions
        for col in neighbourhood_cols:
            groups = age_group_data[col]
            if not groups:
                continue
            total_pop = sum(count for _, _, count in groups)
            if total_pop <= 0:
                continue
            # Sort by lower bound and find the group containing the median
            groups.sort(key=lambda g: g[0])
            cumulative = 0
            half = total_pop / 2
            for age_lo, age_hi, count in groups:
                cumulative += count
                if cumulative >= half:
                    # Interpolate within the group
                    prev_cumulative = cumulative - count
                    fraction = (half - prev_cumulative) / count if count > 0 else 0.5
                    midpoint = age_lo + fraction * (age_hi - age_lo)
                    neighbourhood_data[col]["median_age"] = Decimal(
                        str(round(midpoint, 1))
                    )
                    break

        # Compute owner/renter percentages from tenure counts
        for col in neighbourhood_cols:
            td = tenure_data[col]
            total = td.get("total", 0)
            if total > 0:
                owner = td.get("owner", 0)
                renter = td.get("renter", 0)
                neighbourhood_data[col]["pct_owner_occupied"] = Decimal(
                    str(round(owner / total * 100, 1))
                )
                neighbourhood_data[col]["pct_renter_occupied"] = Decimal(
                    str(round(renter / total * 100, 1))
                )

        # Compute bachelor's degree percentage from education counts
        for col in neighbourhood_cols:
            ed = education_data[col]
            total = ed.get("total", 0)
            if total > 0:
                bachelors = ed.get("bachelors", 0)
                neighbourhood_data[col]["pct_bachelors_or_higher"] = Decimal(
                    str(round(bachelors / total * 100, 1))
                )

        # Convert to CensusRecord objects
        records = []
        unmatched = []

        for neighbourhood_name, data in neighbourhood_data.items():
            if not data:
                continue

            # Match neighbourhood name to ID
            neighbourhood_id = self._match_neighbourhood_id(neighbourhood_name)
            if neighbourhood_id is None:
                unmatched.append(neighbourhood_name)
                continue

            try:
                pop_val = data.get("population")
                population = int(pop_val) if pop_val is not None else None

                record = CensusRecord(
                    neighbourhood_id=neighbourhood_id,
                    census_year=year,
                    population=population,
                    population_density=data.get("population_density"),
                    median_household_income=data.get("median_household_income"),
                    average_household_income=data.get("average_household_income"),
                    unemployment_rate=data.get("unemployment_rate"),
                    pct_bachelors_or_higher=data.get("pct_bachelors_or_higher"),
                    pct_owner_occupied=data.get("pct_owner_occupied"),
                    pct_renter_occupied=data.get("pct_renter_occupied"),
                    median_age=data.get("median_age"),
                    average_dwelling_value=data.get("average_dwelling_value"),
                )
                records.append(record)
            except Exception as e:
                logger.debug(f"Skipping neighbourhood {neighbourhood_name}: {e}")

        if unmatched:
            logger.warning(
                f"Could not match {len(unmatched)} neighbourhoods: {unmatched[:5]}..."
            )

        logger.info(f"Parsed {len(records)} census records for year {year}")
        return records

    def get_neighbourhood_profiles(self, year: int = 2021) -> list[ProfileRecord]:
        """Fetch neighbourhood community profile data from Statistics Canada.

        The Toronto Open Data neighbourhood profiles dataset is pivoted:
        - Rows are demographic characteristics (e.g., "Born in Africa", "English")
        - Columns are neighbourhoods

        This method transposes the data to create one ProfileRecord per
        neighbourhood-category-subcategory combination.

        Only supports 2021 XLSX data (158 neighbourhoods, most complete).
        Returns empty list with warning for other years.

        Args:
            year: Census year. Only 2021 is supported.

        Returns:
            List of validated ProfileRecord objects.
        """
        if year != 2021:
            logger.warning(f"Neighbourhood profiles only available for 2021; got {year}")
            return []

        raw_records: list[dict[str, Any]] = []
        try:
            raw_records = self._fetch_xlsx_as_records(
                self.DATASETS["neighbourhood_profiles"],
                name_filter="2021",
            )
        except (ValueError, Exception) as e:
            logger.warning(f"Could not fetch 2021 neighbourhood profiles: {e}")
            return []

        if not raw_records:
            logger.warning("Neighbourhood profiles dataset is empty")
            return []

        logger.info(f"Fetched {len(raw_records)} profile rows")

        # Identify neighbourhood columns (exclude metadata)
        sample_row = raw_records[0]
        exclude_cols = {
            "Characteristic",
            "Category",
            "_id",
            "Topic",
            "Data Source",
        }
        neighbourhood_cols = [col for col in sample_row if col not in exclude_cols]
        logger.info(f"Found {len(neighbourhood_cols)} neighbourhood columns")

        # Tag rows by category using state machine
        tagged_rows = self._tag_profile_rows(raw_records)

        # Build mapping of neighbourhood column to ID
        col_to_id: dict[str, int] = {}
        for col in neighbourhood_cols:
            neighbourhood_id = self._match_neighbourhood_id(col)
            if neighbourhood_id is not None:
                col_to_id[col] = neighbourhood_id

        if not col_to_id:
            logger.warning("Could not match any neighbourhood columns to IDs")
            return []

        logger.info(
            f"Matched {len(col_to_id)} neighbourhood columns to IDs "
            f"(out of {len(neighbourhood_cols)} total)"
        )

        # Build records by category, applying filters where needed
        records = self._build_profile_records(tagged_rows, col_to_id, year)

        logger.info(f"Parsed {len(records)} profile records for year {year}")
        return records

    def _tag_profile_rows(
        self, raw_records: list[dict[str, Any]]
    ) -> list[tuple[str, str, str, dict[str, Any]]]:
        """Tag profile rows with category, subcategory, and level.

        Extracts rows from specific community profile sections using exact
        section header matching. Avoids false matches from demographic sections.

        Tags each row as (category, subcategory, level, row_dict).

        Skips:
        - Header rows (starting with "Total - ")
        - Rows with empty characteristic
        - Aggregate sub-totals (rows containing "Total")

        Place-of-birth rows are tagged with level (continent vs country)
        by matching subcategory against known continent names.

        Args:
            raw_records: Raw records from XLSX fetch.

        Returns:
            List of (category, subcategory, level, row_dict) tuples.
        """
        # Exact section header mappings for community profile categories
        # Using specific text patterns to avoid matching related sections
        # (e.g., "mother tongue" section vs "language spoken at home" section)
        profile_sections: dict[str, str] = {
            "knowledge of official languages for the population in private": "official_language",
            "citizenship for the population in private households": "citizenship",
            "immigrant status and period of immigration for the population": "immigration_status",
            "place of birth for the immigrant population in private households - 25%": "place_of_birth",
            "place of birth for the recent immigrant population in private": "place_of_birth_recent",
            "generation status for the population in private households - 25%": "generation_status",
            "admission category and applicant type for the immigrant population": "admission_category",
            "visible minority for the population in private households - 25%": "visible_minority",
            "ethnic or cultural origin for the population in private": "ethnic_origin",
            "total - mother tongue for the population in private households - 25%": "mother_tongue",
        }

        # Find all profile section header rows
        section_headers: list[tuple[int, str, str]] = []  # (index, header_text, category)

        for idx, row in enumerate(raw_records):
            characteristic = str(row.get("Characteristic", "")).strip()
            if not characteristic:
                continue

            char_lower = characteristic.lower()

            # Check for exact profile section matches
            for header_anchor, category in profile_sections.items():
                if header_anchor in char_lower:
                    section_headers.append((idx, characteristic, category))
                    logger.debug(f"Found section: {category} at row {idx}: {characteristic[:60]}")
                    break

        if not section_headers:
            logger.warning("No profile sections detected in XLSX data")
            return []

        logger.info(f"Detected {len(section_headers)} profile sections")

        # Extract rows between section headers
        tagged = []

        for sec_idx, (header_idx, _header_text, category) in enumerate(section_headers):
            # Find end of this section
            # Stop at the next profile section header OR any "Total - " header
            # (since there may be intermediate "Total - " headers between profile sections)
            next_header_idx = len(raw_records)

            if sec_idx + 1 < len(section_headers):
                next_header_idx = section_headers[sec_idx + 1][0]
            else:
                # For the last profile section, find the next "Total - " header
                for row_idx in range(header_idx + 1, len(raw_records)):
                    char = str(raw_records[row_idx].get("Characteristic", "")).strip().lower()
                    if char.startswith("total -"):
                        next_header_idx = row_idx
                        break

            # Collect rows in this section (skip the header itself)
            section_rows = 0
            for row_idx in range(header_idx + 1, next_header_idx):
                row = raw_records[row_idx]
                characteristic = str(row.get("Characteristic", "")).strip()

                if not characteristic:
                    continue

                # Skip ANY "Total" rows (they're section headers, not data)
                if characteristic.lower().startswith("total -"):
                    # Stop at next section header
                    next_header_idx = row_idx
                    break

                # Skip aggregate sub-totals (rows that just contain "Total")
                if characteristic.lower() == "total":
                    continue

                # Subcategory is the characteristic itself
                subcategory = characteristic
                section_rows += 1

                # Detect level for place_of_birth categories
                level = ""
                if category in ("place_of_birth", "place_of_birth_recent"):
                    level = self._detect_place_of_birth_level(subcategory)

                tagged.append((category, subcategory, level, row))

            logger.debug(f"  {category:30} extracted {section_rows} subcategories")

        logger.debug(f"Tagged {len(tagged)} profile rows")
        return tagged

    def _parse_count(self, value: Any) -> int | None:
        """Parse a Statistics Canada count value.

        Strips commas from numbers and returns None for suppression codes.

        Args:
            value: Raw value from XLSX.

        Returns:
            Parsed integer count, or None if suppressed/invalid.
        """
        if value is None or value == "":
            return None

        str_val = str(value).strip()
        if not str_val:
            return None

        # Handle StatCan suppression codes
        if str_val in ("x", "X", "F", ".."):
            return None

        # Strip commas and convert
        try:
            clean = str_val.replace(",", "").strip()
            if clean and clean not in ("x", "X", "F", ".."):
                return int(clean)
        except (ValueError, TypeError):
            pass

        return None

    def _build_profile_records(
        self,
        tagged_rows: list[tuple[str, str, str, dict[str, Any]]],
        col_to_id: dict[str, int],
        year: int,
    ) -> list[ProfileRecord]:
        """Build ProfileRecord objects from tagged rows.

        Routes processing by category:
        - Standard categories: emit all rows for all neighbourhoods
        - ethnic_origin: apply top-30 city-wide filter
        - mother_tongue: apply per-neighbourhood top-15 filter

        Args:
            tagged_rows: Output from _tag_profile_rows.
            col_to_id: Mapping of neighbourhood column names to IDs.
            year: Census year.

        Returns:
            List of validated ProfileRecord objects.
        """
        # Organize rows by category for filtering
        rows_by_category: dict[str, list[tuple[str, str, str, dict[str, Any]]]] = {}
        for category, subcategory, level, row in tagged_rows:
            if category not in rows_by_category:
                rows_by_category[category] = []
            rows_by_category[category].append((category, subcategory, level, row))

        records = []

        # Process each category
        for category in rows_by_category:
            cat_rows = rows_by_category[category]

            if category == "ethnic_origin":
                # Apply top-30 city-wide filter
                cat_records = self._filter_ethnic_origin(cat_rows, col_to_id, year)
            elif category == "mother_tongue":
                # Apply per-neighbourhood top-15 filter
                cat_records = self._filter_mother_tongue(cat_rows, col_to_id, year)
            else:
                # Standard: emit all rows for all neighbourhoods
                cat_records = self._emit_category_records(cat_rows, col_to_id, year)

            records.extend(cat_records)

        return records

    def _emit_category_records(
        self,
        tagged_rows: list[tuple[str, str, str, dict[str, Any]]],
        col_to_id: dict[str, int],
        year: int,
    ) -> list[ProfileRecord]:
        """Emit ProfileRecord for all rows in a standard (non-filtered) category.

        Args:
            tagged_rows: Rows for this category from _tag_profile_rows.
            col_to_id: Neighbourhood ID mapping.
            year: Census year.

        Returns:
            List of ProfileRecord objects.
        """
        records = []

        for category, subcategory, level, row in tagged_rows:
            # Emit one record per neighbourhood
            for col, neighbourhood_id in col_to_id.items():
                value = row.get(col)
                count = self._parse_count(value)

                try:
                    record = ProfileRecord(
                        neighbourhood_id=neighbourhood_id,
                        census_year=year,
                        category=category,
                        subcategory=subcategory,
                        count=count,
                        level=level,
                    )
                    records.append(record)
                except Exception as e:
                    logger.debug(
                        f"Skipping record for {col}/"
                        f"{subcategory}: {e}"
                    )

        return records

    def _filter_ethnic_origin(
        self,
        tagged_rows: list[tuple[str, str, str, dict[str, Any]]],
        col_to_id: dict[str, int],
        year: int,
    ) -> list[ProfileRecord]:
        """Filter ethnic origin to top-30 by city-wide total.

        Computes the sum of counts across all neighbourhoods for each
        ethnic origin, keeps only the top-30, then emits records only for
        those ethnicities.

        Args:
            tagged_rows: Rows for ethnic_origin category.
            col_to_id: Neighbourhood ID mapping.
            year: Census year.

        Returns:
            List of ProfileRecord objects for top-30 ethnicities only.
        """
        # Compute city-wide total per subcategory
        subcategory_totals: dict[str, int] = {}

        for _category, subcategory, _level, row in tagged_rows:
            total = 0
            for col in col_to_id:
                count = self._parse_count(row.get(col))
                if count is not None:
                    total += count
            if total > 0:
                subcategory_totals[subcategory] = total

        # Get top-30 by city-wide total
        sorted_subs = sorted(
            subcategory_totals.items(), key=lambda x: x[1], reverse=True
        )
        top_30 = {sub for sub, _ in sorted_subs[:30]}

        logger.info(
            f"Ethnic origin: selected top-30 from {len(subcategory_totals)} total; "
            f"cutoff threshold: {sorted_subs[29][1] if len(sorted_subs) >= 30 else 'N/A'}"
        )

        # Emit records only for top-30 subcategories
        records = []
        for category, subcategory, level, row in tagged_rows:
            if subcategory not in top_30:
                continue

            for col, neighbourhood_id in col_to_id.items():
                value = row.get(col)
                count = self._parse_count(value)

                try:
                    record = ProfileRecord(
                        neighbourhood_id=neighbourhood_id,
                        census_year=year,
                        category=category,
                        subcategory=subcategory,
                        count=count,
                        level=level,
                    )
                    records.append(record)
                except Exception as e:
                    logger.debug(
                        f"Skipping ethnic origin record for {col}/"
                        f"{subcategory}: {e}"
                    )

        return records

    def _filter_mother_tongue(
        self,
        tagged_rows: list[tuple[str, str, str, dict[str, Any]]],
        col_to_id: dict[str, int],
        year: int,
    ) -> list[ProfileRecord]:
        """Filter mother tongue to per-neighbourhood top-15 non-official + official.

        For each neighbourhood:
        - Collect all mother tongue rows (official + non-official)
        - Rank non-official by count
        - Keep top-15 non-official + always include English and French
        - Emit records for these languages only

        Skips aggregate rows like "Non-official languages" that don't represent
        individual languages.

        Args:
            tagged_rows: Rows for mother_tongue category.
            col_to_id: Neighbourhood ID mapping.
            year: Census year.

        Returns:
            List of ProfileRecord objects with per-neighbourhood top-15 filtering.
        """
        # Aggregate rows: skip these
        skip_patterns = {"non-official", "official", "other"}

        records = []

        # Process each neighbourhood independently
        for neighbourhood_col, neighbourhood_id in col_to_id.items():
            # Collect language counts for this neighbourhood
            lang_counts: dict[str, int] = {}

            for _category, subcategory, _level, row in tagged_rows:
                # Skip aggregate rows
                subcat_lower = subcategory.lower()
                if any(pat in subcat_lower for pat in skip_patterns):
                    continue

                # Get count for this neighbourhood
                count = self._parse_count(row.get(neighbourhood_col))
                if count is not None:
                    lang_counts[subcategory] = count

            # Identify official languages
            # Only include English and French (exact two languages, no variants)
            official_langs = set()
            for _category, subcategory, _level, _row in tagged_rows:
                subcat_lower = subcategory.lower().strip()
                # Match only English and French (the two official languages)
                if subcat_lower in ("english", "french"):
                    official_langs.add(subcategory)

            # Rank non-official by count, keep top-15 + official
            non_official = [
                (lang, count)
                for lang, count in lang_counts.items()
                if lang not in official_langs
            ]
            non_official.sort(key=lambda x: x[1], reverse=True)
            top_15_non_official = {lang for lang, _ in non_official[:15]}

            # Combine: top-15 non-official + all official
            include_langs = top_15_non_official | official_langs

            logger.debug(
                f"Mother tongue for neighbourhood {neighbourhood_id}: "
                f"keeping {len(include_langs)} languages "
                f"(top-15 non-official + {len(official_langs)} official)"
            )

            # Emit records for included languages only
            for category, subcategory, level, row in tagged_rows:
                if subcategory not in include_langs:
                    continue

                count = self._parse_count(row.get(neighbourhood_col))

                try:
                    record = ProfileRecord(
                        neighbourhood_id=neighbourhood_id,
                        census_year=year,
                        category=category,
                        subcategory=subcategory,
                        count=count,
                        level=level,
                    )
                    records.append(record)
                except Exception as e:
                    logger.debug(
                        f"Skipping mother tongue record for neighbourhood "
                        f"{neighbourhood_id}/{subcategory}: {e}"
                    )

        return records

    def _detect_place_of_birth_level(self, characteristic_text: str) -> str:
        """Detect place-of-birth level (continent vs country).

        Matches the characteristic text (subcategory) against known continent
        names to distinguish continent-level rows from country-level rows.

        Args:
            characteristic_text: The characteristic/subcategory text.

        Returns:
            'continent' if text matches a known continent, else 'country'.
        """
        text_lower = characteristic_text.lower().strip()
        # Extract subcategory (remove any leading prefixes like "Total -")
        if " - " in text_lower:
            parts = text_lower.split(" - ")
            subcategory = parts[-1].strip()
        else:
            subcategory = text_lower

        # Check against known continents
        if subcategory in self._POB_CONTINENTS:
            return "continent"
        return "country"

    def _build_spatial_index(self) -> None:
        """Build spatial index from neighbourhood boundaries for point-in-polygon lookups."""
        from shapely.geometry import shape
        from shapely.strtree import STRtree

        neighbourhoods = self.get_neighbourhoods()
        geometries = []
        ids: list[int] = []
        for n in neighbourhoods:
            if n.geometry:
                geom = shape(n.geometry)
                geometries.append(geom)
                ids.append(n.area_id)

        tree = STRtree(geometries)
        self._spatial_index = (tree, geometries, ids)
        logger.info(f"Built spatial index with {len(ids)} neighbourhood polygons")

    def _assign_neighbourhood_id(self, lat: float, lon: float) -> int:
        """Find neighbourhood containing a point using spatial index.

        Returns:
            Neighbourhood ID, or 0 if no match found.
        """
        from shapely.geometry import Point

        if self._spatial_index is None:
            self._build_spatial_index()

        tree, geometries, ids = self._spatial_index  # type: ignore[misc]
        point = Point(lon, lat)
        # Use intersects for candidate filtering, then verify with contains
        candidates = tree.query(point, predicate="intersects")
        for idx in candidates:
            if geometries[idx].contains(point):
                return int(ids[idx])
        return 0

    def get_parks(self) -> list[AmenityRecord]:
        """Fetch park locations from parks-and-recreation-facilities dataset.

        Filters to TYPE='Park' records only.

        Returns:
            List of validated AmenityRecord objects.
        """
        return self._fetch_amenities(
            self.DATASETS["parks"],
            AmenityType.PARK,
            name_field="ASSET_NAME",
            address_field="ADDRESS",
            type_filter="Park",
        )

    def get_schools(self) -> list[AmenityRecord]:
        """Fetch school locations.

        Returns:
            List of validated AmenityRecord objects.
        """
        return self._fetch_amenities(
            self.DATASETS["schools"],
            AmenityType.SCHOOL,
            name_field="NAME",
            address_field="ADDRESS_FULL",
        )

    def get_childcare_centres(self) -> list[AmenityRecord]:
        """Fetch licensed childcare centre locations.

        Returns:
            List of validated AmenityRecord objects.
        """
        return self._fetch_amenities(
            self.DATASETS["childcare"],
            AmenityType.CHILDCARE,
            name_field="LOC_NAME",
            address_field="ADDRESS",
        )

    def get_community_centres(self) -> list[AmenityRecord]:
        """Fetch community centre locations from parks-and-recreation-facilities dataset.

        Filters to TYPE='Community Centre' records only.

        Returns:
            List of validated AmenityRecord objects.
        """
        return self._fetch_amenities(
            self.DATASETS["parks"],
            AmenityType.COMMUNITY_CENTRE,
            name_field="ASSET_NAME",
            address_field="ADDRESS",
            type_filter="Community Centre",
        )

    def get_libraries(self) -> list[AmenityRecord]:
        """Fetch Toronto Public Library branch locations.

        Uses the library-branch-general-information dataset.

        Returns:
            List of validated AmenityRecord objects.
        """
        try:
            records = self._fetch_csv_as_json("library-branch-general-information")
        except (httpx.HTTPError, ValueError) as e:
            logger.warning(f"Could not fetch library data: {e}")
            return []

        amenity_records = []
        skipped_no_location = 0

        for record in records:
            # Only include physical branches (excludes bookmobiles, virtual branches)
            if str(record.get("PhysicalBranch", "0")) != "1":
                continue

            lat = record.get("Lat")
            lon = record.get("Long")

            # Skip if missing coordinates
            if not lat or not lon:
                skipped_no_location += 1
                continue

            try:
                lat_float = float(lat)
                lon_float = float(lon)
            except (ValueError, TypeError):
                skipped_no_location += 1
                continue

            # Use spatial matching to determine neighbourhood ID
            neighbourhood_id = self._assign_neighbourhood_id(lat_float, lon_float)
            if neighbourhood_id == 0:
                skipped_no_location += 1
                continue

            amenity_records.append(
                AmenityRecord(
                    amenity_name=str(record.get("BranchName", "Unknown Library")),
                    amenity_type=AmenityType.LIBRARY,
                    address=str(record.get("Address", "")),
                    latitude=lat_float,
                    longitude=lon_float,
                    neighbourhood_id=neighbourhood_id,
                )
            )

        if skipped_no_location > 0:
            logger.warning(
                f"Skipped {skipped_no_location} libraries without valid coordinates"
            )

        logger.info(f"Parsed {len(amenity_records)} library records")
        return amenity_records

    def get_transit_stops(self) -> list[AmenityRecord]:
        """Fetch TTC transit stop locations from GTFS data.

        Downloads the Merged GTFS ZIP, extracts stops.txt, and converts
        boarding stops to AmenityRecord objects. Deduplicates subway stations
        by parent_station to avoid counting multiple platforms per station.

        Returns:
            List of validated AmenityRecord objects.
        """
        try:
            raw_stops = self._fetch_gtfs_stops(self.DATASETS["transit_stops"])
        except (httpx.HTTPError, ValueError) as e:
            logger.warning(f"Could not fetch GTFS transit stops: {e}")
            return []

        if not raw_stops:
            logger.warning("GTFS stops.txt is empty")
            return []

        # Filter to boarding stops only:
        # location_type 0 or empty = stop/platform (boarding point)
        # Exclude: 1=station parent, 2=entrance, 3=node, 4=boarding area
        boarding_stops = [
            stop
            for stop in raw_stops
            if stop.get("location_type", "").strip() in ("0", "")
        ]

        logger.info(
            f"Filtered to {len(boarding_stops)} boarding stops "
            f"(from {len(raw_stops)} total GTFS records)"
        )

        # Deduplicate subway/streetcar platforms by parent_station:
        # Multiple platforms at the same station should count as one stop.
        # Bus stops have no parent_station so they pass through.
        seen_parents: set[str] = set()
        unique_stops: list[dict[str, str]] = []

        for stop in boarding_stops:
            parent = stop.get("parent_station", "").strip()
            if parent:
                if parent in seen_parents:
                    continue
                seen_parents.add(parent)
            unique_stops.append(stop)

        logger.info(
            f"Deduplicated to {len(unique_stops)} unique stops "
            f"(removed {len(boarding_stops) - len(unique_stops)} duplicate platforms)"
        )

        # Convert to AmenityRecord objects with spatial join
        records = []
        skipped = 0

        for stop in unique_stops:
            try:
                lat = float(stop.get("stop_lat", "0"))
                lon = float(stop.get("stop_lon", "0"))
            except (ValueError, TypeError):
                skipped += 1
                continue

            if lat == 0 or lon == 0:
                skipped += 1
                continue

            neighbourhood_id = self._assign_neighbourhood_id(lat, lon)
            if neighbourhood_id == 0:
                skipped += 1
                continue

            records.append(
                AmenityRecord(
                    neighbourhood_id=neighbourhood_id,
                    amenity_type=AmenityType.TRANSIT_STOP,
                    amenity_name=stop.get("stop_name", "Unknown")[:200],
                    address=None,
                    latitude=Decimal(str(lat)),
                    longitude=Decimal(str(lon)),
                )
            )

        if skipped:
            logger.warning(
                f"Skipped {skipped} transit stop records "
                f"(no valid location or neighbourhood match)"
            )

        logger.info(f"Parsed {len(records)} transit_stop records")
        return records

    def _fetch_amenities(
        self,
        package_id: str,
        amenity_type: AmenityType,
        name_field: str,
        address_field: str,
        type_filter: str | None = None,
    ) -> list[AmenityRecord]:
        """Fetch and parse amenity data from GeoJSON.

        Args:
            package_id: CKAN package ID.
            amenity_type: Type of amenity.
            name_field: Property name containing amenity name.
            address_field: Property name containing address.
            type_filter: Optional TYPE field value to filter records.

        Returns:
            List of AmenityRecord objects.
        """
        try:
            geojson = self._fetch_geojson(package_id)
        except (httpx.HTTPError, ValueError) as e:
            logger.warning(f"Could not fetch {package_id}: {e}")
            return []

        features = geojson.get("features", [])
        records = []
        skipped_no_location = 0

        for feature in features:
            props = feature.get("properties", {})
            geometry = feature.get("geometry")

            # Apply type filter if specified
            if type_filter and props.get("TYPE") != type_filter:
                continue

            # Get coordinates from geometry
            lat, lon = None, None
            if geometry and geometry.get("type") == "Point":
                coords = geometry.get("coordinates", [])
                if len(coords) >= 2:
                    lon, lat = coords[0], coords[1]

            # Try to determine neighbourhood_id from properties first
            neighbourhood_id = (
                props.get("AREA_ID")
                or props.get("area_id")
                or props.get("NEIGHBOURHOOD_ID")
                or 0
            )

            # Fall back to spatial join if no ID in properties
            if neighbourhood_id == 0 and lat is not None and lon is not None:
                neighbourhood_id = self._assign_neighbourhood_id(lat, lon)

            name = props.get(name_field) or props.get(name_field.lower()) or "Unknown"
            address = props.get(address_field) or props.get(address_field.lower())

            # Skip if we still don't have a neighbourhood assignment
            if neighbourhood_id == 0:
                skipped_no_location += 1
                continue

            records.append(
                AmenityRecord(
                    neighbourhood_id=int(neighbourhood_id),
                    amenity_type=amenity_type,
                    amenity_name=str(name)[:200],
                    address=str(address)[:300] if address else None,
                    latitude=Decimal(str(lat)) if lat else None,
                    longitude=Decimal(str(lon)) if lon else None,
                )
            )

        if skipped_no_location:
            logger.warning(
                f"Skipped {skipped_no_location} {amenity_type.value} records "
                f"(no neighbourhood match)"
            )
        logger.info(f"Parsed {len(records)} {amenity_type.value} records")
        return records
