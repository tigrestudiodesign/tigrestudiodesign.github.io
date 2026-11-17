import sys, os, math, random
import bpy, bmesh, mathutils
from mathutils import Vector
OUT=sys.argv[sys.argv.index('--')+1]; SHOT=sys.argv[sys.argv.index('--')+2]
RES=int(os.environ.get('RES','900')); SPP=int(os.environ.get('SPP','24'))
EXPL=float(os.environ.get('EXPL','0'))
bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene
mm=0.001; HERE=os.path.dirname(os.path.abspath(__file__))
def hx(h): h=h.lstrip('#'); c=[int(h[i:i+2],16)/255 for i in (0,2,4)]; return tuple(((v/12.92) if v<=0.04045 else ((v+0.055)/1.055)**2.4) for v in c)+(1,)
C=dict(shell='#ddd4c2',face='#222326',orange='#ff5a1f',sos='#e8321a',cream='#f1ece1',ink='#1a1a1c',alu='#c9cbcd',graph='#3a3c40',floor='#ece8e0',grid='#d3cdc2')

def mat(name,col,rough,metal=0,coat=0,trans=0,aniso=0,sss=0):
    m=bpy.data.materials.new(name); m.use_nodes=True; b=m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value=hx(col); b.inputs['Roughness'].default_value=rough; b.inputs['Metallic'].default_value=metal
    b.inputs['Coat Weight'].default_value=coat; b.inputs['Transmission Weight'].default_value=trans; b.inputs['Anisotropic'].default_value=aniso
    b.inputs['Subsurface Weight'].default_value=sss
    return m,b
def grain(m,b,scale=2500,s=0.08):
    N=m.node_tree.nodes; L=m.node_tree.links; nz=N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value=scale
    bp=N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value=s; L.new(nz.outputs['Fac'],bp.inputs['Height']); L.new(bp.outputs['Normal'],b.inputs['Normal'])
    return m
def decal(base,col,img,ink,w,h,axes='xz',face=(0,-1,0),flipu=False):
    """image mask printed on the face whose local normal matches `face`; object-space mapping, centred on origin"""
    m,b=mat(base,col,0.55); N=m.node_tree.nodes; L=m.node_tree.links
    tc=N.new('ShaderNodeTexCoord'); sx=N.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'],sx.inputs[0])
    ia={'x':0,'y':1,'z':2}
    def lin(out,k,off):
        n=N.new('ShaderNodeMath'); n.operation='MULTIPLY_ADD'; L.new(out,n.inputs[0]); n.inputs[1].default_value=k; n.inputs[2].default_value=off; return n.outputs[0]
    u=lin(sx.outputs[ia[axes[0]]],(-1 if flipu else 1)/w,0.5); v=lin(sx.outputs[ia[axes[1]]],1/h,0.5)
    cb=N.new('ShaderNodeCombineXYZ'); L.new(u,cb.inputs[0]); L.new(v,cb.inputs[1])
    it=N.new('ShaderNodeTexImage'); it.image=bpy.data.images.load(os.path.join(HERE,img)); it.image.colorspace_settings.name='Non-Color'; it.extension='CLIP'; it.interpolation='Cubic'
    L.new(cb.outputs[0],it.inputs['Vector'])
    dp=N.new('ShaderNodeVectorMath'); dp.operation='DOT_PRODUCT'; dp.inputs[1].default_value=face; L.new(tc.outputs['Normal'],dp.inputs[0])
    gt=N.new('ShaderNodeMath'); gt.operation='GREATER_THAN'; gt.inputs[1].default_value=0.8; L.new(dp.outputs['Value'],gt.inputs[0])
    a=N.new('ShaderNodeMath'); a.operation='MULTIPLY'; L.new(it.outputs['Color'],a.inputs[0]); L.new(gt.outputs[0],a.inputs[1])
    mx=N.new('ShaderNodeMix'); mx.data_type='RGBA'; mx.inputs['A'].default_value=hx(col); mx.inputs['B'].default_value=hx(ink)
    L.new(a.outputs[0],mx.inputs['Factor']); L.new(mx.outputs['Result'],b.inputs['Base Color'])
    grain(m,b,2200,0.05)
    return m

M_shell,b=mat('shell',C['shell'],0.6,sss=0.05); grain(M_shell,b,1800,0.12)
M_alu,_=mat('alu',C['alu'],0.28,metal=1.0,aniso=0.6)
M_steel,_=mat('steel','#9a9da1',0.32,metal=1.0)
M_graph,b=mat('graph',C['graph'],0.5); grain(M_graph,b)
M_rubber,b=mat('rubber','#202124',0.8); grain(M_rubber,b,1200,0.2)
M_orange,b=mat('orange',C['orange'],0.45); grain(M_orange,b)
M_ledon,b=mat('ledon',C['orange'],0.3); b.inputs['Emission Color'].default_value=hx(C['orange']); b.inputs['Emission Strength'].default_value=6
M_ledoff,_=mat('ledoff','#5a4a40',0.3)
M_diff,b=mat('diff','#efe6d2',0.3,trans=0.0,sss=0.5); b.inputs['Emission Color'].default_value=hx('#ffd9a0'); b.inputs['Emission Strength'].default_value=float(os.environ.get('LANT','0.12'))
M_pcb,b=mat('pcb','#1d3b33',0.4)
M_chip,_=mat('chip','#141416',0.35)
M_cell,b=mat('cell',C['orange'],0.35,coat=0.6)
M_cone,_=mat('cone','#18181a',0.75)
M_screwhole,_=mat('blk','#0c0c0d',0.6)

def rrect(name,w,h,r,t,mat_,loc=(0,0,0),axis='y',rim=0.8*mm,seg=12):
    """rounded-rect prism: profile w x h (local X,Y) extruded t along Z, then rotated so Z -> axis"""
    bm=bmesh.new(); pts=[]
    for cx,cy,a0 in ((w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)):
        for i in range(seg+1):
            a=math.radians(a0+90*i/seg); pts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
    vb=[bm.verts.new((x,y,-t/2)) for x,y in pts]; vt=[bm.verts.new((x,y,t/2)) for x,y in pts]
    n=len(pts)
    for i in range(n): bm.faces.new((vb[i],vb[(i+1)%n],vt[(i+1)%n],vt[i]))
    bm.faces.new(vt); bm.faces.new(list(reversed(vb))); bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    me=bpy.data.meshes.new(name); bm.to_mesh(me); o=bpy.data.objects.new(name,me); sc.collection.objects.link(o)
    if axis=='y': o.rotation_euler=(math.radians(90),0,0)
    elif axis=='x': o.rotation_euler=(0,math.radians(90),0)
    o.location=loc
    if rim>0:
        bv=o.modifiers.new('rim','BEVEL'); bv.width=rim; bv.segments=5; bv.limit_method='ANGLE'; bv.angle_limit=math.radians(40)
    for p in me.polygons: p.use_smooth=True
    o.data.materials.append(mat_); return o
def cyl(name,r,d,loc,mat_,axis='z',v=64,rim=0.4*mm,rot=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=v,radius=r,depth=d,location=loc); o=bpy.context.object; o.name=name
    if axis=='y': o.rotation_euler=(math.radians(90),0,0)
    elif axis=='x': o.rotation_euler=(0,math.radians(90),0)
    if rot: o.rotation_euler=rot
    if rim>0:
        bv=o.modifiers.new('rim','BEVEL'); bv.width=rim; bv.segments=4; bv.limit_method='ANGLE'; bv.angle_limit=math.radians(40)
    bpy.ops.object.shade_smooth(); o.data.materials.append(mat_); return o
def apply_bool(target,cutter,op='DIFFERENCE'):
    bpy.context.view_layer.update()
    bpy.context.view_layer.objects.active=target; md=target.modifiers.new('b','BOOLEAN'); md.object=cutter; md.operation=op; md.solver='EXACT'
    target.modifiers.move(len(target.modifiers)-1,0)
    bpy.ops.object.modifier_apply(modifier=md.name); bpy.data.objects.remove(cutter)

GROUPS={}   # name -> list of objects, exploded by group offset
def G(g,*objs):
    GROUPS.setdefault(g,[]).extend(objs); return objs[0]

# ---------------- dimensions
W,D,H=160*mm,64*mm,124*mm; Z0=4*mm; ZC=Z0+H/2; YF=-D/2
PZ0=Z0+7*mm      # faceplate bottom (panel z=0)
def P(x,pz): return (x*mm, PZ0+pz*mm)

# ---------------- shell
shell=rrect('shell',W,H,18*mm,D,M_shell,(0,0,ZC),'y',rim=5*mm,seg=16)
# lantern well + SOS pocket on top
k=cyl('k',19.5*mm,20*mm,(38*mm,0,Z0+H),M_shell,rim=0); apply_bool(shell,k)
G('shell',shell)
# ---------------- faceplate (graphite with cream print)
FP_T=2.5*mm
fp=rrect('face',150*mm,110*mm,9*mm,FP_T,decal('face',C['face'],'dec_panel.png',C['cream'],150*mm,110*mm,axes='xy',face=(0,0,1)),(0,YF-FP_T/2+0.6*mm,PZ0+55*mm),'y',rim=0.7*mm)
# rotation (90,0,0) maps local +Z -> world -Y (front) and local +Y -> world +Z ; decal uses local x,y with face +Z: correct
G('face',fp)
# ---------------- speaker plate: Fermat-spiral holes, graded diameter (centre big, edge small)
SPX,SPZ=-36*mm,PZ0+60*mm; SP_T=2.2*mm; YP=YF-FP_T+0.6*mm-SP_T/2
plate=rrect('plate',66*mm,66*mm,8*mm,SP_T,decal('plate',C['orange'],'dec_plate2.png',C['ink'],66*mm,66*mm,axes='xy',face=(0,0,1)),(SPX,YP,SPZ),'y',rim=0.5*mm)
# hole field centred 2mm below plate centre (plate local y up = world z)
bm=bmesh.new(); golden=math.pi*(3-math.sqrt(5)); NH=int(os.environ.get('NH','150')); RF=17.2*mm; holes=0
for i in range(NH):
    r=RF*math.sqrt((i+0.5)/NH); a=i*golden; t=r/RF
    hr=(1.0-0.45*t)*mm           # rule: 2.0 mm holes at centre -> 1.1 mm at edge
    cx,cz=r*math.cos(a), r*math.sin(a)-0*mm
    ring=[bm.verts.new((cx+hr*math.cos(2*math.pi*j/14),cz+hr*math.sin(2*math.pi*j/14),z)) for z in (-3*mm,3*mm) for j in range(14)]
    for j in range(14): bm.faces.new((ring[j],ring[(j+1)%14],ring[14+(j+1)%14],ring[14+j]))
    bm.faces.new(ring[14:]); bm.faces.new(list(reversed(ring[:14]))); holes+=1
me=bpy.data.meshes.new('holes'); bmesh.ops.recalc_face_normals(bm,faces=bm.faces); bm.to_mesh(me); hc=bpy.data.objects.new('holes',me); sc.collection.objects.link(hc)
hc.rotation_euler=plate.rotation_euler; hc.location=plate.location; hc.location.z+=0   # same frame as plate
# plate local y maps to world z; hole centre offset (0,-0) -> plate centre... shift field down 0 (decal ring centred at 33mm from top = centre)
apply_bool(plate,hc); print('HOLES',holes)
G('plate',plate)
cone=cyl('cone',24*mm,8*mm,(SPX,YF+4*mm,SPZ),M_cone,axis='y',rim=1*mm); G('speaker',cone)
mag=cyl('magnet',11*mm,10*mm,(SPX,YF+12*mm,SPZ),M_steel,axis='y'); G('speaker',mag)

# ---------------- Torx screw (T10 hexalobular recess), built once, instanced
def torx_screw():
    bm=bmesh.new(); R=2.7*mm; Hh=1.6*mm; n=48
    # pan head profile revolved
    prof=[(0,0),(R,0),(R,Hh*0.45),(R*0.85,Hh*0.85),(R*0.5,Hh),(0,Hh)]
    rings=[]
    for i in range(n):
        a=2*math.pi*i/n; rings.append([bm.verts.new((x*math.cos(a),x*math.sin(a),z)) if x>0 else None for x,z in prof])
    cb=bm.verts.new((0,0,0)); ct=bm.verts.new((0,0,Hh))
    for i in range(n):
        A=rings[i]; B=rings[(i+1)%n]
        bm.faces.new((cb,B[1],A[1]))
        for j in range(1,4): bm.faces.new((A[j],B[j],B[j+1],A[j+1]))
        bm.faces.new((A[4],B[4],ct))
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    me=bpy.data.meshes.new('screw'); bm.to_mesh(me); o=bpy.data.objects.new('screw',me); sc.collection.objects.link(o)
    for p in me.polygons: p.use_smooth=True
    # 6-lobe star cutter
    bs=bmesh.new(); pts=[]
    for i in range(72):
        a=2*math.pi*i/72; r=(0.95+0.32*math.cos(6*a))*mm; pts.append((r*math.cos(a),r*math.sin(a)))
    vb=[bs.verts.new((x,y,0.7*mm)) for x,y in pts]; vt=[bs.verts.new((x,y,3*mm)) for x,y in pts]
    for i in range(72): bs.faces.new((vb[i],vb[(i+1)%72],vt[(i+1)%72],vt[i]))
    bs.faces.new(vt); bs.faces.new(list(reversed(vb))); bmesh.ops.recalc_face_normals(bs,faces=bs.faces)
    m2=bpy.data.meshes.new('star'); bs.to_mesh(m2); st=bpy.data.objects.new('star',m2); sc.collection.objects.link(st)
    apply_bool(o,st); o.data.materials.append(M_steel); return o
SCREW=torx_screw(); SCREW.location=(0,0,-1)  # hidden template
def screw_at(loc,normal,g):
    o=bpy.data.objects.new('scr',SCREW.data); sc.collection.objects.link(o); o.location=loc
    o.rotation_euler=Vector(normal).to_track_quat('Z','Y').to_euler(); G(g,o); return o
for dx in (-27,27):
    for dz in (-27,27): screw_at((SPX+dx*mm,YP-SP_T/2,SPZ+dz*mm),(0,-1,0),'pscrew')
for x in (-69,69):
    for pz in (6,104): screw_at((x*mm,YF-FP_T+0.6*mm,PZ0+pz*mm),(0,-1,0),'fscrew')
SCREW.hide_render=True

# ---------------- tune/dim dial: knurled aluminium
def knurl(name,R,Hk,teeth,mat_,depth=0.035):
    bm=bmesh.new(); r0=[];r1=[]
    for i in range(teeth):
        a=2*math.pi*i/teeth; r=R*(1-depth*((i%4)<2))
        r0.append(bm.verts.new((r*math.cos(a),r*math.sin(a),0))); r1.append(bm.verts.new((r*math.cos(a),r*math.sin(a),Hk*0.82)))
    for i in range(teeth): bm.faces.new((r0[i],r0[(i+1)%teeth],r1[(i+1)%teeth],r1[i]))
    top=[bm.verts.new((R*0.95*math.cos(2*math.pi*i/teeth),R*0.95*math.sin(2*math.pi*i/teeth),Hk)) for i in range(teeth)]
    for i in range(teeth): bm.faces.new((r1[i],r1[(i+1)%teeth],top[(i+1)%teeth],top[i]))
    bm.faces.new(top); bm.faces.new(list(reversed(r0))); bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    me=bpy.data.meshes.new(name); bm.to_mesh(me); o=bpy.data.objects.new(name,me); sc.collection.objects.link(o)
    for p in me.polygons: p.use_smooth=True
    bv=o.modifiers.new('b','BEVEL'); bv.width=0.5*mm; bv.segments=3; bv.limit_method='ANGLE'
    o.data.materials.append(mat_); return o
DX,DZ=38*mm,PZ0+72*mm; YFP=YF-FP_T+0.6*mm
dial=knurl('dial',15.5*mm,13*mm,200,M_alu); dial.rotation_euler=(math.radians(90),0,0); dial.location=(DX,YFP,DZ)
cap=cyl('dialcap',12.5*mm,1.2*mm,(DX,YFP-13*mm,DZ),M_graph,axis='y',rim=0.4*mm)
ind=rrect('ind',1.6*mm,8*mm,0.8*mm,0.6*mm,M_orange,(DX-4.5*mm,YFP-13.7*mm,DZ+4.5*mm),'y',rim=0)
ind.rotation_euler=(math.radians(90),math.radians(45),0)
G('dial',dial,cap,ind)
# ---------------- big buttons LIGHT / RADIO
def button(x,pz,m,icon,ink,g):
    bx,bz=P(x,pz)
    mm_=decal('btn_'+icon,m,icon,ink,11*mm,11*mm,axes='xy',face=(0,0,1)) if icon else None
    o=cyl('btn',8*mm,5*mm,(bx,YFP-2.5*mm,bz),mm_,axis='y',rim=1.2*mm)
    o.rotation_euler=(math.radians(90),0,0)
    ring=cyl('bez',9.4*mm,1.6*mm,(bx,YFP-0.8*mm,bz),M_alu,axis='y',rim=0.4*mm); G(g,o,ring)
button(24,23.5,C['orange'],'ico_sun.png',C['ink'],'btns'); button(52,23.5,C['cream'],'ico_radio.png',C['ink'],'btns')
# ---------------- band slider (AM/FM/WX), knob at FM
sx,sz=P(38,35)
sl=rrect('slider',7*mm,5*mm,1.5*mm,4*mm,M_orange,(sx,YFP-2*mm,sz),'y',rim=0.6*mm); G('btns',sl)
for k in range(3):
    r=rrect('rib',0.6*mm,3.4*mm,0.3*mm,0.6*mm,M_graph,(sx+(k-1)*1.6*mm,YFP-4.1*mm,sz),'y',rim=0); G('btns',r)
# charge LEDs
for i,x in enumerate((49.5,53,56.5)):
    lx,lz=P(x,99.6); G('btns',cyl('led',1.1*mm,1*mm,(lx,YFP-0.4*mm,lz),M_ledon if i<2 else M_ledoff,axis='y',rim=0.3*mm))

# ---------------- top: SOS button + pop-up lantern
TOP=Z0+H
sosm=decal('sos',C['sos'],'ico_sos.png',C['cream'],12*mm,12*mm,axes='xy',face=(0,0,1))
sos=cyl('sos',7*mm,4*mm,(-52*mm,-6*mm,TOP+1.5*mm),sosm,rim=1.2*mm); sring=cyl('sosring',8.6*mm,1.4*mm,(-52*mm,-6*mm,TOP+0.2*mm),M_alu,rim=0.3*mm)
G('sos',sos,sring)
LX=38*mm; up=float(os.environ.get('LUP','1'))
collar=knurl('collar',19.2*mm,5*mm,180,M_alu,0.02); collar.location=(LX,0,TOP-2.5*mm)
diff=cyl('diff',16*mm,40*mm*up+2*mm,(LX,0,TOP+2.5*mm+(40*mm*up)/2-1*mm),M_diff,rim=0.6*mm)
lcap=knurl('lcap',17.5*mm,7*mm,160,M_graph,0.03); lcap.location=(LX,0,TOP+2.5*mm+40*mm*up)
lring=cyl('lring',13*mm,0.8*mm,(LX,0,TOP+2.5*mm+40*mm*up+7.1*mm),M_orange,rim=0.2*mm)
bulb=bpy.data.lights.new('lant','POINT'); bulb.energy=float(os.environ.get('LANTW','0.25'))*up; bulb.color=(1,0.82,0.6); bulb.shadow_soft_size=0.01
lo=bpy.data.objects.new('lant',bulb); sc.collection.objects.link(lo); lo.location=(LX,0,TOP+22*mm*max(up,0.2))
G('lantern',collar,diff,lcap,lring,lo)

# ---------------- crank on the right side, deployed
CX=W/2; HZ=Z0+70*mm; HY=8*mm
hub=cyl('hub',12*mm,5*mm,(CX+2.5*mm,HY,HZ),M_alu,axis='x',rim=0.8*mm)
arm=rrect('arm',52*mm,8*mm,4*mm,4*mm,M_graph,(CX+6.5*mm,HY,HZ-22*mm),'x',rim=0.8*mm)
arm.rotation_euler=(0,math.radians(90),0)
kn=knurl('cknob',6*mm,20*mm,96,M_orange,0.05); kn.rotation_euler=(0,math.radians(90),0); kn.location=(CX+8.5*mm,HY,HZ-44*mm)
G('crank',hub,arm,kn)
# feet
for x in (-62,62):
    for y in (-20,20): G('shell',cyl('foot',5*mm,Z0,(x*mm,y*mm,Z0/2),M_rubber,rim=0.8*mm))

# ---------------- back plate + label + port
bp=rrect('back',130*mm,96*mm,10*mm,2*mm,decal('back',C['shell'],'dec_back.png',C['ink'],120*mm,80*mm,axes='xy',face=(0,0,1),flipu=False),(0,D/2+0.4*mm,ZC),'y',rim=0.6*mm)
bp.rotation_euler=(math.radians(90),0,math.radians(180))   # local +Z -> world +Y (rear), text upright
G('back',bp)
for x in (-58,58):
    for z in (-41,41): screw_at((x*mm,D/2+1.4*mm,ZC+z*mm),(0,1,0),'back')
port=rrect('port',9.5*mm,3.4*mm,1.6*mm,2*mm,M_screwhole,(0,D/2+1.0*mm,Z0+9*mm),'y',rim=0.3*mm); G('back',port)

# ---------------- internals (seen only in the exploded view)
INT=EXPL>0 or os.environ.get('INT')=='1'
if INT:
    pcb=rrect('pcb',140*mm,100*mm,6*mm,1.6*mm,M_pcb,(0,-6*mm,ZC),'y',rim=0.2*mm); G('board',pcb)
    random.seed(4)
    for i in range(14):
        G('board',rrect('chip',random.choice([6,8,10,12])*mm,random.choice([4,6,8])*mm,0.6*mm,1.6*mm,M_chip,(random.uniform(-0.05,0.06),-7.6*mm,ZC+random.uniform(-0.04,0.04)),'y',rim=0.2*mm))
    for x in (-34,34):
        G('cells',cyl('cell',9.3*mm,65*mm,(x*mm,14*mm,Z0+38*mm),M_cell,axis='x',rim=1*mm))
        G('cells',cyl('cap',9.4*mm,3*mm,(x*mm+33*mm,14*mm,Z0+38*mm),M_steel,axis='x',rim=0.6*mm))

# ---------------- explode
OFF={'btns':(0,-190,0),'dial':(0,-190,0),'pscrew':(0,-166,0),'plate':(0,-150,0),'fscrew':(0,-134,0),'face':(0,-118,0),'speaker':(0,-92,0),
     'board':(0,-62,0),'cells':(0,52,0),'shell':(0,0,0),'back':(0,96,0),'crank':(50,0,0),'lantern':(0,0,50),'sos':(0,0,34)}
if EXPL>0:
    for g,objs in GROUPS.items():
        o3=Vector(OFF.get(g,(0,0,0)))*mm*EXPL
        for o in objs: o.location+=o3


# ================= MANUAL MODE: clay + freestyle lines, highlighted group, section cut, callout projection
CLAY=os.environ.get('CLAY')=='1'; HL=[g for g in os.environ.get('HL','').split(',') if g]
if os.environ.get('SECT')=='1':
    cut=bpy.data.objects.new('cut',bpy.data.meshes.new('cutm')); sc.collection.objects.link(cut)
    import bmesh as _bm; bb=_bm.new(); _bm.ops.create_cube(bb,size=1.0); bb.to_mesh(cut.data); bb.free()
    cut.scale=(0.3,0.4,0.4); cut.location=(0.15+0.0005,0,0.1); cut.hide_render=True
    for o in list(sc.objects):
        if o.type=='MESH' and o.name not in ('cyc','cut') and not o.name.startswith('cell') and not o.name.startswith('cap'):
            m=o.modifiers.new('sect','BOOLEAN'); m.object=cut; m.operation='DIFFERENCE'
if CLAY:
    def flat(name,col):
        m=bpy.data.materials.new(name); m.use_nodes=True; b=m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value=hx(col); b.inputs['Roughness'].default_value=0.75
        try: b.inputs['Specular IOR Level'].default_value=0.2
        except Exception: pass
        return m
    WHITE=flat('clay','#F4F1EA'); ORG=flat('hl','#FF5A1F'); DARK=flat('dk','#BDB8AE')
    hlobjs={id(o) for g in HL for o in GROUPS.get(g,[])}
    for o in sc.objects:
        if o.type!='MESH' or o.name=='cyc': continue
        o.data.materials.clear(); o.data.materials.append(ORG if id(o) in hlobjs else WHITE)
        o.material_slots[0].link='OBJECT'; o.material_slots[0].material=ORG if id(o) in hlobjs else WHITE
    sc.render.use_freestyle=True; vl=sc.view_layers[0]; vl.use_freestyle=True
    fs=vl.freestyle_settings; fs.crease_angle=math.radians(134)
    ls=fs.linesets[0] if fs.linesets else fs.linesets.new('L'); ls.select_by_visibility=True; ls.visibility='VISIBLE'
    ls.select_silhouette=True; ls.select_border=True; ls.select_crease=True
    ls.linestyle=ls.linestyle or bpy.data.linestyles.new('LS'); ls.linestyle.color=(0.04,0.04,0.045); ls.linestyle.thickness=float(os.environ.get('LW','1.4'))
    sc.render.line_thickness_mode='ABSOLUTE'

# ---------------- studio: Tarka cyclorama with a fine grid
def gridmat(name):
    m,b=mat(name,C['floor'],0.85); N=m.node_tree.nodes; L=m.node_tree.links; tc=N.new('ShaderNodeTexCoord')
    br=N.new('ShaderNodeTexBrick'); br.offset=0; br.squash=1; br.inputs['Scale'].default_value=1.0
    br.inputs['Brick Width'].default_value=0.02; br.inputs['Row Height'].default_value=0.02; br.inputs['Mortar Size'].default_value=0.0003
    for k in ('Color1','Color2'): br.inputs[k].default_value=hx(C['floor'])
    br.inputs['Mortar'].default_value=hx(C['grid']); L.new(tc.outputs['Object'],br.inputs['Vector']); L.new(br.outputs['Color'],b.inputs['Base Color']); return m
bm=bmesh.new(); prof=[]
for i in range(25):
    a=math.radians(90*i/24); prof.append((0.35-0.25*math.sin(a)+0.0, 0.25-0.25*math.cos(a)))   # (y,z) cove radius 0.25 behind product
prof=[(-1.2,0)]+[(y,z) for (y,z) in reversed(prof)]
prof=[(-1.2,0.0)]+[(0.16+0.25*math.sin(math.radians(90*i/24)),0.25-0.25*math.cos(math.radians(90*i/24))) for i in range(25)]+[(0.41,1.2)]
rows=[[bm.verts.new((x,y,z)) for (y,z) in prof] for x in (-1.5,1.5)]
for j in range(len(prof)-1): bm.faces.new((rows[0][j],rows[1][j],rows[1][j+1],rows[0][j+1]))
me=bpy.data.meshes.new('cyc'); bm.to_mesh(me); cy=bpy.data.objects.new('cyc',me); sc.collection.objects.link(cy)
for p in me.polygons: p.use_smooth=True
cy.data.materials.append(gridmat('floor'))
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=True; w.node_tree.nodes['Background'].inputs['Color'].default_value=hx(C['floor']); w.node_tree.nodes['Background'].inputs['Strength'].default_value=float(os.environ.get('WSTR','0.1'))
def area(loc,size,energy,col='#ffffff',tgt=(0,0,0.06)):
    l=bpy.data.lights.new('a','AREA'); l.size=size; l.energy=energy; l.color=hx(col)[:3]; o=bpy.data.objects.new('a',l); sc.collection.objects.link(o); o.location=loc
    o.rotation_euler=(Vector(tgt)-Vector(loc)).to_track_quat('-Z','Y').to_euler()
K=float(os.environ.get('KEY','4'))
area((-0.35,-0.45,0.5),0.45,K); area((0.5,-0.25,0.25),0.35,K*0.45,'#eaf3ff'); area((0.2,0.35,0.45),0.35,K*0.6)
cam=bpy.data.cameras.new('c'); co=bpy.data.objects.new('c',cam); sc.collection.objects.link(co); sc.camera=co
def look(loc,tgt,lens,f=None):
    co.location=loc; d=Vector(tgt)-Vector(loc); co.rotation_euler=d.to_track_quat('-Z','Y').to_euler(); cam.lens=lens
    if f: cam.dof.use_dof=True; cam.dof.aperture_fstop=f; cam.dof.focus_distance=d.length
def res(x,y): sc.render.resolution_x=x; sc.render.resolution_y=y
if SHOT=='hero': look((0.38,-0.62,0.28),(0.004,0,0.078),85,11); res(RES,int(RES*0.8))
elif SHOT=='front': cy.hide_render=True; sc.render.film_transparent=True; look((0,-1.2,ZC+0.02),(0,0,ZC+0.02),100); cam.type='ORTHO'; cam.ortho_scale=0.235; res(RES,RES)
elif SHOT=='back': cy.hide_render=True; sc.render.film_transparent=True; look((0,1.2,ZC+0.02),(0,0,ZC+0.02),100); cam.type='ORTHO'; cam.ortho_scale=0.235; res(RES,RES)
elif SHOT=='dial': look((0.12,-0.26,0.16),(0.03,-0.035,0.075),100,6); res(RES,RES)
elif SHOT=='speaker': look((-0.10,-0.20,0.12),(-0.036,-0.035,0.071),100,6); res(RES,RES)
elif SHOT=='top': look((0.16,-0.24,0.32),(0.02,0,0.12),100,8); res(RES,RES)
elif SHOT=='exploded': look((0.78,-0.30,0.40),(0.0,-0.02,0.09),70,16); res(RES,int(RES*0.8))
elif SHOT=='m_iso': cy.hide_render=True; sc.render.film_transparent=True; look((0.62,-0.62+float(os.environ.get('TY','0')),0.46),(0,float(os.environ.get('TY','0')),ZC),80); cam.type='ORTHO'; cam.ortho_scale=float(os.environ.get('OS','0.30')); res(RES,int(RES*float(os.environ.get('AR','0.8'))))
elif SHOT=='m_isoback': cy.hide_render=True; sc.render.film_transparent=True; look((-0.62,0.62,0.46),(0,0,ZC),80); cam.type='ORTHO'; cam.ortho_scale=float(os.environ.get('OS','0.30')); res(RES,int(RES*0.8))
elif SHOT=='m_front': cy.hide_render=True; sc.render.film_transparent=True; look((0,-1.2,ZC+0.01),(0,0,ZC+0.01),100); cam.type='ORTHO'; cam.ortho_scale=0.22; res(RES,RES)
elif SHOT=='m_side': cy.hide_render=True; sc.render.film_transparent=True; look((1.2,0,ZC+0.01),(0,0,ZC+0.01),100); cam.type='ORTHO'; cam.ortho_scale=0.22; res(RES,RES)
elif SHOT=='m_top': cy.hide_render=True; sc.render.film_transparent=True; look((0,-0.0001,1.2),(0,0,0),100); cam.type='ORTHO'; cam.ortho_scale=0.22; res(RES,RES)
elif SHOT=='m_sect': cy.hide_render=True; sc.render.film_transparent=True; look((1.2,-0.0,ZC+0.01),(0,0,ZC+0.01),100); cam.type='ORTHO'; cam.ortho_scale=0.22; cam.clip_start=1.2-float(os.environ.get('CUTX','0.0')); cam.clip_end=3; res(RES,RES)
elif SHOT=='m_sectiso': cy.hide_render=True; sc.render.film_transparent=True; look((0.62,-0.5,0.40),(0,0,ZC),80); cam.type='ORTHO'; cam.ortho_scale=0.26; res(RES,int(RES*0.8))
elif SHOT=='side': look((0.45,-0.42,0.18),(0.03,0,0.07),85,11); res(RES,RES)
sc.cycles.device='CPU'; sc.render.engine='CYCLES'; sc.cycles.samples=SPP; sc.cycles.use_denoising=True
sc.cycles.max_bounces=6; sc.cycles.transmission_bounces=6
sc.view_settings.view_transform=os.environ.get('VT','Standard'); sc.view_settings.exposure=float(os.environ.get('EXP','0'))

# callout anchors: projected centre of each group
import json as _json
from bpy_extras.object_utils import world_to_camera_view as _w2c
sc.view_layers[0].update(); A={}
for g,objs in GROUPS.items():
    pts=[]
    for o in objs:
        if o.type!='MESH': continue
        for v in o.bound_box: pts.append(o.matrix_world@Vector(v))
    if not pts: continue
    c=sum(pts,Vector())/len(pts); p=_w2c(sc,co,c); A[g]=[round(p.x,4),round(1-p.y,4)]
_json.dump(A,open(os.path.abspath(OUT)+'.json','w'))
sc.render.filepath=os.path.abspath(OUT); bpy.ops.render.render(write_still=True)
