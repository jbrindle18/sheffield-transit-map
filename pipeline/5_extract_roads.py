"""Fetch major roads inside Sheffield via the Overpass API.

We pull motorway/trunk/primary/secondary/tertiary highways inside the LAD
boundary's bbox and write a single GeoJSON to web/public/data/roads.geojson.

Used as a thin overlay above the heatmap so streets stay legible.
"""
from __future__ import annotations

import json
import sys
import urllib.request

import config

OVERPASS = "https://overpass-api.de/api/interpreter"
QUERY_TEMPLATE = """
[out:json][timeout:90];
(
  way["highway"~"^(motorway|motorway_link|trunk|trunk_link|primary|primary_link|secondary|secondary_link|tertiary|tertiary_link)$"]
    ({s},{w},{n},{e});
);
out geom;
"""


def main() -> int:
    boundary_path = config.RAW / "sheffield-boundary.geojson"
    if not boundary_path.exists():
        print(f"Missing {boundary_path}. Run 0_get_boundary.py first.", file=sys.stderr)
        return 1
    boundary = json.loads(boundary_path.read_text())

    # Use the boundary's overall bbox; we'll rely on the city-mask in the
    # frontend to dim roads outside the boundary.
    bounds = [float("inf"), float("inf"), float("-inf"), float("-inf")]  # [minLon,minLat,maxLon,maxLat]
    for f in boundary["features"]:
        g = f["geometry"]
        coords_list = g["coordinates"] if g["type"] == "Polygon" else [c[0] for c in g["coordinates"]]
        for ring in coords_list:
            for lon, lat in ring:
                bounds[0] = min(bounds[0], lon)
                bounds[1] = min(bounds[1], lat)
                bounds[2] = max(bounds[2], lon)
                bounds[3] = max(bounds[3], lat)

    query = QUERY_TEMPLATE.format(
        w=bounds[0], s=bounds[1], e=bounds[2], n=bounds[3],
    ).strip()
    print(f"Querying Overpass for major roads in {bounds}…")

    import urllib.parse
    req = urllib.request.Request(
        OVERPASS,
        data=urllib.parse.urlencode({"data": query}).encode(),
        method="POST",
        headers={"User-Agent": "sheffield-transit-map/0.1 (research)"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        elements = json.loads(r.read())["elements"]
    print(f"  {len(elements):,} ways returned")

    features = []
    for el in elements:
        if "geometry" not in el or len(el.get("geometry", [])) < 2:
            continue
        coords = [[p["lon"], p["lat"]] for p in el["geometry"]]
        tags = el.get("tags", {})
        features.append({
            "type": "Feature",
            "properties": {
                "highway": tags.get("highway", ""),
                "name": tags.get("name", ""),
                "ref": tags.get("ref", ""),
            },
            "geometry": {"type": "LineString", "coordinates": coords},
        })

    fc = {"type": "FeatureCollection", "features": features}
    config.PUBLIC.mkdir(parents=True, exist_ok=True)
    out = config.PUBLIC / "roads.geojson"
    out.write_text(json.dumps(fc, separators=(",", ":")))
    size_kb = out.stat().st_size / 1024
    print(f"Wrote {out} ({len(features):,} ways, {size_kb:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
