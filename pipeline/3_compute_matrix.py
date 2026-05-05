"""Compute a travel-time matrix for the H3 grid using r5py.

For every origin cell, the travel time (minutes) to every destination cell
at the configured weekday departure time, including walking, bus, tram,
and rail egress walks.

This is the slow step. Expect 5-30 minutes on a laptop with the default
~800-cell grid. Tune JVM heap with R5_JVM_OPTS before running, e.g.:
    set R5_JVM_OPTS=-Xmx8G

Outputs:
  data/intermediate/matrix.parquet   columns: from_id, to_id, travel_time
"""
from __future__ import annotations

import datetime as dt
import sys
import time

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

import config


def main() -> int:
    # Import r5py lazily so the rest of the pipeline can run without Java installed.
    from r5py import TransportNetwork, TravelTimeMatrix, TransportMode

    grid = pd.read_parquet(config.INTERMEDIATE / "grid.parquet")
    print(f"Loaded {len(grid):,} grid cells")

    # r5py requires an `id` column on the GeoDataFrame.
    points = gpd.GeoDataFrame(
        {"id": grid["h3"].astype(str)},
        geometry=[Point(lon, lat) for lon, lat in zip(grid["lon"], grid["lat"])],
        crs="EPSG:4326",
    )

    osm_pbf = config.RAW / "south-yorkshire.osm.pbf"
    gtfs_zip = config.RAW / "yorkshire-gtfs.zip"
    for f in (osm_pbf, gtfs_zip):
        if not f.exists():
            print(f"Missing {f}. Run pipeline/1_download_data.py first.", file=sys.stderr)
            return 1

    print("Building R5 transport network (one-time, can take a few minutes)...")
    t0 = time.time()
    network = TransportNetwork(str(osm_pbf), [str(gtfs_zip)])
    print(f"  built in {time.time() - t0:.1f}s")

    departure = dt.datetime.fromisoformat(f"{config.DEPARTURE_DATE}T{config.DEPARTURE_TIME}")
    print(f"Departure window: {departure.isoformat()} + {config.DEPARTURE_WINDOW_MIN} min")

    print("Computing travel-time matrix (this is the slow part)...")
    t0 = time.time()
    matrix = TravelTimeMatrix(
        network,
        origins=points,
        destinations=points,
        departure=departure,
        departure_time_window=dt.timedelta(minutes=config.DEPARTURE_WINDOW_MIN),
        transport_modes=[
            TransportMode.WALK,
            TransportMode.BUS,
            TransportMode.TRAM,
            TransportMode.RAIL,
        ],
        access_modes=[TransportMode.WALK],
        egress_modes=[TransportMode.WALK],
        max_time=dt.timedelta(minutes=config.MAX_TRAVEL_TIME_MIN),
        max_time_walking=dt.timedelta(minutes=config.MAX_WALK_MIN),
        speed_walking=config.WALK_SPEED_KMH,
    )
    print(f"  done in {(time.time() - t0) / 60:.1f} min, {len(matrix):,} pairs")

    # Drop unreachable rows and downcast to int16 to keep file size sane.
    df = pd.DataFrame(matrix.drop(columns=[c for c in matrix.columns if c == "geometry"], errors="ignore"))
    df = df.dropna(subset=["travel_time"])
    df["travel_time"] = df["travel_time"].astype("int16")

    out = config.INTERMEDIATE / "matrix.parquet"
    df.to_parquet(out, index=False)
    print(f"Wrote {out} ({out.stat().st_size / 1024 / 1024:.1f} MB)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
