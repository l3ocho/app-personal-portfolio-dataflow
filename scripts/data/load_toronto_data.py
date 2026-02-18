#!/usr/bin/env python3
"""Load Toronto neighbourhood data into the database.

Usage:
    python scripts/data/load_toronto_data.py [OPTIONS]

Options:
    --skip-fetch    Skip API fetching, only run dbt
    --skip-dbt      Skip dbt run, only load data
    --dry-run       Show what would be done without executing
    -v, --verbose   Enable verbose logging

This script orchestrates:
1. Fetching data from Toronto Open Data and CMHC APIs
2. Loading data into PostgreSQL fact tables
3. Running dbt to transform staging -> intermediate -> marts

Exit codes:
    0 = Success
    1 = Error
"""

import argparse
import logging
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Load .env file so dbt can access POSTGRES_* environment variables
load_dotenv(PROJECT_ROOT / ".env")
sys.path.insert(0, str(PROJECT_ROOT))

from dataflow.toronto.loaders import (  # noqa: E402
    build_cmhc_neighbourhood_crosswalk,
    get_session,
    load_amenities,
    load_census_data,
    load_cmhc_zones,
    load_crime_data,
    load_excel_rental_data,
    load_neighbourhoods,
    load_statcan_cmhc_data,
    load_time_dimension,
)
from dataflow.toronto.parsers import (  # noqa: E402
    TorontoOpenDataParser,
    TorontoPoliceParser,
    parse_cmhc_excel_rental_directory,
)
from dataflow.toronto.parsers.geo import CMHCZoneParser  # noqa: E402
from dataflow.toronto.parsers.statcan_cmhc import (  # noqa: E402
    fetch_toronto_rental_data,
)
from dataflow.toronto.schemas import Neighbourhood  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


class DataPipeline:
    """Orchestrates data loading from APIs to database to dbt."""

    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.stats: dict[str, int] = {}

        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)

    def fetch_and_load(self) -> bool:
        """Fetch data from APIs and load into database.

        Returns:
            True if successful, False otherwise.
        """
        logger.info("Starting data fetch and load pipeline...")

        try:
            with get_session() as session:
                # 1. Load time dimension first (for date keys)
                self._load_time_dimension(session)

                # 2. Load neighbourhoods (required for foreign keys)
                self._load_neighbourhoods(session)

                # 3. Load CMHC zone geometries from GeoJSON
                self._load_cmhc_zones(session)

                # 4. Load census data
                self._load_census(session)

                # 5. Load crime data
                self._load_crime(session)

                # 6. Load amenities
                self._load_amenities(session)

                # 7. Load CMHC rental data from StatCan
                self._load_rentals(session)

                # 8. Build CMHC-neighbourhood crosswalk
                self._build_cmhc_crosswalk(session)

                session.commit()
                logger.info("All data committed to database")

            self._print_stats()
            return True

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            if self.verbose:
                import traceback

                traceback.print_exc()
            return False

    def _load_time_dimension(self, session: Any) -> None:
        """Load time dimension with date range for dashboard."""
        logger.info("Loading time dimension...")

        if self.dry_run:
            logger.info(
                "  [DRY RUN] Would load time dimension 2019-01-01 to 2025-12-01"
            )
            return

        count = load_time_dimension(
            start_date=date(2019, 1, 1),
            end_date=date(2025, 12, 1),
            session=session,
        )
        self.stats["time_dimension"] = count
        logger.info(f"  Loaded {count} time dimension records")

    def _load_neighbourhoods(self, session: Any) -> None:
        """Fetch and load neighbourhood boundaries."""
        logger.info("Fetching neighbourhoods from Toronto Open Data...")

        if self.dry_run:
            logger.info("  [DRY RUN] Would fetch and load neighbourhoods")
            return

        import json

        parser = TorontoOpenDataParser()
        raw_neighbourhoods = parser.get_neighbourhoods()

        # Convert NeighbourhoodRecord to Neighbourhood schema
        neighbourhoods = []
        for n in raw_neighbourhoods:
            # Convert GeoJSON geometry dict to WKT if present
            geometry_wkt = None
            if n.geometry:
                # Store as GeoJSON string for PostGIS ST_GeomFromGeoJSON
                geometry_wkt = json.dumps(n.geometry)

            neighbourhood = Neighbourhood(
                neighbourhood_id=n.area_id,
                name=n.area_name,
                geometry_wkt=geometry_wkt,
                population=None,  # Will be filled from census data
                land_area_sqkm=None,
                pop_density_per_sqkm=None,
                census_year=2021,
            )
            neighbourhoods.append(neighbourhood)

        count = load_neighbourhoods(neighbourhoods, session)
        self.stats["neighbourhoods"] = count
        logger.info(f"  Loaded {count} neighbourhoods")

    def _load_census(self, session: Any) -> None:
        """Fetch and load census profile data for 2016 and 2021."""
        logger.info("Fetching census profiles from Toronto Open Data...")

        if self.dry_run:
            logger.info("  [DRY RUN] Would fetch and load census data (2016 and 2021)")
            return

        parser = TorontoOpenDataParser()
        total_count = 0

        # Load 2016 census data
        try:
            logger.info("  Fetching 2016 census profiles...")
            census_records_2016 = parser.get_census_profiles(year=2016)
            if census_records_2016:
                count = load_census_data(census_records_2016, session)
                total_count += count
                logger.info(f"  Loaded {count} census records for 2016")
            else:
                logger.warning("  No 2016 census records fetched")
        except Exception as e:
            logger.warning(f"  Failed to load 2016 census data: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()

        # Load 2021 census data
        try:
            logger.info("  Fetching 2021 census profiles...")
            census_records_2021 = parser.get_census_profiles(year=2021)
            if census_records_2021:
                count = load_census_data(census_records_2021, session)
                total_count += count
                logger.info(f"  Loaded {count} census records for 2021")
            else:
                logger.warning("  No 2021 census records fetched")
        except Exception as e:
            logger.warning(f"  Failed to load 2021 census data: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()

        self.stats["census"] = total_count
        if total_count == 0:
            logger.warning("  No census records loaded")
        else:
            logger.info(f"  Total census records loaded: {total_count}")

    def _load_crime(self, session: Any) -> None:
        """Fetch and load crime statistics."""
        logger.info("Fetching crime data from Toronto Police Service...")

        if self.dry_run:
            logger.info("  [DRY RUN] Would fetch and load crime data")
            return

        parser = TorontoPoliceParser()
        crime_records = parser.get_crime_rates()

        if not crime_records:
            logger.warning("  No crime records fetched")
            return

        count = load_crime_data(crime_records, session)
        self.stats["crime"] = count
        logger.info(f"  Loaded {count} crime records")

    def _load_amenities(self, session: Any) -> None:
        """Fetch and load amenity data (parks, schools, childcare, libraries, community centres)."""
        logger.info("Fetching amenities from Toronto Open Data...")

        if self.dry_run:
            logger.info("  [DRY RUN] Would fetch and load amenity data")
            return

        parser = TorontoOpenDataParser()
        total_count = 0

        # Fetch parks
        try:
            parks = parser.get_parks()
            if parks:
                count = load_amenities(parks, year=2024, session=session)
                total_count += count
                logger.info(f"  Loaded {count} park amenities")
        except Exception as e:
            logger.warning(f"  Failed to load parks: {e}")

        # Fetch schools
        try:
            schools = parser.get_schools()
            if schools:
                count = load_amenities(schools, year=2024, session=session)
                total_count += count
                logger.info(f"  Loaded {count} school amenities")
        except Exception as e:
            logger.warning(f"  Failed to load schools: {e}")

        # Fetch childcare centres
        try:
            childcare = parser.get_childcare_centres()
            if childcare:
                count = load_amenities(childcare, year=2024, session=session)
                total_count += count
                logger.info(f"  Loaded {count} childcare amenities")
        except Exception as e:
            logger.warning(f"  Failed to load childcare: {e}")

        # Fetch libraries
        try:
            libraries = parser.get_libraries()
            if libraries:
                count = load_amenities(libraries, year=2024, session=session)
                total_count += count
                logger.info(f"  Loaded {count} library amenities")
        except Exception as e:
            logger.warning(f"  Failed to load libraries: {e}")

        # Fetch community centres
        try:
            community_centres = parser.get_community_centres()
            if community_centres:
                count = load_amenities(community_centres, year=2024, session=session)
                total_count += count
                logger.info(f"  Loaded {count} community centre amenities")
        except Exception as e:
            logger.warning(f"  Failed to load community centres: {e}")

        # Fetch transit stops (TTC GTFS data)
        try:
            transit_stops = parser.get_transit_stops()
            if transit_stops:
                count = load_amenities(transit_stops, year=2024, session=session)
                total_count += count
                logger.info(f"  Loaded {count} transit stop amenities")
        except Exception as e:
            logger.warning(f"  Failed to load transit stops: {e}")

        self.stats["amenities"] = total_count

    def _load_rentals(self, session: Any) -> None:
        """Fetch and load CMHC rental data from StatCan, then load full metrics from Excel."""
        logger.info("Fetching CMHC rental data from Statistics Canada...")

        if self.dry_run:
            logger.info("  [DRY RUN] Would fetch and load CMHC rental data")
            logger.info("  [DRY RUN] Would load zone-level rental metrics from Excel files")
            return

        try:
            # Fetch rental data from StatCan API (2014-present, CMA-level)
            rental_records = fetch_toronto_rental_data(start_year=2014)

            if not rental_records:
                logger.warning("  No rental records fetched")
                return

            count = load_statcan_cmhc_data(rental_records, session)
            self.stats["rentals"] = count
            logger.info(f"  Loaded {count} CMHC rental records from StatCan API")

            # Load zone-level rental metrics from Excel files
            logger.info("Loading zone-level rental metrics from CMHC Excel files...")
            cmhc_excel_dir = PROJECT_ROOT / "data" / "raw" / "cmhc"
            if cmhc_excel_dir.exists():
                excel_data = parse_cmhc_excel_rental_directory(
                    cmhc_excel_dir, start_year=2021
                )
                if excel_data:
                    updated_count = load_excel_rental_data(excel_data, session)
                    self.stats["excel_rental_updates"] = updated_count
                    logger.info(
                        f"  Loaded {updated_count} zone-level rental records from Excel"
                    )
                else:
                    logger.warning("  No rental data parsed from Excel files")
            else:
                logger.warning(f"  CMHC Excel directory not found: {cmhc_excel_dir}")

        except Exception as e:
            logger.warning(f"  Failed to load CMHC rental data: {e}")
            if self.verbose:
                import traceback

                traceback.print_exc()

    def _load_cmhc_zones(self, session: Any) -> None:
        """Load CMHC zone geometries from GeoJSON."""
        logger.info("Loading CMHC zone geometries from GeoJSON...")

        if self.dry_run:
            logger.info("  [DRY RUN] Would load CMHC zone geometries")
            return

        try:
            geojson_path = (
                PROJECT_ROOT / "data" / "toronto" / "raw" / "geo" / "cmhc_zones.geojson"
            )
            if not geojson_path.exists():
                logger.warning(f"  CMHC zones GeoJSON not found: {geojson_path}")
                return

            parser = CMHCZoneParser(geojson_path)
            zones = parser.parse()
            count = load_cmhc_zones(zones, session)
            self.stats["cmhc_zones"] = count
            logger.info(f"  Loaded {count} CMHC zone geometries")
        except Exception as e:
            logger.warning(f"  Failed to load CMHC zones: {e}")
            if self.verbose:
                import traceback

                traceback.print_exc()

    def _build_cmhc_crosswalk(self, session: Any) -> None:
        """Compute TORCMA geometry and build crosswalk."""
        logger.info("Building CMHC-neighbourhood crosswalk...")

        if self.dry_run:
            logger.info("  [DRY RUN] Would build crosswalk")
            return

        from sqlalchemy import text

        try:
            # Compute TORCMA geometry as neighbourhood union
            session.execute(
                text(
                    """
                UPDATE raw_toronto.dim_cmhc_zone
                SET geometry = (
                    SELECT ST_Multi(ST_Union(geometry))
                    FROM raw_toronto.dim_neighbourhood
                    WHERE geometry IS NOT NULL
                )
                WHERE zone_code = 'TORCMA'
            """
                )
            )
            logger.info("  Computed TORCMA geometry")

            # Build crosswalk using PostGIS spatial joins
            count = build_cmhc_neighbourhood_crosswalk(session)
            self.stats["cmhc_crosswalk"] = count
            logger.info(f"  Built {count} crosswalk records")
        except Exception as e:
            logger.warning(f"  Failed to build crosswalk: {e}")
            if self.verbose:
                import traceback

                traceback.print_exc()

    def run_dbt(self) -> bool:
        """Run dbt to transform data.

        Returns:
            True if successful, False otherwise.
        """
        logger.info("Running dbt transformations...")

        dbt_project_dir = PROJECT_ROOT / "dbt"
        venv_dbt = PROJECT_ROOT / ".venv" / "bin" / "dbt"

        # Use venv dbt if available, otherwise fall back to system dbt
        dbt_cmd = str(venv_dbt) if venv_dbt.exists() else "dbt"

        if not dbt_project_dir.exists():
            logger.error(f"dbt project directory not found: {dbt_project_dir}")
            return False

        if self.dry_run:
            logger.info("  [DRY RUN] Would run: dbt deps")
            logger.info("  [DRY RUN] Would run: dbt run")
            logger.info("  [DRY RUN] Would run: dbt test")
            return True

        try:
            # Install dbt packages if needed
            logger.info("  Running dbt deps...")
            result = subprocess.run(
                [dbt_cmd, "deps", "--profiles-dir", str(dbt_project_dir)],
                cwd=dbt_project_dir,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                logger.error(f"dbt deps failed:\n{result.stdout}\n{result.stderr}")
                return False

            # Run dbt models
            logger.info("  Running dbt run...")
            result = subprocess.run(
                [dbt_cmd, "run", "--profiles-dir", str(dbt_project_dir)],
                cwd=dbt_project_dir,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                logger.error(f"dbt run failed:\n{result.stdout}\n{result.stderr}")
                return False

            logger.info("  dbt run completed successfully")

            # Run dbt tests
            logger.info("  Running dbt test...")
            result = subprocess.run(
                [dbt_cmd, "test", "--profiles-dir", str(dbt_project_dir)],
                cwd=dbt_project_dir,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                logger.warning(
                    f"dbt test had failures:\n{result.stdout}\n{result.stderr}"
                )
                # Don't fail on test failures, just warn
            else:
                logger.info("  dbt test completed successfully")

            return True

        except FileNotFoundError:
            logger.error(
                "dbt not found in PATH. Install with: pip install dbt-postgres"
            )
            return False
        except Exception as e:
            logger.error(f"dbt execution failed: {e}")
            return False

    def _print_stats(self) -> None:
        """Print loading statistics."""
        if not self.stats:
            return

        logger.info("Loading statistics:")
        for key, count in self.stats.items():
            logger.info(f"  {key}: {count} records")


def main() -> int:
    """Main entry point for the data loading script."""
    parser = argparse.ArgumentParser(
        description="Load Toronto neighbourhood data into the database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--skip-fetch",
        action="store_true",
        help="Skip API fetching, only run dbt",
    )
    parser.add_argument(
        "--skip-dbt",
        action="store_true",
        help="Skip dbt run, only load data",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.skip_fetch and args.skip_dbt:
        logger.error("Cannot skip both fetch and dbt - nothing to do")
        return 1

    pipeline = DataPipeline(dry_run=args.dry_run, verbose=args.verbose)

    # Execute pipeline stages
    if not args.skip_fetch and not pipeline.fetch_and_load():
        return 1

    if not args.skip_dbt and not pipeline.run_dbt():
        return 1

    logger.info("Pipeline completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
