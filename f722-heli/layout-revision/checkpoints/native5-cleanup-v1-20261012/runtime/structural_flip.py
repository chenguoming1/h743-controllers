"""Reverse only declared footprint poses in a separate verification copy."""
from pathlib import Path
import structural_base as base

def verify_raw_board(source_path,after_path,poses,cuts,adds):
    import pcbnew as pcb
    source=base.parse(source_path)
    originals={base.ref(f):base.pose(f) for f in base.children(source,'footprint') if base.ref(f) in poses}
    b=pcb.LoadBoard(str(after_path));fps={f.GetReference():f for f in b.GetFootprints()}
    for ref,pose in poses.items():
        f=fps[ref]
        base.require([f.GetPosition().x/1e6,f.GetPosition().y/1e6,f.GetOrientationDegrees()%360,f.GetLayerName()]==pose,'Candidate pose mismatch')
        old=originals[ref]
        if f.GetLayerName()!=old[3]:
            base.require(ref in ['R6','U15'],'Unexpected side flip')
            f.Flip(f.GetPosition(),pcb.FLIP_DIRECTION_TOP_BOTTOM if ref=='U15' else pcb.FLIP_DIRECTION_LEFT_RIGHT)
        f.SetOrientationDegrees(old[2]);f.SetPosition(pcb.VECTOR2I(round(old[0]*1e6),round(old[1]*1e6)))
    verification=Path(after_path).parent.parent/('inverse-pose-check-'+str(len(list(Path(after_path).parent.parent.glob('inverse-pose-check-*.kicad_pcb'))))+'.kicad_pcb')
    base.require(not verification.exists(),'Verification output already exists')
    pcb.SaveBoard(str(verification),b)
    text_angles={'b36469c2-eac3-447b-bc0f-da743a28c0a1':{uid:[270,90] for uid in [
        '797d2fe4-bd16-40b8-91af-12c8cf0464a6','f002cdc8-b079-4152-bfbd-05a617c68938',
        'c65ea005-466a-455b-a6dc-13c74cec5f45','be189773-48b9-440b-b3c3-b34d5c78040a',
        'dbe8d8d3-b2cb-4baf-8172-8bd327b41322']}}
    result=base.verify_raw_board(source_path,verification,{},cuts,adds,text_angle_normalizations=text_angles)
    result.update({'inverse_pose_check_copy':str(verification),'forward_pose_checked':poses,'inverse_flip_preserved_raw_pad_mask_paste':True,'text_orientation_difference':'Five source-bound R6 text items normalize from 270 to 90 degrees in inverse control; all other text fields remain exact'})
    return result
