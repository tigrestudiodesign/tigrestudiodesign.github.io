"""Trenza Alpargata · Muisca CMF study. Henry's loafer last (r.3dm) rebuilt as an alpargata in Blender Cycles.
usage: python3 alp.py <shot> <out.png> <colourway> [rx] [ry] [spp]
shots: hero, side, top, toe, sole, strap, heel, exploded, trio, flat
"""
import sys, math, os
import numpy as np
import rhino3dm as r3
import bpy
from mathutils import Vector, Matrix

SHOT, OUT, CW = sys.argv[1], sys.argv[2], sys.argv[3]
RX = int(sys.argv[4]) if len(sys.argv) > 4 else 1600
RY = int(sys.argv[5]) if len(sys.argv) > 5 else 1000
SPP = int(sys.argv[6]) if len(sys.argv) > 6 else 64
HERE = os.path.dirname(os.path.abspath(__file__))
LIFT = 0.026            # braided fique midsole inserted under the last (m)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def hexc(h, a=1.0):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [a]

PAL = {
 'manta':   dict(leather='#7A4320', thread='#23305E', lining='#E3D6BC', rubber='#1F1C19', fique='#C7A46E', bg='#E7E0D4', dark='#141210', stage='#4E1D12'),
 'tumbaga': dict(leather='#141210', thread='#C9A04A', lining='#2A221A', rubber='#141210', fique='#B8945C', bg='#2A2622', dark='#0C0B0A', stage='#141210'),
 'paramo':  dict(leather='#D6C7AA', thread='#C08A3A', lining='#E3D6BC', rubber='#2C3326', fique='#C7A46E', bg='#C9CCBE', dark='#121510', stage='#2F3A2B'),
}

def node_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    return m, m.node_tree, m.node_tree.nodes['Principled BSDF']

def N(nt, kind, **kw):
    n = nt.nodes.new(kind)
    for k, v in kw.items():
        if k == 'op': n.operation = v
        else: n.inputs[k].default_value = v
    return n

def math_(nt, op, a, b=None, c=None):
    n = nt.nodes.new('ShaderNodeMath'); n.operation = op
    for i, x in enumerate((a, b, c)):
        if x is None: continue
        if isinstance(x, (int, float)): n.inputs[i].default_value = x
        else: nt.links.new(x, n.inputs[i])
    return n.outputs[0]

def xyz(nt):
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs['Vector']); return tc.outputs['Object'], sep.outputs

def mixc(nt, fac, a, b):
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
    for inp, v in ((6, a), (7, b)):
        if isinstance(v, (list, tuple)): mx.inputs[inp].default_value = v
        else: nt.links.new(v, mx.inputs[inp])
    if isinstance(fac, (int, float)): mx.inputs['Factor'].default_value = fac
    else: nt.links.new(fac, mx.inputs['Factor'])
    return mx.outputs[2]

def mixs(nt, fac, a, b):
    mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(fac, mx.inputs[0]); nt.links.new(a, mx.inputs[1]); nt.links.new(b, mx.inputs[2]); return mx.outputs[0]

def img(nt, path, vec, box=False, interp='Cubic'):
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(path, check_existing=True); t.interpolation = interp
    if box: t.projection = 'BOX'; t.projection_blend = 0.06
    nt.links.new(vec, t.inputs['Vector']); return t.outputs['Color']

def plain(name, col, rough=0.5, metal=0.0, coat=0.0):
    m, nt, b = node_mat(name); b.inputs['Base Color'].default_value = hexc(col); b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal; b.inputs['Coat Weight'].default_value = coat; return m

def gold(name, rough=0.3, hammer=0.0):
    m, nt, b = node_mat(name); b.inputs['Base Color'].default_value = hexc('#D9B05C'); b.inputs['Metallic'].default_value = 1.0
    b.inputs['Roughness'].default_value = rough
    if hammer:
        v, _ = xyz(nt); vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 700; nt.links.new(v, vo.inputs['Vector'])
        bp = N(nt, 'ShaderNodeBump', Strength=hammer, Distance=0.0004); nt.links.new(vo.outputs['Distance'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m

def mats(cw, tag=''):
    P = PAL[cw]; T = lambda k: os.path.join(HERE, 'tex', f'{cw}_{k}.png')
    # ---- upper: painted manta toe + heel, over-under woven leather in between
    m, nt, b = node_mat('upper' + tag); v, s = xyz(nt)
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1 / 0.09,) * 3; nt.links.new(v, mp.inputs['Vector'])
    manta = img(nt, T('manta'), mp.outputs['Vector'], box=True)
    W = 0.0105  # strap width
    xc = math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', s['X'], 0.07 if not tag.endswith('L') else -0.07))
    a = math_(nt, 'DIVIDE', math_(nt, 'ADD', math_(nt, 'ADD', s['Y'], s['Z']), xc), W)
    bb = math_(nt, 'DIVIDE', math_(nt, 'SUBTRACT', math_(nt, 'SUBTRACT', s['Y'], s['Z']), xc), W)
    fa, fb = math_(nt, 'FRACT', a), math_(nt, 'FRACT', bb)
    ia, ib = math_(nt, 'FLOOR', a), math_(nt, 'FLOOR', bb)
    top = math_(nt, 'MODULO', math_(nt, 'ABSOLUTE', math_(nt, 'ADD', ia, ib)), 2.0)          # 0: strap A over, 1: B over
    ea = math_(nt, 'SUBTRACT', 0.5, math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', fa, 0.5)))   # 0 at edges, .5 centre
    eb = math_(nt, 'SUBTRACT', 0.5, math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', fb, 0.5)))
    edge = math_(nt, 'ADD', math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', 1, top), ea), math_(nt, 'MULTIPLY', top, eb))
    h = math_(nt, 'SMOOTH_MIN', math_(nt, 'MULTIPLY', edge, 6.0), 1.0, 0.4)                  # rounded strap profile
    gap = math_(nt, 'LESS_THAN', edge, 0.06)
    lc = hexc(P['leather']); ld = [x * 0.35 for x in lc[:3]] + [1]; lh = [min(1, x * 1.3) for x in lc[:3]] + [1]
    nz = N(nt, 'ShaderNodeTexNoise', Scale=900.0, Detail=6.0); nt.links.new(v, nz.inputs['Vector'])
    weavec = mixc(nt, gap, mixc(nt, math_(nt, 'MULTIPLY', nz.outputs['Fac'], 0.6), lc, lh), ld)
    weave_alt = mixc(nt, top, weavec, mixc(nt, 0.12, weavec, ld))                            # under-strap slightly darker
    # zones along the last (heel y=0, toe y=0.29)
    toe = math_(nt, 'GREATER_THAN', s['Y'], 0.205); heel = math_(nt, 'LESS_THAN', s['Y'], 0.062)
    zone = math_(nt, 'MAXIMUM', toe, heel)
    col = mixc(nt, zone, weave_alt, manta)
    nt.links.new(col, b.inputs['Base Color'])
    rgh = math_(nt, 'ADD', math_(nt, 'MULTIPLY', zone, 0.45), 0.38)
    nt.links.new(rgh, b.inputs['Roughness'])
    sh = math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', 1, zone), 0.25); nt.links.new(sh, b.inputs['Coat Weight'])
    b.inputs['Coat Roughness'].default_value = 0.3
    zone_sheen = math_(nt, 'MULTIPLY', zone, 0.5); nt.links.new(zone_sheen, b.inputs['Sheen Weight'])
    hb = math_(nt, 'ADD', math_(nt, 'MULTIPLY', h, math_(nt, 'SUBTRACT', 1, zone)), math_(nt, 'MULTIPLY', nz.outputs['Fac'], 0.05))
    bp = N(nt, 'ShaderNodeBump', Strength=0.9, Distance=0.0012); nt.links.new(hb, bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    UP = m
    # ---- faja strap (woven band), mapped along the strap
    m, nt, b = node_mat('faja' + tag); v, s = xyz(nt)
    xc0 = -0.07 if tag.endswith('L') else 0.07
    dx = math_(nt, 'SUBTRACT', s['X'], xc0); sg = math_(nt, 'SIGN', dx)
    u = math_(nt, 'ADD', dx, math_(nt, 'MULTIPLY', sg, math_(nt, 'SUBTRACT', 0.098, s['Z'])))
    vv = math_(nt, 'DIVIDE', math_(nt, 'SUBTRACT', s['Y'], 0.1455), 0.042)
    cmb = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(math_(nt, 'DIVIDE', u, 0.042 * 2048 / 320), cmb.inputs['X']); nt.links.new(vv, cmb.inputs['Y'])
    fj = img(nt, T('faja'), cmb.outputs['Vector']); nt.links.new(fj, b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.75; b.inputs['Sheen Weight'].default_value = 0.6
    nz = N(nt, 'ShaderNodeTexWave', Scale=1400.0); nz.wave_type = 'BANDS'; nz.bands_direction = 'X'; nt.links.new(v, nz.inputs['Vector'])
    bp = N(nt, 'ShaderNodeBump', Strength=0.3, Distance=0.0003); nt.links.new(nz.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    FJ = m
    # ---- sole: rubber below 4.5 mm, braided fique above, faja band at the top lip
    m, nt, b = node_mat('sole' + tag); v, s = xyz(nt)
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 's'
    z = s['Z']; rows = 2; zl0 = 0.0045; zl1 = 0.0045 + LIFT - 0.004
    rz = math_(nt, 'DIVIDE', math_(nt, 'SUBTRACT', z, zl0), (zl1 - zl0) / rows)
    rr = math_(nt, 'ABSOLUTE', math_(nt, 'SUBTRACT', math_(nt, 'FRACT', rz), 0.5))         # 0 centre of a braid row, .5 edge
    sm = math_(nt, 'MULTIPLY', at.outputs['Fac'], 1000 / 6.0)                               # 6 mm braid pitch
    chev = math_(nt, 'FRACT', math_(nt, 'ADD', sm, math_(nt, 'MULTIPLY', rr, 2.2)))
    strand = math_(nt, 'SINE', math_(nt, 'MULTIPLY', chev, math.pi))                         # rounded strand
    rowedge = math_(nt, 'SMOOTH_MIN', math_(nt, 'MULTIPLY', math_(nt, 'SUBTRACT', 0.5, rr), 8), 1, 0.3)
    hgt = math_(nt, 'MULTIPLY', strand, rowedge)
    fib = N(nt, 'ShaderNodeTexNoise', Scale=2500.0, Detail=8.0); nt.links.new(v, fib.inputs['Vector'])
    fc = hexc(P['fique']); fdk = [x * 0.45 for x in fc[:3]] + [1]; flt = [min(1, x * 1.18) for x in fc[:3]] + [1]
    fcol = mixc(nt, math_(nt, 'MULTIPLY', fib.outputs['Fac'], 0.7), mixc(nt, hgt, fdk, fc), flt)
    # top band
    cmb = nt.nodes.new('ShaderNodeCombineXYZ'); nt.links.new(math_(nt, 'DIVIDE', at.outputs['Fac'], 0.0085 * 2048 / 320), cmb.inputs['X'])
    nt.links.new(math_(nt, 'DIVIDE', math_(nt, 'SUBTRACT', z, zl1), 0.0085), cmb.inputs['Y'])
    band = img(nt, T('faja'), cmb.outputs['Vector'])
    isband = math_(nt, 'GREATER_THAN', z, zl1); isrub = math_(nt, 'LESS_THAN', z, zl0)
    col = mixc(nt, isrub, mixc(nt, isband, fcol, band), hexc(P['rubber']))
    nt.links.new(col, b.inputs['Base Color'])
    nt.links.new(math_(nt, 'ADD', 0.62, math_(nt, 'MULTIPLY', isrub, 0.12)), b.inputs['Roughness'])
    bh = math_(nt, 'MULTIPLY', math_(nt, 'ADD', hgt, math_(nt, 'MULTIPLY', fib.outputs['Fac'], 0.25)), math_(nt, 'SUBTRACT', 1, math_(nt, 'MAXIMUM', isrub, isband)))
    bp = N(nt, 'ShaderNodeBump', Strength=1.0, Distance=0.0022); nt.links.new(bh, bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    SO = m
    lin = plain('lining' + tag, P['lining'], 0.85); lin.node_tree.nodes['Principled BSDF'].inputs['Sheen Weight'].default_value = 0.5
    return {'Upper': UP, 'Strap': FJ, 'Outsole': SO, 'Footbed': lin, 'Piping': gold('piping' + tag, 0.32),
            'Heel Tab': gold('tab' + tag, 0.22, hammer=0.35), 'Stitching': plain('thread' + tag, P['thread'], 0.55)}

# ---------------------------------------------------------------- geometry
F = r3.File3dm.Read(os.path.join(HERE, '..', 'loafer', 'r.3dm'))
RAW = []
for o in F.Objects:
    lay = F.Layers[o.Attributes.LayerIndex].FullPath
    if '::' not in lay: continue
    side, part = lay.split('::'); side = side[-1]
    V = []; Nn = []; Fc = []
    for f in o.Geometry.Faces:
        me = f.GetMesh(r3.MeshType.Any)
        if not me: continue
        base = len(V)
        for i in range(len(me.Vertices)): p = me.Vertices[i]; V.append((p.X * 0.001, p.Y * 0.001, p.Z * 0.001))
        if len(me.Normals) == len(me.Vertices):
            for i in range(len(me.Normals)): n = me.Normals[i]; Nn.append((n.X, n.Y, n.Z))
        else: Nn += [(0, 0, 1)] * len(me.Vertices)
        for i in range(len(me.Faces)):
            q = me.Faces[i]; Fc.append((base + q[0], base + q[1], base + q[2]) if q[2] == q[3] else (base + q[0], base + q[1], base + q[2], base + q[3]))
    V = np.array(V)
    if part == 'Outsole': V[:, 2] = np.where(V[:, 2] > 0.0045, V[:, 2] + LIFT, V[:, 2])
    else: V[:, 2] += LIFT
    RAW.append((side, part, V, Nn, Fc))

def arc_attr(V):
    """arc length (m) along the sole outline for every vertex -> braid + band mapping"""
    c = V[:, :2].mean(0); ang = np.arctan2(V[:, 1] - c[1], V[:, 0] - c[0])
    k = 720; bins = np.linspace(-np.pi, np.pi, k + 1); out = np.zeros((k, 2))
    for i in range(k):
        sel = (ang >= bins[i]) & (ang < bins[i + 1])
        if sel.any():
            d = np.linalg.norm(V[sel, :2] - c, axis=1); out[i] = V[sel][d.argmax(), :2]
        else: out[i] = out[i - 1]
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.vstack([out, out[:1]]), axis=0), axis=1))]
    idx = np.clip(np.digitize(ang, bins) - 1, 0, k - 1)
    t = (ang - bins[idx]) / (bins[1] - bins[0])
    return seg[idx] + t * (seg[idx + 1] - seg[idx])

def build(cw, tag, xform=Matrix.Identity(4), sides='LR', explode=None):
    root = bpy.data.objects.new('root' + tag + sides, None); bpy.context.collection.objects.link(root)
    cx = {'R': 0.07, 'L': -0.07, 'LR': 0.0}[sides]; root.matrix_world = xform @ Matrix.Translation((-cx, -0.145, 0))
    obs = []
    for side, part, V, Nn, Fc in RAW:
        if side not in sides: continue
        mesh = bpy.data.meshes.new(f'{side}{part}{tag}'); mesh.from_pydata(V.tolist(), [], Fc); mesh.update()
        mesh.polygons.foreach_set('use_smooth', [True] * len(mesh.polygons))
        try: mesh.normals_split_custom_set_from_vertices(Nn)
        except Exception: pass
        if part == 'Outsole':
            a = mesh.attributes.new('s', 'FLOAT', 'POINT'); a.data.foreach_set('value', arc_attr(V).astype(np.float32))
        mk = 'L' if side == 'L' else 'R'
        ob = bpy.data.objects.new(mesh.name, mesh); bpy.context.collection.objects.link(ob); ob.parent = root
        mesh.materials.append(MS[(cw, tag + mk)][part])
        if explode: ob.location.z += explode.get(part, 0)
        obs.append((side, part, ob))
    return root, obs

mats_side = {}; MS = {}
def prep(cw, tag):
    for mk in 'LR': MS[(cw, tag + mk)] = mats(cw, tag + mk)

# ---------------------------------------------------------------- scene helpers
def cam(loc, look, lens=60, fstop=None, ortho=None):
    c = bpy.data.cameras.new('cam'); c.lens = lens; c.clip_start = 0.005
    if ortho: c.type = 'ORTHO'; c.ortho_scale = ortho
    ob = bpy.data.objects.new('cam', c); bpy.context.collection.objects.link(ob); ob.location = loc
    ob.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); sc.camera = ob
    if fstop: c.dof.use_dof = True; c.dof.focus_distance = (Vector(look) - Vector(loc)).length; c.dof.aperture_fstop = fstop
    return ob

def area(name, loc, look, size, power, col='#FFFFFF', sy=None):
    l = bpy.data.lights.new(name, 'AREA'); l.size = size; l.energy = power; l.color = hexc(col)[:3]
    if sy: l.shape = 'RECTANGLE'; l.size_y = sy
    ob = bpy.data.objects.new(name, l); bpy.context.collection.objects.link(ob); ob.location = loc
    ob.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()

def sweep(col, rough=0.9, back=0.75, R=0.5):
    verts = []; faces = []; W = 8
    prof = [(y, 0.0) for y in np.linspace(-4, back, 6)] + [(back + R * math.sin(a), R - R * math.cos(a)) for a in np.linspace(0, math.pi / 2, 24)][1:] + [(back + R, z) for z in np.linspace(R, 4, 4)][1:]
    for (y, z) in prof: verts += [(-W, y, z), (W, y, z)]
    for i in range(len(prof) - 1): a = 2 * i; faces.append((a, a + 1, a + 3, a + 2))
    me = bpy.data.meshes.new('sweep'); me.from_pydata(verts, [], faces); me.update(); me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    ob = bpy.data.objects.new('sweep', me); bpy.context.collection.objects.link(ob); me.materials.append(plain('sweep', col, rough)); return ob

def plinth(col, loc, size, h, rough=0.4):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(loc[0], loc[1], loc[2] - h / 2)); ob = bpy.context.active_object
    ob.scale = (size[0], size[1], h); ob.data.materials.append(plain('plinth', col, rough))
    bev = ob.modifiers.new('b', 'BEVEL'); bev.width = 0.004; bev.segments = 4; return ob

def world(col, s):
    w = bpy.data.worlds.new('w'); w.use_nodes = True; bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = hexc(col); bg.inputs['Strength'].default_value = s; sc.world = w

def T(tx=0, ty=0, tz=0, rz=0):
    return Matrix.Translation((tx, ty, tz)) @ Matrix.Rotation(math.radians(rz), 4, 'Z')

sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SPP; sc.cycles.use_denoising = True
sc.render.resolution_x = RX; sc.render.resolution_y = RY
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
P = PAL[CW]
# shoe R: x 0.013..0.127, heel y=0, toe y=0.29, top ~0.123 after lift. centre R ~ (0.07, 0.145)
if SHOT == 'hero':
    prep(CW, 'a')
    world(P['stage'], 0.06); sweep(P['stage'], 0.7).rotation_euler = (0, 0, math.pi * 0.62)
    build(CW, 'a', T(0.05, -0.04, 0, 30), 'R')
    build(CW, 'a', T(-0.1, -0.01, 0, 22), 'L')
    area('key', (0.35, -0.55, 0.7), (0, 0.0, 0.05), 0.7, 22, '#FFF1E0')
    area('fill', (0.8, -0.4, 0.25), (0, 0.0, 0.05), 1.0, 7, '#E9EEFF')
    area('rim', (-0.6, -0.3, 0.45), (0, 0.0, 0.06), 0.4, 40, '#FFC890', sy=0.9)
    area('top', (0, 0.0, 1.2), (0, 0.0, 0), 0.8, 6)
    cam((0.62, 0.42, 0.3), (-0.03, -0.01, 0.045), 58, fstop=11)
elif SHOT == 'side':
    prep(CW, 'a'); world(P['bg'], 0.15); sweep(P['bg'], 0.85)
    build(CW, 'a', T(0, 0, 0, -90), 'R')
    area('key', (-0.5, -0.6, 0.6), (0, 0, 0.05), 0.9, 22, '#FFF1E0'); area('fill', (0.6, -0.5, 0.2), (0, 0, 0.05), 1.0, 7, '#E9EEFF')
    area('rim', (0.1, 0.7, 0.4), (0, 0, 0.06), 0.6, 18, '#FFD9B0')
    cam((0.0, -0.82, 0.075), (0.0, 0.0, 0.058), 70)
elif SHOT == 'top':
    prep(CW, 'a'); world(P['bg'], 0.2); sweep(P['bg'], 0.85)
    build(CW, 'a', T(0, 0, 0, 0), 'LR')
    area('key', (-0.4, -0.5, 1.0), (0, 0, 0), 1.0, 24, '#FFF1E0'); area('fill', (0.5, 0.4, 0.8), (0, 0, 0), 1.0, 8)
    cam((0, 0, 0.9), (0, 0, 0), 60); bpy.data.objects['cam'].rotation_euler = (0, 0, math.radians(90))
elif SHOT in ('toe', 'sole', 'strap', 'heel'):
    prep(CW, 'a'); world(P['bg'], 0.2); sweep(P['bg'], 0.85)
    build(CW, 'a', T(0, 0, 0, 0), 'R')
    area('key', (-0.4, -0.45, 0.55), (0, 0, 0.06), 0.5, 12, '#FFF1E0'); area('fill', (0.5, -0.1, 0.25), (0, 0, 0.05), 0.6, 4, '#E9EEFF')
    area('rim', (0.3, 0.5, 0.35), (0, 0, 0.06), 0.4, 10, '#FFD9B0'); area('top', (0, 0, 0.9), (0, 0, 0), 0.8, 4)
    if SHOT == 'toe':   cam((0.12, 0.33, 0.14), (0.0, 0.1, 0.06), 85, fstop=4)
    if SHOT == 'sole':  cam((0.21, -0.02, 0.035), (0.055, 0.02, 0.022), 95, fstop=5)
    if SHOT == 'strap': cam((0.3, 0.2, 0.25), (0.0, 0.02, 0.085), 85, fstop=6)
    if SHOT == 'heel':  cam((0.13, -0.3, 0.12), (0.0, -0.11, 0.05), 90, fstop=4.5)
elif SHOT == 'exploded':
    prep(CW, 'a'); world(P['bg'], 0.18); sweep(P['bg'], 0.85)
    ex = {'Outsole': 0.0, 'Footbed': 0.05, 'Upper': 0.1, 'Heel Tab': 0.115, 'Piping': 0.14, 'Strap': 0.185, 'Stitching': 0.21}
    build(CW, 'a', T(0, 0, 0, -60), 'R', explode=ex)
    area('key', (-0.6, -0.6, 0.9), (0, 0, 0.12), 0.9, 26, '#FFF1E0'); area('fill', (0.7, -0.3, 0.4), (0, 0, 0.1), 1.0, 8, '#E9EEFF')
    area('rim', (0.2, 0.7, 0.5), (0, 0, 0.12), 0.5, 18, '#FFD9B0')
    cam((0.8, -0.56, 0.42), (0.0, 0.0, 0.125), 50)
elif SHOT == 'trio':     # three colourways, one stage
    world('#1A1816', 0.1); sweep('#24211E', 0.6)
    for i, cw in enumerate(('paramo', 'manta', 'tumbaga')):
        prep(cw, 't%d' % i); build(cw, 't%d' % i, T((i - 1) * 0.13, -(i - 1) * 0.2, 0, -70), 'R')
    area('key', (-0.7, -0.6, 0.8), (0, 0, 0.05), 1.0, 34, '#FFF1E0'); area('fill', (0.8, -0.4, 0.3), (0, 0, 0.05), 1.2, 9, '#E9EEFF')
    area('rimO', (0.4, 0.9, 0.35), (0, 0, 0.06), 0.8, 9, '#FF5A1F', sy=0.3)
    cam((0.25, -1.1, 0.55), (0.0, 0.0, 0.03), 58, fstop=11)

os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True); sc.render.filepath = os.path.abspath(OUT)
bpy.ops.render.render(write_still=True); print('DONE', OUT)
