# FLASH_WP_N local completion proposal

**Native polygon checks pass; native import, refill, DRC and final connectivity are still required.** Source candidate09 and the original located topology are unchanged. No router/JVM/solver was run.

`proposal.json` is the construction input. `native-exact-witnesses.json` contains exact nearest-point witnesses for every trace segment and all new-via copper, SMT-mask, drill, edge, NPTH and rule-keepout checks. `prepare_flash_completion.py` reproduces the proposal from candidate09's hash-bound native export in a few seconds.

Source board SHA256: `544491a48469d418ed47cf5da12b6b9406db282d60a3cda77b154f6ed11a869d`.

The existing via at `(31.5, 20.9853)` is UUID `d41c1d0a-2833-4d09-b76c-706923526c40`. Use the same located new through via at `(30.21631, 24.55996)`, diameter 0.45 mm, drill 0.20 mm, F.Cu–B.Cu. All added tracks are 0.127 mm wide.

In2.Cu centerline, in millimetres:

```text
(31.5, 20.9853)
(30.21631, 22.26899)
(30.21631, 24.55996)
```

B.Cu centerline, in millimetres:

```text
(30.21631, 24.55996)
(29.72977, 25.0465)
(28.9515, 25.0465)
(28.775, 24.87)
(28.775, 24.1)
(28.165, 23.49)
(27.485, 23.49)
(27.285, 23.49)
```

Every segment is horizontal, vertical or 45°. The last two collinear segments intentionally retain a 0.20 mm witness fully inside R5.2's actual native inside polygon. Its full-width containment excess is 0.0565 mm. Destination pad UUID is `5f4c8e5b-5b44-4f68-a793-0a4377aa4f5b`.

The raw In2 path's 15 corners / 4.54640 mm reduce to 3 corners / 4.10638 mm. The raw B.Cu path's 116 corners / 15.28001 mm reduce to 8 corners / 4.22862 mm. The source raw topology, including its backtracking and microsegments, is retained verbatim in the proof.

Minimum B.Cu foreign-copper clearance is 0.163000 mm at R38.2, versus the hard 0.127 mm rule and the raw path's 0.127200 mm. The lower-edge copper clearance is 0.290000 mm versus 0.254 mm. Both limiting reserves are 0.036 mm. R38.1's clearance is 0.176500 mm versus 0.133948 mm on the raw path. This keeps the hard 0.127 mm rule unchanged while moving the route away from its narrowest tangencies.

The new via's limiting reserve is 0.0934196 mm above the foreign-copper rule, against the +5V_BEC track on In3.Cu. All via mask and drill checks include same-net objects; no net exemption is applied. Only the explicitly enumerated regenerable GND fills on In1.Cu/In4.Cu are omitted, so the actual refill and saved-ground contour checks remain necessary.

The proposal is bound to candidate09, before the concurrent ADC route. Recheck against that added geometry and any later candidate before acceptance. The metadata correction proven separately under `tests/mpn-parity/` changes no geometry and can be applied after routing is complete.
