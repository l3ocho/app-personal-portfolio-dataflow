"""Loader for amenities data to fact_amenities table."""

from collections import Counter

from sqlalchemy.orm import Session

from dataflow.toronto.models import FactAmenities
from dataflow.toronto.schemas import AmenityCount, AmenityRecord

from .base import get_session, upsert_by_key


def load_amenities(
    records: list[AmenityRecord],
    year: int,
    session: Session | None = None,
) -> int:
    """Load amenity records to fact_amenities table.

    Aggregates individual amenity records into counts by neighbourhood
    and amenity type before loading.

    Args:
        records: List of validated AmenityRecord schemas.
        year: Year to associate with the amenity counts.
        session: Optional existing session.

    Returns:
        Number of records loaded (inserted + updated).
    """
    # Aggregate records by neighbourhood and amenity type
    counts: Counter[tuple[int, str]] = Counter()
    for r in records:
        key = (r.neighbourhood_id, r.amenity_type.value)
        counts[key] += 1

    # Convert to AmenityCount schemas then to models
    def _load(sess: Session) -> int:
        models = []
        for (neighbourhood_id, amenity_type), count in counts.items():
            model = FactAmenities(
                neighbourhood_id=neighbourhood_id,
                amenity_type=amenity_type,
                count=count,
                year=year,
            )
            models.append(model)

        inserted, updated = upsert_by_key(
            sess, FactAmenities, models, ["neighbourhood_id", "amenity_type", "year"]
        )
        return inserted + updated

    if session:
        return _load(session)
    with get_session() as sess:
        return _load(sess)


def load_amenity_counts(
    records: list[AmenityCount],
    session: Session | None = None,
) -> int:
    """Load pre-aggregated amenity counts to fact_amenities table.

    Args:
        records: List of validated AmenityCount schemas.
        session: Optional existing session.

    Returns:
        Number of records loaded (inserted + updated).
    """

    def _load(sess: Session) -> int:
        models = []
        for r in records:
            model = FactAmenities(
                neighbourhood_id=r.neighbourhood_id,
                amenity_type=r.amenity_type.value,
                count=r.count,
                year=r.year,
            )
            models.append(model)

        inserted, updated = upsert_by_key(
            sess, FactAmenities, models, ["neighbourhood_id", "amenity_type", "year"]
        )
        return inserted + updated

    if session:
        return _load(session)
    with get_session() as sess:
        return _load(sess)
