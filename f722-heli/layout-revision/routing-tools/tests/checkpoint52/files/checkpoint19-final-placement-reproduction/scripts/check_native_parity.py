"""Compare every assigned native PCB pad with the paired exported KiCad XML netlist."""
import argparse, hashlib, json, xml.etree.ElementTree as E
from pathlib import Path
import pcbnew as p
ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--netlist',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
b=p.LoadBoard(str(a.board));root=E.parse(a.netlist).getroot();schematic={};sch_values={c.attrib['ref']:c.findtext('value') for c in root.findall('./components/comp')}
for net in root.findall('./nets/net'):
 for node in net.findall('node'):
  k=(node.attrib['ref'],node.attrib['pin']);assert k not in schematic or schematic[k]==net.attrib['name'];schematic[k]=net.attrib['name']
footprints={};assigned={};pads=[];value_mismatches=[]
for f in b.GetFootprints():
 r=f.GetReference();footprints[r]={'value':f.GetValue(),'side':f.GetLayerName(),'xy_mm':[f.GetPosition().x/1e6,f.GetPosition().y/1e6],'angle_deg':f.GetOrientationDegrees(),'uuid':f.m_Uuid.AsString()}
 if sch_values.get(r)!=f.GetValue():value_mismatches.append({'ref':r,'pcb':f.GetValue(),'schematic':sch_values.get(r)})
 for x in f.Pads():
  k=(r,x.GetNumber());net=x.GetNetname()
  if net and x.GetNumber():
   assert k not in assigned or assigned[k]==net;assigned[k]=net
  pads.append({'ref':r,'pad':x.GetNumber(),'net':net,'xy_mm':[x.GetPosition().x/1e6,x.GetPosition().y/1e6],'uuid':x.m_Uuid.AsString()})
def canonical_net(name):
 return name.replace('{slash}','/') if name and name.startswith('unconnected-(') else name
name_aliases=[{'ref':r,'pad':pin,'pcb':net,'schematic':schematic.get((r,pin))} for (r,pin),net in assigned.items() if schematic.get((r,pin))!=net and canonical_net(schematic.get((r,pin)))==canonical_net(net)]
mismatches=[{'ref':r,'pad':pin,'pcb':net,'schematic':schematic.get((r,pin))} for (r,pin),net in assigned.items() if canonical_net(schematic.get((r,pin)))!=canonical_net(net)]
missing=[{'ref':r,'pad':pin,'schematic':net} for (r,pin),net in schematic.items() if r in footprints and (r,pin) not in assigned]
report={'board_sha256':hashlib.sha256(a.board.read_bytes()).hexdigest(),'netlist_sha256':hashlib.sha256(a.netlist.read_bytes()).hexdigest(),'kicad_version':p.Version(),'component_count':len(footprints),'assigned_pad_count':len(assigned),'physical_pad_count':len(pads),'copper_layers':b.GetCopperLayerCount(),'orthogonal':all(abs(v['angle_deg']%90)<1e-6 for v in footprints.values()),'generated_unconnected_name_encoding_aliases':name_aliases,'pad_net_mismatches':mismatches,'schematic_pads_missing_native_assignment':missing,'value_mismatches':value_mismatches,'footprints':footprints,'pads':pads,'passed':not(mismatches or missing or value_mismatches)}
a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['pads','footprints']}));raise SystemExit(0 if report['passed'] else 1)
