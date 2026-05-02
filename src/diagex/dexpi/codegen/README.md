# diagex DEXPI 2.0 codegen

Translates the vendored DEXPI 2.0 specification source (`vendored/model/`,
CC-BY 4.0) into pydantic v2 classes under `src/diagex/dexpi/_generated/`.

## When to regenerate

- After bumping the vendored DEXPI spec to a newer 2.x version (see
  [Bumping the vendored DEXPI spec](#bumping-the-vendored-dexpi-spec) below).
- After modifying `pydantic_emit.py`.
- After bumping `ruff` (the regenerator pipes its output through `ruff format`
  and `ruff check --fix` to keep `_generated/*.py` idiomatic; a ruff version
  bump that changes formatting will require a regen + commit).
- Otherwise: never. Generated files are checked in and consumed by the runtime
  on Python 3.11+.

## How

```bash
# One-time per dev machine (Python 3.12+ required for dexpi.specificator):
pip install -e '.[codegen]'

# Run the generator (also via 'make regen-dexpi'):
python -m diagex.dexpi.codegen.regenerate
```

The generator overwrites `_generated/__init__.py`, `core.py`, `plant.py`,
`enums.py`, and (v2 Phase D) `process.py`. Run
`pytest tests/unit/test_dexpi_codegen.py` afterwards to verify the output is
well-formed and importable. CI enforces this contract via the `codegen`
workflow, which fails any PR where `_generated/` differs from a fresh regen —
see `.github/workflows/codegen.yml` and `make check-generated`.

## Bumping the vendored DEXPI spec

DEXPI 2.x patches arrive periodically; bumping the vendored copy is the only
supported way to track them.

1. Resolve the upstream commit hash on
   <https://gitlab.com/dexpi/Specification> (e.g. tag `V2.0.1`).
2. Replace `vendored/model/` with the new tree's `model/` directory. Keep the
   same layout (`Plant.py`, `Core.py`, `Process/`, `Enumerations/*.py`, `*.ods`).
3. Update `vendored/PROVENANCE.md` with the new commit hash, tag, and date.
4. `make regen-dexpi` (or `python -m diagex.dexpi.codegen.regenerate`).
5. Run the full unit suite: `make test`. (Step 4's `make regen-dexpi` already
   exercised `tests/unit/test_dexpi_codegen.py`; this step is for the
   builder/JSON-IO/XML-IO regressions a spec change can cause.) Pay
   particular attention to fields that shipped as `Optional[X]` becoming
   `X | None` or vice-versa — `xml_io.py` walks `typing.get_args()` so it
   accepts both, but other consumers may not.
6. **v2 specific checks:**
   - **Typed `BoundDataType` quantities (Phase A):**
     `pydantic_emit.collect_bound_quantity_specs` enumerates every
     `BoundDataType<PhysicalQuantity, UnitType=...>` in the spec. v2.0.0 has
     17 distinct bindings → 17 generated `<X>Quantity` classes. A spec patch
     that adds a new unit family will surface as a new typed class
     automatically. A spec patch that introduces a **non-`PhysicalQuantity`
     `BoundDataType` base** will hit the multi-binding fallback in
     `_bound_class_name` — verify the emitted name is sensible or add an
     explicit branch.
   - **Property kinds (Phase B):** the regen emits `__dexpi_field_kinds__`
     per class. New `composition` / `reference` fields ride the existing
     XML and JSON wire-format paths without code changes.
   - **Process namespace (Phase D):** `process.py` is regenerated alongside
     core/plant. New Process classes show up automatically. Process imports
     Core but not Plant — keep that DAG acyclic.
   - **Coverage matrix (Phase E):**
     `tests/unit/test_dexpi_builder_coverage.py` parametrizes over
     `EQUIPMENT_REGISTRY` / `VALVE_REGISTRY`. A class that `dexpi_schema.py`
     references but the new spec drops will fail with a clear "no concrete
     DEXPI class" message — update or remove the spec entry rather than
     papering over it.
   - **Validator (Phase F):** run
     `diagex dexpi-validate tests/fixtures/dexpi_2_0/reference_pid.xml --skip-xsd`
     after the regen. The reference fixture should still come back with
     0 errors; non-zero means the rule pack assumes a class shape that
     changed.
7. **Reference fixture** `tests/fixtures/dexpi_2_0/reference_pid.xml`: if the
   spec patch ships an updated reference instance, vendor it too and rerun
   the structural round-trip test. Any drift in the
   `(11 PipingNetworkSystems / 5 TaggedPlantItems / 4 PIFs / 1 Diagram)`
   snapshot in `test_official_reference_pid_round_trips_structurally` is
   real — investigate before adjusting the assertions.
8. **Lint baseline:** ruff's `F405` (`X may be undefined, or defined from
   star imports`) is suppressed in the generated-files header. Other warning
   classes will surface; if the regen introduces a new noqa class, decide
   whether to suppress (codegen artefact) or fix upstream in
   `pydantic_emit.py`.
9. If any tests fail, the upstream change is non-additive — investigate
   before committing. Common causes: a field rename that breaks
   `dexpi_builder.py`, a class moved between Plant and Core, or a new
   required field on an existing class. The XML / JSON parsers fall back to
   `model_construct` when `model_validate` rejects fixture-omitted fields
   (Phase B), so a spec change that adds a required field won't crash the
   round-trip outright — but the data is gone, so callers should validate
   on their own path before trusting the loaded object.
10. Commit `vendored/`, `_generated/`, and any consumer fixes as a single
    "Bump DEXPI to X.Y.Z" commit so the regen output is bisectable.

## Python version policy

| Component | Python version |
|---|---|
| diagex runtime + generated files | **3.11+** |
| `dexpi.specificator` (codegen-time only) | **3.12+** |

The codegen extra (`pip install -e '.[codegen]'`) requires Python 3.12 because
of `dexpi.specificator`'s own pin. Generated `_generated/*.py` files target
Python 3.11 (no walrus-in-f-string, no `type` statements, etc.).

## Architecture

```
   vendored/model/               (CC-BY 4.0 DEXPI Specification 2.0.0)
        │
        │  dexpi.specificator.dsl_reader.DslReader  (MIT)
        ▼
   in-memory metamodel           (pnb.mcl.metamodel.standard objects)
        │
        │  src/diagex/dexpi/codegen/pydantic_emit.py  (Apache-2.0)
        ▼
   _generated/{enums,core,plant}.py   (Apache-2.0; CC-BY attribution in header)
```

The emitter has two output paths:

- Entity classes (`ConcreteClass` / `AbstractClass`) extend `DexpiEntityBase`,
  which provides UUID `id`, optional `proteusId` alias, and identity-based
  hashing.
- Value types (`AggregatedDataType` like `MultiLanguageString`) extend
  `DexpiValueBase` — no id, no hash boilerplate.

`AbstractDataType` (e.g. `Core.PhysicalQuantities.PhysicalQuantityUnit`) is
emitted as a `Union[…]` type alias of its leaf enum subtypes.

## Status: v2 closes the v1 limitations

- ~~`BoundDataType` properties emitted as `Optional[Any]`~~ — **resolved in
  v2 Phase A.** 17 typed `<X>Quantity` subclasses of `PhysicalQuantity` cover
  the full spec; 0 `Any | None` placeholders remain.
- ~~Process model not generated~~ — **resolved in v2 Phase D.**
  `_generated/process.py` carries the 143 Process classes; same I/O
  machinery (JSON + XML) handles Process round-trip.
- **No camelCase compatibility aliases.** Generated field names stay
  PascalCase, matching DEXPI 2.0. The `dexpi_builder.py` migration in v1
  Phase 5 dealt with the camelCase-to-PascalCase rename.

See [`plan/dexpi-decoupling-v2-plan.md`](../../../plan/dexpi-decoupling-v2-plan.md)
for the full v2 changelog.

## Field-name collisions

DEXPI 2.0 has fields whose names match their type names
(`EngineeringModel.ConceptualModel: ConceptualModel`). These would shadow the
type during pydantic field-resolution, so the generator detects the collision
and emits the Python attribute as snake_case with a PascalCase alias:

```python
class EngineeringModel(DexpiEntityBase):
    conceptual_model: Optional[ConceptualModel] = Field(default=None, alias="ConceptualModel")
```

`model_config.populate_by_name=True` means both names work in constructors.
`model_dump_json(by_alias=True)` emits the PascalCase wire format.
