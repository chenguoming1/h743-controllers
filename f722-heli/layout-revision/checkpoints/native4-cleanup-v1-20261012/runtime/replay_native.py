#!/usr/bin/env python3
"""Rebuild only this exact recipe with official KiCad 10.0.6 in a new directory.

This portable wrapper was syntax-checked and its exact mutation loop was reviewed
against the saved candidate. It was not executed during checkpoint packaging.
Use verify_saved.py for the verified non-native reconstruction and identity check.
"""
import argparse, copy, gzip, hashlib, json, lzma, shutil
from pathlib import Path
import native_trial as n
from apply_recipe import apply_recipe
import polygon_native,transaction_guard,island_guard
ROOT=Path(__file__).resolve().parent.parent

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--repository-root',type=Path)
    args=p.parse_args()
    n.require(not args.output.exists(),'Choose a new output directory')
    references=n.read(ROOT/'INPUT-REFERENCES.json');ref=references['source_board']
    roots=[args.repository_root] if args.repository_root else [ROOT,*ROOT.parents]
    source=next((r/ref['repository_path'] for r in roots if r is not None and (r/ref['repository_path']).is_file()),None)
    n.require(source is not None and n.sha(source)==ref['sha256'],'Exact referenced source board required')
    recipe=n.read(ROOT/'recipe/compiled-additive-recipe-v1.json')
    provenance=n.read(ROOT/'SOURCE-PROVENANCE.json')
    binding=next(r for r in provenance['files'] if r['path']=='recipe/compiled-additive-recipe-v1.json')
    n.require(n.sha(ROOT/binding['path'])==binding['publication']['sha256'],'Published recipe changed')
    import pcbnew as pcb
    import export_with_polygon as exporter
    n.require(pcb.GetBuildVersion()=='10.0.6+dfsg-1','Use the declared KiCad 10.0.6+dfsg-1 runtime')
    target=args.output.resolve();target.mkdir()
    shutil.copytree(ROOT/'hardware',target/'hardware')
    board_path=target/'hardware/f722-heli.kicad_pcb';shutil.copyfile(source,board_path)
    project=target/'hardware/f722-heli.kicad_pro'
    manager=pcb.GetSettingsManager();n.require(manager.LoadProject(str(project)),'Project failed to load')
    board=pcb.LoadBoard(str(board_path));board.SetProject(manager.GetProject(str(project)))
    poses={ref:row['proposed_pose'] for ref,row in recipe['pose_recipe'].items()}
    held=apply_recipe(board,pcb,recipe,poses)
    held.append(polygon_native.add_shape(board,transaction_guard.DECLARATION,transaction_guard.DECLARATION_SHA,pcb))
    island_guard.apply_policy(board,pcb)
    pcb.SaveBoard(str(board_path),board)
    board=pcb.LoadBoard(str(board_path));board.SetProject(manager.GetProject(str(project)))
    board.SynchronizeNetsAndNetClasses(False);board.BuildConnectivity()
    n.require(pcb.ZONE_FILLER(board).Fill(board.Zones()),'Native zone refill failed')
    pcb.SaveBoard(str(board_path),board)
    actual=exporter.export(board_path,transaction_guard.DECLARATION,transaction_guard.DECLARATION_SHA)
    expected=json.loads(lzma.decompress((ROOT/'evidence/candidate.native.json.xz').read_bytes()))
    # Integer net-code allocation is serialization; require a complete name/code bijection.
    def semantic(data):
        names={};codes={}
        for row in data['objects']+data['zones']:
            name,code=row['net'],row['net_code']
            n.require(name not in names or names[name]==code,'Net name has multiple codes')
            n.require(code not in codes or codes[code]==name,'Net code has multiple names')
            names[name]=code;codes[code]=name
        out=copy.deepcopy({k:data[k] for k in ['objects','footprints','zones','edge_cuts','outline_with_npth','copper_layers','board_thickness_mm']})
        for row in out['objects']+out['zones']:row['net_code']=row['net']
        return out
    n.require(semantic(actual)==semantic(expected),'Replayed native geometry/UUIDs/net identities differ')
    output=target/'after.native.json'
    output.write_text(json.dumps(actual,sort_keys=True,separators=(',',':'))+'\n')
    print(json.dumps({'native_geometry_and_identities_exact':True,'board_sha256':n.sha(board_path),
                      'byte_identical_board':n.sha(board_path)=='293631bc83f880a11bf5d5da2cd2d21cc3e1ecb12e8e95731ef2547a10bcc862',
                      'fresh_DRC_ERC_and_parity_still_required':True,'output':str(target)}))

if __name__=='__main__':main()
