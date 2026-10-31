# Audio

| File | Content |
|---|---|
| `puntocom_mix.wav` | 48 kHz / 16-bit stereo master mix (music + SFX), 35.0 s, peak −0.5 dBFS |
| `stems/music.wav` | original score: D-major pad, pluck arpeggio, soft pulse from 7.25 s, sub-bass, reveal chord and gold bells |
| `stems/sfx.wav` | metro ambience, city ambience, whooshes on every cut, GPS pings, reverse swell and logo impact |
| `stems/vo.wav` | empty until a VO is supplied |

Everything is synthesised by `tools/make_audio.py`. No third-party music or samples are used, so there are no licensing issues.
The cue times are shared with the picture: cuts at 1.95 / 5.0 / 7.25 / 16.9 / 21.95 / 28.9 s, pings on each
step card and map pin, and the impact at 29.55 s.

## Italian voiceover: status ⚠️

Voice chosen: **ElevenLabs "Alfio – Voce fresca e moderna"** (Italian male, professional, friendly,
not a hard-sell announcer; `voice_id 3arxYWHh1h73mJX4m0Fi`). The generation request was **refused by
ElevenLabs ("free generations are busy", nothing charged)**, so **the current master has no voiceover**.
The on-screen subtitles carry the script.

Script and cue points (seconds) for the five lines:

| Cue | Line |
|---|---|
| 0.6 | Sei alla fermata Cimiano della linea M2? |
| 5.3 | Raggiungerci è semplicissimo! |
| 10.3 | Segui il percorso verso Via Padova e troverai Puntocom al numero 167. |
| 23.0 | CAF, Patronato e tanti servizi per te. |
| 30.6 | PUNTOCOM. Siamo qui per aiutarti! |

To add the VO once the five line files exist (any sample rate, mono or stereo WAV):

```bash
python3 tools/make_audio.py --vo-lines vo/l1.wav vo/l2.wav vo/l3.wav vo/l4.wav vo/l5.wav   # music ducks −5 dB under VO
ffmpeg -i 08_render/PUNTOCOM_TheWayToUs_1080x1920_30fps.mp4 -i 07_audio/puntocom_mix.wav \
       -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest 08_render/PUNTOCOM_TheWayToUs_VO.mp4
```

Line 3 is the longest (about 4.5 s at a natural pace) and fits its 10.3 → 16.6 s window. Keep each line within its subtitle
window (see `02_storyboard/storyboard.md`).
