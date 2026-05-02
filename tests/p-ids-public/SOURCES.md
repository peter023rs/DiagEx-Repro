# P&ID source attribution

The 10 PDFs in this directory are publicly redistributable diagrams sourced
from the references below. Use this file (rather than the manifest) as the
human-readable provenance card; the machine-readable `meta.yaml` next to
each fixture under `eval/datasets/<stem>/` carries the same information in
structured form.

## Sources

| PDF(s) | Source | Link |
|---|---|---|
| `butane1.pdf`, `butane2.pdf` | *A Digitization and Conversion Tool for Imaged Drawings to Intelligent Piping and Instrumentation Diagrams (P&ID)*. Energies (MDPI), 2019. | <https://doi.org/10.3390/en12132593> |
| `dexpi-reference.pdf` | DEXPI Initiative — *C01 DEXPI Reference P&ID* (training & test cases, DEXPI 1.3 example PIDs). | <https://gitlab.com/dexpi/TrainingTestCases/-/tree/master/dexpi%201.3/example%20pids/C01%20DEXPI%20Reference%20P&ID?ref_type=heads> |
| `grit-washer1.pdf` | *PID_dataset* (Zenodo deposition). | <https://zenodo.org/records/8028570> |
| `open100-1.pdf`, `open100-2.pdf`, `open100-3.pdf`, `open100-4.pdf` | *PID2Graph Dataset* (Zenodo deposition). | <https://zenodo.org/records/14803338> |
| `tennessee1.pdf` | *Revision of the Tennessee Eastman Process Model*. IFAC-PapersOnLine, 2015. | <https://www.sciencedirect.com/science/article/pii/S2405896315010666> |
| `two-tanks.pdf` | GetReskilled — *Reading P&ID Symbols and Abbreviations for the Pharmaceutical Industry: A Step-by-Step Guide*. | <https://www.getreskilled.com/validation/pid-symbols/> |

## Redistribution notes

All ten PDFs are redistributed in this repository under the licensing terms
of their respective sources. The DEXPI reference is published by the DEXPI
Initiative under CC-BY 4.0 and may appear in LLM training corpora — its
score is reported separately to make any contamination posture explicit
(see `docs/DATA_CARD.md`, "Contamination posture"). The two Zenodo
depositions (`PID_dataset`, `PID2Graph Dataset`) are released under their
deposit-page licenses; consult the linked records for the exact terms
before redistributing further.

The ground-truth annotations (`eval/datasets/<stem>/{graph.truth.json,
annotations.truth.jsonl, queries.truth.yaml, meta.yaml}`) are authored by
the diagex project and released under **Apache-2.0** alongside the rest of
the source.

## Adding a new fixture

If you add a new PDF to this directory:

1. Drop the file here with a stable, lower-case, hyphenated stem
   (`<domain>-<index>.pdf`).
2. Add a row to the table above with the source citation and URL.
3. Add the per-fixture entry to `eval/datasets/manifest.yaml` (stem,
   domain, source_type, page_size_pts, draughting_tool, annotation_level,
   role, notable_flags).
4. Author ground truth under `eval/datasets/<stem>/` per the templates
   (`_template.queries.truth.yaml`, `_template.annotations.truth.md`).
5. Re-run `pytest tests/unit/test_eval_*.py` to sanity-check the loader.
