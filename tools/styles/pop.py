import sys, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
SRC=sys.argv[1] if len(sys.argv)>1 else '/home/claude/series/cut.png'
W,H=1500,1200; YEL=(255,228,0); RED=(232,35,28); BLU=(29,79,216); INK=(15,15,17); WH=(255,255,255)
im=Image.new('RGB',(W,H),YEL); d=ImageDraw.Draw(im)
for j,y in enumerate(range(0,H+30,26)):
    for x in range(0 if j%2 else 13,W+30,26): d.ellipse([x-6,y-6,x+6,y+6],fill=(255,150,0))
# burst
cx,cy=W*0.52,H*0.5; pts=[]
for i in range(32):
    a=i*math.pi/16; r=(560 if i%2==0 else 410)*(1+0.06*math.sin(i*2.3)); pts.append((cx+r*math.cos(a),cy+r*math.sin(a)*0.82))
d.polygon(pts,fill=WH,outline=INK,width=8)
# radio: flat-colour posterise
r=Image.open(SRC).convert('RGBA'); r=r.crop(r.split()[-1].getbbox())
s=820/r.width; r=r.resize((820,int(r.height*s)),Image.LANCZOS)
a=r.split()[-1]; rgb=r.convert('RGB')
from PIL import ImageEnhance
rgb=ImageEnhance.Color(ImageEnhance.Contrast(ImageEnhance.Brightness(rgb).enhance(1.45)).enhance(1.25)).enhance(1.8)
pal=Image.new('P',(1,1)); P=[*INK,*WH,*RED,*BLU,*YEL,(150,150,155),(60,60,66)]; pal.putpalette([c for t in [INK,WH,RED,BLU,YEL,(170,170,176),(70,70,78)] for c in t]+[0]*(768-21))
q=rgb.quantize(palette=pal,dither=Image.Dither.NONE).convert('RGB')
# halftone dots on greys
L=rgb.convert('L'); ht=Image.new('L',q.size,0); hd=ImageDraw.Draw(ht)
for y in range(0,q.height,12):
    for x in range(0,q.width,12):
        v=L.getpixel((x,y)); rr=(1-v/255)*3.4
        if rr>0.6: hd.ellipse([x-rr,y-rr,x+rr,y+rr],fill=255)
q=Image.composite(Image.new('RGB',q.size,INK),q,ImageChops.multiply(ht,L.point(lambda v:255 if 110<v<200 else 0)))
edges=q.convert('L').filter(ImageFilter.FIND_EDGES).point(lambda v:255 if v>40 else 0).filter(ImageFilter.MaxFilter(3))
q=Image.composite(Image.new('RGB',q.size,INK),q,edges)
ox,oy=int(cx-q.width/2),int(cy-q.height/2+20)
outl=a.filter(ImageFilter.MaxFilter(17))
im.paste(INK,(ox+14,oy+14),outl); im.paste(INK,(ox,oy),outl); im.paste(q,(ox,oy),a)
# lettering
t=Image.new('RGBA',(1100,260),(0,0,0,0)); td=ImageDraw.Draw(t); f=ImageFont.truetype('/tmp/fonts/InterDisplay-Black.ttf',190)
for dx,dy,c in [(10,10,INK),(0,0,RED)]: td.text((20+dx,10+dy),'CRANK IT!',font=f,fill=c,stroke_width=8,stroke_fill=INK)
t=t.rotate(8,expand=True,resample=Image.BICUBIC); im.paste(t,(40,40),t)
d=ImageDraw.Draw(im); m=ImageFont.truetype('/tmp/fonts/JetBrainsMono-700.ttf',22)
d.rectangle([60,H-110,560,H-60],fill=INK); d.text((80,H-100),'TIGRE STUDIO · STYLE 05 / POP ART',font=m,fill=YEL)
im.save('/home/claude/series/pop.png')
