# -*- coding: utf-8 -*-
"""V5-R7 内源规则面首批钉值族：per-netclass 间距 + 真实板轮廓。

任务书 V5-R7-NETCLASS-EDGE-TASKBOOK-2026-09-24（sha256-LF[:16]=2c7a2a4a359e4bb8）
§2 W-1..W-4 + §3 验收门 1/2（全量绿+新增钉值；缺省路径逐位一致）。族别：

- **W-1 双源优先序**（任务书 §4 风险①「钉值先行」——开工探针
  out/v5-p5/r7/probe_priority.py P1..P5 的测试面固化）：.kicad_pro
  net_settings.classes 非空 ⇒ 板内 legacy 块整体忽略（P1）；单源板内（P2）；
  两源皆无=零漂移缺省（P3）；源 Default 类 → hard_rules.R5（P4）；多类指派
  列表形（P5）+ stale 成员计数披露 + patterns 非空/坏 JSON/未知类 fail-closed。
- **W-2 类别取值**：drc.check_clearance(net_clearance=) 网对 max（中心线
  口径不变，required_mm=网对值）；route_check e2e（R5 违例按类值）；executor
  障碍栅格保守 max 近似（首版口径：类值>R5 标量的板，介于两者间的间隙被封）。
- **缺省路径等价**：无声明板走旧标量语义——drc 标量分支逐位、route_check
  输出等价、world-frozen 字节级对账（adapter 板 dict / kicad_export 双件
  bytes；模块版本串差按仓库惯例豁免）。
- **W-3 真实板轮廓**：矩形外环 ⇒ OutlineBand 与 workspace 矩形带逐位同式
  （栅格探针全等）；切角边距正反面（轮廓收紧=新违例 / 轮廓大于 workspace=
  旧带假阳消除）；孔环；坏轮廓 fail-closed（开口/自交/孔穿外环/孔出外环/
  不支持图元/弧缺 mid+angle/圆半径非正）与 kicad-cli 同口径；adapter 双弧形
  （KiCad ≥6 三点形 / KiCad ≤5 中心形度制）+ gr_circle 四分之一弧分解 +
  fp_* 旋转换算 + 重复环去重；语料异形板清单钉值锚（Edge_Cuts 含弧/含孔板
  逐板登记——语料不在场则 skip）。
- **导出 per-class**：Default+逐类 classes + netclass_assignments（meta v4
  列表形）；缺类板 .kicad_pro bytes 与冻结版逐字节等；掩蔽窗口逐项消除表
  （.netclass-mask.json 随件落盘：均匀宽度类对消除、混合宽度类对残差披露；
  确定性双跑字节等；A1/EXEC-R3 R3-2 起缺类板也落件——Default 单类最小形）。

stdlib+pytest；无随机无时钟；零渲染零读图；登记类哈希零手抄。
"""
import copy
import hashlib
import importlib
import importlib.util
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from v5 import canonical  # noqa: E402
from v5.adapters import kicad_adapter as ka  # noqa: E402
from v5.adapters.kicad_adapter import AdapterError  # noqa: E402
from v5.board import compute_board_sha256, load_board  # noqa: E402
from v5.drc import (Copper, OutlineBand, VERSION as DRC_VERSION,  # noqa: E402
                    check_clearance, edge_inner_rect, max_net_class_clearance,
                    net_clearance_map, normalize_net_classes,
                    normalize_outline)
from v5.executor import EXECUTOR_VERSION, _Context, execute_candidate  # noqa: E402
from v5.kicad_export import (VERSION as EXPORT_VERSION,  # noqa: E402
                             kicad_pcb_bytes, netclass_mask_table,
                             project_kicad_pro_bytes, write_kicad_pcb)
from v5.route_check import ROUTE_CHECK_VERSION, check_routes  # noqa: E402

CORPUS_MANIFEST = ("E:/ZCodeData/.zcode/workspace/default/tools/"
                   "pcbflow/datasets/corpus-r2-r1/manifest.json")


# ---------------------------------------------------------------- 冻结参照

def _frozen(name):
    """world-frozen 旧代码包成员（字节级零漂移对账参照；不在场则 skip）。"""
    pkg_dir = os.path.join(ROOT, "out", "v5-p5", "r7", "world-frozen", "v5")
    if not os.path.isdir(pkg_dir):
        pytest.skip("world-frozen 参照不在场")
    key = "r7_frozen_v5"
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            key, os.path.join(pkg_dir, "__init__.py"),
            submodule_search_locations=[pkg_dir])
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return importlib.import_module(name, package=key)


def _strip_versions(board_dict):
    """对账豁免面：provenance.adapter（版本升位=仓库惯例）+ board_sha256。"""
    out = copy.deepcopy(board_dict)
    out["provenance"].pop("board_sha256", None)
    out["provenance"].pop("adapter", None)
    return out


# ---------------------------------------------------------------- 板/源夹具

SIG = [{"id": "F.Cu", "kind": "signal", "preferred_direction": "any",
        "available": True},
       {"id": "B.Cu", "kind": "signal", "preferred_direction": "any",
        "available": True}]


def _seg(a, b):
    return {"type": "segment", "start_mm": [a[0], a[1]], "end_mm": [b[0], b[1]]}


def rect_outline(x0, y0, x1, y1):
    """矩形外环（4 段、角序确定）。"""
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return {"outer": [_seg(a, b) for a, b in zip(pts, pts[1:] + pts[:1])],
            "holes": []}


def make_board(board_id="r7", workspace=(0.0, 0.0, 20.0, 20.0),
               parts=(("PA", (2.0, 2.0), (18.0, 2.0)),
                      ("PB", (2.0, 18.0), (18.0, 18.0))),
               nets=(("NA", ("PA",)), ("NB", ("PB",))),
               net_classes=None, outline=None, r5=0.5, validate=True):
    """合成板（wave6 同型）+ V5-R7 兼容键（net_classes/outline_mm）。"""
    partitions = [
        {"partition_id": pid, "ptype": "MISC", "layer_policy": "F.Cu",
         "planned_width": 0.2, "current_a": 0,
         "geometry": {"endpoints": [list(a), list(b)]},
         "speed_class": "low_speed",
         "width_prior": {"w_min": 0.2, "w_max": 0.4}}
        for pid, a, b in parts]
    board = {
        "schema_version": "v5.board.v1",
        "board_id": board_id,
        "stackup": SIG,
        "workspace": {"x_min": workspace[0], "y_min": workspace[1],
                      "x_max": workspace[2], "y_max": workspace[3]},
        "zones": [],
        "partitions": partitions,
        "nets": [{"net_id": nid, "partitions": list(pids)}
                 for nid, pids in nets],
        "hard_rules": {
            "R1": {"floor_mm": 0.3, "k_a": 0.4},
            "R2": {"max_parallel_mm": 5.0, "min_distance_mm": 3.0},
            "R3": {"unsplittable": True},
            "R4": {"max_distance_mm": 2.0, "return_via_required": True},
            "R5": {"min_clearance_mm": r5},
            "R6": {"keepout_zones_forbidden": True, "plane_forbidden": True},
        },
        "principle_registry": [],
        "provenance": {"source_type": "synthetic", "source_uri": "synthetic://r7",
                       "source_sha256": "0" * 64, "adapter": "hand"},
    }
    if net_classes is not None:
        board["net_classes"] = copy.deepcopy(net_classes)
    if outline is not None:
        board["outline_mm"] = copy.deepcopy(outline)
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    if validate:
        return load_board(board)
    return board


def routes_doc(board, entries):
    sha = board["provenance"]["board_sha256"]
    return {"schema_version": "v5.routes.v1", "board_id": board["board_id"],
            "board_sha256": sha, "routes": entries, "negotiation_log": [],
            "provenance": {"generator": "hand", "board_sha256": sha}}


def entry(pid, nid, poly, layer="F.Cu", width=0.2):
    return {"partition_id": pid, "net_id": nid, "layer": layer,
            "polyline": [list(p) for p in poly], "width": width,
            "transition_vias": [], "return_vias": []}


def cand_for(board, cid="C-R7"):
    parts = [p["partition_id"] for p in board["partitions"]]
    return {"candidate_id": cid, "arm": "no-principle",
            "provenance": {"generator": "hand", "rules_consumed": [],
                           "compiled_sha256": "0" * 64},
            "route_order": parts,
            "layer_assignment": {p["partition_id"]: "F.Cu"
                                 for p in board["partitions"]},
            "polylines": {}, "generation_trace": []}


# KiCad 源模板（带净类/轮廓注入位）
KI_SRC = """(kicad_pcb (version 20171130) (host pcbnew "r7")
  (layers (0 F.Cu signal) (31 B.Cu signal))
  (net 0 "")
  (net 1 GND)
  (net 2 SIG)
  (net 3 CLK)
%(netclass)s
%(outline)s
  (module M:FP (layer F.Cu) (at 10 10)
    (pad 1 thru_hole circle (at 0 0) (size 1.6 1.6) (drill 0.8) (layers *.Cu) (net 1 GND))
    (pad 2 thru_hole circle (at 5 0) (size 1.6 1.6) (drill 0.8) (layers *.Cu) (net 2 SIG))
    (pad 3 thru_hole circle (at 10 0) (size 1.6 1.6) (drill 0.8) (layers *.Cu) (net 3 CLK))
  )
)
"""

BOARD_NETCLASS = """  (net_class "Default" "d" (clearance 0.4) (trace_width 0.25)
    (add_net "GND"))
  (net_class "BdHigh" "d" (clearance 0.8) (trace_width 0.5)
    (add_net "SIG"))"""

OUTLINE_RECT = "  (gr_rect (start 0 0) (end 40 40) (layer Edge.Cuts) (width 0.05))"

PRO_CLASSES = {
    "net_settings": {
        "classes": [
            {"name": "Default", "clearance": 0.3, "track_width": 0.2},
            {"name": "ProHigh", "clearance": 1.1, "track_width": 0.6},
        ],
        "meta": {"version": 4},
        "netclass_assignments": {"SIG": ["ProHigh"], "CLK": ["ProHigh"]},
        "netclass_patterns": [],
    },
}


def _write_src(tmp_path, stem, netclass="", outline=OUTLINE_RECT, pro=None,
               pro_raw=None):
    pcb = tmp_path / (stem + ".kicad_pcb")
    pcb.write_text(KI_SRC % {"netclass": netclass, "outline": outline},
                   encoding="utf-8")
    if pro is not None or pro_raw is not None:
        (tmp_path / (stem + ".kicad_pro")).write_text(
            pro_raw if pro_raw is not None else json.dumps(pro),
            encoding="utf-8")
    return str(pcb)


# ---------------------------------------------------------------- 版本钉

def test_versions():
    """V5-R7 版本面（升位理由见各模块 docstring；既有钉已按 R8 F1 先例同步）。"""
    # adapter-fix-r1 双版本串合同：方言路径=v0.6.0（ADAPTER_NAME）；零漂移路径=v0.5.0
    assert ka.ADAPTER_NAME == "kicad-adapter v0.6.0"
    assert ka.ADAPTER_NAME_V050 == "kicad-adapter v0.5.0"
    assert DRC_VERSION == "v5.drc/0.4.0"
    assert ROUTE_CHECK_VERSION == "v5.route_check/0.5.0"
    assert EXECUTOR_VERSION == "v5.executor/0.13.0"  # 0.13.0 同步（engine-fix-r1 阶段一：FX-1 梯内 memo＋FX-2 微优化，纯等价提速；0.11.0=EXEC-R8-B）  # EXEC-R8-B 同步
    assert EXPORT_VERSION == "0.7.0"


# ---------------------------------------------------------------- W-1 双源优先序

def test_p1_pro_wins_over_board_blocks(tmp_path):
    """.kicad_pro net_settings.classes 非空 ⇒ 板内 legacy 块整体忽略（计数披露）。"""
    pcb = _write_src(tmp_path, "both", netclass=BOARD_NETCLASS, pro=PRO_CLASSES)
    board, report = ka.convert_file_with_report(pcb, "both")
    nc = board["net_classes"]
    assert sorted(nc) == ["ProHigh"]
    assert nc["ProHigh"] == {"clearance_mm": 1.1, "width_mm": 0.6,
                             "members": ["CLK", "SIG"]}
    assert board["hard_rules"]["R5"]["min_clearance_mm"] == 0.3   # P4：Default
    assert report["net_class_source"] == "kicad_pro"
    assert report["net_class_board_blocks_ignored"] == 2
    assert report["net_class_unassigned_nets"] == 1               # GND→Default


def test_p2_board_internal_only(tmp_path):
    """无 .kicad_pro ⇒ 板内 (net_class) 块生效（KiCad ≤5 载体）。"""
    pcb = _write_src(tmp_path, "bdonly", netclass=BOARD_NETCLASS)
    board, report = ka.convert_file_with_report(pcb, "bdonly")
    assert board["net_classes"]["BdHigh"]["members"] == ["SIG"]
    assert board["net_classes"]["BdHigh"]["clearance_mm"] == 0.8
    assert board["hard_rules"]["R5"]["min_clearance_mm"] == 0.4
    assert report["net_class_source"] == "kicad_pcb"
    assert report["net_class_count"] == 1
    assert report["net_class_unassigned_nets"] == 2     # GND+CLK=Default 类


def test_p3_no_declaration_zero_drift(tmp_path):
    """两源皆无 ⇒ 无 net_classes 键、R5=引擎缺省 0.5（缺省路径零漂移前提）。"""
    pcb = _write_src(tmp_path, "none", netclass="")
    board, report = ka.convert_file_with_report(pcb, "none")
    assert "net_classes" not in board
    assert board["hard_rules"]["R5"]["min_clearance_mm"] == 0.5
    assert report["net_class_source"] == "none"
    assert report["net_class_unassigned_nets"] == 3
    assert report["net_class_stale_members"] == 0


def test_p5_multiclass_assignment_list_form(tmp_path):
    """netclass_assignments 列表形（KiCad 8.99 meta v4 语料口径）：一网多类收
    全部成员类（有效间距=类 max 由 drc 换算）；stale 网忽略计数不拒整板。"""
    pro = {
        "net_settings": {
            "classes": [
                {"name": "Default", "clearance": 0.25, "track_width": 0.2},
                {"name": "A", "clearance": 0.7, "track_width": 0.3},
                {"name": "B", "clearance": 1.3, "track_width": 0.4},
            ],
            "meta": {"version": 4},
            "netclass_assignments": {"SIG": ["A", "B"], "GHOST": ["A"]},
            "netclass_patterns": [],
        }
    }
    pcb = _write_src(tmp_path, "multi", pro=pro)
    board, report = ka.convert_file_with_report(pcb, "multi")
    nc = board["net_classes"]
    assert nc["A"]["members"] == ["SIG"]
    assert nc["B"]["members"] == ["SIG"]
    assert report["net_class_stale_members"] == 1        # GHOST 不在板网表
    assert board["hard_rules"]["R5"]["min_clearance_mm"] == 0.25


def test_pro_fail_closed_faces(tmp_path):
    """坏 .kicad_pro：JSON 不可解析 / classes 非列表 / patterns 非空 /
    assignments 引用未知类 / clearance 非数值 ⇒ AdapterError（不静默缺省）。"""
    cases = [
        ("badjson", None, "{ not json"),
        ("noclasses", {"net_settings": {"meta": {"version": 4}}}, None),
        ("patterns", {"net_settings": {
            "classes": [{"name": "Default", "clearance": 0.3,
                         "track_width": 0.2}],
            "netclass_patterns": [{"pattern": ".*", "netclass": "Default"}]}},
         None),
        ("unknowncls", {"net_settings": {
            "classes": [{"name": "Default", "clearance": 0.3,
                         "track_width": 0.2}],
            "netclass_assignments": {"SIG": ["Nope"]}}}, None),
        ("badclear", {"net_settings": {
            "classes": [{"name": "Default", "clearance": "x",
                         "track_width": 0.2}]}}, None),
    ]
    for stem, pro, raw in cases:
        pcb = _write_src(tmp_path, stem, pro=pro, pro_raw=raw)
        with pytest.raises(AdapterError):
            ka.convert_file(pcb, stem)


def test_board_block_fail_closed_faces(tmp_path):
    """板内块坏形：缺 clearance/trace_width / 重复声明 ⇒ AdapterError。"""
    base = '  (net_class "X" "d" %s(add_net "SIG"))'
    for body in ("", "(trace_width 0.3) "):
        pcb = _write_src(tmp_path, "b1", netclass=base % body)
        with pytest.raises(AdapterError):
            ka.convert_file(pcb, "b1")
    pcb = _write_src(tmp_path, "b2",
                     netclass=BOARD_NETCLASS + "\n" + BOARD_NETCLASS)
    with pytest.raises(AdapterError):
        ka.convert_file(pcb, "b2")


def test_convert_bytes_has_no_pro_access():
    """convert_bytes 无路径 ⇒ 板内源单可达（文档化局限的钉面）。"""
    data = (KI_SRC % {"netclass": BOARD_NETCLASS,
                      "outline": OUTLINE_RECT}).encode("utf-8")
    board = ka.convert_bytes(data, "bytes-only", "synthetic://x")
    assert board["net_classes"]["BdHigh"]["members"] == ["SIG"]


# ---------------------------------------------------------------- W-2 类别取值

def _coppers():
    a = Copper("NA", "ca", "F.Cu", polyline=[(0.0, 0.0), (10.0, 0.0)])
    b = Copper("NB", "cb", "F.Cu", polyline=[(0.0, 0.7), (10.0, 0.7)])
    c = Copper("NC", "cc", "F.Cu", polyline=[(0.0, 2.0), (10.0, 2.0)])
    return [a, b, c]


def test_r5_pairwise_max_values():
    """网对取值：pair 所需=max(两侧类值)；无类网=缺省标量；中心线口径不变。"""
    viol, checked = check_clearance(_coppers(), 0.5)
    assert checked == 3
    assert viol == []                       # 0.7/1.3/2.0 间隙均 ≥0.5（标量口径）
    nc = {"NA": 0.9, "NB": 0.4, "NC": 0.5}  # NA 类 0.9 > 标量；NB 类 < 标量
    viol2, checked2 = check_clearance(_coppers(), 0.5, net_clearance=nc)
    assert checked2 == 3
    got = {(v.subject_a, v.subject_b): v.data for v in viol2}
    assert set(got) == {("ca", "cb")}
    assert got[("ca", "cb")]["required_mm"] == 0.9        # max(0.9, 0.4)=0.9
    assert got[("ca", "cb")]["gap_mm"] == 0.7
    # 类值高于标量的另一形态：NB=1.6 ⇒ NB 的全部邻对按 1.6 收（ca-cb 的
    # 0.7 间隙与 cb-cc 的 1.3 间隙均违例；2.0 间隙对不受影响）
    nc2 = {"NB": 1.6, "NC": 0.5}
    viol3, _ = check_clearance(_coppers(), 0.5, net_clearance=nc2)
    assert {(v.subject_a, v.subject_b) for v in viol3} ==         {("ca", "cb"), ("cb", "cc")}
    assert all(v.data["required_mm"] == 1.6 for v in viol3)


def test_r5_scalar_path_untouched_by_none_map():
    """net_clearance=None ⇒ 标量分支与 0.3.0 逐位一致（缺省路径）。"""
    viol, checked = check_clearance(_coppers(), 0.5, net_clearance=None)
    assert (viol, checked) == check_clearance(_coppers(), 0.5)


def test_helpers_and_invalid_shapes():
    nc = normalize_net_classes({
        "HS": {"clearance_mm": 0.8, "width_mm": 0.3, "members": ["NB", "NC"]},
        "PWR": {"clearance_mm": 1.2, "width_mm": 0.6, "members": ["NC", "NC2"]},
    })
    assert net_clearance_map(nc, 0.5) == {"NB": 0.8, "NC": 1.2, "NC2": 1.2}
    assert max_net_class_clearance(nc, 0.5) == 1.2
    assert max_net_class_clearance({}, 0.5) == 0.5      # 缺类板原值返回
    assert normalize_net_classes(None) == {}
    with pytest.raises(ValueError):
        normalize_net_classes({"X": {"clearance_mm": 0.5, "width_mm": 0.2,
                                     "members": ["N", "N"]}})   # 成员重复
    with pytest.raises(ValueError):
        normalize_net_classes({"X": {"clearance_mm": -1, "width_mm": 0.2,
                                     "members": []}})
    with pytest.raises(ValueError):
        normalize_net_classes([("X", 1)])               # 非对象


def test_route_check_r5_by_class_e2e():
    """route_check e2e：类板 R5 违例按网对类值（required_mm=1.0）；同几何无类
    板不报——类别取值真的接进了权威检查面。"""
    entries = [entry("PA", "NA", [(2.0, 2.0), (18.0, 2.0)]),
               entry("PB", "NB", [(2.0, 2.7), (18.0, 2.7)])]   # 间隙 0.7
    parts = (("PA", (2.0, 2.0), (18.0, 2.0)),
             ("PB", (2.0, 2.7), (18.0, 2.7)))
    plain = make_board(parts=parts)
    res_plain = check_routes(plain, routes_doc(plain, entries))
    assert [v for v in res_plain["violations"] if v["rule"] == "R5"] == []
    cls = make_board(
        parts=(("PA", (2.0, 2.0), (18.0, 2.0)),
               ("PB", (2.0, 2.7), (18.0, 2.7))),
        net_classes={"HS": {"clearance_mm": 1.0, "width_mm": 0.3,
                            "members": ["NA"]}})
    res_cls = check_routes(cls, routes_doc(cls, entries))
    r5 = [v for v in res_cls["violations"] if v["rule"] == "R5"]
    assert len(r5) == 1
    assert r5[0]["data"]["required_mm"] == 1.0           # max(1.0, 0.5)
    assert r5[0]["data"]["gap_mm"] == 0.7
    assert res_cls["feasible"] is False


def test_route_check_member_net_must_exist():
    """net_classes 成员悬空（指向不存在网）⇒ fail-closed。"""
    bd = make_board(validate=False,
                    net_classes={"HS": {"clearance_mm": 0.9, "width_mm": 0.3,
                                        "members": ["GHOST"]}})
    with pytest.raises(ValueError) as ei:
        check_routes(bd, routes_doc(bd, []))
    assert "net_classes.HS.members" in str(ei.value)


def test_executor_obstacle_conservative_max():
    """executor 障碍栅格保守 max（任务书 §4 风险②首版）：类值 0.9 的板，他网铜
    与候选边间隙 0.7（>0.5 标量、<0.9 类值）⇒ 封；无类板同几何不封。"""
    def _blocked(net_classes):
        bd = make_board(net_classes=net_classes)
        if net_classes is not None:
            bd["provenance"]["board_sha256"] = compute_board_sha256(bd)
            load_board(bd)
        ctx = _Context(bd)
        committed = [Copper("NB", "route:NB:0", "F.Cu",
                            polyline=[(2.0, 2.7), (18.0, 2.7)], half_width=0.1)]
        ctx.commit_entries(
            [entry("PB", "NB", [(2.0, 2.7), (18.0, 2.7)], width=0.2)],
            committed)
        return ctx.edge_blocked("F.Cu", (2.0, 2.0), (18.0, 2.0),
                                "NA", "PA", 0.2)
    assert _blocked(None) is None                    # 0.7 > 0.5 标量：开放
    assert _blocked({"HS": {"clearance_mm": 0.9, "width_mm": 0.3,
                            "members": ["NA"]}}) == "R5"   # 保守 max 封


# ---------------------------------------------------------------- 缺省路径等价

def test_default_path_route_check_equivalence():
    """无声明板 vs net_classes={} 板：检查面输出逐键等价（缺省=旧标量语义）。"""
    parts = (("PA", (2.0, 2.0), (18.0, 2.0)),
             ("PB", (2.0, 2.6), (18.0, 2.6)))
    plain = make_board(parts=parts)
    empty = make_board(parts=parts, net_classes={})
    entries = [entry("PA", "NA", [(2.0, 2.0), (18.0, 2.0)]),
               entry("PB", "NB", [(2.0, 2.6), (18.0, 2.6)])]
    a = check_routes(plain, routes_doc(plain, entries))
    b = check_routes(empty, routes_doc(empty, entries))
    assert a["violations"] == b["violations"]
    assert a["feasible"] == b["feasible"]
    assert a["edge_violations"] == b["edge_violations"] == []
    assert a["hole_violations"] == b["hole_violations"] == []


def test_default_path_frozen_adapter_board_equal():
    """冻结对账：无净类/无轮廓源零新键——板 dict 逐键等（豁免
    provenance.adapter 版本串与 board_sha256）；报告旧键全同值。"""
    frozen_ad = _frozen(".adapters.kicad_adapter")
    src = KI_SRC % {"netclass": "", "outline": ""}
    data = src.encode("utf-8")
    b_old, r_old = frozen_ad.convert_bytes_with_report(data, "d", "synthetic://d")
    b_new, r_new = ka.convert_bytes_with_report(data, "d", "synthetic://d")
    assert _strip_versions(b_new) == _strip_versions(b_old)
    old_keys = set(r_old) - {"board_id"}
    assert {k: r_new[k] for k in old_keys} == {k: r_old[k] for k in old_keys}
    assert set(r_new) - set(r_old) == {
        "net_class_source", "net_class_count", "net_class_unassigned_nets",
        "net_class_stale_members", "net_class_board_blocks_ignored",
        "outline_edges", "outline_arcs", "outline_loops", "outline_holes",
        # adapter-fix-r1（2026-10-23）：方言修复披露键（未激活=空/零，常驻）——
        # 族清单 / drill 椭圆单参修复 / Edge_Cuts 愈合簇
        "adapter_dialect_fixes", "drill_oval_single_param",
        "outline_healed_clusters"}


def test_default_path_frozen_export_bytes_equal():
    """冻结对账：缺类板 .kicad_pro bytes 逐字节等；.kicad_pcb bytes 仅
    generator_version 版本行差（升位惯例）。"""
    frozen_ke = _frozen(".kicad_export")
    bd = make_board()
    doc = routes_doc(bd, [entry("PA", "NA", [(2.0, 2.0), (18.0, 2.0)])])
    assert project_kicad_pro_bytes(bd, doc) == \
        frozen_ke.project_kicad_pro_bytes(bd, doc)
    new = kicad_pcb_bytes(bd, doc).decode("utf-8").splitlines()
    old = frozen_ke.kicad_pcb_bytes(bd, doc).decode("utf-8").splitlines()
    assert len(new) == len(old)
    diff = [(i, a) for i, (a, b) in enumerate(zip(new, old)) if a != b]
    assert len(diff) == 1 and "generator_version" in diff[0][1]


def test_default_path_frozen_route_check_equal():
    """冻结对账：无新键板 check_routes 判定面（violations/feasible/edge/
    hole）逐键等（版本串按惯例差）。"""
    frozen_rc = _frozen(".route_check")
    bd = make_board(parts=(("PA", (2.0, 2.0), (18.0, 2.0)),
                           ("PB", (2.0, 2.45), (18.0, 2.45))))
    doc = routes_doc(bd, [entry("PA", "NA", [(2.0, 2.0), (18.0, 2.0)]),
                          entry("PB", "NB", [(2.0, 2.45), (18.0, 2.45)])])
    a = check_routes(bd, doc)
    b = frozen_rc.check_routes(bd, doc)
    for key in ("violations", "attributed_violations", "feasible",
                "edge_violations", "hole_violations"):
        assert a[key] == b[key]


def test_default_path_executor_routes_deterministic():
    """缺省路径 executor 输出确定性（同板双跑 routes 逐字节等）+ 类板可重复
    （类别取值确定性——保守 max 不引入序漂移）。"""
    bd = make_board()
    r1 = execute_candidate(bd, cand_for(bd))
    r2 = execute_candidate(bd, cand_for(bd))
    assert r1["verdict"] == r2["verdict"]
    assert canonical.canonical_json(r1["routes"]) == \
        canonical.canonical_json(r2["routes"])
    cls = make_board(net_classes={"HS": {"clearance_mm": 0.9, "width_mm": 0.3,
                                         "members": ["NA"]}})
    c1 = execute_candidate(cls, cand_for(cls))
    c2 = execute_candidate(cls, cand_for(cls))
    assert canonical.canonical_json(c1["routes"]) == \
        canonical.canonical_json(c2["routes"])


# ---------------------------------------------------------------- W-3 轮廓

def test_rect_outline_band_equals_workspace_band():
    """矩形轮廓等价（零漂移机制）：OutlineBand(轴对齐矩形外环) 与
    edge_inner_rect 判定在全栅格探针上逐位同值（含擦边/EPS 语义）。"""
    ws = (0.0, 0.0, 40.0, 30.0)
    band = OutlineBand(normalize_outline(rect_outline(0.0, 0.0, 40.0, 30.0)))
    ix0, iy0, ix1, iy1 = edge_inner_rect(ws)
    n = agree = 0
    for i in range(-40, 441, 1):
        for j in range(-30, 331, 2):
            x, y = i / 10.0, j / 10.0
            old = (x < ix0 - 1e-9 or x > ix1 + 1e-9
                   or y < iy0 - 1e-9 or y > iy1 + 1e-9)
            n += 1
            if old == band.point_blocked((x, y)):
                agree += 1
    assert agree == n


def test_rect_outline_board_edge_violations_equal():
    """矩形外环=workspace 的板：edge_violations 与无轮廓板逐项等。"""
    entries = [entry("PA", "NA", [(2.0, 2.0), (18.0, 2.0)])]
    plain = make_board()
    ro = make_board(outline=rect_outline(0.0, 0.0, 20.0, 20.0))
    a = check_routes(plain, routes_doc(plain, entries))
    b = check_routes(ro, routes_doc(ro, entries))
    assert a["edge_violations"] == b["edge_violations"] == []


def chamfer_outline():
    """(20,20) 角切 2mm 斜角的外环：x+y=38 以内为板内。"""
    loop = [(0.0, 0.0), (20.0, 0.0), (20.0, 18.0), (18.0, 20.0), (0.0, 20.0)]
    return {"outer": [_seg(a, b) for a, b in zip(loop, loop[1:] + loop[:1])],
            "holes": []}


def test_chamfer_edge_band_positive_and_negative():
    """切角边距正反面：
    正面（轮廓收紧）——切角三角内点=出板（新违例）、贴斜边 <0.2=入带；
    反面（轮廓放大）——外环大于 workspace 时旧 workspace 带的假阳被消除。"""
    band = OutlineBand(normalize_outline(chamfer_outline()))
    # 正面 1：切角三角内（19.5,19.5：x+y=39>38）⇒ 出板
    assert band.point_blocked((19.5, 19.5)) is True
    # 正面 2：板内贴斜边（(19.0,18.8)：到 x+y=38 距离 0.2/√2≈0.141<0.2）
    assert band.point_blocked((19.0, 18.8)) is True
    # 正面 3：同位无切角（矩形角）合法点（18.8,18.8：距斜边 0.283>0.2）
    assert band.point_blocked((18.8, 18.8)) is False
    # 反面：外环 (0,0)-(40,30) > workspace (5,5)-(35,25)：(4.5,15) 旧带内
    big = OutlineBand(normalize_outline(rect_outline(0.0, 0.0, 40.0, 30.0)))
    ix0, _iy0, _ix1, _iy1 = edge_inner_rect((5.0, 5.0, 35.0, 25.0))
    p = (4.5, 15.0)
    assert (p[0] < ix0) is True                     # 旧 workspace 带判违例
    assert big.point_blocked(p) is False            # 轮廓带消除假阳


def test_chamfer_executor_and_route_check_consume_band():
    """executor 消费：切角带内边/孔位拒布（"edge-clearance"）；route_check
    披露：带内走线点入 edge_violations；同一板无轮廓键=零漂移不报。"""
    parts = (("PA", (2.0, 2.0), (19.0, 18.8)),)
    bd = make_board(outline=chamfer_outline(), parts=parts,
                    nets=(("NA", ("PA",)),))
    ctx = _Context(bd)
    assert ctx.edge_blocked("F.Cu", (19.0, 18.8), (19.4, 19.2),
                            "NA", "PA", 0.2) == "edge-clearance"
    assert ctx.via_blocked((19.0, 18.8), "NA") == "edge-clearance"
    assert ctx.edge_blocked("F.Cu", (18.0, 18.0), (18.5, 18.5),
                            "NA", "PA", 0.2) is None
    parts = (("PA", (2.0, 2.0), (19.0, 18.8)),)
    entries = [entry("PA", "NA", [(2.0, 2.0), (19.0, 18.8)])]
    res = check_routes(bd, routes_doc(bd, entries))
    assert {(v["net_id"], round(v["pos"][0], 6), round(v["pos"][1], 6))
            for v in res["edge_violations"]} == {("NA", 19.0, 18.8)}
    plain = make_board(parts=parts, nets=(("NA", ("PA",)),))
    assert check_routes(plain, routes_doc(plain, entries))["edge_violations"] == []


def test_outline_hole_band():
    """孔环（cutout）：孔内点=出板违例；孔边带内点违例；远离孔合法。"""
    outline = {
        "outer": rect_outline(0.0, 0.0, 20.0, 20.0)["outer"],
        "holes": [rect_outline(8.0, 8.0, 12.0, 12.0)["outer"]],
    }
    band = OutlineBand(normalize_outline(outline))
    assert band.point_blocked((10.0, 10.0)) is True          # 孔内=出板
    assert band.point_blocked((7.9, 10.0)) is True           # 孔边带内
    assert band.point_blocked((7.7, 10.0)) is False          # 距孔边 0.3
    assert band.point_blocked((5.0, 5.0)) is False


def test_bad_outline_fail_closed(tmp_path):
    """坏轮廓 fail-closed（与 kicad-cli 同口径）：开口/自交/孔穿外环/孔出外环/
    不支持图元/弧缺 mid+angle/圆半径非正。"""
    open_outline = ("  (gr_line (start 0 0) (end 20 0) (layer Edge.Cuts)"
                    " (width 0.05))\n"
                    "  (gr_line (start 0 20) (end 0 0) (layer Edge.Cuts)"
                    " (width 0.05))")
    bowtie = "\n".join([
        "  (gr_line (start 0 0) (end 20 20) (layer Edge.Cuts) (width 0.05))",
        "  (gr_line (start 20 20) (end 20 0) (layer Edge.Cuts) (width 0.05))",
        "  (gr_line (start 20 0) (end 0 20) (layer Edge.Cuts) (width 0.05))",
        "  (gr_line (start 0 20) (end 0 0) (layer Edge.Cuts) (width 0.05))"])
    hole_cross = "\n".join([
        "  (gr_rect (start 0 0) (end 20 20) (layer Edge.Cuts) (width 0.05))",
        "  (gr_line (start -5 10) (end 25 10) (layer Edge.Cuts) (width 0.05))",
        "  (gr_line (start 25 10) (end 25 12) (layer Edge.Cuts) (width 0.05))",
        "  (gr_line (start 25 12) (end -5 12) (layer Edge.Cuts) (width 0.05))",
        "  (gr_line (start -5 12) (end -5 10) (layer Edge.Cuts) (width 0.05))"])
    hole_outside = "\n".join([
        "  (gr_rect (start 0 0) (end 20 20) (layer Edge.Cuts) (width 0.05))",
        "  (gr_rect (start 30 30) (end 34 34) (layer Edge.Cuts) (width 0.05))"])
    unsupported = ('  (gr_text "x" (at 10 10) (layer Edge.Cuts)'
                   " (effects (font (size 1 1))))")
    arc_no_mid_angle = ("  (gr_arc (start 0 0) (end 20 0) (layer Edge.Cuts)"
                        " (width 0.05))")
    circle_bad_r = "\n".join([
        "  (gr_circle (center 10 10) (end 10 10) (layer Edge.Cuts)"
        " (width 0.05))",
        "  (gr_rect (start 0 0) (end 20 20) (layer Edge.Cuts) (width 0.05))"])
    cases = [
        ("open", open_outline, "开口"),
        ("bowtie", bowtie, "自交"),
        ("holecross", hole_cross, "自交"),
        ("holeoutside", hole_outside, "不在外环内"),
        ("unsupported", unsupported, "不支持图元"),
        ("arcnomid", arc_no_mid_angle, "弧缺"),
        ("circlebadr", circle_bad_r, "圆半径非正"),
    ]
    for stem, outline_src, expect in cases:
        pcb = _write_src(tmp_path, "bad-" + stem, outline=outline_src)
        with pytest.raises(AdapterError) as ei:
            ka.convert_file(pcb, stem)
        assert expect in str(ei.value), (stem, str(ei.value))


def test_bad_outline_consumer_side_fail_closed():
    """消费侧双保险：normalize_outline 断链/边数不足 fail-closed；route_check
    对坏 outline_mm 板拒检。"""
    with pytest.raises(ValueError):
        normalize_outline({"outer": [_seg((0, 0), (10, 0)),
                                     _seg((0, 5), (0, 0))],
                           "holes": []})
    with pytest.raises(ValueError):
        normalize_outline({"outer": [_seg((0, 0), (10, 0))], "holes": []})
    bd = make_board(outline={"outer": [_seg((0, 0), (10, 0)),
                                      _seg((10, 0), (10, 10)),
                                      _seg((10, 10), (5, 10))],
                              "holes": []}, validate=False)
    with pytest.raises(ValueError):
        check_routes(bd, routes_doc(bd, []))


def test_adapter_outline_forms(tmp_path):
    """轮廓解析族：gr_rect→4 段闭环；KiCad ≤5 中心形弧（(start)=圆心、度制）
    换算三点弧（mid 钉值）；gr_circle→4 段四分之一弧孔环；fp_line 旋转换算；
    重复环去重（badge-pcb 语料形态）；报告计数。"""
    outline = "\n".join([
        "  (gr_rect (start 0 0) (end 40 40) (layer Edge.Cuts) (width 0.05))",
        "  (gr_circle (center 20 20) (end 25 20) (layer Edge.Cuts)"
        " (width 0.05))",
    ])
    pcb = _write_src(tmp_path, "forms", outline=outline)
    board, report = ka.convert_file_with_report(pcb, "forms")
    ol = board["outline_mm"]
    assert len(ol["outer"]) == 4 and len(ol["holes"]) == 1
    assert report["outline_edges"] == 8            # 4 段矩形 + 4 段四分之一弧
    assert report["outline_arcs"] == 4
    assert report["outline_loops"] == 2 and report["outline_holes"] == 1
    for e in ol["holes"][0]:
        assert e["type"] == "arc"
    # KiCad ≤5 中心形弧：圆心 (20,10)、起点 (20,15)、−90°（顺时针）⇒
    # mid=(20+5cos45°, 10+5sin45°)=(23.5355,13.5355)、end=(25,10)
    src_v5arc = "\n".join([
        "  (gr_line (start 15 10) (end 20 15) (layer Edge.Cuts) (width 0.05))",
        "  (gr_arc (start 20 10) (end 20 15) (angle -90) (layer Edge.Cuts)"
        " (width 0.05))",
        "  (gr_line (start 25 10) (end 15 10) (layer Edge.Cuts) (width 0.05))",
    ])
    pcb2 = _write_src(tmp_path, "v5arc", outline=src_v5arc)
    board2, report2 = ka.convert_file_with_report(pcb2, "v5arc")
    arc = board2["outline_mm"]["outer"][1]
    assert arc["type"] == "arc"
    assert [round(v, 4) for v in arc["start_mm"]] == [20.0, 15.0]
    assert [round(v, 4) for v in arc["mid_mm"]] == [23.5355, 13.5355]
    assert [round(v, 4) for v in arc["end_mm"]] == [25.0, 10.0]
    assert report2["outline_arcs"] == 1
    # 重复环去重：同一矩形画两遍 ⇒ 单外环
    pcb3 = _write_src(tmp_path, "dbl",
                      outline=OUTLINE_RECT + "\n" + OUTLINE_RECT)
    _b3, report3 = ka.convert_file_with_report(pcb3, "dbl")
    assert report3["outline_loops"] == 1
    # fp_line 旋转（footprint at 10,10 转 90°）：局部 (0,0)→绝对 (10,10)、
    # 局部 (20,0)→旋 90°（KiCad 口径 rel=(0,−20)）→绝对 (10,−10)
    fp_src = ("  (module M:OUT (layer F.Cu) (at 10 10 90)\n"
              "    (fp_line (start 0 0) (end 20 0) (layer Edge.Cuts)"
              " (width 0.05))\n"
              "    (fp_line (start 20 0) (end 20 20) (layer Edge.Cuts)"
              " (width 0.05))\n"
              "    (fp_line (start 20 20) (end 0 20) (layer Edge.Cuts)"
              " (width 0.05))\n"
              "    (fp_line (start 0 20) (end 0 0) (layer Edge.Cuts)"
              " (width 0.05))\n"
              "  )")
    pcb4 = _write_src(tmp_path, "fp", outline=fp_src)
    board4, _report4 = ka.convert_file_with_report(pcb4, "fp")
    seg0 = board4["outline_mm"]["outer"][0]
    assert [round(v, 6) for v in seg0["start_mm"]] == [10.0, 10.0]
    assert [round(v, 6) for v in seg0["end_mm"]] == [10.0, -10.0]


# ---------------------------------------------------------------- 导出 per-class

def _class_board():
    return make_board(
        net_classes={"HS": {"clearance_mm": 0.9, "width_mm": 0.35,
                            "members": ["NB"]}})


def _class_routes(bd):
    return routes_doc(bd, [entry("PA", "NA", [(2.0, 2.0), (18.0, 2.0)],
                                 width=0.2),
                           entry("PB", "NB", [(2.0, 18.0), (18.0, 18.0)],
                                 width=0.35)])


def test_pro_per_class_writeout():
    """per-class 净类：Default+逐类 classes（逐类 C=max(0,t−w_max_cls)、
    track_width=w_min_cls）+ netclass_assignments 列表形；缺类板旧单类形。"""
    bd = _class_board()
    doc = _class_routes(bd)
    pro = json.loads(project_kicad_pro_bytes(bd, doc).decode("utf-8"))
    classes = {c["name"]: c for c in pro["net_settings"]["classes"]}
    assert set(classes) == {"Default", "HS"}
    # Default：t=0.5、类内网 NA 宽 {0.2} → C=0.3 / track=0.2
    assert classes["Default"] == {"clearance": 0.3, "name": "Default",
                                  "track_width": 0.2}
    # HS：t=0.9、NB 宽 {0.35} → C=0.55 / track=0.35
    assert classes["HS"] == {"clearance": 0.55, "name": "HS",
                             "track_width": 0.35}
    assert pro["net_settings"]["netclass_assignments"] == {"NB": ["HS"]}
    assert pro["board"]["design_settings"]["rules"]["min_track_width"] == 0.2
    # 缺类板：旧单类形（assignments None）
    plain = make_board()
    pro2 = json.loads(project_kicad_pro_bytes(
        plain, routes_doc(plain, [entry("PA", "NA", [(2.0, 2.0), (18.0, 2.0)],
                                        width=0.2)])).decode("utf-8"))
    assert len(pro2["net_settings"]["classes"]) == 1
    assert pro2["net_settings"]["netclass_assignments"] is None


def test_mask_table_elimination():
    """掩蔽窗口逐项消除表：均匀宽度类对窗口消除（residual=0/eliminated）；
    混合宽度类对残差如实披露（Default×HS：t=0.9、宽度 0.2×0.35 ⇒ 0.075）；
    语义注记在件；A1（EXEC-R3 R3-2）起缺类板也落 mask（Default 单类最小形，
    schema_version=2、v5_width_mm 补面——旧「缺类板 → None 不落件」口径废除）。"""
    bd = _class_board()
    doc = _class_routes(bd)
    mt = json.loads(netclass_mask_table(bd, doc).decode("utf-8"))
    assert mt["rule"] == "netclass-mask-v1"
    pairs = {tuple(p["classes"]): p for p in mt["pairs"]}
    assert pairs[("Default", "Default")]["eliminated"] is True
    assert pairs[("HS", "HS")]["eliminated"] is True
    assert pairs[("Default", "Default")]["residual_window_mm"] == 0.0
    dhs = pairs[("Default", "HS")]
    assert dhs["v5_required_mm"] == 0.9
    assert dhs["kicad_clearance_mm"] == 0.55
    assert dhs["residual_window_mm"] == 0.075      # 0.9−(0.2+0.35)/2−0.55
    assert dhs["eliminated"] is False
    assert "唯一内源权威" in mt["semantics"]
    assert set(mt["classes"]) == {"Default", "HS"}
    # A1（EXEC-R3 R3-2，G1 A 口径）：缺类板也落 mask（Default 单类最小形，
    # 原 R5 唯一可信回程载体）；Default v5_width_mm=null=not_available（源
    # Default 线宽不入板模型），schema_version=2 值权威面。
    plain = make_board()
    pdoc = routes_doc(plain, [entry("PA", "NA", [(2.0, 2.0), (18.0, 2.0)])])
    mt2 = json.loads(netclass_mask_table(plain, pdoc).decode("utf-8"))
    assert mt2["schema_version"] == 2
    assert set(mt2["classes"]) == {"Default"}
    assert mt2["classes"]["Default"]["v5_clearance_mm"] == 0.5
    assert mt2["classes"]["Default"]["v5_width_mm"] is None
    assert mt2["empty_net_classes"] == []
    assert mt2["pairs"][0]["classes"] == ["Default", "Default"]


def test_mask_and_pro_determinism():
    """确定性：类板 pro/mask 双跑字节等；canonical 键序化往返稳定。"""
    bd = _class_board()
    doc = _class_routes(bd)
    assert project_kicad_pro_bytes(bd, doc) == project_kicad_pro_bytes(bd, doc)
    assert netclass_mask_table(bd, doc) == netclass_mask_table(bd, doc)
    bd2 = json.loads(canonical.canonical_text(bd))
    doc2 = json.loads(canonical.canonical_text(doc))
    assert project_kicad_pro_bytes(bd2, doc2) == project_kicad_pro_bytes(bd, doc)
    assert netclass_mask_table(bd2, doc2) == netclass_mask_table(bd, doc)


def test_write_kicad_pcb_third_file(tmp_path, monkeypatch):
    """随件落盘：类板与缺类板均写 .netclass-mask.json 第三件（与纯函数一致；
    A1/EXEC-R3 R3-2 起缺类板也落——Default 单类最小形，旧「缺类板不落第三件」
    口径废除，.pcb/.pro 两件本体不变）。"""
    from v5 import sidecar
    monkeypatch.setattr(sidecar, "ALLOWED_ROOTS", (str(tmp_path),))
    bd = _class_board()
    doc = _class_routes(bd)
    target = str(tmp_path / "out" / "x.kicad_pcb")
    write_kicad_pcb(bd, doc, target)
    mask_path = target[:-len(".kicad_pcb")] + ".netclass-mask.json"
    assert os.path.exists(mask_path)
    with open(mask_path, "rb") as f:
        assert f.read() == netclass_mask_table(bd, doc)
    plain = make_board()
    pdoc = routes_doc(plain, [entry("PA", "NA", [(2.0, 2.0), (18.0, 2.0)])])
    target2 = str(tmp_path / "out" / "y.kicad_pcb")
    write_kicad_pcb(plain, pdoc, target2)
    mask_path2 = target2[:-len(".kicad_pcb")] + ".netclass-mask.json"
    assert os.path.exists(mask_path2)
    with open(mask_path2, "rb") as f:
        assert f.read() == netclass_mask_table(plain, pdoc)


def test_pro_fail_closed_unknown_member():
    """导出侧 net_classes 坏成员 fail-closed（drc 单源归一 + 成员耦合校验）。"""
    bd = make_board(validate=False,
                    net_classes={"HS": {"clearance_mm": 0.9, "width_mm": 0.3,
                                        "members": ["GHOST"]}})
    doc = routes_doc(bd, [])
    for fn in (project_kicad_pro_bytes, kicad_pcb_bytes, netclass_mask_table):
        with pytest.raises(ValueError) as ei:
            fn(bd, doc)
        assert "net_classes" in str(ei.value)


# ---------------------------------------------------------------- schema/W-4

def test_schema_accepts_new_keys_and_still_strict():
    """schema：net_classes/outline_mm 兼容键过 load_board；未知键仍拒。"""
    bd = make_board(net_classes={"HS": {"clearance_mm": 0.9, "width_mm": 0.3,
                                        "members": ["NA"]}},
                    outline=rect_outline(0.0, 0.0, 20.0, 20.0))
    assert "net_classes" in bd and "outline_mm" in bd
    bad = make_board(validate=False)
    bad["unexpected_key"] = 1
    with pytest.raises(Exception):
        load_board(bad)


def test_intake_template_registered():
    """W-4 成文在场：intake 模板 + 首两条候选（annular ring/阻焊=暂缓）。"""
    path = os.path.join(ROOT, "tools", "v5_rule_intake.md")
    assert os.path.exists(path)
    text = open(path, encoding="utf-8").read()
    assert "annular ring" in text and "阻焊" in text
    assert text.count("暂缓") >= 2
    assert "掩蔽窗口" in text          # 已入列项回填含 W-2 消除表指针


# ---------------------------------------------------------------- 语料钉值锚

#: 异形板清单（W-3 钉值锚）：corpus-r2-r1 全量实测（2026-10-04，adapter v0.5.0）
#: ——Edge_Cuts 含弧板（板名→弧元素数）与含孔环板（板名→孔数）。
ARC_BOARD_INVENTORY = {
    "anavi-fume-extractor": 4, "anthc": 4, "atmega32u4-breakout": 8,
    "cm5-minima-rev3": 14, "hackrf-one": 14, "m2-pcie-adapter": 3,
    "om-flexgrid-v4-rigid-pcb": 4, "ottercast-audio-v2": 6,
    "pmod-bme280": 4, "pmod-crypto": 4, "pmod-i2c24io": 4, "pslab-v6": 1,
    "scalenode-cm4-baseboard": 4, "stm32-ds2480-emu": 4, "thatmicpre-v2": 8,
    "thunderbolt-pcie-adapter": 1, "tinytapeout-demo": 4, "tmp108": 20,
    "torxhat": 6, "tt06-fpga-ice40up5k": 4, "vga-panel-breakout": 4,
}
HOLE_BOARD_INVENTORY = {
    "badge-pcb": 5, "thatmicpre-v2": 3, "tmp108": 4, "vga-panel-breakout": 2,
}
#: fail-closed 披露面：badgeleds 语料原始副本 42µm 开口轮廓（本批起拒——
#: 中央板目录的清洗副本无此问题）；throwing-star 无铜层=既有失败（冻结版同拒）。
KNOWN_FAIL_BOARDS = {"badgeleds-do-electronics": "开口",
                     # throwing-star-pro「铜层」已移出：adapter-fix-r1（2026-10-23）
                     # FA-5a legacy 层名族修复后转 ok（回归账 fail→ok=15 之一）。
                     }


@pytest.fixture(scope="module")
def corpus_converted():
    if not os.path.exists(CORPUS_MANIFEST):
        pytest.skip("corpus-r2-r1 语料不在场（异形板清单钉值锚跳过）")
    with open(CORPUS_MANIFEST, encoding="utf-8") as f:
        manifest = json.load(f)
    base = os.path.dirname(CORPUS_MANIFEST)
    want = (set(ARC_BOARD_INVENTORY) | set(HOLE_BOARD_INVENTORY)
            | set(KNOWN_FAIL_BOARDS) | {"ice40hx1k-evb-rev-b"})
    out = {}
    for item in manifest["boards"]:
        bid = item["board_id"]
        if bid not in want:
            continue
        pcb = [f for f in item["files"] if f.endswith(".kicad_pcb")]
        path = os.path.join(base, item["dir"], pcb[0])
        with open(path, "rb") as f:
            assert hashlib.sha256(f.read()).hexdigest() == \
                item["board_file_sha256"]      # 源哈希对账（禁手抄核对）
        try:
            out[bid] = ("ok",) + ka.convert_file_with_report(path, bid)
        except AdapterError as exc:
            out[bid] = ("fail", str(exc))
    return out


def test_corpus_arc_board_inventory(corpus_converted):
    """Edge_Cuts 含弧板逐板登记（任务书 W-3 钉值锚）。"""
    for bid, arcs in sorted(ARC_BOARD_INVENTORY.items()):
        status, *rest = corpus_converted[bid]
        assert status == "ok", (bid, rest)
        assert rest[1]["outline_arcs"] == arcs, bid
        assert rest[1]["outline_loops"] >= 1, bid


def test_corpus_hole_board_inventory(corpus_converted):
    """孔环板登记（外环+孔环多环模型）。"""
    for bid, holes in sorted(HOLE_BOARD_INVENTORY.items()):
        status, *rest = corpus_converted[bid]
        assert status == "ok", (bid, rest)
        board, report = rest
        assert report["outline_holes"] == holes, bid
        assert len(board["outline_mm"]["holes"]) == holes


def test_corpus_known_failures_disclosed(corpus_converted):
    """已知失败面如实披露（不静默）。"""
    for bid, expect in sorted(KNOWN_FAIL_BOARDS.items()):
        status, *rest = corpus_converted[bid]
        assert status == "fail", bid
        assert expect in rest[0], (bid, rest[0])


def test_corpus_double_run_determinism(corpus_converted):
    """双跑确定性（含弧+非凸轮廓板 torxhat / 含孔板 tmp108）：同源双转换
    board_sha256 逐位等。"""
    with open(CORPUS_MANIFEST, encoding="utf-8") as f:
        manifest = json.load(f)
    base = os.path.dirname(CORPUS_MANIFEST)
    by_id = {b["board_id"]: b for b in manifest["boards"]}
    for bid in ("torxhat", "tmp108"):
        item = by_id[bid]
        pcb = [f for f in item["files"] if f.endswith(".kicad_pcb")][0]
        path = os.path.join(base, item["dir"], pcb)
        b1 = ka.convert_file(path, bid)
        b2 = ka.convert_file(path, bid)
        assert b1["provenance"]["board_sha256"] == \
            b2["provenance"]["board_sha256"]
        status, *rest = corpus_converted[bid]
        assert b1["provenance"]["board_sha256"] == \
            rest[0]["provenance"]["board_sha256"]


def test_corpus_rect_board_outline_shape(corpus_converted):
    """矩形语料板（ice40）：4 段外环、无孔、缺省净类——轮廓面最小形态。"""
    status, board, report = corpus_converted["ice40hx1k-evb-rev-b"]
    assert status == "ok"
    assert report["outline_edges"] == 4
    assert board["outline_mm"]["holes"] == []
    assert "net_classes" not in board
