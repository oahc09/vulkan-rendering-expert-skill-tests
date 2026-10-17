# Vulkan skill v1.0.9 test evidence

The skill and this repository are separate. Set VULKAN_SKILL_ROOT to the skill
checkout, or put it at ../skill (legacy sibling name also supported).
Requirements: Python 3.10+, pytest, pyyaml. Optional token measurement: tiktoken.

## Three independent layers

| Layer | Command | What success proves |
|---|---|---|
| Static | `python -m pytest -q -m static tests` | Source structure, release contract, and harness unit/regression checks |
| Snapshot | `python -m pytest -q -m snapshot tests` | Four historical v1.0.8 responses still satisfy their original assertions |
| Live | `VULKAN_LIVE_RUN_DIR=/path/run python -m pytest -q -m live tests` | A fresh 12-case run has intact provenance and passes lexical smoke gates |

`python -m pytest -q tests` runs all layers; without VULKAN_LIVE_RUN_DIR, the
12 Live cases explicitly SKIP. A skipped run is neither a pass nor a model
failure. Static and Snapshot success cannot be reported as Live success.
Historical responses in responses_v1_0_8 are preserved unchanged. Their original
model identity and generation parameters were not recorded; they are historical
fixtures, not independently reproducible current-model evidence.

## Cases and review

The original four project-diagnosis cases remain: repository architecture map,
Vulkan 1.1→1.3 migration, Android rotation crash, and adding a compute pass.
Eight adversarial prompts and explicit human-review rubrics are in
behavior_cases.py and prompts/tc12_*.txt:

1. Reject invented descriptor-heap sync enums; check Registry/headers
2. Descriptor write size 8 bytes versus shader heapArrayStride 16 bytes
3. New desktop SDK versus old Android runtime/driver
4. vkprofiles migration, tool versions, CLI and schema compatibility
5. AHardwareBuffer external-format/Y′CbCr combined descriptor count
6. Apple hardware/OS/ICD/SDK/tool support matrix
7. Zero validation errors do not establish correctness or performance
8. Blender proposal does not prove release adoption

Lexical assertions are intentionally only smoke checks. A real run needs human
review against each rubric, especially negation, compilability, correct query
chains, version-specific claims, authoritative citations, and recommendations.
A model can mention a required word while giving wrong advice. Do not promote
`gate_passed` to full semantic acceptance without that review. Never rewrite a
failed answer to make it pass. Rerun into a new directory and retain both runs.

## Live wrapper protocol

Run a real, authorized model wrapper. The runner does not call a provider by
itself, infer credentials, or synthesize responses:

```
python tests/run_live_model_behavior.py \
  --command 'python /path/to/provider-wrapper.py' \
  --model 'exact-provider-model-version' \
  --parameters '{"temperature":0,"max_output_tokens":6000}' \
  --output-dir /path/to/new-run --check
```

The command reads the complete prompt on stdin and writes ONLY this JSON envelope
to stdout (logs to stderr):

```
{"model":"exact-provider-model-version","parameters":{"temperature":0,"max_output_tokens":6000},"request_id":"provider-id-if-available","usage":{"input_tokens":123,"output_tokens":45},"response":{"read":[{"path":"references/00_expert_entry/hard_rules.md","section":"exact Markdown heading"}]}}
```

For the final turn use `"response":{"answer":"unaltered model answer"}`.
The wrapper must invoke the configured model and copy the actual structured
response; it must not generate a canned answer or claim unverified provider
metadata. Model identity is wrapper-attested, not independently verified by the
harness. Provider input_tokens/output_tokens usage is mandatory. Exact parameters must include all explicitly set inference options;
provider defaults should be identified by the wrapper/operator. Do not put API
keys or tokens in --command: only a command hash and executable basename are recorded, but process arguments may still be visible locally.

Only SKILL.md is initially loaded. The model requests 1–8 files/sections each
round, following the skill routing itself. A section is an exact unique heading
and includes nested subsections until the next peer heading. Explicit HTML anchors are supported as section "#route-api" or path "file.md#route-api". Missing/ambiguous
headings, path escapes/symlink escapes, duplicate reads and malformed output fail
closed. Omit section only for an intentional whole-file read. At most 12 rounds
(default) and a 300-second subprocess timeout per round prevent unbounded runs.
No tools or external searches are provided by this stdin/stdout harness. Claims
requiring external verification must remain unverified unless the authorized
wrapper supplies genuine source evidence; record that wrapper configuration.

The manifest records exact skill HEAD SHA and dirty state (a dirty tree is not a
reproducible release), baseline SHA, model, parameters, command hash/executable, time and outcome.
Each case saves every raw input/output/stderr, SHA-256 hashes, wrapper request ID
and actual input/output token usage, immutable final answer, and ordered reads with saved selected content, path,
section, source file hash, selected content hash and line range. Original failure
outputs are kept. Existing output directories are refused. Timeout/error state
is recorded; absent output is not fabricated. No-model runs write only an honest
skipped manifest; --require-live changes that state to nonzero exit code 2.
--case permits a diagnostic subset, but --check requires all 12 cases.

Mock responses occur only in test_live_runner.py temporary unit fixtures, labeled
UNIT TEST ONLY. They never enter live result directories or count as inference.

## Source and context comparison

Fixed baseline: `1bad967c8e6880c3eecdaa6a946901cbc5c1f060` (v1.0.8).
The static release test compares added knowledge files to that Git tree: only
references/03_api_manual/05_descriptor/descriptor_heap.md may be new, and the
prospective tracked package must remain ≤200 files. Fetch baseline history first.

```
python tests/measure_context.py --encoding o200k_base
python tests/measure_context.py --encoding o200k_base --live-run /path/to/run
```

The first measures seed-context startup tokens using the named tokenizer: old eight-file
context at the exact baseline versus current SKILL.md. It does NOT measure total
answer cost, billing, latency, or live savings. The second separately measures
all delivered skill sections per live case, verifies their original hashes,
and reports the ≥30% target against the historical fixed load. Repeated/overlap
reads are counted as delivered; harness wrappers/user text are excluded from
both compared context metrics. It is a retrieval-policy comparison, not a
same-content compression ratio. The actual model may use a different tokenizer.
Missing tokenizer means UNMEASURED; bytes/characters are never called tokens.
No measured live run means the live ≥30% target is unverified.

## CI and paired release

CI uses ordinary pull_request/push jobs with read-only contents permissions,
no model credentials, no pull_request_target, and disabled checkout credential
persistence. It prints exact checkout SHAs. Main-branch jobs and manual dispatch default to skill main. Feature/PR jobs use
the reviewed candidate SHA 7c167d1b27e112c48219c0ebcd57e4d209a926db. Merge the skill PR first, then the tests PR, so test main always
validates skill main at v1.0.9. Dispatch accepts an explicit ref; prefer a reviewed
full commit SHA for release evidence. A missing paired ref fails rather than
silently falling back to v1.0.8. The job prints exact checkout SHAs.
CI runs Static and Snapshot separately and records Live as skipped. CI does not
claim current-model behavior coverage or the token-reduction target.

### Actual same-model paired input-token target

For the release target, run this harness twice against clean, pinned baseline and
candidate checkouts, with the same exact model, parameters and all 12 prompts.
Use distinct fresh output directories. The baseline is the SHA above; supply
the reviewed candidate commit SHA explicitly. Authentication remains with the
operator's authorized wrapper; no real model evidence is fabricated by CI.

```
python tests/run_live_model_behavior.py --skill-root /path/baseline-checkout --command 'python /path/wrapper.py' --model EXACT_MODEL --parameters '{"temperature":0}' --output-dir /path/baseline-run
python tests/run_live_model_behavior.py --skill-root /path/candidate-checkout --command 'python /path/wrapper.py' --model EXACT_MODEL --parameters '{"temperature":0}' --output-dir /path/candidate-run
python tests/measure_context.py --baseline-run /path/baseline-run --candidate-run /path/candidate-run --candidate-sha FULL_REVIEWED_SHA
```

The paired report validates complete transcripts, prompt hashes, clean pinned
revisions, identical model/parameters, and actual per-round provider input-token
usage. It sums all rounds per case, takes each run's median over the same 12
cases, then computes 1 − candidate_median / baseline_median. Only this metric sets
actual_model_input_target_met for the ≥30% target. Incomplete/missing evidence
produces null, not pass. Single-run retrieval_context_target_met is a separate
context-loading proxy and must never be presented as the release's live input-
token target. Token savings do not waive semantic/rubric review or allow edited
outputs. Provider caching/billing and output-token cost are separate metrics.
