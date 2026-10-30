"""P1a 铜箔事实模型（pcbflow/copper_model.py）测试。

覆盖：
- 冻结 API：parse_copper 恰好 10 个顶层键、字段名/量化口径（坐标 6 位、
  宽度/尺寸/钻孔 3 位）；
- 身份：uuid 原样（kicad_uuid）/ 几何回退 G:<16hex>（geometric_fallback）/
  混合（mixed）；uuid 被 ≥2 个铜箔节点共享（真实 Rev-C 板：路由级内容
  派生 uuid）→ `"<uuid>@<digest>"` 消歧并逐条登记 identity_disambiguated，
  **不进** unrepresentable；identity_map 对每个节点各一条、span 就是该
  节点自身字节跨度；digest 只含节点自身事实 → 同键其它节点改几何时本
  节点 key 不漂移；消歧后仍撞键（同 uuid 且几何全同）→
  identity_key_collision（fail-closed 残留，绝不静默并合）；
- canonical：CRLF/空白无关；事实变则铜箔哈希变；zone 填充（KiCad 派生）
  不进 copper_sha256，但 fill_sha256/fill_points 单独可查；
- fail-closed 负向：顶层 arc、无轮廓 zone、结构非法 segment/via、
  未识别铜类顶层节点、板文本括号不平衡 —— 一律进 unrepresentable
  （kind/where/reason 齐备），绝不静默丢弃；
- 守恒：板上顶层节点数 == 已解析对象数 + 对应的 unrepresentable 条数；
- 真实板只读抽样（config.REVC_BOARD）与 KiCad5 语料（datasets/pcbench-r1）
  只读抽样；断言解析器不写板文件（前后 sha256 相同）。
"""

import glob
import os
import re

import pytest

import revc_board_fixture
from pcbflow import config, copper_model as cm, hashing
from pcbflow.board_writer import _top_level_nodes

SCHEMA_KEYS = {"schema", "identity_basis", "segments", "vias", "zones",
               "unrepresentable", "identity_disambiguated", "counts",
               "identity_map", "copper_sha256"}

SYNTH = """(kicad_pcb (version 20260206) (generator "pcbnew")
\t(general
\t\t(thickness 1.6)
\t)
\t(layers
\t\t(0 "F.Cu" signal)
\t\t(2 "B.Cu" signal)
\t\t(4 "In1.Cu" signal)
\t\t(6 "In2.Cu" signal)
\t)
\t(gr_line
\t\t(start 0 0) (end 70 0) (layer "Edge.Cuts") (width 0.05)
\t)
\t(segment
\t\t(start 10.0 20.0)
\t\t(end 10.0 25.0)
\t\t(width 0.25)
\t\t(layer "F.Cu")
\t\t(net "N1")
\t\t(uuid "aaaaaaaa-1111-2222-3333-444444444444")
\t)
\t(segment
\t\t(start 10.0 25.0)
\t\t(end 12.5 25.0)
\t\t(width 0.25)
\t\t(layer "F.Cu")
\t\t(net "N1")
\t\t(uuid "bbbbbbbb-1111-2222-3333-444444444444")
\t)
\t(segment
\t\t(start 20.0 20.0)
\t\t(end 20.0 30.0)
\t\t(width 0.3)
\t\t(layer "F.Cu")
\t\t(net "N2")
\t)
\t(via buried
\t\t(at 10.0 22.0)
\t\t(size 0.7)
\t\t(drill 0.4)
\t\t(layers "F.Cu" "In2.Cu")
\t\t(net "N1")
\t\t(uuid "cccccccc-1111-2222-3333-444444444444")
\t)
\t(zone
\t\t(net "GND")
\t\t(layer "B.Cu")
\t\t(uuid "dddddddd-1111-2222-3333-444444444444")
\t\t(hatch edge 0.5)
\t\t(connect_pads (clearance 0.2))
\t\t(min_thickness 0.2)
\t\t(fill yes
\t\t\t(thermal_gap 0.5)
\t\t\t(thermal_bridge_width 0.5)
\t\t\t(island_removal_mode 0)
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

UUID_A = "aaaaaaaa-1111-2222-3333-444444444444"
UUID_B = "bbbbbbbb-1111-2222-3333-444444444444"
UUID_V = "cccccccc-1111-2222-3333-444444444444"
UUID_Z = "dddddddd-1111-2222-3333-444444444444"

KICAD5 = """(kicad_pcb (version 20171130) (host pcbnew "(5.1.12)-1")
  (general
    (thickness 1.6)
  )
  (layers
    (0 F.Cu signal)
    (31 B.Cu signal)
  )
  (segment (start 1 2) (end 3 4) (width 0.25) (layer F.Cu) (net 7))
  (segment (start 3 4) (end 3 9) (width 0.25) (layer F.Cu) (net 7) (status 30))
  (via (at 2 3) (size 0.8) (drill 0.4) (layers F.Cu B.Cu) (net 7))
  (via (at 5 5) (size 0.6) (layers F.Cu B.Cu) (net 7))
  (zone (net 1) (net_name GND) (layer B.Cu) (tstamp 5EE4015E) (hatch edge 0.508)
    (connect_pads (clearance 0.254))
    (min_thickness 0.254)
    (fill yes (arc_segments 32) (thermal_gap 0.508) (thermal_bridge_width 0.508))
    (polygon
      (pts
        (xy 0 0) (xy 9 0) (xy 9 9) (xy 0 9)
      )
    )
    (filled_polygon
      (pts
        (xy 0.2 0.2) (xy 8.8 0.2)
      )
    )
  )
)
"""


def kinds(model):
    out = {}
    for u in model["unrepresentable"]:
        out[u["kind"]] = out.get(u["kind"], 0) + 1
    return out


def _corpus_boards():
    """KiCad5 语料板（datasets/pcbench-r1/raw/*/raw.kicad_pcb）路径。"""
    return sorted(glob.glob(os.path.join(
        config.PCBFLOW_ROOT, "datasets", "pcbench-r1", "raw", "*",
        "raw.kicad_pcb")))


# ----------------------------------------------------- 冻结 API 与基本形状

def test_parse_copper_top_level_keys_exact():
    r = cm.parse_copper(SYNTH)
    assert set(r.keys()) == SCHEMA_KEYS
    assert r["schema"] == cm.SCHEMA == "pcbflow.copper-model/1"


def test_counts_and_identity_basis_mixed():
    r = cm.parse_copper(SYNTH)
    assert r["counts"] == {"segments": 3, "vias": 1, "zones": 1}
    assert r["identity_basis"] == cm.IDENTITY_MIXED
    assert r["unrepresentable"] == []
    assert r["identity_disambiguated"] == []   # uuid 全唯一 → 无需消歧
    # counts 仍是三段式（消歧统计在 counts 之外的信息性键里）
    assert set(r["counts"]) == {"segments", "vias", "zones"}


def test_uuid_identity_is_uuid_as_is():
    r = cm.parse_copper(SYNTH)
    for key in (UUID_A, UUID_B, UUID_V, UUID_Z):
        assert key in r["identity_map"]
    for s in r["segments"]:
        if s["uuid"]:
            assert s["key"] == s["uuid"]


def test_geometric_fallback_key_shape_and_determinism():
    r = cm.parse_copper(SYNTH)
    fb = [s for s in r["segments"] if s["uuid"] is None]
    assert len(fb) == 1
    key = fb[0]["key"]
    assert key.startswith("G:") and len(key) == 18
    assert re.fullmatch(r"G:[0-9a-f]{16}", key)
    # 同内容 → 同 key（纯函数确定性）
    assert key in cm.parse_copper(SYNTH)["identity_map"]
    # 几何变化 → key 变化（同一 net/layer 下）
    moved = SYNTH.replace("(start 20.0 20.0)", "(start 20.0 21.0)")
    assert cm.parse_copper(moved)["segments"][0]["key"] != key


def test_identity_map_spans_slice_node_text():
    r = cm.parse_copper(SYNTH)
    assert set(r["identity_map"]) == set(
        s["key"] for s in r["segments"]) | set(v["key"] for v in r["vias"]) \
        | set(z["key"] for z in r["zones"])
    # 每个铜箔节点各一条（不是每个 key 一条）
    assert len(r["identity_map"]) == sum(r["counts"].values())
    for kind, tag in (("segment", "segment"), ("via", "via"), ("zone", "zone")):
        keys = [k for k, v in r["identity_map"].items() if v["kind"] == kind]
        for key in keys:
            s, e = r["identity_map"][key]["span"]
            assert SYNTH[s:e].startswith("(%s" % tag)
            assert SYNTH[s:e].count("(") == SYNTH[s:e].count(")")
    # index 是排序后列表内的下标，且 span 能独立切出该对象的节点文本
    for key, rec in r["identity_map"].items():
        lst = {"segment": r["segments"], "via": r["vias"],
               "zone": r["zones"]}[rec["kind"]]
        assert lst[rec["index"]]["key"] == key
        s, e = rec["span"]
        assert SYNTH[s:e].startswith("(%s" % rec["kind"])
        assert SYNTH[s:e].count("(") == SYNTH[s:e].count(")")


def by_key(model, kind):
    return {e["key"]: e for e in model[kind]}


def test_field_names_and_quantization():
    r = cm.parse_copper(SYNTH)
    assert set(r["segments"][0]) == {"uuid", "key", "net", "layer", "width",
                                     "start", "end"}
    assert set(r["vias"][0]) == {"uuid", "key", "net", "at", "size", "drill",
                                 "layers", "via_kind"}
    assert set(r["zones"][0]) == {"uuid", "key", "net", "layers", "outline_mm",
                                  "fill_points", "fill_sha256", "params"}
    v = by_key(r, "vias")[UUID_V]
    assert v["at"] == [10.0, 22.0] and v["size"] == 0.7 and v["drill"] == 0.4
    assert v["layers"] == ["F.Cu", "In2.Cu"] and v["via_kind"] == "buried"
    # 3 位量化：更精细的宽度被归到 3 位；6 位量化：坐标
    q = cm.parse_copper(SYNTH.replace("(width 0.25)\n\t\t(layer \"F.Cu\")\n\t\t"
                                      "(net \"N1\")\n\t\t(uuid \"%s\")" % UUID_A,
                                      "(width 0.250456789)\n\t\t(layer \"F.Cu\")"
                                      "\n\t\t(net \"N1\")\n\t\t(uuid \"%s\")"
                                      % UUID_A))
    assert by_key(q, "segments")[UUID_A]["width"] == 0.25
    p = cm.parse_copper(SYNTH.replace("(start 10.0 20.0)",
                                      "(start 10.0000001 20.0)"))
    assert by_key(p, "segments")[UUID_A]["start"] == [10.0, 20.0]


def test_zone_outline_layers_fill_and_params():
    z = cm.parse_copper(SYNTH)["zones"][0]
    assert z["net"] == "GND" and z["layers"] == ["B.Cu"]
    assert z["outline_mm"] == [[0.0, 0.0], [30.0, 0.0], [30.0, 40.0],
                               [0.0, 40.0]]
    assert z["fill_points"] == 3
    assert re.fullmatch(r"[0-9a-f]{64}", z["fill_sha256"])
    assert z["params"]["fill"] == "yes"
    assert z["params"]["min_thickness"] == 0.2
    assert z["params"]["clearance"] == 0.2
    assert z["params"]["hatch"] == "edge 0.5"
    assert z["params"]["fill_island_removal_mode"] == 0


# ------------------------------------------------------------ canonical

def test_canonical_hash_ignores_whitespace_and_line_endings():
    base = cm.parse_copper(SYNTH)["copper_sha256"]
    assert re.fullmatch(r"[0-9a-f]{64}", base)
    assert cm.parse_copper(SYNTH.replace("\n", "\r\n"))["copper_sha256"] == base
    assert cm.parse_copper(SYNTH.replace("\t", "   "))["copper_sha256"] == base
    assert cm.parse_copper(SYNTH + "\n")["copper_sha256"] == base


def test_canonical_hash_tracks_copper_facts():
    base = cm.parse_copper(SYNTH)["copper_sha256"]
    for mut in ("(start 10.0 20.0)", '(net "N1")', "(width 0.25)",
                '(layer "F.Cu")'):
        moved = SYNTH.replace(mut, mut.replace("10.0 20.0", "10.0 20.5")
                              .replace('"N1"', '"N5"')
                              .replace("0.25", "0.35")
                              .replace('"F.Cu"', '"In1.Cu"'), 1)
        assert moved != SYNTH
        assert cm.parse_copper(moved)["copper_sha256"] != base


def test_zone_fill_geometry_excluded_from_fact_hash():
    base = cm.parse_copper(SYNTH)
    changed = cm.parse_copper(SYNTH.replace("(xy 0.1 0.1)", "(xy 0.15 0.15)"))
    assert changed["copper_sha256"] == base["copper_sha256"]
    assert changed["zones"][0]["fill_sha256"] != base["zones"][0]["fill_sha256"]
    # 但轮廓变化必须改变事实哈希
    outline = cm.parse_copper(SYNTH.replace("(xy 30 40)", "(xy 30 41)"))
    assert outline["copper_sha256"] != base["copper_sha256"]


# ---------------------------------------------------------- fail-closed

def test_top_level_arc_reported_not_dropped():
    arc = SYNTH.replace("\t(zone", """\t(arc
\t\t(start 1 1) (mid 2 2) (end 3 1) (width 0.2)
\t\t(layer "F.Cu")
\t\t(net "N1")
\t)
\t(zone""")
    r = cm.parse_copper(arc)
    assert kinds(r) == {"arc_track": 1}
    u = r["unrepresentable"][0]
    assert set(u) == {"kind", "where", "reason"} and u["where"] and u["reason"]
    assert r["counts"] == {"segments": 3, "vias": 1, "zones": 1}


def test_zone_without_outline_reported():
    r = cm.parse_copper(SYNTH.replace(
        "\t\t(polygon\n\t\t\t(pts\n\t\t\t\t(xy 0 0) (xy 30 0) (xy 30 40) (xy 0 40)\n\t\t\t)\n\t\t)\n", ""))
    assert kinds(r) == {"zone_no_outline": 1}
    assert r["counts"]["zones"] == 0


def test_malformed_segment_and_via_reported():
    no_width = SYNTH.replace("\t\t(width 0.3)\n", "")
    r = cm.parse_copper(no_width)
    assert kinds(r) == {"segment_malformed": 1}
    assert r["counts"]["segments"] == 2
    assert "width" in r["unrepresentable"][0]["reason"]

    no_drill = SYNTH.replace("\t\t(drill 0.4)\n", "")
    r2 = cm.parse_copper(no_drill)
    assert kinds(r2) == {"via_malformed": 1}
    assert r2["counts"]["vias"] == 0


def test_unrecognized_copper_top_node_reported():
    copper_gr = SYNTH.replace("\t(segment", """\t(gr_line
\t\t(start 0 0) (end 5 5) (layer "F.Cu") (width 0.2)
\t)
\t(segment""", 1)
    r = cm.parse_copper(copper_gr)
    assert kinds(r) == {"unrecognized_copper_node": 1}
    # 非铜层（Edge.Cuts / F.SilkS）的图形节点不报（不误报）
    assert cm.parse_copper(SYNTH)["unrepresentable"] == []
    silk = SYNTH.replace('(layer "Edge.Cuts")', '(layer "F.SilkS")')
    assert cm.parse_copper(silk)["unrepresentable"] == []
    # footprint/module 内的 pad 铜不在 P1a 铜箔范围（不误报）
    fp = SYNTH.replace("\t(segment", """\t(footprint "R_0603" (layer "F.Cu")
\t\t(pad "1" smd roundrect (at 0 0) (size 1 1) (layers "F.Cu" "F.Paste" "F.Mask"))
\t)
\t(segment""", 1)
    assert cm.parse_copper(fp)["unrepresentable"] == []


def test_route_level_uuid_shared_disambiguated_not_unrepresentable():
    """真实 Rev-C 同款：路由级 uuid 被同一条 route 的多个对象共享。

    共享**不是**"不可表示"：两个对象各得 `"<uuid>@<digest>"` 唯一 key，
    登记到 identity_disambiguated，unrepresentable 保持为空，对象全保留。
    """
    dup = SYNTH.replace(UUID_B, UUID_A)
    r = cm.parse_copper(dup)
    assert r["counts"]["segments"] == 3          # 对象保留（不丢弃）
    assert r["unrepresentable"] == []            # 不再报"不可表示"
    assert len(r["identity_disambiguated"]) == 2
    for d in r["identity_disambiguated"]:
        assert set(d) == {"key", "uuid", "kind", "reason"}
        assert d["uuid"] == UUID_A and d["kind"] == "segment"
        assert d["reason"] == cm.IDENTITY_DISAMBIGUATED_REASON
        assert d["key"].startswith(UUID_A + "@")
        assert re.fullmatch(re.escape(UUID_A) + r"@[0-9a-f]{12}", d["key"])
    # 同 uuid 但几何不同 → 两个 key 不同；裸 uuid 不再是 key
    shared = [s for s in r["segments"] if s["uuid"] == UUID_A]
    assert len(shared) == 2 and shared[0]["key"] != shared[1]["key"]
    assert UUID_A not in r["identity_map"]
    # identity_map 每个对象各一条（含被消歧者），span 各归自身
    assert len(r["identity_map"]) == 5
    for s in shared:
        st, en = r["identity_map"][s["key"]]["span"]
        assert dup[st:en].startswith("(segment")
        assert "(uuid \"%s\")" % UUID_A in dup[st:en]
    # 事实哈希仍覆盖两个对象（内容不同 → 哈希与原始不同）
    assert r["copper_sha256"] != cm.parse_copper(SYNTH)["copper_sha256"]


def test_disambiguated_key_does_not_drift_when_sibling_changes():
    """同 uuid 的两个 segment：改掉其一的几何，另一个的 key 必须不变。

    digest 只含节点自身事实（无序号/索引/文档位置），这是"不漂移"的关键
    证据 —— 补丁引擎对某节点的寻址键不会因同键其它节点增删/改几何而失效。
    """
    def shared_by_start(text):
        return {tuple(s["start"]): s["key"]
                for s in cm.parse_copper(text)["segments"]
                if s["uuid"] == UUID_A}

    dup = SYNTH.replace(UUID_B, UUID_A)
    before = shared_by_start(dup)
    assert len(before) == 2
    # 只改第一个共享节点（start 10.0 20.0 的那个）的 end
    moved = dup.replace("(start 10.0 20.0)\n\t\t(end 10.0 25.0)",
                        "(start 10.0 20.0)\n\t\t(end 10.0 25.5)")
    assert moved != dup
    after = shared_by_start(moved)
    assert len(after) == 2
    assert before[(10.0, 20.0)] != after[(10.0, 20.0)]   # 被改者 key 变
    assert before[(10.0, 25.0)] == after[(10.0, 25.0)]   # 未改者 key 不变


def test_cross_kind_uuid_reuse_disambiguated_by_kind_prefix():
    """同一个 uuid 跨 segment/via 复用（Rev-C 有 2 例）：kind 前缀保证 digest 不同。"""
    cross = SYNTH.replace(UUID_V, UUID_A)
    r = cm.parse_copper(cross)
    assert r["unrepresentable"] == []
    assert len(r["identity_disambiguated"]) == 2
    seg_key = [s["key"] for s in r["segments"] if s["uuid"] == UUID_A][0]
    via_key = [v["key"] for v in r["vias"] if v["uuid"] == UUID_A][0]
    assert seg_key != via_key
    assert all(k.startswith(UUID_A + "@") for k in (seg_key, via_key))
    assert len(r["identity_map"]) == 5
    # 纯函数确定性：两次解析得到同一组 key
    assert [s["key"] for s in cm.parse_copper(cross)["segments"]] == \
        [s["key"] for s in r["segments"]]


def test_identical_geometry_same_uuid_is_residual_collision():
    """消歧后仍撞键（同 uuid 且几何全同）：fail-closed 残留，绝不静默并合。"""
    coll = SYNTH.replace(UUID_B, UUID_A).replace(
        "(start 10.0 25.0)\n\t\t(end 12.5 25.0)",
        "(start 10.0 20.0)\n\t\t(end 10.0 25.0)")
    r = cm.parse_copper(coll)
    assert r["counts"]["segments"] == 3          # 对象仍在（不丢弃）
    assert kinds(r) == {"identity_key_collision": 1}
    u = r["unrepresentable"][0]
    assert set(u) == {"kind", "where", "reason"} and u["where"] and u["reason"]
    # 摘要相同 → identity_map 只能表达首个 span（比对象数少 1）
    assert len(r["identity_map"]) == 4


def test_board_parse_error_refuses_partial_parse():
    r = cm.parse_copper("(kicad_pcb (segment (start 1 2) (end 3 4)")
    assert kinds(r) == {"board_parse_error": 1}
    assert r["counts"] == {"segments": 0, "vias": 0, "zones": 0}
    assert r["identity_map"] == {}


def test_parse_copper_rejects_non_str():
    with pytest.raises(ValueError):
        cm.parse_copper(None)


def test_blank_board_yields_empty_model():
    r = cm.parse_copper("(kicad_pcb (version 1))\n")
    assert r["counts"] == {"segments": 0, "vias": 0, "zones": 0}
    assert r["identity_basis"] == cm.IDENTITY_KICAD_UUID
    assert r["unrepresentable"] == [] and r["identity_map"] == {}


# ------------------------------------------------------ KiCad5 语料口径

def test_kicad5_unquoted_tokens_and_tstamp_not_identity():
    r = cm.parse_copper(KICAD5)
    assert r["identity_basis"] == cm.IDENTITY_GEOMETRIC_FALLBACK
    assert r["counts"] == {"segments": 2, "vias": 1, "zones": 1}
    assert all(s["key"].startswith("G:") for s in r["segments"])
    assert all(v["key"].startswith("G:") for v in r["vias"])
    assert all(z["key"].startswith("G:") for z in r["zones"])
    assert all(not k.startswith("5EE4015E") for k in r["identity_map"])
    # (net 7) 序号原样保留；zone 取 (net_name GND)
    assert r["segments"][0]["net"] == "7"
    assert r["zones"][0]["net"] == "GND"
    assert r["segments"][0]["layer"] == "F.Cu"
    assert r["vias"][0]["via_kind"] == "through"
    # 缺 drill 的 KiCad5 via 必须上报（fail-closed）
    assert kinds(r) == {"via_malformed": 1}
    # (status 30) 等扩展字段不影响解析
    assert r["segments"][1]["end"] == [3.0, 9.0]


# ------------------------------------------------- 守恒与扫描原语等价性

def test_census_agrees_with_board_writer():
    """原语（board_writer._top_level_nodes）与普查在原语能力域内跨度一致。"""
    texts = [SYNTH, KICAD5]
    if os.path.exists(config.REVC_BOARD):
        with open(config.REVC_BOARD, encoding="utf-8", newline="") as f:
            texts.append(f.read())
    for text in texts:
        census = {}
        for tag, s, e in cm._scan_all_top_level(text):
            census.setdefault(tag, []).append((s, e))
        for tag in ("segment", "via", "zone", "arc"):
            assert census.get(tag, []) == _top_level_nodes(text, tag)
        # parse_copper 认的跨度 == 原语跨度（文档序）
        assert cm.top_level_copper_nodes(text) == sorted(
            ((tag, s, e) for tag in ("segment", "via", "zone", "arc")
             for (s, e) in _top_level_nodes(text, tag)),
            key=lambda t: t[1])


def _conservation(text, model):
    """顶层节点数 == 已解析对象数 + 对应 unrepresentable 条数。"""
    k = kinds(model)
    assert len(_top_level_nodes(text, "segment")) == \
        model["counts"]["segments"] + k.get("segment_malformed", 0)
    assert len(_top_level_nodes(text, "via")) == \
        model["counts"]["vias"] + k.get("via_malformed", 0)
    assert len(_top_level_nodes(text, "zone")) == \
        model["counts"]["zones"] + k.get("zone_no_outline", 0) \
        + k.get("zone_malformed", 0)
    assert len(_top_level_nodes(text, "arc")) == k.get("arc_track", 0)


def test_conservation_on_synthetic_and_kicad5():
    _conservation(SYNTH, cm.parse_copper(SYNTH))
    _conservation(KICAD5, cm.parse_copper(KICAD5))


# ----------------------------------------------------------- 真实板抽样

BOARD_OK = os.path.exists(config.REVC_BOARD)
needs_board = pytest.mark.skipif(not BOARD_OK, reason="Rev-C board missing")


@needs_board
def test_real_board_counts_and_identity_basis(monkeypatch):
    # REPAIR-P1 W-5（铜环案 R4 三步法②）：精确计数/身份抽样改钉仓内冻结
    # 夹具板（与 2026-09-11 live 板 dbfea089 逐字节同，sha 锚 fail-closed），
    # 与 live 板演进解耦；live 不变量另见 test_real_board_live_invariants_only。
    monkeypatch.setattr(config, "REVC_BOARD", revc_board_fixture.fixture_board())
    r = cm.parse_copper_file(config.REVC_BOARD)
    assert r["schema"] == cm.SCHEMA
    # M1 刷新：counts=dbfea089 夹具板实测 2372/358/2（原 2026-09-11 live 口径
    # 原样保留，仅钉板）
    assert r["counts"] == {"segments": 2372, "vias": 358, "zones": 2}
    assert r["identity_basis"] == cm.IDENTITY_KICAD_UUID
    assert re.fullmatch(r"[0-9a-f]{64}", r["copper_sha256"])
    # identity_map 对每个铜箔节点各一条（2372 + 358 + 2 = 2732），key 全局唯一
    assert len(r["identity_map"]) == 2732
    assert len(r["identity_map"]) == sum(r["counts"].values())
    text = open(config.REVC_BOARD, encoding="utf-8", newline="").read()
    keys = set()
    for kind, items in (("segment", r["segments"]), ("via", r["vias"]),
                        ("zone", r["zones"])):
        for it in items:
            # key == uuid（唯一）或 "<uuid>@<digest12>"（共享，向后兼容前缀）
            assert it["key"].startswith(it["uuid"])
            assert it["key"] == it["uuid"] or re.fullmatch(
                re.escape(it["uuid"]) + r"@[0-9a-f]{12}", it["key"])
            keys.add(it["key"])
    assert len(keys) == 2732
    # 每个 key 的 span 都能切出该对象自身的节点文本（含被消歧者）
    for key, rec in r["identity_map"].items():
        s, e = rec["span"]
        assert text[s:e].startswith("(%s" % rec["kind"])
        assert text[s:e].count("(") == text[s:e].count(")")


@needs_board
def test_real_board_route_level_uuid_disambiguated_and_conserved(monkeypatch):
    # REPAIR-P1 W-5：钉冻结夹具板（精确消歧计数=dbfea089 板实测）。
    monkeypatch.setattr(config, "REVC_BOARD", revc_board_fixture.fixture_board())
    text = open(config.REVC_BOARD, encoding="utf-8", newline="").read()
    r = cm.parse_copper(text)
    # Rev-C 的 uuid 是路由级内容派生值 → APPLY-1 落线后实测 34 组共享、共 217
    # 个对象被消歧（210 segment + 7 via；含跨 segment/via 复用），
    # 但**没有**任何对象因此"不可表示"：unrepresentable == 0。
    # M1 刷新：消歧计数=dbfea089 夹具板实测 217/210/7（原口径原样保留）
    assert r["unrepresentable"] == []
    assert len(r["identity_disambiguated"]) == 217
    by_kind = {}
    for d in r["identity_disambiguated"]:
        assert d["reason"] == "route_level_uuid_shared"
        by_kind[d["kind"]] = by_kind.get(d["kind"], 0) + 1
    assert by_kind == {"segment": 210, "via": 7}
    # 消歧只影响共享 uuid 的 217 个对象；其余 2515 个保持裸 uuid key
    assert sum(1 for it in r["segments"] + r["vias"] + r["zones"]
               if "@" in it["key"]) == 217
    _conservation(text, r)


@needs_board
def test_real_board_disambiguated_keys_do_not_drift(monkeypatch):
    """同一 uuid 组内逐个 object 的 key 互不依赖（不漂移的实板证据）。

    Rev-C 最大组 38 个 segment 共享一个 uuid：删掉其中一个节点后，组内
    其余节点的 key 必须逐一不变。REPAIR-P1 W-5：钉冻结夹具板（组结构=
    dbfea089 板实测）。
    """
    monkeypatch.setattr(config, "REVC_BOARD", revc_board_fixture.fixture_board())
    text = open(config.REVC_BOARD, encoding="utf-8", newline="").read()
    target = "f9790e18-1099-55e8-7f05-75eb1d7fac6c"    # 38 个 segment 共享
    before = [s["key"] for s in cm.parse_copper(text)["segments"]
              if s["uuid"] == target]
    assert len(before) == 38
    # 用 copper_model 自己定位的 span 删掉该组的一个节点
    model = cm.parse_copper(text)
    victim = next(s for s in model["segments"] if s["uuid"] == target)
    s, e = model["identity_map"][victim["key"]]["span"]
    trimmed = text[:s] + text[e:]
    after = [x["key"] for x in cm.parse_copper(trimmed)["segments"]
             if x["uuid"] == target]
    assert len(after) == 37
    removed = set(before) - set(after)
    assert len(removed) == 1 and victim["key"] in removed
    assert set(after) == set(before) - removed          # 其余 37 个 key 全不变


@needs_board
def test_real_board_parse_is_read_only():
    before = hashing.sha256_file(config.REVC_BOARD)
    cm.parse_copper_file(config.REVC_BOARD)
    assert hashing.sha256_file(config.REVC_BOARD) == before


@needs_board
def test_real_board_live_invariants_only():
    """R4③ live 板不变量用例（REPAIR-P1 W-5）：live 板演进不破坏解析合同。

    只断板无关不变量（在新旧板上都成立），不带精确计数/身份抽样——
    那些由钉夹具板的用例守护；板变更登记走 design1_proposal 前缀与
    R28 live 登记用例。
    """
    text = open(config.REVC_BOARD, encoding="utf-8", newline="").read()
    r = cm.parse_copper(text)
    assert r["schema"] == cm.SCHEMA
    assert r["identity_basis"] == cm.IDENTITY_KICAD_UUID
    # 守恒：identity_map 对每个已解析节点恰一条且全局唯一
    assert len(r["identity_map"]) == sum(r["counts"].values())
    assert len({it["key"] for it in r["segments"] + r["vias"] + r["zones"]}) \
        == len(r["identity_map"])
    # 消歧合同：被消歧不是不可表示；key 形态要么裸 uuid 要么 uuid@digest12
    assert r["unrepresentable"] == []
    for it in r["segments"] + r["vias"] + r["zones"]:
        assert it["key"] == it["uuid"] or re.fullmatch(
            re.escape(it["uuid"]) + r"@[0-9a-f]{12}", it["key"])
    _conservation(text, r)
    assert re.fullmatch(r"[0-9a-f]{64}", r["copper_sha256"])


def test_negative_control_board_tamper_moves_counts():
    """负对照（R28「不得弱化」硬约束检出证明）：注入一个新 uuid 的 segment
    后计数与身份图随之 +1（2372→2373、2732→2733）——精确断言确实跟踪板
    字节，钉板改造没有把它们变成恒真。"""
    tampered = revc_board_fixture.duplicate_first_segment(
        revc_board_fixture.fixture_board_text())
    r = cm.parse_copper(tampered)
    assert r["counts"]["segments"] == 2373
    assert len(r["identity_map"]) == 2733
    assert r["unrepresentable"] == []
    assert r["counts"]["segments"] != 2372    # M1 精确值在此板内容下不成立


def test_kicad5_corpus_samples():
    boards = _corpus_boards()
    if not boards:
        pytest.skip("pcbench-r1 corpus missing")
    seen = 0
    for path in boards[:3]:
        text = open(path, encoding="utf-8", newline="").read()
        assert "(uuid" not in text  # KiCad5 语料：无 uuid
        r = cm.parse_copper(text)
        assert r["counts"]["segments"] > 0
        assert r["identity_basis"] == cm.IDENTITY_GEOMETRIC_FALLBACK
        assert all(s["key"].startswith("G:") for s in r["segments"])
        assert all(v["drill"] > 0 for v in r["vias"])
        for u in r["unrepresentable"]:
            assert set(u) == {"kind", "where", "reason"}
        _conservation(text, r)
        seen += 1
    assert seen == 3
