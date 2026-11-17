"""BASECAMP BC-01 technology manual: a Tigre Studio study in Henry Ortega's tech-manual format.
Builds manual.html (12 landscape pages, 1600x1000). Renders come from the real BASECAMP Blender model (basecamp2/bcm.py)."""
import json, math, os
M = '/home/claude/basecamp2/m/'
FONTS = '/home/claude/tigrestudiodesign.github.io/fonts/'
def J(n):
    try: return json.load(open(M + n + '.json'))
    except Exception: return {}

DOC = 'TM-BC01-001'; REV = 'REV A'; DATE = 'NOV 2026'
CH = ['TECHNOLOGY DEFINITION', 'USER BENEFITS', 'DESIGN REQUIREMENTS', 'DIGITAL PROCESS', 'SYSTEM & ARCHITECTURE', 'METHOD OF MAKING', 'QC & TROUBLESHOOTING', 'BOM & DOCUMENT CONTROL']
TOTAL = 12

css = f"""
@font-face{{font-family:ID;font-weight:900;src:url(file://{FONTS}InterDisplay-Black.woff2)}}
@font-face{{font-family:ID;font-weight:700;src:url(file://{FONTS}InterDisplay-Bold.woff2)}}
@font-face{{font-family:JM;font-weight:400;src:url(file://{FONTS}JetBrainsMono-400.woff2)}}
@font-face{{font-family:JM;font-weight:700;src:url(file://{FONTS}JetBrainsMono-700.woff2)}}
@page{{size:1600px 1000px;margin:0}}
*{{box-sizing:border-box}}html,body{{margin:0;background:#777}}
:root{{--ink:#0B0B0C;--paper:#F2EEE6;--or:#FF5A1F;--g:#8A857C;--l:#D9D3C7}}
.pg{{width:1600px;height:1000px;position:relative;overflow:hidden;background:var(--paper);color:var(--ink);font:15px/1.45 ID,sans-serif;page-break-after:always;
 background-image:linear-gradient(rgba(11,11,12,.055) 1px,transparent 1px),linear-gradient(90deg,rgba(11,11,12,.055) 1px,transparent 1px);background-size:20px 20px;background-position:-1px -1px}}
.pg.dk{{background-color:var(--ink);color:var(--paper);background-image:linear-gradient(rgba(242,238,230,.06) 1px,transparent 1px),linear-gradient(90deg,rgba(242,238,230,.06) 1px,transparent 1px)}}
.hd{{position:absolute;left:60px;right:120px;top:28px;display:flex;justify-content:space-between;font:700 11px JM;letter-spacing:.12em;border-bottom:1.5px solid currentColor;padding-bottom:10px}}
.hd b{{color:var(--or)}}
.ft{{position:absolute;left:60px;right:120px;bottom:24px;display:flex;justify-content:space-between;font:400 10px JM;letter-spacing:.1em;opacity:.75;border-top:1px solid currentColor;padding-top:8px}}
.rail{{position:absolute;right:0;top:0;bottom:0;width:72px;background:var(--ink);display:flex;flex-direction:column;justify-content:center;gap:4px;padding:0 0 0 0}}
.rail span{{display:block;height:84px;color:#F2EEE6;font:700 11px JM;writing-mode:vertical-rl;transform:rotate(180deg);text-align:center;opacity:.35;letter-spacing:.12em;border-left:3px solid transparent}}
.rail span.on{{opacity:1;color:var(--or);border-left-color:var(--or)}}
.dk .rail{{background:#1b1b1d}}
h1,h2{{font-family:ID;font-weight:900;margin:0;letter-spacing:-.01em;line-height:.92}}
.ttl{{position:absolute;left:60px;top:66px}} .ttl small{{display:block;font:700 12px JM;letter-spacing:.14em;color:var(--or);margin-bottom:10px}}
.ttl h2{{font-size:46px}} .ttl p{{max-width:620px;margin:12px 0 0;font-size:15px;opacity:.85}}
.mono{{font:400 11.5px/1.5 JM;letter-spacing:.02em}}
table{{border-collapse:collapse;width:100%}} td,th{{text-align:left;padding:7px 10px 7px 0;border-bottom:1px solid rgba(11,11,12,.25);font:400 12px/1.35 JM;vertical-align:top}}
th{{font:700 10.5px JM;letter-spacing:.1em;border-bottom:1.5px solid var(--ink)}}
.dk td{{border-color:rgba(242,238,230,.25)}} .dk th{{border-color:var(--paper)}}
.ctq{{display:inline-block;width:14px;height:14px;background:var(--or);transform:rotate(45deg) scale(.8);vertical-align:-2px;margin-right:6px}}
.tag{{display:inline-block;font:700 10px JM;letter-spacing:.08em;padding:3px 7px;border:1.5px solid currentColor;border-radius:3px}}
.box{{position:absolute}}
.box img{{display:block;width:100%;height:100%;object-fit:contain}}
svg text{{font-family:JM}}
.num{{display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:50%;background:var(--ink);color:var(--paper);font:700 11px JM;flex:none}}
.or{{color:var(--or)}}
table.tight td{{padding:5px 10px 5px 0}}
.note{{border-left:4px solid var(--or);padding:8px 12px;background:rgba(255,90,31,.08);font:400 12px/1.45 JM}}
"""

def page(n, ch, title, kicker, body, intro='', dark=False):
    rail = ''.join(f'<span class="{"on" if i + 1 == ch else ""}">{i + 1:02d}</span>' for i in range(8))
    chname = f'{ch:02d} · {CH[ch - 1]}' if ch else 'FRONT MATTER'
    return f'''<section class="pg{' dk' if dark else ''}"><div class="hd"><span>TIGRE STUDIO · <b>BASECAMP BC-01</b> · TECHNOLOGY MANUAL</span><span>{chname}</span><span>{DOC} · {REV} · {DATE}</span></div>
<div class="rail">{rail}</div>
{f'<div class="ttl"><small>{kicker}</small><h2>{title}</h2>{f"<p>{intro}</p>" if intro else ""}</div>' if title else ''}
{body}
<div class="ft"><span>STUDY · ORIGINAL TIGRE STUDIO CONCEPT · WRITTEN IN THE FORMAT OF THE FACTORY TECH MANUALS I AUTHORED</span><span>PAGE {n:02d} / {TOTAL:02d}</span></div></section>'''

def img(src, x, y, w, h, extra=''):
    return f'<div class="box" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px">{extra}<img src="{src}"></div>'

def callouts(src, x, y, w, h, iw, ih, pts, side_x=None):
    """pts: list of (label_num, anchor_normalized(u,v), label_xy_page, text). Image is object-fit contain inside box."""
    s = min(w / iw, h / ih); ox = x + (w - iw * s) / 2; oy = y + (h - ih * s) / 2
    svg = ['<svg class="box" style="left:0;top:0;width:1600px;height:1000px;pointer-events:none" viewBox="0 0 1600 1000">']
    for num, (u, v), (lx, ly), t in pts:
        ax, ay = ox + u * iw * s, oy + v * ih * s
        svg.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{lx}" y2="{ly}" stroke="#0B0B0C" stroke-width="1.2"/><circle cx="{ax:.1f}" cy="{ay:.1f}" r="4" fill="#FF5A1F" stroke="#0B0B0C" stroke-width="1.2"/>'
                   f'<circle cx="{lx}" cy="{ly}" r="13" fill="#0B0B0C"/><text x="{lx}" y="{ly + 4}" text-anchor="middle" font-size="11" font-weight="700" fill="#F2EEE6">{num}</text>')
        if t:
            anchor = 'end' if lx < ax else 'start'; tx = lx - 20 if anchor == 'end' else lx + 20
            svg.append(f'<text x="{tx}" y="{ly + 4}" text-anchor="{anchor}" font-size="11.5" fill="#0B0B0C">{t}</text>')
    svg.append('</svg>')
    return img(src, x, y, w, h) + ''.join(svg)

pages = []

# ---------- 01 COVER
pages.append(f'''<section class="pg dk"><div class="hd"><span>TIGRE STUDIO · <b>TECHNOLOGY MANUAL</b></span><span>CONTROLLED DOCUMENT</span><span>{DOC} · {REV} · {DATE}</span></div>
{img('img/F_hero.png', 640, 70, 960, 768)}
<div style="position:absolute;left:60px;top:150px;width:640px">
<p class="mono or" style="font-weight:700;letter-spacing:.14em;margin:0 0 18px">TECHNOLOGY MANUAL · MODEL BC-01</p>
<h1 style="font-size:150px">BASE<br>CAMP</h1>
<p style="font-size:22px;margin:22px 0 0;max-width:520px;line-height:1.3">Emergency radio + lantern. Construction, design requirements, method of making and quality standards for build partners.</p>
<div style="display:flex;gap:10px;margin-top:28px"><span class="tag">8 CHAPTERS</span><span class="tag">12 PARTS</span><span class="tag">12 × T10 TORX</span><span class="tag">IPX4</span></div></div>
<div style="position:absolute;left:60px;right:60px;bottom:60px;display:grid;grid-template-columns:repeat(4,1fr);gap:20px" class="mono">
<div><b>DOCUMENT</b><br>{DOC}</div><div><b>REVISION</b><br>{REV} · RELEASED FOR BUILD</div><div><b>AUTHOR</b><br>HENRY ORTEGA · TIGRE STUDIO</div><div><b>AUDIENCE</b><br>FACTORY ENGINEERING · QC · OPERATORS</div></div>
<div class="ft"><span>STUDY · ORIGINAL TIGRE STUDIO CONCEPT · WRITTEN IN THE FORMAT OF THE FACTORY TECH MANUALS I AUTHORED</span><span>PAGE 01 / {TOTAL:02d}</span></div></section>''')

# ---------- 02 CONTENTS + HOW TO READ
toc = ''.join(f'<tr><td class="or" style="font-weight:700;width:46px">{i + 1:02d}</td><td style="font:700 14px ID">{c}</td><td>{p}</td></tr>' for i, (c, p) in enumerate(zip(CH, ['03', '04', '05–06', '07', '08–09', '10', '11–12', '12'])))
legend = [('<span class="ctq"></span>', 'CRITICAL TO QUALITY', 'Must be measured on every lot. Out of spec = hold the lot.'),
          ('<span style="display:inline-block;width:0;height:0;border-left:8px solid transparent;border-right:8px solid transparent;border-bottom:14px solid #0B0B0C"></span>', 'CAUTION', 'Risk of damage to the part or the operator.'),
          ('<span class="tag" style="padding:1px 5px">T10</span>', 'TOOL', 'Driver bit or fixture required at this step.'),
          ('<span class="num">3</span>', 'CALLOUT', 'Part number in the bill of materials (page 12).'),
          ('<span style="display:inline-block;width:26px;height:12px;background:#FF5A1F"></span>', 'FOCUS PART', 'The part this step or rule is about, shown in signal orange.')]
leg = ''.join(f'<tr><td style="width:60px">{a}</td><td style="font-weight:700;width:180px">{b}</td><td>{c}</td></tr>' for a, b, c in legend)
pages.append(page(2, 0, 'HOW TO USE THIS MANUAL', 'FRONT MATTER', f'''
<div class="box" style="left:60px;top:250px;width:680px"><table><tr><th>CH</th><th>CHAPTER</th><th>PAGE</th></tr>{toc}</table></div>
<div class="box" style="left:800px;top:250px;width:680px"><table><tr><th colspan="3">SYMBOLS</th></tr>{leg}</table>
<div class="note" style="margin-top:28px">Every drawing in this manual is generated from the production CAD model. If a drawing and the model disagree, the model wins and this manual is revised.</div>
<p class="mono" style="margin-top:22px;opacity:.8">One chapter per question a factory asks: what is it, why does it matter, what are the limits, how is it made, how do we know it is right.</p></div>''',
    'The same eight-chapter structure I used across a 50+ manual library, applied to an original product.'))

# ---------- 03 TECHNOLOGY DEFINITION
a = J('iso_closed.png')
def A(k, d=(0.5, 0.5)): return a.get(k, d)
feat = [(1, A('lantern'), (1100, 210), 'POP-UP LANTERN · LIFTS 40 MM'), (2, A('sos'), (1100, 260), 'SOS · ALONE ON TOP, IN RED'),
        (3, A('plate'), (300, 470), 'SPEAKER BEHIND PERFORATED PLATE'), (4, A('dial'), (300, 690), 'TUNE / DIM DIAL'),
        (5, A('btns'), (300, 760), 'LIGHT · RADIO · BAND'), (6, A('crank'), (1100, 720), 'FOLD-OUT CRANK')]
spec = [('MODEL', 'BC-01'), ('ENVELOPE', '160 × 64 × 124 MM (W × D × H)'), ('POWER', '2 × 18650 CELLS, USER-REPLACEABLE'), ('CHARGING', 'HAND CRANK · USB-C 5 V / 2 A'),
        ('BANDS', 'AM 530–1700 KHZ · FM 87.9–107.9 MHZ · WX 7 CH'), ('LIGHT', 'POP-UP DIFFUSER, DIMMABLE'), ('FASTENERS', '8 FRONT + 4 BACK · TORX T10'), ('INGRESS', 'IPX4 · RAIN AND SPLASH')]
pages.append(page(3, 1, 'WHAT IT IS', '01 · TECHNOLOGY DEFINITION', callouts('m/iso_closed.png', 330, 170, 760, 640, 1400, 1120, feat) + f'''
<div class="box" style="left:1140px;top:330px;width:340px"><table><tr><th colspan="2">KEY SPECIFICATION</th></tr>{''.join(f'<tr><td style="font-weight:700;width:96px">{k}</td><td>{v}</td></tr>' for k, v in spec)}</table></div>''',
    'A hand-crank emergency radio and lantern. Upright on a shelf, speaker facing you, every fastener reachable so it is repaired, not replaced.'))

# ---------- 04 USER BENEFITS
ben = [('img/F_top.png', 'FIND IT IN THE DARK', 'SOS sits alone on the top surface, in red, so it is found by touch. The lantern pops 40 mm out of the top and lights the room, not just the radio.', 'SOS · LANTERN'),
       ('img/F_dial.png', 'ONE DIAL, TWO JOBS', 'A knurled aluminium dial tunes the radio or dims the light, depending on the mode. Knurl depth and tooth count are set for a gloved hand.', '200-TOOTH KNURL · Ø31 MM'),
       ('img/F_speaker.png', 'HEARD OVER WEATHER', 'The speaker plate hole pattern is graded: bigger holes at the centre where the cone moves most, smaller at the edge to keep strength and splash protection.', '150 HOLES · FERMAT SPIRAL')]
cards = ''.join(f'''<div class="box" style="left:{60 + i * 480}px;top:250px;width:450px"><div style="height:380px;background:#E6E0D4;border-radius:6px;overflow:hidden"><img src="{s}" style="width:100%;height:100%;object-fit:cover"></div>
<p class="mono or" style="font-weight:700;margin:16px 0 6px">BENEFIT {i + 1:02d} · {k}</p><h2 style="font-size:26px">{t}</h2><p style="margin:10px 0 0;font-size:14.5px">{d}</p></div>''' for i, (s, t, d, k) in enumerate(ben))
pages.append(page(4, 2, 'WHY IT MATTERS', '02 · USER BENEFITS', cards, 'Every requirement later in this manual traces back to one of these three benefits. If a change hurts one of them, it needs design sign-off.'))

# ---------- 05 DESIGN REQUIREMENTS · ORTHOGRAPHIC
def dimsvg(views):
    out = ['<svg class="box" style="left:0;top:0;width:1600px;height:1000px" viewBox="0 0 1600 1000">',
           '<defs><marker id="ar" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,1 L10,5 L0,9 z" fill="#0B0B0C"/></marker></defs>']
    for (x1, y1, x2, y2, t, tx, ty, rot) in views:
        out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#0B0B0C" stroke-width="1.1" marker-start="url(#ar)" marker-end="url(#ar)"/>')
        out.append(f'<rect x="{tx - len(t) * 3.6 - 6}" y="{ty - 11}" width="{len(t) * 7.2 + 12}" height="17" fill="#F2EEE6"' + (f' transform="rotate({rot} {tx} {ty})"' if rot else '') + '/>')
        out.append(f'<text x="{tx}" y="{ty + 2}" text-anchor="middle" font-size="12" font-weight="700"' + (f' transform="rotate({rot} {tx} {ty})"' if rot else '') + f'>{t}</text>')
    out.append('</svg>')
    return ''.join(out)
# ortho images are 1300 px for 220 mm  ->  k = px per mm in the page box
def ortho(src, X, Y, S):  # S = box size in page px
    return img(src, X, Y, S, S)
S = 430; k = S / 220.0
FX, FY = 70, 215; SX, SY = 560, 215; TX, TY = 1050, 215
# front: x in [-80,80] around centre, z: shell 4..128 with centre 76
fc = (FX + S / 2, FY + S / 2)
def fpt(x, z): return (fc[0] + x * k, fc[1] - (z - 76) * k)
L, R = fpt(-80, 0)[0], fpt(80, 0)[0]; B, T = fpt(0, 4)[1], fpt(0, 128)[1]
sc_ = (SX + S / 2, SY + S / 2)
def spt(y, z): return (sc_[0] + y * k, sc_[1] - (z - 76) * k)
SL, SR = spt(-32, 0)[0], spt(32, 0)[0]
tc = (TX + S / 2, TY + S / 2)
dims = dimsvg([
    (L, B + 26, R, B + 26, '160', (L + R) / 2, B + 30, 0),
    (L - 22, T, L - 22, B, '124', L - 26, (T + B) / 2, -90),
    (SL, B + 26, SR, B + 26, '64', (SL + SR) / 2, B + 30, 0),
    (SR + 22, fpt(0, 128)[1], SR + 22, fpt(0, 128 + 42.5)[1], '40 LIFT', SR + 26, (fpt(0, 128)[1] + fpt(0, 170.5)[1]) / 2, -90),
    (tc[0] - 80 * k, tc[1] + 32 * k + 26, tc[0] + 80 * k, tc[1] + 32 * k + 26, '160', tc[0], tc[1] + 32 * k + 30, 0),
    (tc[0] + 80 * k + 22, tc[1] - 32 * k, tc[0] + 80 * k + 22, tc[1] + 32 * k, '64', tc[0] + 80 * k + 26, tc[1], -90),
])
lab = lambda x, y, t: f'<div class="box mono" style="left:{x}px;top:{y}px;font-weight:700;letter-spacing:.12em">{t}</div>'
rules = [('ENVELOPE', '160 × 64 × 124 mm', '±0.5', True), ('SHELL CORNER RADIUS', 'R18', '±0.3', False), ('FACEPLATE', '150 × 110 × 2.5 mm, R9', '±0.2', True),
         ('BACK SCREW PITCH', '116 × 82 mm', '±0.15', True), ('FRONT SCREW PITCH', '138 × 98 mm', '±0.15', True), ('LANTERN LIFT', '40 mm, full travel', '+1 / −0', False)]
rt = ''.join(f'<tr><td style="font-weight:700">{"<span class=ctq></span>" if c else ""}{a}</td><td>{b}</td><td>{t}</td></tr>' for a, b, t, c in rules)
pages.append(page(5, 3, 'ENVELOPE & INTERFACES', '03 · DESIGN REQUIREMENTS', ortho('m/o_front.png', FX, FY, S) + ortho('m/o_side.png', SX, SY, S) + ortho('m/o_top.png', TX, TY, S) + dims +
    lab(FX, 196, 'FRONT') + lab(SX, 196, 'RIGHT SIDE · LANTERN UP') + lab(TX, 196, 'TOP') +
    f'<div class="box" style="left:70px;top:690px;width:1410px"><table class="tight"><tr><th>FEATURE</th><th>NOMINAL</th><th>TOLERANCE</th></tr>{rt}</table></div>',
    'Third-angle views generated from the model. All dimensions in millimetres.'))

# ---------- 06 DESIGN REQUIREMENTS · SPEAKER PLATE RULE (drawn from the model's formula)
NH = 150; RF = 17.2; gold = math.pi * (3 - math.sqrt(5)); sc2 = 7.6
cx, cy = 370, 560
holes = []
for i in range(NH):
    r = RF * math.sqrt((i + 0.5) / NH); t = r / RF; a = i * gold; hr = (1.0 - 0.45 * t)
    holes.append(f'<circle cx="{cx + r * math.cos(a) * sc2:.1f}" cy="{cy - r * math.sin(a) * sc2:.1f}" r="{hr * sc2:.1f}" fill="#0B0B0C"/>')
plate = (f'<svg class="box" style="left:0;top:0;width:1600px;height:1000px" viewBox="0 0 1600 1000">'
         f'<rect x="{cx - 33 * sc2}" y="{cy - 33 * sc2}" width="{66 * sc2}" height="{66 * sc2}" rx="{8 * sc2}" fill="#FF5A1F" stroke="#0B0B0C" stroke-width="1.5"/>' + ''.join(holes) +
         f'<circle cx="{cx}" cy="{cy}" r="{RF * sc2 + 14}" fill="none" stroke="#0B0B0C" stroke-dasharray="4 4"/>' +
         ''.join(f'<circle cx="{cx + dx * sc2}" cy="{cy + dz * sc2}" r="{2.2 * sc2}" fill="#F2EEE6" stroke="#0B0B0C" stroke-width="1.2"/><text x="{cx + dx * sc2}" y="{cy + dz * sc2 + 4}" font-size="11" text-anchor="middle" font-weight="700">T10</text>' for dx in (-27, 27) for dz in (-27, 27)) +
         f'<line x1="{cx - 33 * sc2}" y1="{cy + 33 * sc2 + 30}" x2="{cx + 33 * sc2}" y2="{cy + 33 * sc2 + 30}" stroke="#0B0B0C" marker-start="url(#ar2)" marker-end="url(#ar2)"/><text x="{cx}" y="{cy + 33 * sc2 + 26}" text-anchor="middle" font-size="12" font-weight="700">66</text>'
         '<defs><marker id="ar2" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,1 L10,5 L0,9 z" fill="#0B0B0C"/></marker></defs>'
         f'<line x1="{cx + RF * sc2 + 14}" y1="{cy}" x2="{cx + RF * sc2 + 60}" y2="{cy - 120}" stroke="#0B0B0C" stroke-width="1"/><rect x="{cx + RF * sc2 + 56}" y="{cy - 138}" width="92" height="18" fill="#F2EEE6"/><text x="{cx + RF * sc2 + 60}" y="{cy - 124}" font-size="11" font-weight="700">R17.2 FIELD</text>'
         '</svg>')
# graph of hole diameter vs radius
gx, gy, gw, gh = 860, 270, 600, 230
pts = ' '.join(f'{gx + (i / 50) * gw:.1f},{gy + gh - ((2 * (1 - 0.45 * i / 50)) - 1.0) / 1.0 * gh:.1f}' for i in range(51))
graph = (f'<svg class="box" style="left:0;top:0;width:1600px;height:1000px" viewBox="0 0 1600 1000">'
         f'<rect x="{gx}" y="{gy}" width="{gw}" height="{gh}" fill="none" stroke="#0B0B0C"/>' +
         ''.join(f'<line x1="{gx}" y1="{gy + gh * j / 4}" x2="{gx + gw}" y2="{gy + gh * j / 4}" stroke="#0B0B0C" stroke-opacity=".15"/>' for j in range(1, 4)) +
         f'<polyline points="{pts}" fill="none" stroke="#FF5A1F" stroke-width="3"/>'
         f'<text x="{gx}" y="{gy - 10}" font-size="11" font-weight="700">HOLE Ø (MM) VS DISTANCE FROM CENTRE</text>'
         f'<text x="{gx - 8}" y="{gy + 4}" font-size="11" text-anchor="end">2.0</text><text x="{gx - 8}" y="{gy + gh + 4}" font-size="11" text-anchor="end">1.0</text>'
         f'<text x="{gx}" y="{gy + gh + 18}" font-size="11">0</text><text x="{gx + gw}" y="{gy + gh + 18}" font-size="11" text-anchor="end">17.2 MM</text>'
         f'<circle cx="{gx}" cy="{gy}" r="5" fill="#FF5A1F"/><text x="{gx + 14}" y="{gy + 34}" font-size="11" font-weight="700">Ø2.0 AT CENTRE</text>'
         f'<circle cx="{gx + gw}" cy="{gy + gh - 0.1 * gh}" r="5" fill="#FF5A1F"/><text x="{gx + gw - 10}" y="{gy + gh - 0.1 * gh + 22}" font-size="11" text-anchor="end" font-weight="700">Ø1.1 AT EDGE</text></svg>')
rules2 = [('HOLE COUNT', '150, Fermat spiral (golden angle 137.5°)', True), ('HOLE Ø', '2.0 mm at centre → 1.1 mm at edge, linear in radius', True),
          ('MIN WEB BETWEEN HOLES', '≥ 0.25 mm (model minimum 0.27 mm), checked on every revision', True), ('FIELD', 'R17.2 mm, centred on the driver axis', False),
          ('PLATE', '66 × 66 × 2.2 mm, R8, signal orange', False), ('FIXING', '4 × T10 at 54 × 54 mm pitch', False)]
pages.append(page(6, 3, 'THE SPEAKER PLATE RULE', '03 · DESIGN REQUIREMENTS', plate + graph +
    f'<div class="box" style="left:860px;top:560px;width:600px"><table><tr><th>RULE</th><th>REQUIREMENT</th></tr>{"".join(f"<tr><td style=font-weight:700;width:190px>{chr(32).join([]) }{"<span class=ctq></span>" if c else ""}{a}</td><td>{b}</td></tr>" for a, b, c in rules2)}</table>'
    '<div class="note" style="margin-top:16px">Written as a rule, not a drawing: change the plate size or hole count and the pattern regenerates with the same limits.</div></div>',
    'A design requirement written so a designer can design to it and a factory can check it. Drawn here from the same formula the model uses.'))

# ---------- 07 DIGITAL PROCESS
flow = [('DEFINE', 'Rules sheet: envelope, hole rule, fastener map, CMF.'), ('MODEL', 'Python script builds every part in Blender from the rules.'), ('CHECK', 'Script prints counts and limits: 150 holes, 12 screws, webs.'),
        ('RENDER', 'Cycles renders and clay line drawings from one scene.'), ('PROTOTYPE', 'Electronics behaviour in Tinkercad, firmware in C++.'), ('DOCUMENT', 'This manual: every drawing regenerated on each revision.')]
fl = ''.join(f'''<div class="box" style="left:{60 + i * 238}px;top:300px;width:214px;height:200px;border:1.5px solid #0B0B0C;border-radius:6px;padding:16px;background:{'#FF5A1F' if i == 2 else '#F2EEE6'}">
<p class="mono" style="font-weight:700;margin:0">STEP {i + 1:02d}</p><h2 style="font-size:24px;margin:8px 0">{t}</h2><p style="margin:0;font-size:13.5px">{d}</p></div>''' + (f'<div class="box" style="left:{60 + i * 238 + 214}px;top:388px;width:24px;height:24px;font:700 18px JM;text-align:center">→</div>' if i < 5 else '') for i, (t, d) in enumerate(flow))
pages.append(page(7, 4, 'ONE MODEL, EVERY OUTPUT', '04 · DIGITAL PROCESS', fl + f'''
<div class="box" style="left:60px;top:560px;width:640px"><p class="mono or" style="font-weight:700">WHY IT MATTERS ON THE FACTORY FLOOR</p>
<p style="font-size:16px;margin:6px 0 0">When a dimension changes, the model, the renders and every drawing in this manual change with it. The factory never works from a drawing that is out of date.</p></div>
<div class="box" style="left:760px;top:560px;width:720px"><table><tr><th>OUTPUT</th><th>SOURCE</th><th>REGENERATED</th></tr>
<tr><td>Hero and detail renders</td><td>bc.py · Cycles</td><td>Every revision</td></tr><tr><td>Clay line drawings (this manual)</td><td>bcm.py · Freestyle</td><td>Every revision</td></tr>
<tr><td>Callout positions</td><td>Projected from part centres</td><td>Every render</td></tr><tr><td>Speaker hole pattern</td><td>Hole rule, page 06</td><td>On rule change</td></tr>
<tr><td>Behaviour prototype</td><td>Tinkercad · Arduino C++</td><td>On firmware change</td></tr></table></div>''',
    'The digital pipeline from rules to geometry to documentation. Nothing in this manual is drawn by hand.'))

# ---------- 08 SYSTEM · EXPLODED + BOM
e = J('exp_all.png')
parts = [('btns', 'Controls: light, radio, band slider'), ('dial', 'Tune / dim dial'), ('pscrew', 'Plate screws · 4 × T10'), ('plate', 'Perforated speaker plate'), ('fscrew', 'Front screws · 4 × T10'),
         ('face', 'Printed faceplate'), ('board', 'Main board'), ('shell', 'Shell'), ('cells', '2 × 18650 cells'), ('back', 'Back plate + label · 4 × T10'), ('crank', 'Fold-out crank'), ('lantern', 'Pop-up lantern'), ('sos', 'SOS button')]
lpos = {'btns': (170, 840), 'dial': (170, 790), 'pscrew': (170, 520), 'plate': (170, 600), 'fscrew': (170, 460), 'face': (170, 700), 'board': (620, 250), 'shell': (760, 210),
        'cells': (1080, 820), 'back': (1150, 330), 'crank': (1150, 760), 'lantern': (1000, 160), 'sos': (720, 150)}
L_ = sorted([(e[g][1], i, g) for i, (g, t) in enumerate(parts) if g in e and e[g][0] < 0.42])
R_ = sorted([(e[g][1], i, g) for i, (g, t) in enumerate(parts) if g in e and e[g][0] >= 0.42])
def spread(lst, x, y0, y1):
    n = len(lst); return [(i + 1, e[g], (x, int(y0 + (y1 - y0) * (k + 0.5) / max(n, 1))), '') for k, (v, i, g) in enumerate(lst)]
pts = spread(L_, 110, 200, 880) + spread(R_, 1190, 160, 880)
bom = ''.join(f'<tr><td class="or" style="font-weight:700;width:30px">{i + 1:02d}</td><td>{t}</td></tr>' for i, (g, t) in enumerate(parts))
pages.append(page(8, 5, 'PRODUCT ARCHITECTURE', '05 · SYSTEM & ARCHITECTURE', callouts('m/exp_all.png', 150, 150, 1060, 763, 1800, 1296, pts) +
    f'<div class="box" style="left:1230px;top:180px;width:250px"><table><tr><th colspan="2">PARTS</th></tr>{bom}</table><p class="mono" style="margin-top:14px">Front to back: every layer is a separate, replaceable part held by screws you can reach.</p></div>',
    ''))

# ---------- 09 SYSTEM · SECTION + ELECTRONICS
s_ = J('o_sectiso.png')
stack = [('FACEPLATE + CONTROLS', 'Graphite, printed cream legends'), ('SPEAKER DRIVER', 'Ø48 cone behind the plate'), ('MAIN BOARD', '140 × 100 mm, 1.6 mm'), ('CELLS', '2 × 18650, rear compartment'), ('BACK PLATE', '2 mm, 4 × T10, spec label')]
pages.append(page(9, 5, 'SECTION & ELECTRONICS', '05 · SYSTEM & ARCHITECTURE', callouts('m/o_sectiso.png', 70, 160, 700, 560, 1400, 1120, [(i+1, s_.get(g,(0.5,0.5)), (60 if i%2==0 else 760, 260+i*95), '') for i,g in enumerate(['face','speaker','board','cells','back'])]) + '<div class="box mono" style="left:70px;top:150px;font-weight:700;letter-spacing:.12em">SECTION · SHELL CUT AT THE RIGHT-HAND SIDE</div>' +
    f'<div class="box" style="left:60px;top:765px;width:700px"><table class="tight"><tr><th>#</th><th>LAYER (FRONT → BACK)</th><th>NOTE</th></tr>{"".join(f"<tr><td class=or style=font-weight:700>{i+1}</td><td style=font-weight:700>{a}</td><td>{b}</td></tr>" for i,(a, b) in enumerate(stack))}</table></div>' +
    img('img/bc2__el-block.webp', 800, 170, 680, 450) +
    '<div class="box" style="left:800px;top:640px;width:680px"><p class="mono or" style="font-weight:700;margin:0">POWER & SIGNAL</p><p style="font-size:14.5px;margin:6px 0 0">Orange is power, black is signal. The crank and USB-C feed one charger; a quiet regulator keeps switching noise out of the radio. The behaviour of every control was proven in a Tinkercad prototype before any board layout.</p></div>',
    ''))

# ---------- 10 METHOD OF MAKING · ASSEMBLY SEQUENCE
steps = [('INSTALL CELLS', 'Seat both 18650 cells in the rear compartment, + to the label mark.', 'POLARITY CHECK', 'step1'),
         ('FIT MAIN BOARD', 'Lower the board onto the front bosses; connect cell and crank leads.', 'ESD STRAP', 'step2'),
         ('MOUNT SPEAKER', 'Place the driver on the board side of the faceplate opening, cone forward.', 'NO FINGERS ON CONE', 'step3'),
         ('FIT FACEPLATE', 'Fit the printed faceplate; check legend registration before fixing.', 'CTQ · REGISTRATION', 'step4'),
         ('FIX PLATE + FRONT', 'Speaker plate with 4 × T10, then faceplate corners with 4 × T10.', 'T10 · CROSS PATTERN', 'step5'),
         ('CLOSE THE BACK', 'Back plate with 4 × T10, label upright, USB-C port aligned.', 'T10 · SEAL CHECK', 'step6')]
st = ''.join(f'''<div class="box" style="left:{60 + (i % 3) * 474}px;top:{215 + (i // 3) * 360}px;width:450px">
<div style="height:225px;border:1.5px solid #0B0B0C;border-radius:6px;background:#F7F4EE;overflow:hidden;position:relative"><img src="m/{s}.png" style="width:100%;height:100%;object-fit:cover;object-position:35% 55%;transform:scale(1.25)"><span class="num" style="position:absolute;left:12px;top:12px;width:30px;height:30px;font-size:13px">{i + 1}</span></div>
<p style="margin:10px 0 0;font:900 18px ID">{t}</p><p style="margin:4px 0 6px;font-size:13.5px">{d}</p><span class="tag">{k}</span></div>''' for i, (t, d, k, s) in enumerate(steps))
pages.append(page(10, 6, 'ASSEMBLY SEQUENCE', '06 · METHOD OF MAKING', st, ''))

# ---------- 11 QC · ACCEPT / MARGINAL / REJECT
def tile(kind, g):
    c = {'A': '#2E7D4F', 'M': '#E0A21B', 'R': '#C8321E'}[kind]; lab = {'A': 'ACCEPT', 'M': 'MARGINAL · ENGINEERING REVIEW', 'R': 'REJECT'}[kind]
    return f'<div style="border:1.5px solid #0B0B0C;border-radius:6px;overflow:hidden;background:#fff"><svg viewBox="0 0 240 150" style="display:block;width:100%">{g}</svg><div style="background:{c};color:#fff;font:700 10.5px JM;letter-spacing:.08em;padding:6px 8px">{lab}</div></div>'
def legend(off):  # faceplate legend registration: printed box vs window
    return f'<rect width="240" height="150" fill="#222326"/><rect x="60" y="40" width="120" height="70" rx="6" fill="none" stroke="#555" stroke-width="2" stroke-dasharray="4 3"/><g transform="translate({off},0)"><rect x="60" y="40" width="120" height="70" rx="6" fill="none" stroke="#F1ECE1" stroke-width="3"/><text x="120" y="82" text-anchor="middle" fill="#F1ECE1" font-size="16" font-weight="700">RADIO</text></g>'
def gap(g):
    return f'<rect width="240" height="150" fill="#DDD4C2"/><rect x="0" y="0" width="240" height="70" fill="#222326"/><rect x="0" y="{70 + g}" width="240" height="{80 - g}" fill="#DDD4C2"/><rect x="0" y="70" width="240" height="{g}" fill="#0B0B0C"/><text x="12" y="135" font-size="12" fill="#0B0B0C" font-weight="700">GAP {g / 20:.2f} MM</text>'
def holes_t(n):
    h = ''.join(f'<circle cx="{40 + (i % 8) * 23}" cy="{35 + (i // 8) * 26}" r="7" fill="#0B0B0C"/>' for i in range(32))
    blk = ''.join(f'<circle cx="{40 + (j % 8) * 23}" cy="{35 + (j // 8) * 26}" r="7" fill="#FF5A1F"/>' for j in [9, 18][:n]) if n < 3 else '<circle cx="109" cy="61" r="7" fill="#FF5A1F"/><circle cx="132" cy="87" r="7" fill="#FF5A1F"/><circle cx="86" cy="87" r="7" fill="#FF5A1F"/><circle cx="109" cy="113" r="7" fill="#FF5A1F"/>'
    return f'<rect width="240" height="150" fill="#FF5A1F"/>{h}' + (blk.replace('#FF5A1F', '#FF5A1F" stroke="#0B0B0C" stroke-width="1.5') if n else '')
rows = [('LEGEND REGISTRATION', '≤ 0.3 mm offset from window', [legend(0), legend(5), legend(14)]),
        ('FACEPLATE TO SHELL GAP', '≤ 0.20 mm all round; ≤ 0.40 review', [gap(3), gap(7), gap(14)]),
        ('SPEAKER HOLES', 'All 150 open; flash in 1–2 = review', [holes_t(0), holes_t(2), holes_t(4)])]
qc = ''.join(f'''<div class="box" style="left:60px;top:{175 + r * 255}px;width:1080px;display:grid;grid-template-columns:240px repeat(3,1fr);gap:18px;align-items:center">
<div><p style="font:900 18px ID;margin:0"><span class="ctq"></span>{t}</p><p class="mono" style="margin:6px 0 0">SPEC: {s}</p></div>{''.join(tile(k, g) for k, g in zip('AMR', gs))}</div>''' for r, (t, s, gs) in enumerate(rows))
ctq = [('ENVELOPE', 'Calipers', '1 / lot · 5 pcs'), ('LEGEND REGISTRATION', 'Overlay film', 'Every unit'), ('FACEPLATE GAP', 'Feeler gauge 0.20', 'Every unit'), ('SCREW SEATING', 'Visual + T10 torque check', 'Every unit'),
       ('SPEAKER HOLES', 'Back-light check', 'Every plate'), ('IPX4', 'Splash test', '1 / lot')]
pages.append(page(11, 7, 'ACCEPT · REVIEW · REJECT', '07 · QC & TROUBLESHOOTING', qc + f'<div class="box" style="left:1170px;top:175px;width:310px"><table><tr><th>CTQ</th><th>METHOD</th><th>FREQ.</th></tr>{"".join(f"<tr><td style=font-weight:700>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in ctq)}</table><div class="note" style="margin-top:18px">Same defect, same decision, in every factory: graded examples, not adjectives.</div></div>', ''))

# ---------- 12 TROUBLESHOOTING + BOM + REVISIONS (dark back page)
tr = [('No sound in RADIO mode', 'Band slider between detents', 'Move slider fully to AM, FM or WX'), ('Lantern does not light', 'Diffuser not fully raised', 'Lift to the 40 mm stop'),
      ('Crank turns, no charge LEDs', 'Crank lead unseated on board', 'Re-seat connector, repeat step 02'), ('Rattle when shaken', 'Front screw not seated', 'Re-drive T10 in cross pattern'),
      ('Water inside after splash', 'Back plate seal pinched', 'Replace seal, re-close back (step 06)')]
rev = [('A', 'NOV 2026', 'First release for build. All drawings regenerated from model rev 02.', 'H. ORTEGA')]
pages.append(page(12, 8, 'TROUBLESHOOTING & CONTROL', '07 · 08', f'''
<div class="box" style="left:60px;top:250px;width:860px"><table><tr><th>SYMPTOM</th><th>LIKELY CAUSE</th><th>ACTION</th></tr>{''.join(f'<tr><td style="font-weight:700">{a}</td><td>{b}</td><td>{c}</td></tr>' for a, b, c in tr)}</table></div>
<div class="box" style="left:980px;top:250px;width:500px"><table><tr><th>REV</th><th>DATE</th><th>CHANGE</th><th>BY</th></tr>{''.join(f'<tr><td class="or" style="font-weight:700">{a}</td><td>{b}</td><td>{c}</td><td>{d}</td></tr>' for a, b, c, d in rev)}</table>
<p class="mono" style="margin-top:26px"><b>DOCUMENT OWNER</b><br>Henry Ortega · Tigre Studio<br>tigrestudiodesign.github.io</p>
<p class="mono" style="margin-top:18px;opacity:.75">This is a portfolio study: an original product, documented in the same structure, drawing language and quality system I used for 50+ factory tech manuals. No content from any client document is reproduced.</p></div>''',
    'What to do when it is wrong, and who owns the document.', dark=True))

html = f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body>{"".join(pages)}</body></html>'
open('/home/claude/bcman/manual.html', 'w').write(html)
print('pages', len(pages))
