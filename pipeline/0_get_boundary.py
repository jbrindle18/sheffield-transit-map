"""Fetch the Sheffield City Council boundary from ONS.

Source: ONS Open Geography Portal, Local Authority Districts (UK) BFE.
LAD code for Sheffield: E08000019.

Output:
  data/raw/sheffield-boundary.geojson    polygon in EPSG:4326
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request

import config

# ONS publishes a fresh LAD layer each December. We fetch the most recent that
# returns Sheffield successfully — fall through if any year is missing.
LAD_LAYERS = [
    (
        "2024",
        "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
        "Local_Authority_Districts_December_2024_Boundaries_UK_BFE/FeatureServer/0/query",
        "LAD24CD",
        "LAD24NM",
    ),
    (
        "2023",
        "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
        "Local_Authority_Districts_December_2023_Boundaries_UK_BFE/FeatureServer/0/query",
        "LAD23CD",
        "LAD23NM",
    ),
]
SHEFFIELD_CODE = "E08000019"


def fetch() -> dict:
    last_err: Exception | None = None
    for year, base, code_field, name_field in LAD_LAYERS:
        params = {
            "where": f"{code_field}='{SHEFFIELD_CODE}'",
            "outFields": f"{code_field},{name_field}",
            "outSR": "4326",
            "f": "geojson",
        }
        url = base + "?" + urllib.parse.urlencode(params)
        try:
            print(f"Trying ONS LAD {year}…")
            with urllib.request.urlopen(url, timeout=30) as r:
                data = json.loads(r.read())
            if data.get("features"):
                return data
        except Exception as e:
            last_err = e
            print(f"  failed: {e}")
    raise RuntimeError(f"All ONS LAD layers failed; last error: {last_err}")


def main() -> int:
    config.RAW.mkdir(parents=True, exist_ok=True)
    out = config.RAW / "sheffield-boundary.geojson"
    if out.exists():
        size = out.stat().st_size
        print(f"  exists ({size} bytes), skipping. Delete to force re-fetch.")
        return 0

    data = fetch()
    feature = data["features"][0]
    geom = feature["geometry"]
    print(f"Got {feature['properties']}")
    print(f"Geometry: {geom['type']}")
    if geom["type"] == "MultiPolygon":
        print(f"  {len(geom['coordinates'])} polygon(s)")

    out.write_text(json.dumps(data))
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
