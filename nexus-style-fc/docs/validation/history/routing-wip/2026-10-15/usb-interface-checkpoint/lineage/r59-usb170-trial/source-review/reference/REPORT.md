# r57 In3 trunk: nearer-reference correction scope

## Engineering result

For the fixed 0.150/0.127/0.150 mm In3 pair trimmed to north y=110.85, one or two complete In2 donor reroutes cannot restore contiguous nearer GND projection along the full trunk while the other source copper is retained. Six distinct nets have actual copper crossing or overlapping the 0.427 mm projected pair envelope: 5V_BUCK, 3V3 (two regions), 5V, 5V_SENSE, SPI1_MISO, and DSM_DATA. This is a specific fixed-trunk/source-retention obstruction, not a claim that another trunk, layer plan, or coordinated relocation is impossible.

Even granting an optimistic removal of any two entire interfering nets, not just two branches, at least 3.241172 mm of the trunk still has non-GND In2 copper overlapping its envelope. The best pair in that overly generous calculation is SPI1_MISO plus 5V_BUCK. Total union of direct In2 copper projection is 5.685806 mm. Actual rerouting would also have to place all replacement copper somewhere legal; removal here is only a lower-bound thought experiment. No source copper was removed.

A coordinated nearer-reference option must address all six implicated donor/net regions, preserve every complete donor port and branch, and also address the retained IMU_INT and SPI1_SCK via clearance slivers if the goal is GND below the whole pair envelope. Moving In2 tracks alone cannot remove those through-via antipads. Minimum-thickness refill behavior and finite GND connectivity must then be qualified. This report contains no routed replacement and makes no clearance-certified feasibility claim.

An alternative conditional engineering choice is to retain the In2 network and qualify the changing actual reference structure. Both In1 and In4 saved GND cover all seven sampled rays of the trimmed trunk, including all nearer-In2 gaps. That supports considering remote-reference sensitivity cases; it does not certify those as solid finite planes or validate impedance.

## Exact source and method

- Source: `/workspace/scratch/8a35c1f26232/nexus-recovery-20261015/routing-continuation/r57-rpm-center/hardware/nexus-style-fc.kicad_pcb`
- Source SHA-256: `583e73ba08c80e70d42bfd726ef1b440ab0ddf4d7309cef266de486fd03f461f`
- Input trunk-proposal SHA-256: `ca054b1f3124e947bceb980bbb3d1b377d8d36bfceee89ccb252cfb4a8da0383`
- Reviewed and imported only the read-only source_context.py/static_clearance.py parser helpers. build_trunk.py was read, not imported or executed, because its top-level code writes trunk-proposal.json.
- New calculations and reports are confined to this reference/ directory. No native KiCad, refill, PCB write, routing solver, GitHub action, or impedance calculation was performed.
- Center-path length after trim: 13.533168007 mm. Only final endpoint changed analytically from y=110.6 to y=110.85; the source board and input proposal are untouched.
- Common-normal midpoint sample spacing ≤0.001 mm. Ray offsets from center are −0.2135, −0.1385, −0.0635, 0, +0.0635, +0.1385, +0.2135 mm. Numerical interval transitions are uncertain by up to one sample at each boundary; coordinates below are first/last sample centers, not exact boundary roots.
- Direct foreign-copper overlap uses exact capsule/normal-section geometry at each arclength sample, spanning the full 0.427 mm envelope. The 0.200 mm expanded-copper column is an explanatory model from the source In2 GND zone clearance, not a computed refill.
- The closer In2 dielectric is 0.1532 mm, Er 4.16. In4 dielectric is 0.55 mm, Er 4.6. Inner copper is 0.0152 mm. In1 nearest face is 0.7184 mm above the In3 top face (0.1532+0.0152+0.55).

## Retained saved-fill projection

| Reference layer | Center uncovered (mm) | Any of seven rays uncovered (mm) | Source filled-polygon records |
|---|---:|---:|---|
| In1.Cu | 0.000000 | 0.000000 | `9f2a2d78-0e48-4414-9879-4fc68abc23e3:0` |
| In2.Cu | 5.370791 | 7.423624 | `31ebd316-e294-41f0-8942-ba78a56019d4:2`, `31ebd316-e294-41f0-8942-ba78a56019d4:3` |
| In4.Cu | 0.000000 | 0.000000 | `88957e6f-e13e-4cbf-a8e2-1d52ff9863ab:0` |

Filled-polygon indices above are zero-based within the source zone. The records are kept exactly as source data; listing different records does not prove that they are electrically separate, and a single record does not prove adequate finite return connectivity.

All 5.370791 mm of missing In2 center projection have BOTH In1 and In4 saved GND present at the same center samples. For all 7.423624 mm where at least one In2 ray is absent, each of In1 and In4 covers all seven rays. The trim eliminates the prior small In4 endpoint gap. All In2 missing-center and any-ray samples lie inside the union of the six nets’ modeled 0.200 mm clearance corridors; this is a geometric explanation, not a causal refill reconstruction.

### In2 missing-center intervals

| Center-path s interval (mm) | Length (mm) | Approximate coordinate extent (south → north) |
|---|---:|---|
| 0.000000–0.888549 | 0.888549 | (109.65, 123.9995) → (109.65, 123.111951) |
| 3.682063–4.187054 | 0.504991 | (110.5, 120.577949) → (110.5, 120.073957) |
| 5.733028–6.588013 | 0.854985 | (110.5, 118.526984) → (110.5, 117.672999) |
| 8.659977–9.200968 | 0.540991 | (110.5, 115.600034) → (110.5, 115.060044) |
| 9.598961–11.044067 | 1.445106 | (110.5, 114.661051) → (110.75, 113.298984) |
| 12.396999–13.533168 | 1.136169 | (110.75, 111.945051) → (110.9, 110.8505) |

## Exact In2 copper crossings and clearance flanks

Lengths below are projection along the USB center path, not donor track lengths. Overlap lengths between segments/nets must not be added without taking their union. Negative minimum edge distance means direct overlap; positive is a gap.

| Net | Exact segment UUID | Source endpoints (mm) | Direct copper projection (mm) | 0.200 mm clearance projection (mm) | Direct-overlap coordinate extent |
|---|---|---|---:|---:|---|
| 3V3 | `2a635da5-3b33-455f-8eea-4d8dc24d6cb4` | (110.049, 120.326807) → (108.622, 121.748) | 0.000000 | 0.443992 | none |
| 3V3 | `6f662942-269c-4d4a-a0b4-c70c3d6e00bd` | (110.049, 120.326807) → (108.405858, 120.334142) | 0.000000 | 0.443992 | none |
| 3V3 | `9837cc91-103f-4b26-98ea-940dbf296415` | (111.311, 111.452) → (113.042512, 111.443749) | 0.000000 | 0.431459 | none |
| 3V3 | `dddac0b8-a6eb-4faa-886b-aef91aff3830` | (110.124, 110.266) → (111.311, 111.452) | 0.581538 | 0.775186 | (110.9, 111.431038) → (110.9, 110.8505) |
| 3V3 | `ff0813ab-110a-4fad-a12b-2193d305bf36` | (113.614, 120.32) → (110.049, 120.326807) | 0.250996 | 0.650989 | (110.5, 120.450951) → (110.5, 120.200955) |
| DSM_DATA | `bb23b271-f7c2-469d-b1f2-14bc6b5ab3ed` | (112.352669, 113.575) → (110.958432, 112.243745) | 0.155992 | 0.631969 | (110.75, 112.336032) → (110.75, 112.18104) |
| DSM_DATA | `c145da0f-e4d0-45ba-adfd-4d47530b42ed` | (110.958432, 112.243745) → (110.96968, 111.901314) | 0.625289 | 0.938902 | (110.75, 112.307033) → (110.839972, 111.70896) |
| DSM_DATA | `dacfa6a2-e243-418d-b906-6ab881f301fc` | (110.96968, 111.901314) → (110.288331, 111.157574) | 0.506683 | 1.003437 | (110.75, 111.96405) → (110.9, 111.498984) |
| 5V_SENSE | `ad3c97ef-91a0-46c7-bbf8-6e93ce043885` | (111.667142, 114.160008) → (109.484929, 116.348355) | 0.607990 | 1.173980 | (110.5, 115.634034) → (110.5, 115.027044) |
| 5V | `bbe00047-dc38-46b4-8a4c-f425b1d771d7` | (108.825, 119.775) → (111.825, 116.775) | 0.921984 | 1.486974 | (110.5, 118.560983) → (110.5, 117.639999) |
| SPI1_MISO | `5c41153e-c1ee-4a39-b19c-476a7706202d` | (110.575, 113.375) → (109.925, 112.725) | 0.191990 | 0.674966 | (110.75, 113.437977) → (110.75, 113.246986) |
| SPI1_MISO | `9300db13-5a13-4290-9363-14a583a0281c` | (110.575, 113.375) → (110.617426, 114.289757) | 1.083740 | 1.524098 | (110.56939, 114.330695) → (110.75, 113.311983) |
| SPI1_MISO | `e10f9f0f-174a-4f12-82c2-b50db7da1984` | (110.617426, 114.289757) → (109.516071, 115.320402) | 0.499891 | 1.016137 | (110.5, 114.68605) → (110.658109, 114.241891) |
| 5V_BUCK | `6c6696d5-0bd8-4d60-8caf-64b51ab638e1` | (107.364, 121.359) → (112.372, 126.367) | 0.922532 | 1.205388 | (109.65, 123.9995) → (109.65, 123.077968) |

### Per-net unions

| Net | Direct envelope overlap (mm) | 0.200 mm clearance corridor overlap (mm) |
|---|---:|---:|
| 3V3 | 0.832534 | 1.426175 |
| 5V | 0.921984 | 1.486974 |
| 5V_BUCK | 0.922532 | 1.205388 |
| 5V_SENSE | 0.607990 | 1.173980 |
| DSM_DATA | 0.878665 | 1.451415 |
| SPI1_MISO | 1.522103 | 2.079084 |

### Other nearby flanking In2 tracks

These are within 0.75 mm of the projected envelope but do not overlap even the 0.200 mm clearance model. They remain relevant obstacles to a future replacement route.

| Net | UUID | Endpoints | Minimum edge gap (mm) |
|---|---|---|---:|
| 3V3 | `e2ba8598-bb31-40aa-bd4e-bd91933e99b6` | (109.406, 110.266) → (110.124, 110.266) | 0.686200 |
| DSM_DATA | `87e8d54f-5287-4323-90ad-2ba690cc25e3` | (110.288331, 111.157574) → (109.769795, 111.157574) | 0.334669 |
| 5V_SENSE | `6a587d52-e7f1-48fb-9f07-81c4394c4ef3` | (109.484929, 116.348355) → (108.661, 116.339815) | 0.738071 |
| 5V_SENSE | `aa5619ff-873b-4bf3-b7c4-c2e613778cb2` | (112.176, 114.142935) → (111.667142, 114.160008) | 0.645654 |
| SPI1_MISO | `39496a8b-2685-418e-a01f-f57b9b5adcea` | (109.975, 111.575) → (109.925, 111.625) | 0.549371 |
| SPI1_MISO | `806b365a-29b9-4f7d-ba65-fb571efa6279` | (109.516071, 115.320402) → (109.263331, 115.313331) | 0.706929 |
| SPI1_MISO | `e15c5b2a-138d-4e15-ba2e-39ff0416d5c3` | (109.925, 111.625) → (109.925, 112.675) | 0.548000 |
| IMU_CS | `071949d7-2ed8-412a-9603-f5db809d1dfc` | (112.409, 110.215) → (111.610503, 110.264497) | 0.704882 |
| IMU_CS | `91546caa-2776-4d18-a585-2372a009501f` | (111.610503, 110.264497) → (110.528858, 109.112142) | 0.704882 |
| DSM_TX | `42e1b835-88ce-4bb7-a102-7cd5b9a17505` | (107.325, 122.225) → (108.775, 123.675) | 0.598000 |

## Complete donor transactions to preserve

These are whole physically connected same-net In2 source components, computed by copper capsule contact. Every segment UUID and every incident outside-layer segment is retained in complete-donor-ports.json. The shortest required transaction may be a branch rather than the entire component, but any chosen cuts must preserve all affected junctions and ports. A nearby crossing segment by itself is not a complete donor.

### 3V3
- Complete source In2 component: 12 segments, 28.223032 mm total source length.
- Complete via ports:
  - (108.829358, 116.918442): `105831b3-9d66-44f4-81a2-9b52d43006ba`
  - (109.141, 110.56): `3d897835-301a-465b-9f31-fe58c21fcbc5`
  - (108.622, 121.748): `44eb5399-2c82-41bc-8f8d-5685903f1964`
  - (117.746, 116.188): `96ff38f8-fc0d-4fbf-98a6-7958794d7701`
- Complete segment UUIDs: `2a635da5-3b33-455f-8eea-4d8dc24d6cb4`, `4972fc10-ca64-4cc5-b3f3-da27af1383a3`, `6f662942-269c-4d4a-a0b4-c70c3d6e00bd`, `81cec0d0-6321-469a-a0e2-7affe4c441c0`, `9837cc91-103f-4b26-98ea-940dbf296415`, `ab23c3a9-0cd7-4e40-a44f-2e314778aab6`, `d71df7e4-32bd-433f-be6f-31432bb810dd`, `dddac0b8-a6eb-4faa-886b-aef91aff3830`, `de88d3fe-731a-4d33-8b6f-4eb1ad293f11`, `e2ba8598-bb31-40aa-bd4e-bd91933e99b6`, `f18394fc-b364-4888-aeeb-57da14e94f19`, `ff0813ab-110a-4fad-a12b-2193d305bf36`

### 5V
- Complete source In2 component: 3 segments, 4.942641 mm total source length.
- Complete via ports:
  - (108.525, 119.775): `194f233c-6975-4ca0-97d3-264326e7f356`
  - (111.825, 116.375): `d765ec86-064a-49a8-bd25-1c2ed606abde`
- Complete segment UUIDs: `0e95630e-44fa-46df-9061-6087dbf9c99e`, `80012e0f-0384-482a-a105-a604e8290608`, `bbe00047-dc38-46b4-8a4c-f425b1d771d7`

### 5V_BUCK
- Complete source In2 component: 4 segments, 17.512623 mm total source length.
- Complete via ports:
  - (114.213, 126.367): `6da53a85-5dfd-42e0-9d17-30fa99cf293a`
  - (104.575, 113.925): `a33d9038-104a-4904-836a-f2c168df6d4c`
- Complete segment UUIDs: `6c6696d5-0bd8-4d60-8caf-64b51ab638e1`, `ab3e6f5d-97cb-4629-8dd6-88d9ff0b75bd`, `aec15c0e-391f-40fd-b2e6-a9bcac740aeb`, `f7930e38-b8bf-43ea-bf85-f997a3632566`

### 5V_SENSE
- Complete source In2 component: 5 segments, 5.658357 mm total source length.
- Complete via ports:
  - (108.461, 116.140815): `18a99482-dc02-4eab-a4d5-027591e1b2b2`
  - (112.867689, 114.797995): `4c8b79af-68bd-4e72-ab67-315fc898e40d`
- Complete segment UUIDs: `4fb716cc-9707-4276-bbe2-bb7572994fca`, `5f0f8c1d-528b-4b75-b254-541aa2b96a3a`, `6a587d52-e7f1-48fb-9f07-81c4394c4ef3`, `aa5619ff-873b-4bf3-b7c4-c2e613778cb2`, `ad3c97ef-91a0-46c7-bbf8-6e93ce043885`

### DSM_DATA
- Complete source In2 component: 15 segments, 26.783872 mm total source length.
- Complete via ports:
  - (101.375, 111.675): `b8a4a05a-c4fe-471c-9774-9ae6eb8ba5bd`
  - (113.225, 113.575): `e79d29fc-3fbc-43e0-b5d6-54e6a9022da7`
- Complete segment UUIDs: `0c0b060d-12fa-4b11-b100-019c978df58e`, `0fd631d7-2a04-46b8-9d86-b6d6fc46fa7e`, `28881ec4-4a2c-4ddc-bd8a-469fc5af5692`, `30710790-4e0b-459a-a62f-d5873fc3ac53`, `4a8edaa1-b102-4207-82c7-622d6c351f52`, `82b2f45c-a273-4745-a603-f3901db1c9fc`, `87e8d54f-5287-4323-90ad-2ba690cc25e3`, `8f8ab239-441d-4935-b778-fa5f611032d7`, `97c13329-2e7d-4d4f-aea4-a4159a9a10e1`, `ac642dcd-c3c9-4b0b-8607-030b4dfaccb8`, `bb23b271-f7c2-469d-b1f2-14bc6b5ab3ed`, `c145da0f-e4d0-45ba-adfd-4d47530b42ed`, `dacfa6a2-e243-418d-b906-6ab881f301fc`, `e0c1e805-0cbd-414b-a762-9ee36f017b06`, `ede7822e-a074-4220-acb9-a96ce6359396`

### SPI1_MISO
- Complete source In2 component: 7 segments, 7.882387 mm total source length.
- Complete via ports:
  - (109.975, 111.575): `5f46e9a4-f918-4841-852c-5aabd6a859b8`
  - (107.025, 113.075): `b1c41908-3ba5-4d27-b159-317c96a1d849`
- Complete segment UUIDs: `39496a8b-2685-418e-a01f-f57b9b5adcea`, `5c41153e-c1ee-4a39-b19c-476a7706202d`, `806b365a-29b9-4f7d-ba65-fb571efa6279`, `9300db13-5a13-4290-9363-14a583a0281c`, `be46a131-99e1-4e29-a570-e3de9937391d`, `e10f9f0f-174a-4f12-82c2-b50db7da1984`, `e15c5b2a-138d-4e15-ba2e-39ff0416d5c3`

For 3V3, the common via at (117.746,116.188) divides the north supply run from the southern branched tree. Both sides affect this USB trunk: the north diagonal crosses at y≈111.04, while the southern horizontal crosses at y≈120.326. The south tree has a junction at (110.049,120.326807) and ports at (108.622,121.748) and (108.829358,116.918442). Preserving only one of those branches would leave an incomplete donor. The whole 12-segment component has four via ports.

SPI1_MISO is the most bounded useful single donor for the middle-upper gap: seven source In2 segments between (109.975,111.575) and (107.025,113.075), 7.882387 mm. 5V_SENSE is another bounded donor: five segments between (108.461,116.140815) and (112.867689,114.797995), 5.658357 mm. Addressing those two is a conditional partial improvement only: 5V_BUCK, 5V, DSM_DATA and both 3V3 crossing regions remain. DSM_DATA’s complete same-layer path extends to (101.375,111.675); a short local cut would need explicit retained intermediate ports and complete replacement, not truncation.

## Additional retained through-via edge obstructions

The two following via copper lands do not directly overlap the proposed pair envelope, but their source-zone 0.200 mm clearances reach its edge. Both vias remain on In2 even though their attached tracks are on outer layers. Moving either requires a complete fanout/transition transaction, not just removing its In2 appearance.

### IMU_INT: `33fe43e9-c4cc-45bc-a9cc-df1353a05aaf`
- At (110.14, 113.659); diameter 0.450 mm; edge distance to envelope 0.171500 mm.
- Source-zone clearance corridor intersects 0.305985 mm of trunk: (110.75, 113.811958) → (110.75, 113.506973).
- Retained incident source segments:
  - F.Cu `eb3fcf6d-c315-45ca-9570-ad62f8bffe42`: (110.14, 113.659) → (110.14, 113.15)
  - B.Cu `873405e4-8db6-403f-981e-9198c6430054`: (110.371, 113.659) → (112.903128, 111.133442)
  - B.Cu `98099883-a9e5-48a2-bb14-762cd08541fe`: (110.14, 113.659) → (110.371, 113.659)

### SPI1_SCK: `6cefe031-faec-4489-9649-f1d8d8274b4f`
- At (111.383295, 112.062456); diameter 0.450 mm; edge distance to envelope 0.194795 mm.
- Source-zone clearance corridor intersects 0.131993 mm of trunk: (110.75, 112.128042) → (110.75, 111.997049).
- Retained incident source segments:
  - F.Cu `1e5280a2-eb87-4195-8fec-2115f2d627ec`: (111.4, 111.39) → (111.383295, 112.062456)
  - B.Cu `818134af-637b-4809-a57f-c8dbc37e7619`: (110.559173, 112.063666) → (111.383295, 112.062456)

## Decision boundary and remaining qualification

1. If continuous closer In2 reference across this fixed trunk is mandatory, authorize a larger coordinated donor study. Preserve the six complete donor/net transactions and both potentially affected transition vias; screen all mutual and retained-copper clearances before any board edit.
2. If moving only one or two donors is the limit, treat that as partial reference improvement. It cannot make the full fixed trunk uniformly referenced to In2 because four or more independent direct-copper crossings remain even under optimistic net removal.
3. If existing copper is to remain, retain the remote In1/In4 cases in the analytical sensitivity study. Do not call the In2 missing region free space or assume the two remote references are finite electrically solid planes.
4. Any implementation still needs actual post-refill projection, complete donor and USB connectivity, finite GND return analysis, native DRC, via/launch treatment, and manufacturing stack qualification. No route or fill implementation is provided here.

## Files

- reference-analysis.json: all source objects, per-object projection intervals and coordinates, numerical union summaries, and retained-fill coverage.
- complete-donor-ports.json: every segment in each complete donor component, all via ports, all outside-layer incident source tracks, and the two extra through-via obstructions.
- In1.Cu-fill-components.json, In2.Cu-fill-components.json, In4.Cu-fill-components.json: exact retained source fill record identities and coverage.
- numerical-projection.npz: reproducible common-normal sample arrays and saved-fill membership.
- saved-reference-and-crossings.png: inspected visualization of the three retained reference layers, donor crossings and proposed pair.
- study_reference.py, trace_donors.py, plot_reference.py, write_report.py: read-only analysis/report scripts.
- SHA256SUMS: artifact hashes.
