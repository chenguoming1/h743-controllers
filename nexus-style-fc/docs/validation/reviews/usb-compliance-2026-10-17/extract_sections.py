"""Read-only native copper cross-section extraction at selected straight USB runs.

Horizontal intervals sampled at 0.005 mm with transition bisection to <0.1 um.
This is geometry, not a 3D electromagnetic representation of crossing traces.
"""
import hashlib
import sys
import json
from pathlib import Path
import pcbnew as k

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
SRC = Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'hardware/nexus-style-fc.kicad_pcb'
before = hashlib.sha256(SRC.read_bytes()).hexdigest()
b = k.LoadBoard(str(SRC))
sections = []
for y, cx in [(116.,110.5),(118.1,110.5),(120.2,110.5),(113.4,110.75),(123.4,109.65)]:
    section = dict(y_mm=y, center_x_mm=cx, halfspan_mm=2.5, copper={})
    for layer in b.GetEnabledLayers().CuStack():
        predicates = {}
        for z in b.Zones():
            if z.IsOnLayer(layer) and z.GetNetname():
                poly = z.GetFilledPolysList(layer)
                predicates.setdefault(z.GetNetname(),[]).append(lambda q, poly=poly: poly.Contains(q))
        items = list(b.GetTracks()) + [p for f in b.GetFootprints() for p in f.Pads()] + list(b.GetDrawings())
        for item in items:
            if not item.IsOnLayer(layer) or not hasattr(item,'GetNetname') or not item.GetNetname():
                continue
            bb = item.GetBoundingBox()
            if not bb.GetTop() <= round(y*1e6) <= bb.GetBottom():
                continue
            shape = item.GetEffectiveShape(layer)
            predicates.setdefault(item.GetNetname(),[]).append(lambda q, shape=shape: shape.Collide(q,0))
        rows = {}
        for net, tests in predicates.items():
            def inside(x):
                q=k.VECTOR2I(round((x+cx)*1e6),round(y*1e6))
                return any(test(q) for test in tests)
            xs=[-2.5+i*.005 for i in range(1001)]
            flags=[inside(x) for x in xs]; intervals=[]; start=xs[0] if flags[0] else None
            for i in range(1,len(xs)):
                if flags[i]==flags[i-1]:continue
                lo,hi=xs[i-1:i+1]
                for _ in range(17):
                    mid=(lo+hi)/2
                    if inside(mid)==flags[i-1]:lo=mid
                    else:hi=mid
                edge=(lo+hi)/2
                if flags[i]:start=edge
                else:intervals.append([start,edge]);start=None
            if start is not None:intervals.append([start,xs[-1]])
            if intervals:rows[net]=intervals
        section['copper'][b.GetLayerName(layer)]=rows
    sections.append(section)
assert hashlib.sha256(SRC.read_bytes()).hexdigest()==before
result=dict(source=str(SRC),sha256=before,native_version=k.GetBuildVersion(),method=__doc__,sections=sections)
(OUT/'sections.json').write_text(json.dumps(result,indent=2))
for s in sections:
    print('y',s['y_mm'],'In3',s['copper']['In3.Cu'],'In2',s['copper']['In2.Cu'])
