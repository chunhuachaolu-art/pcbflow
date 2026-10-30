"""TL-2 critic run 管线（S14；SPEC-v3.0-PROPOSAL §TD4/§TD5；APR-0005）。

三段职责（全部纯函数；盘上实测与落盘由编排侧完成）：

1. ``reader_task_card`` / ``build_input_bundle``：critic 输入 bundle 的
   canonical 构建（byte-exact；bundle 自身 sha256 不内嵌自引——由编排侧
   写入 sidecar 文件，``bundle_sha256`` 供对账）。
2. ``validate_raw_flags``：读取者原始输出（**untrusted 模型输出**）的
   结构/语义校验。读者自封的 critic_status/valid 字段一律无效——raw
   顶层键固定，多余键直接判 invalid（fail-closed）。
3. ``ingest_run``：raw flags → hash 对账（bundle sha256+渲染/源板/profile
   hash 对盘上实测值）→ critic_status 赋值（全部过=executed；任一不过=
   invalid+原因）→ critic_run_record（合同 schema，经 critic.build_run）
   → critic.triage（TD5 十条件）→ 非 eligible 时人工队列 enqueue 事件
   （queue-event-ledger 纯函数内核，可并入调用方账本）。

TD4 红线：
- 记录是合同级投影：record.flags 只保留 category/confidence/location
  合同字段；读取者完整原文（含 description/abstain/reading_notes）以
  raw 字节 sha256 进入 record.evidence_refs，由主智能体落盘保全。
- flags=[] 只在五条件合取（executed+schema 合法+hash 匹配+模型获批+
  置信度在校准域内）时才表示「无旗」；bundle 声明无已校准域时
  in_calibrated_range=False，任何 run 一律 blocked→人工队列。
- 模型获批（model.approved）唯一依据=APR-0005（advisory_only 最小上岗
  等级）；编排侧实测 disposition 文件 hash 后以 approval_ok 传入，
  本模块不做 IO、不自行判定。

生成器模式：零 IO、零子进程、零网络、无 wall-clock、无主机路径；
仅标准库 + 包内 schemas/hashing/critic/queue。
"""

from __future__ import annotations

import json

from . import critic, hashing, queue, schemas

SCHEMA_VERSION = schemas.SCHEMA_V3
KIND = "critic_input_bundle"

RECORD_SCHEMA = critic.CRITIC_RUN_SCHEMA          # critic_run_record
APPROVAL_DISPOSITION_ID = "APR-0005"
APPROVAL_PATH_REL = ("out/v3-approvals/"
                     "disposition-APR-0005-critic-duty-level.json")
APPROVAL_DUTY_LEVEL = "advisory_only"
MODEL_PROVIDER = "subagent_critic_reader"

# raw flags JSON 合同（读取者输出；主智能体原样落盘 raw-flags.json）
RAW_TOPLEVEL_KEYS = ("reader_id", "per_board", "reading_notes")
RAW_BOARD_KEYS = ("profile_id", "flags")
RAW_FLAG_KEYS = ("category", "confidence", "location_evidence",
                 "description", "abstain")
READER_ID_MAX = 128
LOCATION_MAX = 256        # 与 critic_run_record.flags.location 同步
DESCRIPTION_MAX = 1024
SIDES = ("top", "bottom")
SPLITS = ("train", "validation", "holdout", "external_eval")

#: bundle 校准域声明（run-r1：无已校准域 → in_calibrated_range=False）
CALIBRATION_NOTE = ("当前无已校准置信域（校准数据未建立）：confidence 仅作 "
                    "advisory 排序参考，不进入任何 gate；in_calibrated_range "
                    "恒 False，flags=[] 一律按 blocked 路由人工（fail-closed）。"
                    "不确定时用 abstain=true，不得压低 confidence 伪装确定。")

#: TD4 输入缺席声明（run-r1 读参考 routed 态，无提议在审）
TD4_INPUTS_ABSENT_NOTE = (
    "TD4 critic 输入=板渲染、前后 diff、提议摘要、确定性 artifact refs。"
    "run-r1 为参考 routed 态的首次读取（无提议在审）：前后 diff 与提议"
    "摘要缺席，本 run 只读板渲染；缺席如实声明，不补造、不预支。")

#: 读取者禁止事项（TD4 语义红线；写入 bundle 与任务卡）
PROHIBITIONS = (
    "不得形成 DRC/solver/physics/waiver/layout/placement/board 结论"
    "（advisory 只出旗标/置信度/位置证据/说明）",
    "不得给出任何修改指令（改线、改布局、改参数等一律禁止）",
    "不得消旗/降级既有旗标（L2 加旗律：flags 单调增长）",
    "不得自封 critic_status/executed/valid——状态与合法性由管线赋值",
    "不确定就 abstain=true；宁缺勿造，禁止编造位置或现象",
    "输出恒为 untrusted 模型输出，不进入 gate 谓词或板写路径",
)


# ---------------------------------------------------------------------------
# bundle 构建（canonical、byte-exact）
# ---------------------------------------------------------------------------

def reader_task_card(*, renders_by_profile: dict) -> dict:
    """读取者任务卡（bundle 内字段；主智能体按此派发读取者）。

    renders_by_profile: {profile_id: [渲染文件相对 run 目录的 posix 路径]}。
    """
    return {
        "mission": (
            "以 advisory 身份对指定板渲染 PNG 做视觉读取：只输出旗标"
            "（类别/置信度/位置证据/说明）。允许类别以 bundle."
            "allowed_categories 为准；本任务不裁决任何质量结论。"),
        "untrusted_note": (
            "读取者输出恒为 untrusted 模型输出：critic_status/valid、"
            "flags=[] 是否表示「无旗」均由管线（pcbflow.critic_run."
            "ingest_run）赋值，读者不得自封任何状态或合法性。"),
        "inputs": {
            "renders": {pid: list(paths)
                        for pid, paths in renders_by_profile.items()},
            "bundle_fields": ("allowed_categories", "confidence_scale",
                              "prohibitions", "boards"),
        },
        "output_contract": {
            "format": ("单个 JSON 对象以文本返回（主智能体原样字节落盘 "
                       "raw-flags.json；不得改写读者文本）"),
            "shape": {
                "reader_id": "非空字符串（≤128 字符）",
                "per_board": [{
                    "profile_id": "必须与 bundle.boards[].profile_id 一一对应",
                    "flags": [{
                        "category": "allowed_categories 枚举之一",
                        "confidence": "0.0–1.0 数值（不含布尔）",
                        "location_evidence": "非空位置证据（≤256 字符）",
                        "description": "非空说明（≤1024 字符）",
                        "abstain": "布尔；不确定=true，禁止编造",
                    }],
                }],
                "reading_notes": "字符串；每板 flags=[] 时必须在此说明依据",
            },
            "requirements": (
                "每板必须出现且仅出现一次（profile_id 精确匹配）；"
                "每板给出 flags 数组（可为空数组+reading_notes 说明）；"
                "不确定就 abstain=true；只输出观察不输出结论或指令。"),
        },
    }


def build_input_bundle(*, run_id: str, selection_rule: str, boards: list,
                       approval_sha256: str,
                       calibration_domain_established: bool) -> dict:
    """构建 critic 输入 bundle（canonical dict；byte-exact 由调用方复验）。

    boards 每项：{profile_id, split, split_basis,
                  source_board: {path_rel, sha256},
                  profile: {path_rel, sha256},
                  renders: [{file_rel, side, sha256, observation}]}。
    approval_sha256: APR-0005 disposition 文件实测 sha256（编排侧读取）。
    非法输入 ValueError（fail-closed；bundle 是管线可信侧输入）。
    """
    if not (isinstance(run_id, str) and run_id):
        raise ValueError("build_input_bundle: run_id 必须为非空字符串")
    if not (isinstance(selection_rule, str) and selection_rule):
        raise ValueError("build_input_bundle: selection_rule 必须为非空字符串")
    if not _is_sha256(approval_sha256):
        raise ValueError("build_input_bundle: approval_sha256 必须为 64-hex")
    if not isinstance(calibration_domain_established, bool):
        raise ValueError("build_input_bundle: calibration_domain_established"
                         " 必须为布尔")
    norm_boards = []
    seen = set()
    for b in boards:
        norm_boards.append(_norm_board(b, seen))
    norm_boards.sort(key=lambda b: b["profile_id"])
    renders_by_profile = {b["profile_id"]: [r["file_rel"] for r in
                                            b["renders"]]
                          for b in norm_boards}
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": KIND,
        "run_id": run_id,
        "selection_rule": selection_rule,
        "boards": norm_boards,
        "td4_inputs_absent": TD4_INPUTS_ABSENT_NOTE,
        "allowed_categories": list(critic.FLAG_CATEGORIES),
        "confidence_scale": {
            "range": "0.0–1.0",
            "abstain_rule": "不确定就 abstain=true，禁止编造",
            "calibration_note": CALIBRATION_NOTE,
        },
        "prohibitions": list(PROHIBITIONS),
        "calibration": {
            "domain_established": calibration_domain_established,
            "note": CALIBRATION_NOTE,
        },
        "approval": {
            "disposition_id": APPROVAL_DISPOSITION_ID,
            "duty_level": APPROVAL_DUTY_LEVEL,
            "path_rel": APPROVAL_PATH_REL,
            "sha256": approval_sha256,
            "note": ("model.approved 的唯一依据指针（人工批准：advisory_only "
                     "最小上岗等级）；编排侧实测该文件 sha256 后绑定。"),
        },
        "reader_task_card": reader_task_card(
            renders_by_profile=renders_by_profile),
        "pipeline": {
            "record_schema": RECORD_SCHEMA,
            "status_assigned_by": "pcbflow.critic_run.ingest_run",
            "queue_events": "pcbflow.queue（queue-event-ledger 内核）",
            "advisory_only": critic.ADVISORY_ONLY,
        },
    }


def bundle_sha256(bundle: dict) -> str:
    """bundle 的 canonical 字节 sha256（sidecar 值；bundle 内不嵌入自引）。"""
    return hashing.sha256_bytes(hashing.canonical_json_bytes(bundle))


def canonical_sha256(obj: dict) -> str:
    """任意合同对象的 canonical 字节 sha256（与 bundle_sha256 同口径）。"""
    return bundle_sha256(obj)


def validate_bundle(bundle) -> None:
    """bundle 结构校验（管线可信侧；非法 ValueError，不产出 record）。"""
    if not isinstance(bundle, dict):
        raise ValueError("validate_bundle: bundle 必须为 dict")
    if bundle.get("kind") != KIND:
        raise ValueError(f"validate_bundle: kind 应为 {KIND!r}")
    if bundle.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("validate_bundle: schema_version 不符")
    if not (isinstance(bundle.get("run_id"), str) and bundle["run_id"]):
        raise ValueError("validate_bundle: run_id 缺失")
    if bundle.get("allowed_categories") != list(critic.FLAG_CATEGORIES):
        raise ValueError("validate_bundle: allowed_categories 与 critic."
                         "FLAG_CATEGORIES 不一致")
    cal = bundle.get("calibration")
    if not (isinstance(cal, dict)
            and isinstance(cal.get("domain_established"), bool)):
        raise ValueError("validate_bundle: calibration.domain_established "
                         "必须为布尔")
    ap = bundle.get("approval")
    if not (isinstance(ap, dict)
            and ap.get("disposition_id") == APPROVAL_DISPOSITION_ID
            and ap.get("duty_level") == APPROVAL_DUTY_LEVEL
            and _is_sha256(ap.get("sha256", ""))):
        raise ValueError("validate_bundle: approval 块缺失或非法"
                         "（APR-0005 指针必须完整）")
    if not isinstance(bundle.get("reader_task_card"), dict):
        raise ValueError("validate_bundle: reader_task_card 缺失")
    if not isinstance(bundle.get("boards"), list) or not bundle["boards"]:
        raise ValueError("validate_bundle: boards 必须为非空列表")
    seen = set()
    for b in bundle["boards"]:
        _norm_board(b, seen)


# ---------------------------------------------------------------------------
# raw flags（untrusted 读取者输出）校验
# ---------------------------------------------------------------------------

def validate_raw_flags(raw, *, expected_profiles) -> list:
    """raw flags JSON 结构+语义校验；返回错误列表（[]=合法，fail-closed）。

    顶层键固定为 reader_id/per_board/reading_notes（多余键=invalid——
    读者自封 status/valid 等字段由此挡下）；per_board 必须与
    expected_profiles 一一对应；每面旗五字段齐全且合法。
    """
    errs: list = []
    if not isinstance(raw, dict):
        return ["raw_flags: 不是 JSON 对象"]
    extra = sorted(set(raw) - set(RAW_TOPLEVEL_KEYS))
    if extra:
        errs.append(f"raw_flags: 未知顶层键 {extra}（读者自封字段一律无效）")
    missing = [k for k in RAW_TOPLEVEL_KEYS if k not in raw]
    if missing:
        errs.append(f"raw_flags: 缺少顶层键 {missing}")
    rid = raw.get("reader_id")
    if not (isinstance(rid, str) and 0 < len(rid) <= READER_ID_MAX):
        errs.append("raw_flags.reader_id: 必须为非空字符串"
                    f"（≤{READER_ID_MAX} 字符）")
    if "reading_notes" in raw and not isinstance(raw["reading_notes"], str):
        errs.append("raw_flags.reading_notes: 必须为字符串")
    boards = raw.get("per_board")
    if not isinstance(boards, list):
        errs.append("raw_flags.per_board: 必须为数组")
        return errs
    expected = sorted(set(expected_profiles))
    got = []
    for i, b in enumerate(boards):
        if not isinstance(b, dict):
            errs.append(f"per_board[{i}]: 不是对象")
            continue
        extra_b = sorted(set(b) - set(RAW_BOARD_KEYS))
        if extra_b:
            errs.append(f"per_board[{i}]: 未知键 {extra_b}")
        missing_b = [k for k in RAW_BOARD_KEYS if k not in b]
        if missing_b:
            errs.append(f"per_board[{i}]: 缺少键 {missing_b}")
            continue
        pid = b["profile_id"]
        if not isinstance(pid, str):
            errs.append(f"per_board[{i}].profile_id: 必须为字符串")
        else:
            got.append(pid)
            if pid not in expected:
                errs.append(f"per_board[{i}].profile_id: {pid!r} 不在 "
                            f"bundle 板集 {expected} 内")
        flags = b["flags"]
        if not isinstance(flags, list):
            errs.append(f"per_board[{i}].flags: 必须为数组")
            continue
        for j, f in enumerate(flags):
            errs.extend(_flag_errors(f, f"per_board[{i}].flags[{j}]"))
    dup = sorted({p for p in got if got.count(p) > 1})
    if dup:
        errs.append(f"raw_flags.per_board: profile_id 重复 {dup}")
    absent = [p for p in expected if p not in got]
    if absent:
        errs.append(f"raw_flags.per_board: 缺少 bundle 板 {absent}")
    return errs


def _flag_errors(f, where: str) -> list:
    errs: list = []
    if not isinstance(f, dict):
        return [f"{where}: 旗标不是对象"]
    extra = sorted(set(f) - set(RAW_FLAG_KEYS))
    if extra:
        errs.append(f"{where}: 未知键 {extra}")
    missing = [k for k in RAW_FLAG_KEYS if k not in f]
    if missing:
        errs.append(f"{where}: 缺少键 {missing}")
        return errs
    if f["category"] not in critic.FLAG_CATEGORIES:
        errs.append(f"{where}.category: {f['category']!r} 不在 advisory "
                    f"类别集 {list(critic.FLAG_CATEGORIES)}")
    c = f["confidence"]
    if isinstance(c, bool) or not isinstance(c, (int, float)) \
            or not 0.0 <= float(c) <= 1.0:
        errs.append(f"{where}.confidence: 必须为 [0,1] 数值，得到 {c!r}")
    loc = f["location_evidence"]
    if not (isinstance(loc, str) and loc.strip()
            and len(loc) <= LOCATION_MAX):
        errs.append(f"{where}.location_evidence: 必须为非空字符串"
                    f"（≤{LOCATION_MAX} 字符）")
    desc = f["description"]
    if not (isinstance(desc, str) and desc.strip()
            and len(desc) <= DESCRIPTION_MAX):
        errs.append(f"{where}.description: 必须为非空字符串"
                    f"（≤{DESCRIPTION_MAX} 字符）")
    if not isinstance(f["abstain"], bool):
        errs.append(f"{where}.abstain: 必须为布尔")
    return errs


# ---------------------------------------------------------------------------
# ingest + 分诊（critic_status 赋值 → record → TD5 路由 → 队列事件）
# ---------------------------------------------------------------------------

def ingest_run(*, run_id: str, bundle: dict, raw_flags_text: str,
               expected_bundle_sha256: str, actual_hashes: dict,
               approval_ok: bool, ledger_events=None,
               provenance_hashes: dict | None = None,
               judge_gate_pass: bool = False,
               required_checkers_executed: bool = False,
               no_stale_or_unknown: bool = False,
               whitelist_item: bool = False) -> dict:
    """raw flags → critic_run_record + TD5 路由 + 队列事件（fail-closed）。

    - expected_bundle_sha256：sidecar 声明值；与内存 bundle 的 canonical
      hash 不符 = 管线可信侧漂移 → ValueError（不产出 record）。
    - actual_hashes：编排侧对盘上实测的 sha256，键约定
      {"bundle": 可选, "raw_flags": 可选,
       "render:<file_rel>", "source_board:<profile_id>",
       "profile:<profile_id>"}；任一声明键缺失或与 bundle 不符 →
      input_hashes_match=False → critic_status=invalid（fail-closed）。
    - approval_ok：编排侧实测 APR-0005 disposition 文件 hash 后的真值；
      False → invalid（模型未获批不得执行）。
    - provenance_hashes：可选披露绑定（如 raw 输出曾做纯结构性修复时的
      原文留证/披露文件 sha256）——以 ``provenance:<名>`` 键并入
      input_hashes，值并入 evidence_refs；record 本身无自由文本 notes
      字段（additionalProperties=false），人读披露由编排侧产物承载。
    - TD5 前置谓词缺省全 False（run-r1 无 judge/checker 数据=fail-closed）。

    返回 {record, record_sha256, triage, queue_events, ledger_events,
          invalid_reasons, abstain_count, raw_flags_sha256}。
    """
    validate_bundle(bundle)
    if bundle["run_id"] != run_id:
        raise ValueError(f"ingest_run: bundle.run_id={bundle['run_id']!r} "
                         f"≠ run_id={run_id!r}")
    if bundle_sha256(bundle) != expected_bundle_sha256:
        raise ValueError("ingest_run: bundle canonical hash 与 sidecar 声明"
                         "不符（可信侧漂移，拒绝产出 record）")
    expected_profiles = [b["profile_id"] for b in bundle["boards"]]
    domain_established = bundle["calibration"]["domain_established"]

    # ---- untrusted raw 解析与校验 ----------------------------------------
    invalid_reasons: list = []
    try:
        raw = json.loads(raw_flags_text)
    except Exception as exc:                      # noqa: BLE001
        raw = None
        invalid_reasons.append(f"raw_flags: 不是合法 JSON（{exc}）")
    raw_valid = raw is not None
    if raw is not None:
        raw_errs = validate_raw_flags(raw, expected_profiles=expected_profiles)
        invalid_reasons.extend(raw_errs)
        raw_valid = not raw_errs

    raw_bytes = raw_flags_text.encode("utf-8")
    raw_sha = hashing.sha256_bytes(raw_bytes)
    actual = actual_hashes if isinstance(actual_hashes, dict) else {}

    # ---- hash 对账（bundle 声明 vs 盘上实测） ------------------------------
    hash_reasons, declared = _hash_check(bundle, actual)
    if "raw_flags" in actual and actual["raw_flags"] != raw_sha:
        hash_reasons.append("hash: raw_flags 盘上实测 sha256 与传入文本"
                            "不一致（落盘须为原样字节）")
    invalid_reasons.extend(hash_reasons)
    hashes_ok = not hash_reasons

    # ---- critic_status 赋值（管线，不由读者自封） --------------------------
    executed = raw_valid and hashes_ok and approval_ok is True
    critic_status = "executed" if executed else "invalid"
    if approval_ok is not True:
        invalid_reasons.append(f"approval: {APPROVAL_DISPOSITION_ID} 锚校验"
                               "未通过（model.approved=False，fail-closed）")

    # ---- record 构建（合同 schema 投影） -----------------------------------
    flags = []
    abstain_count = 0
    if raw is not None and raw_valid:
        rid = raw.get("reader_id")
        for b in raw.get("per_board", []):
            for f in b.get("flags", []):
                if f.get("abstain") is True:
                    abstain_count += 1
                flags.append({"category": f["category"],
                              "confidence": float(f["confidence"]),
                              "location": f["location_evidence"]})
    else:
        rid = None
    input_hashes = {"raw_flags": raw_sha,
                    f"approval:{APPROVAL_DISPOSITION_ID}":
                        bundle["approval"]["sha256"]}
    for key in sorted(declared):
        input_hashes[key] = declared[key]
    if "bundle" in actual:
        input_hashes["bundle"] = actual["bundle"]
    # provenance 披露绑定（键冲突/格式非法 fail-closed；名字不含命名空间分隔符）
    prov = dict(provenance_hashes) if provenance_hashes else {}
    bad_prov = sorted(k for k, v in prov.items()
                      if not (isinstance(k, str) and k and ":" not in k
                              and _is_sha256(v)))
    if bad_prov:
        raise ValueError(f"ingest_run: provenance_hashes 键值非法: {bad_prov}")
    evidence = [raw_sha]
    for k in sorted(prov):
        pkey = f"provenance:{k}"
        if pkey in input_hashes:
            raise ValueError(f"ingest_run: provenance 键冲突 {pkey!r}")
        input_hashes[pkey] = prov[k]
        evidence.append(prov[k])
    run = critic.build_run(
        critic_run_id=f"CR-{run_id}",
        candidate_id=f"tl2-{run_id}",
        critic_status=critic_status,
        model={"provider": MODEL_PROVIDER, "version": rid,
               "approved": approval_ok is True},
        input_hashes=input_hashes,
        flags=flags,
        input_hashes_match=hashes_ok,
        calibration={"in_calibrated_range": domain_established},
        evidence_refs=evidence,
        schema_validation={"valid": raw_valid,
                           "schema_sha256":
                               schemas.schema_hash(RECORD_SCHEMA)},
    )
    decision = critic.triage(
        run, judge_gate_pass=judge_gate_pass,
        required_checkers_executed=required_checkers_executed,
        no_stale_or_unknown=no_stale_or_unknown,
        whitelist_item=whitelist_item)
    run["critic_outcome"] = "advisory" if decision["eligible"] else "blocked"
    errs = critic.validate_run(run)
    if errs:                                       # 不变性守卫：不可达
        raise ValueError(f"ingest_run: record 非法（内部错误）: {errs}")
    record_sha = canonical_sha256(run)

    # ---- 队列事件（非 eligible → 人工 enqueue；eligible → 无事件） ----------
    events = list(ledger_events) if ledger_events is not None else []
    queue_events: list = []
    if not decision["eligible"]:
        ev = queue.make_event(
            events, event="enqueue", item_id=f"ITEM-{run_id}",
            actor="pcbflow-critic-pipeline", actor_role="critic_model",
            reason_code=decision["status"], refs={"critic_ref": record_sha})
        events, ev = queue.append(events, ev)
        queue_events.append(ev)
    return {
        "record": run,
        "record_sha256": record_sha,
        "triage": decision,
        "queue_events": queue_events,
        "ledger_events": events,
        "invalid_reasons": invalid_reasons,
        "abstain_count": abstain_count,
        "raw_flags_sha256": raw_sha,
    }


# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------

def _is_sha256(v) -> bool:
    return (isinstance(v, str) and len(v) == 64
            and all(ch in "0123456789abcdef" for ch in v))


def _norm_board(b, seen: set) -> dict:
    if not isinstance(b, dict):
        raise ValueError("build_input_bundle: board 必须为 dict")
    required = ("profile_id", "split", "split_basis", "source_board",
                "profile", "renders")
    unknown = sorted(set(b) - set(required))
    if unknown:
        raise ValueError(f"build_input_bundle: board 未知键 {unknown}"
                         "（additionalProperties=false）")
    missing = [k for k in required if k not in b]
    if missing:
        raise ValueError(f"build_input_bundle: board 缺少键 {missing}")
    pid = b["profile_id"]
    if not (isinstance(pid, str) and pid) or pid in seen:
        raise ValueError(f"build_input_bundle: profile_id 非法或重复 {pid!r}")
    seen.add(pid)
    if b["split"] not in SPLITS:
        raise ValueError(f"build_input_bundle: split 非法 {b['split']!r}")
    if not (isinstance(b["split_basis"], str) and b["split_basis"]):
        raise ValueError(f"build_input_bundle: split_basis 缺失（{pid}）")
    for part, label in ((b["source_board"], "source_board"),
                        (b["profile"], "profile")):
        if not isinstance(part, dict) \
                or sorted(set(part) - {"path_rel", "sha256"}) \
                or not isinstance(part.get("path_rel"), str) \
                or not part["path_rel"] \
                or not _is_sha256(part.get("sha256", "")):
            raise ValueError(f"build_input_bundle: {label} 路径/hash 非法"
                             f"（{pid}；仅允许 path_rel/sha256）")
    renders = b["renders"]
    if not isinstance(renders, list) or len(renders) < 2:
        raise ValueError(f"build_input_bundle: renders 必须 ≥2（顶/底，{pid}）")
    norm_renders = []
    sides = set()
    render_keys = {"file_rel", "side", "sha256", "observation"}
    for r in renders:
        if not isinstance(r, dict) or sorted(set(r) - render_keys) \
                or not isinstance(r.get("file_rel"), str) or not r["file_rel"] \
                or not _is_sha256(r.get("sha256", "")) \
                or r.get("side") not in SIDES \
                or not (isinstance(r.get("observation"), str)
                        and r["observation"]):
            raise ValueError(f"build_input_bundle: render 条目非法（{pid}）"
                             "（仅允许 file_rel/sha256/side/observation，"
                             "observation 须非空）")
        sides.add(r["side"])
        norm_renders.append({"file_rel": r["file_rel"], "side": r["side"],
                             "sha256": r["sha256"],
                             "observation": r["observation"]})
    norm_renders.sort(key=lambda r: r["file_rel"])
    if sides != {"top", "bottom"}:
        raise ValueError(f"build_input_bundle: {pid} 缺顶/底渲染（{sides}）")
    return {"profile_id": pid, "split": b["split"],
            "split_basis": b["split_basis"],
            "source_board": dict(b["source_board"]),
            "profile": dict(b["profile"]), "renders": norm_renders}


def _hash_check(bundle: dict, actual: dict) -> tuple:
    """bundle 声明 hash vs 盘上实测；（reasons, declared 键值表）。"""
    reasons: list = []
    declared: dict = {}
    for b in bundle["boards"]:
        pid = b["profile_id"]
        for label, part in (("source_board", b["source_board"]),
                            ("profile", b["profile"])):
            key = f"{label}:{pid}"
            declared[key] = part["sha256"]
            got = actual.get(key)
            if got is None:
                reasons.append(f"hash: {key} 缺少盘上实测值（fail-closed）")
            elif got != part["sha256"]:
                reasons.append(f"hash: {key} 实测 {got} ≠ 声明 "
                               f"{part['sha256']}")
        for r in b["renders"]:
            key = f"render:{r['file_rel']}"
            declared[key] = r["sha256"]
            got = actual.get(key)
            if got is None:
                reasons.append(f"hash: {key} 缺少盘上实测值（fail-closed）")
            elif got != r["sha256"]:
                reasons.append(f"hash: {key} 实测 {got} ≠ 声明 {r['sha256']}")
    if "bundle" in actual and not _is_sha256(actual["bundle"]):
        reasons.append("hash: actual_hashes['bundle'] 非 64-hex")
    return reasons, declared
