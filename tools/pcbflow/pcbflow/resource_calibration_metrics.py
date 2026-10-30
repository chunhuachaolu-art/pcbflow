"""前馈资源需求校准指标计算器（PREREG-RESOURCE-CALIBRATION-R1 冻结版；纯函数、零 IO）。

指标计算批=冻结后首个授权动作（冻结版 §6.2；P-RC-1 冻结版口径：本模块产出的
指标数值全部产生于冻结之后）。本模块逐字面实现冻结文本 §0/§1 指标族：

- **M1 校准误差分位**（每资源类；行级池与板级池**双口径并列**，均描述性、
  不定主判据口径——Q2 裁定）：类内可测行池 |e(R)| 的 P50/P90/P95；
  板级池=先板内聚合（板内 median|e|，type-7）再对板值取分位，板等权，
  板内行数 < M4 门槛的板不参评。
- **M2 欠测尾部分位**（同双口径）：可测行池 signed e(R) 的 P95，正值=欠测
  方向尾部幅度；板级池=板内 median(signed e) 后板间 P95。
- **M2b 欠测率**（描述性辅助，**不进门**——Q6/RC-6）：#(e>0)/#可测行。
- **M3 worst-board**：板级聚合=板内 median|e|（type-7，Q3 裁定）；argmax 板
  报告 {board_id, 板内中位|e|, n 行}；并列时 board_id 字典序取首（防 tie 漂移）；
  板内行数 < M4 门槛的板不参评。
- **M4 分母护栏**：n=0 → ``not_available``（沿 D-OBS-6）；0<n<5 →
  ``not_enough_data``（如实报 n，不外推）；n≥5 才产出 M1/M2/M3 数值（Q7：
  门槛=5 固定，不做类内自适应）。
- **附属 rails/padload 忠实性核对**（Q6 裁定：纯描述性、不挂门，不入
  M1–M3）：同款分位/欠测率描述统计，输出标注 auxiliary 语义。

残差定义（§0.2/§0.3）：``E(R) = actual(R) − predicted(R)``；
``e(R) = E(R) / actual(R)``（分母=actual）；``E(R) > 0`` = underprediction。
可测行池=prediction 非空 ∧ actual 非空 ∧ unit 一致；**actual=0 或不可测 →
该行不入任何指标分母**，进台账（§0.3，禁止换算硬并）。单位护栏（§0.4）：
unit 不一致行剔除并登记，不做跨单位聚合。

分位法一律 **type-7 线性插值**（冻结版 §1；自实现、不依赖 numpy，浮动
运算序确定）。**P-RC-6 计算器资格**：本模块须先通过最小数值自检（分位/
中位数与手算样例对账、byte-exact 重放）方可产出正式报告；自检件与报告
同批落盘（见 tests/test_resource_calibration_metrics.py 与 metrics-r1/
自检件）。

输入=observation 行 dict（schema=pcbflow.schemas "observation-row-v1"），
经批处理编排层读盘对账后传入。本模块零文件 IO、零子进程、零网络、
零 wall-clock、零随机；同输入 ⇒ byte-exact 同输出（测试强制）。
生成器模式（hashing.py 同款）：.py 不写文件，产物在内存构建，由批处理
脚本 canonical 落盘。
"""

from __future__ import annotations

import math

MODULE_NAME = "pcbflow.resource_calibration_metrics"

#: 指标族版本标识（绑定预注册版本；修订=新预注册版本文件=本模块新版本）
PREREG_ID = "resource-calibration-r1"
METRICS_VERSION = "resource-calibration-metrics-r1"

#: 六类资源（SPEC.md §6.2 L502–509 原序；冻结版 §0.1）
SIX_KINDS = (
    "escape_slots",
    "corridor",
    "layer_capacity",
    "bus_lane",
    "via_budget",
    "power_return_space",
)

#: 附属核对行种（rails pad 账本 + signal_layer_pad_load 逐层 pad 账本；
#: Q6：纯描述性不挂门，不入 M1–M3）
AUXILIARY_KINDS = ("rails", "signal_layer_pad_load")

#: M4 分母护栏门槛（冻结版 §1 M4 行；Q7 裁定=5 固定，不做类内自适应）
M4_MIN_ROWS = 5

#: 板级池参评门槛（冻结版 §1 M1/M2/M3 板级行：板内行数 < M4 门槛的板不参评；
#: 与 M4 同值，Q7 执行注记）
MIN_BOARD_ROWS = M4_MIN_ROWS

#: M1/M2 行级池分位点；板级池 M1 取同三点、M2 取 0.95
QUANTILES_M1 = (0.50, 0.90, 0.95)
QUANTILE_M2 = 0.95

#: M4 状态枚举（冻结版 §1 M4 行字面）
STATUS_OK = "ok"
STATUS_NOT_AVAILABLE = "not_available"
STATUS_NOT_ENOUGH_DATA = "not_enough_data"

# ---------------------------------------------------------------------------
# 基础统计原语（type-7；纯 float 运算，运算序固定）
# ---------------------------------------------------------------------------


def quantile_type7(values, q):
    """type-7 线性插值分位（冻结版 §1：numpy/pandas 默认 ``linear``）。

    h = (n−1)·q；结果 = x[⌊h⌋] + (h−⌊h⌋)·(x[⌊h⌋+1] − x[⌊h⌋])（升序）。
    空输入与非有限值 → ValueError（fail-closed，上游须先过护栏）。
    """
    if not values:
        raise ValueError("quantile_type7: empty values")
    xs = sorted(float(v) for v in values)
    for v in xs:
        if not math.isfinite(v):
            raise ValueError("quantile_type7: non-finite value")
    n = len(xs)
    h = (n - 1) * q
    lo = int(math.floor(h))
    hi = min(lo + 1, n - 1)
    frac = h - lo
    return xs[lo] + frac * (xs[hi] - xs[lo])


def median_type7(values):
    """中位数=type-7 P50（冻结版 §1 分位法统一 type-7）。"""
    return quantile_type7(values, 0.5)


# ---------------------------------------------------------------------------
# 行分类与可测行池（§0.3/§0.4 护栏；fail-closed）
# ---------------------------------------------------------------------------


def row_kind(row):
    """行种=observation_id 载荷的 row_id 前缀（``kind:object``）。"""
    row_id = row["row_id"]
    if ":" not in row_id:
        raise ValueError("row_kind: row_id lacks kind prefix: %r" % (row_id,))
    return row_id.split(":", 1)[0]


def board_id_of(row):
    """板标识=split.board_id（M3/板级池聚合单元）。"""
    return row["split"]["board_id"]


def _finite_number(value):
    """非布尔有限数判定（JSON 数值域；bool 是 int 子类须排除）。"""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(float(value))


def classify_row(row):
    """单行分类（冻结版 §0.3/§0.4 护栏，逐行归因，禁止静默丢弃）。

    返回 ``(status, detail)``；status ∈：
    - ``measurable``      —— 入可测行池（pred/actual 均有有限值 ∧ 均有
      非空 unit 字符串 ∧ unit 相等 ∧ actual ≠ 0）
    - ``prediction_null`` —— prediction.value 缺/null（blocked/actual-only/
      零封装诚实 null 等台账行）
    - ``actual_null``     —— actual.value 缺/null（fail-closed 转记/类语义
      缺/粒度不齐等台账行，D-OBS-6）
    - ``actual_zero``     —— actual=0：E 有定义但 e 分母=0 → 不入任何指标
      分母（§0.3），进台账
    - ``unit_mismatch``   —— 两侧均有值但 unit 不一致/一侧缺 unit → 剔除并
      登记（§0.4 单位护栏）
    detail 携带逐行归因键（observation_id/board_id/kind/reason）。
    """
    kind = row_kind(row)
    common = {
        "observation_id": row.get("observation_id"),
        "board_id": board_id_of(row),
        "kind": kind,
    }
    prediction = row.get("prediction") or {}
    actual = row.get("actual") or {}
    p_val = prediction.get("value")
    a_val = actual.get("value")
    p_unit = prediction.get("unit")
    a_unit = actual.get("unit")

    if not _finite_number(p_val):
        return ("prediction_null", dict(
            common, reason=prediction.get("not_available_reason") or "prediction.value null"))
    if not _finite_number(a_val):
        return ("actual_null", dict(
            common, reason=actual.get("not_available_reason") or "actual.value null"))

    # 单位护栏（§0.4）：两侧均有值时 unit 须两侧非空且相等
    if not (isinstance(p_unit, str) and p_unit) or not (isinstance(a_unit, str) and a_unit) \
            or p_unit != a_unit:
        return ("unit_mismatch", dict(
            common, predicted_unit=p_unit, actual_unit=a_unit,
            reason="unit missing or mismatch (§0.4 单位护栏剔除登记)"))

    if float(a_val) == 0.0:
        return ("actual_zero", dict(
            common, predicted_value=float(p_val),
            reason="actual=0 → e 分母为零，不入任何指标分母（§0.3）"))

    e = (float(a_val) - float(p_val)) / float(a_val)
    return ("measurable", dict(
        common,
        predicted_value=float(p_val),
        actual_value=float(a_val),
        unit=p_unit,
        residual=float(a_val) - float(p_val),
        relative_residual=e + 0.0,  # 规范化 −0.0 → 0.0
    ))


def classify_rows(rows):
    """批量分类：返回 ``(measurable, excluded)``。

    measurable=可测行记录 list（classify_row 的 ``measurable`` detail，按
    (board_id, observation_id) 典序稳定排序——输入顺序不敏感，同输入
    byte-exact）；excluded=其余四类 detail list（同序）。
    """
    measurable = []
    excluded = []
    for row in rows:
        status, detail = classify_row(row)
        if status == "measurable":
            measurable.append(detail)
        else:
            excluded.append(dict(detail, status=status))
    key = lambda d: (d["board_id"], d["observation_id"] or "")
    measurable.sort(key=key)
    excluded.sort(key=key)
    return measurable, excluded


def group_by_board(measurable):
    """按 board_id 分组（板级池/M3 聚合单元；返回 dict 值按 key 典序）。"""
    boards = {}
    for rec in measurable:
        boards.setdefault(rec["board_id"], []).append(rec)
    return {b: boards[b] for b in sorted(boards)}


# ---------------------------------------------------------------------------
# M4 门控与 M1/M2/M2b/M3（冻结版 §1 逐字面）
# ---------------------------------------------------------------------------


def m4_status(n):
    """M4 分母护栏状态（n=0 → not_available；0<n<5 → not_enough_data；n≥5 → ok）。"""
    if n == 0:
        return STATUS_NOT_AVAILABLE
    if n < M4_MIN_ROWS:
        return STATUS_NOT_ENOUGH_DATA
    return STATUS_OK


def board_medians(measurable, signed):
    """逐板板内聚合（板级池/M3 同源）：板内 median(|e|) 或 median(signed e)。

    返回 list[(board_id, 板内行数, 板内中位值)]，按 board_id 典序。
    """
    out = []
    for board_id, recs in group_by_board(measurable).items():
        vals = [r["relative_residual"] for r in recs]
        if signed:
            agg = median_type7(vals)
        else:
            agg = median_type7([abs(v) for v in vals])
        out.append((board_id, len(recs), agg + 0.0))
    return out


def m1_row_pool(measurable):
    """M1 行级池：类内可测行池 |e| 的 P50/P90/P95（板不加权，行独立入池）。"""
    abs_e = [abs(r["relative_residual"]) for r in measurable]
    return {
        "p50": quantile_type7(abs_e, QUANTILES_M1[0]),
        "p90": quantile_type7(abs_e, QUANTILES_M1[1]),
        "p95": quantile_type7(abs_e, QUANTILES_M1[2]),
    }


def m1_board_pool(measurable):
    """M1 板级池：板内 median|e|（板行数≥门槛参评，板等权）后板间 P50/P90/P95。

    无参评板（所有板板内行数 < MIN_BOARD_ROWS）→ 按 Q7 执行注记报
    ``not_enough_data``（不产出任何分位数值）。
    """
    eligible = [(b, n, v) for (b, n, v) in board_medians(measurable, signed=False)
                if n >= MIN_BOARD_ROWS]
    vals = [v for (_, _, v) in eligible]
    out = {"eligible_boards": [
        {"board_id": b, "n_rows": n, "board_median_abs_e": v}
        for (b, n, v) in eligible]}
    if not vals:
        out["status"] = STATUS_NOT_ENOUGH_DATA
        return out
    out["p50"] = quantile_type7(vals, QUANTILES_M1[0])
    out["p90"] = quantile_type7(vals, QUANTILES_M1[1])
    out["p95"] = quantile_type7(vals, QUANTILES_M1[2])
    return out


def m2_row_pool(measurable):
    """M2 行级池：signed e 的 P95（正值=欠测方向尾部幅度；与 M1 分列不合并）。"""
    e = [r["relative_residual"] for r in measurable]
    return {"p95": quantile_type7(e, QUANTILE_M2)}


def m2_board_pool(measurable):
    """M2 板级池：板内 median(signed e)（板行数≥门槛）后板间 P95。

    无参评板 → 同 m1_board_pool 口径报 ``not_enough_data``。
    """
    eligible = [(b, n, v) for (b, n, v) in board_medians(measurable, signed=True)
                if n >= MIN_BOARD_ROWS]
    vals = [v for (_, _, v) in eligible]
    out = {"eligible_boards": [
        {"board_id": b, "n_rows": n, "board_median_signed_e": v}
        for (b, n, v) in eligible]}
    if not vals:
        out["status"] = STATUS_NOT_ENOUGH_DATA
        return out
    out["p95"] = quantile_type7(vals, QUANTILE_M2)
    return out


def m2b_rate(measurable):
    """M2b 欠测率（描述性辅助，不进门）：#(e>0)/#可测行。"""
    n = len(measurable)
    under = sum(1 for r in measurable if r["relative_residual"] > 0.0)
    return {"n_underprediction": under, "n_measurable": n, "rate": under / n}


def m3_worst_board(measurable):
    """M3 worst-board：argmax 板内 median|e|；并列 board_id 字典序取首。

    仅板内行数 ≥ MIN_BOARD_ROWS 的板参评（与 M1/M2 板级池参评口径一致）；
    无参评板 → None（上游按 M4/not_enough_data 口径报告）。
    """
    best = None
    for board_id, n, agg in board_medians(measurable, signed=False):
        if n < MIN_BOARD_ROWS:
            continue
        # 并列（精确相等）取 board_id 字典序更小者；board_medians 已按典序
        # 迭代，故严格大于才替换 → 并列时自然保留字典序首位。
        if best is None or agg > best[2]:
            best = (board_id, n, agg)
    if best is None:
        return None
    return {"board_id": best[0], "n_rows": best[1], "board_median_abs_e": best[2]}


def compute_metrics(measurable):
    """对**已过 M4 门控**（n≥5）的可测行池产出 M1/M2/M2b/M3 全套（双口径）。"""
    return {
        "n_measurable": len(measurable),
        "m1_row_pool": m1_row_pool(measurable),
        "m1_board_pool": m1_board_pool(measurable),
        "m2_row_pool": m2_row_pool(measurable),
        "m2_board_pool": m2_board_pool(measurable),
        "m2b": m2b_rate(measurable),
        "m3_worst_board": m3_worst_board(measurable),
    }


# ---------------------------------------------------------------------------
# 类池门控报告（六类主指标 / 附属核对共用的编排入口）
# ---------------------------------------------------------------------------


def ledger_summary(excluded):
    """排除行按（状态 × 原因）聚合（P-RC-4「逐类逐因登记」口径）。

    六类大池（如 escape_slots 19705 行）逐行全文会使台账失焦；本函数给出
    ``(status, reason) → n`` 聚合，按 (status, reason) 典序。逐行明细仅对
    小池（附属 rails/padload 核对）保留（describe_pool ``exclude_detail``）。
    """
    agg = {}
    for rec in excluded:
        key = (rec["status"], rec["reason"])
        agg[key] = agg.get(key, 0) + 1
    return [{"status": s, "reason": r, "n": n}
            for (s, r), n in sorted(agg.items())]


def board_null_detail(excluded, kind, status="actual_null"):
    """指定行种排除行的逐板计数明细（fail-closed 影响面对账用）。"""
    agg = {}
    for rec in excluded:
        if rec["kind"] == kind and rec["status"] == status:
            agg[rec["board_id"]] = agg.get(rec["board_id"], 0) + 1
    return {b: agg[b] for b in sorted(agg)}


def describe_pool(rows, resource_kind=None, auxiliary=False, exclude_detail=False):
    """一类×一池的完整门控报告（冻结版 §1/M4 逐字面；编排层逐类逐池调用）。

    rows=该池该类全部行（**不删行**——所有行都进分类台账）；resource_kind=
    六类类名或附属行种名（None=不校验行种一致性）；auxiliary=True 时输出
    标注附属核对语义（Q6：纯描述性、不挂门、不入 M1–M3）。

    返回 dict：
    - n_rows_total：该池该类全部行数（分母完整性核对用）
    - ledger_counts：{prediction_null, actual_null, actual_zero, unit_mismatch,
      measurable} 逐因计数（P-RC-4 如实登记）
    - excluded_summary：排除行按（状态 × 原因）聚合（逐类逐因登记）；
      excluded_detail=逐行归因明细（仅 exclude_detail=True 时，供小池）
    - n_measurable / m4_status / 六类：not_available/not_enough_data 时
      **不出任何 M 数值**（M4 字面）；n≥5 时 metrics=compute_metrics 全套。
    - auxiliary 核对：同样受 M4 门控，出数时 metrics 键名相同，note 声明
      附属语义。
    """
    measurable, excluded = classify_rows(rows)
    ledger_counts = {
        "prediction_null": 0,
        "actual_null": 0,
        "actual_zero": 0,
        "unit_mismatch": 0,
    }
    for rec in excluded:
        ledger_counts[rec["status"]] += 1
    kinds = sorted({row_kind(r) for r in rows}) if rows else (
        [resource_kind] if resource_kind else [])
    if resource_kind is not None and kinds not in ([resource_kind], []):
        raise ValueError(
            "describe_pool: mixed kinds %r in pool declared %r" % (kinds, resource_kind))

    n = len(measurable)
    status = m4_status(n)
    out = {
        "resource_kind": resource_kind,
        "n_rows_total": len(rows),
        "ledger_counts": ledger_counts,
        "excluded_summary": ledger_summary(excluded),
        "n_measurable": n,
        "m4_status": status,
    }
    if exclude_detail:
        out["excluded_detail"] = excluded
    if status == STATUS_OK:
        out["metrics"] = compute_metrics(measurable)
    if auxiliary:
        out["note"] = ("附属账本忠实性核对：纯描述性、不挂门、不入 M1–M3"
                       "（冻结版 §2 附属行/Q6 裁定/RC-6）")
    return out


def ledger_of_pool(rows):
    """池级台账（跨类汇总用）：全行分类计数与逐行明细（P-RC-4 如实登记）。"""
    measurable, excluded = classify_rows(rows)
    counts = {k: 0 for k in ("prediction_null", "actual_null", "actual_zero",
                             "unit_mismatch")}
    for rec in excluded:
        counts[rec["status"]] += 1
    return {
        "n_rows_total": len(rows),
        "n_measurable": len(measurable),
        "ledger_counts": counts,
        "excluded": excluded,
        "measurable": measurable,
    }
