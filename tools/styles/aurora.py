exec(open('/home/claude/styles/_u.py').read())
sc=bpy.context.scene
for k in ('shell','back','graph','rubber','cone','blk','btn_*'): setm(k,col='#F3F1EE',rough=0.55,metal=0,coat=0,ink='#1A1A1C',sss=0)
setm('face',col='#F3F1EE',ink='#1A1A1C'); setm('plate',col='#FF5A1F',ink='#FFFFFF')
floor('#E9E4F2','#E9E4F2',rough=0.6); world('#E9E4F2',0.15)
sc.objects['cyc'].hide_render=True
for loc,r,c,s in [((-0.40,1.15,0.22),0.34,'#4BE3C1',3.0),((0.05,1.3,0.36),0.38,'#7A5CFF',3.0),((0.45,1.1,0.14),0.3,'#FF6FB5',3.0),((0.15,1.0,-0.12),0.26,'#FFB547',2.4)]:
    sphere(loc,r,emat('au'+c,c,s))
bpy.ops.mesh.primitive_plane_add(size=3,location=(0,0,0)); pl=bpy.context.object
m=bpy.data.materials.new('au_floor'); m.use_nodes=True; b=m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value=_hx('#EDE8F5'); b.inputs['Roughness'].default_value=0.35
pl.data.materials.append(m)
cam=sc.camera.data; cam.dof.use_dof=True; cam.dof.aperture_fstop=2.0
clear_lights(); area((-0.4,-0.5,0.55),0.9,3.2); area((0.5,-0.3,0.25),0.7,1.2,'#F1ECFF')
