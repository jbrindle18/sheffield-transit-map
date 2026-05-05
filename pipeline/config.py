"""Shared config for the Sheffield isochrone pipeline."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
INTERMEDIATE = ROOT / "data" / "intermediate"
PUBLIC = ROOT / "web" / "public" / "data"

# Sheffield bounding box (rough Sheffield City Council area).
# Tweak if you want to extend coverage.
BBOX = {
    "min_lat": 53.30,
    "max_lat": 53.50,
    "min_lon": -1.65,
    "max_lon": -1.30,
}

# H3 resolution. 8 ≈ 0.74 km², 9 ≈ 0.105 km² (~175 m edge).
# Res 9 inside the Sheffield boundary gives ~3500 cells.
H3_RESOLUTION = 9

# Departure window for the matrix. Tuesday 08:30 local, 1-hour window.
# Pick a date during term-time, well clear of UK bank holidays / school holidays.
DEPARTURE_DATE = "2026-05-19"   # Tuesday in May 2026
DEPARTURE_TIME = "08:30:00"
DEPARTURE_WINDOW_MIN = 60        # search across an hour for best connection

# Travel-time cap (minutes). Anything beyond is treated as unreachable.
MAX_TRAVEL_TIME_MIN = 90

# Walking parameters.
WALK_SPEED_KMH = 4.8
MAX_WALK_MIN = 30                # cap walking-only legs

# Data sources.
BODS_GTFS_URL = "https://data.bus-data.dft.gov.uk/timetable/download/gtfs-file/yorkshire/"
OSM_PBF_URL = "https://download.geofabrik.de/europe/united-kingdom/england/south-yorkshire-latest.osm.pbf"
