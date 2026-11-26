"""Cover image for the portfolio artifact's gallery card and link previews.
Run from the repo root:  python3 tools/make_thumb.py   ->  tools/artifact_thumb.png (1200x630, under 1 MB)
tools/build_artifact.py copies it into the artifact as thumb.png and links it from the page head."""
from PIL import Image, ImageDraw, ImageFont, ImageOps

W, H = 1200, 630
BG, GRID, ORANGE, INK, MUTED = (11, 11, 12), (27, 27, 30), (255, 90, 31), (242, 238, 230), (140, 136, 128)
F = '/usr/share/fonts/opentype/inter/'
black = lambda s: ImageFont.truetype(F + 'InterDisplay-Black.otf' if __import__('os').path.exists(F + 'InterDisplay-Black.otf') else F + 'Inter-Black.otf', s)
bold = lambda s: ImageFont.truetype(F + 'Inter-Bold.otf', s)
mono = lambda s: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', s)

im = Image.new('RGB', (W, H), BG)
d = ImageDraw.Draw(im)
for x in range(0, W, 30): d.line([(x, 0), (x, H)], fill=GRID)
for y in range(0, H, 30): d.line([(0, y), (W, y)], fill=GRID)

# project mosaic, right side: 2 x 2 tiles
tiles = ['img/ml__board_vz.webp', 'img/bc2__hero.webp', 'img/spvz__shelf.webp', 'img/hk__hero.webp']
labels = ['MATERIAL LIBRARY', 'BASECAMP', 'STANDARD PLAY', 'HESTIA']
tw, th, gap, x0, y0 = 252, 252, 12, 660, 54
for i, (p, lab) in enumerate(zip(tiles, labels)):
    x, y = x0 + (i % 2) * (tw + gap), y0 + (i // 2) * (th + gap)
    t = ImageOps.fit(Image.open(p).convert('RGB'), (tw, th), Image.LANCZOS, centering=(0.5, 0.5))
    im.paste(t, (x, y))
    d.rectangle([x, y, x + tw - 1, y + th - 1], outline=(60, 60, 64))
    lw = d.textlength(lab, font=mono(11))
    d.rectangle([x + 8, y + th - 28, x + 8 + lw + 14, y + th - 9], fill=BG)
    d.text((x + 15, y + th - 25), lab, font=mono(11), fill=INK)
    d.text((x + 8, y + 8), f'{i + 1:02d}', font=mono(11), fill=ORANGE)

# corner ticks around the mosaic
mx0, my0, mx1, my1 = x0 - 14, y0 - 14, x0 + 2 * tw + gap + 14, y0 + 2 * th + gap + 14
for cx, cy, sx, sy in [(mx0, my0, 1, 1), (mx1, my0, -1, 1), (mx0, my1, 1, -1), (mx1, my1, -1, -1)]:
    d.line([(cx, cy), (cx + 18 * sx, cy)], fill=ORANGE, width=2)
    d.line([(cx, cy), (cx, cy + 18 * sy)], fill=ORANGE, width=2)

# type, left side
X = 60
d.text((X, 62), 'TIGRE STUDIO · PORTFOLIO 2026', font=mono(14), fill=ORANGE)
d.line([(X, 92), (X + 520, 92)], fill=(60, 60, 64), width=1)
d.text((X, 120), 'HENRY', font=black(96), fill=INK)
d.text((X, 214), 'ORTEGA', font=black(96), fill=INK)
d.text((X, 340), 'SENIOR CREATIVE FOR', font=bold(32), fill=INK)
d.text((X, 380), 'TECHNICAL PRODUCTS', font=bold(32), fill=ORANGE)
d.text((X, 446), 'CMF · MATERIAL SYSTEMS · TECHNICAL', font=mono(13), fill=MUTED)
d.text((X, 468), 'DOCUMENTATION · COMPUTATIONAL DESIGN', font=mono(13), fill=MUTED)
# knurled dial accent
cx, cy, r = X + 26, 548, 22
d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(42, 43, 47), outline=(90, 92, 98), width=2)
import math
for k in range(36):
    a = k * math.pi / 18
    d.line([(cx + (r - 6) * math.cos(a), cy + (r - 6) * math.sin(a)), (cx + r * math.cos(a), cy + r * math.sin(a))], fill=(120, 122, 128), width=1)
d.line([(cx, cy - 14), (cx, cy - 5)], fill=ORANGE, width=3)
d.text((X + 64, 532), 'OPEN TO SENIOR IC ROLES', font=mono(13), fill=INK)
d.text((X + 64, 552), 'PORTLAND, OR · REMOTE', font=mono(13), fill=MUTED)
d.text((W - 60, H - 34), 'TIGRESTUDIODESIGN.GITHUB.IO', font=mono(12), fill=MUTED, anchor='ra')

im.save('tools/artifact_thumb.png', optimize=True)
print('tools/artifact_thumb.png', __import__('os').path.getsize('tools/artifact_thumb.png') // 1000, 'KB')
