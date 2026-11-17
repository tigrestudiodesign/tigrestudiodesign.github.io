// Summit Claws: draws the rig sheet and captures gameplay screens straight from the game's own
// canvas code (games/summit-claws.html). No sprites, no generated images.
// Usage: python3 -m http.server 8765 &  then
//   FONTS=/path/to/node_modules/@fontsource node tools/summit_claws_rig.js <outdir>
// Needs the npm packages @fontsource/bungee and @fontsource/barlow-condensed (the game's Google Fonts).
const {chromium}=require('playwright');
const fs=require('fs'),path=require('path');
const OUT=process.argv[2]||'.';const FS=process.env.FONTS;const BASE='http://localhost:8765/';

async function prep(page){
 await page.route('https://fonts.googleapis.com/**',r=>{
  const ff=(fam,w,file)=>`@font-face{font-family:"${fam}";font-weight:${w};src:url(/__fs/${file})}`;
  r.fulfill({contentType:'text/css',body:[ff('Bungee',400,'bungee/files/bungee-latin-400-normal.woff2'),
   ...[500,600,700].map(w=>ff('Barlow Condensed',w,`barlow-condensed/files/barlow-condensed-latin-${w}-normal.woff2`))].join('\n')});
 });
 await page.route('**/__fs/**',r=>r.fulfill({contentType:'font/woff2',body:fs.readFileSync(path.join(FS,r.request().url().split('/__fs/')[1]))}));
 await page.route('**/games/summit-claws.html',async r=>{
  const res=await r.fetch();let t=await res.text();
  const k=t.lastIndexOf('requestAnimationFrame(frame);');
  t=t.slice(0,k)+'window.__SC={ANIMALS,FURS,drawAnimal,mix,rr,W,H,keys,startGame,showOnly,get G(){return G},get look(){return look},set look(v){look=v}};'+t.slice(k);
  r.fulfill({response:res,body:t});
 });
}

const SHEET=()=>{
 const S=window.__SC,A=S.ANIMALS;const WD=1600,HT=1860,DPR=2;
 const cv=document.createElement('canvas');cv.id='rig';cv.width=WD*DPR;cv.height=HT*DPR;
 cv.style.cssText=`position:fixed;left:0;top:0;width:${WD}px;height:${HT}px;z-index:99`;document.body.appendChild(cv);
 const c=cv.getContext('2d');c.scale(DPR,DPR);
 const INK='#0B0B0C',OR='#FF5A1F',PAPER='#F2EEE6',MUT='rgba(242,238,230,.52)',LINE='rgba(242,238,230,.16)';
 const MONO='"JetBrains Mono", monospace',DISP='"Inter Display", sans-serif';
 c.fillStyle=INK;c.fillRect(0,0,WD,HT);
 for(let x=0;x<=WD;x+=20){c.fillStyle=x%100?'rgba(255,255,255,.035)':'rgba(255,255,255,.07)';c.fillRect(x,0,1,HT)}
 for(let y=0;y<=HT;y+=20){c.fillStyle=y%100?'rgba(255,255,255,.035)':'rgba(255,255,255,.07)';c.fillRect(0,y,WD,1)}
 const txt=(s,x,y,f,col,al='left')=>{c.font=f;c.fillStyle=col;c.textAlign=al;c.fillText(s,x,y)};
 const ticks=(x,y,w,h,col=OR,l=10)=>{c.strokeStyle=col;c.lineWidth=2;c.beginPath();
  for(const[px,py,dx,dy]of[[x,y,1,1],[x+w,y,-1,1],[x,y+h,1,-1],[x+w,y+h,-1,-1]]){c.moveTo(px+dx*l,py);c.lineTo(px,py);c.lineTo(px,py+dy*l)}c.stroke()};
 const box=(x,y,w,h)=>{c.strokeStyle=LINE;c.lineWidth=1;c.strokeRect(x+.5,y+.5,w-1,h-1);ticks(x,y,w,h)};
 // T mark
 const T=(x,y,s)=>{c.fillStyle=OR;c.fillRect(x,y,24*s,6*s);c.fillRect(x+9*s,y,6*s,28*s)};
 // header
 T(48,40,1.3);
 txt('FIG. SC-01  ·  SUMMIT CLAWS  ·  CHARACTER SYSTEM',90,58,`700 13px ${MONO}`,OR);
 txt('ONE RIG, EIGHT ANIMALS',48,118,`900 52px ${DISP}`,PAPER);
 txt('5 PART SLOTS  ·  12 FURS  ·  4 GEAR  ·  4 STATS + 1 PERK',WD-48,58,`400 13px ${MONO}`,MUT,'right');
 txt('drawAnimal(ctx, x, y, dir, look, t)',WD-48,112,`400 15px ${MONO}`,PAPER,'right');
 // mirrored spectrum stripe, amber at centre
 const g=c.createLinearGradient(48,0,WD-48,0);
 [['#2D7FF9',0],['#7A2BD9',.18],['#E8203A',.36],['#FFB000',.5],['#E8203A',.64],['#7A2BD9',.82],['#2D7FF9',1]].forEach(([col,o])=>g.addColorStop(o,col));
 c.fillStyle=g;c.fillRect(48,140,WD-96,3);

 // ---- section A: lineup
 txt('A  /  THE EIGHT ANIMALS',48,186,`700 13px ${MONO}`,OR);
 txt('SAME BODY, LEGS AND HEAD. ONLY THE PARAMETERS CHANGE.',WD-48,186,`400 12px ${MONO}`,MUT,'right');
 const keys=Object.keys(A).filter(k=>k!=='tmp');
 const rng=(k)=>{const v=keys.map(a=>A[a][k]);return[Math.min(...v),Math.max(...v)]};
 const R={speed:rng('speed'),jump:rng('jump'),power:rng('power'),hp:rng('hp')};
 const cw=(WD-96-3*16)/4,ch=250;
 keys.forEach((k,i)=>{const a=A[k],x=48+(i%4)*(cw+16),y=204+Math.floor(i/4)*(ch+16);
  c.fillStyle='rgba(242,238,230,.025)';c.fillRect(x,y,cw,ch);box(x,y,cw,ch);
  txt(String(i+1).padStart(2,'0'),x+16,y+28,`700 12px ${MONO}`,OR);
  txt(a.name.toUpperCase(),x+44,y+29,`700 19px ${DISP}`,PAPER);
  // ground line + crosshair
  const gx=x+118,gy=y+172;c.fillStyle='rgba(242,238,230,.22)';c.fillRect(x+16,gy,200,1);
  c.fillStyle=OR;c.fillRect(gx-1,gy-5,2,10);
  c.save();c.translate(gx,gy);c.scale(2.7,2.7);S.drawAnimal(c,0,0,1,{animal:k,fur:a.fur,pattern:'auto',gear:'none'},.35,{noShadow:true});c.restore();
  // spec column
  const sx=x+cw-128;const rows=[['EARS',a.ears],['TAIL',a.tail],['SNOUT',a.snout],['MARK',a.pattern],['SIZE',a.size.toFixed(2)]];
  rows.forEach(([kk,v],j)=>{txt(kk,sx,y+64+j*20,`400 11px ${MONO}`,MUT);txt(v.toUpperCase(),sx+112,y+64+j*20,`700 11px ${MONO}`,PAPER,'right')});
  c.fillStyle=a.fur;c.fillRect(sx,y+172,14,14);c.strokeStyle=LINE;c.strokeRect(sx+.5,y+172.5,13,13);
  txt(a.fur.toUpperCase(),sx+22,y+184,`400 11px ${MONO}`,MUT);
  // stat bars
  const st=[['SPD','speed'],['JMP','jump'],['PWR','power'],['HP','hp']];
  st.forEach(([lab,key],j)=>{const bx=x+16+j*((cw-32)/4),bw=(cw-32)/4-12,by=y+204;
   txt(lab+' '+a[key],bx,by,`400 10px ${MONO}`,MUT);
   const f=.18+.82*(a[key]-R[key][0])/((R[key][1]-R[key][0])||1);
   c.fillStyle='rgba(242,238,230,.12)';c.fillRect(bx,by+10,bw,5);c.fillStyle=OR;c.fillRect(bx,by+10,bw*f,5)});
  const perk=a.perk.replace(/<[^>]+>/g,'').split('.')[0];
  txt('PERK  '+perk.toUpperCase(),x+16,y+ch-14,`700 10px ${MONO}`,OR);
 });

 // ---- section B: parameter sweep
 const by0=204+2*(ch+16)+40;
 txt('B  /  PARAMETER SWEEP',48,by0,`700 13px ${MONO}`,OR);
 txt('BASE: GRAY WOLF. EACH ROW CHANGES ONE INPUT AND HOLDS THE REST.',WD-48,by0,`400 12px ${MONO}`,MUT,'right');
 const base=Object.assign({},A.wolf);
 const rowsB=[
  ['EARS','ears',['point','big','tufts','round','horns','tiny']],
  ['TAIL','tail',['bushy','fox','long','stub']],
  ['SNOUT','snout',['long','short','goat']],
  ['MARKINGS','pattern',['none','stripes','spots','badger']],
  ['GEAR','gear',['none','scarf','helmet','pack']],
  ['SIZE','size',[.9,.95,1,1.05,1.15]],
 ];
 const lx=48,lw=196,gx0=lx+lw,gw=WD-48-gx0,rh=132;
 rowsB.forEach(([lab,key,opts],r)=>{const y=by0+18+r*(rh+10);
  c.fillStyle='rgba(242,238,230,.025)';c.fillRect(lx,y,WD-96,rh);box(lx,y,WD-96,rh);
  txt(lab,lx+18,y+50,`900 24px ${DISP}`,PAPER);
  txt(String(opts.length).padStart(2,'0')+' OPTIONS',lx+18,y+74,`400 11px ${MONO}`,MUT);
  const n=6,cwB=gw/n;
  opts.forEach((o,j)=>{const cx=gx0+j*cwB;
   if(j){c.fillStyle=LINE;c.fillRect(cx,y+14,1,rh-28)}
   A.tmp=Object.assign({},base);let lk={animal:'tmp',fur:base.fur,pattern:'auto',gear:'none'};
   if(key==='gear')lk.gear=o;else A.tmp[key]=o;
   const ox=cx+cwB/2-6,oy=y+96;
   c.save();c.translate(ox,oy);c.scale(1.55,1.55);S.drawAnimal(c,0,0,1,lk,.35,{noShadow:true});c.restore();
   const on=(key==='gear'?o==='none':base[key]===o);
   txt((typeof o==='number'?o.toFixed(2):o).toUpperCase(),cx+cwB/2,y+rh-12,`700 11px ${MONO}`,on?OR:PAPER,'center');
  });
 });
 delete A.tmp;
 // furs strip
 const fy=by0+18+rowsB.length*(rh+10);
 c.fillStyle='rgba(242,238,230,.025)';c.fillRect(lx,fy,WD-96,rh);box(lx,fy,WD-96,rh);
 txt('FUR',lx+18,fy+50,`900 24px ${DISP}`,PAPER);txt(String(S.FURS.length)+' OPTIONS',lx+18,fy+74,`400 11px ${MONO}`,MUT);
 const cwF=gw/S.FURS.length;
 S.FURS.forEach((f,j)=>{const cx=gx0+j*cwF;
  c.save();c.translate(cx+cwF/2-2,fy+94);c.scale(1.05,1.05);S.drawAnimal(c,0,0,1,{animal:'wolf',fur:f,pattern:'auto',gear:'none'},.35,{noShadow:true});c.restore();
  txt(f.slice(1).toUpperCase(),cx+cwF/2,fy+rh-12,`400 10px ${MONO}`,j===0?OR:MUT,'center')});
 // footer
 txt('EVERY FRAME ABOVE IS DRAWN LIVE BY THE GAME\'S OWN drawAnimal() ON A CANVAS. NO SPRITES, NO BITMAPS.',48,HT-28,`400 12px ${MONO}`,MUT);
 txt('TIGRE STUDIO  ·  H. ORTEGA',WD-48,HT-28,`700 12px ${MONO}`,OR,'right');
 return [WD,HT];
};

(async()=>{
 const b=await chromium.launch({executablePath:'/usr/bin/google-chrome'});
 // 1. rig sheet
 {const p=await b.newPage({viewport:{width:1600,height:1860},deviceScaleFactor:2});await prep(p);
  await p.goto(BASE+'games/summit-claws.html');
  await p.addStyleTag({content:'@font-face{font-family:"Inter Display";font-weight:900;src:url(/fonts/InterDisplay-Black.woff2)}@font-face{font-family:"Inter Display";font-weight:700;src:url(/fonts/InterDisplay-Bold.woff2)}@font-face{font-family:"JetBrains Mono";font-weight:400;src:url(/fonts/JetBrainsMono-400.woff2)}@font-face{font-family:"JetBrains Mono";font-weight:700;src:url(/fonts/JetBrainsMono-700.woff2)}'});
  await p.evaluate(async()=>{for(const f of['900 20px "Inter Display"','700 20px "Inter Display"','400 12px "JetBrains Mono"','700 12px "JetBrains Mono"'])await document.fonts.load(f)});
  await p.waitForFunction(()=>window.__SC);
  await p.evaluate(SHEET);
  await p.locator('#rig').screenshot({path:path.join(OUT,'sc_rig.png')});await p.close()}
 // 2. ice screen: red fox in a scarf high on the ice band, near Camp III
 {const p=await b.newPage({viewport:{width:480,height:800},deviceScaleFactor:2});await prep(p);
  await p.goto(BASE+'games/summit-claws.html');await p.waitForFunction(()=>window.__SC);
  await p.evaluate(()=>document.fonts.ready);
  await p.evaluate(()=>{const S=__SC;S.look={animal:'fox',fur:S.ANIMALS.fox.fur,pattern:'auto',gear:'scarf',name:''};
   document.getElementById('nameIn').value='';S.startGame();Math.random=(()=>{let a=7;return()=>{a=(a*16807)%2147483647;return a/2147483647}})();});
  await p.evaluate(()=>{const G=__SC.G;
   // ice band = zone 3 rock ledges; stand on one with a hawk or ram nearby
   const pl=G.plats.filter(q=>q.zone===3&&q.kind==='rock'&&q.i>58)[2];
   const camp=G.plats.find(q=>q.kind==='camp'&&q.camp===3);
   Object.assign(G.p,{x:pl.x+pl.w*.45,y:pl.y,vx:0,vy:0,onGround:true,plat:pl,dir:1});
   G.camp=3;G.checkpoint=camp;G.camY=pl.y-__SC.H*.58;G.banner=null;G.score=11280;G.kills=9;G.berries=4;G.p.hp=G.p.maxHp-1;
   G.enemies=G.enemies.filter(e=>Math.abs(e.y-pl.y)>40||e.type==='hawk');});
  await p.waitForTimeout(700);
  await p.evaluate(()=>{__SC.keys.right=true});await p.waitForTimeout(160);await p.evaluate(()=>{__SC.keys.right=false});
  await p.waitForTimeout(250);
  await p.locator('#stage').screenshot({path:path.join(OUT,'sc_snow_raw.png')});await p.close()}
 await b.close();
})();
