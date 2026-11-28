/* UNIT 1024 · PERCEPTION — an illustrative robot-vision HUD (not real robot software) */
(function(){
var cv=document.getElementById('vz'); if(!cv) return;
var x=cv.getContext('2d'), W=0, H=0, DPR=1, t=0, raf=0, vis=true;
var RM=matchMedia('(prefers-reduced-motion: reduce)').matches;
var MODE='fused';
var TEAL='#2fa39e', TEALL='#7fe3dc', INK='#0b1a21', WHITE='#e9f3f4', YEL='#f2c230', GRN='#39d353', RED='#e23b2e';
var MONO='"JetBrains Mono",ui-monospace,Menlo,monospace';
// ---- camera (robot head) ----
var CAM={x:0,y:3.3,z:-5.2,pitch:0.30}, F=1;
function P(px,py,pz){ // world -> screen
  var dx=px-CAM.x, dy=py-CAM.y, dz=pz-CAM.z;
  var c=Math.cos(CAM.pitch), s=Math.sin(CAM.pitch);
  var y2=dy*c+dz*s, z2=-dy*s+dz*c;
  if(z2<0.15) return null;
  return [W/2+F*dx/z2, H*0.28-F*y2/z2, z2];
}
function unprojectFloor(sx,sy){ // screen -> floor (y=0)
  var c=Math.cos(CAM.pitch), s=Math.sin(CAM.pitch);
  var rx=(sx-W/2)/F, ry=-(sy-H*0.28)/F; // ray in cam space (x, y, 1)
  // cam->world: dy = y2*c - z2*s ; dz = y2*s + z2*c  (inverse rotation)
  var dyw=ry*c-1*s, dzw=ry*s+1*c, dxw=rx;
  if(dyw>=-1e-4) return null;
  var k=(0-CAM.y)/dyw; return [CAM.x+dxw*k, CAM.z+dzw*k];
}
// ---- scene ----
var racks=[], totes=[], pts=[];
function box(x0,x1,y0,y1,z0,z1){return {x0:x0,x1:x1,y0:y0,y1:y1,z0:z0,z1:z1}}
[-1,1].forEach(function(sd){
  var xa=sd<0?-3.0:2.1, xb=sd<0?-2.1:3.0;
  for(var b=0;b<5;b++){ var z0=3+b*2.2, z1=z0+2.0; racks.push(box(xa,xb,0,2.5,z0,z1));
    [0.12,0.95,1.75].forEach(function(sh,si){ if((b+si+(sd>0?1:0))%2===0){ var cz=z0+0.4+((b*7+si*3)%3)*0.45; totes.push({b:box(xa+0.15,xa+0.75,sh,sh+0.38,cz,cz+0.55),id:'T-'+(sd<0?'L':'R')+(b+1)+(si+1)}) } });
  }
});
var NARROW=false; var target=totes.filter(function(o){return o.id==='T-L21'||o.id==='T-L22'})[0]||totes[1];
var conveyor=box(-1.6,1.6,0,0.8,15.2,15.9);
// point cloud on floor + rack faces
(function(){ var r=0;
 function rnd(){ r=(r*9301+49297)%233280; return r/233280 }
 for(var z=-3.2;z<16.5;z+=0.24) for(var xx=-3.4;xx<=3.4;xx+=0.22){ pts.push([xx+(rnd()-.5)*.08,0,z+(rnd()-.5)*.08]) }
 racks.forEach(function(k){ var fx=k.x0<0?k.x1:k.x0; for(var z=k.z0;z<=k.z1;z+=0.2) for(var y=0;y<=k.y1;y+=0.2){ if(rnd()<.55) pts.push([fx,y+(rnd()-.5)*.05,z]) } });
})();
// ---- person ----
var person={x:0.9,z:5.2,tx:0.9,tz:5.2,phase:0,dragging:false,user:false};
var robot={speed:1,state:'WORKING'};
// ---- helpers ----
function line(a,b,col,w){ if(!a||!b) return; x.strokeStyle=col; x.lineWidth=w||1; x.beginPath(); x.moveTo(a[0],a[1]); x.lineTo(b[0],b[1]); x.stroke() }
function edges(k){ var c=[[k.x0,k.y0,k.z0],[k.x1,k.y0,k.z0],[k.x1,k.y1,k.z0],[k.x0,k.y1,k.z0],[k.x0,k.y0,k.z1],[k.x1,k.y0,k.z1],[k.x1,k.y1,k.z1],[k.x0,k.y1,k.z1]].map(function(p){return P(p[0],p[1],p[2])});
  return [[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7]].map(function(e){return [c[e[0]],c[e[1]]]}) }
function bbox(k){ var xs=[],ys=[]; [[k.x0,k.y0,k.z0],[k.x1,k.y0,k.z0],[k.x1,k.y1,k.z0],[k.x0,k.y1,k.z0],[k.x0,k.y0,k.z1],[k.x1,k.y0,k.z1],[k.x1,k.y1,k.z1],[k.x0,k.y1,k.z1]].forEach(function(p){var q=P(p[0],p[1],p[2]); if(q){xs.push(q[0]);ys.push(q[1])}}); if(!xs.length) return null; return [Math.min.apply(0,xs),Math.min.apply(0,ys),Math.max.apply(0,xs),Math.max.apply(0,ys)] }
function depthCol(z,a){ var k=Math.max(0,Math.min(1,(z-1)/14)); var r=Math.round(127+(19-127)*k*.2), g=Math.round(227-(227-90)*k), b=Math.round(220-(220-120)*k); if(k<.18){r=242;g=Math.round(194+(227-194)*k/.18);b=Math.round(48+(220-48)*k/.18)} return 'rgba('+r+','+g+','+b+','+a+')' }
function bracket(b,col,lab,sub){ var l=Math.min(16,(b[2]-b[0])*.25); x.strokeStyle=col; x.lineWidth=2; x.beginPath();
  [[b[0],b[1],1,1],[b[2],b[1],-1,1],[b[0],b[3],1,-1],[b[2],b[3],-1,-1]].forEach(function(c){x.moveTo(c[0],c[1]+c[3]*l);x.lineTo(c[0],c[1]);x.lineTo(c[0]+c[2]*l,c[1])}); x.stroke();
  if(lab){ x.font='600 '+Math.max(10,Math.round(W/95))+'px '+MONO; var tw=x.measureText(lab).width+12; x.fillStyle=col; x.fillRect(b[0],b[1]-18,tw,16); x.fillStyle=INK; x.fillText(lab,b[0]+6,b[1]-6);
    if(sub){ x.fillStyle=col; x.font=Math.max(9,Math.round(W/115))+'px '+MONO; x.fillText(sub,b[0],b[3]+14) } } }
function skel(px,pz,ph){ var sw=Math.sin(ph)*0.22, J={
  head:[px,1.66,pz], neck:[px,1.48,pz], shL:[px-.2,1.42,pz], shR:[px+.2,1.42,pz], elL:[px-.27,1.15,pz+sw*.5], elR:[px+.27,1.15,pz-sw*.5], haL:[px-.28,.9,pz+sw], haR:[px+.28,.9,pz-sw],
  hip:[px,0.98,pz], hiL:[px-.12,.95,pz], hiR:[px+.12,.95,pz], knL:[px-.13,.52,pz+sw*.6], knR:[px+.13,.52,pz-sw*.6], ftL:[px-.14,0.04,pz+sw], ftR:[px+.14,0.04,pz-sw]};
  var S={}; for(var k in J) S[k]=P(J[k][0],J[k][1],J[k][2]); return S }
// ---- draw ----
function draw(){
  x.setTransform(DPR,0,0,DPR,0,0);
  var g=x.createLinearGradient(0,0,0,H); g.addColorStop(0,'#071217'); g.addColorStop(1,'#0d2028'); x.fillStyle=g; x.fillRect(0,0,W,H);
  var sweep=(t*0.35)%1, sweepZ=1+sweep*15;
  var showDepth=MODE==='fused'||MODE==='depth', showObj=MODE==='fused'||MODE==='objects', showPath=MODE==='fused'||MODE==='path';
  // floor grid
  x.lineWidth=1;
  for(var gz=-3;gz<=16;gz+=1){ line(P(-3.4,0,gz),P(3.4,0,gz),'rgba(47,163,158,'+(0.25-gz*.012)+')') }
  for(var gx=-3;gx<=3;gx+=1){ line(P(gx,0,-3.2),P(gx,0,16.5),'rgba(47,163,158,.12)') }
  // point cloud
  if(showDepth){ for(var i=0;i<pts.length;i++){ var p=pts[i], q=P(p[0],p[1],p[2]); if(!q) continue; var near=Math.abs(p[2]-sweepZ)<.5; var a=MODE==='depth'?.95:.55; x.fillStyle=depthCol(p[2],near?1:a); var r=Math.max(.8,(MODE==='depth'?5:2.4)/q[2]*3); if(near) r*=1.8; x.fillRect(q[0]-r/2,q[1]-r/2,r,r) } }
  // scan line on floor
  if(!RM){ line(P(-3.4,0,sweepZ),P(3.4,0,sweepZ),'rgba(127,227,220,.7)',2) }
  // racks + totes wire
  x.shadowColor=TEALL; x.shadowBlur=MODE==='depth'?0:6;
  racks.forEach(function(k){ edges(k).forEach(function(e){ line(e[0],e[1],MODE==='depth'?'rgba(127,227,220,.25)':'rgba(127,227,220,.55)',1.2) }) });
  edges(conveyor).forEach(function(e){ line(e[0],e[1],'rgba(127,227,220,.6)',1.4) });
  totes.forEach(function(o){ var on=o===target; edges(o.b).forEach(function(e){ line(e[0],e[1],on?YEL:'rgba(233,243,244,.6)',on?2:1) }) });
  x.shadowBlur=0;
  // safety rings around robot (camera foot point)
  if(showPath||showObj){ [[1.6,'rgba(242,194,48,'],[3.2,'rgba(47,163,158,']].forEach(function(rg,ri){ x.beginPath(); var first=true; for(var a=-3.15;a<=3.15;a+=.05){ var q=P(Math.sin(a)*rg[0],0,0.0+Math.cos(a)*rg[0]); if(!q) continue; if(first){x.moveTo(q[0],q[1]);first=false} else x.lineTo(q[0],q[1]) } x.strokeStyle=rg[1]+(ri===0&&robot.state!=='WORKING'?.95:.55)+')'; x.lineWidth=2; x.setLineDash(ri?[6,6]:[]); x.stroke(); x.setLineDash([]); var lq=P(Math.sin(0.7)*rg[0],0,Math.cos(0.7)*rg[0]); if(lq&&!NARROW){ x.font=Math.max(9,Math.round(W/110))+'px '+MONO; x.fillStyle=rg[1]+'.9)'; x.fillText(ri?'SLOW · 3.2 M':'WAIT · 1.6 M',lq[0]+6,lq[1]-4) } }); }

  // robot digital twin at origin
  (function(){ var sp=robot.speed, col='rgba(47,163,158,.95)'; x.shadowColor=TEALL; x.shadowBlur=10;
    [box(-.38,.38,0,.42,-.45,.45),box(-.12,.12,.42,1.05,-.12,.12),box(-.3,.3,1.05,1.55,-.18,.18),box(-.13,.13,1.6,1.85,-.12,.12)].forEach(function(k){ edges(k).forEach(function(e){ line(e[0],e[1],col,1.6) }) });
    x.shadowBlur=0; var hp=P(0,1.95,0); if(hp){ x.font='700 '+Math.max(10,Math.round(W/95))+'px '+MONO; x.fillStyle=TEALL; x.textAlign='center'; x.fillText('UNIT 1024',hp[0],hp[1]-6); x.textAlign='left' }
    var lp=P(0,.5,-.46); if(lp){ var st=robot.state, a=st==='WAITING'?(RM?.6:(.35+.65*Math.abs(Math.sin(t*3)))):1; x.fillStyle='rgba(57,211,83,'+a+')'; x.beginPath(); x.arc(lp[0],lp[1],Math.max(3,W/260),0,7); x.fill() } })();
  // path to target
  if(showPath){ var tz=(target.b.z0+target.b.z1)/2, tx=target.b.x1+0.55; var path=[[0,.5],[0,tz-2],[tx*.5,tz-.6],[tx,tz]];
    x.lineWidth=4; x.strokeStyle='rgba(57,211,83,.85)'; x.setLineDash([14,10]); x.lineDashOffset=RM?0:-t*40*robot.speed; x.beginPath(); path.forEach(function(p,i){var q=P(p[0],0.01,p[1]); if(q){ i?x.lineTo(q[0],q[1]):x.moveTo(q[0],q[1]) }}); x.stroke(); x.setLineDash([]);
    var e=P(tx,0.01,tz); if(e){ x.strokeStyle=GRN; x.lineWidth=2; x.beginPath(); x.arc(e[0],e[1],10,0,7); x.stroke(); x.font='600 '+Math.max(10,Math.round(W/95))+'px '+MONO; x.fillStyle=GRN; x.fillText('GOAL · PICK '+target.id,e[0]+14,e[1]+4) } }
  // object detections
  if(showObj){ totes.forEach(function(o){ var d=(o.b.z0+o.b.z1)/2; var on=o===target; if(!on&&(NARROW||d>12||d<1.5)) return; var b=bbox(o.b); if(!b) return; if(!on&&(b[0]<12||b[2]>W-12||b[1]<H*.12||b[3]>H*.8)) return; bracket(b,on?YEL:TEALL,on?'TARGET '+o.id:'TOTE 0.'+(90+((o.id.charCodeAt(3)*7)%9)), on?d.toFixed(1)+' M · REACHABLE':null) });
    var cb=bbox(conveyor); if(cb&&!NARROW) bracket(cb,TEALL,'CONVEYOR · DROP','15.5 M'); }
  // person
  var S=skel(person.x,person.z,person.phase), pd=Math.hypot(person.x,person.z);
  x.shadowColor=YEL; x.shadowBlur=8;
  var bonesCol=MODE==='depth'?depthCol(person.z,1):YEL;
  [['head','neck'],['neck','shL'],['neck','shR'],['shL','elL'],['elL','haL'],['shR','elR'],['elR','haR'],['neck','hip'],['hip','hiL'],['hip','hiR'],['hiL','knL'],['knL','ftL'],['hiR','knR'],['knR','ftR']].forEach(function(b){ line(S[b[0]],S[b[1]],bonesCol,2.5) });
  if(S.head){ x.beginPath(); x.arc(S.head[0],S.head[1],Math.max(4,F*.11/S.head[2]),0,7); x.strokeStyle=bonesCol; x.lineWidth=2.5; x.stroke() }
  for(var k in S){ if(S[k]){ x.fillStyle=WHITE; x.fillRect(S[k][0]-2,S[k][1]-2,4,4) } }
  x.shadowBlur=0;
  if(showObj){ var pb=bbox(box(person.x-.35,person.x+.35,0,1.8,person.z-.2,person.z+.2)); if(pb) bracket(pb,YEL,'PERSON 0.98',pd.toFixed(1)+' M · '+(robot.state==='WORKING'?'TRACKING':robot.state==='SLOW'?'SLOWING':'YIELDING')) }
  hud(pd);
}
function hud(pd){
  var s=Math.max(10,Math.round(W/90)), m=Math.round(W*0.025);
  x.font='700 '+s+'px '+MONO; x.fillStyle=TEALL; x.fillText('UNIT 1024 · PERCEPTION',m,m+s);
  x.font=s*.85+'px '+MONO; x.fillStyle='rgba(233,243,244,.6)'; x.fillText('MODE · '+MODE.toUpperCase()+'   SIMULATED VIEW',m,m+s*2.4);
  // top right sim telemetry
  if(!NARROW){ x.textAlign='right'; x.fillStyle='rgba(233,243,244,.6)'; var tt=(t%60).toFixed(1);
  x.fillText('T+'+tt+' S',W-m,m+s); x.fillText('DEPTH · OBJECTS · POSE · PATH',W-m,m+s*2.4); x.textAlign='left'; }
  // corner brackets
  x.strokeStyle='rgba(127,227,220,.6)'; x.lineWidth=2; var L=W*.03; x.beginPath();
  [[m*.5,m*.5,1,1],[W-m*.5,m*.5,-1,1],[m*.5,H-m*.5,1,-1],[W-m*.5,H-m*.5,-1,-1]].forEach(function(c){x.moveTo(c[0],c[1]+c[3]*L);x.lineTo(c[0],c[1]);x.lineTo(c[0]+c[2]*L,c[1])}); x.stroke();
  // center reticle
  var tq=P(target.b.x0+.3,(target.b.y0+target.b.y1)/2,(target.b.z0+target.b.z1)/2)||[W/2,H*.28], cx=tq[0], cy=tq[1], R=Math.min(W,H)*.06, rot=RM?0:t*.6;
  x.strokeStyle='rgba(127,227,220,.75)'; x.lineWidth=1.5;
  for(var i=0;i<3;i++){ x.beginPath(); x.arc(cx,cy,R,rot+i*2.094,rot+i*2.094+1.4); x.stroke() }
  x.strokeStyle='rgba(127,227,220,.35)'; x.beginPath(); x.arc(cx,cy,R*1.35,-rot*.7,-rot*.7+4.6); x.stroke();
  x.beginPath(); x.moveTo(cx-R*.4,cy); x.lineTo(cx-R*.15,cy); x.moveTo(cx+R*.15,cy); x.lineTo(cx+R*.4,cy); x.moveTo(cx,cy-R*.4); x.lineTo(cx,cy-R*.15); x.moveTo(cx,cy+R*.15); x.lineTo(cx,cy+R*.4); x.stroke();
  for(var a=0;a<36;a++){ var an=a/36*6.283+rot*.3, r1=R*1.55, r2=R*(a%9===0?1.7:1.62); x.beginPath(); x.moveTo(cx+Math.cos(an)*r1,cy+Math.sin(an)*r1); x.lineTo(cx+Math.cos(an)*r2,cy+Math.sin(an)*r2); x.stroke() }
  // radar (top-down)
  if(!NARROW){
  var rw=Math.min(W*.2,220), rh=rw*1.15, rx=W-m-rw, ry=H-m-rh-H*.11;
  x.fillStyle='rgba(7,18,23,.75)'; x.fillRect(rx,ry,rw,rh); x.strokeStyle='rgba(127,227,220,.5)'; x.strokeRect(rx,ry,rw,rh);
  var sc=rw/8, ox=rx+rw/2, oy=ry+rh-rh*.22; function M(px,pz){return [ox+px*sc, oy-pz*sc*0.62]}
  racks.forEach(function(k){ var a=M(k.x0,k.z0), b=M(k.x1,k.z1); x.strokeStyle='rgba(127,227,220,.45)'; x.strokeRect(a[0],b[1],b[0]-a[0],a[1]-b[1]) });
  [1.6,3.2].forEach(function(r,i){ x.beginPath(); x.ellipse(ox,oy,r*sc,r*sc*.62,0,0,2*Math.PI); x.strokeStyle=i?'rgba(47,163,158,.6)':'rgba(242,194,48,.8)'; x.stroke() });
  if(!RM){ var sa=t*2%6.283; x.strokeStyle='rgba(127,227,220,.5)'; x.beginPath(); x.moveTo(ox,oy); x.lineTo(ox+Math.cos(Math.PI+sa%Math.PI)*rw*.5, oy+Math.sin(Math.PI+sa%Math.PI)*rh*.9); x.stroke() }
  var pp=M(person.x,person.z); x.fillStyle=YEL; x.beginPath(); x.arc(pp[0],pp[1],5,0,7); x.fill();
  var tp=M(target.b.x1,(target.b.z0+target.b.z1)/2); x.strokeStyle=GRN; x.strokeRect(tp[0]-4,tp[1]-4,8,8);
  x.fillStyle=TEAL; x.beginPath(); x.moveTo(ox,oy-8); x.lineTo(ox-6,oy+4); x.lineTo(ox+6,oy+4); x.fill();
  x.font=s*.8+'px '+MONO; x.fillStyle='rgba(233,243,244,.7)'; x.fillText('TOP-DOWN · 8 M',rx+8,ry+s+4);
  }
  // status bar
  var bh=NARROW?Math.max(34,H*.08):H*.075, by=H-m-bh; x.fillStyle='rgba(7,18,23,.95)'; x.fillRect(m,by,W-2*m,bh); x.strokeStyle='rgba(127,227,220,.4)'; x.strokeRect(m,by,W-2*m,bh);
  var st=robot.state, lamp=st==='WAITING'?(RM?.6:(.35+.65*Math.abs(Math.sin(t*3)))):1;
  x.fillStyle='rgba(57,211,83,'+lamp+')'; x.beginPath(); x.arc(m+bh*.5,by+bh/2,bh*.22,0,7); x.fill();
  x.font='700 '+Math.round(s*1.15)+'px '+MONO; x.fillStyle=WHITE;
  var label=NARROW?(st==='WORKING'?'WORKING':st==='SLOW'?'SLOWING':'WAITING'):(st==='WORKING'?'STEADY GREEN · WORKING':st==='SLOW'?'STEADY GREEN · SLOWING NEAR A PERSON':'PULSING GREEN · WAITING FOR YOU TO PASS');
  x.fillText(label,m+bh,by+bh/2+s*.4);
  x.textAlign='right'; x.font=s*.9+'px '+MONO; x.fillStyle=TEALL;
  x.fillText(NARROW?(Math.round(robot.speed*100)+'% · '+pd.toFixed(1)+' M'):('SPEED '+Math.round(robot.speed*100)+'%   ·   PERSON '+pd.toFixed(1)+' M'),W-m-14,by+bh/2+s*.35); x.textAlign='left';
  // speed bar
  x.fillStyle='rgba(127,227,220,.2)'; x.fillRect(m,by-6,W-2*m,3); x.fillStyle=TEALL; x.fillRect(m,by-6,(W-2*m)*robot.speed,3);
}
function update(dt){
  t+=dt;
  if(!person.user&&!person.dragging){ // idle walk loop across the aisle
    var u=(t*0.09)%1, a=u*6.283; person.tx=Math.sin(a)*1.4; person.tz=1.4+(Math.cos(a)+1)*3.2; }
  var dx=person.tx-person.x, dz=person.tz-person.z, d=Math.hypot(dx,dz);
  person.x+=dx*Math.min(1,dt*3); person.z+=dz*Math.min(1,dt*3); person.phase+=dt*(1.5+d*6);
  var pd=Math.hypot(person.x,person.z); if(pd<0.9){ var kk=0.9/Math.max(pd,1e-3); person.x*=kk; person.z*=kk; pd=0.9 }
  robot.state=pd<1.6?'WAITING':pd<3.2?'SLOW':'WORKING';
  var targetSpeed=robot.state==='WORKING'?1:robot.state==='SLOW'?.4:0; robot.speed+=(targetSpeed-robot.speed)*Math.min(1,dt*4);
  var out=document.getElementById('vzState'); if(out){ var txt=robot.state==='WORKING'?'Working · full speed':robot.state==='SLOW'?'Slowing · person within 3 m':'Waiting · person within 1.5 m'; if(out.textContent!==txt) out.textContent=txt }
}
function fit(){ var r=cv.getBoundingClientRect(); NARROW=r.width<640; DPR=Math.min(2,devicePixelRatio||1); W=r.width; H=r.height; cv.width=W*DPR; cv.height=H*DPR; F=W<640?W*1.15:W*0.75 }
var last=0; function loop(ts){ var dt=last?Math.min(.05,(ts-last)/1000):.016; last=ts; update(dt); draw(); if(vis&&!RM) raf=requestAnimationFrame(loop) }
function pointer(e){ var r=cv.getBoundingClientRect(), f=unprojectFloor(e.clientX-r.left,e.clientY-r.top); if(!f) return; person.tx=Math.max(-1.9,Math.min(1.9,f[0])); person.tz=Math.max(-2.5,Math.min(12,f[1])); person.user=true; if(RM){ person.x=person.tx; person.z=person.tz; update(0); draw() } }
cv.addEventListener('pointerdown',function(e){ person.dragging=true; cv.setPointerCapture(e.pointerId); pointer(e) });
cv.addEventListener('pointermove',function(e){ if(person.dragging||e.pointerType==='mouse') pointer(e) });
cv.addEventListener('pointerup',function(){ person.dragging=false });
cv.addEventListener('pointerleave',function(){ if(!person.dragging) person.user=false });
cv.addEventListener('keydown',function(e){ var k={ArrowLeft:[-.3,0],ArrowRight:[.3,0],ArrowUp:[0,.4],ArrowDown:[0,-.4]}[e.key]; if(!k) return; e.preventDefault(); person.user=true; person.tx=Math.max(-1.9,Math.min(1.9,person.tx+k[0])); person.tz=Math.max(-1.2,Math.min(12,person.tz+k[1])); if(RM){ person.x=person.tx; person.z=person.tz; update(0); draw() } });
[].forEach.call(document.querySelectorAll('#vzModes button'),function(b){ b.addEventListener('click',function(){ MODE=b.dataset.m; [].forEach.call(document.querySelectorAll('#vzModes button'),function(o){o.setAttribute('aria-pressed',o===b?'true':'false')}); if(RM) draw() }) });
new ResizeObserver(function(){ fit(); draw() }).observe(cv);
new IntersectionObserver(function(es){ vis=es[0].isIntersecting; cancelAnimationFrame(raf); last=0; if(vis&&!RM) raf=requestAnimationFrame(loop) }).observe(cv);
fit(); update(0); draw();
})();
