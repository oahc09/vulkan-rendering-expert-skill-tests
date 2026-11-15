# Ordinary memory binding HOST contract

```sh
python checks19/run_memory_binding_contracts.py \
 --resources /path/to/frozen368/chapters/resources.adoc \
 --memory /path/to/frozen368/chapters/memory.adoc \
 --validusage /path/to/frozen309/validusage.json --out /fresh/output
```

26 authored HOST controls verify caller-declared arithmetic and lifetime facts.
No allocation, binding, free or GPU command is performed. Exact368 raw section
hashes and separate309 VUID entries are recorded; includes and outer conditions
are not evaluated, and whole normative coverage is not claimed.

Binding uses memory requirements size/alignment/typeBits, not logical resource
size. Offsets and sizes are exact uint64; memory type indices are0..31. A normal
non-sparse resource cannot be rebound. Dedicated bindings require matching
resource identity and offset0 in the ordinary branch; preference is not a
requirement. Same device, valid allocation creation and ordinary scope are
independently established caller facts. Sparse/disjoint, external/protected,
NV dedicated and dedicated-image-aliasing exceptions are not modeled.

Dedicated allocation creation has an explicit version split: frozen309
02964/02965 require allocationSize equal requirements.size; frozen368 uses
allocationSize >= requirements.size. The helper only checks that size condition
for ordinary nonimported memory. Identical VUID numbers do not imply identical
text. Binding acceptance never independently validates allocation creation.

Granularity checks an ordered, nonoverlapping adjacent pair in the same memory
allocation, using requirements sizes and caller-proven linear/nonlinear class.
For simultaneous mixed classes, floor((A.offset+A.size-1)/g) must be less than
floor(B.offset/g). A one-byte gap can suffice across pages. This is not minimum
distance, generic binding alignment, resident page size or nonCoherentAtomSize.
Failure reports aliasing risk, not a fabricated bind VUID. Non-simultaneous use
requires separately proven lifetime/synchronization safety.

Memory may be freed with objects still bound if all submitted uses and relevant
host accesses have retired and those resources will not subsequently be used.
Bound-object count alone is not a rejection. The helper does not validate every
handle, allocator, concurrency or destruction requirement. No complete API,
L1/L2 or release acceptance follows from these limited caller-fact checks.
