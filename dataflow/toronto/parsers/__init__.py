"""Parsers for Toronto housing data sources."""

from .cmhc import CMHCParser
from .cmhc_excel import CMHCExcelParser, parse_cmhc_excel_directory
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
    "parse_cmhc_excel_directory",
    # GeoJSON parsers
    "CMHCZoneParser",
    "NeighbourhoodParser",
    "load_geojson",
    # API parsers (Phase 3)
    "TorontoOpenDataParser",
    "TorontoPoliceParser",
]
