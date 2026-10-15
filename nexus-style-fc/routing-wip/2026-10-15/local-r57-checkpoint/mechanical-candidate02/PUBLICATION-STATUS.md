# Separate unfinished mechanical implementation

This is the exact sealed candidate02 implementation and static study based on historical r54. It is **not** the accepted r57 routing source. Do not fabricate or assemble it.

The approved scope preserves the board body, connectors and pinout while redesigning tabs, slots and solder contacts. The candidate uses 10.0 x 2.1 mm R0.5 slots, 8.4 x 2.6 mm tabs and root reliefs, with redistributed matching contacts. Read the [dimensioned design and limitations](candidate-02/nexus-style-fc/docs/header-interface-candidate/README.md) and [preview](candidate-02/nexus-style-fc/docs/header-interface-candidate/header-interface-dimensioned-preview.pdf).

Static analysis identifies inherited copper that must be rerouted: three DSM_DATA slot-edge conflicts, five main moved-pad different-net overlaps, six child edge conflicts and two child pad-to-track gaps. These are visible implementation deficits, not accepted exceptions. The guarded transaction is intended for replay on latest accepted copper; never overwrite that copper with this old r54-based board.

Nominal and adverse tolerance screens are calculations. Gross tab-root area is 17.65% lower; solder exposure and locating overlap also change. No allowable structural load is established. Assembly fixture capability, actual fit, solder wetting/current, vibration and strength tests remain required. The generated new child-board 3D model and native refill/ERC/DRC/parity integration are not certified by this static snapshot.
