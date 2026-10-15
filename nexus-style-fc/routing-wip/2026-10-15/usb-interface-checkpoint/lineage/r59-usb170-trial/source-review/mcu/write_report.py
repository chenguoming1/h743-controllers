from candidate_check import *
from pathlib import Path
summary=json.loads((D/'mcu'/'clearance-summary.json').read_text())
report='''# MCU full-width terminal proposal: closed analytical candidate

This is a bounded read-only geometry proposal against accepted r57. No PCB, project, native routing, GitHub, or fabrication data was changed. The source hash remained `583e73ba08c80e70d42bfd726ef1b440ab0ddf4d7309cef266de486fd03f461f`.

## Integration result

- All replacement USB tracks are 0.150 mm. All new/moved vias are ordinary 0.450/0.200 mm through vias.
- U1.44 USB_DM remains (115.35,106.15); U1.45 USB_DP remains (115.85,106.15).
- In3.Cu handoff is DP (110.7615,110.85), DM (111.0385,110.85), running toward increasing y.
- IMPORTANT: the trunk's earlier proposed starts at y=110.60 must be trimmed to y=110.85. A DM vertical extension above the new handoff would collide with the DP via fanout. Keep the exact new fanout instead.
- All original USB tracks/vias are excluded from this transaction and must be replaced by the combined terminal/trunk/port proposal. Fixed USB pads remain clearance obstacles for the opposite net.
- Fixed GND vias/return traces and all power tracks remain unchanged.
- Two donor nets only: SWDIO and IMU_CS. FLASH_CS is unchanged.
- Zero analytic fixed-object or new-mutual violations at 0.127 mm copper clearance.

## Margin and qualifications

The fixed B_TX/GND via-center gate is 1.133616985 mm wide. Two 0.150 mm tracks with three 0.127 mm gaps and the two 0.225 mm via radii need 1.131 mm, leaving only 0.002616985 mm excess. The proposed tracks pass the two fixed vias at 0.127500147 mm copper gaps. This is a numerically compliant, very low-margin construction, not a manufacturing robustness claim.

Other nearest clearances: DP via to nominal C19.2 copper/paste bound 0.128035409 mm; DM fanout to FLASH_CS 0.129558705 mm; minimum new mutual clearance is the intended 0.127 mm handoff gap. Rounded-rectangle pads were conservatively treated as rectangles.

This is not native KiCad DRC, zone/refill, return-plane continuity, field-solver impedance, assembled solderability, or fabrication signoff. No arbitrary length or skew acceptance threshold was applied. Local copper centerline lengths to the handoff, excluding barrels: DM 7.858047702 mm; DP 7.797952063 mm; DM is 0.060095639 mm longer.

## Complete donor preservation

SWDIO: replace all five B.Cu terminal segments, its old via at (114.251387,108.48676), and the In3 tie `f4f94bae-80da-4eb4-bca1-2a090557d795`. New via is (114.251387,108.55). The replacement preserves the exact interfaces at U1.46 (116.35,106.15) and existing In3 segment `0a4ad166-9289-4ed4-b244-08e470c46176` at (114.191252,108.776284).

IMU_CS: replace only `91546caa-2776-4d18-a585-2372a009501f`, retaining exact interfaces (110.528858,109.112142) and (111.610503,110.264497), joining retained segments `d1ecbb59-89ae-47ce-83ac-59a4412dfd9f` and `071949d7-2ed8-412a-9603-f5db809d1dfc`.

Finite same-net copper-intersection screening found exactly those retained contacts before and after each donor transaction, no lost contacts, no added contacts, and a single connected replacement component per donor. No intermediate branch/contact is left open.

## Via and paste distinction

No new/moved via's annulus or drill intersects a nominal paste aperture. Nearest conservative nominal-paste gaps:
- USB_DM via (110.98,109.68): annulus 0.130000 mm, drill 0.255000 mm, C9.1 / C19.2 F.Paste.
- USB_DP via (110.972,110.34): annulus 0.128035 mm, drill 0.253035 mm, C19.2 F.Paste.
- SWDIO via (114.251387,108.55): annulus 0.245000 mm, drill 0.370000 mm, U3.4 F.Paste.

No explicit solder-paste margin overrides were found in the board/project. Nominal pad aperture geometry was screened, not exported stencil/Gerber geometry. Solder-mask expansion/tenting and fabrication tolerances still need the implementation-stage check.

## Exact replacement geometry

Coordinates in millimeters. Candidate JSON is authoritative for full segment endpoints and removal UUIDs.
'''
for net in ['USB_DM','USB_DP','SWDIO','IMU_CS']:
 report+='\n### '+net+'\n'
 for o in new:
  if o['net']!=net:continue
  if o['kind']=='via':report+='- Through via '+str(o['at'])+' diameter 0.450, drill 0.200\n'
  else:report+=f"- {o['layer']} {o['width']:.3f}: {o['start']} → {o['end']}\n"
report+='''
## Reproduce

Run `candidate_check.py`, `finalize.py`, and `donor_and_paste_check.py` from this directory. They parse only the accepted source and write numerical reports in this research directory. `candidate.json` includes all new objects and eight foreign removal UUIDs; `clearance-summary.json` contains nearest clearances and lengths; `donor-and-paste-summary.json` contains the retained-contact evidence.
'''
(D/'mcu'/'REPORT.md').write_text(report)
print(D/'mcu'/'REPORT.md')
