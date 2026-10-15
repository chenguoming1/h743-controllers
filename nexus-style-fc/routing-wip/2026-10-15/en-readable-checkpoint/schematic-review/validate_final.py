from pathlib import Path
import sys,json,hashlib
P=Path(__file__).parent; sys.path.insert(0,str(P/'work/tools')); import sexpr as sx

def pinmap(path):
 d=sx.parse(path.read_text());m={}
 for net in sx.find(d,'nets')[0][1:]:
  name=sx.text(sx.find(net,'name')[0][1])
  for node in sx.find(net,'node'):m[tuple(sx.text(sx.find(node,k)[0][1]) for k in ['ref','pin'])]=name
 return m

def identity(path):
 d=sx.parse(path.read_text());out={}
 for n in sx.find(d,'symbol'):
  props={sx.text(p[1]):sx.text(p[2]) for p in sx.find(n,'property')};out[props['Reference']]={'uuid':sx.find(n,'uuid'),'pins':sx.find(n,'pin'),'instances':sx.find(n,'instances'),'lib_id':sx.find(n,'lib_id'),'value':props['Value'],'footprint':props['Footprint'],'lcsc':props.get('LCSC')}
 return sx.find(d,'uuid'),out

a,b=map(pinmap,[P/'baseline/baseline.net',P/'preview/connected.net']);delta=[{'ref':r,'pin':p,'before':a.get((r,p)),'after':b.get((r,p))} for r,p in sorted(set(a)|set(b)) if a.get((r,p))!=b.get((r,p))]
assert delta==[{'ref':'U10','pin':'3','before':'VSYS','after':'unconnected-(U10-EN-Pad3)'}],delta
assert identity(P/'baseline/nexus-style-fc.kicad_sch')==identity(P/'work/hardware/nexus-style-fc.kicad_sch')
a_sch,b_sch=[sx.parse((P/f).read_text()) for f in ['baseline/nexus-style-fc.kicad_sch','work/hardware/nexus-style-fc.kicad_sch']]
assert sx.find(a_sch,'lib_symbols')==sx.find(b_sch,'lib_symbols'),'Embedded symbol definitions changed'

erc=json.loads((P/'preview/erc.json').read_text());violations=[v for sheet in erc['sheets'] for v in sheet['violations']];assert not violations,violations
files=[P/'work/hardware/nexus-style-fc.kicad_sch',*[P/'work/tools'/n for n in ['design.py','gen_schematic.py','readable_schematic.py','connect_functional_units.py']]]
report={'result':'PASS','native_kicad_version':erc['kicad_version'],'pin_pairs_before':len(a),'pin_pairs_after':len(b),'unchanged_pin_pairs':len(a)-1,'approved_delta':delta,'symbol_identity_count':len(identity(P/'work/hardware/nexus-style-fc.kicad_sch')[1]),'root_uuid_preserved':True,'all_embedded_symbol_definitions_preserved_exactly':True,'symbol_and_pin_uuid_and_instance_paths_preserved':True,'erc_violations':0,'hashes':{str(f.relative_to(P)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}}
(P/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
