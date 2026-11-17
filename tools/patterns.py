"""Original pattern system for the Trenza Alpargata · Muisca study.
Vocabulary taken from painted Muisca cotton mantas (alternating geometric panels: rhomboids, spirals, triangles)
and spindle-whorl geometry. Drawn fresh, not copied from any one object.
python3 patterns.py  -> tex/<cw>_manta.png, tex/<cw>_faja.png, sheets/pattern_<cw>.png
"""
import math, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

CW = {
 'manta':   dict(ground='#E8DDC6', ink='#4A2E1E', a='#23305E', b='#A8391C', gold='#C9A04A', name='MANTA'),
 'tumbaga': dict(ground='#17140F', ink='#C9A04A', a='#6E1F1A', b='#8C6A2E', gold='#D8B25A', name='TUMBAGA'),
 'paramo':  dict(ground='#3C4631', ink='#E6DCC4', a='#1E2A4E', b='#C08A3A', gold='#C9A04A', name='PÁRAMO'),
}
S = 4  # supersample

def rgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def jit(pts, a, rnd):
    return [(x + rnd.uniform(-a, a), y + rnd.uniform(-a, a)) for x, y in pts]

def cotton(img, rnd, amt=10):
    """plain-weave cotton ground: fine warp/weft modulation + slub noise"""
    W, H = img.size; a = np.asarray(img).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    weave = (np.sin(xx * 2 * math.pi / (S * 3)) * np.sin(yy * 2 * math.pi / (S * 3))) * 0.5
    slub = np.repeat(np.random.default_rng(rnd.randint(0, 9999)).normal(0, 1, (H, 1)), W, 1) * 0.6
    n = (weave + slub)[..., None] * amt
    return Image.fromarray(np.clip(a + n, 0, 255).astype(np.uint8))

def paint(d, poly, col, rnd, w=None, wob=1.2):
    pts = jit(poly, wob * S, rnd)
    if w: d.line(pts + [pts[0]], fill=col, width=int(w * S), joint='curve')
    else: d.polygon(pts, fill=col)

def sq_spiral(cx, cy, r, step):
    pts = [(cx, cy)]; L = step; x, y = cx, cy; dirs = [(1, 0), (0, 1), (-1, 0), (0, -1)]; k = 0
    while L < 2 * r:
        for _ in range(2):
            dx, dy = dirs[k % 4]; x += dx * L; y += dy * L; pts.append((x, y)); k += 1
        L += step
    return pts

def manta(c, seed=7, N=1024):
    """4x4 alternating panels: nested rhombus / squared spiral, double-ruled frames, triangle corners"""
    rnd = random.Random(seed); W = N * S
    img = Image.new('RGB', (W, W), rgb(c['ground'])); img = cotton(img, rnd, 9 if c['ground'] != '#17140F' else 6)
    d = ImageDraw.Draw(img); P = W // 4; ink = rgb(c['ink']); A = rgb(c['a']); B = rgb(c['b'])
    for i in range(4):
        for j in range(4):
            x0, y0 = i * P, j * P; cx, cy = x0 + P / 2, y0 + P / 2; m = P * 0.08
            # frame: double rule
            for k, w in ((0.02, 3.2), (0.055, 1.6)):
                o = P * k; paint(d, [(x0 + o, y0 + o), (x0 + P - o, y0 + o), (x0 + P - o, y0 + P - o), (x0 + o, y0 + P - o)], ink, rnd, w)
            # corner triangles
            t = P * 0.16
            for (ax, ay, sx, sy) in ((x0 + m, y0 + m, 1, 1), (x0 + P - m, y0 + m, -1, 1), (x0 + P - m, y0 + P - m, -1, -1), (x0 + m, y0 + P - m, 1, -1)):
                paint(d, [(ax, ay), (ax + sx * t, ay), (ax, ay + sy * t)], B if (i + j) % 2 else A, rnd)
            if (i + j) % 2 == 0:   # nested rhombi
                for k, col in enumerate((ink, rgb(c['ground']), A, rgb(c['ground']), ink, B)):
                    r = P * (0.34 - k * 0.055)
                    if r <= 0: break
                    paint(d, [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], col, rnd)
            else:                 # squared spiral, painted line
                pts = sq_spiral(cx, cy, P * 0.3, P * 0.06)
                d.line(jit(pts, 1.0 * S, rnd), fill=ink, width=int(5.5 * S), joint='curve')
                d.ellipse([cx - P * .03, cy - P * .03, cx + P * .03, cy + P * .03], fill=A)
    img = img.filter(ImageFilter.GaussianBlur(S * 0.5))
    return img.resize((N, N), Image.LANCZOS)

def faja(c, seed=3, N=2048, H=320):
    """woven band: warp stripes, stepped diamond chain, gold edge threads"""
    rnd = random.Random(seed); W, HH = N * S // 2, H * S // 2
    img = Image.new('RGB', (W, HH), rgb(c['ground'])); d = ImageDraw.Draw(img)
    ink, A, B, G = rgb(c['ink']), rgb(c['a']), rgb(c['b']), rgb(c['gold'])
    e = HH * 0.12
    d.rectangle([0, 0, W, e], fill=ink); d.rectangle([0, HH - e, W, HH], fill=ink)
    d.rectangle([0, e, W, e + HH * .04], fill=G); d.rectangle([0, HH - e - HH * .04, W, HH - e], fill=G)
    cy = HH / 2; h = (HH - 2 * e) * 0.40; step = h * 2.2; k = 0
    x = 0
    while x < W + step:
        col = (A, B)[k % 2]
        # stepped diamond (terraced, woven look)
        for s in range(5, 0, -1):
            r = h * s / 5; q = r * 0.92
            d.polygon([(x, cy - r), (x + q, cy), (x, cy + r), (x - q, cy)], fill=(col if s % 2 else rgb(c['ground'])))
        d.rectangle([x - h * .08, cy - h * .08, x + h * .08, cy + h * .08], fill=G)
        # small triangles between
        xm = x + step / 2
        d.polygon([(xm - h * .3, e + HH * .04), (xm + h * .3, e + HH * .04), (xm, e + HH * .04 + h * .45)], fill=ink)
        d.polygon([(xm - h * .3, HH - e - HH * .04), (xm + h * .3, HH - e - HH * .04), (xm, HH - e - HH * .04 - h * .45)], fill=ink)
        x += step; k += 1
    a = np.asarray(img).astype(np.float32); xx = np.arange(W)
    warp = (np.sin(xx * 2 * math.pi / (S * 2.5)) * 10)[None, :, None]
    weft = (np.sin(np.arange(HH) * 2 * math.pi / (S * 6)) * 6)[:, None, None]
    img = Image.fromarray(np.clip(a + warp + weft, 0, 255).astype(np.uint8))
    return img.resize((N, H), Image.LANCZOS)

if __name__ == '__main__':
    os.makedirs('tex', exist_ok=True)
    for k, c in CW.items():
        manta(c).save(f'tex/{k}_manta.png'); faja(c).save(f'tex/{k}_faja.png'); print(k)
