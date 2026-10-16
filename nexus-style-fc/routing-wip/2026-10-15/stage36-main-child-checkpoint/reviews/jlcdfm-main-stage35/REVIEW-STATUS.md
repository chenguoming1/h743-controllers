# Stage35 main-board JLC DFM recheck

Both targeted PCB findings cleared in the fresh JLC result:
- Unconnected trace end: stage32 0 danger / 1 warning / 0 good → stage35 0 / 0 / 0.
- Solder-mask opening exposing trace: 1 / 82 / 4 → 0 / 83 / 4.

The returned mask table no longer contains a danger. The remaining bottom-side first displayed warning is 0.10 mm; its first-50 cap does not expose the repaired 0.235 mm native gap. The native gap and removed sensor leaf/via/drill are source-owner verification, while the vanished check flags are the external DFM result.

## U10 and remaining gates

U10 is unchanged from stage32:
- C89347, TPS70933DBVR, TPS70933DBVR_TI_DBV0005A
- Top, rotation 0°, CPL X 9.4500 mm / Y 26.1000 mm
- One pin-without-pad danger
- Four overlap ratios 0.66, below 0.75 danger cutoff; good boundary 0.90
- Two outer-edge extension dangers at 0.15 mm
- One 0.96 mm misalignment warning

All 18 SMT summary rows match stage32. Component-edge, lead-to-hole and other unresolved assembly findings remain. Pad-spacing is now 7 danger / 77 warning / 16 good, previously 7 / 79 / 14. Via-to-pad remains 3 / 1 / 7; four 0.60 mm plated-slot flags persist. Silkscreen results remain capped at 100 dangers for each pad/hole category.

## Exact source binding

Source PCB SHA256:
bf9a10563839b18071dedd1c4a71af60c25ac19e94f392adb1917955b1f4e95d

Gerber/drill ZIP:
bcf525a22962fea52f75eae84222c7ba2723e16b4e2caa4864729ebadd9ff457

BOM:
2f6a4b397ec8f024e5d7a3af2dda365843d928af03de5ace5fd50504501bd9fc

CPL:
dedbc7419bcf7d472864b7e0f0e7aabdada9d939caccd508f1ec1398261b96a1

Seal:
8705a184aab9fd5dfa307e4a3e10c94caeeadbb25fff6722a67d475be0ea9bfa

Twenty main source/manufacturing files were independently checked against the seal. One new stage35 project received each exact input once. All 48 BOM groups matched, with 83 CPL placements. The unchanged child was not uploaded again.

## Coverage and limits

The site detected six copper layers and 22.4 × 33.1 mm. Retrieved routing distributions name F.Cu/B.Cu only; equivalent inner-layer checks are not proven. Generic rules were unchanged, and no factory-specific stack, copper, ENIG, tenting, corner/EP, fill/plug/cap or stencil process was accepted. Native zero errors/opens/parity does not close these process gates.

The cloud browser again reported unsupported 3D. Loading-components/board rendering did not finish, so model orientation and bottom component localization remain unresolved. The small illustrative graphics in rule dialogs are generic examples, not actual board images.

One bounded PDF attempt timed out after 15 seconds; no second attempt or recovery loop was made. Actual combined report DOM/text, 47 summary rows, 60 focused detail rows and two actual screenshots are retained. The report shows overlap as “0.02mm,” while the detailed table explicitly reports the dimensionless 0.66 ratio; this inconsistency is preserved.

Report time displayed by JLC: 2026-10-15 10:17:47, timezone unstated. Observed approximately 17:18 UTC.

## Files

- stage35-dfm-findings.json: complete findings, comparison, exact hashes and limitations
- dfm-summary.csv: all 47 returned PCB/SMT summary rows
- localized-findings.csv: focused mask and U10 details
- combined-report-dom.txt and combined-report-visible-text.txt: actual website report
- pcb-mask-danger-cleared.jpg: actual mask result
- u10-overlap-still-open.jpg: actual U10 overlap table
- input-binding.json and PUBLIC-EVIDENCE-MANIFEST.json: source/file bindings

Private session continuation and original receipts are excluded from public evidence. Public files contain no account email, private session/project identifiers, order/pricing fields or tokens. No order, quote, purchase, factory outreach, design/rule/placement change or publication occurred.

Status: targeted fixes confirmed; other DFM/process gates remain. Not manufacturing release.
