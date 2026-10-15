from pathlib import Path
import pcbnew as k,json,hashlib,shutil,sys,uuid,math,importlib.util
sys.path.insert(0,'/workspace/shared/nexus-recovery-evidence');from apply_en_cut import children,field
R=Path('/workspace/scratch/8a35c1f26232/nexus-recovery-20261015');S=R/'routing-continuation/r58-buck-center';O=R/'routing-continuation/r59-usb170-trial';D=Path('/workspace/shared/nexus-usb-stack-review/r57-inner-pair');assert not O.exists();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();P=S/'hardware/nexus-style-fc.kicad_pcb';assert sha(P)=='85c5cede5407d2022df36e0323527704a84c55687fc9dcc426565073aa9c4f8e';m=json.loads((D/'FINAL-HANDOFF-MANIFEST.json').read_text());print(type(m['files']),flush=True)
for rec in m['files']:assert sha(D/rec['path'])==rec['sha256'],(rec['path'],'review artifact changed')
j=json.loads((D/'complete-transaction.json').read_text());ov=json.loads((D/'NATIVE-170-OVERLAY.json').read_text());assert sha(D/'complete-transaction.json')==ov['baseline_sha256']=='04c1aa1a78049f912f1cd6a0a04d9f3531a32c442bf6d04306fa13ad7115e209';assert sha(D/'NATIVE-170-OVERLAY.json')=='ab3580557d9c40a55205226dc6f229cb67aea997ac699bad312768d48df62311';assert sha(D/'width-170-variant.json')==ov['width_variant_sha256'];Q=Path(j['source_path']);assert sha(Q)==j['source_sha256'];text=P.read_text();nodes={field(text[i:z],'uuid').strip('"'):(i,z,text[i:z]) for i,z in children(text) if text[i:z].startswith(('(segment','(arc','(via'))};oldtext=Q.read_text();oldnodes={field(oldtext[i:z],'uuid').strip('"'):oldtext[i:z] for i,z in children(oldtext) if oldtext[i:z].startswith(('(segment','(arc','(via'))}
changes=json.loads((S/'transaction.json').read_text())['replacements'];gone={r['source_uuid'] for r in changes};newbuck={r['replacement']['uuid'] for r in changes};assert set(oldnodes)-set(nodes)==gone and set(nodes)-set(oldnodes)==newbuck
for u in set(nodes)&set(oldnodes):assert nodes[u][2]==oldnodes[u],('Unexpected source rebase change',u)
assert set(j['delete_uuids']).isdisjoint(gone|newbuck);assert set(j['delete_uuids'])=={r['uuid'] for r in j['delete_expected_records']}
b=k.LoadBoard(str(P));uid=lambda o:o.m_Uuid.AsString();xy=lambda p:[p.x/1e6,p.y/1e6];ts={uid(t):t for t in b.GetTracks()};ps={uid(p):p for f in b.GetFootprints() for p in f.Pads()};ls=list(b.GetEnabledLayers().CuStack())
for r in j['delete_expected_records']:
 t=ts[r['uuid']];assert t.GetNetname()==r['net']
 if r['kind']=='via':assert isinstance(t,k.PCB_VIA) and xy(t.GetPosition())==r['at'] and t.GetWidth(k.F_Cu)/1e6==r['diameter'] and t.GetDrillValue()/1e6==r['drill']
 else:assert xy(t.GetStart())==r['start'] and xy(t.GetEnd())==r['end'] and t.GetWidth()/1e6==r['width'] and b.GetLayerName(t.GetLayer())==r['layer']
assert all(u in ts and u not in j['delete_uuids'] for u in j['preserve_bridge_uuids']+j['reuse_via_uuids'])
# Quantize each native coordinate once to KiCad's one-nanometre integer grid.
f=lambda x:format(round(x,6),'.6f').rstrip('0').rstrip('.') or '0'
pt=lambda p:' '.join(f(x) for x in p)
adds=[dict(x) for x in j['add_primitives'] if x['id'] not in ov['remove_baseline_added_ids']];assert len(j['add_primitives'])-len(adds)==34
ns=uuid.UUID('ba4a263b-23e8-4457-9898-7959bf6932b2')
for x in ov['add_inner_primitives']+ov['add_explicit_taper_shapes']:adds.append(dict(x,uuid=str(uuid.uuid5(ns,x['id'])),group='usb170_overlay'))
assert len({r['uuid'] for r in adds})==len(adds) and set(r['uuid'] for r in adds).isdisjoint(ts)
blocks=[]
for r in adds:
 kind=r['kind'];u=r['uuid'];net=r['net']
 if kind in ['segment','arc']:
  coords=' '.join(f'({key} {pt(r[key])})' for key in (['start','end'] if kind=='segment' else ['start','mid','end']));block=f'({kind} {coords} (width {f(r["width"])}) (layer "{r["layer"]}") (net "{net}") (uuid "{u}"))'
 elif kind=='via':
  assert r['diameter']==.45 and r['drill']==.2 and r['layers']==['F.Cu','B.Cu'];block=f'(via (at {pt(r["at"])}) (size 0.45) (drill 0.2) (layers "F.Cu" "B.Cu") (net "{net}") (uuid "{u}"))'
 elif kind=='taper_copper_polygon':
  block=f'(gr_poly (pts '+ ' '.join('(xy '+pt(v)+')' for v in r['vertices_mm'])+f') (stroke (width 0) (type default)) (fill yes) (layer "{r["layer"]}") (net "{net}") (uuid "{u}"))'
 else:raise ValueError(kind)
 blocks.append(block)
for i,z,t in sorted([nodes[u] for u in j['delete_uuids']],reverse=True):text=text[:i]+text[z:]
end=text.rfind(')');text=text[:end]+'\n\t'+'\n\t'.join(blocks)+'\n'+text[end:]
shutil.copytree(S/'hardware',O/'hardware');(O/'hardware/nexus-style-fc.kicad_pcb').write_text(text);shutil.copytree(D,O/'source-review',ignore=shutil.ignore_patterns('__pycache__'));shutil.copy2(S/'current-main-binding.json',O/'current-main-binding.json')
# Native reload establishes net-assigned filled PCB_SHAPE taper representation, not an unconnected graphic.
c=k.LoadBoard(str(O/'hardware/nexus-style-fc.kicad_pcb'));shapes={uid(s):s for s in c.GetDrawings()};taper=[]
for r in adds:
 if r['kind']!='taper_copper_polygon':continue
 q=shapes[r['uuid']];assert q.GetNetname()==r['net'] and c.GetLayerName(q.GetLayer())=='In3.Cu' and q.GetWidth()==0 and q.IsSolidFill();poly=q.GetPolyShape();assert poly.OutlineCount()==1 and poly.VertexCount()==4
 expected=[tuple(round(v*1e6) for v in p) for p in r['vertices_mm']];actual=[(poly.CVertex(i).x,poly.CVertex(i).y) for i in range(poly.VertexCount())];assert actual==expected;taper.append({'uuid':r['uuid'],'net':q.GetNetname(),'layer':'In3.Cu','native_type':type(q).__name__,'polygon_vertices_nm':actual})
tr={'status':'CONDITIONAL USB170 complete-topology native trial; not accepted routing lineage','source_directory':str(S),'source_board_sha256':sha(P),'source_schematic_sha256':sha(S/'hardware/nexus-style-fc.kicad_sch'),'review_source_board_sha256':sha(Q),'source_rebase':'Only four sealed r58 5V_BUCK centering replacements differ from r57; every other source segment/arc/via matches exact bytes and no donor overlaps them. All new geometry requires fresh native checks against r58.','removed_uuids':j['delete_uuids'],'removed_records':j['delete_expected_records'],'removed_blocks':{u:nodes[u][2] for u in j['delete_uuids']},'added_primitives':adds,'preserve_bridge_uuids':j['preserve_bridge_uuids'],'reuse_via_uuids':j['reuse_via_uuids'],'taper_native_realization':taper,'width_scope':ov['width_scope'],'acceptance_gates':ov['acceptance_gates'],'stopping_bound':'One exact complete USB170 transaction. Stop on new/worsened native errors, opens, parity, incomplete contacts or unproved taper geometry. Any geometry revision requires a distinct bounded source-bound correction and review; no part/net/outline/power narrowing changes.','source_handoff_manifest_sha256':sha(D/'FINAL-HANDOFF-MANIFEST.json'),'candidate_pre_native_sha256':sha(O/'hardware/nexus-style-fc.kicad_pcb')};(O/'transaction.json').write_text(json.dumps(tr,indent=2)+'\n');print(json.dumps({'candidate':tr['candidate_pre_native_sha256'],'removed':len(j['delete_uuids']),'added':len(adds),'tapers':len(taper)}),flush=True)
