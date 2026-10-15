"""Generate the read-only reference review report from the saved analysis."""
from pathlib import Path
import json,hashlib,itertools
R=Path('/workspace/shared/nexus-usb-stack-review/r57-inner-pair/reference');r=json.loads((R/'reference-analysis.json').read_text());d=json.loads((R/'complete-donor-ports.json').read_text())
def pt(x):return '('+', '.join(f'{v:.6f}'.rstrip('0').rstrip('.') for v in x)+')'
def ivs(xs):return '; '.join(pt(x['first_sample_mm'])+' → '+pt(x['last_sample_mm']) for x in xs) or 'none'
lines=['# r57 In3 trunk: nearer-reference correction scope','',
'## Engineering result','',
'For the fixed 0.150/0.127/0.150 mm In3 pair trimmed to north y=110.85, one or two complete In2 donor reroutes cannot restore contiguous nearer GND projection along the full trunk while the other source copper is retained. Six distinct nets have actual copper crossing or overlapping the 0.427 mm projected pair envelope: 5V_BUCK, 3V3 (two regions), 5V, 5V_SENSE, SPI1_MISO, and DSM_DATA. This is a specific fixed-trunk/source-retention obstruction, not a claim that another trunk, layer plan, or coordinated relocation is impossible.','',
'Even granting an optimistic removal of any two entire interfering nets, not just two branches, at least 3.241172 mm of the trunk still has non-GND In2 copper overlapping its envelope. The best pair in that overly generous calculation is SPI1_MISO plus 5V_BUCK. Total union of direct In2 copper projection is 5.685806 mm. Actual rerouting would also have to place all replacement copper somewhere legal; removal here is only a lower-bound thought experiment. No source copper was removed.','',
'A coordinated nearer-reference option must address all six implicated donor/net regions, preserve every complete donor port and branch, and also address the retained IMU_INT and SPI1_SCK via clearance slivers if the goal is GND below the whole pair envelope. Moving In2 tracks alone cannot remove those through-via antipads. Minimum-thickness refill behavior and finite GND connectivity must then be qualified. This report contains no routed replacement and makes no clearance-certified feasibility claim.','',
'An alternative conditional engineering choice is to retain the In2 network and qualify the changing actual reference structure. Both In1 and In4 saved GND cover all seven sampled rays of the trimmed trunk, including all nearer-In2 gaps. That supports considering remote-reference sensitivity cases; it does not certify those as solid finite planes or validate impedance.','',
'## Exact source and method','',f'- Source: `{r["source"]}`',f'- Source SHA-256: `{r["source_sha256"]}`',f'- Input trunk-proposal SHA-256: `{r["trunk_proposal_sha256"]}`',
'- Reviewed and imported only the read-only source_context.py/static_clearance.py parser helpers. build_trunk.py was read, not imported or executed, because its top-level code writes trunk-proposal.json.',
'- New calculations and reports are confined to this reference/ directory. No native KiCad, refill, PCB write, routing solver, GitHub action, or impedance calculation was performed.',
f'- Center-path length after trim: {r["trunk_center_length_mm"]:.9f} mm. Only final endpoint changed analytically from y=110.6 to y=110.85; the source board and input proposal are untouched.',
'- Common-normal midpoint sample spacing ≤0.001 mm. Ray offsets from center are −0.2135, −0.1385, −0.0635, 0, +0.0635, +0.1385, +0.2135 mm. Numerical interval transitions are uncertain by up to one sample at each boundary; coordinates below are first/last sample centers, not exact boundary roots.',
'- Direct foreign-copper overlap uses exact capsule/normal-section geometry at each arclength sample, spanning the full 0.427 mm envelope. The 0.200 mm expanded-copper column is an explanatory model from the source In2 GND zone clearance, not a computed refill.',
'- The closer In2 dielectric is 0.1532 mm, Er 4.16. In4 dielectric is 0.55 mm, Er 4.6. Inner copper is 0.0152 mm. In1 nearest face is 0.7184 mm above the In3 top face (0.1532+0.0152+0.55).','',
'## Retained saved-fill projection','',
'| Reference layer | Center uncovered (mm) | Any of seven rays uncovered (mm) | Source filled-polygon records |','|---|---:|---:|---|']
for l in ['In1.Cu','In2.Cu','In4.Cu']:
 f=json.loads((R/(l+'-fill-components.json')).read_text());c=r['coverage'][l]
 lines.append(f'| {l} | {c["center_uncovered_mm"]:.6f} | {c["any_seven_line_uncovered_mm"]:.6f} | '+', '.join('`'+x['source_fill']['id']+'`' for x in f)+' |')
lines+=['','Filled-polygon indices above are zero-based within the source zone. The records are kept exactly as source data; listing different records does not prove that they are electrically separate, and a single record does not prove adequate finite return connectivity.','',
'All 5.370791 mm of missing In2 center projection have BOTH In1 and In4 saved GND present at the same center samples. For all 7.423624 mm where at least one In2 ray is absent, each of In1 and In4 covers all seven rays. The trim eliminates the prior small In4 endpoint gap. All In2 missing-center and any-ray samples lie inside the union of the six nets’ modeled 0.200 mm clearance corridors; this is a geometric explanation, not a causal refill reconstruction.','',
'### In2 missing-center intervals','',
'| Center-path s interval (mm) | Length (mm) | Approximate coordinate extent (south → north) |','|---|---:|---|']
for x in r['coverage']['In2.Cu']['center_uncovered_intervals']:lines.append(f'| {x["s_start_mm"]:.6f}–{x["s_end_mm"]:.6f} | {x["projected_centerline_length_mm"]:.6f} | {ivs([x])} |')
lines+=['','## Exact In2 copper crossings and clearance flanks','',
'Lengths below are projection along the USB center path, not donor track lengths. Overlap lengths between segments/nets must not be added without taking their union. Negative minimum edge distance means direct overlap; positive is a gap.','',
'| Net | Exact segment UUID | Source endpoints (mm) | Direct copper projection (mm) | 0.200 mm clearance projection (mm) | Direct-overlap coordinate extent |','|---|---|---|---:|---:|---|']
for t in r['non_ground_in2_tracks']:
 if t['projected_0200_zone_clearance_overlap_mm']<=0:continue
 s=t['source'];lines.append(f'| {s["net"]} | `{s["uuid"]}` | {pt(s["start"])} → {pt(s["end"])} | {t["projected_copper_overlap_mm"]:.6f} | {t["projected_0200_zone_clearance_overlap_mm"]:.6f} | {ivs(t["copper_overlap_intervals"])} |')
lines+=['','### Per-net unions','',
'| Net | Direct envelope overlap (mm) | 0.200 mm clearance corridor overlap (mm) |','|---|---:|---:|']
for n in r['by_net']:
 if n['union_projected_0200_clearance_overlap_mm']:lines.append(f'| {n["net"]} | {n["union_projected_copper_overlap_mm"]:.6f} | {n["union_projected_0200_clearance_overlap_mm"]:.6f} |')
lines+=['','### Other nearby flanking In2 tracks','',
'These are within 0.75 mm of the projected envelope but do not overlap even the 0.200 mm clearance model. They remain relevant obstacles to a future replacement route.','',
'| Net | UUID | Endpoints | Minimum edge gap (mm) |','|---|---|---|---:|']
for t in r['non_ground_in2_tracks']:
 if t['projected_0200_zone_clearance_overlap_mm']>0:continue
 s=t['source'];lines.append(f'| {s["net"]} | `{s["uuid"]}` | {pt(s["start"])} → {pt(s["end"])} | {t["minimum_edge_distance_to_envelope_mm"]:.6f} |')
lines+=['','## Complete donor transactions to preserve','',
'These are whole physically connected same-net In2 source components, computed by copper capsule contact. Every segment UUID and every incident outside-layer segment is retained in complete-donor-ports.json. The shortest required transaction may be a branch rather than the entire component, but any chosen cuts must preserve all affected junctions and ports. A nearby crossing segment by itself is not a complete donor.','']
for c in d['complete_same_net_in2_components']:
 lines += [f'### {c["net"]}',f'- Complete source In2 component: {c["segment_count"]} segments, {c["total_source_length_mm"]:.6f} mm total source length.','- Complete via ports:']
 for p in c['via_ports']:
  v=p['source'];lines.append(f'  - {pt(v["at"])}: `{v["uuid"]}`')
 lines += ['- Complete segment UUIDs: '+', '.join('`'+t['uuid']+'`' for t in c['segments']), '']
lines+=['For 3V3, the common via at (117.746,116.188) divides the north supply run from the southern branched tree. Both sides affect this USB trunk: the north diagonal crosses at y≈111.04, while the southern horizontal crosses at y≈120.326. The south tree has a junction at (110.049,120.326807) and ports at (108.622,121.748) and (108.829358,116.918442). Preserving only one of those branches would leave an incomplete donor. The whole 12-segment component has four via ports.','',
'SPI1_MISO is the most bounded useful single donor for the middle-upper gap: seven source In2 segments between (109.975,111.575) and (107.025,113.075), 7.882387 mm. 5V_SENSE is another bounded donor: five segments between (108.461,116.140815) and (112.867689,114.797995), 5.658357 mm. Addressing those two is a conditional partial improvement only: 5V_BUCK, 5V, DSM_DATA and both 3V3 crossing regions remain. DSM_DATA’s complete same-layer path extends to (101.375,111.675); a short local cut would need explicit retained intermediate ports and complete replacement, not truncation.','',
'## Additional retained through-via edge obstructions','',
'The two following via copper lands do not directly overlap the proposed pair envelope, but their source-zone 0.200 mm clearances reach its edge. Both vias remain on In2 even though their attached tracks are on outer layers. Moving either requires a complete fanout/transition transaction, not just removing its In2 appearance.','']
for x in d['additional_retained_via_clearance_obstructions']:
 v=x['source'];lines += [f'### {v["net"]}: `{v["uuid"]}`',f'- At {pt(v["at"])}; diameter {v["diameter"]:.3f} mm; edge distance to envelope {x["minimum_edge_distance_to_envelope_mm"]:.6f} mm.',f'- Source-zone clearance corridor intersects {x["projected_0200_zone_clearance_overlap_mm"]:.6f} mm of trunk: {ivs(x["clearance_overlap_intervals"])}.', '- Retained incident source segments:']
 for t in x['source_incident_tracks']:lines.append(f'  - {t["layer"]} `{t["uuid"]}`: {pt(t["start"])} → {pt(t["end"])}')
 lines.append('')
lines+=['## Decision boundary and remaining qualification','',
'1. If continuous closer In2 reference across this fixed trunk is mandatory, authorize a larger coordinated donor study. Preserve the six complete donor/net transactions and both potentially affected transition vias; screen all mutual and retained-copper clearances before any board edit.',
'2. If moving only one or two donors is the limit, treat that as partial reference improvement. It cannot make the full fixed trunk uniformly referenced to In2 because four or more independent direct-copper crossings remain even under optimistic net removal.',
'3. If existing copper is to remain, retain the remote In1/In4 cases in the analytical sensitivity study. Do not call the In2 missing region free space or assume the two remote references are finite electrically solid planes.',
'4. Any implementation still needs actual post-refill projection, complete donor and USB connectivity, finite GND return analysis, native DRC, via/launch treatment, and manufacturing stack qualification. No route or fill implementation is provided here.','',
'## Files','',
'- reference-analysis.json: all source objects, per-object projection intervals and coordinates, numerical union summaries, and retained-fill coverage.',
'- complete-donor-ports.json: every segment in each complete donor component, all via ports, all outside-layer incident source tracks, and the two extra through-via obstructions.',
'- In1.Cu-fill-components.json, In2.Cu-fill-components.json, In4.Cu-fill-components.json: exact retained source fill record identities and coverage.',
'- numerical-projection.npz: reproducible common-normal sample arrays and saved-fill membership.',
'- saved-reference-and-crossings.png: inspected visualization of the three retained reference layers, donor crossings and proposed pair.',
'- study_reference.py, trace_donors.py, plot_reference.py, write_report.py: read-only analysis/report scripts.',
'- SHA256SUMS: artifact hashes.']
(R/'REPORT.md').write_text('\n'.join(lines)+'\n')
source=Path(r['source']);assert hashlib.sha256(source.read_bytes()).hexdigest()==r['source_sha256']
files=sorted(p for p in R.iterdir() if p.is_file() and p.name!='SHA256SUMS')
(R/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in files))
print((R/'SHA256SUMS').read_text())
