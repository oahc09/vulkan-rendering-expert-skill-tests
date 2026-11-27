# Scoped official Reference preload path repair experiment

The fixed Vulkan-Docs `config/katex_replace/extension.rb` lines24–32 hard-code
nine `../katex/fonts/` preload hrefs. Reference pages live in `gen/out/man/html`,
so these point to missing `gen/out/man/katex/fonts` files, while the real files
are at `gen/out/katex/fonts`. The same extension already uses its `katexpath`
attribute for the stylesheet. This is a source/configuration defect, not a link
checker treating an anchor in another page as a valid current-page target.

`checks19/probe_reference_fonts19.py` operates only on an isolated copy of the
fixed P4 v2 all-Vulkan cohort. It adds one line before stylesheet generation:

```ruby
katexScript.gsub!('../katex/fonts/', katexpath + '/fonts/')
```

It actually rerenders one Reference page and the full all-configuration spec,
then restores the original extension and rerenders the Reference page again.
The patched Reference must differ only in nine hrefs, all nine actual font files
must exist at those URLs, the spec HTML must remain byte-identical, and the
reverted Reference must reproduce the exact original bytes and missing targets.
The final copied input tree and original input tree must match their preimages.
Original snapshots, P5 full-build outputs and P6 broken-link findings are not
modified. Source copyright/license notices remain in the isolated tree.

The first probe retained only dynamic assertions/hashes of intermediate HTML,
so it does not support later raw intermediate-byte review. The second probe
retains baseline/patched/reverted HTML and source preimage/postimage as separate
artifacts; it is the stronger evidence used for independent review. Executable
and Python dependency identities are recorded. This is not an exhaustive dynamic
loading audit, browser/network/font-appearance test, or all3553-page patched
rebuild. Missing fragments, two rule-page links and upstream placeholders are not
fixed by this experiment. No upstream repository was modified or PR submitted.
