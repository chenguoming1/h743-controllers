#!/usr/bin/env python3
"""FOR SOLE NATIVE LANE ONLY, using its KiCad Python wrapper.
Load project-local libraries, apply scoped annotations in memory, serialize small
before/after test boards and prove all non-graphic footprint nodes unchanged.
Never opens or overwrites the routed board. Not a full generator rebuild.
"""
import argparse,importlib.util,json,pathlib,sys
import pcbnew
from guarded_cleanup import parse,footprint_map,csha,sha,write_json,Node
ap=argparse.ArgumentParser();ap.add_argument('--candidate-project',required=True,type=pathlib.Path);ap.add_argument('--expected-helper-sha256',required=True);ap.add_argument('--out',required=True,type=pathlib.Path);a=ap.parse_args();C=a.candidate_project.resolve();O=a.out.resolve();assert not O.exists();assert sha(C/'tools/assembly_annotations.py')==a.expected_helper_sha256
O.mkdir(parents=True);spec=importlib.util.spec_from_file_location('native_checked_annotations',C/'tools/assembly_annotations.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
source=footprint_map(parse((C/'hardware/nexus-style-fc.kicad_pcb').read_text()));refs=['J1','J3','J4','J5','J6','D1','D2','D3','U3','L2','U14'];rows=[]
for project in ['nexus-style-fc','standalone-module','nexus-header-board']:
 b=pcbnew.BOARD();fps={}
 for ref in refs:
  p=source[ref];fp=pcbnew.FootprintLoad(str(C/'hardware/library/NexusFC.pretty'),p.items[1].split(':')[1]);assert fp is not None;fp.SetReference(ref);b.Add(fp);fps[ref]=fp
 before=O/(project+'-before.kicad_pcb');after=O/(project+'-after.kicad_pcb');pcbnew.SaveBoard(str(before),b)
 for ref,fp in fps.items():p=source[ref];m.apply_main_assembly_annotations(fp,{'ref':ref,'fp':p.items[1],'lcsc':p.prop('LCSC')},project)
 pcbnew.SaveBoard(str(after),b);bf=footprint_map(parse(before.read_text()));af=footprint_map(parse(after.read_text()))
 def protected(f):return [n.value() if isinstance(n,Node) else n for n in f.items if not isinstance(n,Node) or n.tag not in ['fp_line','fp_circle']]
 for ref in refs:
  assert protected(bf[ref])==protected(af[ref]),(project,ref,'non-graphic source mutation')
  gb=[n.value() for n in bf[ref].children('fp_line')+bf[ref].children('fp_circle')];ga=[n.value() for n in af[ref].children('fp_line')+af[ref].children('fp_circle')];changed=gb!=ga;expected=project=='nexus-style-fc' and ref in ['J4','J6','D1','D2','D3'];assert changed==expected,(project,ref,changed,expected)
  if expected:
   def geometry(n):
    result=[]
    for x in n.children('fp_line')+n.children('fp_circle'):
     key='start' if x.tag=='fp_line' else 'center'
     fill=x.children('fill');filled=bool(fill and fill[0].items[1] not in ['no','none'])
     result.append([x.tag,x.val('layer'),list(map(float,x.one(key).items[1:3])),list(map(float,x.one('end').items[1:3])),float(x.one('stroke').val('width')),filled])
    return sorted(result,key=lambda x:json.dumps(x))
   assert geometry(af[ref])==geometry(source[ref]),(ref,'native helper artwork differs from candidate source')
   removed=[n for n in gb if n not in ga];added=[n for n in ga if n not in gb];assert len(removed)==1 and len(added)==(2 if ref in ['J4','J6'] else 1),(ref,removed,added)
  rows.append({'project':project,'ref':ref,'non_graphic_source_exact':True,'graphic_change_expected':expected,'before_graphic_sha256':csha(gb),'after_graphic_sha256':csha(ga)})
write_json(O/'native-generator-verification.json',{'status':'PASS scoped annotation helper on real native imported footprint objects','helper_sha256':sha(C/'tools/assembly_annotations.py'),'marker_style':m.MARKER_STYLE,'checks':rows,'qualification':'Real native helper/load/save check only, not full floorplan rebuild, DRC, render or release signoff.'});print('PASS native helper: 33 project/ref cases, only intended five main graphic instances changed')
