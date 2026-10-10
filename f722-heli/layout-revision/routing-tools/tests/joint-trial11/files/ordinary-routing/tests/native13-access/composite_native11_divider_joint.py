"""Complete local divider support on corrected joint signal packet; no native adoption."""
import json,hashlib
from composite_native11_CSGREEN_C_RED_CAP import *
D=H/'divider-ground-domain-native11.json';G=H/'divider-ground-finite-margin11.json'
DIV=json.loads(D.read_text());GR=json.loads(G.read_text());assert DIV['complete_local_divider_MID_IMU_ground']and GR['passed']
EXTRA_CUTS={'3626f6cc-be40-5a8d-8986-c8125a15e930','eedfc367-c461-562d-aa85-69f54e0d2b29','58875d78-33e0-43fb-879b-22554b70173c','a7116edf-7f47-4bb1-824f-eff8212fed00','8074ddce-ca09-4994-8805-3fe327acfc96','991d0e93-c7b2-44e7-8624-30e7e498d446','c13414ed-d272-42d0-a868-72e3fcc13b42','96709e88-de8b-4afa-bab2-22bec5f81f1c'}
BASE=[q for q in BASE if q[0]['uuid']not in EXTRA_CUTS and q[0].get('ref')not in ('R43','R44')]
DIVIDER_PADS=DIV['rows'][0]['pads'];BASE += [entry(o)for o in DIVIDER_PADS]
DIVIDER_ROUTES=DIV['routes'][:2]+[GR['selected']['route']];DIVIDER_VIAS=[GR['selected']['via']]
for i,r in enumerate(DIVIDER_ROUTES):BASE.append(track(r['net'],r['layer'],r['points'],'divider-route-'+str(i),r['width']))
for i,v in enumerate(DIVIDER_VIAS):BASE.append(via(v['net'],v['xy'],'divider-via-'+str(i)))
REMOVED_NATIVE_IDS=set(REMOVED_NATIVE_IDS)|EXTRA_CUTS
s.OBJECTS=BASE;assert len({q[0]['uuid']for q in BASE})==len(BASE)
_prior_binding=binding
def binding():
 b=_prior_binding();b.update(explicit_source_removals=sorted(REMOVED_NATIVE_IDS),divider_input_receipts={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in [D,G]},declared_poses=DIV['rows'][0]['poses'],local_divider_support_complete=True,actual_ADC_tree_complete=False,actual_BOOT_tree_complete=False,IMU_feed_intentionally_changed=True,prior_numerical_power_AC_transferable=False,fresh_power_AC_required=True,native_candidate=False)
 return b

# Accessors must expose the transformed physical pads, not inherited source poses.
pads = {}
for o,c,m,d in BASE:
 if o["kind"]=="pad":pads.setdefault(o["key"],[]).append(o)
def one_pad(key):
 rows=pads[key];assert len(rows)==1,(key,len(rows));return rows[0]
