"""Apply one hash-bound, isolated power transaction with exact native retention checks.

Run with the local official KiCad Python. A successful construction still requires
full native DRC, process, mechanics, reference and loaded-power qualification.
"""
import argparse, hashlib, json, shutil, sys
from pathlib import Path
import pcbnew as p

HERE = Path(__file__).resolve().parent
ROUTING = HERE.parents[1]
sys.path.insert(0, str(ROUTING / 'native-tools'))
from export_native_copper import export

sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
vec = lambda xy: p.VECTOR2I(*[round(v * 1e6) for v in xy])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--proposal', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    q = json.loads(a.proposal.read_text())
    assert sha(a.source) == q['source_board_sha256']
    assert not a.out.exists(), 'Use a new isolated destination.'
    allowed = set(q['allowed_changed_nets'])
    assert allowed <= {'+5V_BEC', '+5V_PERIPH', 'USB_VBUS_RAW', 'GND'}
    before = export(a.source)
    old = {o['uuid']: o for o in before['objects']}
    remove = set(q['remove_tracks']) | set(q.get('remove_vias', []))
    assert all(old[x]['kind'] != 'pad' and old[x]['net'] in allowed for x in remove)
    assert all(old[x]['kind'] == 'track' for x in q['remove_tracks'])
    assert all(old[x]['kind'] == 'via' for x in q.get('remove_vias', []))
    shutil.copytree(a.source.parent, a.out, ignore=shutil.ignore_patterns('*.json', '*.log', '*.svg', '*.png', '*.py', '*.ses', '*.kicad_prl', '__pycache__'))
    for name in ['parts.json']:
        src = a.source.parent / name
        if src.exists(): shutil.copyfile(src, a.out / name)
    board_path = a.out / a.source.name
    b = p.LoadBoard(str(board_path.resolve()))
    tracks = {t.m_Uuid.AsString(): t for t in b.GetTracks()}
    for uid in sorted(remove): b.Remove(tracks[uid])
    intended = {uid: o['net'] for uid, o in old.items() if o['kind'] != 'pad' and uid not in remove}
    added = []
    held = []
    for s in q['segments']:
        assert s['net'] in allowed and s['layer'] in ['F.Cu', 'In2.Cu', 'In3.Cu', 'B.Cu']
        assert s['width'] >= .127 and s['start'] != s['end']
        t = p.PCB_TRACK(b)
        t.SetStart(vec(s['start'])); t.SetEnd(vec(s['end']))
        t.SetWidth(round(s['width'] * 1e6)); t.SetLayer(b.GetLayerID(s['layer']))
        t.SetNet(b.FindNet(s['net'])); b.Add(t); held.append(t)
        uid = t.m_Uuid.AsString(); intended[uid] = s['net']; added.append(uid)
    for v in q.get('vias', []):
        assert v['net'] in allowed
        t = p.PCB_VIA(b); t.SetPosition(vec(v['xy'])); t.SetWidth(450000); t.SetDrill(200000)
        t.SetViaType(p.VIATYPE_THROUGH); t.SetLayerPair(p.F_Cu, p.B_Cu)
        t.SetFrontTentingMode(p.TENTING_MODE_TENTED); t.SetBackTentingMode(p.TENTING_MODE_TENTED)
        t.SetNet(b.FindNet(v['net'])); b.Add(t); held.append(t)
        uid = t.m_Uuid.AsString(); intended[uid] = v['net']; added.append(uid)
    def nets(board):
        actual = {t.m_Uuid.AsString(): t.GetNetname() for t in board.GetTracks()}
        assert actual == intended, 'Native connectivity changed an intended net or track set.'
    nets(b)
    p.SaveBoard(str(board_path.resolve()), b)
    b = p.LoadBoard(str(board_path.resolve())); nets(b)
    project = board_path.with_suffix('.kicad_pro').resolve()
    sm = p.GetSettingsManager(); assert project.exists() and sm.LoadProject(str(project))
    b.SetProject(sm.GetProject(str(project))); b.SynchronizeNetsAndNetClasses(False); b.BuildConnectivity()
    for zone in b.Zones():
        if not zone.GetIsRuleArea(): zone.SetNeedRefill(True)
    assert p.ZONE_FILLER(b).Fill(b.Zones()), 'Native zone refill returned false.'
    nets(b); p.SaveBoard(str(board_path.resolve()), b)
    b = p.LoadBoard(str(board_path.resolve())); nets(b)
    after = export(board_path)
    now = {o['uuid']: o for o in after['objects']}
    retained = set(old) - remove
    assert all(now.get(uid) == old[uid] for uid in retained), 'An unapproved source object changed.'
    assert set(now) == retained | set(added)
    assert before['footprints'] == after['footprints'] and before['edge_cuts'] == after['edge_cuts'] and before['copper_layers'] == after['copper_layers']
    strip = lambda z: {k: v for k, v in z.items() if k not in {'filled', 'fill_representation'}}
    assert list(map(strip, before['zones'])) == list(map(strip, after['zones']))
    assert sha(a.source) == q['source_board_sha256']
    board_path.with_suffix('.native.json').write_text(json.dumps(after, separators=(',', ':')) + '\n')
    source_map = json.loads(a.source.with_suffix('.logical-route-map.json').read_text())
    assert source_map['board_sha256'] == q['source_board_sha256']
    assert not remove.intersection(source_map['logical_route_map']), 'Power transaction removed ordinary branch ownership.'
    route_map = dict(source_map, board_sha256=sha(board_path), source_sha256=sha(a.source))
    board_path.with_suffix('.logical-route-map.json').write_text(json.dumps(route_map, indent=2) + '\n')
    receipt = dict(status='constructed_and_refilled_not_native_or_loaded_qualification', source_board_sha256=sha(a.source), board_sha256=sha(board_path), proposal_sha256=sha(a.proposal), constructor_sha256=sha(Path(__file__)), source_object_count=len(old), retained_source_object_count=len(retained), removed_objects=[old[x] for x in sorted(remove)], added_objects=[now[x] for x in added], intended_net_assertions=['before_save', 'after_reload', 'after_refill', 'after_final_reload'], all_ordinary_logical_ownership_retained=True, all_footprints_outline_and_zone_designs_exact=True, reference_planes_refilled=True)
    (a.out / 'power-construction.json').write_text(json.dumps(receipt, indent=2) + '\n')
    shutil.copyfile(a.proposal, a.out / 'power-proposal.json')
    shutil.copyfile(Path(__file__), a.out / 'construct_power_candidate.used.py')
    print(json.dumps({k: v for k, v in receipt.items() if k not in ['removed_objects', 'added_objects']}))

if __name__ == '__main__': main()
