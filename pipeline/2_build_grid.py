"""Build an H3 hex grid clipped to the Sheffield City Council boundary.

Outputs:
  data/intermediate/grid.parquet    columns: h3, lat, lon
  data/intermediate/grid.geojson    polygons for visual sanity check
"""
from __future__ import annotations

import json
import sys

import h3
import pandas as pd
from shapely.geometry import shape

import config


def load_boundary() -> object:
    path = config.RAW / "sheffield-boundary.geojson"
    if not path.exists():
        print(f"Missing {path}. Run pipeline/0_get_boundary.py first.", file=sys.stderr)
        sys.exit(1)
    fc = json.loads(path.read_text())
    geom = shape(fc["features"][0]["geometry"])
    return geom


def hexes_in_geometry(geom_geojson: dict, resolution: int) -> list[str]:
    """All H3 cells whose centroid falls inside the given geometry."""
    return list(h3.geo_to_cells(geom_geojson, resolution))


def main() -> int:
    config.INTERMEDIATE.mkdir(parents=True, exist_ok=True)

    print("Loading Sheffield boundary…")
    geom = load_boundary()
    print(f"  bounds: {geom.bounds}")

    # h3.geo_to_cells accepts a GeoJSON dict directly.
    geom_geojson = json.loads(json.dumps(geom.__geo_interface__))

    print(f"Generating H3 res-{config.H3_RESOLUTION} cells inside the boundary…")
    cells = hexes_in_geometry(geom_geojson, config.H3_RESOLUTION)
    print(f"  {len(cells):,} cells")

    rows = []
    features = []
    for h in cells:
        lat, lon = h3.cell_to_latlng(h)
        rows.append({"h3": h, "lat": lat, "lon": lon})
        boundary = h3.cell_to_boundary(h)  # [(lat, lon), ...]
        ring = [[lon, lat] for (lat, lon) in boundary]
        ring.append(ring[0])
        features.append({
            "type": "Feature",
            "id": h,
            "properties": {"h3": h},
            "geometry": {"type": "Polygon", "coordinates": [ring]},
        })

    df = pd.DataFrame(rows)
    df.to_parquet(config.INTERMEDIATE / "grid.parquet", index=False)
    print(f"  wrote {config.INTERMEDIATE / 'grid.parquet'}")

    fc = {"type": "FeatureCollection", "features": features}
    (config.INTERMEDIATE / "grid.geojson").write_text(json.dumps(fc))
    print(f"  wrote {config.INTERMEDIATE / 'grid.geojson'}")

    print()
    n2 = len(cells) ** 2
    print(f"  matrix size: {n2:,} pairs (was 624,100 at res 8)")
    print(f"  rough compute estimate vs previous: {n2 / 624100:.1f}x -> {4.1 * n2 / 624100:.1f} min")

    return 0


if __name__ == "__main__":
    sys.exit(main())
