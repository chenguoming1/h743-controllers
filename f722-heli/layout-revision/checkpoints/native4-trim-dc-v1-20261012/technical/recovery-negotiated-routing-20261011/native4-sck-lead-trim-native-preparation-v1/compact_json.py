"""Lossless complete JSON storage; streamed plaintext digest, no temporary copy."""
import gzip,hashlib,json
from pathlib import Path

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 return h.hexdigest()

def plaintext_binding(path):
 h=hashlib.sha256();count=0
 with gzip.open(path,'rb') as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk);count+=len(chunk)
 return {'sha256':h.hexdigest(),'bytes':count}

def write(path,value):
 path=Path(path)
 if path.exists():raise ValueError('Fresh compressed artifact required')
 h=hashlib.sha256();count=0;encoder=json.JSONEncoder(sort_keys=True,separators=(',',':'),allow_nan=False)
 with path.open('xb') as raw:
  with gzip.GzipFile(filename='',mode='wb',fileobj=raw,compresslevel=6,mtime=0) as f:
   pending=bytearray()
   for part in encoder.iterencode(value):
    data=part.encode();pending.extend(data);h.update(data);count+=len(data)
    if len(pending)>=1048576:f.write(pending);pending.clear()
   pending.extend(b'\n');f.write(pending);h.update(b'\n');count+=1
 plain={'sha256':h.hexdigest(),'bytes':count}
 if plaintext_binding(path)!=plain:raise ValueError('Compressed artifact failed full decompressed hash verification')
 return {'path':path.name,'encoding':'gzip','compressed':{'sha256':sha(path),'bytes':path.stat().st_size},'uncompressed':plain,'decompression_verified':True}

def read(path,binding):
 path=Path(path)
 if binding['encoding']!='gzip' or sha(path)!=binding['compressed']['sha256'] or path.stat().st_size!=binding['compressed']['bytes'] or plaintext_binding(path)!=binding['uncompressed']:raise ValueError('Compressed artifact binding changed')
 with gzip.open(path,'rt',encoding='utf-8') as f:return json.load(f)

read_native=read
read_auxiliary=read
