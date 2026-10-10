"""Verify pinned sources and bind this limited review to the final native handoff."""
import datetime
import hashlib
import json
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
CAND=ROOT/'ordinary-routing/tests/joint-flash-group/small-candidate01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
EXPECTED='14dea1df09ea9d800bf66a6d74eb5f0dac33a8705161e9ed1a02f2e11f3b58b8'
HANDOFF='31c2e16c27c8458734e7e46ae6bbb4f114ed3580552e45a3ffeae5601aa69fca'
NATIVE='694974b065fedf387f1b66c004f440cc138b0075549fd6383e18e595c139cc53'
handoff=read(CAND/'route-handoff.json')
assert sha(CAND/'route-handoff.json')==HANDOFF
assert sha(CAND/'f722-heli.kicad_pcb')==handoff['board_sha256']==EXPECTED
assert sha(CAND/'f722-heli.native.json')==handoff['native_sha256']==NATIVE
for name,expected in handoff['files'].items():
    assert sha(CAND/name)==expected, name
firmware=read(OUT/'new-firmware-sources.json')+[read(OUT/'hal-firmware-source.json')]
for row in firmware:
    p=ROOT/row['path'];data=p.read_bytes()
    assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==row['git_blob_sha1']
    row['sha256']=sha(p)
sources=[
 'ordinary-routing/tests/joint-flash-group/small-candidate01/f722-heli.kicad_pcb',
 'ordinary-routing/tests/joint-flash-group/small-candidate01/f722-heli.native.json',
 'ordinary-routing/tests/joint-flash-group/small-candidate01/route-handoff.json',
 'ordinary-routing/tests/joint-flash-group/small-candidate01/proposal.json',
 'ordinary-routing/tests/joint-flash-group/small-candidate01/construction-provenance.json',
 'ordinary-routing/tests/joint-flash-group/small-candidate01/parts.json',
 'ordinary-routing/candidate54/f722-heli.native.json',
 'ordinary-routing/candidate53/conditional-signal-review/stm32f7x2_lqfp64.ibs',
 'ordinary-routing/candidate53/conditional-signal-review/firmware/src/main/drivers/io.h',
 'ordinary-routing/candidate53/conditional-signal-review/firmware/src/main/drivers/io.c',
 'ordinary-routing/tests/green-electrical54/README.md',
 'ordinary-routing/tests/green-electrical54/source-index.json',
 'ordinary-routing/tests/green-electrical54/firmware/light_led.c',
 'stock-spi-review/RDMS-NEXUS_F7.config',
 'stock-spi-review/firmware/src/main/drivers/flash.c',
 'stock-spi-review/firmware/src/main/drivers/flash_w25n01g.c',
 'stock-spi-review/firmware/src/main/target/common_pre.h',
 'stock-spi-review/firmware/src/main/target/STM32_UNIFIED/target.h',
 'stock-spi-review/fetched-source-index.json',
 'stock-spi-review/sources/W25N01GV_DS-RevQ.pdf',
 'stock-spi-review/sources/W25N01GV_DS-RevQ.txt',
 'signal-review/STM32F722-DS11853-Rev9.pdf',
 'signal-review/STM32F722-DS11853-Rev9.txt',
 'signal-review/stock-ba6c7e3/src/main/startup/system_stm32f7xx.c',
 'independent-core-voltage-review/sources/adc_stm32f7xx.c',
 'independent-core-voltage-review/input-hashes.json',
 'independent-core-voltage-review/REPORT.md']
index={'schema':'f722-small-signal-review-source-index/v1','firmware_commit':'ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94',
 'target_commit':'1d9cb4dc6f85c7895c2b089f4b8aa776ca3d3bd3','new_firmware_files_git_blob_verified':firmware,
 'files':[{'path':p,'sha256':sha(ROOT/p)} for p in sources],
 'fresh_primary_web_reads':[
  {'url':'https://www.onsemi.com/download/data-sheet/pdf/esd9m5.0s-d.pdf','identity':'ESD9M5.0S/D, February2024 Rev9','pages':[2,4],'local_pdf_retained':False},
  {'url':'https://www.st.com/resource/en/datasheet/stm32f722re.pdf','identity':'DS11853 Rev9; saved PDF/text used for exact data','pages':[80,143,144,145,149,150]},
  {'url':'https://www.mouser.com/pdfDocs/W25N01GV_DS.pdf','identity':'Manufacturer-authored Winbond RevQ, May17 2021','pages':[10,58]},
  {'url':'https://www.analog.com/media/en/training-seminars/tutorials/mt-094.pdf','identity':'ADI MT-094 Rev0 Jan2009','equations':[4,6,8,10],'local_pdf_retained':False}],
 'limits':'Pinned component/source evidence and arithmetic. No external receiver identity, installed configuration, total capacitance, return impedance, ESD or bench qualification.'}
(OUT/'source-index.json').write_text(json.dumps(index,indent=2)+'\n')
arithmetic=read(OUT/'arithmetic.json')
assert arithmetic['board_sha256']==EXPECTED and arithmetic['sealed_native_handoff_sha256']==HANDOFF
assert arithmetic['checks']['native_recipe_records_exact'] and not arithmetic['qualified']
receipt={'schema':'f722-small-signal-review-receipt/v1','sealed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'board_sha256':EXPECTED,'native_sha256':NATIVE,'native_handoff_sha256':HANDOFF,
 'native_handoff_file_hashes_checked':len(handoff['files']),'all_native_handoff_file_hashes_match':True,
 'new_firmware_git_blob_hashes_checked':len(firmware),'source_bound_arithmetic_passed':True,
 'scope':'Conditional prototype electrical screen; only this directory written; no board/BOM/firmware/canonical edits.',
 'electrical_qualification_claimed':False,'parent_adoption_decision_separate':True,
 'files':{str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='review-receipt.json'}}
(OUT/'review-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='files'},indent=2))
