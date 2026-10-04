#!/usr/bin/python3
"""Build a cumulative immutable-source UUID delta. Geometry approval is a separate mandatory gate."""
import os
os.environ.setdefault('KICAD_CONFIG_HOME','/tmp/controller-p6-final-kicad')
import pcbnew as p,pathlib,json,hashlib,collections,sys,shutil,argparse,re
D=pathlib.Path(__file__).resolve().parent;ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=pathlib.Path,required=True);ap.add_argument('--sha256',required=True);args=ap.parse_args();S=D/'input-p5/controller.kicad_pcb';PIN='6e2031b040ce8f3a534c2f73abb0091e25b3e6adcab982463264ad8898d65cf8';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();assert sha(S)==PIN and sha(args.candidate)==args.sha256

def blocks(text):
 out=[];depth=0;start=0;quoted=False;esc=False;comment=False
 for i,c in enumerate(text):
  if comment:
   if c=='\n':comment=False
   continue
  if quoted:
   if esc:esc=False
   elif c=='\\':esc=True
   elif c=='"':quoted=False
   continue
  if c=='"':quoted=True;continue
  if c==';':comment=True;continue
  if c=='(':
   depth+=1
   if depth==2:start=i
  elif c==')':
   if depth==2:out.append(text[start:i+1])
   depth-=1
 return out
key=lambda x:x[1:].split(None,1)[0].rstrip(')')
retirement=json.loads((D/'retirement-dispositions.json').read_text());assert retirement['candidate_sha256']==args.sha256 and retirement['source_sha256']==PIN;retired=set(retirement['authorized_removed_via_ids'])
oldblocks=blocks(S.read_text());newblocks=blocks(args.candidate.read_text());immutable=lambda bb:collections.Counter(x.replace('R3-S6-P6','R3-S6-P5') for x in bb if key(x) not in ['segment','arc','zone','via']);assert immutable(oldblocks)==immutable(newblocks)
via_blocks=lambda bb: {re.search(r'\(uuid "([^"]+)"\)',x).group(1):x for x in bb if key(x)=='via'}
source_via_blocks=via_blocks(oldblocks);final_via_blocks=via_blocks(newblocks);assert set(source_via_blocks)-set(final_via_blocks)==retired;assert {k:v for k,v in source_via_blocks.items() if k not in retired}==final_via_blocks
zones=lambda bb:collections.Counter(tuple(c for c in blocks(z) if key(c) not in ['filled_polygon','fill_segments']) for z in bb if key(z)=='zone');assert zones(oldblocks)==zones(newblocks),'Zone definition changed'
a=p.LoadBoard(str(S));b=p.LoadBoard(str(args.candidate));b.BuildConnectivity();assert b.GetConnectivity().GetUnconnectedCount(False)==0
uid=lambda t:t.m_Uuid.AsString()
def row(t):
 v=isinstance(t,p.PCB_VIA);r={'id':uid(t),'net':t.GetNetname(),'layer':t.GetLayerName(),'width_mm':p.ToMM(t.GetWidth(p.F_Cu) if v else t.GetWidth()),'start':[p.ToMM(t.GetStart().x),p.ToMM(t.GetStart().y)],'end':[p.ToMM(t.GetEnd().x),p.ToMM(t.GetEnd().y)],'kind':'via' if v else ('arc' if isinstance(t,p.PCB_ARC) else 'track')}
 if v:r.update(drill_mm=p.ToMM(t.GetDrillValue()),layer_pair=[t.TopLayer(),t.BottomLayer()])
 else:r['length_mm']=p.ToMM(t.GetLength())
 return r
A={uid(t):row(t) for t in a.GetTracks()};B={uid(t):row(t) for t in b.GetTracks()};removed=[A[k] for k in A.keys()-B.keys()];added=[B[k] for k in B.keys()-A.keys()];assert not [k for k in A.keys()&B.keys() if A[k]!=B[k]];assert {r['id'] for r in removed if r['kind']=='via'}==retired;assert all(r['kind']=='track' for r in added);assert all(r['kind'] in ['track','via'] for r in removed);assert min(r['width_mm'] for r in B.values() if r['kind']=='track')>=.13
planes=[]
for layer in [p.In1_Cu,p.In3_Cu,p.In4_Cu]:
 def plane(board):
  x=p.SHAPE_POLY_SET()
  for z in board.Zones():
   if z.GetNetname()=='GND' and z.IsOnLayer(layer) and z.HasFilledPolysForLayer(layer):x.BooleanAdd(z.GetFilledPolysList(layer))
  return x
 x,y=plane(a),plane(b);xx=p.SHAPE_POLY_SET(x);xx.BooleanSubtract(y);yy=p.SHAPE_POLY_SET(y);yy.BooleanSubtract(x);area=xx.Area()+yy.Area();expanded=p.SHAPE_POLY_SET(y);expanded.Inflate(2,p.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);residual=p.SHAPE_POLY_SET(x);residual.BooleanSubtract(expanded);assert residual.Area()<1;assert abs(yy.Area()/1e12-retirement['reference_plane_expected_gain_mm2'][b.GetLayerName(layer)])<1e-10, (b.GetLayerName(layer),yy.Area()/1e12);planes.append({'layer':b.GetLayerName(layer),'raw_loss_mm2':xx.Area()/1e12,'gain_mm2':yy.Area()/1e12,'loss_beyond_2nm_rounding_mm2':residual.Area()/1e12,'symmetric_difference_mm2':area/1e12,'disposition':'retirement-dispositions.json'})
by={}
for net in sorted({r['net'] for r in removed+added}):
 rr=[r for r in removed if r['net']==net];aa=[r for r in added if r['net']==net];by[net]={'removed':sum(r['kind']=='track' for r in rr),'added':len(aa),'retired_vias':sum(r['kind']=='via' for r in rr),'segment_reduction':sum(r['kind']=='track' for r in rr)-len(aa),'old_length_mm':sum(r.get('length_mm',0) for r in rr),'new_length_mm':sum(r.get('length_mm',0) for r in aa)}
summary={'old_track_count':sum(r['kind']=='track' for r in A.values()),'new_track_count':sum(r['kind']=='track' for r in B.values()),'removed_segments':sum(r['kind']=='track' for r in removed),'added_segments':len(added),'segment_reduction':sum(r['kind']=='track' for r in removed)-len(added),'changed_nets':len(by),'old_length_mm':sum(r.get('length_mm',0) for r in removed),'new_length_mm':sum(r['length_mm'] for r in added),'source_vias':sum(r['kind']=='via' for r in A.values()),'final_vias':sum(r['kind']=='via' for r in B.values()),'retired_vias':len(retired),'ground_vias_unchanged':sum(r['kind']=='via' and r['net']=='GND' for r in B.values()),'footprints_fixed':len(list(a.GetFootprints()))}
report={'source':'input-p5/controller.kicad_pcb','source_sha256':PIN,'candidate':'controller.kicad_pcb','candidate_sha256':args.sha256,'native_opens_after_refill':0,'summary':summary,'invariants':{'nonrouting_objects_byte_identical_except_declared_revision_label_and_exact_six_via_retirement':True,'all_surviving_via_records_identical':True,'zone_definitions_identical':True,'unchanged_track_uuid_records_identical':True,'reference_planes':planes,'trace_minimum_mm':.13},'board_metadata_replacements':[{'old':'(rev "R3-S6-P5")','new':'(rev "R3-S6-P6")','count':1,'purpose':'Approved P6 revision label only'}],'reference_engineering_dispositions_file':'reference-dispositions.json','via_retirement_dispositions_file':'retirement-dispositions.json','attachment_quality_gate':'validate_attachment_quality.py; must pass before acceptance/export','by_net':by,'removed':sorted(removed,key=lambda r:r['id']),'added':sorted(added,key=lambda r:r['id'])};shutil.copy2(args.candidate,D/'controller.kicad_pcb');(D/'source-delta.json').write_text(json.dumps(report,indent=2));(D/'by-net-changes.csv').write_text('net,removed,added,segment_reduction,old_length_mm,new_length_mm\n'+'\n'.join(','.join([net]+[str(r[k]) for k in ['removed','added','segment_reduction','old_length_mm','new_length_mm']]) for net,r in by.items())+'\n');assert sha(S)==PIN and sha(args.candidate)==args.sha256;print(json.dumps({'candidate_sha256':args.sha256,'summary':summary,'reference_planes':planes}),flush=True);sys.stdout.flush();os._exit(0)
