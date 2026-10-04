#!/usr/bin/python3
from pathlib import Path
import pcbnew as p,json,csv,hashlib
D=Path(__file__).resolve().parents[1];source=D/'review/printed-pad-legend.json'
if not source.exists():source=D.parent/'research/controller-r3s-stage16-silk-qa/precise-texts-and-pad-mapping.json'
base=json.loads(source.read_text());b=p.LoadBoard(str(D/'controller.kicad_pcb'))
def xy(v):return[p.ToMM(v.x),p.ToMM(v.y)]
def row(t):
 poly=p.SHAPE_POLY_SET();t.TransformTextToPolySet(poly,0,1000,p.ERROR_OUTSIDE);pts=[xy(poly.Outline(i).CPoint(j)) for i in range(poly.OutlineCount()) for j in range(poly.Outline(i).PointCount())];bb=[min(v[0] for v in pts),min(v[1] for v in pts),max(v[0] for v in pts),max(v[1] for v in pts)]
 return {'uuid':t.m_Uuid.AsString(),'text':t.GetText(),'side':'Bottom' if t.GetLayer()==p.B_SilkS else 'Top','native_anchor':xy(t.GetPosition()),'ink_bounds':bb,'ink_center':[(bb[0]+bb[2])/2,(bb[1]+bb[3])/2],'font_size':xy(t.GetTextSize()),'stroke_mm':p.ToMM(t.GetTextThickness()),'mirrored':t.IsMirrored()}
texts={t.m_Uuid.AsString():row(t) for t in b.GetDrawings() if isinstance(t,p.PCB_TEXT) and t.GetLayer() in [p.F_SilkS,p.B_SilkS]};assert len(texts)==69
fps={f.GetReference():f for f in b.GetFootprints()};pads=[]
for q in base['pad_mapping']:
 label=texts[q.get('label_uuid',q.get('physical_label_uuid'))];f=fps[q['reference']];pads.append({'reference':q['reference'],'net':next(f.Pads()).GetNetname() if False else list(f.Pads())[0].GetNetname(),'side':'Bottom' if f.GetLayer()==p.B_Cu else 'Top','native_position':xy(f.GetPosition()),'printed_text':label['text'],'label_uuid':label['uuid'],'label_native_anchor':label['native_anchor'],'shared_label_with':q.get('shared_label_with',q.get('shared_with'))})
assert len(pads)==67 and len({q['label_uuid'] for q in pads})==66
result={'status':'Actual native printed legend; full DRC and mask-clearance review required after final routing','native_sha256':hashlib.sha256((D/'controller.kicad_pcb').read_bytes()).hexdigest(),'physical_pad_label_count':66,'identified_pad_count':67,'board_legend_count':3,'shared_ground_label':'One G between the aligned J123/J133 pads identifies both; both are GND','power_legend':'5V=STACK identifies +5V_STACK, not battery-cell count; 3V3 is shared CORE budget','abbreviations':{'CR':'FDCAN1 controller RX, external transceiver required','CT':'FDCAN1 controller TX, external transceiver required','CL':'I2C SCL','DA':'I2C SDA','IN':'external sensor interrupt','MI':'SPI MISO','MO':'SPI MOSI','CK':'SPI SCK or SWCLK as defined by pad reference','DI':'SWDIO','RS':'NRST','BT':'BOOT0','VR':'3V3 VTREF','RM':'RPM','LD':'LED data','BZ':'buzzer control','C8':'PC8','C9':'PC9','14':'PD14','RN':'motor RUN, active high','OK':'motor healthy, active high'},'texts':list(texts.values()),'pad_mapping':pads};(D/'review/printed-pad-legend.json').write_text(json.dumps(result,indent=2))
with (D/'review/pad-wiring-map.csv').open('w',newline='') as f:
 fields=['Reference','Net','Printed label','Side','Native X mm','Native Y mm','Shared label with'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
 for q in pads:w.writerow(dict(zip(fields,[q['reference'],q['net'],q['printed_text'],q['side'],*q['native_position'],q['shared_label_with'] or ''])))
print('Actual69texts,66padlabels,67pad mappings exported')
