# Two fixed dynamic-state reference routes

This isolated build overlay addresses only `dynamic-state-lifetime` and `dynamic-state-current-value` on the registered 26 reference pages. The actual converter-stage instrumentation retained the generated refpage as `source_location`, not the individual commonvalidity include. Consequently the authorization is the fixed source cohort, the 26 generated-page hashes and their established include relationships, the source definition span and the unique target in the fixed full specification. It is not per-xref source attribution or a general missing-fragment resolver.

The converter calls the original implementation first and preserves its output unless all reference-only, exact page/ID, source identity and absent-local-anchor gates match. It changes only that anchor's href to `../../html/vkspec.html#ID`. A valid local catalog anchor, unrelated ID, non-reference document and nonregistered page are not rerouted. Source and target preflight occurs before rendering; duplicated/missing target anchors or changed source bytes are rejected. Ruby guards use synthetic node objects against the real module, separately from real HTML rendering.

`checks19/repair_reference_dynamic_routes19.py` takes the fixed P4 `--source-root`, private `--runtime-root`, the font-render `--baseline-build`, its final offline `--baseline-recheck`, and fresh `--output`; optional `--cancel-file` uses the existing owned-process supervisor. It copies the source, preserves the font patch, installs the new explicit overlay, removes the copied reference HTML directory, and executes official all-Vulkan 1.4.368 `manhtmlpages -j4` for all 3553 pages. The fixed input sources and old P4/P5/P6 evidence are not modified.

All 3553 results must equal the font-repaired baseline except exactly 4581 href replacements across 26 pages. The remaining 3527 pages and every other byte are unchanged. Existing source-derived Name/section/C-code-identifier checks and 477 exact aliases remain enforced. A separate official single-page reversion render must restore the font-baseline bytes; the saved freshly repaired bytes are then restored to the final inventory, explicitly recorded. This control is not another full render.

The full offline href audit runs unchanged: other broken links remain findings and external links are not fetched. Actual source snapshots are saved before execution; stdout/stderr hashes are saved after every step, including failed steps, and rechecked at completion. Scope remains static fixed-configuration navigation, not browser behavior, normative text correctness, alternate configuration, or upstream acceptance.

Source attribution: the fixed source excerpt/definition spans come from [Khronos Vulkan-Docs fa30d4e](https://github.com/KhronosGroup/Vulkan-Docs/tree/fa30d4e312e843193601be7cb926c7e25d9ec885), `chapters/pipelines.adoc` and `chapters/commonvalidity/*` (Khronos Group, CC-BY-4.0). Original source headers and license files remain in the isolated copy. The new routing overlay and HOST assertions are separately added by this project; no normative wording is edited.

## Retained preliminary probes and full run

A source-location observation run rendered vkCmdDraw without changing its HTML
and recorded 180 candidate references; it did not retain original include-file
coordinates. A separate one-page routing probe changed only expected hrefs. The
first standalone Ruby guard harness failed because it omitted loading Asciidoctor
before its converter; that NameError log is retained, followed by a corrected
harness and the actual guard step in the final run. None is relabeled as full
cohort acceptance.

The complete run then freshly rendered 3553 pages in 333.4 seconds. Actual
comparison found 1873 lifetime and 2708 current-value href replacements across
26 pages, with 3527 other pages unchanged. All 477 aliases remain valid. The
whole href audit reports 197731 resolved local occurrences, 2 missing page targets,
11699 missing fragments and 14670 unfetched external/mailto links. Remaining
findings are not repaired or waived. The compact report and retained evidence
digests are in `coverage/v1.0.19/reference-dynamic-route-repair.json`.
