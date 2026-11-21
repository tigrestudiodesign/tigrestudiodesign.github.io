import json, math, sys
from PIL import Image, ImageDraw, ImageFont
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt; import matplotlib.ticker
H = '/home/claude/hestia/'; R = H + 'r/'; OUT = '/home/claude/tigrestudiodesign.github.io/img/'
mono = lambda s: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', s)
monob = lambda s: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', s)
blk = lambda s: ImageFont.truetype('/usr/share/fonts/opentype/inter/InterDisplay-Black.otf', s)
BG = (236, 232, 224); GRID = (216, 210, 199); OR = (255, 90, 31); INK = (26, 26, 28); GREY = (96, 92, 86); CARD = (246, 243, 236)
C = json.load(open(H + 'calc.json'))
SW = [('OATMEAL', '#B9A787', '3D knit outer skin'), ('BIRCH', '#ABA498', 'pelvis, shins, vent mesh'), ('SLATE-MOSS', '#5E6555', 'rib flex sleeves, feet'),
      ('TERRACOTTA', '#B65A3A', 'silicone grip knit'), ('CHAMPAGNE', '#B49C74', 'anodised hand + handle'), ('WEAVE', '#2A2B2B', 'sensor + LiDAR windows')]

def base(W, Hh, step=40):
    im = Image.new('RGB', (W, Hh), BG); d = ImageDraw.Draw(im)
    for x in range(0, W, step): d.line([(x, 0), (x, Hh)], fill=GRID)
    for y in range(0, Hh, step): d.line([(0, y), (W, y)], fill=GRID)
    return im, d
def header(d, W, Hh, title, sub, tag):
    d.text((48, 58), title, font=blk(50), fill=INK, anchor='lm'); d.text((50, 102), sub, font=mono(17), fill=GREY, anchor='lm')
    d.rectangle((48, Hh - 64, 48 + 300, Hh - 38), fill=OR); d.text((58, Hh - 51), tag, font=mono(16), fill=INK, anchor='lm')
    d.text((W - 48, Hh - 51), 'TIGRE STUDIO · HESTIA · SOFT GOODS CMF · UNOFFICIAL CONCEPT', font=mono(14), fill=GREY, anchor='rm')
def hexrgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def tag(d, x, y, n):
    d.rectangle((x, y, x + 40, y + 30), fill=OR); d.text((x + 20, y + 15), n, font=monob(16), fill=INK, anchor='mm')
def paste_fit(im, src, box, cover=True):
    x0, y0, x1, y1 = box; w, h = x1 - x0, y1 - y0
    s = (max if cover else min)(w / src.width, h / src.height); r = src.resize((int(src.width * s), int(src.height * s)), Image.LANCZOS)
    cx, cy = (r.width - w) // 2, (r.height - h) // 2
    im.paste(r.crop((cx, cy, cx + w, cy + h)) if cover else r, (x0, y0) if cover else (x0 + (w - r.width) // 2, y0 + (h - r.height) // 2))
from matplotlib import font_manager as _fm
_fm.fontManager.addfont('/home/claude/cmf/gf/JetBrainsMono.ttf')
CK = '#f6f3ec'; CI = '#1a1a1c'; CG = '#6b665e'; CO = '#ff5a1f'; CM = '#5e6555'; CL = '#e3ddd0'
def chart_style():
    plt.rcParams.update({'font.family': 'JetBrains Mono', 'font.size': 11, 'text.color': CI, 'axes.facecolor': CK, 'figure.facecolor': CK,
                         'axes.edgecolor': CI, 'axes.linewidth': 1.0, 'axes.grid': True, 'axes.grid.axis': 'y', 'grid.color': CL, 'grid.linewidth': 0.8,
                         'axes.spines.top': False, 'axes.spines.right': False, 'axes.spines.left': False, 'xtick.color': CG, 'ytick.color': CG,
                         'xtick.major.size': 0, 'ytick.major.size': 0, 'xtick.major.pad': 7, 'ytick.major.pad': 6, 'hatch.linewidth': 0.7})
def chart_frame(ax, ytitle, xtitle):
    ax.text(0, 1.06, ytitle, transform=ax.transAxes, fontsize=10.4, color=CG, ha='left', va='bottom')
    ax.text(1, -0.13, xtitle, transform=ax.transAxes, fontsize=10.4, color=CG, ha='right', va='top')
    ax.set_axisbelow(True)
def end_label(ax, x, y, txt, col, dy=0):
    ax.annotate(txt, (x, y), xytext=(10, dy), textcoords='offset points', va='center', ha='left', fontsize=10.7, color=CI, annotation_clip=False)
    ax.plot([x], [y], 'o', ms=8, mfc=col, mec=CK, mew=1.6, clip_on=False, zorder=6)
def series(ax, x, y, col, lw=2.5, ls='-', z=3, log=False):
    (ax.semilogx if log else ax.plot)(x, y, color=col, lw=lw, ls=ls, solid_capstyle='round', dash_capstyle='round', zorder=z)

# ---------- 1. CMF: palette + material matrix + yarn macros
def cmf():
    W, Hh = 1600, 1180; im, d = base(W, Hh); header(d, W, Hh, 'WARM MINIMALIST', 'PALETTE · MATERIAL MATRIX · PERFORMANCE TARGETS', '01 · CMF')
    x = 48
    for i, (n, hx, use) in enumerate(SW):
        x0 = 48 + i * 252; d.rectangle((x0, 150, x0 + 232, 330), fill=hexrgb(hx), outline=INK, width=2)
        d.text((x0, 350), n, font=monob(17), fill=INK); d.text((x0, 376), hx.upper(), font=mono(15), fill=GREY); d.text((x0, 400), use, font=mono(13), fill=GREY)
    rows = [('ZONE', 'CONSTRUCTION', 'WHY', 'TARGET'),
            ('Outer skin', '3D knit, recycled PES / wool, hydrophobic finish', 'heathered upholstery feel, wipes clean', 'Martindale ≥ 40,000 · TB 117-2013 cover fabric'),
            ('Flex sleeves', 'Elastane rib knit, 6–8 mm pleats', 'unfolds before it stretches', '≤ 30 % fabric strain · 10,000 cycles'),
            ('Vent zones', 'Spacer mesh under perforated knit', 'air in at the flanks, out at the back', '≥ 68 cm² open area · ≤ 1.5 m/s'),
            ('Grip zones', 'Silicone-dot knit, terracotta', 'shows where to hold and guide', 'dry + wet grip, no tack transfer'),
            ('Sensor windows', 'Open technical weave, graphite', 'optically and acoustically clear', 'depth / LiDAR return unchanged (to test)'),
            ('Hard accents', 'Anodised aluminium, champagne', 'hand, handle, collar: touch points', 'scratch, sweat, cleaner resistant')]
    cw = [230, 470, 410, 410]; y = 460
    for r, row in enumerate(rows):
        h = 52 if r else 40; x = 48
        if r == 0: d.rectangle((48, y, 48 + sum(cw), y + h), fill=INK)
        else: d.line([(48, y + h), (48 + sum(cw), y + h)], fill=INK)
        for j, t in enumerate(row):
            d.text((x + 12, y + h / 2), t, font=(monob(14) if r == 0 or j == 0 else mono(14)), fill=((255, 255, 255) if r == 0 else (INK if j == 0 else GREY)), anchor='lm'); x += cw[j]
        y += h
    for i, (f, lab) in enumerate([('macro_oat.png', 'OATMEAL JERSEY · 3D YARN'), ('macro_rib.png', 'SLATE-MOSS RIB · 3D YARN')]):
        x0 = 48 + i * 530; src = Image.open(R + f).convert('RGB'); paste_fit(im, src, (x0, 860, x0 + 500, 1070)); d.rectangle((x0, 860, x0 + 500, 1070), outline=INK, width=2)
        d.text((x0, 1082), lab, font=mono(13), fill=GREY)
    d.text((1120, 880), 'Every colour is a neutral', font=monob(16), fill=INK); d.text((1120, 906), 'from a living room; the only', font=mono(14), fill=GREY)
    d.text((1120, 928), 'hot colour (terracotta) marks', font=mono(14), fill=GREY); d.text((1120, 950), 'the places you may touch.', font=mono(14), fill=GREY)
    im.save(OUT + 'hs__cmf.webp', quality=88)

# ---------- 2. ZONE MAP
def zones():
    W, Hh = 1600, 1250; im, d = base(W, Hh); header(d, W, Hh, 'ZONE MAP', 'WHERE EACH TEXTILE GOES, AND WHY', '02 · ZONES')
    src = Image.open(R + 'F_zones.png').convert('RGB').crop((190, 70, 810, 1230))
    box = (520, 140, 1080, 1140); d.rectangle(box, fill=CARD, outline=INK, width=2)
    k = min(556 / src.width, 996 / src.height); r = src.resize((int(src.width * k), int(src.height * k)), Image.LANCZOS)
    ox = 522 + (556 - r.width) // 2; oy = 142 + (996 - r.height) // 2; im.paste(r, (ox, oy))
    P = lambda x, y: (ox + (x - 190) * k, oy + (y - 70) * k)
    calls = [((470, 120), (1250, 200), '01', 'SENSOR WEAVE', ['LiDAR crown + depth band', 'open graphite weave']),
             ((640, 340), (1250, 380), '02', 'RIB FLEX SLEEVES', ['shoulder · elbow · waist', 'hip · knee · ankle']),
             ((655, 600), (1250, 560), '03', 'TERRACOTTA GRIP', ['forearms + sternum tab', 'silicone-dot knit']),
             ((660, 730), (1250, 740), '04', 'CHAMPAGNE HANDS', ['anodised · terracotta palm']),
             ((420, 300), (380, 200), '05', 'OATMEAL 3D KNIT', ['outer skin, quilted', 'channels on the torso']),
             ((385, 470), (380, 420), '06', 'VENT MESH', ['flanks in, back out', 'spacer mesh plenum']),
             ((440, 980), (380, 700), '07', 'BIRCH KNIT', ['pelvis + shins', 'darker = hides scuffs']),
             ((440, 1205), (380, 980), '08', 'SLATE-MOSS FEET', ['soft pads, floor-safe'])]
    for (sx, sy), (tx, ty), n, t, sub in calls:
        px, py = P(sx, sy); right = tx > 900
        d.line([(px, py), (tx, ty)], fill=INK, width=2); d.ellipse((px - 7, py - 7, px + 7, py + 7), fill=OR, outline=INK, width=2)
        x2 = tx + 300 if right else tx - 330; d.line([(tx, ty), (x2, ty)], fill=INK, width=2); bx = tx if right else x2
        tag(d, bx, ty - 38, n); d.text((bx + 52, ty - 23), t, font=monob(16), fill=INK, anchor='lm')
        for i, l in enumerate(sub): d.text((bx, ty + 16 + i * 20), l, font=mono(14), fill=GREY, anchor='lm')
    im.save(OUT + 'hs__zones.webp', quality=88)

# ---------- 3. FLEX ZONES: pleats instead of stretch
def flex():
    chart_style()
    fig, ax = plt.subplots(figsize=(8.12, 3.70), dpi=200)
    th = [i for i in range(0, 121, 1)]
    ro, L0, p = 0.068, 0.150, 0.0115; n = L0 / p; h = next(f for f in C['flex'] if f['joint'] == 'Knee')['pleat_h_mm'] / 1000
    c = 2 * math.sqrt((p / 2) ** 2 + h ** 2); reserve = n * (c - p)
    flat = [ro * math.radians(t) / L0 * 100 for t in th]
    pl = [max(0, ro * math.radians(t) - reserve) / (n * c) * 100 for t in th]
    ax.axhspan(30, 100, facecolor='none', hatch='////', edgecolor=(1, .353, .122, .17), lw=0, zorder=0)
    ax.text(3, 93, 'OVER THE STRAIN LIMIT', fontsize=9.9, color=CO, va='top')
    ax.axhline(30, color=CO, lw=1.1, ls=(0, (4, 3)), zorder=2); ax.text(119, 32.5, '30 % LIMIT', fontsize=9.9, color=CO, ha='right', va='bottom')
    ax.fill_between(th, pl, 0, color=CO, alpha=.10, lw=0, zorder=1)
    series(ax, th, flat, CI); series(ax, th, pl, CO, lw=3.0, z=4)
    x30 = next(t for t, v in zip(th, flat) if v >= 30); x0 = next(t for t, v in zip(th, pl) if v > 0)
    ax.plot([x30], [30], 'o', ms=6, mfc=CK, mec=CI, mew=1.6, zorder=6)
    ax.annotate(f'FLAT KNIT PASSES 30 %\nAT {x30}° OF FLEXION', (x30, 30), xytext=(x30 + 26, 40), fontsize=9.9, color=CI, ha='left', va='center',
                arrowprops=dict(arrowstyle='-', color=CI, lw=.8, shrinkA=4, shrinkB=5))
    ax.annotate(f'PLEATS UNFOLD FIRST:\n0 % STRAIN TO {x0}°', (x0, 0), xytext=(x0 - 4, 9), fontsize=9.9, color=CO, ha='right', va='center',
                arrowprops=dict(arrowstyle='-', color=CO, lw=.8, shrinkA=3, shrinkB=3))
    end_label(ax, 120, flat[-1], f'FLAT KNIT  {flat[-1]:.1f} %', CI); end_label(ax, 120, pl[-1], f'PLEATED RIB  {pl[-1]:.1f} %', CO)
    ax.set_xlim(0, 120); ax.set_ylim(0, 100); ax.set_xticks(range(0, 121, 20)); ax.set_xticklabels([f'{v}°' for v in range(0, 121, 20)])
    ax.set_yticks(range(0, 101, 25)); ax.set_yticklabels([f'{v}' for v in range(0, 101, 25)])
    chart_frame(ax, 'FABRIC STRAIN · %', 'KNEE FLEXION · DEGREES')
    fig.subplots_adjust(left=.07, right=.75, top=.84, bottom=.2)
    fig.savefig(R + 'ch_flex.png'); plt.close(fig)
    W, Hh = 1600, 1180; im, d = base(W, Hh); header(d, W, Hh, 'FLEX ZONES', 'UNFOLD FIRST, STRETCH SECOND · FIRST-PASS GEOMETRY, NOT FEA', '03 · KINEMATICS')
    # pleat diagram
    d.rectangle((48, 150, 700, 520), fill=CARD, outline=INK, width=2); d.text((70, 178), 'RIB PLEAT, IN SECTION', font=monob(16), fill=INK)
    x0, y0, pp, hh = 90, 380, 50, 60
    pts = []
    for i in range(12):
        pts += [(x0 + i * pp, y0), (x0 + i * pp + pp / 2, y0 - hh)]
    pts.append((x0 + 12 * pp, y0)); d.line(pts, fill=OR, width=5, joint='curve')
    d.line([(x0, y0 + 40), (x0 + 12 * pp, y0 + 40)], fill=INK, width=2); d.text((x0 + 6 * pp, y0 + 62), 'L0 = 150 mm sleeve (knee)', font=mono(14), fill=GREY, anchor='mm')
    d.line([(x0 + 5 * pp, y0 - hh), (x0 + 5 * pp, y0)], fill=INK, width=2); d.text((x0 + 5 * pp + 10, y0 - hh / 2), 'h', font=monob(16), fill=INK, anchor='lm')
    d.text((x0 + 2 * pp, y0 - hh - 26), 'p = 11.5 mm', font=mono(14), fill=GREY, anchor='mm')
    d.text((70, 480), 'Bending the knee asks the outer side for r·θ more length.', font=mono(13), fill=GREY)
    d.text((70, 500), 'The pleats give it back before the yarn has to stretch.', font=mono(13), fill=GREY)
    ch = Image.open(R + 'ch_flex.png').convert('RGB'); paste_fit(im, ch, (740, 150, 1552, 520), cover=False); d.rectangle((740, 150, 1552, 520), outline=INK, width=2)
    # table
    cols = ['JOINT', 'ROM', 'OUTER NEEDS', 'FLAT STRAIN', 'PLEAT h', 'INNER LEFT', 'PLEAT STACK', 'PINCH MARGIN']
    cw = [180, 120, 190, 190, 150, 190, 200, 284]; y = 560; x = 48
    d.rectangle((48, y, 48 + sum(cw), y + 40), fill=INK)
    for j, t in enumerate(cols): d.text((x + 12, y + 20), t, font=monob(14), fill=(255, 255, 255), anchor='lm'); x += cw[j]
    y += 40
    for f in C['flex']:
        x = 48; bad = f['pinch_margin_mm'] < 0
        if bad: d.rectangle((48, y, 48 + sum(cw), y + 46), fill=(255, 226, 210))
        vals = [f['joint'], f"{f['rom']}°", f"{f['need_mm']} mm", f"{f['flat_strain']} %", f"{f['pleat_h_mm']} mm", f"{f['inner_mm']} mm", f"{f['stack_mm']} mm",
                (f"{f['pinch_margin_mm']} mm · GUSSET" if bad else f"+{f['pinch_margin_mm']} mm")]
        for j, t in enumerate(vals):
            d.text((x + 12, y + 23), t, font=(monob(15) if j in (0, 7) else mono(15)), fill=(OR if (bad and j == 7) else INK), anchor='lm'); x += cw[j]
        d.line([(48, y + 46), (48 + sum(cw), y + 46)], fill=INK); y += 46
    notes = ['Hip and knee: 6–7 mm rib pleats hold the knee at the 30 % limit at full bend (30.3 % at 120°), against 95 % flat.',
             'Shoulder and elbow: the inside of the bend has no room for a pleat stack, so the sleeve pinches.',
             'Fix: an open stretch-mesh gusset on the inner arm, no pleats there. Next: 10,000-cycle stretch test.',
             'Assumed: joint radii from the model, design ROM, 2 mm fabric. Replace with motion-capture data.']
    for i, t in enumerate(notes): d.text((48, y + 30 + i * 26), ('→ ' if i < 3 else '* ') + t, font=mono(15), fill=(INK if i < 3 else GREY))
    im.save(OUT + 'hs__flex.webp', quality=88)

# ---------- 4. THERMAL + ACOUSTIC
def thermal():
    T = C['thermal']; chart_style()
    fig, ax = plt.subplots(figsize=(8.12, 4.30), dpi=200)
    A = C['acoustic']; f = [a['f'] for a in A]; so = [a['solid'] for a in A]; ve = [a['with_vents'] for a in A]; ba = [a['baffled'] for a in A]
    ax.axvspan(2000, 4000, color=CO, alpha=.07, lw=0, zorder=0)
    ax.text(2828, 30.6, 'ACTUATOR WHINE\n2–4 kHz', fontsize=9.6, color=CO, ha='center', va='top')
    ax.fill_between(f, ve, so, facecolor='none', hatch='////', edgecolor=(1, .353, .122, .45), lw=0, zorder=1)
    ax.annotate('VENT LEAK\n3–6 dB', (6100, 22.2), xytext=(6300, 11.5), fontsize=9.6, color=CO, ha='center',
                arrowprops=dict(arrowstyle='-', color=CO, lw=.8, shrinkA=2, shrinkB=0))
    series(ax, f, so, CI, log=True); series(ax, f, ba, CM, lw=2.5, ls=(0, (4, 3)), log=True); series(ax, f, ve, CO, lw=3.0, z=4, log=True)
    for ys, col in ((so, CI), (ba, CM), (ve, CO)):
        ax.plot(f[:-1], ys[:-1], 'o', ms=6.5, mfc=col, mec=CK, mew=1.4, zorder=5)
    end_label(ax, f[-1], so[-1], f'SOLID SKIN  {so[-1]:.0f} dB', CI, dy=7); end_label(ax, f[-1], ba[-1], f'LABYRINTH  {ba[-1]:.0f} dB', CM, dy=-5)
    end_label(ax, f[-1], ve[-1], f'OPEN VENTS  {ve[-1]:.0f} dB', CO)
    ax.set_xticks(f); ax.set_xticklabels(['500', '1k', '2k', '4k', '8k']); ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_xlim(f[0] / 1.15, f[-1]); ax.set_ylim(0, 32); ax.set_yticks(range(0, 31, 10))
    chart_frame(ax, 'SOUND REDUCTION · dB   (MASS LAW, UPPER BOUND)', 'FREQUENCY · Hz')
    fig.subplots_adjust(left=.06, right=.74, top=.87, bottom=.17)
    fig.savefig(R + 'ch_ac.png'); plt.close(fig)
    W, Hh = 1600, 1180; im, d = base(W, Hh); header(d, W, Hh, 'HEAT + SOUND', 'FIRST-PASS NUMBERS · STATED ASSUMPTIONS · CFD AND LAB TESTS NEXT', '04 · THERMAL / ACOUSTIC')
    # airflow schematic: torso section
    d.rectangle((48, 150, 760, 640), fill=CARD, outline=INK, width=2); d.text((70, 178), 'TORSO, TOP SECTION', font=monob(16), fill=INK)
    cx, cy = 404, 410
    d.rounded_rectangle((cx - 250, cy - 150, cx + 250, cy + 150), 90, outline=hexrgb('#B9A787'), width=16)
    d.rounded_rectangle((cx - 232, cy - 132, cx + 232, cy + 132), 80, outline=hexrgb('#ABA498'), width=12)
    d.rounded_rectangle((cx - 214, cy - 114, cx + 214, cy + 114), 72, outline=INK, width=5)
    d.rectangle((cx - 90, cy - 50, cx + 90, cy + 50), fill=hexrgb('#3A3B3D')); d.text((cx, cy), 'COMPUTE + DRIVES', font=monob(13), fill=(240, 236, 228), anchor='mm')
    d.ellipse((cx - 28, cy + 70, cx + 28, cy + 126), outline=OR, width=4); d.text((cx, cy + 98), 'FAN', font=monob(12), fill=OR, anchor='mm')
    for sx in (-1, 1):
        a = (cx + sx * 310, cy - 40); b = (cx + sx * 200, cy - 40); d.line([a, b], fill=hexrgb('#5E8DB0'), width=5)
        d.polygon([b, (b[0] + sx * 14, b[1] - 9), (b[0] + sx * 14, b[1] + 9)], fill=hexrgb('#5E8DB0'))
        d.text((cx + sx * 300, cy - 70), 'IN', font=monob(14), fill=hexrgb('#5E8DB0'), anchor='mm')
    d.line([(cx, cy + 128), (cx, cy + 190)], fill=OR, width=5); d.polygon([(cx, cy + 202), (cx - 9, cy + 188), (cx + 9, cy + 188)], fill=OR)
    d.text((cx + 16, cy + 175), 'OUT · BACK PANEL', font=monob(14), fill=OR, anchor='lm')
    d.text((70, 178+28), 'skin: knit 2 mm · spacer mesh 6 mm · shell 2 mm', font=mono(13), fill=GREY)
    # numbers
    nums = [('PASSIVE, BARE SHELL', f"{T['Q_bare']} W", 'shell + still air, ΔT 20 K, 0.45 m²'),
            ('PASSIVE, IN TEXTILE', f"{T['Q_soft']} W", f"−{T['passive_loss_pct']} %: the skin insulates"),
            ('FAN MUST MOVE', f"{T['Q_fan']} W", 'of an assumed 150 W internal load'),
            ('AIRFLOW', f"{T['flow_Ls']} L/s", f"{T['flow_cfm']} CFM at 10 K air rise"),
            ('OPEN AREA NEEDED', f"{T['open_need_cm2']} cm²", f"≈ {T['panel_need_cm2']} cm² of 35 % open knit"),
            ('DESIGNED VENTS', f"{T['inlet_cm2']} + {T['outlet_cm2']} cm²", f"face speed {T['v_inlet']} / {T['v_outlet']} m/s")]
    for i, (a, b, c) in enumerate(nums):
        y = 150 + i * 82; d.rectangle((800, y, 1552, y + 70), fill=CARD, outline=INK, width=2); d.rectangle((800, y, 810, y + 70), fill=OR if i in (2, 5) else INK)
        d.text((830, y + 22), a, font=monob(14), fill=GREY, anchor='lm'); d.text((830, y + 50), c, font=mono(13), fill=GREY, anchor='lm'); d.text((1530, y + 35), b, font=blk(30), fill=INK, anchor='rm')
    ch = Image.open(R + 'ch_ac.png').convert('RGB'); paste_fit(im, ch, (48, 670, 860, 1100), cover=False); d.rectangle((48, 670, 860, 1100), outline=INK, width=2)
    notes = ['The textile costs over half the passive cooling,', 'so the vents carry the heat: 10 L/s, quiet face speeds.', '',
             'Sound: the soft skin is a light layer; mass law', 'gives at most ~15–20 dB in the 2–4 kHz actuator', 'whine band. The open vents cost 3–6 dB at 4–8 kHz;',
             'a lined labyrinth through the spacer mesh wins', 'most of it back.', '', '* Mass law is an upper bound for porous textiles.', '  Next: CFD of the torso, impedance-tube tests.']
    for i, t in enumerate(notes): d.text((900, 690 + i * 26), t, font=mono(15), fill=(GREY if t.startswith('*') or t.startswith('  ') else INK))
    im.save(OUT + 'hs__thermal.webp', quality=88)

for fn in sys.argv[1:]: globals()[fn]()
print('ok')
