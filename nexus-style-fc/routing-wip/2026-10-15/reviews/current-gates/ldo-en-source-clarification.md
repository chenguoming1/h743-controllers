# U10 enable-source clarification

This supplements the earlier LDO decision addendum without changing its geometric recommendation.

TI TPS709 Rev H §7.4 explicitly says not to connect EN to VIN. It permits leaving EN floating using the internal pull-up. The stated 300 nA pull-up is not an allowable externally injected clamp current. Therefore the observed IN/EN-to-VSYS tie is an inherited vendor-guidance violation even before determining whether VSYS exceeds the EN rating. The voltage/transient range still determines additional electrical stress; no specific failure is asserted without it.

Source: https://www.ti.com/lit/ds/symlink/tps709.pdf

The parent is handling the authorization and schematic/netlist scope for a possible EN isolation. This read-only review neither edits nor approves a net change. The original output-loop proposal must not be represented as resolving this separate gate.
