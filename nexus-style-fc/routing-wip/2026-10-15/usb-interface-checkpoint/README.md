# Experimental routing checkpoint: 8 clearance errors, unfinished

**Do not fabricate, assemble or fly from this checkpoint.** This successor preserves the accepted routing experiment and a separate, incomplete mechanical redesign. Canonical source is unchanged.

## Exact files and checks

- [Current experimental project](lineage/r60-r4-r18/hardware/nexus-style-fc.kicad_pro), board SHA256 `db583aaa5a1c2ddac33e42a174bd614504dc21b86b953bd0ec93d8360903f4b8`.
- [Current native DRC](lineage/r60-r4-r18/native-drc.json), [verification](lineage/r60-r4-r18/verification.json), and all-visible diagnostic in that directory.
- [USB source and complete evidence](lineage/r59-usb170-trial/README.md).
- [Fresh unchanged schematic PDF](../../../docs/schematic-main.pdf), schematic SHA256 `5e964b66b1bf4aa02caf87b678fc725b82ed688d0050609746a029eba928f101`.

Native KiCad 10.0.7 refill/save/DRC reports **8 clearance errors, zero opens and zero electrical/footprint-filter parity findings**. Minimum remaining gap is **0.0927 mm**. The exact unchanged schematic retains its source-bound native ERC 0 receipt. All-visible diagnostics expose 13 off-center, five footprint-type and 54 silk warnings. No new or worsened residual clearance pair, DRC exclusion or fresh severity suppression is accepted. Counts remain settings-bound, with the separate all-visible report retained.

## Progress since published r57

1. **r58:** Four 5V_BUCK donor entries are centered and their complete finite annular contacts proved. Inherited 0.375/0.500 mm widths and all seven external ports remain. These four centering warnings disappear; full-width ground reference outside the existing via-transition openings is retained. U5 current/thermal and VOS topology qualification remain open.
2. **r59:** Complete USB pair/protection topology is rerouted with 0.170 mm In3 trunks, 0.150 mm terminal launches and four explicit solid copper tapers. This is a documented width change, not an inherited width-preservation claim. All three USB clearance errors disappear. Both connector orientations, all five physical pads per USB net, both U7 external-pad bridges and MCU contacts are physically connected; bridge-cut tests exclude reliance on unspecified internal chip conductivity. All changed donor ports and untouched contacts are proved. Actual In3 Gerber contains the four solid tapers; front/back mask and paste apertures are unchanged, and seven new/replacement holes clear actual aperture bounds. These exports are diagnostic, not release CAM.

3. **r60:** R4's isolated LED-only terminal branch uses an explicit two-track 0.150 mm width exception instead of 0.350 mm. Complete topology proves no shared supply load passes through the narrowed branch; the documented resistor/current calculation supports this local choice. R18's sense-only 0.350 mm branch is rerouted partly on thinner inner copper, with its approximately 161 uA divider load and cross-section tradeoff explicit. Shared supply feeds are retained. Both changes have fresh complete-port, annular, return and native checks.

All accepted batches are listed in [the exact lineage](lineage-verification.json), each with its own source-bound transaction, width exceptions, native receipts and finite-contact checks. Original canonical PCB `925642c3...` remains at 627 inherited errors and is not silently replaced by this experimental board.

## USB acceptance and remaining qualification

[Actual post-refill reference measurements](lineage/r59-usb170-trial/usb-reference-return-verification.json) show In1 and In4 each remain one connected main-ground component. Every actual ground component projected under the USB route has a finite-via path to main ground. All 96 inherited shield-spoke regions, R20/U7/J6 finite main-plane contacts and current U10/C18/C19 returns pass.

The compact DP In1 join removes 0.952993 mm2 of ground within its clearance envelope. It has no F.Cu ground projection and about 46.1% In2 coverage. In3 full-width near-reference coverage is about 53.9% DP / 55.7% DM; nearest measured transition return-via distances span 1.134–2.884 mm. These are explicit signal-integrity tradeoffs. The route does not have a uniform reference, and no 90-ohm, USB compliance or delay-matching signoff is claimed. Actual production stack, copper/dielectric tolerance, varying coupling, plane transitions and bench USB operation remain to be qualified.

## Separate mechanical implementation

- [Initial native deficits](mechanical/initial-native/INITIAL-DEFICITS.json): redesigned main 49 errors/one open; child 12 errors/two opens.
- [Main S3/TAIL correction](mechanical/main-signal-01/verification.json): 45 errors and zero opens, with no new or worsened finding in that batch.
- [Child copper correction](mechanical/child-copper-01/verification.json): **zero errors, zero opens, ERC 0 and exact physical net mapping** after native refill. Its 11 bare-contact courtyard and 11 footprint-filter warnings remain visible.

These mechanical files have not replaced the accepted routing or canonical sources. The main mechanical board still needs complete copper repair and integration onto the latest route. The old accepted header still has its 11 edge errors. Tab/slot dimensions, body/connectors/pinout constraints and tolerance/strength study remain in [the earlier candidate02 package](../local-r57-checkpoint/mechanical-candidate02/PUBLICATION-STATUS.md). Calculated fit does not establish fixture capability, solder wetting, load strength or vibration endurance. Physical tests and the combined final validation remain open.

## Power and manufacturing hold

[C27's exact-part DC-bias evidence](power-input-capacitor-review/README.md) reveals inadequate effective input-capacitance margin against the TPS629210 requirement. No silent nominal-value substitution is made. C27 remedy and compact input/return routing remain required, independently of DRC.

Sixteen inherited pasted vias / seventeen contacts remain. Assembly process, current/thermal/transient/fault behavior, U2 orientation/FSYNC and connector mapping questions remain open. The 7.4 V BEC / 10 A continuous / 25 A peak goal is not a verified PCB rating. Never apply raw 6S to the FC. Manufacturing CAM/CPL are historical/stale; manufacturing stays on hold.
