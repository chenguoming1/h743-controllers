#!/usr/bin/python3
"""Read-only native KiCad copper audit. Never saves or alters a board."""
import argparse,collections,hashlib,json,math,time
from pathlib import Path
import pcbnew as p
ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('--sha256',required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--min-width',type=float,default=.13);ap.add_argument('--spacing',type=float,default=.16);ap.add_argument('--nontrace-spacing',type=float,default=.15);ap.add_argument('--skip-zones',action='store_true');a=ap.parse_args()
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(a.source)==a.sha256, 'Source does not match authorized SHA-256'
b=p.LoadBoard(str(a.source));start=time.time();minimum=p.FromMM(a.min_width);spacing=p.FromMM(a.spacing);layers=list(b.GetEnabledLayers().CuStack());hold=[];records=[];narrow=[];zone_hits=[]
xy=lambda q:[p.ToMM(q.x),p.ToMM(q.y)]
def uid(t):return t.m_Uuid.AsString()
def usb(t):return 'USB' in t.GetNetname().upper() and any(x in t.GetNetname().upper() for x in ['DP','DM','D+','D-','D_P','D_N'])
def rec(t):
 r={'id':uid(t),'net':t.GetNetname(),'net_code':t.GetNetCode()}
 if isinstance(t,p.PCB_VIA):r.update(kind='via',xy=xy(t.GetPosition()),diameter_mm=p.ToMM(t.GetWidth(p.F_Cu)),drill_mm=p.ToMM(t.GetDrillValue()))
 elif isinstance(t,p.PAD):r.update(kind='pad',ref=t.GetParentFootprint().GetReference(),pin=t.GetNumber(),xy=xy(t.GetPosition()))
 else:r.update(kind='arc' if isinstance(t,p.PCB_ARC) else 'track',layer=t.GetLayerName(),start=xy(t.GetStart()),end=xy(t.GetEnd()),width_mm=p.ToMM(t.GetWidth()),length_mm=p.ToMM(t.GetLength()),protected_usb=usb(t))
 return r
def bbox(s):
 bb=s.BBox();return bb.GetLeft(),bb.GetTop(),bb.GetRight(),bb.GetBottom()
def near(bb,cc,dist):return not(bb[2]+dist<cc[0] or cc[2]+dist<bb[0] or bb[3]+dist<cc[1] or cc[3]+dist<bb[1])
for t in list(b.GetTracks())+[pd for f in b.GetFootprints() for pd in f.Pads()]:
 r=rec(t);shapes={};wide={};wide_item=None
 if r['kind'] in ['track','arc'] and t.GetWidth()<minimum:
  narrow.append(r)
  if not usb(t):
   if isinstance(t,p.PCB_ARC):
    wide_item=p.PCB_ARC(b);wide_item.SetStart(t.GetStart());wide_item.SetMid(t.GetMid());wide_item.SetEnd(t.GetEnd())
   else:
    wide_item=p.PCB_TRACK(b);wide_item.SetStart(t.GetStart());wide_item.SetEnd(t.GetEnd())
   wide_item.SetLayer(t.GetLayer());wide_item.SetNetCode(t.GetNetCode());wide_item.SetWidth(minimum);hold.append(wide_item)
 for layer in layers:
  if not t.IsOnLayer(layer):continue
  s=t.GetEffectiveShape(layer);shapes[layer]=(s,bbox(s))
  if wide_item:
   ws=wide_item.GetEffectiveShape(layer);wide[layer]=(ws,bbox(ws))
  else:wide[layer]=shapes[layer]
 records.append((t,r,shapes,wide,bool(wide_item)))
print(json.dumps({'phase':'inventory','items':len(records),'narrow':len(narrow),'layers':[b.GetLayerName(z) for z in layers]}),flush=True)
conflicts=[];hist=collections.Counter();affected=collections.Counter();baseline_pairs=0;new_pairs=0
for i,(t,r,ss,ww,widened) in enumerate(records):
 for u,q,qs,qw,qwide in records[i+1:]:
  if r['net_code'] and r['net_code']==q['net_code']:continue
  for layer in ss.keys()&qs.keys():
   s,sb=ss[layer];o,ob=qs[layer];ws,wb=ww[layer];wo,wob=qw[layer]
   required=spacing if r['kind'] in ['track','arc'] and q['kind'] in ['track','arc'] else p.FromMM(a.nontrace_spacing)
   if not near(wb,wob,required):continue
   base=s.Collide(o,required);wide=ws.Collide(wo,required)
   if not base and not wide:continue
   actual=p.ToMM(s.GetClearance(o));actual_wide=p.ToMM(ws.GetClearance(wo));kind='-'.join(sorted([r['kind'],q['kind']]))
   row={'a':r['id'],'b':q['id'],'layer':b.GetLayerName(layer),'kind':kind,'required_mm':p.ToMM(required),'baseline_gap_mm':actual,'hypothetical_widened_gap_mm':actual_wide,'baseline_below_target':base,'widened_below_target':wide,'new_after_widening':wide and not base}
   conflicts.append(row);hist[(kind,'baseline' if base else 'new-after-widen')]+=1;affected[r['net']]+=1;affected[q['net']]+=1;baseline_pairs+=base;new_pairs+=(wide and not base)
 if i%500==0:print(json.dumps({'phase':'copper-pairs','item':i,'pairs':len(conflicts)}),flush=True)
# Filled copper is inventoried separately: it can be refilled, but changes need reference-plane review.
for z in ([] if a.skip_zones else b.Zones()):
 for layer in layers:
  if not z.IsOnLayer(layer) or not z.HasFilledPolysForLayer(layer):continue
  shape=z.GetFilledPolysList(layer);bb=bbox(shape)
  for t,r,ss,ww,widened in records:
   if r['net_code']==z.GetNetCode() or layer not in ss:continue
   s,sb=ss[layer];ws,wb=ww[layer]
   if not near(bb,wb,spacing):continue
   base=s.Collide(shape,p.FromMM(a.nontrace_spacing));wide=ws.Collide(shape,p.FromMM(a.nontrace_spacing))
   if base or wide:zone_hits.append({'item':r['id'],'zone':uid(z),'zone_net':z.GetNetname(),'layer':b.GetLayerName(layer),'baseline_below_target':base,'widened_below_target':wide,'baseline_gap_mm':p.ToMM(s.GetClearance(shape)),'hypothetical_widened_gap_mm':p.ToMM(ws.GetClearance(shape))})
# Exactly collinear degree-two joints preserve the copper union when merged at equal width.
by_node=collections.defaultdict(list)
for t,r,ss,ww,widened in records:
 if r['kind']!='track' or r['protected_usb']:continue
 for here,other in [(t.GetStart(),t.GetEnd()),(t.GetEnd(),t.GetStart())]:by_node[(t.GetNetCode(),t.GetLayer(),here.x,here.y)].append((t,r,(other.x-here.x,other.y-here.y)))
collinear=[];short_turns=[]
for key,rows in by_node.items():
 if len(rows)!=2:continue
 t,r,v=rows[0];u,q,w=rows[1]
 if t.GetWidth()!=u.GetWidth():continue
 cross=v[0]*w[1]-v[1]*w[0];dot=v[0]*w[0]+v[1]*w[1]
 entry={'a':r['id'],'b':q['id'],'net':r['net'],'layer':r['layer'],'join_mm':[p.ToMM(key[2]),p.ToMM(key[3])],'lengths_mm':[r['length_mm'],q['length_mm']]}
 if cross==0 and dot<0:collinear.append(entry)
 elif min(r['length_mm'],q['length_mm'])<.30:short_turns.append(entry)
width_count=collections.Counter((r['layer'],r['width_mm']) for _,r,_,_,_ in records if r['kind'] in ['track','arc']);narrow_nets=collections.Counter(r['net'] for r in narrow)
report={'source':str(a.source),'sha256':a.sha256,'method':'Native KiCad 9.0.2 effective copper shapes and GetClearance/Collide, with bounding-box broad phase. Board is never saved. Thresholds are study targets, not verified JLCDFM classifications. USB data-pair tracks are not widened.','min_width_mm':a.min_width,'spacing_target_mm':a.spacing,'nontrace_spacing_target_mm':a.nontrace_spacing,'layers':[b.GetLayerName(z) for z in layers],'summary':{'track_count':sum(r['kind'] in ['track','arc'] for _,r,_,_,_ in records),'narrow_track_count':len(narrow),'narrow_track_length_mm':sum(r['length_mm'] for r in narrow),'protected_usb_narrow_count':sum(r['protected_usb'] for r in narrow),'baseline_foreign_copper_pairs_below_target':baseline_pairs,'new_foreign_copper_pairs_after_width_only_change':new_pairs,'exact_collinear_join_candidates':len(collinear),'short_turn_candidates_unvalidated':len(short_turns),'filled_zone_item_hits_below_target_or_widening':len(zone_hits)},'width_histogram':[{'layer':l,'width_mm':w,'count':c}for(l,w),c in sorted(width_count.items())],'narrow_by_net':dict(narrow_nets.most_common()),'copper_pair_types':[{'kind':k,'category':c,'count':n}for(k,c),n in hist.most_common()],'affected_net_pair_counts':dict(affected.most_common()),'items':{r['id']:r for _,r,_,_,_ in records},'narrow_tracks':narrow,'foreign_copper_pairs':conflicts,'zone_hits':zone_hits,'collinear_join_candidates':collinear,'short_turn_candidates_unvalidated':short_turns,'elapsed_seconds':time.time()-start}
assert sha(a.source)==a.sha256,'Source changed during audit'
a.out.write_text(json.dumps(report,indent=2));print(json.dumps(report['summary']),flush=True)
