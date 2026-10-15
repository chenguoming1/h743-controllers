#!/usr/bin/env python3
"""Pure-source stage08 overlay. Never edits a routed PCB or invokes KiCad."""
import argparse, copy, importlib.util, json, os, pathlib, re, shutil, subprocess, sys
if not __debug__: raise SystemExit('Refusing optimized Python: active guards are required')
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from guarded_cleanup import parse,raw,sha,csha,footprint_map,index,apply_replacements,replace_once,Node,write_json,TARGET_UIDS,NEW_UIDS,ATTR_REFS
BOARD=pathlib.Path('hardware/nexus-style-fc.kicad_pcb');SCH=pathlib.Path('hardware/nexus-style-fc.kicad_sch');LIB=pathlib.Path('hardware/library/NexusFC.pretty')
SOURCE_SHA='ccd8865f6785fd1cdec0214a08fe409faed4d47bb01e8474f09264ee36acab99'
ART_SHA='282e48d05d5adb1a6933b5f29ea851c7452183f508bc3fae8264982b5e1121aa'
REFS=['J4','J6','D1','D2','D3']
def load_design(project,name):
 spec=importlib.util.spec_from_file_location(name,project/'tools/design.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def graphic(n):
 key='start' if n.tag=='fp_line' else 'center';width=n.one('stroke').val('width') if n.children('stroke') else n.val('width');fill=n.val('fill') if n.children('fill') else 'no'
 return [n.tag,n.val('layer'),list(map(float,n.one(key).items[1:3])),list(map(float,n.one('end').items[1:3])),float(width),fill not in ['none','no']]
def graphics(n):return sorted([graphic(x) for x in n.children('fp_line')+n.children('fp_circle')],key=lambda x:json.dumps(x))
def quoted(s):return json.dumps(s)
def protected_sch(n):
 v=copy.deepcopy(n.value())
 for sym in v:
  if not isinstance(sym,list) or sym[0]!='symbol':continue
  ref=next(x[2] for x in sym if isinstance(x,list) and x[:2]==['property','Reference'])
  if ref in REFS:
   for x in sym:
    if isinstance(x,list) and x[:2]==['property','Footprint']:x[2]='<ALLOWLISTED-FPID>'
 return v

def prepare(source,art,out):
 source=source.resolve();art=art.resolve();out=out.resolve()
 assert not out.exists() and source not in out.parents and art not in out.parents
 assert sha(source/BOARD)==SOURCE_SHA and sha(art/BOARD)==ART_SHA
 # Seal every source input before execution or copying; no trust in later mutable inputs.
 inputs={str(p.relative_to(source)):sha(p) for folder in ['tools','hardware'] for p in (source/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
 assert inputs==json.loads((HERE/'stage08-input-bindings.json').read_text()),'stage08 authoritative source binding changed'
 st=(source/BOARD).read_text();at=(art/BOARD).read_text();sb=parse(st);ab=parse(at);sf=footprint_map(sb);af=footprint_map(ab);si=index(sb);ai=index(ab)
 out.mkdir(parents=True)
 for d in ['hardware','tools']:shutil.copytree(source/d,out/d,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 before=load_design(source,'source_design');parts0=before.get_main_parts();by0={p['ref']:p for p in parts0};mapping={};changes=[];nodes=[]
 for ref in REFS:
  oldfp=sf[ref].items[1];assert af[ref].items[1]==oldfp and by0[ref]['fp']==oldfp
  assert af[ref].prop('LCSC')==by0[ref]['lcsc'];name=oldfp.split(':')[1];newname=name+'__NexusMain_'+ref;newfp='NexusFC:'+newname
  rel=LIB/(name+'.kicad_mod');target=LIB/(newname+'.kicad_mod');text=(source/rel).read_text();root=parse(text)
  assert root.tag=='module' and root.items[1]==name
  oldgraphic=[g for g in root.children('fp_line')+root.children('fp_circle') if graphic(g)==graphic(si[TARGET_UIDS[ref]])];assert len(oldgraphic)==1
  old=oldgraphic[0];approved=[ai[TARGET_UIDS[ref]]]+([ai[NEW_UIDS[ref]]] if ref in NEW_UIDS else [])
  chunks=[]
  for node in approved:
   s=raw(at,node)
   if node.children('uuid'):s=replace_once(s,raw(at,node.one('uuid')),'')
   chunks.append(s)
  new=apply_replacements(text,[(old.start,old.end,'\n\t'.join(chunks))])
  # Project-owned footprint header prevents the generic courtyard rebuilder from
  # redrawing this exact bounded variant; every other generic source node stays exact.
  new=replace_once(new,'(module '+name+' ','(footprint '+quoted(newname)+' ')
  (out/target).write_text(new);nr=parse(new)
  oldrest=[x.value() if isinstance(x,Node) else x for x in root.items[2:] if x is not old]
  newgraphics=[g for g in nr.children('fp_line')+nr.children('fp_circle') if graphic(g) in [graphic(g) for g in approved]]
  assert len(newgraphics)==len(approved)
  newrest=[x.value() if isinstance(x,Node) else x for x in nr.items[2:] if x not in newgraphics]
  assert oldrest==newrest,(ref,'non-target library source node changed')
  assert graphics(nr)==graphics(af[ref]),(ref,'library/approved board geometry mismatch')
  assert [raw(text,p) for p in root.children('pad')]==[raw(new,p) for p in nr.children('pad')],ref
  mapping[ref]={'old_fpid':oldfp,'new_fpid':newfp,'lcsc':by0[ref]['lcsc'],'value':by0[ref]['value'],'symbol':by0[ref]['sym'],'source_library':str(rel),'variant_library':str(target),'source_library_sha256':sha(source/rel),'variant_library_sha256':sha(out/target),'stage08_footprint_canonical_sha256':csha(sf[ref].value()),'stage09_footprint_canonical_sha256':csha(af[ref].value()),'pad_nodes_canonical_sha256':csha([p.value() for p in sf[ref].children('pad')]),'graphic_geometry_sha256':csha(graphics(nr))}
  changes.append(str(target));nodes.append({'ref':ref,'before_node':old.value(),'after_nodes':[g.value() for g in newgraphics],'all_non_target_library_nodes_exact':True,'library_pad_raw_nodes_exact':True})
 for ref in ATTR_REFS:
  rel=LIB/(sf[ref].items[1].split(':')[1]+'.kicad_mod');t=(source/rel).read_text();r=parse(t);assert r.one('attr').value()==['attr','through_hole']
  assert all(p.items[2]=='smd' and not p.children('drill') for p in r.children('pad'))
  n=replace_once(t,raw(t,r.one('attr')),'(attr smd)');(out/rel).write_text(n);assert sha(out/rel)==sha(art/rel)
  changes.append(str(rel));nodes.append({'ref':ref,'before_node':['attr','through_hole'],'after_nodes':[['attr','smd']],'all_other_library_bytes_exact':True})
 # Single selector used only by main PCB, main schematic, and main BOM generation.
 d=(source/'tools/design.py').read_text();lines=['# Main-board-only library variants for the approved annotation artwork.', '# Legacy PARTS and sibling projects retain their original generic footprints.', 'MAIN_ANNOTATION_FOOTPRINTS = {']
 for ref,row in mapping.items():lines.append('    '+repr(ref)+': ('+repr(row['old_fpid'])+', '+repr(row['lcsc'])+', '+repr(row['new_fpid'])+'),')
 lines+=['}', '']
 d=replace_once(d,'def get_main_parts():','\n'.join(lines)+'\ndef get_main_parts():')
 d=replace_once(d,'    return selected\n','    for ref, (original_fp, lcsc, variant_fp) in MAIN_ANNOTATION_FOOTPRINTS.items():\n        p = by_ref[ref]\n        assert (p["fp"], p["lcsc"]) == (original_fp, lcsc), (ref, "annotation variant identity changed")\n        p["fp"] = variant_fp\n    return selected\n')
 (out/'tools/design.py').write_text(d);changes.append('tools/design.py');after=load_design(out,'new_design');parts1=after.get_main_parts()
 assert before.PARTS==after.PARTS and before.LAYOUT==after.LAYOUT
 assert len(parts0)==len(parts1)==89 and sum(len(p['pins']) for p in parts0)==349
 norm=copy.deepcopy(parts1)
 for p in norm:
  if p['ref'] in mapping:p['fp']=mapping[p['ref']]['old_fpid']
 assert norm==parts0,'part selection changed beyond five FPIDs'
 assert before.get_main_nets()==after.get_main_nets()
 # Reviewed pure text generator, with pinned symbol definitions; no native modules.
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
 baseline=out/'baseline-regenerated.kicad_sch'
 r0=subprocess.run([sys.executable,'-B',str(source/'tools/gen_schematic.py'),'design',str(baseline),'nexus-style-fc'],env=env,capture_output=True,text=True,check=True)
 assert baseline.read_bytes()==(source/SCH).read_bytes(),'baseline schematic generator is not byte-exact; stop before adoption'
 r1=subprocess.run([sys.executable,'-B',str(out/'tools/gen_schematic.py'),'design',str(out/SCH),'nexus-style-fc'],env=env,capture_output=True,text=True,check=True)
 oldsch=parse((source/SCH).read_text());newsch=parse((out/SCH).read_text());assert protected_sch(oldsch)==protected_sch(newsch),'schematic changed beyond allowed Footprint properties'
 assert set(index(oldsch))==set(index(newsch)),'schematic UUID identity changed'
 changedprops=[]
 for s in newsch.children('symbol'):
  ref=s.prop('Reference')
  if ref in mapping:assert s.prop('Footprint')==mapping[ref]['new_fpid'];changedprops.append(ref)
 assert set(changedprops)==set(REFS);changes.append(str(SCH))
 # Rebind only the exact schematic digest used by the existing mechanical checker.
 checkrel='tools/check_header_interface_static.py';check=(source/checkrel).read_text()
 assert check.count(sha(source/SCH))==1,'mechanical schematic guard shape changed'
 rebound=replace_once(check,sha(source/SCH),sha(out/SCH));(out/checkrel).write_text(rebound);changes.append(checkrel)
 guard_rebinding={'path':checkrel,'before_schematic_sha256':sha(source/SCH),'after_schematic_sha256':sha(out/SCH),'all_other_checker_bytes_exact':True}
 assert rebound.replace(sha(out/SCH),sha(source/SCH))==check
 # All target symbols have no footprint-filter restriction, generic symbol sources stay untouched.
 symbols=parse((source/'hardware/library/NexusFC.kicad_sym').read_text())
 for ref,row in mapping.items():
  sym=next(s for s in symbols.children('symbol') if s.items[1]==row['symbol'].split(':')[1]);assert not [p for p in sym.children('property') if p.items[1]=='ki_fp_filters']
 # Generic courtyard rebuilder must deliberately skip the project-owned variants.
 spec=importlib.util.spec_from_file_location('source_fix_courtyards',out/'tools/fix_courtyards.py');fc=importlib.util.module_from_spec(spec);spec.loader.exec_module(fc)
 for ref,row in mapping.items():assert fc.fix(str(out/row['variant_library'])) is False and sha(out/row['variant_library'])==row['variant_library_sha256']
 assert sha(out/BOARD)==SOURCE_SHA and sha(out/'tools/pcbutil.py')==sha(source/'tools/pcbutil.py') and not (out/'tools/assembly_annotations.py').exists()
 changedset=set(changes);overlay=[]
 for rel,h in inputs.items():
  assert sha(source/rel)==h,('concurrent source modification',rel)
  if rel not in changedset:assert sha(out/rel)==h,('unexpected source overlay change',rel)
 for rel in changes:overlay.append({'path':rel,'source_sha256':inputs.get(rel),'stage09_sha256':sha(art/rel) if (art/rel).exists() else None,'new_sha256':sha(out/rel),'size':(out/rel).stat().st_size})
 assert sha(art/BOARD)==ART_SHA
 data={'status':'SOURCE-ONLY PREPARED; no native validation performed','stage08_source':str(source),'stage09_artwork_source':str(art),'source_pcb_sha256':SOURCE_SHA,'artwork_pcb_sha256':ART_SHA,'output_pcb_sha256':sha(out/BOARD),'routed_pcb_edited':False,'source_input_sha256':inputs,'overlay_files':overlay,'fpid_mapping':mapping,'library_node_changes':nodes,'guard_rebinding':guard_rebinding,'checks':{'89_main_parts_preserved':True,'349_pin_assignments_preserved_including_26_no_connects':True,'323_connected_assignments_preserved':True,'legacy_PARTS_exact':True,'all_main_part_fields_except_five_FPID_exact':True,'all_schematic_nodes_except_five_Footprint_properties_exact':True,'schematic_UUID_set_exact':True,'baseline_schematic_regeneration_byte_exact':True,'mechanical_checker_rebound_only_exact_schematic_SHA':True,'generic_graphic_libraries_byte_exact':True,'shared_symbol_libraries_byte_exact':True,'pcbutil_byte_exact_without_instance_mutations':True,'new_variant_graphics_match_stage09':True,'new_variant_pad_raw_nodes_match_generic':True,'fix_courtyards_skips_owned_variants':True,'no_restrictive_target_footprint_filters':True,'all_unlisted_source_files_byte_exact':True},'generator_stdout':[r0.stdout,r1.stdout]}
 write_json(out/'source-variant-transaction.json',data);write_json(out/'fpid-mapping.json',mapping);return data
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage08',type=pathlib.Path,required=True);p.add_argument('--stage09',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();r=prepare(a.stage08,a.stage09,a.output);print(json.dumps({'status':r['status'],'files':len(r['overlay_files']),'checks':r['checks']},indent=2))
