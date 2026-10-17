"""Finite barrel-segment, multilayer DC screen of the extracted current candidate."""
from pathlib import Path
import numpy as np,json,math
OUT=Path(__file__).resolve().parent
M=json.loads((OUT/'four-layer-sheet-model.json').read_text())
G=json.loads((OUT/'four-layer-geometry.json').read_text())
LAYERS=['F.Cu','In1.Cu','In2.Cu','B.Cu']
# Nominal copper-center distances for published JLC041622-3313 geometry.
# Scale full F-to-B barrel length to the same conservative 1.65 mm screen.
Z=np.array([0,.249,1.270,1.519])*1.65/1.519
PROFILES={'equal':[.02]*4,'unequal':[.02,.02,.08,.08],
          'ESC_only':[.04,.04,None,None],'SBUS_only':[None,None,.04,.04]}
rho=1.724e-5*(1+.00393*60)/.95
def run(h,profile,mainport='small'):
 vx=next(x for x in M if x['net']=='VX' and x['h_mm']==h)
 gn=next(x for x in M if x['net']=='GND' and x['h_mm']==h)
 names=['VX:'+p for p in vx['ports']]+['GND:'+p for p in gn['ports']]
 nv=len(vx['ports']);n=len(names);K=np.zeros((n,n));sheet=rho/.060
 K[:nv,:nv]=np.array(vx['K_unit_sheet_S'])/sheet;K[nv:,nv:]=np.array(gn['K_unit_sheet_S'])/sheet
 sheetK=K.copy();b=np.zeros(n);idx={s:i for i,s in enumerate(names)};barrels=[]
 def res(a,z,r,label):
  u,v=idx[a],idx[z];g=1/r;K[u,u]+=g;K[v,v]+=g;K[u,v]-=g;K[v,u]-=g;barrels.append((label,u,v,g))
 def barrel(prefix,bore):
  area=math.pi*((bore/2+.018)**2-(bore/2)**2)
  for k in range(3):res(prefix+':'+LAYERS[k],prefix+':'+LAYERS[k+1],rho*(Z[k+1]-Z[k])/area,prefix+':'+LAYERS[k]+'-'+LAYERS[k+1])
 for net,pins in [('VX',[2,5,8,11,14,17,20]),('GND',[3,6,9,12,15,18,21])]:
  for pin in pins:barrel(net+':J1.'+str(pin),.97)
 for t in G['tracks']:
  if t['type']=='PCB_VIA' and t['net'] in ['VX','GND']:barrel(t['net']+':VIA:'+t['uuid'],t['drill'])
 sinks=[]
 def load(name,pos,neg,I):
  u,v=idx[pos],idx[neg];b[u]-=I;b[v]+=I;sinks.append((name,u,v,I))
 for p,q,I in zip([2,5,8,11],[3,6,9,12],[5,5,5,3.5]):load('servo_'+str(p),'VX:J1.'+str(p)+':B.Cu','GND:J1.'+str(q)+':B.Cu',I)
 a,z=('VX:T2.1:B.Cu','GND:T1.1:B.Cu') if mainport=='small' else ('VX:K2.1:F.Cu','GND:K1.1:F.Cu')
 load('main',a,z,1.1)
 feeds=[]
 for label,pin,R,V in zip(['ESC_pos','ESC_ret','SBUS_pos','SBUS_ret'],[14,15,20,21],PROFILES[profile],[7.4,0,7.4,0]):
  if R is None:continue
  u=idx[('VX' if V else 'GND')+':J1.'+str(pin)+':B.Cu'];g=1/R;K[u,u]+=g;b[u]+=g*V;feeds.append((label,u,g,V))
 V=np.linalg.solve(K,b)
 sheetloss=0
 for net,off,ports,sz in [('VX',0,vx['ports'],nv),('GND',nv,gn['ports'],n-nv)]:
  for layer in LAYERS:
   ids=[off+i for i,p in enumerate(ports) if p.endswith(':'+layer)]
   vs=V[ids]-V[ids[0]];sheetloss+=float(vs@sheetK[np.ix_(ids,ids)]@vs)
 bi={lab:float((V[u]-V[v])*g) for lab,u,v,g in barrels}
 bloss=sum((V[u]-V[v])**2*g for _,u,v,g in barrels)
 fl=sum((v-V[u])**2*g for _,u,g,v in feeds)
 supply=sum((v-V[u])*g*v for _,u,g,v in feeds)
 lp=sum((V[u]-V[v])*I for _,u,v,I in sinks)
 probes={name:float(V[u]-V[v]) for name,u,v,_ in sinks}
 fp={lab:float((v-V[u])*g*(1 if v else -1)) for lab,u,g,v in feeds}
 rails={lab:float(V[idx['VX:J1.'+str(p)+':B.Cu']]-V[idx['GND:J1.'+str(q)+':B.Cu']]) for lab,p,q in [('ESC',14,15),('SBUS',20,21)]}
 result=dict(h_mm=h,profile=profile,main_port=mainport,sheet_loss_W=sheetloss,barrel_loss_W=float(bloss),board_loss_W=float(sheetloss+bloss),
  feed_currents_A=fp,lead_contact_loss_W=float(fl),load_pair_V=probes,feed_pair_V=rails,barrel_currents_A=bi,
  max_residual_A=float(max(abs(K@V-b))),power_balance_error_W=float(supply-lp-sheetloss-bloss-fl),ports_V=dict(zip(names,map(float,V))))
 if profile in ['ESC_only','SBUS_only']:
  result['board_only_worst_servo_drop_V']=rails[profile.split('_')[0]]-min(v for k,v in probes.items() if k.startswith('servo'))
 return result
if __name__=='__main__':
 rows=[]
 for h in sorted(set(x['h_mm'] for x in M)):
  for profile in PROFILES:
   for port in ['small','broad']:
    r=run(h,profile,port);rows.append(r)
    print(h,profile,port,'W',round(r['board_loss_W'],6),'sheet',round(r['sheet_loss_W'],6),'barrel',round(r['barrel_loss_W'],6),'drop_mV',round(r.get('board_only_worst_servo_drop_V',0)*1000,3),flush=True)
 assert max(x['max_residual_A'] for x in rows)<1e-7
 assert max(abs(x['power_balance_error_W']) for x in rows)<1e-5
 (OUT/'four-layer-full-load.json').write_text(json.dumps(dict(source_sha256=G['sha256'],layers=LAYERS,barrel_z_mm=Z.tolist(),outer_um=60,inner_um=55,temperature_C_prescribed=80,IACS=.95,barrel_wall_um=18,header_bore_mm_resistance_only=.97,servo_A=[5,5,5,3.5],main_A=1.1,rows=rows),indent=2)+'\n')
