"""Verify typed support audit chains and emit a separate normalized proof.

Original source receipts are read without adding legacy fields. The pinned owner
adapter checks per-net predecessor UUID/group equality; this layer additionally
binds actual native bytes, the complete current pad inventory and dependencies.
"""
import copy,hashlib,json,sys
from pathlib import Path
from power_case_model import require,Refused
from owner_support_contract import verify as owner_verify

DSM='f722-complete-DSM-support-audit-binding/v1'
I2C='f722-I2C-complete-support-binding/v1'
LEGACY=(None,'f722-native-support-audit/v1')

def sha_bytes(value):return hashlib.sha256(value).hexdigest()

def verify_files(records):
    for name,expected in records.items():
        require(sha_bytes(Path(name).read_bytes())==expected,'Support dependency changed: '+name)

def verify_support(directory,native_path=None,report_path=None):
    require(sys.flags.optimize==0,'Support verification requires nonoptimized Python')
    directory=Path(directory).resolve();archive_root=directory.parent
    dependencies={};chain=[];active=set()

    def bound_bytes(path):
        path=Path(path).resolve()
        require(path.is_relative_to(archive_root),'Support evidence escapes selected archive root')
        value=path.read_bytes();digest=sha_bytes(value)
        require(str(path) not in dependencies or dependencies[str(path)]==digest,'Support evidence changed while reading')
        dependencies[str(path)]=digest
        return value

    def bound_json(path):
        try:return json.loads(bound_bytes(path))
        except (ValueError,OSError) as exc:raise Refused('Missing or invalid support evidence: '+str(path)) from exc

    def lookup_prior(expected_sha,source_board_sha):
        # Hash identity, not a guessed candidate number. Search only direct
        # candidate directories in the already selected routing archive.
        found=[]
        for p in sorted(archive_root.glob('candidate*/power-audit.json')):
            if p.parent.resolve()==directory:continue
            raw=p.read_bytes()
            if sha_bytes(raw)==expected_sha:
                row=json.loads(raw)
                if row.get('board_sha256')==source_board_sha:found.append(p.resolve())
        require(len(found)==1,'Expected one exact predecessor support receipt by SHA and board identity')
        return found[0]

    def visit(folder,selected_native=None,selected_report=None):
        folder=Path(folder).resolve();rp=Path(selected_report) if selected_report else folder/'power-audit.json'
        require(rp.resolve().parent==folder,'Support report must belong to selected source directory')
        require(str(rp.resolve()) not in active,'Cyclic support evidence chain')
        active.add(str(rp.resolve()))
        report=bound_json(rp);schema=report.get('schema')
        require(schema in (*LEGACY,DSM,I2C),'Unknown support-proof schema')
        board=folder/'f722-heli.kicad_pcb';board_sha=sha_bytes(bound_bytes(board))
        require(report.get('board_sha256')==board_sha and report.get('passed')is True,'Failed or stale support wrapper')
        np=Path(selected_native) if selected_native else folder/'owner-native.json'
        if not np.exists():np=folder/'f722-heli.native.json'
        require(np.resolve().parent==folder,'Native evidence must belong to selected source directory')
        native=bound_json(np);native_sha=dependencies[str(np.resolve())]
        require(native.get('board_sha256')==board_sha and native.get('source_unchanged')is True,'Native export is stale or mutating')
        nets=report.get('nets')
        require(isinstance(nets,dict) and nets,'Empty support net inventory')
        native_sets={}
        for p in native['objects']:
            if p['kind']=='pad' and p.get('number'):
                native_sets.setdefault(p.get('net'),[]).append(p['uuid'])
        prior=None;audit=None;ap=None
        if schema in LEGACY:
            require(report.get('native_sha256')==native_sha,'Legacy support/native byte binding differs')
        else:
            name=report.get('audit')
            require(isinstance(name,str) and Path(name).name==name and name not in ['','.','..'],'Unsafe typed audit basename')
            ap=folder/name;audit=bound_json(ap)
            require(dependencies[str(ap.resolve())]==report.get('audit_sha256'),'Typed nested audit hash differs')
            require(audit.get('passed')is True and audit.get('gates') and all(v is True for v in audit['gates'].values()),'Failed or empty typed audit gates')
            require(audit.get('source_board_sha256')==report.get('source_board_sha256'),'Typed predecessor board binding differs')
            if 'native_sha256' in report:
                require(report['native_sha256']==native_sha,'Typed wrapper/native byte binding differs')
            if schema==DSM:
                require(audit.get('schema')=='f722-dsm41-entry-return-audit/v1','Unknown nested DSM audit schema')
                require(audit.get('candidate_board_sha256')==board_sha and audit.get('support_nets')==nets,'DSM nested board/support inventory differs')
                hashes=audit.get('input_hashes',{})
                require(hashes.get(folder.name+'/f722-heli.kicad_pcb')==board_sha,'DSM nested candidate board hash differs')
                require(hashes.get(folder.name+'/f722-heli.native.json')==native_sha,'DSM nested candidate native hash differs')
                possible=[]
                for key,expected in hashes.items():
                    rel=Path(key)
                    if rel.name!='power-audit.json':continue
                    require(not rel.is_absolute() and len(rel.parts)==2 and '..' not in rel.parts,'Unsafe DSM predecessor receipt reference')
                    path=archive_root/rel
                    candidate=bound_json(path)
                    require(dependencies[str(path.resolve())]==expected,'DSM predecessor receipt hash differs')
                    if candidate.get('board_sha256')==report['source_board_sha256']:possible.append(path)
                require(len(possible)==1,'DSM predecessor receipt is missing or ambiguous')
                prior_path=possible[0]
            else:
                require(audit.get('schema')=='f722-I2C43-entry-support-audit/v1','Unknown nested I2C audit schema')
                require(audit.get('board_sha256')==board_sha and audit.get('nets')==nets,'I2C nested board/support inventory differs')
                require(audit.get('numerical_power_VCAP_applicable')is False,'I2C copper proof cannot claim numerical applicability')
                require(audit.get('candidate_native_sha256')==native_sha,'I2C nested native byte binding differs')
                expected=audit.get('source_power_audit_sha256')
                require(isinstance(expected,str) and len(expected)==64,'Missing I2C predecessor receipt hash')
                prior_path=lookup_prior(expected,report['source_board_sha256'])
            prior,prior_native,prior_native_sha=visit(prior_path.parent,selected_report=prior_path)
            if schema==I2C:
                require(audit.get('source_native_sha256')==prior_native_sha,'I2C predecessor native byte binding differs')
            else:
                require(hashes.get(prior_path.parent.name+'/f722-heli.kicad_pcb')==prior['board_sha256'],'DSM predecessor board byte binding differs')
                require(hashes.get(prior_path.parent.name+'/f722-heli.native.json')==prior_native_sha,'DSM predecessor native byte binding differs')
            try:owner_verify(report,prior,report['source_board_sha256'],board_sha,folder)
            except (AssertionError,KeyError,TypeError) as exc:raise Refused('Owner typed support UUID/group contract refused') from exc
        normalized={}
        for net,row in nets.items():
            groups=row.get('groups')
            require(isinstance(groups,list) and len(groups)==1,'Support net does not have exactly one proven group: '+net)
            if schema in LEGACY:
                require(row.get('pad_group_count')==1 and row.get('complete',True)is True,'Legacy support net is incomplete: '+net)
            else:
                require(row.get('passed')is True and row.get('source_groups_exactly_preserved')is True,'Typed support group preservation failed: '+net)
                if 'pad_group_count' in row:require(row['pad_group_count']==len(groups),'Typed group count contradicts actual groups')
            actual=groups[0].get('pad_uuids',[]);expected=native_sets.get(net,[])
            require(actual and len(actual)==len(set(actual)) and len(expected)==len(set(expected)) and set(actual)==set(expected),
                    'Support group differs from complete current native UUID inventory: '+net)
            normalized[net]={'pad_group_count':len(groups),'groups':copy.deepcopy(groups),
                             'proof_source':'Verified typed/legacy support evidence; normalized group count derived from checked groups',
                             'source_report_sha256':dependencies[str(rp.resolve())],'source_report_schema':schema}
        chain.append({'directory':str(folder),'schema':schema,'board_sha256':board_sha,'native_sha256':native_sha,
                      'support_report_sha256':dependencies[str(rp.resolve())],
                      'nested_audit_sha256':dependencies[str(ap.resolve())] if ap else None,'net_count':len(nets)})
        active.remove(str(rp.resolve()))
        if folder==directory:result.update(board_sha256=board_sha,native_sha256=native_sha,nets=normalized)
        return report,native,native_sha

    result={'schema':'f722-verified-support-connectivity/v1','passed':True,
            'normalization':'New derived connectivity proof; original receipts remain byte-unchanged and retain their real schemas.',
            'numerical_acceptance_claimed':False}
    visit(directory,native_path,report_path)
    verify_files(dependencies)
    result.update(evidence_files_sha256=dependencies,verified_chain=chain)
    return result

def select_approved_poses(source,mechanical,explicit=None):
    source=Path(source).resolve();expected=mechanical.get('input_hashes',{}).get('poses-native.json')
    require(isinstance(expected,str) and len(expected)==64,'Mechanical receipt lacks a pose digest')
    path=Path(explicit).resolve() if explicit else source/'poses-native.json'
    require(path.is_file(),'Source-local approved poses missing; supply an explicit mechanically bound pose file')
    require(sha_bytes(path.read_bytes())==expected,'Selected poses differ from source mechanical receipt')
    return path

def compile_connectivity(native,critical,support,networks):
    """Select checked support rows or exact critical-pad proofs for new rails."""
    require(native['board_sha256']==support['board_sha256']==critical['board_sha256'],'Connectivity source boards differ')
    critical_nets={row['net']:row for row in critical['fullnet_connectivity']}
    result={'board_sha256':native['board_sha256'],
            'normalization':'Typed support receipts verified with owner UUID/group contract; absent rail nets require exact critical native-pad proof.',
            'nets':{}}
    for network in networks:
        net=network['net']
        objects=[p for p in native['objects'] if p['kind']=='pad' and p.get('net')==net and p.get('number')]
        row=support['nets'].get(net)
        if row is None:
            proof=critical_nets.get(net,{})
            require(proof.get('complete')is True and not proof.get('unreached') and set(proof.get('pads',[]))=={p['key'] for p in objects},
                    'Missing exact critical connectivity proof: '+net)
            row={'pad_group_count':1,'groups':[{'pad_uuids':[p['uuid'] for p in objects]}],
                 'proof_source':'Critical complete native pad-key set resolved against the same board/native export'}
        require(row['pad_group_count']==len(row['groups'])==1,'Normalized connectivity group mismatch: '+net)
        uuids=[u for group in row['groups'] for u in group['pad_uuids']]
        require(len(uuids)==len(set(uuids)) and set(uuids)=={p['uuid'] for p in objects},'Normalized native pad UUID mismatch: '+net)
        result['nets'][net]=copy.deepcopy(row)
    return result
