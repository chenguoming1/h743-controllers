from pathlib import Path
import importlib.util,sys,json,hashlib,copy
P=Path(__file__).parent
module_source=P/'evidence/standalone-design-power.py'
def load(name,path):
 sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
results=[]
for tree in ('baseline','work'):
 tools=P/tree/'nexus-style-fc/tools';d=load('design',tools/'design.py');sys.modules['design']=d
 power=load('design_power',module_source)
 results.append((d,copy.deepcopy(power.PARTS),power.nets()))
a,b=results[0][0],results[1][0]
assert a.PARTS==b.PARTS and a.CAP==b.CAP and a.nets()==b.nets()
assert results[0][1:]==results[1][1:]
selected=b.get_main_parts();old={p['ref']:p for p in a.PARTS};new={p['ref']:p for p in selected}
assert set(new)-set(old)=={'C31'}
assert all(new[k]==v for k,v in old.items() if k not in ('C27','D5'))
assert {k:v for k,v in new['D5'].items() if k!='place'}=={k:v for k,v in old['D5'].items() if k!='place'}
assert all(new[k]['pins']=={'1':'VSYS','2':'GND'} for k in ('C27','C31'))
assert new['C27']['value']==new['C31']['value']=='22uF'
assert new['C27']['lcsc']==new['C31']['lcsc']=='C602037'
selected[0]['pins']['test']='not-a-real-net';assert b.PARTS==a.PARTS and 'test' not in b.get_main_parts()[0]['pins']
report={'result':'PASS','legacy_part_count':len(a.PARTS),'selected_main_part_count':len(new),'legacy_PARTS_CAP_and_default_nets_exact':True,'standalone_power_PARTS_and_nets_exact':True,'selected_other_parts_exact':True,'deep_copy_isolation':True,'added_physical_pins':2,'placement_status':'Approved centers and D5 move; native position proof passed; final PCB validation separate','consumer_bindings':{'gen_schematic.py':'get_main_parts only for design/nexus-style-fc; explicit selection passed to Draft','draft_circuits.py':'explicit selected parts argument; legacy fallback retained','build_floorplan.py':'get_main_parts at main entry; no board generated','export_fab.py':'get_main_parts only for design/nexus-style-fc; no CAM/CPL generated','design.py':'get_main_nets explicit; default nets retains legacy behavior; CLI main selection'}}
(P/'compatibility.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
