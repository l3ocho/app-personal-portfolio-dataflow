"""Pydantic schema for neighbourhood community profile data."""

from pydantic import BaseModel, Field, field_validator

VALID_CATEGORIES: frozenset[str] = frozenset(
    {
        # Existing (10)
        "immigration_status",
        "place_of_birth",
        "place_of_birth_recent",
        "citizenship",
        "generation_status",
        "admission_category",
        "visible_minority",
        "ethnic_origin",
        "mother_tongue",
        "official_language",
        # New Sprint 12 categories (18)
        "language_at_home",
        "indigenous_identity",
        "religion",
        "education_level",
        "field_of_study",
        "occupation",
        "industry_sector",
        "income_bracket",
        "income_source",
        "household_type",
        "family_type",
        "commute_mode",
        "commute_duration",
        "commute_destination",
        "housing_suitability",
        "dwelling_type",
        "bedrooms",
        "construction_period",
    }
)


class ProfileRecord(BaseModel):
    """Community profile data for a neighbourhood subcategory.

    Grain: one record per (neighbourhood_id, census_year, category,
    subcategory, level).

    count is None when Statistics Canada suppressed the value (small population).
    level is only populated for place_of_birth categories to distinguish
    continent-level from country-level rows.
    category_total is the section header row value (total for the category),
    used as the denominator for percentage calculations.
    indent_level is the hierarchy depth derived from leading whitespace in the
    original XLSX Characteristic column (0 = no indent, 2 = two leading spaces).
    """

    neighbourhood_id: int = Field(ge=1, le=200)
    census_year: int = Field(ge=2016, le=2030)
    category: str = Field(max_length=50)
    subcategory: str = Field(max_length=100)
    count: int | None = Field(default=None, ge=0)
    level: str = Field(default="", max_length=20)  # '' | 'continent' | 'country'
    category_total: int | None = Field(default=None, ge=0)
    indent_level: int = Field(default=0, ge=0, le=20)

    model_config = {"str_strip_whitespace": True}

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in VALID_CATEGORIES:
            raise ValueError(
                f"Invalid category '{v}'. Must be one of: {sorted(VALID_CATEGORIES)}"
            )
        return v

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        if v not in ("", "continent", "country"):
            raise ValueError(
                f"Invalid level '{v}'. Must be '', 'continent', or 'country'."
            )
        return v
