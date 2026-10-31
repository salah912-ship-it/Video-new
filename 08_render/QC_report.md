# QC report: Egyptian Arabic edition

Verified on the rendered files with `tools/qc_check.sh` (ffprobe, blackdetect, freezedetect, EBU R128), plus visual inspection
of full-resolution frames (`02_storyboard/storyboard_frames.jpg` comes from the silent master).

| Check | `…_SILENT_…mp4` | `…_MUSIC_SFX_noVO_…mp4` |
|---|---|---|
| Codec | H.264 High, yuv420p, faststart | same |
| Resolution / aspect | 1080×1920, 9:16 | same |
| Frame rate / length | 30 fps, 1050 frames, 35.000 s | same |
| Audio | **none (no audio stream)** ✅ | AAC 48 kHz stereo, 35.000 s, **no narration** ✅ |
| Loudness | — | −20.2 LUFS integrated, peak −6.0 dBFS (room for the owner's voice) |
| Black frames (≥0.1 s) | none ✅ | none ✅ |
| Frozen frames (≥0.6 s) | none ✅ | none ✅ |
| Size | 68.8 MB | 69.9 MB |

| Content check | Result |
|---|---|
| Arabic shaping and RTL | ✅ HarfBuzz/FriBiDi via libraqm (the renderer refuses to run without it). Letters are joined, mixed Arabic/Latin order is correct, the shadda (كمّل) renders, and "؟" is used for the Arabic question. |
| Fonts | ✅ Cairo Bold for headlines. IBM Plex Sans Arabic for supporting text and chips. Inter only for Latin place labels. |
| Scene texts | ✅ exactly as briefed: نازل محطة Cimiano M2؟ / تعالى نوصلك لمكتبنا / الطريق أسهل مما تتخيل! / وجهتك Puntocom / وصلت! إحنا في انتظارك / PUNTOCOM CAF PATRONATO (official logo) · Via Padova 167 – Milano · مستنيينك! |
| Italian names unchanged | ✅ Cimiano M2, Via Padova 167, Milano, PUNTOCOM CAF PATRONATO |
| No Italian narration or Italian promo text | ✅ |
| No synthetic or AI voice, no fake VO file | ✅ (`AUDIO/VOICEOVER_OWNER.wav` intentionally absent) |
| Storefront integrity | ✅ original photo, only scaled and translated. Text is in the plate bands only. |
| Logo integrity | ✅ original extracted layers |
| No Street View imagery or UI | ✅ |
| No invented distances or street names | ✅. The map is labelled "رسم توضيحي · مش بمقياس رسم" |

Not verifiable here: the `.aep` itself. After Effects is not installed, so `build_puntocom_project.jsx` was syntax-checked only.
Run it once in AE (see README) to produce and check the project.
