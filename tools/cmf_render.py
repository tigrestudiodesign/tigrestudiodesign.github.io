"""Nike CMF Reads - material sample renders (Tigre Studio, 2026).
Every chip is built for its material class, not just its colour: knit and mesh get true displaced yarn
structure, foams get subsurface scattering, Air units are inflated TPU pillows (clear or gloss), prints are
raised ink on a textile base, chrome is polished metal, sensory nodes and pins are real relief.
Colours and finishes come straight from CMFN_D in index.html, so the renders and the page cannot drift.
Colour management: Khronos PBR Neutral (built for product colour fidelity), D50-ish neutral studio.

usage: python3 tools/cmf_render.py <product key|fan> <out.png> [res_x] [res_y] [spp]
"""
import sys, os, math, json, re, tempfile
import bpy, bmesh
from mathutils import Vector, Euler

KEY = sys.argv[1]; OUT = sys.argv[2]
RX = int(sys.argv[3]) if len(sys.argv) > 3 else 1600
RY = int(sys.argv[4]) if len(sys.argv) > 4 else 1000
SPP = int(sys.argv[5]) if len(sys.argv) > 5 else 128
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MM = 0.001

src = open(f'{ROOT}/index.html', encoding='utf8').read()
i = src.index('const CMFN_D=') + len('const CMFN_D='); j = src.index(';\n', i)
DATA = json.loads(src[i:j])

# fonts: the site's own JetBrains Mono, converted from woff2 once
def site_font(name):
    out = os.path.join(tempfile.gettempdir(), f'tigre_{name}.ttf')
    if not os.path.exists(out):
        from fontTools.ttLib import TTFont
        f = TTFont(f'{ROOT}/fonts/{name}.woff2'); f.flavor = None; f.save(out)
    return bpy.data.fonts.load(out)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
MONO = site_font('JetBrainsMono-700')

def lin(h, a=1.0):
    h = h.lstrip('#'); c = [int(h[k:k + 2], 16) / 255 for k in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [a]

def shade(h, f):
    c = lin(h); return [min(1, x * f) for x in c[:3]] + [1]

# ------------------------------------------------------------------ node helpers
class N:
    def __init__(self, name):
        self.m = bpy.data.materials.new(name); self.m.use_nodes = True
        self.nt = self.m.node_tree; self.b = self.nt.nodes['Principled BSDF']; self.out = self.nt.nodes['Material Output']
        self.m.displacement_method = 'BOTH'
    def node(self, t, **kw):
        n = self.nt.nodes.new(t)
        for k, v in kw.items(): setattr(n, k, v)
        return n
    def link(self, a, b): self.nt.links.new(a, b)
    def math(self, op, a, b=None, clamp=False):
        n = self.node('ShaderNodeMath'); n.operation = op; n.use_clamp = clamp
        for idx, v in enumerate((a, b)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[idx].default_value = v
            else: self.link(v, n.inputs[idx])
        return n.outputs[0]
    def xy_mm(self, rot=0.0):
        """object-space coordinates in mm (chips are built at the origin, then moved, so patterns stay per-chip)"""
        tc = self.node('ShaderNodeTexCoord'); mp = self.node('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (1000, 1000, 1000); mp.inputs['Rotation'].default_value = (0, 0, rot)
        self.link(tc.outputs['Object'], mp.inputs['Vector'])
        sp = self.node('ShaderNodeSeparateXYZ'); self.link(mp.outputs['Vector'], sp.inputs['Vector'])
        return sp.outputs['X'], sp.outputs['Y'], mp.outputs['Vector']
    def disp(self, h, scale_mm, mid=0.0, half=27.0):
        # fade the relief out at the sheet edge so plates keep a clean moulded border
        x, y, _ = self.xy_mm()
        fx = smooth(self, half + 1.6, half - 0.6, self.math('ABSOLUTE', x)); fy = smooth(self, half + 1.6, half - 0.6, self.math('ABSOLUTE', y))
        h = self.math('MULTIPLY', h, self.math('MULTIPLY', fx, fy))
        d = self.node('ShaderNodeDisplacement'); d.inputs['Scale'].default_value = scale_mm * MM; d.inputs['Midlevel'].default_value = mid
        self.link(h, d.inputs['Height']); self.link(d.outputs['Displacement'], self.out.inputs['Displacement'])
    def micro(self, scale=1.0, strength=0.06, dist=0.00008):
        """fine surface noise for normals (mould texture / foam skin / fibre)"""
        _, _, v = self.xy_mm(); n = self.node('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = scale; n.inputs['Detail'].default_value = 8
        self.link(v, n.inputs['Vector'])
        bp = self.node('ShaderNodeBump'); bp.inputs['Strength'].default_value = strength; bp.inputs['Distance'].default_value = dist
        self.link(n.outputs['Fac'], bp.inputs['Height']); self.link(bp.outputs['Normal'], self.b.inputs['Normal'])
    def set(self, **kw):
        for k, v in kw.items(): self.b.inputs[k].default_value = v

def smooth(n, e0, e1, x):
    """smoothstep via map range"""
    m = n.node('ShaderNodeMapRange'); m.interpolation_type = 'SMOOTHSTEP'
    m.inputs['From Min'].default_value = e0; m.inputs['From Max'].default_value = e1
    if isinstance(x, (int, float)): m.inputs['Value'].default_value = x
    else: n.link(x, m.inputs['Value'])
    return m.outputs['Result']

def dot_field(n, pitch, stagger=True, rot=0.0):
    """distance (in pitch units, 0..0.7) to the nearest dot of a staggered grid"""
    x, y, _ = n.xy_mm(rot)
    u = n.math('DIVIDE', x, pitch); v = n.math('DIVIDE', y, pitch * (0.866 if stagger else 1.0))
    row = n.math('FLOOR', v)
    off = n.math('MULTIPLY', n.math('MODULO', row, 2.0), 0.5 if stagger else 0.0)
    cu = n.math('SUBTRACT', n.math('FRACT', n.math('ADD', u, off)), 0.5)
    cv = n.math('SUBTRACT', n.math('FRACT', v), 0.5)
    cv = n.math('MULTIPLY', cv, 0.866 if stagger else 1.0)
    return n.math('SQRT', n.math('ADD', n.math('MULTIPLY', cu, cu), n.math('MULTIPLY', cv, cv)))

# ------------------------------------------------------------------ material classes
def knit_height(n, wale=1.5, course=1.25, rot=0.0):
    """jersey V-stitch: columns of chevron loops; returns (height 0..1, gap mask between legs)"""
    x, y, _ = n.xy_mm(rot)
    u = n.math('DIVIDE', x, wale); v = n.math('DIVIDE', y, course)
    cu = n.math('SUBTRACT', n.math('FRACT', u), 0.5); a = n.math('ABSOLUTE', cu)
    cv = n.math('FRACT', n.math('SUBTRACT', v, n.math('MULTIPLY', a, 1.25)))
    leg = n.math('POWER', n.math('SINE', n.math('MULTIPLY', cv, math.pi)), 0.55)
    w = n.math('SUBTRACT', 1.0, n.math('POWER', n.math('DIVIDE', n.math('SUBTRACT', a, 0.25), 0.23), 2.0), clamp=True)
    h = n.math('MULTIPLY', leg, n.math('POWER', w, 0.6))
    # yarn twist: fine diagonal striations along each leg
    tw = n.math('SINE', n.math('MULTIPLY', n.math('ADD', n.math('MULTIPLY', u, 9.0), n.math('MULTIPLY', v, 5.0)), math.pi))
    h = n.math('ADD', h, n.math('MULTIPLY', n.math('MULTIPLY', tw, 0.06), h))
    return h, a, cv

def mat_knit(hexc, open_knit=False, wale=2.3):
    n = N('knit ' + hexc)
    h, a, cv = knit_height(n, wale=wale, course=wale * 0.83)
    # recess darkening + heather so the yarn reads, not a flat colour
    nz = n.node('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.9; nz.inputs['Detail'].default_value = 3
    _, _, v = n.xy_mm(); n.link(v, nz.inputs['Vector'])
    occ = n.math('ADD', 0.62, n.math('MULTIPLY', h, 0.38))
    occ = n.math('MULTIPLY', occ, n.math('ADD', 0.93, n.math('MULTIPLY', nz.outputs['Fac'], 0.12)))
    mix = n.node('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
    mix.inputs['Factor'].default_value = 1.0; mix.inputs[6].default_value = lin(hexc)
    cmb = n.node('ShaderNodeCombineColor'); n.link(occ, cmb.inputs[0]); n.link(occ, cmb.inputs[1]); n.link(occ, cmb.inputs[2])
    n.link(cmb.outputs[0], mix.inputs[7]); n.link(mix.outputs[2], n.b.inputs['Base Color'])
    n.set(Roughness=0.86, **{'Sheen Weight': 0.85, 'Sheen Roughness': 0.38, 'Subsurface Weight': 0.18, 'Subsurface Scale': 0.0012})
    n.b.inputs['Sheen Tint'].default_value = shade(hexc, 1.25)
    n.disp(h, 0.55)
    if open_knit:
        # open knit: the gap between the two legs opens into a hole at mid-loop
        hole = n.math('MULTIPLY', n.math('LESS_THAN', a, 0.085), n.math('GREATER_THAN', n.math('SINE', n.math('MULTIPLY', cv, math.pi)), 0.55))
        n.m.blend_method = 'HASHED' if hasattr(n.m, 'blend_method') else None
        tr = n.node('ShaderNodeBsdfTransparent'); ms = n.node('ShaderNodeMixShader')
        n.link(hole, ms.inputs['Fac']); n.link(n.b.outputs[0], ms.inputs[1]); n.link(tr.outputs[0], ms.inputs[2])
        n.link(ms.outputs[0], n.out.inputs['Surface'])
    return n.m

def mat_mesh(hexc, pitch=2.2):
    """fine engineered mesh: hex-staggered open cells over a backing layer"""
    n = N('mesh ' + hexc)
    d = dot_field(n, pitch)
    hole = n.math('LESS_THAN', d, 0.24)
    h = smooth(n, 0.2, 0.42, d)
    occ = n.math('ADD', 0.7, n.math('MULTIPLY', h, 0.3))
    cmb = n.node('ShaderNodeCombineColor')
    for k in range(3): n.link(n.math('MULTIPLY', occ, lin(hexc)[k]), cmb.inputs[k])
    n.link(cmb.outputs[0], n.b.inputs['Base Color'])
    n.set(Roughness=0.8, **{'Sheen Weight': 0.6, 'Sheen Roughness': 0.4})
    n.b.inputs['Sheen Tint'].default_value = shade(hexc, 1.4)
    n.disp(h, 0.35)
    tr = n.node('ShaderNodeBsdfTransparent'); ms = n.node('ShaderNodeMixShader')
    n.link(hole, ms.inputs['Fac']); n.link(n.b.outputs[0], ms.inputs[1]); n.link(tr.outputs[0], ms.inputs[2])
    n.link(ms.outputs[0], n.out.inputs['Surface'])
    return n.m

def mat_print_dots(hexc, base='#070702', pitch=2.2, fade=False):
    """raised textured print: satin ink dots standing proud of a matte mesh base; fade shrinks the dots across the chip"""
    n = N('print ' + hexc)
    d = dot_field(n, pitch)
    r = 0.33
    if fade:
        x, _, _ = n.xy_mm()
        r = n.math('ADD', 0.12, n.math('MULTIPLY', smooth(n, -30, 30, x), 0.24))
        dot = n.math('LESS_THAN', d, r)
        h = n.math('MULTIPLY', dot, smooth(n, 0.0, 0.08, n.math('SUBTRACT', r, d)))
    else:
        dot = n.math('LESS_THAN', d, r); h = smooth(n, r, r - 0.1, d)
    mix = n.node('ShaderNodeMix'); mix.data_type = 'RGBA'; n.link(dot, mix.inputs['Factor'])
    mix.inputs[6].default_value = lin(base); mix.inputs[7].default_value = lin(hexc)
    n.link(mix.outputs[2], n.b.inputs['Base Color'])
    rough = n.node('ShaderNodeMix'); rough.data_type = 'FLOAT'; n.link(dot, rough.inputs['Factor'])
    rough.inputs[2].default_value = 0.85; rough.inputs[3].default_value = 0.3; n.link(rough.outputs[0], n.b.inputs['Roughness'])
    n.set(**{'Coat Weight': 0.0})
    n.disp(h, 0.45)
    return n.m

def mat_chrome(hexc):
    n = N('chrome'); n.set(**{'Base Color': lin(hexc), 'Metallic': 1.0, 'Roughness': 0.035})
    n.micro(4.0, 0.015); return n.m

def mat_foam(hexc, rough=0.46):
    """supercritical foam with a satin moulded skin: SSS body, fine pores, soft sheen"""
    n = N('foam ' + hexc)
    n.set(**{'Base Color': lin(hexc), 'Roughness': rough, 'Subsurface Weight': 0.22, 'Subsurface Scale': 0.003,
             'Coat Weight': 0.12, 'Coat Roughness': 0.35})
    n.b.inputs['Subsurface Radius'].default_value = (1.0, 0.75, 0.55)
    _, _, v = n.xy_mm()
    vo = n.node('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 3.2; n.link(v, vo.inputs['Vector'])
    nz = n.node('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.6; nz.inputs['Detail'].default_value = 6; n.link(v, nz.inputs['Vector'])
    pores = n.math('MULTIPLY', smooth(n, 0.0, 0.08, vo.outputs['Distance']), 1.0)
    hgt = n.math('ADD', n.math('MULTIPLY', pores, 0.4), n.math('MULTIPLY', nz.outputs['Fac'], 0.6))
    bp = n.node('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.35; bp.inputs['Distance'].default_value = 0.0001
    n.link(hgt, bp.inputs['Height']); n.link(bp.outputs['Normal'], n.b.inputs['Normal'])
    return n.m


def mat_foam_cell(hexc):
    """the cut face of a supercritical foam: closed cells, rougher and a touch darker than the skin"""
    n = N('foam cell ' + hexc); _, _, v = n.xy_mm()
    vo = n.node('ShaderNodeTexVoronoi'); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs['Scale'].default_value = 0.95; n.link(v, vo.inputs['Vector'])
    h = smooth(n, 0.0, 0.09, vo.outputs['Distance'])
    occ = n.math('ADD', 0.72, n.math('MULTIPLY', h, 0.28))
    cmb = n.node('ShaderNodeCombineColor')
    for k in range(3): n.link(n.math('MULTIPLY', occ, lin(hexc)[k]), cmb.inputs[k])
    n.link(cmb.outputs[0], n.b.inputs['Base Color'])
    n.set(**{'Roughness': 0.85, 'Subsurface Weight': 0.3, 'Subsurface Scale': 0.003})
    bp = n.node('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.8; bp.inputs['Distance'].default_value = 0.00025
    n.link(h, bp.inputs['Height']); n.link(bp.outputs['Normal'], n.b.inputs['Normal'])
    return n.m

def mat_moulded(hexc, rough=0.32, texture=0.05, sss=0.12):
    n = N('moulded ' + hexc)
    n.set(**{'Base Color': lin(hexc), 'Roughness': rough, 'Subsurface Weight': sss, 'Subsurface Scale': 0.0015})
    n.micro(1.6, texture); return n.m

def mat_ribbed(hexc, pitch=2.4):
    n = N('ribbed ' + hexc); x, _, _ = n.xy_mm()
    h = n.math('POWER', n.math('ABSOLUTE', n.math('SINE', n.math('MULTIPLY', n.math('DIVIDE', x, pitch), math.pi))), 0.5)
    n.set(**{'Base Color': lin(hexc), 'Roughness': 0.62, 'Subsurface Weight': 0.1, 'Subsurface Scale': 0.0015})
    n.disp(h, 0.9); n.micro(2.0, 0.05); return n.m

def mat_rubber_tex(hexc):
    """outsole rubber: pebble texture + fine mould grain, matte"""
    n = N('rubber ' + hexc); _, _, v = n.xy_mm()
    vo = n.node('ShaderNodeTexVoronoi'); vo.feature = 'SMOOTH_F1'; vo.inputs['Scale'].default_value = 0.55; n.link(v, vo.inputs['Vector'])
    h = smooth(n, 0.0, 0.5, vo.outputs['Distance']); h = n.math('SUBTRACT', 1.0, h)
    n.set(**{'Base Color': lin(hexc), 'Roughness': 0.78, 'Subsurface Weight': 0.08, 'Subsurface Scale': 0.0012})
    n.disp(h, 0.5); n.micro(3.0, 0.08); return n.m

def mat_pins(hexc, pitch=1.9):
    n = N('pins ' + hexc); d = dot_field(n, pitch, stagger=False)
    h = smooth(n, 0.26, 0.2, d)
    n.set(**{'Base Color': lin(hexc), 'Roughness': 0.66, 'Subsurface Weight': 0.15, 'Subsurface Scale': 0.0015})
    n.disp(h, 1.1); n.micro(2.0, 0.04); return n.m

def mat_nodes(hexc, mode, pitch=8.0, rough=0.38):
    """sensory nodes: 'tips' are domes, 'cups' are rings with a hollow, 'base' is a matte plate with sockets"""
    n = N('nodes ' + hexc); d = dot_field(n, pitch, stagger=True)
    if mode == 'tips':
        h = n.math('SQRT', n.math('SUBTRACT', 1.0, n.math('POWER', n.math('DIVIDE', d, 0.36), 2.0), clamp=True))
        sc_ = 3.2
    elif mode == 'cups':
        ring = n.math('SUBTRACT', 1.0, n.math('POWER', n.math('DIVIDE', n.math('SUBTRACT', d, 0.3), 0.09), 2.0), clamp=True)
        h = n.math('SUBTRACT', ring, n.math('MULTIPLY', n.math('LESS_THAN', d, 0.26), 0.35)); sc_ = 2.4
    else:
        h = n.math('MULTIPLY', smooth(n, 0.34, 0.28, d), -1.0); sc_ = 1.2
    n.set(**{'Base Color': lin(hexc), 'Roughness': rough, 'Subsurface Weight': 0.3, 'Subsurface Scale': 0.0025,
             'Sheen Weight': 0.25 if mode != 'base' else 0.0})
    n.disp(h, sc_, mid=0.0); n.micro(2.0, 0.03); return n.m

def mat_tpu_clear(hexc):
    """see-through Air: tinted TPU film, near-perfect gloss, absorption volume for depth"""
    n = N('tpu ' + hexc)
    n.set(**{'Base Color': [min(1, c * 1.6) for c in lin(hexc)[:3]] + [1], 'Roughness': 0.015, 'Transmission Weight': 1.0, 'IOR': 1.5,
             'Coat Weight': 0.3, 'Coat Roughness': 0.02})
    va = n.node('ShaderNodeVolumeAbsorption'); va.inputs['Color'].default_value = lin(hexc); va.inputs['Density'].default_value = 0.5
    n.link(va.outputs[0], n.out.inputs['Volume'])
    return n.m

def mat_gloss(hexc):
    n = N('gloss ' + hexc)
    n.set(**{'Base Color': lin(hexc), 'Roughness': 0.12, 'Coat Weight': 1.0, 'Coat Roughness': 0.01, 'Specular IOR Level': 0.6})
    return n.m

def mat_print_matte(hexc):
    n = N('print matte ' + hexc)
    n.set(**{'Base Color': lin(hexc), 'Roughness': 0.9}); n.micro(1.2, 0.05); return n.m


def yarn_knit(name, mat, S, wale=2.4, course=1.9, r=0.46, curl=11.0, open_knit=False, rib=False):
    """real jersey yarn: one polyline per course, x = t + a*sin(2t), y = b*cos(t), z = c*cos(2t) per stitch
    (the classic loop model), so every loop interlocks with the course below it"""
    if open_knit: wale, course, r = wale * 1.12, course * 1.18, r * 0.92
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r * MM; cu.bevel_resolution = 3
    cu.use_fill_caps = True
    nst = int(S / wale) + 1; nrow = int(S / course) + 1; spl = 18
    a, b, c = 0.95, course * 0.95, r * 0.9
    for row in range(nrow):
        sp = cu.splines.new('POLY'); pts = []
        for k in range(nst):
            for q in range(spl):
                t = -math.pi + 2 * math.pi * q / spl
                x = (k * 2 * math.pi + t + a * math.sin(2 * t)) * wale / (2 * math.pi) - S / 2
                y = row * course + b * math.cos(t) * 0.5 - S / 2
                z = c * math.cos(2 * t)
                if rib and (k % 2): z = -c * math.cos(2 * t) - 2.2 * r   # back loops sink: 1x1 rib
                if -S / 2 <= x <= S / 2 and -S / 2 - 1 <= y <= S / 2 + 1:
                    xn, yn = (x + S / 2) / S, (y + S / 2) / S
                    tt = max(0.0, (xn + (1 - yn)) - 1.35) / 0.65
                    pts.append((x * MM, y * MM, (z + r + curl * tt ** 2.2) * MM))
        if len(pts) < 2: continue
        sp.points.add(len(pts) - 1)
        for p_, co in zip(sp.points, pts): p_.co = (*co, 1)
    ob = link_obj(name, cu); cu.materials.append(mat); return ob

def mat_yarn(hexc):
    n = N('yarn ' + hexc); n.m.displacement_method = 'BUMP'
    tc = n.node('ShaderNodeTexCoord'); wv = n.node('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'DIAGONAL'
    wv.inputs['Scale'].default_value = 1400; wv.inputs['Distortion'].default_value = 2.0; wv.inputs['Detail'].default_value = 4
    n.link(tc.outputs['Object'], wv.inputs['Vector'])
    nz = n.node('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 900; n.link(tc.outputs['Object'], nz.inputs['Vector'])
    hgt = n.math('ADD', n.math('MULTIPLY', wv.outputs['Fac'], 0.7), n.math('MULTIPLY', nz.outputs['Fac'], 0.3))
    bp = n.node('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.45; bp.inputs['Distance'].default_value = 0.00008
    n.link(hgt, bp.inputs['Height']); n.link(bp.outputs['Normal'], n.b.inputs['Normal'])
    hv = n.node('ShaderNodeTexNoise'); hv.inputs['Scale'].default_value = 60; n.link(tc.outputs['Object'], hv.inputs['Vector'])
    mix = n.node('ShaderNodeMix'); mix.data_type = 'RGBA'; n.link(hv.outputs['Fac'], mix.inputs['Factor'])
    mix.inputs[6].default_value = shade(hexc, 0.8); mix.inputs[7].default_value = shade(hexc, 0.98)
    n.link(mix.outputs[2], n.b.inputs['Base Color'])
    n.set(Roughness=0.82, **{'Sheen Weight': 0.45, 'Sheen Roughness': 0.4, 'Subsurface Weight': 0.2, 'Subsurface Scale': 0.0006})
    n.b.inputs['Sheen Tint'].default_value = shade(hexc, 1.1)
    return n.m

def classify(z):
    t = (z[4] + ' | ' + z[5]).lower(); fin = z[5].lower()
    if 'atomknit' in t or 'open knit' in t: return 'knit_open'
    if 'knit' in t or 'engineered upper' in t: return 'knit'
    if 'raised dots' in t: return 'dots'
    if 'print' in t and 'satin' in fin and 'textured' in t: return 'dots_fade'
    if 'mesh' in fin: return 'mesh'
    if 'mirror' in fin or 'metallic' in t: return 'chrome'
    if 'see-through' in fin: return 'tpu'
    if 'high gloss' in fin: return 'gloss_air'
    if 'pin texture' in fin: return 'pins'
    if 'node tips' in z[3].lower(): return 'tips'
    if 'node cups' in z[3].lower(): return 'cups'
    if 'sensory-node bottom' in t: return 'nodebase'
    if 'ribbed' in fin: return 'ribbed'
    if 'rubber' in t and 'textured' in fin: return 'rubber'
    if 'foam' in t or 'zoomx' in t: return 'foam'
    if 'printed graphic' in t or 'print' in t: return 'print'
    if 'pod' in t: return 'pod'
    if 'satin' in fin or 'low sheen' in fin or 'smooth' in fin: return 'satin'
    return 'matte'

def material_for(z, kind):
    hx = z[6]
    return {'knit_open': lambda: mat_knit(hx, True), 'knit': lambda: mat_knit(hx), 'dots': lambda: mat_print_dots(hx),
            'dots_fade': lambda: mat_print_dots(hx, fade=True), 'mesh': lambda: mat_mesh(hx), 'chrome': lambda: mat_chrome(hx),
            'tpu': lambda: mat_tpu_clear(hx), 'gloss_air': lambda: mat_gloss(hx), 'pins': lambda: mat_pins(hx),
            'tips': lambda: mat_nodes(hx, 'tips'), 'cups': lambda: mat_nodes(hx, 'cups'), 'nodebase': lambda: mat_nodes(hx, 'base', rough=0.72),
            'ribbed': lambda: mat_ribbed(hx), 'rubber': lambda: mat_rubber_tex(hx), 'foam': lambda: mat_foam(hx),
            'print': lambda: mat_print_matte(hx), 'pod': lambda: mat_moulded(hx, 0.34, 0.03, 0.2),
            'satin': lambda: mat_moulded(hx, 0.36, 0.03), 'matte': lambda: mat_moulded(hx, 0.7, 0.07)}[kind]()

# ------------------------------------------------------------------ chip geometry (built at origin, top face at z=thickness)
def link_obj(name, me):
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); return ob

def grid_sheet(name, sx, sy, res, curl=0.0, thick=0.0):
    """dense sheet for true displacement; optional corner curl so fabric reads as fabric"""
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=res, y_subdivisions=int(res * sy / sx), size=1)
    ob = bpy.context.object; ob.name = name; ob.scale = (sx * MM, sy * MM, 1); bpy.ops.object.transform_apply(scale=True)
    if curl:
        for v in ob.data.vertices:
            x, y = v.co.x / (sx * MM) + 0.5, v.co.y / (sy * MM) + 0.5
            t = max(0.0, (x + (1 - y)) - 1.35) / 0.65
            v.co.z += curl * MM * (t ** 2.2)
    if thick:
        so = ob.modifiers.new('t', 'SOLIDIFY'); so.thickness = thick * MM; so.offset = -1
    bpy.ops.object.shade_smooth()
    return ob

def rounded_block(name, sx, sy, sz, r, seg=8, res=0):
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, sz / 2 * MM)); ob = bpy.context.object; ob.name = name
    ob.scale = (sx / 2 * MM, sy / 2 * MM, sz / 2 * MM); bpy.ops.object.transform_apply(scale=True)
    bv = ob.modifiers.new('b', 'BEVEL'); bv.width = r * MM; bv.segments = seg; bv.limit_method = 'NONE'
    if res:
        bpy.ops.object.modifier_apply(modifier='b')
        sd = ob.modifiers.new('s', 'SUBSURF'); sd.subdivision_type = 'SIMPLE'; sd.levels = res; sd.render_levels = res
    bpy.ops.object.shade_smooth(); return ob

def pillow(name, sx, sy, sz):
    """inflated Air-style pillow: superellipse plan, pressure-rounded section, a weld flange and two internal weld lines"""
    bm = bmesh.new(); nu, nv = 96, 40
    verts = []
    for iv in range(nv + 1):
        phi = -math.pi / 2 + math.pi * iv / nv
        row = []
        for iu in range(nu):
            th = 2 * math.pi * iu / nu
            c, s = math.cos(th), math.sin(th)
            ex = 4.0
            px = math.copysign(abs(c) ** (2 / ex), c) * sx / 2; py = math.copysign(abs(s) ** (2 / ex), s) * sy / 2
            k = math.cos(phi) ** 0.35
            z = sz / 2 * math.sin(phi)
            # weld lines across the width pinch the top and bottom
            pinch = 1.0
            for wx in (-sx / 6, sx / 6):
                pinch *= 1 - 0.0 * math.exp(-((px * k - wx) / (sx * 0.025)) ** 2)
            rs = max(0.0, math.cos(phi)) ** 0.22
            row.append(bm.verts.new(((px * rs) * MM, (py * rs) * MM, (sz / 2 + z * pinch) * MM)))
        verts.append(row)
    for iv in range(nv):
        for iu in range(nu):
            a, b_ = verts[iv][iu], verts[iv][(iu + 1) % nu]; c_, d_ = verts[iv + 1][(iu + 1) % nu], verts[iv + 1][iu]
            try: bm.faces.new((a, b_, c_, d_))
            except ValueError: pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = link_obj(name, me)
    sd = ob.modifiers.new('s', 'SUBSURF'); sd.levels = 1; sd.render_levels = 2
    for p in me.polygons: p.use_smooth = True
    # flange: the RF-welded seam around the unit
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=1, depth=0.6 * MM, location=(0, 0, sz / 2 * MM)); fl = bpy.context.object; fl.name = name + ' flange'
    fl.scale = (sx / 2 * 1.04 * MM, sy / 2 * 1.08 * MM, 1); bpy.ops.object.transform_apply(scale=True)
    bv = fl.modifiers.new('b', 'BEVEL'); bv.width = 0.25 * MM; bv.segments = 2
    return ob, fl

def pebble(name, sx, sy, sz):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=1, location=(0, 0, sz / 2 * MM)); ob = bpy.context.object; ob.name = name
    ob.scale = (sx / 2 * MM, sy / 2 * MM, sz / 2 * MM); bpy.ops.object.transform_apply(scale=True)
    for v in ob.data.vertices:
        # flatten top/bottom a little: a pod, not an egg
        v.co.z = (sz / 2 * MM) + (v.co.z - sz / 2 * MM) * (0.85 + 0.15 * (1 - abs(v.co.z - sz / 2 * MM) / (sz / 2 * MM)))
        if v.co.z < 0.15 * sz * MM: v.co.z = 0.15 * sz * MM * (1 - 0.5 * (1 - v.co.z / (0.15 * sz * MM + 1e-9)))
    bpy.ops.object.shade_smooth(); return ob

def chip(z, kind, mat):
    """returns list of objects and the chip's top height (mm) for the tag"""
    S = 62
    if kind in ('knit', 'knit_open'):
        ob = yarn_knit('knit', mat_yarn(z[6]), S, open_knit=(kind == 'knit_open'))
        return [ob], 2.5
    if kind == 'mesh':
        ob = grid_sheet('fabric', S, S, 560, curl=11.0)
        ob.location.z = 1.2 * MM
        bk = None
        if kind != 'knit':
            # backing layer seen through the open cells
            bk = grid_sheet('backing', S - 1, S - 1, 4); bk.location.z = 0.5 * MM
            bm_ = N('backing'); bm_.set(**{'Base Color': shade(z[6], 0.55), 'Roughness': 0.9, 'Sheen Weight': 0.5}); bk.data.materials.append(bm_.m)
        ob.data.materials.append(mat); return [o for o in (ob, bk) if o], 2.5
    if kind in ('dots', 'dots_fade', 'pins', 'ribbed', 'rubber', 'tips', 'cups', 'nodebase'):
        th = {'dots': 2.0, 'dots_fade': 2.0, 'pins': 4.0, 'ribbed': 4.0, 'rubber': 5.0, 'tips': 6.0, 'cups': 6.0, 'nodebase': 6.0}[kind]
        ob = rounded_block('plate', S, S, th, 1.6 if th < 3 else 2.6, seg=6)
        top = grid_sheet('relief', S - 2 * (1.6 if th < 3 else 2.6) - 0.4, S - 2 * (1.6 if th < 3 else 2.6) - 0.4, 520)
        top.location.z = th * MM + 0.01 * MM
        ob.data.materials.append(mat); top.data.materials.append(mat)
        # the plate body shares the colour but not the relief
        return [ob, top], th + 1.0
    if kind == 'foam':
        # moulded block with one corner cut away, so the cell structure under the satin skin shows (a CMF section cut)
        ob = rounded_block('foam', S, S * 0.72, 16, 5.5, seg=10); ob.data.materials.append(mat)
        bpy.ops.mesh.primitive_cube_add(location=(S * 0.42 * MM, -S * 0.3 * MM, 16 * MM)); cut = bpy.context.object
        cut.scale = (S * 0.17 * MM, S * 0.14 * MM, 9 * MM)
        cut.data.materials.append(mat_foam_cell(z[6]))
        bo = ob.modifiers.new('cut', 'BOOLEAN'); bo.object = cut; bo.operation = 'DIFFERENCE'; bo.material_mode = 'TRANSFER'
        cut.hide_render = True; cut.hide_viewport = True; cut.parent = ob
        return [ob], 16
    if kind == 'tpu':
        ob, fl = pillow('air', S * 1.06, S * 0.7, 15); ob.data.materials.append(mat); fl.data.materials.append(mat); return [ob, fl], 15
    if kind == 'gloss_air':
        ob, fl = pillow('air', S * 1.06, S * 0.7, 10); ob.data.materials.append(mat); fl.data.materials.append(mat); return [ob, fl], 13
    if kind == 'chrome':
        ob = rounded_block('badge', S * 0.9, S * 0.55, 3.2, 1.4, seg=10); ob.data.materials.append(mat)
        base = rounded_block('card', S, S * 0.72, 1.2, 1.0, seg=4)
        bm_ = N('card'); bm_.set(**{'Base Color': lin('#1C1C1E'), 'Roughness': 0.85}); base.data.materials.append(bm_.m)
        ob.location.z = 1.2 * MM
        return [ob, base], 4.4
    if kind == 'pod':
        ob = pebble('pod', S * 0.92, S * 0.6, 20); ob.data.materials.append(mat); return [ob], 20
    # moulded colour chip, stepped like a production colour plaque (4 mm and 2.5 mm), with a hang hole
    ob = rounded_block('chip', S, S * 0.8, 2.5, 1.2, seg=8); ob.data.materials.append(mat)
    st = rounded_block('step', S * 0.55, S * 0.8, 4.0, 1.2, seg=8); st.location.x = -S * 0.225 * MM; st.data.materials.append(mat)
    bo = ob.modifiers.new('step', 'BOOLEAN'); bo.object = st; bo.operation = 'UNION'; st.hide_render = True; st.hide_viewport = True
    bpy.ops.mesh.primitive_cylinder_add(radius=2.6 * MM, depth=12 * MM, vertices=48, location=(S * 0.36 * MM, S * 0.28 * MM, 0)); hole = bpy.context.object
    for o in (ob,):
        bo = o.modifiers.new('hole', 'BOOLEAN'); bo.object = hole; bo.operation = 'DIFFERENCE'
    hole.hide_render = True; hole.hide_viewport = True
    st.parent = ob; hole.parent = ob
    return [ob], 4.0

def place(objs, x, y, rz):
    for o in objs:
        o.location.x += x * MM; o.location.y += y * MM
        o.rotation_euler.z += rz
        if o.rotation_euler.z and o.location.x != x * MM: pass
    # rotate around the chip centre: parent-less, so rotate positions too
    c = Vector((x * MM, y * MM, 0))
    for o in objs:
        d = o.location - c; d.z = 0
        r = Euler((0, 0, rz)).to_matrix() @ d
        o.location.x, o.location.y = c.x + r.x, c.y + r.y

def tag(num, x, y, rz):
    """hang-tag style number plate: ink plate, orange mono numerals, printed"""
    t = rounded_block('tag', 13, 7.5, 0.8, 0.8, seg=3)
    tm = N('tag ink'); tm.set(**{'Base Color': lin('#0B0B0C'), 'Roughness': 0.55}); t.data.materials.append(tm.m)
    bpy.ops.object.text_add(location=(0, -2.3 * MM, 0.82 * MM)); tx = bpy.context.object
    tx.data.body = f'{num:02d}'; tx.data.font = MONO; tx.data.size = 5.6 * MM; tx.data.align_x = 'CENTER'; tx.data.extrude = 0.05 * MM
    om = N('tag orange'); om.set(**{'Base Color': lin('#FF5A1F'), 'Roughness': 0.4}); tx.data.materials.append(om.m)
    place([t, tx], x, y, rz)

# ------------------------------------------------------------------ studio
def studio(dark=False):
    """CMF light table: neutral seamless (faint 24 mm grid, the Tigre/Tarka backdrop), big top softbox, two strip lights, rim"""
    bg = '#1B1B1D' if dark else '#9C978F'
    verts, faces = [], []
    R = 0.18; W = 1.2
    prof = [(y, 0.0) for y in (-1.2, -0.6, -0.2, 0.0, 0.12)] + [(0.12 + R * math.sin(a), R - R * math.cos(a)) for a in [k * math.pi / 2 / 16 for k in range(1, 17)]] + [(0.12 + R, 0.6), (0.12 + R, 1.2)]
    for (y, zz) in prof: verts += [(-W, y, zz), (W, y, zz)]
    for k in range(len(prof) - 1):
        a = 2 * k; faces.append((a, a + 1, a + 3, a + 2))
    me = bpy.data.meshes.new('sweep'); me.from_pydata(verts, [], faces); sw = link_obj('sweep', me)
    for p in me.polygons: p.use_smooth = True
    n = N('sweep')
    tc = n.node('ShaderNodeTexCoord'); br = n.node('ShaderNodeTexBrick'); br.offset = 0.0; br.squash = 1.0
    br.inputs['Scale'].default_value = 1.0; br.inputs['Mortar Size'].default_value = 0.0005
    br.inputs['Brick Width'].default_value = 0.024; br.inputs['Row Height'].default_value = 0.024
    br.inputs['Color1'].default_value = lin(bg); br.inputs['Color2'].default_value = lin(bg)
    br.inputs['Mortar'].default_value = shade(bg, 0.9 if not dark else 1.6)
    n.link(tc.outputs['Object'], br.inputs['Vector']); n.link(br.outputs['Color'], n.b.inputs['Base Color'])
    n.set(Roughness=0.92); sw.data.materials.append(n.m)
    w = bpy.data.worlds.new('w'); w.use_nodes = True; b = w.node_tree.nodes['Background']
    b.inputs['Color'].default_value = lin('#E8E6E2'); b.inputs['Strength'].default_value = 0.06; sc.world = w

def area(name, loc, look, size, power, col='#FFFFFF', sy=None, spread=180):
    l = bpy.data.lights.new(name, 'AREA'); l.size = size; l.energy = power; l.color = lin(col)[:3]; l.spread = math.radians(spread)
    if sy: l.shape = 'RECTANGLE'; l.size_y = sy
    ob = link_obj(name, l); ob.location = loc
    ob.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()

def lights(k=0.13):
    area('key', (-0.36, -0.30, 0.42), (0, 0, 0), 0.4, 36 * k, '#FFF8F0', sy=0.28, spread=60)
    area('top fill', (0.0, 0.0, 0.7), (0, 0, 0), 0.6, 3.5 * k, '#FFFFFF', sy=0.4, spread=120)
    area('strip R', (0.40, 0.04, 0.16), (0, 0, 0.01), 0.05, 10 * k, '#EEF3FF', sy=0.6, spread=60)
    area('rim', (0.05, 0.40, 0.22), (0, 0, 0.0), 0.5, 10 * k, '#FFFFFF', sy=0.06, spread=60)
    # reflection card: a big soft white panel on the sweep wall, seen only in reflections (chrome, gloss, satin highlights)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0.0, 0.26, 0.26)); rc = bpy.context.object; rc.name = 'reflection card'
    rc.scale = (0.9, 0.34, 1); rc.rotation_euler = (math.radians(-60), 0, 0)
    em = bpy.data.materials.new('card'); em.use_nodes = True; nt = em.node_tree; nt.nodes.remove(nt.nodes['Principled BSDF'])
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Strength'].default_value = 9 * k
    gr = nt.nodes.new('ShaderNodeTexGradient'); tc = nt.nodes.new('ShaderNodeTexCoord'); ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (0.25, 0.25, 0.25, 1); ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    # three strip softboxes with black gaps: sharp bands in chrome, a long gradient in gloss
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'X'; wv.wave_profile = 'SAW'
    wv.inputs['Scale'].default_value = 1.5; nt.links.new(tc.outputs['Generated'], wv.inputs['Vector'])
    st = nt.nodes.new('ShaderNodeMath'); st.operation = 'GREATER_THAN'; st.inputs[1].default_value = 0.22; nt.links.new(wv.outputs['Fac'], st.inputs[0])
    nt.links.new(tc.outputs['Generated'], gr.inputs['Vector']); nt.links.new(gr.outputs['Fac'], ramp.inputs['Fac'])
    mul = nt.nodes.new('ShaderNodeMixRGB'); mul.blend_type = 'MULTIPLY'; mul.inputs['Fac'].default_value = 1.0
    nt.links.new(ramp.outputs['Color'], mul.inputs[1]); nt.links.new(st.outputs[0], mul.inputs[2]); nt.links.new(mul.outputs[0], e.inputs['Color'])
    nt.links.new(e.outputs[0], nt.nodes['Material Output'].inputs['Surface']); rc.data.materials.append(em)
    rc.visible_camera = False; rc.visible_diffuse = False; rc.visible_shadow = False
    area('bounce', (0.15, -0.5, 0.05), (0, 0, 0.02), 0.6, 1.5 * k, '#FFFFFF', sy=0.3)

def cam(loc, look, lens, fstop=None):
    c = bpy.data.cameras.new('cam'); c.lens = lens; c.clip_start = 0.01
    ob = link_obj('cam', c); ob.location = loc; d = Vector(look) - Vector(loc)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler(); sc.camera = ob
    if fstop: c.dof.use_dof = True; c.dof.focus_distance = d.length; c.dof.aperture_fstop = fstop

# ------------------------------------------------------------------ scenes
def product(p):
    zs = p['z']; n = len(zs)
    slots = {4: [(-44, 46, 0.06), (44, 48, -0.05), (-46, -40, -0.04), (44, -42, 0.07)],
             5: [(-72, 42, 0.06), (0, 46, -0.03), (72, 42, -0.06), (-38, -38, -0.05), (40, -40, 0.05)]}[n]
    for k, z in enumerate(zs):
        kind = classify(z); m = material_for(z, kind)
        objs, top = chip(z, kind, m)
        x, y, rz = slots[k]
        place(objs, x, y, rz)
        tag(k + 1, x - 24, y - 41, rz)
        print('chip', k + 1, z[2], kind)
    studio(); lights()
    wide = n == 5
    cam((0.03, -0.34 if not wide else -0.40, 0.27 if not wide else 0.30), (0.0, -0.012 if not wide else -0.004, 0.0), 64 if not wide else 76, fstop=10)

def fan():
    """27 colours from all six products as a CMF fan deck: rounded cards on a Chicago-screw pivot, each card in its finish,
    printed with name, hex and finish in the site's mono"""
    seen = []; cards = []
    for p in DATA:
        for z in p['z']:
            if z[6].upper() in seen: continue
            seen.append(z[6].upper()); cards.append(z)
    N_ = len(cards); L, Wd, T = 170, 40, 0.7
    piv = Vector((0.0, -0.065, 0.0))
    spread = math.radians(150)
    for k, z in enumerate(cards):
        kind = classify(z)
        fin = z[5].lower()
        if kind in ('knit', 'knit_open', 'mesh', 'dots', 'dots_fade'): m = mat_moulded(z[6], 0.78, 0.09, 0.0)
        elif kind == 'chrome': m = mat_chrome(z[6])
        elif kind in ('tpu', 'gloss_air'): m = mat_gloss(z[6])
        elif 'satin' in fin or kind in ('foam', 'pod'): m = mat_moulded(z[6], 0.38, 0.03, 0.0)
        else: m = mat_moulded(z[6], 0.62, 0.06, 0.0)
        bpy.ops.mesh.primitive_cube_add(location=(0, L / 2 * MM, T / 2 * MM)); c = bpy.context.object; c.name = f'card {k}'
        c.scale = (Wd / 2 * MM, L / 2 * MM, T / 2 * MM); bpy.ops.object.transform_apply(scale=True)
        bv = c.modifiers.new('b', 'BEVEL'); bv.width = 3.5 * MM; bv.segments = 8; bv.affect = 'EDGES'
        bv2 = c.modifiers.new('b2', 'BEVEL'); bv2.width = 0.2 * MM; bv2.segments = 2
        c.data.materials.append(m)
        # printed label on the card tip: name + hex, light ink on dark cards
        lum = sum(lin(z[6])[:3]) / 3
        inkm = N('ink'); inkm.set(**{'Base Color': lin('#F2EEE6' if lum < 0.22 else '#0B0B0C'), 'Roughness': 0.6})
        objs = [c]
        # printed along the exposed right edge of each card, reading from the tip toward the pivot
        for (txt, xx, sz) in ((z[2].upper(), Wd / 2 - 5.5, 3.4), (z[6].upper() + '  ' + f'{k + 1:02d}', Wd / 2 - 10.5, 2.6)):
            bpy.ops.object.text_add(location=(xx * MM, (L - 6) * MM, T * MM + 0.01 * MM)); tx = bpy.context.object
            tx.rotation_euler.z = -math.pi / 2
            tx.data.body = txt; tx.data.font = MONO; tx.data.size = sz * MM; tx.data.extrude = 0.02 * MM; tx.data.materials.append(inkm.m)
            objs.append(tx)
        a = -spread / 2 + spread * k / (N_ - 1)
        for o in objs:
            o.location.z += k * (T + 0.08) * MM
            p0 = Vector((o.location.x, o.location.y, 0)); r = Euler((0, 0, a)).to_matrix() @ p0
            o.location.x, o.location.y = piv.x + r.x, piv.y + r.y; o.rotation_euler.z += a
    # Chicago screw through the stack
    h = N_ * (T + 0.08) + 2
    bpy.ops.mesh.primitive_cylinder_add(radius=5.2 * MM, depth=1.4 * MM, vertices=64, location=(piv.x, piv.y + 6 * MM, (h + 0.7) * MM))
    alu = N('alu'); alu.set(**{'Base Color': lin('#C8CBD0'), 'Metallic': 1.0, 'Roughness': 0.22}); bpy.context.object.data.materials.append(alu.m)
    bv = bpy.context.object.modifiers.new('b', 'BEVEL'); bv.width = 0.5 * MM; bv.segments = 4; bpy.ops.object.shade_smooth()
    studio(); lights(0.14)
    cam((0.018, -0.37, 0.5), (0.018, 0.03, 0.0), 50, fstop=11)


# ------------------------------------------------------------------ HESTIA: Warm Minimalist material board
def weave(name, mat, S, pitch=2.0, r=0.32, gap=0.9, curl=0.0):
    """open technical weave: warp and weft yarns passing over and under each other, with open cells between"""
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r * MM; cu.bevel_resolution = 3
    n = int(S / pitch)
    for axis in (0, 1):
        for i in range(n):
            sp = cu.splines.new('POLY'); pts = []
            c = -S / 2 + (i + 0.5) * pitch
            for q in range(n * 8 + 1):
                u = -S / 2 + q * S / (n * 8)
                ph = (u + S / 2) / pitch * math.pi + (i % 2) * math.pi
                z = r * 0.9 * math.sin(ph) * (1 if axis == 0 else -1)
                x, y = (u, c) if axis == 0 else (c, u)
                pts.append((x * MM, y * MM, (z + r) * MM))
            sp.points.add(len(pts) - 1)
            for p_, co in zip(sp.points, pts): p_.co = (*co, 1)
    ob = link_obj(name, cu); cu.materials.append(mat); return ob

def silicone_dots(base_objs, S, pitch=4.0, r=1.1, hexc='#B65A3A'):
    """printed silicone grip dots standing on the knit"""
    m = N('silicone ' + hexc); m.set(**{'Base Color': lin(hexc), 'Roughness': 0.42, 'Subsurface Weight': 0.35, 'Subsurface Scale': 0.0015, 'Coat Weight': 0.25, 'Coat Roughness': 0.3})
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=r * MM, location=(0, 0, 0)); proto = bpy.context.object
    proto.scale.z = 0.55; bpy.ops.object.transform_apply(scale=True); bpy.ops.object.shade_smooth(); proto.data.materials.append(m.m)
    out = []; n = int(S / pitch)
    for i in range(n):
        for j in range(n):
            x = -S / 2 + (i + 0.5) * pitch + (pitch / 2 if j % 2 else 0); y = -S / 2 + (j + 0.5) * pitch * 0.866 + 2
            if abs(x) > S / 2 - 3 or abs(y) > S / 2 - 3: continue
            xn, yn = (x + S / 2) / S, (y + S / 2) / S
            tt = max(0.0, (xn + (1 - yn)) - 1.35) / 0.65
            if tt > 0.05: continue
            o = bpy.data.objects.new('dot', proto.data); bpy.context.collection.objects.link(o)
            o.location = (x * MM, y * MM, 1.25 * MM); out.append(o)
    bpy.data.objects.remove(proto)
    return out

def anodised(hexc):
    """bead-blasted anodised aluminium body with diamond-cut bright chamfers (material slot 1)"""
    body = N('anodised ' + hexc); body.set(**{'Base Color': lin(hexc), 'Metallic': 1.0, 'Roughness': 0.34, 'Anisotropic': 0.0})
    body.micro(6.0, 0.05, 0.00003)
    cutm = N('diamond cut'); cutm.set(**{'Base Color': shade(hexc, 1.25), 'Metallic': 1.0, 'Roughness': 0.07, 'Anisotropic': 0.6})
    return body.m, cutm.m

def hestia_board():
    P = [('Oatmeal', '#B9A787', 'knit'), ('Birch', '#ABA498', 'mesh'), ('Slate-moss', '#5E6555', 'rib'),
         ('Terracotta', '#B65A3A', 'grip'), ('Champagne', '#B49C74', 'alu'), ('Graphite', '#2A2B2B', 'weave')]
    slots = [(-74, 44, 0.05), (0, 48, -0.03), (74, 44, -0.06), (-74, -40, -0.04), (0, -38, 0.03), (74, -40, 0.05)]
    S = 60
    for k, (nm, hx, kind) in enumerate(P):
        if kind == 'knit': objs = [yarn_knit('oat', mat_yarn(hx), S)]
        elif kind == 'rib': objs = [yarn_knit('rib', mat_yarn(hx), S, wale=2.0, rib=True)]
        elif kind == 'mesh':
            ob = grid_sheet('spacer', S, S, 520, curl=11.0); ob.location.z = 1.2 * MM; ob.data.materials.append(mat_mesh(hx, pitch=2.6))
            bk = grid_sheet('backing', S - 1, S - 1, 4); bk.location.z = 0.5 * MM
            bm_ = N('backing'); bm_.set(**{'Base Color': shade(hx, 0.55), 'Roughness': 0.9, 'Sheen Weight': 0.5}); bk.data.materials.append(bm_.m)
            objs = [ob, bk]
        elif kind == 'grip':
            objs = [yarn_knit('grip knit', mat_yarn(hx), S)] + silicone_dots(None, S, hexc=hx)
        elif kind == 'alu':
            bm, cm = anodised(hx)
            bpy.ops.mesh.primitive_cube_add(location=(0, 0, 4 * MM)); ob = bpy.context.object
            ob.scale = (S / 2 * MM, S * 0.36 * MM, 4 * MM); bpy.ops.object.transform_apply(scale=True)
            ob.data.materials.append(bm); ob.data.materials.append(cm)
            bv = ob.modifiers.new('chamfer', 'BEVEL'); bv.width = 1.1 * MM; bv.segments = 1; bv.material = 1
            bv2 = ob.modifiers.new('soft', 'BEVEL'); bv2.width = 0.15 * MM; bv2.segments = 2; bv2.material = 1
            bpy.ops.object.shade_smooth()
            ws = ob.modifiers.new('ws', 'WEIGHTED_NORMAL'); ws.keep_sharp = True
            objs = [ob]
        else:
            wm = N('weave ' + hx); wm.set(**{'Base Color': lin(hx), 'Roughness': 0.55, 'Sheen Weight': 0.35, 'Coat Weight': 0.15})
            frame = rounded_block('window frame', S, S, 1.2, 1.0, seg=3)
            fm = N('frame'); fm.set(**{'Base Color': lin('#1A1A1B'), 'Roughness': 0.6}); frame.data.materials.append(fm.m)
            bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0)); hole = bpy.context.object; hole.scale = ((S - 10) / 2 * MM, (S - 10) / 2 * MM, 5 * MM)
            bo = frame.modifiers.new('open', 'BOOLEAN'); bo.object = hole; bo.operation = 'DIFFERENCE'; hole.hide_render = True; hole.hide_viewport = True; hole.parent = frame
            w = weave('weave', wm.m, S - 8, pitch=2.2); w.location.z = 1.4 * MM
            objs = [frame, w]
        x, y, rz = slots[k]
        place(objs, x, y, rz)
        tag(k + 1, x - 24, y - 40, rz)
        print('sample', k + 1, nm, kind)
    studio(); lights()
    cam((0.03, -0.40, 0.30), (0.0, -0.02, 0.0), 62, fstop=10)

def render(out, spp=None, rx=None, ry=None):
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = spp or SPP; sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 10; sc.cycles.transmission_bounces = 10; sc.cycles.transparent_max_bounces = 16
    sc.render.resolution_x = rx or RX; sc.render.resolution_y = ry or RY
    sc.view_settings.view_transform = 'Khronos PBR Neutral'; sc.view_settings.exposure = -2.0
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print('DONE', out)

if KEY != '__lib__':
    if KEY == 'fan': fan()
    elif KEY == 'hestia': hestia_board()
    else: product(next(p for p in DATA if p['k'] == KEY))
    render(OUT)
