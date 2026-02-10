"""Loaders for dimension tables."""

from datetime import date

from sqlalchemy.orm import Session

from portfolio_app.toronto.models import (
    DimCMHCZone,
    DimNeighbourhood,
    DimPolicyEvent,
    DimTime,
)
from portfolio_app.toronto.schemas import (
    CMHCZone,
    Neighbourhood,
    PolicyEvent,
)

from .base import get_session, upsert_by_key


def generate_date_key(d: date) -> int:
    """Generate integer date key from date (YYYYMMDD format).

    Args:
        d: Date to convert.

    Returns:
        Integer in YYYYMMDD format.
    """
    return d.year * 10000 + d.month * 100 + d.day


def load_time_dimension(
    start_date: date,
    end_date: date,
    session: Session | None = None,
) -> int:
    """Load time dimension with date range.

    Args:
        start_date: Start of date range.
        end_date: End of date range (inclusive).
        session: Optional existing session.

    Returns:
        Number of records loaded.
    """

    month_names = [
        "",
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]

    def _load(sess: Session) -> int:
        records = []
        current = start_date.replace(day=1)  # Start at month beginning

        while current <= end_date:
            quarter = (current.month - 1) // 3 + 1
            dim = DimTime(
                date_key=generate_date_key(current),
                full_date=current,
                year=current.year,
                month=current.month,
                quarter=quarter,
                month_name=month_names[current.month],
                is_month_start=True,
            )
            records.append(dim)

            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

        inserted, updated = upsert_by_key(sess, DimTime, records, ["date_key"])
        return inserted + updated

    if session:
        return _load(session)
    with get_session() as sess:
        return _load(sess)


def load_cmhc_zones(
    zones: list[CMHCZone],
    session: Session | None = None,
) -> int:
    """Load CMHC zone dimension.

    Args:
        zones: List of validated zone schemas.
        session: Optional existing session.

    Returns:
        Number of records loaded.
    """

    def _load(sess: Session) -> int:
        records = []
        for z in zones:
            dim = DimCMHCZone(
                zone_code=z.zone_code,
                zone_name=z.zone_name,
                geometry=z.geometry_wkt,
            )
            records.append(dim)

        inserted, updated = upsert_by_key(sess, DimCMHCZone, records, ["zone_code"])
        return inserted + updated

    if session:
        return _load(session)
    with get_session() as sess:
        return _load(sess)


def load_neighbourhoods(
    neighbourhoods: list[Neighbourhood],
    session: Session | None = None,
) -> int:
    """Load neighbourhood dimension.

    Args:
        neighbourhoods: List of validated neighbourhood schemas.
        session: Optional existing session.

    Returns:
        Number of records loaded.
    """

    def _load(sess: Session) -> int:
        records = []
        for n in neighbourhoods:
            dim = DimNeighbourhood(
                neighbourhood_id=n.neighbourhood_id,
                name=n.name,
                geometry=n.geometry_wkt,
                population=n.population,
                land_area_sqkm=n.land_area_sqkm,
                pop_density_per_sqkm=n.pop_density_per_sqkm,
                pct_bachelors_or_higher=n.pct_bachelors_or_higher,
                median_household_income=n.median_household_income,
                pct_owner_occupied=n.pct_owner_occupied,
                pct_renter_occupied=n.pct_renter_occupied,
                census_year=n.census_year,
            )
            records.append(dim)

        inserted, updated = upsert_by_key(
            sess, DimNeighbourhood, records, ["neighbourhood_id"]
        )
        return inserted + updated

    if session:
        return _load(session)
    with get_session() as sess:
        return _load(sess)


def load_policy_events(
    events: list[PolicyEvent],
    session: Session | None = None,
) -> int:
    """Load policy event dimension.

    Args:
        events: List of validated policy event schemas.
        session: Optional existing session.

    Returns:
        Number of records loaded.
    """

    def _load(sess: Session) -> int:
        records = []
        for e in events:
            dim = DimPolicyEvent(
                event_date=e.event_date,
                effective_date=e.effective_date,
                level=e.level.value,
                category=e.category.value,
                title=e.title,
                description=e.description,
                expected_direction=e.expected_direction.value,
                source_url=e.source_url,
                confidence=e.confidence.value,
            )
            records.append(dim)

        # For policy events, use event_date + title as unique key
        inserted, updated = upsert_by_key(
            sess, DimPolicyEvent, records, ["event_date", "title"]
        )
        return inserted + updated

    if session:
        return _load(session)
    with get_session() as sess:
        return _load(sess)
