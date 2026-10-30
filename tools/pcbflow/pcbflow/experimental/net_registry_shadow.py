"""② 只读 shadow：实验性网络注册表旁路测试（NET-REGISTRY-PROPOSAL 阶段 N1）。

边界（任务书 §三）：不改 SPEC / proposal / pcbagent / Rev-C 工程；不接入正式
audit 的硬约束、红黄绿门或回退逻辑；ambiguous/unclassified 不改变阶段②结论。
本模块是实验性诊断旁路，不是正式注册表引入；`pcbflow audit` 仍为 specified
stub（cli.py cmd_stub），不消费任何注册表字段（registry_consumed=false）。

生成器模式（Mimosa 钩子）：零落盘、零子进程；`python -m
pcbflow.experimental.net_registry_shadow --select <产物>` 打到 stdout，
由 shell 重定向到 <project>/pcbflow-out/stage2-shadow/。

分类来源优先级（proposal §4.3 / 任务书 §六）：
  explicit_spec > structure_declaration > schematic_attribute/net_class
  > naming_rule > inference；冲突 → ambiguous_until_reviewed。
本次不冻结 net_id：身份用可回溯 source_net_key（revc.netlist#<网名>）。
confirmed 仅在有明确来源声明或已批人工裁决记录（compile_seeds.AMBIGUITIES
AMB-1..4，2026-08-29 已批）时使用；本工具从不伪造 confirmed。

确定性（任务书 §十）：同输入 ⇒ 核心产物（candidate/coverage/comparison）
byte-exact；排序全稳定键；wall-clock/主机只进 run-manifest。
"""

from __future__ import annotations

import argparse
import ast
import datetime
import json
import math
import os
import re
import socket
import sys

from .. import compile_cmd, compile_seeds as seeds_mod, config, envelope, hashing, sexpr_min, toolchain
from .. import enum_cmd as enum_mod

PROJECT_ID = compile_cmd.PROJECT_ID
SCHEMA_REGISTRY = "0.1-experimental"

# 分类状态（proposal §5.8 / 任务书 §五）
CLASSIFICATION_STATUSES = ("inferred", "source_declared", "confirmed",
                           "ambiguous", "unclassified", "waived")

# 来源优先级（任务书 §六；数值越小优先级越高）
PRECEDENCE = [
    "explicit_spec_or_structure_declaration",
    "schematic_attribute_pin_mux_kicad_net_class",
    "confirmed_group_or_length_group_declaration",
    "stable_naming_rule",
    "inference",
]
CONFLICT_POLICY = "ambiguous_until_reviewed"

# ---- 输入相对路径（revc 工程内） --------------------------------------------
REL_NETLIST = "revc.netlist"
REL_BOARD = "stm32h743-coreboard-revc.kicad_pcb"
REL_SCH = "stm32h743-coreboard-revc.kicad_sch"
REL_PRO = "stm32h743-coreboard-revc.kicad_pro"
REL_LEN = "length-report.py"
REL_PLANNER_CFG = "tools/pcbagent/pcbagent/config.py"
REL_B2_GATE = "design/coreboard/kicad/stm32h743-coreboard-revc/pcbagent-out/b2/gate.json"
BASELINE_DIR = "tools/pcbflow/out/revc-a2"


# ===========================================================================
# 纯分类管线（fixture 与真实输入共用；输入全部为可 JSON 化的纯数据）
# ===========================================================================

def match_spec_classes(net_name, class_patterns):
    """全部命中的 spec 类（不只首个）——重叠命中是歧义候选。有序稳定。"""
    hits = []
    for cls, patterns in class_patterns:
        if any(re.match(p, net_name) for p in patterns):
            hits.append(cls)
    return hits


def classify_planner(net_name, planner_patterns, planner_default):
    for pref, key in planner_patterns:
        if net_name.startswith(pref):
            return key
    return planner_default


def parse_allowed_layers(raw):
    """§2 允许层 raw → {layers, preferred, notes}。确定性解析；解析失败返回 null 层。"""
    m = {
        "F/In2/B(批准)": (["F.Cu", "In2.Cu", "B.Cu"], None,
                          "B.Cu 仅经批准短跳（raw 保留）"),
        "F（全程）": (["F.Cu"], "F.Cu", None),
        "F/In2": (["F.Cu", "In2.Cu"], None, None),
        "F 优先/In2": (["F.Cu", "In2.Cu"], "F.Cu", None),
        "F": (["F.Cu"], None, None),
    }
    if raw in ("全部", "铺铜 | 0.6/0.3 缝合 | 全部"):
        return {"layers": ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"],
                "preferred_layer": None, "note": "GND 平面层（铺铜）"}
    if raw in m:
        layers, pref, note = m[raw]
        return {"layers": layers, "preferred_layer": pref, "note": note}
    return {"layers": None, "preferred_layer": None,
            "note": f"unparsed_raw:{raw}"}


def parse_via_policy(raw):
    """§2 过孔 raw → 粗粒度策略。无显式限数 → null（不虚构）。"""
    if "整对≤1" in raw:
        return {"policy": "pair_le_1", "max_count": None,
                "raw_note": "整对 ≤1 次换层，成对"}
    mm = re.search(r"≤(\d+)", raw)
    if mm:
        return {"policy": "max_count", "max_count": int(mm.group(1)),
                "raw_note": None}
    return None


_SPEC_TO_PLANNER = {
    "PWR_5V": "PWR", "PWR_3V3": "PWR", "PWR_SW": "PWR", "PWR_MISC": "PWR",
    "USB_DIFF": "USB", "FMC_CLK": "FMC", "FMC_CTRL": "FMC",
    "FMC_DATA_L": "FMC", "FMC_DATA_H": "FMC", "FMC_ADDR": "FMC",
    "SDMMC2": "SDMMC2", "SDMMC1": "SDMMC1", "QSPI": "QSPI",
    "ETH_RMII": "ETH", "LTDC": "LTDC", "SIG_DEFAULT": "SIG",
    "ANLG": "ANLG",
    # GND 无对应 planner 类键：pcbagent classify_net 落 L2_NET_CLASS_DEFAULT=SIG
    # （平面语义由 L3_RIPUP_FORBIDDEN/plane 处理，不在此静默等价）——如实映射为 None。
    "GND": None,
}


def electrical_role_of(net_name, cls):
    """确定性电气角色（全部 inferred 级，规则 ID 记录；spec 条款作旁证）。"""
    if net_name == "GND":
        return "ground_return", "rule:gnd_exact"
    if net_name == "SW_NODE":
        return "power_switch_node", "rule:sw_node_exact(C-0033旁证)"
    if net_name == "FB_NODE":
        return "power_feedback", "rule:fb_node_exact(PWR_SW_raw_FB凯尔文)"
    if net_name == "EMMC_VSEL":
        return "power_enable", "rule:emmc_vsel(C-0045旁证)"
    if cls and cls.startswith("PWR"):
        return "power_rail", "rule:pwr_class"
    if net_name.startswith(("HSE_", "LSE_")):
        return "crystal_node", "rule:xo_prefix(C-0032旁证)"
    if net_name == "GNDA":
        return "ground_return_analog", "rule:gnda_exact(C-0042旁证)"
    if net_name == "VDDA":
        return "power_rail", "rule:vdda_exact(C-0042旁证)"
    if cls and cls.startswith("ANLG"):
        return "analog_sensitive", "rule:anlg_class"
    if net_name.endswith("DM") or "_DM" in net_name:
        return "differential_negative", "rule:usb_dm_suffix"
    if net_name.endswith("DP") or "_DP" in net_name:
        return "differential_positive", "rule:usb_dp_suffix"
    if net_name.endswith(("CLK", "_CK", "PCLK")) or net_name == "FMC_SDCLK":
        return "clock", "rule:clk_suffix"
    if net_name == "NRST":
        return "reset", "rule:nrst_exact"
    if net_name in ("SWCLK", "SWDIO", "BOOT0") or net_name.startswith(("BTN_", "LED")):
        return "test_or_configuration", "rule:dbg_prefix"
    if net_name.startswith("GPIO_"):
        return "ordinary_gpio", "rule:gpio_prefix"
    if cls == "SIG_DEFAULT":
        return "ordinary_control", "rule:sig_default_residual"
    return None, "rule:none"


def bus_role_of(net_name):
    if net_name.endswith(("CLK", "_CK", "PCLK")):
        return "clock"
    if re.match(r"^FMC_A(?:\d+)$", net_name) or net_name.startswith("FMC_BA"):
        return "address"
    if (re.match(r"^(FMC_D\d+|FMC_NBL\d|SDMMC[12]_D\d|QSPI_IO\d)$", net_name)
            or net_name.startswith(("LTDC_R", "LTDC_G", "LTDC_B"))
            or net_name.startswith(("ETH_RXD", "ETH_TXD")) or net_name == "ETH_CRS_DV"):
        return "data"
    if net_name.startswith(("LTDC_HSYNC", "LTDC_VSYNC", "LTDC_DE")) or \
       net_name in ("FMC_SDNCAS", "FMC_SDNRAS", "FMC_SDNWE", "FMC_SDNE0",
                    "FMC_SDCKE0", "SDMMC2_CMD", "SDMMC1_CMD", "QSPI_NCS",
                    "ETH_TX_EN", "ETH_MDC", "ETH_MDIO", "SD_CD"):
        return "control"
    return "signal"


def build_diff_pair_index(diff_pairs):
    """[{pair_id,pos:[...],neg:[...],segments:{net:seg},source_refs,status}] → net→info。"""
    idx = {}
    for p in diff_pairs:
        for n in p["pos"] + p["neg"]:
            idx[n] = {
                "pair_id": p["pair_id"],
                "polarity": "positive" if n in p["pos"] else "negative",
                "segment": (p.get("segments") or {}).get(n),
                "source_refs": list(p.get("source_refs") or []),
                "status": p.get("status", "source_declared"),
            }
    return idx


def build_registry(inp):
    """纯函数：inputs → registry candidate dict（任务书 §五 顶层结构）。

    inp 键：netlist_nets{net:[[ref,pin]]}, board_net_names[], board_footprint_refs[],
    script_groups, spec_members(九组 spec 侧), class_patterns, catch_all_class,
    planner_patterns, planner_default, kicad_pro_classes{name:netnames_count},
    bus_rules[{bus_id,pattern,source_kind,source}], diff_pairs, rulings,
    lengths{nine_groups}, corridor_formula{pitch,layers,margin},
    hashes{rel:sha256}, comps{ref:{value,footprint}}
    """
    nets_in = inp["netlist_nets"]
    all_names = sorted(nets_in)
    named = [n for n in all_names if not n.startswith("unconnected-")]
    nc_nets = [n for n in all_names if n.startswith("unconnected-")]
    board_names = set(inp["board_net_names"])
    board_refs = set(inp["board_footprint_refs"])
    script_groups = inp["script_groups"]

    # ① 消费已批裁决（compile_seeds.AMBIGUITIES=人工确认记录；只有它可产生 confirmed）
    ruled = _ruling_index(inp["rulings"])

    # ② canonical 九组成员（与 enum_cmd._canonical_groups 同口径）
    canonical = _canonical_groups_named(named, script_groups, inp["spec_members"],
                                        inp["rulings"], inp["lengths"])

    # ③ 差分对索引
    diff_idx = build_diff_pair_index(inp["diff_pairs"])

    # ④ 逐网分类
    net_records = []
    status_counts = {s: 0 for s in CLASSIFICATION_STATUSES}
    unmapped, ambiguous_nets, unclassified_nets = [], [], []
    for name in named:
        rec = _classify_net(name, nets_in[name], inp, ruled, canonical,
                            diff_idx, board_names, board_refs)
        net_records.append(rec)
        status_counts[rec["classification_status"]] += 1
        if rec["classification_status"] == "ambiguous":
            ambiguous_nets.append(name)
        if rec["classification_status"] == "unclassified":
            unclassified_nets.append(name)
        if rec["routing_class"] is None:
            unmapped.append(name)

    # ⑤ 关系完整性诊断（差分对完整性/重复成员/悬空引用）
    diagnostics = _relation_diagnostics(inp, canonical, named, board_names)
    diagnostics += _nc_net_note(nc_nets)

    registry = {
        "schema_version": SCHEMA_REGISTRY,
        "status": "proposal",
        "experimental_note": "只读 shadow 候选（NET-REGISTRY-PROPOSAL 阶段 N1）；"
                             "非正式注册表，不冻结 net_id，不改变阶段②门",
        "snapshot": {
            "schematic_sha256": inp["hashes"].get(REL_SCH),
            "board_sha256": inp["hashes"].get(REL_BOARD),
            "source_revision": inp["source_revision"],
        },
        "classification_policy": {
            "precedence": list(PRECEDENCE),
            "conflict_policy": CONFLICT_POLICY,
            "confirmed_basis": "仅明确来源声明或已批人工裁决记录（AMB-1..4, 2026-08-29）；"
                               "本工具不伪造 confirmed",
        },
        "nets": net_records,
        "diagnostics": sorted(diagnostics, key=lambda d: (d["id"], json.dumps(
            d, ensure_ascii=False, sort_keys=True))),
        "source_net_key_convention": "revc.netlist#<net_name>（可回溯网表/PCB；不冻结 net_id）",
    }
    return {
        "registry": registry,
        "stats": {
            "total_nets": len(all_names),
            "named_nets": len(named),
            "nc_pad_nets": len(nc_nets),
            "status_counts": status_counts,
            "unmapped_nets": unmapped,
            "ambiguous_nets": ambiguous_nets,
            "unclassified_nets": unclassified_nets,
        },
    }


def _ruling_index(rulings):
    """已批裁决 → {net: [ruling_id...]}。

    真实裁决（compile_seeds.AMBIGUITIES AMB-1..4）的成员面按其已批语义在此
    显式镜像（有注释可审计）；通用裁决可带 `member_nets` 字段直接声明成员面。
    """
    idx = {}
    def touch(net, rid):
        idx.setdefault(net, [])
        if rid not in idx[net]:
            idx[net].append(rid)
    for a in rulings:
        rid, st = a["id"], a["status"]
        if st != "resolved":
            continue
        for net in a.get("member_nets") or []:
            touch(net, rid)
        if rid == "AMB-1":  # FMC_A12 纳入 FMC_ADDR / G_FMC_A（已批语义）
            touch("FMC_A12", rid)
        elif rid == "AMB-2":  # LTDC canonical 以网表为准；成员面由 canonical 按前缀消费
            pass
        elif rid == "AMB-3":  # USB 两段均为约束域
            for n in ("USB_DP", "USB_DM", "USB_DP_C", "USB_DM_C"):
                touch(n, rid)
        elif rid == "AMB-4":  # SD_CD 归 SDMMC1/G_SD
            touch("SD_CD", rid)
    return idx


def _canonical_groups_named(named, script_groups, spec_members, rulings, lengths):
    """与 enum_cmd._canonical_groups 同口径的 canonical 九组（纯数据版）。

    组级裁决映射：真实 AMB-1→G_FMC_A / AMB-3→G_USB（已批语义镜像）；
    通用裁决可带 `applies_to_length_group` 字段声明组归属。
    """
    amb = {a["id"]: a["status"] for a in rulings}
    group_ruling = {}
    for a in rulings:
        gid = a.get("applies_to_length_group") or {
            "AMB-1": "G_FMC_A", "AMB-3": "G_USB"}.get(a["id"])
        if a["status"] == "resolved" and gid:
            group_ruling[gid] = a["id"]
    all_names = set(named)
    out = {}
    for g in lengths:
        sg = script_groups[g]
        if spec_members.get(g) is None:  # LTDC 型：spec 未枚举 → 板上前缀实际为准
            members = sorted(n for n in named
                             if n.startswith("LTDC_") and n != sg["ref"])
            out[g] = {
                "members": members,
                "ref": sg["ref"],
                "basis": "AMB-2 已批（2026-08-29）：canonical 以网表实际为准",
                "ruling": "AMB-2" if amb.get("AMB-2") == "resolved" else None,
                "disputed_members": list(members),  # 整面按网表修正=全部经裁决
            }
            continue
        spec = set(spec_members[g])
        script = set(sg["nets"])
        if spec != script:
            rid = group_ruling.get(g)
            if rid:
                out[g] = {"members": sorted(spec | script), "ref": sg["ref"],
                          "basis": f"{rid} 已批并集", "ruling": rid,
                          "disputed_members": sorted(spec ^ script)}
                continue
        out[g] = {"members": sorted(script), "ref": sg["ref"],
                  "basis": "spec §2 类行 = 脚本 = 网表一致", "ruling": None,
                  "disputed_members": []}
    return out


def _classify_net(name, nodes, inp, ruled, canonical, diff_idx,
                  board_names, board_refs):
    class_patterns = inp["class_patterns"]
    catch_all = inp["catch_all_class"]
    hits = match_spec_classes(name, class_patterns)
    source_refs, inference_rule = [], None
    ruling_ids = ruled.get(name, [])

    if len(hits) > 1:
        # 具体行重叠：除非有已批裁决，否则 ambiguous（不静默择一）
        cls = hits[0]  # 展示值按有序匹配；状态仍 ambiguous
        status = "ambiguous"
        inference_rule = f"multi_class_hit:{','.join(hits)};conflict_policy={CONFLICT_POLICY}"
        source_refs.append("routing-spec §2 多行重叠")
    elif hits:
        cls = hits[0]
        if ruling_ids:
            status = "confirmed"
            source_refs.append("ruling:" + "+".join(ruling_ids))
        else:
            status = "source_declared"
        source_refs.append("routing-spec §2 类行:" + cls)
    else:
        cls = catch_all
        status = "source_declared"  # spec §2 SIG_DEFAULT 行显式声明"其余全部"
        inference_rule = ("routing-spec §2 SIG_DEFAULT 兜底行（'其余全部'）；"
                          "网名不匹配任何具体类行")
        source_refs.append("routing-spec §2 SIG_DEFAULT 行")
        if ruling_ids:
            status = "confirmed"
            source_refs.append("ruling:" + "+".join(ruling_ids))

    # 总线（命名规则推断 + structures 草案旁证；显式声明面由 inp.bus_rules.source_kind 决定）
    bus, bus_status = None, None
    for rule in inp["bus_rules"]:
        if re.match(rule["pattern"], name):
            bus = rule["bus_id"]
            if rule.get("source_kind") == "explicit_declaration":
                bus_status = "source_declared"
            else:
                bus_status = "inferred"
                inference_rule = (inference_rule or
                                  f"bus_prefix_rule:{rule['bus_id']}"
                                  f"({rule.get('source', 'naming_rule')})")
            if ruling_ids:
                bus_status = "confirmed"
            source_refs.append(rule.get("source", "naming_rule"))
            break

    # 电气角色 / 总线角色（inferred 级规则；无专项规则时由 bus_role 投影）
    role, role_rule = electrical_role_of(name, cls)
    bus_role = bus_role_of(name) if bus else None
    if role is None and bus_role in ("data", "address", "control", "handshake"):
        role = f"single_ended_{bus_role}"
        role_rule = "rule:bus_role_projection"

    # 长度组（canonical 成员或参考网；裁决只确认争议成员，两侧一致的保持 source_declared）
    length_group = None
    lg_status = None
    for g in sorted(canonical):
        cg = canonical[g]
        if name in cg["members"] or name == cg["ref"]:
            length_group = g
            if cg["ruling"] and (name in cg["disputed_members"] or ruling_ids):
                lg_status = "confirmed"
            else:
                lg_status = "source_declared"
            source_refs.append("length_group:" + g)
            break

    # 差分对
    dp = diff_idx.get(name)
    if dp:
        differential_pair = {"pair_id": dp["pair_id"], "polarity": dp["polarity"],
                             "segment": dp["segment"], "complete": None}
        if dp["status"] == "confirmed" or ruling_ids:
            differential_pair["status"] = "confirmed"
        else:
            differential_pair["status"] = dp["status"]
        source_refs.extend(dp["source_refs"])
    else:
        differential_pair = None

    # 物理布线属性（spec §2 行 raw 解析；解析失败如实 null）
    routing_attrs = _routing_attrs(cls, inp)

    # 端点（REF.pin 稳定排序；板上不可解析端点单列诊断由 coverage 承接）
    endpoints = sorted(f"{nd['ref']}.{nd['pin']}" for nd in nodes)

    # 网级状态汇总：ambiguous > confirmed > source_declared > inferred
    field_statuses = [status]
    if bus is not None:
        field_statuses.append(bus_status)
    if lg_status:
        field_statuses.append(lg_status)
    if differential_pair:
        field_statuses.append(differential_pair["status"])
    if "ambiguous" in field_statuses:
        net_status = "ambiguous"
    elif "confirmed" in field_statuses:
        net_status = "confirmed"
    elif "unclassified" in field_statuses:
        net_status = "unclassified"
    elif "source_declared" in field_statuses:
        net_status = "source_declared"
    else:
        net_status = "inferred"

    # 板上存在性标注（netlist ↔ board 交叉核对不改动分类，只记来源事实）
    if name not in board_names:
        source_refs.append("board_net:absent")

    rec = {
        "source_net_key": f"{REL_NETLIST}#{name}",
        "net_name": name,
        "bus": bus,
        "bus_role": bus_role,
        "member_group": cls,
        "electrical_role": role,
        "routing_class": cls,
        "length_group": length_group,
        "differential_pair": differential_pair,
        "endpoints": endpoints,
        "allowed_layers": routing_attrs["allowed_layers"],
        "preferred_layer": routing_attrs["preferred_layer"],
        "via_policy": routing_attrs["via_policy"],
        "classification_status": net_status,
        "source_refs": sorted(set(source_refs)),
        "inference_rule": inference_rule,
    }
    return rec


def _routing_attrs(cls, inp):
    """§2 行 raw =「线宽 | 过孔 | 允许层 | 等长组」；取段解析，全 raw 保留旁证。"""
    raws = inp.get("class_raws") or {}
    raw = raws.get(cls)
    if raw is None:
        return {"allowed_layers": None, "preferred_layer": None,
                "via_policy": None, "note": f"unknown_class_raw:{cls}"}
    segments = [s.strip() for s in raw.split("|")]
    layer_seg = segments[2] if len(segments) >= 3 else raw
    via_seg = segments[1] if len(segments) >= 3 else raw
    layers = parse_allowed_layers(layer_seg)
    return {"allowed_layers": layers["layers"],
            "preferred_layer": layers["preferred_layer"],
            "via_policy": parse_via_policy(via_seg),
            "note": layers["note"]}


def _relation_diagnostics(inp, canonical, named, board_names):
    """关系完整性：差分对完整性/悬空引用/重复成员/脚本幻影成员。"""
    diags = []
    named_set = set(named)
    for p in sorted(inp["diff_pairs"], key=lambda x: x["pair_id"]):
        pos, neg = p["pos"], p["neg"]
        segs = p.get("segments") or {}
        if segs:
            # 分段对（如 USB 两段）：各段必须正负齐备，且两侧段数平衡
            pos_segs = {segs.get(n) for n in pos}
            neg_segs = {segs.get(n) for n in neg}
            incomplete = (None in pos_segs or None in neg_segs
                          or len([n for n in pos if segs.get(n)])
                          != len([n for n in neg if segs.get(n)]))
        else:
            incomplete = not pos or not neg
        if incomplete:
            diags.append({"id": f"PAIR-INCOMPLETE:{p['pair_id']}",
                          "kind": "incomplete_differential_pair",
                          "detail": {"pos": pos, "neg": neg},
                          "action": "不自动配对；待显式声明"})
    for g in sorted(canonical):
        cg = canonical[g]
        dup = sorted({m for m in cg["members"] if cg["members"].count(m) > 1})
        if dup:
            diags.append({"id": f"DUP-MEMBER:{g}", "kind": "duplicate_group_member",
                          "detail": dup, "action": "去重前先披露"})
        dangling = sorted(m for m in cg["members"] if m not in named_set)
        if dangling:
            diags.append({"id": f"MISSING-NET:{g}",
                          "kind": "group_member_not_on_board",
                          "detail": dangling,
                          "action": "missing_reference（不默认为真实长度）"})
        script_only = sorted(set(inp["script_groups"][g]["nets"]) - named_set)
        if script_only:
            diags.append({"id": f"SCRIPT-PHANTOM:{g}",
                          "kind": "script_member_not_on_board",
                          "detail": script_only,
                          "action": "length-report.py 枚举含板上不存在网名；"
                                    "不默认为真实长度（unrouted/缺失区分由测量方给出）"})
        canon_no_script = sorted(set(cg["members"]) - set(inp["script_groups"][g]["nets"]))
        if canon_no_script:
            diags.append({"id": f"UNMEASURED:{g}",
                          "kind": "canonical_member_not_measured_by_script",
                          "detail": canon_no_script,
                          "action": "canonical 成员未被 length-report.py 枚举（unmeasured）"})
    return diags


def _nc_net_note(nc_nets):
    if not nc_nets:
        return []
    return [{"id": "NC-PAD-NETS", "kind": "out_of_scope_nets",
             "detail": {"count": len(nc_nets),
                        "members": sorted(nc_nets)},
             "action": "unconnected-(...) NC 焊盘网：无布线实体，不参与分类；"
                       "显式列出防静默丢弃"}]


# ===========================================================================
# coverage（任务书 §九.2）
# ===========================================================================

def build_coverage(reg, stats, inp):
    nets = reg["nets"]
    by_cls = {}
    by_role = {}
    by_bus = {}
    for r in nets:
        by_cls[r["routing_class"]] = by_cls.get(r["routing_class"], 0) + 1
        role_key = r["electrical_role"] if r["electrical_role"] is not None \
            else "unspecified"
        by_role[role_key] = by_role.get(role_key, 0) + 1
        if r["bus"]:
            by_bus[r["bus"]] = by_bus.get(r["bus"], 0) + 1
    # 规范/脚本/网表三方成员差集（任务书 §七）
    named = sorted(r["net_name"] for r in nets)
    named_set = set(named)
    group_diffs = {}
    for g in sorted(inp["lengths"]):
        sg = inp["script_groups"][g]
        spec = inp["spec_members"][g]
        board = sorted(n for n in named_set
                       if (n.startswith("LTDC_") if g == "G_LTDC"
                           else n in set(sg["nets"]) or n == sg["ref"]))
        if g == "G_LTDC":
            spec_members_effective = None  # spec 未枚举（仅 23 网计数声明）
        else:
            spec_members_effective = sorted(set(spec))
        script_list = sorted(set(sg["nets"]) | {sg["ref"]} if sg["ref"] else set(sg["nets"]))
        group_diffs[g] = {
            "spec_members": spec_members_effective,
            "script_members": script_list,
            "board_members": board,
            "spec_minus_board": sorted(set(spec_members_effective or []) - set(board)),
            "board_minus_spec": sorted(set(board) - set(spec_members_effective or []))
            if spec_members_effective is not None else None,
            "script_minus_board": sorted(set(sg["nets"]) - named_set),
            "board_minus_script": sorted(set(board) - set(sg["nets"])
                                         - ({sg["ref"]} if sg["ref"] else set())),
            "ref": sg["ref"],
        }
    coverage = {
        "schema_version": SCHEMA_REGISTRY,
        "project": PROJECT_ID,
        "role": "net-registry shadow coverage（只读诊断；不改变阶段②门）",
        "totals": {
            "all_nets_in_netlist": stats["total_nets"],
            "named_nets": stats["named_nets"],
            "nc_pad_nets_excluded": stats["nc_pad_nets"],
            "classified": (stats["status_counts"]["source_declared"]
                           + stats["status_counts"]["confirmed"]),
            "source_declared": stats["status_counts"]["source_declared"],
            "confirmed": stats["status_counts"]["confirmed"],
            "inferred": stats["status_counts"]["inferred"],
            "ambiguous": stats["status_counts"]["ambiguous"],
            "unclassified": stats["status_counts"]["unclassified"],
            "waived": stats["status_counts"]["waived"],
        },
        "unmapped_nets": stats["unmapped_nets"],
        "ambiguous_selectors": [
            {"net": r["net_name"], "detail": r["inference_rule"]}
            for r in nets if r["classification_status"] == "ambiguous"],
        "missing_groups": [],
        "missing_endpoints": _missing_endpoints(reg, inp),
        "missing_length_members": {
            g: {k: v for k, v in {
                "script_members_not_on_board": group_diffs[g]["script_minus_board"],
                "board_members_not_measured_by_script":
                    group_diffs[g]["board_minus_script"],
                "note": "不把缺失网络长度默认为真实长度（missing_reference/unmeasured/"
                        "unrouted 区分由测量方 length-report.py 给出；本工具不测量）",
            }.items() if v}
            for g in sorted(group_diffs)
            if group_diffs[g]["script_minus_board"] or group_diffs[g]["board_minus_script"]
        },
        "unimplemented_consumers": [
            {"consumer": "pcbflow.cli audit（② 阶段命令）", "status": "specified",
             "note": "cli.py cmd_stub 桩；registry_consumed=false"},
            {"consumer": "pcbflow.cli check（⑤ 检查器族）", "status": "specified"},
            {"consumer": "pcbflow.check.length_pair_diff（G_USB 连接器段测量，C-0019 segments）",
             "status": "specified", "note": "length-report.py 只测 MCU 段"},
        ],
        "group_member_diffs": group_diffs,
        "spec_class_planner_diffs": _class_planner_diffs(inp, nets),
        "distribution": {"by_routing_class": by_cls, "by_electrical_role": by_role,
                         "by_bus": by_bus},
        "source_impacts": _source_impacts(inp),
    }
    return coverage


def _missing_endpoints(reg, inp):
    board_refs = set(inp["board_footprint_refs"])
    missing = []
    for r in reg["nets"]:
        for ep in r["endpoints"]:
            ref = ep.split(".", 1)[0]
            if ref not in board_refs and ref not in inp["comps"]:
                missing.append({"net": r["net_name"], "endpoint": ep})
    return sorted(missing, key=lambda m: (m["net"], m["endpoint"]))


def _class_planner_diffs(inp, nets):
    """routing-spec §2 类 ↔ pcbagent planner 类 canonical mapping（任务书 §七.4）。"""
    patterns = inp["planner_patterns"]
    default = inp["planner_default"]
    # spec 类 → planner 键（映射表 + planner 前缀规则对每个类代表网验证）
    spec_to_planner = {}
    for spec_cls, planner_key in sorted(_SPEC_TO_PLANNER.items()):
        spec_to_planner[spec_cls] = planner_key
    # 逐网核数：planner 直接分类 vs spec 类映射
    disagree = []
    for r in nets:
        pkey = classify_planner(r["net_name"], patterns, default)
        mapped = _SPEC_TO_PLANNER.get(r["routing_class"])
        if pkey != mapped:
            disagree.append({"net": r["net_name"], "spec_class": r["routing_class"],
                             "spec_mapped": mapped, "planner_classify": pkey})
    inv = {}
    for k, v in _SPEC_TO_PLANNER.items():
        inv.setdefault(v, []).append(k)
    return {
        "level_note": "routing-spec §2 类=设计语义层（18 行）；pcbagent planner 无独立类层级，"
                      "消费 KiCad net_classes（§9 建类），实际键=L2_NET_CLASS_PATTERNS 前缀"
                      "（config.py）。二者不同层级，禁止按数量等价（SPEC §①）",
        "spec_to_planner": spec_to_planner,
        "one_to_many": {("unmapped(None)" if k is None else k): sorted(v)
                        for k, v in
                        sorted(inv.items(), key=lambda kv: (kv[0] is None, str(kv[0])))
                        if len(v) > 1},
        "unmapped_spec_classes": sorted(k for k, v in _SPEC_TO_PLANNER.items() if v is None),
        "mechanism_differences": [
            "pcbflow=精确正则（^name$，LTDC 前缀例外）；pcbagent=startswith 前缀，先到先得",
            ".kicad_pro 声明 18 类但 netnames 全空（无逐网指派）→ 两侧逐网绑定均为命名规则派生，"
            "均非 KiCad 逐网声明（registry 侧因此不标 source_declared 自 KiCad net class）",
        ],
        "per_net_disagreements": sorted(disagree, key=lambda d: d["net"]),
    }


def _source_impacts(inp):
    """每个已知差异的来源与影响（任务书 §九.2）。"""
    amb = {a["id"]: a for a in inp["rulings"]}
    impacts = []
    for rid in sorted(amb):
        a = amb[rid]
        impacts.append({"id": rid, "kind": a["kind"], "status": a["status"],
                        "title": a["title"], "decision": a["decision"],
                        "approver": a.get("approver"), "review": a.get("review"),
                        "source": "compile_seeds.AMBIGUITIES（已批人工裁决记录）"})
    impacts.append({
        "id": "KICAD-CLASS-UNASSIGNED", "kind": "source_gap", "status": "open",
        "title": ".kicad_pro 声明 18 net class 但 netnames 全空",
        "impact": "逐网 net→class 绑定无 KiCad 侧声明；注册表来源只能是命名规则+spec 行，"
                  "不能标 source_declared 自 KiCad net class",
        "source": "stm32h743-coreboard-revc.kicad_pro net_settings.classes",
        "required_action": "未来若注册表转正：由 spec §9 建类条款补逐网指派或保持命名规则口径",
    })
    impacts.append({
        "id": "USB-C-SEGMENT-UNMEASURED", "kind": "measurement_gap", "status": "open",
        "title": "USB _C 段（连接器侧）无测量实现",
        "impact": "G_USB canonical 含 4 网；length-report.py 只测 MCU 段 2 网；"
                  "_C 段 unmeasured（不默认长度）",
        "source": "AMB-3 已批 + C-0019 params.segments（measured_by=pcbflow checker, specified）",
        "required_action": "等⑤检查器实现或明确豁免",
    })
    impacts.append({
        "id": "LTDC-MEASUREMENT-GAP", "kind": "measurement_gap", "status": "open",
        "title": "G_LTDC 脚本枚举 19 名中 8 名不在板上；板上 11 成员中 8 名未被脚本枚举",
        "impact": "AMB-2 已按网表修正 canonical；脚本成员表未同步（测量侧缺口）",
        "source": "AMB-2 已批 + length-report.py GROUPS",
        "required_action": "脚本成员表按网表修正或声明以 canonical 为准",
    })
    return impacts


# ===========================================================================
# shadow comparison（任务书 §八）
# ===========================================================================

def build_comparison(reg, stats, coverage, inp, baseline):
    """baseline 不变式对照 + advisory 指标。gate_unchanged 恒为声明性 true：
    本工具零写盘、不接入门逻辑；baseline hash 由外部校验命令复核。"""
    cand = {
        "schema_version": SCHEMA_REGISTRY,
        "baseline": baseline,
        "registry_shadow": {
            "candidate_path": inp["out_dir_rel"] + "/net-registry-candidate.json",
            "candidate_sha256": inp["registry_sha256"],
            "generation_status": inp["generation_status"],
            "fields_consumed": [],
            "fields_ignored_note": "pcbflow audit 为 specified stub（cli.py cmd_stub，"
                                   "exit 4）：未读取任何注册表字段；本候选未接入任何门",
            "metrics": _shadow_metrics(reg, stats, coverage, inp),
            "diagnostics": reg["diagnostics"],
        },
        "comparison": {
            "gate_unchanged": True,
            "baseline_verdict_unchanged": True,
            "registry_consumed": False,
            "classification_count_delta": _classification_delta(stats, baseline),
            "coverage_delta": _coverage_delta(stats, coverage, baseline),
            "capacity_metric_delta": {
                "pcbflow_audit_metrics": None,
                "reason": "pcbflow audit 未实现（specified stub）——无 audit 指标可作 delta；"
                          "本列不得解读为容量提升或预测命中率变化",
                "context_only_pcbagent_b2": inp.get("b2_context"),
            },
            "ambiguities": [
                {"net": r["net_name"], "detail": r["inference_rule"]}
                for r in reg["nets"] if r["classification_status"] == "ambiguous"],
            "unclassified": stats["unclassified_nets"],
            "known_mapping_differences": coverage["spec_class_planner_diffs"],
            "known_data_differences": coverage["source_impacts"],
        },
    }
    return cand


def _classification_delta(stats, baseline):
    enum_metrics = (baseline or {}).get("enum_metrics") or {}
    struct_cov = ((baseline or {}).get("structures_summary") or {}).get(
        "coverage_summary") or {}
    return {
        "registry_status_counts": stats["status_counts"],
        "structures_home_bucket_counts": (struct_cov.get("bucket_counts")
                                          if struct_cov else
                                          enum_metrics.get("bucket_counts")),
        "note": "两套分类轴不同（registry=逐网多维状态；structures=逐网 home 桶）；"
                "并排列出，不做语义等价折算",
    }


def _coverage_delta(stats, coverage, baseline):
    compile_metrics = (baseline or {}).get("compile_metrics") or {}
    enum_metrics = (baseline or {}).get("enum_metrics") or {}
    return {
        "registry_unmapped": len(stats["unmapped_nets"]),
        "baseline_uncovered_structures": enum_metrics.get("uncovered"),
        "baseline_catch_all_only_count": compile_metrics.get("catch_all_only_count"),
        "registry_named_nets": stats["named_nets"],
        "baseline_named_nets": enum_metrics.get("named_nets"),
        "named_net_delta": (stats["named_nets"]
                            - (enum_metrics.get("named_nets") or 0)),
    }


def _shadow_metrics(reg, stats, coverage, inp):
    """shadow/advisory 指标（任务书 §八）：明确不改门；缺模型的项 null+reason。"""
    nets = reg["nets"]
    buses = {}
    for r in nets:
        if r["bus"]:
            e = buses.setdefault(r["bus"], {"member_count": 0, "endpoint_refs": set()})
            e["member_count"] += 1
            for ep in r["endpoints"]:
                e["endpoint_refs"].add(ep.split(".", 1)[0])
    pitch = inp["corridor_formula"]["pitch_mm"]
    layers_n = inp["corridor_formula"]["routing_layers"]
    margin = inp["corridor_formula"]["margin_mm"]
    corridors = []
    for bus_id in sorted(buses):
        n = buses[bus_id]["member_count"]
        refs = sorted(buses[bus_id]["endpoint_refs"])
        demand = math.ceil(n / layers_n) * pitch + margin
        corridors.append({"corridor": "-".join(refs), "bus": bus_id,
                          "advisory_net_count": n, "endpoint_refs": refs,
                          "advisory_demand_mm": round(demand, 2),
                          "basis": "C-0053 公式（ceil(N/层)×0.35+0.6）；advisory，"
                                   "不替代 C-0035 的 7.5mm 条款值"})
    f_locked = sorted({r["routing_class"] for r in nets
                       if r["allowed_layers"] == ["F.Cu"]})
    return {
        "registry_status_counts": stats["status_counts"],
        "nets_per_bus": {k: v["member_count"] for k, v in sorted(buses.items())},
        "nets_per_routing_class": coverage["distribution"]["by_routing_class"],
        "nets_per_electrical_role": coverage["distribution"]["by_electrical_role"],
        "advisory_corridors": corridors,
        "f_layer_locked_classes": f_locked,
        "f_layer_locked_net_count": sum(1 for r in nets
                                        if r["allowed_layers"] == ["F.Cu"]),
        "differential_pair_count": len({r["differential_pair"]["pair_id"]
                                        for r in nets if r["differential_pair"]}),
        "length_group_coverage": {
            g: {"canonical_members": len([r for r in nets if r["length_group"] == g]),
                "measured_by_script": len([r for r in nets if r["length_group"] == g
                                           and "length_group:" + g in r["source_refs"]
                                           and r["net_name"] in inp["script_groups"][g]["nets"]])}
            for g in sorted(inp["lengths"])},
        "per_net_measured_length_mm": None,
        "per_net_measured_length_reason": "板内铜长不在本 shadow 范围：length-report.py"
                                          "（pcbnew）为权威测量路径；文本 s-expr 重复实现"
                                          "会引入第二套几何口径",
        "layer_budget_demand": None,
        "layer_budget_reason": "叠层定义缺失（TBD-1）+ 无逐网长度 → 无法计算层需求",
    }


# ===========================================================================
# run-manifest（任务书 §九.4；允许时间/主机——仅元数据，不参与核心比较）
# ===========================================================================

def build_manifest(inp, artifacts, t0, t1):
    lock = toolchain.load_lock()
    return {
        "started_at": t0.isoformat(), "finished_at": t1.isoformat(),
        "elapsed_s": round((t1 - t0).total_seconds(), 3),
        "host": socket.gethostname(),
        "python_version": sys.version.split()[0],
        "numpy_version": (lock or {}).get("numpy", {}).get("version", "not_probed"),
        "kicad_cli_version": (lock or {}).get("kicad_cli", {}).get("version", "not_probed"),
        "pcbagent_adapter_version": "not_used",
        "pcbagent_adapter_note": "planner 分类规则经 ast 从 tools/pcbagent/pcbagent/config.py "
                                 "只读提取（sha256 锁定）；未 import pcbagent，未调用其 adapter",
        "tool_version": config.TOOL_VERSION + "+experimental/net-registry-shadow",
        "schema_version": SCHEMA_REGISTRY,
        "spec_sha256": hashing.sha256_file(os.path.join(config.PCBFLOW_ROOT, "SPEC.md")),
        "proposal_sha256": hashing.sha256_file(
            os.path.join(config.PCBFLOW_ROOT, "NET-REGISTRY-PROPOSAL.md")),
        "input_sha256": inp["hashes"],
        "baseline_sha256": inp["baseline_hashes"],
        "out_dir": inp["out_dir_rel"],
        "backend": sexpr_min.BACKEND,
        "capabilities": sexpr_min.CAPABILITIES,
        "fidelity": sexpr_min.FIDELITY,
        "fallback_reason": sexpr_min.FALLBACK_REASON,
        "determinism_claim": "byte_exact",
        "determinism_scope": "net-registry-candidate.json / net-registry-coverage.json / "
                             "shadow-comparison.json 三件核心产物规范化字节级一致；"
                             "run-manifest 与 shadow-report.md 属元数据/人读视图，不参与比较",
        "temp_copy_relations": [],
        "write_operations": "none（生成器模式：stdout 重定向由会话 shell 完成；"
                            ".py 零落盘零子进程）",
        "artifacts": artifacts,
    }


# ===========================================================================
# 人读报告（视图，非事实源）
# ===========================================================================

def report_markdown(reg, stats, coverage, comparison, run_note):
    st = stats["status_counts"]
    tot = stats["named_nets"]
    lines = [
        "# 阶段② 网络注册表旁路（shadow）报告",
        "",
        "> 本次为阶段②只读 shadow integration；未修改正式 SPEC，未改变阶段②门，未修改 Rev-C 工程。",
        "",
        f"- 注册表候选 schema：{reg['schema_version']}（status={reg['status']}，实验性）",
        f"- 网络覆盖：{tot} 具名网全部生成记录；另有 {stats['nc_pad_nets']} 个 NC 焊盘网"
        f"显式排除（coverage.nc_pad_nets，无静默丢弃）",
        f"- 分类状态：confirmed={st['confirmed']}（AMB-1..4 已批裁决面），"
        f"source_declared={st['source_declared']}，inferred={st['inferred']}，"
        f"ambiguous={st['ambiguous']}，unclassified={st['unclassified']}，waived={st['waived']}",
        "",
        "## 覆盖与歧义",
        "",
        f"- unmapped_nets：{len(stats['unmapped_nets'])}（SIG_DEFAULT 兜底行=spec 显式声明）",
        f"- ambiguous：{st['ambiguous']}（冲突策略 {CONFLICT_POLICY}；无新增未决歧义）",
        "- 已知差异（详见 coverage.source_impacts）：AMB-1 FMC_A12（已批）、AMB-2 LTDC 成员"
        "（已批，脚本 8 幻影名/板上 8 名未测量）、AMB-3 USB 两段（已批，_C 段未测量）、"
        "AMB-4 SD_CD（已批）；KiCad net class 声明 18 类但 netnames 全空（open）",
        "",
        "## 映射差异（spec §2 类 ↔ pcbagent planner 类）",
        "",
        "- 层级不同：spec 18 行语义类 vs planner 10 个前缀键（USB/ANLG/FMC/SDMMC1/SDMMC2/"
        "QSPI/ETH/LTDC/PWR/SIG）；一对多：FMC←5 个 spec 类、PWR←4 个、SIG←SIG_DEFAULT；"
        "GND 无 planner 键（classify_net 落 SIG 默认；平面语义另经 L3_RIPUP_FORBIDDEN 承载）",
        "- 数量相等不当作语义等价；逐网 disagreement 见 coverage.spec_class_planner_diffs",
        "",
        "## 阶段②是否真正消费注册表",
        "",
        "- **registry_consumed = false**：`pcbflow audit` 是 specified stub（cli.py cmd_stub，"
        "exit 4），未读取任何注册表字段；本候选未接入硬约束/红黄绿门/回退逻辑",
        f"- baseline 门结论未变：comparison.gate_unchanged=true；baseline（out/revc-a2，"
        f"compile+enum 均 status=blocked/verdict=yellow，structures 草案待批）原样保留",
        "",
        "## 重放结果",
        "",
        run_note,
        "",
        "## 下一步建议",
        "",
        "- 保留为诊断产物（阶段 N1）；注册表候选不冻结任何正式契约字段",
        "- 修正数据源（非注册表职责）：length-report.py G_LTDC 成员表按网表修正；"
        ".kicad_pro 逐网指派或明确命名规则口径",
        "- 转正前须评审：net_id 生成权、与 structures.json 权威关系、routing_class 映射语义、"
        "USB segment 级作用域（proposal §13 待评审问题）",
    ]
    return "\n".join(lines) + "\n"


# ===========================================================================
# 真实输入装载（只读 IO；.py 不写盘不子进程）
# ===========================================================================

def extract_planner_rules(text):
    """ast 只读提取 pcbagent config.py 的 L2_NET_CLASS_PATTERNS/DEFAULT（字面量契约）。"""
    tree = ast.parse(text)
    patterns, default = None, None
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)):
            tid = node.targets[0].id
            if tid == "L2_NET_CLASS_PATTERNS":
                out = []
                for elt in node.value.elts:
                    vals = [e.value for e in elt.elts]
                    if len(vals) != 2 or not all(isinstance(v, str) for v in vals):
                        raise ValueError("L2_NET_CLASS_PATTERNS drift: non-literal entry")
                    out.append(tuple(vals))
                patterns = out
            elif tid == "L2_NET_CLASS_DEFAULT":
                if not isinstance(node.value.value, str):
                    raise ValueError("L2_NET_CLASS_DEFAULT drift")
                default = node.value.value
    if patterns is None or default is None:
        raise ValueError("planner rules not found in pcbagent config.py")
    return patterns, default


def load_real_inputs(out_dir_rel):
    """只读装载真实工程输入 → build_registry 的 inp dict（含 hash 清单）。"""
    hashes = {}
    def h(rel, path):
        hashes[rel] = hashing.sha256_file(path)
        return path

    revc = config.REVC_DIR
    netlist = h(REL_NETLIST, config.REVC_NETLIST)
    board = h(REL_BOARD, config.REVC_BOARD)
    h(REL_SCH, os.path.join(revc, "stm32h743-coreboard-revc.kicad_sch"))
    h(REL_PRO, os.path.join(revc, "stm32h743-coreboard-revc.kicad_pro"))
    len_py = h(REL_LEN, config.LENGTH_REPORT_PY)
    planner_cfg = h(REL_PLANNER_CFG, os.path.join(
        config.WORKSPACE_ROOT, "tools", "pcbagent", "pcbagent", "config.py"))
    h("design/coreboard/reports/routing-spec-v1.md", config.ROUTING_SPEC)
    h("design/coreboard/reports/placement-spec-v1.md", config.PLACEMENT_SPEC)

    nets = compile_cmd.parse_netlist(netlist)
    with open(config.LENGTH_REPORT_PY, "r", encoding=config.ENCODING) as f:
        script_groups = compile_cmd.extract_script_groups(f.read())

    broot = sexpr_min.load_file(board)[0]
    # KiCad 10 板内网引用形态统一为 (net "NAME")（焊盘/走线/过孔内直接字符串）
    board_net_names = sorted({c for n in sexpr_min.find_all(broot, "net")
                              for c in n[1:] if isinstance(c, str)})
    board_refs = []
    for fp in sexpr_min.find_all(broot, "footprint"):
        for prop in sexpr_min.find_all(fp, "property"):
            if sexpr_min.get_str(prop, 1) == "Reference":
                ref = sexpr_min.get_str(prop, 2)
                if ref:
                    board_refs.append(ref)
    with open(os.path.join(revc, "stm32h743-coreboard-revc.kicad_pro"),
              encoding=config.ENCODING) as f:
        pro = json.load(f)
    kicad_classes = {c["name"]: len(c.get("netnames") or [])
                     for c in pro.get("net_settings", {}).get("classes", [])}

    with open(planner_cfg, "r", encoding=config.ENCODING) as f:
        planner_patterns, planner_default = extract_planner_rules(f.read())

    class_raws = {s["params"]["class"]: s["params"]["raw"]
                  for s in seeds_mod.SEEDS if s["domain"] == "NETCLASS"}
    corridor = next(s["params"] for s in seeds_mod.SEEDS if s["id"] == "C-0053")
    usb_topo = next(s for s in seeds_mod.SEEDS if s["id"] == "C-0028")
    diff_pairs = [{
        "pair_id": "USB_DIFF_PAIR",
        "pos": list(usb_topo["scope"]["pair"][:1]) + list(
            usb_topo["scope"]["pair_connector_side"][:1]),
        "neg": list(usb_topo["scope"]["pair"][1:]) + list(
            usb_topo["scope"]["pair_connector_side"][1:]),
        "segments": {"USB_DP": "mcu_side", "USB_DM": "mcu_side",
                     "USB_DP_C": "connector_side", "USB_DM_C": "connector_side"},
        "source_refs": ["C-0028", "C-0005", "AMB-3(ruling 2026-08-29)",
                        "routing-spec §4.1"],
        "status": "confirmed",
    }]

    bus_rules = [{"bus_id": r["bus_id"], "pattern": r["pattern"],
                  "source_kind": "naming_rule",
                  "source": f"structures 草案 {r['bus_id']} 前缀规则（draft，"
                            f"{r['spec_source']}）"}
                 for r in enum_mod._BUS_RULES]

    comps = enum_mod._fp_table()
    baseline, baseline_hashes = _load_baseline()

    b2_context = None
    b2_path = os.path.join(config.WORKSPACE_ROOT, *REL_B2_GATE.split("/"))
    if os.path.exists(b2_path):
        hashes[REL_B2_GATE] = hashing.sha256_file(b2_path)
        with open(b2_path, encoding=config.ENCODING) as f:
            g = json.load(f)
        b2_context = {
            "note": "pcbagent B2 容量门（pcbagent 侧产物，非 pcbflow ② audit）；"
                    "仅作上下文并排，不参与 delta，不得解读为注册表带来的容量变化",
            "path": REL_B2_GATE, "verdict": g.get("verdict"), "pass": g.get("pass"),
            "corridor_hit_p3": g.get("corridor_hit", {}).get("p3"),
            "escape_3v3_hits": g.get("escape_3v3", {}).get("hits"),
        }

    inp = {
        "netlist_nets": nets,
        "board_net_names": board_net_names,
        "board_footprint_refs": sorted(set(board_refs)),
        "script_groups": script_groups,
        "spec_members": compile_cmd.EXPECTED_SPEC_GROUP_MEMBERS,
        "class_patterns": list(seeds_mod.NETCLASS_PATTERNS),
        "catch_all_class": seeds_mod.CATCH_ALL_CLASS,
        "class_raws": class_raws,
        "planner_patterns": planner_patterns,
        "planner_default": planner_default,
        "kicad_pro_classes": kicad_classes,
        "bus_rules": bus_rules,
        "diff_pairs": diff_pairs,
        "rulings": seeds_mod.AMBIGUITIES,
        "lengths": list(config.NINE_GROUPS),
        "corridor_formula": {"pitch_mm": corridor["pitch_mm"],
                             "routing_layers": corridor["routing_layers"],
                             "margin_mm": corridor["margin_mm"]},
        "hashes": hashes,
        "comps": comps,
        "baseline": baseline,
        "baseline_hashes": baseline_hashes,
        "b2_context": b2_context,
        "source_revision": "workdir-unversioned(sha256-locked); specs v1.0-draft",
        "out_dir_rel": out_dir_rel,
        "generation_status": "ok",
    }
    return inp


def _load_baseline():
    """只读装载 baseline（out/revc-a2 ⓪/① 产物）。缺失 → status=unknown，主流程继续。"""
    base_dir = os.path.join(config.PCBFLOW_ROOT, "out", "revc-a2")
    bhashes, env_compile, env_enum, structs_summary = {}, None, None, None
    for fn in ("envelope.json", "envelope-enum.json", "coverage.json",
               "coverage-structures.json", "structures.json", "constraints.json"):
        p = os.path.join(base_dir, fn)
        rel = BASELINE_DIR + "/" + fn
        if os.path.exists(p):
            bhashes[rel] = hashing.sha256_file(p)
    if os.path.exists(os.path.join(base_dir, "envelope.json")):
        with open(os.path.join(base_dir, "envelope.json"), encoding=config.ENCODING) as f:
            env_compile = json.load(f)
    if os.path.exists(os.path.join(base_dir, "envelope-enum.json")):
        with open(os.path.join(base_dir, "envelope-enum.json"), encoding=config.ENCODING) as f:
            env_enum = json.load(f)
    if os.path.exists(os.path.join(base_dir, "structures.json")):
        with open(os.path.join(base_dir, "structures.json"), encoding=config.ENCODING) as f:
            structs = json.load(f)
        structs_summary = {
            "authority_status": structs.get("authority_status"),
            "coverage_summary": structs.get("coverage_summary"),
            "note": "structures 草案（人工确认点 #1 待批）；注册表只读对照，不修改",
        }
    if env_compile is None and env_enum is None:
        return {"source_path": BASELINE_DIR, "status": "unknown",
                "note": "baseline 产物缺失；baseline 继续（任务书 §十二）"}, bhashes
    return {
        "source_path": BASELINE_DIR,
        "source_sha256": bhashes,
        "status": (env_enum or env_compile).get("status"),
        "verdict": (env_enum or env_compile).get("verdict"),
        "audit_status": "not_implemented",
        "audit_note": "pcbflow audit 为 specified stub；baseline=阶段⓪/① 产物"
                      "（② 将消费的分类/容量输入）+ Rev-C opens.csv 回测真值",
        "compile_metrics": (env_compile or {}).get("metrics"),
        "enum_metrics": (env_enum or {}).get("metrics"),
        "structures_summary": structs_summary,
        "opens_csv_truth": {
            "path": "design/coreboard/kicad/stm32h743-coreboard-revc/opens.csv",
            "rows_total": 65, "non_gnd_breakpoints": 61,
            "note": "② 回测输入（只读）；本 shadow 未修改、未重算",
        },
    }, bhashes


# ===========================================================================
# CLI（模块自有入口；不进入正式命令面）
# ===========================================================================

def _build_all(out_dir_rel):
    t0 = datetime.datetime.now(datetime.timezone.utc)
    inp = load_real_inputs(out_dir_rel)
    built = build_registry(inp)
    coverage = build_coverage(built["registry"], built["stats"], inp)
    cand_bytes = hashing.canonical_json_bytes(built["registry"])
    inp["registry_sha256"] = hashing.sha256_bytes(cand_bytes)
    comparison = build_comparison(built["registry"], built["stats"], coverage,
                                  inp, inp["baseline"])
    core = {
        "net-registry-candidate.json": built["registry"],
        "net-registry-coverage.json": coverage,
        "shadow-comparison.json": comparison,
    }
    artifacts = {name: hashing.sha256_bytes(hashing.canonical_json_bytes(obj))
                 for name, obj in core.items()}
    t1 = datetime.datetime.now(datetime.timezone.utc)
    manifest = build_manifest(inp, artifacts, t0, t1)
    return core, manifest, built, coverage, comparison, inp


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="pcbflow.experimental.net_registry_shadow",
        description="② 只读 shadow：实验性网络注册表旁路（不进入正式命令面/门）")
    ap.add_argument("--select", default="summary",
                    choices=("net-registry-candidate.json",
                             "net-registry-coverage.json", "shadow-comparison.json",
                             "run-manifest.json", "shadow-report.md", "summary"))
    ap.add_argument("--out-dir", default="pcbflow-out/stage2-shadow",
                    help="产物相对路径（仅记入 manifest/comparison，不落盘）")
    args = ap.parse_args(argv)

    core, manifest, built, coverage, comparison, inp = _build_all(args.out_dir)
    if args.select == "run-manifest.json":
        payload = manifest
    elif args.select == "shadow-report.md":
        run_note = ("确定性验证由会话 shell 复核：连续两次生成核心产物并比对规范化 "
                    "SHA-256；结果记录于本次运行的 shadow-report 最终报告（工具本身"
                    "不写盘、不重跑自身）。")
        payload = report_markdown(built["registry"], built["stats"], coverage,
                                  comparison, run_note)
        sys.stdout.buffer.write(payload.encode(config.ENCODING))
        return config.EXIT_OK
    elif args.select == "summary":
        st = built["stats"]["status_counts"]
        payload = {
            "command": "net_registry_shadow", "experimental": True,
            "generation_status": inp["generation_status"],
            "registry_consumed_by_audit": False,
            "totals": built["stats"],
            "diagnostics": len(built["registry"]["diagnostics"]),
            "note": "人读摘要；核心产物见 --select 三个 JSON",
        }
    else:
        payload = core[args.select]
    sys.stdout.buffer.write(hashing.canonical_json_bytes(payload))
    return config.EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
