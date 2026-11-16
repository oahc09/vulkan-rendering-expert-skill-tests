# Authored real-API transfer repair loop

Original deliberate fault injection, NOT a discovered external production bug.
The baseline omits fill-to-copy visibility. Validation aborts the invalid command.
fix.patch enables the already-written precise barrier. run.py applies the actual
patch and compiles baseline, repaired and independent dstAccess=0 mutant paths.
Repaired output must contain 64/64 expected words after submission/fence wait.
Baseline exit0 means expected diagnostic reproduced, NOT valid buggy execution.
Mutant exits6. All runs must use the same CPU ICD; no physical GPU/performance claim.

Set explicit local VK_DRIVER_FILES, VK_LAYER_PATH and library path, then run:

    python -O cases19/transfer/run.py --include /path/to/headers --loader /path/to/libvulkan.so.1 --output /tmp/new-transfer-run

Requires gcc, patch and official Vulkan tooling. Performs no installation.
Output must be new. Raw callbacks contain handles and remain local; checked-in
summary contains hashes/scoped results only. Skill buffer_memory_barrier.md
contains the delivery19-transfer-contract L1/L2 explanation. Production recovery,
cross-queue ownership, noncoherent memory, SC and external blind tasks stay open.
