"""网络注册表（SPEC §1.1 逐网只读编译视图）+ 身份映射（§1.2）。纯内存、零落盘。

权威顺序（SPEC §1.1，不得反向覆盖）：
  1. constraints.json 拥有规则/参数/enforcement 权威（本模块不产出规则）；
  2. structures.json（批准后）拥有总线/电源树/回流树/组成员/锚件权威 → 本模块
     从 structures 草案编译，registry.structures_ref 绑定其 sha256；
  3. net-registry.json 把上述权威 + 网表/板事实编译成逐网视图；
  4. KiCad net class 仅执行视图（.kicad_pro 逐网指派为空，不作分类事实源）。

身份（§1.2）：net_id 首次分配后不可变（按网名字典序 N0001..N0160）；重命名走
aliases+lineage；禁止用数组位置或 KiCad net code 当稳定 ID。NC 焊盘网显式
excluded_nets 列账（不静默丢弃）。

registry_snapshot_hash = canonical(registry 且本字段=null) 的 sha256
（自哈希约定：字段置 null 后整体参与哈希；验证时将字段置 null 重算比对）。
"""

from __future__ import annotations

import re

from . import compile_cmd, compile_seeds as seeds_mod, config, hashing
from . import profile_loader

PLANNER_CLASS_NOTE = ("pcbagent planner 类为兼容视图（前缀规则）；注册表分类权威="
                      "routing-spec §2 类行 + structures 草案，二者不同层级")

# 电气角色（确定性规则表；rule id 可审计。与 shadow 侧同规则，正式版落库）。
# G0（REPAIR-P4 W-1）：规则数据（角色/原子/规则 id）自 profiles/revc-coreboard/
# profile.json 的 net_registry.role_rules 装载；匹配器（原子解释器）留本模块。
# 原子：net_eq/net_in/net_prefix/net_suffix/net_contains/net_regex/cls_eq/
# cls_prefix；每条规则 any=or 组合（与源码 lambda 谓词逐条等价，等价门=
# net-registry.json 与历史台账 byte-exact 对账）。
_pf = profile_loader.load_profile(config.PCBFLOW_ROOT)
_pf_nr = profile_loader.require(_pf, "net_registry")


def _nr_atom_ok(atom, net_name, cls):
    if "net_eq" in atom:
        return net_name == atom["net_eq"]
    if "net_in" in atom:
        return net_name in atom["net_in"]
    if "net_prefix" in atom:
        return net_name.startswith(tuple(atom["net_prefix"]))
    if "net_suffix" in atom:
        return net_name.endswith(tuple(atom["net_suffix"]))
    if "net_contains" in atom:
        return atom["net_contains"] in net_name
    if "net_regex" in atom:
        return re.match(atom["net_regex"], net_name) is not None
    if "cls_eq" in atom:
        return cls == atom["cls_eq"]
    if "cls_prefix" in atom:
        return cls.startswith(atom["cls_prefix"])
    raise profile_loader.ProfileError(
        "role_rule_atom_unknown:%r" % (sorted(atom),))


def _nr_pred(rule):
    atoms = rule.get("any") or []
    if not atoms:
        raise profile_loader.ProfileError(
            "role_rule_empty_any:%r" % (rule.get("role"),))

    def pred(net_name, cls, _atoms=tuple(atoms)):
        return any(_nr_atom_ok(a, net_name, cls) for a in _atoms)
    return pred


_ROLE_RULES = [(r["role"], _nr_pred(r), r["rule_id"])
               for r in profile_loader.require(_pf_nr, "role_rules")]

_BUS_ROLE_RULES = [(r["role"], _nr_pred(r))
                   for r in profile_loader.require(_pf_nr, "bus_role_rules")]
_BUS_ROLE_FALLBACK = profile_loader.require(_pf_nr, "bus_role_fallback")


def electrical_role_of(net_name, cls):
    for role, pred, rule in _ROLE_RULES:
        if pred(net_name, cls):
            return role, rule
    if cls == "SIG_DEFAULT":
        return "ordinary_control", "rule:sig_default_residual"
    return "ordinary_signal", "rule:default"


def bus_role_of(net_name):
    # G0：声明化装载（profile net_registry.bus_role_rules，顺序=声明序；
    # fallthrough=bus_role_fallback；与源码 if 链逐分支等价）
    for role, pred in _BUS_ROLE_RULES:
        if pred(net_name, None):
            return role
    return _BUS_ROLE_FALLBACK


def parse_allowed_layers(raw):
    """§2 允许层 raw 确定性解析（解析失败返回 layers=null，不猜）。"""
    table = {
        "F/In2/B(批准)": (["F.Cu", "In2.Cu", "B.Cu"], None,
                          "B.Cu 仅经批准短跳（raw 保留）"),
        "F（全程）": (["F.Cu"], "F.Cu", None),
        "F/In2": (["F.Cu", "In2.Cu"], None, None),
        "F 优先/In2": (["F.Cu", "In2.Cu"], "F.Cu", None),
        "F": (["F.Cu"], None, None),
    }
    if raw.startswith("铺铜"):
        return {"layers": ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"],
                "preferred_layer": None, "note": "GND 平面层（铺铜）"}
    if raw in table:
        layers, pref, note = table[raw]
        return {"layers": layers, "preferred_layer": pref, "note": note}
    return {"layers": None, "preferred_layer": None, "note": f"unparsed_raw:{raw}"}


def parse_via_policy(raw):
    if "整对≤1" in raw:
        return {"policy": "pair_le_1", "max_count": None, "raw_note": "整对 ≤1 次换层，成对"}
    if "≤1 次" in raw:
        return {"policy": "pair_le_1", "max_count": 1, "raw_note": None}
    import re as _re
    m = _re.search(r"≤(\d+)", raw)
    if m:
        return {"policy": "max_count", "max_count": int(m.group(1)), "raw_note": None}
    return None


def routing_attrs(cls):
    """§2 行 raw → 线宽/过孔/允许层（「线宽|过孔|允许层|等长组」段式）。"""
    raws = {s["params"]["class"]: s["params"]["raw"]
            for s in seeds_mod.SEEDS if s["domain"] == "NETCLASS"}
    raw = raws.get(cls)
    if raw is None:
        return {"allowed_layers": None, "preferred_layer": None,
                "via_policy": None, "width_mm": None, "note": f"unknown_class_raw:{cls}"}
    seg = [s.strip() for s in raw.split("|")]
    layers = parse_allowed_layers(seg[2] if len(seg) >= 3 else raw)
    m = re.match(r"^([\d.]+)", seg[0])
    return {
        "allowed_layers": layers["layers"],
        "preferred_layer": layers["preferred_layer"],
        "via_policy": parse_via_policy(seg[1] if len(seg) >= 2 else raw),
        "width_mm": float(m.group(1)) if m else None,
        "note": layers["note"],
    }


def _ruling_index():
    idx = {}

    def touch(net, rid):
        idx.setdefault(net, [])
        if rid not in idx[net]:
            idx[net].append(rid)
    for a in seeds_mod.AMBIGUITIES:
        if a["status"] != "resolved":
            continue
        for net in a.get("member_nets") or []:
            touch(net, a["id"])
        if a["id"] == "AMB-1":
            touch("FMC_A12", "AMB-1")
        elif a["id"] == "AMB-3":
            for n in ("USB_DP", "USB_DM", "USB_DP_C", "USB_DM_C"):
                touch(n, "AMB-3")
        elif a["id"] == "AMB-4":
            touch("SD_CD", "AMB-4")
    return idx


def _ruling_lift_set(structures, script_groups):
    """已批裁决 → 争议成员集合（与 shadow 口径一致；confirmed 只来自真实裁决面）。

    组级映射：AMB-1→G_FMC_A、AMB-3→G_USB（枚举组：争议=spec△script）；
    AMB-2→G_LTDC（spec 未枚举：整面按网表修正=structures canonical 成员全体）。
    返回 {net_name: ruling_id}。
    """
    lift = {}
    group_ruling = {}
    for a in seeds_mod.AMBIGUITIES:
        if a["status"] != "resolved":
            continue
        gid = {"AMB-1": "G_FMC_A", "AMB-3": "G_USB", "AMB-2": "G_LTDC"}.get(a["id"])
        if gid:
            group_ruling[gid] = a["id"]
    canon = structures["mapping"]["timing_groups"]
    for g, rid in sorted(group_ruling.items()):
        sg = script_groups.get(g)
        spec = compile_cmd.EXPECTED_SPEC_GROUP_MEMBERS.get(g)
        if sg is None:
            continue
        if spec is None:  # LTDC 型：整面修正 → canonical 成员（板面实际）
            for m in canon[g]["canonical_members"]:
                lift[m] = rid
        else:
            for m in set(spec) ^ set(sg["nets"]):
                lift[m] = rid
    return lift


def _home_of(net, structures):
    """网 → 结构 home（structures 草案 coverage_summary 同口径，独立重导）。"""
    for b in structures["buses"]:
        if net in b["members"]:
            return {"kind": "bus", "ref": b["bus_id"]}
    pt = structures["power_tree"]
    if net in pt["rails"]:
        return {"kind": "power_tree", "ref": net}
    if compile_cmd._match_class(net) == "GND":
        return {"kind": "return_tree", "ref": "GND"}
    for e in structures["loose"]["entries"]:
        if e["net"] == net:
            return {"kind": "loose", "ref": e["kind"]}
    return None


def build(structures, structures_sha256, nets, script_groups=None):
    """structures(内存对象)+structures hash+网表 → (registry, identity_map, stats)。

    nets: compile_cmd.parse_netlist 产物 {net: [{ref,pin},...]}；
    script_groups: length-report.py GROUPS（裁决提升用；缺省仅直接裁决面）。
    """
    all_names = sorted(nets)
    named = [n for n in all_names if not n.startswith("unconnected-")]
    nc = [n for n in all_names if n.startswith("unconnected-")]
    ruled = _ruling_index()
    lift = _ruling_lift_set(structures, script_groups or {}) if script_groups else {}

    # 时序组 relation 成员（structures.mapping.timing_groups=canonical 权威）
    tg = structures["mapping"]["timing_groups"]
    net_id = {n: "N%04d" % (i + 1) for i, n in enumerate(named)}

    relations = {}
    for g in sorted(tg):
        members = sorted(tg[g]["canonical_members"])
        relations["RLG-" + g] = {
            "relation_id": "RLG-" + g, "kind": "length_group",
            "members": [net_id[m] for m in members],
            "reference_net": net_id.get(tg[g]["reference_net"]),
            "tolerance_mm": tg[g]["tolerance_mm"], "source": tg[g]["canonical_basis"],
        }
    usb_scope = next(s for s in seeds_mod.SEEDS if s["id"] == "C-0028")["scope"]
    relations["RDP-USB"] = {
        "relation_id": "RDP-USB", "kind": "differential_pair",
        "segments": {
            "mcu_side": [net_id[x] for x in sorted(usb_scope["pair"])],
            "connector_side": [net_id[x] for x in sorted(usb_scope["pair_connector_side"])],
        },
        "members": sorted(net_id[x] for x in
                          list(usb_scope["pair"]) + list(usb_scope["pair_connector_side"])),
        "source": "C-0028/C-0019(params.segments)+AMB-3 已批(2026-08-29)",
    }
    for b in structures["buses"]:
        if b["symmetry_class"]:
            relations["RSYM-" + b["symmetry_class"]] = {
                "relation_id": "RSYM-" + b["symmetry_class"], "kind": "symmetry_class",
                "members": [net_id[m] for m in sorted(b["members"])],
                "constraint_ref": b["symmetry_constraint"], "source": b["spec_source"],
            }

    net_records = []
    status_counts = {s: 0 for s in ("inferred", "source_declared", "confirmed",
                                    "ambiguous", "unclassified", "waived")}
    for n in named:
        cls = compile_cmd._match_class(n)
        rulings = list(ruled.get(n, []))
        if n in lift and lift[n] not in rulings:
            rulings.append(lift[n])
        if len(_multi_hits(n)) > 1:
            status, rule = "ambiguous", "multi_class_hit;conflict_policy=ambiguous_until_reviewed"
        elif rulings:
            status = "confirmed"
        else:
            # SIG_DEFAULT 兜底行为 spec §2 显式声明（"其余全部"），非推断
            status = "source_declared"
        role, role_rule = electrical_role_of(n, cls)
        attrs = routing_attrs(cls)
        bus_home = _home_of(n, structures)
        lg = next((g for g in sorted(tg)
                   if n in tg[g]["canonical_members"] or n == tg[g]["reference_net"]), None)
        rel_ids = sorted([k for k, v in relations.items() if net_id[n] in v["members"]])
        rec = {
            "net_id": net_id[n],
            "net_name": n,
            "aliases": [],
            "source_net_key": f"revc.netlist#{n}",
            "structure": bus_home,
            "bus_role": bus_role_of(n) if bus_home and bus_home["kind"] == "bus" else None,
            "electrical_role": {"value": role, "inference_rule": role_rule,
                                "status": "inferred"},
            "routing_class": {"value": cls, "status": status,
                              "source_refs": sorted(set(
                                  ["routing-spec §2 类行:" + cls]
                                  + ["ruling:" + r for r in rulings]))},
            "planner_class_view": _planner_view(n),
            "allowed_layers": attrs["allowed_layers"],
            "preferred_layer": attrs["preferred_layer"],
            "via_policy": attrs["via_policy"],
            "width_mm": attrs["width_mm"],
            "length_group": {"value": lg, "status": status if lg else None},
            "relation_ids": rel_ids,
            "endpoints": sorted(f"{nd['ref']}.{nd['pin']}" for nd in nets[n]),
            "classification_status": status,
        }
        net_records.append(rec)
        status_counts[status] += 1

    registry = {
        "schema_version": config.SCHEMA_NET_REGISTRY,
        "project": compile_cmd.PROJECT_ID,
        "registry_snapshot_hash": None,  # 自哈希：canonical(去本字段) 的 sha256
        "policy_version": "1.0",
        "snapshot_revision": 1,  # 首次正式成档（FA3 v1.2 adoption）；追加式递增
        "status": "formal",
        "authority_note": "SPEC §1.1 逐网只读编译视图；权威在 constraints/structures，"
                          "不得反向覆盖；KiCad net class 逐网指派为空（执行视图）",
        "structures_ref": {
            "path": "structures.json", "sha256": structures_sha256,
            "authority": "draft（人工确认点 #1 待批；批准后重绑 approved hash）",
        },
        "classification_policy": {
            "precedence": ["explicit_spec_or_structure_declaration",
                           "schematic_attribute_pin_mux_kicad_net_class",
                           "confirmed_group_or_length_group_declaration",
                           "stable_naming_rule", "inference"],
            "conflict_policy": "ambiguous_until_reviewed",
            "confirmed_basis": "仅已批人工裁决记录（AMB-1..4，2026-08-29）",
            "catch_all_note": "SIG_DEFAULT 兜底=spec §2 显式行（source_declared，非推断）",
        },
        "nets": net_records,
        "relations": relations,
        "excluded_nets": [{"net_name": n, "reason": "unconnected-(...) NC 焊盘网："
                           "无布线实体，显式列账不丢弃（SPEC §1.1 校验门）"} for n in nc],
        "consumer_note": "②③④⑤ 消费须记录 registry_snapshot_hash 与实际消费字段（SPEC §1.2）",
    }
    payload = {k: v for k, v in registry.items()}
    registry["registry_snapshot_hash"] = hashing.sha256_bytes(
        hashing.canonical_json_bytes(payload))

    identity_map = {
        "schema_version": config.SCHEMA_IDENTITY_MAP,
        "project": compile_cmd.PROJECT_ID,
        "policy": "net_id 首次分配后不可变（SPEC §1.2）；重命名经 aliases+lineage 迁移；"
                  "无法证明连续身份时生成新 ID 并记录 lineage；禁用数组位置/KiCad net code",
        "assignments": [{"net_id": net_id[n], "net_name": n, "aliases": [],
                         "lineage": [{"event": "initial_assignment",
                                      "source": "revc.netlist",
                                      "note": "FA3 v1.2 adoption 首次成档（按网名字典序）"}]}
                        for n in named],
        "excluded": [{"net_name": n, "reason": "nc_pad_net"} for n in nc],
    }
    stats = {
        "named_nets": len(named), "nc_pad_nets": len(nc),
        "status_counts": status_counts,
        "relation_count": len(relations),
        "ambiguous_nets": sorted(r["net_name"] for r in net_records
                                 if r["classification_status"] == "ambiguous"),
    }
    return registry, identity_map, stats


def _multi_hits(net_name):
    return [cls for cls, pats in seeds_mod.NETCLASS_PATTERNS
            if any(re.match(p, net_name) for p in pats)]


# pcbagent planner 前缀（兼容视图；来源 tools/pcbagent/pcbagent/config.py，b2 gate.json 同源）
_PLANNER_PREFIX = [
    ("USB_", "USB"), ("ADC_", "ANLG"), ("VREF", "ANLG"), ("VDDA", "ANLG"),
    ("GNDA", "ANLG"), ("HSE_", "ANLG"), ("LSE_", "ANLG"), ("FMC_", "FMC"),
    ("SDMMC2", "SDMMC2"), ("SDMMC1", "SDMMC1"), ("SD_CD", "SDMMC1"),
    ("QSPI", "QSPI"), ("ETH_", "ETH"), ("LTDC", "LTDC"), ("3V3", "PWR"),
    ("5V", "PWR"), ("VBUS", "PWR"), ("VBAT", "PWR"),
]
_PLANNER_DEFAULT = "SIG"


def _planner_view(net_name):
    for pref, key in _PLANNER_PREFIX:
        if net_name.startswith(pref):
            return key
    return _PLANNER_DEFAULT
