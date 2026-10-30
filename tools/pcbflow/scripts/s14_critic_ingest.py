#!/usr/bin/env python
"""S14-TL2 编排（第二段）：raw flags ingest → 分诊 → 入账（写 out/v3-tl2/）。

编排侧职责（库侧 pcbflow/critic_run.py 保持纯函数零落盘）：
1. 对账（fail-closed）：bundle/sidecar canonical hash 一致；APR-0005
   disposition 文件实测 sha256 == bundle.approval.sha256 且语义为
   advisory；盘上实测 hash（bundle/渲染×4/源板×2/profile×2/raw-flags）。
2. raw 修复披露（如实、不掩盖）：读取者原文 raw-flags-as-returned.txt
   必须不可解析（留证事实）；对 raw-flags.json 的差异必须为**纯单点
   插入**（0 删 0 改）——否则拒绝入账（防「机械修复」掩盖内容改动）；
   实测修复事实写 raw-flags-repair-disclosure.json（canonical）。
3. ingest_run：critic_status 赋值 → TD5 十条件分诊 → 人工 enqueue 事件
   （queue-event-ledger 纯函数内核）；provenance_hashes 把披露文件与
   读取者原文 sha 绑进 record.input_hashes/evidence_refs（record 为
   合同级投影、无自由文本 notes 字段）。
4. 落盘四件：raw-flags-repair-disclosure.json / critic-run-record-
   CR-run-r1.json / queue-event-ledger.jsonl / ingest-report.json
   （canonical JSON、防覆写、无 wall-clock、无主机路径）。

用法：python scripts/s14_critic_ingest.py   （仓库根执行）
"""

from __future__ import annotations

import difflib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import critic, critic_run, hashing, queue    # noqa: E402

RUN_ID = "run-r1"
RUN_DIR = REPO / "out" / "v3-tl2" / "critic-runs" / RUN_ID
BUNDLE = RUN_DIR / "critic-input-bundle.json"
SIDECAR = RUN_DIR / "critic-input-bundle.sha256"
RAW_FLAGS = RUN_DIR / "raw-flags.json"
RAW_ORIG = RUN_DIR / "raw-flags-as-returned.txt"
APPROVAL = REPO / critic_run.APPROVAL_PATH_REL

DISCLOSURE = RUN_DIR / "raw-flags-repair-disclosure.json"
RECORD_OUT = RUN_DIR / "critic-run-record-CR-run-r1.json"
LEDGER_OUT = RUN_DIR / "queue-event-ledger.jsonl"
REPORT_OUT = RUN_DIR / "ingest-report.json"

#: TD5 前置谓词（run-r1 参考态 advisory 读取的如实取值与依据）
PREDICATES = {
    "judge_gate_pass": False,
    "required_checkers_executed": False,
    "no_stale_or_unknown": True,
    "whitelist_item": False,
}
PREDICATE_BASIS = (
    "judge_gate_pass=False：run-r1 为参考 routed 态 advisory 读取，无 judge "
    "运行记录（缺证据闭门律，fail-closed）；required_checkers_executed="
    "False：本 run 无 checker 上下文；no_stale_or_unknown=True：run 自身"
    "各状态无 stale/unknown/not_available（critic_status/schema/hash 面"
    "如实），judge/checker 缺席由对应谓词 False 捕捉；whitelist_item="
    "False：非白名单项。")


def _fail(msg: str) -> None:
    print(f"[s14-ingest] FAIL: {msg}")
    sys.exit(1)


def _write_canonical(path: Path, obj) -> str:
    data = hashing.canonical_json_bytes(obj)
    path.write_bytes(data)
    return hashing.sha256_bytes(data)


def _sha_file(path: Path) -> str:
    return hashing.sha256_file(str(path))


def main() -> None:
    for out in (DISCLOSURE, RECORD_OUT, LEDGER_OUT, REPORT_OUT):
        if out.exists():
            _fail(f"{out.name} 已存在（防覆写；发布产物不可覆写）")

    # ---- 1. bundle/sidecar 对账 ------------------------------------------
    if not BUNDLE.exists() or not SIDECAR.exists():
        _fail("bundle/sidecar 缺失（先跑第一段 render+bundle）")
    bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
    sidecar = SIDECAR.read_text(encoding="utf-8").strip()
    bundle_sha_disk = _sha_file(BUNDLE)
    if critic_run.bundle_sha256(bundle) != sidecar \
            or bundle_sha_disk != sidecar:
        _fail("bundle canonical/sidecar/盘上字节 三方对账不符（可信侧漂移）")
    # ---- 2. APR-0005 锚 ----------------------------------------------------
    if not APPROVAL.exists():
        _fail("APR-0005 disposition 缺失")
    approval_sha = _sha_file(APPROVAL)
    apr = json.loads(APPROVAL.read_text(encoding="utf-8"))
    if approval_sha != bundle["approval"]["sha256"] \
            or apr.get("disposition_id") != critic_run.APPROVAL_DISPOSITION_ID \
            or "advisory" not in str(apr.get("rationale_code", "")):
        _fail("APR-0005 锚校验不符（bundle 声明 vs 盘上实测/语义）")
    approval_ok = True

    # ---- 3. raw 修复披露（实测事实；纯插入守卫） ----------------------------
    if not RAW_FLAGS.exists() or not RAW_ORIG.exists():
        _fail("raw-flags.json / raw-flags-as-returned.txt 缺失")
    raw_text = RAW_FLAGS.read_text(encoding="utf-8")
    orig_text = RAW_ORIG.read_text(encoding="utf-8")
    raw_sha = _sha_file(RAW_FLAGS)
    orig_sha = _sha_file(RAW_ORIG)
    if raw_text == orig_text:
        _fail("raw-flags.json 与原文相同：与移交事实（已做结构性修复）矛盾")
    try:
        json.loads(orig_text)
        _fail("读取者原文可解析：与移交事实（json.loads 失败）矛盾，"
              "拒绝入账（修复叙事与实测不符）")
    except json.JSONDecodeError as parse_error:
        orig_parse_error = (f"{type(parse_error).__name__}: {parse_error}")
    json.loads(raw_text)                      # repaired 必须可解析
    ops = [op for op in difflib.SequenceMatcher(None, orig_text, raw_text,
                                                autojunk=False).get_opcodes()
           if op[0] != "equal"]
    if len(ops) != 1 or ops[0][0] != "insert" \
            or ops[0][2] - ops[0][1] != 0:
        _fail(f"raw 修复差异非纯单点插入（ops={ops}）：拒绝入账——"
              "「内容字符零改动」不可证")
    _, i1, i2, j1, j2 = ops[0]
    inserted = raw_text[j1:j2]
    disclosure = {
        "schema_version": "3.0",
        "kind": "tl2_raw_flags_repair_disclosure",
        "run_id": RUN_ID,
        "as_returned": {
            "path_rel": f"out/v3-tl2/critic-runs/{RUN_ID}/"
                        "raw-flags-as-returned.txt",
            "sha256": orig_sha,
            "bytes": len(orig_text.encode("utf-8")),
            "json_parses": False,
            "parse_error": orig_parse_error,
        },
        "repaired_ingested": {
            "path_rel": f"out/v3-tl2/critic-runs/{RUN_ID}/raw-flags.json",
            "sha256": raw_sha,
            "bytes": len(raw_text.encode("utf-8")),
        },
        "repair": {
            "kind": "single_insertion",
            "insert_at_char": i1,
            "inserted": inserted,
            "chars_added": j2 - j1,
            "chars_removed": 0,
            "chars_modified": 0,
            "note": ("实测修复=在 flags 数组闭合处单点插入 2 个结构字符"
                     "（板对象闭合 } 与 per_board 数组闭合 ] 的缺失对）；"
                     "内容字符零改动零移动（difflib 单 insert op 守卫）。"
                     "读取者原文中 reading_notes 本已写在顶层——移交描述"
                     "「移到顶层」与实测不符，如实以本文件实测为准。"),
        },
        "pipeline_note": ("管线对读取者输出零位置容错：未修复的原文会因 "
                          "JSON 解析失败判 critic_status=invalid；本修复"
                          "为落盘前置的纯结构机械操作，留证于 as_returned"
                          " 字节与 hash，不在 record 内掩藏。"),
    }
    disclosure_sha = _write_canonical(DISCLOSURE, disclosure)
    print(f"[s14-ingest] 披露文件写出：raw-flags-repair-disclosure.json "
          f"sha256={disclosure_sha[:16]}…（插入 {inserted!r}@{i1}，"
          f"0 删 0 改）")

    # ---- 4. 盘上实测 hash → ingest -----------------------------------------
    actual = {"bundle": bundle_sha_disk, "raw_flags": raw_sha}
    for b in bundle["boards"]:
        pid = b["profile_id"]
        actual[f"source_board:{pid}"] = _sha_file(REPO / b["source_board"]
                                                  ["path_rel"])
        actual[f"profile:{pid}"] = _sha_file(REPO / b["profile"]["path_rel"])
        for r in b["renders"]:
            actual[f"render:{r['file_rel']}"] = _sha_file(
                RUN_DIR / r["file_rel"])
    enum = schemas_enum()
    other_ok = "other_advisory" in enum
    result = critic_run.ingest_run(
        run_id=RUN_ID, bundle=bundle, raw_flags_text=raw_text,
        expected_bundle_sha256=sidecar, actual_hashes=actual,
        approval_ok=approval_ok,
        provenance_hashes={"raw_flags_as_returned": orig_sha,
                           "raw_flags_repair_disclosure": disclosure_sha},
        **PREDICATES)
    rec = result["record"]
    print(f"[s14-ingest] ingest 裁决：critic_status={rec['critic_status']} "
          f"outcome={rec['critic_outcome']} flags={len(rec['flags'])} "
          f"abstain={result['abstain_count']} "
          f"invalid_reasons={result['invalid_reasons']}")

    # ---- 5. 落盘 record / ledger / report ----------------------------------
    record_sha = _write_canonical(RECORD_OUT, rec)
    if record_sha != result["record_sha256"]:
        _fail("record 落盘字节与 record_sha256 不符")
    events = result["ledger_events"]
    if queue.verify_chain(events) != []:
        _fail("queue-event-ledger 链校验失败")
    # 落盘口径与 decision-ledger.jsonl 惯例一致：每事件单行紧凑 JSON+换行
    ledger_bytes = "".join(
        json.dumps(ev, ensure_ascii=False, sort_keys=True) + "\n"
        for ev in events).encode("utf-8")
    LEDGER_OUT.write_bytes(ledger_bytes)
    reread = [json.loads(line) for line in
              LEDGER_OUT.read_text(encoding="utf-8").splitlines()]
    if queue.verify_chain(reread) != [] or len(reread) != len(events):
        _fail("ledger 落盘后复读校验失败")
    ledger_head = (events[-1]["event_sha256"] if events else None)
    ledger_sha = _sha_file(LEDGER_OUT) if events else None

    other_flag_count = sum(1 for f in rec["flags"]
                           if f["category"] == "other_advisory")
    report = {
        "schema_version": "3.0",
        "kind": "tl2_critic_ingest_report",
        "run_id": RUN_ID,
        "inputs": {
            "bundle": {"path_rel": f"out/v3-tl2/critic-runs/{RUN_ID}/"
                                   "critic-input-bundle.json",
                       "sha256": bundle_sha_disk, "sidecar_match": True},
            "approval": {"path_rel": critic_run.APPROVAL_PATH_REL,
                         "sha256": approval_sha,
                         "disposition_id": "APR-0005",
                         "duty_level": "advisory_only",
                         "anchor_ok": True},
            "raw_flags": {"path_rel": f"out/v3-tl2/critic-runs/{RUN_ID}/"
                                      "raw-flags.json",
                          "sha256": raw_sha},
            "actual_hashes_checked": sorted(actual),
        },
        "validation": {
            "invalid_reasons": result["invalid_reasons"],
            "hashes_ok": rec["input_hashes_match"],
            "raw_schema_valid": rec["schema_validation"]["valid"],
        },
        "record": {
            "path_rel": f"out/v3-tl2/critic-runs/{RUN_ID}/"
                        "critic-run-record-CR-run-r1.json",
            "sha256": record_sha,
            "critic_run_id": rec["critic_run_id"],
            "critic_status": rec["critic_status"],
            "critic_outcome": rec["critic_outcome"],
            "advisory_only": rec["advisory_only"],
            "model": rec["model"],
            "flags_count": len(rec["flags"]),
            "abstain_count": result["abstain_count"],
            "evidence_refs": rec["evidence_refs"],
        },
        "other_advisory_enum_check": {
            "in_allowed_categories": other_ok,
            "allowed_categories": list(critic.FLAG_CATEGORIES),
            "source": ("critic.FLAG_CATEGORIES 与 schemas."
                       "critic_run_record flags.category 枚举一致；"
                       "未改枚举"),
            "other_advisory_flags_mapped": other_flag_count,
        },
        "triage": {
            "decision": result["triage"],
            "predicates": PREDICATES,
            "basis": PREDICATE_BASIS,
            "note": ("无论 eligible 与否，裁决依据=triage."
                     "failed_conditions（机器可读）+本 basis（人读）；"
                     "queue_deprioritized 只是分流不是质量 pass。"),
        },
        "queue": {
            "path_rel": f"out/v3-tl2/critic-runs/{RUN_ID}/"
                        "queue-event-ledger.jsonl",
            "sha256": ledger_sha,
            "event_count": len(events),
            "event_kinds": [ev["event"] for ev in events],
            "item_ids": [ev["item_id"] for ev in events],
            "head_event_sha256": ledger_head,
            "reason_codes": [ev.get("reason_code") for ev in events],
        },
        "disclosure": {
            "path_rel": f"out/v3-tl2/critic-runs/{RUN_ID}/"
                        "raw-flags-repair-disclosure.json",
            "sha256": disclosure_sha,
            "summary": ("读取者原文不可解析（留证 as-returned.txt）；"
                        "ingest 输入=主智能体纯结构修复版（单点插入 2 结构"
                        "字符，内容零改动零移动，difflib 守卫）；两者 sha256 "
                        "均绑进 record provenance/evidence_refs。"),
        },
    }
    report_sha = _write_canonical(REPORT_OUT, report)
    print(f"[s14-ingest] record={RECORD_OUT.name} "
          f"sha256={record_sha[:16]}… | ledger {len(events)} 事件 "
          f"head={str(ledger_head)[:16]}… | report sha256="
          f"{report_sha[:16]}…")
    print("[s14-ingest] 入账完成（TL-2 首次 advisory run）")


def schemas_enum() -> tuple:
    from pcbflow import schemas
    return tuple(schemas.SCHEMAS["critic_run_record"]["properties"]["flags"]
                 ["items"]["properties"]["category"]["enum"])


if __name__ == "__main__":
    main()
