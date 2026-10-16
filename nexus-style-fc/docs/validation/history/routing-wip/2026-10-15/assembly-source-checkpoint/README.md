# Source-consistent assembly checkpoint, unfinished

[Open the stable current project](../../current/README.md).
Main PCB 2099ceb9ff904859a68e288683ee68b2ad74d7741b8b670341baf67bf67e1ea3; schematic 7bfd6617e7d0285c738615fd2b6d7b6d6958675c095e50de87a8ed44111b972b; accepted manifest ea7b161a78d4d3e12cf5f80af5812e4128ec26427bcb2b48986f6ce9a1943f90.

Fresh main/child native checks have zero geometric errors and opens. Main parity, dangling and
library mismatch findings are zero; enabled ERC is zero on both. Main has 11 centering, one mixed
assembly type and 49 silk advisories. Child has 11 courtyard and 11 footprint-filter advisories.
No severities, clearances, pin maps or physical copper were changed to obtain these results.

Five Nexus-only footprint variants make the approved J4/J6 outline and D1/D2/D3 cathode marks
source-consistent. U3/L2/U14 assembly attributes reflect actual SMT packages. J1 is a manual
child-board joint; J6 retains mixed SMT/PTH assembly. Exact selected-part polarity drawings,
actual silk plots, final source tests and BOM/CPL comparisons are in [accepted](accepted/).

The [geometry comparison](accepted/geometry-verification.json) proves complete physical/fill
identity with stage08, binding its finite-return, mask/paste, USB and mechanical checks.
[Manufacturing gates](manufacturing-gates/RELEASE-GATES.md) distinguish cloud checks, manufacturer
evidence and physical tests. The final stack is unresolved: the saved 1.600 mm declaration and
1.6168 mm copper/dielectric sum must be reconciled with the actual manufacturing offer.
No order, fabrication release, current rating or USB impedance compliance is claimed.
