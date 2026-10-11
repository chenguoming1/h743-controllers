"""Fabricated geometry and JSON tests only; no source board geometric audit."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
from shapely.geometry import box

import audit_native7_IO4_final_contacts_v1 as a
from test_audit_native7_final_contacts_v2 import object_record, track_record, via_record, exported


def pad(uid,key,shape,net='PORT_C_RX_EXT'):
    row=object_record(uid,shape); row.update(net=net,key=key); return row


def case():
    records=[pad('bond','U15.5',box(-.5,-.5,.5,.5)),
             pad('header','J11.1',box(-2.2,-.2,-1.8,.2)),
             pad('target','R34.1',box(1.8,-.2,2.2,.2))]
    for uid,start,end in [('up',(-2,0),(-.2,0)),('down',(.2,0),(2,0))]:
        r=track_record(uid,start,end,.127);r['net']=a.RX;records.append(r)
    c={'id':'published-06','net':a.RX,'clamp':'U15.5','source':'J11.1','target':'R34.1','minimum_gap_required_mm':.127}
    return records,c


class NarrowBindings(unittest.TestCase):
    def test_exact_only_rx_row_change(self):
        old={'checks':[{'id':'published-06','net':a.RX,'clamp':'U15.1'}, {'id':'other','clamp':'U15.2'}]}
        new={'checks':[{'id':'published-06','net':a.RX,'clamp':'U15.5'}, {'id':'other','clamp':'U15.2'}],
             'U15_actual_clamps':{a.RX:'U15.5','PORT_C_TX_EXT':'U15.2'},
             'U15_routing_land_assignments':{'U15.6':a.RX,'U15.9':'PORT_C_TX_EXT'},'package_internal_NC_conduction':False}
        a.exact_contract_delta(old,new)
        for change in ('foreign','nc','bond'):
            bad=copy.deepcopy(new)
            if change=='foreign': bad['checks'][1]['clamp']='U15.9'
            if change=='nc': bad['checks'][0]['clamp']='U15.6'
            if change=='bond': bad['package_internal_NC_conduction']=True
            with self.assertRaises(ValueError): a.exact_contract_delta(old,bad)

    def test_exact_cut_inventory_and_four_names(self):
        records=[{'uuid':u,'kind':'track'} for u in sorted(a.CUTS)]
        source={'objects':records};scope={'inventory':{'removed_native_records':records}}
        cuts=[{'record':r,'full_record_sha256':a.imp.record_sha(r)} for r in records]
        paired={'removed_native_records':cuts,'pad_net_delta':[{'uuid':u,'after_net':n} for u,n in a.PAD_NETS.items()]}
        plan={'removed_native_records':cuts}
        a.validate_scope(scope,source,paired,plan)
        for alteration in ('extra','missing','placeholder','record'):
            bscope,bpaired,bplan=map(copy.deepcopy,(scope,paired,plan))
            if alteration=='extra': bscope['inventory']['removed_native_records'].append({'uuid':'new-cut','kind':'track'})
            if alteration=='missing': bplan['removed_native_records'].pop()
            if alteration=='placeholder': bpaired['pad_net_delta'][1]['after_net']='unconnected-(U15-NC-Pad10)'
            if alteration=='record': bplan['removed_native_records'][0]['record']['kind']='via'
            with self.assertRaises(ValueError): a.validate_scope(bscope,source,bpaired,bplan)

    def test_import_is_geometry_and_CAD_free(self):
        script="""import builtins
old=builtins.__import__
def guarded(name,*args,**kw):
 if name.startswith(('shapely','pcbnew')): raise RuntimeError(name)
 return old(name,*args,**kw)
builtins.__import__=guarded
import audit_native7_IO4_final_contacts_v1
"""
        p=subprocess.run([sys.executable,'-c',script],cwd=Path(__file__).parent,text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr)

    def test_no_old_common90_binding(self):
        self.assertEqual(len(a.CUTS),11)
        self.assertNotIn('common_packet',a.FILES)
        self.assertNotIn('historical_ledger',a.FILES)
        self.assertEqual(len(a.FILES),14)


class OriginalTrees(unittest.TestCase):
    def test_preserve_preexisting_open_components_individually(self):
        rows=[object_record('a',box(0,0,1,1)),object_record('b',box(3,0,4,1))]
        g=a.rich_partition(rows)
        checks=a.preserve_original_components(g,g)
        self.assertEqual(len(checks),2)
        self.assertTrue(all(c['passed'] for c in checks))

    def test_preserve_returns_cannot_drop_last_anchor(self):
        old=a.rich_partition([object_record('a',box(0,0,1,1))])
        final=a.rich_partition([])
        self.assertFalse(a.preserve_original_components(old,final)[0]['passed'])
        self.assertFalse(a.preserve_original_components(old,final,{'a'})[0]['passed'])

    def test_foreign_drill_splitting_single_UUID_detected(self):
        track=track_record('wide',(-2,0),(2,0),.2)
        old=a.rich_partition([track])
        final=a.rich_partition([track],global_holes={'F.Cu':box(-.1,-1,.1,1)})
        self.assertEqual(len(final['memberships']['wide']),2)
        check=a.preserve_original_components(old,final)[0]
        self.assertFalse(check['passed'])
        self.assertEqual(len(check['final_component_roots']),2)

    def test_alternate_full_path_restores_drill_split(self):
        track=track_record('wide',(-2,0),(2,0),.2)
        paths=[track,track_record('v1',(-1,0),(-1,1),.2),track_record('top',(-1,1),(1,1),.2),track_record('v2',(1,1),(1,0),.2)]
        old=a.rich_partition([track]);new=a.rich_partition(paths,global_holes={'F.Cu':box(-.1,-.2,.1,.2)})
        self.assertTrue(a.preserve_original_components(old,new)[0]['passed'])

    def test_declared_terminal_replacement_is_explicit(self):
        old=a.rich_partition([object_record('IO1',box(0,0,1,1))]);new=a.rich_partition([object_record('IO4',box(3,0,4,1))])
        self.assertFalse(a.preserve_original_components(old,new)[0]['passed'])
        self.assertTrue(a.preserve_original_components(old,new,substitutions={'IO1':'IO4'})[0]['passed'])

    def test_retired_unused_pad_only(self):
        old=a.rich_partition([object_record('old-unused',box(0,0,1,1))]);new=a.rich_partition([])
        checks=a.preserve_original_components(old,new,retired={'old-unused'})
        self.assertTrue(checks[0]['passed']);self.assertTrue(checks[0]['retired_unused_singleton'])

    def test_rich_matches_v2_connectivity_and_positive_area(self):
        rows=[object_record('a',box(0,0,1,1)),object_record('b',box(1,0,2,1)),object_record('c',box(.9,.9,1.1,1.1))]
        x=a.rich_partition(rows);y=a.k.partition_native(rows)
        self.assertEqual({frozenset(s) for s in x['groups']},{frozenset(s) for s in y['groups']})
        self.assertEqual(x['contacts'],y['contacts'])


class ActualProtection(unittest.TestCase):
    def test_actual_IO4_opposite_branches_pass(self):
        rows,c=case();r=a.protection_case(rows,c,{},.00001)
        self.assertTrue(r['passed'],r)

    def test_outside_pad_bypass_fails(self):
        rows,c=case()
        for uid,st,en in [('b1',(-1,0),(-1,1)),('b2',(-1,1),(1,1)),('b3',(1,1),(1,0))]:
            r=track_record(uid,st,en,.127);r['net']=a.RX;rows.append(r)
        r=a.protection_case(rows,c,{},.00001)
        self.assertFalse(r['passed']);self.assertFalse(r['no_outside_actual_pad_bypass'])

    def test_historical_IO1_missing_is_recorded_failure(self):
        rows,c=case();c['clamp']='U15.1'
        r=a.protection_case(rows,c,{},.00001)
        self.assertFalse(r['passed']);self.assertEqual(r['missing_actual_pads'],['U15.1'])

    def test_bonded_pad_required_not_NC_internal_bond(self):
        rows,c=case();rows[0]['key']='U15.6'
        self.assertFalse(a.protection_case(rows,c,{},.00001)['passed'])

    def test_positive_area_not_tangency_required(self):
        rows,c=case();rows[3]['copper']={'F.Cu':exported(box(-2,-.05,-.5,.05))}
        r=a.protection_case(rows,c,{},.00001)
        self.assertFalse(r['full_actual_function_connected'])

    def test_outside_gap_limit_is_not_ignored(self):
        rows,c=case();c['minimum_gap_required_mm']=1.001
        r=a.protection_case(rows,c,{},.00001)
        self.assertFalse(r['passed']);self.assertFalse(r['outside_pad_gaps'][0]['passed'])

    def test_global_drill_removes_bonded_path(self):
        rows,c=case()
        r=a.protection_case(rows,c,{'F.Cu':box(-.3,-.6,.3,.6)},.00001)
        self.assertFalse(r['full_actual_function_connected'])

    def test_RX_roles_and_actual_full_width_contacts(self):
        rows,c=case();rows.append(pad('nc','U15.6',box(-1.2,-.1,-.8,.1)))
        data={'added_ids':{'up','down'},'added_roles':{'up':'upstream','down':'downstream'}}
        good=a.rx_roles_check(data,rows,{},.00001);self.assertTrue(good['passed'],good)
        bad=copy.deepcopy(data);bad['added_roles']['down']='upstream'
        self.assertFalse(a.rx_roles_check(bad,rows,{},.00001)['passed'])

    def test_NC6_on_downstream_is_rejected(self):
        rows,c=case();rows.append(pad('nc','U15.6',box(.8,-.1,1.2,.1)))
        data={'added_ids':{'up','down'},'added_roles':{'up':'upstream','down':'downstream'}}
        r=a.rx_roles_check(data,rows,{},.00001)
        self.assertFalse(r['passed']);self.assertFalse(r['NC6']['belongs_only_to_upstream'])


if __name__=='__main__':unittest.main()
