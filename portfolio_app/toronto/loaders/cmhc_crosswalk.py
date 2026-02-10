"""Loader for CMHC zone to neighbourhood crosswalk with area weights."""

from sqlalchemy import text
from sqlalchemy.orm import Session

from .base import get_session


def build_cmhc_neighbourhood_crosswalk(
    session: Session | None = None,
) -> int:
    """Calculate area overlap weights between CMHC zones and neighbourhoods.

    Uses PostGIS ST_Intersection and ST_Area functions to compute the
    proportion of each CMHC zone that overlaps with each neighbourhood.
    This enables disaggregation of CMHC zone-level data to neighbourhood level.

    The function is idempotent - it clears existing crosswalk data before
    rebuilding.

    Args:
        session: Optional existing session.

    Returns:
        Number of bridge records created.

    Note:
        Requires both dim_cmhc_zone and dim_neighbourhood tables to have
        geometry columns populated with valid PostGIS geometries.
    """

    def _build(sess: Session) -> int:
        # Clear existing crosswalk data
        sess.execute(text("DELETE FROM raw_toronto.bridge_cmhc_neighbourhood"))

        # Calculate overlap weights using PostGIS
        # Weight = area of intersection / total area of CMHC zone
        crosswalk_query = text(
            """
            INSERT INTO raw_toronto.bridge_cmhc_neighbourhood
                (cmhc_zone_code, neighbourhood_id, weight)
            SELECT
                z.zone_code,
                n.neighbourhood_id,
                CASE
                    WHEN ST_Area(z.geometry::geography) > 0
                    THEN
                        ST_Area(
                            ST_Intersection(
                                z.geometry, n.geometry
                            )::geography
                        )
                        / ST_Area(z.geometry::geography)
                    ELSE 0
                END as weight
            FROM raw_toronto.dim_cmhc_zone z
            JOIN raw_toronto.dim_neighbourhood n
                ON ST_Intersects(z.geometry, n.geometry)
            WHERE
                z.geometry IS NOT NULL
                AND n.geometry IS NOT NULL
                AND ST_Area(ST_Intersection(z.geometry, n.geometry)::geography) > 0
        """
        )

        sess.execute(crosswalk_query)

        # Count records created
        count_result = sess.execute(
            text("SELECT COUNT(*) FROM raw_toronto.bridge_cmhc_neighbourhood")
        )
        count = count_result.scalar() or 0

        return int(count)

    if session:
        return _build(session)
    with get_session() as sess:
        return _build(sess)


def get_neighbourhood_weights_for_zone(
    zone_code: str,
    session: Session | None = None,
) -> list[tuple[int, float]]:
    """Get neighbourhood weights for a specific CMHC zone.

    Args:
        zone_code: CMHC zone code.
        session: Optional existing session.

    Returns:
        List of (neighbourhood_id, weight) tuples.
    """

    def _get(sess: Session) -> list[tuple[int, float]]:
        result = sess.execute(
            text(
                """
                SELECT neighbourhood_id, weight
                FROM raw_toronto.bridge_cmhc_neighbourhood
                WHERE cmhc_zone_code = :zone_code
                ORDER BY weight DESC
            """
            ),
            {"zone_code": zone_code},
        )
        return [(int(row[0]), float(row[1])) for row in result]

    if session:
        return _get(session)
    with get_session() as sess:
        return _get(sess)


def disaggregate_zone_value(
    zone_code: str,
    value: float,
    session: Session | None = None,
) -> dict[int, float]:
    """Disaggregate a CMHC zone value to neighbourhoods using weights.

    Args:
        zone_code: CMHC zone code.
        value: Value to disaggregate (e.g., average rent).
        session: Optional existing session.

    Returns:
        Dictionary mapping neighbourhood_id to weighted value.

    Note:
        For averages (like rent), the weighted value represents the
        contribution from this zone. To get a neighbourhood's total,
        sum contributions from all overlapping zones.
    """
    weights = get_neighbourhood_weights_for_zone(zone_code, session)
    return {neighbourhood_id: value * weight for neighbourhood_id, weight in weights}
