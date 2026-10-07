# Exact-board native evidence

These compact reports bind the final95 PCB SHA-256 `4da0708a4795662cc32b035a0783c70b9bdb85fc386bd4d39af33385b175667f`.

- Standard and all-track DRC: 0 unfinished connections, 0 geometric errors and 9 unsuppressed warnings
- ERC/source parity: 0 ERC violations across 9 sheets; 156 components, 506 netted pin keys and 511 physical assigned pads
- Actual via-mask geometry: all 323 checks pass. Production and assembly acceptance remain separate
- Active-pad clamp geometry: all 18 scoped cases pass
- Reference continuity: no new deficits or unchanged-track regressions; exact cold refill reproduces the saved PCB

Eight of the nine warning objects have operating-current or local spreading-field dispositions. The retained PERIPH tail `874efe98` is harmless obsolete copper and is explicitly not a loaded conductor. The final electrical report supplies the exact field/current scope; no warning is suppressed.

Public path labels and the obsolete generic mask-audit note were clarified without changing numerical check data or the source board hash. These are CAD checks and scoped engineering evidence, not a blanket manufacturing, assembly, USB, EMC, thermal or flight qualification.
