/* Tigre Studio · tiny isometric brick engine for /play/ */
(function(){
'use strict';
var COL={red:'#D7261E',yel:'#F7B500',blu:'#1E5BD8',grn:'#1F9D55',wht:'#F6F4EE',blk:'#1F2024',org:'#FF5A1F',sky:'#4FB6E8',lim:'#9BC53D',pnk:'#F27AA8',tan:'#D8B67A',gry:'#9AA0A8'};
var PAL=['red','yel','blu','grn','wht','blk','org','sky','lim','pnk','tan','gry'];
var reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;

/* ---------- colour helpers ---------- */
function hex2rgb(h){h=h.replace('#','');return[parseInt(h.substr(0,2),16),parseInt(h.substr(2,2),16),parseInt(h.substr(4,2),16)]}
function shade(h,f){var c=hex2rgb(h);return 'rgb('+c.map(function(v){return Math.max(0,Math.min(255,Math.round(f<0?v*(1+f):v+(255-v)*f)))}).join(',')+')'}

/* ---------- sound ---------- */
var AC=null,soundOn=true;
function snap(pitch){if(!soundOn)return;try{AC=AC||new (window.AudioContext||window.webkitAudioContext)();var t=AC.currentTime;
  var o=AC.createOscillator(),g=AC.createGain();o.type='square';o.frequency.setValueAtTime(1400*(pitch||1),t);o.frequency.exponentialRampToValueAtTime(380*(pitch||1),t+.05);
  g.gain.setValueAtTime(.08,t);g.gain.exponentialRampToValueAtTime(.0001,t+.07);o.connect(g).connect(AC.destination);o.start(t);o.stop(t+.08);
  var b=AC.createBuffer(1,AC.sampleRate*.03,AC.sampleRate),d=b.getChannelData(0);for(var i=0;i<d.length;i++)d[i]=(Math.random()*2-1)*Math.pow(1-i/d.length,3);
  var n=AC.createBufferSource(),ng=AC.createGain();n.buffer=b;ng.gain.value=.12;n.connect(ng).connect(AC.destination);n.start(t)}catch(e){}}
window.TS_setSound=function(v){soundOn=v};

/* ---------- isometric renderer ----------
   world: x to the right-down, y to the left-down, z up. unit = one stud. */
function Scene(canvas,opt){
  this.c=canvas;this.ctx=canvas.getContext('2d');this.o=opt||{};
  this.N=this.o.N||10;this.rot=0;this.bricks=[];this.anim=[];this.hover=null;this.ghost=null;
  this.resize();var self=this;
  if(window.ResizeObserver){new ResizeObserver(function(){self.resize();self.draw()}).observe(canvas)}else{addEventListener('resize',function(){self.resize();self.draw()})}
}
Scene.prototype.resize=function(){var r=this.c.getBoundingClientRect(),dpr=Math.min(2,window.devicePixelRatio||1);
  this.W=Math.max(10,r.width);this.H=Math.max(10,r.height);this.c.width=this.W*dpr;this.c.height=this.H*dpr;this.ctx.setTransform(dpr,0,0,dpr,0,0);
  var N=this.N,fitW=this.W/(N*1.02),fitH=this.H/(N*0.52+(this.o.headroom||6)*0.62);
  this.T=Math.max(10,Math.min(fitW,fitH,this.o.maxT||64));this.BH=this.T*0.6;
  this.ox=this.W/2;this.oy=this.H-(N*this.T*0.5)-this.T*0.35-(this.o.bottomPad||8);};
Scene.prototype.rc=function(x,y){var N=this.N;switch(this.rot&3){case 0:return[x,y];case 1:return[N-y,x];case 2:return[N-x,N-y];default:return[y,N-x]}};
Scene.prototype.P=function(x,y,z){var q=this.rc(x,y);return[this.ox+(q[0]-q[1])*this.T/2,this.oy+(q[0]+q[1])*this.T/4-z*this.BH]};
Scene.prototype.cells=function(){ // expand bricks into unit cells
  var out=[],self=this;this.bricks.forEach(function(b){var dz=b.dz||0;for(var i=0;i<b.w;i++)for(var j=0;j<b.d;j++)out.push({b:b,x:b.x+i,y:b.y+j,z:b.z+dz})});
  var key=function(c){var r=self.rc(c.x+.5,c.y+.5);return [r[0]+r[1],c.z]};
  out.forEach(function(c){c.k=key(c)});out.sort(function(a,b){return a.k[0]-b.k[0]||a.k[1]-b.k[1]});return out};
Scene.prototype.poly=function(pts,fill,stroke,lw){var g=this.ctx;g.beginPath();g.moveTo(pts[0][0],pts[0][1]);for(var i=1;i<pts.length;i++)g.lineTo(pts[i][0],pts[i][1]);g.closePath();
  if(fill){g.fillStyle=fill;g.fill();g.strokeStyle=fill;g.lineWidth=1;g.stroke()}if(stroke){g.strokeStyle=stroke;g.lineWidth=lw||1;g.stroke()}};
Scene.prototype.stud=function(cx,cy,col,alpha){var g=this.ctx,r=this.T*0.19,ry=r*0.5,h=this.BH*0.28;g.save();if(alpha!=null)g.globalAlpha=alpha;
  g.fillStyle=shade(col,-.22);g.beginPath();g.ellipse(cx,cy,r,ry,0,0,Math.PI);g.lineTo(cx-r,cy-h);g.ellipse(cx,cy-h,r,ry,0,Math.PI,0,true);g.closePath();g.fill();
  g.fillStyle=shade(col,.12);g.beginPath();g.ellipse(cx,cy-h,r,ry,0,0,Math.PI*2);g.fill();
  g.fillStyle='rgba(255,255,255,.28)';g.beginPath();g.ellipse(cx-r*.25,cy-h-ry*.15,r*.45,ry*.42,0,0,Math.PI*2);g.fill();g.restore()};
Scene.prototype.plate=function(){var N=this.N,col=this.o.plate||COL.grn,g=this.ctx,P=this.P.bind(this),th=this.BH*0.33;
  var a=P(0,0,0),b=P(N,0,0),c=P(N,N,0),d=P(0,N,0);
  // plate sides (visible two)
  var corners=[[0,0],[N,0],[N,N],[0,N]].map(function(q){return P(q[0],q[1],0)});
  var maxi=0;corners.forEach(function(p,i){if(p[1]>corners[maxi][1])maxi=i});
  var L=corners[(maxi+3)%4],M=corners[maxi],R=corners[(maxi+1)%4];
  this.poly([L,M,[M[0],M[1]+th],[L[0],L[1]+th]],shade(col,-.28));
  this.poly([M,R,[R[0],R[1]+th],[M[0],M[1]+th]],shade(col,-.15));
  this.poly([a,b,c,d],col);
  var occ=this.occ();
  for(var x=0;x<N;x++)for(var y=0;y<N;y++){if(occ[x+','+y+',0'])continue;var s=P(x+.5,y+.5,0);this.stud(s[0],s[1],col,.9)}};
Scene.prototype.occ=function(){var o={};this.bricks.forEach(function(b){if(b.dz)return;for(var i=0;i<b.w;i++)for(var j=0;j<b.d;j++)o[(b.x+i)+','+(b.y+j)+','+b.z]=b});return o};
Scene.prototype.cell=function(c,occ,alpha){
  var b=c.b,x=c.x,y=c.y,z=c.z,P=this.P.bind(this),col=COL[b.c]||b.c,g=this.ctx;g.save();if(alpha!=null)g.globalAlpha=alpha;
  var same=function(dx,dy,dz){var n=occ[(x+dx)+','+(y+dy)+','+(Math.round(z)+dz)];return n===b};
  // which world directions face the viewer after rotation
  var faces=[[1,0],[0,1],[-1,0],[0,-1]],self=this,vis=[];
  faces.forEach(function(f){var a=self.rc(x+.5,y+.5),q=self.rc(x+.5+f[0],y+.5+f[1]);var dx=q[0]-a[0],dy=q[1]-a[1];if(dx>0||dy>0)vis.push({f:f,right:dx>0})});
  vis.forEach(function(v){var f=v.f,pts;
    if(f[0]===1)pts=[P(x+1,y,z+1),P(x+1,y+1,z+1),P(x+1,y+1,z),P(x+1,y,z)];
    else if(f[0]===-1)pts=[P(x,y,z+1),P(x,y+1,z+1),P(x,y+1,z),P(x,y,z)];
    else if(f[1]===1)pts=[P(x,y+1,z+1),P(x+1,y+1,z+1),P(x+1,y+1,z),P(x,y+1,z)];
    else pts=[P(x,y,z+1),P(x+1,y,z+1),P(x+1,y,z),P(x,y,z)];
    if(!same(f[0],f[1],0))self.poly(pts,shade(col,v.right?-.16:-.32));else self.poly(pts,shade(col,v.right?-.16:-.32))});
  var top=[P(x,y,z+1),P(x+1,y,z+1),P(x+1,y+1,z+1),P(x,y+1,z+1)];this.poly(top,col);
  // outline only on brick boundary
  g.strokeStyle=shade(col,-.45);g.lineWidth=1;
  var edge=function(p,q){g.beginPath();g.moveTo(p[0],p[1]);g.lineTo(q[0],q[1]);g.stroke()};
  if(!same(0,-1,0))edge(top[0],top[1]);if(!same(1,0,0))edge(top[1],top[2]);if(!same(0,1,0))edge(top[2],top[3]);if(!same(-1,0,0))edge(top[3],top[0]);
  if(!occ[x+','+y+','+(Math.round(z)+1)]||b.dz){var s=P(x+.5,y+.5,z+1);this.stud(s[0],s[1],col)}
  g.restore()};
Scene.prototype.draw=function(){var g=this.ctx;g.clearRect(0,0,this.W,this.H);if(this.o.noPlate!==true)this.plate();var occ=this.occ(),self=this;
  this.cells().forEach(function(c){self.cell(c,occ,c.b.alpha)});
  if(this.ghost){var gh=this.ghost;var gb={x:gh.x,y:gh.y,z:gh.z,w:gh.w,d:gh.d,c:gh.c};var gocc={};for(var i=0;i<gb.w;i++)for(var j=0;j<gb.d;j++)gocc[(gb.x+i)+','+(gb.y+j)+','+gb.z]=gb;
    var cs=[];for(i=0;i<gb.w;i++)for(j=0;j<gb.d;j++)cs.push({b:gb,x:gb.x+i,y:gb.y+j,z:gb.z});
    cs.sort(function(a,b){var ra=self.rc(a.x+.5,a.y+.5),rb=self.rc(b.x+.5,b.y+.5);return(ra[0]+ra[1])-(rb[0]+rb[1])});
    cs.forEach(function(c){self.cell(c,gocc,.45)})}};
Scene.prototype.colH=function(x,y){var h=0;this.bricks.forEach(function(b){if(x>=b.x&&x<b.x+b.w&&y>=b.y&&y<b.y+b.d)h=Math.max(h,b.z+1)});return h};
Scene.prototype.pick=function(mx,my){ // returns column under the pointer (frontmost hit)
  var best=null,N=this.N;
  for(var x=0;x<N;x++)for(var y=0;y<N;y++){var h=this.colH(x,y),pts=[this.P(x,y,h),this.P(x+1,y,h),this.P(x+1,y+1,h),this.P(x,y+1,h)];
    if(inPoly(mx,my,pts)){var r=this.rc(x+.5,y+.5),k=r[0]+r[1]+h*0.01;if(!best||k>best.k)best={x:x,y:y,h:h,k:k}}}
  return best};
Scene.prototype.animate=function(){var self=this;if(this._raf)return;
  var step=function(){var live=false;self.bricks.forEach(function(b){if(b.dz){b.v=(b.v||0)+0.045;b.dz=Math.max(0,b.dz-b.v);if(b.dz>0)live=true;else{b.dz=0;b.v=0;if(b.onLand){var f=b.onLand;b.onLand=null;f()}}}});
    self.draw();if(live)self._raf=requestAnimationFrame(step);else self._raf=null};
  this._raf=requestAnimationFrame(step)};
function inPoly(x,y,p){var c=false;for(var i=0,j=p.length-1;i<p.length;j=i++){if(((p[i][1]>y)!==(p[j][1]>y))&&(x<(p[j][0]-p[i][0])*(y-p[i][1])/(p[j][1]-p[i][1])+p[i][0]))c=!c}return c}

/* ---------- confetti ---------- */
function confetti(el){if(reduce)return;var r=el.getBoundingClientRect();for(var i=0;i<36;i++){var d=document.createElement('i');d.className='cf';var c=COL[PAL[i%8]];d.style.background=c;
  d.style.left=(r.left+r.width/2)+'px';d.style.top=(r.top+r.height/3)+'px';document.body.appendChild(d);
  var a=Math.random()*Math.PI*2,v=120+Math.random()*260,dx=Math.cos(a)*v,dy=Math.sin(a)*v-220;
  d.animate([{transform:'translate(0,0) rotate(0)',opacity:1},{transform:'translate('+dx+'px,'+(dy+420)+'px) rotate('+(Math.random()*720-360)+'deg)',opacity:0}],{duration:1300+Math.random()*700,easing:'cubic-bezier(.2,.6,.4,1)'}).onfinish=(function(n){return function(){n.remove()}})(d)}}

/* ================= HERO: brick-built word ================= */
var FONT={P:['111','101','111','100','100'],L:['100','100','100','100','111'],A:['010','101','111','101','101'],Y:['101','101','010','010','010'],H:['101','101','111','101','101'],I:['111','010','010','010','111']};
function heroWord(canvas,word){
  var sc=new Scene(canvas,{N:18,headroom:8,maxT:46,plate:COL.grn,bottomPad:4});var cols=['red','yel','blu','org','grn'];
  function build(){sc.bricks=[];var x0=1,k=0;word.split('').forEach(function(ch,li){var g=FONT[ch];for(var r=0;r<5;r++)for(var c=0;c<3;c++)if(g[r][c]==='1'){
      sc.bricks.push({x:x0+c,y:8,z:4-r,w:1,d:1,c:cols[li%cols.length],dz:reduce?0:14+k*0.35+Math.random()*2});k++}
      x0+=4});
    // a little base wall of plates in front
    for(var i=0;i<16;i++)sc.bricks.push({x:1+i,y:10,z:0,w:1,d:1,c:i%2?'wht':'blk',dz:reduce?0:20+i*0.3});
    sc.animate()}
  build();
  canvas.addEventListener('click',function(){snap(.8);sc.bricks.forEach(function(b){b.dz=6+Math.random()*12;b.v=0});sc.animate()});
  return sc}

/* ================= BUILDER ================= */
function builder(root){
  var cv=root.querySelector('canvas'),sc=new Scene(cv,{N:10,headroom:7,maxT:62}),cur='red',size=[2,1],erase=false,hist=[],nid=1;
  var $=function(s){return root.querySelector(s)},msg=$('.bmsg'),cnt=$('.bcount');
  // palette
  var sw=$('.bsw');PAL.forEach(function(p){var b=document.createElement('button');b.style.setProperty('--c',COL[p]);b.title=p;b.setAttribute('aria-label','Colour '+p);b.setAttribute('aria-pressed',p===cur);
    b.onclick=function(){cur=p;erase=false;upd();[].forEach.call(sw.children,function(x){x.setAttribute('aria-pressed',x===b)})};sw.appendChild(b)});
  var sizes=root.querySelectorAll('[data-size]');[].forEach.call(sizes,function(b){b.onclick=function(){var s=b.dataset.size.split('x');size=[+s[0],+s[1]];erase=false;upd()}});
  function upd(){[].forEach.call(sizes,function(b){b.setAttribute('aria-pressed',!erase&&b.dataset.size===size[0]+'x'+size[1])});$('.berase').setAttribute('aria-pressed',erase);
    var n=sc.bricks.length;cnt.textContent=n+(n===1?' brick':' bricks')+' · '+Math.max(0,...sc.bricks.map(function(b){return b.z+1}).concat([0]))+' high'}
  $('.berase').onclick=function(){erase=!erase;upd()};
  $('.brot').onclick=function(){var t=size[0];size=[size[1],t];upd();flash('Brick turned '+size[0]+'×'+size[1])};
  $('.bview').onclick=function(){sc.rot=(sc.rot+1)&3;sc.draw();snap(.6)};
  $('.bundo').onclick=function(){var b=hist.pop();if(!b)return;var i=sc.bricks.indexOf(b);if(i>=0)sc.bricks.splice(i,1);sc.draw();upd();snap(.7)};
  $('.bclear').onclick=function(){sc.bricks=[];hist=[];sc.draw();upd();flash('Fresh baseplate.')};
  $('.bsound').onclick=function(e){soundOn=!soundOn;e.currentTarget.setAttribute('aria-pressed',soundOn);e.currentTarget.textContent=soundOn?'Sound on':'Sound off'};
  function flash(t){msg.textContent=t}
  function footprintZ(x,y,w,d){var z=0;for(var i=0;i<w;i++)for(var j=0;j<d;j++)z=Math.max(z,sc.colH(x+i,y+j));return z}
  function fit(p){var w=size[0],d=size[1];var x=Math.min(p.x,sc.N-w),y=Math.min(p.y,sc.N-d);return{x:x,y:y,w:w,d:d}}
  function local(e){var r=cv.getBoundingClientRect(),t=e.touches?e.touches[0]:e;return[t.clientX-r.left,t.clientY-r.top]}
  function hover(e){var m=local(e),p=sc.pick(m[0],m[1]);if(!p||erase){sc.ghost=null;sc.draw();cv.style.cursor=p?'crosshair':'default';return}
    var f=fit(p),z=footprintZ(f.x,f.y,f.w,f.d);if(z>=12){sc.ghost=null}else sc.ghost={x:f.x,y:f.y,z:z,w:f.w,d:f.d,c:cur};cv.style.cursor='pointer';sc.draw()}
  function place(e){var m=local(e),p=sc.pick(m[0],m[1]);if(!p)return;
    if(erase){var top=null;sc.bricks.forEach(function(b){if(p.x>=b.x&&p.x<b.x+b.w&&p.y>=b.y&&p.y<b.y+b.d&&(!top||b.z>top.z))top=b});
      if(top){sc.bricks.splice(sc.bricks.indexOf(top),1);hist=hist.filter(function(h){return h!==top});snap(.55);sc.draw();upd()}return}
    var f=fit(p),z=footprintZ(f.x,f.y,f.w,f.d);if(z>=12){flash('That tower is tall enough!');return}
    var b={id:nid++,x:f.x,y:f.y,z:z,w:f.w,d:f.d,c:cur,dz:reduce?0:2.2};b.onLand=function(){snap(1+Math.random()*.15)};sc.bricks.push(b);hist.push(b);sc.ghost=null;sc.animate();upd();
    if(sc.bricks.length===25)flash('25 bricks. You think through making too.')}
  cv.addEventListener('mousemove',hover);cv.addEventListener('mouseleave',function(){sc.ghost=null;sc.draw()});
  cv.addEventListener('click',place);
  // presets
  var PRE={
    tiger:function(){ // a little orange tiger cub with black stripes
      var B=[];var add=function(x,y,z,w,d,c){B.push({x:x,y:y,z:z,w:w,d:d,c:c})};
      add(3,4,0,1,1,'org');add(6,4,0,1,1,'org');add(3,6,0,1,1,'org');add(6,6,0,1,1,'org'); // legs
      add(3,4,1,4,3,'org');add(4,4,2,2,3,'blk');add(3,4,2,1,3,'org');add(6,4,2,1,3,'org'); // body + stripe
      add(2,4,3,3,3,'org');add(2,7,3,1,1,'wht');add(4,7,3,1,1,'wht');add(1,5,3,1,1,'blk'); // head, cheeks, nose
      add(2,4,4,1,1,'blk');add(4,4,4,1,1,'blk'); // ears
      add(7,5,2,1,1,'org');add(8,5,3,1,1,'blk');add(8,5,4,1,1,'org'); // tail
      return B},
    rocket:function(){var B=[];var add=function(x,y,z,w,d,c){B.push({x:x,y:y,z:z,w:w,d:d,c:c})};
      add(3,3,0,1,1,'red');add(6,3,0,1,1,'red');add(3,6,0,1,1,'red');add(6,6,0,1,1,'red');
      for(var z=1;z<7;z++)add(4,4,z,2,2,z===3?'blu':'wht');add(4,4,7,2,2,'red');add(4,4,8,1,1,'red');add(4,4,1,2,1,'gry');return B},
    house:function(){var B=[];var add=function(x,y,z,w,d,c){B.push({x:x,y:y,z:z,w:w,d:d,c:c})};
      for(var z=0;z<3;z++){add(2,2,z,6,1,'yel');add(2,7,z,6,1,'yel');add(2,3,z,1,4,'yel');add(7,3,z,1,4,'yel')}
      add(4,7,0,2,1,'blk');add(4,7,1,2,1,'blk');add(3,7,2,1,1,'sky');add(6,7,2,1,1,'sky');
      add(2,2,3,6,6,'red');add(3,3,4,4,4,'red');add(4,4,5,2,2,'red');add(0,8,0,2,2,'lim');add(0,8,1,2,2,'grn');return B}
  };
  [].forEach.call(root.querySelectorAll('[data-pre]'),function(btn){btn.onclick=function(){var arr=PRE[btn.dataset.pre]();sc.bricks=[];hist=[];
    arr.forEach(function(b,i){b.id=nid++;b.dz=reduce?0:6+i*0.45;b.onLand=(i%3===0)?function(){snap(1.1)}:null;sc.bricks.push(b);hist.push(b)});sc.animate();upd();flash(btn.dataset.msg||'')}});
  // share
  function enc(){return sc.bricks.map(function(b){return [b.x,b.y,b.z,b.w,b.d,PAL.indexOf(b.c)].map(function(v){return v.toString(36)}).join('')}).join('.')}
  $('.bshare').onclick=function(){var u=location.origin+location.pathname+'#build='+enc();try{history.replaceState(null,'','#build='+enc())}catch(e){}
    if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(u).then(function(){flash('Link copied. Send it to ortegatohenry@gmail.com')},function(){flash(u)});else flash(u)};
  var m=location.hash.match(/#build=([0-9a-z.]+)/);if(m){m[1].split('.').forEach(function(s){if(s.length<6)return;var v=s.split('').map(function(ch){return parseInt(ch,36)});sc.bricks.push({id:nid++,x:v[0],y:v[1],z:v[2],w:v[3],d:v[4],c:PAL[v[5]]||'red'})});flash('Someone built this for you.')}
  else{PRE.tiger().forEach(function(b){b.id=nid++;sc.bricks.push(b)});flash('A tiger cub, built from '+sc.bricks.length+' bricks. Your turn.')}
  sc.draw();upd();
  return sc}

/* ================= INSTRUCTION BOOKLET ================= */
function booklet(root){
  var cv=root.querySelector('canvas'),sc=new Scene(cv,{N:8,headroom:15,maxT:54,plate:COL.wht}),i=0;
  var STEPS=[
    {t:'2010 · The base',d:'Nike iD, then Nike Air. Colour and material specs, then inventing making processes from lab to line. Milestone Award, 2014.',b:[[1,2,0,4,2,'red'],[1,4,0,4,2,'red']],p:'2× red 4×2 · Nike iD + Nike Air'},
    {t:'2014 · Go to the factory',d:'Taichung, Taiwan. Three years inside the factories, scaling four new platforms with contract manufacturers.',b:[[2,3,1,2,2,'yel'],[1,2,1,1,2,'yel'],[4,4,1,1,2,'yel']],p:'1× yellow 2×2 · 2× yellow 1×2 · Taiwan'},
    {t:'2017 · Build the system',d:'Nike NXT. A documentation system from scratch, and the team across the US, South Korea and Taiwan that ran it.',b:[[1,2,2,4,1,'grn'],[1,5,2,4,1,'grn']],p:'2× green 4×1 · Nike NXT'},
    {t:'2019 · Concept to launch',d:'Product Innovation Manager. Prototyping sprints, hands-on workshops, powered products with Hyperice.',b:[[1,3,2,4,2,'blu'],[2,3,3,2,2,'blu']],p:'1× blue 4×2 · 1× blue 2×2 · Innovation'},
    {t:'2024 · Future product',d:'High-risk platforms, 3D-printed and sensory footwear, and the visual manuals factories build from.',b:[[2,3,4,2,2,'blk'],[2,3,5,1,1,'blk'],[3,4,5,1,1,'blk']],p:'1× black 2×2 · 2× black 1×1 · Future'},
    {t:'2026 · Tigre Studio',d:'Six games, three prototypes, a guide that teaches code with bricks, and a page built for you.',b:[[2,3,6,2,2,'org'],[2,3,7,1,1,'yel'],[3,4,7,1,1,'sky']],p:'1× orange 2×2 · 2× 1×1 · Now'},
    {t:'Next · The Play Lab',d:'This brick is yours to place. Let\'s build the next way to play, together.',b:[[2,3,8,2,2,'red']],p:'1× red 2×2 · ?'}
  ];
  var num=root.querySelector('.bk-n'),tt=root.querySelector('.bk-t'),dd=root.querySelector('.bk-d'),parts=root.querySelector('.bk-parts'),prog=root.querySelector('.bk-prog');
  STEPS.forEach(function(_,k){var s=document.createElement('i');prog.appendChild(s)});
  function show(n,animate){i=Math.max(0,Math.min(STEPS.length-1,n));sc.bricks=[];
    for(var k=0;k<=i;k++)STEPS[k].b.forEach(function(a,j){sc.bricks.push({x:a[0],y:a[1],z:a[2],w:a[3],d:a[4],c:a[5],dz:(animate&&k===i&&!reduce)?5+j*1.2:0,onLand:(animate&&k===i&&j===0)?function(){snap(1.05)}:null,alpha:(k<i)?1:1})});
    var s=STEPS[i];num.textContent=i+1;tt.textContent=s.t;dd.textContent=s.d;
    parts.innerHTML='';s.b.forEach(function(a){var e=document.createElement('span');e.className='pt';e.innerHTML='<b style="--c:'+COL[a[5]]+';--w:'+a[3]+';--d:'+a[4]+'"></b>'+a[3]+'×'+a[4];parts.appendChild(e)});
    var lab=document.createElement('em');lab.textContent=s.p;parts.appendChild(lab);
    [].forEach.call(prog.children,function(e,k){e.className=k<=i?'on':''});
    root.querySelector('.bk-prev').disabled=i===0;var nx=root.querySelector('.bk-next');nx.textContent=i===STEPS.length-1?'Build again ↺':'Next step →';
    if(animate)sc.animate();else sc.draw();
    if(animate&&i===STEPS.length-1)setTimeout(function(){confetti(cv)},700)}
  root.querySelector('.bk-next').onclick=function(){if(i===STEPS.length-1)show(0,true);else show(i+1,true)};
  root.querySelector('.bk-prev').onclick=function(){show(i-1,false)};
  show(0,false);return sc}

/* ================= boot ================= */
function boot(){
  var h=document.getElementById('heroCv');if(h)heroWord(h,'PLAY');
  var b=document.getElementById('builder');if(b)builder(b);
  var k=document.getElementById('booklet');if(k)booklet(k);
  // bricks that snap on scroll-in
  if('IntersectionObserver' in window&&!reduce){var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}})},{threshold:.2});
    [].forEach.call(document.querySelectorAll('.snapin'),function(el){io.observe(el)})}else{[].forEach.call(document.querySelectorAll('.snapin'),function(el){el.classList.add('in')})}
  // stud counter in the top bar = scroll progress
  var bar=document.getElementById('studbar');if(bar){var n=24;for(var i=0;i<n;i++)bar.appendChild(document.createElement('i'));
    var on=function(){var p=scrollY/(document.documentElement.scrollHeight-innerHeight||1);var k=Math.round(p*n);[].forEach.call(bar.children,function(s,j){s.className=j<k?'on':''})};addEventListener('scroll',on,{passive:true});on()}
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();
