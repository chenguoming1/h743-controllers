"""Read-only engineering arithmetic; no firmware or PCB mutations."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CLK = 54_000_000
TCLK = 1e9 / CLK
TIMINGR = 0x00800D26  # Executed unchanged upstream C in stock-ba6c7e3/timing_probe.
FIELDS = dict(PRESC=0, SCLDEL=8, SDADEL=0, SCLH=13, SCLL=38)
def period(tr, tf, af_rise, af_fall, sync_rise, sync_fall):
    return (14 + 39) * TCLK + tr + tf + af_rise + af_fall + (sync_rise + sync_fall) * TCLK
def parallel(*r):
    return 1 / sum(1 / x for x in r)
def pullup_case(name, delta_t):
    lo = 2200 * .99 * (1 - 100e-6 * delta_t)
    hi = 2200 * 1.01 * (1 + 100e-6 * delta_t)
    return dict(name=name,delta_t_C=delta_t,r_external_min_ohm=lo,r_external_max_ohm=hi,
        r_if_DPS_bus_pullup_present_min_ohm=parallel(lo,60000),
        r_if_DPS_bus_pullup_present_max_ohm=parallel(hi,180000),
        rise_50pF_external_only_ns=.8473*hi*50e-3,
        cmax_at_100ns_external_only_pF=100e3/(.8473*hi),
        cmax_at_120ns_external_only_pF=120e3/(.8473*hi),
        current_mA=[dict(rail_V=v,at_Vol0_external=v/lo*1000,
            at_Vol0_external_plus_conditional_DPS=v/parallel(lo,60000)*1000,
            at_Vol0_external_plus_conditional_DPS_and_MCU=v/parallel(lo,60000,30000)*1000,
            at_Vol0p4_external_plus_conditional_DPS=(v-.4)/parallel(lo,60000)*1000)
            for v in [3.3,3.432,3.6]])
data=dict(review_date_utc='2026-10-09',nominal_i2c_kernel_clock_Hz=CLK,
    timing_register_hex=f'0x{TIMINGR:08X}',fields=FIELDS,tclk_ns=TCLK,
    programmed_counter_ns=dict(scl_high=14*TCLK,scl_low=39*TCLK,scldel=9*TCLK,sdadel_counter=0),
    stock_algorithm_assumption=dict(rise_ns=100,fall_ns=10,analog_filter_ns=50,synchronizer_cycles_each=2,
        resulting_period_ns=period(100,10,50,50,2,2),resulting_frequency_kHz=1e6/period(100,10,50,50,2,2)),
    timing_inequality_limits_at_nominal_clock_ns=dict(
        rise_from_setup=9*TCLK-50,
        fall_from_hold_minimum=50+3*TCLK,
        rise_from_unstretched_data_valid_maximum=450-260-4*TCLK),
    provisional_design_targets=dict(rise_30_70_max_ns=100,fall_70_30_max_ns=100,bus_C_per_line_max_pF=50,
        measured_total_C=False,capacitance_allocation_status='Engineering allocation, not component pin maximum or extracted final load'),
    illustrative_unstretched_period_envelope=dict(
        description='Nominal 54 MHz; edges independently 0..100 ns; analog delay 50..260 ns each; sync 2..3 cycles each. No clock stretching/software stalls. Not a guaranteed on-board frequency.',
        period_min_ns=period(0,0,50,50,2,2),period_max_ns=period(100,100,260,260,3,3),
        frequency_min_kHz=1e6/period(100,100,260,260,3,3),frequency_max_kHz=1e6/period(0,0,50,50,2,2)),
    pullup_cases=[pullup_case('Initial tolerance at25C',0),pullup_case('Resistor temperature -40..85C',65),pullup_case('Resistor temperature -55..125C; manufacturer TCR test endpoints',100)],
    supply_note='3.432 V is +4% initial PFM accuracy only. 3.6 V is an operating-ceiling design screen, not a proven regulator transient bound.',
    internal_pullup_note='DPS368 Rpull=60..180k is not positively assigned to SDA/SCL in reviewed datasheet; conditional parallel cases only. Stock MCU internal pullup default false; 30k conditional case covers an unexpected enabled MCU pullup.',
    sources=[])
data['sources'] = json.loads((ROOT / 'datasheet-source-index.json').read_text())['sources']
(ROOT/'stock-i2c-calculations.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(data,indent=2))
