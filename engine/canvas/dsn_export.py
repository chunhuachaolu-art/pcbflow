# -*- coding: utf-8 -*-
"""canvas.dsn_export —— board.v1 → Specctra DSN 导出器（Lane-DSN；主审裁定
CANVAS-ECOSYSTEM-ADJUDICATION-2026-09-25.md D-2 采纳项，排波 2 收口后落位）。

原型（``freerouting-baseline-r1/dsn_writer/boardjson_to_dsn.py``，另批自研
尽力件）的产品化重写/吸收——非 GPL 污染源吸收（该原型是本仓库生态的
自研脚本）；Freerouting jar 本身 GPLv3，**只许独立进程 ``java -jar`` 调用**
（本模块不含任何进程调用；冒烟驱动独立落在
``out/canvas-toolchain/dsn-lane/smoke/``），零源码拷贝/链接/修改。

映射（继承原型已验证口径）
--------------------------
- stackup 可用 signal 层 → structure.layer（保持 stackup 物理序=层 index）。
- workspace 矩形 → structure.boundary（坐标 um 整数 + y 取反，KiCad 导出器惯例）。
- via_model（drill+2×annular）→ via padstack，class circuit use_via 引用。
- hard_rules R1.floor_mm → rule.width；R5.min_clearance_mm → rule.clearance
  （structure.rule + class rule 双落）。
- 每分区一 image 双 pin（endpoints 定 placement，pad_terminals 定 padstack
  shape/size/layers；rect 以 oval-path 近似=KiCad 导出器惯例，非精确矩形铜）。
- net → network.net（该网全部分区端点 pin，**net 级连通**——DSN 网内 pins
  自由互连，不保 v5 逐分区路由拓扑；语义差异披露不掩盖）。
- wiring 空（未布线板）。

模式与 fail-closed
------------------
- **忠实模式（缺省 ``relaxed=False``）**：无任何放宽。缺 via_model（或
  drill_mm<=0）= :class:`DsnExportError` 显式报错并披露机理（原型实测：
  Freerouting 2.4.1 在 DSN 无任何 via padstack 时布线机器整体停滞，
  badgeleds 忠实版 9/9 未布通、0.00 CPU 秒——直接喂会得到"完全不可布"假象）。
  ``allow_missing_via=True`` 为显式越狱：照实无 via 导出，仅供链路验证
  冒烟（停滞本身是披露的预期结果，不用于对外对比结论）。
- **relaxed 模式（``relaxed=True``，披露语义）**：①缺 via_model 时补标称
  via padstack（drill 0.4mm + annular 0.15mm → pad Ø0.7mm）；②boundary
  外扩 2.0mm（v5 workspace 贴铜包围盒，真实净距规则下边缘焊盘违反 outline
  间距）。板自带真 via_model 时 relaxed 只外扩边界（via 用真值）。
- **board 形态异常不吞**：本件入口先过 ``v5.board.load_board`` 单源校验
  （schema+跨字段+provenance 哈希链；BoardLoadError 是 ValueError 子类），
  再加导出侧语义校验（可用 signal 层空/未知焊盘层引用/零尺寸焊盘/退化
  endpoints/含引号网名/空 partitions 或 nets → ValueError）。

原型已修陷阱的保留（产品化红线）
--------------------------------
- **refdes 连字符陷阱**：DSN ``(pins REF-pin)`` 引用按连字符切分，refdes
  含连字符时解析漂移（表现=全网已连通假象）。本件一切标识符（refdes/
  image/padstack/via 名）只留 ``[A-Za-z0-9_]``，连字符/点号一律下划线化
  （点号同类预防：原型 tmp108 试验 via 名含点曾触发 Freerouting
  ``Library.read_scope: via padstack ... not found`` WARN）；sanitize 撞名
  按首用序确定性后缀去重（保 refdes↔分区 1:1，防连通性张冠李戴）。
- **确定性**：纯函数；无时间戳、无路径渗透（host_cad 固定串）、固定序
  （分区按 partition_id 排序、网按 net_id 排序、padstack 首用序）——
  同输入双跑字节等（canonical）。

载入口径（wrap 件或裸件，参照 canvas/integration.py 的 load_wrapped_board）
---------------------------------------------------------------------------
``load_board_doc(path)`` = ``json.load`` → ``raw["board"]`` 体（裸件=raw
本身）→ ``v5.board.load_board`` 全校验。
"""

import json
import math
import re

from v5 import board as v5board

GENERATOR = "canvas.dsn_export"
VERSION = "1.0.0"

UM = 1000.0                 # mm -> um（DSN resolution um 1）
RELAXED_BOUNDARY_MARGIN_MM = 2.0   # relaxed 边界外扩（披露语义②）
NOMINAL_VIA = {"drill_mm": 0.4, "annular_mm": 0.15}   # relaxed 标称 via（披露语义①）

_STALL_DISCLOSURE = (
    "Freerouting 2.4.1 在 DSN 无任何 via padstack 时布线机器整体停滞"
    "（原型实测 badgeleds 忠实版 9/9 未布通、0.00 CPU 秒——见 "
    "freerouting-baseline-r1/dsn_writer/README.md 机理发现1）")


class DsnExportError(ValueError):
    """DSN 导出 fail-closed 拒绝（via_model 缺失忠实模式等，披露型报错）。"""


# ---------------------------------------------------------------- 载入

def load_board_doc(path):
    """wrap 件或裸件 → 校验后的 board dict（v5.board.load_board 单源）。

    - wrap 件（顶层含 "board"）取体；裸件原样。
    - schema/跨字段/哈希链失败抛 BoardLoadError（ValueError 子类）不吞。
    """
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    board = raw["board"] if isinstance(raw, dict) and "board" in raw else raw
    return v5board.load_board(board)


# ---------------------------------------------------------------- 标识符

def _sanitize(name, maxlen=60):
    """标识符净化：只留 [A-Za-z0-9_]（连字符/点号→下划线——refdes 切分陷阱）。

    空/全符号名回退 "N"；截断到 maxlen。
    """
    s = re.sub(r"[^A-Za-z0-9_]", "_", str(name))
    s = s.strip("_") or "N"
    return s[:maxlen]


def _name_num(v):
    """数字入名：小数点→p、负号→n（名内免点号/连字符）。"""
    s = ("%.1f" % v).rstrip("0").rstrip(".") if abs(v - round(v)) > 1e-9 \
        else str(int(round(v)))
    return s.replace(".", "p").replace("-", "n")


def _fmt(v):
    """um 数值文本：整值整数、否则 1 位小数（确定性格式）。"""
    iv = int(round(v))
    return str(iv) if math.isclose(v, iv, abs_tol=1e-6) else ("%.1f" % v)


def _q(s):
    """DSN 双引号字符串（net 名等；含引号/控制符=形态异常，调用侧已拒）。"""
    return '"%s"' % s


# ---------------------------------------------------------------- 校验

def _signal_layers(board):
    layers = [l["id"] for l in board["stackup"]
              if l.get("available") and l.get("kind") == "signal"]
    if not layers:
        raise ValueError(
            "stackup 无可用 signal 层（available=true 且 kind=signal）——"
            "DSN structure.layer 无从生成（throwing-star-pro 类'无启用铜层族'"
            "板的同症先例见 baseline-r1 REPORT §3）")
    if len(set(layers)) != len(layers):
        raise ValueError("stackup 可用 signal 层 id 重复")
    return layers


def _check_endpoints(part):
    eps = part["geometry"]["endpoints"]
    if not (isinstance(eps, (list, tuple)) and len(eps) == 2
            and all(isinstance(p, (list, tuple)) and len(p) == 2
                    and all(isinstance(c, (int, float))
                            and math.isfinite(c) for c in p) for p in eps)):
        raise ValueError("partitions[%r].geometry.endpoints 形态异常"
                         "（须=2×[有限 x,y]）" % (part.get("partition_id"),))
    if eps[0][0] == eps[1][0] and eps[0][1] == eps[1][1]:
        raise ValueError("partitions[%r].geometry.endpoints 两端点同坐标"
                         "（零跨距退化分区）" % (part.get("partition_id"),))


def _pad_layers(term, layers, pid):
    lay = term.get("layers", "all")
    if lay == "all":
        return tuple(layers)
    ls = [lay] if isinstance(lay, str) else list(lay)
    if not ls:
        raise ValueError("partition %r 焊盘 layers 为空列表" % pid)
    unknown = [l for l in ls if l not in layers]
    if unknown:
        raise ValueError(
            "partition %r 焊盘引用未知/不可用层 %r（可用 signal 层=%r）——"
            "静默改投全层会偷换铜域，fail-closed 拒绝"
            % (pid, unknown, layers))
    return tuple(l for l in layers if l in set(ls))


def _check_pad_terminals(part, layers):
    terms = part["geometry"].get("pad_terminals") or []
    pid = part.get("partition_id")
    for t in terms:
        if any(s <= 0 for s in t["size_mm"]):
            raise ValueError("partition %r 焊盘 size_mm 含非正值 %r"
                             "（零尺寸铜）" % (pid, t["size_mm"]))
        _pad_layers(t, layers, pid)
    return terms


def _check_net_ids(board):
    for n in board["nets"]:
        nid = n["net_id"]
        if not isinstance(nid, str) or not nid:
            raise ValueError("net_id 须为非空字符串，实得 %r" % (nid,))
        if '"' in nid or "\\" in nid or any(ord(c) < 32 for c in nid):
            raise ValueError(
                "net_id %r 含引号/反斜杠/控制符——DSN 字符串引用无法确定性"
                "转义，fail-closed 拒绝" % nid)


# ---------------------------------------------------------------- 导出

def _via_model_effective(board, relaxed, allow_missing_via):
    """→ (via_dict_or_None, disclosures)。忠实缺 via=显式报错（停滞机理）。"""
    vm = board.get("via_model")
    if not (isinstance(vm, dict) and vm.get("drill_mm", 0) > 0):
        vm = None
    if vm is not None:
        return vm, []
    if relaxed:
        return dict(NOMINAL_VIA), ["relaxed: 标称 via padstack "
                                   "(drill 0.4mm + annular 0.15mm → pad Ø0.7mm)"]
    if allow_missing_via:
        return None, ["allow_missing_via: 照实无 via padstack 导出（Freerouting "
                      "整体停滞=披露的预期结果，仅供链路验证）"]
    raise DsnExportError(
        "板 %r 无 via_model（或 drill_mm<=0）：忠实模式拒绝导出——%s。"
        "选择: relaxed=True（披露放宽=标称 via+边界外扩 2mm）或 "
        "allow_missing_via=True（照实导出，冒烟专用）"
        % (board.get("board_id"), _STALL_DISCLOSURE))


def _padstack_factory(layers):
    """(shape,size,layers) → padstack 名（首用序、确定性去重）。"""
    defs = []            # [(name, shape_lines)]
    by_key = {}
    used = set()

    def padstack_for(term):
        shape = term["shape"]
        size = list(term["size_mm"]) + [None]
        w, h = size[0], (size[1] if size[1] is not None else size[0])
        ls = _pad_layers(term, layers, None)
        key = (shape, round(w, 6), round(h, 6), ls)
        if key in by_key:
            return by_key[key]
        if shape == "circle":
            base = "Pad_v5_c_%s_um" % _name_num(w * UM)
            shapes = ["(shape (circle %s %s))" % (l, _fmt(w * UM)) for l in ls]
        else:              # rect: oval-path 近似（KiCad 导出器惯例）
            base = "Pad_v5_r_%sx%s_um" % (_name_num(w * UM), _name_num(h * UM))
            hy = h * UM / 2.0
            shapes = ["(shape (path %s %s  0 %s  0 %s))" % (
                l, _fmt(w * UM), _fmt(-hy), _fmt(hy)) for l in ls]
        name, n = base, 2
        while name in used:
            name = "%s_%d" % (base, n)
            n += 1
        used.add(name)
        by_key[key] = name
        defs.append((name, shapes))
        return name

    return padstack_for, defs


def export_dsn(board, relaxed=False, allow_missing_via=False):
    """校验后的 board dict → Specctra DSN 文本（str，canonical/确定性）。

    - relaxed: 披露放宽（标称 via padstack + 边界外扩 2mm），见模块 docstring。
    - allow_missing_via: 忠实模式显式越狱（无 via 照实导出，冒烟专用）。
    - board 先过 v5.board.load_board 单源校验（形态异常=ValueError 不吞）。
    """
    v5board.load_board(board)      # 单源 fail-closed（schema+跨字段+哈希链）
    layers = _signal_layers(board)
    if not board["partitions"]:
        raise ValueError("partitions 为空——DSN 无从生成 placement/library")
    if not board["nets"]:
        raise ValueError("nets 为空——DSN network 无从生成")
    _check_net_ids(board)
    for part in board["partitions"]:
        _check_endpoints(part)
        _check_pad_terminals(part, layers)

    vm, _ = _via_model_effective(board, relaxed, allow_missing_via)
    ws = board["workspace"]
    hr = board["hard_rules"]
    width_um = _fmt(hr["R1"]["floor_mm"] * UM)
    clear_um = _fmt(hr["R5"]["min_clearance_mm"] * UM)

    via_name = None
    if vm is not None:
        pad_d = vm["drill_mm"] + 2.0 * (vm.get("annular_mm") or 0.0)
        if pad_d > 0:
            via_name = "Via_v5_%s_%s_um" % (_name_num(vm["drill_mm"] * UM),
                                            _name_num(pad_d * UM))

    L = []
    L.append('(pcb %s' % _q(_sanitize(board.get("board_id", "board"))))
    L.append("  (parser")
    L.append('    (string_quote ")')
    L.append('    (host_cad "%s/%s")' % (GENERATOR, VERSION))
    L.append("  )")
    L.append("  (resolution um 1)")
    L.append("  (unit um)")
    L.append("  (structure")
    for idx, lid in enumerate(layers):
        L.append("    (layer %s" % lid)
        L.append("      (type signal)")
        L.append("      (property")
        L.append("        (index %d)" % idx)
        L.append("      )")
        L.append("    )")
    m = RELAXED_BOUNDARY_MARGIN_MM * UM if relaxed else 0.0
    x0, y0 = ws["x_min"] * UM - m, -ws["y_max"] * UM - m
    x1, y1 = ws["x_max"] * UM + m, -ws["y_min"] * UM + m
    L.append("    (boundary")
    L.append("      (path pcb 0  %s %s  %s %s  %s %s  %s %s  %s %s)" % (
        _fmt(x0), _fmt(y0), _fmt(x1), _fmt(y0), _fmt(x1), _fmt(y1),
        _fmt(x0), _fmt(y1), _fmt(x0), _fmt(y0)))
    L.append("    )")
    if via_name:
        L.append("    (via %s)" % _q(via_name))
    L.append("    (rule")
    L.append("      (width %s)" % width_um)
    L.append("      (clearance %s)" % clear_um)
    L.append("      (clearance %s (type smd_smd))" % clear_um)
    L.append("    )")
    L.append("  )")

    # 分区 → image/placement（固定序=partition_id 排序；refdes 净化+确定性去重）
    padstack_for, padstack_defs = _padstack_factory(layers)
    used_refs = set()
    images, placements, net_pin_refs = [], [], {}

    for part in sorted(board["partitions"], key=lambda p: p["partition_id"]):
        pid = part["partition_id"]
        ref, n = _sanitize(pid), 2
        while ref in used_refs:
            ref = "%s_%d" % (_sanitize(pid), n)
            n += 1
        used_refs.add(ref)
        (ex0, ey0), (ex1, ey1) = part["geometry"]["endpoints"]
        terms = part["geometry"].get("pad_terminals") or []
        default_term = {"shape": "circle", "size_mm": [0.6], "layers": "all"}
        pins = []
        for no, (ex, ey) in ((1, (ex0, ey0)), (2, (ex1, ey1))):
            t = next((t for t in terms if t.get("endpoint") == no - 1), None)
            ps = padstack_for(t or default_term)
            pins.append((ps, no, (ex - ex0) * UM, -(ey - ey0) * UM))
        images.append(("IMG_" + ref, pins))
        placements.append(("IMG_" + ref, ref, ex0 * UM, -ey0 * UM))
        net_pin_refs[pid] = ["%s-1" % ref, "%s-2" % ref]

    L.append("  (placement")
    for img, ref, x, y in placements:
        L.append("    (component %s" % _q(img))
        L.append("      (place %s %s %s front 0)" % (ref, _fmt(x), _fmt(y)))
        L.append("    )")
    L.append("  )")

    L.append("  (library")
    for nm, shapes in padstack_defs:
        L.append("    (padstack %s" % _q(nm))
        for s in shapes:
            L.append("      %s" % s)
        L.append("      (attach off)")
        L.append("    )")
    for img, pins in images:
        L.append("    (image %s" % _q(img))
        for ps, no, dx, dy in pins:
            L.append("      (pin %s %d %s %s)" % (ps, no, _fmt(dx), _fmt(dy)))
        L.append("    )")
    L.append("  )")

    L.append("  (network")
    net_rows = []
    for n in sorted(board["nets"], key=lambda n: n["net_id"]):
        pins = [p for pid in n["partitions"] for p in net_pin_refs[pid]]
        net_rows.append((n["net_id"], pins))
        L.append("    (net %s" % _q(n["net_id"]))
        L.append("      (pins %s)" % " ".join(pins))
        L.append("    )")
    L.append('    (class "v5_default" %s' % " ".join(_q(nid) for nid, _ in net_rows))
    if via_name:
        L.append("      (circuit")
        L.append("        (use_via %s)" % _q(via_name))
        L.append("      )")
    L.append("      (rule")
    L.append("        (width %s)" % width_um)
    L.append("        (clearance %s)" % clear_um)
    L.append("      )")
    L.append("    )")
    L.append("  )")
    L.append("  (wiring")
    L.append("  )")
    L.append(")")
    return "\n".join(L) + "\n"


def write_dsn(board, path, relaxed=False, allow_missing_via=False):
    """export_dsn → 落盘（utf-8、\\n 换行；返回 path）。"""
    text = export_dsn(board, relaxed=relaxed, allow_missing_via=allow_missing_via)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return path
