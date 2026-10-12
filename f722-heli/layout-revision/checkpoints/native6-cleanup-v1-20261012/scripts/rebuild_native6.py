#!/usr/bin/env python3
"""Rebuild the checked WIP board from published native7 hardware in a fresh folder.

Requires KiCad 10.0.6 Python and the paired project. This portable wrapper was
syntax checked; the original construction/check bodies produced this checkpoint.
A reconstruction is accepted as this exact artifact only if its board hash matches.
"""
import argparse, json
from pathlib import Path
import pcbnew as pcb
import export_native_copper as exporter
from native_checks import *
PACKAGE=Path(__file__).resolve().parent.parent
ROOT=Path('/')

def build(args):
    require(pcb.GetBuildVersion()=='10.0.6+dfsg-1','Use the recorded KiCad build')
    require(exporter.ERROR_IU==10,'Exporter contour error changed')
    r=read(PACKAGE/'compiled-cleanup-recipe-v1.json')
    provenance=read(PACKAGE/'provenance.json')
    require(sha(PACKAGE/'compiled-cleanup-recipe-v1.json')==provenance['recipe']['sha256'],'Recipe changed')
    source=args.source_hardware.resolve()
    for name, binding in provenance['source_hardware'].items():
        require(sha(source/name)==binding['sha256'],'Source hardware changed: '+name)
    root=args.output.resolve()
    require(not root.exists(),'Output folder must be absent')
    root.mkdir(parents=True)
    c={'hardware':{name:{'path':str(source/name),'sha256':binding['sha256']} for name,binding in provenance['source_hardware'].items()},
       'source_board':str(source/'f722-heli.kicad_pcb'),'variants':{'local_v1':{ref:row['proposed_pose'] for ref,row in r['pose_recipe'].items()}}}
    args.variant='local_v1'
    import shutil
    candidate=root/'diagnostic-board';candidate.mkdir()
    for name,binding in c['hardware'].items():
        target=candidate/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/binding['path'],target)
        require(sha(target)==binding['sha256'],'Hardware clone mismatch')
    board_path=candidate/'f722-heli.kicad_pcb'
    before=exporter.export(ROOT/c['source_board'])
    # Re-export the unmodified clone to bind the actual runtime to the exact source.
    reproduced=exporter.export(board_path)
    for key in ['objects','footprints','zones','edge_cuts','outline_with_npth','copper_layers']:
        require(before[key]==reproduced[key],'Official source reproduction differs: '+key)
    del reproduced
    board=pcb.LoadBoard(str(board_path));fps={f.GetReference():f for f in board.GetFootprints()}
    project=candidate/'f722-heli.kicad_pro';manager=pcb.GetSettingsManager()
    require(manager.LoadProject(str(project)),'Copied project failed to load')
    board.SetProject(manager.GetProject(str(project)))

    def raw_pad_settings():
        result={}
        for ref in sorted(fps):
            for pad in fps[ref].Pads():
                vector=lambda q:[q.x,q.y]
                result[pad.m_Uuid.AsString()]={'ref':ref,'number':pad.GetNumber(),'relative_angle':pad.GetFPRelativeOrientation().AsDegrees()%360,
                  'size':vector(pad.GetSize()),'offset':vector(pad.GetOffset()),'drill_size':vector(pad.GetDrillSize()),'drill_shape':int(pad.GetDrillShape()),
                  'attribute':int(pad.GetAttribute()),'net':pad.GetNetname(),'layers':[int(l) for l in pad.GetLayerSet().Seq()],
                  'zone_connection':int(pad.GetLocalZoneConnection()),
                  'local_mask':pad.GetLocalSolderMaskMargin(),'local_paste':pad.GetLocalSolderPasteMargin(),'local_paste_ratio':pad.GetLocalSolderPasteMarginRatio(),
                  'effective_paste':{str(int(l)):vector(pad.GetSolderPasteMargin(l)) for l in [pcb.F_Paste,pcb.B_Paste] if pad.IsOnLayer(l)}}
        return result

    def pad_settings():
        saved={ref:[f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees(),f.GetLayerName()] for ref,f in fps.items() if ref in c['variants'][args.variant]}
        for ref in saved:
            f=fps[ref];old=next(x for x in before['footprints'] if x['ref']==ref)
            if f.GetLayerName()!=old['side']:f.Flip(f.GetPosition(),pcb.FLIP_DIRECTION_LEFT_RIGHT)
            f.SetOrientationDegrees(old['angle']);f.SetPosition(pcb.VECTOR2I(*map(nm,old['xy'])))
        result=raw_pad_settings()
        for ref,pose in saved.items():
            f=fps[ref]
            if f.GetLayerName()!=pose[3]:f.Flip(f.GetPosition(),pcb.FLIP_DIRECTION_LEFT_RIGHT)
            f.SetOrientationDegrees(pose[2]);f.SetPosition(pcb.VECTOR2I(pose[0],pose[1]))
        return result
    settings=pad_settings()
    def capture_auxiliary(b):
        inners={};mechanics={}
        for f in b.GetFootprints():
            f.BuildCourtyardCaches()
            mechanics[f.GetReference()]={'uuid':f.m_Uuid.AsString(),'side':f.GetLayerName(),'courtyards':{b.GetLayerName(l):exporter.polygons(f.GetCourtyard(l)) for l in [pcb.F_Cu,pcb.B_Cu]}}
        # All record inside contours cover every later local query; no silent outer-only contact pass.
        for item in list(b.GetTracks())+[pad for f in b.GetFootprints() for pad in f.Pads()]:
            inners[item.m_Uuid.AsString()]={}
            for l in b.GetEnabledLayers().CuStack():
                if item.IsOnLayer(l) and (not hasattr(item,'FlashLayer') or item.FlashLayer(l)):
                    inners[item.m_Uuid.AsString()][b.GetLayerName(l)]=exporter.shape_polygons(item,l,pcb.ERROR_INSIDE,clearance=0)
        return {'inside':inners,'mechanics':mechanics}
    write(root/'before-auxiliary.json',capture_auxiliary(board))
    write(root/'before-pad-settings.json',settings)
    for ref,pose in c['variants'][args.variant].items():
        f=fps[ref]
        if f.GetLayerName()!=pose[3]:
            require(ref=='R6','Only R6 may flip');f.Flip(f.GetPosition(),pcb.FLIP_DIRECTION_LEFT_RIGHT)
        f.SetOrientationDegrees(pose[2]);f.SetPosition(pcb.VECTOR2I(nm(pose[0]),nm(pose[1])))
    routes={t.m_Uuid.AsString():t for t in board.GetTracks()}
    for uid in r['remove_source_records']:
        require(uid in routes,'Cut route UUID missing');board.Remove(routes[uid])
    held=[]
    for row in r['proposed_add_tracks']+r['proposed_add_vias']:
        require(board.FindNet(row['net']) is not None,'Added net not present in source')
        if row['kind']=='track':
            item=pcb.PCB_TRACK(board);item.SetStart(pcb.VECTOR2I(*map(nm,row['start'])));item.SetEnd(pcb.VECTOR2I(*map(nm,row['end'])));item.SetWidth(nm(row['width']));item.SetLayer(board.GetLayerID(row['layer']))
        else:
            item=pcb.PCB_VIA(board);item.SetPosition(pcb.VECTOR2I(*map(nm,row['xy'])));item.SetWidth(nm(row['diameter']));item.SetDrill(nm(row['drill']));item.SetViaType(pcb.VIATYPE_THROUGH);item.SetLayerPair(pcb.F_Cu,pcb.B_Cu);item.SetFrontTentingMode(pcb.TENTING_MODE_TENTED);item.SetBackTentingMode(pcb.TENTING_MODE_TENTED)
        item.SetUuid(pcb.KIID(row['uuid']));item.SetNet(board.FindNet(row['net']));board.Add(item);held.append(item)
    require(settings==pad_settings(),'Internal pad/paste/mask settings changed during move')
    pcb.SaveBoard(str(board_path),board)
    board=pcb.LoadBoard(str(board_path));fps={f.GetReference():f for f in board.GetFootprints()}
    import structural_flip as structural
    prefill_raw=structural.verify_raw_board(ROOT/c['source_board'],board_path,c['variants'][args.variant],r['remove_source_records'],r['proposed_add_tracks']+r['proposed_add_vias'])
    require(settings==pad_settings(),'Pad/aperture settings changed before refill')
    prefill=exporter.export(board_path);prefill_proof=verify_delta(before,prefill,c['variants'][args.variant],r)
    write(root/'before-refill-native-verification.json',{'proof':prefill_proof,'raw_source':prefill_raw,'board_sha256':sha(board_path),'all_exact_transformed_pads_verified_before_refill':True})
    del prefill
    board.SetProject(manager.GetProject(str(project)));board.SynchronizeNetsAndNetClasses(False);board.BuildConnectivity()
    require(pcb.ZONE_FILLER(board).Fill(board.Zones()),'Native zone refill failed')
    pcb.SaveBoard(str(board_path),board)
    require(settings==pad_settings(),'Internal pad settings changed after native save/refill')
    after=exporter.export(board_path);proof=verify_delta(before,after,c['variants'][args.variant],r)
    import structural_flip as structural
    raw=structural.verify_raw_board(ROOT/c['source_board'],board_path,c['variants'][args.variant],r['remove_source_records'],r['proposed_add_tracks']+r['proposed_add_vias'])
    write(root/'structural-edit-ledger.json',{'native':proof,'raw_source':raw,'before_pad_settings':settings,'after_pad_settings':pad_settings(),'accepted_or_adopted':False})
    write(root/'after-pad-settings.json',pad_settings())
    write(root/'after.native.json',after);write(root/'after-auxiliary.json',capture_auxiliary(board))
    write(root/'native-construction.json',{'recipe_sha256':sha(PACKAGE/'compiled-cleanup-recipe-v1.json'),'variant':args.variant,'board_sha256':sha(board_path),'native_sha256':sha(root/'after.native.json'),'auxiliary_sha256':{name:sha(root/name) for name in ['before-auxiliary.json','after-auxiliary.json']},'proof':proof,'pad_settings':settings,'refill_performed':True,'all_unlisted_routes_retained':True,'exact_recipe_cuts_and_adds_applied':True,'accepted_or_adopted':False})
    for name,binding in c['hardware'].items():
        if name!='f722-heli.kicad_pcb':require(sha(candidate/name)==binding['sha256'],'Paired non-board hardware changed')
    actual=sha(root/'diagnostic-board/f722-heli.kicad_pcb')
    require(actual==provenance['candidate_board']['sha256'],'Rebuilt board differs from sealed artifact; inspect before use')
    print(json.dumps({'board_sha256':actual,'exact_sealed_board_reproduced':True}))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-hardware',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    build(parser.parse_args())
