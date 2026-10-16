# Redesigned child JLCDFM result — b49ef410

Automated PCB and assembly tables were captured in dot's cloud browser on 2026-10-15. The exact sealed Gerber/drill ZIP and matching BOM/CPL were accepted in a distinct project. This is an engineering check, not fabrication release.

## Results

- PCB: displayed **0 danger, 32 warning** findings. Annular ring: 6 warnings at displayed 0.15 mm (4 front, 2 back), against 4/6 mil classification boundaries (0.1016/0.1524 mm). The reported primitives correspond to 0.30 mm holes / 0.60 mm copper diameter.
- PCB tht-to-smd: 26 warnings (8 front, 18 back), displayed clearances 2.35–2.85 mm, versus displayed 2.03/3.05 mm boundaries. Objects are header-pad circles and joint-pad rectangles. The table does not expose XY/net identities. These broad process-proximity checks do not establish electrical shorts.
- Assembly: displayed **0 danger, 7 warning** findings. All seven are J1-to-board-edge at displayed 0.56 mm, versus 20/32 mil boundaries (0.508/0.8128 mm). J1 matched C32713294, HX PZ2.54-3x7P ZZ, explicitly through-hole. Original CPL: Top, 0°, midpoint 11.2250/7.4650 mm; no placement edits.
- Detected board: 2 layers, 22.4 × 11.0 mm.
- Other reported minima: trace width 0.20 mm; pad-to-edge 0.23 mm; pad spacing 0.37 mm; PTH-to-trace 0.44 mm; via-to-pad 0.20 mm.

## Process and coverage limits

Only **Built-in system rules** was available. No 2 oz, thickness, or finish selector was exposed. No rules were altered. The intended FR4, 2 oz both faces, 1.6 mm and ENIG remain source declarations, not an accepted supplier stack/process. The automated result does not qualify delivered copper thickness, current/thermal performance, the soldered board joint, matched-profile tolerances, edge registration, vibration or flight readiness.

F.Cu and B.Cu detail tables were retrieved. Bottom tht-to-smd reports 68 results but retains only the first 50 (18 warning, 32 good). Counts refer to primitive/check results, not distinct components. Zero-result categories show “No” for measurements and do not establish complete coverage. The sole through-hole header requires insertion/soldering qualification independently of the site's SMT-named workflow.

The site could not render 3D; its 2D/board viewer remained blank/loading. No site XY/pin localization was recovered. PDF export stalled with “Exporting PDF, please wait...” and a browser-runtime timeout. Actual generated report text and table receipts are retained; there is no downloaded PDF. The report's literal timestamp is 2026-10-15 07:47:10, with no time zone exposed; capture was approximately 14:47 UTC.

## Source binding

- Source PCB SHA256: b49ef4108ab0b85d4cd96fac22553e3bc16b214f5acde148a8680e1212097ee6
- Gerber/drill ZIP SHA256: 79992a19ed45803321ac0dff7762fc96e10b41c2f740df3c2fac40d74067c21b
- BOM SHA256: 6a2b3bbf1d27e84750eeaf034740681aaec0cd7413f736f5d7a42f3fed85e706
- CPL SHA256: bf4bcb800239e4bae3c8b60adf1c5857b3636ae2fb359dbaedc06789f03488cf

Detailed structured results: `child-dfm-findings.json`; full summary: `child-dfm-summary.csv`; actual report receipt: `combined-report-visible-text.txt`. Screenshots show the real warning table/rendering limitation and PDF-export state. These files exclude account, customer, order/pricing and private project identifiers. Keep `private-originals/` private; its continuation file contains a project URL/upload identifier.

The first ZIP selection met an expired DFM session and yielded a site error without a project ID; server storage is unknown. A single controlled retry after restoring sign-in produced the confirmed project. No order, quote, payment, factory contact, deletion, geometry or placement change occurred.
