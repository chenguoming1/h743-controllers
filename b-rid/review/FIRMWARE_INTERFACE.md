# Firmware interface and required behavior

Hardware interface specification only. No firmware has been implemented or flashed in this work.

| ESP GPIO | Module pad | Function |
|---|---:|---|
| GPIO0 | 12 | BQ24074 EN1, USB current mode; hardware pull-down |
| GPIO1 / ADC1 | 13 | Isolated BAT_SENSE from TMUX1119 common terminal |
| GPIO2 | 5 | Boot strap, 10 kΩ pull-up; do not repurpose casually |
| GPIO3 | 6 | BQ24074 EN2, suspend mode; hardware pull-down |
| GPIO4 | 18 | PGOOD_N, active-low valid charger input indication |
| GPIO5 | 19 | CHARGE_ACTIVE from isolated open-drain status translator |
| GPIO6 | 20 | G indicator, active-high green |
| GPIO7 | 21 | R indicator, active-high green |
| GPIO8 | 22 | Boot strap, 10 kΩ pull-up |
| GPIO9 | 23 | BOOT/download strap, TP3 |
| GPIO10 | 16 | Unused |
| GPIO18 | 26 | Native USB D− through R4 / ESD network |
| GPIO19 | 27 | Native USB D+ through R3 / ESD network |
| GPIO20 / RXD0 | 30 | Receiver UART input |
| GPIO21 / TXD0 | 31 | Receiver UART output |

## Indicators

- **G:** blink while acquiring; steady only with a fresh, valid GNSS navigation solution. A UART message alone is not a valid fix
- **R:** indicate actual successful RID transmit scheduling/state. A GPIO transition or illuminated LED is not proof of an on-air, standards-compliant broadcast
- **S-green:** hardwired to enabled 3V3 through 1 kΩ. It indicates system power, not firmware health
- **S-red:** VBUS-fed, charger CHG_N-controlled. It works with SW1 off. Green and red can appear together while powered and charging
- Charging state must be interpreted as `PGOOD_N == 0 && CHARGE_ACTIVE == 1`. Without valid external input, CHARGE_ACTIVE can also be high

G/R use the green die of Kingbright APHB1608CGKSURKC. The letter R means RID, not red. Their unused red dies are disconnected. Nominal LED current is approximately 1 mA; actual brightness and daylight visibility require inspection.

## USB power policy

BQ24074 modes, written as EN2/EN1:

| EN2/EN1 | Mode |
|---|---|
| 00 | USB 100 mA default |
| 01 | USB 500 mA |
| 11 | USB suspend |
| 10 | Resistor-programmed ILIM mode; avoid unintended entry |

For suspend, set EN1 high before EN2. For resume, clear EN2 before EN1. Keep the defined state during supported MCU sleep.

The ESP-IDF `usb_serial_jtag_is_connected()` API only detects SOF traffic. Do not use it as permission to select 500 mA. Verify the actual fixed USB descriptor and a valid configuration/current-grant mechanism or validated host protocol. USB-only startup/programming with an absent or depleted cell, and MCU-off behavior on a suspended host, remain qualification gates. The default 100 mA setting is deliberately retained.

## ADC and power-off behavior

R13/R14 are 1 MΩ / 330 kΩ. TMUX1119 is powered from VSYS; SEL follows 3V3. Off selects ground at the ADC; on selects BAT_DIV. The 100 nF reservoir is on the divider side, not on the unpowered ADC side.

The divider nominal Thevenin resistance is 248 kΩ and its nominal RC time constant is about 24.8 ms. Allow at least five time constants after initial battery attachment before precision sampling. Use calibrated ADC1 measurements and sufficient attenuation headroom. Validate rail-collapse timing and off-state ADC voltage physically.

## GNSS

Use UART0 for GNSS, not the application console. Verify the receiver's default 38400 baud, 8N1 configuration. USB Serial/JTAG can serve development logging/programming.

The selected patch is characterized at 1575.42 ±3 MHz. GPS L1, Galileo E1 and QZSS L1 are the intended band-compatible configuration; do not imply GLONASS or BeiDou B1I antenna performance from a GPS L1 specification. Configure supported constellations explicitly and verify acquisition, fix age and coexistence with ESP radio transmissions. Backup power is absent, so full shutdown causes cold-start behavior.
