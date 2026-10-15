"""Read-only native-text proposal. No PCB writes, native jobs or source mutation."""
from pathlib import Path
import json,hashlib,sys,uuid,copy
sys.dont_write_bytecode=True
BASE=Path('/workspace/scratch/8a35c1f26232');OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE/'nexus-header-redesign-20261015/candidate-02/nexus-style-fc/tools'));import sexpr as s
SOURCE=BASE/'nexus-recovery-20261015/mechanical-integration/initial-native/hardware/header-board/nexus-header-board.kicad_pcb'
SOURCE_HASH='de56d5e4a066ff03a8c16d7e0501f45ca651ebf177c45ba12667488162010f38'
raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_HASH
b=s.parse(raw.decode())
def one(n,k):return s.find(n,k)[0]
def uid(n):return s.text(one(n,'uuid')[1])
def net(n):return s.text(one(n,'net')[-1])
def xy(n,k):return [float(v) for v in one(n,k)[1:3]]
def ref(f):return next(s.text(p[2]) for p in s.find(f,'property') if s.text(p[1])=='Reference')
segments={uid(n):n for n in s.find(b,'segment')}
plans=[
 ('VX',['231b7cbd-70f5-429b-b94b-faef2b63c3af','ca788c04-a07c-422b-824f-dbeafc220a25'],[[113.5022,107.9983],[113.654,108.1501],[113.654,109.573]],'T2'),
 ('S1',['1311c86b-1e8c-4833-8518-864755ff334c','a189ef97-eaa6-4497-8a33-d897ace91f54'],[[101.3,104.3017],[102.254,105.2557],[102.254,109.573]],'P1'),
 ('SBUS',['66d19cc4-5711-4d71-8657-ceebbea5c7b9'],[[121.1,103.3],[120.3,104.1],[120.3,109.573],[120.146,109.573]],'P7'),
 ('GND',['cbf85f81-7873-4ccf-8b3d-ddc0f3494041'],[[109.7,107.14],[108.746,108.094],[108.746,109.573]],'T1')]
NS=uuid.UUID('ed005c0f-4bdc-4c8e-bbbc-1c1a78f5323a');result=[]
for nn,ids,points,target in plans:
    donors=[segments[u] for u in ids];widths={float(one(x,'width')[1]) for x in donors};assert len(widths)==1
    w=widths.pop();assert w==(.5 if nn in ('VX','GND') else .2)
    new=[]
    for i,(a,c) in enumerate(zip(points,points[1:])):
        n=copy.deepcopy(donors[min(i,len(donors)-1)]);u=ids[i] if i<len(ids) else str(uuid.uuid5(NS,f'{nn}-{i}'))
        one(n,'start')[1:3]=[f'{z:.6f}'.rstrip('0').rstrip('.') for z in a];one(n,'end')[1:3]=[f'{z:.6f}'.rstrip('0').rstrip('.') for z in c];one(n,'uuid')[1]=('s',u)
        new.append({'uuid':u,'start':a,'end':c,'width':w,'layer':'B.Cu','net':nn,'native_record':s.dump(n)})
    f=next(f for f in s.find(b,'footprint') if ref(f)==target);pad=one(f,'pad');center=[sum(v) for v in zip(xy(f,'at'),xy(pad,'at'))];assert points[-1]==[round(v,6) for v in center]
    result.append({'net':nn,'original_width_mm':w,'source_donor_segments':[{'uuid':uid(n),'native_record':s.dump(n),'start':xy(n,'start'),'end':xy(n,'end')} for n in donors],'replacement_segments':new,'retained_upstream_port':{'point':points[0],'layer':'B.Cu'},'terminal_port':{'reference':target,'pad_number':s.text(pad[1]),'pad_uuid':uid(pad),'center':center,'size':xy(pad,'size'),'layer':'B.Cu','new_endpoint':points[-1],'full_width_endpoint_inside_pad':True}})
proposal={'status':'UNFINISHED read-only full donor-route proposal; not applied or native-validated','source':{'path':str(SOURCE),'sha256':SOURCE_HASH},'scope':'Replace exactly six B.Cu donor segments with nine segments at original widths. No vias, footprints, pads, mask, contours, rules, schematic, or retained copper changes. Zone refill required in native lane.','routes':result,'expected_segment_count_before':len(segments),'expected_segment_count_after':len(segments)-6+9,'native_gates':['source/hash and exact UUID/record guard','complete route replacement preserving all external copper ports','zone refill','native child all-visible DRC/ERC/parity with unchanged floors','zero opens/shorts/edge violations; keep filter/courtyard advisories visible']}
(OUT/'complete-transaction.json').write_text(json.dumps(proposal,indent=2)+'\n')
# Complete four-net inventory including all physical pads and every retained segment/via.
nets={r['net'] for r in result};inventory={}
for nn in sorted(nets):
    pads=[]
    for f in s.find(b,'footprint'):
        for p in s.find(f,'pad'):
            if s.find(p,'net') and net(p)==nn:
                pads.append({'ref':ref(f),'pad':s.text(p[1]),'uuid':uid(p),'center':[sum(v) for v in zip(xy(f,'at'),xy(p,'at'))],'size':xy(p,'size'),'shape':s.text(p[3]),'layers':[s.text(v) for v in one(p,'layers')[1:]],'native_record':s.dump(p)})
    inventory[nn]={'pads':pads,'segments':[{'uuid':uid(n),'native_record':s.dump(n)} for n in segments.values() if net(n)==nn],'vias':[{'uuid':uid(n),'native_record':s.dump(n)} for n in s.find(b,'via') if net(n)==nn]}
(OUT/'complete-net-inventory.json').write_text(json.dumps({'source_sha256':SOURCE_HASH,'nets':inventory},indent=2)+'\n')
print(json.dumps({'source':SOURCE_HASH,'donors':6,'replacements':9,'affected_net_pads':sum(len(v['pads']) for v in inventory.values())}))
