#!/usr/bin/env python3
"""Refresh only the exact selected minimal V19 evidence; never include raw dumps."""
import argparse,hashlib,json,lzma
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workspace',type=Path,required=True);a=ap.parse_args();packet=ROOT/'tests/checkpoint49';index=json.loads((packet/'raw-evidence.json').read_bytes())
 assert index['schema']=='f722-selected-evidence/v2';inputs={}
 for name,info in index['files'].items():
  data=(a.workspace/name).read_bytes();assert sha(data)==info['sha256']and len(data)==info['bytes'];inputs[name]=data
 for name,data in inputs.items():
  info=index['files'][name]
  if 'compressed_file'in info:
   data=lzma.compress(data,preset=1);assert sha(data)==info['compressed_sha256'];dest=packet/info['compressed_file']
  else:dest=packet/info['file']
  dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
 print(json.dumps({'passed':True,'selected_exact_files':len(inputs),'excluded_raw_files':len(index['excluded_files']),'excluded_data_read_or_copied':False,'native_replay_inputs_complete':False}))
if __name__=='__main__':main()
