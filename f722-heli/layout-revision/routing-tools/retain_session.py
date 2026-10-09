#!/usr/bin/env python3
"""Discard explicitly rejected, newly routed logical nets from a real SES.
Run with KiCad Python. Retains exact text and geometry of all other session nets.
"""
import argparse,collections,hashlib,json,re
from pathlib import Path
from import_session import ses_routes,from_snapshot,key
ap=argparse.ArgumentParser();ap.add_argument('--model',type=Path,required=True);ap.add_argument('--session',type=Path,required=True);ap.add_argument('--engine-report',type=Path,required=True);ap.add_argument('--exclude',action='append',required=True);ap.add_argument('--reason',required=True);ap.add_argument('--out-prefix',type=Path,required=True);a=ap.parse_args();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();m=json.loads(a.model.read_text());report=json.loads(a.engine_report.read_text());assert report['model_sha256']==sha(a.model);original=ses_routes(a.session);assert collections.Counter(map(key,original))==collections.Counter(map(key,from_snapshot(report)));excluded=set(a.exclude);assert excluded<={r['logical_net']for r in original};assert not(excluded&set(m['source_logical_nets'].values())),'Cannot discard pre-existing source routes';text=a.session.read_text()
for net in sorted(excluded):
 pattern=r'\(\s*net\s+(?:'+re.escape(json.dumps(net))+'|'+re.escape(net)+r')(?=\s|\))';matches=list(re.finditer(pattern,text));assert len(matches)==1,(net,'Expected one actual session net block');start=matches[0].start();depth=0;quoted=False;escape=False;end=None
 for i in range(start,len(text)):
  c=text[i]
  if quoted:
   if escape:escape=False
   elif c=='\\':escape=True
   elif c=='"':quoted=False
  elif c=='"':quoted=True
  elif c=='(':depth+=1
  elif c==')':
   depth-=1
   if depth==0:end=i+1;break
 assert end is not None;text=text[:start]+text[end:]
a.out_prefix.parent.mkdir(parents=True,exist_ok=True);ses=Path(str(a.out_prefix)+'.ses');out=Path(str(a.out_prefix)+'.after.json');ses.write_text(text);retained=ses_routes(ses);assert collections.Counter(map(key,retained))==collections.Counter(key(r)for r in original if r['logical_net']not in excluded)
projection={'original_session_sha256':sha(a.session),'original_engine_report_sha256':sha(a.engine_report),'excluded_new_logical_nets':sorted(excluded),'reason':a.reason,'remaining_session_geometry_exact_subset':True,'source_routes_discarded':False};report['routes']=[r for r in report['routes']if not excluded.intersection(r['nets'])];report.pop('areas',None);report.pop('contact_partitions',None);report['route_projection']=projection;out.write_text(json.dumps(report,indent=2)+'\n');receipt={'board_sha256':m['board_sha256'],'model_sha256':sha(a.model),'session_sha256':sha(ses),'engine_report_sha256':sha(out),'filter_source_sha256':sha(__file__),**projection};Path(str(a.out_prefix)+'.retention.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
