"""TL-5 第二包：真实板 → 非 Rev-C profile 转换（TD8 conversion_script）。

输入：datasets/ 下 KiCad 5.1.4（board version 20171130）.kicad_pcb 文本
（unrouted 状态=设计起点；routed 状态=回测参考，只读 hash 绑定）。
本模块产出（全部纯内存对象/文本；落盘由编排侧完成）：

  - parse_kicad5_board：KiCad5 板文本 → 结构模型（层/网/封装/焊盘本质，
    数值保留源文本字面量，不浮点重排）；
  - normalized_board_text：规范化板文本（pcbflow 剖面方言：KiCad6 术语
    footprint；确定性 byte-exact，可从同一源重放）；
  - stackup / constraints / net-registry / audit / feedforward-plan 构件
    （compile/enum/audit/feedforward 段的 corpus 级证据）；
  - profile / manifest / graph 内容与 topology group id、conversion log。

诚实边界（不虚构，SPEC TD8/L7）：
  - critical nets/约束只从网名约定表推导（basis=net_name_convention，
    名字级启发非电气真值）；数值容差类字段不可从板文本判定 → 不生成
    对应约束/阈值；
  - anchors、via cost、长度匹配容差等 router 参数不可判定 → 显式留空
    并登记 field_missingness；
  - route/check 段不在此伪造：v1.x route/check 引擎硬连 Rev-C 输入
    （config.py 冻结=红线），v3 轨道尚无引擎——由 TL-5-G gate 如实
    blocked（缺证据闭门），本模块只产 corpus 级段证据。

生成器纪律：纯函数、零子进程、零自身落盘、零网络、零 wall-clock
（conversion_date 为声明常量）、零主机路径（source 引用一律仓库相对
POSIX）；JSON 输出一律 canonical（hashing.json_dumps）。
"""

from __future__ import annotations

import json

from . import hashing, sexpr_min

TRACK = "tl5-convert-r1"
MODULE_NAME = "pcbflow.corpus_convert"

#: 转换声明日期（人工会话声明，非机器 wall-clock）
CONVERSION_DATE = "2026-09-03"

#: 网名约定表（名字级启发；推导结果必须带 basis 声明）
POWER_RAIL_NAMES = ("GND", "+5V", "+3V3", "3.3V", "VIN", "VBUS", "VBAT",
                    "USBVCC", "PWRIN", "VDD", "VCC")
DIFF_PAIR_NAMES = (("D+", "D-"), ("USB_DP", "USB_DM"), ("/USBD+", "/USBD-"),
                   ("USB_P", "USB_N"), ("/DP", "/DM"))

#: KiCad5 封装内未命名网前缀（Eagle/网表生成器惯例）
_UNNAMED_PREFIXES = ("N$", "Net-(")

_KICAD5_BOARD_VERSION = "20171130"


def _direct_children(root: list, name: str) -> list:
    return [c for c in root[1:] if isinstance(c, list) and c and c[0] == name]


def _tok(node: list, key: str):
    """取子节点 (key v...) 的值叶子（无则 None）。"""
    n = sexpr_min.find_first(node, key)
    if n is None or len(n) < 2:
        return None
    return n[1]


def _toks(node: list, key: str) -> list:
    n = sexpr_min.find_first(node, key)
    if n is None:
        return []
    return [t for t in n[1:] if isinstance(t, str)]


# ---------------------------------------------------------------------------
# 1. KiCad5 板解析（text-level；数值字面量保留）
# ---------------------------------------------------------------------------

def parse_kicad5_board(text: str) -> dict:
    """KiCad 5.x .kicad_pcb 文本 → 结构模型 dict（纯函数）。

    能力边界：文本结构级（sexpr_min；无几何求值/无 DRC/无写回）。
    解析失败 fail-closed（SexprError/ValueError 原样上抛，不猜）。
    """
    top = sexpr_min.parse(text)
    roots = [n for n in top if isinstance(n, list) and n and n[0] == "kicad_pcb"]
    if len(roots) != 1:
        raise ValueError(f"expect exactly one kicad_pcb root, got {len(roots)}")
    root = roots[0]
    version = _tok(root, "version")
    if version != _KICAD5_BOARD_VERSION:
        raise ValueError(
            f"expect board version {_KICAD5_BOARD_VERSION} (KiCad 5.x), "
            f"got {version!r}")
    # root 级查询索引（align-r1 2026-09-25）：一次遍历替代多次全树走查；
    # 索引值与逐次 find_all/find_first(root, k) 逐位一致（pre-order 同序）。
    idx = sexpr_min.build_index(root)
    host_node = sexpr_min.index_first(idx, "host")
    host = " ".join(t for t in host_node[1:] if isinstance(t, str)) \
        if host_node else None

    general = {}
    g = sexpr_min.index_first(idx, "general")
    if g is not None:
        for c in g[1:]:
            if isinstance(c, list) and len(c) == 2:
                general[c[0]] = c[1]

    layers = []
    for lyr_block in _direct_children(root, "layers"):
        for c in lyr_block[1:]:
            if isinstance(c, list) and len(c) >= 3:
                # KiCad5 层表条目形如 (0 Top signal)——首 token=层号
                layers.append({"index": int(c[0]), "name": c[1],
                               "type": c[2] if len(c) > 2 else "signal"})
    copper = [l for l in layers if 0 <= l["index"] <= 31]

    setup = {}
    s = sexpr_min.index_first(idx, "setup")
    if s is not None:
        for c in s[1:]:
            if isinstance(c, list) and len(c) == 2 and isinstance(c[1], str):
                setup[c[0]] = c[1]

    nets = []
    for n in _direct_children(root, "net"):
        if len(n) >= 3:
            nets.append({"net_id": int(n[1]), "name": n[2]})
    nets.sort(key=lambda x: x["net_id"])

    modules = []
    warnings = []
    for m in sexpr_min.index_all(idx, "module"):
        ref = None
        for ft in sexpr_min.find_all(m, "fp_text"):
            if len(ft) > 2 and ft[1] == "reference":
                ref = ft[2]
                break
        if ref is None:
            warnings.append(f"module_without_reference:{m[1]}")
            ref = f"__NOREF__{len(modules):03d}"
        pads = []
        for p in sexpr_min.find_all(m, "pad"):
            net_node = sexpr_min.find_first(p, "net")
            net = None
            if net_node is not None and len(net_node) >= 3:
                net = {"net_id": int(net_node[1]), "name": net_node[2]}
            pads.append({
                "name": p[1], "type": p[2], "shape": p[3],
                "at": _toks(p, "at"), "size": _toks(p, "size"),
                "drill": _toks(p, "drill") or None,
                "layers": _toks(p, "layers"), "net": net,
            })
        modules.append({
            "lib": m[1], "ref": ref,
            "layer": _tok(m, "layer"), "at": _toks(m, "at"),
            "pads": pads,
        })
    modules.sort(key=lambda x: x["ref"])

    return {
        "board_version": version, "host": host, "general": general,
        "layers": layers, "copper_layers": copper, "setup": setup,
        "nets": nets, "modules": modules,
        "segment_count": len(sexpr_min.index_all(idx, "segment")),
        "via_count": len(sexpr_min.index_all(idx, "via")),
        "arc_count": len(sexpr_min.index_all(idx, "arc")),
        "zone_count": len(sexpr_min.index_all(idx, "zone")),
        "parse_warnings": warnings,
    }


def board_denominators(model: dict) -> dict:
    """真实分母：网/命名网/封装/焊盘/焊盘明细（如实计数）。"""
    pads = [p for m in model["modules"] for p in m["pads"]]
    named = [n for n in model["nets"] if n["name"] != ""]
    return {
        "net_count": len(model["nets"]),
        "named_net_count": len(named),
        "module_count": len(model["modules"]),
        "pad_count": len(pads),
        "pad_thru_hole_count": sum(1 for p in pads if p["type"] == "thru_hole"),
        "pad_smd_count": sum(1 for p in pads if p["type"] == "smd"),
        "pad_without_net_count": sum(1 for p in pads if p["net"] is None),
        "copper_layer_count": len(model["copper_layers"]),
    }


# ---------------------------------------------------------------------------
# 2. 规范化板文本（确定性；同一源 byte-exact 可重放）
# ---------------------------------------------------------------------------

def _q(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def normalized_board_text(model: dict, *, source_path: str,
                          source_sha256: str) -> str:
    """规范化板文本（pcbflow 剖面方言；数值=源文本字面量）。

    保留：层名/类型、网声明（含空名网 0）、封装 ref/lib/layer/at、
    焊盘 name/type/shape/at/size/drill/layers/net。
    丢弃（计入 conversion_log）：fp_text 值文本、fp_* 图形、zones、
    drawings、setup 细参（最小值另入 stackup）、routed 段/过孔。
    """
    if not isinstance(source_sha256, str) or len(source_sha256) != 64:
        raise ValueError("source_sha256 required (64 hex)")
    out = []
    out.append(f"(kicad_pcb (version {model['board_version']}) "
               f"(generator {_q('pcbflow-corpus-convert-r1')})")
    out.append(f"  (source (path {_q(source_path)}) "
               f"(sha256 {_q(source_sha256)}))")
    g = model["general"]
    out.append(f"  (general (thickness {g.get('thickness', 'null')}) "
               f"(modules {g.get('modules', len(model['modules']))}) "
               f"(nets {g.get('nets', len(model['nets']))}))")
    for l in model["copper_layers"]:
        out.append(f"  (layer {_q(l['name'])} (index {l['index']}) "
                   f"(type {_q(l['type'])}))")
    for n in model["nets"]:
        out.append(f"  (net {n['net_id']} {_q(n['name'])})")
    for m in model["modules"]:
        at = " ".join(m["at"])
        out.append(f"  (footprint {_q(m['ref'])} (lib {_q(m['lib'])}) "
                   f"(layer {_q(m['layer'])}) (at {at})")
        for p in m["pads"]:
            parts = [f"    (pad {_q(p['name'])} {p['type']} {p['shape']}",
                     f"(at {' '.join(p['at'])})",
                     f"(size {' '.join(p['size'])})"]
            if p["drill"]:
                parts.append(f"(drill {' '.join(p['drill'])})")
            parts.append("(layers "
                         + " ".join(_q(x) for x in p["layers"]) + ")")
            if p["net"]:
                parts.append(f"(net {p['net']['net_id']} "
                             f"{_q(p['net']['name'])})")
            out.append(" ".join(parts) + ")")
        out.append("  )")
    out.append(")")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# 3. 约定表推导（critical nets / diff pairs——名字级启发，如实 basis）
# ---------------------------------------------------------------------------

def derive_critical_nets(model: dict) -> dict:
    net_names = {n["name"] for n in model["nets"]}
    rails = sorted(n for n in POWER_RAIL_NAMES if n in net_names)
    pairs = []
    for a, b in DIFF_PAIR_NAMES:
        if a in net_names and b in net_names:
            pairs.append(sorted([a, b]))
    pairs.sort()
    return {
        "power_rails": rails,
        "diff_pairs": pairs,
        "critical_nets": sorted(set(rails) | {x for p in pairs for x in p}),
        "basis": "net_name_convention（POWER_RAIL_NAMES/DIFF_PAIR_NAMES "
                 "精确名匹配；名字级启发，非电气真值）",
        "not_determinable_from_board_text": [
            "length_match 容差（无原理图/规范源）",
            "时钟网（无原理图 net class）",
            "anchor 器件（布局冻结集属项目决策）",
            "via cost / router 权重（路由器参数非板属性）",
            "critical_net_return 参考平面（两板均无 plane 层，不可声明 "
            "unbroken_reference）",
        ],
    }


def build_constraints_obj(model: dict, *, project_id: str,
                          crit: dict) -> dict:
    """约束构件：只生成参数可从板文本判定的约束种类（diff_pair，规则名
    无数值容差）；不可判定种类显式列入 not_generated。"""
    entries = []
    for i, (a, b) in enumerate(crit["diff_pairs"], start=1):
        entries.append({
            "id": f"C-DP-{i:03d}", "kind": "diff_pair", "nets": [a, b],
            "rule": "intra_pair_gap_le_track_width",
            "basis": "net_name_convention",
        })
    return {
        "schema_version": "3.0", "artifact_kind": "constraints",
        "project_id": project_id, "entries": entries,
        "not_generated": {
            "length_match": "tolerance_mm 不可从板文本判定（不虚构数值）",
            "critical_net_return": "无 plane 层参考可声明（两板 "
                                   "Top/Bottom 均 type signal）",
        },
        "producer": MODULE_NAME, "track": TRACK,
        "authority": "corpus_conversion_first_order",
    }


# ---------------------------------------------------------------------------
# 4. stackup / net-registry / audit / feedforward 构件
# ---------------------------------------------------------------------------

def _num(setup: dict, key: str):
    v = setup.get(key)
    return float(v) if v is not None else None


def build_stackup_obj(model: dict, *, board_id: str,
                      source: dict) -> dict:
    return {
        "schema_version": "3.0", "artifact_kind": "stackup",
        "board_id": board_id,
        "thickness_mm": float(model["general"].get("thickness", "nan")),
        "copper_layers": [{"index": l["index"], "name": l["name"],
                           "type": l["type"]}
                          for l in model["copper_layers"]],
        "non_copper_layer_count": len(model["layers"])
        - len(model["copper_layers"]),
        "setup_mins": {
            "trace_min_mm": _num(model["setup"], "trace_min"),
            "trace_clearance_mm": _num(model["setup"], "trace_clearance"),
            "via_size_mm": _num(model["setup"], "via_size"),
            "via_drill_mm": _num(model["setup"], "via_drill"),
            "via_min_size_mm": _num(model["setup"], "via_min_size"),
            "via_min_drill_mm": _num(model["setup"], "via_min_drill"),
        },
        "source": source, "producer": MODULE_NAME, "track": TRACK,
        "authority": "corpus_conversion_first_order（setup 最小值=板内声明，"
                     "非规范条款）",
    }


def classify_net(name: str, crit: dict) -> str:
    if name == "":
        return "empty"
    if name.startswith(_UNNAMED_PREFIXES):
        return "unnamed"
    if name in crit["power_rails"]:
        return "power_rail"
    if any(name in p for p in crit["diff_pairs"]):
        return "diff_pair_member"
    return "signal"


def build_net_registry_obj(model: dict, *, board_id: str,
                           crit: dict) -> dict:
    """逐网注册表（enum 段证据）：net_id/name/分类/焊盘数/成员 ref.pad。

    成员分组双口径（r2 待决①手术；按档同判，fail-closed 纪律不变）：
    - id 档（top_level/嵌套声明；含 k5 与 legacy）：按 p["net"]["net_id"]
      分组（既有口径零改动）；
    - pad_derived（20260206+，net_declaration_source=="pad_derived"，
      net_id 结构性 None 不虚构）：按 p["net"]["name"] 分组——原按 net_id
      分组时全部绑网 pad 落 None 单桶、每网 pad_count=全部绑网 pad 数
      （r1 kicaddemo-pic_programmer 实证失准：每网 236、sum=26196≠真实；
      G1-REPORT §8 待决① 登记）。口径变化披露：r1 盘上产物为冻结件不
      回写，r2 期起新产物用新口径；pad_derived 板的空名绑网 pad（net
      token=""）不入任何网账（nets 推导源不含空名，与 parse_kicad9_
      board pad_net_names 口径一致）。
    """
    pad_derived = model.get("net_declaration_source") == "pad_derived"

    def _group_key(net_ref: dict):
        return net_ref["name"] if pad_derived else net_ref["net_id"]

    members: dict = {}
    for m in model["modules"]:
        for p in m["pads"]:
            if p["net"]:
                members.setdefault(_group_key(p["net"]), []).append(
                    f"{m['ref']}.{p['name']}")
    nets = []
    for n in model["nets"]:
        refs = sorted(members.get(_group_key(n), []))
        nets.append({
            "net_id": n["net_id"], "name": n["name"],
            "classification": classify_net(n["name"], crit),
            "pad_count": len(refs), "member_refs": refs,
        })
    return {
        "schema_version": "3.0", "artifact_kind": "net_registry",
        "board_id": board_id,
        "net_count": len(nets),
        "named_net_count": sum(1 for n in nets if n["name"] != ""),
        "unnamed_net_count": sum(1 for n in nets
                                 if n["classification"] == "unnamed"),
        "nets": nets,
        "producer": MODULE_NAME, "track": TRACK,
        "authority": "corpus_conversion_first_order",
    }


def build_audit_obj(model_u: dict, model_r: dict, *, board_id: str) -> dict:
    """audit 段证据（corpus 级真实检查；非 v1.x FA3 引擎——该引擎硬连
    Rev-C 输入，不可用于非 Rev-C 板）。全部检查从两态模型实算。"""
    checks = []
    checks.append({
        "id": "unrouted_state_pristine",
        "pass": (model_u["segment_count"] == 0 and model_u["via_count"] == 0
                 and model_u["arc_count"] == 0
                 and model_u["general"].get("tracks") == "0"),
        "evidence": f"unrouted segments={model_u['segment_count']} "
                    f"vias={model_u['via_count']} arcs={model_u['arc_count']} "
                    f"general.tracks={model_u['general'].get('tracks')}",
    })
    nets_u = [n["net_id"] for n in model_u["nets"]]
    nets_r = [n["net_id"] for n in model_r["nets"]]
    refs_u = sorted(m["ref"] for m in model_u["modules"])
    refs_r = sorted(m["ref"] for m in model_r["modules"])
    checks.append({
        "id": "unrouted_routed_same_board_identity",
        "pass": nets_u == nets_r and refs_u == refs_r,
        "evidence": f"net_ids_equal={nets_u == nets_r} "
                    f"module_refs_equal={refs_u == refs_r}",
    })
    declared = {n["net_id"] for n in model_u["nets"]}
    bad_net_pads = []
    pads = [(m["ref"], p) for m in model_u["modules"] for p in m["pads"]]
    for ref, p in pads:
        if p["net"] and p["net"]["net_id"] not in declared:
            bad_net_pads.append(f"{ref}.{p['name']}")
    checks.append({
        "id": "pads_bound_to_declared_nets",
        "pass": not bad_net_pads,
        "evidence": f"pad_net_refs_outside_declaration="
                    f"{len(bad_net_pads)}",
    })
    per_net: dict = {}
    for ref, p in pads:
        if p["net"]:
            per_net[p["net"]["name"]] = per_net.get(p["net"]["name"], 0) + 1
    zero_pad = sorted(n["name"] for n in model_u["nets"]
                      if n["name"] != "" and per_net.get(n["name"], 0) == 0)
    single_pad = sum(1 for n in model_u["nets"]
                     if n["name"] != "" and per_net.get(n["name"], 0) == 1)
    checks.append({
        "id": "named_nets_have_pad_binding",
        "pass": not zero_pad,
        "evidence": f"zero_pad_named_nets={len(zero_pad)} "
                    f"single_pad_named_nets={single_pad}（单焊盘命名网="
                    f"no-connect 引脚常态，如实计数不判失败）",
    })
    no_geom = [f"{ref}.{p['name']}" for ref, p in pads
               if not p["at"] or not p["size"]]
    checks.append({
        "id": "pad_geometry_present",
        "pass": not no_geom,
        "evidence": f"pads_without_at_or_size={len(no_geom)}",
    })
    denom_u = board_denominators(model_u)
    denom_r = board_denominators(model_r)
    return {
        "schema_version": "3.0", "artifact_kind": "audit_report",
        "board_id": board_id,
        "denominators_unrouted": denom_u,
        "denominators_routed": denom_r,
        "routed_reference": {
            "segment_count": model_r["segment_count"],
            "via_count": model_r["via_count"],
            "arc_count": model_r["arc_count"],
        },
        "checks": checks,
        "result": "pass" if all(c["pass"] for c in checks) else "fail",
        "producer": MODULE_NAME, "track": TRACK,
        "authority": "corpus_conversion_first_order（结构级事实检查；"
                     "非 v1.x FA3 可布性引擎、非 DRC）",
    }


def build_feedforward_obj(model: dict, *, board_id: str,
                          crit: dict) -> dict:
    """feedforward 段证据（corpus 级资源账本：rail 扇出+信号层焊盘负载；
    authority=corpus_conversion planning 级，非 v1.x FF1 引擎）。"""
    rails = []
    for name in crit["power_rails"]:
        net = next((n for n in model["nets"] if n["name"] == name), None)
        if net is None:
            continue
        pads = [f"{m['ref']}.{p['name']}" for m in model["modules"]
                for p in m["pads"]
                if p["net"] and p["net"]["net_id"] == net["net_id"]]
        rails.append({"net": name, "pad_count": len(pads),
                      "member_refs": sorted(pads)})
    layer_load = []
    for l in model["copper_layers"]:
        cnt = sum(1 for m in model["modules"] for p in m["pads"]
                  if any(x == l["name"] or x == "*.Cu"
                         for x in p["layers"]))
        layer_load.append({"layer": l["name"], "pad_count": cnt})
    return {
        "schema_version": "3.0", "artifact_kind": "feedforward_plan",
        "board_id": board_id,
        "plan_id": f"FF-CORPUS-{board_id.upper()}-0001",
        "rails": rails,
        "signal_layer_pad_load": layer_load,
        "not_modelled": [
            "电流预算/线宽推导（无原理图电流源，不虚构）",
            "via 预算（无路由器执行）",
            "impedance targets（无叠层介质参数）",
        ],
        "producer": MODULE_NAME, "track": TRACK,
        "authority": "corpus_conversion_first_order（planning_advisory 级）",
    }


# ---------------------------------------------------------------------------
# 5. topology group / profile / manifest / graph / conversion log
# ---------------------------------------------------------------------------

def topology_group_id(model: dict, crit: dict) -> str:
    """拓扑分组 id（一阶计数口径，与 corpus.topology_signature 同级；
    非图同构——V3-MATRIX 偏差 D11 措辞沿用）。"""
    d = board_denominators(model)
    diff = "-usb-diffpair" if crit["diff_pairs"] else "-no-diffpair"
    return (f"cu{d['copper_layer_count']}-{d['named_net_count']}net-"
            f"{d['module_count']}mod-{d['pad_count']}pad{diff}")


def build_profile_obj(model: dict, *, profile_id: str, project_id: str,
                      crit: dict) -> dict:
    """profile.json 内容（严格贴合 schemas.profile：additionalProperties
    false——转换 provenance 不入 profile，入 conversion_log/dataset manifest）。

    层角色映射（如实）：KiCad type signal→signal、power→power、
    mixed/jumper→signal（无 plane 类型出现在两真实板）。"""
    role_map = {"signal": "signal", "power": "power", "mixed": "signal",
                "jumper": "signal"}
    setup = model["setup"]
    thresholds = {
        "min_track_width_mm": _num(setup, "trace_min"),
        "min_clearance_mm": _num(setup, "trace_clearance"),
        "via_min_size_mm": _num(setup, "via_min_size"),
        "via_min_drill_mm": _num(setup, "via_min_drill"),
    }
    # 不可判定（setup 缺项）→ 整键不生成（thresholds 值域禁 null，不虚构）
    thresholds = {k: v for k, v in thresholds.items() if v is not None}
    return {
        "schema_version": "3.0", "profile_id": profile_id,
        "project_id": project_id,
        "layers": [{"name": l["name"], "role": role_map.get(l["type"],
                                                            "signal")}
                   for l in model["copper_layers"]],
        "kicad_cli": {
            "drc_batch_severity": "severity-error",
            "drc_final_severity": "severity-all",
            "refill_policy": "none",
        },
        "critical_net_set": crit["critical_nets"],
        "physics_required": [],
        "external_required": [],
        "bring_up_required": False,
        "measurement_conventions": None,
        "thresholds": thresholds,
        "anchors": [],
        "keepouts": [],
    }


def build_manifest_obj(*, project_id: str, profile_id: str,
                       eda_version: str, critical_nets: list,
                       dataset_splits: dict, output_root: str,
                       board_id: str, dataset_routed_rel: str,
                       drc_baseline_rel: str) -> dict:
    """manifest.json 内容（schemas.project_manifest 严格贴合）。

    backtest.reference_route=数据集 routed 态只读引用（hash 绑定）；
    backtest.drc_baseline=编排侧 kicad-cli 产物引用（生成先行，context
    只读哈希）。
    """
    return {
        "schema_version": "3.0", "project_id": project_id,
        "profile_id": profile_id,
        "eda": {"name": "kicad", "version": eda_version},
        "inputs": {
            "board": "inputs/board.kicad_pcb",
            "schematic": None, "netlist": None, "placement": None,
            "stackup": "inputs/stackup.json",
            "constraints": "inputs/constraints.json",
            "structures": None,
            "toolchain_lock": "../../toolchain_lock.json",
            "identity_map": None,
        },
        "backtest": {
            "opens": None, "reference_layout": None,
            "reference_route": dataset_routed_rel,
            "drc_baseline": drc_baseline_rel,
            "datasets": None,
        },
        "policy": {"profile": None, "core_policy": None,
                   "feedforward_policy": None, "optimization_policy": None,
                   "model_policy": None},
        "external_authority": {"impedance": None, "si": None, "pi": None,
                               "thermal": None, "emc": None, "dfm": None},
        "params": [],
        "critical_nets": critical_nets,
        "dataset_splits": dataset_splits,
        "outputs": {"root": output_root, "preserve_history": True},
        "toolchain": {
            "lock_path": "../../toolchain_lock.json",
            "executable_allowlist": ["kicad-cli"],
            "backend_declarations": [],
        },
        "path_base": "manifest_dir",
        "compatibility": {"mode": "explicit_manifest", "warning": False},
    }


def build_graph_spec(*, project_id: str, profile_id: str, revision: str,
                     file_hashes: dict) -> dict:
    """graph.json 内容。真实盘上节点（board/stackup/constraints/net_registry/
    audit_report/feedforward_plan）带实算 sha256；decision_ledger/
    gate_records 为声明节点（path=null，与 smoke 口径一致）。

    stage 全序合法：compile(constraints) < enum(net_registry) <
    audit(audit_report) < feedforward(feedforward_plan) < ledger < gate。
    route/check 段不出现为 present 节点（无引擎可产证据；TL-5-G 以
    missing input 如实 blocked，不在图内凑 present）。
    """
    def node(aid, kind, path, stage, inputs):
        return {
            "artifact_id": aid, "kind": kind, "path": path,
            "sha256": file_hashes[path], "status": "present",
            "revision": revision, "stage_label": stage, "inputs": inputs,
        }
    return {
        "schema_version": "3.0", "artifact_kind": "artifact_graph_spec",
        "project_id": project_id, "profile_id": profile_id,
        "revision": revision,
        "nodes": [
            node("board", "board", "inputs/board.kicad_pcb", None, []),
            node("stackup", "stackup", "inputs/stackup.json", None, []),
            node("constraints", "constraints", "inputs/constraints.json",
                 "compile", []),
            node("net_registry", "net_registry", "derived/net-registry.json",
                 "enum", ["board", "constraints"]),
            node("audit_report", "audit_report", "derived/audit.json",
                 "audit", ["board", "net_registry"]),
            node("feedforward_plan", "feedforward_plan",
                 "derived/feedforward-plan.json", "feedforward",
                 ["net_registry", "audit_report"]),
            {
                "artifact_id": "decision_ledger", "kind": "decision_ledger",
                "path": None, "sha256": None, "status": "present",
                "revision": revision, "stage_label": "ledger",
                "inputs": ["feedforward_plan"],
            },
            {
                "artifact_id": "gate_records", "kind": "gate_record",
                "path": None, "sha256": None, "status": "present",
                "revision": revision, "stage_label": "gate",
                "inputs": ["decision_ledger"],
            },
        ],
    }


def build_conversion_log(*, board_id: str, module_sha256: str,
                         inputs: list, outputs: list, model_u: dict,
                         model_r: dict, crit: dict, topology_group: str) -> dict:
    """conversion_log（TD8 字段）：输入/输出 hash 绑定+保留/丢弃决策+
    field_missingness+确定性声明。纯函数；hashes 由编排侧实算注入。"""
    dropped = {
        "fp_text_value_and_graphics": "fp_text 值文本/fp_poly/fp_line 等"
                                      "图形不进规范化板（计数见 parsed）",
        "zones": f"unrouted zones={model_u['zone_count']}（两板均为 0）",
        "setup_detail": "setup 细参只留最小值集（进 stackup.setup_mins）",
        "routed_geometry": f"routed segments={model_r['segment_count']} "
                           f"vias={model_r['via_count']} 不进规范化板"
                           f"（routed 态以 manifest.backtest.reference_route "
                           f"hash 绑定为回测参考）",
        "non_copper_layers": "非铜层（ silk/mask/user 等）不进规范化板"
                             "（计数入 stackup.non_copper_layer_count）",
    }
    return {
        "track": TRACK, "conversion_date": CONVERSION_DATE,
        "board_id": board_id,
        "module": MODULE_NAME, "module_sha256": module_sha256,
        "inputs": inputs, "outputs": outputs,
        "retained": [
            "copper layer name/index/type", "net declarations (id+name)",
            "footprint ref/lib/layer/at", "pad name/type/shape/at/size/"
            "drill/layers/net",
        ],
        "dropped": dropped,
        "convention_basis": crit["basis"],
        "field_missingness": {
            "anchors": "not_determinable（布局冻结集属项目决策，板文本无据）",
            "via_cost": "not_determinable（router 参数非板属性）",
            "length_match_tolerance": "not_determinable（无原理图/规范源）",
            "physics_required": "not_determinable（无介质参数/电流源）",
            "params": "空（搜索域不可从板文本判定）",
        },
        "parse_warnings": model_u["parse_warnings"]
        + model_r["parse_warnings"],
        "topology_group": topology_group,
        "determinism_claim": "pure function of source text; byte-exact "
                             "replay（数值保留源字面量；canonical JSON）",
    }


def dumps_canonical(obj) -> str:
    """编排侧统一出口：canonical JSON 文本（零落盘由调用方保证）。"""
    return hashing.json_dumps(obj)


# ---------------------------------------------------------------------------
# 6. 逐 profile 报告（TD8 门定义：denominator/quality/限制/holdout/
#    leakage audit/source hash；事实全部由编排侧实跑注入，本函数只装配）
# ---------------------------------------------------------------------------

#: 主路径段与证据口径（route/check=不可执行段的如实登记，非凑门）
MAIN_PATH_STAGES = (
    "manifest", "compile", "enum", "audit", "feedforward", "route_check",
)


def build_profile_report(*, board_id: str, profile_id: str,
                         dataset_role: str, denominators: dict,
                         quality: dict, limits: list, leakage_audit_ref: dict,
                         source: dict, main_path: dict) -> dict:
    """TD8 逐 profile 报告（纯装配；字段缺一即 ValueError，不静默）。

    main_path: {stage: {status: executed|not_executed, evidence: str,
    authority: str}}——status 由编排侧按实跑结果填入（v3cli exit code /
    产物 hash），不得在此伪造。
    """
    for stage in MAIN_PATH_STAGES:
        if stage not in main_path:
            raise ValueError(f"main_path missing stage: {stage}")
        ent = main_path[stage]
        if ent.get("status") not in ("executed", "not_executed"):
            raise ValueError(f"main_path[{stage}].status 非法: "
                             f"{ent.get('status')!r}")
        if not isinstance(ent.get("evidence"), str) or not ent["evidence"]:
            raise ValueError(f"main_path[{stage}].evidence 必填")
    for key in ("net_count", "named_net_count", "module_count", "pad_count"):
        if key not in denominators:
            raise ValueError(f"denominators missing: {key}")
    if dataset_role not in ("train", "validation", "holdout",
                            "external_eval"):
        raise ValueError(f"dataset_role 非法: {dataset_role!r}")
    holdout = {
        "role": dataset_role,
        "frozen_readonly": dataset_role in ("holdout", "external_eval"),
        "note": "holdout 冻结=datasets/ 原始板与既有产物零写入（raw_hash "
                "复验）；本报告与 profile 产物只落 profiles/ 与 out/v3-tl5/"
                if dataset_role == "holdout" else "train 侧板；不参与任何 "
                "holdout 判定",
    }
    return {
        "schema_version": "3.0", "artifact_kind": "tl5_profile_report",
        "track": TRACK, "report_date": CONVERSION_DATE,
        "board_id": board_id, "profile_id": profile_id,
        "dataset_role": holdout,
        "denominators": denominators,
        "quality": quality,
        "limits": limits,
        "main_path": main_path,
        "leakage_audit_ref": leakage_audit_ref,
        "source": source,
    }


# ---------------------------------------------------------------------------
# 7. KiCad 6.0–10.99 解析路径（S18；版本门显式；corpus-r2-r1 现代档
#    20210424/20211014/20221018 纳入；既有 KiCad5/pcbench 路径的函数
#    与本节零共享可变状态、行为零改动）
# ---------------------------------------------------------------------------

TRACK_K9 = "tl5-convert-k9-r1"
K9_GENERATOR = "pcbflow-corpus-convert-k9-r1"
K9_CONVERTER_VERSION = "pcbflow.corpus_convert#k9-path-r1"

#: 版本门：本路径显式支持的 board version token
#: （数据档全集实测：
#:   datasets/kicad-demos-r1/raw/ 18 板：20241030=KiCad 8.99、
#:     20241229=9.0、20260206=10.0、20260624=10.99；
#:   datasets/corpus-r2-r1/raw/ 现代档 19 板：20210424=KiCad 6.0、
#:     20211014=6.0、20221018=7.0（6.x/7.0 档 gen=pcbnew 无
#:     generator_version token）、20260206=10.0；
#:   legacy 两档 20171114/"4" 不在本门（另一工单），20171130 归 k5 门）
K9_SUPPORTED_VERSIONS = ("20210424", "20211014", "20221018",
                         "20241030", "20241229", "20260206", "20260624")

#: 20260206（KiCad 10.0）起：顶层 net 声明取消，pad 改按名引用
K9_NET_BY_NAME_FROM = "20260206"

#: 10.99 版本 token（constraints demo 所在档；新增 (constraint ...) 语义
#: token 与 (embedded_fonts ...)，本路径不消费、如实计数丢弃）
K9_TOKEN_1099 = "20260624"

#: 新纳入档（20210424/20211014/20221018，KiCad 6.x/7.0）铜层 type 白名单
#: （=KiCad 叠层铜层类型全集；corpus-r2-r1 实测：usb-gigabit 4 铜层与
#: kria-k26 8 铜层全部为 mixed/power——signal-only 判据会得出 0 铜层的
#: 虚假事实）。既有档（20241030+）维持 signal-only 口径零改动（S18 起该
#: 口径已冻结：complex_hierarchy F.Cu=power、jetson-agx In4.Cu=jumper 等
#: 既有板按 signal-only 产出构件与 R8 对账，变更即破坏既有行为）。
K9_MODERN_COPPER_TYPES = ("signal", "mixed", "power", "jumper")


def _k9_direct_children(root: list, name: str) -> list:
    return [c for c in root[1:] if isinstance(c, list) and c and c[0] == name]


def _k9_toks(node: list, key: str) -> list:
    n = sexpr_min.find_first(node, key)
    if n is None:
        return []
    return [t for t in n[1:] if isinstance(t, str)]


def parse_kicad9_board(text: str) -> dict:
    """KiCad 6.0–10.99 .kicad_pcb 文本 → 结构模型 dict（纯函数）。

    返回键与 parse_kicad5_board 同构（board_version/host/general/layers/
    copper_layers/setup/nets/modules/segment|via|arc|zone_count/
    parse_warnings），另加 k9 事实键：
      - net_declaration_source: "top_level"（20210424/20211014/20221018/
        20241030/20241229）| "pad_derived"（20260206+，顶层声明取消、
        结构性 net_id 不可得，nets 由 pad 引用推导，net_id=None 如实
        ——不虚构 id）；
      - generator_tokens: {"generator", "generator_version"}（6.x/7.0 档
        无 generator_version，如实 None）。
    版本门显式：version token 不在 K9_SUPPORTED_VERSIONS 即 ValueError
    （KiCad5 20171130 由 parse_kicad5_board 处理，两门互斥）。
    格式差异（证据=盘上真实文件，见 out/v3-tl5 r2 证据表与
    datasets/corpus-r2-r1 实测盘点）：
      - (footprint "Lib:Name" ...) 取代 (module ...)；reference 取自
        (property "Reference" "R5" ...)（20241030+ 档）或
        (fp_text "reference" "C2" ...)（20210424/20211014/20221018 档
        实测全量 footprint 无 property 形态，2485/2485）；
      - layers 表条目 (N "Name" type [alias])——层名带引号；
      - 铜层判据双口径（按档显式）：≤20221018 新纳入档 copper type 白名单
        signal/mixed/power/jumper（6.x/7.0 档实测铜层含 mixed/power 形态）
        ；20241030+ 既有档维持 type=="signal" 零改动；
      - pad (net N "name")（≤20241229）或 (net "name")（20260206+）；
      - (drill oval X Y) 形态；(embedded_fonts ...) 新 token（不消费）；
      - pad 第 4 位置 lock-state flag token（"locked"，6.x/7.0 档实测
        1630/1630 带旗 pad）——name/type/shape 取前 3 位不受影响。
    解析失败 fail-closed（SexprError/ValueError 原样上抛，不猜）。
    """
    top = sexpr_min.parse(text)
    roots = [n for n in top if isinstance(n, list) and n and n[0] == "kicad_pcb"]
    if len(roots) != 1:
        raise ValueError(f"expect exactly one kicad_pcb root, got {len(roots)}")
    root = roots[0]
    version = _tok(root, "version")
    if version not in K9_SUPPORTED_VERSIONS:
        raise ValueError(
            f"board version {version!r} outside k9 path gate "
            f"{list(K9_SUPPORTED_VERSIONS)} (KiCad5 20171130 uses "
            f"parse_kicad5_board)")
    # root 级查询索引（align-r1 2026-09-25；同 k5 线口径）。
    idx = sexpr_min.build_index(root)
    gen = sexpr_min.index_first(idx, "generator")
    genv = sexpr_min.index_first(idx, "generator_version")
    gen_tok = gen[1] if gen is not None and len(gen) > 1 else None
    genv_tok = genv[1] if genv is not None and len(genv) > 1 else None
    host = " ".join(str(t) for t in (gen_tok, genv_tok) if t is not None)

    general = {}
    g = sexpr_min.index_first(idx, "general")
    if g is not None:
        for c in g[1:]:
            if isinstance(c, list) and len(c) == 2:
                general[c[0]] = c[1]

    layers = []
    for lyr_block in _k9_direct_children(root, "layers"):
        for c in lyr_block[1:]:
            if isinstance(c, list) and len(c) >= 3:
                # k9 层表条目形如 (0 "F.Cu" signal ["alias"])——首 token=层号
                layers.append({"index": int(c[0]), "name": c[1],
                               "type": c[2]})
    # k9 层编号与 KiCad5 不同（copper id 随板层数重排：F.Cu=0、B.Cu=2…，
    # 技术层随后）；copper 判据=layer type（不能用 KiCad5 的 0..31 index
    # 过滤——会把 user 技术层误计为铜层），且按档显式双口径：
    # - ≤20221018（新纳入 6.x/7.0 档）：type ∈ K9_MODERN_COPPER_TYPES
    #   （signal/mixed/power/jumper；见该常量注——signal-only 在这两桶
    #   实测板得出 0 铜层）；
    # - 20241030+（S18 既有档）：type=="signal" 零改动。
    if version < "20241030":
        copper = [l for l in layers if l["type"] in K9_MODERN_COPPER_TYPES]
    else:
        copper = [l for l in layers if l["type"] == "signal"]

    setup = {}
    s = sexpr_min.index_first(idx, "setup")
    if s is not None:
        for c in s[1:]:
            if isinstance(c, list) and len(c) == 2 and isinstance(c[1], str):
                setup[c[0]] = c[1]

    # net 声明：顶层 (net N "name") 仅 ≤20241229 存在
    declared = []
    for n in _k9_direct_children(root, "net"):
        if len(n) >= 3:
            declared.append({"net_id": int(n[1]), "name": n[2]})
    net_by_name = version < K9_NET_BY_NAME_FROM
    if net_by_name:
        nets = sorted(declared, key=lambda x: x["net_id"])
        net_src = "top_level"
    else:
        nets = []
        net_src = "pad_derived"

    modules = []
    warnings = []
    pad_net_names: dict = {}
    for m in sexpr_min.index_all(idx, "footprint"):
        lib = m[1] if len(m) > 1 and isinstance(m[1], str) else None
        ref = None
        for prop in sexpr_min.find_all(m, "property"):
            if len(prop) > 2 and prop[1] == "Reference":
                ref = prop[2]
                break
        if ref is None:
            # 6.x/7.0 档（20210424/20211014/20221018，corpus-r2-r1 实测）：
            # property "Reference" 不存在，reference 在 fp_text（与 KiCad5
            # 同位形、带引号；ft[2]=ref 值字面量）
            for ft in sexpr_min.find_all(m, "fp_text"):
                if len(ft) > 2 and ft[1] == "reference":
                    ref = ft[2]
                    break
        if ref is None:
            warnings.append(f"footprint_without_reference:{lib}")
            ref = f"__NOREF__{len(modules):03d}"
        pads = []
        for p in sexpr_min.find_all(m, "pad"):
            net_node = sexpr_min.find_first(p, "net")
            net = None
            if net_node is not None:
                if len(net_node) >= 3 and net_node[1].isdigit():
                    net = {"net_id": int(net_node[1]), "name": net_node[2]}
                elif len(net_node) >= 2 and isinstance(net_node[1], str):
                    net = {"net_id": None, "name": net_node[1]}
                    if net_node[1] != "":
                        pad_net_names[net_node[1]] = True
            pads.append({
                "name": p[1], "type": p[2], "shape": p[3],
                "at": _k9_toks(p, "at"), "size": _k9_toks(p, "size"),
                "drill": _k9_toks(p, "drill") or None,
                "layers": _k9_toks(p, "layers"), "net": net,
            })
        modules.append({
            "lib": lib, "ref": ref,
            "layer": _tok(m, "layer"), "at": _toks(m, "at"),
            "pads": pads,
        })
    modules.sort(key=lambda x: x["ref"])
    if not net_by_name:
        # pad_derived：nets=pad 引用推导（确定性：按名排序；net_id=None 如实）
        nets = [{"net_id": None, "name": n}
                for n in sorted(pad_net_names)]

    return {
        "board_version": version, "host": host, "general": general,
        "layers": layers, "copper_layers": copper, "setup": setup,
        "nets": nets, "modules": modules,
        "segment_count": len(sexpr_min.index_all(idx, "segment")),
        "via_count": len(sexpr_min.index_all(idx, "via")),
        "arc_count": len(sexpr_min.index_all(idx, "arc")),
        "zone_count": len(sexpr_min.index_all(idx, "zone")),
        "parse_warnings": warnings,
        "net_declaration_source": net_src,
        "generator_tokens": {
            "generator": gen_tok,
            "generator_version": genv_tok,
        },
    }


def normalized_k9_board_text(model: dict, *, source_path: str,
                             source_sha256: str) -> str:
    """KiCad 6.0–10.99 规范化板文本（pcbflow k9 方言；与 KiCad5 规范化
    板同构；数值=源文本字面量；确定性 byte-exact 可重放）。

    net 行按源格式事实分两形态（不虚构 id）：顶层声明板=
    (net {id} {name})；pad_derived 板=(net {name})。
    """
    if not isinstance(source_sha256, str) or len(source_sha256) != 64:
        raise ValueError("source_sha256 required (64 hex)")
    out = []
    out.append(f"(kicad_pcb (version {model['board_version']}) "
               f"(generator {_q(K9_GENERATOR)})")
    out.append(f"  (source (path {_q(source_path)}) "
               f"(sha256 {_q(source_sha256)}))")
    g = model["general"]
    out.append(f"  (general (thickness {g.get('thickness', 'null')}) "
               f"(footprints {g.get('footprints', len(model['modules']))}) "
               f"(nets {len(model['nets'])}))")
    for l in model["copper_layers"]:
        out.append(f"  (layer {_q(l['name'])} (index {l['index']}) "
                   f"(type {_q(l['type'])}))")
    for n in model["nets"]:
        if n["net_id"] is None:
            out.append(f"  (net {_q(n['name'])})")
        else:
            out.append(f"  (net {n['net_id']} {_q(n['name'])})")
    for m in model["modules"]:
        at = " ".join(m["at"])
        out.append(f"  (footprint {_q(m['ref'])} (lib {_q(m['lib'])}) "
                   f"(layer {_q(m['layer'])}) (at {at})")
        for p in m["pads"]:
            parts = [f"    (pad {_q(p['name'])} {p['type']} {p['shape']}",
                     f"(at {' '.join(p['at'])})",
                     f"(size {' '.join(p['size'])})"]
            if p["drill"]:
                parts.append(f"(drill {' '.join(p['drill'])})")
            parts.append("(layers "
                         + " ".join(_q(x) for x in p["layers"]) + ")")
            if p["net"]:
                if p["net"]["net_id"] is None:
                    parts.append(f"(net {_q(p['net']['name'])})")
                else:
                    parts.append(f"(net {p['net']['net_id']} "
                                 f"{_q(p['net']['name'])})")
            out.append(" ".join(parts) + ")")
        out.append("  )")
    out.append(")")
    return "\n".join(out) + "\n"


def build_k9_graph_spec(*, project_id: str, profile_id: str, revision: str,
                        file_hashes: dict, has_audit: bool) -> dict:
    """k9 板 graph spec（build_graph_spec 同构；audit_report 节点仅在该
    构件实际产出时在场——单态 as_shipped 板无 unrouted/routed 对，
    audit 段不生成不凑 present（deviations 如实声明））。"""
    def node(aid, kind, path, stage, inputs):
        return {
            "artifact_id": aid, "kind": kind, "path": path,
            "sha256": file_hashes[path], "status": "present",
            "revision": revision, "stage_label": stage, "inputs": inputs,
        }
    nodes = [
        node("board", "board", "inputs/board.kicad_pcb", None, []),
        node("stackup", "stackup", "inputs/stackup.json", None, []),
        node("constraints", "constraints", "inputs/constraints.json",
             "compile", []),
        node("net_registry", "net_registry", "derived/net-registry.json",
             "enum", ["board", "constraints"]),
    ]
    if has_audit:
        nodes.append(node("audit_report", "audit_report",
                          "derived/audit.json", "audit",
                          ["board", "net_registry"]))
    nodes.append(node("feedforward_plan", "feedforward_plan",
                      "derived/feedforward-plan.json", "feedforward",
                      ["net_registry"] + (["audit_report"] if has_audit
                                          else [])))
    nodes.append({
        "artifact_id": "decision_ledger", "kind": "decision_ledger",
        "path": None, "sha256": None, "status": "present",
        "revision": revision, "stage_label": "ledger",
        "inputs": ["feedforward_plan"],
    })
    nodes.append({
        "artifact_id": "gate_records", "kind": "gate_record",
        "path": None, "sha256": None, "status": "present",
        "revision": revision, "stage_label": "gate",
        "inputs": ["decision_ledger"],
    })
    deviations = [] if has_audit else [
        "audit_report 节点不在场：单态 as_shipped 板无 unrouted/routed "
        "对，audit 构件不生成（不虚构两态检查）"]
    return {
        "schema_version": "3.0", "artifact_kind": "artifact_graph_spec",
        "project_id": project_id, "profile_id": profile_id,
        "revision": revision,
        "converter_path": K9_CONVERTER_VERSION,
        "deviations": deviations,
        "nodes": nodes,
    }


def build_k9_conversion_log(*, board_id: str, profile_id: str,
                            module_sha256: str, inputs: list,
                            outputs: list, model: dict,
                            model_r: dict | None, crit: dict,
                            topology_group: str, audit_result: str | None,
                            route_check_status: str) -> dict:
    """k9 板 conversion log（与 build_conversion_log 同构；字段以 k9 格式
    事实为准）。model_r=None=单态板（audit 段不生成）；route_check_status
    由编排侧如实填（S18=not_executed，无 kicad-cli 运行）。"""
    dropped = {
        "graphics_and_text": "gr_line/gr_text/gr_arc/gr_circle/gr_curve/"
                             "dimension 等图形不进规范化板",
        "properties": 'footprint (property "Reference"/"Value"/...) 只取 '
                      "Reference 作 ref；其余属性文本不进规范化板",
        "zones": f"zones={model['zone_count']} 不进规范化板（原样留存于 "
                 f"datasets）",
        "setup_detail": "setup 只留标量子键；k9 setup 内 stackup/pcbplotparams/"
                        "tenting/covering 等子块不消费（stackup 构件只含铜层"
                        "与 thickness）",
        "embedded_fonts": "(embedded_fonts ...) token 不消费（18/18 板在场）",
        "routed_geometry": f"segments={model['segment_count']} "
                           f"vias={model['via_count']} arcs={model['arc_count']}"
                           " 不进规范化板（as_shipped 参考态以 r2 manifest "
                           "output/raw hash 绑定）",
        "constraint_tokens": "（仅 20260624 板）(constraint ...) 语义 token "
                             "不消费（本路径文本级结构转换，非约束求值器）",
        "net_ids_pad_derived": "（仅 20260206+ 板）顶层 net 声明已在该格式取消"
                               "，net_id 结构性不可得——nets 由 pad 引用推导，"
                               "不虚构 id",
    }
    if model_r is not None:
        dropped["pair_state"] = (
            f"routed 参考态（同板双态文件）segments={model_r['segment_count']} "
            f"vias={model_r['via_count']} 以 r2 manifest 输出 hash 绑定")
    missingness = {
        "setup_min_values": "not_available（k9 setup 无 trace_min/"
                            "trace_clearance/via_* 键——stackup.setup_mins "
                            "与 profile.thresholds 如实留空/留 null，不虚构）",
        "anchors": "not_determinable（布局冻结集属项目决策，板文本无据）",
        "via_cost": "not_determinable（router 参数非板属性）",
        "length_match_tolerance": "not_determinable（无原理图/规范源）",
        "physics_required": "not_determinable（无介质参数/电流源）",
        "params": "空（搜索域不可从板文本判定）",
        "route_check": route_check_status,
    }
    if audit_result is None:
        missingness["audit_pair_check"] = (
            "not_applicable_single_state（单态 as_shipped 板无 unrouted/"
            "routed 对——audit 构件不生成，不虚构两态检查）")
    return {
        "track": TRACK_K9, "conversion_date": CONVERSION_DATE,
        "board_id": board_id, "profile_id": profile_id,
        "converter_version": K9_CONVERTER_VERSION,
        "module": MODULE_NAME, "module_sha256": module_sha256,
        "version_gate": {
            "supported": list(K9_SUPPORTED_VERSIONS),
            "board_version": model["board_version"],
            "net_declaration_source": model["net_declaration_source"],
        },
        "inputs": inputs, "outputs": outputs,
        "retained": [
            "copper layer name/index/type", "net declarations（两形态："
            "id+name 或 pad_derived name-only，不虚构 id）",
            "footprint ref(=property Reference)/lib/layer/at",
            "pad name/type/shape/at/size/drill(含 oval)/layers/net",
        ],
        "dropped": dropped,
        "convention_basis": crit["basis"],
        "field_missingness": missingness,
        "parse_warnings": model["parse_warnings"],
        "audit_result": audit_result,
        "topology_group": topology_group,
        "determinism_claim": "pure function of source text; byte-exact "
                             "replay（数值保留源字面量；canonical JSON）",
    }
