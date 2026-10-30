# -*- coding: utf-8 -*-
"""L5 三臂对照接线与 P5-G4 对账三数 + 终解 diff/席位 C 复查旗标（V5.0-DEV-TASKBOOK
§4 L5/L8、§5 P5-G4；P5③ 交付，引擎侧先行，零模型会话——A8/R46）。

三臂（改进四）：①无理念默认规划器（诊断臂）vs ②理念编译默认规划器（主路径）
vs ③②+模型 shadow 候选注入位。本模块只做**接线与对账**：①②直接调用
v5.planner 双臂；③=②的深拷贝候选 + 空注入位，模型候选经 inject_model_candidates
登记后由调用方合并送 L6 终选。真实模型会话是 P5 第二阶段（A3 五通道 output →
planner 形状候选的转译器届时交付）；本阶段的注入点=**合同占位**——输入形状校验
fail-closed + 透传登记，不含任何转译逻辑。

=======================================================================
P5-G4 三数的操作化定义（compute_g4；本 docstring 即钉死文本，改动=新决定）
=======================================================================

输入 = 三臂各自的 L6 终选结果（v5.selection.select_best 返回值）。

1. principle_gain（①vs② 对比值，bool）
   对每臂取**终选摘要** summary(sel) = (sel["verdict"],
   best 的 candidate_id, best 的**路由本体指纹**)，三元组任一不等 → True。
   - best 为 None（UNSAT/UNKNOWN）时 id/指纹均记 None，只比 verdict；
   - **路由本体指纹** = canonical_sha256({"route_order", "layer_assignment",
     "polylines"} 三键子集)。刻意**排除** arm/provenance/generation_trace——
     它们跨臂按构造必然不同（arm 令牌、rules_consumed、留痕），计入指纹会把
     指标恒置 True、彻底平庸化（文档化决定）；只比路由决策本身。
   - 语义：True=理念编译改变了引擎可见的终选结局（裁决态或路由本体）。
     **不判方向**——方向属 P5-G5 PU 六指标（不断言方向，如实给数）。

2. model_increment（②vs③ 对比值，bool）
   同一定义施于 ②与③：summary(arm2_sel) != summary(arm3_sel) → True。
   语义：模型候选在理念空间内改变了终选结局（含「②全滤除而③可行」型）。

3. echo_rate（②③候选重合率，float ∈ [0,1]）
   **操作化选择（二选一已定）：候选 id 集合的 Jaccard**——
   A2、A3 各取 sel["per_candidate"] 的 candidate_id 集合（注册参测全集，
   不论可行与否），echo_rate = |A2∩A3| / |A2∪A3|；
   A2=A3=∅ → 1.0（两空集视为完全重合）；恰一空集 → 0.0。结果 round 10。
   - 选 Jaccard 而非序重合的理由（文档化）：两臂候选注册序由各自规划器独立
     生成，序重合会把「同候选不同位次」计为不重合，而位次差不影响 ②③
     「模型复述了哪些候选」的语义；集合 Jaccard 对称、无序、确定性。
   - 未注入时 arm3 候选集=arm2 → echo_rate 恒 1.0（基线锚）。

=======================================================================
终解 diff 与席位 C 复查旗标（L8，§3.7「L8 终解+diff+复查旗标图」的引擎侧）
=======================================================================

diff_solutions(board, solution_a, solution_b) → v5.soldiff.v1 结构化差异清单：
两终解（v5.routes.v1 工件，executor 产物合同）先过 route_check.validate_routes
fail-closed 校验，再按 (partition_id, net_id) 键归并 entry（文档序），逐键比较
layer/polyline/width 三字段——任一不等即一条 difference（fields 排序、a/b 摘要
各含 layers/polyline/widths）。differences 按 (partition_id, net_id) 字典序；
零差异 → identical=True。视图渲染（view.render_l8_diff_view）与本 diff 语义同锁。

review_flags(diff) → 席位 C 复查旗标列表（**advisory 不阻塞**，继承 P09 复查
通道语义；P5 正式跑以投票形态出票，本函数是投票前的确定性差异点清单基座）：
规则=每条 difference 一面旗，flag_id 按 differences 序 RF-001 起连续编号；
severity 恒 "advisory"。输入 diff 形状不符 fail-closed 抛错；差异本身绝不抛错。

文档化最小决定（偏离披露）：
1. inject_model_candidates 的模型候选合同（占位期即冻结，第二阶段转译器照此
   产出）：candidate_id 形如 M-###（与引擎臂 C-### 空间隔离）；arm 恒
   "model-shadow"（席位 B shadow 语义的候选级令牌，selection 不枚举校验 arm、
   可透传）；provenance.generator 恒以 "v5.model_bridge/" 前缀（转译器版本
   标识位）；其余键形状与 planner 候选合同同名同型。几何/层合法性在此只做
   形状级检查（键齐、层数枚举、点数≥2、坐标有限、route_order 恰为全部分区）；
   可行性归 L6 测量环（A4：测量即批准人），此处不预判。
2. 注入是**事务式**的：整批先全量校验、后一次性登记；任一候选形状违约则整批
   拒绝、arm3 保持原状（不半登记）。
3. run_three_arms 的 arm3.base_candidates 是 arm2 的深拷贝（隔离性：arm2 侧
   后续变动不渗入 arm3）；board 以引用存入 arm3 供注入时形状核对。
4. 本模块零 I/O、零网络、零 LLM API、零随机零时钟；同输入双跑 canonical 字节
   相等（compute_g4/diff_solutions/review_flags 纯函数）。
"""
import copy
import re

from . import canonical
from .planner import plan_candidates
from .route_check import validate_routes

THREEARM_VERSION = "v5.threearm/0.1.0"
DIFF_SCHEMA_VERSION = "v5.soldiff.v1"

# 模型候选合同（决定 1）
MODEL_ARM_TOKEN = "model-shadow"
MODEL_ID_RE = re.compile(r"^M-\d{3}$")
MODEL_GENERATOR_PREFIX = "v5.model_bridge/"
_FREEDOMS = ("ordering", "allocation", "layer_plan", "corridor")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ThreeArmError(ValueError):
    """三臂接线/注入/对账 fail-closed 错误；path=键路径，message=原因。"""

    def __init__(self, path, message):
        self.path = path
        self.message = message
        super().__init__("[%s] %s" % (path or "<root>", message))


def _require(cond, path, msg):
    if not cond:
        raise ThreeArmError(path, msg)


def _is_num(v):
    return not isinstance(v, bool) and isinstance(v, (int, float)) \
        and v == v and v not in (float("inf"), float("-inf"))


# ---------------------------------------------------------------- 三臂接线

def run_three_arms(board, compiled_artifact):
    """三臂候选源接线（纯引擎侧）。

    返回 {"arm1": [候选...], "arm2": [候选...], "arm3": 注入位容器}：
    - arm1 = plan_candidates(arm="no-principle")（诊断臂；planner 合同保证其
      generation_trace 与 rules_consumed 恒空）；
    - arm2 = plan_candidates(arm="principle")（主路径）；
    - arm3 = {"arm": "arm3", "board": board（引用，注入时形状核对用）,
              "base_candidates": arm2 深拷贝, "model_candidates": []（注入位）}。
    板/工件校验由 planner 入口 fail-closed（本层不重复）。
    """
    arm1 = plan_candidates(board, compiled_artifact, arm="no-principle")
    arm2 = plan_candidates(board, compiled_artifact, arm="principle")
    arm3 = {"arm": "arm3", "board": board,
            "base_candidates": copy.deepcopy(arm2), "model_candidates": []}
    return {"arm1": arm1, "arm2": arm2, "arm3": arm3}


def _check_point(pt, path):
    _require(isinstance(pt, (list, tuple)) and len(pt) == 2, path,
             "坐标须为 [x,y] 二元组，得到 %r" % (pt,))
    _require(all(_is_num(v) for v in pt), path,
             "坐标须为有限数值，得到 %r" % (pt,))


def _validate_model_candidate(arm3, cand, idx, seen_ids):
    """单个模型候选形状校验（fail-closed 报键路径；合同见模块 docstring 决定 1）。"""
    base = "model_candidates[%d]" % idx
    _require(isinstance(cand, dict), base, "须为 dict")
    for key in ("candidate_id", "arm", "provenance", "route_order",
                "layer_assignment", "polylines", "generation_trace"):
        _require(key in cand, base, "缺少必填键 %s" % key)

    cid = cand["candidate_id"]
    _require(isinstance(cid, str) and MODEL_ID_RE.match(cid),
             base + ".candidate_id",
             "模型候选 id 须形如 M-001（合同决定 1），得到 %r" % (cid,))
    _require(cid not in seen_ids, base + ".candidate_id",
             "id %r 在 arm3 内重复（base+model 全局唯一）" % cid)

    _require(cand["arm"] == MODEL_ARM_TOKEN, base + ".arm",
             "模型候选 arm 须为 %r，得到 %r" % (MODEL_ARM_TOKEN, cand["arm"]))

    prov = cand["provenance"]
    _require(isinstance(prov, dict), base + ".provenance", "须为 dict")
    gen = prov.get("generator")
    _require(isinstance(gen, str) and gen.startswith(MODEL_GENERATOR_PREFIX),
             base + ".provenance.generator",
             "须为 %s 前缀的转译器标识（合同决定 1），得到 %r"
             % (MODEL_GENERATOR_PREFIX, gen))
    consumed = prov.get("rules_consumed")
    _require(isinstance(consumed, list)
             and all(isinstance(x, str) and x for x in consumed),
             base + ".provenance.rules_consumed", "须为非空字符串数组（可为空表）")
    sha = prov.get("compiled_sha256")
    _require(isinstance(sha, str) and _SHA256_RE.match(sha),
             base + ".provenance.compiled_sha256", "须为 64 位十六进制 sha256")

    board = arm3["board"]
    part_ids = {p["partition_id"] for p in board.get("partitions", [])}
    signal_ids = {str(layer["id"]) for layer in board.get("stackup", [])
                  if layer.get("kind") == "signal" and layer.get("available") is True}

    order = cand["route_order"]
    _require(isinstance(order, list)
             and all(isinstance(x, str) and x for x in order),
             base + ".route_order", "须为非空分区 id 字符串数组")
    _require(len(order) == len(set(order)), base + ".route_order", "含重复分区")
    _require(set(order) == part_ids, base + ".route_order",
             "不恰为全部分区（缺 %s，多 %s）"
             % (sorted(part_ids - set(order)), sorted(set(order) - part_ids)))

    assign = cand["layer_assignment"]
    _require(isinstance(assign, dict), base + ".layer_assignment", "须为 dict")
    _require(set(map(str, assign)) == set(order),
             base + ".layer_assignment", "键须恰为 route_order 分区集")
    for pid, layer in assign.items():
        _require(layer in signal_ids, base + ".layer_assignment.%s" % pid,
                 "层 %r 不在 stackup 可用信号层 %s" % (layer, sorted(signal_ids)))

    polys = cand["polylines"]
    _require(isinstance(polys, dict), base + ".polylines", "须为 dict")
    _require(set(map(str, polys)) == set(order),
             base + ".polylines", "键须恰为 route_order 分区集")
    for pid, poly in polys.items():
        ppath = base + ".polylines.%s" % pid
        _require(isinstance(poly, list) and len(poly) >= 2, ppath,
                 "折线须为 ≥2 个坐标点，得到 %r" % (poly,))
        for k, pt in enumerate(poly):
            _check_point(pt, "%s[%d]" % (ppath, k))

    trace = cand["generation_trace"]
    _require(isinstance(trace, list), base + ".generation_trace", "须为数组")
    for j, entry in enumerate(trace):
        epath = "%s.generation_trace[%d]" % (base, j)
        _require(isinstance(entry, dict)
                 and {"rule", "freedom", "effect"} <= set(entry),
                 epath, "须含 rule/freedom/effect 三键")
        _require(isinstance(entry.get("rule"), str) and entry["rule"],
                 epath + ".rule", "须为非空字符串")
        _require(entry.get("freedom") in _FREEDOMS,
                 epath + ".freedom", "须在四自由度枚举内")
        _require(isinstance(entry.get("effect"), str) and entry["effect"],
                 epath + ".effect", "须为非空一句话")
    return cid


def inject_model_candidates(arm3, model_candidates):
    """模型候选注入（A3 转译器合同占位：形状校验 fail-closed + 透传登记）。

    - arm3 须为 run_three_arms 产出的注入位容器（形状不符 fail-closed）；
    - model_candidates 须为 list（可为空表=无模型候选的基线对照）；
    - **事务式**（决定 2）：整批先全量校验，任一违约抛 ThreeArmError 且 arm3
      保持原状；全过才按输入序深拷贝登记进 arm3["model_candidates"]；
    - 返回同一 arm3（原地登记；调用方可续链）。
    """
    _require(isinstance(arm3, dict), "arm3", "须为 dict（run_three_arms 产出）")
    _require(arm3.get("arm") == "arm3", "arm3.arm", "须为 'arm3'")
    _require(isinstance(arm3.get("board"), dict), "arm3.board", "须为 dict（板引用）")
    _require(isinstance(arm3.get("base_candidates"), list),
             "arm3.base_candidates", "须为 list")
    _require(isinstance(arm3.get("model_candidates"), list),
             "arm3.model_candidates", "须为 list（注入位）")
    _require(isinstance(model_candidates, list), "model_candidates",
             "须为 list，得到 %s" % type(model_candidates).__name__)

    seen = {c["candidate_id"] for c in arm3["base_candidates"]
            if isinstance(c, dict) and isinstance(c.get("candidate_id"), str)}
    seen |= {c["candidate_id"] for c in arm3["model_candidates"]
             if isinstance(c, dict) and isinstance(c.get("candidate_id"), str)}
    for i, cand in enumerate(model_candidates):
        # 逐个校验并把 id 记入 seen（批内重复同 id 即时拒绝，仍满足事务式：
        # 登记统一在全部校验通过之后）
        seen.add(_validate_model_candidate(arm3, cand, i, seen))
    arm3["model_candidates"].extend(copy.deepcopy(c) for c in model_candidates)
    return arm3


def arm3_candidates(arm3):
    """arm3 全候选 = base_candidates + model_candidates（送 L6 select_best 的
    合并视图；新列表，不改 arm3）。"""
    _require(isinstance(arm3, dict) and arm3.get("arm") == "arm3",
             "arm3", "须为 run_three_arms 产出的注入位容器")
    return list(arm3["base_candidates"]) + list(arm3["model_candidates"])


# ---------------------------------------------------------------- G4 三数

def _require_selection(sel, path):
    _require(isinstance(sel, dict), path, "终选结果须为 dict（select_best 返回值）")
    _require(isinstance(sel.get("verdict"), str) and sel["verdict"],
             path + ".verdict", "须为非空字符串（SAT/UNSAT/UNKNOWN）")
    best = sel.get("best")
    _require(best is None or isinstance(best, dict), path + ".best",
             "须为候选 dict 或 None")
    if isinstance(best, dict):
        for key in ("candidate_id", "route_order", "layer_assignment", "polylines"):
            _require(key in best, path + ".best", "best 候选缺少必填键 %s" % key)
    pcs = sel.get("per_candidate")
    _require(isinstance(pcs, list), path + ".per_candidate", "须为 list")
    for i, pc in enumerate(pcs):
        _require(isinstance(pc, dict) and isinstance(pc.get("candidate_id"), str)
                 and pc["candidate_id"],
                 "%s.per_candidate[%d].candidate_id" % (path, i),
                 "须为含非空 candidate_id 字符串的 dict")


def _sel_summary(sel):
    """终选摘要三元组（操作化定义见模块 docstring「G4 三数」1/2）。"""
    best = sel["best"]
    if best is None:
        cid, fp = None, None
    else:
        cid = best["candidate_id"]
        essence = {"route_order": best["route_order"],
                   "layer_assignment": best["layer_assignment"],
                   "polylines": best["polylines"]}
        fp = canonical.canonical_sha256(essence)
    return {"verdict": sel["verdict"], "best_candidate_id": cid,
            "best_essence_sha256": fp}


def _candidate_ids(sel):
    return {pc["candidate_id"] for pc in sel["per_candidate"]}


def compute_g4(arm1_sel, arm2_sel, arm3_sel):
    """P5-G4 三数（操作化定义钉死在模块 docstring，此处只算不解释）：
    {"principle_gain": bool, "model_increment": bool, "echo_rate": float}。"""
    _require_selection(arm1_sel, "arm1_sel")
    _require_selection(arm2_sel, "arm2_sel")
    _require_selection(arm3_sel, "arm3_sel")
    s1, s2, s3 = _sel_summary(arm1_sel), _sel_summary(arm2_sel), _sel_summary(arm3_sel)
    a2, a3 = _candidate_ids(arm2_sel), _candidate_ids(arm3_sel)
    if not a2 and not a3:
        echo = 1.0
    elif not a2 or not a3:
        echo = 0.0
    else:
        echo = round(len(a2 & a3) / len(a2 | a3), 10)
    return {"principle_gain": s1 != s2,
            "model_increment": s2 != s3,
            "echo_rate": echo}


# ---------------------------------------------------------------- 终解 diff

def _key_entries(routes):
    """routes entry 按 (partition_id, net_id) 归并（文档序）→ 摘要表。"""
    keys = {}
    for e in routes:
        key = (e["partition_id"], e["net_id"])
        acc = keys.setdefault(key, {"layers": [], "polyline": [], "widths": []})
        acc["layers"].append(e["layer"])
        acc["polyline"].extend([list(pt) for pt in e["polyline"]])
        acc["widths"].append(e["width"])
    return keys


def diff_solutions(board, solution_a, solution_b):
    """两终解（v5.routes.v1 工件）→ v5.soldiff.v1 结构化差异清单（合同见模块
    docstring「终解 diff」节）。先 validate_routes fail-closed（错板错件配对、
    形状违约一律抛错），再逐键比较 layer/path/width。纯函数，双跑字节等。"""
    validate_routes(board, solution_a)
    validate_routes(board, solution_b)
    ka = _key_entries(solution_a["routes"])
    kb = _key_entries(solution_b["routes"])
    differences = []
    for key in sorted(set(ka) | set(kb)):
        ea, eb = ka.get(key), kb.get(key)
        if ea == eb:
            continue
        fields = []
        if (ea or {}).get("layers") != (eb or {}).get("layers"):
            fields.append("layer")
        if (ea or {}).get("polyline") != (eb or {}).get("polyline"):
            fields.append("path")
        if (ea or {}).get("widths") != (eb or {}).get("widths"):
            fields.append("width")
        differences.append({"partition_id": key[0], "net_id": key[1],
                            "fields": sorted(fields), "a": ea, "b": eb})
    board_sha = (board.get("provenance") or {}).get("board_sha256")
    return {"schema_version": DIFF_SCHEMA_VERSION,
            "board_id": board.get("board_id"),
            "board_sha256": board_sha,
            "identical": not differences,
            "differences": differences}


def review_flags(diff):
    """席位 C 复查旗标（advisory 不阻塞；规则=终解 diff 的结构化差异点清单，
    见模块 docstring）。返回旗标列表：每条 difference 一面旗，RF-### 连续编号。
    diff 形状不符 fail-closed；差异存在本身绝不抛错。"""
    _require(isinstance(diff, dict), "diff", "须为 dict（diff_solutions 产出）")
    _require(diff.get("schema_version") == DIFF_SCHEMA_VERSION, "diff.schema_version",
             "须为 %r，得到 %r" % (DIFF_SCHEMA_VERSION, diff.get("schema_version")))
    diffs = diff.get("differences")
    _require(isinstance(diffs, list), "diff.differences", "须为 list")
    flags = []
    for i, d in enumerate(diffs):
        path = "diff.differences[%d]" % i
        _require(isinstance(d, dict), path, "须为 dict")
        _require(isinstance(d.get("partition_id"), str) and d["partition_id"],
                 path + ".partition_id", "须为非空字符串")
        _require(isinstance(d.get("net_id"), str) and d["net_id"],
                 path + ".net_id", "须为非空字符串")
        fields = d.get("fields")
        _require(isinstance(fields, list) and fields
                 and all(isinstance(f, str) and f for f in fields),
                 path + ".fields", "须为非空字段名字符串数组")
        fields_txt = ",".join(fields)
        flags.append({
            "flag_id": "RF-%03d" % (i + 1),
            "severity": "advisory",
            "partition_id": d["partition_id"],
            "net_id": d["net_id"],
            "fields": list(fields),
            "note": "终解 A/B 在分区 %s（净 %s）存在结构化差异 [%s]"
                    "（席位 C 复查建议，advisory 不阻塞）"
                    % (d["partition_id"], d["net_id"], fields_txt),
        })
    return flags


# P5③ 预留挂点（第二阶段接线位，本阶段零行为）：
# - A3 五通道 output → planner 形状候选的真实转译器将作为独立函数落在本模块
#   （合同=inject_model_candidates 的候选合同 + resolve_scope 的 scope 语义），
#   届时 inject_model_candidates 的「透传登记」语义不变，只在其上游加转译步；
# - 席位 C 投票形态（A6）将在 review_flags 清单之上按 v5.voting.tally 汇票。
# 本阶段不落任何占位函数体（禁止假实现混入测量环），只留本注记锚点。
