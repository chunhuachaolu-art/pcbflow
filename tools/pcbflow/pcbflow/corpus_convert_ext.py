"""observation 线预测侧扩展（扩展实施批·包 b；ADJUDICATION-2026-09-12 R5/R8）。

六类 feedforward 估计路径扩展到 54 语料板（预测侧）：以新 producer 名
（本模块）并行于既有 pcbflow.corpus_convert 的 FF-CORPUS 薄形链——既有
corpus_convert 及一切既有模块行为零改动（并列新增路径，R5 授权）。

六类逐类诚实判定（判定依据=Rev-C 需求模型（feedforward_config.DEMAND_MODELS）
的输入源在语料板域的可得性；不伪造、不降级凑数）：
- escape_slots     可估：② C2 同源一阶模型（audit_cmd.escape_check）——
                   纯布局几何输入（pad 板绝对位置/封装 pad-bbox/同网对端
                   transit 判定），不消费 routed 走线；语料板 pad 几何全部
                   可得。口径同源保留：GND/unconnected- 跳过为模型内建。
- layer_capacity   可估：② C3 同源 demand（2/≤4 端非电源网链式直连长×
                   AUDIT_TRACK_PITCH_MM）+ 语料板域 supply（铜层数×
                   max(0, pad-bbox 板面积−封装膨胀占用)）。口径声明：Rev-C
                   的「In1/B 为 GND 平面层不供信号」层数排除系该板专用
                   stackup 口径，语料板无 plane 排除声明源 → 铜层全数计入
                   （不虚构排除），差异入 diagnostics。
- corridor         blocked：C-0053 几何宽度需求模型依赖 structures.buses
                   （总线成员表=Rev-C 域人工产物）；语料板无 bus 定义源，
                   发明 bus 识别口径=伪造，不出数。
- bus_lane         blocked：同 corridor（车道堆叠宽模型的 bus 成员缺失）。
- via_budget       blocked：demand=③ layer-plan via_count_total（路由器
                   计划级口径——语料板无路由器执行）；supply=板厂能力表
                   推导密度上界（缺源；Rev-C 自身在缺能力表时亦保持
                   missing_basis 不虚构）。FF-CORPUS not_modelled 原文
                   「via 预算（无路由器执行）」逐字保留。
- power_return_space blocked：D5 电源/回流模型需电源树/loop 网络定义
                   （Rev-C 专用 buck 环+C-0046 约束）；语料板无电源树源，
                   rails pad 账本与铜空间 mm² 语义不齐（MATERIALIZATION-
                   DESIGN §2），不混读。

R8：signal_layer_pad_load 逐层 pad 计数纳入预测侧处理范围——本模块复算
（判据与 corpus_convert.build_feedforward_obj 严格同判：铜层集合按
signal 口径，pad layers token 命中层名或 *.Cu 即计入）并与板级 FF-CORPUS
计划声明逐层对账，任何不一致 fail-closed（CorpusExtError）；对账过的层
声明（54 板合计 146 条=真实 84+demo 62）即配对就绪。

产物契约（SPEC §7 对齐）：schema_version="1.3"、plan_id、status=
planning_advisory、snapshot 六键组（语料板域填法逐键显式：board/
registry 两键 verifiable 可复核，其余三键 null+missing reason 不硬造、
feedforward_config_sha256 沿 R11 精神 null+reason）、resources、controls
（=[]：语料板域无阶段消费链，不虚构 consumer——diagnostics 显式登记）、
diagnostics、consumption_contract、stale_plan 语义（check_stale_ext：
仅 verifiable 键参与比对，任何不匹配→stale_plan 不得静默消费）。

fail-closed 纪律（沿仓库现状；负向四类显式通道）：
- 缺字段（pad 缺 at/size/layers、net 节点形态不完整）→ CorpusExtError；
- 非法输入（board_text 非 str、版本 token 不在十档全集）→ CorpusExtError；
- 非有限数（被消费数值 token 不可 float 化 / NaN / Inf）→ CorpusExtError；
- 数据不自洽（同 net_key 联名冲突）与对账失败（R8 逐层不等、参考态声明
  hash 不等）→ CorpusExtError。

预测侧诚实性关键边界：本模块全部估计只消费板文本中的 **pad/footprint
布局几何**；segments/arcs/vias/zones（routed 态）显式不解析、不消费
（consumption_contract.ignored 逐项登记）——禁止把参考态布线计数冒充
预测（via_budget blocked 的根因即此）。

确定性：输出全部由输入文本与声明常量决定；列表顺序确定（层 index 升序、
场键典序、资源行 resource_id 典序）；零 I/O、零子进程、零网络、零
wall-clock；canonical 序列化由调用方走 hashing.canonical_json_bytes。
"""

from __future__ import annotations

import math

from . import (audit_cmd, config, corpus_convert as cc,
               feedforward_config as ffc, geo, sexpr_min)
from .feedforward import classify_resource  # 既有四态分类，只消费不修改

MODULE_NAME = "pcbflow.corpus_convert_ext"
TRACK = "observation-ffext-r1"

#: 声明日期（人工会话声明常量，非机器 wall-clock）
EXT_DATE = "2026-09-12"

#: SPEC §7.1 计划 schema 版本（与 Rev-C FF 计划同契约面）
SCHEMA_VERSION = "1.3"
ARTIFACT_KIND = "feedforward_plan_ext"
PLAN_STATUS = "planning_advisory"

#: 既有 FF-CORPUS 链 producer（并行对照，不修改其任何行为）
FF_CORPUS_PRODUCER = "pcbflow.corpus_convert"

#: 资源六类（feedforward_config.RESOURCE_KINDS 同集；此处显式重申判定分组）
RESOURCE_KINDS_ALL = tuple(ffc.RESOURCE_KINDS)
ESTIMABLE_KINDS = ("escape_slots", "layer_capacity")
BLOCKED_KINDS = ("corridor", "bus_lane", "via_budget", "power_return_space")

#: FF-CORPUS not_modelled 三条中与本扩展判定相关的原文锚（照抄引用，
#: 不改写；via_budget blocked 行的 not_modelled_verbatim 取此条）
NOT_MODELLED_VIA = "via 预算（无路由器执行）"

#: 顶层 version token 全集（=盘上实测数据档；与 actual_ext 版本面一致）。
#: r2 扩档（G2a；追加式，既有五档行为零改动）：
#: - 追加 k9 6.x/7.0 三档 20210424/20211014/20221018（id 绑定；与
#:   corpus_convert.py `net_by_name = version < K9_NET_BY_NAME_FROM`
#:   同判——该三档 net 声明=顶层 (net N "name") 数字形态）；
#: - 追加 legacy 两档 20171114/"4"（module 形态 + id 绑定，顶层
#:   (net N NAME)；corpus_convert_legacy.LEGACY_SUPPORTED_VERSIONS
#:   同集——绑定档路由只依赖绑定形态，与解析器门分立）。
ID_BOUND_VERSIONS = ("20171130", "20210424", "20211014", "20221018",
                     "20241030", "20241229", "20171114", "4")
NET_NAME_BOUND_VERSIONS = ("20260206", "20260624")
ALL_VERSIONS = ID_BOUND_VERSIONS + NET_NAME_BOUND_VERSIONS

#: 新纳入 k9 6.x/7.0 档（corpus-r2-r1 实测桶）：铜层判据=
#: corpus_convert.K9_MODERN_COPPER_TYPES 白名单（signal/mixed/power/
#: jumper；signal-only 在 mixed/power 铜层板会得出 0 铜层虚假事实——
#: 按档同判纪律，单一事实源引用 corpus_convert 常量）；20241030+ 既有
#: 档 signal-only 判据零改动。
EXT_MODERN_COPPER_VERSIONS = ("20210424", "20211014", "20221018")

#: module 形态档（KiCad4/5 方言 + legacy 两档；铜层判据=KiCad4/5 层编号
#: 0..31，与 parse_kicad5_board / corpus_convert_legacy 同判）。
K5_MODULE_VERSIONS = ("20171130", "20171114", "4")

#: net_id==0 = 无绑定（KiCad 语义）；"unconnected-" 前缀为 KiCad 自动网
_UNNAMED_REF_PREFIX = "__NOREF__"


class CorpusExtError(ValueError):
    """corpus_convert_ext 域 fail-closed 失败（ValueError 子类）。"""


# ---------------------------------------------------------------------------
# 严格化工具（fail-closed；与既有宽容路径刻意区分）
# ---------------------------------------------------------------------------

def _strict_float(tok, what: str) -> float:
    """token → 有限 float；不可化/NaN/Inf 一律 CorpusExtError（不猜）。"""
    if not isinstance(tok, str):
        raise CorpusExtError(f"{what}: 非字符串 token: {tok!r}")
    try:
        v = float(tok)
    except ValueError:
        raise CorpusExtError(f"{what}: 数值 token 不可解析: {tok!r}") from None
    if not math.isfinite(v):
        raise CorpusExtError(f"{what}: 非有限数: {tok!r}")
    return v


def _own(node: list, key: str):
    """节点直接子级键查找（防嵌套遮蔽；沿 actual_ext._own 口径）。"""
    if not isinstance(node, list):
        return None
    for c in node[1:]:
        if isinstance(c, list) and c and c[0] == key:
            return c
    return None


def _direct_children(node: list, name: str) -> list:
    return [c for c in node[1:] if isinstance(c, list) and c and c[0] == name]


def _str_toks(node: list, key: str) -> list:
    n = _own(node, key)
    if n is None:
        return []
    return [t for t in n[1:] if isinstance(t, str)]


# ---------------------------------------------------------------------------
# 版本探测 → binding 路由（确定性按档路由，非猜测）
# ---------------------------------------------------------------------------

def _board_root(board_text: str) -> list:
    if not isinstance(board_text, str):
        raise CorpusExtError("board_text 必须为 str")
    top = sexpr_min.parse(board_text)
    roots = [n for n in top
             if isinstance(n, list) and n and n[0] == "kicad_pcb"]
    if len(roots) != 1:
        raise CorpusExtError(
            f"expect exactly one kicad_pcb root, got {len(roots)}")
    return roots[0]


def detect_binding(board_text: str) -> str:
    """板文本顶层 version token → 绑定档路由（确定性；不猜格式）。

    version ∈ ID_BOUND_VERSIONS → net_id_bound；∈ NET_NAME_BOUND_VERSIONS
    → net_name_bound；缺 version / 不在十档全集 → CorpusExtError
    （未知格式 fail-closed）。
    """
    root = _board_root(board_text)
    v = sexpr_min.find_first(root, "version")
    version = v[1] if v is not None and len(v) > 1 else None
    if version in ID_BOUND_VERSIONS:
        return "net_id_bound"
    if version in NET_NAME_BOUND_VERSIONS:
        return "net_name_bound"
    raise CorpusExtError(
        f"board version {version!r} 不在十档全集 {list(ALL_VERSIONS)} 内"
        "（未知格式 fail-closed，不猜绑定档）")


# ---------------------------------------------------------------------------
# pad/footprint 布局几何视图（预测侧唯一消费面；routed 元素不解析）
# ---------------------------------------------------------------------------

def _copper_layers(root: list, version: str) -> list:
    """layers 表 → 铜层条目 [{index,name,type}]（**文件声明序**，与
    corpus_convert.parse_kicad5_board/parse_kicad9_board 及
    corpus_convert_legacy.parse_legacy_board 严格同判——R8 逐层对账的
    顺序口径以此为准；不做 index 重排：k9 板文件书写序可与 index 序
    不同（如 B.Cu 书写在 In 层后），FF-CORPUS 声明序=文件序）。

    铜层判据与 corpus_convert / corpus_convert_legacy 同判（r2 扩档后
    按档三口径，显式枚举不猜——"4" 等短 token 禁用字符串序比较）：
    - KiCad4/5 层编号档（20171130 + legacy 20171114/"4"）：copper=
      0<=index<=31（parse_kicad5_board / corpus_convert_legacy 同判）；
    - k9 6.x/7.0 档（20210424/20211014/20221018）：type ∈
      corpus_convert.K9_MODERN_COPPER_TYPES（signal/mixed/power/jumper
      白名单——signal-only 在 mixed/power 铜层板得出 0 铜层虚假事实；
      单一事实源引用 corpus_convert 常量，20241030+ 档零改动）；
    - k9 既有档（20241030+）：copper=type=="signal"（既有口径零改动；
      非 signal 铜层——如 jumper 型 In4.Cu——沿 corpus_convert 既有
      口径不入铜层集合；该口径在 R8 逐层对账中与 FF-CORPUS 逐板核验）。
    """
    layers = []
    for block in _direct_children(root, "layers"):
        for c in block[1:]:
            if isinstance(c, list) and len(c) >= 3:
                layers.append({"index": int(c[0]), "name": c[1],
                               "type": c[2]})
    if version in K5_MODULE_VERSIONS:
        return [l for l in layers if 0 <= l["index"] <= 31]
    if version in EXT_MODERN_COPPER_VERSIONS:
        return [l for l in layers
                if l["type"] in cc.K9_MODERN_COPPER_TYPES]
    return [l for l in layers if l["type"] == "signal"]


def _reference_of(m: list, ordinal: int, warnings: list) -> str:
    """封装 reference（缺失→__NOREF__%03d 显式降级标记+parse_warnings，
    沿 corpus_convert/actual_ext 既有先例；不合成假名冒充）。"""
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


def _pad_net_name(pnode: list, binding: str, what: str):
    """pad 的 (net_key, net_name)：id 档 (net N [name])（N 数字，N==0→无
    绑定；name 尽力——顶层无 nets 名表数据档（实测 pcbench 系 (nets <计数>）
    仅计数形态），联名缺失→None 如实）；名档 (net "name")（非数字 str，
    空→无绑定）。档内出现另一档 token 形态 → CorpusExtError（绑定档错配
    fail-closed）。

    r2 扩档精确化（与 parse_kicad9_board 同判，om-flexgrid 实板形态）：
    名档 net 节点 token 计数区分引用形态——两 token `(net "100")`=
    KiCad10 未命名网（网名字面量为数字串），按名读（net_key=net_name=
    '100'；与 parse_kicad9_board L907 起两 token 分支同判）；三 token
    数字首 token `(net 100 "NAME")`=id 引用形态 → 档错配照拒（不放宽）。
    """
    nn = _own(pnode, "net")
    if nn is None or len(nn) < 2:
        return None, None
    tok = nn[1]
    if binding == "net_id_bound":
        if not isinstance(tok, str) or not tok.isdigit():
            raise CorpusExtError(
                f"{what}: id 绑定档出现非数字 net token: {tok!r}"
                "（绑定档错配 fail-closed）")
        net_id = int(tok)
        name = nn[2] if len(nn) >= 3 and isinstance(nn[2], str) else None
        if net_id == 0:
            return None, None
        return net_id, name
    if not isinstance(tok, str):
        raise CorpusExtError(
            f"{what}: 名绑定档出现非字符串 net token: {tok!r}"
            "（绑定档错配 fail-closed）")
    if tok.isdigit() and len(nn) >= 3:
        raise CorpusExtError(
            f"{what}: 名绑定档出现三 token 数字 id 引用形态: {tok!r}"
            "（绑定档错配 fail-closed）")
    if tok == "":
        return None, None
    return tok, tok


def extract_pad_geometry(board_text: str) -> dict:
    """板文本 → pad/footprint 布局几何视图（预测侧估计唯一输入面；纯函数）。

    返回键：board_version / binding / copper_layers（文件声明序，R8 对账
    口径）/ footprints {ref: {ref,x,y,rot,pads:[…]}} / pads（(ref,num) 典序，
    含 abs_xy/w/h/net_key/net_name/side）/ bbox（pad 包络，geo.finalize_
    board 口径；板无任何封装时=None 显式无定义，不虚构）/
    pads_without_net_token（无 net 子节点计数）/
    pads_net_id_zero（net_id==0 无绑定计数）/ parse_warnings。

    口径声明：pad 板绝对位置 = footprint at + pcbnew y-down 旋转折算的
    pad 局部 at（pad 自旋不影响中心，沿 actual_ext._pad_abs_xy 同法）；
    pad w/h = size 字面量（不做 pad 自旋尺寸折算——与 geo.parse_board 对
    Rev-C 板口径同源）；side=封装 pad-bbox 最近边（geo.finalize_board）。

    fail-closed：pad 缺 at/size（或不足两位）/size 非有限数 →
    CorpusExtError；footprint 缺 at → CorpusExtError；同 net_key 出现
    互相冲突的联名（id 档）→ CorpusExtError。
    routed 元素（segment/arc/via/zone）不解析（预测侧不消费，见模块
    docstring 边界声明）。
    """
    binding = detect_binding(board_text)
    root = _board_root(board_text)
    v = sexpr_min.find_first(root, "version")
    version = v[1] if v is not None and len(v) > 1 else None
    copper = _copper_layers(root, version)

    warnings: list = []
    # module 形态=KiCad4/5 方言 + legacy 两档（r2 扩档：20171114/"4" 与
    # 20171130 同 module/fp_text 形态）；k9 各档=footprint 形态。
    fp_nodes = (sexpr_min.find_all(root, "module")
                if version in K5_MODULE_VERSIONS
                else sexpr_min.find_all(root, "footprint"))
    footprints: dict = {}
    name_by_key: dict = {}
    no_net_token = 0
    net_id_zero = 0
    for ordinal, m in enumerate(fp_nodes):
        atn = _own(m, "at")
        if atn is None or len(atn) < 3:
            raise CorpusExtError(
                f"footprint[{ordinal}]: 缺 at 或坐标不足两位（fail-closed）")
        fx = _strict_float(atn[1], f"footprint[{ordinal}].atx")
        fy = _strict_float(atn[2], f"footprint[{ordinal}].aty")
        rot = 0.0
        if len(atn) >= 4:
            rot = _strict_float(atn[3], f"footprint[{ordinal}].at_rot")
        ref = _reference_of(m, ordinal, warnings)
        if ref in footprints:
            # 重复字面 reference（KiCad 未标注占位 REF** 多实例等板面正常
            # 现象；corpus_convert 列表形态容忍、geo.parse_board 字典形态
            # 静默覆盖——两者皆不取）：按出现序唯一化降级 + parse_warnings
            # 显式登记（不静默、不合成假唯一名——降级后缀保留原字面量）。
            n = 1
            while f"{ref}~dup{n:02d}" in footprints:
                n += 1
            new_ref = f"{ref}~dup{n:02d}"
            warnings.append(
                f"duplicate_reference:{ref}->{new_ref}（唯一化降级，"
                "escape scope.ref 如实带标记）")
            ref = new_ref
        rad = math.radians(rot)
        c_, s_ = math.cos(rad), math.sin(rad)
        pads: list = []
        for p in sexpr_min.find_all(m, "pad"):
            if len(p) < 2 or not isinstance(p[1], str):
                raise CorpusExtError(
                    f"footprint[{ordinal}]: pad 缺 name token（fail-closed）")
            what = f"pad[{ref}.{p[1]}]"
            pat = _own(p, "at")
            if pat is None or len(pat) < 3:
                raise CorpusExtError(
                    f"{what}: 缺 at 或坐标不足两位（fail-closed）")
            px = _strict_float(pat[1], f"{what}.atx")
            py = _strict_float(pat[2], f"{what}.aty")
            psz = _own(p, "size")
            if psz is None or len(psz) < 3:
                raise CorpusExtError(
                    f"{what}: 缺 size 或不足两位（fail-closed）")
            w = _strict_float(psz[1], f"{what}.sizew")
            h = _strict_float(psz[2], f"{what}.sizeh")
            layers = _str_toks(p, "layers")
            if not layers:
                raise CorpusExtError(f"{what}: 缺 layers（fail-closed）")
            net_key, net_name = _pad_net_name(p, binding, what)
            if net_key is None:
                if _own(p, "net") is None:
                    no_net_token += 1
                else:
                    net_id_zero += 1
            elif net_name is not None:
                prev = name_by_key.setdefault(net_key, net_name)
                if prev != net_name:
                    raise CorpusExtError(
                        f"{what}: net_key {net_key!r} 联名冲突 "
                        f"{prev!r} != {net_name!r}（数据不自洽 fail-closed）")
            ax = fx + px * c_ + py * s_
            ay = fy - px * s_ + py * c_
            pads.append({"ref": ref, "num": p[1], "x": ax, "y": ay,
                         "w": w, "h": h, "net": net_name,
                         "net_key": net_key, "layers": list(layers)})
        footprints[ref] = {"ref": ref, "x": fx, "y": fy, "rot": rot,
                           "pads": pads}

    board = (geo.finalize_board(footprints) if footprints else None)
    if board is not None:
        # finalize_board 返回的 pads 为 footprints 内同一 dict 引用
        # （net_key/layers 字段随元素保留）；(ref,num) 典序输出。
        all_pads = sorted(board["pads"], key=lambda p: (p["ref"], p["num"]))
        bbox = board["bbox"]
    else:
        # 零封装板（如 constraints demo 板：板文本无 footprint 节点）——
        # pad 包络 bbox 无定义（显式 None，不虚构板面积）；空视图如实返回
        # （R8 层对账与 escape 零场账在此形态下仍可执行）。
        all_pads = []
        bbox = None
    return {
        "board_version": version,
        "binding": binding,
        "copper_layers": [dict(l) for l in copper],
        "footprints": footprints,
        "pads": all_pads,
        "bbox": bbox,
        "pads_without_net_token": no_net_token,
        "pads_net_id_zero": net_id_zero,
        "parse_warnings": list(warnings),
    }


# ---------------------------------------------------------------------------
# escape_slots（C2 同源模型）与 layer_capacity（C3 同源 demand）估计
# ---------------------------------------------------------------------------

_C2_SKIP_NOTE = ("C2 同源模型内建口径：net 为 None、字面 'GND' 或 "
                 "'unconnected-' 前缀的 pad 不入逃逸账（audit_cmd."
                 "escape_check 原样行为，语料板域不改写）")


def estimate_escape_slots(pad_geo: dict) -> dict:
    """escape_slots 估计（C2 同源一阶模型；布局几何输入，非 routed 消费）。

    消费 audit_cmd.escape_check（既有实现零改动）：逐 pad 外向通道测试
    （直线或 ±45° 单折；AUDIT_ESCAPE_DEPTH_MM/AUDIT_CHANNEL_HALF_MM）+
    transit 判定（同网对端 pad 落在逃逸带外）。列账口径与 Rev-C
    _escape_resources 同：无逃逸需求的场不列账（总数入 meta）。

    返回 {kind, estimable, resources:[…], fields_meta, basis, skip_note}；
    资源行对齐 SPEC §7.3（resource_id/kind/scope/supply/demand/reserve/
    margin/yellow_margin/state/basis/net_ids/relation_ids）；语料板域无
    全局注册表 → net_ids=[]，transit 网名单入 scope.transit_nets（确定性
    典序）；快照绑定见计划级 snapshot 段（行内不复制 null hash）。
    """
    board = {"footprints": pad_geo["footprints"], "pads": pad_geo["pads"],
             "bbox": pad_geo["bbox"]}
    if not pad_geo["pads"]:
        # 零封装板：escape 场账为合法空账（无 pad 即无扇出需求；fields
        # 全零如实，不虚构任何场）。
        return {
            "kind": "escape_slots",
            "estimable": True,
            "resources": [],
            "fields_meta": {
                "fields_total": 0, "fields_with_demand": 0,
                "escape_fatal_nets": [],
                "pads_total": 0,
                "pads_without_net_token": pad_geo["pads_without_net_token"],
                "pads_net_id_zero": pad_geo["pads_net_id_zero"],
            },
            "skip_note": _C2_SKIP_NOTE,
            "basis": ("② C2 同源模型；零封装板：空场账如实（无 pad 即无"
                      "扇出需求）"),
        }
    esc = audit_cmd.escape_check(board, None)  # cls_of 为 C2 模型未消费形参
    snap_note = ("corpus_ext 域快照绑定见计划级 snapshot 段"
                 "（registry/structures/constraints/placement 缺源口径逐键"
                 "显式；行内不复制）")
    rows = []
    for key in sorted(esc["fields"]):
        f = esc["fields"][key]
        if not f["demand_transit_nets"]:
            continue  # 无逃逸需求不列账（同 Rev-C 口径；总数入 meta）
        margin = float(f["supply_clear_channels"]) - float(
            f["demand_transit_nets"])
        yellow = ffc.YELLOW_MARGIN["escape_slots"]
        rows.append({
            "resource_id": "escape_slots:" + key,
            "kind": "escape_slots",
            "scope": {"ref": f["ref"], "side": f["side"],
                      "transit_nets": list(f["transit_nets"])},
            "supply": {"value": f["supply_clear_channels"],
                       "unit": "channels",
                       "basis": ["audit escape_check（C2 一阶扇出模型）"]},
            "demand": {"value": f["demand_transit_nets"],
                       "unit": "channels",
                       "basis": ["transit 网数（需离场网；C2 同源）"]},
            "reserve": {"value": 0.0, "unit": "channels",
                        "basis": [ffc.RESERVE_DEFAULT_BASIS]},
            "margin": {"value": round(margin, 6), "unit": "channels"},
            "yellow_margin": dict(yellow),
            "state": classify_resource(margin, yellow["value"], True),
            "basis": ["audit_cmd.escape_check", "C-0037 逃逸 ≤3mm",
                      "corpus_ext：pad 几何代理布局输入（routed 走线不消费）"],
            "demand_model": ffc.DEMAND_MODELS["escape_slots"],
            "net_ids": [], "relation_ids": [], "blocking_net_ids": [],
            "snapshot_note": snap_note,
            "blocked_transit_nets": list(f["blocked_transit_nets"]),
        })
    rows.sort(key=lambda r: r["resource_id"])
    fields = esc["fields"]
    return {
        "kind": "escape_slots",
        "estimable": True,
        "resources": rows,
        "fields_meta": {
            "fields_total": len(fields),
            "fields_with_demand": sum(1 for f in fields.values()
                                      if f["demand_transit_nets"]),
            "escape_fatal_nets": list(esc["escape_fatal_nets"]),
            "pads_total": len(pad_geo["pads"]),
            "pads_without_net_token": pad_geo["pads_without_net_token"],
            "pads_net_id_zero": pad_geo["pads_net_id_zero"],
        },
        "skip_note": _C2_SKIP_NOTE,
        "basis": ("② C2 同源模型（audit_cmd.escape_check 于语料板 pad "
                  "几何重算）：demand=transit 网数、supply=外向净通道数；"
                  "输入=pad 板绝对位置/封装 pad-bbox（布局几何代理），"
                  "routed 走线不消费"),
    }


def estimate_layer_capacity(pad_geo: dict) -> dict:
    """layer_capacity 估计（C3 同源 demand + 语料板域 supply 口径）。

    demand=Σ(2/≤4 端非电源网链式直连长)×AUDIT_TRACK_PITCH_MM（与
    audit_cmd.layer_budget_check._route_iter 同源模型：GND 与
    unconnected- 前缀跳过；pad 坐标典序相邻连接欧氏长和）。语料板域无
    constraints 分类源 → cls_of 恒 None（不虚构 PWR 分类；2-4 端电源网
    未被排除的口径差异入 diagnostics）。

    supply=铜层数×max(0, pad-bbox 板面积−Σ(封装 pad-bbox 膨胀
    AUDIT_BODY_INFLATE_MM 后面积))。层数口径：语料板无 plane 排除声明源
    → 铜层全数计入（Rev-C「GND 平面层不供信号」系该板专用 stackup 口径，
    不虚构排除）；board 面积=pad 包络（geo.finalize_board bbox，与 Rev-C
    layer_budget_check 的 board['bbox'] 口径同源）。

    返回板级 1 行（kind=layer_capacity）+ utilization + basis/demand_model。
    零封装板特例：pad 包络 bbox 无定义 → supply 口径无输入，不出数（返回
    板级 blocked 声明行：不虚构板面积——类可估性与板级输入可得性分立）。
    """
    if pad_geo["bbox"] is None or not pad_geo["pads"]:
        row = {
            "resource_id": "layer_capacity:board",
            "kind": "layer_capacity",
            "estimable": False,
            "status": "blocked",
            "not_available_reason": (
                "零封装板：pad 包络板面积口径无输入（geo.finalize_board "
                "bbox 无定义）；corpus_ext 不虚构 board 面积，不出数"),
            "demand_model": ffc.DEMAND_MODELS["layer_capacity"],
            "basis": ["corpus_ext：类可估（C3 同源），板级输入缺失（零"
                      "封装）→ 板级显式 blocked"],
        }
        return {"kind": "layer_capacity", "estimable": False,
                "resources": [row],
                "layer_capacity_meta": {"zero_geometry_board": True},
                "basis": row["not_available_reason"]}
    board = {"footprints": pad_geo["footprints"], "pads": pad_geo["pads"],
             "bbox": pad_geo["bbox"]}
    nets = sorted({p["net"] for p in pad_geo["pads"] if p["net"] is not None})
    demand_len = 0.0
    nets_counted = 0
    for net in nets:
        if net == "GND" or net.startswith("unconnected-"):
            continue
        cls = None  # 语料板域无 constraints 分类源：恒 None（不虚构）
        if cls and cls.startswith("PWR"):
            continue
        pads = [p for p in pad_geo["pads"] if p["net"] == net]
        if not 2 <= len(pads) <= 4:
            continue
        pts = sorted((p["x"], p["y"]) for p in pads)
        nets_counted += 1
        for a, b in zip(pts, pts[1:]):
            demand_len += math.hypot(b[0] - a[0], b[1] - a[1])
    pitch = config.AUDIT_TRACK_PITCH_MM
    demand_area = demand_len * pitch
    used = sum(geo.bbox_area(geo.bbox_inflate(f["bbox"],
                                              config.AUDIT_BODY_INFLATE_MM))
               for f in pad_geo["footprints"].values())
    board_area = geo.bbox_area(pad_geo["bbox"])
    layer_count = len(pad_geo["copper_layers"])
    supply_area = layer_count * max(0.0, board_area - used)
    util = (demand_area / supply_area) if supply_area > 0 else None
    yellow = {"value": round(ffc.FF_LAYER_YELLOW_FRACTION * supply_area, 3),
              "unit": "mm2",
              "basis": ["FF-config：supply 的 %.0f%%（筛查）"
                        % (ffc.FF_LAYER_YELLOW_FRACTION * 100)]}
    margin = (supply_area - demand_area) if supply_area > 0 else None
    row = {
        "resource_id": "layer_capacity:board",
        "kind": "layer_capacity",
        "scope": {"board": "corpus_ext", "layer_count": layer_count,
                  "layers": [l["name"] for l in pad_geo["copper_layers"]]},
        "supply": {"value": round(supply_area, 3), "unit": "mm2",
                   "basis": ["corpus_ext C3 同构：铜层数×(pad-bbox 板面积−"
                             "封装膨胀占用)；层数=铜层全数（plane 排除无"
                             "声明源，不虚构）"]},
        "demand": {"value": round(demand_area, 3), "unit": "mm2",
                   "basis": ["audit C3 同源：链式直连长×AUDIT_TRACK_PITCH_"
                             "MM（2/≤4 端非电源网；GND/unconnected- 跳过）"]},
        "reserve": {"value": 0.0, "unit": "mm2",
                    "basis": [ffc.RESERVE_DEFAULT_BASIS]},
        "margin": ({"value": round(margin, 3), "unit": "mm2"}
                   if margin is not None else None),
        "yellow_margin": yellow,
        "state": classify_resource(margin, yellow["value"], True),
        "basis": ["out/revc-a3/audit.json#C3（口径引用）",
                  "corpus_ext：supply 层数口径与 Rev-C 差异见 diagnostics"],
        "demand_model": ffc.DEMAND_MODELS["layer_capacity"],
        "net_ids": [], "relation_ids": [], "blocking_net_ids": [],
        "snapshot_note": ("corpus_ext 域快照绑定见计划级 snapshot 段"),
        "chain_direct_nets_counted": nets_counted,
        "utilization": round(util, 6) if util is not None else None,
    }
    return {
        "kind": "layer_capacity",
        "estimable": True,
        "resources": [row],
        "layer_capacity_meta": {
            "board_area_mm2": round(board_area, 6),
            "footprint_used_mm2": round(used, 6),
            "layer_count": layer_count,
            "demand_len_mm": round(demand_len, 3),
            "named_nets_total": len(nets),
        },
        "basis": ("② C3 同源 demand 模型 + corpus_ext supply 口径；"
                  "cls_of 恒 None（语料板域无 constraints 分类源，不虚构"
                  " PWR 分类）"),
    }


# ---------------------------------------------------------------------------
# blocked 四类显式声明（诚实标记；不伪造、不降级凑数）
# ---------------------------------------------------------------------------

_BLOCKED_REASONS = {
    "corridor": (
        "C-0053 几何宽度需求模型依赖 structures.buses（总线成员表）；"
        "语料板域无 structures 产物（board 文本不含 bus 语义声明），"
        "发明 bus 识别口径=伪造，不出数"),
    "bus_lane": (
        "车道堆叠宽模型（ceil(N/2)×0.35）依赖 bus 成员定义；语料板域无 "
        "structures.buses 源（同 corridor），不出数"),
    "via_budget": (
        "demand=③ layer-plan via_count_total（路由器计划级口径）——语料板"
        "无路由器执行；supply=板厂能力表推导密度上界——缺源（Rev-C 自身在"
        "缺能力表时亦 missing_basis 不虚构）；参考态 routed via 计数属 "
        "actual 侧，不得冒充预测"),
    "power_return_space": (
        "D5 电源/回流模型需电源树/loop 网络定义（Rev-C 专用 buck 环+"
        "C-0046 约束）；语料板域无电源树源；rails pad 账本与铜空间 mm² "
        "语义不齐（MATERIALIZATION-DESIGN §2），不混读"),
}


def declare_blocked_kinds(ff_corpus_not_modelled: list) -> list:
    """四类 blocked 声明行（estimable=false；逐类缺源依据显式）。

    ff_corpus_not_modelled=板级 FF-CORPUS 计划的 not_modelled 原文列表
    （verbatim 引用；via_budget 的原文锚命中时入行 not_modelled_verbatim）。
    FF-CORPUS 未声明该类（六类模型为 Rev-C 域口径）→ not_modelled_verbatim
    =null + ff_corpus_declaration_present=false（显式布尔，非静默缺）。
    """
    rows = []
    for kind in BLOCKED_KINDS:
        verbatim = None
        if kind == "via_budget":
            verbatim = (NOT_MODELLED_VIA
                        if NOT_MODELLED_VIA in (ff_corpus_not_modelled or [])
                        else None)
        rows.append({
            "resource_id": f"{kind}:board",
            "kind": kind,
            "estimable": False,
            "status": "blocked",
            "not_available_reason": _BLOCKED_REASONS[kind],
            "ff_corpus_declaration_present": verbatim is not None,
            "not_modelled_verbatim": verbatim,
            "demand_model": ffc.DEMAND_MODELS[kind],
            "basis": ["feedforward_config.DEMAND_MODELS（Rev-C 域口径）",
                      "corpus_ext：需求模型输入源在语料板域缺失（逐类依据"
                      "见 not_available_reason）"],
        })
    rows.sort(key=lambda r: r["resource_id"])
    return rows


# ---------------------------------------------------------------------------
# R8：signal_layer_pad_load 复算 + FF-CORPUS 逐层对账（fail-closed）
# ---------------------------------------------------------------------------

def _pad_layer_counts(pad_geo: dict) -> list:
    """逐铜层 pad 计数（判据与 corpus_convert.build_feedforward_obj 严格
    同判：pad layers token 命中铜层名或 *.Cu 即计入该铜层；含通配 pad 的
    跨层重复计数）。层序=copper_layers index 升序。"""
    out = []
    for l in pad_geo["copper_layers"]:
        cnt = sum(1 for p in pad_geo["pads"]
                  if any(x == l["name"] or x == "*.Cu" for x in p["layers"]))
        out.append({"layer": l["name"], "pad_count": cnt})
    return out


def align_signal_layer_pad_load(pad_geo: dict, ff_corpus_plan: dict) -> dict:
    """R8：逐层 pad 计数复算并与板级 FF-CORPUS 计划声明逐层对账。

    对账规则（fail-closed）：层名集合全等 + 逐层 pad_count 全等；任何
    不一致 → CorpusExtError（不修复、不跳过、不降级）。
    返回 {recomputed:[…], ff_corpus_declared:[…], aligned:true, layers_total}。
    """
    if not isinstance(ff_corpus_plan, dict):
        raise CorpusExtError("ff_corpus_plan 必须为 dict")
    for key in ("signal_layer_pad_load", "not_modelled", "plan_id"):
        if key not in ff_corpus_plan:
            raise CorpusExtError(
                f"ff_corpus_plan 缺键 {key!r}（fail-closed）")
    recomputed = _pad_layer_counts(pad_geo)
    declared = [{"layer": d["layer"], "pad_count": d["pad_count"]}
                for d in ff_corpus_plan["signal_layer_pad_load"]]
    if [d["layer"] for d in declared] != [r["layer"] for r in recomputed]:
        raise CorpusExtError(
            "R8 对账失败：层名集合/顺序与 FF-CORPUS 声明不一致 "
            f"declared={[d['layer'] for d in declared]} vs "
            f"recomputed={[r['layer'] for r in recomputed]}")
    for d, r in zip(declared, recomputed):
        if d["pad_count"] != r["pad_count"]:
            raise CorpusExtError(
                f"R8 对账失败：层 {d['layer']!r} pad_count "
                f"declared={d['pad_count']} vs recomputed={r['pad_count']}")
    return {
        "recomputed": recomputed,
        "ff_corpus_declared": declared,
        "aligned": True,
        "layers_total": len(recomputed),
    }


# ---------------------------------------------------------------------------
# 扩展计划对象（SPEC §7 契约面）
# ---------------------------------------------------------------------------

def build_snapshot_section(board_sha256: str, registry_sha256) -> dict:
    """snapshot 六键组（语料板域填法逐键显式；stale 语义见 check_stale_ext）。

    board_snapshot_sha256=调用方 sha256_file 字节口径（datasets 权威原件）；
    registry_snapshot_hash=板级 derived/net-registry.json 字节 sha256
    （语料板域注册表语义最近对应物，口径显式；None=文件不可得时如实 null）。
    structures/constraints/placement/feedforward_config 四键=null+missing
    reason（语料板域无源，不硬造——R11 同精神）。
    """
    missing = {
        "structures_sha256": (
            "语料板域无 structures 产物（Rev-C 域人工产物；board 文本不含 "
            "structures 语义），不虚构"),
        "constraints_sha256": (
            "语料板 profiles derived 无 constraints.json（实测），不虚构"),
        "placement_snapshot_sha256": (
            "语料板域无 placement CSV；escape/层容量模型消费 pad 几何"
            "（board 文本内嵌布局语义代理），不虚构 placement 快照"),
        "feedforward_config_sha256": (
            "FF-CORPUS 薄形域无 feedforward config 产物（R11 同精神：不"
            "硬造）；planning 阈值取自代码常量 pcbflow/feedforward_config."
            "py v%s，模块文件 hash 见 plan_meta.feedforward_config_module_"
            "sha256" % ffc.FF_CONFIG_VERSION),
    }
    section = {
        "board_snapshot_sha256": board_sha256,
        "registry_snapshot_hash": registry_sha256,
    }
    for k, reason in missing.items():
        section[k] = None
    basis = {
        "board_snapshot_sha256": {
            "verifiable": True,
            "source": "datasets 权威板原件（字节口径 sha256_file）"},
        "registry_snapshot_hash": {
            "verifiable": registry_sha256 is not None,
            "source": ("profiles/<pid>/derived/net-registry.json（板级派生"
                       "注册表，字节口径 sha256_file；语料板域无全局注册表"
                       "快照，代位口径显式声明）"
                       if registry_sha256 is not None else
                       "net-registry.json 不可得，如实 null"),
        },
    }
    for k, reason in missing.items():
        basis[k] = {"verifiable": False, "reason": reason}
    return {"values": section, "binding": basis}


def check_stale_ext(plan: dict, current_board_sha256: str,
                    current_registry_sha256) -> dict:
    """stale_plan 检查（对齐 feedforward.check_stale 输出形态）。

    规则：仅对 snapshot.binding 中 verifiable=true 的键比对 plan 值与
    current 值，任何不匹配 → stale_plan=true + diff_keys（不得静默消费）；
    verifiable=false 的键无源可比，不参与比对（缺源口径显式在 binding）。
    """
    snap = plan["snapshot"]
    diffs = {}
    for k, b in snap["binding"].items():
        if not b.get("verifiable"):
            continue
        current = (current_board_sha256 if k == "board_snapshot_sha256"
                   else current_registry_sha256)
        if snap["values"].get(k) != current:
            diffs[k] = {"plan": snap["values"].get(k), "current": current}
    return {"stale_plan": bool(diffs), "diff_keys": sorted(diffs),
            "diffs": diffs}


def build_ext_plan_obj(board_text: str, *, profile_id: str, board_id: str,
                       dataset_id: str, split_role: str, board_path_rel: str,
                       board_sha256: str, ff_corpus_plan: dict,
                       registry_sha256=None) -> dict:
    """单板扩展计划对象（SPEC §7 契约面；纯函数，输入全显式）。

    组装：snapshot 六键组 + 六类资源段（escape/layer_capacity 估计行 +
    四类 blocked 声明行，resource_id 典序）+ controls=[]（语料板域无阶段
    消费链，diagnostics 显式登记）+ diagnostics（口径差异逐条）+
    consumption_contract（routed 元素 ignored 显式）+ R8 逐层对账段 +
    corpus_baseline（FF-CORPUS 原计划引用，not_modelled 原文 verbatim）。
    任何估计失败异常原样上抛（fail-closed，不留半形计划）。
    """
    pad_geo = extract_pad_geometry(board_text)
    esc = estimate_escape_slots(pad_geo)
    cap = estimate_layer_capacity(pad_geo)
    blocked = declare_blocked_kinds(ff_corpus_plan.get("not_modelled") or [])
    r8 = align_signal_layer_pad_load(pad_geo, ff_corpus_plan)

    resources = (esc["resources"] + cap["resources"] + blocked)
    resources.sort(key=lambda r: r["resource_id"])
    diagnostics = [
        {"id": "corpus_ext_controls_empty",
         "severity": "scope_declaration",
         "title": "controls=[]：语料板域无 ③④ 阶段消费链",
         "resolution": "不虚构 consumer/不生成 reserve 提案；Rev-C 的 "
                       "reserve_* 控制语义依赖下游路由阶段，语料板域不存在"},
        {"id": "corpus_ext_layer_capacity_layer_count",
         "severity": "convention_declaration",
         "title": "layer_capacity supply 层数=铜层全数",
         "resolution": "Rev-C「In1/B 为 GND 平面层不供信号」系该板专用 "
                       "stackup 口径；语料板无 plane 排除声明源，不虚构排除"},
        {"id": "corpus_ext_cls_of_none",
         "severity": "convention_declaration",
         "title": "C3 demand 链 cls_of 恒 None（无 constraints 分类源）",
         "resolution": "2/≤4 端电源网未被 PWR 类排除的口径差异如实登记；"
                       "GND 与 unconnected- 前缀跳过为模型内建同源口径"},
        {"id": "corpus_ext_routed_not_consumed",
         "severity": "prediction_hygiene",
         "title": "预测侧不消费 routed 元素（segment/arc/via/zone）",
         "resolution": "全部估计只消费 pad/footprint 布局几何；参考态布线"
                       "计数属 actual 侧（via_budget blocked 根因即此）"},
        {"id": "corpus_ext_supply_pad_bbox_proxy",
         "severity": "convention_declaration",
         "title": "layer_capacity supply 板面积=pad 包络代理（非 Edge.Cuts "
                  "轮廓；zones/板轮廓不在消费面）",
         "resolution": "与 Rev-C layer_budget_check 的 board['bbox'] 口径"
                       "同源；pad 分布稀疏/位置退化的板 supply 可为 0 → "
                       "missing_basis 如实（不虚构板轮廓面积）"},
        {"id": "corpus_ext_snapshot_missing_keys",
         "severity": "missing_basis",
         "title": "snapshot 四键缺源（structures/constraints/placement/"
                  "feedforward_config）",
         "resolution": "null+missing reason 逐键显式（不硬造）；stale 比对"
                       "仅 verifiable 键参与（check_stale_ext）"},
    ]
    plan = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": ARTIFACT_KIND,
        "board_id": board_id,
        "profile_id": profile_id,
        "dataset_id": dataset_id,
        "split_role": split_role,
        "plan_id": f"FF-EXT-{profile_id.upper()}-0001",
        "status": PLAN_STATUS,
        "snapshot": build_snapshot_section(board_sha256, registry_sha256),
        "resources": resources,
        "controls": [],
        "diagnostics": diagnostics,
        "resource_kind_summary": {
            "estimable_kinds": list(ESTIMABLE_KINDS),
            "blocked_kinds": list(BLOCKED_KINDS),
            "escape_rows": len(esc["resources"]),
            "layer_capacity_rows": (len(cap["resources"])
                                    if cap["estimable"] else 0),
            "layer_capacity_board_blocked": not cap["estimable"],
            "blocked_rows": (len(blocked) + (0 if cap["estimable"] else 1)),
        },
        "escape_fields_meta": esc["fields_meta"],
        "layer_capacity_meta": cap["layer_capacity_meta"],
        "signal_layer_pad_load": {
            "convention": ("corpus_convert.build_feedforward_obj 同判复算："
                           "pad layers token 命中铜层名或 *.Cu 即计入"
                           "（含通配 pad 跨层重复计数）；R8 对账已过"
                           "（fail-closed）"),
            "recomputed": r8["recomputed"],
            "ff_corpus_declared": r8["ff_corpus_declared"],
            "aligned": r8["aligned"],
            "layers_total": r8["layers_total"],
        },
        "consumption_contract": {
            "declared_consumed": [
                {"artifact": board_path_rel, "role": "board_layout_geometry",
                 "sha256": board_sha256},
                {"artifact": f"profiles/{profile_id}/derived/"
                             "feedforward-plan.json",
                 "role": "ff_corpus_baseline_plan"},
            ],
            "actually_read": [
                {"artifact": board_path_rel, "field": "layers/module|"
                                 "footprint/pad(at,size,layers,net)",
                 "role": "board"},
                {"artifact": "ff_corpus_plan(调用方传入对象)",
                 "field": "signal_layer_pad_load/not_modelled/plan_id",
                 "role": "ff_corpus"},
            ],
            "derived": [
                "extract_pad_geometry（pad 布局几何视图）",
                "estimate_escape_slots（C2 同源场账）",
                "estimate_layer_capacity（C3 同源 demand+corpus_ext supply）",
                "align_signal_layer_pad_load（R8 逐层对账）",
            ],
            "ignored": [
                {"elements": "segment/arc/via/zone",
                 "reason": "routed 态；预测侧显式不消费（prediction_hygiene）"},
                {"elements": "zones",
                 "reason": "铜区面积语义未建模（不伪造电源平面容量）"},
            ],
            "fallback": None,
            "fidelity": "corpus_ext_first_order（planning_advisory 级；"
                        "C2/C3 同源一阶模型；非 DRC、非 v1.x FA3 引擎）",
        },
        "corpus_baseline": {
            "producer": ff_corpus_plan.get("producer"),
            "plan_id": ff_corpus_plan["plan_id"],
            "not_modelled_verbatim": list(ff_corpus_plan["not_modelled"]),
            "parallel_note": ("既有 FF-CORPUS 链（pcbflow.corpus_convert）"
                              "行为零改动；本计划为并列新 producer 产物"),
        },
        "plan_meta": {
            "producer": MODULE_NAME,
            "track": TRACK,
            "ext_date": EXT_DATE,
            "authority": ("corpus_ext_first_order（planning_advisory 级；"
                          "非 Rev-C FF1 引擎、非 DRC）"),
            "feedforward_config_module_sha256_note": (
                "由调用方按需以 hashing.sha256_file 补记（本模块零 I/O）"),
            "stale_semantics": {
                "rule": "SPEC §7.4：六键逐一比对，不匹配→stale_plan 不得"
                        "静默消费",
                "corpus_ext_domain": ("仅 snapshot.binding 中 verifiable="
                                      "true 的键参与比对（check_stale_ext）；"
                                      "verifiable=false 键无源可比、缺源口径"
                                      "逐键显式"),
            },
        },
    }
    return plan


# ---------------------------------------------------------------------------
# 54 板盘点与单板记录（清单可追溯：manifest 对账，fail-closed）
# ---------------------------------------------------------------------------

def build_board_records(k9_plan: dict, manifests: dict) -> list:
    """54 语料板盘点记录（纯函数；输入=盘面事实对象，全部显式）。

    k9_plan=out/v3-tl5/k9-route-check-batch-r1/plan.json 解析对象（demo 17
    板：profile_id/board_id/source_rel/source_sha256_before_drc/split_role）；
    manifests={"pcbench": <pcbench-r1-v3 manifest obj>, "pcbbm": <…>, "kicad":
    <kicad-demos-r1 manifest obj>}。返回逐板记录（profile_id/board_id/
    dataset_id/split_role/board_path_rel/ff_plan_rel/manifest_ref），sorted
    by profile_id；54 之外的记录一概不收（不扩名单）；kicad manifest 的
    r1 为引用版本（R3：split.manifest_ref=kicad-demos-r1）。
    """
    records = []
    by_pid_k9 = {b["profile_id"]: b for b in k9_plan["boards"]}
    for pid in sorted(by_pid_k9):
        b = by_pid_k9[pid]
        mid = b["board_id"]
        splits = manifests["kicad"]["dataset_splits"]
        role = None
        for r in ("train", "validation", "holdout"):
            if mid in splits.get(r, []):
                role = r
                break
        if role is None:
            raise CorpusExtError(
                f"{pid}: board_id {mid!r} 不在 kicad-r1 manifest "
                "dataset_splits 任一侧（对账 fail-closed）")
        if role != b["split_role"]:
            raise CorpusExtError(
                f"{pid}: k9 split_role={b['split_role']!r} 与 kicad-r1 "
                f"manifest 派生 role={role!r} 冲突（对账 fail-closed）")
        if mid not in manifests["kicad"]["board_ids"]:
            raise CorpusExtError(f"{pid}: board_id {mid!r} 不在 kicad-r1 "
                                 "manifest board_ids（对账 fail-closed）")
        records.append({
            "profile_id": pid, "board_id": mid,
            "dataset_id": manifests["kicad"]["dataset_id"],
            "split_role": role,
            "board_path_rel": b["source_rel"],
            "board_declared_sha256": b["source_sha256_before_drc"],
            "ff_plan_rel": f"profiles/{pid}/derived/feedforward-plan.json",
            "registry_rel": f"profiles/{pid}/derived/net-registry.json",
            "manifest_ref": "dataset-manifest-kicad-demos-r1.json",
            "route_check_rel": None,
        })
    # 真实板：调用方传入 route-check 记录（含 profile_id/board_id/
    # dataset_role/reference_route{path,sha256}），按 manifest 归池对账。
    return records


def reconcile_real_board_record(rec: dict, manifests: dict) -> dict:
    """真实板记录与 manifest 对账（pcbench/pcbbm 归池；role 冲突 fail-closed）。

    rec 需含 profile_id/board_id/dataset_role/reference_path（route-check
    的 reference_route.path）；dataset 归池按 path 前缀（datasets/pcbench-r1/
    →pcbench、datasets/pcbbenchmarks-r1/→pcbbm）；board_id 必须在归池
    manifest 的 board_ids 且 role 与 dataset_splits 一致（否则
    CorpusExtError）。
    """
    path = rec["reference_path"]
    if path.startswith("datasets/pcbench-r1/"):
        pool, dskey = "pcbench", "pcbench"
    elif path.startswith("datasets/pcbbenchmarks-r1/"):
        pool, dskey = "pcbbm", "pcbbm"
    else:
        raise CorpusExtError(
            f"{rec['profile_id']}: reference_path {path!r} 不属 pcbench/"
            "pcbbm 数据域（对账 fail-closed）")
    m = manifests[dskey]
    role = None
    for r in ("train", "validation", "holdout"):
        if rec["board_id"] in m["dataset_splits"].get(r, []):
            role = r
            break
    if role is None:
        raise CorpusExtError(
            f"{rec['profile_id']}: board_id {rec['board_id']!r} 不在 {dskey} "
            "manifest dataset_splits 任一侧（对账 fail-closed）")
    if role != rec["dataset_role"]:
        raise CorpusExtError(
            f"{rec['profile_id']}: route-check dataset_role="
            f"{rec['dataset_role']!r} 与 {dskey} manifest 派生 role={role!r} "
            "冲突（对账 fail-closed）")
    if rec["board_id"] not in m["board_ids"]:
        raise CorpusExtError(
            f"{rec['profile_id']}: board_id {rec['board_id']!r} 不在 {dskey} "
            "manifest board_ids（对账 fail-closed）")
    out = dict(rec)
    out["dataset_id"] = m["dataset_id"]
    out["split_role"] = role
    out["manifest_ref"] = ("dataset-manifest-pcbench-r1-v3.json" if pool
                           == "pcbench" else
                           "dataset-manifest-pcbbenchmarks-r1-v3.json")
    return out


# ---------------------------------------------------------------------------
# F1：corpus-r2 记录源（r2 扩档；并列新增路径——build_board_records 与
# reconcile_real_board_record 既有行为零改动）
# ---------------------------------------------------------------------------

#: corpus-r2 板文件路径前缀（datasets 原件域；对账 fail-closed 锚）
CORPUS_R2_PREFIX = "datasets/corpus-r2-r1/"

#: tier_designation → split_role 派生规则（与 G1 profile manifest
#: dataset_splits 快照同派生；枚举外 tier → CorpusExtError 不猜）
CORPUS_R2_TIER_ROLE = {
    "train/val-candidate": "train",
    "holdout-pool": "holdout",
}


def reconcile_corpus_r2_board_record(rec: dict,
                                     dataset_manifest: dict) -> dict:
    """corpus-r2 板记录对账（F1 记录源；纯函数，输入=盘面事实对象）。

    rec 需含 profile_id/board_id/dataset_role/reference_path/
    reference_sha256（消费 route-check 声明件形态：reference_route
    {path,sha256} + dataset_role + corpus_anchor——与 r1 真实板
    reconcile_real_board_record 的 rec 消费形态同构）；
    dataset_manifest=datasets/corpus-r2-r1/manifest.json 解析对象。

    corpus-r2 manifest 形态（F5 实测）：无顶层 dataset_splits/board_ids
    （区别于 pcbench/pcbbm/kicad-r1 manifests）；split 事实=board 级
    tier_designation（CORPUS_R2_TIER_ROLE 派生；validation 侧如实空——
    沿 R14 不占位先例），board 定位=boards[] 逐板 board_id。

    对账 fail-closed（任何不一致 → CorpusExtError，不修复不跳过）：
    - reference_path 前缀必须 datasets/corpus-r2-r1/；
    - board_id 必须在 manifest boards；
    - reference_sha256 == manifest board_file_sha256（字节口径锚）；
    - reference_path == manifest dir+板文件（files 中恰一个 .kicad_pcb）；
    - dataset_role == tier 派生 role（CORPUS_R2_TIER_ROLE）；
    - profile_id 前缀 corpusr2-。

    返回 record（核心键面与 build_board_records/reconcile_real_board_
    record 输出同构；另附 governance 子段=tier/holdout/never_holdout/
    project_group/disposition 原样携带，供批级治理段消费——非 r1 rec
    键面的增量如实披露）。
    """
    pid = rec.get("profile_id")
    mid = rec.get("board_id")
    if not isinstance(pid, str) or not pid.startswith("corpusr2-"):
        raise CorpusExtError(
            f"{pid!r}: corpus-r2 记录 profile_id 必须带 corpusr2- 前缀"
            "（对账 fail-closed）")
    path = rec.get("reference_path")
    if not isinstance(path, str) or not path.startswith(CORPUS_R2_PREFIX):
        raise CorpusExtError(
            f"{pid}: reference_path {path!r} 不属 corpus-r2 数据域"
            f"（前缀 {CORPUS_R2_PREFIX}；对账 fail-closed）")
    board = None
    for b in dataset_manifest.get("boards", []):
        if b.get("board_id") == mid:
            board = b
            break
    if board is None:
        raise CorpusExtError(
            f"{pid}: board_id {mid!r} 不在 corpus-r2-r1 manifest boards"
            "（对账 fail-closed）")
    pcb_files = [f for f in board.get("files", [])
                 if isinstance(f, str) and f.endswith(".kicad_pcb")]
    if len(pcb_files) != 1:
        raise CorpusExtError(
            f"{pid}: board {mid!r} files 中 .kicad_pcb 数 {len(pcb_files)}"
            " != 1（对账 fail-closed）")
    expected_path = CORPUS_R2_PREFIX + board["dir"] + "/" + pcb_files[0]
    if path != expected_path:
        raise CorpusExtError(
            f"{pid}: reference_path {path!r} != manifest 派生板文件 "
            f"{expected_path!r}（对账 fail-closed）")
    ref_sha = rec.get("reference_sha256")
    if ref_sha != board.get("board_file_sha256"):
        raise CorpusExtError(
            f"{pid}: reference_sha256 与 manifest board_file_sha256 不一致"
            f"（对账 fail-closed） {ref_sha!r} != "
            f"{board.get('board_file_sha256')!r}")
    tier = board.get("tier_designation")
    role = CORPUS_R2_TIER_ROLE.get(tier)
    if role is None:
        raise CorpusExtError(
            f"{pid}: tier_designation {tier!r} 不在派生规则枚举 "
            f"{sorted(CORPUS_R2_TIER_ROLE)} 内（不猜 role，fail-closed）")
    if role != rec.get("dataset_role"):
        raise CorpusExtError(
            f"{pid}: route-check dataset_role={rec.get('dataset_role')!r} "
            f"与 manifest tier 派生 role={role!r} 冲突（对账 fail-closed）")
    return {
        "profile_id": pid, "board_id": mid,
        "dataset_id": dataset_manifest.get("dataset_id"),
        "split_role": role,
        "board_path_rel": path,
        "board_declared_sha256": ref_sha,
        "ff_plan_rel": f"profiles/{pid}/derived/feedforward-plan.json",
        "registry_rel": f"profiles/{pid}/derived/net-registry.json",
        "manifest_ref": CORPUS_R2_PREFIX + "manifest.json",
        "route_check_rel": f"profiles/{pid}/route-check.json",
        "governance": {
            "tier_designation": tier,
            "holdout": board.get("holdout"),
            "never_holdout": board.get("never_holdout"),
            "project_group": board.get("project_group"),
            "disposition": board.get("disposition"),
        },
    }
