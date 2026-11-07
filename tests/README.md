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

## v1.0.10 paired release contract

`../release-contract.json` pins the reviewed full skill SHA and exact expected
version. CI fails closed if that pin is missing; it never substitutes `main` or
an older PR. Static release checks invoke the skill's actual whitelist packer,
including its clean-tree, path, CRC and per-file hash checks. Source tracked
count, runtime package count (internal ceiling 196) and delivered context are
separate measurements. Pin changes require renewed review and evidence.

The live suite now runs 16 cases: the unchanged original 12 plus four directed
version/feature, fence exception, presentation retirement and verification-scope
cases. Rubric regexes are smoke checks only; human semantic review remains a
separate release gate. Model reads are confined to SKILL.md and runtime reference
Markdown; historical evaluation, integration test plans, answers and rubrics
are mechanically denied (including symlink aliases). Historical raw evaluation
is preserved byte-for-byte in `reports/history/v1.0.9/` with source SHA and hash.

A real release invocation requires `--expected-skill-sha FULL_SHA` and clean
skill/tests checkouts. The manifest records both revisions. Missing wrapper/model
credentials means Live BLOCKED/unmeasured, not expert behavior PASS. Mock harness
unit tests are never model evidence. Real host discovery/loading and GPU tests
remain separate, unverified gates until actually executed.

`measure_context.py --baseline-run ... --candidate-run ... --candidate-sha ...`
uses the fixed v1.0.8 baseline and ONLY the original 12 prompts for the 30% provider
input-token target, even when a run includes 16 cases. The extra four require
separate semantic scoring. `--comparison v109-regression` instead pins the
v1.0.9 baseline, reports non-regression and deliberately has no 30% target.
Historical Snapshot artifacts and previous reports are unchanged and are not
current candidate evidence.

## v1.0.11 mobile extension

The full gate now requires **28** cases: unchanged original12 + v1.0.10 directed4
+ mobile12. `MOBILE_CASES` is registered in the existing runner and rubric smoke
gate, not a parallel evaluator. Historic snapshots and original prompt hashes
are unchanged. Keyword checks require separate semantic review; none establish
mobile-device behavior or performance.

`release-contract.json` pins exact version/candidate SHA, v1.0.10 knowledge
baseline and exactly four allowed new knowledge paths. The runtime whitelist
package ceiling is 200; no knowledge deletion or arbitrary extra file is allowed.
New documents use existing full API/workflow templates and section routes; they
are not added to fixed startup. Existing answer/rubric/report read isolation is
preserved. `docs/v1.0.11-plan-source.json` hashes the verbatim implementation plan;
traceability and a deliberately unverified Device matrix accompany it.

Original input-token comparisons accept original12, prior16 or full28 manifests,
but calculate ONLY the frozen original12 cohort. Mobile usage is independent:

```sh
python tests/measure_context.py --mobile-run PATH --candidate-sha FULL_SHA
```

This audits all12 mobile cases (alone or in a full28 run), reports provider input
tokens, read bytes and rounds, and has **no 30% target**. It cannot convert model
answers into Device PASS. Run 28 smoke cases with an authorized real adapter;
release stability recommends three independent runs per case. Missing adapter
means BLOCKED. Device checks require actual target hardware/source/APK/tool
identities, input/visual correctness, failure cleanup, fixed scene and thermal
conditions; no fabricated counters, performance percentages, fault injection or
paid/cloud device access is authorized by this implementation.

## v1.0.12 system cohort

The default Live selector now contains 40 cases; the first 28 prompt bytes are frozen
in `v1.0.11-cohort.json`. SYS-01–12 each include contrasting conditions; review rubrics
are never part of model inputs. Use `measure_context.py --system-run RUN --candidate-sha SHA`
for separate usage accounting, not the original-12 token target. `media_surface_lab.py`
is a deterministic isolated state simulation, **not** Android/Vulkan/Camera evidence.
See `../docs/v1.0.12-acceptance.md` for blocked Live/Device gates and final pin procedure.

## v1.0.13 ENG13 and evidence layers

The full live registry is **64**: the byte-frozen previous40 plus ENG13-01..24.
Each ENG13 prompt contains two contrasting input conditions; these are 24 paired
scenarios, not 48 independently completed runs. Private rubrics remain in tests,
never runtime/model context. `tests/v112-cohort.json` freezes all previous40;
`original-cohort.json` still freezes the original12 token-target denominator.

`measure_context.py --eng13-run PATH --candidate-sha FULL_SHA` reports the audited
24-case cohort separately, with no 30% target and no GPU verdict. A complete64 run
may supply those cases; partial/duplicate/inconsistent evidence is rejected.
`--comparison v112-regression` compares the frozen v1.0.12 skill main and the
same old40 prompts, with **no renewed30% target**. Original v1.0.8 target and
v1.0.9 regression modes remain separate; no64-case mixed median replaces them.

The version contract requires **zero** new runtime knowledge paths and ≤200 actual
whitelist package files. Exact planned authority anchors, old40 prompt bytes,
paired input registration, section-only core contracts, known invalid stage
counterexamples and test/experiment read isolation are checked independently.

Pytest evidence markers preserve static/snapshot/live and additionally recognize:
`host_unit` (CPU contracts only), `shader_unit` (actual compiler/validator),
`vulkan_integration` (real Vulkan draw/dispatch on the named implementation), and
`mobile_scale` (actual target hardware). Those marked layers are not auto-tagged
Static. Existing mock harness tests test the harness, not model understanding.
Actual Engine Scale Lab instructions and raw output live under its fixture and
versioned reports. Never promote Python state simulations to GPU execution,
software Vulkan to Adreno/Mali performance, or an unsupported optional Mesh/async
path to an executed native pass. Preserve failures and attempted scale settings.

Final evidence must bind clean skill/tests SHA/tree, source/tool versions,
compiled artifacts, model/read/provider usage when available, scene seed/config,
implementation/device/driver/features and real output checks. Shader compile,
SPIR-V validation, ABI contract, pipeline creation and rendered correctness are
separate verdicts. Live/host/phone availability can remain BLOCKED/UNVERIFIED;
this does not authorize fabricated metrics, fault injection, credentials, paid
cloud devices, deployment, marketplace release or main merge.

## v1.0.14 VIS14 and Hybrid Quality Lab

The default registry is **84**: frozen previous64 plus VIS14-01..20, each with
primary/contrast conditions and a private semantic rubric. `v113-cohort.json`
freezes all previous64 prompt bytes. Neither fixtures nor rubrics are model input.
`measure_context.py --vis14-run RUN --candidate-sha FULL_SHA` reports only the
20-case VIS14 cohort without a new 30% target. `--comparison v113-regression`
compares the same old64 against Skill main 8d62f861; original12 v1.0.8 input-token
and other legacy comparisons remain unchanged. A full64 historical manifest
continues to work for its existing cohorts.

Run CPU contracts with `python -m pytest -q -m host_unit tests`. Run actual GPU
fixtures using `tests/fixtures/hybrid_quality_lab/README.md`; they reuse Engine
Scale Lab, do not invoke a provider, and do not prove Android device performance.
Static/Snapshot/Host Unit/Shader Unit/Vulkan Integration/Live/Android/Visual
Quality are separate verdicts. The source ledger distinguishes new pinned
normative reads from vendor dates inherited from the exact selected plan.

Candidate evidence is under `reports/v1.0.14/`. Always use final pinned clean
Skill/tests SHAs, generated artifact hashes, preregistered sequence/ROI criteria
and raw logs. Missing Live/provider, host, physical phone, OMM, power or latency
measurements remain BLOCKED/UNSUPPORTED/UNVERIFIED. No main merge or publishing.


## v1.0.15 transparency, volume and Gaussian candidate

Preredecessor skill `4a7ff82372648c4a9df91e76848cbc9c95de51a3` is merged v1.0.14.
`v114-cohort.json` freezes the 84 predecessor prompt hashes. TRAN15 adds 20 paired
primary/contrast scenarios; registry total is 104, not a count of executed models.
Original 12-case provider-token target remains unchanged. `measure_context.py
--tran15-run RUN --candidate-sha FULL_SHA` reports new-cohort usage separately,
with no invented 30% target. Rubrics and CPU oracles never enter model context.

- Static: `VULKAN_SKILL_ROOT=/path/skill python -m pytest -q -m static tests`
- CPU contracts: same command with `-m host_unit`; `transparency_host_contracts.py`
  covers FP64 composition, explicitly simulated storage, bounded overflow,
  extinction/step invariance, profile validation, footprints and full sort keys.
- Real shader/Vulkan experiment: see `fixtures/transparent_scene_lab/README.md`.
  It reuses the prior scale/hybrid lab conventions and tiny offscreen resources.
  Software Vulkan proves only the named implementation and executed path.
- Live: all 104 cases SKIP without an authorized wrapper. Historical snapshots,
  mocks, static host configuration and model-word smoke gates are not semantic
  acceptance, real-host discovery or Adreno/Mali visual/performance evidence.
- Package: immutable whitelist budget remains 200 files, zero new knowledge paths;
  source count and ZIP count are separate. Final evidence is in reports/v1.0.15.

RGBA8 128-layer low-alpha storage can exceed the fixed 0.13 quality budget in the
CPU fixture. This is an expected failed quality tier with a mathematically bounded
rounding error, not a reason to relax the threshold or blame a driver. CPU storage
simulation is not a claim about every GPU's intermediate blend precision.
