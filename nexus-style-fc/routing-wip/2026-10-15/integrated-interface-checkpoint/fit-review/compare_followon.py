"""Read-only full footprint/edge/slot-keepout equality gate for follow-on copper trials."""
import sys,json,hashlib
from pathlib import Path
ROOT=Path('/workspace/scratch/8a35c1f26232');P=ROOT/'nexus-recovery-20261015/mechanical-integration/main-dsm-slot-03';Q=Path(sys.argv[1]);OUT=Path(__file__).parent
sys.path.insert(0,str(P/'tools'));import sexpr as s
files=['hardware/nexus-style-fc.kicad_pcb','hardware/header-board/nexus-header-board.kicad_pcb','hardware/library/NexusFC.3dshapes/nexus-header-board-root-relief-candidate.wrl']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(fp):return next(s.text(v[2]) for v in s.find(fp,'property') if s.text(v[1])=='Reference')
def norm(o):
 if isinstance(o,tuple):return o[1]
 if isinstance(o,list):return [norm(x) for x in o]
 try:return round(float(o),6)
 except(ValueError,TypeError):return o
def records(b):
 return {'footprints':{ref(fp):norm(fp) for fp in s.find(b,'footprint')},'edge':sorted([norm(n) for n in b if isinstance(n,list) and n and n[0] in ['gr_line','gr_arc'] and s.find(n,'layer') and s.text(s.find(n,'layer')[0][1])=='Edge.Cuts'],key=str),'keepout':sorted([norm(n) for n in s.find(b,'zone') if s.find(n,'keepout')],key=str),'general':norm(s.find(b,'general'))}
hashes={role:{f:sha(base/f) for f in files} for role,base in [('reviewed',P),('followon',Q)]};result={'followon_path':str(Q),'sha256':hashes,'comparison':{}}
for f in files[:2]:
 a,b=(records(s.parse((base/f).read_text())) for base in [P,Q]);result['comparison'][f]={k:a[k]==b[k] for k in a};result['comparison'][f]['footprint_differences']=[r for r in set(a['footprints'])|set(b['footprints']) if a['footprints'].get(r)!=b['footprints'].get(r)]
result['model_unchanged']=hashes['reviewed'][files[2]]==hashes['followon'][files[2]]
assert hashes=={role:{f:sha(base/f) for f in files} for role,base in [('reviewed',P),('followon',Q)]}
(OUT/(Q.name+'-geometry-binding.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
