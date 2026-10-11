"""Native7-only IO4 model with one complete ordinary TX-up header donor."""
from native7_IO4_native_only_model_v2 import build as build_base
from native7_IO4_native_only_model_v2 import adapter,HERE,ROOT
import json

def build():
 g,base,C,view,work,inventory=build_base()
 scope=json.loads((HERE/'native7-C-compact-scope-receipt-v4.json').read_text())['scopes']['TX_up_header_tail'];ids=set(scope['native_ids']);assert len(ids)==6
 for q in work:
  if q[0]['uuid'] in ids:assert q[0]==base.by[q[0]['uuid']] and q[0]['net']=='PORT_C_TX_EXT' and q[0]['width']==.127
 work=[q for q in work if q[0]['uuid'] not in ids];inventory['removed_native_records']+= [base.by[u] for u in sorted(ids)];inventory['removed_native_ids']=sorted(set(inventory['removed_native_ids'])|ids);inventory['native_cut_count']=17
 inventory['TX_up_complete_header_donor']=scope;inventory['TX_down_and_both_MCU_native_trees_held']=True;inventory['all_ordinary_IMU_C12_R3_TX_copper_preserved']=False;inventory['all_uncut_native_copper_preserved']=True
 g.by={q[0]['uuid']:q[0] for q in work};g.N=dict(g.N,objects=[q[0] for q in work]);return g,base,C,view,work,inventory
