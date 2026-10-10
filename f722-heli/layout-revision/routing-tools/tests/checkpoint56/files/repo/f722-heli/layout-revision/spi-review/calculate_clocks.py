"""Source-derived divider arithmetic. Does not emulate or qualify hardware."""
import json
from pathlib import Path

core_hz = 216_000_000
def divider(request_hz):
    clk = (core_hz // 2) >> 1
    divisor = 2
    while clk > request_hz and divisor < 256:
        divisor <<= 1
        clk >>= 1
    return divisor

rows = []
for name, bus, request in [('imu_detection', 1, 1_000_000),
                            ('imu_initialized', 1, 24_000_000),
                            ('flash_detection', 2, 5_000_000),
                            ('flash_initialized', 2, 104_000_000)]:
    d = divider(request)
    hw_div = max(2, min(256, d // 2 if bus in (2, 3) else d))
    pclk = core_hz // (4 if bus in (2, 3) else 2)
    rows.append(dict(name=name, spi=bus, request_hz=request,
                     software_divisor=d, hardware_prescaler=hw_div,
                     br_bits=hw_div.bit_length()-2, peripheral_clock_hz=pclk,
                     actual_nominal_sck_hz=pclk/hw_div,
                     helper_spiCalculateClock_hz=(core_hz/2)/d))
output = dict(core_hz=core_hz, apb1_hz=core_hz/4, apb2_hz=core_hz/2,
              rows=rows,
              caveat='Default unoverclocked clocks only. Read back installed firmware/settings/registers and measure actual SCK. The helper alone overstates SPI2 frequency at software divisor 2.')
print(json.dumps(output, indent=2))
