"""Explicit regulator and sensing circuits, drafted left-to-right."""
def draw(d):
 d.panel('01  VX INPUT / 5 V BUCK',20,44,258,130,'TPS62130: 3 A, 2.5 MHz  |  Vout = 0.8 V x (1 + 120k / 22k) = 5.16 V')
 d.place('U5',108,70);u=lambda n:d.p('U5',n)
 # Input protection and capacitors share one short input rail.
 for r,x in [('D4',16),('C21',39),('C22',64)]:
  d.place(r,x,41,270 if r=='D4' else 0)
  p=d.p(r,'1');d.wire(p,(p[0],28));d.ground(r,'2',drop=6.35)
 d.wire((16,28),(80,28),(80,u('13')[1]));d.label('VX',(16,28),90)
 for n in ('11','12','10','13'):
  p=u(n);d.wire(p,(80,p[1]));d.dot((80,p[1]))
 for x in (39,64):d.dot((x,28))
 # Switch-node bundle, horizontal inductor, output rail and feedback divider.
 sw=u('1');d.place('L1',164,sw[1],90);l1=d.p('L1','1');l2=d.p('L1','2')
 for n in ('1','2','3'):p=u(n);d.wire(p,(140,p[1]))
 d.wire((140,u('3')[1]),(140,sw[1]),l1);d.dot((140,u('2')[1]));d.dot((140,sw[1]));d.label('SW_5V',(140,sw[1]),90)
 d.place('C24',194,62);d.place('R11',234,68);d.place('R12',234,91)
 d.wire(l2,(248,sw[1]));d.label('5V_BUCK',(248,sw[1]))
 for r in ('C24','R11'):
  p=d.p(r,'1');d.wire(p,(p[0],sw[1]));d.dot((p[0],sw[1]))
 p=u('14');d.wire(p,(183,p[1]),(183,sw[1]));d.dot((183,sw[1]))
 mid=(234,79);d.wire(d.p('R11','2'),mid,d.p('R12','1'));d.wire(u('5'),(222,u('5')[1]),(222,79),mid);d.dot(mid);d.label('FB_5V',(178,u('5')[1]))
 # label sits on the feedback segment
 d.ground('C24','2',drop=2.54);d.ground('R12','2',drop=6.35)
 d.place('C23',70,82);p=u('9');d.wire(p,(70,p[1]),d.p('C23','1'));d.label('SS_5V',(70,p[1]),90);d.ground('C23','2',drop=6.35)
 for pins,x in [(('8','7'),80),(('17','6','15','16'),140)]:
  for n in pins:p=u(n);d.wire(p,(x,p[1]))
  ys=[u(n)[1] for n in pins];d.wire((x,min(ys)),(x,98));d.label('GND',(x,98),270)
  for y in ys:d.dot((x,y))
 d.text('FSW = GND: 2.5 MHz; DEF = GND',8,122,1.4)

 d.panel('02  5 V SOURCE PRIORITY',20,180,258,85,'Buck-priority power mux  |  5V_BUCK preferred, USB VBUS fallback')
 d.place('U9',128,43);u=lambda n:d.p('U9',n)
 d.place('C25',184,58);d.place('C26',218,45);d.place('R13',83,49);d.place('R14',83,64)
 # Input rail enters VIN1 and priority divider; output joins both VOUT pins above IC.
 p=u('3');d.wire(p,(102,p[1]),(102,28),(58,28));d.label('5V_BUCK',(58,28),180)
 d.wire((83,28),d.p('R13','1'));d.dot((83,28))
 d.wire(d.p('R13','2'),(83,57),d.p('R14','1'));p=u('4');d.wire(p,(102,p[1]),(102,57),(83,57));d.dot((83,57));d.label('PR1',(102,57))
 p=u('5');d.wire(p,(155,p[1]),(155,72));d.label('5V_BUCK',(155,72),270)
 p=u('6');d.wire(p,(184,p[1]),d.p('C25','1'));d.label('VBUS',(184,p[1]))
 for n,x in [('2',110),('7',148)]:
  p=u(n);d.wire(p,(x,p[1]),(x,23))
 d.wire((110,23),(238,23));d.label('5V',(238,23));d.dot((148,23));d.wire((218,23),d.p('C26','1'));d.dot((218,23))
 d.ground('U9','1',dx=-5.08,drop=28);d.ground('C25','2',drop=6.35);d.ground('C26','2',drop=6.35);d.ground('R14','2',drop=2.54)

 d.panel('03  VSYS / MCU 3.3 V',20,271,258,105,'Diode-OR supply -> TPS629210 -> MCU rail; fused DSM supply branch')
 # Flip buck so input is on left and switch output on right.
 d.place('U14',139,56,180);u=lambda n:d.p('U14',n)
 d.place('D5',36,30,180);d.place('D6',36,47,180)
 for r,net in [('D5','VX'),('D6','VBUS')]:
  a=d.p(r,'2');d.wire(a,(15,a[1]));d.label(net,(15,a[1]),180);p=d.p(r,'1');d.wire(p,(61,p[1]))
 d.wire((61,30),(61,47),(79,47),(79,36),(105,36));d.dot((61,47));d.place('C27',79,57);d.wire((79,47),d.p('C27','1'));d.dot((79,47));d.ground('C27','2',drop=8.89);d.label('VSYS',(79,36),90)
 for n in ('6','7'):p=u(n);d.wire(p,(105,p[1]))
 d.wire((105,36),(105,u('7')[1]));d.dot((105,u('6')[1]))
 d.place('R15',102,82);p=u('8');d.wire(p,(112,p[1]),(112,72),(102,72),d.p('R15','1'));d.label('SCONF',(102,72),180);d.ground('R15','2',drop=3.81)
 d.ground('U14','5',dx=-7.62,drop=13.97)
 sw=u('4');d.place('L2',188,sw[1],90);d.wire(sw,d.p('L2','1'));d.label('SW_3V3',(170,sw[1]),90)
 d.place('C28',218,67);d.wire(d.p('L2','2'),(218,sw[1]),d.p('C28','1'));d.label('3V3',(218,sw[1]));d.ground('C28','2',drop=6.35)
 p=u('3');d.wire(p,(207,p[1]),(207,sw[1]));d.dot((207,sw[1]))
 d.place('F2',187,89);d.wire(d.p('F2','1'),(167,d.p('F2','1')[1]));d.label('3V3',(167,d.p('F2','1')[1]),180);d.wire(d.p('F2','2'),(217,d.p('F2','2')[1]));d.label('3V3_DSM',(217,d.p('F2','2')[1]))

 d.panel('04  LOW-NOISE SENSOR SUPPLY',20,382,258,82,'TPS70933: EN pin 3 intentionally floating, supported by internal pull-up')
 d.place('U10',128,41);d.place('C18',70,48);d.place('C19',189,48)
 for n,r,x,net in [('1','C18',46,'VSYS'),('5','C19',220,'3V3_SENS')]:
  p=d.p('U10',n);c=d.p(r,'1');d.wire(p,(x,p[1]));d.wire(c,(c[0],p[1]));d.dot((c[0],p[1]));d.label(net,(x,p[1]),180 if n=='1' else 0);d.ground(r,'2',drop=6.35)
 d.ground('U10','2',dx=-6.35,drop=20.32);d.text('EN and NC are intentionally unconnected. Do not tie EN to VSYS.',8,73,1.4)

 d.panel('05  VOLTAGE MONITORING / POWER FLAGS',20,470,258,85,'ADC divider filters  |  VX_SENSE -> U1.9; 5V_SENSE -> U1.10')
 for a,b,c,x,net in [('R16','R17','C29',40,'VX'),('R18','R19','C30',130,'5V')]:
  d.place(a,x,35);d.place(b,x,57);d.place(c,x+25.4,57);d.wire(d.p(a,'1'),(x,25));d.label(net,(x,25),90)
  mid=(x,46);d.wire(d.p(a,'2'),mid,d.p(b,'1'));d.wire(mid,(x+45.72,46));d.label(d.net(a,'2'),(x+45.72,46));d.dot(mid);d.wire((x+25.4,46),d.p(c,'1'));d.dot((x+25.4,46));d.ground(b,'2',drop=5.08);d.ground(c,'2',drop=5.08)
 for i,net in enumerate(d.design.PWR_FLAGS):d.place(f'#FLG{i+1:02d}',218+i*12.7,44);d.stub(f'#FLG{i+1:02d}','1',5.08)
