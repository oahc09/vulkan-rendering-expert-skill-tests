"""TRAN15 paired evaluation; private rubrics never enter model context."""
TRAN15_CASES = {'tran15_01_alpha': {'id': 'TRAN15-01',
                     'prompt': '输入是 straight 线性 RGBA，如何设置颜色与 alpha 的 source-over 混合？\n'
                               '对照变体：同一内容改为 premultiplied 输入时哪些转换与因子要变？\n'
                               '请分别给出判断依据、能力与数据合同、同步/生命周期、回退和可执行验证；明确未执行项。',
                     'variants': {'primary': '输入是 straight 线性 RGBA，如何设置颜色与 alpha 的 source-over 混合？',
                                  'contrast': '同一内容改为 premultiplied 输入时哪些转换与因子要变？'},
                     'required': ['alpha', 'ONE', 'SRC_ALPHA'],
                     'rubric': 'Require linear-light operations, straight RGB SRC_ALPHA versus '
                               'premultiplied ONE, destination ONE_MINUS_SRC_ALPHA, alpha ONE and '
                               'ONE_MINUS_SRC_ALPHA. Decode before premultiplication and do not '
                               'multiply alpha twice. Separate offscreen alpha from Android '
                               'compositeAlpha.'},
 'tran15_02_order': {'id': 'TRAN15-02',
                     'prompt': '红在前蓝在后，两层 alpha=0.5，黑色背景，不开 tone mapping，线性结果是多少？\n'
                               '对照变体：交换前后深度，结果和 alpha 如何变化？\n'
                               '请分别给出判断依据、能力与数据合同、同步/生命周期、回退和可执行验证；明确未执行项。',
                     'variants': {'primary': '红在前蓝在后，两层 alpha=0.5，黑色背景，不开 tone mapping，线性结果是多少？',
                                  'contrast': '交换前后深度，结果和 alpha 如何变化？'},
                     'required': ['0.5', '0.25', '0.75'],
                     'rubric': 'Red-front yields (0.5,0,0.25), blue-front (0.25,0,0.5), both alpha '
                               '0.75. Distinguish front-to-back transmittance and back-to-front '
                               'source-over; define depth and stable ties. Center sort is not '
                               'exact for intersecting primitives.'},
 'tran15_03_precision': {'id': 'TRAN15-03',
                         'prompt': '少层透明在 RGBA8 上正常，128 层低 alpha 在同格式出现偏差，是驱动问题吗？\n'
                                   '对照变体：把中间格式换为支持混合的 FP16 后误差减小，能证明零误差或免费加速吗？\n'
                                   '请分别给出判断依据、能力与数据合同、同步/生命周期、回退和可执行验证；明确未执行项。',
                         'variants': {'primary': '少层透明在 RGBA8 上正常，128 层低 alpha 在同格式出现偏差，是驱动问题吗？',
                                      'contrast': '把中间格式换为支持混合的 FP16 后误差减小，能证明零误差或免费加速吗？'},
                         'required': ['量化|quant', '排序|sort', 'FP16'],
                         'rubric': 'Isolate source quantization, alpha representation/color space, '
                                   'ordering, per-layer attachment quantization and final display. '
                                   'FP64 oracle is semantic, not a bit-exact blend emulator. Query '
                                   'each use and preserve fixed tolerances and quality-matched '
                                   'measurement.'},
 'tran15_04_capability': {'id': 'TRAN15-04',
                          'prompt': 'independentBlend 和所需 MRT blend 格式均支持，如何配置 WBOIT '
                                    'accum/revealage？\n'
                                    '对照变体：设备缺 independentBlend 或其中格式不支持 blend 时如何合法回退？\n'
                                    '请分别给出判断依据、能力与数据合同、同步/生命周期、回退和可执行验证；明确未执行项。',
                          'variants': {'primary': 'independentBlend 和所需 MRT blend 格式均支持，如何配置 WBOIT '
                                                  'accum/revealage？',
                                       'contrast': '设备缺 independentBlend 或其中格式不支持 blend 时如何合法回退？'},
                          'required': ['independentBlend', 'reveal', '回退|fallback'],
                          'rubric': 'Specify accumulation clear zero additive ONE/ONE, revealage '
                                    'clear one with multiplicative destination '
                                    'ONE_MINUS_SRC_ALPHA, resolve semantics and finite '
                                    'denominator. Independently query format uses/features. '
                                    'Missing capability permits declared multipass or sorted '
                                    'fallback, never unconditional enable.'},
 'tran15_05_overflow': {'id': 'TRAN15-05',
                        'prompt': '有界 OIT 每像素和共享池容量足够，能否称其无条件精确？\n'
                                  '对照变体：局部像素层数或全局池超过容量时，如何计数并确定性拒绝或退化？\n'
                                  '请分别给出判断依据、能力与数据合同、同步/生命周期、回退和可执行验证；明确未执行项。',
                        'variants': {'primary': '有界 OIT 每像素和共享池容量足够，能否称其无条件精确？',
                                     'contrast': '局部像素层数或全局池超过容量时，如何计数并确定性拒绝或退化？'},
                        'required': ['容量|capacity', '溢出|overflow', '近似|approx'],
                        'rubric': 'Bound precision, depth ordering and retention capacity. Expose '
                                  'both per-pixel and global overflow; deterministic refusal or '
                                  'documented tail approximation. WBOIT is approximate even '
                                  'without capacity overflow; do not silently drop fragments or '
                                  'overwrite storage.'},
 'tran15_06_feedback': {'id': 'TRAN15-06',
                        'prompt': '折射 fragment 读取已完成 scene-color snapshot，输出到另一 image，需要什么依赖？\n'
                                  '对照变体：若采样和 attachment 写入同一 subresource，仅改 GENERAL 或任意 barrier '
                                  '能解决吗？\n'
                                  '请分别给出判断依据、能力与数据合同、同步/生命周期、回退和可执行验证；明确未执行项。',
                        'variants': {'primary': '折射 fragment 读取已完成 scene-color snapshot，输出到另一 '
                                                'image，需要什么依赖？',
                                     'contrast': '若采样和 attachment 写入同一 subresource，仅改 GENERAL 或任意 '
                                                 'barrier 能解决吗？'},
                        'required': ['GENERAL', 'COLOR_ATTACHMENT_OUTPUT', 'FRAGMENT_SHADER'],
                        'rubric': 'Default to separate resources or ping-pong with '
                                  'attachment-write to fragment-sampled-read dependency and legal '
                                  'layout. GENERAL and a barrier do not legalize feedback. '
                                  'Optional feedback needs exact feature, usage, state, layout and '
                                  'access semantics, not guessed extensions.'},
 'tran15_07_depth': {'id': 'TRAN15-07',
                     'prompt': '厚度使用已重建到同一坐标系的线性深度，怎样处理遮挡和屏外？\n'
                               '对照变体：换成原始非线性 depth 差，并改为反 Z 后还能沿用相同厚度吗？\n'
                               '请分别给出判断依据、能力与数据合同、同步/生命周期、回退和可执行验证；明确未执行项。',
                     'variants': {'primary': '厚度使用已重建到同一坐标系的线性深度，怎样处理遮挡和屏外？',
                                  'contrast': '换成原始非线性 depth 差，并改为反 Z 后还能沿用相同厚度吗？'},
                     'required': ['线性|linear', '反|revers', '屏外|offscreen'],
                     'rubric': 'Reconstruct actual projection/depth mapping and units; raw depth '
                               'difference is not physical distance. Front/back thickness or valid '
                               'surrogate must be explicit, clamp/reject negative or absent '
                               'intersections and fall back at offscreen regions; UV distortion is '
                               'approximate single-layer refraction.'},
 'tran15_08_volume': {'id': 'TRAN15-08',
                      'prompt': '均匀雾体 sigma_t 和总距离固定，使用步长 ds 积分透射率。\n'
                                '对照变体：步长减半、采样数加倍，怎样使浓度不漂移？\n'
                                '请分别给出判断依据、能力与数据合同、同步/生命周期、回退和可执行验证；明确未执行项。',
                      'variants': {'primary': '均匀雾体 sigma_t 和总距离固定，使用步长 ds 积分透射率。',
                                   'contrast': '步长减半、采样数加倍，怎样使浓度不漂移？'},
                      'required': ['exp', 'distance|距离', '步长|step'],
                      'rubric': 'T=exp(-sigma_t*distance), per-step alpha=1-exp(-sigma_t*ds), '
                                'accumulate premultiplied contribution and transmittance. Handle '
                                'final partial step; early termination needs an error budget '
                                'especially for HDR background. Do not double apply absorption or '
                                'equate sample count with density.'},
 'tran15_09_volume_order': {'id': 'TRAN15-09',
                            'prompt': '雾体完全位于透明表面前方，怎样合成？\n'
                                      '对照变体：雾体移到表面后方或穿过表面，仍固定雾最后一个 pass 是否正确？\n'
                                      '请分别给出判断依据、能力与数据合同、同步/生命周期、回退和可执行验证；明确未执行项。',
                            'variants': {'primary': '雾体完全位于透明表面前方，怎样合成？',
                                         'contrast': '雾体移到表面后方或穿过表面，仍固定雾最后一个 pass 是否正确？'},
                            'required': ['透射|transmittance', '分段|segment', '近似|approx'],
                            'rubric': 'Depth-relative integration is necessary. Explain front/back '
                                      'contributions, no repeated medium attenuation, segment '
                                      'intersecting media or declare single-dominant-layer '
                                      'approximation. Fixed pass order cannot solve arbitrary '
                                      'interpenetrating refractive/volumetric layers.'},
 'tran15_10_weather': {'id': 'TRAN15-10',
                       'prompt': '静态粒子和稳定相机有有效 history，如何避免软交界硬边？\n'
                                 '对照变体：粒子移动或相机突变且无可靠 MV 时，可否填零向量后强累积？\n'
                                 '请分别给出判断依据、能力与数据合同、同步/生命周期、回退和可执行验证；明确未执行项。',
                       'variants': {'primary': '静态粒子和稳定相机有有效 history，如何避免软交界硬边？',
                                    'contrast': '粒子移动或相机突变且无可靠 MV 时，可否填零向量后强累积？'},
                       'required': ['motion|MV', 'history|历史', '深度|depth'],
                       'rubric': 'Compare scene/particle linear depth for soft intersection, keep '
                                 'coverage and opacity separate. Track actual particle/camera '
                                 'motion, invalidate on cut or absent semantics and use reduced '
                                 'history/reactivity only where supported. Zero motion cannot '
                                 'fabricate validity; blur is not temporal correctness.'},
 'tran15_11_profile': {'id': 'TRAN15-11',
                       'prompt': 'PLY A 明确 scale 为 log、opacity 为 logit、rotation 为 wxyz，如何导入？\n'
                                 '对照变体：PLY B 使用线性 scale/概率 opacity/xyzw 和不同 SH 排列，字段同名可照搬吗？\n'
                                 '请分别给出判断依据、能力与数据合同、同步/生命周期、回退和可执行验证；明确未执行项。',
                       'variants': {'primary': 'PLY A 明确 scale 为 log、opacity 为 logit、rotation 为 '
                                               'wxyz，如何导入？',
                                    'contrast': 'PLY B 使用线性 scale/概率 opacity/xyzw 和不同 SH '
                                                '排列，字段同名可照搬吗？'},
                       'required': ['profile', 'SH', '拒绝|reject'],
                       'rubric': 'Require explicit field encoding, units/coordinates, quaternion '
                                 'order, SH order/normalization and generation. Normalize '
                                 'validated values, reject unknown/non-finite/invalid covariance '
                                 'or size. PLY is only a container; trained radiance cannot be '
                                 'relit as a BRDF without data.'},
 'tran15_12_footprint': {'id': 'TRAN15-12',
                         'prompt': 'Gaussian 中心在屏外但椭圆覆盖屏内，是否可剔除？\n'
                                   '对照变体：Gaussian 接近或跨越 near plane、投影极大时如何避免 NaN 和无界分配？\n'
                                   '请分别给出判断依据、能力与数据合同、同步/生命周期、回退和可执行验证；明确未执行项。',
                         'variants': {'primary': 'Gaussian 中心在屏外但椭圆覆盖屏内，是否可剔除？',
                                      'contrast': 'Gaussian 接近或跨越 near plane、投影极大时如何避免 NaN 和无界分配？'},
                         'required': ['footprint|覆盖', 'near|近裁', '有限|finite'],
                         'rubric': 'Use conservative finite-support bounds and actual '
                                   'covariance/projection, not center-only culling. Near-plane '
                                   'requires bounded fallback/clip strategy or explicit rejection '
                                   'with lost-content status, never arbitrary universal shrinking. '
                                   'Distinguish quad area, ellipse area and tile coverage.'},
 'tran15_13_sets': {'id': 'TRAN15-13',
                    'prompt': '只有一个 Gaussian 集合时材质 ID 选取正常。\n'
                              '对照变体：加入第二个 transform/材质不同的集合和 mesh 后，颜色 blend 正常是否证明 picked '
                              'ID/depth proxy 正确？\n'
                              '请分别给出判断依据、能力与数据合同、同步/生命周期、回退和可执行验证；明确未执行项。',
                    'variants': {'primary': '只有一个 Gaussian 集合时材质 ID 选取正常。',
                                 'contrast': '加入第二个 transform/材质不同的集合和 mesh 后，颜色 blend 正常是否证明 '
                                             'picked ID/depth proxy 正确？'},
                    'required': ['set', 'generation|代际', '材质|material'],
                    'rubric': 'Use stable (setID,localID,generation), transformed positions and '
                              'one documented visible-contributor policy for ID/depth '
                              'proxy/material diagnostics. Integer attachments do not alpha-blend. '
                              'A proxy is not opaque depth and cannot indiscriminately occlude '
                              'remaining transmission.'},
 'tran15_14_sort_cache': {'id': 'TRAN15-14',
                          'prompt': '相机、实例、时间、LOD 和所有资源都静止，可否重用排序？\n'
                                    '对照变体：相机不动但 Gaussian 动态参数、可见集合或资源代际改变，可否每 N 帧才重排？\n'
                                    '请分别给出判断依据、能力与数据合同、同步/生命周期、回退和可执行验证；明确未执行项。',
                          'variants': {'primary': '相机、实例、时间、LOD 和所有资源都静止，可否重用排序？',
                                       'contrast': '相机不动但 Gaussian 动态参数、可见集合或资源代际改变，可否每 N 帧才重排？'},
                          'required': ['generation|代际', '排序|sort', '失效|invalid'],
                          'rubric': 'Cache validity covers complete camera, transform, dynamic '
                                    'state, LOD, visibility/index construction and resource '
                                    'identity; static case can reuse with a proof. Relevant '
                                    'changes invalidate or require a declared error-bounded '
                                    'certificate, never unconditional fixed-frame reuse.'},
 'tran15_15_coverage': {'id': 'TRAN15-15',
                        'prompt': '优化点数减半且投影覆盖、重叠层数均下降，怎样验证收益？\n'
                                  '对照变体：另一个方案点数减半但剩余 splat 更大，是否能直接预测加速？\n'
                                  '请分别给出判断依据、能力与数据合同、同步/生命周期、回退和可执行验证；明确未执行项。',
                        'variants': {'primary': '优化点数减半且投影覆盖、重叠层数均下降，怎样验证收益？',
                                     'contrast': '另一个方案点数减半但剩余 splat 更大，是否能直接预测加速？'},
                        'required': ['覆盖|coverage', 'sort|排序', '测量|measure'],
                        'rubric': 'Measure project/sort/draw/resolve stages, clipped raster '
                                  'area/layer distributions and memory with matched quality. Fewer '
                                  'primitives can increase blend work. Label compute estimates, '
                                  'debug atomics and hardware counters separately; neither point '
                                  'count nor pixel estimate proves bandwidth or power.'},
 'tran15_16_background': {'id': 'TRAN15-16',
                          'prompt': '远背景低视差区域有大量冗余 Gaussian，可否合并或预合成？\n'
                                    '对照变体：相同操作用于前景轮廓、动态物体或有视差结构，怎样判断是否可接受？\n'
                                    '请分别给出判断依据、能力与数据合同、同步/生命周期、回退和可执行验证；明确未执行项。',
                          'variants': {'primary': '远背景低视差区域有大量冗余 Gaussian，可否合并或预合成？',
                                       'contrast': '相同操作用于前景轮廓、动态物体或有视差结构，怎样判断是否可接受？'},
                          'required': ['视差|parallax', '误差|error', '背景|background'],
                          'rubric': 'Gate background-only simplification on content and '
                                    'multiview/camera sequence evidence. Preserve silhouette, '
                                    'foreground, dynamics and parallax. Compare '
                                    'color/transmittance, popping, coverage, sort and memory, not '
                                    'universal parameter averaging or distance-only eligibility.'},
 'tran15_17_consumer': {'id': 'TRAN15-17',
                        'prompt': 'compute 只生成 indirect 参数，graphics 的消费同步怎么选？\n'
                                  '对照变体：compute 同时写 vertex shader 读取的 SSBO，单独 DRAW_INDIRECT '
                                  'barrier 是否覆盖属性？\n'
                                  '请分别给出判断依据、能力与数据合同、同步/生命周期、回退和可执行验证；明确未执行项。',
                        'variants': {'primary': 'compute 只生成 indirect 参数，graphics 的消费同步怎么选？',
                                     'contrast': 'compute 同时写 vertex shader 读取的 SSBO，单独 '
                                                 'DRAW_INDIRECT barrier 是否覆盖属性？'},
                        'required': ['DRAW_INDIRECT', 'INDIRECT_COMMAND_READ', 'VERTEX_SHADER'],
                        'rubric': 'Separate COMPUTE_SHADER/SHADER_WRITE to '
                                  'DRAW_INDIRECT/INDIRECT_COMMAND_READ from actual '
                                  'VERTEX_SHADER/SHADER_READ SSBO or '
                                  'VERTEX_INPUT/VERTEX_ATTRIBUTE_READ fixed fetch. Cross-queue '
                                  'semaphore and ownership depend on actual queues/sharing, '
                                  'retirement covers all consumers.'},
 'tran15_18_interlock': {'id': 'TRAN15-18',
                         'prompt': '设备支持 fragment shader interlock，是否无需深度排序即可得到精确透明？\n'
                                   '对照变体：设备不支持 interlock，基础 Gaussian/排序 blend 应当如何工作？\n'
                                   '请分别给出判断依据、能力与数据合同、同步/生命周期、回退和可执行验证；明确未执行项。',
                         'variants': {'primary': '设备支持 fragment shader interlock，是否无需深度排序即可得到精确透明？',
                                      'contrast': '设备不支持 interlock，基础 Gaussian/排序 blend 应当如何工作？'},
                         'required': ['interlock', '排序|sort', '回退|fallback'],
                         'rubric': 'Interlock protects conflicting fragment access within its '
                                   'defined scope; it does not magically produce geometric order. '
                                   'Use independent feature checks and supported raster sorted '
                                   'baseline without mandatory interlock/RT/mesh shaders; bound '
                                   'all advanced storage and precision.'},
 'tran15_19_views': {'id': 'TRAN15-19',
                     'prompt': '主视图移动但第二视图稳定，两者共享 Gaussian 数据，sort/history 如何分组？\n'
                               '对照变体：只销毁第二 Surface 或其中一个实例 generation 改变，是否必须重建所有设备资源？\n'
                               '请分别给出判断依据、能力与数据合同、同步/生命周期、回退和可执行验证；明确未执行项。',
                     'variants': {'primary': '主视图移动但第二视图稳定，两者共享 Gaussian 数据，sort/history 如何分组？',
                                  'contrast': '只销毁第二 Surface 或其中一个实例 generation 改变，是否必须重建所有设备资源？'},
                     'required': ['view|视图', 'generation|代际', '退休|retire'],
                     'rubric': 'Shared immutable data may persist while camera-dependent '
                               'sort/history are keyed by view/instance generations and actual '
                               'inputs. Invalidate affected scopes, retire only after all '
                               'consumers complete, avoid global device recreation for a surface '
                               'event or sharing stale view order.'},
 'tran15_20_measurement': {'id': 'TRAN15-20',
                           'prompt': '同设备同质量、分辨率和持续热状态下，排序与 draw p95 都下降，可以报告什么？\n'
                                     '对照变体：另一组删对象并冷机短测，FPS 更高，能推出原生帧提升和节电比例吗？\n'
                                     '请分别给出判断依据、能力与数据合同、同步/生命周期、回退和可执行验证；明确未执行项。',
                           'variants': {'primary': '同设备同质量、分辨率和持续热状态下，排序与 draw p95 都下降，可以报告什么？',
                                        'contrast': '另一组删对象并冷机短测，FPS 更高，能推出原生帧提升和节电比例吗？'},
                           'required': ['热|thermal', '质量|quality', '功耗|power'],
                           'rubric': 'Report controlled timing and uncertainty, cold/warm and '
                                     'p50/p95/p99 plus resource peaks; changed content is a '
                                     'separate experiment. Distinguish '
                                     'rendered/presented/generated frames and forbid '
                                     'power/bandwidth claims without matching instrumentation or '
                                     'desktop-to-mobile extrapolation.'}}
