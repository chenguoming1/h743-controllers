# Exact saved-board recovery and separate native replay

From this recipe directory, run `python3 restore_exact.py --output /your/new/f722-heli.kicad_pcb`. The default source is the sibling native2 checkpoint's PCB. Its source hash and the final native1 hash are checked. This standard-library patch reconstruction was tested and reproduces the exact saved PCB; it does not refill copper or validate engineering behavior.

Run `python3 replay_native.py` for the tested read-only 61-file and exact delta checks. To request a fresh native construction, use `python3 replay_native.py --rebuild-native /your/new/project-directory` with KiCad pcbnew 10.0.6+dfsg-1 available. This explicit mode adds the pinned primitives, performs the pinned removal and fills/saves the board under stated bounds. It was syntax-checked but not executed during packaging. A native replay mismatch is a failure to investigate, not permission to replace the recorded accepted PCB.

Neither command claims manufacture or flight qualification. The numerical replay source has its own source-only verification and explicit heavy commands in ../dc/REPLAY.md.
