"""Parsers for Toronto housing data sources."""

from .cmhc import CMHCParser
from .cmhc_excel import (
    CMHCExcelParser,
    CMHCExcelRentalRecord,
    parse_cmhc_excel_directory,
    parse_cmhc_excel_rental_directory,
)
from .geo import (
    CMHCZoneParser,
    NeighbourhoodParser,
    load_geojson,
)
from .toronto_open_data import TorontoOpenDataParser
from .toronto_police import TorontoPoliceParser

__all__ = [
    "CMHCParser",
    "CMHCExcelParser",
    "CMHCExcelRentalRecord",
    "parse_cmhc_excel_directory",
    "parse_cmhc_excel_rental_directory",
    # GeoJSON parsers
    "CMHCZoneParser",
    "NeighbourhoodParser",
    "load_geojson",
    # API parsers (Phase 3)
    "TorontoOpenDataParser",
    "TorontoPoliceParser",
]
