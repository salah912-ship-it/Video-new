# PUNTOCOM – THE WAY TO US · Egyptian Arabic edition

A 35-second vertical (1080×1920, 9:16, 30 fps) advert for **PUNTOCOM CAF & PATRONATO, Via Padova 167, Milano**,
aimed at Egyptians living in Italy. The viewer travels from the **Cimiano M2** exit to the real storefront and ends on the
official logo. All promotional text is natural Egyptian Arabic. Italian place names (Cimiano M2, Via Padova 167, Milano)
and the brand name are unchanged.

**There is no narration in this video, by design.** It is built for the owner's own Egyptian Arabic voiceover, recorded separately.
No AI or synthetic voice was generated.

## Final exports (`08_render/`)

| File | Content |
|---|---|
| `PUNTOCOM_AR_TheWayToUs_SILENT_1080x1920_30fps.mp4` | final promotional video, **no audio track** |
| `PUNTOCOM_AR_TheWayToUs_MUSIC_SFX_noVO_1080x1920_30fps.mp4` | the same picture with music and SFX, **no narration** |

## On-screen text

| Scene | Time | Text |
|---|---|---|
| 1 Cimiano M2 | 2.4–5.0 | نازل محطة Cimiano M2؟ |
| 2 Leaving the metro | 5.3–9.8 | تعالى نوصلك لمكتبنا |
| 3 Street journey | 10.5–16.5 | الطريق أسهل مما تتخيل! (step cards: اطلع من المترو / شوارع سكنية هادية / عند الإشارة: Via Padova) |
| 4 GPS map | 17.4–21.9 | وجهتك Puntocom |
| 5 Arrival | 24.5–28.6 | وصلت! إحنا في انتظارك (chips from the shop's own sign: خدمات الكاف · الباتروناتو · الهجرة والجنسية · المحاسبة) |
| 6 Brand | 29.5–35 | PUNTOCOM CAF PATRONATO (official logo) · Via Padova 167 – Milano · مستنيينك! |

Typography: **Cairo Bold** for headlines and **IBM Plex Sans Arabic** for supporting text. Text is right-to-left with full HarfBuzz shaping.
Reveals wipe from right to left, step cards slide in from the right, and the journey progress rail fills right to left.

## Project folder

| Folder | Deliverable |
|---|---|
| `AUDIO/` | `BACKGROUND_MUSIC.wav`, `SOUND_EFFECTS.wav`, reference mix, **voiceover slot** (`VOICEOVER_OWNER.wav` comes from the owner) and recording guide |
| `05_aftereffects/scripts/build_puntocom_project.jsx` | builds and saves the **editable AE project** `PUNTOCOM_AR_TheWayToUs.aep` with the voiceover-ready comp `00_MAIN_VO_READY_1080x1920` |
| `fonts/` | Cairo and IBM Plex Sans Arabic (OFL) |
| `06_motion_graphics/` | logo layers extracted from the official master (not redrawn) |
| `00_assets/` · `01_analysis/` · `02_storyboard/` · `03_ai_prompts/` | sources, route analysis, storyboard, AI clip prompts |
| `tools/` | `render_video.py` (picture), `make_audio.py` (music/SFX), `extract_logo.py`, `qc_check.sh` |

## After Effects

1. Install the fonts in `fonts/`. On AE older than 24, set Preferences › Type › *South Asian and Middle Eastern* and restart.
2. Optional: copy the owner's recording to `AUDIO/VOICEOVER_OWNER.wav`.
3. File › Scripts › Run Script File… › `build_puntocom_project.jsx`, then choose this folder.

The main comp has three audio tracks, **VOICEOVER_OWNER** (an empty labelled placeholder until the recording exists), **BACKGROUND_MUSIC**
(with a `MUSIC LEVEL dB` slider for dipping under the voice) and **SOUND_EFFECTS**. It also has comp markers for each scene's suggested voiceover window,
and each scene sits on its own precomp layer, so the timing can follow the owner's delivery. Two render-queue items are added: a silent one and one with audio.

## Rebuild from code

```bash
pip install numpy pillow scipy fonttools          # Pillow must have libraqm (Arabic shaping); ffmpeg on PATH
python3 tools/make_audio.py
python3 tools/render_video.py 08_render/PUNTOCOM_AR_TheWayToUs_SILENT_1080x1920_30fps.mp4
ffmpeg -i 08_render/PUNTOCOM_AR_TheWayToUs_SILENT_1080x1920_30fps.mp4 -i AUDIO/MUSIC_SFX_REFERENCE_MIX.wav \
       -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest 08_render/PUNTOCOM_AR_TheWayToUs_MUSIC_SFX_noVO_1080x1920_30fps.mp4
tools/qc_check.sh 08_render/PUNTOCOM_AR_TheWayToUs_SILENT_1080x1920_30fps.mp4
```

## Production status

| Item | Status |
|---|---|
| Silent master and music+SFX master (1080×1920, 30 fps, 35 s) | ✅ rendered and verified, see `08_render/QC_report.md` |
| Arabic typography (Cairo / IBM Plex Sans Arabic, RTL, shaped) | ✅ |
| Owner voiceover | ⏳ waiting for the owner's recording. The track and markers are ready, and nothing synthetic was created. |
| `.aep` file | ⚠️ After Effects is not available in this build environment. The JSX creates and saves the `.aep` on any machine with AE. |
| AI video clips | ❌ no AI video engine was available. Scenes 2–3 use an original procedural 3D street. The prompts are in `03_ai_prompts/`. |
| Map | ⚠️ schematic and labelled as such ("رسم توضيحي · مش بمقياس رسم"), because map data services were blocked. See `01_analysis/route_analysis.md`. |
