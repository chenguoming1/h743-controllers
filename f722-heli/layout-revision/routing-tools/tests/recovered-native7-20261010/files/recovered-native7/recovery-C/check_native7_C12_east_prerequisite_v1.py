"""Bounded actual pad/courtyard and saved-crossing prerequisite; no route solver."""
import json,signal,time
from pathlib import Path
from native7_C12_shift_model_v1 import build,adapter,HERE

start=time.monotonic();signal.alarm(25)
g,base,C,view,work,before,replaced,out=build()
out.update(schema='f722-native7-C12-east-prerequisite/v1',selected=False,native_board_edited=False,routing_executed=False)
job=next(z for z in C._jobs(g) if z['name']=='RX_down')
net,peers=C._view(view,job,work)
witness=[[26.236294869,10.998763379],[25.671020236,11.134466673]]
checks=g.check_track(net,'F.Cu',witness,width=.127,objects=peers)
out['saved_crossing_without_replacement_leaves']={'points':witness,'passed':C._passed(checks),'checks':checks[:12],'scope':'Local crossing only; the four full support branches remain mandatory before useful full RX approach can be claimed.'}
out['passed']=out['mechanical']['passed'] and all(z['passed'] for z in out['candidate_pad_checks']) and out['saved_crossing_without_replacement_leaves']['passed']
out['seconds']=time.monotonic()-start;out['script_sha256']=adapter.digest(__file__);out['model_sha256']=adapter.digest(HERE/'native7_C12_shift_model_v1.py')
path=HERE/'native7-C12-east-prerequisite-v1.json';path.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n');signal.alarm(0)
print(json.dumps({'passed':out['passed'],'seconds':out['seconds'],'receipt_sha256':adapter.digest(path),'pad_checks':out['candidate_pad_checks'],'mechanical':out['mechanical'],'crossing_passed':out['saved_crossing_without_replacement_leaves']['passed']},indent=2))
