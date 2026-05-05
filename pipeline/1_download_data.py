"""Download BODS Yorkshire GTFS + Geofabrik South Yorkshire OSM extract.

Both files are large-ish (GTFS ~50 MB, OSM ~80 MB). Re-runs are skipped if
the files already exist; pass --force to re-download.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests
from tqdm import tqdm

import config


def download(url: str, dest: Path, force: bool = False) -> None:
    if dest.exists() and not force:
        size_mb = dest.stat().st_size / 1024 / 1024
        print(f"  exists ({size_mb:.1f} MB), skipping. Pass --force to re-download.")
        return

    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        with open(dest, "wb") as f, tqdm(
            total=total, unit="B", unit_scale=True, desc=dest.name
        ) as bar:
            for chunk in r.iter_content(chunk_size=64 * 1024):
                f.write(chunk)
                bar.update(len(chunk))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="re-download even if cached")
    args = ap.parse_args()

    print(f"GTFS  -> {config.RAW / 'yorkshire-gtfs.zip'}")
    download(config.BODS_GTFS_URL, config.RAW / "yorkshire-gtfs.zip", args.force)

    print(f"OSM   -> {config.RAW / 'south-yorkshire.osm.pbf'}")
    download(config.OSM_PBF_URL, config.RAW / "south-yorkshire.osm.pbf", args.force)

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
