"""Main-only TI TPS70933DBVR land variant. Does not edit the generic source.
Use generate(Path(hardware_dir)/'library/NexusFC.pretty') from the main build hook.
TI DBV0005A example lands: .60x1.10, row Y±1.30, pitch .95, corner radius .05.
Courtyard Y±2.00 deliberately retains the project's ~.15 mm dense-layout margin.
It is not an IPC .25 mm courtyard or a qualified placement-tolerance envelope.
"""
from pathlib import Path
import re,sys,hashlib
NAME='TPS70933DBVR_TI_DBV0005A'
SOURCE='SOT-23-5_L3.0-W1.7-P0.95-LS2.8-BL'
def generate(libdir):
 libdir=Path(libdir);p=libdir/(SOURCE+'.kicad_mod');s=p.read_text()
 assert s.startswith('(module '+SOURCE+' ')
 s=s.replace('(module '+SOURCE+' ','(module '+NAME+' ',1)
 s=s.replace('(descr "ME6211C33M5G-N")','(descr "TPS70933DBVR C89347; TI DBV0005A example lands; dense 0.15 mm vertical courtyard margin")',1)
 s=s.replace('(fp_text value '+SOURCE+' ','(fp_text value TPS70933DBVR ',1).replace('(property "LCSC Part" "C82942")','(property "LCSC Part" "C89347")',1)
 for num in range(1,6):
  pattern=rf'\(pad {num} smd rect \(at ([^ ]+) ([^ ]+) 0\.00\) \(size [^)]*\) \(layers F\.Cu F\.Paste F\.Mask\)\)'
  m=re.search(pattern,s);assert m,(num,p)
  x=float(m[1]);y=1.3 if float(m[2])>0 else -1.3
  s=s[:m.start()]+f'(pad {num} smd roundrect (at {x:g} {y:g} 0.00) (size 0.6 1.1) (layers F.Cu F.Paste F.Mask) (roundrect_rratio 0.08333333333))'+s[m.end():]
 # Exact inherited courtyard, with vertical margin retained for the longer outer extent.
 s=s.replace('-1.887','-2.00').replace('1.878','2.00')
 target=libdir/(NAME+'.kicad_mod')
 if target.exists():assert target.read_text()==s,('Refusing to overwrite a different variant',target)
 else:target.write_text(s)
 return target
if __name__=='__main__':print(generate(Path(sys.argv[1])))
