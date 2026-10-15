"""Read-only native/VRML analytic review. Writes only this review's JSON output.
No pcbnew imports, native calls, network operations, or source design writes.
"""
from pathlib import Path
import hashlib,json,math,re,sys
ROOT=Path('/workspace/scratch/8a35c1f26232')
P=ROOT/'nexus-recovery-20261015/mechanical-integration/main-dsm-slot-03'
PRIOR=ROOT/'nexus-header-redesign-20261015/candidate-02/nexus-style-fc'
OUT=Path(__file__).parent
sys.path.insert(0,str(P/'tools'))
import sexpr as s
FILES={'main':P/'hardware/nexus-style-fc.kicad_pcb','child':P/'hardware/header-board/nexus-header-board.kicad_pcb','model':P/'hardware/library/NexusFC.3dshapes/nexus-header-board-root-relief-candidate.wrl','connector_model':P/'hardware/library/NexusFC.3dshapes/CONN-TH_HX-PZ2.54-3X7P-ZZ.wrl'}
EXPECTED={'main':'673f4e6fd86e3fb06eadcd1de49e48322a540080544d4bd51f51ec7df5b09782','child':'bfec2a120fbda6c97c1f8a36dfff6a35337e13ab1c3af63abb987f529d761403','model':'e1f0da0372a9d95a13fcff612a7effc7f4033363e482d384f0d170019d3f5dbe','connector_model':'cd25aa172890bc506dc1254577b35eda18c9faff947c4a08dc74b8e0192f8294'}
H={k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in FILES.items()};assert H==EXPECTED
main=s.parse(FILES['main'].read_text()); child=s.parse(FILES['child'].read_text())
pm=s.parse((PRIOR/'hardware/nexus-style-fc.kicad_pcb').read_text());pc=s.parse((PRIOR/'hardware/header-board/nexus-header-board.kicad_pcb').read_text())
def one(n,k):
 v=s.find(n,k);return v[0][1:] if v else []
def ref(fp):return next(s.text(v[2]) for v in s.find(fp,'property') if s.text(v[1])=='Reference')
def fps(b):return {ref(fp):fp for fp in s.find(b,'footprint')}
def norm(o):
 if isinstance(o,tuple):return o[1]
 if isinstance(o,list):return [norm(x) for x in o]
 try:return round(float(o),6)
 except(ValueError,TypeError):return o
def edge(n):return sorted([norm([x[0]]+[v for v in x[1:] if isinstance(v,list) and v[0] in ['start','mid','end','layer']]) for x in n if isinstance(x,list) and x and x[0] in ['gr_line','gr_arc','fp_line','fp_arc'] and one(x,'layer') and s.text(one(x,'layer')[0])=='Edge.Cuts'],key=str)
def fp_sig(fp):return norm([s.text(fp[1]),one(fp,'at'),one(fp,'layer'),[[s.text(p[1]),p[2:4],one(p,'at'),one(p,'size'),one(p,'drill'),one(p,'layers'),one(p,'net'),one(p,'uuid')] for p in s.find(fp,'pad')],one(fp,'model')])
mf,cf,pmf,pcf=map(fps,(main,child,pm,pc))
comp={'main_outer_outline_unchanged':edge(main)==edge(pm),'main_J1_cutouts_unchanged':edge(mf['J1'])==edge(pmf['J1']),'main_J1_contact_and_transform_unchanged':fp_sig(mf['J1'])==fp_sig(pmf['J1']),'child_outer_outline_unchanged':edge(child)==edge(pc),'child_all_footprint_pad_net_models_unchanged':all(fp_sig(cf[r])==fp_sig(pcf[r]) for r in cf),'main_J2_to_J6_footprint_pad_net_models_unchanged':{r:fp_sig(mf[r])==fp_sig(pmf[r]) for r in ('J2','J3','J4','J5','J6')}}
assert all(comp[k] for k in list(comp)[:5]);assert all(comp['main_J2_to_J6_footprint_pad_net_models_unchanged'].values())
# VRML scope: this exact export has identity rotations/scales throughout, only connector translation.
t=FILES['model'].read_text();stack=[];br={}
for i,c in enumerate(t):
 if c=='{':stack.append(i)
 elif c=='}':br[stack.pop()]=i
assert not stack
trans=[]
for m in re.finditer(r'DEF (TXFM_\d+) Transform \{',t):
 h=t[m.end():t.index('children',m.end())]
 tr=tuple(map(float,re.search(r'translation ([^\n]+)',h)[1].split()));rot=tuple(map(float,re.search(r'rotation ([^\n]+)',h)[1].split()));sc=tuple(map(float,re.search(r'\n  scale ([^\n]+)',h)[1].split()))
 assert rot==(0,0,1,0) and sc==(1,1,1);trans.append((m.start(),br[m.end()-1],tr,m[1]))
def bounds(ps):return [[min(p[i] for p in ps) for i in range(3)],[max(p[i] for p in ps) for i in range(3)]]
def assembled(p):return (22.4-p[0],2.4-p[2],p[1]) # mm; main x/y down, z above main front copper
meshes=[];connector=[];boardmesh=[]
for m in re.finditer(r'DEF (SHAPE_\d+) Shape \{',t):
 body=t[m.end():br[m.end()-1]]; vals=[float(v) for v in re.findall(r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?',re.search(r'point\s*\[([^]]+)\]',body)[1])];ps=list(zip(*[iter(vals)]*3));trs=[x for x in trans if x[0]<m.start()<x[1]];off=[sum(x[2][i] for x in trs) for i in range(3)];ps=[tuple((p[i]+off[i])*2.54 for i in range(3)) for p in ps]
 is_conn=any(x[3]=='TXFM_2' for x in trs);(connector if is_conn else boardmesh).extend(ps)
 meshes.append({'name':m[1],'vertices':len(ps),'connector':is_conn,'native_model_mm_bbox':bounds(ps),'assembled_bbox':bounds(list(map(assembled,ps)))})
cb=bounds(list(map(assembled,connector)));bb=bounds(list(map(assembled,boardmesh)))
def padinfo(fp,p,orig):
 at=one(fp,'at');assert len(at)==2 or float(at[2])==0
 px,py=map(float,one(p,'at')[:2]);w,h=map(float,one(p,'size'))
 x=float(at[0])+px-orig[0];y=float(at[1])+py-orig[1]
 return {'ref':ref(fp),'number':s.text(p[1]),'net':s.text(one(p,'net')[-1]),'layers':[s.text(x) for x in one(p,'layers')],'box':[x-w/2,y-h/2,x+w/2,y+h/2],'size':[w,h]}
mp=[padinfo(mf['J1'],p,(100,100)) for p in s.find(mf['J1'],'pad')];cp=[padinfo(fp,p,(100,108.4)) for r,fp in cf.items() if r!='J1' for p in s.find(fp,'pad')]
contacts=[]
for c in cp:
 strip='F.Cu' in c['layers'];m=next(p for p in mp if p['net']==c['net'] and (p['box'][1]<2.4)==strip);xr=[22.4-c['box'][2],22.4-c['box'][0]]
 def overlap(dx):return max(0,min(m['box'][2],xr[1]+dx)-max(m['box'][0],xr[0]+dx))
 contacts.append({'child':c['ref'],'net':c['net'],'main_pad':m['number'],'type':'outer_strip' if strip else 'inner','assembled_x_mm':xr,'main_x_mm':[m['box'][0],m['box'][2]],'child_face_main_y_mm':1.6 if strip else 3.2,'main_land_y_mm':[m['box'][1],m['box'][3]],'nominal_x_overlap_mm':overlap(0),'worst_x_overlap_with_0p1_alignment_mm':min(overlap(-.1),overlap(.1)),'child_vertical_copper_mm':[-c['box'][3],-c['box'][1]],'exposed_height_main_1p6_mm':c['box'][3]-1.6,'exposed_height_main_1p76_mm':c['box'][3]-1.76,'nominal_solder_reach_mm':.6})
assert len(contacts)==11 and all(abs(c['nominal_x_overlap_mm']-(7.892 if c['type']=='outer_strip' else (1.6 if c['net'] in ['VX','GND'] else 1.2)))<1e-6 for c in contacts)
def eff(L,W,t,r):
 assert t<=W and r<=W/2;q=max(0,t/2-(W/2-r));return L-2*r+2*math.sqrt(r*r-q*q)
tols=[]
for name,L,W,T,t,r,pitch in [('nominal',10,2.1,8.4,1.6,.5,0),('adverse_size',9.8,1.9,8.6,1.76,.5,0),('adverse_pitch_R0p5',9.8,1.9,8.6,1.76,.5,.4),('adverse_pitch_R0p55',9.8,1.9,8.6,1.76,.55,.4),('adverse_pitch_R0p6',9.8,1.9,8.6,1.76,.6,.4),('loose_size',10.2,2.3,8.2,1.44,.5,0)]:
 xp=eff(L,W,t,r)-T; tols.append({'case':name,'slot_length':L,'slot_width':W,'tab_width':T,'child_thickness':t,'radius':r,'illustrative_pitch_mismatch':pitch,'x_play_total':xp,'remaining_x_budget_after_pitch':xp-pitch,'common_translation_half_budget':(xp-pitch)/2,'y_play_total':W-t})
def pos(p,at):
 a=math.radians(float(at[2]) if len(at)>2 else 0);x,y=p;return (float(at[0])+x*math.cos(a)+y*math.sin(a)-100,float(at[1])-x*math.sin(a)+y*math.cos(a)-100)
def fp_bbox(fp,layer):
 ps=[]
 for n in fp:
  if isinstance(n,list) and n and n[0] in ['fp_rect','fp_line','fp_arc','fp_poly','fp_circle'] and one(n,'layer') and s.text(one(n,'layer')[0]).endswith(layer):
   for k in ['start','mid','end','center']:
    ps +=[pos(tuple(map(float,q[1:3])),one(fp,'at')) for q in s.find(n,k)]
   for q in s.walk(n,'xy'):ps.append(pos(tuple(map(float,q[1:3])),one(fp,'at')))
 if not ps:return None
 return [min(p[0] for p in ps),min(p[1] for p in ps),max(p[0] for p in ps),max(p[1] for p in ps)]
items=[]
for r,fp in mf.items():
 if r=='J1':continue
 box=fp_bbox(fp,'CrtYd');fab=fp_bbox(fp,'Fab')
 if box:items.append({'ref':r,'layer':s.text(one(fp,'layer')[0]),'courtyard_bbox':box,'fab_bbox':fab,'nominal_y_gap_to_header_full_bbox':box[1]-cb[1][1],'model_paths':[s.text(q[1]) for q in s.find(fp,'model')],'model_files_present':[ (P/'hardware'/s.text(q[1]).replace('${KIPRJMOD}/','')).is_file() for q in s.find(fp,'model')]})
items.sort(key=lambda x:x['nominal_y_gap_to_header_full_bbox'])
result={'scope':'Read-only analytic native geometry and actual exported VRML mesh checks; no native renderer/DRC, physical assembly, fit/strength/current acceptance or fabrication','source_paths':{k:str(p) for k,p in FILES.items()},'source_sha256':H,'reviewed_candidate02_equivalence':comp,'model_transform':{'offset_mm':[22.4,-2.4,0],'kicad_rotation_deg':[-90,0,180],'scale':[1,1,1],'input_vrml_mm_per_unit':2.54,'child_native_to_main_local':'X=122.4-x_child; Y=2.4-z_child_centered; Z=108.4-y_child, height above main F.Cu','mesh_to_main_local':'X=22.4-2.54*u; Y=2.4-2.54*w; Z=2.54*v (u,v,w are model VRML coordinates)','verdict':'Existing transform matches intended nominal seating and face/contact order; do not add a half-thickness offset or change rotation signs.','sources':['https://docs.kicad.org/doxygen/3d__math_8cpp_source.html','https://docs.kicad.org/doxygen/exporter__vrml_8cpp_source.html']},'meshes':meshes,'header_connector_assembled_bbox':cb,'child_board_art_assembled_bbox':bb,'contacts':sorted(contacts,key=lambda x:(x['type'],x['assembled_x_mm'][0])),'tolerance_cases':tols,'nearby_component_courtyards':items,'loose_size_inward_connector_tip_y':2.4+(.2+2.1-1.44)/2-1.44/2+2.999994,'notes':['All dimensions in mm. Main coordinates use origin (100,100); Z=0 main front copper plane.','VRML board art offsets draw FR4 ±0.7875, copper ±0.8 and mask ±0.8125; these are rendering conventions, not independently specified manufacturing thicknesses.','Nominal contact overlap is longitudinal solder alignment, not direct copper area contact; the two boards meet perpendicularly across a 0.6 mm nominal fillet reach.','Manufacturing tolerance assumptions are inherited from reviewed candidate02; pitch and maximum radius are illustrative, not supplier-qualified.','Main component courtyards are 2D envelope screens, not verified 3D maximum material models. C27/C31 have no 3D model; use maximum 2.20 x 1.45 x 1.45 body.','D5 and main connector model paths are unresolved in this sealed package; absence cannot establish a rendered collision pass.','No enclosure model, connector mating plug/cable or assembly fixture is supplied.']}
assert {k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in FILES.items()}==H
(OUT/'assembly-review.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'source_sha256':H,'equivalence':comp,'connector_bbox':cb,'board_art_bbox':bb,'contacts':result['contacts'],'tolerances':tols,'nearest_courtyards':items[:8],'specific_parts':[i for i in items if i['ref'] in ['C27','C31','D5','J2','J3','J4','J5','J6']]},indent=2))
