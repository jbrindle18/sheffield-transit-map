# Pickup list

## Next session

- [ ] **Zoom / tooltip overlap.** MapLibre's default `NavigationControl` is anchored top-right, same corner as the legend panel (`#legend`, top: 16px, right: 16px, 220px wide). They collide. Fix options: move the nav control to bottom-right (`map.addControl(..., "bottom-right")`), or restyle/hide the nav and use scroll/pinch only. The hover tooltip is fixed-position relative to cursor and may also clip the legend panel — verify after moving the nav.

- [ ] **Methodology section.** Write a concise "How this works" panel/page explaining:
  - Data: BODS Yorkshire GTFS + Geofabrik South Yorkshire OSM
  - Routing: R5 via r5py, departure window Tue 2026-05-19 08:30 + 60 min, median across the window
  - Grid: H3 res 9 (~175 m hexes), 3,935 cells clipped to Sheffield LAD boundary (ONS)
  - Overlay: GTFS bus + tram route shapes (188 routes) — see `pipeline/6_extract_transit.py`
  - Caveat: single-snapshot timetable; not real-time; walking capped at 30 min
  - Could be a small "About" link in the title card opening a glassmorphic modal, or a second floating panel

- [ ] **Host it.** GitHub Pages is the simplest first step:
  1. `git init`, `git add`, commit
  2. New GitHub repo (public)
  3. Push
  4. Build the web app: `cd web && npm run build` → `web/dist/`
  5. GitHub Pages workflow: deploy from `gh-pages` branch or via Actions
  6. Tweaks needed: set `base` in `web/vite.config.ts` to `/<repo-name>/` for GH Pages subpath
  7. Watch repo size — `web/public/data/origins/` has 3,935 small JSON files plus `.json.gz` mirrors. ~30 MB total. Within GitHub's 1 GB soft limit but worth checking.
  8. Alternative: Cloudflare Pages — better CDN, no subpath gymnastics, generous free tier

## Open ideas (not committed)

- Time-of-day slider — needs matrices at 4 departure times and a UI control
- Detailed journey display (which buses/trams) — needs either a small R5 backend on a VM or per-origin journey JSONs (~1–4 GB at res 9). Discussed earlier in chat; deferred to v2.
- Add Tram Train + National Rail (we already enabled `TransportMode.RAIL` so train data IS in the matrix from BODS — but no overlay yet)
- Population-weighted accessibility ("X people reachable in Y min") — needs ONS LSOA population
- Extend grid to full South Yorkshire MCA (Rotherham, Barnsley, Doncaster — same BODS feed)

## Health check before tomorrow

- Pipeline runnable: `cd pipeline && .venv/Scripts/python.exe 0_get_boundary.py && ... && 6_extract_transit.py`
- Web app: `cd web && npm run dev` → http://localhost:5173
- Java 21 (Temurin) installed at `C:\Program Files\Eclipse Adoptium\jdk-21.0.11.10-hotspot`
- The matrix.parquet (10.5 MB) can be regenerated; everything in `web/public/data/` is derived
