"""Synthetic exact-grid proposal tests; no PCB or routing graph is loaded."""
import time
from types import SimpleNamespace
from shapely.geometry import box
import native7_joint_routing_helpers_v3 as routing

routing.require_native_grid([[.3,.5],[1,1]])
try:
    routing.require_native_grid([[.1+.2,.5]])
except routing.JointRoutingFailure:
    pass
else:
    raise AssertionError('Off-grid proposal accepted')

def run(component,bend):
    finite=[]
    def check(net,layer,points,**kwargs):
        finite.append(points)
        return [{'pass_with_polygon_error':True}]
    g=SimpleNamespace(rt=SimpleNamespace(domain=lambda *args,**kwargs:(component,[],[]),
                       component=lambda shape,point:shape),
                      s=SimpleNamespace(paths2=lambda a,b:iter([[a,bend,b]])),
                      check_track=check,
                      track=lambda net,layer,points,name,width:({'uuid':name},{},{},None))
    router=routing.Router(g,[],time.monotonic()+5)
    try:
        router.layer_route('N','F.Cu',[0,0],[.1,.2],'test')
        return router,finite,None
    except routing.JointRoutingFailure as e:
        return router,finite,e

r,finite,error=run(box(-1,-1,.4,1),[.1+.2,.1])
assert error is None and finite[0][1]==[.3,.1] and r.routes[0]['points']==finite[0]
r,finite,error=run(box(-1,-1,.29999999,1),[.29999996,.1])
assert error is not None and not finite and not r.routes
print('4 native-grid and original-domain controls passed')
