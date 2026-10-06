# DSM receiver power requirements — checked 2026-10-05

## Applicable classic three-wire remote interface

Spektrum's official [Remote Receiver Interfacing Rev A](https://my.spektrumrc.com/ProdInfo/Files/Remote%20Receiver%20Interfacing%20Rev%20A.pdf), dated12 April2016, is publicly linked from the [SPMAR7210BX product support page](https://my.spektrumrc.com/Products/Default.aspx?ProdID=SPMAR7210BX). Section6 specifies 3.3 V ±5% and 20 mA maximum for its classic three-wire remote receiver interface. This is a sourced receiver requirement, distinct from a controller port advertising nominal3.3 V/0.5 A capacity. The connector at the remote is S3B-ZR(LF)(SN), mating ZHR-3; controller-side pin order still needs the documented harness mapping.

The [official Rotorflight receiver table](https://rotorflight.org/docs/2.1.0/configurator/tabs/receiver) lists SPM9545, SPM4645, SPM4648, SPM9745 and SPM9746 as3.3 V serial receivers. Its SRXL/SRXL2 entries use5 V ports: SPM4649T requires4–8.4 V, while SPM4650(C), SPM4651T and SPM9747 list3.3–8.4 V. These families must not all be treated as the same3.3 V satellite load or protocol.

The [official Rotorflight NEXUS page](https://rotorflight.org/docs/2.1.0/controllers/rm-nexus) repeats nominal3.3 V/0.5 A for DSM and5 V/2 A for A-B-C. It does not publish a load/temperature accuracy guarantee. Do not infer that the original NEXUS guarantees±5% at its full0.5 A rating from those nominal figures alone.

## Design review consequence

The frozen-tree full0.5 A DSM analysis cannot support a3.3 V±5% guarantee at that load. A separate20 mA remote-receiver calculation with simultaneous CORE load is now required against the actual3.135–3.465 V interface window. Include regulator PFM/PWM low corner, common tree drop, dedicated branch/switch/contact/return drop, and a remaining cable/transient margin. Do not raise the shared CORE rail to hide receiver-path loss.

Any20 mA compatibility result applies to the documented classic remote interface. It is not proof that every generic DSM-labelled device, SRXL2 receiver, arbitrary0.5 A load or unknown cable meets its requirements. A voltage/load curve and first-article receiver power/bind/failsafe tests remain necessary.

## Frozen-tree classic-remote calculation

The independent calculation is recorded in `validation/routing-45-abc-loaded-voltage-review/dsm-classic-20ma-curve.json`. At20 mA remote load plus0.32 A CORE, regulator PFM low3.1845 V,125°C conductor stress and assumed20µm via plating, its receiver-terminal estimate is3.15556 V. Included losses are20.42 mV common-tree,0.385 mV dedicated output copper,3 mV switch,2.4 mV for both post-test JST ZH power/return contact pairs, and2.739 mV modeled PCB ground return. The remaining20.56 mV above3.135 V must still cover cable, source line/load effects and dynamics. A proposed10 mV dynamic allocation leaves about0.528Ω cable-loop resistance at20 mA; that allocation is a design target, not a measured transient pass.

This conditionally supports the documented classic satellite interface without changing shared CORE voltage. It is not an arbitrary0.5 A±5% guarantee, and it must be recalculated after any power-tree changes. First-article tests still need actual receiver startup/binding, supply ripple/load steps and failsafe behavior with the chosen cable.
