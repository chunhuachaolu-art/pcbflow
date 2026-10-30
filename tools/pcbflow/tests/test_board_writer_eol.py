"""board_writer 行尾（EOL）能力单测：opt-in 保真，默认路径逐字节不变。

背景：真实板 Rev-C 为纯 CRLF（probe: out/revc-asm/board 快照 17986 CRLF/0 裸 LF），
而历史 writer 链硬编码 "\\n"，每次 apply_routes 都在原始区之后引入 LF-only 行
（applied.kicad_pcb 实测 18114 CRLF + 37840 裸 LF）→ 闭环反复编辑会逐轮劣化。

约定（本文件守卫）：
  * nodes_text/apply_routes 不传 eol 时输出与历史实现逐字节相同（历史实现逐字
    复刻见 _legacy_*，另有固定期望字符串 _NODE_LF/_APPLIED_LF）；
  * eol="auto" 按 pristine 主导行尾；只影响**新增节点**，pristine 自身字节不动。
"""

from __future__ import annotations

import inspect

import pytest

from pcbflow import board_writer

_UUID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

# ---- 固定期望：历史口径（LF + \t 缩进 + %.4f 去尾零 + 字段顺序） -------------
_ROUTE = {
    "net": "N1",
    "width": 0.2500,
    "via_size": 0.4500,
    "via_drill": 0.2000,
    "uuid": _UUID,
    "segments": [[0, 1.0, 2.0, 3.0, 4.0]],
    "vias": [[5.0, 6.0]],
}

_ROUTE2 = {
    "net": "N2",
    "width": 0.3,
    "via_size": 0.45,
    "via_drill": 0.2,
    "uuid": "11111111-2222-3333-4444-555555555555",
    "segments": [[6, 7.0, 8.0, 9.0, 10.0]],
    "vias": [],
}

_NODE_LF = (
    "\t(segment\n"
    "\t\t(start 1.0000 2.0000)\n"
    "\t\t(end 3.0000 4.0000)\n"
    "\t\t(width 0.25)\n"
    '\t\t(layer "F.Cu")\n'
    '\t\t(net "N1")\n'
    '\t\t(uuid "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")\n'
    "\t)\n"
    "\t(via buried\n"
    "\t\t(at 5.0000 6.0000)\n"
    "\t\t(size 0.45)\n"
    "\t\t(drill 0.2)\n"
    '\t\t(layers "F.Cu" "In2.Cu")\n'
    '\t\t(net "N1")\n'
    '\t\t(uuid "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")\n'
    "\t)\n"
)

_PRISTINE_LF = (
    "(kicad_pcb\n"
    "\t(version 20260206)\n"
    '\t(net 0 "")\n'
    '\t(net 1 "N1")\n'
    '\t(gr_rect (start 0 0) (end 10 10) (layer "Edge.Cuts") (width 0.05)'
    ' (uuid "e0"))\n'
    ")\n"
)

_APPLIED_LF = (
    "(kicad_pcb\n"
    "\t(version 20260206)\n"
    '\t(net 0 "")\n'
    '\t(net 1 "N1")\n'
    '\t(gr_rect (start 0 0) (end 10 10) (layer "Edge.Cuts") (width 0.05)'
    ' (uuid "e0"))\n'
    "\t(segment\n"
    "\t\t(start 1.0000 2.0000)\n"
    "\t\t(end 3.0000 4.0000)\n"
    "\t\t(width 0.25)\n"
    '\t\t(layer "F.Cu")\n'
    '\t\t(net "N1")\n'
    '\t\t(uuid "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")\n'
    "\t)\n"
    "\t(via buried\n"
    "\t\t(at 5.0000 6.0000)\n"
    "\t\t(size 0.45)\n"
    "\t\t(drill 0.2)\n"
    '\t\t(layers "F.Cu" "In2.Cu")\n'
    '\t\t(net "N1")\n'
    '\t\t(uuid "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")\n'
    "\t)\n"
    ")\n"
)

_PRISTINE_CRLF = _PRISTINE_LF.replace("\n", "\r\n")
_NODE_CRLF = _NODE_LF.replace("\n", "\r\n")
_APPLIED_CRLF = _PRISTINE_CRLF.rstrip()[:-1] + _NODE_CRLF + ")\r\n"


# ---- 历史实现逐字复刻（改动前 board_writer.py:33-76 的行为） ------------------
def _legacy_nodes_text(route):
    uuid = route.get("uuid") or board_writer.route_uuid(route)
    out = []
    for (L, x1, y1, x2, y2) in route["segments"]:
        out.append(
            "\t(segment\n"
            "\t\t(start %.4f %.4f)\n"
            "\t\t(end %.4f %.4f)\n"
            "\t\t(width %s)\n"
            '\t\t(layer "%s")\n'
            '\t\t(net "%s")\n'
            '\t\t(uuid "%s")\n'
            "\t)\n" % (x1, y1, x2, y2, board_writer._num(route["width"]),
                       board_writer.LAYER_FILE_NAME[L], route["net"], uuid))
    for (x, y) in route["vias"]:
        out.append(
            "\t(via buried\n"
            "\t\t(at %.4f %.4f)\n"
            "\t\t(size %s)\n"
            "\t\t(drill %s)\n"
            '\t\t(layers "F.Cu" "In2.Cu")\n'
            '\t\t(net "%s")\n'
            '\t\t(uuid "%s")\n'
            "\t)\n" % (x, y, board_writer._num(route["via_size"]),
                       board_writer._num(route["via_drill"]),
                       route["net"], uuid))
    return "".join(out)


def _legacy_apply_routes(pristine_text, routes):
    stripped = pristine_text.rstrip()
    if not stripped.endswith(")"):
        raise ValueError("板文本非预期结尾（缺根闭合括号）")
    tail = pristine_text[len(stripped):]
    return stripped[:-1] + "".join(_legacy_nodes_text(r)
                                   for r in routes) + ")" + tail


def _no_bare_eol(text):
    """去净 CRLF 后既无裸 LF 亦无裸 CR：**整份输出无 LF-only 行**。"""
    return "\n" not in text.replace("\r\n", "") and \
        "\r" not in text.replace("\r\n", "")


# ---- 1. 默认路径零变化 ------------------------------------------------------
def test_api_defaults_are_opt_in():
    """opt-in 契约：nodes_text 默认 "\\n"，apply_routes 默认 None（= 历史口径）。"""
    assert inspect.signature(board_writer.nodes_text).parameters["eol"] \
        .default == "\n"
    assert inspect.signature(board_writer.apply_routes).parameters["eol"] \
        .default is None


def test_nodes_text_default_matches_fixed_expected():
    """固定期望字符串：默认输出仍为历史 LF 口径（含 \\t 缩进与去尾零）。"""
    assert board_writer.nodes_text(_ROUTE) == _NODE_LF
    assert "\r" not in board_writer.nodes_text(_ROUTE)


def test_nodes_text_default_matches_legacy_implementation():
    """与改动前实现逐字节相同（含无显式 uuid 的内容派生分支、纯 segment 网）。"""
    for r in (_ROUTE, _ROUTE2, {k: v for k, v in _ROUTE2.items()
                                if k != "uuid"}):
        assert board_writer.nodes_text(r) == _legacy_nodes_text(r)
        assert board_writer.nodes_text(r, eol="\n") == _legacy_nodes_text(r)


def test_apply_routes_default_matches_fixed_expected_and_legacy():
    """apply_routes 默认输出 = 固定期望 = 历史实现（pristine 无尾随空白以外变体）。"""
    assert board_writer.apply_routes(_PRISTINE_LF, [_ROUTE]) == _APPLIED_LF
    assert board_writer.apply_routes(_PRISTINE_LF, [_ROUTE]) == \
        _legacy_apply_routes(_PRISTINE_LF, [_ROUTE])
    assert board_writer.apply_routes(_PRISTINE_LF, [_ROUTE], eol=None) == \
        _APPLIED_LF
    assert board_writer.apply_routes(_PRISTINE_LF, [_ROUTE], eol="\n") == \
        _APPLIED_LF


def test_apply_routes_default_unchanged_even_on_crlf_input():
    """默认 eol（不传参）在 CRLF 板上仍按历史口径落 LF 节点（不动既有契约）。"""
    out = board_writer.apply_routes(_PRISTINE_CRLF, [_ROUTE])
    assert out != _APPLIED_CRLF
    assert out.startswith(_PRISTINE_CRLF.rstrip()[:-1])
    assert _NODE_LF in out


# ---- 2. CRLF / auto：输出板不出现裸 LF --------------------------------------
def test_nodes_text_crlf_only_changes_separators():
    t = board_writer.nodes_text(_ROUTE, eol="\r\n")
    assert t == _NODE_CRLF
    assert _no_bare_eol(t)
    # 反向不变式：CRLF 输出 == LF 输出仅换行符不同（缩进/数值/顺序不变）
    assert t.replace("\r\n", "\n") == board_writer.nodes_text(_ROUTE)


def test_apply_routes_explicit_crlf_no_bare_lf_and_bytes_preserved():
    out = board_writer.apply_routes(_PRISTINE_CRLF, [_ROUTE], eol="\r\n")
    assert out == _APPLIED_CRLF
    assert _no_bare_eol(out)
    assert out.encode("utf-8").count(b"\n") == \
        out.encode("utf-8").count(b"\r\n")
    # 除新增节点外原始字节未变（摘掉新节点即还原 pristine）
    assert out.replace(_NODE_CRLF, "", 1) == _PRISTINE_CRLF


def test_apply_routes_auto_on_crlf_board_equals_explicit_crlf():
    auto = board_writer.apply_routes(_PRISTINE_CRLF, [_ROUTE], eol="auto")
    assert auto == _APPLIED_CRLF
    assert _no_bare_eol(auto)
    assert auto.replace(_NODE_CRLF, "", 1) == _PRISTINE_CRLF


def test_apply_routes_crlf_multiple_routes_and_vias():
    """多网（含 via 与无 via 混合）：全部新增节点统一 CRLF，无裸 LF。"""
    out = board_writer.apply_routes(_PRISTINE_CRLF, [_ROUTE, _ROUTE2],
                                    eol="auto")
    assert _no_bare_eol(out)
    assert '(net "N1")' in out and '(net "N2")' in out
    assert out.count("\t(segment\r\n") == 2
    assert out.count("\t(via buried\r\n") == 1
    assert out.replace(_NODE_CRLF, "", 1).replace(
        board_writer.nodes_text(_ROUTE2, eol="\r\n"), "", 1) == _PRISTINE_CRLF


def test_closed_loop_repeated_edits_stay_pure_crlf():
    """P0 目标：同一块 CRLF 板反复闭环编辑，行尾不再逐轮劣化。"""
    t1 = board_writer.apply_routes(_PRISTINE_CRLF, [_ROUTE], eol="auto")
    t2 = board_writer.apply_routes(t1, [_ROUTE2], eol="auto")
    t3 = board_writer.apply_routes(t2, [_ROUTE], eol="auto")
    for t in (t1, t2, t3):
        assert _no_bare_eol(t)
    assert board_writer.dominant_eol(t3) == "\r\n"
    assert t3.count("\r\n") == t3.count("\n")


def test_auto_requires_newline_preserving_read(tmp_path):
    """文件闭环：CRLF 板经 newline="" 读出 → auto 保 CRLF 落盘，无裸 LF。

    同时钉住调用方契约：默认 text 模式读已把 CRLF 归一为 LF，auto 只能给 LF
    （故本测试显式 newline=""）。"""
    pcb = tmp_path / "b.kicad_pcb"
    pcb.write_bytes(_PRISTINE_CRLF.encode("utf-8"))
    with open(pcb, encoding="utf-8", newline="") as f:
        raw = f.read()
    assert board_writer.dominant_eol(raw) == "\r\n"
    raw_out = board_writer.apply_routes(raw, [_ROUTE, _ROUTE2], eol="auto")
    pcb.write_bytes(raw_out.encode("utf-8"))
    on_disk = pcb.read_bytes()
    added = 8 * (len(_ROUTE["segments"]) + len(_ROUTE["vias"])
                 + len(_ROUTE2["segments"]) + len(_ROUTE2["vias"]))
    assert on_disk.count(b"\n") == on_disk.count(b"\r\n")
    assert on_disk.count(b"\r\n") == _PRISTINE_CRLF.count("\r\n") + added
    assert b"(segment\r\n" in on_disk and b"(via buried\r\n" in on_disk
    # 对照：默认 text 模式读回 → 已归一为 LF，auto 只能给 LF（不凭空造 CRLF）
    norm = pcb.read_text(encoding="utf-8")
    assert "\r" not in norm
    assert board_writer.dominant_eol(norm) == "\n"


def test_apply_routes_crlf_keeps_trailing_whitespace_verbatim():
    """尾随空白（原样保留）在 CRLF 模式下逐字节不变。"""
    src = _PRISTINE_CRLF + "\r\n\r\n  "
    tail = src[len(src.rstrip()):]          # "\r\n\r\n\r\n  "
    out = board_writer.apply_routes(src, [_ROUTE], eol="auto")
    assert out.endswith(")" + tail)
    assert out[:out.index(_NODE_CRLF)] == src.rstrip()[:-1]
    assert _no_bare_eol(out)


# ---- 3. auto：LF 板给 LF、无换行不崩 ----------------------------------------
def test_apply_routes_auto_on_lf_board_is_lf_and_equals_default():
    auto = board_writer.apply_routes(_PRISTINE_LF, [_ROUTE], eol="auto")
    assert auto == _APPLIED_LF
    assert "\r" not in auto
    assert auto == board_writer.apply_routes(_PRISTINE_LF, [_ROUTE])


def test_apply_routes_auto_on_input_without_any_newline():
    src = '(kicad_pcb (net 0 "") (net 1 "N1"))'
    out = board_writer.apply_routes(src, [_ROUTE], eol="auto")
    assert "\r" not in out
    assert out.endswith(")")
    assert out.startswith('(kicad_pcb (net 0 "") (net 1 "N1")')
    assert _NODE_LF in out


def test_apply_routes_auto_majority_lf_with_stray_crlf_untouched():
    """LF 占多数的混合板：auto 取 LF，且 pristine 内既有 CRLF 原样保留。"""
    src = ('(kicad_pcb\n'
           '\t(net 0 "")\r\n'
           '\t(net 1 "N1")\n'
           "\t(gr_rect (start 0 0) (end 1 1) (layer \"Edge.Cuts\")\n"
           ")\n")
    out = board_writer.apply_routes(src, [_ROUTE], eol="auto")
    assert out.count("\r\n") == 1
    assert out.startswith(src.rstrip()[:-1])
    assert out.replace(_NODE_LF, "", 1) == src


def test_apply_routes_auto_majority_crlf_with_stray_lf():
    """CRLF 占多数的混合板：auto 取 CRLF（新节点不再引入裸 LF）。"""
    src = ('(kicad_pcb\r\n'
           '\t(net 0 "")\r\n'
           '\t(net 1 "N1")\r\n'
           "\t(gr_rect (start 0 0) (end 1 1) (layer \"Edge.Cuts\"))\n"
           ")\r\n")
    assert board_writer.dominant_eol(src) == "\r\n"
    out = board_writer.apply_routes(src, [_ROUTE], eol="auto")
    assert out.startswith(src.rstrip()[:-1])
    assert out.replace(_NODE_CRLF, "", 1) == src
    # 新节点无裸 LF：裸 LF 净增量 = 0（pristine 自带的那 1 个原样留着）
    assert out.count("\n") - out.count("\r\n") == \
        src.count("\n") - src.count("\r\n") == 1


# ---- 4. dominant_eol 工具 ---------------------------------------------------
def test_dominant_eol_counts():
    assert board_writer.dominant_eol("") == "\n"
    assert board_writer.dominant_eol("abc") == "\n"
    assert board_writer.dominant_eol("a\nb\nc") == "\n"
    assert board_writer.dominant_eol("a\r\nb\r\nc\r\n") == "\r\n"
    assert board_writer.dominant_eol("a\r\nb\r\nc\n") == "\r\n"  # 2:1
    assert board_writer.dominant_eol("a\nb\nc\r\n") == "\n"      # 2:1
    assert board_writer.dominant_eol("a\r\nb\n") == "\n"         # 平票 → LF
    assert board_writer.dominant_eol("a\rb\r") == "\n"           # 裸 CR 不计


def test_dominant_eol_matches_real_revc_shape():
    """真实板形态：纯 CRLF pristine（17986 行）→ CRLF；LF-only 板 → LF。"""
    assert board_writer.dominant_eol(_PRISTINE_CRLF) == "\r\n"
    assert board_writer.dominant_eol(_PRISTINE_LF) == "\n"
    assert board_writer.dominant_eol(_APPLIED_LF) == "\n"


# ---- 5. 结构守卫与非法 eol 仍然失败关闭 -------------------------------------
def test_apply_routes_structure_guard_unchanged():
    truncated = '(kicad_pcb\n\t(version 20260206)\n\t(net 0 ""'
    with pytest.raises(ValueError):
        board_writer.apply_routes(truncated, [_ROUTE])
    with pytest.raises(ValueError):
        board_writer.apply_routes(truncated, [_ROUTE], eol="\r\n")
    with pytest.raises(ValueError):
        board_writer.apply_routes("(kicad_pcb\n", [], eol="auto")
    with pytest.raises(ValueError):
        board_writer.apply_routes("", [_ROUTE], eol="\r\n")


def test_apply_routes_rejects_unknown_eol():
    for bad in ("AUTO", "auto ", "\r", ""):
        with pytest.raises(ValueError):
            board_writer.apply_routes(_PRISTINE_LF, [_ROUTE], eol=bad)
