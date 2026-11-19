"""TIGRE SY-5000 · hardware edition (renders). Tigre Studio 2026.
A concept enclosure built around the Tinkercad circuit on the SY-5000 page: Arduino Uno R3, eight keys,
four 10 kOhm pots under knurled knobs, MODE button, piezo and LED. Every part is placed from the same
pin list as the wiring sheet; the Uno is drawn at its real 68.6 x 53.4 mm footprint.
usage: python3 tools/sy5000_hw_render.py <hero|exploded|top> <out.png> [res_x] [res_y] [spp]
"""
import sys, math, os
import bpy, bmesh
from mathutils import Vector

SHOT = sys.argv[1]; OUT = sys.argv[2]
RX = int(sys.argv[3]) if len(sys.argv) > 3 else 1920
RY = int(sys.argv[4]) if len(sys.argv) > 4 else 1200
SPP = int(sys.argv[5]) if len(sys.argv) > 5 else 96
MM = 0.001

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def lin(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1.0]

def mat(name, col, rough=0.5, metal=0.0, coat=0.0, emit=0.0, sss=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = lin(col); b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal; b.inputs['Coat Weight'].default_value = coat
    if emit:
        b.inputs['Emission Color'].default_value = lin(col); b.inputs['Emission Strength'].default_value = emit
    return m

def grained(name, col, rough=0.62, scale=2600, strength=0.08):
    """moulded plastic with a fine texture (MT-11000-ish), so the paper shell does not read as CG white"""
    m = mat(name, col, rough); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = scale; n.inputs['Detail'].default_value = 6
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = strength; bp.inputs['Distance'].default_value = 0.0002
    nt.links.new(n.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m

M = dict(
    paper=grained('paper shell', '#F2EEE6'), ink=grained('ink tray', '#0B0B0C', 0.55), orange=mat('orange', '#FF5A1F', 0.42),
    keys=grained('key caps', '#E4DED2', 0.5, strength=0.05), keyO=mat('key C', '#FF5A1F', 0.45),
    blue=mat('knob blue', '#2F5BFF', 0.38), green=mat('knob green', '#1FA35C', 0.38), white=mat('knob white', '#F4F1EA', 0.4), orangeK=mat('knob orange', '#FF5A1F', 0.38),
    alu=mat('aluminium', '#C9CCD1', 0.28, 1.0), dark=mat('grille dark', '#151517', 0.7), led=mat('LED', '#FF5A1F', 0.2, emit=6.0),
    pcb=mat('Uno PCB', '#0E6E8A', 0.45, coat=0.3), hdr=mat('header', '#111113', 0.5), gold=mat('pins', '#D9B45A', 0.25, 1.0),
    tact=mat('tact', '#2A2A2D', 0.5), perf=mat('perfboard', '#C9A46A', 0.6), steel=mat('steel', '#9EA2A8', 0.3, 1.0), cable=mat('wire', '#FF5A1F', 0.5))

def put(ob, m):
    ob.data.materials.append(m); return ob

def rbox(name, cx, cy, cz, sx, sy, sz, r, m, seg=6):
    """rounded box centred at cx,cy with bottom at cz (all mm)"""
    bpy.ops.mesh.primitive_cube_add(location=(cx * MM, cy * MM, (cz + sz / 2) * MM)); ob = bpy.context.object; ob.name = name
    ob.scale = (sx / 2 * MM, sy / 2 * MM, sz / 2 * MM); bpy.ops.object.transform_apply(scale=True)
    bv = ob.modifiers.new('bevel', 'BEVEL'); bv.width = r * MM; bv.segments = seg; bv.limit_method = 'ANGLE'
    bpy.ops.object.shade_smooth(); return put(ob, m)

def cyl(name, cx, cy, cz, r, h, m, n=64, bevel=0.3):
    bpy.ops.mesh.primitive_cylinder_add(radius=r * MM, depth=h * MM, vertices=n, location=(cx * MM, cy * MM, (cz + h / 2) * MM)); ob = bpy.context.object; ob.name = name
    if bevel:
        bv = ob.modifiers.new('bevel', 'BEVEL'); bv.width = bevel * MM; bv.segments = 3; bv.limit_method = 'ANGLE'
    bpy.ops.object.shade_smooth(); return put(ob, m)

def knurled(name, cx, cy, cz, r, h, m, ridges=60, depth=0.45):
    """knurled knob: a straight-knurl skirt (alternating radii), a smooth domed top and an engraved pointer"""
    bm = bmesh.new(); n = ridges * 2
    rings = []
    for z, sc_ in ((0.0, 1.0), (h * 0.78, 1.0)):
        ring = []
        for i in range(n):
            a = 2 * math.pi * i / n; rr = (r if i % 2 == 0 else r - depth) * sc_
            ring.append(bm.verts.new((cx * MM + rr * MM * math.cos(a), cy * MM + rr * MM * math.sin(a), (cz + z) * MM)))
        rings.append(ring)
    for i in range(n):
        j = (i + 1) % n; bm.faces.new((rings[0][i], rings[0][j], rings[1][j], rings[1][i]))
    bm.faces.new(list(reversed(rings[0])))
    top = bm.faces.new(rings[1])
    bmesh.ops.inset_region(bm, faces=[top], thickness=0.7 * MM, depth=0)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); put(ob, m)
    # domed cap
    bpy.ops.mesh.primitive_uv_sphere_add(radius=(r - 0.9) * MM, segments=64, ring_count=32, location=(cx * MM, cy * MM, (cz + h * 0.78 - (r - 0.9) * 0.82) * MM))
    cap = bpy.context.object; cap.scale.z = 0.32; cap.name = name + ' cap'
    bpy.ops.object.shade_smooth(); put(cap, m)
    # pointer line
    rbox(name + ' pointer', cx, cy + r * 0.45, cz + h * 0.78 + 0.25, 0.9, r * 0.75, 0.8, 0.3, M['ink'] if m is not M['blue'] and m is not M['green'] else M['white'], seg=2)
    return ob

def label(txt, x, y, z, size, m, rot=0.0, align='LEFT'):
    bpy.ops.object.text_add(location=(x * MM, y * MM, z * MM)); t = bpy.context.object
    t.data.body = txt; t.data.size = size * MM; t.data.extrude = 0.08 * MM; t.data.align_x = align
    t.rotation_euler = (0, 0, rot); put(t, m); return t

# ------------------------------------------------------------------ geometry (mm). Body 168 x 96, tray 10 mm + shell 16 mm
W, D, HT, HS = 168, 96, 10, 16
LIFT = 70 if SHOT == 'exploded' else 0           # exploded: shell and its parts rise together
UNO_LIFT = 16 if SHOT == 'exploded' else 0
Z_TOP = HT + HS + LIFT

def shell_parts():
    rbox('tray', 0, 0, 0, W, D, HT, 8, M['ink'])
    sl = rbox('split line', 0, 0, HT - 0.5, W - 5.0, D - 5.0, 1.0, 6.0, M['orange'], seg=4)
    cut = rbox('split cut', 0, 0, HT - 2, W - 12, D - 12, 4, 3, M['orange'], seg=2)
    bo = sl.modifiers.new('ring', 'BOOLEAN'); bo.object = cut; bo.operation = 'DIFFERENCE'; cut.hide_render = True; cut.hide_viewport = True
    rbox('shell', 0, 0, HT + LIFT, W, D, HS, 8, M['paper'])
    # feet
    for fx in (-70, 70):
        for fy in (-36, 36): cyl('foot', fx, fy, -1.6, 5, 1.8, M['dark'], bevel=0.6)
    # piezo grille: 5 x 5 holes
    for i in range(5):
        for j in range(5):
            cyl('grille', -75.4 + i * 4.2, 13 + j * 4.2, Z_TOP - 0.6, 1.1, 0.8, M['dark'], n=24, bevel=0)
    # LED (D13) and MODE (D10)
    cyl('LED bezel', -67, -2, Z_TOP - 0.2, 3.4, 0.9, M['alu'])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=2.3 * MM, location=(-67 * MM, -2 * MM, (Z_TOP + 0.7) * MM)); led = bpy.context.object; led.scale.z = 0.8; bpy.ops.object.shade_smooth(); put(led, M['led'])
    cyl('MODE', -67, -22, Z_TOP - 0.2, 6.2, 3.2, M['ink'], bevel=0.8)
    cyl('MODE ring', -67, -22, Z_TOP - 0.3, 7.6, 0.8, M['orange'], bevel=0.3)
    # four knobs on A0..A3: octave, vibrato, decay, tempo (blue, green, white, orange, like the phone)
    for i, m in enumerate((M['blue'], M['green'], M['white'], M['orangeK'])):
        x = -26 + i * 30
        cyl('knob collar', x, 20, Z_TOP - 0.2, 11.2, 0.8, M['alu'])
        knurled(f'knob {i}', x, 20, Z_TOP + 0.6, 9.5, 11, m)
    # eight keys D2..D9; C keys in orange
    for i in range(8):
        x = -45.5 + i * 16.4
        rbox('key well', x, -24, Z_TOP - 0.4, 15.0, 26.0, 0.6, 2.6, M['ink'], seg=3)
        rbox(f'key {i}', x, -24, Z_TOP + 0.2, 13.6, 24.4, 3.6, 2.2, M['keyO'] if i in (0, 7) else M['keys'])
    # wordmark + micro-type, printed
    label('SY-5000', -78, -44 + 2.5, Z_TOP, 5.2, M['ink'])
    for i, t in enumerate(('OCT', 'VIB', 'DEC', 'TMP')):
        label(t, -26 + i * 30, 6.8, Z_TOP, 2.4, M['ink'], align='CENTER')
    for i, t in enumerate(('C', 'D', 'E', 'F', 'G', 'A', 'B', 'C')):
        label(t, -45.5 + i * 16.4, -40.2, Z_TOP, 2.4, M['ink'], align='CENTER')
    label('MODE', -67, -32.6, Z_TOP, 2.2, M['ink'], align='CENTER')
    # orange top stripe (Tigre accent)
    rbox('accent', -40, 41.0, Z_TOP - 0.1, 60, 1.4, 0.3, 0.6, M['orange'], seg=2)

def internals():
    z0 = 3 + UNO_LIFT
    # Arduino Uno R3: 68.6 x 53.4 x 1.6 mm board, headers along both long edges, USB-B and barrel jack on the back edge
    ux, uy = 30, -6
    rbox('Uno', ux, uy, z0, 68.6, 53.4, 1.6, 1.5, M['pcb'], seg=3)
    rbox('USB-B', ux - 26, uy + 26.7 - 3, z0 + 1.6, 12, 16, 11, 0.6, M['steel'], seg=2)
    rbox('DC jack', ux + 18, uy + 26.7 - 4, z0 + 1.6, 9, 13.5, 11, 0.6, M['hdr'], seg=2)
    rbox('MCU', ux - 4, uy - 6, z0 + 1.6, 35, 7.5, 3.6, 0.4, M['hdr'], seg=2)
    for (hx, hy, ln) in ((ux - 2, uy + 24.5, 56), (ux - 2, uy - 24.5, 44)):
        rbox('header', hx, hy, z0 + 1.6, ln, 2.6, 8.4, 0.2, M['hdr'], seg=1)
        for k in range(int(ln / 2.54)):
            cyl('pin', hx - ln / 2 + 1.27 + k * 2.54, hy, z0 + 1.6 + 8.0, 0.32, 0.6, M['gold'], n=8, bevel=0)
    # key board: perfboard with eight 12 mm tact switches, sitting under the keys
    rbox('key perfboard', 11.9, -24, 6 + LIFT * 0.5, 134, 22, 1.6, 1, M['perf'], seg=2)
    for i in range(8):
        x = -45.5 + i * 16.4
        rbox('tact', x, -24, 7.6 + LIFT * 0.5, 12, 12, 3.4, 0.6, M['tact'], seg=2)
        cyl('tact stem', x, -24, 11 + LIFT * 0.5, 3.2, 2.2, M['tact'], bevel=0.3)
    # four 10 kOhm pots with knurled shafts under the knobs
    for i in range(4):
        x = -26 + i * 30
        rbox('pot', x, 20, 6 + LIFT * 0.5, 16, 16, 7, 1, M['steel'], seg=2)
        cyl('pot shaft', x, 20, 13 + LIFT * 0.5, 3, 9, M['alu'], bevel=0.2)
    # piezo disc
    cyl('piezo', -67, 21.4, 5 + LIFT * 0.5, 13.5, 2.4, M['hdr'], bevel=0.4)
    cyl('piezo brass', -67, 21.4, 7.4 + LIFT * 0.5, 11, 0.3, M['gold'], bevel=0)

before = set(bpy.data.objects); shell_parts()
if SHOT == 'exploded':
    # slide the lid back as well as up, so the pots, keyboard and Uno read in one view
    for ob in set(bpy.data.objects) - before:
        if ob.name.split('.')[0] not in ('tray', 'split line', 'split cut', 'foot'): ob.location.y += 0.05
internals()

# ------------------------------------------------------------------ studio: paper sweep, grid on the floor (Tarka-ish), soft key
def sweep():
    bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, -1.8 * MM)); fl = bpy.context.object
    m = mat('floor', '#E9E3D8', 0.85); nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); br = nt.nodes.new('ShaderNodeTexBrick')
    br.inputs['Scale'].default_value = 1.0; br.inputs['Mortar Size'].default_value = 0.0007; br.offset = 0.0; br.squash = 1.0
    br.inputs['Brick Width'].default_value = 0.024; br.inputs['Row Height'].default_value = 0.024
    br.inputs['Color1'].default_value = lin('#E9E3D8'); br.inputs['Color2'].default_value = lin('#E9E3D8'); br.inputs['Mortar'].default_value = lin('#C9BFAE')
    nt.links.new(tc.outputs['Object'], br.inputs['Vector']); nt.links.new(br.outputs['Color'], b.inputs['Base Color'])
    fl.data.materials.append(m)
    bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0.42, 0)); wl = bpy.context.object; wl.rotation_euler = (math.radians(90), 0, 0); wl.data.materials.append(m)
    w = bpy.data.worlds.new('w'); w.use_nodes = True; bg = w.node_tree.nodes['Background']; bg.inputs['Color'].default_value = lin('#EDE7DD'); bg.inputs['Strength'].default_value = 0.12; sc.world = w

def area(name, loc, look, size, power, col='#FFFFFF', sy=None):
    l = bpy.data.lights.new(name, 'AREA'); l.size = size; l.energy = power; l.color = lin(col)[:3]
    if sy: l.shape = 'RECTANGLE'; l.size_y = sy
    ob = bpy.data.objects.new(name, l); bpy.context.collection.objects.link(ob); ob.location = loc
    ob.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()

def cam(loc, look, lens, fstop=None):
    c = bpy.data.cameras.new('cam'); c.lens = lens; c.clip_start = 0.005
    ob = bpy.data.objects.new('cam', c); bpy.context.collection.objects.link(ob)
    ob.location = loc; d = Vector(look) - Vector(loc); ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler(); sc.camera = ob
    if fstop: c.dof.use_dof = True; c.dof.focus_distance = d.length; c.dof.aperture_fstop = fstop

sweep()
area('key', (-0.32, -0.36, 0.42), (0, 0, 0.01), 0.45, 9, '#FFF3E4')
area('fill', (0.42, -0.2, 0.18), (0, 0, 0.01), 0.5, 2.5, '#E6EEFF')
area('top', (0.02, 0.06, 0.6), (0, 0, 0), 0.6, 5, '#FFFFFF', sy=0.3)
area('rim', (0.25, 0.35, 0.2), (0, 0, 0.02), 0.2, 3.5, '#FFD8B0')

sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SPP; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 6; sc.render.resolution_x = RX; sc.render.resolution_y = RY
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = -0.55

if SHOT == 'hero':
    cam((0.19, -0.29, 0.2), (0.004, -0.004, 0.012), 70, fstop=6.3)
if SHOT == 'exploded':
    cam((0.25, -0.33, 0.44), (0.004, 0.004, 0.05), 56)
if SHOT == 'top':
    cam((0.0, -0.035, 0.52), (0.0, -0.003, 0.0), 60)

os.makedirs(os.path.dirname(OUT) or '.', exist_ok=True)
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print('DONE', OUT)
