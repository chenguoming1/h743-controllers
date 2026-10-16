# ADC-local placement / bounded DSM repair

Status: apply-only delta verified in memory against the retained-clock stage33 topology. No PCB saved, refill performed, or native DRC/parity run by this worker. Native acceptance remains required after coordinated integration.

## Accepted source and scope

- Source: `stage33/hardware/nexus-style-fc.kicad_pcb`
- SHA-256: `1fff67ee301156ef1e05809bcd92ea15d70c0094468adc84d4b6917bac405efe`
- Preserve C10 B(111.75,122.05),180°; C12 B(112.35,120.5),−90°; Y1 B(114.9,120.5),180°. Preserve B_TX and the complete original B-ground tree except the two specifically replaced/stub objects below.
- Parent supplies C29 F(111,119.2),270°; R16 F(111.4,121.15),90°; removal of old VX_SENSE routing; C29-to-R16 and C29-to-ADC routing and C29's quiet return.
- This delta supplies C30 F(114.39,114.16),0° and R17 F(111.4,123.2),270°. C14 stays unchanged. Values, footprints and pinouts stay unchanged.
- Apply `apply_adc_dsm_delta.apply(board, reconnect_old_ground=True)`. Keep its returned removed-object list alive. It never loads, writes, refills or runs DRC. Guards reject the abandoned NRST/clock-relocation candidate, wrong ADC ports, wrong pad nets/layers, missing live clock branches, and changed anchor vias.

## Resulting paths

Exact path coordinates and widths are the seven `PATHS` entries in `apply_adc_dsm_delta.py`.

- C30.1 → existing 5V_SENSE ADC via: 1.222 mm F, 0.127 mm wide. Together with unchanged B leg to U1.10: 3.974 mm / one via, versus the original approximately 11.32 mm / two vias.
- C30.2 → existing signal-ground stitch (114.4,113.6): 0.731 mm F, 0.25 mm wide. The existing two R17-site ground branches are preserved, adjusting their endpoint from (114.9,114.16) to C30.2=(114.87,114.16).
- R16.2 → local R17.1: 2.394 mm F, 0.20 mm wide; no layer changes. R17.2 → retained GND stitch (110.375,122.525): 1.567 mm F, 0.20 mm wide.
- Repurpose existing ground via `143f6a86-dfad-4a4b-8c52-59e7a5c3ed89` at (110.590858,121.956) as DSM_TX. Remove the former DSM via at (111.025,123.675), B bridge `e1826a78-56eb-4e65-a47e-04959ff29a23`, and In2 diagonal `c52d84d2-ab73-4340-acef-2a0febfffa3d`.
- New DSM B + In2 branch: 10.797 mm, about 0.500 mm longer than its replaced branch. DSM via count is unchanged; no new drill location is introduced.

## Exact ground removals and replacement meaning

Ground tracks removed by this delta:

1. `77dabf7b-f7b0-4de5-8b21-a08d70f66662`: old C30.2 (109.07,112.97) → short free endpoint (109.18,112.86).
2. `9fdb6c49-9ec2-4300-a2dc-24c408f0eaec`: old C30.2 → (109.07,112.3475).
3. `77d81050-58a6-470d-b9ba-535a5df0f5fd`: obsolete old-C30 branch (109.555702,111.8525) → (109.07,112.3475).
4. `ff7cfb1b-c125-4db0-9000-8d64e4e8fec9`: old C29.2 (111.39,122.03) → GND stitch (110.375,122.525). Parent may already have removed this.
5. `3a5f9f92-0cf2-42df-87b3-919435a0d723`: live original clock/reset ground-tree link from the repurposed stitch to (111.176,121.956). Replaced by the guarded 1.021 mm B route from retained GND stitch (110.375,122.525) to that same live-tree port.
6. `d102ec12-9c83-4e54-bfee-f50279572b50`: approximately 0.014 mm stub (110.605,121.958) → repurposed stitch. Its remote endpoint has no other trace attached; do not reconnect it into DSM_TX.

`reconnect_old_ground=True` is mandatory for this retained-topology plan. It restores the live C10.2 / C12.2 / Y1.2 tree, not an obsolete capacitor-only stub. In-memory endpoint/shape traversal confirms C10.2, C12.2, Y1.2 and C25.2 connect through B copper to retained GND stitch (110.375,122.525). Y1.4's separate original grounding is untouched. Keep the remaining original tree, including 98f62710, 81d2d709, 22fed353, aca49794, bc8de5db, da1a158d and fed846f1. Keep the unrelated original U1.12 return tracks b54eb5dd and b3bcbf59.

The option `False` is only appropriate if a separately verified complete replacement of that live ground tree exists. It is not appropriate for this ADC-only candidate.

## Verification and remaining acceptance

- `check_adc_only.py` / `.log`: all seven clearance-guarded paths pass with original C10/C12/Y1/B_TX and B-ground retained; all original live ground-tree targets above remain connected.
- Repurposed DSM via: checked against actual foreign-net tracks/pads on all six copper layers; no contacts. Both-side pad/paste margin check at 0.10 mm passes. Its physical hole position is unchanged.
- C30/R17 changed pads and courtyard packing pass the bounded geometric checks. R17 clears J4/J5/D3 courts; C14 and connector poses are untouched.
- Native refill/DRC/parity, final zone/annular connectivity and final assembly/mask rendering still required. C29's ADC supply/via escape is the parent's separate integration dependency.
- The earlier two-part remote R17/C30 swap remains only a documented fallback in `pose_swap.py`, `routes_swap_inner.log`, `check_transfer.log`: its R17→C29 branch is 7.924 mm / two vias and is inferior to the accepted local-R17 solution. Do not integrate it with this plan.
