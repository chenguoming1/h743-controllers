# Complete SBUS native candidate17

Source: final shared A/B native19, PCB80eb38da…a75e6. Candidate:71d33748…90d660. Native17 opens/0 errors/0 warnings, strict parity and ERC clean. Owner adoption is pending.

This complete transaction closes the protected R45.2→U13.1→U1.17 tree, relocates R45 inward to F(11.65,21.8), and reconstructs the complete SBUS_LV pull-up/pass-FET branch.41 tracks and5 ordinary tented vias replace5 old LV tracks. All155 other footprints,556 other pad records and existing vias are exact. Complete source NRST is unchanged.

All82 new endpoints have finite pad, junction or actual-annulus proof. All28 support groups and all prior actual cuts remain complete.18/22 actual cases and16/20 channels pass, with U13.1 outside-pad branch gap0.170269mm. Remaining signals are explicitly unfinished.

Both new nets have zero saved-plane centerline and finite-width gap outside explicit own-via windows. Critical copper and outside-own-window missing reference geometries are exact; raw BARO_SDA width delta−2.3792756653762126e−10mm² is retained, with zero actual lost critical width overlap. Whole-plane equality and AC-return qualification are not claimed.

SBUS_LV is75.647640mm; SBUS_MCU is50.990697mm. The pinned default100k SBUS has conditional RC support, with optional200k requiring a substantially smaller load budget. Unknown receiver/cable, nonlinear FET loading and low-level behavior prevent an electrical-release guarantee. See conditional-signal-review. Fresh numerical power/VCAP qualification remains pending.
