# Vendored DEXPI 2.0 specification sources

The contents of this directory are copied verbatim from the DEXPI Specification
repository. They are **not** authored by the diagex project. They are vendored
so that diagex can regenerate its DEXPI 2.0 pydantic model offline and at a
pinned upstream version.

## Provenance

- **Upstream repository:** https://gitlab.com/dexpi/Specification
- **Pinned commit:** `260c81c51039789a6148a98af4c6caf23f87a3e2`
- **Pinned tag:** `V2.0.0`
- **Upstream commit date:** 2025-10-10
- **Vendored on:** 2026-05-01

## Contents

| Path | Source path in upstream repo |
|---|---|
| `model/Core/`, `model/Plant/`, `model/Process/` | `src/model/Core/`, `src/model/Plant/`, `src/model/Process/` |
| `DEXPI_XML_Schema.xsd` | `src/documentation/_static/DEXPI_XML_Schema.xsd` |

## License

Copyright © 2025 DEXPI Initiative.

The DEXPI Specification, including the source files vendored here, is published
under the **Creative Commons Attribution 4.0 International License (CC-BY 4.0)**.

License text: https://creativecommons.org/licenses/by/4.0/

## Modifications

None. Files in this directory are byte-identical to upstream at the pinned
commit. Any modifications by the diagex project are made in the generator
output (`src/diagex/dexpi/_generated/`) or in `src/diagex/dexpi/extensions.py`,
not here.

## How to refresh

```bash
SHA=<new-commit-sha>
curl -fsSL "https://gitlab.com/dexpi/Specification/-/archive/$SHA/Specification-$SHA.tar.gz?path=src%2Fmodel" \
  | tar -xz -C /tmp
# replace src/diagex/dexpi/codegen/vendored/model/ with the extracted tree
# update PROVENANCE.md (commit, tag, date)
# rerun: python -m diagex.dexpi.codegen.regenerate
```
