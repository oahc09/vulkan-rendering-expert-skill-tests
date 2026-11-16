# Traditional descriptor set vs KHR push descriptors

```sh
python cases19/binding_choice/run.py \
 --tools /official-tools/bin --include /official-headers/include \
 --loader /official-loader/libvulkan.so.1 --icd /selected/icd.json \
 --libdir /selected/libraries --layerdir /validation/manifests \
 --spec-root /frozen-Vulkan-Docs-368 --max-set-allocations 1 \
 --output /fresh/output
```

The fixed scene compares set→push→set on one software CPU ICD. Each process
creates its own appropriate pipeline/layout. Two coherent SSBO buffers and the
same SPIR-V are used throughout both generations. Generation0 input is `7*i+3`;
generation1 is `7*i+103`. Each dispatch returns all64 `3*input+i` words, checked
independently. Before the second generation, the actual first fence must retire;
then the fence/command pool are reset and commands rerecorded. Both modes use the
same generation inputs, synchronization, resource sizes and complete oracle.
No asynchronous rewrite or pending descriptor mutation is performed.

The ordinary-set path creates one pool, allocates one set, updates it **once**,
and reuses it for two binds/dispatches. It is not artificially reallocated every
frame. The push path creates no ordinary pool/set and records two push commands.
Actual successful create/allocation counts and recording-call counts are emitted.
These are **application API counts**, not descriptor driver memory or measured
CPU/GPU performance. Changing a buffer's contents is not changing the descriptor;
the set remains valid while the same bindings are reused after retirement.

KHR extension advertisement, actual device extension enablement and the queried
`maxPushDescriptors` are distinct fields. The extension path does not falsely
require the promoted Vulkan1.4 core feature. The limit applies to the sum of
layout descriptor counts (two here), not merely write-call count. Unsupported
push returns exit3 and blocks full A/B/A verification; it never fabricates a push
result. The bounded policy helper can retain an independently verified traditional
baseline when push evidence is unavailable. A caller disallowing ordinary-set
allocations may have no admissible path instead.

Layouts differ in PUSH_DESCRIPTOR layout flags and have separately created
pipelines. Identical shaders do not make the two layouts compatible. Commands
happen to bind the pipeline first here; push descriptor recording does not
inherently require that order. Push descriptor state also obeys layout
compatibility/disturbance rules. No descriptor-indexing, descriptor-buffer,
update-template or shader-object path is evaluated.

`--max-set-allocations 0` is an explicit **application-managed allocation-count
policy**, not a hardware memory limit. If both actual outputs are verified, it
can select push as the only path meeting that policy. Default1 retains the
traditional baseline. `--require-performance` requires new comparable evidence;
fewer API calls are not treated as a speedup. CPU submit/fence intervals are raw
observations under Validation, not full-frame or GPU performance measurements.
Both modes request the same512 bytes on the current flags15 unified memory type.

The two wrong-reference runs change only the expected first result of generation1
and must return6. They are CPU oracle negatives, not API misuse or independent
historical defects. Normal and wrong-reference runs must produce no VVL error.
The full raw records are retained. The verifier independently checks both actual
arithmetic generations, then projects only checked numeric inputs/outputs and a
path label into the reused coherent-buffer structural gate. This does not rewrite
raw observations or claim the binding methods are the same API.

Frozen368 memory/resources/synchronization/descriptor prose is hash checked.
Raw anchors are not expanded conditional/include closure. All source/tool/header,
SPIR-V/binary and log hashes are checked at completion. No full C2/resource-binding
family, physical hardware, sustained latency or performance certification follows.
