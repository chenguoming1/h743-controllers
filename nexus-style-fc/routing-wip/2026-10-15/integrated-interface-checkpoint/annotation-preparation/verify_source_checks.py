#!/usr/bin/env python3
"""Read-only source/geometry checks. Does not execute native KiCad or export CAM."""
import ast, collections, importlib.util, json, math, pathlib, re, sys
from guarded_cleanup import parse, footprint_map, index, sha, write_json, BOARD, TARGET_UIDS, NEW_UIDS
O=pathlib.Path(__file__).resolve().parent
C=pathlib.Path(sys.argv[1]).resolve() if len(sys.argv)>1 else O/'isolated-candidate'
tr=json.loads((C/'annotation-transaction.json').read_text());S=pathlib.Path(tr['source_project'])
B=parse((C/BOARD).read_text());F=footprint_map(B);BI=index(B)

def val(n,k,default=None):
 rows=n.children(k);return rows[0].items[1] if rows else default

def xy(n,k):return tuple(map(float,n.one(k).items[1:3]))
def trxy(p,f):
 if f is None:return p
 at=f.one('at').items;a=-math.radians(float(at[3]) if len(at)>3 else 0);x,y=p
 return (float(at[1])+x*math.cos(a)-y*math.sin(a),float(at[2])+x*math.sin(a)+y*math.cos(a))
def rect_gap(a,b):return math.hypot(max(a[0]-b[2],b[0]-a[2],0),max(a[1]-b[3],b[1]-a[3],0))
def silkbox(n,f):
 typ=n.tag;ss=n.children('stroke');stroke=float(val(ss[0],'width',0))/2 if ss else 0;pts=[]
 if typ in ['fp_line','gr_line']:pts=[trxy(xy(n,k),f) for k in ['start','end']]
 elif typ in ['fp_circle','gr_circle']:
  c=trxy(xy(n,'center'),f);rr=math.dist(xy(n,'center'),xy(n,'end'))+stroke;return [c[0]-rr,c[1]-rr,c[0]+rr,c[1]+rr]
 elif typ in ['fp_poly','gr_poly']:pts=[trxy(tuple(map(float,p.items[1:3])),f) for p in n.one('pts').children('xy')]
 elif typ in ['fp_arc','gr_arc']:
  a,c,z=[trxy(xy(n,k),f) for k in ['start','mid','end']];ax,ay=a;bx,by=c;cx,cy=z;dd=2*(ax*(by-cy)+bx*(cy-ay)+cx*(ay-by));ux=((ax*ax+ay*ay)*(by-cy)+(bx*bx+by*by)*(cy-ay)+(cx*cx+cy*cy)*(ay-by))/dd;uy=((ax*ax+ay*ay)*(cx-bx)+(bx*bx+by*by)*(ax-cx)+(cx*cx+cy*cy)*(bx-ax))/dd;rr=math.dist((ux,uy),a)+stroke;return [ux-rr,uy-rr,ux+rr,uy+rr]
 elif typ in ['gr_text','fp_text','property']:
  if 'hide' in n.items or val(n,'hide')=='yes':return None
  txt=n.items[1] if typ=='gr_text' else n.items[2];font=n.one('effects').one('font');size=xy(font,'size');stroke=float(val(font,'thickness',0))/2;at=trxy(xy(n,'at'),f);w=size[0]*max(1,len(txt))*1.15/2+stroke;h=size[1]*1.15/2+stroke;return [at[0]-w,at[1]-h,at[0]+w,at[1]+h]
 if not pts:return None
 return [min(x for x,y in pts)-stroke,min(y for x,y in pts)-stroke,max(x for x,y in pts)+stroke,max(y for x,y in pts)+stroke]
# Reuse only the previously read pure parser function, never its native-lane entrypoint.
parser_source=S.parent.parent/'routing-continuation/r62-input-cap-star/audit-scripts/check_offpad_mask_paste.py'
tree=ast.parse(parser_source.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='parse');env={'re':re,'math':math};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(parser_source),'exec'),env)
maskfile=S/'mask-paste/after/nexus-style-fc-F_Mask.gts'
mask=env['parse'](maskfile.read_text())
silk=[]
for f in [None]+list(F.values()):
 for n in B.items if f is None else f.items:
  if not hasattr(n,'tag') or val(n,'layer')!='F.SilkS':continue
  box=silkbox(n,f)
  if box:silk.append({'uuid':val(n,'uuid'),'ref':f.prop('Reference') if f else None,'kind':n.tag,'bounds':box})
def gaps(box,exclude):
 ma=min(((rect_gap(box,m['bounds_board_mm']),m) for m in mask),key=lambda z:z[0]);si=min(((rect_gap(box,s['bounds']),s) for s in silk if s['uuid'] not in exclude),key=lambda z:z[0]);return {'mask_gap_lower_bound_mm':ma[0],'nearest_mask':ma[1],'silk_gap_lower_bound_mm':si[0],'nearest_silk':si[1]}
syms=parse((C/'hardware/library/NexusFC.kicad_sym').read_text())
def allnodes(n,kind):
 out=[n] if n.tag==kind else []
 for c in n.items:
  if hasattr(c,'tag'):out+=allnodes(c,kind)
 return out
spec=importlib.util.spec_from_file_location('annotation_checked_design',C/'tools/design.py');design=importlib.util.module_from_spec(spec);spec.loader.exec_module(design);parts={p['ref']:p for p in design.get_main_parts()}
led=[]
for ref in ['D1','D2','D3']:
 f=F[ref];dot=BI[TARGET_UIDS[ref]];center=trxy(xy(dot,'center'),f);end=trxy(xy(dot,'end'),f);pads={p.items[1]:p for p in f.children('pad')};p1=trxy(xy(pads['1'],'at'),f);p2=trxy(xy(pads['2'],'at'),f)
 sym=next(s for s in syms.children('symbol') if s.items[1]==parts[ref]['sym'].split(':')[1]);pin1=next(p for p in allnodes(sym,'pin') if val(p,'number')=='1');assert val(pin1,'name') in ('K','C')
 assert center[0]<float(f.one('at').items[1]) and math.dist(center,p1)<math.dist(center,p2)
 assert center[0]==(107.2 if ref=='D1' else 113.6 if ref=='D2' else 110.4) or abs(center[0]-(107.2 if ref=='D1' else 113.6 if ref=='D2' else 110.4))<1e-10
 assert abs(center[1]-(126.25 if tr.get('marker_style')=='filled-0.30' else 126.15))<1e-10 and abs(math.dist(center,end)-(.075 if tr.get('marker_style')=='filled-0.30' else .03))<1e-10
 g=gaps(silkbox(dot,f),{TARGET_UIDS[ref]});assert g['mask_gap_lower_bound_mm']>=.15-1e-9 and g['silk_gap_lower_bound_mm']>=.15-1e-9
 led.append({'ref':ref,'dot_uuid':TARGET_UIDS[ref],'center_mm':center,'radius_mm':math.dist(center,end),'stroke_mm':val(dot.one('stroke'),'width'),'fill':val(dot,'fill'),'outer_ink_diameter_mm':2*math.dist(center,end)+float(val(dot.one('stroke'),'width')),'cathode_pin':'1','schematic_pin_name':val(pin1,'name'),'cathode_pin_net':pads['1'].one('net').items[-1],'cathode_center_mm':p1,'anode_center_mm':p2,'dot_distance_to_cathode_mm':math.dist(center,p1),'dot_distance_to_anode_mm':math.dist(center,p2),'gap_checks':g,'visual_native_review':'pending sole native lane'})
glyphs=[]
for ref,label in [('J4','C'),('J6','>')]:
 t=next(n for n in B.children('gr_text') if n.items[1]==label);box=silkbox(t,None);ends=[]
 for u in [TARGET_UIDS[ref],NEW_UIDS[ref]]:ends.append({'uuid':u,'start_mm':trxy(xy(BI[u],'start'),F[ref]),'end_mm':trxy(xy(BI[u],'end'),F[ref]),'stroke_mm':val(BI[u].one('stroke'),'width'),'text_box_gap_lower_bound_mm':rect_gap(box,silkbox(BI[u],F[ref]))})
 assert all(x['text_box_gap_lower_bound_mm']>=.15-1e-9 for x in ends)
 g=gaps(box,{val(t,'uuid')});glyphs.append({'ref':ref,'text':label,'text_uuid':val(t,'uuid'),'unchanged_text_node':t.value(),'text_conservative_box':box,'retained_outline_pieces':ends,'actual_mask_and_all_silk':g})
# Project-local package consumers: enumerate actual main and child source boards.
usage=collections.defaultdict(list)
for p in (C/'hardware').rglob('*.kicad_pcb'):
 for f in parse(p.read_text()).children('footprint'):usage[f.items[1]].append(str(p.relative_to(C))+':'+f.prop('Reference'))
attrs=[]
for ref in ['U3','L2','U14']:
 f=F[ref];lib=C/'hardware/library/NexusFC.pretty'/(f.items[1].split(':')[1]+'.kicad_mod');n=parse(lib.read_text());assert val(f,'attr')==val(n,'attr')=='smd'
 attrs.append({'ref':ref,'footprint':f.items[1],'board_attr':f.one('attr').value(),'library_attr':n.one('attr').value(),'smd_pad_count':len(f.children('pad')),'actual_project_consumers':usage[f.items[1]],'scope_justification':'Imported package contains only SMD pads and no holes; correcting package metadata is appropriate for any consumer, without changing its geometry.'})
selected={r for r,p in parts.items() if p.get('lcsc','').startswith('C')};boardrefs=set(F);assert set(parts)==boardrefs
assert all(r in selected for r in ['U3','L2','U14','J6']);assert 'J1' not in selected
# Existing real-native r62 WIP evidence, never substituted for the later native export.
import csv
prior=S.parent.parent/'routing-continuation/r62-input-cap-star/wip-bom-cpl/candidate'
oldcpl=list(csv.DictReader((prior/'nexus-style-fc-cpl-jlc.csv').open()));oldbom=list(csv.DictReader((prior/'nexus-style-fc-bom-jlc.csv').open()));oldcrefs={x['Designator'] for x in oldcpl};oldbrefs={r for x in oldbom for r in x['Designator'].split(',')};assert selected==oldcrefs==oldbrefs
result={'status':'PASS source-only guards and conservative geometry; native/visual/export pending','source_board_sha256':sha(S/BOARD),'candidate_board_sha256':sha(C/BOARD),'mask_export_source_sha256':sha(maskfile),'assembly_attributes':attrs,'LED_cathode_association':led,'meaningful_identifiers':glyphs,'assembly_selection':{'source_design_sha256':sha(S/'tools/design.py'),'candidate_design_sha256':sha(C/'tools/design.py'),'component_count':len(F),'selected_machine_part_count':len(selected),'selected_refs':sorted(selected),'omitted_refs':sorted(boardrefs-selected),'J1':{'attribute_preserved':F['J1'].one('attr').value(),'lcsc':F['J1'].prop('LCSC'),'role':'Manual child-board slot/fillet joint. No LCSC placement item. Not a normal machine-placed SMD component.','excluded_by_actual_exporter_selection':True,'new_actual_native_export':'PENDING sole native lane'},'J6':{'process':'Mixed SMT signal contacts plus PTH ground shell lugs and NPTH locators; shell soldering process remains explicit/unqualified.','included_by_exporter_selection':True},'historical_real_native_r62_CPL_sha256':sha(prior/'nexus-style-fc-cpl-jlc.csv'),'historical_real_native_r62_BOM_sha256':sha(prior/'nexus-style-fc-bom-jlc.csv'),'historical_real_native_refs_match_current_selection':True,'new_actual_native_comparison':'PENDING; run native_verify_assembly.py in the sole native lane'},'library_reuse':dict(usage),'qualification':'Conservative source geometry only, not native KiCad glyph rendering, body-fit, printable-feature, assembly-process or release qualification.'}
write_json(C/'annotation-source-checks.json',result);print(json.dumps({'status':result['status'],'selected_machine_parts':len(selected),'omitted_refs':sorted(boardrefs-selected),'led_mask_silk_gaps':{r['ref']:[r['gap_checks']['mask_gap_lower_bound_mm'],r['gap_checks']['silk_gap_lower_bound_mm']] for r in led},'glyph_outline_gap':{r['ref']:[p['text_box_gap_lower_bound_mm'] for p in r['retained_outline_pieces']] for r in glyphs}},indent=2))
