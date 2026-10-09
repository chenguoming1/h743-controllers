# Bounded native construction from an actual located path

`prepare_located_branch.py` is a read-only proposal generator. It binds the source PCB, exact native export, logical-route map, model and captured engine diagnostics. It accepts one failed single-layer F.Cu/B.Cu trace between adjacent SMD branch terminals. It completes both endpoints at their native pad centers, then removes unnecessary intermediate corners only when the entire replacement segment passes the native geometry screen.

A different logical branch may overlap the proposed trace only within their shared native pad region. Both branches outside that region retain the 0.127 mm physical clearance. The generator refuses existing copper in the selected logical branch, vias, plated terminals, wrong source identity and wrong alias. Multi-layer continuation and THT entry require separate methods.

Run from the ordinary-routing directory with the local analysis dependencies:

```sh
PYTHONPATH=../python-deps python3 prepare_located_branch.py \
  --board candidate21/f722-heli.kicad_pcb \
  --native candidate21/f722-heli.native.json \
  --logical-route-map candidate21/f722-heli.logical-route-map.json \
  --model model-candidate21-ready/model.json \
  --located-receipt tests/local-closures20/port-b-located-path.json \
  --engine-log model-candidate21-ready/short-port-batch.log \
  --logical-net PORT_B_RX_EXT::P0 \
  --out tests/shared-pad-alias21/reproduced-proposal.json

PYTHONPATH=../python-deps python3 tests/shared-pad-alias21/test_located_preparation.py
```

The positive fixture reproduces the exact three segments independently native-verified in frozen candidate22. Negative fixtures reject a different board, a different logical alias and an outside-shared-pad shortcut. The last input/log pair is explicitly synthetic; it is not an engine result. The test checks that source PCB bytes remain unchanged.

This is explicit native route construction after stock insertion failed. The actual engine log remains the provenance, and no engine-success claim is made. A generated proposal still requires intended-net/logical-map assertions, native import and DRC/process/strict-parity gates, actual shared-pad cut, finite full-width entries, source-retention and power/reference applicability checks, and owner adoption.

The new candidate22 historical 2/18 routing-pad-cut count is an NC routing-pad dependency at U14.7. It is not a fully protected port: the actual bonded U14.4 to R32.1 branch remains unfinished. The supplemental count remains 5/7. The separate bonded-I/O coverage audit is authoritative for functional protection interpretation.

`located-path-inventory.json` records all three attempts from the short source21 batch. Only PORT_B_RX_EXT::P0 produced a located trace; neither of the other attempts retained a path that can be constructed by this method. The final SES retained zero new engine geometry.
