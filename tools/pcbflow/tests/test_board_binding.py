"""P1a 第三腿（pcbflow/board_binding.py）测试：板铜箔 ↔ manifest 绑定核对。

manifest 侧一律用 svg_route_package.build_manifest 构造（真合同形状，
不是手搓 dict），板侧用合成 s-expr 与真实板只读抽样。

覆盖：
- 正向：完全一致 → verify_board_binding 返回 []，binding_report 的
  pending 显式登记 zone/ via_size / net 口径；
- 身份：板上 uuid 被多个铜箔对象共享（路由级 uuid）时，板侧 key 已被
  copper_model 消歧成 `"<uuid>@<digest>"`，manifest 用同一组 key 即可
  1:1 完全配对、**不**产生 `*_paired_ambiguous`；这两个违规只在"同一 key
  仍命中多个板侧节点"（几何全同的残留）这种防御性场景触发；
- fail-closed 负向（任务书要求全项）：篡改坐标（1e-6 零容差）/ 改 layer /
  改 width（3 位量化）/ 改 net / 删一个 segment / 多一个 segment /
  net_map 缺键 / unrepresentable 上报（顶层 arc、坏节点）/ 板文本损坏 /
  manifest 侧形状非法；
- 量化口径：低于量子的差异不报（0.2504 → 3 位与 0.250 同）；
- zone 合同 v2：板 zone ↔ manifest zone 按 zone_id 1:1 配对，核对
  net/layers/outline_mm（6 位零容差）/fill_state/outline_kind；layers 按
  任务书口径**稳定排序后逐项比**（声明顺序无语义，成员/重数零容差）；
  配对成功即从 `pending` 移除旧口径 `zone_contract_v2`；无法配对/多命中按
  既有风格报显式违规（含 `zone_paired_ambiguous` 防御性残留）；fill_sha256/
  fill_points 是派生数据 → 只作 info 信息项，**不得**作为违规依据
  （含板侧填充数据缺失亦不报违规，且改动前后违规计数恒为 0）；
- 真实板：空 manifest 必报 route/via_only_in_board（fail-closed 不空过），
  且 pending 里**不得**再出现 `unrepresentable:duplicate_identity_key`。
"""

import copy
import os
import re

import pytest

import revc_board_fixture
from pcbflow import board_binding as bb, config, copper_model as cm
from pcbflow import svg_route_package as s4

ROUTE_A = "11111111-1111-1111-1111-111111111111"
ROUTE_B = "22222222-2222-2222-2222-222222222222"
VIA_C = "33333333-3333-3333-3333-333333333333"
ZONE_D = "44444444-4444-4444-4444-444444444444"

BOARD = """(kicad_pcb (version 20260206) (generator "pcbnew")
\t(layers
\t\t(0 "F.Cu" signal)
\t\t(2 "B.Cu" signal)
\t\t(4 "In1.Cu" signal)
\t\t(6 "In2.Cu" signal)
\t)
\t(segment
\t\t(start 10 20)
\t\t(end 10 25)
\t\t(width 0.25)
\t\t(layer "F.Cu")
\t\t(net "N1")
\t\t(uuid "11111111-1111-1111-1111-111111111111")
\t)
\t(segment
\t\t(start 10 25)
\t\t(end 12.5 25)
\t\t(width 0.25)
\t\t(layer "F.Cu")
\t\t(net "N1")
\t\t(uuid "22222222-2222-2222-2222-222222222222")
\t)
\t(via buried
\t\t(at 10 22)
\t\t(size 0.7)
\t\t(drill 0.4)
\t\t(layers "F.Cu" "In2.Cu")
\t\t(net "N1")
\t\t(uuid "33333333-3333-3333-3333-333333333333")
\t)
\t(zone
\t\t(net "GND")
\t\t(layer "B.Cu")
\t\t(uuid "44444444-4444-4444-4444-444444444444")
\t\t(hatch edge 0.5)
\t\t(fill yes
\t\t\t(thermal_gap 0.5)
\t\t)
\t\t(polygon
\t\t\t(pts
\t\t\t\t(xy 0 0) (xy 30 0) (xy 30 40) (xy 0 40)
\t\t\t)
\t\t)
\t\t(filled_polygon
\t\t\t(layer "B.Cu")
\t\t\t(pts
\t\t\t\t(xy 0.1 0.1) (xy 29.9 0.1) (xy 29.9 39.9)
\t\t\t)
\t\t)
\t)
)
"""

BLANK = "(kicad_pcb (version 20260206))\n"


def board_obj():
    return {"scenario_id": "SC-P1A-BIND",
            "board": {"bbox_mm": [0.0, 0.0, 40.0, 30.0]},
            "rules": {}, "pads": [], "keepouts": [], "relations": []}


def zone_ref_from_board(board_text):
    """板侧 zone → manifest zone 条目（事实抄自 copper_model，派生填充只作引用）。

    zone_id == 板侧 key（与 route/via 同规）；outline_mm = 轮廓事实；
    fill_sha256/fill_points 是派生数据（合同 v2 标 derived），抄来自板侧只为
    让 manifest 齐备，**不**参与核对判定。
    """
    zones = cm.parse_copper(board_text)["zones"]
    out = []
    for z in sorted(zones, key=lambda e: e["key"]):
        out.append({"zone_id": z["key"], "net_id": z["net"],
                    "layers": list(z["layers"]), "outline_kind": "polygon",
                    "outline_mm": [list(p) for p in z["outline_mm"]],
                    "fill_state": "unknown",
                    "fill_sha256": z["fill_sha256"],
                    "fill_points": z["fill_points"]})
    return out


def ref():
    return {
        "scenario_id": "SC-P1A-BIND",
        "routes": [
            {"route_id": ROUTE_A, "net_id": "N1", "relation_ids": [],
             "line_type": "signal", "parent_id": None, "layer": "F.Cu",
             "width_mm": 0.25, "polyline_mm": [[10, 20], [10, 25]],
             "endpoint_ids": ["A", "B"], "constraint_refs": [],
             "state": "baseline", "source": "baseline"},
            {"route_id": ROUTE_B, "net_id": "N1", "relation_ids": [],
             "line_type": "signal", "parent_id": None, "layer": "F.Cu",
             "width_mm": 0.25, "polyline_mm": [[10, 25], [12.5, 25]],
             "endpoint_ids": ["B", "C"], "constraint_refs": [],
             "state": "baseline", "source": "baseline"},
        ],
        "vias": [
            {"via_id": VIA_C, "net_id": "N1", "parent_id": ROUTE_A,
             "from_layer": "F.Cu", "to_layer": "In2.Cu",
             "center_mm": [10, 22], "drill_mm": 0.4,
             "annular_ring_mm": 0.15},
        ],
        # zone（合同 v2）：与 BOARD 里的 zone 1:1 —— net_id 取板侧 net 名
        # （raw 口径下与板侧逐字相同），fill_state 一律 unknown
        "zones": zone_ref_from_board(BOARD),
    }


def manifest():
    """真合同形状的 manifest（由 build_manifest 生成，含 payload hash）。"""
    return s4.build_manifest(board_obj(), ref())


def shared_uuid_board():
    """板：两个不同几何的 segment 共享同一 uuid（Rev-C 路由级 uuid 同款）。"""
    return BOARD.replace('(uuid "%s")' % ROUTE_B, '(uuid "%s")' % ROUTE_A)


def ref_by_board_keys(board_text):
    """按板侧（消歧后）key 逐节点构造 ref：manifest id == 板 key，1:1。"""
    model = cm.parse_copper(board_text)
    routes = []
    for i, s in enumerate(sorted(model["segments"], key=lambda e: e["key"])):
        routes.append({
            "route_id": s["key"], "net_id": "N1", "relation_ids": [],
            "line_type": "signal", "parent_id": None, "layer": s["layer"],
            "width_mm": s["width"],
            "polyline_mm": [list(s["start"]), list(s["end"])],
            "endpoint_ids": ["E%d" % i, "F%d" % i], "constraint_refs": [],
            "state": "baseline", "source": "baseline"})
    vias = [{"via_id": v["key"], "net_id": "N1",
             "parent_id": routes[0]["route_id"],
             "from_layer": v["layers"][0], "to_layer": v["layers"][1],
             "center_mm": list(v["at"]), "drill_mm": v["drill"],
             "annular_ring_mm": 0.15} for v in model["vias"]]
    return {"scenario_id": "SC-P1A-BIND", "routes": routes, "vias": vias,
            "zones": zone_ref_from_board(board_text)}


def manifest_for(board_text):
    return s4.build_manifest(board_obj(), ref_by_board_keys(board_text))


def has(violations, prefix):
    return any(v.startswith(prefix) for v in violations)


# ----------------------------------------------------------------- 正向

def test_clean_binding_has_no_violations():
    assert bb.verify_board_binding(BOARD, manifest()) == []


def test_report_counts_and_pending():
    rep = bb.binding_report(BOARD, manifest())
    assert rep["violations"] == []
    # v2：zone 已纳入核对，`zone_contract_v2` 口径已清理
    assert "zone_contract_v2" not in rep["pending"]
    assert "zone_fill_derived_not_a_violation_basis" in rep["pending"]
    assert "via_size_mm" in rep["pending"]
    assert "net_basis=raw" in rep["pending"]
    assert rep["identity_basis"] == "kicad_uuid"
    assert re.fullmatch(r"[0-9a-f]{64}", rep["copper_sha256"])
    c = rep["counts"]
    assert c["manifest_segments"] == 2 and c["board_segments"] == 2
    assert c["paired_segments"] == 2 and c["manifest_only_segments"] == 0 \
        and c["board_only_segments"] == 0
    assert c["manifest_vias"] == 1 and c["board_vias"] == 1
    assert c["paired_vias"] == 1
    assert c["manifest_zones"] == 1 and c["board_zones"] == 1
    assert c["board_zone_keys"] == 1 and c["paired_zones"] == 1
    assert c["manifest_only_zones"] == 0 and c["board_only_zones"] == 0
    assert c["board_unrepresentable"] == 0
    # 派生填充数据只作信息项，不作违规依据
    info = rep["info"]["zones"]
    assert info["fill_derived_is_not_a_violation_basis"] is True
    assert info["fill_state_counts"] == {"fresh": 0, "stale": 0, "unknown": 1}
    assert info["fill_fingerprint_missing"] == []


def test_blank_board_empty_manifest_is_clean():
    m = {"routes": [], "vias": []}
    assert bb.verify_board_binding(BLANK, m) == []
    rep = bb.binding_report(BLANK, m)
    assert rep["counts"]["board_segments"] == 0
    assert rep["counts"]["board_zones"] == 0
    assert "zone_fill_derived_not_a_violation_basis" not in rep["pending"]


# ----------------------------------------------------- fail-closed 负向

def test_tampered_coordinate_detected_zero_tolerance():
    text = BOARD.replace("(start 10 20)", "(start 10 20.000001)")
    out = bb.verify_board_binding(text, manifest())
    assert has(out, "route_polyline_mismatch")


def test_tampered_manifest_polyline_detected():
    m = manifest()
    m["routes"][0]["polyline_mm"] = [[10, 20], [10, 25.000001]]
    assert has(bb.verify_board_binding(BOARD, m), "route_polyline_mismatch")


def test_layer_mismatch_detected_both_sides():
    text = BOARD.replace('(layer "F.Cu")\n\t\t(net "N2")', "x")  # no-op guard
    assert text == BOARD
    tampered = BOARD.replace('\t\t(layer "F.Cu")\n\t\t(net "N1")\n\t\t(uuid "%s")'
                             % ROUTE_A,
                             '\t\t(layer "In1.Cu")\n\t\t(net "N1")\n\t\t'
                             '(uuid "%s")' % ROUTE_A)
    assert has(bb.verify_board_binding(tampered, manifest()),
               "route_layer_mismatch")
    m = manifest()
    m["routes"][0]["layer"] = "B.Cu"
    assert has(bb.verify_board_binding(BOARD, m), "route_layer_mismatch")


def test_width_mismatch_detected_and_subquantum_tolerated():
    tampered = BOARD.replace('\t\t(width 0.25)\n\t\t(layer "F.Cu")\n\t\t'
                             '(net "N1")\n\t\t(uuid "%s")' % ROUTE_A,
                             '\t\t(width 0.26)\n\t\t(layer "F.Cu")\n\t\t'
                             '(net "N1")\n\t\t(uuid "%s")' % ROUTE_A)
    out = bb.verify_board_binding(tampered, manifest())
    assert has(out, "route_width_mismatch")
    # 3 位量化：0.2504 与 0.250 同口径 → 不报
    sub = BOARD.replace('(width 0.25)', '(width 0.2504)', 1)
    assert bb.verify_board_binding(sub, manifest()) == []
    m = manifest()
    m["routes"][0]["width_mm"] = 0.35
    assert has(bb.verify_board_binding(BOARD, m), "route_width_mismatch")


def test_net_mismatch_raw_basis():
    tampered = BOARD.replace('(net "N1")\n\t\t(uuid "%s")' % ROUTE_A,
                             '(net "N9")\n\t\t(uuid "%s")' % ROUTE_A)
    out = bb.verify_board_binding(tampered, manifest())
    assert has(out, "route_net_mismatch")
    m = manifest()
    m["routes"][0]["net_id"] = "N5"
    assert has(bb.verify_board_binding(BOARD, m), "route_net_mismatch")


def test_net_map_basis_resolves_and_flags_missing_key():
    ok = {"N1": "N1", "GND": "GND"}   # zone net 亦须在 net_map 内
    assert bb.verify_board_binding(BOARD, manifest(), ok) == []
    # net_map 把 manifest 的 net_id 解析成另一个板侧名字 → 不匹配
    out = bb.verify_board_binding(BOARD, manifest(), {"N1": "GND", "GND": "GND"})
    assert has(out, "route_net_mismatch") and has(out, "via_net_mismatch")
    # 缺键 → net_map_key_missing（route×2 + via×1 + zone×1）
    out = bb.verify_board_binding(BOARD, manifest(), {"OTHER": "N1"})
    assert has(out, "net_map_key_missing")
    assert sum(1 for v in out if v.startswith("net_map_key_missing")) == 4
    rep = bb.binding_report(BOARD, manifest(), ok)
    assert "net_basis=net_map" in rep["pending"]
    # net_map 形状非法 → 违规且不猜（不产生 net 噪声比对）
    out = bb.verify_board_binding(BOARD, manifest(), ["N1"])
    assert len(out) == 1 and has(out, "net_map")


def test_deleted_segment_only_in_manifest():
    text = BOARD.replace("""\t(segment
\t\t(start 10 25)
\t\t(end 12.5 25)
\t\t(width 0.25)
\t\t(layer "F.Cu")
\t\t(net "N1")
\t\t(uuid "22222222-2222-2222-2222-222222222222")
\t)
""", "")
    out = bb.verify_board_binding(text, manifest())
    assert out == ["route_only_in_manifest: %s" % ROUTE_B]
    rep = bb.binding_report(text, manifest())
    assert rep["counts"]["manifest_only_segments"] == 1
    assert rep["counts"]["paired_segments"] == 1


def test_extra_segment_only_in_board():
    text = BOARD.replace("\t(via buried", """\t(segment
\t\t(start 30 30) (end 31 31) (width 0.2)
\t\t(layer "F.Cu") (net "N7")
\t)
\t(via buried""")
    out = bb.verify_board_binding(text, manifest())
    assert len(out) == 1 and out[0].startswith("route_only_in_board: G:")
    rep = bb.binding_report(text, manifest())
    assert rep["counts"]["board_only_segments"] == 1
    assert rep["counts"]["board_segments"] == 3


def test_extra_via_only_in_board_and_deleted_via():
    extra = BOARD.replace("\t(zone", """\t(via
\t\t(at 5 5) (size 0.6) (drill 0.3)
\t\t(layers "F.Cu" "B.Cu") (net "N1")
\t)
\t(zone""")
    out = bb.verify_board_binding(extra, manifest())
    assert len(out) == 1 and out[0].startswith("via_only_in_board: G:")
    removed = BOARD.replace("""\t(via buried
\t\t(at 10 22)
\t\t(size 0.7)
\t\t(drill 0.4)
\t\t(layers "F.Cu" "In2.Cu")
\t\t(net "N1")
\t\t(uuid "33333333-3333-3333-3333-333333333333")
\t)
""", "")
    out = bb.verify_board_binding(removed, manifest())
    assert out == ["via_only_in_manifest: %s" % VIA_C]


def test_via_field_mismatches():
    m = manifest()
    m["vias"][0]["from_layer"] = "B.Cu"
    assert has(bb.verify_board_binding(BOARD, m), "via_from_layer_mismatch")
    m = manifest()
    m["vias"][0]["to_layer"] = "In1.Cu"
    assert has(bb.verify_board_binding(BOARD, m), "via_to_layer_mismatch")
    m = manifest()
    m["vias"][0]["center_mm"] = [10.000001, 22]
    assert has(bb.verify_board_binding(BOARD, m), "via_center_mismatch")
    m = manifest()
    m["vias"][0]["drill_mm"] = 0.5
    assert has(bb.verify_board_binding(BOARD, m), "via_drill_mismatch")
    # 低于量子的 center 差异不报（6 位量化）
    m = manifest()
    m["vias"][0]["center_mm"] = [10.0000001, 22]
    assert bb.verify_board_binding(BOARD, m) == []


def test_shared_uuid_pairs_one_to_one_by_disambiguated_key():
    """板侧 uuid 被同一条 route 的两个 segment 共享 → key 已消歧，1:1 配对。

    manifest 用板侧 key（`"<uuid>@<digest>"`）寻址：两个 route 各配对自己的
    segment，**不得**再出现 route_paired_ambiguous（也不再是"不可表示"）。
    """
    board = shared_uuid_board()
    model = cm.parse_copper(board)
    keys = sorted(s["key"] for s in model["segments"])
    assert len(keys) == 2 and len(set(keys)) == 2
    assert all(k.startswith(ROUTE_A + "@") for k in keys)

    m = manifest_for(board)
    assert bb.verify_board_binding(board, m) == []
    rep = bb.binding_report(board, m)
    c = rep["counts"]
    assert c["board_segments"] == 2 and c["board_segment_keys"] == 2
    assert c["paired_segments"] == 2
    assert c["board_only_segments"] == 0 and c["manifest_only_segments"] == 0
    assert c["paired_vias"] == 1
    assert c["board_identity_disambiguated"] == 2
    assert not any(v.startswith(("route_paired_ambiguous", "via_paired_ambiguous"))
                   for v in rep["violations"])
    assert not any(p.startswith("unrepresentable:") for p in rep["pending"])


def test_shared_uuid_with_bare_uuid_manifest_id_does_not_pair():
    """消歧后裸 uuid 不再是板侧 key：manifest 用裸 uuid 必须配对失败。

    fail-closed 的如实结果 —— 一条 route uuid ↔ 多个板侧对象无法 1:1，
    必须报 only_in_manifest/only_in_board，而不是硬配成歧义。
    """
    board = shared_uuid_board()
    out = bb.verify_board_binding(board, manifest())   # manifest 用 ROUTE_A/ROUTE_B
    assert any(v.startswith("route_only_in_manifest: %s" % ROUTE_A)
               for v in out)
    assert has(out, "route_only_in_board")
    assert not has(out, "route_paired_ambiguous")


def test_paired_ambiguous_is_defensive_residual_only():
    """防御性残留：同 uuid 且几何全同的两个 segment → 消歧后 key 仍相同。

    copper_model 已报 identity_key_collision；配对层不得任取其一，必须报
    route_paired_ambiguous（正常板上此违规为 0）。
    """
    board = shared_uuid_board().replace(
        "(start 10 25)\n\t\t(end 12.5 25)", "(start 10 20)\n\t\t(end 10 25)")
    model = cm.parse_copper(board)
    assert model["counts"]["segments"] == 2
    key = model["segments"][0]["key"]
    seg = model["segments"][0]
    assert key == model["segments"][1]["key"]           # 摘要相同 → key 相同
    assert any(u["kind"] == "identity_key_collision"
               for u in model["unrepresentable"])
    # manifest 只能有一个该 id（route_id 需唯一），板侧却有 2 个同 key 节点
    m = s4.build_manifest(board_obj(), {
        "scenario_id": "SC-P1A-BIND",
        "routes": [{"route_id": key, "net_id": "N1", "relation_ids": [],
                    "line_type": "signal", "parent_id": None,
                    "layer": seg["layer"], "width_mm": seg["width"],
                    "polyline_mm": [list(seg["start"]), list(seg["end"])],
                    "endpoint_ids": ["A", "B"], "constraint_refs": [],
                    "state": "baseline", "source": "baseline"}],
        "vias": [],
    })
    out = bb.verify_board_binding(board, m)
    assert any(v.startswith("route_paired_ambiguous: %s" % key) for v in out)
    rep = bb.binding_report(board, m)
    assert rep["counts"]["paired_segments"] == 0        # 歧义项不参与核对


def test_top_level_arc_reported_as_pending_not_violation():
    text = BOARD.replace("\t(zone", """\t(arc
\t\t(start 1 1) (mid 2 2) (end 3 1) (width 0.2)
\t\t(layer "F.Cu") (net "N1")
\t)
\t(zone""")
    assert bb.verify_board_binding(text, manifest()) == []
    rep = bb.binding_report(text, manifest())
    assert "unrepresentable:arc_track" in rep["pending"]
    assert rep["counts"]["board_unrepresentable"] == 1


def test_zone_pairs_one_to_one_and_no_longer_pending_contract_v2():
    """zone 合同 v2：板 zone ↔ manifest zone 按 zone_id 1:1 配对核对。

    配对成功后 `pending` 里的 `zone_contract_v2` 必须消失（旧口径清理）；
    只剩"派生填充数据不作违规依据"这一显式登记。
    """
    m = manifest()
    assert bb.verify_board_binding(BOARD, m) == []
    rep = bb.binding_report(BOARD, m)
    assert "zone_contract_v2" not in rep["pending"]
    assert "zone_fill_derived_not_a_violation_basis" in rep["pending"]
    assert rep["counts"]["paired_zones"] == 1
    assert rep["counts"]["board_zone_keys"] == 1


def test_zone_only_in_board_and_only_in_manifest():
    # 板侧多一个 zone（manifest 未表达）→ zone_only_in_board
    extra = BOARD.replace("\t(zone", """\t(zone
\t\t(net "GND")
\t\t(layer "In1.Cu")
\t\t(polygon (pts (xy 1 1) (xy 2 1) (xy 2 2)))
\t)
\t(zone""")
    out = bb.verify_board_binding(extra, manifest())
    assert len(out) == 1 and out[0].startswith("zone_only_in_board: G:")
    assert bb.binding_report(extra, manifest())["counts"]["board_only_zones"] == 1
    # 板侧删掉 zone → zone_only_in_manifest
    removed = BOARD.replace("""\t(zone
\t\t(net "GND")
\t\t(layer "B.Cu")
\t\t(uuid "44444444-4444-4444-4444-444444444444")
\t\t(hatch edge 0.5)
\t\t(fill yes
\t\t\t(thermal_gap 0.5)
\t\t)
\t\t(polygon
\t\t\t(pts
\t\t\t\t(xy 0 0) (xy 30 0) (xy 30 40) (xy 0 40)
\t\t\t)
\t\t)
\t\t(filled_polygon
\t\t\t(layer "B.Cu")
\t\t\t(pts
\t\t\t\t(xy 0.1 0.1) (xy 29.9 0.1) (xy 29.9 39.9)
\t\t\t)
\t\t)
\t)
""", "")
    out = bb.verify_board_binding(removed, manifest())
    assert out == ["zone_only_in_manifest: %s" % ZONE_D]


def test_v1_manifest_without_zones_is_fail_closed_on_zoned_board():
    """v1 形状 manifest（无 zones 键）对有 zone 的板：不得假装核对过。"""
    m = manifest()
    del m["zones"]
    out = bb.verify_board_binding(BOARD, m)
    assert out == ["zone_only_in_board: %s" % ZONE_D]


def test_zone_outline_mismatch_zero_tolerance():
    m = manifest()
    m["zones"] = copy.deepcopy(m["zones"])
    m["zones"][0]["outline_mm"][1][0] = 30.000001     # 第 6 位差异
    out = bb.verify_board_binding(BOARD, m)
    assert has(out, "zone_outline_mismatch")
    # 少一个顶点（点数不符）
    m = manifest()
    m["zones"] = copy.deepcopy(m["zones"])
    m["zones"][0]["outline_mm"] = m["zones"][0]["outline_mm"][:3]
    assert has(bb.verify_board_binding(BOARD, m), "zone_outline_mismatch")
    # <3 点 → zone_outline_invalid（多边形不成立）
    m = manifest()
    m["zones"] = copy.deepcopy(m["zones"])
    m["zones"][0]["outline_mm"] = m["zones"][0]["outline_mm"][:2]
    assert has(bb.verify_board_binding(BOARD, m), "zone_outline_invalid")
    # 低于量子的差异（6 位量化）不报
    m = manifest()
    m["zones"] = copy.deepcopy(m["zones"])
    m["zones"][0]["outline_mm"][1][0] = 30.0000001
    assert bb.verify_board_binding(BOARD, m) == []


def test_zone_layers_net_and_kind_mismatches():
    m = manifest()
    m["zones"] = copy.deepcopy(m["zones"])
    m["zones"][0]["layers"] = ["In1.Cu"]
    assert has(bb.verify_board_binding(BOARD, m), "zone_layers_mismatch")
    m = manifest()
    m["zones"] = copy.deepcopy(m["zones"])
    m["zones"][0]["net_id"] = "N9"
    assert has(bb.verify_board_binding(BOARD, m), "zone_net_mismatch")
    m = manifest()
    m["zones"] = copy.deepcopy(m["zones"])
    m["zones"][0]["outline_kind"] = "circle"
    assert has(bb.verify_board_binding(BOARD, m),
               "zone_outline_kind_mismatch")
    # 板侧 zone 的 net 改动（raw 口径下与 manifest 不符）
    tampered = BOARD.replace('(zone\n\t\t(net "GND")', '(zone\n\t\t(net "N9")')
    assert has(bb.verify_board_binding(tampered, manifest()),
               "zone_net_mismatch")
    # net_map 口径：zone net 经 net_map 解析后再比
    assert bb.verify_board_binding(BOARD, manifest(),
                                   {"N1": "N1", "GND": "GND"}) == []
    out = bb.verify_board_binding(BOARD, manifest(),
                                  {"N1": "N1", "GND": "GND"}.copy())
    assert out == []


#: 双层 zone 的合成板（layers 稳定排序口径用；见 R2 任务书第 1 条）
ZONE_2L_BOARD = """(kicad_pcb (version 20260206) (generator "pcbnew")
\t(layers
\t\t(0 "F.Cu" signal)
\t\t(2 "B.Cu" signal)
\t)
\t(zone
\t\t(net "GND")
\t\t(layers "F.Cu" "B.Cu")
\t\t(uuid "44444444-4444-4444-4444-444444444444")
\t\t(polygon
\t\t\t(pts
\t\t\t\t(xy 0 0) (xy 30 0) (xy 30 40) (xy 0 40)
\t\t\t)
\t\t)
\t)
)
"""


def test_zone_layers_compared_as_stable_sorted_multiset():
    """`layers` **稳定排序后逐项比**：声明顺序无语义，成员/重数仍零容差。

    依据 R2 任务书第 1 条（"layers（稳定排序后逐项比）"）。板侧
    `(layers "F.Cu" "B.Cu")` 与 manifest 侧 `["B.Cu", "F.Cu"]` 描述的是
    **同一个 zone 的层集合** → 置换顺序不得报违规（有序逐位比会在此产生
    假阳性）；零容差未被放宽：少一层 / 换一层 / 重复一层都必须
    `zone_layers_mismatch`。
    """
    assert cm.parse_copper(ZONE_2L_BOARD)["zones"][0]["layers"] == \
        ["F.Cu", "B.Cu"]
    m = manifest_for(ZONE_2L_BOARD)
    assert m["zones"][0]["layers"] == ["F.Cu", "B.Cu"]   # 适配层保序
    assert bb.verify_board_binding(ZONE_2L_BOARD, m) == []
    perm = copy.deepcopy(m)
    perm["zones"][0]["layers"] = ["B.Cu", "F.Cu"]        # 仅置换声明顺序
    assert bb.verify_board_binding(ZONE_2L_BOARD, perm) == []
    for bad in (["F.Cu"], ["B.Cu"], ["F.Cu", "In1.Cu"],
                ["F.Cu", "B.Cu", "B.Cu"], ["B.Cu", "B.Cu"]):
        m2 = copy.deepcopy(m)
        m2["zones"][0]["layers"] = bad
        out = bb.verify_board_binding(ZONE_2L_BOARD, m2)
        assert has(out, "zone_layers_mismatch"), (bad, out)
    # 板侧置换顺序（真值侧）同样不报；板侧少一层则报
    board_perm = ZONE_2L_BOARD.replace('(layers "F.Cu" "B.Cu")',
                                       '(layers "B.Cu" "F.Cu")')
    assert board_perm != ZONE_2L_BOARD
    assert bb.verify_board_binding(board_perm, m) == []
    board_less = ZONE_2L_BOARD.replace('(layers "F.Cu" "B.Cu")',
                                       '(layer "F.Cu")')
    assert has(bb.verify_board_binding(board_less, m), "zone_layers_mismatch")


def test_zone_outline_invalid_vertices_fail_closed():
    """轮廓缺失/非法/非数值对一律 zone_outline_invalid（不猜、不静默跳过）。"""
    cases = [["x", 0], [0, 0, 0], "not-a-list", None, [0, None],
             [[0, 0], [1, 1], "bad"]]
    for bad in cases:
        m = manifest()
        m["zones"] = copy.deepcopy(m["zones"])
        m["zones"][0]["outline_mm"] = bad
        out = bb.verify_board_binding(BOARD, m)
        assert has(out, "zone_outline_invalid"), (bad, out)
    # zones 键整体形状非法
    assert has(bb.verify_board_binding(BLANK, {"routes": [], "vias": [],
                                               "zones": {"a": 1}}),
               "manifest.zones")
    # 条目缺 zone_id / zone_id 重复
    m = manifest()
    m["zones"] = copy.deepcopy(m["zones"]) + [{"net_id": "GND"}]
    assert has(bb.verify_board_binding(BOARD, m), "manifest.zones[1]")
    m = manifest()
    m["zones"] = copy.deepcopy(m["zones"])
    m["zones"].append(copy.deepcopy(m["zones"][0]))
    assert has(bb.verify_board_binding(BOARD, m),
               "manifest.zones: zone_id 重复")


def _zone_block(text):
    """取出合成板里唯一顶层 zone 节点的原文（含前导缩进，不含行尾换行）。

    用于构造"两个字节全同的 zone"（同 uuid + 同 net/layers/轮廓/params）：
    只有全同才会让 copper_model 消歧后仍撞键（`identity_key_collision`）。
    """
    i = text.index("\t(zone")
    depth, j = 0, i
    while True:
        if text[j] == "(":
            depth += 1
        elif text[j] == ")":
            depth -= 1
            if depth == 0:
                break
        j += 1
    return text[i:j + 1]


def test_zone_paired_ambiguous_is_defensive_residual_only():
    """同 uuid 且 net/layers/轮廓/params 全同的两个 zone → 消歧后 key 仍相同。

    配对层不得任取其一：必须报 `zone_paired_ambiguous`（正常板上为 0）；
    copper_model 已把它记进 unrepresentable（`identity_key_collision`）。
    """
    blk = _zone_block(BOARD)
    assert blk.startswith("\t(zone") and blk.endswith("\t)")
    two = BOARD.replace(blk, blk + "\n" + blk, 1)
    assert two != BOARD and two.count(blk) == 2
    model = cm.parse_copper(two)
    assert model["counts"]["zones"] == 2
    key = model["zones"][0]["key"]
    assert key == model["zones"][1]["key"]
    assert any(u["kind"] == "identity_key_collision"
               for u in model["unrepresentable"])
    z0 = model["zones"][0]
    m = s4.build_manifest(board_obj(), {
        "scenario_id": "SC-P1A-BIND", "routes": [], "vias": [],
        "zones": [{"zone_id": key, "net_id": "GND",
                   "layers": list(z0["layers"]), "outline_kind": "polygon",
                   "outline_mm": [list(p) for p in z0["outline_mm"]],
                   "fill_state": "unknown"}]})
    out = bb.verify_board_binding(two, m)
    assert any(v.startswith("zone_paired_ambiguous: %s" % key) for v in out)
    rep = bb.binding_report(two, m)
    assert rep["counts"]["paired_zones"] == 0        # 歧义项不参与核对
    assert rep["counts"]["board_zone_keys"] == 1 and \
        rep["counts"]["board_zones"] == 2


def test_zone_fill_derived_changes_never_change_violation_count():
    """反证（R2 任务书第 2 条）：派生填充字段变化**不得**报违规。

    同一块板、同一 manifest：把 manifest 的 fill_sha256/fill_points 改得
    面目全非，并把板侧 filled_polygon 整段删掉 —— 改动前后违规计数**都是
    0**、核对结论不变（派生数据只进 info，不进违规判定）。
    """
    m = manifest()
    before = bb.verify_board_binding(BOARD, m)
    assert before == []
    tampered = copy.deepcopy(m)
    tampered["zones"][0]["fill"] = {"derived": True, "fill_sha256": "0" * 64,
                                    "fill_points": 10 ** 6}
    after_manifest = bb.verify_board_binding(BOARD, tampered)
    assert after_manifest == before == []
    no_fill = BOARD.replace("""\t\t(filled_polygon
\t\t\t(layer "B.Cu")
\t\t\t(pts
\t\t\t\t(xy 0.1 0.1) (xy 29.9 0.1) (xy 29.9 39.9)
\t\t\t)
\t\t)
""", "")
    assert no_fill != BOARD
    both = bb.verify_board_binding(no_fill, tampered)
    assert both == []
    rep = bb.binding_report(no_fill, tampered)
    assert rep["violations"] == [] and rep["counts"]["paired_zones"] == 1
    # 派生字段在 info 里如实登记（缺失即登记，但不升格为违规）
    info = rep["info"]["zones"]
    assert info["fill_fingerprint_missing"] == []
    m_nofp = copy.deepcopy(m)
    m_nofp["zones"][0]["fill"] = {"derived": True, "fill_sha256": None,
                                  "fill_points": None}
    assert bb.verify_board_binding(BOARD, m_nofp) == []
    assert bb.binding_report(BOARD, m_nofp)["info"]["zones"][
        "fill_fingerprint_missing"] == [ZONE_D]


def test_zone_fill_state_checked_but_derived_fill_is_not_a_violation_basis():
    """fill_state 只核声明值合法性；派生填充数据**不得**作为违规依据。"""
    m = manifest()
    m["zones"] = copy.deepcopy(m["zones"])
    m["zones"][0]["fill_state"] = "burnt"
    assert has(bb.verify_board_binding(BOARD, m), "zone_fill_state_invalid")
    # 声明 fresh 且给指纹 → 合法（板侧无重填证据，不因此判违规）
    m = manifest()
    m["zones"] = copy.deepcopy(m["zones"])
    m["zones"][0]["fill_state"] = "fresh"
    m["zones"][0]["fill"] = {"derived": True,
                             "fill_sha256": "a" * 64, "fill_points": 3}
    assert bb.verify_board_binding(BOARD, m) == []
    # 派生填充指纹/点数被改得面目全非 → 仍不得产生任何违规（只作信息项）
    m = manifest()
    m["zones"] = copy.deepcopy(m["zones"])
    m["zones"][0]["fill"] = {"derived": True, "fill_sha256": None,
                             "fill_points": None}
    assert bb.verify_board_binding(BOARD, m) == []
    rep = bb.binding_report(BOARD, m)
    assert rep["info"]["zones"]["fill_fingerprint_missing"] == [ZONE_D]
    # 板侧 zone 的 filled_polygon 整段删掉（派生数据消失）→ 同样不报违规
    no_fill = BOARD.replace("""\t\t(filled_polygon
\t\t\t(layer "B.Cu")
\t\t\t(pts
\t\t\t\t(xy 0.1 0.1) (xy 29.9 0.1) (xy 29.9 39.9)
\t\t\t)
\t\t)
""", "")
    assert no_fill != BOARD
    assert bb.verify_board_binding(no_fill, manifest()) == []


def test_unbalanced_board_text_is_violation():
    out = bb.verify_board_binding("(kicad_pcb (segment (start 1 2)", manifest())
    assert has(out, "board_parse_error")
    assert has(out, "route_only_in_manifest")
    rep = bb.binding_report("(kicad_pcb (segment (start 1 2)", manifest())
    assert rep["violations"] and rep["counts"]["board_segments"] == 0


def test_input_shape_fail_closed():
    assert bb.verify_board_binding(BOARD, []) == ["manifest: 不是对象"]
    assert bb.verify_board_binding(BOARD, None) == ["manifest: 不是对象"]
    assert bb.verify_board_binding(None, manifest()) == \
        ["board_text: 不是字符串"]
    rep = bb.binding_report(None, manifest())
    assert rep["identity_basis"] is None and rep["copper_sha256"] is None
    # manifest.routes 形状非法
    out = bb.verify_board_binding(BOARD, {"routes": {"a": 1}, "vias": []})
    assert has(out, "manifest.routes")
    # route 缺 route_id / 重复 route_id
    m = manifest()
    m["routes"] = copy.deepcopy(m["routes"]) + [{"net_id": "N1"}]
    out = bb.verify_board_binding(BOARD, m)
    assert has(out, "manifest.routes[2]")
    m = manifest()
    m["routes"] = copy.deepcopy(m["routes"])
    m["routes"].append(copy.deepcopy(m["routes"][0]))
    out = bb.verify_board_binding(BOARD, m)
    assert has(out, "manifest.routes: route_id 重复")
    # 无括号的输入不是板文本（防"路径当文本"的假阳性空列表）
    assert bb.verify_board_binding(config.REVC_BOARD, m) == \
        ["board_text: 不含任何 s-expr 节点（疑似把路径或空文本当板文本传入，"
         "拒绝按'空板'处理）"]


def test_violations_are_sorted_and_deterministic():
    tampered = BOARD.replace('(net "N1")', '(net "N9")')
    a = bb.verify_board_binding(tampered, manifest())
    b = bb.verify_board_binding(tampered, manifest())
    assert a == b == sorted(a) and len(a) == 3


# --------------------------------------------------------- 真实板（只读）

needs_board = pytest.mark.skipif(
    not os.path.exists(config.REVC_BOARD), reason="Rev-C board missing")


def real_board_text():
    """真实板只读抽样：以文本读入（board_binding 的入参是板文本）。"""
    with open(config.REVC_BOARD, encoding="utf-8", newline="") as f:
        return f.read()


@needs_board
def test_real_board_empty_manifest_fails_closed(monkeypatch):
    """真实板 + 空 manifest：板上铜箔必须全部配对失败（不空过）。

    计数按**消歧后的全局唯一 key**：Rev-C 落线后（dbfea089）2372 个 segment /
    358 个 via
    各得唯一 key（uuid 共享的 104 个对象被 copper_model 消歧成
    `"<uuid>@<digest>"`），故 key 数 == 节点数；被消歧不是"不可表示"，
    unrepresentable 必须为 0。

    REPAIR-P1 W-5（铜环案 R4 三步法②）：精确计数改钉仓内冻结夹具板
    tests/fixtures/revc-live-dbfea089/（与 2026-09-11 live 板逐字节同，
    sha 锚校验 fail-closed），与 live 板演进解耦；live 板不变量另见
    test_real_board_live_invariants_only。
    """
    monkeypatch.setattr(config, "REVC_BOARD", revc_board_fixture.fixture_board())
    text = real_board_text()
    empty = {"routes": [], "vias": [], "zones": []}
    out = bb.verify_board_binding(text, empty)
    rep = bb.binding_report(text, empty)
    # M1 刷新：counts=dbfea089 夹具板实测 2372/358/消歧 217（原 2026-09-11
    # live 板口径原样保留，仅钉板）
    assert rep["counts"]["board_segment_keys"] == 2372
    assert rep["counts"]["board_via_keys"] == 358
    assert rep["counts"]["board_zone_keys"] == 2
    # 2 个 zone 亦按 v2 合同参与配对 → 空 manifest 下同样 only_in_board
    assert len(out) == 2372 + 358 + 2
    assert has(out, "route_only_in_board") and has(out, "via_only_in_board")
    assert has(out, "zone_only_in_board")
    assert not has(out, "route_paired_ambiguous")
    assert not has(out, "via_paired_ambiguous")
    assert not has(out, "zone_paired_ambiguous")
    assert rep["counts"]["board_segments"] == 2372
    assert rep["counts"]["board_vias"] == 358
    assert rep["counts"]["board_zones"] == 2
    assert rep["counts"]["board_unrepresentable"] == 0
    assert rep["counts"]["board_identity_disambiguated"] == 217
    assert rep["identity_basis"] == "kicad_uuid"
    assert "zone_contract_v2" not in rep["pending"]
    assert "zone_fill_derived_not_a_violation_basis" in rep["pending"]
    assert "via_size_mm" in rep["pending"]
    # 既有"重复身份键"名目必须彻底消失（不再是不可表示）
    assert not any(p.startswith("unrepresentable:") for p in rep["pending"])


@needs_board
def test_real_board_zone_pairing_matches_mirror(monkeypatch):
    """真实板镜像的 manifest（adapter 产出）与板侧 zone 1:1 配对无违规。

    REPAIR-P1 W-5：同上钉冻结夹具板（registry/out 链只读口径不变）。
    """
    monkeypatch.setattr(config, "REVC_BOARD", revc_board_fixture.fixture_board())
    import json
    reg_path = os.path.join(config.OUT_DIR, "revc-a3", "net-registry.json")
    if not os.path.exists(reg_path):
        pytest.skip("net-registry.json missing")
    from pcbflow import board_svg_adapter as ba
    with open(reg_path, encoding="utf-8") as f:
        registry = json.load(f)
    board, ref = ba.build_inputs(config.REVC_BOARD, registry,
                                 scenario_id="SC-ZONE-BIND")
    _svg, m = s4.build(board, ref)
    net_map = {n["net_id"]: n.get("net_name")
               for n in registry["nets"] if isinstance(n, dict)}
    rep = bb.binding_report(real_board_text(), m, net_map)
    assert rep["violations"] == []
    c = rep["counts"]
    assert c["manifest_zones"] == 2 and c["paired_zones"] == 2
    assert c["board_only_zones"] == 0 and c["manifest_only_zones"] == 0
    assert rep["info"]["zones"]["fill_state_counts"]["unknown"] == 2


@needs_board
def test_real_board_is_read_only():
    from pcbflow import hashing
    before = hashing.sha256_file(config.REVC_BOARD)
    bb.binding_report(real_board_text(), {"routes": [], "vias": []})
    assert hashing.sha256_file(config.REVC_BOARD) == before


@needs_board
def test_real_board_live_invariants_only():
    """R4③ live 板不变量用例（REPAIR-P1 W-5）：live 板演进不破坏配对合同。

    只断板无关不变量（在新旧板上都成立），不带精确计数——精确值由钉
    夹具板的用例守护；板变更登记走 design1_proposal 前缀与 R28 live
    登记用例，不由本用例承担。
    """
    text = real_board_text()
    empty = {"routes": [], "vias": [], "zones": []}
    out = bb.verify_board_binding(text, empty)
    rep = bb.binding_report(text, empty)
    c = rep["counts"]
    # 空 manifest：板侧全部铜箔落 only_in_board（fail-closed 不空过）
    assert len(out) == c["board_segments"] + c["board_vias"] + c["board_zones"]
    assert has(out, "route_only_in_board") and has(out, "via_only_in_board")
    assert has(out, "zone_only_in_board")
    # 消歧合同：key 数 == 节点数，零不可表示，零歧义配对
    assert c["board_segment_keys"] == c["board_segments"]
    assert c["board_via_keys"] == c["board_vias"]
    assert c["board_zone_keys"] == c["board_zones"]
    assert c["board_unrepresentable"] == 0
    assert not has(out, "route_paired_ambiguous")
    assert not has(out, "via_paired_ambiguous")
    assert not has(out, "zone_paired_ambiguous")
    assert rep["identity_basis"] == "kicad_uuid"


def test_negative_control_board_tamper_moves_counts():
    """负对照（R28「不得弱化」硬约束检出证明）：向夹具板注入一个 segment
    后，M1 精确计数必须随之移动（2372 → 2373）——计数确实跟踪板字节，
    钉板改造没有把精确断言变成恒真。"""
    tampered = revc_board_fixture.duplicate_first_segment(
        revc_board_fixture.fixture_board_text())
    empty = {"routes": [], "vias": [], "zones": []}
    rep = bb.binding_report(tampered, empty)
    c = rep["counts"]
    assert c["board_segments"] == 2373
    assert c["board_segment_keys"] == 2373
    assert c["board_unrepresentable"] == 0
    # M1 精确值原形态在此板内容下不再成立（检出）
    assert rep["counts"]["board_segments"] != 2372
