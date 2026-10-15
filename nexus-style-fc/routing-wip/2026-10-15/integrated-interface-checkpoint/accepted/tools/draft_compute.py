"""Explicit MCU support and sensor circuits; no logical design changes."""
import math
import sexpr as sx


def draw(d):
    d.panel('06  STM32F722 CORE',286,44,258,140,
            'Rotorflight RDMS-NEXUS_F7 pin map; boundary labels connect the functional units')
    inst=d.place('U1',129,77)
    # Keep the original four-sided symbol, but keep its title out of the top fanout.
    for prop in sx.find(inst,'property'):
        name=sx.text(prop[1])
        if name in ('Reference','Value'):
            sx.find(prop,'at')[0][1:]=[*d.xy((48,30 if name=='Reference' else 34)),0]
    for num in d.parts['U1']['pins']:
        if d.net('U1',num) is not None:
            p=d.p('U1',num);angle=int((d.pins['U1',num][1]+180)%360)
            a=math.radians(angle)
            q=(d.snap(p[0]+round(math.cos(a))*5.08),d.snap(p[1]-round(math.sin(a))*5.08))
            d.wire(p,q)
            d.items.append(d.glabel(d.net('U1',num),*d.xy(q),angle,'left' if angle in (0,90) else 'right',d.id('mcu-boundary')))
    d.text('SPI1: inertial sensor   |   SPI2: blackbox   |   I2C1: barometer',8,132,1.5)

    d.panel('07  CLOCK / BOOT / DEBUG',286,190,258,95,
            '8 MHz HSE with load capacitors; BOOT0 button and pull-down; SWD / reset pads')
    d.place('Y1',55,40)
    for ref,x,pin in [('C11',30,'1'),('C12',83,'3')]:
        d.place(ref,x,55)
        p=d.p('Y1',pin)
        d.wire(p,(x,p[1]),d.p(ref,'1'))
        d.label(d.net(ref,'1'),(x,p[1]),180 if ref=='C11' else 0)
        d.ground(ref,'2',drop=6.35)
    # The two grounded crystal case pads are separate from its oscillator terminals.
    p=d.p('Y1','4');d.wire(p,(43,p[1]),(43,27));d.label('GND',(43,27),90)
    d.ground('Y1','2',dx=7.62,drop=21.59)
    d.place('SW1',143,36);d.place('R1',121,55)
    p=d.p('SW1','1');d.wire(p,(121,p[1]),d.p('R1','1'));d.dot((121,p[1]))
    d.wire((121,p[1]),(113,p[1]));d.label('BOOT0',(113,p[1]),180)
    p=d.p('SW1','2');d.wire(p,(p[0],26));d.label('3V3',(p[0],26),90)
    d.ground('R1','2',drop=6.35)
    for ref,x in [('TP1',183),('TP2',211),('TP3',239)]:
        d.place(ref,x,35);d.stub(ref,'1',7.62)
    d.place('TP4',173,69);d.ground('TP4','1',drop=7.62)
    d.place('TP5',195,61);d.place('C10',223,69)
    p=d.p('TP5','1');d.wire(p,(p[0],61),(223,61),d.p('C10','1'))
    d.label('NRST',(223,61));d.ground('C10','2',drop=6.35)
    d.text('Crystal case pads -> GND',15,81,1.4)
    d.text('Press BOOT during reset for DFU',108,86,1.4)

    d.panel('08  MCU DECOUPLING',286,291,258,79,
            'Local 3V3 bypass: C1-4 VDD, C5 bulk, C6-7 VDDA, C8 VBAT; C9 VCAP only')
    # One explicit supply spine, short individual ground branches, independent VCAP.
    xs=[16+i*25.4 for i in range(8)]
    for ref,x in zip(['C1','C2','C3','C4','C5','C6','C7','C8'],xs):
        d.place(ref,x,44);d.wire(d.p(ref,'1'),(x,29));d.ground(ref,'2',drop=6.35)
    d.wire((xs[0],29),(xs[-1],29));d.label('3V3',(xs[0],29),90)
    for x in xs[1:-1]:d.dot((x,29))
    d.place('C9',232,44);d.wire(d.p('C9','1'),(232,29));d.label('VCAP',(232,29),90);d.ground('C9','2',drop=6.35)
    d.text('VDD pins 19 / 32 / 48 / 64',8,69,1.4)
    d.text('VDDA pin 13 / VBAT pin 1',117,69,1.4)
    d.text('VCAP pin 30',218,69,1.3)

    d.panel('09  SPI1 INERTIAL SENSOR',286,376,258,85,
            'ICM-42688-P; IMU_CS pull-up maintains SPI mode at startup; IMU_INT -> U1.50')
    d.place('U2',104,48);u=lambda n:d.p('U2',n)
    for n in ('1','4','13','14'):d.stub('U2',n,7.62)
    # Compact grouped ground connections on each side, without crossing signal leads.
    for pins,x in [(('2','3'),64),(('6','7'),64),(('10','11'),145)]:
        pp=[u(n) for n in pins]
        for p in pp:d.wire(p,(x,p[1]))
        d.wire((x,min(p[1] for p in pp)),(x,max(p[1] for p in pp)))
        if pins==('2','3'):
            d.label('GND',(x,min(p[1] for p in pp)),180)
        elif pins==('10','11'):
            d.label('GND',(x,max(p[1] for p in pp)),0)
        else:
            bottom=(x,73);d.wire((x,max(p[1] for p in pp)),bottom);d.label('GND',bottom,270)
    # VDDIO has its own nearby bypass; VDD and CS pull-up share the top rail.
    d.place('C15',30,62);p=u('5');d.wire(p,(30,p[1]),d.p('C15','1'));d.label('3V3_SENS',(30,p[1]),180);d.ground('C15','2',drop=6.35)
    d.place('R5',179,34,180);p=u('12');d.wire(p,(179,p[1]),d.p('R5','1'));d.label('IMU_CS',(157,p[1]))
    p=d.p('R5','2');d.wire(p,(179,24),(239,24));d.label('3V3_SENS',(239,24))
    p=u('8');d.wire(p,(184,p[1]),(184,24));d.dot((184,24))
    for ref,x in [('C13',195),('C14',224)]:
        d.place(ref,x,57);d.wire(d.p(ref,'1'),(x,24));d.dot((x,24));d.ground(ref,'2',drop=9)

    d.panel('10  I2C1 PRESSURE SENSOR',286,467,258,88,
            'DPS368 address 0x76: SDO low; CSB high selects I2C; local SCL / SDA pull-ups')
    d.place('U3',125,49);u=lambda n:d.p('U3',n)
    # SDA/SCL enter from the left with independent, explicitly connected pull-ups.
    for ref,x,n in [('R6',35,'4'),('R7',72,'3')]:
        d.place(ref,x,38,180);p=u(n)
        d.wire(p,(13,p[1]));d.label(d.net('U3',n),(13,p[1]),180)
        d.wire(d.p(ref,'1'),(x,p[1]));d.dot((x,p[1]))
        d.wire(d.p(ref,'2'),(x,26))
    d.wire((35,26),(103,26));d.dot((72,26));d.label('3V3_SENS',(35,26),90)
    p=u('2');d.wire(p,(103,p[1]),(103,26))
    # Ground pins remain short and avoid crossing the I2C and mode-select branches.
    p=u('1');d.wire(p,(109,p[1]),(109,36));d.label('GND',(109,36),90)
    p=u('5');d.wire(p,(145,p[1]),(145,72));d.label('GND',(145,72),270)
    p=u('7');d.wire(p,(143,p[1]));d.label('GND',(143,p[1]))
    for n in ('6','8'):
        p=u(n);d.wire(p,(161,p[1]))
    d.wire((161,u('6')[1]),(161,26),(236,26));d.label('3V3_SENS',(236,26))
    d.dot((161,u('8')[1]))
    for ref,x in [('C16',189),('C17',222)]:
        d.place(ref,x,50);d.wire(d.p(ref,'1'),(x,26));d.dot((x,26));d.ground(ref,'2',drop=8.89)
    d.text('CSB = VDDIO; SDO = GND',12,78,1.4)
