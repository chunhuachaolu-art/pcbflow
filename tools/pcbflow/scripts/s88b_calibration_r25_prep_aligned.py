#!/usr/bin/env python
"""S88B_CALIBRATION_R25_PREP_ALIGNED：s88 的 D4 对齐变体（v2 口径生成
路径）。

授权：out/v3-rereg-proposal/RE-REGISTRATION-ADJUDICATION-2026-09-13.md
D4（用户原文「保存现有的前提下对齐做对比」：r1 历史件与生成器原样保
留，另做 v2 对齐路径并产出 r1/v2 两路对比记录——对齐不替换、对比不
覆盖）+ RE-REGISTRATION-PROPOSAL-R1.md §4.5 forward 规则。

基座=scripts/s88_calibration_r25_prep.py（留旧历史生成器，本批零改动）；
本变体经 importlib 装载 s88、复用其全部 probe/build/derive 纯函数与
fail-closed 锚校验，编排层恰三处参数化（本变体全部差异所在）：
  (1) cli.py 保护锚期望=盘上现值 0a738047…（s88 原常量=6ed4f3fd 历史
      锚=留旧生成时点事实，保持不动）；
  (2) observation-guidance-r25.md=只读核验（冻结域零写入：冻结件在盘
      且与内存重派生字节逐字一致方可继续；缺失/不一致→FAIL，不代写）；
  (3) REL_OUT 对齐 v2 口径：输出写新目录 out/v3-rereg-exec-r1/aligned/
      （r1 路径与既有 canonical v2 件零触碰）；记录构建后叠加 v2 三要素
      （逐字取自在案 canonical v2 件 r25-prep-record-v2.json，取用前
      fail-closed 校验其 supersedes 链指向 r1 冻结件实测 sha256）。

防覆写护栏语义保持：输出已存在且重建字节不同→FAIL；相同→幂等零覆
写。对齐自证：叠加后 canonical 字节==在案 canonical v2 件字节
（fail-closed）。产出 2/2：r1 路径 vs v2 对齐路径机器对比记录
（canonical JSON，逐字段差异+差异归因分类；unclassified 差异如实登记、
不硬凑相等）。

纪律：日期=声明常量 2026-09-13（零 wall-clock）；零网络/零 git 写操作；
pcbflow/ 与 datasets/ 零写入、profiles/ 只读；s85/s88 本体与 r1 件/既有
v2 件/holdout 域全部零回写；本脚本唯一写入面=新目录两件。

用法：python scripts/s88b_calibration_r25_prep_aligned.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import hashing  # noqa: E402

DECLARED_DATE = "2026-09-13"
R1_REL = "out/v3-tl2/calibration/r25-prep-record.json"
R1_SHA = ("0943a8ec518473d4956e805eaac420c9f9583e7efdef7343325638674"
          "521c284")
V2_REL = "out/v3-tl2/calibration/r25-prep-record-v2.json"
V2_SHA = ("5951a6efec1f26c52cd043bc04ea46f080e40abffa2c5d4afedec975e"
          "e6c2372")
V2_KIND = "tl2_calibration_r25_prep_record_v2"
CLI_SHA_CURRENT = ("0a7380476f86ea3aa72de1982aa9d39e1414b458428d127a"
                   "43a62d8c775da32e")
CLI_SHA_HISTORICAL = ("6ed4f3fd7c87947562acffb90c8563dfae0d05ad82c395"
                      "a45d0aad226c206e17")
OUT_REL = "out/v3-rereg-exec-r1/aligned/r25-prep-record-v2-aligned.json"
COMP_REL = "out/v3-rereg-exec-r1/d4-comparison-r25-prep.json"


def _load_s88():
    path = REPO / "scripts" / "s88_calibration_r25_prep.py"
    spec = importlib.util.spec_from_file_location(
        "s88_calibration_r25_prep_base", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


S88 = _load_s88()


def _fail(msg: str) -> None:
    print(f"[r25-prep-aligned] FAIL: {msg}")
    sys.exit(1)


def _sha(path) -> str:
    return hashing.sha256_file(str(path))


def _classify(d: dict) -> tuple:
    p = d["field_path"]
    if p == ["kind"]:
        return ("v2_gauge_provenance_element",
                "kind 显式后缀（§4.5 要素 1）：tl2_calibration_r25_prep_"
                "record → tl2_calibration_r25_prep_record_v2")
    if p == ["protected_files_verification", "hashes", "pcbflow/cli.py"]:
        return ("anchor_byte",
                "cli.py 保护锚世代更替 6ed4f3fd→0a738047（铜环案接纳；"
                "历史值保留于 r1 冻结件与本记录 anchor_amendment.old_"
                "value）")
    if p == ["supersedes"]:
        return ("v2_gauge_provenance_element",
                "supersedes 哈希链（§4.5 要素 2）：path_rel+全文 sha256 "
                "指向 r1 冻结件")
    if p == ["anchor_amendment"]:
        return ("v2_gauge_provenance_element",
                "双值披露（§4.5 要素 3）：old 保留+note、new 进期望字段")
    return ("unclassified", "未归因差异（如实登记，不硬凑相等）")


def _leaf_diff(a, b, path: list) -> list:
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a:
                out.append({"field_path": path + [k],
                            "type": "added_in_aligned"})
            elif k not in b:
                out.append({"field_path": path + [k],
                            "type": "removed_from_aligned"})
            else:
                out += _leaf_diff(a[k], b[k], path + [k])
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            out += _leaf_diff(x, y, path + [i])
    elif a != b:
        out.append({"field_path": path, "type": "changed",
                    "r1_value": a, "aligned_value": b})
    return out


def build_aligned() -> tuple:
    base = S88
    # ---- 开工保护三文件（cli 期望=现值）----
    protected_hashes = {
        "pcbflow/cli.py": base._require_full_sha(
            base.CLI_PY, CLI_SHA_CURRENT, "pcbflow/cli.py"),
        "pcbflow/config.py": base._require_full_sha(
            base.CONFIG_PY, base.CONFIG_PY_SHA, "pcbflow/config.py"),
        "toolchain_lock.json": base._require_full_sha(
            base.TOOLCHAIN_LOCK, base.TOOLCHAIN_LOCK_SHA,
            "toolchain_lock.json"),
    }
    # ---- r1 冻结件与 canonical v2 件身份钉死 ----
    if _sha(REPO / R1_REL) != R1_SHA:
        _fail("r1 冻结件 r25-prep-record.json sha256 与在案值不符（疑被回写）")
    if _sha(REPO / V2_REL) != V2_SHA:
        _fail("canonical v2 件 r25-prep-record-v2.json sha256 与在案值不符"
              "（疑被回写）")
    # ---- 前置存在性（与 s88.main 同集；guidance-r25 冻结件必须在盘）----
    for path in (base.GUIDANCE_R23, base.GUIDANCE_R25, base.DEV_RECORD_R22,
                 base.DEV_RECORD_R23, base.DEV_RECORD_R24, base.AXIS_PLAN,
                 base.TYPOLOGY, base.R23_PREP_RECORD, base.R24_PREP_RECORD,
                 base.RUN_R22, base.RUN_R23, base.RUN_R24, base.WITNESS_R14B,
                 base.EVAL_PROTOCOL_V1, base.EVAL_PROTOCOL_V2):
        if not path.exists():
            _fail(f"缺失：{path}（guidance-r25=冻结域件，本变体不代写）")
    if not base.RENDR14B_DIR.is_dir():
        _fail(f"缺失渲染目录：{base.RENDR14B_DIR}")
    # ---- 全 64 位锚 ----
    guidance_sha = base._require_full_sha(
        base.GUIDANCE_R23, base.GUIDANCE_R23_SHA,
        "observation-guidance-r23.md")
    dev24_sha = base._require_full_sha(
        base.DEV_RECORD_R24, base.DEV_RECORD_R24_SHA,
        "round24-dev-record.json")
    axis_sha = base._require_full_sha(
        base.AXIS_PLAN, base.AXIS_PLAN_SHA,
        "axis-experiment-plan-r17-r20.json")
    typology_sha = base._require_full_sha(
        base.TYPOLOGY, base.TYPOLOGY_SHA, "abstain-typology-r13-r16.json")
    run24_sha = base._require_full_sha(
        base.RUN_R24, base.RUN_R24_SHA, "calibration-run-r24.json")
    # ---- 前缀锚 ----
    dev22_sha = base._require_prefix_sha(
        base.DEV_RECORD_R22, base.DEV_RECORD_R22_SHA_PREFIX,
        "round22-dev-record.json")
    dev23_sha = base._require_prefix_sha(
        base.DEV_RECORD_R23, base.DEV_RECORD_R23_SHA_PREFIX,
        "round23-dev-record.json")
    r23_record_sha = base._require_prefix_sha(
        base.R23_PREP_RECORD, base.R23_PREP_RECORD_SHA_PREFIX,
        "r23-prep-record")
    r24_record_sha = base._require_prefix_sha(
        base.R24_PREP_RECORD, base.R24_PREP_RECORD_SHA_PREFIX,
        "r24-prep-record")
    run22_sha = base._require_prefix_sha(
        base.RUN_R22, base.RUN_R22_SHA_PREFIX, "calibration-run-r22")
    run23_sha = base._require_prefix_sha(
        base.RUN_R23, base.RUN_R23_SHA_PREFIX, "calibration-run-r23")
    witness_sha = base._require_prefix_sha(
        base.WITNESS_R14B, base.WITNESS_R14B_SHA_PREFIX,
        "render-witness-r14b")
    protocol_v1_sha = base._require_prefix_sha(
        base.EVAL_PROTOCOL_V1, base.EVAL_PROTOCOL_V1_SHA_PREFIX,
        "evaluation-protocol-v1")
    protocol_v2_sha = base._require_prefix_sha(
        base.EVAL_PROTOCOL_V2, base.EVAL_PROTOCOL_V2_SHA_PREFIX,
        "evaluation-protocol-v2")
    # ---- 基座只读装载 + 结构探测（与 s88.main 同序）----
    guidance_text = base.GUIDANCE_R23.read_text(encoding="utf-8")
    dev22_text = base.DEV_RECORD_R22.read_text(encoding="utf-8")
    dev23_text = base.DEV_RECORD_R23.read_text(encoding="utf-8")
    dev24_text = base.DEV_RECORD_R24.read_text(encoding="utf-8")
    witness = json.loads(base.WITNESS_R14B.read_text(encoding="utf-8"))
    run24 = json.loads(base.RUN_R24.read_text(encoding="utf-8"))
    run23 = json.loads(base.RUN_R23.read_text(encoding="utf-8"))
    run22 = json.loads(base.RUN_R22.read_text(encoding="utf-8"))
    dev24 = json.loads(dev24_text)
    axis_plan = json.loads(base.AXIS_PLAN.read_text(encoding="utf-8"))
    typology = json.loads(base.TYPOLOGY.read_text(encoding="utf-8"))
    r23_record = json.loads(
        base.R23_PREP_RECORD.read_text(encoding="utf-8"))
    r24_record = json.loads(
        base.R24_PREP_RECORD.read_text(encoding="utf-8"))
    if r23_record.get("kind") != "tl2_calibration_r23_prep_record" or \
            r23_record.get("round_label") != "r23":
        _fail("r23-prep-record 机械变换先例件结构漂移")
    if r24_record.get("kind") != "tl2_calibration_r24_prep_record" or \
            r24_record.get("round_label") != "r24":
        _fail("r24-prep-record 结构血统件结构漂移")
    base.probe_witness(witness)
    png_checks = base.check_renders_byte_freeze(witness)
    guidance_ref = base.probe_guidance_r23(guidance_text, guidance_sha)
    axis_ref = base.probe_axis_plan(axis_plan, axis_sha)
    typology_ref = base.probe_typology(typology, typology_sha)
    run24_ref = base.probe_run_r24(run24, run24_sha)
    run23_ref = base.probe_run_r23(run23, run23_sha)
    run22_ref = base.probe_run_r22(run22, run22_sha)
    dev24_ref = base.probe_dev_record_r24(dev24, dev24_sha, dev24_text,
                                          run24_ref["m_tuple_r24_live"])
    drift_counts = base.probe_drift_anchor(dev22_text, dev23_text)
    lineage_note = (r24_record.get("hypothesis_test", {})
                    .get("adjudication", {})
                    .get("descriptive_boundary_note", ""))
    if base.DESCRIPTIVE_BOUNDARY_NOTE != lineage_note:
        _fail("descriptive_boundary_note 未照抄 r24-prep-record 血统原文")
    ht_text = json.loads(base.HYPOTHESIS_TEST_TEXT)
    if base.HYPOTHESIS_TEST != ht_text:
        _fail("hypothesis_test 常量与预注册判据原文不一致")
    if 928571 - 666667 != base.M4_ANCHOR_6DP or \
            862069 - 771429 != base.DRIFT_6DP:
        _fail("定点整数自证失败")
    if base.G2_R24 != 0 or base.G2_R23 != 1 or base.G2_R22 != 2:
        _fail("G2 对照链常量不符")
    # ---- 指引机械变换（内存重派生；冻结域零写入——只核验在盘件）----
    derived_text = base.derive_guidance_r25(guidance_text)
    seg_bytes = base.assert_guidance_r25(derived_text, guidance_text)
    derived_sha = hashing.sha256_text(derived_text)
    derived_bytes = len(derived_text.encode("utf-8"))
    if base.GUIDANCE_R25.read_bytes() != derived_text.encode("utf-8"):
        _fail("observation-guidance-r25.md 在盘字节与内存重派生不一致"
              "（冻结件疑被改动）")
    if _sha(base.GUIDANCE_R25) != derived_sha:
        _fail("observation-guidance-r25.md sha256 与重派生口径不一致")
    # ---- 记录构建（纯函数）+ 结构镜像 + 确定性自证 ----
    kwargs = dict(
        guidance_ref=guidance_ref, dev24_ref=dev24_ref, axis_ref=axis_ref,
        typology_ref=typology_ref, run24_ref=run24_ref, run23_ref=run23_ref,
        run22_ref=run22_ref, r23_record_sha=r23_record_sha,
        r24_record_sha=r24_record_sha, witness_sha=witness_sha,
        protocol_v1_sha=protocol_v1_sha, protocol_v2_sha=protocol_v2_sha,
        png_checks=png_checks, drift_counts=drift_counts,
        derived_sha=derived_sha, derived_bytes=derived_bytes,
        seg_bytes=seg_bytes, m_tuple_r24_live=run24_ref["m_tuple_r24_live"],
        protected_hashes=protected_hashes)
    record = base.build_record(**kwargs)
    missing = sorted(set(r24_record.keys()) - set(record.keys()))
    extra = sorted(set(record.keys()) - set(r24_record.keys()))
    if missing or extra:
        _fail(f"顶层键集合与 r24-prep-record 镜像不符：少={missing}，"
              f"多={extra}")
    if len(record) != 25:
        _fail(f"顶层键数须恰 25：{len(record)}")
    if record["round_id_constant"] != base.ROUND_ID or \
            record["declared_date"] != base.DATE_CONSTANT:
        _fail("轮次标识不符（2026-09-10-r25 / 2026-09-10）")
    pre_bytes = hashing.canonical_json_bytes(record)
    rebuild = base.build_record(**kwargs)
    if hashing.canonical_json_bytes(rebuild) != pre_bytes:
        _fail("同参重建不一致（byte-exact 破坏）")
    # ---- v2 三要素叠加（逐字取自在案 canonical v2 件；链校验）----
    v2doc = json.loads((REPO / V2_REL).read_text(encoding="utf-8"))
    if v2doc.get("kind") != V2_KIND:
        _fail(f"canonical v2 件 kind 不符：{v2doc.get('kind')!r}")
    sup = v2doc.get("supersedes", {})
    if sup.get("path_rel") != R1_REL or sup.get("sha256") != R1_SHA:
        _fail("v2 件 supersedes 链与 r1 冻结件不符（对齐来源失信）")
    if v2doc.get("anchor_amendment", {}).get("old_value") != \
            CLI_SHA_HISTORICAL:
        _fail("v2 件 anchor_amendment.old_value 与 r1 历史锚不符")
    record["kind"] = v2doc["kind"]
    record["supersedes"] = sup
    record["anchor_amendment"] = v2doc["anchor_amendment"]
    record_bytes = hashing.canonical_json_bytes(record)
    if record_bytes != (REPO / V2_REL).read_bytes():
        _fail("叠加后字节与在案 canonical v2 件不一致（对齐失败）")
    return record, record_bytes, protected_hashes


def build_comparison(r1_raw: bytes, aligned_bytes: bytes) -> dict:
    r1_doc = json.loads(r1_raw)
    aligned_doc = json.loads(aligned_bytes)
    diffs = _leaf_diff(r1_doc, aligned_doc, [])
    classes = {}
    for d in diffs:
        cls, note = _classify(d)
        d["attribution_class"] = cls
        d["attribution_note"] = note
        classes[cls] = classes.get(cls, 0) + 1
    unclassified = classes.get("unclassified", 0)
    comp = {
        "kind": "rereg_exec_r1_d4_comparison_r25_prep",
        "declared_date": DECLARED_DATE,
        "authority": [
            "out/v3-rereg-proposal/RE-REGISTRATION-ADJUDICATION-2026-09-13.md"
            " D4（保存现有的前提下对齐做对比）",
            "out/v3-rereg-proposal/RE-REGISTRATION-PROPOSAL-R1.md §4.5 "
            "forward 规则",
        ],
        "comparison_scope": (
            "r1 历史路径（out/v3-tl2/calibration/r25-prep-record.json，"
            "生成器=s88 留旧、cli 锚=6ed4f3fd 生成时点历史值）vs v2 对齐"
            "路径（本变体 s88b：cli 锚期望=0a738047 现值+输出对齐 v2 口径）"),
        "path_r1": {
            "path_rel": R1_REL, "sha256": R1_SHA, "byte_size": len(r1_raw),
            "generator": "scripts/s88_calibration_r25_prep.py（留旧，本批"
                         "零改动）",
        },
        "path_v2_aligned": {
            "path_rel": OUT_REL,
            "sha256": hashing.sha256_text(aligned_bytes.decode("utf-8")),
            "byte_size": len(aligned_bytes),
            "generator": "scripts/s88b_calibration_r25_prep_aligned.py"
                         "（本批新增；基座=s88 复用，编排层三处参数化）",
        },
        "leaf_diffs": diffs,
        "attribution_summary": {
            "anchor_byte": classes.get("anchor_byte", 0),
            "v2_gauge_provenance_element": classes.get(
                "v2_gauge_provenance_element", 0),
            "unclassified": unclassified,
        },
        "conclusion": (
            "差异恰=锚字节+三要素：protected_files_verification.hashes"
            "['pcbflow/cli.py'] 1 处 6ed4f3fd→0a738047（anchor_byte）+"
            "kind 后缀/supersedes/anchor_amendment 三项 v2 口径新增字段"
            "（v2_gauge_provenance_element）；其余字段逐字节同源。对齐输"
            "出与在案 canonical v2 件 r25-prep-record-v2.json 逐字节相等"
            "（独立生成路径再证；R25 批先例复核）。对齐不替换：r1 件与"
            "s88 生成器原样保留、本记录不覆盖任何既有产物。"
            if unclassified == 0 else
            "存在未归因差异（unclassified>0）——逐条见 leaf_diffs，如实"
            "登记、不硬凑相等。"),
        "cross_check_vs_canonical_v2": {
            "path_rel": V2_REL, "sha256": V2_SHA,
            "byte_equal": aligned_bytes == (REPO / V2_REL).read_bytes(),
        },
        "no_wallclock_note": (
            "日期=声明常量 2026-09-13；零 wall-clock/零网络/零 git 写操作；"
            "canonical JSON=pcbflow.hashing.canonical_json_bytes 口径"),
    }
    return comp


def _commit_guard(path: Path, data: bytes, label: str) -> str:
    if path.exists():
        if path.read_bytes() != data:
            _fail(f"{label} 已存在且重建字节不同（防覆写；拒绝覆写）")
        return "idempotent_skip"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    if path.read_bytes() != data:
        _fail(f"回读不一致: {label}")
    return "written"


def main() -> None:
    r1_raw = (REPO / R1_REL).read_bytes()
    record, aligned_bytes, protected_hashes = build_aligned()
    state = _commit_guard(REPO / OUT_REL, aligned_bytes, "对齐记录")
    comp = build_comparison(r1_raw, aligned_bytes)
    comp_bytes = hashing.canonical_json_bytes(comp)
    state2 = _commit_guard(REPO / COMP_REL, comp_bytes, "对比记录")
    if _sha(REPO / "pcbflow" / "cli.py") != CLI_SHA_CURRENT or \
            _sha(REPO / R1_REL) != R1_SHA or _sha(REPO / V2_REL) != V2_SHA:
        _fail("收工复核不符（保护/r1/v2 文件疑被触碰）")
    print(f"[r25-prep-aligned] 对齐记录 {state}：{OUT_REL}")
    print(f"[r25-prep-aligned] 对比记录 {state2}：{COMP_REL}")
    print(f"[r25-prep-aligned] 对齐自证：与 {V2_REL} 逐字节相等（sha256="
          f"{V2_SHA[:8]}）；r1 冻结件零回写（{R1_SHA[:8]}）")
    summary = comp["attribution_summary"]
    print(f"[r25-prep-aligned] 差异归因：anchor_byte="
          f"{summary['anchor_byte']}、v2_gauge_provenance_element="
          f"{summary['v2_gauge_provenance_element']}、unclassified="
          f"{summary['unclassified']}")


if __name__ == "__main__":
    main()
