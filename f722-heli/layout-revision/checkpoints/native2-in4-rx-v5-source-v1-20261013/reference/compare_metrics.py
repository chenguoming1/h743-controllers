"""Compare replayed measurements to the exact current v5 saved measurements."""
import argparse,json,math
from pathlib import Path
def compact(inventory,targeted,returns):
    return {
      'source':inventory['source'],'candidate':inventory['candidate'],
      'routed_net_count':inventory['routed_net_count'],'track_projection_count':inventory['track_projection_count'],
      'net_summaries':inventory['net_summaries'],
      'planes':{layer:{k:r[k] for k in ['source_area_mm2','candidate_area_mm2','exactly_equal']}|{'lost_area_mm2':r['lost']['area_mm2'],'gained_area_mm2':r['gained']['area_mm2']} for layer,r in inventory['plane_changes'].items()},
      'actual_In4_loss_mm2':targeted['actual_In4_loss_mm2'],'source_In1_exact':targeted['source_In1_exact'],
      'TP2_margin_mm':targeted['TP2']['candidate_pad_to_plane_boundary_mm'],
      'TP2_collar_newloss_mm2':targeted['TP2']['source_0p10mm_collar']['newly_lost']['area_mm2'],
      'FLASH_CS_collar_newloss_mm2':targeted['FLASH_CS_collar']['exact_source_collar']['newly_lost']['area_mm2'],
      'FLASH_CS_curves':{k:{n:r[n] for n in ['candidate_uncovered_mm','candidate_minimum_boundary_distance_mm','source_minimum_boundary_distance_mm','length_mm']} for k,r in targeted['FLASH_CS_collar']['curves'].items()},
      'FLASH_CS_exits':[{'via_uuid':r['via_uuid'],'path':{n:r['actual_v5_path'][n] for n in ['candidate_uncovered_mm','candidate_minimum_boundary_distance_mm','source_minimum_boundary_distance_mm','length_mm']}} for r in targeted['FLASH_CS_collar']['full_exit_paths']],
      'C3':{r['uuid']:{'projection_loss_mm2':r['newly_lost_reference_mm2'],'slot_margin_mm':r['route_slot_margin']['distance_mm'],'record_exact':r['record_exact']} for r in targeted['C3']['records']},
      'C3_exception_UUIDs':targeted['C3']['feed_exception_UUIDs'],
      'U15_J11':{'corridor_newloss_mm2':targeted['U15_J11']['corridor']['newly_lost']['area_mm2'],'rectangle_newloss_mm2':targeted['U15_J11']['between_lips_0p254mm_rectangle']['newly_lost']['area_mm2'],'lip_sections':targeted['U15_J11']['at_annular_lips_transverse_sections']},
      'protection_GND_entries':returns['actual_protection_GND_entries'],
      'return_annuli':returns['selected_return_via_attachments'],
      'RX_transition_GND_stitches':returns['RX_transition_GND_stitches']}
def compare(a,b,path=''):
    if isinstance(a,dict):
        assert isinstance(b,dict) and set(a)==set(b), 'Changed fields at '+path
        for k in a:compare(a[k],b[k],path+'/'+k)
    elif isinstance(a,list):
        assert isinstance(b,list) and len(a)==len(b), 'Changed inventory at '+path
        for i,(x,y) in enumerate(zip(a,b)):compare(x,y,path+'/'+str(i))
    elif isinstance(a,float):
        assert isinstance(b,(int,float)) and math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12), 'Changed measurement at '+path
    else:assert a==b, 'Changed value at '+path
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);args=p.parse_args()
    read=lambda n:json.loads((args.output/n).read_text())
    actual=compact(read('inventory-summary.json'),read('targeted-actual-reference.json'),read('actual-return-geometry.json'))
    expected=json.loads((Path(__file__).parent/'EXPECTED-METRICS.json').read_text())
    compare(expected['measurements'],actual)
    receipt={'saved_current_v5_measurements_match':True,'numeric_comparison_tolerance':{'relative':1e-12,'absolute':1e-12},'tolerance_is_not_a_geometry_repair_or_clearance_waiver':True,'new_acceptance_claimed':False}
    (args.output/'METRIC-COMPARISON.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':main()
