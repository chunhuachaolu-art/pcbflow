"""① 结构枚举（pcbflow enum）。纯内存构建、零落盘、零子进程（生成器模式）。

SPEC §①：网络表图分析先产出候选，再由显式结构声明或人工确认生成五类结构
（接口组/时序组/电源树/回流树/散件）+ 锚件 + 优先级 + canonical mapping。
本实现（FA2）产出 structures **草案**（authority_status=draft）：
  - 自动枚举候选：网名规则 + 网表端点表（封装+引脚集）全部数据推导；
  - canonical mapping：含 AMB-1..4 已批裁决（2026-08-29）落库记录；
  - 全量网络覆盖报告：160 具名网逐网 home 归属，uncovered 必须为空。
人工确认点 #1（HANDOFF §3）：structures 草案经用户批准后方为权威 →
批准前 ① 门"候选全量覆盖"半边已过、"显式确认"半边 pending →
envelope status=blocked / verdict=yellow（同 ⓪ 口径：阻权威确认，不阻建造）。

优先级三分报告（SPEC §1.1）：routing-spec §9 执行顺序、pcbagent planner 顺序、
PCBFlow 优化顺序分别列出，不默认同一排序。
"""

from __future__ import annotations

import datetime
import os
import re
import socket
import sys

from . import compile_cmd, compile_seeds as seeds_mod, config, envelope, hashing
from . import net_registry, profile_loader, sexpr_min, toolchain

PROJECT_ID = compile_cmd.PROJECT_ID

# G0（REPAIR-P4 W-1）：Rev-C 规则表（总线/电源树/锚件/优先级/三序/组映射）
# 自 profiles/revc-coreboard/profile.json 的 enum 节装载；语义注释随值迁
# profile note，代码保留装载位说明。
_pf = profile_loader.load_profile(config.PCBFLOW_ROOT)
_pf_enum = profile_loader.require(_pf, "enum")

# ---- 总线候选规则（有序、互斥前缀；成员以板上网表实际为准） ----------------
# symmetry_class 引用对称条款约束（C-0028 usb_pair / C-0029 fmc_byte_lanes）
_BUS_RULES = profile_loader.require(_pf_enum, "bus_rules")

# ---- 电源树边（spec 条款 + 网表共享器件验证；验证失败如实报告） ------------
# 注意：初稿按 spec 文本写的「VBUS_RAW→F1→5V」「3V3→FB1→VDDA」两条边被
# 网表验证机制否决（F1 实际馈入 5V_USB；FB1 实际为 VDDA→VREF+ 滤波）。
# 以下边以网表实测拓扑为准，spec 条款作旁证（历史调参记录，随值在 profile）。
_POWER_EDGES = profile_loader.require(_pf_enum, "power_edges")

# 电流预算：spec 未给数值 → null + pending 说明（不虚构）；最小线宽取 §2 类行 raw

# ---- 锚件（SPEC §① 清单：连接器/U1/U2/晶振/USB 保护） ----------------------
_ANCHORS = [tuple(a) for a in profile_loader.require(_pf_enum, "anchors")]
_ANCHOR_LOCK = profile_loader.require(_pf_enum, "anchor_lock")

# ---- 优先级作用域（SPEC §1.1 八项，全部带 rank/tie_break/source） -----------
# 跨总线顺序来自项目规范（routing §9 明确点名前五，其余按 §2 表行序追加=派生
# 决定，见 STR-2；逐项 source 文本随值在 profile enum.priorities）
_PRIORITIES = profile_loader.require(_pf_enum, "priorities")

# 三份执行顺序分别报告（SPEC §1.1：不得默认为同一排序）
_THREE_ORDERS = profile_loader.require(_pf_enum, "three_orders")


def _fp_table():
    """网表 → {ref: {"value","footprint"}}（确定性）。"""
    top = sexpr_min.load_file(config.REVC_NETLIST)
    root = top[0]
    comps = {}
    for comp in sexpr_min.find_all(root, "comp"):
        ref = sexpr_min.get_str(sexpr_min.find_first(comp, "ref"))
        if ref is None:
            continue
        fp = sexpr_min.find_first(comp, "footprint")
        comps[ref] = {
            "value": sexpr_min.get_str(sexpr_min.find_first(comp, "value")),
            "footprint": sexpr_min.get_str(fp) if fp is not None else None,
        }
    return comps


def _crystal_load_caps(nets):
    """晶体负载电容（HSE/LSE 网上的电容），供电源树去耦排除与散件标注。"""
    loads = set()
    for net, nodes in nets.items():
        if net in ("HSE_IN", "HSE_OUT", "LSE_IN", "LSE_OUT"):
            for node in nodes:
                if re.match(r"^C\d+$", node["ref"]):
                    loads.add(node["ref"])
    return loads


# G0：组→网类映射与组拓扑约束文本自 profile enum 节装载
_CLASS_OF_GROUP = profile_loader.require(_pf_enum, "class_of_group")

_GROUP_TOPOLOGY = profile_loader.require(_pf_enum, "group_topology")


def _group_allowed_layers_raw(g):
    """组内各网络类的 §2 表行 raw（允许层的权威载体，不在此转录改写）。"""
    rows = []
    for cls in _CLASS_OF_GROUP[g]:
        seed = next(s for s in seeds_mod.SEEDS
                    if s["domain"] == "NETCLASS" and s["params"]["class"] == cls)
        rows.append({"net_class": cls, "raw": seed["params"]["raw"]})
    return rows


def _canonical_groups(net_names, script_groups):
    """九组 canonical 成员（按已批裁决；与 ⓪ nine_group_comparison 同口径）。

    返回 {group: {"members": [...], "basis": str}}。
    """
    amb = {a["id"]: a["status"] for a in seeds_mod.AMBIGUITIES}
    out = {}
    for g in config.NINE_GROUPS:
        sg = script_groups[g]
        if g == "G_LTDC":
            out[g] = {
                "members": sorted(n for n in net_names
                                  if n.startswith("LTDC_") and n != sg["ref"]),
                "basis": "AMB-2 已批（2026-08-29）：Rev-C 网表实际为准"
                         "（spec 23 网声明登记差异，waiver 复审）",
            }
            continue
        spec = compile_cmd.EXPECTED_SPEC_GROUP_MEMBERS[g]
        script = set(sg["nets"])
        if spec and set(spec) != script:
            amb_id = compile_cmd._group_ambiguity(g)
            if amb_id and amb.get(amb_id) == "resolved":
                out[g] = {"members": sorted(set(spec) | script),
                          "basis": f"{amb_id} 已批裁决并集（见 mapping.rulings_consumed）"}
                continue
        out[g] = {"members": sorted(script),
                  "basis": "spec §2 类行 = 脚本 = 网表一致"}
    return out


def build_products(out_dir_rel=config.load_project_manifest().out_dirs["enum"]):
    """返回 {name: {"obj","bytes","sha256"}}。全程内存；写盘由调用方重定向。"""
    t0 = datetime.datetime.now(datetime.timezone.utc)

    # 输入（与 ⓪ 同源，只读）
    nets = compile_cmd.parse_netlist(config.REVC_NETLIST)
    net_names = sorted(nets)
    named_nets = [n for n in net_names if not n.startswith("unconnected-")]
    with open(config.LENGTH_REPORT_PY, "r", encoding=config.ENCODING) as f:
        script_groups = compile_cmd.extract_script_groups(f.read())
    comps = _fp_table()
    input_hashes = {
        compile_cmd._rel(p): hashing.sha256_file(p)
        for p in (config.REVC_NETLIST, config.LENGTH_REPORT_PY)
    }
    canonical = _canonical_groups(named_nets, script_groups)

    def length_group_of(net):
        """网 → 九组归属（按 canonical 成员；参考网同组标注）。"""
        for g in config.NINE_GROUPS:
            if net in canonical[g]["members"] or net == script_groups[g]["ref"]:
                return g
        return None

    # 1) 总线候选（前缀规则 ∩ 板上实际；端点表全数据推导）
    buses = []
    bus_of = {}
    for rule in _BUS_RULES:
        rx = re.compile(rule["pattern"])
        members = sorted(n for n in named_nets if rx.match(n))
        if not members:
            continue
        endpoints = {}
        for m in members:
            for node in nets[m]:
                ref, pin = node["ref"], node["pin"]
                e = endpoints.setdefault(ref, {
                    "footprint": (comps.get(ref) or {}).get("footprint"),
                    "value": (comps.get(ref) or {}).get("value"),
                    "pins": [],
                })
                e["pins"] = sorted(set(e["pins"]) | {pin})
        buses.append({
            "bus_id": rule["bus_id"], "title": rule["title"],
            "members": members, "member_count": len(members),
            "endpoints": {ref: endpoints[ref] for ref in sorted(endpoints)},
            "endpoint_refs": sorted(endpoints),
            "symmetry_class": rule["symmetry_class"],
            "symmetry_constraint": rule["symmetry_constraint"],
            "length_groups": sorted({g for g in (length_group_of(m) for m in members) if g}),
            "spec_source": rule["spec_source"],
            "status": "draft_candidate",  # 批准后方为权威（人工确认点 #1）
        })
        for m in members:
            bus_of[m] = rule["bus_id"]

    # 2) 电源树（轨成员网表推导；边按 spec 声明 + 共享器件验证）
    crystal_loads = _crystal_load_caps(nets)
    power_rails = {}
    power_nets = set()
    for net in named_nets:
        cls = compile_cmd._match_class(net)
        if cls and cls.startswith("PWR_"):
            power_nets.add(net)
    for net in sorted(power_nets):
        refs = {}
        for node in nets[net]:
            refs.setdefault(node["ref"], []).append(node["pin"])
        cls = compile_cmd._match_class(net)
        class_seed = next(s for s in seeds_mod.SEEDS
                          if s["domain"] == "NETCLASS" and s["params"]["class"] == cls)
        power_rails[net] = {
            "net_class": cls,
            "refs": {r: sorted(p) for r, p in sorted(refs.items())},
            "decoupling_caps": sorted(r for r in refs
                                      if re.match(r"^C\d+$", r) and r not in crystal_loads),
            "min_width_raw": class_seed["params"]["raw"],
            "current_budget_a": None,
            "budget_note": "spec 未给支路电流数值（缺失源 fab/stackup/接口规范关联）；不虚构，pending",
        }
    power_edges = []
    for e in _POWER_EDGES:
        shared = None
        for bridge in ([e["bridge_ref"]] if isinstance(e["bridge_ref"], str)
                       else (e["bridge_ref"] or [])):
            refs_from = {n["ref"] for n in nets.get(e["from"], [])}
            refs_to = {n["ref"] for n in nets.get(e["to"], [])}
            if bridge in refs_from and bridge in refs_to:
                shared = bridge
                break
        power_edges.append({
            "from": e["from"], "to": e["to"],
            "bridge_ref": e["bridge_ref"], "bridge_desc": e["bridge_desc"],
            "validated_by_shared_ref": shared,
            "source": e["source"],
        })
    power_tree = {
        "rails": power_rails,
        "edges": power_edges,
        "topology_rule": "单点树状、不环回（routing §7.1）；去耦归属随 IC 成组（placement §4.2，"
                         "IC 级归属表待③ 布局期从坐标导出）",
        "status": "draft_candidate",
    }

    # 3) 回流树（层角色/缝合/功率环路，全部条款引用）
    return_tree = {
        "planes": {
            "In1.Cu": "完整 GND 平面，禁信号（≤2mm 批准短跳例外 C-0040）",
            "B.Cu": "完整 GND 平面，默认无信号（批准电源短跳）",
        },
        "regions": [
            {"region": "F.Cu 逃逸/关键短距", "signals": ["USB 对", "晶振", "去耦就近", "逃逸≤3mm"],
             "intended_return": "In1.Cu", "source": "routing-spec §1/§5.3"},
            {"region": "In2.Cu 主干（U1↔U2/北南向）", "signals": ["FMC 等总线主干"],
             "intended_return": "In1.Cu + B.Cu", "source": "routing-spec §1/§5.2"},
            {"region": "analog 角（NW）", "signals": ["ADC/VREF/晶体"],
             "intended_return": "GNDA 单点经 FB1 接 GND；数字线禁穿",
             "source": "routing-spec §6.6 + placement §5"},
        ],
        "stitching": {"grid_mm": 8.0, "dense_mm": 4.0,
                      "dense_regions": ["J5_shell", "U3_below", "connector_rows"],
                      "source": "routing-spec §6.3 / C-0039"},
        "power_loop": {"loop": "Cin-SW_NODE-L1-3V3 Cout 外包络",
                       "refs": ["U3", "L1"],
                       "budget_mm2": [15, 10], "limit_mm2": [20, 12],
                       "source": "C-0046 / routing §7.4 / placement §2.5"},
        "status": "draft_candidate",
    }

    # 4) 锚件 + 分区
    anchors = [{
        "ref": ref, "role": role,
        "footprint": (comps.get(ref) or {}).get("footprint"),
        "lock": _ANCHOR_LOCK, "source": src, "status": "draft_candidate",
    } for ref, role, src in _ANCHORS]
    zones = [
        {"zone": "power_SW", "rule": "电源区固定 SW 角，远离晶振/模拟/USB；功率环路不跨信号区",
         "refs": ["U3", "L1", "Q1", "Q2", "F1"], "source": "placement §5"},
        {"zone": "analog_NW", "rule": "ADC/VREF 模拟角，GNDA 单点接地", "refs": None,
         "source": "placement §5（成员按坐标在③期落位判定）"},
        {"zone": "crystal_NE", "rule": "晶振区 U1 引脚旁，3mm 净空", "refs": ["Y1", "Y2"],
         "source": "placement §5/§6.1"},
        {"zone": "north_J2", "rule": "J2 低速 GPIO/调试簇北边", "refs": ["J2"],
         "source": "placement §5"},
        {"zone": "south_J1_J5", "rule": "J1+J5(SE) 南边", "refs": ["J1", "J5"],
         "source": "placement §5"},
    ]

    # 5) 散件 + 逐网 home 归属（全量覆盖：named 网 100% 落桶）
    gnd_nets = sorted(n for n in named_nets if compile_cmd._match_class(n) == "GND")
    analog_loose = sorted(n for n in named_nets if n not in bus_of
                          and compile_cmd._match_class(n) == "ANLG")
    loose = sorted(n for n in named_nets if n not in bus_of
                   and n not in gnd_nets and n not in power_nets
                   and n not in analog_loose)
    loose_entries = [{
        "net": n, "kind": "analog_point" if n in analog_loose else "gpio_point",
        "note": ("点对点短走线，仍受 ANLG/晶体条款（C-0032）" if n in analog_loose
                 else "点对点，不进骨架就近平铺；电气/DFM 约束经 net_class 绑定"),
    } for n in analog_loose + loose]
    loose_struct = {
        "entries": loose_entries,
        "count": len(loose_entries),
        "rule": "点对点 GPIO/模拟——不进骨架，就近平铺；仍必须有电气/DFM 约束（SPEC §①）",
        "status": "draft_candidate",
    }

    # 逐网 home 表（覆盖证据；一网一 home，时序组为附加标注不占 home）
    net_home = {}
    for n in named_nets:
        if n in bus_of:
            home, ref = "bus", bus_of[n]
        elif n in gnd_nets:
            home, ref = "return_tree", "GND"
        elif n in power_nets:
            home, ref = "power_tree", n
        elif n in analog_loose:
            home, ref = "loose", "analog_point"
        else:
            home, ref = "loose", "gpio_point"
        rec = {"home": home, "ref": ref,
               "net_class": compile_cmd._match_class(n),
               "length_group": length_group_of(n)}
        if home == "bus" and ref == "BUS_FMC":
            rec["corridor"] = "U1-U2"
        net_home[n] = rec
    uncovered = sorted(n for n in named_nets if n not in net_home)
    bucket_counts = {
        "bus": sum(1 for v in net_home.values() if v["home"] == "bus"),
        "power_tree": sum(1 for v in net_home.values() if v["home"] == "power_tree"),
        "return_tree": sum(1 for v in net_home.values() if v["home"] == "return_tree"),
        "loose": sum(1 for v in net_home.values() if v["home"] == "loose"),
    }

    # 6) canonical mapping（三类映射 + 九组 canonical + 已批裁决记录）
    amb_resolved = [a for a in seeds_mod.AMBIGUITIES if a["status"] == "resolved"]
    timing_groups = {}
    for g in config.NINE_GROUPS:
        seed = next(s for s in seeds_mod.SEEDS
                    if s["domain"] == "LENGTH" and s["scope"]["group"] == g)
        params = seed["params"]
        measurement = dict(params["measurement"])
        if "segments" in params:
            measurement["segments"] = params["segments"]
        timing_groups[g] = {
            "canonical_members": canonical[g]["members"],
            "canonical_basis": canonical[g]["basis"],
            "reference_net": script_groups[g]["ref"],
            "tolerance_mm": {"target": params["target_mm"], "limit": params["limit_mm"]},
            "measurement": measurement,
            "allowed_layers_raw": _group_allowed_layers_raw(g),
            "topology_constraint": _GROUP_TOPOLOGY[g],
            "segment_budget": {"mechanism": "走廊段预算由②走廊容量/③骨架段填数",
                               "filled": False},
            "constraint_id": compile_cmd._group_constraint_id(g),
        }
    mapping = {
        "net_class_to_planner": {
            "level_note": "routing-spec §2 网络类=设计语义层；pcbagent planner 无独立类层级，"
                          "直接消费 KiCad net_classes（§9 建类）。二者不同层级，"
                          "禁止按类数量直接等价（SPEC §①）",
            "pcbagent_class_basis": "kicad net_classes（routing-spec §9 建类条款）",
        },
        "planner_to_length_groups": {
            g: {"kicad_net_classes": _CLASS_OF_GROUP[g],
                "canonical_members": timing_groups[g]["canonical_members"],
                "member_count": len(timing_groups[g]["canonical_members"])}
            for g in config.NINE_GROUPS
        },
        "timing_groups": timing_groups,
        "rulings_consumed": [{"id": a["id"], "decision": a["decision"],
                              "decided_on": a["decided_on"], "approver": a["approver"],
                              "review": a["review"], "applied_to": a["applied_to"]}
                             for a in amb_resolved],
    }

    # 7) 枚举新发现（spec/网表结构差异，如实登记不择一）
    findings = _findings(buses)

    structures = {
        "schema_version": config.SCHEMA_STRUCTURES,
        "project": PROJECT_ID,
        "stage": 1,
        "authority_status": "draft",  # 人工确认点 #1：批准后置 approved（structures.override.json）
        "authority_note": "SPEC §①/HANDOFF §3：显式结构声明经用户批准后方为权威；本文件为 FA2 草案",
        "buses": buses,
        "power_tree": power_tree,
        "return_tree": return_tree,
        "anchors": anchors,
        "zones": zones,
        "loose": loose_struct,
        "priorities": {**_PRIORITIES, "three_orders_report": _THREE_ORDERS},
        "mapping": mapping,
        "findings": findings,
        "coverage_summary": {
            "named_nets": len(named_nets),
            "home_assigned": len(net_home),
            "uncovered": uncovered,
            "bucket_counts": bucket_counts,
            "crystal_load_caps": sorted(crystal_loads),
        },
    }

    # 8) coverage-structures.json（① 追加证据：逐网 home + 候选表 + 新发现）
    cov_struct = {
        "schema_version": config.SCHEMA_COVERAGE,
        "project": PROJECT_ID,
        "stage": 1,
        "role": "① 追加证据（⓪ coverage.json 的增量；成员/歧义裁决以 ⓪ 产物为准）",
        "rulings_consumed": [a["id"] for a in amb_resolved],
        "net_home_assignment": net_home,
        "candidate_bus_table": [{"bus_id": b["bus_id"], "member_count": b["member_count"],
                                 "endpoint_refs": b["endpoint_refs"],
                                 "length_groups": b["length_groups"]}
                                for b in buses],
        "new_diffs": findings,
        "coverage": {"named_nets": len(named_nets), "assigned": len(net_home),
                     "uncovered": uncovered},
        "source_notes": [
            {"id": "SN-S1", "note": "候选成员一律取板上网表实际（含 AMB-1/2 裁决结果）；"
                                    "spec 成员差异保留在 ⓪ coverage.nine_group_comparison，不重复"},
            {"id": "SN-S2", "note": "锚件/分区表按 SPEC §① 清单 + placement §1/§5 起草；"
                                    "坐标级归属（去耦→IC）在③期由布局数据导出"},
            {"id": "SN-S3", "note": "电流预算未定（缺失源）；power_tree.current_budget_a=null 不虚构"},
        ],
    }

    # 9) 门判定：候选全量覆盖=必过项；结构权威确认=人工确认点 #1（pending）
    if uncovered:
        status, verdict = "failed", "red"
    else:
        # 权威确认 pending → blocked（同 ⓪ 口径：阻权威，不阻建造）
        status, verdict = "blocked", "yellow"

    # 10) 网络注册表（SPEC §1.1/§1.2：① 正式成档，绑定 structures snapshot hash；
    #     v1.2 adoption——FA3 起历史 shadow（registry_consumed=false）保持原样）
    products_pre = {}
    for name, obj in (("structures", structures), ("coverage", cov_struct)):
        data = hashing.canonical_json_bytes(obj)
        products_pre[name] = {"obj": obj, "bytes": data, "sha256": hashing.sha256_bytes(data)}
    registry, identity_map, reg_stats = net_registry.build(
        structures, products_pre["structures"]["sha256"], nets,
        script_groups=script_groups)

    products = dict(products_pre)
    for name, obj in (("net_registry", registry), ("net_identity_map", identity_map)):
        data = hashing.canonical_json_bytes(obj)
        products[name] = {"obj": obj, "bytes": data, "sha256": hashing.sha256_bytes(data)}

    inputs = [
        {"path": compile_cmd._rel(config.REVC_NETLIST),
         "sha256": input_hashes[compile_cmd._rel(config.REVC_NETLIST)], "role": "netlist"},
        {"path": compile_cmd._rel(config.LENGTH_REPORT_PY),
         "sha256": input_hashes[compile_cmd._rel(config.LENGTH_REPORT_PY)], "role": "script"},
    ]
    artifacts = [
        {"path": f"{out_dir_rel}/structures.json", "sha256": products["structures"]["sha256"],
         "role": "core"},
        # ① 增量覆盖证据与 ⓪ coverage.json 同目录并存，落盘名带 -structures 后缀
        {"path": f"{out_dir_rel}/coverage-structures.json",
         "sha256": products["coverage"]["sha256"], "role": "core"},
        # v1.2 adoption：① 正式成档（SPEC §1.1/§1.2）
        {"path": f"{out_dir_rel}/net-registry.json",
         "sha256": products["net_registry"]["sha256"], "role": "core"},
        {"path": f"{out_dir_rel}/net-identity-map.json",
         "sha256": products["net_identity_map"]["sha256"], "role": "core"},
    ]
    env = envelope.build_envelope(
        command="enum", status=status, verdict=verdict,
        inputs=inputs, artifacts=artifacts,
        config_sha256=hashing.sha256_text(hashing.json_dumps(
            {k: v for k, v in vars(config).items() if k.isupper()})),
        spec_refs=["tools/pcbflow/SPEC.md#v1.1-①", "routing-spec-v1.md", "placement-spec-v1.md"],
        metrics={
            "named_nets": len(named_nets),
            "home_assigned": len(net_home),
            "uncovered": len(uncovered),
            "bus_count": len(buses),
            "anchor_count": len(anchors),
            "power_rail_count": len(power_rails),
            "timing_group_count": len(timing_groups),
            "rulings_consumed": [a["id"] for a in amb_resolved],
            "new_findings": [f["id"] for f in findings],
            "authority_status": "draft",
            "registry_nets": reg_stats["named_nets"],
            "registry_snapshot_hash": registry["registry_snapshot_hash"],
            "registry_status_counts": reg_stats["status_counts"],
        },
        diagnostics=(
            [{"id": f["id"], "title": f["title"], "proposal": f["proposal"]}
             for f in findings]
            + [{"id": "structure_authority",
                "title": "structures 草案待用户批准（人工确认点 #1）；批准前为 draft 不进入签核"}]
        ),
        data={"gate": {
            "candidate_full_coverage": not uncovered,
            "explicit_confirmation": "pending_user（人工确认点 #1：structures 草案批准）",
            "diff_resolution": "每个差异带 source/理由/批准人/复审（AMB-1..4 已批；新发现见 findings）",
            "blocking": "structures 草案权威确认待人工 → 阻签核不阻建造（FA3 可按 draft 继续）",
        }},
    )
    products["envelope"] = {"obj": env,
                            "bytes": hashing.canonical_json_bytes(env),
                            "sha256": hashing.sha256_bytes(hashing.canonical_json_bytes(env))}

    lock = toolchain.load_lock()
    t1 = datetime.datetime.now(datetime.timezone.utc)
    manifest = {
        "started_at": t0.isoformat(), "finished_at": t1.isoformat(),
        "elapsed_s": round((t1 - t0).total_seconds(), 3),
        "host": socket.gethostname(), "python_version": sys.version.split()[0],
        "kicad_cli_version": (lock or {}).get("kicad_cli", {}).get("version", "not_probed"),
        "tool_version": config.TOOL_VERSION,
        "input_sha256": input_hashes,
        "config_sha256": env["config_sha256"],
        "spec_sha256": hashing.sha256_file(os.path.join(config.PCBFLOW_ROOT, "SPEC.md")),
        "schema_version": config.SCHEMA_ENVELOPE,
        "out_dir": out_dir_rel,
    }
    products["run_manifest"] = {"obj": manifest,
                                "bytes": hashing.canonical_json_bytes(manifest),
                                "sha256": hashing.sha256_bytes(
                                    hashing.canonical_json_bytes(manifest))}
    return products


def _findings(buses):
    """枚举新发现（spec/网表结构差异；登记不择一 → 待人工）。"""
    findings = []
    storage_buses = [b for b in buses if b["bus_id"] in
                     ("BUS_QSPI", "BUS_SDMMC1", "BUS_SDMMC2")]
    if storage_buses and all("J1" in b["endpoint_refs"] for b in storage_buses):
        n = sum(b["member_count"] for b in storage_buses)
        req = -(-n // 2) * 0.35 + 0.6
        findings.append({
            "id": "STR-1",
            "title": "存储类总线端点=U1↔J1（QSPI/SDMMC 存储在底板），placement §1.3/§3/§5 的"
                     "「QSPI 存储簇/区」在核板上无对应器件",
            "evidence": [f"{b['bus_id']} endpoint_refs={b['endpoint_refs']}"
                         for b in storage_buses],
            "impact": ["placement §3「U1↔QSPI 簇 6 网」走廊对象应为 U1↔J1 存储通道"
                       f"（{n} 网 → 需求宽 {req:.1f}mm）",
                       "分区图 QSPI 区 East 条款待重释（通道预算保留，对象修正）"],
            "proposal": "按网表修正走廊对象为 U1↔J1；placement 条款差异登记 waiver 复审",
            "status": "pending",  # 待人工（阻签核不阻建造）
            "kind": "structure_endpoint_diff",
        })
    order = [b["bus_id"] for b in buses]
    findings.append({
        "id": "STR-2",
        "title": "routing §9 执行顺序未点名 SDMMC1/LTDC（归入「其余」）",
        "evidence": [f"bus_order ranks={order}"],
        "impact": ["① bus_order 需为全部总线定序"],
        "proposal": "SDMMC1/LTDC 按 §2 表行序追加于显式五类之后（派生决定，本草案已采用；"
                    "批准 structures 即连带批准）",
        "status": "derived_pending_structure_approval",
        "kind": "ordering_gap",
    })
    return findings
