exec(open('/home/claude/styles/_u.py').read())
P={'shell':'#B9A9F0','face':'#FFB48C','plate':'#FFE27A','orange':'#FF8A6B','graph':'#7D76B8','rubber':'#6E6AA0','alu':'#FFE27A','steel':'#FFD5E5','cell':'#FF8A6B','pcb':'#9FE3C9','chip':'#6E6AA0','cone':'#6E6AA0','blk':'#5B568C','back':'#B9A9F0','sos':'#FF6F7D','diff':'#FFF3D6','btn_*':'#FFD5E5','ledoff':'#C9B9F5'}
for k,c in P.items(): setm(k,col=c,rough=0.9,metal=0,coat=0,spec=0.25,ink='#4A4580')
setm('ledon',col='#FF8A6B',emis=('#FF8A6B',2))
floor('#BFE8D6','#B2DFCB',rough=0.95); world('#E9F6EF',0.12)
clear_lights(); area((-0.45,-0.5,0.6),1.1,4.5); area((0.6,-0.3,0.3),0.9,1.4,'#FFF1E6'); area((0.1,0.5,0.5),0.8,2,'#E8E4FF')
