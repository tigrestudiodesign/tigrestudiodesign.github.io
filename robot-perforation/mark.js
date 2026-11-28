/* UNIT MARK — 32 × 32 = 1024 holes. A perforated tile with a forward chevron punched through it.
   Every unit number seeds its own field, so each robot in a fleet gets a unique mark; the chevron never changes. */
(function(g){
var N=32;
function hash(n){ n=(n|0)^61^((n|0)>>>16); n=(n+(n<<3))|0; n^=n>>>4; n=Math.imul(n,0x27d4eb2d); n^=n>>>15; return (n>>>0)/4294967296 }
function segDist(px,py,ax,ay,bx,by){ var vx=bx-ax,vy=by-ay,wx=px-ax,wy=py-ay,t=Math.max(0,Math.min(1,(wx*vx+wy*vy)/(vx*vx+vy*vy))); return Math.hypot(px-(ax+t*vx),py-(ay+t*vy)) }
// chevron centreline in grid units (0..31)
var CH=[[9.5,5.5],[22,15.5],[9.5,25.5]];
function chevron(i,j){ return Math.min(segDist(i,j,CH[0][0],CH[0][1],CH[1][0],CH[1][1]),segDist(i,j,CH[1][0],CH[1][1],CH[2][0],CH[2][1])) }
function inTile(i,j){ // rounded-square tile: drop the corner holes
  var cx=Math.abs(i-15.5), cy=Math.abs(j-15.5), r=4.2, e=15.5-r; if(cx<=e||cy<=e) return true; return Math.hypot(cx-e,cy-e)<=r+0.15 }
// dots(unit) -> [{i,j,r,hot}] with r as a fraction of the cell
function dots(unit,opt){ opt=opt||{}; var u=Math.max(0,unit|0), a1=hash(u*7+1), a2=hash(u*13+5), a3=hash(u*31+9);
  var ax=4+a1*23, ay=4+a2*23, freq=0.55+a3*0.5, out=[];
  for(var j=0;j<N;j++) for(var i=0;i<N;i++){ if(!inTile(i,j)) continue;
    var dc=chevron(i,j), hot=dc<2.35;
    var r; if(hot){ r=0.43 } else { var d=Math.hypot(i-ax,j-ay); r=0.07+0.21*(0.5+0.5*Math.cos(d*freq)); r*=0.72+0.28*Math.min(1,dc/6) }
    out.push({i:i,j:j,r:r,hot:hot}) }
  return out }
// draw on a 2D context; size = tile edge in px
function draw(ctx,x0,y0,size,unit,o){ o=o||{}; var c=size/N, ds=dots(unit);
  if(o.simple){ ctx.fillStyle=o.bg||'#132630'; roundRect(ctx,x0,y0,size,size,size*4.2/N); ctx.fill(); ctx.strokeStyle=o.hot||'#2fa39e'; ctx.lineWidth=size*0.15; ctx.lineCap='square'; ctx.lineJoin='miter'; ctx.beginPath(); ctx.moveTo(x0+(CH[0][0]+.5)*c,y0+(CH[0][1]+.5)*c); ctx.lineTo(x0+(CH[1][0]+.5)*c,y0+(CH[1][1]+.5)*c); ctx.lineTo(x0+(CH[2][0]+.5)*c,y0+(CH[2][1]+.5)*c); ctx.stroke(); return }
  if(o.bg){ ctx.fillStyle=o.bg; var rr=size*4.2/N; roundRect(ctx,x0,y0,size,size,rr); ctx.fill() }
  ds.forEach(function(d){ ctx.fillStyle=d.hot?(o.hot||'#2fa39e'):(o.field||'#132630'); ctx.beginPath(); ctx.arc(x0+(d.i+.5)*c,y0+(d.j+.5)*c,Math.max(.35,d.r*c),0,7); ctx.fill() });
  if(o.grid){ ctx.strokeStyle=o.grid; ctx.lineWidth=1; for(var k=0;k<=N;k++){ ctx.beginPath(); ctx.moveTo(x0+k*c,y0); ctx.lineTo(x0+k*c,y0+size); ctx.moveTo(x0,y0+k*c); ctx.lineTo(x0+size,y0+k*c); ctx.stroke() } }
}
function roundRect(ctx,x,y,w,h,r){ ctx.beginPath(); ctx.moveTo(x+r,y); ctx.arcTo(x+w,y,x+w,y+h,r); ctx.arcTo(x+w,y+h,x,y+h,r); ctx.arcTo(x,y+h,x,y,r); ctx.arcTo(x,y,x+w,y,r); ctx.closePath() }
function svg(unit,o){ o=o||{}; var s=o.size||320, c=s/N, p=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '+s+' '+s+'" width="'+s+'" height="'+s+'">'];
  if(o.bg) p.push('<rect width="'+s+'" height="'+s+'" rx="'+(s*4.2/N)+'" fill="'+o.bg+'"/>');
  dots(unit).forEach(function(d){ p.push('<circle cx="'+((d.i+.5)*c).toFixed(2)+'" cy="'+((d.j+.5)*c).toFixed(2)+'" r="'+Math.max(.35,d.r*c).toFixed(2)+'" fill="'+(d.hot?(o.hot||'#2fa39e'):(o.field||'#132630'))+'"/>') });
  p.push('</svg>'); return p.join('') }
g.UnitMark={N:N,dots:dots,draw:draw,svg:svg,hash:hash};
})(window);
