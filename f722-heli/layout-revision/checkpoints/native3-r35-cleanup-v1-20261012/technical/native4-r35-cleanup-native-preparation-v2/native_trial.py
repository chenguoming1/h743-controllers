"""Non-executing source excerpts. See SOURCE-PROVENANCE.json for original identity.
Dependencies belong to the original implementation; use reproduction/replay_native.py
for the standalone verifier and exact sealed-recipe replay.
"""

def validate_contract(c):
 plan=guard.check_sources()
 require(c['schema']==SCHEMA and c['diagnostic_only'] is True and c['accepted_or_adopted'] is False,'Wrong complete-candidate contract')
 require(c['primary']=='local_v1' and c['variants']=={'local_v1':{}},'No footprint moves permitted')
 require(c['resources']==plan['resources'] and c['disk_budget']==plan['disk_budget'],'Resource/disk bounds changed')
 require(c['hardware']==plan['hardware'] and c['source_plan_sha256']==guard.PLAN_SHA,'Source pairing/plan changed')
 require(c['native_build']=='10.0.6+dfsg-1' and c['native_exporter_error_iu']==10,'Native runtime differs')
 for rel,h in c['bound_files'].items():require(sha(ROOT/rel)==h,'Bound candidate input/helper changed: '+rel)
 profile=read(c['profile']['path']);require(sha(c['profile']['path'])==c['profile']['sha256'],'Exact selected scope differs')
 delta=read(c['delta']['path']);require(sha(c['delta']['path'])==c['delta']['sha256'],'Exact complete recipe differs')
 guard.validate_delta(delta,profile,read(plan['paths']['source_index']))
 require(c['required_stages']==plan['mandatory_stages'],'Mandatory native/physical stages changed')
