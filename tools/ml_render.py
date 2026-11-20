"""Material Library - fifteen prototype materials rebuilt as 50 mm physical samples (Tigre Studio, 2026).
Each sample is read from the crop of Henry's own prototype photo (img/mlr__*.webp): structure, repeat and colours,
then built with the same material system as tools/cmf_render.py: real yarn geometry for every knit, woven tows for
carbon, printed struts for the lattice, displaced rubber for every outsole, and transmission for clear rubber.

usage: python3 tools/ml_render.py <sample key|board> <out.png> [res_x] [res_y] [spp]
"""
import sys, os, math, runpy, random
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARGS = sys.argv[1:]
sys.argv = ['cmf_render', '__lib__', '/tmp/none.png']
L = runpy.run_path(f'{ROOT}/tools/cmf_render.py')
globals().update({k: v for k, v in L.items() if not k.startswith('__')})
import bpy
from mathutils import Vector

KEY = ARGS[0]; OUT = ARGS[1]
RX = int(ARGS[2]) if len(ARGS) > 2 else 1200
RY = int(ARGS[3]) if len(ARGS) > 3 else 1200
SPP = int(ARGS[4]) if len(ARGS) > 4 else 64
S = 50.0
H = S / 2 - 3.2     # relief half-size inside a plate border

# ------------------------------------------------------------------ yarn colour variants
def yarn_mat(name, cols, mode='solid', period=1.9, gloss=0.0):
    """mode: solid | rows (heathered courses) | melange (two-colour twist) | gradient (space-dyed along x)"""
    m = mat_yarn(cols[0]); n = N.__new__(N); n.m = m; n.nt = m.node_tree; n.b = n.nt.nodes['Principled BSDF']; n.out = n.nt.nodes['Material Output']
    if mode == 'solid':
        if gloss: n.set(Roughness=0.35, **{'Coat Weight': gloss})
        return m
    x, y, v = n.xy_mm()
    if mode == 'rows':
        f = n.math('GREATER_THAN', n.math('SINE', n.math('MULTIPLY', y, math.pi / period * 0.5)), 0.35)
    elif mode == 'melange':
        nz = n.node('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.1; nz.inputs['Detail'].default_value = 0; n.link(v, nz.inputs['Vector'])
        f = smooth(n, 0.49, 0.51, nz.outputs['Fac'])
    elif mode == 'gradient':
        rp = n.node('ShaderNodeValToRGB'); e = rp.color_ramp.elements
        e[0].position = 0.0; e[0].color = lin(cols[0]); e[1].position = 0.5; e[1].color = lin(cols[1])
        e3 = e.new(1.0); e3.color = lin(cols[2])
        n.link(n.math('DIVIDE', n.math('ADD', x, S / 2), S), rp.inputs['Fac'])
        n.link(rp.outputs['Color'], n.b.inputs['Base Color']); n.b.inputs['Sheen Tint'].default_value = (1, 1, 1, 1)
        return m
    else:
        f = 0.0
    mix = n.node('ShaderNodeMix'); mix.data_type = 'RGBA'; n.link(f, mix.inputs['Factor'])
    mix.inputs[6].default_value = lin(cols[0]); mix.inputs[7].default_value = lin(cols[1])
    n.link(mix.outputs[2], n.b.inputs['Base Color'])
    if gloss: n.set(Roughness=0.35, **{'Coat Weight': gloss})
    return m

def tube(name, pts, r, mat, flat=1.0):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r * MM; cu.bevel_resolution = 4; cu.use_fill_caps = True
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for p_, co in zip(sp.points, pts): p_.co = (co[0] * MM, co[1] * MM, co[2] * MM, 1)
    ob = link_obj(name, cu); cu.materials.append(mat); ob.scale.z = flat; return ob

def plate(name, mat, th=3.0, r=2.0, top_mat=None, res=520):
    """moulded plate with a relief sheet on top (relief fades to the border)"""
    ob = rounded_block(name, S, S, th, r, seg=6); ob.data.materials.append(mat)
    top = grid_sheet(name + ' relief', S - 2 * r - 0.4, S - 2 * r - 0.4, res); top.location.z = th * MM + 0.01 * MM
    top.data.materials.append(top_mat or mat)
    return [ob, top]

def rubber(hexc, rough=0.7):
    n = N('rubber ' + hexc); n.set(**{'Base Color': lin(hexc), 'Roughness': rough, 'Subsurface Weight': 0.1, 'Subsurface Scale': 0.0012})
    return n

# ------------------------------------------------------------------ the fifteen builders
def b_pink_knit():
    k = yarn_knit('pink knit', yarn_mat('pink', ['#D9506F']), S, wale=2.1, course=1.7, curl=0.0)
    vol = yarn_mat('volt', ['#A9DB4C'])
    # bound edge: a folded volt binding tape wrapping the lower edge
    objs = [k]
    for i in range(3):
        z = 1.4 + i * 0.5
        objs.append(tube('binding', [(-S / 2, -S / 2 + 3.2 - i * 0.2, z), (S / 2, -S / 2 + 3.2 - i * 0.2, z)], 1.6, vol, flat=0.55))
    for i in range(int(S / 1.4)):
        x = -S / 2 + 0.7 + i * 1.4
        objs.append(tube('bind rib', [(x, -S / 2 + 0.6, 2.3), (x, -S / 2 + 5.6, 2.3)], 0.42, vol))
    return objs

def b_blue_knit():
    return [yarn_knit('sock', yarn_mat('blue', ['#5B67C6', '#7686DA'], 'rows', period=1.4), S, wale=1.6, course=1.35, r=0.34, curl=6.0)]

def b_sculpt_knit():
    base = yarn_knit('base', yarn_mat('white', ['#E9E5E0']), S, wale=1.8, course=1.5, r=0.38, curl=0.0)
    red = yarn_mat('red', ['#C9483F'])
    rnd = random.Random(7); objs = [base]; g = 3.6; n = int(S / g)
    # raised maze: a deterministic random walk over a 3.6 mm grid, knitted as thick red cords
    seen = set()
    for start in range(9):
        cx, cy = rnd.randrange(n), rnd.randrange(n); pts = []
        for step in range(18):
            seen.add((cx, cy)); pts.append((-S / 2 + (cx + 0.5) * g, -S / 2 + (cy + 0.5) * g, 1.9))
            opts = [(cx + dx, cy + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= cx + dx < n and 0 <= cy + dy < n and (cx + dx, cy + dy) not in seen]
            if not opts: break
            cx, cy = rnd.choice(opts)
        if len(pts) > 2: objs.append(tube('maze', pts, 1.25, red, flat=0.8))
    return objs

def b_iri_knit():
    base = yarn_knit('lime', yarn_mat('lime', ['#E6EBC2']), S, wale=1.9, course=1.55, r=0.38, curl=0.0)
    net = yarn_mat('purple', ['#7C4A86'], gloss=0.6)
    objs = [base]; p = 7.0
    for i in range(-8, 9):
        c = i * p
        for sgn in (1, -1):
            pts = []
            for q in range(61):
                x = -S / 2 + q * S / 60; y = sgn * (x - c)
                if -S / 2 <= y <= S / 2: pts.append((x, y, 1.3))
            if len(pts) > 2: objs.append(tube('net', pts, 0.45, net, flat=0.7))
    return objs

def b_melange():
    return [yarn_knit('melange', yarn_mat('melange', ['#2A2A2A', '#E2E0DC'], 'melange'), S, wale=1.8, course=1.5, r=0.4, curl=6.0)]

def b_pastel_knit():
    k = yarn_knit('pastel', yarn_mat('pastel', ['#EDB9C6', '#F1E0A6', '#C8B4E6'], 'gradient'), S, wale=1.8, course=1.5, r=0.4, curl=0.0)
    fl = yarn_mat('float', ['#6C3E86'])
    objs = [k]
    for i in range(-6, 7):
        c = i * 8.0; pts = []
        for q in range(41):
            x = -S / 2 + 1 + q * (S - 2) / 40; y = 0.35 * (x - c)
            if -S / 2 + 1 <= y <= S / 2 - 1: pts.append((x, y, 1.15))
        if len(pts) > 2: objs.append(tube('float', pts, 0.32, fl))
    return objs

def b_white_rib():
    under = rounded_block('underlay', S, S, 0.8, 0.6, seg=2); um = N('underlay'); um.set(**{'Base Color': lin('#7F93B4'), 'Roughness': 0.7, 'Sheen Weight': 0.4}); under.data.materials.append(um.m)
    wm = yarn_mat('white', ['#ECEFEA'])
    objs = [under]; pitch = 5.0
    for j in range(int(S / pitch)):
        y = -S / 2 + 2 + j * pitch
        objs.append(tube('cord', [(-S / 2, y, 2.4), (S / 2, y, 2.4)], 1.35, wm, flat=0.85))
        # ladder threads across the open gap to the next cord
        if j < int(S / pitch) - 1:
            for i in range(int(S / 1.6)):
                x = -S / 2 + 0.8 + i * 1.6
                objs.append(tube('ladder', [(x, y + 1.2, 2.1), (x, y + pitch - 1.2, 2.1)], 0.26, wm))
    return objs

def b_black_perf():
    n = N('perf film'); d = dot_field(n, 2.6)
    x, _, _ = n.xy_mm()
    r = n.math('ADD', 0.08, n.math('MULTIPLY', smooth(n, -S / 2, S / 2, x), 0.3))
    hole = n.math('LESS_THAN', d, r)
    rim = n.math('MULTIPLY', smooth(n, 0.12, 0.0, n.math('ABSOLUTE', n.math('SUBTRACT', d, r))), 1.0)
    n.set(**{'Base Color': lin('#141513'), 'Roughness': 0.22, 'Coat Weight': 0.6, 'Coat Roughness': 0.12})
    bp = n.node('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.6; bp.inputs['Distance'].default_value = 0.0002
    n.link(rim, bp.inputs['Height']); n.link(bp.outputs['Normal'], n.b.inputs['Normal'])
    tr = n.node('ShaderNodeBsdfTransparent'); ms = n.node('ShaderNodeMixShader')
    n.link(hole, ms.inputs['Fac']); n.link(n.b.outputs[0], ms.inputs[1]); n.link(tr.outputs[0], ms.inputs[2]); n.link(ms.outputs[0], n.out.inputs['Surface'])
    f = grid_sheet('film', S, S, 8, thick=0.5); f.location.z = 0.8 * MM; f.data.materials.append(n.m)
    # a pale backing knit under the film, so the graded perforation reads
    bk = yarn_knit('backing', yarn_mat('backing', ['#9A9890']), S - 1, wale=1.6, course=1.35, r=0.3, curl=0.0)
    return [f, bk]

def b_grey_lattice():
    """3D-printed hex lattice: struts and raised nodes, PA12 grey with powder grain"""
    m = N('pa12'); m.set(**{'Base Color': lin('#6F6B60'), 'Roughness': 0.78}); m.micro(5.0, 0.25, 0.00006)
    base = rounded_block('skin', S, S, 0.8, 0.6, seg=2); bm_ = N('skin'); bm_.set(**{'Base Color': lin('#2E2B24'), 'Roughness': 0.8}); base.data.materials.append(bm_.m)
    objs = [base]; a = 4.2; hgt = a * math.sqrt(3)
    nodes = set()
    for i in range(-8, 9):
        for j in range(-8, 9):
            cx = i * 1.5 * a; cy = j * hgt + (i % 2) * hgt / 2
            ring = [(cx + a * math.cos(math.radians(60 * k)), cy + a * math.sin(math.radians(60 * k))) for k in range(7)]
            if all(abs(px) > S / 2 - 1 or abs(py) > S / 2 - 1 for px, py in ring): continue
            pts = [(max(-S / 2 + 1, min(S / 2 - 1, px)), max(-S / 2 + 1, min(S / 2 - 1, py)), 2.2) for px, py in ring]
            objs.append(tube('strut', pts, 0.75, m.m))
            for px, py, _ in pts[:-1]: nodes.add((round(px, 2), round(py, 2)))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=10, radius=1.25 * MM); proto = bpy.context.object; proto.data.materials.append(m.m); bpy.ops.object.shade_smooth()
    for (px, py) in nodes:
        if abs(px) < S / 2 - 1.5 and abs(py) < S / 2 - 1.5:
            o = bpy.data.objects.new('node', proto.data); bpy.context.collection.objects.link(o); o.location = (px * MM, py * MM, 2.4 * MM); objs.append(o)
    bpy.data.objects.remove(proto)
    return objs

def b_carbon():
    """2x2 twill carbon: tows as anisotropic fibre, rotated 90 degrees between warp and weft, under a thick clear coat"""
    n = N('carbon'); x, y, _ = n.xy_mm()
    tw = 2.6
    u = n.math('FLOOR', n.math('DIVIDE', x, tw)); v = n.math('FLOOR', n.math('DIVIDE', y, tw))
    warp = n.math('LESS_THAN', n.math('MODULO', n.math('ADD', n.math('ADD', u, v), 400.0), 4.0), 2.0)
    n.set(**{'Base Color': lin('#7A7F7D'), 'Metallic': 1.0, 'Roughness': 0.3, 'Anisotropic': 0.92, 'Coat Weight': 1.0, 'Coat Roughness': 0.015, 'Coat IOR': 1.52})
    n.link(n.math('MULTIPLY', warp, 0.25), n.b.inputs['Anisotropic Rotation'])
    tg = n.node('ShaderNodeTangent'); tg.direction_type = 'UV_MAP'; n.link(tg.outputs['Tangent'], n.b.inputs['Tangent'])
    # tow crown: each tow is slightly domed
    fu = n.math('SINE', n.math('MULTIPLY', n.math('FRACT', n.math('DIVIDE', x, tw)), math.pi))
    fv = n.math('SINE', n.math('MULTIPLY', n.math('FRACT', n.math('DIVIDE', y, tw)), math.pi))
    crown = n.node('ShaderNodeMix'); crown.data_type = 'FLOAT'; n.link(warp, crown.inputs['Factor']); n.link(fv, crown.inputs[2]); n.link(fu, crown.inputs[3])
    bp = n.node('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.35; bp.inputs['Distance'].default_value = 0.0002
    n.link(crown.outputs[0], bp.inputs['Height']); n.link(bp.outputs['Normal'], n.b.inputs['Normal'])
    ob = rounded_block('carbon', S, S, 1.6, 0.6, seg=4); ob.data.materials.append(n.m)
    return [ob]

def b_trans_sole():
    k = yarn_knit('under', yarn_mat('knit', ['#D9D7E4']), S - 2, wale=1.8, course=1.5, r=0.36, curl=0.0)
    n = N('clear rubber'); x, y, _ = n.xy_mm()
    w = n.math('SINE', n.math('MULTIPLY', n.math('ADD', n.math('DIVIDE', y, 3.4), n.math('MULTIPLY', n.math('SINE', n.math('DIVIDE', x, 6.0)), 0.9)), math.pi))
    h = smooth(n, 0.35, 0.95, w)
    n.set(**{'Base Color': lin('#E4E1F4'), 'Roughness': 0.22, 'Transmission Weight': 0.95, 'IOR': 1.5, 'Subsurface Weight': 0.0})
    va = n.node('ShaderNodeVolumeAbsorption'); va.inputs['Color'].default_value = lin('#B4AADA'); va.inputs['Density'].default_value = 0.25
    n.disp(h, 1.4, half=H)
    slab = rounded_block('clear slab', S, S, 1.6, 1.4, seg=6); slab.visible_shadow = False; slab.location.z = 1.1 * MM; slab.data.materials.append(n.m)
    top = grid_sheet('lugs', S - 3.2, S - 3.2, 520, thick=0.0); top.visible_shadow = False; top.location.z = 2.71 * MM; top.data.materials.append(n.m)
    return [k, slab, top]

def b_pink_sole():
    n = rubber('#EFAFB2', 0.62); d = dot_field(n, 3.4); x, y, _ = n.xy_mm()
    r = n.math('ADD', 0.12, n.math('MULTIPLY', smooth(n, -S / 2, S / 2, y), 0.24))
    dimple = n.math('MULTIPLY', smooth(n, 0.0, 0.1, n.math('SUBTRACT', r, d)), -1.0)
    panel = 0.0
    h = n.math('MULTIPLY', n.math('ADD', 1.0, dimple), 0.6)
    n.disp(h, 2.0, half=H, mid=0.0); n.micro(2.4, 0.06)
    return plate('pink sole', n.m, th=4.0)

def b_volt_wave():
    n = rubber('#8A887B', 0.66); x, y, _ = n.xy_mm()
    wave = n.math('ADD', x, n.math('MULTIPLY', n.math('SINE', n.math('DIVIDE', y, 5.5)), 4.0))
    ph = n.math('FRACT', n.math('DIVIDE', wave, 9.0))
    inlay = n.math('LESS_THAN', n.math('ABSOLUTE', n.math('SUBTRACT', ph, 0.5)), 0.07)
    groove = n.math('MULTIPLY', n.math('POWER', n.math('ABSOLUTE', n.math('SINE', n.math('MULTIPLY', n.math('DIVIDE', wave, 1.1), math.pi))), 0.4), 0.35)
    h = n.math('ADD', groove, n.math('MULTIPLY', inlay, 0.55))
    col = n.node('ShaderNodeMix'); col.data_type = 'RGBA'; n.link(inlay, col.inputs['Factor'])
    col.inputs[6].default_value = lin('#8A887B'); col.inputs[7].default_value = lin('#C8E05A'); n.link(col.outputs[2], n.b.inputs['Base Color'])
    rr = n.node('ShaderNodeMix'); rr.data_type = 'FLOAT'; n.link(inlay, rr.inputs['Factor']); rr.inputs[2].default_value = 0.7; rr.inputs[3].default_value = 0.12
    n.link(rr.outputs[0], n.b.inputs['Roughness']); n.set(**{'Coat Weight': 0.0})
    n.disp(h, 0.9, half=H)
    return plate('volt wave', n.m, th=4.0)

def b_green_trac():
    """traction rubber: a staggered field of raised hex-cell lugs, each with a recessed centre (read from the photo)"""
    n = rubber('#3F8A51', 0.6)
    d = dot_field(n, 6.4, stagger=True)
    wall = smooth(n, 0.44, 0.40, d)
    pocket = smooth(n, 0.2, 0.26, d)
    h = n.math('MULTIPLY', wall, n.math('ADD', 0.45, n.math('MULTIPLY', pocket, 0.55)))
    n.disp(h, 1.6, half=H); n.micro(2.0, 0.05)
    return plate('green trac', n.m, th=3.5)

def b_black_sole():
    n = rubber('#111312', 0.55); x, y, _ = n.xy_mm()
    px, py = 4.2, 3.6
    cu = n.math('FRACT', n.math('ADD', n.math('DIVIDE', x, px), n.math('MULTIPLY', n.math('MODULO', n.math('FLOOR', n.math('DIVIDE', y, py)), 2.0), 0.5)))
    cv = n.math('FRACT', n.math('DIVIDE', y, py))
    lug = n.math('MULTIPLY', n.math('LESS_THAN', n.math('ABSOLUTE', n.math('SUBTRACT', cu, 0.5)), 0.26), n.math('LESS_THAN', n.math('ABSOLUTE', n.math('SUBTRACT', cv, 0.5)), 0.22))
    col = n.node('ShaderNodeMix'); col.data_type = 'RGBA'; n.link(lug, col.inputs['Factor'])
    col.inputs[6].default_value = lin('#111312'); col.inputs[7].default_value = lin('#D9DCDA'); n.link(col.outputs[2], n.b.inputs['Base Color'])
    n.disp(n.math('MULTIPLY', lug, 1.0), 0.8, half=H); n.micro(2.0, 0.05)
    return plate('black sole', n.m, th=3.5)

BUILD = {k[2:]: v for k, v in globals().items() if k.startswith('b_')}
ORDER = ['pink_knit', 'blue_knit', 'sculpt_knit', 'iri_knit', 'melange', 'pastel_knit', 'white_rib', 'black_perf', 'grey_lattice', 'carbon',
         'trans_sole', 'pink_sole', 'volt_wave', 'green_trac', 'black_sole']

if KEY == 'board':
    for idx, k in enumerate(ORDER):
        objs = BUILD[k]()
        x = (idx % 5 - 2) * 66; y = (1 - idx // 5) * 64
        place(objs, x, y, [0.04, -0.03, 0.05, -0.05, 0.02][idx % 5])
        print('sample', idx + 1, k)
    studio(); lights()
    cam((0.02, -0.46, 0.40), (0.0, -0.008, 0.0), 54, fstop=11)
else:
    BUILD[KEY]()
    studio(); lights()
    cam((0.03, -0.088, 0.082), (0.0, 0.002, 0.0), 68, fstop=18)
render(OUT, SPP, RX, RY)
