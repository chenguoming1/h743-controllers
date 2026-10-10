# R38 portal local exit receipt

Source board SHA256: 1ee7174a578dffe4d5ef3ae8b39d8dc88f28b80395539263a65f23be234c21e6
Sealed joint proof SHA256: 27f2c81539a92809d4f9c6ae0ea593193881780936f8cbd6641da14307d0b4bd

Origin (18.45, 24.095), 0.127 mm trace width, exact declared BEC reconstruction. Eight straight cardinal/diagonal spokes per layer, limited to 1 mm Euclidean length. North is decreasing PCB y. Existing joint proof was not changed.

## Positive full 1 mm exits

- F.Cu W: endpoint [17.45, 24.095]; minimum extra clearance 0.253624577 mm, nearest 80402d8b-9dab-4fd2-90a9-4008470e25fb (RPM_LV).
- In2.Cu SE: endpoint [19.157106781186545, 24.802106781186545]; minimum extra clearance 0.230747551 mm, nearest fca836a9-bf7d-4116-be41-0e8a09f2be2f (+3V3_DSM).
- In2.Cu SW: endpoint [17.742893218813453, 24.802106781186545]; minimum extra clearance 0.236581859 mm, nearest fca836a9-bf7d-4116-be41-0e8a09f2be2f (+3V3_DSM).
- In2.Cu W: endpoint [17.45, 24.095]; minimum extra clearance 0.236581859 mm, nearest fca836a9-bf7d-4116-be41-0e8a09f2be2f (+3V3_DSM).
- In2.Cu NW: endpoint [17.742893218813453, 23.387893218813453]; minimum extra clearance 0.236581859 mm, nearest fca836a9-bf7d-4116-be41-0e8a09f2be2f (+3V3_DSM).
- In2.Cu N: endpoint [18.45, 23.095]; minimum extra clearance 0.038197893 mm, nearest fca836a9-bf7d-4116-be41-0e8a09f2be2f (+3V3_DSM).
- In3.Cu E: endpoint [19.45, 24.095]; minimum extra clearance 0.029500000 mm, nearest 4c4a4e4b-4d3a-4b90-8e5a-85f800b56adb (+3V3_DSM).
- In3.Cu N: endpoint [18.45, 23.095]; minimum extra clearance 0.159500000 mm, nearest 4c4a4e4b-4d3a-4b90-8e5a-85f800b56adb (+3V3_DSM).

## First straight-spoke barriers

- F.Cu E: safe rounded prefix 0.3586 mm; first barrier 80402d8b-9dab-4fd2-90a9-4008470e25fb (RPM_LV).
- F.Cu SE: safe rounded prefix 0.2536 mm; first barrier 80402d8b-9dab-4fd2-90a9-4008470e25fb (RPM_LV).
- F.Cu S: safe rounded prefix 0.3248 mm; first barrier 6222d56c-8217-4bf9-a662-c5b479fcd654 (RPM_LV).
- F.Cu SW: safe rounded prefix 0.6445 mm; first barrier 6222d56c-8217-4bf9-a662-c5b479fcd654 (RPM_LV).
- F.Cu NW: safe rounded prefix 0.9652 mm; first barrier a6b2551f-da4e-4c73-97c3-13db055b8165 (SBUS_HV).
- F.Cu N: safe rounded prefix 0.6900 mm; first barrier ba723236-9e41-4526-8f25-7bfbbde14b83 (SBUS_HV).
- F.Cu NE: safe rounded prefix 0.3160 mm; first barrier 4c4a4e4b-4d3a-4b90-8e5a-85f800b56adb (+3V3_DSM).
- In2.Cu E: safe rounded prefix 0.3686 mm; first barrier fca836a9-bf7d-4116-be41-0e8a09f2be2f (+3V3_DSM).
- In2.Cu S: safe rounded prefix 0.9874 mm; first barrier board-outline-including-npth (None).
- In2.Cu NE: safe rounded prefix 0.2394 mm; first barrier fca836a9-bf7d-4116-be41-0e8a09f2be2f (+3V3_DSM).
- In3.Cu SE: safe rounded prefix 0.2718 mm; first barrier replacement-BEC-In3-centerline (+5V_BEC).
- In3.Cu S: safe rounded prefix 0.1967 mm; first barrier replacement-BEC-In3-centerline (+5V_BEC).
- In3.Cu SW: safe rounded prefix 0.2849 mm; first barrier replacement-BEC-In3-centerline (+5V_BEC).
- In3.Cu W: safe rounded prefix 0.2594 mm; first barrier replacement-BEC-In3-centerline (+5V_BEC).
- In3.Cu NW: safe rounded prefix 0.3669 mm; first barrier replacement-BEC-In3-centerline (+5V_BEC).
- In3.Cu NE: safe rounded prefix 0.3160 mm; first barrier 4c4a4e4b-4d3a-4b90-8e5a-85f800b56adb (+3V3_DSM).

This demonstrates specific usable local exits, not connectivity to the MCU/R71 tree or a global topology result. Prefix limits concern straight spokes only; bends can continue beyond them. The exact source-bound receipt contains native distance witnesses and full constraint identities.
