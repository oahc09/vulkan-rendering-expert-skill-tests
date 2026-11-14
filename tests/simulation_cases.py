"""SIM16 private paired rubrics; not model context or executed Live evidence."""
SIM16_CASES = {'sim16_01_clock': {'id': 'SIM16-01',
                    'prompt': '应用60Hz呈现，绳索每秒更新60次，怎样定义时间输入？\n'
                              '对照变体：同一场景改为120Hz呈现且增加一个预览窗口，更新策略如何变化？\n'
                              '请分别分析实现合同、适用限制、回退与验证方法；未执行项明确标出。',
                    'variants': {'primary': '应用60Hz呈现，绳索每秒更新60次，怎样定义时间输入？',
                                 'contrast': '同一场景改为120Hz呈现且增加一个预览窗口，更新策略如何变化？'},
                    'required': ['tick|步长', '视图|view|owner'],
                    'rubric': 'Separate fixed simulation tick from render callbacks; one owner advances each '
                              'world, views only consume. Compare equal simulation ticks and timestamped '
                              'inputs at 30/60/120Hz; do not claim bitwise cross-device determinism.'},
 'sim16_02_backlog': {'id': 'SIM16-02',
                      'prompt': '前台偶尔出现小幅帧间隔抖动，如何安排仿真？\n'
                                '对照变体：后台停留40秒后恢复，如何处理累计时间和已有输入？\n'
                                '请分别分析实现合同、适用限制、回退与验证方法；未执行项明确标出。',
                      'variants': {'primary': '前台偶尔出现小幅帧间隔抖动，如何安排仿真？',
                                   'contrast': '后台停留40秒后恢复，如何处理累计时间和已有输入？'},
                      'required': ['droppedTime|丢弃', '暂停|pause', '上限|bounded|有限'],
                      'rubric': 'Specify bounded backlog/max ticks and explicit droppedTime. Default freeze '
                                'world time during pause, not a huge dt or unlimited catch-up; document '
                                'alternatives and reset input/time mapping on resume.'},
 'sim16_03_event': {'id': 'SIM16-03',
                    'prompt': '一次点击给粒子施加瞬时冲量，随后持续风力推动。\n'
                              '对照变体：两个view收到同一个eventId且每tick有4个substep，应如何消费？\n'
                              '请分别分析实现合同、适用限制、回退与验证方法；未执行项明确标出。',
                    'variants': {'primary': '一次点击给粒子施加瞬时冲量，随后持续风力推动。',
                                 'contrast': '两个view收到同一个eventId且每tick有4个substep，应如何消费？'},
                    'required': ['eventId', 'impulse|冲量', 'force|力'],
                    'rubric': 'Deduplicate eventId once per world/tick, not view or substep. Distinguish '
                              'impulse velocity jump from force integrated over time; resample timestamped '
                              'inputs, handle bounded queue overflow explicitly.'},
 'sim16_04_substeps': {'id': 'SIM16-04',
                       'prompt': '固定4个substep和8次iteration，compliance与damping怎样配置？\n'
                                 '对照变体：CPU等待GPU变慢，预算器把substeps从4降为1，这是否可直接上线？\n'
                                 '请分别分析实现合同、适用限制、回退与验证方法；未执行项明确标出。',
                       'variants': {'primary': '固定4个substep和8次iteration，compliance与damping怎样配置？',
                                    'contrast': 'CPU等待GPU变慢，预算器把substeps从4降为1，这是否可直接上线？'},
                       'required': ['compliance|柔顺', 'h|子步', '等待|wait'],
                       'rubric': 'Use actual h in alpha/h^2; changing substeps requires '
                                 'stability/material/input/damping validation. CPU completion wait is not '
                                 'kernel time; prefer validated tiers and timestamp queries with capability '
                                 'checks.'},
 'sim16_05_lambda': {'id': 'SIM16-05',
                     'prompt': 'XPBD在每个积分子步开始将lambda清零，并在8次iteration间保留。\n'
                               '对照变体：另一实现每次iteration前清零lambda，两者结果是否相同？\n'
                               '请分别分析实现合同、适用限制、回退与验证方法；未执行项明确标出。',
                     'variants': {'primary': 'XPBD在每个积分子步开始将lambda清零，并在8次iteration间保留。',
                                  'contrast': '另一实现每次iteration前清零lambda，两者结果是否相同？'},
                     'required': ['lambda|λ', 'iteration|迭代', '子步|substep'],
                     'rubric': 'Lambda accumulates within one substep, resets at each baseline substep. Show '
                               'alpha/h^2 and retained multiplier restoring compliance; warm start is '
                               'separate with timestep/material/topology invalidation, not automatic.'},
 'sim16_06_color': {'id': 'SIM16-06',
                    'prompt': '已验证同色距离约束不共享可写粒子，怎样并行？\n'
                              '对照变体：运行中增加一条边后同色约束共享粒子，原dispatch方案还能用吗？\n'
                              '请分别分析实现合同、适用限制、回退与验证方法；未执行项明确标出。',
                    'variants': {'primary': '已验证同色距离约束不共享可写粒子，怎样并行？',
                                 'contrast': '运行中增加一条边后同色约束共享粒子，原dispatch方案还能用吗？'},
                    'required': ['拓扑|topology', 'gather|着色|color', '写|write'],
                    'rubric': 'Validate writable vertex sets rather than constraint IDs. Topology '
                              'invalidates coloring; recolor with inter-color dependencies or use '
                              'per-constraint exclusive contribution slots and unique particle gather.'},
 'sim16_07_atomic': {'id': 'SIM16-07',
                     'prompt': '设备报告buffer float32 atomic add支持，求解器需要什么启用检查？\n'
                               '对照变体：另一设备仅有整数atomic，没有浮点加，怎样继续运行？\n'
                               '请分别分析实现合同、适用限制、回退与验证方法；未执行项明确标出。',
                     'variants': {'primary': '设备报告buffer float32 atomic add支持，求解器需要什么启用检查？',
                                  'contrast': '另一设备仅有整数atomic，没有浮点加，怎样继续运行？'},
                     'required': ['feature|能力', 'gather|着色|color', 'float|浮点'],
                     'rubric': 'Check exact storage domain, width and add feature queried and enabled, not '
                               'extension name alone. FP32 coloring or Jacobi+gather baseline requires no '
                               'float atomics; measure numerical differences before optional atomic use.'},
 'sim16_08_collision': {'id': 'SIM16-08',
                        'prompt': '短绳与静态球、平面和胶囊碰撞，如何验证投影？\n'
                                  '对照变体：碰撞器一帧移动超过自身直径，邻域列表还复用旧版本，能保证无穿透吗？\n'
                                  '请分别分析实现合同、适用限制、回退与验证方法；未执行项明确标出。',
                        'variants': {'primary': '短绳与静态球、平面和胶囊碰撞，如何验证投影？',
                                     'contrast': '碰撞器一帧移动超过自身直径，邻域列表还复用旧版本，能保证无穿透吗？'},
                        'required': ['穿透|tunnel', '子步|swept|连续', '邻域|neighbor'],
                        'rubric': 'Analytic projection is a discrete approximation, not universal continuous '
                                  'collision. Validate displacement/scale, bounded substeps or swept tests, '
                                  'invalidate stale neighborhoods and report overflow instead of silent '
                                  'truncation.'},
 'sim16_09_tail': {'id': 'SIM16-09',
                   'prompt': 'dispatch末尾有无效粒子线程，后续没有workgroup barrier，可怎样处理？\n'
                             '对照变体：同一kernel后续需要shared归约和统一barrier，尾线程处理有何不同？\n'
                             '请分别分析实现合同、适用限制、回退与验证方法；未执行项明确标出。',
                   'variants': {'primary': 'dispatch末尾有无效粒子线程，后续没有workgroup barrier，可怎样处理？',
                                'contrast': '同一kernel后续需要shared归约和统一barrier，尾线程处理有何不同？'},
                   'required': ['barrier', 'mask|掩码', 'shared|共享'],
                   'rubric': 'Bounds-check both variants; early return only where participation permits. For '
                             'shared/barrier path use active masks and neutral initialization with uniform '
                             'participation; query workgroup limits, never run deliberate deadlock tests.'},
 'sim16_10_global': {'id': 'SIM16-10',
                     'prompt': '单workgroup内交换shared数据，需要什么同步？\n'
                               '对照变体：网格跨多个workgroup且下一阶段读取所有上一阶段结果，原barrier是否够用？\n'
                               '请分别分析实现合同、适用限制、回退与验证方法；未执行项明确标出。',
                     'variants': {'primary': '单workgroup内交换shared数据，需要什么同步？',
                                  'contrast': '网格跨多个workgroup且下一阶段读取所有上一阶段结果，原barrier是否够用？'},
                     'required': ['dispatch', 'workgroup', '依赖|dependency|同步'],
                     'rubric': 'Workgroup barrier cannot synchronize an entire dispatch. Split global stages '
                               'into dispatches with proper resource dependencies; no busy-wait global '
                               'counter. Distinguish invocation/workgroup/dispatch/queue scopes.'},
 'sim16_11_cfl': {'id': 'SIM16-11',
                  'prompt': '均匀二维高度场使用显式中心差分波动模型，当前波速、dt和dx满足稳定条件。\n'
                            '对照变体：将波速加倍或dx减半后，怎样判断能否继续用原dt？\n'
                            '请分别分析实现合同、适用限制、回退与验证方法；未执行项明确标出。',
                  'variants': {'primary': '均匀二维高度场使用显式中心差分波动模型，当前波速、dt和dx满足稳定条件。',
                               'contrast': '将波速加倍或dx减半后，怎样判断能否继续用原dt？'},
                  'required': ['CFL|稳定', 'dx', 'clamp|截断'],
                  'rubric': 'For stated linear stencil evaluate c*h*sqrt(1/dx^2+1/dy^2)<=1 with safety '
                            'margin, revalidate damping/boundaries. Reject invalid configuration instead of '
                            'height clamp; not a universal fluid theorem.'},
 'sim16_12_normal': {'id': 'SIM16-12',
                     'prompt': 'height和normal来自同一tick，水面显示正常。\n'
                               '对照变体：normal生成落后一个tick但画面仍平滑，是否能发布并通过验收？\n'
                               '请分别分析实现合同、适用限制、回退与验证方法；未执行项明确标出。',
                     'variants': {'primary': 'height和normal来自同一tick，水面显示正常。',
                                  'contrast': 'normal生成落后一个tick但画面仍平滑，是否能发布并通过验收？'},
                     'required': ['snapshot|快照', 'tick', '数值|numerical'],
                     'rubric': 'Publish height and normal with matching tick and generation completion; '
                               'reject mixed snapshots. Zero field, impulses, boundaries and numerical error '
                               'are independent of shading; heightfield cannot represent overturning or full '
                               '3D fluid.'},
 'sim16_13_retire': {'id': 'SIM16-13',
                     'prompt': '单consumer已经完成读取仿真输出，何时可以复用？\n'
                               '对照变体：新增第二view和shadow异步读取，两个ping-pong buffer是否仍足够？\n'
                               '请分别分析实现合同、适用限制、回退与验证方法；未执行项明确标出。',
                     'variants': {'primary': '单consumer已经完成读取仿真输出，何时可以复用？',
                                  'contrast': '新增第二view和shadow异步读取，两个ping-pong buffer是否仍足够？'},
                     'required': ['consumer|消费者', '完成|completion', '回收|retire|复用'],
                     'rubric': 'Track all actual consumer completions including view/shadow/optional AS; '
                               'double buffering alone proves nothing for multi-frame flight. Surface '
                               'destruction retires its references, not shared world or unfinished '
                               'consumers.'},
 'sim16_14_history': {'id': 'SIM16-14',
                      'prompt': '常规变形每帧更新position、normal、bounds和运动向量。\n'
                                '对照变体：发生teleport或拓扑重建，上一子步位置能否直接作为上一呈现姿态？\n'
                                '请分别分析实现合同、适用限制、回退与验证方法；未执行项明确标出。',
                      'variants': {'primary': '常规变形每帧更新position、normal、bounds和运动向量。',
                                   'contrast': '发生teleport或拓扑重建，上一子步位置能否直接作为上一呈现姿态？'},
                      'required': ['history|历史', 'bounds|包围', 'generation|代际'],
                      'rubric': 'Previous displayed pose is per-output history, not previous solver substep. '
                                'Invalidate correspondence on teleport/topology/LOD, publish conservative '
                                'bounds and matching geometry generation; optional AS update requires legal '
                                'invariants and synchronization.'},
 'sim16_15_queue': {'id': 'SIM16-15',
                    'prompt': '仿真compute与graphics在同一queue，如何表达数据交接？\n'
                              '对照变体：改成独立queue或不同queue family，哪些同步和ownership要求会变化？\n'
                              '请分别分析实现合同、适用限制、回退与验证方法；未执行项明确标出。',
                    'variants': {'primary': '仿真compute与graphics在同一queue，如何表达数据交接？',
                                 'contrast': '改成独立queue或不同queue family，哪些同步和ownership要求会变化？'},
                    'required': ['semaphore|信号量', 'ownership|所有权', 'queue'],
                    'rubric': 'Select stages/access by actual vertex fetch, shader, indirect or AS consumer. '
                              'Same queue barriers differ from cross-queue semaphore dependency; exclusive '
                              'cross-family resources need release/acquire ownership, concurrent sharing '
                              'differs. Async is measured optional optimization.'},
 'sim16_16_mobile': {'id': 'SIM16-16',
                     'prompt': '桌面演示高FPS、float atomic与FP16均可用，能得出哪些结论？\n'
                               '对照变体：手机持续运行后限热且无这些可选能力，怎样保持正确性并比较性能？\n'
                               '请分别分析实现合同、适用限制、回退与验证方法；未执行项明确标出。',
                     'variants': {'primary': '桌面演示高FPS、float atomic与FP16均可用，能得出哪些结论？',
                                  'contrast': '手机持续运行后限热且无这些可选能力，怎样保持正确性并比较性能？'},
                     'required': ['FP32', '热|thermal', '未验证|未执行|unverified'],
                     'rubric': 'No desktop-to-phone extrapolation. Preserve FP32/no-atomic/single-queue '
                               'baselines and validated quality tiers, record fixed solver/visual workload '
                               'and thermal duration; distinguish CPU wait, GPU timestamps, full frame cost, '
                               'device evidence and unexecuted paths.'}}
