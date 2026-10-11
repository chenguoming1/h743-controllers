"""Small synthetic controls; no recovered board or router is loaded."""
from shapely.geometry import Point, box
from native7_positive_contact_partition_v1 import partition

def item(name,shape,layer='F.Cu'):
    return ({'uuid':name,'net':'N','kind':'track'},{layer:shape},{},None)
# Historical intersects would join these tangent edges; positive-area must not.
assert len(partition([item('a',box(0,0,1,1)),item('b',box(1,0,2,1))],'N',['F.Cu'])[0])==2
assert len(partition([item('a',box(0,0,1,1)),item('b',box(.9,0,2,1))],'N',['F.Cu'])[0])==1
# A hole removes apparent copper contact at the center.
hole=Point(0,0).buffer(.2)
via=({'uuid':'v','net':'N','kind':'via','barrel_layers':['F.Cu','B.Cu']},{'F.Cu':Point(0,0).buffer(.5),'B.Cu':Point(0,0).buffer(.5)},{},hole)
inside=item('inside',box(-.05,-.05,.05,.05))
groups,members=partition([via,inside],'N',['F.Cu','B.Cu'])
assert 'inside' not in members
assert len(groups)==1
# Declared plated annuli connect real F/B material; a remote same-record island
# cannot inherit the barrel's vertical connection.
from shapely import unary_union
island=box(2,2,3,3)
via2=(via[0],dict(via[1],**{'F.Cu':unary_union([via[1]['F.Cu'],island])}),{},hole)
assert len(partition([via2],'N',['F.Cu','B.Cu'])[0])==2
print('5 positive-area/drill/barrel synthetic controls passed')
