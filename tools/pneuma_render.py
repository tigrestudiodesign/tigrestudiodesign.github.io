"""PNEUMA - soft textile hand for HESTIA (renders). Tigre Studio 2026.
Every finger is built from the bend model in tools/pneuma_model.py (data/pneuma.json):
constant curvature, woven layer on the palm side, power-mesh knit over a TPU bladder.
usage: python3 tools/pneuma_render.py <shot> <out.png> [res_x] [res_y] [spp]
shots: hero, open, sequence, exploded
"""
import sys, math, os, json
import numpy as np
import bpy
from mathutils import Vector

SHOT = sys.argv[1]; OUT = sys.argv[2]
RX = int(sys.argv[3]) if len(sys.argv) > 3 else 1920
RY = int(sys.argv[4]) if len(sys.argv) > 4 else 1080
SPP = int(sys.argv[5]) if len(sys.argv) > 5 else 64
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = json.load(open(f'{ROOT}/data/pneuma.json'))
K, EMAX = MOD['k'], MOD['eps_max']

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def hexc(h, a=1.0):
    h = h.lstrip('#'); c = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [a]

P = dict(oat='#B9A787', oat2='#C8B898', birch='#958E82', moss='#5E6555', terra='#B65A3A', champ='#C9B48C')

# ---------------------------------------------------------------- materials (HESTIA family, UV-mapped for bending parts)
def node_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    return m, nt, b

def uvw(nt, scale=1.0, uv=True):
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs['UV' if uv else 'Object'], mp.inputs['Vector']); return mp.outputs['Vector']

def knit_mat(name, col, col2=None, rough=0.9, sheen=0.5, bump=0.22, gauge=900, uv=True):
    """jersey wales along U (the finger), courses across V. UV is in metres, so gauge = wales per metre."""
    m, nt, b = node_mat(name)
    v = uvw(nt, 1.0, uv)
    noise = nt.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 2600; noise.inputs['Detail'].default_value = 4
    nt.links.new(v, noise.inputs['Vector'])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    mix.inputs[6].default_value = hexc(col); mix.inputs[7].default_value = hexc(col2 or col)
    nt.links.new(noise.outputs['Fac'], mix.inputs['Factor']); nt.links.new(mix.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    b.inputs['Sheen Weight'].default_value = sheen; b.inputs['Sheen Roughness'].default_value = 0.45; b.inputs['Sheen Tint'].default_value = hexc(col2 or col)
    w1 = nt.nodes.new('ShaderNodeTexWave'); w1.wave_type = 'BANDS'; w1.bands_direction = 'Y'; w1.inputs['Scale'].default_value = gauge
    w2 = nt.nodes.new('ShaderNodeTexWave'); w2.wave_type = 'BANDS'; w2.bands_direction = 'X'; w2.inputs['Scale'].default_value = gauge * 1.35
    w1.inputs['Distortion'].default_value = 1.2; w2.inputs['Distortion'].default_value = 0.6
    nt.links.new(v, w1.inputs['Vector']); nt.links.new(v, w2.inputs['Vector'])
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    nt.links.new(w1.outputs['Fac'], mul.inputs[0]); nt.links.new(w2.outputs['Fac'], mul.inputs[1])
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump; bp.inputs['Distance'].default_value = 0.0004
    nt.links.new(mul.outputs[0], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m

def rib_mat(name, col, ribs=900, uv=True):
    """slate-moss rib: deep wales along V"""
    m, nt, b = node_mat(name)
    v = uvw(nt, 1.0, uv)
    w = nt.nodes.new('ShaderNodeTexWave'); w.wave_type = 'BANDS'; w.bands_direction = 'Y' if uv else 'X'; w.inputs['Scale'].default_value = ribs
    nt.links.new(v, w.inputs['Vector'])
    b.inputs['Base Color'].default_value = hexc(col); b.inputs['Roughness'].default_value = 0.85; b.inputs['Sheen Weight'].default_value = 0.5
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.8; bp.inputs['Distance'].default_value = 0.0006
    nt.links.new(w.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m

def dots_mat(name, col, dot, k=2400, thr=0.55, rough=0.6, uv=True):
    """raised silicone dots on a grid (palm-side grip print)"""
    m, nt, b = node_mat(name)
    v = uvw(nt, 1.0, uv)
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(v, sep.inputs[0])
    s = []
    for ax in ('X', 'Y'):
        mm = nt.nodes.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; mm.inputs[1].default_value = k
        nt.links.new(sep.outputs[ax], mm.inputs[0])
        sn = nt.nodes.new('ShaderNodeMath'); sn.operation = 'SINE'; nt.links.new(mm.outputs[0], sn.inputs[0]); s.append(sn)
    pr = nt.nodes.new('ShaderNodeMath'); pr.operation = 'MULTIPLY'
    nt.links.new(s[0].outputs[0], pr.inputs[0]); nt.links.new(s[1].outputs[0], pr.inputs[1])
    gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = thr
    nt.links.new(pr.outputs[0], gt.inputs[0])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    mix.inputs[6].default_value = hexc(col); mix.inputs[7].default_value = hexc(dot)
    nt.links.new(gt.outputs[0], mix.inputs['Factor']); nt.links.new(mix.outputs[2], b.inputs['Base Color'])
    rr = nt.nodes.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value = 0.85; rr.inputs['To Max'].default_value = rough
    nt.links.new(gt.outputs[0], rr.inputs['Value']); nt.links.new(rr.outputs[0], b.inputs['Roughness'])
    b.inputs['Sheen Weight'].default_value = 0.3
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.7; bp.inputs['Distance'].default_value = 0.0005
    nt.links.new(gt.outputs[0], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m

def plain(name, col, rough=0.5, metal=0.0, sheen=0.0, coat=0.0, aniso=0.0, trans=0.0, ior=1.45, alpha=1.0):
    m, nt, b = node_mat(name)
    b.inputs['Base Color'].default_value = hexc(col); b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal; b.inputs['Sheen Weight'].default_value = sheen
    b.inputs['Coat Weight'].default_value = coat; b.inputs['Transmission Weight'].default_value = trans; b.inputs['IOR'].default_value = ior
    if aniso: b.inputs['Anisotropic'].default_value = aniso
    if alpha < 1: b.inputs['Alpha'].default_value = alpha
    return m

M = dict(
    oat=knit_mat('power-mesh knit', P['oat'], P['oat2']),
    birch=knit_mat('woven base', P['birch'], '#A39C90', rough=0.8, sheen=0.2, bump=0.25, gauge=1400),
    moss=rib_mat('slate-moss rib', P['moss']),
    terra=dots_mat('terracotta silicone dots', '#A89A86', P['terra']),
    pad=dots_mat('palm pad', P['terra'], '#8E4229', k=1900, thr=0.4, rough=0.45),
    champ=plain('champagne anodised', '#B49C74', rough=0.32, metal=1.0, aniso=0.4),
    tpu=plain('TPU bladder', '#D9B060', rough=0.2, trans=0.55, coat=0.6, ior=1.5),
    ceramic=plain('glazed ceramic', '#EEE8DE', rough=0.12, coat=1.0, sheen=0.0),
    coffee=plain('coffee', '#1E120B', rough=0.05, coat=1.0),
    tube=plain('PU tube', '#D8D4CC', rough=0.25, trans=0.6),
)

# ---------------------------------------------------------------- geometry
def build(name, verts, faces, fmat, mats, uvs=None, smooth=True):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in verts], [], faces); me.update()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    for m in mats: me.materials.append(m)
    me.polygons.foreach_set('material_index', fmat)
    me.polygons.foreach_set('use_smooth', [smooth] * len(faces))
    if uvs is not None:
        uv = me.uv_layers.new(name='UVMap')
        for poly in me.polygons:
            for li in poly.loop_indices:
                uv.data[li].uv = uvs[me.loops[li].vertex_index]
    return ob

def kappa_at(p_kpa, h_mm):
    """curvature (1/m) from the bend model"""
    N = p_kpa / 1000 * h_mm / 2
    eps = EMAX * (1 - math.exp(-N / (K * EMAX)))
    return eps / (h_mm / 1000)

def finger(name, L, w, h, kap, origin, t0, n0, wdir, p_kpa=0, ns=150, nphi=56, root_band=0.012, pad=True, part=None, hscale=1.0):
    """textile bending actuator. origin: root centre of the woven layer. t0: root tangent. n0: palm side (toward the
    centre of curvature). wdir: width axis. kap: curvature 1/m. part: None (whole), 'knit', 'bladder', 'woven', 'grip'."""
    L, w, h = L / 1000, w / 1000, h / 1000 * hscale
    t0, n0, wdir, origin = map(lambda a: np.array(a, float), (t0, n0, wdir, origin))
    eps = kap * h
    gather = 0.00025 * max(0.0, 1 - eps / EMAX)
    verts, uvs = [], []
    S = np.linspace(0, L, ns)
    phis = np.linspace(0, 2 * np.pi, nphi, endpoint=False)
    for s in S:
        if abs(kap) < 1e-6: c = origin + s * t0; n = n0
        else:
            c = origin + math.sin(kap * s) / kap * t0 + (1 - math.cos(kap * s)) / kap * n0
            n = -math.sin(kap * s) * t0 + math.cos(kap * s) * n0
        u = -n
        ws = w * (1 - 0.14 * s / L); hs = h * (1 - 0.1 * s / L)
        cap = ws * 0.5
        f = 1.0
        if s > L - cap: f = math.sqrt(max(0.0, 1 - ((s - (L - cap)) / cap) ** 2))
        f = max(f, 0.02)
        rootf = min(1.0, 0.75 + s / 0.006 * 0.25)  # pocket gathered into the root clamp
        for ph in phis:
            cs, sn = math.cos(ph), math.sin(ph)
            y = (ws / 2) * math.copysign(abs(cs) ** (2 / 4.0), cs)
            ab = 0.12 * hs
            if part == 'bladder': y *= 0.88
            if sn >= 0:
                v = ab + (hs - ab) * abs(sn) ** (2 / 2.2) * (0.86 if part == 'bladder' else 1.0)
                if part != 'bladder': v += gather * math.sin(2 * math.pi * s / 0.0055) * abs(sn) ** 2
            else:
                v = ab - ab * abs(sn) ** (2 / 7.0)
            y += 0.0009 * math.exp(-(sn / 0.12) ** 2) * math.copysign(1, cs)  # sewn edge bead
            p = c + y * f * rootf * wdir + v * f * rootf * u
            verts.append(p)
            uvs.append((s, ph / (2 * np.pi) * (2 * ws + 2 * hs)))
    faces, fm = [], []
    keys = ['oat', 'terra', 'birch', 'moss'] if part != 'bladder' else ['tpu']
    for i in range(ns - 1):
        for j in range(nphi):
            a = i * nphi + j; b = i * nphi + (j + 1) % nphi
            faces.append((a, b, b + nphi, a + nphi))
            if part == 'bladder': fm.append(0); continue
            ph = phis[j]; sn = math.sin(ph); s = S[i]
            if abs(sn) < 0.09: k = 3                       # edge binding
            elif sn > 0: k = 0                              # knit top
            elif pad and root_band < s < L - 0.006: k = 1   # grip print
            else: k = 2                                     # woven
            fm.append(k)
    # tip and root caps
    n0i = len(verts); verts.append(np.mean(verts[-nphi:], axis=0)); uvs.append((L, 0))
    for j in range(nphi):
        a = (ns - 1) * nphi + j; b = (ns - 1) * nphi + (j + 1) % nphi; faces.append((a, b, n0i)); fm.append(0 if part != 'bladder' else 0)
    r0 = len(verts); verts.append(np.mean(verts[:nphi], axis=0)); uvs.append((0, 0))
    for j in range(nphi):
        faces.append(((j + 1) % nphi, j, r0)); fm.append(3 if part != 'bladder' else 0)
    return build(name, verts, faces, fm, [M[k] for k in keys], uvs)

def ring_band(name, center, axis, r_out, length, mat, n=64, ribs=0):
    """short cylinder band (wrist, collars); axis unit vector"""
    axis = np.array(axis, float); axis /= np.linalg.norm(axis)
    a = np.cross(axis, [0, 0, 1]); a = a if np.linalg.norm(a) > 1e-3 else np.cross(axis, [0, 1, 0]); a /= np.linalg.norm(a); b = np.cross(axis, a)
    nl = 24; verts, uvs, faces = [], [], []
    for i in range(nl + 1):
        t = i / nl; x = (t - 0.5) * length
        rr = r_out * (1 + (0.035 * math.cos(t * ribs * 2 * math.pi) if ribs else 0)) * (1 - 0.04 * (2 * t - 1) ** 8)
        for j in range(n):
            ph = 2 * math.pi * j / n
            verts.append(np.array(center) + x * axis + rr * (math.cos(ph) * a + math.sin(ph) * b)); uvs.append((x, ph * r_out))
    for i in range(nl):
        for j in range(n):
            p = i * n + j; q = i * n + (j + 1) % n; faces.append((p, q, q + n, p + n))
    return build(name, verts, faces, [0] * len(faces), [mat], uvs)

def tube_path(name, pts, r, mat, n=16):
    pts = [np.array(p, float) for p in pts]; verts, faces = [], []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]); t /= np.linalg.norm(t)
        a = np.cross(t, [0, 0, 1]); a = a if np.linalg.norm(a) > 1e-3 else np.cross(t, [1, 0, 0]); a /= np.linalg.norm(a); b = np.cross(t, a)
        for j in range(n):
            ph = 2 * math.pi * j / n; verts.append(p + r * (math.cos(ph) * a + math.sin(ph) * b))
    for i in range(len(pts) - 1):
        for j in range(n):
            p = i * n + j; q = i * n + (j + 1) % n; faces.append((p, q, q + n, p + n))
    return build(name, verts, faces, [0] * len(faces), [mat])

# ---------------------------------------------------------------- hand (gripping a vertical mug: grip plane horizontal)
FING = {f['finger']: f for f in MOD['fingers']}
R_MUG = 0.040

def palm_hub(Rin, alpha, zr, thick=0.024):
    """C-shaped palm: an arc block that cups the mug; terracotta pad inside, champagne outside"""
    na, nz = 48, 2
    verts, faces, fm, uvs = [], [], [], []
    angs = np.linspace(math.pi - alpha, math.pi + alpha, na)
    prof = [(Rin, zr[0] + 0.004), (Rin, zr[1] - 0.004), (Rin + 0.004, zr[1]), (Rin + thick - 0.004, zr[1]), (Rin + thick, zr[1] - 0.004),
            (Rin + thick, zr[0] + 0.004), (Rin + thick - 0.004, zr[0]), (Rin + 0.004, zr[0])]
    for a in angs:
        for (r, z) in prof:
            verts.append((r * math.cos(a), r * math.sin(a), z)); uvs.append((a * Rin, z))
    npf = len(prof)
    for i in range(na - 1):
        for j in range(npf):
            p = i * npf + j; q = i * npf + (j + 1) % npf
            faces.append((p, q, q + npf, p + npf)); fm.append(0 if j == 0 else 1)
    for end in (0, na - 1):
        c = len(verts); verts.append(np.mean([verts[end * npf + j] for j in range(npf)], axis=0)); uvs.append((0, 0))
        for j in range(npf):
            a_, b_ = end * npf + j, end * npf + (j + 1) % npf
            faces.append((a_, b_, c) if end else (b_, a_, c)); fm.append(1)
    return build('palm', np.array(verts), faces, fm, [M['pad'], M['champ']], uvs, smooth=True)

def hand(p_kpa, wrap=True):
    """wrap=True: fingers hug the mug (curvature = 1/R). Otherwise curvature from the model at p_kpa."""
    alpha = math.radians(21)
    Rin = R_MUG + 0.0015
    palm_hub(Rin, alpha, (0.004, 0.108))
    zs = {'Index': 0.094, 'Middle': 0.0675, 'Ring': 0.041, 'Little': 0.0165}
    a0 = math.pi + alpha  # fingers leave the palm here and wrap counter-clockwise (through the front, -Y)
    for fn, z in zs.items():
        f = FING[fn]
        kap = (1 / Rin) if wrap else kappa_at(p_kpa, f['h'])
        o = (Rin * math.cos(a0), Rin * math.sin(a0), z)
        t0 = (-math.sin(a0), math.cos(a0), 0); n0 = (-math.cos(a0), -math.sin(a0), 0)
        finger(fn, f['L'], f['w'], f['h'], kap, o, t0, n0, (0, 0, 1))
    f = FING['Thumb']; a1 = math.pi - alpha
    kap = (1 / Rin) if wrap else kappa_at(p_kpa, f['h'])
    o = (Rin * math.cos(a1), Rin * math.sin(a1), 0.052)
    finger('Thumb', f['L'], f['w'], f['h'], kap, o, (math.sin(a1), -math.cos(a1), 0), (-math.cos(a1), -math.sin(a1), 0), (0, 0, 1))
    # wrist + forearm (HESTIA): champagne wrist, slate-moss rib cuff, oatmeal knit sleeve, terracotta grip band
    x0 = -(Rin + 0.024); zc = 0.052
    ring_band('wrist', (x0 - 0.012, 0, zc), (1, 0, 0), 0.03, 0.026, M['champ'])
    ring_band('cuff', (x0 - 0.04, 0, zc), (1, 0, 0), 0.034, 0.032, M['moss'], ribs=9)
    ring_band('sleeve', (x0 - 0.16, 0, zc), (1, 0, 0), 0.038, 0.21, M['oat'])
    ring_band('grip band', (x0 - 0.12, 0, zc), (1, 0, 0), 0.0385, 0.07, M['terra'])

def mug():
    # lathe profile: outer wall, rim, inner wall
    prof = [(0.0, 0.0), (R_MUG - 0.004, 0.0), (R_MUG, 0.004), (R_MUG, 0.113), (R_MUG - 0.002, 0.115), (R_MUG - 0.004, 0.113), (R_MUG - 0.004, 0.008), (0.0, 0.008)]
    n = 128; verts, faces = [], []
    for j in range(n):
        a = 2 * math.pi * j / n
        for (r, z) in prof: verts.append((r * math.cos(a), r * math.sin(a), z))
    npf = len(prof)
    for j in range(n):
        for i in range(npf - 1):
            p = j * npf + i; q = ((j + 1) % n) * npf + i; faces.append((p, q, q + 1, p + 1))
    ob = build('mug', verts, faces, [0] * len(faces), [M['ceramic']])
    bpy.ops.mesh.primitive_cylinder_add(radius=R_MUG - 0.0041, depth=0.001, vertices=96, location=(0, 0, 0.098)); bpy.context.object.data.materials.append(M['coffee'])
    bpy.ops.mesh.primitive_torus_add(major_radius=0.021, minor_radius=0.0055, location=(0.057 * math.cos(math.radians(53)), 0.057 * math.sin(math.radians(53)), 0.06), rotation=(math.radians(90), 0, math.radians(53)),
                                     major_segments=64, minor_segments=20)
    h = bpy.context.object; h.data.materials.append(M['ceramic']); bpy.ops.object.shade_smooth()
    return ob

# ---------------------------------------------------------------- stage, camera
def cam(loc, look, lens=60, fstop=None):
    c = bpy.data.cameras.new('cam'); c.lens = lens; c.clip_start = 0.01
    ob = bpy.data.objects.new('cam', c); bpy.context.collection.objects.link(ob)
    ob.location = loc; d = Vector(look) - Vector(loc); ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler(); sc.camera = ob
    if fstop: c.dof.use_dof = True; c.dof.focus_distance = d.length; c.dof.aperture_fstop = fstop
    return ob

def area(name, loc, look, size, power, col='#FFFFFF', sy=None):
    l = bpy.data.lights.new(name, 'AREA'); l.size = size; l.energy = power; l.color = hexc(col)[:3]
    if sy: l.shape = 'RECTANGLE'; l.size_y = sy
    ob = bpy.data.objects.new(name, l); bpy.context.collection.objects.link(ob); ob.location = loc
    ob.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return ob

def world(col, strength=1.0):
    w = bpy.data.worlds.new('w'); w.use_nodes = True; bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = hexc(col); bg.inputs['Strength'].default_value = strength; sc.world = w

def launch_stage(s=0.25):
    """HESTIA launch studio, scaled to a hand-sized set"""
    world('#050506', 0.0)
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0)); fl = bpy.context.object
    fm_, fnt, fb = node_mat('stage floor'); fb.inputs['Base Color'].default_value = hexc('#0D0D0F'); fb.inputs['Roughness'].default_value = 0.3
    fb.inputs['Coat Weight'].default_value = 0.6; fb.inputs['Coat Roughness'].default_value = 0.08; fl.data.materials.append(fm_)
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 4 * s, 0)); wl = bpy.context.object; wl.rotation_euler = (math.radians(90), 0, 0)
    wl.data.materials.append(plain('stage wall', '#121214', 0.9))
    area('wallglow', (0, 2.6 * s, 0.3 * s), (0, 4 * s, 1.6 * s), 2.5 * s, 260 * s * s, '#F2C79A')
    area('top', (0, -0.3 * s, 3.2 * s), (0, 0, 0.3 * s), 0.5 * s, 320 * s * s, '#FFFFFF', sy=2.4 * s)
    area('rimL', (-1.5 * s, 1.1 * s, 1.4 * s), (0, 0, 0.25 * s), 0.25 * s, 380 * s * s, '#FFD9A8', sy=2.6 * s)
    area('rimR', (1.5 * s, 1.1 * s, 1.4 * s), (0, 0, 0.25 * s), 0.25 * s, 380 * s * s, '#BFD4FF', sy=2.6 * s)
    area('key', (-1.8 * s, -2.6 * s, 1.6 * s), (0, 0, 0.2 * s), 1.4 * s, 90 * s * s, '#FFF4E6')

def paper_sweep(col='#CFC6B8', s=0.3):
    sc.view_settings.exposure = -1.1
    verts = []; faces = []; W = 2; R = 0.3 * s
    prof = [(y, 0.0) for y in np.linspace(-2, 0.4 * s, 8)] + \
           [(0.4 * s + R * math.sin(a), R - R * math.cos(a)) for a in np.linspace(0, math.pi / 2, 24)][1:] + [(0.4 * s + R, z) for z in np.linspace(R, 2, 6)][1:]
    for (y, z) in prof: verts += [(-W, y, z), (W, y, z)]
    for i in range(len(prof) - 1):
        a = 2 * i; faces.append((a, a + 1, a + 3, a + 2))
    build('sweep', np.array(verts, float), faces, [0] * len(faces), [plain('sweep', col, rough=0.9)])
    world('#E9E4DA', 0.25)
    area('key', (-0.5 * s, -0.9 * s, 1.2 * s), (0, 0, 0.1 * s), 0.8 * s, 120 * s * s, '#FFF4E6')
    area('fill', (0.9 * s, -0.7 * s, 0.5 * s), (0, 0, 0.1 * s), 1.0 * s, 40 * s * s, '#E8EEF8')
    area('top', (0, 0.1 * s, 1.4 * s), (0, 0, 0), 1.2 * s, 70 * s * s, '#FFFFFF')

sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SPP; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 8; sc.render.resolution_x = RX; sc.render.resolution_y = RY
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = -0.1

if SHOT == 'hero':
    hand(MOD['p_hold'], wrap=True); mug(); launch_stage()
    cam((0.21, -0.40, 0.2), (-0.01, -0.005, 0.058), 62, fstop=5.6)
if SHOT == 'top':
    hand(MOD['p_hold'], wrap=True); mug(); launch_stage()
    cam((0.06, -0.2, 0.43), (-0.03, 0.0, 0.05), 50, fstop=8)
if SHOT == 'sequence':
    paper_sweep(s=0.5)
    PS = [0, 20, 45, 70]
    f = FING['Index']
    for i, p in enumerate(PS):
        x = -0.2 + i * 0.13
        # root clamp: champagne block; finger points +X, palm side down (-Z), width along Y
        bpy.ops.mesh.primitive_cube_add(location=(x - 0.012, 0, 0.115)); cb = bpy.context.object; cb.scale = (0.012, 0.016, 0.014)
        bv = cb.modifiers.new('b', 'BEVEL'); bv.width = 0.002; bv.segments = 3; cb.data.materials.append(M['champ'])
        bpy.ops.mesh.primitive_cube_add(location=(x - 0.012, 0, 0.0575)); st = bpy.context.object; st.scale = (0.006, 0.006, 0.058); st.data.materials.append(M['champ'])
        bpy.ops.mesh.primitive_cylinder_add(radius=0.022, depth=0.004, location=(x - 0.012, 0, 0.002)); bpy.context.object.data.materials.append(M['champ'])
        finger(f'idx{p}', f['L'], f['w'], f['h'], kappa_at(p, f['h']), (x, 0, 0.108), (1, 0, 0), (0, 0, -1), (0, 1, 0), p_kpa=p)
        tube_path(f'tube{p}', [(x - 0.024, 0, 0.115), (x - 0.04, 0.0, 0.11), (x - 0.05, 0.02, 0.02), (x - 0.06, 0.06, 0.002)], 0.002, M['tube'])
    cam((0.035, -0.8, 0.11), (0.035, 0, 0.072), 50)
if SHOT == 'exploded':
    paper_sweep(s=0.5)
    f = FING['Index']; L = f['L']; X0 = -0.045
    lay = [('grip', 0.0), ('woven', 0.022), ('bladder', 0.05), ('knit', 0.085)]
    for part, dz in lay:
        o = (X0, 0, 0.03 + dz)
        if part == 'bladder':
            finger('bladder', L - 4, f['w'] - 3, f['h'], 0.0, o, (1, 0, 0), (0, 0, -1), (0, 1, 0), part='bladder')
        elif part == 'knit':
            ob = finger('knit', L, f['w'], f['h'], 0.0, o, (1, 0, 0), (0, 0, -1), (0, 1, 0), pad=False)
            # open the pocket: drop the woven/edge faces so only the knit top shell shows
            me = ob.data
            import bmesh
            bm = bmesh.new(); bm.from_mesh(me)
            dele = [fc for fc in bm.faces if fc.material_index != 0]
            bmesh.ops.delete(bm, geom=dele, context='FACES'); bm.to_mesh(me); bm.free()
            sol = ob.modifiers.new('t', 'SOLIDIFY'); sol.thickness = 0.0008
        else:
            # flat panels: woven base, and the grip print as its own thin layer
            Lm, wm = L / 1000, f['w'] / 1000
            bpy.ops.mesh.primitive_cube_add(location=(X0 + Lm / 2, 0, o[2])); pn = bpy.context.object
            pn.scale = (Lm / 2, wm / 2 * (0.93), 0.0006 if part == 'woven' else 0.0009)
            bv = pn.modifiers.new('b', 'BEVEL'); bv.width = 0.0004; bv.segments = 2
            if part == 'woven': pn.data.materials.append(M['birch'])
            else:
                pn.scale = ((Lm - 0.018) / 2, (wm - 0.006) / 2, 0.0009); pn.location.x += 0.0045
                pn.data.materials.append(M['pad'])
            bpy.ops.object.transform_apply(scale=True)
            bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.uv.cube_project(cube_size=1.0); bpy.ops.object.mode_set(mode='OBJECT')
    # inlet barb + tube at the root
    ring_band('barb', (X0 - 0.008, 0, 0.03 + 0.05 + 0.006), (1, 0, 0), 0.003, 0.016, M['champ'])
    tube_path('tube', [(X0 - 0.016, 0, 0.086), (X0 - 0.04, 0, 0.08), (X0 - 0.06, 0.02, 0.03), (X0 - 0.07, 0.06, 0.002)], 0.0022, M['tube'])
    cam((0.10, -0.30, 0.25), (0.0, 0.0, 0.07), 55)

os.makedirs(os.path.dirname(OUT) or '.', exist_ok=True)
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print('DONE', OUT)
