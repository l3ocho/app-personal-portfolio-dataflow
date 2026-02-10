"""Loader for census data to fact_census table."""

from sqlalchemy.orm import Session

from dataflow.toronto.models import FactCensus
from dataflow.toronto.schemas import CensusRecord

from .base import get_session, upsert_by_key


def load_census_data(
    records: list[CensusRecord],
    session: Session | None = None,
) -> int:
    """Load census records to fact_census table.

    Args:
        records: List of validated CensusRecord schemas.
        session: Optional existing session.

    Returns:
        Number of records loaded (inserted + updated).
    """

    def _load(sess: Session) -> int:
        models = []
        for r in records:
            model = FactCensus(
                neighbourhood_id=r.neighbourhood_id,
                census_year=r.census_year,
                population=r.population,
                population_density=float(r.population_density)
                if r.population_density
                else None,
                median_household_income=float(r.median_household_income)
                if r.median_household_income
                else None,
                average_household_income=float(r.average_household_income)
                if r.average_household_income
                else None,
                unemployment_rate=float(r.unemployment_rate)
                if r.unemployment_rate
                else None,
                pct_bachelors_or_higher=float(r.pct_bachelors_or_higher)
                if r.pct_bachelors_or_higher
                else None,
                pct_owner_occupied=float(r.pct_owner_occupied)
                if r.pct_owner_occupied
                else None,
                pct_renter_occupied=float(r.pct_renter_occupied)
                if r.pct_renter_occupied
                else None,
                median_age=float(r.median_age) if r.median_age else None,
                average_dwelling_value=float(r.average_dwelling_value)
                if r.average_dwelling_value
                else None,
            )
            models.append(model)

        inserted, updated = upsert_by_key(
            sess, FactCensus, models, ["neighbourhood_id", "census_year"]
        )
        return inserted + updated

    if session:
        return _load(session)
    with get_session() as sess:
        return _load(sess)
