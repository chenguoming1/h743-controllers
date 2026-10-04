#!/usr/bin/python3
"""Independent final archive-member, guard and submission parity check."""
import argparse,hashlib,json,zipfile
from pathlib import Path
H='cf16a6f5ceae65aad217e29eef23a60dbc8f15af743b363df03aa5a42c9c71dc'
sha=lambda data:hashlib.sha256(data).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--package',type=Path,required=True);ap.add_argument('--spec',type=Path,required=True);ap.add_argument('--project',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();P=a.project;spec=json.loads(a.spec.read_text());errors=[]
 def check(ok,msg):
  if not ok:errors.append(msg)
 with zipfile.ZipFile(a.package) as z:
  names=z.namelist();check(len(names)==len(set(names)),'Duplicate ZIP member');check(z.testzip() is None,'ZIP CRC failed');check(all(not n.startswith('/') and '..' not in Path(n).parts for n in names),'Unsafe archive path');check(all(not n.lower().endswith('.zip') for n in names),'Nested ZIP found');manifest=json.loads(z.read('SHA256_MANIFEST.json'));check(set(manifest)==set(names)-{'SHA256_MANIFEST.json'},'Root manifest coverage differs')
  for name,h in manifest.items():check(sha(z.read(name))==h,'Manifest member differs: '+name)
  for row in spec['files']:
   check(row['archive_path'] in names,'Spec file missing: '+row['archive_path'])
   if row['archive_path'] in names:check(sha(z.read(row['archive_path']))==row['sha256']==sha(Path(row['path']).read_bytes()),'Spec/source/archive mismatch: '+row['archive_path'])
  check(sha(z.read('native/controller.kicad_pcb'))==sha((P/'controller.kicad_pcb').read_bytes())==H,'Native board differs');guard=json.loads(z.read('native/review/p6-qualified-export-guard.json'));source_count=evidence_count=0
  for group in ['qualified_source_files','qualification_evidence_files']:
   for relative,h in guard[group].items():
    member='native/'+relative;check(member in names,'Required portable export-guard input absent: '+member)
    if member in names:check(sha(z.read(member))==h,'Portable guard input differs: '+member)
   if group=='qualified_source_files':source_count=len(guard[group])
   else:evidence_count=len(guard[group])
  qmember='native/'+guard['qualification_report'];check(sha(z.read(qmember))==guard['qualification_report_sha256'],'Source qualification differs');q=json.loads(z.read(qmember));check(q['candidate_sha256']==H and not q['errors'],'Source qualification not current/clean')
  final_member='native/review/p6-final-release-qualification.json';final=json.loads(z.read(final_member));check(final['native_sha256']==H and final['status']=='PASS P6 FINAL RELEASE QUALIFICATION' and not final['errors'],'Final qualification not current/clean');check(final['source_qualification_sha256']==sha(z.read(qmember)),'Final/source qualification chain differs')
  release_manifest=json.loads(z.read('release/SHA256_MANIFEST.json'));check(sha(z.read('release/SHA256_MANIFEST.json'))==final['release_manifest_sha256'],'Original release manifest differs')
  for name,h in release_manifest.items():check('release/'+name in names and sha(z.read('release/'+name))==h,'Original immutable export differs: '+name)
  reconstruction=json.loads(z.read('reconstruction/packet-manifest.json'));check(reconstruction['candidate_sha256']==H and len(reconstruction['files_sha256'])==161,'Reconstruction manifest source/count differs');expected_reconstruction={'reconstruction/'+n for n in reconstruction['files_sha256']}|{'reconstruction/packet-manifest.json'};check({n for n in names if n.startswith('reconstruction/')}==expected_reconstruction,'Reconstruction packet membership differs')
  for name,h in reconstruction['files_sha256'].items():check(sha(z.read('reconstruction/'+name))==h,'Reconstruction member differs: '+name)
  check(z.read('release/assembly/JLC_CPL.csv')==(P/'inputs/user-corrected-JLC_CPL.csv').read_bytes(),'Supplier CPL is not authoritative user input');check(sha(z.read('release/assembly/JLC_BOM.csv'))==spec['bom_sha256'],'BOM mismatch')
  hold=z.read('history/BASELINE_NOT_FOR_FABRICATION.txt').decode();check('Never fabricate it' in hold and 'P5 contained confirmed narrow copper joints' in hold,'Prior-release hold is missing');check(not final['PCBA_production']['approved'] and len(final['PCBA_production']['required_before_assembly'])==4,'Assembly production boundary changed')
  reportqa=json.loads(z.read('native/review/p6-report-visual-qa.json'));check(reportqa['status'].startswith('PASS') and reportqa['native_sha256']==H and not reportqa['visual_defects_found'],'Routing handoff PDF QA not passed/current');check(z.read('documents/R3-S6-P6-Fabrication-Review.pdf')==(P/'review/R3-S6-P6-Routing-Review.pdf').read_bytes(),'Final report PDF archive differs');check(sha(z.read('documents/R3-S6-P6-Fabrication-Review.pdf'))==reportqa['pdf_sha256'],'Final PDF differs from pixel-reviewed PDF');check(sha(z.read('documents/P6-Fabrication-Review.md'))==reportqa['source_markdown_sha256'],'Report Markdown differs from reviewed source');check(sha(z.read(final_member))==sha((P/'review/p6-final-release-qualification.json').read_bytes()),'Final qualification copy differs')
  for path,h in reportqa['source_evidence_sha256'].items():check(sha(Path(path).read_bytes())==h,'Final PDF evidence changed: '+path)
  facts={'members':len(names),'all_hashed_members':len(manifest),'qualified_source_files_present':source_count,'qualification_evidence_files_present':evidence_count,'original_release_files_exact':len(release_manifest),'reconstruction_members_verified':161,'native_sha256':H,'source_qualification_sha256':sha(z.read(qmember)),'final_release_qualification_sha256':sha(z.read(final_member)),'release_manifest_sha256':sha(z.read('release/SHA256_MANIFEST.json')),'routing_report_PDF_sha256':sha(z.read('documents/R3-S6-P6-Fabrication-Review.pdf')),'routing_report_QA_sha256':sha(z.read('native/review/p6-report-visual-qa.json'))}
 result={'status':'PASS INDEPENDENT FINAL PACKAGE CRC, EVERY MEMBER AND PORTABLE GUARD' if not errors else 'NOT PASSED','errors':errors,'package':str(a.package),'package_sha256':sha(a.package.read_bytes()),'spec_sha256':sha(a.spec.read_bytes()),'audit_script_sha256':sha(Path(__file__).read_bytes()),**facts,'qualification':'Final report PDF and immutable release qualification are jointly bound here without circular hashes; four preassembly production deliverables remain explicit'};a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return bool(errors)
if __name__=='__main__':raise SystemExit(main())
