# -*- coding: utf-8 -*-
"""KiCad .kicad_pcb → v5.board.v1 适配器（L0，P1；任务书 §3.1 provenance 落链）。

adapter 标识 = "kicad-adapter v0.1.0"（写入 provenance.adapter）。下列**局限与策略**
是 v0.1.0 契约的一部分，全部在此披露：

- s-expression 解析：手写 tokenizer（括号 / 带引号字符串含 ``\"`` ``\\`` ``\n``
  ``\t`` ``\r`` 转义与引号内括号 / 裸原子），**禁 eval**；任何解析失败（非法字符、
  未闭合引号、括号不配对、顶层不是唯一 ``(kicad_pcb ...)`` 表）抛 AdapterError。
  version token 各板不同（20171114/20171130/20211014/20241229/20260206…）只作记录，
  不做任何版本分支。
- stackup：按 ``(layers)`` 块启用的铜层（名字以 ``.Cu`` 结尾）生成，顺序
  F.Cu → In<N>.Cu（按 N 升序）→ B.Cu；kind 全 ``"signal"``、preferred_direction 全
  ``"any"``（v0.1.0 局限：不读文件布线偏好）、available=True。
- zones=[]（v0.1.0 局限：真实板不声明 V5 禁布/敏感/走廊区）；铜铺区 ``(zone ...)``
  不解析为几何，仅计入 report["ignored_zones"]。装饰性对象（gr_*、fp_*、text、
  text_box、dimension、group）跳过并计入 report["ignored_drawings"]。
- workspace：全部 pad/track(segment+arc)/via 铜几何的包围盒外扩固定余量
  **WORKSPACE_MARGIN_MM = 1.0 mm**（常数披露于此）。线段按两端点 ±半宽、pad 按
  中心 ±半尺寸、via 按中心 ±半径、弧按 start/mid/end 控制点与真实圆弧扫掠范围
  （含轴向极值）计入。workspace 必含全部铜几何。
- pad 绝对坐标 = footprint (module/footprint) 位置 + 按 footprint 角度旋转 pad 局部
  坐标（KiCad 口径 abs = fp + R(θ)·local）。角度 0/90/180/270°（含 -90 等价角）用
  精确三角值；其余角度走 math 三角函数——弧段包围盒与任意角旋转跨 libc 平台可能有
  末位浮点差，同机双跑严格一致（P1 门只测同机双跑同 hash）。
- 分区 = **每网一个**（board.v1 nets[].partitions minItems=1 且须指向已存在分区）：
  - partition_id = "PT-" + 净化网名（非 [A-Za-z0-9_.-] 字符替换为 "_"，空名 → "_"；
    冲突按确定网序（numbered=网号升序 / names=名字典序）追加 "_2"、"_3"… 保证唯一）。
  - geometry.endpoints = 该网全部 pad 中欧氏距离最远的两个 pad 坐标（平方距离比较；
    平手取坐标字典序最小的一对；**单 pad 网 = 两端重合的退化终点；0 pad 网
    fail-closed 抛 AdapterError**——策略披露于此）。
  - **geometry.pad_terminals（升级件① D1）**：端点两 pad 的物理铜逐项落键——
    endpoint 0/1 各一项（单 pad 退化网 = 同一 pad 两项，与退化终点语义一致）；
    shape：KiCad pad shape token circle→"circle"（size [w]，圆 pad w==h），
    其余（rect/roundrect/oval/custom…）→"rect"（size [w,h]；footprint 旋转角下
    取**轴对齐外接盒**尺寸——保守包络，披露）；layers：token 含 ``*.Cu`` →
    "all"，否则取 (layers) 中在启用铜层内的 token 列表（无铜层 token 的
    焊盘不落项、计入 report["pad_terminal_skipped"]——宽容，不 fail-closed）。
    TH pad 的 drill 不入模（schema 无孔径键；孔铜由 via_model/缺省常数承担，
    披露）。
  - ptype 确定性映射表（写死，披露于此）：网名以 "+" 开头；或 upper 后属于
    POWER_EXACT_NAMES={GND,VCC,VDD,VSS,AGND,DGND,GNDA,GNDD,AVDD,AVSS,VDDA,VSSA,
    VBUS,VBAT}；或 upper 后以 "GND" 开头（GND… 前缀族）；或 upper 后含 "PWR" 或
    "POWER" → "PWR"；其余 → "MISC"。
  - width_prior 用 adapter 文档化默认 DEFAULT_WIDTH_PRIOR={"w_min":0.3,"w_max":1.0}；
    current_a=0；speed_class="unknown"；layer_policy="any"。
  - note：多 pad 网 = "adapter: n pads abstracted to 2 endpoints"；单 pad 网 =
    "adapter: 1 pad abstracted to 2 coincident endpoints (degenerate)"。
  - 退化分区处置（升级件④ 2026-09-14 披露）：两端点重合的退化分区（单 pad 网
    或多点重合网）由 executor 按 trivially satisfied 处置（零长 route 条目，
    见 v5/executor 模块 docstring「模式A 退化分区合同」）；report 增计
    degenerate_partitions（板 dict 不变、board_sha256 不变）。
- nets：**两种网表形态都收**（version token 差异的宽容）：numbered（KiCad ≤9，
  顶层 ``(net N "name")`` 表 + 引用 ``(net N)``/``(net N "name")``，网序按网号升序）与
  name-only（KiCad 10+，version 20260206 语风，无顶层 net 表，pad/segment/via 直接
  ``(net "name")``，pad 引用即声明，网序按名字典序；形态与模式不符 → AdapterError）。
  net 0 / 空名（未连接）不产出 net/分区，其上铜只计入 workspace；net_class 省略
  （schema 可选）。numbered 模式下 track/via/pad 引用未声明 net（≠0）→ AdapterError；
  names 模式下 track/via 引用无任何 pad 的网 → AdapterError；0 pad 网 fail-closed
  抛 AdapterError。
- **via_model（升级件① D2）**：真实板 (via) 的 (size)/(drill) 对按出现次数取
  众数（平手取 (drill, size) 字典序最小——确定性；无 drill 的孔形不参选）落
  板级可选键 ``via_model={drill_mm, annular_mm=(size-drill)/2 夹 0}``；无可用
  孔对 → 不落键（消费方缺省 drill 0.3 / annular 0.15 文档化兜底）。
- hard_rules 用引擎缺省不变式地板（与 tests/fixtures_v2.py 转录一致：R1 k_a=0.4/
  floor 0.3；R2 3.0/5.0；R3 unsplittable；R4 true/2.0；R5 0.5；R6 true/true）。
- principle_registry=[]（v0.1.0 不注入理念条目）。

provenance（§3.1）：source_type="kicad_pcb"；source_uri=绝对路径（convert_file，
正斜杠规范形）或调用方传入（convert_bytes）；source_sha256=源文件原始 bytes 的
sha256；adapter="kicad-adapter v0.2.0"；board_sha256=v5.board.compute_board_sha256
结果。**返回前必须通过 v5.board.load_board 校验**（fail-closed）。

report（不入板 dict，board schema additionalProperties=false）：经
convert_file_with_report / convert_bytes_with_report 获取，键含 kicad_version、
net_count、footprint_count、pad_count、netted_pad_count、segment_count、arc_count、
via_count、ignored_zones、ignored_drawings、degenerate_partitions（升级件④
2026-09-14 增计：两端点重合的分区数）、pad_terminal_count / pad_terminal_skipped
（升级件① 2026-09-14 增计：端点焊盘落键数 / 无铜层 token 跳过数）。
"""
import collections
import math
import os
import re

from .. import canonical
from ..board import compute_board_sha256, load_board

ADAPTER_NAME = "kicad-adapter v0.2.0"

#: workspace 铜包围盒外扩余量（mm），固定常数（模块 docstring 已披露）。
WORKSPACE_MARGIN_MM = 1.0

#: adapter 文档化宽度先验默认（每分区同值；docstring 已披露）。
DEFAULT_WIDTH_PRIOR = {"w_min": 0.3, "w_max": 1.0}

#: ptype 精确名映射表（配合 "+" 前缀、"GND" 前缀、含 "PWR"/"POWER"；docstring 已披露）。
POWER_EXACT_NAMES = frozenset({
    "GND", "VCC", "VDD", "VSS", "AGND", "DGND",
    "GNDA", "GNDD", "AVDD", "AVSS", "VDDA", "VSSA",
    "VBUS", "VBAT",
})

_TO_POW = {"n": "\n", "r": "\r", "t": "\t"}


class AdapterError(ValueError):
    """KiCad 源不可解析或不可转换（fail-closed，信息带原因/位置）。"""


# ---------------------------------------------------------------- s-expression 解析

#: tokenizer 主正则：带引号字符串（含转义与引号内括号）→ 括号 → 裸原子。
_TOKEN_RE = re.compile(r'"(?:\\.|[^"\\])*"|[()]|[^\s()"]+')


def _unescape(token):
    """带引号 token（含首尾引号）→ 字符串值。转义：\\n \\r \\t \\" \\\\，其余
    反斜杠组合取字面字符（宽容）。"""
    body = token[1:-1]
    if "\\" not in body:
        return body
    out = []
    i = 0
    n = len(body)
    while i < n:
        ch = body[i]
        if ch == "\\" and i + 1 < n:
            nxt = body[i + 1]
            out.append(_TO_POW.get(nxt, nxt))
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def parse_sexpr(text):
    """解析 KiCad s-expression 文本 → 树（list 节点，头为原子字符串；叶为字符串）。

    迭代栈机实现（无递归、无 eval）。词法缺口（不可识别字符，如未闭合引号）、
    多余右括号、EOF 时括号未闭合、顶层不是唯一 ``(kicad_pcb ...)`` 表 → AdapterError。
    """
    root = []
    stack = [root]
    pos = 0
    for m in _TOKEN_RE.finditer(text):
        if m.start() > pos:
            gap = text[pos:m.start()]
            if not gap.isspace():
                raise AdapterError("词法错误：位置 %d 起存在不可识别字符 %r（如未闭合引号）"
                                   % (pos, gap[:12]))
        elif m.start() < pos:
            raise AdapterError("词法错误：位置 %d 词元重叠" % m.start())
        pos = m.end()
        tok = m.group()
        if tok == "(":
            node = []
            stack[-1].append(node)
            stack.append(node)
        elif tok == ")":
            if len(stack) == 1:
                raise AdapterError("括号不配对：位置 %d 出现多余右括号" % m.start())
            stack.pop()
        elif tok[0] == '"':
            stack[-1].append(_unescape(tok))
        else:
            stack[-1].append(tok)
    if pos != len(text) and not text[pos:].isspace():
        raise AdapterError("词法错误：位置 %d 起存在不可识别字符（如未闭合引号截断）" % pos)
    if len(stack) != 1:
        raise AdapterError("括号不配对：EOF 时仍有 %d 层未闭合括号（输入截断）" % (len(stack) - 1))
    if (len(root) != 1 or type(root[0]) is not list or not root[0]
            or type(root[0][0]) is not str or root[0][0] != "kicad_pcb"):
        raise AdapterError("顶层应恰有一个 (kicad_pcb ...) 表（得到 %d 个顶层元素）" % len(root))
    return root[0]


def _sub(node, name):
    """node 的直接子节点中头为 name 的第一个子表；无则 None。"""
    for item in node[1:]:
        if type(item) is list and item and type(item[0]) is str and item[0] == name:
            return item
    return None


def _as_float(tok, where):
    try:
        v = float(tok)
    except (TypeError, ValueError):
        raise AdapterError("%s: 数字字段不可解析 %r" % (where, tok)) from None
    if not math.isfinite(v):
        raise AdapterError("%s: 数字字段非有限值 %r" % (where, tok))
    return v


def _as_int(tok, where):
    try:
        return int(tok)
    except (TypeError, ValueError):
        raise AdapterError("%s: 整数字段不可解析 %r" % (where, tok)) from None


def _floats(node, min_count, where):
    """子表 node[1:] 全部转 float（至少 min_count 个）。任何非数值 → AdapterError。"""
    vals = []
    for tok in node[1:]:
        if type(tok) is not str:
            raise AdapterError("%s: 意外的子表嵌套" % where)
        vals.append(_as_float(tok, where))
    if len(vals) < min_count:
        raise AdapterError("%s: 需要 %d 个数值，实际 %d 个" % (where, min_count, len(vals)))
    return vals


# ---------------------------------------------------------------- 几何辅助

#: 0/90/180/270° 的精确 (cos, sin)，保证常见 footprint 角度的跨平台一致旋转。
_EXACT_COS_SIN = ((0.0, 1.0, 0.0), (90.0, 0.0, 1.0), (180.0, -1.0, 0.0), (270.0, 0.0, -1.0))
_TAU = 2.0 * math.pi


def _rotate(x, y, angle_deg):
    """KiCad 口径旋转：rel = (x·cosθ + y·sinθ, −x·sinθ + y·cosθ)。θ 按 360° 归一，
    0/90/180/270° 用精确值。"""
    a = angle_deg % 360.0
    for base, cs, sn in _EXACT_COS_SIN:
        if abs(a - base) < 1e-9:
            return (x * cs + y * sn, -x * sn + y * cs)
    rad = math.radians(a)
    cs = math.cos(rad)
    sn = math.sin(rad)
    return (x * cs + y * sn, -x * sn + y * cs)


class _BBox(object):
    __slots__ = ("x0", "y0", "x1", "y1")

    def __init__(self):
        self.x0 = math.inf
        self.y0 = math.inf
        self.x1 = -math.inf
        self.y1 = -math.inf

    def add(self, x0, y0, x1, y1):
        if x0 < self.x0:
            self.x0 = x0
        if y0 < self.y0:
            self.y0 = y0
        if x1 > self.x1:
            self.x1 = x1
        if y1 > self.y1:
            self.y1 = y1

    @property
    def empty(self):
        return self.x0 > self.x1


def farthest_endpoints(points):
    """端点极值选择策略（docstring 已披露）：欧氏距离（平方比较）最大的两点。

    平手取坐标字典序最小的一对（先对输入排序，扫描序即字典序，严格大于才更新）。
    单点 → 该点重复两次（退化终点）；空表 → AdapterError。
    返回 ((ax, ay), (bx, by))，a ≤ b 字典序。
    """
    if not points:
        raise AdapterError("farthest_endpoints: 空点集，无端点可选")
    pts = sorted(points)
    if len(pts) == 1:
        p = pts[0]
        return p, p
    best = None  # (d2, a, b)
    for i in range(len(pts)):
        ax, ay = pts[i]
        for j in range(i + 1, len(pts)):
            bx, by = pts[j]
            dx = ax - bx
            dy = ay - by
            d2 = dx * dx + dy * dy
            if best is None or d2 > best[0]:
                best = (d2, pts[i], pts[j])
    return best[1], best[2]


def _arc_bbox(bbox, x1, y1, xm, ym, x2, y2, hw):
    """铜弧（track arc，KiCad 6+）包围盒：三控制点 + 真实圆弧扫掠范围（含 0/90/180/
    270° 轴向极值点），各 ± 半宽。三点共线或外接圆退化时控制点包围盒兜底。"""
    bbox.add(x1 - hw, y1 - hw, x1 + hw, y1 + hw)
    bbox.add(xm - hw, ym - hw, xm + hw, ym + hw)
    bbox.add(x2 - hw, y2 - hw, x2 + hw, y2 + hw)
    d = 2.0 * (x1 * (ym - y2) + xm * (y2 - y1) + x2 * (y1 - ym))
    if d == 0.0 or not math.isfinite(d):
        return
    r1sq = x1 * x1 + y1 * y1
    rmsq = xm * xm + ym * ym
    r2sq = x2 * x2 + y2 * y2
    ux = (r1sq * (ym - y2) + rmsq * (y2 - y1) + r2sq * (y1 - ym)) / d
    uy = (r1sq * (x2 - xm) + rmsq * (x1 - x2) + r2sq * (xm - x1)) / d
    r = math.hypot(x1 - ux, y1 - uy)
    if not (math.isfinite(ux) and math.isfinite(uy) and math.isfinite(r)) or r > 1e9:
        return
    a1 = math.atan2(y1 - uy, x1 - ux)
    am = math.atan2(ym - uy, xm - ux)
    a2 = math.atan2(y2 - uy, x2 - ux)
    dm = (am - a1) % _TAU
    d2 = (a2 - a1) % _TAU
    if dm <= d2:
        lo, span = a1, d2            # 逆时针 a1 → a2（含 mid）
    else:
        lo, span = a2, ((a1 - a2) % _TAU)  # 顺时针 a1 → a2 ⇔ 逆时针 a2 → a1
    for k in range(4):
        ang = k * (math.pi / 2.0)
        if (ang - lo) % _TAU <= span:
            if k == 0:
                bbox.add(ux + r - hw, uy - hw, ux + r + hw, uy + hw)
            elif k == 1:
                bbox.add(ux - hw, uy + r - hw, ux + hw, uy + r + hw)
            elif k == 2:
                bbox.add(ux - r - hw, uy - hw, ux - r + hw, uy + hw)
            else:
                bbox.add(ux - hw, uy - r - hw, ux + hw, uy - r + hw)


# ---------------------------------------------------------------- ptype / id 策略

def classify_ptype(net_name):
    """网名 → ptype 确定性映射（映射表写死并已在模块 docstring 披露）。"""
    u = net_name.upper()
    if u.startswith("+"):
        return "PWR"
    if u in POWER_EXACT_NAMES:
        return "PWR"
    if u.startswith("GND"):
        return "PWR"
    if "PWR" in u or "POWER" in u:
        return "PWR"
    return "MISC"


def sanitize_net_id(net_name):
    """网名 → 净化 id 片段：非 [A-Za-z0-9_.-] 字符替换为 "_"，空名 → "_"。"""
    out = []
    for ch in net_name:
        if ("a" <= ch <= "z" or "A" <= ch <= "Z" or "0" <= ch <= "9"
                or ch == "_" or ch == "." or ch == "-"):
            out.append(ch)
        else:
            out.append("_")
    s = "".join(out)
    return s if s else "_"


def _unique_partition_id(base, used):
    """base 未用则直接用；否则追加 "_2"、"_3"…（按确定网序处理 ⇒ 确定性）。"""
    if base not in used:
        used.add(base)
        return base
    k = 2
    while "%s_%d" % (base, k) in used:
        k += 1
    pid = "%s_%d" % (base, k)
    used.add(pid)
    return pid


def _cu_order(name):
    """铜层栈序键：F.Cu → In<N>.Cu（按 N 升序）→ B.Cu → 其余 *.Cu（名字序兜底）。"""
    if name == "F.Cu":
        return (0, 0, name)
    if name == "B.Cu":
        return (2, 0, name)
    if name.startswith("In") and name.endswith(".Cu"):
        try:
            return (1, int(name[2:-3]), name)
        except ValueError:
            return (1, 1 << 30, name)
    return (3, 0, name)


def _cos_sin(angle_deg):
    """(cos, sin)：0/90/180/270° 精确值（与 _rotate 同表），其余 math 三角。"""
    a = angle_deg % 360.0
    for base, cs, sn in _EXACT_COS_SIN:
        if abs(a - base) < 1e-9:
            return cs, sn
    rad = math.radians(a)
    return math.cos(rad), math.sin(rad)


def _pad_terminal(pad_sub, shape_tok, size, angle, layer_set):
    """pad 子表 → pad_terminals 项（升级件① D1；模块 docstring 披露映射）。

    返回 dict（endpoint 由调用方按端点序填）或 None（无铜层 token——宽容跳过，
    调用方计数 pad_terminal_skipped）。rect 族在 footprint 旋转角下取轴对齐
    外接盒尺寸（保守包络，docstring 披露）。"""
    w, h = size
    if shape_tok == "circle":
        shape, dims = "circle", [w]
    else:
        cs, sn = _cos_sin(angle)
        dims = [max(abs(w * cs) + abs(h * sn), 1e-9),
                max(abs(w * sn) + abs(h * cs), 1e-9)]
        shape = "rect"
    lay_node = _sub(pad_sub, "layers")
    tokens = [t for t in (lay_node[1:] if lay_node is not None else [])
              if isinstance(t, str)]
    if "*.Cu" in tokens or "*" in tokens:
        layers = "all"
    else:
        copper = [t for t in tokens if t in layer_set]
        if not copper:
            return None
        layers = copper
    return {"endpoint": 0, "shape": shape, "size_mm": dims, "layers": layers}


# ---------------------------------------------------------------- 转换主流程

def _default_hard_rules():
    """引擎缺省不变式地板（每次调用构造新 dict，防调用方突变污染缺省）。"""
    return {
        "R1": {"k_a": 0.4, "floor_mm": 0.3},
        "R2": {"min_distance_mm": 3.0, "max_parallel_mm": 5.0},
        "R3": {"unsplittable": True},
        "R4": {"return_via_required": True, "max_distance_mm": 2.0},
        "R5": {"min_clearance_mm": 0.5},
        "R6": {"plane_forbidden": True, "keepout_zones_forbidden": True},
    }

_DRAWING_HEADS = frozenset({"text", "text_box", "dimension", "group"})


def _count_ignored(root):
    """全树迭代一遍，统计 (ignored_zones, ignored_drawings)。zone 不解析为几何。"""
    zones = 0
    drawings = 0
    pending = [root]
    while pending:
        node = pending.pop()
        for item in node:
            if type(item) is list and item:
                head = item[0]
                if type(head) is str:
                    if head == "zone":
                        zones += 1
                    elif (head.startswith("gr_") or head.startswith("fp_")
                          or head in _DRAWING_HEADS):
                        drawings += 1
                pending.append(item)
    return zones, drawings


def _declared_nets(root):
    """kicad_pcb 直接子节点的 (net N "name") 声明 → {num: name}（net 0 除外）。

    同号重复：同名宽容去重、异名 AdapterError；异号同名 AdapterError。
    可能为空：KiCad 10+（version 20260206 语风）取消顶层 net 表，网只以名字出现在
    pad/segment/via 的 (net "name") 引用里（names 模式，由调用方探测）。
    """
    nets = {}
    names = {}
    for item in root[1:]:
        if type(item) is not list or not item or item[0] != "net":
            continue
        if len(item) < 3:
            raise AdapterError("(net %r) 声明缺网名字段" % (item[1] if len(item) > 1 else "?"))
        num = _as_int(item[1], "net 号")
        if num < 0:
            raise AdapterError("net 号为负: %d" % num)
        name = item[2]
        if type(name) is not str:
            raise AdapterError("net %d 网名不是字符串: %r" % (num, name))
        if num == 0:
            continue  # 未连接网，不产出（模块 docstring 已披露）
        if num in nets:
            if nets[num] == name:
                continue
            raise AdapterError("net %d 重复声明且网名冲突: %r vs %r" % (num, nets[num], name))
        if name in names:
            raise AdapterError("网名 %r 重复（net %d 与 net %d）" % (name, names[name], num))
        nets[num] = name
        names[name] = num
    return nets


def _ref_net(item, what, declared, names_mode):
    """track(segment/arc)/via/pad 的 (net …) 引用 → 网名（统一键）；未连接 → None。

    numbered 模式（有顶层 net 表）：(net N) / (net N "name")，N≠0 必须已声明。
    names 模式（KiCad 10+）：(net "name")，空名视为未连接；pad 引用即声明，
    track/via 引用由调用方收集、扫描后统一校验。形态与模式不符 → AdapterError。
    """
    netn = _sub(item, "net")
    if netn is None:
        return None
    if len(netn) < 2 or type(netn[1]) is not str:
        raise AdapterError("%s 的 (net) 节点缺引用或引用不是字符串" % what)
    tok = netn[1]
    if names_mode:
        if len(netn) != 2:
            raise AdapterError("%s 的 (net) 引用为 numbered 形态，与文件的 name-only 网表不符: %r"
                               % (what, tok))
        return tok if tok != "" else None
    if len(netn) > 3:
        raise AdapterError("%s 的 (net) 引用字段过多: %r" % (what, netn[1:]))
    num = _as_int(tok, "%s.net 号" % what)
    if num == 0:
        return None
    if num not in declared:
        raise AdapterError("%s 引用未声明的 net %d（载有 net 的 track 必须有声明）" % (what, num))
    return declared[num]


def _convert(data, board_id, source_uri):
    """bytes → (v5.board.v1 板 dict, report dict)；板 dict 过 load_board 后返回。"""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AdapterError("源文件不是合法 UTF-8: %s" % exc) from exc
    root = parse_sexpr(text)

    report = {
        "board_id": board_id,
        "kicad_version": None,
        "net_count": 0,
        "footprint_count": 0,
        "pad_count": 0,
        "netted_pad_count": 0,
        "segment_count": 0,
        "arc_count": 0,
        "via_count": 0,
        "ignored_zones": 0,
        "ignored_drawings": 0,
        "degenerate_partitions": 0,
        "pad_terminal_count": 0,
        "pad_terminal_skipped": 0,
    }
    version = _sub(root, "version")
    if version is not None and len(version) > 1:
        report["kicad_version"] = version[1]

    # ---- stackup：按 (layers) 块启用的铜层（docstring 已披露顺序与局限）
    layers_node = _sub(root, "layers")
    if layers_node is None:
        raise AdapterError("缺 (layers) 块，无法确定启用铜层")
    copper = {}
    for entry in layers_node[1:]:
        if (type(entry) is not list or len(entry) < 2 or type(entry[0]) is not str
                or type(entry[1]) is not str):
            raise AdapterError("(layers) 条目不可解析: %r" % (entry,))
        _as_int(entry[0], "(layers) 层号")
        name = entry[1]
        if name in copper:
            raise AdapterError("(layers) 铜层名重复: %r" % name)
        if name.endswith(".Cu"):
            copper[name] = True
    if not copper:
        raise AdapterError("(layers) 块中无启用的铜层（*.Cu）")
    stackup = [{"id": name, "kind": "signal", "preferred_direction": "any",
                "available": True}
               for name in sorted(copper, key=_cu_order)]
    layer_set = frozenset(copper)

    # ---- nets：numbered 模式（顶层 net 表）或 names 模式（KiCad 10+，引用即声明）
    declared = _declared_nets(root)
    names_mode = not declared
    net_pads = {}      # 网名 -> [(x, y, pad_terminal|None)]（升级件① 附铜信息）
    used_refs = set()  # names 模式下 track/via/arc 引用的网名（扫描后统一校验）
    via_shapes = collections.Counter()   # (drill, size) → 出现数（via_model 众数）

    # ---- 铜几何遍历（顶层：module/footprint → pad；segment/arc/via）
    bbox = _BBox()
    for item in root[1:]:
        if type(item) is not list or not item or type(item[0]) is not str:
            raise AdapterError("kicad_pcb 顶层出现裸 token: %r" % (item,))
        head = item[0]
        if head == "module" or head == "footprint":
            report["footprint_count"] += 1
            at = _sub(item, "at")
            if at is None:
                raise AdapterError("%s 缺 (at) 位置" % head)
            vals = _floats(at, 2, "%s.at" % head)
            fx, fy = vals[0], vals[1]
            angle = vals[2] if len(vals) > 2 else 0.0
            for sub in item[1:]:
                if type(sub) is not list or not sub or sub[0] != "pad":
                    continue
                report["pad_count"] += 1
                pat = _sub(sub, "at")
                if pat is None:
                    raise AdapterError("pad 缺 (at)（%s @ %s, %s）" % (head, fx, fy))
                pv = _floats(pat, 2, "pad.at")
                size = _sub(sub, "size")
                if size is None:
                    raise AdapterError("pad 缺 (size)（%s @ %s, %s）" % (head, fx, fy))
                sv = _floats(size, 2, "pad.size")
                hw, hh = sv[0] / 2.0, sv[1] / 2.0
                rx, ry = _rotate(pv[0], pv[1], angle)
                ax, ay = fx + rx, fy + ry
                bbox.add(ax - hw, ay - hh, ax + hw, ay + hh)
                name = _ref_net(sub, "pad", declared, names_mode)
                if name is None:
                    continue
                report["netted_pad_count"] += 1
                shape_tok = sub[3] if len(sub) > 3 and type(sub[3]) is str else ""
                terminal = _pad_terminal(sub, shape_tok, sv, angle, layer_set)
                net_pads.setdefault(name, []).append((ax, ay, terminal))
        elif head == "segment":
            report["segment_count"] += 1
            s = _sub(item, "start")
            e = _sub(item, "end")
            w = _sub(item, "width")
            lay = _sub(item, "layer")
            if s is None or e is None or w is None or lay is None:
                raise AdapterError("segment 缺 start/end/width/layer 字段")
            sv = _floats(s, 2, "segment.start")
            ev = _floats(e, 2, "segment.end")
            hw = _floats(w, 1, "segment.width")[0] / 2.0
            if len(lay) < 2 or type(lay[1]) is not str:
                raise AdapterError("segment 缺层名")
            if lay[1] not in layer_set:
                raise AdapterError("segment 层 %r 不在启用铜层中" % lay[1])
            bbox.add(min(sv[0], ev[0]) - hw, min(sv[1], ev[1]) - hw,
                     max(sv[0], ev[0]) + hw, max(sv[1], ev[1]) + hw)
            name = _ref_net(item, "segment", declared, names_mode)
            if name is not None and names_mode:
                used_refs.add(name)
        elif head == "arc":
            report["arc_count"] += 1
            s = _sub(item, "start")
            m = _sub(item, "mid")
            e = _sub(item, "end")
            w = _sub(item, "width")
            lay = _sub(item, "layer")
            if s is None or m is None or e is None or w is None or lay is None:
                raise AdapterError("arc 缺 start/mid/end/width/layer 字段")
            sv = _floats(s, 2, "arc.start")
            mv = _floats(m, 2, "arc.mid")
            ev = _floats(e, 2, "arc.end")
            hw = _floats(w, 1, "arc.width")[0] / 2.0
            if len(lay) < 2 or type(lay[1]) is not str:
                raise AdapterError("arc 缺层名")
            if lay[1] not in layer_set:
                raise AdapterError("arc 层 %r 不在启用铜层中" % lay[1])
            _arc_bbox(bbox, sv[0], sv[1], mv[0], mv[1], ev[0], ev[1], hw)
            name = _ref_net(item, "arc", declared, names_mode)
            if name is not None and names_mode:
                used_refs.add(name)
        elif head == "via":
            report["via_count"] += 1
            at = _sub(item, "at")
            size = _sub(item, "size")
            if at is None or size is None:
                raise AdapterError("via 缺 (at)/(size)")
            av = _floats(at, 2, "via.at")
            sz = _floats(size, 1, "via.size")[0] / 2.0
            bbox.add(av[0] - sz, av[1] - sz, av[0] + sz, av[1] + sz)
            drill_node = _sub(item, "drill")
            if drill_node is not None and len(drill_node) > 1 and \
                    type(drill_node[1]) is str:
                try:
                    dv = float(drill_node[1])
                except ValueError:
                    dv = -1.0
                if math.isfinite(dv) and dv > 0.0 and sz * 2.0 > 0.0:
                    via_shapes[(dv, sz * 2.0)] += 1
            vl = _sub(item, "layers")
            if vl is not None:
                for tok in vl[1:]:
                    if type(tok) is str and tok not in layer_set:
                        raise AdapterError("via 层 %r 不在启用铜层中" % tok)
            name = _ref_net(item, "via", declared, names_mode)
            if name is not None and names_mode:
                used_refs.add(name)

    if bbox.empty:
        raise AdapterError("文件中无任何 pad/track/via 铜几何，工作区无法确定")

    # ---- 网序（确定性）：numbered 按网号升序；names 按名字典序
    if names_mode:
        for name in sorted(used_refs):
            if name not in net_pads:
                raise AdapterError("net %r 仅有 track/via 引用而无任何 pad，无法生成分区端点"
                                   % name)
        net_order = sorted(net_pads)
    else:
        net_order = [declared[num] for num in sorted(declared)]
    if not net_order:
        raise AdapterError("未发现任何 net（net 0 / 空名除外），无法产出分区")

    # ---- 分区：每网一个（端点极值 + 确定性 id/ptype/默认先验 +
    #      升级件① 端点焊盘物理铜落键）
    used_ids = set()
    partitions = []
    nets_out = []
    for name in net_order:
        pads = net_pads.get(name, [])
        if not pads:
            raise AdapterError("net %r 无任何 pad，无法生成分区端点（策略：fail-closed）"
                               % name)
        (ax, ay), (bx, by) = farthest_endpoints([p[:2] for p in pads])
        if abs(ax - bx) <= 1e-9 and abs(ay - by) <= 1e-9:
            report["degenerate_partitions"] += 1   # 升级件④：退化分区增计
        pid = _unique_partition_id("PT-" + sanitize_net_id(name), used_ids)
        if len(pads) >= 2:
            note = "adapter: %d pads abstracted to 2 endpoints" % len(pads)
        else:
            note = "adapter: 1 pad abstracted to 2 coincident endpoints (degenerate)"
        geo = {"endpoints": [[ax, ay], [bx, by]]}
        # 端点焊盘铜落键（D1）：farthest_endpoints 的两点回找首个同坐标 pad
        #（确定性；同点重复 pad 几何一致）。退化单 pad 网 = 同一 pad 落两项。
        ia = next(i for i, p in enumerate(pads)
                  if p[0] == ax and p[1] == ay)
        ib = next(i for i, p in enumerate(pads)
                  if p[0] == bx and p[1] == by)
        items = []
        for ep_idx, pi in ((0, ia), (1, ib)):
            terminal = pads[pi][2]
            if terminal is None:
                report["pad_terminal_skipped"] += 1
                continue
            item = dict(terminal)
            item["endpoint"] = ep_idx
            items.append(item)
            report["pad_terminal_count"] += 1
        if items:
            geo["pad_terminals"] = items
        partitions.append({
            "partition_id": pid,
            "ptype": classify_ptype(name),
            "geometry": geo,
            "layer_policy": "any",
            "width_prior": dict(DEFAULT_WIDTH_PRIOR),
            "current_a": 0,
            "speed_class": "unknown",
            "note": note,
        })
        nets_out.append({"net_id": name, "partitions": [pid]})
    report["net_count"] = len(net_order)

    # ---- via_model（D2）：真实孔径众数（平手取 (drill, size) 字典序最小）
    via_model = None
    if via_shapes:
        best = min(via_shapes.items(),
                   key=lambda kv: (-kv[1], kv[0]))
        drill, size = best[0]
        via_model = {"drill_mm": drill,
                     "annular_mm": max(0.0, (size - drill) / 2.0)}

    # ---- 组装板 dict（zones=[] / principle_registry=[]：v0.1.0 局限，docstring 已披露）
    board = {
        "schema_version": "v5.board.v1",
        "board_id": board_id,
        "stackup": stackup,
        "workspace": {
            "x_min": bbox.x0 - WORKSPACE_MARGIN_MM,
            "y_min": bbox.y0 - WORKSPACE_MARGIN_MM,
            "x_max": bbox.x1 + WORKSPACE_MARGIN_MM,
            "y_max": bbox.y1 + WORKSPACE_MARGIN_MM,
        },
        "zones": [],
        "partitions": partitions,
        "nets": nets_out,
        "hard_rules": _default_hard_rules(),
        "principle_registry": [],
    }
    if via_model is not None:
        board["via_model"] = via_model
    prov = {
        "source_type": "kicad_pcb",
        "source_uri": source_uri,
        "source_sha256": canonical.sha256_bytes(data),
        "adapter": ADAPTER_NAME,
        "board_sha256": "",
    }
    board["provenance"] = prov
    prov["board_sha256"] = compute_board_sha256(board)  # 复算时剔除本字段自身

    zones_n, drawings_n = _count_ignored(root)
    report["ignored_zones"] = zones_n
    report["ignored_drawings"] = drawings_n

    load_board(board)  # schema + 跨字段 + 哈希链，fail-closed
    return board, report


# ---------------------------------------------------------------- 公开入口

def convert_bytes(data, board_id, source_uri):
    """KiCad 源 bytes → v5.board.v1 板 dict（已过 v5.board.load_board 校验）。

    source_sha256 = sha256(data 原始 bytes)；source_uri 由调用方给定。
    """
    return _convert(data, board_id, source_uri)[0]


def convert_bytes_with_report(data, board_id, source_uri):
    """同 convert_bytes，另返回 report dict（含 ignored_zones 等计数）。"""
    return _convert(data, board_id, source_uri)


def convert_file(pcb_path, board_id):
    """KiCad .kicad_pcb 文件 → v5.board.v1 板 dict（已过 load_board 校验）。

    source_uri = 绝对路径（os.path.abspath，反斜杠规范为正斜杠）。
    """
    with open(pcb_path, "rb") as f:
        data = f.read()
    uri = os.path.abspath(pcb_path).replace("\\", "/")
    return _convert(data, board_id, uri)[0]


def convert_file_with_report(pcb_path, board_id):
    """同 convert_file，返回 (board, report)。"""
    with open(pcb_path, "rb") as f:
        data = f.read()
    uri = os.path.abspath(pcb_path).replace("\\", "/")
    return _convert(data, board_id, uri)
