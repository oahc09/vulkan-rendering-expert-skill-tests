# Registered project patch replay: AST portability

This entry replays **one known historical repair in the authorized Tests project**.
It is not a new user defect, blind solution, generic shell executor or GPU test.
No new project or network dependency is fetched; no current branch is checked out,
reset or committed. There is no standalone portable binary/source package claim:
the output is a locally reproducible evidence directory for this fixed cohort.

## Preregistered recipe and oracle

- Base: `00c3b8b234576817989df116948a2eaa5af761e2`
- Candidate: `3afa22d29f93a48c5012a968a5eba2085189bc66`
- Patch SHA256: `162f353bcd0b2bdc0786a29634f7f011f10678bd531d088cf2279a40823cb33c`
- Exactly three approved paths: `tools/contract_registry19.py`,
  `tests/fixtures/contract-registry19.json`, `tests/test_contract_registry19.py`.
- Actual fixed interpreters: Python 3.12.14 and 3.13.5, with registered executable
  hashes. Critical AST/JSON stdlib files and dynamically linked libraries are
  recorded and rechecked; this is not a claim of every transitive OS dependency.

Python 3.13 changed `ast.dump` display of empty fields. The base's display-derived
hash fails the same frozen fixture on 3.13 while matching on 3.12. The repair uses
explicit recursive AST serialization. The oracle compares **all 23 semantic entries
and 21 helpers**, complete scans and rebuilt manifests. Expected baseline failure
requires exactly the 44 `ast_sha256` coordinates to differ, every other field to
remain equal, and worker exit 42. Missing tools, exceptions or arbitrary nonzero
exit codes never count as reproduction.

The candidate must match its fixed fixture on both interpreters, and the two full
rebuilt manifests must be identical. Its fixture differs from the original fixture
only at those 44 hashes. A separately constructed semantic AST mutation must still
change the hash: a constant PASS/hash implementation is not a valid repair.
Each rebuild runs the same 125 original HOST controls. Six stage/interpreter runs
are repetitions, **not 750 independent tests**.

## Isolation and actual patch application

Ordinary Git blobs are exported from the exact historical commits to fresh output
subdirectories. Symlinks, submodules, traversal and unregistered files are rejected.
Git runs with a controlled environment, replacement objects disabled, hooks and
fsmonitor disabled, and fixed diff settings. No repository config is changed.
The exact patch is applied to an isolated base export, and every exported byte
must match a separate candidate export. **After executes that patch-applied tree**,
not merely the candidate checkout. Rollback is a new export of the original base
and repeats both interpreters; it is not rollback of the user's working tree.

Before and after each worker, and finally, exact directory inventories reject extra
`__init__.py`, `.pyc`, symlinks or other import files. Workers use `-I -S -B` and a
fixed import path. Historical Skill cards and fixed368 prose are separately exported
from exact source commits, and the original309 VUID bytes are hash-bound.

## Usage

```sh
python checks19/replay_project_patch.py \
  --project-root /path/to/authorized-tests \
  --skill-root /path/to/paired-skill --docs-root /path/to/vulkan-docs-git \
  --validusage /path/to/fixed-validusage.json --output /fresh/replay \
  --base 00c3b8b234576817989df116948a2eaa5af761e2 \
  --candidate 3afa22d29f93a48c5012a968a5eba2085189bc66 \
  --expected-patch-sha256 162f353bcd0b2bdc0786a29634f7f011f10678bd531d088cf2279a40823cb33c \
  --allowed-path tests/fixtures/contract-registry19.json \
  --allowed-path tests/test_contract_registry19.py \
  --allowed-path tools/contract_registry19.py \
  --expected-tests-head CURRENT_FULL_TESTS_SHA \
  --expected-skill-head CURRENT_FULL_SKILL_SHA
```

This registered recipe requires the existing local interpreter paths/hashes and
historical Git objects. A different project, commit, patch, interpreter build or
recipe needs independent registration/review; no arbitrary user commands or patch
files are accepted. Strict mode requires current clean exact paired sources;
`--development` is explicitly non-published evidence.

`--budget-seconds`, `--step-seconds` and `--cancel-file` bound owned subprocess
execution after initial source preflight/export. They are not a wall-clock promise
covering all Git/hash preflight. Failures preserve raw streams and verified stage
prefix with pending stages, remain BLOCKED, and require a fresh directory to retry.
Successful output includes `review.patch`, `REPLAY.md`, `replay-index.json`, isolated
source trees and all stdout/stderr. Hashes preserve byte identity, not authorship or
proof of a general causal diagnosis. Original failed CI remains historical evidence;
this task does not retroactively mark the base revision green.
