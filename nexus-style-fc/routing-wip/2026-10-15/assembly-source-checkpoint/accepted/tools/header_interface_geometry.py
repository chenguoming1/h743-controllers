"""UNFINISHED root-aware header candidate. Dimensions in mm, full routed profiles.
No fit, strength, current, fixture or process approval is implied by this definition.
Use apply_header_interface.py to preserve routed copper; never rebuild a routed board.
"""
from math import sqrt
WIDTH, TOP, CHILD_THICKNESS, MAIN_THICKNESS = 22.4, 8.4, 1.6, 1.6
TAB_LENGTH = 2.6
TABS = ((1.4, 9.8), (12.6, 21.0))
SLOT_CENTERS = ((5.6, 2.4), (16.8, 2.4))
SLOT_LENGTH, SLOT_WIDTH, SLOT_RADIUS, ROOT_RADIUS = 10.1, 2.2, 0.5, 0.5
CONTACT_EDGE = 0.254
MAIN_INNER_Y, MAIN_OUTER_Y = (3.8, 4.65), (0.35, 1.0)
MAIN_OUTER_STRIP_WIDTH = 9.8
CHILD_STRIP_WIDTH = 7.892
# Keep original X bounds using a 0.45 offset for 10.10 length; expand Y to retain 0.30 beyond the 2.20 slot.
SLOT_ROUTE_KEEPOUT_X, SLOT_ROUTE_KEEPOUT_Y = 0.45, 0.3
MODEL_FILE = 'nexus-header-board-root-relief-candidate.wrl'
INNER = ((('3','SBUS'),('4','RPM'),('5','ESC'),('6','TAIL'),('1','VX')),
         (('2','GND'),('7','S3'),('8','S2'),('9','S1')))

def inner_pads_main():
    result = []
    for (a,b), contacts in zip(TABS,INNER):
        widths = [1.6 if net in ('VX','GND') else 1.2 for _,net in contacts]
        gap = (b-a-2*CONTACT_EDGE-sum(widths))/(len(widths)-1)
        x = a + CONTACT_EDGE
        for (num,net),w in zip(contacts,widths):
            result.append((num,net,round(x+w/2,6),w))
            x += w+gap
    return result

def rounded_slot(cx,cy):
    """Ordered closed Edge.Cuts segments: ('line', start,end) / ('arc',start,mid,end)."""
    x0,x1 = cx-SLOT_LENGTH/2,cx+SLOT_LENGTH/2
    y0,y1 = cy-SLOT_WIDTH/2,cy+SLOT_WIDTH/2
    r=SLOT_RADIUS; d=r/sqrt(2)
    return [('line',(x0+r,y0),(x1-r,y0)),
            ('arc',(x1-r,y0),(x1-r+d,y0+r-d),(x1,y0+r)),
            ('line',(x1,y0+r),(x1,y1-r)),
            ('arc',(x1,y1-r),(x1-r+d,y1-r+d),(x1-r,y1)),
            ('line',(x1-r,y1),(x0+r,y1)),
            ('arc',(x0+r,y1),(x0+r-d,y1-r+d),(x0,y1-r)),
            ('line',(x0,y1-r),(x0,y0+r)),
            ('arc',(x0,y0+r),(x0+r-d,y0+r-d),(x0+r,y0))]

def tab_outline():
    """Ordered bottom contour, left to right; upper R0.5 relief semicircles.
    Root contours are open to the exterior and are not detached holes.
    """
    result=[];x=0.;r=ROOT_RADIUS
    for a,b in TABS:
        result += [('line',(x,0),(a-2*r,0)),
                   ('arc',(a-2*r,0),(a-r,-r),(a,0)),
                   ('line',(a,0),(a,TAB_LENGTH)),
                   ('line',(a,TAB_LENGTH),(b,TAB_LENGTH)),
                   ('line',(b,TAB_LENGTH),(b,0)),
                   ('arc',(b,0),(b+r,-r),(b+2*r,0))]
        x=b+2*r
    return result+[('line',(x,0),(WIDTH,0))]

def kicad_shape(shape,prefix='fp',offset=(0,0),uid=None):
    typ,*points=shape
    names=('start','end') if typ=='line' else ('start','mid','end')
    coords=' '.join(f'({key} {x+offset[0]:.6f} {y+offset[1]:.6f})' for key,(x,y) in zip(names,points))
    ident=f' (uuid "{uid}")' if uid else ''
    return f'({prefix}_{typ} {coords} (stroke (width 0.05) (type solid)) (layer "Edge.Cuts"){ident})'
