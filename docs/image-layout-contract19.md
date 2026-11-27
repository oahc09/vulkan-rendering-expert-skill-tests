# Image-layout HOST contract (bounded)

Run in a fresh output directory:

```sh
python checks19/run_image_layout_contracts.py \
  --synchronization /path/to/frozen368/chapters/synchronization.adoc \
  --validusage /path/to/frozen309/validusage.json --out /fresh/output
```

The command verifies exact source bytes, retains raw source slice hashes and
conditional directives, and runs 17 fixed positive/negative HOST controls.
Implementation hashes and exact 309 VUID owner/condition/page coordinates are
recorded. Source368 and validusage309 remain distinct. Raw slices do not expand
includes, evaluate outer conditionals, or establish full normative closure.

## Contract

Ordinary 2D COLOR subresources are explicit `(mip, layer)` cells. Current layout
and `defined` are caller-established inputs, not Vulkan device queries. Only
selected cells change in the modeled result. Formats, usage, masks and API
validity require independent proof. Ownership transfers, external or aliased
memory, 3D slice rules and depth/stencil aspects are outside this model.

- Barrier2, or legacy barriers with synchronization2 enabled: if queue-family
  indices are equal **and** old/new layouts equal, layout values are ignored.
  Actual layouts and definedness are preserved even if the supplied equal values
  differ from the current layout or are UNDEFINED. This alone proves no memory
  dependency; the caller must still establish relevant dependencies.
- Legacy without synchronization2 does not use that exception. Old layout must
  match every selected cell, or be UNDEFINED; transition new layout cannot be
  UNDEFINED/PREINITIALIZED in this bounded branch.
- UNDEFINED permits discard, but does not eliminate prior/next access ordering,
  availability or visibility requirements. `defined=False` means contents may
  no longer be relied upon. It does not predict a clear, zero data or an actual
  physical modification. A preserving transition never turns undefined input
  into defined output.

UNKNOWN or insufficient dependency produces no modeled updated state. Results
are caller-fact semantic checks, **not GPU execution, universal barrier
validation, full L1/L2 coverage or release acceptance**. No arbitrary stage/access
combination is automatically declared correct.
