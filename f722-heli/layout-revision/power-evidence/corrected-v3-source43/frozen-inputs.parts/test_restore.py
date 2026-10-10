"""Exercise corruption, missing chunk, ordering and overwrite refusals without changing inputs."""
import json,shutil,subprocess,tempfile
from pathlib import Path
root=Path(__file__).resolve().parent
def run(d,out):return subprocess.run(['python3',str(d/'restore.py'),'--output',str(out)],capture_output=True)
def check(ok,message):
    if not ok:raise RuntimeError(message)
with tempfile.TemporaryDirectory(prefix='f722-split-controls-') as tmp:
    tmp=Path(tmp);d=tmp/'parts';shutil.copytree(root,d);out=tmp/'output.tar.gz'
    check(run(d,out).returncode==0,'Valid reconstruction failed')
    check(run(d,out).returncode==0,'Identical output verification failed')
    out.write_bytes(b'preserve existing data')
    check(run(d,out).returncode!=0 and out.read_bytes()==b'preserve existing data','Overwrite refusal failed')
    out.unlink();first=d/'part-0000.bin';original=first.read_bytes()
    first.write_bytes(bytes([original[0]^1])+original[1:])
    check(run(d,out).returncode!=0 and not out.exists(),'Corruption refusal failed')
    first.unlink()
    check(run(d,out).returncode!=0 and not out.exists(),'Missing chunk refusal failed')
    first.write_bytes(original);m=json.loads((d/'manifest.json').read_text());m['parts'][1]['offset']+=1
    (d/'manifest.json').write_text(json.dumps(m))
    check(run(d,out).returncode!=0 and not out.exists(),'Offset refusal failed')
print('Passed valid reconstruction, identical output and four refusal controls.')
