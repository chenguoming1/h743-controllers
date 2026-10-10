# R38 DSM transition: complete local positive witness

Source board: candidate43/f722-heli.kicad_pcb
SHA256: 1ee7174a578dffe4d5ef3ae8b39d8dc88f28b80395539263a65f23be234c21e6
Native geometry SHA256: 05dc43aad22ced8a7b7b9145a4514cca62854bf888a9ffc7626877eae8a36140

No board save, source edit, Git/public mutation, JVM, or FEM occurred in this task. All files are read-only planning evidence under tests/dsm-r38-transition43.

## Exact joint proposal

Keep R38 unchanged. Add DSM_RX_MCU on B.Cu, width 0.127 mm:
(18.11, 23.46) → (18.45, 23.8) → (18.45, 24.095).
Length: 0.775832611 mm. The first point is exact native R38.2 center.

Add a 0.45 mm copper / 0.20 mm drill through-via at (18.45, 24.095), tented on both faces.

Remove exactly these two +5V_BEC In3.Cu tracks:
- 38e0887e-ae81-480f-82c7-f32e7ea12c27
- cad1419a-e60e-4274-b9ad-78e419772ee4

Replace them with this continuous +5V_BEC In3.Cu path, maintaining 0.6 mm full width throughout:
(15.021874, 20.464544) → (17.7, 23.7) → (17.7, 24.8) → (24.147805, 24.648486).

Old two-segment length: 10.967014750 mm.
New three-segment length: 11.749648552 mm.
Added length: 0.782633802 mm.

The replacement endpoints exactly match native retained tracks 3c9d0986-cb92-4a98-95ab-47049350e62b and cc812963-97cb-461c-a9a1-37f1f946c240. Both retained tracks and replacement are 0.6 mm wide; source native copper overlap areas are recorded in joint-escape-proof.json.

## Exact geometry and connectivity results

- B.Cu stub: 1188 constraints, all pass; smallest extra clearance 0.178734597 mm.
- Via: 3915 constraints, all pass; smallest extra clearance 0.035186396 mm.
- Reconstructed BEC: 660 constraints, all pass; smallest extra clearance 0.015108050 mm.
- Full new copper is inside the exact source outline, with edge/NPTH clearance included.
- All SMT mask-to-drill checks include both faces and same-net masks; all drill spacing checks include same-net drills. In1/In4 GND fill is the only skipped copper, for an eventual native antipad/reference review.
- Actual +5V_BEC remains one connected component containing the same 12 pads: C55.1, C56.1, C57.1, C59.1, C73.1, R54.1, R56.1, R58.1, U6.7, U6.8, U7.3, U7.5.
- No other tracks, pads, footprints, or drill locations change. The complete actual D7 protected DSM_RX_EXT cut, both BARO trees, critical reference routing, and prior I2C work remain untouched.

## Scope and required later gates

This proves the local R38 pad-to-via escape and its complete two-track BEC reconstruction. It does not include the parent’s inner DSM trunk or claim a native candidate has been adopted. Fresh native DRC, source-specific reference/GND antipad review, and a new loaded-power calculation remain required on the final joint candidate. Equal BEC width and preserved pad groups do not establish equal loaded power after the 0.782634 mm length change.

Reproduce from ordinary-routing:

PYTHONPATH=../python-deps python tests/dsm-r38-transition43/verify_joint_escape.py
PYTHONPATH=../python-deps python tests/dsm-r38-transition43/compare_bec_connectivity.py

Proof files: joint-escape-proof.json and bec-connected-pad-groups.json. The bounded discovery screen in minimal-conflict-screen.json is diagnostic, not an impossibility result.
