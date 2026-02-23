"""Loader for census extended wide-format scalar indicators to fact_census_extended table."""

from sqlalchemy.orm import Session

from dataflow.toronto.models.census_extended import FactCensusExtended
from dataflow.toronto.schemas.census_extended import CensusExtendedRecord

from .base import get_session, upsert_by_key


def load_census_extended_data(
    records: list[CensusExtendedRecord],
    session: Session | None = None,
) -> int:
    """Load census extended records to fact_census_extended table.

    Uses upsert-by-key on (neighbourhood_id, census_year), so re-runs are
    idempotent — existing rows are updated with fresh values.

    Args:
        records: List of validated CensusExtendedRecord schemas.
        session: Optional existing session. If None, a new session is created.

    Returns:
        Number of records loaded (inserted + updated).
    """

    def _load(sess: Session) -> int:
        if not records:
            return 0

        models = [
            FactCensusExtended(
                neighbourhood_id=r.neighbourhood_id,
                census_year=r.census_year,
                # Population
                population=r.population,
                pop_0_to_14=r.pop_0_to_14,
                pop_15_to_24=r.pop_15_to_24,
                pop_25_to_64=r.pop_25_to_64,
                pop_65_plus=r.pop_65_plus,
                # Households
                total_private_dwellings=r.total_private_dwellings,
                occupied_private_dwellings=r.occupied_private_dwellings,
                avg_household_size=r.avg_household_size,
                avg_household_income_after_tax=r.avg_household_income_after_tax,
                # Housing
                pct_owner_occupied=r.pct_owner_occupied,
                pct_renter_occupied=r.pct_renter_occupied,
                pct_suitable_housing=r.pct_suitable_housing,
                avg_shelter_cost_owner=r.avg_shelter_cost_owner,
                avg_shelter_cost_renter=r.avg_shelter_cost_renter,
                pct_shelter_cost_30pct=r.pct_shelter_cost_30pct,
                # Education
                pct_no_certificate=r.pct_no_certificate,
                pct_high_school=r.pct_high_school,
                pct_college=r.pct_college,
                pct_university=r.pct_university,
                pct_postsecondary=r.pct_postsecondary,
                # Labour
                participation_rate=r.participation_rate,
                employment_rate=r.employment_rate,
                unemployment_rate=r.unemployment_rate,
                pct_employed_full_time=r.pct_employed_full_time,
                # Income
                median_after_tax_income=r.median_after_tax_income,
                median_employment_income=r.median_employment_income,
                lico_at_rate=r.lico_at_rate,
                market_basket_measure_rate=r.market_basket_measure_rate,
                # Diversity
                pct_immigrants=r.pct_immigrants,
                pct_recent_immigrants=r.pct_recent_immigrants,
                pct_visible_minority=r.pct_visible_minority,
                pct_indigenous=r.pct_indigenous,
                # Language
                pct_english_only=r.pct_english_only,
                pct_french_only=r.pct_french_only,
                pct_neither_official_lang=r.pct_neither_official_lang,
                pct_bilingual=r.pct_bilingual,
                # Mobility
                pct_non_movers=r.pct_non_movers,
                pct_movers_within_city=r.pct_movers_within_city,
                pct_movers_from_other_city=r.pct_movers_from_other_city,
                # Commuting
                pct_car_commuters=r.pct_car_commuters,
                pct_transit_commuters=r.pct_transit_commuters,
                pct_active_commuters=r.pct_active_commuters,
                pct_work_from_home=r.pct_work_from_home,
                # Additional
                median_age=r.median_age,
                pct_lone_parent_families=r.pct_lone_parent_families,
                avg_number_of_children=r.avg_number_of_children,
                pct_dwellings_in_need_of_repair=r.pct_dwellings_in_need_of_repair,
                pct_unaffordable_housing=r.pct_unaffordable_housing,
                pct_overcrowded_housing=r.pct_overcrowded_housing,
                median_commute_minutes=r.median_commute_minutes,
                pct_management_occupation=r.pct_management_occupation,
                pct_business_finance_admin=r.pct_business_finance_admin,
                pct_service_sector=r.pct_service_sector,
                pct_trades_transport=r.pct_trades_transport,
                population_density=r.population_density,
            )
            for r in records
        ]

        inserted, updated = upsert_by_key(
            sess, FactCensusExtended, models, ["neighbourhood_id", "census_year"]
        )
        return inserted + updated

    if session:
        return _load(session)
    with get_session() as sess:
        return _load(sess)
