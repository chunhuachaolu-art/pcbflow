# -*- coding: utf-8 -*-
"""L7 走廊执行器（V5.0-DEV-TASKBOOK §4 L7；P4 第⑤路交付）。

入口 execute_candidate(board, candidate, out_dir=None)：
  逐网按 candidate.route_order 执行 → routes（v5.routes.v1 工件）→
  route_check.check_routes 全量自检（A9：判定全出自 v5.drc）→
  {"verdict": "ROUTED"|"FAILED", "routes": 工件|None, "per_net": [...],
   "negotiation_log": [...]}。

执行形态（任务书 L7 行：ribbon 整体 / pour / 回流针对 / 单线 A*；协商兜底；
staging+rollback）：
- **ribbon 整体（R3 不可拆分）**：带 geometry.copper_band 的分区 = 已声明整体铜带，
  直接产出 ribbon entry（中心线+铜带宽/声明占用），不做 A*；工件顶层 ribbon_groups
  披露（net_ids/occupancy_mm/route_index）。与既布（ptype=="ROUTED"）分区同属
  fixed-shape：其铜在 route_check 场景中映射到板内固定铜（同一物理铜，不双计容量）。
- **pour**：demo 板无用例，留接口位——分区 geometry.pour 矩形照常 A* 布其端点连线，
  工件顶层 pour_regions 披露矩形（专项测试以构造板驱动）。
- **单线 A***：网格化板面（0.25mm 栅格、8 连通、多信号层），障碍 =
  禁布区（R6，逐段 bbox 间隙 >0，与 route_check 的 R6 逐段精查同口径）+ 既布铜/
  已布网膨胀（R5 净距，中心线口径与 v5.drc 一致）+ 敏感区 R2（两档保守引导，
  见下）+ 走廊容量账本（逐走廊×层，占满即封）。层间过渡 = 过孔（记
  transition_vias；每孔配回流孔 ≤ R4.max_distance_mm）。无随机、heapq 计数器
  tie-break，确定性。
- **宽度**：电流分区取 R1 保守下限（v5.metrics.width_prior.conservative_min_width），
  其余取分区 planned_width；统一夹入 width_prior 区间（区间矛盾 fail-closed）。
- **每网 staging 事务**：_NetTransaction 复用 v5.staging.StagingTransaction 语义
  （staging 暂存 → 网级 v5.drc 门校验 → 一次性 commit 生效 / rollback 无残留、
  提交后不可变；未提交的 staging 弃置不触状态）。网内失败→回滚该网→协商兜底
  （确定性尝试阶梯：R2 档位让位 near→overlap_free / 去层偏好 / 免过孔费 /
  换 lane=栅格相位偏移）→仍失败→整体 FAILED 且 routes=None（已成功网保持在
  上一致态，不随失败网回退；回滚后状态指纹断言逐字节一致）。
- **out_dir** 给定时：routes 工件经 v5.staging.StagingTransaction 原子落盘
  （staging→os.replace 提交；FAILED 无工件不落盘——sidecar 卫生 §3.5）。

R2 的两档保守引导（v5.drc.check_ana_proximity 是**路径级**规则：折线最近段距
< min_distance 时对整条折线全部水平/垂直段累计投影重叠，> max_parallel 判违例；
路径级累计无法用逐边局部判定表达）：协商阶梯以两档保守边规则引导 A*——
"near"（近距且有投影重叠才封，多数网直达近优）与 "overlap_free"（有投影重叠
即封，累计恒 0）；两档被接受的路径其累计平行长度恒 ≤ max_parallel，真实判定
由网级 v5.drc 门（check_all 内 check_ana_proximity）对每条尝试的实际铜审计，
终检在 route_check（A9）。代价披露：近锁网在 overlap_free 档可能走斜角阶梯
绕行（目标值劣化，无目标值门；DRC-clean 与确定性是 P4 合同）。

容量按「边进入走廊矩形即计入该走廊×层」的边级保守预留（与 route_check 的
整 run 计入同向，宁可错封不放行）；既有占用含条目间距（与
v5.metrics.capacity.corridor_occupancy 同式）。

多段表示合同（与 route_check.validate_routes 同锁）：换层网 = 同 net_id 多条
entry（每层一段 run），首 entry 首点 = 分区端点、末 entry 末点 = 另一端点，相邻
entry 在过渡孔点衔接且双方 transition_vias 均披露该点；单层网 = 单 entry。
DIFF 等「两网同分区」：两网各一条独立 A* 路线，执行器强制对腿 R5 净距（共享端点
的入边邻域豁免）；route_check 侧同分区 R5 对在归责层豁免（见 route_check docstring）。

升级件④（2026-09-14，真实板健壮性；DISPATCH-LOG P5② 三类失败模式）：
- **模式A 退化分区合同（主审钉死，照实现）**：两端点重合的退化分区（adapter 对
  单 pad 网的既定抽象，kicad_adapter note "…coincident endpoints (degenerate)"）
  = **trivially satisfied**——executor 产出零长 route 条目（polyline=[pt,pt]、
  层=候选指派层、无 transition_vias/return_vias、宽度=planned_width），
  negotiation_log 记 "degenerate: zero-length partition trivially satisfied"；
  条目仅作工件声明（零铜展宽）：不入障碍/容量账本，route_check.build_scene
  对零长 polyline 同规则跳过（零铜=无间距交互；非退化分区的零长 entry 仍被
  validate_routes 链审计拒绝——首末点须为两个不同端点）。
- **模式B/C 尝试阶梯（每网确定性计划序，每次尝试策略入 negotiation_log）**：
  阶段1 基线栅格（0.25mm）× 5 变体（现行行为，位 1..5，日志格式不变）；
  阶段2 细化栅格 0.125mm × 5 变体（模式B 栅格分辨率根因：薄门/窄走廊的
  中心线窗口宽 <0.25 且 ≥0.125 时基线无路、细化可布——见 d4-tight-door/
  d4-escape-seal D 层夹具）；阶段3/4 逃逸阶梯（基线/细化栅格各一轮：起点
  先、终点后；半径渐进 1→2→3 格；每半径内 4 向先、对角后；变体固定取
  最宽容 no-prefer/overlap_free/via-free）。标签：非基线尝试在 variant 后
  追加 " pitch=<p>"（scale≠1）与 " escape=start|goal:(dx,dy)r<k>"；吸附
  等价的计划（同 scale/起终点节点/变体）去重跳过、不计 attempts。全部尝试
  失败时追加一行 "exhaustion-cause=<分类>"（endpoint-sealed / capacity-locked
  / sensitive-crossed / obstacle-dense，确定性几何检查、R2 不参与）。
- **几何二级归因披露行（0.6.1，V5-SMALLWAVE A3，log-only）**：每条
  exhaustion-cause 行后追加一行 "geom-secondary=fixed-copper-sealed|open"——
  失败网两端点 r0/r1 出边密封普查、阻塞源仅计板固有固定铜（DIAG-FAILED8
  证据：ripup-exhausted 字面易误读为 rip-up 深度不足，4/4 实为板固有焊盘场
  封死）。诊断披露件：不改任何路由决策/序/尝试阶梯（失败已定局后追加）。
  **不放松任何硬规则**：R1/R2/R5/R6 判定路径零改动，容量不松弛，层指派保持
  软先验；细化/逃逸只扩大搜索空间，不放宽任何边的合法性谓词。
- **模式C 边界**：本件只做「逃逸尝试策略」（重吸附 + 阶梯），不改焊盘几何
  模型（焊盘物理铜入模归升级件①）。

升级件①（2026-09-14，出口合同升级 D1-D4；docs/up1-exit-contract-design.md）：
- **D1 焊盘铜入占用**：**真实**端点焊盘铜（pad_terminals，adapter 落键；
  route_check._fixed_coppers 场景侧同源）随固定铜进 obstacles——他网焊盘=
  障碍（R5 按铜形），本网焊盘=合法连接（net 跳过）。隐式 anchor（无
  pad_terminals 的合成板端子抽象）**不入 v5 障碍**（导出器按该网 route
  entry 层落画；合成板端点邻域常有既布铜贴行，抽象铜入障碍会封死端点——
  文档化决定，见 route_check docstring）。同分区豁免区半径从「R5+1 格」
  扩到「max(R5, 端点焊盘半尺寸+R5)+1 格」：多网共分区的端点焊盘几何重合，
  两腿须经共享端子区（焊盘+R5 光晕）进出——扩的是抽象固有影子区，他网
  （异分区）铜不受豁免。
- **D2 孔铜入占用**：过孔铜形=圆（半径=drill/2+annular，板 via_model 缺省
  0.3；kicad_export.via_model_params 唯一推导口）。A* 换层边的孔位须过
  _via_ok：R6 禁布 + **对异网铜 R5 且无同分区豁免**（钻孔穿他网铜是制造
  违例，抽象豁免只及铜不及孔）+ 对全部既有孔点 ≥ 2·孔半径+R5（孔-孔最小
  孔心距）。commit 后孔点入 ctx.via_points 供后续网核对。
- **D3 孔错位**：回流孔位与同网孔点（含其过渡孔）最小孔心距 = 2·孔半径+
  R5.min_clearance_mm（_return_via_offsets 栅格环序确定性展开，≤R4 上限）；
  每网 commit 行披露 via-plan（孔数/错位决策）。
- **D4 全程折线+双侧相连**：折线焊盘心→焊盘心（端点贴回既有合同）；过孔
  落折线顶点；**回流孔以 [T,R,T] 桩段入相邻两层 entry**（R 为折线顶点、
  两侧相连=无悬空；单点 stub 层提升为 [T,R,T] entry 保证 F.Cu 侧也有铜）。
  桩段按边合法性核对（R5/R6/容量，严格档失败再试同分区豁免档）。
- **端点层约束**：首/末 run 层须 ∈ 端点焊盘层集合（**仅显式 pad_terminals**；
  无 pad_terminals 的端点不约束——隐式 anchor 随 route 层走，见 kicad_export；
  焊盘层缺席该端点项 → 不约束）——A* 起种于焊盘层、goal 弹出仅收焊盘层；
  层不符时经端点过孔换层（同网孔穿自网焊盘，kicad 实测不报 hole_clearance）。
- **④对账（文档化决定，主审建议采纳）**：退化分区零长 route 仍零铜声明，
  焊盘铜（真实 pad_terminals 或无）以固定铜入场景，二者并存不冲突——
  零长条目不构造 route 铜（无间距交互），焊盘铜独立参与场景；带真实
  pad_terminals 的退化分区其焊盘铜照常入场景（他网障碍）。

升级件⑤（2026-09-14，F12：executor-孔协调缝修复 + 回流孔安置扩容；
A 层真实板 0/7 SAT 归因 out/v5-p5/trial/final-g1-assessment.md）：
- **F1 缝修复（走线↔他网已提交孔铜）**：edge_blocked 栅格障碍模型补入全部
  已提交**他网**过孔铜圆盘（半径=via_model 推导口，缺省 drill/2+annular
  =0.3，与 route_check D2 场景 _via_coppers 同源），按 R5 中心线口径
  （pad_segment_distance−via_r < R5）封边——此前障碍只含他网走线/焊盘铜，
  先布网的孔（transition+return 提交进 ctx.via_points）只在放置新孔时经
  via_blocked 核对、从未入后续网走线的障碍栅格，后网走线穿孔铜 R5 邻域被
  final route_check 实抓（badgeleds-do-electronics / pmod-bme280 根因）。
  孔铜跨全信号层（场景侧逐层一枚，不按 layer 过滤）；**同网已提交孔=合法
  连接点不入障碍**；同分区豁免与折线障碍同口径（仅共享端点豁免区入边；
  归责层 route_check 同分区豁免覆盖该对）。反方向（先孔后线）已由 D2
  via_blocked 对他网铜 R5 **无同分区豁免**闭合（①件），本件以测试钉住。
  耗尽归因补 via-obstacle-sealed 类：直连段穿他网已提交孔铜 R5 邻域
  （无绕行空间场景的确定性归因串，含 via 障碍字样）。
- **F2 回流孔安置扩容**：_return_via_offsets 枚举域扩容、约束一律不放松——
  半径按 pitch/2（0.125mm）细步进（向 R4 上限渐进）、方向 8→16（轴向/对角/
  马步三族：马步 ±(2,1)/±(1,2) 补齐轴向↔对角之间的两侧角域，即双侧锚点
  偏移备选面）；确定性全序（距离, 家族序, 方向序）不变；旧枚举域是新域
  子集（D3 ≥2r+R5、R4 ≤max_distance_mm 零放松）。真实板 pmod-i2c24io
  「错位+双侧相连约束下无有效位」（36 网布通后 /SDA 106 attempts 全耗尽）
  在扩容域内重搜。

升级件⑤-F4（2026-09-14，引擎搜索能力三件；F1/F3 之上的 ⑤ 收口。四类真实
失败签名 out/v5-p5/trial/final-g1-assessment.md 只读归因：stm32 首栅格部分
段被封、atmega 端点吸附出边全封、dc-scm 稠密多焊盘网首网耗尽、m2-pcie
/PWRGD 耗尽）。核心原则（④先例）：**扩的是合法搜索空间，硬约束一律不可
松弛**（R5/R6/R4/D3/容量/敏感区公式与判定路径零改动）：
- **F4a 细化层级扩展**：尝试阶梯追加 0.0625mm 细档（scale=0.25）——阶段序
  追加在既有阶段之后（基线→0.125 细化→逃逸×2→**新 0.0625 细化→新 0.0625
  逃逸**），既有位 1..10（基线 5 + 0.125 细化 5）逐位不动（④钉「attempt6
  细化 0.125 过门」零翻转）；**总预算确定性再分配保持 106/网**：既有两个
  48 计划逃逸块各修剪为 40（r3 大位移档 8 向→4 轴向——大位移粗定位，对角
  增量留给 r1/r2 细档；保留计划相对序不变），腾出的 16 槽 = 新细化 4 计划
  + 新逃逸 12 计划。新细化档取前 4 变体（不含 lane-shift——0.0625 栅格上
  半格相位 0.015625mm 属亚栅格噪声，R2 档位/层偏好/过孔价三轴多样性保留）。
  细档搜索为**确定性限域窗口**（_fine_window：直连端点+本尝试锚点 bbox 外扩
  1.0mm；栅格相位仍锚定工作区原点=同一 lattice 子矩形，窗口外邻边剪枝、
  边合法性谓词零改动）——细档价值在端点/薄门局部缝隙（四类真实签名），
  全板细搜与粗档全板阶梯冗余且单 attempt 代价 16×（20mm 板实测 ~33s），
  窗口外路径由粗档全板计划覆盖（运行时守门红线）。
- **F4b 逃逸强化**：端点吸附出边全封（atmega 签名）与首栅格部分段被封
  （stm32 签名）两类失败面由细档逃逸重锚扩张——新逃逸档以 0.0625mm 位移
  粒度枚举端点邻域重吸附候选（起点侧 r1×8 向全、终点侧 r1×4 轴向，确定性
  方向序），逃逸×细化交错（细档逃逸计划本身就是 0.0625 栅格上的整网 A*，
  追加在细化档之后成组执行=④「环封下纯逃逸不可达、主解=细化穿薄门」方向
  的落实）；对角逃逸向在 r1/r2 全档保留。
- **F4c rip-up-and-retry（有界、确定性）**：网 N 在当前候选内耗尽全部
  attempts 后：确定性选定阻塞集（已布 A* 网按**提交序**、其铜落入 N 失败
  走廊——直连段 (width/2+R5) 带或端点逃逸邻域 (reach+R5) 盘——者；贪心
  逐网独立入选、提交序决胜）→ ctx 快照（既有 snapshot/restore，本件升级为
  列表副本恢复——rip 收缩列表截断不可逆）→ rip
  （ctx.rip_net：铜/条目/孔点/账本重建，fixed-shape/退化条目不参与）→
  N 以 fresh 106 阶梯重布 → 被 rip 网按原提交序以 fresh 计划**前缀 20**
  （_RIPUP_REROUTE_MAX_PLANS：重布语义=障碍超集下恢复既有布线的有界协商
  重搜；N 本网重布保持完整阶梯）重布；任何重布失败 → 回滚 rip 前快照并
  进入下一轮（逃逸邻域 reach 随轮次 ×round 放宽）。
  预算：每网 ≤2 轮、每候选全局 ≤8（常量披露于下）；全部 rip 事件逐条入
  negotiation_log（ripped 谁/为何/重布结果；**只增行不改行**——下游
  build_g1_assessment.py 按 "FAILED after N attempts"/"exhaustion-cause="
  等串解析，既有行格式逐字节兼容）。新耗尽归因类 ripup-exhausted /
  ripup-reroute-failed（+cause）扩展 exhaustion-cause 分类序（进程类，几何
  细节保留在 ripup 事件行）。rip-up 触发为耗尽后无条件（有界），阻塞集为
  空（无已布网可 rip）时零开销直落原归因。

V5-R2（2026-09-24，rip-up 有界深化+导引通道接线，任务书
V5-R2-RIPUP-DEEPEN-GUIDE-TASKBOOK-2026-09-24.md；0.6.1→0.7.0）：
- **W-1 有界参数深化**：每网轮 2→5、每候选全局 8→12、被 rip 网重布前缀
  20→30（后二者带值扫描候选，缺省待主审 LEAD-REVIEW 复核裁定）；三值+
  探针预算 B=3+联合因子 2+导引开关全白名单化 execute_candidate(
  ripup_params=...) 可配（board/任务级；_RIPUP_PARAM_KEYS；fail-closed 校验）。
  逃逸邻域 reach 0.75 不动。
- **W-2 阻塞集联合重排**：_ripup_blocker_ids 选择器升级——候选阻塞集=
  当前阻塞者（F4c 命中语义不变）∪上位替代者（与 hit 段重布走廊
  (width/2+R5) 交叠的已布网）；联合评估 vs 逐个贪心：纯整数评分
  cost(w)=该网铜段数（重布工作量代理，无浮点环境差），启用判据
  score(joint) ≤ joint_factor×score(greedy)（护栏=2）；确定性冻结=全部
  集合迭代 sorted()、tie-break=（联合评估分，网 id 字典序）（F4c 原提交序
  决胜废止——0.7.0 行为差异披露）。joint_factor=0 可退化为纯贪心。
- **W-3 波次导引接线（v5.guide/0.1.0 新件）**：被 rip 网重布序=波次通道
  展开（EXP-S2 主选：7/8 闭环 1.0）——空间 x 带连续分波（k 冻结规则
  <3 网→1、3–4→2、≥5→3；块内 id 字典序）；档位通道（宽度三档 tier，
  序=(tier,id)）仅重布集 ≤12 网时作次选展开（EXP-S2 n16 档位崩塌在案）。
  guide=False（对照臂）退化=联合重排入选序。展开去随机化，一切集合/
  字典遍历 sorted() 后使用（字节等门前提）。导引=纯排序自由度，
  **A* 搜索语义与成本函数内核零改动**（非目标红线）。
- **W-4 victim 定向探针**：被 rip 网重布失败（victim）时对阻塞集邻域发
  定向探针——交换 victim 在当前序中的邻位（step 冻结序 +1/−1/+2，取前
  B 个），一次交换序测量=该交换序下全量 rip+重布试跑（事务回滚）；探针
  结果逐条入 negotiation_log（probe 行）。S2 结论=约束在提案质量非预算，
  B=3 缺省、批内可扫 3/5。N 本网重布失败与序无关（同集确定性）不探针。
- negotiation_log 新增行族（只增不改）：guide-order 行 / probe 行 /
  committed 行尾 channel 披露；既有行格式（"FAILED after N attempts"/
  "exhaustion-cause=" 等解析串）逐字节兼容。

⑥波 D6-3（2026-09-17，板边距入 v5 世界模型；合同 V5-P5-WAVE6 §2 D6-3，
0.4.0→0.5.0）：
- **障碍栅格加入板边禁布带**：workspace 内缩 EDGE_CLEARANCE_MM（0.2mm =
  kicad-cli 生效缺省 copper_edge_clearance；board.json 现无显式边距规则
  字段——考证披露于 drc.py）的环带入 edge_blocked 与 via_blocked 障碍
  （全信号层同带、**无豁免档**；内矩形凸 ⇒ 段触带 ⟺ 端点触带，逐点 O(1)
  判定，①族式障碍注入同口径）。带值/轮廓源单源=v5.drc.edge_inner_rect
  （轮廓唯一源=workspace 矩形，board.py:40-45 校验、kicad_export.py:698
  同源转录，禁第二轮廓源），与 route_check edge_violations / drc
  check_edge_clearance 同一带同口径。**只紧不松**：R1/R2/R5/R6/容量/敏感
  判定路径零改动，禁布带是新增空间约束——此前「合法贴边」自 ⑥ 起拒布
  （对应 kicad-cli copper_edge_clearance 判边距的世界模型补全）。
- **exhaustion 归因词表增 edge-clearance 类**：端点入带即归（分类序首位——
  带内端点 sealed 同真但根因是带，先判防遮蔽；见 _exhaustion_cause
  docstring）。
- **板固孔禁布带（V5-D8，2026-09-22，0.6.0）**：board.holes[]（adapter D8
  全量落键：全部 TH/NPTH pad 钻孔**不分网**、oval=保守外接圆 max(a,b)）入
  障碍栅格——via_blocked 对全部板固孔**零豁免**（心距 < r_hole+0.25+via_r
  拒；kicad hole_to_hole 同网不豁免，wave6 14 条 C 类 genuine 全为引擎过孔
  vs **同网**板固 PTH=本带闭合的差口）；edge_blocked 对走线段判
  r_hole+0.25+width/2，**端点豁免**=孔心与本分区端点重合（走线连自身端点
  焊盘孔=合法铜连接，kicad 同网铜-孔豁免族；世界模型无孔网信息，端点豁免
  =最近似——同网非端点孔仍拦走线=保守方向，PREREG-D8 §2.4 披露）。带值
  单源=v5.drc.HOLE_TO_HOLE_MM 0.25（与 route_check/drc 同带同口径；判式用
  via_r≥kicad 钻半径=单向保守 0.15mm 豁免带宽）。holes=[]（旧世界板/合成
  板）新路径全短路=行为与 0.5.0 逐位一致（向后兼容）。exhaustion 归因词表
  增 hole-keep-out 类（分类序=edge-clearance 之后：带类）。
- **边界（披露）**：fixed-shape（ribbon/既布）与退化分区的板声明铜不经 A*，
  不因入带被 executor 拒布（板数据固有态，v5 不可移铜）——由 route_check
  edge_violations 如实披露、D6-4 分类器同位归责；焊盘铜贴边同口径（v5
  边距带为中心线口径，物理铜缘口径差不在执行侧建模，残差归 D6-4 披露）。

V5-EXECUTOR-0.13.0（2026-10-23，引擎吞吐阶段二＝FX-3 乐观可达性预检，
engine-fix-r1；用户裁决「两阶段修」第二步。诊断依据=
out\\throughput-diag-r1\\THROUGHPUT-DIAG-REPORT-2026-10-23.md §5 FX-3：
FAILED 族每网 2×106 计划全图穷举、逃逸计划占 87%）：
- **escape-only 门**：仅逃逸计划预检——直连计划与 attempt=1 成功网
  零接触零回归（r21 型单 attempt 板不受累）。
- **族级一次多源 BFS**：当前栅格族全部逃逸计划锚点并源，穷尽得乐观
  连通分量；计划短路 ⟺ 其目标锚 ∉ 分量（O(1)）。早退=族内全部目标
  可达 → 本族零短路。缓存 ctx._relaxed_cache 与 FX-1b 族清/finally 同步。
- **健全性**：乐观图边集 ⊇ 精确 A* 图（节点封锁仅计最宽容精确配置下
  必然全邻边封锁的源；R2/容量/窗口/目标层/via 严格性一律不建模）；
  乐观不可达 ⟹ 精确不可达；短路行与 A* 耗尽行逐字节相同。
- **验收**：ROUTED 板全量字节等（含 negotiation_log）；FAILED 板终态面
  全等（verdict/per_net/status/first_fail）；crossproc 双跑全等——
  见 out\\engine-fix-r1\\FX-STAGE2-REPORT-2026-10-23.md。

V5-EXECUTOR-0.12.0（2026-10-23，引擎吞吐阶段一＝纯等价提速，engine-fix-r1；
用户裁决「两阶段修」第一步。诊断依据=out\\throughput-diag-r1\\
THROUGHPUT-DIAG-REPORT-2026-10-23.md：edge_blocked 调用树占 CPU 62-70%、
GRID 预选族 32-48%、FAILED 族每网 2×106 计划全图穷举）：
- **FX-1 梯内判定 memo**：_run_attempt_ladder 作用域内（场景冻结＋
  net_id/pid/width 恒定）对 edge_blocked/via_blocked 结果按判定实参键 memo
  （同键必同值=纯 memo，行为字节等）；包装器带激活三元组比对健全性双保险，
  finally 保证任何路径关闭；容量帽防大板细栅格无界膨胀（达帽停登记、
  既有键继续命中）。
- **FX-2 微优化三连**：①D8 孔端点豁免按 pid 预计算（容差语义逐字保留）
  ②_grid_query 单格快路（格内列表天然升序，免 set+sorted）③_r2_edge_blocked
  无敏感区短路（原循环零迭代恒 False）。
- **红线保持**：A* 搜索语义/成本函数/计划阶梯/协商日志行格式/R 规则判定
  路径零改动；一切改动为等价重构（逐条注记在代码内）。

V5-EXECUTOR-ENG-R1（2026-10-02，构造性无解快速失败短路+终态口径收口，
任务书 TASKBOOK-V5-EXECUTOR-ENG-R1-2026-10-01.md；判据/白名单冻结件=
out/v5-p5/exec-eng-r1/PREREG-EXECUTOR-ENG-R1.md；设计定案=同目录
DESIGN-DECISION.md；0.8.0→0.9.0）：
- **W-1 SC-1 事前短路（sealed-short-circuit）**：execute_candidate 入口
  （合同校验后、任何阶梯之前）对 ladder-bound 分区逐端点做附着闭包
  S(e)=S_grid(e)∪{端点精确坐标} 全层密封普查——封锁源只计 fixed: 前缀
  ∧异网∧异分区铜（fixed 铜全集=焊盘铜+ribbon 铜带+既布折线，宽于
  PREREG 类名字面的 all-layer-pad-seal 焊盘族，健全性成立：三者皆板固有、
  rip_net 摘除面外），谓词 ob.distance_blocked(p,p,R5−EPS) 与 edge_blocked
  同源同值；S_grid=阶梯全部计划（_attempt_plans）的吸附锚点节点集，与
  阶梯消费同一 helper（_escape_anchor 单一位移事实源，纯等价重构），
  精确坐标项=M3 直连/胶合附着（工件折线电气附着终点恒为原始端点精确
  坐标——V1 闭包缺此项即误杀，对抗板 fixture 钉死）。某端点 S(e) 全
  (p,层) 封死 ⇒ cross-check（ctx.edge_blocked 生产谓词、最宽豁免档）
  逐对复核，全同意 → FAILED 阻断终态（attempts=0、exhaustion-cause=
  sealed-short-circuit 新类、证据链五行入 negotiation_log、per_net 条目
  键集与穷举失败条目同构）；任一不同意 → 弃权不短路（宁漏判不误杀，
  mismatch 披露行入 log）。**零触发=零 log 增量**：判定纯内存读数，
  非密封板 negotiation_log 与 0.8.0 逐字节相等。判定世界=入口天然
  fixed-only 最弱世界（route_coppers/via_points 俱空）；封锁对障碍集
  单调 ⇒ 一切可达世界成立。单端点封死即充分；多密封板指认=route_order
  序首命中（确定性）。**宽度口径注记**：判定用分区生效宽（_resolve_width
  同源同值）；R5 封锁对宽单调，未来若引入宽度阶梯须扫宽度集后再定
  封锁判据（0.9.0 版本注记，另批复审）。刻意不设的判据（宁漏判清单）：
  事后 geom-secondary 升格/keepout/板固孔带/板边带/容量锁/via-obstacle
  类/ribbon/fixed-shape/退化分区密封（DESIGN §1.7）。
- **W-2 verdict_provenance 出口读数**：execute_candidate 新增可选 kwarg
  selection_verdict=None|"SAT"|"UNSAT"|"UNKNOWN"（他值 fail-closed 抛
  ExecutorError）；kwarg 只参与 provenance 计算，零触碰路由决策/序/log=
  只动出口读数面、不动 selection 算法（v5/selection.py 零改动）。返回面
  新增键 verdict_provenance（kwarg 未提供=省略键，主线旧调用面输出与
  0.8.0 字节等）：ROUTED×UNKNOWN=executor-renegotiated（终态出自执行器
  重协商，非 selection 直选）；ROUTED×SAT=selection-certified；ROUTED×
  UNSAT=contradictory-selection-unsat（口径冲突须披露复核）；FAILED 短路
  =execute-short-circuit:sealed-short-circuit；FAILED 穷举=
  execute-exhausted（取值表=DESIGN-DECISION §3）。**fail-closed 滤除语义
  文档化**：select_best 的 fail-closed 滤除（ledger.rejection_reasons）
  =该候选未过 selection 静态合同校验、不得作「已认证候选」直选，**≠板
  不可布**——执行器在完整世界模型（A* 阶梯+有界 rip-up）下仍可能协商出
  合法实现（syn-r02 实例：唯一候选被 R6 拒后执行器布通、check/drc 干净）；
  反之 SAT 亦不担保必布通。selection_verdict 答「selection 层能否认证
  候选」，routed+verdict_provenance 答「终态真值及其出处」；UNKNOWN+
  routed+executor-renegotiated 三元组即「selection 口径遮蔽执行真值」的
  显式化收口。FAILED 侧同理：穷举/短路终态是执行器的构造性主张，非
  selection 判定。

文档化最小决定（偏离披露）：
1. candidate.layer_assignment 作为**首选层**而非硬约束——A* 停留在首选层 0 成本、
   换层付过孔费；容量/障碍封死时允许换层（无任何 R 规则把 layer_policy 定为硬
   地板，v5.drc 亦不查层策略；软先验冲突由过孔费的价格机制体现）。升级件①
   起「首选层 ∉ 端点焊盘层」时起种于焊盘层（首选层经换层孔回归，软先验
   价格机制不变）。
2. 过渡孔/回流孔的孔铜**在放置点强制**（_via_ok 无豁免 R5 + 孔-孔最小距，
   比 route_check 场景的同分区豁免更严）——网级门/终检仍按场景口径复核
   折线铜；孔铜 R5 的豁免差（同分区孔-铜对）由放置侧严格性兜底。
3. FAILED 时已成功网不落盘（routes=None，无半成品工件——sidecar 卫生 §3.5）。
4. 同分区对腿的 R5 强制在 A* 边检查中执行（共享端点入边豁免除外）；
   route_check 的同分区豁免只影响归责，不放松执行器侧物理分离。
"""
import heapq
import math
import os

from . import staging
from . import guide as _guide   # R2 W-3：波次（主选）/档位（n≤12）导引展开（纯函数）
from .steiner import _mst_edges  # R1 W-4：多端网拓扑失败 MST 回退边序（纯函数）
from .drc import check_all, check_clearance, check_keepout
from .drc import (HOLE_TO_HOLE_MM, edge_inner_rect, normalize_holes,   # D8 板固孔禁布带
                  hole_track_blocked, hole_via_blocked)   # 带值/口径单源=v5.drc
from .measure import DEFAULT_COST_MODEL, polyline_length
from .metrics import capacity as cap_mod
from .metrics import clearance
from .metrics import width_prior as wp
from .route_check import (FIXED_CID_PREFIX, ROUTE_CID_PREFIX, ROUTES_SCHEMA_VERSION,
                          ROUTE_CHECK_VERSION, _BoardView, _RouteCopper,
                          _fixed_coppers, _routing_coppers, _segment_coppers,
                          _width_checks, _zone_rect,
                          capacity_ledger, validate_routes)
from .route_check import check_routes as _check_routes
# OPT-09（EXEC-R2 E2，2026-10-08）：真实工作进度 sidecar 接线（opt-in）。
# 默认（环境变量 V5_OPT09_PROGRESS_SIDECAR 未设）= ProgressSidecar.from_env
# 返回 None → 全部接线守卫短路：不建文件、不写事件、不改任何返回值/
# canonical 面（A1 writeAuthorization：仅进度回调/sidecar 接线，只加不改；
# 搜索/几何/候选排序零触碰）。health_watchdog 仅依赖 stdlib，无环导。
from .health_watchdog import ProgressSidecar
from .failure_events import FailEventJournal   # R4-B：fail-event.v1 opt-in 失败事件侧车
from .candidate_events import (CandidateEventJournal,   # R8-B：candidate-event.v1
                               register_engine_exit)     # opt-in 候选出口事件侧车
# OPT-04（EXEC-R2 E2，2026-10-08）：统一 geometry_semantics 版本声明接线
# （纯声明，A1 04-F/09-G：executor.py 由 OPT-09 单写者集成；契约=
# v5/geometry_semantics.py 的 VERSION + declare_consumer("executor")，幂等）。
# 零判定迁移：只登记消费方身份并暴露 GEOMETRY_SEMANTICS_VERSION；几何判定/
# 搜索/候选排序零触碰；canonical routes/结果核心零改动——版本载体=进度
# sidecar manifest（关联侧车，A1 04-F「实际调用输出或关联侧车」），
# 不进 routes 工件。geometry_semantics 模块级仅依赖 stdlib（无环导）。
from . import geometry_semantics as _geometry_semantics
_geometry_semantics.declare_consumer("executor")
GEOMETRY_SEMANTICS_VERSION = _geometry_semantics.VERSION


def _progress_candidate_sha256(candidate):
    """OPT-09 侧车 manifest 绑定用候选 canonical hash（纯读；失败→None）。"""
    try:
        from . import canonical
        return canonical.canonical_sha256(candidate)
    except Exception:
        return None

EXECUTOR_VERSION = "v5.executor/0.13.0"  # 0.13.0=engine-fix-r1 阶段二（用户
                                         # 2026-10-23 裁「两阶段修」第二步）：
                                         # FX-3 乐观可达性预检（escape-only
                                         # 门；族级一次多源 BFS 短路必然失败
                                         # 的逃逸计划，照常输出逐字节相同的
                                         # 耗尽失败行——negotiation_log/终态
                                         # 面全等，FAILED 族墙钟坍缩；健全性
                                         # 论证=_relaxed_family_reached
                                         # docstring；验证=engine-fix-r1 阶段二
                                         # 批 ROUTED 全量字节等＋FAILED 终态面
                                         # 全等＋crossproc，见
                                         # out\engine-fix-r1\FX-STAGE2-REPORT-
                                         # 2026-10-23.md）。R 判定/A* 语义/
                                         # 计划阶梯/日志格式零改动。
                                         # 0.12.0=阶段一：FX-1 梯内 memo＋
                                         # FX-2 微优化（纯等价提速，字节等
                                         # 验证=FX-STAGE1-REPORT-2026-10-23.md；
                                         # 依据=out\throughput-diag-r1\
                                         # THROUGHPUT-DIAG-REPORT-2026-10-23.md）。
                                         # 0.11.0=EXEC-R8-B：候选出口事件
                                         # 侧车接线（opt-in env
                                         # V5_R4B_CANDIDATE_EVENTS，沿
                                         # fail-event 同款纪律；出口事件走
                                         # baseline 通道 registered_not_
                                         # extension，准入语义零改动）。
                                         # 0.10.0=V5-R7：W-2 障碍栅格保守 max
                                         # 近似（r5→view.r5_max；drc 单源）+
                                         # _net_gate R5 网对类别取值 +
                                         # W-3 真实板轮廓带入 edge_blocked/
                                         # via_blocked/归因/geom-secondary
                                         # 摘除面（outline_band；缺键零漂移）。
                                         # 0.9.0=V5-EXECUTOR-ENG-R1（W-1 SC-1
                                         # 构造性无解事前短路 sealed-short-circuit
                                         # +W-2 verdict_provenance 出口读数面，
                                         # selection_verdict kwarg 纯读数；详见
                                         # 模块 docstring「V5-EXECUTOR-ENG-R1」
                                         # 节与 DESIGN-DECISION.md）。
                                         # 0.8.0=V5-R1（多端网显式 Steiner 拓扑
                                         # 逐边布线）：W-4 逐拓扑边 2 端 A*（A*
                                         # 内核/成本函数/R 判定零改；端点层约束/
                                         # 豁免半径经 endpoint_meta 注入=消费面
                                         # 扩展）；连通融合=同网铜 A* 面既非障碍
                                         # （0.7.0 既有语义）+Steiner 分支点起种
                                         # 层=已布层账；拓扑失败 MST 回退（任务书
                                         # §5 可达性回退）。
                                         # 0.7.0=V5-R2（rip-up 有界深化+导引
                                         # 通道接线）：W-1 有界参数 2/8/20→5/12/30
                                         # +ripup_params 可配；W-2 阻塞集联合重排
                                         # （上位替代者∪联合评估，sorted() 冻结）；
                                         # W-3 波次导引主选+档位 n≤12（v5.guide）；
                                         # W-4 victim 定向交换探针 B=3。A* 内核/
                                         # 成本函数/R 判定零改动（非目标）。
                                         # 0.6.1=V5-SMALLWAVE A3：geom-secondary
                                         # log 行；0.6.0=V5-D8 板固孔禁布带；
                                         # （0.5.0=P5⑥ D6-3 板边禁布带）
GENERATOR = "v5.executor"
GRID_PITCH = 0.25
# 协商兜底尝试阶梯（确定性；variant 键见 _attempt_label）
# r2 档位语义（v5.drc 整线累计的保守实现，两档皆保证过网级 v5.drc 门）：
#   "near"         —— 段距 < min_distance 且该段有投影重叠才封（多数网直达最优）；
#   "overlap_free" —— 有投影重叠即封（累计恒 0 ≤ max_parallel，近锁网兜底）。
_ATTEMPT_VARIANTS = (
    {"prefer": True, "r2": "near", "via_cost": None, "phase": 0.0},
    {"prefer": True, "r2": "overlap_free", "via_cost": None, "phase": 0.0},
    {"prefer": False, "r2": "near", "via_cost": None, "phase": 0.0},
    {"prefer": False, "r2": "overlap_free", "via_cost": 0.0, "phase": 0.0},
    {"prefer": False, "r2": "overlap_free", "via_cost": 0.0, "phase": 0.5},
)
_DIRS8 = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
_SQRT2 = math.sqrt(2.0)
# 升级件④尝试阶梯常量（序披露于模块 docstring；确定性）：
_GRID_SCALES = (1.0, 0.5, 0.25)  # 0.25mm 基线 / 0.125mm 细化 / 0.0625mm 细档（F4a）
_ESCAPE_RADII = (1, 2, 3)      # 逃逸半径渐进（栅格格数）
_ESCAPE_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1),
                (1, 1), (1, -1), (-1, 1), (-1, -1))   # 4 向先、对角后
_ESCAPE_VARIANT = {"prefer": False, "r2": "overlap_free", "via_cost": 0.0,
                   "phase": 0.0}   # 逃逸计划固定用最宽容变体（=阶梯位 4 语义）
# 升级件⑤ F4 常量（序披露于模块 docstring「升级件⑤-F4」节；确定性）：
_FINE_SCALE = 0.25             # F4a 细档 scale → pitch = 0.0625mm
_FINE_VARIANTS = _ATTEMPT_VARIANTS[:4]   # 细化档前 4 变体（不含 lane-shift，
# 0.0625 栅格半格相位 0.015625mm 属亚栅格噪声；R2 档位/层偏好/过孔价三轴保留）
_FINE_ESCAPE_START_DIRS = _ESCAPE_DIRS       # F4b 细档逃逸：起点侧 r1×8 向全
_FINE_ESCAPE_GOAL_DIRS = _ESCAPE_DIRS[:4]    # 终点侧 r1×4 轴向
_RIPUP_MAX_ROUNDS_PER_NET = 5      # R2 W-1（0.6.1 值 2）：每网 rip-up 轮数上限
_RIPUP_MAX_TOTAL_PER_CANDIDATE = 12  # R2 W-1（0.6.1 值 8；带值扫描候选 12/16，
#  缺省=12 待主审 LEAD-REVIEW 复核裁定）：每候选全局 rip-up 轮数上限
_RIPUP_ESCAPE_REACH_MM = 0.75       # 端点逃逸邻域半径 = 逃逸阶梯最大位移（r3×0.25）
_RIPUP_REROUTE_MAX_PLANS = 30       # R2 W-1（0.6.1 值 20；带值扫描候选 20/30/40，
# 缺省=30 待主审复核裁定）：被 rip 网 fresh 重布的计划前缀上界
# （重布语义=在障碍超集下恢复既有布线，前缀计划（两档栅格全变体+逃逸批次）
# 为有界协商重搜；N 本网重布仍用完整 106 阶梯）
_RIPUP_PROBE_BUDGET = 3             # R2 W-4：victim 定向交换探针预算/轮（B=3 缺省，
#  S2 结论=约束在提案质量非预算；批内可扫 3/5——ripup_params.probe_budget）
_RIPUP_JOINT_COST_FACTOR = 2        # R2 W-2：联合集启用护栏（score_joint ≤
#  factor×score_greedy；纯整数比较，防联合重排集爆炸）
# R2 W-1：board/任务可配有界参数（execute_candidate(ripup_params=...) 白名单
# 键覆盖缺省；缺省=上列常量。带值扫描实验经此通道，不触环境变量/全局态）
_RIPUP_PARAM_KEYS = ("max_rounds_per_net", "max_total_per_candidate",
                     "reroute_max_plans", "probe_budget", "joint_cost_factor",
                     "guide")
_FINE_WINDOW_MARGIN_MM = 1.0        # F4a 细档限域窗口外扩（≥逃逸位移+吸附半格）
# 升级件⑤ F2 回流孔候选扩容常量（确定性；序披露于模块 docstring「升级件⑤」节）：
_RETURN_VIA_SUBSTEP = 0.5      # 半径细步进档 = pitch×0.5（0.25mm 栅格→0.125mm 档）
_RETURN_VIA_FAMILIES = (       # 家族序即方向序底座：轴向 4 → 对角 4 → 马步 8
    ((1, 0), (-1, 0), (0, 1), (0, -1)),
    ((1, 1), (1, -1), (-1, 1), (-1, -1)),
    ((2, 1), (2, -1), (-2, 1), (-2, -1),
     (1, 2), (1, -2), (-1, 2), (-1, -2)),
)   # 马步族补齐轴向↔对角之间的两侧角域（双侧锚点偏移备选），共 16 方向
# R1 性能件（proto）常量（perf/PROFILE-R1.md §8；等价论证见 PERF-R1-REPORT.md）：
_PRUNE_SLACK = 1e-12   # 段级下界剪枝安全裕度（≫rect_rect_gap 舍入上偏差 ~1e-15，
                       # 被剪段真距离必 > 当前最优 → min 逐位不变）
_GRID_CELL = 2.0       # 障碍/孔点粗预选网格边长（mm；纯整数格算，候选集为
                       # 原逐障碍精确预滤的超集，精判沿用原比较）

# 0.12.0 FX-1（engine-fix-r1 阶段一）：梯内判定 memo 的哨兵与容量帽。
# _MEMO_MISS=dict.get 缺省哨兵（区分「未命中」与「命中值=None(边开放)」）；
# 容量帽=防大板细栅格族（如 6 层×15 万格点）memo 无界膨胀的内存护栏
# （profile 外推：badgeleds 全梯唯一键 ~2.5M 条，帽内典型 ~0.5M；
# 达帽后停止登记新键、既有键继续命中——收益部分保留，如实披露）。
_MEMO_MISS = object()
_EB_MEMO_CAP = 1200000   # FX-1b：族清策略下峰值=单族唯一键（badgeleds
                          # P1 族 ~1.84M、帽内覆盖 ~65%；内存峰值 ~0.5GB/worker）
_VB_MEMO_CAP = 500000


def _grid_add(grid, bbox, cell, idx):
    """bbox 覆盖的全部网格单元登记 idx（A4 预选超集登记）。"""
    cx0 = int(math.floor(bbox[0] / cell))
    cy0 = int(math.floor(bbox[1] / cell))
    cx1 = int(math.floor(bbox[2] / cell))
    cy1 = int(math.floor(bbox[3] / cell))
    for cx in range(cx0, cx1 + 1):
        for cy in range(cy0, cy1 + 1):
            k = (cx, cy)
            lst = grid.get(k)
            if lst is None:
                grid[k] = [idx]
            else:
                lst.append(idx)


def _grid_query(grid, bbox, cell):
    """bbox 覆盖单元的候选索引并集（升序=障碍表提交序；纯比较零浮点）。

    0.12.0 FX-2b（engine-fix-r1 阶段一）：单格快路——查询框只落 1 格时直接
    返回该格登记列表（_grid_add 按 idx 升序登记 ⇒ 格内列表天然升序，与
    sorted(并集) 同序同值），空格返回 ()（调用面纯迭代，[]/() 等价）；
    多格路径逐字保留原实现。等价依据=THROUGHPUT-DIAG-REPORT-2026-10-23
    §5 FX-2；字节等验证=本批 crossproc＋在盘记录复验。"""
    cx0 = int(math.floor(bbox[0] / cell))
    cy0 = int(math.floor(bbox[1] / cell))
    cx1 = int(math.floor(bbox[2] / cell))
    cy1 = int(math.floor(bbox[3] / cell))
    if cx0 == cx1 and cy0 == cy1:
        return grid.get((cx0, cy0)) or ()
    hit = set()
    for cx in range(cx0, cx1 + 1):
        for cy in range(cy0, cy1 + 1):
            lst = grid.get((cx, cy))
            if lst is not None:
                hit.update(lst)
    return sorted(hit)


def _escape_plans(scale):
    """逃逸计划子阶梯（先起点后终点；半径渐进；4 向先、对角后；F4a 预算
    再分配修剪：r3 大位移档仅 4 轴向——大位移粗定位，对角增量留给 r1/r2
    细档；保留计划的相对序与 0.3.0 一致）。"""
    out = []
    for side in ("start", "goal"):
        for rad in _ESCAPE_RADII:
            dirs = _ESCAPE_DIRS if rad < 3 else _ESCAPE_DIRS[:4]
            for dx, dy in dirs:
                out.append((_ESCAPE_VARIANT, scale, (side, (dx, dy), rad)))
    return out


def _fine_escape_plans(scale):
    """F4b 细档逃逸计划（新变体组；先起点后终点）：起点侧 r1 全 8 向、
    终点侧 r1 4 轴向——0.0625mm 位移粒度的端点邻域重吸附候选（确定性
    方向序）；每计划即细档栅格上的整网 A*（逃逸×细化交错）。"""
    out = []
    for dx, dy in _FINE_ESCAPE_START_DIRS:
        out.append((_ESCAPE_VARIANT, scale, ("start", (dx, dy), 1)))
    for dx, dy in _FINE_ESCAPE_GOAL_DIRS:
        out.append((_ESCAPE_VARIANT, scale, ("goal", (dx, dy), 1)))
    return out


def _attempt_plans():
    """每网确定性尝试计划阶梯（docstring「升级件④」「升级件⑤-F4」节）：
    计划 = (variant, grid_scale, escape)；escape=None 为整网常规搜索，
    否则 ("start"|"goal", (dx, dy), 半径格数)——起点/终点按格数平移后重吸附。
    阶段序（追加在既有阶段之后）：基线 5 → 0.125 细化 5 → 逃逸@0.25mm 40
    → 逃逸@0.125mm 40 → 新 0.0625mm 细化 4（F4a）→ 新 0.0625mm 逃逸 12
    （F4b），总预算 106/网（确定性再分配，不放宽）。"""
    plans = [(v, 1.0, None) for v in _ATTEMPT_VARIANTS]
    plans.extend((v, 0.5, None) for v in _ATTEMPT_VARIANTS)
    plans.extend(_escape_plans(1.0))
    plans.extend(_escape_plans(0.5))
    plans.extend((v, _FINE_SCALE, None) for v in _FINE_VARIANTS)
    plans.extend(_fine_escape_plans(_FINE_SCALE))
    return plans


class ExecutorError(ValueError):
    """执行器 fail-closed 错误（候选/板合同违约）；message 含键路径。"""

    def __init__(self, path, message):
        self.path = path
        self.message = message
        super().__init__("[%s] %s" % (path or "<root>", message))


def _require(cond, path, msg):
    if not cond:
        raise ExecutorError(path, msg)


def _attempt_label(variant):
    parts = []
    parts.append("prefer" if variant["prefer"] else "no-prefer")
    parts.append("r2-" + variant["r2"])
    parts.append("via-free" if variant["via_cost"] is not None else "via-priced")
    if variant["phase"]:
        parts.append("lane-shift%g" % variant["phase"])
    return "+".join(parts)


def _same_point(a, b):
    """两端点重合（逐坐标 ≤ EPS；与 route_check 链审计 _eq_pt 同口径）。"""
    return (abs(float(a[0]) - float(b[0])) <= clearance.EPS
            and abs(float(a[1]) - float(b[1])) <= clearance.EPS)


def _rect_dict(rect):
    return {"x_min": rect[0], "y_min": rect[1], "x_max": rect[2], "y_max": rect[3]}


def _copper_in_rect(cu, rect_d):
    """铜几何是否进入矩形（与 route_check._copper_in_rect 同口径）。"""
    if cu.band is not None:
        return clearance.rect_rect_gap(cu.band, (rect_d["x_min"], rect_d["y_min"],
                                                 rect_d["x_max"], rect_d["y_max"])) \
            <= clearance.EPS
    if cu.pad is not None:
        return clearance.pad_rect_distance(cu.pad[0], cu.pad[1], rect_d) <= clearance.EPS
    return min(clearance.segment_rect_distance(a, b, rect_d)
               for a, b in clearance.polyline(cu.polyline)) <= clearance.EPS


# ---------------------------------------------------------------- 场景上下文

class _Obstacle:
    """已入场景铜的搜索视图（分段与包围盒预计算；bbox 预滤加速 A*）。

    R1 性能件（proto）：折线障碍逐段包围盒预计算（seg_bbs，纯 min/max 零舍入），
    distance_to/via_gap 以 rect_rect_gap(bbox, seg_bbox) 作**精确下界**做候选段
    剪枝——被剪段的真距离 > 当前最优（剪枝裕度 _PRUNE_SLACK 覆盖下界浮点舍入
    上偏差），min 结果与全段扫描逐位相同（等价论证见 perf/PERF-R1-REPORT.md）。
    """

    __slots__ = ("cu", "segs", "seg_bbs", "seg_grid", "bbox", "partition_id")

    _SEG_GRID_MIN = 16   # 段数 ≥ 此值才建段网格（短折线全段精判更快）

    def __init__(self, cu):
        self.cu = cu
        pts = []
        if cu.polyline:
            pts = [(float(p[0]), float(p[1])) for p in cu.polyline]
        elif cu.band is not None:
            pts = [(cu.band[0], cu.band[1]), (cu.band[2], cu.band[3])]
        elif cu.pad is not None:
            (cx, cy), r = cu.pad
            pts = [(cx - r, cy - r), (cx + r, cy + r)]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        self.bbox = (min(xs), min(ys), max(xs), max(ys))
        self.segs = list(zip(pts[:-1], pts[1:])) if cu.polyline else None
        if self.segs:
            self.seg_bbs = [(min(a[0], b[0]), min(a[1], b[1]),
                             max(a[0], b[0]), max(a[1], b[1]))
                            for a, b in self.segs]
        else:
            self.seg_bbs = None
        # R1 性能件二级：长折线的段级粗网格（distance_blocked/via_gap_blocked
        # 的候选段预选；登记=各段 bbox 覆盖格，纯整数格算）
        if self.segs and len(self.segs) >= self._SEG_GRID_MIN:
            self.seg_grid = {}
            for i, sb in enumerate(self.seg_bbs):
                _grid_add(self.seg_grid, sb, _GRID_CELL, i)
        else:
            self.seg_grid = None
        self.partition_id = getattr(cu, "partition_id", None)

    def distance_to(self, p, q):
        """线段 (p,q) 与本铜的最小距离（口径同 v5.drc._actual_gap 的分派）。
        折线分支按段包围盒精确下界剪枝（R1 性能件；min 逐位不变）。
        （热路径消费方已改走 distance_blocked 阈值谓词；本方法保留精确值口。）"""
        cu = self.cu
        if cu.band is not None:
            return clearance.segment_rect_distance(p, q, _rect_dict(cu.band))
        if cu.pad is not None:
            (c, r) = cu.pad
            return clearance.pad_segment_distance(c, r, p, q)
        best = float("inf")
        bb = (min(p[0], q[0]), min(p[1], q[1]), max(p[0], q[0]), max(p[1], q[1]))
        thresh = None   # 首段必算；其后仅算下界 < best+SLACK 的段
        for (a, b), sb in zip(self.segs, self.seg_bbs):
            if thresh is not None and \
                    clearance.rect_rect_gap(bb, sb) >= thresh:
                continue
            d = clearance.segment_segment(p, q, a, b)
            if d < best:
                best = d
                thresh = best + _PRUNE_SLACK
        return best

    def distance_blocked(self, p, q, t):
        """谓词版 distance_to：折线铜与本线段最小距离是否 < t（R1 性能件二级）。
        候选段 = 段网格中与 (p,q) 包围盒 ⊕t 覆盖格相交者——真距离 < t 的段其
        段包围盒与查询框 ⊕t 必相交（bbox 间隙 ≤ 真距离 < t ⟹ 双轴分离 < t），
        即「违例段必在候选集」⇒ any(候选段 segment_segment < t) 与
        min(全段) < t 逐位等价（min 选取精确无舍入）。band/pad 分支单发
        原语直判（原口径）。非折线铜/无网格短折线全段精判。"""
        cu = self.cu
        if cu.band is not None:
            return clearance.segment_rect_distance(p, q, _rect_dict(cu.band)) < t
        if cu.pad is not None:
            (c, r) = cu.pad
            return clearance.pad_segment_distance(c, r, p, q) < t
        if self.seg_grid is not None:
            bb = (min(p[0], q[0]) - t, min(p[1], q[1]) - t,
                  max(p[0], q[0]) + t, max(p[1], q[1]) + t)
            cand = _grid_query(self.seg_grid, bb, _GRID_CELL)
        else:
            cand = range(len(self.segs))
        for i in cand:
            a, b = self.segs[i]
            if clearance.segment_segment(p, q, a, b) < t:
                return True
        return False

    def via_gap(self, p, via_r):
        """孔铜圆 (p, via_r) 与本铜的 R5 间隙（口径同 v5.drc._actual_gap 的
        圆-铜分派：圆-矩形=pad_rect_distance、圆-圆=点距-两半径、
        圆-折线=点线距-半径——中心线铜的半径侧=孔铜半径）。
        折线分支以点为退化包围盒取段级精确下界剪枝（R1 性能件；min 逐位不变）。
        （热路径消费方已改走 via_gap_blocked 谓词；本方法保留精确值口。）"""
        cu = self.cu
        if cu.band is not None:
            return clearance.pad_rect_distance(p, via_r, _rect_dict(cu.band))
        if cu.pad is not None:
            (c, r) = cu.pad
            return max(0.0, clearance.point_point(p, c) - r - via_r)
        best = float("inf")
        bb = (p[0], p[1], p[0], p[1])   # 点=退化矩形（rect_rect_gap=点-矩形距离）
        thresh = None
        for (a, b), sb in zip(self.segs, self.seg_bbs):
            if thresh is not None and \
                    clearance.rect_rect_gap(bb, sb) >= thresh:
                continue
            d = clearance.point_segment(p, a, b)
            if d < best:
                best = d
                thresh = best + _PRUNE_SLACK
        return max(0.0, best - via_r)

    def via_gap_blocked(self, p, via_r, t):
        """谓词版 via_gap：max(0, 最小点线距 - via_r) 是否 < t（R1 性能件二级）。
        候选段 = 段网格中与孔心 ⊕(t+via_r) 覆盖格相交者（谓词真 ⟹ 点线距
        < t+via_r ⟹ 该段必在候选集），候选段逐段复算原精确谓词式
        max(0.0, point_segment - via_r) < t——与全段 min 版逐位等价。"""
        cu = self.cu
        if cu.band is not None:
            return clearance.pad_rect_distance(p, via_r, _rect_dict(cu.band)) < t
        if cu.pad is not None:
            (c, r) = cu.pad
            return max(0.0, clearance.point_point(p, c) - r - via_r) < t
        reach = t + via_r
        if self.seg_grid is not None:
            bb = (p[0] - reach, p[1] - reach, p[0] + reach, p[1] + reach)
            cand = _grid_query(self.seg_grid, bb, _GRID_CELL)
        else:
            cand = range(len(self.segs))
        for i in cand:
            a, b = self.segs[i]
            if max(0.0, clearance.point_segment(p, a, b) - via_r) < t:
                return True
        return False


class _Context:
    """执行期确定性场景状态（固定铜 + 已提交网 + 容量账本）。

    fixed-shape（ribbon/既布）分区的铜已经由 _fixed_coppers 进入 obstacles/ledger，
    其工件 entry 只进 entries（工件声明），**不**重复入账本/障碍（同一物理铜，
    防双计——route_check.build_scene 同款去重规则）。
    """

    def __init__(self, board):
        self.board = board
        self.view = _BoardView(board)
        fixed, declared = _fixed_coppers(self.view)
        self.fixed = fixed
        self.declared = declared
        # D6-3 板边禁布带内矩形（workspace 内缩 EDGE_CLEARANCE_MM；带值/轮廓
        # 源单源=v5.drc.edge_inner_rect，与 route_check/drc 同一带同口径）
        self.edge_inner = edge_inner_rect(self.view.workspace)
        # V5-R7 W-3：真实板轮廓边距带（board.outline_mm；缺键 ⇒ None=workspace
        # 矩形带旧路径零漂移；判定单源=v5.drc.OutlineBand，与 route_check 同带）
        self.outline_band = self.view.outline_band
        # D8 板固孔禁布带（V5-D8 2026-09-22）：holes=[]（旧世界板/合成板）时
        # self.holes 为空、全部孔检查短路=行为与 0.5.0 逐位一致（向后兼容）。
        self.holes = normalize_holes(self.board.get("holes"))
        # D8 分区端点缓存（孔禁布带端点豁免判定；端点=焊盘中心=孔心，板 dict
        # 同值精确相等，1e-9 容差仅防末位表示差）。V5-R1：多点网=全部端点
        # （去重后逐点豁免；Steiner 分支点非焊盘不入豁免集——保守方向）。
        self._pid_endpoints = {
            pid: tuple((float(pt[0]), float(pt[1]))
                       for pt in _dedup_endpoints(p["geometry"]["endpoints"]))
            for pid, p in self.view.partitions.items()}
        # D8 孔粗网格登记扩的走线侧半宽上界：全板 width_prior.w_max/2（width
        # 由 width_prior 计算且 clamp 至 [w_min, w_max]，planned_width 恒 ≤
        # w_max——wp.width_for 合同；网格为超集预选，精判沿 drc 谓词）
        w_max = 0.0
        for _p in self.view.partitions.values():
            _wp = _p.get("width_prior") or {}
            w_max = max(w_max, float(_wp.get("w_max", 0.0)))
        self._hole_w_max_half = w_max / 2.0
        self.obstacles = []            # _Obstacle（固定铜 + 已提交网铜，提交序）
        self.entries = []              # 已提交 route entry（工件序）
        self.route_coppers = []        # 已提交 A* 网铜（_RouteCopper，非 fixed-shape）
        self.via_points = []           # 已提交孔点 [(net_id, pid, (x, y))]（D2/D3）
        # 容量账本：(zone_id, layer) -> {"widths": [..], "capacity": c}
        self.ledger = {}
        init = capacity_ledger(self.view, fixed, declared)
        for clid, item in init.items():
            zid, layer = clid.split("/", 1)
            self.ledger[(zid, layer)] = {
                "widths": [float(e.occupancy) for e in item["entries"]],
                "capacity": float(item["capacity_mm"])}
        for cu in fixed:
            self.obstacles.append(_Obstacle(cu))
        # 固定铜基账（F4c rip-up 账本重建基线：此刻 widths 仅含固定铜条目）
        self._ledger_base = {k: list(v["widths"]) for k, v in self.ledger.items()}
        # ---- R1 性能件（proto；A3/A4/A2，等价论证见 PERF-R1-REPORT.md）----
        self._gen = 0         # 场景代数：障碍/孔点集合实质变更时 +1（网格失效）
        self._spatial = None  # (gen, r5, via_r, grid5, gridall, gridvp) 惰性构建
        # A2：走廊 (zone_id, rect_dict, capacity) 预计算（恒定；免逐边重建 dict）
        self._corridor_rects = [
            (zone["zone_id"], _rect_dict(_zone_rect(zone)),
             float(zone["capacity"])) for zone in self.view.corridors]
        # ---- 0.12.0 FX-2a/FX-1（engine-fix-r1 阶段一；依据=
        # THROUGHPUT-DIAG-REPORT-2026-10-23 §4/§5；字节等验证=本批
        # crossproc＋在盘记录复验）----
        # FX-2a：D8 孔端点豁免预计算缓存（pid → 豁免孔索引 frozenset）。
        # _pid_endpoints 与 holes 均为 __init__ 后不变量 ⇒ 缓存终身有效；
        # 豁免判定逐字保留原 any(abs≤1e-9) 容差语义（预计算仅把逐候选
        # 重复扫描折叠为每 pid 一次，profile 实证 bme280 族省 ~12% CPU）。
        self._hole_exempt = {}
        # FX-1：梯内边/孔判定 memo（None=未激活；_run_attempt_ladder 作用域
        # 内激活，finally 保证关闭）。激活作用域内场景冻结（失败尝试
        # stage→discard 不触 ctx；成功即 commit 后梯即刻返回）且
        # net_id/pid/width 恒定 ⇒ 同键必同值=纯 memo，行为字节等。
        # _eb_memo_args=激活时 (net_id, pid, width) 三元组——包装器逐调用
        # 比对，不符即旁路（防作用域外误用，健全性双保险）。
        self._eb_memo = None
        self._vb_memo = None
        self._eb_memo_args = None
        # FX-3（0.13.0）：梯内可达性预检的族级缓存（(scale,相位)→
        # _RELAXED_REACHABLE/_RELAXED_CAPPED/穷尽分量 frozenset）；与 FX-1
        # 同作用域纪律（_run_attempt_ladder 激活、finally 关闭、FX-1b 族清
        # 同步清空）。scale 地板：某 scale 触预算帽→更细族（节点更多）直接
        # 跳过预检（候选级记忆，防逐族重复无谓 BFS——r21 实证三族各付一次
        # 触帽成本）。已布铜只增不减 ⇒ 组件只缩不涨（封锁单调）⇒ 地板为
        # 保守方向（只会少短路、不会误短路）。
        self._relaxed_cache = None
        self._relaxed_scale_floor = 0.0

    def _build_spatial(self):
        """障碍/孔点粗预选索引（R1 性能件 A3/A4）。四套网格（纯比较整数格）：
        grid5=edge_blocked R5 障碍（按层，扩=R5——与原逐障碍 bbox 预滤同扩）；
        gridall=via_blocked 障碍（跨层，扩=R5+via_r+各 obstacle half_width——
        与原 slack 预滤同扩）；gridvp=edge_blocked 孔点（扩=via_r+R5，与原
        slack 预滤同扩）；gridholes=D8 板固孔（扩=r_i+HOLE_TO_HOLE_MM+
        max(via_r, 全板 w_max/2)——via 查询框 ⊕via_r 与段查询框 ⊕width/2
        （width≤w_max）均 ⊆ 登记框 ⟹ 谓词真者必在候选集，超集精判沿 drc
        谓词，升序=孔表序）。候选集均为原精确预滤的超集，逐候选沿用原比较
        与原几何原语精判，升序=提交序。"""
        view = self.view
        r5 = view.r5_max   # V5-R7 W-2：保守 max 近似（任务书 §4 风险②首版；
                       # drc.max_net_class_clearance——缺类板=标量零漂移）
        via_r = float(view.via_radius)
        g5, gall, gvp, gh = {}, {}, {}, {}
        for idx, ob in enumerate(self.obstacles):
            b = ob.bbox
            hw = float(ob.cu.half_width)
            _grid_add(g5.setdefault(ob.cu.layer, {}),
                      (b[0] - r5, b[1] - r5, b[2] + r5, b[3] + r5),
                      _GRID_CELL, idx)
            _grid_add(gall,
                      (b[0] - r5 - via_r - hw, b[1] - r5 - via_r - hw,
                       b[2] + r5 + via_r + hw, b[3] + r5 + via_r + hw),
                      _GRID_CELL, idx)
        for idx, (_n, _p, pt) in enumerate(self.via_points):
            _grid_add(gvp, (pt[0] - via_r - r5, pt[1] - via_r - r5,
                            pt[0] + via_r + r5, pt[1] + via_r + r5),
                      _GRID_CELL, idx)
        hole_extra = HOLE_TO_HOLE_MM + max(via_r, self._hole_w_max_half)
        for idx, (hx, hy, hr) in enumerate(self.holes):
            e = hr + hole_extra
            _grid_add(gh, (hx - e, hy - e, hx + e, hy + e), _GRID_CELL, idx)
        sp = (self._gen, r5, via_r, g5, gall, gvp, gh)
        self._spatial = sp
        return sp

    # -- 快照 / 恢复（_NetTransaction 底座；无残留语义见 staging） --
    # （升级件⑤ F4c：快照升级为列表副本恢复——rip-up 会收缩列表，截断式
    # 恢复不可逆；append-only 场景下列表恢复与旧截断语义逐字节一致）

    def snapshot(self):
        return {
            "obstacles": list(self.obstacles),
            "entries": list(self.entries),
            "route_coppers": list(self.route_coppers),
            "via_points": list(self.via_points),
            "ledger": {k: list(v["widths"]) for k, v in self.ledger.items()},
        }

    def restore(self, snap):
        # R1 性能件：先探障碍/孔点是否实质变化（未提交事务的回滚=逐元素同一，
        # 场景代数不递增 → 粗网格保持有效；网格输入仅 obstacles/via_points）
        changed = (len(self.obstacles) != len(snap["obstacles"])
                   or any(a is not b for a, b in
                          zip(self.obstacles, snap["obstacles"]))
                   or len(self.via_points) != len(snap["via_points"])
                   or any(a is not b for a, b in
                          zip(self.via_points, snap["via_points"])))
        self.obstacles[:] = snap["obstacles"]
        self.entries[:] = snap["entries"]
        self.route_coppers[:] = snap["route_coppers"]
        self.via_points[:] = snap["via_points"]
        for k, widths in snap["ledger"].items():
            self.ledger[k]["widths"] = list(widths)
        if changed:
            self._gen += 1

    def state_key(self):
        """状态指纹（测试用：rollback 后与快照前逐字节一致）。"""
        from . import canonical
        return canonical.canonical_json({
            "entries": self.entries,
            "ledger": {"/".join(k): v["widths"] for k, v in sorted(self.ledger.items())},
            "n_obstacles": len(self.obstacles),
            "via_points": self.via_points})

    # -- 提交 --

    def commit_entries(self, entries, coppers):
        for entry, cu in zip(entries, coppers):
            self.entries.append(entry)
            self.route_coppers.append(cu)
            self.obstacles.append(_Obstacle(cu))
            for zid, layer in self._touched_corridors(cu):
                cell = self.ledger.get((zid, layer))
                if cell is not None:
                    cell["widths"].append(float(entry["width"]))
        for entry in entries:
            for key in ("transition_vias", "return_vias"):
                for vp in entry.get(key) or []:
                    pt = (float(vp[0]), float(vp[1]))
                    if all(pt != q for _n, _p, q in self.via_points):
                        self.via_points.append((entry["net_id"],
                                                entry["partition_id"], pt))
        # R1 性能件：障碍/孔点集合实质变更 → 场景代数递增（粗网格失效重建）
        self._gen += 1

    def _touched_corridors(self, cu):
        """run 铜进入的走廊列表（镜像 route_check._copper_in_rect 口径）。
        R1 性能件（A2）：走廊矩形/zone_id 预计算复用（同值同序）。"""
        hits = []
        for zid, rect_d, _cap in self._corridor_rects:
            if _copper_in_rect(cu, rect_d):
                hits.append((zid, cu.layer))
        return hits

    # -- rip-up（升级件⑤ F4c；有界确定性网摘除） --

    def rip_net(self, net_id):
        """摘除已提交 A* 网 net_id 的全部 route 铜/条目/孔点并重建容量账本。
        只摘 commit_entries 流入的 A* 铜（cid=route: 前缀，即 self.route_coppers
        中 net_id 匹配者）；fixed-shape/退化条目（直接 append、无 route 铜、
        零铜展宽）不参与。账本按固定铜基账 + 现存 route 铜当前提交序重放
        （corridor_occupancy 与序无关，宽度序=提交序，与 commit_entries 一致）。
        返回摘除的 route 铜数（0=该网无已提交铜）。"""
        removed = [cu for cu in self.route_coppers if cu.net_id == net_id]
        if not removed:
            return 0
        removed_cids = {cu.cid for cu in removed}
        self.route_coppers = [cu for cu in self.route_coppers
                              if cu.net_id != net_id]
        # A* 条目 = 有 route 铜的条目（零长退化条目 [pt,pt] 无铜，不摘）
        def _ripped(e):
            return (e["net_id"] == net_id
                    and not (len(e["polyline"]) == 2
                             and e["polyline"][0] == e["polyline"][1]))
        self.entries = [e for e in self.entries if not _ripped(e)]
        self.obstacles = [ob for ob in self.obstacles
                          if ob.cu.cid not in removed_cids]
        self.via_points = [vp for vp in self.via_points if vp[0] != net_id]
        self._rebuild_ledger()
        # R1 性能件：障碍/孔点集合实质变更 → 场景代数递增（粗网格失效重建）
        self._gen += 1
        return len(removed)

    def _rebuild_ledger(self):
        """容量账本重建（F4c）：固定铜基账 + 现存 route 铜按当前提交序重放。"""
        for k, base in self._ledger_base.items():
            self.ledger[k]["widths"] = list(base)
        for cu in self.route_coppers:
            for zid, layer in self._touched_corridors(cu):
                cell = self.ledger.get((zid, layer))
                if cell is not None:
                    cell["widths"].append(float(cu.half_width) * 2.0)

    # -- A* 边合法性 --

    def edge_blocked(self, layer, p, q, net_id, pid, width,
                     exempt_same_partition=False):
        """候选边 (p,q) 在 layer 上是否封死。返回 None 或原因标记。

        0.12.0 FX-1（engine-fix-r1 阶段一）：本方法为 _edge_blocked_compute
        （原判定体，逐字保留）的**梯内 memo 包装**——memo 仅由
        _run_attempt_ladder 激活（其作用域内场景冻结且 net_id/pid/width
        恒定 ⇒ 同键必同值=纯 memo，行为字节等；论证与 profile 依据=
        THROUGHPUT-DIAG-REPORT-2026-10-23 §4-4/§5 FX-1）；未激活/实参
        三元组与激活时不符（健全性双保险）→ 直通判定体。障碍面语义、
        返回值与 docstring 合同见 _edge_blocked_compute。"""
        memo = self._eb_memo
        if memo is None or self._eb_memo_args != (net_id, pid, width):
            return self._edge_blocked_compute(
                layer, p, q, net_id, pid, width, exempt_same_partition)
        key = (layer, p, q, exempt_same_partition)
        hit = memo.get(key, _MEMO_MISS)
        if hit is not _MEMO_MISS:
            return hit
        result = self._edge_blocked_compute(
            layer, p, q, net_id, pid, width, exempt_same_partition)
        if len(memo) < _EB_MEMO_CAP:
            memo[key] = result
        return result

    def _edge_blocked_compute(self, layer, p, q, net_id, pid, width,
                              exempt_same_partition=False):
        """候选边 (p,q) 在 layer 上是否封死。返回 None 或原因标记。

        R2 不在此判（整线累计语义，由 _astar 的状态增广精确建模，见其 docstring）。
        exempt_same_partition：共享端点豁免半径内的边（仅同分区对腿）。
        障碍面（升级件⑤ F1）：固定铜 + 已提交网铜 + **已提交他网过孔铜**
        （跨全信号层圆盘，R5 中心线口径；同网孔=合法连接点）。
        D6-3（0.5.0）：板边禁布带（workspace 内缩 0.2mm 环带）入障碍——段任一
        端点出内矩形即封（内矩形凸 ⟺ 段触带），全信号层同带（本函数逐层调用
        天然逐层生效），带值/轮廓源单源=v5.drc；无豁免档（贴边无协商余地，
        对应 kicad copper_edge_clearance 0.2mm 缺省）。
        D8（0.6.0）：板固孔禁布带（board.holes[]）入障碍——段触孔禁布带即封
        （hole-keep-out，判定单源=v5.drc.hole_track_blocked）；端点豁免=孔心
        与本分区端点重合（走线连自身端点焊盘孔=合法铜连接；同网非端点孔仍
        拦=保守方向，PREREG-D8 §2.4 披露）。
        """
        view = self.view
        # R1 性能件（A3/A4）：场景代数校验 → 惰性（重）建粗预选网格
        sp = self._spatial
        if sp is None or sp[0] != self._gen:
            sp = self._build_spatial()
        # D6-3：板边禁布带（先于 R5/R6 的 O(1) 包络检查；原因标记与 exhaustion
        # 归因类同名）
        ix0, iy0, ix1, iy1 = self.edge_inner
        if p[0] < ix0 - clearance.EPS or p[0] > ix1 + clearance.EPS \
                or p[1] < iy0 - clearance.EPS or p[1] > iy1 + clearance.EPS \
                or q[0] < ix0 - clearance.EPS or q[0] > ix1 + clearance.EPS \
                or q[1] < iy0 - clearance.EPS or q[1] > iy1 + clearance.EPS:
            return "edge-clearance"
        # V5-R7 W-3：真实板轮廓带（在场 ⇒ 逐端点判定；轮廓凸 ⇒ 端点判即完备，
        # 凹轮廓栅格步内中段擦带为披露近似——步距=GRID_PITCH×scale 上界）。
        if self.outline_band is not None and (
                self.outline_band.point_blocked(p)
                or self.outline_band.point_blocked(q)):
            return "edge-clearance"
        # R6：禁布区（逐段 bbox 间隙 >0，与 route_check R6 逐段精查同口径）
        bbox = (min(p[0], q[0]), min(p[1], q[1]), max(p[0], q[0]), max(p[1], q[1]))
        for _zid, ko in view.keepouts:
            if clearance.rect_rect_gap(bbox, ko) <= 0.0:
                return "R6"
        # D8（0.6.0）：板固孔禁布带（R6 后、R5 前——带类先于铜间距类；holes=[]
        # 时 sp[6] 空网格零迭代=零行为差）。端点豁免：孔心与本分区任一端点
        # 重合（走线连自身端点焊盘孔=合法铜连接，kicad 同网铜-孔豁免族；世界
        # 模型无孔网信息，端点豁免=最近似——同网非端点孔仍拦=保守方向，
        # PREREG-D8 §2.4 披露）。判定单源=v5.drc.hole_track_blocked。
        if self.holes:
            # 0.12.0 FX-2a（0.13.0 起抽为 _hole_exempt_ids 共享件——与 FX-3
            # 可达性预检同一缓存同一容差语义）
            exempt = _hole_exempt_ids(self, pid)
            for hi in _grid_query(sp[6], bbox, _GRID_CELL):
                if hi in exempt:
                    continue
                hx, hy, hr = self.holes[hi]
                if hole_track_blocked((hx, hy), hr, p, q, width / 2.0):
                    return "hole-keep-out"
        # R5：既布铜/已布网膨胀（中心线口径与 v5.drc.check_clearance 一致）。
        # R1 性能件（A3/A4）：本层候选由粗网格预选（原逐障碍 bbox 预滤的超集，
        # 升序=提交序），逐候选沿用下方原精确比较与原几何原语——判定路径零改动。
        r5 = view.r5_max   # V5-R7 W-2：保守 max 近似（任务书 §4 风险②首版；
                       # drc.max_net_class_clearance——缺类板=标量零漂移）
        for oi in _grid_query(sp[3].get(layer) or {}, bbox, _GRID_CELL):
            ob = self.obstacles[oi]
            if ob.cu.net_id == net_id:
                continue
            if ob.bbox[0] - r5 > bbox[2] or ob.bbox[2] + r5 < bbox[0] \
               or ob.bbox[1] - r5 > bbox[3] or ob.bbox[3] + r5 < bbox[1]:
                continue   # bbox 预滤（原比较逐字保留；bbox 分量=原 min/max 同值）
            if exempt_same_partition and ob.partition_id is not None \
               and ob.partition_id == pid:
                continue   # 同分区对腿：共享端点入边豁免
            if ob.distance_blocked(p, q, r5 - clearance.EPS):
                return "R5"
        # R5（升级件⑤ F1，executor-孔协调缝）：已提交**他网**过孔铜圆盘按 R5
        # 入走线障碍——route_check 场景对已提交孔逐信号层构造圆铜（_via_coppers），
        # 本模型此前只含他网走线/焊盘铜，后网走线落入先提交孔 R5 邻域被终检
        # 实抓（badgeleds/pmod-bme280 根因）。孔铜跨全信号层，不按 layer 过滤；
        # 同网已提交孔=合法连接点跳过；同分区豁免与折线障碍同口径（共享端点
        # 入边豁免区；归责层同分区豁免覆盖该对）。
        # R1 性能件（A3/A4）：孔点候选由 gridvp 预选（登记扩=via_r+R5=原 slack
        # 预滤同扩，查询用未扩边 bbox——共享格 ⟺ 原预滤通过，超集精判）。
        via_r = sp[2]
        slack = via_r + r5
        for vi in _grid_query(sp[5], bbox, _GRID_CELL):
            vnet, vpid, vpt = self.via_points[vi]
            if vnet == net_id:
                continue
            if exempt_same_partition and pid is not None and vpid == pid:
                continue
            if vpt[0] + slack < bbox[0] or vpt[0] - slack > bbox[2] \
               or vpt[1] + slack < bbox[1] or vpt[1] - slack > bbox[3]:
                continue   # bbox 预滤（原比较逐字保留）
            if clearance.pad_segment_distance(vpt, via_r, p, q) < r5 - clearance.EPS:
                return "R5"
        # capacity：边进走廊矩形即按该走廊×层预留（近似 2）。
        # 既有占用 = Σ宽 + 既有条目间距（与 v5.metrics.capacity.corridor_occupancy
        # 同式），新条目增量 = 本网宽 + 1 个新增相邻间距。
        # R1 性能件（A2）：走廊 rect/capacity 预计算复用（同值同序）。
        for zid, rect_d, cap in self._corridor_rects:
            if clearance.segment_rect_distance(p, q, rect_d) <= clearance.EPS:
                cell = self.ledger.get((zid, layer))
                widths = cell["widths"] if cell else []
                occ = cap_mod.corridor_occupancy(
                    [cap_mod.CapacityEntry("n", w) for w in widths])
                need = width + (cap_mod.NET_NET_SPACING if widths else 0.0)
                if occ + need > cap + clearance.EPS:
                    return "capacity"
        return None

    def via_blocked(self, p, net_id):
        """孔位 p 是否封死（合同与障碍面语义见 _via_blocked_compute）。

        0.12.0 FX-1：梯内 memo 包装（同 edge_blocked——_run_attempt_ladder
        作用域激活；net_id 与激活三元组首元不符即旁路，纯 memo 字节等）。"""
        memo = self._vb_memo
        if memo is None or self._eb_memo_args is None \
                or self._eb_memo_args[0] != net_id:
            return self._via_blocked_compute(p, net_id)
        key = (p, net_id)
        hit = memo.get(key, _MEMO_MISS)
        if hit is not _MEMO_MISS:
            return hit
        result = self._via_blocked_compute(p, net_id)
        if len(memo) < _VB_MEMO_CAP:
            memo[key] = result
        return result

    def _via_blocked_compute(self, p, net_id):
        """孔位 p 是否封死（升级件① D2：孔铜=圆 radius=via_model 缺省 0.3）。
        严格判定（比折线边更严）：R6 禁布（圆入禁布区）+ **异网铜 R5 无同分区
        豁免**（钻孔穿他网铜=制造违例；共享端点抽象豁免只及铜不及孔）+
        对全部既有孔点最小孔心距 2·r+R5（D3 同式，孔-孔不变式）。返回
        None 或原因标记。D6-3（0.5.0）：孔心入板边禁布带即封（孔铜同为铜，
        与折线同带同口径、无豁免档）。D8（0.6.0）：孔位对板固孔禁布带零豁免
        （hole-keep-out，判定单源=v5.drc.hole_via_blocked）。"""
        view = self.view
        # R1 性能件（A3/A4）：场景代数校验 → 惰性（重）建粗预选网格
        sp = self._spatial
        if sp is None or sp[0] != self._gen:
            sp = self._build_spatial()
        via_r = float(view.via_radius)
        r5 = view.r5_max   # V5-R7 W-2：保守 max 近似（任务书 §4 风险②首版；
                       # drc.max_net_class_clearance——缺类板=标量零漂移）
        ix0, iy0, ix1, iy1 = self.edge_inner
        if p[0] < ix0 - clearance.EPS or p[0] > ix1 + clearance.EPS \
                or p[1] < iy0 - clearance.EPS or p[1] > iy1 + clearance.EPS:
            return "edge-clearance"
        # V5-R7 W-3：真实板轮廓带（孔心同带同口径；判定单源=v5.drc.OutlineBand）
        if self.outline_band is not None and self.outline_band.point_blocked(p):
            return "edge-clearance"
        for _zid, ko in view.keepouts:
            if clearance.pad_rect_distance(p, via_r, _rect_dict(ko)) <= 0.0:
                return "R6"
        # D8（0.6.0）：孔位对板固孔禁布带——**零豁免**（含本分区端点孔：
        # via-in-pad 叠孔同被拒）。kicad hole_to_hole 同网不豁免（wave6 14 条
        # genuine 全为引擎过孔 vs **同网**板固 PTH=本带闭合的差口）；判定单源
        # =v5.drc.hole_via_blocked（v5 判式用 via_r≥kicad 钻半径，单向保守）。
        if self.holes:
            for hi in _grid_query(sp[6], (p[0], p[1], p[0], p[1]), _GRID_CELL):
                hx, hy, hr = self.holes[hi]
                if hole_via_blocked((hx, hy), hr, p, via_r):
                    return "hole-keep-out"
        # R5（R1 性能件 A3/A4）：跨层候选由 gridall 预选（登记扩=各障碍
        # R5+via_r+half_width=原 slack 预滤同扩，查询用孔心退化 bbox——
        # 共享格 ⟺ 原预滤通过，超集精判，升序=提交序）。
        for oi in _grid_query(sp[4], (p[0], p[1], p[0], p[1]), _GRID_CELL):
            ob = self.obstacles[oi]
            if ob.cu.net_id == net_id:
                continue
            slack = r5 + via_r + float(ob.cu.half_width)
            if ob.bbox[0] - slack > p[0] or ob.bbox[2] + slack < p[0] \
               or ob.bbox[1] - slack > p[1] or ob.bbox[3] + slack < p[1]:
                continue   # bbox 预滤（含铜半宽；原比较逐字保留）
            if ob.via_gap_blocked(p, via_r, r5 - clearance.EPS):
                return "R5"
        min_hole = 2.0 * via_r + r5
        for _n, _pid, q in self.via_points:
            if clearance.point_point(p, q) < min_hole - clearance.EPS:
                return "D3"
        return None


# ---------------------------------------------------------------- 每网事务

class _NetTransaction:
    """网内 staging 事务（复用 v5.staging.StagingTransaction 语义）：
    stage（staging 暂存，可被下一尝试替换/弃置）→ 网级 v5.drc 门校验 →
    commit 一次性生效；rollback 终态回滚到快照（无残留：状态指纹与快照前
    逐字节一致）；提交后不可变。未提交的 staging 不触状态（discard 弃置）。"""

    def __init__(self, ctx, net_id, partition_id):
        self.ctx = ctx
        self.net_id = net_id
        self.partition_id = partition_id
        self._snap = ctx.snapshot()
        self._staged = None
        self._committed = False
        self._rolled_back = False

    def _guard_open(self, action):
        if self._committed:
            raise ExecutorError("transaction", "事务已提交，禁止 %s" % action)
        if self._rolled_back:
            raise ExecutorError("transaction", "事务已回滚，禁止 %s" % action)

    def stage(self, entries, coppers):
        self._guard_open("stage")
        self._staged = (entries, coppers)

    def discard(self):
        """弃置未提交 staging（不触状态；协商下一尝试前调用）。"""
        self._guard_open("discard")
        self._staged = None

    def commit(self):
        self._guard_open("commit")
        if not self._staged:
            raise ExecutorError("transaction", "空事务不可提交")
        entries, coppers = self._staged
        self.ctx.commit_entries(entries, coppers)
        self._staged = None
        self._committed = True

    def rollback(self):
        if self._committed:
            raise ExecutorError("transaction", "已提交事务不可回滚")
        self.ctx.restore(self._snap)
        self._staged = None
        self._rolled_back = True

    @property
    def committed(self):
        return self._committed

    @property
    def rolled_back(self):
        return self._rolled_back


# ---------------------------------------------------------------- 网级 v5.drc 门

def _net_gate(ctx, pid, net_id, coppers):
    """提交前网级自检：新铜是否**引入**违例（判定全出自 v5.drc，A9）。
    返回 None（过）或违例摘要字符串。capacity 只在新铜致溢出时归责本网
    （固定铜固有溢出归 route_check 终检，不阻塞单网）。"""
    view = ctx.view
    scene = list(ctx.fixed) + list(ctx.route_coppers) + list(coppers)
    new_cids = {cu.cid for cu in coppers}
    hard = view.hard_rules
    # R5（同分区对腿在归责层豁免——与 route_check 同规则）；V5-R7 W-2：
    # net_clearance 在场 ⇒ 网对类别取值（drc 单源换算；缺类板 None=零漂移）
    r5v, _checked = check_clearance(
        scene, float(hard.get("R5", {}).get("min_clearance_mm", 0.5)),
        net_clearance=view.net_clearance or None)
    part_of = {}
    for cu in scene:
        part_of[cu.cid] = getattr(cu, "partition_id", None)
    for v in r5v:
        a, b = v.subject_a, v.subject_b
        if a in new_cids or b in new_cids:
            pa, pb = part_of.get(a), part_of.get(b)
            if pa is not None and pa == pb:
                continue
            return "R5 %s↔%s gap=%.4f" % (a, b, v.data.get("gap_mm", -1))
    # R2 / capacity / R1（check_all 聚合）
    cap_checks = _tentative_capacity_checks(ctx, coppers)
    w_checks = _tentative_width_checks(view, coppers)
    report = check_all(scene, hard, sensitive_rects=view.sensitives,
                       capacity_checks=cap_checks, width_checks=w_checks)
    occ_with = dict((c[0], c[1]) for c in cap_checks)
    cap_by = dict((c[0], c[2]) for c in cap_checks)
    for v in report.violations:
        if v.rule == "R2" and (v.subject_a in new_cids or v.subject_b in new_cids):
            return "R2 %s↔%s" % (v.subject_a, v.subject_b)
        if v.rule == "capacity":
            clid = v.subject_a
            if clid not in occ_with:
                continue
            without = _corridor_occ_without(ctx, clid)
            if occ_with[clid] > cap_by[clid] + clearance.EPS and \
               without <= cap_by[clid] + clearance.EPS:
                return "capacity %s occ=%.3f>%.3f（本网致溢）" % (
                    clid, occ_with[clid], cap_by[clid])
        if v.rule == "R1":
            for cu in coppers:
                if cu.partition_id == v.subject_a:
                    return "R1 %s planned=%.3f<%.3f" % (
                        v.subject_a, v.data.get("planned_mm", -1),
                        v.data.get("required_min_mm", -1))
    # R6（逐段精查，镜像 route_check）
    for v in check_keepout(_segment_coppers(scene), view.keepouts, view.plane_layers):
        if v.subject_a.split("#seg")[0] in new_cids:
            return "R6 %s↔%s" % (v.subject_a, v.subject_b)
    return None


def _tentative_capacity_checks(ctx, new_coppers):
    """含新铜的走廊占用（镜像 route_check._capacity_checks：固定铜在前、
    已提交网按提交序、新铜按 entry 序）。"""
    view = ctx.view
    checks = []
    for zone in view.corridors:
        rect = _rect_dict(_zone_rect(zone))
        cap = float(zone["capacity"])
        by_layer = {}
        for cu in _routing_coppers(list(ctx.fixed) + list(ctx.route_coppers)
                                   + list(new_coppers)):
            info = view.layers.get(cu.layer)
            if info is None or info.get("kind") != "signal":
                continue
            if _copper_in_rect(cu, rect):
                by_layer.setdefault(cu.layer, []).append(cu)
        for layer in sorted(by_layer):
            group = by_layer[layer]
            fixed_part = [cu for cu in group if cu.cid.startswith(FIXED_CID_PREFIX)]
            rest = [cu for cu in group if not cu.cid.startswith(FIXED_CID_PREFIX)]
            entries = [cap_mod.CapacityEntry(
                cu.net_id, cu.half_width * 2.0,
                declared_occupancy=ctx.declared.get(cu.cid))
                for cu in fixed_part + rest]
            checks.append(("%s/%s" % (zone["zone_id"], layer),
                           cap_mod.corridor_occupancy(entries), cap))
    return checks


def _tentative_width_checks(view, new_coppers):
    """新铜的 R1 宽度核算（镜像 route_check._width_checks）。"""
    checks, _meta = _width_checks(view, list(new_coppers))
    return checks


def _corridor_occ_without(ctx, clid):
    """该走廊×层在**不含**新铜时的占用（区分固定铜固有溢出与新网致溢）。"""
    zid, layer = clid.split("/", 1)
    cell = ctx.ledger.get((zid, layer))
    if not cell:
        return 0.0
    return cap_mod.corridor_occupancy(
        [cap_mod.CapacityEntry("n", w) for w in cell["widths"]])


# ---------------------------------------------------------------- 耗尽归因

def _corridor_all_locked(ctx, zone, width):
    """该走廊在全部信号层上都满（本网再进任一层都溢出）。"""
    view = ctx.view
    for layer in view.signal_layers:
        cell = ctx.ledger.get((zone["zone_id"], layer))
        widths = cell["widths"] if cell else []
        occ = cap_mod.corridor_occupancy(
            [cap_mod.CapacityEntry("n", w) for w in widths])
        need = width + (cap_mod.NET_NET_SPACING if widths else 0.0)
        if occ + need <= float(zone["capacity"]) + clearance.EPS:
            return False
    return True


def _exhaustion_cause(ctx, pid, net_id, width, a_pt, b_pt):
    """A* 耗尽根因分类（升级件④诊断披露；升级件⑤ F1 补 via 障碍类；F4c 补
    rip-up 进程类；⑥波 D6-3 补 edge-clearance 边距类；确定性几何检查；R2 不
    参与——其整线累计语义无法逐边归因，敏感类以直连段距离作切片指示）。
    分类序：edge-clearance（端点入板边禁布带，⑥ D6-3——置首位：带内端点的
    部分段/出边必然全封，sealed 同真但根因是带，先判防遮蔽）> hole-keep-out
    （直连段穿板固孔禁布带，V5-D8 带类同理先判）> endpoint-
    sealed（端点吸附节点全部出边/换层边被封，逃逸/细化类）> via-obstacle-
    sealed（直连段穿他网已提交过孔铜 R5 邻域，executor-孔协调类）>
    capacity-locked（直连段穿过的走廊×层全满，分层中继类）> sensitive-crossed
    （直连段近敏感区，R2 切片类）> obstacle-dense（兜底）。F4c rip-up 启动后
    仍失败的网，exhaustion-cause 以**进程类**披露（ripped 网重布失败→
    ripup-reroute-failed（+cause）；轮/预算耗尽→ripup-exhausted），几何细节
    保留在 ripup 事件行——进程类在归责披露序中先于几何类（更有信息量）。"""
    view = ctx.view
    layers = list(view.signal_layers)
    pitch = GRID_PITCH
    x0, y0, x1, y1 = view.workspace
    nx = int(math.floor((x1 - x0) / pitch + 1e-9))
    ny = int(math.floor((y1 - y0) / pitch + 1e-9))

    # ⑥ D6-3 归因类：端点入板边禁布带（与 ctx.edge_inner 同源同带；内矩形凸
    # ⇒ 端点触带 ⟺ 直连段触带，端点判即完备）
    ix0, iy0, ix1, iy1 = ctx.edge_inner

    def _in_edge_band(pt):
        if (pt[0] < ix0 - clearance.EPS or pt[0] > ix1 + clearance.EPS
                or pt[1] < iy0 - clearance.EPS or pt[1] > iy1 + clearance.EPS):
            return True
        # V5-R7 W-3：真实板轮廓带（在场 ⇒ 同带同源判定）
        return ctx.outline_band is not None and ctx.outline_band.point_blocked(pt)

    if _in_edge_band(a_pt) or _in_edge_band(b_pt):
        return "edge-clearance（端点入板边禁布带，边距类）"

    # D8 归因类：直连段穿板固孔禁布带（端点豁免同 edge_blocked；带类先于
    # sealed/铜类，仅次于 edge-clearance——非热路径，全量扫描 219 孔级可接受）
    eps_pts = ctx._pid_endpoints.get(pid)
    for (hx, hy, hr) in ctx.holes:
        if eps_pts is not None and any(
                abs(hx - ex) <= 1e-9 and abs(hy - ey) <= 1e-9
                for (ex, ey) in eps_pts):
            continue
        if hole_track_blocked((hx, hy), hr, a_pt, b_pt, width / 2.0):
            return "hole-keep-out（直连段穿板固孔禁布带，孔距类）"

    def sealed(p):
        ix = max(0, min(nx, int(math.floor((p[0] - x0) / pitch + 0.5))))
        iy = max(0, min(ny, int(math.floor((p[1] - y0) / pitch + 0.5))))
        pt = (x0 + ix * pitch, y0 + iy * pitch)
        for li, layer in enumerate(layers):
            for dx, dy in _DIRS8:
                q = (pt[0] + dx * pitch, pt[1] + dy * pitch)
                if not (x0 <= q[0] <= x1 and y0 <= q[1] <= y1):
                    continue
                if ctx.edge_blocked(layer, pt, q, net_id, pid, width) is None:
                    return False
            for lj in range(len(layers)):
                if lj != li and ctx.edge_blocked(layers[lj], pt, pt, net_id,
                                                 pid, width) is None:
                    return False
        return True

    if sealed(a_pt) or sealed(b_pt):
        return "endpoint-sealed（端点吸附节点出边全封，逃逸/细化类）"
    # 升级件⑤ F1 归因类：直连段穿他网已提交过孔铜 R5 邻域（无绕行空间时
    # 的确定性归因串，与 edge_blocked 的孔铜障碍同口径）。
    r5x = view.r5_max   # V5-R7 W-2：保守 max（缺类板=标量零漂移）
    via_rx = float(view.via_radius)
    for vnet, _vpid, vpt in ctx.via_points:
        if vnet == net_id:
            continue
        if clearance.pad_segment_distance(vpt, via_rx, a_pt, b_pt) \
                < r5x - clearance.EPS:
            return "via-obstacle-sealed（他网过孔铜障碍封死直连走廊，绕行类）"
    for zone in view.corridors:
        rect_d = _rect_dict(_zone_rect(zone))
        if clearance.segment_rect_distance(a_pt, b_pt, rect_d) <= clearance.EPS                 and _corridor_all_locked(ctx, zone, width):
            return "capacity-locked:%s（直连走廊×层全满，分层中继类）" % zone["zone_id"]
    r2_min = float(view.hard_rules.get("R2", {}).get("min_distance_mm", 3.0))
    for rect_d in view.sensitive_rect_ds:
        if clearance.segment_rect_distance(a_pt, b_pt, rect_d) < r2_min - clearance.EPS:
            return "sensitive-crossed（直连段近敏感区，R2 切片类）"
    return "obstacle-dense（障碍稠密兜底类）"


def _geom_secondary_attr(ctx, pid, net_id, width, a_pt, b_pt):
    """几何二级归因（0.6.1，V5-SMALLWAVE A3，log-only 披露件）。

    exhaustion-cause 的进程类字面（ripup-exhausted）易被误读为「rip-up 深度
    不足」——DIAG-FAILED8 证据：4/4 ripup-exhausted 网实为板固有固定铜封死
    （阻塞集摘除也不解锁）。本件在其后补一行几何二级归因：失败网两端点的
    r0（吸附节点）+r1（八向锚节点）出边/换层边密封普查，阻塞源**仅计板
    固有固定铜**（摘他网已布铜/他网过孔/板固孔带/板边带后复检；口径=DIAG
    batch 类摘除的补集，A* 栅格与带检查同步生效）：
    - 两端点之一 r0/r1 全封 → "fixed-copper-sealed（…）"；
    - 均存在开放边 → "open（…）"（如实，不构成固定铜密封 witness）。

    纯诊断披露：在失败定局后调用，不改任何路由决策/序/输出面（除 log 行）；
    幂等/确定性：ctx 快照→内存面摘除→普查→恢复（holes/edge_inner 不在
    snapshot 内，单独保存还原；恢复侧场景代数必递增一次——普查期间
    _build_spatial 以 holes=[] 落粗网格，若摘除未实质变更 obstacles 则
    restore 不递增代数，旧代网格对 holes 查询失效不充分，故显式 +1 强制
    重建，确保后续（若有）查询回到全量口径）。
    """
    view = ctx.view
    layers = list(view.signal_layers)
    x0, y0, x1, y1 = view.workspace
    pitch = GRID_PITCH
    snap = ctx.snapshot()
    saved_holes = ctx.holes
    saved_edge_inner = ctx.edge_inner
    saved_outline_band = ctx.outline_band   # V5-R7 W-3：轮廓带随板边带一并摘除
    try:
        ctx.obstacles = [ob for ob in ctx.obstacles
                         if ob.cu.cid.startswith(FIXED_CID_PREFIX)]
        ctx.route_coppers = [cu for cu in ctx.route_coppers
                             if cu.net_id == net_id]
        ctx.via_points = [vp for vp in ctx.via_points if vp[0] == net_id]
        ctx.holes = []
        ctx.edge_inner = (x0, y0, x1, y1)
        ctx.outline_band = None
        ctx._rebuild_ledger()
        ctx._gen += 1

        def _ring_open(pt):
            ix = int(round((pt[0] - x0) / pitch))
            iy = int(round((pt[1] - y0) / pitch))
            nodes = [(ix, iy)] + [(ix + dx, iy + dy) for dx, dy in _DIRS8]
            for jx, jy in nodes:
                node = (x0 + jx * pitch, y0 + jy * pitch)
                if not (x0 <= node[0] <= x1 and y0 <= node[1] <= y1):
                    continue   # 工作域外节点不计（_exhaustion_cause.sealed 同口径）
                for li, layer in enumerate(layers):
                    for dx, dy in _DIRS8:
                        q = (node[0] + dx * pitch, node[1] + dy * pitch)
                        if not (x0 <= q[0] <= x1 and y0 <= q[1] <= y1):
                            continue
                        if ctx.edge_blocked(layer, node, q, net_id, pid,
                                            width) is None:
                            return True
                    for lj in range(len(layers)):
                        if lj != li and ctx.edge_blocked(
                                layers[lj], node, node, net_id, pid,
                                width) is None:
                            return True
            return False

        if not _ring_open(a_pt) or not _ring_open(b_pt):
            return ("fixed-copper-sealed（端点 r0/r1 出边在仅计板固有固定铜"
                    "口径下全封——板固有焊盘场密封 witness）")
        return ("open（端点 r0/r1 出边在仅计板固有固定铜口径下均存在开放边"
                "——不构成固定铜密封 witness）")
    finally:
        ctx.restore(snap)
        ctx.holes = saved_holes
        ctx.edge_inner = saved_edge_inner
        ctx.outline_band = saved_outline_band
        ctx._gen += 1


# --------------------------------------- V5-EXECUTOR-ENG-R1 W-1（SC-1 短路）

def _ladder_bound_partitions(view, route_order):
    """SC-1 判定范围=走阶梯的分区（与 execute_candidate 主循环分支谓词
    逐字同源：非 ribbon、非 fixed-shape、端点去重后 ≥2 点；route_order 序）。
    返回 [(pid, 去重端点列表)]。"""
    out = []
    for pid in route_order:
        partition = view.partitions[pid]
        if view.ribbon_partition(pid) or view.fixed_partition(pid):
            continue
        eps = _dedup_endpoints(partition["geometry"]["endpoints"])
        if len(eps) >= 2:
            out.append((pid, eps))
    return out


def _seal_survey_rows(ctx, route_order):
    """SC-1 普查（纯读数、零副作用、零 log 增量；V5-EXECUTOR-ENG-R1
    DESIGN §1.5）。逐 ladder 分区逐端点枚举 S(e)（_attachment_closure，
    含精确坐标），逐 (p, 信号层) 找封锁铜：只计 fixed: 前缀 ∧ 异网
    （ob.cu.net_id≠分区网）∧ 异分区（partition_id=None 两侧同视为不
    豁免）∧ 该层呈现者；谓词 ob.distance_blocked(p,p,r5−EPS) 与
    edge_blocked 的 R5 段判定同源同值（退化段与 _exhaustion_cause
    换层边同款用法）。候选障碍经粗网格 grid5 预滤（登记扩=R5=查询框
    超集，升序=提交序）。刻意不查孔带/板边带/R6 keepout/他网 route 铜
    （类纯度=铜封，宁漏判清单见 DESIGN §1.7）。返回逐端点行列表
    （route_order×端点序）。"""
    view = ctx.view
    r5 = view.r5_max   # V5-R7 W-2：保守 max 近似（任务书 §4 风险②首版；
                       # drc.max_net_class_clearance——缺类板=标量零漂移）
    layers = list(view.signal_layers)
    sp = ctx._spatial
    if sp is None or sp[0] != ctx._gen:
        sp = ctx._build_spatial()
    rows = []
    for pid, eps in _ladder_bound_partitions(view, route_order):
        partition = view.partitions[pid]
        net_id = view.net_of.get(pid, pid)
        try:
            width = _resolve_width(view, partition, pid)
        except ExecutorError:
            # 保守守卫（行为等价）：0.8.0 主循环只在其 route_order 轮到该
            # 分区时才解析宽度（先失败分区 break 则永不触达）——普查不提前
            # 抛、跳过该分区，成败/异常仍由主循环按原序决定
            continue
        for idx, e in enumerate(eps):
            pts = _attachment_closure(view, e)
            n_pairs = len(pts) * len(layers)
            sealed_pairs = 0
            sealing = set()
            for p in pts:
                for layer in layers:
                    blocker = None
                    for oi in _grid_query(sp[3].get(layer) or {},
                                          (p[0], p[1], p[0], p[1]), _GRID_CELL):
                        ob = ctx.obstacles[oi]
                        if not ob.cu.cid.startswith(FIXED_CID_PREFIX):
                            continue   # 只计板固有固定铜（rip_net 摘除面外）
                        if ob.cu.net_id == net_id:
                            continue   # 本网铜=合法连接（edge_blocked :877 同豁免）
                        if ob.partition_id is not None \
                                and ob.partition_id == pid:
                            continue   # 同分区铜（edge_blocked :882 同豁免；
                            # partition_id=None（band/既布铜）不豁免=保守方向）
                        if ob.cu.layer != layer:
                            continue
                        if ob.distance_blocked(p, p, r5 - clearance.EPS):
                            blocker = ob.cu.cid
                            break
                    if blocker is not None:
                        sealed_pairs += 1
                        sealing.add(blocker)
            rows.append({"partition": pid, "net": net_id, "endpoint": e,
                         "endpoint_index": idx, "n_points": len(pts),
                         "n_pairs": n_pairs, "sealed_pairs": sealed_pairs,
                         "sealed": sealed_pairs == n_pairs and n_pairs > 0,
                         "sealing_cids": sorted(sealing), "width": width})
    return rows


def _preflight_seal_shortcircuit(ctx, route_order, negotiation_log):
    """SC-1 事前短路判定（execute_candidate 入口、任何阶梯之前；判定时机/
    证明面见模块 docstring「V5-EXECUTOR-ENG-R1」节与 DESIGN §1.3/§1.4）。

    首个（route_order×端点序）S(e) 全 (p,层) 封死的端点 → cross-check：
    逐 (p,层) 断言 ctx.edge_blocked(L,p,p,net,pid,width,
    exempt_same_partition=True) is not None（最宽豁免档复核）；全同意 →
    落五行证据链（既有 FAILED 行前缀逐字保留：FAILED after N attempts/
    exhaustion-cause= 前缀兼容 build_g1_assessment 解析面）并返回 FAILED
    终局 dict（attempts=0、per_net 条目键集与穷举失败条目同构、无 routes
    工件）；任一不同意 → 弃权不短路（宁漏判不误杀；mismatch 披露行入
    log，回落正常阶梯）。零触发=零 log 增量（非密封板 negotiation_log
    与 0.8.0 逐字节相等）。"""
    rows = _seal_survey_rows(ctx, route_order)
    sealed = [r for r in rows if r["sealed"]]
    if not sealed:
        return None
    view = ctx.view
    layers = list(view.signal_layers)
    hit = sealed[0]
    pid = hit["partition"]
    net_id = hit["net"]
    width = hit["width"]
    e = hit["endpoint"]
    pts = _attachment_closure(view, e)
    total = len(pts) * len(layers)
    agree = 0
    for p in pts:
        for layer in layers:
            if ctx.edge_blocked(layer, p, p, net_id, pid, width,
                                exempt_same_partition=True) is not None:
                agree += 1
    if agree < total:
        negotiation_log.append(
            "net=%s partition=%s preflight-seal-abstain: cross_check "
            "mismatch sealed=%d agree=%d/%d（edge_blocked 复核不同意——"
            "弃权不短路，回落正常阶梯；宁漏判不误杀）"
            % (net_id, pid, total, agree, total))
        return None
    ladder_n = len(_ladder_bound_partitions(view, route_order))
    negotiation_log.append(
        "partition=%s preflight-seal-survey: ladder_partitions=%d"
        "（fixed-only-world，零 route 铜/零孔带/零板边带/零 keepout 计入；"
        "S=grid+exact）" % (pid, ladder_n))
    negotiation_log.append(
        "net=%s partition=%s FAILED after 0 attempts: constructive-unroutable"
        "（附着点位集（栅格+端点精确坐标）全层被异网固定铜 R5 封死，事前短路）"
        % (net_id, pid))
    negotiation_log.append(
        "net=%s partition=%s exhaustion-cause=sealed-short-circuit"
        "（全层异网固定铜密封构造性无解，事前短路类）" % (net_id, pid))
    negotiation_log.append(
        "net=%s partition=%s geom-secondary=%s"
        % (net_id, pid, _geom_secondary_attr(ctx, pid, net_id, width, e, e)))
    negotiation_log.append(
        "net=%s partition=%s short-circuit-basis: sealed_endpoint=e%d "
        "attachment_sealed=%d/%d points=grid:%d+exact:1 layers=all "
        "sealing_cids=%s cross_check=edge_blocked_agree=%d/%d "
        "immutable=rip_net-scope-fixed-not-removable"
        % (net_id, pid, hit["endpoint_index"], total, total, len(pts) - 1,
           ",".join(hit["sealing_cids"]), agree, total))
    _fev = getattr(ctx, "fail_events", None)
    if _fev is not None:   # R4-B：sealed_short_circuit 失败事件
        _fev.emit_sealed_short_circuit(
            ctx, pid, net_id, width, hit["endpoint_index"],
            hit["sealing_cids"], total, agree)
    per_net = [{"partition_id": pid, "net_id": net_id, "status": "failed",
                "attempts": 0, "negotiated": False, "vias": 0,
                "length_mm": 0.0, "width_mm": float(width), "layers": []}]
    return {"verdict": "FAILED", "routes": None, "per_net": per_net,
            "negotiation_log": negotiation_log}


# ---------------------------------------------------------------- 单线 A*

_RELAXED_REACHABLE = object()   # FX-3（0.13.0）：族可达早退标记（区别于
                                # 穷尽分量位集；独立哨兵防 dict.get 缺省歧义）
_RELAXED_CAPPED = object()      # FX-3：预算阀触发标记（该族放弃短路；并触发
                                # scale 地板——更细栅格族节点更多、必然同样
                                # 触帽，直接跳过预检省无谓 BFS；r21 实证）


def _hole_exempt_ids(ctx, pid):
    """D8 孔端点豁免索引集（FX-2a 预计算，0.13.0 起抽为模块函数——
    _edge_blocked_compute 与 FX-3 可达性预检共用同一缓存与容差语义：
    any(abs(hx-ex)≤1e-9 ∧ abs(hy-ey)≤1e-9)，逐字保留；eps_pts 缺席
    =空集=零豁免，与原「eps_pts is not None 才豁免」同值）。"""
    exempt = ctx._hole_exempt.get(pid)
    if exempt is None:
        eps_pts = ctx._pid_endpoints.get(pid)
        if eps_pts is None:
            exempt = frozenset()
        else:
            exempt = frozenset(
                hi for hi, (hx, hy, _hr) in enumerate(ctx.holes)
                if any(abs(hx - ex) <= 1e-9 and abs(hy - ey) <= 1e-9
                       for (ex, ey) in eps_pts))
        ctx._hole_exempt[pid] = exempt
    return exempt


def _endpoint_radii(view, pitch, ext_a, ext_b):
    """A* 豁免区半径簇（升级件① D1 缩放；_astar 与 FX-3 预检共用单一
    事实源——算式逐字同值）。"""
    r5 = view.r5_max
    base = int(math.ceil(r5 / pitch)) + 1
    return (max(base, int(math.ceil((ext_a + r5) / pitch)) + 1),
            max(base, int(math.ceil((ext_b + r5) / pitch)) + 1))


def _exempt_region_nodes(center_a, center_b, rad_a, rad_b, nx, ny):
    """两曼哈顿盘并集（同分区对腿共享端点豁免节点集；同上单一事实源，
    与 _astar 原 region() 逐集合同值）。"""
    out = set()
    for center, radius in ((center_a, rad_a), (center_b, rad_b)):
        if center is None:
            continue
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if abs(dx) + abs(dy) <= radius:
                    x2, y2 = center[0] + dx, center[1] + dy
                    if 0 <= x2 <= nx and 0 <= y2 <= ny:
                        out.add((x2, y2))
    return out


_RELAXED_EDGE_CAP = 1200000   # FX-3 精确边 BFS 的边检查预算阀（防大板
                              # 病理性 BFS 成本；触阀=放弃本族短路，健全
                              # 方向=零跳过零行为差；确定性计数。实测校准：
                              # badgeleds 族 BFS ~0.6M/bme280 ~0.15M（帽内
                              # 全收益）；syn2-r21 型 6 层 15 万格 ~7.2M 超帽
                              # 即弃（0.12.0 基线行为＋~秒级 BFS 探测成本，
                              # 阶段二实测 6M 帽在 r21 上 BFS 贵过节省、
                              # 回归 0.56×——帽收到 1.2M 修复）


def _relaxed_family_reached(ctx, pid, net_id, width, a_pt, b_pt,
                            plan_list, scale, vphase, assigned_layer,
                            endpoint_meta):
    """FX-3（0.13.0，engine-fix-r1 阶段二）：栅格族级**精确边**可达性预检。

    对 ladder 当前栅格族（scale×variant 相位）的全部逃逸计划，从全部
    起点锚（吸附节点×镜像起种层 li0）做多源 BFS，逐边用生产判定
    ctx.edge_blocked（与 FX-1 梯内 memo 共享缓存——BFS 先填、后续精确
    A* 命中）+ ctx.via_blocked。返回：
    - _RELAXED_REACHABLE：族内全部目标锚可达（早退）或触预算阀 →
      本族任何计划不允许短路；
    - frozenset：BFS 穷尽后的到达位集；某逃逸计划允许短路 ⟺ 其
      g_key（吸附目标节点）∉ 该集。

    健全性（误短路=静默改 verdict 高危，论证钉死）：本 BFS 图 ⊇ 任一
    变体的精确 A* 图，放宽项只有两个、全部只在精确侧减边：
    ① R2 档位检查不建模（near/overlap_free 两档皆 ⊂ R2-off）；
    ② 细档窗口剪枝不建模（窗口外邻边精确侧被剪）。
    其余逐边逐孔逐层**精确镜像** A* 判定（同一 ctx 状态=梯内冻结）：
    目标侧按 goal_pads 层约束记账（A* 收尾层的镜像）、起种层 li0 与
    A* 同式（首选层→焊盘层回退，含 D4）；同分区豁免取族内各计划豁免区
    并集（⊇ 任一单计划豁免区=最宽容）。
    ⇒ BFS 不可达 ⟹ 每个变体 A* 都不可达＝短路安全；短路行与 A* 耗尽
    行逐字节相同（negotiation_log 向后兼容红线）。
    确定性：seeds sorted、_DIRS8 固定序、FIFO 队列、预算计数确定性；
    集合仅作成员判定，判定结果与内部遍历序无关。"""
    view = ctx.view
    pitch = GRID_PITCH * scale
    phase = vphase * 0.5 * pitch
    nx, ny = _grid_limits(view, pitch, phase)
    if nx <= 0 or ny <= 0:
        return _RELAXED_REACHABLE
    layers = list(view.signal_layers)
    # —— li0 镜像（与 _astar 逐字同式）——
    if endpoint_meta is None:
        start_pads = _endpoint_pad_layer_set(view, pid, 0)
        ext_a = _endpoint_pad_extent(view, pid, 0)
        ext_b = _endpoint_pad_extent(view, pid, 1)
    else:
        start_pads = endpoint_meta[0][0]
        ext_a = endpoint_meta[0][1]
        ext_b = endpoint_meta[1][1]
    preferred = assigned_layer
    if preferred not in layers:
        preferred = layers[0]
    if start_pads is not None and preferred not in start_pads:
        preferred = next(l for l in layers if l in start_pads)
    li0 = layers.index(preferred)
    goal_pads = endpoint_meta[1][0] if endpoint_meta is not None         else _endpoint_pad_layer_set(view, pid, 1)
    rad_a, rad_b = _endpoint_radii(view, pitch, ext_a, ext_b)
    x0, y0 = view.workspace[0], view.workspace[1]

    def npt(ix, iy):
        return (x0 + ix * pitch + phase, y0 + iy * pitch + phase)

    seeds = set()
    targets = set()
    exempt_nodes = set()
    for _v, _sc, esc in plan_list:
        if _sc != scale or _v["phase"] != vphase or esc is None:
            continue
        s_pt = _escape_anchor(a_pt, esc, pitch, "start")
        g_pt = _escape_anchor(b_pt, esc, pitch, "goal")
        s_key = _snap_grid(view, s_pt, pitch, phase)
        g_key = _snap_grid(view, g_pt, pitch, phase)
        if s_key is not None:
            seeds.add((s_key[0], s_key[1], li0))
            exempt_nodes |= _exempt_region_nodes(s_key, g_key, rad_a, rad_b,
                                                 nx, ny)
        if g_key is not None:
            targets.add(g_key)
    if not seeds or not targets:
        return _RELAXED_REACHABLE
    reached = set()
    remaining = set(targets)
    visited = set(seeds)
    queue = list(sorted(seeds))
    for six, siy, _l in queue:
        reached.add((six, siy))
    budget = _RELAXED_EDGE_CAP
    head = 0
    nl = len(layers)
    while head < len(queue) and remaining:
        ix, iy, li = queue[head]
        head += 1
        layer = layers[li]
        p = npt(ix, iy)
        p_in = (ix, iy) in exempt_nodes
        for dx, dy in _DIRS8:
            jx, jy = ix + dx, iy + dy
            if not (0 <= jx <= nx and 0 <= jy <= ny)                     or (jx, jy, li) in visited:
                continue
            budget -= 1
            if budget < 0:
                return _RELAXED_CAPPED   # 预算阀：放弃短路（零跳过+设地板）
            if ctx.edge_blocked(
                    layer, p, npt(jx, jy), net_id, pid, width,
                    exempt_same_partition=p_in
                    and (jx, jy) in exempt_nodes) is None:
                visited.add((jx, jy, li))
                queue.append((jx, jy, li))
                if (jx, jy) not in reached:
                    reached.add((jx, jy))
                if (jx, jy) in remaining and (goal_pads is None
                                              or layer in goal_pads):
                    remaining.discard((jx, jy))
        if ctx.via_blocked(p, net_id) is None:
            for lj in range(nl):
                if lj == li or (ix, iy, lj) in visited:
                    continue
                budget -= 1
                if budget < 0:
                    return _RELAXED_CAPPED
                if ctx.edge_blocked(
                        layers[lj], p, p, net_id, pid, width,
                        exempt_same_partition=p_in) is None:
                    visited.add((ix, iy, lj))
                    queue.append((ix, iy, lj))
                    if (ix, iy) not in reached:
                        reached.add((ix, iy))
                    if (ix, iy) in remaining and (goal_pads is None
                                                  or layers[lj] in goal_pads):
                        remaining.discard((ix, iy))
    if remaining:
        return frozenset(targets - remaining)
        # 穷尽：返回**已按 goal_pads 层约束满足**的目标锚集——不在集内
        # 的逃逸计划=精确 A* 必然耗尽，允许短路
    return _RELAXED_REACHABLE      # 全目标可达（早退）：本族零短路

def _r2_edge_blocked(view, p, q, mode):
    """R2 边档检查（v5.drc.check_ana_proximity 整线累计语义的保守实现）。

    "near"：段距 < min_distance 且该段有投影重叠 → 封；
    "overlap_free"：该段有投影重叠（无论距离）→ 封。
    任一档被接受的路径，其折线在敏感区的投影重叠累计为 0（档内规则保证），
    v5.drc 累计平行长度 ≤ max_parallel 必然成立；真实判定仍由网级 v5.drc 门与
    route_check 终检作出（A9）。

    0.12.0 FX-2c（engine-fix-r1 阶段一）：无敏感区短路——rects 为空时原循环
    体零迭代恒返 False，本快路同值同返（profile 实证：敏感区空表板仍付
    22M–81M 次/板的函数调用成本；等价依据/验证同 FX-2b 注记）。"""
    rects = view.sensitive_rect_ds
    if not rects:
        return False
    r2 = view.hard_rules.get("R2", {})
    r2_min = float(r2.get("min_distance_mm", 3.0))
    for rect_d in rects:
        if mode == "near":
            d = clearance.segment_rect_distance(p, q, rect_d)
            if d >= r2_min:
                continue
        par = 0.0
        if abs(p[1] - q[1]) <= clearance.EPS:
            lo, hi = sorted((p[0], q[0]))
            par = max(0.0, min(hi, rect_d["x_max"]) - max(lo, rect_d["x_min"]))
        elif abs(p[0] - q[0]) <= clearance.EPS:
            lo, hi = sorted((p[1], q[1]))
            par = max(0.0, min(hi, rect_d["y_max"]) - max(lo, rect_d["y_min"]))
        if par > 0.0:
            return True
    return False


def _grid_limits(view, pitch, phase):
    """栅格规模（nx, ny）——workspace 内相位平移栅格的节点索引上限。"""
    _x0, _y0, x1, y1 = view.workspace
    nx = int(math.floor((x1 - _x0) / pitch - phase / pitch + 1e-9))
    ny = int(math.floor((y1 - _y0) / pitch - phase / pitch + 1e-9))
    return nx, ny


def _endpoint_pad_layer_set(view, pid, endpoint_idx):
    """端点焊盘层集合（D4 端点层约束；route_check._BoardView 归一）：
    None=该端点无焊盘项（不约束）；有则限信号层。"""
    sets = view.endpoint_pad_layers.get(pid)
    if not sets:
        return None
    sig = set(sets[endpoint_idx] or ()) & set(view.signal_layers)
    return sig or None


def _endpoint_pad_extent(view, pid, endpoint_idx):
    """端点焊盘最大半尺寸（D1 同分区豁免区缩放用；无焊盘项=0）。"""
    ext = 0.0
    for item in view.pad_items.get(pid, ()):
        if item["endpoint"] == endpoint_idx:
            ext = max(ext, float(max(item["size"])) / 2.0)
    return ext


def _via_min_hole(view):
    """D3 最小孔心距 = 2·孔半径 + R5.min_clearance_mm。"""
    r5 = view.r5_max   # V5-R7 W-2：保守 max 近似（任务书 §4 风险②首版；
                       # drc.max_net_class_clearance——缺类板=标量零漂移）
    return 2.0 * float(view.via_radius) + r5


def _return_via_offsets(min_hole, max_dist, pitch):
    """D3 回流孔错位候选（升级件⑤ F2 扩容枚举域；确定性全序（距离, 家族序,
    方向序））：半径按 pitch/2 细步进（向 R4 上限渐进），16 方向三族（轴向/
    对角/马步——马步补齐轴向↔对角两侧角域=双侧锚点偏移备选）；约束一律不
    放松：仅收孔心距 ≥min_hole 且 ≤max_dist 者（旧 0.25mm/8 向枚举域是新域
    子集）。返回 [(dx, dy)...] 偏移向量列表（落 pitch/2 子栅格）。"""
    step = pitch * _RETURN_VIA_SUBSTEP
    cands = []
    for fam, dirs in enumerate(_RETURN_VIA_FAMILIES):
        k = 1
        while True:
            ax = k * step
            dist = math.hypot(dirs[0][0], dirs[0][1]) * ax
            if dist > max_dist + clearance.EPS:
                break
            k += 1
            if dist < min_hole - clearance.EPS:
                continue
            for j, (ux, uy) in enumerate(dirs):
                cands.append((dist, fam, j, ux * ax, uy * ax))
    cands.sort(key=lambda c: (round(c[0], 9), c[1], c[2]))
    return [(c[3], c[4]) for c in cands]


def _snap_grid(view, p, pitch, phase):
    """精确点 → 栅格节点索引（最近节点、workspace 夹紧）；无有效栅格 → None。
    _astar 与尝试计划去重共用（单一事实源，防口径漂移）。"""
    nx, ny = _grid_limits(view, pitch, phase)
    if nx <= 0 or ny <= 0:
        return None
    x0, y0, _x1, _y1 = view.workspace
    ix = int(math.floor((p[0] - x0 - phase) / pitch + 0.5))
    iy = int(math.floor((p[1] - y0 - phase) / pitch + 0.5))
    return (max(0, min(nx, ix)), max(0, min(ny, iy)))


def _escape_anchor(e, escape, pitch, side):
    """阶梯计划对端点 e 的搜索锚点（未吸附；单一位移事实源）：
    escape=None 或 side 不匹配 → e 精确坐标；否则按 (side, (dx,dy), rad)
    平移 rad·pitch 格。V5-EXECUTOR-ENG-R1 W-1 抽因子（DESIGN §1.2）：
    _run_attempt_ladder 的端点位移与 SC-1 附着闭包消费同一本函数——
    纯等价重构（位移算式逐字同值），闭包精确性由构造保证。"""
    if escape is None or escape[0] != side:
        return (float(e[0]), float(e[1]))
    _side, (dx, dy), rad = escape
    return (float(e[0]) + dx * rad * pitch, float(e[1]) + dy * rad * pitch)


def _attachment_closure(view, e):
    """端点 e 的附着点位闭包 S(e)=S_grid(e)∪{e 精确坐标}（V5-EXECUTOR-ENG-R1
    W-1；DESIGN §1.2 单一事实源）。S_grid(e)=阶梯全部计划（_attempt_plans）
    对端点 e 的吸附锚点节点集：escape side=start/goal 只位移对应侧锚点
    （_escape_anchor），锚点经 _snap_grid 吸附到 (pitch, phase) 栅格
    （phase=variant.phase·0.5·pitch，细档变体集=_FINE_VARIANTS 仅 0.0），
    节点坐标=工作区原点平移格（_astar.node_pt 同式）。精确坐标项=M3
    直连/胶合附着（_astar 同格直连段 + _entries_from_runs 端点回贴——
    工件折线的电气附着终点恒为原始端点精确坐标，与档位/相位/逃逸无关）。
    返回升序去重点位列表（含精确坐标项）；纯函数零副作用。"""
    pts = set()
    x0, y0 = view.workspace[0], view.workspace[1]
    for variant, scale, escape in _attempt_plans():
        pitch = GRID_PITCH * scale
        phase = variant["phase"] * 0.5 * pitch
        for side in ("start", "goal"):
            anchor = _escape_anchor(e, escape, pitch, side)
            key = _snap_grid(view, anchor, pitch, phase)
            if key is not None:
                pts.add((x0 + key[0] * pitch + phase,
                         y0 + key[1] * pitch + phase))
    pts.add((float(e[0]), float(e[1])))
    return sorted(pts)


def _astar(ctx, pid, net_id, width, start_pt, goal_pt, preferred_layer, variant,
           pitch=GRID_PITCH, window=None, endpoint_meta=None):
    """多信号层 8 连通 A*（网格 pitch，缺省 0.25mm；R2 以 variant["r2"] 档位
    保守引导）。返回 (seq, vias) 或 None：
    seq = [(pt, layer_id)...] 逐节点序列（含纯过孔 stub 节点）；
    vias = 层切换点去重列表（唯一孔位）。
    确定性：heapq 键 (f, h, counter)；邻域固定展开序；无随机无时钟。
    pitch 形参（升级件④）：尝试阶梯的细化栅格阶段以 pitch=0.125 复用本搜索——
    只改栅格密度，边合法性谓词零改动（不放松任何硬规则）。
    window 形参（升级件⑤ F4a）：细档（0.0625mm）搜索的确定性限域窗口——
    栅格相位仍锚定工作区原点（同一 lattice 的子矩形），窗口外邻边一律剪枝，
    边合法性谓词零改动；语义=局部细化搜索（细档价值在端点/薄门的局部缝隙，
    全板细搜与粗档全板阶梯冗余且代价 16×，窗口披露于 _fine_window）。
    升级件①：换层边经 ctx.via_blocked（孔铜严格 R5/R6/D3 孔心距，无同分区
    豁免）；起种层/收尾层受端点焊盘层集合约束（D4 端点层约束）；同分区豁免
    区半径按端点焊盘半尺寸+R5 扩（D1 共享端子区）。
    """
    view = ctx.view
    layers = list(view.signal_layers)
    # V5-R1 W-4：端点约束注入（None=原 0/1 焊盘查询，2 端网行为零差）——
    # 多点网拓扑边端点的层集（Steiner 点=已布层账连通融合/pad k=焊盘层集）
    # 与豁免半径簇（Steiner=铜半宽）；搜索语义（D4/D1 机制）零改。
    if endpoint_meta is None:
        start_pads = _endpoint_pad_layer_set(view, pid, 0)
        goal_pads = _endpoint_pad_layer_set(view, pid, 1)
        ext_a = _endpoint_pad_extent(view, pid, 0)
        ext_b = _endpoint_pad_extent(view, pid, 1)
    else:
        start_pads = endpoint_meta[0][0]
        goal_pads = endpoint_meta[1][0]
        ext_a = endpoint_meta[0][1]
        ext_b = endpoint_meta[1][1]
    if preferred_layer not in layers:
        preferred_layer = layers[0]
    if start_pads is not None and preferred_layer not in start_pads:
        # D4 端点层约束：首选层不在起点焊盘层集合 → 起种于首个焊盘层
        #（首选层经换层孔回归，软先验价格机制不变）
        preferred_layer = next(l for l in layers if l in start_pads)
    li0 = layers.index(preferred_layer)
    phase = variant["phase"] * 0.5 * pitch
    x0, y0, x1, y1 = view.workspace
    nx, ny = _grid_limits(view, pitch, phase)
    if nx <= 0 or ny <= 0:
        return None

    def node_pt(ix, iy):
        return (x0 + ix * pitch + phase, y0 + iy * pitch + phase)

    def snap(p):
        return _snap_grid(view, p, pitch, phase)

    if window is not None:
        wx0, wy0, wx1, wy1 = window

        def out_of_window(p):
            return not (wx0 <= p[0] <= wx1 and wy0 <= p[1] <= wy1)
    else:
        def out_of_window(_p):
            return False

    start = snap(start_pt)
    goal = snap(goal_pt)
    gx, gy = goal
    # 同分区对腿的共享端点豁免半径（升级件① D1 缩放）：R5+1 格与
    # 端点焊盘半尺寸+R5+1 格取大——多网共分区的端点焊盘几何重合，两腿须经
    # 共享端子区（焊盘+R5 光晕）进出；异分区铜不受豁免。
    r5 = view.r5_max   # V5-R7 W-2：保守 max 近似（任务书 §4 风险②首版；
                       # drc.max_net_class_clearance——缺类板=标量零漂移）
    # 0.13.0 FX-3：豁免区半径簇与节点并集抽为 _endpoint_radii/
    # _exempt_region_nodes（与可达性预检共用单一事实源；算式逐字同值=
    # 纯等价重构）
    rad_a, rad_b = _endpoint_radii(view, pitch, ext_a, ext_b)
    exempt_nodes = _exempt_region_nodes(start, goal, rad_a, rad_b, nx, ny)

    cm = dict(DEFAULT_COST_MODEL)
    via_cost = cm["via_cost"] if variant["via_cost"] is None else float(variant["via_cost"])
    ret_cost = cm["return_cost"] if variant["via_cost"] is None else 0.0
    dir_rate = cm["direction_rate"]
    r2_mode = variant["r2"]

    def h(ix, iy):
        dx, dy = abs(ix - gx), abs(iy - gy)
        return (max(dx, dy) + (_SQRT2 - 1.0) * min(dx, dy)) * pitch

    def cost(layer, p, q):
        d = view.layer_directions.get(layer, "any")
        wrong = 0.0
        if d == "h":
            wrong = abs(q[1] - p[1])
        elif d == "v":
            wrong = abs(q[0] - p[0])
        return math.hypot(q[0] - p[0], q[1] - p[1]) + dir_rate * wrong

    counter = 0
    heap = [(h(*start), 0.0, counter, start[0], start[1], li0)]
    counter += 1
    came = {}
    gbest = {(start[0], start[1], li0): 0.0}
    found = None
    while heap:
        f, _hh, _c, ix, iy, li = heapq.heappop(heap)
        state = (ix, iy, li)
        g = gbest.get(state)
        if g is None or f > g + h(ix, iy) + 1e-9:
            continue   # 过期堆项
        if (ix, iy) == (gx, gy):
            if goal_pads is None or layers[li] in goal_pads:
                found = state
                break
            # D4 端点层约束：goal 层不在焊盘层集合 → 不收，继续扩展
            #（需经端点过孔换到焊盘层）
        p = node_pt(ix, iy)
        layer = layers[li]
        in_region = (ix, iy) in exempt_nodes
        # 8 连通
        for dx, dy in _DIRS8:
            jx, jy = ix + dx, iy + dy
            if not (0 <= jx <= nx and 0 <= jy <= ny):
                continue
            q = node_pt(jx, jy)
            if out_of_window(q):
                continue   # F4a 细档限域窗口（同一 lattice 子矩形，谓词零改动）
            if _r2_edge_blocked(view, p, q, r2_mode):
                continue
            blocked = ctx.edge_blocked(
                layer, p, q, net_id, pid, width,
                exempt_same_partition=in_region and (jx, jy) in exempt_nodes)
            if blocked:
                continue
            ng = g + cost(layer, p, q)
            nstate = (jx, jy, li)
            if ng < gbest.get(nstate, float("inf")) - 1e-12:
                gbest[nstate] = ng
                came[nstate] = state
                counter += 1
                heapq.heappush(heap, (ng + h(jx, jy), h(jx, jy), counter, jx, jy, li))
        # 层间过渡（过孔）：同 (x,y) 换层——孔铜严格判定（D2，无同分区豁免）。
        # R1 性能件（A1）：via_blocked(p,net_id) 与 _r2_edge_blocked(view,p,p,mode)
        # 为 for lj 循环不变量（仅依赖 p/net/mode）——提出循环一次判定，被拒即
        # 整组层跳过，与逐层 continue 等价（代数等价，主审核准）。
        if out_of_window(p):
            continue
        if ctx.via_blocked(p, net_id) is None and \
                not _r2_edge_blocked(view, p, p, r2_mode):
            h_here = h(ix, iy)   # 循环不变量（同 (ix,iy) 同值）
            for lj in range(len(layers)):
                if lj == li:
                    continue
                blocked = ctx.edge_blocked(
                    layers[lj], p, p, net_id, pid, width,
                    exempt_same_partition=in_region)
                if blocked:
                    continue
                ng = g + via_cost + ret_cost
                nstate = (ix, iy, lj)
                if ng < gbest.get(nstate, float("inf")) - 1e-12:
                    gbest[nstate] = ng
                    came[nstate] = state
                    counter += 1
                    heapq.heappush(heap, (ng + h_here, h_here, counter,
                                          ix, iy, lj))
    if found is None:
        return None

    # 回溯 → 节点序列（含纯过孔 stub）
    nodes = [found]
    while nodes[-1] in came:
        nodes.append(came[nodes[-1]])
    nodes.reverse()
    seq = [(node_pt(ix, iy), layers[li]) for ix, iy, li in nodes]
    vias = []
    for k in range(1, len(seq)):
        if seq[k][1] != seq[k - 1][1] and seq[k][0] not in vias:
            vias.append(seq[k][0])
    if len(seq) == 1:
        # 起终点同栅格：直连段（合法性在此显式核对）
        a, b = tuple(start_pt), tuple(goal_pt)
        if a != b and (_r2_edge_blocked(view, a, b, r2_mode) or
                       ctx.edge_blocked(seq[0][1], a, b, net_id, pid, width,
                                        exempt_same_partition=True)):
            return None
    return seq, vias



def _place_return_via(ctx, via_pt, net_id, pid, width, adjacent_layers, own_vias):
    """确定性回流孔位（升级件① D3/D4；升级件⑤ F2 扩容枚举域）：错位候选
    环序（_return_via_offsets：pitch/2 细半径档 × 16 方向三族，孔心距
    ≥ 2·孔半径+R5、偏移 ≤ R4.max_distance_mm，确定性全序）；孔位经
    ctx.via_blocked（R6 禁布 + 异网铜 R5 **无同分区豁免** + 对已提交孔点
    最小孔心距）+ 对本尝试孔点（全部过渡孔与已置回流孔）D3 核对；D4 桩段
    T→R 逐相邻层边合法性核对（严格档失败再试同分区豁免档——端点邻域的
    共享端子区，与折线边同款两档）。第一有效候选胜。
    """
    view = ctx.view
    x0, y0, x1, y1 = view.workspace
    min_hole = _via_min_hole(view)
    max_d = float(view.hard_rules.get("R4", {}).get("max_distance_mm", 2.0))
    for dx, dy in _return_via_offsets(min_hole, max_d, GRID_PITCH):
        p = (via_pt[0] + dx, via_pt[1] + dy)
        if not (x0 <= p[0] <= x1 and y0 <= p[1] <= y1):
            continue
        if ctx.via_blocked(p, net_id) is not None:
            continue
        if any(clearance.point_point(p, q) < min_hole - clearance.EPS
               for q in own_vias):
            continue
        if not all(ctx.edge_blocked(lay, via_pt, p, net_id, pid, width) is None
                   for lay in adjacent_layers) and not all(
                ctx.edge_blocked(lay, via_pt, p, net_id, pid, width,
                                 exempt_same_partition=True) is None
                for lay in adjacent_layers):
            continue
        return p
    return None


def _via_adjacent_layers(seq, vias):
    """层切换点的相邻层集合（D4 桩段落层用）：{(x, y): set(layers)}。"""
    out = {}
    for k in range(1, len(seq)):
        if seq[k][1] != seq[k - 1][1]:
            out.setdefault(seq[k][0], set()).update((seq[k - 1][1], seq[k][1]))
    for vp in vias:
        out.setdefault(vp, set())
    return out


def _entries_from_runs(ctx, pid, net_id, width, start_pt, goal_pt, seq, vias):
    """节点序列 → route entries（+回流孔错位定位与 D4 桩段；合同见模块 docstring）。

    纯过孔 stub 段（单点）不产出 entry，其孔位由相邻存续 run 披露；首个/末个
    存续 run 贴回精确分区端点（部分段合法性在此核对）；R4/D3 无法配孔 / 部分
    段被封 / 本尝试孔对最小孔心距不足 → (None, 原因)。
    升级件①：每过渡孔的回流孔以 [T,R,T] 桩段入相邻两层 entry（R=折线顶点、
    双侧相连——kicad 无悬空）；单点 stub 层提升为 [T,R,T] entry（换层端点
    的另一层铜保证）。
    """
    via_layers = _via_adjacent_layers(seq, vias)
    min_hole = _via_min_hole(ctx.view)
    ret_of = {}
    own_vias = list(vias)
    for vp in vias:
        rp = _place_return_via(ctx, vp, net_id, pid, width,
                               sorted(via_layers.get(vp, ())), own_vias)
        if rp is None:
            return None, ("R4/D3 回流孔无处安置（错位+双侧相连约束下无有效位）"
                          "@%s" % (vp,))
        ret_of[vp] = rp
        own_vias.append(rp)
    # D3 本尝试孔对核对（A* 状态不含孔史，过渡-过渡对在此强制）
    for i in range(len(own_vias)):
        for j in range(i + 1, len(own_vias)):
            if clearance.point_point(own_vias[i], own_vias[j]) < \
                    min_hole - clearance.EPS:
                return None, ("D3 孔对最小孔心距不足（%.3f < %.3f）@%s↔%s"
                              % (clearance.point_point(own_vias[i], own_vias[j]),
                                 min_hole, own_vias[i], own_vias[j]))
    # 切 maximal 同层段（含纯过孔 stub）
    runs = []
    for pt, layer in seq:
        if runs and runs[-1][0] == layer:
            if runs[-1][1][-1] != pt:
                runs[-1][1].append(pt)
        else:
            runs.append([layer, [pt]])
    # 单点 stub 提升（D4）：换层点上的单点 run → [T, R, T] entry（另一层铜）
    promoted = set()
    for k, r in enumerate(runs):
        if len(r[1]) == 1 and r[1][0] in ret_of:
            r[1] = [r[1][0], ret_of[r[1][0]], r[1][0]]
            promoted.add(k)
    # 首/末存续段贴回精确端点（stub 段跳过）
    emitted_idx = [k for k, r in enumerate(runs) if len(r[1]) >= 2]
    if not emitted_idx:
        # 起终点同栅格：直连段（合法性在此显式核对）
        a, b = tuple(start_pt), tuple(goal_pt)
        if a == b:
            return None, "端点退化重合"
        if ctx.edge_blocked(runs[0][0] if runs else list(ctx.view.signal_layers)[0],
                            a, b, net_id, pid, width,
                            exempt_same_partition=True):
            return None, "端点直连段被封（R5/R6/R2/容量）"
        runs[0][1] = [a, b]
        emitted_idx = [0]
    first_k, last_k = emitted_idx[0], emitted_idx[-1]
    a, b = tuple(start_pt), tuple(goal_pt)
    if a != runs[first_k][1][0]:
        if ctx.edge_blocked(runs[first_k][0], a, runs[first_k][1][0], net_id, pid,
                            width, exempt_same_partition=True):
            return None, "端点→首栅格部分段被封（%s）" % runs[first_k][0]
        runs[first_k][1].insert(0, a)
    if b != runs[last_k][1][-1]:
        if ctx.edge_blocked(runs[last_k][0], runs[last_k][1][-1], b, net_id, pid,
                            width, exempt_same_partition=True):
            return None, "末栅格→端点部分段被封（%s）" % runs[last_k][0]
        runs[last_k][1].append(b)
    # 产出 entry（D4 桩段折线：段端为孔点者插入 [T,R,T] 折返；stub 已提升）
    entries, coppers = [], []
    for k, (layer, pts_) in enumerate(runs):
        if len(pts_) < 2:
            continue   # 纯过孔 stub：无 entry（未提升=无回流孔挂靠，不可能）
        tv, rv = [], []
        seen_joint = set()
        for end_pt in (pts_[0], pts_[-1]):
            if end_pt in ret_of and end_pt not in seen_joint:
                seen_joint.add(end_pt)
                tv.append([end_pt[0], end_pt[1]])
                rv.append([ret_of[end_pt][0], ret_of[end_pt][1]])
        poly = [list(p) for p in pts_]
        if k not in promoted:
            if pts_[0] in ret_of:
                r_pt = ret_of[pts_[0]]
                poly = [poly[0], [r_pt[0], r_pt[1]]] + poly
            if pts_[-1] in ret_of:
                r_pt = ret_of[pts_[-1]]
                poly = poly + [[r_pt[0], r_pt[1]], poly[-1]]
        entry = {
            "partition_id": pid,
            "net_id": net_id,
            "layer": layer,
            "polyline": poly,
            "width": float(width),
            "transition_vias": tv,
            "return_vias": rv,
        }
        entries.append(entry)
        coppers.append(_RouteCopper(
            net_id, "%s%s:%s#%d" % (ROUTE_CID_PREFIX, net_id, pid, k),
            layer, pid, entry["polyline"], width))
    if not entries:
        return None, "无有效路线段"
    return (entries, coppers), None


# ---------------------------------------------------------------- 宽度/形状

def _fine_window(view, a_pt, b_pt, s_pt, g_pt):
    """F4a 细档限域窗口（确定性）：直连端点与本次尝试吸附锚点的 bbox 外扩
    _FINE_WINDOW_MARGIN_MM、夹紧到工作区。细档价值=端点/薄门局部缝隙，全板
    细搜与粗档全板阶梯冗余（代价 16×）；窗口外路径由粗档全板计划覆盖。"""
    x0, y0, x1, y1 = view.workspace
    m = _FINE_WINDOW_MARGIN_MM
    xs = (float(a_pt[0]), float(b_pt[0]), float(s_pt[0]), float(g_pt[0]))
    ys = (float(a_pt[1]), float(b_pt[1]), float(s_pt[1]), float(g_pt[1]))
    return (max(x0, min(xs) - m), max(y0, min(ys) - m),
            min(x1, max(xs) + m), min(y1, max(ys) + m))


def _run_attempt_ladder(ctx, pid, net_id, width, a_pt, b_pt, assigned_layer,
                        negotiation_log, plans=None, endpoint_meta=None):
    """单网一次完整尝试阶梯（升级件⑤ F4 从 execute_candidate 提取，供
    F4c rip-up 重布复用；计划序/日志行格式与 0.3.0 逐字节一致——
    negotiation_log 向后兼容红线）。plans=None=完整阶梯；调用方可传入
    计划前缀（F4c 被 rip 网有界重布，常量披露）。
    endpoint_meta（V5-R1 W-4）：((start_layers, start_extent),
    (goal_layers, goal_extent)) 端点约束注入（多点网拓扑边端点）；None=
    原 0/1 焊盘查询（2 端网既有路径，注入等值=行为零差）。

    持有本网 staging 事务：成功 stage+commit 并返回
    (True, attempts, reason, entries, vias_n)；全耗尽则 rollback（状态指纹
    断言）并返回 (False, attempts, reason, None, 0)。
    """
    tx = _NetTransaction(ctx, net_id, pid)
    state_before = ctx.state_key()
    attempts = 0
    reason = "搜索空间耗尽"
    tried = set()
    # 0.12.0 FX-1（engine-fix-r1 阶段一）：梯内判定 memo 激活——作用域=本
    # 函数调用。作用域内场景冻结（失败尝试 stage→discard 不触 ctx；成功
    # attempt commit 后即刻 return，不再消费判定面——已核验：本梯内全部
    # edge_blocked/via_blocked 消费点（_astar/_entries_from_runs/
    # _place_return_via 直连与桩段核对）均在 stage/commit 之前）；同一
    # (net_id, pid, width) 恒定。finally 保证任何路径（含异常）关闭。
    ctx._eb_memo, ctx._vb_memo = {}, {}
    ctx._eb_memo_args = (net_id, pid, width)
    ctx._relaxed_cache = {}
    _fam = None
    plan_list = plans if plans is not None else _attempt_plans()
    try:
        for variant, scale, escape in plan_list:
            # 0.12.0 FX-1b：栅格族（scale×variant 相位）切换即清 memo——
            # 跨族键为不同 lattice 的不同浮点、占槽不命中（profile 实证：
            # badgeleds 帽饱和时整体命中率 35% vs bme280 未饱和 91%）；
            # 清出容量给当前族。清除只影响时序不影响结果=纯缓存策略，
            # 字节等契约不变。
            _fam_new = (scale, variant["phase"])
            if _fam_new != _fam:
                ctx._eb_memo.clear()
                ctx._vb_memo.clear()
                ctx._relaxed_cache.clear()
                _fam = _fam_new
            pitch = GRID_PITCH * scale
            phase = variant["phase"] * 0.5 * pitch
            # V5-EXECUTOR-ENG-R1 W-1：位移逻辑走 _escape_anchor 单一事实源
            # （与 SC-1 附着闭包同源；算式逐字同值=纯等价重构）
            s_pt = _escape_anchor(a_pt, escape, pitch, "start")
            g_pt = _escape_anchor(b_pt, escape, pitch, "goal")
            esc_label = ""
            if escape is not None:
                _side, (dx, dy), rad = escape
                esc_label = " escape=%s:(%+d,%+d)r%d" % (_side, dx, dy, rad)
            pitch_label = "" if scale == 1.0 else " pitch=%g" % pitch
            s_key = _snap_grid(ctx.view, s_pt, pitch, phase)
            g_key = _snap_grid(ctx.view, g_pt, pitch, phase)
            if s_key is not None and g_key is not None:
                dedupe = (scale, s_key, g_key, _attempt_label(variant))
                if dedupe in tried:
                    continue   # 吸附等价计划不重跑（不计 attempts）
                tried.add(dedupe)
            attempts += 1
            _progress = getattr(ctx, "progress", None)
            if _progress is not None:   # OPT-09：attempt 边界到达（计划 N 开跑
                _progress.emit_work(     # =引擎线程实际推进到该尝试边界）
                    "attempt", partition_id=pid, net_id=net_id,
                    attempt=attempts, scale=scale, escape=(escape is not None))
            window = None
            if scale == _FINE_SCALE:
                window = _fine_window(ctx.view, a_pt, b_pt, s_pt, g_pt)
            # 0.13.0 FX-3（engine-fix-r1 阶段二）：乐观可达性预检——仅逃逸
            # 计划（escape-only 门：直连计划与 attempt=1 成功网零接触零
            # 回归）；族级一次多源 BFS（键=当前族），逐计划 O(1) 判定。
            # 短路=该计划精确 A* 不可能成功（健全性论证见
            # _relaxed_family_reached docstring），照常输出与 A* 耗尽
            # 逐字节相同的失败行（negotiation_log 向后兼容红线）。
            if escape is not None and s_key is not None \
                    and g_key is not None and s_key != g_key \
                    and scale >= ctx._relaxed_scale_floor:
                _relaxed = ctx._relaxed_cache.get(_fam, _MEMO_MISS)
                if _relaxed is _MEMO_MISS:
                    _relaxed = _relaxed_family_reached(
                        ctx, pid, net_id, width, a_pt, b_pt,
                        plan_list, scale, variant["phase"],
                        assigned_layer, endpoint_meta)
                    ctx._relaxed_cache[_fam] = _relaxed
                if _relaxed is _RELAXED_CAPPED:
                    if ctx._relaxed_scale_floor < scale:
                        ctx._relaxed_scale_floor = scale
                    _relaxed = _RELAXED_REACHABLE   # 触帽族零短路
                if _relaxed is not _RELAXED_REACHABLE \
                        and g_key not in _relaxed:
                    reason = "A* 搜索空间耗尽（障碍/容量/敏感约束下无路）"
                    negotiation_log.append(
                        "net=%s partition=%s attempt=%d variant=%s%s%s"
                        " failed: %s"
                        % (net_id, pid, attempts, _attempt_label(variant),
                           pitch_label, esc_label, reason))
                    continue
            result = _astar(ctx, pid, net_id, width, s_pt, g_pt,
                            assigned_layer, variant, pitch, window,
                            endpoint_meta=endpoint_meta)
            if result is None:
                reason = "A* 搜索空间耗尽（障碍/容量/敏感约束下无路）"
                negotiation_log.append(
                    "net=%s partition=%s attempt=%d variant=%s%s%s failed: %s"
                    % (net_id, pid, attempts, _attempt_label(variant),
                       pitch_label, esc_label, reason))
                continue
            seq, vias = result
            packed, r4_reason = _entries_from_runs(ctx, pid, net_id, width,
                                                   a_pt, b_pt, seq, vias)
            if packed is None:
                reason = r4_reason
                negotiation_log.append(
                    "net=%s partition=%s attempt=%d variant=%s%s%s failed: %s"
                    % (net_id, pid, attempts, _attempt_label(variant),
                       pitch_label, esc_label, reason))
                continue
            entries, coppers = packed
            tx.stage(entries, coppers)
            gate = _net_gate(ctx, pid, net_id, coppers)
            if gate is not None:
                reason = gate
                negotiation_log.append(
                    "net=%s partition=%s attempt=%d variant=%s%s%s failed: %s"
                    % (net_id, pid, attempts, _attempt_label(variant),
                       pitch_label, esc_label, gate))
                tx.discard()
                continue
            tx.commit()
            negotiation_log.append(
                "net=%s partition=%s committed attempt=%d variant=%s%s%s%s"
                % (net_id, pid, attempts, _attempt_label(variant),
                   pitch_label, esc_label,
                   "（协商兜底生效）" if attempts > 1 else ""))
            # D3 错位决策披露（升级件①）：孔数/各孔错位向量/最小孔心距
            if vias:
                tv_all = [tuple(v) for e in entries
                          for v in e["transition_vias"]]
                via_rows = []
                for e in entries:
                    for tv, rv in zip(e["transition_vias"], e["return_vias"]):
                        via_rows.append("tv(%g,%g)→rv(%g,%g)+%g"
                                        % (tv[0], tv[1], rv[0], rv[1],
                                           math.hypot(rv[0] - tv[0],
                                                      rv[1] - tv[1])))
                negotiation_log.append(
                    "net=%s partition=%s via-plan: %d 过渡孔错位 %s"
                    "（D3 最小孔心距 %.2fmm）"
                    % (net_id, pid, len(set(tv_all)),
                       "; ".join(via_rows), _via_min_hole(ctx.view)))
            return True, attempts, reason, entries, len(vias)
        tx.rollback()
        if ctx.state_key() != state_before:
            raise ExecutorError("transaction", "回滚后状态指纹不一致（内部错误）")
        return False, attempts, reason, None, 0
    finally:
        ctx._eb_memo = None
        ctx._vb_memo = None
        ctx._eb_memo_args = None
        ctx._relaxed_cache = None


# ------------------------------------------------- V5-R1 W-4 多端网逐边面

def _dedup_endpoints(ends):
    """端点序列去重保序（浮点精确相等；多点网退化判定/孔豁免支撑件）。"""
    seen = set()
    out = []
    for pt in ends:
        key = (float(pt[0]), float(pt[1]))
        if key not in seen:
            seen.add(key)
            out.append(key)
    return out


def _topology_edge_plan(topo):
    """board.topology 条目 → (nodes, [(edge_id, u, v)...])。

    网内布线序确定性冻结（任务书 W-4【待定】→本批冻结=DFS 前序）：根=
    nodes[0]（首个 pad 端点，=endpoints 出现序首）、邻接展开序=节点索引序
    （=端点出现序在前+分支点坐标字典序在后的 nodes 序）、迭代栈实现（无递归
    深度限制）。连通前缀性质：每条新边至少一端已在已布集合（树 DFS 固有）。
    edge_id="T<k>"=topology.edges 原始索引（routes entry 逐边对账锚）。"""
    nodes = [(float(p[0]), float(p[1])) for p in topo["nodes"]]
    norm = [(min(int(u), int(v)), max(int(u), int(v))) for u, v in topo["edges"]]
    eidx = {e: k for k, e in enumerate(norm)}
    adj = {i: [] for i in range(len(nodes))}
    for (u, v) in norm:
        adj[u].append(v)
        adj[v].append(u)
    for i in adj:
        adj[i].sort()
    order = []
    seen = {0}
    stack = [(0, None)]
    while stack:
        u, parent = stack.pop()
        if parent is not None:
            order.append(("T%d" % eidx[(min(u, parent), max(u, parent))],
                          parent, u))
        for v in reversed(adj[u]):
            if v not in seen:
                seen.add(v)
                stack.append((v, u))
    return nodes, order


def _edge_sequences(view, pid, partition, hints=None):
    """分区边执行计划（确定性）：返回 (topo_seq, mst_seq, fail_msg)。

    - 2 端网（endpoints 去重后 2 点）：topo_seq=[("T0", a, b, 0, 1)]（与
      board.topology 单边合同一致；无拓扑键的旧世界板/合成板同构构造——
      0.7.0 行为路径等价），mst_seq=None（无回退面）。
    - 多端网（>2 点）：topology 键缺失=fail_msg（调用方 fail-closed 抛）；
      topo_seq=DFS 前序（端点索引<terminal_count → partition endpoints 出现
      序索引，Steiner 分支点=None）；mst_seq=曼哈顿 MST 边序（任务书 §5
      Steiner 点可达性回退；edge_id="M<k>"）。
    - hints（V5-R1 W-5 导引通道开口，不接模型）：{"edge_order": [edge_id...]}
      =边序软先验（R3/席位批提案位；校验=topo_seq 的 permutation，非法
      fail-closed）；度量权归引擎——hints 只重排执行序不改边集/合法性。"""
    ends = _dedup_endpoints(partition["geometry"]["endpoints"])
    if len(ends) == 2:
        a, b = ends
        return [("T0", a, b, 0, 1)], None, None
    topo = view.topology.get(pid)
    if topo is None:
        return None, None, ("多点网（%d 端）无 board.topology 条目——世界模型"
                            "不一致（R1 后世界由 adapter 恒落键）" % len(ends))
    nodes, order = _topology_edge_plan(topo)
    tc = int(topo["terminal_count"])
    seq = []
    for eid, u, v in order:
        seq.append((eid, nodes[u], nodes[v],
                    u if u < tc else None, v if v < tc else None))
    if hints is not None:
        order_hint = hints.get("edge_order")
        if order_hint is not None:
            by_id = {e[0]: e for e in seq}
            if sorted(order_hint) != sorted(by_id):
                return None, None, ("topology_hints.edge_order 非 topology 边集"
                                    " permutation（得到 %s，期望 %s）"
                                    % (order_hint, sorted(by_id)))
            seq = [by_id[eid] for eid in order_hint]
    mst = _mst_edges(ends)
    mst_seq = [("M%d" % k, ends[i], ends[j], i, j)
               for k, (i, j) in enumerate(mst)]
    return seq, mst_seq, None


def _run_net_ladder(ctx, pid, net_id, width, edges_seq, assigned_layer,
                    negotiation_log, plans=None):
    """多端网逐拓扑边 2 端 A*（W-4；内核 _run_attempt_ladder 零改复用）。

    edges_seq=[(edge_id, a_pt, b_pt, a_pad_idx, b_pad_idx)...]（确定性边序由
    _edge_sequences 冻结）。逐边独立事务（_run_attempt_ladder 内建）；任一边
    失败 → ctx.rip_net 摘除本网全部已提交铜（部分成功不留残铜：残铜阻他网
    且终检不过）→ 失败返回。
    连通融合（Steiner 分支点=多边共享端点，落点合法性按半径簇）：同网铜在
    A*/归责面既非障碍（0.7.0 既有语义）+层账 {节点→已布层集}——后续边端点
    若为 Steiner 点，其层约束=层账（无记录=None 自由起种）；pad 端点=焊盘
    层集（D4 既有）；豁免半径簇=焊盘半尺寸（pad）/铜半宽（Steiner）。
    返回 (committed, attempts, reason, entries, vias_n, fail_ab)。"""
    layer_ledger = {}
    attempts = 0
    entries_all = []
    vias_n = 0
    view = ctx.view

    def _meta(pt, pad_idx):
        if pad_idx is not None:
            return (_endpoint_pad_layer_set(view, pid, pad_idx),
                    _endpoint_pad_extent(view, pid, pad_idx))
        layers = layer_ledger.get((float(pt[0]), float(pt[1])))
        return (set(layers) if layers else None, width / 2.0)

    for (edge_id, a_pt, b_pt, a_pad_idx, b_pad_idx) in edges_seq:
        meta = (_meta(a_pt, a_pad_idx), _meta(b_pt, b_pad_idx))
        ok, att, reason, entries, vn = _run_attempt_ladder(
            ctx, pid, net_id, width, a_pt, b_pt, assigned_layer,
            negotiation_log, plans=plans, endpoint_meta=meta)
        attempts += att
        if not ok:
            ripped = ctx.rip_net(net_id)
            negotiation_log.append(
                "net=%s partition=%s topology-edge=%s failed after %d "
                "attempts: %s → whole-net rolled back (%d entries ripped)"
                % (net_id, pid, edge_id, att, reason, ripped))
            return (False, attempts, "topology edge %s: %s" % (edge_id, reason),
                    None, 0, (a_pt, b_pt))
        for e in entries:
            e["topology_edge"] = edge_id
            for end_pt in (e["polyline"][0], e["polyline"][-1]):
                key = (float(end_pt[0]), float(end_pt[1]))
                layer_ledger.setdefault(key, set()).add(e["layer"])
        entries_all.extend(entries)
        vias_n += vn
    return True, attempts, None, entries_all, vias_n, None


def _ripup_params(overrides):
    """R2 W-1 有界参数解析：缺省=模块常量；overrides（board/任务级）只认
    白名单键 _RIPUP_PARAM_KEYS，整型键须 ≥1、guide 须 bool（fail-closed）。
    返回确定性 dict（键序=白名单序）；纯函数（无环境变量/全局态读取）。"""
    base = {
        "max_rounds_per_net": _RIPUP_MAX_ROUNDS_PER_NET,
        "max_total_per_candidate": _RIPUP_MAX_TOTAL_PER_CANDIDATE,
        "reroute_max_plans": _RIPUP_REROUTE_MAX_PLANS,
        "probe_budget": _RIPUP_PROBE_BUDGET,
        "joint_cost_factor": _RIPUP_JOINT_COST_FACTOR,
        "guide": True,
    }
    if overrides is None:
        return base
    _require(isinstance(overrides, dict), "ripup_params", "须为 dict 或 None")
    for k in sorted(overrides):
        _require(k in _RIPUP_PARAM_KEYS, "ripup_params.%s" % k,
                 "非白名单键（白名单=%s）" % (", ".join(_RIPUP_PARAM_KEYS)))
        v = overrides[k]
        if k == "guide":
            _require(isinstance(v, bool), "ripup_params.guide", "须为 bool")
        elif k == "probe_budget":
            _require(isinstance(v, int) and not isinstance(v, bool) and v >= 0,
                     "ripup_params.%s" % k, "须为 ≥0 整数（0=关探针）")
        else:
            _require(isinstance(v, int) and not isinstance(v, bool) and v >= 1,
                     "ripup_params.%s" % k, "须为 ≥1 整数")
        base[k] = v
    return base


def _ripup_blocker_ids(ctx, net_id, width, a_pt, b_pt, reach,
                       joint_factor=_RIPUP_JOINT_COST_FACTOR):
    """F4c 确定性阻塞集 + R2 W-2 联合重排。

    阶段 1（F4c 原语义保留）：已布 A* 网其铜落入 N 失败区域者——直连段
    (width/2+R5) 走廊带或端点逃逸邻域 (reach+R5) 盘（中心线口径，与
    edge_blocked 的 R5 同式）——逐网独立判定=当前阻塞者 hits。

    阶段 2（R2 W-2 上位替代者）：与 hit 网重布走廊交叠的已布网——其铜段与
    某 hit 段 seg-seg 距离 < corr_hw（hit 网重布同样需要其让位）。联合候选
    集=hits ∪ alts。

    阶段 3（联合评估 vs 逐个贪心，纯整数）：cost(w)=该网铜段数（重布工作量
    代理，无浮点环境差）；启用判据 score(joint) ≤ joint_factor×score(hits)
    （护栏防联合集爆炸；joint_factor=0 关闭联合重排=F4c 纯贪心）。

    确定性冻结（任务书 §2 W-2）：全部集合迭代一律 sorted()；选中集序
    tie-break=（联合评估分，网 id 字典序）。返回 (selected, net_geo)，
    net_geo={mid:(cx,cy)}=该网铜段 bbox 中心（W-3 波次分带键）。
    全程无墙钟/随机/集合序。
    """
    view = ctx.view
    r5 = view.r5_max   # V5-R7 W-2：保守 max 近似（任务书 §4 风险②首版；
                       # drc.max_net_class_clearance——缺类板=标量零漂移）
    corr_hw = width / 2.0 + r5
    disc = reach + r5
    by_net = {}
    for cu in ctx.route_coppers:
        if cu.net_id != net_id:
            pts = [(float(p[0]), float(p[1])) for p in cu.polyline]
            by_net.setdefault(cu.net_id, []).extend(
                list(zip(pts[:-1], pts[1:])))
    hits = {}
    for mid in sorted(by_net):
        segs = []
        for p, q in by_net[mid]:
            if clearance.segment_segment(p, q, a_pt, b_pt) < corr_hw:
                segs.append((p, q))
            elif (clearance.point_point(p, a_pt) < disc
                  or clearance.point_point(q, a_pt) < disc
                  or clearance.point_point(p, b_pt) < disc
                  or clearance.point_point(q, b_pt) < disc):
                segs.append((p, q))
        if segs:
            hits[mid] = segs
    if not hits:
        return [], {}
    # R2 W-2 阶段 2：上位替代者（重布走廊交叠的已布网）
    alts = set()
    if joint_factor > 0:
        hit_nets = sorted(hits)
        other_nets = [w for w in sorted(by_net) if w not in hits]
        for mid in hit_nets:
            for hp, hq in hits[mid]:
                for oid in other_nets:
                    if oid in alts:
                        continue
                    for p, q in by_net[oid]:
                        if clearance.segment_segment(p, q, hp, hq) < corr_hw:
                            alts.add(oid)
                            break
    # 阶段 3：联合评估（纯整数段数；护栏启用判据）
    cost = {w: len(by_net[w]) for w in by_net}
    joint = set(hits) | alts
    score_greedy = sum(cost[m] for m in hits)
    score_joint = sum(cost[m] for m in joint)
    selected = joint if score_joint <= joint_factor * score_greedy else set(hits)
    # 冻结序：tie-break=（联合评估分，网 id 字典序）
    order = sorted(selected, key=lambda m: (cost[m], m))
    net_geo = {}
    for w in order:
        xs = [pt for seg in by_net[w] for pt in seg]
        net_geo[w] = (
            (min(p[0] for p in xs) + max(p[0] for p in xs)) / 2.0,
            (min(p[1] for p in xs) + max(p[1] for p in xs)) / 2.0)
    return order, net_geo


def _ripup_retry(ctx, pid, net_id, width, a_pt, b_pt, layer, negotiation_log,
                 exec_of, budget, params=None, edges_seq=None):
    """F4c rip-up-and-retry（有界、确定性；docstring「升级件⑤-F4」节）+ R2
    W-2/W-3/W-4（联合重排/导引序池/victim 定向探针）。

    前置：net_id 已耗尽全部 attempts（阶梯已回滚，场景为耗尽时一致态）。
    exec_of：已提交网的执行参数账 {(net_id): (pid, width, edges_seq,
    fail_ab, layer)}（V5-R1：edges_seq=边执行计划（None=2 端单边 a/b 模式
    ——旧 5 元组语义由 fail_ab=(a_pt,b_pt) 承接）；execute_candidate 按提交
    序记录，供被 rip 网重布）。budget：候选级全局轮数账 {"total": int}
    （调用方持有）。params：_ripup_params 白名单 dict（R2 W-1 可配有界参数；
    None=模块缺省——白名单外 fork 调用方〔v5_diag_inherent 归因器〕以缺省
    参数面运行 0.7.0 行为）。edges_seq（V5-R1 W-4）：N（本网）为多端网时的
    边执行计划（重布=逐边；None=2 端 a/b 单边）。返回
    (info, cause, n_extra)：info=None → 放弃 rip-up（cause=None=无阻塞集
    维持原几何归因，否则为 ripup-* 归因串；n_extra=N 在重布阶梯中新增
    耗尽的 attempts 数，调用方并入 FAILED 总数披露）；info=(attempts_total,
    vias_n, entries, rerouted) → 成功，rerouted 为被 rip 网的重布结果
    [(net_id, reroute_attempts, entries, vias_n)]（per_net 行更新由调用方
    执行）。

    R2 轮内结构（确定性冻结）：每轮=W-2 联合重排选集 → rip 全集 → N 重布 →
    按 W-3 导引序池逐序重布被 rip 网（波次主选；档位仅 n≤12；guide=False
    退化为联合重排入选序）→ victim 失败时 W-4 定向探针（交换 victim 邻位
    step=+1/−1/+2 取前 B 个，一次交换序测量，结果逐条入 log）。N 本身重布
    失败（reroute）与被 rip 网序无关（同轮同集场景确定性相同）→ 直落下一轮。
    """
    params = _ripup_params(params)
    reach = _RIPUP_ESCAPE_REACH_MM
    rounds = 0
    n_extra = 0
    last_blockers = []
    last_fail = None   # None | ("reroute",) | ("victim", mid, reason)
    probe_steps = (1, -1, 2)   # W-4 冻结交换步序（确定性；取前 B 个）

    def _attempt_once(order):
        """单序全量试跑（事务）：rip 全部 blockers → N fresh 106 阶梯重布 →
        按 order 重布被 rip 网（前缀=params.reroute_max_plans）。返回
        (ok, att_n, att_total, entries, vias_n, rerouted, fail)——att_n=N
        本网 attempts（n_extra 口径=0.6.1：被 rip 网 attempts 失败不计入 N、
        成功时经 rerouted 入 per_net）；att_total=N+被 rip 网总和（committed
        行披露）；fail=None 成功；("reroute", att_n, reason) N 失败；
        ("victim", mid, reason, att_total) 被 rip 网失败。"""
        snap = ctx.snapshot()
        state_before = ctx.state_key()
        for mid in order:
            ctx.rip_net(mid)
        if edges_seq is not None:
            ok, att, reason, entries, vias_n, _fb = _run_net_ladder(
                ctx, pid, net_id, width, edges_seq, layer, negotiation_log,
                plans=_attempt_plans()[:params["reroute_max_plans"]])
        else:
            ok, att, reason, entries, vias_n = _run_attempt_ladder(
                ctx, pid, net_id, width, a_pt, b_pt, layer, negotiation_log)
        if not ok:
            ctx.restore(snap)
            if ctx.state_key() != state_before:
                raise ExecutorError("transaction",
                                    "rip-up 回滚后状态指纹不一致（内部错误）")
            return False, att, att, None, 0, None, ("reroute", att, reason)
        rerouted = []
        att_total = att
        for mid in order:
            m_pid, m_width, m_edges, m_fail_ab, m_layer = exec_of[mid]
            if m_edges is not None:
                ok_m, att_m, reason_m, m_entries, m_vias, _fbm = \
                    _run_net_ladder(ctx, m_pid, mid, m_width, m_edges, m_layer,
                                    negotiation_log,
                                    plans=_attempt_plans()[
                                        :params["reroute_max_plans"]])
            else:
                ok_m, att_m, reason_m, m_entries, m_vias = \
                    _run_attempt_ladder(
                        ctx, m_pid, mid, m_width, m_fail_ab[0], m_fail_ab[1],
                        m_layer, negotiation_log,
                        plans=_attempt_plans()[
                            :params["reroute_max_plans"]])
            att_total += att_m
            if not ok_m:
                ctx.restore(snap)
                if ctx.state_key() != state_before:
                    raise ExecutorError(
                        "transaction", "rip-up 回滚后状态指纹不一致（内部错误）")
                return (False, att, att_total, None, 0, None,
                        ("victim", mid, reason_m, att_total))
            rerouted.append((mid, att_m, m_entries, m_vias))
        return True, att, att_total, entries, vias_n, rerouted, None

    while rounds < params["max_rounds_per_net"]:
        if budget["total"] >= params["max_total_per_candidate"]:
            negotiation_log.append(
                "net=%s partition=%s ripup budget exhausted: global rounds "
                "=%d 已达上限 %d" % (net_id, pid, budget["total"],
                                     params["max_total_per_candidate"]))
            return None, ("ripup-exhausted（rip-up 预算耗尽：全局 %d 轮上限，"
                          "阻塞集=%s）" % (budget["total"], last_blockers)), n_extra
        blockers, net_geo = _ripup_blocker_ids(
            ctx, net_id, width, a_pt, b_pt, reach * (rounds + 1),
            joint_factor=params["joint_cost_factor"])
        _fev = getattr(ctx, "fail_events", None)
        if _fev is not None:   # R4-B：blocker 测量登记（空集=如实记录）
            _fev.record_blocker_measurement(
                net_id, pid, blockers, reach * (rounds + 1), rounds + 1,
                params["joint_cost_factor"], params)
        if not blockers:
            return None, None, n_extra   # 无已布网可 rip：维持原几何归因
        last_blockers = list(blockers)
        rounds += 1
        budget["total"] += 1
        negotiation_log.append(
            "net=%s partition=%s ripup round=%d ripped=%s "
            "reason=attempt-ladder exhausted" % (net_id, pid, rounds, blockers))
        # R2 W-3：导引序池（确定性；guide=False 退化=入选序，对照臂用）
        if params["guide"]:
            orders = [("wave", _guide.wave_order(blockers, net_geo))]
            if len(blockers) <= _guide.TIER_MAX_NETS:
                widths = {m: exec_of[m][1] for m in blockers if m in exec_of}
                if len(widths) == len(blockers):
                    orders.append(("tier", _guide.tier_order(blockers, widths)))
        else:
            orders = [("committed", list(blockers))]
        for channel, order in orders:
            if params["guide"]:
                negotiation_log.append(
                    "net=%s partition=%s ripup round=%d guide-order channel=%s "
                    "order=%s" % (net_id, pid, rounds, channel, order))
            ok, att_n, att_t, entries, vias_n, rerouted, fail = _attempt_once(
                order)
            n_extra += att_n
            if ok:
                negotiation_log.append(
                    "net=%s partition=%s ripup round=%d committed: N rerouted "
                    "attempt=%d, ripped rerouted=%s channel=%s"
                    % (net_id, pid, rounds, att_t,
                       [(m, a) for m, a, _e, _v in rerouted], channel))
                return (att_t, vias_n, entries, rerouted), None, n_extra
            if fail[0] == "reroute":
                negotiation_log.append(
                    "net=%s partition=%s ripup round=%d reroute failed after %d "
                    "attempts: %s → rolled back" % (net_id, pid, rounds, fail[1],
                                                    fail[2]))
                last_fail = ("reroute",)
                break   # N 重布失败与被 rip 网序无关（同集确定性）：换序徒劳
            negotiation_log.append(
                "net=%s partition=%s ripup round=%d reroute of ripped net %s "
                "failed: %s → rolled back" % (net_id, pid, rounds, fail[1],
                                              fail[2]))
            last_fail = ("victim", fail[1], fail[2])
            # R2 W-4：victim 定向探针（一次交换序测量；B=params.probe_budget）
            victim = fail[1]
            for pi in range(min(params["probe_budget"], len(probe_steps))):
                p_order = _guide.probe_swap(order, victim, probe_steps[pi])
                if p_order is None:
                    break
                negotiation_log.append(
                    "net=%s partition=%s ripup round=%d probe=%d victim=%s "
                    "swap-order=%s" % (net_id, pid, rounds, pi + 1, victim,
                                       p_order))
                ok, att_n, att_t, entries, vias_n, rerouted, fail = \
                    _attempt_once(p_order)
                n_extra += att_n
                if ok:
                    negotiation_log.append(
                        "net=%s partition=%s ripup round=%d committed: N "
                        "rerouted attempt=%d, ripped rerouted=%s channel=%s"
                        "-probe%d"
                        % (net_id, pid, rounds, att_t,
                           [(m, a) for m, a, _e, _v in rerouted], channel,
                           pi + 1))
                    return (att_t, vias_n, entries, rerouted), None, n_extra
                negotiation_log.append(
                    "net=%s partition=%s ripup round=%d probe=%d failed after "
                    "%d attempts → rolled back"
                    % (net_id, pid, rounds, pi + 1, att_t))
                if fail[0] == "reroute":
                    break   # N 失败与序无关：探针环终止
                last_fail = ("victim", fail[1], fail[2])
                victim = fail[1]
    if last_fail is not None and last_fail[0] == "victim":
        return None, ("ripup-reroute-failed（被 rip 网 %s 重布失败：%s）"
                      % (last_fail[1], last_fail[2])), n_extra
    return None, ("ripup-exhausted（rip-up %d 轮仍耗尽，阻塞集=%s）"
                  % (rounds, last_blockers)), n_extra


def _resolve_width(view, partition, pid):
    """电流分区取 R1 保守下限，其余取 planned_width；夹入 width_prior（矛盾 fail-closed）。"""
    prior = partition.get("width_prior") or {}
    w_min = float(prior.get("w_min", 0.0))
    w_max = float(prior.get("w_max", float("inf")))
    planned = float(partition.get("planned_width", 0.2))
    cur = float(partition.get("current_a") or 0.0)
    r1 = view.hard_rules.get("R1", {})
    required = wp.conservative_min_width(
        cur, fab_min_mm=0.0,
        k_per_amp=float(r1.get("k_a", wp.DEFAULT_K_PER_AMP)),
        floor_mm=float(r1.get("floor_mm", wp.DEFAULT_FLOOR_MM))) if cur > 0 else 0.0
    w = required if cur > 0 else planned
    w = min(max(w, w_min), w_max)
    if cur > 0 and w < required - clearance.EPS:
        raise ExecutorError(
            "partitions.%s.width_prior" % pid,
            "width_prior.w_max %r 低于 R1 保守下限 %r（板数据矛盾，fail-closed）"
            % (w_max, required))
    if not (w > 0 and math.isfinite(w)):
        raise ExecutorError("partitions.%s.width_prior" % pid,
                            "宽度先验区间解不出正宽度（w_min=%r, w_max=%r）"
                            % (w_min, w_max))
    return w


def _fixed_shape_entry(view, partition, pid):
    """ribbon / 既布分区的固定形状 entry（不做 A*）。返回 (entry, kind) 或 (None, 原因)。"""
    geo = partition.get("geometry") or {}
    net_id = view.net_of.get(pid, pid)
    band = geo.get("copper_band")
    if band:
        # ribbon 组网取板注册序首个引用网（多网同带，组披露见 ribbon_groups）
        net_id = (view.nets_by_partition.get(pid) or [net_id])[0]
    layer = partition.get("layer_policy")
    if layer not in view.signal_layers:
        return None, "层策略 %r 不是可用信号层" % (layer,)
    band = geo.get("copper_band")
    if band:
        lo, hi = sorted((float(band[0]), float(band[1])))
        width = float(geo["occupancy_mm"]) if geo.get("occupancy_mm") is not None \
            else hi - lo
        centerline = geo.get("centerline") or geo["endpoints"]
        polyline = [[float(pt[0]), float(pt[1])] for pt in centerline]
        return {"partition_id": pid, "net_id": net_id, "layer": layer,
                "polyline": polyline, "width": width,
                "transition_vias": [], "return_vias": []}, "ribbon"
    if partition.get("ptype") == "ROUTED":
        polyline = [[float(pt[0]), float(pt[1])] for pt in geo["endpoints"]]
        return {"partition_id": pid, "net_id": net_id, "layer": layer,
                "polyline": polyline,
                "width": float(partition.get("planned_width", 0.2)),
                "transition_vias": [], "return_vias": []}, "fixed"
    return None, None


# --------------------------------------- V5-EXECUTOR-ENG-R1 W-2（出口读数面）

_SELECTION_VERDICT_VALUES = ("SAT", "UNSAT", "UNKNOWN")
_PROVENANCE_ROUTED = {
    "UNKNOWN": "executor-renegotiated（终态出自执行器重协商，非 selection 直选）",
    "SAT": "selection-certified（selection 直选候选，执行器落实布通）",
    "UNSAT": ("contradictory-selection-unsat（selection UNSAT 而执行器布通"
              "——口径冲突，须披露复核）"),
}
_PROVENANCE_FAILED_EXHAUSTED = \
    "execute-exhausted（终态出自执行器穷举失败，非 selection 判定）"
_PROVENANCE_FAILED_SHORT = (
    "execute-short-circuit:sealed-short-circuit"
    "（事前短路：全层异网固定铜密封构造性无解）")


def _verdict_provenance(verdict, selection_verdict, short_circuit=False):
    """W-2 出口读数（纯函数；取值表=DESIGN-DECISION §3，token（中文释义）式，
    机器可按「（」前缀切分）。selection_verdict=None（kwarg 未提供）→ None
    =execute_candidate 返回面省略该键（主线旧调用面输出与 0.8.0 字节等）。
    short_circuit=True 走 FAILED 的 SC-1 短路行（事前短路=执行器的构造性
    主张）。fail-closed 滤除语义（滤除≠不可布）见模块 docstring W-2 节。"""
    if selection_verdict is None:
        return None
    if verdict == "ROUTED":
        return _PROVENANCE_ROUTED[selection_verdict]
    return _PROVENANCE_FAILED_SHORT if short_circuit \
        else _PROVENANCE_FAILED_EXHAUSTED


# ---------------------------------------------------------------- 主入口

def _validate_candidate(board, candidate):
    _require(isinstance(candidate, dict), "candidate", "须为 dict")
    order = candidate.get("route_order")
    _require(isinstance(order, list) and all(isinstance(x, str) for x in order),
             "candidate.route_order", "须为分区 id 字符串数组")
    assign = candidate.get("layer_assignment")
    _require(isinstance(assign, dict), "candidate.layer_assignment", "须为 dict")
    parts = {p["partition_id"] for p in board.get("partitions", [])}
    _require(sorted(order) == sorted(parts), "candidate.route_order",
             "不恰为全部分区（缺 %s，多 %s）"
             % (sorted(set(parts) - set(order)), sorted(set(order) - set(parts))))
    signal = {l["id"] for l in board.get("stackup", [])
              if l.get("kind") == "signal" and l.get("available") is True}
    for pid in order:
        layer = assign.get(pid)
        _require(layer in signal, "candidate.layer_assignment.%s" % pid,
                 "层 %r 不在可用信号层 %s" % (layer, sorted(signal)))
    return list(order), dict(assign)


def execute_candidate(board, candidate, out_dir=None, ripup_params=None,
                      topology_hints=None, selection_verdict=None):
    """L7 主入口（合同见模块 docstring）。纯确定性；同输入双跑 canonical
    字节等。R2 W-1：ripup_params（可选 dict）覆盖 rip-up 有界参数缺省
    （白名单键见 _RIPUP_PARAM_KEYS；board/任务级可配通道，None=模块缺省）。
    V5-R1 W-5 导引通道开口（不接模型）：topology_hints={pid: {"edge_order":
    [...], "branch_candidates": [...]}}——拓扑面软先验注入位（R3/席位批
    提案分支点候选/边序；本批只开通道口）。edge_order=边执行序先验（校验
    =board.topology 边集 permutation，非法 fail-closed；度量权归引擎——
    先验只重排执行序不改边集/合法性判定）；branch_candidates 仅留痕
    （negotiation_log 行），无引擎消费面。None=板序缺省（DFS 前序）。
    V5-EXECUTOR-ENG-R1 W-2：selection_verdict（可选，None|"SAT"|"UNSAT"|
    "UNKNOWN"，他值 fail-closed 抛 ExecutorError）=调用方（runner/工具）
    透传的 selection 终选判定，只参与 verdict_provenance 计算，零触碰
    路由决策/序/log（只动出口读数面，不动 selection 算法本身）；未提供
    =返回面省略该键（主线旧调用面输出与 0.8.0 字节等）。W-1：入口先过
    SC-1 事前短路（sealed-short-circuit，见模块 docstring 与
    _preflight_seal_shortcircuit）。"""
    if selection_verdict is not None:
        _require(isinstance(selection_verdict, str)
                 and selection_verdict in _SELECTION_VERDICT_VALUES,
                 "selection_verdict",
                 "须为 None|'SAT'|'UNSAT'|'UNKNOWN'（得到 %r）"
                 % (selection_verdict,))
    if topology_hints is not None:
        _require(isinstance(topology_hints, dict), "topology_hints",
                 "须为 dict（pid → 软先验 dict）或 None")
        for pid in sorted(topology_hints):
            _require(isinstance(topology_hints[pid], dict),
                     "topology_hints.%s" % pid, "须为 dict")
            _require(set(topology_hints[pid]) <= {"edge_order",
                                                  "branch_candidates"},
                     "topology_hints.%s" % pid,
                     "键白名单=edge_order/branch_candidates（得到 %s）"
                     % sorted(topology_hints[pid]))
    view = _BoardView(board)
    route_order, layer_assignment = _validate_candidate(board, candidate)
    ripup_params = _ripup_params(ripup_params)
    ctx = _Context(board)
    negotiation_log = []
    # OPT-09：进度 sidecar（opt-in；未设环境变量 → None=零行为差）。侧车
    # manifest 绑定 executor/board/schema/candidate hash 与进程身份；只在
    # 执行线程实际到达候选/网/attempt 边界时写 work 事件（独立 sidecar
    # 文件，不触 canonical routes hash、不入 canonical 运行账）。
    progress = ProgressSidecar.from_env({
        "executor_version": EXECUTOR_VERSION,
        "board_id": getattr(view, "board_id", None),
        "board_sha256": getattr(view, "board_sha256", None),
        "schema_version": ROUTES_SCHEMA_VERSION,
        "candidate_sha256": _progress_candidate_sha256(candidate),
        "geometry_semantics": _geometry_semantics.consumer_manifest(),
        "stage": "execute_candidate"})
    ctx.progress = progress
    if progress is not None:
        progress.emit_work("candidate_start", n_partitions=len(route_order),
                           route_order=list(route_order))
    # OPT-07／R4-B：fail-event.v1 失败事件侧车（opt-in；V5_R4B_FAIL_EVENTS
    # 未设 → None=零行为差。只加不改：不动 canonical routes hash/路由决策/
    # 返回工件/日志语义与序；IO 失败只降级不抛出）
    fail_journal = FailEventJournal.from_env({
        "executor_version": EXECUTOR_VERSION,
        "board_id": getattr(view, "board_id", None),
        "board_sha256": getattr(view, "board_sha256", None),
        "routes_schema_version": ROUTES_SCHEMA_VERSION,
        "candidate_sha256": _progress_candidate_sha256(candidate),
        "geometry_semantics": _geometry_semantics.consumer_manifest()})
    if fail_journal is not None:
        ctx.fail_events = fail_journal
    # EXEC-R8-B：candidate-event.v1 候选出口事件侧车（opt-in；
    # V5_R4B_CANDIDATE_EVENTS 未设 → None=零行为差。沿 fail-event 同款
    # 纪律：只加不改，不动 canonical routes hash/路由决策/返回工件/日志
    # 语义与序；IO 失败只降级不抛出。出口事件走 baseline 通道
    # registered_not_extension（不算证书扩展；准入语义 evaluate_admission
    # 零改动）；FAILED 收口携 source_fail_event 关联（fail-event 收口事件
    # id，只引用不重放）。
    candidate_journal = CandidateEventJournal.from_env({
        "executor_version": EXECUTOR_VERSION,
        "board_id": getattr(view, "board_id", None),
        "board_sha256": getattr(view, "board_sha256", None),
        "routes_schema_version": ROUTES_SCHEMA_VERSION,
        "candidate_sha256": _progress_candidate_sha256(candidate)})
    cand_exit_nets = None
    if candidate_journal is not None:
        cand_exit_nets = [view.net_of.get(p, p) for p in route_order]
    # V5-EXECUTOR-ENG-R1 W-1：SC-1 事前短路（任何阶梯之前；零触发=零 log
    # 增量——非密封板此调用对 negotiation_log 零副作用）
    short = _preflight_seal_shortcircuit(ctx, route_order, negotiation_log)
    if short is not None:
        prov = _verdict_provenance("FAILED", selection_verdict,
                                   short_circuit=True)
        if prov is not None:
            short["verdict_provenance"] = prov
        if progress is not None:
            progress.emit_work("candidate_done", verdict="FAILED",
                               outcome="sealed-short-circuit")
            progress.close(verdict="FAILED")
        if fail_journal is not None:   # R4-B：候选收口事件（sealed）
            fail_journal.emit_candidate_failed_close(
                ctx, "sealed-short-circuit",
                sum(pn.get("attempts", 0) for pn in short.get("per_net", [])))
            fail_journal.close()
        if candidate_journal is not None:   # R8-B：候选出口事件（sealed）
            register_engine_exit(
                candidate_journal, candidate=candidate,
                affected_nets=cand_exit_nets,
                board_sha256=view.board_sha256,
                source_fail_event_id=(
                    fail_journal.last_event_id
                    if fail_journal is not None else None))
            candidate_journal.close()
        return short
    per_net = []
    fixed_partitions = []
    ribbon_groups = {}
    pour_regions = {}
    failed = False
    exec_of = {}            # F4c：已提交网执行参数账（rip-up 原序重布用）
    budget = {"total": 0}   # F4c：候选级全局 rip-up 轮数（R2 W-1 可配缺省 12）

    for pid in route_order:
        if progress is not None:   # OPT-09：网（分区）边界到达
            progress.emit_work("partition_start", partition_id=pid)
        partition = view.partitions[pid]
        pour = (partition.get("geometry") or {}).get("pour")
        if pour is not None:
            pour_regions[pid] = dict(pour)
        # 1) 固定形状：ribbon（R3 整体）与既布分区（铜已在场景，entry 只作声明）
        if view.ribbon_partition(pid) or view.fixed_partition(pid):
            entry, kind = _fixed_shape_entry(view, partition, pid)
            if entry is None:
                negotiation_log.append(
                    "partition=%s fixed-shape failed: %s" % (pid, kind))
                per_net.append({"partition_id": pid,
                                "net_id": view.net_of.get(pid, pid),
                                "status": "failed", "attempts": 0,
                                "negotiated": False, "vias": 0,
                                "length_mm": 0.0, "width_mm": 0.0, "layers": []})
                if progress is not None:   # OPT-09：网边界（fixed-shape 失败）
                    progress.emit_work("net_done", partition_id=pid,
                                       net_id=view.net_of.get(pid, pid),
                                       status="failed", attempts=0)
                if fail_journal is not None:   # R4-B：fixed_shape_failed
                    fail_journal.emit_fixed_shape_failed(
                        ctx, pid, view.net_of.get(pid, pid), kind)
                failed = True
                break
            if kind == "ribbon":
                nets = view.nets_by_partition.get(pid, [entry["net_id"]])
                ribbon_groups[pid] = {"net_ids": list(nets),
                                      "occupancy_mm": float(entry["width"]),
                                      "route_index": len(ctx.entries)}
            else:
                fixed_partitions.append(pid)
            ctx.entries.append(entry)
            negotiation_log.append(
                "partition=%s committed fixed-shape (%s)" % (pid, kind))
            per_net.append({"partition_id": pid, "net_id": entry["net_id"],
                            "status": kind, "attempts": 0, "negotiated": False,
                            "vias": 0,
                            "length_mm": round(polyline_length(entry["polyline"]), 10),
                            "width_mm": float(entry["width"]),
                            "layers": [entry["layer"]]})
            if progress is not None:   # OPT-09：网边界（fixed-shape 提交）
                progress.emit_work("net_done", partition_id=pid,
                                   net_id=entry["net_id"], status=kind,
                                   attempts=0)
            continue
        # 2) 退化分区（升级件④模式A合同）：端点去重后 ≤1 点 = trivially
        #    satisfied——零长 route 条目（polyline=[pt,pt]、层=候选指派层、
        #    无过渡/回流孔、宽=planned_width），仅作工件声明（零铜展宽：不入
        #    障碍/容量账本；route_check.build_scene 对零长 polyline 同规则
        #    跳过=无间距交互）。V5-R1：多点网退化判据=endpoints 去重点数
        #    （2 端重合=旧判据子集）。
        ends = partition["geometry"]["endpoints"]
        uniq_ends = _dedup_endpoints(ends)
        if len(uniq_ends) <= 1:
            layer = layer_assignment[pid]
            width0 = float(partition.get("planned_width", 0.2))
            pt0 = [float(ends[0][0]), float(ends[0][1])]
            nets0 = view.nets_by_partition.get(pid) or [view.net_of.get(pid, pid)]
            for net_id in nets0:
                ctx.entries.append({
                    "partition_id": pid, "net_id": net_id, "layer": layer,
                    "polyline": [list(pt0), list(pt0)], "width": width0,
                    "transition_vias": [], "return_vias": []})
                negotiation_log.append(
                    "net=%s partition=%s degenerate: zero-length partition "
                    "trivially satisfied" % (net_id, pid))
                per_net.append({"partition_id": pid, "net_id": net_id,
                                "status": "degenerate", "attempts": 0,
                                "negotiated": False, "vias": 0, "length_mm": 0.0,
                                "width_mm": width0, "layers": [layer]})
                if progress is not None:   # OPT-09：网边界（退化分区）
                    progress.emit_work("net_done", partition_id=pid,
                                       net_id=net_id, status="degenerate",
                                       attempts=0)
            continue
        # 3) A* 网（每网一个 staging 事务；每网可含多 run/多 entry）；
        #    尝试计划阶梯见模块 docstring「升级件④」「升级件⑤-F4」节
        #    （基线→细化→逃逸→F4a/F4b 细档，每次尝试策略入 negotiation_log；
        #    R1/R2/R5/R6 判定零改动）；耗尽后 F4c rip-up-and-retry 兜底。
        #    V5-R1 W-4：边执行计划（2 端网=单边恒等；多端网=board.topology
        #    DFS 前序+MST 回退面）；W-5 导引通道开口=topology_hints（见
        #    execute_candidate 签名，只开通道不接模型）。
        nets = view.nets_by_partition.get(pid) or [view.net_of.get(pid, pid)]
        width = _resolve_width(view, partition, pid)
        hint = (topology_hints or {}).get(pid)
        edges_seq, mst_seq, edge_fail = _edge_sequences(
            view, pid, partition, hints=hint if isinstance(hint, dict) else None)
        if edge_fail is not None:
            raise ExecutorError("partitions.%s.geometry" % pid, edge_fail)
        if hint is not None:
            negotiation_log.append(
                "partition=%s topology-hints consumed: %s"
                % (pid, sorted(hint) if isinstance(hint, dict) else repr(hint)))
        a_pt = partition["geometry"]["endpoints"][0]
        b_pt = partition["geometry"]["endpoints"][1]
        for net_id in nets:
            committed, attempts, reason, entries, vias_n, fail_ab = \
                _run_net_ladder(ctx, pid, net_id, width, edges_seq,
                                layer_assignment[pid], negotiation_log)
            ripup_cause = None
            active_edges = edges_seq
            if not committed and mst_seq is not None:
                # 任务书 §5：Steiner 点可达性回退——拓扑边序失败（禁布点/
                # 分支几何不可达）→ 曼哈顿 MST 边序整网重试一次（去 Steiner
                # 化=2 端抽象逐边；如实入 log）
                negotiation_log.append(
                    "net=%s partition=%s topology-fallback-mst: topology edges "
                    "exhausted, retrying with MST edge order (%d edges)"
                    % (net_id, pid, len(mst_seq)))
                committed, m_att, reason, entries, vias_n, fail_ab = \
                    _run_net_ladder(ctx, pid, net_id, width, mst_seq,
                                    layer_assignment[pid], negotiation_log)
                attempts += m_att
                active_edges = mst_seq
            if not committed:
                info, ripup_cause, n_extra = _ripup_retry(
                    ctx, pid, net_id, width,
                    (fail_ab or (a_pt, b_pt))[0], (fail_ab or (a_pt, b_pt))[1],
                    layer_assignment[pid], negotiation_log, exec_of, budget,
                    ripup_params,
                    edges_seq=active_edges if len(active_edges) > 1 else None)
                attempts += n_extra
                if info is not None:
                    attempts, vias_n, entries, rerouted = info
                    committed = True
                    negotiation_log.append(
                        "net=%s partition=%s committed via ripup: total "
                        "attempts=%d" % (net_id, pid, attempts))
                    for m_id, m_att, m_entries, m_vias in rerouted:
                        for pn in per_net:
                            if pn["net_id"] == m_id:
                                pn["attempts"] = pn["attempts"] + m_att
                                pn["negotiated"] = pn["attempts"] > 1
                                pn["vias"] = m_vias
                                pn["length_mm"] = round(
                                    sum(polyline_length(e["polyline"])
                                        for e in m_entries), 10)
                                pn["layers"] = [e["layer"] for e in m_entries]
                                break
            if committed:
                # V5-R1：执行参数账 5 槽=(pid, width, edges_seq, fail_ab, layer)
                #（edges_seq=None=2 端单边；多端网 rip 重布=逐边，fail_ab=
                # 拓扑/MST 回退后最后生效边序）
                exec_of[net_id] = (pid, width,
                                   active_edges if len(active_edges) > 1
                                   else None,
                                   fail_ab or (a_pt, b_pt),
                                   layer_assignment[pid])
                per_net.append({"partition_id": pid, "net_id": net_id,
                                "status": "routed", "attempts": attempts,
                                "negotiated": attempts > 1, "vias": vias_n,
                                "length_mm": round(sum(polyline_length(
                                    e["polyline"]) for e in entries), 10),
                                "width_mm": float(width),
                                "layers": [e["layer"] for e in entries]})
                if progress is not None:   # OPT-09：网边界（A* 提交）
                    progress.emit_work("net_done", partition_id=pid,
                                       net_id=net_id, status="routed",
                                       attempts=attempts, vias=vias_n)
                continue
            fb = fail_ab or (a_pt, b_pt)
            negotiation_log.append(
                "net=%s partition=%s FAILED after %d attempts: %s"
                % (net_id, pid, attempts, reason))
            cause = ripup_cause
            if cause is None:
                cause = _exhaustion_cause(ctx, pid, net_id, width, fb[0], fb[1])
            negotiation_log.append(
                "net=%s partition=%s exhaustion-cause=%s" % (net_id, pid, cause))
            # 0.6.1 log-only（V5-SMALLWAVE A3）：几何二级归因披露行——失败已
            # 定局后追加，不改任何路由决策/序（此前全部尝试与归因已入 log）。
            negotiation_log.append(
                "net=%s partition=%s geom-secondary=%s"
                % (net_id, pid,
                   _geom_secondary_attr(ctx, pid, net_id, width, fb[0], fb[1])))
            per_net.append({"partition_id": pid, "net_id": net_id,
                            "status": "failed", "attempts": attempts,
                            "negotiated": attempts > 1, "vias": 0,
                            "length_mm": 0.0, "width_mm": float(width),
                            "layers": []})
            if progress is not None:   # OPT-09：网边界（耗尽失败）
                progress.emit_work("net_done", partition_id=pid,
                                   net_id=net_id, status="failed",
                                   attempts=attempts)
            if fail_journal is not None:   # R4-B：net_exhausted 失败事件
                if active_edges is mst_seq and mst_seq is not None:
                    _edge_src = "mst_fallback"
                elif isinstance(hint, dict) and "edge_order" in hint:
                    _edge_src = "topology_hints"
                else:
                    _edge_src = "board_topology_dfs"
                fail_journal.emit_net_exhausted(
                    ctx, pid, net_id, attempts, cause,
                    _geom_secondary_attr(ctx, pid, net_id, width, fb[0], fb[1]),
                    active_edges, _edge_src)
            failed = True
            break
        if failed:
            break

    if failed:
        out = {"verdict": "FAILED", "routes": None, "per_net": per_net,
               "negotiation_log": negotiation_log}
        prov = _verdict_provenance("FAILED", selection_verdict)
        if prov is not None:
            out["verdict_provenance"] = prov
        if progress is not None:   # OPT-09：候选边界（穷举失败收口）
            progress.emit_work("candidate_done", verdict="FAILED",
                               outcome="exhausted")
            progress.close(verdict="FAILED")
        if fail_journal is not None:   # R4-B：候选 FAILED 收口事件
            fail_journal.emit_candidate_failed_close(
                ctx, "exhausted",
                sum(pn.get("attempts", 0) for pn in per_net))
            fail_journal.close()
        if candidate_journal is not None:   # R8-B：候选出口事件（exhausted）
            register_engine_exit(
                candidate_journal, candidate=candidate,
                affected_nets=cand_exit_nets,
                board_sha256=view.board_sha256,
                source_fail_event_id=(
                    fail_journal.last_event_id
                    if fail_journal is not None else None))
            candidate_journal.close()
        return out

    # 3) 全量自检（A9：route_check 编排，判定全出自 v5.drc）
    doc = {
        "schema_version": ROUTES_SCHEMA_VERSION,
        "board_id": view.board_id,
        "board_sha256": view.board_sha256,
        "routes": list(ctx.entries),
        "negotiation_log": list(negotiation_log),
        "provenance": {"generator": EXECUTOR_VERSION,
                       "board_sha256": view.board_sha256},
    }
    if ribbon_groups:
        doc["ribbon_groups"] = ribbon_groups
    if fixed_partitions:
        doc["fixed_partitions"] = fixed_partitions
    if pour_regions:
        doc["pour_regions"] = pour_regions
    validate_routes(board, doc)   # 出口自检（防御性；fail-closed）
    report = _check_routes(board, doc)
    if report["feasible"]:
        negotiation_log.append(
            "final route_check feasible=True (%s, drc %s, capacity %d 项全过)"
            % (ROUTE_CHECK_VERSION, report["drc_version"],
               len(report["capacity_checks"])))
        doc["negotiation_log"] = list(negotiation_log)
        if out_dir is not None:
            tx = staging.StagingTransaction(os.path.join(out_dir, "_staging"),
                                            out_dir, "%s.routes" % view.board_id)
            try:
                tx.write_json("%s.routes.json" % view.board_id, doc)
                tx.commit()
            except Exception:
                tx.rollback()
                raise
        out = {"verdict": "ROUTED", "routes": doc, "per_net": per_net,
               "negotiation_log": negotiation_log}
        prov = _verdict_provenance("ROUTED", selection_verdict)
        if prov is not None:
            out["verdict_provenance"] = prov
        if progress is not None:   # OPT-09：候选边界（ROUTED 收口）
            progress.emit_work("candidate_done", verdict="ROUTED")
            progress.close(verdict="ROUTED")
        if fail_journal is not None:   # R4-B：健康收口只关句柄（零事件）
            fail_journal.close()
        if candidate_journal is not None:   # R8-B：候选出口事件（ROUTED；
            register_engine_exit(           # 无失败→source_fail_event=None）
                candidate_journal, candidate=candidate,
                affected_nets=cand_exit_nets,
                board_sha256=view.board_sha256,
                source_fail_event_id=None)
            candidate_journal.close()
        return out
    tops = report["attributed_violations"][:3]
    detail = "; ".join("%s(%s↔%s)" % (v["rule"], v["subjects"][0], v["subjects"][1])
                       for v in tops)
    negotiation_log.append(
        "final route_check infeasible: %d 项归责违例（%s%s）→ 整体 FAILED、routes 回退为 None"
        % (len(report["attributed_violations"]), detail,
           " 等" if len(report["attributed_violations"]) > 3 else ""))
    out = {"verdict": "FAILED", "routes": None, "per_net": per_net,
           "negotiation_log": negotiation_log}
    prov = _verdict_provenance("FAILED", selection_verdict)
    if prov is not None:
        out["verdict_provenance"] = prov
    if progress is not None:   # OPT-09：候选边界（终检不可行收口）
        progress.emit_work("candidate_done", verdict="FAILED",
                           outcome="final-check-infeasible")
        progress.close(verdict="FAILED")
    if fail_journal is not None:   # R4-B：终检不合格+候选收口事件
        fail_journal.emit_final_check_infeasible(
            ctx, sum(pn.get("attempts", 0) for pn in per_net),
            "final route_check infeasible: %d 项归责违例（%s%s）"
            % (len(report["attributed_violations"]), detail,
               " 等" if len(report["attributed_violations"]) > 3 else ""),
            report.get("capacity_meta"), doc)
        fail_journal.emit_candidate_failed_close(
            ctx, "final-check-infeasible",
            sum(pn.get("attempts", 0) for pn in per_net))
        fail_journal.close()
    if candidate_journal is not None:   # R8-B：候选出口事件（终检不可行；
        register_engine_exit(           # 携 fail-event 收口关联）
            candidate_journal, candidate=candidate,
            affected_nets=cand_exit_nets,
            board_sha256=view.board_sha256,
            source_fail_event_id=(
                fail_journal.last_event_id
                if fail_journal is not None else None))
        candidate_journal.close()
    return out
