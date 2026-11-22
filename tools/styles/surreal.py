exec(open('/home/claude/styles/_u.py').read())
import bmesh
sc=bpy.context.scene
cy=sc.objects.get('cyc'); cy.hide_render=True
# pink dune
bpy.ops.mesh.primitive_plane_add(size=6,location=(0,1.2,0)); d=bpy.context.object
md=d.modifiers.new('s','SUBSURF'); md.levels=6; md.render_levels=6; md.subdivision_type='SIMPLE'
tx=bpy.data.textures.new('dune','CLOUDS'); tx.noise_scale=0.9
dm=d.modifiers.new('d','DISPLACE'); dm.texture=tx; dm.strength=0.004; dm.mid_level=0.55
m=bpy.data.materials.new('sand'); m.use_nodes=True; b=m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value=_hx('#2E2A4A'); b.inputs['Roughness'].default_value=0.02
d.data.materials.append(m); bpy.ops.object.shade_smooth()
# sink and tilt the radio
for o in sc.objects:
    if o.type=='MESH' and o.parent is None and o.name not in ('cyc',) and o!=d: o.location.z+=0.09
wn=sc.world.node_tree; N=wn.nodes; L=wn.links
tc=N.new('ShaderNodeTexCoord'); sp=N.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Generated'],sp.inputs[0])
mr=N.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value=0.0; mr.inputs['From Max'].default_value=0.45; L.new(sp.outputs['Z'],mr.inputs['Value'])
cr=N.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color=_hx('#F6C3A8'); cr.color_ramp.elements[1].color=_hx('#7E8BD8'); L.new(mr.outputs['Result'],cr.inputs['Fac'])
L.new(cr.outputs['Color'],N['Background'].inputs['Color']); N['Background'].inputs['Strength'].default_value=0.5
# second, tiny radio-moon: a floating sphere moon
sphere((0.12,2.2,0.62),0.16,emat('moon','#FFE6CC',1.1))
clear_lights()
sun=bpy.data.lights.new('sun','SUN'); sun.energy=2.2; sun.angle=0.05; sun.color=(1,0.86,0.74); so=bpy.data.objects.new('sun',sun); sc.collection.objects.link(so); so.rotation_euler=(math.radians(80),0,math.radians(-35))
area((0.4,-0.6,0.3),0.8,0.8,'#BFD6FF')

# floating object, long shadow, wide lens
co=sc.objects['c']; co.location=(0.5,-0.9,0.1); tgt=Vector((-0.02,0.05,0.17))
co.rotation_euler=(tgt-co.location).to_track_quat('-Z','Y').to_euler(); co.data.lens=62; co.data.dof.use_dof=False
