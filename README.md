# PUNTOCOM – THE WAY TO US

A 35-second vertical (1080×1920, 30 fps, H.264) cinematic advert for **PUNTOCOM CAF & Patronato,
Via Padova 167, Milano**. The viewer travels from the **Cimiano M2** exit to the real storefront and finishes on the
official logo.

**Final video:** `08_render/PUNTOCOM_TheWayToUs_1080x1920_30fps.mp4`

## Project folder

| Folder | Deliverable |
|---|---|
| `00_assets/` | supplied originals: Cimiano photos, route references, storefront, logo (Street View = reference only) |
| `01_analysis/` | asset inventory, Street View contact sheets and keyframes, **route analysis report**, logo extraction check, audio waveform |
| `02_storyboard/` | full beat-by-beat storyboard and storyboard frames rendered from the final video |
| `03_ai_prompts/` | individual image-to-video prompts per clip, with negative prompt and rules |
| `04_generated/` | generated video assets (programmatic street plate; AI clips pending, see below) |
| `05_aftereffects/scripts/` | **`build_puntocom_project.jsx`**: builds and saves the editable `.aep` |
| `06_motion_graphics/` | transparent logo layers extracted from the official master |
| `07_audio/` | master mix and stems, VO script and cue sheet |
| `08_render/` | final MP4 and QC report |
| `tools/` | `render_video.py` (picture), `make_audio.py` (sound), `extract_logo.py` |

## Rebuild everything

```bash
pip install numpy pillow scipy            # plus ffmpeg on PATH, Inter font installed
python3 tools/extract_logo.py 00_assets/logo/puntocom_logo_master.jpg 06_motion_graphics
python3 tools/make_audio.py               # add --vo-lines l1..l5.wav once VO exists
python3 tools/render_video.py 08_render/PUNTOCOM_TheWayToUs_1080x1920_30fps.mp4 --audio 07_audio/puntocom_mix.wav
python3 tools/render_video.py /tmp/pv --preview 3 12 25 33   # stills for review
```

In After Effects: **File › Scripts › Run Script File… › `05_aftereffects/scripts/build_puntocom_project.jsx`**, then choose
this folder. It creates the 7 compositions (01_METRO_OPENING, 02_STREET_SEQUENCES, 03_GPS_MAP, 04_ROUTE_ANIMATION,
05_STOREFRONT, 06_LOGO_REVEAL, 00_MAIN_1080x1920), with shape layers, Trim Paths, a 3D camera with a null rig, parallax,
masks, motion blur, a grade adjustment layer and a render-queue item. It then saves `05_aftereffects/PUNTOCOM_TheWayToUs.aep`.

## Honest production status

| Item | Status |
|---|---|
| Final MP4 (1080×1920, 30 fps, 35 s, H.264 + AAC) | ✅ rendered and verified (see `08_render/QC_report.md`) |
| Original storefront and logo preserved | ✅ only transformed or masked; logo extracted, not redrawn |
| AI-generated video clips | ❌ **no image-to-video engine is available here**. Scenes 02–03 use an original procedural 3D street. Prompts are ready, and AE placeholders are in place. |
| `.aep` file | ⚠️ After Effects is not installed in this environment. The JSX builds and saves it on any machine with AE. |
| Italian voiceover | ⚠️ ElevenLabs refused the generation (free tier busy, nothing charged). The master has music, SFX and subtitles. The VO slots and ducking are ready (`07_audio/README.md`). |
| Map geographic precision | ⚠️ map data services were blocked. The S04 map is a labelled **schematic** ("non in scala"). There is a one-step upgrade path in `01_analysis/route_analysis.md`. |
