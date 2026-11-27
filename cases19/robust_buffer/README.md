# VK18 bounded protected SSBO + NULL descriptor cohort

Original repository-authored controlled experiment, not an external production defect.
Two distinct coherent buffer allocations (source+output); three descriptor bindings, the third truly NULL.
Actual extension/features are queried then core robustBufferAccess, robustBufferAccess2 and nullDescriptor are explicitly enabled for the positive dispatch. No unprotected out-of-bounds dispatch is performed.

Source range is at least16 bytes and divisible by4 and queried robustness alignment; physical source size adds16 guard bytes. Source uints start100+i. A one-invocation shader reads first/last in-bounds values, the first fully out-of-bounds uint and NULL resource, then writes a DIFFERENT out-of-bounds address and NULL resource. Output must be [100,last,0,0]; full source including guard must be unchanged. The disassembly check binds descriptors, local size, push offset, absence of atomics and both protected writes after all protected reads; it is not a general SPIR-V proof.

Compute write→HOST read dependency and a successful fence precede coherent readback. Runtime allocation masks/types/flags, actual bounds, enabled state and raw arrays are retained. No images/BDA/atomics/pipeline robustness overrides, noncoherent memory, physical GPU behavior or full VK18 claim.

Modes: good exits0; wrong-output deliberately expects OOB value1 and exits6, with no VVL error; null-disabled uses a separate device invocation and only updates a NULL descriptor(offset0/WHOLE_SIZE), getting02998 callback-abort before bind/dispatch. Callback update is a void API, not a fabricated error VkResult.

## Run
Set VK_DRIVER_FILES, VK_LAYER_PATH, LD_LIBRARY_PATH to the trusted CPU ICD/Validation tool cohort and MESA_SHADER_CACHE_DISABLE=true. Then:
```
python -O cases19/robust_buffer/run.py --tools TOOL_BIN --include HEADERS --loader LOADER --validusage VALIDUSAGE --output FRESH_DIRECTORY
```

Normative: full validusage schema2/API1.4.309 fixed SHA in normative.json; exact02998/02999/04000 excerpts retain owner/condition. Robustness semantics are separately reviewed against Vulkan-Docs tagv1.4.309 features chapter blob e8e07194550ac4f2a28c58939c1df42631338f60. Core robustBufferAccess alone does NOT establish the strict zero/discard oracle. Rounded descriptor padding and store-then-load exceptions are excluded by this setup. Standalone cohort is not automatically part of prior five-chain delivery bundle.
