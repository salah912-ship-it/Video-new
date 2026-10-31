# Fonts (SIL Open Font License 1.1, free for commercial use)

| File | Use |
|---|---|
| `Cairo-Bold.ttf`, `Cairo-ExtraBold.ttf` | Arabic headlines (static instances cut from Google Fonts' variable Cairo with fontTools, wght 700 / 800) |
| `IBMPlexSansArabic-Regular/Medium/SemiBold.ttf` | Arabic supporting text |

Licences: `OFL_Cairo.txt`, `OFL_IBMPlexSansArabic.txt`. Install them before opening or building the AE project.
Arabic in the renders is shaped with HarfBuzz and FriBiDi (Pillow + libraqm). The renderer refuses to run without libraqm,
so disconnected letters or wrong RTL order are not possible.
