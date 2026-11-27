# Independent source audit of 66 empty reference sections

This is a read-only classification of the exact P5 rendered cohort, not a new render, a general exemption, or a semantic-completeness certificate. The accompanying JSON binds each item to its generated source file and section line span, SHA-256 and text; original fixed Vulkan-Docs source contexts are compared byte-for-byte with Git commit `fa30d4e312e843193601be7cb926c7e25d9ec885`.

## Findings

- **47 Description sections:** the section contains only a generated validity include. All 47 included files were individually read and contain only comments. API declarations and member prose elsewhere on these pages are separate evidence. The absence of generated validity text does not prove that every normative constraint has been captured.
- **3 Description sections:** `VkDeviceMemory`, `VkShaderModule`, and `VkStructureType` contain body text entirely guarded by `VKSC_VERSION_1_0`. The heading remains while the body is filtered in this fixed Vulkan configuration. This does not validate Vulkan SC.
- **12 Members sections:** the original upstream blocks explicitly say that specification language is not written and that the text is a placeholder to avoid dead links. These are **known upstream documentation gaps**, not semantically complete pages. Their exact entity names and original source spans remain in the JSON.
- **4 Members sections:** member bullets are present elsewhere on the same generated page. `VkAllocationCallbacks`, `VkPhysicalDeviceVertexAttributeDivisorPropertiesEXT`, and `VkSurfaceCapabilitiesKHR` place them in Description; `VkDeviceFaultDebugInfoKHR` places them before the API include in C Specification. This is section-partition behavior, distinct from missing prose.

## Extraction mechanism and bounds

The fixed `scripts/reflib.py` lines 317–345 infer member and description paragraph boundaries, while `scripts/genRef.py` lines 557–590 slice `include`, `param`, and `body` ranges into C Specification, Members, and Description. The JSON retains exact script bytes/spans. Conditions/comments between the API include and member bullets can therefore produce an empty Members section while retaining bullets in Description. The debugging structure places its bullets before its API include, so the extracted C Specification contains them.

No source, generator, or HTML was edited. This inventory explains the observed emptiness of these 66 fixed sections only. It does not establish full prose correctness, all constraints, all conditional configurations, visual quality, or cross-page-link closure. Do not convert the classification into a blanket allowance for new empty sections. A changed source, section span, generated include, or rendered cohort needs a new review.

## Upstream excerpt attribution

Evidence JSON contains unchanged excerpts from the fixed [Khronos Vulkan-Docs source](https://github.com/KhronosGroup/Vulkan-Docs/tree/fa30d4e312e843193601be7cb926c7e25d9ec885). Classification, selection and line-span metadata are additions; upstream text was not rewritten. Original per-file notices follow. Documentation is licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); script excerpts retain their stated license. See the [upstream license directory](https://github.com/KhronosGroup/Vulkan-Docs/tree/fa30d4e312e843193601be7cb926c7e25d9ec885/LICENSES) for applicable terms.

### `appendices/VK_NVX_binary_import.adoc`

```text
// Copyright (c) 2018-2021 NVIDIA Corporation
// SPDX-License-Identifier: CC-BY-4.0
```

### `appendices/VK_SEC_amigo_profiling.adoc`

```text
// Copyright 2020-2026 The Khronos Group Inc.
// SPDX-License-Identifier: CC-BY-4.0
```

### `appendices/VK_SEC_pipeline_cache_incremental_mode.adoc`

```text
// Copyright 2020-2026 The Khronos Group Inc.
// SPDX-License-Identifier: CC-BY-4.0
```

### `appendices/VK_SEC_throttle_hint.adoc`

```text
// Copyright 2026 The Khronos Group Inc.
// SPDX-License-Identifier: CC-BY-4.0
```

### `appendices/VK_VALVE_descriptor_set_host_mapping.adoc`

```text
// Copyright 2020-2026 The Khronos Group Inc.
// SPDX-License-Identifier: CC-BY-4.0
```

### `chapters/VK_ARM_data_graph/graphs.adoc`

```text
// Copyright 2022-2025 Arm Ltd.
// SPDX-License-Identifier: CC-BY-4.0
```

### `chapters/VK_KHR_surface/wsi.adoc`

```text
// Copyright 2014-2026 The Khronos Group Inc.
// Copyright (c) 2021 BlackBerry Limited.
// Copyright (c) 2018-2020 The Brenwill Workshop Ltd.
// Copyright (c) 2018-2020 Google LLC
// Copyright (c) 2025 Huawei Technologies Co. Ltd.
// Copyright (c) 2018-2020 Nintendo
// Copyright (c) 2018-2022 NVIDIA Corporation.
// SPDX-License-Identifier: CC-BY-4.0
```

### `chapters/accelstructures.adoc`

```text
// Copyright 2020-2026 The Khronos Group Inc.
// Copyright (c) 2019-2025 NVIDIA Corporation
// SPDX-License-Identifier: CC-BY-4.0
```

### `chapters/capabilities.adoc`

```text
// Copyright 2014-2026 The Khronos Group Inc.
// Copyright (c) 2014-2020 NVIDIA Corporation
// SPDX-License-Identifier: CC-BY-4.0
```

### `chapters/debugging.adoc`

```text
// Copyright 2014-2026 The Khronos Group Inc.
// Copyright (c) 2018-2020 NVIDIA Corporation
// SPDX-License-Identifier: CC-BY-4.0
```

### `chapters/descriptorheaps.adoc`

```text
// Copyright 2024-2026 The Khronos Group Inc.
// SPDX-License-Identifier: CC-BY-4.0
```

### `chapters/device_generated_commands/generatedcommands.adoc`

```text
// Copyright (c) 2019-2020 NVIDIA Corporation
// Copyright (c) 2024 VALVE Corporation
// SPDX-License-Identifier: CC-BY-4.0
```

### `chapters/devsandqueues.adoc`

```text
// Copyright 2015-2026 The Khronos Group Inc.
// Copyright (c) 2018-2020 NVIDIA Corporation
// SPDX-License-Identifier: CC-BY-4.0
```

### `chapters/executiongraphs.adoc`

```text
// Copyright 2023-2026 The Khronos Group Inc.
// SPDX-License-Identifier: CC-BY-4.0
```

### `chapters/extensions.adoc`

```text
// Copyright 2015-2026 The Khronos Group Inc.
// SPDX-License-Identifier: CC-BY-4.0
```

### `chapters/formats.adoc`

```text
// Copyright 2015-2026 The Khronos Group Inc.
// SPDX-License-Identifier: CC-BY-4.0
```

### `chapters/fundamentals.adoc`

```text
// Copyright 2015-2026 The Khronos Group Inc.
// SPDX-License-Identifier: CC-BY-4.0
```

### `chapters/limits.adoc`

```text
// Copyright 2015-2026 The Khronos Group Inc.
// SPDX-License-Identifier: CC-BY-4.0
```

### `chapters/memory.adoc`

```text
// Copyright 2015-2026 The Khronos Group Inc.
// Copyright (c) 2021-2022 The Brenwill Workshop Ltd.
// Copyright (c) 2021 Google Inc.
// Copyright (c) 2018-2020 NVIDIA Corporation
// Copyright 2023 QNX Software Systems
// SPDX-License-Identifier: CC-BY-4.0
```

### `chapters/pipelines.adoc`

```text
// Copyright 2015-2026 The Khronos Group Inc.
// SPDX-License-Identifier: CC-BY-4.0
```

### `chapters/queries.adoc`

```text
// Copyright 2015-2026 The Khronos Group Inc.
// Copyright (c) 2018-2020 Intel Corporation
// SPDX-License-Identifier: CC-BY-4.0
```

### `chapters/renderpass.adoc`

```text
// Copyright 2015-2026 The Khronos Group Inc.
// SPDX-License-Identifier: CC-BY-4.0
```

### `chapters/resources.adoc`

```text
// Copyright 2015-2026 The Khronos Group Inc.
// Copyright (c) 2020-2025 Huawei Technologies Co. Ltd.
// SPDX-License-Identifier: CC-BY-4.0
```

### `chapters/shaders.adoc`

```text
// Copyright 2015-2026 The Khronos Group Inc.
// Copyright (c) 2020-2021 NVIDIA Corporation
// SPDX-License-Identifier: CC-BY-4.0
```

### `chapters/sparsemem.adoc`

```text
// Copyright 2015-2026 The Khronos Group Inc.
// SPDX-License-Identifier: CC-BY-4.0
```

### `chapters/vertexpostproc.adoc`

```text
// Copyright 2015-2026 The Khronos Group Inc.
// Copyright (c) 2018-2020 NVIDIA Corporation
// SPDX-License-Identifier: CC-BY-4.0
```

### `chapters/video/av1_encode.adoc`

```text
// Copyright 2023-2026 The Khronos Group Inc.
// SPDX-License-Identifier: CC-BY-4.0
```

### `chapters/video/h264_encode.adoc`

```text
// Copyright 2018-2026 The Khronos Group Inc.
// SPDX-License-Identifier: CC-BY-4.0
```

### `chapters/video/h265_encode.adoc`

```text
// Copyright 2018-2026 The Khronos Group Inc.
// SPDX-License-Identifier: CC-BY-4.0
```

### `scripts/genRef.py`

```text
# Copyright 2016-2026 The Khronos Group Inc.
# SPDX-License-Identifier: Apache-2.0
```

### `scripts/reflib.py`

```text
# Copyright 2016-2026 The Khronos Group Inc.
# SPDX-License-Identifier: Apache-2.0
```
