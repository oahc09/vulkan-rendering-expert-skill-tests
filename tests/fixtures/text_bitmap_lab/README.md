# Trusted Linux bitmap run to real Vulkan

Scope: explicit single-run HarfBuzz glyph IDs/positions → FreeType grayscale
rasterization by glyph ID → 65×49 float coverage → actual R32 sampled Vulkan
image → premultiplied RGBA32F blend → readback. O and ffi use LTR English; سلام
uses explicit RTL Arabic. ffi must produce fewer than three glyphs; no .notdef
or clipped samples are allowed. Font file stays local and is never bundled.

Positions use HarfBuzz font units scaled to 20 px and rounded to integer pixels;
FreeType normal hinted bitmap bearings are applied. This is a deliberately
limited bitmap-run placement policy, not platform paragraph layout, fractional
hinting correctness, mixed bidi, fallback or typography-reference validation.
Overlapping glyph coverages use source-over union. The independent scalar
oracle checks composition against prepared float masks, NOT whether FreeType
produced the correct font outline. Do not call these image diffs font quality.

The runner uses pinned freetype-py 2.5.1 (install separately from official PyPI),
system HarfBuzz and caller-supplied trusted local DejaVuSans.ttf. The Python
wheel may bundle FreeType; receipt records actual library hash/version, not an
assumed system version. Only trusted fonts are supported. No sandbox for
untrusted font parsing is implemented. Run via the outer pytest process timeout.

The existing text_vector_lab source is unchanged. Build copies its source into
an output-only header, renames its entry point and resolves the helper include;
the independent executable reuses TextLab.draw. Existing thirteen-frame tests
are not modified or replaced. Same preserved-attachment overlay fallback
applies, not active MRT independentBlend.

```
VULKAN_TEXT18_BITMAP=1 TEXT18_TEST_FONT=/trusted/DejaVuSans.ttf \
  python -m pytest -c tests/pytest.ini tests/test_text18_bitmap_lab.py
python tests/fixtures/text_bitmap_lab/run_lab.py \
  --font /trusted/DejaVuSans.ttf --out /new/output
```

Use the same explicit toolchain/ICD environment as text_vector_lab. Child
commands time out at 120 s; opt-in pytest bounds the entire run at 240 s.
Truncated/NaN/out-of-range masks fail before Vulkan creation. Output directories
must not exist. Modified RGBA and non-target sentinel readbacks fail independent
verification. Every pixel and nonzero-coverage ROI uses predeclared 1e-6 linear
absolute tolerance. RGB PNG is an sRGB preview of raw premultiplied RGB, not a
reference display composite of the alpha channel.

Raw local receipts include exact glyph/cluster positions, font/library/source
hashes, logs, coverage and readbacks. Publish only minimal numerical findings,
never font binaries or environment logs. Software Vulkan success is not Android,
Windows, MSDF/MTSDF, arbitrary vector, mobile GPU or performance acceptance.

## Bounded vector-mask fallback extension

Five additional frames use CPU-generated bounded masks from closed M/L/Q/C/Z
paths: evenodd ring, opposite-winding nonzero ring, Q and C curves, and reflected
ring. Integer rings have independent area/hole/stroke assertions. Curve
flattening has separate CPU dense-reference tests. Here the Vulkan oracle only
validates coverage-mask composition; no GPU tessellation or general vector
geometry acceptance is claimed. Generated masks, not font/environment files,
pass through the same upload/sample/readback path.
