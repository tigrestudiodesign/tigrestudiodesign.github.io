import bpy, math, os
from mathutils import Vector
def _hx(h):
    h=h.lstrip('#'); c=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(((v/12.92) if v<=0.04045 else ((v+0.055)/1.055)**2.4) for v in c)+(1,)
def mats(prefix):
    return [m for m in bpy.data.materials if m.name==prefix or m.name.startswith(prefix+'.') or (prefix.endswith('*') and m.name.startswith(prefix[:-1]))]
def setm(prefix, col=None, rough=None, metal=None, trans=None, coat=None, emis=None, ink=None, film=None, sss=None, spec=None, alpha=None):
    for m in mats(prefix):
        nt=m.node_tree; b=nt.nodes.get('Principled BSDF')
        if not b: continue
        mix=[n for n in nt.nodes if n.type=='MIX' and n.data_type=='RGBA']
        if col:
            if mix: mix[0].inputs['A'].default_value=_hx(col)
            else:
                for l in list(b.inputs['Base Color'].links): nt.links.remove(l)
                b.inputs['Base Color'].default_value=_hx(col)
        if ink and mix: mix[0].inputs['B'].default_value=_hx(ink)
        if rough is not None: b.inputs['Roughness'].default_value=rough
        if metal is not None: b.inputs['Metallic'].default_value=metal
        if trans is not None: b.inputs['Transmission Weight'].default_value=trans
        if coat is not None: b.inputs['Coat Weight'].default_value=coat
        if sss is not None: b.inputs['Subsurface Weight'].default_value=sss
        if spec is not None: b.inputs['Specular IOR Level'].default_value=spec
        if alpha is not None: b.inputs['Alpha'].default_value=alpha
        if film is not None: b.inputs['Thin Film Thickness'].default_value=film
        if emis is not None:
            b.inputs['Emission Color'].default_value=_hx(emis[0]); b.inputs['Emission Strength'].default_value=emis[1]
def allmats(skip=('floor',)):
    return [m.name for m in bpy.data.materials if m.node_tree and m.node_tree.nodes.get('Principled BSDF') and not any(m.name.startswith(s) for s in skip)]
def floor(col, grid=None, rough=None):
    for m in mats('floor'):
        for n in m.node_tree.nodes:
            if n.type=='TEX_BRICK':
                n.inputs['Color1'].default_value=_hx(col); n.inputs['Color2'].default_value=_hx(col); n.inputs['Mortar'].default_value=_hx(grid or col)
        if rough is not None: m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=rough
def world(col, strength):
    w=bpy.context.scene.world; w.node_tree.nodes['Background'].inputs['Color'].default_value=_hx(col); w.node_tree.nodes['Background'].inputs['Strength'].default_value=strength
def clear_lights():
    for o in [o for o in bpy.context.scene.objects if o.type=='LIGHT' and o.data.type=='AREA']: bpy.data.objects.remove(o)
def area(loc, size, energy, col='#ffffff', tgt=(0,0,0.07), shape=None):
    l=bpy.data.lights.new('s','AREA'); l.size=size; l.energy=energy; l.color=_hx(col)[:3]
    if shape: l.shape='RECTANGLE'; l.size_y=shape
    o=bpy.data.objects.new('s',l); bpy.context.scene.collection.objects.link(o); o.location=loc
    o.rotation_euler=(Vector(tgt)-Vector(loc)).to_track_quat('-Z','Y').to_euler(); return o
def sphere(loc, r, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=64, ring_count=32); o=bpy.context.object
    bpy.ops.object.shade_smooth(); o.data.materials.append(mat); return o
def emat(name, col, strength):
    m=bpy.data.materials.new(name); m.use_nodes=True; b=m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value=_hx(col); b.inputs['Emission Color'].default_value=_hx(col); b.inputs['Emission Strength'].default_value=strength; return m
