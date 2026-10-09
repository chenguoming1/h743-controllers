# Candidate15 endpoint and actual-annulus audit

**PASS.** The receipt is frozen. No board or source files were changed.

- Receipt: `candidate15-endpoints.json`
- Receipt SHA256: `8b7bcae7d87ee3bb8273ada31da9dfb54390af494b4b95013549e5360ac919b4`
- Script: `audit_native_endpoints.py`
- Script SHA256: `97d814fa10e1539ef5b26e68626882182c694cb4444e51409493a2e4a37a6b55`
- Candidate15 board SHA256: `23232e7bc1903c06c1809d569c91e4cb161281be9225f3776076386593e55674`
- Source13 board SHA256: `008d0b11df400284d12750c7f5c877b43a7ea28ffddbf4a4b799c3ae7ec4917e`

All 1,559 existing source13 native object records are unchanged; candidate15 adds 19 tracks and two vias. No source object was removed.

## Qualified endpoints

All nine new SMD pad terminations pass native ERROR_INSIDE geometry, actual interior termination and a complete 0.127 mm transverse section. The finite entry interval is calculated by intersecting the centerline with the convex actual pad translated by both transverse half-width offsets, with a further 1 nm inward reserve.

- Minimum positive pad depth: 0.063535764861 mm
- Minimum finite full-width pad entry: 0.021170181755 mm

Both added vias have verified F.Cu and B.Cu annular entry. The actual annulus is the native copper polygon contracted by the export error, minus the native conservative drill void. Five finite full-width transverse strips pass, including both sides of ADC_BEC's through-running F.Cu track.

- Minimum full-width annular strip length: 0.010000000000 mm
- Minimum strip-section distance from drill/outer annular boundary: 0.050528065612 mm

This does not use a centerpoint in the drill void or require an impossible half-width disk erosion across a 0.125 mm radial annulus. The complete rectangular strip is checked inside actual copper.

## Retained non-evidence

NRST segment `25dc9b1a-5683-4364-8aaf-24d61f83d884`, `(16.41974,14.32167)` to `(16.47327,14.32167)`, is a 0.05353 mm redundant buried spur. Its centerline is inside the drill and its copper is contained by the via disk. It is retained unchanged and is not counted as annular-entry evidence.

The upstream horizontal NRST segment `9319384d-9f9d-45bd-9f66-ae32c0862fb5` has incidental side overlap at the via edge. It shares an exact full-width path endpoint with diagonal `59c9c52f-ec0f-431e-8061-f6cdffc7460d`, which independently proves full-width actual-annulus entry. The incidental overlap is not used as entry evidence. The raw initial overly strict per-segment diagnostic is preserved as `candidate15-endpoints.initial-diagnostic.json`.

## Scope

ADC_BEC adds 11 tracks and one via; NRST adds five tracks and one via. BOOT0 adds three tracks joining the two duplicate SW1.2 physical pads only. ADC_BUS receives no additions. The receipt qualifies the new endpoint/contact geometry, not complete routing of every named net. Native DRC, process, saved-fill and full connectivity remain separate owner gates.

Reproduce without board edits:

```sh
python ordinary-routing/tests/broad-endpoints/audit_native_endpoints.py \
  --source ordinary-routing/candidate13 \
  --candidate ordinary-routing/candidate15 \
  --out ordinary-routing/tests/broad-endpoints/candidate15-recheck.json
```
