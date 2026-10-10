# Compact CORE and power-terminal review

Read REPORT.md first. Historical power-model supply injection uses TPS2553 EN4 instead of IN6 at both U10 and U11; fresh source-bound correction and revalidation remain required. Candidate41 pin-role identity is checked, but its power is not numerically qualified here.

Run `python3 -B verify_packet.py` in this directory. It checks SHA-256 integrity and consistency of retained inventories/findings only. It does not fetch sources, re-extract the original PCB, run a solver, or certify manufacturer documents or board behavior.

Official documents are linked in the report and source-register.json. Raw vendor PDFs, screenshots, firmware copies and large native-board sources are omitted. Their exact hashes are retained where acquired. source-register local_path fields refer to the original research tree, not files included here. Ferrite official access limitations remain explicit.

The full research extraction scripts require the source-bound rebuild workspace; this compact packet is intentionally self-contained only for evidence inspection and integrity verification. No board, firmware, canonical repository, numerical model, historical diagnostics, Git or Library item was changed by this review.
