"""Legacy KiCad 板解析（corpus-r2-r1 转换域外两板；S18 之后的跨板学习线）。

覆盖对象（datasets/corpus-r2-r1/raw/，2026-09-12 实测口径）：
  - OLIMEX__teres-pcb1-a64-main-rev-c/TERES_PCB1-A64-MAIN_Rev.C.kicad_pcb
    （version 20171114，host pcbnew "(2017-11-22 revision 78366f8f0)-master"）
  - OLIMEX__ice40hx1k-evb-rev-b/iCE40HX1K-EVB_Rev_B.kicad_pcb
    （version 4，host pcbnew 4.0.2+dfsg1-stable）

两板的转换门（metadata.conversion_gate）已实测：sexpr_min.parse 可读、
corpus_convert.parse_kicad5_board 如预期拒绝（它只收 20171130）。本模块
返回与 parse_kicad5_board 同构的契约 dict，另加 legacy 事实键（先例=
parse_kicad9_board 的 net_declaration_source/generator_tokens 追加法）：

  - net_declaration_source: "top_level" | "nested_block"
    （两真实板实测均为 top_level；嵌套 (nets ...) 块在两板实测 0 例——
    若出现且子条目为同形 (net N name) 则照读，形态未知即 ValueError
    fail-closed。判据=直接子节点，避免误中 (general (nets 475)) 标量块）；
  - layer_entry_flags: {层号: [多余 token]}——层表条目 (index name type
    [flags...]) 的旗标（实测全部为 "hide"；ice40 16 条、teres 9 条）；
  - module_locked_count: (module X locked ...) 裸 token 计数
    （实测 teres 46 / ice40 1）。

古董版差异实测口径（一切以两板原文为准，先采样后写码）：
  - 层表：条目 3~4 token；v4 板层名可带引号自定义裸名（实测
    "In1(GND).Cu" / "In2(PWR).Cu"）；teres 层 type 含 mixed/power
    （KiCad5 角色映射表之外的取值只记录、不重写）；
  - module 命名（非 footprint）：(module "Lib:Name" [locked] (layer ...) ...)，
    reference 取自 (fp_text reference REF ...)；两板实测无一缺 fp_text
    reference（parse_warnings=0），但图形类 module（LOGO/基准点）实测
    reference 值为空串（teres 10 / ice40 7 例，如
    OLIMEX_Other-FP:Fiducial1x3）——与 parse_kicad5_board 同口径：ref=""
    原样保留、不告警不造名；
  - 网声明：顶层 (net N "NAME")，NAME 引号可选（实测 "(net 1 +5V)" 与
    "(net 3 \\"Net-(ANT1-Pad1)\\")" 并存；net 0 空名 "(net 0 \\"\\")"）；
  - 焊盘：(pad N smd|thru_hole shape (at ...) (size ...) [(drill ...)]
    (layers ...) [(net N NAME)])；drill 可为 (drill oval X Y)（实测
    ice40）；(net N NAME) 的 NAME 引号可选；无 (net ...) 的焊盘=未绑网
    （net=None）。推测形态（如 (net N) 无名焊盘网）本路径不支持——
    len<3 的 pad net 节点如实记 parse_warning 并按未绑网处理，不造名。
    顶层/嵌套 (net N)（len==2，无名编号网）同样：name="" 如实 + warning，
    两板实测 0 例；
  - copper 判定沿用 KiCad4/5 编号 0..31（与 parse_kicad5_board 一致；
    实测 teres 6 铜层 / ice40 4 铜层）。

与 metadata.json 计数的已知口径差异（如实登记，不硬凑断言）：
  - metadata.net_count（teres 285 / ice40 17）= 入库工具正则只数
    【带引号网名】的声明（out/v3-corpus-r2-research/_tools/
    parse_kicad_pcb.py 的 numbered-named 口径）；本解析器数全部顶层
    声明 = teres 475 / ice40 97，与两板 (general (nets ...)) 自声明一致；
  - metadata.layers（ice40=2）为入库正则少计：其层名模式不匹配带引号
    自定义名 "In1(GND).Cu"；本解析器按层表实测 4 铜层。teres 6 一致。

能力边界：纯文本结构级（pcbflow.sexpr_min）；无几何求值/无 DRC/无写回；
零子进程/零网络/零落盘。解析失败 fail-closed（SexprError/ValueError
原样上抛，不猜不造）。
"""

from __future__ import annotations

from . import sexpr_min

#: 版本门：本路径显式支持的 board version token（两块真实板实测全集）
LEGACY_SUPPORTED_VERSIONS = ("20171114", "4")

#: 同构契约键（= parse_kicad5_board 返回键，实测对齐 corpus_convert.py）
CONTRACT_KEYS = (
    "board_version", "host", "general", "layers", "copper_layers",
    "setup", "nets", "modules", "segment_count", "via_count", "arc_count",
    "zone_count", "parse_warnings",
)


def _direct_children(root: list, name: str) -> list:
    return [c for c in root[1:] if isinstance(c, list) and c and c[0] == name]


def _tok(node: list, key: str):
    n = sexpr_min.find_first(node, key)
    if n is None or len(n) < 2:
        return None
    return n[1]


def _toks(node: list, key: str) -> list:
    n = sexpr_min.find_first(node, key)
    if n is None:
        return []
    return [t for t in n[1:] if isinstance(t, str)]


def _int_token(v, what: str) -> int:
    """编号 token → int；非法即 ValueError（fail-closed，不猜）。"""
    if isinstance(v, str) and v.lstrip("-").isdigit():
        return int(v)
    raise ValueError(f"legacy {what}: expect integer token, got {v!r}")


def _parse_legacy_root(root: list, version: str) -> dict:
    """共同核心：两板实测的结构面一致，版本差异只体现在下述已声明的
    形态宽容（引号可选/旗标/locked/oval drill），不分叉逻辑。"""
    host_node = sexpr_min.find_first(root, "host")
    host = " ".join(t for t in host_node[1:] if isinstance(t, str)) \
        if host_node else None

    general = {}
    g = sexpr_min.find_first(root, "general")
    if g is not None:
        for c in g[1:]:
            if isinstance(c, list) and len(c) == 2:
                general[c[0]] = c[1]

    layers = []
    layer_flags: dict = {}
    for lyr_block in _direct_children(root, "layers"):
        for c in lyr_block[1:]:
            if not (isinstance(c, list) and len(c) >= 3):
                continue
            idx = _int_token(c[0], "layer entry index")
            layers.append({"index": idx, "name": c[1], "type": c[2]})
            extra = [x for x in c[3:] if isinstance(x, str)]
            if extra:
                layer_flags[idx] = extra
    copper = [l for l in layers if 0 <= l["index"] <= 31]

    setup = {}
    s = sexpr_min.find_first(root, "setup")
    if s is not None:
        for c in s[1:]:
            if isinstance(c, list) and len(c) == 2 and isinstance(c[1], str):
                setup[c[0]] = c[1]

    # 网声明：顶层 (net N NAME)（两板实测）；或直接子节点 (nets ...) 嵌套块
    # （实测 0 例；子条目只接受同形 (net N NAME)，其余 fail-closed）。
    warnings: list = []

    def _net_entry(n: list) -> dict:
        if len(n) >= 3:
            return {"net_id": _int_token(n[1], "net id"), "name": n[2]}
        # (net N) 无名编号网：网存在、名字结构性为空——如实 name=""
        # + warning，不造名（两真实板实测 0 例）
        nid = _int_token(n[1], "net id")
        warnings.append(f"net_declaration_without_name:{nid}")
        return {"net_id": nid, "name": ""}

    nets_nested = _direct_children(root, "nets")
    nets = []
    if nets_nested:
        net_src = "nested_block"
        for blk in nets_nested:
            for n in blk[1:]:
                # 嵌套块形态未见于任何真实板——只接受同形 (net N "NAME")，
                # 其余（含无名 (net N)）一律 fail-closed，不猜
                if not (isinstance(n, list) and len(n) >= 3 and n[0] == "net"
                        and isinstance(n[1], str) and n[1].isdigit()
                        and isinstance(n[2], str)):
                    raise ValueError(
                        f"legacy net declaration not parseable: {n!r}")
                nets.append({"net_id": int(n[1]), "name": n[2]})
    else:
        net_src = "top_level"
        for n in _direct_children(root, "net"):
            nets.append(_net_entry(n))
    nets.sort(key=lambda x: x["net_id"])

    modules = []
    locked_count = 0
    for m in sexpr_min.find_all(root, "module"):
        if len(m) > 2 and m[2] == "locked":
            locked_count += 1
        lib = m[1] if len(m) > 1 and isinstance(m[1], str) else None
        ref = None
        for ft in sexpr_min.find_all(m, "fp_text"):
            if len(ft) > 2 and ft[1] == "reference":
                ref = ft[2]
                break
        if ref is None:
            warnings.append(f"module_without_reference:{lib}")
            ref = f"__NOREF__{len(modules):03d}"
        pads = []
        for p in sexpr_min.find_all(m, "pad"):
            net_node = sexpr_min.find_first(p, "net")
            net = None
            if net_node is not None:
                if len(net_node) >= 3:
                    net = {"net_id": _int_token(net_node[1], "pad net id"),
                           "name": net_node[2]}
                else:
                    warnings.append(
                        f"pad_net_without_name:{ref}.{p[1]}")
            pads.append({
                "name": p[1], "type": p[2], "shape": p[3],
                "at": _toks(p, "at"), "size": _toks(p, "size"),
                "drill": _toks(p, "drill") or None,
                "layers": _toks(p, "layers"), "net": net,
            })
        modules.append({
            "lib": lib, "ref": ref,
            "layer": _tok(m, "layer"), "at": _toks(m, "at"),
            "pads": pads,
        })
    modules.sort(key=lambda x: x["ref"])

    return {
        "board_version": version, "host": host, "general": general,
        "layers": layers, "copper_layers": copper, "setup": setup,
        "nets": nets, "modules": modules,
        "segment_count": len(sexpr_min.find_all(root, "segment")),
        "via_count": len(sexpr_min.find_all(root, "via")),
        "arc_count": len(sexpr_min.find_all(root, "arc")),
        "zone_count": len(sexpr_min.find_all(root, "zone")),
        "parse_warnings": warnings,
        "net_declaration_source": net_src,
        "layer_entry_flags": layer_flags,
        "module_locked_count": locked_count,
    }


def parse_legacy_board(text: str) -> dict:
    """Legacy KiCad 板文本（version 20171114 / "4"）→ 结构模型 dict。

    按 version token 分派（显式版本门 LEGACY_SUPPORTED_VERSIONS）；
    20171130 归 parse_kicad5_board、k9 token 归 parse_kicad9_board，
    三门互斥。返回 dict 与 parse_kicad5_board 同构（CONTRACT_KEYS），
    另加 legacy 事实键（见模块 docstring 实测口径）。
    解析失败 fail-closed（SexprError/ValueError 原样上抛，不猜不造）。
    """
    top = sexpr_min.parse(text)
    roots = [n for n in top if isinstance(n, list) and n and n[0] == "kicad_pcb"]
    if len(roots) != 1:
        raise ValueError(f"expect exactly one kicad_pcb root, got {len(roots)}")
    root = roots[0]
    version = _tok(root, "version")
    if version == "20171114":
        return _parse_legacy_root(root, version)
    if version == "4":
        return _parse_legacy_root(root, version)
    raise ValueError(
        f"board version {version!r} outside legacy gate "
        f"{list(LEGACY_SUPPORTED_VERSIONS)} (20171130 uses "
        f"parse_kicad5_board; k9 tokens use parse_kicad9_board)")
