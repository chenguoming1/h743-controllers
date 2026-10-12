"""Only the exact two-track recipe and unchanged power/fill contract controls."""
import copy,resource,unittest
from pathlib import Path
import stitch_guard as g

class Controls(unittest.TestCase):
 def test_exact_two_tracks_and_reject_unrelated_changes(self):
  p=g.check_sources();d=g.read(p['delta']);r=g.read(p['cumulative_recipe']);g.validate_recipe(d,r)
  for key in ['endpoint','via','polygon','pose','cut']:
   a=copy.deepcopy(d);b=copy.deepcopy(r)
   if key=='endpoint':a['add_tracks'][0]['end'][0]+=.000001
   elif key=='via':b['proposed_add_vias'][0]['xy'][0]+=.000001
   elif key=='polygon':b['proposed_add_copper_polygons'][0]['outer_nm'][0][0]+=1
   elif key=='pose':b['pose_recipe']['U15']['proposed_pose'][0]+=.001
   else:a['remove_native4_records'].pop(next(iter(a['remove_native4_records'])))
   with self.subTest(key=key),self.assertRaises(ValueError):g.validate_recipe(a,b)
 def test_frozen_actual_power_projection_and_negative_hole(self):
  source=g.read_source('native');proof=g.power_equivalence(source,source)
  self.assertTrue(proof['all_15_power_networks_exact']);self.assertTrue(proof['all_326_full_hole_owner_records_exact'])
  # A shallow view avoids duplicating the complete board under the 512 MiB cap.
  changed=dict(source);changed['objects']=list(source['objects']);idx=next(i for i,o in enumerate(changed['objects']) if o.get('drill'))
  changed['objects'][idx]=copy.deepcopy(changed['objects'][idx]);changed['objects'][idx]['drill']['width']+=.000001
  with self.assertRaises(ValueError):g.power_equivalence(source,changed)
  self.assertEqual(g.sha(g.HERE/'compact_json.py'),g.sha(g.HERE.parent/'native4-return-stitch-native-preparation-v1/compact_json.py'))

if __name__=='__main__':
 resource.setrlimit(resource.RLIMIT_AS,(536870912,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,61));unittest.main()
