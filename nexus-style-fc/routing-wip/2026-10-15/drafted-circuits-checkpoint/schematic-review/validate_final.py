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
assert delta==[],delta
ai=identity(P/'baseline/nexus-style-fc.kicad_sch');bi=identity(P/'work/hardware/nexus-style-fc.kicad_sch');assert ai[0]==bi[0];assert all(bi[1].get(k)==v for k,v in ai[1].items() if k!='C19');c19_identity=dict(bi[1]['C19']);c19_identity.update(value=ai[1]['C19']['value'],lcsc=ai[1]['C19']['lcsc']);assert c19_identity==ai[1]['C19'];added={k:v for k,v in bi[1].items() if k not in ai[1]};assert all(v['lib_id']==[['lib_id',('s','power:GND')]] for v in added.values())
a_sch,b_sch=[sx.parse((P/f).read_text()) for f in ['baseline/nexus-style-fc.kicad_sch','work/hardware/nexus-style-fc.kicad_sch']]
ad={sx.text(v[1]):v for v in sx.find(a_sch,'lib_symbols')[0][1:]};bd={sx.text(v[1]):v for v in sx.find(b_sch,'lib_symbols')[0][1:]};assert all(bd.get(k)==v for k,v in ad.items());assert set(bd)-set(ad)=={'power:GND'}

# Added ground symbols are virtual power-input markers, never drivers or PCB parts.
for n in sx.find(b_sch,'symbol'):
 ref=sx.text(sx.find(n,'property')[0][2])
 if ref in added:
  assert sx.find(n,'in_bom')==[['in_bom','no']]
  assert sx.find(n,'on_board')==[['on_board','no']]
assert all(pin[1]=='power_in' for pin in sx.walk(bd['power:GND'],'pin'))
assert sx.find(bd['power:GND'],'power')==[['power','global']]
def property_values(sch):
 return {sx.text(sx.find(n,'property')[0][2]):{sx.text(p[1]):sx.text(p[2]) for p in sx.find(n,'property')} for n in sx.find(sch,'symbol')}
av,bv=property_values(a_sch),property_values(b_sch)
assert all(bv.get(k)==v for k,v in av.items() if k!='C19'),'Other original property values changed'
assert {k for k,v in av['C19'].items() if bv['C19'].get(k)!=v}=={'Value','LCSC','Description'}
assert bv['C19']['Value']=='10uF' and bv['C19']['LCSC']=='C19702'

erc=json.loads((P/'preview/erc.json').read_text());violations=[v for sheet in erc['sheets'] for v in sheet['violations']];assert not violations,violations
files=[P/'work/hardware/nexus-style-fc.kicad_sch',*[P/'work/tools'/n for n in ['design.py','gen_schematic.py','draft_circuits.py','draft_power.py','draft_compute.py','draft_interfaces.py']]]
report={'result':'PASS','approved_component_update':{'ref':'C19','Value':'10uF','LCSC':'C19702','Description':bv['C19']['Description']},'native_kicad_version':erc['kicad_version'],'pin_pairs_before':len(a),'pin_pairs_after':len(b),'unchanged_pin_pairs':len(a),'approved_delta':delta,'added_virtual_ground_symbols':added,'preserved_original_symbol_count':len(ai[1]),'symbol_identity_count':len(identity(P/'work/hardware/nexus-style-fc.kicad_sch')[1]),'root_uuid_preserved':True,'all_embedded_symbol_definitions_preserved_exactly':True,'symbol_and_pin_uuid_and_instance_paths_preserved':True,'erc_violations':0,'hashes':{str(f.relative_to(P)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}}
(P/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
