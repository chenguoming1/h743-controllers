# Conditional SBUS geometry review

This review supports retaining a complete geometric routing witness. It does not qualify the assembled board, receiver, cable, waveform, ESD behavior or power supply. Exact timing inputs and sensitivity results are in `conditional-timing.json`; fetched firmware files and their identities are in `fetched-source-index.json`. Final native candidate02 is bound to PCB SHA71d33748909bb960c5829973642272460607d8521831a6212975f7de6790d660, constructed on final shared19 SHA80eb38da7100fd677862b8d3bc161329b278c410614f3b15460b5a5c863a75e6.

## Actual circuit and firmware

Native pads establish Q2.1 at +3V3_CORE, Q2.2 at SBUS_LV and Q2.3 at SBUS_HV. With the BSS138 pinout, this is a non-inverting pass-FET level translator. R37 is a 4.7 kΩ ±1% LV pull-up; R45 is 220 Ω ±1% between LV and the MCU/clamp network. R26 is 470 Ω ±1% on the external HV side. The rising edge depends on the pull-up, nonlinear FET capacitance and the HV driver/cable; it is not a push-pull output with a guaranteed MCU slew rate. The onsemi pinout and electrical limits are in [BSS138LT1/D](https://www.onsemi.com/pdf/datasheet/bss138lt1-d.pdf).

The pinned Rotorflight commit ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94 defines 100,000 baud SBUS, optional 200,000 baud fast SBUS, even parity and two stop bits. Its default configuration sets `sbus_baud_fast=false`. The pinned Nexus target maps SERIAL_RX2 to PA3, matching U1.17. Receiver inversion is selected by the UART configuration, not by Q2. Sources: [sbus.c](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/rx/sbus.c), [rx.c](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/pg/rx.c), and [Nexus target](https://github.com/rotorflight/rotorflight-targets/blob/1d9cb4dc6f85c7895c2b089f4b8aa776ca3d3bd3/configs/RDMS-NEXUS_F7.config). These are source settings; no installed firmware or receiver settings were read back.

## Load and guaranteed limits

Initial native17 has 75.6476 mm of SBUS_LV and 50.9899 mm of SBUS_MCU planar copper. Fixed reference bends add less than 0.001 mm. Five ordinary through-vias are added. LV uses F/In2/F; the MCU tree uses F/B/In3/B. R45-to-U13.1 is 7.6768 mm and U13.1-to-U1.17 is about 43.3131 mm of routed copper; actual pad traversal and barrel length are separate. The actual U13 cut separates both branches by 0.170269 mm outside the bonded pad; no source-to-target bypass exists.

U13's USBLC6-4SC6 specifies 4 pF maximum I/O-to-GND capacitance at 1.65 V and 25 °C. That is not a constant-capacitance guarantee across the full signal swing and temperature. Other active channels can add coupling. [ST USBLC6-4 datasheet](https://www.st.com/resource/en/datasheet/usblc6-4.pdf)

The MCU data sheet gives production-tested digital thresholds of 0.7VDD high and 0.3VDD low. The listed 5 pF pin capacitance is typical, not a maximum. The tighter design-guaranteed threshold formulas are not needed for this conservative calculation. [ST DS11853 Rev9, Table61](https://www.st.com/resource/en/datasheet/stm32f722rc.pdf)

Q2's 50 pF maximum Ciss and 25 pF maximum Coss are specified at VDS=25 V, VGS=0 and 1 MHz. They cannot be summed and treated as a guaranteed low-voltage circuit capacitance. Its on-resistance maximum applies at specified VGS/current/temperature; the actual low-level gate-source bias may be lower, so this review does not extrapolate that limit to prove VOL. [onsemi BSS138LT1/D](https://www.onsemi.com/pdf/datasheet/bss138lt1-d.pdf)

The native stack uses 0.127 mm signal width, 0.0994 mm surface-to-plane dielectric, and 0.25 mm near inner-to-plane dielectric. A deliberately broad engineering sensitivity range of 0.08–0.25 pF/mm gives roughly 10–32 pF of trace capacitance, before pads, five vias, device capacitances and coupling. Allowing 2–10 pF for pads/vias is a scenario, not an extracted or fabrication-guaranteed bound. These estimates motivate the 80–300 pF total-load sweep, but do not establish that the assembled load is below its acceptance limit. Actual stackup, Q2 bias, the HV receiver and cable must be included in extraction or measurement.

## Conditional rise and sampling calculation

The calculation pessimistically places all effective LV/MCU capacitance behind R37+R45, with 5 kΩ total resistance including tolerance, copper and temperature effects. The named ±1% values give 4,969.2 Ω before copper; the 5 kΩ all-condition limit is an explicit additional condition, not a claim that unknown resistor temperature behavior has been qualified.

For VDD at least 2.7 V, at most 10 µA total adverse leakage, and VIH=0.7VDD, the first-order rise is `-R*C*ln(1-VIH/(VDD-R*Ileak))`. External driver/cable/FET release delay receives a separate 0.25 µs allowance, plus 0.001 µs nominal board propagation. The HV network is not assumed isolated throughout a transition. A larger coupled cable load or slower release invalidates this allowance.

The conservative analytical sampling allowance is `Tbit*(0.5-1/16-11.5*0.02)`. It reserves one 16x sample for synchronization/early sampling and 2% combined transmitter/receiver frequency error over 11.5 bit periods. This is an explicit conservative model, not a claim about measured baud error or a substitute for the receiver's full tolerance conditions. The pinned driver disables one-bit sampling; the analytical calculation conditions on 16x oversampling (the HAL constant is zero), without claiming a register readback. The hardware majority-sampling mechanism is described in [ST RM0431, USART sections27.5.4–27.5.5](https://www.st.com/resource/en/reference_manual/rm0431-stm32f72xxx-and-stm32f73xxx-advanced-armbased-32bit-mcus-stmicroelectronics.pdf).

Under all those conditions, total effective capacitance must be below about 292 pF at default100k, or126 pF at optional200k. At120pF, the total modeled delay is1.0004µs, leaving1.0746µs and0.0371µs respectively. At250pF, default100k has0.2628µs margin, while200k fails the model. The small120pF fast-mode margin is unsuitable as an unmeasured release claim.

A separate low-level condition remains: the actual receiver through R26 and Q2 must pull U1.17 below0.3VDD with adequate noise margin, within the same timing budget. Receiver VOL/sink impedance, cable capacitance, Q2 low-bias conduction and protection-device leakage are not supplied. The rising-edge calculation cannot prove this falling-edge/low-level requirement.

## Return path and release conditions

Initial native17 has no outside-own-via-window centerline reference gap. Four width-only fragments totaling0.000190658 mm² were measured and retained. A single fixed recentering pass removes them in the saved-plane planning model; the final native refill independently confirms zero remaining centerline or full-width projection outside those same own-via windows. Own-via antipads and reference transitions remain physical discontinuities. No AC return-current, ringing, crosstalk or ESD simulation is implied by an empty projection.

The route is a complete geometric witness with conditional timing support for default100k. Present evidence does not require discarding it solely because of length. Functional release still requires a source-bound final stackup/load model or measurements using the actual receiver/cable: both threshold crossings, low level, ringing/overshoot, sampling margin and error-free frames across supply/temperature and configured baud. Fast200k needs its stricter load/delay bound demonstrated independently. Fresh numerical power/VCAP validation also remains pending.
