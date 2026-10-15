"""Deterministic main-board presentation. No connectivity or PCB placement changes.

Keep the original single-sheet instance paths and all symbol/pin UUIDs. Electrical
intent lives in design.py; these coordinates affect only the schematic drawing.
"""
import copy
import math
import sexpr as sx


def arrange(sch, design, project):
    from gen_schematic import uid, snap, S, glabel
    parts = {p['ref']: p for p in design.PARTS}
    defs = {sx.text(n[1]): n for n in sx.find(sch, 'lib_symbols')[0][1:]}
    originals = {sx.text(sx.find(n, 'property')[0][2]): n for n in sx.find(sch, 'symbol')}
    items, placed = [], set()

    def text(t,x,y,size=1.5,bold=False):
        f=['font',['size',size,size]]
        if bold: f.append(['bold','yes'])
        items.append(['text',S(t),['exclude_from_sim','no'],['at',snap(x),snap(y),0],['effects',f,['justify','left']],['uuid',uid(project,'readable-text',t,x,y)]])

    def wire(a,b,key):
        if a==b: return
        items.append(['wire',['pts',['xy',*a],['xy',*b]],['stroke',['width',0],['type','default']],['uuid',uid(project,'readable-wire',key)]])

    def label(net,x,y,key,angle=0):
        items.append(glabel(net,snap(x),snap(y),angle,'left' if angle in (0,90) else 'right',uid(project,'readable-label',key)))

    def dot(x,y,key):
        items.append(['junction',['at',snap(x),snap(y)],['diameter',0],['color',0,0,0,0],['uuid',uid(project,'readable-dot',key)]])

    def panel(title,x,y,w,h,note):
        items.append(['polyline',['pts',['xy',x,y],['xy',x+w,y],['xy',x+w,y+h],['xy',x,y+h],['xy',x,y]],['stroke',['width',0.254],['type','default']],['fill',['type','none']],['uuid',uid(project,'panel',title)]])
        text(title,x+5,y+6,2.2,True)
        text(note,x+5,y+12,1.4)

    def place(ref,x,y,omit=(),rotation=0):
        assert ref not in placed, ref
        placed.add(ref)
        p=parts.get(ref)
        inst=copy.deepcopy(originals[ref]); at=sx.find(inst,'at')[0]; ox,oy=float(at[1]),float(at[2]); x,y=snap(x),snap(y)
        at[1:]=[x,y,rotation]
        lib=sx.text(sx.find(inst,'lib_id')[0][1]); sym=defs[lib]
        xa,ya,xb,yb=sx.symbol_bbox(sym)
        passive=ref.startswith(('R','C','L')) and len(sx.symbol_pins(sym))==2
        for prop in sx.find(inst,'property'):
            pa=sx.find(prop,'at')[0]; pa[1:]=[x,y,0]
            name=sx.text(prop[1])
            if name in ('Reference','Value'):
                if passive and not rotation:
                    pa[1:]=[snap(x+4),snap(y+(-1.27 if name=='Reference' else 1.27)),0]
                    eff=sx.find(prop,'effects')[0]
                    eff[:]=[v for v in eff if not isinstance(v,list) or v[0]!='justify']
                    eff.append(['justify','left'])
                else:
                    pa[1:]=[x,snap(y-yb-(6 if name=='Reference' else 3.5)),0]
                    if rotation:
                        pa[1:]=[x,snap(y-(7 if name=='Reference' else 4)),rotation]
                    if ref == 'J2':
                        pa[1:]=[snap(x-12.7),snap(179 if name=='Reference' else 183),0]
                    if ref == 'U1':
                        pa[1:]=[x,snap(65 if name=='Reference' else 69),0]
        items.append(inst)
        pins={}
        for num,(px,py,ang,length,name) in sx.symbol_pins(sym).items():
            r=math.radians(rotation); rx=px*math.cos(r)-py*math.sin(r); ry=px*math.sin(r)+py*math.cos(r)
            ex,ey=snap(x+rx),snap(y-ry); pins[num]=(ex,ey); ang+=rotation
            if num in omit: continue
            net=p['pins'][num] if p else next(n for i,n in enumerate(design.PWR_FLAGS) if ref==f'#FLG{i+1:02d}')
            if net is None:
                items.append(['no_connect',['at',ex,ey],['uuid',uid(project,'nc',ref,num)]])
                continue
            a=math.radians(ang+180); dx,dy=round(math.cos(a)),-round(math.sin(a))
            lx,ly=snap(ex+dx*3.81),snap(ey+dy*3.81)
            wire((ex,ey),(lx,ly),(ref,num))
            # Horizontal labels on passive branches avoid the original rotated text.
            if passive:
                wire((lx,ly),(snap(lx-3.81),ly),(ref,num,'bend'))
                label(net,lx-3.81,ly,(ref,num),180)
            else:
                angle=0 if dx>0 else 180 if dx<0 else 90 if dy<0 else 270
                label(net,lx,ly,(ref,num),angle)
        return pins

    def bank(refs,x,y,spacing=23):
        """Parallel passives, with explicitly wired shared top/bottom rails."""
        assert len({tuple(parts[r]['pins'].values()) for r in refs})==1
        pp=[place(r,x+i*spacing,y,('1','2')) for i,r in enumerate(refs)]
        for pin,rail in [('1',snap(y-10.16)),('2',snap(y+10.16))]:
            net=parts[refs[0]]['pins'][pin]
            points=[(p[pin][0],rail) for p in pp]
            for i,(p,point) in enumerate(zip(pp,points)):
                wire(p[pin],point,('bank',refs[i],pin))
                if 0<i<len(pp)-1: dot(*point,('bank',refs[i],pin))
            start=(snap(points[0][0]-6.35),rail)
            wire(start,points[0],('rail-start',refs[0],pin))
            for i in range(len(points)-1): wire(points[i],points[i+1],('rail',refs[i],pin))
            if len(points)>1: dot(*points[0],('bank-first',refs[0],pin))
            label(net,*start,('bank',refs[0],pin),180)

    def divider(top,bottom,cap,x,y):
        a=place(top,x,y-10.16,('2',)); b=place(bottom,x,y+10.16,('1',))
        middle=(snap(x),snap(y)); wire(a['2'],middle,(top,'mid')); wire(middle,b['1'],(bottom,'mid'))
        net=parts[top]['pins']['2']; assert parts[bottom]['pins']['1']==net
        end=(snap(x+25.4),snap(y)); wire(middle,end,(top,'tap')); dot(*middle,(top,'tap')); label(net,*end,(top,'tap'))
        if cap:
            c=place(cap,x+15.24,y+10.16,('1',)); tap=(snap(x+15.24),snap(y)); wire(tap,c['1'],(cap,'tap')); dot(*tap,(cap,'tap'))

    # A three-column reading order: power -> compute/sensing -> external interfaces.
    text('NEXUS-STYLE FLIGHT CONTROLLER  |  FUNCTIONAL SCHEMATIC',20,20,3,True)
    text('Read left to right: POWER  /  MCU + SENSORS  /  INTERFACES. Matching global labels connect across panels.',20,28,1.8)
    text('UNFINISHED PCB CHECKPOINT - NOT RELEASED FOR FABRICATION. X = intentionally unconnected pin.',20,35,1.6)
    panel('01  VX INPUT / 5 V BUCK',20,44,258,130,'VX -> U5 / L1 -> 5V_BUCK; feedback R11 / R12 sets about 5.16 V')
    u=place('U5',75,105,('1','2','3')); place('D4',167,157)
    bank(['C21','C22'],35,75)
    place('C23',35,143)
    l=place('L1',145,u['1'][1],('1','2'),rotation=90)
    c=place('C24',181,121,('1','2')); r1=place('R11',231,110,('1','2')); r2=place('R12',231,137,('1','2'))
    for pin in ('1','2','3'):
        corner=(snap(105),u[pin][1]); wire(u[pin],corner,('buck-sw',pin))
    wire((snap(105),u['1'][1]),(snap(105),u['2'][1]),'buck-sw-join1'); wire((snap(105),u['2'][1]),(snap(105),u['3'][1]),'buck-sw-join2')
    dot(105,u['2'][1],'buck-sw-join'); dot(105,u['1'][1],'buck-sw-top')
    wire((snap(105),u['1'][1]),l['1'],'buck-sw-L'); label('SW_5V',105,u['1'][1],'buck-sw',90)
    rail=u['1'][1]
    for start,end,key in [(l['2'],(c['1'][0],rail),'out1'),((c['1'][0],rail),(r1['1'][0],rail),'out2'),((r1['1'][0],rail),r1['1'],'out3'),((c['1'][0],rail),c['1'],'cap')]: wire(start,end,('buck',key))
    dot(c['1'][0],rail,'buck-out-cap'); label('5V_BUCK',r1['1'][0],rail,'buck-out')
    mid=(r1['2'][0],snap(123)); wire(r1['2'],mid,'buck-fb1'); wire(mid,r2['1'],'buck-fb2'); wire(mid,(snap(252),mid[1]),'buck-fb-tap'); dot(*mid,'buck-fb'); label('FB_5V',252,mid[1],'buck-fb')
    gnd=snap(151); wire(c['2'],(c['2'][0],gnd),'buck-gnd1'); wire(r2['2'],(r2['2'][0],gnd),'buck-gnd2'); wire((c['2'][0],gnd),(r2['2'][0],gnd),'buck-gnd3'); label('GND',r2['2'][0],gnd,'buck-gnd')
    panel('02  5 V SOURCE PRIORITY',20,180,258,85,'5V_BUCK is preferred; USB VBUS supplies 5V when the buck is absent')
    place('U9',72,222); divider('R13','R14',None,144,225)
    place('C25',205,225); place('C26',252,225)
    panel('03  VSYS / MCU 3.3 V',20,271,258,105,'VX / VBUS diode-OR -> VSYS -> U14 / L2 -> 3V3; F2 limits the DSM port')
    place('D5',57,309); place('D6',57,350); place('U14',133,319)
    place('C27',207,310); place('R15',246,310); place('L2',122,354); place('C28',170,354); place('F2',235,353)
    panel('04  LOW-NOISE SENSOR SUPPLY',20,382,258,82,'VSYS -> U10 -> 3V3_SENS. EN pin 3 intentionally floating (internal pull-up).')
    u=place('U10',132,425,('1','2','5')); ci=place('C18',65,433,('1','2')); co=place('C19',210,433,('1','2'))
    for pin,c,r in [('1',ci,'C18'),('5',co,'C19')]:
        rail=(c['1'][0],u[pin][1]); wire(u[pin],rail,('ldo',pin)); wire(rail,c['1'],('ldo',r,'in'))
        label(parts['U10']['pins'][pin],*rail,('ldo',pin),180 if pin=='1' else 0)
        bottom=(c['2'][0],snap(445)); wire(c['2'],bottom,('ldo',r,'gnd'))
    ground=(snap(105),snap(445)); bend=(ground[0],u['2'][1])
    wire(u['2'],bend,('ldo','ground1')); wire(bend,ground,('ldo','ground2'))
    wire((ci['2'][0],ground[1]),ground,('ldo','ground3')); wire(ground,(co['2'][0],ground[1]),('ldo','ground4')); dot(*ground,('ldo','ground')); label('GND',ci['2'][0],ground[1],('ldo','ground'),180)
    text('Do not tie EN to VSYS. Pin 4 is also intentionally unconnected.',28,454,1.5)
    panel('05  VOLTAGE MONITORING / POWER FLAGS',20,470,258,85,'ADC input dividers: VX_SENSE -> U1.9; 5V_SENSE -> U1.10')
    divider('R16','R17','C29',61,517); divider('R18','R19','C30',151,517)
    for i,n in enumerate(design.PWR_FLAGS): place(f'#FLG{i+1:02d}',230+i*14,520)

    panel('06  STM32F722 CORE',286,44,258,140,'Rotorflight RDMS-NEXUS_F7 pin map; named interfaces continue in panels 09-15')
    place('U1',416,119)
    text('SPI1: IMU   |   SPI2: blackbox   |   I2C1: barometer',294,174,1.6)
    panel('07  CLOCK / BOOT / DEBUG',286,190,258,95,'8 MHz HSE; BOOT selects DFU. SWD pads are for bring-up and debug.')
    place('Y1',325,230); bank(['C11'],379,232); bank(['C12'],433,232)
    place('SW1',500,224); place('R1',494,263); place('C10',444,263)
    for i in range(5): place('TP'+str(i+1),304+i*25,265)
    panel('08  MCU DECOUPLING',286,291,258,79,'C1-4: VDD; C5: bulk; C6-7: VDDA; C8: VBAT; C9: VCAP')
    bank(['C1','C2','C3','C4','C5','C6','C7','C8'],307,334,25.4)
    bank(['C9'],520,334)
    panel('09  SPI1 INERTIAL SENSOR',286,376,258,85,'ICM-42688-P: IMU_CS / SPI1; IMU_INT -> U1.50; powered by 3V3_SENS')
    place('U2',357,423); bank(['C13','C14','C15'],438,425,25.4); place('R5',519,425)
    panel('10  I2C1 PRESSURE SENSOR',286,467,258,88,'DPS368: address 0x76; CSB high selects I2C; R6 / R7 pull up SCL / SDA')
    place('U3',331,516); bank(['C16','C17'],388,518); place('R6',458,518); place('R7',509,518)

    panel('11  USB-C / PROTECTION',552,44,269,105,'USB 2.0 device; CC1 / CC2 Rd = 5.1k; F1 protects VBUS')
    place('J6',600,99); place('U7',680,102); place('F1',767,83)
    place('R20',743,123); place('R21',791,123)
    panel('12  RECEIVER INTERFACES',552,155,269,145,'A = UART4 (CRSF); B = UART6; C = UART3; DSM = UART1')
    place('J3',590,199); place('J5',656,199); place('J4',722,199); place('J2',787,202)
    place('U13',604,265); place('U15',701,265); place('R22',780,265)
    panel('13  SERVO HEADER / SIGNAL CLAMPS',552,306,269,90,'J1 mates with the separate header board; VX and GND enter at pins 1 / 2')
    place('J1',594,358); place('U11',672,355); place('U12',772,355)
    panel('14  SPI2 BLACKBOX',552,402,269,76,'W25N01GV 128 MB; /CS, /WP and /HOLD pull-ups; EP intentionally floating')
    place('U4',608,447); bank(['C20'],666,449); place('R8',709,449); place('R9',753,449); place('R10',800,449)
    panel('15  STATUS INDICATION',552,484,269,61,'PC14 / PC15 sink only: active low, about 1.3 mA. Blue = 5 V bus present.')
    for r,d,x in [('R2','D1',590),('R3','D2',677),('R4','D3',764)]:
        place(r,x-15,529); place(d,x+24,530)

    assert placed==set(originals), (set(originals)-placed,placed-set(originals))
    keep=[n for n in sch if not isinstance(n,list) or n[0] not in ('symbol','wire','global_label','no_connect','text','junction','polyline')]
    # Preserve title block, root UUID and all instance paths.
    return keep+items
