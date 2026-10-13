"""Non-executing source excerpts. See SOURCE-PROVENANCE.json for original identity.
Dependencies belong to the original implementation; use reproduction/replay_native.py
for the standalone verifier and exact sealed-recipe replay.
"""

def scope():return g.read(H/'R35-exact-half-turn-source.json')

def pose_map(profile,delta=None):
 poses=profile.get('pose_changes',{})
 if not poses:return {}
 s=scope();g.require(poses=={'R35':NEW},'Only exact R35 B90 to B270 half-turn allowed')
 g.require(profile['pose_source_sha256']==g.sha(H/'R35-exact-half-turn-source.json'),'Unbound exact R35 pose source')
 if delta is not None:g.require(delta.get('pose_changes')==poses and delta.get('poses_and_nets_unchanged') is False and delta.get('pad_net_identities_unchanged') is True,'Full candidate must explicitly declare exact R35 rotation and held pad nets')
 return poses

def verify(before,after,profile):
 s=scope();old={x['ref']:x for x in before['footprints']};new={x['ref']:x for x in after['footprints']};g.require(pose_map(profile)=={'R35':NEW},'Exact half-turn not selected')
 g.require(old['R35']==s['source_footprint'],'R35 source record changed');g.common.verify_footprint(old['R35'],new['R35'],OLD,NEW)
 a={r['uuid']:r for r in before['objects']};b={r['uuid']:r for r in after['objects']}
 for u,row in s['source_pads'].items():
  g.require(a[u]==row,'R35 source pad record changed');g.common.verify_pad(row,b[u],OLD,NEW)
  g.require(b[u]['xy']==s['expected_pad_map'][u]['xy'] and b[u]['key']==row['key'] and b[u]['net']==row['net'],'Actual R35 pin map differs')
 return {'R35_footprint_UUID':s['source_footprint']['uuid'],'source_pose':OLD,'candidate_pose':NEW,'exact_actual_pad_map':s['expected_pad_map'],'same_package_value_pin_net_identity_and_local_apertures':True}

def verify_auxiliary(source,actual):
 s=scope();pads=set(s['source_pads'])
 for u in pads:
  g.require(set(source['inside'][u])==set(actual['inside'][u]),'R35 inside layer inventory changed')
  for l,rows in source['inside'][u].items():g.require(g.common.polygons_id(g.common.transformed_polygons(rows,OLD,NEW))==g.common.polygons_id(actual['inside'][u][l]),'Exact rotated inside contour differs')
 a=source['mechanics']['R35'];b=actual['mechanics']['R35'];g.require({k:v for k,v in a.items() if k!='courtyards'}=={k:v for k,v in b.items() if k!='courtyards'},'R35 mechanics identity differs')
 g.require(set(a['courtyards'])==set(b['courtyards']),'R35 courtyard layers differ')
 for l,rows in a['courtyards'].items():g.require(g.common.polygons_id(rows)==g.common.polygons_id(b['courtyards'][l]),'R35 actual courtyard geometry changed')
 return pads
