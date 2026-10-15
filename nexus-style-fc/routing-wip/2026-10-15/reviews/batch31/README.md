# Read-only board-level review of batch31

This review is bound to experimental PCB SHA-256 47b6cf94fb2213c0ae46ab692fd9b8f71e90c2c278944827f9156daa25e8e23b, published at PR33 commit 8d7fdeb5c5b73123b70e972923f1386c262d018b. It does not certify newer candidates or fabrication readiness.

Start with review.md and native-evidence-review.md. The three geometry JSON files contain exact stored-copper/pad/zone extraction for original main, candidate16 and batch31; plane-power-analysis.json and the CSV provide measured comparisons. Source-evidence.json identifies vendor guidance and explicit calculation assumptions. The original review manifest is retained; publication-manifest.json also seals the supplemental native evidence and this index.

Projected plane coverage is a sampled geometric measurement, not a simulated return-current fraction. Trace resistance estimates use declared bulk-copper and stored-stack assumptions, excluding vias and temperature. Unknown effective capacitance, current, impedance, transient/stability and EMI effects are explicitly unqualified. No failure or current rating is predicted.

The read-only extraction/analysis scripts are archived for method transparency and contain the original cloud experiment paths. They are not a portable one-command qualification procedure. Only source paths should be adjusted in a disposable local copy when reproducing the measurements. No design-generating or manufacturing-export script is invoked by this review.
