"""SQLAlchemy model for neighbourhood community profile fact table."""

from sqlalchemy import Index, Integer, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .dimensions import RAW_TORONTO_SCHEMA


class FactNeighbourhoodProfile(Base):
    """Community profile statistics by neighbourhood, category, and subcategory.

    Grain: One row per (neighbourhood_id, census_year, category, subcategory, level).
    count is NULL when Statistics Canada suppresses small population cells.
    level is used only for place_of_birth categories to distinguish continent
    from country rows.
    category_total is the section header value (total for the category) used as
    a denominator for percentage calculations — fixes the denominator bug.
    indent_level is the hierarchy depth from leading whitespace (0 = top level).
    """

    __tablename__ = "fact_neighbourhood_profile"
    __table_args__ = (
        UniqueConstraint(
            "neighbourhood_id",
            "census_year",
            "category",
            "subcategory",
            "level",
            "indent_level",
            name="uq_fact_profile_natural_key",
        ),
        Index(
            "ix_fact_profile_nbhd_year_cat",
            "neighbourhood_id",
            "census_year",
            "category",
        ),
        Index("ix_fact_profile_cat_subcat", "category", "subcategory"),
        Index(
            "ix_fact_profile_indent",
            "neighbourhood_id",
            "category",
            "indent_level",
        ),
        {"schema": RAW_TORONTO_SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    neighbourhood_id: Mapped[int] = mapped_column(Integer, nullable=False)
    census_year: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    subcategory: Mapped[str] = mapped_column(String(100), nullable=False)
    count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    level: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    category_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    indent_level: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
