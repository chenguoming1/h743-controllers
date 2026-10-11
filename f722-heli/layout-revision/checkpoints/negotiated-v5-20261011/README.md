# Local v5 OOM recovery delta

The v5 trial failed after 2266.596 seconds with Java heap exhaustion in exact
statistics capture. Three complete passes ended at 17, 17, 16 required joins;
the original source remained best at 13. No final report or session exists.
All 19 complete checkpoint report/SES/exact-trace triplets, raw exact primitive
baseline, terminal/progress/failure receipts and final static expanded-scope
proposal are preserved. No future 173/cache successor is included or adopted.

Verified byte recovery: 52 new archive objects, 152 exact corrected-v2 objects
reused, 363 restored paths, 204 unique objects. The single-part archive contains
2905572 bytes, SHA-256
d976e477f8ff4e41cf2cba460a9a99dee6eadf503a77496d931be412c370ef40.
All member bytes/order/metadata, part reassembly and restored aliases passed
size/SHA-256/Git-blob checks. Packaging/restore took 2.035 seconds under one CPU,
1 GiB address-space and a 60-second bound, without engineering execution.

Restore the immutable corrected-v2 package first, then:

    python restore.py --repository /path/to/repository --published-workspace /path/to/restored-corrected-v2 --output /path/to/new-v5-workspace

The output must not exist. Omitted generated models/classes and official
artifacts retain their pinned recipes in regeneration-map.json. Exact historical
engineering replay has the documented absolute-path/runtime/receipt bindings;
no engineering rerun or exact router-process resume is claimed.

Corrected-v2 predecessor manifest:
bdecb40f7471f90ac9a59f22bc9d8c213ee90651127d3815b89b7babb06de905.
This is local-only recovery, with no remote availability or publication claim.
Original packages and source files remain unchanged. Native7 remains accepted;
the failed planning candidate is unaccepted and numerical power remains stale.
