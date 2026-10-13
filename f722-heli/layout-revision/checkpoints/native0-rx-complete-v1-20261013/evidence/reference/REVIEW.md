# Cleanup applicability and bounded prototype disposition

The cleanup preserves the actual-v2 reference and protection-return findings. It removes exactly the obsolete GREEN via and F spur, restores their local GND antipad, and introduces no newly lost reference on any surviving track. The two known residuals remain explicit: a short RX/MOSI crossing before the clamp, and a small MISO trace-edge overhang at the separate new GREEN antipad. These do not, by themselves, justify another automatic routing change. The cleaned geometry is a credible prototype candidate within the existing 27 MHz stock-source envelope; fresh candidate-bound power/current review remains separate, and hardware behavior is not certified by this geometry.

## Exact cleanup and coverage

Source v2 PCB: `462fe6420795db1be524689132d6a60ef1461a89a6426f58e9ade46396ab2bf2`.
Cleaned PCB: `84229c571433bd72d410fb18d02cffa3a380c00a87fbe1270e3a73b63f8dd6cd`.
Clean native logical hash: `04d8ecd80edf004f3226f204f23adba51692a498ae38edc183debeffb704603d`.
Clean auxiliary logical hash: `fd69a86a4df11b1815419a288012e32487c7c57a6d0200eab1d7f53007f3f6ba`.

Independent stored/logical hash checks bind both native pairs and PCB bytes. Exactly two source records disappear: via `255b4bac-a2be-542a-849b-c3f26cc969a4` and F spur `9e18ffd3-153b-5213-9d54-f67ad2248b23`. All 2,525 remaining native records, all footprints, the outline/layers, all 331 remaining drills and the actual zone settings are unchanged. Only the In1/In4 GND fill records change. Derived fill-representation statistics are correctly treated as fill evidence, not configuration; the initial strict comparison and its narrow correction are preserved.

All 1,662 surviving tracks are inventoried, including all 28 In4 signal segments. None loses newly supported reference compared with actual v2. Approximately 0.41066285 mm² of GND is restored on each plane around the removed barrel. Raw Boolean contour losses of 0.000000118 mm² on In1 and 0.000000023 mm² on In4 remain in the report; no affected current track projection or reviewed contact intersects them. No geometry was repaired, snapped or silently rounded away. Both GND planes remain one copper component.

The two surviving GREEN In2 records positively overlap by 0.012668970 mm² at `(32.15746,21.80934)`. Their union covers the former drill center with 0.063500264 mm boundary distance, preserving the actual 0.127 mm junction. Removing the obsolete drill eliminates its endpoint reference gap: the new GREEN lead's unsupported centerline falls from 0.705704 to 0.352853 mm, leaving only its live new-via transition.

## What transfers geometrically

The actual U15 pads and ground collector are exact, with their full In4 backing and margins unchanged. IO1 remains at 0.099502 mm minimum lateral margin; IO2 at 0.190546 mm. The one-dielectric comparison is a nominal engineering target, not a fabricated tolerance guarantee.

The 2.162850 mm, 0.25 mm B ground connection directly to connector barrel edc8 is unchanged, as are its positive pad/annulus contacts, full conductive-copper reference support and both ground-plane annuli. The finite c8-to-J11 corridor remains supported. All six previous SPI/BARO finite witnesses retain their exact measured margins and lengths. These are explicit applicability checks; global DC connectivity is not being substituted for return quality.

Every reported RX/TX reference interval is unchanged. The isolated RX/MOSI gap remains 0.609907 mm, about 0.523476 mm before actual IO1 copper. Its cross-layer overlap remains 0.025751792 mm², with the previously stated approximately 0.009703 pF parallel-plate scale. The source-side path length, fringing, clamp pulse voltage and ground-return impedance prevent treating that scale as an extracted bound. A bounded straight-path check did not establish a complete short finite return across this new gap; the scoped negative remains preserved without implying a disconnected plane or demonstrated malfunction.

The MISO In2 centerline remains fully referenced. At the separate new GREEN antipad near `(36.947032,23.754177)`, the trace edge still extends 0.003312 mm beyond the In1 GND edge over 0.000083385 mm². The 0.060188 mm centerline-to-GND-edge distance is unchanged. Requiring every micron of every ordinary trace's width to have literal plane backing would be an invented blanket constraint. This small edge perturbation should instead be judged within the complete interconnect. Its parallel-plate capacitance scale is about 0.0000125 pF, expressly not a fringing or impedance bound. It is a minor geometric perturbation relative to the full route and does not establish SPI failure.

## Timing, waveform and protection disposition

The exact cleaned SCK/MOSI/MISO copper lengths are 49.739070, 48.644681 and 49.051343 mm. Their used via spans remain unchanged. Using the largest declared εr = 4.4 gives quasi-TEM flight scales of 0.370481, 0.342104 and 0.360215 ns, still within the prior 0.4 ns per-signal timing allowance. The existing 27 MHz timing screen therefore retains its numerical margin, including the proposed 2 ns settling/jitter allowance. Those allowances are engineering screens, not measured guarantees.

Pinned stock source selects VERY_HIGH output speed and nominal 216 MHz core / 27 MHz SPI2. The MCU datasheet supplies maximum edge times but no minimum, and the actual installed binary, load and live clock/register settings have not been established by this geometry review. The 30 MHz/240 MHz case remains an overclock stress case. Positive setup/hold arithmetic cannot rule out ringing, threshold recrossing or discharge-induced corruption. See [ST STM32F722 datasheet](https://www.st.com/resource/en/datasheet/stm32f722re.pdf) and the previously sealed source/timing ledger.

The direct connector-ground improvement, fully backed clamp pads, short 0.523 mm pre-IO distance and small overlap scale support retaining the selected prototype tradeoff. They do not establish ESD immunity, nor does being before the clamp automatically demonstrate worse protection. TI recommends short protection ground paths and reducing coupling from connector discharge paths; it does not impose a numeric ban on this overlap. See [TI TPD4E05U06 datasheet](https://www.ti.com/lit/ds/symlink/tpd4e05u06.pdf) and [TI ESD Protection Layout Guide](https://www.ti.com/lit/an/slva680a/slva680a.pdf).

Checks available now are complete for this narrow applicability scope: exact records/drills, actual refill differences, all surviving reference projections, contacts, unchanged finite witnesses and route-length timing applicability. Fresh DC/current evidence must bind the clean board and remains owned by the separate power review.

Prototype checks remain concrete and limited: verify the stock binary and actual full-speed 27 MHz clock; capture SCK/MOSI/CS at the flash and MISO at the MCU with controlled probe loading; check threshold stability, setup/hold, overshoot and first/last-bit behavior while UART traffic and normal supplies operate. Exercise designated flash test data/readback. For protection claims, perform connector discharge testing at the intended product level and check data integrity, resets and recovery. Do not replace these with an exhaustive hypothetical simulation requirement, or claim system ESD qualification from the TVS component rating.

No source adoption, board mutation, routing, power solve or ESD qualification occurred here. The previous full actual-v2 review remains separately sealed as `7cd74f6d…`; this packet narrows its applicability to the exact cleaned board.
