# Asset inventory and Phase 1 report

| # | File | Origin | Size | Role in the advert | Allowed in final picture? |
|---|---|---|---|---|---|
| 1 | `00_assets/cimiano/IMG_2111_cimiano_platform.jpg` | client photo | 640×1138 | S01 opening: green CIMIANO platform sign, native 9:16 | ✅ yes |
| 2 | `00_assets/cimiano/IMG_4079_cimiano_entrance.jpg` | client photo | 1800×1020 | S01 hero: entrance sign, stairs, red handrails, M totem | ✅ yes |
| 3 | `00_assets/cimiano/IMG_4081_cimiano_entrance_wide.jpg` | client photo (older, low-res) | 457×437 | S02 "exit" photo card (kept small because it is low-res) | ✅ yes |
| 4 | `00_assets/route/IMG_4188_corner_trafficlight.png` | Street View screenshot | 1320×2868 | reference: Via Padova corner, yellow pole, park | ❌ reference only |
| 5 | `00_assets/route/IMG_4189_via_padova_ahead.png` | Street View screenshot | 1320×2868 | reference: Via Padova, trolley wires | ❌ reference only |
| 6 | `00_assets/route/IMG_4190_via_padova_173.png` | Street View screenshot | 1320×2868 | reference: no. 173, shop row | ❌ reference only |
| 7 | `00_assets/route/IMG_4191_streetview_storefront.jpg` | Street View screenshot | 1320×2083 | reference: storefront context, neighbour shop | ❌ reference only |
| 8 | `00_assets/streetview/route_streetview.mp4` | Street View screen recording | 1320×2868, 60 fps, 119 s | route analysis (not committed, 222 MB; see SOURCE.md) | ❌ reference only |
| 9 | `00_assets/storefront/puntocom_storefront_original.jpg` | client photo | 2356×1640 | **S05 destination: used unmodified** | ✅ yes (master) |
| 10 | `00_assets/logo/puntocom_logo_master.jpg` | official logo | 1004×620 | **S06: official brand master** | ✅ yes (master) |

## Derived assets

| File | How it was made |
|---|---|
| `06_motion_graphics/puntocom_logo_full_alpha.png` | `tools/extract_logo.py`: the flat navy field (RGB 12,22,32) is un-premultiplied to alpha. Logo pixels, colours, typography and proportions are not redrawn. The check is in `01_analysis/logo_alpha_check.jpg`. |
| `06_motion_graphics/puntocom_logo_symbol.png` / `_wordmark.png` / `_subline.png` | Same extraction, split by row bands (symbol 90–390, PUNTOCOM 392–480, CAF PATRONATO + gold rules 480–525) for the staged reveal. Stacked together they reproduce the full logo exactly. |

## Missing resources and integration status (Phase 1 findings)

| Need | Status | Consequence |
|---|---|---|
| **AI video generation** (image-to-video) | ❌ No engine available in this environment. The connected ElevenLabs connector is the *restricted* one (no image, video or music). No Runway, Kling, Veo, Luma or Sora integration. | Scenes 02–03 are built as an original **procedural 3D "navigation mode" street** (code-rendered) plus the real exit photo. Ready-to-run prompts for each AI clip are in `03_ai_prompts/`. The AE project has placeholder slots for them. |
| **Adobe After Effects** | ❌ Not installed (Linux cloud container). | A `.aep` cannot be written without AE. `05_aftereffects/scripts/build_puntocom_project.jsx` builds and saves the full editable project in one run. The master MP4 was rendered with the equivalent Python/FFmpeg pipeline (`tools/render_video.py`). |
| **Italian male voiceover** | ⚠️ ElevenLabs is reachable. The first request returned "free generations busy, nothing charged". | The mix has the VO cue points and ducking ready. Generate the VO, then run `python3 tools/make_audio.py --vo-lines l1.wav … l5.wav` and re-mux. See `07_audio/README.md`. |
| **Map data** (OSM, Nominatim, OSRM, map tiles) | ❌ Blocked by the network policy. | The GPS map is a labelled schematic. See `route_analysis.md` §3 for the one-step upgrade. |
| Higher-resolution `IMG_4081` | optional | It is 457 px wide, so it is used as a floating card, not full screen. |
| Vector logo (SVG/AI) | optional | The raster master extracts cleanly. A vector master would allow larger, sharper reveals. |
