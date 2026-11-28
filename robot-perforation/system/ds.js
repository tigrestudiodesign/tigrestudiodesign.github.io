(function(){
'use strict';
var T=window.TOKENS, IC=window.ICONS, $=function(s,r){return (r||document).querySelector(s)}, $$=function(s,r){return [].slice.call((r||document).querySelectorAll(s))};
var RM=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
var P=T.primitive, H=function(ref){var a=ref.split('.');return a.length>1?P[a[0]][a[1]]:P[a[0]]};

// sprite
var sp='<svg xmlns="http://www.w3.org/2000/svg" style="display:none">';
Object.keys(IC).forEach(function(k){sp+='<symbol id="i-'+k+'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square" stroke-linejoin="miter">'+IC[k]+'</symbol>'});
$('#sprite').innerHTML=sp+'</svg>';
function ico(k,cls){return '<svg class="i '+(cls||'')+'" aria-hidden="true"><use href="#i-'+k+'"/></svg>'}

// toast + copy
var toastT; function toast(msg){var t=$('#toast');t.querySelector('span').textContent=msg;t.classList.add('on');clearTimeout(toastT);toastT=setTimeout(function(){t.classList.remove('on')},1600)}
function copy(txt,msg){(navigator.clipboard?navigator.clipboard.writeText(txt):Promise.reject()).then(function(){toast(msg)},function(){toast('Copy: '+txt.slice(0,40))})}

// contrast
function lum(h){h=h.replace('#','');var c=[0,2,4].map(function(i){var x=parseInt(h.substr(i,2),16)/255;return x<=.03928?x/12.92:Math.pow((x+.055)/1.055,2.4)});return .2126*c[0]+.7152*c[1]+.0722*c[2]}
function cr(a,b){var x=lum(a),y=lum(b);if(x<y){var t=x;x=y;y=t}return (x+.05)/(y+.05)}
function grade(r,kind){if(kind==='graphic')return r>=3?['aa','GRAPHIC ✓']:['no','GRAPHIC ✕'];return r>=7?['aaa','AAA']:r>=4.5?['aa','AA']:r>=3?['lg','LARGE ONLY']:['no','FAILS']}

// hero
(function(){var c=$('#heroMark');if(!c||!window.UnitMark)return;if(window.UnitBoot){var b=UnitBoot.attach(c,{unit:1024,size:1000,top:20,bg:'none',field:'rgba(228,232,234,.55)',hot:'#2fa39e',live:'#2fa39e',text:false,duration:2600});b.start();c.style.cursor='pointer';c.addEventListener('click',b.start);c.removeAttribute('aria-hidden');c.setAttribute('role','img');c.setAttribute('aria-label','Unit 1024 mark, drawn hole by hole')}else UnitMark.draw(c.getContext('2d'),20,20,1000,1024,{field:'rgba(228,232,234,.55)',hot:'#2fa39e'})})();
(function(){var n=0;['primitive'].forEach(function(){Object.keys(P).forEach(function(k){n+=typeof P[k]==='string'?1:Object.keys(P[k]).length})});
 var s=0;Object.keys(T.semantic).forEach(function(g){s+=Object.keys(T.semantic[g]).length});
 var o=Object.keys(T.space).length+Object.keys(T.radius).length+Object.keys(T.type).length+Object.keys(T.motion.duration).length+Object.keys(T.motion.easing).length+Object.keys(T.shadow).length;
 $('#stats').innerHTML=[['Tokens',n+s+o],['Icons',Object.keys(IC).length],['Components',10],['Contrast checks','live']].map(function(a){return '<div>'+a[0]+'<b>'+a[1]+'</b></div>'}).join('')})();

// ramps
(function(){var el=$('#ramps'),h='';
 [['Teal','teal'],['Ink','ink'],['Safety','safety']].forEach(function(r){var g=P[r[1]];h+='<div class="lbl" style="margin:0 0 8px">'+r[0]+'</div><div class="ramp">';
  Object.keys(g).forEach(function(k){var hex=g[k],dark=lum(hex)<.3;h+='<button class="sw" style="background:'+hex+'" data-hex="'+hex+'" aria-label="Copy '+r[1]+'-'+k+' '+hex+'"><span>'+r[1]+'-'+k+'<small>'+hex.toUpperCase()+'</small></span></button>'});h+='</div>'});
 el.innerHTML=h;$$('.sw',el).forEach(function(b){b.addEventListener('click',function(){copy(b.dataset.hex,'Copied '+b.dataset.hex)})})})();

// roles
(function(){var S=T.semantic,bgD=H('ink.50'),ink=H('ink.800'),white=H('white'),deep=H('ink.900');
 var on={'bg.default':[ink,'text','fg-default'],'bg.raised':[ink,'text','fg-default'],'bg.sunken':[ink,'text','fg-default'],'bg.inverse':[white,'text','fg-inverse'],'bg.deep':[white,'text','fg-inverse'],'bg.brand':[deep,'text','fg-on-brand'],
  'fg.default':[bgD,'text','bg-default'],'fg.muted':[bgD,'text','bg-default'],'fg.subtle':[H('ink.800'),'text','bg-inverse'],'fg.inverse':[H('ink.800'),'text','bg-inverse'],'fg.brand':[bgD,'text','bg-default'],'fg.on-brand':[H('teal.500'),'text','bg-brand'],
  'border.default':[bgD,'decor','bg-default'],'border.strong':[bgD,'graphic','bg-default'],'border.brand':[deep,'graphic','bg-deep'],'border.focus':[bgD,'graphic','bg-default'],
  'status.working':[deep,'graphic','console'],'status.working-text':[bgD,'text','bg-default'],'status.caution':[ink,'text','ink text'],'status.caution-text':[bgD,'text','bg-default'],'status.stop':[deep,'graphic','console'],'status.stop-text':[bgD,'text','bg-default'],'status.info':[deep,'graphic','console'],'status.info-text':[bgD,'text','bg-default'],'status.offline':[ink,'graphic','bg-inverse'],
  'data.1':[bgD,'graphic','bg-default'],'data.2':[bgD,'graphic','bg-default'],'data.3':[bgD,'graphic','bg-default'],'data.4':[bgD,'graphic','bg-default'],'data.5':[deep,'graphic','bg-deep']};
 var tb=$('#roles tbody'),h='';
 Object.keys(S).forEach(function(g){Object.keys(S[g]).forEach(function(k){var r=S[g][k],key=g+'.'+k,o=on[key]||[bgD,'graphic','bg-default'],ratio=cr(r.hex,o[0]),gr=o[1]==='decor'?['lg','DECOR ONLY']:grade(ratio,o[1]);
  h+='<tr><td><span class="chip-c" style="background:'+r.hex+'"></span><b>'+key+'</b></td><td><code>--'+g+'-'+k+'</code></td><td><code>'+r.ref.replace('.','-')+' '+r.hex+'</code></td><td><code>'+o[2]+'</code></td><td><span class="wc '+gr[0]+'">'+ratio.toFixed(2)+' · '+gr[1]+'</span></td></tr>'})});
 tb.innerHTML=h})();

// type
(function(){var el=$('#typescale'),h='',sample={'display-1':'Unit 1024','display-2':'Takes the dull shift','heading-1':'Built for the floor','heading-2':'It moves the heavy totes, all shift.','body':'Plain, direct, honest. Say what it does, give the number, say what happens next.','mono-1':'Zone B-04 · status: working','mono-2':'Line 3 → dock 2 · 14:02'};
 Object.keys(T.type).forEach(function(k){var t=T.type[k],fam=t.family==='mono'?'var(--font-mono)':'var(--font-display)';
  var sz=Math.min(t.size,96);h+='<div class="ts"><div class="lbl">'+k+'</div><div class="s" style="font:'+t.weight+' '+sz+'px/'+t.line+' '+fam+';font-size:min('+sz+'px,max(14px,'+(sz*0.14).toFixed(2)+'vw));letter-spacing:'+t.track+'em;text-transform:'+(t.case==='upper'?'uppercase':'none')+'">'+sample[k]+'</div><div class="meta lbl" style="text-align:right">'+(t.family==='mono'?'JetBrains Mono':'Inter Display')+' '+t.weight+' · '+t.size+'/'+Math.round(t.size*t.line)+(t.size>96?' · shown at 96':'')+'</div></div>'});
 el.innerHTML=h})();

// space, radius, grid
(function(){var h='';Object.keys(T.space).forEach(function(k){var v=T.space[k];h+='<div class="sp"><span>space-'+k+'</span><span>'+v+' px</span><i style="width:'+Math.max(2,v*2)+'px"></i></div>'});$('#spacescale').innerHTML=h;
 var r='';Object.keys(T.radius).forEach(function(k){var v=T.radius[k];r+='<div style="border-radius:'+(typeof v==='string'?v:Math.min(v,55)+'px')+'">radius-'+k+'<br>'+(typeof v==='string'?v:v+' px')+'</div>'});$('#radius').innerHTML=r;
 $('#gridToggle').addEventListener('change',function(e){$('#gridov').classList.toggle('on',e.target.checked)})})();

// mark demo
(function(){var el=$('#markdemo');if(!window.UnitMark)return;
 [[1024,'#f4f5f5','#132630','#2fa39e','Paper'],[1031,'#132630','#e4e8ea','#2fa39e','Ink'],[1056,'#0b1317','#cfd6da','#39d353','Chest screen · working']].forEach(function(a){
  var d=document.createElement('div');d.className='card';d.style.background=a[1];d.style.textAlign='center';var c=document.createElement('canvas');c.width=c.height=480;c.style.width='70%';c.style.height='auto';
  UnitMark.draw(c.getContext('2d'),0,0,480,a[0],{field:a[2],hot:a[3]});d.appendChild(c);var l=document.createElement('div');l.className='lbl';l.style.marginTop='12px';l.style.color=a[1]==='#f4f5f5'?'':'#9fb0b8';l.textContent='Unit '+a[0]+' · '+a[4];d.appendChild(l);el.appendChild(d)})})();

// icons
(function(){var g=$('#iconGrid'),keys=Object.keys(IC),h='';keys.forEach(function(k){h+='<button class="ic" data-k="'+k+'" aria-label="Copy '+k+' icon SVG"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square" stroke-linejoin="miter" aria-hidden="true">'+IC[k]+'</svg>'+k+'</button>'});g.innerHTML=h;
 $$('.ic',g).forEach(function(b){b.addEventListener('click',function(){var k=b.dataset.k;copy('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square" stroke-linejoin="miter">'+IC[k]+'</svg>','Copied '+k+'.svg');setBig(k);b.classList.add('copied');setTimeout(function(){b.classList.remove('copied')},600)});b.addEventListener('mouseenter',function(){setBig(b.dataset.k)})});
 function setBig(k){$('#bigIcon').innerHTML='<rect x="2" y="2" width="20" height="20" stroke="#2fa39e" stroke-width=".25" stroke-dasharray=".6 .6"/>'+IC[k]}
 setBig('unit');
 $('#sizes').innerHTML=[16,24,32,48].map(function(s){return '<span style="display:inline-flex;flex-direction:column;align-items:center;gap:6px"><svg style="width:'+s+'px;height:'+s+'px"><use href="#i-unit"/></svg><span class="lbl">'+s+'</span></span>'}).join('')})();

// badges, meters
function badge(el,u,zone,dark){if(!el)return;var c=document.createElement('canvas');c.width=c.height=112;c.style.width=c.style.height='56px';UnitMark.draw(c.getContext('2d'),0,0,112,u,{field:dark?'#cfd6da':'#132630',hot:'#2fa39e'});el.innerHTML='';el.appendChild(c);var t=document.createElement('div');t.innerHTML='<b>UNIT '+u+'</b><span>'+zone+'</span>';el.appendChild(t)}
badge($('#badge1'),1024,'ZONE B-04 · FLOOR 2',1);badge($('#badge2'),1047,'ZONE C-11 · FLOOR 2',0);
(function(){var b3=$('#badge3');if(b3){b3.className='badge light';b3.style.border='0';b3.style.padding='0';badge(b3,1024,'ZONE B-04',0)}})();
function meter(el,p){var n=Math.round(p/10),h='';for(var i=0;i<10;i++)h+='<i class="'+(i<n?'on':'')+'"></i>';el.innerHTML=h+'<b>'+p+'%</b>';el.classList.toggle('low',p<=20);el.setAttribute('aria-label','Battery '+p+' percent')}
meter($('#m1'),72);meter($('#m2'),18);

// field + seg
(function(){var inp=$('#unitIn'),help=$('#unitHelp'),known={1001:'A-01',1024:'B-04',1025:'B-04',1031:'B-07',1033:'C-02',1040:'C-05',1047:'C-11',1056:'D-01',1064:'D-03'};
 inp.addEventListener('input',function(){var v=inp.value.replace(/\D/g,'');if(known[v]){inp.setAttribute('aria-invalid','false');help.className='help';help.innerHTML=ico('check')+'Unit '+v+' · Zone '+known[v]}else{inp.setAttribute('aria-invalid','true');help.className='help err';help.innerHTML=ico('caution')+(v?'No unit '+v+' on this floor. Check the number on its base plate.':'Type the number from the base plate.')}
  $$('#unitHelp svg').forEach(function(s){s.style.width=s.style.height='14px'})});
 $$('#seg button').forEach(function(b){b.addEventListener('click',function(){$$('#seg button').forEach(function(o){o.setAttribute('aria-pressed',o===b)})})})})();

// templates
(function(){var L=[['rp__r_booth_wall','Booth wall','r01'],['rp__r_sign','Facility sign','r02'],['rp__r_explainer','Explainer','r03'],['rp__r_slide1','Slide','r04'],['rp__r_social1','Social','r05'],['rp__r_library','Asset library','r06'],['rp__r_web_desktop','Web','r08'],['rp__r_wayfinding','Wayfinding','r02b']];
 $('#tpl').innerHTML=L.map(function(a){return '<a href="../#'+a[2]+'"><img src="../img/'+a[0]+'.webp" alt="'+a[1]+' template" loading="lazy"><span>'+a[1]+' ↗</span></a>'}).join('')})();

// motion
(function(){var M=T.motion,el=$('#motionDemos');
 function curve(b){var p='M0,80';for(var i=1;i<=40;i++){var t=i/40,x=3*(1-t)*(1-t)*t*b[0]+3*(1-t)*t*t*b[2]+t*t*t,y=3*(1-t)*(1-t)*t*b[1]+3*(1-t)*t*t*b[3]+t*t*t;p+=' L'+(x*200).toFixed(1)+','+(80-y*70).toFixed(1)}return '<svg class="curve" viewBox="-4 0 208 90"><path d="M0,80H200M0,10H200" stroke="#cfd6da" stroke-width="1"/><path d="'+p+'" fill="none" stroke="#1f807c" stroke-width="2.5"/></svg>'}
 var D=[['Status change','standard','base','status'],['Chevron wipe','enter','slow','wipe'],['Reticle lock','standard','fast','lock']];
 el.innerHTML=D.map(function(d,i){return '<div class="mo"><div class="lbl">'+d[0]+'</div><div style="font:900 22px/1 var(--font-display);margin-top:6px">'+M.duration[d[2]]+' MS · '+d[1].toUpperCase()+'</div>'+curve(M.easing[d[1]])+'<div class="stage" id="st'+i+'"></div><button class="btn btn-secondary btn-sm" data-i="'+i+'">'+ico('go')+'Play</button></div>'}).join('');
 var s0=$('#st0');s0.innerHTML='<span class="pill working" style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%)"><span class="dot"></span><span>Working</span></span>';
 var s1=$('#st1');s1.innerHTML='<svg viewBox="0 0 32 32" style="position:absolute;left:50%;top:50%;width:90px;height:90px;transform:translate(-50%,-50%)"><g id="wipeG" fill="#2fa39e"></g></svg>';
 (function(){var g=$('#wipeG'),ds=UnitMark.dots(1024).filter(function(d){return d.hot});g.innerHTML=ds.map(function(d){return '<circle cx="'+(d.i+.5)+'" cy="'+(d.j+.5)+'" r=".43" data-x="'+d.i+'"/>'}).join('')})();
 var s2=$('#st2');s2.innerHTML='<div id="ret" style="position:absolute;left:50%;top:50%;width:120px;height:80px;transform:translate(-50%,-50%);border:2px solid transparent"></div><div style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);font:700 11px var(--font-mono);letter-spacing:.1em;color:#132630">TOTE T-L22</div>';
 function bez(b){return 'cubic-bezier('+b.join(',')+')'}
 function play(i){var d=RM?0:M.duration[D[i][2]],e=bez(M.easing[D[i][1]]);
  if(i===0){var p=s0.querySelector('.pill'),w=p.classList.contains('working');p.animate([{transform:'translate(-50%,-50%) scale(1)'},{transform:'translate(-50%,-50%) scale(.94)'},{transform:'translate(-50%,-50%) scale(1)'}],{duration:d,easing:e});
   p.className='pill '+(w?'caution':'working');p.innerHTML=w?ico('slow')+'<span>Slow · person near</span>':'<span class="dot"></span><span>Working</span>'}
  if(i===1){$$('#wipeG circle').forEach(function(c){var x=+c.dataset.x;c.animate([{opacity:0,transform:'translateX(-3px)'},{opacity:1,transform:'none'}],{duration:d,delay:RM?0:(x-9)*28,easing:e,fill:'both'})})}
  if(i===2){var r=$('#ret');r.style.borderImage='none';r.animate([{width:'240px',height:'110px',borderColor:'rgba(31,128,124,0)'},{width:'120px',height:'80px',borderColor:'#1f807c'}],{duration:d*2,easing:e,fill:'forwards'})}}
 $$('#motionDemos button').forEach(function(b){b.addEventListener('click',function(){play(+b.dataset.i)})})})();

// a11y matrix
(function(){var fg=[['ink-800',H('ink.800')],['ink-500',H('ink.500')],['teal-800',H('teal.800')],['teal-500',H('teal.500')],['white',H('white')],['ink-900',H('ink.900')]],
 bg=[['ink-50',H('ink.50')],['white',H('white')],['ink-100',H('ink.100')],['ink-800',H('ink.800')],['teal-500',H('teal.500')],['yellow',H('safety.yellow')],['red-700',H('safety.red-700')]];
 var h='<thead><tr><th>Text ↓ / Ground →</th>'+bg.map(function(b){return '<th>'+b[0]+'</th>'}).join('')+'</tr></thead><tbody>';
 fg.forEach(function(f){h+='<tr><th>'+f[0]+'</th>';bg.forEach(function(b){var r=cr(f[1],b[1]),g=grade(r,'text');h+='<td aria-label="'+f[0]+' on '+b[0]+': '+r.toFixed(1)+' to 1, '+g[1]+'"><div aria-hidden="true" style="background:'+b[1]+';color:'+f[1]+';border:1px solid rgba(19,38,48,.1)">'+r.toFixed(1)+'<small class="wc '+g[0]+'">'+g[1]+'</small></div></td>'});h+='</tr>'});
 $('#mx').innerHTML=h+'</tbody>'})();

// checklist
(function(){var items=['Uses role tokens only, no raw hex values','One teal accent moment per layout','Red, yellow and green only mean stop, caution and running','Every status has an icon and a word, not just a colour','Robot on pale steel, never cropped at the head','Every number is measured, or marked as a placeholder','Headlines uppercase, body in sentence case','Text passes 4.5:1 (3:1 for large text)','Mark has 4 cells of clear space and is above minimum size','The first line says what it does'];
 var ul=$('#check');ul.innerHTML=items.map(function(t,i){return '<li><label><input type="checkbox" data-i="'+i+'">'+t+'</label></li>'}).join('');
 function upd(){var n=$$('#check input:checked').length;$('#score').textContent=n+' / 10';$('#scoreNote').textContent=n===10?'Ship it.':n>=7?'Close. Fix the gaps before it goes to a vendor.':'Not yet. Go back to the principles.';$('#score').style.color=n===10?'var(--status-working-text)':''}
 ul.addEventListener('change',upd);upd()})();

// scrollspy
(function(){var links=$$('.side a'),map={};links.forEach(function(a){map[a.getAttribute('href').slice(1)]=a});
 if(!('IntersectionObserver' in window))return;var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){links.forEach(function(l){l.classList.remove('on')});var l=map[e.target.id];if(l)l.classList.add('on')}})},{rootMargin:'-45% 0px -50% 0px'});
 $$('main section[id]').forEach(function(s){io.observe(s)})})();

// ===== fleet console =====
(function(){var cv=$('#floor');if(!cv)return;var x=cv.getContext('2d'),W=1120,Hh=1200;
 var AX=[150,350,550,750,950],TOP=120,BOT=1070;
 var C={teal:'#2fa39e',teal3:'#6cc2be',yel:'#f2c230',red:'#e23b2e',grn:'#39d353',ink3:'#9fb0b8',line:'#22363f'};
 var IDS=[1024,1025,1031,1033,1040,1047,1056,1064];
 function loop(a,b){return [[AX[a],TOP],[AX[a],BOT],[AX[b],BOT],[AX[b],TOP]]}
 var units=IDS.map(function(id,i){var a=i%4,b=a+1,path=i%2?loop(b,a):loop(a,b),seg=i%4,t=(i*0.37)%1;return {id:id,path:path,seg:seg,t:t,spd:70+((i*17)%30),bat:40+((i*23)%60),st:'working',prev:'working',totes:0,task:i%2?'Totes · line '+(i%3+1)+' → dock '+(i%2+1):'Empty totes · dock → line '+(i%3+1),x:0,y:0,dx:0,dy:1,chg:0}});
 var people=[],sel=1024,stopped=false,clock=0,totes=0,logEl=$('#log'),lines=[];
 function log(html){var m=Math.floor(clock),hh=String(14+Math.floor(m/60)).padStart(2,'0'),mm=String(m%60).padStart(2,'0');lines.unshift('<div><b>'+hh+':'+mm+'</b> '+html+'</div>');lines=lines.slice(0,7);logEl.innerHTML=lines.join('')}
 // rows
 var ul=$('#ulist');units.forEach(function(u){var b=document.createElement('button');b.className='urow';b.type='button';var c=document.createElement('canvas');c.width=c.height=80;c.style.width=c.style.height='40px';UnitMark.draw(c.getContext('2d'),0,0,80,u.id,{field:'#cfd6da',hot:'#2fa39e'});b.appendChild(c);
  var mid=document.createElement('div');mid.innerHTML='<div class="nm">UNIT '+u.id+'</div><div class="tk"></div>';b.appendChild(mid);var r=document.createElement('div');r.style.cssText='display:flex;flex-direction:column;align-items:flex-end;gap:6px';r.innerHTML='<span class="pill"></span><span class="meter" style="transform:scale(.7);transform-origin:right"></span>';b.appendChild(r);
  b.addEventListener('click',function(){sel=u.id;$$('.urow').forEach(function(o){o.classList.toggle('sel',o===b)})});u.row=b;if(u.id===sel)b.classList.add('sel');ul.appendChild(b)});
 var PILL={working:['working','<span class="dot"></span>Working'],slow:['caution',ico('slow')+'Slow'],waiting:['caution',ico('pause')+'Waiting'],stopped:['stop',ico('stop')+'Stopped'],charging:['info',ico('charge')+'Charging']};
 function rowUpd(u){var p=u.row.querySelector('.pill'),d=PILL[u.st];if(p.dataset.s!==u.st){p.className='pill '+d[0];p.innerHTML=d[1];p.dataset.s=u.st}
  u.row.querySelector('.tk').textContent=(u.st==='charging'?'Charging · dock sim':u.st==='stopped'?'Stopped · waiting for release':u.task)+' · '+Math.round(u.bat)+'%';
  var m=u.row.querySelector('.meter'),n=Math.round(u.bat/10),h='';for(var i=0;i<10;i++)h+='<i class="'+(i<n?'on':'')+'"></i>';m.innerHTML=h;m.classList.toggle('low',u.bat<=20)}
 // people
 function addPerson(px,py){var a=AX.reduce(function(best,v){return Math.abs(v-px)<Math.abs(best-px)?v:best},AX[0]);
  if(py<TOP+40||py>BOT-40){people.push({x:px,y:py<TOP+40?TOP:BOT,vx:(px<W/2?1:-1)*38,vy:0,life:14})}else people.push({x:a,y:py,vx:0,vy:(py<Hh/2?1:-1)*30,life:12});log('<span class="c">Person entered</span> near aisle '+(AX.indexOf(a)+1))}
 cv.addEventListener('click',function(e){var r=cv.getBoundingClientRect();addPerson((e.clientX-r.left)*W/r.width,(e.clientY-r.top)*Hh/r.height)});
 $('#addP').addEventListener('click',function(){addPerson(AX[1+Math.floor(Math.random()*3)],200+Math.random()*360)});
 $('#stopAll').addEventListener('click',function(){stopped=!stopped;this.querySelector('span').textContent=stopped?'Release all':'Stop all';this.className='btn btn-sm '+(stopped?'btn-dark':'btn-stop');log(stopped?'<span class="s">STOP ALL pressed.</span> Every unit stopped.':'<span class="g">Released.</span> Units back to work.')});
 function step(dt){clock+=dt*1.5;
  people.forEach(function(p){p.x+=p.vx*dt;p.y+=p.vy*dt;p.life-=dt;if(p.y<TOP||p.y>BOT){p.vy*=-1}if(p.x<60||p.x>W-60)p.vx*=-1});
  people=people.filter(function(p){if(p.life<=0){log('Person left the floor');return false}return true});
  units.forEach(function(u){var a=u.path[u.seg],b=u.path[(u.seg+1)%4],len=Math.hypot(b[0]-a[0],b[1]-a[1]);u.dx=(b[0]-a[0])/len;u.dy=(b[1]-a[1])/len;
   var near=1e9;people.forEach(function(p){near=Math.min(near,Math.hypot(p.x-u.x,p.y-u.y))});
   var st;if(stopped)st='stopped';else if(u.chg>0){st='charging';u.chg-=dt;u.bat=Math.min(100,u.bat+dt*9);if(u.chg<=0)log('<span class="g">Unit '+u.id+'</span> charged, back to work')}
   else if(u.bat<12){u.chg=9;st='charging';log('Unit '+u.id+' battery 12%, <b>charging</b>')}
   else st=near<64?'waiting':near<128?'slow':'working';
   if(st!==u.st){if(st==='waiting')log('<span class="c">Unit '+u.id+' waiting</span>, person '+(near/40).toFixed(1)+' m ahead');else if(st==='working'&&u.st==='waiting')log('Unit '+u.id+' path clear, moving');u.st=st}
   var v=st==='working'?u.spd:st==='slow'?u.spd*.35:0;u.t+=v*dt/len;u.bat=Math.max(0,u.bat-dt*(v?0.55:0.1));
   if(u.t>=1){u.t=0;u.seg=(u.seg+1)%4;if(u.seg===2){u.totes++;totes++}}
   var aa=u.path[u.seg],bb=u.path[(u.seg+1)%4];u.x=aa[0]+(bb[0]-aa[0])*u.t;u.y=aa[1]+(bb[1]-aa[1])*u.t})}
 function draw(t){x.fillStyle='#0e1d25';x.fillRect(0,0,W,Hh);
  x.strokeStyle='rgba(255,255,255,.04)';x.lineWidth=1;for(var g=0;g<W;g+=40){x.beginPath();x.moveTo(g,0);x.lineTo(g,Hh);x.stroke()}for(g=0;g<Hh;g+=40){x.beginPath();x.moveTo(0,g);x.lineTo(W,g);x.stroke()}
  // racks
  for(var i=0;i<AX.length-1;i++){var rx=AX[i]+34,rw=AX[i+1]-AX[i]-68;x.fillStyle='#132630';x.fillRect(rx,TOP+30,rw,BOT-TOP-60);x.strokeStyle='#22363f';x.strokeRect(rx+.5,TOP+30.5,rw,BOT-TOP-60);
   for(var y=TOP+50;y<BOT-40;y+=34){x.fillStyle='#1a2f39';x.fillRect(rx+8,y,rw-16,22)}
   x.fillStyle='#5c6a72';x.font='700 13px "JetBrains Mono"';x.fillText('R-'+(i+1),rx+8,TOP+22)}
  // aisles
  x.setLineDash([6,8]);x.strokeStyle='rgba(242,194,48,.28)';x.lineWidth=2;AX.forEach(function(a){x.beginPath();x.moveTo(a,TOP);x.lineTo(a,BOT);x.stroke()});x.beginPath();x.moveTo(AX[0],TOP);x.lineTo(AX[4],TOP);x.moveTo(AX[0],BOT);x.lineTo(AX[4],BOT);x.stroke();x.setLineDash([]);
  x.fillStyle='#9fb0b8';x.font='700 13px "JetBrains Mono"';x.fillText('LINES 1–3',AX[0]-20,TOP-24);x.fillText('DOCKS 1–2',AX[0]-20,BOT+44);
  // selected path
  var su=units.filter(function(u){return u.id===sel})[0];
  if(su){x.strokeStyle='rgba(47,163,158,.55)';x.lineWidth=4;x.beginPath();su.path.concat([su.path[0]]).forEach(function(p,k){k?x.lineTo(p[0],p[1]):x.moveTo(p[0],p[1])});x.stroke()}
  // people
  people.forEach(function(p){x.strokeStyle='rgba(242,194,48,.5)';x.setLineDash([4,6]);x.beginPath();x.arc(p.x,p.y,128,0,7);x.stroke();x.strokeStyle='rgba(242,194,48,.8)';x.beginPath();x.arc(p.x,p.y,64,0,7);x.stroke();x.setLineDash([]);x.fillStyle='rgba(242,194,48,.75)';x.font='700 11px "JetBrains Mono"';x.fillText('3.2 M',p.x+92,p.y-92);x.fillText('1.6 M',p.x+46,p.y-46);x.setLineDash([]);
   x.fillStyle='#f2c230';x.beginPath();x.arc(p.x,p.y,11,0,7);x.fill();x.fillStyle='#132630';x.beginPath();x.arc(p.x,p.y-3,3.5,0,7);x.fill();x.fillRect(p.x-1.5,p.y,3,7)});
  // units
  units.forEach(function(u){var col={working:C.teal,slow:C.yel,waiting:C.yel,stopped:C.red,charging:C.teal3}[u.st];
   x.save();x.translate(u.x,u.y);var ang=Math.atan2(u.dy,u.dx);
   x.fillStyle='#0b1317';x.strokeStyle=col;x.lineWidth=3;x.beginPath();x.arc(0,0,19,0,7);x.fill();x.stroke();
   x.rotate(ang);x.strokeStyle=col;x.lineWidth=4;x.lineCap='square';x.beginPath();x.moveTo(-5,-8);x.lineTo(5,0);x.lineTo(-5,8);x.stroke();x.restore();
   x.fillStyle='#fff';x.font='700 13px "JetBrains Mono"';x.fillText(String(u.id),u.x+24,u.y-6);x.fillStyle=col;x.font='700 10px "JetBrains Mono"';x.fillText(u.st.toUpperCase(),u.x+24,u.y+8);
   if(u.id===sel){var s=30+(RM?0:Math.sin(t/300)*3);x.strokeStyle='#fff';x.lineWidth=2;[[-1,-1],[1,-1],[1,1],[-1,1]].forEach(function(q){x.beginPath();x.moveTo(u.x+q[0]*s,u.y+q[1]*(s-10));x.lineTo(u.x+q[0]*s,u.y+q[1]*s);x.lineTo(u.x+q[0]*(s-10),u.y+q[1]*s);x.stroke()})}});
  // stop overlay
  if(stopped){x.fillStyle='rgba(180,35,24,.16)';x.fillRect(0,0,W,Hh);x.fillStyle='#e23b2e';x.fillRect(0,0,W,6);x.fillRect(0,Hh-6,W,6)}}
 var last=0,run=false,acc=0;
 function frame(t){if(!run)return;var dt=Math.min(.1,(t-(last||t))/1000);last=t;
  if(RM){acc+=dt;if(acc<.5){requestAnimationFrame(frame);return}dt=acc;acc=0}
  step(dt);draw(t);
  units.forEach(rowUpd);
  var w=0,c=0;units.forEach(function(u){if(u.st==='working')w++;if(u.st==='slow'||u.st==='waiting')c++});$('#k1').textContent=w;$('#k2').textContent=c;$('#k3').textContent=totes;$('#k4').textContent=people.length;
  var m=Math.floor(clock);$('#clock').textContent='SHIFT 2 · '+String(14+Math.floor(m/60)).padStart(2,'0')+':'+String(m%60).padStart(2,'0');
  requestAnimationFrame(frame)}
 step(0);draw(0);units.forEach(rowUpd);log('Shift 2 started · 8 units on floor 2');
 addPerson(AX[2],420);
 if('IntersectionObserver' in window){new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting&&!run){run=true;last=0;requestAnimationFrame(frame)}else if(!e.isIntersecting)run=false})}).observe(cv)}else{run=true;requestAnimationFrame(frame)}
})();
})();
