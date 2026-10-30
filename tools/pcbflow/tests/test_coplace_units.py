"""③ 单元测试：量化/变换/几何原语/CSV 格式/转换证明/门映射（自包含，无 IO）。"""

import pytest

from pcbflow import config, coplace_cmd, envelope, geo


def test_quant_roundtrip():
    for v in (0.0, 0.05, 0.1, 13.0, 41.3, 30.25, 66.75, 69.95):
        assert coplace_cmd.uq(coplace_cmd.q(v)) == pytest.approx(v, abs=1e-9)


def test_rot90_matches_geo_transform():
    """_rot90 与 geo.transform 在 90° 步进下逐点一致（KiCad 屏幕系）。"""
    for rot in (0, 90, 180, 270, -90, 360):
        for (px, py) in ((1.3, -0.7), (-2.5, 0.0), (0.0, 0.0), (3.2, 4.8)):
            ax, ay = geo.transform(px, py, 10.0, 20.0, float(rot))
            rx, ry = coplace_cmd._rot90(coplace_cmd.q(px), coplace_cmd.q(py),
                                        rot // 90)
            assert (rx + coplace_cmd.q(10.0), ry + coplace_cmd.q(20.0)) == \
                   (coplace_cmd.q(ax), coplace_cmd.q(ay))


def test_fmt_csv_matches_p3_style():
    assert coplace_cmd.fmt_csv(41.3) == "41.3"
    assert coplace_cmd.fmt_csv(30.25) == "30.25"
    assert coplace_cmd.fmt_csv(13.0) == "13.0"
    assert coplace_cmd.fmt_csv(0.0) == "0.0"
    assert coplace_cmd.fmt_csv(66.75) == "66.75"


def test_bbox_primitives():
    a = (0, 0, 10, 10)
    b = (15, 3, 25, 13)  # 东侧，y 重叠
    assert coplace_cmd._bbox_gap(a, b) == 5
    c = (4, 4, 6, 6)  # 全包围
    # MTD=两轴重叠的较浅者=6（非最近边距 4）；_rect_depth=min 重叠=2 保留
    assert coplace_cmd._intrusion_depth(c, a) == 6
    assert coplace_cmd._rect_depth(c, a) == 2
    d = (20, 20, 30, 30)
    assert coplace_cmd._bbox_gap(a, d) == pytest.approx((10 ** 2 + 10 ** 2) ** 0.5)
    # 部分重叠：MTD=较浅轴深度
    e = (8, 2, 14, 6)
    assert coplace_cmd._intrusion_depth(e, a) == 2


def test_seg_cross():
    assert coplace_cmd._seg_cross((0, 0), (10, 10), (0, 10), (10, 0))
    assert not coplace_cmd._seg_cross((0, 0), (10, 0), (0, 0), (5, 0))   # 共线
    assert not coplace_cmd._seg_cross((0, 0), (10, 0), (5, 0), (5, 5))   # 共端
    assert not coplace_cmd._seg_cross((0, 0), (1, 0), (5, -3), (5, 3))   # 不相交


def test_placement_csv_shape_and_order():
    layout = {"placements": [
        {"ref": "B2", "x": 1.0, "y": 2.25, "rot": 270, "side": "F", "zone": "Z"},
        {"ref": "A1", "x": 41.3, "y": 39.6, "rot": 0, "side": "F", "zone": "AN"},
        {"ref": "C10", "x": 13.0, "y": 8.3, "rot": 90, "side": "F", "zone": ""},
    ]}
    data = coplace_cmd.to_placement_csv(layout)
    text = data.decode("utf-8")
    lines = text.split("\r\n")
    assert lines[0] == "ref,x,y,rot,side,zone"
    assert lines[1] == "A1,41.3,39.6,0,F,AN"
    assert lines[2] == "B2,1.0,2.25,270,F,Z"
    assert lines[3] == "C10,13.0,8.3,90,F,"
    assert text.endswith("\r\n")
    # 双跑 byte-exact（dict 顺序无关）
    assert coplace_cmd.to_placement_csv(layout) == data


def test_conversion_proof_contract():
    proof = coplace_cmd.conversion_proof("a" * 64, "b" * 64, "out/x")
    assert proof["schema_version"] == config.SCHEMA_CONVERSION
    assert "pending_approval" in proof["execution"]
    assert proof["deterministic"] is True
    assert proof["rules"]["newline"] == "CRLF（既有 apply 脚本输入口径）"
    assert envelope.scan_forbidden_core_fields(proof) == []


def test_placement_gate_map_covers_spec8():
    gates = {g["gate"] for g in coplace_cmd.PLACEMENT_GATE_MAP}
    assert gates == {"channel_budget", "proximity", "body_spacing",
                     "orientation", "keepout", "zone_purity"}


def test_core_constants_frozen():
    """SPEC §③ 候选集参数锚定；改动必须先改真值认知（PHASE-REPORT-4 §3）。"""
    assert config.CPLACE_STEPS_MM == (0.5, 1.0, 2.0)
    assert config.CPLACE_ROT_STEP == 90
    assert config.CPLACE_QUANT == 0.05
    assert config.CPLACE_MIN_BEND_SPACING_MM == 1.0
    assert config.CPLACE_MAX_SWEEPS >= 30


def test_bend_spacing_guard():
    seg = {"polyline": [[0.0, 0.0], [5.0, 0.0], [5.0, 5.0]]}
    assert coplace_cmd._bend_spacing_ok(seg, 0, -coplace_cmd.q(1.0))  # 4mm ≥1
    # 拐点压到端点上（距 0）→ 违反最小拐点间距
    tight = {"polyline": [[0.0, 0.0], [0.5, 0.0], [5.0, 5.0]]}
    assert not coplace_cmd._bend_spacing_ok(tight, -coplace_cmd.q(0.5), 0)


def test_verdict_thresholds():
    """软目标阈值语义：硬违=红；软超阈=黄；全绿=pass（config.py 固定）。"""
    hard_fail, skel = [], {"crossings": 0, "congestion_max": 0.5, "vias": 0,
                           "detour_max": 1.2, "symmetry_dev_max_mm": 0.1}
    assert coplace_cmd._verdict_of(hard_fail, skel) == "pass"
    assert coplace_cmd._verdict_of(hard_fail,
                                   dict(skel, crossings=2)) == "yellow"
    assert coplace_cmd._verdict_of(hard_fail,
                                   dict(skel, detour_max=1.6)) == "yellow"
    assert coplace_cmd._verdict_of(["channel_budget"], skel) == "red"


# ---- FF-3：②↔③ required_mm 三态交叉核对（SPEC v1.3 §8.3；PATCH-FF1 §5） --------
def test_sanity_required_mm_three_states():
    """缺字段 / null / 正常 / 不一致 四负正例；禁止 None→true。"""
    rows = [{"bus_id": "BUS_A", "demand_mm": 2.0, "gap_mm": 5.0, "ok": True},
            {"bus_id": "BUS_B", "demand_mm": 3.0, "gap_mm": 5.0, "ok": True},
            {"bus_id": "BUS_C", "demand_mm": 4.0, "gap_mm": 5.0, "ok": True},
            {"bus_id": "BUS_D", "demand_mm": 9.9, "gap_mm": 5.0, "ok": False}]
    corridors = [
        {"bus_id": "BUS_A", "required_mm": 2.0},        # 正常：一致
        {"bus_id": "BUS_B", "required_mm": None},       # null → unknown
        {"bus_id": "BUS_D", "required_mm": 7.6},        # 不一致
    ]  # BUS_C 缺整条走廊记录 → unknown（missing_basis:required_mm）
    out = {r["bus_id"]: r for r in
           coplace_cmd.sanity_vs_audit_rows(rows, corridors)}
    assert out["BUS_A"]["demand_consistent"] == "consistent"
    assert out["BUS_A"]["audit_demand_mm"] == 2.0
    assert out["BUS_A"]["tolerance_mm"] == coplace_cmd.SANITY_TOLERANCE_MM
    assert out["BUS_A"]["source"].startswith("audit corridor_budget_check")
    assert out["BUS_B"]["demand_consistent"] == "unknown"
    assert out["BUS_B"]["reason"] == "missing_basis:required_mm_null"
    assert out["BUS_B"]["audit_demand_mm"] is None
    assert out["BUS_C"]["demand_consistent"] == "unknown"
    assert out["BUS_C"]["reason"] == "missing_basis:required_mm"
    assert out["BUS_D"]["demand_consistent"] == "inconsistent"
    assert out["BUS_D"]["reason"] is not None


def test_sanity_no_silent_true_on_none():
    """空比较禁令：audit 值缺失时不得产出 consistent（v1.3 §8.3 红线）。"""
    rows = [{"bus_id": "BUS_X", "demand_mm": 1.0, "gap_mm": 2.0, "ok": True}]
    for corridors in ([{"bus_id": "BUS_X"}],
                      [{"bus_id": "BUS_X", "required_mm": None}],
                      []):
        out = coplace_cmd.sanity_vs_audit_rows(rows, corridors)
        assert out[0]["demand_consistent"] != "consistent"
        assert out[0]["demand_consistent"] == "unknown"
