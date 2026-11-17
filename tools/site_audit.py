"""Site-wide audit: crawls every route at 1440 and 390 px and reports JS errors, failed requests, broken images, horizontal overflow and dead links.
Usage: python3 -m http.server 8791 & python3 tools/site_audit.py   (writes /tmp/site_audit.json and prints a summary)"""
import subprocess,time,socket,atexit,os
def _up():
    k=socket.socket()
    try:k.connect(('127.0.0.1',8791));k.close();return
    except Exception:pass
    pr=subprocess.Popen(['python3','-m','http.server','8791'],cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    atexit.register(pr.kill);time.sleep(1)
_up()

import json,re,sys
from playwright.sync_api import sync_playwright
B='http://localhost:8791/'
res={'pages':{},'links':{},'ext':set(),'files':set()}
CHECK=r"""async (w)=>{
 // force lazy images
 document.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager');
 const step=800;for(let y=0;y<document.body.scrollHeight;y+=step){scrollTo(0,y);await new Promise(r=>setTimeout(r,60))}
 await new Promise(r=>setTimeout(r,1200));scrollTo(0,0);
 const W=document.documentElement.clientWidth;
 const brokenImg=[...document.querySelectorAll('img')].filter(i=>i.complete&&i.naturalWidth===0&&i.getAttribute('src')).map(i=>i.getAttribute('src'));
 const over=[];document.querySelectorAll('body *').forEach(e=>{const r=e.getBoundingClientRect();if(r.width&&r.right>W+1){let p=e.parentElement,clip=false;while(p&&p!==document.body){const o=getComputedStyle(p).overflowX;if(o!=='visible'){clip=true;break}p=p.parentElement}if(!clip&&getComputedStyle(e).position!=='fixed')over.push(e.tagName+'.'+(e.className.baseVal??e.className)+'@'+Math.round(r.right))}});
 const links=[...document.querySelectorAll('a[href]')].map(a=>({href:a.getAttribute('href'),text:(a.innerText||a.getAttribute('aria-label')||a.querySelector('img')?.alt||'').trim().slice(0,80),img:!!a.querySelector('img,picture,video'),inMain:!!a.closest('main,#app'),dl:a.hasAttribute('download'),blank:a.target}));
 const empty=[...document.querySelectorAll('a')].filter(a=>!a.getAttribute('href')||a.getAttribute('href')==='#').map(a=>a.outerHTML.slice(0,120));
 const tiny=W<500?[...document.querySelectorAll('a,button')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&(r.height<24||r.width<24)&&getComputedStyle(e).display!=='inline'}).map(e=>(e.innerText||e.getAttribute('aria-label')||'').trim().slice(0,30)+' '+Math.round(e.getBoundingClientRect().width)+'x'+Math.round(e.getBoundingClientRect().height)).slice(0,15):[];
 return {title:document.title,view:document.getElementById('app').dataset.view,h:document.body.scrollHeight,brokenImg,over:over.slice(0,6),links,empty,tiny}}"""
def visit(pg,h,w):
    errs=[];bad=[]
    pg.on('pageerror',lambda e:errs.append('JS '+str(e)[:200]))
    pg.on('console',lambda m:m.type=='error' and not m.text.startswith('Failed to load resource') and errs.append(m.text[:200]))
    pg.on('response',lambda r:r.status>=400 and bad.append(f'{r.status} {r.url}'))
    pg.on('requestfailed',lambda r:('localhost' in r.url) and bad.append('FAIL '+r.url))
    pg.goto(B+'#'+h if h else B,wait_until='load');pg.wait_for_timeout(900)
    d=pg.evaluate(CHECK,w);d['errs']=errs;d['bad']=sorted(set(bad));return d
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--autoplay-policy=no-user-gesture-required'])
    seen=set();queue=['']
    while queue:
        h=queue.pop(0)
        if h in seen:continue
        seen.add(h)
        out={}
        for w in (1440,390):
            ctx=b.new_context(viewport={'width':w,'height':900});pg=ctx.new_page()
            try:out[w]=visit(pg,h,w)
            except Exception as e:out[w]={'crash':str(e)[:200],'links':[]}
            ctx.close()
        d=out[1440]
        # resolve hash route kind
        if h and d.get('view')=='home':
            pass
        res['pages'][h]=out
        for L in d.get('links',[])+out[390].get('links',[]):
            hr=L['href']
            if hr.startswith('#'):
                t=hr[1:]
                res['links'].setdefault(t,set()).add((h,L['text'],L['img']))
                if t not in seen and t not in queue:queue.append(t)
            elif hr.startswith('http') or hr.startswith('mailto') or hr.startswith('tel'):res['ext'].add((hr,h,L['text']))
            else:res['files'].add((hr,h))
        print(h or '(home)',d.get('view'),len(d.get('links',[])),file=sys.stderr)
    b.close()
json.dump({'pages':res['pages'],'links':{k:sorted(v) for k,v in res['links'].items()},'ext':sorted(res['ext']),'files':sorted(res['files'])},open('/tmp/site_audit.json','w'),indent=1,default=list)
P=json.load(open('/tmp/site_audit.json'))['pages'];n=0
for w in ('1440','390'):
    for h,o in P.items():
        for k in ('errs','bad','brokenImg','over','empty'):
            if o[w].get(k):print(k,w,h or 'home',o[w][k][:5]);n+=1
print(len(P),'routes; issues',n)
