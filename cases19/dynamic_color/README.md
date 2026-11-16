# Single color dynamic rendering lifecycle
Original deliberately injected repository faults, not an external-production bug.

Run with the established CPU ICD and Validation environment:
```
python -O cases19/dynamic_color/run.py --include HEADERS --loader LOADER --validusage VALIDUSAGE_1_4_309 --output FRESH_DIRECTORY
```

Real API1.3 device feature query and explicit enable; RGBA8_UNORM optimal COLOR_ATTACHMENT|TRANSFER_SRC combination query; compatible image memory and image view; coherent readback allocation. Four-by-four color image transitions from UNDEFINED to COLOR_ATTACHMENT_OPTIMAL. First pass CLEAR magenta + STORE, explicit color-write→color-read|write dependency preserving layout, second pass LOAD + STORE with green clearValue (ignored by LOAD). Transition to TRANSFER_SRC, copy, transfer-write→host-read, fence then all16 pixels exactly255,0,255,255. No shader/draw/pipeline experiment. Green mismatch is an oracle negative, not an independently injected GPU fault.

Independent invalid BeginRendering modes: renderArea width5 exceeds view4 (06079), TRANSFER_SRC attachment layout (06135), supported but not enabled dynamicRendering (06446). Validation callback returns true; the void command is aborted, command buffer immediately reset/discarded, never EndRendering or submit that invalid scope. Exact phase/diagnostic count and cleanup checked; absent/unexpected diagnostics or timeout fail closed. Callback-aborted void commands have no VkResult and no fabricated VK_ERROR_VALIDATION_FAILED return.

Policy reads actual configuration and preserve-dependency manifests. Known full-region CLEAR/STORE defines content; LOAD preserves only defined content with synchronization; DONT_CARE is not defined. Source and original schema2 validusage1.4.309 SHA bind observed clauses. No mobile/hardware, performance, resolve, depth/stencil, multiview, layered/subregion/extended layouts or full VK10 claim. Noncoherent path remains untested; this fixture requires host coherent compatible memory. Source, binary, loader, layer/ICD manifest and raw logs are hashed.

The C manifest supplies origin, actual samples/layers/viewMask/resolveMode and image extent. Missing scope facts are UNKNOWN; nonzero origin, non-single-sample/layer or multiview/resolve are OUT_OF_SCOPE. Second-pass prior-defined state derives from first-pass content policy. maxWidth/maxHeight are image-format capabilities, not framebuffer limits; framebuffer-limit and tracked-layout proof remain separate explicit obligations. Selected physical API must support core1.3; this path does not substitute an unenabled KHR extension.

Prose source: Khronos Vulkan-Docs tag v1.4.309 `chapters/renderpass.adoc`,
Git blob `83a7d8bd4ed10ff3a2cbd55ea5e50aea0a822d72` (CC-BY-4.0).
Generated validusage1.4.309 is separately hash-pinned; the older full-scope
vk.xml1.4.368 denominator is not merged into this source cohort.
The source-paired retained snapshot test does not rerun the device. A fresh run
is required after changing the C probe, runner or rules. Development v6 rejected
a duplicate/conflicting samples manifest; it was corrected by separating actual
samples from format support masks, not counted as a successful run.
This standalone family does not silently extend the previous five-chain bundle.
