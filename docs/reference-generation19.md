# Fixed Reference / validusage generation (P4, development)

This route runs the official Vulkan-Docs `fa30d4e312e843193601be7cb926c7e25d9ec885` build in independent source copies. It does not modify the original Docs/CTS repository, earlier P3 evidence, or the installed system.

## Registered configuration and actual outputs

The configuration is official `makeSpec -spec all -version 1.4`: 20 core-version attributes and 482 registered extension attributes. These include provisional extensions and platform-dependent documentation. Selection is not an implementation-support claim, Windows/Android/etc. runtime test, or Vulkan SC validation. This is separate from P3's no-extension core configuration; no core generated files are supplied to this all build.

The official `generated` and `refpages` targets are executed. The observed reference-source inventory has 3553 `.adoc` files. **Only two reference pages are rendered** using the official individual HTML targets, including their conditional Node mathematics postprocessing when required:

* `VkMemoryDedicatedRequirements`
* `vkBindBufferMemory`

Extracted reference source is not rendered reference HTML. No claim is made that all reference pages render.

The official `validusage` target also renders the full all-configuration HTML for `xrefMap`, and runs Antora preprocessing for `pageMap`. Antora-generated files are new output under the isolated source copy, not edits to original tracked input. Actual 368 output contains 2251 owner groups and 27464 VUID entries. Each entry is associated with its actual rendered HTML anchor and official xref/page maps. Fixed full row identities, text digests, order, and page coordinates are compared against the recorded source cohort. This is a reproducibility and association gate, **not an independent proof of all normative semantics or complete configuration closure**.

## Important upstream failure behavior

* `quiet-include-failure.rb` is used only by validusage, not normal HTML. It may silently omit a missing active include.
* `add_validusage_pages.py` may warn about missing VUID/page associations yet return zero.
* The extractor calls `exit!`, so an `at_exit` marker is not a valid completeness assumption for VU observations. The dedicated observer writes every event immediately and delegates actual processing to `super`.
* The Ruby `json-schema` gem is absent in this cohort. Independent validation uses the existing system Python 3.13 `jsonschema` against the **declared Draft 4** official schema. It is not Ruby validation. The schema uses `const: 3`, which Draft 4 ignores, while the actual extractor emits version 2. The official schema also omits several required/type constraints. Therefore a Draft 4 success is only a weak check; independent strict cohort checks are required. No schema or upstream code is rewritten to obtain success.
* The JSON's legacy `core` bucket is used for extension entries too. It does not mean core-only requirements.

The actual negative overlays remove one active validity include and one xref-map entry in independent copies. The official zero exit is retained; the outer audit must reject the resulting omission. These are controlled HOST build-input mutations, not discovered GPU failures or upstream source fixes.

## Runtime and replay

Use the exact previously verified private Debian Ruby/Asciidoctor/Rouge runtime (32 signed-package cohort), existing Node 24.22.1, and system Python 3.13. The all build additionally needs existing system `lxml`, `pyparsing`, and `jsonschema` dependencies. No download, shell command, URL, or arbitrary patch is accepted by this entry. Paths must be shell-neutral because official Make recipes interpolate paths.

```sh
/tmp/vulkan118-py/bin/python checks19/generate_reference19.py \
  --docs-git /path/to/fixed/Vulkan-Docs \
  --runtime-root /path/to/verified/private/runtime/root \
  --output /path/to/fresh/output
```

`--cancel-file` accepts an external cancellation marker. Owned process-group supervision is reused. Output directories cannot be reused. A failed or cancelled run remains `BLOCKED` with completed step logs and cannot be promoted from exit codes alone. Baseline/observed VU JSON, two rendered reference pages, and extracted reference sources are the deterministic comparison set; whole generated inventories also contain path-dependent diagnostic files and are not silently described as byte-identical.

This is Linux/POSIX and this fixed local runtime cohort, not a portable turnkey binary bundle. Source copyright/license files remain in each exported source tree. Performance, device behavior, full Reference rendering, Vulkan SC, all Asciidoctor configurations, and full normative closure remain outside scope.

## Observed conditions and remaining limits

The dedicated VU observer records 60,886 events: 52,537 conditional-processing events and 8,349 pushed includes, including 477 tag selections. The gate validates the entire path-normalized fixed observation fingerprint, selected source-file bytes, event shapes, and absence of quiet-missing events for the intact run. This is an observed fixed configuration, not a general preprocessor solver. Selected-segment hashes come from the actual unmodified engine invocation; they are not an independently reconstructed tag expansion.

**This P4 run does not perform tag-content or condition-configuration mutation controls.** P3's controls apply only to its own core/no-extension execution and are not counted as P4 evidence. Further configuration/conditional expansion closure remains open.

P4 binds the fixed extracted Ruby runtime, its `RUBYLIB`, main executable/shared-library identities, and observes actual Python dependency module locations. It does **not** record Ruby `$LOADED_FEATURES` for this run or establish a complete dynamic runtime loading closure. It must not inherit that observation from P3. The upstream `exit!` behavior is explicitly accommodated without inventing a termination event.
