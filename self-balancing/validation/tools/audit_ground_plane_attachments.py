#!/usr/bin/python3
"""Read-only finite-width filled-GND attachments, with explicit annulus scope.

Native plated pad/via lands are terminal regions; their drilled annuli are
verified and recorded separately, not mistaken for ordinary trace necks.
Eroding the native plane/land union screens the copper outside those terminal
regions. The check requires all terminal anchors to remain in the main broad
plane component, avoiding false claims from mere Boolean contact or harmless
isolated plane slivers. Native solid/thermal zone modes are explicitly reported.
"""
import argparse,hashlib,json,os,collections
from pathlib import Path
os.environ.setdefault('KICAD_CONFIG_HOME','/tmp/controller-r3-kicad')
import pcbnew as p
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();uid=lambda q:q.m_Uuid.AsString();xy=lambda q:[q.x/1e6,q.y/1e6]
def polygon(q,l):
 out=p.SHAPE_POLY_SET();q.TransformShapeToPolygon(out,l,0,50,p.ERROR_OUTSIDE);return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert sha(a.candidate)==a.sha256;b=p.LoadBoard(str(a.candidate));layers=list(b.GetEnabledLayers().CuStack());tracks=list(b.GetTracks());pads=[q for f in b.GetFootprints() for q in f.Pads()];ground_vias=[q for q in tracks if isinstance(q,p.PCB_VIA) and q.GetNetname()=='GND'];by=collections.defaultdict(list);zones=[];errors=[];untraced=[]
 for t in tracks:
  if isinstance(t,p.PCB_VIA):continue
  for l in layers:
   if t.IsOnLayer(l):by[(t.GetNetname(),l)].append(t)
 for q in pads:
  n=q.GetNetname()
  if not n or n.startswith('unconnected-'):continue
  if any(q.IsOnLayer(l) and any(q.GetEffectiveShape(l).GetClearance(t.GetEffectiveShape(l))<=0 for t in by[(n,l)]) for l in layers):continue
  contacts=[]
  for z in b.Zones():
   if z.GetIsRuleArea() or z.GetNetname()!=n:continue
   for l in layers:
    if q.IsOnLayer(l) and z.IsOnLayer(l) and z.HasFilledPolysForLayer(l) and q.GetEffectiveShape(l).GetClearance(z.GetFilledPolysList(l))<=0:contacts.append(b.GetLayerName(l))
  untraced.append({'uuid':uid(q),'reference':q.GetParentFootprint().GetReference(),'pin':q.GetNumber(),'net':n,'xy_mm':xy(q.GetPosition()),'size_mm':xy(q.GetSize()),'drill_mm':xy(q.GetDrillSize()),'shape':int(q.GetShape()),'pad_zone_connection_override':int(q.GetLocalZoneConnection()),'plane_contacts':contacts})
 expected=[q for q in untraced if q['reference']=='J2' and q['pin']=='S1' and q['net']=='GND']
 if len(untraced)!=4 or len(expected)!=4:errors.append('Unexpected live untraced terminal inventory')
 all_gnd_lands=ground_vias+[q for q in pads if q.GetNetname()=='GND' and q.HasHole()];terminal_rows=[]
 for q in all_gnd_lands:
  isvia=isinstance(q,p.PCB_VIA)
  if isvia:
   row={'uuid':uid(q),'kind':'via','xy_mm':xy(q.GetPosition()),'diameter_mm':q.GetWidth(p.F_Cu)/1e6,'drill_mm':q.GetDrillValue()/1e6,'radial_annulus_mm':(q.GetWidth(p.F_Cu)-q.GetDrillValue())/2e6};minimum=.075
  else:
   ds=q.GetDrillSize();sz=q.GetSize();row={'uuid':uid(q),'kind':'plated_pad','reference':q.GetParentFootprint().GetReference(),'pin':q.GetNumber(),'xy_mm':xy(q.GetPosition()),'size_mm':xy(sz),'drill_mm':xy(ds),'shape':int(q.GetShape()),'drill_shape':int(q.GetDrillShape()),'radial_annulus_mm':min(sz.x-ds.x,sz.y-ds.y)/2e6};minimum=.15
  if row['radial_annulus_mm']<minimum:errors.append('Terminal annulus below approved geometry floor: '+uid(q))
  terminal_rows.append(row)
 for l in layers:
  zz=[z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname()=='GND' and z.IsOnLayer(l) and z.HasFilledPolysForLayer(l)]
  if not zz:continue
  raw=p.SHAPE_POLY_SET()
  for z in zz:raw.BooleanAdd(z.GetFilledPolysList(l))
  union=p.SHAPE_POLY_SET(raw);lands=[q for q in all_gnd_lands if q.IsOnLayer(l)]
  for q in lands:union.BooleanAdd(polygon(q,l))
  eroded=p.SHAPE_POLY_SET(union);eroded.Inflate(-65100,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,50);components=[]
  for oi in range(eroded.OutlineCount()):
   component=p.SHAPE_POLY_SET(eroded.COutline(oi))
   for hi in range(eroded.HoleCount(oi)):component.AddHole(eroded.CHole(oi,hi),0)
   components.append(component)
  main=max(range(len(components)),key=lambda i:components[i].Area()) if components else None;rows=[]
  for q in lands:
   present=[i for i,poly in enumerate(components) if poly.Contains(q.GetPosition())];native_contact=q.GetEffectiveShape(l).GetClearance(raw)<=0;ok=main in present and native_contact;rows.append({'uuid':uid(q),'native_filled_plane_contact':native_contact,'eroded_component_ids':present,'connected_to_main_broad_plane_at_01302mm':ok})
   if not ok and l in [p.In1_Cu,p.In3_Cu,p.In4_Cu]:errors.append('Ground terminal lacks bounded reference-plane-width proof: '+uid(q)+' '+b.GetLayerName(l))
  zones.append({'layer':b.GetLayerName(l),'is_reference_plane':l in [p.In1_Cu,p.In3_Cu,p.In4_Cu],'native_zone_modes':[{'uuid':uid(z),'pad_connection_enum':int(z.GetPadConnection()),'pad_connection_name':'FULL_SOLID' if z.GetPadConnection()==p.ZONE_CONNECTION_FULL else 'THERMAL_OR_OTHER','configured_unused_thermal_spoke_width_mm':z.GetThermalReliefSpokeWidth()/1e6} for z in zz],'raw_polygon_count':raw.OutlineCount(),'eroded_component_count':len(components),'main_eroded_area_mm2':components[main].Area()/1e12 if main is not None else 0,'disposition':'Every terminal must connect to the common broad reference-plane component' if l in [p.In1_Cu,p.In3_Cu,p.In4_Cu] else 'Supplemental GND fill on routed layer; separate islands are not assumed to be a reference plane. Every terminal is independently required to pass all three solid reference planes.','terminal_count':len(lands),'terminals':rows})
  if any(z.GetPadConnection()!=p.ZONE_CONNECTION_FULL for z in zz):errors.append('Unexpected non-solid GND zone mode requires spoke review')
 report={'status':'PASS BOUNDED GND PLANE/LAND ATTACHMENT GEOMETRY' if not errors else 'REVIEW REQUIRED','candidate_sha256':a.sha256,'errors':errors,'all_pad_count':len(pads),'live_pads_without_direct_tracks':untraced,'ground_via_count':len(ground_vias),'plated_ground_pad_count':sum(not isinstance(q,p.PCB_VIA) for q in all_gnd_lands),'terminal_annulus_inventory':terminal_rows,'plane_results':zones,'method':__doc__,'verified_reference_plane_terminal_attachments':sum(q['terminal_count'] for q in zones if q['is_reference_plane']),'scope':'All four live untraced J2 shell lands plus97GNDvias across every actual filled GND layer; direct tracked SMD pads are separately audited. Solid-zone geometry is measured; unused configured thermal width is not claimed as an actual spoke.','precision':{'outside_terminal_screen_width_mm':.1302,'native_polygon_error_mm':.00005},'annulus_exception':'Native plated annuli remain intentionally exempt from ordinary .130mm trace-width rules. Their exact unchanged diameter/drill/slot geometry and approved manufacturing floors are checked separately. Filling a terminal land for this attachment test does not claim copper exists in its drilled hole.','limits':'Bounded CAD attachment proof only; not thermal/current-capacity or physical process certification.'}
 assert sha(a.candidate)==a.sha256;a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'errors':errors,'plane_only_pads':len(untraced),'ground_vias':len(ground_vias),'planes':[{'layer':q['layer'],'terminals':q['terminal_count'],'failed':sum(not x['connected_to_main_broad_plane_at_01302mm'] for x in q['terminals'])} for q in zones]},indent=2))
if __name__=='__main__':main()
