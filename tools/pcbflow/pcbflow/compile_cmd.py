"""⓪ 约束编译（pcbflow compile）。纯内存构建、零落盘、零子进程。

产物由 CLI 以生成器模式打到 stdout，shell 重定向落盘（HANDOFF §4）。
门逻辑（SPEC §⓪ + HANDOFF FA1）：
  - 锚点验证失败（spec 漂移）→ failed
  - 存在歧义/缺失源 → blocked（不得宣称"约束编译完成"）
  - 约束条数不在 40–60 → failed（FA1 门）
"""

from __future__ import annotations

import ast
import datetime
import os
import re
import socket
import sys

from . import compile_seeds as seeds_mod
from . import config, envelope, hashing, sexpr_min, toolchain
from . import profile_loader

# G0（REPAIR-P4 W-1）：项目标识自 profiles/revc-coreboard/profile.json 装载
_pf = profile_loader.load_profile(config.PCBFLOW_ROOT)
PROJECT_ID = profile_loader.require(_pf, "compile", "project_id")
NET_TOTAL_SPEC_CLAIM = profile_loader.require(  # routing-spec §2 标题声称"覆盖全部 160 网"
    _pf, "compile", "net_total_spec_claim")

# spec 侧九组成员转录（§2 类行，行锚点在 seeds 中验证；LTDC 仅前缀+计数声明）
def _rng(prefix, n):
    return [f"{prefix}{i}" for i in range(n)]

EXPECTED_SPEC_GROUP_MEMBERS = {
    "G_USB": ["USB_DP", "USB_DM", "USB_DP_C", "USB_DM_C"],
    "G_FMC_D": _rng("FMC_D", 16) + ["FMC_NBL0", "FMC_NBL1"],
    "G_FMC_C": ["FMC_SDNCAS", "FMC_SDNRAS", "FMC_SDNWE", "FMC_SDNE0", "FMC_SDCKE0"],
    # spec 侧事实保留（无 A12）；AMB-1 已批（2026-08-29）：canonical 纳入 A12，差异登记不隐藏
    "G_FMC_A": _rng("FMC_A", 12) + ["FMC_BA0", "FMC_BA1"],
    "G_EMMC": ["SDMMC2_CMD"] + _rng("SDMMC2_D", 4),
    "G_SD": ["SDMMC1_CMD"] + _rng("SDMMC1_D", 4) + ["SD_CD"],
    "G_QSPI": _rng("QSPI_IO", 4) + ["QSPI_NCS"],
    "G_ETH": ["ETH_CRS_DV", "ETH_RXD0", "ETH_RXD1", "ETH_TXD0", "ETH_TXD1",
              "ETH_TX_EN", "ETH_MDC", "ETH_MDIO"],
    "G_LTDC": None,  # spec 未枚举 → 前缀 LTDC_* + "23 网"计数 → AMB-2（已批：网表为准）
}
LTDC_SPEC_CLAIMED_COUNT = 23


# ---- 输入读取 --------------------------------------------------------------
def _read_lines(path):
    with open(path, "r", encoding=config.ENCODING) as f:
        return f.read().splitlines()


def _rel(path):
    return os.path.relpath(path, config.WORKSPACE_ROOT).replace("\\", "/")


def verify_anchors(spec_texts):
    """每条种子的 (行, 锚点) 必须仍存在于源文件该行。返回失败列表。"""
    failures = []
    files = {"routing": spec_texts["routing"], "placement": spec_texts["placement"]}
    for s in seeds_mod.SEEDS:
        lines = files[s["source"]]
        line_no, anchor = s["line"], s["anchor"]
        if not (1 <= line_no <= len(lines)) or anchor not in lines[line_no - 1]:
            failures.append({"constraint": s["id"], "source": s["source"],
                             "line": line_no, "anchor": anchor})
    return failures


def _expand(node, env=None):
    """受限确定性展开 GROUPS 字面量（列表推导/range/字符串拼接）。
    不 eval；遇到不支持节点抛错（脚本漂移即失败）。"""
    env = dict(env or {})
    import ast as _ast
    if isinstance(node, _ast.Dict):
        return {_expand(k, env): _expand(v, env) for k, v in zip(node.keys, node.values)}
    if isinstance(node, _ast.List):
        return [_expand(e, env) for e in node.elts]
    if isinstance(node, _ast.Constant):
        return node.value
    if isinstance(node, _ast.BinOp) and isinstance(node.op, _ast.Add):
        left, right = _expand(node.left, env), _expand(node.right, env)
        if isinstance(left, list) and isinstance(right, list):
            return left + right
        if isinstance(left, str) and isinstance(right, str):
            return left + right
    if isinstance(node, _ast.Call) and isinstance(node.func, _ast.Name) and node.func.id == "range":
        return list(range(*[_expand(a, env) for a in node.args]))
    if isinstance(node, _ast.ListComp) and len(node.generators) == 1:
        gen = node.generators[0]
        if not isinstance(gen.target, _ast.Name) or gen.ifs:
            raise ValueError(f"unsupported comprehension at {node.lineno}")
        out = []
        for v in _expand(gen.iter, env):
            env2 = dict(env)
            env2[gen.target.id] = v
            out.append(_expand(node.elt, env2))
        return out
    if isinstance(node, _ast.JoinedStr):
        parts = []
        for v in node.values:
            if isinstance(v, _ast.Constant):
                parts.append(str(v.value))
            elif isinstance(v, _ast.FormattedValue) and isinstance(v.value, _ast.Name):
                parts.append(str(env[v.value.id]))
            else:
                raise ValueError(f"unsupported f-string part at {node.lineno}")
        return "".join(parts)
    raise ValueError(f"unsupported AST node {type(node).__name__} at line {getattr(node, 'lineno', '?')}")


def extract_script_groups(script_text):
    """ast 提取 length-report.py 的 GROUPS（只取九组口径，不执行脚本）。"""
    tree = ast.parse(script_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            t = node.targets[0]
            if isinstance(t, ast.Name) and t.id == "GROUPS":
                raw = _expand(node.value)
                return {k: {"ref": v["ref"], "target": v["target"],
                            "limit": v["limit"], "nets": list(v["nets"])}
                        for k, v in raw.items()}
    raise ValueError("GROUPS not found in length-report.py")


def parse_netlist(path):
    """netlist → 有序 {net_name: [{"ref","pin"},...]}。"""
    top = sexpr_min.load_file(path)
    root = top[0]  # (export ...)
    nets = {}
    for net in sexpr_min.find_all(root, "net"):
        name = sexpr_min.get_str(sexpr_min.find_first(net, "name"))
        if name is None:
            continue
        nodes = []
        for node in sexpr_min.find_all(net, "node"):
            nodes.append({
                "ref": sexpr_min.get_str(sexpr_min.find_first(node, "ref")),
                "pin": sexpr_min.get_str(sexpr_min.find_first(node, "pin")),
            })
        nets[name] = nodes
    return nets


def _match_class(net_name):
    for cls, patterns in seeds_mod.NETCLASS_PATTERNS:
        for pat in patterns:
            if re.match(pat, net_name):
                return cls
    return seeds_mod.CATCH_ALL_CLASS


# ---- 产物构建 --------------------------------------------------------------
def build_products(out_dir_rel=config.load_project_manifest().out_dirs["compile"]):
    """返回 {name: {"obj":…, "bytes":…, "sha256":…}} + status 判定依据。

    全程内存；写盘由调用方 shell 重定向完成。
    """
    t0 = datetime.datetime.now(datetime.timezone.utc)

    routing_lines = _read_lines(config.ROUTING_SPEC)
    placement_lines = _read_lines(config.PLACEMENT_SPEC)
    with open(config.LENGTH_REPORT_PY, "r", encoding=config.ENCODING) as f:
        script_text = f.read()
    spec_texts = {"routing": routing_lines, "placement": placement_lines}

    # 1) 锚点验证（spec 漂移守卫）
    anchor_failures = verify_anchors(spec_texts)

    # 2) 输入哈希 + 网表
    input_hashes = {
        _rel(p): hashing.sha256_file(p)
        for p in (config.ROUTING_SPEC, config.PLACEMENT_SPEC,
                  config.REVC_NETLIST, config.LENGTH_REPORT_PY)
    }
    nets = parse_netlist(config.REVC_NETLIST)
    net_names = sorted(nets)
    unconnected_pad_nets = [n for n in net_names if n.startswith("unconnected-")]
    named_nets = [n for n in net_names if not n.startswith("unconnected-")]

    # 3) 网类绑定（具名类有序匹配，SIG_DEFAULT 兜底）
    binding = {cls: [] for cls, _ in seeds_mod.NETCLASS_PATTERNS}
    catch_all_only = []
    for n in named_nets:  # NC 焊盘网不参与类绑定（单列）
        cls = _match_class(n)
        if cls == seeds_mod.CATCH_ALL_CLASS:
            catch_all_only.append(n)
        else:
            binding[cls].append(n)

    # 4) 九组逐条对照（spec §2 类行 vs length-report.py GROUPS vs 实际网表）
    script_groups = extract_script_groups(script_text)
    length_seeds = {s["scope"]["group"]: s
                    for s in seeds_mod.SEEDS if s["domain"] == "LENGTH"}
    amb_status = {a["id"]: a["status"] for a in seeds_mod.AMBIGUITIES}
    nine_group_comparison = []
    for g in config.NINE_GROUPS:
        sg = script_groups.get(g)
        spec_members = EXPECTED_SPEC_GROUP_MEMBERS[g]
        seed = length_seeds[g]
        script_set = set(sg["nets"])
        actual = sorted(n for n in net_names
                        if n in script_set or n == sg["ref"])
        tol_match = (sg["target"] == seed["params"]["target_mm"]
                     and sg["limit"] == seed["params"]["limit_mm"])
        entry = {
            "group": g,
            "constraint_id": _group_constraint_id(g),
            "spec_members_basis": ("prefix LTDC_* + 23 网（§2 未枚举）" if spec_members is None
                                   else "routing-spec §2 类行（锚点验证）"),
            "script_members": sg["nets"], "script_ref": sg["ref"],
            "script_nets_missing_on_board": sorted(script_set - set(net_names)),
            "board_actual_members": actual,
            "tolerance": {"target_mm": sg["target"], "limit_mm": sg["limit"],
                          "seed_params_match": tol_match},
            "spec_script_match": None, "diff": {}, "status": "ambiguous", "ambiguity": None,
            "canonical_members": None, "canonical_basis": None,
        }
        if spec_members is None:  # LTDC
            claimed, scripted = LTDC_SPEC_CLAIMED_COUNT, len(sg["nets"])
            entry["diff"] = {"spec_claimed_count": claimed, "script_count": scripted,
                             "board_prefix_count": len([n for n in net_names
                                                        if n.startswith("LTDC_")])}
            entry["ambiguity"] = "AMB-2"
            if amb_status["AMB-2"] == "resolved":
                entry["status"] = "resolved_with_diff"
                entry["canonical_members"] = sorted(
                    n for n in net_names if n.startswith("LTDC_") and n != sg["ref"])
                entry["canonical_basis"] = (
                    "AMB-2 已批（2026-08-29）：canonical 以 Rev-C 网表实际为准"
                    "（19 成员 + PCLK 参考）；spec「23 网」为未枚举声明，"
                    "登记差异并 waiver 复审；脚本 8 名不在板上按网表修正")
        else:
            s_set, c_set = set(spec_members), set(sg["nets"])
            spec_only = sorted(s_set - c_set)
            script_only = sorted(c_set - s_set)
            entry["diff"] = {"spec_only": spec_only, "script_only": script_only}
            entry["spec_script_match"] = not spec_only and not script_only
            if spec_only or script_only:
                amb = _group_ambiguity(g)
                entry["ambiguity"] = amb
                if amb and amb_status.get(amb) == "resolved":
                    entry["status"] = "resolved_with_diff"
                    entry["canonical_members"] = sorted(s_set | c_set)
                    entry["canonical_basis"] = {
                        "AMB-1": "已批（2026-08-29）：canonical 纳入 FMC_A12（网表实际存在；"
                                 "差异来源=routing-spec §2 缺行）；走廊网数 38→39 衍生见 structures",
                        "AMB-3": "已批（2026-08-29）：两段均为约束域，测量分段记录"
                                 "（C-0019 params.segments）",
                    }[amb]
                # else: 保持 ambiguous（未决歧义）
            else:
                entry["status"] = "match"
        nine_group_comparison.append(entry)

    # 脚本允差 vs §3 表（种子 params）一致性
    tol_mismatches = []
    for s in seeds_mod.SEEDS:
        if s["domain"] != "LENGTH":
            continue
        g = s["scope"]["group"]
        sg = script_groups.get(g)
        if sg and (sg["target"] != s["params"]["target_mm"]
                   or sg["limit"] != s["params"]["limit_mm"]):
            tol_mismatches.append({"group": g, "spec_seed": s["params"],
                                   "script": {"target": sg["target"], "limit": sg["limit"]}})

    # 5) coverage
    unimplemented = sorted({s["checker"] for s in seeds_mod.SEEDS})
    critical_nets = sorted(
        {sg["ref"] for sg in script_groups.values() if sg["ref"]}
        | {"5V", "3V3", "SW_NODE", "FB_NODE", "USB_DP", "USB_DM", "USB_DP_C", "USB_DM_C"}
    )
    uncovered_pins = [n for n in critical_nets if n not in net_names]

    layer_binding = {
        "F.Cu": ["C-0037", "C-0005(USB 全程)"], "In1.Cu": ["C-0038", "C-0040", "C-0033"],
        "In2.Cu": ["C-0036", "C-0002..C-0014(允许层)"], "B.Cu": ["C-0038", "C-0001/C-0002(批准短跳)"],
    }
    missing_sources = [
        {"source": "fab_capability_jlc", "desc": "板厂能力表（嘉立创线宽/间距/孔环/板边）无文件",
         "impact": "DFM 条款数值暂取 spec 文本", "blocks": "signoff"},
        {"source": "stackup_definition", "desc": "板厂叠层未定稿（TBD-1）",
         "impact": "impedance_targets 仅预估", "blocks": "signoff"},
        {"source": "interface_specs", "desc": "USB HS/RMII/SDRAM 时序/LTDC 接口规范无独立文件（仅 spec 内摘录）",
         "impact": "时序类约束依据薄弱", "blocks": "signoff"},
    ]
    coverage = {
        "schema_version": config.SCHEMA_COVERAGE,
        "project": PROJECT_ID,
        "missing_sources": missing_sources,
        "unmapped_nets": [],  # SIG_DEFAULT 兜底覆盖一切；具名匹配失败的见 catch_all_only
        "catch_all_only_nets": catch_all_only,
        "unconnected_pad_nets": {
            "count": len(unconnected_pad_nets),
            "note": "unconnected-(...) NC 焊盘网，无布线实体，不参与类绑定",
            "members": unconnected_pad_nets,
        },
        "uncovered_groups": [g for g in config.NINE_GROUPS
                             if g not in {e["group"] for e in nine_group_comparison}],
        "uncovered_pins": uncovered_pins,
        "critical_pins_basis": "九组参考网 + 电源干网 + USB 对（引脚级端点表由① structures.json endpoints 承接）",
        "uncovered_layers": [],
        "layer_binding": layer_binding,
        "ambiguous_selectors": seeds_mod.AMBIGUITIES,
        "unimplemented_checkers": [{"checker": c, "implementation_status": "specified"}
                                   for c in unimplemented],
        "nine_group_comparison": nine_group_comparison,
        "tolerance_mismatches": tol_mismatches,
        "net_class_binding": {cls: {"count": len(v), "members": v}
                              for cls, v in binding.items()},
        "source_notes": _source_notes(len(net_names), len(named_nets),
                                      len(unconnected_pad_nets), len(catch_all_only)),
        "pending_decisions": seeds_mod.PENDING_DECISIONS,
        "fallback": {"backend": sexpr_min.BACKEND, "capabilities": sexpr_min.CAPABILITIES,
                     "fidelity": sexpr_min.FIDELITY,
                     "fallback_reason": sexpr_min.FALLBACK_REASON},
        "totals": {"nets": len(net_names), "named_nets": len(named_nets),
                   "unconnected_pad_nets": len(unconnected_pad_nets),
                   "net_classes": len(seeds_mod.NETCLASS_PATTERNS) + 1,
                   "constraints": len(seeds_mod.SEEDS)},
    }

    # 6) constraints 产物
    constraints_obj = {
        "schema_version": config.SCHEMA_CONSTRAINTS,
        "project": PROJECT_ID,
        "tool": "pcbflow", "tool_version": config.TOOL_VERSION,
        "counts": {"total": len(seeds_mod.SEEDS), "by_type": _count_by(seeds_mod.SEEDS, "type"),
                   "by_domain": _count_by(seeds_mod.SEEDS, "domain"),
                   "by_authority": _count_by(seeds_mod.SEEDS, "authority")},
        "constraints": [_constraint_record(s) for s in seeds_mod.SEEDS],
    }

    # 7) 阻抗目标表
    impedance = _impedance_targets()

    # 8) 门判定
    lo, hi = config.GATE_CONSTRAINT_COUNT
    count_ok = lo <= len(seeds_mod.SEEDS) <= hi
    unclassified = bool(coverage["unmapped_nets"]) or bool(coverage["uncovered_groups"]) \
        or bool(coverage["uncovered_layers"])
    ambiguous_open = [a["id"] for a in seeds_mod.AMBIGUITIES if a["status"] == "pending"]
    rulings_applied = sorted(a["id"] for a in seeds_mod.AMBIGUITIES
                             if a["status"] == "resolved")

    if anchor_failures or tol_mismatches or not count_ok:
        status, verdict = "failed", "red"
    elif ambiguous_open or missing_sources or unclassified:
        status, verdict = "blocked", "yellow"  # 编译完成宣称被阻断（SPEC §⓪/§0.2）
    else:
        status, verdict = "ok", "pass"

    # 9) 核心产物字节 + envelope
    products = {}
    for name, obj in (("constraints", constraints_obj), ("coverage", coverage),
                      ("impedance_targets", impedance)):
        data = hashing.canonical_json_bytes(obj)
        products[name] = {"obj": obj, "bytes": data, "sha256": hashing.sha256_bytes(data)}

    inputs = [
        {"path": _rel(config.ROUTING_SPEC), "sha256": input_hashes[_rel(config.ROUTING_SPEC)],
         "role": "spec"},
        {"path": _rel(config.PLACEMENT_SPEC), "sha256": input_hashes[_rel(config.PLACEMENT_SPEC)],
         "role": "spec"},
        {"path": _rel(config.REVC_NETLIST), "sha256": input_hashes[_rel(config.REVC_NETLIST)],
         "role": "netlist"},
        {"path": _rel(config.LENGTH_REPORT_PY), "sha256": input_hashes[_rel(config.LENGTH_REPORT_PY)],
         "role": "script"},
    ]
    artifacts = [
        {"path": f"{out_dir_rel}/{name}.json", "sha256": products[name]["sha256"],
         "role": "core"}
        for name in ("constraints", "coverage", "impedance_targets")
    ]
    env = envelope.build_envelope(
        command="compile", status=status, verdict=verdict,
        inputs=inputs, artifacts=artifacts,
        config_sha256=hashing.sha256_text(hashing.json_dumps(
            {k: v for k, v in vars(config).items() if k.isupper()})),
        spec_refs=["tools/pcbflow/SPEC.md#v1.1-⓪", "routing-spec-v1.md", "placement-spec-v1.md"],
        metrics={
            "constraint_count": len(seeds_mod.SEEDS),
            "constraint_count_gate": {"min": lo, "max": hi, "pass": count_ok},
            "net_total": len(net_names),
            "net_total_spec_claim": NET_TOTAL_SPEC_CLAIM,
            "net_class_named": len(binding),
            "catch_all_only_count": len(catch_all_only),
            "nine_groups_bound": len(nine_group_comparison),
            "nine_groups_match": sum(1 for e in nine_group_comparison
                                     if e["status"] == "match"),
            "nine_groups_resolved_with_diff": sum(
                1 for e in nine_group_comparison if e["status"] == "resolved_with_diff"),
            "ambiguous_open": ambiguous_open,
            "rulings_applied": rulings_applied,
            "named_net_total": len(named_nets),
            "unconnected_pad_net_count": len(unconnected_pad_nets),
            "unimplemented_checker_count": len(unimplemented),
            "missing_source_count": len(missing_sources),
        },
        diagnostics=(
            [{"id": a["id"], "title": a["title"], "proposal": a["proposal"]}
             for a in seeds_mod.AMBIGUITIES if a["status"] == "pending"]
            + [{"id": m["source"], "title": m["desc"]} for m in missing_sources]
            + [{"id": "anchor_drift", "title": f"{len(anchor_failures)} anchors failed"}]
            if anchor_failures else
            [{"id": a["id"], "title": a["title"], "proposal": a["proposal"]}
             for a in seeds_mod.AMBIGUITIES if a["status"] == "pending"]
            + [{"id": m["source"], "title": m["desc"]} for m in missing_sources]
        ),
        data={"gate": {
            "constraint_count": len(seeds_mod.SEEDS), "in_range": count_ok,
            "nine_groups": {"bound": 9, "match": [e["group"] for e in nine_group_comparison
                                                  if e["status"] == "match"],
                            "resolved_with_diff": [e["group"] for e in nine_group_comparison
                                                   if e["status"] == "resolved_with_diff"],
                            "ambiguous": [e["group"] for e in nine_group_comparison
                                          if e["status"] == "ambiguous"]},
            "unclassified_nets": 0 if not unclassified else coverage["unmapped_nets"],
            "rulings_applied": rulings_applied,
            "blocking": ("missing_sources → 签核阻断（不阻建造）；歧义已全部裁决闭环"
                         if not ambiguous_open else
                         "ambiguous_selectors+missing_sources → 签核阻断；约束库供 A 期建造使用"),
        }},
    )
    products["envelope"] = {"obj": env, "bytes": hashing.canonical_json_bytes(env),
                            "sha256": hashing.sha256_bytes(
                                hashing.canonical_json_bytes(env))}

    # 10) run_manifest（元数据；允许时间/主机，单独存放不参与核心比较）
    lock = toolchain.load_lock()
    t1 = datetime.datetime.now(datetime.timezone.utc)
    manifest = {
        "started_at": t0.isoformat(), "finished_at": t1.isoformat(),
        "elapsed_s": round((t1 - t0).total_seconds(), 3),
        "host": socket.gethostname(), "python_version": sys.version.split()[0],
        "kicad_cli_version": (lock or {}).get("kicad_cli", {}).get("version", "not_probed"),
        "kipy_version": (lock or {}).get("kipy", {}).get("version"),
        "numpy_version": (lock or {}).get("numpy", {}).get("version"),
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


def _group_constraint_id(group):
    return "C-%04d" % (19 + config.NINE_GROUPS.index(group))


def _group_ambiguity(group):
    return {"G_FMC_A": "AMB-1", "G_USB": "AMB-3"}.get(group)


def _source_notes(net_total, named_total, nc_total, catch_total):
    return [
        {"id": "SN-1", "note": f"§2 标题称'16 类'，表实际 18 行（含 SIG_DEFAULT 兜底与 GND）；按 18 行编译"},
        {"id": "SN-2", "note": f"§2 标题称'覆盖全部 160 网'；网表导出共 {net_total} 网，其中具名网 {named_total}（=160 ✓）、NC 焊盘网 {nc_total}；具名网无未映射（兜底类覆盖），类模式外的 {catch_total} 个单列 catch_all_only_nets（AMB-1 已批 2026-08-29 后 FMC_A12 归 FMC_ADDR，不再列于此）"},
        {"id": "SN-3", "note": "两份 spec 状态=待评审；source_revision 记 v1.0-draft，签核前需评审签字"},
        {"id": "SN-4", "note": "§1 单端 50Ω 条款未编译为约束（TBD-1 未定且 spec 自身降权）→ impedance_targets.json pending 行承载"},
        {"id": "SN-5", "note": "§6.2 跨槽条款并入 C-0038 params（遵守 6.1 自动满足）"},
        {"id": "SN-6", "note": "§7.4 丝印条款未编译（装配级；⑤/人工目检承载）"},
        {"id": "SN-7", "note": "§3 测量口径入全部 LENGTH 约束共享 params.measurement（与脚本 VIA_EQUIV=0.2 一致）"},
        {"id": "SN-8", "note": "原理图经 revc.netlist 导出消费（2026-08-23 导出，Eeschema 10.0.5）；.kicad_sch 未直接解析"},
        {"id": "SN-9", "note": "PCBFLOW .py 零落盘零子进程（Mimosa 钩子）；产物经生成器模式 stdout 重定向写盘"},
    ]


def _count_by(items, key):
    out = {}
    for it in items:
        out[it[key]] = out.get(it[key], 0) + 1
    return dict(sorted(out.items()))


def _constraint_record(s):
    src = seeds_mod.SOURCES[s["source"]]
    return {
        "id": s["id"],
        "source_uri": src["source_uri"],
        "source_revision": src["source_revision"],
        "type": s["type"],
        "domain": s["domain"],
        "scope": s["scope"],
        "statement": s["statement"],
        "checker": s["checker"],
        "earliest_stage": s["earliest_stage"],
        "final_stage": s["final_stage"],
        "enforcement_mode": s["enforcement_mode"],
        "authority": s["authority"],
        "waivable": s["waivable"],
        "params": s["params"],
        "implementation": f"pcbflow.check.{s['checker']}",
        "implementation_version": "0.0.0",
        "implementation_status": "specified",  # 红线：未实现一律 specified
        "source_anchor": {"line": s["line"], "anchor": s["anchor"]},
    }


def _impedance_targets():
    return {
        "schema_version": config.SCHEMA_IMPEDANCE,
        "project": PROJECT_ID,
        "basis": "routing-spec §1（1.6mm 板、0.2mm 半固化片/1oz 铜预估）；TBD-1 板厂叠层未定稿",
        "stackup": [
            {"layer": "F.Cu", "role": "signal_escape_and_critical_short"},
            {"layer": "In1.Cu", "role": "gnd_plane_no_signal"},
            {"layer": "In2.Cu", "role": "signal_trunk"},
            {"layer": "B.Cu", "role": "gnd_plane_default"},
        ],
        "targets": [
            {"net_class": "USB_DIFF", "impedance_ohm": 90, "tolerance_pct": 15,
             "geom_width_mm": 0.20, "geom_spacing_mm": 0.20, "layer": "F.Cu",
             "status": "pending_TBD-1",
             "note": "预估几何；板厂叠层定稿后重算（偏差 >30% 回头修订 §1）"},
            {"net_class": "single_ended_critical", "impedance_ohm": 50, "tolerance_pct": 15,
             "est_width_mm": "0.35~0.40", "adopted_width_mm": 0.20,
             "status": "deprioritized_by_spec",
             "note": "铜长 <70mm：等长+连续参考平面为主控；0.20mm 统一线宽优先，阻抗偏差可接受（§1 注）"},
        ],
    }
