# Ordinary UBO descriptor update rule/tool pair

Original bounded API experiment, not an external project or shader workload.
Runner compiles probe.c against official Vulkan headers/loader using gcc. Explicitly select CPU ICD and Validation layer. Then:

    python -O cases19/descriptor/run.py --include /path/to/headers --loader /path/to/libvulkan.so.1 --output /tmp/new-ubo-run

Two legal updates (explicit range and WHOLE_SIZE) and three illegal updates
(zero range, range beyond buffer, offset at end) must exactly match the host
rules' VUID sets against actual queried maxUniformBufferRange/alignment.
The layer aborts illegal calls. No shader is compiled or dispatched, no timing
result is measured, and clean updates are not proof of correct shader access.
Raw handles remain local; committed evidence has source/binary/callback hashes.
Pool/layout/write counts are fixed to one in this experiment. General counts,
dynamic offsets, null/sparse, indexing and descriptor-buffer paths stay open.
