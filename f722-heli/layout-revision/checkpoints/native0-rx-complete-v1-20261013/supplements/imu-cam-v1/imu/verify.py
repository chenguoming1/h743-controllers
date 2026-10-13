"""Read-only, standard-library checks for the static IMU orientation receipt."""
import argparse,hashlib,json,re,math
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--checkpoint-root',type=Path,required=True);a=ap.parse_args()
P=Path(__file__).resolve().parent;r=json.loads((P/'receipt.json').read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
def block(s,start):
 depth=0;quote=False;escape=False
 for i in range(start,len(s)):
  c=s[i]
  if escape:escape=False;continue
  if quote and c=='\\':escape=True;continue
  if c=='"':quote=not quote;continue
  if quote:continue
  if c=='(':depth+=1
  if c==')':
   depth-=1
   if depth==0:return s[start:i+1]
 raise AssertionError('unbalanced block')
for x in r['sources']:
 b=(P/x['file']).read_bytes();assert sha(b)==x['sha256'];assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['git_blob_sha1']
H=a.checkpoint_root/'hardware';b=(H/'f722-heli.kicad_pcb').read_bytes();assert sha(b)==r['pcb_sha256'];s=b.decode()
for m in re.finditer(r'\(footprint\s+"',s):
 fp=block(s,m.start())
 if re.search(r'\(property\s+"Reference"\s+"U2"',fp):break
else:raise AssertionError('U2 missing')
assert sha(fp.encode())==r['U2_board_record_sha256']
assert '(at 23.209999 11.6)'in fp and '(layer "F.Cu")'in fp
lib=H/'library/F722_Heli.pretty/LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y.kicad_mod';assert sha(lib.read_bytes())==r['footprint_sha256']
expected={x['pad']:x['local_xy_mm']for x in r['pads']}
for source in [fp,lib.read_text()]:
 actual={int(m.group(1)):[float(x)for x in re.search(r'\(at ([^)]+)\)',block(source,m.start())).group(1).split()[:2]]for m in re.finditer(r'\(pad\s+"(\d+)"',source)}
 assert actual==expected and len(actual)==14
# Algebraic evaluation of the pinned yaw matrix. This is not a firmware execution.
z=math.pi/2;c=math.cos(z);si=math.sin(z);T=[[c,si,0],[-si,c,0],[0,0,1]];S=r['standard_transform_output_from_raw']
assert max(abs(T[i][j]-S[i][j])for i in range(3)for j in range(3))<1e-15
print(json.dumps({'static_orientation_consistent':True,'mounting_reference':'F.Cu up; A/B edge (PCB -Y) forward','pad_centers_verified':14,'source_blobs_verified':len(r['sources']),'CW90_and_yaw900_are_alternatives':True,'runtime_qualified':False}))
