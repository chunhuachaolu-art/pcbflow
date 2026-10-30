# -*- coding: utf-8 -*-
"""demo-01b-local-c1 修正板测试（boards 只增不改：demo-01 保持如实 UNSAT 负例）。

demo-01-v2-corridor 的走廊 C1 被声明为全高带（y∈[0,40]），容量核算把垂直横穿的
既布铜 P7/P9 也计入，零路线时 C1/F.Cu 已溢出（3.3+0.2+0.2+2×0.5=4.7>4.3），
任何候选必然 UNSAT（口径缝文档化于 tests/test_executor.py 的
test_demo01_fixed_only_capacity_seam）。demo-01b 为用户裁定的新增修正板：
唯一语义改动 = C1 rect 改局部带 y∈[16,24]（对齐 V2 场景：K1/K2 之间的唯一通道），
零路线时固定铜只余 ribbon 3.3，给 SAT 路径。

覆盖（P4 门 G1 同口径）：
- 板可载入（L0 fail-closed 含 schema+哈希链）、provenance 一致、文件 canonical 字节稳定；
- 零 routes 时 check_routes 容量不溢出（C1/F.Cu 3.3 ≤ 4.3）；
- 全链：compile → plan_candidates(arm="principle") → select_best → execute_candidate
  判定 ROUTED 且 check_routes feasible（selection 对候选端点直线如实 UNSAT 时，
  按 P4 门 G1 口径取 plan_candidates[0] 进执行器）；
- 执行器确定性：同一候选双跑 routes canonical 字节相等。

执行器单跑 ~30s：模块级缓存跑一次全链（含确定性双跑），全部用例复用。
板只读；不落盘（不传 out_dir）。
"""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from v5 import canonical  # noqa: E402
from v5.board import compute_board_sha256, load_board_file  # noqa: E402
from v5.compiler import compile_board  # noqa: E402
from v5.executor import execute_candidate  # noqa: E402
from v5.planner import plan_candidates  # noqa: E402
from v5.route_check import ROUTES_SCHEMA_VERSION, check_routes  # noqa: E402
from v5.selection import select_best  # noqa: E402

BOARD_PATH = os.path.join(ROOT, "boards", "d", "demo-01b-local-c1.board.v1.json")

_CACHE = {}


def _chain():
    """模块级一次跑全链：板 → 编译 → 规划 → 终选 → 执行器双跑（缓存复用）。"""
    if "chain" not in _CACHE:
        board = load_board_file(BOARD_PATH)
        art, _ = compile_board(board)
        cands = plan_candidates(board, art, arm="principle")
        sel = select_best(board, cands)
        # P4 门 G1 同口径：selection UNSAT（候选折线=P3 合同端点直线）时
        # 用 plan_candidates[0] 进执行器（执行器侧 A* 细化几何）。
        if sel["verdict"] == "SAT" and sel["best"] is not None:
            cand = sel["best"]
        else:
            cand = cands[0]
        res1 = execute_candidate(board, cand)
        res2 = execute_candidate(board, cand)   # 确定性硬测试：同一候选双跑
        _CACHE["chain"] = (board, cands, sel, res1, res2)
    return _CACHE["chain"]


def _routes_doc(board, entries):
    """空/给定 entries 的 v5.routes.v1 工件（镜像 tests/test_executor.py helper）。"""
    sha = board["provenance"]["board_sha256"]
    return {"schema_version": ROUTES_SCHEMA_VERSION, "board_id": board["board_id"],
            "board_sha256": sha, "routes": entries, "negotiation_log": ["t"],
            "provenance": {"generator": "v5.executor/0.1.0", "board_sha256": sha}}


# ---------------------------------------------------------------- a. 载入与哈希链

def test_board_loads_schema_and_hash_chain():
    """板过 L0 fail-closed（schema+哈希链）；provenance 一致；唯一语义改动=C1 局部带。"""
    board, _, _, _, _ = _chain()
    assert board["board_id"] == "demo-01b-local-c1"
    assert board["provenance"]["board_sha256"] == compute_board_sha256(board)
    # 唯一语义改动：C1 rect 全高 y∈[0,40] → 局部带 y∈[16,24]（x/capacity/layers 不变）
    c1 = next(z for z in board["zones"] if z["zone_id"] == "C1")
    assert c1["kind"] == "corridor" and c1["layers"] == "signal"
    assert c1["capacity"] == pytest.approx(4.3)
    assert c1["rect"] == {"x_min": 30.0, "y_min": 16.0, "x_max": 36.0, "y_max": 24.0}
    # 其余一切原样保留（对底板 demo-01-v2-corridor 的逐键结构对账）
    with open(os.path.join(ROOT, "boards", "d",
                           "demo-01-v2-corridor.board.v1.json"),
              encoding="utf-8") as f:
        base = json.load(f)
    assert board["hard_rules"] == base["hard_rules"]
    assert board["partitions"] == base["partitions"]
    assert board["nets"] == base["nets"]
    assert board["principle_registry"] == base["principle_registry"]
    assert board["stackup"] == base["stackup"]
    assert board["workspace"] == base["workspace"]
    assert [z for z in board["zones"] if z["zone_id"] != "C1"] == \
        [z for z in base["zones"] if z["zone_id"] != "C1"]
    for key in ("adapter", "source_sha256", "source_type", "source_uri"):
        assert board["provenance"][key] == base["provenance"][key]


def test_board_file_canonical_roundtrip():
    """文件本体即 canonical 字节：读入→再序列化逐字节稳定（round-trip）。"""
    with open(BOARD_PATH, "rb") as f:
        raw = f.read()
    board = json.loads(raw.decode("utf-8"))
    assert raw == canonical.canonical_json(board)


# ---------------------------------------------------------------- b. 零路线容量

def test_zero_routes_capacity_no_overflow():
    """修正板口径缝修复实证：零 routes 时 C1/F.Cu 只余固定 ribbon 3.3 ≤ 4.3
    （demo-01 同口径为 4.7 > 4.3 必然溢出，见 test_executor 缝测试）。"""
    board, _, _, _, _ = _chain()
    rep = check_routes(board, _routes_doc(board, []))
    assert rep["feasible"] is True
    c1 = [c for c in rep["capacity_checks"] if c[0] == "C1/F.Cu"]
    assert len(c1) == 1
    clid, occ, cap = c1[0]
    assert (clid, cap) == ("C1/F.Cu", pytest.approx(4.3))
    assert occ == pytest.approx(3.3) and occ <= cap
    assert rep["capacity_meta"]["C1/F.Cu"]["terms"] == [3.3]   # 固定铜只余 ribbon
    assert rep["attributed_violations"] == []


# ---------------------------------------------------------------- c. 全链 SAT 路径

def test_full_chain_routed_and_feasible():
    """全链：selection 对端点直线候选如实 UNSAT → P4 门 G1 口径 plan[0] 进执行器
    → ROUTED 且 check_routes feasible（容量账本可审计：F.Cu 4.0 / B.Cu 0.2）。"""
    board, cands, sel, res, _ = _chain()
    assert len(cands) >= 1
    assert sel["verdict"] == "UNSAT" and sel["best"] is None   # 直线候选如实滤除
    assert res["verdict"] == "ROUTED" and res["routes"] is not None
    assert all(pn["status"] in ("routed", "fixed", "ribbon")
               for pn in res["per_net"])
    rep = check_routes(board, res["routes"])
    assert rep["feasible"] is True
    assert rep["attributed_violations"] == []
    occ = {clid: o for clid, o, cap in rep["capacity_checks"]}
    for clid, o in occ.items():
        assert clid.startswith("C1/") and o <= 4.3 + 1e-9
    assert rep["capacity_meta"]["C1/F.Cu"]["terms"] == [3.3, 0.2]   # ribbon+1 条穿越
    assert rep["capacity_meta"]["C1/B.Cu"]["terms"] == [0.2]        # 换层穿越


# ---------------------------------------------------------------- d. 确定性

def test_executor_double_run_byte_equal():
    """同一候选 execute_candidate 双跑：routes canonical 字节相等（硬测试）。"""
    _, _, _, res1, res2 = _chain()
    assert res1["verdict"] == res2["verdict"] == "ROUTED"
    assert canonical.canonical_json(res1["routes"]) == \
        canonical.canonical_json(res2["routes"])
    assert res1["negotiation_log"] == res2["negotiation_log"]
    assert res1["per_net"] == res2["per_net"]
