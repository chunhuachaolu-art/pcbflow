# -*- coding: utf-8 -*-
"""升级件⑤测试（2026-09-14，F12：executor-孔协调缝修复 + 回流孔安置扩容）。

A 层真实板升级世界全链 0/7 SAT 归因（out/v5-p5/trial/final-g1-assessment.md，
只读参考）的两类 executor 缺陷，本件以构造板/单元场景修复并钉死：

- **F1 缝修复（走线↔他网已提交过孔铜）**：badgeleds-do-electronics /
  pmod-bme280 所有网 attempt=1 布通、final route_check（D2 场景）实抓已布
  走线落在先提交的他网过孔铜 R5 邻域——根因=executor 栅格障碍模型含他网
  走线铜但不含他网已提交过孔铜。修后 edge_blocked 把全部已提交**他网**孔铜
  圆盘（radius=drill/2+annular，与 route_check _via_coppers 同源）按 R5 入
  障碍；同网孔=合法连接点；同分区豁免与折线障碍同口径。反方向（先孔后线）
  的 via_blocked 对他网铜 R5 无同分区豁免（①件）以单元测试钉住。耗尽归因
  补 via-obstacle-sealed 类（无绕行空间场景，归因串含 via 障碍字样）。
  夹具 f1-seam-detour（双门墙：A 网过渡孔封死 1 号门 → B 网修后绕行）+
  改造前世界复现对照（旧枚举孔位 + 门 1 穿越 = R5 track-vs-via 归责，即
  真实板失败签名）+ f1-via-seal（单走廊双壁全封 → 如实 FAILED 且
  exhaustion-cause=via-obstacle-sealed）。
- **F2 回流孔安置扩容**：pmod-i2c24io 36 网布通后 /SDA「错位+双侧相连约束
  下无有效位」106 attempts 全耗尽。_return_via_offsets 枚举域扩容（pitch/2
  细半径档 × 16 方向三族），确定性全序不变、D3/R4 约束零放松（旧域 ⊆ 新域
  逐项断言）；placement 单元场景=首环/旧域全封锁、扩容域命中，且逐项对照
  断言旧 0.25mm/8 向枚举确实全灭。
- **确定性**：两夹具板同输入双跑 canonical 字节等（红线钉）。

零网络、零 LLM API、零 kicad-cli；零 out/ 写入（夹具全部内联构造，board
文件零新增——红线只准动 v5/executor.py + tests/）。
"""
import json
import math
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from v5 import canonical  # noqa: E402
from v5.board import compute_board_sha256, load_board  # noqa: E402
from v5.executor import (  # noqa: E402
    EXECUTOR_VERSION, _Context, _place_return_via, _return_via_offsets,
    execute_candidate)
from v5.metrics import clearance as clr  # noqa: E402
from v5.route_check import (  # noqa: E402
    ROUTES_SCHEMA_VERSION, _RouteCopper, check_routes, validate_routes)


# ---------------------------------------------------------------- 板构造

SIG = [{"id": "F.Cu", "kind": "signal", "preferred_direction": "h",
        "available": True},
       {"id": "B.Cu", "kind": "signal", "preferred_direction": "v",
        "available": True}]


def _part(pid, a, b, ptype="MISC", layer="F.Cu", width=0.2, pads=None):
    g = {"endpoints": [list(a), list(b)]}
    if pads is not None:
        g["pad_terminals"] = pads
    return {"partition_id": pid, "ptype": ptype, "layer_policy": layer,
            "planned_width": width, "current_a": 0, "geometry": g,
            "speed_class": "low_speed",
            "width_prior": {"w_min": width, "w_max": 0.4}}


def _net(nid, pids):
    return {"net_id": nid, "net_class": "MISC", "partitions": list(pids)}


def _mk(board_id, workspace, parts, nets, zones=None):
    board = {
        "schema_version": "v5.board.v1", "board_id": board_id,
        "stackup": SIG, "workspace": workspace,
        "zones": zones or [],
        "partitions": parts, "nets": nets,
        "hard_rules": {
            "R1": {"floor_mm": 0.3, "k_a": 0.4},
            "R2": {"max_parallel_mm": 5.0, "min_distance_mm": 3.0},
            "R3": {"unsplittable": True},
            "R4": {"max_distance_mm": 2.0, "return_via_required": True},
            "R5": {"min_clearance_mm": 0.5},
            "R6": {"keepout_zones_forbidden": True, "plane_forbidden": True},
        },
        "principle_registry": [],
        "provenance": {"source_type": "synthetic", "adapter": "hand",
                       "source_uri": "tests/test_upgrade5_via_coordination.py",
                       "source_sha256": "0" * 64},
    }
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    return load_board(board)


def _cand(board, order=None):
    parts = [p["partition_id"] for p in board["partitions"]]
    return {"candidate_id": "C-U5", "arm": "no-principle",
            "provenance": {"generator": "hand", "rules_consumed": [],
                           "compiled_sha256": "0" * 64},
            "route_order": order or parts,
            "layer_assignment": {p["partition_id"]: "F.Cu"
                                 for p in board["partitions"]},
            "polylines": {}, "generation_trace": []}


# 端点焊盘：endpoint0 仅 B.Cu、endpoint1 仅 F.Cu（D4 端点层约束 → A 网在
# 起点 (8,2) 确定性落过渡孔；B.Cu preferred_direction="v" + 水平路由的方向
# 代价使「起点即换层」严格最优 → 孔位唯一）。
_PADS = [{"endpoint": 0, "shape": "circle", "size_mm": [0.6],
          "layers": ["B.Cu"]},
         {"endpoint": 1, "shape": "circle", "size_mm": [0.6],
          "layers": ["F.Cu"]}]


def _seam_detour_board():
    """f1-seam-detour：x=8 竖墙留双门（门1 y∈[1,3] 含 A 网过渡孔位、门2
    y∈[9,11]）；A 网焊盘异层 → 过渡孔恰落门 1 中点 (8,2)；B 网近唯一 F.Cu
    直径路径穿门 1。修后 B 绕行（可行）；改造前 B 穿门 1 → R5 track-vs-via。"""
    parts = [_part("PT-W1", (8, 0), (8, 1), ptype="ROUTED"),
             _part("PT-W2", (8, 3), (8, 9), ptype="ROUTED"),
             _part("PT-W3", (8, 11), (8, 12), ptype="ROUTED"),
             _part("PT-PA", (8, 2), (12, 2), pads=_PADS),
             _part("PT-PB", (2, 2), (14, 2))]
    nets = [_net("NW1", ["PT-W1"]), _net("NW2", ["PT-W2"]),
            _net("NW3", ["PT-W3"]), _net("NA", ["PT-PA"]),
            _net("NB", ["PT-PB"])]
    return _mk("f1-seam-detour", {"x_min": 0.0, "y_min": 0.0,
                                  "x_max": 16.0, "y_max": 12.0}, parts, nets)


def _via_seal_board():
    """f1-via-seal：全宽水平双壁（F.Cu+B.Cu，y=1.05/2.95）夹出 y∈[1.55,2.45]
    唯一走廊，A 网过渡孔 (8,2) 的 R5 邻域（半径 0.8）恰封死走廊全部 x=8 穿越节
    点（两层同封：孔铜跨层）→ B 网无任何绕行空间，如实 FAILED；归因串含
    via 障碍字样。"""
    parts = [_part("PT-HF1", (0, 1.05), (16, 1.05), ptype="ROUTED"),
             _part("PT-HF2", (0, 2.95), (16, 2.95), ptype="ROUTED"),
             _part("PT-HB1", (0, 1.05), (16, 1.05), ptype="ROUTED",
                   layer="B.Cu"),
             _part("PT-HB2", (0, 2.95), (16, 2.95), ptype="ROUTED",
                   layer="B.Cu"),
             _part("PT-PA", (8, 2), (12, 2), pads=_PADS),
             _part("PT-PB", (2, 2), (14, 2))]
    nets = [_net("NHF1", ["PT-HF1"]), _net("NHF2", ["PT-HF2"]),
            _net("NHB1", ["PT-HB1"]), _net("NHB2", ["PT-HB2"]),
            _net("NA", ["PT-PA"]), _net("NB", ["PT-PB"])]
    return _mk("f1-via-seal", {"x_min": 0.0, "y_min": 0.0,
                               "x_max": 16.0, "y_max": 6.0}, parts, nets)


def _plain_board(board_id, zones=None, x_max=20.0, y_max=12.0):
    """单元测试用最小板（单 MISC 分区，无固定铜；zones 可注 keepout）。"""
    return _mk(board_id, {"x_min": 0.0, "y_min": 0.0, "x_max": x_max,
                          "y_max": y_max},
               [_part("PT-X", (1, 1), (19, 1))], [_net("NX", ["PT-X"])],
               zones=zones)


def _commit_run(ctx, net_id, pid, layer, pts, tv, rv, k=0):
    """提交一条 route entry + 其铜（复现 commit_entries 合同）。"""
    entry = {"partition_id": pid, "net_id": net_id, "layer": layer,
             "polyline": [list(p) for p in pts], "width": 0.2,
             "transition_vias": [list(v) for v in tv],
             "return_vias": [list(v) for v in rv]}
    copper = _RouteCopper(net_id, "route:%s:%s#%d" % (net_id, pid, k),
                          layer, pid, entry["polyline"], 0.2)
    ctx.commit_entries([entry], [copper])


# 改造前（executor/0.2.0）枚举域复制——对照断言的唯一事实源（旧公式逐字）。
def _legacy_return_via_offsets(min_hole, max_dist, pitch):
    cands = []
    dirs = ((1, 0), (-1, 0), (0, 1), (0, -1))
    diag_dirs = ((1, 1), (1, -1), (-1, 1), (-1, -1))
    k = 1
    while k * pitch <= max_dist + clr.EPS:
        ax = k * pitch
        if ax >= min_hole - clr.EPS:
            for j, (dx, dy) in enumerate(dirs):
                cands.append((ax, j, dx * ax, dy * ax))
        diag = ax * math.sqrt(2.0)
        if diag <= max_dist + clr.EPS and diag >= min_hole - clr.EPS:
            for j, (dx, dy) in enumerate(diag_dirs):
                cands.append((diag, len(dirs) + j, dx * ax, dy * ax))
        k += 1
    cands.sort(key=lambda c: (round(c[0], 9), c[1]))
    return [(c[2], c[3]) for c in cands]


_CACHE = {}


def _board(builder):
    key = builder.__name__
    if key not in _CACHE:
        _CACHE[key] = builder()
    return _CACHE[key]


# ---------------------------------------------------------------- 版本钉

def test_versions_executor_050():
    """升级件⑤版本升格：executor 0.3.0→0.4.0（F4 引擎搜索能力三件）；⑥波
    D6-3 版本升格：executor 0.4.0→0.5.0（板边禁布带入障碍栅格 + exhaustion
    归因 edge-clearance 类）、route_check 0.2.0→0.3.0（edge_violations 消费
    接口键）。既有钉 040 的更新（披露：版本钉同步）。"""
    # V5-D8 翻转披露（2026-09-22）：executor 0.5.0→0.6.0、route_check
    # 0.3.0→0.4.0（hole_violations 键；板固孔禁布带见 executor docstring）
    # V5-SMALLWAVE 翻转披露（2026-09-23）：executor 0.6.0→0.6.1（geom-secondary
    # 几何二级归因 log 行，log-only）
    # V5-R2 翻转披露（2026-09-24）：executor 0.6.1→0.7.0（rip-up 有界深化
    # 2/8/20→5/12/30+W-2 联合重排+W-3 波次/档位导引+W-4 victim 定向探针）
    # V5-EXECUTOR-ENG-R1 翻转披露（2026-10-02）：executor 0.8.0→0.9.0
    assert EXECUTOR_VERSION == "v5.executor/0.13.0"  # 0.13.0 同步（engine-fix-r1 阶段一：FX-1 梯内 memo＋FX-2 微优化，纯等价提速；0.11.0=EXEC-R8-B）  # EXEC-R8-B 同步（候选出口事件接线）
    from v5.route_check import ROUTE_CHECK_VERSION
    # W-6 ED-2 修复翻新披露（2026-09-26）：0.4.0→0.4.1（PTH 孔筒 union）
    assert ROUTE_CHECK_VERSION == "v5.route_check/0.5.0"  # V5-R7 同步


# ---------------------------------------------------------------- F1 单元

def test_f1_committed_via_copper_blocks_other_net_track_edges():
    """F1 核心：已提交他网过孔铜按 R5 入走线障碍（修后行为）；跨全信号层；
    同网孔=合法连接点不入障碍。"""
    ctx = _Context(_plain_board("u5-f1-edge"))
    _commit_run(ctx, "NA", "PT-PA", "F.Cu", [(8, 2), (12, 2)],
                [(8, 2)], [(9, 2.5)])
    assert ctx.via_points == [("NA", "PT-PA", (8.0, 2.0)),
                              ("NA", "PT-PA", (9.0, 2.5))]
    # 他网边落入过渡孔 (8,2) R5 邻域（0.8=孔半径 0.3+R5 0.5）→ 封
    assert ctx.edge_blocked("F.Cu", (8.0, 2.25), (8.25, 2.25),
                            "NB", "PT-PB", 0.2) == "R5"
    # 孔铜跨全信号层：B.Cu 同几何边同封（route_check 场景逐层一枚同款）
    assert ctx.edge_blocked("B.Cu", (8.0, 2.25), (8.25, 2.25),
                            "NB", "PT-PB", 0.2) == "R5"
    # 回流孔 (9,2.5) 铜同款封边
    assert ctx.edge_blocked("F.Cu", (9.0, 2.75), (9.25, 3.0),
                            "NB", "PT-PB", 0.2) == "R5"
    # 远离孔铜的边不封
    assert ctx.edge_blocked("F.Cu", (2.0, 2.0), (2.25, 2.0),
                            "NB", "PT-PB", 0.2) is None
    # 同网已提交孔=合法连接点：本网边贴自家孔铜不封
    assert ctx.edge_blocked("F.Cu", (8.0, 2.25), (8.25, 2.25),
                            "NA", "PT-PA", 0.2) is None
    # 间隙 0.55（> R5 0.5）的边不封（R5 "<" 才违例，与 v5.drc 同口径；
    # 恰 0.8 边距的浮点擦边由 v5.drc 自身测试锚定，此处不复制浮点刀口）
    assert ctx.edge_blocked("F.Cu", (8.0, 2.85), (8.25, 2.85),
                            "NB", "PT-PB", 0.2) is None


def test_f1_via_copper_same_partition_exemption_mirrors_tracks():
    """同分区豁免与折线障碍同口径：仅共享端点豁免区入边（exempt_same_partition）
    对同分区他网孔铜豁免；异分区孔铜不豁免；严格档恒封。"""
    ctx = _Context(_plain_board("u5-f1-exempt"))
    _commit_run(ctx, "NX2", "PT-PX", "F.Cu", [(11, 7), (14, 7)],
                [(11, 7)], [(12, 7.5)])
    q = ((11.0, 7.3), (11.2, 7.3))
    # 同分区对腿 + 共享端点豁免区 → 过（归责层 route_check 同分区豁免覆盖）
    assert ctx.edge_blocked("F.Cu", *q, "NX3", "PT-PX", 0.2,
                            exempt_same_partition=True) is None
    # 同分区严格档 → 封（物理分离不放松，docstring 决定 4 同款）
    assert ctx.edge_blocked("F.Cu", *q, "NX3", "PT-PX", 0.2) == "R5"
    # 异分区 + 豁免旗 → 不豁免（豁免只及同分区）
    assert ctx.edge_blocked("F.Cu", *q, "NX3", "PT-OTHER", 0.2,
                            exempt_same_partition=True) == "R5"


def test_f1_reverse_direction_via_placement_stays_strict():
    """反方向钉死（①件 D2 既有语义，本件测试承重）：孔安置经 via_blocked 对
    他网铜 R5 **无同分区豁免**（豁免只及铜不及孔——即便走线边在共享端点豁免
    区可贴同分区铜，孔位仍封）+ 对已提交孔点 D3 最小孔心距 + R6 禁布。"""
    ctx = _Context(_plain_board("u5-f1-viaok"))
    _commit_run(ctx, "NA", "PT-PA", "F.Cu", [(8, 2), (12, 2)],
                [(8, 2)], [(9, 2.5)])
    _commit_run(ctx, "NA", "PT-P1", "F.Cu", [(14, 5), (18, 5)], [], [], k=1)
    # 同分区（PT-P1）他网走线上方 0.45 处落孔：gap=0.45−0.3=0.15<R5 → 封，
    # 即便孔属同分区（无豁免）
    assert ctx.via_blocked((16.0, 5.45), "NB") == "R5"
    # 对照：同分区走线边在共享端点豁免区可贴行（豁免只及铜）
    assert ctx.edge_blocked("F.Cu", (16.0, 5.45), (16.25, 5.45),
                            "NB", "PT-P1", 0.2,
                            exempt_same_partition=True) is None
    assert ctx.edge_blocked("F.Cu", (16.0, 5.45), (16.25, 5.45),
                            "NB", "PT-P1", 0.2) == "R5"
    # 已提交孔点最小孔心距（D3 = 2r+R5 = 1.1）：距 (8,2) 1.0 → D3
    assert ctx.via_blocked((8.0, 1.0), "NB") == "D3"
    # R6 禁布：孔圆入 keepout → 封
    ko = [{"zone_id": "K1", "kind": "keepout", "layers": "all",
           "rect": {"x_min": 4.0, "y_min": 4.0, "x_max": 6.0, "y_max": 6.0}}]
    ctx2 = _Context(_plain_board("u5-f1-ko", zones=ko))
    assert ctx2.via_blocked((5.0, 5.0), "NB") == "R6"


# ---------------------------------------------------------------- F1 全链

def test_f1_seam_detour_board_routes_and_final_check_clean():
    """seam 场景（修后）：f1-seam-detour 全链 ROUTED 且 route_check feasible；
    A 网过渡孔恰落门 1 中点 (8,2)、扩容枚举首候选马步 (9,2.5) 落回流孔；
    B 网所有走线段距 A 网全部孔铜 ≥ 孔半径+R5（F1 生效的几何证据）。"""
    board = _board(_seam_detour_board)
    res = execute_candidate(board, _cand(board))
    assert res["verdict"] == "ROUTED" and res["routes"] is not None
    assert check_routes(board, res["routes"])["feasible"] is True
    by_pid = {pn["partition_id"]: pn for pn in res["per_net"]}
    assert by_pid["PT-PA"]["status"] == "routed"
    assert by_pid["PT-PB"]["status"] == "routed"
    # A 网孔位钉：过渡孔 (8,2)（门 1 中点）、回流孔 = 扩容枚举第一候选
    # 马步族 (+1.0,+0.5)（1.118 ≥ D3 1.1，旧域首候选为轴向 (1.25,0)）
    na = [e for e in res["routes"]["routes"] if e["net_id"] == "NA"]
    tvs = {(v[0], v[1]) for e in na for v in e["transition_vias"]}
    rvs = {(v[0], v[1]) for e in na for v in e["return_vias"]}
    assert tvs == {(8.0, 2.0)}
    assert rvs == {(9.0, 2.5)}
    # B 网走线对 A 网全部孔铜保持 ≥ 0.8（中心线口径：pad_segment_distance
    # −孔半径 ≥ R5）——门 1 直径路径（距 (8,2) 仅 0.5）已被 F1 封死
    via_pts = sorted(tvs | rvs)
    mind = min(clr.pad_segment_distance(v, 0.3, p, q)
               for v in via_pts
               for e in res["routes"]["routes"] if e["net_id"] == "NB"
               for p, q in zip(e["polyline"][:-1], e["polyline"][1:]))
    assert mind >= 0.5 - 1e-9


def test_f1_seam_prefix_world_reproduction_control():
    """改造前世界复现对照（测试承重证明）：旧枚举回流孔位 (9.25,2) + B 网门 1
    穿越（贴墙-贴走线合法的中心线 y=2.5）——final route_check 实抓 R5
    track-vs-via（gap=0.2）归责，即 badgeleds/pmod-bme280 失败签名；证明
    B 网修后绕行确为 F1 所致而非板巧合。"""
    board = _board(_seam_detour_board)

    def e(pid, nid, layer, pts, tv, rv):
        return {"partition_id": pid, "net_id": nid, "layer": layer,
                "polyline": [list(p) for p in pts], "width": 0.2,
                "transition_vias": [list(v) for v in tv],
                "return_vias": [list(v) for v in rv]}

    a_bc = e("PT-PA", "NA", "B.Cu", [(8, 2), (9.25, 2), (8, 2)],
             [(8, 2)], [(9.25, 2)])          # 旧域首候选 (+1.25, 0)
    a_fc = e("PT-PA", "NA", "F.Cu", [(8, 2), (9.25, 2), (8, 2), (12, 2)],
             [(8, 2)], [(9.25, 2)])
    b_fc = {"partition_id": "PT-PB", "net_id": "NB", "layer": "F.Cu",
            "polyline": [[2.0, 2.0], [4.0, 2.5], [8.0, 2.5], [10.8, 2.5],
                         [12.0, 2.85], [13.2, 2.5], [14.0, 2.0]],
            "width": 0.2, "transition_vias": [], "return_vias": []}
    sha = board["provenance"]["board_sha256"]
    doc = {"schema_version": ROUTES_SCHEMA_VERSION,
           "board_id": board["board_id"], "board_sha256": sha,
           "routes": [a_bc, a_fc, b_fc], "negotiation_log": ["t"],
           "provenance": {"generator": "v5.executor/0.2.0",
                          "board_sha256": sha}}
    validate_routes(board, doc)   # 链审计过（合法工件形态）
    rep = check_routes(board, doc)
    assert rep["feasible"] is False
    r5_via = [v for v in rep["attributed_violations"] if v["rule"] == "R5"
              and any("via" in s for s in v["subjects"])]
    assert len(r5_via) == 2        # 过渡孔 + 回流孔各一处 track-vs-via
    assert all(v["data"]["gap_mm"] == pytest.approx(0.2) for v in r5_via)


def test_f1_sealed_no_detour_fails_with_via_attribution():
    """无绕行空间场景（如实 FAILED）：f1-via-seal 全宽双壁夹唯一走廊、A 网
    过渡孔 (8,2) 的 R5 邻域封死全部 x=8 穿越节点（两层同封）→ B 网 106
    attempts 全耗尽。

    升级件⑤-F4c 语义更新（披露，既有断言翻转）：耗尽后 rip-up 有界触发——
    阻塞集确定性选中 A 网（其铜落在 B 失败走廊内）；rip A 后 B 重布布通、
    A 重布（30 计划前缀）因 B+双壁全封而耗尽 → 回滚；5 轮轮尽 → 如实
    FAILED，exhaustion-cause 升格为进程类 ripup-reroute-failed（ripped 网重
    布失败）；几何细节（ripped 谁/为何）保留在 ripup 事件行。A 网重布耗尽
    本身即 F1 缝的承重证据：B 占位后 A 的孔/线无处安放。"""
    board = _board(_via_seal_board)
    res = execute_candidate(board, _cand(board))
    assert res["verdict"] == "FAILED" and res["routes"] is None
    by_pid = {pn["partition_id"]: pn for pn in res["per_net"]}
    assert by_pid["PT-PA"]["status"] == "routed"    # A 网本身布通并提交
    assert by_pid["PT-PB"]["status"] == "failed"
    # 106 初始 + 5 轮 ×2 序 ×（N 重布 1 attempt 即布通；被 rip 网 NA 的 30
    # 计划前缀耗尽计入 NA 自身账，不计 N）。R2 翻转披露：轮 2→5、前缀
    # 20→30、W-3 波次+档位双序（0.6.1=106+2）
    assert by_pid["PT-PB"]["attempts"] == 106 + 5 * 2
    log = res["negotiation_log"]
    causes = [ln for ln in log if "exhaustion-cause=" in ln]
    assert causes == ["net=NB partition=PT-PB exhaustion-cause="
                      "ripup-reroute-failed（被 rip 网 NA 重布失败：A* 搜索"
                      "空间耗尽（障碍/容量/敏感约束下无路））"]
    rips = [ln for ln in log if "ripped=" in ln]
    assert len(rips) == 5 and all("ripped=['NA']" in ln for ln in rips)
    # A 网回流孔：扩容域细半径档生效（马步/对角候选被双壁封死后落到新域
    # 轴向 1.125 档；旧域首候选为 (9.25,2)）
    na = [e for e in res["per_net"] if e["partition_id"] == "PT-PA"]
    assert na[0]["vias"] == 1


def test_via_obstacle_sealed_cause_unit_pin():
    """F1 归因类单测钉（F4c 语义更新后 exhaustion-cause 几何分类保持不变；
    rip-up 不触发时（无已布网可 rip）仍按几何类如实归因）：场景上下文先提交
    A 网走线（含过渡孔 (8,2)+回流孔 (9,2.5)），直接钉 _exhaustion_cause 的
    via-obstacle-sealed 分类串。"""
    from v5 import executor as ex
    board = _board(_via_seal_board)
    ctx = _Context(board)
    _commit_run(ctx, "NA", "PT-PA", "F.Cu", [(8, 2), (12, 2)],
                [(8, 2)], [(9, 2.5)])
    cause = ex._exhaustion_cause(ctx, "PT-PB", "NB", 0.2,
                                 (2.0, 2.0), (14.0, 2.0))
    assert cause == "via-obstacle-sealed（他网过孔铜障碍封死直连走廊，绕行类）"


# ---------------------------------------------------------------- F2 契约

def test_f2_return_via_offsets_expansion_contract():
    """F2 枚举域契约：确定性；全候选 ∈ [D3 2r+R5, R4 上限]；落 pitch/2 子
    栅格；16 方向三族（轴向/对角/马步）；首候选=最小距离马步 (1.0,0.5)
    （1.118 ≥ 缺省 D3 1.1）；旧 0.25mm/8 向域（min_hole 1.1 与 0.8 两组参数）
    是新域子集（约束零放松 + 域扩容逐项钉）。"""
    for min_hole in (1.1, 0.8):
        offs = _return_via_offsets(min_hole, 2.0, 0.25)
        assert offs == _return_via_offsets(min_hole, 2.0, 0.25)
        for dx, dy in offs:
            d = math.hypot(dx, dy)
            assert min_hole - 1e-9 <= d <= 2.0 + 1e-9
            assert abs(dx / 0.125 - round(dx / 0.125)) < 1e-9
            assert abs(dy / 0.125 - round(dy / 0.125)) < 1e-9
        legacy = _legacy_return_via_offsets(min_hole, 2.0, 0.25)
        assert set(legacy) <= set(offs)          # 旧域 ⊆ 新域（零放松）
        assert len(offs) > len(legacy)           # 域扩容
    offs = _return_via_offsets(1.1, 2.0, 0.25)
    assert offs[0] == (1.0, 0.5)                 # 马步族 1.118 最小距离环
    assert (0.5, 1.0) in offs and (1.0, 0.5) in offs   # 双侧马步角域在场
    assert len(offs) == 84                       # 24（旧）→ 84（16 方向×细档）
    assert len(_return_via_offsets(0.8, 2.0, 0.25)) == 108   # pmod 缺省口径
    # 方向族完整：轴向/对角/马步三族代表点全部在场
    for spot in ((1.125, 0.0), (0.875, 0.875), (1.0, 0.5), (0.5, 1.0),
                 (1.75, 0.875), (2.0, 0.0), (1.25, 1.25)):
        assert spot in offs, spot


def test_f2_placement_first_ring_blocked_expanded_hits():
    """placement 场景（F2 核心验收）：过渡孔 T=(10,5) 周围以他网已提交孔点
    封锁旧 0.25mm/8 向枚举全域（逐项对照断言：24 个旧候选经 via_blocked 全灭），
    扩容域命中马步候选 (9,5.5)（第一有效候选胜，确定性）。"""
    ctx = _Context(_plain_board("u5-f2-place", x_max=16.0, y_max=10.0))
    t = (10.0, 5.0)
    # 封锁孔位（T 相对偏移）：每枚距全部旧候选 <1.1（D3 封锁），且距幸存
    # 新候选 (−1,+0.5) ≥1.1、距桩段 T→R* ≥0.8（F1 孔铜障碍不误封桩段）
    blockers = [
        (-2.15, -0.35),   # 旧轴向左环 (−1.25/−1.5/−1.75, 0)
        (-1.9, 1.6),      # 旧对角左上 (−1,1), (−1.25,1.25)
        (2.0, 0.9),       # 新马步 (1,+0.5)（旧域外、排序在幸存者前 → 须封）
        (2.0, -0.9),      # 新马步 (1,−0.5)（同上）
        (1.625, 0.6),     # 旧轴向右环 (1.25/1.5/1.75/2, 0)
        (1.85, 1.15),     # 旧对角右上 (1,1), (1.25,1.25)
        (1.85, -1.15),    # 旧对角右下 (1,−1), (1.25,−1.25)
        (0.6, 1.625),     # 旧轴向上环 (0, 1.25..2)
        (0.6, -1.625),    # 旧轴向down环 (0, −1.25..−2)
        (-1.15, -1.85),   # 旧对角左下 (−1,−1), (−1.25,−1.25)
        (-2.6, 0.6),      # 旧轴向 (−2, 0)
    ]
    for bx, by in blockers:
        ctx.via_points.append(("OTHR", "PT-OTH", (t[0] + bx, t[1] + by)))
    # 对照断言：旧枚举域逐项全灭（经 via_blocked 的 D3 封锁）
    legacy = _legacy_return_via_offsets(1.1, 2.0, 0.25)
    assert len(legacy) == 24
    for dx, dy in legacy:
        p = (t[0] + dx, t[1] + dy)
        reason = ctx.via_blocked(p, "N1")
        assert reason is not None, ("旧域候选未被封锁", (dx, dy), reason)
    # 扩容域命中：第一有效候选 = 马步 (−1,+0.5)（1.118 ≥ D3 1.1）
    res = _place_return_via(ctx, t, "N1", "PT-P1", 0.2,
                            ["F.Cu", "B.Cu"], [t])
    assert res == (9.0, 5.5)
    # 幸存者合法性复核：D3 对 T 与全部封锁孔点、桩段双侧相连边全过
    assert clr.point_point(res, t) >= 1.1 - 1e-9
    assert all(clr.point_point(res, q) >= 1.1 - 1e-9
               for _n, _p, q in ctx.via_points)


def test_f2_placement_no_candidates_fail_closed():
    """扩容不放松：枚举域内确无有效位时 _place_return_via 仍返回 None
    （R4/D3 失败语义保持，fail-closed 不造假）。"""
    ctx = _Context(_plain_board("u5-f2-none", x_max=6.0, y_max=6.0))
    # 全部 84 候选位播他网孔点（workbook 内逐一封锁）
    for dx, dy in _return_via_offsets(1.1, 2.0, 0.25):
        ctx.via_points.append(("OTHR", "PT-OTH", (3.0 + dx, 3.0 + dy)))
    assert _place_return_via(ctx, (3.0, 3.0), "N1", "PT-P1", 0.2,
                             ["F.Cu", "B.Cu"], [(3.0, 3.0)]) is None


# ---------------------------------------------------------------- 确定性

@pytest.mark.parametrize("builder", [_seam_detour_board, _via_seal_board])
def test_double_run_byte_equal(builder):
    """确定性红线：两夹具板同输入双跑 canonical 字节等（含协商日志与 per_net；
    FAILED 板对整结果字典比对）。"""
    board = _board(builder)
    r1 = execute_candidate(board, _cand(board))
    r2 = execute_candidate(board, _cand(board))
    assert r1["verdict"] == r2["verdict"]
    assert canonical.canonical_json(r1) == canonical.canonical_json(r2)
    assert r1["negotiation_log"] == r2["negotiation_log"]
    assert r1["per_net"] == r2["per_net"]
