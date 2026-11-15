# Bounded actual CPU font cache cost ledger

Original plan §7.1 and §13.1 resource/cost accounting, not a new performance target.
This fixture exercises actual trusted DejaVu Sans HarfBuzz shaping and FreeType
per-glyph grayscale production. Layout and glyph payload caches are separate.
Layout identity includes font SHA/index, HB/FT versions, face generation, text,
explicit LTR and en/fr locale. Glyph identity includes the same identity and
actual glyph ID, pixel size and fixed gray-normal/no-axis/no-style/phase-zero
configuration. This API does not support variable axes, alternate representation,
custom fallback chains, palette, hinting options or subpixel phase; those are not
silently omitted configurable fields. It is a single-owner diagnostic cache,
not a thread-safe production font service or GPU atlas.

Twelve rounds clear *application* caches then request OFF twice. Every cold
round executes one HB call and two FT producers (repeated F reuses a glyph);
every hot request executes neither. Independent Mock spies wrap actual provider
entry points and are checked against provider counters. A direct uncached
provider path verifies complete shaping receipt and bitmap bytes, not typography
quality against an independent shaper. Font parsing handles are not retained.
Size changes preserve layout but regenerate coverage; locale changes reshape
but reuse unchanged glyphs; generation changes both layers. Capacity-one LRU
eviction provably produces again. Caller mutations cannot change stored data.
A byte-oversize glyph is not published; its already-completed layout may remain.
This is not all-or-nothing batch rollback or proof of native allocation cleanup.

Timing uses perf_counter_ns: shape includes font I/O, SHA verification and
HB face/font/buffer setup and destruction; raster includes FT face setup,
load/render and copying owned coverage. Request includes lookup/copy and any
miss work. Report nearest-rank p50/p95/p99 with sample counts; twelve rounds
are a bounded observation, NOT stable tail-latency characterization or a
cold-faster/slower-than-hot requirement. No process restart, OS page-cache
purge or native library cold start is claimed. Provider initialization is
outside request timers. Owned bytes count coverage payload only, not Python
object overhead, FT/HB allocator heap, VRAM or peak process memory. Cache clear
returns tracked entries/payload to zero; Python/native allocator retention is
not measured. JNI, upload, draw, total frame time, power/thermal remain
UNMEASURED. Existing GPU upload-budget evidence is separate, not a joint run.

Opt in with TEXT18_CACHE_COST=1 and VULKAN_SKILL_ROOT, using the existing
Python environment with freetype-py and trusted system font. The integration
marker selects the repository's external-environment cohort; **no Vulkan API
or GPU is exercised by this CPU-only test**. Raw provider/version/font receipts
stay local. Sanitized timing/count summaries contain no environment paths.

Cold and hot request distributions are reported separately (12 samples each);
per-round cold shape/raster samples and zero hot production samples are retained.
The mixed request distribution also includes invalidation/copy checks. Deliberate
stale-key negative overwrites actual 24px cache slots with 20px payloads, then
compares the resulting cache hit against uncached 24px production. This is fault
injection bypassing the production cache API, not a supported mutation API.
Diagnostic timer lists survive clear and are not charged to the payload budget;
steady-state claims apply only to layout/glyph entries and owned coverage, not
all instance memory. Constructor budgets are bounded strict integers.
