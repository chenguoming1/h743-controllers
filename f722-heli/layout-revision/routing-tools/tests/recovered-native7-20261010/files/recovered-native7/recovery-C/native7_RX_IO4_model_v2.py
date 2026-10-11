"""IO4 RX model with a complete dedicated northern U2.9 return proposal."""
import math
from native7_RX_IO4_model_v1 import build as build_base
from native7_RX_IO4_model_v1 import adapter,HERE,ROOT

def build():
    g,base,C,view,work,before,inventory,jobs=build_base()
    old=next(q for q in work if q[0]['uuid']=='recovered-U2-9-ground-1')
    entry=next(q for q in work if q[0]['uuid']=='recovered-U2-9-ground-0')
    assert old[0]['net']==entry[0]['net']=='GND' and old[0]['width']==entry[0]['width']==.18
    xy=[25.397615,10.812554]
    track={'kind':'track','name':'IO4-dedicated-U2-9-GND-tail','net':'GND','logical_net':'GND','layer':'F.Cu','points':[[24.86,11.85],[24.925,11.63],[24.925,10.812554],xy],'width':.18}
    via={'kind':'via','name':'IO4-dedicated-U2-9-GND-via','net':'GND','logical_net':'GND','xy':xy,'diameter':.45,'drill':.20,'layers':list(g.N['copper_layers']),'tented_front':True,'tented_back':True}
    work=[q for q in work if q[0]['uuid']!=old[0]['uuid']]
    work.append(g.track('GND','F.Cu',track['points'],track['name'],.18));work.append(g.via('GND',xy,via['name']))
    retained=next(q for q in work if q[0]['uuid']=='f4d4785b-7402-479d-a058-3ba1808bdbdd')
    assert retained[0]==base.by[retained[0]['uuid']] and retained[0]['xy']==[24.525,9.85]
    g.by={q[0]['uuid']:q[0] for q in work};g.N=dict(g.N,objects=[q[0] for q in work])
    oldpoints=[[24.86,11.85],[24.925,11.63],[24.925,10.36],[24.525,9.85]]
    length=lambda pts:sum(math.dist(a,b) for a,b in zip(pts,pts[1:]))
    inventory['dedicated_U2_9_ground']={'removed_unadopted_proposal_record':old[0],'held_actual_entry_record':entry[0],'actual_source_pad':g.one_pad('U2.9'),
      'routes':[track],'vias':[via],'retained_MCU_GND_barrel_record':retained[0],
      'original_native_U2_9_barrel_remains_preexisting_common_cut':True,'new_native_GND_cuts':[],
      'new_full_entry_plus_tail_length_mm':.25+length(track['points']),'prior_common_entry_plus_tail_length_mm':.25+length(oldpoints),
      'native_fill_plane_necks_reference_return_and_power_review_pending':True,'no_AC_equivalence_claim':True}
    return g,base,C,view,work,before,inventory,jobs
