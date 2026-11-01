"""ENG13 paired input conditions; private rubrics are never model context."""
ENG13_CASES = {'eng13_01_shader_target': {'id': 'ENG13-01',
                            'prompt': 'Shader用新编译器成功输出SPIR-V，旧手机未查询所需features，可以直接发布吗？\n'
                                      '对照变体：若target environment、扩展/features和设备limits均验证匹配，编译成功后还要区分哪些验证层？\n'
                                      '请分别说明合法条件、失败与回退、可验证证据；不要把未执行的验证说成通过。',
                            'variants': {'primary': 'Shader用新编译器成功输出SPIR-V，旧手机未查询所需features，可以直接发布吗？',
                                         'contrast': '若target '
                                                     'environment、扩展/features和设备limits均验证匹配，编译成功后还要区分哪些验证层？'},
                            'required': ['SPIR-V', 'feature', 'target|环境', '验证'],
                            'rubric': 'Distinguish compiler version, Vulkan/SPIR-V target, enabled runtime '
                                      'features, validation, pipeline creation and actual numerical/image '
                                      'correctness. Matching capabilities permits further validation, not a '
                                      'blanket old-device rejection. Reject compilation success as proof of '
                                      'runtime support.'},
 'eng13_02_reflection_layout': {'id': 'ENG13-02',
                                'prompt': '反射看到普通uniform block，host使用动态UBO且stageFlags是实际使用阶段的超集，能直接判布局非法吗？\n'
                                          '对照变体：若block member offset或matrix/array stride确实不兼容，怎样定位并拒绝错误数据？\n'
                                          '请分别说明合法条件、失败与回退、可验证证据；不要把未执行的验证说成通过。',
                                'variants': {'primary': '反射看到普通uniform '
                                                        'block，host使用动态UBO且stageFlags是实际使用阶段的超集，能直接判布局非法吗？',
                                             'contrast': '若block member offset或matrix/array '
                                                         'stride确实不兼容，怎样定位并拒绝错误数据？'},
                                'required': ['offset', 'stride', '动态|DYNAMIC', '兼容'],
                                'rubric': 'Check actual set/binding/types/counts, offsets, strides, push '
                                          'constants and stage interface. Legal dynamic UBO and allowed '
                                          'stage supersets are not automatically invalid; contrast a real '
                                          'layout mismatch and explain target-specific compatibility rather '
                                          'than textual equality.'},
 'eng13_03_hot_reload': {'id': 'ENG13-03',
                         'prompt': '热更新只改实现且接口兼容，旧命令还在GPU执行，能发布新Pipeline吗？\n'
                                   '对照变体：若新shader新增binding或feature且新Pipeline创建失败，能只换module并销毁旧对象吗？\n'
                                   '请分别说明合法条件、失败与回退、可验证证据；不要把未执行的验证说成通过。',
                         'variants': {'primary': '热更新只改实现且接口兼容，旧命令还在GPU执行，能发布新Pipeline吗？',
                                      'contrast': '若新shader新增binding或feature且新Pipeline创建失败，能只换module并销毁旧对象吗？'},
                         'required': ['接口|interface', 'generation|代际', '旧', '失败'],
                         'rubric': 'Allow compatible new and old pipelines to coexist until actual '
                                   'retirement. Interface or feature changes require coordinated '
                                   'schema/layout/data migration. Keep old usable artifacts on failure; '
                                   'reject half-published layouts, premature in-flight destruction and stale '
                                   'generation callbacks.'},
 'eng13_04_fp16_boundary': {'id': 'ENG13-04',
                            'prompt': 'FP16使画面更快但视锥边缘开始漏对象，能以FPS提高判优化成功吗？\n'
                                      '对照变体：如果目标只有16-bit storage而没有shaderFloat16算术，或者算术支持但stage '
                                      'IO不支持，分别怎样选变体？\n'
                                      '请分别说明合法条件、失败与回退、可验证证据；不要把未执行的验证说成通过。',
                            'variants': {'primary': 'FP16使画面更快但视锥边缘开始漏对象，能以FPS提高判优化成功吗？',
                                         'contrast': '如果目标只有16-bit storage而没有shaderFloat16算术，或者算术支持但stage '
                                                     'IO不支持，分别怎样选变体？'},
                            'required': ['FP16', 'storage', '算术|arithmetic', '边界|漏', '精度'],
                            'rubric': 'Separate arithmetic, storage and stage-I/O features; preserve '
                                      'conservative culling/depth precision and test NaN/Inf, scale and '
                                      'camera boundaries. Faster wrong output fails correctness. Contrast '
                                      'supported precision paths without inferring support from a single '
                                      'feature.'},
 'eng13_05_cache_corrupt': {'id': 'ENG13-05',
                            'prompt': '升级驱动后磁盘PipelineCache校验失败，能修改opaque字节或硬用另一设备的Pipeline Binary吗？\n'
                                      '对照变体：若兼容标识、长度和hash都满足且设备支持相应路径，应怎样使用缓存并保留失效回退？\n'
                                      '请分别说明合法条件、失败与回退、可验证证据；不要把未执行的验证说成通过。',
                            'variants': {'primary': '升级驱动后磁盘PipelineCache校验失败，能修改opaque字节或硬用另一设备的Pipeline '
                                                    'Binary吗？',
                                         'contrast': '若兼容标识、长度和hash都满足且设备支持相应路径，应怎样使用缓存并保留失效回退？'},
                            'required': ['opaque', '驱动|driver', '回退|fallback', 'key|标识'],
                            'rubric': 'Separate layered cache artifacts and validate '
                                      'key/environment/integrity. Reject edited opaque data and cross-driver '
                                      'binary assumptions. A valid cache can be consumed through supported '
                                      'API rules, with cold creation or compatible old path on miss/failure '
                                      'and no guaranteed speed claim.'},
 'eng13_06_async_cancel': {'id': 'ENG13-06',
                           'prompt': '后台Pipeline任务引用已离开作用域的create-info指针，Device已退出后结果才返回，如何处理？\n'
                                     '对照变体：若输入拥有稳定寿命且Device/material generation仍有效，怎样发布新结果并分别退休CPU任务与GPU对象？\n'
                                     '请分别说明合法条件、失败与回退、可验证证据；不要把未执行的验证说成通过。',
                           'variants': {'primary': '后台Pipeline任务引用已离开作用域的create-info指针，Device已退出后结果才返回，如何处理？',
                                        'contrast': '若输入拥有稳定寿命且Device/material '
                                                    'generation仍有效，怎样发布新结果并分别退休CPU任务与GPU对象？'},
                           'required': ['generation|代际', '输入|指针', '取消|cancel', '退休|退役'],
                           'rubric': 'Own all create-info/pNext/shader input memory through creation, '
                                     'coordinate device teardown and reject canceled/stale completion. Valid '
                                     'results may publish atomically; CPU task completion and GPU object '
                                     'retirement are distinct. Do not resurrect old devices or free '
                                     'executing inputs.'},
 'eng13_07_cache_concurrency': {'id': 'ENG13-07',
                                'prompt': '多个线程共享VkPipelineCache，能以Vulkan内部同步为理由无锁调用所有cache命令吗？\n'
                                          '对照变体：若使用EXTERNALLY_SYNCHRONIZED标志，或改每线程cache后merge，检查与同步责任怎样变化？\n'
                                          '请分别说明合法条件、失败与回退、可验证证据；不要把未执行的验证说成通过。',
                                'variants': {'primary': '多个线程共享VkPipelineCache，能以Vulkan内部同步为理由无锁调用所有cache命令吗？',
                                             'contrast': '若使用EXTERNALLY_SYNCHRONIZED标志，或改每线程cache后merge，检查与同步责任怎样变化？'},
                                'required': ['flags|标志', '同步', '命令|调用', 'cache|Cache'],
                                'rubric': 'Determine host synchronization per command and actual cache '
                                          'flags, including external-synchronization opt-out and merge '
                                          'accesses. Contrast internally supported operations, explicit '
                                          'locks and per-thread caches rather than declaring every Vulkan '
                                          'object universally synchronized.'},
 'eng13_08_variant_cost': {'id': 'ENG13-08',
                           'prompt': '把几十份shader改成specialization constants再启用GPL，是否必然减少Pipeline数量并显著加速？\n'
                                     '对照变体：若组合只用少数且实测冷/热创建不同，如何统计source、SPIR-V、key及实际使用组合？\n'
                                     '请分别说明合法条件、失败与回退、可验证证据；不要把未执行的验证说成通过。',
                           'variants': {'primary': '把几十份shader改成specialization '
                                                   'constants再启用GPL，是否必然减少Pipeline数量并显著加速？',
                                        'contrast': '若组合只用少数且实测冷/热创建不同，如何统计source、SPIR-V、key及实际使用组合？'},
                           'required': ['SPIR-V', 'Pipeline', '组合', '测|验证'],
                           'rubric': 'Count source variants, bytecode artifacts, pipeline keys and actually '
                                     'used specialization/state combinations separately. Specialization and '
                                     'GPL can help selected workloads but do not automatically reduce '
                                     'pipeline count or total cost; require controlled cold/warm '
                                     'measurements.'},
 'eng13_09_offscreen_texture': {'id': 'ENG13-09',
                                'prompt': '没有Surface或swapchain，但有效VkDevice支持纹理format/usage，能创建普通离屏image并上传吗？\n'
                                          '对照变体：若项目初始化顺序强依赖Surface，或资源是外部AHB，怎样区分引擎约束与API/导入合同？\n'
                                          '请分别说明合法条件、失败与回退、可验证证据；不要把未执行的验证说成通过。',
                                'variants': {'primary': '没有Surface或swapchain，但有效VkDevice支持纹理format/usage，能创建普通离屏image并上传吗？',
                                             'contrast': '若项目初始化顺序强依赖Surface，或资源是外部AHB，怎样区分引擎约束与API/导入合同？'},
                                'required': ['Surface', 'Device', 'AHB', '约束|合同'],
                                'rubric': 'Ordinary image creation is device/resource-dependent, not '
                                          'inherently Surface-dependent. Preserve actual engine '
                                          'initialization constraints and external AHB requirements '
                                          'separately; never turn one project order into a universal Vulkan '
                                          'precondition or ignore resource capability checks.'},
 'eng13_10_ktx_formats': {'id': 'ENG13-10',
                          'prompt': 'KTX2/Basis纹理准备在不同手机转码，可按品牌固定ASTC并对全部压缩mip直接blit吗？\n'
                                    '对照变体：若查询目标format/usage/tiling和过滤支持充分，怎样选择上传路径；不支持时如何离线mip或转码回退？\n'
                                    '请分别说明合法条件、失败与回退、可验证证据；不要把未执行的验证说成通过。',
                          'variants': {'primary': 'KTX2/Basis纹理准备在不同手机转码，可按品牌固定ASTC并对全部压缩mip直接blit吗？',
                                       'contrast': '若查询目标format/usage/tiling和过滤支持充分，怎样选择上传路径；不支持时如何离线mip或转码回退？'},
                          'required': ['KTX', '格式|format', 'mip', 'blit', '回退|fallback'],
                          'rubric': 'Distinguish container, transmission encoding, transcode result and GPU '
                                    'format. Query usage/tiling/filter support and validate compressed '
                                    'blocks/copy regions. Supported paths are conditional; unsupported blits '
                                    'require offline mip or valid format fallback, not brand assumptions.'},
 'eng13_11_partial_mips': {'id': 'ENG13-11',
                           'prompt': '完整mip链已分配但仅部分上传，限制sampler LOD是否同时保证不读未初始化mip并释放未用显存？\n'
                                     '对照变体：如果改用较小替代image或重建较小资源，怎样安全发布view/descriptor并等待旧使用退休？\n'
                                     '请分别说明合法条件、失败与回退、可验证证据；不要把未执行的验证说成通过。',
                           'variants': {'primary': '完整mip链已分配但仅部分上传，限制sampler LOD是否同时保证不读未初始化mip并释放未用显存？',
                                        'contrast': '如果改用较小替代image或重建较小资源，怎样安全发布view/descriptor并等待旧使用退休？'},
                           'required': ['mip', 'LOD', 'allocation|分配', 'descriptor', '退休|退役'],
                           'rubric': 'Prevent uninitialized sampling with initialized ranges, view-relative '
                                     'LOD semantics and safe versioned descriptors. A LOD clamp does not '
                                     'free full image allocation; distinguish logical availability, actual '
                                     'memory reclamation and optional sparse paths. Retire old references '
                                     'after completion.'},
 'eng13_12_upload_cancel': {'id': 'ENG13-12',
                            'prompt': '上传尚未submit时取消，与copy已提交后取消，staging和geometry回收条件相同吗？\n'
                                      '对照变体：两个Engine共享mesh，一个退出但另一个仍引用，预算下降时能直接淘汰它吗？\n'
                                      '请分别说明合法条件、失败与回退、可验证证据；不要把未执行的验证说成通过。',
                            'variants': {'primary': '上传尚未submit时取消，与copy已提交后取消，staging和geometry回收条件相同吗？',
                                         'contrast': '两个Engine共享mesh，一个退出但另一个仍引用，预算下降时能直接淘汰它吗？'},
                            'required': ['提交|submit', 'staging', '共享', 'generation|代际', '完成'],
                            'rubric': 'Separate pre-submit CPU cancellation from pending GPU copies and '
                                      'readers. Keep staging/resource memory until relevant completion, '
                                      'preserve shared ownership and generations, and apply bounded '
                                      'backpressure/resident alternatives rather than destroying other '
                                      'Engine references.'},
 'eng13_13_dispatch_limits': {'id': 'ENG13-13',
                              'prompt': 'Compute写间接dispatch参数后用DISPATCH_INDIRECT_BIT同步，并把x*y*z与maxComputeWorkGroupCount比较，可以吗？\n'
                                        '对照变体：若每维groupCount合法但shader LocalSize或总local '
                                        'invocations超限，应如何区分和验证？\n'
                                        '请分别说明合法条件、失败与回退、可验证证据；不要把未执行的验证说成通过。',
                              'variants': {'primary': 'Compute写间接dispatch参数后用DISPATCH_INDIRECT_BIT同步，并把x*y*z与maxComputeWorkGroupCount比较，可以吗？',
                                           'contrast': '若每维groupCount合法但shader LocalSize或总local '
                                                       'invocations超限，应如何区分和验证？'},
                              'required': ['DRAW_INDIRECT',
                                           'x|每维',
                                           'LocalSize|local',
                                           'maxComputeWorkGroupCount'],
                              'rubric': 'Indirect dispatch parameters are consumed at DRAW_INDIRECT with '
                                        'INDIRECT_COMMAND_READ. Reject invented DISPATCH_INDIRECT stage. '
                                        'Check each x/y/z group-count limit independently and separately '
                                        'validate local dimensions/product, shader target and enabled '
                                        'limits.'},
 'eng13_14_fixed_slots': {'id': 'ENG13-14',
                          'prompt': 'GPU每帧更新固定槽位instanceCount，不可见槽设0；没有Indirect Count就不是真正GPU可见性控制吗？\n'
                                    '对照变体：若设备没有multiDrawIndirect，逐条drawCount=1可否作为合法回退，又能否保证CPU一定更快？\n'
                                    '请分别说明合法条件、失败与回退、可验证证据；不要把未执行的验证说成通过。',
                          'variants': {'primary': 'GPU每帧更新固定槽位instanceCount，不可见槽设0；没有Indirect '
                                                  'Count就不是真正GPU可见性控制吗？',
                                       'contrast': '若设备没有multiDrawIndirect，逐条drawCount=1可否作为合法回退，又能否保证CPU一定更快？'},
                          'required': ['instanceCount', '固定|槽', '回退|fallback', 'CPU'],
                          'rubric': 'Recognize GPU-written fixed-slot visibility as valid GPU-driven '
                                    'baseline, with all slots refreshed each frame. Count is optional and '
                                    'CPU readback is not required. Single-command draw fallback is legal '
                                    'when constraints hold but no CPU speedup is guaranteed.'},
 'eng13_15_feature_separation': {'id': 'ENG13-15',
                                 'prompt': '设备支持Indirect '
                                           'Count但没启用drawIndirectFirstInstance，能用非零firstInstance映射object '
                                           'ID并默认有DrawID/BDA吗？\n'
                                           '对照变体：若multiDrawIndirect、firstInstance、shader draw '
                                           'parameters分别可用，怎样逐项选路径和低能力回退？\n'
                                           '请分别说明合法条件、失败与回退、可验证证据；不要把未执行的验证说成通过。',
                                 'variants': {'primary': '设备支持Indirect '
                                                         'Count但没启用drawIndirectFirstInstance，能用非零firstInstance映射object '
                                                         'ID并默认有DrawID/BDA吗？',
                                              'contrast': '若multiDrawIndirect、firstInstance、shader draw '
                                                          'parameters分别可用，怎样逐项选路径和低能力回退？'},
                                 'required': ['firstInstance', 'multiDraw', 'Count', '回退|fallback'],
                                 'rubric': 'Query support and enablement independently for multi-draw, '
                                           'firstInstance, indirect count, draw parameters, BDA and '
                                           'descriptor indexing. Use legal zero-base mapping or batch '
                                           'fallback when required; never infer all features from Count/core '
                                           'API version.'},
 'eng13_16_capacity_abi': {'id': 'ENG13-16',
                           'prompt': 'compute append写命令超过容量，但draw时maxDrawCount被限制，还会越界吗？\n'
                                     '对照变体：若使用紧凑前缀且容量足够，仍须如何校验offset/stride、count、VkDrawIndexedIndirectCommand与负vertexOffset？\n'
                                     '请分别说明合法条件、失败与回退、可验证证据；不要把未执行的验证说成通过。',
                           'variants': {'primary': 'compute append写命令超过容量，但draw时maxDrawCount被限制，还会越界吗？',
                                        'contrast': '若使用紧凑前缀且容量足够，仍须如何校验offset/stride、count、VkDrawIndexedIndirectCommand与负vertexOffset？'},
                           'required': ['容量|capacity', '写入|write', 'stride', 'vertexOffset', '前缀|prefix'],
                           'rubric': 'Bound writes before append, handle counter overflow and keep count '
                                     'aligned with initialized compact prefix. maxDrawCount does not prevent '
                                     'producer OOB. Check exact command ABI, signed vertexOffset, '
                                     'alignment/stride/range and overflow-safe byte arithmetic including '
                                     'zero/count-one cases.'},
 'eng13_17_reset_compact': {'id': 'ENG13-17',
                            'prompt': '先fill清零count，再cull、compact、draw；只在最后加command barrier，shader '
                                      'barrier能覆盖全部dispatch和count依赖吗？\n'
                                      '对照变体：若合并成一个dispatch，workgroup之间或跨queue仍有哪些不能靠barrier()保证？\n'
                                      '请分别说明合法条件、失败与回退、可验证证据；不要把未执行的验证说成通过。',
                            'variants': {'primary': '先fill清零count，再cull、compact、draw；只在最后加command '
                                                    'barrier，shader barrier能覆盖全部dispatch和count依赖吗？',
                                         'contrast': '若合并成一个dispatch，workgroup之间或跨queue仍有哪些不能靠barrier()保证？'},
                            'required': ['count', 'reset|清零|fill', 'compact', 'barrier', '跨|全局'],
                            'rubric': 'Cover fill-to-atomic read/write, cull-to-compact, command and '
                                      'separate count-to-draw dependencies. Shader barriers are not global '
                                      'cross-workgroup/dispatch/queue completion. Even fused work requires '
                                      'legal algorithm synchronization; no generic final barrier repairs '
                                      'missing producer dependencies.'},
 'eng13_18_consumers': {'id': 'ENG13-18',
                        'prompt': 'compute同时生成indirect command、visible-ID SSBO、vertex stream和index '
                                  'stream，只加DRAW_INDIRECT/INDIRECT_COMMAND_READ够吗？\n'
                                  '对照变体：若实际只生成command/count、不写vertex或SSBO，怎样按真实消费者缩小同步而不机械ALL_COMMANDS？\n'
                                  '请分别说明合法条件、失败与回退、可验证证据；不要把未执行的验证说成通过。',
                        'variants': {'primary': 'compute同时生成indirect command、visible-ID SSBO、vertex '
                                                'stream和index '
                                                'stream，只加DRAW_INDIRECT/INDIRECT_COMMAND_READ够吗？',
                                     'contrast': '若实际只生成command/count、不写vertex或SSBO，怎样按真实消费者缩小同步而不机械ALL_COMMANDS？'},
                        'required': ['DRAW_INDIRECT', 'SSBO', 'VERTEX|vertex', 'INDEX|index', '访问|access'],
                        'rubric': 'Map command/count to indirect read, shader SSBO to actual shader storage '
                                  'read, vertex data to vertex attribute fetch and index data to index '
                                  'input. Apply only actual producer/consumer accesses with queue-capable '
                                  'stages; do not assume indirect synchronization covers all resource '
                                  'roles.'},
 'eng13_19_state_bins': {'id': 'ENG13-19',
                         'prompt': '一次MDI数组含不同Pipeline、blend和descriptor的对象，命令是否自动切状态？标准alpha透明也可任意重排吗？\n'
                                   '对照变体：没有Bindless时怎样按兼容批次绘制；additive且顺序无关特效与标准透明的取舍有何不同？\n'
                                   '请分别说明合法条件、失败与回退、可验证证据；不要把未执行的验证说成通过。',
                         'variants': {'primary': '一次MDI数组含不同Pipeline、blend和descriptor的对象，命令是否自动切状态？标准alpha透明也可任意重排吗？',
                                      'contrast': '没有Bindless时怎样按兼容批次绘制；additive且顺序无关特效与标准透明的取舍有何不同？'},
                         'required': ['Pipeline', '批|bin', '透明|alpha', 'descriptor'],
                         'rubric': 'Ordinary MDI consumes parameters under bound compatible state, not '
                                   'arbitrary state changes. Group '
                                   'pipeline/render-target/layout/topology/blend contracts, retain '
                                   'descriptor batching without bindless, and preserve order or appropriate '
                                   'transparency strategy; additive shortcuts are conditional.'},
 'eng13_20_queues': {'id': 'ENG13-20',
                     'prompt': 'Compute与Graphics是同family不同VkQueue，是否天然有序？跨family exclusive '
                               'buffer只加semaphore就足够吗？\n'
                               '对照变体：若使用同queue或concurrent sharing，哪些ownership步骤可省，哪些执行/内存依赖仍必须存在？\n'
                               '请分别说明合法条件、失败与回退、可验证证据；不要把未执行的验证说成通过。',
                     'variants': {'primary': 'Compute与Graphics是同family不同VkQueue，是否天然有序？跨family exclusive '
                                             'buffer只加semaphore就足够吗？',
                                  'contrast': '若使用同queue或concurrent sharing，哪些ownership步骤可省，哪些执行/内存依赖仍必须存在？'},
                     'required': ['queue|Queue', 'family', 'semaphore', 'ownership|所有权', '同步'],
                     'rubric': 'Different queues require execution/memory synchronization even within one '
                               'family. Exclusive cross-family transfer may require release/acquire '
                               'ownership; concurrent sharing removes that transfer, not dependencies. '
                               'Same-queue ordering is not automatic resource visibility; no unconditional '
                               'async speed claim.'},
 'eng13_21_lod_residency': {'id': 'ENG13-21',
                            'prompt': '相机在LOD阈值附近抖动，细LOD尚未上传，能输出指向它的indirect command或释放旧粗LOD吗？\n'
                                      '对照变体：若细LOD已驻留且旧命令完成，怎样切换并区分几何LOD、纹理mip与画质误差？\n'
                                      '请分别说明合法条件、失败与回退、可验证证据；不要把未执行的验证说成通过。',
                            'variants': {'primary': '相机在LOD阈值附近抖动，细LOD尚未上传，能输出指向它的indirect command或释放旧粗LOD吗？',
                                         'contrast': '若细LOD已驻留且旧命令完成，怎样切换并区分几何LOD、纹理mip与画质误差？'},
                            'required': ['resident|驻留', '滞回|hysteresis', '旧', 'LOD', '地址|引用'],
                            'rubric': 'Choose resident fallback with hysteresis and valid generation/address '
                                      'ranges. Never emit unready geometry references or retire still-used '
                                      'storage. Compare culling at fixed LOD and measure LOD quality '
                                      'separately; transition only after upload visibility and old-reader '
                                      'retirement.'},
 'eng13_22_hiz': {'id': 'ENG13-22',
                  'prompt': '常规Z做max层级与Reversed-Z做min层级，clear/比较方向能不变吗？相机瞬移后上一帧深度可以继续剔除吗？\n'
                            '对照变体：若使用当前帧可信不透明深度，如何保守处理空洞、近平面、NPOT边缘与透明覆盖，避免漏画？\n'
                            '请分别说明合法条件、失败与回退、可验证证据；不要把未执行的验证说成通过。',
                  'variants': {'primary': '常规Z做max层级与Reversed-Z做min层级，clear/比较方向能不变吗？相机瞬移后上一帧深度可以继续剔除吗？',
                               'contrast': '若使用当前帧可信不透明深度，如何保守处理空洞、近平面、NPOT边缘与透明覆盖，避免漏画？'},
                  'required': ['max', 'min', 'clear', '保守', '历史|history|上一帧'],
                  'rubric': 'Derive reduction/clear/compare/epsilon for the selected depth convention, '
                            'include holes/far samples and conservatively cover projected bounds. Invalidate '
                            'stale history on camera/scene/output changes. Current-frame trustworthy depth '
                            'still needs NPOT/near-plane/alpha/MSAA conservative tests and reference '
                            'no-missing-ID comparison.'},
 'eng13_23_particles_cost': {'id': 'ENG13-23',
                             'prompt': 'GPU粒子alive list可能溢出，但draw数下降了，能宣布优化成功并任意重排标准alpha粒子吗？\n'
                                       '对照变体：如果容量有界且特效是additive，怎样对照CPU/GPU完整时间、图像、显存和持续热状态？\n'
                                       '请分别说明合法条件、失败与回退、可验证证据；不要把未执行的验证说成通过。',
                             'variants': {'primary': 'GPU粒子alive list可能溢出，但draw数下降了，能宣布优化成功并任意重排标准alpha粒子吗？',
                                          'contrast': '如果容量有界且特效是additive，怎样对照CPU/GPU完整时间、图像、显存和持续热状态？'},
                             'required': ['alive', '容量|capacity', '透明|alpha', 'CPU', 'GPU', '热|thermal'],
                             'rubric': 'Validate spawn/kill, bounded alive/indirect counts, ping-pong '
                                       'lifetime and update-to-draw synchronization. Standard alpha order '
                                       'differs from additive. Draw-count reduction alone proves neither '
                                       'correctness nor total speed; measure fair full CPU/GPU cost, '
                                       'quality, memory and sustained thermals.'},
 'eng13_24_mesh_multiview': {'id': 'ENG13-24',
                             'prompt': '一个输出支持mesh/task与async候选路径，另一个低能力输出不支持，必须升级硬件并共用可见列表吗？\n'
                                       '对照变体：若扩展/features/limits满足，怎样独立验证mesh与task、每view的LOD/Hi-Z及async真实overlap和回退？\n'
                                       '请分别说明合法条件、失败与回退、可验证证据；不要把未执行的验证说成通过。',
                             'variants': {'primary': '一个输出支持mesh/task与async候选路径，另一个低能力输出不支持，必须升级硬件并共用可见列表吗？',
                                          'contrast': '若扩展/features/limits满足，怎样独立验证mesh与task、每view的LOD/Hi-Z及async真实overlap和回退？'},
                             'required': ['mesh|Mesh', 'task', 'view|视图', '回退|fallback', 'async'],
                             'rubric': 'Mesh/task features and limits are independent optional enhancements. '
                                       'Preserve indexed indirect/CPU fallback and common resident scene '
                                       'contracts, separate per-view culling/LOD/history/output buffers and '
                                       'completion, and measure actual async overlap without forced '
                                       'hardware/API upgrade or shared-list contamination.'}}
