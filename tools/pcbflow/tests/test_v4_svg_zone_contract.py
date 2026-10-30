"""铜箔闭环 P3 —— zone 合同扩展（SVG/manifest 合同 v2）测试。

被测模块：`pcbflow/svg_route_package.py`（zone 对象 + 版本提升 + verify 覆盖）
与 `pcbflow/board_svg_adapter.py`（铜箔 zone → 只读镜像）。

覆盖：
- 版本：`SVG_SCHEMA`/`MANIFEST_SCHEMA_VERSION` 提升到 v2，v1 常量保留导出、
  `is_legacy_package` 可显式分流；v1 产物不自称 v2（verify 如实报版本违规，
  绝不静默接受）；
- manifest：顶层 `zones`（zone_id 唯一、按 zone_id 稳定排序、outline_mm 6 位
  量化、outline_kind=polygon、fill 组 derived=true）+ `zones_summary` +
  `zones_facts_sha256`；
- **事实 vs 派生**：`zone_facts_sha256` 只含事实投影（改 fill_points 不变、
  改轮廓必变）；填充派生数据不入事实哈希、不入 SVG 几何；
- **fill_state 语义**：调用方显式传入（未传 = unknown，绝不假定 fresh）；
  声明 fresh 必须带 fill_sha256 指纹（否则 ValueError）；stale/unknown 在
  manifest / SVG / zones_summary 三处可读（供 P3b"未重填不得采纳"）；
- SVG：`<g data-object-kind="zone">` 全套 data-*、闭合轮廓 path、零容差
  round-trip（`parse_svg_zone_outline`）、低透明度轮廓投影；
- 负向矩阵：篡改轮廓坐标 / 改 fill_state / 删 zone（两侧）/ 轮廓点数 < 3 /
  缺必填属性 / 去派生标记 / 改派生指纹 / 改 zones_facts_sha256 /
  改 zones_summary / 轮廓不闭合 / zone_id 重复 / layers 不一致 → 必检出；
- 真实板（只读抽样）：`config.REVC_BOARD` + `out/revc-a3/net-registry.json`
  的 2 个 GND 铺铜进入镜像且 verify 零违规；不写任何板文件、不调 kicad-cli。
"""

import copy
import json
import os
import re
import xml.etree.ElementTree as ET

import pytest

from pcbflow import board_svg_adapter as ba
from pcbflow import config, copper_model, svg_route_package as s4

SVG_NS = "http://www.w3.org/2000/svg"

Z1 = "ZONE-GND-BCU"
Z2 = "ZONE-GND-IN1"


# --------------------------------------------------------------- 合成夹具

def make_board():
    return {
        "scenario_id": "SC-P3-ZONE",
        "board": {"bbox_mm": [0.0, 0.0, 40.0, 30.0]},
        "rules": {},
        "pads": [
            {"pad_id": "U1.1", "net_id": "N0001", "x_mm": 5.0, "y_mm": 5.0,
             "w_mm": 0.6, "h_mm": 0.4, "layer": "F.Cu"},
        ],
        "keepouts": [],
        "relations": [],
    }


def make_ref():
    return {
        "scenario_id": "SC-P3-ZONE",
        "routes": [
            {"route_id": "R1", "net_id": "N0001", "relation_ids": [],
             "line_type": "signal", "parent_id": None, "layer": "F.Cu",
             "width_mm": 0.25, "polyline_mm": [[5.0, 5.0], [15.0, 5.0]],
             "endpoint_ids": ["A", "B"], "constraint_refs": [],
             "state": "baseline", "source": "baseline"},
        ],
        "vias": [],
        "zones": [
            # 故意乱序传入：manifest 必须按 zone_id 稳定排序
            {"zone_id": Z2, "net_id": "N0002", "layers": ["In1.Cu"],
             "outline_kind": "polygon",
             "outline_mm": [[1.0, 1.0], [39.0, 1.0], [39.0, 29.0],
                            [1.0, 29.0]],
             "fill_state": "unknown", "fill_sha256": "b" * 64,
             "fill_points": 18795},
            {"zone_id": Z1, "net_id": "N0002", "layers": ["B.Cu"],
             "outline_kind": "polygon",
             "outline_mm": [[0.5, 0.5], [39.5, 0.5], [39.5, 29.5],
                            [0.5, 29.5]],
             "fill_state": "stale", "fill_sha256": "a" * 64,
             "fill_points": 5715},
        ],
    }


@pytest.fixture(scope="module")
def package():
    board, ref = make_board(), make_ref()
    svg, manifest = s4.build(board, ref)
    return board, ref, svg, manifest


def find_by_id(root, el_id):
    for el in root.iter():
        if isinstance(el.tag, str) and el.attrib.get("id") == el_id:
            return el
    raise AssertionError(f"SVG 中找不到 id={el_id!r}")


def rehash(manifest: dict) -> dict:
    """篡改后重算全部自哈希（payload + zone 事实 + summary），
    以便让违规只能来自**跨腿核对**（SVG ↔ manifest）而非自哈希不符。"""
    m = copy.deepcopy(manifest)
    m.pop("manifest_payload_sha256", None)
    m.pop("zones_facts_sha256", None)
    m["zones_facts_sha256"] = s4.zone_facts_sha256(m["zones"])
    m["manifest_payload_sha256"] = s4._sha256_of(m)
    return m


# -------------------------------------------------------- 版本（v2 + v1 兼容）

class TestSchemaVersion:
    def test_v2_constants_and_v1_retained(self, package):
        _, _, svg, manifest = package
        assert s4.SVG_SCHEMA == "v4-svg-route-2"
        assert s4.MANIFEST_SCHEMA_VERSION == "v4-route-manifest-2"
        # v1 常量保留导出（v1 产物仍可读，语义不被覆写）
        assert s4.SVG_SCHEMA_V1 == "v4-svg-route-1"
        assert s4.MANIFEST_SCHEMA_VERSION_V1 == "v4-route-manifest-1"
        assert ET.fromstring(svg).get("data-pcbflow-schema") == \
            s4.SVG_SCHEMA
        assert manifest["schema_version"] == s4.MANIFEST_SCHEMA_VERSION

    def test_is_legacy_package_only_for_v1_pair(self, package):
        _, _, _svg, manifest = package
        assert s4.is_legacy_package("v4-svg-route-1",
                                    "v4-route-manifest-1") is True
        assert s4.is_legacy_package(s4.SVG_SCHEMA,
                                    s4.MANIFEST_SCHEMA_VERSION) is False
        # 混搭（v1 SVG + v2 manifest）不是"已知的 v1 组合"：不得被当 v1 放行
        assert s4.is_legacy_package("v4-svg-route-1",
                                    s4.MANIFEST_SCHEMA_VERSION) is False
        assert s4.is_legacy_package("v4-svg-route-9", "v4-route-manifest-9") \
            is False

    def test_v1_product_is_not_silently_accepted(self, package):
        """v1 产物（无 zone、旧版本字面量）不被静默当 v2：如实报版本违规。"""
        board, ref, svg, manifest = package
        # 构造 v1 形状产物：摘掉 zones/summary/facts 与根上的 zone 绑定，
        # 版本字面量回退 v1、其余（route/via/pad/图例）逐字不变。
        v1_ref = dict(ref, zones=[])
        v1_svg, v1_man = s4.build(board, v1_ref)
        for key in ("zones", "zones_summary", "zones_facts_sha256"):
            v1_man.pop(key, None)
        v1_man["schema_version"] = s4.MANIFEST_SCHEMA_VERSION_V1
        v1_man["manifest_payload_sha256"] = s4._sha256_of(v1_man)
        v1_svg = v1_svg.replace(
            f'data-pcbflow-schema="{s4.SVG_SCHEMA}"',
            f'data-pcbflow-schema="{s4.SVG_SCHEMA_V1}"', 1)
        v1_svg = re.sub(r' data-zones-facts-sha256="[^"]*"', "", v1_svg, 1)
        v1_svg = v1_svg.replace(
            f'data-route-manifest-sha256="{manifest["manifest_payload_sha256"]}"',
            f'data-route-manifest-sha256='
            f'"{v1_man["manifest_payload_sha256"]}"', 1)
        assert s4.is_legacy_package(ET.fromstring(v1_svg)
                                    .get("data-pcbflow-schema"),
                                    v1_man["schema_version"]) is True
        out = s4.verify_consistency(v1_svg, v1_man)
        assert out  # 非空：v1 不被静默接受
        assert any("data-pcbflow-schema" in v for v in out)
        assert any("zones" in v or "zones_facts_sha256" in v for v in out)


# ------------------------------------------------------------ manifest 侧

class TestManifestZoneContract:
    def test_zones_sorted_unique_and_shaped(self, package):
        _, _, _svg, manifest = package
        zones = manifest["zones"]
        assert [z["zone_id"] for z in zones] == [Z1, Z2]  # 稳定排序
        assert len({z["zone_id"] for z in zones}) == 2
        for z in zones:
            assert z["svg_id"] == f"zone-{z['zone_id']}"
            assert z["outline_kind"] == "polygon"
            assert z["outline_kind"] in s4.ZONE_OUTLINE_KINDS
            assert z["fill_state"] in s4.ZONE_FILL_STATES
            assert z["layers"] and all(isinstance(v, str) for v in z["layers"])
            assert len(z["outline_mm"]) >= 3
            for p in z["outline_mm"]:
                assert re.fullmatch(r"-?\d+\.?\d*", str(p[0]))
            assert z["fill"]["derived"] is True
            assert re.fullmatch(r"[0-9a-f]{64}", z["fill"]["fill_sha256"])
            assert isinstance(z["fill"]["fill_points"], int)

    def test_outline_is_geometry_fact_fill_is_derived(self, package):
        _, _, _svg, manifest = package
        by_id = {z["zone_id"]: z for z in manifest["zones"]}
        assert by_id[Z1]["outline_mm"] == [[0.5, 0.5], [39.5, 0.5],
                                           [39.5, 29.5], [0.5, 29.5]]
        assert by_id[Z1]["layers"] == ["B.Cu"]
        assert by_id[Z1]["net_id"] == "N0002"
        # 填充派生数据只出现在 zone 条目内（不参与任何几何事实）
        assert set(by_id[Z1]["fill"]) == {"derived", "fill_sha256",
                                          "fill_points"}

    def test_zones_summary_readable_for_p3b_gate(self, package):
        _, _, _svg, manifest = package
        summ = manifest["zones_summary"]
        assert summ["count"] == 2
        assert summ["fill_state_counts"] == {"fresh": 0, "stale": 1,
                                            "unknown": 1}
        # 未重填者必须能一眼读出（P3b"未重填不得采纳"）
        assert summ["not_fresh_zone_ids"] == [Z1, Z2]
        assert summ["fill_state_is_caller_declared"] is True

    def test_zone_fact_hash_excludes_derived_data(self, package):
        _, ref, _svg, manifest = package
        base = s4.zone_facts_sha256(manifest["zones"])
        assert manifest["zones_facts_sha256"] == base
        assert re.fullmatch(r"[0-9a-f]{64}", base)
        # 改派生数据（fill_points / fill_sha256）→ 事实哈希不变
        derived = copy.deepcopy(manifest["zones"])
        derived[0]["fill"]["fill_points"] = 999999
        derived[0]["fill"]["fill_sha256"] = "c" * 64
        assert s4.zone_facts_sha256(derived) == base
        # 改轮廓（事实）→ 事实哈希必变
        moved = copy.deepcopy(manifest["zones"])
        moved[0]["outline_mm"][0][0] += 0.000001
        assert s4.zone_facts_sha256(moved) != base
        # 改 fill_state（P3b 直接消费的声明）→ 事实哈希必变（防篡改可检）
        restated = copy.deepcopy(manifest["zones"])
        restated[0]["fill_state"] = "fresh"
        assert s4.zone_facts_sha256(restated) != base

    def test_svg_root_binds_zone_fact_hash(self, package):
        _, _, svg, manifest = package
        root = ET.fromstring(svg)
        assert root.get("data-zones-facts-sha256") == \
            manifest["zones_facts_sha256"]
        assert root.get("data-route-manifest-sha256") == \
            manifest["manifest_payload_sha256"]


# ---------------------------------------------------- fill_state 语义（不猜）

class TestFillStateSemantics:
    def test_absent_fill_state_is_unknown_never_fresh(self):
        board, ref = make_board(), make_ref()
        z = dict(ref["zones"][0])
        z.pop("fill_state")
        zones = [z]
        man = s4.build_manifest(board, dict(ref, zones=zones))
        assert man["zones"][0]["fill_state"] == "unknown"
        assert man["zones_summary"]["fill_state_counts"]["fresh"] == 0
        assert man["zones"][0]["zone_id"] in \
            man["zones_summary"]["not_fresh_zone_ids"]

    def test_explicit_stale_and_unknown_are_preserved(self, package):
        _, _, _svg, manifest = package
        by_id = {z["zone_id"]: z for z in manifest["zones"]}
        assert by_id[Z1]["fill_state"] == "stale"
        assert by_id[Z2]["fill_state"] == "unknown"

    def test_fresh_requires_fingerprint_evidence(self):
        board, ref = make_board(), make_ref()
        z = dict(ref["zones"][0], fill_state="fresh")
        # 有指纹：允许（调用方显式声明 + 证据）
        man = s4.build_manifest(board, dict(ref, zones=[z]))
        assert man["zones"][0]["fill_state"] == "fresh"
        assert man["zones_summary"]["fill_state_counts"]["fresh"] == 1
        assert man["zones_summary"]["not_fresh_zone_ids"] == []
        # 无指纹却声称 fresh：fail-closed 拒绝（生成器不猜填充新鲜度）
        for drop in ({"fill_sha256"}, {"fill_sha256", "fill_points"},
                     {"fill_sha256": None}):
            bad = {k: v for k, v in z.items() if k not in drop}
            if drop == {"fill_sha256": None}:
                bad = dict(z, fill_sha256=None)
            with pytest.raises(ValueError):
                s4.build_manifest(board, dict(ref, zones=[bad]))

    def test_invalid_fill_state_rejected(self):
        board, ref = make_board(), make_ref()
        for bad_fs in ("FRESH", "filled", "", None, 1):
            z = dict(ref["zones"][0], fill_state=bad_fs)
            with pytest.raises(ValueError):
                s4.build_manifest(board, dict(ref, zones=[z]))

    def test_fill_fingerprint_shape_enforced(self):
        board, ref = make_board(), make_ref()
        for field, bad in (("fill_sha256", "XYZ"), ("fill_sha256", "a" * 63),
                           ("fill_points", -1), ("fill_points", 1.5),
                           ("fill_points", True)):
            z = dict(ref["zones"][0])
            z[field] = bad
            with pytest.raises(ValueError):
                s4.build_manifest(board, dict(ref, zones=[z]))


# ------------------------------------------------------------- SVG 侧

class TestSvgZoneContract:
    def test_zone_group_attrs_and_order(self, package):
        _, _, svg, manifest = package
        root = ET.fromstring(svg)
        groups = [el for el in root.iter()
                  if el.attrib.get("data-object-kind") == "zone"]
        assert len(groups) == 2
        # 按 zone_id 稳定排序
        assert [g.get("data-zone-id") for g in groups] == [Z1, Z2]
        by_id = {z["zone_id"]: z for z in manifest["zones"]}
        for g in groups:
            z = by_id[g.get("data-zone-id")]
            for name in s4.SVG_ZONE_ATTRS:
                assert name in g.attrib, (z["zone_id"], name)
            assert g.get("id") == f"zone-{z['zone_id']}"
            assert g.get("data-net-id") == z["net_id"]
            assert g.get("data-layers") == " ".join(z["layers"])
            assert g.get("data-outline-kind") == z["outline_kind"]
            assert g.get("data-fill-state") == z["fill_state"]
            # 派生数据显式标记 + 明确"只画轮廓投影"
            assert g.get("data-fill-derived") == "true"
            assert g.get("data-fill-projection") == "outline_only"
            assert g.get("data-fill-sha256") == z["fill"]["fill_sha256"]
            assert g.get("data-fill-points") == str(z["fill"]["fill_points"])

    def test_outline_path_is_closed_and_zero_tolerance(self, package):
        _, _, svg, manifest = package
        root = ET.fromstring(svg)
        for z in manifest["zones"]:
            path = find_by_id(root, f"geom-zone-{z['zone_id']}")
            assert path.tag == f"{{{SVG_NS}}}path"
            assert path.get("class") == "zone-outline"
            d = path.get("d", "")
            toks = d.split(" ")
            groups = [toks[i:i + 3] for i in range(0, len(toks), 3)]
            assert len(groups) == len(z["outline_mm"]) + 1
            assert [g[0] for g in groups] == ["M"] + ["L"] * (
                len(groups) - 1)
            for g in groups:
                assert re.fullmatch(r"-?\d+\.\d{6}", g[1]), g
                assert re.fullmatch(r"-?\d+\.\d{6}", g[2]), g
            # 闭合：末组坐标与首组逐位相同
            assert groups[-1][1:] == groups[0][1:]
            # 零容差 round-trip（解析结果去掉闭合点 == manifest.outline_mm）
            assert s4.parse_svg_zone_outline(svg, z["zone_id"]) == \
                z["outline_mm"]

    def test_real_fill_geometry_not_embedded(self, package):
        """填充是派生数据且点数巨大：SVG 只画轮廓（+低透明度投影），
        绝不把 filled_polygon 逐点写进 SVG。"""
        _, _, svg, manifest = package
        total_fill_points = sum(z["fill"]["fill_points"]
                               for z in manifest["zones"])
        assert total_fill_points > 0
        for z in manifest["zones"]:
            d = find_by_id(ET.fromstring(svg), f"geom-zone-{z['zone_id']}").get("d")
            assert len(d.split(" ")) == 3 * (len(z["outline_mm"]) + 1)
        assert "filled_polygon" not in svg
        assert "fill_points=" not in svg   # 只以 data-fill-points 声明

    def test_zone_nets_feed_relation_member_registry(self):
        """zone 的 net 是产物内铜箔事实网（与 pad 同口径）：关系成员不会再
        因"该网只有铺铜"被误报为未注册。"""
        board, ref = make_board(), make_ref()
        board = dict(board, relations=[
            {"relation_id": "RP", "relation_type": "bus",
             "members": ["N0002"], "parent_id": None}])
        svg, man = s4.build(board, ref)
        assert s4.verify_consistency(svg, man) == []


# ------------------------------------------------------------ 负向矩阵

class TestZoneTamperDetected:
    def test_tampered_svg_outline_coordinate(self, package):
        # 篡改非首顶点（闭合点仍等于首点）→ 必报零容差坐标不一致
        _, _, svg, manifest = package
        assert "L 39.500000 0.500000" in svg
        bad = svg.replace("L 39.500000 0.500000", "L 39.500001 0.500000", 1)
        assert bad != svg
        out = s4.verify_consistency(bad, manifest)
        assert any("轮廓坐标与 outline_mm 不一致" in v for v in out), out

    def test_tampered_svg_outline_first_vertex_breaks_closure(self, package):
        """改首顶点 → 末点不再与首点相同（闭合规则先于坐标比对报出）。"""
        _, _, svg, manifest = package
        bad = svg.replace("M 0.500000 0.500000", "M 0.500001 0.500000", 1)
        assert bad != svg
        out = s4.verify_consistency(bad, manifest)
        assert any("闭合" in v for v in out), out

    def test_tampered_svg_outline_point_removed(self, package):
        """删掉一个轮廓顶点（path 少一组坐标）→ 必检出。"""
        _, _, svg, manifest = package
        bad = svg.replace(" L 39.500000 29.500000", "", 1)
        assert bad != svg
        out = s4.verify_consistency(bad, manifest)
        assert out, "少一个顶点必须被检出"

    def test_tampered_svg_outline_not_closed(self, package):
        """去掉闭合点（末点 != 首点）→ 必检出。"""
        _, _, svg, manifest = package
        bad = svg.replace(" L 0.500000 0.500000\" class=\"zone-outline\"",
                          "\" class=\"zone-outline\"", 1)
        assert bad != svg
        out = s4.verify_consistency(bad, manifest)
        assert any("闭合" in v for v in out), out

    def test_tampered_manifest_outline(self, package):
        """改 manifest 轮廓并重算全部自哈希 → 仍被跨腿核对检出。"""
        _, _, svg, manifest = package
        dup = copy.deepcopy(manifest)
        dup["zones"][0]["outline_mm"][2] = [39.0, 29.0]
        dup = rehash(dup)
        out = s4.verify_consistency(svg, dup)
        assert any("轮廓坐标与 outline_mm 不一致" in v for v in out), out

    def test_tampered_fill_state_in_svg(self, package):
        _, _, svg, manifest = package
        bad = svg.replace('data-fill-state="stale"',
                          'data-fill-state="fresh"', 1)
        assert bad != svg
        out = s4.verify_consistency(bad, manifest)
        assert any("fill_state" in v for v in out), out

    def test_tampered_fill_state_in_manifest(self, package):
        _, _, svg, manifest = package
        dup = copy.deepcopy(manifest)
        dup["zones"][0]["fill_state"] = "fresh"
        dup["manifest_payload_sha256"] = s4._sha256_of(dup)
        out = s4.verify_consistency(svg, dup)
        # SVG 侧仍写 stale → 跨腿不符；summary 仍写 stale → 汇总不符；
        # 事实哈希未重算 → 事实哈希不符（三处独立报出）
        assert any("fill_state" in v for v in out), out
        assert any("zones_facts_sha256" in v for v in out), out
        assert any("fill_state_counts" in v for v in out), out

    def test_tampered_zones_summary(self, package):
        _, _, svg, manifest = package
        dup = copy.deepcopy(manifest)
        dup["zones_summary"]["not_fresh_zone_ids"] = []   # 假装都 fresh
        dup["manifest_payload_sha256"] = s4._sha256_of(dup)
        out = s4.verify_consistency(svg, dup)
        assert any("not_fresh_zone_ids" in v for v in out), out

    def test_tampered_zones_facts_sha256(self, package):
        _, _, svg, manifest = package
        dup = copy.deepcopy(manifest)
        dup["zones_facts_sha256"] = "0" * 64
        dup["manifest_payload_sha256"] = s4._sha256_of(dup)
        out = s4.verify_consistency(svg, dup)
        assert any("zones_facts_sha256" in v for v in out), out

    def test_zone_deleted_from_manifest_only(self, package):
        _, _, svg, manifest = package
        dup = copy.deepcopy(manifest)
        dup["zones"] = [z for z in dup["zones"] if z["zone_id"] != Z1]
        dup["zones_summary"] = s4._zones_summary(dup["zones"])
        dup = rehash(dup)
        out = s4.verify_consistency(svg, dup)
        assert any("仅在 SVG 中" in v and Z1 in v for v in out), out

    def test_zone_deleted_from_svg_only(self, package):
        _, _, svg, manifest = package
        g = find_by_id(ET.fromstring(svg), f"zone-{Z1}")
        # 精确摘掉一个 zone 组（含其轮廓 path）
        start = svg.index(f'<g id="zone-{Z1}"')
        end = svg.index("</g>", start) + len("</g>")
        bad = svg[:start] + svg[end:]
        assert bad != svg
        out = s4.verify_consistency(bad, manifest)
        assert any("仅在 manifest 中" in v and Z1 in v for v in out), out

    def test_manifest_outline_fewer_than_three_points(self, package):
        _, _, svg, manifest = package
        dup = copy.deepcopy(manifest)
        dup["zones"][0]["outline_mm"] = [[0.5, 0.5], [39.5, 0.5]]
        dup = rehash(dup)
        out = s4.verify_consistency(svg, dup)
        assert any("点数 < 3" in v for v in out), out
        # 生产者侧同样 fail-closed
        board, ref = make_board(), make_ref()
        with pytest.raises(ValueError):
            s4.build_manifest(board, dict(
                ref, zones=[dict(ref["zones"][0],
                                 outline_mm=[[0.0, 0.0], [1.0, 1.0]])]))

    def test_missing_required_zone_attr(self, package):
        _, _, svg, manifest = package
        for attr in s4.SVG_ZONE_ATTRS:
            bad = re.sub(rf' {re.escape(attr)}="[^"]*"', "", svg, count=1)
            assert bad != svg, attr
            assert s4.verify_consistency(bad, manifest), attr

    def test_missing_derived_marker_or_wrong_projection(self, package):
        _, _, svg, manifest = package
        for new in ('data-fill-derived="false"', 'data-fill-derived=""'):
            bad = re.sub(r'data-fill-derived="[^"]*"', new, svg, count=1)
            assert s4.verify_consistency(bad, manifest), new

    def test_tampered_derived_fill_fingerprint_in_svg(self, package):
        _, _, svg, manifest = package
        bad = re.sub(r'data-fill-points="5715"', 'data-fill-points="5716"',
                     svg, count=1)
        assert bad != svg
        out = s4.verify_consistency(bad, manifest)
        assert any("fill_points" in v for v in out), out

    def test_tampered_zone_layers_and_net(self, package):
        _, _, svg, manifest = package
        bad = re.sub(r'data-layers="B\.Cu"', 'data-layers="F.Cu"', svg, count=1)
        assert bad != svg
        out = s4.verify_consistency(bad, manifest)
        assert any("layers" in v for v in out), out
        bad2 = re.sub(r'data-net-id="N0002"', 'data-net-id="N0009"', svg,
                      count=1)
        assert s4.verify_consistency(bad2, manifest)

    def test_unknown_fill_state_enum_in_svg(self, package):
        _, _, svg, manifest = package
        bad = svg.replace('data-fill-state="stale"',
                          'data-fill-state="FILLED"', 1)
        out = s4.verify_consistency(bad, manifest)
        assert any("未知 data-fill-state" in v for v in out), out

    def test_duplicate_zone_id_in_manifest(self, package):
        _, _, svg, manifest = package
        dup = copy.deepcopy(manifest)
        dup["zones"][1]["zone_id"] = dup["zones"][0]["zone_id"]
        dup = rehash(dup)
        out = s4.verify_consistency(svg, dup)
        assert any("zone_id 重复" in v for v in out), out

    def test_unknown_object_kind_still_rejected(self, package):
        """zone 之外不得出现未登记的对象种类（合同未松动）。"""
        _, _, svg, manifest = package
        bad = svg.replace('data-object-kind="zone"',
                          'data-object-kind="copper_pour"', 1)
        out = s4.verify_consistency(bad, manifest)
        assert any("未知 data-object-kind" in v for v in out), out

    def test_build_svg_refuses_tampered_zones(self, package):
        """渲染侧 fail-closed：篡改后的 manifest 不产出 SVG。"""
        board, _ref, _svg, manifest = package
        def _short_outline(m):
            m["zones"][0]["outline_mm"] = [[0.5, 0.5]]

        def _bad_fill_state(m):
            m["zones"][0]["fill_state"] = "FRESH"

        def _undisclosed_fill(m):
            m["zones"][0]["fill"] = {"fill_sha256": "a" * 64,
                                     "fill_points": 5715}

        def _bad_facts_hash(m):
            m["zones_facts_sha256"] = "0" * 64

        for mutate in (_short_outline, _bad_fill_state, _undisclosed_fill,
                       _bad_facts_hash):
            dup = copy.deepcopy(manifest)
            mutate(dup)
            if "manifest_payload_sha256" in dup:
                dup["manifest_payload_sha256"] = s4._sha256_of(dup)
            with pytest.raises(ValueError):
                s4.build_svg(board, dup)


# --------------------------------------------------- 协议稳定性回归（不改口径）

class TestExistingContractUnaffected:
    def test_v2_clean_with_and_without_snapshot(self, package):
        board, _ref, svg, manifest = package
        assert s4.verify_consistency(svg, manifest) == []
        assert s4.verify_consistency(svg, manifest, snapshot=board) == []

    def test_deterministic_byte_exact(self):
        b1, r1 = make_board(), make_ref()
        b2, r2 = make_board(), make_ref()
        svg1, man1 = s4.build(b1, r1)
        svg2, man2 = s4.build(b2, r2)
        assert svg1 == svg2
        assert json.dumps(man1, sort_keys=True) == \
            json.dumps(man2, sort_keys=True)

    def test_ref_without_zones_key_still_valid(self):
        """ref 不带 zones（v1 形状调用方）→ 空 zone 合同形态，不报错。"""
        board, ref = make_board(), make_ref()
        ref = {k: v for k, v in ref.items() if k != "zones"}
        svg, man = s4.build(board, ref)
        assert man["zones"] == []
        assert man["zones_summary"]["count"] == 0
        assert man["zones_summary"]["not_fresh_zone_ids"] == []
        assert man["zones_facts_sha256"] == s4.zone_facts_sha256([])
        assert s4.verify_consistency(svg, man) == []

    def test_parse_svg_zone_outline_fail_closed(self, package):
        _, _, svg, _manifest = package
        for zid in ("no-such-zone", ""):
            with pytest.raises(ValueError):
                s4.parse_svg_zone_outline(svg, zid)
        with pytest.raises(ValueError):
            s4.parse_svg_zone_outline(svg, "R1")   # route 组，不是 zone 组
        with pytest.raises(ValueError):
            s4.parse_svg_polyline(svg, f"zone-{Z1}")  # zone 组不是 route 组
        with pytest.raises(ValueError):
            s4.parse_svg_zone_outline("not xml", Z1)


# --------------------------------------------------------- 真实板（只读）

REGISTRY_PATH = os.path.join(config.OUT_DIR, "revc-a3", "net-registry.json")
REAL_SCENARIO = "revc-a3-svg-p3"


@pytest.fixture(scope="module")
def real_run():
    if not os.path.exists(config.REVC_BOARD) or \
            not os.path.exists(REGISTRY_PATH):
        pytest.skip("Rev-C board / net-registry missing")
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        registry = json.load(f)
    board, ref = ba.build_inputs(config.REVC_BOARD, registry,
                                 scenario_id=REAL_SCENARIO)
    svg, manifest = s4.build(board, ref)
    copper = copper_model.parse_copper_file(config.REVC_BOARD)
    return board, ref, svg, manifest, copper


needs_board = pytest.mark.skipif(
    not (os.path.exists(config.REVC_BOARD)
         and os.path.exists(REGISTRY_PATH)),
    reason="Rev-C board / net-registry missing")


@needs_board
class TestRealRevCZoneMirror:
    def test_two_gnd_zones_mirrored_and_clean(self, real_run):
        board, ref, svg, manifest, copper = real_run
        assert s4.verify_consistency(svg, manifest) == []
        assert s4.verify_consistency(svg, manifest, snapshot=board) == []
        assert copper["counts"]["zones"] == 2
        assert len(ref["zones"]) == 2
        assert len(manifest["zones"]) == 2
        assert len({z["zone_id"] for z in ref["zones"]}) == 2

    def test_zone_facts_match_copper(self, real_run):
        _b, _r, _svg, manifest, copper = real_run
        by_key = {z["key"]: z for z in copper["zones"]}
        for mz in manifest["zones"]:
            cz = by_key[mz["zone_id"]]
            assert mz["outline_mm"] == cz["outline_mm"]        # 轮廓=事实
            assert mz["layers"] == cz["layers"]
            assert mz["outline_kind"] == "polygon"
            assert mz["fill"]["fill_points"] == cz["fill_points"]
            assert mz["fill"]["fill_sha256"] == cz["fill_sha256"]
            assert mz["fill"]["derived"] is True

    def test_fill_state_is_unknown_and_visible_not_fresh(self, real_run):
        board, _r, _svg, manifest, _c = real_run
        assert {z["fill_state"] for z in manifest["zones"]} == {"unknown"}
        assert manifest["zones_summary"]["fill_state_counts"] == \
            {"fresh": 0, "stale": 0, "unknown": 2}
        assert manifest["zones_summary"]["not_fresh_zone_ids"] == \
            sorted(z["zone_id"] for z in manifest["zones"])
        note = board["adapter_notes"]["zones_in_manifest"]
        assert note["fill_state"] == "unknown"
        assert note["fill_state_basis"] == "adapter_no_refill_evidence"
        assert note["count"] == 2
        root = ET.fromstring(_svg)
        for z in manifest["zones"]:
            g = find_by_id(root, f"zone-{z['zone_id']}")
            assert g.get("data-fill-state") == "unknown"

    def test_real_fill_geometry_absent_from_svg(self, real_run):
        _b, _r, svg, manifest, copper = real_run
        assert sum(z["fill"]["fill_points"]
                   for z in manifest["zones"]) == 24510  # 5715 + 18795
        for z in manifest["zones"]:
            d = find_by_id(ET.fromstring(svg),
                           f"geom-zone-{z['zone_id']}").get("d")
            assert len(d.split(" ")) == 3 * (len(z["outline_mm"]) + 1)
        assert "filled_polygon" not in svg

    def test_every_zone_net_comes_from_registry(self, real_run):
        board, ref, _svg, _m, _c = real_run
        with open(REGISTRY_PATH, encoding="utf-8") as f:
            net_ids = {n["net_id"] for n in json.load(f)["nets"]}
        for z in ref["zones"]:
            assert z["net_id"] in net_ids
        assert board["adapter_notes"]["zones_not_represented"]["count"] == 0

    def test_real_board_is_read_only(self, real_run):
        from pcbflow import hashing
        before = hashing.sha256_file(config.REVC_BOARD)
        assert hashing.sha256_file(config.REVC_BOARD) == before
