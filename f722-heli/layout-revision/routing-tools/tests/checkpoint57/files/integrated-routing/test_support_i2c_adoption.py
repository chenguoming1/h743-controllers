"""Exercise typed audit binding and independent support-group refusals."""
from pathlib import Path
import copy,hashlib,json,tempfile
from verify_support_adoption import verify
R=Path(__file__).resolve().parents[1];D=R/'ordinary-routing/candidate43'
report=json.loads((D/'power-audit.json').read_text());prior=json.loads((R/'ordinary-routing/candidate41/power-audit.json').read_text());source=report['source_board_sha256'];board=report['board_sha256'];assert verify(report,prior,source,board,D)['nets']==28
controls=[]
for name in ['wrong_audit_hash','wrong_source','wrapper_pass_false','split_group','changed_pad_uuid','net_pass_false','source_group_claim_false']:
 row=copy.deepcopy(report)
 with tempfile.TemporaryDirectory(prefix='f722-support-control-') as td:
  directory=Path(td);audit=json.loads((D/report['audit']).read_text())
  if name=='wrong_source':row['source_board_sha256']='0'*64
  elif name=='wrapper_pass_false':row['passed']=False
  elif name=='split_group':row['nets']['+3V3_CORE']['groups'].append({'pad_uuids':[]})
  elif name=='changed_pad_uuid':row['nets']['+3V3_CORE']['groups'][0]['pad_uuids'][0]='wrong'
  elif name=='net_pass_false':row['nets']['+3V3_CORE']['passed']=False
  elif name=='source_group_claim_false':row['nets']['+3V3_CORE']['source_groups_exactly_preserved']=False
  audit['nets']=copy.deepcopy(row['nets']);path=directory/row['audit'];path.write_text(json.dumps(audit));row['audit_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
  if name=='wrong_audit_hash':row['audit_sha256']='0'*64
  try:verify(row,prior,source,board,directory)
  except AssertionError:controls.append({'name':name,'rejected':True})
  else:raise RuntimeError('Accepted invalid proof: '+name)
out={'passed':True,'controls':controls,'typed_positive_nets':28,'scope':'Temporary fixture defects leave every native source and sealed audit unchanged; nested-group controls rebind the fixture audit hash so topology checks themselves must refuse.','script_sha256':hashlib.sha256((R/'integrated-routing/verify_support_adoption.py').read_bytes()).hexdigest()};(R/'integrated-routing/support-i2c-adoption-controls.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
