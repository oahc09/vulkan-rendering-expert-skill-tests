# Pending packed glyph + shader clip + active MRT, one draw path

`VULKAN_TEXT18_JOINT_LIFECYCLE=1 python -m pytest -c tests/pytest.ini tests/test_text18_joint_lifecycle_lab.py`
requires the established local software-Vulkan and trusted glyph dependencies.
No font/source upload or download. Static tests exclude this integration marker.

This is **not** a merger of independent test summaries. The authored adapter
builds one new pipeline used inside the existing actual combined lifecycle
engine, in the same process/device/queue/submission. That pipeline consumes
real packed glyph vertex UVs, executes all three clip predicates in its fragment
shader, and targets three active color attachments. independentBlend is queried
and enabled. The fragment shader emits changed velocity/ID values; their write
masks are0 and actual readbacks must remain exact. There are no UNUSED refs or
preserve fallback in this new pipeline. No depth attachment is claimed here.

The shared combined Engine's exact real lifecycle executes unchanged: A upload
and publish, timeline-gated old A draw, B upload queued behind it and canceled
while pending, reject pending retirement/publication, signal/wait, old A
published-route draw, legal diagnostic canceled B draw, B retirement, new B
generation upload/publish, reject rollback, gated new draw and old A retirement.
Each submission owns its vertex/readback/attachment/staging resources. Candidate
cancellation affects host routing, not cancellation of Vulkan execution. The
ALL_COMMANDS gate proves pending submission, not shader already running.

Three copies of actual trusted O coverage use packed atlas UVs at fixed
screen positions(25,25),(11,19),(27,10). CPU-only boundary analysis selected these
positions before the first joint GPU run; each omitted clip predicate exposes
nonzero glyph coverage. `conditions.json` records per-layer bypass and positive
visible pixel counts before compilation/execution of the joint pipeline. This
fixed placement gives22/38/25 affected nonzero pixels for bypassing rectangle/
circle/rotated-rectangle respectively, and252 positive visible nonzero pixels.
The GPU receives the full unmodified atlas, NOT a clipped mask. The CPU oracle
uses original glyph pixels and the existing independent rectangle/circle/ray-
crossing rotated-polygon predicates to zero reference samples outside all three
clips. Predeclared1e-6 color tolerance and exact sentinels remain unchanged.

The main lifecycle makes exactly4 draws:3 positive images (old-A, retained-A,
and new-B), plus1 diagnostic wrong-route image. Other negative/preparation runs
are not counted as positive joint frames. The diagnostic
canceled-page route is required to fail the independent reference. Four separate
negative runs execute the full real lifecycle with valid Vulkan: each clip layer
bypassed in turn, or auxiliary color-write masks enabled. Correct error category
must be observed. The controlled pending exception releases gates and validates
cleanup. Outer pytest separately rejects stale new-page readback and forged
publication events on copies, not original evidence. Negative runs do not count
as positive combined evidence.

This is fixed pixel-center hard shader clipping, not clip AA/stencil, arbitrary
path stacks, or a GPU mask-producer→sampler pass. It is one controlled nearest
integer glyph layout and lifecycle, not full asynchronous renderer, production
allocation/device-loss cleanup, sustained memory leak proof, multithreaded routing,
multiple physical GPUs or target-platform/Live acceptance. Generation2 scales
original coverage by0.5 as in the previous combined fixture.

Preparation invokes earlier fixtures only to build trusted glyph/pipeline inputs;
their independent successes are not reported as joint coverage. Joint evidence
is the new binary's `frames/` output plus actual lifecycle records. Runtime
validation and SPIR-V validation are required. Native120s/outer240s deadlines.
Raw images, input/source/tool/driver receipts stay local; public evidence is
source and numerical summaries only.
