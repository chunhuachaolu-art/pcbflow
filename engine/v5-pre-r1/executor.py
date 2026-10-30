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
- **边界（披露）**：fixed-shape（ribbon/既布）与退化分区的板声明铜不经 A*，
  不因入带被 executor 拒布（板数据固有态，v5 不可移铜）——由 route_check
  edge_violations 如实披露、D6-4 分类器同位归责；焊盘铜贴边同口径（v5
  边距带为中心线口径，物理铜缘口径差不在执行侧建模，残差归 D6-4 披露）。

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
from .drc import check_all, check_clearance, check_keepout
from .drc import edge_inner_rect   # D6-3 板边禁布带（带值/口径单源=v5.drc）
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

EXECUTOR_VERSION = "v5.executor/0.5.0"   # 0.5.0=P5⑥ D6-3：板边禁布带入障碍栅格
                                         # + exhaustion 归因 edge-clearance 类
                                         # （0.4.0=升级件⑤ F1-F4）
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
_RIPUP_MAX_ROUNDS_PER_NET = 2      # F4c 每网 rip-up 轮数上限
_RIPUP_MAX_TOTAL_PER_CANDIDATE = 8  # F4c 每候选全局 rip-up 轮数上限
_RIPUP_ESCAPE_REACH_MM = 0.75       # 端点逃逸邻域半径 = 逃逸阶梯最大位移（r3×0.25）
_RIPUP_REROUTE_MAX_PLANS = 20       # F4c 被 rip 网 fresh 重布的计划前缀上界
# （重布语义=在障碍超集下恢复既有布线，前 20 计划（两档栅格全变体+首批逃逸）
# 为有界协商重搜；N 本网重布仍用完整 106 阶梯）
_FINE_WINDOW_MARGIN_MM = 1.0        # F4a 细档限域窗口外扩（≥逃逸位移+吸附半格）
# 升级件⑤ F2 回流孔候选扩容常量（确定性；序披露于模块 docstring「升级件⑤」节）：
_RETURN_VIA_SUBSTEP = 0.5      # 半径细步进档 = pitch×0.5（0.25mm 栅格→0.125mm 档）
_RETURN_VIA_FAMILIES = (       # 家族序即方向序底座：轴向 4 → 对角 4 → 马步 8
    ((1, 0), (-1, 0), (0, 1), (0, -1)),
    ((1, 1), (1, -1), (-1, 1), (-1, -1)),
    ((2, 1), (2, -1), (-2, 1), (-2, -1),
     (1, 2), (1, -2), (-1, 2), (-1, -2)),
)   # 马步族补齐轴向↔对角之间的两侧角域（双侧锚点偏移备选），共 16 方向


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
    """已入场景铜的搜索视图（分段与包围盒预计算；bbox 预滤加速 A*）。"""

    __slots__ = ("cu", "segs", "bbox", "partition_id")

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
        self.partition_id = getattr(cu, "partition_id", None)

    def distance_to(self, p, q):
        """线段 (p,q) 与本铜的最小距离（口径同 v5.drc._actual_gap 的分派）。"""
        cu = self.cu
        if cu.band is not None:
            return clearance.segment_rect_distance(p, q, _rect_dict(cu.band))
        if cu.pad is not None:
            (c, r) = cu.pad
            return clearance.pad_segment_distance(c, r, p, q)
        best = float("inf")
        for a, b in self.segs:
            d = clearance.segment_segment(p, q, a, b)
            if d < best:
                best = d
        return best

    def via_gap(self, p, via_r):
        """孔铜圆 (p, via_r) 与本铜的 R5 间隙（口径同 v5.drc._actual_gap 的
        圆-铜分派：圆-矩形=pad_rect_distance、圆-圆=点距-两半径、
        圆-折线=点线距-半径——中心线铜的半径侧=孔铜半径）。"""
        cu = self.cu
        if cu.band is not None:
            return clearance.pad_rect_distance(p, via_r, _rect_dict(cu.band))
        if cu.pad is not None:
            (c, r) = cu.pad
            return max(0.0, clearance.point_point(p, c) - r - via_r)
        return max(0.0, min(clearance.point_segment(p, a, b)
                            for a, b in self.segs) - via_r)


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
        self.obstacles[:] = snap["obstacles"]
        self.entries[:] = snap["entries"]
        self.route_coppers[:] = snap["route_coppers"]
        self.via_points[:] = snap["via_points"]
        for k, widths in snap["ledger"].items():
            self.ledger[k]["widths"] = list(widths)

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

    def _touched_corridors(self, cu):
        """run 铜进入的走廊列表（镜像 route_check._copper_in_rect 口径）。"""
        hits = []
        for zone in self.view.corridors:
            if _copper_in_rect(cu, _rect_dict(_zone_rect(zone))):
                hits.append((zone["zone_id"], cu.layer))
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

        R2 不在此判（整线累计语义，由 _astar 的状态增广精确建模，见其 docstring）。
        exempt_same_partition：共享端点豁免半径内的边（仅同分区对腿）。
        障碍面（升级件⑤ F1）：固定铜 + 已提交网铜 + **已提交他网过孔铜**
        （跨全信号层圆盘，R5 中心线口径；同网孔=合法连接点）。
        D6-3（0.5.0）：板边禁布带（workspace 内缩 0.2mm 环带）入障碍——段任一
        端点出内矩形即封（内矩形凸 ⟺ 段触带），全信号层同带（本函数逐层调用
        天然逐层生效），带值/轮廓源单源=v5.drc；无豁免档（贴边无协商余地，
        对应 kicad copper_edge_clearance 0.2mm 缺省）。
        """
        view = self.view
        # D6-3：板边禁布带（先于 R5/R6 的 O(1) 包络检查；原因标记与 exhaustion
        # 归因类同名）
        ix0, iy0, ix1, iy1 = self.edge_inner
        if p[0] < ix0 - clearance.EPS or p[0] > ix1 + clearance.EPS \
                or p[1] < iy0 - clearance.EPS or p[1] > iy1 + clearance.EPS \
                or q[0] < ix0 - clearance.EPS or q[0] > ix1 + clearance.EPS \
                or q[1] < iy0 - clearance.EPS or q[1] > iy1 + clearance.EPS:
            return "edge-clearance"
        # R6：禁布区（逐段 bbox 间隙 >0，与 route_check R6 逐段精查同口径）
        bbox = (min(p[0], q[0]), min(p[1], q[1]), max(p[0], q[0]), max(p[1], q[1]))
        for _zid, ko in view.keepouts:
            if clearance.rect_rect_gap(bbox, ko) <= 0.0:
                return "R6"
        # R5：既布铜/已布网膨胀（中心线口径与 v5.drc.check_clearance 一致）
        r5 = float(view.hard_rules.get("R5", {}).get("min_clearance_mm", 0.5))
        for ob in self.obstacles:
            if ob.cu.layer != layer:
                continue
            if ob.cu.net_id == net_id:
                continue
            if ob.bbox[0] - r5 > max(p[0], q[0]) or ob.bbox[2] + r5 < min(p[0], q[0]) \
               or ob.bbox[1] - r5 > max(p[1], q[1]) or ob.bbox[3] + r5 < min(p[1], q[1]):
                continue   # bbox 预滤
            if exempt_same_partition and ob.partition_id is not None \
               and ob.partition_id == pid:
                continue   # 同分区对腿：共享端点入边豁免
            if ob.distance_to(p, q) < r5 - clearance.EPS:
                return "R5"
        # R5（升级件⑤ F1，executor-孔协调缝）：已提交**他网**过孔铜圆盘按 R5
        # 入走线障碍——route_check 场景对已提交孔逐信号层构造圆铜（_via_coppers），
        # 本模型此前只含他网走线/焊盘铜，后网走线落入先提交孔 R5 邻域被终检
        # 实抓（badgeleds/pmod-bme280 根因）。孔铜跨全信号层，不按 layer 过滤；
        # 同网已提交孔=合法连接点跳过；同分区豁免与折线障碍同口径（共享端点
        # 入边豁免区；归责层同分区豁免覆盖该对）。
        via_r = float(view.via_radius)
        plo, phi = min(p[0], q[0]), max(p[0], q[0])
        qlo, qhi = min(p[1], q[1]), max(p[1], q[1])
        slack = via_r + r5
        for vnet, vpid, vpt in self.via_points:
            if vnet == net_id:
                continue
            if exempt_same_partition and pid is not None and vpid == pid:
                continue
            if vpt[0] + slack < plo or vpt[0] - slack > phi \
               or vpt[1] + slack < qlo or vpt[1] - slack > qhi:
                continue   # bbox 预滤
            if clearance.pad_segment_distance(vpt, via_r, p, q) < r5 - clearance.EPS:
                return "R5"
        # capacity：边进走廊矩形即按该走廊×层预留（近似 2）。
        # 既有占用 = Σ宽 + 既有条目间距（与 v5.metrics.capacity.corridor_occupancy
        # 同式），新条目增量 = 本网宽 + 1 个新增相邻间距。
        for zone in view.corridors:
            rect_d = _rect_dict(_zone_rect(zone))
            if clearance.segment_rect_distance(p, q, rect_d) <= clearance.EPS:
                cell = self.ledger.get((zone["zone_id"], layer))
                widths = cell["widths"] if cell else []
                occ = cap_mod.corridor_occupancy(
                    [cap_mod.CapacityEntry("n", w) for w in widths])
                need = width + (cap_mod.NET_NET_SPACING if widths else 0.0)
                if occ + need > float(zone["capacity"]) + clearance.EPS:
                    return "capacity"
        return None

    def via_blocked(self, p, net_id):
        """孔位 p 是否封死（升级件① D2：孔铜=圆 radius=via_model 缺省 0.3）。
        严格判定（比折线边更严）：R6 禁布（圆入禁布区）+ **异网铜 R5 无同分区
        豁免**（钻孔穿他网铜=制造违例；共享端点抽象豁免只及铜不及孔）+
        对全部既有孔点最小孔心距 2·r+R5（D3 同式，孔-孔不变式）。返回
        None 或原因标记。D6-3（0.5.0）：孔心入板边禁布带即封（孔铜同为铜，
        与折线同带同口径、无豁免档）。"""
        view = self.view
        via_r = float(view.via_radius)
        r5 = float(view.hard_rules.get("R5", {}).get("min_clearance_mm", 0.5))
        ix0, iy0, ix1, iy1 = self.edge_inner
        if p[0] < ix0 - clearance.EPS or p[0] > ix1 + clearance.EPS \
                or p[1] < iy0 - clearance.EPS or p[1] > iy1 + clearance.EPS:
            return "edge-clearance"
        for _zid, ko in view.keepouts:
            if clearance.pad_rect_distance(p, via_r, _rect_dict(ko)) <= 0.0:
                return "R6"
        for ob in self.obstacles:
            if ob.cu.net_id == net_id:
                continue
            slack = r5 + via_r + float(ob.cu.half_width)
            if ob.bbox[0] - slack > p[0] or ob.bbox[2] + slack < p[0] \
               or ob.bbox[1] - slack > p[1] or ob.bbox[3] + slack < p[1]:
                continue   # bbox 预滤（含铜半宽）
            if ob.via_gap(p, via_r) < r5 - clearance.EPS:
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
    # R5（同分区对腿在归责层豁免——与 route_check 同规则）
    r5v, _checked = check_clearance(
        scene, float(hard.get("R5", {}).get("min_clearance_mm", 0.5)))
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
    部分段/出边必然全封，sealed 同真但根因是带，先判防遮蔽）> endpoint-
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
        return (pt[0] < ix0 - clearance.EPS or pt[0] > ix1 + clearance.EPS
                or pt[1] < iy0 - clearance.EPS or pt[1] > iy1 + clearance.EPS)

    if _in_edge_band(a_pt) or _in_edge_band(b_pt):
        return "edge-clearance（端点入板边禁布带，边距类）"

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
    r5x = float(view.hard_rules.get("R5", {}).get("min_clearance_mm", 0.5))
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


# ---------------------------------------------------------------- 单线 A*

def _r2_edge_blocked(view, p, q, mode):
    """R2 边档检查（v5.drc.check_ana_proximity 整线累计语义的保守实现）。

    "near"：段距 < min_distance 且该段有投影重叠 → 封；
    "overlap_free"：该段有投影重叠（无论距离）→ 封。
    任一档被接受的路径，其折线在敏感区的投影重叠累计为 0（档内规则保证），
    v5.drc 累计平行长度 ≤ max_parallel 必然成立；真实判定仍由网级 v5.drc 门与
    route_check 终检作出（A9）。
    """
    r2 = view.hard_rules.get("R2", {})
    r2_min = float(r2.get("min_distance_mm", 3.0))
    for rect_d in view.sensitive_rect_ds:
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
    r5 = float(view.hard_rules.get("R5", {}).get("min_clearance_mm", 0.5))
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


def _astar(ctx, pid, net_id, width, start_pt, goal_pt, preferred_layer, variant,
           pitch=GRID_PITCH, window=None):
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
    start_pads = _endpoint_pad_layer_set(view, pid, 0)
    goal_pads = _endpoint_pad_layer_set(view, pid, 1)
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
    r5 = float(view.hard_rules.get("R5", {}).get("min_clearance_mm", 0.5))
    base_radius = int(math.ceil(r5 / pitch)) + 1

    def region(center, radius):
        out = set()
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if abs(dx) + abs(dy) <= radius:
                    x2, y2 = center[0] + dx, center[1] + dy
                    if 0 <= x2 <= nx and 0 <= y2 <= ny:
                        out.add((x2, y2))
        return out

    rad_a = max(base_radius,
                int(math.ceil((_endpoint_pad_extent(view, pid, 0) + r5)
                              / pitch)) + 1)
    rad_b = max(base_radius,
                int(math.ceil((_endpoint_pad_extent(view, pid, 1) + r5)
                              / pitch)) + 1)
    exempt_nodes = region(start, rad_a) | region(goal, rad_b)

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
        # 层间过渡（过孔）：同 (x,y) 换层——孔铜严格判定（D2，无同分区豁免）
        if out_of_window(p):
            continue
        for lj in range(len(layers)):
            if lj == li:
                continue
            if ctx.via_blocked(p, net_id) is not None:
                continue
            if _r2_edge_blocked(view, p, p, r2_mode):
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
                heapq.heappush(heap, (ng + h(ix, iy), h(ix, iy), counter, ix, iy, lj))
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
                        negotiation_log, plans=None):
    """单网一次完整尝试阶梯（升级件⑤ F4 从 execute_candidate 提取，供
    F4c rip-up 重布复用；计划序/日志行格式与 0.3.0 逐字节一致——
    negotiation_log 向后兼容红线）。plans=None=完整阶梯；调用方可传入
    计划前缀（F4c 被 rip 网有界重布，常量披露）。

    持有本网 staging 事务：成功 stage+commit 并返回
    (True, attempts, reason, entries, vias_n)；全耗尽则 rollback（状态指纹
    断言）并返回 (False, attempts, reason, None, 0)。
    """
    tx = _NetTransaction(ctx, net_id, pid)
    state_before = ctx.state_key()
    attempts = 0
    reason = "搜索空间耗尽"
    tried = set()
    for variant, scale, escape in (_attempt_plans() if plans is None
                                   else plans):
        pitch = GRID_PITCH * scale
        phase = variant["phase"] * 0.5 * pitch
        s_pt, g_pt = a_pt, b_pt
        esc_label = ""
        if escape is not None:
            end_tag, (dx, dy), rad = escape
            off = (dx * rad * pitch, dy * rad * pitch)
            if end_tag == "start":
                s_pt = (float(a_pt[0]) + off[0], float(a_pt[1]) + off[1])
                esc_label = " escape=start:(%+d,%+d)r%d" % (dx, dy, rad)
            else:
                g_pt = (float(b_pt[0]) + off[0], float(b_pt[1]) + off[1])
                esc_label = " escape=goal:(%+d,%+d)r%d" % (dx, dy, rad)
        pitch_label = "" if scale == 1.0 else " pitch=%g" % pitch
        s_key = _snap_grid(ctx.view, s_pt, pitch, phase)
        g_key = _snap_grid(ctx.view, g_pt, pitch, phase)
        if s_key is not None and g_key is not None:
            dedupe = (scale, s_key, g_key, _attempt_label(variant))
            if dedupe in tried:
                continue   # 吸附等价计划不重跑（不计 attempts）
            tried.add(dedupe)
        attempts += 1
        window = None
        if scale == _FINE_SCALE:
            window = _fine_window(ctx.view, a_pt, b_pt, s_pt, g_pt)
        result = _astar(ctx, pid, net_id, width, s_pt, g_pt,
                        assigned_layer, variant, pitch, window)
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


def _ripup_blocker_ids(ctx, net_id, width, a_pt, b_pt, reach):
    """F4c 确定性阻塞集：已布 A* 网按**提交序**（route_coppers 首现序），
    其铜落入 N 失败区域者——直连段 (width/2+R5) 走廊带或端点逃逸邻域
    (reach+R5) 盘（中心线口径，与 edge_blocked 的 R5 同式）。贪心最小集：
    逐网独立判定（每入选网自身铜命中失败区域=独立阻塞元素，无传递并集
    推断——过度入选由回滚兜底、欠选漏 rip 风险更高）；顺序=提交序（id 决
    胜底座）。全程无墙钟/随机/集合序。"""
    view = ctx.view
    r5 = float(view.hard_rules.get("R5", {}).get("min_clearance_mm", 0.5))
    corr_hw = width / 2.0 + r5
    disc = reach + r5
    order = []
    seen = set()
    for cu in ctx.route_coppers:
        if cu.net_id != net_id and cu.net_id not in seen:
            seen.add(cu.net_id)
            order.append(cu.net_id)
    by_net = {}
    for cu in ctx.route_coppers:
        if cu.net_id in seen:
            pts = [(float(p[0]), float(p[1])) for p in cu.polyline]
            by_net.setdefault(cu.net_id, []).extend(
                list(zip(pts[:-1], pts[1:])))
    hits = {}
    for mid in order:
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
    # 贪心入选（提交序；逐网独立阻塞元素，见 docstring）
    return [mid for mid in order if mid in hits]


def _ripup_retry(ctx, pid, net_id, width, a_pt, b_pt, layer, negotiation_log,
                 exec_of, budget):
    """F4c rip-up-and-retry（有界、确定性；docstring「升级件⑤-F4」节）。

    前置：net_id 已耗尽全部 attempts（阶梯已回滚，场景为耗尽时一致态）。
    exec_of：已提交网的执行参数账 {(net_id): (pid, width, a_pt, b_pt, layer)}
    （execute_candidate 按提交序记录，供被 rip 网原序重布）。budget：候选级
    全局轮数账 {"total": int}（调用方持有）。返回 (info, cause, n_extra)：
    info=None → 放弃 rip-up（cause=None=无阻塞集维持原几何归因，否则为
    ripup-* 归因串；n_extra=N 在重布阶梯中新增耗尽的 attempts 数，调用方
    并入 FAILED 总数披露）；info=(attempts_total, vias_n, entries, rerouted)
    → 成功，rerouted 为被 rip 网的重布结果 [(net_id, reroute_attempts,
    entries, vias_n)]（per_net 行更新由调用方执行）。
    """
    reach = _RIPUP_ESCAPE_REACH_MM
    rounds = 0
    n_extra = 0
    last_blockers = []
    last_fail = None   # None | ("reroute",) | ("victim", mid, reason)
    while rounds < _RIPUP_MAX_ROUNDS_PER_NET:
        if budget["total"] >= _RIPUP_MAX_TOTAL_PER_CANDIDATE:
            negotiation_log.append(
                "net=%s partition=%s ripup budget exhausted: global rounds "
                "=%d 已达上限 %d" % (net_id, pid, budget["total"],
                                     _RIPUP_MAX_TOTAL_PER_CANDIDATE))
            return None, ("ripup-exhausted（rip-up 预算耗尽：全局 %d 轮上限，"
                          "阻塞集=%s）" % (budget["total"], last_blockers)), n_extra
        blockers = _ripup_blocker_ids(ctx, net_id, width, a_pt, b_pt,
                                      reach * (rounds + 1))
        if not blockers:
            return None, None, n_extra   # 无已布网可 rip：维持原几何归因
        last_blockers = list(blockers)
        rounds += 1
        budget["total"] += 1
        negotiation_log.append(
            "net=%s partition=%s ripup round=%d ripped=%s "
            "reason=attempt-ladder exhausted" % (net_id, pid, rounds, blockers))
        snap = ctx.snapshot()
        state_before = ctx.state_key()
        for mid in blockers:
            ctx.rip_net(mid)
        ok, att, _reason, entries, vias_n = _run_attempt_ladder(
            ctx, pid, net_id, width, a_pt, b_pt, layer, negotiation_log)
        n_extra += att
        if not ok:
            ctx.restore(snap)
            if ctx.state_key() != state_before:
                raise ExecutorError("transaction",
                                    "rip-up 回滚后状态指纹不一致（内部错误）")
            negotiation_log.append(
                "net=%s partition=%s ripup round=%d reroute failed after %d "
                "attempts: %s → rolled back" % (net_id, pid, rounds, att,
                                                _reason))
            last_fail = ("reroute",)
            continue
        rerouted = []
        failed_mid = None
        fail_reason = None
        for mid in blockers:
            m_pid, m_width, m_a, m_b, m_layer = exec_of[mid]
            ok_m, att_m, reason_m, m_entries, m_vias = _run_attempt_ladder(
                ctx, m_pid, mid, m_width, m_a, m_b, m_layer, negotiation_log,
                plans=_attempt_plans()[:_RIPUP_REROUTE_MAX_PLANS])
            if not ok_m:
                failed_mid = mid
                fail_reason = reason_m
                break
            rerouted.append((mid, att_m, m_entries, m_vias))
        if failed_mid is not None:
            ctx.restore(snap)
            if ctx.state_key() != state_before:
                raise ExecutorError("transaction",
                                    "rip-up 回滚后状态指纹不一致（内部错误）")
            negotiation_log.append(
                "net=%s partition=%s ripup round=%d reroute of ripped net %s "
                "failed: %s → rolled back" % (net_id, pid, rounds, failed_mid,
                                              fail_reason))
            last_fail = ("victim", failed_mid, fail_reason)
            continue
        negotiation_log.append(
            "net=%s partition=%s ripup round=%d committed: N rerouted "
            "attempt=%d, ripped rerouted=%s"
            % (net_id, pid, rounds, att, [(m, a) for m, a, _e, _v in rerouted]))
        total = att + sum(a for _m, a, _e, _v in rerouted)
        return (total, vias_n, entries, rerouted), None, n_extra
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


def execute_candidate(board, candidate, out_dir=None):
    """L7 主入口（合同见模块 docstring）。纯确定性；同输入双跑 canonical 字节等。"""
    view = _BoardView(board)
    route_order, layer_assignment = _validate_candidate(board, candidate)
    ctx = _Context(board)
    negotiation_log = []
    per_net = []
    fixed_partitions = []
    ribbon_groups = {}
    pour_regions = {}
    failed = False
    exec_of = {}            # F4c：已提交网执行参数账（rip-up 原序重布用）
    budget = {"total": 0}   # F4c：候选级全局 rip-up 轮数（≤8，常量披露）

    for pid in route_order:
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
            continue
        # 2) 退化分区（升级件④模式A合同）：两端点重合 = trivially satisfied——
        #    零长 route 条目（polyline=[pt,pt]、层=候选指派层、无过渡/回流孔、
        #    宽=planned_width），仅作工件声明（零铜展宽：不入障碍/容量账本；
        #    route_check.build_scene 对零长 polyline 同规则跳过=无间距交互）。
        ends = partition["geometry"]["endpoints"]
        if _same_point(ends[0], ends[1]):
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
            continue
        # 3) A* 网（每网一个 staging 事务；每网可含多 run/多 entry）；
        #    尝试计划阶梯见模块 docstring「升级件④」「升级件⑤-F4」节
        #    （基线→细化→逃逸→F4a/F4b 细档，每次尝试策略入 negotiation_log；
        #    R1/R2/R5/R6 判定零改动）；耗尽后 F4c rip-up-and-retry 兜底。
        nets = view.nets_by_partition.get(pid) or [view.net_of.get(pid, pid)]
        width = _resolve_width(view, partition, pid)
        a_pt = partition["geometry"]["endpoints"][0]
        b_pt = partition["geometry"]["endpoints"][1]
        for net_id in nets:
            committed, attempts, reason, entries, vias_n = _run_attempt_ladder(
                ctx, pid, net_id, width, a_pt, b_pt, layer_assignment[pid],
                negotiation_log)
            ripup_cause = None
            if not committed:
                info, ripup_cause, n_extra = _ripup_retry(
                    ctx, pid, net_id, width, a_pt, b_pt,
                    layer_assignment[pid], negotiation_log, exec_of, budget)
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
                exec_of[net_id] = (pid, width, a_pt, b_pt,
                                   layer_assignment[pid])
                per_net.append({"partition_id": pid, "net_id": net_id,
                                "status": "routed", "attempts": attempts,
                                "negotiated": attempts > 1, "vias": vias_n,
                                "length_mm": round(sum(polyline_length(
                                    e["polyline"]) for e in entries), 10),
                                "width_mm": float(width),
                                "layers": [e["layer"] for e in entries]})
                continue
            negotiation_log.append(
                "net=%s partition=%s FAILED after %d attempts: %s"
                % (net_id, pid, attempts, reason))
            cause = ripup_cause
            if cause is None:
                cause = _exhaustion_cause(ctx, pid, net_id, width, a_pt, b_pt)
            negotiation_log.append(
                "net=%s partition=%s exhaustion-cause=%s" % (net_id, pid, cause))
            per_net.append({"partition_id": pid, "net_id": net_id,
                            "status": "failed", "attempts": attempts,
                            "negotiated": attempts > 1, "vias": 0,
                            "length_mm": 0.0, "width_mm": float(width),
                            "layers": []})
            failed = True
            break
        if failed:
            break

    if failed:
        return {"verdict": "FAILED", "routes": None, "per_net": per_net,
                "negotiation_log": negotiation_log}

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
        return {"verdict": "ROUTED", "routes": doc, "per_net": per_net,
                "negotiation_log": negotiation_log}
    tops = report["attributed_violations"][:3]
    detail = "; ".join("%s(%s↔%s)" % (v["rule"], v["subjects"][0], v["subjects"][1])
                       for v in tops)
    negotiation_log.append(
        "final route_check infeasible: %d 项归责违例（%s%s）→ 整体 FAILED、routes 回退为 None"
        % (len(report["attributed_violations"]), detail,
           " 等" if len(report["attributed_violations"]) > 3 else ""))
    return {"verdict": "FAILED", "routes": None, "per_net": per_net,
            "negotiation_log": negotiation_log}
