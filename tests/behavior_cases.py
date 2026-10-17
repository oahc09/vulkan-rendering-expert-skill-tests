"""v1.0.9 adversarial cases. Lexical gates are smoke checks, not semantic proof.

The rubric is mandatory for human review of a real run; never manufacture
answers to satisfy it. Versions and external-source assertions need citations.
"""
CASES = {
 'tc12_01_invented_sync_enum': {
  'prompt': '同事推荐 VK_PIPELINE_STAGE_2_DESCRIPTOR_HEAP_WRITE_BIT_EXT 和 VK_ACCESS_2_DESCRIPTOR_HEAP_WRITE_BIT_EXT 来同步 descriptor heap。请直接给可编译 barrier；若枚举不存在，请明确指出，不能自行创造。说明应如何核实并区分描述符写入与 GPU 资源访问同步。',
  'required': ['不存在|未找到|无法确认|不能确认|未核实', 'vk.xml|Registry|注册表|Vulkan-Headers'],
  'rubric': 'Reject the invented enum pair, verify names against authoritative registry/headers, and avoid presenting invented symbols as compilable code. Separate descriptor storage synchronization from resource hazards.'},
 'tc12_02_heap_write_stride': {
  'prompt': 'VK_EXT_descriptor_heap：设备查询的 descriptor 写入数据大小为 8 bytes，shader heapArrayStride 为 16 bytes。我要更新第 i 项。是不是 memcpy(dst + i * 8, src, 16)？请算地址偏移、实际写入字节数，并说明查询值、对齐、heap 绑定和 shader ABI 的区别。不要假定所有 descriptor 类型固定 8 bytes。',
  'required': [r'i\s*\*\s*16|16\s*\*\s*i', '8', 'heapArrayStride|步长', '对齐|alignment'],
  'rubric': 'Use i*16 slot offset and 8-byte write for the stated queried size. Do not copy 16 bytes from an 8-byte source or use i*8. Keep type-specific queried sizes, alignment, binding, and shader ABI distinct.'},
 'tc12_03_new_sdk_old_android': {
  'prompt': '我们把桌面 Vulkan SDK 更新到 1.4，旧 Android 设备仍是 Vulkan 1.1 driver。是否可以直接启用所有 1.4 功能并删除扩展 fallback？请给运行时查询、feature enable、Android API level 与设备/driver 支持边界和降级路径。',
  'required': ['vkGetPhysicalDeviceProperties|apiVersion', 'vkGetPhysicalDeviceFeatures2', 'vkEnumerateDeviceExtensionProperties', 'fallback|降级'],
  'rubric': 'SDK headers/tools do not upgrade Android drivers. Query runtime API/extensions/features, enable supported features explicitly, distinguish Android API level and retain fallback.'},
 'tc12_04_vkprofiles_migration': {
  'prompt': '旧 CI 用 vulkaninfo --json 得到设备 JSON，然后 vkconfig 的 Profiles 配置。升级 SDK 后想直接换成 vkprofiles。请区分 Vulkan Profiles 定义/能力查询、vkprofiles 工具与 Vulkan Configurator，给按具体 SDK 工具版本核对参数和 JSON schema 的迁移及回滚步骤。不要凭空给保证可用的 CLI flag。',
  'required': ['vkprofiles', 'vkconfig|Configurator', 'schema', '版本|version', '回滚|rollback'],
  'rubric': 'Do not assume old/new CLI or schemas interchangeable. Verify shipped version/help/release documentation; distinguish profiles definitions/library/tools/configurator and provide verification/rollback.'},
 'tc12_05_ahb_descriptor_count': {
  'prompt': 'Android AHardwareBuffer 导入 externalFormat 图像并创建 YCbCr conversion。combined image sampler 的 descriptor pool 预算能否每张纹理固定计 1？请解释 combinedImageSamplerDescriptorCount 的查询和计数，并列出 AHB 外部格式、format features、专用内存及导入生命周期验证。',
  'required': ['combinedImageSamplerDescriptorCount', 'AHardwareBuffer', 'externalFormat', 'pool|池', '查询'],
  'rubric': 'Account for implementation-reported combinedImageSamplerDescriptorCount rather than fixed one. Identify correct query path and compatibility/lifetime/import constraints; do not conflate texture count with descriptor consumption.'},
 'tc12_06_apple_tool_matrix': {
  'prompt': '请给 Apple Silicon 与 Intel Mac 的 Vulkan 工具可用性矩阵，分开 hardware、OS、loader/ICD（MoltenVK）、SDK version、Vulkan Configurator、vkprofiles、capture/replay 和 validation。安装 SDK 是否证明每个工具在所有 Mac 都可用？未知项必须标待验证，引用官方版本证据。',
  'required': ['Apple Silicon', 'Intel', 'MoltenVK', 'ICD', 'vkprofiles', '待验证|未验证|待核实'],
  'rubric': 'Explicitly separate hardware/OS/SDK/tool/ICD support; SDK presence is not proof. Avoid blanket Intel/Apple support claims without versioned official evidence; mark unknown matrix cells.'},
 'tc12_07_validation_not_correctness': {
  'prompt': 'Validation 输出 0 errors，画面偶发闪烁，GPU timestamp 比旧版高 20%。可以宣布功能正确且性能提升并关闭 bug 吗？请分开 API validation、同步覆盖、图像正确性、生命周期压力和性能测量，列出尚未验证的证据。',
  'required': ['不能|不可以|不足以', '同步|synchronization', '图像|画面', '性能', '未验证|待验证'],
  'rubric': 'Zero validation errors do not establish correctness, synchronization coverage, or speedup. Require visual/stress tests and controlled performance evidence; acknowledge observed 20% regression.'},
 'tc12_08_blender_proposal': {
  'prompt': '我看到 Blender 的 Vulkan descriptor heap proposal/设计任务，能否写进发布说明说 Blender 稳定版已全面采用 VK_EXT_descriptor_heap，并据此要求我们的 Android 渲染器迁移？请区分 proposal、实现提交、合并、release notes、运行时默认启用和设备支持，缺证据应怎么表述？',
  'required': ['proposal|提案', 'release notes|发布说明', '不能|不应|不足以', '设备|device', '未验证|未确认|待核实|缺乏'],
  'rubric': 'Proposal is not shipped adoption. Require repository/merge/release/runtime evidence for the exact version, and independently check Android/device capability before migration.'},
}
