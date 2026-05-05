"""Extract bus + tram route shapes from the GTFS feed.

For each route serving Sheffield (any point within the LAD bbox), pick the
single most-used shape and emit it as a LineString. The result is shown on
the map as the underlay instead of road geometry — busy bus corridors
self-emphasise via alpha stacking when multiple route lines overlap.

Output:
  web/public/data/transit-shapes.geojson  features tagged with route_type
                                           (0 = tram, 3 = bus) and name.
"""
from __future__ import annotations

import json
import sys
import zipfile

import pandas as pd

import config

# GTFS route_type values we care about.
TRAM = 0
BUS = 3
KEEP_TYPES = {TRAM, BUS}


def main() -> int:
    gtfs = config.RAW / "yorkshire-gtfs.zip"
    if not gtfs.exists():
        print(f"Missing {gtfs}. Run 1_download_data.py first.", file=sys.stderr)
        return 1

    print(f"Reading {gtfs.name}…")
    with zipfile.ZipFile(gtfs) as z:
        with z.open("routes.txt") as f:
            routes = pd.read_csv(f, dtype={"route_id": str})
        with z.open("trips.txt") as f:
            trips = pd.read_csv(f, dtype={"route_id": str, "shape_id": str})
        with z.open("shapes.txt") as f:
            shapes = pd.read_csv(f, dtype={"shape_id": str})
    print(f"  routes={len(routes):,}  trips={len(trips):,}  shapes pts={len(shapes):,}")

    routes = routes[routes["route_type"].isin(KEEP_TYPES)].copy()
    print(f"  bus + tram routes: {len(routes):,}")

    # For each route, the most-used shape (the canonical one).
    counts = (
        trips.dropna(subset=["shape_id"])
        .groupby(["route_id", "shape_id"], as_index=False)
        .size()
        .rename(columns={"size": "trip_count"})
    )
    best = counts.sort_values(["route_id", "trip_count"], ascending=[True, False]) \
                 .drop_duplicates("route_id")
    print(f"  routes with shapes: {len(best):,}")

    # Sort shape points once for fast lookup.
    shapes = shapes.sort_values(["shape_id", "shape_pt_sequence"])
    shapes_by_id = {sid: g for sid, g in shapes.groupby("shape_id")}

    # Sheffield bbox (slightly padded to keep routes that just clip the edge).
    bbox = config.BBOX
    pad = 0.03
    s, n = bbox["min_lat"] - pad, bbox["max_lat"] + pad
    w, e = bbox["min_lon"] - pad, bbox["max_lon"] + pad

    features = []
    skipped_outside = 0
    skipped_empty = 0
    for _, row in routes.iterrows():
        match = best[best["route_id"] == row["route_id"]]
        if match.empty:
            continue
        sid = match["shape_id"].iloc[0]
        pts = shapes_by_id.get(sid)
        if pts is None or len(pts) < 2:
            skipped_empty += 1
            continue

        # Keep route only if any point is inside Sheffield bbox.
        lats = pts["shape_pt_lat"].to_numpy()
        lons = pts["shape_pt_lon"].to_numpy()
        in_bbox = (lats >= s) & (lats <= n) & (lons >= w) & (lons <= e)
        if not in_bbox.any():
            skipped_outside += 1
            continue

        coords = [[float(lon), float(lat)] for lat, lon in zip(lats, lons)]

        # GTFS route_color may be present (hex without #). Use it for trams so
        # Supertram lines wear something close to their real livery.
        rc = row.get("route_color")
        if isinstance(rc, str) and rc and rc.lower() not in ("nan",):
            color = "#" + rc.lstrip("#").lower()
        else:
            color = ""

        features.append({
            "type": "Feature",
            "properties": {
                "route_id": str(row["route_id"]),
                "route_type": int(row["route_type"]),
                "name": str(row.get("route_short_name", "") or "").strip(),
                "long_name": str(row.get("route_long_name", "") or "").strip(),
                "color": color,
            },
            "geometry": {"type": "LineString", "coordinates": coords},
        })

    print(f"  kept: {len(features):,}  skipped outside bbox: {skipped_outside:,}  skipped empty: {skipped_empty:,}")
    by_type = {}
    for f in features:
        by_type[f["properties"]["route_type"]] = by_type.get(f["properties"]["route_type"], 0) + 1
    print(f"  by type: {by_type}")

    config.PUBLIC.mkdir(parents=True, exist_ok=True)
    out = config.PUBLIC / "transit-shapes.geojson"
    fc = {"type": "FeatureCollection", "features": features}
    out.write_text(json.dumps(fc, separators=(",", ":")))
    print(f"Wrote {out} ({out.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
