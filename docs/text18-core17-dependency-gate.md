# Independent CORE17 static dependency gate

TEXT18 and reconstructed CORE17 tests remain sibling branches of the unchanged
v1.0.16 test base. This addition neither rebases nor merges either branch, changes
no existing candidate/release contract, and retains the legacy16/TEXT18 CI matrix.
The additional CI job resolves a separate immutable tests/Skill pair from
`core17-dependency-manifest.json`, then checks out each exact commit. It runs the
paired Skill17 source/safety tests and the ORIGINAL CORE17 version-scoped gate.

The manifest freezes the original candidate contract and gate script digests as
well as tests, Skill and base commit SHAs. The runner rejects wrong heads, dirty
checkouts, hidden index flags, shallow histories, submodules, unavailable or
non-ancestor bases, changed source digests and mismatched original contracts.
It checks both trees again after execution. It does not rewrite version assertions,
copy CORE17 tests into TEXT18, remove tests, substitute latest branches, or treat
a missing dependency as success. Git/subprocess operations have explicit bounds.

Successful output is `DEPENDENCY_STATIC_PAIR_PASS`, always with release BLOCKED,
semantic acceptance UNVERIFIED and merged_into_text18 false. The six partial
legacy links remain six PARTIAL links, with equivalent reuse zero. Passing both
independent pairs in one workflow makes the dependency reproducible, but does not
establish same-candidate cumulative semantic coverage, original CORE17 complete
acceptance, Live behavior, platform/device acceptance, or a merged test history.
The independent CORE17 gate's existing exclusions and scope remain unchanged.

Local reproduction uses clean exact checkouts and an unused result path:
```
python tests/run_core17_dependency.py --tests CORE17_TESTS_CHECKOUT \
 --skill SKILL17_CHECKOUT --output NEW_RESULT.json
```
Synthetic tests validate fail-closed orchestration, not model or GPU behavior.
Remote PR/main freshness is outside this offline runner; the pinned pair is a
reviewed snapshot, not a claim that a branch remains current or has merged.
