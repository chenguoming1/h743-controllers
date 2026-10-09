"""Analytical/adversarial synthetic fixtures only. No project PCB is loaded."""
import copy,json,math,tempfile,unittest
from pathlib import Path
import numpy as np
from shapely.geometry import box,Point,Polygon,MultiPolygon
from copper_fem import Mesh,Refused,Limits,barrel_resistance,native_geometry,polygon_set,contact_spec_geometry
from exact_native_contours import decode_fractured_contour
from test_exact_native_contours import check_fixture
from dc_circuit import solve_circuit
from validate_static import preflight,run_screen,sha256,guard_output
from audit_native_ports import audit_ports

def records(p):return [{'outer':list(p.exterior.coords),'holes':[list(h.coords)for h in p.interiors]}]
def strip(h=.5,extra=None):
    d=box(0,0,4,1)
    return Mesh({'F.Cu':d if extra is None else d.union(extra)}, {'a':('F.Cu',box(0,0,.3,1)),'b':('F.Cu',box(3.7,0,4,1))},h,.01,.015)
def value(m):return m.solve({'a':1,'b':-1},'b')

class CopperTests(unittest.TestCase):
    def test_grouped_native_contact_union(self):
        pads={name:[{'copper':{'F.Cu':records(poly)}}]for name,poly in [
            ('U.1',box(0,0,.2,1)),('U.2',box(.1,0,.3,1)),('U.3',box(1,0,1.2,1)),
            ('U.4',box(.2,1,.4,2))]}
        grouped=contact_spec_geometry(pads,{'pads':['U.1','U.2'],'layer':'F.Cu'})
        self.assertTrue(grouped.equals(box(0,0,.3,1)))
        m=Mesh({'F.Cu':box(0,0,4,1)}, {'a':('F.Cu',grouped),'b':('F.Cu',box(3.7,0,4,1))},.25,.01,.015)
        self.assertAlmostEqual(value(m)['contact_voltage_V']['a'],.034,10)
        for keys in [['U.1','U.3'],['U.1','U.4']]:
            with self.assertRaisesRegex(Refused,'one connected finite'):
                contact_spec_geometry(pads,{'pads':keys,'layer':'F.Cu'})
        for spec in [{'pads':[]},{'pads':['U.1','U.1']},{'pad':'U.1','pads':['U.2']},{'pads':'U.1'}]:
            with self.assertRaises(Refused):contact_spec_geometry(pads,{**spec,'layer':'F.Cu'})
        with self.assertRaisesRegex(Refused,'No finite native copper'):
            contact_spec_geometry(pads,{'pads':['U.1','U.2'],'layer':'B.Cu'})
    def test_exact_fractured_bridge_controls(self):
        self.assertTrue(check_fixture()['passed'])
    def test_native_saved_fill_fixture_preserves_holes_and_islands(self):
        fixture=json.loads((Path(__file__).parent/'native-fill-fixture.json').read_text())
        self.assertEqual(fixture['native_version'],'10.0.6')
        self.assertTrue(fixture['input_objects_unchanged'])
        recovered=polygon_set(fixture['decoded_output'])
        explicit=polygon_set(fixture['explicit_output'])
        self.assertTrue(recovered.is_valid)
        self.assertTrue(recovered.equals(explicit))
        self.assertAlmostEqual(recovered.area,fixture['expected_area_mm2'])
        self.assertEqual(len(fixture['decoded_output']),fixture['expected_outlines'])
        self.assertEqual(sum(len(p['holes'])for p in fixture['decoded_output']),fixture['expected_holes'])
        for raw,receipt in zip(fixture['fractured_input'],fixture['decoded_receipts']):
            _,proof=decode_fractured_contour(raw['outer_nm'])
            self.assertEqual(proof['doubled_area_before_nm2'],receipt['doubled_area_after_nm2'])
            self.assertTrue(proof['boundary_edges_preserved_exactly'])
            self.assertEqual(proof['maximum_coordinate_displacement_nm'],0)
    def test_analytical_finite_contacts(self):
        for h in [1,.5,.25,.125]:
            r=value(strip(h));self.assertAlmostEqual(r['contact_voltage_V']['a'],.034,10)
            self.assertAlmostEqual(r['copper_loss_W'],.034,10);self.assertLess(r['KCL_max_residual_A'],1e-8)
    def test_float_point_touch_and_disconnected_contact(self):
        r=value(strip(extra=box(5,0,6,1)));self.assertAlmostEqual(r['contact_voltage_V']['a'],.034,10);self.assertGreater(r['floating_unloaded_nodes'],0)
        with self.assertRaisesRegex(Refused,'one copper/barrel component'):
            Mesh({'F.Cu':MultiPolygon([box(0,0,1,1),box(1,1,2,2)])},{'a':('F.Cu',box(0,0,.2,.2)),'b':('F.Cu',box(1.8,1.8,2,2))},.25,.01,.015)
        with self.assertRaisesRegex(Refused,'short disconnected'):
            Mesh({'F.Cu':MultiPolygon([box(0,0,1,1),box(2,0,3,1)])},{'a':('F.Cu',box(0,0,3,.2)),'b':('F.Cu',box(0,.8,1,1))},.25,.01,.015)
    def test_bad_contacts_and_numbers(self):
        with self.assertRaisesRegex(Refused,'finite copper overlap'):
            Mesh({'F.Cu':box(0,0,4,1)},{'a':('F.Cu',box(-1,0,0,1)),'b':('F.Cu',box(3.7,0,4,1))},.5,.01,.015)
        with self.assertRaisesRegex(Refused,'equivalent contacts'):
            Mesh({'F.Cu':box(0,0,4,1)},{'a':('F.Cu',box(0,0,.3,1)),'b':('F.Cu',box(0,0,.3,1))},.5,.01,.015)
        for h in [0,math.nan,math.inf]:
            with self.assertRaises(Refused):strip(h)
        m=strip()
        with self.assertRaisesRegex(Refused,'not conserved'):m.solve({'a':1,'b':-.9})
        with self.assertRaisesRegex(Refused,'nonfinite'):m.solve({'a':math.nan,'b':-1})
    def test_actual_all_net_drill_voids_and_saved_fills(self):
        hole=box(1,.4,2,.6)
        s={'copper_layers':['F.Cu','B.Cu'],'outline_with_npth':{'valid':True,'polygons':records(box(0,0,4,1))},'objects':[{'kind':'pad','net':'OTHER','copper':{},'key':'H.1','plated':False,'drill':{'outside':records(hole)}}],'zones':[{'rule':False,'net':'GND','filled':{'F.Cu':records(box(0,0,4,1)),'B.Cu':records(box(0,0,4,1))}}]}
        d,_,_=native_geometry(s,'GND');self.assertAlmostEqual(d['F.Cu'].area,3.8);self.assertAlmostEqual(d['B.Cu'].area,3.8)
        s['objects'][0].update(kind='via',barrel_layers=['F.Cu']);d,_,_=native_geometry(s,'GND');self.assertAlmostEqual(d['B.Cu'].area,4)
    def test_barrel_and_unflashed_layer_span(self):
        ring=Point(0,0).buffer(.4).difference(Point(0,0).buffer(.1));rho=.001*.015
        o={'uuid':'via','drill':{'start':[0,0],'end':[0,0],'width':.2},'barrel_layers':['F.Cu','In1.Cu','B.Cu'],'copper':{'F.Cu':records(ring),'B.Cu':records(ring)}}
        expected=rho/(math.pi*.2*.015);self.assertAlmostEqual(barrel_resistance(o,1,rho,.015),expected)
        m=Mesh({'F.Cu':ring,'In1.Cu':Polygon(),'B.Cu':ring},{'a':('F.Cu',ring),'b':('B.Cu',ring)},.2,.001,.015,[o],{'F.Cu':0,'In1.Cu':.2,'B.Cu':1})
        r=value(m);self.assertAlmostEqual(r['contact_voltage_V']['a'],expected,10);self.assertAlmostEqual(r['sheet_loss_W'],0,10);self.assertAlmostEqual(r['barrels'][0]['current_A'],1,10)
        bad=copy.deepcopy(o);bad['drill']['end'][0]=math.nan
        with self.assertRaises(Refused):barrel_resistance(bad,1,rho,.015)
        o['drill']['end']=[.4,0];self.assertAlmostEqual(barrel_resistance(o,1,rho,.015),rho/((math.pi*.2+.8)*.015))
    def test_irregular_mesh_conformity_convergence_reciprocity(self):
        d=Polygon([(0,0),(4,.1),(3.7,2),(0,1.7)]).difference(Point(2,.85).buffer(.28,quad_segs=8))
        contacts={'a':('F.Cu',box(0,.3,.3,1.3)),'b':('F.Cu',box(3.4,.5,3.7,1.5)),'c':('F.Cu',box(1.5,.1,2,.3))};zs=[]
        for h in [.5,.25,.125]:
            m=Mesh({'F.Cu':d},contacts,h,.01,.015);zs.append(np.array(m.impedance()['impedance_ohm']));self.assertLess(abs(m.area_error_mm2),1e-8)
            for tri in m.triangles:
                for i,j in [(0,1),(1,2),(2,0)]:
                    a,b=m.xy[tri[i]],m.xy[tri[j]];ab=b-a;t=(m.xy-a)@ab/(ab@ab);dist=np.linalg.norm(m.xy-(a+t[:,None]*ab),axis=1)
                    self.assertFalse(np.any((t>1e-7)&(t<1-1e-7)&(dist<1e-8)))
        self.assertLess(np.max(abs(zs[-1]-zs[-2])),np.max(abs(zs[-2]-zs[-3])))
        self.assertLess(np.max(abs(zs[-1]-zs[-2]))/np.max(abs(zs[-1])),.025)
    def test_caps(self):
        with self.assertRaisesRegex(Refused,'Tile cap'):
            Mesh({'F.Cu':box(0,0,4,1)},{'a':('F.Cu',box(0,0,.3,1)),'b':('F.Cu',box(3.7,0,4,1))},.1,.01,.015,limits=Limits(max_tiles=2))
    def test_narrow_feeder_before_wide_trunk_is_retained(self):
        domain=box(0,0,2,.4).union(box(2,-.4,5,.8))
        mesh=Mesh({'F.Cu':domain},{'a':('F.Cu',box(0,0,.3,.4)),'b':('F.Cu',box(4.7,-.4,5,.8))},.1,.01,.015)
        r=value(mesh)
        # The 0.4 mm feeder remains in series with the 1.2 mm trunk; spreading
        # adds to the separate uniform-section lower bound.
        self.assertGreater(r['contact_voltage_V']['a'],.01*(1.7/.4+2.7/1.2))
        self.assertGreater(r['peak_element_density_A_per_mm2'],1/(.4*.015)*.999)
        self.assertAlmostEqual(sum(r['layer_sheet_loss_W'].values()),r['sheet_loss_W'])

class CircuitTests(unittest.TestCase):
    def case(self):return {'name':'return','reference_node':'g','sources':[{'name':'s','p':'s','n':'g','voltage_V':5}],'loads':[{'name':'load','p':'p','n':'r','current_A':1}],'probes':[{'name':'load','p':'p','n':'r','minimum_V':4.8}]}
    def ports(self):return [{'net':'P','contacts':['s','p'],'impedance_ohm':[[.1]]},{'net':'GND','contacts':['g','r'],'impedance_ohm':[[.2]]}]
    def test_return_floor_power(self):
        c=self.case();r=solve_circuit(c,self.ports());self.assertAlmostEqual(r['probes'][0]['voltage_V'],4.7);self.assertFalse(r['static_probe_pass']);self.assertAlmostEqual(r['power_W']['balance_error'],0,10);self.assertAlmostEqual(r['power_W']['copper_loss'],.3)
        for b in r['port_injections']:self.assertAlmostEqual(sum(b['injections_A'].values()),0)
        c['probes'][0]['minimum_V']=4.6;self.assertTrue(solve_circuit(c,self.ports())['static_probe_pass'])
    def test_converter_and_contacts(self):
        c={'name':'converter','reference_node':'g','sources':[{'name':'battery','p':'s','n':'g','voltage_V':5}],'resistors':[{'name':'input lead','p':'s','n':'in','ohm':.1},{'name':'return lead','p':'cg','n':'g','ohm':.1},{'name':'contact loop','p':'out','n':'load','ohm':.2}],'converters':[{'name':'buck','in_p':'in','in_n':'cg','out_p':'out','out_n':'cg','voltage_V':3.3,'efficiency':.85,'quiescent_A':.005,'minimum_input_V':3.5,'maximum_output_A':1}],'loads':[{'name':'logic','p':'load','n':'cg','current_A':.8}],'probes':[{'name':'load','p':'load','n':'cg','minimum_V':3.0}]}
        r=solve_circuit(c);v=r['converters'][0];self.assertAlmostEqual(v['input_V']*(v['input_A']-.005)*.85,v['output_V']*v['output_A'],8);self.assertAlmostEqual(r['probes'][0]['voltage_V'],3.14);self.assertAlmostEqual(r['power_W']['balance_error'],0,8)
        c['converters'][0]['minimum_input_V']=5
        with self.assertRaisesRegex(Refused,'outside explicit model range'):solve_circuit(c)
    def test_same_bec_feed_sharing(self):
        c={'name':'dual','reference_node':'g','sources':[{'name':'BEC','p':'s','n':'g','voltage_V':7.4}],'resistors':[{'name':'p1','p':'s','n':'p','ohm':.02},{'name':'p2','p':'s','n':'p','ohm':.08},{'name':'r1','p':'r','n':'g','ohm':.08},{'name':'r2','p':'r','n':'g','ohm':.02}],'loads':[{'name':'servo','p':'p','n':'r','current_A':10}]}
        rows={x['name']:x for x in solve_circuit(c)['resistors']};self.assertAlmostEqual(rows['p1']['current_A'],8);self.assertAlmostEqual(rows['r1']['current_A'],2)
    def test_bad_models(self):
        c=self.case();c['probes'][0]['p']='unknown'
        with self.assertRaisesRegex(Refused,'unmodeled'):solve_circuit(c,self.ports())
        c=self.case();c['loads'][0]['current_A']=math.nan
        with self.assertRaisesRegex(Refused,'Nonfinite'):solve_circuit(c,self.ports())
        c=self.case();c['loads'][0]['current_A']=-1
        with self.assertRaisesRegex(Refused,'Negative load'):solve_circuit(c,self.ports())
        p=self.ports();p[0]['impedance_ohm']=[[-.1]]
        with self.assertRaisesRegex(Refused,'positive definite'):solve_circuit(self.case(),p)

class SourceTests(unittest.TestCase):
    def fixture(self,directory):
        d=Path(directory)
        def save(name,data):
            p=d/name;p.write_text(json.dumps(data)if not isinstance(data,str)else data);return {'path':name,'sha256':sha256(p)}
        files={'board':save('toy-board.txt','(kicad_pcb (setup (stackup (layer "F.Cu" (type "copper") (thickness 0.035)))))')};h=files['board']['sha256']
        objs=[{'uuid':n,'kind':'pad','net':'P','number':'1','key':n,'copper':{'F.Cu':records(p)},'drill':None,'plated':False}for n,p in [('a',box(0,0,.3,1)),('b',box(3.7,0,4,1))]]
        g={'schema':'kicad-native-copper/v1','board_sha256':h,'source_unchanged':True,'units':'mm','copper_layers':['F.Cu'],'outline_with_npth':{'valid':True,'polygons':records(box(0,0,4,1))},'objects':objs,'zones':[{'rule':False,'net':'P','filled':{'F.Cu':records(box(0,0,4,1))}}]}
        files['geometry']=save('geometry.json',g);files['connectivity']=save('connectivity.json',{'board_sha256':h,'nets':{'P':{'pad_group_count':1,'groups':[{'pad_uuids':['a','b']}]}}});files['parts']=save('parts.json',{'synthetic':True})
        for n in ['parity','physical']:files[n]=save(n+'.json',{'board_sha256':h,'passed':True})
        for n in ['drc_normal','drc_all_track']:files[n]=save(n+'.json',{'violations':[],'unconnected_items':[{'items':[{'uuid':'ordinary'}]}],'ignored_checks':[]})
        f={'schema':'f722-scoped-static-freeze/v1','status':'frozen-for-scoped-static-screen','scope':'power-only','saved_fill_verified':True,'checks_run_on_frozen_board':True,'tested_nets':['P'],'files':files};save('freeze.json',f)
        l={'schema':'f722-static-ledger/v1','status':'ready','freeze_manifest_sha256':sha256(d/'freeze.json'),'mesh_spacings_mm':[.5,.25],'material':{'temperature_C':105,'thickness_mm':.015,'conductivity_IACS':.95,'plating_mm':.015},'convergence':{'relative_impedance':.02,'absolute_impedance_ohm':1e-5,'absolute_voltage_V':1e-4},'networks':[{'net':'P','contacts':{'a':{'pad':'a','layer':'F.Cu'},'b':{'pad':'b','layer':'F.Cu'}}}],'unit_transfers':[{'name':'strip','net':'P','source':'a','sink':'b','maximum_ohm':.035}]};save('ledger.json',l);return d,f,l
    def test_preflight_synthetic_screen_and_stale(self):
        with tempfile.TemporaryDirectory()as tmp:
            d,_,_=self.fixture(tmp);c=preflight(d/'freeze.json',d/'ledger.json');self.assertEqual(c['drc']['drc_normal']['ordinary_opens_outside_scope'],1)
            r=run_screen(c);self.assertTrue(r['conditional_static_screen_pass']);self.assertFalse(r['scope_is_final_board'])
            (d/'toy-board.txt').write_text('changed')
            with self.assertRaisesRegex(Refused,'changed'):preflight(d/'freeze.json',d/'ledger.json')
    def test_grouped_contact_preflight_and_run(self):
        with tempfile.TemporaryDirectory()as tmp:
            d,f,l=self.fixture(tmp)
            g=json.loads((d/'geometry.json').read_text())
            g['objects'][0]['copper']['F.Cu']=records(box(0,0,.2,1))
            g['objects'].append({'uuid':'a2','kind':'pad','net':'P','number':'2','key':'a2',
                'copper':{'F.Cu':records(box(.1,0,.3,1))},'drill':None,'plated':False})
            (d/'geometry.json').write_text(json.dumps(g));f['files']['geometry']['sha256']=sha256(d/'geometry.json')
            c=json.loads((d/'connectivity.json').read_text());c['nets']['P']['groups'][0]['pad_uuids'].append('a2')
            (d/'connectivity.json').write_text(json.dumps(c));f['files']['connectivity']['sha256']=sha256(d/'connectivity.json')
            (d/'freeze.json').write_text(json.dumps(f));l['freeze_manifest_sha256']=sha256(d/'freeze.json')
            l['networks'][0]['contacts']['a']={'pads':['a','a2'],'layer':'F.Cu'}
            (d/'ledger.json').write_text(json.dumps(l))
            r=run_screen(preflight(d/'freeze.json',d/'ledger.json'))
            self.assertTrue(r['conditional_static_screen_pass'])
            l['networks'][0]['contacts']['a']['pads']=['a','b']
            (d/'ledger.json').write_text(json.dumps(l))
            with self.assertRaisesRegex(Refused,'one connected finite'):
                preflight(d/'freeze.json',d/'ledger.json')
    def test_geometry_only_audit_and_foreign_drill_split(self):
        with tempfile.TemporaryDirectory()as tmp:
            d,_,l=self.fixture(tmp)
            l['loops']=[{'name':'toy_loop','maximum_ohm':.04,'legs':[{'net':'P','source':'a','sink':'b'}]}]
            (d/'ledger.json').write_text(json.dumps(l))
            args=[d/'toy-board.txt',d/'geometry.json',d/'ledger.json',d/'connectivity.json']
            receipt=audit_ports(*args)
            self.assertTrue(receipt['passed']);self.assertEqual(receipt['contact_count'],2)
            self.assertFalse(receipt['source_acceptance_or_final_board_qualification'])
            self.assertFalse(receipt['loops'][0]['resistance_solved'])
            l['networks'][0]['contacts']['duplicate_a']={'pad':'a','layer':'F.Cu'}
            (d/'ledger.json').write_text(json.dumps(l))
            with self.assertRaisesRegex(Refused,'touches/overlaps contact'):audit_ports(*args)
            del l['networks'][0]['contacts']['duplicate_a'];(d/'ledger.json').write_text(json.dumps(l))
            g=json.loads((d/'geometry.json').read_text())
            g['objects'].append({'uuid':'foreign-drill','kind':'pad','net':'OTHER','number':'1','key':'hole',
                'copper':{},'plated':False,'drill':{'outside':records(box(.1,-.1,.2,1.1))}})
            (d/'geometry.json').write_text(json.dumps(g))
            with self.assertRaisesRegex(Refused,'after actual drill'):audit_ports(*args)
            g['board_sha256']='stale';(d/'geometry.json').write_text(json.dumps(g))
            with self.assertRaisesRegex(Refused,'does not belong'):audit_ports(*args)
    def test_unfinished_and_draft_refuse(self):
        for change,pattern in [('final','ordinary unfinished'),('draft','unfinished'),('groups','unfinished'),('tested-open','opens on tested')]:
            with self.subTest(change=change),tempfile.TemporaryDirectory()as tmp:
                d,f,l=self.fixture(tmp)
                if change=='final':f['scope']='final-board'
                elif change=='draft':l['status']='draft'
                elif change=='groups':
                    p=d/'connectivity.json';r=json.loads(p.read_text());r['nets']['P']['pad_group_count']=2;p.write_text(json.dumps(r));f['files']['connectivity']['sha256']=sha256(p)
                else:
                    p=d/'drc_normal.json';r=json.loads(p.read_text());r['unconnected_items'][0]['items'][0]['uuid']='a';p.write_text(json.dumps(r));f['files']['drc_normal']['sha256']=sha256(p)
                (d/'freeze.json').write_text(json.dumps(f));l['freeze_manifest_sha256']=sha256(d/'freeze.json');(d/'ledger.json').write_text(json.dumps(l))
                with self.assertRaisesRegex(Refused,pattern):preflight(d/'freeze.json',d/'ledger.json')
    def test_coupled_screen_and_marginal_floor(self):
        with tempfile.TemporaryDirectory()as tmp:
            d,_,l=self.fixture(tmp)
            l['cases']=[{'name':'synthetic','reference_node':'g','nets':['P'],'assumptions':['Analytical toy circuit only'],
                         'sources':[{'name':'source','p':'a','n':'g','voltage_V':5}],
                         'loads':[{'name':'load','p':'b','n':'g','current_A':1}],
                         'probes':[{'name':'load','p':'b','n':'g','minimum_V':4.8}]}]
            (d/'ledger.json').write_text(json.dumps(l));r=run_screen(preflight(d/'freeze.json',d/'ledger.json'))
            self.assertTrue(r['conditional_static_screen_pass'])
            voltage=r['runs'][-1]['cases'][0]['probes'][0]['voltage_V']
            l['cases'][0]['probes'][0]['minimum_V']=voltage-1e-6
            (d/'ledger.json').write_text(json.dumps(l));r=run_screen(preflight(d/'freeze.json',d/'ledger.json'))
            self.assertTrue(r['runs'][-1]['cases'][0]['static_probe_pass'])
            self.assertFalse(r['conditional_static_screen_pass'])
    def test_bad_ledger_rejected_before_mesh(self):
        for change,pattern in [('duplicate','Duplicate unit_transfers'),('contact','absent network contact'),('zero','distinct contacts')]:
            with self.subTest(change=change),tempfile.TemporaryDirectory()as tmp:
                d,_,l=self.fixture(tmp)
                if change=='duplicate':l['unit_transfers'].append(copy.deepcopy(l['unit_transfers'][0]))
                elif change=='contact':l['unit_transfers'][0]['sink']='missing'
                else:l['unit_transfers'][0]['sink']='a'
                (d/'ledger.json').write_text(json.dumps(l))
                with self.assertRaisesRegex(Refused,pattern):preflight(d/'freeze.json',d/'ledger.json')
    def test_output_cannot_overwrite_sources(self):
        with tempfile.TemporaryDirectory()as tmp:
            d,_,_=self.fixture(tmp)
            for name in ['freeze.json','ledger.json','geometry.json','parts.json','physical.json']:
                with self.assertRaisesRegex(Refused,'aliases'):
                    guard_output(d/'freeze.json',d/'ledger.json',d/name)
            (d/'alias.json').symlink_to(d/'geometry.json')
            with self.assertRaisesRegex(Refused,'aliases'):
                guard_output(d/'freeze.json',d/'ledger.json',d/'alias.json')
            (d/'hardlink.json').hardlink_to(d/'geometry.json')
            with self.assertRaisesRegex(Refused,'aliases'):
                guard_output(d/'freeze.json',d/'ledger.json',d/'hardlink.json')
            guard_output(d/'freeze.json',d/'ledger.json',d/'result.json')

if __name__=='__main__':unittest.main(verbosity=2)
