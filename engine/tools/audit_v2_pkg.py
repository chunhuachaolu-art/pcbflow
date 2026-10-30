# -*- coding: utf-8 -*-
"""V2 盲包语义等价审计工具（P2 门：重生成盲包 vs V2 提示词 diff 审计）。

链路（全部真实模块，零 stub，不改 v5/ 与 tests/）：
  tests/fixtures_v2.build_v2_board()（只读 import）
  -> 注入分区聚类粒度先验（L1 硬要求：聚类粒度须溯源注册表；fixtures_v2 注册表为空，
     取 tests/test_pkg.py 同模板 min_gap_mm=2.0 / group_types=["BUS","DIFF"]，
     板哈希按链式规则重算）
  -> v5.board.load_board
  -> v5.partition.build_partition_artifact   (L1)
  -> v5.envelope_plan.build_envelope_artifact (L2)
  -> v5.overlay.build_conflicts              (L3)
  -> v5.pkg.build_pkg -> v5.pkg.write_pkg 落盘

产物（sidecar 卫生：只写 out/ 下）：
  out/v5-p2/audit/v2-scenario.pkg.json  重生成盲包（provenance 头由 write_sidecar 注入）
  out/v5-p2/audit/v2-pkg-diff.json      审计报告（provenance 头 generator=v5.audit）

审计口径（诚实分类，不为好看放水）：
- V2 侧常量逐条转录自冻结模板；先验门槛：模板字节 sha256 必须 ==
  fixtures_v2.SOURCE_SHA256，漂移即拒绝审计（与 tests/test_golden_v2.py 同口径防转录失真）；
- 每条 verdict 由 pkg 实际值与 V2 常量对比 / 全树键与文本扫描计算，不手工钦定；
  数值对账注记给两侧数值；
- verdict：equivalent=语义被 pkg 数据覆盖；deviation=有对应键但语义/形态有差；
  missing=V2 有 pkg 无；extra=pkg 有 V2 无；
- 发现的合同层缺口只进 fix_candidates 供主审裁决，本工具不改任何代码。

确定性：无时间戳、无随机、无 set 迭代序依赖（扫描全 sorted）；canonical json 落盘，
重跑同字节。
"""
import hashlib
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (PROJECT_ROOT, os.path.join(PROJECT_ROOT, "tests")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from v5.board import compute_board_sha256, load_board                     # noqa: E402
from v5.envelope_plan import build_envelope_artifact                      # noqa: E402
from v5.envelope_plan import validate_envelope_artifact                   # noqa: E402
from v5.overlay import build_conflicts, validate_conflicts_artifact       # noqa: E402
from v5.partition import build_partition_artifact                         # noqa: E402
from v5.pkg import build_pkg, validate_pkg, write_pkg                     # noqa: E402
from v5 import sidecar                                                    # noqa: E402
import fixtures_v2 as fx                                                  # noqa: E402

AUDIT_VERSION = "v5.audit/0.1.0"
GENERATOR = "v5.audit"
GENERATOR_VERSION = "0.1.0"
V2_TEMPLATE_PATH = fx.SOURCE_PATH
OUT_DIR = os.path.join(PROJECT_ROOT, "out", "v5-p2", "audit")
PKG_PATH = os.path.join(OUT_DIR, "v2-scenario.pkg.json")
REPORT_PATH = os.path.join(OUT_DIR, "v2-pkg-diff.json")

SECTIONS = ("板参数", "区域", "成本模型", "分区表", "冲突扫描说明", "待裁决项",
            "路由顺序", "输出合同")

# ------------------------------------------------------- V2 冻结常量（模板转录）
# 模板 sha 先验校验通过后，以下转录值才有效（逐条对应 prompt-v2-template.md 原文）。
V2_WORKSPACE = {"x_min": 0.0, "y_min": 0.0, "x_max": 50.0, "y_max": 40.0}
V2_PAD_RADIUS_MM = 0.15
V2_STACKUP = {  # id -> (kind, preferred_direction, available)
    "F.Cu": ("signal", "h", True),
    "In1.Cu": ("signal", "v", True),
    "In2.Cu": ("plane", "any", False),   # 完整 GND 平面，禁布（R6）
    "B.Cu": ("signal", "any", True),     # 任意方向无方向罚
}
V2_ZONES = {
    "K1": {"kind": "keepout", "rect": (0.0, 16.0, 30.0, 24.0), "layers": "all"},
    "K2": {"kind": "keepout", "rect": (36.0, 16.0, 50.0, 24.0), "layers": "all"},
    "C1": {"kind": "corridor", "rect": (30.0, None, 36.0, None), "layers": "signal",
           "capacity": 4.3, "band_lo": 30.85, "band_hi": 35.15},
    "ANA": {"kind": "sensitive", "rect": (20.0, 8.0, 28.0, 15.0), "layers": "signal"},
}
V2_WEIGHTS = {"detour_rate": 0.5, "direction_rate": 0.2,
              "via_cost": 4.0, "return_cost": 1.0}
V2_RULES = {
    "R1": {"k_a": 0.4, "floor_mm": 0.3},
    "R2": {"min_distance_mm": 3.0, "max_parallel_mm": 5.0},
    "R3": {"unsplittable": True},
    "R4": {"return_via_required": True, "max_distance_mm": 2.0},
    "R5": {"min_clearance_mm": 0.5},
    "R6": {"plane_forbidden": True, "keepout_zones_forbidden": True},
}
V2_PART_IDS = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9"]
V2_PARTS = {
    "P1": {"endpoints": [[2.0, 38.0], [44.0, 38.0]], "ptype": "PWR",
           "layer": "F.Cu", "current_a": 1.5, "prior": (0.6, 1.4), "speed": "power",
           "planned_width": 1.2},
    "P2": {"endpoints": [[5.0, 10.0], [45.0, 10.0]], "ptype": "CLK",
           "layer": "F.Cu", "prior": (0.15, 0.15), "speed": "clk_200M",
           "planned_width": 0.15},
    "P3": {"endpoints": [[16.0, 4.0], [16.0, 36.0]], "ptype": "HS",
           "layer": "F.Cu", "prior": (0.2, 0.2), "speed": "hs_125M",
           "planned_width": 0.2},
    "P4": {"centerline": [[32.6, 4.0], [32.6, 36.0]], "ptype": "BUS",
           "occupancy_mm": 3.3, "copper_band": [30.95, 34.25],
           "planned_width": 0.15},
    "P5": {"endpoints": [[37.0, 10.0], [37.0, 30.0]], "ptype": "MISC",
           "prior": (0.2, 0.2), "speed": "low_speed", "planned_width": 0.2},
    "P6": {"endpoints": [[46.0, 32.0], [46.0, 38.0]], "ptype": "MISC",
           "prior": (0.2, 0.2), "speed": "low_speed", "planned_width": 0.2},
    "P7": {"endpoints": [[2.0, 36.7], [44.0, 36.7]], "ptype": "ROUTED",
           "prior": (0.2, 0.2), "speed": "low_speed", "planned_width": 0.2},
    "P8": {"endpoints": [[44.0, 4.0], [48.0, 4.0]], "ptype": "PWR",
           "current_a": 2.0, "prior": (0.8, 1.6), "speed": "power",
           "planned_width": 0.5},
    "P9": {"endpoints": [[2.0, 36.1], [44.0, 36.1]], "ptype": "ROUTED",
           "prior": (0.2, 0.2), "speed": "low_speed", "planned_width": 0.2},
}
V2_LADDER_FIVE = "时钟 > 高速串行 > 并行总线 > 电源 > 低速杂项"
V2_LADDER_C1 = "（C1）"
V2_COMBO_ENUM_NORM = "留F.Cu过C1|换层B.Cu|换层In1"   # V2 逐字形态含空格，比对去空格
V2_DEFECT_RULE_ENUM = "R1..R6 或 自相矛盾"


def _fmt(x):
    """数值紧凑确定格式（与 v5.overlay._fmt 同口径），供注记两侧数值。"""
    return repr(round(float(x), 10))


# ------------------------------------------------------------------ 扫描原语

def _iter_strings(obj, path=""):
    """全树字符串遍历（路径确定序）。"""
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k in sorted(obj):
            for item in _iter_strings(obj[k], path + "." + str(k)):
                yield item
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            for item in _iter_strings(v, "%s[%d]" % (path, i)):
                yield item


def _iter_keys(obj, path=""):
    """全树键名遍历（路径确定序）。"""
    if isinstance(obj, dict):
        for k in sorted(obj):
            yield path + "." + str(k), k
            for item in _iter_keys(obj[k], path + "." + str(k)):
                yield item
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            for item in _iter_keys(v, "%s[%d]" % (path, i)):
                yield item


def _has_text(pkg, needle):
    return any(needle in s for _, s in _iter_strings(pkg))


def _has_key_like(pkg, *needles):
    hits = []
    for path, k in _iter_keys(pkg):
        low = k.lower()
        if any(n in low for n in needles):
            hits.append(path)
    return hits


def _find_j(pkg, subjects=None, kind=None, zone=None, text=None):
    """按 (subjects, kind, zone, statement 含串) 找 J 项；全参 None 即任取首个。"""
    for it in pkg["j_items"]:
        if subjects is not None and it["subjects_partitions"] != subjects:
            continue
        if kind is not None and it["kind"] != kind:
            continue
        if zone is not None and it["zone"] != zone:
            continue
        if text is not None and text not in it["statement"]:
            continue
        return it
    return None


def _zone(pkg, zid):
    return next(z for z in pkg["zones"] if z["zone_id"] == zid)


def _part(pkg, pid):
    return next(e for e in pkg["partition_table"] if e["partition_id"] == pid)


def _row(section, v2_item, pkg_field, verdict, note):
    """审计行构造（字段顺序固定，canonical 落盘时按键序）。"""
    assert section in SECTIONS, section
    return {"section": section, "v2_item": v2_item, "pkg_field": pkg_field,
            "verdict": verdict, "note": note}


def _vd(cond):
    """有对应键的语义对账：cond=True → equivalent，否则 deviation。"""
    return "equivalent" if cond else "deviation"


# ------------------------------------------------------------------ 板构造

def _gran_entry():
    """分区聚类粒度先验（tests/test_pkg.py gran_entry 同模板；L1 必需输入）。

    fixtures_v2.build_v2_board() 的 principle_registry 为空，而 L1 分区器
    fail-closed 要求恰一条 kind=partition_granularity 先验；本工具按仓库既定
    V2 场景口径（min_gap_mm=2.0，test_pkg.v2_board_with_gran 同参）注入，
    注入后板哈希按链式规则重算。
    """
    from v5 import canonical
    entry = {
        "principle_id": "P-PART-GRAN-V2AUDIT",
        "name": "分区聚类粒度先验",
        "intent": {"protects": "走廊通行容量", "sacrifices": "细粒度自由"},
        "scope": "partitioning",
        "protected_resources": ["corridor_capacity"],
        "target_freedom": "corridor",
        "priority": 50,
        "hard_or_soft": "soft",
        "overridable": True,
        "compiled_rule": {"kind": "partition_granularity",
                          "params": {"min_gap_mm": 2.0,
                                     "group_types": ["BUS", "DIFF"]}},
        "enforcement": "generation",
        "conflict_policy": {"conflicts_with": [], "yields_to": []},
        "evidence_refs": ["V5.0-DEV-TASKBOOK §4 L1"],
        "version": "1.0.0",
    }
    entry["source_hash"] = canonical.canonical_sha256(entry)
    return entry


def build_audit_board():
    """fixtures_v2 板 + 粒度先验，链式重算 board_sha256（确定性）。"""
    board = fx.build_v2_board()
    board["principle_registry"] = [_gran_entry()]
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    return board


# ------------------------------------------------------------------ 审计行

def audit_rows(pkg, part_artifact, env_artifact, conf_artifact):
    """逐节对账：每条 verdict 由 pkg 实际值与 V2 常量对比/扫描计算。"""
    rows = []
    ws = pkg["board_brief"]["workspace"]
    stack = {s["id"]: s for s in pkg["board_brief"]["stackup"]}
    cm = pkg["board_brief"]["cost_model"]
    hr = pkg["board_brief"]["hard_rules"]
    table = {e["partition_id"]: e for e in pkg["partition_table"]}
    ji = pkg["j_items"]
    ch = pkg["output_contract"]["channels"]
    oc_note = pkg["output_contract"]["note"]
    texts = [s for _, s in _iter_strings(pkg)]

    # ---------------- 板参数 ----------------
    rows.append(_row(
        "板参数", "布线工作区 x∈[0,50], y∈[0,40] mm（工作区外不存在任何可布空间）",
        "board_brief.workspace",
        _vd(ws == V2_WORKSPACE),
        ("pkg 四边界 x_min=%s/y_min=%s/x_max=%s/y_max=%s 与 V2 逐值一致；"
         "「工作区外不存在任何可布空间」由四边界显式披露承接（f8-01）"
         % (_fmt(ws["x_min"]), _fmt(ws["y_min"]), _fmt(ws["x_max"]), _fmt(ws["y_max"])))))

    pad_hits = _has_key_like(pkg, "pad", "radius")
    rows.append(_row(
        "板参数", "所有端点均为焊盘，半径 0.15mm，位于其所属层的 F.Cu 面",
        "board_brief（全树扫描 pad/radius 键）",
        "missing" if not pad_hits else "deviation",
        ("pkg 全树无 pad/radius 键；数值 %s 仅以 P2/P4 width_prior（线宽先验语义）出现；"
         "V2「端点=焊盘 r%s、位于所属层 F.Cu 面」未数据化，端点仅以裸坐标透传——"
         "R5 焊盘间距复核缺焊盘几何基准（合同层缺口，见 fix_candidates）"
         % (_fmt(V2_PAD_RADIUS_MM), _fmt(V2_PAD_RADIUS_MM)))))

    for lid, v2_item_note in (
            ("F.Cu", "信号层，优选水平方向"),
            ("In1.Cu", "信号层，优选垂直方向"),
            ("B.Cu", "信号层，任意方向无方向罚")):
        e = stack.get(lid, {})
        got = (e.get("id"), e.get("kind"), e.get("preferred_direction"),
               e.get("available"))
        rows.append(_row(
            "板参数", "%s：%s" % (lid, v2_item_note),
            "board_brief.stackup[%s]" % lid,
            _vd(got == (lid,) + V2_STACKUP[lid]),
            "pkg stackup %s = {kind:%s, preferred_direction:%s, available:%s} 与 V2 一致"
            % (lid, e.get("kind"), e.get("preferred_direction"), e.get("available"))))

    e = stack.get("In2.Cu", {})
    in2_ok = (e.get("id") == "In2.Cu" and e.get("kind") == "plane"
              and e.get("available") is False
              and hr.get("R6", {}).get("plane_forbidden") is True)
    rows.append(_row(
        "板参数", "In2.Cu：完整 GND 平面，禁布（R6）",
        "board_brief.stackup[In2.Cu] + board_brief.hard_rules.R6",
        _vd(in2_ok),
        ("pkg stackup In2.Cu = {kind:%s, available:%s} + R6.plane_forbidden=%s 承接"
         "「平面+禁布」；「GND/完整」字样未数据化（对布线裁决无增量语义）"
         % (e.get("kind"), e.get("available"), hr.get("R6", {}).get("plane_forbidden")))))

    # ---------------- 区域 ----------------
    for zid, extra_note in (
            ("K1", "全层禁布区"),
            ("K2", "全层禁布区")):
        z = _zone(pkg, zid)
        want = V2_ZONES[zid]
        r = z["rect"]
        got = (r["x_min"], r["y_min"], r["x_max"], r["y_max"])
        ok = (z["kind"] == want["kind"] and z["layers"] == want["layers"]
              and got == want["rect"])
        rows.append(_row(
            "区域", "%s：%s x∈[%s,%s], y∈[%s,%s]" % (
                zid, extra_note, _fmt(want["rect"][0]), _fmt(want["rect"][2]),
                _fmt(want["rect"][1]), _fmt(want["rect"][3])),
            "zones[%s] (kind/rect/layers)" % zid,
            _vd(ok),
            "pkg zones %s = {kind:%s, rect:(%s,%s,%s,%s), layers:%s} 与 V2 逐值一致"
            % (zid, z["kind"], _fmt(r["x_min"]), _fmt(r["y_min"]),
               _fmt(r["x_max"]), _fmt(r["y_max"]), z["layers"])))

    z = _zone(pkg, "C1")
    r = z["rect"]
    c1_ok = (z["kind"] == "corridor" and z["layers"] == "signal"
             and r["x_min"] == 30.0 and r["x_max"] == 36.0
             and "唯一通道" in z.get("note", ""))
    rows.append(_row(
        "区域", "C1：x∈[30,36] 的贯穿带，是 y<16 与 y>24 两区之间唯一通道（任何信号层）",
        "zones[C1] (kind/rect/layers/note)",
        _vd(c1_ok),
        ("pkg zones C1 = {kind:corridor, rect x %s..%s, layers:%s, note 含「唯一通道」}；"
         "rect y 取禁布窗 [%s,%s]（夹具蓝本转录口径；demo-01 蓝本才改全高 y∈[0,40]，"
         "属任务书明确差异），贯穿语义由 note+容量承接"
         % (_fmt(r["x_min"]), _fmt(r["x_max"]), z["layers"],
            _fmt(r["y_min"]), _fmt(r["y_max"])))))

    ledger_c1 = env_artifact["corridor_ledger"].get("C1", {})
    band_ok = (z.get("capacity") == V2_ZONES["C1"]["capacity"]
               and "30.85" in z.get("note", "") and "35.15" in z.get("note", ""))
    rows.append(_row(
        "区域", "C1 每信号层可用布线带 x∈[30.85,35.15]（4.3mm，已含对禁布区的间距扣减）",
        "zones[C1].capacity + zones[C1].note",
        _vd(band_ok),
        ("pkg capacity=%s、note 含布线带 [30.85,35.15]，与 V2 4.3mm 一致；链上 L2 账本 "
         "corridor_ledger.C1={capacity:%s, occupancy:%s, slack:%s, fits:%s}（仅 P4 命中）"
         % (_fmt(z.get("capacity")), _fmt(ledger_c1.get("capacity_mm")),
            _fmt(ledger_c1.get("occupancy_mm")), _fmt(ledger_c1.get("slack_mm")),
            ledger_c1.get("fits")))))

    formula_in_pkg = any("0.5×" in s or "0.5*" in s for s in texts)
    n_cap = sum(1 for c in conf_artifact["conflicts"]
                if c["kind"] == "capacity_infeasible")
    rows.append(_row(
        "区域", "C1 占用核算 = 铜宽 + 网间 0.5mm 间距",
        "（pkg 无显式键；公式仅随 capacity_infeasible 冲突 arithmetic 入包）",
        "missing" if not formula_in_pkg else "equivalent",
        ("pkg 全树无占用公式文本；本板直线几何与走廊窗 (30,16)-(36,24) 相交者仅 P4 "
         "（账本 occupancy 3.3≤4.3），capacity_infeasible 冲突 %d 条，"
         "「Σ铜宽+0.5×(n−1)」未随任何冲突 arithmetic 进入盲包" % n_cap)))

    z = _zone(pkg, "ANA")
    r = z["rect"]
    ana_ok = (z["kind"] == "sensitive" and z["layers"] == "signal"
              and (r["x_min"], r["y_min"], r["x_max"], r["y_max"])
              == V2_ZONES["ANA"]["rect"])
    rows.append(_row(
        "区域", "ANA：模拟敏感区 x∈[20,28], y∈[8,15]，对所有信号层生效",
        "zones[ANA] (kind/rect/layers)",
        _vd(ana_ok),
        "pkg zones ANA = {kind:%s, rect:(%s,%s,%s,%s), layers:%s} 与 V2 逐值一致"
        % (z["kind"], _fmt(r["x_min"]), _fmt(r["y_min"]),
           _fmt(r["x_max"]), _fmt(r["y_max"]), z["layers"])))

    rows.append(_row(
        "区域", "R2：距 ANA 边界 <3mm 且累计平行 >5mm 禁止",
        "board_brief.hard_rules.R2",
        _vd(hr.get("R2") == V2_RULES["R2"]),
        "pkg R2={min_distance_mm:%s, max_parallel_mm:%s} 与 V2 3mm/5mm 一致"
        % (_fmt(hr["R2"]["min_distance_mm"]), _fmt(hr["R2"]["max_parallel_mm"]))))

    rows.append(_row(
        "区域", "R6：In2 禁布；K1/K2 全层禁布",
        "board_brief.hard_rules.R6 + zones[K1/K2].layers + stackup[In2.Cu].available",
        _vd(hr.get("R6") == V2_RULES["R6"]),
        "pkg R6={plane_forbidden:%s, keepout_zones_forbidden:%s} 与 V2 一致；"
        "K1/K2 layers=all、In2.Cu available=false 三处互相印证"
        % (hr["R6"]["plane_forbidden"], hr["R6"]["keepout_zones_forbidden"])))

    # ---------------- 成本模型 ----------------
    w = cm["weights"]
    rows.append(_row(
        "成本模型", "过孔 4/个", "board_brief.cost_model.weights.via_cost",
        _vd(w.get("via_cost") == V2_WEIGHTS["via_cost"]),
        "pkg via_cost=%s = V2 4/个" % _fmt(w["via_cost"])))

    rows.append(_row(
        "成本模型", "回流孔 1/个（R4：每个换层过渡孔配 1 个回流孔，距离 ≤2mm）",
        "board_brief.cost_model.weights.return_cost + hard_rules.R4",
        _vd(w.get("return_cost") == V2_WEIGHTS["return_cost"]
            and hr.get("R4") == V2_RULES["R4"]),
        "pkg return_cost=%s = V2 1/个；R4={return_via_required:%s, max_distance_mm:%s} "
        "= V2 必配+≤2mm"
        % (_fmt(w["return_cost"]), hr["R4"]["return_via_required"],
           _fmt(hr["R4"]["max_distance_mm"]))))

    rows.append(_row(
        "成本模型", "绕行：布线长度超出两端点直线距离的部分 × 0.5/mm",
        "board_brief.cost_model.weights.detour_rate",
        _vd(w.get("detour_rate") == V2_WEIGHTS["detour_rate"]),
        "pkg detour_rate=%s = V2 0.5/mm" % _fmt(w["detour_rate"])))

    dirs_ok = (stack["F.Cu"]["preferred_direction"] == "h"
               and stack["In1.Cu"]["preferred_direction"] == "v"
               and stack["B.Cu"]["preferred_direction"] == "any")
    rows.append(_row(
        "成本模型", "逆优选方向：总长度 × 0.2/mm（F.Cu 计垂直段，In1 计水平段，B.Cu 不计）",
        "board_brief.cost_model.weights.direction_rate + stackup[*].preferred_direction",
        _vd(w.get("direction_rate") == V2_WEIGHTS["direction_rate"] and dirs_ok),
        ("pkg direction_rate=%s = V2 0.2/mm；层计段规则未逐字内嵌，方向语义由 "
         "stackup preferred_direction F.Cu=h（逆=垂直段）/In1.Cu=v（逆=水平段）/"
         "B.Cu=any（不计）等价承接" % _fmt(w["direction_rate"]))))

    rows.append(_row(
        "成本模型", "宽度在允许区间内调整：0 罚",
        "（pkg 无显式键；区间由 partition_table[*].width_prior 承载）",
        "missing" if not _has_text(pkg, "0 罚") else "equivalent",
        ("pkg cost_model 键集={weights, ordinal_note}，无宽度零罚条目；"
         "允许区间本身在 width_prior（如 P1 [0.6,1.4]），"
         "「区间内调整不计罚」未数据化（合同层缺口，见 fix_candidates）")))

    rows.append(_row(
        "成本模型", "（罚分，仅用于排序，不需要输出数值）",
        "board_brief.cost_model.ordinal_note",
        _vd("仅用于排序" in cm["ordinal_note"] and "不要求输出数值" in cm["ordinal_note"]),
        "pkg ordinal_note=「%s」与 V2 括注同义" % cm["ordinal_note"]))

    # ---------------- 分区表 ----------------
    actual_ids = [e["partition_id"] for e in pkg["partition_table"]]
    pg = next((e for e in pkg["partition_table"]
               if e["partition_id"].startswith("PG")), None)
    gran = part_artifact["granularity_provenance"][0]
    rows.append(_row(
        "分区表", "分区表九行 P1–P9（P7、P9 为既布网络，路径固定，不参与重规划）",
        "partition_table（行数与 id 列表）",
        _vd(actual_ids == V2_PART_IDS),
        ("pkg 实际 %d 行：%s；L1 聚类（先验 %s: min_gap_mm=%s）把同 ptype=ROUTED、"
         "端点距 0.6mm 的 P7/P9 合并为 %s（source_partitions=%s）。工程理由：主粒度="
         "类型×几何邻接聚类是 v5.partition 文档化决定，「既布不重规划」由 ptype=ROUTED"
         "+source_partitions 溯源保留；属设计行为非代码缺陷，不进 fix_candidates"
         % (len(actual_ids), ",".join(actual_ids), gran["principle_id"],
            _fmt(gran["value"]), pg["partition_id"], pg["source_partitions"]))))

    p1 = table["P1"]
    p1_ok = (p1["geometry"]["endpoints"] == V2_PARTS["P1"]["endpoints"]
             and p1["layer_policy"] == "F.Cu" and p1["current_a"] == 1.5
             and p1["width_prior"] == {"w_min": 0.6, "w_max": 1.4}
             and p1["ptype"] == "PWR" and p1["speed_class"] == "power")
    rows.append(_row(
        "分区表", "P1 PWR-5V｜电源 1.5A｜(2,38)→(44,38)｜F.Cu｜允许区间 [0.6,1.4]",
        "partition_table[P1] (geometry/layer_policy/current_a/width_prior/speed_class)",
        _vd(p1_ok),
        ("pkg P1={endpoints [[2.0,38.0],[44.0,38.0]], layer_policy:F.Cu, "
         "current_a:%s, width_prior:[%s,%s], ptype:PWR, speed_class:power} 与 V2 行一致"
         % (_fmt(p1["current_a"]), _fmt(p1["width_prior"]["w_min"]),
            _fmt(p1["width_prior"]["w_max"])))))

    pw_missing = [e["partition_id"] for e in pkg["partition_table"]
                  if "planned_width" in e]
    rows.append(_row(
        "分区表", "各分区行「计划宽」（P1=1.2、P8=0.5；P2–P7/P9 与区间同值）",
        "partition_table[*]（键存在性扫描 planned_width）",
        "missing" if not pw_missing else "equivalent",
        ("pkg 行键集不含 planned_width（L1 工件透传形状无此字段，行注亦未携带）；"
         "V2 计划宽 P1=1.2/P8=0.5 只经冲突通道间接可见（瓶颈 J 项 statement 含 1.0<1.2；"
         "P8 播种缺陷 0.5<0.8 属不产 J 项的 seeded_width_defect，计划宽值在包内完全不可达）"
         "——真实合同缺口，见 fix_candidates")))

    j_bn = _find_j(pkg, subjects=["P1"], kind="disposition")
    if j_bn is not None and "瓶颈" not in p1["note"]:
        v_bottleneck, note_bottleneck = "deviation", (
            "pkg P1 行 note=「%s」（板注未透传）；同一事实改经 j_items[%s] statement="
            "「%s」披露，数值（usable 1.0 < 计划宽 1.2、span [8,10]）与 V2 行注/J4 一致"
            % (p1["note"], j_bn["jid"], j_bn["statement"]))
    elif j_bn is None:
        v_bottleneck, note_bottleneck = "missing", "pkg 无瓶颈 J 项且行注未携带"
    else:
        v_bottleneck, note_bottleneck = "equivalent", "行注携带瓶颈事实"
    rows.append(_row(
        "分区表", "P1 行注：x∈[8,10] 段因两侧焊盘可用宽度仅 1.0",
        "partition_table[P1].note + j_items[bottleneck P1].statement",
        v_bottleneck, note_bottleneck))

    for pid in ("P2", "P3"):
        e = table[pid]
        want = V2_PARTS[pid]
        ok = (e["geometry"]["endpoints"] == want["endpoints"]
              and e["layer_policy"] == "F.Cu"
              and e["width_prior"] == {"w_min": want["prior"][0],
                                       "w_max": want["prior"][1]}
              and e["speed_class"] == want["speed"] and e["ptype"] == want["ptype"])
        rows.append(_row(
            "分区表", "%s %s｜%s→%s｜F.Cu｜宽 %s" % (
                pid, {"P2": "CLK-200M 时钟", "P3": "ETH-MAC 高速 125MHz"}[pid],
                tuple(want["endpoints"][0]), tuple(want["endpoints"][1]),
                want["prior"][0]),
            "partition_table[%s]" % pid,
            _vd(ok),
            ("pkg %s={endpoints %s, layer_policy:F.Cu, width_prior:[%s,%s], "
             "ptype:%s, speed_class:%s} 与 V2 行一致（频率语义入 speed_class 枚举）"
             % (pid, want["endpoints"], _fmt(want["prior"][0]),
                _fmt(want["prior"][1]), want["ptype"], want["speed"]))))

    p4 = table["P4"]
    p4_geom = p4["geometry"]
    p4_ok = (p4_geom.get("centerline") == V2_PARTS["P4"]["centerline"]
             and p4_geom.get("occupancy_band")
             == {"occupancy_mm": 3.3, "copper_band": [30.95, 34.25]}
             and hr["R3"]["unsplittable"] is True and p4["ptype"] == "BUS")
    rows.append(_row(
        "分区表", "P4 BUS-FMC｜8 位并行总线 ribbon｜中心线 (32.6,4)→(32.6,36)｜"
                 "占用 3.3（铜带 x∈[30.95,34.25]）｜R3 整体不可拆分",
        "partition_table[P4].geometry + hard_rules.R3",
        _vd(p4_ok),
        ("pkg P4 centerline/occupancy_band 照板原值透传"
         "（occupancy_mm=3.3、copper_band=[30.95,34.25]）；ribbon 不可拆分由 "
         "R3.unsplittable=true + ptype=BUS/speed_class=bus_8bit 承接"
         "（板注「ribbon 整体」字样未透传，无语义损失）")))

    p56_ok = all(
        table[pid]["geometry"]["endpoints"] == V2_PARTS[pid]["endpoints"]
        and table[pid]["width_prior"] == {"w_min": 0.2, "w_max": 0.2}
        and table[pid]["speed_class"] == "low_speed"
        for pid in ("P5", "P6"))
    rows.append(_row(
        "分区表", "P5/P6 MISC｜低速｜(37,10)→(37,30)、(46,32)→(46,38)｜F.Cu｜宽 0.2",
        "partition_table[P5]/[P6]",
        _vd(p56_ok),
        ("pkg P5/P6={endpoints 照板原值, width_prior:[0.2,0.2], "
         "speed_class:low_speed, layer_policy:F.Cu} 与 V2 行一致")))

    p8 = table["P8"]
    p8_ok = (p8["geometry"]["endpoints"] == V2_PARTS["P8"]["endpoints"]
             and p8["current_a"] == 2.0
             and p8["width_prior"] == {"w_min": 0.8, "w_max": 1.6}
             and p8["ptype"] == "PWR")
    rows.append(_row(
        "分区表", "P8 PWR-3V3-BR｜电源 2.0A｜(44,4)→(48,4)｜计划宽 0.5，允许区间 [0.8,1.6]",
        "partition_table[P8] (geometry/current_a/width_prior)",
        _vd(p8_ok),
        ("pkg P8={endpoints [[44.0,4.0],[48.0,4.0]], current_a:%s, "
         "width_prior:[0.8,1.6]}；区间下限 0.8 与 R1 复算 max(0.4×2.0,0.3)=0.8 一致；"
         "计划宽 0.5 未入表（见 planned_width 行）" % _fmt(p8["current_a"]))))

    rows.append(_row(
        "分区表", "R1：电源网络线宽 ≥ max(0.4×电流A, 0.3) mm",
        "board_brief.hard_rules.R1 + partition_table[*].current_a",
        _vd(hr.get("R1") == V2_RULES["R1"]),
        ("pkg R1={k_a:%s, floor_mm:%s} 与 V2 max(0.4×A,0.3) 一致；"
         "载流 A 逐行在 current_a（P1=%s、P8=%s）"
         % (_fmt(hr["R1"]["k_a"]), _fmt(hr["R1"]["floor_mm"]),
            _fmt(table["P1"]["current_a"]), _fmt(table["P8"]["current_a"])))))

    # ---------------- 冲突扫描说明 ----------------
    has_env_text = _has_text(pkg, "包络")
    diags = [c for c in conf_artifact["conflicts"]
             if c["kind"] == "envelope_overlap_diagnostic"]
    rows.append(_row(
        "冲突扫描说明", "扫描基于保守包络（实际铜几何向外扩 0.6mm 的矩形）",
        "（pkg 全树扫描「包络」文本）",
        "missing" if not has_env_text else "equivalent",
        ("pkg 全树无「包络」字样——扫描口径披露只存在于工件层：L3 实际产出 %d 条 "
         "envelope_overlap_diagnostic（%s），该 kind 按 jitems 合同不产 J 项，"
         "0.6mm 外扩口径未进盲包（合同层缺口，见 fix_candidates）"
         % (len(diags), "、".join("%s %s" % (c["conflict_id"], c["subjects"])
                                  for c in diags)))))

    rows.append(_row(
        "冲突扫描说明", "包络重叠不代表实际冲突，是否真冲突须按 R5 用实际几何自行复核",
        "（pkg 全树扫描复核指令文本）",
        "missing" if not _has_text(pkg, "实际冲突") else "equivalent",
        "pkg 无任何键承载「包络重叠≠实际冲突、按 R5 实际几何复核」指令；"
        "R5 数值本身已数据化（见下行），但复核指令语义未入包"))

    rows.append(_row(
        "冲突扫描说明", "R5 复核基准：任意两不同网络铜（含焊盘）间距 ≥0.5mm",
        "board_brief.hard_rules.R5",
        _vd(hr.get("R5") == V2_RULES["R5"]),
        "pkg R5={min_clearance_mm:%s} = V2 0.5mm" % _fmt(hr["R5"]["min_clearance_mm"])))

    # ---------------- 待裁决项 ----------------
    j1 = _find_j(pkg, subjects=["P2"], kind="disposition", zone="ANA")
    rows.append(_row(
        "待裁决项", "J1：P2 直线路径穿过 ANA。给出处置。",
        "j_items[disposition P2×ANA].statement",
        "equivalent" if j1 is not None else "missing",
        ("pkg %s statement=「%s」与 V2 J1 同一事实（几何坐标更具体）"
         % (j1["jid"], j1["statement"]) if j1 else "pkg 无对应 J 项")))

    j3k = _find_j(pkg, subjects=["P3"], kind="disposition", zone="K1")
    j_joint_c1 = _find_j(pkg, kind="joint", zone="C1")
    j2_verdict = ("missing" if j3k is None
                  else "equivalent" if j_joint_c1 is not None else "deviation")
    rows.append(_row(
        "待裁决项", "J2：P3 纵贯全板穿 K1，唯一通道 C1；F.Cu 过 C1 占用 4.0/4.3，给出通路方案",
        "j_items[disposition P3×K1] + j_items[joint C1]",
        j2_verdict,
        ("穿 K1 处置问句在：j_items[%s]=「%s」；「唯一通道 C1+占用 4.0/4.3 联合求解」"
         "无对应项——本板直线几何 x=16 与走廊窗 rect(30,16)-(36,24) 不相交，"
         "capacity_infeasible 冲突 %d 条、joint 项 %d 个；检测驱动 vs 手工出题口径差"
         % (j3k["jid"] if j3k else "-", j3k["statement"] if j3k else "-",
            n_cap, len([i for i in ji if i["kind"] == "joint"])))))

    j5k = _find_j(pkg, subjects=["P5"], kind="disposition", zone="K2")
    j3_verdict = ("missing" if j5k is None
                  else "equivalent" if j_joint_c1 is not None else "deviation")
    rows.append(_row(
        "待裁决项", "J3：P5 穿 K2；双留 F.Cu 占用 4.7>4.3 不可行；与 J2 共享 C1 必须联合求解排序",
        "j_items[disposition P5×K2] + j_items[joint C1]",
        j3_verdict,
        ("穿 K2 处置问句在：j_items[%s]=「%s」；联合求解与 4.7>4.3 预判无对应项"
         "（capacity_infeasible %d 条；且 v5 statement 合同不向模型预给算术答案）；"
         "检测驱动 vs 手工出题口径差"
         % (j5k["jid"] if j5k else "-", j5k["statement"] if j5k else "-", n_cap))))

    j4 = _find_j(pkg, subjects=["P1"], kind="disposition")
    rows.append(_row(
        "待裁决项", "J4：P1 在 x∈[8,10] 瓶颈段可用宽度 1.0 < 计划宽度 1.2。给出处置。",
        "j_items[bottleneck P1].statement",
        "equivalent" if j4 is not None else "missing",
        ("pkg %s statement=「%s」，数值 1.0<1.2 与 V2 J4 逐值一致"
         % (j4["jid"], j4["statement"]) if j4 else "pkg 无对应 J 项")))

    j5 = _find_j(pkg, kind="joint", zone="C1") or _find_j(pkg, text="额外处置")
    rows.append(_row(
        "待裁决项", "J5：若 P3 走 F.Cu，C1-F.Cu 占用 4.0/4.3，是否需要额外处置？",
        "（j_items 全树扫描 joint C1/「额外处置」）",
        "missing" if j5 is None else "equivalent",
        ("pkg 无对应项：出题者附加的克制测试项，检测驱动下无 capacity_infeasible 冲突"
         "（%d 条）即无 J 项；且 v5 statement 合同不预给 4.0/4.3 算术；"
         "检测驱动 vs 手工出题口径差" % n_cap)))

    j6 = _find_j(pkg, text="包络") or _find_j(pkg, subjects=["P7"]) \
        or _find_j(pkg, subjects=["P1", "P7"])
    rows.append(_row(
        "待裁决项", "J6：P1 与 P7 的保守包络重叠 0.6mm，是否需要处置？",
        "（j_items 全树扫描「包络」/P7 主体）",
        "missing" if j6 is None else "equivalent",
        ("pkg 无对应项，且连 diagnostic 冲突都不产生：v5 包络口径=直线段包围盒±0.6"
         "（中心线基，half_width=0），P1-P7 中心线距 1.3>1.2 不重叠——V2 的 0.6mm 重叠"
         "按铜宽半和口径手算（1.2/2+0.2/2 对 0.7 间距），两口径结论相反；"
         "即使产生 envelope_overlap_diagnostic 也按合同不产 J 项；"
         "检测驱动 vs 手工出题口径差")))

    # ---------------- 路由顺序 ----------------
    ladder = pkg["routing_ladder"]
    rows.append(_row(
        "路由顺序", "按阶梯给出全部 9 个分区的布线顺序：%s；同档位先占用稀缺资源%s者在前；"
                   "仍平手按分区编号字典序" % (V2_LADDER_FIVE, V2_LADDER_C1),
        "routing_ladder",
        _vd(V2_LADDER_FIVE in ladder and V2_LADDER_C1 in ladder
            and "字典序" in ladder),
        ("pkg 逐字=「%s」——五档阶梯与两条平手规则逐字一致；差异两点："
         "「稀缺资源%s」泛化为「稀缺资源（走廊）」；V2「全部 9 个分区」计数语未数据化"
         "（重生成表为 %d 行）"
         % (ladder, V2_LADDER_C1, len(actual_ids)))))

    # ---------------- 输出合同 ----------------
    has_action_enum = _has_text(pkg, "layer_change") or _has_text(pkg, "no_action")
    rows.append(_row(
        "输出合同", "decisions 数组：id/action 枚举 detour|layer_change|narrow|no_action、"
                   "partition、layer 枚举 F.Cu|In1.Cu|B.Cu、detail",
        "output_contract.channels（键存在性扫描 decisions/action 枚举）",
        "missing" if not has_action_enum and "decisions" not in ch else "deviation",
        ("pkg 无 decisions 数组与 action/layer 枚举（全树无 layer_change/no_action 文本）；"
         "pkg 以五通道（ranked_options/ranked_combos/routing_order/defect_scan/"
         "principle_objection）重组输出形状，逐决策动作/层选择由 ranked_options.label "
         "自由文本承载——形状不同构（合同层缺口，见 fix_candidates）")))

    ro = ch["ranked_options"]
    rows.append(_row(
        "输出合同", "ranked_options 至少 3 项，按给定成本模型从优到劣；不可行排最后并标注",
        "output_contract.channels.ranked_options + output_contract.note",
        _vd("不可行" in oc_note and ("至少 3" in oc_note or "3 项" in oc_note)),
        ("pkg channels.ranked_options=[{\"label\":\"…\"}] 形状在；note=「%s」覆盖"
         "「不可行方案排最后并标注」，但「至少 3 项」「按给定成本模型从优到劣」未入 note"
         "（排序语境由 cost_model+ordinal_note 承接）" % oc_note)))

    combo = ch["ranked_combos"][0] if ch["ranked_combos"] else {}
    combo_norm = str(combo.get("P3", "")).replace(" ", "")
    rows.append(_row(
        "输出合同", "joint_solution_J2_J3.ranked_combos：P3/P5 槽位枚举"
                   "「留F.Cu过C1 | 换层B.Cu | 换层In1」，列出全部可行组合",
        "output_contract.channels.ranked_combos",
        "deviation",
        ("V2 硬编码键 joint_solution_J2_J3 泛化为 pkg 通用键 channels.ranked_combos"
         "（命名泛化）；P3/P5 槽位枚举语义一致（去空格后=%s，V2=%s 逐字形态去空格）；"
         "「列出全部可行组合（至少含双留F.Cu/单换层×2/双换层四组合）」的完备性要求未入 note"
         % (combo_norm, V2_COMBO_ENUM_NORM))))

    rows.append(_row(
        "输出合同", "routing_order 数组（示例 [\"P2\"]）",
        "output_contract.channels.routing_order",
        _vd(ch["routing_order"] == ["<partition_id>"]),
        "pkg channels.routing_order=%s 为形状占位，与 V2 示例值同构（泛化占位符）"
        % ch["routing_order"]))

    ds = ch["defect_scan"][0] if ch["defect_scan"] else {}
    rows.append(_row(
        "输出合同", "defect_scan [{subject, rule: R1..R6 或 自相矛盾, note}]，"
                   "只查给定数据自身矛盾（直线路径违规不算缺陷）",
        "output_contract.channels.defect_scan",
        _vd(ds.get("rule") == V2_DEFECT_RULE_ENUM
            and set(ds) == {"subject", "rule", "note"}
            and "只查" in oc_note),
        ("pkg channels.defect_scan 形状与 rule 枚举「%s」逐字一致；"
         "「只查给定数据自身矛盾、各分区直线路径违规不属于数据缺陷」的口径限定未入 note"
         "（note=「%s」）" % (V2_DEFECT_RULE_ENUM, oc_note))))

    rows.append(_row(
        "输出合同", "data_consistency_notes 字符串通道（无则填空字符串）",
        "output_contract.channels（键存在性扫描 data_consistency）",
        "missing" if "data_consistency" not in str(sorted(ch)) else "equivalent",
        "pkg 五通道无 data_consistency_notes（合同层缺口，见 fix_candidates）；"
        "V2 数据自洽备案通道语义无承接键"))

    rows.append(_row(
        "输出合同", "principle_objection：备案未计价原则冲突，不改排序",
        "output_contract.channels.principle_objection + output_contract.note",
        _vd("principle_objection" in ch and "备案" in oc_note
            and "不改排序" in oc_note),
        "pkg 通道在 + note=「…principle_objection 只备案不改排序」与 V2 约束一致"))

    rows.append(_row(
        "输出合同", "最终输出一个 json 代码块；枚举值逐字使用，不得发明新值",
        "output_contract.note",
        _vd("json 代码块" in oc_note and "枚举值逐字使用" in oc_note),
        "pkg note=「%s」覆盖「单一 json 代码块+枚举值逐字」两条约束" % oc_note))

    return rows


# ------------------------------------------------------------------ 主流程

def run_audit():
    """跑真实链生成盲包 + 逐节对账，落盘两产物；返回 (pkg, report)。"""
    template_bytes = open(V2_TEMPLATE_PATH, "rb").read()
    prompt_sha = hashlib.sha256(template_bytes).hexdigest()
    if prompt_sha != fx.SOURCE_SHA256:
        raise SystemExit(
            "V2 模板哈希漂移：现测 %s != 夹具冻结 %s，审计拒绝（转录基准失效）"
            % (prompt_sha, fx.SOURCE_SHA256))

    board = build_audit_board()
    loaded = load_board(board)
    part_artifact = build_partition_artifact(loaded)
    env_artifact = validate_envelope_artifact(
        build_envelope_artifact(loaded, part_artifact))
    conf_artifact = validate_conflicts_artifact(build_conflicts(loaded))
    pkg = validate_pkg(build_pkg(loaded, part_artifact, conf_artifact))
    write_pkg(pkg, PKG_PATH)

    rows = audit_rows(pkg, part_artifact, env_artifact, conf_artifact)
    summary = {v: sum(1 for r in rows if r["verdict"] == v)
               for v in ("equivalent", "deviation", "missing", "extra")}
    report = {
        "audit_version": AUDIT_VERSION,
        "board_id": pkg["board_id"],
        "v2_prompt_sha256": prompt_sha,
        "pkg_board_sha256": pkg["board_sha256"],
        "sections": rows,
        "summary": summary,
        "fix_candidates": [
            "pkg.v1 partition_table 不携带 planned_width（V2 分区行「计划宽」P1=1.2/"
            "P8=0.5 未数据化；P8 播种 R1 缺陷 0.5<0.8 的表内发现素材随之消失，"
            "defect_scan 通道对该缺陷不可达）。partition.py「透传不携带 "
            "planned_width/bottleneck」的「无信息损失」论断仅对 L2 容量核算成立，"
            "对盲包语义有损；是否扩 v5.pkg.v1/v5.partition.v1 合同请主审裁决。",
            "pkg.v1 无焊盘半径/端点所在层字段：V2 板参数「所有端点均为焊盘，半径 "
            "0.15mm，位于其所属层的 F.Cu 面」未数据化，R5 含焊盘的间距复核缺几何基准。",
            "pkg.v1 无冲突扫描口径说明键：V2「保守包络（实际铜几何外扩 0.6mm）；包络"
            "重叠≠实际冲突，须按 R5 用实际几何复核」未入包。且 v5 包络口径=直线段包围盒"
            "±0.6（中心线基，metrics.envelope half_width=0），与 V2 文本口径（铜几何"
            "外扩）存在几何基差——J6 场景结论相反（V2 手算重叠 0.6mm；v5 中心线距 "
            "1.3>1.2 不重叠，diagnostic 冲突为 0）。口径是否统一或在包内披露，请主审裁决。",
            "output_contract.channels 缺 data_consistency_notes 通道，且无 decisions[] "
            "逐项 action 枚举（detour|layer_change|narrow|no_action）与 layer 枚举 "
            "（F.Cu|In1.Cu|B.Cu）；pkg 五通道形状与 V2 输出合同不同构。",
            "cost_model 无「宽度在允许区间内调整 0 罚」条目（区间由 "
            "partition_table[*].width_prior 承载，零罚语义未声明）。",
        ],
    }
    sidecar.write_sidecar(REPORT_PATH, report, GENERATOR, GENERATOR_VERSION,
                          pkg["board_sha256"])
    return pkg, report


def main():
    pkg, report = run_audit()
    print("audit_version: %s" % report["audit_version"])
    print("v2_prompt_sha256: %s" % report["v2_prompt_sha256"])
    print("pkg_board_sha256: %s" % report["pkg_board_sha256"])
    print("pkg written: %s" % PKG_PATH)
    print("report written: %s" % REPORT_PATH)
    print("sections: %d  summary: %s" % (len(report["sections"]),
                                         report["summary"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
