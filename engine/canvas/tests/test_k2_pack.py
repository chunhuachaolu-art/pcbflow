# -*- coding: utf-8 -*-
"""canvas.pack 测试（Lane-K2）。

桩仅测试用、非平行实现；真件集成由编排体冒烟。
覆盖：pack_view 同态双跑字节等（≥2）、write_pack 三件落盘、SVG 机器事实
（pad/seg/via/tuning 各 kind 齐）、view_spec 层可见性/视窗、state 缝
fail-closed。
"""

import json
import os
import re

import pytest

from v5.board import compute_board_sha256
from v5.canonical import canonical_json, canonical_sha256

from canvas.pack import pack_view, write_pack

# ---------------------------------------------------------------------------
# 合同签名桩（§1）：仅测试用、非平行实现；真件集成由编排体冒烟
# ---------------------------------------------------------------------------

BOARD = {
    "schema_version": "v5.board.v1",
    "board_id": "k2-stub-board",
    "provenance": {},
    "stackup": [{"id": "F.Cu", "kind": "signal", "available": True},
                {"id": "B.Cu", "kind": "signal", "available": True}],
    "nets": [{"net_id": "N1", "partitions": ["PT1"]},
             {"net_id": "N2", "partitions": ["PT2"]}],
    "partitions": [
        {"partition_id": "PT1", "geometry": {"endpoints": [[0.0, 0.0], [0.0, 3.0]]}},
        {"partition_id": "PT2", "geometry": {"endpoints": [[5.0, 0.0], [5.0, 3.0]]}},
    ],
    "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 10.0, "y_max": 10.0},
    "hard_rules": {"R5": {"min_clearance_mm": 0.2}},
}
BOARD["provenance"]["board_sha256"] = compute_board_sha256(BOARD)

ANCHORS = {"PT1": [[0, 0], [0, 3]], "PT2": [[5, 0], [5, 3]]}
LAT = {"cols": 10, "rows": 10, "pitch_mm": 0.25}


class StubState(object):
    """合同签名桩（§1 segs/vias/widths/placements/tunings/connectivity/
    state_facts/state_sha256/board/lat）；仅测试用，非平行实现。"""

    def __init__(self):
        self.board = BOARD
        self.board_path = "out/v5-p5/boards/k2-stub-board/board.json"
        self.board_sha256 = BOARD["provenance"]["board_sha256"]
        self.lat = LAT
        self.anchors = ANCHORS
        self.segs = [{
            "shape_id": "seg:N1:1", "net_id": "N1", "partition_id": "PT1",
            "layer": "F.Cu", "grid": [[0, 0], [1, 0], [2, 0]],
            "width_class": "default",
        }, {
            "shape_id": "seg:N2:1", "net_id": "N2", "partition_id": "PT2",
            "layer": "B.Cu", "grid": [[5, 3], [4, 3]],
            "width_class": "power",
        }]
        self.vias = [{
            "shape_id": "via:N1:2_0", "net_id": "N1", "grid": [2, 0],
        }]
        self.widths = {"N1": "default", "N2": "power"}
        self.placements = {"PT2": {"move": [5, 1], "rotate": 1, "flip": False}}
        self.tunings = [{
            "shape_id": "tun:N1:G1:1", "net_id": "N1", "group_id": "G1",
            "kind": "accordion", "grid": [[0, 0], [1, 0]],
            "params": {"amplitude": 2},
        }]
        self.connectivity = {"N1": True, "N2": False}
        self.chain_detail = {}

    def state_facts(self):
        import copy
        return {
            "board_sha256": self.board_sha256,
            "segs": copy.deepcopy(self.segs),
            "vias": copy.deepcopy(self.vias),
            "widths": dict(self.widths),
            "placements": copy.deepcopy(self.placements),
            "tunings": copy.deepcopy(self.tunings),
            "connectivity": dict(self.connectivity),
            "chain_detail": copy.deepcopy(self.chain_detail),
        }

    def state_sha256(self):
        return canonical_sha256(self.state_facts())

    # ---- apply 缝桩（确定性最小语义；仅测试用，非平行实现） ----

    def _partition_of(self, net_id):
        for net in self.board["nets"]:
            if net["net_id"] == net_id:
                return net["partitions"][0]
        return ""

    def apply_action(self, action):
        """copy-on-write 最小语义：route/via 追加、ripup 按 shape_id 删、
        submit 空操作；未知动作拒收。"""
        name = action.get("action")
        if name == "route":
            net = action["net_id"]
            seq = len([s for s in self.segs if s["net_id"] == net]) + 1
            self.segs = list(self.segs) + [{
                "shape_id": "seg:%s:%d" % (net, seq), "net_id": net,
                "partition_id": self._partition_of(net),
                "layer": action["layer"],
                "grid": [list(p) for p in action["waypoints"]],
                "width_class": self.widths.get(net, "default")}]
            return True, None, ""
        if name == "via":
            i, j = action["grid"]
            sid = "via:%s:%d_%d" % (action["net_id"], i, j)
            if any(v["shape_id"] == sid for v in self.vias):
                return False, "V_DUPLICATE_VIA", sid
            self.vias = list(self.vias) + [
                {"shape_id": sid, "net_id": action["net_id"],
                 "grid": [i, j]}]
            return True, None, ""
        if name == "ripup":
            sid = action.get("shape_id")
            for pool in ("segs", "vias"):
                if any(x["shape_id"] == sid for x in getattr(self, pool)):
                    setattr(self, pool, [x for x in getattr(self, pool)
                                         if x["shape_id"] != sid])
                    return True, None, ""
            return False, "V_RIPUP_UNKNOWN", sid
        if name == "submit":
            return True, None, ""
        return False, "E_UNKNOWN_ACTION", name


@pytest.fixture
def stub_state():
    return StubState()


def test_pack_view_double_run_byte_equal(stub_state):
    """确定性双跑字节等 ≥2：同态 3 跑，svg/facts_json/view_spec 两两字节等。"""
    packs = [pack_view(stub_state) for _ in range(3)]
    for key in ("svg", "facts_json"):
        assert packs[0][key] == packs[1][key] == packs[2][key]
    specs = [canonical_json(p["view_spec"]) for p in packs]
    assert specs[0] == specs[1] == specs[2]


def test_write_pack_three_files(stub_state, tmp_path):
    pack = pack_view(stub_state)
    paths = write_pack(pack, str(tmp_path))
    assert sorted(os.path.basename(p) for p in paths.values()) == [
        "view-facts.json", "view-spec.json", "view.svg"]
    with open(paths["view.svg"], "rb") as f:
        assert f.read() == pack["svg"].encode("utf-8")
    with open(paths["view-facts.json"], "rb") as f:
        assert f.read() == pack["facts_json"].encode("utf-8")
    with open(paths["view-spec.json"], "rb") as f:
        assert f.read() == canonical_json(pack["view_spec"])


def _elements(svg, kind):
    """抽 SVG 内带 data-kind=kind 的图元行。"""
    return [line for line in svg.splitlines()
            if "data-kind=%s" % ('"%s"' % kind) in line
            or ("data-kind=" + kind) in line]


def _attr(line, name):
    m = re.search(r'%s="([^"]*)"' % name, line)
    if m is None:
        return None
    return m.group(1).replace("&quot;", '"').replace("&lt;", "<") \
        .replace("&gt;", ">").replace("&amp;", "&")


def test_svg_machine_facts_all_kinds(stub_state):
    """每图元带 data-shape-id/net/layer/grid/kind；pad/seg/via/tuning 四 kind 齐。"""
    svg = pack_view(stub_state)["svg"]
    pads = _elements(svg, "pad")
    segs = _elements(svg, "seg")
    vias = _elements(svg, "via")
    tuns = _elements(svg, "tuning")
    assert len(pads) == 4  # 2 分区 × 2 端点锚
    assert len(segs) == 2 and len(vias) == 1 and len(tuns) == 1
    shape_ids = []
    for line in pads + segs + vias + tuns:
        for attr in ("data-shape-id", "data-net", "data-layer",
                     "data-grid", "data-kind"):
            assert _attr(line, attr) is not None, line
        grid = json.loads(_attr(line, "data-grid"))
        assert isinstance(grid, list) and len(grid) >= 1
        shape_ids.append(_attr(line, "data-shape-id"))
    assert len(shape_ids) == len(set(shape_ids))  # shape_id 唯一
    # 层取值口径（模块 docstring 披露）：seg=自身层、via=*、pad=all、tuning=-
    assert _attr(segs[0], "data-layer") == "F.Cu"
    assert _attr(vias[0], "data-layer") == "*"
    assert all(_attr(l, "data-layer") == "all" for l in pads)
    assert _attr(tuns[0], "data-layer") == "-"
    # placement 覆盖透传（PT2 有覆盖，其 pad 带 data-placement；PT1 无）
    placed = [l for l in pads if "data-placement=" in l]
    assert len(placed) == 2
    override = json.loads(_attr(placed[0], "data-placement"))
    assert override == {"move": [5, 1], "rotate": 1, "flip": False}
    # tuning 子类机器事实
    tun_line = tuns[0]
    assert _attr(tun_line, "data-tuning-kind") == "accordion"
    assert _attr(tun_line, "data-group-id") == "G1"


def test_view_spec_layers_and_viewport(stub_state):
    spec = pack_view(stub_state)["view_spec"]
    assert spec["layers"] == {"F.Cu": True, "B.Cu": True}
    vp = spec["viewport"]
    for key in ("min_i", "min_j", "max_i", "max_j",
                "width_px", "height_px"):
        assert key in vp
    assert (vp["min_i"], vp["min_j"], vp["max_i"], vp["max_j"]) == (0, 0, 5, 3)
    assert vp["width_px"] == 5 * 20 + 80 and vp["height_px"] == 3 * 20 + 80
    assert spec["lat"] == LAT
    assert spec["kinds"] == ["pad", "seg", "via", "tuning"]
    assert spec["board_sha256"] == stub_state.board_sha256


def test_state_seam_fail_closed(stub_state, monkeypatch):
    """state 缝未接线（无 state_facts）→ AttributeError，不静默。"""
    monkeypatch.delattr(StubState, "state_facts")
    with pytest.raises(AttributeError, match="state_facts"):
        pack_view(stub_state)


def test_segs_dict_container(stub_state):
    """合同容 segs 两种容器（list / shape_id 索引 dict）——dict 形态同样可用。"""
    stub_state.segs = {s["shape_id"]: s for s in stub_state.segs}
    pack = pack_view(stub_state)
    assert len(_elements(pack["svg"], "seg")) == 2


def test_partition_multi_net_fail_closed(stub_state):
    """一分区被多网引用 → pack fail-closed（板语义不容）。"""
    stub_state.board = dict(BOARD, nets=[
        {"net_id": "N1", "partitions": ["PT1"]},
        {"net_id": "NX", "partitions": ["PT1"]},
    ])
    with pytest.raises(ValueError, match="多网引用"):
        pack_view(stub_state)
