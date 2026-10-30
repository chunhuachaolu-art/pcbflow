# -*- coding: utf-8 -*-
"""v5.routes.v1 routes 判定编排（V5.0-DEV-TASKBOOK P4/L7 交付；A9 内源单源消费方）。

职责：对 L7 执行器产出的 routes 工件做**全量可复核判定**——
  routes + 板内固定铜 → Copper 场景 → v5.drc check_all（R5/R2/capacity/R1）
  + R6 逐段精查 + R4 回流孔配对结构对账 → {"feasible": bool, "violations": [...]}。

口径同源声明（任务书 P4 第⑤路任务书条款）：本模块的 _BoardView/_fixed_coppers/
_run_drc/_candidate_attribution/_capacity_checks 与 v5/selection.py **同型同源**
（逐条镜像其语义，候选铜前缀 "cand:" 对应本模块 "route:"）。**不改 v5/selection.py**，
两处同型构造并存、披露即可（任务书明示）。

判定编排（全部出自 v5.drc，无旁路几何实现）：
- R5/R2/capacity/R1 走 check_all 聚合；R6（禁布区 + plane 层）用 check_keepout 对
  **逐段分解铜**精查（check_keepout 的整线 bbox 形态对绕行走线过保守，逐段 bbox
  消除伪影——与 selection._run_drc 同一处置）；对角段 bbox 仍偏保守（保守方向 =
  误杀不漏放，fail-closed）。
- 容量核算独立可复核：逐（走廊 × 信号层）条目化（复用 v5.metrics.capacity 公共件），
  固定铜按声明占用（geometry.occupancy_mm）或计划宽、routes 铜按路线宽；条目序 =
  固定铜（板注册序）在前、routes 铜（工件 entry 序）在后；返回 capacity_meta
  （terms/capacity_mm）供独立复算算术。
- R1 宽度核查：被布线且 current_a>0 的分区，取该分区 routes 宽度（执行器实际落铜宽）
  对照保守下限（v5.metrics.width_prior.conservative_min_width），判定经 v5.drc.check_width。
  （selection 口径查分区 planned_width 属性；routes 场景的落铜宽是执行器的宽度决定，
  查工件宽度才是查实际铜——口径适配，判定语义仍唯一出自 v5.drc。）

归责口径（镜像 selection._candidate_attribution，候选铜→路线铜）：
- capacity/R1 恒归责 routes（走廊占用/宽度由布线选择触发——selection 同款语义）；
- 其余规则按违例主体是否含 "route:" 前缀判定；
- 固定铜互扰（双 fixed）= 板内固有缺陷，不归责 routes；
- **同分区豁免（最小文档化决定，本文披露）**：v5.board.v1 允许两个网指向同一分区
  （DIFF 对、BUS ribbon），分区端点只有一对——两条 route 折线在共享端点处必然接触
  （gap=0），pad 级分离在板合同里不可表达。故 R5 过滤「同 partition_id 的两条
  route 铜」对（gap 事实仍由 v5.drc 计算，过滤是归责层处置，docstring 披露 +
  专项测试锚定）；执行器侧 A* 仍强制对腿间距 ≥ R5（见 executor），物理分离不放松。

R4 结构对账（披露）：v5.drc 无 R4 判定器（check_all 只含 R5/R2/R6/capacity/R1）。
回流孔配对（每个过渡孔 ≤ max_distance_mm 内有配对回流孔）在本模块做**结构对账**
（violation rule="R4"，data.audit="structural"），非几何 DRC 判定、不冒充 v5.drc。

ribbon / 既布分区去重（最小文档化决定，本文披露）：板上带 geometry.copper_band 的
分区（ribbon）与 ptype=="ROUTED" 的既布分区，其铜已由 _fixed_coppers 进场景；routes
中这些分区的 entry 是**同一物理铜的声明**，不再重复构造 route 铜（避免容量双计）。
声明与板数据的一致性（中心线/宽度相符）以 violation rule="structure" 核对。

焊盘/过孔物理铜入模（升级件① 2026-09-14，D1/D2；route_check 场景侧）：
- **焊盘铜=固定铜**（D1，同 ribbon/fixed 先例）：分区 geometry.pad_terminals
  （adapter 从真实 .kicad_pcb 落键）逐项入场景（circle→圆铜 / rect→轴对齐
  矩形铜；layers "all"=全部信号层、列表=逐层一枚），每引用网一枚×每层一枚，
  归一口 kicad_export.partition_pads。**隐式 anchor（无 pad_terminals 的合成
  板端子抽象）不入 v5 场景**——导出器按该网 route entry 层落画（跟随路线，
  见 kicad_export docstring）；合成板端点邻域常有既布铜贴行（demo-01 族 P3
  端点距 P9 铜带 0.1mm），抽象铜入障碍会把端点封死（文档化决定）。焊盘铜
  参与 R5/R6 场景但**不入容量**（端子是连接点不是布线占用；ribbon 声明占用
  已含端部——若入容量则端点在走廊口的板成双计）。
- **过孔铜=圆铜**（D2）：routes 工件每个 transition/return 孔位（同网同点
  去重=物理一孔）在每个信号层入一枚圆铜（半径=drill/2+annular，板
  via_model 缺省 0.3——kicad_export.via_model_params 唯一推导口），逐对与
  线/孔/焊盘算 R5；同网对豁免同折线（same_net_exempt）。
- **同分区豁免扩展（本文披露）**：R5 对的两侧主体若属同一分区（route 铜
  ↔route 铜、route 铜↔该分区焊盘铜、焊盘铜↔焊盘铜）一律过滤——多网共
  分区（DIFF 对/BUS 带）的端点焊盘几何重合是板抽象的固有影子（分区端点
  只有一对），过滤在归责层、gap 事实仍由 v5.drc 计算（与④前既有的
  route↔route 同分区豁免同款语义，范围扩到焊盘铜）。
- 跨层铜对 R5 天然跳过（_actual_gap 层间返回 None）；多层焊盘逐层一枚
  铜即「层跨」的世界表达。

validate_routes：v5.routes.v1 工件 fail-closed 校验（键路径化报错；无独立 schema 文件——
本任务只准新建 3 个文件，故以代码内校验器承担 schema 职责，键路径逐条报出）。
多段表示合同（最小文档化决定）：换层网 = 同 (net_id) 多条 entry（每层一段 run），
首 entry 首点 = 分区端点之一、末 entry 末点 = 另一端点；相邻 entry 在过渡孔点衔接
（该点同在两条 entry 的 transition_vias 中披露）。单段网 = 单 entry，首末点即分区端点。

 零长 polyline 接受缝（升级件④ 2026-09-14，本件唯一改动点；route_check 其余逻辑
 一行未动）：两端点重合的退化分区（adapter 对单 pad 网的既定抽象）= trivially
 satisfied——executor 产出零长 route 条目（polyline=[pt,pt]），validate_routes 链
 审计天然通过（首末点均为退化端点；非退化分区的零长 entry 仍被链审计拒绝）；
 build_scene 对零长 polyline **不构造 route 铜**（零铜展宽 = 无间距交互：不参与
 R5/R2/R6 场景、不入容量条目、不触发 R1 宽度核算——零铜即无载流截面），条目仅作
 工件声明。与升级件①（焊盘物理铜入模）的边界：本缝不建模焊盘铜。

 板边禁布带自查（P5⑥ D6-3 2026-09-17）：check_routes 结果新增恒在场键
 edge_violations（判定出自 v5.drc.check_edge_clearance 单源；带值=kicad-cli
 生效缺省 copper_edge_clearance 0.2mm 常量，board.json 无显式边距字段——考证
 见 drc.py；轮廓唯一源=workspace 矩形）。元素 {"net_id","pos"}，披露通道不入
 feasible/归责：执行侧拒布在 executor 障碍栅格（同一带同源），检查侧只如实
 记铜（含板数据固定铜/焊盘贴边——板内固有态不归责 routes 的既有纪律），
 kicad copper_edge_clearance 残差由 D6-4 分类器按同位归责（匹配容差在消费侧
 tools/run_p5_board.py 的 SHARED_PT_TOL_MM）。0.2.0→0.3.0。
"""
import math

from . import board as board_mod
from .drc import VERSION as DRC_VERSION
from .drc import Copper, check_all, check_edge_clearance, check_keepout
from .kicad_export import ANCHOR_PAD_SIZE_MM, partition_pads, via_model_params
from .metrics import capacity as cap_mod
from .metrics import clearance
from .metrics import width_prior as wp

ROUTE_CHECK_VERSION = "v5.route_check/0.3.0"   # 0.3.0=P5⑥ D6-3：edge_violations
                                               # 板边距自查键（0.2.0=P4 首版）
ROUTES_SCHEMA_VERSION = "v5.routes.v1"
ROUTE_CID_PREFIX = "route:"
FIXED_CID_PREFIX = "fixed:"
# 工件顶层附加键（合同允许的披露键；其余一律拒）
EXTRA_TOP_KEYS = ("ribbon_groups", "fixed_partitions", "pour_regions")
# 单条 route entry 允许的键（合同逐字；多一键拒）
ENTRY_KEYS = ("partition_id", "net_id", "layer", "polyline", "width",
              "transition_vias", "return_vias")
_HEX = "0123456789abcdef"
_SHA256_LEN = 64


class RouteCheckError(ValueError):
    """routes 工件 fail-closed 校验错误；message 含键路径。"""


# ---------------------------------------------------------------- 板视图（只读；
# 与 v5/selection.py 同型同源，见模块 docstring）

def _zone_rect(zone):
    """zone.rect 归一为 (x0, y0, x1, y1)。"""
    rect = zone["rect"]
    if isinstance(rect, dict):
        return (float(rect["x_min"]), float(rect["y_min"]),
                float(rect["x_max"]), float(rect["y_max"]))
    return (float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3]))


class _BoardView:
    """板的确定性只读视图（与 selection._BoardView 同型；L0 已 fail-closed 校验）。"""

    def __init__(self, board):
        self.board = board
        self.board_id = board["board_id"]
        self.provenance = board.get("provenance", {})
        self.board_sha256 = board_mod.compute_board_sha256(board)
        self.partitions = {p["partition_id"]: p for p in board.get("partitions", [])}
        self.partition_order = [p["partition_id"] for p in board.get("partitions", [])]
        self.net_of = {}
        self.nets_by_partition = {}
        for net in board.get("nets", []):
            for pid in net.get("partitions", []):
                self.net_of[pid] = net["net_id"]      # 与 selection 同口径（末写胜）
                self.nets_by_partition.setdefault(pid, []).append(net["net_id"])
        self.layers = {l["id"]: l for l in board.get("stackup", [])}
        self.layer_directions = {lid: l.get("preferred_direction", "any")
                                 for lid, l in self.layers.items()}
        self.signal_layers = [l["id"] for l in board.get("stackup", [])
                              if l.get("kind") == "signal" and l.get("available") is True]
        self.plane_layers = tuple(sorted(
            lid for lid, l in self.layers.items() if l.get("kind") == "plane"))
        zones = board.get("zones", [])
        self.keepouts = [(z["zone_id"], _zone_rect(z))
                         for z in zones if z.get("kind") == "keepout"]
        self.sensitives = [(z["zone_id"], z["rect"])
                           for z in zones if z.get("kind") == "sensitive"]
        # 敏感区矩形 dict 归一（R2 热路径用；列表形式 rect 归一为 dict）
        self.sensitive_rect_ds = []
        for _zid, rect in self.sensitives:
            if isinstance(rect, dict):
                self.sensitive_rect_ds.append({
                    "x_min": float(rect["x_min"]), "y_min": float(rect["y_min"]),
                    "x_max": float(rect["x_max"]), "y_max": float(rect["y_max"])})
            else:
                self.sensitive_rect_ds.append({
                    "x_min": float(rect[0]), "y_min": float(rect[1]),
                    "x_max": float(rect[2]), "y_max": float(rect[3])})
        self.corridors = [z for z in zones if z.get("kind") == "corridor"]
        self.hard_rules = board.get("hard_rules", {})
        ws = board.get("workspace", {})
        self.workspace = (float(ws["x_min"]), float(ws["y_min"]),
                          float(ws["x_max"]), float(ws["y_max"]))
        # ---- 升级件①：端点焊盘归一（**显式 pad_terminals 才入世界模型**）
        # 隐式 anchor 是导出器的端子抽象（kicad_export.partition_pads 按
        # 该网 route entry 层落画），不进 v5 场景、不设端点层约束——合成板
        # （demo/V2 族）端点邻域常有既布铜贴行（如 demo-01 族 P3 端点距 P9
        # 铜带 0.1mm），抽象 anchor 入障碍会把端点封死；真实焊盘铜（adapter
        # 落键）恒入场景与约束。partition_pads 的语义校验 fail-closed
        # （ExportError=ValueError 子类，以 RouteCheckError 面世）。
        self.first_signal_layer = self.signal_layers[0] if self.signal_layers \
            else None
        all_signal = [l["id"] for l in board.get("stackup", [])
                      if l.get("kind") == "signal"]
        self.pad_items = {}        # pid -> 显式 pad_terminals 归一列表
        self.implicit_pads = {}    # pid -> bool（无 pad_terminals=隐式抽象）
        for pid, p in self.partitions.items():
            geo = p.get("geometry") or {}
            if geo.get("pad_terminals") is None:
                self.pad_items[pid] = []
                self.implicit_pads[pid] = True
                continue
            try:
                items = partition_pads(p, self.first_signal_layer, all_signal)
            except ValueError as exc:
                _fail("partitions.%s.geometry.pad_terminals" % pid, str(exc))
            self.pad_items[pid] = items
            self.implicit_pads[pid] = False
        # 端点层集合（executor 端点层约束用）：显式项的层并集；无显式项 →
        # None（不约束——隐式 anchor 随 route 层走，见 kicad_export）。
        self.endpoint_pad_layers = {}
        for pid, items in self.pad_items.items():
            sets = [set(), set()]
            for item in items:
                sets[item["endpoint"]].update(item["pad_layers"])
            self.endpoint_pad_layers[pid] = tuple(s or None for s in sets)
        try:
            self.via_radius = via_model_params(board)["radius"]
        except ValueError as exc:
            _fail("via_model", str(exc))

    def ribbon_partition(self, pid):
        """分区是否 ribbon（带 copper_band 声明）。"""
        geo = (self.partitions.get(pid) or {}).get("geometry") or {}
        return geo.get("copper_band") is not None

    def fixed_partition(self, pid):
        """分区是否既布（ptype=="ROUTED"，路径固定）。"""
        return (self.partitions.get(pid) or {}).get("ptype") == "ROUTED"


class _PadCopper(Copper):
    """端点焊盘铜（D1 固定铜；partition_id 供同分区豁免、is_pad_terminal 供
    容量排除——焊盘是端子不是布线占用）。"""

    def __init__(self, net_id, cid, layer, partition_id, shape, size, center):
        if shape == "circle":
            Copper.__init__(self, net_id, cid, layer,
                            pad=((float(center[0]), float(center[1])),
                                 float(size[0]) / 2.0))
        else:
            hw, hh = float(size[0]) / 2.0, float(size[1]) / 2.0
            cx, cy = float(center[0]), float(center[1])
            Copper.__init__(self, net_id, cid, layer,
                            band=(cx - hw, cy - hh, cx + hw, cy + hh))
        self.partition_id = partition_id
        self.is_pad_terminal = True


class _ViaCopper(Copper):
    """过孔铜（D2：孔位×每信号层一枚圆铜，半径=drill/2+annular）；
    partition_id 供同分区豁免、is_via 供披露。"""

    def __init__(self, net_id, cid, layer, partition_id, center, radius):
        Copper.__init__(self, net_id, cid, layer,
                        pad=((float(center[0]), float(center[1])),
                             float(radius)))
        self.partition_id = partition_id
        self.is_via = True


def _pad_scene_items(view):
    """端点焊盘铜的入场景决定（模块 docstring「焊盘/过孔物理铜入模」节）：
    **仅显式 pad_terminals 入场景**（真实焊盘=真铜，每引用网一枚×每层一枚）；
    隐式 anchor（无 pad_terminals）不入——导出器按该网 route entry 层落画
    （跟随路线的端子抽象，kicad_export.partition_pads），v5 场景无此铜。
    返回 pads=[(pid, net_id, item_idx, item, center)]。"""
    pads = []
    for pid in view.partition_order:
        if view.implicit_pads[pid]:
            continue
        p = view.partitions[pid]
        eps = p["geometry"]["endpoints"]
        for k, item in enumerate(view.pad_items[pid]):
            for net_id in view.nets_by_partition.get(pid, []):
                pads.append((pid, net_id, k, item, eps[item["endpoint"]]))
    return pads


def _fixed_coppers(view):
    """板内固定铜（与 selection._fixed_coppers 同型同源 + 升级件① 焊盘铜）：
    ROUTED 既布折线 + copper_band ribbon 铜带 + 端点焊盘铜（D1，入场景决定见
    _pad_scene_items）。返回 (coppers, declared_occupancy)。"""
    coppers = []
    declared = {}
    for pid in view.partition_order:
        p = view.partitions[pid]
        geo = p.get("geometry") or {}
        layer = p.get("layer_policy")
        net = view.net_of.get(pid, pid)
        half = float(p.get("planned_width", 0.2)) / 2.0
        band = geo.get("copper_band")
        if band:
            (x0, y0), (x1, y1) = geo["endpoints"][0], geo["endpoints"][1]
            lo, hi = sorted((float(band[0]), float(band[1])))
            if abs(float(x1) - float(x0)) <= clearance.EPS:
                rect = (lo, min(float(y0), float(y1)), hi, max(float(y0), float(y1)))
            else:
                rect = (min(float(x0), float(x1)), lo, max(float(x0), float(x1)), hi)
            coppers.append(Copper(net, FIXED_CID_PREFIX + pid, layer,
                                  band=rect, half_width=half))
            if geo.get("occupancy_mm") is not None:
                declared[FIXED_CID_PREFIX + pid] = float(geo["occupancy_mm"])
        elif p.get("ptype") == "ROUTED" and geo.get("endpoints"):
            pts = [[float(pt[0]), float(pt[1])] for pt in geo["endpoints"]]
            coppers.append(Copper(net, FIXED_CID_PREFIX + pid, layer,
                                  polyline=pts, half_width=half))
    pads = _pad_scene_items(view)
    for pid, net_id, k, item, center in pads:
        for lay in item["pad_layers"]:
            coppers.append(_PadCopper(
                net_id, "%spad:%s:%s:e%d#%d" % (FIXED_CID_PREFIX, pid, net_id,
                                                item["endpoint"], k),
                lay, pid, item["shape"], item["size"], center))
    return coppers, declared


# ---------------------------------------------------------------- 场景/容量/宽度

def _copper_in_rect(cu, rect_d):
    """铜几何是否进入矩形（间隙 ≤ EPS；与 selection._copper_in_rect 同型）。"""
    if cu.band is not None:
        return clearance.rect_rect_gap(cu.band, (rect_d["x_min"], rect_d["y_min"],
                                                 rect_d["x_max"], rect_d["y_max"])) \
            <= clearance.EPS
    if cu.pad is not None:
        return clearance.pad_rect_distance(cu.pad[0], cu.pad[1], rect_d) <= clearance.EPS
    return min(clearance.segment_rect_distance(a, b, rect_d)
               for a, b in clearance.polyline(cu.polyline)) <= clearance.EPS


def _routing_coppers(coppers):
    """容量核算铜（升级件①）：焊盘端子不入容量（docstring「不入容量」披露）。"""
    return [cu for cu in coppers
            if not getattr(cu, "is_pad_terminal", False)]


def capacity_ledger(view, coppers, declared):
    """逐（走廊×信号层）初始占用条目（镜像 selection._capacity_checks 的场景侧）。

    返回 {corridor_layer_id: {"entries": [CapacityEntry], "capacity_mm": c}}，
    供执行器容量账本与 check_routes 共用（本工程内单源）。
    """
    ledger = {}
    coppers = _routing_coppers(coppers)
    for zone in view.corridors:
        rect = _zone_rect(zone)
        rect_d = {"x_min": rect[0], "y_min": rect[1], "x_max": rect[2], "y_max": rect[3]}
        cap = float(zone["capacity"])
        by_layer = {}
        for cu in coppers:
            info = view.layers.get(cu.layer)
            if info is None or info.get("kind") != "signal":
                continue
            if _copper_in_rect(cu, rect_d):
                by_layer.setdefault(cu.layer, []).append(cu)
        for layer in sorted(by_layer):
            entries = [cap_mod.CapacityEntry(
                cu.net_id, cu.half_width * 2.0, declared_occupancy=declared.get(cu.cid))
                for cu in by_layer[layer]]
            ledger["%s/%s" % (zone["zone_id"], layer)] = {
                "entries": entries, "capacity_mm": cap}
    return ledger


def _capacity_checks(view, route_coppers, fixed_coppers, declared):
    """逐（走廊×信号层）占用核算（镜像 selection._capacity_checks，条目序确定性）。

    返回 (checks, meta)；checks=[(corridor_layer_id, occupancy, capacity)]，
    meta[corridor_layer_id]={"terms": [...], "capacity_mm": c}（独立复算用）。
    """
    checks, meta = [], {}
    for zone in view.corridors:
        rect = _zone_rect(zone)
        rect_d = {"x_min": rect[0], "y_min": rect[1], "x_max": rect[2], "y_max": rect[3]}
        cap = float(zone["capacity"])
        by_layer = {}
        for cu in _routing_coppers(list(route_coppers) + list(fixed_coppers)):
            info = view.layers.get(cu.layer)
            if info is None or info.get("kind") != "signal":
                continue
            if _copper_in_rect(cu, rect_d):
                by_layer.setdefault(cu.layer, []).append(cu)
        for layer in sorted(by_layer):
            group = by_layer[layer]
            fixed_part = [cu for cu in group if cu.cid.startswith(FIXED_CID_PREFIX)]
            route_part = [cu for cu in group if not cu.cid.startswith(FIXED_CID_PREFIX)]
            entries = []
            for cu in fixed_part + route_part:   # 条目序 = 板注册序在前，routes 按 entry 序
                entries.append(cap_mod.CapacityEntry(
                    cu.net_id, cu.half_width * 2.0,
                    declared_occupancy=declared.get(cu.cid)))
            occ = cap_mod.corridor_occupancy(entries)
            clid = "%s/%s" % (zone["zone_id"], layer)
            checks.append((clid, occ, cap))
            meta[clid] = {"terms": [float(e.occupancy) for e in entries],
                          "capacity_mm": cap}
    return checks, meta


def _width_checks(view, route_coppers):
    """被布线且有电流分区的 R1 宽度核算（镜像 selection._width_checks，宽度源=routes）。"""
    checks, meta = [], {}
    r1 = view.hard_rules.get("R1", {})
    seen = set()
    for cu in route_coppers:
        pid = cu.partition_id
        if pid in seen:
            continue
        seen.add(pid)
        p = view.partitions.get(pid) or {}
        cur = float(p.get("current_a") or 0.0)
        if cur <= 0:
            continue
        required = wp.conservative_min_width(
            cur, fab_min_mm=0.0,
            k_per_amp=float(r1.get("k_a", wp.DEFAULT_K_PER_AMP)),
            floor_mm=float(r1.get("floor_mm", wp.DEFAULT_FLOOR_MM)))
        planned = cu.half_width * 2.0
        checks.append((pid, planned, required))
        meta[pid] = {"planned_mm": planned, "required_min_mm": required}
    return checks, meta


def _run_drc(view, scene, cap_checks, w_checks):
    """DRC 判定编排（与 selection._run_drc 同型同源，见模块 docstring）。"""
    report = check_all(scene, view.hard_rules,
                       sensitive_rects=view.sensitives,
                       capacity_checks=cap_checks,
                       width_checks=w_checks)
    r6 = check_keepout(_segment_coppers(scene), view.keepouts, view.plane_layers)
    return list(report.violations) + list(r6)


def _segment_coppers(coppers):
    """折线铜逐段分解为单段铜（R6 精查用；与 selection._segment_coppers 同型）。"""
    out = []
    for cu in coppers:
        if cu.polyline:
            for k, (a, b) in enumerate(clearance.polyline(cu.polyline)):
                out.append(Copper(cu.net_id, "%s#seg%d" % (cu.cid, k), cu.layer,
                                  polyline=[[a[0], a[1]], [b[0], b[1]]],
                                  half_width=cu.half_width))
        else:
            out.append(cu)
    return out


def _routes_attribution(violation):
    """归责（镜像 selection._candidate_attribution；候选铜→路线铜）：
    capacity/R1 恒归责；其余规则按主体是否含 "route:" 前缀；structure/R4 为 routes
    工件缺陷恒归责；固定铜互扰（双 fixed）不归责。"""
    if violation.rule in ("capacity", "R1", "structure", "R4"):
        return True
    for s in (violation.subject_a, violation.subject_b):
        if isinstance(s, str) and s.startswith(ROUTE_CID_PREFIX):
            return True
    return False


# ---------------------------------------------------------------- 工件校验

def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _is_point(v):
    return isinstance(v, (list, tuple)) and len(v) == 2 and all(_is_num(x) for x in v)


def _is_hex64(s):
    return isinstance(s, str) and len(s) == _SHA256_LEN and \
        all(c in _HEX for c in s)


def _fail(path, msg):
    raise RouteCheckError("[%s] %s" % (path, msg))


def validate_routes(board, doc):
    """v5.routes.v1 工件 fail-closed 校验（键路径化报错；合同见模块 docstring）。"""
    if not isinstance(doc, dict):
        _fail("routes_doc", "须为 dict")
    if doc.get("schema_version") != ROUTES_SCHEMA_VERSION:
        _fail("schema_version", "须为 %r，得到 %r" % (ROUTES_SCHEMA_VERSION, doc.get("schema_version")))
    bid = doc.get("board_id")
    if not isinstance(bid, str) or not bid:
        _fail("board_id", "须为非空字符串")
    if bid != board.get("board_id"):
        _fail("board_id", "与板 board_id 不匹配（%r != %r）" % (bid, board.get("board_id")))
    sha = doc.get("board_sha256")
    if not _is_hex64(sha):
        _fail("board_sha256", "须为 64 位十六进制 sha256")
    if sha != board_mod.compute_board_sha256(board):
        _fail("board_sha256", "与板 provenance 哈希链不复算（错板错件配对）")
    log = doc.get("negotiation_log")
    if not isinstance(log, list) or not all(isinstance(x, str) for x in log):
        _fail("negotiation_log", "须为字符串数组")
    prov = doc.get("provenance")
    if not isinstance(prov, dict):
        _fail("provenance", "须为 dict")
    if not isinstance(prov.get("generator"), str) or not prov.get("generator"):
        _fail("provenance.generator", "须为非空字符串")
    if prov.get("board_sha256") != sha:
        _fail("provenance.board_sha256", "须与顶层 board_sha256 一致")

    view = _BoardView(board)
    routes = doc.get("routes")
    if not isinstance(routes, list):
        _fail("routes", "须为数组")
    chain = {}   # net_id -> [entry, ...]（网级链审计）
    for i, entry in enumerate(routes):
        path = "routes[%d]" % i
        if not isinstance(entry, dict):
            _fail(path, "须为 dict")
        extra = set(entry) - set(ENTRY_KEYS)
        if extra:
            _fail(path, "含合同外键 %s（允许键：%s）" % (sorted(extra), list(ENTRY_KEYS)))
        missing = set(ENTRY_KEYS) - set(entry)
        if missing:
            _fail(path, "缺键 %s" % sorted(missing))
        pid = entry["partition_id"]
        if not isinstance(pid, str) or pid not in view.partitions:
            _fail(path + ".partition_id", "指向不存在的分区 %r" % (pid,))
        nid = entry["net_id"]
        net = None
        for n in board.get("nets", []):
            if n.get("net_id") == nid:
                net = n
                break
        if not isinstance(nid, str) or net is None:
            _fail(path + ".net_id", "指向不存在的网 %r" % (nid,))
        if pid not in net["partitions"]:
            _fail(path + ".net_id", "网 %r 不引用分区 %r" % (nid, pid))
        layer = entry["layer"]
        info = view.layers.get(layer)
        if info is None:
            _fail(path + ".layer", "未知层 %r" % (layer,))
        if info.get("kind") != "signal" or info.get("available") is not True:
            _fail(path + ".layer", "层 %r 不可布线（非信号层或不可用）" % (layer,))
        pts = entry["polyline"]
        if not isinstance(pts, list) or len(pts) < 2 or not all(_is_point(p) for p in pts):
            _fail(path + ".polyline", "须为 ≥2 个 [x,y] 有限数值坐标点")
        for key in ("transition_vias", "return_vias"):
            v = entry[key]
            if not isinstance(v, list) or not all(_is_point(p) for p in v):
                _fail(path + "." + key, "须为 [x,y] 数组")
        w = entry["width"]
        if not _is_num(w) or w <= 0:
            _fail(path + ".width", "须为正有限数值")
        chain.setdefault(nid, []).append(entry)

    # 网级链审计：首末点=分区端点；多段在过渡孔点衔接（合同见 docstring）
    for nid in sorted(chain):
        entries = chain[nid]
        pids = {e["partition_id"] for e in entries}
        if len(pids) != 1:
            _fail("routes", "网 %s 的 entry 指向多个分区 %s" % (nid, sorted(pids)))
        pid = entries[0]["partition_id"]
        eps = [list(map(float, pt)) for pt in view.partitions[pid]["geometry"]["endpoints"]]
        first, last = entries[0]["polyline"][0], entries[-1]["polyline"][-1]

        def _eq_pt(a, b):
            return abs(a[0] - b[0]) <= clearance.EPS and abs(a[1] - b[1]) <= clearance.EPS

        ok_orient = (_eq_pt(first, eps[0]) and _eq_pt(last, eps[1])) or \
                    (_eq_pt(first, eps[1]) and _eq_pt(last, eps[0]))
        if not ok_orient:
            _fail("routes", "网 %s 首末点须为分区 %s 端点 %s（得到 %s..%s）"
                  % (nid, pid, eps, first, last))
        for k in range(len(entries) - 1):
            a, b = entries[k], entries[k + 1]
            joint_a, joint_b = a["polyline"][-1], b["polyline"][0]
            if not _eq_pt(joint_a, joint_b):
                _fail("routes", "网 %s 第 %d/%d 段衔接点不重合" % (nid, k, k + 1))
            if not any(_eq_pt(joint_a, v) for v in a["transition_vias"]) or \
               not any(_eq_pt(joint_a, v) for v in b["transition_vias"]):
                _fail("routes", "网 %s 第 %d/%d 段衔接点未在 transition_vias 披露" % (nid, k, k + 1))

    # 附加披露键
    extra_keys = set(doc) - {"schema_version", "board_id", "board_sha256", "routes",
                             "negotiation_log", "provenance"} - set(EXTRA_TOP_KEYS)
    if extra_keys:
        _fail("routes_doc", "含合同外顶层键 %s（允许：%s）" % (sorted(extra_keys), list(EXTRA_TOP_KEYS)))
    rg = doc.get("ribbon_groups")
    if rg is not None:
        if not isinstance(rg, dict):
            _fail("ribbon_groups", "须为 dict（partition_id → 披露对象）")
        for pid, item in rg.items():
            if pid not in view.partitions:
                _fail("ribbon_groups.%s" % pid, "指向不存在的分区")
            if not isinstance(item, dict) or \
               not isinstance(item.get("net_ids"), list) or \
               not all(isinstance(x, str) for x in item.get("net_ids", [])) or \
               not _is_num(item.get("occupancy_mm")) or not isinstance(item.get("route_index"), int):
                _fail("ribbon_groups.%s" % pid,
                      "须含 net_ids[str]/occupancy_mm(float)/route_index(int)")
    fp = doc.get("fixed_partitions")
    if fp is not None:
        if not isinstance(fp, list) or not all(isinstance(x, str) for x in fp):
            _fail("fixed_partitions", "须为分区 id 字符串数组")
        for pid in fp:
            if pid not in view.partitions:
                _fail("fixed_partitions", "指向不存在的分区 %r" % (pid,))
    pr = doc.get("pour_regions")
    if pr is not None:
        if not isinstance(pr, dict):
            _fail("pour_regions", "须为 dict（partition_id → rect）")
        for pid, rect in pr.items():
            if pid not in view.partitions:
                _fail("pour_regions.%s" % pid, "指向不存在的分区")
            if not isinstance(rect, dict) or \
               not all(_is_num(rect.get(k)) for k in ("x_min", "y_min", "x_max", "y_max")):
                _fail("pour_regions.%s" % pid, "须为 x_min/y_min/x_max/y_max 矩形")
    return True


# ---------------------------------------------------------------- 场景构造与判定

class _RouteCopper(Copper):
    """带 partition_id 的路线铜（归责/同分区豁免用）。"""

    def __init__(self, net_id, cid, layer, partition_id, polyline, width):
        Copper.__init__(self, net_id, cid, layer, polyline=polyline,
                        half_width=float(width) / 2.0)
        self.partition_id = partition_id


def build_scene(view, doc):
    """routes + 板固定铜 → (scene_coppers, route_coppers, declared, structure_violations,
    cid_partition)。

    ribbon（copper_band）与既布（ROUTED）分区的 entry 是固定铜的声明，不重复构造
    route 铜（去重规则见模块 docstring）；声明一致性以 structure 违例核对。
    过孔铜（D2）追加进 scene（不入 route_coppers——容量/R1 以走线宽计，孔铜
    只参与 R5/R6 间距场景）；同网同孔位去重=物理一孔。
    """
    structure = []
    cid_partition = {}
    route_coppers = []
    for i, entry in enumerate(doc["routes"]):
        pid = entry["partition_id"]
        cid = "%s%s:%s#%d" % (ROUTE_CID_PREFIX, entry["net_id"], pid, i)
        cid_partition[cid] = pid
        if view.ribbon_partition(pid):
            p = view.partitions[pid]
            geo = p.get("geometry") or {}
            band = geo.get("copper_band")
            occ = geo.get("occupancy_mm")
            lo, hi = sorted((float(band[0]), float(band[1])))
            band_w = hi - lo
            if occ is not None and abs(entry["width"] - float(occ)) > clearance.EPS:
                structure.append(_mk_v("structure", cid, FIXED_CID_PREFIX + pid,
                                       {"reason": "ribbon entry width %r != occupancy_mm %r"
                                                  % (entry["width"], occ)}))
            elif abs(band_w - entry["width"]) > clearance.EPS and occ is None:
                structure.append(_mk_v("structure", cid, FIXED_CID_PREFIX + pid,
                                       {"reason": "ribbon entry width %r != 铜带宽 %r"
                                                  % (entry["width"], band_w)}))
            continue   # 固定铜已在场景（去重，不双计容量）
        if view.fixed_partition(pid):
            continue   # 同上：既布分区 entry = 固定铜声明，不重复构造
        pts = [[float(pt[0]), float(pt[1])] for pt in entry["polyline"]]
        if all(abs(p[0] - pts[0][0]) <= clearance.EPS
               and abs(p[1] - pts[0][1]) <= clearance.EPS for p in pts):
            continue   # 零长 polyline（升级件④接受缝，docstring「零长缝」节）：
                       # 退化分区 trivially-satisfied 声明，零铜展宽 = 无间距
                       # 交互，不构造 route 铜（非退化分区的零长 entry 已被
                       # validate_routes 链审计拒绝，此分支不可达）
        route_coppers.append(_RouteCopper(
            entry["net_id"], cid, entry["layer"], pid, pts, entry["width"]))
    via_coppers = _via_coppers(view, doc, cid_partition)
    fixed, declared = _fixed_coppers(view)
    scene = route_coppers + via_coppers + fixed
    return scene, route_coppers, declared, structure, cid_partition


def _via_coppers(view, doc, cid_partition):
    """routes 工件孔位 → 每信号层一枚圆铜（D2；同网同点去重=物理一孔）。

    cid = "route:via:<net>:<pid>#<k>"（ROUTE_CID_PREFIX 前缀 → 归责 routes；
    pid 进 cid_partition → 同分区豁免覆盖孔铜对）。"""
    seen = set()
    ordered = []
    for entry in doc["routes"]:
        for key in ("transition_vias", "return_vias"):
            for p in entry.get(key) or []:
                vkey = (entry["net_id"], round(float(p[0]), 9), round(float(p[1]), 9))
                if vkey in seen:
                    continue
                seen.add(vkey)
                ordered.append((entry["net_id"], entry["partition_id"],
                                (float(p[0]), float(p[1]))))
    coppers = []
    for k, (net_id, pid, pt) in enumerate(ordered):
        cid = "%svia:%s:%s#%d" % (ROUTE_CID_PREFIX, net_id, pid, k)
        cid_partition[cid] = pid
        for layer in view.signal_layers:
            coppers.append(_ViaCopper(net_id, cid, layer, pid, pt,
                                      view.via_radius))
    return coppers


class _V:
    """轻量违例视图（as_dict 形状与 drc.Violation 一致）。"""

    def __init__(self, rule, subject_a, subject_b, data):
        self.rule = rule
        self.subject_a = subject_a
        self.subject_b = subject_b
        self.data = data

    def as_dict(self):
        return {"rule": self.rule, "subjects": [self.subject_a, self.subject_b],
                "data": self.data}


def _mk_v(rule, a, b, data):
    return _V(rule, a, b, data)


def _r4_audit(view, doc):
    """R4 回流孔配对结构对账（非 v5.drc 判定，披露见 docstring）：
    每个过渡孔须在同网 return_vias 的并集内有配对孔，距离 ≤ R4.max_distance_mm。"""
    r4 = view.hard_rules.get("R4", {})
    max_d = float(r4.get("max_distance_mm", 2.0))
    violations = []
    by_net = {}
    for entry in doc["routes"]:
        by_net.setdefault(entry["net_id"], {"t": [], "r": []})
        by_net[entry["net_id"]]["t"].extend(entry["transition_vias"])
        by_net[entry["net_id"]]["r"].extend(entry["return_vias"])
    for nid in sorted(by_net):
        t, r = by_net[nid]["t"], by_net[nid]["r"]
        if len(t) != len(r):
            violations.append(_mk_v("R4", "net:" + nid, None,
                                    {"audit": "structural", "transition_vias": len(t),
                                     "return_vias": len(r),
                                     "reason": "回流孔数须等于过渡孔数（R4 return_via_required）"}))
            continue
        for i, via in enumerate(t):
            best = min((clearance.point_point(via, rv), j) for j, rv in enumerate(r)) \
                if r else (float("inf"), -1)
            if best[0] > max_d:
                violations.append(_mk_v("R4", "net:" + nid, None,
                                        {"audit": "structural", "via": list(via),
                                         "paired_distance_mm": round(best[0], 10),
                                         "max_distance_mm": max_d,
                                         "reason": "过渡孔无 ≤max_distance_mm 配对回流孔"}))
    return violations


def _edge_violations(view, scene):
    """P5⑥ D6-3 板边禁布带自查 → 消费接口键 edge_violations 的元素列表。

    判定全出自 v5.drc.check_edge_clearance（A9 单源；带值/轮廓源/口径见该
    判定器与 drc.EDGE_CLEARANCE_MM 注）。**恒在场、可为空列表**；元素 =
    {"net_id": str, "pos": [x, y]}——route（场景）铜判定点落入 workspace
    内缩 0.2mm 禁布带即记。本键为披露通道，**不入** feasible/归责违例流
    （板内固定铜贴边是板数据固有态，v5 不可移铜；归责纪律=板内固有缺陷不
    归责 routes，见模块 docstring）——执行侧拒布由 executor 障碍栅格承担
    （同一带同一源），kicad 侧残差由 D6-4 分类器以本键同位归责（匹配容差
    口径 SHARED_PT_TOL_MM 在消费侧 tools/run_p5_board.py）。(net_id, pos)
    去重、首现序（孔铜逐信号层枚枚重复点与 [T,R,T] 桩段同位点=物理一处
    一记）；零长条目不构造铜（升级件④缝）天然不参与。"""
    out, seen = [], set()
    for v in check_edge_clearance(scene, view.workspace):
        net_id = str(v.data["net_id"])
        pos = [float(v.data["pos"][0]), float(v.data["pos"][1])]
        key = (net_id, pos[0], pos[1])
        if key in seen:
            continue
        seen.add(key)
        out.append({"net_id": net_id, "pos": pos})
    return out


def check_routes(board, doc):
    """routes 判定编排主入口。

    返回 {"feasible": bool, "violations": [as_dict...],
          "attributed_violations": [...], "edge_violations": [{"net_id", "pos"}...],
          "capacity_checks": [(clid, occ, cap)...],
          "capacity_meta": {...}, "width_meta": {...}, "drc_version": str,
          "route_check_version": str}。
    edge_violations（P5⑥ D6-3）恒在场、可为空列表，披露通道不入 feasible
    （口径与消费方见 _edge_violations）。
    """
    validate_routes(board, doc)
    view = _BoardView(board)
    scene, route_coppers, declared, structure, cid_partition = build_scene(view, doc)
    cap_checks, cap_meta = _capacity_checks(view, route_coppers, scene_fixed(scene), declared)
    w_checks, w_meta = _width_checks(view, route_coppers)
    violations = _run_drc(view, scene, cap_checks, w_checks)
    violations.extend(structure)
    violations.extend(_r4_audit(view, doc))
    # 同分区豁免（模块 docstring「最小文档化决定」）：R5 双 route 铜同 partition 过滤
    filtered = []
    for v in violations:
        if v.rule == "R5" and _same_partition_pair(v, cid_partition):
            continue
        filtered.append(v)
    attributed = [v for v in filtered if _routes_attribution(v)]
    return {
        "feasible": not attributed,
        "violations": [v.as_dict() for v in filtered],
        "attributed_violations": [v.as_dict() for v in attributed],
        "edge_violations": _edge_violations(view, scene),
        "capacity_checks": [(clid, occ, cap) for clid, occ, cap in cap_checks],
        "capacity_meta": cap_meta,
        "width_meta": w_meta,
        "drc_version": DRC_VERSION,
        "route_check_version": ROUTE_CHECK_VERSION,
    }


def scene_fixed(scene):
    return [cu for cu in scene if cu.cid.startswith(FIXED_CID_PREFIX)]


def _subject_partition(subject, cid_partition):
    """违例主体 → 所属分区（升级件① 扩展）：route 铜/via 铜查 cid_partition；
    焊盘铜 cid 形如 "fixed:pad:<pid>:<net>:e<k>#<j>" 自带 pid。未知形态 None。"""
    if not isinstance(subject, str):
        return None
    part = cid_partition.get(subject)
    if part is not None:
        return part
    marker = FIXED_CID_PREFIX + "pad:"
    if subject.startswith(marker):
        return subject[len(marker):].split(":", 1)[0]
    return None


def _same_partition_pair(violation, cid_partition):
    """同分区豁免（模块 docstring「同分区豁免扩展」）：R5 对两侧主体同分区
    （route↔route / route↔via / route↔焊盘 / 焊盘↔焊盘）一律过滤。"""
    a, b = violation.subject_a, violation.subject_b
    if not (isinstance(a, str) and isinstance(b, str)):
        return False
    if not (a.startswith(ROUTE_CID_PREFIX) or a.startswith(FIXED_CID_PREFIX + "pad:")):
        return False
    if not (b.startswith(ROUTE_CID_PREFIX) or b.startswith(FIXED_CID_PREFIX + "pad:")):
        return False
    pa = _subject_partition(a, cid_partition)
    pb = _subject_partition(b, cid_partition)
    return pa is not None and pa == pb
