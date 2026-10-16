#!/usr/bin/env python3
"""Guarded, byte-bounded successor-only DFM patch. No native save or zone refill.
Usage: python apply_dfm_leaf_and_sw_fix.py SOURCE.kicad_pcb NEW_TARGET.kicad_pcb
Only the exact sealed stage32 or accepted stage33 source hashes are accepted.
"""
import hashlib,json,re,sys,uuid
from pathlib import Path
HASHES={
 'f214f8141e8f21a7e0983c8eb4f2be89634e3b69d0d2b168a1ac3153f28a83de':'sealed-stage32',
 '1fff67ee301156ef1e05809bcd92ea15d70c0094468adc84d4b6917bac405efe':'accepted-stage33',
}
REMOVE={
 '0adcb4a0-b0fe-4b49-b244-d914acbab1ce':'6a137c9d1f0732e4de8370c8511366c5a725086d39744864d55463c62a2da40f',
 '89e5d93a-cc40-522e-be96-8c2063593c4c':'3a09b1e09309bd1566796d6218513d752d0bf9176ddd2a58ca7aba540080be65',
 'adb7bb4c-38a5-57ec-bbe5-a8d40e92e278':'f034b35070cc3151d6226e1c408db2bd9329ad9be246cacc9f13e0a6d5879b7d',
 '8b59c581-e91f-406b-9384-8355a01b2e0a':'7c3b19424218e3a317ee35e6f91bf3411449d65c0e3633f1a7273d6e4415fb2f',
 'a15c473b-2f9d-4005-9cb7-441f047b496c':'a31e08be60a15be8f8b9bb342e17b1e2024f0f40578669d996dd185934348fde',
 'f2afd7f2-fa48-4d3a-9ad6-69bdbf939294':'12ca7e6fa2dee75a7c61fc3125cb6ff528d0ad71a2dd7905f6092d5fb7a5bf21',
}
SW='fc0e48be-4a94-43ae-8736-78e983b4a763'
SWHASH='aa00491bcd82d75d69c179cef945dcb97614e9a4f30e308b013f7b6a74481ddd'
NEW=str(uuid.uuid5(uuid.NAMESPACE_URL,'nexus-style-fc/stage34/U5.2-mask-sliver/short-vertical-then-diagonal/v2'))
sha=lambda x:hashlib.sha256(x).hexdigest()
def patch(source,target):
 source=Path(source).resolve();target=Path(target).resolve()
 assert source!=target and not target.exists(),'Target must be a new isolated file'
 assert not any('checkpoint' in x or x in ['stage32','stage33'] for x in target.parts),'Sealed or accepted stage targets forbidden'
 raw=source.read_bytes();h=sha(raw);assert h in HASHES,f'Unexpected source SHA-256: {h}'
 s=raw.decode();blocks={}
 for m in re.finditer(r'(?m)^\t\((?:segment|via)\n.*?^\t\)',s,re.S):
  u=re.search(r'\(uuid "([^"]+)"\)',m[0]).group(1)
  assert u not in blocks;blocks[u]=m
 assert NEW not in s
 for u,want in {**REMOVE,SW:SWHASH}.items():assert u in blocks and sha(blocks[u][0].encode())==want,f'Changed item {u}'
 old=blocks[SW][0]
 assert old.count('(end 102.6 111.675)')==1
 first=old.replace('(end 102.6 111.675)','(end 103.55 110.65)')
 diagonal='\t(segment\n\t\t(start 103.55 110.65)\n\t\t(end 102.6 111.675)\n\t\t(width 0.25)\n\t\t(layer "B.Cu")\n\t\t(net "SW_5V")\n\t\t(uuid "'+NEW+'")\n\t)'
 edits=[(blocks[u].start(),blocks[u].end()+1,'',u) for u in REMOVE]
 edits.append((blocks[SW].start(),blocks[SW].end(),first+'\n'+diagonal,SW))
 result=s
 for a,z,replacement,u in sorted(edits,reverse=True):result=result[:a]+replacement+result[z:]
 # Exact untouched text outside the seven authorized original objects is unchanged.
 stripped_before=s;stripped_after=result
 for u in REMOVE:stripped_before=stripped_before.replace(blocks[u][0]+'\n','',1)
 stripped_before=stripped_before.replace(old,'',1)
 stripped_after=stripped_after.replace(first+'\n'+diagonal,'',1)
 assert stripped_before==stripped_after,'Unexpected nonlocal edit'
 assert sha(source.read_bytes())==h,'Source changed during patch'
 target.parent.mkdir(parents=True,exist_ok=True)
 with target.open('xb') as f:f.write(result.encode())
 receipt=dict(source=str(source),source_sha256=h,source_class=HASHES[h],target=str(target),target_sha256=sha(target.read_bytes()),removed_uuids=sorted(REMOVE),modified_uuid=SW,added_uuid=NEW,old_path_mm=[[103.55,110.15],[102.6,111.675]],new_path_mm=[[103.55,110.15],[103.55,110.65],[102.6,111.675]],width_mm=.25,layer='B.Cu',net='SW_5V',unchanged_text_outside_authorized_objects=True,all_footprints_pads_nets_rules_mask_paste_settings_unchanged=True,saved_zone_fill_copied_requires_successor_native_refill=True)
 rp=target.with_suffix('.dfm-delta.json');assert not rp.exists();rp.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':
 assert len(sys.argv)==3,__doc__
 patch(sys.argv[1],sys.argv[2])
