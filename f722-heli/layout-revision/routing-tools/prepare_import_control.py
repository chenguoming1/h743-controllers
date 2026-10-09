"""Create an explicitly synthetic SES/report pair for native importer testing.

These fixtures are not router output and never count as a routed candidate.
The independent engine clearance control must approve the chosen position.
"""
import argparse
import hashlib
import json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--model',type=Path,required=True);ap.add_argument('--via-control',type=Path,required=True);ap.add_argument('--out-prefix',type=Path,required=True);a=ap.parse_args()
    m=json.loads(a.model.read_text());control=json.loads(a.via_control.read_text());model_hash=hashlib.sha256(a.model.read_bytes()).hexdigest();assert control['passed'] and control['model_sha256']==model_hash
    xy=next(c['xy'] for c in control['cases'] if c['actual_allowed']);end=[xy[0]+.4,xy[1]];s=lambda x:round(x*1e5)
    ses=f'(session "synthetic-native-import-control" (routes (resolution mm 100000) (network_out (net FLASH_CS (wire (path F.Cu 12700 {s(xy[0])} {-s(xy[1])} {s(end[0])} {-s(end[1])})) (via VIA_450_200 {s(xy[0])} {-s(xy[1])})))))\n'
    report={'synthetic_import_fixture':True,'route_solver_used':False,'board_sha256':m['board_sha256'],'model_sha256':model_hash,'routes':[{'kind':'track','fixed':'NOT_FIXED','nets':['FLASH_CS'],'layer':'F.Cu','width':.127,'points':[xy,end]},{'kind':'via','fixed':'NOT_FIXED','nets':['FLASH_CS'],'xy':xy,'diameter':.45,'drill':.2}]}
    a.out_prefix.with_suffix('.ses').write_text(ses);a.out_prefix.with_suffix('.after.json').write_text(json.dumps(report,indent=2)+'\n');print('Created synthetic importer fixtures; no routing engine output is claimed.')

if __name__=='__main__':main()
