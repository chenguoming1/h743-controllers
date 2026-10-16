#!/usr/bin/env python3
"""Read-only canonical source/native and manufacturing consistency checks."""
import sys
sys.dont_write_bytecode = True
import importlib.util, json, hashlib, copy, math, csv
from pathlib import Path
import pcbnew
R=Path(__file__).resolve().parents[3]
O=Path(__file__).resolve().parent
S=R/'docs/validation/stage36'
sys.path.insert(0,str(R/'tools'))
import design, pcbutil, make_footprints, design_header
spec=importlib.util.spec_from_file_location('placement_sync_readonly',S/'verification/main-source-synchronization/synchronize_main.py')
sync=importlib.util.module_from_spec(spec);spec.loader.exec_module(sync)
assert pcbnew.Version()=='10.0.7',pcbnew.Version()
legacy=copy.deepcopy(design.PARTS)
parts=design.get_main_parts()
assert design.PARTS==legacy
assert parts==design.get_main_parts()
assert parts is not design.PARTS
parts[0]['place']=('test-independence',)
assert design.PARTS==legacy
parts=design.get_main_parts()
assert parts==design.get_main_parts()
b=pcbnew.LoadBoard(str(R/'hardware/nexus-style-fc.kicad_pcb'))
snap=sync.board_snapshot(b)
sync.verify_identities_and_nets(parts,snap)
placements=sync.extract_placements(snap,(100.0,100.0),make_footprints.DESIGN_SHIFT,pcbutil.Board)
pose_diff={p['ref']:{'source':p['place'],'native_replayed':placements[p['ref']]} for p in parts if not sync.near_equal(p['place'],placements[p['ref']])}
assert not pose_diff,pose_diff
accepted=json.loads((S/'verification/main-source-synchronization/placement-pad-snapshot.json').read_text())
# Only the nine declared artwork-only footprint identifiers may differ.
variants=json.loads((O/'artwork-variants.json').read_text())
for ref, change in variants.items():
    assert accepted[ref]['footprint']==change['old']
    accepted[ref]['footprint']=change['new']
assert sync.near_equal(snap,accepted),'Unexpected pad, net, placement or part change'
bom=sync.verify_bom_cpl(R/'manufacturing/nexus-style-fc',parts,b,snap)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
main=dict(get_main_parts='PASS; independent main selection leaves legacy PARTS unchanged',footprint_count=len(snap),pad_count=sum(len(x['pads']) for x in snap.values()),placement_differences=pose_diff,source_pin_nets='PASS',native_snapshot_vs_accepted_stage36='PASS; declared artwork-only footprint identifiers allowed',placement_snapshot_sha256=sync.stable_hash(snap),bom_cpl=bom)
main['native_board_net_names']=sorted(str(x) for x in b.GetNetsByName().keys() if str(x))
main['accepted_bom_cpl_byte_identical']={p.name:sha(p)==sha(S/'verification/main-source-synchronization/bom-cpl'/p.name) for p in (R/'manufacturing/nexus-style-fc').glob('*.csv')}
assert main['accepted_bom_cpl_byte_identical']['nexus-style-fc-cpl-jlc.csv']
main['bom_changes']='Artwork-only footprint identities split 48 predecessor groups into 51; same 83 selected parts/values/LCSC identities.'
child=pcbnew.LoadBoard(str(R/'hardware/header-board/nexus-header-board.kicad_pcb'))
csnap=sync.board_snapshot(child)
sync.verify_identities_and_nets(design_header.PARTS,csnap)
# Check the child BOM/CPL directly with the same tolerance and orientation rules.
cp={p['ref']:p for p in design_header.PARTS if p.get('lcsc','').startswith('C')}
base=R/'manufacturing/nexus-header-board'
br=list(csv.DictReader((base/'nexus-header-board-bom-jlc.csv').open()))
cr=list(csv.DictReader((base/'nexus-header-board-cpl-jlc.csv').open()))
byref={r:row for row in br for r in row['Designator'].split(',')}
assert set(byref)==set(cp)
assert len(cr)==len(cp) and {r['Designator'] for r in cr}==set(cp)
for ref,p in cp.items():
 row=byref[ref]
 assert (row['Comment'],row['Footprint'],row['LCSC Part #'])==(p['value'],p['fp'].split(':')[1],p['lcsc'])
ox,oy=sync.mm(child.GetDesignSettings().GetAuxOrigin()); errs=[]
for row in cr:
 f=csnap[row['Designator']];x,y=f['position_mm']
 err=math.hypot(float(row['Mid X'].removesuffix('mm'))-(x-ox),float(row['Mid Y'].removesuffix('mm'))-(oy-y));errs.append(err)
 assert err<=0.00008
 assert row['Layer']==('Top' if f['side']=='F' else 'Bottom')
 assert sync.norm_angle(float(row['Rotation']))==sync.norm_angle(round(f['orientation_deg']))
baseline_child_blobs={'nexus-header-board-B_Cu.gbl': '54b7def5f5c75f889738dc57f960db66a4309801', 'nexus-header-board-B_Mask.gbs': 'b1fedf3eb10045bfd044b1ded77a8892f5d9352c', 'nexus-header-board-B_Paste.gbp': 'ecc4a19d3f8109f63ca5c382ec1faab2ab6a3549', 'nexus-header-board-B_Silkscreen.gbo': 'af3807bae96af58345aa1903dfa22335c0c9daa2', 'nexus-header-board-Edge_Cuts.gm1': 'ca4624f25bd895c7db85a8dc5f0e4e14c40e5040', 'nexus-header-board-F_Cu.gtl': '298923e9782cc4b731e20897e09078ad6983f4af', 'nexus-header-board-F_Mask.gts': '53724597120c4258632ea672eedb292378046177', 'nexus-header-board-F_Paste.gtp': '9208dbdb370001810c88755bcf4fcc81ba251f11', 'nexus-header-board-F_Silkscreen.gto': '130e5e4a4b129ee079e2fc693aa69c94b1080088', 'nexus-header-board-NPTH.drl': '77a8b89c476433a8d44241bd880b9cdfa943c579', 'nexus-header-board-PTH.drl': 'c392f0877d40c2d44937051d7930e8055d6c0824', 'nexus-header-board-job.gbrjob': '5611dd8f51e44478d2cee8cf21b5a24082de19b4', 'nexus-header-board-bom-jlc.csv': 'cc913e2a19083dc87057c2c0ff382b4259f9f8c6', 'nexus-header-board-cpl-jlc.csv': '888a741863ffe70f22ed39839b6c679e838107a3', 'nexus-header-board-gerbers.zip': 'd1ab2b1816e3c3333b598c6f06252c400d66cbb3'}
child_result=dict(footprint_count=len(csnap),pad_count=sum(len(x['pads']) for x in csnap.values()),source_pin_nets='PASS',bom_groups=len(br),cpl_parts=len(cr),max_cpl_position_error_mm=max(errs,default=0),accepted_bom_cpl_byte_identical={p.name:hashlib.sha1(b'blob '+str(len(p.read_bytes())).encode()+b'\0'+p.read_bytes()).hexdigest()==baseline_child_blobs[p.name] for p in base.glob('*.csv')})
assert all(child_result['accepted_bom_cpl_byte_identical'].values())
assert sha(R/'hardware/header-board/nexus-header-board.kicad_pcb')=='b49ef4108ab0b85d4cd96fac22553e3bc16b214f5acde148a8680e1212097ee6'
report=dict(status='PASS; read-only source/native and manufacturing consistency; not manufacturing approval',kicad=pcbnew.Version(),main=main,child=child_result,scope='Read-only verification; imported pinned stage36 helper functions only. Report files are written beside this script.')
(O/'source-consistency.json').write_text(json.dumps(report,indent=2)+'\n')
(O/'main-placement-pad-snapshot.json').write_text(json.dumps(snap,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='main'},indent=2));print(json.dumps({k:v for k,v in main.items() if k not in ('native_board_net_names','bom_cpl')},indent=2));print({k:v for k,v in bom.items() if k!='rotations'})
