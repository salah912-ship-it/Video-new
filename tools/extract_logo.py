"""Extract the official Puntocom logo onto transparency WITHOUT redrawing it.

The master JPG sits on a flat navy field (RGB 12,22,32). We un-premultiply
against that colour: P = a*F + (1-a)*B  ->  alpha from max channel distance,
F = B + (P-B)/a. Original pixels/colours/typography are preserved; only the
navy field becomes transparent. Also splits it into reveal layers by row bands.
"""
import sys, numpy as np
from PIL import Image
src, out = sys.argv[1], sys.argv[2]
P = np.asarray(Image.open(src).convert('RGB')).astype(np.float32)
B = np.array([12, 22, 32], np.float32)
d = np.abs(P - B).max(2)
a = np.clip((d - 10) / 90.0, 0, 1)            # 10 = jpeg noise/world-map dots floor
F = B + (P - B) / np.maximum(a, 1e-3)[..., None]
F = np.clip(F, 0, 255)
rgba = np.dstack([F, a * 255]).astype(np.uint8)
full = Image.fromarray(rgba, 'RGBA')
full.save(f'{out}/puntocom_logo_full_alpha.png')
bands = {'symbol': (90, 390), 'wordmark': (392, 480), 'subline': (480, 525)}
for k, (y0, y1) in bands.items():
    layer = np.zeros_like(rgba); layer[y0:y1] = rgba[y0:y1]
    Image.fromarray(layer, 'RGBA').save(f'{out}/puntocom_logo_{k}.png')
print('ok', full.size)
