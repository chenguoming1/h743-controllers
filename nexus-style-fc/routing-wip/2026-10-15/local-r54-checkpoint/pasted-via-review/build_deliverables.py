from geometry import *
from datetime import datetime,timezone
base=SOURCE.parent.parent
contacts=json.loads(OUT.joinpath('static-contacts.json').read_text())
probes={v['via_uuid']:v for v in json.loads(OUT.joinpath('finite-land-probes.json').read_text())}
options={v['via_uuid']:v for v in json.loads(OUT.joinpath('simple-routing-only-options.json').read_text())}
roles={
'C3':('capacitor_power','MCU pin 48 3V3 decoupling feed','Retain B.Cu and In3.Cu 0.25 mm branches and the C3 power pad. Minimum local investigation: a C3 escape with its B.Cu decoupling path and both In3.Cu donor endpoints; nearest conservative land probes meet 3V3_SENS/R6 obstacles.'),
'J3':('other_ground','J3 grounded connector mounting/shield land','Retain connector ground and F.Cu return d05141d2. Nearby conservative points are limited by drill spacing and board edge; inspect one connector-ground exit corridor without moving the footprint.'),
'J4':('other_ground','J4 grounded mounting land and opposite-side C27 buck-input return','Treat as dual-side capacitor return. A geometrically open south land probe fails hole spacing. Inspect J4/C27 joint corridor and keep C27 close to a solid return.'),
'J5':('other_ground','J5 grounded mounting land and opposite-side C20 flash decoupling return','The only finite conservative land candidate is 2.03 mm away at (119.975,124.405); this is NOT an approved option because the C20 return and both-layer paths are unproved. Inspect a shorter coordinated flash/connector-ground corridor.'),
'J6':('other_ground','USB-C B12 local ground return','A bounded F.Cu full-land-width dogbone candidate is supplied. Native zone/return validation must show J6 ground remains connected to the same solid In1/In4 ground regions and other USB/ESD return stitching is unchanged.'),
'C19':('capacitor_power','TPS70933 LDO output-capacitor ground return','Retain the approved C19 placement/value and short U10/C19 ground loop. Conservative probes collide with 3V3 copper and approach U10 EN; inspect complete two-capacitor/LDO return corridor, never reconnect EN.'),
'C24':('capacitor_power','TPS62130 output-capacitor ground shared with opposite-side J2 mounting land','Dual-sided pasted pads: both F J2.5 and B C24.2 must clear the drill. Preserve buck-output return, J2 return, both source track donors and independent second J2 via. Conservative south point conflicts with that second via’s hole; do not merge or delete vias.'),
'J2':('other_ground','J2 mounting/shield ground, separate from the C24-sharing via','A bounded 0.25 mm south relocation with a 0.45 mm F.Cu dogbone is supplied. Keep the distinct C24-sharing via in place; check both ground-plane joins and masked solder separation after native refill.'),
'U2_GND':('other_ground','ICM-42688-P GND pin 10 and local IMU return','Retain all three F.Cu track contacts plus pad10 and solid return-plane joins. Finite conservative probes hit adjacent IMU pads, IMU_CS and power routes; investigate the entire local IMU fanout rather than deleting this return.'),
'R14':('other_ground','TPS2116 PR1 threshold divider lower-leg ground','Preserve R14’s ground reference. Conservative probes are occupied by PR1, LED and 5V_BUCK; inspect a nearby quiet reference-ground connection, with no change to divider parts/nets.'),
'U11':('other_ground','SRV05-4 ESD/clamp ground also touching C21 TPS62130 input-cap ground','Preserve BOTH F.Cu U11.2 surge-return path and B.Cu C21.2 input-cap return. A left shift meets SBUS/TAIL, and other directions meet RPM/VSYS/DSM_DATA/C21 paste. Investigate a bounded U11/C21 all-layer corridor with explicit two-sided full-width ties and local ground-plane continuity; no single via deletion.'),
'C26':('capacitor_power','5 V bus bulk capacitor ground','Retain F.Cu return f37ef651 at its original 0.127 mm width or greater. Nearest conservative north probe needs a coordinated 5V route shift; inspect capacitor return and power-mux loop, not netlist continuity alone.'),
'C9':('capacitor_power','STM32F722 VCAP_1 4.7 uF ground return','Do not lengthen or remove the core-regulator capacitor return casually. Nearest conservative exit meets USB_DP and IMU_CS; inspect the complete VCAP/C9/GND local loop together with nearby USB clearance.'),
'U5':('thermal_ground','TPS62130 exposed thermal pad17, AGND pin6, and opposite-side C15 IMU VDDIO return','Only GND via within 2 mm copper-edge distance of EP17. Preserve thermal barrel, pad17/AGND contacts, C15 and six direct track contacts. Nine small-displacement probes fail source aperture or unrelated-copper checks; review exact blockers before any larger coordinated routing transaction. Thermal sufficiency requires actual losses/load/ambient/copper geometry; no deletion or thermal-equivalence claim.'),
'RPM':('signal','STM32F722 PA3/RPM pad16 via to In3.Cu','Retain pad16 and both In3.Cu source donors at 0.127 mm, including the short branch. Conservative outward exit is obstructed by GND/5V and nearby C6; investigate a full B.Cu escape plus In3.Cu donor rewrite.'),
'U3':('capacitor_power','DPS368 VDDIO pad6 supply and decoupling network','Retain all F.Cu and In2.Cu 0.25 mm source tracks and pad6. Conservative probes run into U3 GND, U1 pads, DSM_TX and other internal routes; review the local barometer fanout/decoupling corridor.'),
'SPI1_MISO':('signal','ICM-42688-P SDO pad1 via to In2.Cu','Retain U2.1 and both In2.Cu donors at 0.127 mm. Conservative probes meet VCAP, DSM_DATA, nearby GND vias and U2.2; investigate local IMU escape with ground-return continuity.'),
'I2C1_SCL':('signal','STM32F722 PB8/I2C1_SCL pad61 via to In2.Cu','Retain B.Cu and In2.Cu branches at 0.127 mm and pad61 full-width connection. Nearest conservative outward exit hits R1/BOOT0; investigate a bounded coupled BOOT0/SCL escape without changing nets or pull-down.')}
records=[]
for uid,pr in probes.items():
 v=items[uid];cp=[c for c in contacts if c['via']['uuid']==uid]
 refs=[c['pad']['ref'] for c in cp]
 key='C24' if 'C24' in refs else ('U2_GND' if v['net']=='GND' and 'U2' in refs else (v['net'] if v['net'] in ['RPM','SPI1_MISO','I2C1_SCL'] else refs[0]))
 cat,role,nextstep=roles[key]
 donor=[]
 for d in items.values():
  if d['uuid']==uid or d['net']!=v['net']:continue
  dist=gap(v,d)
  if dist<=1e-9:
   ent=dict(d,source_via_copper_contact_gap_mm=dist)
   if d['kind']=='segment':ent['complete_fixed_donor_endpoints_to_preserve']=[d['start'],d['end']]
   donor.append(ent)
 zmem=[]
 for z in zones:
  if z['net']!=v['net']:continue
  ix=[p['index'] for p in z['fill_polygons'] if contains(v['at'],p['points'])]
  if ix:zmem.append(dict(zone_uuid=z['uuid'],layer=z['layer'],source_fill_polygon_indices=ix))
 rec=dict(via=v,classification=cat,function=role,pasted_pad_contacts=cp,all_direct_same_net_copper_donors=donor,source_ground_fill_centre_memberships=zmem,zone_membership_is_not_a_finite_width_path_or_thermal_proof=True,smallest_further_investigation=nextstep,finite_land_probe_summary=pr,candidate=options.get(uid),proposal_status='Geometry-qualified bounded candidate, native/process/return checks pending' if uid in options else 'No complete routing-only option proved in this read-only review')
 records.append(rec)
paths=[SOURCE,SOURCE.with_suffix('.kicad_sch'),SOURCE.with_suffix('.kicad_pro'),SOURCE.with_suffix('.kicad_dru'),SOURCE.parent/'library/NexusFC.kicad_sym',base/'geometry-verification.json',base/'verification.json',base/'native-receipt.json',base/'native-drc.json',base/'evidence-manifest.json',Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015/checkpoint-08/nexus-style-fc/tools/design.py'),Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015/via-clearance-study/all-copper-geometry.json')]
manifest=[dict(path=str(p),sha256=sha(p.read_bytes()),bytes=p.stat().st_size) for p in paths]
archive=json.loads(paths[-1].read_text());padsnative=[p for p in archive if p['kind']=='pad']
checks=[dict(uuid=p['uuid'],position_difference_mm=math.dist(items[p['uuid']]['at'],p['position']),angle_difference_deg=abs(items[p['uuid']]['rotation_deg']-p['angle'])) for p in padsnative]
result=dict(review_time_utc=datetime.now(timezone.utc).isoformat(),source_sha256=EXPECTED,source_files=manifest,method='Native-text parser and exact analytic convex shapes; no KiCad import/run, no solver, no source board edits. 19 drill-to-pasted-copper contacts reproduce sealed native totals. Pads with absent serialized rotation correctly use absolute 0 degrees.',validation=dict(unsupported_copper_shapes=unsupported,native_pad_crosscheck_count=len(checks),maximum_position_difference_mm=max(c['position_difference_mm'] for c in checks),maximum_rotation_difference_deg=max(c['angle_difference_deg'] for c in checks)),summary=dict(unique_vias=18,contact_pairs=19,same_net_pairs=19,by_classification=dict(collections.Counter(r['classification'] for r in records)),fully_qualified_manufacturing_remedies=0,bounded_static_routing_candidates=len(options)),via_size_mm=.45,drill_mm=.2,board_via_process=dict(tenting_front=True,tenting_back=True,covering=False,plugging=False,capping=False,filling=False),qualification='The contact metric is drill versus the copper shape of a pasted SMD pad, not a final mask/paste-Gerber/CAM certification. All listed affected pads have source mask and paste layers and no local reductions; exact export/CAM inspection remains required.',vias=records)
OUT.joinpath('per-via-review.json').write_text(json.dumps(result,indent=2))
assert sha(SOURCE.read_bytes())==EXPECTED
OUT.joinpath('source-manifest.json').write_text(json.dumps(manifest,indent=2))
print(result['summary']);print(result['validation'])
