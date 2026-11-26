/* Tigre Studio case pages: lightbox, before/after compare, scroll reveal */
(function(){
  var shots=[].slice.call(document.querySelectorAll('.shot'));
  var lb=document.getElementById('lb'),im=document.getElementById('lbImg'),cap=document.getElementById('lbCap'),ct=document.getElementById('lbCt');
  var i=0,last=null;
  function show(){var s=shots[i],src=s.querySelector('img');im.src=s.dataset.full||src.src;im.alt=src.alt;cap.textContent=src.alt;ct.textContent=(i+1)+' / '+shots.length}
  function open(k){i=k;last=document.activeElement;show();lb.classList.add('open');document.getElementById('lbX').focus()}
  function close(){lb.classList.remove('open');if(last)last.focus()}
  shots.forEach(function(s,k){s.addEventListener('click',function(){open(k)})});
  document.getElementById('lbX').onclick=close;
  document.getElementById('lbP').onclick=function(){i=(i-1+shots.length)%shots.length;show()};
  document.getElementById('lbN').onclick=function(){i=(i+1)%shots.length;show()};
  lb.addEventListener('click',function(e){if(e.target===lb)close()});
  document.addEventListener('keydown',function(e){if(!lb.classList.contains('open'))return;if(e.key==='Escape')close();if(e.key==='ArrowLeft')document.getElementById('lbP').click();if(e.key==='ArrowRight')document.getElementById('lbN').click()});
  var x0=null;lb.addEventListener('touchstart',function(e){x0=e.touches[0].clientX},{passive:true});
  lb.addEventListener('touchend',function(e){if(x0===null)return;var dx=e.changedTouches[0].clientX-x0;if(Math.abs(dx)>45)(dx<0?document.getElementById('lbN'):document.getElementById('lbP')).click();x0=null});
  document.querySelectorAll('.cmp input').forEach(function(r){r.addEventListener('input',function(){r.parentElement.style.setProperty('--x',r.value+'%')})});
  if(!matchMedia('(prefers-reduced-motion: reduce)').matches&&'IntersectionObserver' in window){
    var els=document.querySelectorAll('.obj');els.forEach(function(e){e.classList.add('rv')});
    var io=new IntersectionObserver(function(es){es.forEach(function(en){if(en.isIntersecting){en.target.classList.add('in');io.unobserve(en.target)}})},{rootMargin:'0px 0px -8% 0px'});
    els.forEach(function(e){io.observe(e)});
  }
})();
