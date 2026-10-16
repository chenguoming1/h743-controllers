"""Apply-only coordinated ADC/DSM delta. Does not load, save, refill, or run DRC.
Expected input: stage33 geometry with C10/C12/Y1 and all original B ground retained,
plus parent's C29/R16 relocation and removal of old VX_SENSE routes.
Parent owns C29->R16, C29->ADC, and C29's quiet return.
reconnect_old_ground=True is required for the retained-ground candidate: it restores
the live C10/C12/Y1.2 tree to GND stitch (110.375,122.525), also tied to C25.2.
False is only for an explicitly verified replacement of that complete return tree.
"""
import sys
sys.path.insert(0,'/workspace/shared/nexus-main-placement-fix/scripts')
from router import *

C30_REMOVE_IDS={
 '0f14bd4d-b683-4a0e-b08c-1afabd0a9f14','65665935-d141-4ec4-867d-7a368f751691',
 'c3de4200-b39f-4a4d-a90f-8e389752dc5e','f8a7586e-ea45-4d68-b8dc-1781a7490039',
 '18a99482-dc02-4eab-a4d5-027591e1b2b2','4fb716cc-9707-4276-bbe2-bb7572994fca',
 '5f0f8c1d-528b-4b75-b254-541aa2b96a3a','6a587d52-e7f1-48fb-9f07-81c4394c4ef3',
 'aa5619ff-873b-4bf3-b7c4-c2e613778cb2','ad3c97ef-91a0-46c7-bbf8-6e93ce043885',
 '77dabf7b-f7b0-4de5-8b21-a08d70f66662','9fdb6c49-9ec2-4300-a2dc-24c408f0eaec',
 '77d81050-58a6-470d-b9ba-535a5df0f5fd',
}
DSM_REMOVE_IDS={
 'ea2fcd32-612d-4f7b-abd5-da944fe7b111', # original DSM via 111.025,123.675
 'e1826a78-56eb-4e65-a47e-04959ff29a23', # former DSM B bridge
 'c52d84d2-ab73-4340-acef-2a0febfffa3d', # former DSM In2 diagonal
 '3a5f9f92-0cf2-42df-87b3-919435a0d723', # GND link off stitch now DSM
 'd102ec12-9c83-4e54-bfee-f50279572b50', # isolated 0.014 mm GND stub
 'ff7cfb1b-c125-4db0-9000-8d64e4e8fec9', # obsolete C29 return; parent removes too
}
PATHS=[
 ('5V_SENSE',k.F_Cu,.127,[(113.91,114.16),(112.867689,114.797995)]),
 ('GND',k.F_Cu,.25,[(114.87,114.16),(114.4,113.6)]),
 ('DSM_TX',k.B_Cu,.127,[(108.775,123.675),(110.15,122.15),(110.590858,121.956)]),
 ('DSM_TX',k.In2_Cu,.127,[(110.590858,121.956),(112,122.7),(116.715,117.985)]),
 ('GND',k.B_Cu,.2,[(110.375,122.525),(110.85,122.35),(111.075,122.125),(111.176,121.956)]),
 ('GND',k.F_Cu,.2,[(111.4,123.71),(110.375,122.525)]),
 ('VX_SENSE',k.F_Cu,.2,[(111.4,120.64),(111.925,121.375),(111.95,121.5),(111.95,121.9),(111.875,122.025),(111.4,122.69)]),
]

def apply(b, strict=True, reconnect_old_ground=True):
 fs={f.GetReference():f for f in b.GetFootprints()};removed=[]
 # Source guards intentionally reject the abandoned NRST/clock-relocation trial.
 for ref,pos,angle in [('C10',(111.75,122.05),180),('C12',(112.35,120.5),-90),('Y1',(114.9,120.5),180)]:
  f=fs[ref]
  assert f.GetLayer()==k.B_Cu and math.dist(xy(f.GetPosition()),pos)<.00001 and abs(f.GetOrientationDegrees()-angle)<.00001, 'Retained-clock pose guard failed: '+ref
 for ref,pins in [('C30',{'1':'5V_SENSE','2':'GND'}),('R17',{'1':'VX_SENSE','2':'GND'})]:
  assert fs[ref].GetLayer()==k.F_Cu and {p.GetNumber():p.GetNetname() for p in fs[ref].Pads()}==pins, 'Pinout/layer guard failed: '+ref
 for ref,num,pos in [('C29','1',(111,118.72)),('R16','2',(111.4,120.64))]:
  assert math.dist(xy(next(p for p in fs[ref].Pads() if p.GetNumber()==num).GetPosition()),pos)<.00001, 'ADC port guard failed: '+ref
 tracks={t.m_Uuid.AsString():t for t in b.GetTracks()}
 for uid,net,pos in [('143f6a86-dfad-4a4b-8c52-59e7a5c3ed89','GND',(110.590858,121.956)),('a352772a-8c87-46bf-877b-6fd610aab36c','GND',(110.375,122.525)),('4c8b79af-68bd-4e72-ab67-315fc898e40d','5V_SENSE',(112.867689,114.797995))]:
  t=tracks[uid]
  assert t.GetClass()=='PCB_VIA' and t.GetNetname()==net and math.dist(xy(t.GetPosition()),pos)<.00001, 'Via source guard failed: '+uid
 for uid in ['22fed353-00d8-46ef-8e79-214d038508b6','81d2d709-ca26-458a-8ff5-186965268676','98f62710-a2ac-4c71-be26-d321136dd89e','aca49794-88d4-4009-9ff8-6f8d11613c61','bc8de5db-c205-4ab3-a414-5900c8c6d4ec','da1a158d-e1b5-4410-996d-0449f08b5394','fed846f1-114f-4743-92de-be26f7426347']:
  assert uid in tracks and tracks[uid].GetNetname()=='GND', 'Live clock-return guard failed: '+uid
 fs['C30'].SetPosition(vec((114.39,114.16)));fs['C30'].SetOrientationDegrees(0)
 fs['R17'].SetPosition(vec((111.4,123.2)));fs['R17'].SetOrientationDegrees(270)
 for t in list(b.GetTracks()):
  uid=t.m_Uuid.AsString()
  if uid in C30_REMOVE_IDS|DSM_REMOVE_IDS:removed.append(t);b.Remove(t);continue
  if uid=='143f6a86-dfad-4a4b-8c52-59e7a5c3ed89':
   assert t.GetClass()=='PCB_VIA' and math.dist(xy(t.GetPosition()),(110.590858,121.956))<.00001
   t.SetNet(b.FindNet('DSM_TX'))
  if t.GetClass()=='PCB_TRACK' and t.GetNetname()=='GND':
   for attr in ['Start','End']:
    if math.dist(xy(getattr(t,'Get'+attr)()),(114.9,114.16))<.00001:
     getattr(t,'Set'+attr)(vec((114.87,114.16)))
 for net,l,w,path in PATHS:
  if not reconnect_old_ground and net=='GND' and l==k.B_Cu:continue
  rt=Router(b,l,net,w)
  okay=all(rt.free(a,z) for a,z in zip(path,path[1:]))
  print('ADC_DELTA_PATH',net,b.GetLayerName(l),'clear',okay,'length_mm',sum(math.dist(a,z) for a,z in zip(path,path[1:])),path,flush=True)
  if strict and not okay:raise RuntimeError('Integration geometry blocks '+net+' '+b.GetLayerName(l))
  rt.add(path)
 return removed
