# Image-copy size compatibility and mip-edge contracts

This is a bounded C1 semantics increment, not another GPU experiment.

## Actual card contradictions repaired

`copy_blit_resolve.md` previously required equal block extents for all compatible
copy formats. Fixed368 normative text allows size-compatible compressed versus
uncompressed representations. Both-compressed copy additionally requires equal
block extents (separately pinned309 VUID09247). A second checklist falsely made
block alignment absolute despite the same card already allowing mip-edge extent
exceptions. The repair keeps **offset** alignment strict and makes the **extent**
exception conditional on exactly reaching the appropriate mip boundary.

## Versioned primary sources

Original Khronos Vulkan-Docs commit fa30d4e312e843193601be7cb926c7e25d9ec885:
- formats.adoc:9360d12ae4c69c9eb7cf374dc3c99c061b6386f1551b9b4648d14728101cb7f1
- copies.adoc:b821b4b219c3e7e691332b651c40cd169b74017d7212aad9d1ddbeef8acbec05
- commonvalidity/copy_image_common.adoc:7251d3047441e1be6bf16f4669393ae31b957dea61b3a737ef6a35998b1ef6e0

Paths are under `chapters/`; source license CC-BY-4.0, copyright Khronos Group.
Exact raw selected anchors and the named common-validity include are bound.
Other includes, alpha-format feature variants and all normative closure are not
silently expanded. The309 VUID corpus is independently pinned, not merged into a
claim that these sources are one uniform version.

## Do not invent a unique coordinate conversion

The normative size relation equates ceil-divided block counts. It does not choose
one unique partial-edge destination extent. A full-block representation is only
one mathematical representation, not automatic approval of a VkImageCopy region.
The planner does not invent rounding for nonzero cross-block destination offsets.
Single-image range tests consume already-known image coordinates. They do not
prove the complete command's mapping, queue granularity, format support, aspects,
layouts, usage, multisampling, overlap or synchronization.

Examples: BC1(4×4,8bytes) and R32G32_UINT(1×1,8bytes) are size-compatible in this
limited ordinary-color contract; BC1→RGBA8(4bytes) is not. Two compressed formats
with unequal block extents still fail the extra requirement even when both have
16-byte blocks. Mip width7, aligned offset4 and extent3 reaches the boundary;
offset3 is not excused by reaching it, and extent2 fromoffset4 does not reach it.
None of these operations decodes compressed pixels or converts color values.

Caller-proven format metadata is not discovered hardware capability. Alpha-only formats (not ordinary RGBA),
multi-plane, depth/stencil and unsupported special scopes remain unknown. Pure
positive/negative controls do not upgrade real device coverage, complete L1/L2,
SC, Live/blind or the original36 final tasks.

## Reproduce

Run `checks19/run_image_copy_contracts.py` with `--formats`, `--copies` and
`--common` pointing to the three fixed368 files above, `--validusage` pointing
to the fixed309 corpus and `--out` a new directory. It checks all source byte
hashes and19 fixed HOST outcomes before writing a report, including exact
implementation hashes. Metadata fields are caller declarations, not a format
table query. The result deliberately never says the entire copy command is legal.
