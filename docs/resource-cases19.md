# C7: evidence to scoped local candidates / 有界经验候选

`checks19/build_resource_cases.py` does not run an LLM, database or service and
never promotes a passing experiment automatically. The input is a completed
strict four-family resource suite, plus its SHA-256 supplied independently by
the caller. The command rechecks the exact current two-repository pairing,
committed verifier/rule/source bytes before importing helpers, tool digests,
all artifact bytes, execution completeness, and four independent raw gates.
A changed/partial/development suite is rejected. Development permits only the
new builder/helper to be uncommitted; generated candidates remain development.

```
python checks19/build_resource_cases.py --output fresh-candidates.json build \
  --suite COMPLETE_SUITE --expected-index-sha256 TRUSTED_INDEX_DIGEST \
  --expected-tests-head TESTS40 --expected-skill-head SKILL40 \
  --skill-root SKILL_CHECKOUT --toolchain TRUSTED_TOOLCHAIN_JSON
```

Only fixed facts, exact CPU/driver/API/layer/source/feature/access scope, and
relative source/raw evidence references with digests leave the original suite.
No device addresses, original raw contents, argv, private absolute paths or
environment variables are exported. These are repository-authored controlled
fixtures, not customer bugs. A deliberately wrong output oracle, a callback-
aborted invalid API attempt, and a successful positive execution are distinct.
No minimal repair patch is demonstrated by these four cases.

## Explicit review and revocation

Extract one candidate object from `records` into a new local JSON file. Hash
that file externally; do not overwrite the candidate. A review request contains
`action: review`, UTC `at`, caller-declared `reviewer`, the complete unchanged
`scope`, UTC `expires_at`, and `evidence` with three SHA-256 values:
`reproduction`, `counterexample_review`, `review_report`. Those refer to concrete
separately retained evidence reviewed by the caller, not a boolean approval.
Reviewer must differ from the fixture author. This checks the contract, not the
reviewer's real-world identity, authenticity or the quality of their judgment.

```
python checks19/build_resource_cases.py --output reviewed.json transition \
  --input candidate.json --expected-input-sha256 TRUSTED_LATEST_DIGEST \
  --request review-request.json
python checks19/build_resource_cases.py --output retrieval.json retrieve \
  --input reviewed.json --expected-input-sha256 TRUSTED_LATEST_DIGEST \
  --request exact-scope-and-now.json
```

Retrieval request has complete `scope` and UTC `now`. Only reviewed, unexpired,
nonrevoked records with exact scope equality are returned, with reasons and next
verification conditions. A candidate never matches. Duplicated IDs are rejected
rather than arbitrarily choosing an older state. Revocation/expiration requests
use `action: revoke` or `expire`, `at`, `reviewer`, unchanged `scope`,
`evidence: {decision_report: SHA256}`, and `expires_at: null`. These append a
hash-linked event; they do not delete old evidence or permit re-review of an
inactive record. A test policy withdrawal is not a newly discovered GPU defect.

**The caller must retain and independently supply the latest ledger digest.**
Hashes are not signatures and there is no authenticated global latest-state
service. Selecting an old trusted digest can replay an old state. This explicit
boundary also applies to rewriting a whole chain and supplying a replacement
anchor. No inferred external/human review, cross-device generalization, new
permissions, model-routing change, performance claim, or ALL19/E2E release
promotion is made. The complete original evidence remains local and required
for repeat verification; candidate records are not executable evidence bundles.

Review binding is mechanical: `reproduction` must equal this case's referenced
`good.stdout` digest. `counterexample_review` must equal SHA-256 of canonical
JSON (`sort_keys=True,separators=(',',':'),ensure_ascii=True`) mapping the two
negative modes' `.stdout` and `.stderr` relative paths to their digests. Use
`tools/resource_cases19.py:review_evidence(base)` to obtain the exact values.
`review_report` is the digest of a separate actual review receipt. An internal
read-only reviewer must be labeled as such, not as human/external approval.
Scope also hard-matches a digest of the original suite's tool hash map, its
config digest, and the pinned 1.4.309 normative corpus digest. Only their hashes,
not private absolute tool paths, are exported.

Failed, cancelled and unreproduced suites are not imported by this bounded
builder. Their original raw reports remain retained locally; no failed history
is deleted or turned into a successful case. General failure-case ingestion,
authenticated review systems and broad C7/full-release closure remain unverified.
