# TEXT18 bounded MSDF experiment

This is an opt-in Linux experiment, not a new runtime dependency or typography
certification. It uses a caller-supplied trusted DejaVuSans font (SHA-256
`57f73e11f51999432bf7ab22ce55b6f945d5eca1bf824404cfa9ec2e3718c84e`) and a clean local
checkout of official msdfgen v1.13 commit
`1874bcf7d9624ccc85b4bc9a85d78116f690f35b`. Neither fonts nor third-party source
are included here. Keep the upstream `LICENSE.txt`; its hash is recorded locally.

Source interface: [msdfgen v1.13](https://github.com/Chlumsky/msdfgen/tree/1874bcf7d9624ccc85b4bc9a85d78116f690f35b).
The adapter compiles only `core/*.cpp`, not the extension/font/SVG loaders.

## Actual chain

1. Existing Linux HarfBuzz provider chooses the shaped glyph ID for `A` and `O`.
2. FreeType loads that glyph from the same hashed face, unscaled and unhinted;
   move/line/quadratic/cubic outline callbacks retain contours and holes.
3. The authored adapter validates bounded contours, calls `normalize`,
   `orientContours`, `edgeColoringSimple(angle=3, seed=0)`, and `generateMSDF`.
   These are independently computed edge-colored RGB distances, NOT a single
   distance copied into three channels. `A` must have differing channels.
4. RGB is explicitly clamped to [0,1] before transport in a linear RGBA32F
   texture. A is constant 1 and is not MTSDF's true-distance channel.
   Format linear-filter capability is queried before use.
5. A real Vulkan shader samples LINEAR, reconstructs median RGB with derivative
   screen range, and applies premultiplied-over. Non-target velocity/ID attachments
   must retain their sentinels.
6. CPU bilinear+median reconstruction independently checks GPU sampling/blending.
   A second reference subdivides the original Beziers (64 steps) and computes
   even-odd scanline coverage at 16×16 subpixel samples. This reference never reads
   MSDF texture values and is only an approximation to continuous outline coverage.

## Pre-registered bounded conditions

Atlas/output 65×49; glyph control-point bounds fitted to 24-pixel height and
centered; distance range 4 atlas pixels; scales .75, 1, 1.5; additional .25-pixel
horizontal phase at unit scale. No packing, mipmaps, anisotropic filtering,
perspective or arbitrary fonts are claimed. Centered fixtures have blank atlas
margin greater than half-range plus linear footprint; transformed outlines must
remain inside the framebuffer. These conditions are not general padding advice.

Fixed before the first measurement:

- maximum linear RGBA sampling/composition error: 0.0002;
- coverage MAE on union of foreground/reference ROI: 0.04;
- coverage MAE on fractional edge ROI: 0.16;
- maximum absolute coverage difference: 0.45;
- untouched MRT sentinels: exact;
- wrong single-channel shader, sRGB reinterpretation and wrong range: reject.

The outline thresholds account for a bounded distance-coverage reconstruction,
not pixel identity with a platform's hinted rasterizer. They cannot establish
optimal small-font quality or the user's entire visual acceptance plan. A failure
must remain a failure; do not loosen thresholds after inspecting output.
`preregistered.json` is written before any build or native font parsing. Failed
runs are retained in their separate output directories. View the actual preview
and outline reference before making even a scoped visual statement.

## Run

```sh
python tests/fixtures/text_msdf_lab/run_lab.py \
  --out /absolute/new-output \
  --font /absolute/approved-DejaVuSans.ttf \
  --msdf-source /absolute/pinned-msdfgen-checkout
```

Uses existing `CXX`, `GLSLANG`, `SPIRV_VAL`, `VULKAN_SDK_PREFIX` and Vulkan ICD/layer
environment. It does not download or install anything. Native commands have a
180-second timeout; the input font is hash-approved, not an arbitrary untrusted
font parser security test. Public reports should not redistribute the font or
third-party checkout. Local receipts contain source, font, binaries and metrics.

## Initial local engineering runs

The first attempt stopped at an exact source-adapter replacement-count guard
(expected three R32 tokens, actually two). The second stopped because an inherited
base-harness compute shader was absent from the variant folder. Both failed run
directories were retained; neither was a quality-gate failure and no numerical
threshold was changed. The third executed all eight positive draws and three
negative draws. In that bounded software-Vulkan run, A had a maximum local
coverage difference of approximately 0.3997. This large local difference is
explicitly not pixel consistency or complete text-quality acceptance. The fixed,
permissive coverage thresholds establish only this limited experimental path.

MRT sentinel evidence here exercises the UNUSED/preserve overlay fallback, not
active MRT writes or per-attachment independent blending.
