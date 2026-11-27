# Registered real-font text representation choice

This entry reuses the unchanged original Scene A board, refined board and compact
budget board. It runs the three labs once, in that order. All subsequent policy
comparisons reuse that same measured data, not independent GPU executions.

The original seven rows include actual FreeType unhinted rasterization, HarfBuzz
layout, CJK, ligatures, combining marks, bidi, variable axes and a bitmap emoji.
The independent outline reference uses subdivided curves and sampled pixel
coverage, not analytic coverage for all curves or independent shaping. The emoji
reference is separately decoded from the font's CBDT PNG. Numerical sampler
agreement is not product visual qualification.

The decision domain is **six monochrome rows × four common transforms**, not the
whole seven-row board. Its MAE is over the identical registered **65 × 49 = 3185**
pixels, with the refined/compact image cropped at y=8. This is common-crop MAE,
not ink ROI MAE and not the original differently-sized full-tile MAE. Maximum
error uses that same crop. Original six mono rotate90 cases remain unsupported.
New square-rotate and the one bounded perspective are verified independently,
but excluded from common-domain product decisions. Emoji remains bitmap-only.

Costs are the actual format payload W×H×16, including packed header and padding.
They are not VkMemoryRequirements, residency, driver allocation, CPU peak, mobile
power or GPU performance. Compact generation still produces full 4× CPU sources
before cropping. Each compact row/budget creates its own logical device; there
is no simultaneous whole-board memory-peak claim.

`quality_targets: null` returns `NEEDS_QUALITY_TARGET`. Explicit targets are
caller policy, not thresholds chosen from the measured error to claim success.
The policy returns eligible registered candidates or keeps the named baseline.
It does not rank candidates using an invented score. A performance requirement
remains `NEEDS_MEASUREMENT`. Bitmap fallback may worsen quality. No MSDF, mesh,
text family, Android, real-device performance or full-release gate is promoted.

## Fresh execution

```
python checks19/run_text_choice.py \
  --expected-tests-head <40-hex-tests> --expected-skill-head <40-hex-skill> \
  --skill-root <skill-checkout> --tools <official-bin> \
  --include <official-include> --loader <actual-libvulkan.so.1> \
  --icd <lvp-icd.json> --libdir <official-libdir> --layerdir <official-layerdir> \
  --variable-font <RobotoFlex.ttf-with-OFL-and-receipt> \
  --msdf-source <clean-msdfgen-1874bcf-checkout> --output <fresh-directory>
```

The existing pinned font guards and licenses remain mandatory. No font, atlas,
third-party implementation or private absolute path is published in this doc.
Local reports retain paths so the operator can reverify the actual dependencies.
The entry requires exact clean paired source bytes before imports, runs fixed
commands under an owned-process-group supervisor and finite budget, and hashes
sources, tools, headers, providers and artifacts again at completion.

Example policy format (illustrative numbers, **not product qualification**):

```json
{"baseline":"board/bitmap","quality_targets":{"max_common_crop_mae":0.02,"max_common_crop_error":0.2},"per_row_payload_budget":400000,"require_performance":false}
```

Original shader negatives are real legal draw executions with deliberately wrong
composition. HOST mutations of saved observations are separate checker tests,
not injected Vulkan defects. Failed/partial executions are never successful
qualification receipts. Original refined historical before/after fields remain
historical; fresh comparisons are recomputed from the new raw pixel files.

Use repeated `--additional-policy <json>` options to evaluate several declared
policies after the single fresh chain and single raw re-verification. Their
results explicitly share the same observation cohort. This is not a new GPU
execution per policy, nor permission to trust an arbitrary edited receipt.
