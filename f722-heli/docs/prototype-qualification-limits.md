# Prototype qualification boundaries

These limits accompany the exact final95 CAD, selected-component source index, manufacturing notes and final electrical report. Numerical or geometric screens do not replace physical tests.

- USB firmware compatibility: the unchanged pinned Nexus target does not provide normal VBUS sensing. Self-powered attach, an unpowered host, backfeed and full USB compliance remain unproven; follow the controlled configuration-use and first-article checks in the final handoff
- Classic DSM: the cited classic three-wire interface requires 20 mA maximum at 3.3 V ±5%, or 3.135–3.465 V. This is not a generic 0.5 A ±5% guarantee and does not cover every DSM/SRXL/SRXL2 device or unknown harness. [Spektrum Remote Receiver Interfacing Rev A](https://my.spektrumrc.com/ProdInfo/Files/Remote%20Receiver%20Interfacing%20Rev%20A.pdf), [Rotorflight receiver compatibility](https://rotorflight.org/docs/2.1.0/configurator/tabs/receiver)
- Temperature assumptions: 105°C copper in a resistance sensitivity model does not raise component body-temperature ratings. Selected X5R capacitor bodies remain subject to their 85°C limit and DC-bias/effective-capacitance behavior. Use the exact MPN sources in component-source-index.json
- Protection devices: individual TVS data-sheet ratings do not establish system ESD compliance, connector-discharge survival or MCU-pin stress safety. The actual-pad clamp audit checks the stated copper topology and geometry; bench qualification remains separate
- Sensors and firmware: retain the current IMU Rev 2.4 qualification discussion. A surface keepout pass does not establish compliance for buried copper or all-layer guidance. Use one coherent CW90/yaw transformation, not two accumulated transforms, and verify sensor direction, noise and failsafes on a first article
- Assembly: stackup, exact R16 supply and installed network, R31 0201 Standard assembly, seven THT headers, four USB shell-slot solder joints, factory placement preview, housing/mating fit and actual contact/harness performance remain explicit factory or bench gates

No motor-connected or flight qualification is asserted. Preserve all visible native warnings and their exact final-board dispositions.
