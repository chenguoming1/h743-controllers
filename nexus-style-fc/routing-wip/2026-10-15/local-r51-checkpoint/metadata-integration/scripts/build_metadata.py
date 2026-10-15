from pathlib import Path
import json,hashlib,shutil,sys,difflib,importlib.util,copy,subprocess
import pcbnew as k
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');O=R/'u10-metadata-integration';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sys.path.insert(0,'/workspace/shared/nexus-recovery-evidence');from apply_en_cut import children,field
spec=importlib.util.spec_from_file_location('validator',R/'latest-main/nexus-style-fc/tools/validate_nexus_reroute.py');V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)
if len(sys.argv)==1:
 for role in ['canonical','experimental-r51']:subprocess.run([sys.executable,__file__,role],check=True)
 raise SystemExit(0)
H=R/'u10-metadata-cleanup/generator-handoff.json';h=json.loads(H.read_text());ops=h['instance_operations'];assert sha(Path(h['candidate']))==h['candidate_sha256'];spec=importlib.util.spec_from_file_location('pcbutil_cleanup',h['candidate']);M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
for role,S,expected in [('canonical',R/'c19-integration/canonical','afd0f3225b8d9eca28487b62dfe92ed8feba742e9577b70fb08b03ff8411859f'),('experimental-r51',R/'routing-continuation/r51-ldo-output','4e3b32282d184faef88e86e1d8f269065cfbf2acc79457953ee75bc610405d66')]:
 if len(sys.argv)>1 and role!=sys.argv[1]:continue
 D=O/role;assert not D.exists();SP=S/'hardware/nexus-style-fc.kicad_pcb';assert sha(SP)==expected;assert sha(S/'hardware/nexus-style-fc.kicad_sch')=='49f9e0571424d0610e294bdcd6b120a42d04db284ecda9e660428fc587e62699'
 text=SP.read_text();fps=[(i,z,text[i:z]) for i,z in children(text) if text[i:z].startswith('(footprint ')];i,z,fp=next((i,z,f) for i,z,f in fps if '(property "Reference" "U10"' in f);fu=json.loads(next(fp[a:b][6:-1].strip() for a,b in children(fp) if fp[a:b].startswith('(uuid ')));patches=[]
 pi,pz,prop=next((a,b,fp[a:b]) for a,b in children(fp) if fp[a:b].startswith('(property "LCSC Part" '));assert prop.startswith('(property "LCSC Part" "C82942"');pu=field(prop,'uuid').strip('"');patches.append((pi,pz,''));di,dz,descr=next((a,b,fp[a:b]) for a,b in children(fp) if fp[a:b].startswith('(descr '));assert descr=='(descr "ME6211C33M5G-N")';patches.append((di,dz,'(descr '+json.dumps(ops['new_library_description'])+')'))
 newfp=fp
 for a,b,v in sorted(patches,reverse=True):newfp=newfp[:a]+v+newfp[b:]
 outtext=text[:i]+newfp+text[z:];shutil.copytree(S/'hardware',D/'hardware');P=D/'hardware/nexus-style-fc.kicad_pcb';P.write_text(outtext);shutil.copy2(P,D/'minimal-pre-refill.kicad_pcb');(D/'metadata-only.patch').write_text(''.join(difflib.unified_diff(text.splitlines(True),outtext.splitlines(True),fromfile='source',tofile='candidate')))
 # Verify the exact generator helper using the actual selected U10 instance and native KiCad API.
 b=k.LoadBoard(str(SP));f=next(f for f in b.GetFootprints() if f.GetReference()=='U10');assert f.GetValue()=='TPS70933DBVR' and f.GetField('LCSC').GetText()=='C89347';M.clear_main_u10_donor_metadata(f,{'ref':'U10','value':'TPS70933DBVR','lcsc':'C89347'},'nexus-style-fc');helperfile=D/'helper-smoke-native.kicad_pcb';k.SaveBoard(str(helperfile),b)
 ht,ct=[V.parse_sexpr(p.read_text()) for p in [helperfile,P]];assert V.keyed_nodes(V.children(ht,'footprint'))==V.keyed_nodes(V.children(ct,'footprint')),'Generator helper footprint output differs from exact instance patch'
 for name in ['native-erc.json','final-netlist.xml']:shutil.copy2(S/name,D/name)
 shutil.copy2(H,D/'generator-handoff.json');shutil.copy2(R/'current-main-binding-09.json',D/'current-main-binding.json');shutil.copy2(S/'evidence-manifest.json',D/'source-evidence-manifest.json')
 tr={'role':role,'source_directory':str(S),'source_board_sha256':expected,'source_schematic_sha256':sha(S/'hardware/nexus-style-fc.kicad_sch'),'candidate_schema_sha256':sha(D/'hardware/nexus-style-fc.kicad_sch'),'candidate_pre_refill_sha256':sha(P),'source_main_commit_reported_by_owner':'80a3f763d5031198b4622402bb73a532676b9be9','approved_footprint_uuid':fu,'approved_metadata_delta':{'removed_property_name':'LCSC Part','removed_property_value':'C82942','removed_property_uuid':pu,'old_lib_description':'ME6211C33M5G-N','new_lib_description':ops['new_library_description']},'generator_helper_smoke':{'generator_sha256':h['candidate_sha256'],'native_saved_sha256':sha(helperfile),'all_footprint_definitions_equal_to_exact_text_patch':True},'scope':'Only U10 stale donor property removal and exact library-description replacement. All selected part fields, library ID, geometry, pads, nets, tracks, vias and other metadata must remain exact.'};(D/'transaction.json').write_text(json.dumps(tr,indent=2)+'\n');assert sha(SP)==expected;print(role,sha(P))
