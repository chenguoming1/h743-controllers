#!/usr/bin/env python3
"""Bounded, separately bound symmetric GND-plane delta supplement."""
import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:
    os.environ[key]='1'
import gc,json,resource,sys,time
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(536870912,)*2)
resource.setrlimit(resource.RLIMIT_CPU,(60,)*2)
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
import check_candidate as c
BINDING_SHA='c2ef45f32af56e5538969dd208bf25a967fd2fb8a434d121c78a8769f72673b6'
RAW_SHA='dff63778a524168ff42bc176e67addc280a3c80458303bba3480a70201afe3bc'
def main():
    start=time.monotonic();bp=c.HERE/'binding-return-stitch-v2.json';rp=c.HERE/'physical-audit-return-stitch-v1.json'
    c.require(c.sha(bp)==BINDING_SHA and c.sha(rp)==RAW_SHA,'Bound source changed')
    files=c.read(bp)['files'];o=c.read(c.HERE/'obligations.json');layers=list(o['GND_planes'])
    compact={}
    for role in ['source_native','candidate_native']:
        path=c.bound(files[role]);native=c.read(path)
        zones={z['uuid']:z for z in native['zones']}
        fills={layer:zones[uid]['filled'][layer] for layer,uid in o['GND_planes'].items()}
        drills=[{key:row[key] for key in ['uuid','drill','barrel_layers','npth'] if key in row} for row in native['objects'] if row.get('drill')]
        original_drill_digest=c.digest(drills)
        for row in drills:
            row['barrel_layers']=[layer for layer in row.get('barrel_layers',[]) if layer in layers]
        drills=[row for row in drills if row.get('npth') or row['barrel_layers']]
        compact[role]={'fills':fills,'drills':drills,'original_all_drill_records_sha256':original_drill_digest}
        del native,zones,fills,drills;gc.collect()
    sys.path.insert(0,str(c.ROOT/'python-deps'))
    direct=c.load_module('symmetric_fixed_contact_adapter',c.bound(files['contact_adapter']));_,k,_=direct.kernels()
    geometry={};evidence={}
    for role,view in compact.items():
        holes=k.hole_map(view['drills'],layers)
        geometry[role]={layer:{'saved':k.native_polygons(rows)} for layer,rows in view['fills'].items()}
        for layer,shapes in geometry[role].items():shapes['conductive']=shapes['saved'].difference(holes[layer])
        evidence[role]={'file':files[role],'original_all_drill_records_sha256':view['original_all_drill_records_sha256'],'physical_drill_records_in_two_layers_sha256':c.digest(view['drills']),'drill_UUIDs':sorted(r['uuid'] for r in view['drills']),'native_fills_sha256':{layer:c.digest(rows) for layer,rows in view['fills'].items()},'hole_union_area_mm2':{layer:s.area for layer,s in holes.items()}}
        del holes
    rows=[]
    for layer,uid in o['GND_planes'].items():
        row={'layer':layer,'zone_uuid':uid}
        for representation in ['saved','conductive']:
            before=geometry['source_native'][layer][representation];after=geometry['candidate_native'][layer][representation]
            added=after.difference(before);removed=before.difference(after)
            row[representation]={'source_area_mm2':before.area,'candidate_area_mm2':after.area,'added_mm2':added.area,'removed_mm2':removed.area,'net_change_mm2':after.area-before.area,'source_components':len(k.polygon_parts(before)),'candidate_components':len(k.polygon_parts(after)),'added_bounds_mm':list(added.bounds),'removed_bounds_mm':list(removed.bounds),'added_WKB_sha256':__import__('hashlib').sha256(added.wkb).hexdigest(),'removed_WKB_sha256':__import__('hashlib').sha256(removed.wkb).hexdigest()}
        rows.append(row)
    raw=c.read(rp)
    result={'schema':'f722-return-stitch-symmetric-GND-delta/v1','accepted_or_adopted':False,'candidate_native_plain_sha256':raw['candidate_sha256'],'source_native_sha256':raw['native4_sha256'],'method':'Compare saved native fills to saved native fills, then compare each source after Boolean subtraction of its own actual drill union. No geometry repair, simplification or rule change.','source_geometry':evidence,'per_plane':rows,'raw_asymmetric_fields_preserved':raw['changed_via_plane_and_clearance_review']['removed_SCK_barrel_refill_review'],'raw_field_limitation':'Raw total areas compare saved source fill with drilled candidate fill; use these separately identified symmetric values for plane delta statements.','pad_topology_and_reference_gates_unchanged':True,'does_not_qualify_SI_ESD_current_or_assembly':True,'bindings':{'script':c.file_binding(__file__),'binding':c.file_binding(bp),'raw_audit':c.file_binding(rp),'contact_adapter':files['contact_adapter']},'elapsed_seconds':time.monotonic()-start,'peak_RSS_MiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024}
    c.require(c.sha(rp)==RAW_SHA,'Raw audit changed');out=c.HERE/'symmetric-plane-delta-v1.json';c.write(out,result)
    print(json.dumps({'output':c.file_binding(out),'per_plane':rows,'elapsed_seconds':result['elapsed_seconds'],'peak_RSS_MiB':result['peak_RSS_MiB']}))
if __name__=='__main__':main()
