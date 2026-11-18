"""Crawl every route and record which images each route shows and how big they are drawn.
usage: python3 tools/image_map.py            -> writes tools/image_map.json
{ "routes": {route: {img path: px drawn}}, "need": {img path: target pixel width} }
target width = the widest the image is ever drawn (1920 and 1440 desktop, 390 phone) x device pixel ratio,
or its full size when it can open in the page viewer or is linked as a full-size file. Never above 2560."""
import json, os, socket, subprocess, sys, time, atexit, math
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
PORT = 8793
def _up():
    k = socket.socket()
    try: k.connect(('127.0.0.1', PORT)); k.close(); return
    except Exception: pass
    pr = subprocess.Popen(['python3', '-m', 'http.server', str(PORT)], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    atexit.register(pr.kill); time.sleep(1)
_up()
B = 'http://localhost:%d/' % PORT
CAP = 2560
JS = r"""async ()=>{
 document.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager');
 for(let y=0;y<document.body.scrollHeight;y+=700){scrollTo(0,y);await new Promise(r=>setTimeout(r,50))}
 await new Promise(r=>setTimeout(r,800));
 const rel=u=>{try{const x=new URL(u,location.href);return x.origin===location.origin?x.pathname.replace(/^\//,''):null}catch(e){return null}};
 const im=[...document.querySelectorAll('img')].map(i=>({p:rel(i.getAttribute('src')||''),w:i.getBoundingClientRect().width,full:!!i.closest('.gl-pages figure')})).filter(o=>o.p&&o.p.startsWith('img/'));
 const css=[];document.querySelectorAll('*').forEach(e=>{const b=getComputedStyle(e).backgroundImage;if(b&&b.includes('url(')){const m=b.match(/url\("?([^")]+)"?\)/);if(m){const p=rel(m[1]);if(p&&p.startsWith('img/'))css.push(p)}}});
 const links=[...document.querySelectorAll('a[href]')].map(a=>a.getAttribute('href'));
 const hl=links.filter(h=>h.startsWith('#')).map(h=>h.slice(1));
 const fl=links.map(rel).filter(p=>p&&p.startsWith('img/'));
 return {im,css,hl,fl}}"""
routes = {}; need = {}; full = set(); cssimg = set()
with sync_playwright() as p:
    b = p.chromium.launch()
    seen = set(); q = ['']
    while q:
        h = q.pop(0)
        if h in seen: continue
        seen.add(h); got = {}
        for vw, dpr in ((1920, 2), (1440, 2), (390, 3)):
            ctx = b.new_context(viewport={'width': vw, 'height': 1000}); pg = ctx.new_page()
            try:
                pg.goto(B + ('#' + h if h else ''), wait_until='load'); pg.wait_for_timeout(700)
                d = pg.evaluate(JS)
            except Exception as e:
                print('crash', h, e, file=sys.stderr); ctx.close(); continue
            ctx.close()
            for o in d['im']:
                px = math.ceil(o['w'] * dpr); got[o['p']] = max(got.get(o['p'], 0), px); need[o['p']] = max(need.get(o['p'], 0), px)
                if o['full']: full.add(o['p'])
            for c in d['css']: got[c] = 0; cssimg.add(c)
            for f in d['fl']: full.add(f)
            if vw == 1440:
                for t in d['hl']:
                    if t not in seen and t not in q and not t.startswith('top') and '/' not in t: q.append(t)
        # anchors inside a page (#section ids) render the home view: keep only real routes
        routes[h] = got
        print(h or '(home)', len(got), file=sys.stderr)
    b.close()
# drop anchor 'routes' that are just the home page again
home = set(routes.get('', {}))
routes = {k: v for k, v in routes.items() if k == '' or set(v) != home}
from PIL import Image
out = {}
for f in sorted(set(need) | full | cssimg):
    if not os.path.exists(f): continue
    try: W = Image.open(f).width
    except Exception: continue
    t = W if (f in full or f in cssimg) else max(need.get(f, 0), 320)
    out[f] = min(W, t, CAP) if f not in cssimg else W
json.dump({'routes': routes, 'need': out, 'full': sorted(full), 'css': sorted(cssimg)}, open('tools/image_map.json', 'w'), indent=0)
print(len(routes), 'routes;', len(out), 'images mapped')
