# VK13 serialized headless WSI lifecycle

Repository-authored CPU ICD experiment, not a production defect or physical display test. Uses actual EXT_headless_surface and KHR_swapchain plus EXT_swapchain_maintenance1 present fences. Requires extension dependencies surface_maintenance1/get_surface_capabilities2; no X server or new software installation.

Two application-selected swapchain generations4x4→8x4, each two distinct endpoint-color frames. Actual surface formats/modes/count/extent/transform/composite/usage capabilities and optimal2D imageformatproperties are queried. Format37/44 UNORM and colorspace0 only; Python independently decodes RGBA/BGRA bytes and checks every pixel.

Each frame: acquire binary semaphore→TRANSFER-stage wait+matching TRANSFER→TRANSFER transition→clear→TRANSFER write/read dependency→copy to coherent buffer→PRESENT layout→present waiting on renderDone. Separate render fence establishes readback; explicitly attached maintenance present fence establishes WSI resource retirement. Both waits complete before semaphore/fence reuse. QueueWaitIdle is additional conservatism, NEVER substituted for present fence. This is serial, not frames-in-flight performance evidence.

Old generation's two present fences complete before vkCreateSwapchainKHR(oldSwapchain); old handle is retired at that call and never acquired again. Successful replacement precedes destruction; new generation independently clears unknown initial layouts. This is intentional extent selection, NOT a genuine window resize, OUT_OF_DATE or physical display observation.

Invalid-acquire mode has semaphore/fence bothNULL and timeout0: exact01780 callback-abort, resultchecked; output index never consumed. Wrong-output computes an alternative expected first byte(255-normal), records it, verifies mismatch and exits6; normal pixels still checked independently. V1/V2 failed compilation due warning-as-error and are not passing cohorts.

On incomplete acquire/submit/present retirement after failures, the probe exits nonzero without unsafe Vulkan destruction; it does not claim recovery or successful cleanup. A process timeout cannot generate a success report. OS process reclamation is not a GPU/WSI fault-recovery acceptance.

Run with trusted ICD/Validation VK_DRIVER_FILES/VK_LAYER_PATH/LD_LIBRARY_PATH and MESA_SHADER_CACHE_DISABLE=true:
```
python -O cases19/headless_wsi/run.py --include HEADERS --loader LOADER --validusage VALIDUSAGE --output FRESH_DIRECTORY
```
Exact validusage1.4.30901780 excerpt retained in normative.json and checked against full source hash. Standalone bounded cohort, not completeVK13 or prior diagnostic bundle acceptance.
