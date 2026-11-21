"""Space check for the GitHub site and the claude.ai artifact. Run before every push.
usage: python3 tools/size_report.py [ARTIFACT_OUTDIR]
Exit code 1 when a budget is broken. Budgets:
  GitHub: published site < 500 MB (GitHub Pages limit is 1 GB), no single file > 25 MB,
          no image > 1.5 MB, no image over 7 megapixels except CSS sprites and full-size linked files.
  Artifact: index.html < 4 MB (hard cap 16 MiB), < 400 files (cap 512), each file < 15 MB (cap 20 MiB)."""
import json, os, subprocess, sys, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
from PIL import Image
try: _m = json.load(open('tools/image_map.json')); CSSIMG = set(_m.get('css', [])) | set(_m.get('full', []))
except FileNotFoundError: CSSIMG = set()
bad = []; warn = []
def _mp(f):
    try: im = Image.open(f); return im.width * im.height
    except Exception: return 0
files = [f for f in subprocess.check_output(['git', 'ls-files'], text=True).split('\n') if f and os.path.exists(f)]
site = sum(os.path.getsize(f) for f in files)
print('GitHub site files: %d, %.1f MB (budget 500 MB)' % (len(files), site / 1e6))
if site > 500e6: bad.append('site over 500 MB')
try:
    pk = subprocess.check_output(['git', 'count-objects', '-v'], text=True)
    sp = int([l for l in pk.split('\n') if l.startswith('size-pack')][0].split()[1]) * 1024
    print('git history (packed): %.1f MB  (GitHub warns at 1 GB; if near, see README "Squash history")' % (sp / 1e6))
except Exception: pass
for f in files:
    sz = os.path.getsize(f)
    if sz > 25e6: bad.append('file > 25 MB: ' + f)
    if f.startswith('img/') and f.endswith(('.webp', '.jpg', '.png')) and 'sprite' not in f and f not in CSSIMG and _mp(f) > 7.2e6: bad.append("image over 7 megapixels: " + f)
    if f.startswith('img/') and f.endswith(('.webp', '.jpg', '.png')) and sz > 1.5e6 and 'sprite' not in f: bad.append('image > 1.5 MB: %s (%.1f MB)' % (f, sz / 1e6))
try:
    from PIL import Image
    need = json.load(open('tools/image_map.json'))['need']
    for f, t in need.items():
        if os.path.exists(f):
            try: W = Image.open(f).width
            except Exception: continue
            if W > max(t, 480) * 1.3 and os.path.getsize(f) > 150e3: warn.append('%s %dpx (drawn needs %dpx)' % (f, W, t))
except FileNotFoundError: print('no tools/image_map.json yet: run tools/image_map.py')
print('%d images stored wider than they are drawn (fine, just extra bytes; tools/right_size.py can shrink them)' % len(warn))
top = sorted(files, key=os.path.getsize, reverse=True)[:8]
print('largest:', ', '.join('%s %.1fMB' % (f, os.path.getsize(f) / 1e6) for f in top))
out = sys.argv[1] if len(sys.argv) > 1 else None
if out and os.path.exists(out + '/files.json'):
    af = json.load(open(out + '/files.json'))
    ix = os.path.getsize(out + '/index.html'); big = max(os.path.getsize(out + '/' + f) for f in af)
    print('Artifact: index.html %.2f MB (budget 4), %d files (budget 400), biggest %.1f MB (budget 15), total %.1f MB'
          % (ix / 1e6, len(af), big / 1e6, sum(os.path.getsize(out + '/' + f) for f in af) / 1e6))
    if ix > 4e6: bad.append('artifact index.html over 4 MB')
    if len(af) > 400: bad.append('artifact over 400 files')
    if big > 15.5 * 1024 * 1024: bad.append('artifact file over 15 MB')
print('\n'.join('OVER BUDGET: ' + b for b in bad) or 'All within budget.')
sys.exit(1 if bad else 0)
