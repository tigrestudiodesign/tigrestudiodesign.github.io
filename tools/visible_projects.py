"""List project pages a visitor can reach from the homepage or the top menu.
Usage: serve the repo (python3 -m http.server 8791), then: python3 tools/visible_projects.py [port]
Prints one hash id per line. The daily improvement task picks only from this list."""
import sys,json
from playwright.sync_api import sync_playwright
port=sys.argv[1] if len(sys.argv)>1 else '8791'
base=f'http://localhost:{port}/'
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome');pg=b.new_page()
    pg.goto(base);pg.wait_for_timeout(1200)
    nav=pg.evaluate("()=>NAV.map(n=>n[0])")
    seen=set();pages=['']+nav
    for h in pages:
        pg.goto(base+'#'+h);pg.wait_for_timeout(500)
        for a in pg.evaluate("()=>[...document.querySelectorAll('main a[href^=\"#\"]')].map(a=>a.getAttribute('href').slice(1)).filter(Boolean)"):
            seen.add(a)
    sections=set(nav)|{'resume','contact'}
    out=sorted(x for x in seen if x not in sections)
    print('\n'.join(out))
    b.close()
