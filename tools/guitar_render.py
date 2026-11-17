"""Henry's Rhino solid-body electric guitar (Fender-Claude-HMO.3dm) rendered in Blender Cycles.
usage: python3 guitar.py <shot> <out.png> <colourway> [rx] [ry] [spp]
shots: hero, front, back, bridge, head, controls, exploded, clay, edge
No logos: the headstock decal layer is never imported.
"""
import sys, math, os
import numpy as np
import rhino3dm as r3
import bpy, mathutils
from mathutils import Vector, Matrix
from scipy import ndimage

SHOT, OUT, CW = sys.argv[1], sys.argv[2], sys.argv[3]
RX = int(sys.argv[4]) if len(sys.argv) > 4 else 1600
RY = int(sys.argv[5]) if len(sys.argv) > 5 else 1000
SPP = int(sys.argv[6]) if len(sys.argv) > 6 else 64
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def hexc(h, a=1.0):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [a]

CWS = {
 'sunburst': dict(body='burst', guard='#EFEAE0', plastic='#EDE6D2', bg='#E9E4DA', name='3-Tone Burst'),
 'orange':   dict(body='#E8400A', guard='#F1ECE2', plastic='#F1ECE2', bg='#E9E4DA', name='Tigre Orange'),
 'ice':      dict(body='#9CC9D6', guard='#EFEAE0', plastic='#EDE6D2', bg='#E6E6E2', name='Ice Blue'),
 'ink':      dict(body='#101012', guard='#F1EEE7', plastic='#F1EEE7', bg='#E4E2DE', name='Ink Black'),
 'clay':     dict(body='clay', guard='#E9E7E3', plastic='#E9E7E3', bg='#ECEAE6', name='Clay'),
}
C = CWS[CW]
CLAY = CW == 'clay'

def node_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    return m, m.node_tree, m.node_tree.nodes['Principled BSDF']

def obj_vec(nt):
    tc = nt.nodes.new('ShaderNodeTexCoord'); return tc.outputs['Object']

def plain(name, col, rough=0.5, metal=0.0, coat=0.0, coat_r=0.05):
    m, nt, b = node_mat(name); b.inputs['Base Color'].default_value = hexc(col); b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal; b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = coat_r
    return m

def grain(nt, v, scale=(1, 1, 1), sc_=30.0):
    """long wood grain running along the guitar's length (Y)"""
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = scale; nt.links.new(v, mp.inputs['Vector'])
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'X'
    wv.inputs['Scale'].default_value = sc_; wv.inputs['Distortion'].default_value = 6; wv.inputs['Detail'].default_value = 4
    wv.inputs['Detail Scale'].default_value = 1.5; nt.links.new(mp.outputs['Vector'], wv.inputs['Vector'])
    return wv.outputs['Fac']

def body_mat():
    if CLAY: return plain('body', '#E2DFDA', 0.55)
    m, nt, b = node_mat('body'); v = obj_vec(nt)
    b.inputs['Coat Weight'].default_value = 1.0; b.inputs['Coat Roughness'].default_value = 0.02; b.inputs['Coat IOR'].default_value = 1.55
    if C['body'] == 'burst':
        at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'edge'
        mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Max'].default_value = 95.0; nt.links.new(at.outputs['Fac'], mr.inputs['Value'])
        rp = nt.nodes.new('ShaderNodeValToRGB'); e = rp.color_ramp.elements
        e[0].position = 0.0; e[0].color = hexc('#0E0704'); e[1].position = 1.0; e[1].color = hexc('#EBA521')
        for pos, col in ((0.10, '#120703'), (0.22, '#4A0F05'), (0.34, '#8E2207'), (0.50, '#C85A0C'), (0.68, '#E08E14')):
            el = e.new(pos); el.color = hexc(col)
        nt.links.new(mr.outputs['Result'], rp.inputs['Fac'])
        g = grain(nt, v, (6, 0.35, 6), 40)
        mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs['Factor'].default_value = 0.22
        nt.links.new(rp.outputs['Color'], mix.inputs[6])
        gr = nt.nodes.new('ShaderNodeValToRGB'); gr.color_ramp.elements[0].color = (0.55, 0.45, 0.35, 1); nt.links.new(g, gr.inputs['Fac'])
        nt.links.new(gr.outputs['Color'], mix.inputs[7]); nt.links.new(mix.outputs[2], b.inputs['Base Color'])
        b.inputs['Roughness'].default_value = 0.35
    else:
        b.inputs['Base Color'].default_value = hexc(C['body']); b.inputs['Roughness'].default_value = 0.3
        if C['body'] in ('#9CC9D6', '#E8400A'):   # metallic-flake nitro look
            b.inputs['Metallic'].default_value = 0.25; b.inputs['Roughness'].default_value = 0.28
    return m

def maple():
    if CLAY: return plain('neck', '#E2DFDA', 0.55)
    m, nt, b = node_mat('maple'); v = obj_vec(nt)
    g = grain(nt, v, (5, 0.08, 5), 40)
    rp = nt.nodes.new('ShaderNodeValToRGB'); rp.color_ramp.elements[0].color = hexc('#D9A866'); rp.color_ramp.elements[1].color = hexc('#E3B97C')
    nt.links.new(g, rp.inputs['Fac']); nt.links.new(rp.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.45; b.inputs['Coat Weight'].default_value = 0.5; b.inputs['Coat Roughness'].default_value = 0.2
    return m

def rosewood():
    if CLAY: return plain('board', '#CFCBC5', 0.6)
    m, nt, b = node_mat('rosewood'); v = obj_vec(nt)
    g = grain(nt, v, (10, 0.4, 10), 90)
    rp = nt.nodes.new('ShaderNodeValToRGB'); rp.color_ramp.elements[0].color = hexc('#1C0F0A'); rp.color_ramp.elements[1].color = hexc('#4A2A1A')
    nt.links.new(g, rp.inputs['Fac']); nt.links.new(rp.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.6
    return m

M = {
 'Body': body_mat(), 'Neck': maple(), 'Fretboard': rosewood(),
 'Frets': plain('frets', '#D9D6CF', 0.18, 1.0), 'Inlays': plain('inlay', '#EFE7D2', 0.4),
 'Nut': plain('nut', '#EFE7D2', 0.35),
 'Pickguard White': plain('guard', C['guard'], 0.22, coat=0.4), 'Pickguard Black': plain('guard ply', '#121212', 0.4),
 'Back Plate': plain('back plate', C['guard'], 0.25, coat=0.3),
 'Pickups': plain('pickups', C['plastic'], 0.35), 'Knobs': plain('knobs', C['plastic'], 0.35),
 'Pole Pieces': plain('poles', '#B9B6B0', 0.25, 1.0),
 'Chrome': plain('chrome', '#E8E8EA', 0.06, 1.0), 'Steel': plain('steel', '#8E8E8C', 0.32, 1.0),
 'Strings Plain': plain('str plain', '#D9D9DB', 0.15, 1.0), 'Strings Wound': plain('str wound', '#C9B48A', 0.25, 1.0),
}
if CLAY:
    for k in ('Chrome', 'Steel', 'Frets', 'Pole Pieces', 'Strings Plain', 'Strings Wound'):
        M[k] = plain(k, '#BDBAB4', 0.35, 0.0)
    M['Pickguard Black'] = plain('ply', '#2A2B2E', 0.5)
    M['Inlays'] = plain('inl', '#FF5A1F', 0.4); M['Nut'] = plain('nut', '#FF5A1F', 0.4)

# ---------------------------------------------------------------- groups for the exploded view
def grp(lay, name):
    n = name or ''
    if lay == 'Body': return 'body'
    if lay == 'Back Plate': return 'back'
    if lay in ('Neck', 'Fretboard', 'Frets', 'Inlays', 'Nut'): return 'neck'
    if lay.startswith('Strings'): return 'strings'
    if lay in ('Pickguard White', 'Pickguard Black', 'Pickups', 'Pole Pieces'):
        return 'body' if n == 'Jack insert' else 'guard'
    if lay == 'Knobs': return 'bridge' if 'Tremolo' in n else 'knobs'
    if n.startswith(('Tuner', 'String tree', 'Truss')): return 'neck'
    if n.startswith('Pickguard screw') or n.startswith('Switch'): return 'guard'
    if n.startswith('Neck plate'): return 'back'
    if n.startswith(('Trem claw', 'Trem spring')): return 'back'
    if n.startswith(('Jack', 'Strap')): return 'body'
    if n.startswith('Cover screw'): return 'back'
    return 'bridge'

# ---------------------------------------------------------------- import
F = r3.File3dm.Read(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'g.3dm'))
ROOT = bpy.data.objects.new('G', None); bpy.context.collection.objects.link(ROOT)
OBJ = []
for o in F.Objects:
    g = o.Geometry
    if not isinstance(g, r3.Brep): continue
    lay = F.Layers[o.Attributes.LayerIndex].FullPath.split('::')[-1]
    if lay == 'Decals': continue
    V = []; N = []; Fc = []
    for f in g.Faces:
        me = f.GetMesh(r3.MeshType.Any)
        if not me: continue
        base = len(V)
        for i in range(len(me.Vertices)):
            p = me.Vertices[i]; V.append((p.X * 0.001, p.Y * 0.001, p.Z * 0.001))
        if len(me.Normals) == len(me.Vertices):
            for i in range(len(me.Normals)): n = me.Normals[i]; N.append((n.X, n.Y, n.Z))
        else: N += [(0, 0, 1)] * len(me.Vertices)
        for i in range(len(me.Faces)):
            q = me.Faces[i]
            Fc.append((base + q[0], base + q[1], base + q[2]) if q[2] == q[3] else (base + q[0], base + q[1], base + q[2], base + q[3]))
    if not V: continue
    mesh = bpy.data.meshes.new(o.Attributes.Name or lay); mesh.from_pydata(V, [], Fc); mesh.update()
    mesh.polygons.foreach_set('use_smooth', [True] * len(mesh.polygons))
    try: mesh.normals_split_custom_set_from_vertices(N)
    except Exception as e: print('normals', e)
    if lay == 'Body':   # distance (mm) from the body's silhouette edge -> sunburst
        A = np.array(V) * 1000; x0, y0 = A[:, 0].min() - 5, A[:, 1].min() - 5
        W, H = int(A[:, 0].max() - x0 + 10), int(A[:, 1].max() - y0 + 10)
        mask = np.zeros((H, W), bool)
        for poly in Fc:
            P = A[list(poly)]
            if np.ptp(P[:, 2]) > 50: continue
            xs = np.clip(((P[:, 0] - x0)).astype(int), 0, W - 1); ys = np.clip(((P[:, 1] - y0)).astype(int), 0, H - 1)
            mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1] = True
        mask = ndimage.binary_fill_holes(ndimage.binary_closing(mask, iterations=3))
        dist = ndimage.distance_transform_edt(mask)
        xi = np.clip((A[:, 0] - x0).astype(int), 0, W - 1); yi = np.clip((A[:, 1] - y0).astype(int), 0, H - 1)
        d = dist[yi, xi]
        at = mesh.attributes.new('edge', 'FLOAT', 'POINT'); at.data.foreach_set('value', d.astype(np.float32))
    ob = bpy.data.objects.new(mesh.name, mesh); bpy.context.collection.objects.link(ob); ob.parent = ROOT
    mesh.materials.append(M[lay]); OBJ.append((grp(lay, o.Attributes.Name), lay, ob))

def G(*names): return [ob for g_, l_, ob in OBJ if g_ in names]

# ---------------------------------------------------------------- scene helpers
def cam(loc, look, lens=60, fstop=None, ortho=None, roll=0):
    c = bpy.data.cameras.new('cam'); c.lens = lens; c.clip_start = 0.01; c.clip_end = 100
    if ortho: c.type = 'ORTHO'; c.ortho_scale = ortho
    ob = bpy.data.objects.new('cam', c); bpy.context.collection.objects.link(ob); ob.location = loc
    ob.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    if roll: ob.rotation_euler.rotate_axis('Z', math.radians(roll))
    sc.camera = ob
    if fstop: c.dof.use_dof = True; c.dof.focus_distance = (Vector(look) - Vector(loc)).length; c.dof.aperture_fstop = fstop
    return ob

def area(name, loc, look, size, power, col='#FFFFFF', sy=None):
    l = bpy.data.lights.new(name, 'AREA'); l.size = size; l.energy = power; l.color = hexc(col)[:3]
    if sy: l.shape = 'RECTANGLE'; l.size_y = sy
    ob = bpy.data.objects.new(name, l); bpy.context.collection.objects.link(ob); ob.location = loc
    ob.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return ob

def floor(col, rough=0.85, z=0.0, gridmat=False, wall=None, axes=('X', 'Y'), pitch=0.025):
    me = bpy.data.meshes.new('floor'); s = 20
    me.from_pydata([(-s, -s, z), (s, -s, z), (s, s, z), (-s, s, z)] if wall is None else [(-s, wall, -s), (s, wall, -s), (s, wall, s), (-s, wall, s)], [], [(0, 1, 2, 3)]); me.update()
    ob = bpy.data.objects.new('floor', me); bpy.context.collection.objects.link(ob)
    if gridmat:
        m, nt, b = node_mat('grid'); v = obj_vec(nt)
        b.inputs['Roughness'].default_value = rough
        bk = nt.nodes.new('ShaderNodeTexBrick')
        mp = nt.nodes.new('ShaderNodeMapping'); nt.links.new(v, mp.inputs['Vector'])
        # 25 mm grid via two thin-line waves
        def lines(axis):
            sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(v, sep.inputs['Vector'])
            mt = nt.nodes.new('ShaderNodeMath'); mt.operation = 'PINGPONG'; mt.inputs[1].default_value = pitch / 2
            nt.links.new(sep.outputs[axis], mt.inputs[0])
            lt = nt.nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = 0.0005
            nt.links.new(mt.outputs[0], lt.inputs[0]); return lt.outputs[0]
        mx = nt.nodes.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'; nt.links.new(lines(axes[0]), mx.inputs[0]); nt.links.new(lines(axes[1]), mx.inputs[1])
        mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.inputs[6].default_value = hexc(col)
        mix.inputs[7].default_value = [c * (0.82 if c > 0.05 else 2.2) for c in hexc(col)[:3]] + [1]
        nt.links.new(mx.outputs[0], mix.inputs['Factor']); nt.links.new(mix.outputs[2], b.inputs['Base Color'])
        me.materials.append(m)
    else:
        me.materials.append(plain('floor', col, rough))
    return ob

def world(col, s):
    w = bpy.data.worlds.new('w'); w.use_nodes = True; bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = hexc(col); bg.inputs['Strength'].default_value = s; sc.world = w

def move(objs, d):
    for ob in objs: ob.location = (ob.location[0] + d[0], ob.location[1] + d[1], ob.location[2] + d[2])

def center():
    bpy.context.view_layer.update()
    P = np.array([ob.matrix_world @ Vector(c) for g_, l_, ob in OBJ for c in ob.bound_box])
    return Vector(((P.min(0) + P.max(0)) / 2).tolist()), P.max(0) - P.min(0)

def place(rx=0, ry=0, rz=0, t=(0, 0, 0)):
    ROOT.matrix_world = Matrix.Translation(t) @ Matrix.Rotation(math.radians(rz), 4, 'Z') @ Matrix.Rotation(math.radians(ry), 4, 'Y') @ Matrix.Rotation(math.radians(rx), 4, 'X')

sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SPP; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 8; sc.cycles.glossy_bounces = 4
sc.render.resolution_x = RX; sc.render.resolution_y = RY
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'
BG = C['bg']

# guitar coordinates: length along +Y (strap button ~ -0.16, headstock tip ~ +0.85), top face +Z (~0.05)
if SHOT == 'hero':     # floating, leaning, graphite studio wall with 50 mm grid + hot orange rim
    world('#0B0B0C', 0.0)
    place(rx=90, ry=-50, rz=22)
    c, ext = center(); place(rx=90, ry=-50, rz=22, t=tuple(-c))
    floor('#0C0C0E', 0.9, gridmat=True, wall=1.1, axes=('X', 'Z'), pitch=0.05)
    area('wallglow', (0.45, 0.6, -0.2), (0.6, 1.1, 0.1), 0.9, 30, '#FF5A1F')
    area('key', (-1.2, -1.6, 1.0), (0, 0, 0), 1.2, 140, '#FFF2E2')
    area('fill', (0.9, -1.8, -0.4), (0, 0, 0), 1.5, 35, '#E8EEFF')
    area('rimO', (1.2, 0.4, -0.5), (0, 0, 0), 0.5, 220, '#FF5A1F', sy=2.2)
    area('rimB', (-1.1, 0.4, 0.8), (0, 0, 0), 0.4, 120, '#8FB8FF', sy=1.8)
    area('strip', (-0.45, -1.5, 0.45), (0.05, 0, -0.1), 0.18, 160, '#FFFFFF', sy=1.6)
    cam((0.0, -1.78, 0.0), (0.0, 0, 0.0), 45, fstop=8)
elif SHOT in ('front', 'back'):  # catalog elevation, top-down orthographic on seamless
    world(BG, 0.25); floor(BG, 0.9, z=-0.002)
    R_ = dict(rz=-90) if SHOT == 'front' else dict(rx=180, rz=90)
    place(**R_); c, ext = center(); place(**R_, t=(-c[0], -c[1], -c[2] + ext[2] / 2))
    area('key', (-0.6, -0.9, 1.8), (0, 0, 0), 1.6, 70, '#FFF4E6')
    area('fill', (0.8, 0.8, 1.4), (0, 0, 0), 1.6, 18, '#EEF3FF')
    area('soft', (0, 0, 2.5), (0, 0, 0), 2.5, 25)
    cam((0, 0, 3), (0, 0, 0), ortho=1.12)
    bpy.data.objects['cam'].rotation_euler = (0, 0, 0)
elif SHOT == 'bridge':  # macro: saddles, height screws, springs
    world(BG, 0.45); floor(BG, 0.9, z=-0.002)
    area('key', (-0.35, -0.5, 0.7), (0, -0.03, 0.06), 0.5, 14, '#FFF2E2')
    area('rim', (0.4, 0.3, 0.4), (0, -0.03, 0.06), 0.3, 9, '#FFE2C8')
    area('top', (0, 0, 1.2), (0, 0, 0), 1.0, 6)
    cam((0.19, -0.26, 0.2), (0.0, -0.03, 0.06), 100, fstop=5.6)
elif SHOT == 'head':    # macro: headstock, tuners, string tree (no decal)
    world(BG, 0.45); floor(BG, 0.9, z=-0.002)
    area('key', (-0.4, 0.5, 0.8), (0, 0.76, 0.05), 0.6, 15, '#FFF2E2')
    area('rim', (0.45, 1.1, 0.35), (0, 0.76, 0.05), 0.3, 9, '#FFE2C8')
    area('top', (0, 0.75, 1.2), (0, 0.75, 0), 1.0, 6)
    cam((0.26, 0.55, 0.26), (0.0, 0.77, 0.05), 85, fstop=5.6)
elif SHOT == 'controls':  # macro: knobs, switch, pickups
    world(BG, 0.45); floor(BG, 0.9, z=-0.002)
    area('key', (0.6, -0.5, 0.7), (0.06, -0.04, 0.06), 0.6, 15, '#FFF2E2')
    area('rim', (-0.3, 0.4, 0.3), (0.06, -0.04, 0.06), 0.3, 8, '#FFE2C8')
    area('top', (0, 0, 1.2), (0, 0, 0), 1.0, 6)
    cam((0.42, 0.12, 0.2), (0.07, -0.07, 0.055), 90, fstop=5.6)
elif SHOT == 'exploded':  # technical exploded assembly over a 25 mm grid
    world(BG, 0.12)
    lift = {'back': -0.10, 'body': 0.0, 'bridge': 0.075, 'guard': 0.14, 'knobs': 0.195, 'strings': 0.0, 'neck': 0.02}
    for g_, l_, ob in OBJ:
        move([ob], (0, 0.16 if g_ == 'neck' else 0, lift[g_]))
        if g_ == 'strings': ob.hide_render = True
    place(rz=-90); c, ext = center(); place(rz=-90, t=(-c[0] + 0.25, -c[1], -c[2]))
    floor(BG, 0.85, z=-ext[2] / 2 - 0.05, gridmat=True)
    area('key', (-0.9, -1.0, 1.4), (-0.1, 0, 0), 1.4, 55, '#FFF4E6')
    area('fill', (0.9, -0.9, 0.5), (-0.1, 0, 0), 1.4, 16, '#EEF3FF')
    area('top', (-0.1, 0, 2.2), (-0.1, 0, 0), 2.0, 22)
    cam((0.25, -1.15, 0.62), (-0.08, 0.0, 0.0), 50)
elif SHOT == 'edge':    # low raking light along the body contour
    world('#141416', 0.2); floor('#1A1A1C', 0.5, z=-0.002)
    place(rz=-35)
    area('rake', (-1.2, 0.3, 0.12), (0, 0, 0.04), 0.4, 120, '#FFF0DE', sy=1.5)
    area('rimO', (0.8, -0.2, 0.25), (0, 0, 0.04), 0.3, 120, '#FF5A1F', sy=1.2)
    area('top', (0, 0, 1.6), (0, 0, 0), 0.8, 12)
    cam((0.55, -0.62, 0.22), (0.0, 0.02, 0.03), 70, fstop=4)

os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True); sc.render.filepath = os.path.abspath(OUT)
bpy.ops.render.render(write_still=True); print('DONE', OUT)
