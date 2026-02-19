"""SQLAlchemy model for neighbourhood community profile fact table."""

from sqlalchemy import Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .dimensions import RAW_TORONTO_SCHEMA


class FactNeighbourhoodProfile(Base):
    """Community profile statistics by neighbourhood, category, and subcategory.

    Grain: One row per (neighbourhood_id, census_year, category, subcategory, level).
    count is NULL when Statistics Canada suppresses small population cells.
    level is used only for place_of_birth categories to distinguish continent
    from country rows.
    """

    __tablename__ = "fact_neighbourhood_profile"
    __table_args__ = (
        UniqueConstraint(
            "neighbourhood_id",
            "census_year",
            "category",
            "subcategory",
            "level",
            name="uq_fact_profile_natural_key",
        ),
        Index(
            "ix_fact_profile_nbhd_year_cat",
            "neighbourhood_id",
            "census_year",
            "category",
        ),
        Index("ix_fact_profile_cat_subcat", "category", "subcategory"),
        {"schema": RAW_TORONTO_SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    neighbourhood_id: Mapped[int] = mapped_column(Integer, nullable=False)
    census_year: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    subcategory: Mapped[str] = mapped_column(String(100), nullable=False)
    count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    level: Mapped[str] = mapped_column(String(20), nullable=False, default="")
