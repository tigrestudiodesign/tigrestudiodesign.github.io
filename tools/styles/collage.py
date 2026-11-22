import sys, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageChops
random.seed(7)
SRC=sys.argv[1] if len(sys.argv)>1 else '/home/claude/series/cut.png'
W,H=1500,1200
noise=Image.effect_noise((W,H),18).convert('L')
nz=noise.point(lambda p:max(0,min(40,(p-108)//2)))
im=Image.merge('RGB',[ImageChops.add(Image.new('L',(W,H),v-20),nz) for v in (240,232,218)])
def torn(poly_pts, fill, jag=10):
    pts=[]
    for i in range(len(poly_pts)):
        a=poly_pts[i]; b=poly_pts[(i+1)%len(poly_pts)]
        n=int(math.dist(a,b)/14)+1
        for k in range(n):
            t=k/n; pts.append((a[0]+(b[0]-a[0])*t+random.uniform(-jag,jag),a[1]+(b[1]-a[1])*t+random.uniform(-jag,jag)))
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(lay).polygon(pts,fill=fill)
    sh=lay.split()[-1].filter(ImageFilter.GaussianBlur(6)); im.paste((0,0,0),(6,8),sh.point(lambda v:v*0.25))
    im.paste(lay,(0,0),lay)
torn([(80,120),(760,60),(820,640),(140,700)],(255,90,31,255))
torn([(700,420),(1430,380),(1460,1120),(760,1150)],(30,32,36,255))
torn([(980,70),(1420,110),(1390,330),(960,300)],(120,166,214,255))
# halftone ghost of the object, offset
r=Image.open(SRC).convert('RGBA'); r=r.crop(r.split()[-1].getbbox()); s=760/r.width; r=r.resize((760,int(r.height*s)),Image.LANCZOS)
L=r.convert('L'); a=r.split()[-1]; ht=Image.new('L',r.size,0); hd=ImageDraw.Draw(ht)
for y in range(0,r.height,11):
    for x in range(0,r.width,11):
        if a.getpixel((x,y))>128:
            rr=(1-L.getpixel((x,y))/255)*5+1; hd.ellipse([x-rr,y-rr,x+rr,y+rr],fill=255)
ghost=Image.new('RGBA',r.size,(20,20,22,0)); ghost.putalpha(ht)
g=ghost.rotate(-6,expand=True,resample=Image.BICUBIC); im.paste((20,20,22),(150,330),g.split()[-1])
# sticker cut-out with white border
border=a.filter(ImageFilter.MaxFilter(23))
st=Image.new('RGBA',r.size,(255,255,255,0)); st.putalpha(border); st.alpha_composite(r)
st=st.rotate(4,expand=True,resample=Image.BICUBIC)
shadow=st.split()[-1].filter(ImageFilter.GaussianBlur(10)).point(lambda v:v*0.35)
px,py=470,240; im.paste((0,0,0),(px+12,py+16),shadow); im.paste(st,(px,py),st)
# tape
def tape(cx,cy,ang,w=220,h=58):
    t=Image.new('RGBA',(w,h),(238,226,190,170)); td=ImageDraw.Draw(t)
    for x in range(0,w,6): td.line([(x,0),(x,3)],fill=(0,0,0,0)); td.line([(x+3,h-3),(x+3,h)],fill=(0,0,0,0))
    t=t.rotate(ang,expand=True,resample=Image.BICUBIC); im.paste(t,(int(cx-t.width/2),int(cy-t.height/2)),t)
tape(700,270,24); tape(1300,880,-18); tape(170,140,-30,160)
d=ImageDraw.Draw(im); mono=ImageFont.truetype('/tmp/fonts/JetBrainsMono-700.ttf',24); big=ImageFont.truetype('/tmp/fonts/InterDisplay-Black.ttf',118)
d.text((110,170),'FIELD',font=big,fill=(20,20,22)); d.text((110,290),'NOTES',font=big,fill=(244,239,228))
lab=Image.new('RGBA',(420,52),(250,248,240,255)); ImageDraw.Draw(lab).text((14,12),'NO. 001 · KEEP DRY · CRANK 60 S',font=ImageFont.truetype('/tmp/fonts/JetBrainsMono-400.ttf',19),fill=(20,20,22))
lab=lab.rotate(-3,expand=True,resample=Image.BICUBIC); im.paste(lab,(150,760),lab)
d.rectangle([60,H-100,620,H-52],fill=(20,20,22)); d.text((78,H-92),'TIGRE STUDIO · STYLE 08 / COLLAGE',font=mono,fill=(244,239,228))
im.save('/home/claude/series/collage.png')
