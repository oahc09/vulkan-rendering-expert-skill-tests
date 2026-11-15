# Opt-in real tools, not GPU acceptance

Requires official Vulkan headers/loader, Khronos Validation layer, CPU software
ICD, C compiler, Python and Perfetto Trace Processor. No automated downloads or
system changes are performed. Use compatible versions and explicitly select the
local ICD/layer; do not point this CPU-only probe at a production GPU process.

```sh
cc -Wall -Wextra -Werror validation_probe.c -lvulkan -o /tmp/validation_probe
# Set VK_DRIVER_FILES, VK_LAYER_PATH and, for a local extraction, LD_LIBRARY_PATH.
python -O run_tool_capture.py --probe /tmp/validation_probe \
  --trace-processor /path/to/trace_processor_shell \
  --layer-manifest /path/to/VkLayer_khronos_validation.json \
  --output /tmp/probe19-capture
```

Raw callback/trace/CSV stay at the local output. Only a summary has been checked
in. Layer spec+implementation are enumerated and matched to the selected manifest;
device identity must report a CPU ICD. Perfetto consumes measured subprocess
spans, not fabricated durations. Times are CPU monotonic, not GPU clocks.
The size-zero call is aborted by VK_TRUE from the error callback.

Run with an empty layer directory: must fail. Build a mutant replacing
`size=bad?0:16` with `size=16`: bad invocation must exit 5. Run the CPU contract
tests, including wrong VUID, event name/time/count, duplicate IDs and python -O.
A good path with no error callbacks is NOT a proof of correctness or warning-free
execution; the callback subscribes only to validation ERROR severity.
