/* Tigre Studio · Figures: computational ideas, drawn in code.
   Each figure draws one idea, with a parameter p in [0,1] the viewer drives with the pointer. */
(function(){
"use strict";
const W=480,H=300;
const f=n=>Math.round(n*10)/10;
const pts=a=>a.map(q=>f(q[0])+","+f(q[1])).join(" ");
const pathD=a=>"M"+a.map(q=>f(q[0])+" "+f(q[1])).join("L");
let uid=0;
function grid(step=24){let s="";for(let x=step/2;x<W;x+=step)for(let y=step/2;y<H;y+=step)s+=`<circle cx="${x}" cy="${y}" r="1" class="gd"/>`;return s}
function lab(t,x=16,y=H-14){return `<text x="${x}" y="${y}" class="lb">${t}</text>`}
function mulberry(a){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}}
function bez(P,t){let a=P.map(q=>q.slice());while(a.length>1){const b=[];for(let i=0;i<a.length-1;i++)b.push([a[i][0]+(a[i+1][0]-a[i][0])*t,a[i][1]+(a[i+1][1]-a[i][1])*t]);a=b}return a[0]}
function bspline(P,deg,n=120){
  const m=P.length-1, k=Math.min(deg,m); const knots=[];
  for(let i=0;i<=m+k+1;i++)knots.push(i<=k?0:i>m?1:(i-k)/(m-k+1));
  const out=[];
  for(let s=0;s<=n;s++){let t=s/n;if(t>=1)t=1-1e-9;
    let span=k;while(span<m&&t>=knots[span+1])span++;
    const d=[];for(let j=0;j<=k;j++)d.push(P[span-k+j].slice());
    for(let r=1;r<=k;r++)for(let j=k;j>=r;j--){const i=span-k+j;const den=knots[i+k-r+1]-knots[i];const a=den?(t-knots[i])/den:0;d[j]=[(1-a)*d[j-1][0]+a*d[j][0],(1-a)*d[j-1][1]+a*d[j][1]]}
    out.push(d[k])}
  return out;
}
function curvComb(poly,scale,every=3){ // normals scaled by curvature
  let s="",env=[];
  for(let i=1;i<poly.length-1;i+=every){const a=poly[i-1],b=poly[i],c=poly[i+1];
    const dx1=b[0]-a[0],dy1=b[1]-a[1],dx2=c[0]-b[0],dy2=c[1]-b[1];const cross=dx1*dy2-dy1*dx2;const l1=Math.hypot(dx1,dy1),l2=Math.hypot(dx2,dy2),l3=Math.hypot(c[0]-a[0],c[1]-a[1]);
    const k=l1*l2*l3?2*cross/(l1*l2*l3):0;const tx=(c[0]-a[0])/l3,ty=(c[1]-a[1])/l3;const nx=-ty,ny=tx;
    const e=[b[0]-nx*k*scale,b[1]-ny*k*scale];env.push(e);s+=`<line x1="${f(b[0])}" y1="${f(b[1])}" x2="${f(e[0])}" y2="${f(e[1])}" class="k h"/>`}
  return s+`<polyline points="${pts(env)}" class="r"/>`;
}
const P={
 nurbs(p){let s=grid();const t=Math.max(0,Math.min(1,p));const C=[[60,240],[130,50],[350,60],[420,230]];
   const lv=[C];while(lv[lv.length-1].length>1){const a=lv[lv.length-1];lv.push(a.slice(1).map((q,i)=>[a[i][0]+(q[0]-a[i][0])*t,a[i][1]+(q[1]-a[i][1])*t]))}
   const full=Array.from({length:81},(_,i)=>bez(C,i/80)),done=full.filter((_,i)=>i/80<=t+1e-9);
   s+=`<polyline points="${pts(full)}" class="k faint"/><polyline points="${pts(C)}" class="g dash"/>`;
   s+=`<polyline points="${pts(lv[1])}" class="k faint2"/><polyline points="${pts(lv[2])}" class="r"/>`;
   lv[1].forEach(q=>s+=`<circle cx="${f(q[0])}" cy="${f(q[1])}" r="2.5" class="dk"/>`);lv[2].forEach(q=>s+=`<circle cx="${f(q[0])}" cy="${f(q[1])}" r="3" class="r w2" fill="#fff"/>`);
   if(done.length>1)s+=`<polyline points="${pts(done)}" class="b w2"/>`;
   C.forEach(q=>s+=`<circle cx="${q[0]}" cy="${q[1]}" r="4" class="pt"/>`);const e=lv[3][0];s+=`<circle cx="${f(e[0])}" cy="${f(e[1])}" r="5" class="fb"/>`;
   return s+lab(`T ${t.toFixed(2)} · POINT ON THE CURVE`)+lab("DEGREE 3 · 4 CONTROL POINTS",W-190)},
 degree(p){const C=[[40,220],[100,70],[180,230],[250,60],[320,210],[380,90],[440,190]];const degs=[1,2,3,5];const di=Math.min(3,Math.floor(p*4));
   let s=grid()+`<polyline points="${pts(C)}" class="g dash"/>`;
   degs.forEach((d,i)=>{s+=`<polyline points="${pts(bspline(C,d))}" class="${i===di?"b w2":"k faint"}"/>`});
   C.forEach(q=>s+=`<circle cx="${q[0]}" cy="${q[1]}" r="3.5" class="pt"/>`);
   return s+lab(`DEGREE ${degs[di]}`)+lab(`${C.length} CONTROL POINTS`,W-150)},
 continuity(p){let s=grid();const mode=Math.min(2,Math.floor(p*3));const L=[[40,210],[110,90],[190,80],[240,150]];const M=L[3];
   let Q1,Q2,Q3=[440,130];
   if(mode===0){Q1=[270,230];Q2=[360,220]}
   else if(mode===1){Q1=[M[0]+(M[0]-L[2][0])*.6,M[1]+(M[1]-L[2][1])*.6];Q2=[380,250]}
   else{Q1=[2*M[0]-L[2][0],2*M[1]-L[2][1]];Q2=[L[1][0]-4*L[2][0]+4*M[0],L[1][1]-4*L[2][1]+4*M[1]];Q2=[Math.min(430,Q2[0]),Math.min(280,Q2[1])]}
   const a=Array.from({length:61},(_,i)=>bez(L,i/60)),b=Array.from({length:61},(_,i)=>bez([M,Q1,Q2,Q3],i/60));
   s+=curvComb(a,1400,2)+curvComb(b,1400,2);
   s+=`<polyline points="${pts(a)}" class="k w2"/><polyline points="${pts(b)}" class="b w2"/><circle cx="${M[0]}" cy="${M[1]}" r="4" class="pt"/>`;
   return s+lab(["G0 · POSITION","G1 · TANGENT","G2 · CURVATURE"][mode])},
 surfaces(p){let s=grid();const b1=Math.min(1,p*2),b2=Math.max(0,p*2-1),L=230,L2=340;
   const R1=b1>1e-3?L/(2*Math.PI*b1):0,R2=b2>1e-3?L2/(2*Math.PI*b2):0;
   const S=(u,v)=>{let x,z,y=(v-.5)*L2;if(b1<1e-3){x=(u-.5)*L;z=0}else{const t=(u-.5)*2*Math.PI*b1;x=R1*Math.sin(t);z=R1*(1-Math.cos(t))}
     if(b2>1e-3){const fi=(v-.5)*2*Math.PI*b2,rho=R2+R1-z;y=rho*Math.sin(fi);z=R1+R2-rho*Math.cos(fi)}
     const zc=b2*(R1+R2)*.55+b1*(1-b2)*R1*.5;
     return[240+y*.9+x*.32,190-(z-zc)*.62+x*.42]};
   const N=36;
   for(let j=0;j<=12;j++){const v=j/12;s+=`<polyline points="${pts(Array.from({length:N+1},(_,i)=>S(i/N,v)))}" class="${j===0?"b w2":"k faint2"}"/>`}
   for(let i=0;i<=8;i++){const u=i/8;s+=`<polyline points="${pts(Array.from({length:N+1},(_,j)=>S(u,j/N)))}" class="${i===0?"r w2":"k faint2"}"/>`}
   const o=S(0,0);s+=`<circle cx="${f(o[0])}" cy="${f(o[1])}" r="4" class="pt"/>`;
   return s+lab(p<.34?"PLANE · FOUR OPEN SIDES":p<.67?"CYLINDER · ONE PAIR OF SIDES MEETS AT A SEAM":"TORUS · BOTH PAIRS JOINED")+`<text x="${W-74}" y="30" class="lb" style="fill:var(--spectrum-blue)">U EDGE</text><text x="${W-74}" y="46" class="lb" style="fill:var(--spectrum-red)">V EDGE</text>`},
 booleans(p){const id="m"+(++uid);const ax=180,ay=150,r=88,bx=ax+40+p*150,by=150;
   let s=grid()+`<defs><clipPath id="${id}a"><circle cx="${ax}" cy="${ay}" r="${r}"/></clipPath><mask id="${id}b"><rect width="${W}" height="${H}" fill="#fff"/><circle cx="${bx}" cy="${by}" r="${r}" fill="#000"/></mask></defs>`;
   let hatch="";for(let x=-300;x<W;x+=9)hatch+=`<line x1="${x}" y1="0" x2="${x+H}" y2="${H}" class="rr"/>`;
   s+=`<g clip-path="url(#${id}a)" mask="url(#${id}b)">${hatch}</g>`;
   s+=`<g clip-path="url(#${id}a)"><circle cx="${bx}" cy="${by}" r="${r}" class="fb"/></g>`;
   s+=`<circle cx="${ax}" cy="${ay}" r="${r}" class="k"/><circle cx="${bx}" cy="${by}" r="${r}" class="k"/>`;
   return s+lab("A − B",ax-60,ay-r-12)+lab("A ∩ B",(ax+bx)/2-18,ay+r+22)},
 draft(p){let s=grid();const deg=Math.round(p*8),a=deg*Math.PI/180,top=70,bot=230,h=bot-top,cx=240,wb=150;const off=Math.tan(a)*h;
   const L=[[cx-wb/2-off,bot],[cx-wb/2,top]],R=[[cx+wb/2,top],[cx+wb/2+off,bot]];
   s+=`<path d="M60 ${bot}H${f(L[0][0])}L${L[1][0]} ${top}H${R[0][0]}L${f(R[1][0])} ${bot}H420V40H60Z" fill="#000" opacity=".08"/>`;
   s+=`<path d="M60 40H420" class="k faint2"/><line x1="60" y1="${bot}" x2="420" y2="${bot}" class="k"/>`;
   const ok=deg>=5,cls=ok?"b w2":"r w2";
   s+=`<polyline points="${pts([L[0],L[1],R[0],R[1]])}" class="${cls}"/>`;
   s+=`<line x1="${cx-wb/2}" y1="${top}" x2="${cx-wb/2}" y2="${bot}" class="k faint dash"/><line x1="${cx+wb/2}" y1="${top}" x2="${cx+wb/2}" y2="${bot}" class="k faint dash"/>`;
   s+=`<line x1="${cx}" y1="${top-8}" x2="${cx}" y2="22" class="k w2"/><polyline points="${cx-7},30 ${cx},22 ${cx+7},30" class="k w2"/>`;
   return s+lab(`DRAFT ${deg}° · ${deg>=6?"OK FOR PC AND ABS":deg>=5?"OK FOR ABS":"STICKS IN THE MOULD"}`)+lab("PULL",cx+12,34)},
 matching(p){let s=grid();const mode=Math.min(2,Math.floor(p*3));const A=Array.from({length:4},(_,i)=>[110,60+i*56]),B=Array.from({length:7},(_,i)=>[370,42+i*36]);
   if(mode===2)A.forEach(a=>B.forEach(b=>s+=`<line x1="${a[0]}" y1="${a[1]}" x2="${b[0]}" y2="${b[1]}" class="b faint"/>`));
   else{const n=mode===0?B.length:A.length;for(let i=0;i<n;i++){const a=A[Math.min(i,A.length-1)],b=B[i];s+=`<line x1="${a[0]}" y1="${a[1]}" x2="${b[0]}" y2="${b[1]}" class="${i>=A.length?"r":"b"} w2"/>`}}
   A.forEach(q=>s+=`<circle cx="${q[0]}" cy="${q[1]}" r="5" class="dk"/>`);B.forEach(q=>s+=`<circle cx="${q[0]}" cy="${q[1]}" r="5" class="pt"/>`);
   return s+lab(["LONGEST LIST","SHORTEST LIST","CROSS REFERENCE"][mode])+lab("A · 4 ITEMS",72,30)+lab("B · 7 ITEMS",336,30)},
 trees(p){let s=grid();const t=Math.max(0,Math.min(1,(p-.2)/.6)),e=t*t*(3-2*t);const root=[44,150];
   for(let b=0;b<4;b++){const bn=[150,48+b*68];
     s+=`<line x1="${root[0]}" y1="${root[1]}" x2="${bn[0]}" y2="${bn[1]}" class="k" opacity="${f(1-e)}"/><text x="${bn[0]-12}" y="${bn[1]-10}" class="lb" opacity="${f(1-e)}">{0;${b}}</text>`;
     for(let i=0;i<3;i++){const tree=[240+i*70,48+b*68],flat=[150+(b*3+i)*27,150];const q=[tree[0]+(flat[0]-tree[0])*e,tree[1]+(flat[1]-tree[1])*e];
       s+=`<line x1="${f(bn[0]+(150-bn[0])*e)}" y1="${f(bn[1]+(150-bn[1])*e)}" x2="${f(q[0])}" y2="${f(q[1])}" class="${["b","r","k","b"][b]}"/><circle cx="${f(q[0])}" cy="${f(q[1])}" r="5" class="${b%2?"fbs":"pt"}"/>`}}
   s+=`<line x1="${root[0]}" y1="${root[1]}" x2="150" y2="150" class="k" opacity="${f(e)}"/><circle cx="${root[0]}" cy="${root[1]}" r="6" class="dk"/>`;
   return s+lab(e<.5?"TREE · 4 BRANCHES × 3":"FLATTEN · 1 LIST × 12")},
 remap(p){let s=grid();const c=[[0,0],[.15+p*.7,.9-p*.8],[1,1]];const g=x=>{let t=x;for(let k=0;k<20;k++){const b=bez(c,t);t-= (b[0]-x)*.9}return bez(c,t)[1]};
   const x0=40,x1=320,ty=60,by=240;s+=`<line x1="${x0}" y1="${ty}" x2="${x1}" y2="${ty}" class="k"/><line x1="${x0}" y1="${by}" x2="${x1}" y2="${by}" class="k"/>`;
   for(let i=0;i<=12;i++){const u=i/12,v=g(u);s+=`<line x1="${f(x0+u*(x1-x0))}" y1="${ty}" x2="${f(x0+v*(x1-x0))}" y2="${by}" class="b"/><circle cx="${f(x0+u*(x1-x0))}" cy="${ty}" r="3" class="dk"/><circle cx="${f(x0+v*(x1-x0))}" cy="${by}" r="3" class="pt"/>`}
   const gx=350,gy=90,gs=110;s+=`<rect x="${gx}" y="${gy}" width="${gs}" height="${gs}" class="k"/>`+`<polyline points="${pts(Array.from({length:41},(_,i)=>{const b=bez(c,i/40);return[gx+b[0]*gs,gy+gs-b[1]*gs]}))}" class="r w2"/>`;
   return s+lab("INPUT 0–1",x0,ty-12)+lab("REMAPPED",x0,by+24)+lab("GRAPH MAPPER",gx,gy-10)},
 stagger(p){let s="";const off=p,rows=9,cols=11,gx=40,gy=30;for(let j=0;j<rows;j++)for(let i=0;i<cols;i++){const x=30+i*gx+(j%2?off*gx/2:0),y=30+j*gy;s+=`<rect x="${f(x)}" y="${y-5}" width="26" height="10" rx="5" class="${j%2?"r":"b"} w2" fill="none"/>`}
   return s+lab(`STAGGER ${Math.round(off*50)}% · ODD ROWS DISPATCHED AND SHIFTED`)},
 attractor(p){let s=grid();const nu=11,nv=6;const A=[60+p*360,80+60*Math.sin(p*6)];
   const X=(u,v)=>[50+u*380+18*Math.sin(v*3+u*2),50+v*200+26*Math.sin(u*Math.PI*2)];
   for(let i=0;i<=nu;i++){s+=`<polyline points="${pts(Array.from({length:21},(_,k)=>X(i/nu,k/20)))}" class="k faint"/>`}
   for(let j=0;j<=nv;j++){s+=`<polyline points="${pts(Array.from({length:41},(_,k)=>X(k/40,j/nv)))}" class="k faint"/>`}
   for(let i=0;i<=nu;i++)for(let j=0;j<=nv;j++){const q=X(i/nu,j/nv);const d=Math.hypot(q[0]-A[0],q[1]-A[1]);const r=Math.max(1.4,9-d/22);s+=`<circle cx="${f(q[0])}" cy="${f(q[1])}" r="${f(r)}" class="${d<90?"fbs":"dk"}"/>`}
   s+=`<circle cx="${f(A[0])}" cy="${f(A[1])}" r="5" class="r w2" fill="none"/>`;
   return s+lab("ATTRACTOR · NODE RADIUS")},
 cosine(p){let s=grid();const waves=1+Math.round(p*5),A=40;for(let k=0;k<3;k++){const pp=[];for(let i=0;i<=120;i++){const x=40+i*3.3,u=i/120*waves*Math.PI;pp.push([x,90+k*60-Math.cos(u)*A*(k===1?.5:1)])}
   s+=`<polyline points="${pts(pp)}" class="${k===1?"r":"b"} w2"/>`}
   return s+lab(`COSINE OF 0 TO ${waves}π · ${waves} HALF-WAVES · MIDDLE CURVE TWEENED`)},
 sampler(p){let s="";const n=14,g=W/(n+2),r0=g*.48;const img=(x,y)=>{const a=Math.sin(x/60)+Math.cos(y/45),b=Math.exp(-((x-330)**2+(y-140)**2)/9000);return Math.max(0,Math.min(1,.5+.25*a+.6*b))};
   for(let i=0;i<n;i++)for(let j=0;j<8;j++){const x=g*(i+1.5),y=34+j*32,v=img(x,y),lo=.08+.3*p,rr=r0*(lo+(1-lo)*v);s+=`<circle cx="${f(x)}" cy="${f(y)}" r="${f(rr)}" class="dk"/>`}
   return s+lab(`IMAGE SAMPLER · BRIGHTNESS → RADIUS · REMAP MIN ${(0.08+.3*p).toFixed(2)}`)},
 weave(p){let s=grid();const nu=14,nv=3;const pat=[0,1,1,0];const X=(u,v)=>[40+u*400,90+v*130+36*Math.sin(u*Math.PI*2+p*Math.PI*2)-v*10*Math.cos(u*6)];
   for(let i=0;i<nu;i++)for(let j=0;j<nv;j++){const a=X(i/nu,j/nv),b=X((i+1)/nu,j/nv),c=X((i+1)/nu,(j+1)/nv),d=X(i/nu,(j+1)/nv);
     const m=[[(a[0]+b[0])/2,(a[1]+b[1])/2],[(b[0]+c[0])/2,(b[1]+c[1])/2],[(c[0]+d[0])/2,(c[1]+d[1])/2],[(d[0]+a[0])/2,(d[1]+a[1])/2]];
     s+=`<polygon points="${pts([a,b,c,d])}" class="k faint"/><polygon points="${pts(m)}" class="${pat[(i+j)%4]?"fb":"fk"}"/>`}
   return s+lab("BOX MORPH · WEAVE 0 1 1 0")},
 cage(p){let s=grid();const n=1+Math.min(3,Math.floor(p*4)),xs=[50,95,140,185,230,275,320,365,410],sy=210,py=110;
   const P=xs.map((x,i)=>[x,i>=xs.length-n?sy:py]);const c=bspline(P,3,140);
   s+=`<line x1="410" y1="${sy}" x2="470" y2="${sy}" class="k w2"/><text x="420" y="${sy+18}" class="lb">SURFACE</text>`;
   s+=`<polyline points="${pts(P)}" class="g dash"/>`;
   s+=`<polyline points="${pts(c)}" class="${n>=3?"b":"r"} w2"/>`;
   P.forEach((q,i)=>s+=`<circle cx="${q[0]}" cy="${q[1]}" r="${i>=xs.length-n?5:3.5}" class="${i>=xs.length-n?"fb":"pt"}"/>`);
   s+=`<text x="50" y="${py-14}" class="lb">PATTERN · DEGREE 3 CAGE</text>`;
   const g=["G0 · TOUCHES, CREASE SHOWS","G1 · TANGENT, HIGHLIGHT BREAKS","G2 · CURVATURE, SMOOTH FADE","G2+ · SOFTER, LONGER FADE"][n-1];
   return s+lab(`${n} ROW${n>1?"S":""} COLLAPSED · ${g}`)},
 panels(p){let s="";const k=1+Math.round(p*7),R=17,cols=13,rows=7,pal=["#0036f9","#59c0e6","#8a3ffc","#e50000","#ffb000","#2e8540","#c9c9c9","#000"];
   const area=(i,j)=>.55+.45*Math.sin(i*.45)*Math.cos(j*.6+i*.15);
   const cells=[];for(let j=0;j<rows;j++)for(let i=0;i<cols;i++){const x=40+i*R*1.75+(j%2?R*.875:0),y=34+j*R*1.5,a=area(i,j);cells.push([x,y,a])}
   const lo=Math.min(...cells.map(c=>c[2])),hi=Math.max(...cells.map(c=>c[2]));
   cells.forEach(([x,y,a])=>{const g=Math.min(k-1,Math.floor((a-lo)/(hi-lo+1e-9)*k)),r=R*(.62+.36*a);let d="";for(let m=0;m<6;m++){const t=Math.PI/3*m+Math.PI/6;d+=(m?"L":"M")+f(x+r*Math.cos(t))+" "+f(y+r*Math.sin(t))}
     s+=`<path d="${d}Z" fill="${pal[g%pal.length]}" fill-opacity="${k===1?.25:.85}" stroke="#000" stroke-width=".6"/>`});
   return s+lab(`${cells.length} PANELS → ${k} SHAPE${k>1?"S":""} TO MAKE · CLUSTERED BY AREA`)},
 contour(p){let s=grid();const d=8+Math.round(p*32),y0=262,h=210,cx=240;
   const r=t=>48+30*Math.sin(t*Math.PI*1.15+.4)+14*Math.sin(t*Math.PI*3.2);
   const L=[],Rr=[];for(let i=0;i<=60;i++){const t=i/60;L.push([cx-r(t),y0-t*h]);Rr.push([cx+r(t),y0-t*h])}
   for(let z=0;z<=h;z+=d){const t=z/h,rr=r(t),y=y0-z;s+=`<ellipse cx="${cx}" cy="${f(y)}" rx="${f(rr)}" ry="${f(rr*.22)}" class="b"/>`}
   s+=`<polyline points="${pts(L)}" class="k w2"/><polyline points="${pts(Rr)}" class="k w2"/>`;
   s+=`<line x1="${cx+120}" y1="${y0}" x2="${cx+120}" y2="${y0-d}" class="r w2"/><line x1="${cx+112}" y1="${y0}" x2="${cx+128}" y2="${y0}" class="r"/><line x1="${cx+112}" y1="${y0-d}" x2="${cx+128}" y2="${y0-d}" class="r"/>`;
   return s+lab(`CONTOUR · DISTANCE ${d}`)+lab(`${Math.floor(h/d)+1} SECTIONS`,W-120)},
 gyroid(p){let s="";const L=70+p*110,c=5,t=.3;for(let x=0;x<W;x+=c)for(let y=0;y<H-30;y+=c){const u=(x+c/2)/L*2*Math.PI,v=(y+c/2)/L*2*Math.PI,w=1.3;const g=Math.sin(u)*Math.cos(v)+Math.sin(v)*Math.cos(w)+Math.sin(w)*Math.cos(u);if(Math.abs(g)<t)s+=`<rect x="${x}" y="${y}" width="${c}" height="${c}" class="dk"/>`}
   return s+lab(`GYROID SLICE · WAVELENGTH ${L.toFixed(0)} · SHELL = THIN BAND AROUND ZERO`)},
 voxels(p){let s="";const vs=Math.round(40-34*p),cx=240,cy=150,R=95;for(let x=cx-R-vs;x<cx+R+vs;x+=vs)for(let y=cy-R-vs;y<cy+R+vs;y+=vs){const mx=x+vs/2,my=y+vs/2,d=Math.hypot(mx-cx,(my-cy)*1.3)-R+18*Math.sin(mx/18);if(d<0)s+=`<rect x="${x}" y="${y}" width="${vs}" height="${vs}" class="dk" opacity=".85"/>`}
   s+=`<ellipse cx="${cx}" cy="${cy}" rx="${R}" ry="${f(R/1.3)}" class="r dash" fill="none"/>`;
   return s+lab(`VOXEL SIZE ${vs} · SMALLER = MORE DETAIL, SLOWER`)},
 topology(p){let s=grid();const it=Math.round(p*40),k=Math.min(1,it/30);
   const N=[[30,40],[30,145],[30,250],[140,60],[140,145],[140,230],[250,85],[250,145],[250,205],[360,115],[360,175],[455,150]];
   const keep=new Set(["0-3","3-6","6-9","9-11","2-5","5-8","8-10","10-11","1-4","4-7","7-9","7-10","3-4","4-5","0-4","2-4","6-7","8-7","4-6","4-8"]);
   const main=new Set(["0-3","3-6","6-9","9-11","2-5","5-8","8-10","10-11"]);
   let e="",w="";for(let i=0;i<N.length;i++)for(let j=i+1;j<N.length;j++){const d=Math.hypot(N[i][0]-N[j][0],N[i][1]-N[j][1]);if(d>160)continue;
     const key=i+"-"+j,kk=keep.has(key)||keep.has(j+"-"+i),mm=main.has(key);
     const width=kk?(mm?2+10*k:2+4*k):2*(1-k),op=kk?.35+.65*k:.35*(1-k);if(width<.15||op<.02)continue;
     (kk?w:e);const ln=`<line x1="${N[i][0]}" y1="${N[i][1]}" x2="${N[j][0]}" y2="${N[j][1]}" stroke="#000" stroke-opacity="${op.toFixed(2)}" stroke-width="${width.toFixed(1)}" stroke-linecap="round"/>`;if(kk)w+=ln;else e+=ln}
   s+=e+w;N.forEach((q,i)=>{const r=1.5+3.5*k;s+=`<circle cx="${q[0]}" cy="${q[1]}" r="${r.toFixed(1)}" fill="#000"/>`});
   s+=`<line x1="18" y1="30" x2="18" y2="260" class="r w2"/>`;for(let y=36;y<260;y+=16)s+=`<line x1="18" y1="${y}" x2="10" y2="${y+8}" class="r"/>`;
   s+=`<line x1="455" y1="160" x2="455" y2="205" class="b w2"/><polyline points="449,196 455,207 461,196" class="b w2" fill="none"/>`;
   return s+lab(`TOPOLOGY OPTIMIZATION · ITERATION ${it}`)},
 evolve(p){let s=grid();const g=Math.round(p*20),rnd=mulberry(7),T=[360,90],spread=150*Math.exp(-g/6)+6;let best=1e9;
   s+=`<circle cx="${T[0]}" cy="${T[1]}" r="9" class="r w2" fill="none"/><text x="${T[0]+14}" y="${T[1]+4}" class="lb">FOOD</text>`;
   const cx=120+(T[0]-120)*(1-Math.exp(-g/5)),cy=210+(T[1]-210)*(1-Math.exp(-g/5));
   for(let i=0;i<40;i++){const x=cx+(rnd()-.5)*2*spread,y=cy+(rnd()-.5)*2*spread*.7,d=Math.hypot(x-T[0],y-T[1]);best=Math.min(best,d);s+=`<circle cx="${f(x)}" cy="${f(y)}" r="3" class="dk" opacity=".7"/>`}
   return s+lab(`GENERATION ${g} · 40 DESIGNS · BEST DISTANCE ${best.toFixed(0)}`)},
 bump(p){let s=grid();const amp=4+14*p,N=160,y0=170;const pr=x=>Math.sin(x/9)*.5+Math.sin(x/23)*.5;
   const flat=[],disp=[];for(let i=0;i<=N;i++){const x=40+i*2.5,h=pr(x);flat.push([x,y0]);disp.push([x,y0-30-amp*h-amp])}
   s+=`<text x="40" y="60" class="lb">DISPLACEMENT · GEOMETRY MOVES</text><polyline points="${pts(disp)}" class="b w2"/>`;
   for(let i=0;i<=N;i+=4){const x=40+i*2.5,h=pr(x);s+=`<line x1="${x}" y1="${y0+40}" x2="${f(x+6*h*p+2)}" y2="${y0+32}" class="k faint2"/>`}
   s+=`<line x1="40" y1="${y0+40}" x2="440" y2="${y0+40}" class="k w2"/><text x="40" y="${y0+62}" class="lb">BUMP · SAME FLAT EDGE, ONLY THE SHADING NORMALS TILT</text>`;
   return s+lab(`HEIGHT ${amp.toFixed(0)} · SILHOUETTE ONLY CHANGES WITH DISPLACEMENT`,16,24)},
 light(p){const id="s"+(++uid);let s=grid();const Rl=1+p*30,Lc=[78,92],O=[190,176],ro=30,gy=252,cl=x=>Math.max(20,Math.min(W-20,x));
   const dx=O[0]-Lc[0],dy=O[1]-Lc[1],dl=Math.hypot(dx,dy),mx=-dy/dl,my=dx/dl;
   const E=[[Lc[0]+mx*Rl,Lc[1]+my*Rl],[Lc[0]-mx*Rl,Lc[1]-my*Rl]];
   const iv=P0=>{const ex=O[0]-P0[0],ey=O[1]-P0[1],dd=Math.hypot(ex,ey),al=Math.atan2(ey,ex),be=Math.asin(ro/dd);
     return [al-be,al+be].map(th=>{const t=(gy-P0[1])/Math.sin(th);return P0[0]+t*Math.cos(th)}).sort((a,b)=>a-b)};
   const I=E.map(iv),ua=cl(Math.max(I[0][0],I[1][0])),ub=cl(Math.min(I[0][1],I[1][1])),pa=cl(Math.min(I[0][0],I[1][0])),pb=cl(Math.max(I[0][1],I[1][1]));
   E.forEach((e,k)=>iv(e).forEach(x=>s+=`<line x1="${f(e[0])}" y1="${f(e[1])}" x2="${f(cl(x))}" y2="${f(x>W-20?gy-(x-(W-20))*(gy-e[1])/(x-e[0]):gy)}" class="${k?"b":"r"} faint2"/>`));
   s+=`<defs><linearGradient id="${id}l"><stop offset="0" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000"/></linearGradient><linearGradient id="${id}r"><stop offset="0" stop-color="#000"/><stop offset="1" stop-color="#000" stop-opacity="0"/></linearGradient></defs>`;
   s+=`<line x1="20" y1="${gy}" x2="${W-20}" y2="${gy}" class="k"/>`;
   if(ua>pa)s+=`<rect x="${f(pa)}" y="${gy+2}" width="${f(ua-pa)}" height="14" fill="url(#${id}l)"/>`;
   if(ub>ua)s+=`<rect x="${f(ua)}" y="${gy+2}" width="${f(ub-ua)}" height="14" class="fk"/>`;
   if(pb>ub)s+=`<rect x="${f(ub)}" y="${gy+2}" width="${f(pb-ub)}" height="14" fill="url(#${id}r)"/>`;
   s+=`<circle cx="${O[0]}" cy="${O[1]}" r="${ro}" class="k w2"/><circle cx="${Lc[0]}" cy="${Lc[1]}" r="${f(Math.max(2.5,Rl))}" class="pt"/><line x1="${f(E[0][0])}" y1="${f(E[0][1])}" x2="${f(E[1][0])}" y2="${f(E[1][1])}" class="r w2"/>`;
   return s+lab(`LIGHT RADIUS ${Math.round(Rl)}`,16,30)+lab(Rl<4?"POINT LIGHT · SHARP SHADOW":"BIG LIGHT · SOFT FALLOFF")},
 samples(p){let s=grid();const X=x=>50+x*390,Y=q=>250-q*200,q=x=>1-Math.exp(-4*x),pts2=[];for(let i=0;i<=60;i++){const x=i/60;pts2.push([X(x),Y(q(x))])}
   s+=`<line x1="50" y1="250" x2="440" y2="250" class="k"/><line x1="50" y1="250" x2="50" y2="40" class="k"/><polyline points="${pts(pts2)}" class="b w2"/>`;
   const x=.05+.9*p,x2=Math.min(1,x*2);s+=`<line x1="${f(X(x))}" y1="${f(Y(q(x)))}" x2="${f(X(x))}" y2="250" class="k dash"/><circle cx="${f(X(x))}" cy="${f(Y(q(x)))}" r="5" class="fb"/>`;
   if(x2>x)s+=`<circle cx="${f(X(x2))}" cy="${f(Y(q(x2)))}" r="5" class="r w2" fill="#fff"/>`;
   s+=`<text x="54" y="36" class="lb">QUALITY</text><text x="380" y="270" class="lb">SAMPLES</text>`;
   return s+lab(`2× SAMPLES = 2× TIME · QUALITY +${Math.round((q(x2)-q(x))*100)}%`)}
};
const FIG=[{"id": "nurbs", "g": "Geometry", "t": "How a NURBS curve is built", "c": "From four control points, take the point at t along each line, then again, until one point is left on the curve."}, {"id": "degree", "g": "Geometry", "t": "Curve degree", "c": "The same seven control points read at degree 1, 2, 3 and 5. Higher degree, smoother and lazier curve."}, {"id": "continuity", "g": "Geometry", "t": "Continuity", "c": "Curvature combs across a G0, G1 and G2 joint. The comb shows where a surface will catch the light badly."}, {"id": "surfaces", "g": "Geometry", "t": "Four-sided surfaces", "c": "A flat sheet rolls into a cylinder, then a torus; its U and V edges become seams."}, {"id": "booleans", "g": "Geometry", "t": "Boolean sets", "c": "Intersection in blue, difference hatched in red, as one solid slides through the other."}, {"id": "draft", "g": "Geometry", "t": "Draft angle", "c": "Moulded walls tilt so the part can leave the tool. Below about 5° for ABS or 6° for PC, the walls turn red."}, {"id": "matching", "g": "Data", "t": "Data matching", "c": "Longest list, shortest list, cross reference: three ways to pair two lists of different lengths."}, {"id": "trees", "g": "Data", "t": "Data trees", "c": "Four branches of three items, flattened into a single list."}, {"id": "remap", "g": "Data", "t": "Remap", "c": "Even inputs bent through a graph into shaped outputs."}, {"id": "stagger", "g": "Data", "t": "Staggered rows", "c": "Odd rows split into their own list and shifted by half a gap."}, {"id": "attractor", "g": "Pattern", "t": "Attractor field", "c": "Quads on a warped surface, each node sized by its distance to a point."}, {"id": "cosine", "g": "Pattern", "t": "Cosine texture", "c": "A range from 0 to nπ fed through cosine and scaled; the middle curve is a tween."}, {"id": "sampler", "g": "Pattern", "t": "Image sampler", "c": "Each point reads the brightness under it, and that number sets the circle."}, {"id": "weave", "g": "Pattern", "t": "Box morph weave", "c": "A 0 1 1 0 over-under weave morphed onto a curved strip."}, {"id": "cage", "g": "Pattern", "t": "Fading with a cage", "c": "Collapse cage rows onto the surface: one row touches (G0), two go tangent (G1), three match curvature (G2)."}, {"id": "panels", "g": "Fabrication", "t": "Panel rationalization", "c": "Every hexagon is slightly different. Clustering by area turns hundreds of panels into a few shapes to make."}, {"id": "contour", "g": "Fabrication", "t": "Contour", "c": "A form sliced at a set distance into buildable sections."}, {"id": "gyroid", "g": "Fabrication", "t": "Gyroid", "c": "A slice through a triply periodic field, keeping only the thin band near zero as a shell."}, {"id": "voxels", "g": "Fabrication", "t": "Voxels", "c": "The shape filled with small cubes, so unions and smoothing never fail."}, {"id": "topology", "g": "Fabrication", "t": "Topology optimization", "c": "A dense web between support and load; each step keeps the members that carry the force."}, {"id": "evolve", "g": "Fabrication", "t": "Evolutionary search", "c": "Each dot is a design. Every generation the best survive and breed toward the target."}, {"id": "bump", "g": "Render", "t": "Bump vs displacement", "c": "Bump only tilts the shading, so the edge stays flat; displacement really moves the surface."}, {"id": "light", "g": "Render", "t": "Light size and shadow", "c": "The bigger the light, the softer the shadow it casts."}, {"id": "samples", "g": "Render", "t": "Samples and quality", "c": "Double the samples, double the time, but each doubling buys less quality."}];
const DEF={nurbs:.45,degree:.6,continuity:.9,surfaces:.55,booleans:.35,draft:.4,matching:.1,trees:.15,remap:.3,stagger:1,attractor:.4,cosine:0.4,sampler:0.3,weave:.2,cage:.6,panels:.4,contour:.35,gyroid:.3,voxels:0.5,topology:.7,evolve:.35,bump:0.5,light:.15,samples:0.3};
const CAP=Object.fromEntries(FIG.map(f=>[f.id,f.t+": "+f.c]));
function svg(id,p){return `<svg viewBox="0 0 ${W} ${H}" class="pl" role="img" aria-label="${(CAP[id]||"").split(":")[0]}">${P[id](p)}</svg>`}
function mount(el){
  const id=el.dataset.fig; if(!P[id]) return;
  let p=DEF[id]??.5, target=p, raf=0;
  const draw=()=>{p+=(target-p)*.25;if(Math.abs(target-p)<.002)p=target;el.innerHTML=svg(id,p);if(p!==target)raf=requestAnimationFrame(draw);else raf=0};
  el.innerHTML=svg(id,p);
  const set=v=>{target=Math.max(0,Math.min(1,v));if(!raf)raf=requestAnimationFrame(draw)};
  el.addEventListener("pointermove",e=>{const r=el.getBoundingClientRect();set((e.clientX-r.left)/r.width)});
  el.addEventListener("pointerleave",()=>set(DEF[id]??.5));
  el.tabIndex=0; el.setAttribute("role","group"); el.setAttribute("aria-label",(CAP[id]||"Figure")+" Use left and right arrow keys to change it.");
  el.addEventListener("keydown",e=>{if(e.key==="ArrowRight"){e.preventDefault();set(target+.05)}if(e.key==="ArrowLeft"){e.preventDefault();set(target-.05)}});
}
window.TigreFigures={list:FIG,svg,mountAll:root=>root.querySelectorAll("[data-fig]").forEach(mount)};
})();
