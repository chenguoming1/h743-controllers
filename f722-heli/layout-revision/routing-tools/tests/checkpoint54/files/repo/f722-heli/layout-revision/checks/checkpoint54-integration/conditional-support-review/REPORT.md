# Candidate06: conditional R52–C30 return review

**The shared trace contributes only microvolts of DC drop under the stated current assumptions. This does not qualify it as a quiet ILM return or bound ADC/noise transients.** Candidate06 board SHA-256: `24121b0e46d9a71207cd21e7cf599412c00796d48eb9af5f63ffcf92e5f2ca42`.

## Exact circuit and geometry

U5 is **TPS259472ARPWR**. Its actual device GND is **pin 8**, (12.96,16.725); pin 9 is ILM. R52 is **750 Ω / 1%**, with pin 1 on EFUSE_ILM and pin 2 on GND. C30 is **220 nF / 16 V / X7R**, **ADC_BEC-to-GND**, connected to the MCU ADC_BEC node, not an eFuse timing or ILM capacitor.

The native R52.2 lead runs (14.1,15.49) → C30.2 (15.25,15.52): **1.150391238 mm / 0.20 mm F.Cu**. It then shares C30's existing **1.249986804 mm / 0.25 mm F.Cu** lead to GND via (16.4574,15.8435), 0.45 mm diameter / 0.20 mm drill. Total explicit trace to that via is **2.400378042 mm**. Shared-track UUID: `3971ab08-e156-4148-8f93-1a9c4636b51f`.

U5.8 separately reaches via (14.15,17.23) through **1.448296998 mm / 0.15 mm F.Cu**. Therefore R52's local return is through the C30 lead, via and common plane, rather than a direct short trace to U5.8. The ILM signal trace itself remains 1.163969501 mm / 0.20 mm.

## Requested thin/hot-copper calculation

Assume uniform **15 µm copper at 105°C**, resistivity at 20°C **ρ20 = 1.724×10⁻⁸ Ω·m** (approximately 100% IACS), and linear **α = 0.00393/°C**. Thus ρ105 = 2.2999022×10⁻⁸ Ω·m. Applying R=ρL/(wt) to only the shared lead gives **7.66626 mΩ**. Scaling resistivity by 1/0.95 for the **95% IACS sensitivity** gives **8.06975 mΩ**.

[TI Rev. C, §6.5, p.10](https://www.ti.com/lit/ds/symlink/tps25947.pdf) specifies ILM gain 165–200 µA/A; at the illustrated currents the row requires IOUT<ILIM. Table defaults include VIN=12 V, RILM=549 Ω and −40°C≤TJ≤125°C. The arithmetic below is conditional on applicable specifications, not a measured result for this 750 Ω circuit.

| Assumed total U5 current | Maximum-gain illustration | Shared drop, base copper | Shared drop, 95% IACS |
|---|---:|---:|---:|
| 2.0 A | 0.400 mA ILM | 3.06650 µV | 3.22790 µV |
| 5.5 A, datasheet illustration only | 1.100 mA ILM | 8.43289 µV | 8.87672 µV |

**The external 2 A rail load does not bound total eFuse current:** core/DSM loads can add current when supplied through U5. The 5.5 A row is neither a board continuous-current rating nor assurance that this 750 Ω setting allows 5.5 A below current limit. Relative to nominal 750 Ω, the shared trace is 10.22 ppm (10.76 ppm at 95% IACS). These figures exclude the via, plane, device-ground return, fabrication tolerances and all dynamic effects.

## What remains unqualified

C30 has negligible ideal steady-state capacitor current, but charging/discharging, ADC sampling and coupled switching/noise can drive time-varying current through the shared conductor. The ILM-current calculation does not bound those currents, inductive voltage or the difference between C30's local ground and U5.8. C30 is **not directly connected to ILM**, so its 220 nF value alone does not demonstrate violation of TI's ILM capacitance recommendation; actual ILM parasitic loading has not been extracted.

[TI §8.4.1, pp.62–63](https://www.ti.com/lit/ds/symlink/tps25947.pdf) recommends nearby support parts, short returns to the device GND pin, a quiet eFuse ground reference, separation from switching/noisy signals, and ILM parasitic capacitance below 50 pF. Small calculated DC drop does not establish compliance with that guidance.

The supplied `quiet-return-alternatives14.json` (SHA-256 `c4669bbbf554a8e2662a7df0de874776f373b75351c7673dc891babfbd16f4b7`) records a **bounded 0.20 mm F.Cu domain**, x=10…17.5 mm, y=10.7…19.2 mm, with signal/analog copper fixed and U12 discharge reserved separately. R52 cannot reach the R51 pad/new tie or actual U5.8 pad/via within that domain; C30.2 is reachable. This documents a local structural blocker, **not global routing infeasibility**. No further search or fallback construction was performed here.

## Scope and provenance

Candidate06's proposal is byte-identical to `dedicated-u12-ground15/separated-returns14-proposal.json`, based on board `73dbae05954b8edec4143d91248bf38c40537f83e8f5f3fed51744105169d6c7`. Existing saved native results show **14 unconnected / 0 errors / 0 warnings**, with no critical ground-return fault. Those results do not supply the missing electrical qualification or imply all gates passed. The pinned TI PDF is SHA-256 `8f96de389903091650d4f462dcfad3210071c3ae7093623a7978f34baf8a65b4`.

`evidence.json`, `run-summary.json` and `review_r52_c30.py` reproduce the identities, exact paths, assumptions and arithmetic. All read inputs were hash-verified unchanged. Only new files in this review directory were written; no native board, prior review or seal was changed.
