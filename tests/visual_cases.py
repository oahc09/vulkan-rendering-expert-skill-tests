"""VIS14 paired scenarios. Private rubrics must never enter model context."""
VIS14_CASES = {'vis14_01_query_only': {'id': 'VIS14-01',
                         'prompt': '设备有rayQuery/AS/BDA但没有RT Pipeline；是否需要SBT和RT shader stage？\n'
                                   '对照变体：另一设备缺rayQuery；如何保留合法基础路径而不反复尝试初始化？\n'
                                   '请分别说明能力/数据/生命周期边界、失败回退与可核验证据；未执行项明确标出。',
                         'variants': {'primary': '设备有rayQuery/AS/BDA但没有RT Pipeline；是否需要SBT和RT shader stage？',
                                      'contrast': '另一设备缺rayQuery；如何保留合法基础路径而不反复尝试初始化？'},
                         'required': ['query|查询', 'SBT', '回退|fallback'],
                         'rubric': 'Treat query/AS/BDA and their actual dependencies as independent from RT '
                                   'pipeline, SBT, Bindless and Mesh. Enable queried features and use actual '
                                   'fragment/compute stage. Missing query takes shadow-map/probe fallback.'},
 'vis14_02_visibility': {'id': 'VIS14-02',
                         'prompt': '主相机外物体会向屏内地面投影，GPU相机剔除后能直接从shadow和AS集合删除吗？\n'
                                   '对照变体：若物体确实在光源和反射作用范围外，如何以显式近似和预算决定剔除？\n'
                                   '请分别说明能力/数据/生命周期边界、失败回退与可核验证据；未执行项明确标出。',
                         'variants': {'primary': '主相机外物体会向屏内地面投影，GPU相机剔除后能直接从shadow和AS集合删除吗？',
                                      'contrast': '若物体确实在光源和反射作用范围外，如何以显式近似和预算决定剔除？'},
                         'required': ['投影|shadow', '集合|set', '反射|reflection'],
                         'rubric': 'Distinguish camera, light-caster and reflection/AS relevance sets. '
                                   'Retain offscreen contributors, express proxy/LOD policy and resource '
                                   'generations; do not demand all scene geometry without bounds.'},
 'vis14_03_depth_bias': {'id': 'VIS14-03',
                         'prompt': '正Z与反Z场景都使用clear=1、LESS和固定0.005 bias是否正确？\n'
                                   '对照变体：场景尺度差100倍且出现acne和悬浮阴影，如何分别验证投影、清除、比较和bias？\n'
                                   '请分别说明能力/数据/生命周期边界、失败回退与可核验证据；未执行项明确标出。',
                         'variants': {'primary': '正Z与反Z场景都使用clear=1、LESS和固定0.005 bias是否正确？',
                                      'contrast': '场景尺度差100倍且出现acne和悬浮阴影，如何分别验证投影、清除、比较和bias？'},
                         'required': ['clear|清除', 'bias', '尺度|scale'],
                         'rubric': 'Choose depth mapping, projection, clear and comparison together; '
                                   'handedness is insufficient. Derive bias sign/scale and CSM stabilization '
                                   'from actual mapping, verify acne/peter-panning rather than universal '
                                   'constants.'},
 'vis14_04_reflection_fallback': {'id': 'VIS14-04',
                                  'prompt': 'SSR对屏内物体命中有效，怎样输出置信度并与环境探针混合？\n'
                                            '对照变体：屏外或遮挡造成SSR失配时，可否用模糊补造真实反射并声称完整GI？\n'
                                            '请分别说明能力/数据/生命周期边界、失败回退与可核验证据；未执行项明确标出。',
                                  'variants': {'primary': 'SSR对屏内物体命中有效，怎样输出置信度并与环境探针混合？',
                                               'contrast': '屏外或遮挡造成SSR失配时，可否用模糊补造真实反射并声称完整GI？'},
                                  'required': ['SSR', '置信|confidence', '探针|probe'],
                                  'rubric': 'Use valid SSR when supported, reject '
                                            'missing/out-of-bounds/occluded history, fall back to probe. Do '
                                            'not claim screen-space reconstruction provides missing geometry '
                                            'or complete global illumination.'},
 'vis14_05_as_dependencies': {'id': 'VIS14-05',
                              'prompt': 'compute蒙皮写顶点→BLAS→TLAS→fragment query，每步stage/access怎么选？\n'
                                        '对照变体：把BLAS与依赖它的TLAS放一个multi-build数组是否自动有序，query能用RT专用stage吗？\n'
                                        '请分别说明能力/数据/生命周期边界、失败回退与可核验证据；未执行项明确标出。',
                              'variants': {'primary': 'compute蒙皮写顶点→BLAS→TLAS→fragment '
                                                      'query，每步stage/access怎么选？',
                                           'contrast': '把BLAS与依赖它的TLAS放一个multi-build数组是否自动有序，query能用RT专用stage吗？'},
                              'required': ['SHADER_READ', 'FRAGMENT_SHADER', 'BLAS', 'TLAS'],
                              'rubric': 'Separate build input SHADER_READ from AS_READ. Describe skin-write '
                                        'to build-input, BLAS-write to TLAS-read and AS-write to fragment '
                                        'AS-read dependencies; array ordering is not synchronization.'},
 'vis14_06_scratch': {'id': 'VIS14-06',
                      'prompt': '两个并行AS build使用同一scratch buffer重叠地址，offset各自对齐就安全吗？\n'
                                '对照变体：若地址范围不重叠或两build有明确串行依赖，怎样分别判断对齐、容量与复用？\n'
                                '请分别说明能力/数据/生命周期边界、失败回退与可核验证据；未执行项明确标出。',
                      'variants': {'primary': '两个并行AS build使用同一scratch buffer重叠地址，offset各自对齐就安全吗？',
                                   'contrast': '若地址范围不重叠或两build有明确串行依赖，怎样分别判断对齐、容量与复用？'},
                      'required': ['scratch', '对齐|align', '范围|range'],
                      'rubric': 'Validate actual device address alignment and full size, reject overlapping '
                                'concurrent scratch, permit non-overlap or correctly synchronized sequential '
                                'reuse. Same buffer handle alone neither proves conflict nor safety.'},
 'vis14_07_update': {'id': 'VIS14-07',
                     'prompt': '刚体只改transform、BLAS初建含ALLOW_UPDATE，必须重建全部几何吗？\n'
                               '对照变体：蒙皮拓扑或primitive count变化、原build不允许UPDATE时，可以无条件update吗？\n'
                               '请分别说明能力/数据/生命周期边界、失败回退与可核验证据；未执行项明确标出。',
                     'variants': {'primary': '刚体只改transform、BLAS初建含ALLOW_UPDATE，必须重建全部几何吗？',
                                  'contrast': '蒙皮拓扑或primitive count变化、原build不允许UPDATE时，可以无条件update吗？'},
                     'required': ['UPDATE', 'BUILD|重建', 'transform|变换'],
                     'rubric': 'Separate rigid instance TLAS transform from deforming BLAS, check all '
                               'relevant UPDATE invariants and original flags. Invalid update requires '
                               'BUILD, while legal update still needs measured cost and synchronization.'},
 'vis14_08_compaction': {'id': 'VIS14-08',
                         'prompt': 'BLAS compact得到新地址后，旧TLAS和帧仍在执行，能立刻销毁旧AS吗？\n'
                                   '对照变体：所有消费者完成且新TLAS已发布时，如何安全退休旧对象与重复失败回退？\n'
                                   '请分别说明能力/数据/生命周期边界、失败回退与可核验证据；未执行项明确标出。',
                         'variants': {'primary': 'BLAS compact得到新地址后，旧TLAS和帧仍在执行，能立刻销毁旧AS吗？',
                                      'contrast': '所有消费者完成且新TLAS已发布时，如何安全退休旧对象与重复失败回退？'},
                         'required': ['地址|address', 'TLAS', '退休|回收|retire'],
                         'rubric': 'Separate compaction completion, new address publication/TLAS replacement '
                                   'and old object retirement. Track all in-flight references; retain old '
                                   'usable generation on failure and reclaim only after actual completion.'},
 'vis14_09_shared_lifetime': {'id': 'VIS14-09',
                              'prompt': '主相机剔除mesh且请求被取消，但另一View的反射TLAS仍引用其BLAS，如何回收？\n'
                                        '对照变体：最后一个TLAS/query和hit-shading消费者都已完成时，哪些输入/scratch/材质资源可释放？\n'
                                        '请分别说明能力/数据/生命周期边界、失败回退与可核验证据；未执行项明确标出。',
                              'variants': {'primary': '主相机剔除mesh且请求被取消，但另一View的反射TLAS仍引用其BLAS，如何回收？',
                                           'contrast': '最后一个TLAS/query和hit-shading消费者都已完成时，哪些输入/scratch/材质资源可释放？'},
                              'required': ['BLAS', 'generation|代际', '完成|completion'],
                              'rubric': 'Tie residency/cancellation to all consumers and generations. Build '
                                        'input/scratch may be reusable after build completion, but live TLAS '
                                        'references and hit-shading vertex/material/texture access remain '
                                        'separate lifetime constraints.'},
 'vis14_10_alpha': {'id': 'VIS14-10',
                    'prompt': 'opaque、alpha-cutout和alpha-blend统一标opaque做query阴影会怎样？\n'
                              '对照变体：单次反射要最近有效命中，能否遇到首个candidate就早停，cutout如何确认与继续？\n'
                              '请分别说明能力/数据/生命周期边界、失败回退与可核验证据；未执行项明确标出。',
                    'variants': {'primary': 'opaque、alpha-cutout和alpha-blend统一标opaque做query阴影会怎样？',
                                 'contrast': '单次反射要最近有效命中，能否遇到首个candidate就早停，cutout如何确认与继续？'},
                    'required': ['candidate', 'alpha', '最近|nearest'],
                    'rubric': 'Separate opaque, binary cutout and blended transparency. Alpha test '
                              'candidates with consistent material UV/cutoff and continue/confirm traversal; '
                              'terminate-on-first-hit belongs to suitable occlusion, not nearest-reflection '
                              'semantics.'},
 'vis14_11_omm': {'id': 'VIS14-11',
                  'prompt': '只有KHR OMM与只有EXT OMM的对象/依赖/host命令/query shader控制可以只换后缀吗？\n'
                            '对照变体：alpha纹理或cutoff运行时改变、micromap为unknown状态，如何失效与回退？\n'
                            '请分别说明能力/数据/生命周期边界、失败回退与可核验证据；未执行项明确标出。',
                  'variants': {'primary': '只有KHR OMM与只有EXT OMM的对象/依赖/host命令/query shader控制可以只换后缀吗？',
                               'contrast': 'alpha纹理或cutoff运行时改变、micromap为unknown状态，如何失效与回退？'},
                  'required': ['KHR', 'EXT', 'unknown', '失效|invalidate'],
                  'rubric': 'Check pinned KHR/EXT contracts independently, including AS versus micromap '
                            'objects and KHR query execution-mode requirement. Hash alpha bake '
                            'compatibility, rebuild/fallback on change, and resolve unknown opacity through '
                            'material logic, never transparent by default.'},
 'vis14_12_motion': {'id': 'VIS14-12',
                     'prompt': 'producer输出current→previous pixel MV但consumer要求UV且不含jitter，怎样转换？\n'
                               '对照变体：另一producer输出反方向或含projection jitter，能否只看motion纹理不是黑色就通过？\n'
                               '请分别说明能力/数据/生命周期边界、失败回退与可核验证据；未执行项明确标出。',
                     'variants': {'primary': 'producer输出current→previous pixel '
                                             'MV但consumer要求UV且不含jitter，怎样转换？',
                                  'contrast': '另一producer输出反方向或含projection jitter，能否只看motion纹理不是黑色就通过？'},
                     'required': ['方向|direction', 'jitter', 'pixel|像素', 'UV'],
                     'rubric': 'Define direction, units, source dimensions, Y orientation and jitter exactly '
                               'for each consumer. Verify known translation and current/previous sample '
                               'offsets without double cancellation; nonblack texture is not semantic '
                               'evidence.'},
 'vis14_13_deformation': {'id': 'VIS14-13',
                          'prompt': '相机静止、蒙皮人物运动，只用previous camera matrix生成MV是否足够？\n'
                                    '对照变体：完全静止刚体与相机都不动时，怎样用对照验证previous object/deformation而不臆造运动？\n'
                                    '请分别说明能力/数据/生命周期边界、失败回退与可核验证据；未执行项明确标出。',
                          'variants': {'primary': '相机静止、蒙皮人物运动，只用previous camera matrix生成MV是否足够？',
                                       'contrast': '完全静止刚体与相机都不动时，怎样用对照验证previous object/deformation而不臆造运动？'},
                          'required': ['previous|上一', '蒙皮|deform', 'motion|MV'],
                          'rubric': 'Track prior camera, object, skin/procedural deformation states per '
                                    'logical frame. Camera-only motion misses animated geometry; contrast '
                                    'truly static geometry and validate actual generated buffers rather than '
                                    'force nonzero MV.'},
 'vis14_14_lighting_history': {'id': 'VIS14-14',
                               'prompt': 'geometry不动、MV为0，但灯光和阴影快速移动，history可以一直高权重吗？\n'
                                         '对照变体：灯光与相机均稳定时，如何增加稳定累积而不每帧全部清空？\n'
                                         '请分别说明能力/数据/生命周期边界、失败回退与可核验证据；未执行项明确标出。',
                               'variants': {'primary': 'geometry不动、MV为0，但灯光和阴影快速移动，history可以一直高权重吗？',
                                            'contrast': '灯光与相机均稳定时，如何增加稳定累积而不每帧全部清空？'},
                               'required': ['光|light', 'history|历史', '置信|权重|confidence'],
                               'rubric': 'Radiance/visibility change is independent of geometric motion. '
                                         'Reduce/reject affected history for light/shadow changes while '
                                         'allowing confidence/age-controlled accumulation in stable regions; '
                                         'do not globally reset every frame.'},
 'vis14_15_exposure': {'id': 'VIS14-15',
                       'prompt': 'history存linearRadiance乘exposure，曝光从1变2可以直接与current相加吗？\n'
                                 '对照变体：若SDK采用相反pre-exposure定义或因子非有限/为0，应怎样处理和验证HDR？\n'
                                 '请分别说明能力/数据/生命周期边界、失败回退与可核验证据；未执行项明确标出。',
                       'variants': {'primary': 'history存linearRadiance乘exposure，曝光从1变2可以直接与current相加吗？',
                                    'contrast': '若SDK采用相反pre-exposure定义或因子非有限/为0，应怎样处理和验证HDR？'},
                       'required': ['exposure|曝光', '比|ratio|尺度', 'HDR'],
                       'rubric': 'Rescale history according to exact color/exposure definition '
                                 '(current/previous for stated multiplication), do not clip HDR radiance to '
                                 'visibility range; reject invalid factors or reset and validate high-light '
                                 'transitions.'},
 'vis14_16_history_owner': {'id': 'VIS14-16',
                            'prompt': 'resize/camera cut后仍按swapchain imageIndex复用history，两Engine共用一组纹理安全吗？\n'
                                      '对照变体：算法支持重采样且两个View各有完成点时，如何选择reset/resample与退休？\n'
                                      '请分别说明能力/数据/生命周期边界、失败回退与可核验证据；未执行项明确标出。',
                            'variants': {'primary': 'resize/camera cut后仍按swapchain '
                                                    'imageIndex复用history，两Engine共用一组纹理安全吗？',
                                         'contrast': '算法支持重采样且两个View各有完成点时，如何选择reset/resample与退休？'},
                            'required': ['View|视图', 'reset|重置', 'generation|代际'],
                            'rubric': 'Key history by engine/view/resource generation and logical frame, not '
                                      'presentation index. Apply explicit invalidation policy for '
                                      'cut/size/pause; supported validated resampling is possible, in-flight '
                                      'old resources require retirement.'},
 'vis14_17_filter_semantics': {'id': 'VIS14-17',
                               'prompt': '阴影visibility和HDR反射radiance用同一个0到1截断模糊器，为什么细节丢失？\n'
                                         '对照变体：如何构造非神经history rejection加depth/normal边缘感知滤波，分别衡量拖影和噪声？\n'
                                         '请分别说明能力/数据/生命周期边界、失败回退与可核验证据；未执行项明确标出。',
                               'variants': {'primary': '阴影visibility和HDR反射radiance用同一个0到1截断模糊器，为什么细节丢失？',
                                            'contrast': '如何构造非神经history '
                                                        'rejection加depth/normal边缘感知滤波，分别衡量拖影和噪声？'},
                               'required': ['visibility', 'radiance', 'normal|法线', 'history|历史'],
                               'rubric': 'Use signal-specific ranges/confidence and material/depth/normal '
                                         'checks, preserve HDR, reject disocclusion and clamp history to '
                                         'valid neighborhoods; record noise/detail/temporal tradeoffs rather '
                                         'than hide errors with blur.'},
 'vis14_18_sr_fg': {'id': 'VIS14-18',
                    'prompt': 'SR输出高分辨率color后，把低分辨率depth/MV和已混入UI的图直接喂FG合适吗？\n'
                              '对照变体：另一个SDK明确支持某输入布局时，如何按其revision合同适配而不强制统一格式？\n'
                              '请分别说明能力/数据/生命周期边界、失败回退与可核验证据；未执行项明确标出。',
                    'variants': {'primary': 'SR输出高分辨率color后，把低分辨率depth/MV和已混入UI的图直接喂FG合适吗？',
                                 'contrast': '另一个SDK明确支持某输入布局时，如何按其revision合同适配而不强制统一格式？'},
                    'required': ['SR', 'FG', '尺寸|resolution', 'UI'],
                    'rubric': 'Audit each SDK revision and each stage '
                              'dimensions/jitter/MV/exposure/history/UI contract. Do not transparently reuse '
                              'low-res SR auxiliaries for FG or double-apply TAA/sharpening; supported '
                              'adapter-specific paths remain allowed.'},
 'vis14_19_thermal': {'id': 'VIS14-19',
                      'prompt': '温度上升需从Hybrid降档，瞬间变凉就全量重建Device恢复Enhanced吗？\n'
                                '对照变体：持续稳定达到冷却阈值后如何切换generation/history并公平比较真实与生成帧？\n'
                                '请分别说明能力/数据/生命周期边界、失败回退与可核验证据；未执行项明确标出。',
                      'variants': {'primary': '温度上升需从Hybrid降档，瞬间变凉就全量重建Device恢复Enhanced吗？',
                                   'contrast': '持续稳定达到冷却阈值后如何切换generation/history并公平比较真实与生成帧？'},
                      'required': ['滞回|hysteresis', 'generation|代际', '功耗|power'],
                      'rubric': 'Use predeclared hysteresis/cooldown and priorities, preserve device and '
                                'retire old generations. Separate native/generated/presented frames, fixed '
                                'quality workload and actual latency; temperature/FPS cannot yield '
                                'power-saving percentages.'},
 'vis14_20_source_boundaries': {'id': 'VIS14-20',
                                'prompt': '桌面cage BVH和厂商Mali G2 OMM数字能直接作为本项目Android收益吗？\n'
                                          '对照变体：教程最近更新但API很早存在，Issue报告尚未本地复现时，如何记录日期和证据层？\n'
                                          '请分别说明能力/数据/生命周期边界、失败回退与可核验证据；未执行项明确标出。',
                                'variants': {'primary': '桌面cage BVH和厂商Mali G2 OMM数字能直接作为本项目Android收益吗？',
                                             'contrast': '教程最近更新但API很早存在，Issue报告尚未本地复现时，如何记录日期和证据层？'},
                                'required': ['日期|date', '未验证|未测', '设备|device'],
                                'rubric': 'Distinguish published/updated/checked dates, fixed source '
                                          'revision, official legality, public measurements and unexecuted '
                                          'local claims. No blanket mobile extrapolation, no issue-as-fix or '
                                          'document-update-as-new-API assertion.'}}
