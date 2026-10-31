#!/usr/bin/env python3
"""PUNTOCOM - THE WAY TO US :: Egyptian-Arabic edition, programmatic render (1080x1920, 30 fps, 35 s).

No narration: the picture is voiceover-ready for the owner's own Egyptian Arabic recording.
Arabic text is shaped with HarfBuzz/FriBiDi (Pillow + libraqm), RTL, Cairo Bold + IBM Plex Sans Arabic.

This is the deliverable render built without After Effects (not installed in the
production environment). It mirrors the storyboard / AE precomp structure 1:1:

  S01 Cimiano M2            00:00-00:05   real photos, 2.5D push / pull
  S02 Leaving the metro     00:05-00:10   real photo card -> emergence into route
  S03 Street journey        00:07-00:17   procedural 3D "navigation mode" street
  S04 GPS map               00:17-00:22   3D-tilted schematic map, trim-path route
  S05 Arrival at Puntocom   00:22-00:29   ORIGINAL storefront photo, 2.5D push-in
  S06 Brand reveal          00:29-00:35   ORIGINAL logo layers on navy

Usage:  python3 tools/render_video.py OUT.mp4 [--preview SECONDS...] [--workers N]
"""
import math, os, sys, random, subprocess, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = lambda *p: os.path.join(ROOT, *p)
W, H, FPS, DUR = 1080, 1920, 30, 35.0

# ---------------------------------------------------------------- identity
ORANGE = (245, 130, 32)          # #F58220 journey
BLACK = (17, 17, 17)             # #111111
WHITE = (255, 255, 255)
NAVY = (12, 22, 32)              # sampled from official logo field
GOLD = (201, 151, 74)            # sampled from official logo gold
M2GREEN = (0, 150, 64)

FD = '/usr/share/fonts/opentype/inter/'
_fc = {}
def font(name, size):
    k = (name, int(size))
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FD + name + '.otf', int(size))
    return _fc[k]

AFD = os.path.join(ROOT, 'fonts') + '/'
from PIL import features as _feat
assert _feat.check('raqm'), 'libraqm is required for correct Arabic shaping/RTL'
def afont(name, size):
    """Arabic fonts: Cairo-Bold (headlines), IBMPlexSansArabic-* (supporting text). RAQM layout = HarfBuzz shaping."""
    k = ('ar', name, int(size))
    if k not in _fc:
        _fc[k] = ImageFont.truetype(AFD + name + '.ttf', int(size), layout_engine=ImageFont.Layout.RAQM)
    return _fc[k]
def ar(d, xy, s, f, fill, anchor='mm'):
    d.text(xy, s, font=f, fill=fill, anchor=anchor, direction='rtl', language='ar')
def ar_len(s, f):
    return f.getlength(s, direction='rtl', language='ar')

# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def seg(t, a, b): return clamp((t - a) / (b - a))
def lerp(a, b, x): return a + (b - a) * x
def e_io(x): x = clamp(x); return x * x * (3 - 2 * x)
def e_io5(x): x = clamp(x); return x * x * x * (x * (6 * x - 15) + 10)
def e_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def e_expo(x): x = clamp(x); return 1 if x >= 1 else 1 - 2 ** (-10 * x)
def e_in(x): x = clamp(x); return x ** 3
def win(t, a, b, fi=0.35, fo=0.35):
    return clamp(min(seg(t, a, a + fi), 1 - seg(t, b - fo, b)))

# ---------------------------------------------------------------- assets
def load(p, mode='RGB'): return Image.open(A(p)).convert(mode)
IMG_PLATFORM = load('00_assets/cimiano/IMG_2111_cimiano_platform.jpg')
IMG_ENTR = load('00_assets/cimiano/IMG_4079_cimiano_entrance.jpg')
IMG_ENTR2 = load('00_assets/cimiano/IMG_4081_cimiano_entrance_wide.jpg')
IMG_STORE = load('00_assets/storefront/puntocom_storefront_original.jpg')
LOGO = {k: load(f'06_motion_graphics/puntocom_logo_{k}.png', 'RGBA')
        for k in ('symbol', 'wordmark', 'subline')}
STORE_BG = IMG_STORE.resize((589, 410), Image.BILINEAR).filter(ImageFilter.GaussianBlur(18))
ENTR2_BG = IMG_ENTR2.filter(ImageFilter.GaussianBlur(14))

# vignette + grade helpers
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_r = np.sqrt(((_xx - W / 2) / (W * 0.72)) ** 2 + ((_yy - H / 2) / (H * 0.62)) ** 2)
VIG = np.clip(1 - 0.55 * np.clip(_r - 0.45, 0, 1) ** 1.6, 0, 1)[..., None]

def grade(im, t, strength=1.0, grain=True):
    a = np.asarray(im).astype(np.float32) / 255.0
    # filmic: gentle S-curve, cool shadows / warm highlights
    a = a + strength * 0.06 * np.sin((a - 0.5) * math.pi)  # contrast
    lum = a.mean(2, keepdims=True)
    tint = np.concatenate([lum * 0.03 - 0.012, lum * 0.0, (1 - lum) * 0.025], 2)
    a = a + strength * tint
    a = a * (VIG * strength + (1 - strength))
    if grain:
        rng = np.random.default_rng(int(t * FPS) + 7)
        g = rng.normal(0, 0.012, (H // 2, W // 2, 1)).astype(np.float32)
        a = a + np.repeat(np.repeat(g, 2, 0), 2, 1)
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))

def place(img, scale, cx, cy, size=(W, H), rot=0.0):
    """Render `img` scaled by `scale`, image point (cx,cy) at frame centre."""
    sw, sh = size
    if rot == 0:
        d = (1 / scale, 0, cx - sw / 2 / scale, 0, 1 / scale, cy - sh / 2 / scale)
    else:
        c, s = math.cos(rot), math.sin(rot)
        a, b, dd, e = c / scale, s / scale, -s / scale, c / scale
        d = (a, b, cx - a * sw / 2 - b * sh / 2, dd, e, cy - dd * sw / 2 - e * sh / 2)
    return img.transform(size, Image.AFFINE, d, resample=Image.BICUBIC)

def to_screen(px, py, scale, cx, cy):
    return (W / 2 + (px - cx) * scale, H / 2 + (py - cy) * scale)

def add(base, layer):  # additive (screen-ish) blend
    return ImageChops.add(base, layer)

def glow_layer(draw_fn, radius=18, strength=1.0, ss=1):
    L = Image.new('RGB', (W * ss, H * ss), (0, 0, 0))
    draw_fn(ImageDraw.Draw(L), ss)
    if ss > 1: L = L.resize((W, H), Image.LANCZOS)
    g = L.filter(ImageFilter.GaussianBlur(radius))
    if strength != 1.0:
        g = Image.fromarray(np.clip(np.asarray(g).astype(np.float32) * strength, 0, 255).astype(np.uint8))
    return add(L, g)

def text_tracked(d, xy, s, f, fill, track=0, anchor='mm'):
    """Draw text with letter-spacing (tracking in px). anchor: 'mm','lm','rm'."""
    widths = [f.getlength(ch) for ch in s]
    total = sum(widths) + track * (len(s) - 1)
    x, y = xy
    if anchor[0] == 'm': x -= total / 2
    elif anchor[0] == 'r': x -= total
    for ch, w in zip(s, widths):
        d.text((x, y), ch, font=f, fill=fill, anchor='lm')
        x += w + track
    return total

def overlay_rgba(base, ov):
    b = base.convert('RGBA'); b.alpha_composite(ov); return b.convert('RGB')

def fade(img, k, col=(0, 0, 0)):
    if k >= 1: return img
    return Image.blend(Image.new('RGB', img.size, col), img, clamp(k))

# ---------------------------------------------------------------- shared UI
def headline(ov, t, a, b, text, y=1600, size=84, col=WHITE, plate=True):
    """Scene headline in Egyptian Arabic. Revealed right-to-left (reading direction)."""
    k = win(t, a, b, 0.5, 0.35)
    if k <= 0: return
    ke = e_out(seg(t, a, a + 0.8))
    f = afont('Cairo-Bold', size)
    tw = ar_len(text, f)
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    yy = y + (1 - ke) * 26
    if plate:
        d.rounded_rectangle((W / 2 - tw / 2 - 42, yy - size * 0.78, W / 2 + tw / 2 + 42, yy + size * 0.78), 22,
                            fill=(17, 17, 17, 175))
    ar(d, (W / 2, yy), text, f, col + (255,))
    lw = (tw + 84) * e_out(seg(t, a + 0.25, a + 1.0))
    d.rectangle((W / 2 + tw / 2 + 42 - lw, yy + size * 0.78 - 6, W / 2 + tw / 2 + 42, yy + size * 0.78), fill=ORANGE + (255,))
    # RTL wipe: soft edge travels from the right edge of the text to the left
    edge = lerp(W / 2 + tw / 2 + 60, W / 2 - tw / 2 - 120, e_out(seg(t, a, a + 0.75)))
    xs = np.arange(W, dtype=np.float32)
    ramp_ = np.clip((xs - edge) / 60.0, 0, 1) * k
    al = np.asarray(L.getchannel('A')).astype(np.float32) * ramp_[None, :]
    L.putalpha(Image.fromarray(al.astype(np.uint8)))
    ov.alpha_composite(L)

def wrap(text, f, maxw):
    words, lines, cur = text.split(), [], ''
    for w_ in words:
        tst = (cur + ' ' + w_).strip()
        if f.getlength(tst) > maxw and cur:
            lines.append(cur); cur = w_
        else:
            cur = tst
    lines.append(cur)
    return lines

def step_card(ov, t, a, b, num, title, sub=None, y=250):
    """Wayfinding card, RTL layout: number badge on the right, slides in from the right."""
    k = win(t, a, b, 0.45, 0.35)
    if k <= 0: return
    ke = e_expo(seg(t, a, a + 0.6))
    d = ImageDraw.Draw(ov)
    ft, fs = afont('Cairo-Bold', 50), afont('IBMPlexSansArabic-Medium', 34)
    tw = max(ar_len(title, ft), ar_len(sub, fs) if sub else 0)
    w_ = tw + 190
    x1 = W - 70 + (1 - ke) * 80
    hh = 160 if sub else 115
    al = int(255 * k)
    d.rounded_rectangle((x1 - w_ * (0.3 + 0.7 * ke), y, x1, y + hh), 26, fill=(17, 17, 17, int(215 * k)))
    d.rounded_rectangle((x1 - 10, y, x1, y + hh), 5, fill=ORANGE + (al,))
    cx, cy = x1 - 75, y + hh / 2
    d.ellipse((cx - 34, cy - 34, cx + 34, cy + 34), fill=ORANGE + (al,))
    d.text((cx, cy + 1), '١٢٣'[num - 1], font=afont('Cairo-Bold', 42), fill=(17, 17, 17, al), anchor='mm')
    if ke > 0.35:
        ka = int(al * seg(ke, 0.35, 1))
        ar(d, (x1 - 135, y + (50 if sub else hh / 2)), title, ft, (255, 255, 255, ka), anchor='rm')
        if sub:
            ar(d, (x1 - 135, y + 112), sub, fs, (255, 200, 150, ka), anchor='rm')

def progress_rail(ov, t):
    """Thin journey progress rail, filling right-to-left (Arabic reading direction), 0..29 s."""
    if t > 29.2: return
    k = win(t, 0.4, 29.2, 0.5, 0.4)
    d = ImageDraw.Draw(ov)
    p = seg(t, 0.4, 28.6)
    x = W - 60 - (W - 120) * p
    d.rectangle((60, 92, W - 60, 96), fill=(255, 255, 255, int(60 * k)))
    d.rectangle((x, 92, W - 60, 96), fill=ORANGE + (int(255 * k),))
    d.ellipse((x - 9, 85, x + 9, 103), fill=ORANGE + (int(255 * k),))
    f = font('Inter-SemiBold', 24)
    d.text((W - 60, 125), 'Cimiano M2', font=f, fill=(255, 255, 255, int(200 * k)), anchor='rm')
    d.text((60, 125), 'Via Padova 167', font=f, fill=(255, 255, 255, int(200 * k)), anchor='lm')

# ================================================================ S01 CIMIANO
def s01(t):
    if t < 2.05:
        # platform sign close-up (IMG_2111, native 9:16)
        p = e_io(seg(t, 0, 2.05))
        s = lerp(1.80, 2.05, p)
        im = place(IMG_PLATFORM, s, lerp(400, 420, p), lerp(330, 300, p))
    else:
        # entrance: tight on CIMIANO sign -> pull back & tilt to stairs + red rails
        p = e_io5(seg(t, 2.05, 5.4))
        s = lerp(2.75, 1.90, p)
        im = place(IMG_ENTR, s, lerp(517, 560, p), lerp(560, 640, p))
    im = grade(im, t)
    # whip transition 1.85-2.25: orange light streak + flash
    k = 1 - abs(seg(t, 1.8, 2.3) * 2 - 1)
    if 1.8 < t < 2.3:
        im = Image.blend(im, im.filter(ImageFilter.BoxBlur(20)), k)
        st = Image.new('RGB', (W, H)); d = ImageDraw.Draw(st)
        x = lerp(-400, W + 400, seg(t, 1.8, 2.3))
        d.polygon([(x - 120, 0), (x + 60, 0), (x - 60, H), (x - 240, H)], fill=ORANGE)
        im = add(im, st.filter(ImageFilter.GaussianBlur(60)))
    im = fade(im, seg(t, 0, 0.5))
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ks = win(t, 2.3, 5.1, 0.6, 0.3)
    if ks > 0:
        sc = np.zeros((H, W, 4), np.uint8)
        sc[..., 3] = (np.clip(1 - np.linspace(0, 1, H) / 0.42, 0, 1) ** 1.5 * 190 * ks).astype(np.uint8)[:, None]
        ov.alpha_composite(Image.fromarray(sc, 'RGBA'))
    # Scene 1 headline
    headline(ov, t, 2.4, 5.0, 'نازل محطة Cimiano M2؟', y=430, size=82, plate=False)
    progress_rail(ov, t)
    return overlay_rgba(im, ov)

# ================================================================ S02 LEAVING
def s02_card(t):
    """5.0-7.4  real exit photo as a floating card, camera dives into the stairs."""
    p = seg(t, 4.85, 7.4)
    bg = place(ENTR2_BG, 4.6 + p * 0.4, 228, 230)
    bg = Image.blend(Image.new('RGB', (W, H), BLACK), bg, 0.45)
    dive = e_in(seg(t, 6.55, 7.4))                       # final push into stair opening
    s = lerp(2.05, 2.25, e_io(seg(t, 4.85, 6.55))) * (1 + dive * 5.5)
    cx, cy = lerp(228, 228, p), lerp(225, 300, dive)     # stairs opening ~ (228,300)
    card = place(IMG_ENTR2, s, cx, cy, size=(int(457 * 2.05), int(437 * 2.05 * 1.25)))
    # rounded mask
    m = Image.new('L', card.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, card.size[0] - 1, card.size[1] - 1), int(36 * (1 - dive)), fill=255)
    # card grows to full frame during the dive
    gw = int(lerp(card.size[0], W * 1.02, dive)); gh = int(lerp(card.size[1], H * 1.02, dive))
    card = card.resize((gw, gh), Image.BICUBIC); m = m.resize((gw, gh))
    ox, oy = (W - gw) // 2, int((H - gh) // 2 - 40 * (1 - dive))
    sh = Image.new('L', (W, H), 0)
    ImageDraw.Draw(sh).rounded_rectangle((ox + 10, oy + 30, ox + gw + 10, oy + gh + 30), 40, fill=170)
    bg.paste((0, 0, 0), (0, 0), sh.filter(ImageFilter.GaussianBlur(30)))
    bg.paste(card, (ox, oy), m)
    im = grade(bg, t)
    im = fade(im, 1 - seg(t, 7.05, 7.4) * 0.6)           # into the stairwell (never full black)
    im = fade(im, seg(t, 4.85, 5.15) * 0.8 + 0.2)
    return im

# ================================================================ S03 STREET (procedural 3D)
rng = random.Random(167)
def _mk_buildings():
    B = []
    for side in (-1, 1):
        z = -10.0
        while z < 230:
            ln = rng.uniform(11, 22)
            z1, z2 = z, z + ln
            if z1 < 92 < z2 + 6 and z1 < 80:          # intersection gap (Via Padova crossing)
                z2 = min(z2, 78.0)
            if 78 <= z1 < 92: z1 = 92.0; z2 = z1 + ln
            if side == -1 and (34 < z2 and z1 < 62):     # park with fence on the left
                if z1 < 34: z2 = 34.0
                else: z = 62.0; continue
            if z2 > z1 + 3:
                B.append(dict(side=side, z1=z1, z2=z2, h=rng.choice([15, 18, 18, 21, 21, 24, 27]),
                              x=side * rng.uniform(8.0, 8.6), tone=rng.uniform(0.85, 1.15),
                              shop=[rng.random() < 0.55 for _ in range(12)],
                              lit=[rng.random() for _ in range(400)]))
            z = z2 + rng.choice([0, 0, 0, 0.6])
    return B
BUILD = _mk_buildings()
TREES = [(-rng.uniform(9.5, 15), rng.uniform(36, 61), rng.uniform(3.2, 4.8), rng.uniform(6, 9)) for _ in range(16)] + \
        [(rng.choice([-1, 1]) * rng.uniform(6.6, 7.0), z, 1.6, 4.8) for z in (102, 124, 146)]
TREES.sort(key=lambda q: -q[1])

class Cam:
    def __init__(s, x, y, z, f, hor, ss):
        s.x, s.y, s.z, s.f, s.hor, s.ss = x, y, z, f * ss, hor * ss, ss
    def p(s, X, Y, Z):
        zr = Z - s.z
        return (W * s.ss / 2 + s.f * (X - s.x) / zr, s.hor - s.f * (Y - s.y) / zr)

NEAR = 0.6
def clip_poly(cam, pts):
    out = []
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        ia, ib = a[2] - cam.z >= NEAR, b[2] - cam.z >= NEAR
        if ia: out.append(a)
        if ia != ib:
            u = (cam.z + NEAR - a[2]) / (b[2] - a[2])
            out.append(tuple(a[k] + (b[k] - a[k]) * u for k in range(3)))
    if len(out) < 3: return None
    return [cam.p(*q) for q in out]

def fogc(col, z, cam, sky=(70, 52, 42)):
    k = clamp(math.exp(-(z - cam.z) / 95.0), 0, 1)
    return tuple(int(sky[i] + (col[i] - sky[i]) * k) for i in range(3))

def street_frame(t, ss=2):
    tt = t - 7.2
    speed = 8.6
    camz = -6 + tt * speed - 0.9 * math.sin(clamp(tt / 9.8) * math.pi)  # gentle ease
    emerge = e_out(seg(t, 7.2, 8.6))
    cam = Cam(2.6 + 0.08 * math.sin(tt * 2.3), lerp(0.35, 1.65, emerge) + 0.04 * math.sin(tt * 4.6),
              camz, 980, 900 + 140 * (1 - emerge), ss)
    S = W * ss; HH = H * ss
    im = Image.new('RGB', (S, HH))
    d = ImageDraw.Draw(im)
    # sky gradient + vanishing-point warmth
    hor = int(cam.hor)
    for i in range(0, hor, 8):
        k = i / max(hor, 1)
        c = (int(lerp(16, 92, k ** 2.2)), int(lerp(20, 62, k ** 2.2)), int(lerp(30, 46, k ** 2.2)))
        d.rectangle((0, i, S, i + 8), fill=c)
    d.rectangle((0, hor, S, HH), fill=(26, 26, 29))
    polys = []  # (depth, poly3d, fill, outline)
    def Q(pts, fill, outline=None, depth=None, width=1):
        dz = depth if depth is not None else max(p[2] for p in pts)
        polys.append((dz, pts, fill, outline, width))
    zf = cam.z + 170
    zn = cam.z
    # ground: road, sidewalks, kerbs
    Q([(-20, 0, zn), (20, 0, zn), (20, 0, zf), (-20, 0, zf)], (28, 28, 31), depth=1e9)
    for sx in (-1, 1):
        Q([(sx * 4.6, 0.01, zn), (sx * 8.4, 0.01, zn), (sx * 8.4, 0.01, zf), (sx * 4.6, 0.01, zf)], (44, 44, 48), depth=1e8)
        Q([(sx * 4.55, 0.02, zn), (sx * 4.7, 0.02, zn), (sx * 4.7, 0.02, zf), (sx * 4.55, 0.02, zf)], (120, 120, 125), depth=1e8 - 1)
    # centre dashes
    z0 = math.floor(zn / 6) * 6
    for z in np.arange(z0, zf, 6):
        if 70 < z < 92: continue
        Q([(-0.08, 0.02, z), (0.08, 0.02, z), (0.08, 0.02, z + 3), (-0.08, 0.02, z + 3)], (150, 150, 150), depth=1e8 - 2)
    # crosswalk at the Via Padova intersection
    for i in range(7):
        x = -4.4 + i * 1.3
        Q([(x, 0.03, 73), (x + 0.65, 0.03, 73), (x + 0.65, 0.03, 77), (x, 0.03, 77)], (205, 205, 205), depth=1e8 - 3)
    # "30" zone road marking
    for j in range(24):
        a0, a1 = j / 24 * 2 * math.pi, (j + 1) / 24 * 2 * math.pi
        for r0, r1, col in ((1.25, 1.55, (200, 40, 40)),):
            Q([(1.9 + r0 * math.cos(a0), 0.03, 32 + r0 * math.sin(a0) * 1.4), (1.9 + r1 * math.cos(a0), 0.03, 32 + r1 * math.sin(a0) * 1.4),
               (1.9 + r1 * math.cos(a1), 0.03, 32 + r1 * math.sin(a1) * 1.4), (1.9 + r0 * math.cos(a1), 0.03, 32 + r0 * math.sin(a1) * 1.4)],
              col, depth=1e8 - 4)
    # buildings
    for b in BUILD:
        if b['z2'] < zn or b['z1'] > zf: continue
        x, h, s = b['x'], b['h'], b['side']
        base = tuple(int(c * b['tone']) for c in (56, 54, 58))
        Q([(x, 0, b['z1']), (x, h, b['z1']), (x, h, b['z2']), (x, 0, b['z2'])], base, (60, 60, 66), depth=b['z2'] + 0.5)
        # end walls (visible across gaps)
        for ze in (b['z1'], b['z2']):
            Q([(x, 0, ze), (x + s * 14, 0, ze), (x + s * 14, h, ze), (x, h, ze)], tuple(int(c * 0.7) for c in base), (50, 50, 55), depth=ze + 0.4)
        # windows & ground-floor shops
        nc = int((b['z2'] - b['z1']) / 2.4)
        for ci in range(nc):
            za = b['z1'] + 0.7 + ci * 2.4
            if za + 1.2 > b['z2']: break
            if za + 1.2 < zn + NEAR or za > zf: continue
            if b['shop'][ci % 12]:
                Q([(x - s * 0.01, 0.2, za - 0.4), (x - s * 0.01, 2.6, za - 0.4), (x - s * 0.01, 2.6, za + 1.6), (x - s * 0.01, 0.2, za + 1.6)],
                  (150, 112, 70) if ci % 3 else (100, 108, 118), depth=za + 0.1)
            for fl in range(1, int(h / 3)):
                y0 = fl * 3 + 0.8
                lit = b['lit'][(ci * 13 + fl) % 400]
                col = (84, 88, 98) if lit > 0.22 else (196, 146, 86)
                Q([(x - s * 0.01, y0, za), (x - s * 0.01, y0 + 1.5, za), (x - s * 0.01, y0 + 1.5, za + 1.2), (x - s * 0.01, y0, za + 1.2)], col, depth=za + 0.05)
    # park fence (left, 34..62)
    for z in np.arange(34, 62, 0.8):
        if z < zn + NEAR: continue
        Q([(-8.3, 0, z), (-8.3, 1.4, z), (-8.3, 1.4, z + 0.08), (-8.3, 0, z + 0.08)], (40, 120, 70), depth=z)
    Q([(-8.3, 1.35, 34), (-8.3, 1.45, 34), (-8.3, 1.45, 62), (-8.3, 1.35, 62)], (40, 120, 70), depth=62)
    Q([(-8.4, 0.02, 34), (-30, 0.02, 34), (-30, 0.02, 62), (-8.4, 0.02, 62)], (22, 40, 28), depth=1e8 - 5)
    # sort & draw buildings/ground
    polys.sort(key=lambda q: -q[0])
    for dz, pts, fill, outl, wdt in polys:
        pp = clip_poly(cam, pts)
        if not pp: continue
        zz = min(p[2] for p in pts) if dz > 1e7 else dz
        d.polygon(pp, fill=fogc(fill, max(zz, cam.z + 1), cam) if dz < 1e7 else fill,
                  outline=fogc(outl, zz, cam) if outl else None)
    # billboards (camera-facing): trees, signs, totem, traffic light
    def bb_rect(X, Y0, Y1, Z, wdt, fill):
        if Z - cam.z < NEAR: return None
        a = cam.p(X - wdt / 2, Y1, Z); b = cam.p(X + wdt / 2, Y0, Z)
        d.rectangle((a[0], a[1], b[0], b[1]), fill=fogc(fill, Z, cam)); return a, b
    items = []
    for (tx, tz, r, th) in TREES: items.append((tz, 'tree', (tx, tz, r, th)))
    items += [(10, 'metro', None), (30, 'z30', None), (74, 'light', None), (90, 'plate', None)]
    items.sort(key=lambda q: -q[0])
    for z, kind, prm in items:
        if z - cam.z < NEAR or z > zf: continue
        if kind == 'tree':
            tx, tz, r, th = prm
            bb_rect(tx, 0, th - r, tz, 0.35, (52, 40, 30))
            c = cam.p(tx, th, tz); rr = cam.f * r / (tz - cam.z)
            d.ellipse((c[0] - rr, c[1] - rr * 1.1, c[0] + rr, c[1] + rr * 1.1), fill=fogc((30, 70, 44), tz, cam), outline=fogc((52, 110, 70), tz, cam))
        elif kind == 'metro':        # red "M" totem at the Cimiano exit
            bb_rect(-6.4, 0, 3.4, 10, 0.18, (120, 120, 125))
            r = bb_rect(-6.4, 3.4, 4.6, 10, 1.2, (210, 35, 30))
            if r:
                (a, b) = r; fs = int((b[1] - a[1]) * 0.85)
                if fs > 6: d.text(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), 'M', font=font('Inter-Black', fs), fill=(255, 255, 255), anchor='mm')
        elif kind == 'z30':          # "zona 30" sign
            bb_rect(6.0, 0, 2.6, 30, 0.12, (150, 150, 155))
            r = bb_rect(6.0, 2.6, 3.9, 30, 0.95, (235, 235, 235))
            if r:
                (a, b) = r; cx_, cy_ = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + (b[1] - a[1]) * 0.1; rr = (b[0] - a[0]) * 0.36
                d.ellipse((cx_ - rr, cy_ - rr, cx_ + rr, cy_ + rr), outline=(205, 30, 30), width=max(1, int(rr * 0.22)))
                if rr > 5: d.text((cx_, cy_), '30', font=font('Inter-Black', int(rr * 0.95)), fill=(20, 20, 20), anchor='mm')
                if rr > 5: d.text((cx_, a[1] + (b[1] - a[1]) * 0.12), 'zona', font=font('Inter-Bold', int(rr * 0.5)), fill=(20, 20, 20), anchor='mm')
        elif kind == 'light':        # Milan yellow traffic-light pole with arm over the road
            bb_rect(4.9, 0, 5.4, 74, 0.22, (225, 180, 40))
            a = cam.p(4.9, 5.4, 74); b = cam.p(0.4, 5.25, 74)
            if 74 - cam.z > NEAR:
                d.line((a, b), fill=fogc((225, 180, 40), 74, cam), width=max(1, int(cam.f * 0.16 / (74 - cam.z))))
                r = bb_rect(0.4, 4.0, 5.3, 74, 0.45, (20, 40, 30))
                if r:
                    (p1, p2) = r; cx_ = (p1[0] + p2[0]) / 2; rr = (p2[0] - p1[0]) * 0.33
                    gy = p2[1] - (p2[1] - p1[1]) * 0.18
                    d.ellipse((cx_ - rr, gy - rr, cx_ + rr, gy + rr), fill=(80, 255, 140))
        elif kind == 'plate':        # street plate on the corner building
            r = bb_rect(-7.6, 3.2, 3.9, 92, 2.6, (238, 238, 232))
            if r:
                (a, b) = r; fs = int((b[1] - a[1]) * 0.55)
                if fs > 5: d.text(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), 'VIA PADOVA', font=font('Inter-Bold', fs), fill=(25, 25, 25), anchor='mm')
    im = im.resize((W, H), Image.LANCZOS)
    # ------- orange route ribbon on the right sidewalk, with moving chevrons (glow layer)
    def route(dr, s_):
        c2 = Cam(cam.x, cam.y, cam.z, 980, cam.hor / cam.ss, s_)
        pts = []
        for z in np.arange(max(cam.z + NEAR + 0.2, -6), min(cam.z + 140, 90), 0.8):
            x = 6.3 if z < 74 else lerp(6.3, 5.0, seg(z, 74, 84))
            pts.append(c2.p(x, 0.04, z))
        if len(pts) > 1:
            for i in range(len(pts) - 1):
                z = cam.z + NEAR + 0.2 + i * 0.8
                wdt = max(2, int(s_ * 980 * 0.22 / max(z - cam.z, 0.6)))
                dr.line((pts[i], pts[i + 1]), fill=ORANGE, width=wdt)
        # chevrons
        ph = (t * 9) % 4
        for z in np.arange(math.floor(cam.z / 4) * 4 + ph, min(cam.z + 60, 88), 4):
            if z - cam.z < 1.5: continue
            x = 6.3 if z < 74 else lerp(6.3, 5.0, seg(z, 74, 84))
            a = c2.p(x - 0.5, 0.05, z); b = c2.p(x, 0.05, z + 0.7); c = c2.p(x + 0.5, 0.05, z)
            dr.line((a, b, c), fill=(255, 220, 180), width=max(1, int(s_ * 980 * 0.1 / (z - cam.z))))
    k_route = seg(t, 7.6, 8.6)
    if k_route > 0:
        gl = glow_layer(route, 14, 1.2)
        im = add(im, Image.fromarray((np.asarray(gl).astype(np.float32) * k_route).astype(np.uint8)))
    return im

def s03(t):
    im = street_frame(t)
    # motion-blur feel: subtle radial streak at speed
    im = grade(im, t, 0.8)
    im = fade(im, 0.4 + 0.6 * seg(t, 7.2, 7.9))
    # end: crane-up / zoom transition into the map (16.4-17.0)
    k = seg(t, 16.4, 17.05)
    if k > 0:
        z = 1 + e_in(k) * 0.6
        im = place(im, z, W / 2, H / 2 - 200 * e_in(k))
        im = Image.blend(im, im.filter(ImageFilter.GaussianBlur(14)), e_in(k))
        im = fade(im, 1 - e_in(k) * 0.85, (10, 10, 12))
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    step_card(ov, t, 7.6, 10.3, 1, 'اطلع من المترو', 'محطة Cimiano M2', y=230)
    step_card(ov, t, 10.5, 13.4, 2, 'شوارع سكنية هادية', 'Zona 30 · جنب الجنينة', y=230)
    step_card(ov, t, 13.6, 16.6, 3, 'عند الإشارة: Via Padova', 'كمّل لحد رقم 167', y=230)
    headline(ov, t, 5.3, 9.8, 'تعالى نوصلك لمكتبنا')
    headline(ov, t, 10.5, 16.5, 'الطريق أسهل مما تتخيل!')
    progress_rail(ov, t)
    return overlay_rgba(im, ov)

# ================================================================ S04 MAP (schematic)
MS = 2400                                  # map canvas (px)
# Schematic positions (NOT to scale; see 01_analysis/route_analysis.md).
P_CIM = (560, 1560)
P_DEST = (1640, 860)
VIA_PADOVA = [(250, 1990), (900, 1500), (1640, 860), (2250, 330)]   # straight schematic axis
M2_LINE = [(150, 2250), (560, 1560), (820, 1050), (1000, 300)]
ROUTE = [P_CIM, (820, 1560), (1150, 1330), (1420, 1060), P_DEST]  # smooth schematic arc

def _poly_len(pts):
    return [0] + list(np.cumsum([math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]))
def _smooth(pts, n=120):
    pts = np.array(pts, float); out = []
    P = np.vstack([pts[0], pts, pts[-1]])
    for i in range(1, len(P) - 2):
        for u in np.linspace(0, 1, n // (len(P) - 3), endpoint=False):
            p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
    out.append(P[-2]); return [tuple(p) for p in out]
ROUTE_S = _smooth(ROUTE, 160)
ROUTE_L = _poly_len(ROUTE_S)

def _route_upto(frac):
    L = ROUTE_L[-1] * frac; pts = [ROUTE_S[0]]
    for i in range(1, len(ROUTE_S)):
        if ROUTE_L[i] <= L: pts.append(ROUTE_S[i])
        else:
            u = (L - ROUTE_L[i - 1]) / (ROUTE_L[i] - ROUTE_L[i - 1] + 1e-9)
            a, b = ROUTE_S[i - 1], ROUTE_S[i]; pts.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)); break
    return pts

def _map_base():
    im = Image.new('RGB', (MS, MS), (13, 14, 17)); d = ImageDraw.Draw(im)
    for x in range(0, MS, 40):                              # dot-matrix texture (no fake streets)
        for y in range(0, MS, 40):
            d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(30, 32, 38))
    d.line(VIA_PADOVA, fill=(70, 72, 80), width=44, joint='curve')
    d.line(VIA_PADOVA, fill=(120, 122, 132), width=6, joint='curve')
    d.line(M2_LINE, fill=M2GREEN, width=16, joint='curve')
    return im
MAP_BASE = _map_base()

def _homog(src, dst):
    A_ = []; b_ = []
    for (x, y), (u, v) in zip(src, dst):
        A_ += [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]; b_ += [u, v]
    h = np.linalg.solve(np.array(A_, float), np.array(b_, float)); return np.append(h, 1).reshape(3, 3)

def s04(t):
    p = seg(t, 16.8, 22.3)
    trim = e_io(seg(t, 17.6, 20.6))
    # camera: focus moves along the route; tilt grows; final zoom on destination pin
    fpt = _route_upto(max(trim, 0.001))[-1]
    zoomin = e_io(seg(t, 20.6, 22.2))
    fx = lerp(lerp(P_CIM[0], fpt[0], e_io(seg(t, 17.3, 20.8))), P_DEST[0], zoomin)
    fy = lerp(lerp(P_CIM[1], fpt[1], e_io(seg(t, 17.3, 20.8))), P_DEST[1], zoomin)
    tilt = e_io(seg(t, 16.9, 18.4)) * (1 - 0.55 * zoomin)          # 0 = top-down
    half = lerp(820, 1050, e_io(seg(t, 16.9, 18.6))) * lerp(1, 0.38, zoomin)
    head = math.radians(lerp(-8, 14, p))
    # footprint quad in map space: near edge narrower (perspective), far edge wider
    nearw, farw = half * (1 - 0.45 * tilt), half * (1 + 0.65 * tilt)
    depth_far, depth_near = half * 1.75 * (1 + 0.4 * tilt), half * 1.1
    def rot(dx, dy):
        c, s_ = math.cos(head), math.sin(head)
        return (fx + dx * c - dy * s_, fy + dx * s_ + dy * c)
    quad = [rot(-farw, -depth_far), rot(farw, -depth_far), rot(nearw, depth_near), rot(-nearw, depth_near)]
    Hm = _homog([(0, 0), (W, 0), (W, H), (0, H)], quad)              # screen -> map
    Hinv = np.linalg.inv(Hm)
    def scr(pt):
        v = Hinv @ np.array([pt[0], pt[1], 1.0]); return (v[0] / v[2], v[1] / v[2])
    # dynamic map layer: route trim path (glow) + moving arrows
    mp = MAP_BASE.copy(); d = ImageDraw.Draw(mp)
    gl = Image.new('RGB', (MS, MS)); dg = ImageDraw.Draw(gl)
    if trim > 0:
        rp = _route_upto(trim)
        if len(rp) > 1:
            dg.line(rp, fill=ORANGE, width=30, joint='curve')
        for k in range(14):                                          # arrows riding the route
            u = ((t * 0.18 + k / 14) % 1.0)
            if u > trim - 0.02: continue
            a = _route_upto(u)[-1]; b = _route_upto(min(u + 0.01, 1))[-1]
            ang = math.atan2(b[1] - a[1], b[0] - a[0])
            pts = [(a[0] + 22 * math.cos(ang + s_ * 2.5), a[1] + 22 * math.sin(ang + s_ * 2.5)) for s_ in (1, 0, -1)]
            pts[1] = (a[0] + 26 * math.cos(ang), a[1] + 26 * math.sin(ang))
            dg.line(pts, fill=(255, 235, 210), width=8)
    gsmall = gl.resize((MS // 4, MS // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(8)).resize((MS, MS), Image.BILINEAR)
    mp = add(add(mp, gl), gsmall)
    coeffs = (Hm / Hm[2, 2]).flatten()[:8]
    im = mp.transform((W, H), Image.PERSPECTIVE, tuple(coeffs), Image.BICUBIC, fillcolor=(13, 14, 17))
    # atmospheric depth: darken toward the top (far)
    a = np.asarray(im).astype(np.float32)
    fog = np.linspace(0.25 + 0.75 * (1 - tilt), 1, H)[:, None, None]
    im = Image.fromarray(np.clip(a * fog + (1 - fog) * np.array([13, 14, 17]), 0, 255).astype(np.uint8))
    im = grade(im, t, 0.6, grain=False)
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    # screen-space markers & labels (crisp)
    kc = e_out(seg(t, 17.1, 17.8))
    c = scr(P_CIM)
    if kc > 0:
        r = 26 * kc
        d.ellipse((c[0] - r - 10, c[1] - r - 10, c[0] + r + 10, c[1] + r + 10), fill=(255, 255, 255, 60))
        d.ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), fill=(255, 255, 255, 255), outline=M2GREEN + (255,), width=8)
        lab(d, (c[0] + 46, c[1]), 'CIMIANO', 'M2', kc, M2GREEN)
    kv = win(t, 17.6, 22.4, 0.6, 0.4)
    if kv > 0:
        a_, b_ = scr(VIA_PADOVA[1]), scr(VIA_PADOVA[2])
        mx, my = (a_[0] * 0.45 + b_[0] * 0.55), (a_[1] * 0.45 + b_[1] * 0.55)
        ang = math.degrees(math.atan2(b_[1] - a_[1], b_[0] - a_[0]))
        tl = Image.new('RGBA', (560, 80), (0, 0, 0, 0))
        text_tracked(ImageDraw.Draw(tl), (280, 40), 'VIA PADOVA', font('Inter-Bold', 38), (210, 212, 220, int(255 * kv)), 10)
        tl = tl.rotate(-ang, expand=True, resample=Image.BICUBIC)
        ov.alpha_composite(tl, (int(mx - tl.width / 2 - 40), int(my - tl.height / 2 - 40)))
    kd = e_expo(seg(t, 20.3, 21.1))
    if kd > 0:
        c = scr(P_DEST)
        pulse = (t * 1.4) % 1
        rr = 40 + 90 * pulse
        d.ellipse((c[0] - rr, c[1] - rr * 0.6, c[0] + rr, c[1] + rr * 0.6), outline=ORANGE + (int(200 * (1 - pulse) * kd),), width=5)
        pin(d, c, 1.15 * kd)
        lab(d, (c[0] + 70, c[1] - 110), 'PUNTOCOM', 'Via Padova 167', kd, ORANGE)
    ar(d, (W / 2, 1830), 'رسم توضيحي · مش بمقياس رسم', afont('IBMPlexSansArabic-Regular', 26),
       (255, 255, 255, int(120 * win(t, 17.2, 22, 0.5, 0.4))))
    headline(ov, t, 17.4, 21.9, 'وجهتك Puntocom')
    progress_rail(ov, t)
    im = overlay_rgba(im, ov)
    im = fade(im, seg(t, 16.8, 17.3) * 0.85 + 0.15, (10, 10, 12))
    return im

def pin(d, c, s):
    if s <= 0: return
    x, y = c; r = 34 * s
    d.ellipse((x - 14 * s, y - 6 * s, x + 14 * s, y + 6 * s), fill=(0, 0, 0, 120))
    d.polygon([(x, y), (x - r * 0.75, y - r * 1.5), (x + r * 0.75, y - r * 1.5)], fill=ORANGE + (255,))
    d.ellipse((x - r, y - r * 2.6, x + r, y - r * 0.6), fill=ORANGE + (255,))
    d.ellipse((x - r * 0.42, y - r * 2.02, x + r * 0.42, y - r * 1.18), fill=(17, 17, 17, 255))

def lab(d, xy, a, b, k, col):
    x, y = xy; al = int(255 * clamp(k))
    fa, fb = font('Inter-Black', 40), font('Inter-SemiBold', 28)
    w_ = max(fa.getlength(a), fb.getlength(b)) + 56
    d.rounded_rectangle((x, y - 52, x + w_ * clamp(k * 1.4), y + 52), 18, fill=(17, 17, 17, int(225 * k)))
    d.rectangle((x, y - 52, x + 8, y + 52), fill=col + (al,))
    if k > 0.5:
        d.text((x + 28, y - 16), a, font=fa, fill=(255, 255, 255, al), anchor='lm')
        d.text((x + 28, y + 26), b, font=fb, fill=(255, 205, 160, al), anchor='lm')

# ================================================================ S05 STOREFRONT (original photo)
DOOR = (1726, 1505)                       # threshold of the CAF-PATRONATO entrance (image px)
GPS_PATH = [(980, 1660), (1240, 1610), (1480, 1560), DOOR]
def s05(t):
    p = e_io5(seg(t, 21.9, 28.9))
    s = lerp(0.47, 0.80, p)
    cx = lerp(1178, 1660, p); cy = lerp(800, 830, p)
    # background: blurred plate of the same photo, slower parallax, darkened
    bg = place(STORE_BG, s * 4.0 * 1.25 * lerp(1, 0.92, p), cx / 4.0, cy / 4.0)
    bg = Image.blend(Image.new('RGB', (W, H), BLACK), bg, 0.55)
    fg = place(IMG_STORE, s, cx, cy, size=(W, H))
    # feathered matte so the untouched photo sits inside the plate
    x0, y0 = to_screen(0, 0, s, cx, cy); x1, y1 = to_screen(2356, 1640, s, cx, cy)
    m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).rectangle((x0 + 6, y0 + 6, x1 - 6, y1 - 6), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(10))
    # drop shadow for depth
    sh = Image.new('L', (W, H), 0)
    ImageDraw.Draw(sh).rectangle((x0, y0 + 30, x1, y1 + 40), fill=200)
    bg.paste((0, 0, 0), (0, 0), sh.filter(ImageFilter.GaussianBlur(40)))
    bg.paste(fg, (0, 0), m)
    im = grade(bg, t, 0.7)
    # subtle warm light sweep across the signs (overlay only; photo untouched beneath)
    k = seg(t, 23.2, 25.6)
    if 0 < k < 1:
        L = Image.new('RGB', (W, H)); dl = ImageDraw.Draw(L)
        x = lerp(-500, W + 500, e_io(k))
        dl.polygon([(x - 90, 0), (x + 90, 0), (x - 190, H), (x - 370, H)], fill=(70, 46, 20))
        im = add(im, L.filter(ImageFilter.GaussianBlur(70)))
    # GPS line leading to the entrance (screen space, tracks the photo)
    tr = e_io(seg(t, 22.9, 25.0))
    sp = [to_screen(px, py, s, cx, cy) for px, py in _smooth(GPS_PATH, 60)]
    sp = [(x, min(y, H + 40)) for x, y in sp]
    if tr > 0:
        n = max(2, int(len(sp) * tr))
        def dr(dd, s_):
            dd.line(sp[:n], fill=ORANGE, width=int(16 * s_), joint='curve')
            if tr >= 1:
                r = 18 + 6 * math.sin(t * 6)
                x, y = sp[-1]; dd.ellipse((x - r, y - r * 0.45, x + r, y + r * 0.45), outline=ORANGE, width=6)
        im = add(im, glow_layer(dr, 16, 1.1))
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    headline(ov, t, 24.5, 28.6, 'وصلت! إحنا في انتظارك', y=200, size=66)
    # service chips: wording taken from the shop's own Arabic window sign, ordered right-to-left
    chips = (('خدمات الكاف', 25.9), ('الباتروناتو', 26.25), ('الهجرة والجنسية', 26.6), ('المحاسبة', 26.95))
    fch = afont('IBMPlexSansArabic-SemiBold', 30)
    widths = [ar_len(c, fch) + 48 for c, _ in chips]
    gap = 18; x = W / 2 + (sum(widths) + gap * 3) / 2
    for (txt, a), wdt in zip(chips, widths):
        kk = e_expo(seg(t, a, a + 0.5)) * (1 - seg(t, 28.4, 28.9))
        cxx = x - wdt / 2; x -= wdt + gap
        if kk <= 0: continue
        yy = 1800 + (1 - kk) * 20
        d.rounded_rectangle((cxx - wdt / 2, yy - 30, cxx + wdt / 2, yy + 30), 30, fill=(17, 17, 17, int(210 * kk)), outline=ORANGE + (int(255 * kk),), width=3)
        ar(d, (cxx, yy - 2), txt, fch, (255, 255, 255, int(255 * kk)))
    progress_rail(ov, t)
    im = overlay_rgba(im, ov)
    # entry from map: orange iris opening from the pin position
    ki = e_io(seg(t, 21.9, 22.6))
    if ki < 1:
        m = Image.new('L', (W, H), 0); r = 140 + ki * 1200
        ImageDraw.Draw(m).ellipse((W / 2 - r, 820 - r, W / 2 + r, 820 + r), fill=255)
        ring = Image.new('RGB', (W, H)); ImageDraw.Draw(ring).ellipse((W / 2 - r, 820 - r, W / 2 + r, 820 + r), outline=ORANGE, width=14)
        im = Image.composite(im, Image.new('RGB', (W, H), (13, 14, 17)), m.filter(ImageFilter.GaussianBlur(4)))
        im = add(im, ring.filter(ImageFilter.GaussianBlur(3)))
    return im

# ================================================================ S06 BRAND REVEAL (original logo)
_g = np.sqrt(((_xx - W / 2) / W) ** 2 + ((_yy - 820) / H) ** 2)
NAVY_BG = Image.fromarray(np.clip(np.dstack([
    lerp(NAVY[0] + 10, NAVY[0] - 7, np.clip(_g * 1.6, 0, 1)),
    lerp(NAVY[1] + 14, NAVY[1] - 10, np.clip(_g * 1.6, 0, 1)),
    lerp(NAVY[2] + 22, NAVY[2] - 14, np.clip(_g * 1.6, 0, 1))]), 0, 255).astype(np.uint8))

def logo_layer(key, scale, alpha, blur=0.0, dy=0.0):
    lg = LOGO[key]
    sz = (int(lg.width * scale), int(lg.height * scale))
    l = lg.resize(sz, Image.LANCZOS)
    if blur > 0.3: l = l.filter(ImageFilter.GaussianBlur(blur))
    if alpha < 1:
        a = l.getchannel('A').point(lambda v: int(v * alpha)); l.putalpha(a)
    c = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    c.alpha_composite(l, (int(W / 2 - sz[0] / 2), int(800 - sz[1] / 2 + dy)))
    return c

def s06(t):
    base = NAVY_BG.copy().convert('RGBA')
    S = 1.45
    # 1. gold light sweep
    k = seg(t, 28.7, 30.1)
    if 0 < k < 1:
        L = Image.new('RGB', (W, H)); dl = ImageDraw.Draw(L)
        x = lerp(-600, W + 600, e_io(k))
        dl.polygon([(x - 60, 0), (x + 60, 0), (x - 260, H), (x - 380, H)], fill=GOLD)
        base = add(base.convert('RGB'), L.filter(ImageFilter.GaussianBlur(80))).convert('RGBA')
    # 2. symbol
    ks = e_out(seg(t, 29.5, 30.7))
    if ks > 0:
        base.alpha_composite(logo_layer('symbol', S * lerp(0.9, 1.0, ks), ks, blur=(1 - ks) * 10))
    # 3. wordmark: left-to-right wipe with glint
    kw = e_io(seg(t, 30.5, 31.5))
    if kw > 0:
        wl = logo_layer('wordmark', S, 1.0)
        m = Image.new('L', (W, H), 0)
        xe = lerp(W / 2 - 520, W / 2 + 540, kw)
        ImageDraw.Draw(m).rectangle((0, 0, xe, H), fill=255)
        m = m.filter(ImageFilter.GaussianBlur(26))
        wl.putalpha(ImageChops.multiply(wl.getchannel('A'), m))
        base.alpha_composite(wl)
        if kw < 1:
            gl = Image.new('RGB', (W, H)); ImageDraw.Draw(gl).rectangle((xe - 20, 830 - 10, xe + 20, 830 + 160), fill=(255, 225, 170))
            base = add(base.convert('RGB'), gl.filter(ImageFilter.GaussianBlur(28))).convert('RGBA')
    # 4. CAF PATRONATO + gold rules
    kc = e_out(seg(t, 31.3, 32.2))
    if kc > 0:
        base.alpha_composite(logo_layer('subline', S, kc, dy=(1 - kc) * 16))
    im = base.convert('RGB')
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    # 5. address + claim
    ka = e_out(seg(t, 32.2, 33.0))
    if ka > 0:
        y = 1300 + (1 - ka) * 20
        lw = 300 * ka
        d.rectangle((W / 2 - lw, y - 70, W / 2 + lw, y - 68), fill=GOLD + (int(150 * ka),))
        text_tracked(d, (W / 2, y), 'Via Padova 167 – Milano', font('Inter-Medium', 46), (255, 255, 255, int(255 * ka)), 3)
    kl = e_out(seg(t, 32.8, 33.7))
    if kl > 0:
        y = 1420 + (1 - kl) * 20
        ar(d, (W / 2, y + 6), 'مستنيينك!', afont('Cairo-Bold', 92), GOLD + (int(255 * kl),))
    im = overlay_rgba(im, ov)
    im = grade(im, t, 0.5, grain=True)
    im = fade(im, 1 - seg(t, 34.55, 35.0))
    return im

# ================================================================ timeline
def frame(i):
    t = i / FPS
    if t < 4.85: im = s01(t)
    elif t < 7.2:
        im = s02_card(t)
        ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        k = win(t, 5.3, 7.0, 0.4, 0.3)
        if k > 0:
            dd = ImageDraw.Draw(ov)
            yy = 1360 - e_out(seg(t, 5.3, 6.0)) * 30
            for j in range(3):                                   # rising chevrons
                ph = ((t * 1.6) + j / 3) % 1
                cy = yy - 90 - ph * 160; a = int(255 * k * math.sin(ph * math.pi))
                dd.line([(W / 2 - 46, cy + 30), (W / 2, cy - 10), (W / 2 + 46, cy + 30)], fill=ORANGE + (a,), width=12)
        headline(ov, t, 5.3, 9.8, 'تعالى نوصلك لمكتبنا')
        progress_rail(ov, t)
        im = overlay_rgba(im, ov)
    elif t < 16.95: im = s03(t)
    elif t < 21.9: im = s04(t)
    elif t < 28.85: im = s05(t)
    else: im = s06(t)
    # S05 -> S06 identity transition: orange route line morphs into gold light (28.6-29.2)
    if 28.55 < t < 29.25:
        k = 1 - abs(seg(t, 28.55, 29.25) * 2 - 1)
        L = Image.new('RGB', (W, H)); dl = ImageDraw.Draw(L)
        col = tuple(int(lerp(ORANGE[c], GOLD[c], seg(t, 28.55, 29.25))) for c in range(3))
        y = lerp(H + 100, -100, seg(t, 28.55, 29.25))
        dl.rectangle((0, y - 30, W, y + 30), fill=col)
        im = add(im, Image.fromarray((np.asarray(L.filter(ImageFilter.GaussianBlur(50))).astype(np.float32) * (0.6 + k)).clip(0, 255).astype(np.uint8)))
    return np.asarray(im, dtype=np.uint8).tobytes()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out'); ap.add_argument('--preview', nargs='*', type=float)
    ap.add_argument('--workers', type=int, default=os.cpu_count())
    ap.add_argument('--audio')
    a = ap.parse_args()
    if a.preview:
        for s in a.preview:
            Image.frombytes('RGB', (W, H), frame(int(round(s * FPS)))).save(f'{a.out}_{s:05.2f}.jpg', quality=88)
        return
    n = int(DUR * FPS)
    cmd = ['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-']
    if a.audio: cmd += ['-i', a.audio, '-c:a', 'aac', '-b:a', '256k', '-shortest']
    cmd += ['-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
            '-movflags', '+faststart', '-r', str(FPS), a.out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    from multiprocessing import Pool
    with Pool(a.workers) as pool:
        for k, buf in enumerate(pool.imap(frame, range(n), chunksize=2)):
            ff.stdin.write(buf)
            if k % 150 == 0: print(f'frame {k}/{n}', flush=True)
    ff.stdin.close(); ff.wait()
    print('done', a.out)

if __name__ == '__main__':
    main()
