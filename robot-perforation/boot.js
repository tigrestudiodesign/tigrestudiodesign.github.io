/* UnitBoot: the chest-screen boot sequence. Scans all 1,024 grid positions in order,
   counts the holes it actually draws, then lights the chevron. Needs mark.js. */
(function(g){
var RM=g.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
function boot(cv,o){
  o=o||{};var x=cv.getContext('2d'),W=cv.width,S=o.size||W,ox=(W-S)/2,oy=o.top||0,N=32,c=S/N,unit=o.unit||1024;
  var bg=o.bg||'#0b1317',field=o.field||'#cfd6da',hot=o.hot||'#2fa39e',live=o.live||'#39d353',txt=o.text!==false;
  var map={},ds=UnitMark.dots(unit);ds.forEach(function(d){map[d.j*N+d.i]=d});
  var holes=ds.length,dur=o.duration||3200,t0=0,raf=0,done=false;
  function frame(now){if(!t0)t0=now;var p=Math.min(1,(now-t0)/dur),k=Math.floor(p*N*N),glow=Math.max(0,Math.min(1,((now-t0)-dur)/500));
    if(bg==='none')x.clearRect(0,0,cv.width,cv.height);else{x.fillStyle=bg;x.fillRect(0,0,cv.width,cv.height)}
    var n=0;for(var idx=0;idx<k;idx++){var d=map[idx];if(!d)continue;n++;
      x.fillStyle=d.hot?(p<1?hot:mix(hot,live,glow)):field;x.globalAlpha=d.hot&&p<1?.55:1;
      x.beginPath();x.arc(ox+(d.i+.5)*c,oy+(d.j+.5)*c,Math.max(.4,d.r*c),0,7);x.fill()}
    x.globalAlpha=1;
    if(p<1){var si=k%N,sj=Math.floor(k/N);x.fillStyle='rgba(47,163,158,.18)';x.fillRect(ox,oy+sj*c,S,c);x.fillStyle=hot;x.fillRect(ox+si*c,oy+sj*c,c,c)}
    if(txt){var fy=oy+S+S*.075,fs=Math.round(S*.042);x.font='700 '+fs+'px "JetBrains Mono",monospace';x.textBaseline='middle';
      x.fillStyle='#9fb0b8';x.fillText('POS '+pad(k)+' / 1024',ox,fy);
      var h='HOLES '+pad(n);x.fillText(h,ox+S-x.measureText(h).width,fy);
      x.font='900 '+Math.round(S*.09)+'px "Inter Display",sans-serif';x.fillStyle='#fff';x.fillText('UNIT '+unit,ox,fy+S*.1);
      x.font='700 '+fs+'px "JetBrains Mono",monospace';x.fillStyle=p<1?'#f2c230':live;var st=(p<1?'○ BOOTING':'● WORKING');x.fillText(st,ox+S-x.measureText(st).width,fy+S*.1)}
    if(p<1||glow<1){raf=requestAnimationFrame(frame)}else{done=true;if(o.onDone)o.onDone(holes)}}
  function mix(a,b,t){var A=hex(a),B=hex(b);return 'rgb('+[0,1,2].map(function(i){return Math.round(A[i]*(1-t)+B[i]*t)}).join(',')+')'}
  function hex(h){h=h.replace('#','');return [0,2,4].map(function(i){return parseInt(h.substr(i,2),16)})}
  function pad(v){return ('000'+v).slice(-4)}
  function start(){cancelAnimationFrame(raf);t0=0;done=false;if(RM){t0=-1e9}raf=requestAnimationFrame(frame)}
  return {start:start,setUnit:function(u){unit=u;map={};ds=UnitMark.dots(u);ds.forEach(function(d){map[d.j*N+d.i]=d});holes=ds.length;start()},holes:function(){return holes}};
}
g.UnitBoot={attach:boot};
})(window);
