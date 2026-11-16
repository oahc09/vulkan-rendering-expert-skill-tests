# Existing Simulation Lab: numerical quality decision

This wrapper builds and executes the unchanged v1.0.16 Simulation Lab:144 numerical
snapshots,32 constraint reports,52 nonempty draws,15 shader modules. It does not
introduce a new toy solver or weaken original numerical tolerances. The selected
C2 candidates are rope/cloth × colored GS/Jacobi ×8 ticks. The algorithms differ;
being close to each algorithm's FP64 CPU implementation does not establish equal
convergence or product quality. Python independently recomputes errors, normals,
bounds, topology/rest definitions, residuals, penetration and generations, not a
third complete trajectory. Original draw acceptance is coverage, not golden pixels.

```sh
python checks19/run_simulation_choice.py --tools /path/to/bin \
 --include /path/to/usr/include --loader /actual/libvulkan.so.1 \
 --icd /path/to/lvp_icd.json --libdir /path/to/libraries \
 --layerdir /path/to/explicit_layer.d --skill-root /path/to/skill \
 --expected-tests-head FULL_SHA --expected-skill-head FULL_SHA --output /fresh/out
```

Both repositories must be clean at the expected paired commits. The fixed original
build/run scripts are invoked with controlled tools/environment. Their unmodified
180-second run timeout remains; scoped process supervision adds build90/run190 and
a300-second execution budget. This is not a GPU hang/recovery test. Sources, linked
loader, official tool/header/ICD/VVL cohort, binary and SPIR-V, original logs and
all raw artifacts are hashed and checked at completion. Standard libraries and
all transitive process state are not claimed completely frozen.

Optional `--policy` JSON, default:
```json
{"baseline":"colored","quality_targets":null,"require_performance":false}
```
Null targets return NEEDS_QUALITY_TARGET. An explicitly declared product policy can
supply `rope` and `cloth`, each containing nonnegative `max_absolute_residual` and
`max_penetration`. These are model-unit product requirements, **not** CPU-match
tolerances. No default residual target is inferred from measured maxima. A test-only
policy using residual1 and penetration0.00001 illustrates the schema; it is not a
recommended product target or a preregistered original-plan criterion. Residual0 is
an intentionally strict test control. Never claim compliant cloth must converge
exactly to hard rest distances. Performance requirements remain NEEDS_MEASUREMENT.

The pure decision reruns raw checks, not accepting a caller's PASS or metrics blob.
It keeps the baseline when it meets explicit quality constraints, otherwise names
a quality-admissible alternative if any, with no speed ranking. Serialized
single-queue/fence ticks cannot establish async publishing or consumer concurrency.
A lower residual alone does not establish better visual behavior or equal algorithm.

Seven controlled HOST corruption checks reject missing/duplicate snapshots,
missing/duplicate edges, stale generation, altered residual and altered GPU values.
They do not rerun intentionally invalid shaders. A compressed fixture preserves
32 original baseline packets for host mutation tests, not current-GPU proof.
No Android thermal, physical GPU speed, mobile quality, Live/blind acceptance,
XPBD production-engine correctness or complete simulation/text-family closure.
