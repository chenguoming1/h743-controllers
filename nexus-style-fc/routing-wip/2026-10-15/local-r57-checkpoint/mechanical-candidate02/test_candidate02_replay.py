"""Bounded negative/replay tests for the isolated candidate transaction. No native calls."""
import subprocess,sys,tempfile,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent;P=R/'candidate-02/nexus-style-fc';T=P/'tools';B=R/'rollback-r54-source/nexus-style-fc/hardware'
sys.path.insert(0,str(T));import apply_header_interface as tx
base=['--main',str(B/'nexus-style-fc.kicad_pcb'),'--child',str(B/'header-board/nexus-header-board.kicad_pcb'),'--child-schematic',str(B/'header-board/nexus-header-board.kicad_sch'),'--expect-main','5677fb38db7d7e19cd3afa9dd5da61bbd9932ed0be7f6f2899f7bf4bf58e8fc9','--expect-child','99d06c7ec685f776f357958c22f684f198f9ef5bf7e9bed437833c9d6aadfba0','--expect-child-schematic','7514ce37f03803bdbce5a2f54f290ff78e6cf1f719f5d51fb3509116a4e1cb10']
results={}
with tempfile.TemporaryDirectory(prefix='nexus-mechanical-replay-') as tmp:
    tmp=Path(tmp)
    def run(args,expect,flag=None):
        cmd=[sys.executable]+([flag] if flag else [])+[str(T/'apply_header_interface.py')]+args
        r=subprocess.run(cmd,capture_output=True,text=True)
        assert (r.returncode==0)==expect,(r.stdout,r.stderr)
        return r
    a=base+['--out',str(tmp/'success')];run(a,True)
    for rel in ['nexus-style-fc.kicad_pcb','header-board/nexus-header-board.kicad_pcb','header-board/nexus-header-board.kicad_sch']:
        assert (tmp/'success'/rel).read_bytes()==(P/'hardware'/rel).read_bytes()
    results['fresh_replay_exact_to_candidate_native_and_header_schematic']=True
    run(a,False);results['refuses_existing_output_directory']=True
    a=base.copy();a[a.index('--expect-main')+1]='0'*64;run(a+['--out',str(tmp/'bad-hash')],False);assert not (tmp/'bad-hash').exists();results['wrong_hash_fails_before_output']=True
    original=(B/'nexus-style-fc.kicad_pcb').read_text();board=tx.s.parse(original);j=next(f for f in tx.s.find(board,'footprint') if tx.ref(f)=='J1');tx.first(j,'at')[1]='100.01';changed=tx.s.dump(board)+'\n';f=tmp/'mutated-main.kicad_pcb';f.write_text(changed)
    a=base.copy();a[a.index('--main')+1]=str(f);a[a.index('--expect-main')+1]=hashlib.sha256(f.read_bytes()).hexdigest();run(a+['--out',str(tmp/'bad-anchor')],False);assert not (tmp/'bad-anchor').exists();results['matching_hash_with_changed_J1_anchor_fails_before_output']=True
    board=tx.s.parse(original);z=next(z for z in tx.s.find(board,'zone') if tx.s.find(z,'keepout'));tx.first(tx.first(z,'polygon'),'pts')[1][1]='111.31';f.write_text(tx.s.dump(board)+'\n');a[a.index('--expect-main')+1]=hashlib.sha256(f.read_bytes()).hexdigest();run(a+['--out',str(tmp/'bad-zone-anchor')],False);assert not (tmp/'bad-zone-anchor').exists();results['matching_hash_with_changed_slot_keepout_fails_before_output']=True
    for flag in ('-O','-OO'):run(base+['--out',str(tmp/'optimized')],False,flag);assert not (tmp/'optimized').exists()
    results['optimized_python_refused_before_output']=True
    manifest=json.loads((tmp/'success/source-manifest.json').read_text());assert all(hashlib.sha256((P/k).read_bytes()).hexdigest()==v for k,v in manifest['implementation_sha256'].items());results['implementation_manifest_matches_current_sources']=True
(R/'candidate02-replay-tests.json').write_text(json.dumps({'tests':results,'transaction_sha256':hashlib.sha256((T/'apply_header_interface.py').read_bytes()).hexdigest()},indent=2)+'\n')
print(json.dumps(results,indent=2))
