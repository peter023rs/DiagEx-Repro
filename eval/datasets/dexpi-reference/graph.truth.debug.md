# P&ID debug report — dexpi-reference.pdf
## Summary

```
nodes:       26    (equipment 7, instrument 4, valve 10, opc 5, text/note 0)
edges:       21    (process 15, sig_elec 1, sig_pneu 2, cap 3)
flags:       unsnapped=0  loose=0  unclassified=2  low_confidence=5
conflicts:   3  [dropped_edge_unsnappable=1, edge_auto_drop_via_v2=2]
dangling:    7    per-page: p1=ok
```
## Page 1

### Equipment (7)

```
zone  label         kind/subtype                             loop  conf      notes
----  ------------  ---------------------------------------  ----  --------  -----
B2    T4750         equipment/tank                                 [high]
C3    H1008         equipment/heat_exchanger·plate                 [high]
B3    FE-66KL21-80  equipment/unclassified_equipment               [low]
A3    H1007         equipment/heat_exchanger·shell_and_tube        [high]
A3    P4711         equipment/pump·centrifugal                     [high]
C3    P4712         equipment/pump·centrifugal                     [high]
B3    RED-80/50     equipment/unclassified_equipment               [medium]
```

### Instruments (4)

```
zone  label          kind/subtype           loop     conf    notes
----  -------------  ---------------------  -------  ------  -----
B1    TICSA 4750.03  instrument/controller  4750.03  [high]
A2    HS 4750.01     instrument/switch      4750.01  [high]
D3    PICSA 4712.02  instrument/controller  4712.02  [high]
C3    PI 4712.01     instrument/indicator   4712.01  [high]
```

### Valves (10)

```
zone  label          kind/subtype             loop     conf      notes
----  -------------  -----------------------  -------  --------  -----
C2    SV 104.01      equipment/safety_relief           [high]
C2    PV 4712.02     equipment/control        4712.02  [high]
D2    TV 4750.03     equipment/control        4750.03  [high]
B2    HV-4750.01     equipment/control                 [high]
C3    V-73KH12-25    equipment                         [low]
D3    V-73KH12-25B   equipment/gate                    [low]
B3    STR-75SA21-80  equipment/strainer                [medium]
B3    CV-73KH12-50A  equipment/check                   [medium]
C4    V-73KH12-50    equipment                         [low]
C4    V-73KH12-25A   equipment/gate                    [low]
```

### OPCs (5)

```
zone  label             kind/subtype  loop  conf      notes
----  ----------------  ------------  ----  --------  -----
A3    OPC-IN-MNb47121   opc/in              [high]
A4    OPC-OUT-WKa47130  opc/in              [medium]
A4    OPC-OUT-WKb47131  opc/out             [medium]
D4    OPC-OUT-QSa47140  opc/out→pQ80        [medium]
D4    OPC-OUT-QSb47141  opc/out→pQ80        [medium]
```
## Edges

### Page 1 (21)

```
id          from                             to                line_id                   flags  conf
----------  ----------------  -------------  ----------------  ------------------------  -----  --------
e-0caf90ae  CV-73KH12-50A     ──process──▶   P4712             73KH12-50                        [medium]
e-a3474375  H1007             ──process──▶   HV-4750.01                                         [medium]
e-459467e0  H1007             ──process──▶   OPC-OUT-WKb47131  WKb 47131 75HB13 50              [high]
e-d66ac55f  H1008             ──process──▶   PV 4712.02                                         [medium]
e-4adb1ae6  H1008             ──process──▶   TV 4750.03                                         [high]
e-fc499fdc  HS 4750.01        ──sig_elec──▶  HV-4750.01                                         [medium]
e-d2704c9c  HV-4750.01        ──process──▶   T4750             MNb 47123 75HB13 80              [medium]
e-d946e964  OPC-IN-MNb47121   ──process──▶   P4711             MNb 47121 75HB13 80              [high]
e-07f6109b  OPC-OUT-QSa47140  ──process──▶   H1008             QSa 47140 75HB13 50 Q 80         [medium]
e-3457358f  OPC-OUT-QSb47141  ──process──▶   H1008             QSb 47141 75HB13 50 Q 80         [medium]
e-a06e7f58  OPC-OUT-WKa47130  ──process──▶   H1007             WKa 47130 75HB13 50              [high]
e-267400e9  P4711             ──process──▶   H1007             MNb 47122 75HB13 80              [high]
e-b219565f  PI 4712.01        ──cap──▶       V-73KH12-25                                        [high]
e-a90c9e3d  PICSA 4712.02     ──sig_pneu──▶  PV 4712.02                                         [high]
e-63e9eaff  PICSA 4712.02     ──cap──▶       V-73KH12-25B      73KH12-25                        [medium]
e-4d42b1e4  RED-80/50         ──process──▶   CV-73KH12-50A                                      [medium]
e-70ec46f9  STR-75SA21-80     ──process──▶   RED-80/50                                          [medium]
e-7f8ad0a6  SV 104.01         ──process──▶   T4750                                              [low]
e-8fcc87c9  T4750             ──process──▶   STR-75SA21-80     MNc 47124 75HB13 80              [medium]
e-5556b7b3  TICSA 4750.03     ──cap──▶       T4750                                              [medium]
e-c85044af  TICSA 4750.03     ──sig_pneu──▶  TV 4750.03                                         [high]
```
## Connection graph

```
CV-73KH12-50A      out: → P4712 (process)
                    in:  ← RED-80/50 (process)
H1007              out: → HV-4750.01 (process), → OPC-OUT-WKb47131 (process)
                    in:  ← P4711 (process), ← OPC-OUT-WKa47130 (process)
H1008              out: → PV 4712.02 (process), → TV 4750.03 (process)
                    in:  ← OPC-OUT-QSa47140 (process), ← OPC-OUT-QSb47141 (process)
HS 4750.01         out: → HV-4750.01 (sig_elec)
                    in:  —
HV-4750.01         out: → T4750 (process)
                    in:  ← H1007 (process), ← HS 4750.01 (sig_elec)
OPC-IN-MNb47121    out: → P4711 (process)
                    in:  —
OPC-OUT-QSa47140   out: → H1008 (process)
                    in:  —
OPC-OUT-QSb47141   out: → H1008 (process)
                    in:  —
OPC-OUT-WKa47130   out: → H1007 (process)
                    in:  —
OPC-OUT-WKb47131   out: —
                    in:  ← H1007 (process)
P4711              out: → H1007 (process)
                    in:  ← OPC-IN-MNb47121 (process)
P4712              out: —
                    in:  ← CV-73KH12-50A (process)
PI 4712.01         out: → V-73KH12-25 (cap)
                    in:  —
PICSA 4712.02      out: → V-73KH12-25B (cap), → PV 4712.02 (sig_pneu)
                    in:  —
PV 4712.02         out: —
                    in:  ← H1008 (process), ← PICSA 4712.02 (sig_pneu)
RED-80/50          out: → CV-73KH12-50A (process)
                    in:  ← STR-75SA21-80 (process)
STR-75SA21-80      out: → RED-80/50 (process)
                    in:  ← T4750 (process)
SV 104.01          out: → T4750 (process)
                    in:  —
T4750              out: → STR-75SA21-80 (process)
                    in:  ← HV-4750.01 (process), ← SV 104.01 (process), ← TICSA 4750.03 (cap)
TICSA 4750.03      out: → TV 4750.03 (sig_pneu), → T4750 (cap)
                    in:  —
TV 4750.03         out: —
                    in:  ← TICSA 4750.03 (sig_pneu), ← H1008 (process)
V-73KH12-25        out: —
                    in:  ← PI 4712.01 (cap)
V-73KH12-25B       out: —
                    in:  ← PICSA 4712.02 (cap)
```
## Conflicts (3)

- **dropped_edge_unsnappable**  p1
  → arbitration: status=skipped_unknown_type  detail=dropped_edge_unsnappable
- **edge_auto_drop_via_v2**
- **edge_auto_drop_via_v2**
## Debugging flags

```
Unsnapped edges (0):       —
Loose-snap edges (0):      —
Low-confidence nodes (5):  FE-66KL21-80@p1, V-73KH12-25A@p1, V-73KH12-25B@p1, V-73KH12-25@p1, V-73KH12-50@p1
Unclassified nodes (2):    FE-66KL21-80@p1, RED-80/50@p1
Dangling OPCs (7):         OPC-IN-MNb47121@p1, OPC-OUT-MNc47126@p1, OPC-OUT-WKa47130@p1, OPC-OUT-WKb47131@p1, OPC-IN-MNc47127@p1, OPC-OUT-QSa47140@p1, OPC-OUT-QSb47141@p1
```
