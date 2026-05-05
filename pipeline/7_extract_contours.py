"""Extract contour lines for Sheffield from public elevation tiles.

We fetch terrarium-encoded DEM tiles (AWS Open Data), stitch them into a
single elevation array, then run matplotlib's contour generator at
configured intervals. Output is a GeoJSON of LineStrings with `elevation`
property — thin overlay layer on the map.

Sheffield ranges from ~30m (Don valley near Tinsley) to ~540m (Stanage Edge
on the western moors). 50m contour interval gives good detail.
"""
from __future__ import annotations

import io
import json
import math
import sys
import urllib.request

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

import config

ZOOM = 12  # ~38m per pixel at Sheffield's latitude — plenty of detail
TILE_URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
INTERVAL_M = 50  # contour every 50 metres


def lonlat_to_tile(lon: float, lat: float, z: int) -> tuple[int, int]:
    n = 2 ** z
    xt = int((lon + 180) / 360 * n)
    lat_rad = math.radians(lat)
    yt = int((1 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2 * n)
    return xt, yt


def tile_to_lon(x: float, z: int) -> float:
    return x / (2 ** z) * 360 - 180


def tile_to_lat(y: float, z: int) -> float:
    n = math.pi - 2 * math.pi * y / (2 ** z)
    return math.degrees(math.atan(math.sinh(n)))


def fetch_tile(z: int, x: int, y: int) -> np.ndarray:
    url = TILE_URL.format(z=z, x=x, y=y)
    req = urllib.request.Request(url, headers={"User-Agent": "sheffield-transit-map"})
    with urllib.request.urlopen(req, timeout=30) as r:
        png = r.read()
    img = Image.open(io.BytesIO(png)).convert("RGB")
    arr = np.asarray(img, dtype=np.float32)
    # Terrarium decoding: elev = (R*256 + G + B/256) - 32768
    elev = arr[:, :, 0] * 256.0 + arr[:, :, 1] + arr[:, :, 2] / 256.0 - 32768.0
    return elev


def main() -> int:
    bbox = config.BBOX
    # Tile coords (note: y axis is inverted in slippy maps).
    x0, y0 = lonlat_to_tile(bbox["min_lon"], bbox["max_lat"], ZOOM)
    x1, y1 = lonlat_to_tile(bbox["max_lon"], bbox["min_lat"], ZOOM)
    print(f"Zoom {ZOOM}: tiles x={x0}..{x1}, y={y0}..{y1} ({(x1-x0+1)*(y1-y0+1)} tiles)")

    # Stitch tiles into a single elevation array (north-up, west-left).
    tile_size = 256
    height = (y1 - y0 + 1) * tile_size
    width = (x1 - x0 + 1) * tile_size
    grid = np.zeros((height, width), dtype=np.float32)
    for ty in range(y0, y1 + 1):
        for tx in range(x0, x1 + 1):
            elev = fetch_tile(ZOOM, tx, ty)
            r0 = (ty - y0) * tile_size
            c0 = (tx - x0) * tile_size
            grid[r0:r0 + tile_size, c0:c0 + tile_size] = elev
    print(f"Stitched grid: {grid.shape}, elev range {grid.min():.1f}..{grid.max():.1f} m")

    # Generate contours at 50 m intervals across the actual data range.
    levels = list(range(
        int(math.floor(grid.min() / INTERVAL_M)) * INTERVAL_M,
        int(math.ceil(grid.max() / INTERVAL_M)) * INTERVAL_M + 1,
        INTERVAL_M,
    ))
    print(f"Contour levels: {levels}")

    # matplotlib's contour returns paths in (col, row) pixel coordinates of
    # the input array. We extract them and convert back to lon/lat.
    fig, ax = plt.subplots()
    cs = ax.contour(grid, levels=levels)
    plt.close(fig)

    features = []
    # Pixel → tile coord conversion factors
    tile_x_origin = float(x0)
    tile_y_origin = float(y0)
    for level, segs in zip(cs.levels, cs.allsegs):
        # Major contours (every 100 m) get a flag for stronger styling.
        is_major = (int(level) % 100) == 0
        for seg in segs:
            if len(seg) < 2:
                continue
            coords = []
            for col, row in seg:
                tile_x = tile_x_origin + col / tile_size
                tile_y = tile_y_origin + row / tile_size
                lon = tile_to_lon(tile_x, ZOOM)
                lat = tile_to_lat(tile_y, ZOOM)
                coords.append([round(lon, 6), round(lat, 6)])
            features.append({
                "type": "Feature",
                "properties": {"elevation": int(level), "major": is_major},
                "geometry": {"type": "LineString", "coordinates": coords},
            })

    print(f"Total contour line segments: {len(features):,}")

    out = config.PUBLIC / "contours.geojson"
    fc = {"type": "FeatureCollection", "features": features}
    out.write_text(json.dumps(fc, separators=(",", ":")))
    size_kb = out.stat().st_size / 1024
    print(f"Wrote {out} ({size_kb:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
