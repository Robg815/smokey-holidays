#!/usr/bin/env python3
"""Procedural painter for the holiday artwork. Renders original, layered scenes with real lighting (gradients, glow,
bloom, fog, reflections, depth of field, colour grading, grain) into web/img/<id>/scene.webp. Deterministic (seeded).

    pip install numpy scipy pillow
    python dev/paint.py              every scene
    python dev/paint.py halloween    only some
"""
import math, os, sys, random
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(os.environ['PAINT_OUT']) if os.environ.get('PAINT_OUT') else ROOT / 'web' / 'img'   # PAINT_OUT: draft folder
W, H = 2400, 1040          # delivered size
SS = float(os.environ.get('PAINT_SS', 1.4))   # supersampling for smooth edges (PAINT_SS=0.5 for a quick draft)

def hexc(h, a=None):
    h = h.lstrip('#'); c = np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)
    return c

class Canvas:
    def __init__(self, seed=1):
        self.w, self.h = int(W * SS), int(H * SS)
        self.img = np.zeros((self.h, self.w, 3), np.float32)
        self.emit = np.zeros((self.h, self.w, 3), np.float32)   # light sources only; drives bloom
        self.rng = np.random.default_rng(seed); self.r = random.Random(seed)
        self.yy, self.xx = np.mgrid[0:self.h, 0:self.w].astype(np.float32)
        self.yy /= SS; self.xx /= SS           # coordinates in delivered pixels

    # ---------- masks ----------
    def mask(self, fn):
        m = Image.new('L', (self.w, self.h), 0); fn(ImageDraw.Draw(m), SS)
        return np.asarray(m, np.float32) / 255
    def poly(self, pts):
        return self.mask(lambda d, s: d.polygon([(x * s, y * s) for x, y in pts], fill=255))
    def ellipse(self, cx, cy, rx, ry):
        return self.mask(lambda d, s: d.ellipse([(cx - rx) * s, (cy - ry) * s, (cx + rx) * s, (cy + ry) * s], fill=255))
    def ellipses(self, es):  # [(cx, cy, rx, ry)] drawn into one mask (much faster than one mask each)
        def f(d, s):
            for x, y, rx, ry in es: d.ellipse([(x - rx) * s, (y - ry) * s, (x + rx) * s, (y + ry) * s], fill=255)
        return self.mask(f)
    def bevel(self, m, light=(-0.6, -0.8), width=3.0, hi='#ffffff', hk=0.35, lk=0.45):
        """Light the sun-facing edges of every shape in m and shade the far edges (one pass for many shapes)."""
        lx, ly = light; sh = (ly * width * SS, lx * width * SS)
        lit = np.clip(m - ndimage.shift(m, sh, order=1), 0, 1); dark = np.clip(m - ndimage.shift(m, (-sh[0], -sh[1]), order=1), 0, 1)
        lit = ndimage.gaussian_filter(lit, 0.8 * SS); dark = ndimage.gaussian_filter(dark, 1.2 * SS)
        self.img *= (1 - dark * lk)[..., None]; self.add(lit * m, hexc(hi), hk, False)
    def lines(self, segs):  # [(x0, y0, x1, y1, width)]
        def f(d, s):
            for x0, y0, x1, y1, w in segs:
                d.line([(x0 * s, y0 * s), (x1 * s, y1 * s)], fill=255, width=max(1, int(w * s)))
                r = w * s / 2; d.ellipse([x1 * s - r, y1 * s - r, x1 * s + r, y1 * s + r], fill=255)
        return self.mask(f)
    def below(self, ys):  # ys: height per delivered x column -> mask of everything below that line
        cols = np.interp(np.arange(self.w) / SS, np.linspace(0, W, len(ys)), ys)
        return np.clip((self.yy - cols[None, :]) * SS * 0.8 + 0.5, 0, 1)

    # ---------- painting ----------
    def fill(self, m, color, alpha=1.0):
        c = color if isinstance(color, np.ndarray) and color.ndim == 3 else np.asarray(color, np.float32)[None, None, :]
        a = (m * alpha)[..., None]
        self.img = self.img * (1 - a) + c * a
        self.emit *= (1 - a)
    def add(self, light, color=None, k=1.0, emissive=True):
        if color is not None: light = light[..., None] * np.asarray(color, np.float32)[None, None, :]
        self.img += light * k
        if emissive: self.emit += light * k
    def vgrad(self, stops, y0=0, y1=H):  # stops [(t, '#hex')]
        t = np.clip((self.yy[:, :1] - y0) / (y1 - y0), 0, 1)
        ts = [s[0] for s in stops]; cs = np.array([hexc(s[1]) for s in stops])
        g = np.stack([np.interp(t[:, 0], ts, cs[:, i]) for i in range(3)], -1)
        return np.broadcast_to(g[:, None, :], self.img.shape).copy()
    def radial(self, cx, cy, r, power=2.0):
        d = np.sqrt((self.xx - cx) ** 2 + (self.yy - cy) ** 2) / r
        return np.exp(-d ** power)
    def glow(self, cx, cy, r, color, k=1.0, power=2.0, emissive=True):
        self.add(self.radial(cx, cy, r, power), hexc(color) if isinstance(color, str) else color, k, emissive)

    # ---------- procedural noise ----------
    def noise(self, scale, octaves=5, seed=0, aspect=1.0):
        rng = np.random.default_rng(seed); out = np.zeros((self.h, self.w), np.float32); amp, tot = 1.0, 0.0
        for o in range(octaves):
            gh = max(2, int(self.h / SS / scale * 2 ** o) + 2); gw = max(2, int(self.w / SS / scale * aspect * 2 ** o) + 2)
            g = rng.random((gh, gw)).astype(np.float32)
            z = ndimage.zoom(g, (self.h / gh * 1.02, self.w / gw * 1.02), order=3)[:self.h, :self.w]
            if z.shape != out.shape: z = np.pad(z, ((0, self.h - z.shape[0]), (0, self.w - z.shape[1])), mode='edge')
            out += z * amp; tot += amp; amp *= 0.5
        return out / tot
    def ridge(self, base, amp, scale, seed, n=600, octaves=6):
        rng = np.random.default_rng(seed); xs = np.linspace(0, 1, n); y = np.zeros(n); a = 1.0; tot = 0
        for o in range(octaves):
            k = max(2, int(W / scale * 2 ** o)); g = rng.random(k + 1)
            y += np.interp(xs * k, np.arange(k + 1), g) * a; tot += a; a *= 0.5
        return base - (y / tot - 0.5) * 2 * amp

    # ---------- surface + light ----------
    def tex(self, color, var=0.25, scale=40, seed=0, octaves=4):
        n = self.noise(scale, octaves, seed)
        return hexc(color)[None, None, :] * (1 + var * (n - 0.5) * 2)[..., None]
    def rim(self, m, lx, ly, width=3.0, color='#ffffff', k=1.0, soft=1.0, glow=0.5):
        ys, xs = np.nonzero(m > 0.5)
        if len(xs) == 0: return
        cx, cy = xs.mean() / SS, ys.mean() / SS
        dx, dy = lx - cx, ly - cy; n = math.hypot(dx, dy) or 1; dx, dy = dx / n, dy / n
        ahead = ndimage.shift(m, (-dy * width * SS, -dx * width * SS), order=1, mode='constant')
        edge = np.clip(m - ahead, 0, 1)
        col = hexc(color)
        self.add(ndimage.gaussian_filter(edge, soft * SS), col, k, False)
        if glow: self.add(ndimage.gaussian_filter(edge, 6 * SS), col, k * glow, False)
    def grass(self, ys, height, seed, step=2.6, lean=0.35):
        r = random.Random(seed); xs = np.linspace(0, W, len(ys))
        def f(d, s):
            x = 0.0
            while x < W:
                y = float(np.interp(x, xs, ys)); h = height * r.uniform(0.3, 1.0); l = r.uniform(-lean, lean) * h
                w = r.uniform(1.2, 2.6)
                d.polygon([((x - w) * s, (y + 2) * s), ((x + l) * s, (y - h) * s), ((x + w) * s, (y + 2) * s)], fill=255)
                x += step * r.uniform(0.5, 1.5)
        return self.mask(f)
    def godrays(self, cx, cy, occluder, color, k=0.6, r=500, samples=56, decay=0.965, reach=0.55):
        f = 0.25; sh, sw = int(self.h * f), int(self.w * f)
        src = (self.radial(cx, cy, r, 1.6) * (1 - occluder))
        src = ndimage.zoom(src, (sh / self.h, sw / self.w), order=1)
        yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32); ccx, ccy = cx * SS * f, cy * SS * f
        acc = np.zeros_like(src); w = 1.0
        for i in range(samples):
            sc = 1 - reach * i / samples
            acc += ndimage.map_coordinates(src, [ccy + (yy - ccy) * sc, ccx + (xx - ccx) * sc], order=1) * w; w *= decay
        acc /= samples * 0.35
        acc = ndimage.zoom(acc, (self.h / sh, self.w / sw), order=1)[:self.h, :self.w]
        if acc.shape != (self.h, self.w): acc = np.pad(acc, ((0, self.h - acc.shape[0]), (0, self.w - acc.shape[1])), mode='edge')
        acc = acc / (1 + acc)                       # rays saturate instead of blowing out
        self.add(acc * (1 - 0.85 * occluder), hexc(color), k, False)  # solid things stay dark in front of the rays

    # ---------- post ----------
    def blur(self, a, s): return ndimage.gaussian_filter(a, (s * SS, s * SS, 0) if a.ndim == 3 else s * SS)
    def bloom(self, thresh=0.75, sigma=18, k=0.6):
        # only light sources glow (windows, bulbs, sun, fireworks), plus anything pushed past white
        src = self.emit + np.clip(self.img - 1.0, 0, None)
        self.img += (self.blur(src, sigma) * 0.55 + self.blur(src, sigma * 3) * 0.45) * k
    def grade(self, shadows='#000000', highlights='#ffffff', contrast=1.05, sat=1.05, exposure=1.0, tone='aces'):
        x = np.clip(self.img * exposure, 0, None)
        if tone == 'knee':   # authored colours stay as painted; only highlights above 0.72 roll off (never clip)
            k = 0.72; x = np.where(x < k, x, k + (1 - k) * (1 - np.exp(-(x - k) / (1 - k))))
        else:                # filmic (ACES): lifts shadows and rolls off highlights, the moody look of the night scenes
            x = (x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14)
        lum = x.mean(-1, keepdims=True)
        x = lum + (x - lum) * sat
        x = 0.5 + (x - 0.5) * contrast
        sh, hi = hexc(shadows), hexc(highlights)
        t = np.clip(lum, 0, 1); x = x * (1 - (1 - t) * 0.12) + (1 - t) * sh * 0.05 + t * (hi - 1.0) * 0.1  # tint shadows without lifting blacks
        self.img = x
    def vignette(self, k=0.35):
        d = np.sqrt(((self.xx - W / 2) / (W * 0.62)) ** 2 + ((self.yy - H / 2) / (H * 0.72)) ** 2)
        self.img *= (1 - k * np.clip(d, 0, 1.4) ** 2)[..., None]
    def save(self, path, grain=0.018, quality=86):
        img = self.img + self.rng.normal(0, grain, self.img.shape[:2])[..., None].astype(np.float32)
        im = Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)).resize((W, H), Image.LANCZOS)
        path.parent.mkdir(parents=True, exist_ok=True); im.save(path, 'WEBP', quality=quality, method=6)
        print('wrote', path, f'{path.stat().st_size // 1024} KB')

# ---------------------------------------------------------------- reusable elements
def stars(c, n, ymax, seed, k=1.0, tint='#ffffff'):
    r = random.Random(seed); layer = np.zeros(c.img.shape[:2], np.float32)
    for _ in range(n):
        x, y = r.uniform(0, W), r.uniform(0, ymax) ** 1.15 / ymax ** 0.15
        b = r.random() ** 3; ix, iy = int(x * SS), int(y * SS)
        if 0 <= ix < c.w and 0 <= iy < c.h: layer[iy, ix] += 0.4 + b * 3
    layer = ndimage.gaussian_filter(layer, 0.7 * SS) * 3 + ndimage.gaussian_filter(layer, 3 * SS) * 0.8
    c.add(layer, hexc(tint), k)

def moon(c, x, y, r, seed=3):
    d = np.sqrt((c.xx - x) ** 2 + (c.yy - y) ** 2); disc = np.clip((r - d) * SS, 0, 1)
    n = c.noise(r * 0.5, 4, seed); craters = 0.82 + 0.18 * n
    shade = np.clip(1 - ((c.xx - x + r * 0.35) ** 2 + (c.yy - y + r * 0.3) ** 2) / (r * 1.9) ** 2, 0.55, 1)
    col = hexc('#fff3d6')[None, None, :] * (craters * shade)[..., None]
    c.img = c.img * (1 - disc[..., None]) + col * disc[..., None] * 0.92
    c.glow(x, y, r * 1.35, '#ffe2a8', 0.32); c.glow(x, y, r * 4.5, '#ff9b5a', 0.18, power=1.2)

def cloud_band(c, y, h, color, alpha, seed, scale=260, soft=40):
    n = c.noise(scale, 6, seed, aspect=0.45)
    band = np.exp(-((c.yy - y) / h) ** 2)
    m = np.clip((n * band - 0.32) * 3.2, 0, 1)
    c.fill(ndimage.gaussian_filter(m, soft * SS * 0.1), hexc(color), alpha)

def fog(c, y, h, color, alpha, seed, scale=180):
    n = c.noise(scale, 5, seed, aspect=0.35)
    band = 1 / (1 + np.exp(-(c.yy - y) / h))
    c.fill(np.clip(band * (0.45 + n * 0.8), 0, 1), hexc(color), alpha)

def tree_mask(c, x, y, height, seed, spread=0.55, depth=7, lean=0.0):
    r = random.Random(seed); segs = []
    def br(x0, y0, ang, ln, w, d):
        x1, y1 = x0 + math.cos(ang) * ln, y0 - math.sin(ang) * ln
        segs.append((x0, y0, x1, y1, w))
        if d == 0: return
        for k in range(2 + (r.random() < 0.35)):
            br(x1, y1, ang + r.uniform(-spread, spread) + (k - 0.5) * 0.35, ln * r.uniform(0.62, 0.8), w * 0.68, d - 1)
    br(x, y, math.pi / 2 + lean, height * 0.32, height * 0.045, depth)
    return c.lines(segs)

def skyline(c, base, hmin, hmax, x0, x1, seed, color, lit, density=0.3, wmin=40, wmax=110):
    r = random.Random(seed); sil = np.zeros(c.img.shape[:2], np.float32); win = []
    x = x0
    while x < x1:
        w = r.uniform(wmin, wmax); hgt = r.uniform(hmin, hmax) * (1 - 0.5 * r.random() ** 3)
        top = base - hgt
        sil = np.maximum(sil, c.poly([(x, base + 60), (x, top), (x + w, top), (x + w, base + 60)]))
        if r.random() < 0.25:  # antenna / setback
            sil = np.maximum(sil, c.poly([(x + w * 0.4, top), (x + w * 0.4, top - hgt * 0.12), (x + w * 0.45, top - hgt * 0.12), (x + w * 0.45, top)]))
        for wy in np.arange(top + 10, base - 6, 13):
            for wx in np.arange(x + 6, x + w - 8, 10):
                if r.random() < density: win.append((wx, wy, r.uniform(0.4, 1.0)))
        x += w + r.uniform(-4, 6)
    c.fill(sil, hexc(color))
    if win:
        layer = np.zeros(c.img.shape[:2], np.float32)
        for wx, wy, b in win:
            ix, iy = int(wx * SS), int(wy * SS); layer[iy:iy + int(6 * SS), ix:ix + int(4 * SS)] = b
        layer *= sil
        c.add(layer, hexc(lit), 1.0); c.add(ndimage.gaussian_filter(layer, 6 * SS), hexc(lit), 1.6)
    return sil

def reflect(c, horizon, strength=0.6, ripple=3.0, tint='#0a1430', seed=5):
    hz = int(horizon * SS); below = c.h - hz
    src = c.img[max(0, hz - below):hz][::-1]
    if src.shape[0] < below: src = np.pad(src, ((0, below - src.shape[0]), (0, 0), (0, 0)), mode='edge')
    rows = np.arange(below)[:, None]; n = c.noise(60, 3, seed, aspect=0.15)[hz:]
    shift = (np.sin(rows * 0.35 / SS + n * 12) * ripple * SS * (0.3 + rows / below)).astype(int)
    cols = np.clip(np.arange(c.w)[None, :] + shift, 0, c.w - 1)
    refl = src[rows, cols]
    refl = ndimage.gaussian_filter(refl, (2.5 * SS, 0.6 * SS, 0))
    t = hexc(tint)[None, None, :]
    c.img[hz:] = refl * strength + t * (1 - strength) * (0.6 + 0.4 * rows[..., None] / below)

def particles(c, n, color, size, seed, y0=0, y1=H, blur_near=3.0, shape='dot', alpha=0.9, colors=None):
    r = random.Random(seed)
    for layer in range(3):  # far (sharp, small) .. near (big, blurred)
        m = np.zeros(c.img.shape[:2] + (3,), np.float32); a = np.zeros(c.img.shape[:2], np.float32)
        img = Image.new('RGBA', (c.w, c.h)); d = ImageDraw.Draw(img)
        for _ in range(n // 3):
            x, y = r.uniform(0, W), r.uniform(y0, y1); s = size * (0.5 + layer * 0.7) * r.uniform(0.6, 1.3)
            col = colors[r.randrange(len(colors))] if colors else color
            rgb = tuple(int(v * 255) for v in hexc(col)) + (int(255 * alpha),)
            if shape == 'dot': d.ellipse([(x - s) * SS, (y - s) * SS, (x + s) * SS, (y + s) * SS], fill=rgb)
            else:
                ang = r.uniform(0, math.pi); dx, dy = math.cos(ang) * s * 1.6, math.sin(ang) * s * 1.6
                pts = [((x + dx) * SS, (y + dy) * SS), ((x - dy * 0.5) * SS, (y + dx * 0.5) * SS), ((x - dx) * SS, (y - dy) * SS), ((x + dy * 0.5) * SS, (y - dx * 0.5) * SS)]
                d.polygon(pts, fill=rgb)
        arr = np.asarray(img, np.float32) / 255
        rgb, al = arr[..., :3], arr[..., 3]
        bl = [0.3, 1.2, blur_near][layer] * SS
        rgb = ndimage.gaussian_filter(rgb * al[..., None], (bl, bl, 0)); al = ndimage.gaussian_filter(al, bl)
        c.img = c.img * (1 - al[..., None]) + rgb

def firework(c, x, y, radius, color, seed, n=90, k=1.0, droop=0.25):
    r = random.Random(seed); layer = np.zeros(c.img.shape[:2], np.float32)
    img = Image.new('L', (c.w, c.h)); d = ImageDraw.Draw(img)
    for i in range(n):
        a = i / n * 2 * math.pi + r.uniform(-0.04, 0.04); rr = radius * r.uniform(0.75, 1.05)
        steps = 14
        for s in range(steps):
            t0, t1 = s / steps, (s + 1) / steps
            p = lambda t: (x + math.cos(a) * rr * t, y + math.sin(a) * rr * t + droop * radius * t * t)
            (ax, ay), (bx, by) = p(t0), p(t1)
            v = int(255 * (t1 ** 1.6))
            d.line([(ax * SS, ay * SS), (bx * SS, by * SS)], fill=v, width=max(1, int(1.6 * SS)))
        ex, ey = x + math.cos(a) * rr, y + math.sin(a) * rr + droop * radius
        d.ellipse([(ex - 2.2) * SS, (ey - 2.2) * SS, (ex + 2.2) * SS, (ey + 2.2) * SS], fill=255)
    m = np.asarray(img, np.float32) / 255
    col = hexc(color)
    c.add(m, col, 1.4 * k); c.add(ndimage.gaussian_filter(m, 4 * SS), col, 2.2 * k); c.add(ndimage.gaussian_filter(m, 22 * SS), col, 2.0 * k)
    c.glow(x, y, radius * 0.25, color, 0.5 * k)

def lit_window(c, x, y, w, h, color='#ffb35a', k=1.0):
    m = c.poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)])
    c.fill(m, hexc(color)); c.add(ndimage.gaussian_filter(m, max(w, h) * 0.6 * SS), hexc(color), 1.2 * k)

def jack(c, x, y, s, seed=0):
    body = c.ellipse(x, y, 34 * s, 26 * s)
    shade = np.clip(1 - ((c.xx - x + 10 * s) ** 2 / (40 * s) ** 2 + (c.yy - y + 10 * s) ** 2 / (34 * s) ** 2), 0, 1)
    col = np.stack([0.95 * (0.5 + 0.5 * shade), 0.42 * (0.4 + 0.6 * shade), 0.06 * shade + 0.02], -1)
    c.fill(body, col)
    for dx in (-18, 0, 18):  # ribs
        c.fill(c.ellipse(x + dx * s, y, 3 * s, 24 * s) * body, hexc('#8a3b06'), 0.35)
    face = np.maximum.reduce([c.poly([(x - 20 * s, y - 4 * s), (x - 8 * s, y - 14 * s), (x - 6 * s, y - 2 * s)]), c.poly([(x + 20 * s, y - 4 * s), (x + 8 * s, y - 14 * s), (x + 6 * s, y - 2 * s)]),
                              c.poly([(x - 22 * s, y + 6 * s), (x - 12 * s, y + 4 * s), (x - 6 * s, y + 12 * s), (x, y + 6 * s), (x + 6 * s, y + 12 * s), (x + 12 * s, y + 4 * s), (x + 22 * s, y + 6 * s), (x + 10 * s, y + 18 * s), (x - 10 * s, y + 18 * s)])])
    c.fill(face, hexc('#ffd56a')); c.add(ndimage.gaussian_filter(face, 10 * s * SS), hexc('#ff9a2a'), 2.0)
    c.glow(x, y + 30 * s, 70 * s, '#ff8a2a', 0.35)
    c.fill(c.lines([(x - 2 * s, y - 24 * s, x + 4 * s, y - 36 * s, 6 * s)]), hexc('#3a5a1a'))

def bokeh(c, n, colors, rmin, rmax, seed, y0=0, y1=H, k=0.5, x0=0, x1=W, heart=False):
    r = random.Random(seed)
    for col in colors:
        img = Image.new('L', (c.w, c.h)); d = ImageDraw.Draw(img)
        for _ in range(n // len(colors)):
            x, y, rr = r.uniform(x0, x1), r.uniform(y0, y1), r.uniform(rmin, rmax)
            v = int(255 * r.uniform(0.35, 1))
            if heart:
                pts = [(x + rr * 16 * math.sin(t) ** 3 / 16, y - rr * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) / 16) for t in np.linspace(0, 2 * math.pi, 40)]
                d.polygon([(px * SS, py * SS) for px, py in pts], fill=v)
            else:
                d.ellipse([(x - rr) * SS, (y - rr) * SS, (x + rr) * SS, (y + rr) * SS], fill=v)
        m = np.asarray(img, np.float32) / 255
        c.add(ndimage.gaussian_filter(m, rmin * 0.25 * SS), hexc(col), k)

def sun(c, x, y, r, color='#fff4d6', k=1.0, flare=True):
    d = np.sqrt((c.xx - x) ** 2 + (c.yy - y) ** 2)
    c.add(np.clip((r - d) * SS * 0.5, 0, 1), hexc(color), 1.0 * k)
    c.glow(x, y, r * 1.8, color, 0.45 * k); c.glow(x, y, r * 6, color, 0.14 * k, power=1.1, emissive=False)
    if flare:
        streak = np.exp(-((c.yy - y) / (r * 0.08)) ** 2) * np.exp(-np.abs(c.xx - x) / (r * 9))
        c.add(streak, hexc(color), 0.3 * k)

def day_clouds(c, y, h, seed, lx, ly, k=1.0, scale=300, shade='#9fb4d8', lit='#ffffff', density=0.95):
    n = c.noise(scale, 6, seed, aspect=0.5); d = c.noise(scale * 0.4, 4, seed + 9)
    m = np.clip((n * 0.85 + d * 0.3) * np.exp(-((c.yy - y) / h) ** 2) * 2.1 - density, 0, 1)
    m = ndimage.gaussian_filter(m, 2.5 * SS)
    dx, dy = lx - W / 2, ly - y; nn = math.hypot(dx, dy) or 1
    lightness = ndimage.shift(m, (dy / nn * 14 * SS, dx / nn * 14 * SS), order=1)
    shadeamt = np.clip(lightness - m * 0.6, 0, 1)
    col = hexc(lit)[None, None, :] * (1 - shadeamt[..., None] * 0.55) + hexc(shade)[None, None, :] * shadeamt[..., None] * 0.55
    c.fill(np.clip(m * 1.4, 0, 1), col, k)
    return m

def foliage(c, cx, cy, rx, ry, colors, seed, light=(0.6, -0.8), n=None, blob=None):
    """An organic canopy: noise-shaped silhouette, lit on the sun side, leaf-cluster texture in the given colours (dark to light)."""
    r = random.Random(seed); m = np.zeros(c.img.shape[:2], np.float32)
    for _ in range(9):  # a few overlapping lobes
        a = r.uniform(0, 2 * math.pi); d = r.uniform(0, 0.55)
        m = np.maximum(m, c.ellipse(cx + math.cos(a) * rx * d, cy + math.sin(a) * ry * d * 0.8, rx * r.uniform(0.45, 0.7), ry * r.uniform(0.45, 0.7)))
    m = ndimage.gaussian_filter(m, rx * 0.08 * SS)
    n1 = c.noise(rx * 0.25, 4, seed); n2 = c.noise(rx * 0.045, 3, seed + 1)
    m = np.clip((m + (n1 - 0.5) * 0.9 - 0.5) * 6, 0, 1)
    lx, ly = light; shift = ndimage.shift(m, (-ly * rx * 0.18 * SS, -lx * rx * 0.18 * SS), order=1)
    lit = np.clip(m - shift * 0.7, 0, 1); lit = ndimage.gaussian_filter(lit, rx * 0.06 * SS)
    tone = np.clip(0.25 + lit * 1.4 + (n2 - 0.5) * 0.55 + ((c.xx - cx) * lx + (c.yy - cy) * ly) / (rx * 2.2), 0, 0.999)
    pal = np.array([hexc(col) for col in colors]); idx = tone * (len(colors) - 1)
    lo = np.floor(idx).astype(int); hi = np.minimum(lo + 1, len(colors) - 1); f = (idx - lo)[..., None]
    col = pal[lo] * (1 - f) + pal[hi] * f
    c.fill(m, col.astype(np.float32))
    c.bevel(m, light, rx * 0.04, '#ffffff', 0.08, 0.25)
    return m

def leafy_tree(c, x, y, h, colors, seed, trunk='#2a1a10', light=(0.6, -0.8)):
    t = c.lines([(x, y, x + (light[0] * -6), y - h * 0.55, h * 0.06), (x, y - h * 0.4, x - h * 0.18, y - h * 0.7, h * 0.03), (x, y - h * 0.45, x + h * 0.16, y - h * 0.72, h * 0.03)])
    c.fill(t, hexc(trunk))
    m = foliage(c, x, y - h * 0.7, h * 0.42, h * 0.32, colors, seed, light)
    return np.maximum(t, m)

def pine(c, x, base, h, color, seed, snow=None, lights=None):
    r = random.Random(seed); m = np.zeros(c.img.shape[:2], np.float32); tiers = 7; edges = []
    for i in range(tiers):
        t0 = i / tiers; top = base - h * (0.08 + 0.92 * (1 - t0) ** 0.95) if i else base - h
        y_bot = base - h * 0.1 - (h * 0.9) * (1 - (i + 1) / tiers) * 0.95 + h * 0.05
        y_top = base - h + h * i / tiers * 0.85
        wd = h * 0.38 * (i + 1) / tiers + h * 0.04
        pts = [(x, y_top)]
        for k in range(9):
            u = k / 8; px = x - wd + 2 * wd * u; py = y_bot + (8 if k % 2 else 0) * (h / 400)
            pts.append((px, py))
        pts = [(x, y_top)] + [(x - wd, y_bot)] + [(x - wd + 2 * wd * k / 8, y_bot + (10 * h / 500 if k % 2 else 0)) for k in range(9)] + [(x + wd, y_bot)]
        tier = c.poly(pts); m = np.maximum(m, tier); edges.append((x, y_top, wd, y_bot))
    c.fill(m, c.tex(color, 0.35, 8, seed))
    shade = np.clip((c.xx - x) / (h * 0.3), -1, 1)
    c.fill(m, hexc('#000000'), 0.0)
    c.img = c.img * (1 - (m * np.clip(shade, 0, 1) * 0.35)[..., None])
    if snow:
        for (tx, ty, wd, yb) in edges:
            band = c.poly([(tx, ty), (tx - wd * 0.92, yb - 4), (tx - wd * 0.6, yb - 10), (tx, ty + 18), (tx + wd * 0.6, yb - 10), (tx + wd * 0.92, yb - 4)])
            c.fill(band * m * np.clip(1 - (c.yy - ty) / ((yb - ty) * 0.9), 0, 1), hexc(snow), 0.55)
    c.fill(c.poly([(x - h * 0.03, base), (x - h * 0.03, base - h * 0.12), (x + h * 0.03, base - h * 0.12), (x + h * 0.03, base)]), hexc('#2a1a10'))
    if lights:
        layer = {col: np.zeros(c.img.shape[:2], np.float32) for col in lights}
        for _ in range(int(h * 0.3)):
            t = r.uniform(0.08, 0.95); yy = base - h + h * t; wd = h * 0.4 * t
            xx = x + r.uniform(-wd, wd) * 0.92; col = r.choice(lights)
            layer[col] = np.maximum(layer[col], c.ellipse(xx, yy, h / 220 + 1.4, h / 220 + 1.4))
        for col, l in layer.items():
            c.add(l, hexc(col), 1.1); c.add(ndimage.gaussian_filter(l, 4 * SS), hexc(col), 0.9)
    return m

def ferris(c, cx, cy, R, frame, lights, seed, k=1.0):
    segs = [(cx + math.cos(a) * R, cy + math.sin(a) * R, cx + math.cos(a + 2 * math.pi / 64) * R, cy + math.sin(a + 2 * math.pi / 64) * R, 3) for a in np.linspace(0, 2 * math.pi, 64, endpoint=False)]
    segs += [(cx, cy, cx + math.cos(a) * R, cy + math.sin(a) * R, 1.6) for a in np.linspace(0, 2 * math.pi, 24, endpoint=False)]
    segs += [(cx, cy, cx - R * 0.55, cy + R * 1.25, 6), (cx, cy, cx + R * 0.55, cy + R * 1.25, 6)]
    m = c.lines(segs); c.fill(m, hexc(frame))
    r = random.Random(seed); layer = np.zeros(c.img.shape[:2], np.float32)
    for a in np.linspace(0, 2 * math.pi, 96, endpoint=False):
        layer = np.maximum(layer, c.ellipse(cx + math.cos(a) * R, cy + math.sin(a) * R, 2.6, 2.6))
    for a in np.linspace(0, 2 * math.pi, 24, endpoint=False):
        for t in (0.35, 0.65):
            layer = np.maximum(layer, c.ellipse(cx + math.cos(a) * R * t, cy + math.sin(a) * R * t, 1.8, 1.8))
    for i, col in enumerate(lights):
        part = layer * (np.sin(np.arctan2(c.yy - cy, c.xx - cx) * 6 + i * 2.1) > 0.3 - i * 0.6)
        c.add(part, hexc(col), 1.3 * k); c.add(ndimage.gaussian_filter(part, 5 * SS), hexc(col), 2.0 * k)
    return m

def person(c, x, y, s, arm=0.0, stride=0.0, lean=0.0):
    """A proportioned silhouette standing on (x, y). arm 0..1 raises the arms, stride 0..1 opens the legs (running)."""
    hx = x + lean * 10 * s
    head = c.ellipse(hx, y - 66 * s, 6.5 * s, 7.5 * s)
    neck = c.poly([(hx - 2.5 * s, y - 60 * s), (hx + 2.5 * s, y - 60 * s), (hx + 3 * s, y - 55 * s), (hx - 3 * s, y - 55 * s)])
    torso = c.poly([(hx - 11 * s, y - 56 * s), (hx + 11 * s, y - 56 * s), (x + 9 * s, y - 34 * s), (x + 8 * s, y - 30 * s), (x - 8 * s, y - 30 * s), (x - 9 * s, y - 34 * s)])
    st = stride * 14 * s
    legs = c.lines([(x - 4 * s, y - 31 * s, x - 5 * s - st, y - 15 * s, 6.5 * s), (x - 5 * s - st, y - 15 * s, x - 5 * s - st * 1.4, y, 5.5 * s),
                    (x + 4 * s, y - 31 * s, x + 5 * s + st, y - 15 * s, 6.5 * s), (x + 5 * s + st, y - 15 * s, x + 5 * s + st * 0.6, y - stride * 8 * s, 5.5 * s)])
    a1 = -arm * 38 * s
    arms = c.lines([(hx - 10 * s, y - 54 * s, hx - 17 * s, y - 40 * s + a1 * 0.6, 4.6 * s), (hx - 17 * s, y - 40 * s + a1 * 0.6, hx - 19 * s, y - 28 * s + a1 * 1.4, 4 * s),
                    (hx + 10 * s, y - 54 * s, hx + 17 * s, y - 40 * s + a1 * 0.5, 4.6 * s), (hx + 17 * s, y - 40 * s + a1 * 0.5, hx + 20 * s, y - 28 * s + a1 * 1.3, 4 * s)])
    return np.maximum.reduce([head, neck, torso, legs, arms])

def shade_ball(c, x, y, rx, ry, color, light=(-0.6, -0.7)):
    sh = np.clip(1 - (((c.xx - x - light[0] * rx * 0.5) / (rx * 1.4)) ** 2 + ((c.yy - y - light[1] * ry * 0.5) / (ry * 1.4)) ** 2), 0, 1)
    spec = np.exp(-(((c.xx - x - light[0] * rx * 0.45) / (rx * 0.18)) ** 2 + ((c.yy - y - light[1] * ry * 0.5) / (ry * 0.12)) ** 2))
    return hexc(color)[None, None, :] * (0.45 + 0.9 * sh[..., None]) + spec[..., None] * 0.35

def egg(c, x, y, rx, ry, base, stripe, seed, light=(-0.5, -0.7)):
    m = c.ellipse(x, y, rx, ry)
    shade = np.clip(1 - (((c.xx - x - light[0] * rx * 0.6) / (rx * 1.3)) ** 2 + ((c.yy - y - light[1] * ry * 0.5) / (ry * 1.3)) ** 2), 0, 1)
    col = hexc(base)[None, None, :] * (0.55 + 0.6 * shade[..., None])
    c.fill(m, col)
    r = random.Random(seed)
    for k in range(3):
        yy = y - ry * 0.5 + ry * 0.5 * k + r.uniform(-4, 4)
        band = np.clip(1 - np.abs(c.yy - yy - np.sin((c.xx - x) / rx * 6 + k) * ry * 0.06) / (ry * 0.07), 0, 1) * m
        c.fill(band, hexc(stripe) * 1.0, 0.85)
    c.add(np.exp(-(((c.xx - x - light[0] * rx * 0.45) / (rx * 0.22)) ** 2 + ((c.yy - y - light[1] * ry * 0.55) / (ry * 0.16)) ** 2)) * m, hexc('#ffffff'), 0.55)
    return m

def crane(c, x, base, h, jib, color, seed, flip=False):
    sgn = -1 if flip else 1; segs = []
    for y in np.arange(base, base - h, -22):
        segs += [(x - 10, y, x + 10, y - 22, 2), (x + 10, y, x - 10, y - 22, 2), (x - 10, y, x - 10, y - 22, 3), (x + 10, y, x + 10, y - 22, 3)]
    top = base - h
    segs += [(x - 60 * sgn, top, x + jib * sgn, top, 5), (x - 60 * sgn, top - 4, x + jib * sgn, top - 4, 3), (x, top - 70, x + jib * 0.9 * sgn, top, 2.4), (x, top - 70, x - 60 * sgn, top, 2.4), (x, top, x, top - 70, 4)]
    for u in np.arange(0, jib, 26): segs.append((x + u * sgn, top, x + (u + 13) * sgn, top - 4, 1.6))
    segs.append((x + jib * 0.7 * sgn, top, x + jib * 0.7 * sgn, top + h * 0.45, 1.2))
    m = c.lines(segs)
    m = np.maximum(m, c.poly([(x - 70 * sgn, top), (x - 40 * sgn, top), (x - 40 * sgn, top + 26), (x - 70 * sgn, top + 26)]))
    m = np.maximum(m, c.poly([(x + jib * 0.7 * sgn - 14, top + h * 0.45), (x + jib * 0.7 * sgn + 14, top + h * 0.45), (x + jib * 0.7 * sgn + 14, top + h * 0.45 + 20), (x + jib * 0.7 * sgn - 14, top + h * 0.45 + 20)]))
    c.fill(m, hexc(color)); return m

def hill(c, ys, top, bottom, seed, depth=220, light=None, rim='#ffffff', rimk=0.3, shadows=0.0, haze=None, hazek=0.0, tufts=0):
    """A hill layer: sunlit crest fading to a shaded foot, gentle texture, optional cloud shadows, haze for distance, grass tufts on the crest."""
    m = c.below(ys)
    if tufts: m = np.maximum(m, ndimage.gaussian_filter(c.grass(np.asarray(ys) + 4, tufts, seed, 3.0, 0.45), 0.5 * SS))
    cols = np.interp(np.arange(c.w) / SS, np.linspace(0, W, len(ys)), ys)[None, :]
    t = np.clip((c.yy - cols) / depth, 0, 1)[..., None] ** 0.8
    col = hexc(top)[None, None, :] * (1 - t) + hexc(bottom)[None, None, :] * t
    col = col * (0.94 + 0.12 * c.noise(60, 4, seed))[..., None] * (0.97 + 0.06 * c.noise(9, 2, seed + 3))[..., None]
    if shadows: col *= (1 - shadows * np.clip(c.noise(260, 4, seed + 7, aspect=0.6) * 2 - 0.9, 0, 1))[..., None]
    if haze: col = col * (1 - hazek) + hexc(haze)[None, None, :] * hazek
    c.fill(m, col)
    if light:  # soft sheen along the crest, strongest toward the sun; no hard outline
        crest = np.exp(-np.clip(c.yy - cols, 0, None) / 18) * m * (0.45 + 0.55 * np.exp(-((c.xx - light[0]) / 1100) ** 2))
        c.add(crest, hexc(rim), rimk * 0.55, False)
    return m

def water(c, horizon, top_color, deep_color, seed):
    g = c.vgrad([(0, top_color), (1, deep_color)], horizon, H)
    m = (c.yy >= horizon).astype(np.float32)
    c.fill(m, g)
    waves = c.noise(40, 3, seed, aspect=0.12)
    c.add(np.clip(waves - 0.62, 0, 1) * m * np.clip((c.yy - horizon) / 300, 0.1, 1), hexc('#ffffff'), 0.25)

# ---------------------------------------------------------------- scenes
def bat(c, bx, by, s, flap=0.0):
    up = -14 * s * (1 - flap); return c.poly([(bx, by), (bx - 10 * s, by - 4 * s), (bx - 26 * s, by + up), (bx - 44 * s, by - 4 * s + up * 0.3), (bx - 36 * s, by + 4 * s), (bx - 26 * s, by + 2 * s),
        (bx - 18 * s, by + 10 * s), (bx - 8 * s, by + 4 * s), (bx, by + 8 * s), (bx + 8 * s, by + 4 * s), (bx + 18 * s, by + 10 * s), (bx + 26 * s, by + 2 * s), (bx + 36 * s, by + 4 * s),
        (bx + 44 * s, by - 4 * s + up * 0.3), (bx + 26 * s, by + up), (bx + 10 * s, by - 4 * s)])

def lanterns(c, pts, color='#ffb050', size=3.0):
    layer = np.zeros(c.img.shape[:2], np.float32)
    for x, y, s in pts:
        layer = np.maximum(layer, c.ellipse(x, y, size * s, size * s * 1.2))
    c.add(layer, hexc(color), 1.6); c.add(ndimage.gaussian_filter(layer, 8 * SS), hexc(color), 3.0); c.add(ndimage.gaussian_filter(layer, 30 * SS), hexc(color), 1.6)

def mansion(c, mx, by):
    P = lambda pts: c.poly([(mx + x, by + y) for x, y in pts])
    parts = [
        P([(-260, 20), (-260, -120), (260, -120), (260, 20)]),                       # main body
        P([(-280, -118), (-190, -196), (-100, -118)]),                               # left gable
        P([(-100, -118), (-100, -230), (70, -230), (70, -118)]),                       # centre block
        P([(-122, -228), (-15, -330), (92, -228)]),                                  # centre gable
        P([(-34, -326), (-15, -420), (4, -326)]),                                    # centre spire
        P([(110, -118), (110, -290), (190, -290), (190, -118)]),                       # right tower
        P([(98, -288), (150, -440), (202, -288)]),                                   # tower roof
        P([(-230, -150), (-230, -250), (-206, -250), (-206, -150)]),                   # chimney
        P([(200, -120), (200, -170), (290, -170), (290, -120)]),                       # right wing
        P([(190, -168), (245, -205), (300, -168)]),
        P([(-60, 20), (-60, -40), (60, -40), (60, 20)]),                             # porch
        P([(-80, -38), (0, -80), (80, -38)]),
    ]
    for x in range(-270, 300, 18): parts.append(P([(x, -120), (x + 4, -134), (x + 8, -120)]))  # iron cresting
    m = np.maximum.reduce(parts)
    wins = [(-220, -95, 26, 44), (-160, -95, 26, 44), (-70, -200, 22, 38), (-30, -200, 22, 38), (10, -200, 22, 38), (-26, -300, 20, 26),
            (128, -260, 18, 30), (128, -200, 18, 30), (150, -150, 22, 36), (80, -95, 26, 44), (180, -95, 26, 44), (220, -150, 18, 22), (-20, -24, 40, 44)]
    return m, [(mx + x, by + y, w, h) for x, y, w, h in wins]

def halloween():
    c = Canvas(31)
    occ = np.zeros(c.img.shape[:2], np.float32)
    c.img = c.vgrad([(0, '#05020c'), (0.3, '#160829'), (0.55, '#3a1144'), (0.72, '#7a2348'), (0.86, '#c24a36'), (1, '#f08a45')], 0, 820)
    band = np.exp(-((c.yy - (c.xx * 0.18 + 40)) / 140) ** 2) * c.noise(120, 5, 61)
    c.add(np.clip(band - 0.25, 0, 1), hexc('#6a4aa0'), 0.35)          # faint milky way
    stars(c, 1400, 560, 2, 0.95)
    MX, MY = 1500, 215
    moon(c, MX, MY, 128)
    # clouds lit from the moon
    for y, hgt, a, sd, col in ((260, 70, 0.85, 7, '#1c0a26'), (150, 46, 0.7, 8, '#2a0f34'), (380, 40, 0.6, 9, '#3a1438')):
        n = c.noise(320, 6, sd, aspect=0.4); warp = c.noise(140, 3, sd + 50)
        m = np.clip((n * 0.8 + warp * 0.4) * np.exp(-((c.yy - y) / hgt) ** 2) * 1.9 - 0.85, 0, 1)
        m = ndimage.gaussian_filter(m, 3 * SS)
        c.fill(m, hexc(col), a); c.rim(m, MX, MY, 6, '#ffcf9a', 0.55, 2.0, 0.6); occ = np.maximum(occ, m * a)
    # far ridges with atmospheric haze, distant town lights
    far = c.ridge(650, 46, 520, 11); c.fill(c.below(far), hexc('#3a1840'))
    mid = c.ridge(700, 36, 380, 12); c.fill(c.below(mid), hexc('#2a0f30'))
    r = random.Random(5)
    lanterns(c, [(r.uniform(0, 1100), np.interp(x := r.uniform(0, 1100), np.linspace(0, W, 600), mid) + r.uniform(4, 30), r.uniform(0.2, 0.55)) for _ in range(140)], '#ffa24a', 2.2)
    fog(c, 690, 26, '#8a4a7a', 0.28, 21, 260)
    # the hill and the house on top of it
    xs = np.linspace(0, W, 600)
    hill = 800 - 245 * np.exp(-((xs - 1640) / 470) ** 2) + (c.ridge(0, 10, 90, 3) - 0)
    hm = c.below(hill); c.fill(hm, c.tex('#140716', 0.35, 30, 4)); c.rim(hm, MX, MY - 200, 2.5, '#d98aa0', 0.35, 1.0, 0.3)
    c.fill(c.grass(hill, 16, 14), hexc('#140716'))
    base = float(np.interp(1640, xs, hill)) + 14
    house, wins = mansion(c, 1640, base)
    c.fill(house, c.tex('#0a040e', 0.3, 18, 9)); c.rim(house, MX, MY, 3, '#ffd2a0', 0.9, 0.8, 0.5); occ = np.maximum(occ, house)
    for i, (x, y, w, h) in enumerate(wins):
        k = [1, 0.85, 1, 0.3, 0.9, 1, 1, 0.7, 0.9, 1, 0.8, 0.5, 0.9][i]
        lit_window(c, x, y, w, h, '#ffad45', k)
        bars = np.maximum(c.poly([(x + w / 2 - 1.2, y), (x + w / 2 + 1.2, y), (x + w / 2 + 1.2, y + h), (x + w / 2 - 1.2, y + h)]),
                          c.poly([(x, y + h * 0.42), (x + w, y + h * 0.42), (x + w, y + h * 0.42 + 2.4), (x, y + h * 0.42 + 2.4)]))
        c.fill(bars, hexc('#120608'), 0.9)
    c.glow(1640, base - 120, 380, '#ff8a3a', 0.12)
    # winding lantern path up to the door
    path = []
    for t in np.linspace(0, 1, 34):
        x = 2080 - 440 * t + 140 * math.sin(t * 5.2); y = 1015 - (1015 - base) * t ** 0.85
        path.append((x, y, 1.25 - t * 0.85))
    lanterns(c, path[::2], '#ffb85a', 3.2)
    # trees on the hill and a big gnarled tree framing the left
    for x, y, h, sd in ((1250, float(np.interp(1250, xs, hill)) + 8, 260, 4), (2050, float(np.interp(2050, xs, hill)) + 8, 230, 9), (1980, float(np.interp(1980, xs, hill)) + 8, 150, 19)):
        t = tree_mask(c, x, y, h, sd, 0.6, 6); c.fill(t, hexc('#0a0410')); c.rim(t, MX, MY, 2, '#e09ab0', 0.45, 0.6, 0.2); occ = np.maximum(occ, t)
    fog(c, 820, 34, '#b088d0', 0.14, 33, 240)
    # foreground ground, graves, fence, pumpkins
    gy = c.ridge(930, 18, 420, 9); gm = c.below(gy)
    c.fill(gm, c.tex('#0c0510', 0.4, 22, 17))
    r = random.Random(3)
    for x in np.arange(380, 1250, 105):
        y = float(np.interp(x, np.linspace(0, W, 600), gy)) + r.uniform(8, 26); w = r.uniform(42, 58); h = r.uniform(70, 104); tl = r.uniform(-8, 8)
        if r.random() < 0.3:  # cross
            st = np.maximum(c.poly([(x - 7, y), (x - 7 + tl * 0.2, y - h), (x + 7 + tl * 0.2, y - h), (x + 7, y)]), c.poly([(x - 28 + tl * 0.15, y - h * 0.7), (x + 28 + tl * 0.15, y - h * 0.7), (x + 28 + tl * 0.15, y - h * 0.7 + 12), (x - 28 + tl * 0.15, y - h * 0.7 + 12)]))
        else:
            st = c.poly([(x - w / 2, y), (x - w / 2 + tl * 0.3, y - h + w / 2), (x - w * 0.3 + tl * 0.8, y - h + 6), (x + tl, y - h - 4), (x + w * 0.3 + tl * 0.8, y - h + 6), (x + w / 2 + tl * 0.3, y - h + w / 2), (x + w / 2, y)])
        c.fill(st, c.tex('#2c2438', 0.45, 6, int(x))); c.rim(st, MX, MY, 3, '#d8c4ff', 0.6, 0.8, 0.25)
        c.fill(c.ellipse(x, y + 4, w * 0.8, 7), hexc('#05020a'), 0.6)
    fence = np.zeros(c.img.shape[:2], np.float32)
    fence = np.maximum.reduce([fence, c.poly([(260, 958), (1320, 942), (1320, 950), (260, 966)]), c.poly([(260, 995), (1320, 979), (1320, 987), (260, 1003)])])
    for x in np.arange(268, 1320, 24):
        yb = 966 - (x - 260) * 16 / 1060
        fence = np.maximum(fence, c.poly([(x, 1040), (x, yb - 34), (x + 3, yb - 48), (x + 6, yb - 34), (x + 6, 1040)]))
    c.fill(fence, hexc('#040208')); c.rim(fence, MX, MY, 1.5, '#b8a0e0', 0.35, 0.5, 0)
    big = tree_mask(c, 120, 1060, 980, 77, 0.5, 8, lean=0.08); c.fill(big, hexc('#040208')); c.rim(big, MX, MY, 3, '#e8a8c0', 0.5, 0.8, 0.3); occ = np.maximum(occ, big)
    c.fill(c.grass(gy + 6, 26, 41, 2.0, 0.5), hexc('#07030a'))
    for x, y, s in ((300, 1000, 1.5), (420, 1018, 1.0), (2180, 1000, 1.6), (2320, 1012, 1.0), (1980, 1022, 0.8)):
        c.fill(c.ellipse(x, y + 26 * s, 120 * s, 22 * s), hexc('#ff7a20'), 0.0)
        c.add(np.exp(-(((c.xx - x) / (150 * s)) ** 2 + ((c.yy - y - 20 * s) / (40 * s)) ** 2)), hexc('#ff7a2a'), 0.35)  # warm pool on the ground
        jack(c, x, y, s)
    fog(c, 1000, 22, '#c0a0ff', 0.18, 45, 150)
    for bx, by, s, f in ((1380, 190, 1.3, 0.2), (1620, 140, 0.9, 0.8), (1420, 330, 0.7, 0.4), (620, 170, 1.0, 0.6), (840, 250, 0.6, 0.1), (420, 290, 0.5, 0.9), (1760, 300, 0.55, 0.5)):
        b = bat(c, bx, by, s, f); c.fill(b, hexc('#05020a')); occ = np.maximum(occ, b)
    c.godrays(MX, MY, np.clip(occ, 0, 1), '#ffb880', 0.32, r=200)
    c.bloom(0.78, 14, 0.55); c.grade('#30104a', '#ffd6a8', 1.12, 1.12, 0.96); c.vignette(0.5)
    c.save(OUT / 'halloween' / 'scene.webp')

def christmas():
    c = Canvas(41)
    c.img = c.vgrad([(0, '#030714'), (0.45, '#0a1a3a'), (0.75, '#1a3a6a'), (1, '#2f5a8a')], 0, 760)
    stars(c, 700, 400, 4, 0.6, '#cfe6ff')
    aur = c.noise(260, 5, 3, aspect=0.3) * np.exp(-((c.yy - 170 - np.sin(c.xx / 300) * 40) / 70) ** 2)
    c.add(np.clip(aur - 0.25, 0, 1), hexc('#5affc8'), 0.35)
    skyline(c, 640, 90, 300, 0, W, 8, '#0a1630', '#ffd27a', 0.22, 50, 120)
    fog(c, 600, 40, '#5a7ab0', 0.3, 5, 300)
    # shop fronts left and right with warm windows and snowy roofs
    for x0, x1, top in ((0, 760, 520), (1640, W, 540)):
        bm = c.poly([(x0, 800), (x0, top), (x1, top), (x1, 800)]); c.fill(bm, c.tex('#1a1a2e', 0.3, 20, x0))
        c.fill(c.poly([(x0, top - 6), (x1, top - 6), (x1, top + 10), (x0, top + 10)]), hexc('#e8f0ff'), 0.9)
        for wx in np.arange(x0 + 40, x1 - 60, 120):
            lit_window(c, wx, top + 60, 70, 90, '#ffa84a', 0.45); lit_window(c, wx + 10, top + 190, 50, 60, '#ffb860', 0.3)
            c.fill(c.poly([(wx - 6, top + 150), (wx + 76, top + 150), (wx + 76, top + 158), (wx - 6, top + 158)]), hexc('#eef4ff'), 0.8)
    # snowy plaza
    ground = c.below(np.full(10, 800.0)); c.fill(ground, c.vgrad([(0, '#4a5a7a'), (1, '#8a9ab8')], 800, H) * (0.9 + 0.2 * c.noise(30, 3, 8))[..., None])
    c.add(np.exp(-(((c.xx - 1200) / 520) ** 2 + ((c.yy - 900) / 120) ** 2)), hexc('#ffb860'), 0.45)
    # string lights across the plaza
    r = random.Random(4); seglights = np.zeros(c.img.shape[:2], np.float32)
    for k, (xa, xb, ya) in enumerate(((0, 1200, 300), (1200, W, 300), (0, W, 420))):
        xs = np.linspace(xa, xb, 60); ys = ya + 90 * np.sin(np.pi * (xs - xa) / (xb - xa))
        c.fill(c.lines([(xs[i], ys[i], xs[i + 1], ys[i + 1], 1.4) for i in range(len(xs) - 1)]), hexc('#05080f'))
        for xx, yy in zip(xs[::2], ys[::2]):
            col = r.choice(['#ff5a6e', '#ffd36b', '#6dffb0', '#8fd8ff']); l = c.ellipse(xx, yy + 5, 3, 4)
            c.add(l, hexc(col), 1.5); c.add(ndimage.gaussian_filter(l, 6 * SS), hexc(col), 2.5)
    # the big tree
    pine(c, 1200, 830, 600, '#0f4a2a', 9, snow='#eef6ff', lights=['#ffd36b', '#ff5a6e', '#8fd8ff', '#ffffff'])
    star = c.poly([(1200 + math.cos(a) * (30 if k % 2 == 0 else 12), 222 + math.sin(a) * (30 if k % 2 == 0 else 12)) for k, a in enumerate(np.linspace(-math.pi / 2, 1.5 * math.pi, 11)[:-1])])
    c.fill(star, hexc('#ffe9a0')); c.glow(1200, 222, 40, '#ffd36b', 0.8); c.glow(1200, 222, 160, '#ffb850', 0.18)
    # lamp posts
    for x in (420, 1980):
        post = c.lines([(x, 880, x, 600, 8), (x, 600, x + 30, 590, 5)]); c.fill(post, hexc('#0a0e18'))
        c.glow(x + 30, 600, 40, '#ffd090', 1.0); c.add(np.exp(-(((c.xx - x) / 160) ** 2 + ((c.yy - 885) / 26) ** 2)), hexc('#ffb860'), 0.5)
    for gx in (1060, 1150, 1260, 1340):  # presents
        w = random.Random(gx).uniform(40, 70); col = random.Random(gx + 1).choice(['#c8243a', '#2a7a4a', '#d8a020', '#3a5ab8'])
        b = c.poly([(gx - w / 2, 860), (gx - w / 2, 860 - w * 0.8), (gx + w / 2, 860 - w * 0.8), (gx + w / 2, 860)]); c.fill(b, c.tex(col, 0.15, 10, gx))
        c.fill(c.poly([(gx - 4, 860), (gx - 4, 860 - w * 0.8), (gx + 4, 860 - w * 0.8), (gx + 4, 860)]), hexc('#f4e2a0'), 0.9)
    particles(c, 900, '#ffffff', 2.2, 5, 0, H, 4.0, alpha=0.9)
    c.bloom(0.75, 14, 0.45); c.grade('#0a1a40', '#ffe0b0', 1.08, 1.1, 0.95); c.vignette(0.42)
    c.save(OUT / 'christmas' / 'scene.webp')

def valentines():
    c = Canvas(51)
    c.img = c.vgrad([(0, '#1a0a3a'), (0.35, '#5a1a6a'), (0.6, '#c8407a'), (0.78, '#ff8a7a'), (0.86, '#ffc49a')], 0, 640)
    stars(c, 300, 260, 6, 0.5)
    for y, hh, sd in ((230, 50, 3), (330, 40, 4), (420, 30, 5)):
        n = c.noise(300, 6, sd, aspect=0.35); m = np.clip(n * np.exp(-((c.yy - y) / hh) ** 2) * 2 - 0.8, 0, 1)
        c.fill(ndimage.gaussian_filter(m, 3 * SS), hexc('#7a2a6a'), 0.75); c.rim(m, 1250, 560, 6, '#ffb08a', 0.6, 2, 0.4)
    sun(c, 1250, 572, 60, '#ffd6a0', 0.75)
    water(c, 600, '#b84a7a', '#1a0630', 4)
    # pier and ferris wheel (left), mountains far right
    far = c.ridge(598, 18, 300, 2); far[:300] = 640; c.fill(c.below(far) * (c.yy < 601) * (c.xx > 1500), hexc('#5a2a5a'))
    deck = c.poly([(0, 560), (900, 575), (900, 590), (0, 580)]); posts = c.lines([(x, 578, x, 640, 5) for x in range(10, 900, 36)])
    pier = np.maximum(deck, posts)
    fw = ferris(c, 420, 330, 210, '#2a0a2a', ['#ff6fb5', '#ffffff', '#ffd36b'], 3)
    rc = c.lines([(620 + i * 12, 560 - 70 * abs(math.sin(i / 6)), 632 + i * 12, 560 - 70 * abs(math.sin((i + 1) / 6)), 4) for i in range(22)] + [(620 + i * 24, 560, 620 + i * 24, 560 - 70 * abs(math.sin(i * 2 / 6)), 2) for i in range(11)])
    c.fill(np.maximum(pier, rc), hexc('#24081e'))
    reflect(c, 600, 0.6, 4, '#2a0a3a', 7)
    c.add(np.exp(-(((c.xx - 1250) / 46) ** 2)) * (c.yy > 600) * np.clip(1 - (c.yy - 600) / 440, 0, 1) * (0.6 + 0.4 * c.noise(18, 3, 2, aspect=0.1)), hexc('#ffd6a0'), 0.35)
    bokeh(c, 70, ['#ff6fb5', '#ffc2e0', '#ff4d7a'], 10, 34, 8, 60, 980, 0.5, heart=True)
    bokeh(c, 40, ['#ffd6a0'], 4, 10, 9, 500, 640, 0.6)
    c.bloom(0.72, 16, 0.5); c.grade('#3a0a3a', '#ffe0c8', 1.08, 1.12, 0.92); c.vignette(0.42)
    c.save(OUT / 'valentines' / 'scene.webp')

def easter():
    c = Canvas(61)
    c.img = c.vgrad([(0, '#1f6fc4'), (0.55, '#5aa6e6'), (1, '#b8dcf4')], 0, 600)
    sun(c, 1960, 120, 46, '#fffbe8', 0.65)
    day_clouds(c, 190, 70, 3, 1960, 120, 1.0, 320, '#8aa4cc'); day_clouds(c, 320, 44, 4, 1960, 120, 0.85, 220, '#9ab4d8')
    xs = np.linspace(0, W, 600)
    hill(c, c.ridge(560, 40, 700, 3), '#86b0b4', '#6a9aa0', 3, 160, (1960, 120), '#ffffff', 0.3, haze='#b8dcf0', hazek=0.35)
    hill(c, c.ridge(610, 46, 700, 4), '#62a870', '#3e8050', 4, 200, (1960, 120), '#f4ffe0', 0.4, 0.3, haze='#a8d0e0', hazek=0.15)
    fog(c, 600, 22, '#d0e8f0', 0.18, 6, 300)
    for x, y, h, sd in ((1560, 640, 150, 3), (980, 625, 110, 4), (1240, 630, 90, 7)):
        leafy_tree(c, x, y, h, ['#a8487a', '#d06a9a', '#f29ac0', '#ffd8ea'], sd, '#5a3a2a')
    mid = 690 + 30 * np.sin(xs / 520) - 20 * np.exp(-((xs - 1300) / 300) ** 2)
    hill(c, mid, '#5cb444', '#2e7a28', 5, 220, (1960, 120), '#f4ffc8', 0.5, 0.35, tufts=10)
    for x, y, h, sd in ((330, 760, 420, 1), (2120, 770, 400, 2)):
        leafy_tree(c, x, y, h, ['#8a3a6a', '#c05a8e', '#ec8eb8', '#ffd2e6'], sd, '#4a2e22')
    hill(c, c.ridge(860, 20, 500, 8), '#4aa636', '#1e5e18', 6, 180, (1960, 120), '#f0ffc0', 0.35, tufts=14)
    r = random.Random(5); fl = {k: [] for k in ('#ffffff', '#ffe27a', '#ff9ecb', '#c9a5ff', '#ffd0e4')}; eyes = []
    for _ in range(520):  # flowers, bigger toward the camera
        x, y = r.uniform(0, W), r.uniform(870, 1040); rr = 2 + (y - 860) / 34
        col = r.choice(list(fl)); fl[col] += [(x + math.cos(a * 1.257) * rr * 0.7, y + math.sin(a * 1.257) * rr * 0.55, rr * 0.55, rr * 0.45) for a in range(5)]; eyes.append((x, y, rr * 0.3, rr * 0.28))
    petals = np.zeros(c.img.shape[:2], np.float32)
    for col, es in fl.items(): m = c.ellipses(es); c.fill(m, hexc(col)); petals = np.maximum(petals, m)
    c.bevel(petals, (0.6, -0.8), 1.5, '#ffffff', 0.2, 0.35); c.fill(c.ellipses(eyes), hexc('#ffc830'))
    # woven basket with eggs
    bx, by = 1620, 980
    c.fill(c.ellipse(bx + 20, by + 52, 210, 26), hexc('#1a3a12'), 0.55)
    basket = np.maximum(c.ellipse(bx, by, 190, 70) * (c.yy > by - 10), c.poly([(bx - 190, by - 10), (bx + 190, by - 10), (bx + 160, by + 60), (bx - 160, by + 60)]))
    weave = (np.sin((c.xx - bx) / 6) * np.sin((c.yy - by) / 5) > 0).astype(np.float32)
    c.fill(basket, c.tex('#c08a44', 0.1, 10, 9)); c.fill(basket * weave, hexc('#7a4a1a'), 0.55); c.rim(basket, 1960, 120, 4, '#ffe8b0', 0.6, 1, 0.2)
    handle = c.lines([(bx - 180 + 360 * t, by - 10 - 220 * math.sin(math.pi * t), bx - 180 + 360 * (t + 0.02), by - 10 - 220 * math.sin(math.pi * (t + 0.02)), 14) for t in np.arange(0, 0.98, 0.02)])
    c.fill(handle, c.tex('#9a6a30', 0.25, 6, 3)); c.rim(handle, 1960, 120, 3, '#ffe8b0', 0.5, 1, 0.2)
    for x, y, rx, base, st, sd in ((1520, 930, 48, '#ff8ec4', '#ffffff', 1), (1610, 915, 50, '#8ed0ff', '#ffe27a', 2), (1705, 930, 46, '#ffe27a', '#c9a5ff', 3), (1660, 955, 40, '#b9f0a0', '#ff8ec4', 4)):
        egg(c, x, y, rx, rx * 1.3, base, st, sd, (0.6, -0.8))
    c.fill(basket * (c.yy > by + 4), c.tex('#c08a44', 0.1, 10, 9)); c.fill(basket * weave * (c.yy > by + 4), hexc('#7a4a1a'), 0.55); c.bevel(basket * (c.yy > by + 4), (0.6, -0.8), 6, '#ffe8b0', 0.3, 0.4)
    for x, y, rx, base, st, sd in ((560, 1000, 44, '#c9a5ff', '#ffffff', 5), (760, 1018, 38, '#ffb38a', '#9ed8ff', 6), (2240, 1005, 42, '#9ed8ff', '#ff9ecb', 7)):
        c.fill(c.ellipse(x + 8, y + rx * 1.2, rx * 1.1, rx * 0.25), hexc('#1a3a12'), 0.5); egg(c, x, y, rx, rx * 1.3, base, st, sd, (0.6, -0.8))
    grass = c.grass(np.full(60, 1046.0), 70, 9, 2.6, 0.7); c.fill(ndimage.gaussian_filter(grass, 2 * SS), hexc('#2a6a1e'))
    particles(c, 70, '#ffd0e4', 3, 7, 0, 900, 5, 'petal', 0.9, ['#ffd0e4', '#ffffff', '#f29ac0'])
    c.bloom(0.85, 16, 0.3); c.grade('#1a3a6a', '#fff4d8', 1.05, 1.08, 1.0, 'knee'); c.vignette(0.3)
    c.save(OUT / 'easter' / 'scene.webp')

def stpatricks():
    c = Canvas(71)
    c.img = c.vgrad([(0, '#0f3d7a'), (0.4, '#2f78c0'), (0.78, '#8cc4e4'), (1, '#e6f0dc')], 0, 600)
    SX, SY = 520, 170
    sun(c, SX, SY, 46, '#fff1c4', 1.0)
    c.glow(SX, SY, 520, '#ffe8a8', 0.22, 1.3, False)
    cl = day_clouds(c, 165, 120, 5, SX, SY, 1.0, 360, '#56688a', '#fbfaf2', 0.78)
    day_clouds(c, 330, 50, 11, SX, SY, 0.8, 240, '#7a90b4', '#f4f6f4', 0.95)
    c.godrays(SX, SY, np.clip(cl * 1.5, 0, 1), '#fff4c8', 0.5, r=300)
    # rainbow: centre to the right so its left foot comes down on the pot of gold
    RX, RY, RR = 1620, 1010, 840
    d = np.sqrt((c.xx - RX) ** 2 + (c.yy - RY) ** 2)
    fade = np.clip((RY - c.yy) / 140, 0, 1) * (0.55 + 0.45 * np.clip((c.xx - 600) / 900, 0, 1))
    inside = np.clip((RR - 150 - d) / 60, 0, 1) * np.clip((d - (RR - 520)) / 200, 0, 1)
    c.fill(inside * fade, hexc('#ffffff'), 0.08)
    for i, col in enumerate(['#ff2a2a', '#ff8a1a', '#ffe02a', '#2ad04a', '#2a8aff', '#4a3aff', '#9a3aff']):
        c.fill(np.exp(-((d - (RR - i * 19)) / 11) ** 2) * fade, hexc(col), 0.55)
    xs = np.linspace(0, W, 600)
    hill(c, c.ridge(560, 55, 800, 3), '#6f9ab0', '#5a8a9a', 3, 200, (SX, SY), '#ffffff', 0.25, haze='#a8c8dc', hazek=0.35)
    fog(c, 590, 18, '#d8eaf0', 0.12, 13, 280)
    mid = c.ridge(640, 60, 650, 4)
    hill(c, mid, '#5ab45a', '#2e7a3c', 4, 260, (SX, SY), '#f4ffd0', 0.5, 0.45, haze='#9ac4c0', hazek=0.18)
    # hedgerow trees and a whitewashed cottage with a thatched roof on the middle hill
    for x, h, sd in ((260, 120, 21), (420, 90, 22), (1180, 110, 23), (2240, 130, 24), (2330, 100, 25)):
        leafy_tree(c, x, float(np.interp(x, xs, mid)) + 18, h, ['#123d22', '#1e5a2e', '#2f7a3a', '#5aa04a'], sd, '#2a2016', (-0.6, -0.8))
    hx = 1960; hy = float(np.interp(hx, xs, mid)) + 34
    wall = c.poly([(hx - 120, hy), (hx - 120, hy - 86), (hx + 120, hy - 86), (hx + 120, hy)])
    gable = c.poly([(hx + 120, hy), (hx + 120, hy - 86), (hx + 168, hy - 140), (hx + 200, hy - 86), (hx + 200, hy)])
    c.fill(wall, c.tex('#f2ecdc', 0.06, 30, 2)); c.fill(gable, c.tex('#c8c2b4', 0.06, 30, 3))
    roof = c.poly([(hx - 140, hy - 80), (hx - 100, hy - 150), (hx + 150, hy - 150), (hx + 176, hy - 132), (hx + 124, hy - 80)])
    thatch = c.tex('#b08a44', 0.25, 6, 4) * (0.8 + 0.3 * (np.sin((c.xx - hx) / 2.2 + c.noise(8, 2, 5) * 6) * 0.5 + 0.5))[..., None]
    c.fill(roof, thatch); c.bevel(roof, (-0.6, -0.8), 5, '#fff2c0', 0.35, 0.3)
    c.fill(c.poly([(hx - 140, hy - 80), (hx + 124, hy - 80), (hx + 120, hy - 72), (hx - 136, hy - 72)]), hexc('#5a4420'), 0.6)
    c.fill(c.poly([(hx - 18, hy), (hx - 18, hy - 52), (hx + 18, hy - 52), (hx + 18, hy)]), hexc('#1e6a34'))
    for wx in (hx - 80, hx + 52): c.fill(c.poly([(wx, hy - 30), (wx, hy - 60), (wx + 30, hy - 60), (wx + 30, hy - 30)]), hexc('#2a3a40')); lit_window(c, wx + 15, hy - 45, 24, 24, '#ffcc70', 0.35)
    c.fill(c.poly([(hx + 60, hy - 140), (hx + 60, hy - 178), (hx + 84, hy - 178), (hx + 84, hy - 140)]), c.tex('#8a8478', 0.2, 4, 6))
    smoke = c.noise(30, 4, 8) * np.exp(-((c.xx - hx - 72 - (hy - 178 - c.yy) * 0.35) / (14 + (hy - 178 - c.yy) * 0.25)) ** 2) * (c.yy < hy - 178) * np.clip((c.yy - (hy - 420)) / 200, 0, 1)
    c.fill(np.clip(smoke * 1.4, 0, 1), hexc('#e8eef0'), 0.5)
    c.fill(c.ellipse(hx + 40, hy + 6, 210, 12), hexc('#14402a'), 0.35)
    near = 780 + 36 * np.sin(xs / 600) - 28 * np.exp(-((xs - 600) / 400) ** 2)
    hill(c, near, '#46c05a', '#1c6a30', 5, 260, (SX, SY), '#f8ffc8', 0.6, 0.35, tufts=10)
    # dry-stone wall following the field: dark base, then stones in three tones, lit in one pass
    r = random.Random(3); wy = near + 92
    c.fill(c.poly([(x, float(np.interp(x, xs, wy)) + 4) for x in np.arange(0, W + 30, 30)] + [(x, float(np.interp(x, xs, wy)) - 40) for x in np.arange(W, -30, -30)]), hexc('#3a3a32'))
    groups = [[], [], []]
    for row, (dy, ry) in enumerate(((-10, 12), (-30, 10), (-44, 7))):
        x = r.uniform(-20, 0)
        while x < W + 20:
            rx = r.uniform(12, 22) - row * 2; y = float(np.interp(x, xs, wy)) + dy
            groups[r.randrange(3)].append((x, y + r.uniform(-2, 2), rx, ry + r.uniform(-2, 2))); x += rx * 1.75
    stones = np.zeros(c.img.shape[:2], np.float32)
    for g, col in zip(groups, ['#a8a698', '#8c8a7c', '#bdb8a4']):
        m = c.ellipses(g); c.fill(m, c.tex(col, 0.22, 4, len(g))); stones = np.maximum(stones, m)
    c.bevel(stones, (-0.5, -0.85), 3, '#fffbe8', 0.4, 0.5)
    c.fill(ndimage.gaussian_filter(c.grass(wy + 6, 22, 31, 3.4, 0.5), 0.6 * SS), hexc('#2e8a3e'))
    fg = 940 + 10 * np.sin(xs / 300)
    hill(c, fg, '#38b04c', '#0f4a1e', 6, 140, (SX, SY), '#f0ffc0', 0.3, tufts=14)
    # clovers, bigger toward the camera, batched per tint
    tints = {'#3ccc5c': [], '#26a644': [], '#52e070': [], '#1c8a38': []}
    for _ in range(600):
        x, y = r.uniform(0, W), r.uniform(935, 1060); sz = 3 + (y - 925) / 14; tk = r.choice(list(tints))
        for a in (0, 2.1, 4.2): tints[tk].append((x + math.cos(a - 1.57) * sz * 0.85, y + math.sin(a - 1.57) * sz * 0.8, sz * 0.66, sz * 0.6))
    cl_all = np.zeros(c.img.shape[:2], np.float32)
    for tk, es in tints.items():
        m = c.ellipses(es); c.fill(m, hexc(tk)); cl_all = np.maximum(cl_all, m)
    c.bevel(cl_all, (-0.5, -0.85), 2.5, '#f0ffc8', 0.35, 0.4)
    # pot of gold at the rainbow's foot
    px, py = 790, 985
    c.glow(px, py - 80, 220, '#ffd84a', 0.25)
    c.fill(c.ellipse(px + 30, py + 70, 170, 24), hexc('#06280e'), 0.6)
    pot = c.ellipse(px, py, 124, 88); c.fill(pot, shade_ball(c, px, py, 124, 88, '#18181c', (-0.6, -0.7)))
    for lx in (-80, 80): c.fill(c.ellipse(px + lx, py + 78, 22, 12), hexc('#141416'))
    c.fill(c.ellipse(px, py - 64, 128, 26), hexc('#0a0a0c')); c.fill(c.ellipse(px, py - 64, 128, 26) - c.ellipse(px, py - 62, 116, 21), hexc('#4a4a52'))
    c.fill(c.ellipse(px, py - 70, 112, 28), hexc('#a8761a'))
    for layer in range(4):  # coins heaped in layers, each one outlined so they read separately
        cs = [(px + r.uniform(-100 + layer * 14, 100 - layer * 14), py - 70 - layer * 12 + r.uniform(-10, 10), r.uniform(15, 19), r.uniform(6, 8.5)) for _ in range(34 - layer * 6)]
        c.fill(c.ellipses([(x, y + 1.5, rx + 2, ry + 2) for x, y, rx, ry in cs]), hexc('#7a4e08'))
        face = c.ellipses(cs); c.fill(face, c.tex('#f4c43c', 0.12, 3, 7 + layer))
        c.fill(np.clip(face - c.ellipses([(x, y, rx * 0.7, ry * 0.62) for x, y, rx, ry in cs]), 0, 1), hexc('#ffe27a'), 0.6)
        c.bevel(face, (-0.5, -0.85), 1.5, '#fffbe0', 0.5, 0.25)
    for _ in range(26):
        sx, sy = px + r.uniform(-120, 120), py - 110 + r.uniform(-90, 30); c.glow(sx, sy, 3.5, '#ffffff', 1.3)
    particles(c, 30, '#fff8d0', 2, 9, 200, 900, 2, 'dot', 0.4)
    c.bloom(0.8, 14, 0.35); c.grade('#0a2a3a', '#fff4d0', 1.06, 1.1, 1.0, 'knee'); c.vignette(0.32)
    c.save(OUT / 'stpatricks' / 'scene.webp')

def independence():
    c = Canvas(81)
    c.img = c.vgrad([(0, '#02040e'), (0.6, '#0a1440'), (1, '#1a2a6a')], 0, 640)
    stars(c, 600, 420, 8, 0.6)
    for x, y, rad, col, sd in ((520, 230, 190, '#ff5a5a', 1), (1180, 170, 240, '#ffffff', 2), (1820, 240, 200, '#5a8cff', 3), (860, 330, 120, '#ffd36b', 4), (1560, 340, 130, '#ff5a5a', 5), (2160, 150, 110, '#ffffff', 6)):
        firework(c, x, y, rad, col, sd, 110, 0.9)
    smoke = c.noise(200, 5, 9, aspect=0.5) * np.exp(-((c.yy - 300) / 160) ** 2)
    c.fill(np.clip(smoke - 0.35, 0, 1), hexc('#4a5a8a'), 0.35)
    water(c, 640, '#1a2a6a', '#02040e', 3)
    reflect(c, 640, 0.75, 5, '#020616', 6)
    deck = c.poly([(1500, 600), (W, 590), (W, 606), (1500, 614)]); posts = c.lines([(x, 610, x, 690, 6) for x in range(1510, W, 40)])
    fw = ferris(c, 2100, 420, 150, '#05070f', ['#ff5a5a', '#ffffff', '#5a8cff'], 7, 0.8)
    c.fill(np.maximum(deck, posts), hexc('#05070f'))
    beach = c.below(c.ridge(820, 10, 600, 4)); c.fill(beach, c.vgrad([(0, '#1a1a2a'), (1, '#0a0a12')], 820, H))
    r = random.Random(3); crowd = np.zeros(c.img.shape[:2], np.float32)
    for x in np.arange(60, W, 46):
        if r.random() < 0.75: crowd = np.maximum(crowd, person(c, x + r.uniform(-10, 10), 1040 - r.uniform(0, 30), r.uniform(1.6, 2.2), r.random() if r.random() < 0.4 else 0))
    flags = []
    for fx in (380, 1320, 2010):
        flags.append(c.lines([(fx, 1000, fx, 860, 3)])); flags.append(c.poly([(fx, 862), (fx + 54, 868), (fx + 54, 900), (fx, 894)]))
    c.fill(np.maximum.reduce([crowd] + flags), hexc('#020308'))
    c.bloom(0.65, 18, 0.8); c.grade('#0a1440', '#ffe8d0', 1.08, 1.15); c.vignette(0.45)
    c.save(OUT / 'independence' / 'scene.webp')

def thanksgiving():
    c = Canvas(91)
    c.img = c.vgrad([(0, '#2a1e4a'), (0.35, '#a04a3a'), (0.65, '#e08a3a'), (0.88, '#ffcc70')], 0, 600)
    sun(c, 1700, 520, 64, '#fff0c0', 0.7)
    day_clouds(c, 230, 60, 3, 1700, 520, 0.7, 280, '#8a4a5a', '#ffc090', 1.0)
    hill(c, c.ridge(560, 40, 600, 3), '#a8606a', '#7a4050', 3, 160, (1700, 520), '#ffc070', 0.5, haze='#e09a7a', hazek=0.35)
    hill(c, c.ridge(620, 40, 600, 4), '#8a4a2a', '#4a2414', 4, 160, (1700, 520), '#ffc070', 0.6, 0.3, haze='#d08050', hazek=0.15)
    fog(c, 600, 30, '#e09060', 0.18, 4, 300)
    # farmhouse and barn
    barn = c.poly([(760, 690), (760, 560), (840, 500), (920, 560), (920, 690)]); c.fill(barn, c.tex('#8a2418', 0.08, 30, 2) * (0.85 + 0.15 * (np.sin(c.xx / 3.2) > -0.7))[..., None]); c.rim(barn, 1700, 520, 3, '#ffd090', 0.8, 1, 0.3)
    c.fill(c.poly([(750, 562), (840, 492), (930, 562), (920, 566), (840, 506), (760, 566)]), hexc('#3a2a20'))
    c.fill(c.poly([(810, 690), (810, 620), (870, 620), (870, 690)]), hexc('#4a1410'))
    house = c.poly([(980, 690), (980, 590), (1180, 590), (1180, 690)]); roof = c.poly([(960, 594), (1080, 520), (1200, 594)])
    c.fill(np.maximum(house, roof), c.tex('#d8c8b0', 0.05, 30, 3)); c.fill(roof, c.tex('#4a3028', 0.1, 20, 4)); c.rim(np.maximum(house, roof), 1700, 520, 3, '#ffd090', 0.7, 1, 0.3)
    for wx in (1000, 1060, 1120): lit_window(c, wx, 620, 34, 40, '#ffc060', 0.9)
    c.fill(c.lines([(1150, 520, 1150, 556, 14)]), hexc('#5a3a2a'))
    smoke = ndimage.gaussian_filter(c.lines([(1150 + 30 * math.sin(t / 3), 520 - t * 6, 1150 + 30 * math.sin((t + 1) / 3), 520 - (t + 1) * 6, 10 + t) for t in range(30)]), 8 * SS)
    c.fill(smoke, hexc('#e0c8b8'), 0.35)
    for x, y, h, sd in ((180, 760, 520, 1), (520, 720, 360, 2), (1400, 720, 380, 3), (1980, 760, 480, 4), (2300, 740, 420, 5), (660, 700, 220, 6)):
        leafy_tree(c, x, y, h, ['#7a1e10', '#c84a18', '#f08a28', '#ffc24a'], sd, '#3a2010', (0.8, -0.4))
    field = c.below(c.ridge(770, 16, 500, 6)); c.fill(field, c.vgrad([(0, '#c89040'), (0.4, '#9a6224'), (1, '#4a2a10')], 770, H) * (0.95 + 0.1 * c.noise(40, 4, 7))[..., None])
    c.add(np.exp(-(((c.xx - 1700) / 800) ** 2 + ((c.yy - 780) / 120) ** 2)) * field, hexc('#ffb050'), 0.4, False)
    # crop rows converging on the horizon under the sun: lit tops, dark furrows
    VX, VY = 1700, 762; ang = np.arctan2(c.xx - VX, np.maximum(c.yy - VY, 1)); rows = np.sin(ang * 46)
    depth = np.clip((c.yy - VY) / 280, 0, 1)
    c.fill(field * np.clip(-rows * 1.6, 0, 1) * depth, hexc('#3a200c'), 0.55)
    c.add(field * np.clip(rows - 0.55, 0, 1) * depth * np.exp(-((c.xx - VX) / 1300) ** 2), hexc('#ffc060'), 0.35, False)
    stub = ndimage.gaussian_filter(c.grass(np.full(60, 1046.0), 50, 13, 3.0, 0.3), 0.6 * SS); c.fill(stub, hexc('#5a3410'))
    fence = c.lines([(x, 880, x, 820, 6) for x in range(40, 1100, 90)] + [(40, 840, 1100, 836, 5), (40, 862, 1100, 858, 5)])
    c.fill(fence, hexc('#4a2a14')); c.rim(fence, 1700, 520, 2, '#ffd090', 0.5, 0.6, 0)
    for x, y, s in ((1500, 960, 1.6), (1700, 990, 1.2), (1860, 960, 1.4)):  # hay bales
        c.fill(c.ellipse(x - 40 * s, y + 64 * s, 110 * s, 16 * s), hexc('#2a1408'), 0.5)
        b = c.ellipse(x, y, 90 * s, 70 * s)
        rr = np.sqrt(((c.xx - x) / (90 * s)) ** 2 + ((c.yy - y) / (70 * s)) ** 2); th = np.arctan2(c.yy - y, c.xx - x)
        spiral = 0.5 + 0.5 * np.sin(rr * 60 + th * 1.0 + c.noise(5, 3, int(x)) * 4)
        straw = hexc('#e2b458')[None, None, :] * (0.86 + 0.14 * spiral[..., None] + 0.16 * (c.noise(3, 2, int(x) + 1)[..., None] - 0.5))
        c.fill(b, straw); c.bevel(b, (0.8, -0.55), 6 * s, '#ffe6a8', 0.5, 0.5)
    for x, y, s in ((560, 1000, 1.2), (690, 1015, 0.9), (420, 1020, 0.8)):
        p = c.ellipse(x, y, 60 * s, 44 * s); c.fill(p, shade_ball(c, x, y, 60 * s, 44 * s, '#e0681a', (0.7, -0.6)))
        ribs = 0.5 + 0.5 * np.cos((c.xx - x) / (60 * s) * math.pi * 3.2); c.fill(p * (1 - ribs) ** 3, hexc('#8a3a08'), 0.55)
        c.fill(c.lines([(x, y - 40 * s, x + 6 * s, y - 60 * s, 8 * s)]), hexc('#4a5a1a'))
    particles(c, 160, '#e8701a', 4, 5, 0, H, 5, 'leaf', 0.95, ['#c84a18', '#f08a28', '#ffc24a', '#7a1e10'])
    c.bloom(0.8, 16, 0.4); c.grade('#4a1a3a', '#ffe0b0', 1.06, 1.08, 0.98, 'knee'); c.vignette(0.42)
    c.save(OUT / 'thanksgiving' / 'scene.webp')

def new_years_eve():
    c = Canvas(101)
    c.img = c.vgrad([(0, '#01030c'), (0.6, '#081438'), (1, '#1a2a5a')], 0, 700)
    stars(c, 500, 400, 9, 0.5)
    for x, y, rad, col, sd in ((400, 200, 200, '#ffd36b', 1), (1000, 140, 160, '#ffffff', 2), (1660, 190, 230, '#ffd36b', 3), (2150, 260, 150, '#8fd8ff', 4), (1320, 300, 110, '#ff9ac1', 5)):
        firework(c, x, y, rad, col, sd, 120, 0.85)
    skyline(c, 760, 160, 430, 0, W, 21, '#03060f', '#ffd890', 0.4, 50, 120)
    tower = c.poly([(1180, 760), (1180, 260), (1210, 220), (1240, 260), (1240, 760)]); c.fill(tower, hexc('#03060f'))
    for y in range(280, 740, 26):
        l = c.poly([(1186, y), (1234, y), (1234, y + 4), (1186, y + 4)]); c.add(l, hexc('#ffd36b'), 1); c.add(ndimage.gaussian_filter(l, 6 * SS), hexc('#ffd36b'), 1.4)
    c.glow(1210, 225, 50, '#ffffff', 1.2); c.glow(1210, 225, 180, '#ffd36b', 0.4)
    fog(c, 760, 40, '#3a4a8a', 0.4, 4, 300)
    plaza = c.below(np.full(10, 790.0)); c.fill(plaza, c.vgrad([(0, '#141a30'), (1, '#05070f')], 790, H))
    r = random.Random(4); crowd = np.zeros(c.img.shape[:2], np.float32)
    for x in np.arange(30, W, 40):
        if r.random() < 0.8: crowd = np.maximum(crowd, person(c, x + r.uniform(-10, 10), 1060 - r.uniform(0, 50), r.uniform(1.8, 2.4), r.random() if r.random() < 0.5 else 0))
    c.fill(crowd, hexc('#010205'))
    bokeh(c, 90, ['#ffd36b', '#ffffff', '#8fd8ff', '#ff9ac1'], 6, 26, 6, 0, H, 0.35)
    particles(c, 300, '#ffd36b', 3, 8, 0, H, 4, 'leaf', 0.9, ['#ffd36b', '#ffffff', '#8fd8ff', '#ff9ac1', '#c0c8d8'])
    c.bloom(0.65, 18, 0.8); c.grade('#081030', '#ffe8c0', 1.08, 1.12); c.vignette(0.45)
    c.save(OUT / 'new_years_eve' / 'scene.webp')

def new_years():
    c = Canvas(111)
    c.img = c.vgrad([(0, '#0e1440'), (0.35, '#3a2a6a'), (0.62, '#b0486a'), (0.8, '#f0803a'), (0.92, '#ffc06a')], 0, 590)
    SX, SY = 1560, 590
    for y, hh, sd in ((160, 60, 3), (300, 34, 4), (420, 22, 5)):
        n = c.noise(320, 6, sd, aspect=0.35); m = np.clip(n * np.exp(-((c.yy - y) / hh) ** 2) * 2.1 - 0.85, 0, 1)
        m = ndimage.gaussian_filter(m, 3 * SS); c.fill(m, hexc('#3a2a5a'), 0.85); c.rim(m, SX, SY, 7, '#ffb070', 0.8, 2, 0.5)
    sun(c, SX, SY, 58, '#fff0c8', 0.85)
    hxs = np.linspace(0, W, 600); prof = 470 + 0.00012 * hxs ** 2
    prof = prof + 18 * np.sin(hxs / 70) * np.exp(-hxs / 500) + np.interp(hxs, np.linspace(0, W, 60), np.random.default_rng(9).normal(0, 6, 60))
    prof = np.where(hxs < 820, prof, 700)   # headland tapering into the sea on the left
    head = c.below(prof) * (c.yy < 593)
    c.fill(head, c.vgrad([(0, '#3a2440'), (1, '#1a1026')], 460, 592) * (0.9 + 0.2 * c.noise(14, 4, 12))[..., None])
    c.add(np.exp(-np.clip(c.yy - np.interp(c.xx, hxs, prof), 0, None) / 10) * head * np.exp(-((c.xx - 820) / 500) ** 2), hexc('#ff9a60'), 0.35, False)
    water(c, 592, '#6a3a5a', '#0e1440', 6)
    reflect(c, 592, 0.55, 3, '#0e1440', 8)
    glit = np.exp(-(((c.xx - SX) / (30 + (c.yy - 592) * 0.7)) ** 2)) * (c.yy > 592) * np.clip(1 - (c.yy - 592) / 260, 0, 1) * np.clip(c.noise(7, 3, 4, aspect=0.12) * 2.2 - 0.8, 0, 1)
    c.add(glit, hexc('#ffd890'), 1.6)
    pier = np.maximum(c.poly([(0, 560), (760, 572), (760, 582), (0, 572)]), c.lines([(x, 578, x, 620, 5) for x in range(10, 760, 40)]))
    c.fill(pier, hexc('#1a1028')); lanterns(c, [(x, 556 + x * 0.016, 0.5) for x in range(30, 760, 60)], '#ffd0a0', 2.4)
    xs = np.linspace(0, W, 600)
    for k, (base, a) in enumerate(((700, 0.5), (745, 0.7), (800, 0.9))):  # rolling surf lines
        line = base + 10 * np.sin(xs / (170 + k * 40) + k) + 5 * np.sin(xs / 47 + k * 2)
        crest = c.below(line - 2) * (1 - c.below(line + 2)) * np.clip(c.noise(30, 3, 20 + k, aspect=0.3) * 2.4 - 0.7, 0, 1)
        white = c.below(line) * (1 - c.below(line + 14 + k * 8)) * np.clip(c.noise(6, 3, 30 + k, aspect=0.4) * 2 - 0.6, 0, 1) * np.clip(c.noise(30, 3, 20 + k, aspect=0.3) * 2.4 - 0.7, 0, 1)
        c.fill(ndimage.gaussian_filter(c.below(line + 3) * (1 - c.below(line + 18)), 3 * SS), hexc('#1a1030'), 0.25)   # trough shadow ahead of each crest
        c.fill(ndimage.gaussian_filter(white, 0.8 * SS), hexc('#f8e8ec'), a * 0.55)
        c.fill(ndimage.gaussian_filter(crest, 0.9 * SS), hexc('#fff4ec'), a * 0.9)
        c.add(ndimage.gaussian_filter(crest, 6 * SS) * np.exp(-((c.xx - SX) / 500) ** 2), hexc('#ffc8a0'), 0.35, False)
    shore = 850 + 22 * np.sin(xs / 380) + 6 * np.sin(xs / 90)
    sand = c.below(shore); c.fill(sand, c.vgrad([(0, '#b07a6a'), (1, '#4a2e3a')], 840, H) * (0.93 + 0.14 * c.noise(5, 3, 4))[..., None])
    wet = c.below(shore) * (1 - c.below(shore + 70))
    c.fill(wet, np.flip(c.img, 0) * 0 + hexc('#d08a6a')[None, None, :], 0.0)
    c.add(wet * np.exp(-(((c.xx - SX) / 160) ** 2)), hexc('#ffc890'), 0.5, False); c.fill(wet, hexc('#2a1a30'), 0.25)
    foam = c.below(shore - 6) * (1 - c.below(shore + 5)); c.fill(ndimage.gaussian_filter(foam, 1.5 * SS), hexc('#ffffff'), 0.9)
    tower = np.maximum.reduce([c.lines([(300, 930, 320, 820, 6), (380, 930, 360, 820, 6), (300, 930, 380, 870, 3), (380, 930, 300, 870, 3)]),
                               c.poly([(290, 825), (390, 825), (390, 760), (290, 760)]), c.poly([(280, 762), (340, 730), (400, 762)])])
    c.fill(tower, hexc('#1a1020')); c.rim(tower, SX, SY, 2, '#ffb070', 0.6, 0.6, 0.2)
    figs = np.maximum.reduce([person(c, 1240, 812, 1.3, 1.0, 0.9, 0.3), person(c, 1330, 806, 1.2, 0.8, 0.8, 0.3), person(c, 1420, 798, 1.25, 1.0, 1.0, 0.4),
                              person(c, 1760, 840, 1.45, 0.2, 0.0), person(c, 1830, 848, 1.4, 1.0, 0.0)])
    c.fill(figs, hexc('#140a1c')); c.rim(figs, SX, SY, 2, '#ffc080', 0.9, 0.6, 0.3)
    particles(c, 120, '#ffffff', 2.2, 4, 770, 830, 2, 'dot', 0.8)
    r = random.Random(4)
    for x in range(1500, 2300, 46):
        y = 950 + 40 * math.sin(x / 210) + (10 if (x // 46) % 2 else 0); c.fill(c.ellipse(x, y, 8, 4), hexc('#3a2230'), 0.6)
    c.bloom(0.82, 16, 0.45); c.grade('#1a1a5a', '#fff0d8', 1.08, 1.1, 1.0, 'knee'); c.vignette(0.42)
    c.save(OUT / 'new_years' / 'scene.webp')

def memorial():
    c = Canvas(121)
    c.img = c.vgrad([(0, '#1a2a5a'), (0.4, '#6a5a8a'), (0.7, '#e08a6a'), (0.88, '#ffc890')], 0, 640)
    for y, hh, sd in ((180, 60, 3), (300, 40, 4)):
        n = c.noise(320, 6, sd, aspect=0.35); m = np.clip(n * np.exp(-((c.yy - y) / hh) ** 2) * 2 - 0.85, 0, 1)
        c.fill(ndimage.gaussian_filter(m, 3 * SS), hexc('#5a4a7a'), 0.8); c.rim(m, 1200, 640, 8, '#ffc890', 0.6, 2, 0.4)
    sun(c, 1200, 640, 70, '#ffe0b0', 0.55, False)
    far = c.ridge(620, 24, 600, 3); c.fill(c.below(far), hexc('#4a3a5a'))
    ob = c.poly([(1180, 640), (1188, 330), (1200, 300), (1212, 330), (1220, 640)]); c.fill(ob, hexc('#2a2034')); c.rim(ob, 1200, 700, 2, '#ffd0a0', 0.5, 0.6, 0.2)
    lawn = c.below(np.full(10, 650.0)); c.fill(lawn, c.vgrad([(0, '#3a4a2a'), (1, '#1a2a12')], 650, H))
    # rows of small flags in perspective
    r = random.Random(7)
    for row in range(14):
        t = row / 13; y = 670 + 360 * t ** 1.6; s = 0.35 + 1.6 * t ** 1.5; n = int(46 - row * 2.2); spacing = W / n
        for k in range(n + 1):
            x = k * spacing + (row % 2) * spacing / 2 + r.uniform(-3, 3)
            pole = c.lines([(x, y, x, y - 46 * s, max(1, 1.4 * s))]); c.fill(pole, hexc('#1a1410'))
            fl = c.poly([(x, y - 46 * s), (x + 22 * s, y - 44 * s), (x + 22 * s, y - 32 * s), (x, y - 34 * s)])
            stripes = (np.sin((c.yy - (y - 46 * s)) / (2.2 * s) * math.pi) > 0).astype(np.float32)
            c.fill(fl, hexc('#c8283a')); c.fill(fl * stripes, hexc('#f4f0e8'), 0.85)
            c.fill(fl * (c.xx < x + 9 * s) * (c.yy < y - 39 * s), hexc('#2a3a8a'))
    # big flag on a pole
    pole = c.lines([(560, 1040, 560, 300, 8)]); c.fill(pole, hexc('#14100c')); c.glow(560, 296, 8, '#ffd890', 1)
    wave = lambda u, v: (560 + u * 300, 310 + v * 180 + 22 * math.sin(u * 5))
    flag = c.poly([wave(u, 0) for u in np.linspace(0, 1, 30)] + [wave(u, 1) for u in np.linspace(1, 0, 30)])
    stripes = (np.sin((c.yy - 310 - 22 * np.sin((c.xx - 560) / 300 * 5)) / 180 * 13 * math.pi) > 0).astype(np.float32)
    c.fill(flag, hexc('#b8202f')); c.fill(flag * stripes, hexc('#f4f0e8'), 0.9)
    canton = flag * (c.xx < 690) * ((c.yy - 310 - 22 * np.sin((c.xx - 560) / 300 * 5)) < 97)
    c.fill(canton, hexc('#1f2f7a'))
    c.fill(flag, hexc('#000000'), 0.0); c.img *= (1 - flag * (0.25 * (np.sin((c.xx - 560) / 300 * 5 + 1) * 0.5 + 0.5)))[..., None]
    for x, y, s in ((1600, 990, 1.4), (1720, 1010, 1.1), (1840, 985, 1.3), (1960, 1005, 1.0)):  # candles
        cm = c.poly([(x - 9 * s, y), (x - 9 * s, y - 50 * s), (x + 9 * s, y - 50 * s), (x + 9 * s, y)]); c.fill(cm, c.tex('#f4ead2', 0.1, 4, int(x)))
        fl = c.ellipse(x, y - 62 * s, 5 * s, 11 * s); c.fill(fl, hexc('#ffe9a0')); c.glow(x, y - 62 * s, 30 * s, '#ffb050', 0.5)
        c.add(np.exp(-(((c.xx - x) / (90 * s)) ** 2 + ((c.yy - y) / (16 * s)) ** 2)), hexc('#ffb050'), 0.35)
    for _ in range(140):  # poppies
        x, y = r.uniform(0, W), r.uniform(940, 1040); rr = 5 + (y - 940) / 14
        c.fill(c.ellipse(x, y, rr, rr * 0.8), hexc('#d8202a'), 0.95); c.fill(c.ellipse(x, y, rr * 0.3, rr * 0.3), hexc('#1a0a0a'))
    c.bloom(0.8, 14, 0.4); c.grade('#1a2050', '#ffe0c0', 1.08, 1.08, 0.95); c.vignette(0.42)
    c.save(OUT / 'memorial' / 'scene.webp')

def labor():
    c = Canvas(131)
    c.img = c.vgrad([(0, '#141a3a'), (0.35, '#4a3a5a'), (0.62, '#c05a3a'), (0.8, '#f09040'), (0.92, '#ffc860')], 0, 700)
    SX, SY = 1130, 610
    for y, hh, sd in ((200, 50, 3), (330, 30, 4)):
        n = c.noise(320, 6, sd, aspect=0.35); m = np.clip(n * np.exp(-((c.yy - y) / hh) ** 2) * 2 - 0.85, 0, 1)
        m = ndimage.gaussian_filter(m, 3 * SS); c.fill(m, hexc('#3a2a3a'), 0.8); c.rim(m, SX, SY, 7, '#ffb060', 0.7, 2, 0.5)
    sun(c, SX, SY, 92, '#fff0c0', 1.0)
    occ = np.zeros(c.img.shape[:2], np.float32)
    sk = skyline(c, 700, 50, 220, 0, W, 31, '#2a1e2a', '#ffc070', 0.1, 50, 120); occ = np.maximum(occ, sk)
    c.fill(c.below(np.full(10, 700.0)), c.vgrad([(0, '#2a1e2a'), (1, '#3e2a2a')], 700, 790))   # far ground the skyline stands on
    fog(c, 690, 30, '#c07050', 0.25, 7, 300)
    frame = []
    for x in range(860, 1421, 80): frame.append((x, 760, x, 250, 12))
    for y in range(250, 761, 64): frame.append((860, y, 1420, y, 9))
    for x in range(860, 1420, 80):
        for y in range(250, 760, 64):
            if (x // 80 + y // 64) % 3 == 0: frame.append((x, y, x + 80, y + 64, 3.5))
    fm = c.lines(frame); c.fill(fm, hexc('#120e16')); c.rim(fm, SX, SY, 2.5, '#ffd090', 1.0, 0.6, 0.5); occ = np.maximum(occ, fm)
    for cx, h, jib, flip in ((520, 600, 560, False), (1860, 680, 640, True)):
        m = crane(c, cx, 800, h, jib, '#100c14', 3, flip); c.rim(m, SX, SY, 2, '#ffd090', 0.9, 0.5, 0.3); occ = np.maximum(occ, m)
    workers = np.maximum.reduce([person(c, 940 + i * 160, 314 + (i % 2) * 128, 0.85, (i % 3) / 3) for i in range(4)])
    c.fill(workers, hexc('#0c0a10')); c.rim(workers, SX, SY, 2, '#ffd090', 0.9, 0.5, 0.2); occ = np.maximum(occ, workers)
    c.godrays(SX, SY, occ, '#ffc070', 0.55, r=230)
    r = random.Random(7)
    for jx, jy in ((1020, 506), (1260, 378), (1180, 634)):  # welding sparks
        c.glow(jx, jy, 10, '#ffffff', 1.6); c.glow(jx, jy, 40, '#8fd8ff', 0.5)
        segs = []
        for _ in range(26):
            a = r.uniform(0.2, math.pi - 0.2); l = r.uniform(12, 46); segs.append((jx, jy, jx + math.cos(a) * l * r.choice((-1, 1)), jy + math.sin(a) * l, 1.2))
        sp = c.lines(segs); c.add(sp, hexc('#ffd890'), 1.4); c.add(ndimage.gaussian_filter(sp, 3 * SS), hexc('#ffb040'), 1.2)
    lot = c.below(np.full(10, 790.0)); c.fill(lot, c.vgrad([(0, '#4a3026'), (1, '#140e0c')], 790, H) * (0.9 + 0.2 * c.noise(30, 4, 4))[..., None])
    c.add(np.exp(-(((c.xx - SX) / 500) ** 2 + ((c.yy - 800) / 40) ** 2)) * lot, hexc('#ff9a40'), 0.35, False)
    gravel = c.ellipses([(r.uniform(0, W), y, 2 + (y - 790) / 70, 1 + (y - 790) / 140) for y in (r.uniform(800, H) for _ in range(600))])
    c.fill(gravel * lot, hexc('#5a3e30'), 0.35); c.bevel(gravel * lot, (0.1, -1), 1.2, '#ffb070', 0.3, 0.2)
    for k, (x0, y0, x1, y1, t) in enumerate(((0, 960, 980, 900, 30), (0, 1016, 1080, 950, 30))):  # I-beams: web, lit top flange, shadow below
        c.fill(c.poly([(x0, y0 + t * 0.9), (x1, y1 + t * 0.9), (x1, y1 + t * 1.4), (x0, y0 + t * 1.6)]), hexc('#0a0608'), 0.6)
        c.fill(c.poly([(x0, y0), (x1, y1), (x1, y1 + t), (x0, y0 + t)]), c.vgrad([(0, '#c0582a'), (0.25, '#8a3418'), (1, '#4a1a0c')], y1, y0 + t))
        c.fill(c.poly([(x0, y0), (x1, y1), (x1, y1 + 4), (x0, y0 + 4)]), hexc('#ffb07a'), 0.7)
        c.fill(c.poly([(x1 - 2, y1), (x1 + 8, y1 + 4), (x1 + 8, y1 + t + 4), (x1 - 2, y1 + t)]), hexc('#2a0e06'))
    crate = c.poly([(1760, 1040), (1760, 910), (2080, 910), (2080, 1040)])
    planks = (0.86 + 0.14 * c.noise(4, 2, 9, aspect=0.15))[..., None] * hexc('#7a5434')[None, None, :]
    c.fill(crate, planks); c.bevel(crate, (-0.2, -1), 4, '#ffc080', 0.45, 0.4)
    for k in range(5): c.fill(c.poly([(1760, 934 + k * 26), (2080, 934 + k * 26), (2080, 937 + k * 26), (1760, 937 + k * 26)]), hexc('#2a1a10'), 0.75)
    c.fill(c.lines([(1760, 912, 2080, 1038, 14), (1760, 1038, 2080, 912, 14)]) * crate, hexc('#5a3c22')); c.fill(c.lines([(1770, 912, 2070, 912, 4)]), hexc('#ffc080'), 0.5)
    for x, y, s in ((1240, 1000, 1.0), (1340, 1012, 0.85)):  # traffic cones
        cone = c.poly([(x - 30 * s, y), (x - 9 * s, y - 86 * s), (x + 9 * s, y - 86 * s), (x + 30 * s, y)]); c.fill(cone, shade_ball(c, x, y - 40 * s, 30 * s, 60 * s, '#ff6a1a', (-0.8, -0.4)))
        c.fill(cone * (np.abs(c.yy - (y - 46 * s)) < 8 * s), hexc('#f4f0e8'), 0.9); c.fill(c.poly([(x - 44 * s, y + 2), (x + 44 * s, y + 2), (x + 40 * s, y - 8 * s), (x - 40 * s, y - 8 * s)]), hexc('#c84a12'))
    hx, hy = 1920, 900
    dome = c.ellipse(hx, hy, 72, 50) * (c.yy < hy); brim = c.ellipse(hx, hy + 2, 96, 13)
    c.fill(np.maximum(dome, brim), shade_ball(c, hx, hy - 20, 80, 50, '#ffbe3a', (-0.8, -0.6))); c.rim(np.maximum(dome, brim), SX, SY, 4, '#fff4c0', 0.8, 1, 0.3)
    dust = c.noise(160, 5, 11, aspect=0.5); c.fill(np.clip(dust - 0.35, 0, 1) * np.clip((c.yy - 650) / 300, 0, 1), hexc('#c88a5a'), 0.18)
    c.bloom(0.8, 16, 0.45); c.grade('#1a1a3a', '#ffe0b0', 1.08, 1.1, 1.0, 'knee'); c.vignette(0.45)
    c.save(OUT / 'labor' / 'scene.webp')

def default_hero():
    c = Canvas(141)
    c.img = c.vgrad([(0, '#05060f'), (0.7, '#141a3a'), (1, '#2a2a5a')], 0, H)
    c.glow(500, 200, 700, '#7b5cff', 0.35, 1.3); c.glow(1900, 800, 800, '#5ff3ff', 0.2, 1.3)
    skyline(c, 900, 120, 420, 0, W, 51, '#04050c', '#ffd890', 0.25, 50, 120)
    bokeh(c, 120, ['#7b5cff', '#5ff3ff', '#ffd890'], 8, 40, 5, 0, H, 0.3)
    c.bloom(0.75, 16, 0.5); c.grade('#0a0a30', '#ffffff', 1.05, 1.1); c.vignette(0.45)
    c.save(OUT / 'default' / 'hero.webp')

SCENES = {'halloween': halloween, 'christmas': christmas, 'valentines': valentines, 'easter': easter, 'stpatricks': stpatricks, 'independence': independence,
          'thanksgiving': thanksgiving, 'new_years_eve': new_years_eve, 'new_years': new_years, 'memorial': memorial, 'labor': labor, 'default': default_hero}

if __name__ == '__main__':
    for name in (sys.argv[1:] or SCENES):
        SCENES[name]()
