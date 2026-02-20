"""Pydantic schema for neighbourhood community profile data."""

from pydantic import BaseModel, Field, field_validator

VALID_CATEGORIES: frozenset[str] = frozenset({
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
})


class ProfileRecord(BaseModel):
    """Community profile data for a neighbourhood subcategory.

    Grain: one record per (neighbourhood_id, census_year, category,
    subcategory, level).

    count is None when Statistics Canada suppressed the value (small population).
    level is only populated for place_of_birth categories to distinguish
    continent-level from country-level rows.
    """

    neighbourhood_id: int = Field(ge=1, le=200)
    census_year: int = Field(ge=2016, le=2030)
    category: str = Field(max_length=50)
    subcategory: str = Field(max_length=100)
    count: int | None = Field(default=None, ge=0)
    level: str = Field(default="", max_length=20)  # '' | 'continent' | 'country'

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
            raise ValueError(f"Invalid level '{v}'. Must be '', 'continent', or 'country'.")
        return v
