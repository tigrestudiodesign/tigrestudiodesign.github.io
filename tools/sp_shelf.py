"""Standard Play hero shelf: four VHS clamshell sleeves + C-46 Norelco case, real CMF.
python3 shelf.py OUT.png WIDTH SPP"""
import bpy, math, sys, os
from mathutils import Vector
OUT, W, SPP = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
H = round(W * 860 / 1800)
D = '/home/claude/cmf/shelf/'
mm = 0.001
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SPP
sc.cycles.use_denoising = True; sc.cycles.max_bounces = 10; sc.cycles.transmission_bounces = 10
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.view_settings.view_transform = os.environ.get('VT','AgX')
if sc.view_settings.view_transform == 'AgX': sc.view_settings.look = os.environ.get('LOOKT','AgX - Punchy')
sc.render.film_transparent = False
sc.view_settings.exposure = float(os.environ.get('EXP', -0.9))

def srgb(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple([(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c] + [1])

def mat(name, col='#808080', rough=.5, metal=0, img=None, trans=0, ior=1.5, coat=0, bump=0, bscale=400, aniso=0, emis=None, spec=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    b.inputs['Transmission Weight'].default_value = trans; b.inputs['IOR'].default_value = ior
    b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = 0.05
    b.inputs['Anisotropic'].default_value = aniso; b.inputs['Specular IOR Level'].default_value = spec
    if img:
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(D + img); t.interpolation = 'Cubic'
        nt.links.new(t.outputs[0], b.inputs['Base Color'])
    else:
        b.inputs['Base Color'].default_value = srgb(col)
    if emis:
        b.inputs['Emission Color'].default_value = srgb(emis[0]); b.inputs['Emission Strength'].default_value = emis[1]
    if bump:
        n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = bscale; n.inputs['Detail'].default_value = 6
        tc = nt.nodes.new('ShaderNodeTexCoord'); nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
        bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump; bp.inputs['Distance'].default_value = 0.0004
        nt.links.new(n.outputs[0], bp.inputs['Height']); nt.links.new(bp.outputs[0], b.inputs['Normal'])
    return m

def box(name, sx, sy, sz, loc, m, bev=0.0008, rot=0, parent=None, seg=3):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object; o.name = name; o.scale = (sx, sy, sz); bpy.ops.object.transform_apply(scale=True)
    if bev:
        md = o.modifiers.new('b', 'BEVEL'); md.width = bev; md.segments = seg; md.limit_method = 'ANGLE'
    o.data.materials.append(m); o.rotation_euler.z = math.radians(rot)
    bpy.ops.object.shade_smooth_by_angle()
    if parent: o.parent = parent
    return o

def panel(name, w, h, loc, rot, m, parent):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    o = bpy.context.object; o.name = name; o.scale = (w, h, 1); bpy.ops.object.transform_apply(scale=True)
    o.rotation_euler = rot; o.location = loc; o.data.materials.append(m); o.parent = parent
    return o

def empty(loc, rz):
    e = bpy.data.objects.new('g', None); sc.collection.objects.link(e)
    e.location = loc; e.rotation_euler.z = math.radians(rz); return e

# ---------------------------------------------------------------- sweep with a 10 mm print grid
bpy.ops.mesh.primitive_plane_add(size=1)
sw = bpy.context.object; sw.name = 'sweep'
import bmesh
me = sw.data; bm = bmesh.new()
prof = []
R = 0.35
for i in range(25):
    a = i / 24 * math.pi / 2
    prof.append((-R * math.sin(a) + 0.0, R - R * math.cos(a)))
pts = [(0.9, 0.0)] + [(-y, z) for (y, z) in [(-0.0 - 0.0, 0)]] if False else None
prof2 = [(-1.2, 0)] + [(0.35 + R * math.sin(i / 24 * math.pi / 2), R - R * math.cos(i / 24 * math.pi / 2)) for i in range(25)] + [(0.7, 1.4)]
vs = []
for (y, z) in prof2:
    vs.append((bm.verts.new((-1.6, y, z)), bm.verts.new((1.6, y, z))))
for i in range(len(vs) - 1):
    bm.faces.new((vs[i][0], vs[i][1], vs[i + 1][1], vs[i + 1][0]))
bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
gm = bpy.data.materials.new('grid'); gm.use_nodes = True; nt = gm.node_tree; b = nt.nodes['Principled BSDF']
b.inputs['Roughness'].default_value = 0.72
tc = nt.nodes.new('ShaderNodeTexCoord')
def gridline(step, wdt):
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sep.inputs[0])
    outs = []
    for ax in ('X', 'Y', 'Z'):
        md = nt.nodes.new('ShaderNodeMath'); md.operation = 'PINGPONG'; md.inputs[1].default_value = step / 2
        nt.links.new(sep.outputs[ax], md.inputs[0])
        lt = nt.nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = wdt
        nt.links.new(md.outputs[0], lt.inputs[0]); outs.append(lt)
    mx = nt.nodes.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'; nt.links.new(outs[0].outputs[0], mx.inputs[0]); nt.links.new(outs[1].outputs[0], mx.inputs[1])
    return mx
g1 = gridline(0.01, 0.00025); g2 = gridline(0.05, 0.0005)
mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
mix.inputs[6].default_value = srgb(os.environ.get('SWC','#3A3B3E')); mix.inputs[7].default_value = srgb(os.environ.get('SWL','#5A5C61'))
mx = nt.nodes.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'
s1 = nt.nodes.new('ShaderNodeMath'); s1.operation = 'MULTIPLY'; s1.inputs[1].default_value = 0.45
nt.links.new(g1.outputs[0], s1.inputs[0]); nt.links.new(s1.outputs[0], mx.inputs[0]); nt.links.new(g2.outputs[0], mx.inputs[1])
nt.links.new(mx.outputs[0], mix.inputs[0]); nt.links.new(mix.outputs[2], b.inputs['Base Color'])
sw.data.materials.append(gm)

# ---------------------------------------------------------------- plinth: graphite powder coat + orange anodised edge
PW, PD, PH = 1.3, 0.17, 0.024
graphite = mat('powder graphite', '#1C1D20', .55, bump=.25, bscale=900)
orange = mat('orange anodise', '#FF5A1F', .35, metal=.3)
alu = mat('bead-blast alu', '#C9CBCC', .38, metal=1)
plin = box('plinth', PW, PD, PH, (0.02, 0.05, PH / 2), graphite, bev=0.0015)
box('edge', PW - 0.004, 0.0016, 0.006, (0.02, 0.05 - PD / 2 - 0.0006, PH * 0.55), orange, bev=0.0003)
# micro-type plate on plinth front
for i, x in enumerate([-0.42, 0.44]):
    box('screw%d' % i, 0.007, 0.002, 0.007, (x, 0.05 - PD / 2 - 0.0008, PH * 0.55), alu, bev=0.0012)

# ---------------------------------------------------------------- VHS clamshell sleeves
SW, SH, SD = 0.104, 0.188, 0.026
pet = mat('PET overlay', '#FFFFFF', 0.02, trans=1, ior=1.57, bump=0.012, bscale=40)
TAPES = [('t120', '#0B0A10'), ('t60', '#050B07'), ('t90', '#17181A'), ('t160', '#0F2410')]
XS = [-0.30, -0.175, -0.05, 0.075]; RZ = [16, 7, -4, -12]; YS = [0.03, 0.06, 0.07, 0.05]
for (t, bg), x, rz, y in zip(TAPES, XS, RZ, YS):
    g = empty((x, y, PH), rz)
    board = mat(t + ' board', bg, .7, bump=.15, bscale=1500, spec=.2)
    front = mat(t + ' front', img=t + '_front.png', rough=.62, spec=.12)
    spine = mat(t + ' spine', img=t + '_spine.png', rough=.62, spec=.12)
    back = mat(t + ' back', img=t + '_back.png', rough=.62, spec=.12)
    for m_ in (front, spine, back, board):
        bb_ = m_.node_tree.nodes['Principled BSDF']; bb_.inputs['Coat Weight'].default_value = 1.0; bb_.inputs['Coat Roughness'].default_value = 0.035; bb_.inputs['Coat IOR'].default_value = 1.57
        nz = m_.node_tree.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 9; nz.inputs['Detail'].default_value = 3
        bz = m_.node_tree.nodes.new('ShaderNodeBump'); bz.inputs['Strength'].default_value = 0.05
        m_.node_tree.links.new(nz.outputs[0], bz.inputs['Height']); m_.node_tree.links.new(bz.outputs[0], bb_.inputs['Coat Normal'])
    core = box(t + ' core', SW, SD, SH, (0, 0, SH / 2), board, bev=0.0012, parent=g)
    panel(t + ' f', SW - 0.0016, SH - 0.0016, (0, -SD / 2 - 0.0002, SH / 2), (math.radians(90), 0, 0), front, g)
    panel(t + ' b', SW - 0.0016, SH - 0.0016, (0, SD / 2 + 0.0002, SH / 2), (math.radians(90), 0, math.radians(180)), back, g)
    for sgn in (-1, 1):
        panel(t + ' s', SH - 0.0016, SD - 0.0016, (sgn * (SW / 2 + 0.0002), 0, SH / 2), (math.radians(90), math.radians(90), math.radians(90 * sgn)), spine, g)
    if os.environ.get('PETBOX'): box(t + ' pet', SW + 0.0012, SD + 0.0012, SH + 0.0008, (0, 0, SH / 2 + 0.0002), pet, bev=0.0016, parent=g, seg=4)

# ---------------------------------------------------------------- C-46 Norelco case standing, J-card inside
CW, CH, CD = 0.069, 0.109, 0.017
ps = mat('clear PS', '#FFFFFF', 0.02, trans=1, ior=1.59)
g = empty((0.2, 0.06, PH), -10)
panel('jcard', 0.064, 0.101, (0, -CD / 2 + 0.0018, CH / 2), (math.radians(90), 0, 0), mat('c46 front', img='c46_front.png', rough=.55, spec=.15), g)
panel('jspine', 0.101, 0.0125, (CW / 2 - 0.0035, 0, CH / 2), (math.radians(90), math.radians(90), math.radians(90)), mat('c46 spine', img='c46_spine.png', rough=.55, spec=.15), g)
box('c46 inner', 0.062, 0.010, 0.098, (0, 0.002, CH / 2), mat('smoke ABS', '#141619', .35), bev=0.001, parent=g)
box('c46 case', CW, CD, CH, (0, 0, CH / 2), ps, bev=0.0014, parent=g, seg=4)

# ---------------------------------------------------------------- orange powder-coat bookend with knurled aluminium thumb screw
opc = mat('orange powder', '#FF5A1F', .5, bump=.2, bscale=900)
be = empty((0.285, 0.065, PH), -8)
box('bookend base', 0.055, 0.1, 0.004, (0, 0, 0.002), opc, bev=0.0012, parent=be)
box('bookend wall', 0.005, 0.1, 0.13, (-0.025, 0, 0.065), opc, bev=0.0016, parent=be)
km = mat('knurl', '#BFC2C4', .28, metal=1)
nt = km.node_tree; bb = nt.nodes['Principled BSDF']
tc2 = nt.nodes.new('ShaderNodeTexCoord')
def wave(sx):
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (sx, 1, 1); nt.links.new(tc2.outputs['Object'], mp.inputs[0])
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'DIAGONAL'; wv.inputs['Scale'].default_value = 140; wv.wave_profile = 'TRI'
    nt.links.new(mp.outputs[0], wv.inputs['Vector']); return wv
ml = nt.nodes.new('ShaderNodeMath'); ml.operation = 'MINIMUM'; nt.links.new(wave(1).outputs['Fac'], ml.inputs[0]); nt.links.new(wave(-1).outputs['Fac'], ml.inputs[1])
bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 1.0; bp.inputs['Distance'].default_value = 0.0008
nt.links.new(ml.outputs[0], bp.inputs['Height']); nt.links.new(bp.outputs[0], bb.inputs['Normal'])
bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=0.011, depth=0.016, location=(-0.031, 0, 0.1))
kn = bpy.context.object; kn.parent = be; kn.rotation_euler.y = math.radians(90); kn.data.materials.append(km)
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.0035, depth=0.0012, location=(-0.0395, 0, 0.1))
dot = bpy.context.object; dot.parent = be; dot.rotation_euler.y = math.radians(90); dot.data.materials.append(mat('index', '#141318', .4))

# ---------------------------------------------------------------- VHS cassette lying in front: stipple ABS, smoked windows, reels
abs_ = mat('stipple ABS', '#141318', .55, bump=.5, bscale=2200)
smoke = mat('smoked PC', '#2E2A33', 0.04, trans=.92, ior=1.58)
tape = mat('tape pack', '#3A2A1E', .45, metal=.2)
hub = mat('hub', '#ECEAE4', .4)
VW, VD, VT = 0.187, 0.103, 0.025
cg = empty((-0.16, -0.13, 0), 6)
box('vhs body', VW, VD, VT, (0, 0, VT / 2), abs_, bev=0.0015, parent=cg)
panel('vhs label', VW * 0.86, VT * 0.62, (0, -VD / 2 - 0.0003, VT / 2), (math.radians(90), 0, 0), mat('t120 cart label', img='t120_spine.png', rough=.8), cg)
box('vhs window', 0.11, 0.045, 0.0012, (0, 0.006, VT + 0.0003), smoke, bev=0.0004, parent=cg)
for sx in (-0.045, 0.045):
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=0.03 if sx < 0 else 0.019, depth=0.008, location=(sx, 0.006, VT - 0.005))
    o = bpy.context.object; o.parent = cg; o.data.materials.append(tape)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.011, depth=0.009, location=(sx, 0.006, VT - 0.0048))
    o = bpy.context.object; o.parent = cg; o.data.materials.append(hub)

# ---------------------------------------------------------------- C-46 cassette lying in front: smoked shell, teal label
c2 = empty((0.12, -0.12, 0), -16)
box('cc body', 0.1, 0.0635, 0.0122, (0, 0, 0.0061), mat('cc shell', '#1A1D21', .3, coat=.3), bev=0.0012, parent=c2)
box('cc label', 0.088, 0.045, 0.0004, (0, 0.004, 0.0123), mat('cc label', '#07090B', .7), bev=0.0002, parent=c2)
box('cc stripe', 0.088, 0.006, 0.0005, (0, 0.022, 0.0124), mat('teal print', '#2EF2D0', .6, emis=('#2EF2D0', .6)), bev=0.0002, parent=c2)
box('cc stripe2', 0.088, 0.0025, 0.0005, (0, 0.0145, 0.0124), mat('amber print', '#FFB23E', .6), bev=0.0001, parent=c2)
box('cc window', 0.04, 0.012, 0.0008, (0, 0.002, 0.0127), smoke, bev=0.0003, parent=c2)
for sx in (-0.021, 0.021):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.0062, depth=0.0006, location=(sx, 0.002, 0.0128))
    o = bpy.context.object; o.parent = c2; o.data.materials.append(hub)

# black flag behind the camera: keeps the glossy PET from mirroring the bright sweep
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -1.6, 0.6)); fl = bpy.context.object; fl.scale = (4, 1.6, 1); fl.rotation_euler.x = math.radians(90)
fl.data.materials.append(mat('flag', '#050505', .9)); fl.visible_camera = False
# ---------------------------------------------------------------- lights + camera
def area(name, loc, look, size, en, col=(1, 1, 1), sy=None):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = en; l.size = size; l.color = col
    if sy: l.shape = 'RECTANGLE'; l.size_y = sy
    o = bpy.data.objects.new(name, l); sc.collection.objects.link(o); o.location = loc
    d = Vector(look) - Vector(loc); o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
area('key', (-0.9, -0.8, 1.1), (0, 0.05, 0.1), 0.9, 260, (1, .97, .93))
area('fill', (1.3, -0.7, 0.5), (0, 0.05, 0.1), 0.8, 45, (.92, .95, 1))
area('rim', (0.6, 0.9, 0.7), (0, 0.05, 0.12), 0.15, 90, (1, .9, .85), sy=1.2)
area('top', (0, -0.1, 1.5), (0, 0.05, 0), 0.6, 60)
area('glow', (0.0, 0.18, 0.05), (0.0, 0.6, 0.35), 0.5, float(os.environ.get('GLOW', 40)), (1, .45, .2))
w = bpy.data.worlds.new('w'); w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.16, 0.16, 0.17, 1); sc.world = w

cam = bpy.data.cameras.new('c'); cam.lens = float(os.environ.get('LENS', 48)); cam.dof.use_dof = True; cam.dof.aperture_fstop = 8
co = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co); sc.camera = co
CAM = [float(v) for v in os.environ.get('CAM', '0.03,-1.02,0.42').split(',')]
LOOK = [float(v) for v in os.environ.get('LOOK', '0.0,0.0,0.105').split(',')]
co.location = CAM; co.rotation_euler = (Vector(LOOK) - Vector(CAM)).to_track_quat('-Z', 'Y').to_euler()
cam.dof.focus_distance = (Vector(LOOK) - Vector(CAM)).length
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print('done', OUT)
