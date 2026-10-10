"""Native project, actual-IO and retained-critical reference gates for standalone R2-to-SW1 closure."""
import pathlib,subprocess,os,json,hashlib,sys
H=pathlib.Path(__file__).resolve().parent;R=H.parents[2];S=R/'ordinary-routing/candidate56';D=H/'candidate01';N=R/'repo/f722-heli/layout-revision';K=R.parent/'kicad10-runtime';T=N/'signal-review/native';E=dict(os.environ,PYTHONPATH=str(R/'python-deps'))
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();write=lambda p,x:p.write_text(json.dumps(x,indent=2)+'\n')
h=sha(D/'f722-heli.kicad_pcb');sh=sha(S/'f722-heli.kicad_pcb');prov=read(D/'construction-provenance.json');nets=sorted({o['net']for o in prov['removed_source_records']+prov['added_records']}|{x['before']['net']for x in prov['changed_pad_records']})
write(D/'declared-footprint-transforms.json',dict(schema='f722-declared-footprint-transforms/v1',source_board_sha256=sh,board_sha256=h,changes={'R2':dict(before=[16,7.7,0,'F.Cu'],after=[40.2,6.2,270,'F.Cu'],flip_left_right=None)}))
def run(name,args,codes=(0,)):
 with (D/(name+'.log')).open('w')as f:r=subprocess.run([str(x)for x in args],env=E,stdout=f,stderr=subprocess.STDOUT)
 print(name,r.returncode,flush=True);assert r.returncode in codes,(name,r.returncode)
args=[K/'python',R/'integrated-routing/check_coordinated_integration.py',S/'f722-heli.kicad_pcb',D/'f722-heli.kicad_pcb','--footprint-transforms',D/'declared-footprint-transforms.json','--out',D/'native-coordinated-integration.json']
for net in nets:args+=['--net',net]
run('native-coordinated',args)
run('owner-erc',[K/'kicad-cli','sch','erc','--format','json','--output',D/'owner-erc.json',D/'f722-heli.kicad_sch'])
run('actual-io',[sys.executable,N/'protection-review/tools/check_protection_paths.py','--geometry',D/'f722-heli.native.json','--contracts',N/'protection-review/contracts/actual-io22.json','--out',D/'protection-actual-io.json'],(0,1))
run('reference-export',[K/'python',T/'export_signal_snapshot.py','--board',D/'f722-heli.kicad_pcb','--native-tools-dir',N/'scripts','--out',D/'reference-snapshot'])
run('reference-check',[sys.executable,T/'check_critical_reference.py','--board',D/'f722-heli.kicad_pcb','--snapshot',D/'reference-snapshot','--out',D/'reference-snapshot/critical-reference.json'])
run('reference-comparison',[sys.executable,T/'compare_reference_geometry.py','--before',S/'reference-snapshot','--after',D/'reference-snapshot','--before-board',S/'f722-heli.kicad_pcb','--after-board',D/'f722-heli.kicad_pcb','--out',D/'reference-comparison56.json'],(0,1))
run('i2c',[sys.executable,T/'check_signal_geometry.py','--board',D/'f722-heli.kicad_pcb','--snapshot',D/'reference-snapshot','--out',D/'i2c-geometry-review.json','--profile',T/'model-inputs.template.json','--critical-check',D/'owner-critical.json','--requirements',N/'signal-review/final-native-i2c-requirements.json','--calculations',N/'signal-review/stock-i2c-calculations.json'],(0,2))
run('spi',[K/'python',N/'checks/bind_stock_spi_review.py','--board',D/'f722-heli.kicad_pcb','--parts',D/'parts.json','--packet',N/'spi-review','--out',D/'stock-spi-binding.json'])
assert h==sha(D/'f722-heli.kicad_pcb');print('TERMINAL',h,nets,flush=True)
