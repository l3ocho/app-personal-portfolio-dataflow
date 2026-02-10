"""GeoJSON parser for geographic boundary files.

This module provides parsers for loading geographic boundary files
(GeoJSON format) and converting them to Pydantic schemas for database
loading or direct use in Plotly choropleth maps.
"""

import json
from pathlib import Path
from typing import Any

from pyproj import Transformer
from shapely.geometry import mapping, shape
from shapely.ops import transform

from portfolio_app.toronto.schemas import CMHCZone, Neighbourhood

# Transformer for reprojecting from Web Mercator to WGS84
_TRANSFORMER_3857_TO_4326 = Transformer.from_crs(
    "EPSG:3857", "EPSG:4326", always_xy=True
)


def load_geojson(path: Path) -> dict[str, Any]:
    """Load a GeoJSON file and return as dictionary.

    Args:
        path: Path to the GeoJSON file.

    Returns:
        GeoJSON as dictionary (FeatureCollection).

    Raises:
        FileNotFoundError: If file does not exist.
        ValueError: If file is not valid GeoJSON.
    """
    if not path.exists():
        raise FileNotFoundError(f"GeoJSON file not found: {path}")

    if path.suffix.lower() not in (".geojson", ".json"):
        raise ValueError(f"Expected GeoJSON file, got: {path.suffix}")

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if data.get("type") != "FeatureCollection":
        raise ValueError("GeoJSON must be a FeatureCollection")

    return dict(data)


def geometry_to_wkt(geometry: dict[str, Any]) -> str:
    """Convert GeoJSON geometry to WKT string.

    Args:
        geometry: GeoJSON geometry dictionary.

    Returns:
        WKT representation of the geometry.
    """
    return str(shape(geometry).wkt)


def reproject_geometry(
    geometry: dict[str, Any], source_crs: str = "EPSG:3857"
) -> dict[str, Any]:
    """Reproject a GeoJSON geometry to WGS84 (EPSG:4326).

    Args:
        geometry: GeoJSON geometry dictionary.
        source_crs: Source CRS (default EPSG:3857 Web Mercator).

    Returns:
        GeoJSON geometry in WGS84 coordinates.
    """
    if source_crs == "EPSG:3857":
        transformer = _TRANSFORMER_3857_TO_4326
    else:
        transformer = Transformer.from_crs(source_crs, "EPSG:4326", always_xy=True)

    geom = shape(geometry)
    reprojected = transform(transformer.transform, geom)
    return dict(mapping(reprojected))


class CMHCZoneParser:
    """Parser for CMHC zone boundary GeoJSON files.

    CMHC zone boundaries are extracted from the R `cmhc` package using
    `get_cmhc_geography(geography_type="ZONE", cma="Toronto")`.

    Expected GeoJSON properties:
        - zone_code or Zone_Code: Zone identifier
        - zone_name or Zone_Name: Zone name
    """

    # Property name mappings for different GeoJSON formats
    CODE_PROPERTIES = ["zone_code", "Zone_Code", "ZONE_CODE", "zonecode", "code"]
    NAME_PROPERTIES = [
        "zone_name",
        "Zone_Name",
        "ZONE_NAME",
        "ZONE_NAME_EN",
        "NAME_EN",
        "zonename",
        "name",
        "NAME",
    ]

    def __init__(self, geojson_path: Path) -> None:
        """Initialize parser with path to GeoJSON file.

        Args:
            geojson_path: Path to the CMHC zones GeoJSON file.
        """
        self.geojson_path = geojson_path
        self._geojson: dict[str, Any] | None = None

    @property
    def geojson(self) -> dict[str, Any]:
        """Lazy-load and return raw GeoJSON data."""
        if self._geojson is None:
            self._geojson = load_geojson(self.geojson_path)
        return self._geojson

    def _find_property(
        self, properties: dict[str, Any], candidates: list[str]
    ) -> str | None:
        """Find a property value by checking multiple candidate names."""
        for name in candidates:
            if name in properties and properties[name] is not None:
                return str(properties[name])
        return None

    def parse(self) -> list[CMHCZone]:
        """Parse GeoJSON and return list of CMHCZone schemas.

        Automatically reprojects from EPSG:3857 to EPSG:4326 if needed.

        Returns:
            List of validated CMHCZone objects.

        Raises:
            ValueError: If required properties are missing.
        """
        needs_reproject = self._needs_reprojection()
        zones = []
        for feature in self.geojson.get("features", []):
            props = feature.get("properties", {})
            geom = feature.get("geometry")

            zone_code = self._find_property(props, self.CODE_PROPERTIES)
            zone_name = self._find_property(props, self.NAME_PROPERTIES)

            if not zone_code:
                raise ValueError(
                    f"Zone code not found in properties: {list(props.keys())}"
                )
            if not zone_name:
                zone_name = zone_code  # Fallback to code if name missing

            if geom and needs_reproject:
                geom = reproject_geometry(geom)

            geometry_wkt = geometry_to_wkt(geom) if geom else None

            zones.append(
                CMHCZone(
                    zone_code=zone_code,
                    zone_name=zone_name,
                    geometry_wkt=geometry_wkt,
                )
            )

        return zones

    def _needs_reprojection(self) -> bool:
        """Check if GeoJSON needs reprojection to WGS84."""
        crs = self.geojson.get("crs", {})
        crs_name = crs.get("properties", {}).get("name", "")
        # EPSG:3857 or Web Mercator needs reprojection
        return "3857" in crs_name or "900913" in crs_name

    def get_geojson_for_choropleth(
        self, key_property: str = "zone_code"
    ) -> dict[str, Any]:
        """Get GeoJSON formatted for Plotly choropleth maps.

        Ensures the feature properties include a standardized key for
        joining with data. Automatically reprojects from EPSG:3857 to
        WGS84 if needed.

        Args:
            key_property: Property name to use as feature identifier.

        Returns:
            GeoJSON FeatureCollection with standardized properties in WGS84.
        """
        needs_reproject = self._needs_reprojection()
        features = []

        for feature in self.geojson.get("features", []):
            props = feature.get("properties", {})
            new_props = dict(props)

            # Ensure standardized property names exist
            zone_code = self._find_property(props, self.CODE_PROPERTIES)
            zone_name = self._find_property(props, self.NAME_PROPERTIES)

            new_props["zone_code"] = zone_code
            new_props["zone_name"] = zone_name or zone_code

            # Reproject geometry if needed
            geometry = feature.get("geometry")
            if needs_reproject and geometry:
                geometry = reproject_geometry(geometry)

            features.append(
                {
                    "type": "Feature",
                    "properties": new_props,
                    "geometry": geometry,
                }
            )

        return {"type": "FeatureCollection", "features": features}


class NeighbourhoodParser:
    """Parser for City of Toronto neighbourhood boundary GeoJSON files.

    Neighbourhood boundaries are from the City of Toronto Open Data portal.

    Expected GeoJSON properties:
        - neighbourhood_id or AREA_ID: Neighbourhood ID (1-158)
        - name or AREA_NAME: Neighbourhood name
    """

    ID_PROPERTIES = [
        "neighbourhood_id",
        "AREA_SHORT_CODE",  # City of Toronto 158 neighbourhoods
        "AREA_LONG_CODE",
        "AREA_ID",
        "area_id",
        "id",
        "ID",
        "HOOD_ID",
    ]
    NAME_PROPERTIES = [
        "AREA_NAME",  # City of Toronto 158 neighbourhoods
        "name",
        "NAME",
        "area_name",
        "neighbourhood_name",
    ]

    def __init__(self, geojson_path: Path) -> None:
        """Initialize parser with path to GeoJSON file."""
        self.geojson_path = geojson_path
        self._geojson: dict[str, Any] | None = None

    @property
    def geojson(self) -> dict[str, Any]:
        """Lazy-load and return raw GeoJSON data."""
        if self._geojson is None:
            self._geojson = load_geojson(self.geojson_path)
        return self._geojson

    def _find_property(
        self, properties: dict[str, Any], candidates: list[str]
    ) -> str | None:
        """Find a property value by checking multiple candidate names."""
        for name in candidates:
            if name in properties and properties[name] is not None:
                return str(properties[name])
        return None

    def parse(self) -> list[Neighbourhood]:
        """Parse GeoJSON and return list of Neighbourhood schemas.

        Note: This parser only extracts ID, name, and geometry.
        Census enrichment data (population, income, etc.) should be
        loaded separately and merged.
        """
        neighbourhoods = []
        for feature in self.geojson.get("features", []):
            props = feature.get("properties", {})
            geom = feature.get("geometry")

            neighbourhood_id_str = self._find_property(props, self.ID_PROPERTIES)
            name = self._find_property(props, self.NAME_PROPERTIES)

            if not neighbourhood_id_str:
                raise ValueError(
                    f"Neighbourhood ID not found in properties: {list(props.keys())}"
                )

            neighbourhood_id = int(neighbourhood_id_str)
            if not name:
                name = f"Neighbourhood {neighbourhood_id}"

            geometry_wkt = geometry_to_wkt(geom) if geom else None

            neighbourhoods.append(
                Neighbourhood(
                    neighbourhood_id=neighbourhood_id,
                    name=name,
                    geometry_wkt=geometry_wkt,
                )
            )

        return neighbourhoods

    def get_geojson_for_choropleth(
        self, key_property: str = "neighbourhood_id"
    ) -> dict[str, Any]:
        """Get GeoJSON formatted for Plotly choropleth maps."""
        features = []
        for feature in self.geojson.get("features", []):
            props = feature.get("properties", {})
            new_props = dict(props)

            neighbourhood_id = self._find_property(props, self.ID_PROPERTIES)
            name = self._find_property(props, self.NAME_PROPERTIES)

            new_props["neighbourhood_id"] = (
                int(neighbourhood_id) if neighbourhood_id else None
            )
            new_props["name"] = name

            features.append(
                {
                    "type": "Feature",
                    "properties": new_props,
                    "geometry": feature.get("geometry"),
                }
            )

        return {"type": "FeatureCollection", "features": features}
