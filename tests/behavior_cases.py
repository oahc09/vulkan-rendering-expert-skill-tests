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

# Normalized from the 2026-10-25 directed cases; never injected into model context.
TARGETED_CASES = {'tc13_01_version_features': {'prompt': '设备 apiVersion 要和哪个 1.4 '
                                        '宏比较？scalarBlockLayout、sync2、timelineSemaphore 分别在哪个 '
                                        'feature struct 启用？',
                              'required': ['VK_API_VERSION_1_4',
                                           'Vulkan12Features',
                                           'Vulkan13Features',
                                           '启用'],
                              'rubric': 'Use the numeric API version macro; distinguish support, '
                                        'promotion, query and enablement. scalarBlockLayout and '
                                        'timelineSemaphore belong to Vulkan12Features, '
                                        'synchronization2 to Vulkan13Features, not '
                                        'Vulkan14Features.'},
 'tc13_02_frame_exceptions': {'prompt': '帧开始 wait 后立刻 reset fence，acquire 返回 OUT_OF_DATE 就 '
                                        'return；SUBOPTIMAL 也 return，可以吗？',
                              'required': ['OUT_OF_DATE',
                                           'SUBOPTIMAL',
                                           'submit|提交',
                                           '恢复|recovery',
                                           'fence'],
                              'rubric': 'Explain the unsignaled fence deadlock on early return '
                                        'without submit. Reset adjacent to actual submission after '
                                        'recording succeeds; distinguish acquired SUBOPTIMAL image '
                                        'obligations and submit failure recovery; WaitIdle alone '
                                        'is not a repair.'},
 'tc13_03_present_retirement': {'prompt': '2 个 frame slot、3 个 swapchain image，renderFinished 按 '
                                          'frame slot 分配；frame fence 结束后能复用或随旧 swapchain 释放吗？',
                                'required': ['imageIndex|图像索引',
                                             'present|呈现',
                                             'fence',
                                             '退役|retire',
                                             '不能|不足|不等于'],
                                'rubric': 'Separate frame slot and image index, use per-image '
                                          'present wait semaphores or equivalent completion proof. '
                                          'Submission fence completion alone does not prove '
                                          'presentation retirement. Do not acquire from an already '
                                          'retired swapchain; distinguish extension and fallback '
                                          'paths.'},
 'tc13_04_verification_bounds': {'prompt': '只解释 barrier2 的 srcStageMask；另给一个未运行的同步方案，能否宣布运行验证通过？',
                                 'required': ['srcStageMask', '未运行|未验证', '规范|SPEC', '不能|不可以|不得'],
                                 'rubric': 'Answer the API question with specification and scope '
                                           'without demanding every runtime gate. Separate static '
                                           'reasoning from executed evidence, explicitly mark the '
                                           'proposal untested; actual implementation completion '
                                           'still requires all applicable verification gates, not '
                                           'only clean validation.'}}
CASES.update(TARGETED_CASES)

# v1.0.11 mobile cohort, separate from the original token-target denominator.
MOBILE_CASES = {'mobile_01_tools_trace': {'prompt': '新 Android CLI 可以录 system trace，但目标手机拿不到 GPU counter。现在只有 CPU '
                                     '调度和提交时间事件；如何诊断带宽并映射项目源码？',
                           'required': ['trace', 'counter|计数器', '带宽', '源码|代码', '不能|未验证|不足'],
                           'rubric': 'Distinguish system scheduling traces from frame resource '
                                     'captures and GPU counters. Do not invent bandwidth or event '
                                     'identifiers. Request the actual trace and code map, preserve '
                                     'unavailable tooling fallback, then bind only observed events '
                                     'to source.'},
 'mobile_02_sustained_pacing': {'prompt': 'GPU短测很快，但十分钟后掉帧；开启插帧后显示FPS提高而输入延迟变差。应如何验证性能改善、热状态和帧节奏？',
                                'required': ['热|thermal',
                                             '真实|渲染',
                                             '生成|插帧',
                                             '呈现|显示',
                                             '延迟',
                                             'pacing|节奏'],
                                'rubric': 'Separate real rendered, generated and presented frames, '
                                          'latency and sustained thermal state. Fix '
                                          'scene/resolution/quality/refresh conditions, choose a '
                                          'single pacing owner, and do not equate displayed FPS '
                                          'with responsiveness or sustained performance.'},
 'mobile_03_local_read_limits': {'prompt': '一台 Vulkan 1.4 手机要使用 depth/stencil 和 multisampled '
                                           'dynamic rendering local read，是否只检查 apiVersion 就足够？',
                                 'required': ['properties|属性',
                                              'depth|深度',
                                              'MSAA|multisample|多重采样',
                                              '不能|不足|不够',
                                              '回退|fallback'],
                                 'rubric': 'Core promotion is not a guarantee for every '
                                           'depth/stencil or multisample local-read combination. '
                                           'Query relevant feature/properties, attachment '
                                           'format/sample support and enabled capabilities '
                                           'independently; retain an equivalent standard rendering '
                                           'fallback.'},
 'mobile_04_tile_fallback': {'prompt': '同一后处理部署到Adreno和Mali，只有一侧具备QCOM tile能力。邻域blur能直接改成input '
                                       'attachment local read吗？要不要为另一侧换GPU？',
                             'required': ['QCOM',
                                          '回退|fallback|标准路径',
                                          '邻域',
                                          'feature|能力',
                                          '不能|不应|不可以'],
                             'rubric': 'Choose the vendor fast path only after actual capability '
                                       'checks, keep standard paths on unsupported hardware '
                                       'without GPU replacement. Distinguish same-pixel local '
                                       'reads from arbitrary neighborhood sampling and require '
                                       'image/performance A/B evidence.'},
 'mobile_05_interop_uuid': {'prompt': 'Vulkan/OpenCL交换opaque FD，device UUID相同但driver '
                                      'UUID不同，可以直接导入并保证往返数据正确吗？',
                            'required': ['driver|驱动',
                                         'UUID',
                                         '不能|不应|不足',
                                         '兼容|compatib',
                                         '回退|fallback'],
                            'rubric': 'Matching device UUID alone does not establish opaque FD '
                                      'interop compatibility when driver UUID differs. Check '
                                      'supported handle properties and API/driver compatibility '
                                      'before import; decline unsupported sharing and use an '
                                      'existing Vulkan or supported copy fallback.'},
 'mobile_06_fd_payload': {'prompt': '为了优化，我把同一个sync FD连续复用很多帧，还将optimal image直接导入通用opaque '
                                    'FD路径。内存和同步的owner、layout及失败回收怎么处理？',
                          'required': ['SYNC_FD|sync FD',
                                       '载荷|payload',
                                       '内存|memory',
                                       'layout|布局',
                                       'owner|所有权',
                                       '失败'],
                          'rubric': 'Distinguish sync payload consumption/import from reusable '
                                    'semaphore objects and external-memory handles. Do not treat '
                                    'SYNC_FD as a persistent timeline handle. Verify optimal image '
                                    'representation, ownership transfer, failure cleanup and FD '
                                    'owner at each stage.'},
 'mobile_07_ahb_camera': {'prompt': 'Camera通过AHardwareBuffer输入图像，我想直接套用generic opaque '
                                    'FD的Vulkan/OpenCL样例。格式、layout和ownership能完全照搬吗？',
                          'required': ['AHardwareBuffer|AHB',
                                       '外部格式|externalFormat|format',
                                       'opaque',
                                       '所有权|ownership',
                                       '不能|不应|不可以'],
                          'rubric': 'AHardwareBuffer camera input and generic opaque FD samples '
                                    'are distinct compatibility paths. Query AHB external format '
                                    'and usage/tiling/layout requirements and verify ownership and '
                                    'synchronization rather than importing assumptions from an '
                                    'opaque FD tutorial.'},
 'mobile_08_fault_generation': {'prompt': 'Mali出现VK_ERROR_DEVICE_LOST但Validation '
                                          'clean，fault报告里一个GPU地址已被分配器复用。可以排除OOB/use-after-free并定位shader行吗？',
                                'required': ['generation|代际|代次',
                                             '提交|submission',
                                             '地址',
                                             '不能|不足|不应',
                                             'OOB|越界',
                                             'use-after-free|释放后'],
                                'rubric': 'Validation silence cannot exclude OOB or lifetime '
                                          'errors. Correlate fault range and address '
                                          'binding/unbinding history with resource generation, '
                                          'aliasing and submissions. Do not invent a shader line '
                                          'from a reused address; report uncertain coverage and '
                                          'collect minimal evidence.'},
 'mobile_09_fault_api': {'prompt': '把vkGetDeviceFaultInfoEXT改成vkGetDeviceFaultInfoKHR就能用KHR '
                                   'fault了吗？device lost之后所有API都不能调用吗？手机没有扩展又怎么办？',
                         'required': ['vkGetDeviceFaultReportsKHR',
                                      'vkGetDeviceFaultDebugInfoKHR',
                                      'vkGetDeviceFaultInfoEXT',
                                      '回退|日志',
                                      '规范|SPEC'],
                         'rubric': 'Reject the invented suffix-renamed KHR API. Distinguish the '
                                   'actual EXT query from KHR reports/debug-info interfaces and '
                                   'legal post-loss operations. Query support and enabled '
                                   'features, do not continue ordinary rendering, and use generic '
                                   'diagnostic logs when unavailable.'},
 'mobile_10_neural_emulation': {'prompt': '新手机API版本1.4但没有ARM tensor/data '
                                          'graph能力，SDK只在PC仿真层跑过。是否能宣称原生神经渲染和移动端性能验收通过？',
                                'required': ['仿真|emulat',
                                             '原生|native',
                                             '未验证|未测试',
                                             '回退|传统',
                                             '不能|不可以|不得'],
                                'rubric': 'A Vulkan version and desktop emulation do not prove ARM '
                                          'tensor/data-graph support or native mobile performance. '
                                          'Verify the selected SDK path and feature/format '
                                          'requirements; distinguish emulation-only checks from '
                                          'device results and select conventional rendering '
                                          'fallback.'},
 'mobile_11_neural_multidevice': {'prompt': 'Arm Neural Graphics SDK '
                                            'v1.1.1接两个Engine、两个独立VkDevice，旋转或切场景后有重影。可以并行初始化然后直接归咎模型或驱动吗？',
                                  'required': ['进程|process',
                                               'VkDevice|设备',
                                               'history|历史',
                                               '旋转|resize',
                                               '输入|motion|depth',
                                               '并发|初始化'],
                                  'rubric': 'Check SDK process-global Vulkan function tables and '
                                            'initialization/device-recreation constraints before '
                                            'declaring multi-device concurrency safe. Audit '
                                            'motion/depth/jitter inputs, ownership, history '
                                            'invalidation at rotation/camera cut/resize and '
                                            'pacing; do not assume model or driver is the cause.'},
 'mobile_12_filament_release': {'prompt': '升级Filament '
                                          'v1.79.0时跨帧缓存TransformManager::Instance并混用旧材质包；main发布说明另有v1.80标题，能按正式v1.80兼容性处理吗？',
                                'required': ['Instance',
                                             '材质|material',
                                             'v1.79',
                                             'v1.80',
                                             '正式|release',
                                             '不能|不应|不足'],
                                'rubric': 'Review released v1.79.0 instance lifetime and '
                                          'material/native-Java binary compatibility rather than '
                                          'assuming cached handles and old resources survive. A '
                                          'main release-note heading does not establish a released '
                                          'v1.80 artifact; pin release/tag and source evidence.'}}
CASES.update(MOBILE_CASES)

# v1.0.12 separate system cohort.
from system_cases import SYSTEM_CASES
CASES.update(SYSTEM_CASES)

# v1.0.13 independent engine-scale cohort.
from engine_cases import ENG13_CASES
CASES.update(ENG13_CASES)

# v1.0.14 independent visual-quality cohort.
from visual_cases import VIS14_CASES
CASES.update(VIS14_CASES)
