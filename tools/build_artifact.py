"""Build the claude.ai artifact copy of the site.
usage: python3 tools/image_map.py   (when pages or images changed)
       python3 tools/build_artifact.py OUTDIR
Writes OUTDIR/index.html (no images inside it), OUTDIR/b/*.json image bundles and OUTDIR/files.json
(the list of every file the artifact must hold, for publish_files; anything else in the artifact can be removed).

Why: an artifact holds at most 512 files and its index.html at most 16 MiB, and the viewer blocks images from
other sites. So every page gets ONE bundle with exactly the images it shows, each sized to 2x the width it is
drawn at (from tools/image_map.json). The page fetches its bundle once and shows the images from memory.
Adding projects only adds bundles; the index stays small."""
import base64, io, json, math, os, re, sys, glob, hashlib
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '/home/claude/out/artifact')
LIVE = 'https://tigrestudiodesign.github.io/'
BUNDLE_MAX = 12 * 1024 * 1024
STEPS = [480, 640, 800, 1080, 1280, 1600, 1920, 2560]
M = json.load(open('tools/image_map.json'))
s = open('index.html').read()
s = re.sub(r"(img/[^'\"?\s)]+)\?v=\d+", r'\1', s)   # cache-busting queries are for the live site only
os.makedirs(OUT + '/b', exist_ok=True)
for f in glob.glob(OUT + '/b/*'): os.remove(f)

# ---------- images: one encode per (file, width step) ----------
cache = {}
def enc(f, px):
    im0 = Image.open(f); W = im0.width
    t = W if px <= 0 else next((x for x in STEPS if x >= px), STEPS[-1])
    t = min(t, W)
    k = (f, t)
    if k in cache: return cache[k]
    if t >= W * 0.92 and f.endswith('.webp'):
        b = open(f, 'rb').read()
    else:
        im = im0.convert('RGBA') if im0.mode in ('RGBA', 'LA', 'P') else im0.convert('RGB')
        if t < W: im = im.resize((t, round(im.height * t / W)), Image.LANCZOS)
        bb = io.BytesIO(); im.save(bb, 'WEBP', quality=82, method=5); b = bb.getvalue()
        if f.endswith('.webp') and len(b) > os.path.getsize(f): b = open(f, 'rb').read()
    cache[k] = b; return b

css = set(M.get('css', [])) | set(re.findall(r'url\((img/[^)\s\'"]+)\)', s))
def slug(r): return 'home' if r == '' else re.sub(r'[^a-z0-9]+', '-', r.lower()).strip('-')[:60] or 'x'
BUN = {}            # route -> {"f":[files], "i": {path: [part, off, len]}}
placed = set()
def add_bundle(key, items):
    # artifacts only serve web file types, so a bundle is a .json object {path: data URI}
    parts = [{}]; size = 0; idx = {}
    for f, px in items:
        if not os.path.exists(f) or not re.search(r'\.(webp|png|jpg|jpeg)$', f): continue
        u = 'data:image/webp;base64,' + base64.b64encode(enc(f, px)).decode()
        if size + len(u) > BUNDLE_MAX and parts[-1]:
            parts.append({}); size = 0
        parts[-1][f] = u; size += len(u); idx[f] = len(parts) - 1; placed.add(f)
    names = []
    for i, d in enumerate(parts):
        if not d: continue
        n = 'b/%s%s.json' % (slug(key) if not key.startswith('~') else key[1:], '' if i == 0 else '-%d' % i)
        json.dump(d, open(OUT + '/' + n, 'w'), separators=(',', ':')); names.append(n)
    if idx: BUN[key] = {'f': names, 'i': idx}

for r, imgs in M['routes'].items():
    add_bundle(r, [(f, px) for f, px in sorted(imgs.items()) if f not in css])
# everything else the code can reach (tabs, viewers, rarely drawn states): full size, capped
rest = sorted(f for f in glob.glob('img/**/*.*', recursive=True)
              if re.search(r'\.(webp|png|jpg|jpeg)$', f) and f not in placed and f not in css
              and (os.path.basename(f) in s or re.search(r"img/[\w/]*%s" % re.escape(os.path.basename(f).split('__')[0]), s)))
# grouped by project prefix so a page that needs one of them loads a small bundle, not all of them
groups = {}
for f in rest:
    b = os.path.basename(f); g = b.split('__')[0] if '__' in b else os.path.dirname(f).replace('img', '').strip('/') or 'misc'
    groups.setdefault(g, []).append(f)
for g, fs in sorted(groups.items()):
    add_bundle('~x-' + re.sub(r'[^a-z0-9]+', '-', g.lower()), [(f, 1600) for f in fs])

# ---------- page code ----------
# CSS background sprites stay real files; downloads, films and full-size links open on the live site
s = re.sub(r'href="(downloads/[^"]+\.pdf)" download', lambda m: 'href="' + LIVE + m.group(1) + '" target="_blank" rel="noopener"', s)
s = s.replace('<video class="ta-v" src="${f}" poster="${po}" width="${w}" height="${h}" muted loop playsinline autoplay preload="auto" aria-label="${esc(c)}"></video>',
 '<a class="ta-pl" href="' + LIVE + '#p11" target="_blank" rel="noopener"><img ${pkA(po)} width="${w}" height="${h}" alt="${esc(c)}"><span>▶ Play film</span></a>')
s = s.replace('.ta-films video{', '.ta-pl{position:relative;display:block}.ta-pl img{display:block;width:100%;height:100%;object-fit:cover}.ta-pl span{position:absolute;left:12px;bottom:12px;background:#FF5A1F;color:#0B0B0C;font:700 12px var(--mono);padding:6px 10px;letter-spacing:.06em}.ta-films video{')
s = re.sub(r'"(img/[^"]+\.mp4)"', lambda m: '"' + LIVE + m.group(1) + '"', s)
s = re.sub(r"'(downloads/[^']+\.pdf)'", lambda m: "'" + LIVE + m.group(1) + "'", s)
s = re.sub(r'(href="\$\{[A-Za-z_.]+\}") download', r'\1 target="_blank" rel="noopener"', s)
s = re.sub(r'(<a\b[^>]*?)\sdownload(?=[\s>])(?![^>]*target=)', r'\1 target="_blank" rel="noopener"', s)
s = re.sub(r'(<a\b[^>]*?)\sdownload(?=[\s>])', r'\1', s)
s = re.sub(r'<a href="(img/[^"]+)"', lambda m: '<a href="' + LIVE + m.group(1) + '" target="_blank" rel="noopener"', s)
# literal <img src="img/..."> in templates -> filled from the bundle
BLANK = 'data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=='
def _lit(m):
    pre, p = m.group(1), m.group(2)
    if p in css: return m.group(0)
    if '${' in p: return '<img%s ${pkA(`%s`)}' % (pre, p)
    return '<img%s data-pk="%s" src="%s"' % (pre, p, BLANK)
s = re.sub(r'<img\b([^>]*?)\ssrc="(img/[^"]+)"', _lit, s)
a = "const im=(r,alt,cls='')=>`<img src=\"${r[0]}\""
assert a in s, 'im() changed'
s = s.replace(a, "const im=(r,alt,cls='')=>`<img ${pkA(r[0])}", 1)
LOADER = r"""
/* artifact image bundles (built by tools/build_artifact.py) */
const PKB=__B__,PKZ='__Z__';const pkW={};for(const r in PKB)for(const p in PKB[r].i)(pkW[p]=pkW[p]||[]).push(r);
const pkA=p=>(typeof p==='string'&&pkW[p])?`data-pk="${p}" src="${PKZ}"`:`src="${p}"`;
const pkBuf={};
const pkGet=f=>pkBuf[f]||(pkBuf[f]=fetch(f).then(r=>{if(!r.ok)throw r.status;return r.json()}));
const pkPick=p=>{const h=location.hash.slice(1),c=pkW[p];return c.includes(h)?h:c.includes('')&&!h?'':c[0]};
async function pkFill(e){const p=e.dataset.pk;if(!p||!pkW[p])return;const r=pkPick(p);
 try{const j=await pkGet(PKB[r].f[PKB[r].i[p]]);if(e.dataset.pk===p&&j[p]){e.src=j[p];e.removeAttribute('data-pk')}}catch(x){}}
const pkSrc=e=>{const v=e.getAttribute('src')||'';if(!e.dataset.pk&&pkW[v]){e.dataset.pk=v;e.src=PKZ}if(e.dataset.pk)pkFill(e)};
const pkScan=n=>{if(n.nodeType!==1)return;if(n.tagName==='IMG')pkSrc(n);n.querySelectorAll&&n.querySelectorAll('img').forEach(pkSrc)};
new MutationObserver(ms=>{for(const m of ms){if(m.type==='attributes'){const e=m.target,v=e.getAttribute('src')||'';if(e.tagName==='IMG'&&pkW[v]){e.dataset.pk=v;e.src=PKZ;pkFill(e)}}else m.addedNodes.forEach(pkScan)}})
 .observe(document.documentElement,{subtree:true,childList:true,attributes:true,attributeFilter:['src']});
"""
LOADER = LOADER.replace('__B__', json.dumps(BUN, separators=(',', ':'))).replace('__Z__', BLANK)
i = s.find('<script>')
assert i > 0
s = s[:i + 8] + LOADER + s[i + 8:]
s = s.replace('</body>', '<script>document.querySelectorAll("img[data-pk]").forEach(pkFill)</script></body>', 1)
_ix = OUT + '/index.html'
if os.path.islink(_ix): os.remove(_ix)
open(_ix, 'w').write(s)

# ---------- the artifact's file list ----------
files = ['index.html'] + sorted(n for b in BUN.values() for n in b['f'])
for f in sorted(set(re.findall(r'url\((fonts/[^)]+)\)', s)) | css | {'data/ka_atlas.json', 'figures.js'} | set(glob.glob('games/*.html'))):
    if os.path.exists(f):
        os.makedirs(os.path.dirname(OUT + '/' + f) or OUT, exist_ok=True)
        if f != 'index.html':
            dst = OUT + '/' + f
            if os.path.islink(dst) or os.path.exists(dst): os.remove(dst)   # never write through a symlink into the repo
            open(dst, 'wb').write(open(f, 'rb').read())
        files.append(f)
json.dump(files, open(OUT + '/files.json', 'w'), indent=0)
tot = sum(os.path.getsize(OUT + '/' + f) for f in files)
big = max(os.path.getsize(OUT + '/' + f) for f in files)
print('index %d bytes; %d files; %d bundles; total %.1f MB; biggest file %.1f MB' % (len(s), len(files), sum(len(b['f']) for b in BUN.values()), tot / 1e6, big / 1e6))
assert len(s) < 15 * 1024 * 1024 and len(files) < 480 and big < 19 * 1024 * 1024, 'artifact limits'
