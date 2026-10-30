# -*- coding: utf-8 -*-
"""KiCad 写回导出器（L7 → 外权威对账，P4-G3；任务书 A9/U7）。

v5.board.v1 板 + v5.routes.v1 路由文档 → .kicad_pcb 文本。**口径：可制造走线
视图**——导出叠层（layers 表）、网络表（numbered ``(net N "name")`` 声明）、
走线段（routes[].polyline 逐段 → ``(segment)``，带 width/layer/net）、过孔
（transition_vias/return_vias 逐点 → ``(via)``，带 net）、板框（workspace →
gr_rect@Edge.Cuts）。

**round-trip 语义等范围（逐字披露）**：
- round-trip（write → ``v5.adapters.kicad_adapter.convert_file`` 读回）的语义等
  断言范围 = ①走线几何逐段逐层逐网相等（start/end/width/layer/net 全字段）；
  ②过孔位置逐点逐网相等；③网络表一致（net_id 集合与顺序）。
- **board 侧抽象层不在 round-trip 范围**：partitions（抽象端点不是可制造几何，
  见下 anchor pad）、zones、principle_registry、width_prior、hard_rules、
  stackup 的 kind/preferred_direction/available 元数据、negotiation_log——一律
  **不复刻**进 .kicad_pcb（唯一例外见下升级件②节：R5 口径**换算后**随配套
  .kicad_pro 落盘，不进 .kicad_pcb 本体）；workspace 数值亦然（adapter 读回时
  按铜几何重算，不与原板相等）。导出件里出现的分区号只是 anchor 命名标签，
  不是分区抽象的复刻。
- **板固孔（board.holes，V5-D8 全量入模）四类分开口径（0.7.0 OPT-11 D-B，
  逐字披露）**：①有网 TH 焊盘 → ``(pad 1 thru_hole … (drill 原值))``（oval
  原值转录、方向约定=孔长轴对齐 pad 外接盒长轴——board.v1 不携带旋转角，
  对常规同轴槽 annular 逐轴等值；位置精确匹配 board.holes；无匹配回退
  via_model 孔径=合成板/手搓板路径，0.6.0 前唯一口径）；②有网 NPTH 焊盘 →
  ``np_thru_hole`` + 原值（罕见形，plated 语义随 hole.plated 落型）；
  ③无网 NPTH → 机械孔落件（``V5-npth-N`` module、np_thru_hole、size=钻径、
  无 net、无发明铜，oval 长轴对齐 X）；④**无网 plated TH → 不落件**：真实
  焊盘环铜尺寸不入 board.v1 模型，落件必发明铜几何（发明环铜会制造本件所
  消除的同族假 DRC——annular/clearance 伪报）；丢弃面可机械核对
  （board.holes 全量清单 × 导出件 pad 位置对账）。

**文档化最小决定**：
- **anchor pad**：adapter 网表合同要求每个网 ≥1 个 pad（0-pad 网 fail-closed
  拒读），而 v5.board.v1 不携带真实 pad 几何（分区只有抽象端点）。故每分区
  两端点各导出一个退化锚点 pad（module ``V5-anchor-<净化分区号>-a/b``，无库
  昵称，升级件②起；pad 局部 ``(at 0 0)``，绝对坐标=端点，repr 浮点逐位精
  确；V5-R1 0.5.0 起多端点分区（≥3 端点、无 pad_terminals）端点 2..n-1
  消费侧各补一枚同规格 anchor）。单分区网的读回分区端点因此与原板逐位相等；
  多分区网读回时被 adapter 按「最远两点」合并为单分区（抽象层行为，不在
  round-trip 范围）。
- **网表语风 = numbered 模式**（KiCad ≤9：顶层 ``(net N "name")`` 声明 + 数字
  引用 ``(net N)``，version token 20171130 语风）。理由：语料主体与 adapter 的
  首选模式；网号按 board.nets 顺序 1..N 确定，读回网序=原板网序。
- **无注释语法**：s-expression 无注释（adapter 对裸 token fail-closed），故
  provenance 头走固定 ``(host v5.kicad_export "generator=… board_id=…
  board_sha256=…")`` 行——无日期，同输入双跑字节等。
- **via = 全叠层通孔**：``(layers <stackup 首> <stackup 尾>)``；size/drill 走
  板 ``via_model``（升级件①起；缺省文档化常量 drill 0.3 / annular 0.15，
  :func:`via_model_params` 唯一推导口）。层号用偶数编号惯例、Edge.Cuts=44
  （adapter 不消费层号，只要求唯一整数； Edge.Cuts 与铜层号冲突时顺延避让）。
- **不做几何/DRC 验证**（validator 与 v5.drc 的职守）；只做合同形状 fail-closed
  校验。错误一律 ValueError 子类 :class:`ExportError`，信息带键路径：
  routes.schema_version 不符 / board_id、board_sha256（含
  provenance.board_sha256）与板不匹配 / route 字段非法（未知网、未知分区、
  分区不属于该网、未知层、折线/孔位形状、宽度非正或非有限）/ 板无 net /
  **hard_rules.R5.min_clearance_mm 缺失或非正**（P5 升级件②起，净类口径透传
  fail-closed，见下）。
  路径越界由 ``v5.sidecar.assert_allowed`` 抛 SidecarViolation（只准 out/ 之
  下）；.kicad_pcb 非 .json，sidecar 检查器对它只查路径（与 write_view 同口径）。
- **确定性**（§3.4）：repr 浮点（逐位往返）、固定常数、无时间戳无随机、输入
  序即输出序——同输入双跑字节相等是硬测试。board 只读。零 LLM API、零网络
  （A8）；不装不调 kicad-cli（格式权威=adapter round-trip）。

**P5 升级件②（净类口径透传 + 封装库解析，双文件落盘）**：

kicad-cli（外权威）对 v5 合法导出件报成批「配置缺口」类违例，根因有二并
分别处置如下（kicad-cli 10.0.5 实测标定）。

1. **净类间距按板 R5 口径透传**——随导出件落 ``<同 stem>.kicad_pro``，内嵌
   Default 净类 ``(clearance=C, track_width=Wmin)`` 与板级
   ``board.design_settings.rules.min_track_width=Wmin``。
   **换算推导（文档化决定）**：KiCad 净类 clearance 是**边到边**约束，而 v5
   R5（``v5.drc.check_clearance`` → ``clearance.polyline_polyline``）对走线
   铜是**中心线**距离（Copper.half_width 不参与 gap）。对宽度 w1、w2 的两条
   不同网走线，v5 合法（中心线 ≥ R5）⇔ 边距 ≥ R5 − (w1+w2)/2。净类是单标量，
   取 **C = max(0, R5 − Wmax)**（Wmax = 本导出件全部走线宽度最大值；routes
   为空时回退分区 width_prior.w_max 最大值，再无则 0）。两个方向的论证：
   - **不伪报 v5 合法几何**：合法对边距 ≥ R5 − (w1+w2)/2 ≥ R5 − Wmax = C，
     KiCad 只对「实际边距 < C」报违例，故合法对不报（恰好擦边对受 KiCad
     内部 nm 量化 ±1e-6mm 影响，属确定性量化噪声，逐字披露）。
   - **不放过 v5 违例**：被报 ⇒ 边距 < C = R5 − Wmax ⇒ 中心线 <
     R5 − (Wmax − (w1+w2)/2) ≤ R5（w1+w2 ≤ 2·Wmax），即被报对必为 v5 侧
     间距违例（等式在 w1=w2=Wmax 时取到，KiCad "<" 与 v5 "< −EPS" 的擦边
     容差差异同样属 nm 级量化披露）。
   - **掩蔽窗口（披露）**：宽度对严格小于 (Wmax, Wmax) 的违例对，其中心线
     落于 [R5−(Wmax−(w1+w2)/2), R5) 区间时 kicad 不报——单标量净类不可能
     同时覆盖全部宽度组合；v5.drc 仍是间距判定唯一内源权威，kicad-cli 为
     外权威交叉对账，此窗口是口径换算的固有信息损失，非掩盖。
   - **下限 0 的语义（10.0.5 实测标定）**：板内含特宽走线（如 Wmax ≥ R5）时
     R5−Wmax < 0，任何正 C 都会把 v5 合法的宽线邻网对误报（v5 中心线口径
     允许物理边距为负，demo-02 实证：Wmax=2.1 > R5=0.5）。故取 **C=0**，
     并如实披露其实测语义：净类 clearance=0.0 时 kicad-cli 10.0.5 对铜皮
     ``clearance`` 与 ``shorting_items`` 两类**整体不再报告**（对照实验：
     同文件 C=0.01/0.05 短接 28 条回归、C=0.2 短接 27+间距 6 回归）——即
     该板形下 kicad 侧退化为孔间距/悬空/同位/未连检查，v5.drc 为间距判定
     唯一权威。``hole_clearance``（孔约束，min_hole_to_hole=0.25 内建缺省）
     不受净类约束支配照常报告；C=0 时其计数 2→6 属 kicad 内部 provider 与
     铜皮检查的去重关系变化（同批物理重叠对改由孔约束呈现），非新违例几何，
     逐字披露。
   - **走线宽度约束**：``min_track_width = Wmin``（导出走线宽度最小值，回退
     链同上）为**描述性下限**——导出件宽度按构造全部 ≥ Wmin，故零伪报；R1
     载流宽度判定仍在 v5.drc，kicad 侧该值只防「KiCad 缺省 0.2mm 最小宽度
     对合法细线的成批误报」（demo-02 实测 199 条）。
   - **过孔/锚点焊盘铜不在保证范围（②时披露；①已收口）**：②时 v5 间距
     场景不含过孔、焊盘=端点带抽象，该类残差属升级件①范围；①落地后
     过孔铜（via_model 圆铜）与真实焊盘铜（pad_terminals）已入 v5 场景，
     隐式 anchor 随 route 层落画（见「P5 升级件①」节），该披露收口。
   **为什么落在 .kicad_pro**：KiCad ≥6 起净类定义在项目文件而非板文件；
   导出件 version token 20171130（既有合同与语料口径，上游测试钉死）的板内
   ``(net_settings)`` 被 kicad-cli 10.0.5 旧版语法解析器拒绝（实测「未知标记
   net_settings」）。.kicad_pro 由 kicad-cli 对同目录同名项目文件**自动加载**
   （实测：净类 clearance=2.0 → clearance 违例 6→98，确证生效；部分字段
   JSON 其余键按 KiCad 内建缺省补全，与无项目文件时行为一致）。
2. **封装库解析（三选一：导出内嵌封装）**——anchor 焊盘 module 名从
   ``V5:anchor-<净化分区号>-a/b`` 改为 **无库昵称** 的
   ``V5-anchor-<净化分区号>-a/b``（去冒号）。KiCad 对带昵称的 lib_id 会查
   封装库表并逐 footprint 报「当前配置中不包含封装库 'V5'」（demo-02 实测
   30 条 lib_footprint_issues）；无昵称名即**板内嵌封装、无库依赖**，实测
   lib_footprint_issues=0 且不产生新违例类型。**弃选**其余两案：随导出件落
   ``.pretty`` 库目录+注册表需逐封装保证库内副本逐位一致（KiCad parity 对账
   引入新失败面）且多文件落盘面扩大；kicad-cli 运行配置（全局 fp-lib-table）
   注入会改用户全局 KiCad 配置、破坏可复现性——均劣于内嵌自足。
   adapter 只消费 footprint 的 (at)/pad 几何、不读 module 名（round-trip
   语义等不受影响，既有测试全绿为证）。

``project_kicad_pro_bytes`` 与 ``kicad_pcb_bytes`` 同为纯函数（确定性、双跑
字节等）；:func:`write_kicad_pcb` 一并落两件（sidecar 双路径核验），返回
.kicad_pcb 路径不变。R5 缺失/非正时两函数一并 fail-closed（半成品不落盘）。

**P5 升级件①（出口合同升级 D1-D5，叠加在②之上）**：

- **焊盘铜按板画（D1/D5）**：分区带 ``geometry.pad_terminals`` → 逐项按
  真实焊盘铜画（shape circle/rect、size 逐项转录；完整 pad 行画法⑥起按
  真实层跨，见下「P5⑥ 出口对齐」节）；
  无 pad_terminals → 隐式 anchor（rect ``ANCHOR_PAD_SIZE_MM``²、层=首个**可用
  信号层**——比②前的 stackup[0] 更严：与 route_check 世界模型隐式 anchor 铜
  同层，平面层在首的板不再把 anchor 画进不可布线层）。归一口
  :func:`partition_pads`（世界模型与导出共用，语义校验 fail-closed）。
  多网共分区仍每网各画一份（抽象板合同形状；真实板分区每网一个不重影）。
  实测定向：多层铜 SMD pad 被 kicad-cli 10.0.5 判 ``padstack`` 违例
  （「贴片焊盘在电路板的两面都有铜层」），故隐式 anchor/真实 SMD 焊盘一律
  单层铜；跨层连通由端点过孔承担（同网孔穿自网焊盘实测不报 hole_clearance）。
- **过孔去重 + 真实孔径（D2/D5）**：同网同坐标 via 只画一次（多 entry 在
  衔接点双方披露同一物理孔——②后残差 ``holes_co_located`` 的直接根因）；
  size/drill=``via_model_params(board)``（adapter 从真实板 (via) 众数落
  ``via_model``，缺省 0.3/0.15 常量）。
- 本件不改净类/封装口径（② landed 形状保持：去昵称、.kicad_pro 双件、
  R5 透传换算 C = max(0, R5 − w_max)）。

**P5⑥ 出口对齐（D6-1/D6-2，合同 P5-WAVE6-2026-09-16 §2；纯导出侧，版本
0.4.0 起）**：

- **焊盘真实层跨画法（D6-1）**：⑥前 ``layers=="all"`` 一律展开为**全部信号层**
  并按 ``smd`` 画——通孔焊盘（adapter 对源板 ``*.Cu`` 通孔层跨落 "all"）被画成
  双面铜 SMD，kicad-cli 10.0.5 判 ``padstack`` 违例（「贴片焊盘在电路板的两面
  都有铜层」，pre-⑥ 5 板实测 3/22/18/22/28 条）；且 SMD 焊盘的 connectivity
  被收缩到模块侧面，自反面到达的走线末端悬空（``track_dangling`` 族根因）。
  ⑥起废除该兜底，按真实层跨画：
  - ``layers=="all"``（=通孔标记）→ ``(pad 1 thru_hole … (drill D)
    (layers "*.Cu"))``——KiCad 通孔焊盘规范形（与语料源板逐字同形），
    ``*.Cu`` 由 kicad 按板 (layers) 表解析为全部铜层=真实通孔层跨；
    ``D`` 优先=board.holes 位置匹配的**原孔径**（0.7.0 OPT-11 D-B；oval 原值
    转录、方向约定见模块 docstring「板固孔四类分开口径」节，plated=False 落
    np_thru_hole），无匹配回退 ``via_model_params(board)["drill"]``（板级孔径
    推导口，缺省 0.3；合成板无 holes 键路径）。
    无网 TH/NPTH 机械孔口径见模块 docstring「板固孔四类分开口径」节。
  - 显式层 id 列表（=SMD 焊盘声明铜层）→ ``(pad 1 smd …)`` 单层，正/背面由
    声明层定（F 族=正面、B 族=背面，不翻转不猜测）。语料全量扫描（17 板
    A 层源）：SMD 焊盘全部单铜层、非通配多铜层列表 0 条——列表逐项转录
    不另设单层约束（发明校验=无据加严）。
  - layers 字段缺失/非法（非 "all" 的字符串、空表、未知层 id、非列表）→
    :class:`ExportError` fail-closed（键路径 ``pad_terminals[i].layers``），
    **无任何 "all" 兜底/静默回退**。归一口 :func:`partition_pads` 返回值增
    ``through_hole`` 键，并按调用方传入的铜层域展开 "all"（导出侧传全铜层=
    真实通孔层跨；route_check 世界模型传信号层——世界模型行为⑥内零改写，
    本件纯导出侧）。
- **逃逸桩端点扎铜（D6-2）**：走线段绘制前对**网级真端点**（首 entry 首、
  末 entry 末；换层衔接点与中间点绝不吸附）做对齐：按分区端点近端指派
  （argmin 全端点、平手取索引最小——V5-R1 0.5.0 多端点化），被指派端点的
  同位焊盘按到达层匹配优先；端点已在
  焊盘铜内原样（链合同数据端点=焊盘心，现网导出零扰动）；在铜外但处于
  端点邻域 ``ANCHOR_PAD_SIZE_MM``（1.0mm，隐式 anchor 铜尺度；逃逸阶梯最大
  位移 0.75mm 同量级）内则沿指向焊盘心方向扎入铜区
  （:func:`align_endpoint_into_pad`，铜边界与焊盘心的中点，严格在铜内）；
  邻域外原样——首末点=分区端点的链合同由 route_check 审计，导出不掩盖
  合同违例、不发明长段几何。v5 routes 本体不动。ribbon 带段逐网绘制时
  真端点同规则对齐。
"""
import hashlib
import json
import math
import os

from . import sidecar
from .adapters.kicad_adapter import sanitize_net_id
from .drc import normalize_net_classes

GENERATOR = "v5.kicad_export"
# 0.7.0 = OPT-11（pcbflow-optimap EXEC-R1，S5 F1/F2 修复；路线图
# FINAL-ROADMAP-2026-10-08.md:179-187）：
# D-A 空成员净类：_per_class_params 对声明在板但成员为空的净类（anavi 12V/
# usb/vcc 形态）不再走 max() 空集裸 ValueError（0.6.0 确定性崩溃，S5 五跑签名
# 等值 0158686d…）；改为显式跳过该类的 per-class 写出，并在
# netclass_mask_table 逐字披露（empty_net_classes[].status=
# "not_available_no_members"）。选跳过而非 ExportError：空成员类无类内走线
# ⇒ 宽度界不存在、无网对参与 KiCad 跨类 max ⇒ 不写出对 DRC 惰性；fail-closed
# 语义由披露承载（非静默——mask 随件落盘，缺类板不落件路径不变）。
# D-B TH drill 分开建模（消除统一 via_model 孔径的假 DRC，S5 sdi 28 条
# drill_out_of_range）：①有网 TH 焊盘孔径优先取 board.holes 原值（位置精确
# 匹配；oval 原值转录，方向约定=孔长轴对齐 pad 外接盒长轴——board.v1 不带
# 旋转角，对常规同轴槽 annular 逐轴等值），无匹配回退 via_model 孔径（合成板
# 无 holes 键路径逐字节不变）；②孔型随 hole.plated 落 thru_hole/np_thru_hole
# （有网 NPTH 罕见形语义修正）；③无网 NPTH 机械孔落件（module V5-npth-N，
# np_thru_hole、size=钻径、无 net、无发明铜，oval 长轴对齐 X）；④无网
# plated TH 不落件（真实环铜不入 board.v1 模型，落件必发明几何——与本修复
# 消除的假 DRC 同类；丢弃面=board.holes 全量清单，契约披露于模块 docstring）。
# 0.6.0 = V5-R7 W-2：per-class 净类写出（board.net_classes 非空 ⇒ Default +
# 逐类 classes + netclass_assignments（meta v4 列表形，KiCad 8.99 语料口径）；
# 缺类板 .kicad_pro 逐字节不变）+ 掩蔽窗口逐项消除表随件落盘
# （<stem>.netclass-mask.json，仅类板落盘）；KiCad 跨类间距=max 两类
# clearance（与 v5 网对 max 同构 ⇒ 单类换算窗口按类收敛）。
# 0.5.0 = V5-R1 ED-X 修复（任务书 V5-R1-EDX-EXPORT-FIX-2026-09-26，用户三裁
# 候选 B）：_validate 端点合同「恰 2」→「≥2 逐点 _check_pair」（R1 世界全
# 端点入模后多端网板首次走到 export，ED-X=旧 2 端网时代口径在 round-trip
# 前置合同的遗留缺口）；pads 发射 per_end/tag 域 0..n_ep-1（endpoint ≥2 前缀
# e<k>，a/b 旧域逐位不变）；D6-2 近端指派 argmin 全端点（平手取索引最小=旧
# d0<=d1 取 0 语义推广）；隐式 anchor 多端点补发=消费侧后处理（partition_pads
# 本体零改→route_check 世界模型行为零穿透）。2 端旧域输出逐位不变（既有钉全
# 绿为证）。
# 0.4.0 = P5⑥-D6-1/D6-2（合同 P5-WAVE6-2026-09-16，纯导出侧）：焊盘真实层跨
# 画法（thru_hole + (layers "*.Cu") + via_model drill；废除 "all"→全部信号层
# 兜底）+ 逃逸桩端点扎铜对齐（align_endpoint_into_pad）；
# 0.3.0 = P5 升级件①（D1-D5：pad_terminals/via_model/过孔去重）。
VERSION = "0.7.0"

BOARD_SCHEMA_VERSION = "v5.board.v1"
ROUTES_SCHEMA_VERSION = "v5.routes.v1"

#: 输出语风 = KiCad ≤9 numbered 网表（顶层 (net N "name") + 数字引用）。
KICAD_VERSION_TOKEN = "20171130"
#: 板厚装饰字段（KiCad 惯例；adapter 不消费）。
BOARD_THICKNESS_MM = 1.6
#: 板框层与线宽（gr_rect@Edge.Cuts，真实 KiCad 的板框口径）。
EDGE_CUTS_LAYER = "Edge.Cuts"
EDGE_CUTS_NUM = 44
EDGE_LINE_WIDTH_MM = 0.05
#: anchor pad 尺寸（固定常数；只供 adapter 网表落链，非真实焊盘）。
ANCHOR_PAD_SIZE_MM = 1.0
#: via 固定孔径缺省（升级件① D2 文档化常量：drill 0.3 / annular 0.15，
#: 孔铜半径 = drill/2 + annular = 0.3mm；真实板孔径经 board.via_model 由
#: adapter 读取落板，缺省兜底）。
VIA_SIZE_MM = 0.6
VIA_DRILL_MM = 0.3
VIA_ANNULAR_MM = 0.15


def via_model_params(board):
    """板过孔几何参数（D2 唯一推导口）：dict(drill, annular, size, radius)。

    board.via_model 可选键（adapter 从真实 .kicad_pcb 的 (via) (size)/(drill)
    众数读取）；缺省用本模块文档化常量 drill 0.3 / annular 0.15。非法值
    （非正 drill / 负 annular）raise ExportError（fail-closed）。size =
    drill + 2·annular（KiCad via size=铜盘外径），radius = size/2（v5 场景
    孔铜圆半径）。返回新 dict（调用方可改）。
    """
    vm = board.get("via_model") if isinstance(board, dict) else None
    drill = VIA_DRILL_MM
    annular = VIA_ANNULAR_MM
    if vm is not None:
        if not isinstance(vm, dict):
            _fail("board.via_model", "须为 dict，实得 %s" % type(vm).__name__)
        d = vm.get("drill_mm")
        a = vm.get("annular_mm")
        if not _is_num(d) or float(d) <= 0.0:
            _fail("board.via_model.drill_mm", "须为正的有限数值，实得 %r" % (d,))
        if not _is_num(a) or float(a) < 0.0:
            _fail("board.via_model.annular_mm", "须为非负有限数值，实得 %r" % (a,))
        drill = float(d)
        annular = float(a)
    return {"drill": drill, "annular": annular,
            "size": drill + 2.0 * annular, "radius": drill / 2.0 + annular}


class ExportError(ValueError):
    """routes/板合同不满足（fail-closed，信息带键路径）。"""


def _fail(path, msg):
    raise ExportError("[%s] %s" % (path, msg))


def _is_num(v):
    """JSON 数值（bool 除外）且有限。"""
    return (isinstance(v, (int, float)) and not isinstance(v, bool)
            and math.isfinite(float(v)))


def _check_pair(v, path):
    """[x, y] 有限数值对校验。"""
    if not isinstance(v, (list, tuple)) or len(v) != 2 or not all(_is_num(c) for c in v):
        _fail(path, "应为 [x, y] 有限数值对，实得 %r" % (v,))


def _check_pairs(v, path):
    """[[x, y], ...] 列表校验。"""
    if not isinstance(v, list):
        _fail(path, "应为 [[x, y], ...] 列表，实得 %r" % (v,))
    for j, pt in enumerate(v):
        _check_pair(pt, "%s[%d]" % (path, j))


def _validate(board, routes):
    """合同形状 fail-closed 校验；返回导出上下文（emission 只用已验证字段）。"""
    if not isinstance(board, dict):
        _fail("board", "board 必须为 dict")
    if board.get("schema_version") != BOARD_SCHEMA_VERSION:
        _fail("board.schema_version",
              "应为 %r，实得 %r" % (BOARD_SCHEMA_VERSION, board.get("schema_version")))
    prov = board.get("provenance")
    if not isinstance(prov, dict) or not isinstance(prov.get("board_sha256"), str):
        _fail("board.provenance.board_sha256", "缺 board_sha256（板须先过 load_board 落链）")
    bsha = prov["board_sha256"]

    if not isinstance(routes, dict):
        _fail("routes", "routes 文档必须为 dict")
    if routes.get("schema_version") != ROUTES_SCHEMA_VERSION:
        _fail("routes.schema_version",
              "应为 %r，实得 %r" % (ROUTES_SCHEMA_VERSION, routes.get("schema_version")))
    if routes.get("board_id") != board.get("board_id"):
        _fail("routes.board_id",
              "与板不匹配: %r != %r" % (routes.get("board_id"), board.get("board_id")))
    if routes.get("board_sha256") != bsha:
        _fail("routes.board_sha256",
              "与板不匹配: %r != %r" % (routes.get("board_sha256"), bsha))
    rprov = routes.get("provenance")
    if rprov is not None:
        if not isinstance(rprov, dict):
            _fail("routes.provenance", "存在时必须为 dict")
        if rprov.get("board_sha256") is not None and rprov["board_sha256"] != bsha:
            _fail("routes.provenance.board_sha256",
                  "与板不匹配: %r != %r" % (rprov.get("board_sha256"), bsha))
    nlog = routes.get("negotiation_log")
    if nlog is not None:
        if not isinstance(nlog, list) or not all(isinstance(s, str) for s in nlog):
            _fail("routes.negotiation_log", "存在时必须为字符串列表")
    entries = routes.get("routes")
    if not isinstance(entries, list):
        _fail("routes.routes", "必须为列表（实得 %s）" % type(entries).__name__)

    # ---- 板侧：stackup / workspace / partitions / nets（只校验导出消费的字段）
    hard = board.get("hard_rules")
    r5 = hard.get("R5") if isinstance(hard, dict) else None
    if not isinstance(r5, dict) or not _is_num(r5.get("min_clearance_mm")) \
            or float(r5["min_clearance_mm"]) <= 0.0:
        _fail("board.hard_rules.R5.min_clearance_mm",
              "须为正的有限数值（净类口径透传 fail-closed；schema 本必填），"
              "实得 %r" % (r5.get("min_clearance_mm") if isinstance(r5, dict)
                           else r5,))

    stackup = board.get("stackup")
    if not isinstance(stackup, list) or not stackup:
        _fail("board.stackup", "须为非空列表")
    layer_ids = []
    for i, layer in enumerate(stackup):
        lid = layer.get("id") if isinstance(layer, dict) else None
        if not isinstance(lid, str) or not lid:
            _fail("board.stackup[%d].id" % i, "须为非空字符串，实得 %r" % (lid,))
        if layer.get("kind") not in ("signal", "plane"):
            _fail("board.stackup[%d].kind" % i,
                  "须为 signal|plane，实得 %r" % (layer.get("kind"),))
        if lid in layer_ids:
            _fail("board.stackup[%d].id" % i, "层 id 重复: %r" % lid)
        layer_ids.append(lid)
    ws = board.get("workspace")
    if not isinstance(ws, dict):
        _fail("board.workspace", "须为 dict")
    for key in ("x_min", "y_min", "x_max", "y_max"):
        if not _is_num(ws.get(key)):
            _fail("board.workspace.%s" % key, "须为有限数值，实得 %r" % (ws.get(key),))

    parts = board.get("partitions")
    if not isinstance(parts, list):
        _fail("board.partitions", "须为列表")
    part_by_id = {}
    for i, part in enumerate(parts):
        pid = part.get("partition_id") if isinstance(part, dict) else None
        if not isinstance(pid, str) or not pid:
            _fail("board.partitions[%d].partition_id" % i, "须为非空字符串")
        if pid in part_by_id:
            _fail("board.partitions[%d].partition_id" % i, "重复: %r" % pid)
        geo = part.get("geometry")
        eps = geo.get("endpoints") if isinstance(geo, dict) else None
        # V5-R1 ED-X（0.5.0）：端点合同放宽「恰 2」→「≥2 逐点」——R1 世界
        # （W-2 全端点入模）多端网分区合法；2 端域逐点校验等价旧两行。
        if not isinstance(eps, list) or len(eps) < 2:
            _fail("board.partitions[%d].geometry.endpoints" % i,
                  "须为 ≥2 端点列表")
        for j, pt in enumerate(eps):
            _check_pair(pt, "board.partitions[%d].geometry.endpoints[%d]" % (i, j))
        part_by_id[pid] = part

    nets = board.get("nets")
    if not isinstance(nets, list) or not nets:
        _fail("board.nets", "板无任何 net（adapter 对 0 网板同样 fail-closed，无法 round-trip）")
    net_num = {}
    net_parts = {}
    for i, net in enumerate(nets):
        nid = net.get("net_id") if isinstance(net, dict) else None
        if not isinstance(nid, str) or not nid:
            _fail("board.nets[%d].net_id" % i, "须为非空字符串")
        if nid in net_num:
            _fail("board.nets[%d].net_id" % i, "重复: %r" % nid)
        net_num[nid] = len(net_num) + 1
        refs = net.get("partitions")
        if not isinstance(refs, list) or not refs:
            _fail("board.nets[%d].partitions" % i, "须为非空列表（schema minItems=1）")
        for j, ref in enumerate(refs):
            if not isinstance(ref, str) or ref not in part_by_id:
                _fail("board.nets[%d].partitions[%d]" % (i, j),
                      "指向不存在的分区 %r" % (ref,))
        net_parts[nid] = list(refs)

    # ---- V5-R7 W-2：net_classes 结构+成员耦合校验（drc 单源归一；schema 无
    # patternProperties 面，拓扑同例消费侧核）+ 类板视图
    try:
        nc_norm = normalize_net_classes(board.get("net_classes"))
    except ValueError as exc:
        _fail("board.net_classes", str(exc))
    for name, cls in nc_norm.items():
        for net in cls["members"]:
            if net not in net_num:
                _fail("board.net_classes.%s.members" % name,
                      "成员网 %r 不在 board.nets（fail-closed）" % net)

    # ---- 板固孔（0.7.0 OPT-11 D-B）：board.holes 可选键（V5-D8 adapter 全量
    #      入模：全部 TH/NPTH 钻孔，不分网成员资格）——TH 焊盘原孔径与机械孔
    #      落件的唯一来源。缺键=合成板/手搓板缺省路径（TH 回退 via_model 孔径，
    #      零机械孔，0.6.0 行为不变）；在场则逐项 fail-closed（本模块只校验
    #      消费字段口径，与 R5 同板级合同）。
    holes = None
    holes_raw = board.get("holes")
    if holes_raw is not None:
        if not isinstance(holes_raw, list):
            _fail("board.holes", "须为列表（V5-D8 板固孔清单），实得 %s"
                  % type(holes_raw).__name__)
        holes = []
        for i, h in enumerate(holes_raw):
            where = "board.holes[%d]" % i
            if not isinstance(h, dict):
                _fail(where, "须为 dict，实得 %s" % type(h).__name__)
            pos = h.get("pos_mm")
            _check_pair(pos, where + ".pos_mm")
            drill = h.get("drill_mm")
            if not _is_num(drill) or float(drill) <= 0.0:
                _fail(where + ".drill_mm", "须为正的有限数值，实得 %r" % (drill,))
            plated = h.get("plated")
            if not isinstance(plated, bool):
                _fail(where + ".plated", "须为 bool，实得 %r" % (plated,))
            shape = h.get("shape")
            entry = {"pos": (float(pos[0]), float(pos[1])), "drill": float(drill),
                     "plated": plated, "shape": shape}
            if shape == "oval":
                size = h.get("size_mm")
                if (not isinstance(size, list) or len(size) != 2
                        or not all(_is_num(v) and float(v) > 0.0 for v in size)):
                    _fail(where + ".size_mm",
                          "oval 孔须携带 [a, b] 两个正钻径值，实得 %r" % (size,))
                entry["size"] = [float(size[0]), float(size[1])]
            elif shape != "circle":
                _fail(where + ".shape", "须为 circle|oval，实得 %r" % (shape,))
            holes.append(entry)

    # ---- route 逐条校验
    for i, r in enumerate(entries):
        where = "routes.routes[%d]" % i
        if not isinstance(r, dict):
            _fail(where, "须为 dict")
        pid = r.get("partition_id")
        if not isinstance(pid, str) or not pid:
            _fail(where + ".partition_id", "须为非空字符串，实得 %r" % (pid,))
        if pid not in part_by_id:
            _fail(where + ".partition_id", "指向不存在的分区 %r" % (pid,))
        nid = r.get("net_id")
        if not isinstance(nid, str) or not nid:
            _fail(where + ".net_id", "须为非空字符串，实得 %r" % (nid,))
        if nid not in net_num:
            _fail(where + ".net_id", "未知网 %r（板 nets 无此 id）" % (nid,))
        if pid not in net_parts[nid]:
            _fail(where + ".partition_id",
                  "分区 %r 不属于网 %r（该网分区=%r）" % (pid, nid, net_parts[nid]))
        layer = r.get("layer")
        if not isinstance(layer, str) or layer not in layer_ids:
            _fail(where + ".layer", "未知层 %r（须为 stackup id 之一）" % (layer,))
        poly = r.get("polyline")
        if not isinstance(poly, list) or len(poly) < 2:
            _fail(where + ".polyline", "须为 ≥2 点的 [[x, y], ...] 列表，实得 %r" % (poly,))
        _check_pairs(poly, where + ".polyline")
        width = r.get("width")
        if not _is_num(width) or float(width) <= 0.0:
            _fail(where + ".width", "须为正的有限数值，实得 %r" % (width,))
        for key in ("transition_vias", "return_vias"):
            v = r.get(key)
            if v is None:
                continue  # 缺省按空（合同字段；容忍省略，形状存在则须合法）
            _check_pairs(v, "%s.%s" % (where, key))

    return {
        "board_sha256": bsha,
        "entries": entries,
        "net_num": net_num,
        "net_parts": net_parts,
        "part_by_id": part_by_id,
        "stackup": stackup,
        "workspace": ws,
        "net_classes": nc_norm,   # V5-R7 W-2：归一 net_classes（空 dict=缺类板）
        "holes": holes,           # 0.7.0 OPT-11：归一板固孔（None=缺键缺省路径）
    }


def _exported_width_bounds(board, entries):
    """导出件走线宽度界 (w_max, w_min)；routes 空时回退分区 width_prior，
    再无则 (0.0, 0.0)（确定性回退链，docstring「净类口径透传」披露）。"""
    widths = [float(r["width"]) for r in entries]
    if not widths:
        for p in board.get("partitions") or []:
            wp = p.get("width_prior") if isinstance(p, dict) else None
            if isinstance(wp, dict):
                if _is_num(wp.get("w_max")):
                    widths.append(float(wp["w_max"]))
                if _is_num(wp.get("w_min")):
                    widths.append(float(wp["w_min"]))
    if not widths:
        return 0.0, 0.0
    return max(widths), min(widths)


def _net_class_params(board, entries):
    """净类透传参数推导（docstring 换算推导的唯一实现）。

    返回 dict(clearance, track_width, w_max, w_min)；数值 round 到 9 位小数
    （nm 级量化，远低于 KiCad 1e-6 mm 内部分辨率，确定性披露于 docstring）。
    """
    r5 = float(board["hard_rules"]["R5"]["min_clearance_mm"])
    w_max, w_min = _exported_width_bounds(board, entries)
    return {
        "clearance": round(max(0.0, r5 - w_max), 9),
        "track_width": round(w_min, 9),
        "w_max": round(w_max, 9),
        "w_min": round(w_min, 9),
    }


#: .kicad_pro net_settings.meta.version（KiCad 10.0.5 项目文件实测口径）。
PRO_NET_SETTINGS_META_VERSION = 4

#: 掩蔽窗口消除判定容差（mm）：C 取 9 位小数量化（nm 级）后残差 ≤ 此值即判
#: 消除（与 KiCad 内部 nm 量化同级，docstring「净类口径透传」披露族）。
MASK_ELIM_EPS = 1e-9

#: 缺省净类名（KiCad 同名；adapter 双源 P4 同源）。
PRO_DEFAULT_CLASS = "Default"

#: A1（EXEC-R3 R3-2，G1 A 口径）：.netclass-mask.json 侧车 schema 版本。
#: 2 = 值权威面——① classes/empty_net_classes 逐项补 ``v5_width_mm``（源类宽；
#:    Default 恒 null=not_available，源 Default 线宽不入 board 模型，不用
#:    width_prior/导出 track_width 冒充）；② 缺类板也落 mask（Default 单类
#:    最小形——旧「缺类板不落件」口径废除）；③ 新增 ``pcb_sha256``/
#:    ``pro_sha256`` 实际导出件内容绑定（adapter 归属核验三重对上才采值，
#:    board_sha256 绑导出 PCB host 行原模型 hash）。
#: 1 = 历史形态（仅 v5_clearance_mm、仅类板、无内容绑定）——adapter 对未知/
#: 缺版本 fail-closed 不采值。rule 字串 "netclass-mask-v1" 不变（文档族名）。
MASK_SCHEMA_VERSION = 2


def _class_net_widths(board, entries, net_parts, part_by_id, nets):
    """类内网的导出走线宽度集合（确定性 sorted 列表）。

    宽度源（回退链逐网独立）：该网 routes entry 实测宽度 → 无 entry 网取其
    各分区 width_prior {w_min, w_max} 两界 → 再无 → {0.0}。"""
    by_net = {}
    for r in entries:
        by_net.setdefault(r["net_id"], set()).add(float(r["width"]))
    widths = set()
    for nid in nets:
        ws = by_net.get(nid)
        if ws:
            widths |= ws
            continue
        found = False
        for pid in net_parts.get(nid, ()):
            wp = (part_by_id.get(pid) or {}).get("width_prior")
            if isinstance(wp, dict):
                lo, hi = wp.get("w_min"), wp.get("w_max")
                if _is_num(lo):
                    widths.add(float(lo))
                    found = True
                if _is_num(hi):
                    widths.add(float(hi))
                    found = True
        if not found:
            widths.add(0.0)
    return sorted(widths)


def _per_class_params(board, ctx):
    """V5-R7 W-2 per-class 透传推导（docstring 换算推导的逐类推广）。

    返回 None（缺类板——走 _net_class_params 旧单类路径，bytes 逐字节不变）
    或 dict：{"classes": [ {name, v5_clearance, kicad_clearance, track_width,
    widths} ...（Default 首位，余按名字典序）], "assignments": {net:[cls]},
    "empty_classes": [ {name, v5_clearance, status} ]}。
    逐类：t_cls=类 v5 间距（Default=R5 标量）；w_max_cls/w_min_cls=类内网
    宽度界（_class_net_widths 回退链）；kicad_clearance=max(0, t_cls−
    w_max_cls) round 9（KiCad 跨类间距=max 两类 clearance——与 v5 网对 max
    同构）。空成员类（0.7.0 OPT-11 D-A）不入 classes、入 empty_classes 披露。"""
    nc = ctx["net_classes"]
    if not nc:
        return None
    r5 = float(board["hard_rules"]["R5"]["min_clearance_mm"])
    classed_nets = {}
    for name, cls in nc.items():
        for net in cls["members"]:
            classed_nets.setdefault(net, set()).add(name)
    default_nets = [nid for nid in ctx["net_num"] if nid not in classed_nets]
    names = [PRO_DEFAULT_CLASS] + sorted(nc)
    members = {PRO_DEFAULT_CLASS: default_nets}
    for name, cls in nc.items():
        members[name] = sorted(cls["members"])
    params = []
    empty_classes = []
    for name in names:
        t = r5 if name == PRO_DEFAULT_CLASS else float(nc[name]["clearance_mm"])
        if not members[name]:
            # 0.7.0 OPT-11 D-A：空成员净类（声明在板、成员=[]——anavi 12V/usb/
            # vcc 形态；Default 空=全网民皆有类）。0.6.0 在此走 max() 空集以裸
            # ValueError 确定性崩溃（kicad_export.py:551 旧行号，S5 F1 五跑签名
            # 等值）。空成员类无类内走线 ⇒ 宽度界（w_max/w_min）不存在；无成员
            # ⇒ 无网对参与 KiCad 跨类 max(clearance) ⇒ 不写出对 DRC 惰性。
            # 处置=显式跳过 per-class 写出 + netclass_mask_table 逐字披露
            # （not_available_no_members）——不发明宽度界、不静默丢语义。
            empty_classes.append({"name": name, "v5_clearance_mm": t,
                                  "status": "not_available_no_members"})
            continue
        widths = _class_net_widths(board, ctx["entries"], ctx["net_parts"],
                                   ctx["part_by_id"], members[name])
        w_max, w_min = max(widths), min(widths)
        params.append({
            "name": name,
            "v5_clearance": t,
            "kicad_clearance": round(max(0.0, t - w_max), 9),
            "track_width": round(w_min, 9),
            "widths": widths,
            "members": members[name],
        })
    assignments = {}
    for net, names_of in classed_nets.items():
        assignments[net] = sorted(names_of)
    return {"classes": params, "assignments": assignments,
            "empty_classes": empty_classes}


def netclass_mask_table(board, routes, pcb_data=None, pro_data=None):
    """V5-R7 W-2 掩蔽窗口逐项消除表 + A1 值权威侧车（纯函数；随件落盘
    <stem>.netclass-mask.json）。

    A1（EXEC-R3 R3-2，G1 A 口径，schema_version=MASK_SCHEMA_VERSION=2）三面：
    - **值保真面**：``classes`` 逐类补 ``v5_width_mm``（源 board.net_classes
      类宽原值）；``empty_net_classes`` 逐项补 ``v5_width_mm``（空成员类原宽
      原距随件保全）。Default 项 ``v5_width_mm=null`` = not_available——源
      Default 线宽不入 board 模型，不用 width_prior/导出 track_width 冒充。
    - **缺类板也落 mask**（旧版返回 None 不落件）：Default 单类最小形——
      缺类形态板的原 R5 唯一可信回程载体；缺类板 ``.kicad_pcb``/``.kicad_pro``
      两件本体 bytes 不因此变（pro 仍走旧单类 doc 逐字节不变）。
    - **内容绑定**：``pcb_sha256``/``pro_sha256``=实际导出 .kicad_pcb/
      .kicad_pro bytes 的 sha256（``pcb_data``/``pro_data`` 调用方可传预推导
      bytes，缺省本函数内自行推导——同输入双跑字节等）；``board_sha256``=
      导出 PCB host 行的原模型 hash（≠导出 PCB 文件 hash、≠回读 b2 模型
      hash，三种对象不混比）。adapter A1 读面须三重全对上才采值，任何不匹配
      fail-closed（kicad_adapter.load_netclass_mask_binding/
      _apply_netclass_mask_values）。

    逐类对 (X,Y)（Default+各类、X≤Y 字典序）：v5 所需中心线间距 t_pair=
    max(t_X,t_Y)（R5 网对口径）；KiCad 有效边距 C_pair=max(C_X,C_Y)（KiCad
    跨类=max 两类 clearance）；类内宽度组合 (w_a,w_b)∈widths_X×widths_Y 的
    掩蔽残差 = t_pair−(w_a+w_b)/2−C_pair（>0 即 v5 违例而 kicad 不报的窗口
    ——单标量净类固有信息损失，per-class 写出后按类收敛，均匀宽度类对窗口
    归零）。eliminated=全部组合残差 ≤ MASK_ELIM_EPS。空成员净类（0.7.0
    OPT-11 D-A）不入 classes/pairs（无类内走线 ⇒ 无宽度组合 ⇒ 无掩蔽窗口），
    逐项入 ``empty_net_classes``（status="not_available_no_members"，A1 起并
    携带原宽原距）披露——跳过即披露，非静默。缺类板最小形的 width 界与
    pairs 用类内网宽度集（_class_net_widths，与 per-class 路径同口径），
    kicad_clearance_mm/track_width_mm 则与实际落盘 .kicad_pro 单类值一致
    （_net_class_params；两条回退链仅在 routes 非空时可能不同，披露不混同）。"""
    ctx = _validate(board, routes)
    if pcb_data is None:
        pcb_data = kicad_pcb_bytes(board, routes)
    if pro_data is None:
        pro_data = project_kicad_pro_bytes(board, routes)
    r5 = float(board["hard_rules"]["R5"]["min_clearance_mm"])
    per = _per_class_params(board, ctx)
    if per is not None:
        per_classes = per["classes"]
        empty_classes = [
            {"name": e["name"], "v5_clearance_mm": e["v5_clearance_mm"],
             "v5_width_mm": float(ctx["net_classes"][e["name"]]["width_mm"]),
             "status": e["status"]}
            for e in per["empty_classes"]]
    else:
        # A1：缺类板最小形（Default 单类）——原 R5 入侧车；两件本体不变。
        nc = _net_class_params(board, ctx["entries"])
        default_members = sorted(ctx["net_num"])
        widths = _class_net_widths(board, ctx["entries"], ctx["net_parts"],
                                   ctx["part_by_id"], default_members)
        per_classes = [{
            "name": PRO_DEFAULT_CLASS,
            "v5_clearance": r5,
            "kicad_clearance": nc["clearance"],
            "track_width": nc["track_width"],
            "widths": widths,
            "members": default_members,
        }]
        empty_classes = []
    classes = {c["name"]: c for c in per_classes}
    pairs = []
    names = [c["name"] for c in per_classes]
    for i in range(len(names)):
        for j in range(i, len(names)):
            cx, cy = classes[names[i]], classes[names[j]]
            t_pair = max(cx["v5_clearance"], cy["v5_clearance"])
            c_pair = max(cx["kicad_clearance"], cy["kicad_clearance"])
            residual = max(t_pair - (wa + wb) / 2.0 - c_pair
                           for wa in cx["widths"] for wb in cy["widths"])
            pairs.append({
                "classes": [names[i], names[j]],
                "v5_required_mm": t_pair,
                "kicad_clearance_mm": c_pair,
                "residual_window_mm": round(max(0.0, residual), 10),
                "eliminated": residual <= MASK_ELIM_EPS,
            })
    doc = {
        "rule": "netclass-mask-v1",
        "schema_version": MASK_SCHEMA_VERSION,
        "generated_by": GENERATOR,
        "generator_version": VERSION,
        "board_id": board.get("board_id"),
        "board_sha256": ctx["board_sha256"],
        "pcb_sha256": hashlib.sha256(pcb_data).hexdigest(),
        "pro_sha256": hashlib.sha256(pro_data).hexdigest(),
        "semantics": (
            "v5 R5=中心线间距（网对 max(class_a,class_b)）；KiCad 净类=边到边"
            "（跨类=max 两类 clearance）。kicad_clearance=max(0,t_cls−w_max_cls)"
            "逐类换算。residual_window_mm>0 的类对=v5 违例而 kicad-cli 不报的"
            "掩蔽窗口宽度上界（对类内实际宽度组合取最大）；eliminated=窗口消除。"
            "v5.drc 仍是间距判定唯一内源权威，本表为口径换算信息损失的逐项披露。"
            "schema_version=2（A1 值权威面）：v5_clearance_mm/v5_width_mm=源声明"
            "类原值（Default v5_width_mm=null=not_available，源 Default 线宽不"
            "入板模型）；本件经 board_sha256（导出 PCB host 行原模型 hash）与"
            " pcb_sha256/pro_sha256（实际导出件内容摘要）三重绑定，adapter 核验"
            "全对上后以 v5_* 值为读回值权威（成员仍取 .kicad_pro/"
            "netclass_assignments；空声明只恢复空成员，不发明成员）。"),
        "classes": {c["name"]: {
            "v5_clearance_mm": c["v5_clearance"],
            "v5_width_mm": (None if c["name"] == PRO_DEFAULT_CLASS
                            else float(ctx["net_classes"][c["name"]]["width_mm"])),
            "kicad_clearance_mm": c["kicad_clearance"],
            "track_width_mm": c["track_width"],
            "width_min_mm": min(c["widths"]),
            "width_max_mm": max(c["widths"]),
            "members": c["members"],
        } for c in per_classes},
        "empty_net_classes": empty_classes,
        "pairs": pairs,
    }
    return (json.dumps(doc, ensure_ascii=False, sort_keys=True, indent=1)
            + "\n").encode("utf-8")


def project_kicad_pro_bytes(board, routes):
    """纯函数形态：导出件配套 .kicad_pro bytes（净类口径透传）。

    只写推导键（Default 净类 clearance/track_width +
    board.design_settings.rules.min_track_width），其余键由 kicad-cli 按
    KiCad 内建缺省补全（实测与无项目文件时各违例类型计数一致）。同输入双跑
    字节相等（sort_keys + 固定缩进 + repr 浮点）；board/routes 只读；合同
    违约（含 R5 缺失/非正）抛 ExportError。

    V5-R7 W-2：board.net_classes 非空 ⇒ per-class 写出（Default + 逐类
    classes + netclass_assignments 列表形（KiCad 8.99 meta v4 语料口径））；
    逐类 clearance=max(0, t_cls−w_max_cls)。缺类板 ⇒ 旧单类 doc 逐字节不变。"""
    ctx = _validate(board, routes)
    per = _per_class_params(board, ctx)
    if per is None:
        nc = _net_class_params(board, ctx["entries"])
        doc = {
            "board": {
                "design_settings": {
                    "rules": {
                        "min_track_width": nc["track_width"],
                    },
                },
            },
            "net_settings": {
                "classes": [
                    {
                        "clearance": nc["clearance"],
                        "name": "Default",
                        "track_width": nc["track_width"],
                    },
                ],
                "meta": {"version": PRO_NET_SETTINGS_META_VERSION},
                "net_colors": None,
                "netclass_assignments": None,
                "netclass_patterns": [],
            },
        }
        return (json.dumps(doc, ensure_ascii=False, sort_keys=True, indent=1)
                + "\n").encode("utf-8")
    track_widths = [c["track_width"] for c in per["classes"]]
    doc = {
        "board": {
            "design_settings": {
                "rules": {
                    "min_track_width": min(track_widths),
                },
            },
        },
        "net_settings": {
            "classes": [
                {
                    "clearance": c["kicad_clearance"],
                    "name": c["name"],
                    "track_width": c["track_width"],
                }
                for c in per["classes"]
            ],
            "meta": {"version": PRO_NET_SETTINGS_META_VERSION},
            "net_colors": None,
            "netclass_assignments": per["assignments"],
            "netclass_patterns": [],
        },
    }
    return (json.dumps(doc, ensure_ascii=False, sort_keys=True, indent=1)
            + "\n").encode("utf-8")


def _quote(text):
    """字符串 → 带引号 s-expression token（转义与 adapter._unescape 互逆）。"""
    out = ['"']
    for ch in text:
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def _fmt(v):
    """数值 → 确定性 token（repr 逐位往返：float(token) == float(v)）。"""
    return repr(float(v))


def align_endpoint_into_pad(pt, center, shape, size):
    """逃逸桩端点扎铜几何（P5⑥ D6-2 唯一实现；纯函数、确定性）。

    ``pt`` 已在焊盘物理铜内（circle：到心距 ≤ r；rect：|dx| ≤ w/2 且
    |dy| ≤ h/2，含边界）→ 原坐标返回（现网数据端点=焊盘心，导出零扰动）；
    在铜外 → 沿「pt → 焊盘心」方向移到铜边界交点与焊盘心的**中点**（s =
    s_max/2，s_max 为 pt→心线段与铜边界交点的参数），严格落入铜区，返回新
    ``[x, y]``。浮点全程 IEEE 确定性，同输入逐位同输出。
    """
    px, py = float(pt[0]), float(pt[1])
    cx, cy = float(center[0]), float(center[1])
    dx, dy = px - cx, py - cy
    if shape == "circle":
        r = float(size[0]) / 2.0
        if dx * dx + dy * dy <= r * r:
            return [px, py]
        s_max = r / math.sqrt(dx * dx + dy * dy)
    else:
        hw, hh = float(size[0]) / 2.0, float(size[1]) / 2.0
        if abs(dx) <= hw and abs(dy) <= hh:
            return [px, py]
        steps = []
        if dx:
            steps.append(hw / abs(dx))
        if dy:
            steps.append(hh / abs(dy))
        s_max = min(steps)
    s = s_max / 2.0
    return [cx + s * dx, cy + s * dy]


def partition_pads(partition, first_signal_layer, copper_layer_ids):
    """分区端点焊盘归一（升级件① D1 唯一归一口；导出画法与世界模型共用）。

    pad_terminals 逐项转录（shape circle|rect、size、layers）；分区无
    pad_terminals → 隐式 anchor（rect ANCHOR_PAD_SIZE_MM²、端点 0/1 各一、
    层=首个可用信号层——「分区端点=该网终端」的层不可知抽象，与 v5.route_check
    场景侧同源常数）。返回新列表 [{endpoint, shape, size[w,h], pad_layers[...],
    through_hole}]，每项新 dict（调用方可改）。

    **layers 语义（P5⑥ D6-1 起，"all" 兜底废除）**：``"all"`` = adapter 对源板
    ``*.Cu`` 落键的通孔层跨标记 → ``through_hole=True``、``pad_layers`` 展开=
    ``copper_layer_ids`` 全域；显式层 id 列表 = SMD 焊盘声明铜层（单层，
    正/背面由声明层定）→ 逐项转录。其余形态（非 "all" 字符串、空表、未知
    层 id、非列表）fail-closed 抛错，**无任何 "all" 兜底/静默回退**。

    ``copper_layer_ids`` = "all" 展开域兼列表合法性域，由调用方按世界观传入：
    导出侧传 stackup 全部铜层 id（真实通孔层跨）；route_check 世界模型传信号
    层 id（焊盘铜只入可布线层，⑥内世界模型行为零改写——本件纯导出侧）。

    语义校验 fail-closed（schema 只能表达形状不能表达耦合）：size 维数
    =1(circle)/2(rect) 且逐项为正。
    """
    geo = partition.get("geometry") if isinstance(partition, dict) else None
    items = geo.get("pad_terminals") if isinstance(geo, dict) else None
    if items is None:
        return [
            {"endpoint": 0, "shape": "rect",
             "size": [ANCHOR_PAD_SIZE_MM, ANCHOR_PAD_SIZE_MM],
             "pad_layers": [first_signal_layer], "through_hole": False},
            {"endpoint": 1, "shape": "rect",
             "size": [ANCHOR_PAD_SIZE_MM, ANCHOR_PAD_SIZE_MM],
             "pad_layers": [first_signal_layer], "through_hole": False},
        ]
    out = []
    for i, item in enumerate(items):
        path = "pad_terminals[%d]" % i
        if not isinstance(item, dict):
            _fail(path, "须为 dict，实得 %s" % type(item).__name__)
        shape = item.get("shape")
        size = item.get("size_mm")
        if shape not in ("circle", "rect"):
            _fail(path + ".shape", "须为 circle|rect，实得 %r" % (shape,))
        if not isinstance(size, list) or not size:
            _fail(path + ".size_mm", "须为正数数组，实得 %r" % (size,))
        want = 1 if shape == "circle" else 2
        if len(size) != want:
            _fail(path + ".size_mm", "%s 形状须 %d 个尺寸值，实得 %d 个"
                  % (shape, want, len(size)))
        vals = []
        for k, v in enumerate(size):
            if not _is_num(v) or float(v) <= 0.0:
                _fail("%s.size_mm[%d]" % (path, k), "须为正的有限数值，实得 %r" % (v,))
            vals.append(float(v))
        dims = [vals[0], vals[0]] if shape == "circle" else [vals[0], vals[1]]
        # P5⑥ D6-1：layers 转录——"all"=通孔层跨标记（展开=调用方铜层域），
        # 显式列表=SMD 声明铜层；其余 fail-closed，无兜底。
        layers = item.get("layers")
        if layers == "all":
            through_hole = True
            pad_layers = list(copper_layer_ids)
            if not pad_layers:
                _fail(path + ".layers", "叠层无铜层，\"all\" 无从展开")
        elif isinstance(layers, list) and layers and \
                all(isinstance(x, str) and x in copper_layer_ids for x in layers):
            through_hole = False
            pad_layers = list(layers)
        else:
            _fail(path + ".layers",
                  "须为 \"all\"（通孔层跨标记）或铜层 id 列表（板铜层=%s），"
                  "实得 %r" % (copper_layer_ids, layers))
        # V5-R1：endpoint=pad 质心在 endpoints 中的索引（多点网 ≥2；
        # 2 端网=0|1 旧域子集。上限=原始 endpoints 项数——兼容 adapter 去重
        # 索引域（≤去重数-1≤原数-1）与既有 fixtures 的端点 0/1 语义（重合
        # 端点退化板两项分指 0/1，tests/fixtures_v2 先例）。
        ep = item.get("endpoint")
        n_ep = len(geo.get("endpoints") or []) or 2
        if (not isinstance(ep, int) or isinstance(ep, bool)
                or not 0 <= ep < n_ep):
            _fail(path + ".endpoint", "须为 0..%d 整数（endpoints 去重点数），"
                  "实得 %r" % (n_ep - 1, ep))
        out.append({"endpoint": ep, "shape": shape, "size": dims,
                    "pad_layers": pad_layers, "through_hole": through_hole})
    return out


def kicad_pcb_bytes(board, routes):
    """纯函数形态：v5.board.v1 板 + v5.routes.v1 路由 → .kicad_pcb bytes。

    同输入双跑字节相等（无时间戳/随机）；board 只读；合同违约抛
    ExportError（ValueError 子类，信息带键路径）。
    """
    ctx = _validate(board, routes)
    entries = ctx["entries"]
    stackup = ctx["stackup"]

    lines = []
    host = ("generator=%s generator_version=%s board_id=%s board_sha256=%s"
            % (GENERATOR, VERSION, board["board_id"], ctx["board_sha256"]))
    lines.append("(kicad_pcb (version %s) (host %s %s)"
                 % (KICAD_VERSION_TOKEN, GENERATOR, _quote(host)))
    lines.append("  (general (thickness %s))" % _fmt(BOARD_THICKNESS_MM))

    # ---- 叠层：铜层偶数编号 + Edge.Cuts（adapter 只要求层名唯一、号唯一）
    nums = []
    layer_toks = []
    for i, layer in enumerate(stackup):
        num = 2 * i
        nums.append(num)
        layer_toks.append("(%d %s %s)" % (num, _quote(layer["id"]), layer["kind"]))
    edge_num = (EDGE_CUTS_NUM if EDGE_CUTS_NUM not in nums
                else 2 * len(stackup) + EDGE_CUTS_NUM)
    layer_toks.append("(%d %s user)" % (edge_num, _quote(EDGE_CUTS_LAYER)))
    lines.append("  (layers %s)" % " ".join(layer_toks))

    # ---- 网络表：numbered 模式，网号 = board.nets 顺序 1..N
    lines.append('  (net 0 "")')
    for nid, num in ctx["net_num"].items():
        lines.append("  (net %d %s)" % (num, _quote(nid)))

    # ---- 焊盘铜（升级件① D1/D5 + ⑥ D6-1）：分区带 pad_terminals → 按真实
    # 焊盘铜画（shape/size/layers 逐项转录；**⑥起 "all" 不再展开为全部信号层
    # 按 smd 画**："all"=adapter 的 *.Cu 通孔层跨标记 → (pad 1 thru_hole …
    # (drill D) (layers "*.Cu"))，KiCad 通孔规范形、真实通孔层跨，D=板
    # via_model 孔径（孔几何唯一推导口）；显式层列表=SMD → (pad 1 smd …)
    # 单层，正/背面由声明层定。否则隐式 anchor（rect 1.0×1.0），其层
    # **跟随该网 route entry 层**（端点 a=首 entry 层、端点 b=末 entry 层——
    # 端子抽象随路线走，kicad 侧每段 track 末端必落在本网焊盘铜上=无悬空/
    # 未连；网无 entry（未布通板不出件）回退首个可用信号层）。多网共分区
    # 每网各画一份（抽象板合同形状；真实板分区每网一个，不重影）。
    first_signal = None
    for layer in stackup:
        if layer.get("kind") == "signal" and layer.get("available") is True:
            first_signal = layer["id"]
            break
    if first_signal is None:
        _fail("board.stackup", "无可用信号层，焊盘铜无处安放")
    # D6-1：导出侧 "all" 展开域=stackup 全部铜层（signal+plane）=真实通孔层跨；
    # route_check 世界模型仍传信号层域（世界模型⑥内零改写，纯导出侧）。
    copper_ids = [layer["id"] for layer in stackup]
    vm = via_model_params(board)
    thru_drill = vm["drill"]
    # ---- 0.7.0 OPT-11 D-B：板固孔位置索引（精确浮点键——adapter 端
    #      holes[].pos_mm 与分区端点同源同算（footprint (at) + R(θ)·pad (at)），
    #      逐位相等；同位多孔按源序消费，确定性）。TH 焊盘孔径取原值；无网
    #      NPTH 机械孔落件；无网 plated TH 不落件（契约披露见模块 docstring）。
    hole_entries = ctx["holes"] or []
    hole_index = {}
    for _hi, _h in enumerate(hole_entries):
        hole_index.setdefault(_h["pos"], []).append(_hi)
    hole_consumed = set()

    def _take_hole(x, y):
        for _hi in hole_index.get((float(x), float(y)), ()):
            if _hi not in hole_consumed:
                hole_consumed.add(_hi)
                return hole_entries[_hi]
        return None

    def _hole_drill_tok(hole, pad_w=None, pad_h=None):
        """板固孔 → (drill …) token。oval 原值转录；方向约定（0.7.0 OPT-11）：
        board.v1 不携带钻孔/pad 旋转角（adapter holes[].size_mm 为 pad 局部原值、
        pad_terminals.size_mm 为旋转后轴对齐外接盒），oval 孔长轴对齐 pad 外接盒
        长轴——对常规同轴槽孔 annular 逐轴等值（bbox 旋转互换 ⇒ 钻轴随换），
        消除方向未知模型下的 annular 假报；机械孔（无 pad 面）长轴对齐 X。"""
        if hole["shape"] == "oval":
            long_d, short_d = max(hole["size"]), min(hole["size"])
            if pad_w is None or pad_w >= pad_h:
                return " (drill oval %s %s)" % (_fmt(long_d), _fmt(short_d))
            return " (drill oval %s %s)" % (_fmt(short_d), _fmt(long_d))
        return " (drill %s)" % _fmt(hole["drill"])

    net_end_layers = {}
    for r in entries:
        ends = net_end_layers.setdefault(r["net_id"], {})
        pts = r.get("polyline") or []
        if len(pts) >= 2:
            ends.setdefault("head", (pts[0], r["layer"]))   # 首 entry 头
            ends["tail"] = (pts[-1], r["layer"])            # 末 entry 尾

    def _pt_eq(a, b):
        return abs(float(a[0]) - float(b[0])) <= 1e-9 and \
            abs(float(a[1]) - float(b[1])) <= 1e-9

    # D6-2 端点扎铜参照：(net_id, partition_id) → 该网该分区的有效焊盘铜
    # （隐式 anchor 覆盖后口径），[center/shape/size/layers]。
    net_pad_coppers = {}
    for net in board["nets"]:
        nid = net["net_id"]
        num = ctx["net_num"][nid]
        ends = net_end_layers.get(nid) or {}
        for pid in ctx["net_parts"][nid]:
            part = ctx["part_by_id"][pid]
            pads = partition_pads(part, first_signal, copper_ids)
            implicit = (part.get("geometry") or {}).get("pad_terminals") is None
            eps = part["geometry"]["endpoints"]

            def _layer_for(target):
                if "head" in ends and _pt_eq(ends["head"][0], target):
                    return ends["head"][1]
                if "tail" in ends and _pt_eq(ends["tail"][0], target):
                    return ends["tail"][1]
                return first_signal
            # 无库昵称（冒号）：板内嵌封装、无库依赖——kicad-cli lib parity
            # 不再报「当前配置中不包含封装库 'V5'」（docstring 封装库三选一）。
            base = "V5-anchor-%s-" % sanitize_net_id(pid)
            # V5-R1 ED-X（0.5.0）多端点发射：endpoint 域 0..n_ep-1（R1 全端点
            # 入模）。tag 前缀 a/b 保留 2 端旧域逐位不变；endpoint ≥2 前缀
            # e<k>——(前缀, 计数) 二元组保证 module 名确定性唯一。
            if implicit and len(eps) > 2:
                # 隐式 anchor 多端点补发（消费侧后处理；partition_pads 本体
                # 零改→route_check 世界模型零穿透）：无 pad_terminals 分区的
                # 端点 2..n-1 各补一枚与端点 0/1 同规格 anchor（层随网路线
                # 端点，兜底首个可用信号层），D6-2 扎铜参照覆盖全端点。
                pads = list(pads) + [
                    {"endpoint": k, "shape": "rect",
                     "size": [ANCHOR_PAD_SIZE_MM, ANCHOR_PAD_SIZE_MM],
                     "pad_layers": [_layer_for(eps[k])],
                     "through_hole": False}
                    for k in range(2, len(eps))]
            per_end = {}
            for item in pads:
                e_idx = item["endpoint"]
                ep = eps[e_idx]
                per_end[e_idx] = per_end.get(e_idx, 0) + 1
                tag = ("a" if e_idx == 0 else "b" if e_idx == 1
                       else "e%d" % e_idx) + \
                    ("" if per_end[e_idx] == 1 else str(per_end[e_idx]))
                if implicit:
                    item = dict(item)
                    item["pad_layers"] = [_layer_for(ep)]
                    item["through_hole"] = False
                net_pad_coppers.setdefault((nid, pid), []).append(
                    {"center": (float(ep[0]), float(ep[1])),
                     "shape": item["shape"], "size": item["size"],
                     "layers": item["pad_layers"]})
                if item["through_hole"]:
                    # 0.7.0 OPT-11 D-B：孔径优先=board.holes 位置匹配原值（oval
                    # 原形转录）；孔型随 plated（有网 NPTH 罕见形落 np_thru_hole，
                    # 修正 0.6.0 一律 thru_hole 的镀覆语义）；无匹配回退
                    # via_model 孔径（合成板/手搓板路径，0.6.0 行为不变）。
                    hole = _take_hole(ep[0], ep[1])
                    if hole is None:
                        pad_type = "thru_hole"
                        drill_tok = " (drill %s)" % _fmt(thru_drill)
                        layers_tok = _quote("*.Cu")
                    elif hole["plated"]:
                        pad_type = "thru_hole"
                        drill_tok = _hole_drill_tok(hole, item["size"][0],
                                                    item["size"][1])
                        layers_tok = _quote("*.Cu")
                    else:
                        pad_type = "np_thru_hole"
                        drill_tok = _hole_drill_tok(hole, item["size"][0],
                                                    item["size"][1])
                        layers_tok = "%s %s" % (_quote("*.Cu"), _quote("*.Mask"))
                else:
                    pad_type = "smd"
                    drill_tok = ""
                    layers_tok = " ".join(_quote(l)
                                          for l in item["pad_layers"])
                lines.append("  (module %s (layer %s) (at %s %s)"
                             % (_quote(base + tag),
                                _quote(item["pad_layers"][0]),
                                _fmt(ep[0]), _fmt(ep[1])))
                lines.append(
                    "    (pad 1 %s %s (at 0 0) (size %s %s)%s (layers %s)"
                    " (net %d %s)))"
                    % (pad_type, item["shape"], _fmt(item["size"][0]),
                       _fmt(item["size"][1]), drill_tok, layers_tok,
                       num, _quote(nid)))

    # ---- 无网 NPTH 机械孔落件（0.7.0 OPT-11 D-B ③）：board.holes 未被上节
    #      TH 焊盘消费的 unplated 孔逐孔落 ``V5-npth-N`` module（np_thru_hole、
    #      size=钻径、无 net、无发明铜——纯机械孔开口；oval 原形转录）。无网
    #      plated TH 不落件（④：真实环铜不入模，落件必发明几何；丢弃面=
    #      board.holes 全量清单 × 导出件 pad 位置对账，契约披露于模块
    #      docstring「板固孔四类分开口径」节）。孔序=board.holes 源序（确定性）。
    npth_seq = 0
    for _hi, _h in enumerate(hole_entries):
        if _hi in hole_consumed or _h["plated"]:
            continue
        npth_seq += 1
        if _h["shape"] == "oval":
            np_shape = "oval"
            np_lo, np_sh = max(_h["size"]), min(_h["size"])
            np_size = "(size %s %s)" % (_fmt(np_lo), _fmt(np_sh))
        else:
            np_shape = "circle"
            np_size = "(size %s %s)" % (_fmt(_h["drill"]), _fmt(_h["drill"]))
        lines.append("  (module %s (layer %s) (at %s %s)"
                     % (_quote("V5-npth-%d" % npth_seq), _quote(copper_ids[0]),
                        _fmt(_h["pos"][0]), _fmt(_h["pos"][1])))
        lines.append("    (pad 1 np_thru_hole %s (at 0 0) %s%s (layers %s %s)))"
                     % (np_shape, np_size, _hole_drill_tok(_h),
                        _quote("*.Cu"), _quote("*.Mask")))

    # ---- 走线段：polyline 逐段 → (segment)，输入序即输出序；网级真端点
    # 扎铜对齐（P5⑥ D6-2，见 _aligned：近端指派+ANCHOR 邻域内扎入，链合同
    # 数据零扰动）；ribbon 带（copper_band）分区跳过（其 entry=组首网的带
    # 声明，由下方 ribbon 组网逐网落段——带抽象下组内各网共享同一物理带，
    # 逐网各画一份全带中心线段使各网锚点焊盘皆有本网铜可连；重合铜=带抽象
    # 固有影子，C=0 板形 kicad 静默；真实板无 ribbon（adapter 不产
    # copper_band），披露）

    def _aligned(nid, pid, pts, layer, is_first, is_last):
        """P5⑥ D6-2 端点扎铜（只作用于网的真端点：首 entry 首/末 entry 末；
        换层衔接点与中间点绝不吸附）。几何：
        ①真端点按分区端点**近端指派**（V5-R1 0.5.0 起 argmin 全端点、平手取
        索引最小——2 端域=旧「平手取 endpoint 0」语义，确定性）；
        ②被指派端点的同位焊盘中，到达层匹配者优先、其余取首项（确定性）；
        ③端点已在焊盘铜内 → 原样（链合同数据端点=焊盘心，现网零扰动）；
        ④在铜外但处于端点邻域 ``ANCHOR_PAD_SIZE_MM``（1.0mm，隐式 anchor 铜
        尺度；逃逸阶梯最大位移 0.75mm 与之同量级）内 → 沿指向焊盘心方向
        扎入铜区（:func:`align_endpoint_into_pad`，铜边界与心中点）；
        ⑤邻域外 → 原样（首末点=分区端点的链合同由 route_check 审计，导出
        不掩盖合同违例、不发明长段几何）。"""
        if not (is_first or is_last):
            return pts
        pads = net_pad_coppers.get((nid, pid))
        if not pads:
            return pts
        eps = ctx["part_by_id"][pid]["geometry"]["endpoints"]
        new_pts = list(pts)
        for is_term, idx in ((is_first, 0), (is_last, len(pts) - 1)):
            if not is_term:
                continue
            pt = pts[idx]
            # V5-R1 ED-X（0.5.0）：近端指派 argmin 全端点（平手取索引最小=
            # 2 端旧域 d0<=d1 取 0 语义的推广，逐位兼容）。
            target = 0
            best = None
            for k, ep in enumerate(eps):
                d = math.hypot(float(pt[0]) - float(ep[0]),
                               float(pt[1]) - float(ep[1]))
                if best is None or d < best:
                    best = d
                    target = k
            chosen = None
            for pd in pads:
                if _pt_eq(pd["center"], eps[target]):
                    if chosen is None or (layer in pd["layers"]
                                          and layer not in chosen["layers"]):
                        chosen = pd
            if chosen is None:
                continue
            center = chosen["center"]
            if math.hypot(float(pt[0]) - center[0],
                          float(pt[1]) - center[1]) > ANCHOR_PAD_SIZE_MM:
                continue                                    # 邻域外不动（⑤）
            new_pts[idx] = align_endpoint_into_pad(pt, center,
                                                   chosen["shape"],
                                                   chosen["size"])
        return new_pts

    net_first_last = {}
    for i, r in enumerate(entries):
        fl = net_first_last.setdefault(r["net_id"], [i, i])
        fl[1] = i
    ribbon_pids = set()
    for pid, part in ctx["part_by_id"].items():
        if (part.get("geometry") or {}).get("copper_band") is not None:
            ribbon_pids.add(pid)
    for i, r in enumerate(entries):
        if r["partition_id"] in ribbon_pids:
            continue
        fl = net_first_last[r["net_id"]]
        pts = _aligned(r["net_id"], r["partition_id"], r["polyline"],
                       r["layer"], i == fl[0], i == fl[1])
        num = ctx["net_num"][r["net_id"]]
        for a, b in zip(pts[:-1], pts[1:]):
            lines.append(
                "  (segment (start %s %s) (end %s %s) (width %s) (layer %s) (net %d))"
                % (_fmt(a[0]), _fmt(a[1]), _fmt(b[0]), _fmt(b[1]),
                   _fmt(r["width"]), _quote(r["layer"]), num))
    for pid in [p["partition_id"] for p in board.get("partitions", [])]:
        if pid not in ribbon_pids:
            continue
        part = ctx["part_by_id"][pid]
        entry = next((r for r in entries if r["partition_id"] == pid), None)
        if entry is None:
            continue
        for net in board["nets"]:
            if pid not in net["partitions"]:
                continue
            num = ctx["net_num"][net["net_id"]]
            pts = _aligned(net["net_id"], pid, entry["polyline"],
                           entry["layer"], True, True)
            for a, b in zip(pts[:-1], pts[1:]):
                lines.append(
                    "  (segment (start %s %s) (end %s %s) (width %s) (layer %s)"
                    " (net %d))"
                    % (_fmt(a[0]), _fmt(a[1]), _fmt(b[0]), _fmt(b[1]),
                       _fmt(entry["width"]), _quote(entry["layer"]), num))

    # ---- 过孔（升级件① D2/D5）：transition/return 逐点、全叠层通孔；
    # 同网同坐标去重（多 entry 在衔接点双方披露同一孔——物理一孔，去重后
    # kicad 不再呈现钻孔同位）；size/drill 走板 via_model（缺省文档化常量；
    # 焊盘 thru_hole drill 同源，见焊盘铜节 D6-1）。
    span = (_quote(stackup[0]["id"]), _quote(stackup[-1]["id"]))
    seen_vias = set()
    for r in entries:
        num = ctx["net_num"][r["net_id"]]
        for key in ("transition_vias", "return_vias"):
            for p in r.get(key) or []:
                vkey = (num, _fmt(p[0]), _fmt(p[1]))
                if vkey in seen_vias:
                    continue
                seen_vias.add(vkey)
                lines.append(
                    "  (via (at %s %s) (size %s) (drill %s) (layers %s %s) (net %d))"
                    % (_fmt(p[0]), _fmt(p[1]), _fmt(vm["size"]), _fmt(vm["drill"]),
                       span[0], span[1], num))

    # ---- 板框：workspace → gr_rect@Edge.Cuts
    ws = ctx["workspace"]
    lines.append("  (gr_rect (start %s %s) (end %s %s) (layer %s) (width %s))"
                 % (_fmt(ws["x_min"]), _fmt(ws["y_min"]),
                    _fmt(ws["x_max"]), _fmt(ws["y_max"]),
                    _quote(EDGE_CUTS_LAYER), _fmt(EDGE_LINE_WIDTH_MM)))
    lines.append(")")
    return ("\n".join(lines) + "\n").encode("utf-8")


def write_kicad_pcb(board, routes, path):
    """导出 .kicad_pcb + 配套 .kicad_pro 双件落盘（sidecar 卫生：只准 out/ 之
    下）。

    路径越界抛 SidecarViolation（先于任何写盘/建目录，两件路径分别核验）；
    routes/板合同违约（含 R5 缺失/非正）抛 ExportError（不落半成品：.kicad_pro
    bytes 先行推导成功后才动盘）。返回 .kicad_pcb 写入路径；.kicad_pro 落在
    同 stem 的 ``<stem>.kicad_pro``（KiCad 项目文件同名约定，kicad-cli 对同
    目录同名项目文件自动加载）。返回值向后兼容（仅 .kicad_pcb 路径）。

    V5-R7 W-2：类板（board.net_classes 非空）另落第三件
    ``<stem>.netclass-mask.json``（掩蔽窗口逐项消除表，netclass_mask_table
    纯函数产物）。A1（EXEC-R3 R3-2，schema_version=2）起**缺类板也落第三件**
    （Default 单类最小形——原 R5 可信回程载体；旧「缺类板不落件」口径废除，
    .pcb/.pro 两件本体 bytes 不变）；mask 经 pcb_data/pro_data 预推导 bytes
    绑定实际导出件内容。"""
    path = os.fspath(path)
    sidecar.assert_allowed(path)
    data = kicad_pcb_bytes(board, routes)
    pro_data = project_kicad_pro_bytes(board, routes)
    mask_data = netclass_mask_table(board, routes, pcb_data=data, pro_data=pro_data)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    pro_path = os.path.splitext(path)[0] + ".kicad_pro"
    sidecar.assert_allowed(pro_path)
    with open(path, "wb") as f:
        f.write(data)
    with open(pro_path, "wb") as f:
        f.write(pro_data)
    if mask_data is not None:   # A1 起恒 bytes（缺类板最小形）；卫语留纯函数形态
        mask_path = os.path.splitext(path)[0] + ".netclass-mask.json"
        sidecar.assert_allowed(mask_path)
        with open(mask_path, "wb") as f:
            f.write(mask_data)
    return path
