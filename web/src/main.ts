import maplibregl from "maplibre-gl";
import type { MapLayerMouseEvent } from "maplibre-gl";

interface Manifest {
  departure_date: string;
  departure_time: string;
  departure_window_min: number;
  max_travel_time_min: number;
  h3_resolution: number;
  bbox: { min_lat: number; max_lat: number; min_lon: number; max_lon: number };
  origin_count: number;
  hex_area_km2: number;
  city_area_km2: number;
}

interface OriginPayload {
  o: string;
  d: Record<string, number>;
}

const DATA_BASE = "data";
const HEXES_LAYER = "hexes-fill";
const SELECTED_LAYER = "hexes-selected";

const status = document.getElementById("status")!;
const tooltip = document.getElementById("tooltip")!;
const depTimeEl = document.getElementById("dep-time")!;

// About / methodology modal.
const aboutModal = document.getElementById("about-modal")!;
const aboutBackdrop = document.getElementById("about-backdrop")!;
function openAbout() {
  aboutModal.classList.remove("hidden");
  aboutBackdrop.classList.remove("hidden");
  aboutBackdrop.setAttribute("aria-hidden", "false");
}
function closeAbout() {
  aboutModal.classList.add("hidden");
  aboutBackdrop.classList.add("hidden");
  aboutBackdrop.setAttribute("aria-hidden", "true");
}
document.getElementById("about-trigger")!.addEventListener("click", openAbout);
document.getElementById("about-close")!.addEventListener("click", closeAbout);
aboutBackdrop.addEventListener("click", closeAbout);
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !aboutModal.classList.contains("hidden")) closeAbout();
});

function setStatus(msg: string) {
  status.textContent = msg;
}

async function loadJSON<T>(path: string): Promise<T> {
  const r = await fetch(`${DATA_BASE}/${path}`, { cache: "no-store" });
  if (!r.ok) throw new Error(`${path}: ${r.status}`);
  return r.json() as Promise<T>;
}

function colourForMinutes(t: number, max: number): string {
  // 0 → green, mid → yellow/orange, max → red. Slightly desaturated to play
  // nicer with the basemap underneath at 0.45 opacity.
  const x = Math.max(0, Math.min(1, t / max));
  if (x < 0.25) return interp("#4edea3", "#c1d860", x / 0.25);
  if (x < 0.5)  return interp("#c1d860", "#f0c060", (x - 0.25) / 0.25);
  if (x < 0.75) return interp("#f0c060", "#e08040", (x - 0.5) / 0.25);
  return interp("#e08040", "#d04040", (x - 0.75) / 0.25);
}

function interp(a: string, b: string, t: number): string {
  const pa = parseHex(a), pb = parseHex(b);
  const r = Math.round(pa[0] + (pb[0] - pa[0]) * t);
  const g = Math.round(pa[1] + (pb[1] - pa[1]) * t);
  const bl = Math.round(pa[2] + (pb[2] - pa[2]) * t);
  return `rgb(${r},${g},${bl})`;
}

function parseHex(h: string): [number, number, number] {
  const n = parseInt(h.slice(1), 16);
  return [(n >> 16) & 0xff, (n >> 8) & 0xff, n & 0xff];
}

async function main() {
  setStatus("Loading manifest…");
  const manifest = await loadJSON<Manifest>("manifest.json").catch(() => null);
  if (!manifest) {
    setStatus("No data yet. Run the pipeline (see README) to generate data/.");
    return;
  }
  depTimeEl.textContent = manifest.departure_time.slice(0, 5);

  const map = new maplibregl.Map({
    container: "map",
    style: {
      version: 8,
      sources: {
        // dark_all has the full dark theme with subtle roads + place labels visible.
        carto: {
          type: "raster",
          tiles: [
            "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
            "https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
            "https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
            "https://d.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
          ],
          tileSize: 256,
          attribution: "© OpenStreetMap contributors © CARTO",
        },
      },
      layers: [
        { id: "carto-base", type: "raster", source: "carto" },
      ],
    },
    center: [-1.4701, 53.3811], // Sheffield Town Hall
    zoom: 11.4,
  });
  // Bottom-left keeps the nav clear of the legend (top-right) and the title
  // card (top-left). Compass is hidden — bearing isn't useful for an isochrone.
  map.addControl(
    new maplibregl.NavigationControl({ showCompass: false }),
    "bottom-left",
  );

  await new Promise<void>((res) => map.on("load", () => res()));

  setStatus("Loading map data…");
  const [hexes, boundary, transit, contours] = await Promise.all([
    loadJSON<GeoJSON.FeatureCollection>("hexes.geojson"),
    loadJSON<GeoJSON.FeatureCollection>("boundary.geojson").catch(() => null),
    loadJSON<GeoJSON.FeatureCollection>("transit-shapes.geojson").catch(() => null),
    loadJSON<GeoJSON.FeatureCollection>("contours.geojson").catch(() => null),
  ]);

  // The "outside-the-city" donut polygon: world bbox with Sheffield punched
  // out as a hole. Used as a fully opaque mask above all map content so the
  // viewport cleanly stops at the city edge.
  let cityMaskGeom: GeoJSON.Polygon | null = null;
  if (boundary) {
    const sheffieldRings: number[][][] = [];
    for (const f of boundary.features) {
      const g = f.geometry as GeoJSON.Polygon | GeoJSON.MultiPolygon;
      if (g.type === "Polygon") {
        sheffieldRings.push(g.coordinates[0]);
      } else if (g.type === "MultiPolygon") {
        for (const poly of g.coordinates) sheffieldRings.push(poly[0]);
      }
    }
    const worldRing = [
      [-180, -85], [180, -85], [180, 85], [-180, 85], [-180, -85],
    ];
    cityMaskGeom = { type: "Polygon", coordinates: [worldRing, ...sheffieldRings] };
    map.addSource("city-mask", {
      type: "geojson",
      data: { type: "Feature", geometry: cityMaskGeom, properties: {} },
    });
  }

  map.addSource("hexes", { type: "geojson", data: hexes, promoteId: "h3" });
  map.addLayer({
    id: HEXES_LAYER,
    type: "fill",
    source: "hexes",
    paint: {
      // Hexes without a feature-state fall back to fully transparent.
      "fill-color": ["coalesce", ["feature-state", "colour"], "rgba(0,0,0,0)"],
      "fill-opacity": 0.45,
      "fill-antialias": false,
    },
  });

  // Contour lines (50 m intervals) above the heatmap. Major lines (every
  // 100 m) get a touch more weight; minor ones are nearly transparent so
  // they read as gentle topo cues without competing with the colours.
  if (contours) {
    map.addSource("contours", { type: "geojson", data: contours });
    map.addLayer({
      id: "contours-minor",
      type: "line",
      source: "contours",
      filter: ["!", ["get", "major"]],
      paint: {
        "line-color": "rgba(255, 255, 255, 0.07)",
        "line-width": 0.4,
      },
    });
    map.addLayer({
      id: "contours-major",
      type: "line",
      source: "contours",
      filter: ["==", ["get", "major"], true],
      paint: {
        "line-color": "rgba(255, 255, 255, 0.18)",
        "line-width": 0.7,
      },
    });
  }

  // Transit network underlay — bus + tram route shapes from GTFS.
  // Buses are drawn as faint blue lines: where many routes share a corridor,
  // the alpha stacks naturally so busy streets self-emphasise. Trams sit
  // above in Sheffield Supertram yellow.
  if (transit) {
    map.addSource("transit", { type: "geojson", data: transit });

    // Bus glow halo — faint, diffuse.
    map.addLayer({
      id: "transit-bus-glow",
      type: "line",
      source: "transit",
      filter: ["==", ["get", "route_type"], 3],
      paint: {
        "line-color": "rgba(173, 198, 255, 0.07)",
        "line-blur": 2.5,
        "line-width": [
          "interpolate", ["linear"], ["zoom"], 10, 1.6, 14, 4.0,
        ],
      },
    });

    // Bus lines themselves — single low-alpha colour, designed to stack.
    map.addLayer({
      id: "transit-bus",
      type: "line",
      source: "transit",
      filter: ["==", ["get", "route_type"], 3],
      layout: { "line-cap": "round" },
      paint: {
        "line-color": "rgba(95, 130, 210, 0.10)",
        "line-width": [
          "interpolate", ["linear"], ["zoom"], 10, 0.6, 14, 1.4,
        ],
      },
    });

    // Tram glow halo — broader, in the tram colour.
    map.addLayer({
      id: "transit-tram-glow",
      type: "line",
      source: "transit",
      filter: ["==", ["get", "route_type"], 0],
      paint: {
        "line-color": "rgba(255, 205, 0, 0.20)",
        "line-blur": 4,
        "line-width": [
          "interpolate", ["linear"], ["zoom"], 10, 4, 14, 9,
        ],
      },
    });

    // Tram lines on top — Sheffield Supertram yellow, crisp.
    map.addLayer({
      id: "transit-tram",
      type: "line",
      source: "transit",
      filter: ["==", ["get", "route_type"], 0],
      layout: { "line-cap": "round" },
      paint: {
        "line-color": "#ffcd00",
        "line-width": [
          "interpolate", ["linear"], ["zoom"], 10, 1.2, 14, 2.4,
        ],
        "line-opacity": 0.85,
      },
    });
  }

  // Opaque "outside Sheffield" mask — drawn above the heatmap and roads so
  // nothing visible (labels, basemap roads, our overlay) bleeds outside the city.
  if (cityMaskGeom) {
    map.addLayer({
      id: "city-mask-fill",
      type: "fill",
      source: "city-mask",
      // Slightly cooler/darker than the page bg (--bg #131313) so the city
      // silhouette reads as a distinct "stage" sitting on the page.
      paint: { "fill-color": "#0a0d14", "fill-opacity": 1 },
    });
  }

  // Boundary outline ON TOP of the mask so the city silhouette stays crisp.
  if (boundary) {
    map.addSource("boundary", { type: "geojson", data: boundary });
    map.addLayer({
      id: "boundary-line",
      type: "line",
      source: "boundary",
      paint: {
        "line-color": "rgba(173, 198, 255, 0.55)",
        "line-width": 1.25,
        "line-blur": 0.6,
      },
    });
  }

  // Centre on Sheffield town hall — the LAD boundary stretches far into the
  // Peak District moorland, so fit-to-bounds zooms out too far.
  map.jumpTo({ center: [-1.4701, 53.3811], zoom: 11.4 });

  // Selected origin highlight.
  map.addSource("selected", {
    type: "geojson",
    data: { type: "FeatureCollection", features: [] },
  });
  map.addLayer({
    id: SELECTED_LAYER,
    type: "line",
    source: "selected",
    paint: {
      "line-color": "rgba(229, 226, 225, 0.55)",
      "line-width": 1,
    },
  });

  // Build a quick centroid index for nearest-cell lookup on click.
  const centroids = hexes.features.map((f) => {
    const coords = (f.geometry as GeoJSON.Polygon).coordinates[0];
    let lon = 0, lat = 0;
    for (let i = 0; i < coords.length - 1; i++) { lon += coords[i][0]; lat += coords[i][1]; }
    const n = coords.length - 1;
    return { id: f.id as string, lon: lon / n, lat: lat / n };
  });

  function nearestHex(lon: number, lat: number): string {
    let best = centroids[0]!.id;
    let bestD = Infinity;
    for (const c of centroids) {
      const dx = c.lon - lon;
      const dy = c.lat - lat;
      const d = dx * dx + dy * dy;
      if (d < bestD) { bestD = d; best = c.id; }
    }
    return best;
  }

  const cache = new Map<string, OriginPayload>();
  let currentOrigin: string | null = null;

  async function selectOrigin(originId: string) {
    if (originId === currentOrigin) return;
    currentOrigin = originId;
    setStatus(`Loading travel times from ${originId.slice(0, 8)}…`);
    let payload = cache.get(originId);
    if (!payload) {
      try {
        payload = await loadJSON<OriginPayload>(`origins/${originId}.json`);
        cache.set(originId, payload);
      } catch {
        setStatus("No travel data for that hex (likely out of grid coverage).");
        return;
      }
    }

    // Reset all states, then set new ones.
    for (const f of hexes.features) {
      map.setFeatureState({ source: "hexes", id: f.id! }, { colour: null });
    }
    const max = manifest!.max_travel_time_min;
    for (const [destId, mins] of Object.entries(payload.d)) {
      map.setFeatureState(
        { source: "hexes", id: destId },
        { colour: colourForMinutes(mins, max), minutes: mins },
      );
    }
    // Self-cell explicitly 0.
    map.setFeatureState(
      { source: "hexes", id: originId },
      { colour: colourForMinutes(0, max), minutes: 0 },
    );

    // Highlight the chosen origin.
    const origin = hexes.features.find((f) => f.id === originId);
    (map.getSource("selected") as maplibregl.GeoJSONSource).setData({
      type: "FeatureCollection",
      features: origin ? [origin] : [],
    });

    renderReachStats(payload, manifest!);
  }

  function renderReachStats(payload: OriginPayload, m: Manifest) {
    const tiers = [15, 30, 45, 60];
    const counts: Record<number, number> = {};
    for (const t of tiers) counts[t] = 0;
    for (const mins of Object.values(payload.d)) {
      for (const t of tiers) if (mins <= t) counts[t]++;
    }
    const rows = tiers.map((t) => {
      const km2 = counts[t] * m.hex_area_km2;
      const pct = (km2 / m.city_area_km2) * 100;
      return `<div class="reach-row">
        <span class="reach-time">${t} min</span>
        <span class="reach-area">${km2.toFixed(1)} km²</span>
        <span class="reach-pct">${pct.toFixed(0)}%</span>
      </div>`;
    }).join("");
    status.innerHTML = `
      <div class="reach-head">Reachable area</div>
      <div class="reach-grid">${rows}</div>
      <div class="reach-foot">of Sheffield (${m.city_area_km2} km²)</div>
    `;
  }

  map.on("click", HEXES_LAYER, (e: MapLayerMouseEvent) => {
    const { lng, lat } = e.lngLat;
    selectOrigin(nearestHex(lng, lat));
  });

  map.on("mousemove", HEXES_LAYER, (e: MapLayerMouseEvent) => {
    if (!e.features || e.features.length === 0) return;
    const f = e.features[0];
    const state = map.getFeatureState({ source: "hexes", id: f.id! });
    const minutes = state?.minutes;
    tooltip.classList.remove("hidden");
    tooltip.style.left = `${e.point.x + 14}px`;
    tooltip.style.top = `${e.point.y + 14}px`;
    if (currentOrigin == null) {
      tooltip.innerHTML = "<em>Click a hex to set origin</em>";
    } else if (typeof minutes === "number") {
      tooltip.innerHTML = `<strong>${minutes} min</strong>`;
    } else {
      tooltip.innerHTML = "<em>Not reachable in 90 min</em>";
    }
  });
  map.on("mouseleave", HEXES_LAYER, () => tooltip.classList.add("hidden"));

  // Layer toggles — sync visibility from checkbox state, then listen for changes.
  const LAYER_GROUPS: Record<string, string[]> = {
    tram: ["transit-tram-glow", "transit-tram"],
    bus: ["transit-bus-glow", "transit-bus"],
    contours: ["contours-minor", "contours-major"],
  };
  function applyLayerVisibility(group: string, visible: boolean) {
    const ids = LAYER_GROUPS[group] ?? [];
    for (const id of ids) {
      if (map.getLayer(id)) {
        map.setLayoutProperty(id, "visibility", visible ? "visible" : "none");
      }
    }
  }
  document.querySelectorAll<HTMLInputElement>('#layers input[type="checkbox"]').forEach((cb) => {
    const group = cb.dataset.layer!;
    applyLayerVisibility(group, cb.checked);
    cb.addEventListener("change", () => applyLayerVisibility(group, cb.checked));
  });

  // Search.
  const searchForm = document.getElementById("search") as HTMLFormElement;
  const searchInput = document.getElementById("search-input") as HTMLInputElement;
  const searchError = document.getElementById("search-error")!;
  searchForm.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const q = searchInput.value.trim();
    if (!q) return;
    searchError.classList.add("hidden");
    searchError.textContent = "";
    try {
      const result = await geocode(q);
      if (!result) {
        searchError.textContent = "No match found in Sheffield.";
        searchError.classList.remove("hidden");
        return;
      }
      map.flyTo({ center: [result.lon, result.lat], zoom: 13, duration: 600 });
      await selectOrigin(nearestHex(result.lon, result.lat));
    } catch (e) {
      searchError.textContent = "Search failed. Try again.";
      searchError.classList.remove("hidden");
      console.error(e);
    }
  });

  // Default origin: nearest hex to Sheffield Town Hall (city centre).
  await selectOrigin(nearestHex(-1.4701, 53.3811));
}

const POSTCODE_RE = /^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$/i;
const SHEFFIELD_VIEWBOX = "-1.80,53.50,-1.32,53.30"; // left,top,right,bottom

interface GeocodeResult { lat: number; lon: number; name: string; }

async function geocode(query: string): Promise<GeocodeResult | null> {
  if (POSTCODE_RE.test(query)) {
    const r = await fetch(`https://api.postcodes.io/postcodes/${encodeURIComponent(query)}`);
    if (r.ok) {
      const j = await r.json();
      const p = j.result;
      return { lat: p.latitude, lon: p.longitude, name: p.postcode };
    }
    return null;
  }
  // Nominatim, biased to Sheffield via viewbox + bounded=1.
  const url = new URL("https://nominatim.openstreetmap.org/search");
  url.searchParams.set("q", `${query}, Sheffield, UK`);
  url.searchParams.set("format", "json");
  url.searchParams.set("limit", "1");
  url.searchParams.set("viewbox", SHEFFIELD_VIEWBOX);
  url.searchParams.set("bounded", "1");
  const r = await fetch(url.toString(), { headers: { "Accept": "application/json" } });
  if (!r.ok) throw new Error(`nominatim ${r.status}`);
  const arr = await r.json();
  if (!arr.length) return null;
  const hit = arr[0];
  return { lat: parseFloat(hit.lat), lon: parseFloat(hit.lon), name: hit.display_name };
}

main().catch((e) => {
  console.error(e);
  setStatus(`Error: ${e.message}`);
});
