# QC report: PUNTOCOM_TheWayToUs_1080x1920_30fps.mp4

Verified on the rendered file with `tools/qc_check.sh` (ffprobe, blackdetect, freezedetect, EBU R128).

| Check | Result |
|---|---|
| Container / codec | MP4, H.264 High, yuv420p, `+faststart` ✅ |
| Resolution / aspect | 1080×1920, 9:16 ✅ |
| Frame rate / length | 30 fps, **1050 frames, 35.000 s** ✅ |
| Audio | AAC-LC 48 kHz stereo, 35.000 s, in sync with the picture cue sheet ✅ |
| Loudness | −13.0 LUFS integrated, LRA 10.4 LU, true peak −0.3 dBFS (social / mobile target) ✅ |
| Black frames (≥0.1 s, pix_th 0.06) | **none** ✅. Two 4-frame dips found in v1 (7.2 s, 21.9 s) were removed in v2 |
| Frozen frames (≥0.6 s) | none ✅ |
| File size | 70.8 MB (CRF 19) |
| Correct metro station | CIMIANO, M2 (real photos) ✅ |
| Correct destination | Via Padova 167, Milano: shown in S04, S05 and S06 ✅ |
| Storefront appearance | original photo, only scaled and translated. No graphics over the signs, door or windows. Arabic and Italian signage untouched ✅ |
| Logo integrity | extracted original layers, no redraw, recolour or retype (`01_analysis/logo_alpha_check.jpg`) ✅ |
| Italian spelling | "Sei alla fermata Cimiano della linea M2?", "Raggiungerci è semplicissimo!", "Segui il percorso verso Via Padova…", "…e troverai Puntocom al numero 167.", "CAF, Patronato e tanti servizi per te.", "Via Padova 167 – Milano", "Siamo qui per aiutarti!", "CONTABILITÀ" ✅ |
| Arabic text | none added ✅ |
| Google Street View imagery / UI in picture | none ✅ |
| Invented distances / times / street names | none ✅. The map is labelled "Schema indicativo · non in scala" |
| AI signage errors | n/a. No AI-generated footage is in this master |

## Known limitations (not defects of the file)
1. **No voiceover in this master.** ElevenLabs refused the generation (busy free tier). The subtitles carry the script. See `07_audio/README.md` to add it.
2. **S02–S03 is a stylised procedural 3D street, not photoreal AI footage.** No AI video engine was available. The prompts and AE slots are ready.
3. **The S04 map is schematic.** Map data services were blocked. See `01_analysis/route_analysis.md` §3.

Storyboard frames from this file: `02_storyboard/storyboard_frames.jpg`.
