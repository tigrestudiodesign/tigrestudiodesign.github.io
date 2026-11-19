"""HESTIA - soft-textile domestic humanoid (original design, Agility-class proportions). Tigre Studio 2026.
usage: python3 hestia.py <shot> <out.png> [res_x] [res_y] [spp]
shots: hero, back, living, knee, hand, exploded, zones
"""
import sys, math, os
import numpy as np
import bpy
from mathutils import Vector

SHOT = sys.argv[1]; OUT = sys.argv[2]
RX = int(sys.argv[3]) if len(sys.argv) > 3 else 1200
RY = int(sys.argv[4]) if len(sys.argv) > 4 else 1500
SPP = int(sys.argv[5]) if len(sys.argv) > 5 else 48

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def hexc(h, a=1.0):
    h = h.lstrip('#'); c = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [a]

# ---------------------------------------------------------------- palette (Warm Minimalist)
PALS = {
 'warm':     dict(oat='#B9A787', oat2='#C8B898', birch='#958E82', moss='#5E6555', terra='#B65A3A', champ='#C9B48C', weave='#2A2B2B', shell='#EDEBE6', frame='#3A3B3D'),
 'graphite': dict(oat='#3B3C3E', oat2='#4A4C4E', birch='#2C2D2F', moss='#1D1E20', terra='#B65A3A', champ='#C9B48C', weave='#151617', shell='#2A2B2D', frame='#3A3B3D'),
 'sand':     dict(oat='#E4DCCB', oat2='#EEE8DC', birch='#CEC6B8', moss='#A9A194', terra='#B65A3A', champ='#C9B48C', weave='#2A2B2B', shell='#F2EFE9', frame='#3A3B3D'),
}
P = dict(PALS[os.environ.get('PAL', 'warm')])
ZONE = dict(oat='#E8DCC4', birch='#9FA3A8', moss='#4F8A5B', terra='#E2552C', champ='#D9B44A', weave='#1E2B44', shell='#FFFFFF', frame='#555555')

# ---------------------------------------------------------------- materials
def node_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    return m, nt, b

def coords(nt, scale):
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); return mp.outputs['Vector']

def knit_mat(name, col, col2=None, rough=0.9, sheen=0.45, bump=0.35, gauge=170):
    m, nt, b = node_mat(name)
    v = coords(nt, 1.0)
    noise = nt.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 900; noise.inputs['Detail'].default_value = 4
    nt.links.new(v, noise.inputs['Vector'])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    mix.inputs[6].default_value = hexc(col); mix.inputs[7].default_value = hexc(col2 or col)
    nt.links.new(noise.outputs['Fac'], mix.inputs['Factor'])
    hz = nt.nodes.new('ShaderNodeTexNoise'); hz.inputs['Scale'].default_value = 5200; hz.inputs['Detail'].default_value = 2; nt.links.new(v, hz.inputs['Vector'])
    hr = nt.nodes.new('ShaderNodeMapRange'); hr.inputs['From Min'].default_value = 0.6; hr.inputs['From Max'].default_value = 0.75; hr.inputs['To Max'].default_value = 0.35
    nt.links.new(hz.outputs['Fac'], hr.inputs['Value'])
    hm = nt.nodes.new('ShaderNodeMix'); hm.data_type = 'RGBA'; nt.links.new(hr.outputs[0], hm.inputs['Factor']); nt.links.new(mix.outputs[2], hm.inputs[6])
    hm.inputs[7].default_value = [min(1, x * 1.6 + 0.03) for x in hexc(col)[:3]] + [1]
    nt.links.new(hm.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    b.inputs['Sheen Weight'].default_value = sheen; b.inputs['Sheen Roughness'].default_value = 0.5; b.inputs['Sheen Tint'].default_value = hexc(col2 or col)
    # wales (vertical) x courses (horizontal): a fine jersey grid
    w1 = nt.nodes.new('ShaderNodeTexWave'); w1.wave_type = 'BANDS'; w1.bands_direction = 'X'; w1.inputs['Scale'].default_value = gauge
    w2 = nt.nodes.new('ShaderNodeTexWave'); w2.wave_type = 'BANDS'; w2.bands_direction = 'Z'; w2.inputs['Scale'].default_value = gauge * 1.35
    w1.inputs['Distortion'].default_value = 1.5; w2.inputs['Distortion'].default_value = 0.6
    nt.links.new(v, w1.inputs['Vector']); nt.links.new(v, w2.inputs['Vector'])
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    nt.links.new(w1.outputs['Fac'], mul.inputs[0]); nt.links.new(w2.outputs['Fac'], mul.inputs[1])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump; bp.inputs['Distance'].default_value = 0.002
    nt.links.new(mul.outputs[0], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m

def dots_mat(name, col, hole, k=900, thr=0.55, rough=0.8, sheen=0.4, axes='YZ'):
    """perforated (vent) or raised-dot (grip) surfaces: a grid of dots on two object axes"""
    m, nt, b = node_mat(name)
    v = coords(nt, 1.0)
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(v, sep.inputs[0])
    a1, a2 = axes[0], axes[1]
    s = []
    for ax in (a1, a2):
        mm = nt.nodes.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; mm.inputs[1].default_value = k
        nt.links.new(sep.outputs[ax], mm.inputs[0])
        sn = nt.nodes.new('ShaderNodeMath'); sn.operation = 'SINE'; nt.links.new(mm.outputs[0], sn.inputs[0]); s.append(sn)
    pr = nt.nodes.new('ShaderNodeMath'); pr.operation = 'MULTIPLY'
    nt.links.new(s[0].outputs[0], pr.inputs[0]); nt.links.new(s[1].outputs[0], pr.inputs[1])
    gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = thr
    nt.links.new(pr.outputs[0], gt.inputs[0])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    mix.inputs[6].default_value = hexc(col); mix.inputs[7].default_value = hexc(hole)
    nt.links.new(gt.outputs[0], mix.inputs['Factor']); nt.links.new(mix.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough; b.inputs['Sheen Weight'].default_value = sheen
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.6; bp.inputs['Distance'].default_value = 0.0015
    nt.links.new(gt.outputs[0], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m

def plain(name, col, rough=0.5, metal=0.0, sheen=0.0, coat=0.0, aniso=0.0):
    m, nt, b = node_mat(name)
    b.inputs['Base Color'].default_value = hexc(col); b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal; b.inputs['Sheen Weight'].default_value = sheen
    b.inputs['Coat Weight'].default_value = coat
    if aniso: b.inputs['Anisotropic'].default_value = aniso
    return m

KLIB = '/home/claude/tigrestudiodesign.github.io/img/kn__lib_%s.webp'
def imgknit(name, col, stitch, tile=0.07, bump=0.7, rough=0.85, sheen=0.45):
    """knit structure from the Knit Nodes library: the rendered swatch drives tone and relief"""
    m, nt, b = node_mat(name)
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1 / tile,) * 3
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(KLIB % stitch, check_existing=True)
    t.image.colorspace_settings.name = 'Non-Color'; t.projection = 'BOX'; t.projection_blend = 0.3; t.extension = 'MIRROR'
    nt.links.new(mp.outputs['Vector'], t.inputs['Vector'])
    bw = nt.nodes.new('ShaderNodeRGBToBW'); nt.links.new(t.outputs['Color'], bw.inputs['Color'])
    rr = nt.nodes.new('ShaderNodeMapRange'); rr.inputs['From Min'].default_value = 0.08; rr.inputs['From Max'].default_value = 0.75
    rr.inputs['To Min'].default_value = 0.3; rr.inputs['To Max'].default_value = 1.0; nt.links.new(bw.outputs['Val'], rr.inputs['Value'])
    mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1.0
    mul.inputs[6].default_value = hexc(col)
    cc = nt.nodes.new('ShaderNodeCombineColor'); [nt.links.new(rr.outputs[0], cc.inputs[i]) for i in range(3)]
    nt.links.new(cc.outputs[0], mul.inputs[7]); nt.links.new(mul.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough; b.inputs['Sheen Weight'].default_value = sheen; b.inputs['Sheen Roughness'].default_value = 0.5
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump; bp.inputs['Distance'].default_value = 0.0025
    nt.links.new(bw.outputs['Val'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m

def lt(h, k=1.12):
    h = h.lstrip('#'); return '#' + ''.join('%02X' % min(255, int(int(h[i:i+2], 16) * k + 6)) for i in (0, 2, 4))

def flat(name, col):
    m, nt, b = node_mat(name)
    b.inputs['Base Color'].default_value = hexc(col); b.inputs['Roughness'].default_value = 0.9
    return m

if SHOT == 'zones':
    M = {k: flat(k, ZONE[k]) for k in ZONE}
else:
    def mkM():
        M = dict(
            oat=knit_mat('oatmeal knit', P['oat'], P['oat2']),
            birch=knit_mat('birch knit', P['birch'], lt(P['birch'])),
            moss=knit_mat('slate-moss rib', P['moss'], lt(P['moss']), bump=0.5),
            vent=dots_mat('vent spacer mesh', P['birch'], '#2E2C29', k=820, thr=0.5),
            terra=dots_mat('terracotta silicone grip', P['terra'], '#9A4A2F', k=1050, thr=0.62, rough=0.55, sheen=0.2, axes='XZ'),
            champ=plain('champagne anodised', '#B49C74', rough=0.4, metal=1.0, aniso=0.3),
            weave=knit_mat('sensor weave', P['weave'], '#353636', rough=0.45, sheen=0.9, bump=0.15, gauge=320),
            shell=plain('PC-ABS shell', P['shell'], rough=0.35, coat=0.3),
            frame=plain('frame', P['frame'], rough=0.45, metal=0.6))
        M['vent_z'] = M['vent']; M['gusset'] = M['vent']
        if os.environ.get('KNITMAP'):
            # Knit Nodes selection applied to HESTIA zones (see knit_select.py)
            M.update(oat=imgknit('stockinette jersey', P['oat2'], 'stockinette'), moss=imgknit('rib 1x1', lt(P['moss'], 1.05), 'rib1', tile=0.06, bump=0.9),
                     birch=imgknit('slip-stitch float', P['birch'], 'slip', tile=0.075), vent=imgknit('lace eyelet vent', P['birch'], 'lace', tile=0.06, bump=0.9),
                     terra=imgknit('seed grip', P['terra'], 'seed', tile=0.045, bump=1.0, rough=0.6), weave=imgknit('lace sensor weave', P['weave'], 'lace', tile=0.03, rough=0.5, sheen=0.9),
                     gusset=imgknit('lace gusset', lt(P['moss'], 1.25), 'lace', tile=0.05, bump=0.9))
            M['vent_z'] = M['vent']
        return M
    M = mkM()


def mi(key):
    k = key
    if SHOT == 'zones':
        k = {'vent': 'birch', 'vent_z': 'birch'}.get(key, key)
    return M[k]

# ---------------------------------------------------------------- geometry
def catmull(pts, n):
    pts = [np.array(p, float) for p in pts]
    P_ = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    segs = len(pts) - 1
    for i in range(segs):
        p0, p1, p2, p3 = P_[i], P_[i + 1], P_[i + 2], P_[i + 3]
        m = max(2, n // segs)
        for j in range(m):
            t = j / m
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(pts[-1])
    return np.array(out)

def build(name, verts, faces, fmat, mats):
    me = bpy.data.meshes.new(name); me.from_pydata(verts.tolist() if hasattr(verts, 'tolist') else verts, [], faces); me.update()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    for m in mats: me.materials.append(m)
    me.polygons.foreach_set('material_index', fmat)
    me.polygons.foreach_set('use_smooth', [True] * len(faces))
    return ob

def tube(name, ctrl, prof, zones, ring=40, n=160, ref=(1, 0, 0), sx=None, expo=2.0, rib=(0.012, 0.09), rule=None):
    """sweep a superellipse section along a smoothed path.
    prof(t)->r (or (rx,ry)); zones: list of (t0,t1,matkey,ribbed)."""
    path = catmull(ctrl, n)
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(seg)]); L = s[-1]; T = s / L
    tang = np.gradient(path, axis=0); tang /= np.linalg.norm(tang, axis=1)[:, None]
    r0 = np.array(ref, float); N = []
    nn = r0 - tang[0] * np.dot(r0, tang[0]); nn /= np.linalg.norm(nn)
    for i in range(len(path)):
        nn = nn - tang[i] * np.dot(nn, tang[i]); nn /= np.linalg.norm(nn); N.append(nn.copy())
    N = np.array(N); B = np.cross(tang, N)
    keys = []
    for z in zones:
        if z[2] not in keys: keys.append(z[2])
    def zone_at(t):
        for z in zones:
            if z[0] <= t <= z[1]: return z
        return zones[-1]
    verts = []; ringz = []
    ang = np.linspace(0, 2 * np.pi, ring, endpoint=False)
    ca, sa = np.cos(ang), np.sin(ang)
    se = lambda c: np.sign(c) * np.abs(c) ** (2.0 / expo)
    for i, p in enumerate(path):
        t = T[i]; r = prof(t)
        rx, ry = (r, r) if np.isscalar(r) else r
        z = zone_at(t)
        if z[3]:
            k = abs(math.sin(math.pi * s[i] / rib[0])) ** 0.7
            f = 1 + rib[1] * (k - 0.5)
            rx *= f; ry *= f
        for c_, s_ in zip(se(ca), se(sa)):
            verts.append(p + N[i] * rx * c_ + B[i] * ry * s_)
        ringz.append(keys.index(z[2]))
    verts = np.array(verts); faces = []; fm = []
    R = len(path)
    for i in range(R - 1):
        for j in range(ring):
            a = i * ring + j; b = i * ring + (j + 1) % ring
            faces.append((a, b, b + ring, a + ring)); fm.append(ringz[i])
    # caps
    c0 = len(verts); verts = np.vstack([verts, path[0], path[-1]])
    for j in range(ring):
        faces.append((c0, (j + 1) % ring, j)); fm.append(ringz[0])
        a = (R - 1) * ring
        faces.append((c0 + 1, a + j, a + (j + 1) % ring)); fm.append(ringz[-1])
    mats = [mi(k) for k in keys]
    if rule:
        extra = []
        for fi, f in enumerate(faces):
            vs = verts[list(f)]; c = vs.mean(0)
            nrm = np.cross(vs[1] - vs[0], vs[2] - vs[0]); ln = np.linalg.norm(nrm)
            nrm = nrm / ln if ln > 1e-12 else np.array([0, 0, 1.0])
            k = rule(c, nrm)
            if k:
                if k not in keys: keys.append(k); mats.append(mi(k))
                fm[fi] = keys.index(k)
    return build(name, verts, faces, fm, mats)

def rounded(t, e=0.12, lo=0.0):
    """pill ends: 0 at t=0/1, 1 in the middle"""
    if t < e: return lo + (1 - lo) * math.sqrt(max(0, 1 - (1 - t / e) ** 2))
    if t > 1 - e: return lo + (1 - lo) * math.sqrt(max(0, 1 - (1 - (1 - t) / e) ** 2))
    return 1.0

def lerpk(t, keys):
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            u = (t - t0) / (t1 - t0); u = u * u * (3 - 2 * u); return v0 + (v1 - v0) * u
    return keys[-1][1]

def torus(name, center, axis, R, r, mat, n=64, m=16):
    verts = []; faces = []
    ax = np.array(axis, float); ax /= np.linalg.norm(ax)
    u = np.cross(ax, [0, 0, 1] if abs(ax[2]) < 0.9 else [1, 0, 0]); u /= np.linalg.norm(u); v = np.cross(ax, u)
    for i in range(n):
        a = 2 * math.pi * i / n; d = u * math.cos(a) + v * math.sin(a)
        for j in range(m):
            b = 2 * math.pi * j / m
            verts.append(np.array(center) + d * (R + r * math.cos(b)) + ax * r * math.sin(b))
    for i in range(n):
        for j in range(m):
            a = i * m + j; b_ = ((i + 1) % n) * m + j; c = ((i + 1) % n) * m + (j + 1) % m; d = i * m + (j + 1) % m
            faces.append((a, b_, c, d))
    return build(name, np.array(verts), faces, [0] * len(faces), [mi(mat)])

# ---------------------------------------------------------------- the robot
POSE = 'carry' if SHOT == 'living' else 'stand'
def robot(off=(0, 0, 0), explode=0.0):
    o = np.array(off, float); parts = []
    # torso: wide soft superellipse, vents on the flanks, terracotta sternum tab
    def tprof(t):
        w = lerpk(t, [(0, 0.15), (0.25, 0.165), (0.62, 0.205), (0.86, 0.2), (1, 0.16)])
        d = lerpk(t, [(0, 0.115), (0.4, 0.13), (0.75, 0.14), (1, 0.12)])
        k = rounded(t, 0.14, 0.35); return (w * (0.6 + 0.4 * k) if t > 0.8 or t < 0.2 else w, d * k)
    def trule(c, n):
        z = c[2] - o[2]
        if abs(n[0]) > 0.72 and 1.04 < z < 1.36: return 'vent'
        if n[1] > 0.6 and 1.06 < z < 1.30 and abs(c[0] - o[0]) < 0.11: return 'vent_z'
        return None
    parts.append(tube('torso', [o + (0, 0, 0.99), o + (0, 0, 1.2), o + (0, 0, 1.45)], tprof, [(0, 1, 'oat', True)],
                      ring=64, n=140, ref=(1, 0, 0), expo=2.6, rib=(0.075, 0.035), rule=trule))
    # sternum touch tab: a soft terracotta pill, the one place to tap or guide
    parts.append(tube('tab', [o + (-0.06, -0.143, 1.29), o + (0.06, -0.143, 1.29)], lambda t: (0.02 * rounded(t, 0.35, 0.3), 0.008 * rounded(t, 0.35, 0.3)),
                      [(0, 1, 'terra', False)], ring=32, n=40, ref=(0, 0, 1), expo=2.2))
    # waist flex: rib band between torso and pelvis
    parts.append(tube('waist', [o + (0, 0, 0.93), o + (0, 0, 1.02)], lambda t: (0.148, 0.105), [(0, 1, 'moss', True)], ring=64, n=40, expo=2.6, rib=(0.011, 0.12)))
    # pelvis
    parts.append(tube('pelvis', [o + (0, 0, 0.83), o + (0, 0, 0.96)], lambda t: (0.165 * (0.75 + 0.25 * rounded(t, 0.3)), 0.115 * rounded(t, 0.28, 0.4)),
                      [(0, 1, 'birch', False)], ring=64, n=40, expo=2.6))
    # neck + head
    parts.append(tube('neck', [o + (0, 0.0, 1.43), o + (0, 0.0, 1.54)], lambda t: 0.052, [(0, 1, 'moss', True)], ring=40, n=30, rib=(0.01, 0.14)))
    parts.append(torus('collar', o + (0, 0, 1.455), (0, 0, 1), 0.058, 0.009, 'champ'))
    def hrule(c, n):
        z = c[2] - o[2]
        if n[2] > 0.82: return 'weave'                       # LiDAR crown under a transparent weave
        if n[1] < -0.35 and 1.615 < z < 1.675: return 'weave'  # depth-camera band
        return None
    parts.append(tube('head', [o + (0, 0.005, 1.52), o + (0, 0, 1.63), o + (0, 0.005, 1.74)],
                      lambda t: (0.108 * rounded(t, 0.32, 0.35), 0.098 * rounded(t, 0.36, 0.3)), [(0, 1, 'oat', False)],
                      ring=64, n=80, expo=2.3, rule=hrule))
    # two warm 'eyes' glowing through the sensor weave: the face you talk to
    if SHOT != 'zones':
        em = bpy.data.materials.get('eye') or bpy.data.materials.new('eye')
        em.use_nodes = True; bb = em.node_tree.nodes['Principled BSDF']
        bb.inputs['Base Color'].default_value = hexc('#FFC48A'); bb.inputs['Emission Color'].default_value = hexc('#FFB070'); bb.inputs['Emission Strength'].default_value = 6
        import bmesh
        vm = bpy.data.materials.get('visor')
        if not vm:
            vm, vnt, vb = node_mat('visor'); vb.inputs['Base Color'].default_value = hexc('#07080A'); vb.inputs['Roughness'].default_value = 0.05
            vb.inputs['Coat Weight'].default_value = 1.0; vb.inputs['Coat Roughness'].default_value = 0.01; vb.inputs['Specular IOR Level'].default_value = 0.7
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=256, ring_count=128, location=tuple(o + (0, 0.004, 1.632)))
        vz = bpy.context.object; vz.scale = (0.1125, 0.1035, 0.112); bpy.ops.object.transform_apply(scale=True)
        bm = bmesh.new(); bm.from_mesh(vz.data)
        cz = o[2] + 1.632
        dels = [f for f in bm.faces if not (f.calc_center_median().y + vz.location.y < o[1] - 0.03 and (abs(f.calc_center_median().x) / 0.094) ** 4 + (abs(f.calc_center_median().z - 0.008) / 0.04) ** 4 < 1)]
        bmesh.ops.delete(bm, geom=dels, context='FACES'); bm.to_mesh(vz.data); bm.free()
        sol = vz.modifiers.new('s', 'SOLIDIFY'); sol.thickness = 0.003; sol.offset = 1
        vz.data.materials.append(vm); bpy.ops.object.shade_smooth(); parts.append(vz)
        for ex in (-0.036, 0.036):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=tuple(o + (ex, -0.1075, 1.642)))
            ey = bpy.context.object; ey.scale = (0.017, 0.002, 0.0032); ey.data.materials.append(em); bpy.ops.object.shade_smooth(); parts.append(ey)
    # legs: reverse-knee (Agility-class) with ribbed hip, knee and ankle sleeves
    for sgn in (-1, 1):
        x = 0.105 * sgn; e = np.array((sgn * explode, 0, 0))
        # humanoid leg: hip, full thigh, defined knee slightly forward, calf, slim ankle
        ctrl = [o + e + (x * 0.8, 0.0, 0.9), o + e + (x * 0.98, 0.0, 0.82), o + e + (x * 1.02, -0.012, 0.66), o + e + (x * 1.03, -0.02, 0.49),
                o + e + (x * 1.03, -0.005, 0.32), o + e + (x * 1.03, 0.005, 0.15), o + e + (x * 1.03, 0.0, 0.085)]
        prof = lambda t: lerpk(t, [(0, 0.074), (0.1, 0.08), (0.3, 0.074), (0.44, 0.06), (0.5, 0.058), (0.56, 0.06), (0.66, 0.063), (0.8, 0.05), (0.92, 0.038), (1, 0.034)]) * rounded(t, 0.03, 0.6)
        zones = [(0, 0.1, 'moss', True), (0.1, 0.42, 'oat', False), (0.42, 0.56, 'moss', True), (0.56, 0.9, 'birch', False), (0.9, 1, 'moss', True)]
        parts.append(tube('leg%d' % sgn, ctrl, prof, zones, ring=40, n=200, rib=(0.0115, 0.13)))
        # foot: soft rounded pad, champagne heel tab
        f0 = o + e + (x * 1.03, 0.06, 0.035); f1 = o + e + (x * 1.03, -0.17, 0.035)
        parts.append(tube('foot%d' % sgn, [f0, (f0 + f1) / 2, f1], lambda t: (0.05 * rounded(t, 0.25, 0.4), 0.035 * rounded(t, 0.2, 0.5)),
                          [(0, 1, 'moss', False)], ring=40, n=40, ref=(1, 0, 0), expo=2.4,
                          rule=lambda c, n: 'champ' if (n[1] > 0.7 and c[2] > 0.03) else None))
    # arms
    for sgn in (-1, 1):
        x = 0.235 * sgn; e = np.array((sgn * explode * 1.6, 0, 0))
        if POSE == 'carry':
            ctrl = [o + e + (x * 0.8, 0.0, 1.38), o + e + (x, 0.0, 1.33), o + e + (x * 1.08, 0.02, 1.12), o + e + (x * 0.82, -0.2, 1.08), o + e + (x * 0.7, -0.32, 1.075)]
        else:
            ctrl = [o + e + (x * 0.8, 0.0, 1.38), o + e + (x, 0.0, 1.33), o + e + (x * 1.1, 0.025, 1.08), o + e + (x * 1.08, -0.06, 0.88), o + e + (x * 1.06, -0.08, 0.83)]
        prof = lambda t: lerpk(t, [(0, 0.062), (0.15, 0.06), (0.4, 0.05), (0.5, 0.048), (0.75, 0.044), (1, 0.038)]) * rounded(t, 0.03, 0.6)
        zones = [(0, 0.2, 'moss', True), (0.2, 0.43, 'oat', False), (0.43, 0.58, 'moss', True), (0.58, 0.64, 'oat', False), (0.64, 0.92, 'terra', False), (0.92, 0.96, 'oat', False), (0.96, 1, 'champ', False)]
        def arule(c, n, sgn=sgn, o=o):
            # forearm grip zone: the inner and under side of the forearm is terracotta silicone knit
            z = c[2] - o[2]
            if POSE == 'carry':
                if z < 1.11 and c[1] - o[1] < -0.06 and n[2] < 0.3: return 'terra'
            elif 0.86 < z < 1.02 and (n[0] * -sgn > 0.2 or n[1] < -0.5): return 'terra'
            if os.environ.get('KNITMAP') and POSE == 'stand':
                if z > 1.24 and n[0] * -sgn > 0.3: return 'gusset'          # shoulder: pleat stack has no room inside, open lace gusset
                if 1.02 < z < 1.15 and n[1] < -0.45: return 'gusset'      # inner elbow: same rule, smaller
            return None
        parts.append(tube('arm%d' % sgn, ctrl, prof, zones, ring=40, n=200, rib=(0.0105, 0.13)))
        # hand: soft mitten paddle, champagne back, terracotta palm, separate thumb
        w = np.array(ctrl[-1], float); d = np.array(ctrl[-1], float) - np.array(ctrl[-2], float); d /= np.linalg.norm(d)
        h1 = w + d * 0.15
        side = np.array((1, 0, 0)) if POSE == 'stand' else np.array((0, 0, 1))
        parts.append(tube('hand%d' % sgn, [w - d * 0.01, w + d * 0.07, h1], lambda t: (0.047 * rounded(t, 0.25, 0.5), 0.022 * rounded(t, 0.2, 0.5)),
                          [(0, 1, 'champ', False)], ring=40, n=40, ref=tuple(side if POSE == 'stand' else (1, 0, 0)), expo=2.4,
                          rule=lambda c, n, sgn=sgn: 'terra' if ((POSE == 'stand' and n[0] * -sgn > 0.45) or (POSE == 'carry' and n[2] > 0.5)) else None))
        th0 = w + d * 0.035 + (np.array((-sgn * 0.035, -0.02, 0)) if POSE == 'stand' else np.array((-sgn * 0.04, 0, 0.0)))
        parts.append(tube('thumb%d' % sgn, [th0, th0 + d * 0.05 + np.array((-sgn * 0.01, -0.01, 0))], lambda t: 0.014 * rounded(t, 0.3, 0.5),
                          [(0, 1, 'terra', False)], ring=24, n=20))
    # back carry handle: champagne loop (a grip zone that tells people where to hold)
    hb = [o + (-0.07, 0.125, 1.31), o + (-0.06, 0.165, 1.37), o + (0.06, 0.165, 1.37), o + (0.07, 0.125, 1.31)]
    parts.append(tube('handle', hb, lambda t: 0.011, [(0, 1, 'champ', False)], ring=20, n=60))
    return parts

# ---------------------------------------------------------------- scenes
def cam(loc, look, lens=60, shift=(0, 0)):
    c = bpy.data.cameras.new('cam'); c.lens = lens; c.shift_x, c.shift_y = shift
    ob = bpy.data.objects.new('cam', c); bpy.context.collection.objects.link(ob)
    ob.location = loc; d = Vector(look) - Vector(loc); ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler(); sc.camera = ob
    return ob

def area(name, loc, look, size, power, col='#FFFFFF', shape='RECTANGLE', sy=None):
    l = bpy.data.lights.new(name, 'AREA'); l.size = size; l.energy = power; l.color = hexc(col)[:3]
    if sy: l.shape = 'RECTANGLE'; l.size_y = sy
    ob = bpy.data.objects.new(name, l); bpy.context.collection.objects.link(ob); ob.location = loc
    ob.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return ob

def world(col, strength=1.0):
    w = bpy.data.worlds.new('w'); w.use_nodes = True; bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = hexc(col); bg.inputs['Strength'].default_value = strength; sc.world = w

def box(name, c, size, mat, bevel=0.02, seg=4):
    bpy.ops.mesh.primitive_cube_add(location=c); ob = bpy.context.object; ob.name = name
    ob.scale = (size[0] / 2, size[1] / 2, size[2] / 2); bpy.ops.object.transform_apply(scale=True)
    if bevel:
        m = ob.modifiers.new('b', 'BEVEL'); m.width = bevel; m.segments = seg; m.limit_method = 'NONE'
    ob.data.materials.append(mat); bpy.ops.object.shade_smooth(); return ob

def cyc(col):
    """seamless studio sweep"""
    verts = []; faces = []; W = 8; nseg = 24; R = 1.2
    prof = [(y, 0.0) for y in np.linspace(-6, 1.5, 8)] + \
           [(1.5 + R * math.sin(a), R - R * math.cos(a)) for a in np.linspace(0, math.pi / 2, nseg)][1:] + [(1.5 + R, z) for z in np.linspace(R, 6, 6)][1:]
    for (y, z) in prof:
        verts += [(-W, y, z), (W, y, z)]
    for i in range(len(prof) - 1):
        a = 2 * i; faces.append((a, a + 1, a + 3, a + 2))
    return build('sweep', np.array(verts, float), faces, [0] * len(faces), [plain('sweep', col, rough=0.9)])

sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SPP; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 6; sc.render.resolution_x = RX; sc.render.resolution_y = RY; sc.render.film_transparent = False
sc.view_settings.view_transform = 'AgX'; sc.view_settings.exposure = -0.35; sc.view_settings.look = 'AgX - Medium High Contrast' if SHOT != 'zones' else 'None'
if SHOT == 'zones': sc.view_settings.view_transform = 'Standard'

if SHOT in ('hero', 'back', 'knee', 'hand', 'zones'):
    _parts = robot()
    if SHOT == 'back':
        for ob in _parts:
            l = ob.location; ob.location = (-l[0], -l[1], l[2]); ob.rotation_euler[2] += math.pi
    cyc('#CFC6B8' if SHOT != 'zones' else '#F4F1EC'); world('#E9E4DA', 0.22 if SHOT != 'zones' else 1.0)
    if SHOT in ('hero', 'back'):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.42, depth=0.03, vertices=128, location=(0, -0.04, 0.015)); dk = bpy.context.object
        dk.data.materials.append(plain('dock oak', '#B98D60', 0.45, coat=0.2)); bv = dk.modifiers.new('b', 'BEVEL'); bv.width = 0.008; bv.segments = 4; bpy.ops.object.shade_smooth()
        torus('dock_ring', (0, -0.04, 0.031), (0, 0, 1), 0.36, 0.006, 'champ')
    if SHOT == 'zones':
        area('k', (0, -4, 3), (0, 0, 1), 6, 300)
    else:
        area('key', (-2.2, -2.4, 2.6), (0, 0, 1.0), 2.2, 520, '#FFF1DE')
        area('fill', (2.6, -1.6, 1.2), (0, 0, 1.0), 3.0, 160, '#F4F6FF')
        area('rim', (1.4, 2.4, 2.4), (0, 0, 1.2), 1.6, 380, '#FFE6C8')
    if SHOT == 'hero':  cam((2.45, -2.95, 1.12), (0.0, 0, 0.9), 58)
    if SHOT == 'back':  cam((-1.6, -3.3, 1.3), (0, 0, 0.95), 58)
    if SHOT == 'knee':  cam((0.95, -0.2, 0.62), (0.11, 0.07, 0.52), 60)
    if SHOT == 'hand':  cam((0.7, -0.55, 1.05), (0.25, -0.05, 0.93), 70)
    if SHOT == 'zones': cam((0.0, -5.2, 0.9), (0.0, 0, 0.9), 95)

if SHOT == 'living':
    RO = np.array((0.15, 0.05, 0.0))
    robot(off=tuple(RO))
    world('#CFDCEA', 0.1)
    sc.cycles.max_bounces = 8
    # ---- floor: oak planks
    m, nt, b = node_mat('oak boards')
    v = coords(nt, 1.0); br = nt.nodes.new('ShaderNodeTexBrick'); br.offset = 0.5; br.squash = 1.0
    br.inputs['Color1'].default_value = hexc('#B8875A'); br.inputs['Color2'].default_value = hexc('#C79A6C'); br.inputs['Mortar'].default_value = hexc('#7E5C3E')
    br.inputs['Scale'].default_value = 1.0; br.inputs['Mortar Size'].default_value = 0.003; br.inputs['Brick Width'].default_value = 1.6; br.inputs['Row Height'].default_value = 0.18
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3; nz.inputs['Detail'].default_value = 10
    mp2 = nt.nodes.new('ShaderNodeMapping'); mp2.inputs['Scale'].default_value = (14, 0.7, 1); nt.links.new(v, mp2.inputs['Vector']); nt.links.new(mp2.outputs['Vector'], nz.inputs['Vector'])
    nt.links.new(v, br.inputs['Vector'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 0.3
    nt.links.new(br.outputs['Color'], mx.inputs[6]); nt.links.new(nz.outputs['Color'], mx.inputs[7]); nt.links.new(mx.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.38; b.inputs['Coat Weight'].default_value = 0.15
    oakm = m
    box('floor', (0, 0, -0.01), (12, 12, 0.02), m, 0)
    wall = plain('wall', '#ECE6DC', rough=0.95)
    base_m = plain('skirting', '#E4DDD1', rough=0.7)
    # ---- back wall (y=1.75) with a tall window at x -1.6..-0.2, z 0.35..2.45
    WX0, WX1, WZ0, WZ1, WY = -1.75, -0.25, 0.4, 2.45, 1.75
    box('bw_left', (-4.0 + (WX0 + 4.0) / 2 - 0.0, WY, 1.5), (WX0 + 4.0, 0.12, 3.0), wall, 0)
    box('bw_right', ((WX1 + 4.0) / 2, WY, 1.5), (4.0 - WX1, 0.12, 3.0), wall, 0)
    box('bw_top', ((WX0 + WX1) / 2, WY, (WZ1 + 3.0) / 2), (WX1 - WX0, 0.12, 3.0 - WZ1), wall, 0)
    box('bw_bot', ((WX0 + WX1) / 2, WY, WZ0 / 2), (WX1 - WX0, 0.12, WZ0), wall, 0)
    box('sill', ((WX0 + WX1) / 2, WY - 0.08, WZ0), (WX1 - WX0 + 0.08, 0.2, 0.03), plain('sill', '#E8E2D8', 0.5), 0.004)
    fr = plain('window frame', '#2F2E2C', rough=0.4, metal=0.3)
    for x in (WX0, (WX0 + WX1) / 2, WX1): box('mull', (x, WY, (WZ0 + WZ1) / 2), (0.035, 0.06, WZ1 - WZ0), fr, 0.002)
    for z in (WZ0, 1.55, WZ1): box('tran', ((WX0 + WX1) / 2, WY, z), (WX1 - WX0, 0.06, 0.035), fr, 0.002)
    # outside: soft sky + a blurred hedge line so the window reads as a window
    skym, nt2, b2 = node_mat('outside')
    tc = nt2.nodes.new('ShaderNodeTexCoord'); g = nt2.nodes.new('ShaderNodeSeparateXYZ'); nt2.links.new(tc.outputs['Generated'], g.inputs[0])
    cr = nt2.nodes.new('ShaderNodeValToRGB'); nt2.links.new(g.outputs['Z'], cr.inputs['Fac'])
    cr.color_ramp.elements[0].position = 0.0; cr.color_ramp.elements[0].color = hexc('#7E8F6A')
    cr.color_ramp.elements[1].position = 1.0; cr.color_ramp.elements[1].color = hexc('#EAF1F7')
    e1 = cr.color_ramp.elements.new(0.32); e1.color = hexc('#9AA884'); e2 = cr.color_ramp.elements.new(0.42); e2.color = hexc('#DCE7F0')
    em = nt2.nodes.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = 1.4; nt2.links.new(cr.outputs['Color'], em.inputs['Color'])
    nt2.links.new(em.outputs[0], nt2.nodes['Material Output'].inputs['Surface'])
    ob_out = box('outside', (-1.0, 9.5, 1.6), (14.0, 0.05, 9.0), skym, 0); ob_out.visible_shadow = False; ob_out.hide_render = bool(os.environ.get('NOOUT'))
    box('ceiling', (0, 0, 3.05), (8, 8, 0.1), wall, 0)
    box('lw', (-2.75, 0, 1.5), (0.12, 7.0, 3.0), wall, 0); box('skirting_l', (-2.68, 0, 0.05), (0.02, 7.0, 0.1), base_m, 0)
    box('skirting_b', (1.9, WY - 0.07, 0.05), (4.2, 0.02, 0.1), base_m, 0)
    # ---- right side wall (x=2.3) with art + floating oak shelf
    box('sw', (2.35, 0, 1.5), (0.12, 7.0, 3.0), wall, 0)
    box('skirting_s', (2.28, 0, 0.05), (0.02, 7.0, 0.1), base_m, 0)
    box('frame_art', (2.27, 0.35, 1.55), (0.03, 0.62, 0.82), plain('art frame', '#2F2E2C', 0.5), 0.004)
    box('canvas', (2.255, 0.35, 1.55), (0.01, 0.54, 0.74), plain('canvas', '#EFE8DB', 0.9), 0)
    box('art_sun', (2.248, 0.35, 1.7), (0.004, 0.26, 0.26), plain('ochre', '#C98F4E', 0.9), 0)
    box('art_hill', (2.248, 0.35, 1.38), (0.004, 0.46, 0.14), plain('moss', '#69705F', 0.9), 0)
    # ---- sofa: low boucle, two seat cushions, two back cushions, oak legs
    bou = knit_mat('boucle', '#E8DFD0', '#DCD1BF', bump=1.2, gauge=70)
    SX, SY = -0.35, 1.18
    box('sofa_base', (SX, SY, 0.24), (2.1, 0.92, 0.22), bou, 0.07, 6)
    for dx in (-0.5, 0.5):
        box('seat', (SX + dx, SY - 0.05, 0.42), (0.98, 0.78, 0.16), bou, 0.08, 6)
        box('backc', (SX + dx, SY + 0.32, 0.66), (0.98, 0.24, 0.42), bou, 0.11, 6)
    for dx in (-1.08, 1.08): box('arm', (SX + dx, SY, 0.43), (0.2, 0.92, 0.5), bou, 0.09, 6)
    for dx in (-0.95, 0.95):
        for dy in (-0.38, 0.38):
            bpy.ops.mesh.primitive_cylinder_add(radius=0.022, depth=0.13, location=(SX + dx, SY + dy, 0.065)); bpy.context.object.data.materials.append(oakm)
    box('cushion', (SX - 0.62, SY + 0.12, 0.66), (0.42, 0.13, 0.4), knit_mat('cushion moss', '#5E6555', '#6B7362', bump=0.6), 0.07, 5)
    box('throw', (SX + 0.65, SY - 0.1, 0.515), (0.55, 0.62, 0.03), knit_mat('throw terra', '#B65A3A', '#A9512F', bump=0.8, gauge=60), 0.012, 3)
    # ---- rug + round oak coffee table + book + ceramic
    box('rug', (0.05, 0.25, 0.006), (2.8, 2.0, 0.012), knit_mat('wool rug', '#E2D8C6', '#D2C6B1', bump=0.9, gauge=45), 0.008)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.42, depth=0.04, vertices=96, location=(-0.85, 0.3, 0.38)); bpy.context.object.data.materials.append(oakm)
    bv = bpy.context.object.modifiers.new('b', 'BEVEL'); bv.width = 0.01; bv.segments = 3; bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=0.36, vertices=96, location=(-0.85, 0.3, 0.18)); bpy.context.object.data.materials.append(oakm)
    box('book', (-0.95, 0.28, 0.415), (0.24, 0.17, 0.03), plain('book', '#2E3B36', 0.7), 0.004)
    box('book2', (-0.94, 0.27, 0.44), (0.2, 0.15, 0.02), plain('book2', '#D7CBB4', 0.7), 0.003)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07, location=(-0.68, 0.38, 0.45)); vo = bpy.context.object; vo.scale = (1, 1, 1.25)
    vo.data.materials.append(plain('ceramic', '#B65A3A', 0.45, coat=0.4)); bpy.ops.object.shade_smooth()
    # ---- fiddle-leaf plant in a tapered stone pot (by the window)
    PX, PY = -2.05, 1.25
    bpy.ops.mesh.primitive_cone_add(radius1=0.15, radius2=0.2, depth=0.38, vertices=64, location=(PX, PY, 0.19)); pot = bpy.context.object
    pot.data.materials.append(plain('stone pot', '#CFC6B6', 0.85)); bpy.ops.object.shade_smooth()
    stem_m = plain('stem', '#5A4632', 0.7); leaf = plain('leaf', '#3F5B3A', 0.45, sheen=0.2, coat=0.3)
    import random; random.seed(7)
    for k in range(3):
        sx, sy = PX + 0.04 * (k - 1), PY + 0.03 * ((k * 7) % 3 - 1); h = 1.15 + 0.22 * k
        bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=h, location=(sx, sy, 0.38 + h / 2)); bpy.context.object.data.materials.append(stem_m)
        for i in range(9):
            z = 0.75 + (h - 0.4) * i / 8 + 0.05; a = i * 2.4 + k
            bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=24, ring_count=12, location=(sx + 0.12 * math.cos(a), sy + 0.12 * math.sin(a), z))
            lf = bpy.context.object; sz = 0.11 + 0.03 * random.random()
            lf.scale = (0.075, sz, 0.012); lf.rotation_euler = (math.radians(25 + 20 * random.random()), math.radians(10 * random.random()), a - math.pi / 2)
            lf.data.materials.append(leaf); bpy.ops.object.shade_smooth()
    # ---- floor lamp: oak tripod + linen shade (warm, dim)
    LX, LY = 1.45, 1.38
    for k in range(3):
        a = k * 2.094 + 0.3
        bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=1.45, location=(LX + 0.1 * math.cos(a), LY + 0.1 * math.sin(a), 0.72))
        lg = bpy.context.object; lg.rotation_euler = (math.radians(4) * math.sin(a), -math.radians(4) * math.cos(a), 0); lg.data.materials.append(oakm)
    shm, nt3, b3 = node_mat('linen shade'); b3.inputs['Base Color'].default_value = hexc('#F3EBDD'); b3.inputs['Roughness'].default_value = 0.9
    b3.inputs['Transmission Weight'].default_value = 0.6
    bpy.ops.mesh.primitive_cone_add(radius1=0.24, radius2=0.18, depth=0.32, vertices=64, end_fill_type='NOTHING', location=(LX, LY, 1.55))
    sh = bpy.context.object; sh.data.materials.append(shm); sol = sh.modifiers.new('s', 'SOLIDIFY'); sol.thickness = 0.004
    pl = bpy.data.lights.new('bulb', 'POINT'); pl.energy = 25; pl.color = hexc('#FFC98A')[:3]; pl.shadow_soft_size = 0.05
    po = bpy.data.objects.new('bulb', pl); bpy.context.collection.objects.link(po); po.location = (LX, LY, 1.52)
    # ---- woven laundry basket next to the robot
    bpy.ops.mesh.primitive_cylinder_add(radius=0.24, depth=0.36, vertices=64, location=(0.85, 0.1, 0.18), end_fill_type='TRIFAN'); bk = bpy.context.object
    bk.data.materials.append(knit_mat('woven basket', '#B89A6E', '#A2865E', bump=1.4, gauge=40)); bpy.ops.object.shade_smooth()
    box('basket_towel', (0.85, 0.1, 0.37), (0.36, 0.3, 0.06), knit_mat('towel_b', '#F1ECE3', '#E6DFD3', bump=0.8, gauge=110), 0.025, 4)
    # ---- folded towels resting on both forearms (carry pose)
    for i, col in enumerate(['#F2EDE4', '#C9B9A0', '#E3D6C2']):
        box('towel%d' % i, (RO[0], RO[1] - 0.26, 1.125 + i * 0.034), (0.44, 0.3, 0.032), knit_mat('towel%d' % i, col, col, bump=0.8, gauge=120), 0.014, 3)
    # ---- light: low afternoon sun through the window, sky fill from it, soft room bounce
    d_ = Vector((0.38, -0.78, -0.5)).normalized()
    sp = bpy.data.lights.new('sun', 'SPOT'); sp.energy = 16000; sp.spot_size = math.radians(32); sp.spot_blend = 0.15; sp.shadow_soft_size = 0.04
    sp.color = hexc('#FFD8A8')[:3]
    so = bpy.data.objects.new('sun', sp); bpy.context.collection.objects.link(so)
    so.location = Vector((-1.0, 1.75, 1.45)) - d_ * 5.0; so.rotation_euler = d_.to_track_quat('-Z', 'Y').to_euler()
    area('window_fill', (-1.0, 1.62, 1.42), (-0.3, -1.0, 1.0), 1.5, 110, '#E4EEF8', sy=2.0)
    area('room', (1.6, -2.6, 2.4), (0, 0.5, 1.0), 3.0, 75, '#FFF2E2')
    sc.view_settings.exposure = 0.1
    c_ = cam((1.8, -2.25, 1.28), (-0.2, 0.6, 0.95), 30)
    c_.data.dof.use_dof = True; c_.data.dof.focus_distance = (Vector((1.8, -2.25, 1.28)) - Vector(tuple(RO + (0, 0, 1.1)))).length; c_.data.dof.aperture_fstop = 4.0

if SHOT == 'exploded':
    # layer stack of the chest panel: frame -> snap-fit shell -> spacer mesh -> knit skin
    world('#E9E4DA', 0.35); cyc('#D9D2C6')
    area('key', (-2.2, -2.4, 2.6), (0, 0, 1.0), 2.2, 520, '#FFF1DE'); area('fill', (2.6, -1.6, 1.2), (0, 0, 1.0), 3.0, 160, '#F4F6FF')
    area('rim', (1.4, 2.4, 2.4), (0, 0, 1.2), 1.6, 380, '#FFE6C8')
    def tp(t):
        w = lerpk(t, [(0, 0.15), (0.25, 0.165), (0.62, 0.205), (0.86, 0.2), (1, 0.16)])
        d = lerpk(t, [(0, 0.115), (0.4, 0.13), (0.75, 0.14), (1, 0.12)])
        k = rounded(t, 0.14, 0.35); return (w * (0.6 + 0.4 * k) if t > 0.8 or t < 0.2 else w, d * k)
    layers = [('frame', 0.86, 'frame'), ('shell', 0.94, 'shell'), ('mesh', 0.985, 'vent'), ('skin', 1.0, 'oat')]
    for i, (nm, sc_, mat) in enumerate(layers):
        dy = -0.12 * i; dx = -1.05 + 0.34 * i
        def front_only(c, n, dy=dy):
            return None
        ob = tube(nm, [(dx, dy, 0.99), (dx, dy, 1.2), (dx, dy, 1.45)], lambda t, sc_=sc_: tuple(np.array(tp(t)) * sc_), [(0, 1, mat, False)], ring=64, n=90, expo=2.6)
        # keep the front half only: delete back faces
        me = ob.data
        import bmesh
        bm = bmesh.new(); bm.from_mesh(me)
        dels = [f for f in bm.faces if f.calc_center_median().y > dy + 0.005]
        bmesh.ops.delete(bm, geom=dels, context='FACES'); bm.to_mesh(me); bm.free()
        sol = ob.modifiers.new('s', 'SOLIDIFY'); sol.thickness = 0.006 if nm != 'mesh' else 0.01
        if nm == 'frame':
            ob.data.materials.clear(); ob.data.materials.append(M['frame'])
        if nm == 'shell':
            for sx in (-0.17, 0.17):
                for sz in (1.07, 1.2, 1.33):
                    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.012, location=(dx + sx, dy - 0.11, sz)); bpy.context.object.data.materials.append(M['champ'])
    robot(off=(0.75, 0.35, 0))
    cam((0.6, -3.6, 1.55), (-0.15, -0.1, 1.05), 40)

# ---------------------------------------------------------------- v2: launch-event stage (dark, reflective, rim-lit)
def launch_stage(dock=True):
    sc.view_settings.exposure = -0.1
    world('#050506', 0.0)
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0)); fl = bpy.context.object
    fm, fnt, fb = node_mat('stage floor'); fb.inputs['Base Color'].default_value = hexc('#0D0D0F'); fb.inputs['Roughness'].default_value = 0.32
    fb.inputs['Coat Weight'].default_value = 0.6; fb.inputs['Coat Roughness'].default_value = 0.08; fl.data.materials.append(fm)
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 4.0, 0)); wl = bpy.context.object; wl.rotation_euler = (math.radians(90), 0, 0)
    wl.data.materials.append(plain('stage wall', '#121214', 0.9))
    area('wallglow', (0, 2.6, 0.3), (0, 4.0, 1.6), 2.5, 260, '#F2C79A')
    area('top', (0, -0.3, 3.2), (0, 0, 1.0), 0.5, 320, '#FFFFFF', sy=2.4)
    area('rimL', (-1.5, 1.1, 1.4), (0, 0, 1.0), 0.25, 380, '#FFD9A8', sy=2.6)
    area('rimR', (1.5, 1.1, 1.4), (0, 0, 1.0), 0.25, 380, '#BFD4FF', sy=2.6)
    area('key', (-1.8, -2.6, 1.6), (0, 0, 1.0), 1.4, 70, '#FFF4E6')
    if dock:
        for (x0) in DOCKS:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.42, depth=0.03, vertices=160, location=(x0, -0.04, 0.015)); dk = bpy.context.object
            dk.data.materials.append(plain('dock glass', '#0A0A0B', 0.06, coat=1.0)); bv = dk.modifiers.new('b', 'BEVEL'); bv.width = 0.008; bv.segments = 5; bpy.ops.object.shade_smooth()
            rm = bpy.data.materials.get('dock light') or plain('dock light', '#F2C79A', 0.3)
            rb = rm.node_tree.nodes['Principled BSDF']; rb.inputs['Emission Color'].default_value = hexc('#F2C79A'); rb.inputs['Emission Strength'].default_value = 7
            bpy.ops.mesh.primitive_torus_add(major_radius=0.40, minor_radius=0.0035, location=(x0, -0.04, 0.031), major_segments=160, minor_segments=12)
            bpy.context.object.data.materials.append(rm)

if SHOT == 'exploded2':
    # chest skin stack pulled straight out of the torso along its own axis: frame -> snap-fit shell -> spacer mesh -> knit skin
    if os.environ.get('STAGE', 'dark') == 'dark':
        DOCKS = [0.0]; launch_stage(dock=True)
        area('layerkey', (-1.6, -2.2, 2.0), (0, -0.75, 1.2), 1.6, float(os.environ.get('LK', '160')), '#FFF2E2')
        area('layerrim', (1.2, -0.6, 1.9), (0, -0.8, 1.2), 0.3, 220, '#FFD9A8', sy=1.6)
        area('layertop', (0, -1.3, 2.9), (0, -1.3, 1.2), 2.4, float(os.environ.get('LT', '120')), '#FFFFFF', sy=0.6)
    else:
        world('#E9E4DA', 0.14); sw = cyc('#CFC6B8'); sw.rotation_euler[2] = math.radians(float(os.environ.get('SWR', '-71'))); sw.location = (0.6, -0.2, 0)
        area('key', (-2.4, -2.0, 3.0), (0, -0.5, 1.0), 2.8, 700, '#FFF0DC')
        area('fill', (2.4, -2.6, 1.0), (0, -0.5, 1.0), 3.0, 90, '#EEF2FF')
        area('rim', (1.2, 2.2, 2.6), (0, -0.3, 1.2), 1.4, 520, '#FFE2C0')
    def tp(t):
        w = lerpk(t, [(0, 0.15), (0.25, 0.165), (0.62, 0.205), (0.86, 0.2), (1, 0.16)])
        d = lerpk(t, [(0, 0.115), (0.4, 0.13), (0.75, 0.14), (1, 0.12)])
        k = rounded(t, 0.14, 0.35); return (w * (0.6 + 0.4 * k) if t > 0.8 or t < 0.2 else w, d * k)
    import bmesh
    GAP = float(os.environ.get('GAP', '0.21')); Y0 = float(os.environ.get('Y0', '-0.36'))
    layers = [('frame', 0.9, 'frame', False), ('shell', 0.95, 'shell', False), ('mesh', 0.985, 'vent', False), ('skin', 1.0, 'oat', True)]
    for i, (nm, sc_, mat, rib) in enumerate(layers):
        dy = Y0 - GAP * i
        dz = float(os.environ.get('RISE', '0.05')) * i
        ob = tube(nm, [(0, dy, 0.99 + dz), (0, dy, 1.2 + dz), (0, dy, 1.45 + dz)], lambda t, sc_=sc_: tuple(np.array(tp(t)) * sc_), [(0, 1, mat, rib)],
                  ring=(28 if nm == 'frame' else 72), n=(14 if nm == 'frame' else 120), expo=2.6, rib=(0.075, 0.035))
        me = ob.data; bm = bmesh.new(); bm.from_mesh(me)
        cy = dy - float(os.environ.get('CUT', '0.035'))   # clean straight cut edge: bisect, then drop the back half
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector((0, cy, 0)), plane_no=Vector((0, 1, 0)), clear_outer=True)
        ROT = math.radians(float(os.environ.get('ROT', '-30')) * (0.55 + 0.15 * i))
        from mathutils import Matrix
        bmesh.ops.rotate(bm, verts=bm.verts, cent=Vector((0, dy, 1.2 + dz)), matrix=Matrix.Rotation(ROT, 3, 'Z'))
        bm.to_mesh(me); bm.free()
        if nm == 'frame':   # structural cage: open lattice, not a solid plate
            wf = ob.modifiers.new('w', 'WIREFRAME'); wf.thickness = 0.009; wf.use_even_offset = True; wf.use_boundary = True
            ss = ob.modifiers.new('sub', 'SUBSURF'); ss.levels = 1; ss.render_levels = 2
        else:
            sol = ob.modifiers.new('s', 'SOLIDIFY'); sol.thickness = {'shell': 0.005, 'mesh': 0.012, 'skin': 0.006}[nm]; sol.offset = 1
        bv = ob.modifiers.new('b', 'BEVEL'); bv.width = 0.0015; bv.segments = 2; bv.limit_method = 'ANGLE'
        if nm == 'frame':
            ob.data.materials.clear(); ob.data.materials.append(M['frame'])
        if nm == 'shell':
            for sx in (-0.095, 0.095):
                for sz in (1.07, 1.2, 1.33):
                    px, py = sx, -0.121; ca, sa = math.cos(ROT), math.sin(ROT)
                    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.009, location=(px * ca - py * sa, dy + px * sa + py * ca, sz + dz)); bpy.context.object.data.materials.append(M['champ']); bpy.ops.object.shade_smooth()
    # micro-type tags: number + layer name in hot orange, facing the camera
    if os.environ.get('TAGS', '1') == '1':
        CAMLOC = Vector(tuple(float(v) for v in os.environ.get('CAM', '-2.35,-2.75,1.42').split(',')))
        fnt = bpy.data.fonts.load('/home/claude/hestia/JBM700.ttf')
        om = plain('tag', '#FF5A1F', 0.5); ob_ = om.node_tree.nodes['Principled BSDF']
        ob_.inputs['Emission Color'].default_value = hexc('#FF5A1F'); ob_.inputs['Emission Strength'].default_value = 2.2
        wm = plain('tagw', '#F2EEE6', 0.5); wb_ = wm.node_tree.nodes['Principled BSDF']
        wb_.inputs['Emission Color'].default_value = hexc('#F2EEE6'); wb_.inputs['Emission Strength'].default_value = 1.2
        names = ['FRAME', 'SNAP SHELL', 'SPACER MESH', 'KNIT SKIN']
        subs = ['ALUMINIUM CAGE', 'PC-ABS · SNAP-FIT', 'BREATHABLE AIR GAP', 'OATMEAL KNIT · WASHABLE']
        for i, nm in enumerate(names):
            dy = Y0 - GAP * i; p0 = Vector((0, dy, 1.56 + float(os.environ.get('RISE', '0.05')) * i))
            for txt, mat, sz, oz in (('%02d  %s' % (i + 1, nm), om, 0.034, 0.0), (subs[i], wm, 0.022, -0.04)):
                cu = bpy.data.curves.new('t', 'FONT'); cu.body = txt; cu.font = fnt; cu.size = sz; cu.align_x = 'CENTER'
                t = bpy.data.objects.new('tag', cu); bpy.context.collection.objects.link(t); t.data.materials.append(mat)
                t.location = p0 + Vector((0, 0, oz))
                d = CAMLOC - t.location; d.z = 0
                t.rotation_euler = (math.radians(90), 0, math.atan2(d.y, d.x) + math.radians(90))
            bpy.ops.mesh.primitive_cylinder_add(radius=0.0012, depth=0.07, vertices=8, location=(p0.x, p0.y, p0.z - 0.095)); bpy.context.object.data.materials.append(om)
    robot()
    c = cam(tuple(float(v) for v in os.environ.get('CAM', '-2.35,-2.75,1.42').split(',')), tuple(float(v) for v in os.environ.get('LOOK', '0.05,-0.58,1.1').split(',')), float(os.environ.get('LENS', '48')))
    c.data.dof.use_dof = True; c.data.dof.focus_distance = (Vector(c.location) - Vector((0, -1.1, 1.2))).length; c.data.dof.aperture_fstop = float(os.environ.get('FST', '11'))
    sc.view_settings.exposure = float(os.environ.get('EXPO', '-0.3'))

DOCKS = [0.0]
if SHOT in ('reveal', 'hero2', 'face', 'grip', 'kneeK', 'shoulderK', 'torsoK'):
    robot(); launch_stage(dock=SHOT != 'face')
    if SHOT == 'reveal': cam((0.0, -4.3, 0.7), (0.0, 0, 0.92), 42)
    if SHOT == 'hero2':  cam((2.1, -3.2, 0.62), (0.05, 0, 0.9), 38)
    if SHOT == 'face':
        c = cam((0.5, -1.0, 1.7), (0.0, -0.03, 1.56), 75); c.data.dof.use_dof = True; c.data.dof.focus_distance = 1.1; c.data.dof.aperture_fstop = 2.8
    def dofcam(loc, look, lens, f=3.2):
        c = cam(loc, look, lens); c.data.dof.use_dof = True; c.data.dof.focus_distance = (Vector(look) - Vector(loc)).length; c.data.dof.aperture_fstop = f
    if SHOT == 'kneeK':     dofcam((0.62, -0.78, 0.6), (0.1, -0.02, 0.5), 75)
    if SHOT == 'shoulderK': dofcam((0.02, -0.78, 1.36), (0.2, -0.01, 1.29), 70)
    if SHOT == 'torsoK':    dofcam((0.35, -0.85, 1.25), (0.0, -0.1, 1.18), 85)
    if SHOT == 'grip':
        c = cam((0.75, -0.62, 1.0), (0.25, -0.06, 0.94), 80); c.data.dof.use_dof = True; c.data.dof.focus_distance = 0.86; c.data.dof.aperture_fstop = 3.2
if SHOT == 'trio':
    DOCKS = [-0.95, 0.0, 0.95]
    for x0, pal in zip(DOCKS, ('sand', 'warm', 'graphite')):
        P.clear(); P.update(PALS[pal]); M = mkM(); robot(off=(x0, 0, 0))
    launch_stage(); cam((0.0, -4.9, 0.85), (0.0, 0, 0.9), 42)

if SHOT == 'hero':
    pass
if os.environ.get('SUNONLY'):
    for o in list(sc.objects):
        if o.type=='LIGHT' and o.name!='sun': bpy.data.objects.remove(o)
    sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=0
    bpy.data.objects['outside'].hide_render=True
if os.environ.get('RAYDBG'):
    print([(o.name,o.data.type,o.data.energy,tuple(round(x,2) for x in o.location)) for o in sc.objects if o.type=='LIGHT'])
    dg = bpy.context.evaluated_depsgraph_get(); sunob = bpy.data.objects.get('sun')
    dl = sunob.matrix_world.to_quaternion() @ Vector((0, 0, -1)); print('sun dir', dl)
    for pt in [(0.3, -0.5, 0.01), (0.2, 0.0, 1.0), (-0.5, 0.5, 0.01)]:
        hit = sc.ray_cast(dg, Vector(pt) + Vector((0,0,0.02)), -dl)
        print(pt, hit[0], hit[4].name if hit[0] else None)
    raise SystemExit
os.makedirs(os.path.dirname(OUT) or '.', exist_ok=True)
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print('DONE', OUT)
