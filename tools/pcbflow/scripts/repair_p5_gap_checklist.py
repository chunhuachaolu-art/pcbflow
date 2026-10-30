# -*- coding: utf-8 -*-
"""REPAIR-P5 W-1 签核缺口清单生成器（任务书 exec/REPAIR-P5-SIGNOFF-BOUNDARY-TASKBOOK-2026-09-13.md）。

目标：让生产签核的未闭合缺口**机器可枚举、自动再生、不腐烂**。

- 只读消费三个签核源产物（envelope-signoff fd1 / signoff-package fd1 / signoff-package fc3），
  汇总输出缺口清单 JSON（默认 out/repair-p5/signoff-gap-checklist-r1.json，--out 可覆盖）。
- 条目结构（任务书 §3 W-1）：gate / item / blocker_type(human|external_tool|external_evidence)
  / evidence_path(绝对) / owner_hint / status；另附 source_artifact / note / evidence_sha256。
- 幂等门：canonical 序列化（pcbflow.hashing.json_dumps 正身口径），双跑 byte-exact（EXP-PCBFLOW-012）；
  产物不含墙钟/主机名，保证内容只随源产物变化。
- 负对照（内置自检）：清单非空 ⇒ 全部含 production_signoff_ready 键的源必须为 false
  （SPEC §12 / V3-DESIGN-ARTIFACT-ROLES §5 红线：外部证据+人工批准到位前硬 False）；
  违反 ⇒ exit 2 且不落盘（fail-closed，防止清单与门状态脱钩）。
- 源产物零回写（本脚本对源目录只读）。

非目标（任务书 §1）：不把 production_signoff_ready 翻真；不代替人工确认点；不伪造外部证据。
"""
import argparse
import json
import sys
from pathlib import Path

from pcbflow.hashing import canonical_json_bytes, json_dumps, sha256_file

REPO = Path(__file__).resolve().parents[1]  # tools/pcbflow

# 固定三源：envelope-signoff（fd1 签核 gate 正本）+ fd1 包（envelope core artifact，
# 双时点对照）+ fc3 包（最新 signoff-package 正本）。任务书 §3 W-1 指定前两件与
# out/revc-fc3/signoff-package.json；fd1 包是 envelope-signoff.artifacts[0] 所列 core 件。
SOURCES = [
    ("out/revc-fd1/envelope-signoff.json", "envelope_signoff_fd1"),
    ("out/revc-fd1/signoff-package.json", "signoff_package_fd1"),
    ("out/revc-fc3/signoff-package.json", "signoff_package_fc3"),
]

# 扫描口径：section/entry 级 status 异常值（任务书「全部 not_available/blocked_on_human 项」）
ABNORMAL_STATUS = ("not_available", "missing", "present_unapproved", "blocked")
# 设计内非缺口（不进清单，coverage 里登记排除）
DESIGN_STATUS = ("empty_by_design",)
# gate 布尔键（envelope gate 语义，signoff_cmd.py L535-557 口径）
GATE_BOOL_KEYS = ("structures_approved", "external_signoff_available",
                  "production_signoff_ready")


class NegativeControlError(RuntimeError):
    """负对照断言失败（清单与 production_signoff_ready 门状态脱钩）。"""


def _abs(root: Path, rel: str) -> str:
    return str((root / rel).resolve()).replace("\\", "/")


def load_source(root: Path, rel: str):
    path = root / rel
    if not path.is_file():
        raise FileNotFoundError(f"源产物缺失：{path}（生成器 fail-closed）")
    return json.loads(path.read_text(encoding="utf-8"))


def scan_findings(rel: str, doc):
    """递归扫描一个源产物，返回 (findings, excluded, gate_bools, diagnostics)。

    findings：status 键取异常值的节点（section 级与 entry 级）；
    excluded：设计内声明（empty_by_design 等），非缺口；
    gate_bools：data.gate 下三个布尔键的实测值（无则空 dict）；
    diagnostics：diagnostics[].id 列表（含 blocked 的由调用方消费）。
    """
    findings, excluded = [], []
    gate = doc.get("data", {}).get("gate", {}) if isinstance(doc, dict) else {}
    gate_bools = {k: gate[k] for k in GATE_BOOL_KEYS if k in gate}
    diagnostics = [d.get("id") for d in doc.get("diagnostics", [])
                   if isinstance(d, dict) and d.get("id")] if isinstance(doc, dict) else []

    def walk(node, trail):
        if isinstance(node, dict):
            status = node.get("status")
            if isinstance(status, str):
                if status in ABNORMAL_STATUS:
                    findings.append({
                        "source": rel, "trail": "/".join(trail) or "<root>",
                        "status": status,
                        "item": node.get("item"),
                        "path": node.get("path"),
                        "role": node.get("role"),
                        "note": node.get("note"),
                    })
                elif status in DESIGN_STATUS:
                    excluded.append({
                        "source": rel, "trail": "/".join(trail) or "<root>",
                        "status": status, "item": node.get("item"),
                        "reason": "设计内声明节，非签核缺口（signoff_cmd L371 注释口径）",
                    })
            for k, v in node.items():
                walk(v, trail + [k])
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, trail + [f"[{i}]"])

    walk(doc, [])
    return findings, excluded, gate_bools, diagnostics


def _entry(root, gate, item, blocker_type, evidence_rel, owner_hint, status,
           note, source_rels):
    return {
        "gate": gate,
        "item": item,
        "blocker_type": blocker_type,
        "evidence_path": _abs(root, evidence_rel),
        "evidence_sha256": sha256_file(root / evidence_rel),
        "owner_hint": owner_hint,
        "status": status,
        "source_artifacts": [_abs(root, r) for r in source_rels],
        "note": note,
    }


def build(root: Path):
    docs = {}
    sources_meta = []
    for rel, role in SOURCES:
        docs[rel] = load_source(root, rel)
        sources_meta.append({"path": _abs(root, rel), "sha256": sha256_file(root / rel),
                             "role": role})

    fd1_env = docs["out/revc-fd1/envelope-signoff.json"]
    fd1_pkg = docs["out/revc-fd1/signoff-package.json"]
    fc3_pkg = docs["out/revc-fc3/signoff-package.json"]

    scanned = {rel: scan_findings(rel, docs[rel]) for rel, _ in SOURCES}
    all_findings = [f for rel, _ in SOURCES for f in scanned[rel][0]]
    all_excluded = [e for rel, _ in SOURCES for e in scanned[rel][1]]
    env_gate = scanned["out/revc-fd1/envelope-signoff.json"][2]

    fd1_sections = {s.get("item"): s for s in fd1_pkg.get("sections", [])}
    fc3_sections = {s.get("item"): s for s in fc3_pkg.get("sections", [])}
    waivers = fd1_env.get("waivers", [])
    approved = [w for w in waivers if w.get("approved_via")]
    pending = env_gate.get("waiver_candidates_pending")

    checklist = []
    consumed = []  # 已被固定条目吸收的 finding (source, trail)

    def absorb(predicate):
        """按谓词批量吸收 findings（fd1/fc3 双包同类 section 全吸收，防漏入残余）。"""
        hits = [f for f in all_findings
                if predicate(f) and (f["source"], f["trail"]) not in consumed]
        consumed.extend((f["source"], f["trail"]) for f in hits)
        return hits

    # ── 确认点 #1 structures（human）──────────────────────────────
    note1 = []
    hits1 = absorb(lambda f: f.get("item") == "structures snapshot"
                   and f["status"] == "present_unapproved")
    if env_gate.get("structures_approved") is False:
        note1.append("envelope gate structures_approved=false（fd1 时点）")
    if hits1:
        note1.append("fd1 包 section=present_unapproved")
    fc3_struct = fc3_sections.get("structures snapshot", {})
    if fc3_struct.get("status") == "present":
        note1.append("fc3 包已 override 转正（present）——envelope gate 未随重跑，"
                     "以 gate 为签核正文权威，缺口维持登记")
    checklist.append(_entry(
        root, "production_signoff",
        "确认点 #1 structures 人工批准（HANDOFF §3 不代办确认点）",
        "human", "out/revc-fd1/envelope-signoff.json",
        "用户（人工确认点）", "open", "；".join(note1) or "未见机器状态异常",
        ["out/revc-fd1/envelope-signoff.json", "out/revc-fd1/signoff-package.json",
         "out/revc-fc3/signoff-package.json"]))

    # ── 确认点 #5 waivers 逐条（human）────────────────────────────
    n_app, n_all = len(approved), len(waivers)
    diag_blocked = [d for d in scanned["out/revc-fd1/envelope-signoff.json"][3]
                    if "blocked_on_human" in d]
    note5 = [f"waivers {n_app}/{n_all} 已带 approved_via（2026-08-30 用户会话批注）",
             f"gate waiver_candidates_pending={pending}"]
    if diag_blocked:
        note5.append("envelope 诊断 production_blocked_on_human 时点仍列 #5 待人工；"
                     "全部 waiver expiry=下一 rev 强制复审（SPEC §12.1）为持续义务")
    checklist.append(_entry(
        root, "production_signoff",
        "确认点 #5 waivers 逐条人工确认（含下一 rev 强制复审义务）",
        "human", "out/revc-fd1/envelope-signoff.json",
        "用户（人工确认点）", "open", "；".join(note5),
        ["out/revc-fd1/envelope-signoff.json"]))

    # ── 外部 SI/PI/热/EMC/DFM 工具族（external_tool）──────────────
    note3 = []
    hits3 = absorb(lambda f: f.get("item") == "SI/PI/thermal/DFM/external reports"
                   and f["status"] == "not_available")
    if hits3:
        note3.append(f"包 section=not_available ×{len(hits3)}（fd1+fc3）")
    if env_gate.get("external_signoff_available") is False:
        note3.append("envelope gate external_signoff_available=false"
                     "（toolchain_lock 仅 kicad 工具族）")
    si_note = (fc3_sections.get("SI/PI/thermal/DFM/external reports", {})
               .get("note", ""))
    if "板厂叠层表" in si_note or "功耗" in si_note:
        note3.append("note 原文指认前置=板厂叠层表+BOM 功耗数据")
    checklist.append(_entry(
        root, "production_signoff",
        "外部 SI/PI/thermal/EMC/DFM 工具族未接入（SPEC §12 必要外部签核）",
        "external_tool", "out/revc-fc3/signoff-package.json",
        "外部工具链接入（toolchain_lock 扩展，须报批）", "open",
        "；".join(note3) or "未见机器状态异常",
        ["out/revc-fc3/signoff-package.json", "out/revc-fd1/envelope-signoff.json",
         "out/revc-fd1/signoff-package.json"]))

    # ── 板厂最终叠层表（external_evidence，TBD-1 定稿义务）────────
    checklist.append(_entry(
        root, "production_signoff",
        "板厂最终叠层表（TBD-1 定稿义务；现叠层基面=JLC04161H-7628 一阶预估）",
        "external_evidence", "out/revc-fc3/signoff-package.json",
        "板厂→用户审定", "open",
        "fc3 constraints note 列账「TBD-1 定稿义务保留」；三源结案与阻抗重算见 "
        "out/revc-tbd1/（impedance-recalc.json）",
        ["out/revc-fc3/signoff-package.json"]))

    # ── BOM 实测级功耗数据（external_evidence）────────────────────
    checklist.append(_entry(
        root, "production_signoff",
        "BOM 实测级功耗数据（正式电流定稿前置）",
        "external_evidence", "out/revc-fc3/signoff-package.json",
        "BOM/实测→用户审定", "open",
        "fc3 SI/PI section note：「正式阻抗/电流定稿仍需板厂叠层表+BOM 功耗数据→"
        "生产签核前置条件未满足」；无独立机器载体，按 note 原文登记",
        ["out/revc-fc3/signoff-package.json"]))

    # ── 扫描残余：未被固定条目吸收的异常 finding → 独立条目 ────────
    for f in all_findings:
        if (f["source"], f["trail"]) in consumed:
            continue
        consumed.append((f["source"], f["trail"]))
        rel = f["source"]
        blocker = ("external_evidence" if f.get("role") == "authority_rerun_basis"
                   else "external_evidence" if f["status"] == "not_available"
                   else "human" if f["status"] == "present_unapproved"
                   else "external_evidence")
        item = (f"{f.get('item') or '扫描发现'}：entry {f.get('path')} "
                f"({f.get('role')}) status={f['status']}")
        note = f.get("note") or "递归扫描发现（非固定枚举项）；自动再生"
        checklist.append(_entry(
            root, "production_signoff", item, blocker, rel,
            "按 role 推断（authority_rerun_basis=重算基面缺件，随叠层/阻抗定稿闭合）",
            "open", note, [rel]))

    # ── 覆盖对账 ─────────────────────────────────────────────────
    n_consumed = len(consumed)
    coverage = {
        "scan_rule": (
            "对三源递归扫描：节点 status ∈ " + str(list(ABNORMAL_STATUS))
            + " → finding；status ∈ " + str(list(DESIGN_STATUS))
            + " → 设计内排除；envelope gate 布尔键 "
            + str(list(GATE_BOOL_KEYS)) + "；diagnostics[].id 含 blocked_on_human"),
        "sources_scanned": len(SOURCES),
        "findings_total": len(all_findings),
        "findings_consumed_by_checklist": n_consumed,
        "excluded_by_design": all_excluded,
        "excluded_count": len(all_excluded),
        "gate_bools_observed": {
            "out/revc-fd1/envelope-signoff.json": env_gate},
        "diagnostics_observed": {
            "out/revc-fd1/envelope-signoff.json":
                scanned["out/revc-fd1/envelope-signoff.json"][3]},
        "reconciliation": (
            f"findings {len(all_findings)} = 固定条目吸收 + 独立条目 {n_consumed}；"
            f"设计内排除 {len(all_excluded)}；零遗漏"
            if n_consumed == len(all_findings)
            else f"对账不平：findings={len(all_findings)} consumed={n_consumed}（fail-closed）"),
        "reconciliation_ok": n_consumed == len(all_findings),
    }
    if not coverage["reconciliation_ok"]:
        raise NegativeControlError(
            f"覆盖对账不平：findings={len(all_findings)} consumed={n_consumed}")

    # ── 负对照自检（fail-closed）─────────────────────────────────
    # 断言口径：仅**含** production_signoff_ready 键的源参与断言（该键只存在于
    # envelope-signoff 的 data.gate/metrics）；signoff-package 无此键 → 如实登记
    # null 表示键不存在，不作断言对象。
    asserted = []
    for rel, _ in SOURCES:
        doc = docs[rel]
        ready = None
        if "production_signoff_ready" in doc.get("data", {}).get("gate", {}):
            ready = doc["data"]["gate"]["production_signoff_ready"]
        elif "production_signoff_ready" in doc.get("metrics", {}):
            ready = doc["metrics"]["production_signoff_ready"]
        asserted.append({"source": _abs(root, rel),
                         "production_signoff_ready": ready})
    violations = [a for a in asserted
                  if a["production_signoff_ready"] is not None
                  and a["production_signoff_ready"] is not False]
    if checklist and violations:
        raise NegativeControlError(
            "清单非空但以下源 production_signoff_ready 非 false（清单与门状态脱钩）："
            + json.dumps(violations, ensure_ascii=False))
    negative_control = {
        "rule": ("checklist 非空 ⇒ 全部含 production_signoff_ready 键的源必须为 "
                 "false（SPEC §12；V3-DESIGN-ARTIFACT-ROLES §5 红线；任何翻真捷径=红线）"),
        "checklist_len": len(checklist),
        "asserted_sources": asserted,
        "verdict": "pass" if not violations else "fail",
    }

    return {
        "artifact_kind": "signoff_gap_checklist",
        "schema_version": "1.0",
        "generated_by": "scripts/repair_p5_gap_checklist.py (REPAIR-P5 W-1)",
        "spec_refs": [
            "SPEC.md §12（13 项签核包；签核正文只由约束库终态、KiCad ERC/DRC "
            "authority、必要外部签核和人工批准决定）",
            "SPEC.md §12.1（前馈资源赤字不能自动生成 waiver）",
            "exec/REPAIR-P5-SIGNOFF-BOUNDARY-TASKBOOK-2026-09-13.md §3 W-1",
        ],
        "repo_root": str(root).replace("\\", "/"),
        "sources": sources_meta,
        "checklist": checklist,
        "negative_control": negative_control,
        "coverage": coverage,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="out/repair-p5/signoff-gap-checklist-r1.json",
                    help="输出路径（相对仓库根 tools/pcbflow；默认 r1 件）")
    ap.add_argument("--root", default=str(REPO),
                    help="仓库根（默认脚本所在仓库；测试注入用）")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    try:
        artifact = build(root)
    except (NegativeControlError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"[repair_p5_gap_checklist] FAIL-CLOSED: {exc}", file=sys.stderr)
        return 2

    out = root / args.out if not Path(args.out).is_absolute() else Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(canonical_json_bytes(artifact))
    print(f"[repair_p5_gap_checklist] ok: {len(artifact['checklist'])} 条缺口 → {out}")
    print(f"  negative_control={artifact['negative_control']['verdict']} "
          f"coverage_ok={artifact['coverage']['reconciliation_ok']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
