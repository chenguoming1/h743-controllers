from geometry import *
r54=SOURCE.parent.parent.parent/'r54-crx-ground';p=r54/'hardware/nexus-style-fc.kicad_pcb';t=json.loads((r54/'transaction.json').read_text());inventory=json.loads(OUT.joinpath('per-via-review.json').read_text())
changed={x['uuid'] for x in t['removed_tracks']}|{x['uuid'] for x in t['moved_vias']}
protected={r['via']['uuid'] for r in inventory['vias']}|{d['uuid'] for r in inventory['vias'] for d in r['all_direct_same_net_copper_donors']}
ns={};s=Path(__file__).with_name('geometry.py').read_text().replace(str(SOURCE),str(p)).replace(EXPECTED,sha(p.read_bytes()));exec(compile(s,'r54-static-parser','exec'),ns)
unchanged=all(block(nodes[u])==ns['block'](ns['nodes'][u]) for u in protected)
rec=dict(r53_sha256=EXPECTED,r54_sha256=sha(p.read_bytes()),r54_transaction_sha256=sha((r54/'transaction.json').read_bytes()),changed_item_uuids=sorted(changed),inventory_via_or_direct_donor_intersection=sorted(changed&protected),all_inventory_vias_pads_and_direct_donor_tracks_textually_unchanged=unchanged,qualification='Per-via item classification and direct donor inventory carry over; detailed fill-continuity and candidate validations remain explicitly r53-bound. This does not requalify r54 or any proposed changes. New r54 routing is outside the listed via locations.')
OUT.joinpath('r54-applicability.json').write_text(json.dumps(rec,indent=2));print(json.dumps(rec,indent=2))
