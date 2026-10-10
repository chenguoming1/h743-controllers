"""Small-candidate01 source-bound prototype screen. No layout edits or field solve."""
import hashlib
import heapq
import json
import math
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
CAND = ROOT / 'ordinary-routing/tests/joint-flash-group/small-candidate01'
EXPECTED = '14dea1df09ea9d800bf66a6d74eb5f0dac33a8705161e9ed1a02f2e11f3b58b8'
EXPECTED_NATIVE = '694974b065fedf387f1b66c004f440cc138b0075549fd6383e18e595c139cc53'
EXPECTED_HANDOFF = '31c2e16c27c8458734e7e46ae6bbb4f114ed3580552e45a3ffeae5601aa69fca'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())
pcb = CAND / 'f722-heli.kicad_pcb'
native = read(CAND / 'f722-heli.native.json')
proposal = read(CAND / 'proposal.json')
construction = read(CAND / 'construction-provenance.json')
handoff = read(CAND / 'route-handoff.json')
assert sha(CAND / 'route-handoff.json') == EXPECTED_HANDOFF
assert sha(CAND / 'f722-heli.native.json') == handoff['native_sha256'] == EXPECTED_NATIVE
assert handoff['board_sha256'] == EXPECTED
baseline = read(ROOT / 'ordinary-routing/candidate54/f722-heli.native.json')
assert sha(pcb) == native['board_sha256'] == construction['board_sha256'] == EXPECTED
assert construction['proposal_sha256'] == sha(CAND / 'proposal.json')
assert construction['source_board_sha256'] == baseline['board_sha256'] == proposal['source_board_sha256']
assert len(proposal['routes']) == 21 and len(proposal['vias']) == 13
assert len(construction['removed_source_records']) == 75
byid = {o['uuid']: o for o in native['objects']}
oldid = {o['uuid']: o for o in baseline['objects']}
pads = {o['key']: o for o in native['objects'] if o['kind'] == 'pad'}
fps = {f['ref']: f for f in native['footprints']}
oldfps = {f['ref']: f for f in baseline['footprints']}
for r, ids in zip(proposal['routes'], construction['routes']):
    assert len(ids) == len(r['points']) - 1
    for uid, a, b in zip(ids, r['points'], r['points'][1:]):
        o = byid[uid]
        assert (o['start'], o['end'], o['width'], o['net'], list(o['copper'])) == (a, b, r['width'], r['net'], [r['layer']])
for v, uid in zip(proposal['vias'], construction['vias']):
    o = byid[uid]
    assert o['xy'] == v['xy'] and o['net'] == v['net'] and o['width'] == .45 and o['drill']['width'] == .2
assert all(x['uuid'] not in byid for x in construction['removed_source_records'])
assert [x['after']['ref'] for x in construction['changed_footprint_records']] == ['R44']
for ref in fps:
    assert fps[ref]['value'] == oldfps[ref]['value']
assert fps['R44']['xy'] == oldfps['R44']['xy'] == [25.8, 16.0]
assert fps['R44']['angle'] - oldfps['R44']['angle'] == -180
expected_nets = {'R38.1':'DSM_RX_EXT','R38.2':'DSM_RX_MCU','U1.43':'DSM_RX_MCU',
 'R71.1':'+3V3_CORE','R71.2':'DSM_RX_MCU','J12.3':'DSM_RX_EXT','D7.1':'DSM_RX_EXT','D7.2':'GND',
 'R5.1':'+3V3_CORE','R5.2':'FLASH_WP_N','U3.3':'FLASH_WP_N',
 'R6.1':'+3V3_CORE','R6.2':'FLASH_HOLD_N','U3.7':'FLASH_HOLD_N',
 'R42.1':'+5V_PERIPH','R42.2':'ADC_BUS','R43.1':'ADC_BUS','R43.2':'ADC_DIV_MID',
 'R44.1':'ADC_DIV_MID','R44.2':'GND','C31.1':'ADC_BUS','C31.2':'GND','U1.10':'ADC_BUS',
 'U1.3':'LED_GREEN_K','D1.1':'LED_GREEN_K','R10.1':'+3V3_CORE','R10.2':'D1_A','D1.2':'D1_A'}
assert all(pads[k]['net'] == v for k, v in expected_nets.items())
expected_values = {'R38':'22R / 1%','R71':'100k / 1% / ROM RX idle', 'R5':'10k / 1%', 'R6':'10k / 1%',
 'R42':'68.0k / 0.1%','R43':'16.0k / 0.1%','R44':'16.0k / 0.1%', 'C31':'220nF / 16V / X7R', 'R10':'2.2k / 1%','R11':'2.2k / 1%'}
assert all(fps[k]['value'] == v for k, v in expected_values.items())
thickness = {a: float(b) for a,b in re.findall(r'\(layer "([^"\n]+\.Cu)"\s+\(type "copper"\)\s+\(thickness ([0-9.]+)\)', pcb.read_text())}
dielectrics = [{'index':int(a),'thickness_mm':float(b),'material':c,'epsilon_r':float(d)} for a,b,c,d in
 re.findall(r'\(layer "dielectric (\d+)"\s+\(type "[^"\n]+"\)\s+\(thickness ([0-9.]+)\)\s+\(material "([^"\n]+)"\)\s+\(epsilon_r ([0-9.]+)\)', pcb.read_text())]
assert len(dielectrics) == 5
rho = 1.724e-8
def measure(o):
    layer = next(iter(o['copper']))
    length = math.dist(o['start'], o['end'])
    return {'uuid':o['uuid'],'layer':layer,'width_mm':o['width'],'length_mm':length,
      'trace_resistance_ohm_20C':rho*length*1000/(o['width']*thickness[layer])}
def net_rows(net):
    return [measure(o) for o in native['objects'] if o['kind']=='track' and o['net']==net]
def summary(rows):
    layers = defaultdict(float)
    for r in rows: layers[r['layer']] += r['length_mm']
    return {'length_mm':sum(r['length_mm'] for r in rows),'by_layer_mm':dict(layers),
      'trace_resistance_ohm_20C':sum(r['trace_resistance_ohm_20C'] for r in rows)}
outer_er = dielectrics[0]['epsilon_r']
near_h = dielectrics[1]['thickness_mm']
far_h = dielectrics[2]['thickness_mm'] + thickness['In3.Cu'] + dielectrics[3]['thickness_mm']
def line_sensitivity(rows):
    cases = []
    for label,h,er in [('symmetric_far_planes_er4_23',far_h,4.23),('symmetric_near_planes_er4_4',near_h,4.4)]:
        cap = delay = 0
        for r in rows:
            w,t,le = r['width_mm'],thickness[r['layer']],r['length_mm']
            if r['layer'] in ['F.Cu','B.Cu']:
                c = .67*(outer_er+1.41)/math.log(5.98*dielectrics[0]['thickness_mm']/(.8*w+t))/25.4
                td = 85*math.sqrt(.475*outer_er+.67)/25.4/1000
            else:
                c = 1.41*er/math.log(3.81*h/(.8*w+t))/25.4
                td = 85*math.sqrt(er)/25.4/1000
            cap += le*c; delay += le*td
        cases.append({'case':label,'trace_only_pF':cap,'conditional_uniform_line_flight_time_ns':delay})
    return cases
def path(net, source, target):
    # Exact centerline graph: tracks plus zero-length cross-layer via edges.
    # No field solve; pad and vertical via electrical lengths are excluded.
    graph = defaultdict(list)
    def edge(a,b,weight,uid):
        graph[a].append((b,weight,uid));graph[b].append((a,weight,uid))
    for o in native['objects']:
        if o['net'] != net: continue
        if o['kind'] == 'track':
            ly = next(iter(o['copper']));a=(*o['start'],ly);b=(*o['end'],ly)
            edge(a,b,math.dist(o['start'],o['end']),o['uuid'])
        elif o['kind']=='via':
            nodes=[(*o['xy'],ly) for ly in o['copper']]
            for node in nodes[1:]:edge(nodes[0],node,0,o['uuid'])
    start=(*pads[source]['xy'],next(iter(pads[source]['copper'])))
    finish=(*pads[target]['xy'],next(iter(pads[target]['copper'])))
    heap=[(0,start,[])];done=set()
    while heap:
        distance,node,ids=heapq.heappop(heap)
        if node in done:continue
        done.add(node)
        if node==finish:
            trackids=[u for u in ids if byid[u]['kind']=='track']
            rows=[measure(byid[u]) for u in trackids]
            return {**summary(rows),'source':source,'target':target,'track_uuids':trackids,
               'via_uuids':list(dict.fromkeys(u for u in ids if byid[u]['kind']=='via')),
               'line_sensitivity':line_sensitivity(rows)}
        for other,weight,uid in graph[node]:
            if other not in done:heapq.heappush(heap,(distance+weight,other,ids+[uid]))
    raise AssertionError((net,source,target,'No exact centerline path'))
nets=['LED_GREEN_K','DSM_RX_MCU','DSM_RX_EXT','FLASH_HOLD_N','FLASH_WP_N','ADC_BUS','ADC_DIV_MID','PORT_A_RX_MCU']
inventory={net:{**summary(net_rows(net)), 'via_count':sum(o['net']==net and o['kind']=='via' for o in native['objects']),
 'line_sensitivity':line_sensitivity(net_rows(net))} for net in nets}
dsm_main=path('DSM_RX_MCU','R38.2','U1.43')
dsm_to_pullup=path('DSM_RX_MCU','R38.2','R71.2')
branch_ids=set(dsm_to_pullup['track_uuids'])-set(dsm_main['track_uuids'])
branch_rows=[measure(byid[u]) for u in sorted(branch_ids)]
assert set(dsm_main['track_uuids'])|branch_ids == {r['uuid'] for r in net_rows('DSM_RX_MCU')}
assert len(dsm_main['via_uuids'])==5
green=path('LED_GREEN_K','U1.3','D1.1')
assert abs(green['length_mm']-71.87564991794922)<1e-9
adc_mid=path('ADC_DIV_MID','R43.2','R44.1')
adc_to_pin=path('ADC_BUS','R42.2','U1.10')
adc_to_cap=path('ADC_BUS','C31.1','U1.10')
for uid in adc_to_cap['track_uuids']:
    assert {k:v for k,v in byid[uid].items() if k!='net_code'} == {k:v for k,v in oldid[uid].items() if k!='net_code'}
gnd_route=proposal['routes'][19]
assert gnd_route['net']=='GND' and gnd_route['points'][0]==pads['R44.2']['xy']
gnd_via=byid[construction['vias'][11]]
assert gnd_route['points'][-1]==gnd_via['xy']==[25.08,15.78]
gnd_track=byid[construction['routes'][19][0]]
assert [o['uuid'] for o in native['objects'] if o['kind']=='track' and o['net']=='GND' and gnd_via['xy'] in [o['start'],o['end']]]==[gnd_track['uuid']]
gnd=measure(gnd_track)
rth=68000*32000/100000
sample=480/(216e6/2/8)
settle=(rth*1.001+6000+2)*7e-12*math.log(2**14)
adc={
 'values':{k:expected_values[k] for k in ['R42','R43','R44','C31']},'topology':'R42 from +5V_PERIPH to ADC_BUS; R43 then R44 from ADC_BUS through ADC_DIV_MID to GND; C31 from ADC_BUS to GND; U1.10 PC2 on ADC_BUS.',
 'gain_nominal':.32,'Rth_ohm':rth,'nominal_C31_F':220e-9,'nominal_RC_s':rth*220e-9,'nominal_corner_Hz':1/(2*math.pi*rth*220e-9),
 'nominal_divider_current_at_5V_A':5/100000,'divider_gain_at_resistor_tolerance_extremes':[31968/(68068+31968),32032/(67932+32032)],
 'R42_to_MCU':adc_to_pin,'C31_to_MCU_unchanged_tracks':adc_to_cap,'R43_to_R44':adc_mid,
 'R44_exclusive_local_GND_track':gnd,'R44_ground_via_uuid':gnd_via['uuid'],
 'R44_ground_track_only_DC_drop_at_5V_V':gnd['trace_resistance_ohm_20C']*5/100000,
 'local_via_has_only_R44_track_connection':True,'plane_impedance_and_other_ground_current_not_bounded':True,
 'conditional_acquisition':{'HCLK_Hz_assumed':216e6,'APB2_divider':2,'ADC_divider':8,'sample_cycles':480,'sample_time_s':sample,
 'resolution_bits':12,'RADC_max_ohm':6000,'CADC_max_F':7e-12,'external_resistor_tolerance':.001,'trace_series_sensitivity_ohm':2,
 'quarter_LSB_simple_RC_settling_s':settle,'sample_over_settle_ratio':sample/settle,
 'quarter_LSB_charge_sharing_min_effective_C31_F':7e-12*2**14,'effective_C31_not_guaranteed':True,
 'full_scale_filter_settling_to_quarter_LSB_s':rth*220e-9*math.log(2**14)},
 'new_ADC_BUS_trace_only_capacitance_vs_C31':[v['trace_only_pF']/220000 for v in inventory['ADC_BUS']['line_sensitivity']],
 'MID_trace_capacitance_is_at_different_node_and_not_added_directly_to_C31':True}
parts=read(CAND/'parts.json')
result={
 'schema':'f722-small-signal-review54/v1','board_sha256':EXPECTED,'native_sha256':sha(CAND/'f722-heli.native.json'),
 'sealed_native_handoff_sha256':EXPECTED_HANDOFF,
 'proposal_sha256':sha(CAND/'proposal.json'),'construction_sha256':sha(CAND/'construction-provenance.json'),
 'scope':'Read-only prototype electrical screen of exact small-candidate01. No native edits, waveform simulation, total load extraction, ESD, AC, EMI or hardware qualification.',
 'checks':{'native_recipe_records_exact':True,'all_BOM_values_unchanged':True,'only_footprint_change_R44_in_place_180deg':True,'terminal_nets_match':True},
 'terminal_mapping':{k:{'net':pads[k]['net'],'xy':pads[k]['xy'],'uuid':pads[k]['uuid']} for k in expected_nets},
 'BOM':{ref:{'value':fps[ref]['value'],**parts[ref]} for ref in ['R38','R71','D7','U1','U3','R5','R6','R42','R43','R44','C31','R10','D1']},
 'stackup_copper_thickness_mm':thickness,'stackup_dielectrics':dielectrics,'native_net_inventory':inventory,
 'line_model_limit':'ADI MT-094 equations4/8/6/10: outer ideal microstrip and two symmetric inner sensitivity cases replacing actual asymmetric stack. Continuous reference, no mask, return gaps, vias, pads, device/package/cable/probe load or adjacent-copper coupling. Values are neither total-load bounds nor measured impedances. Track lengths exclude pad and vertical-via travel.',
 'DSM':{'main_path':dsm_main,'pullup_branch':{**summary(branch_rows),'track_uuids':sorted(branch_ids),'line_sensitivity':line_sensitivity(branch_rows)},
 'recipe_new_copper_mm':proposal['route_lengths_by_net_mm']['DSM_RX_MCU'],
 'retained_copper_mm':inventory['DSM_RX_MCU']['length_mm']-proposal['route_lengths_by_net_mm']['DSM_RX_MCU'],
 'branch_junction_xy':[37.3,19.3],'branch_junction_via_uuid':construction['vias'][12],
 'baud_if_SPEKTRUM_selected':115200,'bit_time_us':1e6/115200,'format':'8 data, no parity, 1 stop; default uninverted, halfDuplex=0; ordinary DSM receiver operation MODE_RX.',
 'configured_receiver_provider_and_port_not_fixed_by_target':True,'installed_firmware_not_verified':True,
 'GPIO_receive_path':'U1.43 PA10 / USART1_RX AF7; stock ordinary RX uses AF_PP LOW, no internal pull; input edge governed by external receiver and interconnect.',
 'startup_bind':'Conditional spektrumBind uses rx pin for non-half-duplex default, push-pull LOW speed;120us low/high pulses after60ms; R38 is at far end of board trace in this drive direction.',
 'external_receiver_voltage_edges_drive_impedance_cable_unknown':True,
 'TVS':'D7 ESD9M5.0ST5G shunts DSM_RX_EXT to GND before R38. onsemi Rev9:2.5pF maximum at0V/1MHz/25C,1uA leakage at5V/25C; no board-level clamp/ESD qualification.',
 'PA10_datasheet_CIO_typical_pF':5,'R71_ohm':100000,'R38_ohm':22,
 'idle_DC_example_at3V3_with_2uA_total_leakage_and_R71_max_V':3.3-2e-6*101000,
 'idle_example_limits':'2uA uses MCU1uA within powered rails plus TVS1uA at25C; receiver leakage, unpowered backfeed and hot leakage not bounded.',
 'weak_pullup_loading_examples':[{'C_total_assumed_pF':c,'R71_max_ohm':101000,'rise_10_90_us':2.197224577*101000*c*1e-6,'to_0p7_supply_us':-math.log(.3)*101000*c*1e-6} for c in [20,50,100]],
 '22R_capacitance_example_not_driver_model':[{'C_total_assumed_pF':c,'tau_22ohm_ns':22*c/1000} for c in [20,50,100]]},
 'GREEN':{**green,'resistor_only_upper_current_mA_3V6':3.6/2178*1000,
 'both_LEDs_conservative_resistor_only_upper_mA':7.2/2178*1000,
 'nominal_trace_drop_mV_at_upper_current':green['trace_resistance_ohm_20C']*3.6/2178*1000,
 'restriction':'PC14 output no more than2MHz and30pF; sink-only LED drive. Existing2k2 resistor and special-pin group current interpretation retain prior conditional limits; no total30pF compliance inferred.',
 'old_recipe_66p981610mm_not_reused':True},
 'FLASH':{'R5_R6_pullups_ohm':10000,'input_leakage_max_uA':2,'Rmax_ohm':10100,'leakage_drop_V':2e-6*10100,
 'DC_margin_to_0p7Vcc_at2p7V_V':.3*2.7-2e-6*10100,'DC_margin_to_0p7Vcc_at3p3V_V':.3*3.3-2e-6*10100,
 'stock_mode':'Target flash_spi_bus2; flash.c selects FLASHIO_SPI; ordinary W25N01G read uses03h, quad6Bh only QUADSPI branch. Device reset clears protection/WP-E. /WP and /HOLD are static10k pullups on this board, not four-bit data lanes.',
 'startup_RC_examples':[{'C_total_assumed_pF':c,'Rmax_ohm':10100,'to_0p7_supply_us':-math.log(.3)*10100*c*1e-6} for c in [10,25,50]],
 'datasheet_CIN_max_pF':6,'datasheet_COUT_max_pF':8,
 'transient_margin_not_proven':True},'ADC':adc,
 'physical_and_installed_configuration_limits':['Return-transfer impedance at all changed layer transitions and plane gaps.','External receiver/cable, actual edges, overshoot, ringing, noise and bind contention.','HOLD/WP startup timing, coupling glitches and real flash traffic.','PC14 total load, paired LED current and switching conditions.','Effective C31 with DC bias/temperature, ground offset/noise, ADC acquisition/large-step settling/calibration.'],
 'qualified':False}
(OUT/'arithmetic.json').write_text(json.dumps(result,indent=2)+'\n')
# Extract distinct correct pin models; do not substitute PC14 for PA10.
ibispath=ROOT/'ordinary-routing/candidate53/conditional-signal-review/stm32f7x2_lqfp64.ibs'
ibis=ibispath.read_text()
for name,pin in [('io8p00_arwsudq_ft_v33','PC14 pin3'),('io8p00_id_otg_ft','PA10 pin43')]:
    match=re.search(r'^\[Model\]\s+'+name+r'\s*$',ibis,re.M)
    ending=re.search(r'^\[Model\]',ibis[match.end():],re.M)
    model=ibis[match.start():match.end()+ending.start()]
    header=model[:model.index('[Pulldown]')]
    ramp=model[model.index('[Ramp]'):model.index('[Rising Waveform]')]
    (OUT/('selected-'+pin.split()[0]+'-model.txt')).write_text('Source '+str(ibispath.relative_to(ROOT))+'\nSHA256 '+sha(ibispath)+'\n'+pin+'; simulation-only, no guaranteed installed-board edge bound.\n'+header+ramp)
print(json.dumps({'board_sha256':EXPECTED,'GREEN':inventory['LED_GREEN_K'],'DSM_main':dsm_main['length_mm'],'DSM_pullup_branch':summary(branch_rows),'ADC_RC_ms':adc['nominal_RC_s']*1000,'ADC_sample_us':sample*1e6,'ADC_simple_settle_us':settle*1e6,'qualified':False},indent=2))
