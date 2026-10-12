"""Exact two-island policy and shape checks with portable plan lookup."""
import copy
from pathlib import Path
import paired_source as p
HERE=Path(__file__).resolve().parent
PLAN=HERE/'island-cleanup-contract.json'
PLAN_SHA='dbc45da2e029972579c1c78909e5cc2f5be87ca36ff164a19d79b4dc97ee4ec3'
def check_sources():return p.read(PLAN)


def binding():return {'schema':'f722-native4-two-GND-islands-only/v1','plan_sha256':PLAN_SHA,'zone_UUIDs':['c956a476-e320-4f09-9832-420df749bd95','ee652b71-6147-4d53-abc1-8530e0b19eaf'],'from_policy':'NEVER','to_policy':'ALWAYS','reference_acceptance_unchanged_and_pending':True}


def restore_raw_policy(old,new):
 """Comparison copy only. Validate the two exact 1->0 fields before restoring."""
 import structural_base as raw
 plan=p.read(PLAN);uid=raw.uid(old)
 if uid not in plan['zones']:return new
 row=plan['zones'][uid];p.require(raw.uid(new)==uid,'Cleanup zone UUID changed')
 for item in [old,new]:
  p.require(raw.child(item,'net')==['net','"GND"'] and raw.child(item,'layer')==['layer','"'+row['layer']+'"'],'Cleanup zone net/layer changed')
 a=raw.child(raw.child(old,'fill'),'island_removal_mode');b=raw.child(raw.child(new,'fill'),'island_removal_mode')
 p.require(a==['island_removal_mode','1'] and b==['island_removal_mode','0'],'Only exact NEVER to ALWAYS zone policy permitted')
 result=copy.deepcopy(new);raw.child(raw.child(result,'fill'),'island_removal_mode')[1]='1';return result


def apply_policy(board,pcb):
 plan=check_sources();zones={z.m_Uuid.AsString():z for z in board.Zones()}
 for uid,row in plan['zones'].items():
  z=zones[uid];p.require(z.GetNetname()=='GND' and board.GetLayerName(z.GetLayer())==row['layer'] and int(z.GetIslandRemovalMode())==1,'Source island policy differs')
  z.SetIslandRemovalMode(pcb.ISLAND_REMOVAL_MODE_ALWAYS)


def verify_saved_policy(board_path):
 import structural_base as raw
 plan=check_sources();zones={raw.uid(z):z for z in raw.children(raw.parse(board_path),'zone')}
 for uid,row in plan['zones'].items():
  z=zones[uid];p.require(raw.child(raw.child(z,'fill'),'island_removal_mode')==['island_removal_mode','0'],'Saved ALWAYS policy absent')
  p.require(raw.child(z,'net')==['net','"GND"'] and raw.child(z,'layer')==['layer','"'+row['layer']+'"'],'Saved cleanup zone identity differs')
 return {'zone_UUIDs':sorted(plan['zones']),'saved_reopened_ALWAYS_policy_exact':True}


def verify_fill(old,new,uid,plan):
 row=plan['zones'][uid];layer=row['layer'];before=old['filled'][layer]
 p.require(len(before)==2 and p.digest(before[0])==row['retained_component_sha256'] and p.digest(before[1])==row['removed_component_sha256'],'Raw native4 fill source differs')
 p.require(new['filled']=={layer:[before[0]]},'Only the exact isolated island may disappear; main fill changed')
 return {'zone_uuid':uid,'layer':layer,'retained_main_component_sha256':row['retained_component_sha256'],'removed_island_sha256':row['removed_component_sha256'],'all_main_vertices_holes_and_topology_exact':True}

