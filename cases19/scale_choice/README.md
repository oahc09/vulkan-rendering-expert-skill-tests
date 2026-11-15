# Scale: visible-set generation and indirect count, not a speed ranking

```sh
python cases19/scale_choice/run.py --tools /path/to/bin --include /path/to/include \
 --loader /path/to/libvulkan.so.1 --icd /path/to/lvp_icd.json \
 --libdir /path/to/libraries --layerdir /path/to/explicit_layer.d \
 --spec-root /path/to/frozen/Vulkan-Docs --output /fresh/output
```

Fixed16 candidate cells have7 visible entries. CPU direct recording uses the same
mask as a single compute invocation that stably compacts draw commands and writes
count7. Actual `vkCmdDrawIndirectCount` consumes the generated buffer/count, after
COMPUTE_SHADER/SHADER_WRITE → DRAW_INDIRECT/INDIRECT_COMMAND_READ. FirstVertex
selects a tile, firstInstance is0; no DrawID/nonzero-firstInstance requirement.
The compute path is deliberately serial, not a parallel-culling speed benchmark.

Six real runs: direct → compact-count → direct recovery; wrong pixel expectation
on each path; then legal maxDrawCount6 truncation. The last case must omit a visible
tile, fail the full quality oracle and exit6 without a Validation error. It is not
an API defect. Both wrong expectations preserve invisible magenta cells and swap
visible red/blue. Complete68 uint command/count/guard readback and all16 pixels
are checked independently; stable command order must match the input scan.

All buffers use actual compatible coherent CPU-device memory. Commands/count share
one272-byte allocation; count at256,16-byte command stride,16-command capacity.
Coherent input writes precede submission; output/argument host reads follow explicit
dependencies and fence completion. No pending resource reset, unsafe count or OOB
negative is executed. Actual feature query and enable are distinct. MultiDrawIndirect
is conservatively queried/enabled here, not asserted a universal Count prerequisite.
The compared paths both allocate their compute/resources during setup, even if the
CPU path never dispatches. Object counts are not an optimized memory comparison.

Default keeps the correctness reference. `--max-recorded-draws 1` returns
NEEDS_COMPARABLE_BASELINE, **not** selection of GPU as the only feasible option:
CPU instancing/prebatched multidraw was not compared. `--require-performance`
returns NEEDS_MEASUREMENT. Calls/16cells do not prove throughput or full-frame speed.

Fixed raw368 sources and commonvalidity file are hashed; conditional includes are
not expanded. VVL309 runtime identity is separately recorded. Reused render safety
gates check attachment/dependency/retirement after the new6-vertex geometry,
actualcount/commands and actualfullpixel oracle have already been checked. Their
internal projection does not relabel source records or claim three vertices were
used. No physical GPU, mobile, mesh/DGC, arbitrary scene or full C2 acceptance.
