# Route analysis: Cimiano M2 → Puntocom, Via Padova 167

Source: Google Street View screen recording (119 s, 1320×2868), plus screenshots IMG_4188–4191.
Method: frames extracted with FFmpeg every 2 s (`frames/f_001–060.jpg`), shown in
`contact_sheet_streetview_00-60s.jpg` and `contact_sheet_streetview_60-120s.jpg`, plus 12 larger keyframes
in `keyframes_streetview_A/B.jpg`.

```bash
ffmpeg -i route_streetview.mp4 -vf "fps=1/2,scale=300:-2" frames/f_%03d.jpg
montage frames/f_0{01..30}.jpg -tile 10x3 -geometry 180x391+4+4 contact_A.jpg
```

## 1. Key finding: the recording runs backwards

The recording **starts at the destination end (Via Padova) and finishes at the Cimiano metro exit.**
For the advert, the walking direction is the reverse of the recording order.

| Rec. time | What is visible (verified) | Advert order |
|---|---|---|
| 104–118 s | Cimiano M2 surface exit: **red handrails**, stairwell, red **"M" totem**, grey lift tower, bike-share rack, pedestrian crossing, "zona 30" sign | **START** |
| 82–100 s | Green M2 trains on the **open-air track** behind railings next to the exit; low pink/yellow buildings; sign "← … Comunale di via Don Orione" (partially legible) | Leaving the station |
| 60–80 s | Residential street with a **stone balustrade/parapet** along one side (canal-style embankment), Zona 30 road markings, parked cars, 6–8 storey 1960s–70s blocks | Residential stretch |
| 20–58 s | Residential streets, corner minimarket, crossings, tree-lined stretch with **green park fence** | Approach |
| 6–18 s | **Fenced green park/garden** on the corner, "zona 30" sign and blue arrow on a graffiti-covered corner building | Corner before Via Padova |
| 0–6 s | **Signalised intersection with Via Padova**: Milan-yellow traffic-light pole with green signal, zebra crossings, trolleybus overhead wires, bus shelter | Turn onto Via Padova |
| (IMG_4189/4190) | Via Padova: no. **173** (Bar Giulia), then continuing; the app shows "Arrivo alle Via Padova, 167 — 70 m" | Final approach |
| (IMG_4191) | Puntocom storefront (two black signs, "SECTOR / Fashion & Jewels" next door) | **DESTINATION** |

## 2. What is **not** verified (so the advert does not claim it)

- **Intermediate street names.** Apart from Via Padova, no street-name plate is legible in the recording.
  The advert therefore names only *Cimiano M2* and *Via Padova 167*.
- **Left/right turn directions.** The 360° recording UI makes the heading ambiguous. The advert's step cards
  describe landmarks ("Esci dalla metro", "Strade residenziali · Zona 30 · lungo il parco",
  "Al semaforo: Via Padova") and give no turn instructions.
- **Distances and walking times.** None are invented. The only number shown in the source is the app's
  "70 m" to arrival, which is not used.
- **Exact map geometry.** OpenStreetMap, Nominatim and OSRM are blocked by this environment's network policy,
  so no verified coordinates could be fetched. The GPS map (Scene 04) is therefore drawn as a
  **schematic diagram**, captioned on screen *"Schema indicativo · non in scala"*. It shows only: Cimiano M2
  station, the M2 line, the Via Padova axis, the destination pin, and an orange route connecting them.

## 3. How to make Scene 04 geographically exact (one step)

1. Export the walking route (Google Maps → share/export, or plan it in OpenStreetMap/uMap) as GPX/GeoJSON.
2. Project the coordinates to the 2400×2400 map canvas, for example with Web-Mercator and the bounding box padded by 10 %.
3. Paste the points into:
   - `tools/render_video.py` → `P_CIM`, `P_DEST`, `VIA_PADOVA`, `M2_LINE`, `ROUTE`
   - `05_aftereffects/scripts/build_puntocom_project.jsx` → the `shapePath(c4, …)` vertices in `04_ROUTE_ANIMATION`
4. Remove the "Schema indicativo" caption and re-render.

## 4. Visual characteristics carried into the advert

- Milan "case popolari"/1960s–70s residential blocks, 5–9 storeys, ground-floor shops → procedural street (S03)
- Zona 30 signage and road roundels → sign and road marking in S03
- Fenced park along the route → green fence and trees in S03
- Milan **yellow** traffic-light pole with an arm over the road, plus a zebra crossing at Via Padova → S03, step 3
- Red "M" totem at the exit → S03 start
- Daylight, overcast summer light in the references. The procedural street uses a stylised dusk
  "navigation mode" grade, so it is visibly not documentary footage.
