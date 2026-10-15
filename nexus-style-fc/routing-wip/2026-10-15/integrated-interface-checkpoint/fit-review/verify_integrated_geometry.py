"""Read-only source-bound check of the sole lane's integrated output; no native calls."""
from pathlib import Path
import ast,copy,hashlib,json,sys
O=Path(__file__).parent
S=json.loads((O/'slot101x220-source-guarded-spec.json').read_text())
P=Path(S['source_project']);Q=Path(sys.argv[1])
sys.path.insert(0,str(P/'tools'));import sexpr as s
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def one(n,k):return s.find(n,k)[0]
def uid(n):return s.text(one(n,'uuid')[1])
def ref(n):return next(s.text(p[2]) for p in s.find(n,'property') if s.text(p[1])=='Reference')
def norm(n):
    if isinstance(n,tuple):return ['quoted',n[1]]
    if isinstance(n,list):return [norm(x) for x in n]
    try:return round(float(n),6)
    except (ValueError,TypeError):return n
def edge(n):return isinstance(n,list) and n and n[0] in ('fp_line','fp_arc','gr_line','gr_arc') and s.text(one(n,'layer')[1])=='Edge.Cuts'
def edge_sig(n):return tuple([n[0]]+[tuple(round(float(x),6) for x in one(n,k)[1:3]) for k in (('start','mid','end') if n[0].endswith('_arc') else ('start','end'))])
for f,h in S['source_sha256'].items():assert sha(P/f)==h
files=['hardware/nexus-style-fc.kicad_pcb','hardware/header-board/nexus-header-board.kicad_pcb','hardware/nexus-style-fc.kicad_sch','hardware/header-board/nexus-header-board.kicad_sch','hardware/library/NexusFC.3dshapes/nexus-header-board-root-relief-candidate.wrl']
before={f:sha(Q/f) for f in files}
a=s.parse((P/files[0]).read_text());b=s.parse((Q/files[0]).read_text())
af={ref(f):f for f in s.find(a,'footprint')};bf={ref(f):f for f in s.find(b,'footprint')}
want=copy.deepcopy(af['J1'])
for c in S['edge_changes']:
    n=next(x for x in want if isinstance(x,list) and s.find(x,'uuid') and uid(x)==c['uuid']);assert s.dump(n)==c['old_native_record'];want[want.index(n)]=s.parse(c['new_native_record'])
one(want,'descr')[1]=('s',s.text(one(want,'descr')[1]).replace('10.0 x 2.1','10.1 x 2.2'))
tests={'all_other_footprints_exact_geometry':set(af)==set(bf) and all(norm(af[r])==norm(bf[r]) for r in af if r!='J1'),'J1_only_16_edges_and_description_changed':norm(want)==norm(bf['J1']),'all_11_J1_pads_unchanged':norm(s.find(af['J1'],'pad'))==norm(s.find(bf['J1'],'pad')),'J1_model_transform_unchanged':norm(s.find(af['J1'],'model'))==norm(s.find(bf['J1'],'model')),'outer_body_unchanged':norm([n for n in a if edge(n)])==norm([n for n in b if edge(n)]),'thickness_unchanged':norm(s.find(a,'general'))==norm(s.find(b,'general')),'setup_rules_unchanged':norm(s.find(a,'setup'))==norm(s.find(b,'setup'))}
for c in S['keepout_changes']:
    z=next(z for z in s.find(b,'zone') if uid(z)==c['uuid']);tests['keepout_'+c['uuid']]=norm(z)==norm(s.parse(c['new_native_record']))
for f in files[1:]:tests[f+'_byte_unchanged']=before[f]==S['source_sha256'][f]
# Check library geometry and every unaffected library field against guarded old source.
f='hardware/library/NexusFC.pretty/HeaderBoard_Joint.kicad_mod';old=s.parse((P/f).read_text());new=s.parse((Q/f).read_text());expected=copy.deepcopy(old)
for c in S['edge_changes']:
    sig=edge_sig(s.parse(c['old_native_record']));target=next(n for n in expected if edge(n) and edge_sig(n)==sig);proposed=s.parse(c['new_native_record'])
    for key in ('start','mid','end'):
        if s.find(proposed,key):one(target,key)[1:]=one(proposed,key)[1:]
one(expected,'descr')[1]=('s',s.text(one(expected,'descr')[1]).replace('10.0 x 2.1','10.1 x 2.2'))
tests['library_exact_bounded_edit']=norm(expected)==norm(new)
tests['native_library_slot_geometry_agree']=sorted(edge_sig(n) for n in new if edge(n))==sorted(edge_sig(n) for n in bf['J1'] if edge(n))
tools={}
for f,replacements in S['source_text_replacements'].items():
    text=(P/f).read_text()
    for old,new in replacements:assert old in text;text=text.replace(old,new)
    tools[f]={'expected_sha256':hashlib.sha256(text.encode()).hexdigest(),'actual_sha256':sha(Q/f),'exact_proposed_text':(Q/f).read_text()==text}
    compile((Q/f).read_text(),str(Q/f),'exec')  # Syntax only, no execution.
# The shared constants must have exactly the proposed dimensions and unchanged other assignments.
def constants(path):
    return {ast.unparse(n.targets[0]):ast.literal_eval(n.value) for n in ast.parse(path.read_text()).body if isinstance(n,ast.Assign)}
g=constants(Q/'tools/header_interface_geometry.py');tests['shared_slot_dimensions']=g['(SLOT_LENGTH, SLOT_WIDTH, SLOT_RADIUS, ROOT_RADIUS)']==(10.1,2.2,.5,.5);tests['shared_keepout_offsets']=g['(SLOT_ROUTE_KEEPOUT_X, SLOT_ROUTE_KEEPOUT_Y)']==(.45,.3)
for f,h in before.items():assert sha(Q/f)==h
out={'source_project':str(P),'reviewed_output':str(Q),'source_main_sha256':S['source_sha256'][files[0]],'output_sha256':before,'tests':tests,'source_tool_checks':tools,'all_geometry_checks_pass':all(tests.values()),'scope':'Numeric spelling rounded to native 1nm only; quoted strings, UUIDs, pad/net/model/body/connectors and all unaffected fields remain compared. No native DRC/refill/solid renderer or physical test. Tool text differences require explicit review rather than automatic rejection when additional approved comments/guards exist.'}
dest=O/(Q.name+'-integrated-geometry-binding.json');dest.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
