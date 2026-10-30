"""pcbflow.v4_1.plannerseat -- E5 planner 排序位/投影消融 harness（堵 K5+K6）。

模型撤出几何提案位、坐排序/分解/拥塞诊断位：本模块承载 E5 三门的确定性
harness（planner 恒 untrusted；评估腿与 planner 会话零共享中间态）：

* 排序位（G5.2）：exact optimum 12 场景全集上，模型排序 M（盲读投影）
  vs 稳定序 S（字典序）vs 先例臂 A1（几何局部搜索），对照 OPT
  （冻结 optimum 件只读，hash 对照 E0 基线 fail-closed）；
* 投影消融（G5.1）：manifest 直读投影输入（E5-PROJ）vs 先例 C1 SVG 帧
  输入（E5-SVG）的 planner patch 合法率配对对照，二轮反馈环=一轮
  validator 拒绝原因结构化回流；
* 预算纪律（G5.3）：token 计数与硬停——任一 session 超 200k 或全套累计
  超 7M → 该场景标 blocked 不出数（此行为本身为被测对象）。

validator 语义只读复用先例冻结件：cmp_patch.validate_patch（提案级
合法性/拒绝原因）、cmp_inputs.build_input（SVG 臂输入格式）、
cmp_localsearch.run_local_search（A1 先例臂）、cmp_stats（配对统计）。
v4exp/ 零改动；零子进程、零网络、零 wall-clock（日期=声明常量）。
"""

from __future__ import annotations

import copy
import hashlib
import json
import os

from ..v4exp import cmp_inputs, cmp_localsearch, cmp_patch, cmp_stats, model, router
from ..v4exp.grid import GridWorld
from . import projection as projection_mod
from .canonical import write_canonical_json

DECLARED_DATE = "2026-09-12"

ORDERING_INPUT_SCHEMA = "pcbflow.v4_1.e5.ordering-input/1"
ORDERING_RESPONSE_SCHEMA = "pcbflow.v4_1.ordering-response/1"
ABLATION_PROJ_INPUT_SCHEMA = "pcbflow.v4_1.e5.ablation-input/1"
ORDERING_CAPTURE_SCHEMA = "pcbflow.v4_1.e5.ordering-capture/1"
ABLATION_EVAL_SCHEMA = "pcbflow.v4_1.e5.projection-ablation/1"
LEDGER_SCHEMA = "pcbflow.v4_1.e5.token-ledger/1"

E5_ARMS = ("E5-PROJ", "E5-SVG")
RESPONSE_SCHEMA = cmp_patch.RESPONSE_SCHEMA  # 先例 schema 原样
RESPONSE_ROOT_KEYS = cmp_patch.RESPONSE_ROOT_KEYS
MAX_PATCHES_PER_CALL = cmp_patch.MAX_PATCHES_PER_CALL
MAX_PROPOSALS = 8  # 与先例 A1 同预算（2 轮 × 4）

BOOTSTRAP_SEED = "e5-bootstrap-20260912-v1"
BOOTSTRAP_RESAMPLES = 10000

CHARS_PER_TOKEN = 4
SESSION_CEILING_TOKENS = 200000
SUITE_CEILING_TOKENS = 7000000

ORDERING_TASK_TEXT = """你是 PCB 布线顺序规划器（受限角色）。输入是一块未布线 PCB 的结构化投影（JSON；坐标=板 mm，原点左下，y 正向下，零换算）。
任务：为顺序式布线器选择 net 布线顺序。布线器按 route_order 逐网布线：先布的网走最短路径占据走廊，后布的网须绕开已布几何（绕行增加长度与弯折）；跨层经 via，via 固定成本 8mm；目标函数=总长度(mm)+0.5*弯折数+8*via 数（越小越好）。
输出一个 JSON 对象（不要 markdown、不要多余字段）：
{"schema": "pcbflow.v4_1.ordering-response/1", "scenario_id": <投影中的 scenario_id>, "route_order": [<全部 net_id 恰各一次>], "notes": "<推理摘要，≤200字符>", "uncertainty": "low|medium|high"}
只依据投影内容决策；不确定时仍必须给出完整排列。"""

PROJ_CONTRACT_TEXT = """你是受限局部布线规划器。输出一个 JSON 对象，不要输出 markdown。
响应 schema 必须是 pcbflow.v4cmp.planner-response/1，字段为：
{schema, scenario_id, board_snapshot_sha256, arm, round, patches, notes, uncertainty}。
patches 是最多 4 个 v4-route-patch/1 对象；超过 4 个的对象不计入预算。
每个 patch 必须包含 schema_version、action_type、base_candidate_geometry_sha256、
scenario_id、net_id、relation_id、parent_id、fixed_endpoint_ids、reason、source。
replace_subpath/move_vertex 还必须有 route_id/layer/width_mm/polyline_mm；
insert_via_candidate 还必须有 route_id/layer/via_mm/to_layer；
reject_route_patch 不得带几何字段，但仍须绑定 base hash 和 route identity。
动作只允许 replace_subpath、move_vertex、insert_via_candidate、reject_route_patch。
端点、route/net/relation/parent 身份、层、线宽、网格、净距、keepout 和连接性
必须保持合法。坐标帧：输入投影与 candidate_geometry 的坐标一律是板 mm
坐标系（原点左下角 0,0，与 bbox_mm 同帧，无渲染边距、无需任何换算），
polyline_mm 与 via_mm 直接使用该帧坐标填写。
不能确定时使用 reject_route_patch，不能伪造几何。
所有输出是不可信 planner 提案，必须经过独立 validator、geometry checker 和 rollback。"""


# ---------------------------------------------------------------- 基础 IO

def _read_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _file_chars(path: str) -> int:
    with open(path, "r", encoding="utf-8") as f:
        return len(f.read())


def _write_json(path: str, obj) -> None:
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    write_canonical_json(path, obj)


def read_board(root: str, sid: str) -> dict:
    return model.read_json(os.path.join(root, "board-snapshot-%s.json" % sid))


def baseline_run(board: dict) -> dict:
    """A0 稳定序基线（与先例 cmp_run.baseline_run 同构）。"""
    order = sorted(str(n["net_id"]) for n in board["nets"])
    return router.solve_board(board, {"route_order": order, "group": "E5-A0"})


# ---------------------------------------------------------------- token 台账（G5.3）

def estimate_tokens(n_chars: int) -> int:
    """确定性估计：chars/4 向上取整（prereg 冻结常量）。"""
    return -(-int(n_chars) // CHARS_PER_TOKEN)


def build_ledger(session_files: list, ledger_path: str) -> dict:
    """从 planner 可见文件集构造 token 台账并施加硬停。

    session_files: [{session_id, scenario_id, arm, files: [path, ...]}]
    （files = 该 session 全部 planner 可见负载：轮输入/反馈/响应）。

    硬停语义（prereg g53）：任一 session est_tokens > 200000 → 该 session
    blocked；累计消耗（含已 blocked）> 7M → 该 session 起全部 blocked。
    blocked session 对应场景在评估腿不出数。
    """
    entries = []
    running = 0
    suite_exceeded = False
    for s in session_files:
        chars = 0
        per_file = {}
        for p in s["files"]:
            n = _file_chars(p)
            per_file[os.path.basename(p)] = n
            chars += n
        est = estimate_tokens(chars)
        running += est
        blocked = False
        reason = None
        if est > SESSION_CEILING_TOKENS:
            blocked = True
            reason = "session_ceiling_exceeded"
        elif running > SUITE_CEILING_TOKENS or suite_exceeded:
            blocked = True
            reason = "suite_ceiling_exceeded"
            suite_exceeded = True
        entries.append({
            "session_id": s["session_id"],
            "scenario_id": s["scenario_id"],
            "arm": s["arm"],
            "file_chars": per_file,
            "total_chars": chars,
            "est_tokens": est,
            "blocked": blocked,
            "blocked_reason": reason,
        })
    ledger = {
        "schema": LEDGER_SCHEMA,
        "declared_date": DECLARED_DATE,
        "chars_per_token": CHARS_PER_TOKEN,
        "session_ceiling_tokens": SESSION_CEILING_TOKENS,
        "suite_ceiling_tokens": SUITE_CEILING_TOKENS,
        "sessions": entries,
        "totals": {
            "sessions": len(entries),
            "blocked_sessions": sum(1 for e in entries if e["blocked"]),
            "total_est_tokens": sum(e["est_tokens"] for e in entries),
        },
    }
    if ledger_path:
        _write_json(ledger_path, ledger)
    return ledger


def load_ledger(ledger_path: str) -> dict:
    return _read_json(ledger_path)


def scenario_blocked(ledger: dict, scenario_id: str) -> list:
    """该场景全部 session 的 blocked 情况（评估腿据此不出数）。"""
    return [e for e in ledger.get("sessions", [])
            if e.get("scenario_id") == scenario_id and e.get("blocked")]


# ---------------------------------------------------------------- 排序位输入（G5.2）

def build_ordering_input(board: dict) -> dict:
    """盲化 planner 输入：任务书 + manifest 直读投影（无候选几何、零 optimum）。"""
    return {
        "schema": ORDERING_INPUT_SCHEMA,
        "scenario_id": str(board["scenario_id"]),
        "board_snapshot_sha256": model.sha256_of(board),
        "task_text": ORDERING_TASK_TEXT,
        "projection": projection_mod.build_projection(board, None),
    }


def validate_ordering_response(resp, board: dict) -> dict:
    """严格结构校验：route_order 必须恰为全部 net_id 的排列（非法=blocked）。"""
    sid = str(board.get("scenario_id"))

    def blocked(reason):
        return {"blocked": True, "reason": str(reason), "route_order": None}

    if not isinstance(resp, dict):
        return blocked("response 不是 JSON 对象")
    if resp.get("schema") != ORDERING_RESPONSE_SCHEMA:
        return blocked("schema 非法")
    if resp.get("scenario_id") != sid:
        return blocked("scenario_id 不一致")
    order = resp.get("route_order")
    nets = sorted(str(n["net_id"]) for n in board["nets"])
    if not isinstance(order, list) or sorted(str(x) for x in order) != nets:
        return blocked("route_order 不是全部 net_id 的恰好一次排列")
    if len(order) != len(set(str(x) for x in order)):
        return blocked("route_order 含重复")
    notes = resp.get("notes", "")
    if not isinstance(notes, str) or len(notes) > 400:
        return blocked("notes 非法或超长")
    if resp.get("uncertainty") not in ("low", "medium", "high"):
        return blocked("uncertainty 非法")
    return {"blocked": False, "reason": None, "route_order": [str(x) for x in order]}


def evaluate_order(board: dict, order: list) -> dict:
    """评估腿：确定性求解一个顺序（planner 不可见）。

    双度量空间（DEV-E5-001 度量空间统一化，见 e5-report）：
    - objective_router：router 内建 metrics（冻结 optimum 件口径）；
    - objective_cmp：cmp_patch.cmp_metrics 独立重评分（先例 A1/模型臂口径）。
    capture 一律在 cmp 空间计算（四臂同空间）；router 空间作复现校验与副读数。
    """
    run = router.solve_board(board, {"route_order": list(order), "group": "E5-EVAL"})
    sat = run.get("status") == "sat"
    out = {
        "order": list(order),
        "status": run.get("status"),
        "objective_router": (round(float(run["metrics"]["objective"]), 6)
                             if sat else None),
        "objective": None,
    }
    if sat:
        world = GridWorld(board)
        m = cmp_patch.cmp_metrics(world, run.get("routes", []),
                                  run.get("vias", []))
        out["objective"] = round(float(m["objective"]), 6)
    return out


def verify_optimum_anchors(root: str, sids, prereg_path: str) -> dict:
    """optimum 冻结件逐件 sha256 对照 prereg/E0 锚（fail-closed）。"""
    prereg = _read_json(prereg_path)
    board_hashes = prereg["scenario_sets"]["ordering_seat_g52"][
        "board_snapshot_sha256"]
    baseline = _read_json(os.path.join(
        os.path.dirname(prereg_path), "..", "baseline", "baseline.json"))
    anchors = baseline["anchor_hashes"]["v4exp_synthetic_domain"][
        "exact_optimum_set"]
    out = {}
    for sid in sids:
        split = "cal" if sid.startswith("cal") else "hold"
        opt_path = os.path.join(root, "e1", "optimum", split,
                                "optimum-%s.json" % sid)
        h = hashlib.sha256(open(opt_path, "rb").read()).hexdigest()
        # 锚键=仓库相对路径（与 baseline.json/prereg 登记口径一致，按 sid 构造，
        # 不依赖 cwd）
        rel = "out/v4-experiment/e1/optimum/%s/optimum-%s.json" % (split, sid)
        board_path = os.path.join(root, "board-snapshot-%s.json" % sid)
        hb = hashlib.sha256(open(board_path, "rb").read()).hexdigest()
        board_key = "out/v4-experiment/board-snapshot-%s.json" % sid
        ok = (h == anchors[rel]["sha256"]
              and hb == board_hashes[board_key])
        if not ok:
            raise ValueError("anchor mismatch fail-closed: %s" % sid)
        out[sid] = {"path": rel, "sha256": h, "verified": True}
    return out


def _capture(obj_x, opt_obj, gap_s):
    """prereg 冻结公式：gap_S>0 → 1-gap_X/gap_S；gap_S=0 → tie 带 0/1。"""
    if obj_x is None:
        return "no_sat_order"
    gap_x = round(obj_x - opt_obj, 6)
    if gap_s > 0:
        return round(1.0 - gap_x / gap_s, 6)
    return 1 if abs(gap_x) <= 1e-9 else 0


def run_ordering_eval(root: str, sids, io_dir: str, prereg_path: str,
                      ledger_path: str, out_path: str) -> dict:
    """G5.2 评估腿：只读 planner 响应文件，逐场景 M/S/A1 对照 OPT。"""
    ledger = load_ledger(ledger_path)
    anchors = verify_optimum_anchors(root, sids, prereg_path)
    rows = []
    for sid in sids:
        board = read_board(root, sid)
        nets = sorted(str(n["net_id"]) for n in board["nets"])
        split = "cal" if sid.startswith("cal") else "hold"
        opt = _read_json(os.path.join(root, "e1", "optimum", split,
                                      "optimum-%s.json" % sid))
        opt_obj = opt.get("best_objective")
        unsat_cert = bool(opt.get("unsat_certified"))

        # OPT 腿：冻结 best_order 重解（DEV-E5-001：router 口径复现校验
        # fail-closed + cmp 空间统一重评分，capture 全臂同空间）
        opt_row = {"objective_router": opt_obj,
                   "order": opt.get("best_order"),
                   "anchor_verified": anchors[sid]["verified"],
                   "objective": None, "router_reproduced": None}
        if not unsat_cert and isinstance(opt_obj, (int, float)):
            opt_eval = evaluate_order(board, opt.get("best_order", []))
            reproduced = (opt_eval["objective_router"] is not None
                          and abs(opt_eval["objective_router"] - opt_obj)
                          <= 1e-9)
            opt_row["router_reproduced"] = reproduced
            opt_row["objective"] = opt_eval["objective"]
            if not reproduced:
                raise ValueError(
                    "optimum reproduction fail-closed: %s (%s != %s)"
                    % (sid, opt_eval["objective_router"], opt_obj))

        blocked_sessions = scenario_blocked(ledger, sid)
        s_arm = evaluate_order(board, nets)

        m_row = {"blocked": False, "blocked_reason": None, "order": None,
                 "status": None, "objective": None}
        if blocked_sessions:
            m_row.update({"blocked": True,
                          "blocked_reason": "token_ledger_session_blocked"})
        else:
            resp_path = os.path.join(io_dir, "planner-response-%s-M.json" % sid)
            if not os.path.exists(resp_path):
                m_row.update({"blocked": True,
                              "blocked_reason": "missing_response_file"})
            else:
                resp = _read_json(resp_path)
                vr = validate_ordering_response(resp, board)
                if vr["blocked"]:
                    m_row.update({"blocked": True,
                                  "blocked_reason": vr["reason"]})
                else:
                    ev = evaluate_order(board, vr["route_order"])
                    m_row.update({"order": ev["order"], "status": ev["status"],
                                  "objective": ev["objective"],
                                  "response_notes": resp.get("notes", ""),
                                  "response_uncertainty":
                                      resp.get("uncertainty")})

        base_run = baseline_run(board)
        if base_run.get("status") == "sat":
            world = GridWorld(board)
            geom = cmp_patch.geom_from_run(base_run)
            ls = cmp_localsearch.run_local_search(world, board, geom,
                                                  MAX_PROPOSALS)
            a1_obj = round(float(ls["final_metrics"]["objective"]), 6)
        else:
            a1_obj = None

        applicable = (not unsat_cert) and opt_obj is not None
        gap_s = round(s_arm["objective"] - opt_row["objective"], 6) \
            if applicable else None
        row = {
            "scenario_id": sid,
            "family": board["family"],
            "label": board["label"],
            "unsat_certified": unsat_cert,
            "applicable_for_capture": applicable,
            "optimum": opt_row,
            "arms": {
                "S": s_arm,
                "M": m_row,
                "A1": {"objective": a1_obj,
                       "evaluations": MAX_PROPOSALS if a1_obj is not None
                       else None},
            },
        }
        if applicable:
            row["gap_S"] = gap_s
            row["capture"] = {
                "S": _capture(s_arm["objective"], opt_row["objective"],
                              gap_s),
                "M": ("blocked" if m_row["blocked"]
                      else _capture(m_row["objective"], opt_row["objective"],
                                    gap_s)),
                "A1": _capture(a1_obj, opt_row["objective"], gap_s),
            }
        rows.append(row)

    summary = _ordering_summary(rows)
    result = {"schema": ORDERING_CAPTURE_SCHEMA, "declared_date": DECLARED_DATE,
              "scenario_ids": list(sids), "rows": rows, "summary": summary}
    if out_path:
        _write_json(out_path, result)
    return result


def _verdict(a, b):
    """objective 严格比较（None=不可比）。"""
    if a is None or b is None:
        return "not_comparable"
    if a < b:
        return "win"
    if a > b:
        return "loss"
    return "tie"


def _ordering_summary(rows: list) -> dict:
    sat_rows = [r for r in rows if r["applicable_for_capture"]
                and not r["arms"]["M"]["blocked"]]
    out = {"sat_applicable_n": len(sat_rows)}

    def pair_stats(field_m, field_ref):
        deltas, verdicts = [], {}
        for r in sat_rows:
            m = r["arms"]["M"][field_m]
            ref = r["arms"][field_ref][field_m]
            v = _verdict(m, ref)
            verdicts[r["scenario_id"]] = v
            if m is not None and ref is not None:
                deltas.append(round(m - ref, 6))
        stats = {
            "win": sum(1 for v in verdicts.values() if v == "win"),
            "tie": sum(1 for v in verdicts.values() if v == "tie"),
            "loss": sum(1 for v in verdicts.values() if v == "loss"),
            "per_scenario": [{"scenario_id": sid, "verdict": v}
                             for sid, v in sorted(verdicts.items())],
            "mean_delta": (round(cmp_stats.mean(deltas), 6) if deltas else None),
        }
        if deltas:
            stats["bootstrap_ci95"] = cmp_stats.paired_bootstrap_ci_mean_delta(
                deltas, BOOTSTRAP_SEED, BOOTSTRAP_RESAMPLES)
            stats["sign_test_p"] = cmp_stats.sign_test_two_sided(
                stats["win"], stats["loss"])
        return stats

    out["M_vs_S"] = pair_stats("objective", "S")
    out["M_vs_A1"] = pair_stats("objective", "A1")
    caps_m = [r["capture"]["M"] for r in sat_rows
              if isinstance(r["capture"]["M"], (int, float))]
    caps_a1 = [r["capture"]["A1"] for r in sat_rows
               if isinstance(r["capture"]["A1"], (int, float))]
    out["capture_mean_M"] = (round(cmp_stats.mean(caps_m), 6) if caps_m else None)
    out["capture_mean_A1"] = (round(cmp_stats.mean(caps_a1), 6) if caps_a1 else None)
    gap_rows = [r for r in sat_rows if r["gap_S"] > 0]
    out["gap_S_gt0_scenarios"] = [r["scenario_id"] for r in gap_rows]
    out["capture_on_gap_scenarios"] = {
        r["scenario_id"]: {"M": r["capture"]["M"], "A1": r["capture"]["A1"]}
        for r in gap_rows}
    # 污染敏感版（prereg blinding.mitigation ②：含/不含 cal-f4-07 两版）
    ex = [r for r in sat_rows if r["scenario_id"] != "cal-f4-07"]
    caps_m_ex = [r["capture"]["M"] for r in ex
                 if isinstance(r["capture"]["M"], (int, float))]
    out["capture_mean_M_excluding_cal-f4-07"] = (
        round(cmp_stats.mean(caps_m_ex), 6) if caps_m_ex else None)
    return out


# ---------------------------------------------------------------- 投影消融（G5.1）

def build_ablation_round1_inputs(root: str, sid: str, io_dir: str) -> dict:
    """两臂 round-1 输入（同 base 候选、同任务、唯一差异=表示格式）。"""
    board = read_board(root, sid)
    run = baseline_run(board)
    if run.get("status") != "sat":
        raise ValueError("unsat 场景无 base 候选几何: %s" % sid)
    geom = cmp_patch.geom_from_run(run)

    proj_input = {
        "schema": ABLATION_PROJ_INPUT_SCHEMA,
        "scenario_id": sid,
        "arm": "E5-PROJ",
        "round": 1,
        "board_snapshot_sha256": model.sha256_of(board),
        "base_candidate_geometry_sha256":
            cmp_patch.candidate_geometry_sha256(geom),
        "contract_text": PROJ_CONTRACT_TEXT,
        "action_types": list(cmp_patch.ACTION_TYPES),
        "budget": {"max_patches_per_call": MAX_PATCHES_PER_CALL,
                   "max_calls": 2, "max_total_proposals": MAX_PROPOSALS},
        "projection": projection_mod.build_projection(board, geom),
    }
    svg_input = cmp_inputs.build_input(board, geom, "C1", 1)  # 先例冻结格式
    p1 = os.path.join(io_dir, "planner-input-%s-E5-PROJ-r1.json" % sid)
    p2 = os.path.join(io_dir, "planner-input-%s-E5-SVG-r1.json" % sid)
    _write_json(p1, proj_input)
    _write_json(p2, svg_input)
    base_path = os.path.join(io_dir, "base-geometry-%s.json" % sid)
    _write_json(base_path, geom)
    return {"scenario_id": sid,
            "base_candidate_geometry_sha256":
                cmp_patch.candidate_geometry_sha256(geom),
            "paths": [p1, p2, base_path]}


def validate_patch_response(resp, board: dict, arm: str, rnd: int) -> dict:
    """wrapper 结构校验（对齐先例 cmp_patch.validate_response 字段要求，
    arm 取 E5 域；提案级合法性由 validate_patches 逐 patch 判定）。"""
    sid = str(board.get("scenario_id"))

    def blocked(reason):
        return {"blocked": True, "reason": str(reason), "patches": []}

    if not isinstance(resp, dict):
        return blocked("response 不是 JSON 对象")
    unknown = set(resp) - set(RESPONSE_ROOT_KEYS)
    if unknown:
        return blocked("根级未知键 %r" % sorted(unknown))
    if resp.get("schema") != RESPONSE_SCHEMA:
        return blocked("schema 非法")
    if resp.get("scenario_id") != sid:
        return blocked("scenario_id 不一致")
    got = resp.get("board_snapshot_sha256")
    if not isinstance(got, str) or got != model.sha256_of(board):
        return blocked("board_snapshot_sha256 stale/缺失")
    if resp.get("arm") not in E5_ARMS or resp.get("arm") != arm:
        return blocked("arm 非法或不一致")
    if resp.get("round") != rnd:
        return blocked("round 不一致")
    patches = resp.get("patches")
    if not isinstance(patches, list):
        return blocked("patches 缺失或不是列表")
    if len(patches) > MAX_PATCHES_PER_CALL:
        return blocked("patches 超过每轮上限")
    notes = resp.get("notes", "")
    if notes is None:
        notes = ""
    if not isinstance(notes, str) or len(notes) > cmp_patch.MAX_NOTES_CHARS:
        return blocked("notes 非法或超长")
    if resp.get("uncertainty") not in cmp_patch.UNCERTAINTY_LEVELS:
        return blocked("uncertainty 非法")
    return {"blocked": False, "reason": None, "patches": patches}


def evaluate_patches(world, board: dict, patches, base_geom: dict) -> dict:
    """先例语义评估：逐 patch validator 合法性+拒绝原因；合法且严格改善才接受。

    corrected_by_solver 恒 false（模型输出恒 untrusted，引擎从不修正）。
    """
    best = copy.deepcopy(base_geom)
    best_metrics = cmp_patch.cmp_metrics(world, best["routes"], best["vias"])
    records = []
    accepted = 0
    for i, patch in enumerate(patches):
        if not isinstance(patch, dict):
            records.append({"seq": i, "legal": False,
                            "reasons": ["patch 不是对象"], "accepted": False,
                            "corrected_by_solver": False})
            continue
        res = cmp_patch.validate_patch(world, board, patch, best)
        rec = {
            "seq": i,
            "action_type": patch.get("action_type"),
            "route_id": patch.get("route_id"),
            "legal": bool(res.get("legal")),
            "reasons": list(res.get("reasons", [])),
            "noop": bool(res.get("noop")),
            "accepted": False,
            "corrected_by_solver": False,
        }
        if res.get("legal") and not res.get("noop"):
            applied = cmp_patch.apply_and_check(world, board, patch, best)
            if applied.get("legal"):
                cand = applied["geometry"]
                m = cmp_patch.cmp_metrics(world, cand["routes"], cand["vias"])
                rec["candidate_objective"] = m["objective"]
                if m["objective"] < best_metrics["objective"]:
                    best, best_metrics = cand, m
                    accepted += 1
                    rec["accepted"] = True
                    rec["candidate_geometry_sha256"] = \
                        cmp_patch.candidate_geometry_sha256(cand)
        records.append(rec)
    return {"records": records, "accepted": accepted,
            "best_geometry": best,
            "best_objective": best_metrics["objective"]}


def build_feedback(sid: str, arm: str, rnd: int, eval_res: dict) -> dict:
    """二轮反馈协议：一轮拒绝原因结构化回流 + 已接受结果（prereg 冻结）。"""
    return {
        "schema": "pcbflow.v4_1.e5.planner-feedback/1",
        "scenario_id": sid,
        "arm": arm,
        "feedback_for_round": rnd + 1,
        "note": "逐 patch validator 结果回流：legal=false 的 reasons 为拒绝原因，"
                "请据此在下一轮修正（重新绑定 base_candidate_geometry_sha256）",
        "patch_results": eval_res["records"],
        "accepted_count": eval_res["accepted"],
        "updated_base_candidate_geometry_sha256":
            cmp_patch.candidate_geometry_sha256(eval_res["best_geometry"]),
        "updated_candidate_objective": eval_res["best_objective"],
    }


def build_ablation_round2_input(root: str, sid: str, arm: str, io_dir: str,
                                feedback: dict) -> str:
    """round-2 输入：更新后的 best 几何 + 结构化反馈（先例轮进语义）。"""
    board = read_board(root, sid)
    best_geom = _read_json(os.path.join(io_dir,
                                        "best-geometry-%s-%s.json" % (sid, arm)))
    if arm == "E5-PROJ":
        inp = {
            "schema": ABLATION_PROJ_INPUT_SCHEMA,
            "scenario_id": sid,
            "arm": arm,
            "round": 2,
            "board_snapshot_sha256": model.sha256_of(board),
            "base_candidate_geometry_sha256":
                cmp_patch.candidate_geometry_sha256(best_geom),
            "contract_text": PROJ_CONTRACT_TEXT,
            "action_types": list(cmp_patch.ACTION_TYPES),
            "budget": {"max_patches_per_call": MAX_PATCHES_PER_CALL,
                       "max_calls": 2, "max_total_proposals": MAX_PROPOSALS},
            "projection": projection_mod.build_projection(board, best_geom),
            "feedback": feedback,
        }
    else:
        inp = cmp_inputs.build_input(board, best_geom, "C1", 2,
                                     feedback=feedback)
    path = os.path.join(io_dir, "planner-input-%s-%s-r2.json" % (sid, arm))
    _write_json(path, inp)
    return path


def run_ablation_feedback_round(root: str, sid: str, arm: str,
                                io_dir: str) -> dict:
    """round-1 响应评估 + 反馈构造 + round-2 输入生成（确定性）。"""
    board = read_board(root, sid)
    world = GridWorld(board)
    resp_path = os.path.join(io_dir, "planner-response-%s-%s-r1.json"
                             % (sid, arm))
    resp = _read_json(resp_path)
    vr = validate_patch_response(resp, board, arm, 1)
    if vr["blocked"]:
        return {"scenario_id": sid, "arm": arm, "blocked": True,
                "blocked_reason": vr["reason"]}
    base_geom = _read_json(os.path.join(io_dir, "base-geometry-%s.json" % sid))
    ev = evaluate_patches(world, board, vr["patches"], base_geom)
    _write_json(os.path.join(io_dir, "best-geometry-%s-%s.json" % (sid, arm)),
                ev["best_geometry"])
    fb = build_feedback(sid, arm, 1, ev)
    fb_path = os.path.join(io_dir, "planner-feedback-%s-%s-r2.json"
                           % (sid, arm))
    _write_json(fb_path, fb)
    r2_path = build_ablation_round2_input(root, sid, arm, io_dir, fb)
    return {"scenario_id": sid, "arm": arm, "blocked": False,
            "round1": {"records": ev["records"],
                       "best_objective": ev["best_objective"]},
            "feedback_path": fb_path, "round2_input_path": r2_path}


def run_ablation_eval(root: str, sids, io_dir: str, ledger_path: str,
                      out_path: str) -> dict:
    """G5.1 评估腿：两臂两轮提案级合法率配对对照。"""
    ledger = load_ledger(ledger_path)
    rows = []
    for sid in sids:
        board = read_board(root, sid)
        world = GridWorld(board)
        base_geom = _read_json(os.path.join(io_dir,
                                            "base-geometry-%s.json" % sid))
        row = {"scenario_id": sid, "arms": {}}
        blocked_sessions = [e for e in scenario_blocked(ledger, sid)
                            if e.get("arm") in E5_ARMS]
        for arm in E5_ARMS:
            arm_row = {"rounds": [], "blocked": False, "blocked_reason": None}
            arm_block = [e for e in blocked_sessions if e.get("arm") == arm]
            if arm_block:
                arm_row.update({"blocked": True,
                                "blocked_reason": "token_ledger_session_blocked"})
                row["arms"][arm] = arm_row
                continue
            best_geom = copy.deepcopy(base_geom)
            best_obj = None
            for rnd in (1, 2):
                resp_path = os.path.join(
                    io_dir, "planner-response-%s-%s-r%d.json" % (sid, arm, rnd))
                if not os.path.exists(resp_path):
                    arm_row["rounds"].append({"round": rnd, "missing": True})
                    continue
                resp = _read_json(resp_path)
                vr = validate_patch_response(resp, board, arm, rnd)
                if vr["blocked"]:
                    arm_row["rounds"].append({"round": rnd, "blocked": True,
                                              "blocked_reason": vr["reason"]})
                    continue
                ev = evaluate_patches(world, board, vr["patches"], best_geom)
                arm_row["rounds"].append({
                    "round": rnd,
                    "proposals": len(vr["patches"]),
                    "legal": sum(1 for r in ev["records"] if r["legal"]),
                    "records": ev["records"],
                })
                best_geom = ev["best_geometry"]
                best_obj = ev["best_objective"]
            proposals = sum(r.get("proposals", 0) for r in arm_row["rounds"])
            legal = sum(r.get("legal", 0) for r in arm_row["rounds"])
            arm_row["proposals"] = proposals
            arm_row["legal"] = legal
            arm_row["legality_rate"] = (round(legal / proposals, 6)
                                        if proposals else None)
            arm_row["final_objective"] = (round(best_obj, 6)
                                          if best_obj is not None else None)
            row["arms"][arm] = arm_row
        rows.append(row)
    summary = _ablation_summary(rows)
    result = {"schema": ABLATION_EVAL_SCHEMA, "declared_date": DECLARED_DATE,
              "scenario_ids": list(sids), "rows": rows, "summary": summary}
    if out_path:
        _write_json(out_path, result)
    return result


def _ablation_summary(rows: list) -> dict:
    paired = []
    for r in rows:
        a = r["arms"]["E5-PROJ"]
        b = r["arms"]["E5-SVG"]
        if a.get("blocked") or b.get("blocked"):
            continue
        if a.get("legality_rate") is None or b.get("legality_rate") is None:
            continue
        paired.append((r["scenario_id"], a["legality_rate"],
                       b["legality_rate"]))
    deltas = [round(p - s, 6) for _sid, p, s in paired]
    out = {
        "paired_n": len(paired),
        "per_scenario": [{"scenario_id": sid,
                          "rate_PROJ": p, "rate_SVG": s,
                          "delta": round(p - s, 6)}
                         for sid, p, s in paired],
        "mean_delta_PROJ_minus_SVG": (round(cmp_stats.mean(deltas), 6)
                                      if deltas else None),
        "proposals_PROJ": sum(r["arms"]["E5-PROJ"].get("proposals", 0)
                              for r in rows),
        "proposals_SVG": sum(r["arms"]["E5-SVG"].get("proposals", 0)
                             for r in rows),
        "legal_PROJ": sum(r["arms"]["E5-PROJ"].get("legal", 0) for r in rows),
        "legal_SVG": sum(r["arms"]["E5-SVG"].get("legal", 0) for r in rows),
    }
    if deltas:
        out["bootstrap_ci95_delta"] = cmp_stats.paired_bootstrap_ci_mean_delta(
            deltas, BOOTSTRAP_SEED, BOOTSTRAP_RESAMPLES)
    # 反馈环有效性：round2 vs round1 合法率（逐臂）
    for arm in E5_ARMS:
        r1_p = r1_l = r2_p = r2_l = 0
        for r in rows:
            for rd in r["arms"][arm].get("rounds", []):
                if rd.get("missing") or rd.get("blocked"):
                    continue
                if rd["round"] == 1:
                    r1_p += rd.get("proposals", 0)
                    r1_l += rd.get("legal", 0)
                elif rd["round"] == 2:
                    r2_p += rd.get("proposals", 0)
                    r2_l += rd.get("legal", 0)
        out["round_legality_%s" % arm] = {
            "round1": {"proposals": r1_p, "legal": r1_l,
                       "rate": round(r1_l / r1_p, 6) if r1_p else None},
            "round2": {"proposals": r2_p, "legal": r2_l,
                       "rate": round(r2_l / r2_p, 6) if r2_p else None},
        }
    return out


# ---------------------------------------------------------------- CLI

def main():
    import sys
    payload = model.read_stdin_json()
    mode = payload["mode"]
    root = payload["root"]
    io_dir = payload["io_dir"]
    os.makedirs(io_dir, exist_ok=True)
    sids = [str(s) for s in payload["scenario_ids"]]

    if mode == "ordering-inputs":
        for sid in sids:
            board = read_board(root, sid)
            path = os.path.join(io_dir, "planner-input-%s-M.json" % sid)
            _write_json(path, build_ordering_input(board))
        sys.stdout.write(json.dumps({"mode": mode, "count": len(sids)},
                                    sort_keys=True) + "\n")
        return
    if mode == "ablation-inputs":
        made = [build_ablation_round1_inputs(root, sid, io_dir)
                for sid in sids]
        sys.stdout.write(json.dumps({"mode": mode, "count": len(made)},
                                    sort_keys=True) + "\n")
        return
    if mode == "ablation-feedback":
        res = []
        for sid in sids:
            for arm in E5_ARMS:
                res.append(run_ablation_feedback_round(root, sid, arm, io_dir))
        blocked = [r for r in res if r.get("blocked")]
        sys.stdout.write(json.dumps(
            {"mode": mode, "sessions": len(res), "blocked": len(blocked)},
            sort_keys=True) + "\n")
        return
    if mode == "ordering-eval":
        res = run_ordering_eval(root, sids, io_dir,
                                payload["prereg_path"], payload["ledger_path"],
                                payload["out_path"])
        sys.stdout.write(json.dumps(
            {"mode": mode, "scenarios": len(res["rows"]),
             "capture_mean_M": res["summary"]["capture_mean_M"]},
            sort_keys=True) + "\n")
        return
    if mode == "ablation-eval":
        res = run_ablation_eval(root, sids, io_dir, payload["ledger_path"],
                                payload["out_path"])
        s = res["summary"]
        sys.stdout.write(json.dumps(
            {"mode": mode, "paired_n": s["paired_n"],
             "mean_delta": s["mean_delta_PROJ_minus_SVG"],
             "ci95": s.get("bootstrap_ci95_delta")},
            sort_keys=True) + "\n")
        return
    if mode == "ledger":
        sessions = payload["sessions"]
        ledger = build_ledger(sessions, payload["ledger_path"])
        sys.stdout.write(json.dumps(
            {"mode": mode,
             "total_est_tokens": ledger["totals"]["total_est_tokens"],
             "blocked": ledger["totals"]["blocked_sessions"]},
            sort_keys=True) + "\n")
        return
    raise ValueError("未知 mode: %r" % (mode,))


if __name__ == "__main__":
    main()
