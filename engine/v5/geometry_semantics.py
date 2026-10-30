# -*- coding: utf-8 -*-
"""v5.geometry_semantics —— 几何语义版本/分面声明层（OPT-04 第一刀，EXEC-R2）。

**契约（本模块只做声明与薄委托，不复制几何核）**：
- 几何核本体不变：原语=v5.metrics.clearance，判定=v5.drc，via 半径单源=
  v5.kicad_export.via_model_params，保守地图投影面=net_agent_pilot.pilot。
  本模块的分面注册表只携带语义标签、权威锚（"模块::符号"字符串）与惰性取值
  器（import 引用活树单源值，**不拷贝第二份数值**）；一切判定行为仍走原模块，
  本模块零判定逻辑（零行为漂移第一刀）。
- **消费方契约**：五消费方（map/reach/DRC/executor/judge fixture）在各自模块
  加载时调用 declare_consumer(<name>) 登记并绑定本 VERSION，且在实际输出或
  关联侧车携带 VERSION（最小可验出口）。
  **executor 的声明接线由并行 OPT-09 席按「本模块 VERSION +
  declare_consumer("executor")」落入 v5/executor.py（单写者裁处，GATE-A1 G3）；
  本模块不 import executor、不代写。**
- **世界分离契约**：同版本声明是版本契约，不是各分面数值相同的证明；不同
  geometry version 的世界互不串号，旧产物按其自带版本号解释、永不回写
  （write_strict_cons_diff 缺省拒绝覆盖既有文件；本模块不提供任何改写历史
  JSON 的入口）。
- **strict/保守差异逐案落 JSON**：本层提供机制钩子（make_diff_record 字段
  构造 + write_strict_cons_diff 落盘点，schema=optimap-geometry/
  strict-cons-diff/2）；完整数据面（全量生产案件自动逐案披露与行为收口）属
  后续刀，本刀闭合度=机制钩子+有界 fixture 样例。

分面语义显式区分（同名"R5/间距/带"的四种取值面与投影差异，E1-b 盘点 §2）：
per-pair（网对 max(class_a,class_b)）/ scalar（标量，netclass 盲）/
conservative-max（全类保守 max）/ 含半宽投影（保守地图面，gap 判据里加双方
半宽）——见 FACETS["r5_*"] 与 FACETS["*band*"] 各 facet 的 semantics 字段。
"""
import copy as _copy
import json as _json
import os as _os

VERSION = "v5.geometry_semantics/0.1.0-decl"   # 0.1.0-decl=第一刀纯声明层：
# 不改任何判定/带值/容差/zone 判定；后续刀（重复源收口、差异 JSON 数据面）
# 若改判定行为必须升版本并分世界（不回写历史数字）。

# 任务书点名的五消费面（登记名）。route_check 是 DRC 面的 routes 判定编排
# 消费方，与 drc 权威模块并列登记（同名幂等；见 declare_consumer）。
KNOWN_CONSUMER_NAMES = ("map", "reach", "drc", "route_check", "judge",
                        "executor")

# ---------------------------------------------------------------- 分面注册表
# authority = "模块::符号"（薄委托锚；取值经 _authority_value 惰性 import 活树
# 单源，不复制数值）。semantics = 该面口径的显式声明；pending_second_cut 标记
# 既存第二源/字面量（第一刀只披露不收口——A1 裁定「不执行第二刀」）。
_FACET_VALUE_LAZY = {
    "eps_mm": ("v5.metrics.clearance", "EPS"),
    "prune_slack": ("v5.drc", "_PRUNE_SLACK"),
    "edge_clearance_mm": ("v5.drc", "EDGE_CLEARANCE_MM"),
    "hole_to_hole_mm": ("v5.drc", "HOLE_TO_HOLE_MM"),
    "map_track_half_mm": ("net_agent_pilot.pilot", "TRACK_HALF_MM"),
    "map_edge_margin_mm": ("net_agent_pilot.pilot", "EDGE_MARGIN_MM"),
}
# G2-H1（EXEC-R3）：旧键 map_via_radius_literal→("net_agent_pilot.pilot",
# "VIA_RADIUS_MM") 已随 R31-02 删除该常量而移除——via 半径是 board 参函数
# 非常量，经 via_radius_mm(board) 薄委托 kicad_export.via_model_params 单源。

FACETS = {
    "centerline_gap": {
        "authority": "v5.drc::_actual_gap",
        "semantics": ("strict 中心线距：polyline×polyline=segment_segment 裸"
                      "中心线距（不减任何半宽）；pad 面=点到段−r；band 面="
                      "段到矩；跨层返回 None（层间无 R5）"),
        "predicate": "gap < required - EPS（擦边合规）",
    },
    "r5_strict_per_pair": {
        "authority": "v5.route_check::check_routes→v5.drc.check_all",
        "semantics": ("per-pair：网对值 max(class_a, class_b)，无类网回落"
                      "标量 R5（中心线口径）"),
        "faces": "route_check/selection（selection 走无 net_classes=标量，"
                 "route_check.py:528-530 披露宽类板低估）",
    },
    "r5_executor_conservative_max": {
        "authority": "v5.executor::edge_blocked（route_check.r5_max 定义）",
        "semantics": ("conservative-max：全部网对用 max(缺省, 全类)——保守"
                      "设计取舍，非缺陷"),
    },
    "r5_map_scalar_projected": {
        "authority": "net_agent_pilot.pilot::_blocked_at",
        "semantics": ("scalar+含半宽投影：R5 标量 + 双方半宽（TRACK_HALF+"
                      "hw_other）保守地图提示面，netclass 盲"),
        "pending_second_cut": ("map 面 via 投影半径 0.3 字面量（pilot.py"
                               " _obstacles）与 TRACK_HALF 缺省档钉死——"
                               "第二刀收口对象，本刀只披露"),
    },
    "edge_band_centerline": {
        "authority": "v5.drc::check_edge_clearance",
        "semantics": ("判定点=中心线顶点/焊盘圆心/带角点（不含半宽/半径），"
                      "带值=EDGE_CLEARANCE_MM（薄委托单源）"),
        "value_key": "edge_clearance_mm",
    },
    "edge_band_map_projected": {
        "authority": "net_agent_pilot.pilot::_edge_blocked",
        "semantics": ("含半宽保守带：EDGE_MARGIN_MM + TRACK_HALF_MM（保守"
                      "方向=地图面比 strict 面更宽）"),
        "value_keys": ["map_edge_margin_mm", "map_track_half_mm"],
    },
    "hole_band_true": {
        "authority": "v5.drc::hole_track_blocked/hole_via_blocked",
        "semantics": ("真值带 margin=HOLE_TO_HOLE_MM（薄委托单源）；via 面"
                      "零豁免、track 面端点豁免由调用方筛"),
        "value_key": "hole_to_hole_mm",
    },
    "hole_band_map_conservative": {
        "authority": "net_agent_pilot.pilot::_blocked_at（孔面）",
        "semantics": ("保守带用 R5(0.5) 非 0.25 真值带（closure v2 修正史"
                      "自认保守伪影源）——数值差异第一刀不收口，经差异 JSON "
                      "钩子逐案披露"),
    },
    "via_radius": {
        "authority": "v5.kicad_export::via_model_params",
        "semantics": ("via 铜半径=(drill+2·annular)/2，board.via_model 优先"
                      "（唯一推导口；缺省 0.3）"),
        "pending_second_cut": ("R31-02 已收口，via 半径由 "
                               "v5.kicad_export.via_model_params 唯一推导，"
                               "缺省 0.3、板模型可覆盖"),
    },
    "zone_check": {
        "authority": "v5.drc::check_keepout（R6）",
        "semantics": ("四口径并存（第一刀不统一）：整铜 bbox（check_keepout "
                      "直调）/ 逐段 bbox（route_check/selection/executor，消"
                      "整线伪影）/ 单位段 bbox 过估（cmd_reach/closure，"
                      "docstring 自认）/ 零几何（adapter zones=[]，OPT-10 界"
                      "内）"),
    },
    "tolerances": {
        "authority": "v5.metrics.clearance::EPS / v5.drc::_PRUNE_SLACK",
        "semantics": ("EPS=1e-9（擦边/退化判定）；_PRUNE_SLACK=1e-12（剪枝"
                      "安全裕度）。既存容差分叉：pilot 端点孔豁免 1e-6 vs 其余"
                      "各面 1e-9、pilot._pt_seg_dist 退化阈值 1e-18 vs "
                      "clearance 1e-9——第二刀收口对象，本刀只披露"),
        "value_keys": ["eps_mm", "prune_slack"],
    },
}

# ---------------------------------------------------------------- 消费方登记
CONSUMERS = {}   # name -> {"geometry_semantics": VERSION, "declared_seq": int}
_DECLARED_ORDER = []


def declare_consumer(name):
    """消费方登记（幂等；模块加载时调用）。

    登记=版本契约绑定：CONSUMERS[name] 记录调用时点的本模块 VERSION。同版本
    声明不是该消费方数值与其它面相同的证明（分面差异见 FACETS）。executor
    席接线见模块 docstring 契约（OPT-09 单写者）。
    """
    if name in CONSUMERS:
        return
    CONSUMERS[name] = {"geometry_semantics": VERSION,
                       "declared_seq": len(_DECLARED_ORDER)}
    _DECLARED_ORDER.append(name)


def is_declared(name):
    return name in CONSUMERS


def declared_consumers():
    """已登记消费方（按登记序）。"""
    return tuple(_DECLARED_ORDER)


def version():
    """当前世界 geometry_semantics 版本（查询接口）。"""
    return VERSION


def consumer_versions():
    """各消费方声明绑定的版本（互异即多世界混线，测试断言全等）。"""
    return {name: rec["geometry_semantics"]
            for name, rec in sorted(CONSUMERS.items())}


def consumer_manifest(world=None):
    """最小可验出口（模块/侧车通用字段组）：版本+登记面+分面计数。"""
    return {
        "geometry_semantics": VERSION,
        "declared_consumers": list(_DECLARED_ORDER),
        "facet_count": len(FACETS),
        "world": world,
    }


def facet_table():
    """分面注册表快照（深拷贝；可序列化进侧车/报告）。"""
    return _copy.deepcopy(FACETS)


def _authority_value(key):
    """薄委托取值：惰性 import 权威模块取活树单源常量（不复制第二份值）。"""
    if key not in _FACET_VALUE_LAZY:
        raise KeyError("unknown facet value key: %r" % key)
    mod_name, attr = _FACET_VALUE_LAZY[key]
    import importlib
    return getattr(importlib.import_module(mod_name), attr)


def single_source_values(keys=None):
    """薄委托取值接口（分面声明→活树单源常量的引用式读取）。

    via 半径不在此列（board 参函数非常量）——用 via_radius_mm(board) 薄委托。
    """
    keys = sorted(_FACET_VALUE_LAZY) if keys is None else list(keys)
    return {k: _authority_value(k) for k in keys}


def via_radius_mm(board):
    """via 铜半径薄委托（唯一推导口 kicad_export.via_model_params，board 参）。"""
    from .kicad_export import via_model_params
    return via_model_params(board)["radius"]


# ------------------------------------------------- strict/保守差异 JSON 钩子
STRICT_CONS_DIFF_SCHEMA = "optimap-geometry/strict-cons-diff/2"
NEAR_THRESHOLD_TOL_MM = 1e-6     # |gap-required| ≤ max(EPS, 该值) ⇒ 近阈值


def make_diff_record(case_id, faces, authority_face, authority_rationale,
                     replica_of=None, independent_paths=None,
                     gap_mm=None, required_mm=None, board_sha16=None,
                     state_sha16=None, net_id=None):
    """strict/保守差异逐案记录构造器（机制钩子；数据面属后续刀）。

    - faces：{面名: {"verdict", "authority"(模块::符号或 file:line 锚),
      "semantics", "inputs"{...}}}——cons/true/strict 等面照登不代裁；
    - authority_face/authority_rationale：裁决权威面标识与依据（非权威面照登）；
    - replica_of：同源折叠（S5 §3.3 先例）——同面复述读数指向独立根；
    - independent_paths：聚合后独立输入路径数；
    - 近阈值强制显式：gap/required 给定时 near_threshold.within 机械计算；
      **近阈值案件 multi_route_independent_evidence 恒 False（判据逐字落
      字段：近阈值不得以多路同结果作独立证据）**。
    """
    if authority_face not in faces:
        raise ValueError("authority_face %r not in faces %r"
                         % (authority_face, sorted(faces)))
    near = None
    if gap_mm is not None and required_mm is not None:
        delta = gap_mm - required_mm
        tol = max(float(_authority_value("eps_mm")), NEAR_THRESHOLD_TOL_MM)
        near = {"gap_minus_required_mm": delta, "within_tol_mm": tol,
                "within": abs(delta) <= tol}
    indep = int(independent_paths or 0)
    multi_ok = (near is None or not near["within"]) and indep >= 2
    return {
        "schema": STRICT_CONS_DIFF_SCHEMA,
        "geometry_semantics": VERSION,
        "case_id": case_id,
        "board_sha16": board_sha16, "state_sha16": state_sha16,
        "net_id": net_id,
        "faces": faces,
        "authority_face": authority_face,
        "authority_rationale": authority_rationale,
        "replica_of": replica_of,
        "independent_paths": indep,
        "multi_route_independent_evidence": bool(multi_ok),
        "near_threshold": near,
    }


def write_strict_cons_diff(records, path, world=None, overwrite=False):
    """差异 JSON 落盘点（机制钩子）。

    **不回写纪律**：目标已存在且 overwrite=False 时拒绝（历史数字永不覆盖）；
    追加语义由调用方自管（建议按 case_id 分文件或读出-核验-新档）。
    """
    if _os.path.exists(path) and not overwrite:
        raise FileExistsError("strict/cons diff target exists (no-rewrite "
                              "discipline): %s" % path)
    doc = {"schema": STRICT_CONS_DIFF_SCHEMA, "geometry_semantics": VERSION,
           "world": world, "records": list(records)}
    d = _os.path.dirname(_os.path.abspath(path))
    if d:
        _os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        _json.dump(doc, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    return path


def interpret_product_version(product):
    """读既有产物的自带 geometry_semantics 版本（只读解释，不回写）。

    旧产物按其自带版本号解释（世界分离）；无该字段的旧产物=版本前产物，
    返回 None（不补猜）。
    """
    if isinstance(product, dict):
        v = product.get("geometry_semantics")
        return v if isinstance(v, str) else None
    return None
