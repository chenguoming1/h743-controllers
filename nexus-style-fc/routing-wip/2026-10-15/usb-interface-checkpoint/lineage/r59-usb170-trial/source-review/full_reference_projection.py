"""Saved fill projections for all complete USB primitives; no refill or acceptance inference."""
from source_context import *
q=json.loads((D/'complete-transaction.json').read_text());src={o['uuid']:o for o in tracks+vias};oo=[o for o in q['add_primitives'] if o['net'] in ['USB_DP','USB_DM'] and o['kind']!='via']+[src[u] for u in q['preserve_bridge_uuids']]
refs={'F.Cu':['In1.Cu'],'B.Cu':['In4.Cu'],'In1.Cu':['F.Cu','In2.Cu'],'In3.Cu':['In2.Cu','In4.Cu']};paths={l:[MPath(np.array(p)) for p in ps] for l,ps in fills.items()};rows=[]
for o in oo:
 length=o.get('length_mm',math.dist(o['start'],o['end']));n=max(1,math.ceil(length/.005));tt=(np.arange(n)+.5)/n
 if o['kind']=='segment':
  a=np.array(o['start']);b=np.array(o['end']);v=b-a;norm=np.array([-v[1],v[0]])/np.linalg.norm(v);ss=a+tt[:,None]*v;sets=[ss+x*norm for x in [-o['width']/2,0,o['width']/2]]
 else:
  aa=o['start_radians']+tt*o['sweep_radians'];nn=np.column_stack((np.cos(aa),np.sin(aa)));sets=[np.array(o['center'])+(o['radius_mm']+x)*nn for x in [-o['width']/2,0,o['width']/2]]
 for l in refs[o['layer']]:
  masks=[];ids=[]
  for ss in sets:
   m=np.zeros(n,dtype=bool)
   for i,p in enumerate(paths.get(l,[])):
    hit=p.contains_points(ss,radius=1e-10);m|=hit
    if hit.any() and fill_ids[l][i]['id'] not in ids:ids.append(fill_ids[l][i]['id'])
   masks.append(m)
  rows.append(dict(id=o.get('id',o.get('uuid')),net=o['net'],layer=o['layer'],reference_layer=l,length_mm=length,start=o['start'],end=o['end'],sample_spacing_mm=length/n,center_uncovered_mm=float((~masks[1]).sum()*length/n),any_three_line_uncovered_mm=float((~np.logical_and.reduce(masks)).sum()*length/n),touched_fill_component_ids=ids))
(D/'full-saved-reference-projection.json').write_text(json.dumps(dict(source_sha256=H,rows=rows,limits=['Stored source fill only, before the proposed copper/antipad cutouts.','Per-primitive sums are copper totals, not connector path delay.','Touching component IDs and sampled coverage do not establish finite return paths, connected reference transitions or post-refill acceptance.','The new In1 DP branch cuts a reference layer under neighboring F.Cu copper; its own adjacent F/In2 projections are included, but this does not quantify the new slot effect.']),indent=2)+'\n')
print(len(rows),'reference rows')
