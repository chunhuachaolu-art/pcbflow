# -*- coding: utf-8 -*-
"""KiCad .kicad_pcb → v5.board.v1 适配器（L0，P1；任务书 §3.1 provenance 落链）。

adapter 标识 = "kicad-adapter v0.1.0"（写入 provenance.adapter）。下列**局限与策略**
是 v0.1.0 契约的一部分，全部在此披露：

- s-expression 解析：手写 tokenizer（括号 / 带引号字符串含 ``\"`` ``\\`` ``\n``
  ``\t`` ``\r`` 转义与引号内括号 / 裸原子），**禁 eval**；任何解析失败（非法字符、
  未闭合引号、括号不配对、顶层不是唯一 ``(kicad_pcb ...)`` 表）抛 AdapterError。
  version token 各板不同（20171114/20171130/20211014/20241229/20260206…）只作记录，
  不做任何版本分支。
- stackup：按 ``(layers)`` 块启用的铜层（名字以 ``.Cu`` 结尾）生成，顺序
  F.Cu → In<N>.Cu（按 N 升序）→ B.Cu；kind 全 ``"signal"``、preferred_direction 全
  ``"any"``（v0.1.0 局限：不读文件布线偏好）、available=True。
- zones=[]（v0.1.0 局限：真实板不声明 V5 禁布/敏感/走廊区）；铜铺区 ``(zone ...)``
  不解析为几何，仅计入 report["ignored_zones"]。装饰性对象（gr_*、fp_*、text、
  text_box、dimension、group）跳过并计入 report["ignored_drawings"]。
- workspace：全部 pad/track(segment+arc)/via 铜几何的包围盒外扩固定余量
  **WORKSPACE_MARGIN_MM = 1.0 mm**（常数披露于此）。线段按两端点 ±半宽、pad 按
  中心 ±半尺寸、via 按中心 ±半径、弧按 start/mid/end 控制点与真实圆弧扫掠范围
  （含轴向极值）计入。workspace 必含全部铜几何。
- pad 绝对坐标 = footprint (module/footprint) 位置 + 按 footprint 角度旋转 pad 局部
  坐标（KiCad 口径 abs = fp + R(θ)·local）。角度 0/90/180/270°（含 -90 等价角）用
  精确三角值；其余角度走 math 三角函数——弧段包围盒与任意角旋转跨 libc 平台可能有
  末位浮点差，同机双跑严格一致（P1 门只测同机双跑同 hash）。
- 分区 = **每网一个**（board.v1 nets[].partitions minItems=1 且须指向已存在分区）：
  - partition_id = "PT-" + 净化网名（非 [A-Za-z0-9_.-] 字符替换为 "_"，空名 → "_"；
    冲突按确定网序（numbered=网号升序 / names=名字典序）追加 "_2"、"_3"… 保证唯一）。
  - geometry.endpoints（**V5-R1 W-2 2026-09-25 翻转**）：该网全部 pad 质心
    （= pad 中心绝对坐标）按**源文件出现序去重**落键（同坐标 pad 折叠为单端
    点，多 pad 共享索引）；**多 pad 网不再折叠 2 端点**。旧口径（v≤0.3.0：
    欧氏距离最远两 pad、平手取坐标字典序最小一对）由本件翻转，旧口径入
    R1-REPORT ERRATUM。单 pad 网 = 两端重合的退化终点（升级件④合同沿用）；
    0 pad 网 fail-closed 抛 AdapterError（策略披露于此）。
  - **geometry.pad_terminals（升级件① D1 → V5-R1 逐 pad 化）**：每 pad 一项
    落键，``endpoint`` =该 pad 质心在 endpoints 中的索引（整数 ≥0；同质心
    多 pad=多项共享索引=物理铜并集语义；单 pad 退化网 endpoint=0）；
    shape：KiCad pad shape token circle→"circle"（size [w]，圆 pad w==h），
    其余（rect/roundrect/oval/custom…）→"rect"（size [w,h]；footprint 旋转角下
    取**轴对齐外接盒**尺寸——保守包络，披露）；layers：token 含 ``*.Cu`` →
    "all"，否则取 (layers) 中在启用铜层内的 token 列表（无铜层 token 的
    焊盘不落项、计入 report["pad_terminal_skipped"]——宽容，不 fail-closed）。
    TH pad 的 drill 自 D8 起全量入模（board.holes[]，见下节）；升级件① D1 旧口径
    「TH pad 的 drill 不入模（schema 无孔径键）」已由 V5-D8 决策件翻转，旧口径
    入 D8-REPORT ERRATUM。
  - **board.topology（V5-R1 W-3）**：per-partition 显式 Steiner 拓扑
    （partition_id → {nodes, edges, terminal_count, total_mm, provenance}）。
    nodes 合同=端点（endpoints 出现序）在前+Steiner 分支点（坐标字典序）在
    后；edges=[[u,v]] 规范字典序（u<v）；算法=v5.steiner（FLUTE 查表形态
    自研复现，度数 ≤9 查表精确段+高度数分解；provenance.method 披露逐网
    求解段 pot-table/decomposed/mst-fallback/trivial）。退化网 nodes=[单点]、
    edges=[]。topology 恒落键（全分区必有条目）。
  - ptype 确定性映射表（写死，披露于此）：网名以 "+" 开头；或 upper 后属于
    POWER_EXACT_NAMES={GND,VCC,VDD,VSS,AGND,DGND,GNDA,GNDD,AVDD,AVSS,VDDA,VSSA,
    VBUS,VBAT}；或 upper 后以 "GND" 开头（GND… 前缀族）；或 upper 后含 "PWR" 或
    "POWER" → "PWR"；其余 → "MISC"。
  - width_prior 用 adapter 文档化默认 DEFAULT_WIDTH_PRIOR={"w_min":0.3,"w_max":1.0}；
    current_a=0；speed_class="unknown"；layer_policy="any"。
  - note：多 pad 网 = "adapter: n pads -> m terminal nodes (R1 explicit
    topology)"；单 pad 网 =
    "adapter: 1 pad abstracted to 2 coincident endpoints (degenerate)"。
  - 退化分区处置（升级件④ 2026-09-14 披露）：两端点重合的退化分区（单 pad 网
    或多点重合网）由 executor 按 trivially satisfied 处置（零长 route 条目，
    见 v5/executor 模块 docstring「模式A 退化分区合同」）；report 增计
    degenerate_partitions（板 dict 不变、board_sha256 不变）。
- nets：**两种网表形态都收**（version token 差异的宽容）：numbered（KiCad ≤9，
  顶层 ``(net N "name")`` 表 + 引用 ``(net N)``/``(net N "name")``，网序按网号升序）与
  name-only（KiCad 10+，version 20260206 语风，无顶层 net 表，pad/segment/via 直接
  ``(net "name")``，pad 引用即声明，网序按名字典序；形态与模式不符 → AdapterError）。
  net 0 / 空名（未连接）不产出 net/分区，其上铜只计入 workspace；net_class 省略
  （schema 可选）。numbered 模式下 track/via/pad 引用未声明 net（≠0）→ AdapterError；
  names 模式下 track/via 引用无任何 pad 的网 → AdapterError；0 pad 网 fail-closed
  抛 AdapterError。
- **via_model（升级件① D2）**：真实板 (via) 的 (size)/(drill) 对按出现次数取
  众数（平手取 (drill, size) 字典序最小——确定性；无 drill 的孔形不参选）落
  板级可选键 ``via_model={drill_mm, annular_mm=(size-drill)/2 夹 0}``；无可用
  孔对 → 不落键（消费方缺省 drill 0.3 / annular 0.15 文档化兜底）。
- **板固孔全量入模（V5-D8，2026-09-22）**：全部 ``thru_hole``（PTH）与
  ``np_thru_hole``（NPTH）pad 的钻孔入 board 级 ``holes: []``（**不分网成员
  资格**——kicad hole_to_hole 为纯几何判据；含 NPTH；含 oval）。逐孔
  ``{"pos_mm":[x,y], "drill_mm":n, "plated":bool, "shape":"circle"|"oval",
  "size_mm":[a,b](仅 oval)}``；绝对坐标 = footprint (at) + R(θ)·pad 局部 (at)
  （同 pad_terminals 既有旋转口径，含 footprint 旋转——D7 停线件口径）。oval
  钻孔收录原始 size，**消费侧按保守外接圆（drill_mm=max(a,b) 直径）**（用户
  裁定②）。缺 drill / 非正 drill / drill 带 offset 子表 / 形态非法 →
  AdapterError fail-closed（不入静默缺省）。``holes`` 键**恒落**（真实板转换
  必带，含空数组；合成板 convert_bytes 同样落键）。report 增
  ``holes_pth``/``holes_npth``/``holes_oval`` 三计数。孔顺序=源文件出现序
  （footprint 遍历序 × footprint 内 pad 序，确定性）。
- hard_rules 用引擎缺省不变式地板（与 tests/fixtures_v2.py 转录一致：R1 k_a=0.4/
  floor 0.3；R2 3.0/5.0；R3 unsplittable；R4 true/2.0；R5 0.5；R6 true/true）。
  **V5-R7 W-1 例外**：源带净类声明且含 "Default" 类时，R5.min_clearance_mm =
  Default 类 clearance（缺省类=现标量语义的单源落点，见「net class」节）。
- principle_registry=[]（v0.1.0 不注入理念条目）。
- **net class（V5-R7 W-1，双源口径钉值于开工探针 probe_priority.py P1..P5）**：
  - 双源：板内 legacy ``(net_class "Name" "desc" (clearance C) (trace_width W)
    (add_net "N") ...)``（KiCad ≤5 载体）与同 stem ``.kicad_pro`` 的
    ``net_settings.classes``（KiCad ≥6 载体，kicad-cli 对同目录同名项目文件自动
    加载——kicad_export.py 实测口径同源）。**优先序（P1 钉值）**：.kicad_pro
    net_settings 在场 ⇒ 载体即权威：classes 逐项 fail-closed 校验（缺/非列表/
    项非法 ⇒ AdapterError），板内块整体忽略（report 计
    net_class_board_blocks_ignored；不合并），空类表=零声明缺省路径（source 仍
    披露 kicad_pro）；无项目文件 ⇒ 板内块生效（P2）；两源皆无 ⇒
    无 net_classes 键、R5=引擎缺省 0.5（P3，缺省路径零漂移）。convert_bytes 无
    文件路径 ⇒ 只可达板内源（文档化局限）。
  - ``.kicad_pro`` 侧：``classes[]``（name/clearance/track_width 必填数值 ≥0，
    缺/非法 fail-closed）+ ``netclass_assignments``（{net: "cls"} 或 KiCad 8.99
    meta v4 列表形 {net: ["cls",...]}——多类指派=网有效间距取其类 max）；
    ``netclass_patterns`` 非空 ⇒ AdapterError（正则语义未钉，不静默猜）；
    项目文件存在但不可解析 ⇒ AdapterError。指派引用未知净类 ⇒ AdapterError；
    引用板上不存在的网 ⇒ 忽略并计 net_class_stale_members（指派可能残留他板
    网名，不拒整板）。
  - 落键：``net_classes = {name→{clearance_mm, width_mm, members[]}}``（仅非
    Default 类；members=板上实际存在的网、字典序；"Default" 类=缺省类，其
    clearance → hard_rules.R5.min_clearance_mm（P4），成员不落 net_classes——
    无类网/仅 Default 网即缺省类成员（计 net_class_unassigned_nets 披露，
    **声明缺失≠静默缺省**）。成员类不存在于 classes ⇒ AdapterError。空成员类
    照落键（忠实源声明）。width_mm=track_width 透传（布线宽度选择仍走
    width_prior——per-class 宽度作 routing 先验留改进候选，披露）。
  - report 增计：net_class_source（"none"|"kicad_pcb"|"kicad_pro"）、
    net_class_count（非 Default 类数）、net_class_unassigned_nets、
    net_class_stale_members、net_class_board_blocks_ignored。
- **真实板轮廓（V5-R7 W-3）**：解析 Edge.Cuts 几何 → 板级可选键
  ``outline_mm = {"outer": [元素...], "holes": [[元素...],...]}``（元素
  ``{"type":"segment","start_mm","end_mm"}``；弧加 ``mid_mm``（三点弧，
  start/mid/end 同 track arc R4-W4 弧几何））。口径：
  - 顶层 ``gr_line/gr_rect/gr_arc`` 与 footprint 内 ``fp_line/fp_arc``（局部
    坐标按 footprint (at)+角度旋转到绝对——同 pad 口径）皆收；gr_rect → 4 边
    形顺序段。gr_arc 双形：KiCad ≥6 三点形 (start)(mid)(end)；KiCad ≤5 中心形
    (start=center)(end=起点)(angle=度)——中心形换算 mid/end（r·旋转半角/全角，
    确定三角）。**其余 Edge.Cuts 图元（gr_circle/gr_poly/gr_bbox/fp_circle/
    fp_poly/fp_rect/fp_curve）⇒ AdapterError**（不支持图元 fail-closed，不静默
    丢轮廓）。
  - 链接容差 OUTLINE_CHAIN_TOL_MM=1e-4（KiCad 文件坐标 5~6 位小数舍入实测
    ~2e-6，容差覆盖语料全量；>容差断口=开口轮廓）。全部边须链成闭合环
    （≥3 边）；开口 ⇒ AdapterError（bad outline，与 kicad-cli 同口径）。
  - 环分类：bbox 面积最大者=outer（平手 ⇒ AdapterError 歧义）；其余环为 holes，
    须整体在 outer 内（首顶点射线法+环间零相交保证）；hole 含 hole（嵌套环）
    ⇒ AdapterError（首版不支持，披露）。自交判定：同环非相邻边、跨环边两两
    相交测试（弧按 ARC_TEST_CHORDS=64 弦离散——确定性近似，相邻链边共端点豁免；
    非相邻共点=pinch 亦 fail-closed）。
  - 确定性：环序=外环 + holes（按各环最小源序边升序）；环内元素序=链接序
    （起点=环内最小源序边，方向=链接自然向，被反向链接的边 swap 端点/弧
    start↔end）。报告：outline_edges/outline_arcs/outline_loops/outline_holes。
  - 无任何 Edge.Cuts 图元 ⇒ 不落 outline_mm 键（缺省路径=workspace 矩形，
    既有 17 板语义零漂移）。

- **方言修复（adapter-fix-r1，2026-10-23；四族，全部针对性解析＋明确报错边界）**：
  - **FA-5a legacy 铜层命名**（KiCad ≤4 语风，layers 块无 ``*.Cu`` token，铜层以
    类型 ``signal``/``power``/``mixed`` 标记）：别名映射表 ``Front→F.Cu``、
    ``Back→B.Cu``、``Top→F.Cu``、``Bottom→B.Cu``（语料证据：esp32/bm11/throwing-
    star-pro 等 9 板）＋文档化约定 ``Inner<N>→In<N>.Cu``（N∈1..30，语料无实例、
    按 KiCad ≤4 缺省命名约定收录）。**引用门控**：非 ``*.Cu`` 名的候选铜层**仅当被
    铜几何引用**（segment/arc 的 layer、via 的 layers token、pad 的 layers token）
    才入栈；未被引用的按旧口径忽略（不新增拒收面——kicad-demos multichannel 的
    ``User.1..4 signal`` 自定义名在案，不能 fail-closed，否则破坏存量可转板）。
    自定义 signal 名无映射证据→维持旧口径忽略。层引用经别名翻译到规范名后入
    stackup/pad_terminals。方言板层序=layers 块声明的层号升序（0 F.Cu→…→31 B.Cu，
    KiCad 层号=物理栈位）；纯现代板（全部铜层名以 ``.Cu`` 结尾）保持旧 ``_cu_order``
    排序不变（零漂移）。
  - **FA-5b 自定义 power 铜层挂 track**（证据：kitspace_T32_ref ``(1 GND power)``
    上挂 150 segment）：power 型层名（自定义名如 GND/PWR）**原名保留**入栈（同受
    引用门控约束——kitspace_USBee32-S2 的 power 层仅 zone 使用无 track，维持 2 层
    旧口径不漂移）。
  - **FA-5c drill 单参数 oval**（证据：Theia ``(drill oval 1.1)``、RF_SIGNAL
    ``(drill oval 0.9)``）：``(drill oval D)`` ≡ 两轴同值的退化槽 ≡ 圆孔 D（几何
    恒等，落 circle 形态，**不虚构第二轴**）；report 增计 ``drill_oval_single_param``。
    其余畸形 drill（offset 子表等）维持 fail-closed 拒收。
  - **FA-5d Edge_Cuts 边链开口吸附愈合**（证据：z2amiller_sensorboard 断口实测
    0.068~0.163mm）：``_chain_loops``（容差 0.01mm）失败后，端点按字典序贪心聚类
    （簇径 ≤ ``OUTLINE_HEAL_TOL_MM``=0.2mm；代表点=簇内字典序最小的**实际坐标点**，
    不发明坐标）吸附重链；愈合后仍开口/环边数<3/自交/嵌套校验不过 → 仍 fail-closed
    拒收。report 增计 ``outline_healed_clusters``。容差 0.2mm 覆盖族内实测最大断口
    0.1634mm 且 ≪ 真实设计开口（≥0.1mm 级断口即愈合、更大真实开口仍拒）。**仅链
    失败路径可达**→存量可转板结构零漂移。
  - **provenance.adapter 双版本字符串**（零漂移↔谱系诚实）：未触任何方言路径的板
    落 ``ADAPTER_NAME_V050``（v0.5.0 原串，与修复前逐字节一致）；任一方言路径激活
    （legacy 别名/power 铜层入栈、单参 oval 愈合、轮廓吸附愈合）的板落
    ``ADAPTER_NAME``（v0.6.0）。report 另落 ``adapter_dialect_fixes``（激活族清单，
    仅 report 不入板 dict）。单一全局升版会把 provenance.adapter 入哈希域的全部存量
    板 sha 打花并击穿在盘冻结件链，故不采用。

provenance（§3.1）：source_type="kicad_pcb"；source_uri=绝对路径（convert_file，
正斜杠规范形）或调用方传入（convert_bytes）；source_sha256=源文件原始 bytes 的
sha256；adapter="kicad-adapter v0.2.0"；board_sha256=v5.board.compute_board_sha256
结果。**返回前必须通过 v5.board.load_board 校验**（fail-closed）。

report（不入板 dict，board schema additionalProperties=false）：经
convert_file_with_report / convert_bytes_with_report 获取，键含 kicad_version、
net_count、footprint_count、pad_count、netted_pad_count、segment_count、arc_count、
via_count、ignored_zones、ignored_drawings、degenerate_partitions（升级件④
2026-09-14 增计：两端点重合的分区数）、pad_terminal_count / pad_terminal_skipped
（升级件① 2026-09-14 增计：端点焊盘落键数 / 无铜层 token 跳过数）、
holes_pth / holes_npth / holes_oval（V5-D8 2026-09-22 增计：板固孔 PTH/NPTH/
oval 计数）、topology（V5-R1 2026-09-25 增计：{multi_terminal_nets,
steiner_points, decomposed_nets, mst_fallback_nets}——多端网数/Steiner 分支点
总数/分解段网数/表缺口 MST 兜底网数）、net_class_source / net_class_count /
net_class_unassigned_nets / net_class_stale_members /
net_class_board_blocks_ignored（V5-R7 W-1 2026-10-04 增计）、outline_edges /
outline_arcs / outline_loops / outline_holes（V5-R7 W-3 2026-10-04 增计）、
drill_oval_single_param（adapter-fix-r1 2026-10-23 增计：单参数 oval 按圆孔
收录的计数）、outline_healed_clusters（adapter-fix-r1 增计：FA-5d 吸附愈合合并的
端点簇数，0=未愈合）、adapter_dialect_fixes（adapter-fix-r1 增计：本板激活的
方言修复族清单，如 ["legacy_copper_alias","power_copper_layer",
"drill_oval_single_param","outline_snap_heal"]；空列表=纯旧路径）。
"""
import collections
import json
import math
import os
import re

from .. import canonical
from .. import steiner
from ..board import compute_board_sha256, load_board

ADAPTER_NAME = "kicad-adapter v0.6.0"   # v0.6.0=adapter-fix-r1 方言路径（FA-5a/b/c/d；
                                          # 仅激活方言修复的板落此串）
#: 零漂移路径版本串（未触任何方言路径的板沿用，与 v0.5.0 产物逐字节一致）。
#: 双串机制理由见模块 docstring「方言修复」节——单一全局升版会把 provenance.adapter
#: 入哈希域的全部存量板 sha 打花并击穿在盘冻结件 board_sha256 链。
ADAPTER_NAME_V050 = "kicad-adapter v0.5.0"   # v0.5.0=V5-R7：net class 双源+Edge_Cuts
                                              # 真实板轮廓（v0.4.0=V5-R1 topology）

#: FA-5a legacy 铜层别名映射（KiCad ≤4 语风；语料证据：esp32/bm11/throwing-star-pro
#: 等 9 板 Front/Back、Top/Bottom 两种拼写）。Inner<N>（N∈1..30）按 KiCad ≤4 缺省
#: 命名约定收录（语料无实例，文档化约定）。
LEGACY_COPPER_ALIASES = {
    "Front": "F.Cu", "Back": "B.Cu",
    "Top": "F.Cu", "Bottom": "B.Cu",
}
_LEGACY_INNER_RE = re.compile(r"Inner(?:[1-9]|[12][0-9]|30)\Z")

#: workspace 铜包围盒外扩余量（mm），固定常数（模块 docstring 已披露）。
WORKSPACE_MARGIN_MM = 1.0

#: adapter 文档化宽度先验默认（每分区同值；docstring 已披露）。
DEFAULT_WIDTH_PRIOR = {"w_min": 0.3, "w_max": 1.0}

#: ptype 精确名映射表（配合 "+" 前缀、"GND" 前缀、含 "PWR"/"POWER"；docstring 已披露）。
POWER_EXACT_NAMES = frozenset({
    "GND", "VCC", "VDD", "VSS", "AGND", "DGND",
    "GNDA", "GNDD", "AVDD", "AVSS", "VDDA", "VSSA",
    "VBUS", "VBAT",
})

_TO_POW = {"n": "\n", "r": "\r", "t": "\t"}


class AdapterError(ValueError):
    """KiCad 源不可解析或不可转换（fail-closed，信息带原因/位置）。"""


# ---------------------------------------------------------------- s-expression 解析

#: tokenizer 主正则：带引号字符串（含转义与引号内括号）→ 括号 → 裸原子。
_TOKEN_RE = re.compile(r'"(?:\\.|[^"\\])*"|[()]|[^\s()"]+')


def _unescape(token):
    """带引号 token（含首尾引号）→ 字符串值。转义：\\n \\r \\t \\" \\\\，其余
    反斜杠组合取字面字符（宽容）。"""
    body = token[1:-1]
    if "\\" not in body:
        return body
    out = []
    i = 0
    n = len(body)
    while i < n:
        ch = body[i]
        if ch == "\\" and i + 1 < n:
            nxt = body[i + 1]
            out.append(_TO_POW.get(nxt, nxt))
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def parse_sexpr(text):
    """解析 KiCad s-expression 文本 → 树（list 节点，头为原子字符串；叶为字符串）。

    迭代栈机实现（无递归、无 eval）。词法缺口（不可识别字符，如未闭合引号）、
    多余右括号、EOF 时括号未闭合、顶层不是唯一 ``(kicad_pcb ...)`` 表 → AdapterError。
    """
    root = []
    stack = [root]
    pos = 0
    for m in _TOKEN_RE.finditer(text):
        if m.start() > pos:
            gap = text[pos:m.start()]
            if not gap.isspace():
                raise AdapterError("词法错误：位置 %d 起存在不可识别字符 %r（如未闭合引号）"
                                   % (pos, gap[:12]))
        elif m.start() < pos:
            raise AdapterError("词法错误：位置 %d 词元重叠" % m.start())
        pos = m.end()
        tok = m.group()
        if tok == "(":
            node = []
            stack[-1].append(node)
            stack.append(node)
        elif tok == ")":
            if len(stack) == 1:
                raise AdapterError("括号不配对：位置 %d 出现多余右括号" % m.start())
            stack.pop()
        elif tok[0] == '"':
            stack[-1].append(_unescape(tok))
        else:
            stack[-1].append(tok)
    if pos != len(text) and not text[pos:].isspace():
        raise AdapterError("词法错误：位置 %d 起存在不可识别字符（如未闭合引号截断）" % pos)
    if len(stack) != 1:
        raise AdapterError("括号不配对：EOF 时仍有 %d 层未闭合括号（输入截断）" % (len(stack) - 1))
    if (len(root) != 1 or type(root[0]) is not list or not root[0]
            or type(root[0][0]) is not str or root[0][0] != "kicad_pcb"):
        raise AdapterError("顶层应恰有一个 (kicad_pcb ...) 表（得到 %d 个顶层元素）" % len(root))
    return root[0]


def _sub(node, name):
    """node 的直接子节点中头为 name 的第一个子表；无则 None。"""
    for item in node[1:]:
        if type(item) is list and item and type(item[0]) is str and item[0] == name:
            return item
    return None


def _as_float(tok, where):
    try:
        v = float(tok)
    except (TypeError, ValueError):
        raise AdapterError("%s: 数字字段不可解析 %r" % (where, tok)) from None
    if not math.isfinite(v):
        raise AdapterError("%s: 数字字段非有限值 %r" % (where, tok))
    return v


def _as_int(tok, where):
    try:
        return int(tok)
    except (TypeError, ValueError):
        raise AdapterError("%s: 整数字段不可解析 %r" % (where, tok)) from None


def _floats(node, min_count, where):
    """子表 node[1:] 全部转 float（至少 min_count 个）。任何非数值 → AdapterError。"""
    vals = []
    for tok in node[1:]:
        if type(tok) is not str:
            raise AdapterError("%s: 意外的子表嵌套" % where)
        vals.append(_as_float(tok, where))
    if len(vals) < min_count:
        raise AdapterError("%s: 需要 %d 个数值，实际 %d 个" % (where, min_count, len(vals)))
    return vals


# ---------------------------------------------------------------- 几何辅助

#: 0/90/180/270° 的精确 (cos, sin)，保证常见 footprint 角度的跨平台一致旋转。
_EXACT_COS_SIN = ((0.0, 1.0, 0.0), (90.0, 0.0, 1.0), (180.0, -1.0, 0.0), (270.0, 0.0, -1.0))
_TAU = 2.0 * math.pi


def _rotate(x, y, angle_deg):
    """KiCad 口径旋转：rel = (x·cosθ + y·sinθ, −x·sinθ + y·cosθ)。θ 按 360° 归一，
    0/90/180/270° 用精确值。"""
    a = angle_deg % 360.0
    for base, cs, sn in _EXACT_COS_SIN:
        if abs(a - base) < 1e-9:
            return (x * cs + y * sn, -x * sn + y * cs)
    rad = math.radians(a)
    cs = math.cos(rad)
    sn = math.sin(rad)
    return (x * cs + y * sn, -x * sn + y * cs)


class _BBox(object):
    __slots__ = ("x0", "y0", "x1", "y1")

    def __init__(self):
        self.x0 = math.inf
        self.y0 = math.inf
        self.x1 = -math.inf
        self.y1 = -math.inf

    def add(self, x0, y0, x1, y1):
        if x0 < self.x0:
            self.x0 = x0
        if y0 < self.y0:
            self.y0 = y0
        if x1 > self.x1:
            self.x1 = x1
        if y1 > self.y1:
            self.y1 = y1

    @property
    def empty(self):
        return self.x0 > self.x1


def farthest_endpoints(points):
    """端点极值选择策略（docstring 已披露）：欧氏距离（平方比较）最大的两点。

    平手取坐标字典序最小的一对（先对输入排序，扫描序即字典序，严格大于才更新）。
    单点 → 该点重复两次（退化终点）；空表 → AdapterError。
    返回 ((ax, ay), (bx, by))，a ≤ b 字典序。
    """
    if not points:
        raise AdapterError("farthest_endpoints: 空点集，无端点可选")
    pts = sorted(points)
    if len(pts) == 1:
        p = pts[0]
        return p, p
    best = None  # (d2, a, b)
    for i in range(len(pts)):
        ax, ay = pts[i]
        for j in range(i + 1, len(pts)):
            bx, by = pts[j]
            dx = ax - bx
            dy = ay - by
            d2 = dx * dx + dy * dy
            if best is None or d2 > best[0]:
                best = (d2, pts[i], pts[j])
    return best[1], best[2]


def _arc_bbox(bbox, x1, y1, xm, ym, x2, y2, hw):
    """铜弧（track arc，KiCad 6+）包围盒：三控制点 + 真实圆弧扫掠范围（含 0/90/180/
    270° 轴向极值点），各 ± 半宽。三点共线或外接圆退化时控制点包围盒兜底。"""
    bbox.add(x1 - hw, y1 - hw, x1 + hw, y1 + hw)
    bbox.add(xm - hw, ym - hw, xm + hw, ym + hw)
    bbox.add(x2 - hw, y2 - hw, x2 + hw, y2 + hw)
    d = 2.0 * (x1 * (ym - y2) + xm * (y2 - y1) + x2 * (y1 - ym))
    if d == 0.0 or not math.isfinite(d):
        return
    r1sq = x1 * x1 + y1 * y1
    rmsq = xm * xm + ym * ym
    r2sq = x2 * x2 + y2 * y2
    ux = (r1sq * (ym - y2) + rmsq * (y2 - y1) + r2sq * (y1 - ym)) / d
    uy = (r1sq * (x2 - xm) + rmsq * (x1 - x2) + r2sq * (xm - x1)) / d
    r = math.hypot(x1 - ux, y1 - uy)
    if not (math.isfinite(ux) and math.isfinite(uy) and math.isfinite(r)) or r > 1e9:
        return
    a1 = math.atan2(y1 - uy, x1 - ux)
    am = math.atan2(ym - uy, xm - ux)
    a2 = math.atan2(y2 - uy, x2 - ux)
    dm = (am - a1) % _TAU
    d2 = (a2 - a1) % _TAU
    if dm <= d2:
        lo, span = a1, d2            # 逆时针 a1 → a2（含 mid）
    else:
        lo, span = a2, ((a1 - a2) % _TAU)  # 顺时针 a1 → a2 ⇔ 逆时针 a2 → a1
    for k in range(4):
        ang = k * (math.pi / 2.0)
        if (ang - lo) % _TAU <= span:
            if k == 0:
                bbox.add(ux + r - hw, uy - hw, ux + r + hw, uy + hw)
            elif k == 1:
                bbox.add(ux - hw, uy + r - hw, ux + hw, uy + r + hw)
            elif k == 2:
                bbox.add(ux - r - hw, uy - hw, ux - r + hw, uy + hw)
            else:
                bbox.add(ux - hw, uy - r - hw, ux + hw, uy - r + hw)


# ---------------------------------------------------------------- ptype / id 策略

def classify_ptype(net_name):
    """网名 → ptype 确定性映射（映射表写死并已在模块 docstring 披露）。"""
    u = net_name.upper()
    if u.startswith("+"):
        return "PWR"
    if u in POWER_EXACT_NAMES:
        return "PWR"
    if u.startswith("GND"):
        return "PWR"
    if "PWR" in u or "POWER" in u:
        return "PWR"
    return "MISC"


def sanitize_net_id(net_name):
    """网名 → 净化 id 片段：非 [A-Za-z0-9_.-] 字符替换为 "_"，空名 → "_"。"""
    out = []
    for ch in net_name:
        if ("a" <= ch <= "z" or "A" <= ch <= "Z" or "0" <= ch <= "9"
                or ch == "_" or ch == "." or ch == "-"):
            out.append(ch)
        else:
            out.append("_")
    s = "".join(out)
    return s if s else "_"


def _unique_partition_id(base, used):
    """base 未用则直接用；否则追加 "_2"、"_3"…（按确定网序处理 ⇒ 确定性）。"""
    if base not in used:
        used.add(base)
        return base
    k = 2
    while "%s_%d" % (base, k) in used:
        k += 1
    pid = "%s_%d" % (base, k)
    used.add(pid)
    return pid


def _cu_order(name):
    """铜层栈序键：F.Cu → In<N>.Cu（按 N 升序）→ B.Cu → 其余 *.Cu（名字序兜底）。"""
    if name == "F.Cu":
        return (0, 0, name)
    if name == "B.Cu":
        return (2, 0, name)
    if name.startswith("In") and name.endswith(".Cu"):
        try:
            return (1, int(name[2:-3]), name)
        except ValueError:
            return (1, 1 << 30, name)
    return (3, 0, name)


def _cos_sin(angle_deg):
    """(cos, sin)：0/90/180/270° 精确值（与 _rotate 同表），其余 math 三角。"""
    a = angle_deg % 360.0
    for base, cs, sn in _EXACT_COS_SIN:
        if abs(a - base) < 1e-9:
            return cs, sn
    rad = math.radians(a)
    return math.cos(rad), math.sin(rad)


def _pad_terminal(pad_sub, shape_tok, size, angle, layer_set, alias=None):
    """pad 子表 → pad_terminals 项（升级件① D1；模块 docstring 披露映射）。

    返回 dict（endpoint 由调用方按端点序填）或 None（无铜层 token——宽容跳过，
    调用方计数 pad_terminal_skipped）。rect 族在 footprint 旋转角下取轴对齐
    外接盒尺寸（保守包络，docstring 披露）。alias=FA-5a/5b legacy 层名翻译表
    （声明名→规范名；None/空=纯现代板，token 原样，行为逐字节不变）。"""
    w, h = size
    if shape_tok == "circle":
        shape, dims = "circle", [w]
    else:
        cs, sn = _cos_sin(angle)
        dims = [max(abs(w * cs) + abs(h * sn), 1e-9),
                max(abs(w * sn) + abs(h * cs), 1e-9)]
        shape = "rect"
    lay_node = _sub(pad_sub, "layers")
    tokens = [t for t in (lay_node[1:] if lay_node is not None else [])
              if isinstance(t, str)]
    if "*.Cu" in tokens or "*" in tokens:
        layers = "all"
    else:
        if alias:
            tokens = [alias.get(t, t) for t in tokens]
        copper = [t for t in tokens if t in layer_set]
        if not copper:
            return None
        layers = copper
    return {"endpoint": 0, "shape": shape, "size_mm": dims, "layers": layers}


def _pad_hole(pad_sub, ax, ay, where):
    """pad 子表 → (board.holes[] 项 或 None, 单参 oval 愈合计数 0/1)（V5-D8＋FA-5c）。

    type token（pad 子表第 2 位）= thru_hole → plated=True；np_thru_hole →
    plated=False；其余（smd/connect）→ (None, 0)（不入清单）。drill 子表：
    (drill D) → circle d=D；(drill oval A B) → oval（drill_mm=max(A,B) 保守
    外接圆、size_mm=[A,B] 原始值）；(drill oval D)（FA-5c 单参数，语料证据
    Theia 1.1/RF_SIGNAL 0.9）→ 两轴同值的退化槽 ≡ 圆孔 D（几何恒等，落 circle
    形态，不虚构第二轴；返回计数 1 供 report 汇总）；缺 drill / 非正 drill /
    带 offset 等子表 / 其余形态非法 → AdapterError（fail-closed，信息带定位）。"""
    if len(pad_sub) < 3 or type(pad_sub[2]) is not str:
        return None, 0
    type_tok = pad_sub[2]
    if type_tok == "thru_hole":
        plated = True
    elif type_tok == "np_thru_hole":
        plated = False
    else:
        return None, 0
    drill = _sub(pad_sub, "drill")
    if drill is None:
        raise AdapterError("%s: %s pad 缺 (drill) 钻孔字段（fail-closed，"
                           "不入静默缺省）" % (where, type_tok))
    toks = drill[1:]
    if any(type(t) is not str for t in toks):
        raise AdapterError("%s: (drill) 含 offset 等子表或非 token 形态 %r"
                           "（fail-closed：本 adapter 不近似偏心钻）" % (where, toks))
    if len(toks) == 1:
        d = _as_float(toks[0], "%s.drill" % where)
        if not (d > 0.0):
            raise AdapterError("%s: drill 直径非正 %r（fail-closed）" % (where, d))
        return {"pos_mm": [ax, ay], "drill_mm": d, "plated": plated,
                "shape": "circle"}, 0
    if len(toks) == 2 and toks[0] == "oval":
        # FA-5c：单参数 oval = 两轴同值退化槽 ≡ 圆孔（几何恒等；不虚构第二轴）。
        d = _as_float(toks[1], "%s.drill.oval" % where)
        if not (d > 0.0):
            raise AdapterError("%s: oval drill 尺寸非正 %r（fail-closed）"
                               % (where, d))
        return {"pos_mm": [ax, ay], "drill_mm": d, "plated": plated,
                "shape": "circle"}, 1
    if len(toks) == 3 and toks[0] == "oval":
        a = _as_float(toks[1], "%s.drill.oval" % where)
        b = _as_float(toks[2], "%s.drill.oval" % where)
        if not (a > 0.0 and b > 0.0):
            raise AdapterError("%s: oval drill 尺寸非正 %r×%r（fail-closed）"
                               % (where, a, b))
        return {"pos_mm": [ax, ay], "drill_mm": max(a, b), "plated": plated,
                "shape": "oval", "size_mm": [a, b]}, 0
    raise AdapterError("%s: (drill) 形态不可解析 %r（fail-closed：须为 "
                       "(drill D) 或 (drill oval A B)）" % (where, toks))


# ---------------------------------------------------------------- net class（V5-R7 W-1）

#: KiCad 缺省净类名（该类=缺省类：clearance → hard_rules.R5，成员不落 net_classes）。
DEFAULT_NET_CLASS_NAME = "Default"

# ------------------------------------------------- A1 可信侧车（EXEC-R3 R3-2，G1 A 口径）

#: .netclass-mask.json 侧车合同钉值——与 v5.kicad_export 落件口径同字符串
#: （本件不反向 import exporter，避免环；两处钉值由回归对账，改须同批）。
NETCLASS_MASK_RULE = "netclass-mask-v1"
#: 侧车 schema 版本（2=A1 值权威面：v5_width_mm/缺类板最小形/pcb+pro 内容绑定；
#: 1=历史形态。未知/缺版本 fail-closed 不采值——见 _apply_netclass_mask_values）。
NETCLASS_MASK_SCHEMA_VERSION = 2
NETCLASS_MASK_GENERATOR = "v5.kicad_export"
NETCLASS_MASK_SUFFIX = ".netclass-mask.json"


def _as_num(v, where):
    """JSON 数值（bool 除外）且有限非负；否则 AdapterError（fail-closed）。"""
    if (not isinstance(v, (int, float)) or isinstance(v, bool)
            or not math.isfinite(float(v)) or float(v) < 0.0):
        raise AdapterError("%s: 须为 ≥0 有限数值，实得 %r" % (where, v))
    return float(v)


def load_pro_net_settings(pcb_path):
    """同 stem .kicad_pro 的 net_settings（dict）或 None（无文件/无键）。

    文件存在但 JSON 不可解析 / 顶层非 dict / net_settings 非 dict ⇒ AdapterError
    （声明载体在场而不可读=声明缺失风险，fail-closed 不静默）。"""
    pro_path = os.path.splitext(os.fspath(pcb_path))[0] + ".kicad_pro"
    if not os.path.exists(pro_path):
        return None
    try:
        with open(pro_path, encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, ValueError) as exc:
        raise AdapterError(".kicad_pro 项目文件不可解析 %s: %s（fail-closed）"
                           % (pro_path, exc)) from exc
    if not isinstance(doc, dict):
        raise AdapterError(".kicad_pro 顶层须为 JSON 对象: %s" % pro_path)
    ns = doc.get("net_settings")
    if ns is None:
        return None
    if not isinstance(ns, dict):
        raise AdapterError(".kicad_pro net_settings 须为对象，实得 %s"
                           % type(ns).__name__)
    return ns


def _pro_net_classes(ns):
    """net_settings → (classes{名:(clearance,width)}, membership{网:[类名]})。

    classes 缺/非列表 ⇒ AdapterError；netclass_patterns 非空 ⇒ AdapterError
    （正则语义未钉，fail-closed 不静默猜）；assign 引用未知类 ⇒ AdapterError。
    指派值取 "cls" 或 KiCad 8.99 meta v4 列表形 ["cls",...]。"""
    classes_raw = ns.get("classes")
    if not isinstance(classes_raw, list):
        raise AdapterError(".kicad_pro net_settings.classes 须为列表，实得 %s"
                           % type(classes_raw).__name__)
    classes = {}
    for i, cls in enumerate(classes_raw):
        where = ".kicad_pro net_settings.classes[%d]" % i
        if not isinstance(cls, dict):
            raise AdapterError("%s 须为对象" % where)
        name = cls.get("name")
        if not isinstance(name, str) or not name:
            raise AdapterError("%s.name 须为非空字符串，实得 %r" % (where, name))
        if name in classes:
            raise AdapterError("%s.name 净类名重复: %r" % (where, name))
        classes[name] = (_as_num(cls.get("clearance"), where + ".clearance"),
                         _as_num(cls.get("track_width"), where + ".track_width"))
    patterns = ns.get("netclass_patterns")
    if patterns:
        raise AdapterError(".kicad_pro netclass_patterns 非空（正则指派语义未钉，"
                           "本 adapter 不静默猜——fail-closed；实得 %d 条）"
                           % len(patterns))
    assignments = ns.get("netclass_assignments")
    if assignments is None:
        assignments = {}
    if not isinstance(assignments, dict):
        raise AdapterError(".kicad_pro netclass_assignments 须为对象，实得 %s"
                           % type(assignments).__name__)
    membership = {}
    for net, refs in assignments.items():
        if isinstance(refs, str):
            names = [refs]
        elif isinstance(refs, list) and all(isinstance(r, str) for r in refs):
            names = list(refs)
        else:
            raise AdapterError(".kicad_pro netclass_assignments[%r] 须为类名字符串"
                               "或类名列表，实得 %r" % (net, refs))
        for cls in names:
            if cls not in classes:
                raise AdapterError(".kicad_pro netclass_assignments[%r] 引用未知"
                                   "净类 %r（classes=%s）" % (net, cls,
                                                              sorted(classes)))
        membership.setdefault(net, []).extend(names)
    return classes, membership


def _board_net_class_blocks(root):
    """板内 legacy (net_class ...) 块（KiCad ≤5）→ (classes, membership)。

    形态：(net_class "Name" "desc" (clearance C) (trace_width W) (add_net "N")…)；
    clearance/trace_width 缺/非法、name 非串 ⇒ AdapterError。"""
    classes = {}
    membership = {}
    for item in root[1:]:
        if type(item) is not list or not item or item[0] != "net_class":
            continue
        if len(item) < 2 or type(item[1]) is not str or not item[1]:
            raise AdapterError("(net_class) 名字字段非法: %r"
                               % (item[1] if len(item) > 1 else "?",))
        name = item[1]
        if name in classes:
            raise AdapterError("(net_class %r) 重复声明" % name)
        cl = _sub(item, "clearance")
        tw = _sub(item, "trace_width")
        if cl is None or tw is None:
            raise AdapterError("(net_class %r) 缺 (clearance)/(trace_width)"
                               "（fail-closed）" % name)
        where = "(net_class %r)" % name
        classes[name] = (
            _as_num(_floats(cl, 1, where + ".clearance")[0], where + ".clearance"),
            _as_num(_floats(tw, 1, where + ".trace_width")[0], where + ".trace_width"))
        members = []
        for sub in item[1:]:
            if type(sub) is list and sub and sub[0] == "add_net":
                if len(sub) < 2 or type(sub[1]) is not str:
                    raise AdapterError("(net_class %r) (add_net) 成员名非法: %r"
                                       % (name, sub[1:] and sub[1]))
                members.append(sub[1])
        membership[name] = members
    return classes, membership


def _emit_net_classes(pro_ns, root, known_nets, report):
    """双源合并（P1 优先序）→ (net_classes dict 或 None, r5_default 或 None)。

    known_nets=板上网名集合；未知网成员忽略并计 stale（不拒整板）；仅 Default /
    无类网=缺省类（计 unassigned）；Default clearance → r5_default（P4）。"""
    report["net_class_source"] = "none"
    report["net_class_count"] = 0
    report["net_class_unassigned_nets"] = 0
    report["net_class_stale_members"] = 0
    report["net_class_board_blocks_ignored"] = 0
    blocks = [item for item in root[1:]
              if type(item) is list and item and item[0] == "net_class"]
    classes = membership = None
    if pro_ns is not None:
        # net_settings 在场 ⇒ 载体即权威（P1）：classes 缺/非列表/项非法均
        # fail-closed（_pro_net_classes）；空类表=零声明缺省路径（披露 source）。
        classes, membership = _pro_net_classes(pro_ns)
        report["net_class_source"] = "kicad_pro"
        report["net_class_board_blocks_ignored"] = len(blocks)
        if not classes:
            classes = membership = None
    elif blocks:
        classes, membership = _board_net_class_blocks(root)
        report["net_class_source"] = "kicad_pcb"
    if classes is None:
        report["net_class_unassigned_nets"] = len(known_nets)
        return None, None
    # membership → {网: [类名]}（板内块形态 {类: [网]} → 翻转；stale 计数）
    net_classes_list = {}
    assigned = {}
    if report["net_class_source"] == "kicad_pro":
        for net, names in membership.items():
            if net not in known_nets:
                report["net_class_stale_members"] += len(names)
                continue
            assigned.setdefault(net, []).extend(names)
    else:
        for cls_name, members in membership.items():
            for net in members:
                if net not in known_nets:
                    report["net_class_stale_members"] += 1
                    continue
                assigned.setdefault(net, []).append(cls_name)
    r5_default = None
    out = {}
    for cls_name in sorted(classes):
        clearance, width = classes[cls_name]
        if cls_name == DEFAULT_NET_CLASS_NAME:
            r5_default = clearance
            continue
        members = sorted(net for net, names in assigned.items()
                         if cls_name in names)
        out[cls_name] = {"clearance_mm": clearance, "width_mm": width,
                         "members": members}
    report["net_class_count"] = len(out)
    report["net_class_unassigned_nets"] = sum(
        1 for net in known_nets
        if not any(n != DEFAULT_NET_CLASS_NAME for n in assigned.get(net, ())))
    return (out or None), r5_default


def load_netclass_mask_binding(pcb_path, pcb_bytes):
    """A1 可信侧车原料读（同 stem .netclass-mask.json；EXEC-R3 R3-2）。

    不在场 → None（真实板路径：net_classes/R5 走 P1..P5 原行为，逐字节不变）。
    在场：JSON 不可解析 / 顶层非对象 / 同 stem ``.kicad_pro`` 缺件或不可读 ⇒
    AdapterError（声明载体在场而不可读/绑定缺件=声明缺失风险，fail-closed 不
    静默回退）。返回 {"mask": doc, "mask_path", "pro_path", "pro_sha256"
    （pro 实际 bytes 摘要）}；结构/版本/归属/内容绑定核验统一在
    :func:`_apply_netclass_mask_values`（需板内 host 行，故在 s-expr 解析后）。"""
    mask_path = os.path.splitext(os.fspath(pcb_path))[0] + NETCLASS_MASK_SUFFIX
    if not os.path.exists(mask_path):
        return None
    try:
        with open(mask_path, encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, ValueError) as exc:
        raise AdapterError(".netclass-mask 侧车不可解析 %s: %s（A1 fail-closed，"
                           "不静默回退）" % (mask_path, exc)) from exc
    if not isinstance(doc, dict):
        raise AdapterError(".netclass-mask 顶层须为 JSON 对象: %s（A1 fail-closed）"
                           % mask_path)
    pro_path = os.path.splitext(os.fspath(pcb_path))[0] + ".kicad_pro"
    try:
        with open(pro_path, "rb") as f:
            pro_bytes = f.read()
    except OSError as exc:
        raise AdapterError(".netclass-mask 在场而同 stem .kicad_pro 缺件/不可读 "
                           "%s（v5 导出件三件成套，A1 fail-closed）" % pro_path) from exc
    return {"mask": doc, "mask_path": mask_path, "pro_path": pro_path,
            "pro_sha256": canonical.sha256_bytes(pro_bytes)}


def _mask_num(value, where, positive=False):
    """侧车数值字段核验（bool 除外、有限、>0/≥0）；非法抛 AdapterError。"""
    if (not isinstance(value, (int, float)) or isinstance(value, bool)
            or not math.isfinite(float(value)) or float(value) < 0.0
            or (positive and float(value) <= 0.0)):
        raise AdapterError(".netclass-mask 侧车 %s: 须为 %s 有限数值，实得 %r"
                           "（A1 fail-closed）"
                           % (where, "正" if positive else "≥0", value))
    return float(value)


def _apply_netclass_mask_values(binding, pcb_bytes, root, pro_ns,
                                net_classes, r5_default, report):
    """A1 值权威施加（G1 A 口径）：严格归属/内容绑定核验全对上 ⇒ 值取侧车。

    值面：classes[Default].v5_clearance_mm → r5_default（必为正——exporter
    R5>0 fail-closed 门的源板侧投影）；非 Default 类 v5_clearance_mm/
    v5_width_mm → net_classes 值；empty_net_classes 逐项恢复 board.net_classes
    空声明（members=[]，不从侧车发明成员）。成员面：仍取 .kicad_pro/
    netclass_assignments（_emit_net_classes 产物原样保留），侧车 members 清单
    仅披露不采信。

    fail-closed 面（任一命中即 AdapterError，不静默回退后报保真）：
    - 格式/版本/来源：rule≠netclass-mask-v1；schema_version≠2（含缺/历史 1）；
      generated_by≠v5.kicad_export；
    - 归属（错绑）：PCB host 行非 v5.kicad_export 导出；host 行原模型
      board_sha256/board_id 与侧车不符（host 原模型 hash≠PCB 文件 hash≠回读
      b2 模型 hash，三种对象不混比）；
    - 内容绑定：pcb_sha256 与实际 PCB bytes 摘要不符；pro_sha256 与实际
      .kicad_pro bytes 摘要不符；.kicad_pro net_settings 缺席；
    - 字段完整性：classes 缺/非对象/缺 Default；类缺 v5_clearance_mm/
      v5_width_mm（Default 的 width=null=not_available 容忍）；Default R5 非正；
      empty_net_classes 缺 name/v5_clearance_mm/v5_width_mm；
    - pro 声明冲突：classes 类名集 ≠ .kicad_pro net_settings.classes 类名集；
      空声明类名出现在 classes/或与 pro classes 撞名。"""
    mask = binding["mask"]

    def mfail(where, msg):
        raise AdapterError(".netclass-mask 侧车 %s: %s（A1 fail-closed，"
                           "不静默回退）" % (where, msg))

    if mask.get("rule") != NETCLASS_MASK_RULE:
        mfail("rule", "须为 %r，实得 %r" % (NETCLASS_MASK_RULE, mask.get("rule")))
    sv = mask.get("schema_version")
    if (not isinstance(sv, int) or isinstance(sv, bool)
            or sv != NETCLASS_MASK_SCHEMA_VERSION):
        mfail("schema_version", "未知/缺版本（须 %d；1=历史形态无值权威面），"
              "实得 %r" % (NETCLASS_MASK_SCHEMA_VERSION, sv))
    if mask.get("generated_by") != NETCLASS_MASK_GENERATOR:
        mfail("generated_by", "导出来源须 %r，实得 %r"
              % (NETCLASS_MASK_GENERATOR, mask.get("generated_by")))
    # ---- 归属：导出 PCB host 行（固定形 (host v5.kicad_export "generator=…
    #      generator_version=… board_id=… board_sha256=…")；board_id 含空格属
    #      导出侧格式前置约束，此处同口径解析）。
    host = _sub(root, "host")
    if (host is None or len(host) < 3 or host[1] != NETCLASS_MASK_GENERATOR
            or not isinstance(host[2], str)):
        mfail("归属", "PCB host 行非 %s 导出件（错绑），实得 %r"
              % (NETCLASS_MASK_GENERATOR, host))
    host_meta = {}
    for tok in host[2].split(" "):
        if "=" in tok:
            key, _, val = tok.partition("=")
            host_meta[key] = val
    if mask.get("board_sha256") != host_meta.get("board_sha256"):
        mfail("board_sha256", "与导出 PCB host 行原模型 hash 不符（错绑）: "
              "%r != %r" % (mask.get("board_sha256"),
                            host_meta.get("board_sha256")))
    if mask.get("board_id") != host_meta.get("board_id"):
        mfail("board_id", "与导出 PCB host 行 board_id 不符: %r != %r"
              % (mask.get("board_id"), host_meta.get("board_id")))
    # ---- 实际内容绑定（导出端程序化摘要 ↔ 本地文件逐位复核）。
    if mask.get("pcb_sha256") != canonical.sha256_bytes(pcb_bytes):
        mfail("pcb_sha256", "与实际 PCB 文件内容摘要不符（错绑/被改写）")
    if mask.get("pro_sha256") != binding["pro_sha256"]:
        mfail("pro_sha256", "与实际 .kicad_pro 文件内容摘要不符（错绑/被改写）")
    if pro_ns is None:
        mfail("pro", "net_settings 缺席（成员面权威载体缺失；v5 导出件三件成套）")
    # ---- 字段完整性（值按现行类型/有限性/范围契约验证）。
    classes_raw = mask.get("classes")
    if not isinstance(classes_raw, dict) or not classes_raw:
        mfail("classes", "须为非空对象，实得 %s"
              % (type(classes_raw).__name__ if classes_raw is not None else None))
    if not isinstance(classes_raw.get(DEFAULT_NET_CLASS_NAME), dict):
        mfail("classes[%r]" % DEFAULT_NET_CLASS_NAME,
              "缺 Default 项（Default 原 R5 每板必存）")
    values = {}
    for name, entry in classes_raw.items():
        where = "classes[%r]" % (name,)
        if not isinstance(name, str) or not name or not isinstance(entry, dict):
            mfail(where, "须为非空字符串名→对象项")
        cl = _mask_num(entry.get("v5_clearance_mm"), where + ".v5_clearance_mm")
        if name == DEFAULT_NET_CLASS_NAME:
            w = entry.get("v5_width_mm")
            if w is not None:   # null=not_available（源 Default 线宽不入板模型）
                w = _mask_num(w, where + ".v5_width_mm")
        else:
            w = entry.get("v5_width_mm")
            if w is None:
                mfail(where + ".v5_width_mm", "缺必要源值（非 Default 类必带原宽）")
            w = _mask_num(w, where + ".v5_width_mm")
        values[name] = (cl, w)
    r5_mask = values[DEFAULT_NET_CLASS_NAME][0]
    if not (r5_mask > 0.0):
        mfail("classes[%r].v5_clearance_mm" % DEFAULT_NET_CLASS_NAME,
              "Default R5 须为正（exporter R5>0 fail-closed 门的源板侧投影），"
              "实得 %r" % r5_mask)
    empty_raw = mask.get("empty_net_classes")
    if empty_raw is None:
        empty_raw = []
    if not isinstance(empty_raw, list):
        mfail("empty_net_classes", "须为列表，实得 %s" % type(empty_raw).__name__)
    empty_values = {}
    for i, entry in enumerate(empty_raw):
        where = "empty_net_classes[%d]" % i
        if not isinstance(entry, dict):
            mfail(where, "须为对象")
        name = entry.get("name")
        if not isinstance(name, str) or not name:
            mfail(where + ".name", "须为非空字符串，实得 %r" % (name,))
        if name in classes_raw or name in empty_values:
            mfail(where + ".name", "类名撞名 %r（与 classes/既有空类）" % name)
        cl = _mask_num(entry.get("v5_clearance_mm"), where + ".v5_clearance_mm")
        if entry.get("v5_width_mm") is None:
            mfail(where + ".v5_width_mm", "缺必要源值（空声明类必带原宽）")
        w = _mask_num(entry.get("v5_width_mm"), where + ".v5_width_mm")
        empty_values[name] = (cl, w)
    # ---- pro 声明冲突核验（类名集双侧一致；空类不落 pro 为导出契约）。
    pro_classes, _ = _pro_net_classes(pro_ns)
    if set(pro_classes) != set(classes_raw):
        mfail("声明冲突", "classes 类名集 %s 与 .kicad_pro 声明 %s 不符"
              % (sorted(classes_raw), sorted(pro_classes)))
    for name in empty_values:
        if name in pro_classes:
            mfail("声明冲突", "空声明类 %r 不得出现在 .kicad_pro classes" % name)
    # ---- 施加：值取侧车，成员保留 _emit_net_classes（pro/netclass_assignments
    #      权威），空声明只恢复空成员。
    out = {}
    if net_classes:
        out.update(net_classes)
    for name, (cl, w) in values.items():
        if name == DEFAULT_NET_CLASS_NAME:
            continue
        members = out.get(name, {}).get("members", [])
        out[name] = {"clearance_mm": cl, "width_mm": w, "members": members}
    for name, (cl, w) in empty_values.items():
        out[name] = {"clearance_mm": cl, "width_mm": w, "members": []}
    report["netclass_mask_value_authority"] = True
    report["net_class_count"] = len(out)
    return (out or None), r5_mask


# ---------------------------------------------------------------- 板轮廓（V5-R7 W-3）

#: 轮廓链接容差（mm）：KiCad 文件坐标 5~6 位小数舍入（语料实测断口 ~2e-6；
#: DipTrace 等第三方导出实测断口至 8e-3——axiom-micro 语料）。取 0.01mm：
#: 覆盖文件舍入级断口、仍 ≪ 任何真实设计开口（≥0.1mm 级）。
OUTLINE_CHAIN_TOL_MM = 1e-2
#: 自交判定弧离散弦数（确定性近似；仅判定用，几何本体保持解析弧）。
ARC_TEST_CHORDS = 64


def _edge_layer_of(item):
    lay = _sub(item, "layer")
    if lay is None or len(lay) < 2 or type(lay[1]) is not str:
        return None
    return lay[1]


def _arc_mid_end_from_center(center, start_pt, angle_deg):
    """KiCad ≤5 gr_arc/fp_arc 中心形 → (mid, end)（三点弧同构；确定三角）。"""
    r = math.hypot(start_pt[0] - center[0], start_pt[1] - center[1])
    a0 = math.atan2(start_pt[1] - center[1], start_pt[0] - center[0])
    am = a0 + math.radians(angle_deg) / 2.0
    a1 = a0 + math.radians(angle_deg)
    return ((center[0] + r * math.cos(am), center[1] + r * math.sin(am)),
            (center[0] + r * math.cos(a1), center[1] + r * math.sin(a1)))


def _arc_item_from_node(item, where, transform=None):
    """gr_arc/fp_arc 节点 → ("arc", start, mid, end)（双形归一；transform 施于
    全部三点=footprint 局部→绝对）。中心形角度值=度（语料 vga/anavi 实测 -180/90）。"""
    s = _floats(_sub(item, "start"), 2, where + ".start")
    e = _floats(_sub(item, "end"), 2, where + ".end")
    mid_node = _sub(item, "mid")
    if transform is not None:
        s = transform(s[0], s[1])
        e = transform(e[0], e[1])
    else:
        s, e = (s[0], s[1]), (e[0], e[1])
    if mid_node is not None:
        mv = _floats(mid_node, 2, where + ".mid")
        m = transform(mv[0], mv[1]) if transform is not None else (mv[0], mv[1])
    else:
        ang = _sub(item, "angle")
        if ang is None:
            raise AdapterError("%s: 弧缺 (mid)（三点形）或 (angle)（中心形）"
                               "（fail-closed）" % where)
        # KiCad ≤5 中心形：(start)=圆心、(end)=弧起点、(angle)=带号度数。
        m, e2 = _arc_mid_end_from_center(s, e, _floats(ang, 1, where + ".angle")[0])
        s, e = e, e2   # 弧起点=原 (end) 节点；终点=扫掠角换算点
    return ("arc", s, m, e)


#: 圆图元 → 4 段四分之一弧（闭环；确定性分解，r/起角 从 (center)→(end) 求得）。
def _circle_edges(center, end_pt, where):
    r = math.hypot(end_pt[0] - center[0], end_pt[1] - center[1])
    if not (r > 0.0) or not math.isfinite(r):
        raise AdapterError("%s: 圆半径非正 %r（fail-closed）" % (where, r))
    cx, cy = center
    a0 = math.atan2(end_pt[1] - cy, end_pt[0] - cx)
    out = []
    for k in range(4):
        b0 = a0 + k * (math.pi / 2.0)
        bm = b0 + math.pi / 4.0
        b1 = b0 + math.pi / 2.0
        out.append(("arc",
                    (cx + r * math.cos(b0), cy + r * math.sin(b0)),
                    (cx + r * math.cos(bm), cy + r * math.sin(bm)),
                    (cx + r * math.cos(b1), cy + r * math.sin(b1))))
    return out


#: 贝塞尔离散弦数（确定性近似；gr_curve/fp_curve → 折线段）。
CURVE_TEST_CHORDS = 32


def _curve_edges(pts, where):
    """4 控制点三次贝塞尔 → CURVE_TEST_CHORDS 弦折线段（de Casteljau，确定算术）。"""
    if len(pts) != 4:
        raise AdapterError("%s: 贝塞尔须 4 控制点，实得 %d（fail-closed）"
                           % (where, len(pts)))
    out = []
    k = CURVE_TEST_CHORDS
    prev = pts[0]
    for t in range(1, k + 1):
        u = t / k
        q = [(a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
             for a, b in zip(pts[:3], pts[1:])]
        q = [(a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
             for a, b in zip(q[:2], q[1:])]
        p = (q[0][0] + (q[1][0] - q[0][0]) * u,
             q[0][1] + (q[1][1] - q[0][1]) * u)
        out.append(("segment", prev, p))
        prev = p
    return out


def _polyline_edges(pts, where):
    """(pts (xy..)...) 多边形 → 邻接段+闭合段（≥2 顶点；KiCad poly 不自闭合写）。"""
    if len(pts) < 2:
        raise AdapterError("%s: 多边形顶点 <2（fail-closed）" % where)
    return [("segment", a, b) for a, b in zip(pts, pts[1:] + pts[:1])]


def _pts_of(item, where, transform=None):
    """(pts (xy x y)...) → [点...]（transform 施于每点）。"""
    node = _sub(item, "pts")
    if node is None:
        raise AdapterError("%s: 缺 (pts) 节点（fail-closed）" % where)
    out = []
    for sub in node[1:]:
        if type(sub) is not list or not sub or sub[0] != "xy":
            raise AdapterError("%s.pts: 含非 (xy x y) 项 %r" % (where, sub))
        v = _floats(sub, 2, where + ".pts.xy")
        out.append(transform(v[0], v[1]) if transform is not None
                   else (v[0], v[1]))
    return out


#: Edge_Cuts 支持图元集（gr_/fp_ 前缀外的图元/装饰文本不在此列）。
_OUTLINE_GR_HEADS = ("gr_line", "gr_rect", "gr_arc", "gr_circle", "gr_poly",
                     "gr_curve")
_OUTLINE_FP_HEADS = ("fp_line", "fp_rect", "fp_arc", "fp_circle", "fp_poly",
                     "fp_curve")


def _collect_outline_edges(root):
    """Edge_Cuts 图元 → 边列表（确定性：源文件出现序）。

    顶层 gr_line/gr_rect/gr_arc/gr_circle/gr_poly/gr_curve + footprint 内
    fp_line/fp_rect/fp_arc/fp_circle/fp_poly/fp_curve（局部坐标按 footprint
    (at)+角度旋转=pad 同口径）。circle → 4 段四分之一弧；poly → 邻接+闭合段；
    curve → CURVE_TEST_CHORDS 弦。退化边（起终点距 ≤ 链接容差）剔除（零几何）。
    其余 Edge.Cuts 图元 ⇒ AdapterError（不支持图元 fail-closed，不静默丢轮廓）。
    返回 [] 当板上无 Edge_Cuts 图元（缺省路径零漂移）。"""
    tol = OUTLINE_CHAIN_TOL_MM
    edges = []

    def _add(edge):
        if math.hypot(edge[-1][0] - edge[1][0], edge[-1][1] - edge[1][1]) > tol:
            edges.append(edge)

    def _emit(head, item, where, transform=None):
        if head in ("gr_line", "fp_line"):
            s = _floats(_sub(item, "start"), 2, where + ".start")
            e = _floats(_sub(item, "end"), 2, where + ".end")
            if transform is not None:
                s = transform(s[0], s[1])
                e = transform(e[0], e[1])
            _add(("segment", (s[0], s[1]), (e[0], e[1])))
        elif head in ("gr_rect", "fp_rect"):
            s = _floats(_sub(item, "start"), 2, where + ".start")
            e = _floats(_sub(item, "end"), 2, where + ".end")
            pts = [(s[0], s[1]), (e[0], s[1]), (e[0], e[1]), (s[0], e[1])]
            if transform is not None:
                pts = [transform(x, y) for (x, y) in pts]
            for a, b in zip(pts, pts[1:] + pts[:1]):
                _add(("segment", a, b))
        elif head in ("gr_arc", "fp_arc"):
            _add(_arc_item_from_node(item, where, transform=transform))
        elif head in ("gr_circle", "fp_circle"):
            c = _floats(_sub(item, "center"), 2, where + ".center")
            e = _floats(_sub(item, "end"), 2, where + ".end")
            if transform is not None:
                c = transform(c[0], c[1])
                e = transform(e[0], e[1])
            for edge in _circle_edges((c[0], c[1]), (e[0], e[1]), where):
                _add(edge)
        elif head in ("gr_poly", "fp_poly"):
            for a, b in _polyline_edges(_pts_of(item, where, transform), where):
                _add(("segment", a, b))
        else:  # gr_curve / fp_curve
            for edge in _curve_edges(_pts_of(item, where, transform), where):
                _add(edge)

    for item in root[1:]:
        if type(item) is not list or not item or type(item[0]) is not str:
            continue
        head = item[0]
        if head == "module" or head == "footprint":
            at = _sub(item, "at")
            if at is None:
                raise AdapterError("%s 缺 (at) 位置" % head)
            vals = _floats(at, 2, "%s.at" % head)
            fx, fy = vals[0], vals[1]
            angle = vals[2] if len(vals) > 2 else 0.0
            fdesc = item[1] if len(item) > 1 and type(item[1]) is str else "?"

            def _fp_transform(x, y, _fx=fx, _fy=fy, _a=angle):
                r = _rotate(x, y, _a)
                return (_fx + r[0], _fy + r[1])
            for sub in item[1:]:
                if type(sub) is not list or not sub or type(sub[0]) is not str:
                    continue
                shead = sub[0]
                if _edge_layer_of(sub) != "Edge.Cuts":
                    continue
                if shead not in _OUTLINE_FP_HEADS:
                    if shead.startswith("fp_"):
                        raise AdapterError("Edge.Cuts 上不支持图元 %r@%s（fail-"
                                           "closed 不静默丢轮廓；支持集=%s）"
                                           % (shead, fdesc, _OUTLINE_FP_HEADS))
                    continue
                _emit(shead, sub, "fp_%s@%s" % (shead[3:], fdesc),
                      transform=_fp_transform)
            continue
        if _edge_layer_of(item) != "Edge.Cuts":
            continue
        if head in _OUTLINE_GR_HEADS:
            _emit(head, item, head)
        elif head.startswith("gr_"):
            raise AdapterError("Edge.Cuts 上不支持图元 %r（fail-closed 不静默丢"
                               "轮廓；支持集=%s）" % (head, _OUTLINE_GR_HEADS))
    return edges


def _edge_endpoints(edge):
    return edge[1], edge[-1]


def _loop_key(loop):
    """环几何指纹（方向/起点不敏感；坐标 1e-6 量化）——重复环去重键。

    DipTrace 等第三方导出常见整环重影（badge-pcb 语料：370 fp_line 全部成对）；
    物理轮廓唯一，几何恒等环折叠为一（确定性：保留首现环）。"""
    items = []
    for e in loop:
        z = tuple((round(p[0], 6), round(p[1], 6)) for p in e[1:])
        if e[0] == "segment":
            items.append(("s",) + tuple(sorted(z)))
        else:
            s, m, t = z
            items.append(("a",) + tuple(sorted((s, t))) + (m,))
    return tuple(sorted(items))


def _dedupe_identical_loops(loops):
    seen = set()
    out = []
    for loop in loops:
        key = _loop_key(loop)
        if key in seen:
            continue
        seen.add(key)
        out.append(loop)
    return out


def _reverse_edge(edge):
    if edge[0] == "segment":
        return ("segment", edge[2], edge[1])
    return ("arc", edge[3], edge[2], edge[1])


def _chain_loops(edges):
    """边列表 → 闭合环列表（每环=(边…) 链接序；起点=环内最小源序边）。

    开口（容差内无可继边）⇒ AdapterError bad outline。环序按各环最小源序边
    升序（确定性）。"""
    tol = OUTLINE_CHAIN_TOL_MM
    n = len(edges)
    used = [False] * n
    loops = []
    for i in range(n):
        if used[i]:
            continue
        chain_edges = [edges[i]]
        used[i] = True
        first = edges[i][1]
        cur = edges[i][-1]
        while math.hypot(cur[0] - first[0], cur[1] - first[1]) > tol:
            found = None
            for j in range(n):
                if used[j]:
                    continue
                sj, ej = _edge_endpoints(edges[j])
                if math.hypot(sj[0] - cur[0], sj[1] - cur[1]) <= tol:
                    found = (j, False)
                    break
                if math.hypot(ej[0] - cur[0], ej[1] - cur[1]) <= tol:
                    found = (j, True)
                    break
            if found is None:
                raise AdapterError("bad outline：Edge_Cuts 边链开口（终点 %r 无可"
                                   "继边，容差 %g mm）——与 kicad-cli 同口径 "
                                   "fail-closed" % (cur, tol))
            j, rev = found
            used[j] = True
            edge = _reverse_edge(edges[j]) if rev else edges[j]
            chain_edges.append(edge)
            cur = edge[-1]
        if len(chain_edges) < 3:
            raise AdapterError("bad outline：闭合环边数 <3（%d 边）" % len(chain_edges))
        loops.append(tuple(chain_edges))
    return loops


#: FA-5d 轮廓吸附愈合容差（mm）：端点聚类簇径上限。取 0.2：覆盖族内实测最大断口
#: 0.1634（z2amiller_sensorboard，逐边核验 0.068/0.100/0.163mm 三断口）＋余量、
#: 为链容差 0.01 的 20 倍、仍 ≪ 真实设计开口（≥1mm 级）。更大真实开口在愈合后
#: 仍链不上 → 维持 fail-closed 拒收（不静默吞）。
OUTLINE_HEAL_TOL_MM = 0.2


def _snap_heal_endpoints(edges):
    """FA-5d：边端点吸附愈合 → (新边列表, 合并簇数)；无可合并点 → (None, 0)。

    确定性：端点按字典序排序后扫掠聚类——各簇代表点=簇内字典序最小点（实际文件
    坐标，不发明坐标），成员距代表点 ≤ OUTLINE_HEAL_TOL_MM（簇径 ≤ 2×容差）；
    候选簇=当前活动窗口内全部簇（x 窗淘汰保证只小不大），命中多簇取代表点最近
    （平手取字典序最小代表点=扫描首见）。吸附后重建各边（弧仅动 start/end，mid
    保留原值——愈合量级下弧形偏差可忽略且保持三点弧合同）；吸附后起终重合
    （≤ 链容差）的退化边剔除。"""
    pts = []
    for e in edges:
        pts.append(e[1])
        pts.append(e[-1])
    # 数值容差 +1e-9：临界距离的浮点表示（实测 91.7-91.5=0.20000000000000284）
    # 不得把 0.2mm 内的点误拆簇（z2amiller 实测命中）。
    tol = OUTLINE_HEAL_TOL_MM + 1e-9
    assign = {}
    members = {}     # 代表点 -> {成员点}（去重；>1 即真愈合簇）
    active = []      # 活动簇代表点（升序；x 窗外的簇不可能再吸收后续点，淘汰）
    for p in sorted(pts):
        if p in assign:
            continue
        active = [r for r in active if p[0] - r[0] <= tol]
        best = None   # (距离, 代表点)
        for r in active:
            d = math.hypot(p[0] - r[0], p[1] - r[1])
            if d <= tol and (best is None or d < best[0]):
                best = (d, r)
        if best is None:
            active.append(p)
            active.sort()
            assign[p] = p
            members[p] = {p}
        else:
            assign[p] = best[1]
            members[best[1]].add(p)
    merged = sum(1 for m in members.values() if len(m) > 1)
    if merged == 0:
        return None, 0
    out = []
    for e in edges:
        if e[0] == "segment":
            s, t = assign[e[1]], assign[e[2]]
            if math.hypot(t[0] - s[0], t[1] - s[1]) > OUTLINE_CHAIN_TOL_MM:
                out.append(("segment", s, t))
        else:
            s, m, t = assign[e[1]], e[2], assign[e[3]]
            if math.hypot(t[0] - s[0], t[1] - s[1]) > OUTLINE_CHAIN_TOL_MM:
                out.append(("arc", s, m, t))
    return out, merged


def _orient(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _on_segment(a, b, p):
    return (abs(_orient(a, b, p)) <= 1e-12
            and min(a[0], b[0]) - 1e-12 <= p[0] <= max(a[0], b[0]) + 1e-12
            and min(a[1], b[1]) - 1e-12 <= p[1] <= max(a[1], b[1]) + 1e-12)


def _segments_intersect(a, b, c, d):
    """两端闭线段相交判定（含共点/共线叠置；纯比较+容差 1e-12，确定性）。"""
    if _on_segment(a, b, c) or _on_segment(a, b, d) \
            or _on_segment(c, d, a) or _on_segment(c, d, b):
        return True
    o1 = _orient(a, b, c)
    o2 = _orient(a, b, d)
    o3 = _orient(c, d, a)
    o4 = _orient(c, d, b)
    return ((o1 > 0) != (o2 > 0)) and ((o3 > 0) != (o4 > 0)) \
        and o1 != 0 and o2 != 0 and o3 != 0 and o4 != 0


def _edge_test_segments(edge):
    """边 → 自交/containment 判定用折线段列（弧离散 ARC_TEST_CHORDS 弦，
    首尾精确钉 s/e 端点、中间极坐标插值；s/m/e 共线或外接圆退化 → 弦兜底）。"""
    if edge[0] == "segment":
        return [(edge[1], edge[2])]
    s, m, e = edge[1], edge[2], edge[3]
    d = 2.0 * (s[0] * (m[1] - e[1]) + m[0] * (e[1] - s[1]) + e[0] * (s[1] - m[1]))
    if d == 0.0 or not math.isfinite(d):
        return [(s, e)]
    r1 = s[0] * s[0] + s[1] * s[1]
    rm = m[0] * m[0] + m[1] * m[1]
    re_ = e[0] * e[0] + e[1] * e[1]
    ux = (r1 * (m[1] - e[1]) + rm * (e[1] - s[1]) + re_ * (s[1] - m[1])) / d
    uy = (r1 * (e[0] - m[0]) + rm * (s[0] - e[0]) + re_ * (m[0] - s[0])) / d
    r = math.hypot(s[0] - ux, s[1] - uy)
    if not (math.isfinite(ux) and math.isfinite(uy) and math.isfinite(r)) \
            or r > 1e9:
        return [(s, e)]
    tau = 2.0 * math.pi
    a0 = math.atan2(s[1] - uy, s[0] - ux)
    am = math.atan2(m[1] - uy, m[0] - ux)
    a1 = math.atan2(e[1] - uy, e[0] - ux)
    ccw_span = (a1 - a0) % tau
    if ((am - a0) % tau) <= ccw_span:
        span, sign = ccw_span, 1.0      # 逆时针 a0 → a1（含 mid）
    else:
        span, sign = (a0 - a1) % tau, -1.0   # 顺时针 a0 → a1
    k = ARC_TEST_CHORDS
    pts = [s]
    for t in range(1, k):
        ang = a0 + sign * span * (t / k)
        pts.append((ux + r * math.cos(ang), uy + r * math.sin(ang)))
    pts.append(e)
    return list(zip(pts[:-1], pts[1:]))


def _point_in_loop(p, loop):
    """射线法点在环内（含边界视为在内——弧离散 ARC_TEST_CHORDS 弦上判定）。"""
    segs = []
    for edge in loop:
        segs.extend(_edge_test_segments(edge))
    # 边界判定
    for a, b in segs:
        if _on_segment(a, b, p):
            return True
    inside = False
    for a, b in segs:
        if (a[1] > p[1]) != (b[1] > p[1]):
            x = a[0] + (p[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if x > p[0]:
                inside = not inside
    return inside


def _validate_outline_loops(loops):
    """环分类+自交/嵌套校验 → (outer_loop, holes 列表)。

    outer=bbox 面积最大环（平手 ⇒ AdapterError）；其余环须首顶点在 outer 内且
    不含其他环（hole 嵌套 hole ⇒ AdapterError，首版不支持）；同环非相邻边相交
    ⇒ 自交 fail-closed；跨环边相交 ⇒ fail-closed（相邻=链接相邻或首尾闭合对，
    共端点豁免）。"""
    if not loops:
        return None, []
    bboxes = []
    for loop in loops:
        xs, ys = [], []
        for edge in loop:
            for p in (edge[1], edge[-1]):
                xs.append(p[0])
                ys.append(p[1])
        bboxes.append((min(xs), min(ys), max(xs), max(ys)))
    areas = [(b[2] - b[0]) * (b[3] - b[1]) for b in bboxes]
    best = max(areas)
    if areas.count(best) > 1:
        raise AdapterError("bad outline：外环歧义（多环 bbox 面积并列最大 %g）"
                           % best)
    outer_i = areas.index(best)
    outer = loops[outer_i]
    holes = [loops[i] for i in range(len(loops)) if i != outer_i]
    # 逐环自交（相邻豁免）+ 跨环相交
    flat = []
    for li, loop in enumerate(loops):
        for ei, edge in enumerate(loop):
            for seg in _edge_test_segments(edge):
                flat.append((li, ei, seg[0], seg[1]))
    for x in range(len(flat)):
        li, ei, a, b = flat[x]
        for y in range(x + 1, len(flat)):
            lj, ej, c, d = flat[y]
            if li == lj:
                if ei == ej:
                    continue   # 同一边自身的相邻弦（离散构造共享端点）
                n = len(loops[li])
                if (abs(ei - ej) == 1 or (ei == 0 and ej == n - 1)
                        or (ej == 0 and ei == n - 1)):
                    continue
            if _segments_intersect(a, b, c, d):
                raise AdapterError(
                    "bad outline：轮廓自交（环 %d 边 %d 与环 %d 边 %d 相交）——"
                    "与 kicad-cli 同口径 fail-closed" % (li, ei, lj, ej))
    # 孔环：在 outer 内 + 不嵌套
    for hi, hole in enumerate(holes):
        v = hole[0][1]
        if not _point_in_loop(v, outer):
            raise AdapterError("bad outline：孔环 %d 不在外环内（面板化/多板轮廓"
                               "首版不支持——fail-closed）" % hi)
        for hj, other in enumerate(holes):
            if hj != hi and _point_in_loop(other[0][1], hole):
                raise AdapterError("bad outline：孔环嵌套孔环（环 %d 在环 %d 内）"
                                   "——首版不支持 fail-closed" % (hj, hi))
    return outer, holes


def _edge_to_json(edge):
    if edge[0] == "segment":
        return {"type": "segment",
                "start_mm": [edge[1][0], edge[1][1]],
                "end_mm": [edge[2][0], edge[2][1]]}
    return {"type": "arc",
            "start_mm": [edge[1][0], edge[1][1]],
            "mid_mm": [edge[2][0], edge[2][1]],
            "end_mm": [edge[3][0], edge[3][1]]}


def _outline_mm(root, report):
    """root → outline_mm dict（或 None=无 Edge_Cuts 图元，缺省路径零漂移）。

    FA-5d（adapter-fix-r1）：常规链接（容差 0.01mm）开口失败时，端点吸附愈合
    （OUTLINE_HEAL_TOL_MM 簇径，见 _snap_heal_endpoints）后重链；再失败或后续
    自交/嵌套校验不过仍 fail-closed。report 增计 outline_healed_clusters（0=
    未触愈合路径——存量可转板恒 0，结构零漂移）。"""
    edges = _collect_outline_edges(root)
    report["outline_edges"] = len(edges)
    report["outline_arcs"] = sum(1 for e in edges if e[0] == "arc")
    report["outline_healed_clusters"] = 0
    if not edges:
        report["outline_loops"] = 0
        report["outline_holes"] = 0
        return None
    try:
        loops = _chain_loops(edges)
    except AdapterError:
        healed_edges, merged = _snap_heal_endpoints(edges)
        if healed_edges is None:
            raise
        loops = _chain_loops(healed_edges)   # 仍开口 ⇒ 原样 AdapterError（fail-closed）
        report["outline_healed_clusters"] = merged
        report["outline_edges"] = len(healed_edges)
        report["outline_arcs"] = sum(1 for e in healed_edges if e[0] == "arc")
    loops = _dedupe_identical_loops(loops)
    outer, holes = _validate_outline_loops(loops)
    report["outline_loops"] = len(loops)
    report["outline_holes"] = len(holes)
    return {
        "outer": [_edge_to_json(e) for e in outer],
        "holes": [[_edge_to_json(e) for e in hole] for hole in holes],
    }


# ---------------------------------------------------------------- 转换主流程

def _default_hard_rules():
    """引擎缺省不变式地板（每次调用构造新 dict，防调用方突变污染缺省）。"""
    return {
        "R1": {"k_a": 0.4, "floor_mm": 0.3},
        "R2": {"min_distance_mm": 3.0, "max_parallel_mm": 5.0},
        "R3": {"unsplittable": True},
        "R4": {"return_via_required": True, "max_distance_mm": 2.0},
        "R5": {"min_clearance_mm": 0.5},
        "R6": {"plane_forbidden": True, "keepout_zones_forbidden": True},
    }

_DRAWING_HEADS = frozenset({"text", "text_box", "dimension", "group"})


def _count_ignored(root):
    """全树迭代一遍，统计 (ignored_zones, ignored_drawings)。zone 不解析为几何。

    V5-R7 W-3 起 Edge_Cuts 承载的图元=轮廓几何（非装饰，入 outline_mm），
    不再计入 ignored_drawings（换记 outline_* 计数）。"""
    zones = 0
    drawings = 0
    pending = [root]
    while pending:
        node = pending.pop()
        for item in node:
            if type(item) is list and item:
                head = item[0]
                if type(head) is str:
                    if head == "zone":
                        zones += 1
                    elif (head.startswith("gr_") or head.startswith("fp_")
                          or head in _DRAWING_HEADS):
                        if _edge_layer_of(item) == "Edge.Cuts":
                            continue
                        drawings += 1
                pending.append(item)
    return zones, drawings


def _declared_nets(root):
    """kicad_pcb 直接子节点的 (net N "name") 声明 → {num: name}（net 0 除外）。

    同号重复：同名宽容去重、异名 AdapterError；异号同名 AdapterError。
    可能为空：KiCad 10+（version 20260206 语风）取消顶层 net 表，网只以名字出现在
    pad/segment/via 的 (net "name") 引用里（names 模式，由调用方探测）。
    """
    nets = {}
    names = {}
    for item in root[1:]:
        if type(item) is not list or not item or item[0] != "net":
            continue
        if len(item) < 3:
            raise AdapterError("(net %r) 声明缺网名字段" % (item[1] if len(item) > 1 else "?"))
        num = _as_int(item[1], "net 号")
        if num < 0:
            raise AdapterError("net 号为负: %d" % num)
        name = item[2]
        if type(name) is not str:
            raise AdapterError("net %d 网名不是字符串: %r" % (num, name))
        if num == 0:
            continue  # 未连接网，不产出（模块 docstring 已披露）
        if num in nets:
            if nets[num] == name:
                continue
            raise AdapterError("net %d 重复声明且网名冲突: %r vs %r" % (num, nets[num], name))
        if name in names:
            raise AdapterError("网名 %r 重复（net %d 与 net %d）" % (name, names[name], num))
        nets[num] = name
        names[name] = num
    return nets


def _ref_net(item, what, declared, names_mode):
    """track(segment/arc)/via/pad 的 (net …) 引用 → 网名（统一键）；未连接 → None。

    numbered 模式（有顶层 net 表）：(net N) / (net N "name")，N≠0 必须已声明。
    names 模式（KiCad 10+）：(net "name")，空名视为未连接；pad 引用即声明，
    track/via 引用由调用方收集、扫描后统一校验。形态与模式不符 → AdapterError。
    """
    netn = _sub(item, "net")
    if netn is None:
        return None
    if len(netn) < 2 or type(netn[1]) is not str:
        raise AdapterError("%s 的 (net) 节点缺引用或引用不是字符串" % what)
    tok = netn[1]
    if names_mode:
        if len(netn) != 2:
            raise AdapterError("%s 的 (net) 引用为 numbered 形态，与文件的 name-only 网表不符: %r"
                               % (what, tok))
        return tok if tok != "" else None
    if len(netn) > 3:
        raise AdapterError("%s 的 (net) 引用字段过多: %r" % (what, netn[1:]))
    num = _as_int(tok, "%s.net 号" % what)
    if num == 0:
        return None
    if num not in declared:
        raise AdapterError("%s 引用未声明的 net %d（载有 net 的 track 必须有声明）" % (what, num))
    return declared[num]


def _collect_layer_refs(root):
    """铜几何层引用预扫描（FA-5a/5b 引用门控）→ 引用层名集合。

    收 segment/arc 的 (layer) 名、via 的 (layers) token、footprint 内 pad 的
    (layers) token（通配 *.Cu / * 除外——它们不指向具体声明名）。zone/net_class
    等不参与（非铜几何引用）。"""
    refs = set()
    for item in root[1:]:
        if type(item) is not list or not item or type(item[0]) is not str:
            continue
        head = item[0]
        if head in ("segment", "arc"):
            lay = _sub(item, "layer")
            if lay is not None and len(lay) > 1 and type(lay[1]) is str:
                refs.add(lay[1])
        elif head == "via":
            vl = _sub(item, "layers")
            if vl is not None:
                for tok in vl[1:]:
                    if type(tok) is str and not tok.startswith("*"):
                        refs.add(tok)
        elif head in ("module", "footprint"):
            for sub in item[1:]:
                if type(sub) is not list or not sub or sub[0] != "pad":
                    continue
                pl = _sub(sub, "layers")
                if pl is not None:
                    for tok in pl[1:]:
                        if type(tok) is str and not tok.startswith("*"):
                            refs.add(tok)
    return refs


def _convert(data, board_id, source_uri, pro_net_settings=None,
             netclass_mask_binding=None):
    """bytes → (v5.board.v1 板 dict, report dict)；板 dict 过 load_board 后返回。

    pro_net_settings：同 stem .kicad_pro 的 net_settings（convert_file 路径由
    load_pro_net_settings 读取传入；convert_bytes 无路径 ⇒ None=板内源单可达，
    文档化局限）。

    netclass_mask_binding：A1（EXEC-R3 R3-2）同 stem .netclass-mask.json 的
    原料（convert_file 路径由 load_netclass_mask_binding 读取传入；None=不在
    场或无路径，P1..P5 原行为逐字节不变）。在场时经
    _apply_netclass_mask_values 严格归属/内容绑定核验后作**值**权威（R5/类值/
    空类恢复；成员仍取 pro），核验不过 fail-closed。"""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AdapterError("源文件不是合法 UTF-8: %s" % exc) from exc
    root = parse_sexpr(text)

    report = {
        "board_id": board_id,
        "kicad_version": None,
        "net_count": 0,
        "footprint_count": 0,
        "pad_count": 0,
        "netted_pad_count": 0,
        "segment_count": 0,
        "arc_count": 0,
        "via_count": 0,
        "ignored_zones": 0,
        "ignored_drawings": 0,
        "degenerate_partitions": 0,
        "pad_terminal_count": 0,
        "pad_terminal_skipped": 0,
        "holes_pth": 0,
        "holes_npth": 0,
        "holes_oval": 0,
        "drill_oval_single_param": 0,
        "net_class_source": "none",
        "net_class_count": 0,
        "net_class_unassigned_nets": 0,
        "net_class_stale_members": 0,
        "net_class_board_blocks_ignored": 0,
        "outline_edges": 0,
        "outline_arcs": 0,
        "outline_loops": 0,
        "outline_holes": 0,
    }
    version = _sub(root, "version")
    if version is not None and len(version) > 1:
        report["kicad_version"] = version[1]

    # ---- stackup：按 (layers) 块启用的铜层（docstring 已披露顺序与局限；
    #      FA-5a/5b legacy/power 铜层方言支持与引用门控见模块 docstring「方言修复」节）
    layers_node = _sub(root, "layers")
    if layers_node is None:
        raise AdapterError("缺 (layers) 块，无法确定启用铜层")
    layer_refs = _collect_layer_refs(root)
    copper = {}            # 规范层名 -> 声明层号（纯现代板仅键参与排序/成员判定）
    legacy_alias = {}       # 声明名 -> 规范名（FA-5a/5b 翻译面；纯现代板恒空）
    layer_fix_alias = False
    layer_fix_power = False
    v4_numbering = False    # KiCad ≤4 编号（技术层号插在 1..31）⇒ 层号≠物理栈位
    for entry in layers_node[1:]:
        if (type(entry) is not list or len(entry) < 2 or type(entry[0]) is not str
                or type(entry[1]) is not str):
            raise AdapterError("(layers) 条目不可解析: %r" % (entry,))
        num = _as_int(entry[0], "(layers) 层号")
        name = entry[1]
        ttype = entry[2] if len(entry) > 2 and type(entry[2]) is str else None
        copperish = name.endswith(".Cu") or ttype in ("signal", "power", "mixed")
        if not copperish and num <= 31:
            v4_numbering = True
        canon = None
        dialect_name = False
        if name.endswith(".Cu"):
            # 现代命名（*.Cu）：类型 signal/power 均按旧口径收（KiCad 5+ 文件中
            # .Cu 名可带 power 类型——anthc/MINI_ARC 语料实证，不构成方言信号）。
            canon = name
        elif ttype in ("signal", "power", "mixed"):
            # FA-5a/5b legacy 铜层方言（非 *.Cu 名）：仅当被铜几何引用才入栈。
            dialect_name = True
            if name in LEGACY_COPPER_ALIASES:
                canon = LEGACY_COPPER_ALIASES[name]
            elif _LEGACY_INNER_RE.match(name):
                canon = "In%s.Cu" % name[5:]
            elif ttype == "power":
                canon = name          # FA-5b 自定义 power 层名原名保留
            # 其余自定义 signal 名：无映射证据 → 按旧口径忽略（不新增拒收面）
            if canon is not None and name not in layer_refs:
                canon = None          # 引用门控：未被铜几何引用 → 不入栈（零漂移）
        if canon is None:
            continue
        if canon in copper:
            raise AdapterError("(layers) 铜层名重复: %r" % name)
        copper[canon] = num
        if dialect_name:
            legacy_alias[name] = canon
            if canon != name:
                layer_fix_alias = True
            else:
                layer_fix_power = True   # FA-5b power 层原名入栈
    if not copper:
        raise AdapterError("(layers) 块中无启用的铜层（*.Cu）")
    if layer_fix_alias or layer_fix_power:
        if v4_numbering:
            raise AdapterError(
                "(layers) 旧式层号混排（KiCad ≤4 编号：技术层号插在 1..31，层号"
                "≠物理栈位）与 legacy/power 铜层名并存：层序语义未钉，fail-closed"
                " 不静默猜（语料无此形态，出现即拒收）")
        # 方言板：按 layers 块声明的层号排序（KiCad 5+ 编号下层号=物理栈位，
        # 0 F.Cu→…→31 B.Cu；技术层全 ≥32 已由 v4_numbering=False 保证）
        stackup_names = sorted(copper, key=lambda nm: (copper[nm], nm))
    else:
        stackup_names = sorted(copper, key=_cu_order)
    stackup = [{"id": name, "kind": "signal", "preferred_direction": "any",
                "available": True}
               for name in stackup_names]
    layer_set = frozenset(copper)

    # ---- nets：numbered 模式（顶层 net 表）或 names 模式（KiCad 10+，引用即声明）
    declared = _declared_nets(root)
    names_mode = not declared
    net_pads = {}      # 网名 -> [(x, y, pad_terminal|None)]（升级件① 附铜信息）
    used_refs = set()  # names 模式下 track/via/arc 引用的网名（扫描后统一校验）
    via_shapes = collections.Counter()   # (drill, size) → 出现数（via_model 众数）
    holes = []                            # 板固孔清单（V5-D8；源文件出现序）

    # ---- 铜几何遍历（顶层：module/footprint → pad；segment/arc/via）
    bbox = _BBox()
    for item in root[1:]:
        if type(item) is not list or not item or type(item[0]) is not str:
            raise AdapterError("kicad_pcb 顶层出现裸 token: %r" % (item,))
        head = item[0]
        if head == "module" or head == "footprint":
            report["footprint_count"] += 1
            fp_desc = "%s %s" % (head, item[1] if len(item) > 1
                                 and type(item[1]) is str else "?")
            at = _sub(item, "at")
            if at is None:
                raise AdapterError("%s 缺 (at) 位置" % head)
            vals = _floats(at, 2, "%s.at" % head)
            fx, fy = vals[0], vals[1]
            angle = vals[2] if len(vals) > 2 else 0.0
            for sub in item[1:]:
                if type(sub) is not list or not sub or sub[0] != "pad":
                    continue
                report["pad_count"] += 1
                pat = _sub(sub, "at")
                if pat is None:
                    raise AdapterError("pad 缺 (at)（%s @ %s, %s）" % (head, fx, fy))
                pv = _floats(pat, 2, "pad.at")
                size = _sub(sub, "size")
                if size is None:
                    raise AdapterError("pad 缺 (size)（%s @ %s, %s）" % (head, fx, fy))
                sv = _floats(size, 2, "pad.size")
                hw, hh = sv[0] / 2.0, sv[1] / 2.0
                rx, ry = _rotate(pv[0], pv[1], angle)
                ax, ay = fx + rx, fy + ry
                bbox.add(ax - hw, ay - hh, ax + hw, ay + hh)
                # 板固孔收集（V5-D8）：TH/NPTH pad 钻孔绝对坐标入 holes[]（不分网）
                hole, oval1 = _pad_hole(
                    sub, ax, ay,
                    "%s pad %s" % (fp_desc, sub[1] if len(sub) > 1
                                   and type(sub[1]) is str else "?"))
                if hole is not None:
                    holes.append(hole)
                    if hole["plated"]:
                        report["holes_pth"] += 1
                    else:
                        report["holes_npth"] += 1
                    if hole["shape"] == "oval":
                        report["holes_oval"] += 1
                    report["drill_oval_single_param"] += oval1
                name = _ref_net(sub, "pad", declared, names_mode)
                if name is None:
                    continue
                report["netted_pad_count"] += 1
                shape_tok = sub[3] if len(sub) > 3 and type(sub[3]) is str else ""
                terminal = _pad_terminal(sub, shape_tok, sv, angle, layer_set,
                                         legacy_alias)
                net_pads.setdefault(name, []).append((ax, ay, terminal))
        elif head == "segment":
            report["segment_count"] += 1
            s = _sub(item, "start")
            e = _sub(item, "end")
            w = _sub(item, "width")
            lay = _sub(item, "layer")
            if s is None or e is None or w is None or lay is None:
                raise AdapterError("segment 缺 start/end/width/layer 字段")
            sv = _floats(s, 2, "segment.start")
            ev = _floats(e, 2, "segment.end")
            hw = _floats(w, 1, "segment.width")[0] / 2.0
            if len(lay) < 2 or type(lay[1]) is not str:
                raise AdapterError("segment 缺层名")
            lay_name = legacy_alias.get(lay[1], lay[1])
            if lay_name not in layer_set:
                raise AdapterError("segment 层 %r 不在启用铜层中" % lay[1])
            bbox.add(min(sv[0], ev[0]) - hw, min(sv[1], ev[1]) - hw,
                     max(sv[0], ev[0]) + hw, max(sv[1], ev[1]) + hw)
            name = _ref_net(item, "segment", declared, names_mode)
            if name is not None and names_mode:
                used_refs.add(name)
        elif head == "arc":
            report["arc_count"] += 1
            s = _sub(item, "start")
            m = _sub(item, "mid")
            e = _sub(item, "end")
            w = _sub(item, "width")
            lay = _sub(item, "layer")
            if s is None or m is None or e is None or w is None or lay is None:
                raise AdapterError("arc 缺 start/mid/end/width/layer 字段")
            sv = _floats(s, 2, "arc.start")
            mv = _floats(m, 2, "arc.mid")
            ev = _floats(e, 2, "arc.end")
            hw = _floats(w, 1, "arc.width")[0] / 2.0
            if len(lay) < 2 or type(lay[1]) is not str:
                raise AdapterError("arc 缺层名")
            lay_name = legacy_alias.get(lay[1], lay[1])
            if lay_name not in layer_set:
                raise AdapterError("arc 层 %r 不在启用铜层中" % lay[1])
            _arc_bbox(bbox, sv[0], sv[1], mv[0], mv[1], ev[0], ev[1], hw)
            name = _ref_net(item, "arc", declared, names_mode)
            if name is not None and names_mode:
                used_refs.add(name)
        elif head == "via":
            report["via_count"] += 1
            at = _sub(item, "at")
            size = _sub(item, "size")
            if at is None or size is None:
                raise AdapterError("via 缺 (at)/(size)")
            av = _floats(at, 2, "via.at")
            sz = _floats(size, 1, "via.size")[0] / 2.0
            bbox.add(av[0] - sz, av[1] - sz, av[0] + sz, av[1] + sz)
            drill_node = _sub(item, "drill")
            if drill_node is not None and len(drill_node) > 1 and \
                    type(drill_node[1]) is str:
                try:
                    dv = float(drill_node[1])
                except ValueError:
                    dv = -1.0
                if math.isfinite(dv) and dv > 0.0 and sz * 2.0 > 0.0:
                    via_shapes[(dv, sz * 2.0)] += 1
            vl = _sub(item, "layers")
            if vl is not None:
                for tok in vl[1:]:
                    if type(tok) is str and \
                            legacy_alias.get(tok, tok) not in layer_set:
                        raise AdapterError("via 层 %r 不在启用铜层中" % tok)
            name = _ref_net(item, "via", declared, names_mode)
            if name is not None and names_mode:
                used_refs.add(name)

    if bbox.empty:
        raise AdapterError("文件中无任何 pad/track/via 铜几何，工作区无法确定")

    # ---- 网序（确定性）：numbered 按网号升序；names 按名字典序
    if names_mode:
        for name in sorted(used_refs):
            if name not in net_pads:
                raise AdapterError("net %r 仅有 track/via 引用而无任何 pad，无法生成分区端点"
                                   % name)
        net_order = sorted(net_pads)
    else:
        net_order = [declared[num] for num in sorted(declared)]
    if not net_order:
        raise AdapterError("未发现任何 net（net 0 / 空名除外），无法产出分区")

    # ---- 分区：每网一个（V5-R1 W-2：全 pad 质心集——多 pad 网不再折叠 2 端，
    #      端点序=源文件出现序（footprint 遍历序 × footprint 内 pad 序，同 holes
    #      口径；同坐标 pad 折叠为单端点）+ W-3 显式 Steiner 拓扑落键）
    used_ids = set()
    partitions = []
    nets_out = []
    topology = {}
    topo_stats = {"multi_terminal_nets": 0, "steiner_points": 0,
                  "decomposed_nets": 0, "mst_fallback_nets": 0}
    for name in net_order:
        pads = net_pads.get(name, [])
        if not pads:
            raise AdapterError("net %r 无任何 pad，无法生成分区端点（策略：fail-closed）"
                               % name)
        # 质心集：pad 中心绝对坐标，出现序去重（同点折叠=共享端点索引）
        idx_of = {}
        pts = []
        for (px, py, _t) in pads:
            key = (px, py)
            if key not in idx_of:
                idx_of[key] = len(pts)
                pts.append(key)
        if len(pts) == 1:
            # 单点退化合同（升级件④沿用）：两端重合的两点（executor trivially
            # satisfied；topology 零边）
            endpoints = [[pts[0][0], pts[0][1]], [pts[0][0], pts[0][1]]]
            report["degenerate_partitions"] += 1
        else:
            endpoints = [[float(x), float(y)] for (x, y) in pts]
        pid = _unique_partition_id("PT-" + sanitize_net_id(name), used_ids)
        if len(pads) >= 2:
            note = "adapter: %d pads -> %d terminal nodes (R1 explicit topology)" \
                % (len(pads), len(pts))
        else:
            note = "adapter: 1 pad abstracted to 2 coincident endpoints (degenerate)"
        geo = {"endpoints": endpoints}
        # 端点焊盘铜落键（D1→R1 逐 pad 化）：每 pad 一项，endpoint=该 pad 质心
        # 在 endpoints 中的索引（同质心多 pad=多项共享索引，物理铜并集语义；
        # 消费侧 extent=max(size)/层集=union 天然兼容）
        items = []
        for (px, py, terminal) in pads:
            if terminal is None:
                report["pad_terminal_skipped"] += 1
                continue
            item = dict(terminal)
            item["endpoint"] = idx_of[(px, py)]
            items.append(item)
            report["pad_terminal_count"] += 1
        if items:
            geo["pad_terminals"] = items
        partitions.append({
            "partition_id": pid,
            "ptype": classify_ptype(name),
            "geometry": geo,
            "layer_policy": "any",
            "width_prior": dict(DEFAULT_WIDTH_PRIOR),
            "current_a": 0,
            "speed_class": "unknown",
            "note": note,
        })
        nets_out.append({"net_id": name, "partitions": [pid]})
        # W-3：显式 Steiner 拓扑（W-1 FLUTE 查表形态；nodes=端点（endpoints 序）
        # 在前+分支点（字典序）在后；退化网零边）
        topo = steiner.steiner_topology([tuple(p) for p in pts])
        topology[pid] = {
            "nodes": topo["nodes"],
            "edges": topo["edges"],
            "terminal_count": topo["terminal_count"],
            "total_mm": round(topo["total_mm"], 10),
            "provenance": {"algorithm": topo["algorithm"],
                           "method": topo["method"]},
        }
        if len(pts) > 2:
            topo_stats["multi_terminal_nets"] += 1
        if topo["method"] == "decomposed":
            topo_stats["decomposed_nets"] += 1
        if topo["method"] == "mst-fallback":
            topo_stats["mst_fallback_nets"] += 1
        topo_stats["steiner_points"] += len(topo["nodes"]) - topo["terminal_count"]
    report["net_count"] = len(net_order)
    report["topology"] = dict(topo_stats)

    # ---- via_model（D2）：真实孔径众数（平手取 (drill, size) 字典序最小）
    via_model = None
    if via_shapes:
        best = min(via_shapes.items(),
                   key=lambda kv: (-kv[1], kv[0]))
        drill, size = best[0]
        via_model = {"drill_mm": drill,
                     "annular_mm": max(0.0, (size - drill) / 2.0)}

    # ---- net class（V5-R7 W-1：双源合并，优先序 P1..P5 钉值于 probe_priority.py）
    known_nets = set(net_order)
    net_classes, r5_default = _emit_net_classes(pro_net_settings, root,
                                                known_nets, report)
    if netclass_mask_binding is not None:
        net_classes, r5_default = _apply_netclass_mask_values(
            netclass_mask_binding, data, root, pro_net_settings,
            net_classes, r5_default, report)

    # ---- 真实板轮廓（V5-R7 W-3：Edge_Cuts；无图元 → None=缺省路径零漂移）
    outline = _outline_mm(root, report)

    # ---- 组装板 dict（zones=[] / principle_registry=[]：v0.1.0 局限，docstring 已披露）
    hard_rules = _default_hard_rules()
    if r5_default is not None:
        hard_rules["R5"] = {"min_clearance_mm": r5_default}
    board = {
        "schema_version": "v5.board.v1",
        "board_id": board_id,
        "stackup": stackup,
        "workspace": {
            "x_min": bbox.x0 - WORKSPACE_MARGIN_MM,
            "y_min": bbox.y0 - WORKSPACE_MARGIN_MM,
            "x_max": bbox.x1 + WORKSPACE_MARGIN_MM,
            "y_max": bbox.y1 + WORKSPACE_MARGIN_MM,
        },
        "zones": [],
        "partitions": partitions,
        "nets": nets_out,
        "hard_rules": hard_rules,
        "principle_registry": [],
        "holes": holes,   # V5-D8：恒落键（含空数组；真实板=全板 TH/NPTH 钻孔清单）
        "topology": topology,   # V5-R1 W-3：per-partition 显式 Steiner 拓扑
    }
    if net_classes:
        board["net_classes"] = net_classes   # V5-R7 W-1：仅非 Default 类
    if outline is not None:
        board["outline_mm"] = outline        # V5-R7 W-3：真实板轮廓
    if via_model is not None:
        board["via_model"] = via_model
    # ---- 方言修复谱系（adapter-fix-r1）：激活族清单入 report；provenance.adapter
    #      双版本串——未触方言路径=v0.5.0 原串（存量板逐字节零漂移），激活任一族
    #      =v0.6.0（谱系诚实；见模块 docstring「方言修复」节）。
    dialect_fixes = []
    if layer_fix_alias:
        dialect_fixes.append("legacy_copper_alias")
    if layer_fix_power:
        dialect_fixes.append("power_copper_layer")
    if report["drill_oval_single_param"]:
        dialect_fixes.append("drill_oval_single_param")
    if report["outline_healed_clusters"]:
        dialect_fixes.append("outline_snap_heal")
    report["adapter_dialect_fixes"] = dialect_fixes
    adapter_name = ADAPTER_NAME if dialect_fixes else ADAPTER_NAME_V050
    prov = {
        "source_type": "kicad_pcb",
        "source_uri": source_uri,
        "source_sha256": canonical.sha256_bytes(data),
        "adapter": adapter_name,
        "board_sha256": "",
    }
    board["provenance"] = prov
    prov["board_sha256"] = compute_board_sha256(board)  # 复算时剔除本字段自身

    zones_n, drawings_n = _count_ignored(root)
    report["ignored_zones"] = zones_n
    report["ignored_drawings"] = drawings_n

    load_board(board)  # schema + 跨字段 + 哈希链，fail-closed
    return board, report


# ---------------------------------------------------------------- 公开入口

def convert_bytes(data, board_id, source_uri):
    """KiCad 源 bytes → v5.board.v1 板 dict（已过 v5.board.load_board 校验）。

    source_sha256 = sha256(data 原始 bytes)；source_uri 由调用方给定。
    """
    return _convert(data, board_id, source_uri)[0]


def convert_bytes_with_report(data, board_id, source_uri):
    """同 convert_bytes，另返回 report dict（含 ignored_zones 等计数）。"""
    return _convert(data, board_id, source_uri)


def convert_file(pcb_path, board_id):
    """KiCad .kicad_pcb 文件 → v5.board.v1 板 dict（已过 load_board 校验）。

    source_uri = 绝对路径（os.path.abspath，反斜杠规范为正斜杠）。
    同 stem .kicad_pro 存在时自动读取 net_settings（W-1 双源优先序 P1）。
    A1（EXEC-R3 R3-2）：同 stem .netclass-mask.json 在场时经严格归属/内容
    绑定核验后作值权威（load_netclass_mask_binding；不在场=真实板路径，
    行为逐字节不变；核验不过 fail-closed 不静默）。"""
    with open(pcb_path, "rb") as f:
        data = f.read()
    uri = os.path.abspath(pcb_path).replace("\\", "/")
    return _convert(data, board_id, uri,
                    pro_net_settings=load_pro_net_settings(pcb_path),
                    netclass_mask_binding=load_netclass_mask_binding(
                        pcb_path, data))[0]


def convert_file_with_report(pcb_path, board_id):
    """同 convert_file，返回 (board, report)。"""
    with open(pcb_path, "rb") as f:
        data = f.read()
    uri = os.path.abspath(pcb_path).replace("\\", "/")
    return _convert(data, board_id, uri,
                    pro_net_settings=load_pro_net_settings(pcb_path),
                    netclass_mask_binding=load_netclass_mask_binding(
                        pcb_path, data))
