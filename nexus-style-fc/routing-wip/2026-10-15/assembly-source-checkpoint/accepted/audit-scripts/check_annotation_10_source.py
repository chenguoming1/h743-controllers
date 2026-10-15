from pathlib import Path
import json,hashlib,shutil,subprocess,collections,xml.etree.ElementTree as ET
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');S=R/'mechanical-integration/main-signal-slot-08';C=R/'mechanical-integration/main-assembly-annotation-10';O=C/'erc-all-visible';assert not O.exists();O.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def pinmap(p):
 out={}
 if p.read_text().lstrip().startswith('('):
  import sys
  sys.path.insert(0,str(R/'assembly-annotation-cleanup'));import guarded_cleanup as G
  for net in G.parse(p.read_text()).one('nets').children('net'):
   for node in net.children('node'):
    key=(node.val('ref'),node.val('pin'));assert key not in out,key;out[key]=net.val('name')
  return out
 for net in ET.parse(p).getroot().find('nets').findall('net'):
  for node in net.findall('node'):
   key=(node.get('ref'),node.get('pin'));assert key not in out,key;out[key]=net.get('name')
 return out
before=pinmap(S/'r62-source-final-netlist.xml');after=pinmap(C/'final-netlist.net');assert before==after and len(after)==349
assert after[('U10','3')]=='unconnected-(U10-EN-Pad3)'
shutil.copytree(C/'hardware',O/'hardware');p=O/'hardware/nexus-style-fc.kicad_pro';d=json.loads(p.read_text());flags={k:v for k,v in d['erc']['rule_severities'].items() if v=='ignore'};assert set(flags)=={'single_global_label','four_way_junction','simulation_model_issue','footprint_filter'}
for k in flags:d['erc']['rule_severities'][k]='warning'
p.write_text(json.dumps(d,indent=2)+'\n');cmd=[str(R/'runtime/kicad-cli'),'sch','erc','--severity-all','--format','json','--exit-code-violations','-o',str(O/'native-erc.json'),str(O/'hardware/nexus-style-fc.kicad_sch')]
with (O/'native-erc.log').open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=90)
assert r.returncode in [0,5];erc=json.loads((O/'native-erc.json').read_text());findings=[v for sh in erc['sheets'] for v in sh['violations']];counts=dict(collections.Counter(v['type']+':'+v['severity'] for v in findings));assert counts=={'single_global_label:warning':13},counts
for name in ['main','child']:
 e=json.loads((C/(name+'-native-erc.json')).read_text());assert not [q for sh in e['sheets'] for q in sh['violations']]
child=json.loads((C/'child-native-drc.json').read_text());assert not child['unconnected_items'] and not [q for q in child['violations']+child['schematic_parity'] if q['severity']=='error'];cc=dict(collections.Counter(v['type']+':'+v['severity'] for v in child['violations']+child['schematic_parity']));assert cc=={'missing_courtyard:warning':11,'footprint_filters_mismatch:warning':11},cc
result={'status':'PASS fresh native 349-pin equivalence, enabled/all-visible ERC and matching child checks','source_schematic_sha256':sha(S/'hardware/nexus-style-fc.kicad_sch'),'candidate_schematic_sha256':sha(C/'hardware/nexus-style-fc.kicad_sch'),'source_netlist_sha256':sha(S/'r62-source-final-netlist.xml'),'candidate_netlist_sha256':sha(C/'final-netlist.net'),'pin_count':349,'all_pin_nets_exact':True,'U10_EN_isolated_net':after[('U10','3')],'enabled_main_ERC':0,'enabled_child_ERC':0,'inherited_ERC_ignored_flags':flags,'all_visible_ERC_counts':counts,'child_counts':cc,'child_board_sha256':sha(C/'hardware/header-board/nexus-header-board.kicad_pcb'),'qualification':'All-visible source advisories are retained without suppression; physical pin-net equivalence is distinct from inherited child footprint-filter/courtyard advisories.'};(C/'source-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
