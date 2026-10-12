"""Bounded read-only JSON reduction of the complete preserved raw result."""
import hashlib,json,resource,time,gzip
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
HERE=Path(__file__).resolve().parent
SOURCE=HERE/'run/result.json.gz'
EXPECTED='7c928ee42d873234998f8b8d56c05160253c66436057d2ba91a6ae86a80065d8'

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

class Stream:
    def __init__(self,path):
        self.f=gzip.open(path,'rt',encoding='utf-8');self.buf='';self.pos=0;self.eof=False;self.decoder=json.JSONDecoder();self.peak_buffer=0
    def fill(self):
        self.buf=self.buf[self.pos:];self.pos=0
        block=self.f.read(262144)
        if not block:self.eof=True
        self.buf+=block;self.peak_buffer=max(self.peak_buffer,len(self.buf))
        if len(self.buf)>32*1024**2:raise RuntimeError('Individual JSON value exceeds bounded32MiBbuffer')
    def peek(self):
        while True:
            while self.pos<len(self.buf) and self.buf[self.pos].isspace():self.pos+=1
            if self.pos<len(self.buf):return self.buf[self.pos]
            if self.eof:return ''
            self.fill()
    def expect(self,c):
        if self.peek()!=c:raise RuntimeError('Unexpected JSON token, expected '+c)
        self.pos+=1
    def value(self):
        self.peek()
        while True:
            try:v,end=self.decoder.raw_decode(self.buf,self.pos);self.pos=end;return v
            except json.JSONDecodeError:
                if self.eof:raise
                self.fill()
    def obj(self,visit):
        self.expect('{')
        if self.peek()=='}':self.pos+=1;return
        while True:
            key=self.value();self.expect(':');visit(key,self)
            if self.peek()=='}':self.pos+=1;return
            self.expect(',')
    def array(self,visit):
        self.expect('[')
        if self.peek()==']':self.pos+=1;return
        while True:
            visit(self)
            if self.peek()==']':self.pos+=1;return
            self.expect(',')

references={};certificate_hashes={};certificate_summary={};reference_count=0

def inspect_refs(value):
    global reference_count
    if isinstance(value,dict):
        for key,item in value.items():
            if key=='native_edge_noding_refs':
                for layer,row in item.items():
                    if set(row)!={'certificate_key','sha256'}:raise RuntimeError('Invalid certificate reference')
                    name=row['certificate_key'];h=row['sha256'];reference_count+=1
                    if name in references and references[name]!=h:raise RuntimeError('Conflicting certificate reference')
                    references[name]=h
            else:inspect_refs(item)
    elif isinstance(value,list):
        for item in value:inspect_refs(item)

def read_case(stream,out):
    value=stream.value();inspect_refs(value)
    value['fields']={net:{key:field[key] for key in ['copper_loss_W','sheet_loss_W','port_power_W','KCL_max_residual_A','iterations','native_edge_noding_refs'] if key in field} for net,field in value['fields'].items()}
    out.append(value)

def read_run(stream,out):
    run={}
    def item(key,s):
        if key=='cases':
            run[key]=[];s.array(lambda ss:read_case(ss,run[key]))
        else:
            run[key]=s.value();inspect_refs(run[key])
    stream.obj(item);out.append(run)

def read_certificate(key,s):
    receipt=s.value();h=hashlib.sha256()
    for piece in json.JSONEncoder(sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).iterencode(receipt):h.update(piece.encode())
    certificate_hashes[key]=h.hexdigest()
    rows=receipt.get('ring_certificates',[])
    certificate_summary[key]={'sha256':h.hexdigest(),'rings':len(rows),'grid_spacing_mm':receipt.get('grid_spacing_mm'),
      'native_vertices_changed':receipt.get('native_vertices_changed'),'epsilon_vertex_merging':receipt.get('epsilon_vertex_merging'),
      'all_exact_area_and_orientation_checks_pass':all(row.get('rational_area_preserved_exactly') is True and row.get('orientation_preserved') is True for row in rows),
      'maximum_area_integer_digits':max([len(p.lstrip('-')) for row in rows for p in row['rational_twice_area_nm2'].split('/')]+[0])}

start=time.monotonic();before=sha(SOURCE)
if before!=EXPECTED:raise RuntimeError('Raw result hash mismatch')
stream=Stream(SOURCE);result={}
def top(key,s):
    if key in ['runs','partial_runs_unqualified']:
        result[key]=[];s.array(lambda ss:read_run(ss,result[key]))
    elif key=='geometry_certificates':s.obj(read_certificate)
    else:result[key]=s.value()
stream.obj(top)
if stream.peek():raise RuntimeError('Trailing JSON data')
if any(certificate_hashes.get(key)!=value for key,value in references.items()):raise RuntimeError('Certificate hash mismatch')
if sha(SOURCE)!=before:raise RuntimeError('Raw result changed during reduction')
result['geometry_certificate_summaries']=certificate_summary
result['streaming_reduction']={'raw_result_path':str(SOURCE),'raw_result_sha256':before,'raw_bytes':SOURCE.stat().st_size,
  'reference_count':reference_count,'unique_referenced_certificates':len(references),'certificate_count':len(certificate_hashes),
  'all_certificate_reference_hashes_valid':True,'peak_input_buffer_characters':stream.peak_buffer,
  'peak_RSS_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'address_space_limit_MiB':512,
  'elapsed_seconds':time.monotonic()-start,'field_detail_omitted_from_reduction_but_retained_in_raw_result':True}
output=HERE/'reduced-result.json.gz'
with gzip.open(output,'xt',encoding='utf-8') as f:json.dump(result,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
print(json.dumps(result['streaming_reduction']),flush=True)
