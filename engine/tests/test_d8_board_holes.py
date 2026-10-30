# -*- coding: utf-8 -*-
"""V5-D8 单测：板固孔全量入模与世界换版（board.holes[]）。

覆盖（PREREG-D8 §2.7 冻结口径）：
  - schema：holes[] 可选键逐项结构（circle/oval/size_mm 条件必带/additionalProperties）
  - adapter：TH/NPTH/oval 解析、oval 保守外接圆、缺/非法 drill fail-closed、
    恒落键、report 三计数、绝对坐标含 footprint 旋转
  - 钉值锚（主审全板普查，LEAD-REVIEW-D7-HALT §2）：pmod-bme280=31 PTH+2 NPTH、
    pmod-crypto=31 PTH+0 NPTH、thatmicpre-v2=215 PTH（含 3 oval）+4 NPTH
    （corpus 源 sha 对账 A_LAYER_PREREG 冻结值；对不上=停线件）
  - drc：HOLE_TO_HOLE_MM=0.25 钉值、hole_via_blocked/hole_track_blocked 谓词
    （bme280 wave6 违例例复算）、hole_inherent_pairs、check_hole_keepout
  - executor 0.6.0：贴孔过孔拒布（零豁免，含端点孔=via-in-pad 拒）、贴孔走线
    拒布（异孔）、端点豁免可达（走线连自身端点焊盘孔合法）、holes=[] 向后
    兼容（edge_blocked/via_blocked 无孔行为不变）、exhaustion 归因
    hole-keep-out 类
  - route_check 0.4.0：hole_violations 恒在场披露通道（via/track 两 face、
    不入 feasible）
  - 分类器 0.5.0：hole_to_hole items 含 via→engine、两项均非 via→
    board-inherent；DRC_CATEGORIES 五元
"""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

from v5 import drc as D
from v5.adapters import kicad_adapter as KA
from v5.board import load_board
from v5.route_check import check_routes

try:
    import p5_holdout_ledger as ledger
except ImportError:
    ledger = None

# ---------------------------------------------------------------- 合成夹具

LAYERS = """(kicad_pcb (version 20221018)
  (layers (0 F.Cu signal) (31 B.Cu signal))
  (net 0 "")
  (net 1 GND)
  (net 2 SIG)
  %s
)"""

# 四 pad：TH circle / TH oval / NPTH / SMD（不入清单）；footprint 旋转 90°。
HOLES_FP = """
  (module M:FP (layer F.Cu) (at 10 10 90)
    (pad 1 thru_hole circle (at 2 0) (size 1.6 1.6) (drill 0.8) (layers *.Cu *.Mask) (net 1 GND))
    (pad 2 thru_hole oval (at 4 0) (size 2.0 1.2) (drill oval 1.6 0.9) (layers *.Cu *.Mask) (net 1 GND))
    (pad 3 np_thru_hole circle (at 6 0) (size 1.0 1.0) (drill 1.0) (layers *.Cu *.Mask))
    (pad 4 smd rect (at 8 0) (size 1.0 1.0) (layers F.Cu))
    (pad 5 thru_hole circle (at -2 0) (size 1.6 1.6) (drill 0.8) (layers *.Cu *.Mask) (net 2 SIG))
  )"""


def _convert_fp(fp_text, board_id="holes-mini"):
    board, report = KA.convert_bytes_with_report(
        (LAYERS % fp_text.strip()).encode("utf-8"), board_id, "synthetic://holes")
    return board, report


class TestAdapterHoles:
    def test_counts_and_report(self):
        board, rep = _convert_fp(HOLES_FP)
        assert rep["holes_pth"] == 3
        assert rep["holes_npth"] == 1
        assert rep["holes_oval"] == 1
        assert len(board["holes"]) == 4

    def test_always_present_key(self):
        smd_only = """(kicad_pcb (version 20221018)
  (layers (0 F.Cu signal) (31 B.Cu signal))
  (net 0 "")
  (net 1 GND)
  (module M:FP (layer F.Cu) (at 10 10)
    (pad 4 smd rect (at 1 0) (size 1.0 1.0) (layers F.Cu) (net 1 GND))
  ))"""
        board, rep = KA.convert_bytes_with_report(
            smd_only.encode("utf-8"), "holes-smd", "synthetic://smd")
        assert board["holes"] == []
        assert rep["holes_pth"] == 0 and rep["holes_npth"] == 0 \
            and rep["holes_oval"] == 0

    def test_circle_item_shape(self):
        board, _ = _convert_fp(HOLES_FP)
        circles = [h for h in board["holes"] if h["shape"] == "circle"
                   and h["plated"]]
        assert len(circles) == 2
        for h in circles:
            assert "size_mm" not in h
            assert h["drill_mm"] == 0.8
        # 绝对坐标（KiCad 口径 R(θ)·local）：fp (10,10,90°) + R(90°)·(2,0)
        # = (10,10) + (0,−2) = (10,8)
        assert [round(v, 9) for v in circles[0]["pos_mm"]] == [10.0, 8.0]

    def test_oval_outer_circle(self):
        board, _ = _convert_fp(HOLES_FP)
        ovals = [h for h in board["holes"] if h["shape"] == "oval"]
        assert len(ovals) == 1
        assert ovals[0]["drill_mm"] == pytest.approx(1.6)   # max(1.6, 0.9)
        assert ovals[0]["size_mm"] == [1.6, 0.9]
        assert ovals[0]["plated"] is True

    def test_npth_flag(self):
        board, _ = _convert_fp(HOLES_FP)
        npth = [h for h in board["holes"] if h["plated"] is False]
        assert len(npth) == 1 and npth[0]["drill_mm"] == 1.0

    def test_missing_drill_fail_closed(self):
        bad = """
  (module M:FP (layer F.Cu) (at 10 10)
    (pad 1 thru_hole circle (at 1 0) (size 1.6 1.6) (layers *.Cu *.Mask) (net 1 GND))
  )"""
        with pytest.raises(KA.AdapterError, match="drill"):
            _convert_fp(bad)

    def test_bad_drill_value_fail_closed(self):
        bad = """
  (module M:FP (layer F.Cu) (at 10 10)
    (pad 1 thru_hole circle (at 1 0) (size 1.6 1.6) (drill -0.5) (layers *.Cu *.Mask) (net 1 GND))
  )"""
        with pytest.raises(KA.AdapterError, match="非正"):
            _convert_fp(bad)

    def test_drill_offset_fail_closed(self):
        bad = """
  (module M:FP (layer F.Cu) (at 10 10)
    (pad 1 thru_hole circle (at 1 0) (size 1.6 1.6) (drill 0.8 (offset 0.1 0)) (layers *.Cu *.Mask) (net 1 GND))
  )"""
        with pytest.raises(KA.AdapterError, match="offset"):
            _convert_fp(bad)

    def test_load_board_roundtrip(self):
        board, _ = _convert_fp(HOLES_FP)
        load_board(board)   # schema + 跨字段 + 哈希链 fail-closed 通过


class TestSchema:
    """schema_loader 为 stdlib 最小实现（无 exclusiveMinimum/allOf/if-then）：
    drill_mm 正值与 oval 必带 size_mm 的合同由 adapter fail-closed（生产侧）
    与 drc.normalize_holes（消费侧）承担，schema 层只锁结构/enum/额外键。"""

    def test_schema_rejects_bad_shape(self):
        import v5.schema_loader as SL
        board, _ = _convert_fp(HOLES_FP)
        board["holes"][0]["shape"] = "square"
        with pytest.raises(SL.SchemaViolation):
            SL.validate(board, SL.load_schema("board.v1.schema.json"),
                        SL.default_registry(), "")

    def test_schema_rejects_extra_key(self):
        import v5.schema_loader as SL
        board, _ = _convert_fp(HOLES_FP)
        board["holes"][0]["extra"] = 1
        with pytest.raises(SL.SchemaViolation):
            SL.validate(board, SL.load_schema("board.v1.schema.json"),
                        SL.default_registry(), "")

    def test_production_contracts(self):
        # drill_mm 正值：schema minimum 0 放行 0，消费侧 fail-closed 拒
        #（负例见 test_normalize_fail_closed）；生产侧合同：oval 恒带 size_mm
        board, _ = _convert_fp(HOLES_FP)
        ovals = [h for h in board["holes"] if h["shape"] == "oval"]
        assert ovals and all("size_mm" in h for h in ovals)

    def test_holes_optional(self):
        import v5.schema_loader as SL
        board, _ = _convert_fp(HOLES_FP)
        del board["holes"]                    # 缺键=旧语义
        SL.validate(board, SL.load_schema("board.v1.schema.json"),
                    SL.default_registry(), "")


class TestDrcHoleRules:
    def test_pinned_value(self):
        assert D.HOLE_TO_HOLE_MM == 0.25

    def test_via_pred_bme280_case(self):
        # wave6 bme280 违例例：孔心距 0.283，板固孔 r=0.4，via 侧 0.3 →
        # 0.283 < 0.4+0.25+0.3 拒（kicad 报 0.0000 同源复算）
        assert D.hole_via_blocked((0.0, 0.0), 0.4, (0.283, 0.0), 0.3) is True
        # 远离：0.283+2 > 0.95 → 不拒
        assert D.hole_via_blocked((0.0, 0.0), 0.4, (3.0, 0.0), 0.3) is False

    def test_track_pred(self):
        assert D.hole_track_blocked((0.0, 0.0), 0.4, (-1.0, 0.0), (1.0, 0.0),
                                    0.15) is True     # 穿心
        assert D.hole_track_blocked((0.0, 0.0), 0.4, (-1.0, 0.0), (1.0, 5.0),
                                    0.15) is False    # 远离

    def test_inherent_pairs(self):
        holes = [(0.0, 0.0, 0.4), (0.7, 0.0, 0.4)]   # 边缘距 -0.1
        assert D.hole_inherent_pairs(holes) == [(0, 1, pytest.approx(-0.1, abs=1e-9))]
        holes = [(0.0, 0.0, 0.4), (5.0, 0.0, 0.4)]
        assert D.hole_inherent_pairs(holes) == []

    def test_check_hole_keepout(self):
        holes = [(0.0, 0.0, 0.4)]
        vs = D.check_hole_keepout(holes, [("N1", "PT-1", (0.283, 0.0))], 0.3)
        assert len(vs) == 1 and vs[0].rule == "hole_to_hole"
        assert vs[0].data["required_mm"] == 0.25
        assert D.check_hole_keepout(holes, [("N1", "PT-1", (3.0, 0.0))], 0.3) == []

    def test_normalize_fail_closed(self):
        with pytest.raises(ValueError):
            D.normalize_holes([{"pos_mm": [0, 0], "drill_mm": 0}])
        assert D.normalize_holes(None) == []
        assert D.normalize_holes([]) == []
        assert D.normalize_holes([{"pos_mm": [1, 2], "drill_mm": 0.8,
                                   "plated": True, "shape": "circle"}]) \
            == [(1.0, 2.0, 0.4)]


# ---------------------------------------------------------------- executor 面

def _mk_board(holes, endpoints=((-5.0, 0.0), (5.0, 0.0))):
    """最小合成板：两网 GND/SIG、两分区、给定 holes。"""
    def part(pid, net, eps):
        return {"partition_id": pid, "ptype": "MISC",
                "geometry": {"endpoints": [list(eps[0]), list(eps[1])]},
                "layer_policy": "any",
                "width_prior": {"w_min": 0.3, "w_max": 1.0},
                "current_a": 0, "speed_class": "unknown"}
    board = {
        "schema_version": "v5.board.v1", "board_id": "hole-exec-mini",
        "stackup": [{"id": "F.Cu", "kind": "signal",
                     "preferred_direction": "any", "available": True},
                    {"id": "B.Cu", "kind": "signal",
                     "preferred_direction": "any", "available": True}],
        "workspace": {"x_min": -10.0, "y_min": -10.0, "x_max": 10.0, "y_max": 10.0},
        "zones": [],
        "partitions": [part("PT-GND", "GND", endpoints),
                       part("PT-SIG", "SIG", endpoints)],
        "nets": [{"net_id": "GND", "partitions": ["PT-GND"]},
                 {"net_id": "SIG", "partitions": ["PT-SIG"]}],
        "hard_rules": {
            "R1": {"k_a": 0.4, "floor_mm": 0.3},
            "R2": {"min_distance_mm": 3.0, "max_parallel_mm": 5.0},
            "R3": {"unsplittable": True},
            "R4": {"return_via_required": True, "max_distance_mm": 2.0},
            "R5": {"min_clearance_mm": 0.5},
            "R6": {"plane_forbidden": True, "keepout_zones_forbidden": True}},
        "principle_registry": [],
        "holes": holes,
    }
    from v5.board import compute_board_sha256
    board["provenance"] = {
        "source_type": "synthetic", "source_uri": "synthetic://hole-exec",
        "source_sha256": "0" * 64, "adapter": "test", "board_sha256": ""}
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    return board


class TestExecutorKeepout:
    def _ctx(self, holes):
        from v5.executor import _Context
        return _Context(_mk_board(holes))

    def test_via_near_hole_blocked(self):
        ctx = self._ctx([{"pos_mm": [0.0, 0.0], "drill_mm": 0.8,
                          "plated": True, "shape": "circle"}])
        assert ctx.via_blocked((0.0, 0.0), "SIG") == "hole-keep-out"   # 叠孔
        assert ctx.via_blocked((0.5, 0.0), "SIG") == "hole-keep-out"   # 0.5<0.4+0.25+0.3
        assert ctx.via_blocked((2.0, 0.0), "SIG") != "hole-keep-out"   # 2.0>0.95

    def test_via_endpoint_hole_no_exemption(self):
        # 端点孔（GND 分区端点 (-5,0)）上放过孔=via-in-pad 叠孔：零豁免拒布
        ctx = self._ctx([{"pos_mm": [-5.0, 0.0], "drill_mm": 0.8,
                          "plated": True, "shape": "circle"}])
        assert ctx.via_blocked((-5.0, 0.0), "GND") == "hole-keep-out"

    def test_track_near_hole_blocked(self):
        ctx = self._ctx([{"pos_mm": [0.0, 0.0], "drill_mm": 0.8,
                          "plated": True, "shape": "circle"}])
        r = ctx.edge_blocked("F.Cu", (-1.0, 0.0), (1.0, 0.0), "SIG",
                             "PT-SIG", 0.3)
        assert r == "hole-keep-out"     # 穿心（豁免只及端点 (-5,0)/(5,0)）

    def test_track_endpoint_hole_exempted(self):
        # 走线连自身端点焊盘孔：端点豁免（合法铜连接）
        ctx = self._ctx([{"pos_mm": [-5.0, 0.0], "drill_mm": 0.8,
                          "plated": True, "shape": "circle"}])
        r = ctx.edge_blocked("F.Cu", (-5.0, 0.0), (-3.0, 0.0), "GND",
                             "PT-GND", 0.3)
        assert r != "hole-keep-out"

    def test_no_holes_backward_compat(self):
        ctx0 = self._ctx([])
        assert ctx0.holes == []
        # 无孔时走线/过孔判定不含 hole-keep-out
        r = ctx0.edge_blocked("F.Cu", (-1.0, 0.0), (1.0, 0.0), "SIG",
                              "PT-SIG", 0.3)
        assert r != "hole-keep-out"
        assert "hole-keep-out" not in str(ctx0.via_blocked((0.0, 0.0), "SIG"))

    def test_exhaustion_cause_class(self):
        from v5.executor import _exhaustion_cause
        ctx = self._ctx([{"pos_mm": [0.0, 0.0], "drill_mm": 0.8,
                          "plated": True, "shape": "circle"}])
        cause = _exhaustion_cause(ctx, "PT-SIG", "SIG", 0.3,
                                  (-1.0, 0.0), (1.0, 0.0))
        assert cause.startswith("hole-keep-out")
        # 端点豁免：直连段只在端点孔附近（自身端点）→ 不归 hole-keep-out
        ctx2 = self._ctx([{"pos_mm": [-5.0, 0.0], "drill_mm": 0.8,
                           "plated": True, "shape": "circle"}])
        cause2 = _exhaustion_cause(ctx2, "PT-GND", "GND", 0.3,
                                   (-5.0, 0.0), (-4.5, 0.0))
        assert not cause2.startswith("hole-keep-out")


# ---------------------------------------------------------------- route_check 面

class TestRouteCheckHoleViolations:
    def _doc(self, board, vias=(), polyline=((-5.0, 0.0), (5.0, 0.0)),
             pid="PT-SIG", net="SIG"):
        from v5.board import compute_board_sha256
        sha = compute_board_sha256(board)
        return {
            "schema_version": "v5.routes.v1", "board_id": board["board_id"],
            "board_sha256": sha, "negotiation_log": [],
            "provenance": {"generator": "test", "board_sha256": sha},
            "routes": [{"net_id": net, "partition_id": pid, "layer": "F.Cu",
                        "width": 0.3, "polyline": [list(p) for p in polyline],
                        "transition_vias": [list(v) for v in vias],
                        "return_vias": []}],
        }

    def test_via_face(self):
        board = _mk_board([{"pos_mm": [0.0, 0.0], "drill_mm": 0.8,
                            "plated": True, "shape": "circle"}])
        cr = check_routes(board, self._doc(board, vias=((0.0, 0.0),)))
        assert any(h["face"] == "via" and h["pos"] == [0.0, 0.0]
                   for h in cr["hole_violations"])

    def test_track_face_and_endpoint_exempt(self):
        board = _mk_board([{"pos_mm": [0.0, 0.0], "drill_mm": 0.8,
                            "plated": True, "shape": "circle"}])
        cr = check_routes(board, self._doc(board))
        assert any(h["face"] == "track" for h in cr["hole_violations"])
        # 端点孔豁免：孔=分区端点 (-5,0) 且首段起于该端点 → 该孔不记 track face
        board2 = _mk_board([{"pos_mm": [-5.0, 0.0], "drill_mm": 0.8,
                             "plated": True, "shape": "circle"}])
        cr2 = check_routes(board2, self._doc(board2))
        assert cr2["hole_violations"] == []

    def test_key_always_present_not_in_feasible(self):
        board = _mk_board([])
        cr = check_routes(board, self._doc(board))
        assert cr["hole_violations"] == []
        assert "hole_violations" in cr


# ---------------------------------------------------------------- 分类器

class TestClassifier:
    def _classify(self, items):
        import run_p5_board as M
        rows, counts = M.classify_kicad_violations(
            {"violations": [{"type": "hole_to_hole", "severity": "error",
                             "description": "d", "items": items}]},
            {"nets": [{"net_id": "A"}, {"net_id": "B"}]}, {})
        return rows[0]["category"], counts["classified"]

    def test_engine_class(self):
        cat, _ = self._classify([
            {"description": "过孔 Net-(A)", "pos": {"x": 1, "y": 2}},
            {"description": "焊盘 Net-(B)", "pos": {"x": 1, "y": 2}}])
        assert cat == "hole_to_hole-engine"

    def test_board_inherent_class(self):
        cat, _ = self._classify([
            {"description": "焊盘 Net-(A)", "pos": {"x": 3, "y": 4}},
            {"description": "焊盘 Net-(B)", "pos": {"x": 3, "y": 4}}])
        assert cat == "hole_to_hole-board-inherent"

    def test_categories_tuple(self):
        import run_p5_board as M
        assert M.DRC_CATEGORIES == (
            "config-gap", "contract-artifact", "genuine",
            "hole_to_hole-engine", "hole_to_hole-board-inherent")


# ---------------------------------------------------------------- 钉值锚（A 层真实板）

ANCHOR = {
    "pmod-bme280": (31, 2, 0),
    "pmod-crypto": (31, 0, 0),
    "thatmicpre-v2": (215, 4, 3),
}


@pytest.mark.skipif(ledger is None, reason="ledger 不可用")
@pytest.mark.parametrize("board_id", sorted(ANCHOR))
def test_pinned_hole_counts(board_id):
    """钉值锚（主审全板普查；对不上=停线件——PREREG-D8 §1）。"""
    src = ledger.source_path_for(board_id)
    with open(src, "rb") as f:
        data = f.read()
    import hashlib
    assert hashlib.sha256(data).hexdigest() \
        == ledger.A_LAYER_PREREG[board_id]["sha256"], "源 sha 与预注册不符"
    board, rep = KA.convert_bytes_with_report(data, board_id, src)
    pth, npth, oval = ANCHOR[board_id]
    assert (rep["holes_pth"], rep["holes_npth"], rep["holes_oval"]) \
        == (pth, npth, oval), "钉值锚对不上（主审普查 vs adapter 计数）"
    assert len(board["holes"]) == pth + npth
