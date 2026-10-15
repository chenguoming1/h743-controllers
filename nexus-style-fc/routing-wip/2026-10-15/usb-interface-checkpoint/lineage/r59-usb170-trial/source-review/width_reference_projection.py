"""Saved actual-fill projection for the separate width variants, including tapered terminal widths."""
from source_context import *
T=json.loads((D/'trunk-proposal.json').read_text());paths={l:[MPath(np.array(p)) for p in ps] for l,ps in fills.items()}
for iw in [160,170,180]:
 f=D/f'width-{iw}-variant.json';o=json.loads(f.read_text());w=iw/1000;rows=[]
 for i,ss in enumerate(T['sections']):
  p=ss['primitive'];start=np.array(p['start']);end=np.array(p['end']);
  if i==len(T['sections'])-1:end[1]=110.85
  length=math.dist(start,end) if p['kind']=='segment' else p['length_mm'];n=max(1,math.ceil(length/.001));t=(np.arange(n)+.5)/n
  if p['kind']=='segment':
   v=(end-start)/length;xy=start+t[:,None]*(end-start);normal=np.tile([-v[1],v[0]],(n,1))
  else:
   a=p['start_radians']+t*p['sweep_radians'];nn=np.column_stack((np.cos(a),np.sin(a)));xy=np.array(p['center'])+p['radius_mm']*nn;normal=(-1 if p['sweep_radians']>0 else 1)*nn
  ww=np.full(n,w)
  if i==0:ww=np.minimum(ww,.15+(w-.15)*np.minimum(1,(124-xy[:,1])/.2))
  if i==len(T['sections'])-1:ww=np.minimum(ww,.15+(w-.15)*np.minimum(1,(xy[:,1]-110.85)/.2))
  rays=[-(2*ww+.127)/2,-(ww+.127)/2,np.full(n,-.127/2),np.zeros(n),np.full(n,.127/2),(ww+.127)/2,(2*ww+.127)/2]
  for layer in ['In1.Cu','In2.Cu','In4.Cu']:
   masks=[];ids=[]
   for ray in rays:
    points=xy+ray[:,None]*normal;m=np.zeros(n,dtype=bool)
    for fi,poly in enumerate(paths[layer]):
     hit=poly.contains_points(points,radius=1e-10);m|=hit
     if hit.any() and fill_ids[layer][fi]['id'] not in ids:ids.append(fill_ids[layer][fi]['id'])
    masks.append(m)
   rows.append(dict(section_index=i,reference_layer=layer,sample_spacing_mm=length/n,center_uncovered_mm=float((~masks[3]).sum()*length/n),any_seven_line_uncovered_mm=float((~np.logical_and.reduce(masks)).sum()*length/n),touched_component_ids=ids))
 o['variant_saved_reference_projection']=dict(per_section=rows,summary={l:{k:sum(r[k] for r in rows if r['reference_layer']==l) for k in ['center_uncovered_mm','any_seven_line_uncovered_mm']} for l in ['In1.Cu','In2.Cu','In4.Cu']},qualification='Saved source fill membership only, no post-refill or finite return proof. Each wider envelope and its explicit terminal tapers sampled independently.')
 f.write_text(json.dumps(o,indent=2)+'\n');print(iw,o['variant_saved_reference_projection']['summary'])
