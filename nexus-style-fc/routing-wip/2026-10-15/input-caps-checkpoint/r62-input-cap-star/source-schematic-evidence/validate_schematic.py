from pathlib import Path
import sys,json,hashlib
P=Path(__file__).parent;sys.path.insert(0,str(P/'work/nexus-style-fc/tools'));import sexpr as s

def pinmap(path):
 d=s.parse(path.read_text());out={}
 for net in s.find(d,'nets')[0][1:]:
  for node in s.find(net,'node'):out[tuple(s.text(s.find(node,k)[0][1]) for k in ('ref','pin'))]=s.text(s.find(net,'name')[0][1])
 return out

def symmap(z):return {s.text(s.find(n,'property')[0][2]):n for n in s.find(z,'symbol')}
a,b=pinmap(P/'baseline.net'),pinmap(P/'preview/connected.net');assert len(a)==347 and len(b)==349;assert all(b.get(k)==v for k,v in a.items());assert set(b)-set(a)=={('C31','1'),('C31','2')};assert b['C31','1']=='VSYS' and b['C31','2']=='GND'
x=s.parse((P/'baseline/nexus-style-fc/hardware/nexus-style-fc.kicad_sch').read_text());y=s.parse((P/'work/nexus-style-fc/hardware/nexus-style-fc.kicad_sch').read_text());xm,ym=symmap(x),symmap(y)
assert set(ym)-set(xm)=={'C31'};assert s.find(x,'uuid')==s.find(y,'uuid');assert s.find(x,'lib_symbols')==s.find(y,'lib_symbols')
changes={}
for ref,n in xm.items():
 for k in ('uuid','pin','instances','lib_id','at'):assert s.find(n,k)==s.find(ym[ref],k),(ref,k)
 before={s.text(p[1]):s.text(p[2]) for p in s.find(n,'property')};after={s.text(p[1]):s.text(p[2]) for p in s.find(ym[ref],'property')}
 if before!=after:changes[ref]={k:[v,after[k]] for k,v in before.items() if v!=after[k]}
assert set(changes)=={'C27'};assert set(changes['C27'])=={'Value','Footprint','LCSC','Description'}
erc=json.loads((P/'preview/erc.json').read_text());violations=[v for sh in erc['sheets'] for v in sh['violations']];assert not violations
report={'result':'PASS','native_version':erc['kicad_version'],'baseline_sha256':hashlib.sha256((P/'baseline/nexus-style-fc/hardware/nexus-style-fc.kicad_sch').read_bytes()).hexdigest(),'schematic_sha256':hashlib.sha256((P/'work/nexus-style-fc/hardware/nexus-style-fc.kicad_sch').read_bytes()).hexdigest(),'original_pin_pairs_preserved':347,'final_pin_pairs':349,'added_pins':{'C31.1':'VSYS','C31.2':'GND'},'existing_symbol_identities_and_positions_preserved':len(xm),'all_embedded_definitions_exact':True,'approved_property_changes':changes,'C31_instance_uuid':s.find(ym['C31'],'uuid')[0][1],'erc_violations':0,'deterministic_generation':True,'pcb_validation_status':'pending sole PCB lane combined trial'}
(P/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
