# Fixed-font locale-dependent GSUB → Vulkan churn

`VULKAN_TEXT18_LOCALE_CHURN=1 python -m pytest -c tests/pytest.ini tests/test_text18_locale_churn_lab.py`
uses an existing local DejaVuSerif-Italic.ttf. No download/font redistribution.
Before any font parse the runner requires346544 bytes and SHA256
`d843bf414381dd64b89e6c7c954075657b74168521f02b30e11d308558eda1d2`.
The test is explicitly `vulkan_integration`; static collection does not import
FreeType or require this font.

The exact font's GSUB was independently inspected offline using available
fontTools (not a runtime test dependency). In script `cyrl`, language `SRB `
(and separately `MKD `) selects `locl` lookup1, type1 SingleSubst:

| Source | Destination | Default ID | Localized ID |
|---|---|---:|---:|
|uni0431|uniF6C5|924|3294|
|uni0433|uniF6C4|926|3293|
|uni0434|uniF6C6|927|3295|
|uni043F|uniF6C7|938|3296|
|uni0442|uniF6C8|941|3297|

Actual HarfBuzz glyph IDs are asserted against these fixed-font mappings, not
merely assumed from a language parameter. Same text `бгдпт`, ltr, pixel size16,
integer destination(3,5), font and all other options stay fixed. Only language
alternates ru/sr across seven inputs. Both repeated atlas groups must be stable
and mutually different; missing glyphs or raster clipping are rejected. Actual
receipts retain the provider version, font hash, glyph IDs/positions and language.
No claim about general linguistic correctness, other fonts/locales, paragraph
bidi, language fallback or platform typography follows from this fixture.

The unchanged content-churn C++ flow runs all six transitions in one Vulkan
device/queue: actual pending old draw, canceled candidate upload, retained old
route draw, new page publish/draw, generation rollback rejection and completed
retirement. 18 color readbacks use independent original raster pixels/destination
CPU references. Peak live atlas pages2, end-of-round1 page and0 submission objects.
Counts are fixture ownership, not driver allocation/leak proof. Outer pytest
rejects stale readback substitution and forged publication events on copies.

Trusted run bitmaps are cropped/packed and sampled by real vertex UV quads.
This is not per-glyph geometry, general text layout, MSDF, mobile, DirectWrite or
Live acceptance. Nearest1:1 sampling only. ALL_COMMANDS gates block queued work,
not proof of active shader execution or parallel queues. Existing UNUSED/preserve
non-target attachments are not active MRT/depth integration. Full allocation or
device-loss failure cleanup remains outside scope. Preparation runs are separate
from the actual six-transition evidence; raw logs/provenance stay local.
