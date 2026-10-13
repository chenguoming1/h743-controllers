# Saved-byte recovery and cumulative construction data

Run `python3 restore_exact.py --source /your/public/native1/f722-heli.kicad_pcb --output /your/new/f722-heli.kicad_pcb`. The default source location is the sibling native1 checkpoint. This standard-library patch checks the exact public source hash and selected target hash. It restores recorded bytes and does not refill copper, run DRC or establish engineering qualification.

CUMULATIVE-SOURCE1-TO-CLEAN-RECIPE.json preserves 19 typed source cuts, 36 track/two via additions, three footprint transforms and 14 transformed pads. It reconciles 2,506-19+38=2,525 objects and 330-1+2=331 drilled objects. Public normalization wraps the original artifact identity and retains its primitive values and scientific proof claims.

The actual native validation was performed as the routed v2 stage followed by the exact two-record GREEN cleanup. The compact cumulative recipe was not executed as a single native operation. The original full native-proof execution closure includes broader local helpers and historical-proof bindings; this compact checkpoint does not claim a portable fresh native/physical replay. TRANSACTION-SOURCE-CLOSURE.json records that distinction. Exact intermediate board/native exports are unnecessary for saved-byte recovery and are not duplicated here.

Fresh final-source reference and DC review remain pending. Native correctness and byte recovery do not qualify electrical, fabrication or flight performance.
