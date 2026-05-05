# Sheffield by public transport

Interactive map: click anywhere in Sheffield, see how long it takes to get
to every other part of the city by bus + tram + walking, departing at
weekday 08:30. Inspired by [chronotrains](https://www.chronotrains.com/) and
[castrio.me/nyc](https://castrio.me/nyc).

## Architecture

End-to-end static site. The pipeline runs once on your machine and emits
JSON files; the web app is plain MapLibre + TypeScript with no backend.

```
pipeline/   Python — runs once, produces web/public/data/
web/        Vite + TypeScript + MapLibre — deploys anywhere static
data/       Cached raw and intermediate files (gitignored)
```

Pipeline stages:

| # | Script | What it does |
|---|---|---|
| 1 | `1_download_data.py` | BODS Yorkshire GTFS + Geofabrik South Yorkshire OSM |
| 2 | `2_build_grid.py` | H3 res-8 hex grid covering the Sheffield bounding box (~2k cells) |
| 3 | `3_compute_matrix.py` | r5py: every-cell-to-every-cell travel time at Tue 08:30 |
| 4 | `4_export_static.py` | Per-origin JSON + hex GeoJSON + manifest into `web/public/data/` |

## Prerequisites

- **Python 3.11+**
- **Java 21+** (for R5; `java -version` should report 21 or above)
- **Node 20+** (for the web app)

On Windows the easiest Java is [Temurin 21](https://adoptium.net/).

## Run the pipeline

```bash
cd pipeline

# One-off
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt

# Each step (3 is slow — 5–30 min — and JVM-heavy)
python 1_download_data.py
python 2_build_grid.py
python 3_compute_matrix.py        # set R5_JVM_OPTS=-Xmx8G first if you have RAM to spare
python 4_export_static.py
```

After step 4, `web/public/data/` contains:

```
manifest.json          run config (departure time, bbox, etc.)
hexes.geojson          all hex polygons (~150 KB)
origins/index.json     list of origin h3 ids
origins/{h3}.json      destination travel times for one origin
origins/{h3}.json.gz   gzipped variant for hosts that serve as-is
```

## Run the web app

```bash
cd web
npm install
npm run dev
```

Open http://localhost:5173. Click anywhere on the map to set the origin.

## Configuration

Edit `pipeline/config.py`:

- `BBOX` — extend coverage (e.g. to all of South Yorkshire) by widening this.
- `H3_RESOLUTION` — 8 is the default. Drop to 7 for faster compute / coarser map; 9 for ~7× more cells.
- `DEPARTURE_DATE` / `DEPARTURE_TIME` — pick a non-school-holiday weekday and a time that has a representative service level.
- `MAX_TRAVEL_TIME_MIN` — anything beyond this is treated as unreachable.

## Known caveats

- Single-snapshot departure time. A v2 would compute multiple times and add a slider.
- Supertram is included via BODS. If trams turn out to be missing or modeled oddly in the feed, hand-build a small supplementary GTFS for the 3 lines and pass it as a second feed to `TransportNetwork`.
- BODS feeds occasionally have calendar gaps. Pick a Tuesday well clear of bank holidays. If `3_compute_matrix.py` reports unreachable for everything, that's almost always the cause — try a different `DEPARTURE_DATE`.
- Walking speed is fixed at 4.8 km/h.

## Deploying

Whatever serves `web/dist/` works:

```bash
cd web
npm run build
# Cloudflare Pages, Netlify, GitHub Pages — all fine. No backend needed.
```

## Data attribution

- Bus & tram timetables: [Bus Open Data Service](https://www.bus-data.dft.gov.uk/) (DfT, Open Government Licence v3.0).
- Walking network: © [OpenStreetMap](https://openstreetmap.org/copyright) contributors (ODbL).
- Basemap tiles: © OpenStreetMap contributors, tiles by [CARTO](https://carto.com/attributions).
- Routing: [R5](https://github.com/conveyal/r5) by Conveyal.
