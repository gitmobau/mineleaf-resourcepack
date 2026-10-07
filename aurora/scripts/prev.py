from PIL import Image
import os
L=lambda f: Image.open(f).convert('RGBA')
S=4
sheet=Image.new('RGBA',(900,820),(90,120,80,255))
def put(im,x,y,s=S): sheet.alpha_composite(im.resize((im.width*s,im.height*s),Image.NEAREST),(x,y))
put(L('gui/sprites/hud/hotbar.png'),20,20)
put(L('gui/sprites/hud/hotbar_selection.png').crop((0,0,24,23)),20-4+40*S,20-4)
tools=['diamond_sword','diamond_pickaxe','diamond_axe','diamond_shovel','netherite_sword','netherite_pickaxe','netherite_axe','netherite_hoe','diamond_spear']
for i,t in enumerate(tools): put(L('item/'+t+'.png'),20+(3+i*20)*S,20+3*S)
put(L('gui/sprites/hud/experience_bar_background.png'),20,120)
put(L('gui/sprites/hud/experience_bar_progress.png').crop((0,0,120,5)),20,120)
put(L('gui/sprites/hud/crosshair.png'),800,140,6)
put(L('gui/container/inventory.png').crop((0,0,176,166)),20,160,3)
ws=L('block/water_still.png').crop((0,0,16,16)); tint=(63,118,228)
wt=Image.new('RGBA',(64,64))
for ty in range(4):
  for tx in range(4): wt.alpha_composite(ws,(tx*16,ty*16))
px=wt.load()
for y in range(64):
  for x in range(64):
    r,g,b,a=px[x,y]; px[x,y]=(r*tint[0]//255,g*tint[1]//255,b*tint[2]//255,a)
put(wt,560,160,4)
for i,t in enumerate(['diamond_sword','diamond_pickaxe','diamond_axe','diamond_shovel','diamond_hoe','diamond_spear']):
  put(L('item/'+t+'.png'),560+i*56,440,3); put(L('item/'+t.replace('diamond','netherite')+'.png'),560+i*56,500,3)
put(L('item/diamond_spear_in_hand.png'),560,560,3); put(L('item/netherite_spear_in_hand.png'),680,560,3)
put(L('../../../pack.png'),20,680,1)
sheet.save('../../../_ref.png')
