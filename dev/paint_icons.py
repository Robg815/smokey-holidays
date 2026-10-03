#!/usr/bin/env python3
"""Renders the holiday emblems (enamel medallions with a gold rim) and the reward pictures as shaded, embossed images with
transparent backgrounds. Original artwork, deterministic. Output: web/img/<id>/emblem.webp, web/img/rewards/<kind>.webp,
web/img/halloween/trophy.webp.   python dev/paint_icons.py"""
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'web' / 'img'
N = 640                     # render size (delivered smaller, so edges are smooth)
yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
L = np.array([-0.55, -0.75]); L = L / np.linalg.norm(L)

def hexc(h): h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)

def m_poly(pts): im = Image.new('L', (N, N)); ImageDraw.Draw(im).polygon([(x * N, y * N) for x, y in pts], fill=255); return np.asarray(im, np.float32) / 255
def m_ell(cx, cy, rx, ry): im = Image.new('L', (N, N)); ImageDraw.Draw(im).ellipse([(cx - rx) * N, (cy - ry) * N, (cx + rx) * N, (cy + ry) * N], fill=255); return np.asarray(im, np.float32) / 255
def m_lines(segs):
    im = Image.new('L', (N, N)); d = ImageDraw.Draw(im)
    for x0, y0, x1, y1, w in segs:
        d.line([(x0 * N, y0 * N), (x1 * N, y1 * N)], fill=255, width=int(w * N))
        for x, y in ((x0, y0), (x1, y1)): d.ellipse([(x - w / 2) * N, (y - w / 2) * N, (x + w / 2) * N, (y + w / 2) * N], fill=255)
    return np.asarray(im, np.float32) / 255
def blur(a, s): return ndimage.gaussian_filter(a, s)

class Layer:
    def __init__(self): self.rgb = np.zeros((N, N, 3), np.float32); self.a = np.zeros((N, N), np.float32)
    def put(self, mask, col, alpha=1.0):
        a = (mask * alpha)[..., None]; c = col if col.ndim == 3 else col[None, None, :]
        self.rgb = self.rgb * (1 - a) + c * a; self.a = self.a + mask * alpha * (1 - self.a)
    def add(self, light, col, k=1.0, within=None):
        l = light * (within if within is not None else 1.0)
        self.rgb += l[..., None] * col[None, None, :] * k
    def shadow(self, mask, dx=0.012, dy=0.02, s=10, k=0.45):
        sh = ndimage.shift(blur(mask, s), (dy * N, dx * N), order=1)
        self.rgb *= (1 - sh * k * self.a)[..., None] if self.a.any() else 1
        self.a = np.maximum(self.a, sh * k)

def shade(mask, base, depth=10, spec=0.6, gloss=40.0, flat=0.0):
    """Bevelled, lit colour for a shape: diffuse from the height field's normals plus a specular highlight."""
    h = blur(mask, depth); gy, gx = np.gradient(h * N * 0.06)
    nz = 1.0; nrm = np.sqrt(gx ** 2 + gy ** 2 + nz ** 2)
    nx, ny, nzz = -gx / nrm, -gy / nrm, nz / nrm
    ld = np.array([L[0], L[1], 0.9]); ld /= np.linalg.norm(ld)
    diff = np.clip(nx * ld[0] + ny * ld[1] + nzz * ld[2], 0, 1)
    hv = ld + np.array([0, 0, 1.0]); hv /= np.linalg.norm(hv)
    sp = np.clip(nx * hv[0] + ny * hv[1] + nzz * hv[2], 0, 1) ** gloss
    col = base[None, None, :] * (0.35 + 0.75 * (diff * (1 - flat) + flat))[..., None] + sp[..., None] * spec
    return col

def save(layer, path, size):
    rgb = np.clip(layer.rgb, 0, 1); a = np.clip(layer.a, 0, 1)
    img = np.dstack([rgb, a]); im = Image.fromarray((img * 255 + 0.5).astype(np.uint8), 'RGBA').resize((size, size), Image.LANCZOS)
    path.parent.mkdir(parents=True, exist_ok=True); im.save(path, 'WEBP', quality=92, method=6)
    print('wrote', path.relative_to(ROOT), f'{path.stat().st_size // 1024} KB')

# ---------------------------------------------------------------- medallion
def medallion(c1, c2, symbol, path):
    lay = Layer(); cx = cy = 0.5
    d = np.sqrt((xx / N - cx) ** 2 + (yy / N - cy) ** 2); ang = np.arctan2(yy / N - cy, xx / N - cx)
    outer, inner = (d < 0.485).astype(np.float32), (d < 0.415).astype(np.float32)
    outer, inner = blur(outer, 0.8), blur(inner, 0.8)
    lay.shadow(outer, 0.0, 0.012, 9, 0.5)
    ring = np.clip(outer - inner, 0, 1)
    metal = shade(outer, hexc('#e8b84a'), 6, 0.9, 30) * (0.82 + 0.18 * np.cos(ang * 2 + 0.8))[..., None]   # brushed sheen
    lay.put(outer, metal)
    for r0 in (0.452, 0.43): lay.put(np.clip(1 - np.abs(d - r0) * N / 1.6, 0, 1), hexc('#8a5a10'), 0.55)    # engraved lines
    enamel = (hexc(c1)[None, None, :] * (1 - np.clip(d / 0.42, 0, 1) ** 1.6)[..., None] + hexc(c2)[None, None, :] * np.clip(d / 0.42, 0, 1)[..., None] ** 1.6)
    noise = blur(np.random.default_rng(7).random((N, N)).astype(np.float32), 2.5)
    enamel *= (0.94 + 0.12 * noise)[..., None]
    lay.put(inner, enamel)
    lay.rgb *= (1 - np.clip(1 - (0.415 - d) / 0.05, 0, 1) * inner * 0.35)[..., None]                       # inner bevel shadow
    symbol(lay, inner)
    gl = np.clip(1 - ((xx / N - 0.45) / 0.36) ** 2 - ((yy / N - 0.3) / 0.22) ** 2, 0, 1) * inner          # glass gloss
    lay.add(gl ** 1.5, np.array([1, 1, 1], np.float32), 0.22)
    save(lay, path, 256)

def emblem(lay, mask, col, within, depth=8, spec=0.5, sh=True):
    if sh: lay.shadow(mask * within, 0.008, 0.014, 6, 0.5)
    lay.put(mask, shade(mask, hexc(col), depth, spec))

def sym_pumpkin(lay, within):
    body = np.maximum.reduce([m_ell(0.5, 0.54, 0.2, 0.16), m_ell(0.4, 0.55, 0.12, 0.15), m_ell(0.6, 0.55, 0.12, 0.15)])
    emblem(lay, body, '#ff8a1f', within, 12)
    for x in (0.42, 0.5, 0.58): lay.put(m_ell(x, 0.55, 0.012, 0.14) * body, hexc('#b8520a'), 0.35)
    emblem(lay, m_lines([(0.5, 0.39, 0.53, 0.3, 0.035)]), '#4a7a2a', within, 4)
    face = np.maximum.reduce([m_poly([(0.4, 0.52), (0.45, 0.46), (0.47, 0.53)]), m_poly([(0.6, 0.52), (0.55, 0.46), (0.53, 0.53)]),
                              m_poly([(0.38, 0.58), (0.44, 0.6), (0.47, 0.57), (0.5, 0.61), (0.53, 0.57), (0.56, 0.6), (0.62, 0.58), (0.56, 0.66), (0.44, 0.66)])])
    lay.put(face, hexc('#ffe27a')); lay.add(blur(face, 8), hexc('#ff9a2a'), 0.9, body)

def sym_tree(lay, within):
    tree = np.maximum.reduce([m_poly([(0.5, 0.24), (0.34, 0.46), (0.66, 0.46)]), m_poly([(0.5, 0.32), (0.3, 0.58), (0.7, 0.58)]), m_poly([(0.5, 0.42), (0.27, 0.7), (0.73, 0.7)])])
    emblem(lay, m_poly([(0.47, 0.69), (0.53, 0.69), (0.53, 0.78), (0.47, 0.78)]), '#6a3a1a', within, 3)
    emblem(lay, tree, '#2f9a55', within, 10)
    for x, y, c in ((0.44, 0.44, '#ff4a5a'), (0.56, 0.52, '#ffd36b'), (0.4, 0.62, '#8fd8ff'), (0.6, 0.64, '#ff4a5a'), (0.5, 0.58, '#ffffff')):
        emblem(lay, m_ell(x, y, 0.022, 0.022), c, within, 2, 0.9, False)
    star = m_poly([(0.5 + math.cos(a) * (0.07 if k % 2 == 0 else 0.03), 0.22 + math.sin(a) * (0.07 if k % 2 == 0 else 0.03)) for k, a in enumerate(np.linspace(-math.pi / 2, 1.5 * math.pi, 11)[:-1])])
    emblem(lay, star, '#ffd84a', within, 4, 0.9); lay.add(blur(star, 14), hexc('#ffd84a'), 0.6)

def heart_pts(cx, cy, s):
    return [(cx + s * 16 * math.sin(t) ** 3 / 16, cy - s * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) / 16) for t in np.linspace(0, 2 * math.pi, 80)]

def sym_heart(lay, within): emblem(lay, m_poly(heart_pts(0.5, 0.5, 0.25)), '#e8243f', within, 16, 0.8)

def sym_egg(lay, within):
    e = m_ell(0.5, 0.52, 0.17, 0.23); emblem(lay, e, '#ff9ecb', within, 16, 0.7)
    for y, c in ((0.44, '#ffffff'), (0.53, '#ffe27a'), (0.62, '#9ed8ff')):
        band = (np.abs(yy / N - y - 0.015 * np.sin(xx / N * 40)) < 0.018).astype(np.float32) * e
        lay.put(blur(band, 1), shade(e, hexc(c), 16, 0.4), 0.95)

def sym_shamrock(lay, within):
    leaves = np.maximum.reduce([m_poly(heart_pts(0.5, 0.36, 0.13)), m_poly([(1 - x, y) for x, y in heart_pts(0.5, 0.36, 0.13)])])
    l1 = m_poly([(0.5 + (x - 0.5) * math.cos(a) - (y - 0.5) * math.sin(a), 0.5 + (x - 0.5) * math.sin(a) + (y - 0.5) * math.cos(a)) for x, y in heart_pts(0.5, 0.36, 0.13)] if False else heart_pts(0.5, 0.36, 0.13))
    rot = lambda pts, a: [(0.5 + (x - 0.5) * math.cos(a) - (y - 0.48) * math.sin(a), 0.48 + (x - 0.5) * math.sin(a) + (y - 0.48) * math.cos(a)) for x, y in pts]
    pts = heart_pts(0.5, 0.33, 0.13)
    leaves = np.maximum.reduce([m_poly(rot(pts, a)) for a in (0, 2.094, 4.189)])
    emblem(lay, m_lines([(0.5, 0.5, 0.56, 0.76, 0.035)]), '#2a8a3a', within, 4)
    emblem(lay, leaves, '#34c45a', within, 12, 0.6)

def star_pts(cx, cy, r1, r2, n=5, rot=-math.pi / 2):
    return [(cx + math.cos(rot + k * math.pi / n) * (r1 if k % 2 == 0 else r2), cy + math.sin(rot + k * math.pi / n) * (r1 if k % 2 == 0 else r2)) for k in range(2 * n)]

def sym_star(lay, within):
    s = m_poly(star_pts(0.5, 0.52, 0.27, 0.11)); emblem(lay, s, '#f4f6ff', within, 10, 0.8)
    lay.put(m_poly(star_pts(0.5, 0.52, 0.27, 0.11)) * (xx / N > 0.5), hexc('#c8d0e8'), 0.25)

def sym_leaf(lay, within):
    pts = [(0.5, 0.2), (0.56, 0.34), (0.68, 0.28), (0.64, 0.42), (0.78, 0.44), (0.66, 0.52), (0.72, 0.62), (0.56, 0.6), (0.53, 0.72), (0.5, 0.66),
           (0.47, 0.72), (0.44, 0.6), (0.28, 0.62), (0.34, 0.52), (0.22, 0.44), (0.36, 0.42), (0.32, 0.28), (0.44, 0.34)]
    leaf = m_poly(pts); emblem(lay, leaf, '#ee7a1e', within, 10, 0.5)
    lay.put(m_lines([(0.5, 0.3, 0.5, 0.8, 0.012), (0.5, 0.5, 0.64, 0.4, 0.008), (0.5, 0.5, 0.36, 0.4, 0.008), (0.5, 0.58, 0.62, 0.58, 0.008), (0.5, 0.58, 0.38, 0.58, 0.008)]) * np.maximum(leaf, m_lines([(0.5, 0.7, 0.5, 0.8, 0.012)])), hexc('#9a3a0a'), 0.7)

def sym_clock(lay, within):
    face = m_ell(0.5, 0.5, 0.25, 0.25); emblem(lay, face, '#f4f0e0', within, 8, 0.4)
    for k in range(12):
        a = k * math.pi / 6; r0 = 0.2 if k % 3 else 0.18
        lay.put(m_lines([(0.5 + math.cos(a) * r0, 0.5 + math.sin(a) * r0, 0.5 + math.cos(a) * 0.23, 0.5 + math.sin(a) * 0.23, 0.012)]), hexc('#2a2a3a'))
    emblem(lay, m_lines([(0.5, 0.5, 0.5, 0.31, 0.022), (0.5, 0.5, 0.51, 0.36, 0.03)]), '#c8961a', within, 3, 0.8, False)
    emblem(lay, m_ell(0.5, 0.5, 0.025, 0.025), '#c8961a', within, 2, 0.8, False)

def sym_flutes(lay, within):
    for cx, a in ((0.42, 0.22), (0.58, -0.22)):
        rot = lambda pts: [(cx + (x - cx) * math.cos(a) - (y - 0.55) * math.sin(a), 0.55 + (x - cx) * math.sin(a) + (y - 0.55) * math.cos(a)) for x, y in pts]
        glass = m_poly(rot([(cx - 0.07, 0.26), (cx + 0.07, 0.26), (cx + 0.05, 0.5), (cx + 0.012, 0.56), (cx + 0.012, 0.72), (cx + 0.06, 0.76), (cx - 0.06, 0.76), (cx - 0.012, 0.72), (cx - 0.012, 0.56), (cx - 0.05, 0.5)]))
        wine = m_poly(rot([(cx - 0.062, 0.33), (cx + 0.062, 0.33), (cx + 0.046, 0.49), (cx + 0.01, 0.54), (cx - 0.01, 0.54), (cx - 0.046, 0.49)]))
        lay.shadow(glass * within, 0.006, 0.01, 5, 0.35)
        lay.put(glass, shade(glass, hexc('#e8f4ff'), 5, 0.9), 0.55); lay.put(wine, shade(wine, hexc('#f5c542'), 6, 0.8), 0.95)
    for x, y in ((0.5, 0.2), (0.44, 0.17), (0.57, 0.16), (0.5, 0.12)):
        lay.add(blur(m_ell(x, y, 0.01, 0.01), 3), hexc('#fff4c0'), 2.5)

def sym_poppy(lay, within):
    petals = np.maximum.reduce([m_ell(0.5 + math.cos(a) * 0.1, 0.48 + math.sin(a) * 0.1, 0.13, 0.12) for a in np.linspace(0, 2 * math.pi, 5, endpoint=False) + 0.3])
    emblem(lay, m_lines([(0.5, 0.55, 0.47, 0.82, 0.03)]), '#2a6a2a', within, 4)
    emblem(lay, petals, '#d8202a', within, 12, 0.5)
    emblem(lay, m_ell(0.5, 0.48, 0.06, 0.06), '#1a1012', within, 4, 0.4, False)

def sym_hat(lay, within):
    dome = m_ell(0.5, 0.56, 0.22, 0.2) * (yy / N < 0.58); brim = m_ell(0.5, 0.6, 0.28, 0.05)
    emblem(lay, np.maximum(dome, brim), '#ffc247', within, 12, 0.7)
    lay.put(m_lines([(0.5, 0.37, 0.5, 0.57, 0.025)]) * dome, hexc('#d89a20'), 0.7)

def sym_default(lay, within): emblem(lay, m_poly(star_pts(0.5, 0.52, 0.25, 0.1)), '#ffd84a', within, 10, 0.8)

EMBLEMS = {'halloween': ('#7a3aa0', '#2a0f3e', sym_pumpkin), 'christmas': ('#c8303e', '#5a0a14', sym_tree), 'valentines': ('#ff8ac0', '#8a1a4a', sym_heart),
           'easter': ('#c9a5ff', '#5a3a9a', sym_egg), 'stpatricks': ('#3ab86a', '#0a4a24', sym_shamrock), 'independence': ('#3b57c8', '#0e1a5a', sym_star),
           'thanksgiving': ('#a8582a', '#3a1608', sym_leaf), 'new_years_eve': ('#2a3a8a', '#0a1030', sym_clock), 'new_years': ('#5a7ad0', '#1a2a6a', sym_flutes),
           'memorial': ('#3a4a7a', '#101830', sym_poppy), 'labor': ('#3a6ab8', '#0e1a3a', sym_hat), 'default': ('#7b5cff', '#241a5a', sym_default)}

# ---------------------------------------------------------------- reward pictures (transparent, 320 px)
def reward(draw, path):
    lay = Layer()
    halo = np.clip(1 - np.sqrt((xx / N - 0.5) ** 2 + (yy / N - 0.5) ** 2) / 0.48, 0, 1) ** 2
    lay.rgb += halo[..., None] * hexc('#ffffff')[None, None, :] * 0.0
    lay.a = halo * 0.0
    draw(lay); save(lay, path, 320)

def obj(lay, mask, col, depth=12, spec=0.6, sh=(0.012, 0.03, 12, 0.45)):
    lay.shadow(mask, *sh); lay.put(mask, shade(mask, hexc(col), depth, spec))

def r_gift(lay):
    box = m_poly([(0.24, 0.44), (0.76, 0.44), (0.76, 0.84), (0.24, 0.84)]); lid = m_poly([(0.2, 0.34), (0.8, 0.34), (0.8, 0.46), (0.2, 0.46)])
    obj(lay, box, '#e8384e', 8); obj(lay, lid, '#ff4a62', 6)
    rib = m_poly([(0.46, 0.34), (0.54, 0.34), (0.54, 0.84), (0.46, 0.84)]); lay.put(rib, shade(rib, hexc('#ffd36b'), 4, 0.8))
    bow = np.maximum(m_ell(0.42, 0.29, 0.1, 0.06), m_ell(0.58, 0.29, 0.1, 0.06)); obj(lay, bow, '#ffd36b', 8, 0.8, (0.005, 0.01, 5, 0.3))
    obj(lay, m_ell(0.5, 0.31, 0.035, 0.035), '#e8b03a', 4, 0.8, (0, 0.005, 3, 0.2))

def r_coins(lay):
    for x, y in ((0.36, 0.78), (0.36, 0.72), (0.36, 0.66), (0.62, 0.8), (0.62, 0.74)):
        side = m_poly([(x - 0.16, y), (x + 0.16, y), (x + 0.16, y + 0.04), (x - 0.16, y + 0.04)]); obj(lay, np.maximum(side, m_ell(x, y + 0.04, 0.16, 0.045)), '#c8961a', 4, 0.5, (0.01, 0.02, 6, 0.3))
        obj(lay, m_ell(x, y, 0.16, 0.045), '#f5c542', 3, 0.9, (0, 0, 1, 0))
    coin = m_ell(0.62, 0.4, 0.17, 0.17); obj(lay, coin, '#f5c542', 10, 0.9)
    lay.put(m_ell(0.62, 0.4, 0.13, 0.13) - m_ell(0.62, 0.4, 0.12, 0.12), hexc('#a8740c'), 0.6)
    s = m_poly(star_pts(0.62, 0.41, 0.08, 0.035)); lay.put(s, shade(s, hexc('#d8a428'), 4, 0.6))

def r_candy(lay):
    bag = m_poly([(0.26, 0.4), (0.74, 0.4), (0.7, 0.86), (0.3, 0.86)]); obj(lay, bag, '#ff8a1f', 14, 0.5)
    face = np.maximum.reduce([m_poly([(0.38, 0.56), (0.43, 0.5), (0.46, 0.57)]), m_poly([(0.62, 0.56), (0.57, 0.5), (0.54, 0.57)]), m_poly([(0.38, 0.66), (0.5, 0.74), (0.62, 0.66), (0.5, 0.7)])])
    lay.put(face, hexc('#2a1208'))
    for x, y, a, c in ((0.36, 0.33, -0.5, '#ff5a8a'), (0.55, 0.3, 0.3, '#5ad0ff'), (0.65, 0.36, 0.8, '#ffe27a')):
        w = m_ell(x, y, 0.08, 0.045)
        tw = np.maximum(m_poly([(x - 0.08, y), (x - 0.13, y - 0.04), (x - 0.13, y + 0.04)]), m_poly([(x + 0.08, y), (x + 0.13, y - 0.04), (x + 0.13, y + 0.04)]))
        rot = ndimage.rotate(np.maximum(w, tw), math.degrees(a), reshape=False, order=1)
        obj(lay, rot, c, 6, 0.9, (0.005, 0.01, 4, 0.3))

def r_ghost(lay):
    pts = [(0.3, 0.86)] + [(0.3 + 0.4 * t, 0.86 - 0.05 * (k % 2)) for k, t in enumerate(np.linspace(0, 1, 9))] + [(0.7, 0.86), (0.7, 0.42)]
    body = np.maximum(m_poly(pts + [(0.3, 0.42)]), m_ell(0.5, 0.42, 0.2, 0.2)); obj(lay, body, '#eef6ff', 18, 0.5)
    for x in (0.43, 0.57): lay.put(m_ell(x, 0.42, 0.035, 0.05), hexc('#1a0b2e'))
    lay.put(m_ell(0.5, 0.56, 0.04, 0.055), hexc('#1a0b2e'))
    lay.add(blur(body, 22), hexc('#9fe0ff'), 0.25)

def r_scare(lay):
    skull = np.maximum(m_ell(0.5, 0.44, 0.23, 0.22), m_poly([(0.38, 0.56), (0.62, 0.56), (0.6, 0.76), (0.4, 0.76)])); obj(lay, skull, '#f2ecdc', 14, 0.5)
    for x in (0.41, 0.59): lay.put(m_ell(x, 0.47, 0.065, 0.075), hexc('#1a0a12'))
    lay.put(m_poly([(0.5, 0.54), (0.47, 0.62), (0.53, 0.62)]), hexc('#1a0a12'))
    for x in np.linspace(0.42, 0.58, 5): lay.put(m_lines([(x, 0.66, x, 0.75, 0.012)]), hexc('#4a3a30'), 0.8)
    for x in (0.41, 0.59): lay.add(blur(m_ell(x, 0.48, 0.02, 0.02), 6), hexc('#ff5a2a'), 1.2)

def r_empty(lay):
    house = np.maximum(m_poly([(0.24, 0.5), (0.5, 0.26), (0.76, 0.5)]), m_poly([(0.3, 0.48), (0.7, 0.48), (0.7, 0.84), (0.3, 0.84)])); obj(lay, house, '#5a4a6a', 10, 0.3)
    for x0 in (0.35, 0.57): lay.put(m_poly([(x0, 0.56), (x0 + 0.08, 0.56), (x0 + 0.08, 0.64), (x0, 0.64)]), hexc('#0c0812'))
    lay.put(m_poly([(0.45, 0.66), (0.55, 0.66), (0.55, 0.84), (0.45, 0.84)]), hexc('#0c0812'))

def r_star(lay):
    s = m_poly(star_pts(0.5, 0.52, 0.32, 0.13)); obj(lay, s, '#ffd84a', 14, 0.9)
    lay.add(blur(s, 26), hexc('#ffd84a'), 0.5)

def r_trophy(lay):
    cup = np.maximum(m_poly([(0.3, 0.3), (0.7, 0.3), (0.66, 0.5), (0.56, 0.6), (0.44, 0.6), (0.34, 0.5)]), m_ell(0.5, 0.3, 0.2, 0.04))
    handles = np.clip(m_ell(0.28, 0.4, 0.08, 0.09) - m_ell(0.28, 0.4, 0.05, 0.06), 0, 1) + np.clip(m_ell(0.72, 0.4, 0.08, 0.09) - m_ell(0.72, 0.4, 0.05, 0.06), 0, 1)
    stem = m_poly([(0.47, 0.6), (0.53, 0.6), (0.55, 0.72), (0.45, 0.72)]); base = np.maximum(m_poly([(0.36, 0.72), (0.64, 0.72), (0.64, 0.8), (0.36, 0.8)]), m_poly([(0.32, 0.8), (0.68, 0.8), (0.68, 0.88), (0.32, 0.88)]))
    obj(lay, np.clip(handles, 0, 1), '#e8b03a', 6, 0.9); obj(lay, base, '#5a2a7a', 8, 0.5); obj(lay, stem, '#e8b03a', 6, 0.9); obj(lay, cup, '#f5c542', 14, 0.95)
    p = np.maximum.reduce([m_ell(0.5, 0.22, 0.12, 0.09), m_ell(0.44, 0.22, 0.07, 0.085), m_ell(0.56, 0.22, 0.07, 0.085)])
    obj(lay, p, '#ff8a1f', 10, 0.4, (0.004, 0.01, 4, 0.3)); lay.put(m_lines([(0.5, 0.13, 0.52, 0.09, 0.02)]), hexc('#4a7a2a'))
    face = np.maximum.reduce([m_poly([(0.45, 0.21), (0.48, 0.18), (0.49, 0.22)]), m_poly([(0.55, 0.21), (0.52, 0.18), (0.51, 0.22)]), m_poly([(0.44, 0.25), (0.5, 0.28), (0.56, 0.25), (0.5, 0.265)])])
    lay.put(face, hexc('#ffe27a')); lay.add(blur(face, 5), hexc('#ff9a2a'), 0.8)

REWARDS = {'gift': r_gift, 'coins': r_coins, 'candy': r_candy, 'ghost': r_ghost, 'scare': r_scare, 'empty': r_empty, 'star': r_star}

if __name__ == '__main__':
    for hid, (c1, c2, fn) in EMBLEMS.items(): medallion(c1, c2, fn, OUT / hid / 'emblem.webp')
    for k, fn in REWARDS.items(): reward(fn, OUT / 'rewards' / f'{k}.webp')
    reward(r_trophy, OUT / 'halloween' / 'trophy.webp')
