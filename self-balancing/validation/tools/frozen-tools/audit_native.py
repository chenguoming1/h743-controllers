#!/usr/bin/python3
"""Read-only manufacturing evidence from native CAD. Writes only audit outputs.
This is NOT a release exporter. Run with /usr/bin/python3 for KiCad 9 pcbnew.
"""
import os
os.environ.setdefault('KICAD_CONFIG_HOME','/tmp/controller-r3-kicad')
os.environ.setdefault('XDG_CACHE_HOME','/tmp/controller-r3-cache')
os.environ.setdefault('XDG_DATA_HOME','/tmp/controller-r3-data')
import argparse,collections,csv,datetime,hashlib,json,math,pathlib,re,subprocess,sys
import pcbnew as p

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def mm(x):return round(p.ToMM(x),6)
def xy(pt):return [mm(pt.x),mm(pt.y)]
def fpname(f):return str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName())
def natural(r):return [int(x) if x.isdigit() else x for x in re.split(r'(\d+)',r)]
def csvout(path,rows):
 with path.open('w',newline='') as h:
  w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def norm(net):return net.rsplit('/',1)[-1] if net else None

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--project',type=pathlib.Path,required=True);ap.add_argument('--out',type=pathlib.Path,required=True);ap.add_argument('--cli-project',type=pathlib.Path);ap.add_argument('--frozen',action='store_true');a=ap.parse_args();D=a.project.resolve();O=a.out.resolve();O.mkdir(parents=True,exist_ok=True);C=a.cli_project.resolve() if a.cli_project else D
 src=D/'controller.kicad_pcb';inputs=[src,D/'controller.kicad_pro',D/'review/design-netmap.json',D/'review/bom-draft.csv',D/'review/manufacturing-profile.json']+sorted(D.glob('*.kicad_sch'))+sorted(D.glob('*.kicad_dru'))+[D/'tools/export_release.py',D/'review/sourcing/controller-r3s-bom-source-status.json',D/'review/sourcing/controller-r3s-bom-source-status.csv'];hashes={str(s):sha(s) for s in inputs}
 b=p.LoadBoard(str(src));parts=json.loads(inputs[2].read_text());partmap={q['Reference']:q for q in parts};fitted={r:q for r,q in partmap.items() if q.get('LCSC') and not q.get('DNP')};fps={f.GetReference():f for f in b.GetFootprints()};errors=[]
 def check(ok,msg):
  if not ok:errors.append(msg)
 check(len(parts)==147,'Expected 147 schematic records');check(len(fps)==len(b.GetFootprints())==151,'Expected151 unique footprints');check(len(fitted)==79,'Expected79 fitted components');check(b.GetCopperLayerCount()==6,'Expected six copper layers');check(xy(b.GetDesignSettings().GetAuxOrigin())==[0,38],'Expected datum (0,38)')
 raw=O/'raw-kicad-placements-AUDIT-ONLY.csv'
 assert sha(C/'controller.kicad_pcb')==sha(src) and sha(C/'controller.kicad_pro')==sha(D/'controller.kicad_pro'),'Isolated CLI source differs'
 subprocess.run(['sh',str(D/'tools/kicad_cli.sh'),'pcb','export','pos','--side','both','--format','csv','--units','mm','--use-drill-file-origin','--exclude-dnp','--output',str(raw),str(C/'controller.kicad_pcb')],check=True,stdout=subprocess.DEVNULL)
 rawrows=list(csv.DictReader(raw.open()));rawmap={q['Ref']:q for q in rawrows};check(len(rawrows)==len(rawmap)==79,'Raw placement count/duplicates');check(set(rawmap)==set(fitted),'Raw fitted-reference set mismatch')
 bom=list(csv.DictReader(inputs[3].open()));bommap={q['Reference']:q for q in bom};check(set(bommap)==set(partmap),'BOM/netmap reference set mismatch')
 placements=[];pads=[];drills=[];paste=[];pin_checks=0;unconnected_pin_checks=0
 for r,q in partmap.items():
  f=fps[r]
  check(fpname(f)==q['Footprint'],f'{r}: footprint/netmap mismatch')
  check(f.GetValue()==q['Value'],f'{r}: value/netmap mismatch')
  for field,key in [('LCSC','LCSC'),('Manufacturer_Part_Number','MPN')]:
   fld=f.GetFieldByName(field);actual=fld.GetText() if fld else '';check(actual==q[key],f'{r}: native {field} mismatch')
  for key in ['Value','MPN','LCSC','Footprint']:check(bommap[r][key]==q[key],f'{r}: BOM {key} mismatch')
  numbered=collections.defaultdict(list)
  for pad in f.Pads():
   if pad.GetNumber():numbered[pad.GetNumber()].append(pad)
  check(set(numbered)==set(q['nets']),f'{r}: numbered pad-set mismatch')
  for n,net in q['nets'].items():
   for pad in numbered.get(n,[]):
    got=pad.GetNetname();check(norm(got)==net if net else (not got or got.startswith('unconnected-')),f'{r}.{n}: net expected {net}, got {got}')
   pin_checks+=1;unconnected_pin_checks+=net is None
 for r,f in sorted(fps.items(),key=lambda q:natural(q[0])):
  side='Bottom' if f.GetLayer()==p.B_Cu else 'Top';x,y=xy(f.GetPosition());angle=f.GetOrientationDegrees()%360
  if r in fitted:
   q=fitted[r];v=rawmap[r]
   check(abs(float(v['PosX'])-x)<1e-6 and abs(float(v['PosY'])-(38-y))<1e-6,f'{r}: CPL coordinate mismatch')
   check(abs((float(v['Rot'])-angle+180)%360-180)<1e-6,f'{r}: CPL native angle mismatch');check(v['Side'].lower()==side.lower(),f'{r}: CPL side mismatch')
   placements.append(dict(Reference=r,MPN=q['MPN'],LCSC=q['LCSC'],Footprint=fpname(f),Side=side,Native_X_mm=x,Native_Y_mm=y,Native_angle_deg=angle,CPL_X_mm=x,CPL_Y_mm=round(38-y,6),Supplier_rotation_correction='Native audit only; user supplier overrides recorded separately'))
  for pad in f.Pads():
   layers=[b.GetLayerName(l) for l in pad.GetLayerSet().Seq()];pos=xy(pad.GetPosition());size=xy(pad.GetSize());drill=xy(pad.GetDrillSize())
   rec=dict(Reference=r,Pad=pad.GetNumber(),Net=pad.GetNetname(),Native_X_mm=pos[0],Native_Y_mm=pos[1],Size_X_mm=size[0],Size_Y_mm=size[1],Angle_deg=pad.GetOrientationDegrees()%360,Shape=pad.GetShape(),Attribute=pad.GetAttribute(),Layers=','.join(layers),Drill_X_mm=drill[0],Drill_Y_mm=drill[1])
   pads.append(rec)
   if any(drill):drills.append(dict(reference=r,pad=pad.GetNumber(),center_export_mm=[pos[0],round(38-pos[1],6)],native_xy_mm=pos,drill_local_mm=drill,angle_deg=pad.GetOrientationDegrees()%360,plated=pad.GetAttribute()!=p.PAD_ATTRIB_NPTH))
   if pad.IsOnLayer(p.F_Paste) or pad.IsOnLayer(p.B_Paste):
    layer=p.F_Paste if pad.IsOnLayer(p.F_Paste) else p.B_Paste
    # Effective shape includes declared aperture pad dimensions; local paste ratios recorded separately.
    collisions=[]
    for via in b.GetTracks():
     if isinstance(via,p.PCB_VIA) and via.IsOnLayer(p.F_Cu if layer==p.F_Paste else p.B_Cu) and pad.GetEffectiveShape(layer).Collide(p.SHAPE_CIRCLE(via.GetPosition(),via.GetDrillValue()//2),0):collisions.append({'native_xy_mm':xy(via.GetPosition()),'drill_mm':mm(via.GetDrillValue()),'net':via.GetNetname()})
    paste.append(dict(reference=r,pad=pad.GetNumber(),layer=b.GetLayerName(layer),native_xy_mm=pos,size_mm=size,radius_mm=mm(pad.GetRoundRectCornerRadius()),via_drill_overlaps=collisions))
 for via in b.GetTracks():
  if isinstance(via,p.PCB_VIA):
   pos=xy(via.GetPosition());drills.append(dict(reference='VIA',pad='',center_export_mm=[pos[0],round(38-pos[1],6)],native_xy_mm=pos,drill_local_mm=[mm(via.GetDrillValue())]*2,angle_deg=0,plated=True,layer_pair=[b.GetLayerName(via.TopLayer()),b.GetLayerName(via.BottomLayer())]))
 check(all(d.get('layer_pair',['F.Cu','B.Cu'])==['F.Cu','B.Cu'] for d in drills),'Unexpected blind/buried via span');check(pin_checks==405,'Expected405 logical pin entries');check('J2' in rawmap,'Mixed SMT/PTH J2 missing from placements');check('D1' not in fps and 'D2' not in fps and 'U13' in fps,'Power mux replacement references mismatch')
 current_skus={(q['MPN'],q['LCSC']) for q in fitted.values()};source=json.loads((D/'review/sourcing/controller-r3s-bom-source-status.json').read_text());source_rows=next(v for v in source.values() if isinstance(v,list) and v and isinstance(v[0],dict));source_keys=list(source_rows[0]);
 # Independent exact identity source CSV is the maintained live-catalog snapshot, not a current stock assertion.
 sr=list(csv.DictReader((D/'review/sourcing/controller-r3s-bom-source-status.csv').open()));skus={(q.get('MPN',q.get('mpn')),q.get('LCSC',q.get('lcsc'))) for q in sr};check(len(current_skus)==35 and len(sr)==35 and current_skus==skus,'Exact35 source-snapshot SKU set mismatch')
 check(source.get('source_bom_sha256')==sha(D/'review/bom-draft.csv'),'Source-snapshot BOM hash stale')
 for q in sr:
  refs={r for r,v in fitted.items() if (v['MPN'],v['LCSC'])==(q['mpn'],q['lcsc'])};check(set(q['references'].split(','))==refs and int(q['quantity_per_board'])==len(refs),'Source-snapshot reference/quantity mismatch: '+q['lcsc'])
 csvout(O/'fitted-79-native-placements.csv',placements);csvout(O/'all-pad-evidence.csv',pads)
 (O/'expected-drill-features.json').write_text(json.dumps(drills,indent=2)+'\n');(O/'paste-and-drill-evidence.json').write_text(json.dumps(paste,indent=2)+'\n')
 after={str(s):sha(s) for s in inputs};check(hashes==after,'SOURCE CHANGED DURING AUDIT; rerun')
 summary=dict(status='FROZEN LOCAL CAD CONSISTENCY; SUPPLIER AND HARDWARE QUALIFICATION PENDING' if a.frozen else 'IN-PROGRESS CAD AUDIT ONLY; NOT A MANUFACTURING RELEASE',kicad_version=p.Version(),created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_sha256=hashes,errors=errors,copper_layers=b.GetCopperLayerCount(),schematic_count=len(parts),fitted_count=len(fitted),unique_sku_count=len(current_skus),footprint_count=len(fps),excluded_features=len(fps)-len(fitted),fitted_side_counts=dict(collections.Counter(q['Side'] for q in placements)),logical_pin_entries_checked=pin_checks,logical_unconnected_entries=unconnected_pin_checks,raw_pos_exact_fitted_set=set(rawmap)==set(fitted),origin_native_mm=xy(b.GetDesignSettings().GetAuxOrigin()),coordinate_contract='X=nativeX,Y=38-nativeY; no bottom-X mirror; native modulo360 angles; no JLC correction',drill_features=len(drills),nonplated_features=sum(not q['plated'] for q in drills),plated_slot_features=sum(q['plated'] and q['drill_local_mm'][0]!=q['drill_local_mm'][1] for q in drills),paste_apertures=len(paste),paste_apertures_with_drill_overlap=[q for q in paste if q['via_drill_overlaps']],source_stable=hashes==after,qualification_limits=['Final artifact/source checks, supplier acceptance and hardware qualification remain separate','JLC exact-SKU rotation/pickup anchor, Standard double-side panel/carrier and J2 shell solder process unverified','Native dimensions do not establish stencil-process or physical harness/thermal/startup qualification'])
 (O/'native-audit.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2));return bool(errors)
if __name__=='__main__':sys.exit(main())
