# P5: complete registered Reference HTML batch and aliases

This Linux/POSIX route executes the official fixed Vulkan-Docs `manhtmlpages` target, rather than extrapolating from selected rendered pages. It uses the independently retained P4 all-Vulkan 1.4.368 input cohort from Docs commit `fa30d4e312e843193601be7cb926c7e25d9ec885`.

## Scope and inputs

The input source/generated tree is fixed to SHA-256 `39681837283249fea7741fa5b0c2b9fd3bf77082e169f850a5823f9770f0a6fa`, with `gen/apimap.py` SHA-256 `81a4aad9ed84dfd776b0f8a4875cb77d41512efd69e9536d713a1aaf3d70b1ab`. These identify the local P4 v2 baseline cohort, not arbitrary caller source or arbitrary rebuilt output. The original source and P4 evidence remain read-only. A fresh copy is made and **its entire HTML reference output directory is removed before execution**, including the two pages previously rendered in P4.

The official configuration is `makeSpec -spec all -version 1.4`, including 20 core-version and 482 extension attributes. Provisional extensions and platform-specific documentation remain included. This is neither Vulkan SC coverage nor implementation support on those platforms.

The expected matrix is derived from the fixed literal API map and all 3553 reference-source files. It includes the real `provisional-headers` page. Of 487 API aliases, the official script excludes 10 `_EXTENSION_NAME` / `_SPEC_VERSION` metadata aliases. The remaining 477 targets are direct entities in this cohort, with no alias chains, entity-name collisions, or case-fold collisions. These are observed fixed-cohort properties, not universal alias rules.

## Execution and verification

```sh
/tmp/vulkan118-py/bin/python checks19/render_reference_batch19.py \
  --source-root /path/to/retained/P4-v2/baseline \
  --runtime-root /path/to/verified/private/Debian/runtime/root \
  --output /path/to/fresh/output
```

The route uses the same private signed Debian Ruby/Asciidoctor/Rouge runtime and existing fixed Node executable as P4. `manhtmlpages -j4` uses four Make jobs, with the official per-page mathematics postprocessor and alias-generation target. No caller command or arbitrary patch is accepted. The execution budget is 30 minutes with owned process-group cleanup and an optional `--cancel-file`. It is a build budget, not a GPU performance measurement.

Each expected entity must be a regular, nonempty, UTF-8 HTML file with complete HTML/head/body/title structure and its exact registered page title. The output inventory must contain exactly 3553 entity files and 477 aliases. Each alias must be a symlink whose literal relative target is exactly the official target filename; resolving to equivalent bytes through a different link is insufficient. Targets must remain direct regular entity files inside the output directory.

The official alias script can warn and still exit zero. Two real HOST controls therefore run it against separate outputs:

1. Remove an entity target while leaving no old broken alias. The script warns and returns zero; strict inventory verification rejects the missing target/alias.
2. Pre-create an alias as a readable ordinary file. The script warns and skips it with exit zero; strict verification rejects its file type.

Control entity files are hard links to read-only baseline output, solely to avoid copying the full HTML batch twice. Controls unlink directory entries or add their own alias file; they never write through an entity link or alter the successful output.

## What this establishes, and what it does not

The result binds actual build commands, logs, source and runtime identity, every rendered page hash, and exact alias targets. It establishes complete rendering/inventory for this fixed registered reference set only. It does not establish semantic correctness of every paragraph, full internal cross-page hyperlink validity, all build configurations, alternate runtime portability, GPU execution, or complete normative L1/L2 review. Whole-runtime dynamic loading is not exhaustively observed; explicit runtime, relevant actual module paths, and main ELF dependencies are bounded evidence.

Small-batch timing is used only to estimate resource needs. There is one full batch execution in this milestone, not two independent full rebuilds. Prepublication build evidence must retain its actual source hashes/head and must not be relabeled as a later published-head execution without a real rerun.

## Source-derived body gate and build / audit separation

After the original full batch, independent review tightened the output verifier without rebuilding the HTML. The new verifier checks the actual `Name` paragraph against each fixed source page's Name text and requires every second-level section present in that source page. The fixed source has one registered `{YCbCr}` Name substitution; other Name macro tokens remain as emitted by the official manpage renderer. This is source/content presence, not a generic AsciiDoc evaluator or visual-quality proof. For example, the upstream Name of `VK_NO_STDDEF_H` preserves literal `<stddef.h>` markup: preserving its raw generated representation does not certify correct browser text display.

The original build receipt retains its original implementation hashes. A separate enhanced-verifier receipt binds the unchanged build receipt/output and the strengthened current verifier. This does not pretend that the full build was rerun with the later verifier. A real rendered-page HOST mutation removes the body while preserving its title, HTML closure and padded size; it must be rejected. Full-page semantic correctness and all internal hyperlinks remain unverified.

The bounded body gate additionally requires all 2929 applicable **C Specification** sections to contain a C-code region with the exact registered entity identifier. Removing that body while retaining Name, title, every heading and file padding is rejected. This checks identifier presence, not the full declaration text, member correctness, or a full-text semantic comparison.

One source heading is explicitly excluded, not silently ignored: `VkPipelineCacheCreateInfo`'s Description lies inside `ifdef::VKSC_VERSION_1_0[]`, source lines 47–75 of its fixed generated reference source (span SHA-256 `a6fd8bb41db915545e33f8d55c85e212d6acde770fd854de213c9a6931725646`). This is Vulkan, not SC. The validator requires that exact source/context before applying the exclusion. Other missing required headings are rejected.

The actual output also contains 66 empty **other** sections (Members/Description templates or conditionally empty content). Their full entity/section list is retained in the enhanced receipt. Reasons have not all received individual semantic review. These are not manufactured nonempty bodies, and their existence prevents a claim that every section's substantive content has been validated.

To verify the unchanged full-build artifact with the later body gate without rerunning the build:

```sh
/tmp/vulkan118-py/bin/python checks19/verify_reference_batch19.py \
  --build-output /path/to/original/full-build \
  --expected-report-sha TRUSTED_ORIGINAL_BUILD_REPORT_SHA256 \
  --source-root /path/to/retained/P4-v2/baseline \
  --output /path/to/fresh/recheck
```

The expected digest is a caller-selected integrity anchor, not cryptographic authorship or authenticated truth. The recheck preserves the original build implementation hashes separately from the new verifier's hashes and does not rerun the old runtime commands.

No separate complete source snapshot of the original full-build CLI/helper was
retained. Its report records execution-time before/after implementation digests,
commands, logs and output bytes, and independent review read that implementation
while it existed. The current files are the later enhanced verifier version.
Do not claim that the original implementation was subsequently byte-verified
against a retained source snapshot, or reconstruct a snapshot and label it as
original. The official pinned upstream sources and generated HTML remain retained.
