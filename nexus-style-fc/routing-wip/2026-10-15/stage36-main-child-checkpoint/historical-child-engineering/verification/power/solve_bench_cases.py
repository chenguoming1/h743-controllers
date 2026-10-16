import json,numpy as np,math,sys
from pathlib import Path
O=Path('/workspace/shared/nexus-compact-power-review');NAME=sys.argv[1] if len(sys.argv)>1 else 'prototype';M=json.load(open(O/(NAME+'-sheet-model.json'))); GEOM=json.load(open(O/(NAME+'-geometry.json')))
RHO20=1.724e-5
MATERIALS=[(70,20,1),(70,80,1),(60,20,.95),(60,80,.95)]
PROFILES={
'both_equal20m':[.02,.02,.02,.02],
'both_paired_weak_SBUS':[.02,.02,.08,.08],
'both_crossed_ESC_return_weak':[.02,.08,.08,.02],
'ESC_pair_open':[None,None,.04,.04],
'SBUS_pair_open':[.04,.04,None,None],
'ESC_positive_degraded_200m':[.20,.02,.02,.02],
'ESC_return_degraded_200m':[.02,.20,.02,.02],
'ESC_positive_open':[None,.02,.02,.02],
'ESC_return_open':[.02,None,.02,.02]}
ALLOCATIONS={'equal_four_bench':[2.5,2.5,2.5,2.5], 'uneven_8p9_plus_main':[4.5,1,1,2.4], 'moderate_3p5_plus_main':[1,1,1,.5], 'moderate_servo_only':[1,1,1,.5]}
def run(h,t,T,iacs,wall,profile,allocation,face='B.Cu',mainport='small',bridge=None):
 rho=RHO20*(1+.00393*(T-20))/iacs;sheet=rho/(t/1000)
 vx=next(m for m in M if m['h_mm']==h and m['net']=='VX');gn=next(m for m in M if m['h_mm']==h and m['net']=='GND')
 names=['VX:'+p for p in vx['ports']]+['GND:'+p for p in gn['ports']];nv=len(vx['ports']);n=len(names)
 K=np.zeros((n,n));K[:nv,:nv]=np.array(vx['K_unit_sheet_S'])/sheet;K[nv:,nv:]=np.array(gn['K_unit_sheet_S'])/sheet;sheetK=K.copy();b=np.zeros(n)
 def ix(s):return names.index(s)
 def res(p,q,r):
  u,v=ix(p),ix(q);g=1/r;K[u,u]+=g;K[v,v]+=g;K[u,v]-=g;K[v,u]-=g;return(u,v,g)
 barrels=[]
 # Barrel-only inter-face link, finished bore1.0 mm, length1.6 mm.
 # Pin/solder parallel shunt is deliberately excluded; each annular face is ideal.
 rb=1e-8 if wall==0 else rho*1.6/(math.pi*((.5+wall/1000)**2-.5**2))
 for net,pins in [('VX',[2,5,8,11,14,17,20]),('GND',[3,6,9,12,15,18,21])]:
  for pin in pins:barrels.append((net+':J1.'+str(pin),*res(net+':J1.'+str(pin)+':F.Cu',net+':J1.'+str(pin)+':B.Cu',rb)))
 for v in GEOM['tracks']:
  if v['type']!='PCB_VIA' or v['net'] not in ['VX','GND']:continue
  r=v['drill']/2
  vr=1e-8 if wall==0 else rho*1.6/(math.pi*((r+wall/1000)**2-r*r))
  name=v['net']+':VIA:'+v['uuid'];barrels.append((name,*res(name+':F.Cu',name+':B.Cu',vr)))
 bridges=[]
 if bridge is not None:
  bridges=[res('VX:T2.1:B.Cu','VX:K2.1:F.Cu',bridge),res('GND:T1.1:B.Cu','GND:K1.1:F.Cu',bridge)]
 sinks=[]
 for I,p,g in zip(ALLOCATIONS[allocation],[2,5,8,11],[3,6,9,12]):
  u=ix('VX:J1.'+str(p)+':'+face);v=ix('GND:J1.'+str(g)+':'+face);b[u]-=I;b[v]+=I;sinks.append(('servo_'+str(p),u,v,I))
 mainI=1.1 if allocation=='uneven_8p9_plus_main' else (1.1 if allocation=='moderate_3p5_plus_main' else 0)
 if mainI:
  p,q=('VX:T2.1:B.Cu','GND:T1.1:B.Cu') if mainport=='small' else ('VX:K2.1:F.Cu','GND:K1.1:F.Cu')
  u=ix(p);v=ix(q);b[u]-=mainI;b[v]+=mainI;sinks.append(('main_input',u,v,mainI))
 feeds=[]
 for name,p,r,voltage in zip(['ESC_positive','ESC_return','SBUS_positive','SBUS_return'],[14,15,20,21],PROFILES[profile],[7.4,0,7.4,0]):
  if r is None:continue
  u=ix(('VX' if voltage else 'GND')+':J1.'+str(p)+':'+face);g=1/r;K[u,u]+=g;b[u]+=g*voltage;feeds.append((name,u,g,voltage,r))
 V=np.linalg.solve(K,b)
 feedI={name:(v-V[u])*g*(1 if v else -1) for name,u,g,v,r in feeds}
 feedloss=sum((v-V[u])**2*g for name,u,g,v,r in feeds)
 barrelI={name:(V[u]-V[v])*g for name,u,v,g in barrels};barrelloss=sum((V[u]-V[v])**2*g for name,u,v,g in barrels)
 pv=V[:nv]-V[0];gv=V[nv:]-V[nv];sheetloss=float(pv@sheetK[:nv,:nv]@pv+gv@sheetK[nv:,nv:]@gv)
 bridgeloss=sum((V[u]-V[v])**2*g for u,v,g in bridges)
 supply=sum((v-V[u])*g*v for name,u,g,v,r in feeds);loadpower=sum((V[u]-V[v])*I for _,u,v,I in sinks)
 probes={name:float(V[u]-V[v]) for name,u,v,I in sinks}
 # Board-only drop relative to actual feed pad rails: report path minima; multiple feeds are different terminals.
 feedpairV={}
 for lab,p,g in [('ESC',14,15),('SBUS',20,21)]:feedpairV[lab]=float(V[ix('VX:J1.'+str(p)+':'+face)]-V[ix('GND:J1.'+str(g)+':'+face)])
 return dict(h_mm=h,copper_um=t,T_C=T,IACS=iacs,barrel_wall_um=wall,barrel_ohm=rb,profile=profile,allocation=allocation,injection_face=face,main_port=mainport,main_bridge_ohm=bridge,aggregate_A=sum(ALLOCATIONS[allocation])+mainI,source_A=sum(v for k,v in feedI.items() if 'positive'in k),load_A=ALLOCATIONS[allocation],main_A=mainI,feed_currents_A=feedI,feed_pair_V=feedpairV,load_pair_V=probes,barrel_currents_A=barrelI,sheet_loss_W=sheetloss,barrel_loss_W=barrelloss,bridge_loss_W=bridgeloss,lead_contact_loss_W=feedloss,copper_and_barrel_W=sheetloss+barrelloss,power_balance_error_W=supply-loadpower-sheetloss-barrelloss-bridgeloss-feedloss,linear_residual_A=float(max(abs(K@V-b))),ports_V=dict(zip(names,map(float,V))))
rows=[]
for h in [.10,.075]:
 for t,T,iacs in MATERIALS:
  for wall in [18,20]:
   for profile in PROFILES:
    for alloc in ALLOCATIONS:
     for main in (['small','broad'] if alloc in ['uneven_8p9_plus_main','moderate_3p5_plus_main'] else ['small']):
      rows.append(run(h,t,T,iacs,wall,profile,alloc,mainport=main))
# Source-face and ideal-barrel sensitivity at conservative material/fine grid only.
for wall in [0,18,20]:
 for face in ['F.Cu','B.Cu']:
  for profile in PROFILES:
   for alloc in ALLOCATIONS:
    rows.append(run(.075,60,80,.95,wall,profile,alloc,face=face))
(O/(NAME+'-bench-cases.json')).write_text(json.dumps({'source_sha256':json.load(open(O/(NAME+'-geometry.json')))['sha256'],'scope':'PCB COPPER/BARREL BENCHMARK ONLY, NOT CONTACT/HARNESS/THERMAL QUALIFICATION. Main board omitted: abstract load at selected child joint terminal. Main bridge absent. 2.5 A per servo is a synthetic balanced allocation, NOT an imposed channel rating. Finite 1mm bore barrels link ideal per-face lands. 60um is a proposed fabrication acceptance requirement, not vendor-certified actual material.','profiles_ohm':PROFILES,'allocations_A':ALLOCATIONS,'rows':rows},indent=2))
for alloc in ALLOCATIONS:
 print(alloc)
 for r in rows:
  if r['allocation']==alloc and r['h_mm']==.075 and r['copper_um']==60 and r['T_C']==80 and r['barrel_wall_um']==18 and r['injection_face']=='B.Cu' and r['main_port']=='small':
   print(r['profile'],round(min(r['load_pair_V'].values()),5),round(r['copper_and_barrel_W'],4),{k:round(v,4) for k,v in r['feed_currents_A'].items()},flush=True)
print('MAX linear residual A',max(r['linear_residual_A'] for r in rows),'MAX power balance W',max(abs(r['power_balance_error_W']) for r in rows))
