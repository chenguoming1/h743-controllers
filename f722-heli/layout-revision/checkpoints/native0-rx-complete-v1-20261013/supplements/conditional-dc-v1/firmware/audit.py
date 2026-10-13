"""Read-only stock-source/PCB pinmap audit. No native/geometry/solver execution."""
import argparse,gzip,hashlib,json,re,xml.etree.ElementTree as ET
from pathlib import Path
ap=argparse.ArgumentParser()
ap.add_argument('--checkpoint-root',type=Path,default=Path(__file__).resolve().parents[3])
ap.add_argument('--output',type=Path,help='Optional new receipt destination; default prints summary only.')
a=ap.parse_args()
OUT=Path(__file__).resolve().parent
CHECKPOINT=a.checkpoint_root.resolve()
PAIR=OUT/'inputs'
PCB=CHECKPOINT/'hardware/f722-heli.kicad_pcb'
CONTRACT=PAIR/'firmware-pinmap.json'
sha=lambda b:hashlib.sha256(b).hexdigest()
blob=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
assert sha((PAIR/'fresh-paired.net').read_bytes())=='2ca61314b02815a26f5d2bed0a60b09302448a2940f9c666665f422671e4cab8'
sourcechecks=json.loads((PAIR/'source-index.json').read_text())
for row in sourcechecks:
 b=(OUT/'sources'/row['file']).read_bytes()
 assert sha(b)==row['sha256'] and blob(b)==row['git_blob_sha1']
assert sha(PCB.read_bytes())=='84229c571433bd72d410fb18d02cffa3a380c00a87fbe1270e3a73b63f8dd6cd'
raw=gzip.decompress((CHECKPOINT/'native/after.native.json.gz').read_bytes())
assert sha(raw)=='04d8ecd80edf004f3226f204f23adba51692a498ae38edc183debeffb704603d'
native=json.loads(raw);del raw
native_pads={(x['ref'],x['number']):x['net'] for x in native['objects'] if x['kind']=='pad' and x['number']}
assert len([x for x in native['objects'] if x['kind']=='pad'])==558

def block(s,start):
 depth=0;quote=False;escape=False
 for i in range(start,len(s)):
  c=s[i]
  if escape:escape=False;continue
  if quote and c=='\\':escape=True;continue
  if c=='"':quote=not quote;continue
  if quote:continue
  if c=='(':depth+=1
  if c==')':
   depth-=1
   if depth==0:return s[start:i+1]
 raise AssertionError('unbalanced block')
text=PCB.read_text();board_pads={};physical_count=0
for m in re.finditer(r'\(footprint\s+"',text):
 fp=block(text,m.start());ref=re.search(r'\(property\s+"Reference"\s+"([^"]+)"',fp).group(1)
 for pm in re.finditer(r'\(pad\s+"([^"\n]*)"',fp):
  pad=block(fp,pm.start());num=pm.group(1);physical_count+=1
  nm=re.search(r'\(net\s+(?:\d+\s+)?"([^"]*)"\)',pad)
  if num:board_pads[(ref,num)]=nm.group(1) if nm else ''
assert physical_count==558
assert board_pads==native_pads
layers=block(text,text.index('(layers'))
copper=re.findall(r'\(\d+\s+"([^"\n]+\.Cu)"\s+signal\)',layers)
assert len(copper)==6

netroot=ET.parse(PAIR/'fresh-paired.net')
nodes={};netnodes={}
for net in netroot.findall('./nets/net'):
 name=net.attrib['name'];netnodes[name]=[]
 for n in net.findall('node'):
  key=(n.attrib['ref'],n.attrib['pin']);nodes[key]={'net':name,**n.attrib};netnodes[name].append('.'.join(key))
alias={'unconnected-(U13-I/O3-Pad4)':'unconnected-(U13-I{slash}O3-Pad4)'}
assert all(board_pads[k]==alias.get(v['net'],v['net']) for k,v in nodes.items())
gpio_to_pin={v['pinfunction'].split('_')[0]:k[1] for k,v in nodes.items() if k[0]=='U1' and v.get('pinfunction','').startswith(('PA','PB','PC','PD','PH'))}
contract=json.loads(CONTRACT.read_text());target=(OUT/'sources/RDMS-NEXUS_F7.config').read_text()
resources=[(r,int(i),g)for r,i,g in re.findall(r'^resource (\S+) (\d+) (\S+)',target,re.M)]
config_resources={(r,i):g for r,i,g in resources};checks=[]
for c in contract['checks']:
 r,i,g=c['resource'],c['index'],c['gpio'];pin=c['package_pin'];expected=c['expected_net']
 target_gpio='P'+config_resources[(r,i)][0]+str(int(config_resources[(r,i)][1:]))
 checks.append({**c,'target_gpio':target_gpio,'netlist_gpio':nodes[('U1',pin)]['pinfunction'].split('_')[0],'board_net':board_pads[('U1',pin)],'passed':target_gpio==g and gpio_to_pin[g]==pin and board_pads[('U1',pin)]==nodes[('U1',pin)]['net']==expected})
assert len(checks)==29 and all(c['passed']for c in checks)
all_resources=[]
for r,i,g in resources:
 row={'resource':r,'index':i,'target_pin':g}
 if g=='NONE':row['status']='disabled_in_target'
 else:
  gpio='P'+g[0]+str(int(g[1:]));pin=gpio_to_pin[gpio];net=board_pads[('U1',pin)]
  row.update(gpio=gpio,package_pin=pin,net=net,status='assigned_unconnected'if net.startswith('unconnected-')else 'mapped',same_net_nodes=netnodes[nodes[('U1',pin)]['net']])
 all_resources.append(row)
assert len([r for r in all_resources if r['status']=='assigned_unconnected'])==1

components={c.attrib['ref']:{'value':c.findtext('value'),'footprint':c.findtext('footprint')}for c in netroot.findall('./components/comp')}
connector_rows=[]
for r in ['J'+str(i)for i in range(1,13)]:
 connector_rows.append({'ref':r,**components[r],'pins':{k[1]:v['net'] for k,v in nodes.items() if k[0]==r}})
paths=[]
for j,r,net in [('J2','R20','SERVO1'),('J3','R21','SERVO2'),('J4','R22','SERVO3'),('J5','R23','TAIL'),('J6','R24','ESC'),('J12','R38','DSM_RX')]:
 assert nodes[(j,'3')]['net']==nodes[(r,'1')]['net']==net+'_EXT'
 assert nodes[(r,'2')]['net']==net+'_MCU'
 paths.append({'feature':net,'connector':j+'.3','series_element':r,'series_value':components[r]['value'],'from_net':net+'_EXT','to_net':net+'_MCU','topology_verified':True})
for letter,j,rx,tx in [('A','J9','R30','R31'),('B','J10','R32','R33'),('C','J11','R34','R35')]:
 for direction,pin,res in [('RX','1',rx),('TX','2',tx)]:
  prefix='PORT_'+letter+'_'+direction
  assert nodes[(j,pin)]['net']==nodes[(res,'1')]['net']==prefix+'_EXT'
  assert nodes[(res,'2')]['net']==prefix+'_MCU'
  paths.append({'feature':prefix,'connector':j+'.'+pin,'series_element':res,'series_value':components[res]['value'],'from_net':prefix+'_EXT','to_net':prefix+'_MCU','topology_verified':True})
for feature,j,r,q,end in [('RPM','J7','R25','Q1','R39'),('SBUS_PPM','J8','R26','Q2','R45')]:
 stem='SBUS'if feature=='SBUS_PPM'else feature
 assert nodes[(j,'3')]['net']==nodes[(r,'1')]['net']==stem+'_EXT'
 assert nodes[(r,'2')]['net']==nodes[(q,'3')]['net']==stem+'_HV'
 assert nodes[(q,'2')]['net']==nodes[(end,'1')]['net']==stem+'_LV'
 assert nodes[(q,'1')]['net']=='+3V3_CORE' and nodes[(end,'2')]['net']==stem+'_MCU'
 paths.append({'feature':feature,'connector':j+'.3','elements':[r,q,end],'nets':[stem+s for s in ['_EXT','_HV','_LV','_MCU']],'topology_verified':True,'runtime_direction_and_waveform_not_qualified':True})
device_endpoints=[]
for net,endpoint in [('IMU_CS',('U2','12')),('IMU_SCK',('U2','13')),('IMU_MISO',('U2','1')),('IMU_MOSI',('U2','14')),('IMU_INT',('U2','4')),('FLASH_CS',('U3','1')),('FLASH_SCK',('U3','6')),('FLASH_MISO',('U3','2')),('FLASH_MOSI',('U3','5')),('BARO_SCL',('U4','4')),('BARO_SDA',('U4','3'))]:
 assert nodes[endpoint]['net']==net
 device_endpoints.append({'net':net,'endpoint':'.'.join(endpoint),'same_net_nodes':netnodes[net],'verified':True})

r={'schema':'f722-native0-stock-firmware-replay/v1','pcb_sha256':sha(PCB.read_bytes()),'physical_pad_count':physical_count,'numbered_pad_map_entries':len(board_pads),'schematic_nodes':len(nodes),'copper_layers':copper,'contract_checks':checks,'all_target_resources':all_resources,'connector_pinmaps':connector_rows,'signal_paths':paths,'device_endpoint_checks':device_endpoints,'source_checks_passed':len(sourcechecks),'runtime_qualification':False}
if a.output:
 with a.output.open('x') as f:f.write(json.dumps(r,indent=2)+'\n')
print(json.dumps({'static_mapping_passed':True,'contract_rows':len(checks),'assigned_target_resources':sum(x['status']!='disabled_in_target'for x in all_resources),'physical_pads':physical_count,'numbered_pad_maps':len(board_pads),'schematic_nodes':len(nodes),'connector_paths':len(paths),'device_endpoints':len(device_endpoints),'copper_layers':len(copper),'runtime_qualified':False}))
