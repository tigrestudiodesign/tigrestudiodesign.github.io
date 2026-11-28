/* UNIT 1024 · PERCEPTION v2 — an illustrative robot-vision HUD drawn in canvas.
   Not real robot software. Distances are design intent: slow inside 3.2 m, wait inside 1.6 m. */
(function(){
var cv=document.getElementById('vz'); if(!cv) return;
var x=cv.getContext('2d'), W=0, H=0, DPR=1, t=0, raf=0, vis=false, boot=0, booted=false;
var RM=matchMedia('(prefers-reduced-motion: reduce)').matches;
var MODE='fused', NARROW=false;
var TEAL='#2fa39e', TEALL='#7fe3dc', INK='#0b1a21', WHITE='#e9f3f4', YEL='#f2c230', GRN='#39d353';
var MONO='"JetBrains Mono",ui-monospace,Menlo,monospace', DISP='"Inter Display",system-ui,sans-serif';
var SLOW_R=3.2, WAIT_R=1.6;

// ---------- camera ----------
var CAM={x:0,y:2.9,z:-3.6,pitch:0.24}, F=1, HZ=0.36;
function P(px,py,pz){ var dx=px-CAM.x, dy=py-CAM.y, dz=pz-CAM.z, c=Math.cos(CAM.pitch), s=Math.sin(CAM.pitch);
  var y2=dy*c+dz*s, z2=-dy*s+dz*c; if(z2<0.2) return null; return [W/2+F*dx/z2, H*HZ-F*y2/z2, z2] }
function unprojectFloor(sx,sy){ var c=Math.cos(CAM.pitch), s=Math.sin(CAM.pitch), rx=(sx-W/2)/F, ry=-(sy-H*HZ)/F;
  var dyw=ry*c-s, dzw=ry*s+c; if(dyw>=-1e-4) return null; var k=-CAM.y/dyw; return [CAM.x+rx*k, CAM.z+dzw*k] }

// ---------- colour ----------
function lerp(a,b,k){return a+(b-a)*k}
var RAMP=[[0,[242,194,48]],[1.6,[242,194,48]],[3.2,[200,232,200]],[5,[127,227,220]],[9,[47,163,158]],[16,[18,80,90]]];
function ramp(d){ for(var i=1;i<RAMP.length;i++){ if(d<=RAMP[i][0]){ var a=RAMP[i-1],b=RAMP[i],k=(d-a[0])/(b[0]-a[0]); return [lerp(a[1][0],b[1][0],k)|0,lerp(a[1][1],b[1][1],k)|0,lerp(a[1][2],b[1][2],k)|0] } } return RAMP[RAMP.length-1][1] }
function rgba(c,a){return 'rgba('+c[0]+','+c[1]+','+c[2]+','+a+')'}

// ---------- scene ----------
function box(x0,x1,y0,y1,z0,z1){return {x0:x0,x1:x1,y0:y0,y1:y1,z0:z0,z1:z1}}
var bays=[], totes=[], DECKS=[0.1,0.93,1.73,2.55];
[-1,1].forEach(function(sd){ var xa=sd<0?-3.0:2.1, xb=sd<0?-2.1:3.0;
  for(var b=0;b<5;b++){ var z0=2.6+b*2.25, z1=z0+2.05; bays.push({b:box(xa,xb,0,2.55,z0,z1),sd:sd,i:b});
    [0,1,2].forEach(function(si){ if((b+si+(sd>0?1:0))%2===0){ var cz=z0+0.35+((b*7+si*3)%3)*0.45, sh=DECKS[si]+0.02;
      var tx0=sd<0?xb-0.72:xa+0.12; totes.push({b:box(tx0,tx0+0.6,sh,sh+0.36,cz,cz+0.55),id:'T-'+(sd<0?'L':'R')+(b+1)+(si+1),conf:0.9+((b*3+si*5)%9)/100}) } }) } });
var target=totes.filter(function(o){return o.id.indexOf('T-L3')===0})[0]||totes.filter(function(o){return o.id[2]==='L'})[2];
target.conf=0.97;
var conveyor=box(-1.7,1.7,0,0.85,14.6,15.4);

// static point cloud (seeded)
var pts=[];
(function(){ var r=7; function rnd(){ r=(r*9301+49297)%233280; return r/233280 }
  for(var z=-2.6;z<16.5;z+=0.2) for(var xx=-3.4;xx<=3.4;xx+=0.19){ if(rnd()<.8) pts.push([xx+(rnd()-.5)*.07,0,z+(rnd()-.5)*.07,0]) }
  bays.forEach(function(k){ var bb=k.b, fx=k.sd<0?bb.x1:bb.x0;
    DECKS.forEach(function(y){ for(var z=bb.z0;z<=bb.z1;z+=0.09) pts.push([fx+(rnd()-.5)*.03,y+(rnd()-.5)*.02,z,1]) });
    [bb.z0,bb.z1].forEach(function(z){ for(var y=0;y<=bb.y1;y+=0.07) pts.push([fx,y,z,1]) });
    for(var z=bb.z0;z<=bb.z1;z+=0.16) for(var y=0;y<=bb.y1;y+=0.16){ if(rnd()<.25) pts.push([bb.sd<0?bb.x0+.1:bb.x1-.1,y,z,1]) } });
  totes.forEach(function(o){ var b=o.b, fx=b.x0<0?b.x1:b.x0; for(var z=b.z0;z<=b.z1;z+=0.06) for(var y=b.y0;y<=b.y1;y+=0.06) pts.push([fx,y,z,2]);
    for(var z=b.z0;z<=b.z1;z+=0.08) for(var xx=b.x0;xx<=b.x1;xx+=0.08) pts.push([xx,b.y1,z,2]) });
  for(var xx=conveyor.x0;xx<=conveyor.x1;xx+=0.07) for(var y=0;y<=conveyor.y1;y+=0.07) pts.push([xx,y,conveyor.z0,3]);
  for(var xx=conveyor.x0;xx<=conveyor.x1;xx+=0.08) for(var z=conveyor.z0;z<=conveyor.z1;z+=0.12) pts.push([xx,conveyor.y1,z,3]);
})();

// ---------- actors ----------
var person={x:0.9,z:5.2,tx:0.9,tz:5.2,phase:0,dragging:false,user:false,hist:[],vx:0,vz:0};
var robot={speed:1,state:'WORKING',totes:0};
var replanned=false;

// ---------- helpers ----------
function L(a,b,col,w){ if(!a||!b) return; x.strokeStyle=col; x.lineWidth=w||1; x.beginPath(); x.moveTo(a[0],a[1]); x.lineTo(b[0],b[1]); x.stroke() }
function corners(k){ return [[k.x0,k.y0,k.z0],[k.x1,k.y0,k.z0],[k.x1,k.y1,k.z0],[k.x0,k.y1,k.z0],[k.x0,k.y0,k.z1],[k.x1,k.y0,k.z1],[k.x1,k.y1,k.z1],[k.x0,k.y1,k.z1]].map(function(p){return P(p[0],p[1],p[2])}) }
var EDG=[[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7]];
function wire(k,col,w){ var c=corners(k); EDG.forEach(function(e){ L(c[e[0]],c[e[1]],col,w) }) }
function hull(k){ var p=corners(k).filter(Boolean).map(function(q){return [q[0],q[1]]}); if(p.length<3) return null; p.sort(function(a,b){return a[0]-b[0]||a[1]-b[1]});
  function cr(o,a,b){return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])} var lo=[],up=[];
  p.forEach(function(q){ while(lo.length>=2&&cr(lo[lo.length-2],lo[lo.length-1],q)<=0) lo.pop(); lo.push(q) });
  for(var i=p.length-1;i>=0;i--){ var q=p[i]; while(up.length>=2&&cr(up[up.length-2],up[up.length-1],q)<=0) up.pop(); up.push(q) }
  return lo.slice(0,-1).concat(up.slice(0,-1)) }
function poly(pts3,fill,stroke,w){ var q=pts3.map(function(p){return P(p[0],p[1],p[2])}); if(q.some(function(v){return !v})) return; x.beginPath(); q.forEach(function(v,i){ i?x.lineTo(v[0],v[1]):x.moveTo(v[0],v[1]) }); x.closePath(); if(fill){x.fillStyle=fill;x.fill()} if(stroke){x.strokeStyle=stroke;x.lineWidth=w||1;x.stroke()} }
function bbox2(k){ var c=corners(k).filter(Boolean); if(!c.length) return null; var xs=c.map(function(v){return v[0]}), ys=c.map(function(v){return v[1]}); return [Math.min.apply(0,xs),Math.min.apply(0,ys),Math.max.apply(0,xs),Math.max.apply(0,ys)] }
function floorRing(r,cx,cz){ var out=[]; for(var a=-Math.PI;a<=Math.PI+.01;a+=.04){ var q=P(cx+Math.sin(a)*r,0.01,cz+Math.cos(a)*r); if(q) out.push(q) } return out }
function strokePath(arr){ if(arr.length<2) return; x.beginPath(); arr.forEach(function(v,i){ i?x.lineTo(v[0],v[1]):x.moveTo(v[0],v[1]) }); x.stroke() }
function fs(k){ return Math.max(9,Math.round(W/(k||100))) }
function easeOut(k){ k=Math.max(0,Math.min(1,k)); return 1-Math.pow(1-k,3) }
function stage(a,b){ return easeOut((boot-a)/(b-a)) }

// skeleton
function skel(px,pz,ph){ var sw=Math.sin(ph)*0.22, J={ head:[px,1.68,pz], neck:[px,1.5,pz], shL:[px-.21,1.43,pz], shR:[px+.21,1.43,pz], elL:[px-.28,1.15,pz+sw*.5], elR:[px+.28,1.15,pz-sw*.5], haL:[px-.29,.9,pz+sw], haR:[px+.29,.9,pz-sw],
  hip:[px,0.98,pz], hiL:[px-.12,.95,pz], hiR:[px+.12,.95,pz], knL:[px-.13,.52,pz+sw*.6], knR:[px+.13,.52,pz-sw*.6], ftL:[px-.14,0.04,pz+sw], ftR:[px+.14,0.04,pz-sw]}; return J }
var BONES=[['head','neck'],['neck','shL'],['neck','shR'],['shL','elL'],['elL','haL'],['shR','elR'],['elR','haR'],['neck','hip'],['hip','hiL'],['hip','hiR'],['hiL','knL'],['knL','ftL'],['hiR','knR'],['knR','ftR']];

// label layout: collect, de-collide, draw with leaders
var LABELS=[];
function label(anchor,text,sub,col,pri){ if(anchor) LABELS.push({a:anchor,t:text,s:sub,c:col,p:pri||0}) }
function flushLabels(alpha){ if(alpha<=0){LABELS=[];return}
  var f=fs(98), fsub=fs(118); x.font='700 '+f+'px '+MONO;
  LABELS.sort(function(a,b){return b.p-a.p});
  var placed=[];
  LABELS.forEach(function(l){ var w=Math.max(x.measureText(l.t).width, l.s?x.measureText(l.s).width*fsub/f:0)+16, h=l.s?f*2.6:f*1.7;
    var cands=[[18,-h-14],[18,14],[-w-18,-h-14],[-w-18,14],[18,-h*2-24],[-w-18,-h*2-24]], best=null;
    for(var i=0;i<cands.length;i++){ var r=[l.a[0]+cands[i][0],l.a[1]+cands[i][1],w,h]; if(r[0]<8||r[0]+w>W-8||r[1]<H*.09||r[1]+h>H*.86) continue;
      if(placed.every(function(q){return r[0]+r[2]<q[0]||q[0]+q[2]<r[0]||r[1]+r[3]<q[1]||q[1]+q[3]<r[1]})){best=r;break} }
    if(!best) return; placed.push(best); l.r=best });
  x.globalAlpha=alpha;
  LABELS.forEach(function(l){ if(!l.r) return; var r=l.r, ex=r[0]<l.a[0]?r[0]+r[2]:r[0], ey=r[1]+r[3]/2;
    x.strokeStyle=l.c; x.lineWidth=1.2; x.beginPath(); x.moveTo(l.a[0],l.a[1]); x.lineTo(ex,ey); x.stroke();
    x.fillStyle=l.c; x.beginPath(); x.arc(l.a[0],l.a[1],2.6,0,7); x.fill();
    x.fillStyle='rgba(7,18,23,.86)'; x.fillRect(r[0],r[1],r[2],r[3]); x.fillStyle=l.c; x.fillRect(r[0],r[1],3,r[3]);
    x.strokeStyle=rgbaHex(l.c,.5); x.strokeRect(r[0]+.5,r[1]+.5,r[2]-1,r[3]-1);
    x.font='700 '+f+'px '+MONO; x.fillStyle=l.c; x.fillText(l.t,r[0]+9,r[1]+f*1.2);
    if(l.s){ x.font=fsub+'px '+MONO; x.fillStyle='rgba(233,243,244,.78)'; x.fillText(l.s,r[0]+9,r[1]+f*2.2) } });
  x.globalAlpha=1; LABELS=[] }
function rgbaHex(h,a){ var n=parseInt(h.slice(1),16); return 'rgba('+(n>>16)+','+((n>>8)&255)+','+(n&255)+','+a+')' }

// path (with live re-plan around the person)
function planPath(){ var tz=(target.b.z0+target.b.z1)/2, gx=target.b.x1+0.5, pts=[[0,0.6]], zEnd=tz-1.6;
  replanned=false;
  if(Math.abs(person.x)<1.0&&person.z>0.8&&person.z<zEnd+0.6){ replanned=true; var side=person.x>0?-1:1, dx=Math.max(-1.55,Math.min(1.55,person.x+side*1.15));
    pts.push([0,Math.max(0.9,person.z-1.5)]); pts.push([dx,person.z-0.6]); pts.push([dx,person.z+0.6]); pts.push([dx*0.4,Math.min(zEnd,person.z+1.6)]) }
  pts.push([0,zEnd]); pts.push([gx*0.55,tz-0.5]); pts.push([gx,tz]);
  // smooth with Chaikin
  for(var it=0;it<2;it++){ var o=[pts[0]]; for(var i=0;i<pts.length-1;i++){ var a=pts[i],b=pts[i+1]; o.push([a[0]*.75+b[0]*.25,a[1]*.75+b[1]*.25],[a[0]*.25+b[0]*.75,a[1]*.25+b[1]*.75]) } o.push(pts[pts.length-1]); pts=o }
  return pts }
function pathLen(p){ var s=0; for(var i=1;i<p.length;i++) s+=Math.hypot(p[i][0]-p[i-1][0],p[i][1]-p[i-1][1]); return s }
function pathAt(p,d){ for(var i=1;i<p.length;i++){ var a=p[i-1],b=p[i],l=Math.hypot(b[0]-a[0],b[1]-a[1]); if(d<=l){ var k=d/l; return [a[0]+(b[0]-a[0])*k,a[1]+(b[1]-a[1])*k,Math.atan2(b[0]-a[0],b[1]-a[1])] } d-=l } var e=p[p.length-1]; return [e[0],e[1],0] }

// ---------- draw ----------
function draw(){
  x.setTransform(DPR,0,0,DPR,0,0);
  var g=x.createLinearGradient(0,0,0,H); g.addColorStop(0,'#050d11'); g.addColorStop(.35,'#081820'); g.addColorStop(1,'#0c222b'); x.fillStyle=g; x.fillRect(0,0,W,H);
  var showDepth=MODE==='fused'||MODE==='depth', showObj=MODE==='fused'||MODE==='objects', showPath=MODE==='fused'||MODE==='path';
  var aGrid=stage(0,.25), aPts=stage(.15,.6), aGeo=stage(.35,.7), aLab=stage(.6,.95), aHud=stage(.5,.9);
  var reveal=boot<1?boot*19:99;
  var J=skel(person.x,person.z,person.phase), pd=Math.hypot(person.x,person.z);
  var path=planPath();

  // horizon glow
  var hz=P(0,0,40); if(hz){ var hg=x.createRadialGradient(W/2,hz[1],0,W/2,hz[1],W*.6); hg.addColorStop(0,'rgba(47,163,158,.16)'); hg.addColorStop(1,'rgba(47,163,158,0)'); x.fillStyle=hg; x.fillRect(0,0,W,H) }

  // floor grid
  x.globalAlpha=aGrid;
  for(var gz=-2;gz<=17;gz+=0.5){ var major=gz%2===0; L(P(-3.4,0,gz),P(3.4,0,gz),'rgba(47,163,158,'+((major?.22:.08)*Math.max(0,1-gz/18))+')',1) }
  for(var gx=-3;gx<=3;gx+=0.5){ L(P(gx,0,-2.6),P(gx,0,17),'rgba(47,163,158,'+(gx%1===0?.12:.05)+')',1) }
  // walkway markings
  x.setLineDash([18,12]); [-1.95,1.95].forEach(function(mx){ L(P(mx,0.005,-2.4),P(mx,0.005,16.6),'rgba(242,194,48,.35)',2) }); x.setLineDash([]);
  x.globalAlpha=1;

  // costmap (path mode)
  if(MODE==='path'){ for(var cz=-1.6;cz<15;cz+=0.4) for(var cx=-2.0;cx<2.0;cx+=0.4){ var mx=cx+.2,mz=cz+.2, dr=Math.min(Math.abs(mx+2.1),Math.abs(2.1-mx)), dp=Math.hypot(mx-person.x,mz-person.z);
      var cost=Math.max(Math.exp(-dr*2.2)*.85, dp<WAIT_R?1:dp<SLOW_R?.6*(1-(dp-WAIT_R)/(SLOW_R-WAIT_R))+.25:0); if(cost<.08) continue;
      var col=cost>.9?[242,194,48]:cost>.5?[200,190,90]:[47,163,158]; poly([[cx,0.004,cz],[cx+.4,0.004,cz],[cx+.4,0.004,cz+.4],[cx,0.004,cz+.4]],rgba(col,cost*.32*aGeo),rgba(col,cost*.18*aGeo),1) } }

  // camera frustum on the floor
  if(MODE!=='depth'){ var fa=.62, fl=13, f0=P(0,0.01,0.3), fL=P(-Math.sin(fa)*fl,0.01,Math.cos(fa)*fl), fR=P(Math.sin(fa)*fl,0.01,Math.cos(fa)*fl);
    if(f0&&fL&&fR){ var fg=x.createLinearGradient(0,f0[1],0,fL[1]); fg.addColorStop(0,'rgba(127,227,220,'+(.16*aGrid)+')'); fg.addColorStop(1,'rgba(127,227,220,0)'); x.fillStyle=fg; x.beginPath(); x.moveTo(f0[0],f0[1]); x.lineTo(fL[0],fL[1]); x.lineTo(fR[0],fR[1]); x.closePath(); x.fill();
      x.strokeStyle='rgba(127,227,220,'+(.35*aGrid)+')'; x.lineWidth=1; x.setLineDash([3,6]); L(f0,fL,x.strokeStyle,1); L(f0,fR,x.strokeStyle,1); x.setLineDash([]) } }

  // segmentation fills (objects mode) / shaded geometry
  var seg=MODE==='objects';
  var far=bays.slice().sort(function(a,b){return b.b.z0-a.b.z0});
  x.globalAlpha=aGeo;
  if(seg){ var hc=hull(box(-3.4,3.4,0,0.001,-2,16.5)); }
  far.forEach(function(k){ var b=k.b, inner=k.sd<0?b.x1:b.x0, outer=k.sd<0?b.x0:b.x1;
    if(seg||MODE==='fused'||MODE==='path'){ // shelving: decks + uprights
      DECKS.forEach(function(y){ poly([[b.x0,y,b.z0],[b.x1,y,b.z0],[b.x1,y,b.z1],[b.x0,y,b.z1]], seg?'rgba(47,163,158,.30)':'rgba(19,52,62,.55)', seg?'rgba(127,227,220,.7)':'rgba(127,227,220,.38)',1) });
      [[inner,b.z0],[inner,b.z1],[outer,b.z0],[outer,b.z1]].forEach(function(u,ui){ var a=P(u[0],0,u[1]), c=P(u[0],b.y1,u[1]); L(a,c,ui<2?'rgba(127,227,220,.75)':'rgba(127,227,220,.3)',ui<2?2:1) });
      if(seg) poly([[inner,0,b.z0],[inner,b.y1,b.z0],[inner,b.y1,b.z1],[inner,0,b.z1]],'rgba(47,163,158,.12)',null) } });
  // totes
  totes.slice().sort(function(a,b){return b.b.z0-a.b.z0}).forEach(function(o){ var on=o===target, h=hull(o.b); if(!h) return;
    x.beginPath(); h.forEach(function(v,i){ i?x.lineTo(v[0],v[1]):x.moveTo(v[0],v[1]) }); x.closePath();
    x.fillStyle=seg?(on?'rgba(242,194,48,.55)':'rgba(233,243,244,.38)'):(on?'rgba(242,194,48,.22)':'rgba(233,243,244,.10)'); x.fill();
    if(MODE!=='depth') wire(o.b,on?YEL:'rgba(233,243,244,.55)',on?1.8:1) });
  // conveyor
  if(MODE!=='depth'){ var ch=hull(conveyor); if(ch){ x.beginPath(); ch.forEach(function(v,i){ i?x.lineTo(v[0],v[1]):x.moveTo(v[0],v[1]) }); x.closePath(); x.fillStyle=seg?'rgba(108,194,190,.4)':'rgba(19,52,62,.6)'; x.fill() } wire(conveyor,'rgba(127,227,220,.55)',1.2);
    for(var rz=conveyor.x0+.2;rz<conveyor.x1;rz+=.25) L(P(rz,conveyor.y1,conveyor.z0),P(rz,conveyor.y1,conveyor.z1),'rgba(127,227,220,.25)',1) }
  x.globalAlpha=1;

  // point cloud
  var sweepR=RM?99:((t*5.5)%17), dotK=MODE==='depth'?1.5:1;
  if(showDepth&&aPts>0){ for(var i=0;i<pts.length;i++){ var p=pts[i], dd=Math.hypot(p[0],p[2]); if(dd>reveal) continue; var q=P(p[0],p[1],p[2]); if(!q||q[0]<0||q[0]>W||q[1]<0||q[1]>H) continue;
      var near=Math.abs(dd-sweepR)<.45, c=ramp(dd), a=(MODE==='depth'?.9:(p[3]===0?.35:.6))*aPts; if(near){ c=[233,250,248]; a=Math.min(1,a+.5) }
      var r=Math.max(.9,(F*0.018/q[2]))*dotK*(near?1.6:1); x.fillStyle=rgba(c,a); x.fillRect(q[0]-r/2,q[1]-r/2,r,r) }
    // person points
    for(var bi=0;bi<BONES.length;bi++){ var A=J[BONES[bi][0]],B=J[BONES[bi][1]]; for(var s=0;s<1;s+=.08){ var wx=lerp(A[0],B[0],s)+Math.sin(bi*13+s*40)*.05, wy=lerp(A[1],B[1],s), wz=lerp(A[2],B[2],s)+Math.cos(bi*7+s*30)*.05, q=P(wx,wy,wz); if(!q) continue; var r=Math.max(1.4,F*0.03/q[2])*dotK; x.fillStyle=rgba(ramp(pd),.95*aPts); x.fillRect(q[0]-r/2,q[1]-r/2,r,r) } }
    // sweep ring
    if(!RM&&MODE!=='objects'){ x.strokeStyle='rgba(233,250,248,'+(.55*(1-sweepR/17)*aPts)+')'; x.lineWidth=2; strokePath(floorRing(sweepR,0,0)) } }

  // safety rings
  if(showPath||showObj){ [[WAIT_R,'255,74,58','WAIT · 1.6 M'],[SLOW_R,'242,194,48','SLOW · 3.2 M']].forEach(function(rg,ri){ var hot=(ri===0&&robot.state==='WAITING')||(ri===1&&robot.state!=='WORKING');
      var ring=floorRing(rg[0],0,0); x.globalAlpha=aGeo;
      if(hot&&ring.length>2){ x.fillStyle='rgba('+rg[1]+','+(ri===0?.12:.06)+')'; x.beginPath(); ring.forEach(function(v,i){ i?x.lineTo(v[0],v[1]):x.moveTo(v[0],v[1]) }); x.closePath(); x.fill() }
      x.strokeStyle='rgba('+rg[1]+','+(hot?.95:.45)+')'; x.lineWidth=hot?2.5:1.5; x.setLineDash(ri?[8,7]:[]); x.lineDashOffset=RM?0:-t*20; strokePath(ring); x.setLineDash([]);
      // tick marks around ring
      for(var a=0;a<6.283;a+=0.26){ var q1=P(Math.sin(a)*rg[0],0.01,Math.cos(a)*rg[0]), q2=P(Math.sin(a)*(rg[0]+.12),0.01,Math.cos(a)*(rg[0]+.12)); L(q1,q2,'rgba('+rg[1]+','+(hot?.8:.35)+')',1) }
      var lq=P(Math.sin(-1.0)*rg[0],0.01,Math.cos(-1.0)*rg[0]); if(lq&&!NARROW){ x.font='700 '+fs(118)+'px '+MONO; x.fillStyle='rgba('+rg[1]+',.95)'; x.fillText(rg[2],lq[0]-x.measureText(rg[2]).width-8,lq[1]+4) }
      x.globalAlpha=1 }) }

  // robot footprint + chevron
  (function(){ x.globalAlpha=aGeo; poly([[-.38,0.01,-.45],[.38,0.01,-.45],[.38,0.01,.45],[-.38,0.01,.45]],'rgba(47,163,158,.25)','rgba(127,227,220,.9)',1.6);
    var c1=P(-.18,0.02,-.05),c2=P(0,0.02,.22),c3=P(.18,0.02,-.05); if(c1&&c2&&c3){ x.strokeStyle=TEALL; x.lineWidth=3.5; x.lineCap='square'; x.beginPath(); x.moveTo(c1[0],c1[1]); x.lineTo(c2[0],c2[1]); x.lineTo(c3[0],c3[1]); x.stroke(); x.lineCap='butt' }
    var lamp=robot.state==='WAITING'?(RM?.6:(.35+.65*Math.abs(Math.sin(t*3)))):1, lp=P(0,0.02,-.5); if(lp){ var rg2=x.createRadialGradient(lp[0],lp[1],0,lp[0],lp[1],F*0.12/lp[2]); var LC=robot.state==='WAITING'?'255,74,58':robot.state==='SLOW'?'242,194,48':'57,211,83'; rg2.addColorStop(0,'rgba('+LC+','+(.9*lamp)+')'); rg2.addColorStop(1,'rgba('+LC+',0)'); x.fillStyle=rg2; x.beginPath(); x.arc(lp[0],lp[1],F*0.12/lp[2],0,7); x.fill() }
    x.globalAlpha=1 })();

  // path
  if(showPath){ x.globalAlpha=aGeo; var pq=path.map(function(p){return P(p[0],0.012,p[1])}).filter(Boolean);
    x.strokeStyle='rgba(57,211,83,.18)'; x.lineWidth=Math.max(10,W/70); x.lineJoin='round'; strokePath(pq); x.strokeStyle='rgba(57,211,83,.8)'; x.lineWidth=2; strokePath(pq);
    var Lp=pathLen(path), off=RM?0:(t*1.4*Math.max(.15,robot.speed))%0.9;
    for(var d=off+0.6;d<Lp-0.3;d+=0.9){ var at=pathAt(path,d), s=0.16, ca=Math.cos(at[2]), sa=Math.sin(at[2]);
      function pr(u,v){ return P(at[0]+u*ca+v*sa,0.015,at[1]-u*sa+v*ca) } var a1=pr(-s,-s*.7), a2=pr(0,s*.6), a3=pr(s,-s*.7);
      if(a1&&a2&&a3){ x.strokeStyle='rgba(57,211,83,'+(.95-d/Lp*.5)+')'; x.lineWidth=Math.max(2,F*0.04/a2[2]); x.lineCap='square'; x.beginPath(); x.moveTo(a1[0],a1[1]); x.lineTo(a2[0],a2[1]); x.lineTo(a3[0],a3[1]); x.stroke(); x.lineCap='butt' } }
    var e=path[path.length-1], eq=P(e[0],0.012,e[1]); if(eq){ x.strokeStyle=GRN; x.lineWidth=2; strokePath(floorRing(.25,e[0],e[1])); }
    x.globalAlpha=1;
    if(eq) label([eq[0],eq[1]],'GOAL · PICK '+target.id,(pathLen(path)).toFixed(1)+' M ROUTE'+(replanned?' · REPLANNED':''),GRN,6);
    if(replanned){ var dq=P(path[Math.floor(path.length*.35)][0],0.02,path[Math.floor(path.length*.35)][1]); if(dq) label(dq,'DETOUR','PERSON IN LANE',GRN,7) } }

  // person: predicted motion, body, skeleton
  var predA=aGeo; if(showObj||showPath){ x.globalAlpha=predA; for(var k2=1;k2<=4;k2++){ var px2=person.x+person.vx*k2*.4, pz2=person.z+person.vz*k2*.4, q=P(px2,0.01,pz2); if(q){ x.fillStyle='rgba(242,194,48,'+(.5-k2*.1)+')'; x.beginPath(); x.ellipse(q[0],q[1],Math.max(3,F*.18/q[2]),Math.max(1.5,F*.07/q[2]),0,0,7); x.fill() } }
    var pq0=P(person.x,0.01,person.z), pq1=P(person.x+person.vx*1.6,0.01,person.z+person.vz*1.6); if(pq0&&pq1&&Math.hypot(person.vx,person.vz)>.08){ x.setLineDash([4,5]); L(pq0,pq1,'rgba(242,194,48,.8)',1.5); x.setLineDash([]) } x.globalAlpha=1 }
  var S={}; for(var jk in J) S[jk]=P(J[jk][0],J[jk][1],J[jk][2]);
  var bc=MODE==='depth'?rgba(ramp(pd),1):YEL;
  if(seg){ var hb=hull(box(person.x-.3,person.x+.3,0,1.85,person.z-.15,person.z+.15)); if(hb){ x.beginPath(); hb.forEach(function(v,i){ i?x.lineTo(v[0],v[1]):x.moveTo(v[0],v[1]) }); x.closePath(); x.fillStyle='rgba(242,194,48,.45)'; x.fill() } }
  if(MODE!=='depth'){ x.shadowColor=YEL; x.shadowBlur=10;
    BONES.forEach(function(b){ L(S[b[0]],S[b[1]],bc,3) }); if(S.head){ x.beginPath(); x.arc(S.head[0],S.head[1],Math.max(4,F*.11/S.head[2]),0,7); x.strokeStyle=bc; x.lineWidth=2.5; x.stroke() }
    x.shadowBlur=0; for(var jk2 in S){ if(S[jk2]){ x.fillStyle=WHITE; x.beginPath(); x.arc(S[jk2][0],S[jk2][1],2.4,0,7); x.fill() } } }
  if(showObj){ var pbx=box(person.x-.32,person.x+.32,0,1.85,person.z-.22,person.z+.22); x.globalAlpha=aGeo; wire(pbx,'rgba(242,194,48,.75)',1.2); x.globalAlpha=1;
    var top=P(person.x,1.95,person.z); label(top,'PERSON · 0.98',pd.toFixed(1)+' M · '+(robot.state==='WORKING'?'TRACKING':robot.state==='SLOW'?'ROBOT SLOWING':'ROBOT WAITING'),YEL,10) }

  // detections
  if(showObj){ totes.forEach(function(o){ var on=o===target, d=Math.hypot((o.b.x0+o.b.x1)/2,(o.b.z0+o.b.z1)/2); if(!on&&(NARROW||d>11||d<2)) return; if(!on&&(o.id.charCodeAt(4)%2)) return;
      var a=P((o.b.x0+o.b.x1)/2,o.b.y1,(o.b.z0+o.b.z1)/2); label(a,on?'TARGET · '+o.id:'TOTE · '+o.conf.toFixed(2),on?d.toFixed(1)+' M · REACHABLE':d.toFixed(1)+' M',on?YEL:TEALL,on?9:1) });
    if(!NARROW){ var cq=P(conveyor.x1,conveyor.y1,conveyor.z0); label(cq,'CONVEYOR · DROP','15.0 M',TEALL,2);
      var rq=P(-2.1,2.55,4.0); label(rq,'RACK R-L2 · 0.99','SHELVING · 4 DECKS',TEALL,3) } }

  // target lock reticle
  if(showObj||showPath){ var tc=P((target.b.x0+target.b.x1)/2,(target.b.y0+target.b.y1)/2,(target.b.z0+target.b.z1)/2); if(tc){ var R=Math.min(W,H)*.055*(1+.6*(1-aLab)), rot=RM?0:t*.7;
      x.globalAlpha=aLab; x.strokeStyle='rgba(242,194,48,.9)'; x.lineWidth=1.6; for(var i2=0;i2<3;i2++){ x.beginPath(); x.arc(tc[0],tc[1],R,rot+i2*2.094,rot+i2*2.094+1.3); x.stroke() }
      x.strokeStyle='rgba(242,194,48,.4)'; x.beginPath(); x.arc(tc[0],tc[1],R*1.45,-rot*.6,-rot*.6+4.4); x.stroke();
      for(var a3=0;a3<48;a3++){ var an=a3/48*6.283-rot*.25, r1=R*1.62, r2=R*(a3%12===0?1.85:1.72); L([tc[0]+Math.cos(an)*r1,tc[1]+Math.sin(an)*r1],[tc[0]+Math.cos(an)*r2,tc[1]+Math.sin(an)*r2],'rgba(242,194,48,.45)',1) }
      L([tc[0]-R*.5,tc[1]],[tc[0]-R*.2,tc[1]],YEL,1.5); L([tc[0]+R*.2,tc[1]],[tc[0]+R*.5,tc[1]],YEL,1.5); L([tc[0],tc[1]-R*.5],[tc[0],tc[1]-R*.2],YEL,1.5); L([tc[0],tc[1]+R*.2],[tc[0],tc[1]+R*.5],YEL,1.5);
      if(!NARROW){ x.font='700 '+fs(120)+'px '+MONO; x.fillStyle=YEL; x.fillText('LOCK',tc[0]+R*1.95,tc[1]-4); x.fillStyle='rgba(233,243,244,.7)'; x.fillText('GRASP 0.94',tc[0]+R*1.95,tc[1]+fs(120)+2) }
      x.globalAlpha=1 } }

  flushLabels(aLab);
  hud(pd);
  // scanlines + vignette
  x.fillStyle='rgba(0,0,0,.08)'; for(var sy=0;sy<H;sy+=3) x.fillRect(0,sy,W,1);
  var vg=x.createRadialGradient(W/2,H/2,Math.min(W,H)*.35,W/2,H/2,Math.max(W,H)*.75); vg.addColorStop(0,'rgba(0,0,0,0)'); vg.addColorStop(1,'rgba(0,0,0,.45)'); x.fillStyle=vg; x.fillRect(0,0,W,H);
  // boot overlay
  if(boot<1){ var by=H*easeOut(boot*1.3); x.fillStyle='rgba(5,13,17,'+(.9*(1-boot))+')'; x.fillRect(0,by,W,H-by); L([0,by],[W,by],'rgba(127,227,220,'+(1-boot)+')',2);
    x.font='700 '+fs(70)+'px '+MONO; x.fillStyle='rgba(127,227,220,'+(1-boot*.8)+')'; x.textAlign='center'; x.fillText(boot<.5?'INITIALIZING PERCEPTION':'PERCEPTION ONLINE',W/2,Math.min(H*.6,by+fs(70)*2.2));
    x.font=fs(110)+'px '+MONO; x.fillText('DEPTH '+Math.min(100,Math.round(boot*220))+'% · OBJECTS '+Math.min(100,Math.max(0,Math.round((boot-.3)*200)))+'% · PATH '+Math.min(100,Math.max(0,Math.round((boot-.5)*220)))+'%',W/2,Math.min(H*.6,by+fs(70)*2.2)+fs(110)*2); x.textAlign='left' }
}

function hud(pd){
  var s=fs(92), m=Math.round(Math.max(14,W*0.022)), aH=stage(.5,.9); x.globalAlpha=aH;
  // corner frames
  x.strokeStyle='rgba(127,227,220,.6)'; x.lineWidth=2; var Lc=W*.03; x.beginPath();
  [[m*.5,m*.5,1,1],[W-m*.5,m*.5,-1,1],[m*.5,H-m*.5,1,-1],[W-m*.5,H-m*.5,-1,-1]].forEach(function(c){x.moveTo(c[0],c[1]+c[3]*Lc);x.lineTo(c[0],c[1]);x.lineTo(c[0]+c[2]*Lc,c[1])}); x.stroke();
  // title block
  x.font='800 '+Math.round(s*1.35)+'px '+DISP; x.fillStyle=WHITE; x.fillText('UNIT 1024',m,m+s*1.3);
  x.font='700 '+s+'px '+MONO; x.fillStyle=TEALL; x.fillText('PERCEPTION · '+MODE.toUpperCase(),m,m+s*2.75);
  x.font=Math.round(s*.82)+'px '+MONO; x.fillStyle='rgba(233,243,244,.55)'; x.fillText('SIMULATED VIEW · NOT REAL ROBOT SOFTWARE',m,m+s*4);
  // detections panel
  if(!NARROW){ var items=[['PERSON',.98,pd.toFixed(1)+' M',YEL],['TARGET '+target.id,.97,'',YEL],['TOTE',.94,'×'+totes.length,TEALL],['RACK',.99,'×'+bays.length,TEALL],['CONVEYOR',.96,'×1',TEALL],['FLOOR',.99,'',TEALL]];
    var px=m, py=m+s*5.6, pw=Math.min(240,W*.19), rh=s*1.75; x.fillStyle='rgba(7,18,23,.7)'; x.fillRect(px,py,pw,rh*(items.length+1.3)); x.strokeStyle='rgba(127,227,220,.3)'; x.strokeRect(px+.5,py+.5,pw-1,rh*(items.length+1.3)-1);
    x.font='700 '+Math.round(s*.82)+'px '+MONO; x.fillStyle=TEALL; x.fillText('DETECTIONS · '+(totes.length+bays.length+3),px+10,py+rh*.85);
    items.forEach(function(it,i){ var yy=py+rh*(i+1.6); x.fillStyle=it[3]; x.fillRect(px+10,yy-s*.55,4,s*.7); x.font=Math.round(s*.8)+'px '+MONO; x.fillStyle=WHITE; x.fillText(it[0],px+20,yy); x.textAlign='right'; x.fillStyle='rgba(233,243,244,.6)'; x.fillText(it[2],px+pw-10,yy); x.textAlign='left';
      var bw=pw*.32, bx=px+pw-10-bw-(it[2]?x.measureText(it[2]).width+10:0); x.fillStyle='rgba(127,227,220,.15)'; x.fillRect(bx,yy-s*.42,bw,s*.3); x.fillStyle=it[3]; x.fillRect(bx,yy-s*.42,bw*it[1],s*.3) }) }
  // top-right telemetry
  if(!NARROW){ x.textAlign='right'; x.font=Math.round(s*.82)+'px '+MONO; x.fillStyle='rgba(233,243,244,.6)';
    var n=pts.length; x.fillText('T+'+(t%600).toFixed(1)+' S · 30 HZ (SIM)',W-m,m+s); x.fillText(n.toLocaleString('en-US')+' POINTS · 16 M RANGE',W-m,m+s*2.3);
    x.fillStyle=TEALL; x.fillText('DEPTH · OBJECTS · POSE · PATH',W-m,m+s*3.6); x.textAlign='left';
    // range legend
    var lx=W-m-10, ly=m+s*5, lh=Math.min(H*.32,200); var lg=x.createLinearGradient(0,ly,0,ly+lh); [0,1.6,3.2,5,9,16].forEach(function(d){ lg.addColorStop(d/16,rgba(ramp(d),1)) }); x.fillStyle=lg; x.fillRect(lx,ly,8,lh);
    x.font=Math.round(s*.72)+'px '+MONO; x.textAlign='right'; [[0,'0 M'],[1.6,'1.6'],[3.2,'3.2'],[8,'8'],[16,'16 M']].forEach(function(v){ var yy=ly+lh*v[0]/16; x.fillStyle='rgba(233,243,244,.7)'; x.fillText(v[1],lx-6,yy+4); L([lx-3,yy],[lx,yy],'rgba(233,243,244,.6)',1) }); x.textAlign='left' }
  // radar
  if(!NARROW){ var rr=Math.min(W*.095,110), rcx=W-m-rr-6, rcy=H-m-H*.115-rr-14; x.fillStyle='rgba(7,18,23,.78)'; x.beginPath(); x.arc(rcx,rcy,rr,0,7); x.fill();
    x.strokeStyle='rgba(127,227,220,.45)'; x.lineWidth=1; [1,.66,.33].forEach(function(k){ x.beginPath(); x.arc(rcx,rcy,rr*k,0,7); x.stroke() }); L([rcx-rr,rcy],[rcx+rr,rcy],'rgba(127,227,220,.2)',1); L([rcx,rcy-rr],[rcx,rcy+rr],'rgba(127,227,220,.2)',1);
    var sc=rr/8; function M(px,pz){return [rcx+px*sc, rcy-pz*sc]}
    x.save(); x.beginPath(); x.arc(rcx,rcy,rr,0,7); x.clip();
    bays.forEach(function(k){ var a=M(k.b.x0,k.b.z0), b=M(k.b.x1,k.b.z1); x.fillStyle='rgba(47,163,158,.25)'; x.fillRect(a[0],b[1],b[0]-a[0],a[1]-b[1]); x.strokeStyle='rgba(127,227,220,.5)'; x.strokeRect(a[0],b[1],b[0]-a[0],a[1]-b[1]) });
    [WAIT_R,SLOW_R].forEach(function(r,i){ x.beginPath(); x.arc(rcx,rcy,r*sc,0,7); x.strokeStyle=i?'rgba(127,227,220,.6)':'rgba(242,194,48,.85)'; x.setLineDash(i?[3,3]:[]); x.stroke(); x.setLineDash([]) });
    if(!RM){ var sa=(t*1.6)%6.283; for(var w=0;w<14;w++){ var aa=sa-w*.035; x.strokeStyle='rgba(127,227,220,'+(.5-w*.035)+')'; L([rcx,rcy],[rcx+Math.cos(aa)*rr,rcy+Math.sin(aa)*rr],x.strokeStyle,1.5) } }
    person.hist.forEach(function(h,i){ var hp=M(h[0],h[1]); x.fillStyle='rgba(242,194,48,'+(i/person.hist.length*.5)+')'; x.fillRect(hp[0]-1.5,hp[1]-1.5,3,3) });
    var pp=M(person.x,person.z); x.fillStyle=YEL; x.beginPath(); x.arc(pp[0],pp[1],4.5,0,7); x.fill();
    var tp=M((target.b.x0+target.b.x1)/2,(target.b.z0+target.b.z1)/2); x.strokeStyle=GRN; x.strokeRect(tp[0]-3.5,tp[1]-3.5,7,7);
    x.restore();
    x.fillStyle=TEALL; x.beginPath(); x.moveTo(rcx,rcy-7); x.lineTo(rcx-5,rcy+4); x.lineTo(rcx+5,rcy+4); x.fill();
    x.font=Math.round(s*.72)+'px '+MONO; x.fillStyle='rgba(233,243,244,.7)'; x.textAlign='center'; x.fillText('TOP-DOWN · 8 M',rcx,rcy+rr+s*1.1); x.textAlign='left' }
  // status bar
  var bh=NARROW?Math.max(38,H*.085):Math.max(46,H*.075), byy=H-m-bh, st=robot.state, lamp=st==='WAITING'?(RM?.6:(.35+.65*Math.abs(Math.sin(t*3)))):1;
  x.fillStyle='rgba(7,18,23,.92)'; x.fillRect(m,byy,W-2*m,bh); var SC=st==='WAITING'?'255,74,58':st==='SLOW'?'242,194,48':'57,211,83'; x.strokeStyle=st==='WORKING'?'rgba(127,227,220,.45)':'rgba('+SC+',.7)'; x.lineWidth=1.5; x.strokeRect(m+.5,byy+.5,W-2*m-1,bh-1);
  x.fillStyle=st==='WORKING'?'rgba(47,163,158,.9)':'rgb('+SC+')'; x.fillRect(m,byy,4,bh);
  var lg2=x.createRadialGradient(m+bh*.55,byy+bh/2,0,m+bh*.55,byy+bh/2,bh*.42); lg2.addColorStop(0,'rgba('+SC+','+lamp+')'); lg2.addColorStop(.55,'rgba('+SC+','+(lamp*.8)+')'); lg2.addColorStop(1,'rgba('+SC+',0)'); x.fillStyle=lg2; x.beginPath(); x.arc(m+bh*.55,byy+bh/2,bh*.42,0,7); x.fill();
  x.font='700 '+Math.round(s*1.12)+'px '+MONO; x.fillStyle=WHITE;
  var lab=NARROW?(st==='WORKING'?'WORKING':st==='SLOW'?'SLOWING':'WAITING'):(st==='WORKING'?'STEADY GREEN · WORKING':st==='SLOW'?'YELLOW · SLOWING · PERSON INSIDE 3.2 M':'PULSING RED · WAITING · PERSON INSIDE 1.6 M');
  x.fillText(lab,m+bh*1.05,byy+bh/2+s*.4);
  // segmented speed meter
  var segs=NARROW?8:20, sw2=NARROW?6:8, sx=W-m-14-segs*(sw2+3); for(var i=0;i<segs;i++){ x.fillStyle=i<Math.round(robot.speed*segs)?(st==='WORKING'?TEALL:'rgb('+SC+')'):'rgba(127,227,220,.15)'; x.fillRect(sx+i*(sw2+3),byy+bh*.3,sw2,bh*.4) }
  x.textAlign='right'; x.font=Math.round(s*.85)+'px '+MONO; x.fillStyle=TEALL; if(!NARROW) x.fillText('SPEED '+Math.round(robot.speed*100)+'% · PERSON '+pd.toFixed(1)+' M',sx-14,byy+bh/2+s*.32); x.textAlign='left';
  x.globalAlpha=1;
}

function update(dt){
  t+=dt; if(vis&&boot<1) boot=Math.min(1,boot+dt/(RM?0.001:2.2));
  if(!person.user&&!person.dragging){ var u=(t*0.075)%1, a=u*6.283; person.tx=Math.sin(a)*1.35; person.tz=1.2+(Math.cos(a)+1)*3.3 }
  var dx=person.tx-person.x, dz=person.tz-person.z, d=Math.hypot(dx,dz), ox=person.x, oz=person.z;
  person.x+=dx*Math.min(1,dt*3); person.z+=dz*Math.min(1,dt*3); person.phase+=dt*(1.5+d*6);
  var pd=Math.hypot(person.x,person.z); if(pd<0.9){ var kk=0.9/Math.max(pd,1e-3); person.x*=kk; person.z*=kk; pd=0.9 }
  if(dt>0){ person.vx+=((person.x-ox)/dt-person.vx)*Math.min(1,dt*4); person.vz+=((person.z-oz)/dt-person.vz)*Math.min(1,dt*4) }
  if(!person.hist.length||Math.hypot(person.x-person.hist[person.hist.length-1][0],person.z-person.hist[person.hist.length-1][1])>.15){ person.hist.push([person.x,person.z]); if(person.hist.length>24) person.hist.shift() }
  robot.state=pd<WAIT_R?'WAITING':pd<SLOW_R?'SLOW':'WORKING';
  var ts=robot.state==='WORKING'?1:robot.state==='SLOW'?.4:0; robot.speed+=(ts-robot.speed)*Math.min(1,dt*4);
  var out=document.getElementById('vzState'); if(out){ var txt=robot.state==='WORKING'?'Working · full speed':robot.state==='SLOW'?'Slowing · person within 3.2 m':'Waiting · person within 1.6 m'; if(out.textContent!==txt) out.textContent=txt }
}
function fit(){ var r=cv.getBoundingClientRect(); NARROW=r.width<640; DPR=Math.min(2,devicePixelRatio||1); W=r.width; H=r.height; cv.width=W*DPR; cv.height=H*DPR; F=NARROW?W*0.9:W*0.62; HZ=NARROW?0.38:0.36 }
var last=0; function loop(ts){ var dt=last?Math.min(.05,(ts-last)/1000):.016; last=ts; update(dt); draw(); if(vis&&!RM) raf=requestAnimationFrame(loop) }
function pointer(e){ var r=cv.getBoundingClientRect(), f=unprojectFloor(e.clientX-r.left,e.clientY-r.top); if(!f) return; person.tx=Math.max(-1.9,Math.min(1.9,f[0])); person.tz=Math.max(-2.2,Math.min(12,f[1])); person.user=true; if(RM){ person.x=person.tx; person.z=person.tz; update(0); draw() } }
cv.addEventListener('pointerdown',function(e){ person.dragging=true; try{cv.setPointerCapture(e.pointerId)}catch(_){} pointer(e) });
cv.addEventListener('pointermove',function(e){ if(person.dragging||e.pointerType==='mouse') pointer(e) });
cv.addEventListener('pointerup',function(){ person.dragging=false });
cv.addEventListener('pointerleave',function(){ if(!person.dragging) person.user=false });
cv.addEventListener('keydown',function(e){ var k={ArrowLeft:[-.3,0],ArrowRight:[.3,0],ArrowUp:[0,.4],ArrowDown:[0,-.4]}[e.key]; if(!k) return; e.preventDefault(); person.user=true; person.tx=Math.max(-1.9,Math.min(1.9,person.tx+k[0])); person.tz=Math.max(-1.2,Math.min(12,person.tz+k[1])); if(RM){ person.x=person.tx; person.z=person.tz; update(0); draw() } });
[].forEach.call(document.querySelectorAll('#vzModes button'),function(b){ b.addEventListener('click',function(){ MODE=b.dataset.m; [].forEach.call(document.querySelectorAll('#vzModes button'),function(o){o.setAttribute('aria-pressed',o===b?'true':'false')}); if(RM) draw() }) });
new ResizeObserver(function(){ fit(); draw() }).observe(cv);
new IntersectionObserver(function(es){ vis=es[0].isIntersecting; cancelAnimationFrame(raf); last=0; if(vis){ if(RM){ boot=1; update(0); draw() } else raf=requestAnimationFrame(loop) } },{threshold:.25}).observe(cv);
fit(); update(0); draw();
window.UNIT_VZ={person:person,robot:robot,setMode:function(m){MODE=m},boot:function(v){boot=v}};
})();
