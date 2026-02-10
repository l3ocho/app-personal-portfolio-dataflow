"""Loader for crime data to fact_crime table."""

from sqlalchemy.orm import Session

from dataflow.toronto.models import FactCrime
from dataflow.toronto.schemas import CrimeRecord

from .base import get_session, upsert_by_key


def load_crime_data(
    records: list[CrimeRecord],
    session: Session | None = None,
) -> int:
    """Load crime records to fact_crime table.

    Args:
        records: List of validated CrimeRecord schemas.
        session: Optional existing session.

    Returns:
        Number of records loaded (inserted + updated).
    """

    def _load(sess: Session) -> int:
        models = []
        for r in records:
            model = FactCrime(
                neighbourhood_id=r.neighbourhood_id,
                year=r.year,
                crime_type=r.crime_type.value,
                count=r.count,
                rate_per_100k=float(r.rate_per_100k) if r.rate_per_100k else None,
            )
            models.append(model)

        inserted, updated = upsert_by_key(
            sess, FactCrime, models, ["neighbourhood_id", "year", "crime_type"]
        )
        return inserted + updated

    if session:
        return _load(session)
    with get_session() as sess:
        return _load(sess)
