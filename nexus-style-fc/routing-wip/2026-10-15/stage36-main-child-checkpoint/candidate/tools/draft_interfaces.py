"""Deliberately wired external interfaces, preserving the source pin/net map."""
def draw(d):
    s=d.snap
    def link(a,b,x=None):
        if a[0]==b[0] or a[1]==b[1]: d.wire(a,b)
        else:
            x=s((a[0]+b[0])/2) if x is None else s(x)
            d.wire(a,(x,a[1]),(x,b[1]),b)
    def local(ref,pin,x,y,angle=0):
        p=d.p(ref,pin); q=(s(x),s(y)); link(p,q); d.label(d.net(ref,str(pin)),q,angle)
    def clamp_power(ref):
        # Supplies leave the package beside the signal paths, then turn vertically.
        p=d.p(ref,2); q=(s(p[0]-5.08),p[1]); d.wire(p,q,(q[0],s(q[1]+7.62))); d.label('GND',(q[0],s(q[1]+7.62)),270)
        p=d.p(ref,5); q=(s(p[0]+5.08),p[1]); d.wire(p,q,(q[0],s(q[1]-5.08))); d.label('5V',(q[0],s(q[1]-5.08)),90)
    def socket(ref,x,y,rot):
        d.place(ref,x,y,rot)
        # The mechanical tabs have their own short, explicit ground branches.
        for pin in (5,6):
            if d.p(ref,pin)[1] > y:d.ground(ref,pin,drop=5.08)
            else:
                p=d.p(ref,pin);outer=s(x-22.86 if rot==90 else x+22.86);top=s(p[1]-5.08);bottom=s(p[1]+2.54)
                d.wire(p,(p[0],top),(outer,top),(outer,bottom));d.label('GND',(outer,bottom),270)
        p=d.p(ref,1)
        if rot==90:
            x1=s(x+19.05);x2=s(x+27.94);top=s(y-17.78);bottom=s(y-12.7)
            d.wire(p,(x1,p[1]),(x1,top),(x2,top),(x2,bottom));d.label('GND',(x2,bottom),270)
        else:d.ground(ref,1,dx=-5.08,drop=7.62)
        d.stub(ref,2,10.16)
    def signal(ref,pin,ic,ip,x):
        a=d.p(ref,pin);b=d.p(ic,ip);link(a,b,x)
        q=(s(x),b[1]);d.dot(q);d.label(d.net(ic,str(ip)),q,90)

    d.panel('11  USB-C / PROTECTION',552,44,269,105,'USB 2.0 device  |  CC pull-downs: 5.1k  |  F1: VBUS resettable fuse')
    d.place('J6',56,53);d.place('U7',177,65);d.place('F1',177,32)
    d.place('R20',27,71);d.place('R21',100,71)
    for pin,r in [('A5','R20'),('B5','R21')]:
        a=d.p('J6',pin);b=d.p(r,1);d.wire(a,(b[0],a[1]),b);d.label(d.net(r,'1'),(b[0],a[1]),90);d.ground(r,2,drop=6.35)
    # The mirrored connector contacts are the same two USB nets.
    for pin in ('A6','A7'): d.stub('J6',pin,6.35)
    signal('J6','B7','U7',1,125)
    signal('J6','B6','U7',3,139)
    d.stub('U7',6,17.78);d.stub('U7',4,17.78);d.ground('U7',2,dx=-7.62,drop=24.13)
    a=d.p('F1',2);b=d.p('U7',5);q=(s(218),a[1]);d.wire(a,q,(q[0],b[1]),b);d.label('VBUS',q);d.dot(q)
    # One connector-side VBUS rail feeds the fuse; the duplicate contacts join locally.
    top=s(24)
    for pins,x in [(('A4','A9'),37),(('B4','B9'),78)]:
        x=s(x)
        for pin in pins:
            p=d.p('J6',pin);d.wire(p,(x,p[1]));d.dot((x,p[1]))
        low=d.p('J6',pins[-1])[1];d.wire((x,low),(x,top))
    a=d.p('F1',1);d.wire((s(37),top),(a[0],top),a);d.dot((s(78),top));d.label('VBUS_C',(s(120),top))
    for pin in ('A1','A12','B1','B12'):d.stub('J6',pin,5.08)
    d.ground('J6','EP',drop=16.51)

    d.panel('12  RECEIVER INTERFACES',552,155,269,145,'A: UART4 / CRSF  |  B: UART6  |  C: UART3  |  DSM: UART1')
    socket('J3',38,42,90);socket('J5',230,42,270);d.place('U13',134,42)
    signal('J3',3,'U13',1,83);signal('J3',4,'U13',3,96)
    signal('J5',3,'U13',4,185);signal('J5',4,'U13',6,198)
    clamp_power('U13')
    socket('J4',38,111,90);d.place('U15',134,111);d.place('J2',237,110)
    signal('J4',3,'U15',1,83);signal('J4',4,'U15',3,96);clamp_power('U15')
    # DSM is a one-wire interface; R22 joins the MCU transmit path at the port.
    d.place('R22',193,113,90)
    a=d.p('U15',4);b=d.p('J2',3);link(a,b,220)
    r=d.p('R22',2);tap=(s(220),r[1]);d.wire(r,tap);d.dot(tap)
    d.stub('R22',1,7.62);d.label('DSM_DATA',(s(220),b[1]),90)
    d.stub('J2',1,7.62);d.ground('J2',2,dx=-5.08,drop=20.32)
    d.ground('J2',4,drop=7.62)
    p=d.p('J2',5);q=(s(p[0]+12.7),p[1]);d.wire(p,q,(q[0],s(130)));d.label('GND',(q[0],s(130)),270)

    d.panel('13  SERVO HEADER / SIGNAL CLAMPS',552,306,269,90,'J1 connects the separate header board; VX / GND enter at pins 1 / 2')
    d.place('J1',33,49,180);d.place('U11',123,48);d.place('U12',224,48)
    signal('J1',3,'U11',1,72);signal('J1',4,'U11',3,84)
    d.stub('J1',1,7.62);d.ground('J1',2,dx=20.32,drop=15.24)
    # Fan out the remaining header signals around the protection packages.
    for jp,ref,ip,x1,y,x2 in [(9,'U12',4,50,23,253),(8,'U12',3,55,26,191),(7,'U12',1,60,29,199),(6,'U11',6,65,31,156),(5,'U11',4,65,78,163)]:
        a=d.p('J1',jp);b=d.p(ref,ip);x1,x2,y=s(x1),s(x2),s(y)
        d.wire(a,(x1,a[1]),(x1,y),(x2,y),(x2,b[1]),b)
        d.label(d.net(ref,str(ip)),(x2,b[1]),90)
    for ref in ('U11','U12'):
        clamp_power(ref)

    d.panel('14  SPI2 BLACKBOX',552,402,269,76,'W25N01GV 128 MB  |  /CS, /WP, /HOLD pull-ups  |  EP intentionally floating')
    d.place('U4',130,46);d.place('C20',230,49)
    d.place('R8',75,33,180);d.place('R9',50,44,180);d.place('R10',184,33,180)
    rail=s(23)
    for ref,pin in [('R8',2),('R9',2),('R10',2),('C20',1)]:
        p=d.p(ref,pin);d.wire(p,(p[0],rail));d.dot((p[0],rail))
    left=d.p('R9',2)[0];right=d.p('C20',1)[0];d.wire((left,rail),(right,rail));d.label('3V3',(right,rail))
    for r,pin,x in [('R8',1,90),('R9',3,96),('R10',7,174)]:
        a=d.p(r,1);b=d.p('U4',pin);link(a,b,x)
        if pin!=1:d.label(d.net(r,'1'),(s(x),b[1]),90)
    # Chip select also continues to the MCU; WP and HOLD stay local.
    p=d.p('U4',1);q=(s(90),p[1]);d.dot(q);d.label('FLASH_CS',q,90)
    d.stub('U4',2,7.62);d.stub('U4',5,25.4);d.stub('U4',6,25.4)
    p=d.p('U4',8);q=(s(210),p[1]);d.wire(p,q,(q[0],rail));d.dot((q[0],rail))
    d.ground('U4',4,dx=-7.62,drop=12.7);d.ground('C20',2,drop=7.62)

    d.panel('15  STATUS INDICATION',552,484,269,61,'PC14 / PC15 sink current: active low  |  Blue indicates 5 V bus power')
    for r,led,x in [('R2','D1',34),('R3','D2',121),('R4','D3',208)]:
        d.place(r,x,38,90);d.place(led,x+26,40.64,180)
        link(d.p(r,2),d.p(led,2));d.label(d.net(r,'2'),d.p(r,2),90);d.stub(r,1,8.89)
        if led=='D3':d.ground(led,1,drop=7.62)
        else:d.stub(led,1,10.16)
    # Keep protection IC captions clear of the upper signal-routing corridors.
    import sexpr as sx
    for item in d.items:
        if not isinstance(item,list) or item[0] != 'symbol': continue
        props={sx.text(p[1]):p for p in sx.find(item,'property')}
        if props.get('Reference') and sx.text(props['Reference'][2]) in ('U11','U12'):
            for key,y in [('Reference',379.0),('Value',382.0)]:
                a=sx.find(props[key],'at')[0];a[2]=d.snap(y)
