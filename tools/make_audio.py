#!/usr/bin/env python3
"""Original score + sound design for PUNTOCOM - THE WAY TO US (35 s, 48 kHz stereo).

Everything is synthesised here (no third-party music/SFX), so the audio is
royalty-free and fully reproducible. Stems are written to 07_audio/stems/, the
mix to 07_audio/puntocom_mix.wav.

Optional voiceover: pass --vo path/to/italian_vo.wav (or per-line files via
--vo-lines l1.wav ... l5.wav). Lines are placed on the cue times in VO_CUES and
the music is side-chain ducked under them.
"""
import argparse, os
import numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile

SR, DUR = 48000, 35.0
N = int(SR * DUR)
T = np.arange(N) / SR
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, '07_audio')
rng = np.random.default_rng(167)

BPM = 96.0
BEAT = 60 / BPM
# transitions (s) shared with the picture edit
CUTS = dict(whip=1.95, card=5.0, emerge=7.25, map=16.9, store=21.95, reveal=28.9)
PINGS = [7.6, 10.5, 13.6, 17.15, 20.5, 24.6]
VO_CUES = [0.6, 5.3, 10.3, 23.0, 30.6]   # VO line starts (s)

def lp(x, f, o=2): return sosfilt(butter(o, f / (SR / 2), 'low', output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f / (SR / 2), 'high', output='sos'), x)
def bp(x, a, b, o=2): return sosfilt(butter(o, [a / (SR / 2), b / (SR / 2)], 'band', output='sos'), x)
def env(t0, a, d, length=None):
    e = np.zeros(N); i0 = int(t0 * SR)
    L = int((length or (a + d)) * SR)
    tt = np.arange(L) / SR
    seg = np.where(tt < a, tt / max(a, 1e-4), np.exp(-(tt - a) / max(d, 1e-4)))
    i1 = min(N, i0 + L); e[i0:i1] = seg[: i1 - i0]; return e
def ramp(a, b):
    return np.clip((T - a) / (b - a), 0, 1)
def note(m): return 440 * 2 ** ((m - 69) / 12)

# ---------------------------------------------------------------- music
def saw(f, ph=0):
    return 2 * ((T * f + ph) % 1) - 1

def pad():
    # D major world: Dmaj9 - Bm11 - Gmaj9 - A6sus  (2 bars each = 5 s)
    chords = [[50, 57, 62, 64, 66, 69], [47, 54, 59, 62, 64, 69], [43, 50, 57, 59, 62, 66], [45, 52, 57, 59, 62, 66]]
    out = np.zeros((N, 2))
    bar2 = 8 * BEAT
    for k in range(int(DUR / bar2) + 1):
        ch = chords[k % 4]
        t0 = k * bar2
        g = np.clip((T - t0) / 0.6, 0, 1) * np.clip((t0 + bar2 + 0.6 - T) / 0.6, 0, 1)
        if not g.any(): continue
        for i, m in enumerate(ch):
            for det, pan in ((-0.07, 0.2), (0.07, 0.8)):
                v = saw(note(m) * (1 + det / 100 * 1.2), rng.random()) * g * 0.05
                out[:, 0] += v * (1 - pan); out[:, 1] += v * pan
    cutoff_open = ramp(0, 10) * 0.5 + ramp(17, 22) * 0.3
    out = np.stack([lp(out[:, c], 900) * (0.5 + cutoff_open) + lp(out[:, c], 2600) * cutoff_open for c in (0, 1)], 1)
    return out

def pluck_arp():
    seq = [74, 78, 81, 78, 76, 81, 83, 81]
    roots = [0, -3, -7, -5]
    out = np.zeros(N); step = BEAT / 2
    t = 5.0
    i = 0
    while t < 28.6:
        bar = int(t / (8 * BEAT)) % 4
        m = seq[i % 8] + roots[bar]
        f = note(m)
        L = int(0.5 * SR); i0 = int(t * SR)
        tt = np.arange(L) / SR
        s = (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(4 * np.pi * f * tt) + 0.1 * np.sin(6 * np.pi * f * tt)) * np.exp(-tt * 9)
        i1 = min(N, i0 + L); out[i0:i1] += s[: i1 - i0] * 0.07
        t += step; i += 1
    out *= ramp(5.0, 7.5)
    l = out + 0.35 * np.roll(out, int(SR * BEAT * 0.75)); r = out + 0.35 * np.roll(out, int(SR * BEAT * 0.5))
    return np.stack([l, r], 1)

def kick_pulse():
    out = np.zeros(N); t = 7.25
    while t < 28.7:
        L = int(0.35 * SR); i0 = int(t * SR); tt = np.arange(L) / SR
        f = 48 + 90 * np.exp(-tt * 28)
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9) * 0.5
        i1 = min(N, i0 + L); out[i0:i1] += s[: i1 - i0]
        t += BEAT
    # soft shaker on off-beats from 10 s
    sh = np.zeros(N); t = 10.3 + BEAT / 2
    while t < 28.6:
        sh += bp(rng.normal(0, 1, N), 6000, 11000) * env(t, 0.002, 0.04) * 0.05; t += BEAT
    return np.stack([out + sh * 0.8, out + sh * 1.2], 1)

def sub_bass():
    roots = [38, 35, 31, 33]
    out = np.zeros(N)
    for k in range(int(DUR / (8 * BEAT)) + 1):
        t0 = k * 8 * BEAT
        g = ((T >= t0) & (T < t0 + 8 * BEAT)).astype(float)
        out += np.sin(2 * np.pi * note(roots[k % 4]) * T) * g
    out = lp(out, 200) * 0.16 * ramp(9.5, 11)
    return np.stack([out, out], 1)

def reveal_chord():
    out = np.zeros((N, 2))
    for m, pan in ((50, .5), (57, .3), (62, .7), (66, .4), (69, .6), (74, .5), (78, .45)):
        v = (np.sin(2 * np.pi * note(m) * T) + 0.3 * np.sin(4 * np.pi * note(m) * T)) * 0.045
        g = ramp(29.3, 30.4) * (1 - ramp(33.8, 35.0))
        out[:, 0] += v * g * (1 - pan); out[:, 1] += v * g * pan
    # bell motif: gold "ding" on wordmark & claim
    for t0, m in ((30.6, 86), (31.3, 90), (32.9, 93)):
        tt = np.clip(T - t0, 0, None)
        b = (np.sin(2 * np.pi * note(m) * tt) + 0.5 * np.sin(2 * np.pi * note(m) * 2.76 * tt)) * np.exp(-tt * 2.2) * (T >= t0) * 0.06
        out[:, 0] += b; out[:, 1] += np.roll(b, 300)
    return out

# ---------------------------------------------------------------- sound design
def metro_amb():
    br = np.cumsum(rng.normal(0, 1, N)); br = hp(br / np.abs(br).max(), 20)
    rumble = lp(br, 180) * 2.2 + np.sin(2 * np.pi * 42 * T) * 0.03
    hiss = bp(rng.normal(0, 1, N), 800, 3500) * 0.012
    # distant train pass swell
    sw = np.exp(-((T - 2.6) / 1.4) ** 2)
    train = bp(rng.normal(0, 1, N), 120, 900) * sw * 0.12
    g = np.clip(T / 0.4, 0, 1) * (1 - ramp(6.2, 7.6))
    m = (rumble * 0.25 + hiss + train) * g
    return np.stack([m, np.roll(m, 480)], 1)

def city_amb():
    n = lp(rng.normal(0, 1, N), 1200) * 0.05
    cars = np.zeros(N)
    for t0, w in ((9.0, 1.4), (12.3, 1.8), (15.0, 1.2)):
        cars += bp(rng.normal(0, 1, N), 200, 1500) * np.exp(-((T - t0) / w) ** 2) * 0.09
    g = ramp(7.0, 8.2) * (1 - ramp(16.6, 17.4)) + (ramp(22.0, 23.0) * (1 - ramp(28.4, 29.2))) * 0.6
    l = (n + cars * 1.2) * g; r = (n * 0.9 + np.roll(cars, 2400)) * g
    return np.stack([l, r], 1)

def whoosh(t0, length=0.9, lo=300, hi=6000, gain=0.35, rev=False):
    L = int(length * SR); tt = np.arange(L) / L
    x = rng.normal(0, 1, L)
    e = np.sin(np.pi * tt) ** 2 if not rev else tt ** 3
    # sweep: blend of low and high band-passed noise along the envelope
    sl = bp(x, lo, lo * 3) * (1 - tt); sh_ = bp(x, hi / 3, min(hi, 20000)) * tt
    s = (sl + sh_) * e * gain
    out = np.zeros((N, 2)); i0 = int((t0 - length / 2) * SR) if not rev else int((t0 - length) * SR)
    i1 = min(N, i0 + L)
    pan = np.linspace(0.15, 0.85, L)[: i1 - i0]
    out[i0:i1, 0] = s[: i1 - i0] * (1 - pan); out[i0:i1, 1] = s[: i1 - i0] * pan
    return out

def ping(t0, gain=0.11):
    out = np.zeros(N)
    for f, d in ((1318.5, 0.0), (1760.0, 0.075)):
        tt = np.clip(T - t0 - d, 0, None)
        out += np.sin(2 * np.pi * f * tt) * np.exp(-tt * 14) * (T >= t0 + d)
    return np.stack([out, out], 1) * gain

def impact(t0):
    tt = np.clip(T - t0, 0, None); on = (T >= t0)
    f = 38 + 70 * np.exp(-tt * 10)
    boom = np.sin(2 * np.pi * np.cumsum(f * on) / SR) * np.exp(-tt * 2.2) * on * 0.55
    crack = hp(rng.normal(0, 1, N), 3000) * np.exp(-tt * 18) * on * 0.08
    shimmer = bp(rng.normal(0, 1, N), 7000, 14000) * np.exp(-tt * 1.4) * on * 0.03
    m = boom + crack
    return np.stack([m + shimmer, m + np.roll(shimmer, 900)], 1)

def reverse_swell(t_end, length=1.2):
    return whoosh(t_end, length, 400, 12000, 0.3, rev=True)

def store_door_tone():
    # warm low "arrival" swell under the storefront push-in
    tt = T - 22.0
    g = np.clip(tt / 1.5, 0, 1) * (1 - ramp(28.2, 29.0))
    v = (np.sin(2 * np.pi * note(38) * T) * 0.05 + np.sin(2 * np.pi * note(45) * T) * 0.03) * g
    return np.stack([v, v], 1)

# ---------------------------------------------------------------- mix
def load_wav(p):
    sr, x = wavfile.read(p)
    x = x.astype(np.float32)
    if x.dtype != np.float32 or np.abs(x).max() > 1.5: x = x / 32768.0
    if x.ndim == 1: x = np.stack([x, x], 1)
    if sr != SR:
        idx = np.arange(int(len(x) * SR / sr)) * sr / SR
        x = np.stack([np.interp(idx, np.arange(len(x)), x[:, c]) for c in (0, 1)], 1)
    return x

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--vo', help='single VO wav, placed at VO_CUES[0]')
    ap.add_argument('--vo-lines', nargs=5, help='five per-line VO wavs, placed on VO_CUES')
    a = ap.parse_args()
    os.makedirs(os.path.join(OUT, 'stems'), exist_ok=True)
    music = pad() + pluck_arp() + kick_pulse() + sub_bass() + reveal_chord()
    music *= (1 - 0.65 * (ramp(28.3, 28.9) * (1 - ramp(29.3, 29.9))))[:, None]  # breath before the reveal
    sfx = metro_amb() + city_amb() + store_door_tone()
    for k, t0 in CUTS.items():
        if k == 'reveal':
            sfx += reverse_swell(t0) + impact(t0 + 0.65)
        else:
            sfx += whoosh(t0, 0.8 if k != 'map' else 1.1, gain=0.3)
    for p in PINGS: sfx += ping(p)
    vo = np.zeros((N, 2))
    if a.vo_lines:
        for p, c in zip(a.vo_lines, VO_CUES):
            x = load_wav(p); i0 = int(c * SR); i1 = min(N, i0 + len(x)); vo[i0:i1] += x[: i1 - i0]
    elif a.vo:
        x = load_wav(a.vo); i0 = int(VO_CUES[0] * SR); i1 = min(N, i0 + len(x)); vo[i0:i1] += x[: i1 - i0]
    if np.abs(vo).max() > 0:
        e = np.abs(vo).max(1); e = lp(e, 6); e = e / (e.max() + 1e-9)
        duck = 1 - 0.55 * np.clip(e * 3, 0, 1)
        music *= duck[:, None]; sfx *= (1 - 0.3 * np.clip(e * 3, 0, 1))[:, None]
    fade = np.clip(T / 0.15, 0, 1) * np.clip((DUR - T) / 0.5, 0, 1)
    mix = (music * 0.9 + sfx + vo * 1.0) * fade[:, None]
    peak = np.abs(mix).max(); mix = mix / peak * 0.89          # -1 dBFS peak
    mix = np.tanh(mix * 1.15) / np.tanh(1.15)                  # gentle soft-clip glue
    for name, x in (('music', music), ('sfx', sfx), ('vo', vo)):
        pk = np.abs(x).max() or 1
        wavfile.write(os.path.join(OUT, 'stems', f'{name}.wav'), SR, (x / pk * 0.89 * 32767).astype(np.int16))
    wavfile.write(os.path.join(OUT, 'puntocom_mix.wav'), SR, (mix * 32767).astype(np.int16))
    print('mix written', 'with VO' if np.abs(vo).max() > 0 else '(no VO supplied)')

if __name__ == '__main__':
    main()
