# Current integrated experimental Nexus project

Open **[nexus-style-fc.kicad_pro](hardware/nexus-style-fc.kicad_pro)**,
[main PCB](hardware/nexus-style-fc.kicad_pcb), [schematic](hardware/nexus-style-fc.kicad_sch),
and [matching child board](hardware/header-board/nexus-header-board.kicad_pcb).

Both boards have zero native geometric errors and opens. Main electrical parity, dangling findings,
and library-footprint mismatches are zero. Main retains 11 centering, one mixed-technology type and
49 silk advisories; child retains 11 bare-contact courtyard and 11 footprint-filter advisories.
Enabled ERC is zero on both. Inherited optional-check severity disclosures remain in the evidence.

The current source combines approved capacitor/power fixes, six-layer routing, the redesigned
10.10 × 2.20 mm tab/slot interface and narrow assembly/silk cleanup. All artwork changes use
matching main-only local footprint variants. The latest cleanup changes no copper, pad, net,
placement, stack, outline or filled zone.

PCB SHA256 2099ceb9ff904859a68e288683ee68b2ad74d7741b8b670341baf67bf67e1ea3; schematic SHA256 7bfd6617e7d0285c738615fd2b6d7b6d6958675c095e50de87a8ed44111b972b.

- [Final-source schematic PDF](docs/connected.pdf)
- [Exact source archive](docs/nexus-integrated-project-source.zip)
- [Fresh WIP BOM/CPL](manufacturing-wip/README.md)
- [Sealed main/child Gerber, drill and assembly review package](manufacturing-review/README.md)
- [Latest native/source/export evidence](../2026-10-15/assembly-source-checkpoint/README.md)
- [Manufacturing release gates](../2026-10-15/assembly-source-checkpoint/manufacturing-gates/RELEASE-GATES.md)
- [Integrated geometry and fit evidence](../2026-10-15/integrated-interface-checkpoint/README.md)

**Fabrication, assembly and flight qualification remain on hold.** Actual-stack USB, pasted-via
process, BEC/current/thermal tests, finished fit/contact registration, narrow-rail/joint strength and
IMU pin/axis disposition remain open. Automated DFM is only one part of that closure.

Root hardware is the older coherent reference, not the current routing. The committed native PCB
is authoritative; historical floorplan/build scripts do not reconstruct accepted copper. The source
archive contains project-local core models; standard KiCad models and retained repository models
remain dependencies. The older functional-detail PDF is preserved as a prior-source preview.
