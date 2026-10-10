# Isolated NRST testpoint closure from accepted candidate44

Native result: 34 unfinished connections, zero geometric errors/warnings, strict schematic parity and ERC zero. Not adopted or manufacturing/flight qualified.

TP5 retains its UUID, SWD NRST function, 1.0 mm exposed testpad and native footprint. It moves from F.Cu (37,23.8),0° to B.Cu (16.9,6.0),0°. A native Flip(false),0° orientation and translation exactly reproduce the complete footprint. The other155 footprints and all1381 previous native track/via/arc structures remain identical. TP1 is unchanged.

Two0.127 mm B.Cu tracks are added: (16.9,6.0)→(17.12882,6.22882)→existing NRST via (17.12882,6.83933). There are no new vias, removals or changed existing copper. Native graphs connect C10.1,R1.2,TP5.1,U1.7. Finite full-width pad, join and actual-annulus proofs and five refusal controls pass.

The1.4 mm analytic probe-access disk clears every body; nearest body radial margin is0.411124556 mm. Nearest existing drill-to-new-mask gap is0.269944076 mm and new pad-to-foreign-copper gap is0.358487475 mm. All complete projected through-hole header body/lead spans remain clear, with at least0.3 mm lead-access reserve outside the probe disk. Full native courtyard, assembly reserve, solder access, outline, hole and orthogonal placement checks pass. This does not establish a specific3D fixture or assembled harness geometry.

All16 critical nets and returns, all28 native support partitions, both I2C clean trees, actual protection11/22 endpoint cases and9/20 channels are preserved. I2C electrical status and numerical power/VCAP remain unqualified.

Reference caveat: the raw complete-record comparator remains false because83 critical records received different transient KiCad net_code integers after changing TP5's side. No stored snapshots or raw comparison were normalized. reference-runtime-index-proof.json proves exact physical identity for all153 critical records, bijective runtime net mappings, exact saved zone records and exact complete reference net reports. Six rejection controls cover changes to name,width,UUID,endpoint,copper and omission. Owner adoption needs an explicit adapter for this verified index-only case, not a generic geometry exemption.

Source board SHA256: 02d2090ad7220a64a8f4a1a259d522f7b0bca3e15214b73107491d17626bd51f
Candidate board SHA256: 9881a992b12fed90f17131ed627f12af77680cc2ddf95030adf8c564aaa24eb2

The bounded SWDIO local-placement screen found no accessible1mm testpoint site beside U1.46: the suggested(28.4,16.5) B site overlaps C55 and C3. No SWDIO changes are included.
