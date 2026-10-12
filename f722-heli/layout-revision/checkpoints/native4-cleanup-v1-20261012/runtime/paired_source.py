"""Exact paired netlist and 558-pad verification helpers."""
import hashlib, json, gzip, lzma
from pathlib import Path
import xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
SOURCE=ROOT/'inputs/source-hardware'
SOURCE_XML=ROOT/'inputs/source-paired.net'
SOURCE_XML_SHA='4b364b3bdc0d04a078441c96326e2e1a181accf9e21da0c29c0313d00bf1a38b'


def require(ok,message):
    if not ok:raise ValueError(message)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1048576),b''):h.update(chunk)
    return h.hexdigest()


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def read(path):
    def pairs(rows):
        out={}
        for key,value in rows:
            require(key not in out,'Duplicate JSON key');out[key]=value
        return out
    def invalid(value):raise ValueError('Nonfinite JSON value')
    return json.loads((lzma.open(path,'rt').read() if str(path).endswith('.xz') else gzip.open(path,'rt').read() if str(path).endswith('.gz') else Path(path).read_text()),object_pairs_hook=pairs,parse_constant=invalid)


def write(path,value):
    with Path(path).open('x') as stream:json.dump(value,stream,sort_keys=True,separators=(',',':'),allow_nan=False);stream.write('\n')


def xml_shape(node):return [node.tag,dict(sorted(node.attrib.items())),(node.text or '').strip(),[xml_shape(x) for x in node]]


def netlist_model(data):
    root=ET.fromstring(data);nets={};codes=set();assigned=set()
    for net in root.findall('./nets/net'):
        name=net.get('name');code=net.get('code')
        require(name not in nets and code is not None and code.isdecimal() and int(code)>0 and int(code) not in codes,'Invalid net-name/code bijection')
        codes.add(int(code));nodes=[]
        for node in net.findall('node'):
            identity=(node.get('ref'),node.get('pin'));require(all(identity) and identity not in assigned,'Duplicate/missing assigned node')
            assigned.add(identity);nodes.append(dict(node.attrib))
        nets[name]={'attributes':{k:v for k,v in net.attrib.items() if k not in ['name','code']},'nodes':sorted(nodes,key=lambda x:(x['ref'],x['pin']))}
    comps=root.find('components');libs=root.find('libparts')
    require(comps is not None and libs is not None and len(comps)==156 and len(nets)==127 and len(assigned)==506,'Full source netlist inventory differs')
    return {'nets':nets,'components':xml_shape(comps),'libparts':xml_shape(libs)}


def verify_netlist_and_pads(source_xml,candidate_xml,native):
    expected=netlist_model(source_xml);actual=netlist_model(candidate_xml)
    require(actual==expected,'Complete source netlist identities or semantics changed')
    assigned={n['ref']+'.'+n['pin']:name for name,row in actual['nets'].items() for n in row['nodes']}
    pads=[r for r in native['objects'] if r['kind']=='pad'];require(len(pads)==558 and len({r['uuid'] for r in pads})==558,'Full native pad inventory differs')
    physical={}
    for pad in pads:
        if pad['number'] and pad['net']:
            require(pad['key'] not in physical or physical[pad['key']]==pad['net'],'Repeated physical pin net conflict');physical[pad['key']]=pad['net']
    # Sole exact historical alias, identical to source checkpoint's parity proof.
    alias={'key':'U13.4','pcb':'unconnected-(U13-I{slash}O3-Pad4)','schematic':'unconnected-(U13-I/O3-Pad4)'}
    require(physical.get(alias['key'])==alias['pcb'] and assigned.get(alias['key'])==alias['schematic'],'Historical U13 alias changed')
    physical[alias['key']]=alias['schematic']
    require(physical==assigned,'Full 558-pad/506-node parity differs')
    return {'full_netlist_pad_parity_passed':True,'components':156,'assigned_nodes':506,'physical_pads':558,'nets':127,'complete_expected_netlist_sha256':digest(expected),'all_component_library_identities_exact':True,'only_existing_alias':alias,'all_logical_pin_assignments_unchanged':True}


def verify_pad_nets(before,after):
    def pads(data):
        rows=[r for r in data['objects'] if r['kind']=='pad']
        result={r['uuid']:{k:r[k] for k in ['key','ref','number','net']} for r in rows}
        require(len(rows)==len(result)==558,'Exact 558 pad UUID inventory required')
        return result
    original,current=pads(before),pads(after)
    require(original==current,'Pad UUID/key/reference/number/net assignment changed')
    return {'all_558_pad_net_assignments_unchanged':True,'pad_identity_net_map_sha256':digest(current)}

