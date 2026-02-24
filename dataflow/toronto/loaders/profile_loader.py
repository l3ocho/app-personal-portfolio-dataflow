"""Loader for neighbourhood community profile data to fact_neighbourhood_profile table."""

from sqlalchemy.orm import Session

from dataflow.toronto.models.profile import FactNeighbourhoodProfile
from dataflow.toronto.schemas.profile import ProfileRecord

from .base import get_session


def load_profile_data(
    records: list[ProfileRecord],
    session: Session | None = None,
) -> int:
    """Load profile records to fact_neighbourhood_profile table.

    Uses a full delete-then-insert strategy per census year, which is safe since
    census data is static and avoids NULL uniqueness issues with the level column.

    Args:
        records: List of validated ProfileRecord schemas.
        session: Optional existing session. If None, a new session is created.

    Returns:
        Number of records loaded (inserted).
    """

    def _load(sess: Session) -> int:
        if not records:
            return 0

        # Collect unique years in the batch
        years = {r.census_year for r in records}

        # Delete existing records for these census years to ensure clean replace
        for year in years:
            sess.query(FactNeighbourhoodProfile).filter_by(census_year=year).delete()
        sess.flush()

        # Convert Pydantic schemas to ORM models and bulk insert
        models = [
            FactNeighbourhoodProfile(
                neighbourhood_id=r.neighbourhood_id,
                census_year=r.census_year,
                category=r.category,
                subcategory=r.subcategory,
                count=r.count,
                level=r.level,
                category_total=r.category_total,
                indent_level=r.indent_level,
            )
            for r in records
        ]
        sess.add_all(models)
        sess.flush()
        return len(models)

    if session:
        return _load(session)
    with get_session() as sess:
        return _load(sess)
