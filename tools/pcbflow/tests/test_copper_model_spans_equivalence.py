"""R5 —— copper_model 单遍扫描 / 跨度复用入口的**等价性**与契约守卫测试。

背景（R5 任务书 §6 第 1 条）：`parse_copper` 内部原先做 4 次逐 tag 全量扫描
（`top_level_copper_nodes`）+ 1 次全量普查（`_scan_all_top_level`）+ 1 次
`_balanced`，Rev-C 单次实测 ≈1.43 s，导致补丁单轮 ≈4.4 s。R5 新增
`scan_copper` / `parse_copper_scan` / `iter_copper_nodes` 三个入口（以及把既有
入口内部改为单遍），**硬要求**是产出与既有 `parse_copper` 完全等价。

本文件钉死：
1. 单遍扫描的 census 与 `board_writer._top_level_nodes` 原语**逐 tag 跨度相同**
   （真实 Rev-C + 合成板 + KiCad5 语料 + 定种模糊）；
2. `parse_copper_scan(text, scan_copper(text))` 与 `parse_copper(text)` **逐字节
   等价**：copper_sha256、identity_map（含键序）、counts、unrepresentable、
   identity_disambiguated 全同 —— 用「不排序的 json dumps」整份比对，键序也钉死；
3. **改动前**实现产出的 golden 摘要（`_GOLDEN`，由改动前的实现离线算出并冻结在
   本文件里）在改动后仍逐字节复现 —— 这是「既有 parse_copper 语义未变」的直接
   证据，而不是"只看新老入口互相一致"；
4. 既有函数签名不变（`parse_copper` / `parse_copper_file` / `top_level_copper_nodes`
   仍是单参数）；
5. 扫描次数形状：`parse_copper` 与 `top_level_copper_nodes` 各自**只做一次**全量扫描
   （用 monkeypatch 计数，确定性断言，不依赖计时）；
6. 跨文本复用 scan 必须 fail-closed（ValueError），不得静默错位。

只读约束：真实板以 `open(..., encoding="utf-8", newline="")` 读取，绝不写板。
"""

import glob
import hashlib
import inspect
import json
import os
import random

import pytest

import revc_board_fixture
from pcbflow import board_writer as bw
from pcbflow import config
from pcbflow import copper_model as cm

# --------------------------------------------------------------- 合成板文本

#: 覆盖全部节点类：segment（含共享 uuid / 无 uuid 回退）、via、zone（轮廓 +
#: 填充 + 参数）、顶层 arc（unrepresentable）、顶层铜层 gr_line（未识别铜类
#: 节点）、footprint/module（pad 持有者，不报）、非铜层图形节点（不报）。
SYNTH_LF = """(kicad_pcb (version 20260206) (generator "pcbnew")
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
\t\t(uuid "aaaaaaaa-1111-2222-3333-444444444444")
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
\t(footprint "R_0603" (layer "F.Cu")
\t\t(pad "1" smd roundrect (at 0 0) (size 1 1) (layers "F.Cu" "F.Paste" "F.Mask"))
\t)
)
"""

SYNTH_CRLF = SYNTH_LF.replace("\n", "\r\n")

#: KiCad5 口径：无 uuid（几何回退）、无引号 token、tstamp 不作身份、缺 drill 的 via。
SYNTH_KICAD5 = """(kicad_pcb (version 20171130) (host pcbnew "(5.1.12)-1")
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

#: 对抗性文本：字符串里的括号/转义引号（不得影响深度）、空 tag 节点、
#: 顶层 arc、顶层铜层 gr_line、module（KiCad5 footprint）内 pad 铜。
SYNTH_ADVERSARIAL = """(kicad_pcb (version 20260206) (generator "pcbflow")
\t(gr_text "paren ( in string" (at 1 2) (layer "F.SilkS"))
\t(gr_text "esc \\" quote ) and ( paren" (at 3 4) (layer "F.SilkS"))
\t(module "KiCad5Foot" (layer F.Cu)
\t\t(pad 1 smd rect (at 0 0) (size 1 1) (layers F.Cu F.Paste F.Mask))
\t)
\t(gr_line
\t\t(start 0 0) (end 5 5) (layer "F.Cu") (width 0.2)
\t)
\t(arc
\t\t(start 1 1) (mid 2 2) (end 3 1) (width 0.2)
\t\t(layer "F.Cu")
\t\t(net "N7")
\t)
\t(segment
\t\t(start 1.1234567 2.0000004)
\t\t(end 3 4)
\t\t(width 0.1979)
\t\t(layer "In1.Cu")
\t\t(net "N7")
\t\t(uuid "eeeeeeee-1111-2222-3333-444444444444")
\t)
\t(segment
\t\t(start 1.1234567 2.0000004)
\t\t(end 3 4)
\t\t(width 0.1979)
\t\t(layer "In1.Cu")
\t\t(net "N7")
\t\t(uuid "eeeeeeee-1111-2222-3333-444444444444")
\t)
\t(segment
\t\t(start 9 9)
\t\t(end 9 8)
\t\t(width 0.25)
\t\t(layer F.Cu)
\t\t(net 3)
\t)
)
"""

#: 括号不平衡：parse_copper 必须拒绝部分解析（返回空对象 + board_parse_error）。
SYNTH_UNBALANCED = '(kicad_pcb (segment (start 1 2) (end 3 4)'

#: 空板。
SYNTH_EMPTY = "(kicad_pcb (version 1))\n"

#: 未闭合字符串：`_balanced` 与单遍扫描必须同为"不平衡"。
SYNTH_UNCLOSED_STR = '(kicad_pcb (gr_text "never closed (segment (start 1 2))'

SYNTH_BOARDS = (
    ("synth_lf", SYNTH_LF),
    ("synth_crlf", SYNTH_CRLF),
    ("synth_kicad5", SYNTH_KICAD5),
    ("synth_adversarial", SYNTH_ADVERSARIAL),
)


def _edge_texts():
    """病态/边界文本（含不平衡与未闭合字符串），用于差分与 fail-closed 断言。"""
    return [
        ("unbalanced", SYNTH_UNBALANCED),
        ("empty", SYNTH_EMPTY),
        ("unclosed_str", SYNTH_UNCLOSED_STR),
        ("empty_str", ""),
        ("bare_close", ")"),
        ("bare_open", "("),
        ("empty_node", "(kicad_pcb (segment))"),
        ("escaped_quote", '(kicad_pcb (gr_text "a\\\\(b"))'),
        ("unmatched_in_str", '(kicad_pcb ("\\\n)(via)'),
        ("no_root", "(segment (start 1 2) (end 3 4) (width 0.1) "
                    '(layer "F.Cu") (net "N1"))'),
        ("deep_nest", "(kicad_pcb " + "(a " * 30 + ")" * 30 + ")"),
        ("crlf_only", "\r\n\r\n"),
    ]


# --------------------------------------------------------------- 语料与真实板

def _corpus_boards(limit=3):
    pat = os.path.join(config.PCBFLOW_ROOT, "datasets", "pcbench-r1", "raw",
                       "*", "raw.kicad_pcb")
    out = []
    for path in sorted(glob.glob(pat))[:limit]:
        with open(path, encoding="utf-8", newline="") as f:
            out.append((os.path.basename(os.path.dirname(path)), f.read()))
    return out


def _read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def _revc_text():
    if "t" not in _CACHE:
        _CACHE["t"] = _read(config.REVC_BOARD)
    return _CACHE["t"]


_CACHE = {}


def _pin_fixture_board(monkeypatch):
    """REPAIR-P1 W-5（铜环案 R4 三步法②）：钉仓内冻结夹具板
    （与 2026-09-11 live 板 dbfea089 逐字节同，sha 锚 fail-closed），
    并清 _CACHE（防先前用 live 板预热 _revc_text/_all_boards 串板）。"""
    monkeypatch.setattr(config, "REVC_BOARD", revc_board_fixture.fixture_board())
    _CACHE.clear()


def _live_board_text():
    """R4③：显式取 live 板文本（清缓存，防钉板用例预热串板）。"""
    _CACHE.clear()
    return _revc_text()


def _all_boards():
    """(name, text)：合成板 + KiCad5 语料 + 真实 Rev-C（不存在则跳过）。"""
    if "boards" not in _CACHE:
        boards = list(SYNTH_BOARDS)
        for name, text in _corpus_boards():
            boards.append(("corpus:" + name, text))
        if os.path.exists(config.REVC_BOARD):
            boards.append(("revc", _revc_text()))
        _CACHE["boards"] = boards
    return _CACHE["boards"]


# --------------------------------------------------- golden（改动前冻结摘要）

#: 由**改动前**的 `pcbflow/copper_model.py`（sha256 130370a4fc1576ad…，2026-09-11
#: 07:10:23，31825 B）离线算出并冻结：
#:   model         = sha256(json.dumps(parse_copper(text), ensure_ascii=False))
#:                   —— 不排序键，故**键序亦被钉死**
#:   spans         = sha256(repr(top_level_copper_nodes(text)))
#:   identity_head = [identity_map 的键序（前 8 个）]
#: 这些常量是"改动前 ⇄ 改动后逐字节等价"的独立证据：任何语义漂移（值、键序、
#: 排序、unrepresentable 文案、span 偏移）都会让摘要变化。
#: 语料板（datasets/pcbench-r1）不入 golden —— 其目录集合会被并行会话改动，
#: 冻结摘要会因无关原因失效；语料板走等价性与原语比对（见下）。
_GOLDEN = {
    "synth_lf": {
        "model": "c018c01529a259829ff224171378c4e898b3a83fa512763aa42ae0a955e8de6c",
        "spans": "08ae768af2bb346f6789dabf109add5a61e57ca0d1dd6b75c9b39a6347749652",
        "identity_head": [
            "G:388e6903da768b91",
            "aaaaaaaa-1111-2222-3333-444444444444@35e347d2b3b1",
            "aaaaaaaa-1111-2222-3333-444444444444@f95182984284",
            "cccccccc-1111-2222-3333-444444444444",
            "dddddddd-1111-2222-3333-444444444444",
        ],
    },
    "synth_crlf": {
        "model": "5d77d6d56dd24eb200e04071cfedb2faa535d6773f99401d2cd5190b299b6b0b",
        "spans": "00b7de39cac25103866d85c356ebd608d21b05b335d41eb85993515ba5e75725",
        "identity_head": [
            "G:388e6903da768b91",
            "aaaaaaaa-1111-2222-3333-444444444444@35e347d2b3b1",
            "aaaaaaaa-1111-2222-3333-444444444444@f95182984284",
            "cccccccc-1111-2222-3333-444444444444",
            "dddddddd-1111-2222-3333-444444444444",
        ],
    },
    "synth_kicad5": {
        "model": "b651920bbeac6758adc26d7574bdd6568aa2fe3995770e3a4b1fab7e225f657e",
        "spans": "ba3af1095a65b1a615ca6e2f1afd18eaa9b41a7d21eb4285bc65c5a032034ea8",
        "identity_head": [
            "G:1380171eb74279db", "G:9ca414edb09f28ff",
            "G:dfbd5853a054f205", "G:e49c20d59e749687",
        ],
    },
    "synth_adversarial": {
        "model": "5d8d4c47b07a6bd1c4c221214c7211dccd90769417ea91cf658c6ac0757d44a8",
        "spans": "030286dd7ae54b3ed2de1aaee31a8086806f0dca0cced00135845b2655ff73d2",
        "identity_head": [
            "G:d749a22f0c7def09",
            "eeeeeeee-1111-2222-3333-444444444444@b6aa198559f1",
        ],
    },
    "revc": {
        # M1 刷新：APPLY-1 落线后 dbfea089 板实测重冻结，2026-09-11
        # （model=当前实现 parse_copper 整模型 sha256；spans=顶层铜箔跨度
        # repr sha256；identity_head 前 8 键实测未变）
        # REPAIR-P1 W-5：板输入钉仓内冻结夹具板（与该板逐字节同），
        # 本组 golden 值原样保留。
        "model": "eb9712799a2a996007a5a7014ac1b860e414759f0b96c54b04587dc09a2355df",
        "spans": "97625658381eb0e0d1067b315a6448122f78a6f666e15e46435a1e812a222f57",
        "identity_head": [
            "0006d0f8-b913-40ab-91a0-4a423158b30a",
            "00250a99-f979-4fe9-bef1-c143aef34a4b",
            "0032e363-3df1-4fc0-a58b-7afed40ccba6",
            "004cc362-0464-4046-9b51-1d2bf1a6e1fb",
            "00668761-b81b-4cd2-865f-54826f11d635",
            "0067c1c9-d872-4172-b6ca-200cc3495b73",
            "0072c152-cc19-4c1d-8fe0-2c3176bfc365",
            "007352a8-e489-4066-81ba-1a6c0b2c194b",
        ],
    },
}


def _model_digest(text):
    r = cm.parse_copper(text)
    blob = json.dumps(r, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _spans_digest(text):
    return hashlib.sha256(
        repr(cm.top_level_copper_nodes(text)).encode("utf-8")).hexdigest()


def _identity_head(text, n=8):
    return list(cm.parse_copper(text)["identity_map"])[:n]


# ------------------------------------------- 改动前实现的**逐字副本**（差分基准）

def _legacy_census(text):
    """改动前 `copper_model._scan_all_top_level` 的逐字副本（差分基准）。

    仅作测试内基准，不参与生产路径；用于证明新的单遍扫描在**任意**输入
    （含不平衡文本）上产出与改动前完全相同的普查结果。
    """
    out = []
    depth = 0
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == '"':
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == '"':
                    break
                i += 1
        elif c == "(":
            depth += 1
            if depth == 2:
                j = i + 1
                while j < n and text[j] not in " \t\r\n()":
                    j += 1
                tag = text[i + 1:j]
                k, d, instr = j, 1, False
                while k < n and d > 0:
                    ch = text[k]
                    if instr:
                        if ch == "\\":
                            k += 2
                            continue
                        if ch == '"':
                            instr = False
                    elif ch == '"':
                        instr = True
                    elif ch == "(":
                        d += 1
                    elif ch == ")":
                        d -= 1
                    k += 1
                out.append((tag, i, k))
                depth -= 1
                i = k
                continue
        elif c == ")":
            depth -= 1
        i += 1
    return out


def _legacy_top_level_copper_nodes(text):
    """改动前 `top_level_copper_nodes` 的逐字副本（逐 tag 调原语 + 按 start 归并）。

    原语 `board_writer._top_level_nodes` 本轮未被改动，故这是**独立的**历史
    语义基准：新的单遍实现必须对任意输入与之逐项相同。
    """
    out = []
    for tag in cm.COPPER_TOP_TAGS:
        for (s, e) in bw._top_level_nodes(text, tag):
            out.append((tag, s, e))
    out.sort(key=lambda t: t[1])
    return out


def _legacy_balanced(text):
    """改动前 `copper_model._balanced` 的逐字副本（差分基准）。"""
    depth = 0
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == '"':
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == '"':
                    break
                i += 1
            else:
                return False
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth < 0:
                return False
        i += 1
    return depth == 0


def _legacy_parse_copper(text):
    """改动前 `parse_copper` 的**逐字副本**（差分基准，只用于测试对照）。

    与改动前唯一的形式差别：`top_level_copper_nodes` / `_unknown_top_nodes`
    改成调用本文件的 `_legacy_*` 基准实现（原语与逐 tag 走法未变）。
    全部子解析器（`_parse_segment` / `_parse_via` / `_parse_zone` /
    `_zone_fill` / `_zone_params` / `_assemble`）本轮**未被改动**，直接复用。
    """
    if not isinstance(text, str):
        raise ValueError("board_text: 不是字符串")
    unrep = []
    if not _legacy_balanced(text):
        unrep.append({
            "kind": "board_parse_error",
            "where": "board",
            "reason": "括号/双引号不平衡：拒绝部分解析（字节跨度不可信，"
                      "补丁引擎不得据此定位）",
        })
        return cm._assemble([], [], [], unrep)

    for ordinal, (tag, s, e) in enumerate(
            [n for n in _legacy_census(text)
             if n[0] not in cm.COPPER_TOP_TAGS]):
        if tag in cm._PAD_HOLDER_TAGS:
            continue
        layers = cm._declared_layers_text(text[s:e])
        if any(cm._is_copper_layer(l) for l in layers):
            unrep.append({
                "kind": "unrecognized_copper_node",
                "where": "%s#%d@%d" % (tag, ordinal, s),
                "reason": "顶层 %r 节点声明铜层 %s，但 P1a 合同只表达 "
                          "segment/via/zone/arc" % (tag, layers),
            })

    segments, vias, zones = [], [], []
    for ordinal, (tag, s, e) in enumerate(
            _legacy_top_level_copper_nodes(text)):
        where = "%s#%d@%d" % (tag, ordinal, s)
        node_text = text[s:e]
        if not cm._balanced(node_text):
            unrep.append({"kind": "%s_malformed" % tag, "where": where,
                          "reason": "节点括号不平衡"})
            continue
        if tag == "arc":
            unrep.append({
                "kind": "arc_track", "where": where,
                "reason": "顶层 (arc ...) 走线：P1a 铜箔合同无弧段表达"
                          "（不可近似为 segment，拒绝静默丢失）",
            })
            continue
        try:
            parsed = cm.sexpr_min.parse(node_text)
        except cm.sexpr_min.SexprError as exc:
            unrep.append({"kind": "%s_malformed" % tag, "where": where,
                          "reason": "s-expr 解析失败: %s" % exc})
            continue
        if len(parsed) != 1 or not isinstance(parsed[0], list):
            unrep.append({"kind": "%s_malformed" % tag, "where": where,
                          "reason": "节点形状非法（非单一列表）"})
            continue
        node = parsed[0]
        if tag == "segment":
            entry, reason = cm._parse_segment(node)
            if entry is None:
                unrep.append({"kind": "segment_malformed", "where": where,
                              "reason": reason})
                continue
            entry["_span"] = (s, e)
            segments.append(entry)
        elif tag == "via":
            entry, reason = cm._parse_via(node)
            if entry is None:
                unrep.append({"kind": "via_malformed", "where": where,
                              "reason": reason})
                continue
            entry["_span"] = (s, e)
            vias.append(entry)
        else:
            entry, outline, reason = cm._parse_zone(node)
            if entry is None:
                unrep.append({
                    "kind": "zone_no_outline" if "轮廓" in reason
                    else "zone_malformed",
                    "where": where, "reason": reason})
                continue
            points, fill_sha = cm._zone_fill(node)
            entry["outline_mm"] = outline
            entry["fill_points"] = points
            entry["fill_sha256"] = fill_sha
            entry["params"] = cm._zone_params(node)
            entry["_span"] = (s, e)
            zones.append(entry)
    return cm._assemble(segments, vias, zones, unrep)


# ------------------------------------------------------------------ 等价性

def test_scan_copper_spans_match_board_writer_primitive():
    """单遍扫描的铜箔跨度 == 逐 tag 调 `board_writer._top_level_nodes`（原语）。"""
    for name, text in _all_boards():
        scan = cm.scan_copper(text)
        assert scan.balanced is True, name
        for tag in cm.COPPER_TOP_TAGS:
            want = sorted((tag, s, e) for (s, e) in bw._top_level_nodes(text, tag))
            got = sorted(n for n in scan.copper_spans if n[0] == tag)
            assert got == want, (name, tag)
        # 合并序 == 文档序 == 按 start 排序（既有 top_level_copper_nodes 口径）
        assert scan.copper_spans == sorted(scan.copper_spans, key=lambda t: t[1])
        assert cm.top_level_copper_nodes(text) == scan.copper_spans, name


def test_top_level_copper_nodes_equals_legacy_on_all_inputs():
    """冻结入口：对**任意**输入与改动前的逐 tag 实现逐项相同（含不平衡文本）。"""
    texts = list(_all_boards()) + _edge_texts() + [
        (str(i), t) for i, t in enumerate(_fuzz_texts())]
    bad = []
    for name, text in texts:
        got = cm.top_level_copper_nodes(text)
        want = _legacy_top_level_copper_nodes(text)
        if got != want:
            bad.append((name, got[:3], want[:3]))
    assert not bad, bad


def test_census_equals_legacy_census_on_all_inputs():
    """单遍普查（`_scan_all_top_level`）与改动前逐字实现相同（含不平衡文本）。"""
    for name, text in list(_all_boards()) + _edge_texts():
        assert cm._scan_all_top_level(text) == _legacy_census(text), name
    for text in _fuzz_texts(n=160, seed=99):
        assert cm._scan_all_top_level(text) == _legacy_census(text), \
            repr(text[:120])


def test_balanced_flag_equals_legacy_on_all_inputs():
    """单遍扫描的平衡判定与改动前 `_balanced` 相同（含未闭合字符串等病态输入）。"""
    for name, text in list(_all_boards()) + _edge_texts():
        assert cm.scan_copper(text).balanced == _legacy_balanced(text), name
    for text in _fuzz_texts(n=200, seed=101):
        assert cm.scan_copper(text).balanced == _legacy_balanced(text), \
            repr(text[:120])
    rng = random.Random(4242)
    alphabet = '()"\\ \tabc\r\n'
    for _ in range(600):
        t = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 40)))
        assert cm.scan_copper(t).balanced == _legacy_balanced(t), repr(t)


def test_scan_census_matches_single_pass_census_and_unknown_filter():
    """`scan.nodes` / `unknown_spans` 与既有普查口径一致。"""
    for name, text in _all_boards() + _edge_texts():
        scan = cm.scan_copper(text)
        census = cm._scan_all_top_level(text)
        assert scan.nodes == census, name
        assert scan.unknown_spans == [n for n in census
                                      if n[0] not in cm.COPPER_TOP_TAGS], name
        assert scan.unknown_spans == cm._unknown_top_nodes(text), name
        assert cm._scan_all_top_level(text) == _legacy_census(text), name


def test_balanced_but_tag_contains_quote_falls_back_to_per_tag():
    """**平衡**文本也可能触发"普查 ⇄ 逐 tag"分歧（tag token 内含 `"`）。

    这类输入上线性引号自动机与普查的迷你扫描对节点边界判断不同：普查会把
    一个节点吞到文末（丢掉其后的 arc/segment），逐 tag 走法不会。冻结入口
    与 `CopperScan.copper_spans` 必须都退回逐 tag 结果。
    """
    hits = []
    for t in _fuzz_texts():
        if not cm._balanced(t):
            continue
        census = [n for n in cm._scan_top_level_nodes(t)
                  if n[0] in cm.COPPER_TOP_TAGS]
        if census != cm._top_level_copper_nodes_per_tag(t):
            hits.append(t)
    assert hits, "fuzz 语料未覆盖『平衡但 tag 含双引号』情形（覆盖缺口）"
    for t in hits[:3]:
        per_tag = cm._top_level_copper_nodes_per_tag(t)
        assert [n[0] for n in per_tag].count("segment") >= 1, repr(t[:120])
        assert cm.top_level_copper_nodes(t) == per_tag, repr(t[:120])
        assert cm.scan_copper(t).copper_spans == per_tag, repr(t[:120])
        assert list(cm.iter_copper_nodes(t)) == per_tag, repr(t[:120])
        assert json.dumps(cm.parse_copper(t), ensure_ascii=False) == \
            json.dumps(_legacy_parse_copper(t), ensure_ascii=False), \
            repr(t[:120])


def test_unbalanced_divergence_is_confined_and_fail_closed():
    """不平衡文本上"普查 ⇄ 逐 tag"确有走法差异，但不得泄漏进任何产出。

    分歧样本：深度 2 的未匹配节点里出现未闭合字符串 —— 普查整段跳过并把
    后续字节吞进该节点的迷你扫描（凭空多出一个 via 跨度），逐 tag 原语
    继续下潜（更保守）。此处钉死：(a) 冻结入口与复用通道都退回逐 tag 结果；
    (b) `parse_copper` 在此类文本上只产出 board_parse_error（不做节点行走）。
    """
    text = '(kicad_pcb ("\\\n)(via)'
    assert cm._balanced(text) is False
    scan = cm.scan_copper(text)
    assert scan.balanced is False
    # 原始普查确实与逐 tag 不同（这正是必须退回的理由，留作回归证据）
    assert scan.nodes == _legacy_census(text) == [('"\\', 11, 16), ('via', 16, 21)]
    assert [n for n in scan.nodes if n[0] in cm.COPPER_TOP_TAGS] == \
        [("via", 16, 21)]
    assert cm._top_level_copper_nodes_per_tag(text) == []
    # (a) 冻结入口 / 复用通道都 == 历史逐 tag 结果
    assert cm.top_level_copper_nodes(text) == scan.copper_spans == []
    assert list(cm.iter_copper_nodes(text)) == []
    assert list(cm.iter_copper_nodes(text, scan)) == []
    # (b) 模型层面不可观测：只有 board_parse_error，没有任何对象
    for r in (cm.parse_copper(text), cm.parse_copper_scan(text, scan)):
        assert [u["kind"] for u in r["unrepresentable"]] == ["board_parse_error"]
        assert r["counts"] == {"segments": 0, "vias": 0, "zones": 0}
        assert r["identity_map"] == {}


def test_scan_balanced_flag_equals_balanced_helper():
    cases = [SYNTH_LF, SYNTH_CRLF, SYNTH_KICAD5, SYNTH_ADVERSARIAL,
             "(kicad_pcb)", "", ")", "(", "(kicad_pcb (segment))",
             '(kicad_pcb (gr_text "a\\\\(b"))'] + \
        [t for _n, t in _edge_texts()]
    for text in cases:
        assert cm.scan_copper(text).balanced == cm._balanced(text), repr(text[:40])
        assert cm.scan_copper(text).balanced == _legacy_balanced(text), \
            repr(text[:40])
    for name, text in _all_boards():
        assert cm.scan_copper(text).balanced is True, name


def test_parse_copper_scan_is_byte_equivalent_to_parse_copper():
    """新入口 ⇄ 既有入口：整份 json（不排序键，故键序在内）逐字节相同。"""
    for name, text in _all_boards() + _edge_texts():
        old = cm.parse_copper(text)
        scan = cm.scan_copper(text)
        new = cm.parse_copper_scan(text, scan)
        assert list(new.keys()) == list(old.keys()), name
        assert json.dumps(new, ensure_ascii=False) == \
            json.dumps(old, ensure_ascii=False), name
        assert new["copper_sha256"] == old["copper_sha256"], name
        assert list(new["identity_map"].items()) == \
            list(old["identity_map"].items()), name
        assert new["counts"] == old["counts"], name
        assert new["unrepresentable"] == old["unrepresentable"], name
        assert new["identity_disambiguated"] == old["identity_disambiguated"], name
        assert new["identity_basis"] == old["identity_basis"], name
        # parse_copper_scan(text) 不传 scan 时自建扫描，结果同样等价
        assert json.dumps(cm.parse_copper_scan(text), ensure_ascii=False) == \
            json.dumps(old, ensure_ascii=False), name


def test_parse_copper_equals_legacy_implementation():
    """改动入口 ⇄ 改动前 `parse_copper` 逐字副本：整份 json 逐字节相同。

    覆盖：5 块 golden 板 + 语料板 + 病态边界 + 400 例定种模糊（含
    "平衡但 tag 含双引号"与不平衡样本，即两条兜底路径都会被走到）。
    """
    texts = list(_all_boards()) + _edge_texts() + [
        (str(i), t) for i, t in enumerate(_fuzz_texts(n=240, seed=31337))]
    bad = []
    for name, text in texts:
        want = json.dumps(_legacy_parse_copper(text), ensure_ascii=False)
        got = json.dumps(cm.parse_copper(text), ensure_ascii=False)
        if got != want:
            bad.append(name)
            continue
        scan = cm.scan_copper(text)
        via_scan = json.dumps(cm.parse_copper_scan(text, scan),
                              ensure_ascii=False)
        if via_scan != want:
            bad.append("scan:" + name)
    assert not bad, bad[:5]
    # 确认样本确实覆盖了两条兜底路径（否则本测试的证据力不足）
    fallback = 0
    for _n, text in texts:
        nodes = cm._scan_top_level_nodes(text)
        census = [x for x in nodes if x[0] in cm.COPPER_TOP_TAGS]
        if census != cm._top_level_copper_nodes_per_tag(text):
            fallback += 1
    assert fallback >= 1, "未覆盖兜底路径"


def test_iter_copper_nodes_yields_same_spans():
    for name, text in _all_boards():
        scan = cm.scan_copper(text)
        assert list(cm.iter_copper_nodes(text)) == scan.copper_spans, name
        assert list(cm.iter_copper_nodes(text, scan)) == scan.copper_spans, name
        for (tag, s, e) in cm.iter_copper_nodes(text, scan):
            node = text[s:e]
            assert node.startswith("(" + tag), (name, tag)
            assert node.count("(") == node.count(")"), (name, tag)


def test_scan_reuse_fails_closed_on_text_mismatch():
    scan = cm.scan_copper(SYNTH_LF)
    with pytest.raises(ValueError):
        cm.parse_copper_scan(SYNTH_LF.replace("N1", "N9"), scan)
    with pytest.raises(ValueError):
        list(cm.iter_copper_nodes(SYNTH_LF + "\n", scan))
    with pytest.raises(ValueError):
        cm.parse_copper_scan(SYNTH_LF, ["not-a-scan"])
    # 同一文本（值相等即可，不要求同一对象）→ 放行且结果等价
    same = "".join([SYNTH_LF[:10], SYNTH_LF[10:]])
    assert same == SYNTH_LF and same is not SYNTH_LF
    assert cm.parse_copper_scan(same, scan)["copper_sha256"] == \
        cm.parse_copper(SYNTH_LF)["copper_sha256"]


def test_new_entries_reject_non_str():
    for fn in (cm.scan_copper, cm.parse_copper_scan,
               cm.parse_copper, cm.parse_copper_file):
        with pytest.raises((ValueError, TypeError)):
            fn(None)


def test_existing_signatures_unchanged():
    """R5 硬约束：既有入口签名不得改（新能力只走新入口）。"""
    for fn in (cm.parse_copper, cm.parse_copper_file,
               cm.top_level_copper_nodes):
        params = list(inspect.signature(fn).parameters.values())
        assert [p.name for p in params] == ["board_text"] or \
            [p.name for p in params] == ["path"], fn.__name__
        assert all(p.default is inspect.Parameter.empty for p in params), \
            fn.__name__
        assert all(p.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
                   for p in params), fn.__name__
    # 新入口是可选的额外通道
    assert list(inspect.signature(cm.parse_copper_scan).parameters) == \
        ["board_text", "scan"]
    assert list(inspect.signature(cm.iter_copper_nodes).parameters) == \
        ["board_text", "scan"]
    assert list(inspect.signature(cm.scan_copper).parameters) == ["board_text"]


# ------------------------------------------------- 扫描次数（确定性性能形状）

def test_parse_copper_does_one_full_scan(monkeypatch):
    """parse_copper 只做**一次**节点扫描（原先 4 次逐 tag 扫描 + 1 次普查）。"""
    calls = {"n": 0}
    real = cm._scan_top_level_nodes

    def counted(text):
        calls["n"] += 1
        return real(text)

    monkeypatch.setattr(cm, "_scan_top_level_nodes", counted)
    cm.parse_copper(SYNTH_LF)
    assert calls["n"] == 1
    calls["n"] = 0
    cm.top_level_copper_nodes(SYNTH_LF)
    assert calls["n"] == 1
    calls["n"] = 0
    scan = cm.scan_copper(SYNTH_LF)
    assert calls["n"] == 1
    calls["n"] = 0
    cm.parse_copper_scan(SYNTH_LF, scan)
    assert calls["n"] == 0          # 复用：零额外扫描
    calls["n"] = 0
    list(cm.iter_copper_nodes(SYNTH_LF, scan))
    assert calls["n"] == 0          # 复用：零额外扫描


def test_balanced_check_is_not_fused_into_the_scan():
    """平衡判定必须仍走未被改动的 `_balanced`（不融进扫描循环）。

    反例（`evil` 常量）：tag token 内含双引号、正文内含连续三个双引号 ——
    迷你扫描从 `"` 起吞掉后半段文本，线性引号自动机则按引号开合继续计数，
    两者对同一文本给出**相反**的平衡结论。融合实现会把它判成不平衡，
    `_balanced` 判成平衡。本测试钉死"仍用独立线性检查"。
    """
    evil = '(b\n(a"\n\tb' + '"""' + 'a)\r\t\r(c)\\)'
    assert _legacy_balanced(evil) is True
    assert cm._balanced(evil) is True
    assert cm.scan_copper(evil).balanced is True
    # 融合式判定的错误结论（留作反例证据：单遍普查会把后半段吞进迷你扫描）
    assert _legacy_census(evil) != [] and cm.scan_copper(evil).nodes == \
        _legacy_census(evil)
    # 真正的不平衡仍被识别
    for t in (SYNTH_UNBALANCED, SYNTH_UNCLOSED_STR, ")", "("):
        assert cm.scan_copper(t).balanced is False, repr(t)

    calls = {"n": 0}
    real = cm._balanced

    def counted(text):
        calls["n"] += 1
        return real(text)

    cm._balanced = counted
    try:
        cm.scan_copper(SYNTH_LF)
    finally:
        cm._balanced = real
    assert calls["n"] == 1          # 恰好一次独立线性检查


def test_one_scan_serves_parse_and_patch_style_node_walk():
    """copper_patch._build_pieces 式用法：一次扫描同时喂解析与节点遍历。"""
    text = SYNTH_LF
    scan = cm.scan_copper(text)
    model = cm.parse_copper_scan(text, scan)
    spans = [(tag, s, e) for (tag, s, e) in cm.iter_copper_nodes(text, scan)]
    assert model["counts"] == {"segments": 3, "vias": 1, "zones": 1}
    # 遍历出的跨度可直接切出节点字节（补丁引擎定位口径）
    for (_tag, s, e) in spans:
        assert text[s:e].startswith("(")
        assert text[s:e].count("(") == text[s:e].count(")")
    # 解析出的对象数 == 铜箔跨度数（本板无 arc，故无额外的 unrepresentable 跨度）
    assert len(spans) == sum(model["counts"].values()) == 5
    # 补丁引擎用 identity_map 的 span 定位：必须落在同一组跨度上
    assert sorted(tuple(rec["span"]) for rec in model["identity_map"].values()) \
        == sorted((s, e) for (_t, s, e) in spans)


# ------------------------------------------------------------------ golden

def test_golden_model_digest_frozen_from_pre_change_implementation(monkeypatch):
    """改动前实现的整份模型摘要必须逐字节复现（语义未变的直接证据）。

    REPAIR-P1 W-5：钉冻结夹具板（"revc" 组 golden=dbfea089 板实测）。
    """
    _pin_fixture_board(monkeypatch)
    boards = dict(_all_boards())
    missing = [n for n in _GOLDEN if n not in boards]
    if missing == ["revc"]:
        pytest.skip("Rev-C board missing")
    assert not missing, "golden 板缺失（不允许静默跳过）：%s" % missing
    for name, rec in sorted(_GOLDEN.items()):
        text = boards[name]
        assert _model_digest(text) == rec["model"], name
        assert _spans_digest(text) == rec["spans"], name
        assert _identity_head(text) == rec["identity_head"], name


def test_scan_path_matches_golden_too(monkeypatch):
    """走扫描复用通道得到的模型同样命中改动前 golden（钉夹具板）。"""
    _pin_fixture_board(monkeypatch)
    boards = dict(_all_boards())
    if "revc" not in boards:
        pytest.skip("Rev-C board missing")
    for name, rec in sorted(_GOLDEN.items()):
        text = boards[name]
        scan = cm.scan_copper(text)
        r = cm.parse_copper_scan(text, scan)
        blob = json.dumps(r, ensure_ascii=False).encode("utf-8")
        assert hashlib.sha256(blob).hexdigest() == rec["model"], name


# ------------------------------------------------------------------- 真实板

_HAS_REVC = os.path.exists(config.REVC_BOARD)
needs_board = pytest.mark.skipif(not _HAS_REVC, reason="Rev-C board missing")


@needs_board
def test_real_board_entries_agree_and_facts_unchanged(monkeypatch):
    _pin_fixture_board(monkeypatch)
    text = _revc_text()
    old = cm.parse_copper(text)
    # M1 刷新：counts/identity_map/copper_sha256=dbfea089 夹具板实测（仅钉板）
    assert old["counts"] == {"segments": 2372, "vias": 358, "zones": 2}
    assert len(old["identity_map"]) == 2732
    assert old["unrepresentable"] == []
    assert old["identity_basis"] == cm.IDENTITY_KICAD_UUID
    assert old["copper_sha256"].startswith("c4a46878")
    assert old["copper_sha256"] == (
        "c4a46878290922d01c02ef3a524a426194a5d8a797f8323e654552f77a6acae2")
    scan = cm.scan_copper(text)
    assert scan.balanced is True
    new = cm.parse_copper_scan(text, scan)
    assert json.dumps(new, ensure_ascii=False) == \
        json.dumps(old, ensure_ascii=False)
    assert list(new["identity_map"]) == list(old["identity_map"])
    assert len(scan.copper_spans) == 2732 + 0        # 2372+358+2，无 arc
    assert len(scan.copper_spans) == len(old["identity_map"])
    for (tag, s, e) in cm.iter_copper_nodes(text, scan):
        assert text[s:e].startswith("(" + tag)
        assert text[s:e].count("(") == text[s:e].count(")")


@needs_board
def test_real_board_spans_match_primitive_per_tag():
    # R4③ live 板不变量（板无关：原语与扫描通道逐 tag 跨度相同）
    text = _live_board_text()
    scan = cm.scan_copper(text)
    for tag in ("segment", "via", "zone", "arc"):
        want = [(tag, s, e) for (s, e) in bw._top_level_nodes(text, tag)]
        got = [n for n in scan.copper_spans if n[0] == tag]
        assert got == want, tag
    assert cm.top_level_copper_nodes(text) == scan.copper_spans


@needs_board
def test_real_board_parse_is_read_only():
    from pcbflow import hashing
    before = hashing.sha256_file(config.REVC_BOARD)
    cm.parse_copper_scan(_revc_text(), cm.scan_copper(_revc_text()))
    assert hashing.sha256_file(config.REVC_BOARD) == before


@needs_board
def test_real_board_live_invariants_only():
    """R4③ live 板不变量用例（REPAIR-P1 W-5）：live 板演进不破坏等价性合同。

    双通道逐字节等价（不排序 json dumps 键序也钉）+守恒+零不可表示，
    不带精确计数/golden 摘要——那些由钉夹具板的用例守护。
    """
    text = _live_board_text()
    scan = cm.scan_copper(text)
    assert scan.balanced is True
    old = cm.parse_copper(text)
    new = cm.parse_copper_scan(text, scan)
    assert json.dumps(new, ensure_ascii=False) == \
        json.dumps(old, ensure_ascii=False)
    assert len(scan.copper_spans) == len(old["identity_map"]) \
        == sum(old["counts"].values())
    assert old["unrepresentable"] == []


def test_negative_control_board_tamper_moves_digest():
    """负对照（R28「不得弱化」硬约束检出证明）：注入一个新 uuid 的 segment
    后整模型摘要必然变化（golden 值在新板内容下不再成立）——golden 确实
    跟踪板字节，钉板没有把它变成恒真。"""
    tampered = revc_board_fixture.duplicate_first_segment(
        revc_board_fixture.fixture_board_text())
    digest = _model_digest(tampered)
    assert digest != _GOLDEN["revc"]["model"]
    assert cm.parse_copper(tampered)["counts"]["segments"] == 2373


# --------------------------------------------------------------------- 模糊

_MUT_FRAGMENTS = (
    "", " ", "\t", "\r\n", "\n", "(", ")", '"', "\\", "(segment", "(via",
    "(zone", "(arc", "(gr_line", "(footprint", "(module", "(net \"N1\")",
    "(start 1 2)", "(end 3 4)", "(width 0.25)", "(layer \"F.Cu\")",
    "(uuid \"aaaaaaaa-1111-2222-3333-444444444444\")", "(pts (xy 0 0))",
    "(polygon (pts (xy 0 0) (xy 1 0) (xy 1 1)))", "(size 0.7)", "(drill 0.4)",
    "(layers \"F.Cu\" \"In2.Cu\")", "(at 1 2)", "(filled_polygon (pts (xy 1 1)))",
    "(gr_text \"a(b)c\")", "(gr_text \"esc \\\" q\")", "( )", "\u4e2d\u6587",
)


def _fuzz_texts(n=240, seed=20260911):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        k = rng.randint(1, 14)
        body = "".join(rng.choice(_MUT_FRAGMENTS) for _ in range(k))
        out.append("(kicad_pcb " + body + ")")
    # 再叠加对真实/合成板的确定性切片扰动
    for base in (SYNTH_LF, SYNTH_KICAD5, SYNTH_ADVERSARIAL):
        for _ in range(40):
            t = base
            for _ in range(rng.randint(1, 3)):
                op = rng.randint(0, 2)
                if not t:
                    break
                p = rng.randrange(len(t))
                if op == 0:
                    t = t[:p] + rng.choice(_MUT_FRAGMENTS) + t[p:]
                elif op == 1:
                    t = t[:p] + t[p + rng.randint(1, 6):]
                else:
                    t = t[:p] + t[p:].replace("\n", "\r\n", 1)
            out.append(t)
    return out


def test_fuzz_scan_equals_census_and_primitive():
    texts = _fuzz_texts()
    assert len(texts) >= 300
    balanced_n = 0
    for text in texts:
        scan = cm.scan_copper(text)
        # 单遍普查 == 改动前逐字普查（任意输入）
        assert scan.nodes == _legacy_census(text), repr(text[:120])
        assert scan.balanced == _legacy_balanced(text), repr(text[:120])
        # 冻结入口 == 改动前逐 tag 实现（任意输入）
        assert cm.top_level_copper_nodes(text) == \
            _legacy_top_level_copper_nodes(text), repr(text[:120])
        if scan.balanced:
            balanced_n += 1
            # 平衡文本上：普查过滤 == 逐 tag 原语（这是 parse_copper 走单遍的根据）
            for tag in cm.COPPER_TOP_TAGS:
                want = sorted((tag, s, e)
                              for (s, e) in bw._top_level_nodes(text, tag))
                got = sorted(n for n in scan.copper_spans if n[0] == tag)
                assert got == want, (tag, repr(text[:120]))
            assert scan.copper_spans == cm.top_level_copper_nodes(text), \
                repr(text[:120])
            # identity_map 的跨度必须落在铜箔跨度集合内（补丁引擎定位前提；
            # arc / malformed 跨度没有身份条目，故只断言包含关系）
            model = cm.parse_copper_scan(text, scan)
            spans = set((s, e) for (_t, s, e) in scan.copper_spans)
            for rec in model["identity_map"].values():
                assert (rec["span"][0], rec["span"][1]) in spans, \
                    repr(text[:120])
    assert balanced_n > 0


def test_fuzz_parse_paths_equivalent():
    for text in _fuzz_texts(n=120, seed=7):
        old = cm.parse_copper(text)
        new = cm.parse_copper_scan(text, cm.scan_copper(text))
        assert json.dumps(new, ensure_ascii=False) == \
            json.dumps(old, ensure_ascii=False), repr(text[:120])
        # 不平衡文本必须 fail-closed（单遍普查的差异不得泄漏进模型）
        if not cm.scan_copper(text).balanced:
            assert [u["kind"] for u in new["unrepresentable"]] == \
                ["board_parse_error"], repr(text[:120])
            assert new["counts"] == {"segments": 0, "vias": 0, "zones": 0}
            assert new["identity_map"] == {}


# ------------------------------------------------------- 守恒（沿用既有口径）

def _kinds(model):
    out = {}
    for u in model["unrepresentable"]:
        out[u["kind"]] = out.get(u["kind"], 0) + 1
    return out


def test_conservation_via_scan_path():
    for name, text in _all_boards():
        scan = cm.scan_copper(text)
        model = cm.parse_copper_scan(text, scan)
        k = _kinds(model)
        assert len(bw._top_level_nodes(text, "segment")) == \
            model["counts"]["segments"] + k.get("segment_malformed", 0), name
        assert len(bw._top_level_nodes(text, "via")) == \
            model["counts"]["vias"] + k.get("via_malformed", 0), name
        assert len(bw._top_level_nodes(text, "zone")) == \
            model["counts"]["zones"] + k.get("zone_no_outline", 0) \
            + k.get("zone_malformed", 0), name
        assert len(bw._top_level_nodes(text, "arc")) == k.get("arc_track", 0), name
