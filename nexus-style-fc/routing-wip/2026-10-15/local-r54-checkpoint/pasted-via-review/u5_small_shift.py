from geometry import *
v=items['de26675a-ecba-4fa3-966f-2bc38e53bb1f'];pads=[p for p in items.values() if p['kind']=='pad' and any(x in p['all_native_layers'] for x in ['F.Mask','B.Mask'])]
pts=[[102.675,108.305011],[102.675,108.350011],[102.4,108.350011],[102.425,108.350011],[102.45,108.350011],[102.825,108.350011],[102.85,108.350011],[102.875,108.350011],[102.9,108.350011]]
res=[]
for i,p in enumerate(pts):
 q=dict(v,uuid=v['uuid']+str(i),at=p);ob=[];mask=[]
 for o in items.values():
  if o['net']==v['net']:continue
  d=gap(q,o)
  if d<.127002:ob.append(dict(uuid=o['uuid'],net=o['net'],kind=o['kind'],ref=o.get('ref'),pin=o.get('pin'),layers=o['layers'],copper_gap_mm=d))
 for o in pads:
  ps,pr=shape(o);d=bases_dist([p],ps)-pr-.1
  if d<.050001:mask.append(dict(uuid=o['uuid'],ref=o['ref'],pin=o['pin'],net=o['net'],layers=o['layers'],drill_to_source_opening_gap_mm=d,meets_exploratory_0_05_mm_registration_allowance=d>=.05-1e-8))
 r=dict(at=p,shift_mm=math.dist(v['at'],p),mask_registration_allowance_mm=.05,allowance_is_a_study_parameter_not_a_JLC_commitment=True,opening_issues=mask,copper_issues=sorted(ob,key=lambda x:x['copper_gap_mm']))
 res.append(r);print(p,'mask',[(x['ref']+'.'+x['pin'],round(x['drill_to_source_opening_gap_mm'],6)) for x in mask],'cu',[(x['ref'] or x['uuid'][:8],x['net'],round(x['copper_gap_mm'],6)) for x in r['copper_issues']])
OUT.joinpath('u5-bounded-small-shift.json').write_text(json.dumps(res,indent=2))
