#!/usr/bin/python3
"""Independent P3 fabrication checker; reads CAD/export and writes only audit JSON.

Uses native effective hole segments, rather than the exporter's slot-angle formula.
Checks every copper pad flash, the exact native outer profile, job metadata, and
the separately conserved user supplier-placement file.
"""
import os
os.environ.setdefault('KICAD_CONFIG_HOME', '/tmp/controller-r3-kicad')
import argparse, collections, csv, hashlib, json, math, pathlib, re
import pcbnew as p

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def mm(v): return round(p.ToMM(v), 6)
def xy(v): return (mm(v.x), mm(v.y))
def ex(v): return (mm(v.x), round(38-mm(v.y), 6))
def feature(plated, diameter, a, b=None):
    return (plated, round(diameter, 6), *sorted((a, b if b is not None else a)))

def drill_features(path):
    txt = path.read_text()
    assert 'METRIC' in txt and 'G90' in txt and 'G91' not in txt
    assert 'FORMAT={-:-/ absolute / metric / decimal}' in txt
    plated = 'TF.FileFunction,Plated,1,6,PTH' in txt
    assert plated or 'TF.FileFunction,NonPlated,1,6,NPTH' in txt
    tools, out = {}, []
    tool = None
    def point(s):
        m = re.fullmatch(r'X(-?\d+\.\d{6})Y(-?\d+\.\d{6})', s)
        assert m, 'Unexpected drill coordinate syntax: '+s
        return tuple(float(z) for z in m.groups())
    for line in txt.splitlines():
        m = re.fullmatch(r'T(\d+)C(\d+\.\d+)', line)
        if m: tools[m[1]]=float(m[2]); continue
        m = re.fullmatch(r'T(\d+)', line)
        if m: tool=m[1]; continue
        if line.startswith(('X','Y')):
            endpoints=line.split('G85')
            assert len(endpoints) in (1,2)
            out.append(feature(plated,tools[tool],point(endpoints[0]),point(endpoints[-1])))
        assert not line.startswith(('G00','G01','M15','M16')), 'Unexpected routed-slot mode'
    return out

def gerber_objects(path):
    pin, component, pos, mode = None, None, (0.,0.), 'G01'
    flashes, paths = [], []
    for line in path.read_text().splitlines():
        if line.startswith('%TO.P,'):
            a=line[len('%TO.P,'):-2].split(','); pin=(a[0],a[1])
        elif line.startswith('%TO.C,'): component=line[len('%TO.C,'):-2]
        elif line=='%TD*%': pin=None;component=None
        elif line=='%TD.P*%': pin=None
        elif line=='%TD.C*%': component=None
        elif line in ('G01*','G02*','G03*'): mode=line[:-1]
        else:
            m=re.fullmatch(r'X(-?\d+)Y(-?\d+)(?:I(-?\d+)J(-?\d+))?D0([123])\*',line)
            if not m: continue
            v=(int(m[1])/1e6,int(m[2])/1e6); op=int(m[5])
            if op==3 and (pin or component): flashes.append((*(pin or (component,'')),*v))
            if op==1:
                center=None if m[3] is None else (round(pos[0]+int(m[3])/1e6,6),round(pos[1]+int(m[4])/1e6,6))
                paths.append({'mode':mode,'start':pos,'end':v,'center':center})
            pos=v
    return flashes,paths

ap=argparse.ArgumentParser();ap.add_argument('--project',type=pathlib.Path,required=True);ap.add_argument('--release',type=pathlib.Path);ap.add_argument('--out',type=pathlib.Path,required=True)
a=ap.parse_args();D=a.project.resolve();R=(a.release or D/'release').resolve();O=a.out.resolve();O.mkdir(parents=True,exist_ok=True)
boardpath=D/'controller.kicad_pcb';h=sha(boardpath);b=p.LoadBoard(str(boardpath));fps={f.GetReference():f for f in b.GetFootprints()}
errors=[];facts={}
def check(ok,message):
    if not ok:errors.append(message)

try:
    check(xy(b.GetDesignSettings().GetAuxOrigin())==(0,38),'Native datum differs')
    meta=json.loads((R/'export-verification.json').read_text());check(meta['native_sha256']==h,'Export source hash differs')
    manifest=json.loads((R/'SHA256_MANIFEST.json').read_text());actual={str(f.relative_to(R)) for f in R.rglob('*') if f.is_file() and f.name!='SHA256_MANIFEST.json'}
    check(actual==set(manifest),'Release manifest coverage differs')
    for name,v in manifest.items():check(sha(R/name)==v,'Release hash differs: '+name)
    profile=json.loads((R/'manufacturing-profile.json').read_text());check(profile==json.loads((D/'review/manufacturing-profile.json').read_text()),'Manufacturing profile copy differs')
    parts=json.loads((D/'review/design-netmap.json').read_text());fitted={v['Reference']:v for v in parts if v.get('LCSC') and not v.get('DNP')}
    native_rows=list(csv.DictReader((R/'assembly/JLC_CPL_NATIVE_AUDIT.csv').open()));supplier_rows=list(csv.DictReader((R/'assembly/JLC_CPL.csv').open()));source=D/'inputs/user-corrected-JLC_CPL.csv';over=json.loads((R/'assembly-cpl-overrides.json').read_text())
    for rows,label in [(native_rows,'native'),(supplier_rows,'supplier')]:
        check(len(rows)==len({v['Designator'] for v in rows})==79,label+' CPL count/uniqueness differs')
        check({v['Designator'] for v in rows}==set(fitted),label+' CPL references differ')
    check((R/'assembly/JLC_CPL.csv').read_bytes()==source.read_bytes(),'Supplier CPL bytes differ from user source')
    check(sha(source)==over['source_sha256']=='ed23023d67402462e10042c7a7e8467062def891a487c25afa7da5a2af2c00a2','User CPL hash differs')
    changes=[];nmap={r['Designator']:r for r in native_rows}
    for row in native_rows:
        ref=row['Designator'];f=fps[ref];x,y=ex(f.GetPosition());angle=f.GetOrientationDegrees()%360
        check([float(row['Mid X']),float(row['Mid Y']),float(row['Rotation'])]==[x,y,angle],ref+' native CPL pose differs')
        check(row['Layer']==('Bottom' if f.GetLayer()==p.B_Cu else 'Top'),ref+' native CPL side differs')
    for row in supplier_rows:
        n=nmap[row['Designator']]
        if n!=row:changes.append({'reference':row['Designator'],'before':n,'after':row})
    check(len(changes)==len(over['overrides'])==11,'CPL override count differs')
    for c,it in zip(changes,over['overrides']):check(c['reference']==it['reference'] and c['before']==it['baseline_native_cpl'] and c['after']==it['user_corrected_cpl'],'CPL override provenance differs')
    bom=list(csv.DictReader((R/'assembly/JLC_BOM.csv').open()));refs=[]
    for row in bom:
        rr=row['Designator'].split(',');refs+=rr;check(int(row['Quantity'])==len(rr),'BOM quantity differs')
        for ref in rr:
            q=fitted[ref];f=fps[ref]
            check(row['Comment']==row['Manufacturer Part Number']==q['MPN']==f.GetFieldByName('Manufacturer_Part_Number').GetText(),ref+' BOM MPN differs')
            check(row['LCSC Part #']==q['LCSC']==f.GetFieldByName('LCSC').GetText(),ref+' BOM LCSC differs')
            fpname=str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName())
            check(row['Footprint']==q['Footprint']==fpname,ref+' BOM footprint differs')
    check(len(bom)==35 and len(refs)==len(set(refs))==79 and set(refs)==set(fitted),'BOM SKU/reference census differs')
    facts['assembly']={'fitted_count':79,'sku_groups':35,'side_counts':dict(collections.Counter(r['Layer'] for r in native_rows)),'supplier_byte_sha256':sha(source),'overrides':11}

    fab=R/'single-board-gerbers'
    functions={'controller-F_Cu.gtl':'Copper,L1,Top','controller-In1_Cu.g1':'Copper,L2,Inr','controller-In2_Cu.g2':'Copper,L3,Inr','controller-In3_Cu.g3':'Copper,L4,Inr','controller-In4_Cu.g4':'Copper,L5,Inr','controller-B_Cu.gbl':'Copper,L6,Bot','controller-F_Mask.gts':'Soldermask,Top','controller-B_Mask.gbs':'Soldermask,Bot','controller-F_Paste.gtp':'Paste,Top','controller-B_Paste.gbp':'Paste,Bot','controller-F_Silkscreen.gto':'Legend,Top','controller-B_Silkscreen.gbo':'Legend,Bot','controller-Edge_Cuts.gm1':'Profile,NP'}
    check({f.name for f in fab.iterdir() if f.suffix not in ('.drl','.gbrjob')}==set(functions),'Unexpected Gerber file set')
    for name,ff in functions.items():
        txt=(fab/name).read_text();check('%TF.FileFunction,'+ff+'*%' in txt,name+' function differs')
        check('%FSLAX46Y46*%' in txt and '%MOMM*%' in txt and '%TF.SameCoordinates,Original*%' in txt,name+' coordinate convention differs')
        check(txt.rstrip().endswith('M02*'),name+' end marker missing')
    layerfiles={p.F_Cu:'controller-F_Cu.gtl',p.In1_Cu:'controller-In1_Cu.g1',p.In2_Cu:'controller-In2_Cu.g2',p.In3_Cu:'controller-In3_Cu.g3',p.In4_Cu:'controller-In4_Cu.g4',p.B_Cu:'controller-B_Cu.gbl'}
    padcounts={}
    for layer,name in layerfiles.items():
        got=collections.Counter(gerber_objects(fab/name)[0]);want=collections.Counter((f.GetReference(),pad.GetNumber() if layer in (p.F_Cu,p.B_Cu) else '',*ex(pad.GetPosition())) for f in b.GetFootprints() for pad in f.Pads() if pad.GetNumber() and pad.IsOnLayer(layer))
        check(got==want,name+' copper pad flash inventory/coordinates differ');padcounts[name]={'observed':sum(got.values()),'native':sum(want.values()),'missing':list((want-got).elements()),'extra':list((got-want).elements())}
    facts['copper_pad_flashes']=padcounts
    # Compare actual path primitives and native segment/arc centerline geometry.
    outline=gerber_objects(fab/'controller-Edge_Cuts.gm1')[1];native_edges=[]
    for g in b.GetDrawings():
        if g.GetLayer()!=p.Edge_Cuts:continue
        native_edges.append({'shape':int(g.GetShape()),'start':ex(g.GetStart()),'end':ex(g.GetEnd()),'center':ex(g.GetCenter()) if g.GetShape()==p.SHAPE_T_ARC else None})
    check(len(outline)==len(native_edges)==8,'Outline primitive count differs')
    def close(a,b):return a is not None and b is not None and max(abs(x-y) for x,y in zip(a,b))<=.000002
    for e in outline:
        matches=[n for n in native_edges if ((close(e['start'],n['start']) and close(e['end'],n['end'])) or (close(e['start'],n['end']) and close(e['end'],n['start']))) and ((e['center'] is None and n['center'] is None) or close(e['center'],n['center']))]
        check(len(matches)==1,'Outline primitive differs from native: '+str(e))
    facts['outline']={'gerber_paths':outline,'native_paths':native_edges,'nominal_bounds_mm':[0,0,38,38],'corner_radius_mm':2}

    wanted=[]
    for f in b.GetFootprints():
        for pad in f.Pads():
            if not pad.HasHole():continue
            s=pad.GetEffectiveHoleShape();wanted.append(feature(pad.GetAttribute()!=p.PAD_ATTRIB_NPTH,mm(s.GetWidth()),ex(s.GetSeg().A),ex(s.GetSeg().B)))
    for v in b.GetTracks():
        if isinstance(v,p.PCB_VIA):wanted.append(feature(True,mm(v.GetDrillValue()),ex(v.GetPosition())))
    drills=list(fab.glob('*.drl'));check(len(drills)==2,'Drill file count differs');got=collections.Counter(f for path in drills for f in drill_features(path));want=collections.Counter(wanted)
    check(got==want,'Drill diameter/plating/slot endpoint/coordinate inventory differs')
    facts['drills']={'count':sum(got.values()),'plated_count':sum(v for k,v in got.items() if k[0]),'nonplated_count':sum(v for k,v in got.items() if not k[0]),'slot_count':sum(v for k,v in got.items() if k[2]!=k[3]),'missing':list((want-got).elements()),'extra':list((got-want).elements())}

    job=json.loads((fab/'controller-job.gbrjob').read_text());js=job['GeneralSpecs'];check(js['LayerNumber']==6 and js['Size']=={'X':38.0,'Y':38.0} and js['BoardThickness']==1.5384,'Job board dimensions/stack count differ')
    check(js['Finish']=='ENIG' and js['ImpedanceControlled'] is True,'Job finish/impedance flags differ')
    check(js['ProjectId']['Revision']==b.GetTitleBlock().GetRevision(),'Job revision differs')
    jfiles=job['FilesAttributes'];check(len(jfiles)==13 and {v['Path'] for v in jfiles}==set(functions),'Job file inventory differs')
    aliases={'SolderMask':'Soldermask','SolderPaste':'Paste','Profile':'Profile,NP'}
    for item in jfiles:
        name=item['Path'];ff=item['FileFunction'];token,*rest=ff.split(',');canon=','.join([aliases.get(token,token)]+rest)
        check(canon==functions[name],'Job/Gerber layer assignment differs: '+name)
        check(item['FilePolarity']==('Negative' if name.endswith(('.gts','.gbs')) else 'Positive'),'Job polarity differs: '+name)
    for rule in job['DesignRules']:check(rule['TrackToTrack']==.16 and rule['MinLineWidth']==.13,'Job routing rule differs: '+rule['Layers'])
    stack=job['MaterialStackup'];copper=[v for v in stack if v['Type']=='Copper'];diels=[v for v in stack if v['Type']=='Dielectric'];check([v['Name'] for v in copper]==['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'],'Job copper stack order differs')
    check([v['Thickness'] for v in stack if v['Type'] in ('Copper','Dielectric')]==profile['layer_thickness_mm'],'Job dielectric/copper thickness differs')
    check([float(v['DielectricConstant']) for v in diels]==[4.1,4.6,4.16,4.6,4.1],'Job dielectric constants differ')
    facts['job']={'layer_mapping':{v['Path']:v['FileFunction'] for v in jfiles},'rules':job['DesignRules'],'size':js['Size'],'native_stack_matches':True}
    check(sha(boardpath)==h,'Native source changed during check')
except Exception as exc:
    errors.append(type(exc).__name__+': '+str(exc))
result={'status':'PASS INDEPENDENT FABRICATION CHECKS' if not errors else 'NOT PASSED','native_sha256':h,'export_manifest_sha256':sha(R/'SHA256_MANIFEST.json') if (R/'SHA256_MANIFEST.json').exists() else None,'errors':errors,'facts':facts,'scope':'Local artifact consistency. Does not clear supplier assembly warnings or qualify manufacture or hardware.'}
(O/'independent-fabrication-check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'native_sha256':h,'errors':errors,'report':str(O/'independent-fabrication-check.json')},indent=2));raise SystemExit(bool(errors))
