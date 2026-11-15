# C0/C1 semantic inventory and cross-card correction

This is a reproducible review denominator and bounded conflict correction, not a
claim that M0/M1 or whole-domain L1/L2 have passed.

## Separate denominators

The frozen Registry 1.4.368 source commit and SHA used by the earlier reconstruction
remain unchanged. Core 1.0–1.4 feature records (including subdivisions) and stable
standard Vulkan extensions form a named **review scope**. Their count is neither
API-version count nor semantic completion. Provisional, disabled and other-API
records remain explicitly classified, not silently dropped. SC stays separate.

The independently pinned Vulkan-Headers 1.4.309 validusage corpus is a second,
conditional normative-clause denominator. Owner, condition and VUID coordinates,
exact text digest and source hash identify a clause. No 368→309 semantic join is
assumed. A VUID hit does not demonstrate applicability, an enabled feature, correct
runtime behavior or a completed L1/L2 contract. A condition string is preserved,
not evaluated as an expression or instruction.

Original-plan 3.3 still additionally requires complete normative prose, video,
Headers and SPIR-V mapping, aliases/pNext/member closure and version reconciliation.
These remain explicit gaps, not excluded because they are harder to enumerate.
The new review ledger must not report a percentage over a larger unpinned universe.

## Actual cross-card defects corrected

1. `descriptor_update.md` previously offered rewriting a descriptor as an
   alternative to GPU retirement before destroying the old resource. This
   contradicted its own in-flight discussion and the more precise ordinary UBO
   lifetime card. The repair independently preserves all actual resource-consumer
   retirement (00922) and ordinary pending-update restrictions (03047), plus
   reset/re-record after invalidating recorded ordinary bindings. A signaled
   unrelated/stale fence is not proof; advanced flags are not lifetime waivers.
2. `descriptor_indexing.md` treated a generic update-after-bind feature and a
   generic array-length limit as Vulkan members. Replace these with type-specific
   support/enables, actual layout flags and the appropriate descriptor limits.
   A sampled-image UAB feature does not authorize storage-buffer UAB.

These are source-card corrections, not newly induced GPU illegal-destruction
experiments. Existing actual 03047 and 00070 controls are historical, separately
pinned runtime evidence, not rerun or newly broadened here. Pure negative controls
prove rejection of erroneous review inputs and selected incorrect contracts, not
that natural-language contradictions can be exhaustively recognized automatically.

## Review semantics and completion gates

Hash-bound claims/reviews are declared internal assertions, not signed human
approval. Same predicate + exact scope + opposite assertions is a conflict;
different scopes require applicability review, not an automatic contradiction.
An unresolved or stale review cannot upgrade semantic status. Indexing all clauses
still leaves unreviewed clauses unreviewed. A corrected individual claim must never
mark its containing stable extension or all of Vulkan as L1/L2 complete.

Next: expand explicit contract and applicability reviews against this stable scope,
review source-version mismatches and remaining normative source coverage, then
prepare a traceable external engineering task. Keep 36 ALL19/E2E tasks UNVERIFIED
and both PRs Draft until original acceptance gates actually pass.

## Reproduce without network or a GPU

```sh
python checks19/audit_semantic_cards.py \
  --validusage /path/to/frozen-1.4.309/validusage.json \
  --registry /path/to/frozen-1.4.368/vk.xml \
  --skill /path/to/paired-skill --out /fresh/output
```

Both normative inputs are byte-pinned. The case entry also requires the exact
three reviewed card byte hashes; changing even a card's wording requires a new
review rather than interpreting absence of an old bad sentence as correctness.
It reads the explicit historical Git object for the old defect, not a moving
branch or external command from input. The historical location label is synthetic
and clearly identified as such; its quoted text, line number, path, commit and
file digest identify the actual evidence. Output inventory retains every unit,
separate source identities and unreviewed scope IDs. The compact checked-in report
is a prepublication cohort; fresh exact-head execution is separately recorded.

For your own **declared** structured reviews use `tools/semantic_inventory19.py`
with `--claims` and `--reviews` JSON arrays. It validates coordinate/hash/schema
bindings, not the contents or authenticity of supplied evidence files. Conflicts
block uncontested acceptance declarations, and even an uncontested declaration
cannot automatically complete a scope, clause, feature or domain. Missing original
normative sources remain explicit in the inventory's limitations.
