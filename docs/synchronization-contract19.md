# Fixed prose to bounded buffer-synchronization contracts

This closes a named C1 semantic-review increment, not complete synchronization,
C0/M0 or L1/L2 acceptance. It introduces no new GPU experiment.

## Official prose, not another symbol count

The locally available original Khronos Vulkan-Docs tree is clean at
`fa30d4e312e843193601be7cb926c7e25d9ec885` (the same Registry1.4.368 cohort).
`chapters/synchronization.adoc` is Git blob
`7b8fc732f0184ce6acc060cbea264da4150347d8`, SHA256
`7748c88e48007820179681ef4f82c1d2244afc5482b5bc0c13d370ef64821909`.
Khronos source license: CC-BY-4.0. The map records exact raw source line ranges,
anchor names, slice hashes and conditional directives, not copied whole chapters.

Eight anchors cover execution/chains, availability/visibility, memory/access
scopes, submission order, prior host writes and buffer ownership transfer.
These are physical source slices ending at the next explicit anchor. Includes,
outer conditional context and cross-chapter definitions are not fully evaluated.
This is a versioned review aid, not a generated/preprocessed complete specification.
The independently frozen309 range VUIDs remain a distinct source version.

## Actual old card errors and repair

- A submitted, host-ordered write already available to the host domain does not
  invariably need an extra HOST_WRITE barrier. Required flush, ordering, range
  lifetime and no overlapping in-flight use remain independent obligations.
- Different queues are not necessarily different families. Ordinary exclusive
  cross-family preserved-content use requires appropriate release/acquire and
  queue synchronization; same-family queues still require dependencies but not
  family ownership transfer. Concurrent sharing and newer maintenance exceptions
  are not guessed by the restricted evaluator.
- Ordinary buffer memory-barrier ranges do not inherit noncoherent atom alignment.
  Offset1/size3 within16 is a useful legal range counterexample. Zero, overflow
  and offset-at-end are rejected; WHOLE_SIZE has its own range semantics.
- Same-queue submission order alone supplies neither execution nor memory
  dependency. RAW/WAW require appropriately scoped memory dependencies, whereas
  WAR can be solved with execution ordering alone. A host fence flag is not
  independently proof of the entire GPU access dependency.

## Executable scope

`tools/sync_contract19.py` evaluates caller-proven, precisely scoped facts.
It does not inspect GPU state, infer arbitrary stage/access coverage, discover
resource overlap or authenticate evidence. Unknown inputs remain UNKNOWN;
unsupported special paths remain outside scope. Passing means only the stated
bounded facts satisfy the reviewed contract. Fixed positive/negative examples
are HOST contract controls, never measured races or predicted Validation output.

Existing actual transfer/descriptor/compute synchronization cases retain their
original source/runtime cohorts. No rerun or expanded GPU proof is inferred here.
SyncVal shader-access heuristic OFF silence remains insufficient correctness proof.

The source-map and contract test linkage is auditable, but complete normative
prose mapping, version reconciliation, remaining function families, SC, physical
devices, Live/blind tasks and the original36 final tests remain open.

## Repeat the bounded integrated check

```sh
python checks19/run_sync_contracts.py \
  --prose /path/to/fixed-368/chapters/synchronization.adoc \
  --validusage /path/to/fixed-309/validusage.json --out /fresh/output
```

This hashes the actual input bytes and implementation files, maps the eight
source anchors, then evaluates20 registered HOST controls. It fails before writing
a report if a source hash or expected decision differs. Inputs are declared cases;
no status may be reused as a discovery of runtime state or validation-layer result.
The three counterexample families correspond to actual corrected card text rather
than hypothetical new extension demos.
