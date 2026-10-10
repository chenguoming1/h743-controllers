# RPM_LV candidate37 located-path alternative

This packet proposes a complete add-only R39.1 B.Cu → through-via → R36.2 F.Cu path. It is an independently constructed native alternative, not successful engine output. The actual engine insertion FAILED. Its two partial engine additions are not adopted.

Source board SHA-256: `2a73d9b7dad3a14b0d00c80e81e0ba8a817b50179c15692aad39fde9920c2115`.

## Findings

The complete captured raw path fails native copper clearance at R43.2 (ADC_DIV_MID) by 0.101262417 mm and at retained SBUS_HV tracks `4e822ce0-de92-493e-a701-8f4d796963a1` and `ba723236-9e41-4526-8f25-7bfbbde14b83` by up to 0.012226360 mm. The raw B.Cu route and fixed via position clear their applicable constraints.

Only two bounded corner windows were repaired. All source objects are retained. Pad-entry extensions were verified wholly within their actual native pad copper. Native-checked line-of-sight simplification then reduced 86 raw segments to 20 segments; these exact-coordinate straight lines include arbitrary angles, not only 45°/90°. The via remains exactly `(15.42167,24.77301)`, diameter/drill 0.45/0.20 mm, tented on both faces.

The final B.Cu path is 6.789432059 mm with 0.011046513 mm minimum excess clearance. The F.Cu path is 18.304496011 mm with 0.000200000 mm minimum excess clearance. The via minimum excess clearance is 0.047810000 mm. Every SMT mask on both faces and every native drill is included without same-net exceptions; drill-to-mask and drill-to-drill gaps are 0.20 and 0.25 mm. Copper clearance and track width remain 0.127 mm. Native polygon error is 0.00001 mm.

The two model-declared GND fills on In1.Cu/In4.Cu overlap the new via location as saved. They require normal native antipad refill under the existing model policy, preserving zone identities, outlines, and rules. Every physical source object remains fixed, including all existing RPM_LV copper. Current saved-plane centerline projections are covered, but this does not establish post-refill reference acceptance.

## Files

- `proposal.json`: Complete raw/repaired/simplified coordinates, exact source hashes, constraint witnesses, pad extensions, prospective annular witnesses, and pending gates.
- `captured-rpm-records.json`, `raw-screen.json`: Preserved complete located path and native refusal diagnostics.
- `corner-repair.json`: Bounded local repair choices, points and constraints.
- `native-construction-model.json`, `constructed.ses`, `constructed-report.json`: Standalone source-preserving native import inputs, with no mutable source objects.
- `construction.json`, `packet-verification.json`: Checksummed construction receipt and independent consistency checks using only the importer's pure SES parser functions; no KiCad runtime loaded.
- `screen.py`, `refine.py`, `finalize.py`, `verify_packet.py`: Reproduction helpers. Use `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=python-deps` from the project root.

Wrong-source, outside-pad, invalid via process, and invalid track process controls all reject. No board was edited or imported by these helpers. Native import, DRC, connectivity, actual endpoint/annular/process checks, protection, refill, and post-refill reference checks remain mandatory. No final acceptance or reduction of board opens is claimed.
