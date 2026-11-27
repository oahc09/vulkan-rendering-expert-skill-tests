# P6: offline Reference href audit

This audit reads the fixed P5 rendered reference set and the P4 all-Vulkan full specification as a **fragment lookup target**. It does not rerender, fetch external URLs, modify upstream source, or repair links. The full specification's own outgoing links are not included in the 3553-page reference occurrence denominator.

## Inputs and interpretation

```sh
/tmp/vulkan118-py/bin/python checks19/audit_reference_links19.py \
  --build-root /path/to/P5-full-build \
  --expected-report-sha TRUSTED_ORIGINAL_BUILD_REPORT_SHA256 \
  --source-root /path/to/fixed/P4-v2/baseline \
  --output /path/to/fresh/audit
```

The expected original report digest is an external integrity anchor, not authenticated authorship. The entry rechecks original rendered page hashes, source-generated input/full-spec/asset identities, and the registered 477 alias links before auditing. It emits `occurrences.jsonl` for every href occurrence and a report with occurrence counts and distinct static target/fragment counts. Repeated links are not counted as independent underlying files: for example nine missing font preload paths repeated on 3553 pages represent nine asset targets, not 31,977 independent fonts.

`PARTIAL_WITH_FINDINGS` is a successful audit with unresolved findings, **not a claim that links pass**. A malformed input, changed source/output, wrong expected digest or cancellation is `BLOCKED`. The entry is Linux/POSIX, bounded to this fixed local output and a five-minute audit budget. Fresh output is mandatory.

## Resolution model

* `a` and `area` hrefs are navigation; `link` hrefs are assets. Other href-bearing tags are identified separately, without asserting their browser-specific semantics.
* Relative paths and percent-decoded fragments are resolved within the fixed `gen/out` tree only. Empty paths refer to the current page. Fragment IDs and legacy named anchors are indexed from actual target HTML.
* Only exact registered final-component alias symlinks may be followed. Wrong/unknown symlinks, intermediate symlinks, root escapes, ambiguous backslashes and malformed percent escapes are refused or classified unresolved without reading outside the output tree.
* A root-absolute URL needs an origin and is not guessed. Any base element prevents default relative resolution for that document. HTTP(S), network-path and mailto targets are classified without access; other schemes are never executed.
* Query strings are retained, but server/query semantics are not evaluated. Local file existence is not proof of those semantics.
* Finding the same fragment in the full specification is a **candidate destination only**. It does not fix or validate the original local-fragment href. No proposed replacement is applied.

This is static href inspection, not a browser execution test. Image/script `src`, `srcset`, CSS `url()`, dynamic JavaScript navigation, visual rendering, destination semantics, external availability, and the full specification's outgoing-link completeness remain outside scope. Source line/column refers to parsed HTML location, not an upstream AsciiDoc source coordinate.

## Known source associations, not automatic fixes

The two observed missing reference-page names originate as internal anchor references:

* `chapters/memory.adoc`: anchor `vkAllocationFunction_return_rules` at line 145, reference at line 223; extracted `PFN_vkReallocationFunction.adoc` turns the reference into a `.html` link even though it is not an independent API reference page.
* `appendices/VK_KHR_shader_float_controls.adoc`: anchor `VK_KHR_shader_controls_v4_incompatibility` at line 90, reference at line 125; extraction likewise forms a missing `.html` target.
* `config/katex_replace/extension.rb` lines 24–32 contain the nine `../katex/fonts/...` preload paths. The actual reference output uses a deeper directory than full-spec HTML. The audit records missing preload paths separately from correctly resolved stylesheet/font resources elsewhere; it does not alter them.

Each source association is accompanied by the fixed source-file hash and actual lines in the report. These observations do not imply missing Vulkan API definitions. Upstream correction, regeneration and comparison would be a separate authorized change.

## Controls

HOST fixtures first pass a known local-link baseline, then remove a target page, change a fragment, or alter an alias target. They test the auditor, not Vulkan. An opt-in control uses unchanged real rendered pages, verifies a real `VkStructureType.html` navigation link, then deletes the copied target and requires a missing-target finding. No original P5 file is modified.
