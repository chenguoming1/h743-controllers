#!/usr/bin/env python3
"""Recover selected minimal evidence. Excluded raw files require external inputs."""
import argparse,hashlib,json,lzma,importlib.util
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parent
def digest(b):return hashlib.sha256(b).hexdigest()
def safe(n):
 if not isinstance(n,str)or not n or '\\'in n or PurePosixPath(n).is_absolute()or any(x in ('','.','..')for x in n.split('/')):raise ValueError('Unsafe evidence path')
 return Path(n)
class Evidence:
 def __init__(self,root=ROOT):self.root=root;self.index=json.loads((root/'raw-evidence.json').read_bytes())
 def __enter__(self):assert self.index['schema']=='f722-selected-evidence/v2';return self
 def __exit__(self,*_):pass
 def bytes(self,name):
  safe(name)
  if name in self.index['excluded_files']:raise FileNotFoundError('Excluded raw input: '+name)
  i=self.index['files'][name]
  if 'file'in i:b=(self.root/safe(i['file'])).read_bytes()
  else:
   raw=(self.root/safe(i['compressed_file'])).read_bytes();assert digest(raw)==i['compressed_sha256'];b=lzma.decompress(raw)
  assert digest(b)==i['sha256']and len(b)==i['bytes'],name;return b
 def verify(self,name):self.bytes(name)
 def json(self,name):return json.loads(self.bytes(name))
 def put(self,name,out):
  b=self.bytes(name);p=out/safe(name);p.parent.mkdir(parents=True,exist_ok=True)
  if p.exists():assert p.read_bytes()==b;return
  with p.open('xb')as f:f.write(b)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--path',action='append');ap.add_argument('--base-project',type=Path);a=ap.parse_args()
 if a.out.exists():raise FileExistsError('Output must be new')
 with Evidence()as e:
  names=a.path or list(e.index['files'])
  for n in names:e.verify(n)
  projects={}
  if a.base_project:
   packet=ROOT.parents[1]/'sessions/recovery-v17';s=importlib.util.spec_from_file_location('recovery_v17',packet/'rebuild_historical_source.py');recovery=importlib.util.module_from_spec(s);s.loader.exec_module(recovery)
   projects={label:recovery.prepare_project(a.base_project,label,packet)for label in json.loads((packet/'paired-files.json').read_bytes())['sources']}
  a.out.mkdir(parents=True)
  for label,outputs in projects.items():
   for relative,data in outputs.items():
    p=a.out/'ordinary-routing'/label/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
  for n in names:e.put(n,a.out)
 print(json.dumps({'passed':True,'selected_evidence_files':len(names),'exact_project_recovery':len(projects),'excluded_raw_files_materialized':False,'native_replay_inputs_complete':False}))
if __name__=='__main__':main()
