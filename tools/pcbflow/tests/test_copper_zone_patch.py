"""copper_patch P3b：zone 写操作 + 填充过期语义 + 采纳门（fill_gate）单测。

口径（与任务书 R3 冻结契约一致，见 `pcbflow/copper_patch.py` 模块 docstring）：
  * `modify` 允许 net / layers / outline_mm / params（可编辑参数子集）；
  * `add` 必须给全 net/layers/outline_mm，**不得自造 filled_polygon**，
    ledger 显式记 `fill_state="unknown"` + `refill_required=True`；
  * `delete` 摘整行（前导缩进 + 节点字节 + 行尾）；
  * 轮廓/layers/net/影响填充几何的 params 改动 ⇒ 既有填充 `stale`
    （**保留填充字节不动**，**从不谎称 fresh**）；
  * 采纳门：被触及 zone 的填充非 fresh 而轮次无 `refill_evidence` ⇒ 拦。

真实板 `config.REVC_BOARD` **只读**（不落盘到 design/、不调 kicad-cli）。
运行时产物落在系统临时目录（`tempfile.mkdtemp`），不写仓库 out/ 历史产物。
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import time

import pytest

import revc_board_fixture
from pcbflow import config, copper_loop, copper_model, hashing
from pcbflow import copper_patch as cp

PCBFLOW_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# REPAIR-P1 W-5（铜环案 R4 三步法②）：真实板基准钉仓内冻结夹具板（与
# 2026-09-11 live 板 dbfea089 逐字节同，sha 锚 fail-closed）。zone 身份
# uuid/fill_points 等 M1 精确口径原样保留，仅与 live 板演进解耦；live
# 板不变量另见 test_revc_zone_live_invariants_only。
REVC = revc_board_fixture.fixture_board()

# --------------------------------------------------------------- 合成板

_S1 = "aaaa1111-0000-0000-0000-000000000001"
_S2 = "aaaa1111-0000-0000-0000-000000000002"
_V1 = "bbbb1111-0000-0000-0000-000000000001"
_Z1 = "cccc1111-0000-0000-0000-000000000001"

#: 刻意做成"既有 zone 带填充 + 完整参数块 + 多行 pts"的形状（Rev-C 同构）
_SYNTH_LF = (
    "(kicad_pcb\n"
    "\t(version 20260206)\n"
    '\t(net 0 "")\n'
    '\t(net 1 "N1")\n'
    '\t(net 2 "GND")\n'
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
    "\t(zone\n"
    '\t\t(net "GND")\n'
    '\t\t(layer "B.Cu")\n'
    '\t\t(uuid "%s")\n'
    "\t\t(hatch edge 0.5)\n"
    "\t\t(connect_pads\n"
    "\t\t\t(clearance 0.2)\n"
    "\t\t)\n"
    "\t\t(min_thickness 0.2)\n"
    "\t\t(fill yes\n"
    "\t\t\t(thermal_gap 0.5)\n"
    "\t\t\t(thermal_bridge_width 0.5)\n"
    "\t\t\t(island_removal_mode 0)\n"
    "\t\t)\n"
    "\t\t(polygon\n"
    "\t\t\t(pts\n"
    "\t\t\t\t(xy 0.5 0.5) (xy 9.5 0.5) (xy 9.5 9.5) (xy 0.5 9.5)\n"
    "\t\t\t)\n"
    "\t\t)\n"
    "\t\t(filled_polygon\n"
    '\t\t\t(layer "B.Cu")\n'
    "\t\t\t(pts\n"
    "\t\t\t\t(xy 0.6 0.6) (xy 9.4 0.6) (xy 9.4 9.4) (xy 0.6 9.4)\n"
    "\t\t\t)\n"
    "\t\t)\n"
    "\t)\n"
    ")\n"
) % (_S1, _S2, _V1, _Z1)

_SYNTH_CRLF = _SYNTH_LF.replace("\n", "\r\n")

_SCRATCH = []


@pytest.fixture(scope="module", autouse=True)
def _scratch_lifecycle():
    yield
    for d in _SCRATCH:
        shutil.rmtree(d, ignore_errors=True)


def _scratch(prefix: str) -> str:
    d = tempfile.mkdtemp(prefix="copper-zone-%s-" % prefix)
    _SCRATCH.append(d)
    return d


def _cu(board):
    return copper_model.parse_copper(board)


def _bare_lf(text: str) -> int:
    """裸 LF 计数（去净 CRLF 后剩下的 '\\n'）。"""
    return text.replace("\r\n", "").count("\n")


def _zone_of(board, uuid):
    for z in _cu(board)["zones"]:
        if z["uuid"] == uuid:
            return z
    return None


def _zone_key(cu, uuid):
    for z in cu["zones"]:
        if z["uuid"] == uuid:
            return z["key"]
    raise AssertionError("zone %s 不存在" % uuid)


def _expect_zone(entry, with_params=False):
    """从 copper_model 条目抄出 zone expect（契约字段集）。"""
    exp = {"net": entry["net"], "layers": entry["layers"],
           "outline_mm": [list(p) for p in entry["outline_mm"]]}
    if with_params:
        exp["params"] = dict(entry["params"])
    return exp


def _fill_text(board, entry):
    """zone 的 filled_polygon 字节（按 copper_model 给出的跨度切）。"""
    span = _cu(board)["identity_map"][entry["key"]]["span"]
    node = board[span[0]:span[1]]
    i = node.index("(filled_polygon")
    j = node.rindex(")")
    # filled_polygon 的闭括号：从 i 起括号配平
    depth, k = 0, i
    while k < len(node):
        if node[k] == "(":
            depth += 1
        elif node[k] == ")":
            depth -= 1
            if depth == 0:
                break
        k += 1
    return node[i:k + 1], j


def _zone_node(board, key):
    span = _cu(board)["identity_map"][key]["span"]
    return board[span[0]:span[1]]


def _mod(entry, new, with_params=False):
    return {"op": "modify", "kind": "zone", "key": entry["key"],
            "expect": _expect_zone(entry, with_params), "new": new}


# =========================================== 1) zone modify 成功路径

def test_zone_modify_outline_success_bytes_and_fill_preserved():
    cu = _cu(_SYNTH_LF)
    z = cu["zones"][0]
    old_fill, _ = _fill_text(_SYNTH_LF, z)
    new_outline = [[1.5, 1.5], [8.5, 1.5], [8.5, 8.5], [1.5, 8.5]]
    r = cp.apply_patch(_SYNTH_LF, [_mod(z, {"outline_mm": new_outline})])
    assert r["verdict"] == "accepted", r["reasons"]
    out = r["board_text"]
    led = r["ledger"]
    # 契约字段生效
    z2 = _zone_of(out, _Z1)
    assert z2["outline_mm"] == new_outline
    # 填充字节**逐字节不动**（实证：切片相等 + ledger 指纹相等）
    new_fill, _ = _fill_text(out, z2)
    assert new_fill == old_fill
    rec = led["zone_fill"][0]
    assert rec["op"] == "modify" and rec["fill_state"] == "stale"
    assert rec["fill_present"] is True and rec["fill_invalidated"] is True
    assert rec["refill_required"] is True
    assert rec["fill_bytes_preserved"] is True
    assert rec["fill_sha256_before"] == rec["fill_sha256_after"]
    assert rec["fill_points_before"] == rec["fill_points_after"] == 4
    assert rec["copper_model_fill_identical"] is True
    assert led["zone_fill_summary"]["refill_required"] is True
    assert led["zone_fill_summary"]["stale_zone_ids"] == [_Z1]
    assert led["zone_fill_summary"]["not_fresh_zone_ids"] == [_Z1]
    # 编辑跨度（旧节点坐标）与填充跨度（旧节点坐标）不相交
    for (s, e) in [tuple(x) for x in rec["edited_spans"]]:
        for (fs, fe) in [tuple(x) for x in rec["fill_spans_before"]]:
            assert not (s < fe and fs < e), (s, e, fs, fe)
    # 且改后新节点里对应子串逐字节等于改前（两套坐标各自自洽）
    node_old = _zone_node(_SYNTH_LF, z["key"])
    node_new = _zone_node(out, z2["key"])
    for (bs, be), (as_, ae) in zip(rec["fill_spans_before"],
                                   rec["fill_spans_after"]):
        assert node_old[bs:be] == node_new[as_:ae]
    # 既有强度
    assert led["unchanged_bytes_outside_targets"] is True
    assert led["structural_guard"]["ok"] is True
    assert led["counts_before"] == led["counts_after"]
    assert len(out) == len(_SYNTH_LF)      # 点数不变 ⇒ 长度不变
    # 除 pts 那一段外逐字节相同
    node_old = _zone_node(_SYNTH_LF, z["key"])
    node_new = _zone_node(out, z2["key"])
    i, j = node_old.index("(pts"), node_old.index("\n\t\t\t)") + len("\n\t\t\t)")
    k, m = node_new.index("(pts"), node_new.index("\n\t\t\t)") + len("\n\t\t\t)")
    assert node_old[:i] == node_new[:k] and node_old[j:] == node_new[m:]


def test_zone_modify_params_all_editable_kinds():
    cu = _cu(_SYNTH_LF)
    z = cu["zones"][0]
    r = cp.apply_patch(_SYNTH_LF, [_mod(z, {"params": {
        "clearance": 0.3, "min_thickness": 0.15,
        "fill_thermal_gap": 0.6, "fill_thermal_bridge_width": 0.4,
        "fill_island_removal_mode": 2, "fill": "no",
        "hatch": "none"}}, with_params=True)])
    assert r["verdict"] == "accepted", r["reasons"]
    p = _zone_of(r["board_text"], _Z1)["params"]
    assert p["clearance"] == 0.3 and p["min_thickness"] == 0.15
    assert p["fill_thermal_gap"] == 0.6
    assert p["fill_thermal_bridge_width"] == 0.4
    assert p["fill_island_removal_mode"] == 2
    assert p["fill"] == "no" and p["hatch"] == "none"
    rec = r["ledger"]["zone_fill"][0]
    assert rec["fill_state"] == "stale"
    assert sorted(rec["stale_params"]) == [
        "clearance", "fill", "fill_island_removal_mode",
        "fill_thermal_bridge_width", "fill_thermal_gap", "min_thickness"]
    assert rec["stale_fields"] == []
    # 填充字节仍未动
    assert rec["fill_sha256_before"] == rec["fill_sha256_after"]


def test_zone_modify_hatch_only_is_not_stale_but_never_fresh():
    cu = _cu(_SYNTH_LF)
    z = cu["zones"][0]
    r = cp.apply_patch(_SYNTH_LF, [_mod(z, {"params": {"hatch": "hatch 1"}},
                                        with_params=True)])
    assert r["verdict"] == "accepted", r["reasons"]
    assert _zone_of(r["board_text"], _Z1)["params"]["hatch"] == "hatch 1"
    rec = r["ledger"]["zone_fill"][0]
    assert rec["fill_invalidated"] is False
    assert rec["refill_required"] is False
    assert rec["fill_state"] == "unknown"        # **不谎称 fresh**
    assert rec["fill_bytes_preserved"] is True
    assert r["ledger"]["zone_fill_summary"]["refill_required"] is False
    # 全模块从不产出 fill_state="fresh"
    assert all(x.get("fill_state") != "fresh"
               for x in r["ledger"]["zone_fill"])
    assert set(cp.ZONE_FILL_STATES_PATCH) == {"stale", "unknown"}


def test_zone_modify_layers_one_and_many():
    cu = _cu(_SYNTH_LF)
    z = cu["zones"][0]
    r = cp.apply_patch(_SYNTH_LF, [_mod(z, {"layers": ["In1.Cu"]})])
    assert r["verdict"] == "accepted", r["reasons"]
    assert _zone_of(r["board_text"], _Z1)["layers"] == ["In1.Cu"]
    cu2 = _cu(r["board_text"])
    z2 = [x for x in cu2["zones"] if x["uuid"] == _Z1][0]
    r2 = cp.apply_patch(r["board_text"],
                        [_mod(z2, {"layers": ["In1.Cu", "In2.Cu"]})])
    assert r2["verdict"] == "accepted", r2["reasons"]
    assert _zone_of(r2["board_text"], _Z1)["layers"] == ["In1.Cu", "In2.Cu"]
    assert r2["ledger"]["zone_fill"][0]["fill_state"] == "stale"
    # 层声明被重写，但 filled_polygon 的 (layer ...) 字节不动（交回 KiCad 重填）
    old_fill = _fill_text(r["board_text"], z2)[0]
    new_fill = _fill_text(r2["board_text"],
                          _zone_of(r2["board_text"], _Z1))[0]
    assert new_fill == old_fill


def test_zone_modify_net():
    cu = _cu(_SYNTH_LF)
    z = cu["zones"][0]
    r = cp.apply_patch(_SYNTH_LF, [_mod(z, {"net": "N1"})])
    assert r["verdict"] == "accepted", r["reasons"]
    assert _zone_of(r["board_text"], _Z1)["net"] == "N1"
    assert r["ledger"]["zone_fill"][0]["stale_fields"] == ["net"]


def test_zone_modify_noop_is_byte_identical():
    cu = _cu(_SYNTH_LF)
    z = cu["zones"][0]
    r = cp.apply_patch(_SYNTH_LF, [_mod(z, {"net": "GND",
                                        "layers": ["B.Cu"],
                                        "outline_mm": z["outline_mm"]})])
    assert r["verdict"] == "accepted", r["reasons"]
    assert r["board_text"] == _SYNTH_LF
    rec = r["ledger"]["zone_fill"][0]
    assert rec["refill_required"] is False and rec["fill_state"] == "unknown"


def test_zone_param_alias_equivalence():
    cu = _cu(_SYNTH_LF)
    z = cu["zones"][0]
    a = cp.apply_patch(_SYNTH_LF, [_mod(z, {"params": {"thermal_gap": 0.7}})])
    b = cp.apply_patch(_SYNTH_LF,
                       [_mod(z, {"params": {"fill_thermal_gap": 0.7}})])
    assert a["verdict"] == b["verdict"] == "accepted"
    assert a["board_text"] == b["board_text"]
    # expect 也可用别名断言（逐键子集语义）
    z2 = _zone_of(a["board_text"], _Z1)
    r = cp.apply_patch(a["board_text"], [
        {"op": "modify", "kind": "zone", "key": z2["key"],
         "expect": {"params": {"thermal_gap": 0.7}},
         "new": {"params": {"hatch": "edge 1"}}}])
    assert r["verdict"] == "accepted", r["reasons"]


def test_zone_expect_params_is_per_key_subset():
    cu = _cu(_SYNTH_LF)
    z = cu["zones"][0]
    ok = {"op": "modify", "kind": "zone", "key": z["key"],
          "expect": {"params": {"clearance": 0.2}},
          "new": {"params": {"thermal_gap": 0.9}}}
    assert cp.apply_patch(_SYNTH_LF, [ok])["verdict"] == "accepted"
    bad = {"op": "modify", "kind": "zone", "key": z["key"],
           "expect": {"params": {"clearance": 0.9}},
           "new": {"params": {"thermal_gap": 0.9}}}
    r = cp.apply_patch(_SYNTH_LF, [bad])
    assert r["verdict"] == "blocked" and r["board_text"] is None
    assert any(x.startswith("expect_mismatch: params.clearance")
               for x in r["reasons"])
    # 断言了目标 zone 里**没有落点**的可编辑参数键 ⇒ 也算不符
    missing = {"op": "modify", "kind": "zone", "key": z["key"],
               "expect": {"params": {"connect_pads_mode": "yes"}},
               "new": {"params": {"thermal_gap": 0.9}}}
    r2 = cp.apply_patch(_SYNTH_LF, [missing])
    assert r2["verdict"] == "blocked"
    assert any("expect_mismatch: params.connect_pads_mode(缺)" in x
               for x in r2["reasons"]), r2["reasons"]


# =========================================== 2) zone add / delete

def test_zone_add_records_fill_absent_and_no_filled_polygon():
    ops = [{"op": "add", "kind": "zone",
            "new": {"net": "GND", "layers": ["In1.Cu"],
                    "outline_mm": [[1, 1], [8, 1], [8, 8], [1, 8]],
                    "params": {"clearance": 0.25, "thermal_gap": 0.5,
                               "island_removal_mode": 1}}}]
    r = cp.apply_patch(_SYNTH_LF, ops)
    assert r["verdict"] == "accepted", r["reasons"]
    out = r["board_text"]
    led = r["ledger"]
    assert led["counts_before"]["zones"] == 1
    assert led["counts_after"]["zones"] == 2
    assert led["unchanged_bytes_outside_targets"] is True
    new_key = led["affected_keys"][0]["new_key"]
    node = _zone_node(out, new_key)
    assert "(filled_polygon" not in node          # 不得自造填充
    assert "(polygon" in node and "(pts" in node
    assert node.endswith(")") and node.startswith("(zone")
    rec = led["zone_fill"][0]
    assert rec["op"] == "add" and rec["fill_present"] is False
    assert rec["fill_state"] == "unknown"
    assert rec["refill_required"] is True
    assert rec["fill_absent_recorded"] is True
    assert rec["fill_points_after"] == 0
    s = led["zone_fill_summary"]
    assert s["absent_fill_zone_ids"] == [new_key]
    assert s["refill_required"] is True
    # copper_model 侧：新 zone 被如实解析（fill_points=0），板仍可解析
    nz = _zone_of(out, new_key)
    assert nz is not None and nz["fill_points"] == 0
    assert nz["outline_mm"] == [[1.0, 1.0], [8.0, 1.0], [8.0, 8.0], [1.0, 8.0]]
    assert nz["params"]["clearance"] == 0.25
    assert _cu(out)["unrepresentable"] == []
    # 缩进/括号风格与板内既有 zone 同构：新节点用到的行首缩进都在既有 zone
    # 的行首缩进集合内（既有 zone 多出 filled_polygon 的行，故是超集）
    old_lines = _zone_node(_SYNTH_LF, _zone_key(_cu(_SYNTH_LF), _Z1)).split("\n")
    new_lines = node.split("\n")
    assert set(l[:len(l) - len(l.lstrip())] for l in new_lines) <= \
        set(l[:len(l) - len(l.lstrip())] for l in old_lines)
    assert new_lines[0] == "(zone" and new_lines[-1] == "\t)"
    # 子行都是"制表符缩进 + 表达式/闭括号"形态（多行节点，无空行、无空格缩进）
    assert all(l.startswith("\t") and l.lstrip().startswith(("(", ")"))
               for l in new_lines[1:-1])
    assert not any(l.strip() == "" for l in new_lines)
    assert all(l[:len(l) - len(l.lstrip())].replace("\t", "") == ""
               for l in new_lines)


def test_zone_delete_removes_whole_node_lines():
    cu = _cu(_SYNTH_LF)
    z = cu["zones"][0]
    span = cu["identity_map"][z["key"]]["span"]
    removed = _SYNTH_LF[span[0] - 1:span[1] + 1]     # 前导缩进 + 节点 + 行尾
    r = cp.apply_patch(_SYNTH_LF, [
        {"op": "delete", "kind": "zone", "key": z["key"],
         "expect": _expect_zone(z)}])
    assert r["verdict"] == "accepted", r["reasons"]
    out = r["board_text"]
    assert _cu(out)["counts"]["zones"] == 0
    assert "(zone" not in out and "(filled_polygon" not in out
    # 整行摘除（含前导缩进与行尾）：长度与行数差精确对上，不留空白残行
    assert len(_SYNTH_LF) - len(out) == len(removed)
    assert _SYNTH_LF.count("\n") - out.count("\n") == removed.count("\n")
    assert "\n\n" not in out and "\t\n" not in out and "\r\n\r\n" not in out
    assert r["ledger"]["unchanged_bytes_outside_targets"] is True
    assert r["ledger"]["zone_fill"] == []          # delete 不触发重填门
    assert r["ledger"]["zone_fill_summary"]["refill_required"] is False


def test_zone_delete_real_revc_zone_roundtrip_lengths():
    """删一个多行 zone 后的长度差 = 节点字节 + 前导缩进 + 行尾（精确对账）。"""
    if not os.path.isfile(REVC):
        pytest.skip("真实板不存在")
    text = open(REVC, encoding="utf-8", newline="").read()
    cu = _cu(text)
    z = cu["zones"][0]
    span = cu["identity_map"][z["key"]]["span"]
    lead = len(text[:span[0]]) - len(text[:span[0]].rstrip("\t"))
    eol = 2 if text[span[1]:span[1] + 2] == "\r\n" else 0
    r = cp.apply_patch(text, [{"op": "delete", "kind": "zone", "key": z["key"],
                               "expect": _expect_zone(z)}])
    assert r["verdict"] == "accepted", r["reasons"]
    assert len(text) - len(r["board_text"]) == (span[1] - span[0]) + lead + eol
    assert r["ledger"]["counts_after"]["zones"] == 1


# =========================================== 3) 负向矩阵 + 整批不动

_NEG_CASES = [
    ("outline_lt3_points",
     {"outline_mm": [[1, 1], [8, 1]]}, "invalid_field"),
    ("outline_point_not_pair",
     {"outline_mm": [[1, 1], [8, 1], [8]]}, "invalid_field"),
    ("outline_point_non_numeric",
     {"outline_mm": [[1, 1], [8, 1], ["x", 8]]}, "invalid_field"),
    ("outline_point_nan",
     {"outline_mm": [[1, 1], [8, 1], [float("inf"), 8]]}, "invalid_field"),
    ("net_unmapped",
     {"net": "NO_SUCH_NET"}, "net_unmapped"),
    ("params_enum_invalid",
     {"params": {"fill": "maybe"}}, "invalid_field"),
    ("params_enum_int_invalid",
     {"params": {"island_removal_mode": 7}}, "invalid_field"),
    ("params_not_a_number",
     {"params": {"clearance": "0.2"}}, "invalid_field"),
    ("params_unknown_key",
     {"params": {"priority": 3}}, "invalid_field"),
    ("params_not_present",
     {"params": {"connect_pads_mode": "yes"}}, "param_not_present"),
    ("unknown_field",
     {"island_removal": 1}, "invalid_field"),
]


@pytest.mark.parametrize("name,new,code",
                         _NEG_CASES, ids=[c[0] for c in _NEG_CASES])
def test_zone_negative_matrix_blocks_whole_batch(name, new, code):
    cu = _cu(_SYNTH_LF)
    z = cu["zones"][0]
    ops = [
        {"op": "add", "kind": "segment",
         "new": {"net": "N1", "layer": "F.Cu", "width": 0.2,
                 "start": [1.0, 2.0], "end": [1.0, 3.0]}},
        _mod(z, new),
    ]
    r = cp.apply_patch(_SYNTH_LF, ops)
    assert r["verdict"] == "blocked", name
    assert r["board_text"] is None                 # 整批不动（无半成品文本）
    assert any(x.startswith(code + ":") for x in r["reasons"]), r["reasons"]
    led = r["ledger"]
    assert led["ops_applied"] == 0
    assert led["adds"] == 0 and led["modifies"] == 0 and led["deletes"] == 0
    assert led["affected_keys"] == []
    assert led["counts_after"] is None
    assert led["unchanged_bytes_outside_targets"] is None
    assert led["blocked_ops"] and led["blocked_ops"][0]["index"] == 1


def test_zone_add_negative_matrix_blocks_whole_batch():
    cases = [
        ({"net": "GND", "layers": ["B.Cu"]}, "missing_new"),
        ({"net": "NO_SUCH_NET", "layers": ["B.Cu"],
          "outline_mm": [[1, 1], [8, 1], [8, 8]]}, "net_unmapped"),
        ({"net": "GND", "layers": [], "outline_mm": [[1, 1], [8, 1], [8, 8]]},
         "invalid_field"),
        ({"net": "GND", "layers": ["B.Cu"], "outline_mm": [[1, 1], [8, 1]]},
         "invalid_field"),
    ]
    for new, code in cases:
        r = cp.apply_patch(_SYNTH_LF, [{"op": "add", "kind": "zone",
                                        "new": new}])
        assert r["verdict"] == "blocked", (new, r["reasons"])
        assert r["board_text"] is None
        assert any(x.startswith(code + ":") for x in r["reasons"]), (new,
                                                                    r["reasons"])
        assert r["ledger"]["counts_after"] is None


def test_zone_batch_atomicity_valid_op_with_bad_zone_op():
    """含非法 zone op 的批次：同批合法 op 也不得落实（整批原子）。"""
    cu = _cu(_SYNTH_LF)
    z = cu["zones"][0]
    ops = [
        {"op": "modify", "kind": "segment", "key": cu["segments"][0]["key"],
         "expect": {"net": "N1"}, "new": {"width": 0.4}},
        _mod(z, {"outline_mm": [[1, 1], [2, 2]]}),
    ]
    r = cp.apply_patch(_SYNTH_LF, ops)
    assert r["verdict"] == "blocked" and r["board_text"] is None
    assert r["ledger"]["modifies"] == 0
    assert r["ledger"]["ops_applied"] == 0


# =========================================== 4) CRLF 零劣化（连续 ≥2 轮）

def _zone_round(board, uuid, delta):
    cu = _cu(board)
    z = [x for x in cu["zones"] if x["uuid"] == uuid][0]
    r = cp.apply_patch(board, [_mod(z, {"outline_mm": [
        [0.5 + delta, 0.5], [9.5 - delta, 0.5], [9.5 - delta, 9.5],
        [0.5 + delta, 9.5]]})])
    assert r["verdict"] == "accepted", r["reasons"]
    return r


def test_crlf_zero_degradation_three_rounds_synthetic():
    board = _SYNTH_CRLF
    assert _bare_lf(board) == 0
    for i in range(3):
        r = _zone_round(board, _Z1, 0.1 * (i + 1))
        board = r["board_text"]
        assert _bare_lf(board) == 0
        assert board.count("\n") == board.count("\r\n")
        assert r["ledger"]["eol"] == "\r\n"
        assert r["ledger"]["unchanged_bytes_outside_targets"] is True
    assert _cu(board)["counts"]["zones"] == 1


@pytest.mark.skipif(not os.path.isfile(REVC), reason="真实板不存在")
def test_crlf_zero_degradation_two_rounds_real_revc():
    board = open(REVC, encoding="utf-8", newline="").read()
    for i in range(2):
        cu = _cu(board)
        z = cu["zones"][0]
        r = cp.apply_patch(board, [_mod(z, {"outline_mm": [
            [0.5 + 0.05 * (i + 1), 0.5], [69.5, 0.5], [69.5, 69.5],
            [0.5, 69.5]]}, with_params=True)])
        assert r["verdict"] == "accepted", (i, r["reasons"])
        board = r["board_text"]
        assert _bare_lf(board) == 0
        assert board.count("\n") == board.count("\r\n")
        assert r["ledger"]["eol"] == "\r\n"
        assert r["ledger"]["unchanged_bytes_outside_targets"] is True
        assert r["ledger"]["zone_fill"][0]["fill_bytes_preserved"] is True


# =========================================== 5) 真实 Rev-C 实战

_REVC_TXT = {}


def _revc_text():
    if "t" not in _REVC_TXT:
        with open(REVC, encoding="utf-8", newline="") as f:
            _REVC_TXT["t"] = f.read()
    return _REVC_TXT["t"]


@pytest.mark.skipif(not os.path.isfile(REVC), reason="真实板不存在")
def test_revc_zone_outline_and_params_modify_round():
    text = _revc_text()
    cu = _cu(text)
    z = cu["zones"][0]                       # 3dabd785… / B.Cu / 5715 点
    assert z["uuid"] == "3dabd785-e301-41f1-8359-56e7a983fe20"
    assert z["fill_points"] == 5715
    old_fill = _fill_text(text, z)[0]
    t0 = time.perf_counter()
    r = cp.apply_patch(text, [_mod(z, {
        "outline_mm": [[1.0, 1.0], [69.0, 1.0], [69.0, 69.0], [1.0, 69.0]],
        "params": {"thermal_gap": 0.6, "clearance": 0.25}},
        with_params=True)])
    elapsed = time.perf_counter() - t0
    assert r["verdict"] == "accepted", r["reasons"]
    out = r["board_text"]
    led = r["ledger"]
    z2 = _zone_of(out, z["uuid"])
    assert z2["outline_mm"] == [[1.0, 1.0], [69.0, 1.0], [69.0, 69.0],
                                [1.0, 69.0]]
    assert z2["params"]["fill_thermal_gap"] == 0.6
    assert z2["params"]["clearance"] == 0.25
    # fill_points 未被重写（字节切片 + copper_model 双证）
    assert z2["fill_points"] == 5715
    assert _fill_text(out, z2)[0] == old_fill
    rec = led["zone_fill"][0]
    assert rec["fill_points_before"] == rec["fill_points_after"] == 5715
    assert rec["fill_sha256_before"] == rec["fill_sha256_after"]
    assert rec["fill_bytes_preserved"] is True
    assert rec["copper_model_fill_identical"] is True
    assert rec["copper_model_fill_before"]["fill_sha256"] == \
        z["fill_sha256"]
    assert rec["fill_state"] == "stale"
    assert sorted(rec["stale_params"]) == ["clearance", "fill_thermal_gap"]
    assert rec["stale_fields"] == ["outline_mm"]
    # 另一 zone（18795 点）逐字节未动
    other = [x for x in cu["zones"] if x["uuid"] != z["uuid"]][0]
    o_span = cu["identity_map"][other["key"]]["span"]
    o_new = _cu(out)["identity_map"][other["key"]]["span"]
    assert text[o_span[0]:o_span[1]] == out[o_new[0]:o_new[1]]
    # 行尾 + 既有强度
    assert _bare_lf(out) == 0
    assert out.count("\n") == out.count("\r\n") == text.count("\r\n")
    assert led["unchanged_bytes_outside_targets"] is True
    assert led["structural_guard"]["ok"] is True
    # M1 刷新：counts=dbfea089 夹具板实测 2372/358/2（zone 轮计数不变，仅钉板）
    assert led["counts_before"] == led["counts_after"] == \
        {"segments": 2372, "vias": 358, "zones": 2}
    assert _cu(out)["unrepresentable"] == []
    assert elapsed < 30.0
    print("\n[REVC zone modify] verdict=%s elapsed=%.3fs len_delta=%d"
          % (r["verdict"], elapsed, len(out) - len(text)))


@pytest.mark.skipif(not os.path.isfile(REVC), reason="真实板不存在")
def test_revc_zone_delete_round():
    text = _revc_text()
    cu = _cu(text)
    z = [x for x in cu["zones"]
         if x["uuid"] == "5d173b87-fb0f-4e68-83a5-c32f98fdebd6"][0]
    assert z["fill_points"] == 18795
    t0 = time.perf_counter()
    r = cp.apply_patch(text, [{"op": "delete", "kind": "zone", "key": z["key"],
                               "expect": _expect_zone(z, with_params=True)}])
    elapsed = time.perf_counter() - t0
    assert r["verdict"] == "accepted", r["reasons"]
    out = r["board_text"]
    led = r["ledger"]
    assert led["counts_before"]["zones"] == 2
    assert led["counts_after"]["zones"] == 1
    # M1 刷新：删 zone 后计数=2372/358/1（zones 由 2 删至 1，仅钉板）
    assert _cu(out)["counts"] == {"segments": 2372, "vias": 358, "zones": 1}
    # 另一个 zone 逐字节未动
    kept = [x for x in cu["zones"] if x["uuid"] != z["uuid"]][0]
    s0 = cu["identity_map"][kept["key"]]["span"]
    s1 = _cu(out)["identity_map"][kept["key"]]["span"]
    assert text[s0[0]:s0[1]] == out[s1[0]:s1[1]]
    assert led["unchanged_bytes_outside_targets"] is True
    assert _bare_lf(out) == 0
    assert out.count("\n") == out.count("\r\n")
    assert led["zone_fill_summary"]["refill_required"] is False
    assert elapsed < 30.0
    print("\n[REVC zone delete] verdict=%s elapsed=%.3fs len_delta=%d"
          % (r["verdict"], elapsed, len(out) - len(text)))


# =========================================== 6) fill_gate（纯函数）

def _gate_record(staging_sha="a" * 64, patch=None):
    return {"patch": patch if patch is not None
            else {"staging_sha256": staging_sha}}


def _ledger_with(records):
    return {"patch_ledger": {"zone_fill": records,
                             "zone_fill_summary": cp._zone_fill_summary(
                                 records)}}


def _stale_record(zone_id="z1"):
    return {"index": 0, "op": "modify", "zone_id": zone_id,
            "zone_key": zone_id, "fill_state": "stale", "fill_present": True,
            "fill_invalidated": True, "refill_required": True,
            "stale_fields": ["outline_mm"], "stale_params": []}


def _evidence(source_sha="a" * 64, **over):
    ev = {"schema": cp.REFILL_EVIDENCE_SCHEMA, "refill_performed": True,
          "source_board_sha256": source_sha,
          "refilled_board_sha256": "b" * 64,
          "kicad_version": "9.0.1",
          "steps": [{"step": "kicad-cli pcb drc --refill-zones --format json "
                           "-o drc/staging.json patched/x.kicad_pcb",
                     "exit_code": 0}]}
    ev.update(over)
    return ev


def test_fill_gate_not_required_without_zone_ops():
    g = cp.fill_gate(_gate_record(), ledger={"patch_ledger": {
        "zone_fill": [], "zone_fill_summary": cp._zone_fill_summary([])}})
    assert g["ok"] is True and g["required"] is False
    assert g["reasons"] == [] and g["reason_code"] is None
    assert g["status_label"] == "ok"
    # 缺 zone_fill_summary（台账/记录均无）⇒ required 不可推导 ⇒ fail-closed
    # 拒绝（REPAIR-P2 W-3：旧版静默视 required=False 放行是 fail-open，
    # 铜环裁决 2026-09-11 §8 P1-2 从"缓修"转"修复"）
    g2 = cp.fill_gate(_gate_record(), ledger={"events": []})
    assert g2["ok"] is False and g2["required"] is None
    assert g2["reason_code"] == "ledger_missing"
    assert g2["status_label"] == "unverifiable"
    assert g2["reasons"][0].startswith("ledger_missing:")


def test_fill_gate_hash_only_zone_edit_is_not_required():
    rec = {"index": 0, "op": "modify", "zone_id": "z1", "zone_key": "z1",
           "fill_state": "unknown", "fill_present": True,
           "fill_invalidated": False, "refill_required": False,
           "stale_fields": [], "stale_params": ["hatch"]}
    g = cp.fill_gate(_gate_record(), ledger=_ledger_with([rec]))
    assert g["ok"] is True and g["required"] is False


def test_fill_gate_missing_evidence_is_refused_with_exact_reason():
    g = cp.fill_gate(_gate_record(), ledger=_ledger_with([_stale_record()]))
    assert g["ok"] is False and g["required"] is True
    assert g["reason_code"] == "refill_evidence_missing"
    assert g["status_label"] == "awaiting_refill"
    assert g["reasons"][0].startswith("refill_evidence_missing:")
    assert g["not_fresh_zone_ids"] == ["z1"]
    assert g["expected_source_sha256"] == "a" * 64
    assert g["rule"] == cp.REFILL_GATE_RULE


def test_fill_gate_added_zone_without_fill_is_also_required():
    rec = {"index": 0, "op": "add", "zone_id": "new-1", "zone_key": "new-1",
           "fill_state": "unknown", "fill_present": False,
           "fill_invalidated": False, "refill_required": True,
           "stale_fields": [], "stale_params": []}
    g = cp.fill_gate(_gate_record(), ledger=_ledger_with([rec]))
    assert g["ok"] is False and g["reason_code"] == "refill_evidence_missing"
    assert g["not_fresh_zone_ids"] == ["new-1"]


def test_fill_gate_valid_evidence_passes():
    ev = _evidence()
    g = cp.fill_gate(_gate_record(), ledger=_ledger_with([_stale_record()]),
                     evidence=ev)
    assert g["ok"] is True and g["required"] is True
    assert g["reasons"] == []
    assert g["evidence_source"] == "explicit"
    assert g["refill_evidence_sha256"] == cp._sha(ev)
    assert g["status_label"] == "ok"


def test_fill_gate_evidence_must_bind_this_revision_staging():
    ev = _evidence(source_sha="c" * 64)
    g = cp.fill_gate(_gate_record(), ledger=_ledger_with([_stale_record()]),
                     evidence=ev)
    assert g["ok"] is False
    assert g["reason_code"] == "refill_evidence_stale"
    assert any("refill_evidence_stale" in x for x in g["reasons"])


_BAD_EVIDENCE = [
    ("not_object", "not-a-dict", "refill_evidence_invalid"),
    ("bad_schema", {"schema": "x"}, "refill_evidence_schema_mismatch"),
    ("not_performed", _evidence(refill_performed=False),
     "refill_evidence_invalid"),
    ("no_steps", _evidence(steps=[]), "refill_evidence_invalid"),
    ("step_failed", _evidence(steps=[{"step": "refill", "exit_code": 1}]),
     "refill_evidence_invalid"),
    ("step_no_name", _evidence(steps=[{"exit_code": 0}]),
     "refill_evidence_invalid"),
    ("no_kicad_version", _evidence(kicad_version=""), "refill_evidence_invalid"),
    ("bad_source_sha", _evidence(source_board_sha256="zz"),
     "refill_evidence_invalid"),
    ("bad_refilled_sha", _evidence(refilled_board_sha256=None),
     "refill_evidence_invalid"),
]


@pytest.mark.parametrize("name,ev,code", _BAD_EVIDENCE,
                         ids=[c[0] for c in _BAD_EVIDENCE])
def test_fill_gate_malformed_evidence_refused(name, ev, code):
    g = cp.fill_gate(_gate_record(), ledger=_ledger_with([_stale_record()]),
                     evidence=ev)
    assert g["ok"] is False, name
    assert any(x.startswith(code + ":") for x in g["reasons"]), (name,
                                                                 g["reasons"])
    assert cp.validate_refill_evidence(ev, "a" * 64) != []


def test_fill_gate_reads_evidence_file_from_revision_dir():
    d = _scratch("gate")
    rec = _gate_record()
    led = _ledger_with([_stale_record()])
    # 尚未落证据文件 ⇒ 拦
    assert cp.fill_gate(rec, ledger=led, revision_dir=d)["ok"] is False
    os.makedirs(os.path.join(d, "drc"), exist_ok=True)
    with open(os.path.join(d, cp.REFILL_EVIDENCE_REL), "w",
              encoding="utf-8") as f:
        json.dump(_evidence(), f)
    g = cp.fill_gate(rec, ledger=led, revision_dir=d)
    assert g["ok"] is True
    assert g["evidence_source"] == "drc/refill-evidence.json"
    # 不可解析的证据 ⇒ 明确 reason，不静默当"无证据"
    with open(os.path.join(d, cp.REFILL_EVIDENCE_REL), "w",
              encoding="utf-8") as f:
        f.write("{not json")
    g2 = cp.fill_gate(rec, ledger=led, revision_dir=d)
    assert g2["ok"] is False and g2["reason_code"] == \
        "refill_evidence_unparseable"


# =========================================== 7) copper_loop 采纳门接入

def _lock_version():
    with open(os.path.join(PCBFLOW_ROOT, "toolchain_lock.json"),
              encoding="utf-8") as f:
        return (json.load(f).get("kicad_cli") or {}).get("version")


def _drc_report(source_basename):
    return {"$schema": "https://schemas.kicad.org/drc.v1.json",
            "coordinate_units": "mm", "date": "2026-09-11T00:00:00",
            "ignored_checks": [], "included_severities": ["error"],
            "kicad_version": _lock_version(), "schematic_parity": [],
            "source": source_basename, "violations": [],
            "unconnected_items": []}


def _write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    return path


@pytest.fixture(scope="module")
def revc_zone_revision():
    """Rev-C 上跑一轮**含 outline 变更的 zone modify** 补丁（共享只读）。"""
    if not os.path.isfile(REVC):
        pytest.skip("真实板不存在")
    out_dir = _scratch("loop")
    text = open(REVC, encoding="utf-8", newline="").read()
    cu = _cu(text)
    z = [x for x in cu["zones"]
         if x["uuid"] == "3dabd785-e301-41f1-8359-56e7a983fe20"][0]
    op = _mod(z, {"outline_mm": [[0.75, 0.75], [69.25, 0.75], [69.25, 69.25],
                                 [0.75, 69.25]]})
    rec = copper_loop.revision(REVC, {"patch_set_id": "r3-zone", "ops": [op]},
                               out_dir, base_label="zone")
    rev_dir = os.path.join(out_dir, copper_loop.LOOP_DIRNAME, "zone", "rev-1")
    assert rec["status"] == copper_loop.STATUS_AWAITING_DRC, rec["reasons"]
    report = _write_json(os.path.join(out_dir, "drc-clean.json"),
                         _drc_report(os.path.basename(REVC)))
    led = json.load(open(os.path.join(rev_dir, "ledger.json"),
                         encoding="utf-8"))
    return {"out_dir": out_dir, "rev_dir": rev_dir, "record": rec,
            "report": report, "ledger": led}


def test_loop_patch_ledger_carries_zone_fill_summary(revc_zone_revision):
    led = revc_zone_revision["ledger"]
    pl = led["patch_ledger"]
    assert pl["zone_fill_summary"]["refill_required"] is True
    assert pl["zone_fill_summary"]["stale_zone_ids"] == \
        ["3dabd785-e301-41f1-8359-56e7a983fe20"]
    assert pl["patch_ledger" if False else "zone_fill"][0]["fill_state"] == \
        "stale"


def test_accept_refused_without_refill_evidence_then_accepted_with_it(
        revc_zone_revision):
    rd = revc_zone_revision["rev_dir"]
    report = revc_zone_revision["report"]
    rec_file = os.path.join(rd, "revision-record.json")
    before = hashing.sha256_file(rec_file)

    # (1) 无重填证据 ⇒ 拦，reason 正确，轮次**未被写死**（仍 awaiting_drc）
    res = copper_loop.accept_revision(rd, report)
    assert res["status"] == copper_loop.STATUS_BLOCKED
    assert res["persisted"] is False
    assert res["revision_status"] == copper_loop.STATUS_AWAITING_DRC
    assert any(x.startswith("refill_evidence_missing:")
               for x in res["reasons"]), res["reasons"]
    assert res["fill_gate"]["status_label"] == "awaiting_refill"
    assert res["fill_gate"]["not_fresh_zone_ids"] == \
        ["3dabd785-e301-41f1-8359-56e7a983fe20"]
    assert hashing.sha256_file(rec_file) == before      # 记录未被改写
    on_disk = json.load(open(rec_file, encoding="utf-8"))
    assert on_disk["status"] == copper_loop.STATUS_AWAITING_DRC
    events = json.load(open(os.path.join(rd, "ledger.json"),
                            encoding="utf-8"))["events"]
    assert [e["event"] for e in events][-1] == "accept_refused"

    # (2) 补齐重填证据（绑定本轮 staging sha）⇒ 放行 → accepted
    staging_sha = on_disk["patch"]["staging_sha256"]
    _write_json(os.path.join(rd, cp.REFILL_EVIDENCE_REL),
                _evidence(source_sha=staging_sha))
    res2 = copper_loop.accept_revision(rd, report)
    assert res2["status"] == copper_loop.STATUS_ACCEPTED, res2.get("reasons")
    assert res2["usable"] is True
    assert res2["drc_decision"]["violations_new"] == 0


def test_adopt_refused_without_refill_evidence_then_ok_with_it(
        revc_zone_revision):
    rd = revc_zone_revision["rev_dir"]
    on_disk = json.load(open(os.path.join(rd, "revision-record.json"),
                             encoding="utf-8"))
    assert on_disk["status"] == copper_loop.STATUS_ACCEPTED
    design = os.path.join(_scratch("adopt"), os.path.basename(REVC))
    shutil.copyfile(REVC, design)
    ev_path = os.path.join(rd, cp.REFILL_EVIDENCE_REL)
    keep = open(ev_path, "rb").read()

    # (1) 证据被移走 ⇒ adopt 同样被拦（纵深防御），设计侧未被写
    os.remove(ev_path)
    design_sha = hashing.sha256_file(design)
    res = copper_loop.adopt(rd, design)
    assert res["status"] == copper_loop.STATUS_BLOCKED
    assert res["persisted"] is False
    assert res["revision_status"] == copper_loop.STATUS_ACCEPTED
    assert any(x.startswith("refill_evidence_missing:")
               for x in res["reasons"]), res["reasons"]
    assert hashing.sha256_file(design) == design_sha
    assert not os.path.isfile(os.path.join(
        os.path.dirname(design), "%s_pre-adopt-rev-1.kicad_pcb"
        % os.path.splitext(os.path.basename(REVC))[0]))

    # (2) 证据回位 ⇒ adopt 放行（写到 scratch 副本，**不碰 design/**）
    with open(ev_path, "wb") as f:
        f.write(keep)
    res2 = copper_loop.adopt(rd, design)
    assert res2["status"] == copper_loop.STATUS_ACCEPTED, res2.get("reasons")
    assert res2["adopted"] is True
    ar = json.load(open(os.path.join(rd, "adopt-record.json"),
                        encoding="utf-8"))
    assert ar["design_board_sha256_post"] == on_disk["patch"]["staging_sha256"]
    assert ar["live_board_touched"] is False
    assert not design.startswith(os.path.join(config.WORKSPACE_ROOT, "design"))


@pytest.mark.skipif(not os.path.isfile(REVC), reason="真实板不存在")
def test_accept_without_zone_ops_is_not_gated():
    """未触及 zone 的轮次一律放行（门不得把普通补丁也拦下来）。"""
    out_dir = _scratch("nofill")
    text = open(REVC, encoding="utf-8", newline="").read()
    seg = [e for e in _cu(text)["segments"] if e["layer"] == "In2.Cu"][0]
    op = {"op": "modify", "kind": "segment", "key": seg["key"],
          "expect": {k: seg[k] for k in ("net", "layer", "width", "start",
                                         "end")},
          "new": {"width": 0.25}}
    rec = copper_loop.revision(REVC, {"ops": [op]}, out_dir,
                               base_label="noseg")
    assert rec["status"] == copper_loop.STATUS_AWAITING_DRC, rec["reasons"]
    rev_dir = os.path.join(out_dir, copper_loop.LOOP_DIRNAME, "noseg", "rev-1")
    led = json.load(open(os.path.join(rev_dir, "ledger.json"),
                         encoding="utf-8"))
    assert led["patch_ledger"]["zone_fill_summary"]["refill_required"] is False
    assert led["patch_ledger"]["zone_fill"] == []
    report = _write_json(os.path.join(out_dir, "drc.json"),
                         _drc_report(os.path.basename(REVC)))
    res = copper_loop.accept_revision(rev_dir, report)
    assert res["status"] == copper_loop.STATUS_ACCEPTED, res.get("reasons")


def test_fill_gate_ledger_unavailable_is_refused(tmp_path):
    """台账存在但不可解析 ⇒ fail-closed（拒绝本次尝试，不改轮次）。"""
    rev = tmp_path / "rev-1"
    rev.mkdir()
    rec = {"schema": copper_loop.SCHEMA, "revision_id": "r", "base_label": "b",
           "rev": 1, "status": copper_loop.STATUS_AWAITING_DRC,
           "verdict": copper_loop.STATUS_AWAITING_DRC, "ok": True,
           "usable": False, "reasons": [], "rollback": "armed",
           "adopted": False, "patch": {"staging": "patched/x.kicad_pcb",
                                       "staging_sha256": "a" * 64},
           "transaction": {"batches": [], "live_board_touched": False}}
    _write_json(str(rev / "revision-record.json"), rec)
    with open(rev / "ledger.json", "w", encoding="utf-8") as f:
        f.write("{broken")
    res = copper_loop.accept_revision(str(rev), str(rev / "nope.json"))
    assert res["status"] == copper_loop.STATUS_BLOCKED
    assert res["persisted"] is False
    assert any(x.startswith("fill_gate_ledger_unavailable:")
               for x in res["reasons"]), res["reasons"]


# ------------------- R4③ live 板不变量 + 负对照（REPAIR-P1 W-5）

@pytest.mark.skipif(not os.path.isfile(str(config.REVC_BOARD)),
                    reason="真实板不存在")
def test_revc_zone_live_invariants_only():
    """R4③ live 板不变量用例：live 板演进不破坏 zone 合同（不带精确身份）。

    只断板无关不变量——至少一个 zone、zone 身份/填充字段形状合法、
    零不可表示、CRLF 纯净；zone uuid/fill_points 精确口径由钉夹具板的
    modify/delete 轮用例守护。板输入走 config.REVC_BOARD（live）。
    """
    with open(config.REVC_BOARD, encoding="utf-8", newline="") as f:
        text = f.read()
    cu = _cu(text)
    assert cu["counts"]["zones"] >= 1
    assert cu["unrepresentable"] == []
    for z in cu["zones"]:
        assert z["key"].startswith(z["uuid"])
        assert isinstance(z["fill_points"], int) and z["fill_points"] >= 0
        assert isinstance(z["fill_sha256"], str) and z["fill_sha256"]
    assert text.count("\n") == text.count("\r\n")


def test_negative_control_board_tamper_moves_counts():
    """负对照（R28「不得弱化」硬约束检出证明）：注入一个新 uuid 的 segment
    后 zone 轮前置计数随之 +1（2372→2373）——精确断言确实跟踪板字节。"""
    tampered = revc_board_fixture.duplicate_first_segment(
        revc_board_fixture.fixture_board_text())
    cu = _cu(tampered)
    assert cu["counts"]["segments"] == 2373
    assert cu["unrepresentable"] == []
    assert cu["counts"]["segments"] != 2372    # M1 精确值在此板内容下不成立
