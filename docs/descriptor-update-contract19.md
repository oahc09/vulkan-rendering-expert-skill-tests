# Consecutive descriptor updates: bounded HOST model

```sh
python checks19/run_descriptor_update_contracts.py \
 --descriptors /path/to/frozen368/chapters/descriptorsets.adoc \
 --validusage /path/to/frozen309/validusage.json --out /fresh/output
```

Eleven fixed controls check consecutive binding routing and ordered reference
writes/copies. Exact raw source hashes, slice boundaries/conditional directives,
309 VUID entries and implementation hashes are recorded. 309 clause00317 combines
type/stage; 368 separates stage10776 and binding flags10777. The tool does not
claim identical clause coverage across these versions. Immutable reference
identity uses368 prose, not just30900318's presence/absence condition.

`spill` accepts a caller-proven dense binding table with explicit zero-count
holes. It skips zero-count bindings, checks nonzero participating bindings for
matching type, stage flags, binding flags and declared immutable reference
signatures, and returns individual binding/element coordinates. Signatures mean
identical sampler references, not identical sampler creation parameters. No
sampler object or format support is actually checked.

The starting array element must be inside the initial nonempty binding in this
model. Missing binding numbers, starting at/beyond its count, mutable/inline
uniform types and unsupported metadata return UNKNOWN, not a Vulkan invalidity
claim. Model bounds are128 bindings/operations and4096 descriptors, not device
limits. Extension flags require separate applicability proof.

`apply` is narrower: ordinary UBO/SSBO reference tokens and zero binding flags.
It performs the entire write array first, then the copy array; order within each
array is preserved. Later copies observe prior writes and earlier copies. Same-set
source/destination overlap is rejected even across bindings. Undefined or
already-destroyed references may be copied; the destination becomes undefined.
Copying references is not resource content access or initialization. New write
payloads explicitly marked dead or undefined instead return UNKNOWN with no
modeled final state; the copy permission does not authorize such writes.

All resource/descriptor payload validity, update concurrency and lifetime
preconditions remain external caller proofs. A rejected model returns no final
state; this does not imply real vkUpdateDescriptorSets is transactional or that
an invalid real invocation rolls back earlier operations. No actual Vulkan/GPU
work is performed and full semantic/release acceptance remains unestablished.
