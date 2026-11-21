"""Standard Play CMF: the physical materials behind each tape, rebuilt as 50 mm samples.
python3 sp3d.py -- <key|TAPE:t90|SHELF> <out.png> <res> [spp]"""
import sys, os, json, math
sys.path.insert(0, '/home/claude/cmf')
exec(open('/home/claude/cmf/sw_core.py').read())
import bpy
from mathutils import Vector
A = sys.argv[sys.argv.index('--') + 1:]
KEY, OUT, RES = A[0], A[1], int(A[2]); SPP = int(A[3]) if len(A) > 3 else 128

def hx(h): h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)
def lin(c): c = np.asarray(c, np.float32); return np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
def paint(mask_list, base):
    rgb = np.broadcast_to(hx(base), (HP, PX, 3)).copy()
    for m, c in mask_list:
        cc = hx(c) if isinstance(c, str) else c
        m = m[..., None] if m.ndim == 2 else m
        rgb = rgb * (1 - m) + cc * m
    return rgb
ONE = np.ones((HP, PX), np.float32)


# ---------------------------------------------------------------- Standard Play material registry (5 tapes x 5 materials)
# every sample is 50 x 50 mm; xm/ym are mm; h is a 0..1 height field scaled by disp (mm)
G = {}; SPEC = {}
def reg(key, name, rough=.6, disp=.4, thick=2.0, extra=None, **spec):
    def deco(f): G[key] = dict(f=f, name=name, rough=rough, disp=disp, thick=thick, extra=extra or {}); SPEC[key] = dict(name=name, **spec); return f
    return deco
Z = np.zeros((HP, PX), np.float32)
def smooth(e0, e1, x): t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)
def disc(cx, cy, r, soft=0.15): return 1 - smooth(r - soft, r + soft, np.hypot(xm - cx, ym - cy))
def rect(x0, y0, x1, y1, soft=0.12): return smooth(x0 - soft, x0 + soft, xm) * (1 - smooth(x1 - soft, x1 + soft, xm)) * smooth(y0 - soft, y0 + soft, ym) * (1 - smooth(y1 - soft, y1 + soft, ym))
def rowlines(seed, amp=1.0):
    r = np.random.default_rng(seed).random(HP).astype(np.float32); r = np.convolve(r, np.ones(3) / 3, 'same')
    return (r[:, None] * np.ones((1, PX), np.float32)) * amp
def seg7(ch, x0, y0, w, hgt, t):
    S = {'0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abgcd', '4': 'fgbc', '5': 'afgcd', '6': 'afgcde', '7': 'abc', '8': 'abcdefg', '9': 'abcdfg'}[ch]
    m = Z.copy(); hh = hgt / 2
    segs = {'a': (x0 + t, y0 + 2 * hh - t, x0 + w - t, y0 + 2 * hh), 'g': (x0 + t, y0 + hh - t / 2, x0 + w - t, y0 + hh + t / 2), 'd': (x0 + t, y0, x0 + w - t, y0 + t),
            'f': (x0, y0 + hh + t / 2, x0 + t, y0 + 2 * hh - t), 'b': (x0 + w - t, y0 + hh + t / 2, x0 + w, y0 + 2 * hh - t),
            'e': (x0, y0 + t, x0 + t, y0 + hh - t / 2), 'c': (x0 + w - t, y0 + t, x0 + w, y0 + hh - t / 2)}
    for s in S: m = np.maximum(m, rect(*segs[s], soft=0.08))
    return m

# ---- T-120 VHS STORE · 1980s video rental
@reg('t120_sleeve', 'Printed sleeve board', .62, .12, 1.0, tape='t120', proc='SBS paperboard · 4-colour offset + matte varnish', gloss='8 GU', role='Stripe field / hero pattern', hexes=['#FF1F8F', '#FFC23A', '#3FE6CC', '#7A3CF0'])
def _():
    u = (xm * math.cos(math.radians(32)) + ym * math.sin(math.radians(32))) % 26
    bands = [(0, 3.6, '#FF1F8F'), (5.1, 6.4, '#FF6F86'), (7.9, 10.4, '#F8A39E'), (12, 16.8, '#FFC23A'), (18.4, 19.7, '#7A3CF0'), (21.8, 24.3, '#3FE6CC')]
    ms = [(((u >= a) & (u < b)).astype(np.float32), c) for a, b, c in bands]
    return 0.6 * fbm(0.6, 2), ONE, paint(ms, '#0B0A10')
@reg('t120_shell', 'Cassette shell', .58, .35, 3.0, tape='t120', proc='ABS · injection moulded · fine stipple texture', gloss='12 GU', role='Surface (Night)', hexes=['#141318'])
def _():
    st = fbm(0.28, 2); grip = ((xm % 1.6) < 0.8) & (ym < 12)
    return 0.45 * st + 0.5 * grip, ONE, paint([], '#141318') * (0.92 + 0.1 * st[..., None])
@reg('t120_window', 'Smoked tape window', .06, .05, 1.5, {'tint': '#6A6270', 'under': '#141318', 'reel': 1}, tape='t120', proc='PC · clear smoke 40 % · polished tool', gloss='90 GU', role='Overlay / scrim', hexes=['#2E2A33'])
def _(): return Z, ONE, paint([], '#2E2A33')
@reg('t120_label', 'Spine label paper', .86, .15, 0.6, tape='t120', proc='Uncoated label stock · 1-colour print', gloss='4 GU', role='Text on dark / Paper', hexes=['#F6ECC6'])
def _():
    lines = ((ym % 4.2) < 0.18) & (ym > 6); f = fbm(0.4, 2)
    return 0.5 * f, ONE, paint([(lines.astype(np.float32), '#E3CF94')], '#F6ECC6') * (0.97 + 0.05 * f[..., None])
@reg('t120_sticker', 'Price sticker', .18, .35, 2.0, {'coat': 1}, tape='t120', proc='Gloss PVC vinyl · die-cut · on ABS', gloss='75 GU', role='Accent / Sticker', hexes=['#FF1F8F'])
def _():
    d = disc(25, 25, 13.5, 0.2); st = fbm(0.28, 2)
    return 0.25 * st * (1 - d) + 0.55 * d, ONE, paint([(d, '#FF1F8F')], '#141318')

# ---- T-60 PHOSPHOR · 80s CRT terminal
@reg('t60_crt', 'Phosphor screen', .05, .05, 2.0, {'glass': '#0A140C', 'emit': 5.0}, tape='t60', proc='Soda-lime CRT glass · P1 green phosphor', gloss='95 GU', role='Background / Glow text', hexes=['#050B07', '#39FF6E'])
def _():
    scan = ((ym % 0.7) < 0.42).astype(np.float32); glyph = Z.copy()
    for i, ch in enumerate('046'): glyph = np.maximum(glyph, seg7(ch, 8 + i * 12, 30, 8, 12, 1.4))
    cursor = rect(8, 12, 30, 15.5); em = np.clip(glyph + cursor, 0, 1) * scan * 0.9 + 0.04 * scan
    return Z, ONE, paint([(em, '#39FF6E')], '#050B07'), em
@reg('t60_case', 'Computer case', .62, .28, 3.0, tape='t60', proc='ABS · VDI 30 spark texture', gloss='6 GU', role='Surface (Daylight)', hexes=['#E8E0CA'])
def _():
    st = fbm(0.22, 3); return 0.6 * st, ONE, paint([], '#E8E0CA') * (0.95 + 0.07 * st[..., None])
@reg('t60_vents', 'Cooling vents', .62, 1.4, 3.0, tape='t60', proc='ABS · moulded-through slots · 2 mm pitch', gloss='6 GU', role='Divider / Pattern', hexes=['#E8E0CA', '#3B372E'])
def _():
    slot = ((xm % 3.0) < 1.4) & (ym > 8) & (ym < 42); st = fbm(0.22, 2)
    return 0.15 * st + (1 - slot), ONE, paint([(slot.astype(np.float32), '#3B372E')], '#E8E0CA')
@reg('t60_keys', 'Keycaps', .5, 3.5, 2.0, tape='t60', proc='PBT · double-shot · cylindrical dish', gloss='15 GU', role='Button (secondary)', hexes=['#D9D2C0', '#8C877C'])
def _():
    h = Z.copy(); dark = Z.copy()
    for i in range(2):
        for j in range(2):
            x0, y0 = 4 + i * 22.5, 4 + j * 22.5; k = rect(x0, y0, x0 + 19.5, y0 + 19.5, 0.9)
            dish = 1 - 0.18 * (((xm - x0 - 9.75) / 9.75) ** 2)
            h = np.maximum(h, k * dish)
            if (i + j) % 2: dark = np.maximum(dark, k)
    return h, ONE, paint([(dark, '#8C877C')], '#D9D2C0')
@reg('t60_led', 'Drive-activity lens', .1, 1.2, 3.0, {'emit': 1.2}, tape='t60', proc='Amber PC light-pipe · on ABS case', gloss='85 GU', role='Warning', hexes=['#FFB000'])
def _():
    d = disc(25, 25, 8, 0.4); dome = np.sqrt(np.clip(1 - ((xm - 25) ** 2 + (ym - 25) ** 2) / 64, 0, 1)); st = fbm(0.22, 2)
    return 0.12 * st * (1 - d) + 0.3 + 0.7 * dome * d, ONE, paint([(d, '#FF9800')], '#E8E0CA'), d * (0.5 + 0.5 * dome)

# ---- T-90 HI-FI · 70s stereo receiver
@reg('t90_alu', 'Brushed faceplate', .3, .025, 2.0, {'metal': 1, 'aniso': .85}, tape='t90', proc='6063 aluminium · linear brush 240 grit · clear anodise', gloss='35 GU', role='Surface raised', hexes=['#C3C7CB'])
def _():
    r = rowlines(11) * 0.7 + 0.3 * fbm(0.35, 1); return r, ONE, paint([], '#C3C7CB') * (0.97 + 0.05 * r[..., None])
@reg('t90_walnut', 'Walnut side panel', .45, .035, 4.0, {'coat': .4}, tape='t90', proc='American walnut veneer · oil + satin lacquer', gloss='25 GU', role='Pattern / warm frame', hexes=['#5A3A22', '#8A5A35'])
def _():
    warp = 3.2 * fbm(220, 2) + 0.5 * fbm(45, 2); w = xm + warp; g = (0.5 + 0.5 * np.sin(w * 1.1 + 2.2 * fbm(90, 2))) ** 2.2; pores = (fbm(0.3, 1) > 0.9).astype(np.float32)
    fine = 0.5 + 0.5 * np.sin((xm + warp) * 7.0 + 2 * fbm(30, 1))
    rgb = hx('#4A2E1A') * (1 - g[..., None]) + hx('#8A5A35') * g[..., None]; rgb = rgb * (0.9 + 0.1 * fine[..., None])
    return 0.6 * g + 0.2 * fine - 0.12 * pores, ONE, rgb * (1 - 0.15 * pores[..., None])
@reg('t90_knurl', 'Knurled volume knob', .3, .9, 4.0, {'metal': .9}, tape='t90', proc='Aluminium · diamond knurl 0.8 mm · graphite anodise', gloss='30 GU', role='Control', hexes=['#2A2B2E'])
def _():
    p = 2.0; a = np.abs(((xm + ym) % p) / p - .5) * 2; b = np.abs(((xm - ym) % p) / p - .5) * 2
    k = np.minimum(a, b); return k, ONE, paint([], '#3A3C40') * (0.85 + 0.3 * k[..., None])
@reg('t90_vu', 'Backlit VU dial', .25, .04, 2.0, {'emit': 0.45, 'coat': 1}, tape='t90', proc='Printed PET dial · amber backlight', gloss='70 GU', role='Accent glow / meter', hexes=['#F5A623', '#D7281E'])
def _():
    cx, cy = 25, -2; r = np.hypot(xm - cx, ym - cy); ang = np.degrees(np.arctan2(ym - cy, xm - cx))
    arc = (np.abs(r - 34) < 0.35) & (ang > 40) & (ang < 140)
    tick = (np.abs(r - 31) < 3) & (ang > 40) & (ang < 140) & ((np.abs((ang - 40) % 10) < 0.7))
    red = ((np.abs(r - 34) < 1.1) | tick) & (ang > 40) & (ang < 65)
    needle = (np.abs(np.degrees(np.arctan2(ym - cy, xm - cx)) - 78) < 0.55) & (r < 37) & (r > 4)
    ink = (arc | tick).astype(np.float32)
    rgb = paint([(ink, '#2A1A0C'), (red.astype(np.float32), '#D7281E'), (needle.astype(np.float32), '#D7281E')], '#F29A1E')
    em = (1 - ink) * (1 - needle) * (0.7 - 0.3 * np.clip(r / 50, 0, 1))
    return Z, ONE, rgb, em
@reg('t90_face', 'Silk-screened panel', .4, .05, 2.0, {'metal': .6}, tape='t90', proc='Aluminium · graphite anodise · cream silk-screen', gloss='30 GU', role='Text on surface', hexes=['#17181A', '#F3E7C9'])
def _():
    lines = Z.copy()
    for i, y in enumerate((10, 18, 26, 34, 42)):
        lines = np.maximum(lines, rect(6, y, 6 + (14 + 6 * (i % 3)), y + 0.9, 0.05))
        lines = np.maximum(lines, rect(32, y, 44, y + 0.9, 0.05) * (i % 2))
    return 0.2 * rowlines(3, .5), ONE, paint([(lines, '#F3E7C9')], '#17181A')

# ---- T-160 PIXEL CART · 90s handheld console
@reg('t160_grape', 'Translucent grape shell', .12, .1, 2.5, {'tint': '#6B3FA0', 'under': '#2F5A2B'}, tape='t160', proc='Translucent PC · grape tint · polished', gloss='80 GU', role='Brand surface', hexes=['#6B3FA0'])
def _(): return Z, ONE, paint([], '#6B3FA0')
@reg('t160_berry', 'Berry A/B buttons', .62, 3.2, 2.0, tape='t160', proc='Silicone keypad · berry · soft-touch', gloss='10 GU', role='Button (primary)', hexes=['#C2185B', '#D6D3DE'])
def _():
    d1 = disc(17, 20, 7.5, 0.4); d2 = disc(33, 30, 7.5, 0.4)
    dome = np.maximum(np.sqrt(np.clip(1 - ((xm - 17) ** 2 + (ym - 20) ** 2) / 56, 0, 1)), np.sqrt(np.clip(1 - ((xm - 33) ** 2 + (ym - 30) ** 2) / 56, 0, 1)))
    st = fbm(0.25, 2); m = np.maximum(d1, d2)
    return 0.05 * st + dome * 0.9, ONE, paint([(m, '#C2185B')], '#D6D3DE')
@reg('t160_lcd', 'Reflective LCD', .2, .05, 2.0, {'coat': 1}, tape='t160', proc='STN reflective LCD · pea-green', gloss='60 GU', role='Display / pixel art', hexes=['#C9DB7A', '#0F2410'])
def _():
    p = 1.25; cell = ((xm % p) < 1.08) & ((ym % p) < 1.08); ix, iy = (xm // p).astype(int), (ym // p).astype(int)
    F = {'S': ['01111', '10000', '10000', '01110', '00001', '00001', '11110'], 'P': ['11110', '10001', '10001', '11110', '10000', '10000', '10000']}
    on = np.zeros_like(cell)
    for li, ch in enumerate('SP'):
        for r_, row in enumerate(F[ch]):
            for c_, v in enumerate(row):
                if v == '1':
                    for dy in range(2):
                        for dx in range(2): on |= (ix == 9 + li * 13 + c_ * 2 + dx) & (iy == 26 - (r_ * 2 + dy))
    rgb = paint([((cell & on).astype(np.float32), '#2F5A2B'), ((~cell).astype(np.float32) * .25, '#8FB01A')], '#C9DB7A')
    return Z, ONE, rgb
@reg('t160_shell', 'Grey console body', .6, .6, 3.0, tape='t160', proc='ABS · light texture · speaker grille', gloss='10 GU', role='Surface (Daylight)', hexes=['#D6D3DE'])
def _():
    st = fbm(0.22, 2); holes = Z.copy()
    for i in range(7):
        for j in range(7):
            if (i + j) % 2 == 0: holes = np.maximum(holes, disc(10 + i * 5, 10 + j * 5, 1.4, 0.15))
    return 0.15 * st + 0.85 * (1 - holes), ONE, paint([(holes, '#3E3A48')], '#D6D3DE')
@reg('t160_pills', 'Start / Select pills', .6, 2.0, 2.0, tape='t160', proc='Silicone · yellow · on grey ABS', gloss='10 GU', role='Highlight', hexes=['#FFD23F'])
def _():
    def pill(cx, cy): return np.clip(1 - (np.maximum(np.abs(xm - cx) - 5, 0) ** 2 + (ym - cy) ** 2) / 6.25, 0, 1)
    p = np.maximum(pill(16, 25), pill(34, 25)); m = (p > 0.02).astype(np.float32); st = fbm(0.22, 2)
    return 0.05 * st + np.sqrt(p), ONE, paint([(m, '#FFD23F')], '#D6D3DE')

# ---- C-46 DIGITAL DASH · 80s car dashboards
@reg('c46_vfd', 'Vacuum-fluorescent readout', .04, .05, 2.0, {'glass': '#07090B', 'emit': 6.0}, tape='c46', proc='VFD behind smoked acrylic · teal phosphor', gloss='95 GU', role='Primary readout', hexes=['#07090B', '#2EF2D0'])
def _():
    m = Z.copy()
    for i, ch in enumerate('046'): m = np.maximum(m, seg7(ch, 7 + i * 12.5, 15, 9, 18, 1.6))
    ghost = Z.copy()
    for i in range(3): ghost = np.maximum(ghost, seg7('8', 7 + i * 12.5, 15, 9, 18, 1.6))
    return Z, ONE, paint([(ghost * .15, '#0E3B36'), (m, '#2EF2D0')], '#07090B'), m
@reg('c46_soft', 'Soft-touch dash skin', .7, .8, 3.0, tape='c46', proc='TPO skin · leather-grain emboss · soft-touch', gloss='3 GU', role='Surface (Night)', hexes=['#10151A'])
def _():
    g = fbm(16, 3); cells = np.abs(g - 0.5) < 0.03
    return 0.6 * g - 0.5 * cells, ONE, paint([], '#10151A') * (0.9 + 0.2 * g[..., None])
@reg('c46_amber', 'Amber bar graph', .04, .05, 2.0, {'glass': '#07090B', 'emit': 5.0}, tape='c46', proc='VFD bar segments · amber filter', gloss='95 GU', role='Secondary readout / warning', hexes=['#FFB23E'])
def _():
    m = Z.copy()
    for i in range(10):
        hgt = 6 + i * 2.6; m = np.maximum(m, rect(5 + i * 4.2, 8, 5 + i * 4.2 + 2.8, 8 + hgt, 0.08) * (1 if i < 7 else 0))
        m = np.maximum(m, rect(5 + i * 4.2, 8, 5 + i * 4.2 + 2.8, 8 + hgt, 0.08) * (0.08 if i >= 7 else 0))
    return Z, ONE, paint([(m, '#FFB23E')], '#07090B'), (m > 0.5) * m
@reg('c46_bezel', 'Satin chrome bezel', .22, .5, 3.0, {'metal': 1, 'aniso': .6}, tape='c46', proc='ABS · satin chrome plate · lathe-turned rings', gloss='60 GU', role='Frame / divider', hexes=['#B8C0C8'])
def _():
    r = np.hypot(xm - 25, ym - 25); ring = 0.5 + 0.5 * np.sin(r * 9); lip = smooth(14, 15, r) * (1 - smooth(19, 20, r))
    return 0.15 * ring + 0.85 * lip, ONE, paint([], '#B8C0C8') * (0.93 + 0.1 * ring[..., None])
@reg('c46_lamp', 'Telltale lens', .08, .05, 2.0, {'glass': '#07090B', 'emit': 4.0}, tape='c46', proc='Red PC lens · masked icon · smoked cover', gloss='90 GU', role='Danger lamp', hexes=['#FF3B30'])
def _():
    body = rect(13, 16, 37, 32, 0.12) - rect(14.6, 17.6, 35.4, 30.4, 0.12); t1 = rect(17, 32, 21, 34.5, 0.1); t2 = rect(29, 32, 33, 34.5, 0.1)
    plus = np.maximum(rect(17.5, 23.3, 22.5, 24.7, 0.1), rect(19.3, 21.5, 20.7, 26.5, 0.1)); minus = rect(27.5, 23.3, 32.5, 24.7, 0.1)
    m = np.clip(body + t1 + t2 + plus + minus, 0, 1)
    return Z, ONE, paint([(m, '#FF3B30')], '#07090B'), m

TAPES_ORDER = ['t120', 't60', 't90', 't160', 'c46']

# ------------------------------------------------------------- scene
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SPP; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 10; sc.cycles.transmission_bounces = 10; sc.cycles.transparent_max_bounces = 16
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = os.environ.get('LOOK', 'AgX - Medium High Contrast')


def mkimg(arr, name, ch4):
    hpx, wpx = arr.shape[:2]; im = bpy.data.images.new(name, wpx, hpx, float_buffer=True, alpha=True)
    im.pixels.foreach_set(ch4[::-1].astype(np.float32).ravel()); im.pack(); im.colorspace_settings.name = 'Non-Color'; return im

def principled(name, rough):
    m = bpy.data.materials.new(name); m.use_nodes = True; return m, m.node_tree, m.node_tree.nodes['Principled BSDF']

def sample(key, at=(0, 0, 0), rot=0.0, gres=300):
    g = G[key]; out = g['f'](); X = g['extra']
    h, a, rgb = out[:3]; EM = out[3] if len(out) > 3 else None
    h, a, rgb = h[::-1].copy(), a[::-1].copy(), rgb[::-1].copy()   # image rows run top-down: keep glyphs and dials upright
    if EM is not None: EM = EM[::-1].copy()
    h = h - h.min(); h = h / max(h.max(), 1e-6)
    e = np.minimum(np.minimum(xm, W_MM - xm), np.minimum(ym, H_MM - ym)); rim = np.clip((e - 0.5) / 1.0, 0, 1); rim = rim * rim * (3 - 2 * rim)
    base = float(np.percentile(h, 15)); h = h * rim + base * (1 - rim); RIMB = base
    disp = mkimg(h, key + '_d', np.stack([h, h, h, ONE], -1))
    col = mkimg(h, key + '_c', np.concatenate([lin(rgb), a[..., None]], -1))
    hm = mkimg(h, key + '_h', np.stack([h, h, h, ONE], -1))
    W = W_MM / 1000; objs = []
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=gres, y_subdivisions=gres, size=1); o = bpy.context.active_object
    o.scale = (W, W, 1); bpy.ops.object.transform_apply(scale=True)
    tx = bpy.data.textures.new(key + '_t', 'IMAGE'); tx.image = disp; tx.extension = 'EXTEND'
    dm = o.modifiers.new('d', 'DISPLACE'); dm.texture = tx; dm.texture_coords = 'UV'; dm.strength = g['disp'] / 1000; dm.mid_level = 0
    so = o.modifiers.new('s', 'SOLIDIFY'); so.thickness = (0.00025 if RIMB is not None else g['thick'] / 1000); so.offset = -1
    o.location.z = g['thick'] / 1000
    m, nt, b = principled(key, g['rough']); N, L = nt.nodes, nt.links
    t = N.new('ShaderNodeTexImage'); t.image = col; t.interpolation = 'Cubic'
    th = N.new('ShaderNodeTexImage'); th.image = hm; th.interpolation = 'Cubic'
    L.new(t.outputs['Color'], b.inputs['Base Color']); L.new(t.outputs['Alpha'], b.inputs['Alpha'])
    bp = N.new('ShaderNodeBump'); bp.inputs['Distance'].default_value = .0004; bp.inputs['Strength'].default_value = .8
    L.new(th.outputs['Color'], bp.inputs['Height']); L.new(bp.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = g['rough']
    if X.get('metal'): b.inputs['Metallic'].default_value = X['metal']
    if X.get('aniso'):
        try: b.inputs['Anisotropic'].default_value = X['aniso']
        except Exception: pass
    if X.get('coat') or 'glass' in X:
        try: b.inputs['Coat Weight'].default_value = 1 if 'glass' in X else X['coat']; b.inputs['Coat Roughness'].default_value = .02
        except Exception: pass
    if 'tint' in X:   # translucent coloured plastic over a part you can see through it
        nt.links.remove(b.inputs['Base Color'].links[0]); b.inputs['Base Color'].default_value = list(lin(hx(X['tint']))) + [1]
        b.inputs['Transmission Weight'].default_value = .82; b.inputs['IOR'].default_value = 1.58; b.inputs['Roughness'].default_value = .1
    if EM is not None:
        ei = mkimg(EM, key + '_e', np.stack([EM, EM, EM, ONE], -1)); te = N.new('ShaderNodeTexImage'); te.image = ei; te.interpolation = 'Cubic'
        mu = N.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'; mu.inputs[1].default_value = X.get('emit', 3.0)
        L.new(te.outputs['Color'], mu.inputs[0]); L.new(mu.outputs['Value'], b.inputs['Emission Strength']); L.new(t.outputs['Color'], b.inputs['Emission Color'])
    o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth = True
    objs.append(o)
    if RIMB is not None and 'tint' not in X:   # solid slab under the displaced skin: clean, straight cut edges
        bz = float(h.min()) * g['disp'] / 1000; T = g['thick'] / 1000   # slab top at the deepest point, so holes and slots stay open
        bpy.ops.mesh.primitive_cube_add(size=1); sl = bpy.context.active_object
        sl.scale = (W * 0.9995, W * 0.9995, T); sl.location = (0, 0, o.location.z + bz - T / 2 - 0.00005)
        bpy.ops.object.transform_apply(scale=True); bv = sl.modifiers.new('b', 'BEVEL'); bv.width = 0.00025; bv.segments = 3
        sl.data.materials.append(m); objs.append(sl)
    if 'tint' in X:   # what you see through the translucent shell: a green PCB with traces
        tr = ((np.abs((xm + 0.4 * ym) % 7 - 3.5) < 0.35) | (np.abs(ym % 9 - 4.5) < 0.3)).astype(np.float32); pads = np.zeros_like(xm)
        for i in range(4):
            for j in range(4): pads = np.maximum(pads, disc(8 + i * 11, 8 + j * 11, 1.4, 0.1))
        pc = paint([(tr, '#C9A94A'), (pads, '#D8D2C0')], X['under'])
        if X.get('reel'):
            rr = np.hypot(xm - 25, ym - 25); tape = (rr < 21).astype(np.float32); hub = (rr < 7).astype(np.float32); teeth = ((rr < 5) & (np.abs(np.sin(np.arctan2(ym - 25, xm - 25) * 3)) > .5)).astype(np.float32)
            pc = paint([(tape * (0.85 + 0.15 * (np.sin(rr * 6) > 0)), '#3B2414'), (hub, '#EDE8DC'), (teeth, '#141318')], X['under'])
        kc = mkimg(pc[..., 0], key + '_u', np.concatenate([lin(pc), ONE[..., None]], -1))
        bpy.ops.mesh.primitive_plane_add(size=W * .94); u = bpy.context.active_object; u.location.z = .0004
        um, unt, ub = principled(key + 'u', .5); tt = unt.nodes.new('ShaderNodeTexImage'); tt.image = kc; unt.links.new(tt.outputs['Color'], ub.inputs['Base Color']); u.data.materials.append(um)
        objs.append(u)
    root = bpy.data.objects.new('root_' + key, None); sc.collection.objects.link(root)
    for ob in objs: ob.parent = root
    root.location = at; root.rotation_euler = (0, 0, rot); return root

order = list(G)
BOARD = KEY.startswith('TAPE:') or KEY == 'SHELF'
if KEY.startswith('TAPE:'):
    ks = [k for k in order if k.startswith(KEY[5:] + '_')]
    for i, k in enumerate(ks): sample(k, ((i - 2) * .058, 0, 0), math.radians(np.random.default_rng(i + 3).uniform(-2.5, 2.5)), 220)
elif KEY == 'SHELF':
    for r, tp in enumerate(TAPES_ORDER):
        ks = [k for k in order if k.startswith(tp + '_')]
        for i, k in enumerate(ks): sample(k, ((i - 2) * .058, (2 - r) * .058, 0), math.radians(np.random.default_rng(r * 7 + i).uniform(-2.5, 2.5)), 150)
else:
    sample(KEY, (0, 0, 0), math.radians(-8), int(os.environ.get("GRES", "360")))
bpy.ops.mesh.primitive_plane_add(size=3); fl = bpy.context.active_object; fm, fnt, fb = principled('paper', .9)
br = fnt.nodes.new('ShaderNodeTexBrick'); br.offset = 0; br.inputs['Scale'].default_value = 50; br.inputs['Mortar Size'].default_value = .012
for nm in ('Color1', 'Color2'): br.inputs[nm].default_value = list(lin(hx('#F2EEE6'))) + [1]
br.inputs['Mortar'].default_value = list(lin(hx('#DCD5C8'))) + [1]; br.inputs['Brick Width'].default_value = .5; br.inputs['Row Height'].default_value = .5
tc = fnt.nodes.new('ShaderNodeTexCoord'); fnt.links.new(tc.outputs['Object'], br.inputs['Vector']); fnt.links.new(br.outputs['Color'], fb.inputs['Base Color']); fl.data.materials.append(fm)
def area(loc, e, sz):
    bpy.ops.object.light_add(type='AREA', location=loc); l = bpy.context.active_object; l.data.energy = e; l.data.size = sz
    l.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
area(tuple(float(v) for v in os.environ.get('KEYL', '-.30,-.25,.45').split(',')), float(os.environ.get('KEYE', '7')), .35); area((.40, -.05, .25), 2.2, .45); area((.0, .45, .18), 3.0, .3)
for loc, stg in (((-.5, 0, .22), 1.0), ((.07, .28, .36), 0.0)):
    bpy.ops.mesh.primitive_plane_add(size=.5 if stg else .14, location=loc); c = bpy.context.active_object
    c.rotation_euler = (Vector((0, 0, .02)) - Vector(loc)).to_track_quat('Z', 'Y').to_euler()
    em = bpy.data.materials.new('card'); em.use_nodes = True; e = em.node_tree.nodes.new('ShaderNodeEmission'); e.inputs['Strength'].default_value = stg; e.inputs['Color'].default_value = (1, 1, 1, 1) if stg else (.01, .01, .01, 1)
    em.node_tree.links.new(e.outputs[0], em.node_tree.nodes['Material Output'].inputs[0]); c.data.materials.append(em); c.visible_camera = False; c.visible_shadow = False
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Strength'].default_value = float(os.environ.get('WS', '.5'))
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
if KEY.startswith('TAPE:'):
    cam.data.lens = float(os.environ.get('LENS', '70')); el = math.radians(float(os.environ.get('EL', '50'))); dist = float(os.environ.get('DIST', '.47')); ar = float(os.environ.get('AR', '.38')); tgt = Vector((0, -.004, 0))
elif KEY == 'SHELF':
    cam.data.lens = 70; el = math.radians(56); dist = float(os.environ.get('DIST', '.62')); ar = .9; tgt = Vector((0, -.004, 0))
else:
    cam.data.lens = 100; el = math.radians(float(os.environ.get('EL', '52'))); dist = float(os.environ.get('DIST', '.19')); ar = 1.0; tgt = Vector((0, .001, .002))
cam.location = (0, -dist * math.cos(el), dist * math.sin(el)); cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.dof.use_dof = True; cam.data.dof.focus_distance = (tgt - cam.location).length; cam.data.dof.aperture_fstop = 9 if BOARD else float(os.environ.get('FSTOP', '14'))
sc.render.resolution_x = RES; sc.render.resolution_y = int(RES * ar)
json.dump(SPEC, open('/home/claude/cmf/sp_spec.json', 'w'), indent=1)
sc.render.filepath = OUT; bpy.ops.render.render(write_still=True)
