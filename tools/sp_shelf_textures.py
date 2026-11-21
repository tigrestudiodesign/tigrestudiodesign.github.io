import asyncio
from playwright.async_api import async_playwright
JS=r'''
([id,w,h,mode])=>{const t=TAPES.find(x=>x.id===id);document.querySelectorAll('#capd').forEach(e=>e.remove());
 const d=document.createElement('div');d.id='capd';d.style.cssText=`position:fixed;left:0;top:0;z-index:99999;width:${w}px;height:${h}px;overflow:hidden`;
 if(mode==='front'){d.innerHTML=sleeve(t)}
 else if(mode==='back'){d.innerHTML=`<div style="position:absolute;inset:0;background:${t.bg};color:${t.fg};font-family:var(--sans);padding:6% 8%;box-sizing:border-box">
  <div style="font:700 ${w*0.045}px var(--mono);letter-spacing:.12em;color:${t.acc}">${t.name.toUpperCase()} · ${t.title}</div>
  <div style="font:400 ${w*0.042}px/1.45 var(--sans);margin-top:${w*0.05}px;opacity:.85">${t.body}</div>
  <div style="display:flex;gap:${w*0.02}px;margin-top:${w*0.06}px">${t.sw.map(c=>`<i style="flex:1;height:${w*0.09}px;background:${c};box-shadow:inset 0 0 0 1px rgba(255,255,255,.2)"></i>`).join('')}</div>
  <div style="font:700 ${w*0.034}px/1.6 var(--mono);margin-top:${w*0.06}px;letter-spacing:.08em;opacity:.7">${t.comps.toUpperCase()}</div>
  <div style="position:absolute;left:8%;right:8%;bottom:6%;display:flex;justify-content:space-between;align-items:end;font:700 ${w*0.03}px var(--mono);letter-spacing:.1em">
   <span>STANDARD PLAY<br>TIGRE STUDIO</span><span style="display:flex;gap:2px;height:${w*0.1}px">${Array.from({length:28},(_,i)=>`<i style="width:${(i*7%3)+1}px;background:${t.fg}"></i>`).join('')}</span></div></div>`}
 else {d.innerHTML=`<div style="position:absolute;inset:0;background:${t.bg};color:${t.fg};display:flex;align-items:center;gap:${h*0.22}px;padding:0 ${h*0.32}px;box-sizing:border-box;white-space:nowrap">
  <span style="font-family:${t.font};font-size:${h*0.44}px;font-weight:900;text-shadow:${t.shadow.replace(/cqw/g,'px')}">${t.title}</span>
  <span style="font:700 ${h*0.15}px var(--sans);letter-spacing:.1em;color:${t.acc}">${t.name.toUpperCase()}</span>
  <span style="font:700 ${h*0.15}px 'Noto Sans JP';letter-spacing:.12em">${t.jp}</span>
  <span style="margin-left:auto;font:700 ${h*0.12}px var(--mono);letter-spacing:.06em;border:2px solid ${t.fg};padding:${h*0.06}px ${h*0.1}px">${t.spine}</span></div>`}
 document.body.appendChild(d);return d.getBoundingClientRect().width}
'''
FF="""(()=>{const st=document.createElement('style');st.textContent=`
@font-face{font-family:Unbounded;src:url(/Unbounded[wght].ttf);font-weight:100 900}
@font-face{font-family:VT323;src:url(/VT323-Regular.ttf)}
@font-face{font-family:Syncopate;src:url(/Syncopate-Bold.ttf);font-weight:700}
@font-face{font-family:'Press Start 2P';src:url(/PressStart2P-Regular.ttf)}
@font-face{font-family:Orbitron;src:url(/Orbitron[wght].ttf);font-weight:400 900}
@font-face{font-family:'Noto Sans JP';src:url(/NotoSansJP[wght].ttf);font-weight:100 900}`;document.head.appendChild(st);
return Promise.all(['900 40px Unbounded','40px VT323','700 40px Syncopate',"40px 'Press Start 2P'",'900 40px Orbitron',"700 40px 'Noto Sans JP'"].map(f=>document.fonts.load(f,'T-120高品質デザイン')))})()"""
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page(viewport={'width':1600,'height':1400},device_scale_factor=2)
    await pg.goto('http://localhost:8765/#standard-play');await pg.wait_for_timeout(2500)
    await pg.evaluate(FF);await pg.wait_for_timeout(500)
    for t in ['t120','t60','t90','t160','c46']:
      for mode,w,h in ([('front',520,940),('back',520,940),('spine',940,125)] if t!='c46' else [('front',320,505),('spine',505,85)]):
        await pg.evaluate(JS,[t,w,h,mode]);await pg.wait_for_timeout(700);await pg.evaluate('document.fonts.ready')
        await pg.screenshot(path=f'/home/claude/cmf/shelf/{t}_{mode}.png',clip={'x':0,'y':0,'width':w,'height':h})
        print(t,mode)
    await b.close()
asyncio.run(main())
