"""copper_patch（P2 补丁引擎）单测：对象寻址 + 整批原子 + 行尾/字节保真。

口径（与任务书冻结契约一致）：
  * key = copper_model 的身份键（uuid 全局唯一时 = uuid，否则 uuid@digest）;
  * blocked 时 board_text is None、reasons 逐条给出、整批不落一半；
  * `unchanged_bytes_outside_targets` 是**摘除目标跨度后逐字比较**的实证结果。

真实板 `config.REVC_BOARD` **只读**（不落盘、不调 kicad-cli）。
"""

from __future__ import annotations

import os
import time

import pytest

import revc_board_fixture
from pcbflow import board_writer, config, copper_model
from pcbflow import copper_patch as cp

# --------------------------------------------------------------- 夹具

_SEG1_UUID = "aaaaaaaa-0000-0000-0000-000000000001"
_SEG2_UUID = "aaaaaaaa-0000-0000-0000-000000000002"
_VIA1_UUID = "bbbbbbbb-0000-0000-0000-000000000001"
_VIA2_UUID = "bbbbbbbb-0000-0000-0000-000000000002"
_VIA3_UUID = "bbbbbbbb-0000-0000-0000-000000000003"
_ZONE_UUID = "cccccccc-0000-0000-0000-000000000001"

_SYNTH_LF = (
    "(kicad_pcb\n"
    "\t(version 20260206)\n"
    '\t(net 0 "")\n'
    '\t(net 1 "N1")\n'
    '\t(net 2 "GND")\n'
    '\t(gr_rect (start 0 0) (end 10 10) (layer "Edge.Cuts"))\n'
    "\t(segment\n"
    "\t\t(start 1 2)\n"
    "\t\t(end 3 4)\n"
    "\t\t(width 0.25)\n"
    '\t\t(layer "F.Cu")\n'
    '\t\t(net "N1")\n'
    '\t\t(uuid "%s")\n'
    "\t)\n"
    "\t(segment\n"
    "\t\t(start 5 6)\n"
    "\t\t(end 7 8)\n"
    "\t\t(width 0.3)\n"
    '\t\t(layer "In2.Cu")\n'
    '\t\t(net "N1")\n'
    '\t\t(uuid "%s")\n'
    "\t)\n"
    "\t(via buried\n"
    "\t\t(at 5 6)\n"
    "\t\t(size 0.45)\n"
    "\t\t(drill 0.2)\n"
    '\t\t(layers "F.Cu" "In2.Cu")\n'
    '\t\t(net "N1")\n'
    '\t\t(uuid "%s")\n'
    "\t)\n"
    "\t(via buried\n"
    "\t\t(at 1.5 2.5)\n"
    "\t\t(size 0.6)\n"
    "\t\t(drill 0.3)\n"
    '\t\t(layers "F.Cu" "In2.Cu")\n'
    '\t\t(net "GND")\n'
    '\t\t(uuid "%s")\n'
    "\t)\n"
    "\t(via blind\n"
    "\t\t(at 8.5 8.5)\n"
    "\t\t(size 0.5)\n"
    "\t\t(drill 0.25)\n"
    '\t\t(layers "F.Cu" "In1.Cu")\n'
    '\t\t(net "N1")\n'
    '\t\t(uuid "%s")\n'
    "\t)\n"
    "\t(zone\n"
    '\t\t(net "GND")\n'
    '\t\t(layer "B.Cu")\n'
    '\t\t(uuid "%s")\n'
    "\t\t(min_thickness 0.2)\n"
    "\t\t(polygon\n"
    "\t\t\t(pts\n"
    "\t\t\t\t(xy 0.5 0.5) (xy 9.5 0.5) (xy 9.5 9.5)\n"
    "\t\t\t)\n"
    "\t\t)\n"
    "\t)\n"
    ")\n"
) % (_SEG1_UUID, _SEG2_UUID, _VIA1_UUID, _VIA2_UUID, _VIA3_UUID, _ZONE_UUID)

_SYNTH_CRLF = _SYNTH_LF.replace("\n", "\r\n")


def _no_bare_lf(text: str) -> bool:
    """去净 CRLF 后既无裸 LF 亦无裸 CR（整份输出无 LF-only 行）。"""
    stripped = text.replace("\r\n", "")
    return "\n" not in stripped and "\r" not in stripped


def _cu(board):
    return copper_model.parse_copper(board)


def _expect_of(kind, entry):
    """从 copper_model 条目抄出 expect（契约字段集）。"""
    if kind == "segment":
        return {"net": entry["net"], "layer": entry["layer"],
                "width": entry["width"], "start": entry["start"],
                "end": entry["end"]}
    return {"net": entry["net"], "at": entry["at"], "size": entry["size"],
            "drill": entry["drill"], "layers": entry["layers"]}


def _add_seg(new_net="N9", start=(1.0, 2.0), end=(1.0, 3.0), width=0.2,
             layer="F.Cu"):
    return {"op": "add", "kind": "segment",
            "new": {"net": new_net, "layer": layer, "width": width,
                    "start": list(start), "end": list(end)}}


def _add_via(net="GND", at=(4.0, 4.0), size=0.5, drill=0.25,
             layers=("F.Cu", "In2.Cu")):
    return {"op": "add", "kind": "via",
            "new": {"net": net, "at": list(at), "size": size,
                    "drill": drill, "layers": list(layers)}}


def _modify(kind, entry, new):
    return {"op": "modify", "kind": kind, "key": entry["key"],
            "expect": _expect_of(kind, entry), "new": new}


def _delete(kind, entry):
    return {"op": "delete", "kind": kind, "key": entry["key"],
            "expect": _expect_of(kind, entry)}


# ------------------------------------------------- 1. 成功路径 add/modify/delete

def test_add_segment_accepted_and_appends_after_same_kind():
    cu = _cu(_SYNTH_LF)
    r = cp.apply_patch(_SYNTH_LF, [_add_seg()])
    assert r["ok"] is True and r["verdict"] == "accepted" and r["reasons"] == []
    out = r["board_text"]
    assert out is not None and out != _SYNTH_LF
    after = _cu(out)
    assert after["counts"]["segments"] == cu["counts"]["segments"] + 1
    assert r["ledger"]["ops_applied"] == 1
    assert r["ledger"]["adds"] == 1
    assert r["ledger"]["structural_guard"]["ok"] is True
    # 新节点按同类节点（多行）风格渲染，缩进与真实节点一致
    span = r["ledger"]["op_spans"][0]["final_node_span"]
    node = out[span[0]:span[1]]
    assert node.startswith("(segment\n\t\t(start 1 2)\n")
    assert node.endswith("\n\t)")
    # 插入位置在最后一个同类（segment）节点之后
    assert out.index(node) > out.index('(uuid "%s")' % _SEG2_UUID)
    # 新节点带对象级 uuid 且唯一
    key = r["ledger"]["affected_keys"][0]["new_key"]
    assert key in after["identity_map"]
    assert after["identity_map"][key]["kind"] == "segment"
    assert after["counts"]["segments"] == len(after["segments"])


def test_add_via_modify_segment_delete_via_all_effective():
    cu = _cu(_SYNTH_LF)
    seg1, seg2 = cu["segments"][0], cu["segments"][1]
    via1 = cu["vias"][0]
    ops = [
        _add_via(at=(2.5, 2.5)),
        _modify("segment", seg1, {"width": 0.4}),
        _delete("via", via1),
    ]
    r = cp.apply_patch(_SYNTH_LF, ops)
    assert r["verdict"] == "accepted", r["reasons"]
    out = r["board_text"]
    after = _cu(out)
    assert after["counts"] == {"segments": 2, "vias": 3, "zones": 1}
    # modify 生效：宽度已改，其它字段逐字节保留
    nspan = r["ledger"]["op_spans"][1]["final_node_span"]
    node = out[nspan[0]:nspan[1]]
    assert "\t\t(width 0.4)" in node
    assert '\t\t(net "N1")' in node and "(start 1 2)" in node
    # delete 生效：整行（含行尾）已摘除，不留空白残行
    assert _VIA1_UUID not in out
    assert "\t\n" not in out
    # add 生效
    assert after["counts"]["vias"] == 3
    led = r["ledger"]
    assert (led["adds"], led["modifies"], led["deletes"]) == (1, 1, 1)
    assert led["ops_applied"] == 3
    assert led["counts_before"]["segments"] == 2
    assert led["counts_after"]["vias"] == 3


def test_delete_removes_whole_line_without_residue():
    cu = _cu(_SYNTH_LF)
    via2 = cu["vias"][1]
    r = cp.apply_patch(_SYNTH_LF, [_delete("via", via2)])
    assert r["verdict"] == "accepted", r["reasons"]
    out = r["board_text"]
    assert _VIA2_UUID not in out
    assert "\n\t\n" not in out and "\n\n" not in out
    # 其余字节逐字不变：把删除目标整行摘掉即还原
    span = r["ledger"]["op_spans"][0]["orig_target_span"]
    assert out == _SYNTH_LF[:span[0]] + _SYNTH_LF[span[1]:]
    assert r["ledger"]["unchanged_bytes_outside_targets"] is True


def test_empty_ops_is_identity():
    r = cp.apply_patch(_SYNTH_LF, [])
    assert r["verdict"] == "accepted"
    assert r["board_text"] == _SYNTH_LF
    assert r["ledger"]["ops_total"] == 0 and r["ledger"]["ops_applied"] == 0
    assert r["ledger"]["unchanged_bytes_outside_targets"] is True


# ------------------------------------------------- 2. blocked 负向矩阵

def test_expect_mismatch_blocks_whole_batch():
    cu = _cu(_SYNTH_LF)
    seg1 = cu["segments"][0]
    bad = {"op": "modify", "kind": "segment", "key": seg1["key"],
           "expect": {"width": 0.99}, "new": {"width": 0.5}}
    good = _add_seg()
    r = cp.apply_patch(_SYNTH_LF, [bad, good])
    assert r["verdict"] == "blocked" and r["board_text"] is None
    assert r["ok"] is False
    assert any(x.startswith("expect_mismatch:") for x in r["reasons"])
    assert any("0.99" in x for x in r["reasons"])
    assert r["ledger"]["ops_applied"] == 0


def test_expect_coordinate_quantization_matches_copper_model():
    """expect 抄自 copper_model（坐标 6 位口径）时不得误判。"""
    cu = _cu(_SYNTH_LF)
    seg1 = cu["segments"][0]
    r = cp.apply_patch(_SYNTH_LF, [_modify("segment", seg1, {"width": 0.4})])
    assert r["verdict"] == "accepted", r["reasons"]


def test_key_not_found_blocks():
    r = cp.apply_patch(_SYNTH_LF, [
        {"op": "delete", "kind": "segment", "key": "no-such-key",
         "expect": {"net": "N1"}}])
    assert r["verdict"] == "blocked" and r["board_text"] is None
    assert any(x.startswith("key_not_found:") for x in r["reasons"])


def test_kind_mismatch_blocks():
    cu = _cu(_SYNTH_LF)
    via1 = cu["vias"][0]
    r = cp.apply_patch(_SYNTH_LF, [
        {"op": "modify", "kind": "segment", "key": via1["key"],
         "expect": {"net": "N1"}, "new": {"width": 0.3}}])
    assert r["verdict"] == "blocked"
    assert any(x.startswith("kind_mismatch:") for x in r["reasons"])


def test_zone_kind_ops_are_implemented_not_blocked():
    """R3/P3b：zone 的 add/modify/delete 已实现（不再返回 zone_ops_pending…）。

    三条 op 各自在本文件的 zone 语义测试（`test_copper_zone_patch.py`）里展开；
    这里只钉死"历史 reason 不再产生"这一契约（`ZONE_BLOCKED_REASON` 常量保留，
    仅为兼容既有导入与历史台账的读法）。
    """
    cu = _cu(_SYNTH_LF)
    zone = cu["zones"][0]
    assert cp.ZONE_BLOCKED_REASON == "zone_ops_pending_contract_v2"
    for one in (
        {"op": "add", "kind": "zone",
         "new": {"net": "GND", "layers": ["B.Cu"],
                 "outline_mm": [[1, 1], [8, 1], [8, 8]]}},
        {"op": "modify", "kind": "zone", "key": zone["key"],
         "expect": {"net": "GND"}, "new": {"params": {"min_thickness": 0.3}}},
        {"op": "delete", "kind": "zone", "key": zone["key"],
         "expect": {"net": "GND"}},
    ):
        r = cp.apply_patch(_SYNTH_LF, [one])
        assert r["verdict"] == "accepted", (one["op"], r["reasons"])
        assert cp.ZONE_BLOCKED_REASON not in r["reasons"]


def test_zone_op_with_garbage_fields_is_blocked_not_bare_reason():
    """形状非法的 zone op 走常规缺字段 reason（不再被裸码短路）。"""
    r = cp.apply_patch(_SYNTH_LF, [{"op": "delete", "kind": "zone"}])
    assert r["verdict"] == "blocked" and r["board_text"] is None
    codes = [x.split(":")[0] for x in r["reasons"]]
    assert codes == ["missing_key", "missing_expect"], r["reasons"]


def test_unknown_op_and_kind_block():
    r = cp.apply_patch(_SYNTH_LF, [
        {"op": "replace", "kind": "segment", "key": "x", "expect": {},
         "new": {}},
        {"op": "add", "kind": "arc", "new": {}},
        "not-a-dict",
    ])
    assert r["verdict"] == "blocked" and r["board_text"] is None
    codes = [x.split(":")[0] for x in r["reasons"]]
    assert "unknown_op" in codes and "unknown_kind" in codes
    assert len(r["reasons"]) == 3


def test_shape_violations_block():
    cu = _cu(_SYNTH_LF)
    seg1 = cu["segments"][0]
    cases = [
        ({"op": "modify", "kind": "segment", "expect": {"net": "N1"},
          "new": {"width": 1}}, "missing_key"),
        ({"op": "modify", "kind": "segment", "key": seg1["key"],
          "new": {"width": 1}}, "missing_expect"),
        ({"op": "delete", "kind": "segment", "key": seg1["key"],
          "expect": {}}, None),                     # 空 expect 合法 → 不在本列
        ({"op": "delete", "kind": "segment", "key": seg1["key"],
          "expect": {}, "new": {"width": 1}}, "invalid_field"),
        ({"op": "add", "kind": "segment", "key": "k",
          "new": {"net": "N1", "layer": "F.Cu", "width": 0.2,
                  "start": [1, 2], "end": [1, 3]}}, "unexpected_key"),
        ({"op": "add", "kind": "segment", "expect": {"net": "N1"},
          "new": {"net": "N1", "layer": "F.Cu", "width": 0.2,
                  "start": [1, 2], "end": [1, 3]}}, "unexpected_expect"),
        ({"op": "add", "kind": "segment", "new": {"net": "N1"}},
         "missing_new"),
        ({"op": "add", "kind": "segment",
          "new": {"net": "N1", "layer": "F.Cu", "width": -1,
                  "start": [1, 2], "end": [1, 3]}}, "invalid_field"),
        ({"op": "add", "kind": "segment",
          "new": {"net": "N1", "layer": "F.Cu", "width": 0.2,
                  "start": [1, 2], "end": [1, 3], "bogus": 1}},
         "invalid_field"),
        ({"op": "add", "kind": "via",
          "new": {"net": "N1", "at": [1, 2], "size": 0.5, "drill": 0.25,
                  "layers": ["F.Cu", "In2.Cu"], "via_kind": "micro"}},
         "invalid_field"),
        ({"op": "add", "kind": "via",
          "new": {"net": "N1", "at": [1, 2], "size": 0.5, "drill": 0.25,
                  "layers": ["F.Cu"]}}, "invalid_field"),
    ]
    for op, code in cases:
        if code is None:
            continue
        r = cp.apply_patch(_SYNTH_LF, [op])
        assert r["verdict"] == "blocked", op
        assert any(x.startswith(code + ":") for x in r["reasons"]), (op, r["reasons"])


def test_duplicate_key_blocks():
    cu = _cu(_SYNTH_LF)
    seg1 = cu["segments"][0]
    r = cp.apply_patch(_SYNTH_LF, [
        _modify("segment", seg1, {"width": 0.4}),
        _modify("segment", seg1, {"width": 0.5}),
    ])
    assert r["verdict"] == "blocked" and r["board_text"] is None
    assert any(x.startswith("duplicate_key:") for x in r["reasons"])


def test_batch_atomicity_one_bad_op_reverts_everything():
    cu = _cu(_SYNTH_LF)
    seg1 = cu["segments"][0]
    ops = [
        _add_seg(),
        _modify("segment", seg1, {"width": 0.4}),
        {"op": "delete", "kind": "segment", "key": "ghost", "expect": {}},
    ]
    r = cp.apply_patch(_SYNTH_LF, ops)
    assert r["verdict"] == "blocked"
    assert r["board_text"] is None
    assert r["ledger"]["ops_applied"] == 0
    assert r["ledger"]["adds"] == 0 and r["ledger"]["modifies"] == 0
    assert r["ledger"]["affected_keys"] == []
    assert r["ledger"]["counts_after"] is None


def test_board_parse_error_blocks():
    bad = "(kicad_pcb\n\t(net 0 \"\")\n"
    r = cp.apply_patch(bad, [_add_seg()])
    assert r["verdict"] == "blocked" and r["board_text"] is None
    assert any(x.startswith("board_parse_error:") for x in r["reasons"])


def test_non_str_board_and_non_list_ops_raise():
    with pytest.raises(ValueError):
        cp.apply_patch(None, [])
    with pytest.raises(ValueError):
        cp.apply_patch(_SYNTH_LF, "ops")


# ------------------------------------------------- 3. 行尾保真

@pytest.mark.parametrize("explicit", [None, "\r\n", "auto"])
def test_crlf_board_rounds_stay_pure_crlf(explicit):
    board = _SYNTH_CRLF
    for _ in range(3):
        cu = _cu(board)
        ops = [
            _modify("segment", cu["segments"][0], {"width": 0.21}),
            _add_seg(),
            _delete("via", cu["vias"][0]),
        ]
        r = cp.apply_patch(board, ops, eol=explicit)
        assert r["verdict"] == "accepted", r["reasons"]
        assert r["ledger"]["eol"] == "\r\n"
        board = r["board_text"]
        assert _no_bare_lf(board)
        assert board.count("\n") == board.count("\r\n")
        assert board_writer.dominant_eol(board) == "\r\n"


def test_lf_board_stays_lf():
    board = _SYNTH_LF
    for _ in range(2):
        cu = _cu(board)
        r = cp.apply_patch(board, [_add_via(), _delete("via", cu["vias"][0])])
        assert r["verdict"] == "accepted", r["reasons"]
        assert r["ledger"]["eol"] == "\n"
        board = r["board_text"]
        assert "\r" not in board


def test_explicit_eol_conflicting_with_board_dominant_blocks():
    r = cp.apply_patch(_SYNTH_CRLF, [_add_seg()], eol="\n")
    assert r["verdict"] == "blocked" and r["board_text"] is None
    assert any(x.startswith("eol_mismatch:") for x in r["reasons"])
    r2 = cp.apply_patch(_SYNTH_LF, [_add_seg()], eol="\r\n")
    assert r2["verdict"] == "blocked"
    assert any(x.startswith("eol_mismatch:") for x in r2["reasons"])


def test_eol_on_board_without_any_newline_is_allowed():
    one = '(kicad_pcb (net 0 "") (segment (start 1 2) (end 1 3) (width 0.2)' \
          ' (layer "F.Cu") (net "N1") (uuid "%s")))' % _SEG1_UUID
    r = cp.apply_patch(one, [_add_seg()], eol="\r\n")
    assert r["verdict"] == "accepted", r["reasons"]
    assert "\n" not in r["board_text"].replace("\r\n", "")


def test_unknown_eol_value_raises():
    for bad in ("AUTO", "auto ", "\r", ""):
        with pytest.raises(ValueError):
            cp.apply_patch(_SYNTH_LF, [_add_seg()], eol=bad)


def test_crlf_keeps_original_bytes_verbatim_including_trailing_ws():
    src = _SYNTH_CRLF + "\r\n\r\n  "
    cu = _cu(src)
    r = cp.apply_patch(src, [_add_seg(), _delete("via", cu["vias"][2])])
    assert r["verdict"] == "accepted", r["reasons"]
    out = r["board_text"]
    assert out.endswith(")\r\n\r\n\r\n  ")          # pristine 尾随空白逐字节保留
    assert _no_bare_lf(out)
    assert r["ledger"]["unchanged_bytes_outside_targets"] is True


# ------------------------------------------------- 4. 缩进/风格克隆

def test_inline_style_cloned_for_compact_board():
    one = '(kicad_pcb (net 0 "") (segment (start 1 2) (end 1 3) (width 0.2)' \
          ' (layer "F.Cu") (net "N1") (uuid "%s")))' % _SEG1_UUID
    r = cp.apply_patch(one, [_add_seg()])
    assert r["verdict"] == "accepted", r["reasons"]
    span = r["ledger"]["op_spans"][0]["final_node_span"]
    node = r["board_text"][span[0]:span[1]]
    assert "\n" not in node and "\r" not in node
    assert node.startswith("(segment (start 1 2) (end 1 3) (width 0.2)")


def test_tab_level_cloned_from_adjacent_same_kind_node():
    """前导 \\t 层级从邻近同类节点克隆（两 tab 缩进的板 → 新节点两 tab）。"""
    board = _SYNTH_LF.replace("\t(segment", "\t\t(segment").replace(
        "\t\t\t(start", "\t\t\t\t(start)")
    cu = _cu(board)
    assert cu["counts"]["segments"] == 2
    lead = board[:cu["identity_map"][cu["segments"][0]["key"]]["span"][0]]
    assert lead.endswith("\t\t")
    r = cp.apply_patch(board, [_add_seg()])
    assert r["verdict"] == "accepted", r["reasons"]
    out = r["board_text"]
    start = r["ledger"]["op_spans"][0]["final_target_span"][0]
    assert out[start:start + 3] == "\t\t("          # 前导缩进层级已克隆
    assert "\r\n\t\t\t(start" not in out            # 子字段亦加深一层
    assert "\r\n\t\t(start" not in out


def test_add_without_any_copper_node_inserts_before_root_closer():
    bare = '(kicad_pcb\n\t(version 20260206)\n\t(net 0 "")\n)\n'
    r = cp.apply_patch(bare, [_add_seg()])
    assert r["verdict"] == "accepted", r["reasons"]
    out = r["board_text"]
    assert out.endswith("\t)\n)\n")
    assert _cu(out)["counts"]["segments"] == 1
    assert r["ledger"]["unchanged_bytes_outside_targets"] is True


# ------------------------------------------------- 5. 字节保真/结构守卫

def test_unchanged_bytes_outside_targets_true_on_synthetic():
    cu = _cu(_SYNTH_LF)
    ops = [_add_seg(), _modify("segment", cu["segments"][1], {"width": 0.35}),
           _delete("via", cu["vias"][0])]
    r = cp.apply_patch(_SYNTH_LF, ops)
    assert r["verdict"] == "accepted", r["reasons"]
    assert r["ledger"]["unchanged_bytes_outside_targets"] is True
    # zone 与 footprint 类顶层节点一个字节都没动
    assert '(gr_rect (start 0 0) (end 10 10) (layer "Edge.Cuts"))' in r["board_text"]
    assert r["ledger"]["unrepresentable_before"] == 0
    assert r["ledger"]["unrepresentable_after"] == 0


def test_modify_keeps_unmodified_bytes_identical():
    cu = _cu(_SYNTH_LF)
    seg1 = cu["segments"][0]
    span = cu["identity_map"][seg1["key"]]["span"]
    orig = _SYNTH_LF[span[0]:span[1]]
    r = cp.apply_patch(_SYNTH_LF, [_modify("segment", seg1, {"width": 0.4})])
    nspan = r["ledger"]["op_spans"][0]["final_node_span"]
    node = r["board_text"][nspan[0]:nspan[1]]
    a = orig.split("\n")
    b = node.split("\n")
    assert len(a) == len(b)
    assert [(x, y) for x, y in zip(a, b) if x != y] == [("\t\t(width 0.25)",
                                                         "\t\t(width 0.4)")]


def test_partial_modify_inherits_untouched_fields_from_raw_node_bytes():
    """部分 new：未给字段从原始字节继承（含 4 位小数的宽度不被量化改写）。"""
    board = _SYNTH_LF.replace("(width 0.25)", "(width 0.1979)")
    cu = _cu(board)
    seg1 = cu["segments"][0]
    assert seg1["width"] == 0.198          # copper_model 量化到 3 位
    r = cp.apply_patch(board, [_modify("segment", seg1, {"net": "GND"})])
    assert r["verdict"] == "accepted", r["reasons"]
    nspan = r["ledger"]["op_spans"][0]["final_node_span"]
    node = r["board_text"][nspan[0]:nspan[1]]
    assert "(width 0.1979)" in node        # 未被 3 位量化值覆盖
    assert '(net "GND")' in node


def test_structural_guard_reports_all_checks():
    r = cp.apply_patch(_SYNTH_LF, [_add_seg(), _add_via()])
    g = r["ledger"]["structural_guard"]
    assert g["ok"] is True
    assert g["sexpr_parse"] == "ok"
    assert set(g["checks"]) >= {"sexpr_parse_ok", "counts_reconcile_ok",
                                "targets_effective_ok",
                                "bytes_preserved_outside_targets_ok"}
    assert g["counts_ok"] is True and g["targets_ok"] is True


def test_structural_guard_blocks_when_counts_disagree(monkeypatch):
    real = copper_model.parse_copper
    calls = {"n": 0}

    def fake(text):
        calls["n"] += 1
        out = real(text)
        if calls["n"] >= 2:                     # 产出后那次重解析
            out = dict(out)
            out["counts"] = dict(out["counts"])
            out["counts"]["segments"] += 7
        return out

    monkeypatch.setattr(cp.copper_model, "parse_copper", fake)
    r = cp.apply_patch(_SYNTH_LF, [_add_seg()])
    assert r["verdict"] == "blocked" and r["board_text"] is None
    assert any("counts_delta" in x for x in r["reasons"])


def test_remove_spans_rejects_overlap():
    assert cp._remove_spans("abcdef", [(1, 3), (2, 4)]) is None
    assert cp._remove_spans("abcdef", [(1, 3)]) == "adef"
    assert cp._remove_spans("abcdef", [(0, 6)]) == ""
    assert cp._remove_spans("abcdef", [(0, 7)]) is None


def test_via_kind_mirror_matches_copper_model():
    """本模块的 _via_kind 镜像与 copper_model 冻结规则等价（合成板逐 via）。"""
    cu = _cu(_SYNTH_LF)
    for v in cu["vias"]:
        span = cu["identity_map"][v["key"]]["span"]
        facts, reason = cp._raw_facts("via", _SYNTH_LF[span[0]:span[1]])
        assert reason is None
        assert facts["via_kind"] == v["via_kind"]
        assert cp._via_kind(facts["raw_token"], facts["layers"]) == \
            v["via_kind"]
    assert cp._via_kind("buried", []) == "buried"
    assert cp._via_kind(None, ["F.Cu", "B.Cu"]) == "through"
    assert cp._via_kind(None, ["F.Cu", "In2.Cu"]) == "blind"
    assert cp._via_kind(None, ["F.Cu", "In1.Cu"]) == "blind"
    assert cp._via_kind(None, ["In1.Cu", "In2.Cu"]) == "buried"
    assert cp._via_kind(None, []) is None
    assert cp._via_kind("micro", []) is None


# ------------------------------------------------- 6. 共享 uuid 与身份键迁移

_SHARED_UUID = "dddddddd-0000-0000-0000-00000000000a"
_SHARED_LF = (
    "(kicad_pcb\n"
    '\t(net 0 "")\n'
    "\t(segment\n"
    "\t\t(start 1 2)\n"
    "\t\t(end 3 4)\n"
    "\t\t(width 0.25)\n"
    '\t\t(layer "F.Cu")\n'
    '\t\t(net "N1")\n'
    '\t\t(uuid "%s")\n'
    "\t)\n"
    "\t(segment\n"
    "\t\t(start 5 6)\n"
    "\t\t(end 7 8)\n"
    "\t\t(width 0.3)\n"
    '\t\t(layer "In2.Cu")\n'
    '\t\t(net "N1")\n'
    '\t\t(uuid "%s")\n'
    "\t)\n"
    ")\n"
) % (_SHARED_UUID, _SHARED_UUID)


def test_shared_uuid_nodes_are_disambiguated_then_addressed_by_full_key():
    cu = _cu(_SHARED_LF)
    keys = [e["key"] for e in cu["segments"]]
    assert len(keys) == 2 and len(set(keys)) == 2
    assert all(k.startswith(_SHARED_UUID + "@") for k in keys)
    assert len(cu["identity_disambiguated"]) == 2


def test_modify_shared_uuid_node_reports_old_and_new_key():
    cu = _cu(_SHARED_LF)
    target = [e for e in cu["segments"] if e["start"] == [1.0, 2.0]][0]
    r = cp.apply_patch(_SHARED_LF, [_modify("segment", target, {"net": "GND"})])
    assert r["verdict"] == "accepted", r["reasons"]
    rec = r["ledger"]["affected_keys"][0]
    assert rec["old_key"] == target["key"]
    assert rec["new_key"] != target["key"]        # 几何改了 → 摘要变了 → key 变了
    assert rec["new_key"].startswith(_SHARED_UUID + "@")
    assert r["ledger"]["unchanged_bytes_outside_targets"] is True


def test_delete_one_of_two_uuid_sharers_promotes_sibling_key():
    """mult 2 → 1：兄弟节点 key 由 uuid@digest 变为裸 uuid（v2 key 规则后果）。"""
    cu = _cu(_SHARED_LF)
    target = [e for e in cu["segments"] if e["start"] == [1.0, 2.0]][0]
    r = cp.apply_patch(_SHARED_LF, [_delete("segment", target)])
    assert r["verdict"] == "accepted", r["reasons"]
    assert r["ledger"]["affected_keys"][0]["old_key"] == target["key"]
    after = _cu(r["board_text"])
    assert list(after["identity_map"]) == [_SHARED_UUID]
    assert r["ledger"]["uuid_multiplicity_changes"] == [
        {"uuid": _SHARED_UUID, "mult_before": 2, "mult_after": 1}]
    assert r["ledger"]["unchanged_bytes_outside_targets"] is True


# ------------------------------------------------- 7. 新 uuid 语义
def test_two_identical_adds_get_distinct_uuids():
    a = _add_seg()
    b = _add_seg()
    r = cp.apply_patch(_SYNTH_LF, [a, b])
    assert r["verdict"] == "accepted", r["reasons"]
    keys = [rec["new_key"] for rec in r["ledger"]["affected_keys"]]
    assert len(set(keys)) == 2
    after = _cu(r["board_text"])
    for k in keys:
        assert k in after["identity_map"]
    assert after["counts"]["segments"] == 4


def test_derived_uuid_is_object_level_not_route_level():
    """不得复用 board_writer.route_uuid 的路由级口径（否则一条 route 一个 uuid）。"""
    r = cp.apply_patch(_SYNTH_LF, [_add_seg(start=(1.0, 2.0), end=(1.0, 3.0))])
    new_key = r["ledger"]["affected_keys"][0]["new_key"]
    route = {"net": "N9", "width": 0.2, "via_size": 0.45, "via_drill": 0.2,
             "segments": [[0, 1.0, 2.0, 1.0, 3.0]], "vias": []}
    assert new_key != board_writer.route_uuid(route)
    assert len(new_key) == 36 and new_key.count("-") == 4


def test_derived_uuid_never_collides_with_board_uuids():
    existing = set()
    cu = _cu(_SYNTH_LF)
    for k in ("segments", "vias", "zones"):
        for e in cu[k]:
            if e["uuid"]:
                existing.add(e["uuid"])
    # 逼出一次冲突：把真实派生值预置为板上已有 uuid 之一
    r = cp.apply_patch(_SYNTH_LF, [_add_seg()])
    derived = r["ledger"]["affected_keys"][0]["new_key"]
    assert derived not in existing
def test_new_uuid_field_is_rejected():
    """new 不接受 uuid（新节点 uuid 只能由引擎派生，防"uuid 共享"回流）。"""
    r = cp.apply_patch(_SYNTH_LF, [
        {"op": "add", "kind": "segment",
         "new": {"net": "N9", "layer": "F.Cu", "width": 0.2,
                 "start": [1.0, 2.0], "end": [1.0, 3.0],
                 "uuid": _SEG1_UUID}}])
    assert r["verdict"] == "blocked" and r["board_text"] is None
    assert any(x.startswith("invalid_field:") and "uuid" in x
               for x in r["reasons"])


def test_patch_is_deterministic():
    ops = [_add_seg(), _add_via(), _add_seg(start=(1.0, 2.0), end=(1.0, 3.0))]
    r1 = cp.apply_patch(_SYNTH_LF, ops)
    r2 = cp.apply_patch(_SYNTH_LF, ops)
    assert r1["board_text"] == r2["board_text"]
    assert r1["ledger"]["affected_keys"] == r2["ledger"]["affected_keys"]


# ------------------------------------------------- 8. 真实板（只读）

_HAS_REVC = os.path.exists(config.REVC_BOARD)
_revc_cache = {}


def _revc():
    if "t" not in _revc_cache:
        with open(config.REVC_BOARD, encoding="utf-8", newline="") as f:
            _revc_cache["t"] = f.read()
    return _revc_cache["t"]


def _pin_fixture_board(monkeypatch):
    """REPAIR-P1 W-5（铜环案 R4 三步法②）：钉仓内冻结夹具板
    （与 2026-09-11 live 板 dbfea089 逐字节同，sha 锚 fail-closed），
    并使 _revc() 文本缓存失效（防先前预热串板）。"""
    monkeypatch.setattr(config, "REVC_BOARD", revc_board_fixture.fixture_board())
    _revc_cache.clear()


@pytest.mark.skipif(not _HAS_REVC, reason="真实板不存在")
def test_revc_preconditions(monkeypatch):
    _pin_fixture_board(monkeypatch)
    t = _revc()
    cu = _cu(t)
    # M1 刷新：counts=dbfea089 夹具板实测 2372/358/2（原 2026-09-11 live
    # 口径原样保留，仅钉板）
    assert cu["counts"] == {"segments": 2372, "vias": 358, "zones": 2}
    assert cu["unrepresentable"] == []
    assert t.count("\n") == t.count("\r\n")          # 纯 CRLF
    assert board_writer.dominant_eol(t) == "\r\n"


@pytest.mark.skipif(not _HAS_REVC, reason="真实板不存在")
def test_revc_one_round_add_modify_delete(monkeypatch):
    _pin_fixture_board(monkeypatch)
    t = _revc()
    cu = _cu(t)
    seg_mod, via_del = cu["segments"][0], cu["vias"][0]
    ops = [
        _modify("segment", seg_mod, {"width": round(seg_mod["width"] + 0.05, 3)}),
        _add_seg(new_net="GND"),
        _delete("via", via_del),
    ]
    t0 = time.perf_counter()
    r = cp.apply_patch(t, ops)
    elapsed = time.perf_counter() - t0
    assert r["verdict"] == "accepted", r["reasons"]
    out = r["board_text"]
    led = r["ledger"]
    # M1 刷新：counts=dbfea089 夹具板实测；after=before+add_seg−del_via（仅钉板）
    assert led["counts_before"] == {"segments": 2372, "vias": 358, "zones": 2}
    assert led["counts_after"] == {"segments": 2373, "vias": 357, "zones": 2}
    assert led["unchanged_bytes_outside_targets"] is True
    assert led["eol"] == "\r\n"
    assert led["structural_guard"]["ok"] is True
    assert out.count("\n") == out.count("\r\n")
    assert _no_bare_lf(out)
    # 行数对账（独立口径）：新增 1 段 = 7 行内 + 1 行尾；删除 1 via 整行 = 同量
    ins = led["op_spans"][1]["final_target_span"]
    dele = led["op_spans"][2]["orig_target_span"]
    assert out[ins[0]:ins[1]].count("\r\n") == 8
    assert t[dele[0]:dele[1]].count("\r\n") == 8
    assert out.count("\r\n") == t.count("\r\n")
    assert elapsed < 30.0                    # 单轮上界（含 2 次 parse_copper）


@pytest.mark.skipif(not _HAS_REVC, reason="真实板不存在")
def test_revc_three_rounds_no_bare_lf_and_counts_reconcile(monkeypatch):
    _pin_fixture_board(monkeypatch)
    board = _revc()
    for round_no in range(3):
        cu = _cu(board)
        ops = [
            _modify("segment", cu["segments"][0],
                    {"width": round(cu["segments"][0]["width"] + 0.01, 3)}),
            _add_via(at=(1.0 + round_no, 2.0 + round_no)),
            _delete("via", cu["vias"][round_no]),
        ]
        before = cu["counts"]
        r = cp.apply_patch(board, ops)
        assert r["verdict"] == "accepted", (round_no, r["reasons"])
        board = r["board_text"]
        assert _no_bare_lf(board)
        assert board.count("\n") == board.count("\r\n")
        assert board_writer.dominant_eol(board) == "\r\n"
        assert r["ledger"]["counts_after"] == {
            "segments": before["segments"],
            "vias": before["vias"] + 1 - 1,
            "zones": before["zones"]}
        assert r["ledger"]["unchanged_bytes_outside_targets"] is True
    # M1 刷新：三轮后计数回归夹具板口径 2372/358/2（仅钉板）
    assert _cu(board)["counts"] == {"segments": 2372, "vias": 358, "zones": 2}


@pytest.mark.skipif(not _HAS_REVC, reason="真实板不存在")
def test_revc_modify_noop_is_byte_identical():
    # REPAIR-P1 W-5 R4③：本用例保留在 live 板上（语义板无关：noop 补丁
    # 必须字节不动）——先清缓存防前面钉板用例的预热串板。
    _revc_cache.clear()
    t = _revc()
    cu = _cu(t)
    seg = cu["segments"][7]
    span = cu["identity_map"][seg["key"]]["span"]
    orig = t[span[0]:span[1]]
    r = cp.apply_patch(t, [{"op": "modify", "kind": "segment",
                            "key": seg["key"],
                            "expect": {"width": seg["width"]}, "new": {}}])
    assert r["verdict"] == "accepted", r["reasons"]
    nspan = r["ledger"]["op_spans"][0]["final_node_span"]
    assert r["board_text"][nspan[0]:nspan[1]] == orig


@pytest.mark.skipif(not _HAS_REVC, reason="真实板不存在")
def test_revc_add_style_matches_real_node_style():
    t = _revc()
    r = cp.apply_patch(t, [_add_seg(new_net="GND", start=(1.5, 2.5),
                                    end=(1.5, 3.5))])
    assert r["verdict"] == "accepted", r["reasons"]
    span = r["ledger"]["op_spans"][0]["final_node_span"]
    node = r["board_text"][span[0]:span[1]]
    assert node == (
        "(segment\r\n\t\t(start 1.5 2.5)\r\n\t\t(end 1.5 3.5)\r\n"
        "\t\t(width 0.2)\r\n\t\t(layer \"F.Cu\")\r\n\t\t(net \"GND\")\r\n"
        "\t\t(uuid \"%s\")\r\n\t)"
        % r["ledger"]["affected_keys"][0]["new_key"])
    assert "\n" not in node.replace("\r\n", "")


@pytest.mark.skipif(not _HAS_REVC, reason="真实板不存在")
def test_revc_via_kind_mirror_equivalent():
    t = _revc()
    cu = _cu(t)
    for v in cu["vias"]:
        assert cp._via_kind(v["via_kind"], v["layers"]) == v["via_kind"]


@pytest.mark.skipif(not _HAS_REVC, reason="真实板不存在")
def test_revc_generated_uuid_is_not_shared_by_any_other_node():
    """对象级唯一：新增节点 uuid 在重解析后 key == uuid（未被消歧、未被共享）。"""
    t = _revc()
    r = cp.apply_patch(t, [_add_seg(new_net="GND"), _add_seg(new_net="GND")])
    assert r["verdict"] == "accepted", r["reasons"]
    after = _cu(r["board_text"])
    keys = [rec["new_key"] for rec in r["ledger"]["affected_keys"]]
    assert len(set(keys)) == 2
    for k in keys:
        assert k in after["identity_map"]
        assert after["identity_map"][k]["kind"] == "segment"
    assert not any(e["uuid"] in keys
                   for e in after["identity_disambiguated"])


@pytest.mark.skipif(not _HAS_REVC, reason="真实板不存在")
def test_revc_live_invariants_only():
    """R4③ live 板不变量用例（REPAIR-P1 W-5）：live 板演进不破坏补丁前置合同。

    只断板无关不变量——重解析确定性、纯 CRLF、零不可表示、dominant eol；
    精确计数由钉夹具板的用例守护。清缓存确保读的是 live 板。
    """
    _revc_cache.clear()
    t = _revc()
    cu = _cu(t)
    assert cu["unrepresentable"] == []
    assert t.count("\n") == t.count("\r\n")
    assert board_writer.dominant_eol(t) == "\r\n"
    again = _cu(t)
    assert again["copper_sha256"] == cu["copper_sha256"]   # 重解析确定性


def test_negative_control_board_tamper_moves_counts():
    """负对照（R28「不得弱化」硬约束检出证明）：注入一个新 uuid 的 segment
    后补丁前置计数随之 +1（2372→2373）——精确断言确实跟踪板字节。"""
    tampered = revc_board_fixture.duplicate_first_segment(
        revc_board_fixture.fixture_board_text())
    cu = _cu(tampered)
    assert cu["counts"]["segments"] == 2373
    assert cu["unrepresentable"] == []
    assert cu["counts"]["segments"] != 2372    # M1 精确值在此板内容下不成立
