"""observation 线 actual 侧扩展（扩展实施批·包 a；ADJUDICATION-2026-09-12 R6/R7）。

四件公开能力（R6①②③ + R7），全部纯函数、零 I/O、零子进程、零网络、
零 wall-clock；既有文件零改动（check_stage.parse_routed_geometry 等既有
解析路径行为零变化，本模块为并列新增路径）：

- extract_routed_elements(board_text, *, binding)：
  routed 板文本 → 统一几何元素视图（R6①②③ 与 R7 的共同输入层；
  binding 显式选绑定档，不猜格式）。
- evaluate_layer_track_length_mm(board_text, *, binding)：R6① 逐铜层
  segment/arc 长度求值（mm；MATERIALIZATION-DESIGN §2 layer_capacity
  行声明的 actual 侧「逐层长度计算」扩展点落地）。
- count_pads_per_layer(board_text, *, binding)：R6② 逐铜层 pad 计数
  （口径与 corpus_convert.build_feedforward_obj 的 signal_layer_pad_load
  对齐：pad layers token 命中铜层名或 *.Cu 即计入该铜层；ADJUDICATION
  R8 的 146 条层声明配对依赖本口径）。
- attribute_pad_escapes(board_text, *, binding)：R6③ per-pad 逃逸归因
  （文本级 advisory：pad 板绝对位置同位 + 铜层相交判定；authority 不
  在此，非 DRC）。
- parse_routed_geometry_by_net_name(board_text)：R7 20260206+ 格 net 名
  绑定 routed 几何并行解析器（账本与 check_stage.parse_routed_geometry
  同构、net 维度改为按名绑定；解锁 pic_programmer 板此前 blocked 的
  1 via + 2 rails 计数类 actual）。

r2 扩档（G2b；追加式，既有五档行为零改动）：
- 版本门/铜层判据与 corpus_convert_ext r2 扩档同批同判：ID_BOUND_
  VERSIONS 追加 20210424/20211014/20221018（id 档）与 legacy 两档
  20171114/"4"（module 形态档）；铜层判据按档三口径——KiCad4/5 层
  编号档 index 0..31、k9 6.x/7.0 三档走 corpus_convert.K9_MODERN_
  COPPER_TYPES 白名单（单一事实源引用；mixed/power 铜层板 signal-only
  判据会得出 0 铜层虚假事实并复现 r1 4 板教训同类 fail）、20241030+
  既有档 signal-only 零改动（4 板教训 fail-closed 口径在既有档不豁免）。
- parse_routed_geometry_dual_form(board_text, *, binding)：U-R2-5 id 档
  routed 几何账并列新解析器（账本与 check_stage.parse_routed_geometry
  同构；pad 账=k5 module/k9 footprint 双形态都扫，修复 footprint 形态
  板 pad_count 恒 0 缺口；4 板型 ActualExtError 回退路径留给编排层）。

fail-closed 纪律（沿仓库现状；负向四类各有显式通道）：
- 缺字段（坐标/layers/layer/net 名等求值或归账必需项）→ ActualExtError；
- 非法枚举（binding 不在档）→ ActualExtError；
- 非有限数（被消费数值 token 不可 float 化 / NaN / Inf）→ ActualExtError；
- 未知格式（board version 不在档 / 绑定档错配——id 档出现非数字 net
  token 或名档出现数字 net token / arc 非法几何）→ ActualExtError。
与 check_stage.parse_routed_geometry 同构的宽容点仅两处（缺 width/size
字面量→不入 actual_min 最小值；via 缺 drill→vias_without_drill_token
如实计数），系账本同构口径所需，非静默猜测（有显式计数或口径声明）。

确定性：输出全部由输入文本决定；列表顺序确定（层按 index 升序、net 名
典序、pad 按 (ref,pad) 典序、evidence 按 (kind,item_index,layer) 典序）；
长度值 round 到 1e-9 mm（低于 KiCad 源字面量 1e-6 mm 精度，仅消浮点
尾数）；canonical 序列化由调用方走 hashing.json_dumps（本模块零落盘）。
"""

from __future__ import annotations

import math

from . import corpus_convert as cc, sexpr_min

MODULE_NAME = "pcbflow.actual_ext"
TRACK = "observation-actual-ext-r1"

#: 声明日期（人工会话声明常量，非机器 wall-clock）
EXT_DATE = "2026-09-12"

# ---------------------------------------------------------------------------
# 档位与版本门（显式、互斥；版本 token 全集=盘上实测数据档，与
# corpus_convert 的 KiCad5/K9_SUPPORTED_VERSIONS 版本面一致）
#
# r2 扩档（G2b；追加式，与 corpus_convert_ext r2 扩档同批同判——两侧
# 档位一致扩，避免单侧可读单侧 fail 的半开状态，G-R2-EXPANSION §4.2）：
# - 追加 k9 6.x/7.0 三档 20210424/20211014/20221018（id 绑定；与
#   corpus_convert.py `net_by_name = version < K9_NET_BY_NAME_FROM`
#   同判——该三档 net 声明=顶层 (net N "name") 数字形态）；
# - 追加 legacy 两档 20171114/"4"（module 形态 + id 绑定，顶层
#   (net N NAME)；corpus_convert_legacy.LEGACY_SUPPORTED_VERSIONS
#   同集——绑定档路由只依赖绑定形态，与解析器门分立）。
# 既有五档（20171130/20241030/20241229/20260206/20260624）行为零改动。
# ---------------------------------------------------------------------------

BINDING_ID = "net_id_bound"
BINDING_NAME = "net_name_bound"
BINDINGS = (BINDING_ID, BINDING_NAME)

#: id 绑定档：KiCad5（20171130）、k9 6.x/7.0 三档（20210424/20211014/
#: 20221018）、legacy 两档（20171114/"4"）与 k9 早期档（20241030/
#: 20241229）——元素按数字 net id 引用，顶层 (net N "name") 声明在场
ID_BOUND_VERSIONS = ("20171130", "20210424", "20211014", "20221018",
                     "20241030", "20241229", "20171114", "4")

#: 名绑定档：20260206（KiCad 10.0）起顶层 net 声明取消、元素按名引用
#: （=corpus_convert.K9_NET_BY_NAME_FROM 起；20260624 同档）
NET_NAME_BOUND_VERSIONS = ("20260206", "20260624")

#: module 形态档（KiCad4/5 方言 + legacy 两档）：footprint 节点名=module、
#: reference 取 fp_text reference、arc 取 angle 形态、铜层判据=层编号
#: 0..31（与 corpus_convert.parse_kicad5_board / corpus_convert_legacy
#: 同判）。集合字面与 corpus_convert_ext.K5_MODULE_VERSIONS 同值
#: （测试同值断言钉住）。
K5_MODULE_VERSIONS = ("20171130", "20171114", "4")

#: 新纳入 k9 6.x/7.0 档（corpus-r2-r1 实测桶）：铜层判据=
#: corpus_convert.K9_MODERN_COPPER_TYPES 白名单（signal/mixed/power/
#: jumper 单一事实源引用；signal-only 判据在 mixed/power 铜层板——
#: usb-gigabit 4 铜层、kria-k26 8 铜层全 mixed/power——会得出 0 铜层
#: 虚假事实并复现 r1 4 板教训的同类 fail）。集合字面与
#: corpus_convert_ext.EXT_MODERN_COPPER_VERSIONS 同值（测试同值断言
#: 钉住）。20241030+ 既有档 signal-only 判据零改动（4 板教训 fail-
#: closed 口径在既有档不豁免）。
EXT_MODERN_COPPER_VERSIONS = ("20210424", "20211014", "20221018")

#: R6③ 同位判定容差（mm）。KiCad 文本坐标字面量精度 1e-6 mm，逃逸线
#: 通常自 pad 中心引出；0.01mm 为防御上游舍入的工程容差（advisory 口径，
#: 常量模块内聚）。
ESCAPE_COORD_TOL_MM = 0.01

#: 三点定圆的半径数值一致性相对容差（任意不共线三点恒共圆——本检查
#: 只防字面量舍入噪声级的不自洽，KiCad 6 位小数噪声 ~1e-9 相对；
#: 1e-6 为防御性上界，超出即视为几何字面量不自洽）
ARC_RADIUS_RTOL = 1e-6

_LENGTH_ROUND_DIGITS = 9
_TWO_PI = 2.0 * math.pi
_UNNAMED_REF_PREFIX = "__NOREF__"


class ActualExtError(ValueError):
    """actual_ext 域 fail-closed 失败（ValueError 子类，调用方可细捕）。"""


# ---------------------------------------------------------------------------
# 基础严格化工具（fail-closed；与 check_stage 的宽容工具刻意区分）
# ---------------------------------------------------------------------------

def _strict_float(tok, what: str) -> float:
    """token → 有限 float；不可化/NaN/Inf 一律 ActualExtError（不猜）。"""
    if not isinstance(tok, str):
        raise ActualExtError(f"{what}: 非字符串 token: {tok!r}")
    try:
        v = float(tok)
    except ValueError:
        raise ActualExtError(
            f"{what}: 数值 token 不可解析: {tok!r}") from None
    if not math.isfinite(v):
        raise ActualExtError(f"{what}: 非有限数: {tok!r}")
    return v


def _xy(node: list, key: str, what: str) -> list:
    """(key X Y [...]) → [x, y]（float；缺失/不足两位 → ActualExtError）。
    直接子级查找（_own）。"""
    n = _own(node, key)
    if n is None or len(n) < 3:
        raise ActualExtError(
            f"{what}: 缺 {key} 或坐标不足两位（fail-closed）")
    return [_strict_float(n[1], f"{what}.{key}x"),
            _strict_float(n[2], f"{what}.{key}y")]


def _str_toks(node: list, key: str) -> list:
    n = _own(node, key)
    if n is None:
        return []
    return [t for t in n[1:] if isinstance(t, str)]


def _own(node: list, key: str):
    """直接子级查找（非深度递归）：元素属性键（at/layers/net/start…）
    只认节点自身的子键——防止 footprint 缺 at 时误消费子 pad 的 at
    等嵌套遮蔽（find_first 深度优先语义不适用于属性键）。"""
    for child in node[1:]:
        if isinstance(child, list) and child and child[0] == key:
            return child
    return None


def _scalar_pairs(node: list) -> dict:
    """块的标量子键（(k v) 且 v 为字符串叶子）——与 check_stage.setup 同法。"""
    out: dict = {}
    for c in node[1:]:
        if isinstance(c, list) and len(c) == 2 and isinstance(c[1], str):
            out[c[0]] = c[1]
    return out


def _direct_children(root: list, name: str) -> list:
    return [c for c in root[1:] if isinstance(c, list) and c and c[0] == name]


def _check_binding(binding: str) -> str:
    if binding not in BINDINGS:
        raise ActualExtError(
            f"binding 非法: {binding!r}（合法档 {list(BINDINGS)}——非法"
            f"枚举 fail-closed，不猜格式）")
    return binding


# ---------------------------------------------------------------------------
# routed 板文本 → 统一几何元素视图（共同输入层）
# ---------------------------------------------------------------------------

def _parse_board_root(board_text: str) -> tuple:
    """文本 → (root, version)；kicad_pcb 根唯一性强制。"""
    if not isinstance(board_text, str):
        raise ActualExtError("board_text 必须为 str")
    top = sexpr_min.parse(board_text)
    roots = [n for n in top
             if isinstance(n, list) and n and n[0] == "kicad_pcb"]
    if len(roots) != 1:
        raise ActualExtError(
            f"expect exactly one kicad_pcb root, got {len(roots)}")
    root = roots[0]
    v = sexpr_min.find_first(root, "version")
    version = v[1] if v is not None and len(v) > 1 else None
    return root, version


def _check_version_gate(version, binding: str) -> str:
    allowed = ID_BOUND_VERSIONS if binding == BINDING_ID \
        else NET_NAME_BOUND_VERSIONS
    if version not in allowed:
        raise ActualExtError(
            f"board version {version!r} 不在 binding={binding} 档门 "
            f"{list(allowed)} 内（未知格式 fail-closed；换档请显式改 "
            f"binding 参数）")
    return version


def _parse_copper_layers(root: list, version: str) -> list:
    """layers 表 → 铜层条目 [{index,name,type}]（index 升序）。

    铜层判据按档三口径（r2 扩档；与 corpus_convert / corpus_convert_ext
    同判，显式集合枚举分支、禁用字符串序比较——"4" 等短 token 与 8 位
    token 的字典序陷阱规避）：
    - KiCad4/5 层编号档（20171130 + legacy 20171114/"4"）：copper=
      0<=index<=31（parse_kicad5_board / corpus_convert_legacy 同判）；
    - k9 6.x/7.0 档（20210424/20211014/20221018）：type ∈
      corpus_convert.K9_MODERN_COPPER_TYPES 白名单（signal/mixed/power/
      jumper——signal-only 在 mixed/power 铜层板得出 0 铜层虚假事实；
      单一事实源引用 corpus_convert 常量）；
    - k9 既有档（20241030+）：copper=type=="signal"（既有口径零改动；
      非 signal 铜层——如 jumper 型 In4.Cu——不入铜层集合，该口径下
      声明层外的 segment 沿 r1 4 板教训 fail-closed，不豁免）。
    """
    layers = []
    for block in _direct_children(root, "layers"):
        for c in block[1:]:
            if isinstance(c, list) and len(c) >= 3:
                layers.append({"index": int(c[0]), "name": c[1],
                               "type": c[2]})
    layers.sort(key=lambda x: x["index"])
    if version in K5_MODULE_VERSIONS:
        return [l for l in layers if 0 <= l["index"] <= 31]
    if version in EXT_MODERN_COPPER_VERSIONS:
        return [l for l in layers
                if l["type"] in cc.K9_MODERN_COPPER_TYPES]
    return [l for l in layers if l["type"] == "signal"]


def _net_binding(node: list, binding: str, what: str):
    """元素 net 绑定 → (net_key, net_name)。

    id 档：(net N [name])，N 必须数字；N==0 → 无绑定 (None, None)；
      name 尽力（pad 三 token 形态有名；segment 两 token 形态名=None）。
    名档：(net "name")，name 必须为非数字字符串；空名 → 无绑定。
    交叉形态错配（档内出现另一档 token 形态）→ ActualExtError。
    """
    nn = _own(node, "net")
    if nn is None or len(nn) < 2:
        return None, None
    tok = nn[1]
    if binding == BINDING_ID:
        if not isinstance(tok, str) or not tok.isdigit():
            raise ActualExtError(
                f"{what}: id 绑定档出现非数字 net token: {tok!r}"
                "（绑定档错配 fail-closed）")
        net_id = int(tok)
        name = nn[2] if len(nn) >= 3 and isinstance(nn[2], str) else None
        if net_id == 0:
            return None, None
        return net_id, name
    if not isinstance(tok, str) or tok.isdigit():
        raise ActualExtError(
            f"{what}: 名绑定档出现数字/非字符串 net token: {tok!r}"
            "（绑定档错配 fail-closed——数字 id 形态属 id 档，请改用 "
            f"binding={BINDING_ID!r}）")
    if tok == "":
        return None, None
    return tok, tok


def _extract_reference(m: list, ordinal: int, warnings: list) -> str:
    """footprint/module 的 reference（缺→__NOREF__%03d 显式降级标记，
    沿 corpus_convert 既有先例；标记入 parse_warnings 如实登记）。
    节点形态自证：module（KiCad5 20171130）→ fp_text reference；
    footprint（k9 各档）→ property "Reference"。"""
    if m[0] == "module":
        for ft in sexpr_min.find_all(m, "fp_text"):
            if len(ft) > 2 and ft[1] == "reference":
                return ft[2]
    for prop in sexpr_min.find_all(m, "property"):
        if len(prop) > 2 and prop[1] == "Reference":
            return prop[2]
    ref = f"{_UNNAMED_REF_PREFIX}{ordinal:03d}"
    warnings.append(f"footprint_without_reference:{ref}")
    return ref


def _pad_abs_xy(pad: list, fp_at: list, fp_rot_rad: float,
                what: str) -> list:
    """pad 中心板绝对坐标 = footprint at + Rot(θ)·pad 局部 at。

    旋转角=footprint 旋转（pcbnew y-down 坐标系 RotatePoint 语义）：
    x' = x·cosθ + y·sinθ；y' = −x·sinθ + y·cosθ（θ 度→弧度；缺省 0）。
    pad 自身 (at X Y rot) 的第三 token 为焊盘自旋（只影响形状朝向，
    不影响中心位置，不消费）。advisory 口径：文本级折算，flip/镜像
    组合态的几何权威不在此声明（basis 见 attribute_pad_escapes.basis）。
    """
    local = _xy(pad, "at", what)
    x, y = local
    cx, cy = fp_at
    c, s = math.cos(fp_rot_rad), math.sin(fp_rot_rad)
    return [round(cx + x * c + y * s, _LENGTH_ROUND_DIGITS),
            round(cy - x * s + y * c, _LENGTH_ROUND_DIGITS)]


def extract_routed_elements(board_text: str, *, binding: str) -> dict:
    """routed 板文本 → 统一几何元素视图（纯函数；binding 显式选档）。

    返回键：binding / board_version / copper_layers（index 升序）/
    parse_warnings（reference 缺失降级标记）/ setup（标量子键）/
    pads / segments / arcs / vias / zones。
    元素 net 标识：net_key（id 档=int net_id；名档=net 名 str；无绑定
    =None）+ net_name（尽力，None 如实）。
    数值口径：坐标/width/size/drill 一律严格 float 化（不可化/非有限
    → ActualExtError）；width/size/drill 缺 token → None 如实（消费侧
    决定宽容或计数——与 check_stage 账本口径对齐）。
    解析失败 fail-closed（ActualExtError/SexprError 原样上抛，不猜）。
    """
    _check_binding(binding)
    root, version = _parse_board_root(board_text)
    _check_version_gate(version, binding)
    copper = _parse_copper_layers(root, version)
    copper_names = {l["name"] for l in copper}

    warnings: list = []
    setup_node = sexpr_min.find_first(root, "setup")
    setup = _scalar_pairs(setup_node) if setup_node is not None else {}

    pads, segments, arcs, vias, zones = [], [], [], [], []

    # module 形态=KiCad4/5 方言 + legacy 两档（r2 扩档：20171114/"4" 与
    # 20171130 同 module/fp_text 形态）；k9 各档=footprint 形态。
    fp_nodes = (sexpr_min.find_all(root, "module")
                if version in K5_MODULE_VERSIONS
                else sexpr_min.find_all(root, "footprint"))
    for ordinal, m in enumerate(fp_nodes):
        fp_at_toks = _str_toks(m, "at")
        if len(fp_at_toks) < 2:
            raise ActualExtError(
                f"footprint[{ordinal}]: 缺 at 或坐标不足两位（fail-closed）")
        fp_at = [_strict_float(fp_at_toks[0], f"footprint[{ordinal}].atx"),
                 _strict_float(fp_at_toks[1], f"footprint[{ordinal}].aty")]
        fp_rot = 0.0
        if len(fp_at_toks) >= 3:
            fp_rot = math.radians(_strict_float(
                fp_at_toks[2], f"footprint[{ordinal}].at_rot"))
        ref = _extract_reference(m, ordinal, warnings)
        for p in sexpr_min.find_all(m, "pad"):
            if len(p) < 2 or not isinstance(p[1], str):
                raise ActualExtError(
                    f"footprint[{ordinal}]: pad 缺 name token（fail-closed）")
            what = f"pad[{ref}.{p[1]}]"
            layers = _str_toks(p, "layers")
            if not layers:
                raise ActualExtError(f"{what}: pad 缺 layers（fail-closed）")
            net_key, net_name = _net_binding(p, binding, what)
            pads.append({
                "ref": ref, "pad": p[1],
                "type": p[2] if len(p) > 2 and isinstance(p[2], str) else None,
                "shape": p[3] if len(p) > 3 and isinstance(p[3], str)
                else None,
                "abs_xy": _pad_abs_xy(p, fp_at, fp_rot, what),
                "layers": layers,
                "net_key": net_key, "net_name": net_name,
            })

    for seg in sexpr_min.find_all(root, "segment"):
        what = "segment"
        layer_toks = _str_toks(seg, "layer")
        if len(layer_toks) != 1:
            raise ActualExtError(
                f"{what}: segment 缺 layer 或多值（fail-closed）")
        if layer_toks[0] not in copper_names:
            raise ActualExtError(
                f"{what}: segment layer {layer_toks[0]!r} 非铜层声明层"
                "（未知层 fail-closed）")
        net_key, net_name = _net_binding(seg, binding, what)
        wtoks = _str_toks(seg, "width")
        segments.append({
            "index": len(segments),
            "start": _xy(seg, "start", what),
            "end": _xy(seg, "end", what),
            "width_mm": (_strict_float(wtoks[0], f"{what}.width")
                         if wtoks else None),
            "layer": layer_toks[0],
            "net_key": net_key, "net_name": net_name,
        })

    for arc in sexpr_min.find_all(root, "arc"):
        what = "arc"
        layer_toks = _str_toks(arc, "layer")
        if len(layer_toks) != 1:
            raise ActualExtError(
                f"{what}: arc 缺 layer 或多值（fail-closed）")
        if layer_toks[0] not in copper_names:
            raise ActualExtError(
                f"{what}: arc layer {layer_toks[0]!r} 非铜层声明层"
                "（未知层 fail-closed）")
        net_key, net_name = _net_binding(arc, binding, what)
        wtoks = _str_toks(arc, "width")
        entry = {
            "index": len(arcs),
            "start": _xy(arc, "start", what),
            "end": _xy(arc, "end", what),
            "width_mm": (_strict_float(wtoks[0], f"{what}.width")
                         if wtoks else None),
            "layer": layer_toks[0],
            "net_key": net_key, "net_name": net_name,
        }
        if version in K5_MODULE_VERSIONS:
            atoks = _str_toks(arc, "angle")
            if len(atoks) != 1:
                raise ActualExtError(
                    f"{what}: KiCad4/5 方言 arc 缺 angle（fail-closed）")
            entry["angle_deg"] = _strict_float(atoks[0], f"{what}.angle")
            entry["mid"] = None
        else:
            entry["mid"] = _xy(arc, "mid", what)
            entry["angle_deg"] = None
        arcs.append(entry)

    for via in sexpr_min.find_all(root, "via"):
        what = "via"
        layers = _str_toks(via, "layers")
        if not layers:
            raise ActualExtError(f"{what}: via 缺 layers（fail-closed）")
        net_key, net_name = _net_binding(via, binding, what)
        size_toks = _str_toks(via, "size")
        drill_toks = _str_toks(via, "drill")
        vias.append({
            "index": len(vias),
            "at": _xy(via, "at", what),
            "size_mm": (_strict_float(size_toks[0], f"{what}.size")
                        if size_toks else None),
            "drill_mm": (_strict_float(drill_toks[0], f"{what}.drill")
                         if drill_toks else None),
            "layers": layers,
            "net_key": net_key, "net_name": net_name,
        })

    for zone in sexpr_min.find_all(root, "zone"):
        layer_toks = _str_toks(zone, "layer")
        net_key, net_name = _net_binding(zone, binding, "zone")
        if binding == BINDING_ID and net_key is not None:
            # id 档 zone 名在兄弟键 (net_name X)（两代 id 档同形态）
            nn = _own(zone, "net_name")
            net_name = nn[1] if nn is not None and len(nn) > 1 else None
        zones.append({
            "index": len(zones),
            "layer": layer_toks[0] if len(layer_toks) == 1 else None,
            "net_key": net_key, "net_name": net_name,
        })

    return {
        "binding": binding,
        "board_version": version,
        "copper_layers": [dict(l) for l in copper],
        "parse_warnings": list(warnings),
        "setup": dict(setup),
        "pads": pads,
        "segments": segments,
        "arcs": arcs,
        "vias": vias,
        "zones": zones,
    }


# ---------------------------------------------------------------------------
# R6① layer_capacity 长度求值（逐铜层 segment/arc，mm）
# ---------------------------------------------------------------------------

def _arc_length_mm(arc: dict, version: str, what: str) -> float:
    """弧长（mm）。两种源形态：
    - mid 形态（k9 各档）：三点定圆（任意不共线三点恒共圆；半径数值
      一致性检查仅防字面量舍入噪声不自洽）；共线/退化 → ActualExtError；
    - angle 形态（KiCad4/5 方言档=K5_MODULE_VERSIONS）：R=chord/
      (2·sin(θ/2))，len=R·θ；θ=|angle|°，θ 越出 (0,2π) 或 sin(θ/2)<=0
      → ActualExtError。
    """
    (x1, y1), (x2, y2) = arc["start"], arc["end"]
    if version in K5_MODULE_VERSIONS:
        theta = math.radians(abs(arc["angle_deg"]))
        if theta <= 0.0 or theta >= _TWO_PI:
            raise ActualExtError(
                f"{what}: arc angle 越出 (0,2π)（退化弧 fail-closed）: "
                f"{arc['angle_deg']!r}")
        chord = math.hypot(x2 - x1, y2 - y1)
        half = math.sin(theta / 2.0)
        if half <= 0.0:
            raise ActualExtError(f"{what}: 弦长公式退化（sin(θ/2)<=0）")
        return (chord / (2.0 * half)) * theta

    (xm, ym) = arc["mid"]
    d = 2.0 * (x1 * (y2 - ym) + x2 * (ym - y1) + xm * (y1 - y2))
    if d == 0.0:
        raise ActualExtError(
            f"{what}: arc 三点共线（外接圆不可定，fail-closed）")
    s1 = x1 * x1 + y1 * y1
    s2 = x2 * x2 + y2 * y2
    s3 = xm * xm + ym * ym
    ux = (s1 * (y2 - ym) + s2 * (ym - y1) + s3 * (y1 - y2)) / d
    uy = (s1 * (xm - x2) + s2 * (x1 - xm) + s3 * (x2 - x1)) / d
    r1 = math.hypot(x1 - ux, y1 - uy)
    r2 = math.hypot(x2 - ux, y2 - uy)
    rm = math.hypot(xm - ux, ym - uy)
    rmean = (r1 + r2 + rm) / 3.0
    if rmean <= 0.0 or (max(abs(r1 - rmean), abs(r2 - rmean),
                            abs(rm - rmean)) / rmean) > ARC_RADIUS_RTOL:
        raise ActualExtError(
            f"{what}: arc 三点半径数值不自洽（超字面量噪声容差，"
            "fail-closed）")
    a0 = math.atan2(y1 - uy, x1 - ux)
    am = math.atan2(ym - uy, xm - ux)
    a1 = math.atan2(y2 - uy, x2 - ux)

    def ccw(a: float, b: float) -> float:
        return (b - a) % _TWO_PI

    sweep_to_mid = ccw(a0, am)
    sweep_total = ccw(a0, a1)
    if sweep_to_mid <= sweep_total:
        theta = sweep_total  # mid 在 start→end 正向弧上
    else:
        theta = _TWO_PI - sweep_total  # 反向弧
    if theta <= 0.0:
        raise ActualExtError(f"{what}: arc 退化（θ<=0，fail-closed）")
    return rmean * theta


def _pad_copper_hit(pad_layers: list, item_layers: list,
                    copper_names: set) -> bool:
    """铜层相交判定：pad 层 token 命中 *.Cu → 与任一声明铜层相交；
    否则集合相交非空。"""
    if "*.Cu" in pad_layers:
        return any(l in copper_names for l in item_layers)
    return bool(set(pad_layers) & set(item_layers))


def evaluate_layer_track_length_mm(board_text: str, *, binding: str) -> dict:
    """R6①：逐铜层 segment/arc 长度求值（mm；纯函数）。

    语义（MATERIALIZATION-DESIGN §2 layer_capacity 行「逐层长度计算
    （segment/arc 按层求长）」扩展点的落地口径）：
    - segment 长度 = |end−start|（欧氏，mm；板文本坐标即 mm）；
    - arc 长度 = R·θ（按源形态求出，见 _arc_length_mm）；
    - 逐层账 = 元素 layer 归层（非铜层声明层上的元素已在元素视图
      fail-closed 拒绝）；无元素铜层保留零长度条目（分母完整性）。
    长度值 round 1e-9 mm（消浮点尾数；确定性由纯函数保证）。
    返回：binding / board_version / per_layer（index 升序）/
    board_totals / capability_basis。
    能力边界：非 DRC、无宽度/铜厚加权——layer_capacity 的面积语义
    （mm²=长度×轨宽×层叠因素）不在本函数声称范围，本函数只供长度面。
    """
    el = extract_routed_elements(board_text, binding=binding)
    version = el["board_version"]
    per_layer = []
    for l in el["copper_layers"]:
        per_layer.append({
            "layer": l["name"], "index": l["index"],
            "segment_length_mm": 0.0, "arc_length_mm": 0.0,
            "total_length_mm": 0.0,
            "segment_count": 0, "arc_count": 0,
        })
    by_name = {e["layer"]: e for e in per_layer}

    for seg in el["segments"]:
        (x1, y1), (x2, y2) = seg["start"], seg["end"]
        by_name[seg["layer"]]["segment_length_mm"] += math.hypot(
            x2 - x1, y2 - y1)
        by_name[seg["layer"]]["segment_count"] += 1
    for arc in el["arcs"]:
        length = _arc_length_mm(arc, version, f"arc[{arc['index']}]")
        by_name[arc["layer"]]["arc_length_mm"] += length
        by_name[arc["layer"]]["arc_count"] += 1
    for e in per_layer:
        e["segment_length_mm"] = round(e["segment_length_mm"],
                                       _LENGTH_ROUND_DIGITS)
        e["arc_length_mm"] = round(e["arc_length_mm"],
                                   _LENGTH_ROUND_DIGITS)
        e["total_length_mm"] = round(e["segment_length_mm"]
                                     + e["arc_length_mm"],
                                     _LENGTH_ROUND_DIGITS)
    totals = {
        "segment_length_mm": round(sum(e["segment_length_mm"]
                                       for e in per_layer),
                                   _LENGTH_ROUND_DIGITS),
        "arc_length_mm": round(sum(e["arc_length_mm"] for e in per_layer),
                               _LENGTH_ROUND_DIGITS),
        "total_length_mm": round(sum(e["total_length_mm"]
                                     for e in per_layer),
                                 _LENGTH_ROUND_DIGITS),
        "segment_count": sum(e["segment_count"] for e in per_layer),
        "arc_count": sum(e["arc_count"] for e in per_layer),
    }
    return {
        "binding": binding,
        "board_version": el["board_version"],
        "per_layer": per_layer,
        "board_totals": totals,
        "capability_basis": (
            "text-level length evaluation（segment=欧氏弦长；arc=R·θ，"
            "KiCad5 angle 形态弦长公式 / k9 mid 形态三点定圆）；单位 mm"
            "=板文本坐标单位；非 DRC、无宽度/铜厚加权（layer_capacity "
            "面积语义不在声称范围，本函数只供长度面）"),
    }


# ---------------------------------------------------------------------------
# R6② 逐铜层 pad 计数（口径对齐 signal_layer_pad_load 预测侧）
# ---------------------------------------------------------------------------

def count_pads_per_layer(board_text: str, *, binding: str) -> dict:
    """R6②：逐铜层 pad 计数（纯函数）。

    口径=corpus_convert.build_feedforward_obj 的 signal_layer_pad_load
    逐层判据原样：pad (layers ...) token 命中「铜层名」或「*.Cu」即计入
    该铜层（*.Cu pad 在每个铜层各计 1，故 sum(per_layer.pad_count) 可
    大于 pad_total，差异=通配 pad 数，如实登记为口径事实）。
    pad 缺 layers → ActualExtError（缺字段 fail-closed，元素视图层强制）。
    返回：binding / board_version / per_layer（index 升序）/
    pad_total / wildcard_cu_pad_count / convention_basis。
    """
    el = extract_routed_elements(board_text, binding=binding)
    per_layer = [{"layer": l["name"], "index": l["index"], "pad_count": 0}
                 for l in el["copper_layers"]]
    by_name = {e["layer"]: e for e in per_layer}
    wildcard = 0
    for p in el["pads"]:
        if "*.Cu" in p["layers"]:
            wildcard += 1
            for e in per_layer:
                e["pad_count"] += 1
            continue
        for tok in p["layers"]:
            if tok in by_name:
                by_name[tok]["pad_count"] += 1
    return {
        "binding": binding,
        "board_version": el["board_version"],
        "per_layer": per_layer,
        "pad_total": len(el["pads"]),
        "wildcard_cu_pad_count": wildcard,
        "convention_basis": (
            "pad layers token 命中铜层名或 *.Cu 即计入该铜层（与 "
            "corpus_convert.build_feedforward_obj signal_layer_pad_load "
            "逐层判据同口径）；sum(per_layer)−pad_total=通配 pad 的重复"
            "计数，属口径事实非误差"),
    }


# ---------------------------------------------------------------------------
# R6③ per-pad escape 归因（文本级 advisory）
# ---------------------------------------------------------------------------

def attribute_pad_escapes(board_text: str, *, binding: str) -> dict:
    """R6③：per-pad 逃逸归因（纯函数；advisory 级，authority 不在此）。

    归因规则（文本结构级，全量确定性）：
    - 目标集=绑定命名网的 pad（无 net/空名 pad 单独计数，不入归因）；
    - 候选=同 net_key 的 via 与 segment/arc；
    - via 归因：via at 与 pad 板绝对位置距离 ≤ ESCAPE_COORD_TOL_MM 且
      via layers 与 pad layers 铜层相交；
    - trace 归因：segment/arc 的 start 或 end 与 pad 位置距离 ≤ 容差且
      元素 layer 与 pad layers 铜层相交；
    - kind 优先级：via > trace > none（pad 上有 via 直连=via 逃逸）。
    net 匹配键：id 档=net_id（int）；名档=net 名（str）；unbound 几何
    （net_key=None）不参与匹配（文本级无接触判定，如实声明口径）。
    返回：binding / board_version / coord_tol_mm / pads（(ref,pad) 典序）
    / summary / basis。
    """
    el = extract_routed_elements(board_text, binding=binding)
    copper_names = {l["name"] for l in el["copper_layers"]}
    tol = ESCAPE_COORD_TOL_MM

    def near(a: list, b: list) -> bool:
        return math.hypot(a[0] - b[0], a[1] - b[1]) <= tol

    vias_by_net: dict = {}
    for v in el["vias"]:
        if v["net_key"] is not None:
            vias_by_net.setdefault(v["net_key"], []).append(v)
    traces_by_net: dict = {}
    for s in el["segments"]:
        if s["net_key"] is not None:
            traces_by_net.setdefault(s["net_key"], []).append(
                ("segment", s["index"], s["layer"], s["start"], s["end"]))
    for a in el["arcs"]:
        if a["net_key"] is not None:
            traces_by_net.setdefault(a["net_key"], []).append(
                ("arc", a["index"], a["layer"], a["start"], a["end"]))

    rows = []
    unbound_pads = 0
    kind_counts = {"via": 0, "trace": 0, "none": 0}
    for p in el["pads"]:
        if p["net_key"] is None:
            unbound_pads += 1
            continue
        evidence = []
        for v in vias_by_net.get(p["net_key"], []):
            if near(v["at"], p["abs_xy"]) and _pad_copper_hit(
                    p["layers"], v["layers"], copper_names):
                evidence.append(("via", v["index"], "|".join(v["layers"])))
        for kind, idx, layer, start, end in traces_by_net.get(
                p["net_key"], []):
            if (near(start, p["abs_xy"]) or near(end, p["abs_xy"])) \
                    and _pad_copper_hit(p["layers"], [layer], copper_names):
                evidence.append((kind, idx, layer))
        if any(e[0] == "via" for e in evidence):
            kind = "via"
        elif evidence:
            kind = "trace"
        else:
            kind = "none"
        kind_counts[kind] += 1
        rows.append({
            "ref": p["ref"], "pad": p["pad"],
            "net_key": p["net_key"], "net_name": p["net_name"],
            "abs_xy": p["abs_xy"], "escape_kind": kind,
            "evidence": [{"kind": k, "item_index": i, "layer": l}
                         for k, i, l in sorted(evidence)],
        })
    rows.sort(key=lambda r: (r["ref"], r["pad"]))
    return {
        "binding": binding,
        "board_version": el["board_version"],
        "coord_tol_mm": tol,
        "pads": rows,
        "summary": {
            "pad_bound_count": len(rows),
            "pad_without_net_count": unbound_pads,
            "escape_via": kind_counts["via"],
            "escape_trace": kind_counts["trace"],
            "escape_none": kind_counts["none"],
            "parse_warnings": list(el["parse_warnings"]),
        },
        "basis": (
            "text-level advisory escape attribution（pad 板绝对位置="
            "footprint at + pcbnew y-down 旋转折算的 pad 局部 at；同位"
            f"容差 {tol} mm；层相交含 *.Cu 通配；kind 优先级 via>trace>"
            "none）。authority 不在此：非 DRC、无几何接触求值；flip/"
            "镜像组合态折算边界如实声明（escape_slots actual 侧测量器"
            "扩展点，ADJUDICATION R6③）"),
    }


# ---------------------------------------------------------------------------
# R7：20260206+ 格 net 名绑定 routed 几何并行解析器
# ---------------------------------------------------------------------------

def parse_routed_geometry_by_net_name(board_text: str) -> dict:
    """R7：名绑定档 routed 板文本 → 逐网（按名）铜几何账（纯函数）。

    与 check_stage.parse_routed_geometry 并列的新解析器（该函数及全部
    既有路径零改动）；输出账本与其同构、net 维度改为按名绑定：
    - net 集=元素引用的非空 net 名全集（pad_derived：该格式顶层 net
      声明已取消，结构性 net_id 不可得，net_id=None 如实——沿
      corpus_convert k9 路径既有口径，不虚构 id）；
    - 无 net 子节点或空名绑定的元素 → items_bound_outside_declared_nets
      计数（与 id 路径「无 net 子节点→unbound」同语义对齐；名档无
      「引用未声明表」可言，故该键=无绑定元素计数，口径见
      count_convention_note）；
    - 计数语义（pad/segment/arc/via/zone/copper_item_count）、
      actual_min 字面量最小值、vias_without_drill_token、setup 标量键
      均与 id 路径同构；出现的数值 token 不可化/非有限 → ActualExtError
      （严格化强于 id 路径的宽容 float，属本模块 fail-closed 纪律）。
    版本门：NET_NAME_BOUND_VERSIONS（20260206/20260624）；其余版本
    → ActualExtError（20171130/20241030/20241229 由既有 id 路径处理，
    互斥不越界）。
    """
    el = extract_routed_elements(board_text, binding=BINDING_NAME)

    pads_per_net: dict = {}
    for p in el["pads"]:
        if p["net_key"] is not None:
            pads_per_net[p["net_key"]] = \
                pads_per_net.get(p["net_key"], 0) + 1

    geom: dict = {}  # net_name → [seg, arc, via, zone]
    unbound = 0
    for s in el["segments"]:
        if s["net_key"] is None:
            unbound += 1
            continue
        geom.setdefault(s["net_key"], [0, 0, 0, 0])[0] += 1
    for a in el["arcs"]:
        if a["net_key"] is None:
            unbound += 1
            continue
        geom.setdefault(a["net_key"], [0, 0, 0, 0])[1] += 1
    for v in el["vias"]:
        if v["net_key"] is None:
            unbound += 1
            continue
        geom.setdefault(v["net_key"], [0, 0, 0, 0])[2] += 1
    for z in el["zones"]:
        if z["net_key"] is None:
            unbound += 1
            continue
        geom.setdefault(z["net_key"], [0, 0, 0, 0])[3] += 1

    names = sorted(set(pads_per_net) | set(geom))
    per_net = []
    for name in names:
        g = geom.get(name, [0, 0, 0, 0])
        per_net.append({
            "net_id": None, "name": name,
            "pad_count": pads_per_net.get(name, 0),
            "segment_count": g[0], "arc_count": g[1],
            "via_count": g[2], "zone_count": g[3],
            "copper_item_count": g[0] + g[1] + g[2] + g[3],
        })

    widths = [s["width_mm"] for s in el["segments"]
              if s["width_mm"] is not None]
    widths += [a["width_mm"] for a in el["arcs"]
               if a["width_mm"] is not None]
    sizes = [v["size_mm"] for v in el["vias"] if v["size_mm"] is not None]
    drills = [v["drill_mm"] for v in el["vias"]
              if v["drill_mm"] is not None]
    return {
        "binding": BINDING_NAME,
        "board_version": el["board_version"],
        "net_declaration_source": "pad_derived",
        "net_count": len(names),
        "named_net_count": len(names),
        "per_net": per_net,
        "geometry_counts": {
            "segments": sum(g[0] for g in geom.values()),
            "arcs": sum(g[1] for g in geom.values()),
            "vias": sum(g[2] for g in geom.values()),
            "zones": sum(g[3] for g in geom.values()),
        },
        "items_bound_outside_declared_nets": unbound,
        "actual_min": {
            "track_width_mm": min(widths) if widths else None,
            "via_size_mm": min(sizes) if sizes else None,
            "via_drill_mm": min(drills) if drills else None,
        },
        "vias_without_drill_token": sum(1 for v in el["vias"]
                                        if v["drill_mm"] is None),
        "setup": dict(el["setup"]),
        "count_convention_note": (
            "名绑定档：net 集=元素引用名全集（pad_derived，不虚构 id）；"
            "items_bound_outside_declared_nets=无 net 子节点/空名绑定的 "
            "segment/arc/via/zone 元素计数（与 id 路径『无 net 子节点→"
            "unbound』同语义；pad 无绑定不计——沿 id 路径先例，pad_count "
            "账自然不含）；计数语义与 check_stage.parse_routed_geometry "
            "同构"),
    }


# ---------------------------------------------------------------------------
# U-R2-5：id 档 routed 几何账（双形态 pad 账；并列新解析器）
# ---------------------------------------------------------------------------

def parse_routed_geometry_dual_form(board_text: str, *, binding: str) -> dict:
    """U-R2-5：id 档 routed 板文本 → 逐网铜几何账（双形态 pad 账；纯函数）。

    与 check_stage.parse_routed_geometry 并列的新解析器（该函数及全部
    既有路径零改动），输出账本与其同构；唯一差异=pad 账从统一元素视图
    （extract_routed_elements）产出——k5 module/k9 footprint 双形态都
    扫 pad，修复 footprint 形态板 per_net[].pad_count 恒 0 的覆盖缺口
    （G-R2-EXPANSION §4.4 探针实证 + U-R2-5 裁定对象；r1 demo 池 13 板
    rails actual=0 同源缺口）。计数语义逐项与 check_stage 同判：
    - net 集=顶层 (net N "name") 声明表（len>=3；N 非数字 →
      ActualExtError，较 check_stage 的 int() ValueError 严格化同向）；
    - segment/arc/via/zone 计数=net_key 非 None 且在声明表内才入账，
      否则 items_bound_outside_declared_nets 计数（与 check_stage
      _acc 同构）。口径差异如实声明：无 net 子节点、net id 0（KiCad
      无绑定语义）与引用未声明 id 一律不入账（check_stage 对 id 0
      入账系实现细节，本函数按 actual_ext._net_binding 口径统一）；
    - pad 账判据与 check_stage 同判：pad 的 (net N "name") 三 token
      形态（有 id 且有联名）方计入（两 token (net N) 无名 pad 不计；
      不校验声明表——与 check_stage pads_per_net 同构，未声明 pad id
      经 per_net 的 nets.get(id,"") 兜底出账）；
    - actual_min / vias_without_drill_token / setup / geometry_counts
      键面与语义同 check_stage（数值严格 float 化系本模块 fail-closed
      纪律，宽容度差异见模块 docstring）。

    版本门：binding 必须=BINDING_ID（id 档全集=扩档后 ID_BOUND_
    VERSIONS）；BINDING_NAME → ActualExtError（名档走
    parse_routed_geometry_by_net_name，互斥不越界）。板版本档外 →
    ActualExtError（fail-closed）。铜层纪律沿元素视图：非铜层声明层
    上的 segment/arc → ActualExtError（r1 4 板教训口径按档执行，新档
    不豁免）——编排层对 4 板型板逐 facet try→null+reason 转记（R6②
    先例），本函数不捕获不降级。
    """
    _check_binding(binding)
    if binding != BINDING_ID:
        raise ActualExtError(
            f"parse_routed_geometry_dual_form 仅收 binding={BINDING_ID!r}"
            f"（id 档主解析器双形态账）；收到 {binding!r}——名绑定档请用 "
            "parse_routed_geometry_by_net_name（互斥不越界）")
    root, version = _parse_board_root(board_text)
    _check_version_gate(version, binding)

    nets: dict = {}
    for n in _direct_children(root, "net"):
        if len(n) >= 3:
            if not isinstance(n[1], str) or not n[1].isdigit():
                raise ActualExtError(
                    f"顶层 net 声明 id 非数字 token: {n[1]!r}"
                    "（fail-closed）")
            nets[int(n[1])] = n[2]

    el = extract_routed_elements(board_text, binding=binding)

    def _acc(net_key, idx, geom: dict) -> None:
        nonlocal unbound
        if net_key is None or net_key not in nets:
            unbound += 1
            return
        geom.setdefault(net_key, [0, 0, 0, 0])[idx] += 1

    geom: dict = {}
    unbound = 0
    for s in el["segments"]:
        _acc(s["net_key"], 0, geom)
    for a in el["arcs"]:
        _acc(a["net_key"], 1, geom)
    for v in el["vias"]:
        _acc(v["net_key"], 2, geom)
    for z in el["zones"]:
        _acc(z["net_key"], 3, geom)

    pads_per_net: dict = {}
    for p in el["pads"]:
        if p["net_key"] is not None and p["net_name"] is not None:
            pads_per_net[p["net_key"]] = pads_per_net.get(p["net_key"], 0) + 1

    widths = [s["width_mm"] for s in el["segments"]
              if s["width_mm"] is not None]
    widths += [a["width_mm"] for a in el["arcs"]
               if a["width_mm"] is not None]
    sizes = [v["size_mm"] for v in el["vias"] if v["size_mm"] is not None]
    drills = [v["drill_mm"] for v in el["vias"]
              if v["drill_mm"] is not None]

    per_net = []
    for net_id in sorted(set(nets) | set(geom) | set(pads_per_net)):
        g = geom.get(net_id, [0, 0, 0, 0])
        per_net.append({
            "net_id": net_id, "name": nets.get(net_id, ""),
            "pad_count": pads_per_net.get(net_id, 0),
            "segment_count": g[0], "arc_count": g[1],
            "via_count": g[2], "zone_count": g[3],
            "copper_item_count": g[0] + g[1] + g[2] + g[3],
        })

    return {
        "binding": BINDING_ID,
        "board_version": el["board_version"],
        "pad_account_form": ("module" if version in K5_MODULE_VERSIONS
                             else "footprint"),
        "net_count": len(nets),
        "named_net_count": sum(1 for v in nets.values() if v != ""),
        "per_net": per_net,
        "geometry_counts": {
            "segments": sum(g[0] for g in geom.values()),
            "arcs": sum(g[1] for g in geom.values()),
            "vias": sum(g[2] for g in geom.values()),
            "zones": sum(g[3] for g in geom.values()),
        },
        "items_bound_outside_declared_nets": unbound,
        "actual_min": {
            "track_width_mm": min(widths) if widths else None,
            "via_size_mm": min(sizes) if sizes else None,
            "via_drill_mm": min(drills) if drills else None,
        },
        "vias_without_drill_token": sum(1 for v in el["vias"]
                                        if v["drill_mm"] is None),
        "setup": dict(el["setup"]),
        "count_convention_note": (
            "id 档双形态账（U-R2-5）：账本与 check_stage.parse_routed_"
            "geometry 同构；pad 账=统一元素视图（k5 module/k9 footprint "
            "双形态都扫），修复 footprint 形态板 pad_count 恒 0 缺口；"
            "(net N \"name\") 三 token 形态方计入 pad 账（同 check_"
            "stage 判据）；无 net 子节点/net id 0/引用未声明 id 的元素"
            "一律不入账（id 0=KiCad 无绑定语义，actual_ext 口径）"),
    }
