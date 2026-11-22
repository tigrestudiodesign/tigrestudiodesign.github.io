from PIL import Image, ImageDraw, ImageFont
W,H=1500,1200; BG=(244,242,238); INK=(20,20,22); OR=(255,90,31)
F=lambda f,s: ImageFont.truetype(f,s)
BLK='/tmp/fonts/InterDisplay-Black.ttf'; BLD='/tmp/fonts/InterDisplay-Bold.ttf'; MONO='/tmp/fonts/JetBrainsMono-400.ttf'; MONOB='/tmp/fonts/JetBrainsMono-700.ttf'
im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
M=60; cols=12; cw=(W-2*M)/cols
for i in range(cols+1): d.line([(M+i*cw,0),(M+i*cw,H)],fill=(230,227,221),width=1)
# orange field, right 5 columns
x0=M+7*cw; d.rectangle([x0,0,W,H],fill=OR)
r=Image.open('/home/claude/basecamp2/F_front.png').crop((222,150,1348,1214))
s=640/r.height; r=r.resize((int(r.width*s),640),Image.LANCZOS)
im.paste(r,(int(W-M-r.width+40),int(H-M-r.height-40)),r)
d=ImageDraw.Draw(im)
d.text((M-8,M-40),'BASE',font=F(BLK,250),fill=INK); d.text((M-8,M+170),'CAMP',font=F(BLK,250),fill=INK)
d.line([(M,M+470),(x0-cw,M+470)],fill=INK,width=4)
blocks=[('01','HAND-CRANK','RADIO + LANTERN'),('02','TORX HARDWARE','REPAIRABLE'),('03','ONE ORANGE','THE REST QUIET')]
for i,(n,a,b) in enumerate(blocks):
    x=M+i*(cw*1.9); y=M+500
    d.text((x,y),n,font=F(MONOB,22),fill=OR); d.text((x,y+40),a,font=F(MONOB,19),fill=INK); d.text((x,y+68),b,font=F(MONO,19),fill=INK)
d.text((M,H-M-150),'Emergency',font=F(BLD,64),fill=INK); d.text((M,H-M-80),'radio, 2026.',font=F(BLD,64),fill=INK)
d.text((M,H-M-200),'TIGRE STUDIO · STYLE 07 / SWISS',font=F(MONO,18),fill=(110,106,100))
d.text((x0+24,M-6),'FIG. 1',font=F(MONOB,22),fill=(255,255,255)); d.text((x0+24,M+24),'FRONT ELEVATION · 1:2',font=F(MONO,18),fill=(255,255,255))
im.save('/home/claude/series/swiss.png')
