"""PNEUMA - soft textile hand for HESTIA. First-pass actuator model + technical sheets.
Adapted from the Soft Robotics Toolkit's knit textile bending actuator (Harvard Biodesign Lab):
a bladder inside a pocket of one-way-stretch knit (top) over an inextensible woven (bottom).
Tigre Studio 2026. Hypothetical concept: hand calculations, not FEA or lab data.

usage: python3 tools/pneuma_model.py           -> data/pneuma.json + img/pn__model|pattern|control.webp
"""
import json, math, os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Rectangle, FancyBboxPatch, Polygon, FancyArrowPatch, Arc, Circle
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FD = '/tmp/fonts'  # TTF copies of fonts/*.woff2 (fontTools)
for f in os.listdir(FD): fm.fontManager.addfont(os.path.join(FD, f))
BLACK = fm.FontProperties(fname=f'{FD}/InterDisplay-Black.ttf')
MONO = 'JetBrains Mono'
plt.rcParams.update({'font.family': [MONO, 'DejaVu Sans'], 'font.size': 10, 'axes.edgecolor': '#1B1B1C', 'text.color': '#1B1B1C',
                     'axes.labelcolor': '#1B1B1C', 'xtick.color': '#1B1B1C', 'ytick.color': '#1B1B1C'})
PAPER, CARD, INK, HOT, GRID, MUTE = '#ECE8E0', '#F6F3EC', '#1B1B1C', '#FF5A1F', '#DCD7CC', '#6E6A64'
OAT, MOSS, TERRA, CHAMP, BIRCH = '#B9A787', '#5E6555', '#B65A3A', '#C9B48C', '#958E82'

def modern(ax, ytitle, xtitle):
    ax.set_facecolor(CARD); ax.set_axisbelow(True)
    for sp in ('top', 'right', 'left'): ax.spines[sp].set_visible(False)
    ax.spines['bottom'].set_color(INK); ax.spines['bottom'].set_linewidth(1.0)
    ax.tick_params(length=0, pad=6, colors=MUTE, labelsize=9)
    ax.grid(axis='y', color='#E3DDD0', lw=0.8); ax.grid(axis='x', visible=False)
    ax.set_xlabel(''); ax.set_ylabel('')
    ax.text(0, 1.04, ytitle, transform=ax.transAxes, fontsize=8.6, color=MUTE, ha='left', va='bottom')
    ax.text(1, -0.12, xtitle, transform=ax.transAxes, fontsize=8.6, color=MUTE, ha='right', va='top')
def end_lab(ax, x, y, txt, col, dy=0):
    ax.plot([x], [y], 'o', ms=7, mfc=col, mec=CARD, mew=1.5, clip_on=False, zorder=6)
    ax.annotate(txt, (x, y), xytext=(9, dy), textcoords='offset points', fontsize=8.8, va='center', color=INK, annotation_clip=False)

# ------------------------------------------------------------------ model
# Constant-curvature bending: the woven bottom is inextensible (neutral layer), so a top-layer
# strain eps over a pouch height h bends the finger by theta = L * eps / h.
# Pressure p on the pouch end cap (w x h) is shared by top and bottom: top tension per width N = p*h/2.
# Knit response: linear at small strain (stiffness k, N/mm per unit strain) locking out at eps_max.
KNITS = [  # name, k [N/mm], eps_max
    ('Light jersey', 0.55, 0.65),
    ('Power mesh', 0.80, 0.60),
    ('Spacer rib', 1.30, 0.50),
]
SEL = 1  # power mesh: the selected top layer
FINGERS = [  # name, L [mm], w [mm], h [mm]
    ('Thumb', 70, 24, 15), ('Index', 92, 22, 14), ('Middle', 98, 22, 14), ('Ring', 92, 22, 14), ('Little', 80, 19, 13)]
P_MAX, P_HOLD = 80.0, 70.0  # kPa gauge
SEAL_BURST = 200.0          # kPa, assumed minimum for heat-sealed TPU-coated nylon: to be tested
MUG_D, MUG_M, MU = 80.0, 0.45, 0.9  # mm, kg (350 ml mug + coffee), silicone dots on glazed ceramic (assumed)

def strain(p_kpa, h, k, emax):
    N = p_kpa / 1000.0 * h / 2.0                 # N/mm
    return emax * (1 - math.exp(-N / (k * emax)))  # linear k at the origin, lock-out at emax

def bend_deg(p, L, h, k, emax): return math.degrees(L * strain(p, h, k, emax) / h)

def p_for_curvature(R, h, k, emax):
    """pressure that bends the finger's woven side to radius R (mm)"""
    e = h / R
    if e >= emax: return float('nan')
    N = -k * emax * math.log(1 - e / emax)
    return N * 2 / h * 1000

def tip_force(p, w, h, L):  # blocked tip force [N] from the pressure moment about the woven layer
    return p / 1000 * w * h * h / 2 / L

def model():
    name, k, emax = KNITS[SEL]
    R = MUG_D / 2
    rows = []
    for fn, L, w, h in FINGERS:
        rows.append(dict(finger=fn, L=L, w=w, h=h,
                         theta_hold=round(bend_deg(P_HOLD, L, h, k, emax)),
                         wrap_deg=round(math.degrees(L / R)),
                         p_wrap=round(p_for_curvature(R, h, k, emax)),
                         F_tip=round(tip_force(P_HOLD, w, h, L), 2),
                         vol_cc=round(w * h * L * 0.7 / 1000, 1)))
    F_sum = sum(r['F_tip'] for r in rows)
    hold = MU * F_sum; need = MUG_M * 9.81
    vol = sum(r['vol_cc'] for r in rows)
    free_air = vol * (P_HOLD + 101.3) / 101.3
    # accumulator: 0.4 L charged to 150 kPa gauge, check it still sits above hold pressure after one grip
    VT, PT = 0.4, 150.0
    pt_after = ((PT + 101.3) * VT * 1000 - free_air * 101.3) / (VT * 1000) - 101.3
    curves = {kn: [[p, round(bend_deg(p, 92, 14, kk, em), 1)] for p in range(0, 81, 2)] for kn, kk, em in KNITS}
    return dict(knit=name, k=k, eps_max=emax, p_max=P_MAX, p_hold=P_HOLD, seal_burst=SEAL_BURST,
                seal_sf=round(SEAL_BURST / P_MAX, 1), fingers=rows, F_sum=round(F_sum, 1), hold_N=round(hold, 1),
                need_N=round(need, 1), margin=round(hold / need, 2), vol_cc=round(vol), free_air_cc=round(free_air),
                tank_L=VT, tank_kpa=PT, tank_after_kpa=round(pt_after), curves=curves,
                knits=[dict(name=n, k=kk, eps_max=em) for n, kk, em in KNITS])

# ------------------------------------------------------------------ sheet frame
W, H = 16, 11.8
def sheet(title, sub, tag):
    fig = plt.figure(figsize=(W, H), dpi=100); fig.patch.set_facecolor(PAPER)
    bg = fig.add_axes([0, 0, 1, 1]); bg.set_xlim(0, W); bg.set_ylim(0, H); bg.axis('off')
    for x in np.arange(0, W, 0.4): bg.axvline(x, color=GRID, lw=0.6, zorder=0)
    for y in np.arange(0, H, 0.4): bg.axhline(y, color=GRID, lw=0.6, zorder=0)
    bg.text(0.48, H - 0.85, title, fontproperties=BLACK, fontsize=46, color=INK, va='center')
    bg.text(0.5, H - 1.42, sub, fontsize=14, color=MUTE, va='center')
    bg.add_patch(Rectangle((0.48, 0.38), 3.0, 0.28, color=HOT, zorder=2))
    bg.text(0.58, 0.52, tag, fontsize=13, color=INK, va='center', zorder=3)
    bg.text(W - 0.48, 0.52, 'TIGRE STUDIO · PNEUMA · SOFT ROBOTICS · HYPOTHETICAL CONCEPT', fontsize=11, color=MUTE, va='center', ha='right')
    return fig, bg

def panel(bg, x, y, w, h, title=None):
    bg.add_patch(Rectangle((x, y), w, h, facecolor=CARD, edgecolor=INK, lw=1.6, zorder=1))
    if title: bg.text(x + 0.22, y + h - 0.36, title, fontsize=13, fontweight='bold', va='center', zorder=3)

def save(fig, name):
    p = f'/tmp/{name}.png'; fig.savefig(p, dpi=100, facecolor=PAPER); plt.close(fig)
    Image.open(p).convert('RGB').save(f'{ROOT}/img/pn__{name}.webp', quality=90)

# ------------------------------------------------------------------ sheet 1: bend model
def sheet_model(M):
    fig, bg = sheet('BEND MODEL', 'ONE-WAY STRETCH ON TOP, WOVEN BELOW · FIRST-PASS HAND CALCULATION, NOT FEA', '01 · MODELING')
    panel(bg, 0.48, 5.55, 6.9, 4.3, 'FINGER, IN SECTION')
    # section: woven bottom, bladder, knit top
    cx, cy = 2.95, 7.35
    t = np.linspace(0, np.pi, 80)
    bg.fill(np.r_[cx + 1.55 * np.cos(t), cx - 1.55], np.r_[cy + 1.15 * np.sin(t) ** 0.8, cy], color=OAT, zorder=3)
    bg.fill(np.r_[cx + 1.32 * np.cos(t), cx - 1.32], np.r_[cy + 0.12 + 0.93 * np.sin(t) ** 0.8, cy + 0.12], color='#E9D9A8', ec=INK, lw=0.8, zorder=4)
    bg.add_patch(Rectangle((cx - 1.75, cy - 0.12), 3.5, 0.14, color=BIRCH, zorder=5))
    for xx in np.arange(cx - 1.6, cx + 1.65, 0.16): bg.add_patch(Circle((xx, cy - 0.17), 0.05, color=TERRA, zorder=5))
    for x0, s in ((cx - 1.75, 1), (cx + 1.75, -1)): bg.plot([x0, x0 + s * 0.2], [cy - 0.05, cy - 0.05], color=INK, lw=2.5, zorder=6)
    lab = [(cx + 1.5, cy + 1.0, 'POWER-MESH KNIT · stretches along the finger'), (cx + 0.9, cy + 0.55, 'TPU BLADDER · heat-sealed'),
           (cx + 1.8, cy - 0.06, 'WOVEN · does not stretch'), (cx + 1.5, cy - 0.17, 'SILICONE-DOT GRIP · palm side')]
    for i, (x, y, s) in enumerate(lab):
        ty = cy + 1.75 - i * 0.62
        bg.plot([x, 5.3], [y, ty], color=INK, lw=0.7, zorder=6); bg.text(5.35, ty, s.split(' · ')[0], fontsize=9.5, fontweight='bold', va='center', zorder=6)
        bg.text(5.35, ty - 0.2, s.split(' · ')[1], fontsize=8.5, color=MUTE, va='center', zorder=6)
    bg.annotate('', (cx - 2.05, cy + 1.15), (cx - 2.05, cy), arrowprops=dict(arrowstyle='<->', lw=1, color=HOT), zorder=6)
    bg.text(cx - 2.2, cy + 0.57, 'h', fontsize=12, color=HOT, ha='right', va='center', zorder=6)
    bg.text(0.7, 6.05, 'θ = L · ε / h        N = p · h / 2        ε = ε_max (1 − e^(−N / k·ε_max))', fontsize=10.5, zorder=6)
    bg.text(0.7, 5.75, 'The woven layer is the neutral axis: every mm the knit grows over height h bends the finger.', fontsize=8.8, color=MUTE, zorder=6)
    # curves
    panel(bg, 7.75, 5.55, 7.77, 4.3)
    ax = fig.add_axes([0.53, 0.545, 0.315, 0.25])
    cols = ['#A9A397', HOT, INK]
    if P_MAX < 78:
        ax.axvspan(P_MAX, 80.5, facecolor='none', hatch='////', edgecolor=(1, .353, .122, .35), lw=0, zorder=0)
        ax.text(P_MAX + 0.8, 212, f'ABOVE\n{P_MAX:.0f} kPa', fontsize=7.8, color=HOT, va='top')
    wrap = math.degrees(92 / (MUG_D / 2))
    ax.axhline(wrap, color=MUTE, ls=(0, (4, 3)), lw=1.0); ax.text(1, wrap + 5, f'WRAPS AN {MUG_D:.0f} mm MUG · {wrap:.0f}°', fontsize=7.8, color=MUTE)
    pw = [r for r in M['fingers'] if r['finger'] == 'Index'][0]['p_wrap']
    sel = None
    offs = {INK: -6, '#A9A397': 6, HOT: 0}
    for (kn, pts), c in zip(M['curves'].items(), cols):
        pts = np.array(pts); ax.plot(pts[:, 0], pts[:, 1], color=c, lw=2.6 if c == HOT else 1.9, solid_capstyle='round', zorder=4 if c == HOT else 3)
        end_lab(ax, pts[-1, 0], pts[-1, 1], kn.upper() + (' ◀ PICK' if c == HOT else ''), c, offs[c])
        if c == HOT: sel = pts
    yw = float(np.interp(pw, sel[:, 0], sel[:, 1]))
    ax.plot([pw], [yw], 'o', ms=6.5, mfc=CARD, mec=HOT, mew=1.6, zorder=6)
    ax.annotate(f'{pw} kPa', (pw, yw), xytext=(pw - 4, yw - 40), fontsize=8.4, color=HOT, arrowprops=dict(arrowstyle='-', color=HOT, lw=.8, shrinkA=2, shrinkB=4))
    ax.set_xlim(0, 80.5); ax.set_ylim(0, 220)
    modern(ax, 'BEND, INDEX FINGER · DEGREES', 'PRESSURE · kPa')
    # table
    cols_x = [0.48, 2.3, 3.6, 4.9, 6.2, 7.9, 9.9, 12.0, 13.8]
    hdr = ['FINGER', 'L', 'W × H', 'BEND @70', 'WRAP NEEDS', 'PRESSURE TO WRAP', 'TIP FORCE @70', 'AIR', '']
    bg.add_patch(Rectangle((0.48, 4.62), 15.04, 0.42, color=INK, zorder=2))
    for x, s in zip(cols_x, hdr): bg.text(x + 0.12, 4.83, s, color=CARD, fontsize=10, va='center', fontweight='bold', zorder=3)
    for i, r in enumerate(M['fingers']):
        y = 4.3 - i * 0.46
        vals = [r['finger'], f"{r['L']} mm", f"{r['w']} × {r['h']} mm", f"{r['theta_hold']}°", f"{r['wrap_deg']}°", f"{r['p_wrap']} kPa", f"{r['F_tip']} N", f"{r['vol_cc']} cm³"]
        for j, (x, s) in enumerate(zip(cols_x, vals)):
            bg.text(x + 0.12, y, s, fontsize=10.5, va='center', fontweight='bold' if j == 0 else 'normal', zorder=3)
        bg.plot([0.48, 15.52], [y - 0.23, y - 0.23], color=INK, lw=0.6, zorder=3)
    notes = [f"→ Power mesh closes every finger around an {MUG_D:.0f} mm mug at {min(r['p_wrap'] for r in M['fingers'])}–{max(r['p_wrap'] for r in M['fingers'])} kPa and keeps {P_MAX - max(r['p_wrap'] for r in M['fingers']):.0f} kPa in reserve for squeeze.",
             f"→ Hold at {P_HOLD:.0f} kPa: {M['F_sum']} N of tip force × μ {MU} = {M['hold_N']} N against a {MUG_M*1000:.0f} g mug ({M['need_N']} N): {M['margin']}× margin.",
             f"→ Max {P_MAX:.0f} kPa against an assumed {SEAL_BURST:.0f} kPa seal burst: safety factor {M['seal_sf']}. Light jersey over-bends; spacer rib needs > {P_MAX:.0f} kPa.",
             '* Assumed: knit stiffness from datasheet-range values, constant curvature, rigid woven layer. Replace with a tensile test.']
    for i, s in enumerate(notes): bg.text(0.48, 1.85 - i * 0.3, s, fontsize=10 if i < 3 else 9.5, color=INK if i < 3 else MUTE)
    save(fig, 'model')

# ------------------------------------------------------------------ sheet 2: flat pattern
def outline(L, w, tab=14, tip=0.86, n=40):
    """finger panel outline: straight root tab, taper to tip, round tip; returns closed (x,y) in mm"""
    wt = w * tip
    t = np.linspace(-np.pi / 2, np.pi / 2, n)
    tipx = L - wt / 2 + (wt / 2) * np.cos(t); tipy = (wt / 2) * np.sin(t)
    up = [(-tab, -w / 2), (0, -w / 2), (L - wt / 2, -wt / 2)] + list(zip(tipx, tipy)) + [(L - wt / 2, wt / 2), (0, w / 2), (-tab, w / 2)]
    return np.array(up)

def offset(poly, d):
    from shapely.geometry import Polygon as SP
    g = SP(poly).buffer(d, join_style=1)
    return np.array(g.exterior.coords)

def sheet_pattern(M):
    fig, bg = sheet('FLAT PATTERN', 'ONE HAND = 5 POCKETS · GENERATED FROM THE FINGER TABLE, LIKE A GRASSHOPPER DEFINITION', '02 · FABRICATION')
    S = 0.0192  # sheet units per mm
    panel(bg, 0.48, 4.35, 15.04, 5.5, 'NEST · ONE HAND · REDUCED SCALE')
    rows_y = [8.55, 7.4, 6.25, 5.1]
    labels = [('A · KNIT TOP', '×5 · power mesh'), ('B · WOVEN BASE', '×5 · 210D nylon'), ('C · TPU BLADDER', '×5 · 2 plies'), ('D · GRIP PRINT', 'silicone dots on B')]
    fills = [OAT, BIRCH, '#E9D9A8', TERRA]
    for ri, (y0, (l1, l2), fc) in enumerate(zip(rows_y, labels, fills)):
        bg.text(0.75, y0 + 0.1, l1, fontsize=10, fontweight='bold', va='center', zorder=4)
        bg.text(0.75, y0 - 0.17, l2, fontsize=8.5, color=MUTE, va='center', zorder=4)
        x0 = 2.75
        for fn, L, w, h in FINGERS:
            wtop = w + h if ri == 0 else w
            L2, w2 = (L - 4, w - 3) if ri == 2 else (L, wtop)
            tab = 30 if ri == 2 else 14
            pts = outline(L2, w2, tab=tab, tip=0.86)
            if ri == 2:  # bladder: narrow inlet tail
                pts = np.array([p if p[0] >= -2 else (p[0], np.sign(p[1]) * 3) for p in pts])
            T = lambda q: np.c_[x0 + (q[:, 0] + tab) * S, y0 + q[:, 1] * S]
            if ri == 3:
                bg.add_patch(Polygon(T(pts), closed=True, fc='none', ec=INK, lw=0.8, ls=(0, (2, 2)), zorder=3))
                inner = outline(L - 18, w - 6, tab=0); Q = T(inner + np.array([9, 0]))
                bg.add_patch(Polygon(Q, closed=True, fc=TERRA, ec='none', zorder=3))
                for xx in np.arange(Q[:, 0].min() + 0.05, Q[:, 0].max() - 0.06, 0.065):
                    for yy in np.arange(Q[:, 1].min() + 0.045, Q[:, 1].max() - 0.03, 0.065):
                        bg.add_patch(Circle((xx, yy), 0.014, color='#7E3A24', zorder=4))
            else:
                bg.add_patch(Polygon(T(pts), closed=True, fc=fc, ec=INK, lw=1.0, zorder=3))
                if ri == 2:  # 4 mm heat-seal margin
                    bg.add_patch(Polygon(T(offset(pts, -4)), closed=True, fc='none', ec=HOT, lw=1.3, ls=(0, (3, 2)), zorder=4))
                else:  # 6 mm seam allowance -> sew line
                    bg.add_patch(Polygon(T(offset(pts, -6)), closed=True, fc='none', ec=INK, lw=0.7, ls=(0, (1, 1.5)), zorder=4))
                    for nx in (0, L2 * 0.5):  # notches
                        half = np.interp(nx, [0, L2 - w2 * 0.43], [w2 / 2, w2 * 0.43])
                        for sgn in (1, -1):
                            yy = y0 + sgn * half * S
                            bg.plot([x0 + (nx + tab) * S] * 2, [yy, yy - sgn * 0.09], color=INK, lw=1.3, zorder=5)
                a, b = x0 + (L2 * 0.2 + tab) * S, x0 + (L2 * 0.72 + tab) * S
                if ri == 0: bg.annotate('', (b, y0), (a, y0), arrowprops=dict(arrowstyle='<->', color=HOT, lw=1.6), zorder=5)
                if ri == 1: bg.annotate('', (b, y0), (a, y0), arrowprops=dict(arrowstyle='-|>', color=INK, lw=1.0), zorder=5)
            if ri == 0: bg.text(x0 + tab * S, y0 + (w2 / 2) * S + 0.14, f'{fn.upper()} · {L} mm', fontsize=7.8, color=MUTE, zorder=5)
            x0 += (L2 + tab + 22) * S
    panel(bg, 0.48, 2.25, 15.04, 1.75, 'KEY')
    leg = [('arrow', HOT, 'Stretch direction', 'knit wales along the finger'), ('arrow', INK, 'Grain line', 'woven warp along the finger'),
           ('dash', HOT, 'Heat seal · 4 mm', '150 °C · 15 s'), ('dot', INK, 'Sew line · 6 mm', 'seam allowance'),
           ('notch', INK, 'Notches', 'match A to B')]
    for i, (kind, c, h1, h2) in enumerate(leg):
        x, y = 0.75 + i * 3.0, 3.1
        if kind == 'arrow': bg.annotate('', (x + 0.55, y), (x, y), arrowprops=dict(arrowstyle='<->' if c == HOT else '-|>', color=c, lw=1.5), zorder=5)
        elif kind == 'dash': bg.plot([x, x + 0.55], [y, y], color=c, lw=1.5, ls=(0, (3, 2)), zorder=5)
        elif kind == 'dot': bg.plot([x, x + 0.55], [y, y], color=c, lw=1, ls=(0, (1, 1.5)), zorder=5)
        else: bg.plot([x + 0.27, x + 0.27], [y + 0.09, y - 0.09], color=c, lw=1.6, zorder=5)
        bg.text(x + 0.75, y + 0.1, h1, fontsize=9.5, fontweight='bold', va='center', zorder=5); bg.text(x + 0.75, y - 0.16, h2, fontsize=8, color=MUTE, va='center', zorder=5)
    bg.text(0.75, 2.55, 'Knit top = w + h wide, to cover the bulge  ·  bladder 2 mm inside the pocket  ·  inlet tail 6 × 30 mm  ·  15 cut parts + 5 prints per hand',
            fontsize=9, zorder=5)
    notes = ['→ Every outline is computed from L, w and h in the finger table: change a finger and the nest, seal and sew lines regenerate.',
             '→ Same build as the toolkit: cut, seal the bladder, sew the pocket inside out, turn, insert, then fit the inlet barb.',
             '* Shown at reduced scale. A full-size DXF comes from the same script.']
    for i, s in enumerate(notes): bg.text(0.48, 1.7 - i * 0.3, s, fontsize=10 if i < 2 else 9.5, color=INK if i < 2 else MUTE)
    save(fig, 'pattern')

# ------------------------------------------------------------------ sheet 3: control
def sheet_control(M):
    fig, bg = sheet('CONTROL', 'THE TOOLKIT CONTROL BOARD, CUT DOWN TO FIT A FOREARM', '03 · CONTROL')
    panel(bg, 0.48, 4.6, 7.6, 5.25, 'PNEUMATIC LOOP')
    def blk(x, y, w, h, t, s='', fc=CARD, tc=INK):
        bg.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.02,rounding_size=0.08', fc=fc, ec=INK, lw=1.3, zorder=4))
        bg.text(x + w / 2, y + h / 2 + (0.1 if s else 0), t, ha='center', va='center', fontsize=9.5, fontweight='bold', color=tc, zorder=5)
        if s: bg.text(x + w / 2, y + h / 2 - 0.18, s, ha='center', va='center', fontsize=7.8, color=MUTE if tc == INK else tc, zorder=5)
    def arr(a, b, c=INK, ls='-'):
        bg.add_patch(FancyArrowPatch(a, b, arrowstyle='-|>', mutation_scale=12, color=c, lw=1.4, ls=ls, zorder=3))
    blk(0.8, 7.9, 1.6, 0.8, 'PUMP', '12 V diaphragm')
    blk(2.9, 7.9, 1.6, 0.8, 'ACCUMULATOR', f"{M['tank_L']} L · {M['tank_kpa']:.0f} kPa")
    blk(5.1, 8.55, 1.4, 0.65, 'V1', 'fingers in')
    blk(5.1, 7.45, 1.4, 0.65, 'V2', 'thumb in')
    blk(6.75, 8.55, 1.15, 0.65, 'FINGERS', '4 pockets')
    blk(6.75, 7.45, 1.15, 0.65, 'THUMB', '1 pocket')
    blk(5.1, 6.35, 2.8, 0.65, 'V3 · V4', 'exhaust: fingers · thumb')
    blk(0.8, 5.0, 3.7, 0.95, 'ARDUINO NANO', 'PWM 30 Hz · MOSFET drivers', fc=INK, tc=CARD)
    blk(5.1, 5.0, 2.8, 0.95, 'PRESSURE SENSORS', 'tank · fingers · thumb')
    arr((2.4, 8.3), (2.9, 8.3)); arr((4.5, 8.4), (5.1, 8.85)); arr((4.5, 8.2), (5.1, 7.8))
    arr((6.5, 8.88), (6.75, 8.88)); arr((6.5, 7.78), (6.75, 7.78))
    arr((7.3, 8.55), (7.3, 7.0)); arr((7.0, 7.45), (7.0, 7.0))
    arr((5.1, 5.45), (4.5, 5.45), HOT, '--')
    arr((1.6, 5.95), (1.6, 7.9), MUTE, ':'); arr((4.5, 5.85), (5.1, 6.55), MUTE, ':')
    bg.text(1.7, 6.9, 'pump', fontsize=8, color=MUTE, va='center', zorder=5)
    bg.text(4.62, 6.35, 'valves', fontsize=8, color=MUTE, va='center', ha='right', zorder=5)
    bg.text(4.8, 5.72, 'feedback', fontsize=8, color=HOT, va='center', ha='center', zorder=5)
    # sequence chart
    panel(bg, 8.45, 4.6, 7.07, 5.25)
    ax = fig.add_axes([0.57, 0.445, 0.38, 0.31])
    tt = np.linspace(0, 5, 500)
    def env(t, pts):
        return np.interp(t, [p[0] for p in pts], [p[1] for p in pts])
    th = env(tt, [(0, 0), (0.2, 0), (0.6, 30), (1.4, 32), (1.8, 70), (4.0, 70), (4.4, 0), (5, 0)])
    fg = env(tt, [(0, 0), (0.6, 0), (1.4, 55), (1.8, 70), (4.0, 70), (4.5, 0), (5, 0)])
    rip = np.where((tt > 1.9) & (tt < 4.0), 1.8 * np.sin(tt * 2 * np.pi * 3.2), 0)
    for k, (x0, x1, s_) in enumerate([(0, 0.6, 'PRE-SHAPE'), (0.6, 1.4, 'WRAP'), (1.4, 1.9, 'SQUEEZE'), (1.9, 4.0, 'HOLD ±3 kPa'), (4.0, 4.6, 'VENT')]):
        if k % 2: ax.axvspan(x0, x1, color=INK, alpha=0.035, lw=0, zorder=0)
        ax.text((x0 + x1) / 2, 86, s_, ha='center', fontsize=7.6, color=INK if k == 3 else MUTE)
    ax.fill_between(tt, fg + rip, 0, color=HOT, alpha=0.08, lw=0, zorder=1)
    ax.plot(tt, fg + rip, color=HOT, lw=2.6, zorder=4, solid_capstyle='round'); ax.plot(tt, th + rip * 0.7, color=INK, lw=1.9, zorder=3, solid_capstyle='round')
    ax.axhline(55, color=HOT, ls=(0, (2, 3)), lw=1); ax.text(4.95, 57, 'WRAP 55 kPa', fontsize=7.8, color=HOT, ha='right')
    ax.annotate('THUMB PRE-SHAPES', (0.9, 31), xytext=(0.15, 46), fontsize=8.2, color=INK, arrowprops=dict(arrowstyle='-', color=INK, lw=.8, shrinkA=2, shrinkB=2))
    ax.annotate('FINGERS WRAP', (1.25, 47), xytext=(1.95, 30), fontsize=8.2, color=HOT, arrowprops=dict(arrowstyle='-', color=HOT, lw=.8, shrinkA=2, shrinkB=2))
    ax.set_xlim(0, 5); ax.set_ylim(0, 92); ax.set_yticks(range(0, 91, 30))
    modern(ax, 'PRESSURE · kPa', 'TIME · s')
    for x_, c_, t_ in ((0.0, HOT, 'FINGERS'), (0.9, INK, 'THUMB')):
        ax.plot([x_ + 3.0, x_ + 3.25], [1.07, 1.07], color=c_, lw=2.4, transform=ax.get_xaxis_transform(), clip_on=False)
        ax.text(x_ + 3.3, 1.07, t_, fontsize=8.2, va='center', transform=ax.get_xaxis_transform())
    rows = [('One grip of air', f"{M['vol_cc']} cm³ of pockets = {M['free_air_cc']} cm³ of free air at {M['p_hold']:.0f} kPa"),
            ('From the tank', f"{M['tank_L']} L at {M['tank_kpa']:.0f} kPa drops to {M['tank_after_kpa']} kPa: still above hold, so the grip never waits on the pump"),
            ('Hold', 'PWM on V1/V2 keeps ±3 kPa around 70; the pump only tops up the tank'),
            ('Fail-safe', 'Valves are normally open to exhaust: power off = hand opens, nothing is ever trapped')]
    bg.add_patch(Rectangle((0.48, 3.72), 15.04, 0.42, color=INK, zorder=2))
    for x, s in ((0.6, 'STEP'), (3.4, 'NUMBERS')): bg.text(x, 3.93, s, color=CARD, fontsize=10, fontweight='bold', va='center', zorder=3)
    for i, (a, b) in enumerate(rows):
        y = 3.42 - i * 0.44
        bg.text(0.6, y, a, fontsize=10.5, fontweight='bold', va='center', zorder=3); bg.text(3.4, y, b, fontsize=10, va='center', zorder=3)
        bg.plot([0.48, 15.52], [y - 0.22, y - 0.22], color=INK, lw=0.6, zorder=3)
    bg.text(0.48, 1.05, '* Valve and sensor choices follow the toolkit board (solenoid valves, MOSFETs, PWM, analog pressure sensors). Timings are targets, not measurements.', fontsize=9.5, color=MUTE)
    save(fig, 'control')

if __name__ == '__main__':
    M = model()
    json.dump(M, open(f'{ROOT}/data/pneuma.json', 'w'), indent=1)
    print(json.dumps({k: v for k, v in M.items() if k != 'curves'}, indent=1))
    sheet_model(M); sheet_pattern(M); sheet_control(M)
