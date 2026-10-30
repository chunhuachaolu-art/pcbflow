# -*- coding: utf-8 -*-
"""Lane-DSN 测试（canvas/dsn_export.py，主审裁定 D-2 采纳件回归锚）。

- 板源=out/v5-p5/boards-pre-r1/{badgeleds-do-electronics,pmod-bme280}/board.json
  （冻结两端点世界；wrap 体口径=load_board_doc: json.load→raw["board"]→v5.board.load_board）。
- 面: fail-closed（形态异常/忠实缺 via≥10 例）、确定性双跑字节等（≥2 板×模式
  +canonical 序无关性）、DSN 结构断言（layers/boundary/via/rules/pads/network
  与板数据一致性）、原型已修陷阱钉死（refdes 连字符切分漂移、点号名 WARN 类）。
- 本文件零落盘（write_dsn 用例走 pytest tmp_path 系统临时域，不触仓库树）。
"""
import copy
import json
import os
import re

import pytest

from v5 import board as v5board

from canvas import dsn_export as de

_BOARD_ROOT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..",
    "out", "v5-p5", "boards-pre-r1"))
BADGE_PATH = os.path.join(_BOARD_ROOT, "badgeleds-do-electronics", "board.json")
PMOD_PATH = os.path.join(_BOARD_ROOT, "pmod-bme280", "board.json")

_CACHE = {}


def board_at(path):
    """真板只读加载（共享缓存）——wrap 体口径单源。"""
    if path not in _CACHE:
        _CACHE[path] = de.load_board_doc(path)
    return _CACHE[path]


def badge():
    return board_at(BADGE_PATH)


def pmod():
    return board_at(PMOD_PATH)


# ------------------------------------------------------------------ 合成底板

def synth_board(via_model=None):
    """合成微板（schema 完整、哈希链自洽）：workspace (0,0)-(20,10)。

    分区端点（mm）: P-A (2,2)-(10,2) / P.B (2,8)-(10,8) / P_C (12,4)-(18,6)；
    网: N1=[P-A, P.B]（双分区）、N2=[P_C]。焊盘 rect/circle 混合。
    """
    board = {
        "schema_version": "v5.board.v1",
        "board_id": "synth-dsn",
        "stackup": [
            {"id": "F.Cu", "kind": "signal", "preferred_direction": "any",
             "available": True},
            {"id": "B.Cu", "kind": "signal", "preferred_direction": "any",
             "available": True},
        ],
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 20.0, "y_max": 10.0},
        "zones": [],
        "partitions": [
            {"partition_id": "P-A", "ptype": "MISC", "current_a": 0,
             "speed_class": "unknown", "layer_policy": "any",
             "width_prior": {"w_min": 0.3, "w_max": 0.8},
             "geometry": {"endpoints": [[2.0, 2.0], [10.0, 2.0]],
                          "pad_terminals": [
                              {"endpoint": 0, "shape": "rect",
                               "size_mm": [1.0, 1.0], "layers": "all"},
                              {"endpoint": 1, "shape": "rect",
                               "size_mm": [1.0, 1.0], "layers": "all"}]}},
            {"partition_id": "P.B", "ptype": "MISC", "current_a": 0,
             "speed_class": "unknown", "layer_policy": "any",
             "width_prior": {"w_min": 0.3, "w_max": 0.8},
             "geometry": {"endpoints": [[2.0, 8.0], [10.0, 8.0]],
                          "pad_terminals": [
                              {"endpoint": 0, "shape": "circle",
                               "size_mm": [0.8], "layers": "all"},
                              {"endpoint": 1, "shape": "circle",
                               "size_mm": [0.8], "layers": "all"}]}},
            {"partition_id": "P_C", "ptype": "MISC", "current_a": 0,
             "speed_class": "unknown", "layer_policy": "any",
             "width_prior": {"w_min": 0.3, "w_max": 0.8},
             "geometry": {"endpoints": [[12.0, 4.0], [18.0, 6.0]],
                          "pad_terminals": [
                              {"endpoint": 0, "shape": "rect",
                               "size_mm": [1.2, 0.8], "layers": "F.Cu"},
                              {"endpoint": 1, "shape": "circle",
                               "size_mm": [1.0], "layers": "all"}]}},
        ],
        "nets": [
            {"net_id": "N1", "partitions": ["P-A", "P.B"]},
            {"net_id": "N2", "partitions": ["P_C"]},
        ],
        "hard_rules": {
            "R1": {"k_a": 0.4, "floor_mm": 0.3},
            "R2": {"min_distance_mm": 3.0, "max_parallel_mm": 5.0},
            "R3": {"unsplittable": True},
            "R4": {"return_via_required": True, "max_distance_mm": 2.0},
            "R5": {"min_clearance_mm": 0.5},
            "R6": {"plane_forbidden": True, "keepout_zones_forbidden": True},
        },
        "holes": [],
        "principle_registry": [],
        "provenance": {
            "source_type": "synthetic",
            "source_uri": "canvas-dsn-test-fixture",
            "source_sha256": "0" * 64,
            "adapter": "canvas-dsn-test",
            "board_sha256": None,
        },
    }
    if via_model is not None:
        board["via_model"] = via_model
    board["provenance"]["board_sha256"] = v5board.compute_board_sha256(board)
    return v5board.load_board(board)


def mutated(board, fn, fix_hash=True, validate=True):
    """深拷贝变异（默认重算哈希链+复校验），供 fail-closed 用例构造形态异常。"""
    b = copy.deepcopy(board)
    fn(b)
    if fix_hash:
        b["provenance"]["board_sha256"] = v5board.compute_board_sha256(b)
    if validate:
        return v5board.load_board(b)
    return b


# ------------------------------------------------------------------ 解析助手

def _pins_tokens(text):
    """network.net 的 (pins ...) 全 token（按 net 顺序）。"""
    return [tok for m in re.finditer(r"\(pins ([^)]*)\)", text)
            for tok in m.group(1).split()]


def _boundary_nums(text):
    m = re.search(r"\(path pcb 0\s+((?:[-\d.]+)(?:\s+[-\d.]+)*)\s*\)", text)
    return [float(v) for v in m.group(1).split()]


# ============================================================ fail-closed 面

def test_faithful_missing_via_model_rejected_with_stall_disclosure():
    """忠实缺省: 无 via_model=显式报错+停滞机理披露（真板双源）。"""
    for b in (badge(), pmod()):
        with pytest.raises(de.DsnExportError, match="停滞"):
            de.export_dsn(b)
    with pytest.raises(de.DsnExportError) as ei:
        de.export_dsn(synth_board())
    assert "via" in str(ei.value) and "relaxed=True" in str(ei.value)


def test_faithful_zero_drill_via_model_rejected():
    b = synth_board(via_model={"drill_mm": 0.0, "annular_mm": 0.15})
    with pytest.raises(de.DsnExportError, match="drill_mm<=0"):
        de.export_dsn(b)


def test_faithful_missing_via_explicit_escape_allows_export():
    """allow_missing_via 显式越狱: 照实无 via 导出（披露口径，冒烟专用）。"""
    text = de.export_dsn(badge(), allow_missing_via=True)
    assert "(via " not in text and "use_via" not in text
    assert "(net " in text                      # 板本体照常导出


def test_no_available_signal_layer_rejected():
    b = mutated(synth_board(), lambda bd: [l.update(available=False)
                                           for l in bd["stackup"]])
    with pytest.raises(ValueError, match="无可用 signal 层"):
        de.export_dsn(b, relaxed=True)


def test_pad_referencing_unknown_layer_rejected():
    def fn(bd):
        bd["partitions"][0]["geometry"]["pad_terminals"][0]["layers"] = "X.Cu"
    b = mutated(synth_board(), fn)
    with pytest.raises(ValueError, match="未知/不可用层"):
        de.export_dsn(b, relaxed=True)


def test_zero_size_pad_rejected():
    def fn(bd):
        bd["partitions"][0]["geometry"]["pad_terminals"][0]["size_mm"] = [0.0]
    b = mutated(synth_board(), fn)
    with pytest.raises(ValueError, match="非正值"):
        de.export_dsn(b, relaxed=True)


def test_net_id_with_quote_rejected():
    b = mutated(synth_board(), lambda bd: bd["nets"][0].update(
        net_id='bad"net'))
    with pytest.raises(ValueError, match="引号"):
        de.export_dsn(b, relaxed=True)


def test_degenerate_equal_endpoints_rejected():
    def fn(bd):
        eps = bd["partitions"][2]["geometry"]["endpoints"]
        eps[1] = list(eps[0])
    b = mutated(synth_board(), fn)
    with pytest.raises(ValueError, match="两端点同坐标"):
        de.export_dsn(b, relaxed=True)


def test_empty_partitions_rejected():
    def fn(bd):
        bd.update(partitions=[], nets=[])   # 双清空才过载入侧跨字段校验
    b = mutated(synth_board(), fn)
    with pytest.raises(ValueError, match="partitions 为空"):
        de.export_dsn(b, relaxed=True)


def test_empty_nets_rejected():
    b = mutated(synth_board(), lambda bd: bd.update(nets=[]))
    with pytest.raises(ValueError, match="nets 为空"):
        de.export_dsn(b, relaxed=True)


def test_net_referencing_missing_partition_rejected_by_loader():
    """网指向不存在分区: 载入侧跨字段校验兜住（export_dsn 先过 load_board 单源）。

    变异体不过载入（跨字段即败），export_dsn 内部的 load_board 负责拒收。"""
    b = mutated(synth_board(), lambda bd: bd["nets"][1].update(
        partitions=["P_ZZ"]), validate=False)
    with pytest.raises(v5board.BoardLoadError, match="不存在的分区"):
        de.export_dsn(b, relaxed=True)


def test_hash_chain_tamper_rejected_by_loader():
    b = mutated(synth_board(), lambda bd: None, fix_hash=False)
    b["provenance"]["board_sha256"] = "0" * 64          # 篡改链
    with pytest.raises(v5board.BoardLoadError, match="哈希链不复算"):
        de.export_dsn(b, relaxed=True)


def test_wrapped_doc_passed_undecoded_rejected():
    """wrap 件整包直喂（绕过载入口径）=schema 拒绝（ValueError 不吞）。"""
    with open(BADGE_PATH, encoding="utf-8") as f:
        wrapped = json.load(f)
    with pytest.raises(ValueError):
        de.export_dsn(wrapped, relaxed=True)


def test_malformed_endpoints_nonfinite_rejected():
    """NaN 端点: v5.canonical 序列化层即拒（CanonicalError=ValueError 族，
    哈希链容不下非 JSON 数值——fail-closed 在载入层闭合）。"""
    b = mutated(synth_board(), lambda bd: None, validate=False)
    b["partitions"][0]["geometry"]["endpoints"][1] = [3.0, float("nan")]
    with pytest.raises(ValueError):
        de.export_dsn(b, relaxed=True)


# ============================================================ 确定性面

def test_determinism_badgeleds_relaxed_double_run_byte_equal():
    t1 = de.export_dsn(badge(), relaxed=True)
    t2 = de.export_dsn(de.load_board_doc(BADGE_PATH), relaxed=True)
    assert t1 == t2


def test_determinism_pmod_faithful_allow_double_run_byte_equal():
    t1 = de.export_dsn(pmod(), allow_missing_via=True)
    t2 = de.export_dsn(de.load_board_doc(PMOD_PATH), allow_missing_via=True)
    assert t1 == t2


def test_determinism_canonical_order_invariance():
    """canonical 序: 分区/网列表序打乱（重哈希）→ 同字节输出。"""
    t_ref = de.export_dsn(badge(), relaxed=True)
    b2 = mutated(badge(), lambda bd: (bd.__setitem__(
        "partitions", list(reversed(bd["partitions"]))),
        bd.__setitem__("nets", list(reversed(bd["nets"])))))
    assert de.export_dsn(b2, relaxed=True) == t_ref


def test_no_timestamp_or_path_leakage():
    for text in (de.export_dsn(badge(), relaxed=True),
                 de.export_dsn(pmod(), allow_missing_via=True)):
        assert 'host_cad "canvas.dsn_export/1.0.0"' in text   # 固定生成器串
        for leak in ("board.json", "v5-p5", "E:", BADGE_PATH, PMOD_PATH,
                     "\\", "20:25", "2026-"):
            assert leak not in text, leak


# ============================================================ 结构面

def test_structure_layers_parser_resolution():
    text = de.export_dsn(badge(), relaxed=True)
    for i, lid in enumerate(["F.Cu", "B.Cu"]):
        assert re.search(r"\(layer %s\n\s+\(type signal\)\n\s+\(property\n"
                         r"\s+\(index %d\)" % (re.escape(lid), i), text)
    assert "(resolution um 1)" in text and "(unit um)" in text
    assert "(wiring" in text                     # 未布线板=空 wiring


def test_structure_boundary_matches_workspace():
    """boundary=workspace 矩形（y 取反）；relaxed 外扩 2mm、忠实不外扩。

    矩形五点序: (x0,y0)(x1,y0)(x1,y1)(x0,y1)(x0,y0)，y0=-y_max、y1=-y_min。"""
    for board, kw, m in ((badge(), {"relaxed": True}, 2000.0),
                         (pmod(), {"allow_missing_via": True}, 0.0)):
        ws = board["workspace"]
        nums = _boundary_nums(de.export_dsn(board, **kw))
        assert nums[0:4] == pytest.approx(
            [ws["x_min"] * 1000 - m, -ws["y_max"] * 1000 - m,
             ws["x_max"] * 1000 + m, -ws["y_max"] * 1000 - m], abs=0.05)
        assert nums[4:6] == pytest.approx(
            [nums[2], -ws["y_min"] * 1000 + m], abs=0.05)
        assert nums[6:8] == pytest.approx(
            [nums[0], -ws["y_min"] * 1000 + m], abs=0.05)
        assert nums[8:10] == [nums[0], nums[1]]      # 闭矩形回起点


def test_structure_via_padstack_presence_and_nominal_relaxed():
    """relaxed=标称 via Ø0.7（drill 0.4+2×0.15）+use_via；忠实 allow=无。"""
    text = de.export_dsn(badge(), relaxed=True)
    assert '(via "Via_v5_400_700_um")' in text
    assert '(use_via "Via_v5_400_700_um")' in text
    text_f = de.export_dsn(badge(), allow_missing_via=True)
    assert "(via " not in text_f and "use_via" not in text_f


def test_structure_via_true_model_faithful_and_dot_free_name():
    """真 via_model 忠实导出: Ø=drill+2×annular；名内无点号（tmp108 WARN 类预防）。"""
    text = de.export_dsn(
        synth_board(via_model={"drill_mm": 0.3048, "annular_mm": 0.1524}))
    assert '(via "Via_v5_304p8_609p6_um")' in text
    assert not re.search(r'\(via "[^"]*\.', text)


def test_structure_rules_width_clearance():
    text = de.export_dsn(badge(), relaxed=True)
    assert text.count("(width 300)") == 2          # structure.rule + class rule
    assert text.count("(clearance 500)") >= 2
    assert "(clearance 500 (type smd_smd))" in text


def test_structure_pads_match_partitions_and_terminals():
    """image 数=分区数、每 image 双 pin、padstack 数=板数据去重键数。"""
    for board, text in ((badge(), de.export_dsn(badge(), relaxed=True)),
                        (pmod(), de.export_dsn(pmod(), relaxed=True))):
        parts = board["partitions"]
        assert text.count("(image ") == len(parts)
        assert text.count("(attach off)") == _distinct_padstacks(board)
        for p in parts:
            img = re.search(r"\(image \"IMG_%s\"(.*?)\n    \)" % re.escape(
                _ref_of(text, p["partition_id"])), text, re.S)
            assert img and len(re.findall(r"\(pin Pad_", img.group(1))) == 2


def _distinct_padstacks(board):
    """板数据侧去重键数（含层集——all=全部可用 signal 层、单层=(层,)）。"""
    layers = tuple(l["id"] for l in board["stackup"]
                   if l.get("available") and l.get("kind") == "signal")
    keys = set()
    for p in board["partitions"]:
        for t in (p["geometry"].get("pad_terminals") or []):
            s = list(t["size_mm"]) + [t["size_mm"][0]]
            lay = t["layers"]
            ls = layers if lay == "all" else (
                (lay,) if isinstance(lay, str) else
                tuple(l for l in layers if l in set(lay)))
            keys.add((t["shape"], round(s[0], 6), round(s[1], 6), ls))
    return len(keys)


def _ref_of(text, pid):
    """partition_id → 导出 refdes（净化后；撞名时取首个未占用形态）。"""
    return de._sanitize(pid)


def test_structure_network_matches_nets_and_partitions():
    """net 数=板网数；每网 pins=2×其分区数；class 全网成员。"""
    for board, text in ((badge(), de.export_dsn(badge(), relaxed=True)),
                        (pmod(), de.export_dsn(pmod(), relaxed=True))):
        nets = board["nets"]
        assert len(re.findall(r"\(net ", text)) == len(nets)
        pin_blocks = re.findall(r"\(net \"[^\"]*\"\n\s+\(pins ([^)]*)\)", text)
        assert [len(b.split()) for b in pin_blocks] == \
            [2 * len(n["partitions"]) for n in
             sorted(nets, key=lambda n: n["net_id"])]
        cls = re.search(r'\(class "v5_default" ([^\n]*)', text).group(1)
        assert len(re.findall(r'"[^"]*"', cls)) == len(nets)


def test_structure_placement_at_endpoint0_y_negated():
    text = de.export_dsn(badge(), relaxed=True)
    by_img = {p["partition_id"]: p for p in badge()["partitions"]}
    for pid, p in sorted(by_img.items()):
        ex0, ey0 = p["geometry"]["endpoints"][0]
        pat = r"\(place %s %s %s front 0\)" % (
            re.escape(de._sanitize(pid)),
            re.escape(de._fmt(ex0 * 1000)), re.escape(de._fmt(-ey0 * 1000)))
        assert re.search(pat, text), pid


# ============================================================ 陷阱钉死面

def test_refdes_hyphen_trap_pinned():
    """原型已修陷阱: pins 引用 token=REF-N，REF 内零连字符（切分不漂移）。"""
    for text in (de.export_dsn(badge(), relaxed=True),
                 de.export_dsn(pmod(), allow_missing_via=True),
                 de.export_dsn(synth_board(), relaxed=True)):
        for tok in _pins_tokens(text):
            assert re.match(r"^[A-Za-z0-9_]+-\d+$", tok), tok
        assert "PT-Net-" not in text          # 原始含连字符分区名不渗入引用


def test_refdes_sanitize_collision_dedup_keeps_connectivity():
    """P.1 与 P-1 同净化为 P_1: 确定性后缀去重保 refdes↔分区 1:1。"""
    def fn(bd):
        bd["partitions"][1]["partition_id"] = "P.1"
        bd["partitions"][2]["partition_id"] = "P-1"
        bd["nets"][0]["partitions"] = ["P-A", "P.1"]
        bd["nets"][1]["partitions"] = ["P-1"]
    b = mutated(synth_board(), fn)
    text = de.export_dsn(b, relaxed=True)
    places = re.findall(r"\(place (\S+) ", text)
    assert len(places) == len(set(places)) == 3
    assert sorted(places) == ["P_1", "P_1_2", "P_A"]


def test_write_dsn_roundtrip(tmp_path):
    """落盘往返: 字节=export_dsn 文本、utf-8、\\n 换行。"""
    board = badge()
    path = de.write_dsn(board, str(tmp_path / "b.dsn"), relaxed=True)
    blob = open(path, "rb").read()
    assert blob == de.export_dsn(board, relaxed=True).encode("utf-8")
    assert b"\r" not in blob


def test_load_board_doc_bare_file(tmp_path):
    """裸件（无 wrap）载入口径: 原样过 v5.board.load_board。"""
    board = synth_board()
    p = tmp_path / "bare.json"
    p.write_text(json.dumps(board), encoding="utf-8")
    assert de.load_board_doc(str(p))["board_id"] == "synth-dsn"
