# Manufacturing hold

The F722-rule reroute is unfinished. Do not order either board from these files.

The committed main Gerber ZIP predates the reviewed PCB: it has 227 via drill hits versus 225 source vias, and at least one power-track width differs. The generic header BOM is also stale. No new CAM is claimed by the rule-transfer checkpoint. Existing files are retained as historical evidence only.

Regenerate Gerber/drill/CPL/BOM together from the final source only after native KiCad 10 refill, ERC, DRC, schematic parity, geometry, USB/reference and power checks, and disposition of the header mechanical/contact and via-in-paste issues. See [current status](../docs/f722-reroute-status.md).
