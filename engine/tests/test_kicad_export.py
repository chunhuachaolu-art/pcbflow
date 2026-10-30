# -*- coding: utf-8 -*-
"""KiCad 写回导出器测试（P4-G3：写回导出 round-trip 读→写→读语义等）。

覆盖：
- 确定性：同输入双跑字节等；board/routes dict 键序变化（PS 稳定性口径）不变；
  provenance 头（host 行）无日期；
- **round-trip 核心**（write → v5.adapters.kicad_adapter.convert_file 读回）：
  走线几何逐段逐层逐网相等（start/end/width/layer/net 全字段、repr 逐位）、
  过孔位置逐点逐网相等、网络表一致（net_id 集合与顺序）、adapter report 计数；
- **round-trip 范围逐字披露**：board 侧抽象层（partitions/zones/principle_registry/
  width_prior/hard_rules/stackup 元数据/negotiation_log/workspace 数值）不在
  语义等断言范围——导出器不复刻它们（分区抽象只以 anchor pad 端点形式进入
  网表落链）。单分区网读回端点逐位相等属超范围加分断言（anchor 几何推论），
  多分区网读回被 adapter 合并为单分区，按披露不断言其端点；
- fail-closed：schema_version / board_id / board_sha256（含 provenance 内层）/
  未知网 / 未知分区 / 分区不属于该网 / 未知层 / 折线与孔位形状 / 宽度非法 /
  板无 net，全部 ValueError 带键路径；sidecar 越界 SidecarViolation；
- board 只读；写盘测试 monkeypatch sidecar.ALLOWED_ROOTS → tmp_path（不污染
  真实 out/）。零 LLM API、零网络；不装不调 kicad-cli（外权威半边由主审处置）。
"""
import copy
import json
import os

import pytest

from fixtures_v2 import build_v2_board
from v5 import canonical, sidecar
from v5.adapters.kicad_adapter import (
    convert_bytes,
    convert_file,
    parse_sexpr,
    sanitize_net_id,
)
from v5.board import compute_board_sha256, load_board
from v5.kicad_export import (
    GENERATOR,
    VERSION,
    ExportError,
    kicad_pcb_bytes,
    write_kicad_pcb,
)

# --------------------------------------------------------------- 夹具

# 源板走 adapter 产出（provenance 落链真实）：3 铜层、2 网、单分区每网。
_FIXTURE_PCB = """(kicad_pcb
  (version 20241229)
  (layers (0 "F.Cu" signal) (2 "B.Cu" signal) (4 "In1.Cu" signal))
  (net 0 "")
  (net 1 "GND")
  (net 2 "SIG")
  (module M:FP (layer "F.Cu") (at 10 10)
    (pad 1 thru_hole circle (at 1 0) (size 2 2) (drill 1) (layers *.Cu) (net 1 GND))
    (pad 2 thru_hole circle (at -1 0) (size 2 2) (drill 1) (layers *.Cu) (net 2 SIG)))
)
"""


@pytest.fixture(scope="module")
def board():
    return convert_bytes(_FIXTURE_PCB.encode("utf-8"), "exp-fixture",
                         "synthetic://exp-fixture")


def _routes_doc(bd, entries, **overrides):
    doc = {
        "schema_version": "v5.routes.v1",
        "board_id": bd["board_id"],
        "board_sha256": bd["provenance"]["board_sha256"],
        "routes": entries,
        "negotiation_log": [],
        "provenance": {"generator": "v5.executor/0.1.0",
                       "board_sha256": bd["provenance"]["board_sha256"]},
    }
    doc.update(overrides)
    return doc


def _entry(**kw):
    base = {"partition_id": "PT-SIG", "net_id": "SIG", "layer": "F.Cu",
            "polyline": [[9.0, 10.0], [20.0, 10.0], [20.0, 24.0]], "width": 0.2,
            "transition_vias": [[20.0, 24.0]], "return_vias": [[18.0, 24.0]]}
    base.update(kw)
    return base


def _hand_board(nets, partitions, board_id="hand-exp", workspace=None,
                validate=True):
    """自造合法板（synthetic provenance；load_board 落链）。"""
    bd = {
        "schema_version": "v5.board.v1",
        "board_id": board_id,
        "stackup": [
            {"id": "F.Cu", "kind": "signal", "preferred_direction": "any",
             "available": True},
            {"id": "B.Cu", "kind": "signal", "preferred_direction": "any",
             "available": True},
        ],
        "workspace": workspace or {"x_min": 0.0, "y_min": 0.0,
                                   "x_max": 40.0, "y_max": 30.0},
        "zones": [],
        "partitions": partitions,
        "nets": nets,
        "hard_rules": {
            "R1": {"k_a": 0.4, "floor_mm": 0.3},
            "R2": {"min_distance_mm": 3.0, "max_parallel_mm": 5.0},
            "R3": {"unsplittable": True},
            "R4": {"return_via_required": True, "max_distance_mm": 2.0},
            "R5": {"min_clearance_mm": 0.5},
            "R6": {"plane_forbidden": True, "keepout_zones_forbidden": True},
        },
        "principle_registry": [],
        "provenance": {"source_type": "synthetic", "source_uri": "synthetic://hand",
                       "source_sha256": "0" * 64, "adapter": "hand"},
    }
    bd["provenance"]["board_sha256"] = compute_board_sha256(bd)
    if validate:
        load_board(bd)
    return bd


def _roundtrip(tmp_path, bd, routes):
    """write（tmp 落盘）→ adapter convert_file 读回。"""
    data = kicad_pcb_bytes(bd, routes)
    p = tmp_path / "exp.kicad_pcb"
    p.write_bytes(data)
    return convert_file(str(p), bd["board_id"]), data


# ------------------------------------------------- 导出件文本抽取（判定参照）

def _kids(node, head):
    return [it for it in node[1:] if type(it) is list and it and it[0] == head]


def _first(node, head):
    got = _kids(node, head)
    assert len(got) == 1, head
    return got[0]


def _xy(node):
    return (float(node[1]), float(node[2]))


def _extract(data):
    """从导出 bytes 抽 (net_names, segments, vias)。float(token) 逐位还原。"""
    root = parse_sexpr(data.decode("utf-8"))
    net_names = {}
    for n in _kids(root, "net"):
        net_names[int(n[1])] = n[2]
    segments = []
    for s in _kids(root, "segment"):
        segments.append({
            "start": _xy(_first(s, "start")),
            "end": _xy(_first(s, "end")),
            "width": float(_first(s, "width")[1]),
            "layer": _first(s, "layer")[1],
            "net": net_names[int(_first(s, "net")[1])],
        })
    vias = []
    for v in _kids(root, "via"):
        vias.append({
            "at": _xy(_first(v, "at")),
            "layers": tuple(_first(v, "layers")[1:]),
            "net": net_names[int(_first(v, "net")[1])],
        })
    return net_names, segments, vias


def _expected_segments(routes):
    out = []
    for r in routes["routes"]:
        pts = r["polyline"]
        for a, b in zip(pts[:-1], pts[1:]):
            out.append({
                "start": (float(a[0]), float(a[1])),
                "end": (float(b[0]), float(b[1])),
                "width": float(r["width"]),
                "layer": r["layer"],
                "net": r["net_id"],
            })
    return out


def _expected_vias(routes, bd):
    span = (bd["stackup"][0]["id"], bd["stackup"][-1]["id"])
    out = []
    for r in routes["routes"]:
        for p in (r.get("transition_vias") or []) + (r.get("return_vias") or []):
            out.append({"at": (float(p[0]), float(p[1])), "layers": span,
                        "net": r["net_id"]})
    return out


# --------------------------------------------------------------- 确定性

def test_bytes_deterministic_double_run(board):
    routes = _routes_doc(board, [_entry()])
    first = kicad_pcb_bytes(board, routes)
    second = kicad_pcb_bytes(board, routes)
    assert first == second
    assert isinstance(first, bytes) and first


def test_bytes_stable_under_dict_key_order(board):
    """PS 稳定性口径：board/routes 经 canonical json 往返（键序字母序化）后字节等。"""
    routes = _routes_doc(board, [_entry()])
    bd2 = json.loads(canonical.canonical_text(board))
    routes2 = json.loads(canonical.canonical_text(routes))
    assert kicad_pcb_bytes(bd2, routes2) == kicad_pcb_bytes(board, routes)


def test_header_provenance_fixed_no_date(board):
    data = kicad_pcb_bytes(board, _routes_doc(board, []))
    text = data.decode("utf-8")
    assert text.startswith("(kicad_pcb (version 20171130) (host v5.kicad_export ")
    assert "generator=%s" % GENERATOR in text
    assert "generator_version=%s" % VERSION in text
    assert "board_id=exp-fixture" in text
    assert "board_sha256=%s" % board["provenance"]["board_sha256"] in text
    # 固定 generator 行、禁日期：无 ISO 日期样 token（语料风格版本号 20171130 除外）。
    assert "2026-" not in text and "20260913" not in text


def test_export_replicates_only_manufacturable_view(board):
    """披露断言：抽象层不复刻——无 zone/principle_registry/width_prior 结构。"""
    data = kicad_pcb_bytes(board, _routes_doc(board, [_entry()]))
    text = data.decode("utf-8")
    assert "(zone" not in text
    assert "principle_registry" not in text
    assert "width_prior" not in text
    assert "negotiation_log" not in text
    # 可制造走线视图的必备结构在场：segment/via/板框 gr_rect@Edge.Cuts。
    for head in ("(segment ", "(via ", "(gr_rect ", "(layers ", "(net "):
        assert head in text


# --------------------------------------------------------------- round-trip 核心

def test_roundtrip_netlist_order_and_ids(board, tmp_path):
    """网络表一致：读回 net_id 集合与顺序 == 原板（含未布网，anchor 落链）。"""
    routes = _routes_doc(board, [_entry()])  # 只布 SIG；GND 未布也必须在网表
    reread, data = _roundtrip(tmp_path, board, routes)
    assert [n["net_id"] for n in reread["nets"]] == ["GND", "SIG"]
    net_names, _segs, _vias = _extract(data)
    assert {k: v for k, v in net_names.items() if k != 0} == {1: "GND", 2: "SIG"}
    assert net_names[0] == ""  # net 0 未连接网照 KiCad 惯例声明、adapter 跳过


def test_roundtrip_segments_exact_per_segment_layer_net(board, tmp_path):
    """走线几何逐段逐层逐网相等：全字段（start/end/width/layer/net）逐一对照。"""
    routes = _routes_doc(board, [
        _entry(),  # SIG @F.Cu 2 段 + 2 孔
        _entry(partition_id="PT-GND", net_id="GND", layer="B.Cu", width=0.4,
               polyline=[[11.0, 10.0], [11.0, 20.0]],
               transition_vias=[], return_vias=[]),
        _entry(partition_id="PT-SIG", net_id="SIG", layer="In1.Cu", width=0.25,
               polyline=[[20.0, 24.0], [30.0, 24.0], [30.0, 0.5]],
               transition_vias=[], return_vias=[]),
    ])
    reread, data = _roundtrip(tmp_path, board, routes)
    _net_names, segments, _vias = _extract(data)
    assert segments == _expected_segments(routes)
    # 同层同网分段数核对（防抽取口径自证）：SIG/F.Cu=2、SIG/In1.Cu=2、GND/B.Cu=1
    from collections import Counter
    counts = Counter((s["net"], s["layer"]) for s in segments)
    assert counts == {("SIG", "F.Cu"): 2, ("SIG", "In1.Cu"): 2, ("GND", "B.Cu"): 1}
    assert reread["schema_version"] == "v5.board.v1"


def test_roundtrip_vias_exact_positions_and_nets(board, tmp_path):
    """过孔位置逐点逐网相等：transition 与 return 都按输入序落孔。"""
    routes = _routes_doc(board, [
        _entry(transition_vias=[[20.0, 24.0], [9.0, 10.0]],
               return_vias=[[18.0, 24.0], [7.5, 10.0]]),
        _entry(partition_id="PT-GND", net_id="GND", layer="B.Cu", width=0.4,
               polyline=[[11.0, 10.0], [11.0, 20.0]],
               transition_vias=[[11.0, 20.0]], return_vias=[]),
    ])
    _reread, data = _roundtrip(tmp_path, board, routes)
    _net_names, _segments, vias = _extract(data)
    expected = _expected_vias(routes, board)
    assert len(vias) == len(expected) == 5
    assert vias == expected


def test_roundtrip_via_spans_full_stackup(board, tmp_path):
    """via = 全叠层通孔：(layers <首层> <尾层>) == (F.Cu, B.Cu)。"""
    routes = _routes_doc(board, [_entry()])
    _reread, data = _roundtrip(tmp_path, board, routes)
    _net_names, _segments, vias = _extract(data)
    assert all(v["layers"] == ("F.Cu", "B.Cu") for v in vias)


def test_roundtrip_adapter_report_counts(board, tmp_path):
    """adapter report 计数对账：segment/via/net/footprint(=2×分区 anchor)。"""
    routes = _routes_doc(board, [_entry()])
    reread, data = _roundtrip(tmp_path, board, routes)
    # convert_file 不回 report；用 convert_bytes_with_report 对同一 bytes 复算。
    from v5.adapters.kicad_adapter import convert_bytes_with_report
    _b, report = convert_bytes_with_report(data, board["board_id"], "synthetic://rt")
    assert report["net_count"] == 2
    assert report["segment_count"] == 2
    assert report["via_count"] == 2
    # V5-R1 翻转（2026-09-25）：单 pad 退化网 pad_terminals 双项→单项（逐
    # pad 化），导出 anchor 每网 1 份——footprint/pad 计数 4→2（R1-REPORT §7）
    assert report["footprint_count"] == len(board["partitions"]) == 2
    assert report["pad_count"] == report["netted_pad_count"] == 2


def test_roundtrip_single_partition_endpoints_bitexact(board, tmp_path):
    """超范围加分断言（披露：非 round-trip 必答项）：单分区网读回端点逐位相等。"""
    routes = _routes_doc(board, [_entry()])
    reread, _data = _roundtrip(tmp_path, board, routes)
    orig = {n["net_id"]: n["partitions"][0] for n in board["nets"]}
    parts = {p["partition_id"]: p for p in reread["partitions"]}
    for nid, pid in orig.items():
        rid = "PT-" + sanitize_net_id(nid)
        assert parts[rid]["geometry"]["endpoints"] == \
            next(p for p in board["partitions"]
                 if p["partition_id"] == pid)["geometry"]["endpoints"]


def test_roundtrip_empty_routes_still_converts(board, tmp_path):
    routes = _routes_doc(board, [])
    reread, data = _roundtrip(tmp_path, board, routes)
    _net_names, segments, vias = _extract(data)
    assert segments == [] and vias == []
    assert [n["net_id"] for n in reread["nets"]] == ["GND", "SIG"]


def test_roundtrip_multi_partition_net_merged_on_reread(tmp_path):
    """多分区网：两分区各一条 route，段/网表全对；读回分区被 adapter 按
    「最远两点」合并为单分区（披露的抽象层行为，不在语义等断言范围）。"""
    bd = _hand_board(
        nets=[{"net_id": "NET1", "partitions": ["PA", "PC"]},
              {"net_id": "NET2", "partitions": ["PB"]}],
        partitions=[
            {"partition_id": "PA", "ptype": "MISC",
             "geometry": {"endpoints": [[0.0, 0.0], [10.0, 0.0]]},
             "layer_policy": "any", "width_prior": {"w_min": 0.2, "w_max": 0.4},
             "current_a": 0, "speed_class": "unknown"},
            {"partition_id": "PC", "ptype": "MISC",
             "geometry": {"endpoints": [[20.0, 0.0], [30.0, 0.0]]},
             "layer_policy": "any", "width_prior": {"w_min": 0.2, "w_max": 0.4},
             "current_a": 0, "speed_class": "unknown"},
            {"partition_id": "PB", "ptype": "MISC",
             "geometry": {"endpoints": [[0.0, 20.0], [10.0, 20.0]]},
             "layer_policy": "any", "width_prior": {"w_min": 0.2, "w_max": 0.4},
             "current_a": 0, "speed_class": "unknown"},
        ])
    routes = _routes_doc(bd, [
        {"partition_id": "PA", "net_id": "NET1", "layer": "F.Cu", "width": 0.25,
         "polyline": [[0.0, 0.0], [10.0, 0.0]],
         "transition_vias": [], "return_vias": []},
        {"partition_id": "PC", "net_id": "NET1", "layer": "B.Cu", "width": 0.3,
         "polyline": [[20.0, 0.0], [30.0, 0.0]],
         "transition_vias": [[20.0, 0.0]], "return_vias": [[20.0, 1.0]]},
        {"partition_id": "PB", "net_id": "NET2", "layer": "F.Cu", "width": 0.2,
         "polyline": [[0.0, 20.0], [10.0, 20.0]],
         "transition_vias": [], "return_vias": []},
    ])
    reread, data = _roundtrip(tmp_path, bd, routes)
    _net_names, segments, vias = _extract(data)
    assert segments == _expected_segments(routes)
    assert vias == _expected_vias(routes, bd)
    assert [n["net_id"] for n in reread["nets"]] == ["NET1", "NET2"]
    assert len(reread["partitions"]) == 2  # 每网合并为 1（抽象层，已披露）


def test_roundtrip_v2_golden_combo_a(tmp_path):
    """D 层 V2 黄金夹具组合 A（P3→B.Cu / P5→F.Cu）：9 网网表序、段、孔、端点全对。"""
    bd = build_v2_board()
    combo = {"partition_id": "P3", "net_id": "P3", "layer": "B.Cu", "width": 0.2,
             "polyline": [[16.0, 4.0], [34.70, 4.0], [34.70, 36.0], [16.0, 36.0]],
             "transition_vias": [[34.70, 4.0], [34.70, 36.0]],
             "return_vias": [[33.70, 4.0], [33.70, 36.0]]}
    combo_p5 = {"partition_id": "P5", "net_id": "P5", "layer": "F.Cu", "width": 0.2,
                "polyline": [[37.0, 10.0], [34.85, 10.0], [34.85, 30.0], [37.0, 30.0]],
                "transition_vias": [], "return_vias": []}
    routes = _routes_doc(bd, [combo, combo_p5])
    reread, data = _roundtrip(tmp_path, bd, routes)
    # 网表一致且网序=板序（P1..P9）
    assert [n["net_id"] for n in reread["nets"]] == \
        [n["net_id"] for n in bd["nets"]]
    _net_names, segments, vias = _extract(data)
    assert segments == _expected_segments(routes)
    assert vias == _expected_vias(routes, bd)
    # 超范围加分断言：V2 夹具每网恰一分区 → 读回端点逐位相等。
    parts = {p["partition_id"]: p for p in reread["partitions"]}
    orig = {p["partition_id"]: p for p in bd["partitions"]}
    for net in bd["nets"]:
        rid = "PT-" + sanitize_net_id(net["net_id"])
        assert parts[rid]["geometry"]["endpoints"] == \
            orig[net["partitions"][0]]["geometry"]["endpoints"]


# --------------------------------------------------------------- write_kicad_pcb

def test_write_roundtrip_returns_path_and_bytes_match(board, tmp_path, monkeypatch):
    monkeypatch.setattr(sidecar, "ALLOWED_ROOTS", (str(tmp_path),))
    out_dir = os.path.join(str(tmp_path), "out")
    routes = _routes_doc(board, [_entry()])
    target = write_kicad_pcb(board, routes, os.path.join(
        out_dir, "exp-fixture.routed.kicad_pcb"))
    assert os.path.isfile(target)
    with open(target, "rb") as f:
        assert f.read() == kicad_pcb_bytes(board, routes)
    reread = convert_file(target, board["board_id"])
    assert [n["net_id"] for n in reread["nets"]] == ["GND", "SIG"]
    _net_names, segments, vias = _extract(open(target, "rb").read())
    assert segments == _expected_segments(routes)
    assert vias == _expected_vias(routes, board)


def test_write_creates_missing_subdirs(board, tmp_path, monkeypatch):
    monkeypatch.setattr(sidecar, "ALLOWED_ROOTS", (str(tmp_path),))
    target = os.path.join(str(tmp_path), "out", "run-1", "x.kicad_pcb")
    assert write_kicad_pcb(board, _routes_doc(board, []), target) == target
    assert os.path.isfile(target)


def test_write_rejects_outside_allowed_roots_default(board, tmp_path):
    """缺省 ALLOWED_ROOTS=out/：tmp_path 越界 → SidecarViolation，且零写盘。"""
    target = str(tmp_path / "evil.kicad_pcb")
    with pytest.raises(sidecar.SidecarViolation):
        write_kicad_pcb(board, _routes_doc(board, []), target)
    assert not os.path.exists(target)


def test_write_rejects_outside_when_patched(board, tmp_path, monkeypatch):
    monkeypatch.setattr(sidecar, "ALLOWED_ROOTS", (str(tmp_path),))
    outside = os.path.join(os.path.dirname(str(tmp_path)),
                           os.path.basename(str(tmp_path)) + "-x", "y.kicad_pcb")
    with pytest.raises(sidecar.SidecarViolation):
        write_kicad_pcb(board, _routes_doc(board, []), outside)
    assert not os.path.exists(outside)


def test_write_invalid_routes_leaves_no_file(board, tmp_path, monkeypatch):
    monkeypatch.setattr(sidecar, "ALLOWED_ROOTS", (str(tmp_path),))
    target = os.path.join(str(tmp_path), "out", "bad.kicad_pcb")
    with pytest.raises(ValueError):
        write_kicad_pcb(board, _routes_doc(board, [_entry(net_id="NOPE")]), target)
    assert not os.path.exists(target)


# --------------------------------------------------------------- fail-closed

def test_fail_wrong_schema_version(board):
    routes = _routes_doc(board, [_entry()], schema_version="v4.routes.v1")
    with pytest.raises(ValueError) as ei:
        kicad_pcb_bytes(board, routes)
    assert "routes.schema_version" in str(ei.value)


def test_fail_missing_schema_version(board):
    routes = _routes_doc(board, [_entry()])
    del routes["schema_version"]
    with pytest.raises(ValueError) as ei:
        kicad_pcb_bytes(board, routes)
    assert "routes.schema_version" in str(ei.value)


def test_fail_board_id_mismatch(board):
    routes = _routes_doc(board, [_entry()], board_id="other-board")
    with pytest.raises(ValueError) as ei:
        kicad_pcb_bytes(board, routes)
    assert "routes.board_id" in str(ei.value)


def test_fail_board_sha256_mismatch(board):
    routes = _routes_doc(board, [_entry()], board_sha256="f" * 64)
    with pytest.raises(ValueError) as ei:
        kicad_pcb_bytes(board, routes)
    assert "routes.board_sha256" in str(ei.value)


def test_fail_provenance_sha_mismatch(board):
    routes = _routes_doc(board, [_entry()],
                         provenance={"generator": "x", "board_sha256": "a" * 64})
    with pytest.raises(ValueError) as ei:
        kicad_pcb_bytes(board, routes)
    assert "routes.provenance.board_sha256" in str(ei.value)


def test_fail_routes_not_list_and_doc_not_dict(board):
    with pytest.raises(ValueError) as ei:
        kicad_pcb_bytes(board, _routes_doc(board, "nope"))
    assert "routes.routes" in str(ei.value)
    with pytest.raises(ValueError):
        kicad_pcb_bytes(board, 42)


def test_fail_unknown_net_id(board):
    routes = _routes_doc(board, [_entry(net_id="NOPE")])
    with pytest.raises(ValueError) as ei:
        kicad_pcb_bytes(board, routes)
    assert "routes.routes[0].net_id" in str(ei.value)


def test_fail_unknown_partition_id(board):
    routes = _routes_doc(board, [_entry(partition_id="PT-NOPE")])
    with pytest.raises(ValueError) as ei:
        kicad_pcb_bytes(board, routes)
    assert "routes.routes[0].partition_id" in str(ei.value)


def test_fail_partition_belongs_to_other_net(board):
    routes = _routes_doc(board, [_entry(partition_id="PT-GND")])  # 网写成 SIG
    with pytest.raises(ValueError) as ei:
        kicad_pcb_bytes(board, routes)
    assert "routes.routes[0].partition_id" in str(ei.value)
    assert "不属于" in str(ei.value)


def test_fail_unknown_layer(board):
    routes = _routes_doc(board, [_entry(layer="In9.Cu")])
    with pytest.raises(ValueError) as ei:
        kicad_pcb_bytes(board, routes)
    assert "routes.routes[0].layer" in str(ei.value)


def test_fail_short_polyline(board):
    routes = _routes_doc(board, [_entry(polyline=[[9.0, 10.0]])])
    with pytest.raises(ValueError) as ei:
        kicad_pcb_bytes(board, routes)
    assert "routes.routes[0].polyline" in str(ei.value)


@pytest.mark.parametrize("poly", [
    [[9.0, 10.0], [20.0, 10.0, 0.0]],      # 3 坐标
    [[9.0, 10.0], ["a", 10.0]],            # 非数值
    [[9.0, 10.0], [float("nan"), 10.0]],   # NaN
    [[9.0, 10.0], [20.0]],                 # 单坐标
    "(9 10)(20 10)",                       # 整体非列表
])
def test_fail_bad_polyline_points(board, poly):
    routes = _routes_doc(board, [_entry(polyline=poly)])
    with pytest.raises(ValueError) as ei:
        kicad_pcb_bytes(board, routes)
    assert "routes.routes[0].polyline" in str(ei.value)


@pytest.mark.parametrize("width", [0, -0.2, float("nan"), float("inf"),
                                   "0.2", True, None])
def test_fail_bad_width(board, width):
    routes = _routes_doc(board, [_entry(width=width)])
    with pytest.raises(ValueError) as ei:
        kicad_pcb_bytes(board, routes)
    assert "routes.routes[0].width" in str(ei.value)


@pytest.mark.parametrize("vias", [
    [20.0],                    # 非对
    [[20.0, 24.0, 1.0]],       # 3 坐标
    [[float("inf"), 0.0]],     # 非有限
    "20,24",                   # 非列表
])
def test_fail_bad_via_positions(board, vias):
    routes = _routes_doc(board, [_entry(return_vias=vias)])
    with pytest.raises(ValueError) as ei:
        kicad_pcb_bytes(board, routes)
    assert "routes.routes[0].return_vias" in str(ei.value)


def test_fail_via_field_not_list(board):
    routes = _routes_doc(board, [_entry(transition_vias="nope")])
    with pytest.raises(ValueError) as ei:
        kicad_pcb_bytes(board, routes)
    assert "routes.routes[0].transition_vias" in str(ei.value)


def test_fail_bad_negotiation_log(board):
    routes = _routes_doc(board, [_entry()], negotiation_log=[1, 2])
    with pytest.raises(ValueError) as ei:
        kicad_pcb_bytes(board, routes)
    assert "routes.negotiation_log" in str(ei.value)


def test_fail_board_without_nets():
    """板无 net：adapter 对 0 网板同样拒读，导出器 fail-closed（披露）。"""
    bd = _hand_board(nets=[], partitions=[], validate=True)
    routes = _routes_doc(bd, [])
    with pytest.raises(ValueError) as ei:
        kicad_pcb_bytes(bd, routes)
    assert "board.nets" in str(ei.value)


def test_fail_missing_workspace_key():
    """板缺 workspace 字段（未过 load_board 的裸 dict）→ 键路径报错。"""
    bd = _hand_board(
        nets=[{"net_id": "N1", "partitions": ["PA"]}],
        partitions=[{"partition_id": "PA", "ptype": "MISC",
                     "geometry": {"endpoints": [[0.0, 0.0], [1.0, 1.0]]},
                     "layer_policy": "any",
                     "width_prior": {"w_min": 0.2, "w_max": 0.4},
                     "current_a": 0, "speed_class": "unknown"}],
        validate=False)
    del bd["workspace"]["x_min"]
    with pytest.raises(ValueError) as ei:
        kicad_pcb_bytes(bd, _routes_doc(bd, []))
    assert "board.workspace.x_min" in str(ei.value)


# --------------------------------------------------------------- 只读与精度

def test_board_not_mutated(board):
    routes = _routes_doc(board, [_entry()])
    before = canonical.canonical_json(copy.deepcopy(board))
    kicad_pcb_bytes(board, routes)
    assert canonical.canonical_json(board) == before


def test_float_precision_bitexact_roundtrip(board, tmp_path):
    """repr 浮点逐位往返：0.1+0.2、1e-9、负值、大坐标读回全等。"""
    tricky = [0.1 + 0.2, 1e-9, -12.5, 123456.789]
    routes = _routes_doc(board, [_entry(
        polyline=[[tricky[0], tricky[1]], [tricky[2], tricky[3]]],
        width=0.15000000000000002,
        transition_vias=[[tricky[3], tricky[0]]], return_vias=[]),
    ])
    _reread, data = _roundtrip(tmp_path, board, routes)
    _net_names, segments, vias = _extract(data)
    assert segments == _expected_segments(routes)
    assert vias == _expected_vias(routes, board)
