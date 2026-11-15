# Fixed Roboto Flex axes → real Vulkan churn

Opt in: `VULKAN_TEXT18_VARIATION_CHURN=1`; set `TEXT18_VARIABLE_FONT` to
an execution-side RobotoFlex.ttf. No font is included, installed, downloaded by
the runner, or redistributed. Tests are marked `vulkan_integration`, import no
font provider during collection, and do not require FreeType/fonts in static CI.

Trusted source: Google Fonts organization upstream `googlefonts/roboto-flex`,
commit `04263028f0fe6dbb0cac9df9fc69e3dd69668b26`, `fonts/RobotoFlex[GRAD,XOPQ,XTRA,YOPQ,YTAS,YTDE,YTFI,YTLC,YTUC,opsz,slnt,wdth,wght].ttf`.
1,775,480 bytes; Git blob SHA1 `0abe2ee29292f1b39f59103d069feda87cde585e`;
runtime SHA256 guard `94a7ea95ccee28c54885a507e3cc0a534ce41ec61d413935df0e07261a7ffe63`.
License is SIL OFL1.1. This is not a Google certification/support claim.
Local download/length/Git-object hash checks and license receipt precede use.

The independent adapter preserves the old system-provider bridge unchanged.
It supplies all13 default+override design coordinates both to HarfBuzz
`hb_font_set_variations(font,const hb_variation_t*,unsigned)` and FreeType
`set_var_design_coords`, then compares provider design-coordinate readbacks.
Unknown, nonfinite, out-of-range, boolean, or nonexact shared float32/16.16
coordinates are rejected instead of silently clamped/quantized. Optical size is
explicit default14, not implicitly derived from pixel size20. A deliberate
HB900/FT100 mismatch is rejected before rasterization. API basis:
https://harfbuzz.github.io/harfbuzz-hb-font.html#hb-font-set-variations
https://harfbuzz.github.io/harfbuzz-hb-font.html#hb-font-get-var-coords-design
FreeType wrapper uses FT_Set/Get_Var_Design_Coordinates with16.16 values.

Latin Ofi is shaped/rasterized in seven finite configurations: wght100/400/900,
wdth75/125, wght700+wdth75, wght200+wdth125. All seven actual coverage atlas hashes
must differ; glyph IDs/advances, axes, font/provider hashes remain in local receipts.
Different metadata alone cannot pass the content check. The matched HB/FT axes
are used for actual glyph selection, positioning, and coverage generation.

The unchanged content-churn C++ executable performs six transitions in one
VkDevice/queue, with18 actual UV quad draws and13 uploads. Old draw pending,
candidate upload/cancel, retained-route draw, new publication/draw, rollback
rejection and retirement all execute as in `text_content_churn_lab`. Every round
ends with1 page object and0 submission resources. Original raster pixels and
independent destination coordinates predict GPU color, not the GPU vertex buffer.
The runner checks invalid axes, wrong font, and provider mismatch. The outer
pytest separately checks stale image and forged-event copies; the runner summary
does not claim those outer checks have executed. No illegal GPU resource lifetime is deliberately executed.

Scope: trusted single font/Latin run bitmap quad, fixed nearest1:1, six bounded
axis transitions, software Vulkan. No all-axis/font typography certification,
MSDF, Android/Windows, GPU performance or Live-model acceptance. ALL_COMMANDS
pending gate does not mean shader execution; candidate uploads queue behind it.
Fixture counts are not driver leak proof; allocation/device-loss cleanup remains
limited. Preparation's separate prior fixtures are not this run's evidence.
