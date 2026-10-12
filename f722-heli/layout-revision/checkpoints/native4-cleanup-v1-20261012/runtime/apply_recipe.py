"""Exact native track/via mutation loop, with explicit portable arguments."""
from native_trial import require,nm

def apply_recipe(board,pcb,recipe,poses):
    r=recipe
    fps={f.GetReference():f for f in board.GetFootprints()}
    for ref,pose in poses.items():
        f=fps[ref]
        if f.GetLayerName()!=pose[3]:
            require(ref in ['R6','U15'],'Only exact R6 and U15 may flip');f.Flip(f.GetPosition(),pcb.FLIP_DIRECTION_TOP_BOTTOM if ref=='U15' else pcb.FLIP_DIRECTION_LEFT_RIGHT)
        f.SetOrientationDegrees(pose[2]);f.SetPosition(pcb.VECTOR2I(nm(pose[0]),nm(pose[1])))
    routes={t.m_Uuid.AsString():t for t in board.GetTracks()}
    for uid in r['remove_source_records']:
        require(uid in routes,'Cut route UUID missing');board.Remove(routes[uid])
    held=[]
    for row in r['proposed_add_tracks']+r['proposed_add_vias']:
        require(board.FindNet(row['net']) is not None,'Added net not present in source')
        if row['kind']=='track':
            item=pcb.PCB_TRACK(board);item.SetStart(pcb.VECTOR2I(*map(nm,row['start'])));item.SetEnd(pcb.VECTOR2I(*map(nm,row['end'])));item.SetWidth(nm(row['width']));item.SetLayer(board.GetLayerID(row['layer']))
        else:
            item=pcb.PCB_VIA(board);item.SetPosition(pcb.VECTOR2I(*map(nm,row['xy'])));item.SetWidth(nm(row['diameter']));item.SetDrill(nm(row['drill']));item.SetViaType(pcb.VIATYPE_THROUGH);item.SetLayerPair(pcb.F_Cu,pcb.B_Cu);item.SetFrontTentingMode(pcb.TENTING_MODE_TENTED);item.SetBackTentingMode(pcb.TENTING_MODE_TENTED)
        item.SetUuid(pcb.KIID(row['uuid']));item.SetNet(board.FindNet(row['net']));board.Add(item);held.append(item)
    return held
