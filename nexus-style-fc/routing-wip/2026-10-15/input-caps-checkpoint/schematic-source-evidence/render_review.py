from pathlib import Path
import fitz
from PIL import Image
P=Path(__file__).parent/'preview';d=fitz.open(P/'connected.pdf');s=d[0].rect.width/841
boxes=[(20,44,278,174),(20,180,278,265),(20,271,278,376),(20,382,278,464),(20,470,278,555),(286,44,544,184),(286,190,544,285),(286,291,544,370),(286,376,544,461),(286,467,544,555),(552,44,821,149),(552,155,821,300),(552,306,821,396),(552,402,821,478),(552,484,821,545)]
names=['VX input and 5 V buck','5 V source priority','VSYS and MCU 3.3 V','Sensor supply','Voltage monitoring','STM32F722 core','Clock, boot and debug','MCU decoupling','SPI1 inertial sensor','I2C1 pressure sensor','USB-C and protection','Receiver interfaces','Servo header and clamps','SPI2 blackbox','Status indication']
review=fitz.open();toc=[]
for i,(box,name) in enumerate(zip(boxes,names),1):
 rect=fitz.Rect(*[v*s for v in box]);d[0].get_pixmap(matrix=fitz.Matrix(2,2),clip=rect).save(P/f'panel-{i:02}.png')
 pg=review.new_page(width=842,height=595);pg.show_pdf_page(fitz.Rect(20,20,822,555),d,0,clip=rect);pg.insert_text((20,580),f'Nexus-style FC / connected circuit {i:02} / Unfinished PCB checkpoint; not for fabrication',fontsize=9);toc.append([1,f'{i:02} {name}',i])
review.set_toc(toc);review.save(P/'nexus-connected-circuits-review.pdf')
for col in range(3):
 imgs=[]
 for i in range(col*5+1,col*5+6):
  im=Image.open(P/f'panel-{i:02}.png').convert('RGB');im.thumbnail((1400,800));imgs.append(im)
 canvas=Image.new('RGB',(1400,sum(im.height for im in imgs)+40),'white');y=0
 for im in imgs:canvas.paste(im,(0,y));y+=im.height+8
 canvas.save(P/f'column-{col+1}.png')
d[0].get_pixmap(matrix=fitz.Matrix(.9,.9)).save(P/'connected.png')
