#!/usr/bin/python3
"""Regenerate all 13 Gerbers from fixed isolated native files and compare exactly."""
import argparse,hashlib,json,pathlib,subprocess
ap=argparse.ArgumentParser();ap.add_argument('--project',type=pathlib.Path,required=True);ap.add_argument('--snapshot',type=pathlib.Path,required=True);ap.add_argument('--baseline',type=pathlib.Path,required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--out',type=pathlib.Path,required=True);a=ap.parse_args();B=a.project.resolve();C=a.snapshot.resolve();A=a.baseline.resolve();O=a.out.resolve();O.mkdir(parents=True,exist_ok=True);sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();assert sha(B/'controller.kicad_pcb')==sha(C/'controller.kicad_pcb')==a.sha256
R=B/'release';releasehashes={str(q.relative_to(R)):sha(q) for q in R.rglob('*') if q.is_file()};fresh=O/'fresh-native-gerbers';assert not fresh.exists();fresh.mkdir();cli=['sh',str(pathlib.Path(__file__).resolve().parents[1]/'frozen-tools/kicad_cli.sh')]
subprocess.run(cli+['pcb','export','gerbers','--layers','F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,F.Paste,B.Paste,Edge.Cuts','--precision','6','--subtract-soldermask','--use-drill-file-origin','--output',str(fresh),str(C/'controller.kicad_pcb')],check=True,stdout=subprocess.DEVNULL)
def normalized(path,prior=False):
 lines=path.read_text().splitlines(keepends=True);date=[s for s in lines if s.startswith(('%TF.CreationDate,','G04 Created by KiCad (PCBNEW '))];assert len(date)==2
 text=''.join(s for s in lines if s not in date)
 if prior:text=text.replace(',R3-S6-P5*%',',R3-S6-P6*%')
 return text.encode()
expected={'controller-F_Cu.gtl','controller-In1_Cu.g1','controller-In2_Cu.g2','controller-In3_Cu.g3','controller-In4_Cu.g4','controller-B_Cu.gbl','controller-F_Mask.gts','controller-B_Mask.gbs','controller-F_Paste.gtp','controller-B_Paste.gbp','controller-F_Silkscreen.gto','controller-B_Silkscreen.gbo','controller-Edge_Cuts.gm1'};errors=[];rows=[]
if {q.name for q in fresh.iterdir() if q.suffix!='.gbrjob'}!=expected:errors.append('Fresh native Gerber set differs')
for name in sorted(expected):
 f=fresh/name;r=R/'single-board-gerbers'/name;ok=normalized(f)==normalized(r)
 if not ok:errors.append('Fresh exact Gerber mismatch: '+name)
 rows.append({'file':name,'exact_except_two_creation_date_lines':ok,'normalized_sha256':hashlib.sha256(normalized(f)).hexdigest(),'release_sha256':sha(r)})
conserved=[]
for name in ['controller-F_Paste.gtp','controller-B_Paste.gbp','controller-F_Mask.gts','controller-B_Mask.gbs','controller-F_Silkscreen.gto','controller-B_Silkscreen.gbo','controller-Edge_Cuts.gm1']:
 old=A/'release/single-board-gerbers'/name;new=R/'single-board-gerbers'/name;ok=normalized(old,True)==normalized(new)
 if not ok:errors.append('Conserved non-routing layer changed from P5: '+name)
 conserved.append({'file':name,'invariant_after_exact_title_revision_and_two_date_lines':ok,'normalized_sha256':hashlib.sha256(normalized(new)).hexdigest()})
for name in ['JLC_CPL.csv','JLC_BOM.csv','JLC_CPL_NATIVE_AUDIT.csv']:
 old=A/'release/assembly'/name;new=R/'assembly'/name;ok=old.read_bytes()==new.read_bytes()
 if not ok:errors.append('Assembly file differs from fixed P5 poses/BOM: '+name)
 conserved.append({'file':'assembly/'+name,'byte_identical_P5_to_P6':ok,'sha256':sha(new)})
if releasehashes!={str(q.relative_to(R)):sha(q) for q in R.rglob('*') if q.is_file()}:errors.append('Release artifacts changed during check')
assert sha(B/'controller.kicad_pcb')==sha(C/'controller.kicad_pcb')==a.sha256
report={'status':'PASS EXACT 13-GERBER REGENERATION AND CONSERVED ASSEMBLY/MASK/PASTE/OUTLINE' if not errors else 'NOT PASSED','native_sha256':a.sha256,'errors':errors,'files':rows,'conserved_exports':conserved,'release_manifest_sha256':sha(R/'SHA256_MANIFEST.json'),'method':__doc__,'normalization':'Exactly two creation-date header lines only for fresh comparisons; P5 invariance additionally normalizes only the exact revision field R3-S6-P5 to R3-S6-P6. No coordinates, aperture shapes, copper, plating, dimensions or metadata other than those explicit fields are removed.'}
(O/'exact-gerber-regeneration.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'errors':errors,'Gerbers_checked':len(rows),'conserved_files_checked':len(conserved),'report':str(O/'exact-gerber-regeneration.json')},indent=2));raise SystemExit(bool(errors))
