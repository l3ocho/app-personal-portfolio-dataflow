"""Loader for CMHC rental data into fact_rentals."""

import logging
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from dataflow.toronto.models import DimCMHCZone, DimTime, FactRentals
from dataflow.toronto.schemas import CMHCAnnualSurvey, CMHCRentalRecord

from .base import get_session, upsert_by_key
from .dimensions import generate_date_key

logger = logging.getLogger(__name__)

# Toronto CMA zone code for CMA-level data
TORONTO_CMA_ZONE_CODE = "TORCMA"
TORONTO_CMA_ZONE_NAME = "Toronto CMA"


def load_cmhc_rentals(
    survey: CMHCAnnualSurvey,
    session: Session | None = None,
) -> int:
    """Load CMHC annual survey data into fact_rentals.

    Args:
        survey: Validated CMHC annual survey containing records.
        session: Optional existing session.

    Returns:
        Number of records loaded.
    """
    from datetime import date

    def _load(sess: Session) -> int:
        # Get zone key mapping
        zones = sess.query(DimCMHCZone).all()
        zone_map = {z.zone_code: z.zone_key for z in zones}

        # CMHC surveys are annual - use October 1st as reference date
        survey_date = date(survey.survey_year, 10, 1)
        date_key = generate_date_key(survey_date)

        # Verify time dimension exists
        time_dim = sess.query(DimTime).filter_by(date_key=date_key).first()
        if not time_dim:
            raise ValueError(
                f"Time dimension not found for date_key {date_key}. "
                "Load time dimension first."
            )

        records = []
        for record in survey.records:
            zone_key = zone_map.get(record.zone_code)
            if not zone_key:
                # Skip records for unknown zones
                continue

            fact = FactRentals(
                date_key=date_key,
                zone_key=zone_key,
                bedroom_type=record.bedroom_type.value,
                universe=record.universe,
                avg_rent=record.average_rent,
                vacancy_rate=record.vacancy_rate,
                turnover_rate=record.turnover_rate,
                rent_change_pct=record.rent_change_pct,
                reliability_code=record.average_rent_reliability.value
                if record.average_rent_reliability
                else None,
            )
            records.append(fact)

        inserted, updated = upsert_by_key(
            sess, FactRentals, records, ["date_key", "zone_key", "bedroom_type"]
        )
        return inserted + updated

    if session:
        return _load(session)
    with get_session() as sess:
        return _load(sess)


def load_cmhc_record(
    record: CMHCRentalRecord,
    survey_year: int,
    session: Session | None = None,
) -> int:
    """Load a single CMHC record into fact_rentals.

    Args:
        record: Single validated CMHC rental record.
        survey_year: Year of the survey.
        session: Optional existing session.

    Returns:
        Number of records loaded (0 or 1).
    """
    from datetime import date

    def _load(sess: Session) -> int:
        # Get zone key
        zone = sess.query(DimCMHCZone).filter_by(zone_code=record.zone_code).first()
        if not zone:
            return 0

        survey_date = date(survey_year, 10, 1)
        date_key = generate_date_key(survey_date)

        # Verify time dimension exists
        time_dim = sess.query(DimTime).filter_by(date_key=date_key).first()
        if not time_dim:
            raise ValueError(
                f"Time dimension not found for date_key {date_key}. "
                "Load time dimension first."
            )

        fact = FactRentals(
            date_key=date_key,
            zone_key=zone.zone_key,
            bedroom_type=record.bedroom_type.value,
            universe=record.universe,
            avg_rent=record.average_rent,
            vacancy_rate=record.vacancy_rate,
            turnover_rate=record.turnover_rate,
            rent_change_pct=record.rent_change_pct,
            reliability_code=record.average_rent_reliability.value
            if record.average_rent_reliability
            else None,
        )

        inserted, updated = upsert_by_key(
            sess, FactRentals, [fact], ["date_key", "zone_key", "bedroom_type"]
        )
        return inserted + updated

    if session:
        return _load(session)
    with get_session() as sess:
        return _load(sess)


def ensure_toronto_cma_zone(session: Session | None = None) -> int:
    """Ensure Toronto CMA zone exists in dim_cmhc_zone.

    Creates the zone if it doesn't exist.

    Args:
        session: Optional existing session.

    Returns:
        The zone_key for Toronto CMA.
    """

    def _ensure(sess: Session) -> int:
        zone = (
            sess.query(DimCMHCZone).filter_by(zone_code=TORONTO_CMA_ZONE_CODE).first()
        )
        if zone:
            return int(zone.zone_key)

        # Create new zone
        new_zone = DimCMHCZone(
            zone_code=TORONTO_CMA_ZONE_CODE,
            zone_name=TORONTO_CMA_ZONE_NAME,
            geometry=None,  # CMA-level doesn't need geometry
        )
        sess.add(new_zone)
        sess.flush()
        logger.info(f"Created Toronto CMA zone with zone_key={new_zone.zone_key}")
        return int(new_zone.zone_key)

    if session:
        return _ensure(session)
    with get_session() as sess:
        result = _ensure(sess)
        sess.commit()
        return result


def load_statcan_cmhc_data(
    records: list[Any],  # List of CMHCRentalRecord from statcan_cmhc parser
    session: Session | None = None,
) -> int:
    """Load CMHC rental data from StatCan parser into fact_rentals.

    This function handles CMA-level data from the StatCan API, which provides
    aggregate Toronto data rather than zone-level HMIP data.

    Args:
        records: List of CMHCRentalRecord dataclass instances from statcan_cmhc parser.
        session: Optional existing session.

    Returns:
        Number of records loaded.
    """
    from dataflow.toronto.parsers.statcan_cmhc import (
        CMHCRentalRecord as StatCanRecord,
    )

    def _load(sess: Session) -> int:
        # Ensure Toronto CMA zone exists
        zone_key = ensure_toronto_cma_zone(sess)

        loaded = 0
        for record in records:
            if not isinstance(record, StatCanRecord):
                logger.warning(f"Skipping invalid record type: {type(record)}")
                continue

            # Generate date key for this record's survey date
            survey_date = date(record.year, record.month, 1)
            date_key = generate_date_key(survey_date)

            # Verify time dimension exists
            time_dim = sess.query(DimTime).filter_by(date_key=date_key).first()
            if not time_dim:
                logger.warning(
                    f"Time dimension not found for {survey_date}, skipping record"
                )
                continue

            # Create fact record
            fact = FactRentals(
                date_key=date_key,
                zone_key=zone_key,
                bedroom_type=record.bedroom_type,
                universe=record.universe,
                avg_rent=float(record.avg_rent) if record.avg_rent else None,
                vacancy_rate=float(record.vacancy_rate)
                if record.vacancy_rate
                else None,
                turnover_rate=None,
                rent_change_pct=None,
                reliability_code=None,
            )

            # Upsert
            inserted, updated = upsert_by_key(
                sess, FactRentals, [fact], ["date_key", "zone_key", "bedroom_type"]
            )
            loaded += inserted + updated

        logger.info(f"Loaded {loaded} CMHC rental records from StatCan")
        return loaded

    if session:
        return _load(session)
    with get_session() as sess:
        result = _load(sess)
        sess.commit()
        return result


def load_excel_rental_data(
    excel_data: dict[int, list[Any]],  # year -> list of CMHCExcelRentalRecord
    session: Session | None = None,
) -> int:
    """Load full rental metrics from parsed CMHC Excel files into fact_rentals.

    Writes all available zone-level metrics (universe, avg_rent, vacancy_rate,
    turnover_rate, rent_change_pct, reliability_code) in a single upsert pass.
    Fields not available in Excel files (median_rent, availability_rate) are
    set to None.

    Args:
        excel_data: Dictionary mapping year to list of CMHCExcelRentalRecord
            objects from parse_cmhc_excel_rental_directory().
        session: Optional existing session.

    Returns:
        Number of records inserted or updated.
    """
    from dataflow.toronto.parsers.cmhc_excel import CMHCExcelRentalRecord

    def _load(sess: Session) -> int:
        facts_to_upsert = []

        for year, records in excel_data.items():
            survey_date = date(year, 10, 1)
            date_key = generate_date_key(survey_date)

            time_dim = sess.query(DimTime).filter_by(date_key=date_key).first()
            if not time_dim:
                logger.warning(
                    f"Time dimension not found for {survey_date}, skipping year {year}"
                )
                continue

            zones = sess.query(DimCMHCZone).all()
            zone_map = {z.zone_code: z.zone_key for z in zones}

            for record in records:
                if not isinstance(record, CMHCExcelRentalRecord):
                    logger.warning(f"Skipping invalid record type: {type(record)}")
                    continue

                zone_key = zone_map.get(record.zone_code)
                if not zone_key:
                    logger.debug(
                        f"Zone not found in dim_cmhc_zone: {record.zone_code}, skipping"
                    )
                    continue

                fact = FactRentals(
                    date_key=date_key,
                    zone_key=zone_key,
                    bedroom_type=record.bedroom_type,
                    universe=record.universe,
                    avg_rent=record.avg_rent,
                    vacancy_rate=record.vacancy_rate,
                    turnover_rate=record.turnover_rate,
                    rent_change_pct=record.rent_change_pct,
                    reliability_code=record.avg_rent_reliability,
                )
                facts_to_upsert.append(fact)

        if facts_to_upsert:
            inserted, updated = upsert_by_key(
                sess,
                FactRentals,
                facts_to_upsert,
                ["date_key", "zone_key", "bedroom_type"],
            )
            total = inserted + updated
            logger.info(
                f"Upserted {total} zone-level rental records from Excel "
                f"({inserted} inserted, {updated} updated)"
            )
            return total

        logger.warning("No valid rental records to upsert from Excel data")
        return 0

    if session:
        return _load(session)
    with get_session() as sess:
        result = _load(sess)
        sess.commit()
        return result


def update_universe_from_excel(
    excel_data: dict[int, list[Any]],  # year -> list of CMHCUniverseRecord
    session: Session | None = None,
) -> int:
    """Upsert fact_rentals records with universe data from Excel files.

    This function creates zone-level rental records with universe (total rental units)
    data from CMHC Excel files. The StatCan API only provides CMA-level aggregate data,
    so this adds detailed zone-level records.

    Args:
        excel_data: Dictionary mapping year to list of CMHCUniverseRecord objects
            from the cmhc_excel parser.
        session: Optional existing session.

    Returns:
        Number of records inserted or updated.
    """
    from dataflow.toronto.parsers.cmhc_excel import CMHCUniverseRecord

    def _upsert(sess: Session) -> int:
        facts_to_upsert = []

        for year, records in excel_data.items():
            # Get date key for October (CMHC survey month)
            survey_date = date(year, 10, 1)
            date_key = generate_date_key(survey_date)

            # Verify time dimension exists
            time_dim = sess.query(DimTime).filter_by(date_key=date_key).first()
            if not time_dim:
                logger.warning(
                    f"Time dimension not found for {survey_date}, skipping year {year}"
                )
                continue

            # Get zone key mapping
            zones = sess.query(DimCMHCZone).all()
            zone_map = {z.zone_code: z.zone_key for z in zones}

            for record in records:
                if not isinstance(record, CMHCUniverseRecord):
                    logger.warning(f"Skipping invalid record type: {type(record)}")
                    continue

                # Get zone_key for this zone
                zone_key = zone_map.get(record.zone_code)
                if not zone_key:
                    logger.debug(
                        f"Zone not found in dim_cmhc_zone: {record.zone_code}, skipping"
                    )
                    continue

                # Create fact record with universe only (rent/vacancy will be NULL)
                fact = FactRentals(
                    date_key=date_key,
                    zone_key=zone_key,
                    bedroom_type=record.bedroom_type,
                    universe=record.universe,
                    avg_rent=None,
                    vacancy_rate=None,
                    turnover_rate=None,
                    rent_change_pct=None,
                    reliability_code=None,
                )
                facts_to_upsert.append(fact)

        # Upsert all records
        if facts_to_upsert:
            inserted, updated = upsert_by_key(
                sess,
                FactRentals,
                facts_to_upsert,
                ["date_key", "zone_key", "bedroom_type"],
            )
            total = inserted + updated
            logger.info(
                f"Upserted {total} zone-level rental records with universe data "
                f"({inserted} inserted, {updated} updated)"
            )
            return total
        else:
            logger.warning("No valid records to upsert")
            return 0

    if session:
        return _upsert(session)
    with get_session() as sess:
        result = _upsert(sess)
        sess.commit()
        return result
