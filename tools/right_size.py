"""Shrink site images that are stored much wider than they are ever drawn (2x retina), keeping the hi-res look.
usage: python3 tools/right_size.py [--dry]
Uses tools/image_map.json (run tools/image_map.py first). Only rewrites a file when it saves at least 30%,
so git history does not grow from tiny re-encodes. Masters belong in Google Drive, not in this repo."""
import io, json, os, sys
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
STEPS = [800, 1080, 1280, 1600, 1920, 2560]
M = json.load(open('tools/image_map.json')); dry = '--dry' in sys.argv
full = set(M.get('full', [])) | set(M.get('css', []))
saved = 0; n = 0
for f, need in sorted(M['need'].items()):
    if f in full or not os.path.exists(f) or not f.endswith(('.webp', '.jpg', '.png')): continue
    im = Image.open(f); W = im.width; old = os.path.getsize(f)
    t = next((x for x in STEPS if x >= need * 1.0), STEPS[-1])
    if W <= t * 1.15 and old < 1.5e6: continue
    t = min(t, W)
    im = im.convert('RGBA') if im.mode in ('RGBA', 'LA', 'P') else im.convert('RGB')
    if t < W: im = im.resize((t, round(im.height * t / W)), Image.LANCZOS)
    bb = io.BytesIO(); im.save(bb, 'WEBP', quality=84, method=6); b = bb.getvalue()
    if len(b) > old * 0.7: continue
    n += 1; saved += old - len(b)
    print('%-60s %5d -> %5dpx  %6.0f -> %6.0f KB' % (f, W, t, old / 1e3, len(b) / 1e3))
    if not dry:
        if f.endswith('.webp'): open(f, 'wb').write(b)
        else: print('   (not .webp: left as is)')
print('%d images, %.1f MB saved%s' % (n, saved / 1e6, ' (dry run)' if dry else ''))
