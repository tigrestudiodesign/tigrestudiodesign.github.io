import sys, os, math
import bpy, bmesh, mathutils
OUT=sys.argv[sys.argv.index('--')+1]; SHOT=sys.argv[sys.argv.index('--')+2]
RES=int(os.environ.get('RES','1200')); SPP=int(os.environ.get('SPP','48')); PAL=os.environ.get('PAL','ORIG')
bpy.ops.wm.read_factory_settings(use_empty=True); sc=bpy.context.scene
S=0.45/169.0
def X(px): return px*S
def Y(py): return -py*S
def hx(h): h=h.lstrip('#'); c=[int(h[i:i+2],16)/255 for i in (0,2,4)]; return tuple(((v/12.92) if v<=0.04045 else ((v+0.055)/1.055)**2.4) for v in c)+(1,)
# ---------------- palettes (colour per role)
PALS={
'ORIG':dict(lilac='#d6d1dc',sage='#c3dcc2',yellow='#efcf4e',navy='#1f3a8a',orange='#d9822b',tile='#dcd77c',blue='#2a5d8f',red='#c23a2e',pinkline='#e9a3a8',cream='#ece2c2',green='#2f8a5e',pink='#d9a7aa',grout='#bdb8a6'),
'STONE':dict(lilac='#d8d4cc',sage='#c9c4b8',yellow='#e4ddcf',navy='#2b2b2b',orange='#9b8f7c',tile='#e9e6df',blue='#5b5650',red='#3a3a38',pinkline='#b9b1a3',cream='#efebe3',green='#6d6a63',pink='#cfc7ba',grout='#a8a296'),
'NIGHT':dict(lilac='#2c2a36',sage='#24302c',yellow='#3a3326',navy='#c9a54a',orange='#c4532e',tile='#2f3a33',blue='#1c2c44',red='#8c2a24',pinkline='#c9a54a',cream='#3b372f',green='#c9a54a',pink='#4a3236',grout='#15181a'),
}
P=PALS[PAL]
# ---------------- materials
def principled(name,col,rough,coat=0,spec=0.5,metal=0,sheen=0):
    m=bpy.data.materials.new(name); m.use_nodes=True; b=m.node_tree.nodes['Principled BSDF']

import random
def NN(m): return m.node_tree.nodes, m.node_tree.links
def principled(name,col,rough,coat=0,spec=0.5,metal=0,sheen=0):
    m=bpy.data.materials.new(name); m.use_nodes=True; b=m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value=hx(col); b.inputs['Roughness'].default_value=rough
    b.inputs['Coat Weight'].default_value=coat; b.inputs['Coat Roughness'].default_value=0.04
    b.inputs['Metallic'].default_value=metal; b.inputs['Sheen Weight'].default_value=sheen
    return m,b
def coords(m, scale=1.0):
    N,L=NN(m); tc=N.new('ShaderNodeTexCoord'); mp=N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value=(scale,)*3; L.new(tc.outputs['Object'],mp.inputs['Vector']); return mp.outputs['Vector'],tc
def noise(m,vec,scale,detail=6,dist=0.0,rough=0.5):
    N,L=NN(m); n=N.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value=scale; n.inputs['Detail'].default_value=detail; n.inputs['Distortion'].default_value=dist; n.inputs['Roughness'].default_value=rough; L.new(vec,n.inputs['Vector']); return n.outputs['Fac']
def mixrgb(m,fac,a,b):
    N,L=NN(m); mx=N.new('ShaderNodeMix'); mx.data_type='RGBA'
    for i,v in ((6,a),(7,b)):
        if isinstance(v,tuple): mx.inputs[i].default_value=v
        else: L.new(v,mx.inputs[i])
    if isinstance(fac,float): mx.inputs['Factor'].default_value=fac
    else: L.new(fac,mx.inputs['Factor'])
    return mx.outputs[2]
def mr(m,v,a0,a1,b0,b1,clamp=True):
    N,L=NN(m); r=N.new('ShaderNodeMapRange'); r.clamp=clamp
    for k,x in (('From Min',a0),('From Max',a1),('To Min',b0),('To Max',b1)): r.inputs[k].default_value=x
    L.new(v,r.inputs['Value']); return r.outputs['Result']
def bump(m,b,h,strength,dist):
    N,L=NN(m); bp=N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value=strength; bp.inputs['Distance'].default_value=dist; L.new(h,bp.inputs['Height']); L.new(bp.outputs['Normal'],b.inputs['Normal']); return bp
def shade(c,k): return tuple(min(1,x*k) for x in c[:3])+(1,)
def linoleum(name,col):
    """Forbo-style furniture linoleum: stretched marbling, linseed grain, matte with a soft sheen"""
    m,b=principled(name,col,0.6,sheen=0.15); v,_=coords(m)
    N,L=NN(m); mp=N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value=(1.0,2.5,1.0); L.new(v,mp.inputs['Vector'])
    marb=noise(m,mp.outputs['Vector'],7,12,3.0,0.6)
    c=hx(col); col2=mixrgb(m,mr(m,marb,0.4,0.75,0,0.6),shade(c,0.9),shade(c,1.08))
    fine=noise(m,v,900,4)
    L.new(mixrgb(m,mr(m,fine,0.3,0.7,0,0.12),col2,shade(c,0.8)),b.inputs['Base Color'])
    L.new(mr(m,fine,0,1,0.5,0.66),b.inputs['Roughness'])
    bump(m,b,fine,0.06,0.0003); return m
def lacquer(name,col,gloss=False):
    m,b=principled(name,col,0.12 if gloss else 0.32,coat=1.0 if gloss else 0.35)
    b.inputs['Coat Roughness'].default_value=0.03 if gloss else 0.12
    v,_=coords(m); peel=noise(m,v,1600,3); bump(m,b,peel,0.035 if gloss else 0.05,0.0002)
    N,L=NN(m); L.new(mixrgb(m,mr(m,noise(m,v,4,3),0.3,0.7,0,0.08),hx(col),shade(hx(col),0.85)),b.inputs['Base Color'])
    return m
def hdpe(name,col,fleck='#ffffff'):
    """recycled HDPE sheet: swirled base + multi-size flecks in three tones"""
    m,b=principled(name,col,0.48,coat=0.15); v,_=coords(m); N,L=NN(m)
    sw=noise(m,v,14,10,6.0,0.65); base=mixrgb(m,mr(m,sw,0.35,0.7,0,0.5),shade(hx(col),0.88),shade(hx(col),1.1))
    out=base
    out=chips(m,v,out,((120,0.12,0.6,hx(fleck)),(320,0.12,0.55,shade(hx(col),0.55)),(70,0.15,0.88,hx('#f4efe4'))))
    L.new(out,b.inputs['Base Color']); bump(m,b,noise(m,v,1200,3),0.05,0.0002); return m
def chips(m,v,out,specs):
    """angular aggregate: voronoi cells shrunk by distance-to-edge, randomly selected"""
    N,L=NN(m)
    for sc_,th,p,c in specs:
        vo=N.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value=sc_; vo.inputs['Randomness'].default_value=1.0; L.new(v,vo.inputs['Vector'])
        ve=N.new('ShaderNodeTexVoronoi'); ve.feature='DISTANCE_TO_EDGE'; ve.inputs['Scale'].default_value=sc_; ve.inputs['Randomness'].default_value=1.0; L.new(v,ve.inputs['Vector'])
        wn=N.new('ShaderNodeTexWhiteNoise'); L.new(vo.outputs['Color'],wn.inputs['Vector'])
        gt=N.new('ShaderNodeMath'); gt.operation='GREATER_THAN'; gt.inputs[1].default_value=p; L.new(wn.outputs['Value'],gt.inputs[0])
        lt=N.new('ShaderNodeMath'); lt.operation='GREATER_THAN'; lt.inputs[1].default_value=th; L.new(ve.outputs['Distance'],lt.inputs[0])
        f=N.new('ShaderNodeMath'); f.operation='MULTIPLY'; L.new(gt.outputs[0],f.inputs[0]); L.new(lt.outputs[0],f.inputs[1])
        cv=N.new('ShaderNodeTexNoise'); cv.inputs['Scale'].default_value=sc_*3; L.new(v,cv.inputs['Vector'])
        cc=mixrgb(m,mr(m,cv.outputs['Fac'],0.3,0.7,0,0.35),c,shade(c,0.75))
        out=mixrgb(m,f.outputs[0],out,cc)
    return out
def terrazzo(name,col,chip='#6b7f5a'):
    """cast terrazzo: two chip sizes, three aggregates, honed + sealed"""
    m,b=principled(name,col,0.22,coat=0.5); v,_=coords(m); N,L=NN(m)
    out=mixrgb(m,mr(m,noise(m,v,700,6),0.3,0.7,0,0.3),hx(col),shade(hx(col),0.86))
    out=chips(m,v,out,((70,0.13,0.76,hx(chip)),(70,0.15,0.92,hx('#8b8580')),(150,0.11,0.72,hx('#f6f3ec')),(150,0.13,0.9,hx('#c96d4b')),(320,0.12,0.8,hx('#3a3a38'))))
    L.new(out,b.inputs['Base Color']); bump(m,b,noise(m,v,800,4),0.03,0.0002); return m
def glazed(name,col):
    """handmade glazed tile: per-tile tone shift, glaze pooling, wavy surface, faint crazing"""
    m,b=principled(name,col,0.05,coat=1.0); b.inputs['Coat Roughness'].default_value=0.02
    v,_=coords(m); N,L=NN(m); oi=N.new('ShaderNodeObjectInfo')
    tone=mr(m,oi.outputs['Random'],0,1,0.78,1.12)
    c1=N.new('ShaderNodeMix'); c1.data_type='RGBA'; c1.blend_type='MULTIPLY'; c1.inputs['Factor'].default_value=1.0; c1.inputs[6].default_value=hx(col)
    cv=N.new('ShaderNodeCombineColor'); L.new(tone,cv.inputs[0]); L.new(tone,cv.inputs[1]); L.new(tone,cv.inputs[2]); L.new(cv.outputs[0],c1.inputs[7])
    pool=noise(m,v,22,8,1.5)
    col2=mixrgb(m,mr(m,pool,0.35,0.75,0,0.45),c1.outputs[2],shade(hx(col),0.72))
    vo=N.new('ShaderNodeTexVoronoi'); vo.feature='DISTANCE_TO_EDGE'; vo.inputs['Scale'].default_value=60; L.new(v,vo.inputs['Vector'])
    cr=mr(m,vo.outputs['Distance'],0.0,0.015,1,0)
    ao=N.new('ShaderNodeAmbientOcclusion'); ao.inputs['Distance'].default_value=0.006; ao.samples=8
    col3=mixrgb(m,mr(m,ao.outputs['AO'],0.4,1.0,0.6,0.0),col2,shade(hx(col),0.55))
    L.new(mixrgb(m,mr(m,cr,0,1,0,0.15),col3,shade(hx(col),0.6)),b.inputs['Base Color'])
    bump(m,b,pool,0.12,0.0012); return m
def grout_mat(col):
    m,b=principled('grout',col,0.95); v,_=coords(m); s=noise(m,v,3000,2)
    N,L=NN(m); L.new(mixrgb(m,mr(m,s,0.3,0.7,0,0.4),hx(col),shade(hx(col),0.75)),b.inputs['Base Color']); bump(m,b,s,0.3,0.0003); return m
def plyedge():
    """birch ply edge: 1.5 mm veneers, each with its own grain, dark glue lines"""
    m,b=principled('ply','#d9c49c',0.55); v,tc=coords(m); N,L=NN(m)
    sep=N.new('ShaderNodeSeparateXYZ'); L.new(v,sep.inputs[0])
    lay=N.new('ShaderNodeMath'); lay.operation='MULTIPLY'; lay.inputs[1].default_value=1/0.0015; L.new(sep.outputs['Z'],lay.inputs[0])
    fr=N.new('ShaderNodeMath'); fr.operation='FRACT'; L.new(lay.outputs[0],fr.inputs[0])
    glue=mr(m,fr.outputs[0],0.0,0.09,1,0)
    fl=N.new('ShaderNodeMath'); fl.operation='FLOOR'; L.new(lay.outputs[0],fl.inputs[0])
    wn=N.new('ShaderNodeTexWhiteNoise'); wn.noise_dimensions='1D'; L.new(fl.outputs[0],wn.inputs['W'])
    gr=noise(m,v,260,6,3.0)
    base=mixrgb(m,mr(m,gr,0.3,0.7,0,0.5),hx('#e3cfa6'),hx('#c9ad7c'))
    base=mixrgb(m,mr(m,wn.outputs['Value'],0,1,0,0.35),base,hx('#b8935e'))
    L.new(mixrgb(m,glue,base,hx('#6a5232')),b.inputs['Base Color']); bump(m,b,glue,0.25,0.0002); return m

M=dict(
 lilac=linoleum('lino_lilac',P['lilac']), sage=linoleum('lino_sage',P['sage']), yellow=linoleum('lino_yellow',P['yellow']),
 navy=linoleum('lino_navy',P['navy']), orangeinlay=linoleum('lino_orange',P['orange']), blueinlay=linoleum('lino_blue',P['blue']), pinkline=linoleum('lino_pink',P['pinkline']),
 orange=hdpe('hdpe_orange',P['orange'],'#f3c79a'), blue=hdpe('hdpe_blue',P['blue'],'#9fc2e6'), navyleg=lacquer('lac_navy',P['navy']),
 red=lacquer('lac_red',P['red'],gloss=True), pink=lacquer('lac_pink',P['pink']),
 tile=glazed('tile',P['tile']), grout=grout_mat(P['grout']),
 cream=terrazzo('terrazzo',P['cream'],P['green']), green=lacquer('lac_green',P['green'],gloss=True), ply=plyedge())

# ---------------- geometry helpers
def box(name,x0,x1,y0,y1,z0,z1,mat,bevel=0.0015,side=None):
    bpy.ops.mesh.primitive_cube_add(size=1); o=bpy.context.object; o.name=name
    o.location=((x0+x1)/2,(y0+y1)/2,(z0+z1)/2); o.scale=(abs(x1-x0),abs(y1-y0),abs(z1-z0))
    bpy.ops.object.transform_apply(scale=True)
    if bevel: bv=o.modifiers.new('b','BEVEL'); bv.width=bevel; bv.segments=3; bv.limit_method='ANGLE'
    o.data.materials.append(mat)
    if side:   # ply edge on vertical faces of tops
        o.data.materials.append(side)
        for p in o.data.polygons:
            if abs(p.normal.z)<0.5: p.material_index=1
    bpy.ops.object.shade_smooth(); return o
def top(name,px0,px1,py0,py1,mat,cuts=()):
    o=box(name,X(px0),X(px1),Y(py1),Y(py0),0.42,0.45,mat,0.001,M['ply'])
    for (a,b_,c,d) in cuts:
        bpy.ops.mesh.primitive_cube_add(size=1); k=bpy.context.object; k.location=((X(a)+X(b_))/2,(Y(c)+Y(d))/2,0.435); k.scale=(abs(X(b_)-X(a))+0.0005,abs(Y(d)-Y(c))+0.0005,0.06)
        md=o.modifiers.new('cut','BOOLEAN'); md.object=k; md.operation='DIFFERENCE'; o.modifiers.move(len(o.modifiers)-1,0); k.hide_render=True; k.hide_viewport=True
    return o
def inlay(name,px0,px1,py0,py1,mat):
    return box(name,X(px0),X(px1),Y(py1),Y(py0),0.4501,0.4503,mat,0)
H0,H1=0.0,0.42

GROUP={}; _seen=set()
# ---- LILAC table (front-left): px 277-446, py 192-361
top('lilac_top',277,446,192,361,M['lilac'],cuts=[(337,447,347,362)])
inlay('lil_navy',327,358,192,223,M['navy']); inlay('lil_orange',320,326,192,275,M['orangeinlay'])
box('orange_leg',X(319),X(327),Y(361-20),Y(230),H0,H1,M['orange'],0.002)
box('orange_navy',X(327),X(337),Y(361-20),Y(230),H0,H1,M['navyleg'],0.002)
# tiled slab at front-right, full height, faces front
tx0,tx1=X(337),X(446); ty0,ty1=Y(361),Y(347)
box('tile_core',tx0,tx1,ty0+0.004,ty1,H0,0.45,M['grout'],0.001)
nc,nr=4,7; tw=(tx1-tx0)/nc; th=0.45/nr
for i in range(nc):
    for j in range(nr):
        box(f'tile_{i}_{j}',tx0+i*tw+0.0012,tx0+(i+1)*tw-0.0012,ty0-0.002,ty0+0.006,j*th+0.0012,(j+1)*th-0.0012,M['tile'],0.0012)
        box(f'tilet_{i}_{j}',tx0+i*tw+0.0015,tx0+(i+1)*tw-0.0015,ty0+0.004,ty1,0.45-0.0001,0.4515,M['tile'],0.0) if j==nr-1 else None
GROUP['lilac']=[o for o in sc.objects if o.name not in _seen]; _seen=set(o.name for o in sc.objects)
# ---- SAGE table (back): px 369-538, py 17-185
top('sage_top',369,538,17,185,M['sage'],cuts=[(452,539,177,186)])
inlay('sage_pink',425,538,170,177,M['pinkline'])
# blue arc inlay (quarter ring) centred (452,100) r 80, width 12
bm=bmesh.new(); cx,cy=452,100; segs=48; ro,ri=80,68; vs=[]
for k in range(segs+1):
    a=math.pi+k*(math.pi/2)/segs
    vs.append((bm.verts.new((X(cx+ro*math.cos(a)),Y(cy+ro*math.sin(a)),0.4502)),bm.verts.new((X(cx+ri*math.cos(a)),Y(cy+ri*math.sin(a)),0.4502))))
for k in range(segs): bm.faces.new((vs[k][0],vs[k+1][0],vs[k+1][1],vs[k][1]))
me=bpy.data.meshes.new('arc'); bm.to_mesh(me); arc=bpy.data.objects.new('arc',me); sc.collection.objects.link(arc); arc.data.materials.append(M['blueinlay'])
# blue rounded slab (left, back half), rounded front end
bx0,bx1=X(372),X(398); by_back,by_front=Y(19),Y(101)
box('blue_slab',bx0,bx1,by_front+0.0,by_back,H0,H1,M['blue'],0.002)
bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=(bx1-bx0)/2,depth=H1,location=((bx0+bx1)/2,by_front,H1/2)); c=bpy.context.object; c.data.materials.append(M['blue']); bpy.ops.object.shade_smooth()
# red gloss slab (front-right, thin), top showing as red strip
box('red_slab',X(452),X(538),Y(185),Y(177),H0,0.45,M['red'],0.0015)
GROUP['sage']=[o for o in sc.objects if o.name not in _seen]; _seen=set(o.name for o in sc.objects)
# ---- YELLOW table (right): px 457-626, py 199-368
top('yellow_top',457,626,199,368,M['yellow'],cuts=[(457,490,255,369)])
inlay('yel_pink',613,626,199,368,M['pinkline'])
# cream terrazzo post + green stripe, full height
box('cream_post',X(458),X(481),Y(368),Y(255),H0,0.45,M['cream'],0.002)
box('green_strip',X(481),X(489),Y(368),Y(255),H0,0.45,M['green'],0.0015)
# fluted pink curtain panel on right side, with scalloped top edge
fx0,fx1=X(604),X(626); fy0,fy1=Y(368),Y(199)
nfl=11; seg=(fy1-fy0)/nfl
for k in range(nfl):
    yc=fy0+(k+0.5)*seg
    bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=seg*0.55,depth=0.42,location=(fx1-seg*0.45,yc,0.21)); o=bpy.context.object; o.scale=(0.8,1,1); o.data.materials.append(M['pink']); bpy.ops.object.shade_smooth()
box('pink_back',fx0,fx1-seg*0.4,fy0,fy1,H0,0.42,M['pink'],0.0015)
GROUP['yellow']=[o for o in sc.objects if o.name not in _seen]

if SHOT=='apart':
    for k,d in (('lilac',(-0.3,-0.08,0)),('sage',(0.04,0.32,0)),('yellow',(0.32,-0.14,0))):
        for o in GROUP[k]:
            if o.parent is None: o.location=(o.location[0]+d[0],o.location[1]+d[1],o.location[2]+d[2])


if SHOT=='chips':
    for o in list(sc.objects): o.hide_render=True
    order=['lilac','sage','yellow','navy','tile','orange','blue','red','pink','cream','green','blueinlay']
    for k,key in enumerate(order):
        cx=X(450)-0.165+(k%4)*0.11; cy=Y(190)+0.11-(k//4)*0.11
        bpy.ops.mesh.primitive_cube_add(size=1,location=(cx,cy,0.009)); o=bpy.context.object; o.scale=(0.09,0.09,0.018); bpy.ops.object.transform_apply(scale=True)
        bv=o.modifiers.new('b','BEVEL'); bv.width=0.003; bv.segments=5; bpy.ops.object.shade_smooth(); o.data.materials.append(M[key])
# ---------------- studio: limewash wall, oak floor, window light with mullion shadows
CX=X(450); CY=Y(190)
def limewash(key='WALL',dflt='#ddd2c2',rough=0.95):
    m,b=principled('wall'+key,os.environ.get(key,dflt),rough); v,_=coords(m); N,L=NN(m)
    cl=noise(m,v,1.6,10,0.5,0.7); c=hx(os.environ.get(key,dflt))
    L.new(mixrgb(m,mr(m,cl,0.3,0.7,0,1),shade(c,0.9),shade(c,1.06)),b.inputs['Base Color']); bump(m,b,noise(m,v,40,6),0.12,0.002); return m
def oak():
    m,b=principled('oak','#b8916a',0.45,coat=0.2); b.inputs['Coat Roughness'].default_value=0.25; v,_=coords(m); N,L=NN(m)
    sep=N.new('ShaderNodeSeparateXYZ'); L.new(v,sep.inputs[0])
    pw=0.19; dv=N.new('ShaderNodeMath'); dv.operation='DIVIDE'; dv.inputs[1].default_value=pw; L.new(sep.outputs['X'],dv.inputs[0])
    pl=N.new('ShaderNodeMath'); pl.operation='FLOOR'; L.new(dv.outputs[0],pl.inputs[0])
    wn=N.new('ShaderNodeTexWhiteNoise'); wn.noise_dimensions='1D'; L.new(pl.outputs[0],wn.inputs['W'])
    sh=N.new('ShaderNodeMath'); sh.operation='MULTIPLY'; sh.inputs[1].default_value=11; L.new(wn.outputs['Value'],sh.inputs[0])
    off=N.new('ShaderNodeCombineXYZ'); L.new(sh.outputs[0],off.inputs['Y']); L.new(sh.outputs[0],off.inputs['Z'])
    vv=N.new('ShaderNodeVectorMath'); L.new(v,vv.inputs[0]); L.new(off.outputs[0],vv.inputs[1])
    mp=N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value=(32,1.1,32); L.new(vv.outputs[0],mp.inputs['Vector'])
    gr=noise(m,mp.outputs['Vector'],1.0,10,1.2,0.6)
    fine=noise(m,mp.outputs['Vector'],6.0,4,0.5)
    fr=N.new('ShaderNodeMath'); fr.operation='FRACT'; L.new(dv.outputs[0],fr.inputs[0]); seam=mr(m,fr.outputs[0],0.0,0.006,1,0)
    base=mixrgb(m,mr(m,gr,0.35,0.65,0,1),hx(os.environ.get('OAK','#c9a274')),hx(os.environ.get('OAK2','#9a6f45')))
    base=mixrgb(m,mr(m,fine,0.3,0.7,0,0.25),base,hx('#7d5a38'))
    base=mixrgb(m,mr(m,wn.outputs['Value'],0,1,0,0.25),base,hx('#b48a5c'))
    L.new(mixrgb(m,seam,base,hx('#3d2b1b')),b.inputs['Base Color']); bump(m,b,gr,0.08,0.0006); return m
bpy.ops.mesh.primitive_plane_add(size=12,location=(CX,CY,0)); fl=bpy.context.object; fl.data.materials.append(oak() if os.environ.get('FLOORMAT','cement')=='oak' else limewash('FLOOR','#c9bca9',0.7))
bpy.ops.mesh.primitive_plane_add(size=12,location=(CX,CY+0.75,3)); wl=bpy.context.object; wl.rotation_euler=(math.radians(90),0,0); wl.data.materials.append(limewash())
w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=True; w.node_tree.nodes['Background'].inputs['Color'].default_value=hx(os.environ.get('WORLD','#f2ece2')); w.node_tree.nodes['Background'].inputs['Strength'].default_value=float(os.environ.get('WSTR','0.08'))
sun=bpy.data.lights.new('sun','SUN'); sun.energy=float(os.environ.get('SUN','4.2')); sun.angle=math.radians(0.35); sun.color=hx(os.environ.get('SUNC','#ffe7c9'))[:3]
so=bpy.data.objects.new('sun',sun); sc.collection.objects.link(so)
sdir=mathutils.Vector((-0.55,0.62,-0.56)).normalized(); so.rotation_euler=(-sdir).to_track_quat('Z','Y').to_euler()
# window: mullion bars up-sun of the set, casting a grid of shadow onto table, floor and wall
wm=principled('mull','#222222',0.9)[0]; c0=mathutils.Vector((CX,CY+0.15,0.3))-sdir*1.3
u=sdir.cross(mathutils.Vector((0,0,1))).normalized(); vv=u.cross(sdir).normalized()
for k in range(-5,6):
    for horiz in (0,1):
        bpy.ops.mesh.primitive_cube_add(size=1); bar=bpy.context.object; bar.data.materials.append(wm)
        if horiz: bar.location=c0+mathutils.Vector((0,0,k*0.55)); bar.scale=(8,0.07,0.07)
        else: bar.location=c0+mathutils.Vector((k*0.62,0,0)); bar.scale=(0.07,0.07,8)
        bar.visible_camera=False; bar.visible_glossy=False; bar.visible_diffuse=False
for i,(lx,ly) in enumerate(((-0.9,-1.4),(1.4,-0.6))):
    st=bpy.data.lights.new('strip%d'%i,'AREA'); st.shape='RECTANGLE'; st.size=0.12; st.size_y=1.4; st.energy=float(os.environ.get('STRIP','45'))
    so2=bpy.data.objects.new('strip%d'%i,st); sc.collection.objects.link(so2); so2.location=(CX+lx,CY+ly,0.9); so2.rotation_euler=(mathutils.Vector((CX,CY,0.25))-so2.location).to_track_quat('-Z','Y').to_euler()
ar=bpy.data.lights.new('soft','AREA'); ar.size=2.5; ar.energy=float(os.environ.get('SOFT','25')); ar.color=hx('#eef1ff')[:3]
ao=bpy.data.objects.new('soft',ar); sc.collection.objects.link(ao); ao.location=(CX+1.6,CY-1.8,1.6); ao.rotation_euler=(mathutils.Vector((CX,CY,0.2))-ao.location).to_track_quat('-Z','Y').to_euler()


cam=bpy.data.cameras.new('c'); co=bpy.data.objects.new('c',cam); sc.collection.objects.link(co); sc.camera=co
def look(loc,tgt,lens=50,f=None):
    co.location=loc; co.rotation_euler=(mathutils.Vector(tgt)-mathutils.Vector(loc)).to_track_quat('-Z','Y').to_euler(); cam.lens=lens
    if f: cam.dof.use_dof=True; cam.dof.focus_distance=(mathutils.Vector(tgt)-mathutils.Vector(loc)).length; cam.dof.aperture_fstop=f
R=lambda a: (sc.render.__setattr__('resolution_x',RES), sc.render.__setattr__('resolution_y',int(RES*a)))
if SHOT=='hero':  look((CX+0.8,CY-1.6,0.95),(CX+0.03,CY+0.06,0.2),36,11); R(0.62)
elif SHOT=='apart': look((CX+0.7,CY-2.0,1.05),(CX+0.02,CY+0.1,0.2),32,11); R(0.62)
elif SHOT=='chips': look((CX+0.25,CY-0.55,0.75),(CX,CY,0.0),55,8); R(0.7)
elif SHOT=='macro_tile':  look((X(392)+0.16,Y(361)-0.5,0.38),(X(392),Y(361),0.27),90,3.2); R(0.8)
elif SHOT=='macro_flute': look((X(626)+0.5,Y(300)-0.36,0.5),(X(615),Y(290),0.26),90,3.2); R(0.8)
elif SHOT=='macro_top':   look((X(300)-0.26,Y(361)-0.38,0.58),(X(300),Y(361),0.44),90,3.2); R(0.8)
elif SHOT=='macro_terr':  look((X(470)-0.1,Y(368)-0.42,0.3),(X(472),Y(368),0.22),90,3.2); R(0.8)
elif SHOT=='macro_blue':  look((X(385)-0.42,Y(101)-0.42,0.34),(X(385),Y(101),0.2),90,3.2); R(0.8)
sc.render.engine='CYCLES'; sc.cycles.samples=SPP; sc.cycles.use_denoising=True; sc.cycles.device='CPU'
sc.view_settings.view_transform='AgX'; sc.view_settings.look='AgX - Medium High Contrast'; sc.view_settings.exposure=float(os.environ.get('EXP','-0.4'))
sc.render.filepath=os.path.abspath(OUT); bpy.ops.render.render(write_still=True); print('DONE',OUT)
