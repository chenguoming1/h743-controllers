#!/usr/bin/env python3
"""Host-only source identity and synthetic mutation controls; no CAD execution."""
import copy
import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('pair', HERE / 'prepare_native7_u15_io4_pair_v1.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class PairedSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan, cls.preview, _ = p.build(ROOT)
        cls.raw, _, cls.m = p.load_sources(ROOT)

    def reject_plan(self, mutate):
        got = copy.deepcopy(self.plan)
        mutate(got)
        with self.assertRaisesRegex(ValueError, 'exact source-derived'):
            p.validate(got, self.plan)

    def test_exact_plan_valid(self):
        self.assertTrue(p.validate(self.plan, self.plan))
        self.assertEqual(self.plan['netlist']['expected_assigned_nodes'], 506)
        self.assertEqual(self.plan['netlist']['expected_named_nets'], 127)

    def test_reject_stale_source_board(self):
        self.reject_plan(lambda x: x['source'].__setitem__(p.SRC + '/f722-heli.kicad_pcb', '0'*64))

    def test_reject_unused_net_name_swap(self):
        self.reject_plan(lambda x: x['pad_net_delta'][0].__setitem__('after_net', 'unconnected-(U15-IO4-Pad5)'))

    def test_reject_physical_pin_renumber(self):
        self.reject_plan(lambda x: x['pad_net_delta'][2].__setitem__('key', 'U15.1'))

    def test_reject_NC_as_actual_clamp(self):
        self.reject_plan(lambda x: x['planned_contract_successors'][1]['checks'][5].__setitem__('clamp','U15.6'))

    def test_reject_internal_NC_bond(self):
        self.reject_plan(lambda x: x['actual_IO_inventory'].__setitem__('no_internal_NC_edges', False))

    def test_reject_old_terminal_obligation(self):
        self.reject_plan(lambda x: x['terminal_group_delta'].__setitem__('required_external_RX_group',['J11.1','U15.10','U15.1','R34.1']))

    def test_reject_unrelated_copper_removal(self):
        self.reject_plan(lambda x: x['copper_scope']['removal_records'].pop())

    def test_memory_preview_retains_complete_other_syntax(self):
        p.verify_metadata_preview(self.raw,self.preview,self.m)
        self.assertEqual(len(self.plan['schematic']['operations']),9)

    def test_missing_NC_move_fails(self):
        got = dict(self.preview)
        op = self.plan['schematic']['operations'][4]
        got['io-ports.kicad_sch'] = got['io-ports.kicad_sch'].replace(op['after'],op['before'])
        with self.assertRaises(ValueError): p.verify_metadata_preview(self.raw,got,self.m)

    def test_unrelated_TX_wire_move_fails(self):
        got = dict(self.preview)
        got['io-ports.kicad_sch'] = got['io-ports.kicad_sch'].replace('(xy 358.14 166.37)', '(xy 358.15 166.37)')
        with self.assertRaisesRegex(ValueError,'unrelated metadata syntax'): p.verify_metadata_preview(self.raw,got,self.m)

    def test_actual_IO1_type_retained_passive(self):
        op = self.plan['schematic']['operations'][-1]
        pins = p.pins_of(self.m,self.m.parse(op['after']))
        self.assertEqual(self.m.val(pins['1']),'passive')
        self.assertEqual(self.m.val(pins['6']),'passive')
        self.assertEqual(self.m.val(pins['10']),'no_connect')

    def test_unrelated_symbol_pin_change_fails(self):
        got = dict(self.preview)
        got['library/F722_Heli.kicad_sym'] = got['library/F722_Heli.kicad_sym'].replace('(pin power_in', '(pin passive',1)
        with self.assertRaisesRegex(ValueError,'unrelated metadata syntax'): p.verify_metadata_preview(self.raw,got,self.m)

    def test_exact_contract_delta_only(self):
        import json
        for contract in self.plan['planned_contract_successors']:
            old=json.loads(self.raw[contract['source_path']])['checks']
            new=copy.deepcopy(contract['checks'])
            self.assertEqual(next(x for x in new if x['id']=='published-06')['clamp'],'U15.5')
            next(x for x in new if x['id']=='published-06')['clamp']='U15.1'
            self.assertEqual(old,new)


class SyntheticNetlist(unittest.TestCase):
    def source(self):
        return b'''<export><components><comp ref="U15"><value>TPD</value><libsource part="TPD4E05U06_RoutePads_NC9_NC10"/></comp><comp ref="R34"><value>22</value></comp></components><libparts><libpart lib="F722_Heli" part="TPD4E05U06_RoutePads_NC9_NC10"><pins><pin num="6" type="no_connect"/><pin num="10" type="passive"/></pins></libpart></libparts><nets>
        <net name="PORT_C_RX_EXT" code="15" class="Default"><node ref="U15" pin="1" pinfunction="IO1_1" pintype="passive"/><node ref="U15" pin="10" pinfunction="NC10_10" pintype="passive"/><node ref="R34" pin="1" pintype="passive"/></net>
        <net name="unconnected-(U15-IO4-Pad5)" code="18" class="Default"><node ref="U15" pin="5" pinfunction="IO4_5" pintype="passive+no_connect"/></net>
        <net name="unconnected-(U15-NC6-Pad6)" code="19" class="Default"><node ref="U15" pin="6" pinfunction="NC6_6" pintype="no_connect"/></net></nets></export>'''

    def candidate(self):
        src=self.source(); root=ET.fromstring(src)
        root.find('./components/comp/libsource').set('part',p.NEW)
        root.find('./libparts/libpart').set('part',p.NEW)
        for pin in root.findall('./libparts/libpart/pins/pin'): pin.set('type', {'6':'passive','10':'no_connect'}[pin.get('num')])
        nets=root.find('nets');nets.clear()
        for code,(name,row) in enumerate(p.expected_netlist(src).items(),100):
            net=ET.SubElement(nets,'net',name=name,code=str(code),attrib={'class':row['net_class']})
            for node in row['nodes']: ET.SubElement(net,'node',attrib=node)
        return root

    def check(self,root):
        return p.verify_netlist(ET.tostring(root),p.expected_netlist(self.source()),p.expected_netlist_components_and_libraries(self.source()))

    def test_fresh_numeric_codes_allowed(self): self.assertTrue(self.check(self.candidate()))

    def test_independent_expected_four_pin_semantics(self):
        expected={
            'PORT_C_RX_EXT':{'net_class':'Default','nodes':[
                {'ref':'R34','pin':'1','pintype':'passive'},
                {'ref':'U15','pin':'5','pinfunction':'IO4_5','pintype':'passive'},
                {'ref':'U15','pin':'6','pinfunction':'NC6_6','pintype':'passive'}]},
            'unconnected-(U15-IO1-Pad1)':{'net_class':'Default','nodes':[
                {'ref':'U15','pin':'1','pinfunction':'IO1_1','pintype':'passive+no_connect'}]},
            'unconnected-(U15-NC10-Pad10)':{'net_class':'Default','nodes':[
                {'ref':'U15','pin':'10','pinfunction':'NC10_10','pintype':'no_connect'}]}}
        self.assertEqual(p.expected_netlist(self.source()),expected)

    def test_XML_numeric_code_alias_fails(self):
        root=self.candidate();nets=root.findall('./nets/net');nets[1].set('code',nets[0].get('code'))
        with self.assertRaisesRegex(ValueError,'XML net code'):self.check(root)

    def test_unrelated_component_value_fails(self):
        root=self.candidate();root.find('./components/comp[@ref="R34"]/value').text='47'
        with self.assertRaisesRegex(ValueError,'component/library'): self.check(root)

    def test_wrong_NC_electrical_type_fails(self):
        root=self.candidate();root.find('./nets/net/node[@pin="6"]').set('pintype','no_connect')
        with self.assertRaisesRegex(ValueError,'semantic parity'): self.check(root)

    def test_missing_RX_endpoint_fails(self):
        root=self.candidate();net=root.find('./nets/net[@name="PORT_C_RX_EXT"]');net.remove(net.find('node[@ref="R34"]'))
        with self.assertRaisesRegex(ValueError,'semantic parity'): self.check(root)


class SyntheticNative(unittest.TestCase):
    def pair(self):
        source={'footprints':[{'uuid':'fixed','xy':[25.5,17.6]}], 'zones':[], 'objects':[]}
        before={'1':p.RX,'10':p.RX,'5':'unconnected-(U15-IO4-Pad5)','6':'unconnected-(U15-NC6-Pad6)'}
        for pin,uid in p.PINS.items():
            source['objects'].append(dict(kind='pad',uuid=uid,key='U15.'+pin,ref='U15',number=pin,net=before[pin],net_code=15 if pin in ['1','10'] else int(pin)+20,xy=[1,int(pin)],copper={'F.Cu':'fixed contour'}))
        source['objects'].append(dict(kind='pad',uuid='unrelated',key='U1.28',ref='U1',number='28',net='PORT_C_RX_MCU',net_code=12,xy=[2,2]))
        got=copy.deepcopy(source)
        names={p.RX:101,'unconnected-(U15-IO1-Pad1)':102,'unconnected-(U15-NC10-Pad10)':103,'PORT_C_RX_MCU':104}
        for obj in got['objects']:
            if obj['ref']=='U15':obj['net']=p.PIN_NETS[obj['number']]
            obj['net_code']=names[obj['net']]
        return source,got

    def test_exact_four_nets_and_fresh_codes(self):
        a,b=self.pair();self.assertEqual(p.verify_pad_metadata(a,b)['untouched_pads'],1)

    def test_pad_contour_mutation_fails(self):
        a,b=self.pair();b['objects'][2]['copper']['F.Cu']='shifted'
        with self.assertRaisesRegex(ValueError,'geometry or net'):p.verify_pad_metadata(a,b)

    def test_mcu_pin_change_fails(self):
        a,b=self.pair();b['objects'][-1]['number']='29'
        with self.assertRaisesRegex(ValueError,'geometry or net'):p.verify_pad_metadata(a,b)

    def test_net_code_alias_fails(self):
        a,b=self.pair();b['objects'][-1]['net_code']=101
        with self.assertRaisesRegex(ValueError,'aliases'):p.verify_pad_metadata(a,b)

    def test_pose_change_fails(self):
        a,b=self.pair();b['footprints'][0]['xy'][0]+=.25
        with self.assertRaisesRegex(ValueError,'poses fixed'):p.verify_pad_metadata(a,b)

    def test_zero_code_for_nonempty_net_fails(self):
        a,b=self.pair();b['objects'][-1]['net_code']=0
        with self.assertRaisesRegex(ValueError,'zero reserved'):p.verify_pad_metadata(a,b)

    def test_negative_native_code_fails(self):
        a,b=self.pair();b['objects'][-1]['net_code']=-1
        with self.assertRaisesRegex(ValueError,'zero reserved'):p.verify_pad_metadata(a,b)


if __name__=='__main__':unittest.main()
