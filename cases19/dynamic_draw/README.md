# Bounded dynamic rendering graphics draw
Standalone original in-repository deliberate fault injection, not external production evidence. Not part of the historical five-chain delivery index.

```
python -O cases19/dynamic_draw/run.py --tools OFFICIAL_TOOLS --include HEADERS --loader LOADER --validusage VALIDUSAGE_1_4_309 --output FRESH_DIRECTORY
```

Vertex gl_VertexIndex full-screen triangle and fragment gl_FragCoord parity produce a4×4 red/blue checker. Real GLSL compilation, SPIR-V validation and disassembly are individually logged and hashed. CPU independently enumerates row/column parity and checks every RGBA pixel after actual graphics pipeline/draw→color-write/transfer-read dependency→copy→host dependency→fence/coherent map. Nonconstant oracle rejects clear-only, constant output, red/blue channel swap and Y inversion. Symmetric checker does NOT detect transpose. No raster boundary pixels or fractional color conversions used.

Actual features/core1.3, framebuffer/viewport/color limits, format+usage+sample query and memory selections are checked. Pipeline format/sample/viewMask, draw counts, viewport/scissor and raster/blend/write state come from actual structures used. Tools policy is bounded to the exact ordinary fixture, missing fields UNKNOWN; no hidden support for extended features.

`format` negative uses pipeline B8G8R8A8 versus view RGBA8, without enabling dynamicRenderingUnusedAttachments: vkCmdDraw VUID08910 (validusage1.4.309). Validation callback returns true, reset discards whole command buffer, no EndRendering/submission of invalid scope. `wrong-output` compares actual pixels with inverted red/blue expectation and exits6; this tests the oracle, not another driver defect. Normal output exits0 with no errors, cleanup checked.

Normative source: original schema2 validusage1.4.309 pinned SHA in runner; drawing prose tag v1.4.309 blob77c199718a6d74d179af4536df47f3cdc5fe25ad. CPU ICD only, no physical GPU/mobile/performance acceptance; no blend/depth/resolve/multiview/general pipelines/fullVK10 or full-domain milestone claim. Noncoherent unavailable path is not substituted. Independent resources are not falsely correlated to earlier cohorts.

Runner also consumes the existing dynamic_color19 attachment admission and records its exact source hash. Actual stageMask17, triangle topology3, absent depth state and firstVertex/firstInstance0 are now emitted from pipeline/draw structures and rule-checked. GLSL semantics still require separately inspectable hashed sources and actual pixel oracle, not merely stage bits.
