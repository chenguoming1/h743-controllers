# P6 bounded sourcing recheck — 2026-10-03

No actual current orderability blocker was established. Current availability was not refreshed: the permitted web reads returned older cached pages, so they cannot replace the newer retained live observations. No substitutions, orders, cart changes or third-party contact occurred.

Current native SHA-256: `3c80eba2e6dfd7161f875436aff8c64bcaee0ad8d6cc94a55b24bfc5e2014e47`. All 79 fitted references and 35 exact MPN/C-code identities match the maintained sourcing record. That record preserves live observations from 2026-10-02 20:25:50 through 23:10 UTC, roughly 19–22 hours before this check; it reported no preorder-only parts and no one-board quantity shortages. This is not a batch allocation or assembly MOQ guarantee.

| Part | Newest retained live observation | Stock / available / minimum | Bounded web recheck |
|---|---|---|---|
| Q2 DMN2310UW-7 / C7264627 | Oct 2 23:10 UTC | 49 / 28 / 1 | Old cached results conflict: 10-month crawl says zero, 4-month crawl says 1,077 available. Neither establishes current stock |
| J3 XDWF-0910-06P / C7527621 | Oct 2 20:26:24 UTC | 716 / 715 / 1 | 5-month crawl says 1,088 available; too old to renew the observation |

Sources: [exact Q2 JLC page](https://jlcpcb.com/partdetail/DiodesIncorporated-DMN2310UW7/C7264627), [exact J3 JLC page](https://jlcpcb.com/partdetail/Lian_XinTechnology-XDWF_091006P/C7527621). Retrieval occurred October 3 around 18:05–18:06 UTC; retrieval time is distinct from the recorded crawl age. A recency-filtered attempt produced no fresher exact-SKU evidence. The bounded web attempt is closed.

Q2 remains the only materially scarce prior selection: 28 available units is not a promised build quantity, because batch size, attrition and competing purchases are unreserved. The browser owner can make a narrow live Q2/J3 check when free. Larger-stock parts were not repeatedly shopped.

Correction to earlier readiness wording: the maintained live J3 capture explicitly records no fixture warning; older indexed J3 and Q2 pages flag fixtures. Do not state that either exact SKU currently mandates a fixture or fee. Actual carrier, nozzle, support and depaneling suitability remains production engineering. The readiness report and structured gate list have been corrected accordingly.

The maintained snapshot is [here](../controller-r3s-p6/review/sourcing/controller-r3s-bom-source-status.json). Its historical raw-capture paths are absent from this workspace; this audit does not claim to have replayed them. [Structured results and hashes](controller-r3s-p6-sourcing-recheck-20261003.json) preserve that evidence limit.
