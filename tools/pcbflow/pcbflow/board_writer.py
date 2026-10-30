"""④ FC2：快照副本落板 writer（§10.4 提交纪律的 pcbflow 侧）。

生成器模式：board 文本 → board 文本（纯函数）；落盘由 shell 重定向完成，
且仅允许写入 FC2 workspace 的快照副本（pre/post hash 由编排侧记账）。
语法与 pcbagent SexprWriter 同口径（KiCad 10 net 以名字出现；Rev-C 的
F↔In2 过孔为 (via buried)）。uuid 内容派生（确定性，无随机）。
行尾：默认 LF（历史口径，既有 hash 台账不变）；eol 参数为 opt-in 保真能力
（"auto" 按 pristine 探测主导行尾，供纯 CRLF 板闭环复用，见 dominant_eol）。
"""

from __future__ import annotations

import hashlib

LAYER_FILE_NAME = {0: "F.Cu", 2: "B.Cu", 4: "In1.Cu", 6: "In2.Cu"}

# 允许的行尾（opt-in 保真能力；默认 None/不传参 = 历史 LF 口径）
_LF = "\n"
_CRLF = "\r\n"
_EOL_EXPLICIT = (_LF, _CRLF)


def dominant_eol(text):
    """文本主导行尾探测 → "\\n" | "\\r\\n"（供补丁引擎复用）。

    统计 "\\r\\n" 与裸 "\\n" 的出现次数取多数；两者皆无（或计数平票）→ "\\n"。
    只看行尾，不改写 text 自身字节。

    调用方注意：探测的是**入参文本的字节**。读文件时必须保留换行
    （open(path, encoding="utf-8", newline="")），否则 Python 通用换行翻译
    已把 CRLF 归一成 LF，任何 CRLF 板都会被误判为 LF 板。"""
    crlf = text.count(_CRLF)
    bare_lf = text.count(_LF) - crlf
    return _CRLF if crlf > bare_lf else _LF


def _resolve_eol(text, eol):
    """eol 参数 → 具体行尾串：None=历史默认 LF；"auto"=按 text 探测。"""
    if eol is None:
        return _LF
    if eol == "auto":
        return dominant_eol(text)
    if eol in _EOL_EXPLICIT:
        return eol
    raise ValueError('未知 eol=%r（允许 None / "auto" / "\\n" / "\\r\\n"）'
                     % (eol,))


def _node_lines(eol, lines):
    """节点行列表 → 文本：每行以 eol 收尾（eol="\\n" 时与历史字面量逐字节相同）。"""
    return "".join(line + eol for line in lines)


def route_uuid(route):
    """route dict → 内容 sha256 派生 uuid（同内容同 uuid，确定性去重）。

    hash 输入带 "pcbflow-fc2:" 命名空间前缀（与 pcbagent 派生空间分离）。"""
    h = hashlib.sha256()
    h.update(b"pcbflow-fc2:")
    h.update(route["net"].encode("utf-8"))
    for seg in route["segments"]:
        h.update(("S%d:%.4f,%.4f,%.4f,%.4f;"
                  % (seg[0], seg[1], seg[2], seg[3], seg[4]))
                 .encode("utf-8"))
    for (x, y) in route["vias"]:
        h.update(("V:%.4f,%.4f;" % (x, y)).encode("utf-8"))
    d = h.hexdigest()
    return "-".join((d[:8], d[8:12], d[12:16], d[16:20], d[20:32]))


def nodes_text(route, eol="\n"):
    """单网 route → segment/via s-expr 节点文本（pcbagent 同口径）。

    eol：节点行分隔符（默认 "\\n" = 历史行为）。缩进（"\\t"/"\\t\\t"）、
    数值格式（%.4f 去尾零）、节点顺序均与 eol 无关。"""
    uuid = route.get("uuid") or route_uuid(route)
    out = []
    for (L, x1, y1, x2, y2) in route["segments"]:
        out.append(_node_lines(eol, [
            "\t(segment",
            "\t\t(start %.4f %.4f)" % (x1, y1),
            "\t\t(end %.4f %.4f)" % (x2, y2),
            "\t\t(width %s)" % _num(route["width"]),
            '\t\t(layer "%s")' % LAYER_FILE_NAME[L],
            '\t\t(net "%s")' % route["net"],
            '\t\t(uuid "%s")' % uuid,
            "\t)",
        ]))
    for (x, y) in route["vias"]:
        out.append(_node_lines(eol, [
            "\t(via buried",
            "\t\t(at %.4f %.4f)" % (x, y),
            "\t\t(size %s)" % _num(route["via_size"]),
            "\t\t(drill %s)" % _num(route["via_drill"]),
            '\t\t(layers "F.Cu" "In2.Cu")',
            '\t\t(net "%s")' % route["net"],
            '\t\t(uuid "%s")' % uuid,
            "\t)",
        ]))
    return "".join(out)


def _num(v):
    s = ("%.4f" % float(v)).rstrip("0").rstrip(".")
    return s if s else "0"


def apply_routes(pristine_text, routes, eol=None):
    """pristine 板文本 + route 列表 → 追加 segment/via 后的板文本。

    板文件以 ")" 收尾（s-expr 根闭合）——剥尾追加再合上（pcbagent 同法）。

    eol：新增节点行尾。None（默认）= 历史行为（LF），既有 hash 台账口径不变；
    "auto" = 按 pristine_text 主导行尾（dominant_eol）生成；也接受显式
    "\\n" / "\\r\\n"。只作用于**新增节点**：pristine_text 自身字节（含既有
    行尾与尾随空白）原样保留，插入定位逻辑（剥尾、须以 ")" 收尾）与 eol 无关。
    eol="auto" 要看到 CRLF，pristine_text 须由 newline="" 读出（见
    dominant_eol 调用方注意）。"""
    stripped = pristine_text.rstrip()
    if not stripped.endswith(")"):
        raise ValueError("板文本非预期结尾（缺根闭合括号）")
    tail = pristine_text[len(stripped):]
    node_eol = _resolve_eol(pristine_text, eol)
    body = stripped[:-1] + "".join(nodes_text(r, eol=node_eol)
                                   for r in routes) + ")" + tail
    return body


def _top_level_nodes(text, tag):
    """深度 1 的指定 tag 顶层节点文本段 [(start, end)]（括号平衡扫描）。"""
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
                if text[i + 1:j] == tag:
                    k = j
                    d = 1
                    instr = False
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
                    out.append((i, k))
                    depth -= 1
                    i = k
                    continue
        elif c == ")":
            depth -= 1
        i += 1
    return out


def apply_placement(board_text, placement_rows):
    """③ 重放：按 placement.csv 行 (ref,x,y,rot,…) 改写封装自身 (at)。

    文本级、格式保持：仅替换各目标 footprint 节点内第一个 (at …)；
    未列入 placement 的封装不动；ref 未命中板文件即报错（不静默丢行）。"""
    import re
    want = {r["ref"]: r for r in placement_rows}
    found = set()
    pieces = []
    last = 0
    for (s, e) in _top_level_nodes(board_text, "footprint"):
        node = board_text[s:e]
        mref = re.search(r'\(property "Reference" "([^"]+)"', node)
        ref = mref.group(1) if mref else None
        if ref not in want:
            continue
        found.add(ref)
        row = want[ref]
        m = re.search(r"\(at +(-?[\d.]+) +(-?[\d.]+)(?: +(-?[\d.]+))?\)", node)
        if not m:
            raise ValueError("footprint %s 缺 (at)" % ref)
        new_at = "(at %s %s %s)" % (_num(row["x"]), _num(row["y"]),
                                    _num(row.get("rot") or 0))
        node2 = node[:m.start()] + new_at + node[m.end():]
        pieces.append(board_text[last:s])
        pieces.append(node2)
        last = e
    pieces.append(board_text[last:])
    missing = sorted(set(want) - found)
    if missing:
        raise ValueError("placement refs 未命中板文件: %s" % ",".join(missing))
    return "".join(pieces)
