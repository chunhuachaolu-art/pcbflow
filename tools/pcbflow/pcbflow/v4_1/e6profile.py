"""pcbflow.v4_1.e6profile -- 性能画像格式冻结+E3/E4 求解路径采样（E6 G6.3）。

任务书 §3 E6：search_nodes/耗时/内存进 evaluation_metadata（不进核心
hash），格式冻结。**先冻结格式再产出样例**（prereg g63.order）。

冻结 schema=pcbflow.v4_1.e6-perf-profile/1（validate_profile 程序判）：

    {
      "schema": "pcbflow.v4_1.e6-perf-profile/1",
      "declared_date": "2026-09-12",
      "subject": {"kind","solver","scenario_id","deterministic_key"},
      "search_nodes": int>=0,          # 求解路径确定性计数
      "astar_expanded": int>=0,        # _astar2 expanded 求和（E4 路径）
      "elapsed_s": float>=0,           # 测量时长（非 wall-clock 时间戳）
      "memory": {"method","peak_bytes":int>=0},
      "outcome": {"status"},
      "measurement_policy",
      "hash_policy": {"enters_core_hash": false, "placement": ...}
    }

禁 wall-clock 时间戳字段（timestamp/evaluated_at/at 进 profile=validator
拒收）；对本 schema 任何修改=新版本号+整批降级（P-RC-2）。

不进核心 hash 的机器证：core_facts(record) 剔除 evaluation_metadata
（copper_loop §1.4 同口径）；demo_core_hash_exclusion 对含画像记录算
双哈希（含/不含）证明剔除函数有效。

采样器（零改既有文件）：
- sample_e3_solver2(sid, cost_arm)：out/v4-comparative-experiment
  board-snapshot-<sid>.json -> solver2.solve_board2（flat=v4exp 字节镜像
  臂 / layered=v4_1 分层默认臂）；search_nodes 取自冻结 metrics 键；
- sample_e4_revc_row(proj, row)：e4revc.route_row（A0 路径）；既有
  route_row 失败时 search_nodes=0（如实），另以 solver2._astar2 透明
  计数包装器（monkeypatch-restore）累计 astar_expanded=真实搜索量。

采样值描述性、非判据、允许跨运行漂移（elapsed/memory 逐次不同；
search_nodes/astar_expanded 确定性）。零网络、零模型。
"""

from __future__ import annotations

import hashlib
import json
import time

from . import DECLARED_DATE
from .canonical import dumps_canonical

__all__ = ["PROFILE_SCHEMA", "validate_profile", "make_profile",
           "core_facts", "core_hash", "demo_core_hash_exclusion",
           "sample_e3_solver2", "sample_e4_revc_row", "collect_profiles"]

PROFILE_SCHEMA = "pcbflow.v4_1.e6-perf-profile/1"

#: 测量方法声明（冻结；变更=新版本）
MEASUREMENT_POLICY = {
    "search_nodes": "求解路径确定性计数（solver2 冻结 metrics 键）",
    "astar_expanded": "solver2._astar2 expanded 返回值求和（透明包装器"
                      "monkeypatch-restore，零改既有文件；E4 失败行真实"
                      "搜索量）",
    "elapsed_s": "time.perf_counter 差分（测量时长；非 wall-clock 时间"
                 "戳，不携日期/时刻语义）",
    "memory": "tracemalloc 峰值字节（采样窗口内 Python 分配口径）",
}

#: 禁止字段（wall-clock 时间戳语义；进 profile=拒收）
_FORBIDDEN_FIELDS = ("timestamp", "evaluated_at", "measured_at", "at",
                     "datetime", "wall_clock", "now")

_REQUIRED = {
    "subject": ("kind", "solver", "scenario_id", "deterministic_key"),
}


class ProfileSchemaError(ValueError):
    """画像 schema 违例（fail-closed）。"""


def validate_profile(obj):
    """冻结 schema 程序判（结构/类型/单位/禁字段）。违例 raise。"""
    if not isinstance(obj, dict):
        raise ProfileSchemaError("profile 必须为 dict")
    if obj.get("schema") != PROFILE_SCHEMA:
        raise ProfileSchemaError("schema 版本不符（冻结 %s）: %r"
                                 % (PROFILE_SCHEMA, obj.get("schema")))
    if obj.get("declared_date") != DECLARED_DATE:
        raise ProfileSchemaError("declared_date 必须为声明常量 %s"
                                 % DECLARED_DATE)
    bad = sorted(set(obj) & set(_FORBIDDEN_FIELDS))
    if bad:
        raise ProfileSchemaError("禁 wall-clock 时间戳字段: %s" % bad)
    sub = obj.get("subject")
    if not isinstance(sub, dict):
        raise ProfileSchemaError("subject 必须为 dict")
    for k in _REQUIRED["subject"]:
        if not isinstance(sub.get(k), str) or not sub.get(k):
            raise ProfileSchemaError("subject.%s 必须非空 str" % k)
    for k in ("search_nodes", "astar_expanded"):
        v = obj.get(k)
        if not isinstance(v, int) or isinstance(v, bool) or v < 0:
            raise ProfileSchemaError("%s 必须为 int>=0: %r" % (k, v))
    e = obj.get("elapsed_s")
    if not isinstance(e, (int, float)) or isinstance(e, bool) or e < 0 \
            or e != e or e in (float("inf"),):
        raise ProfileSchemaError("elapsed_s 必须为有限 float>=0: %r" % (e,))
    mem = obj.get("memory")
    if not isinstance(mem, dict) or not isinstance(mem.get("method"), str) \
            or not isinstance(mem.get("peak_bytes"), int) \
            or isinstance(mem.get("peak_bytes"), bool) \
            or mem.get("peak_bytes") < 0:
        raise ProfileSchemaError("memory 必须为 {method:str, peak_bytes:"
                                 "int>=0}")
    out = obj.get("outcome")
    if not isinstance(out, dict) or not isinstance(out.get("status"), str):
        raise ProfileSchemaError("outcome 必须为 {status:str,...}")
    hp = obj.get("hash_policy")
    if not isinstance(hp, dict) or hp.get("enters_core_hash") is not False:
        raise ProfileSchemaError("hash_policy.enters_core_hash 必须 "
                                 "字面 false（不进核心 hash）")
    if not isinstance(obj.get("measurement_policy"), str):
        raise ProfileSchemaError("measurement_policy 必须为 str")
    # canonical 序列化确定性（round-trip 稳定）
    if dumps_canonical(json.loads(dumps_canonical(obj))) != \
            dumps_canonical(obj):
        raise ProfileSchemaError("canonical 序列化不确定")
    return True


def make_profile(subject, search_nodes, astar_expanded, elapsed_s,
                 peak_bytes, outcome, memory_method="tracemalloc_peak_"
                 "bytes"):
    """构造并通过冻结校验的画像 dict。"""
    obj = {
        "schema": PROFILE_SCHEMA,
        "declared_date": DECLARED_DATE,
        "subject": dict(subject),
        "search_nodes": int(search_nodes),
        "astar_expanded": int(astar_expanded),
        "elapsed_s": round(float(elapsed_s), 6),
        "memory": {"method": memory_method, "peak_bytes": int(peak_bytes)},
        "outcome": dict(outcome),
        "measurement_policy": json.dumps(MEASUREMENT_POLICY,
                                         ensure_ascii=False,
                                         sort_keys=True),
        "hash_policy": {
            "enters_core_hash": False,
            "placement": "evaluation_metadata.perf_profile（核心事实体"
                         "剔除 evaluation_metadata 后哈希，copper_loop "
                         "§1.4 同口径）",
        },
    }
    validate_profile(obj)
    return obj


# ================================================================ hash 排除

def core_facts(record):
    """核心事实体=剔除 evaluation_metadata（画像只允许栖身该键）。"""
    return {k: v for k, v in record.items()
            if k != "evaluation_metadata"}


def core_hash(record):
    """核心事实 hash（sha256 of canonical core facts）。"""
    return hashlib.sha256(
        dumps_canonical(core_facts(record)).encode("utf-8")).hexdigest()


def demo_core_hash_exclusion(record):
    """机器证：画像进/不进 evaluation_metadata 不改核心 hash。"""
    without = dict(record)
    without.pop("evaluation_metadata", None)
    with_empty = dict(record)
    with_empty["evaluation_metadata"] = {"perf_profile": None}
    return {
        "schema": "pcbflow.v4_1.e6-profile-hash-exclusion-demo/1",
        "declared_date": DECLARED_DATE,
        "core_hash_as_is": core_hash(record),
        "core_hash_without_evaluation_metadata": core_hash(without),
        "core_hash_with_null_profile": core_hash(with_empty),
        "exclusion_proven": (core_hash(record)
                             == core_hash(without)
                             == core_hash(with_empty)),
        "rule": "画像仅栖身 evaluation_metadata；核心 hash 对其存在/取值"
                "不敏感（schema 冻结的排除语义）",
    }


# ================================================================ 采样器

def sample_e3_solver2(board_obj, sid, cost_arm="flat"):
    """E3 既有求解路径：solver2.solve_board2（v4exp 112 场景快照板）。

    cost_arm：flat=v4exp.router 字节镜像臂（E3 G3.2 byte-equality 口径）
    / layered=v4_1 分层默认成本臂（E4 引擎口径）。
    """
    import tracemalloc
    from . import solver2
    order = sorted(str(n["net_id"]) for n in board_obj["nets"])
    plan = {"route_order": order, "group": "A0"}
    if cost_arm == "flat":
        cost = None  # solve_board2 默认=flat（v4exp 镜像）
        solver_desc = "solver2.solve_board2(flat=v4exp byte-mirror)"
    elif cost_arm == "layered":
        cost = "layered_default"
        solver_desc = ("solver2.solve_board2(layered=v4_1 via-cost-"
                       "model default)")
    else:
        raise ValueError("cost_arm 必须为 flat|layered: %r" % (cost_arm,))
    tracemalloc.start()
    t0 = time.perf_counter()
    if cost_arm == "flat":
        run = solver2.solve_board2(board_obj, plan)
    else:
        from .costmodel import ViaCostModel
        cm = ViaCostModel(list(solver2.GridWorld(board_obj).layers))
        run = solver2.solve_board2(board_obj, plan, cost_model=cm)
    elapsed = time.perf_counter() - t0
    _cur, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    m = run.get("metrics", {})
    return make_profile(
        {"kind": "e3_solver2_scenario", "solver": solver_desc,
         "scenario_id": sid,
         "deterministic_key": "order=%s;arm=%s" % (",".join(order[:6])
                                                   + ("..." if len(order)
                                                      > 6 else ""),
                                                   cost_arm)},
        search_nodes=int(m.get("search_nodes", 0)),
        astar_expanded=int(m.get("search_nodes", 0)),
        elapsed_s=elapsed, peak_bytes=peak,
        outcome={"status": str(run.get("status")),
                 "routes": len(run.get("routes", [])),
                 "vias": len(run.get("vias", []))})


def sample_e4_revc_row(proj, row):
    """E4 既有求解路径：e4revc.route_row（A0 单行求解）。

    透明包装器计数 solver2._astar2 expanded（既有 route_row 失败时
    search_nodes=0 如实；astar_expanded=真实搜索量）。零改既有文件。
    """
    import tracemalloc
    from . import e4revc, solver2

    real_astar2 = solver2._astar2
    counter = {"calls": 0, "expanded": 0}

    def _counting_astar2(*a, **kw):
        seg, exp = real_astar2(*a, **kw)
        counter["calls"] += 1
        counter["expanded"] += int(exp)
        return seg, exp

    solver2._astar2 = _counting_astar2
    try:
        tracemalloc.start()
        t0 = time.perf_counter()
        res = e4revc.route_row(proj, row)
        elapsed = time.perf_counter() - t0
        _cur, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    finally:
        solver2._astar2 = real_astar2
    return make_profile(
        {"kind": "e4_revc_row",
         "solver": "e4revc.route_row(A0)",
         "scenario_id": "%s|%s" % (row.get("row_id", "?"),
                                   row.get("net", "?")),
         "deterministic_key": "endpoint_a=%s;endpoint_b=%s" % (
             (row["a"].get("x"), row["a"].get("y"),
              row["a"].get("layer")),
             (row["b"].get("x"), row["b"].get("y"),
              row["b"].get("layer")))},
        search_nodes=int(res.get("search_nodes", 0)),
        astar_expanded=counter["expanded"],
        elapsed_s=elapsed, peak_bytes=peak,
        outcome={"status": "ok" if res.get("ok") else str(
            res.get("reason")), "astar_calls": counter["calls"]})


def collect_profiles(profiles, path):
    """画像集落盘（canonical；逐条已过 validate_profile）。"""
    from .canonical import write_canonical_json
    for p in profiles:
        validate_profile(p)
    write_canonical_json(path, {
        "schema": "pcbflow.v4_1.e6-profiles-collection/1",
        "declared_date": DECLARED_DATE,
        "profiles": profiles,
    })
    return len(profiles)
