# P6: delayed-include fragment routing diagnosis

The independent source/HTML audit in
`coverage/v1.0.19/reference-dynamic-fragments.json` binds Vulkan-Docs commit
`fa30d4e312e843193601be7cb926c7e25d9ec885` and the unchanged P5 outputs.
It identifies 2708 `dynamic-state-current-value` and 1873
`dynamic-state-lifetime` href occurrences across 26 generated reference pages.
Every current-page target is absent; both target IDs occur uniquely in the
corresponding actual full specification. This is not a checker path/fragment
false positive, nor absent normative text for these two anchors.

`genRef.py` remaps but does not expand commonvalidity include directives.
Its `xrefRewrite` operates on the extracted strings before those includes are
expanded. The generic `<<...>>` references arrive later during Asciidoctor
processing, and therefore remain local `#fragment` URLs. All 26 generated
refpage sources retain `draw_common` includes and neither target string occurs
directly in their extracted text. The existing Makefile `html_spec_relative`
attribute does not by itself redirect ordinary AsciiDoc local xrefs.

This is a generation-stage routing defect, not a missing configuration value
that can simply be set to make all links correct. The report records fixed
source lines/hashes, original anchor definitions, include boundaries, rendered
page hashes, exact occurrence counts and a proposed narrow repair probe.
**The probe is not executed and these fragments are not repaired here.**
A later isolated repair must bind source relationships and target uniqueness,
preserve valid local references and all unrelated bytes, and reject absent or
ambiguous full-spec anchors. It must not globally rewrite every same-named
fragment merely because the full specification contains it. The other 11699
missing-fragment occurrences remain separately unclassified by this diagnosis.

The font-preload rebuild is independent: it fixes asset paths only, retaining
all 16280 original missing-fragment occurrences. Neither diagnosis nor successful
rendering implies full P closure, alternate-configuration/SC review, browser
navigation, or normative semantic acceptance.

## Source attribution

Original source excerpts in the report remain unmodified; generated-page/include
coordinates and explanatory classifications were added by this project.
Sources: [fixed Vulkan-Docs tree](https://github.com/KhronosGroup/Vulkan-Docs/tree/fa30d4e312e843193601be7cb926c7e25d9ec885).

- `chapters/pipelines.adoc`: Copyright 2015-2026 The Khronos Group Inc.; SPDX-License-Identifier: CC-BY-4.0.
- `chapters/commonvalidity/draw_common.adoc` and `draw_vertex_binding.adoc`: Copyright 2019-2026 The Khronos Group Inc.; SPDX-License-Identifier: CC-BY-4.0.
- `scripts/genRef.py`: Copyright 2016-2026 The Khronos Group Inc.; SPDX-License-Identifier: Apache-2.0.
- `Makefile`: Copyright 2014-2026 The Khronos Group Inc.; SPDX-License-Identifier: Apache-2.0.

See [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) and
[upstream license texts](https://github.com/KhronosGroup/Vulkan-Docs/tree/fa30d4e312e843193601be7cb926c7e25d9ec885/LICENSES).
