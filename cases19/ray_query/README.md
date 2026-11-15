# VK14 bounded BLAS → TLAS → compute ray query

Repository-authored CPU ICD fixture, not an external production defect. This is a standalone complete device-build/query/readback chain, not ray-tracing pipeline/SBT or full VK14 acceptance.

Vulkan1.2 core BDA and KHR acceleration_structure, deferred_host_operations, ray_query support are queried and enabled separately. Only a unique CPU physical device with compute queue and R32G32B32_SFLOAT AS vertex format is admitted. Host AS commands are neither required nor used.

One opaque nonindexed triangle(-1,-1,0),(1,-1,0),(0,1,0) builds BLAS. A single identity instance references the actual BLAS AS address (not assumed buffer address), customIndex7, mask255; it builds TLAS in a SEPARATE build command. Independent scratch buffers are sized using actual build-size queries plus alignment padding, and device addresses are aligned. Relevant allocations use DEVICE_ADDRESS and correct input/storage/scratch usage flags.

Explicit AS_BUILD/AS_WRITE→AS_BUILD/AS_READ, AS_BUILD/AS_WRITE→COMPUTE/AS_READ, and COMPUTE/SHADER_WRITE→HOST/HOST_READ dependencies precede the successful fence. Coherent inputs are populated before submission; all referenced objects remain alive until completion.

Two rays have origins(0,0,1) and(3,0,1), direction(0,0,-1), interval[0.1,10]. Origins are actual push constants; direction/interval are shader constants, bound by shader/SPV hashes. The loop calls rayQueryProceed until complete. Only committed triangle hits read custom index, t and primitive index; miss uses sentinel instead of querying invalid attributes. Output per ray is[type,customIndex,tFloatBits,primitive]. Hit distance must be finite and within absolute1e-5 of the independent geometric result; other output words are exact. This tolerance is specific to the fixed unit-scale fixture, not a general ray accuracy guarantee. Python independently computes fixed-geometry Moller-Trumbore intersection from reported ray facts.

Good: hit[1,7,1.0,0], miss[0,UINT_MAX,0,UINT_MAX]. Wrong-output deliberately expects hit type0 and exits6 despite valid execution. Offset negative creates AS with offset1 and backing buildSize+256, isolating03734; callback-abort result is checked, invalid output handle is setNULL, no build/submit occurs. Initial exploratory09542 exposed missing AS backing BDA usage; source corrected before the versioned successful cohort. That debugging observation was not retained as an independently source-paired failure experiment and is not counted as another causal repair acceptance. No failed experiment is relabelled successful.

## Reproduce
Set trusted CPU ICD/Validation VK_DRIVER_FILES/VK_LAYER_PATH/LD_LIBRARY_PATH and MESA_SHADER_CACHE_DISABLE=true:
```
python -O cases19/ray_query/run.py --tools TOOL_BIN --include HEADERS --loader LOADER --validusage VALIDUSAGE --output FRESH_DIRECTORY
```
Raw build/compiler/validator/disassembler logs, source/SPV/tool hashes, actual buffer addresses/types, size queries, geometry/instance, dependencies and output are retained. Addresses are local per-run facts, not portable handles. Timeout/API/unexpected VVL errors cannot produce success summary.

Normative excerpts in normative.json are checked against the exact full validusage1.4.309 SHA. Rule acceptance is bounded; no compaction/update, procedural/intersection shaders, noncoherent memory, multi-queue, hardware traversal/performance or full-domain claim.
