exec(open('/home/claude/styles/_u.py').read())
for k in ('shell','back','face','plate'): setm(k,col='#F4F7FF',rough=0.07,trans=1.0,metal=0,coat=0,ink='#FFFFFF',spec=0.6,sss=0)
setm('pcb',col='#16E0B0',rough=0.35,emis=('#16E0B0',0.15)); setm('cell',col='#FF5A1F',coat=1)
setm('diff',col='#FFFFFF',rough=0.15,trans=1.0)
floor('#0E0B1E','#1B1640',rough=0.4); world('#0E0B1E',0.2)
for loc,r,c,s in [((-0.16,0.30,0.10),0.07,'#7B5CFF',4),((0.14,0.26,0.15),0.06,'#FF4FA3',4),((0.0,0.34,0.04),0.05,'#20D5FF',4)]:
    sphere(loc,r,emat('blob'+c,c,s))
clear_lights(); area((-0.4,-0.5,0.55),0.8,10); area((0.5,-0.3,0.25),0.6,6,'#D9E4FF')
bpy.context.scene.cycles.transmission_bounces=12; bpy.context.scene.cycles.max_bounces=12
