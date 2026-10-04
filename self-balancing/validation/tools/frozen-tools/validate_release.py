#!/usr/bin/python3
"""Independent frozen-release audit; never exports Gerber/drill/assembly data.
Prerequisite: owner has completed native release gate and exported release files.
Refresh audit_native.py into --audit first. Run --checks to repeat ERC/DRC read-only.
"""
import argparse,collections,csv,hashlib,json,math,pathlib,re,subprocess,sys

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def q(x):return round(x,6)
def feature(plated,diameter,start,end=None):
 start=tuple(map(q,start));end=tuple(map(q,end if end is not None else start));return (plated,q(diameter),*sorted([start,end]))
def drill_parse(path):
 text=path.read_text();assert 'METRIC' in text and 'INCH' not in text;assert 'G90' in text and 'G91' not in text
 plated='TF.FileFunction,Plated' in text;assert plated or 'TF.FileFunction,NonPlated' in text
 tools={};tool=None;x=y=0.;route=None;features=[]
 def at(s):
  nonlocal x,y
  m=re.search(r'X([+-]?[\d.]+)',s);n=re.search(r'Y([+-]?[\d.]+)',s)
  if m:x=float(m.group(1))
  if n:y=float(n.group(1))
  return (x,y)
 for s in text.splitlines():
  s=s.strip()
  if s.startswith(';'):continue
  m=re.fullmatch(r'T(\d+)C([\d.]+)',s)
  if m:tools[int(m.group(1))]=float(m.group(2));continue
  m=re.fullmatch(r'T(\d+)',s)
  if m:tool=int(m.group(1));continue
  if 'G85' in s:
   a,z=s.split('G85');start=at(a);end=at(z);features.append(feature(plated,tools[tool],start,end));continue
  if s.startswith('G00'):route=at(s);continue
  if s.startswith('G01') and route is not None:
   end=at(s);features.append(feature(plated,tools[tool],route,end));route=end;continue
  if s=='M16':route=None;continue
  if s.startswith(('X','Y')):features.append(feature(plated,tools[tool],at(s)))
 return features

def expected_feature(d):
 cx,cy=d['center_export_mm'];w,h=d['drill_local_mm'];angle=math.radians(d['angle_deg']);half=(max(w,h)-min(w,h))/2
 dx,dy=(math.cos(angle)*half,math.sin(angle)*half) if w>=h else (-math.sin(angle)*half,math.cos(angle)*half)
 return feature(d['plated'],min(w,h),(cx-dx,cy-dy),(cx+dx,cy+dy))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--project',type=pathlib.Path);ap.add_argument('--audit',type=pathlib.Path);ap.add_argument('--release',type=pathlib.Path);ap.add_argument('--checks',action='store_true');ap.add_argument('--cli-project',type=pathlib.Path);ap.add_argument('--selftest',action='store_true');a=ap.parse_args()
 if a.selftest:
  t=pathlib.Path('/tmp/r3s-excellon-parser-test.drl');t.write_text('M48\n; #@! TF.FileFunction,Plated,1,6,PTH\nMETRIC\nT1C0.6\n%\nG90\nG05\nT1\nX1.0Y2.0\nX3.0Y4.0G85X4.1Y4.0\nG00X5.0Y6.0\nM15\nG01X5.6Y6.0\nM16\nG05\nM30\n')
  assert drill_parse(t)==[feature(True,.6,(1,2)),feature(True,.6,(3,4),(4.1,4)),feature(True,.6,(5,6),(5.6,6))]
  assert expected_feature(dict(center_export_mm=[3.55,4],drill_local_mm=[.6,1.7],angle_deg=90,plated=True))==feature(True,.6,(3,4),(4.1,4))
  t.unlink();print('Drill parser: decimal absolute coordinates, G85 and routed-slot cases pass');return 0
 assert a.project and a.audit
 D=a.project.resolve();A=a.audit.resolve();C=a.cli_project.resolve() if a.cli_project else D;R=a.release or D/'release';errors=[];facts={};check_counts={};checked_reports={};native_hash=sha(D/'controller.kicad_pcb');export_manifest_hash=None
 def check(ok,message):
  if not ok:errors.append(message)
 try:
  native=json.loads((A/'native-audit.json').read_text());check(not native['errors'],'Native audit failed');check(native['source_stable'],'Native audit snapshot unstable')
  for path,h in native['source_sha256'].items():check(sha(pathlib.Path(path))==h,'Audit input no longer current: '+path)
  release=json.loads((R/'export-verification.json').read_text());check(release['native_sha256']==sha(D/'controller.kicad_pcb'),'Release native SHA mismatch')
  export_manifest_hash=sha(R/'SHA256_MANIFEST.json');manifest=json.loads((R/'SHA256_MANIFEST.json').read_text());files={str(p.relative_to(R)) for p in R.rglob('*') if p.is_file() and p.name!='SHA256_MANIFEST.json'};check(set(manifest)==files,'Manifest coverage differs from release files')
  for name,h in manifest.items():check(sha(R/name)==h,'Manifest hash mismatch: '+name)
  profile=json.loads((R/'manufacturing-profile.json').read_text());check(profile==json.loads((D/'review/manufacturing-profile.json').read_text()),'Export stack/profile changed');check(profile['stack_id']=='JLC06161H-3313' and profile['copper_layers']==6,'Wrong six-layer stack')
  expected={x['Reference']:x for x in csv.DictReader((A/'fitted-79-native-placements.csv').open())};cpl=list(csv.DictReader((R/'assembly/JLC_CPL_NATIVE_AUDIT.csv').open()));check(len(cpl)==79 and len({x['Designator'] for x in cpl})==79,'CPL count/duplicates');check({x['Designator'] for x in cpl}==set(expected),'CPL reference set mismatch')
  for row in cpl:
   n=row['Designator'];v=expected[n]
   for actual,key in [('Mid X','CPL_X_mm'),('Mid Y','CPL_Y_mm'),('Rotation','Native_angle_deg')]:check(abs(float(row[actual])-float(v[key]))<1e-6,n+' CPL '+actual+' mismatch')
   check(row['Layer']==v['Side'],n+' CPL side mismatch')
  supplier_cpl=list(csv.DictReader((R/'assembly/JLC_CPL.csv').open()));supplied=D/'inputs/user-corrected-JLC_CPL.csv';overrides=json.loads((D/'review/assembly-cpl-overrides.json').read_text())
  check(sha(supplied)==overrides['source_sha256'],'User CPL source hash mismatch');check(supplier_cpl==list(csv.DictReader(supplied.open())),'Supplier CPL differs from user-corrected input')
  check(len(supplier_cpl)==79 and {x['Designator'] for x in supplier_cpl}==set(expected),'Supplier CPL reference mismatch');facts['supplier_cpl_corrections']=len(overrides['overrides'])
  bom=list(csv.DictReader((R/'assembly/JLC_BOM.csv').open()));seen=[]
  for row in bom:
   refs=row['Designator'].split(',');seen.extend(refs);check(len(refs)==int(row['Quantity']),'BOM group quantity mismatch')
   for n in refs:
    v=expected[n]
    check(row['Manufacturer Part Number']==row['Comment']==v['MPN'] and row['LCSC Part #']==v['LCSC'] and row['Footprint']==v['Footprint'],n+' BOM identity mismatch')
  check(len(seen)==79 and set(seen)==set(expected),'BOM fitted-reference mismatch');check('J2' in seen,'J2 missing from assembly files')
  fab=R/'single-board-gerbers';gerbers={};coords={};attrs={}
  for path in fab.iterdir():
   if path.suffix in ['.drl','.gbrjob']:continue
   content=path.read_text();m=re.search(r'%TF.FileFunction,([^*]+)\*%',content);check(bool(m),'Missing X2 FileFunction: '+path.name)
   if not m:continue
   ff=m.group(1);check(ff not in gerbers,'Duplicate Gerber function: '+ff);gerbers[ff]=path.name;attrs[path.name]=ff
   check('%MOMM*%' in content and '%FSLAX46Y46*%' in content,path.name+' wrong units/precision');check('%TF.SameCoordinates,Original*%' in content,path.name+' lacks unmirrored original-frame assertion');check(content.rstrip().endswith('M02*'),path.name+' missing end marker')
   allxy=re.findall(r'X(-?\d+)Y(-?\d+)D0[123]\*',content);coords[ff]=[(int(x)/1e6,int(y)/1e6) for x,y in allxy]
  expected_functions={'Copper,L1,Top','Copper,L2,Inr','Copper,L3,Inr','Copper,L4,Inr','Copper,L5,Inr','Copper,L6,Bot','Soldermask,Top','Soldermask,Bot','Legend,Top','Legend,Bot','Paste,Top','Paste,Bot','Profile,NP'}
  # KiCad's documented FileFunction token is Paste. Any different token requires explicit review.
  check(set(gerbers)==expected_functions,'Unexpected/missing Gerber functions: '+str(sorted(set(gerbers)^expected_functions)))
  for layer,x,y in [('Copper,L1,Top',10.325,23.5),('Copper,L6,Bot',24.3,19.53)]:check((x,y) in coords.get(layer,[]),layer+' missing known pin-1 export coordinate')
  for ff,pts in coords.items():
   if pts:check(min(x for x,y in pts)>=-.2 and max(x for x,y in pts)<=38.6 and min(y for x,y in pts)>=-.2 and max(y for x,y in pts)<=38.2,ff+' implausible one-board coordinate extents')
  edge=coords.get('Profile,NP',[])
  if edge:check(abs(min(x for x,y in edge))<1e-6 and abs(max(x for x,y in edge)-38)<1e-6 and abs(min(y for x,y in edge))<1e-6 and abs(max(y for x,y in edge)-38)<1e-6,'Outline not38x38 in agreed datum')
  
  drillpaths=list(fab.glob('*.drl'));check(len(drillpaths)==2,'Expected one PTH and one NPTH drill file')
  for path in drillpaths:check(bool(re.search(r'TF.FileFunction,(?:NonPlated|Plated),1,6,(?:N?PTH)',path.read_text())),path.name+' wrong drill layer span')
  observed=collections.Counter(f for path in drillpaths for f in drill_parse(path));drills=json.loads((A/'expected-drill-features.json').read_text());wanted=collections.Counter(expected_feature(d) for d in drills)
  check(observed==wanted,'Drill inventory/diameters/slot endpoints differ from native');facts['drill_missing']=list((wanted-observed).elements());facts['drill_extra']=list((observed-wanted).elements());facts['gerber_file_functions']=gerbers;facts['drill_features']=sum(observed.values());facts['bom_sku_groups']=len(bom);facts['cpl_count']=len(cpl)
  if a.checks:
   for path in [D/'controller.kicad_pcb',D/'controller.kicad_pro']+list(D.glob('*.kicad_sch')):check(sha(path)==sha(C/path.name),'Isolated CLI source differs: '+path.name)
   if errors:raise ValueError('Precheck failed before isolated ERC/DRC')
   for kind,src,target in [('sch',C/'controller.kicad_sch',A/'final-independent-erc.json'),('pcb',C/'controller.kicad_pcb',A/'final-independent-drc.json')]:
    cmd=['sh',str(D/'tools/kicad_cli.sh'),kind,'erc' if kind=='sch' else 'drc','--format','json','--severity-all']
    if kind=='pcb':cmd+=['--schematic-parity']
    subprocess.run(cmd+['-o',str(target),str(src)],check=True,stdout=subprocess.DEVNULL);v=json.loads(target.read_text())
    checked_reports[target.name]=sha(target)
    if kind=='sch':
     check_counts['erc']=sum(len(s.get('violations',[])) for s in v.get('sheets',[]));check(check_counts['erc']==0,'Fresh independent ERC not clean')
    else:
     for key,name in [('violations','physical_drc'),('unconnected_items','unconnected'),('schematic_parity','parity')]:check_counts[name]=len(v[key]);check(not v[key],'Fresh independent DRC '+key+' not empty')
  for path,h in native['source_sha256'].items():check(sha(pathlib.Path(path))==h,'Input changed while validating: '+path)
 except Exception as e:errors.append(type(e).__name__+': '+str(e))
 audit_input_hashes={name:sha(A/name) for name in ['native-audit.json','fitted-79-native-placements.csv','expected-drill-features.json'] if (A/name).is_file()}
 result={'audit_input_sha256':audit_input_hashes,'native_sha256':native_hash,'export_manifest_sha256':export_manifest_hash,'check_counts':check_counts,'check_report_sha256':checked_reports,'status':'PASS LOCAL FILE CONSISTENCY' if not errors else 'NOT PASSED','errors':errors,'facts':facts,'fresh_independent_ERC_DRC_requested':a.checks,'scope':'Local artifact validation only. Does not authorize or qualify supplier panel, component-library alignment, stencil/assembly process, harness or physical performance.'};(A/'release-independent-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return bool(errors)
if __name__=='__main__':sys.exit(main())
