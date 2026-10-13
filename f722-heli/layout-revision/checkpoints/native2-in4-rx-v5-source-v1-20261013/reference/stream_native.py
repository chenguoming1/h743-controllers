import gzip,json

def stream_field(path,field,array=False):
 marker='"'+field+'":';dec=json.JSONDecoder()
 with gzip.open(path,'rt') as f:
  b=''
  while marker not in b:
   x=f.read(65536);assert x,field;b=b[-len(marker):]+x
  b=b.split(marker,1)[1].lstrip()
  if array:
   assert b[0]=='[';b=b[1:]
  while True:
   b=b.lstrip(' \t\r\n,')
   if array and b.startswith(']'):return
   try:o,e=dec.raw_decode(b)
   except json.JSONDecodeError:
    x=f.read(65536);assert x;b+=x;assert len(b)<32*1024**2;continue
   yield o;b=b[e:]
   if not array:return
