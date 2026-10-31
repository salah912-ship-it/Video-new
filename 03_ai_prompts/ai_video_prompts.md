# AI video prompts: individual clips

**Status: not generated.** No image-to-video engine is connected to this production environment
(see `01_analysis/asset_inventory.md`). The prompts below are ready to run in Runway Gen-4, Kling 2.x,
Google Veo 3 or Luma Ray 2 (image-to-video mode). Each clip replaces the matching `AI_*` placeholder solid in
the AE comp `02_STREET_SEQUENCES`.

**Rules for every clip**
- Use image-to-video with the listed **real reference** as the first frame or style reference. Never use Street View
  screenshots as an init image in the final pipeline. They are for describing geography only.
- Generate 5 s at 24/30 fps, vertical 9:16 (or 16:9 and crop in AE). Use the same seed family per scene.
- Shared look: *overcast summer daylight, soft diffuse light, neutral-cool shadows, Kodak 2383-style print
  emulation, 35 mm lens, eye height 1.6 m, slow steady gimbal forward movement, natural motion blur, no
  people facing camera.*
- **Negative prompt (all clips):** `text, signage, letters, logos, watermark, UI, arrows, map interface, phone frame,
  distorted architecture, warped lines, extra floors, melting cars, faces close-up, crowds, night, rain, snow,
  fisheye, oversaturated, cartoon`
- Do **not** ask the model to render readable signs (the "CIMIANO" sign and "M" totem come from real photos and
  graphics). Reject any take with invented lettering.
- Label all output as *AI-generated reconstruction*, not documentary footage.

---

### S01-A — Cimiano sign, macro push (00:00–00:02) · optional
- **Init image:** `IMG_2111_cimiano_platform.jpg`
- **Prompt:** "Slow cinematic push-in toward a green metro station name sign under a concrete platform canopy,
  Milan, overcast daylight, shallow depth of field, a commuter walks out of frame in the background, gentle
  parallax between pillar and trees, subtle film grain."
- **Camera:** dolly-in 10 %, no rotation. **Keep the sign's lettering identical. If it changes, discard the take.**

### S02 — Leaving the metro (00:05–00:10)
- **Init image:** `IMG_4079_cimiano_entrance.jpg` (crop on stairs and red handrails)
- **Prompt:** "First-person point of view climbing the last steps of a granite metro stairwell with red-painted steel
  handrails, emerging to street level in a Milan residential neighbourhood, overcast summer daylight, steady
  gimbal, camera tilts up gently as the street opens up, trees and 1970s apartment blocks ahead, natural motion
  blur."
- **Camera:** forward + tilt up 15°. **AE placeholder:** `AI_S02_exit_stairs`.

### S03-A — Residential Zona 30 street (00:10–00:13)
- **Style reference (not init):** route keyframes 60–80 s (`01_analysis/keyframes_streetview_B.jpg`)
- **Prompt:** "Smooth forward tracking shot along a quiet Milan residential street, 6 to 8 storey 1960s apartment
  blocks with balconies and roller shutters, cars parked on both sides, a low stone balustrade running along the
  left pavement, red-white 30 km/h roundel painted on the asphalt, overcast daylight, documentary realism,
  35 mm."
- **AE placeholder:** `AI_S03a_residential_zona30`

### S03-B — Park fence and trees (00:13–00:15)
- **Prompt:** "Forward walking shot past a small urban park enclosed by a dark green metal railing, mature trees and
  shrubs behind the fence, apartment blocks in the background, Milan, overcast daylight, steady gimbal, gentle
  parallax."
- **AE placeholder:** `AI_S03b_park_fence`

### S03-C — Traffic light at Via Padova (00:15–00:17)
- **Prompt:** "Pedestrian point of view approaching a Milan intersection with a yellow-painted traffic-light pole whose
  arm extends over the road, the signal turns green, zebra crossing in the foreground, trolleybus overhead
  wires above a long straight avenue lined with 7-storey buildings and ground-floor shops, overcast daylight,
  camera pans slightly right to follow the avenue."
- **AE placeholder:** `AI_S03c_trafficlight_ViaPadova`. The "VIA PADOVA" plate is added in AE as graphics, not
  generated.

### Not to be AI-generated
- **S04 map**: motion graphics only.
- **S05 storefront**: the **original photograph only**, with 2.5D moves in AE. Never regenerate it.
- **S06 logo**: the **original logo files only**.
