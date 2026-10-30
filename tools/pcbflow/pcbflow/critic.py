"""TD4 Critic advisory 分诊（TL-2；SPEC-v3.0-PROPOSAL §TD4/§TD5）。

L2 加旗律（advisory-only）：Critic 只能加旗（旗标/置信度/位置证据），
不能消旗、降级、推翻事实或形成 DRC/solver/physics/waiver/layout 结论。
本模块因此**不提供** remove_flag/clear_flag 之类的消旗 API——flags 单调
增长，路由侧（triage）把非空 flags 一律送人工队列。

核心不变量：
1. ``flags=[]`` 只有在 critic_status=executed、schema+语义合法、
   input_hashes_match=true、model.approved=true 且置信度在已校准范围内
   （calibration.in_calibrated_range=true）时才表示「无旗」；否则
   critic_outcome 语义为 blocked 并入人工队列（flags_empty_semantics）。
2. triage 严格实现 TD5 有限自动分流谓词：全前置成立才
   queue_deprioritized（且这只是队列分流，不是质量 pass）；任一缺失即
   critic_auto_route_blocked。judge fail 或白名单项强制人工
   （manual_queue_mandatory 注记，见模块尾 schema 偏差说明）。
3. promotion_gate：晋升不得只看「人工支持旗标 ≥85%」——必须同时过
   最小样本数、分板 recall/FPR、abstain rate、calibration error、
   worst-board 与独立随机审计集；未达门永远只做全量陪审或排序降噪。

生成器模式：纯函数、零 IO、零子进程、零网络、无 wall-clock；
仅标准库 + 包内 schemas/hashing。
"""

from __future__ import annotations

from . import hashing, schemas, health_projection

SCHEMA_VERSION = schemas.SCHEMA_V3
CRITIC_RUN_SCHEMA = "critic_run_record"

# TD4 critic_status 全集（schemas.critic_run_record 同步）
CRITIC_STATUSES = ("executed", "not_executed", "error", "invalid", "stale")

# TD4 允许旗标类别（advisory；schemas 枚举同步）
FLAG_CATEGORIES = ("silk_readability", "courtyard_crowding",
                   "placement_pattern_anomaly", "suspicious_reroute",
                   "doc_artifact_mismatch", "other_advisory")

# L2 加旗律：advisory_only 恒 True（build_run 自动写入，调用方不可覆盖）
ADVISORY_ONLY = True

# ---------------------------------------------------------------------------
# TD5 路由条件 id（failed_conditions 引用；稳定契约，测试锚定）
# ---------------------------------------------------------------------------

COND_JUDGE_GATE = "judge_gate_pass"                # judge_gate=pass
COND_CHECKERS = "required_checkers_executed"       # 全部 required checker 执行
COND_NO_STALE = "no_stale_or_unknown"              # 无 stale/unknown/not_available
COND_STATUS = "critic_status_executed"             # critic.status=executed
COND_SCHEMA = "critic_schema_valid"                # critic.valid=true（schema+语义）
COND_HASHES = "critic_input_hashes_match"          # critic.input_hashes_match=true
COND_MODEL = "critic_model_approved"               # critic.model_approved=true
COND_CALIB = "critic_calibration_in_range"         # 置信度在已校准范围内
COND_FLAGS = "critic_flags_empty"                  # critic.flags=[]
COND_WHITELIST = "item_not_whitelist"              # 非白名单项
# judge fail / 白名单项的强制人工注记（附在 failed_conditions；见文件尾偏差说明）
MANUAL_QUEUE_MANDATORY = "manual_queue_mandatory"

ROUTE_CONDITION_IDS = (COND_JUDGE_GATE, COND_CHECKERS, COND_NO_STALE,
                       COND_STATUS, COND_SCHEMA, COND_HASHES, COND_MODEL,
                       COND_CALIB, COND_FLAGS, COND_WHITELIST)

# ---------------------------------------------------------------------------
# TD4 晋升门默认阈值（SPEC：分层指标门；只看人工支持率不得晋升）
# ---------------------------------------------------------------------------

PROMOTION_MIN_SAMPLES = 200          # 固定最小样本数
PROMOTION_MIN_BOARD_RECALL = 0.8     # 每板 recall 下限
PROMOTION_MAX_BOARD_FPR = 0.15       # 每板 FPR 上限
PROMOTION_MAX_ABSTAIN_RATE = 0.2     # abstain rate 上限
PROMOTION_MAX_CALIBRATION_ERROR = 0.1
PROMOTION_MIN_WORST_BOARD_RECALL = 0.7
PROMOTION_MIN_AUDIT_SAMPLES = 30     # 独立随机审计集最小样本
PROMOTION_MIN_HUMAN_SUPPORT_RATE = 0.85  # 附加记录项：单独不构成晋升


# ---------------------------------------------------------------------------
# 构造与验证
# ---------------------------------------------------------------------------

def build_run(*, critic_run_id: str, candidate_id: str, critic_status: str,
              model: dict, input_hashes: dict, flags=(), **opt) -> dict:
    """按 schemas.critic_run_record 构造 critic run 并自检（fail-closed）。

    advisory_only 恒 True 自动写入（调用方不可通过 opt 覆盖——加旗律）。
    schema_validation 默认填入当前注册表 hash 与实际验证结果。
    opt 仅接受 schema 的可选属性；未知键 ValueError（additionalProperties=
    false 的构造侧落地）。critic_status=executed 时必须显式给出
    input_hashes_match / calibration.in_calibrated_range（validate_run
    语义，缺任一在构造期即拒绝）。
    """
    allowed_opt = {"project_id", "profile_id", "snapshot_revision",
                   "input_hashes_match", "calibration", "evidence_refs",
                   "profile_promotion_state", "critic_outcome", "auto_route",
                   "schema_validation"}
    unknown = sorted(set(opt) - allowed_opt)
    if unknown:
        raise ValueError(f"build_run: 未知可选字段 {unknown}（schema "
                         f"additionalProperties=false）")
    run = {
        "schema_version": SCHEMA_VERSION,
        "critic_run_id": critic_run_id,
        "candidate_id": candidate_id,
        "critic_status": critic_status,
        "model": dict(model),
        "input_hashes": dict(input_hashes),
        "advisory_only": ADVISORY_ONLY,
        "schema_validation": opt.get(
            "schema_validation",
            {"valid": True,
             "schema_sha256": schemas.schema_hash(CRITIC_RUN_SCHEMA)}),
        "flags": [dict(f) for f in flags],
    }
    for key in ("project_id", "profile_id", "snapshot_revision",
                "input_hashes_match", "calibration", "evidence_refs",
                "profile_promotion_state", "critic_outcome", "auto_route"):
        if key in opt:
            run[key] = opt[key]
    errs = validate_run(run)
    if errs:
        raise ValueError(f"build_run: critic run 非法（fail-closed）: {errs}")
    return run


def validate_run(run) -> list:
    """schema + 语义验证（[] = 合法）。

    语义（TD4 flags=[] 解释前置）：critic_status=executed 时
    input_hashes_match、model.approved 与 calibration.in_calibrated_range
    必须显式给出（布尔）——缺任一即错误，因为 flags=[] 的解释依赖它们。
    """
    errs = list(schemas.validate(CRITIC_RUN_SCHEMA, run))
    if not isinstance(run, dict):
        return errs
    if run.get("critic_status") == "executed":
        if not isinstance(run.get("input_hashes_match"), bool):
            errs.append("$.input_hashes_match: critic_status=executed 时必须"
                        "显式给出布尔值（flags=[] 的解释依赖它）")
        model = run.get("model")
        if not (isinstance(model, dict)
                and isinstance(model.get("approved"), bool)):
            errs.append("$.model.approved: critic_status=executed 时必须"
                        "显式给出布尔值（flags=[] 的解释依赖它）")
        cal = run.get("calibration")
        if not (isinstance(cal, dict)
                and isinstance(cal.get("in_calibrated_range"), bool)):
            errs.append("$.calibration.in_calibrated_range: "
                        "critic_status=executed 时必须显式给出布尔值"
                        "（flags=[] 的解释依赖它）")
    return errs


# ---------------------------------------------------------------------------
# L2 加旗律：flags 只能追加
# ---------------------------------------------------------------------------

def add_flag(run: dict, category: str, confidence: float,
             location: str | None = None,
             evidence_ref: str | None = None) -> dict:
    """往 run["flags"] 追加一面旗（加旗律：本模块无消旗/降级 API）。

    category 必须属于 FLAG_CATEGORIES；confidence ∈ [0,1]；
    evidence_ref 为 64-hex sha256 或 None；location ≤256 字符。
    追加后整条 run 重新过 schema 验证，非法则回滚并 ValueError
    （不留半变异状）。
    """
    if category not in FLAG_CATEGORIES:
        raise ValueError(f"add_flag: 未知旗标类别 {category!r}"
                         f"（合法集 {FLAG_CATEGORIES}）")
    if (isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
            or not 0.0 <= float(confidence) <= 1.0):
        raise ValueError("add_flag: confidence 必须为 [0,1] 数值")
    flag = {"category": category, "confidence": float(confidence)}
    if location is not None:
        if not isinstance(location, str) or len(location) > 256:
            raise ValueError("add_flag: location 必须为 ≤256 字符字符串")
        flag["location"] = location
    if evidence_ref is not None:
        flag["evidence_ref"] = evidence_ref
    if not isinstance(run, dict):
        raise ValueError("add_flag: run 必须为 dict")
    run.setdefault("flags", []).append(flag)
    errs = schemas.validate(CRITIC_RUN_SCHEMA, run)
    if errs:
        run["flags"].pop()          # 回滚，保持 flags 语义干净
        raise ValueError(f"add_flag: 追加后 run 非法（已回滚）: {errs}")
    return run


# ---------------------------------------------------------------------------
# TD5 路由谓词（严格实现）
# ---------------------------------------------------------------------------

def triage(run, *, judge_gate_pass: bool, required_checkers_executed: bool,
           no_stale_or_unknown: bool, whitelist_item: bool) -> dict:
    """TD5 有限自动分流谓词；结果写入 run["auto_route"] 并返回。

    全部条件为 True（judge_gate_pass 且 required_checkers_executed 且
    no_stale_or_unknown 且 critic_status=executed 且 schema+语义合法且
    input_hashes_match 且 model.approved 且 calibration.in_calibrated_range
    且 flags==[] 且非白名单项）→ {eligible: True,
    status: "queue_deprioritized", failed_conditions: []}。

    任一缺失/错误/低置信/schema 非法 → {eligible: False,
    status: "critic_auto_route_blocked", failed_conditions: [...]}。
    judge_gate_pass=False 或 whitelist_item=True 时在 failed_conditions
    追加 manual_queue_mandatory 注记（Judge fail/白名单绝不能自动分流）。

    注意：queue_deprioritized 只表示人工队列分流，不是质量 pass。
    """
    is_dict = isinstance(run, dict)
    checks = (
        (COND_JUDGE_GATE, judge_gate_pass is True),
        (COND_CHECKERS, required_checkers_executed is True),
        (COND_NO_STALE, no_stale_or_unknown is True),
        (COND_STATUS, is_dict and run.get("critic_status") == "executed"),
        (COND_SCHEMA, is_dict and not validate_run(run)),
        (COND_HASHES, is_dict and run.get("input_hashes_match") is True),
        (COND_MODEL, is_dict and isinstance(run.get("model"), dict)
         and run["model"].get("approved") is True),
        (COND_CALIB, is_dict and isinstance(run.get("calibration"), dict)
         and run["calibration"].get("in_calibrated_range") is True),
        (COND_FLAGS, is_dict and run.get("flags") == []),
        (COND_WHITELIST, whitelist_item is not True),
    )
    failed = [cid for cid, ok in checks if not ok]
    if (judge_gate_pass is not True or whitelist_item is True) \
            and MANUAL_QUEUE_MANDATORY not in failed:
        failed.append(MANUAL_QUEUE_MANDATORY)
    if not failed:
        decision = {"eligible": True, "status": "queue_deprioritized",
                    "failed_conditions": []}
    else:
        decision = {"eligible": False,
                    "status": "critic_auto_route_blocked",
                    "failed_conditions": failed}
    if is_dict:
        run["auto_route"] = decision
    return decision


def flags_empty_semantics(run) -> dict:
    """解释 run 的 flags=[] 是否表示「无旗」。

    means_no_flags 仅当全部前置成立：flags==[] 且 critic_status=executed
    且 schema+语义合法（validate_run=[]）且 input_hashes_match=true 且
    model.approved=true 且 calibration.in_calibrated_range=true。
    任一不成立 → means_no_flags=False（此情形下 critic_outcome 应为
    blocked 并入人工队列），reason 说明缺了哪些前置。
    """
    if not isinstance(run, dict):
        return {"means_no_flags": False, "reason": "run 不是对象，无语义可解释"}
    missing = []
    if run.get("flags") != []:
        missing.append("flags 非空（不存在 flags=[] 语义问题）")
    if run.get("critic_status") != "executed":
        missing.append(f"critic_status={run.get('critic_status')!r}≠executed")
    if validate_run(run):
        missing.append("schema/语义非法")
    if run.get("input_hashes_match") is not True:
        missing.append("input_hashes_match 未确认为 true")
    model = run.get("model")
    if not (isinstance(model, dict) and model.get("approved") is True):
        missing.append("model.approved 未确认为 true")
    cal = run.get("calibration")
    if not (isinstance(cal, dict)
            and cal.get("in_calibrated_range") is True):
        missing.append("calibration.in_calibrated_range 未确认为 true")
    if missing:
        return {"means_no_flags": False,
                "reason": "前置不成立: " + "；".join(missing)}
    return {"means_no_flags": True,
            "reason": "全部前置成立（executed+合法+hash 匹配+模型获批+"
                      "校准域内）: flags=[] 表示无旗"}


# ---------------------------------------------------------------------------
# TD4 晋升门（分层指标门；上岗等级裁决的前置机器门）
# ---------------------------------------------------------------------------

def promotion_gate(evaluation: dict, *,
                   min_samples: int = PROMOTION_MIN_SAMPLES,
                   min_board_recall: float = PROMOTION_MIN_BOARD_RECALL,
                   max_board_fpr: float = PROMOTION_MAX_BOARD_FPR,
                   max_abstain_rate: float = PROMOTION_MAX_ABSTAIN_RATE,
                   max_calibration_error: float =
                   PROMOTION_MAX_CALIBRATION_ERROR,
                   min_worst_board_recall: float =
                   PROMOTION_MIN_WORST_BOARD_RECALL,
                   min_audit_samples: int = PROMOTION_MIN_AUDIT_SAMPLES,
                   min_human_support_rate: float =
                   PROMOTION_MIN_HUMAN_SUPPORT_RATE) -> dict:
    """TD4 晋升门：最低要求全满足才是 candidate。

    evaluation={total_samples, per_board_metrics:[{board_id, precision,
    recall, fpr, fnr}], abstain_rate, calibration_error, worst_board:
    {board_id, recall}, independent_audit:{sample_count, pass},
    human_support_rate}。缺字段按 fail-closed 记为 failed（missing:*）。

    human_support_rate ≥ 阈值只是附加记录：单独不构成晋升，不满足也不
    阻断 candidate。未达门 → not_promoted，继续全量陪审或排序降噪。
    """
    failed: list = []

    def _num(key: str):
        v = evaluation.get(key) if isinstance(evaluation, dict) else None
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return None
        return float(v)

    total = _num("total_samples")
    if total is None:
        failed.append("missing:total_samples")
    elif total < min_samples:
        failed.append("insufficient_samples")

    boards = evaluation.get("per_board_metrics") \
        if isinstance(evaluation, dict) else None
    if not isinstance(boards, list) or not boards:
        failed.append("missing:per_board_metrics")
    else:
        for b in boards:
            bid = b.get("board_id", "?") if isinstance(b, dict) else "?"
            recall = b.get("recall") if isinstance(b, dict) else None
            fpr = b.get("fpr") if isinstance(b, dict) else None
            if (isinstance(recall, bool)
                    or not isinstance(recall, (int, float))):
                failed.append(f"missing:recall:{bid}")
            elif float(recall) < min_board_recall:
                failed.append(f"board_recall_low:{bid}")
            if (isinstance(fpr, bool) or not isinstance(fpr, (int, float))):
                failed.append(f"missing:fpr:{bid}")
            elif float(fpr) > max_board_fpr:
                failed.append(f"board_fpr_high:{bid}")

    abstain = _num("abstain_rate")
    if abstain is None:
        failed.append("missing:abstain_rate")
    elif abstain > max_abstain_rate:
        failed.append("abstain_rate_high")

    calib = _num("calibration_error")
    if calib is None:
        failed.append("missing:calibration_error")
    elif calib > max_calibration_error:
        failed.append("calibration_error_high")

    worst = evaluation.get("worst_board") \
        if isinstance(evaluation, dict) else None
    wrecall = worst.get("recall") \
        if isinstance(worst, dict) else None
    if (isinstance(wrecall, bool)
            or not isinstance(wrecall, (int, float))):
        failed.append("missing:worst_board.recall")
    elif float(wrecall) < min_worst_board_recall:
        failed.append("worst_board_recall_low")

    audit = evaluation.get("independent_audit") \
        if isinstance(evaluation, dict) else None
    if not isinstance(audit, dict):
        failed.append("missing:independent_audit")
    else:
        sc = audit.get("sample_count")
        if (isinstance(sc, bool) or not isinstance(sc, (int, float))
                or sc < min_audit_samples):
            failed.append("audit_samples_insufficient")
        if audit.get("pass") is not True:
            failed.append("audit_not_passed")

    hs = evaluation.get("human_support_rate") \
        if isinstance(evaluation, dict) else None
    hs_ok = (not isinstance(hs, bool) and isinstance(hs, (int, float))
             and float(hs) >= min_human_support_rate)

    if not failed:
        note = ("达到晋升门（candidate）；human_support_rate 仅作附加记录，"
                "单独不构成晋升")
    else:
        note = ("未达晋升门：永远只做全量陪审或排序降噪"
                "（human_support_rate 单独不构成晋升）")
    return {
        "promotion_state": "candidate" if not failed else "not_promoted",
        "failed": failed,
        "thresholds": {
            "min_samples": min_samples,
            "min_board_recall": min_board_recall,
            "max_board_fpr": max_board_fpr,
            "max_abstain_rate": max_abstain_rate,
            "max_calibration_error": max_calibration_error,
            "min_worst_board_recall": min_worst_board_recall,
            "min_audit_samples": min_audit_samples,
            "min_human_support_rate": min_human_support_rate,
        },
        "human_support_rate": hs,
        "human_support_rate_ok": hs_ok,
        "note": note,
    }


# ---------------------------------------------------------------------------
# P2-5/P2-7 逐旗标人工裁定接入（evaluation-protocol-v2 冻结件口径）
# ---------------------------------------------------------------------------

VERDICT_SCHEMA = "critic-flag-verdict-v1"

# P2-7 verdict 封闭集（schemas."critic-flag-verdict-v1" 枚举同步）
VERDICT_VALUES = ("confirmed", "false_positive", "unadjudicated", "uncertain")

# P2-5 三分口径：可判定侧=经人工裁定确认为真报或误报；unadjudicated/
# uncertain 与无裁定记录（pending）不进判断一致率分母的任何一侧
DECIDABLE_VERDICTS = ("confirmed", "false_positive")


def critic_run_record_sha256(run_record: dict) -> str:
    """run 记录体 canonical sha256（与 queue 事件体同一 canonical 约定）。"""
    return hashing.sha256_bytes(hashing.canonical_json_bytes(run_record))


def flag_id(critic_run_id: str, flag_index: int, flag: dict) -> str:
    """确定性派生逐旗标 id：sha256(canonical({critic_run_id, flag_index, flag}))。

    索引参与派生：同 run 内内容完全相同的重复旗标各自拥有独立 id
    （P2-4 重复旗标单列，逐条可裁定）。顺序敏感——裁定记录绑定的
    flag_id 以冻结 run 记录的 flags 数组顺序为准。
    """
    return hashing.sha256_text(hashing.json_dumps(
        {"critic_run_id": critic_run_id, "flag_index": int(flag_index),
         "flag": flag}))


def run_flag_ids(run_record: dict) -> list:
    """run 记录 flags 数组的确定性 flag_id 列表（顺序=数组顺序）。

    run 非 dict 或缺非空 critic_run_id → ValueError（fail-closed）。
    """
    if not isinstance(run_record, dict):
        raise ValueError("run_flag_ids: run 记录必须为 dict")
    cid = run_record.get("critic_run_id")
    if not isinstance(cid, str) or not cid:
        raise ValueError("run_flag_ids: run 记录缺非空 critic_run_id")
    return [flag_id(cid, i, f)
            for i, f in enumerate(run_record.get("flags") or [])]


def flag_verdict_agreement(run_record, verdicts) -> dict:
    """逐旗标判断一致率（P2-7 逐旗标人工裁定的聚合；P2-5 三分口径）。

    输入=单条 critic run 记录 + 绑定该 run 的裁定记录列表；输出含：
    - agreement_rate（判断一致率）=confirmed/（confirmed+false_positive）
      ——分母只取「可判定」旗标（P2-5：未经裁定不得计入任何一侧）；
    - counts：三分计数 confirmed / unadjudicated_or_pending /
      false_positive（uncertain 归入 unadjudicated-or-pending 桶，
      verdict_breakdown 保留四值+pending 明细）。

    fail-closed（ValueError 拒算，不产出部分结果）：
    - run 非 dict / verdicts 非列表；
    - 裁定记录未过 schemas."critic-flag-verdict-v1"（形状/枚举/格式）；
    - 缺 critic_run_record_sha256（provenance 绑定缺失——schema 层可选、
      本聚合语义强制）或与 run 记录体实测 canonical sha256 不符；
    - 裁定的 critic_run_id 与 run 记录不符（run 错配）；
    - flag_id 不在本 run 派生 id 集内（未知 flag_id）；
    - 同一 flag_id 重复裁定（裁定冲突）。

    verdicts 为 None/空列表 → not_available 语义（rate=None+reason，
    不编造数值）；可判定分母为 0（全部 unadjudicated/uncertain/pending）
    同样 not_available。本函数是质量观察，不是晋升门：一致率单独不构成
    TL-2 晋升或自动分流证据（SPEC §4/TD5 十条件合取照旧）。
    """
    if not isinstance(run_record, dict):
        raise ValueError("flag_verdict_agreement: run 记录必须为 dict")
    if verdicts is None:
        verdicts = []
    if not isinstance(verdicts, list):
        raise ValueError("flag_verdict_agreement: verdicts 必须为列表")
    cid = run_record.get("critic_run_id")
    ids = run_flag_ids(run_record)
    id_set = set(ids)
    record_sha = critic_run_record_sha256(run_record)
    breakdown = {"confirmed": 0, "false_positive": 0,
                 "unadjudicated": 0, "uncertain": 0}
    seen: set = set()
    for v in verdicts:
        vid = v.get("verdict_record_id", "?") if isinstance(v, dict) else "?"
        if not isinstance(v, dict):
            raise ValueError("flag_verdict_agreement: 裁定记录必须为 dict")
        errs = schemas.validate(VERDICT_SCHEMA, v)
        if errs:
            raise ValueError(f"flag_verdict_agreement: 裁定记录 {vid!r} "
                             f"schema 非法（fail-closed）: {errs}")
        if v["critic_run_id"] != cid:
            raise ValueError(
                f"flag_verdict_agreement: 裁定记录 {vid!r} run 错配"
                f"（裁定绑定 {v['critic_run_id']!r}≠run 记录 {cid!r}）")
        bound = v.get("critic_run_record_sha256")
        if not isinstance(bound, str) or not bound:
            raise ValueError(
                f"flag_verdict_agreement: 裁定记录 {vid!r} 缺 "
                f"critic_run_record_sha256（provenance 绑定缺失，拒算）")
        if bound != record_sha:
            raise ValueError(
                f"flag_verdict_agreement: 裁定记录 {vid!r} 的 "
                f"critic_run_record_sha256 与 run 记录体实测 hash 不符"
                f"（provenance 绑定失效，拒算）")
        if v["flag_id"] not in id_set:
            raise ValueError(
                f"flag_verdict_agreement: 裁定记录 {vid!r} 引用未知 "
                f"flag_id {v['flag_id'][:12]}…（不在本 run 派生集内，拒算）")
        if v["flag_id"] in seen:
            raise ValueError(
                f"flag_verdict_agreement: flag_id {v['flag_id'][:12]}… "
                f"重复裁定（裁定冲突，拒算）")
        seen.add(v["flag_id"])
        breakdown[v["verdict"]] += 1
    pending = len(ids) - len(seen)
    confirmed = breakdown["confirmed"]
    false_positive = breakdown["false_positive"]
    undecidable = breakdown["unadjudicated"] + breakdown["uncertain"]
    base = {
        "run_id": cid,
        "schema": VERDICT_SCHEMA,
        "flags_total": len(ids),
        "verdicts_total": len(verdicts),
        "adjudicated_flag_count": len(seen),
        "pending_flag_count": pending,
        "counts": {
            "confirmed": confirmed,
            "false_positive": false_positive,
            "unadjudicated_or_pending": undecidable + pending,
        },
        "verdict_breakdown": dict(sorted(
            {**breakdown, "no_verdict_record": pending}.items())),
        "denominator_basis": ("confirmed+false_positive（P2-5 三分口径："
                              "unadjudicated/uncertain/无裁定不进分母"
                              "任何一侧）"),
    }
    if not verdicts:
        return {**base, "status": "not_available",
                "agreement_rate": None, "numerator": None,
                "denominator": 0,
                "reason": ("not_available: 裁定记录列表为空——无逐旗标人工"
                           "裁定，不编造数值（P2-7：无裁定的旗标保持 "
                           "pending）")}
    denominator = confirmed + false_positive
    if denominator == 0:
        return {**base, "status": "not_available",
                "agreement_rate": None, "numerator": None,
                "denominator": 0,
                "reason": ("not_available: 可判定旗标（confirmed/"
                           "false_positive）为 0——全部裁定为 unadjudicated/"
                           "uncertain 或 pending，不编造数值")}
    return {**base, "status": "value",
            "agreement_rate": confirmed / denominator,
            "numerator": confirmed, "denominator": denominator,
            "note": ("判断一致率=confirmed/（confirmed+false_positive）；"
                     "三分计数对齐 P2-5（confirmed/unadjudicated-or-pending/"
                     "false_positive）；仅质量观察，单独不构成晋升或自动"
                     "分流证据（SPEC §4/TD5）")}


# ---------------------------------------------------------------------------
# P2-7 投影位接入（判断一致率 × 逐旗标裁定；health_projection 零改动）
# ---------------------------------------------------------------------------
# 装配事实（为何接入不在 health_projection.py 本体）：s23 编排把
# sha256(pcbflow/health_projection.py) 作为 evaluator_code_sha256 织入
# out/v3-tl6/health-projection-v3.json 冻结件，且
# tests/test_p1c_projection_v3.py::test_real_out_four_artifacts_and_frozen_
# unchanged 以「同参重建==盘上件」对账；out/ 全只读、冻结件不可再生成，
# 该文件任何字节改动都会破坏对账。故接入以本包装函数承载：hp 本体继续
# 承载无裁定 not_available 路径（输出零变化），本函数在裁定在案时以同一
# 记录形状产出实值投影（复用 hp 指标基座的全部描述字段与 aux 家族）。

_VERDICT_DATASET = ("critic-run-record + 逐旗标人工正确性 verdict"
                    "（critic-flag-verdict-v1，本轮在案）")


def project_judgment_agreement_with_verdicts(
        critic_runs, queue_events, *, record_evidence,
        calibration_observation, flag_verdicts,
        revision: str | None = None, baseline=None,
        baseline_basis=None) -> dict:
    """判断一致率投影位接入：裁定在案 → 实值；不在案 → 原样委托。

    flag_verdicts 为 None/空列表 → 输出与
    health_projection.project_critic_judgment_agreement 同参调用
    canonical byte 等价（零变化通道）。

    flag_verdicts 非空 → 先取同参基座记录，再执行本层 fail-closed 校验
    （任一不过 → blocked，不产出部分数值）：
    - 每条裁定过 schemas."critic-flag-verdict-v1"；
    - 裁定 critic_run_id 落在本投影窗口 run 集内（run 错配拒算）；
    - 裁定 critic_run_record_sha256 与 record_evidence 中同 run 记录
      实测 hash 对账（该 run 无证据指针或对账不符 → blocked；P2-9
      缺证即 blocked）；
    - verdict_record_id 与（critic_run_id, flag_id）均唯一（重复裁定
      =裁定冲突，拒算）。

    聚合口径=confirmed/（confirmed+false_positive）（P2-5 三分：未经
    裁定不进分母任何一侧）；可判定分母 0 → not_available（不编造数值）。
    flag_id 对 run flags 数组的成员性复核与 pending 计数=run 级职责
    （flag_verdict_agreement，输入原始 run 记录时执行）；本投影层消费
    wrapper 记录（无 flags 数组），aux 如实声明此边界。
    """
    base = health_projection.project_critic_judgment_agreement(
        critic_runs, queue_events, record_evidence=record_evidence,
        calibration_observation=calibration_observation,
        revision=revision or health_projection.PROJECTION_REVISION_V3,
        baseline=baseline, baseline_basis=baseline_basis)
    if not flag_verdicts:
        return base

    def _blocked(reason: str) -> dict:
        base["status"] = health_projection.STATUS_BLOCKED
        base["reason"] = reason
        return base

    if not isinstance(flag_verdicts, list):
        return _blocked("trust_invalid: flag_verdicts 必须为裁定记录列表")
    run_ids = {r["run_id"] for r in critic_runs if isinstance(r, dict)}
    evidence_sha_by_run = {}
    for e in record_evidence:
        if (isinstance(e, dict) and e.get("run_id") in run_ids
                and isinstance(e.get("sha256"), str)):
            evidence_sha_by_run[e["run_id"]] = e["sha256"]
    seen_record_ids: set = set()
    seen_flags: set = set()
    breakdown = {"confirmed": 0, "false_positive": 0,
                 "unadjudicated": 0, "uncertain": 0}
    per_run: dict = {}
    for v in flag_verdicts:
        vid = v.get("verdict_record_id", "?") if isinstance(v, dict) else "?"
        errs = (schemas.validate(VERDICT_SCHEMA, v)
                if isinstance(v, dict) else ["$: 裁定记录非 dict"])
        if errs:
            return _blocked(f"trust_invalid: 逐旗标裁定记录 {vid!r} "
                            f"schema 非法 {errs}")
        rid = v["critic_run_id"]
        if rid not in run_ids:
            return _blocked(
                f"trust_invalid: 逐旗标裁定记录 {vid!r} run 错配"
                f"（critic_run_id={rid!r} 不在本投影窗口 {sorted(run_ids)}"
                f" 内，拒算）")
        if rid not in evidence_sha_by_run:
            return _blocked(
                f"trust_invalid: 逐旗标裁定记录 {vid!r} 绑定 run {rid!r} "
                f"无 record_evidence 证据指针（P2-9 缺证即 blocked，拒算）")
        if v.get("critic_run_record_sha256") != evidence_sha_by_run[rid]:
            return _blocked(
                f"trust_invalid: 逐旗标裁定记录 {vid!r} 的 "
                f"critic_run_record_sha256 与 record_evidence 实测值不符"
                f"（provenance 对账失败，拒算）")
        if vid in seen_record_ids:
            return _blocked(f"trust_invalid: verdict_record_id {vid!r} "
                            f"重复（裁定冲突，拒算）")
        seen_record_ids.add(vid)
        if (rid, v["flag_id"]) in seen_flags:
            return _blocked(
                f"trust_invalid: 裁定记录 {vid!r} 对 flag_id "
                f"{v['flag_id'][:12]}… 重复裁定（裁定冲突，拒算）")
        seen_flags.add((rid, v["flag_id"]))
        breakdown[v["verdict"]] += 1
        slot = per_run.setdefault(rid, {"confirmed": 0, "false_positive": 0,
                                        "undecidable": 0, "verdicts": 0})
        slot["verdicts"] += 1
        if v["verdict"] in DECIDABLE_VERDICTS:
            slot[v["verdict"]] += 1
        else:
            slot["undecidable"] += 1
    confirmed = breakdown["confirmed"]
    false_positive = breakdown["false_positive"]
    undecidable = breakdown["unadjudicated"] + breakdown["uncertain"]
    denominator = confirmed + false_positive
    base["dataset"] = _VERDICT_DATASET
    aux = dict(base["aux"])
    aux["verdict_intake"] = {
        "schema": VERDICT_SCHEMA,
        "verdict_records_total": len(flag_verdicts),
        "adjudicated_flag_count": len(seen_flags),
        "confirmed": confirmed,
        "false_positive": false_positive,
        "unadjudicated": breakdown["unadjudicated"],
        "uncertain": breakdown["uncertain"],
        "counts_p2_5": {
            "confirmed": confirmed,
            "false_positive": false_positive,
            "unadjudicated_or_pending": undecidable,
        },
        "per_run": dict(sorted(per_run.items())),
        "runs_with_verdict_records": sorted(per_run),
        "denominator_basis": ("confirmed+false_positive（P2-5 三分口径："
                              "未经裁定不进分母任何一侧）"),
        "note": ("判断一致率实值只覆盖已裁定旗标（P2-7：无裁定保持 "
                 "pending，不计入分母）；flag_id 对 run flags 数组的成员"
                 "性复核与 pending 计数=run 级职责"
                 "（pcbflow.critic.flag_verdict_agreement）；本指标仍只是"
                 "质量观察，单独不构成晋升或自动分流证据（SPEC §4/TD5 "
                 "十条件合取照旧）"),
    }
    base["aux"] = aux
    if denominator == 0:
        base["status"] = health_projection.STATUS_NOT_AVAILABLE
        base["denominator"] = 0
        base["reason"] = (
            "not_available: 裁定记录在案但可判定旗标（confirmed/"
            "false_positive）为 0——全部裁定为 unadjudicated/uncertain"
            "（P2-5 三分口径：不计入任何一侧），不编造数值")
        return base
    base["status"] = health_projection.STATUS_VALUE
    base["numerator"] = confirmed
    base["denominator"] = denominator
    base["value"] = confirmed / denominator
    return base


# ---------------------------------------------------------------------------
# schema 偏差说明（不修改 schemas.py；报告侧补丁建议）
# ---------------------------------------------------------------------------
# critic_run_record.auto_route.status 枚举为
# [queue_deprioritized, manual_queue, critic_auto_route_blocked]，不含
# manual_queue_mandatory，且 auto_route additionalProperties=false——
# 强制人工注记只能以条件 id 形式附在 failed_conditions（本实现做法）。
# 建议后续给 auto_route 增加 enum 值 "manual_queue_mandatory" 或独立
# mandatory 布尔字段；另建议 critic_outcome 的推导规则
# （flags_empty_semantics=False 或 triage 不 eligible ⇒ blocked）写入
# schema 描述。
