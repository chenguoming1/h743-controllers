"""Exact exclusive-load inventory and conditional copper-resistance calculation."""
import json,math,re,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(H))
import native7_recovered_context_v3 as adapter
import native7_positive_contact_partition_v1 as positive
start=time.monotonic();g=adapter.load();uid='da1f25da-e0ad-4065-9e0c-44670c3de5fa';leaf=next(q for q in g.BASE if q[0]['uuid']==uid)
assert leaf[0]['net']=='+3V3_IMU' and set(leaf[1])=={'F.Cu'} and leaf[0]['width']==.20
holes=positive.drill_voids(g.BASE,g.N['copper_layers']);before,mb=positive.partition(g.BASE,'+3V3_IMU',g.N['copper_layers'],holes=holes)
after,ma=positive.partition([q for q in g.BASE if q[0]['uuid']!=uid],'+3V3_IMU',g.N['copper_layers'],holes=holes)
r3=g.one_pad('R3.1');isolated=[x for x in after if r3['uuid'] in x];assert len(isolated)==1 and isolated[0]=={r3['uuid']}
main=next(x for x in after if g.one_pad('C12.1')['uuid'] in x)
assert len(before)==1 and len(after)==2
contacts=[]
for record,copper,masks,drill in g.BASE:
 if record['uuid']==uid or record['net']!='+3V3_IMU' or 'F.Cu' not in copper:continue
 overlap=copper['F.Cu'].intersection(leaf[1]['F.Cu'])
 if overlap.area>0:contacts.append({'uuid':record['uuid'],'key':record.get('key'),'kind':record['kind'],'native_record':record,'overlap_area_mm2':overlap.area})
board=ROOT/'recovered-native7/ordinary-routing/tests/native13-access/joint-native-import11-v1/candidates/published-reference02/f722-heli.kicad_pcb'
stack={name:float(thickness) for name,thickness in re.findall(r'\(layer "([^"]+)"\s+\(type "copper"\)\s+\(thickness ([0-9.]+)\)',board.read_text())};assert stack['F.Cu']==.035 and stack['In2.Cu']==.0152
parts=ROOT/'repo/f722-heli/layout-revision/checkpoints/joint-native7-20261010/hardware/parts.json';part=json.loads(parts.read_text())['R3']
foot=next(x for x in g.N['footprints'] if x['ref']=='R3');assert foot['value']=='10k / 1%'
rmin=10000*.99*(1-100e-6*65);imax=3.6/rmin;rho20=.017241;drho=68e-6
rows=[]
for layer in ['F.Cu','In2.Cu']:
 for temperature in [20,85]:
  rho=rho20+drho*(temperature-20)
  resistance_per_mm=rho*.001/(.127*stack[layer])
  rows.append({'layer':layer,'copper_thickness_mm':stack[layer],'width_mm':.127,'copper_temperature_C':temperature,'resistance_ohm_per_mm':resistance_per_mm,'example_length_mm':10,'example_resistance_ohm':10*resistance_per_mm,'drop_V_at_0_4mA_per_mm':.0004*resistance_per_mm,'example_drop_V_at_0_4mA':.0004*10*resistance_per_mm,'example_dissipation_W_at_0_4mA':.0004**2*10*resistance_per_mm})
report={'schema':'f722-native7-exclusive-R3-pullup-leaf-electrical/v2','source':g.binding(),'board_sha256':adapter.digest(board),'parts_sha256':adapter.digest(parts),'script_sha256':adapter.digest(__file__),'selected':False,'R3_part':part,'R3_footprint':{k:foot[k] for k in ['ref','value','fpid','xy','angle','side']},'original_supply_leaf_record':leaf[0],'original_leaf_length_mm':math.dist(leaf[0]['start'],leaf[0]['end']),'source_component_count':len(before),'component_count_without_leaf':len(after),'isolated_R3_supply_component_record_ids':sorted(isolated[0]),'main_supply_component_actual_pads':sorted(q[0]['key'] for q in g.BASE if q[0]['uuid'] in main and q[0].get('key')),'positive_area_leaf_contacts':contacts,'exclusive_R3_load_confirmed':True,'stackup_copper_thickness_mm':stack,'current_assumptions':{'maximum_normal_rail_V':3.6,'minimum_CS_node_normal_V':0,'resistor_nominal_ohm':10000,'initial_tolerance_fraction':.01,'series_TCR_ppm_per_C':100,'maximum_absolute_temperature_offset_from_25C':65,'minimum_resistance_with_tolerance_and_TCR_ohm':rmin,'normal_current_upper_A':imax,'simple_25C_tolerance_current_A':3.6/9900,'calculation_current_envelope_A':.0004,'scope':'Normal pull-up branch current only. Material tolerance/TCR values are source-bound assumptions; aging, fault and AC qualification are not asserted.'},'copper_assumptions':{'rho20_ohm_mm2_per_m':rho20,'temperature_slope_ohm_mm2_per_m_per_K':drho,'formula':'R = rho(T) * length_m / (width_mm * thickness_mm)','conductivity':'100% IACS annealed-copper reference, not a measured fabricated-board guarantee','geometry':'Nominal finished design width and declared board copper thickness. Supplier etch/plating tolerance and any future via resistance require actual candidate binding.'},'resistance_drop_envelope':rows,'sources':[{'title':'TDK ICM-42688-P product specifications; VDD/VDDIO1.71–3.6V and operating-40–85C','url':'https://product.tdk.com/en/search/sensor/mortion-inertial/imu/info?part_no=ICM-42688-P'},{'title':'Uniroyal general thick-film 0402 >10ohm series; +/-100ppm/C','url':'https://www.uni-royal.cn/en/product.php?s=Thick+Film+Chip+Resistors'},{'title':'Royalohm thick-film chip resistor datasheet','url':'https://www.royalohm.com/assets/pdf/products/smd/1.pdf'},{'title':'Copper Information Center IACS resistivity and temperature coefficient','url':'https://help.copper.fyi/hc/en-us/articles/4410229175442-How-does-copper-set-the-standard-for-electrical-conductivity'}],'conclusion':'A .127 mm complete replacement of only this exclusive R3 pull-up supply leaf has negligible calculated DC drop/heating under the declared copper/current assumptions. Its inherited .20 mm width is not established as a current-capacity requirement. All other IMU feeds/returns keep their declared widths. This does not qualify routing, AC/reference, assembly or manufacturing.'}
report['seconds']=time.monotonic()-start;p=H/'native7-R3-pullup-leaf-electrical-v2.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'exclusive_R3_load_confirmed':True,'remaining_main_supply_pads':report['main_supply_component_actual_pads'],'normal_current_upper_mA':1000*imax,'F_85C_10mm_row':rows[1],'receipt_sha256':adapter.digest(p),'seconds':report['seconds']},indent=2))
