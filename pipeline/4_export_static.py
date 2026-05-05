"""Export the matrix and grid as static files for the web app.

Outputs (under web/public/data/):
  hexes.geojson            polygons keyed by h3 id, used for map layer
  origins/{h3}.json        per-origin destination map: {"d": {h3: minutes}}
  origins/index.json       list of all origin ids (for sanity / lookups)

The per-origin JSON files are small (a few KB gzipped) and lazy-loaded on click.
"""
from __future__ import annotations

import gzip
import json
import shutil
import sys

import h3
import pandas as pd

import config


def main() -> int:
    grid = pd.read_parquet(config.INTERMEDIATE / "grid.parquet")
    matrix_path = config.INTERMEDIATE / "matrix.parquet"
    if not matrix_path.exists():
        print(f"Missing {matrix_path}. Run 3_compute_matrix.py first.", file=sys.stderr)
        return 1
    matrix = pd.read_parquet(matrix_path)

    config.PUBLIC.mkdir(parents=True, exist_ok=True)
    origins_dir = config.PUBLIC / "origins"
    origins_dir.mkdir(exist_ok=True)

    # 1) Hex polygon GeoJSON.
    features = []
    for row in grid.itertuples(index=False):
        boundary = h3.cell_to_boundary(row.h3)
        ring = [[lon, lat] for (lat, lon) in boundary]
        ring.append(ring[0])
        features.append({
            "type": "Feature",
            "id": row.h3,
            "properties": {"h3": row.h3},
            "geometry": {"type": "Polygon", "coordinates": [ring]},
        })
    fc = {"type": "FeatureCollection", "features": features}
    (config.PUBLIC / "hexes.geojson").write_text(
        json.dumps(fc, separators=(",", ":"))
    )
    print(f"Wrote hexes.geojson ({len(features):,} features)")

    # 2) Per-origin JSON files.
    grouped = matrix.groupby("from_id")
    written = 0
    for origin, group in grouped:
        # Drop pairs above the cap and self-pairs (always 0 anyway).
        d = {
            row.to_id: int(row.travel_time)
            for row in group.itertuples(index=False)
            if row.travel_time <= config.MAX_TRAVEL_TIME_MIN
        }
        if not d:
            continue
        payload = {"o": origin, "d": d}
        # Write both raw and gzipped; serve gzipped if your host supports
        # Content-Encoding negotiation, otherwise the raw .json works.
        path = origins_dir / f"{origin}.json"
        path.write_text(json.dumps(payload, separators=(",", ":")))
        with gzip.open(path.with_suffix(".json.gz"), "wt") as f:
            json.dump(payload, f, separators=(",", ":"))
        written += 1

    print(f"Wrote {written:,} per-origin files to {origins_dir}")

    # 3) Index of available origins.
    index = sorted(grouped.groups.keys())
    (origins_dir / "index.json").write_text(json.dumps(index))
    print(f"Wrote origins/index.json ({len(index):,} entries)")

    # 4) Boundary file — copy across so the web app can render the city outline.
    boundary_src = config.RAW / "sheffield-boundary.geojson"
    if boundary_src.exists():
        shutil.copy2(boundary_src, config.PUBLIC / "boundary.geojson")
        print("Wrote boundary.geojson")

    # 5) Compute area-per-hex at this resolution + total city area for stats.
    sample_hex = grid["h3"].iloc[0]
    hex_area_km2 = h3.cell_area(sample_hex, unit="km^2")
    city_area_km2 = round(len(grid) * hex_area_km2, 1)

    # 6) Tiny manifest the web app reads at startup.
    manifest = {
        "departure_date": config.DEPARTURE_DATE,
        "departure_time": config.DEPARTURE_TIME,
        "departure_window_min": config.DEPARTURE_WINDOW_MIN,
        "max_travel_time_min": config.MAX_TRAVEL_TIME_MIN,
        "h3_resolution": config.H3_RESOLUTION,
        "bbox": config.BBOX,
        "origin_count": len(index),
        "hex_area_km2": round(hex_area_km2, 4),
        "city_area_km2": city_area_km2,
    }
    (config.PUBLIC / "manifest.json").write_text(
        json.dumps(manifest, indent=2)
    )
    print(f"Wrote manifest.json (hex={hex_area_km2:.4f} km^2, total~{city_area_km2} km^2)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
