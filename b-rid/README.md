# B-RID engineering prototype

Editable KiCad 10 project for a compact, battery-powered Broadcast Remote ID hardware prototype with onboard GNSS, USB-C charging/programming, a corner power switch and G/R/S indicators.

**Status: engineering CAD completed for review; fabrication and battery connection are not released.** The final native schematic/PCB checks and remaining qualification gates are recorded in `review/`. No firmware, flashing, RF compliance, flight approval or production-readiness claim is included.

## Current hardware

- Six layers, 35 × 24 mm nominal populated plan envelope; height unrestricted; parts on both faces
- ESP32-C3-MINI-1-N4X integrated antenna over a recessed PCB outline, inside the rectangular plan envelope
- u-blox MIA-M10Q-00B receiver with a directly mounted INPAQ PA1575MQ4S-123-1Z ceramic patch; no antenna cable
- JLC06161H-3313 impedance basis: 0.135 mm / 0.150 mm USB pair, and 0.150 mm GNSS feed, with a 0.300 mm minimum outer GND-zone clearance; both coplanar and non-coplanar calculator results were checked
- BQ24074 power-path charger and TPS63031 3V3 converter, with revised local capacitor/switching loops and exact capacitor selections supported by manufacturer DC-bias data
- TMUX1119 battery-sense isolation prevents the powered battery divider from driving an unpowered ESP input
- G and R use green LEDs driven by future GNSS-fix/RID-transmission firmware state. S-green shows enabled 3V3 power; S-red shows charging and can work with system power off
- Patch and G/R/S indicators on the SKY-marked B face; both RF modules on F for one final module reflow pass
- 60 footprint references: 4 test pads and 56 model references. C13/C14 are intentionally unpopulated RF tuning positions

Open `b-rid.kicad_pro`. Local symbols, custom footprints and all referenced 3D model files are included. The PCB is editable without running generators. Existing historical scripts are not needed to open or edit the project.

## Read before fabrication

1. Select and qualify an exact protected cell, temperature sensor and keyed 3-wire harness. Charge temperature limits, current/pulse capability, charge-voltage tolerance and safety-timer behavior remain unresolved. Do not attach a generic LiPo merely because its connector fits
2. Confirm exact MIA-M10Q and INPAQ antenna supply, assembly process and first-article fit. Public stock for the exact GNSS receiver/antenna was not qualified
3. Have the fabricator confirm the stated stackup, finished copper/impedance and filled/capped via-in-pad process. Review the manufacturing data before production
4. Validate GNSS matching/acquisition/coexistence, USB signal integrity/ESD and power/startup/thermal behavior on prototypes
5. Implement and test firmware. USB SOF detection alone does not establish a 500 mA current grant; MCU-off host-suspend detection remains unresolved

The package intentionally separates design checks from supplier and bench gates. It contains the current editable project and actual renders, not an order-ready CAM release. See `review/ENGINEERING_CHECKS.md`, `review/FIRMWARE_INTERFACE.md`, `review/ASSEMBLY_NOTES.md` and `review/PROTOTYPE_GATES.md`.
