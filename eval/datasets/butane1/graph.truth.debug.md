# P&ID debug report — butane1.pdf
## Summary

```
nodes:       58    (equipment 7, instrument 41, valve 1, opc 6, text/note 3)
edges:       12    (process 9, sig_elec 3)
flags:       unsnapped=0  loose=1  unclassified=1  low_confidence=0
conflicts:   36  [dropped_edge_unsnappable=7, edge_auto_drop_via_v2=11, unstitched_line_endpoint=18]
dangling:    6    per-page: p1=ok
```
## Page 1

### Equipment (7)

```
zone  label           kind/subtype                             loop  conf      notes
----  --------------  ---------------------------------------  ----  --------  -----
B1    E-234-009       equipment/heat_exchanger·air_cooler            [high]
B2    HY-2903A        equipment/instrument                           [medium]
B2    HY-2903B        equipment/instrument                           [medium]
B2    E-234-009 Fan1  equipment/other                                [high]
B2    E-234-009 Fan2  equipment/other                                [high]
C2    E-234-010A      equipment/heat_exchanger·shell_and_tube        [high]
C3    E-234-010B      equipment/heat_exchanger·shell_and_tube        [high]
```

### Instruments (41)

```
zone  label                   kind/subtype                        loop  conf    notes
----  ----------------------  ----------------------------------  ----  ------  -----
C1    TI-2917 HH              instrument/indicator                2917  [high]
B1    TY-2911                 instrument/valve_actuator           2911  [high]
A1    TI-2909                 instrument/indicator                2909  [high]
B1    TIC-2911                instrument/indicator                2911  [high]
C1    PSD-2917                instrument/switch                   2917  [high]
A1    TT-2909                 instrument/transmitter              2909  [high]
A1    TG-2910                 instrument/indicator                2910  [high]
B1    TT-2911                 instrument/transmitter              2911  [high]
C1    TG-2912                 instrument/indicator                2912  [high]
C1    TT-2917                 instrument/transmitter              2917  [high]
D2    PSV-2907                instrument/valve_actuator                 [high]
B2    HIC-2903A               instrument/indicator                2903  [high]
B2    HIC-2903B               instrument/indicator                2903  [high]
C2    VB-2911                 instrument/unclassified_instrument  2911  [high]
D2    TI-2916                 instrument/indicator                2916  [high]
A2    HS-2901A                instrument/switch                   2901  [high]
B2    VSHH-2901A              instrument/switch                   2901  [high]
B2    VSHH-2901B              instrument/switch                   2901  [high]
B2    HS-2901B                instrument/switch                   2901  [high]
D2    PG-2913                 instrument/indicator                2913  [high]
D2    TT-2916                 instrument/transmitter              2916  [high]
D2    TG-2917                 instrument/indicator                2917  [high]
B2    VA-2901B                instrument/alarm                    2901  [high]
A2    VA-2901A                instrument/alarm                    2901  [high]
B2    HS-2901A1 LOCAL/REMOTE  instrument/switch                   2901  [high]
B2    HS-2901B1 LOCAL/REMOTE  instrument/switch                   2901  [high]
A2    ESD-3200                instrument/switch                   3200  [high]
B2    ESD-3200                instrument/switch                   3200  [high]
A2    HS-2901A2 STOP/START    instrument/switch                   2901  [high]
B2    HS-2901B2 STOP/START    instrument/switch                   2901  [high]
B2    XI-2901A AVAILABLE      instrument/indicator                2901  [high]
B2    XI-2901B AVAILABLE      instrument/indicator                2901  [high]
B3    XL-2901B RUNNING/STOP   instrument/indicator                2901  [high]
B3    XA-2901B FAULT          instrument/alarm                    2901  [high]
B3    XA-2901A FAULT          instrument/alarm                    2901  [high]
B3    XL-2901A RUNNING/STOP   instrument/indicator                2901  [high]
C3    TW-2922                 instrument/element                  2922  [high]
C3    TW-2921                 instrument/element                  2921  [high]
C3    PG-2914                 instrument/indicator                2914  [high]
B4    TI-2913 H               instrument/indicator                2913  [high]
C4    TT-2913                 instrument/transmitter              2913  [high]
```

### Valves (1)

```
zone  label    kind/subtype         loop  conf    notes
----  -------  -------------------  ----  ------  -----
A1    KV-2904  equipment/three_way        [high]
```

### OPCs (6)

```
zone  label                                                                            kind/subtype           loop  conf    notes
----  -------------------------------------------------------------------------------  ---------------------  ----  ------  -----
D1    OPC OUT: Spent Butane to V-234-004 (P-234-03303-CD3D-2"-N)                       opc/out→p234-3.00-035        [high]
D1    OPC IN: Min Flow from P-234-002A/B (P-234-03505-CD3D-3"-N)                       opc/in→p234-3.00-035         [high]
A1    OPC IN: Spent Butane from V-234-002A~D (P-234-03016-F3D-8"-Is)                   opc/in→p234-3.00-031         [high]
D2    OPC OUT: Sea Water Return to 237-3.00-050 (SWR-234-03301-115201D-10"-N)          opc/out→p237-3.00-050        [high]
D3    OPC IN: Sea Water Supply from 234-3.00-027 (SWS-234-03301-115201D-10"-N)         opc/in→p234-3.00-027         [high]
D4    OPC OUT: Spent Butane (Cooling/Filling) to F-234-004A/B (P-234-03302-CD3D-6"-N)  opc/out→p234-3.00-034        [high]
```

### Text/notes (3)

```
zone  label                                          kind/subtype  loop  conf      notes
----  ---------------------------------------------  ------------  ----  --------  -----
B2    MCC motor control center (fan A &amp; B)       note                [medium]
B2    SEQ sequencer (auto-start sequencer for fans)  note                [medium]
A2    SEQ sequencer - fan A                          note                [medium]
```
## Edges

### Page 1 (12)

```
id          from                                                                                     to                                                                               line_id                     flags           conf
----------  ------------------------------------------------------------------------  -------------  -------------------------------------------------------------------------------  --------------------------  --------------  ------
e-b00a2c87  E-234-009                                                                 ──process──▶   E-234-010A                                                                                                                   [high]
e-d2d85b3a  E-234-009                                                                 ──process──▶   OPC OUT: Spent Butane to V-234-004 (P-234-03303-CD3D-2"-N)                       P-234-03301-CD3D-8"-N       INFERRED_LOOSE  [high]
e-cff48257  E-234-010A                                                                ──process──▶   OPC OUT: Sea Water Return to 237-3.00-050 (SWR-234-03301-115201D-10"-N)          SWR-234-03302-115201D-1"-N                  [high]
e-c9f286ee  E-234-010B                                                                ──process──▶   E-234-010A                                                                                                                   [high]
e-f0a8ad73  E-234-010B                                                                ──process──▶   OPC OUT: Spent Butane (Cooling/Filling) to F-234-004A/B (P-234-03302-CD3D-6"-N)                                              [high]
e-57af5691  KV-2904                                                                   ──process──▶   E-234-009                                                                                                                    [high]
e-59a1658e  MCC motor control center (fan A &amp; B)                                  ──sig_elec──▶  E-234-009 Fan1                                                                                                               [high]
e-ef6a00e3  MCC motor control center (fan A &amp; B)                                  ──sig_elec──▶  E-234-009 Fan2                                                                                                               [high]
e-657ce53d  OPC IN: Min Flow from P-234-002A/B (P-234-03505-CD3D-3"-N)                ──process──▶   E-234-010A                                                                                                                   [high]
e-993cf6df  OPC IN: Sea Water Supply from 234-3.00-027 (SWS-234-03301-115201D-10"-N)  ──process──▶   E-234-010B                                                                                                                   [high]
e-39ec6c2d  OPC IN: Spent Butane from V-234-002A~D (P-234-03016-F3D-8"-Is)            ──process──▶   KV-2904                                                                          P-234-03016-F3D-8"-Is                       [high]
e-945da1db  TIC-2911                                                                  ──sig_elec──▶  TY-2911                                                                                                                      [high]
```
## Connection graph

```
E-234-009                                                                         out: → OPC OUT: Spent Butane to V-234-004 (P-234-03303-CD3D-2"-N) (process), → E-234-010A (process)
                                                                                   in:  ← KV-2904 (process)
E-234-009 Fan1                                                                    out: —
                                                                                   in:  ← MCC motor control center (fan A &amp; B) (sig_elec)
E-234-009 Fan2                                                                    out: —
                                                                                   in:  ← MCC motor control center (fan A &amp; B) (sig_elec)
E-234-010A                                                                        out: → OPC OUT: Sea Water Return to 237-3.00-050 (SWR-234-03301-115201D-10"-N) (process)
                                                                                   in:  ← E-234-009 (process), ← E-234-010B (process), ← OPC IN: Min Flow from P-234-002A/B (P-234-03505-CD3D-3"-N) (process)
E-234-010B                                                                        out: → E-234-010A (process), → OPC OUT: Spent Butane (Cooling/Filling) to F-234-004A/B (P-234-03302-CD3D-6"-N) (process)
                                                                                   in:  ← OPC IN: Sea Water Supply from 234-3.00-027 (SWS-234-03301-115201D-10"-N) (process)
KV-2904                                                                           out: → E-234-009 (process)
                                                                                   in:  ← OPC IN: Spent Butane from V-234-002A~D (P-234-03016-F3D-8"-Is) (process)
MCC motor control center (fan A &amp; B)                                          out: → E-234-009 Fan1 (sig_elec), → E-234-009 Fan2 (sig_elec)
                                                                                   in:  —
OPC IN: Min Flow from P-234-002A/B (P-234-03505-CD3D-3"-N)                        out: → E-234-010A (process)
                                                                                   in:  —
OPC IN: Sea Water Supply from 234-3.00-027 (SWS-234-03301-115201D-10"-N)          out: → E-234-010B (process)
                                                                                   in:  —
OPC IN: Spent Butane from V-234-002A~D (P-234-03016-F3D-8"-Is)                    out: → KV-2904 (process)
                                                                                   in:  —
OPC OUT: Sea Water Return to 237-3.00-050 (SWR-234-03301-115201D-10"-N)           out: —
                                                                                   in:  ← E-234-010A (process)
OPC OUT: Spent Butane (Cooling/Filling) to F-234-004A/B (P-234-03302-CD3D-6"-N)   out: —
                                                                                   in:  ← E-234-010B (process)
OPC OUT: Spent Butane to V-234-004 (P-234-03303-CD3D-2"-N)                        out: —
                                                                                   in:  ← E-234-009 (process)
TIC-2911                                                                          out: → TY-2911 (sig_elec)
                                                                                   in:  —
TY-2911                                                                           out: —
                                                                                   in:  ← TIC-2911 (sig_elec)
```
## Conflicts (36)

- **unstitched_line_endpoint**  p1  at (1222,1419)  process
  → arbitration: status=skipped_handled_by_edge_resolve
- **unstitched_line_endpoint**  p1  at (1222,1549)  process
  → arbitration: status=skipped_handled_by_edge_resolve
- **unstitched_line_endpoint**  p1  at (3029,1944)  process
  → arbitration: status=skipped_handled_by_edge_resolve
- **unstitched_line_endpoint**  p1  at (3666,1229)  process
  → arbitration: status=skipped_handled_by_edge_resolve
- **unstitched_line_endpoint**  p1  at (3029,1728)  process
  → arbitration: status=skipped_handled_by_edge_resolve
- **unstitched_line_endpoint**  p1  at (2444,2667)  process
  → arbitration: status=skipped_handled_by_edge_resolve
- **unstitched_line_endpoint**  p1  at (2714,3672)  process
  → arbitration: status=skipped_handled_by_edge_resolve
- **unstitched_line_endpoint**  p1  at (3971,3067)  process
  → arbitration: status=skipped_handled_by_edge_resolve
- **unstitched_line_endpoint**  p1  at (3961,2592)  process
  → arbitration: status=skipped_handled_by_edge_resolve
- **unstitched_line_endpoint**  p1  at (4166,2592)  process
  → arbitration: status=skipped_handled_by_edge_resolve
- **unstitched_line_endpoint**  p1  at (2714,3163)  process
  → arbitration: status=skipped_handled_by_edge_resolve
- **unstitched_line_endpoint**  p1  at (3971,3768)  process
  → arbitration: status=skipped_handled_by_edge_resolve
- **unstitched_line_endpoint**  p1  at (3666,3768)  process
  → arbitration: status=skipped_handled_by_edge_resolve
- **unstitched_line_endpoint**  p1  at (2322,2929)  process
  → arbitration: status=skipped_handled_by_edge_resolve
- **unstitched_line_endpoint**  p1  at (2335,2929)  process
  → arbitration: status=skipped_handled_by_edge_resolve
- **unstitched_line_endpoint**  p1  at (2335,2855)  process
  → arbitration: status=skipped_handled_by_edge_resolve
- **unstitched_line_endpoint**  p1  at (8271,6017)  process
  → arbitration: status=skipped_handled_by_edge_resolve
- **unstitched_line_endpoint**  p1  at (8645,6017)  process
  → arbitration: status=skipped_handled_by_edge_resolve
- **dropped_edge_unsnappable**  p1
  → arbitration: status=skipped_unknown_type  detail=dropped_edge_unsnappable
- **dropped_edge_unsnappable**  p1
  → arbitration: status=skipped_unknown_type  detail=dropped_edge_unsnappable
- **dropped_edge_unsnappable**  p1
  → arbitration: status=skipped_unknown_type  detail=dropped_edge_unsnappable
- **dropped_edge_unsnappable**  p1
  → arbitration: status=skipped_unknown_type  detail=dropped_edge_unsnappable
- **dropped_edge_unsnappable**  p1
  → arbitration: status=skipped_unknown_type  detail=dropped_edge_unsnappable
- **dropped_edge_unsnappable**  p1
  → arbitration: status=skipped_unknown_type  detail=dropped_edge_unsnappable
- **dropped_edge_unsnappable**  p1
  → arbitration: status=skipped_unknown_type  detail=dropped_edge_unsnappable
- **edge_auto_drop_via_v2**
- **edge_auto_drop_via_v2**
- **edge_auto_drop_via_v2**
- **edge_auto_drop_via_v2**
- **edge_auto_drop_via_v2**
- **edge_auto_drop_via_v2**
- **edge_auto_drop_via_v2**
- **edge_auto_drop_via_v2**
- **edge_auto_drop_via_v2**
- **edge_auto_drop_via_v2**
- **edge_auto_drop_via_v2**
## Debugging flags

```
Unsnapped edges (0):       —
Loose-snap edges (1):      e-d2d85b3a
Low-confidence nodes (0):  —
Unclassified nodes (1):    VB-2911@p1
Dangling OPCs (6):         OPC IN: Spent Bu@p1, OPC OUT: Spent B@p1, OPC IN: Min Flow@p1, OPC OUT: Sea Wat@p1, OPC IN: Sea Wate@p1, OPC OUT: Spent B@p1
```
