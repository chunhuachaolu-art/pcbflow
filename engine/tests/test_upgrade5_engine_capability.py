# -*- coding: utf-8 -*-
"""升级件⑤-F4 测试（2026-09-14，引擎搜索能力三件：F4a/F4b/F4c）。

A 层真实板全链重跑 0/7 SAT（out/v5-p5/trial/final-g1-assessment.md，只读参考）
四类失败签名的本件修复与钉死（F1 孔铜入障碍 / F3 候选轮换已落在
executor 0.3.0，本件在其上收口 ⑤，executor 0.3.0→0.4.0）：

- **F4a 细化层级扩展**：尝试阶梯追加 0.0625mm 细档（阶段序=追加在既有阶段
  之后；总预算确定性再分配保持 106/网：两个 48 计划逃逸块各修剪为 40——
  r3 大位移档 8 向→4 轴向，保留计划相对序不变；既有位 1..10 逐位不动，
  ④「attempt6 细化 0.125 过门」钉零翻转由 test_upgrade4 继续承钉）。细档
  搜索=确定性限域窗口（工作区原点 lattice 子矩形，窗口外邻边剪枝、边合法性
  谓词零改动）。
- **F4b 逃逸强化**：细档逃逸（起点侧 r1×8 向、终点侧 r1×4 轴向）=端点邻域
  0.0625mm 粒度重锚候选；逃逸×细化交错（细档逃逸即 0.0625 栅格整网 A*，
  追加在细化档之后成组执行）。
- **F4c rip-up-and-retry（有界、确定性）**：耗尽后确定性阻塞集（提交序贪心
  +影子剪枝）→ 快照 → rip（ctx.rip_net）→ N fresh 106 阶梯重布 → 被 rip 网
  按原提交序 fresh 20 计划前缀重布；任何重布失败 → 回滚并下一轮；每网 ≤2 轮、
  每候选全局 ≤8。全部 rip 事件逐条入 negotiation_log（只增行不改行，
  "FAILED after N attempts"/"exhaustion-cause=" 既有串格式向后兼容）；新归因类
  ripup-reroute-failed / ripup-exhausted 扩展分类序。

夹具（全部内联构造，零 out/ 写入、零 board 文件新增；F12 先例）对应四类
真实签名，各配**改造前复现对照**（旧 106 阶梯逐字复制 + rip-up 关闭，
monkeypatch 注入，证明测试承重）：
① f4-endpoint-seal（atmega 端点吸附出边全封）——修后细档布通；
② f4-partial-seal（stm32 首栅格部分段被封 F.Cu）——修后 attempt 91 布通；
③ f4-dense-first（dc-scm 稠密多焊盘网首网耗尽）——如实归因
   obstacle-dense（归因串精确钉），无已布网可 rip、零开销；
④ f4-ripup-ok / f4-ripup-fail / f4-ripup-stillsealed（rip-up 承重三态：
   双网布通 / ripup-reroute-failed / ripup-exhausted）。

红线自检：零网络、零 LLM API、零 kicad-cli；只动 v5/executor.py + tests/；
v5/route_check.py/schema/datasets/tools/ 零触碰；holdout 台账零接触；
确定性：全部夹具同输入双跑 canonical 字节等（含 rip-up 路径）。
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from v5 import canonical  # noqa: E402
from v5.board import compute_board_sha256, load_board  # noqa: E402
from v5 import executor as ex  # noqa: E402
from v5.executor import (  # noqa: E402
    _FINE_WINDOW_MARGIN_MM, _RIPUP_ESCAPE_REACH_MM,
    _RIPUP_MAX_ROUNDS_PER_NET, _RIPUP_MAX_TOTAL_PER_CANDIDATE,
    _RIPUP_REROUTE_MAX_PLANS, _Context, _RouteCopper, _attempt_plans,
    execute_candidate)
from v5.route_check import check_routes  # noqa: E402


# ---------------------------------------------------------------- 板构造

_HR = {
    "R1": {"floor_mm": 0.3, "k_a": 0.4},
    "R2": {"max_parallel_mm": 5.0, "min_distance_mm": 3.0},
    "R3": {"unsplittable": True},
    "R4": {"max_distance_mm": 2.0, "return_via_required": True},
    "R5": {"min_clearance_mm": 0.5},
    "R6": {"keepout_zones_forbidden": True, "plane_forbidden": True},
}


def _part(pid, a, b, ptype="MISC", layer="F.Cu", width=0.2, pads=None,
          **geo):
    g = {"endpoints": [list(a), list(b)]}
    if pads is not None:
        g["pad_terminals"] = pads
    g.update(geo)
    return {"partition_id": pid, "ptype": ptype, "layer_policy": layer,
            "planned_width": width, "current_a": 0, "geometry": g,
            "speed_class": "low_speed",
            "width_prior": {"w_min": width, "w_max": 0.4}}


def _net(nid, pids):
    return {"net_id": nid, "net_class": "MISC", "partitions": list(pids)}


def _mk(board_id, ws, parts, nets, zones=None):
    board = {
        "schema_version": "v5.board.v1", "board_id": board_id,
        "stackup": [{"id": "F.Cu", "kind": "signal",
                     "preferred_direction": "any", "available": True}],
        "workspace": ws,
        "zones": zones or [], "partitions": parts, "nets": nets,
        "hard_rules": dict(_HR),
        "principle_registry": [],
        "provenance": {"source_type": "synthetic", "adapter": "hand",
                       "source_uri":
                       "tests/test_upgrade5_engine_capability.py",
                       "source_sha256": "0" * 64},
    }
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    return load_board(board)


def _cand(board, order=None):
    parts = [p["partition_id"] for p in board["partitions"]]
    return {"candidate_id": "C-F4", "arm": "no-principle",
            "provenance": {"generator": "hand", "rules_consumed": [],
                           "compiled_sha256": "0" * 64},
            "route_order": order or parts,
            "layer_assignment": {p["partition_id"]: "F.Cu"
                                 for p in board["partitions"]},
            "polylines": {}, "generation_trace": []}


# 端点焊盘（D1 pad_terminals：circle r=0.25，F.Cu）
_PADS = [{"endpoint": 0, "shape": "circle", "size_mm": [0.5],
          "layers": ["F.Cu"]},
         {"endpoint": 1, "shape": "circle", "size_mm": [0.5],
          "layers": ["F.Cu"]}]


def _endpoint_seal_board():
    """① f4-endpoint-seal（atmega 签名）：三面铜带盒封死端点 a=(2,2.1875)
    的吸附节点粗档全部出边（盒壁 R5 光晕交叠），唯一出口=slot 行
    y∈[2.16,2.2]（0.0625-lattice 行 y=2.1875，粗档 lattice 行 2.0/2.25 全被
    盒壁 R5 封）——改造前全阶梯耗尽 endpoint-sealed；修后 F4a 细化@0.0625
    （a 恰在 0.0625 lattice 上、零部分段）沿 slot 行布通。
    ⑥ D6-3 钉值翻转披露（2026-09-17）：goal 端点原 (4.875, 2.1875) 距右板边
    仅 0.125mm——⑥ 世界模型板边禁布带（workspace 内缩 0.2mm）下如实拒布
    （端点入带=直连部分段必然触带， exhaustion-cause=edge-clearance；该拒布
    行为由 tests/test_wave6_edge_clearance.py 专钉）。goal 内移至 4.75
    （距边 0.25mm，0.25/0.0625 栅格均在格上）以保本件承重语义：端点被封于
    铜带盒而非板边，F4a/F4b 细档破封回归证明不变。"""
    parts = [
        _part("PT-L", (0.95, 0.5), (0.95, 3.4), ptype="BUS",
              copper_band=[0.6, 1.3], occupancy_mm=0.7),    # x∈[0.6,1.3]
        _part("PT-B", (0.6, 1.08), (4.5, 1.08), ptype="BUS",
              copper_band=[0.5, 1.66], occupancy_mm=1.16),  # y∈[0.5,1.66]
        _part("PT-T", (0.6, 3.05), (4.5, 3.05), ptype="BUS",
              copper_band=[2.7, 3.4], occupancy_mm=0.7),    # y∈[2.7,3.4]
        _part("PT-A", (2.0, 2.1875), (4.75, 2.1875)),
    ]
    nets = [_net("NL", ["PT-L"]), _net("NB", ["PT-B"]),
            _net("NT", ["PT-T"]), _net("NA", ["PT-A"])]
    return _mk("f4-endpoint-seal", {"x_min": 0.0, "y_min": 0.0,
                                    "x_max": 5.0, "y_max": 3.4},
               parts, nets)


def _partial_seal_board():
    """② f4-partial-seal（stm32 签名）：端点 a=(1.0625,2.0625) 在 0.25/0.125
    栅格吸附后，精确端点→首栅格的部分段斜穿 K1/K2 禁布小盒（bbox 间隙 ≤0）→
    「端点→首栅格部分段被封（F.Cu）」；a 在 0.0625 lattice 上=细档零部分段，
    上升一档后沿 y=2.125 行（K1-K3 上方缝隙）布通；上下 ROUTED 墙夹出唯一
    水平带（粗档可走行全被 K3/墙封）。改造前全阶梯耗尽；修后 attempt 91 布通。"""
    kos = [{"zone_id": "K1", "kind": "keepout", "layers": "all",
            "rect": {"x_min": 0.98, "y_min": 1.99, "x_max": 1.045,
                     "y_max": 2.045}},
           {"zone_id": "K2", "kind": "keepout", "layers": "all",
            "rect": {"x_min": 1.085, "y_min": 2.085, "x_max": 1.115,
                     "y_max": 2.115}},
           {"zone_id": "K3", "kind": "keepout", "layers": "all",
            "rect": {"x_min": 1.10, "y_min": 1.99, "x_max": 1.18,
                     "y_max": 2.07}},
           {"zone_id": "K4", "kind": "keepout", "layers": "all",
            "rect": {"x_min": 1.02, "y_min": 2.08, "x_max": 1.055,
                     "y_max": 2.11}}]
    parts = [
        _part("PT-WB", (0.5, 1.5), (8.0, 1.5), ptype="ROUTED"),
        _part("PT-WT", (0.5, 2.65), (8.0, 2.65), ptype="ROUTED"),
        _part("PT-S", (1.0625, 2.0625), (7.0, 2.0)),
    ]
    nets = [_net("NWB", ["PT-WB"]), _net("NWT", ["PT-WT"]),
            _net("NS", ["PT-S"])]
    return _mk("f4-partial-seal", {"x_min": 0.0, "y_min": 0.0,
                                   "x_max": 8.0, "y_max": 4.0},
               parts, nets, zones=kos)


def _dense_first_board():
    """③ f4-dense-first（dc-scm 签名）：首网 GND（双 pad 端子网）必穿稠密
    交错焊盘墙（4 行×~50 枚 r=0.25 pad、行距 0.6/列距 0.75 交错——中心线需
    距全部焊盘心 ≥0.75，行间/列间/对角缝隙均 <1.5mm 直径）；首网耗尽时无
    已布网可 rip（阻塞集空）→ 如实 FAILED，归因串 obstacle-dense 精确钉；
    rip-up 零开销（无 ripup 行）。"""
    parts = [_part("PT-G", (5.0, 0.25), (5.0, 3.95), pads=_PADS)]
    nets = [_net("GND", ["PT-G"])]
    k = 0
    for ri, y in enumerate((1.2, 1.8, 2.4, 3.0)):
        for j in range(13):
            x = 0.4 + 0.75 * (j + (ri % 2) * 0.5)
            if not (0.2 <= x <= 9.8):
                continue
            k += 1
            pid = "PT-P%d" % k
            parts.append(_part(pid, (x, y), (x + 0.4, y), pads=_PADS))
            nets.append(_net("NP%d" % k, [pid]))
    return _mk("f4-dense-first", {"x_min": 0.0, "y_min": 0.0,
                                  "x_max": 10.0, "y_max": 4.2},
               parts, nets)


def _ripup_ok_board():
    """④a f4-ripup-ok：A=(5,1.5)-(5,8.5) 竖线先布；B=(2,5)-(8,5) 直径路径
    与 A 正交相穿、上下 R6 禁布条封死绕行（A 竖线端点距禁布条缝 <0.5）→
    B 常规耗尽；rip-up：rip A → B 布通 → A 原序重布（西绕 x=1.5 竖腿，
    距 B 端点恰 0.5=R5 非违例）→ 双网布通。"""
    kos = [{"zone_id": "K1", "kind": "keepout", "layers": "all",
            "rect": {"x_min": 0.0, "y_min": 0.0, "x_max": 10.0,
                     "y_max": 1.2}},
           {"zone_id": "K2", "kind": "keepout", "layers": "all",
            "rect": {"x_min": 0.0, "y_min": 8.8, "x_max": 10.0,
                     "y_max": 10.0}}]
    parts = [_part("PT-A", (5.0, 1.5), (5.0, 8.5)),
             _part("PT-B", (2.0, 5.0), (8.0, 5.0))]
    nets = [_net("NA", ["PT-A"]), _net("NB", ["PT-B"])]
    return _mk("f4-ripup-ok", {"x_min": 0.0, "y_min": 0.0,
                               "x_max": 10.0, "y_max": 10.0},
               parts, nets, zones=kos)


def _ripup_fail_board():
    """④b f4-ripup-fail：同 ④a + 东西 R6 竖墙（x≤2.3 / x≥7.7，y∈[1.3,8.7]）
    封死 A 重布的两侧绕行腿 → rip 后 B 布通但 A 重布耗尽 → 回滚 ×2 轮 →
    如实 FAILED，exhaustion-cause=ripup-reroute-failed（被 rip 网 NA 重布
    失败+cause）。"""
    kos = [{"zone_id": "K1", "kind": "keepout", "layers": "all",
            "rect": {"x_min": 0.0, "y_min": 0.0, "x_max": 10.0,
                     "y_max": 1.2}},
           {"zone_id": "K2", "kind": "keepout", "layers": "all",
            "rect": {"x_min": 0.0, "y_min": 8.8, "x_max": 10.0,
                     "y_max": 10.0}},
           {"zone_id": "K3", "kind": "keepout", "layers": "all",
            "rect": {"x_min": 0.0, "y_min": 1.3, "x_max": 2.3,
                     "y_max": 8.7}},
           {"zone_id": "K4", "kind": "keepout", "layers": "all",
            "rect": {"x_min": 7.7, "y_min": 1.3, "x_max": 10.0,
                     "y_max": 8.7}}]
    parts = [_part("PT-A", (5.0, 1.5), (5.0, 8.5)),
             _part("PT-B", (2.5, 5.0), (7.5, 5.0))]
    nets = [_net("NA", ["PT-A"]), _net("NB", ["PT-B"])]
    return _mk("f4-ripup-fail", {"x_min": 0.0, "y_min": 0.0,
                                 "x_max": 10.0, "y_max": 10.0},
               parts, nets, zones=kos)


def _ripup_stillsealed_board():
    """④c f4-ripup-stillsealed：B 的真阻断=固定 ROUTED 斜墙 (4.9,1.3)-
    (5.1,8.7)（封死全部可穿 y 带）；A=(3,2)-(3,8) 在 B 失败走廊内（可 rip
    但非根因）→ rip 后 B 仍耗尽 → 2 轮轮尽 → 如实 FAILED，
    exhaustion-cause=ripup-exhausted（预算语义）。"""
    kos = [{"zone_id": "K1", "kind": "keepout", "layers": "all",
            "rect": {"x_min": 0.0, "y_min": 0.0, "x_max": 10.0,
                     "y_max": 1.2}},
           {"zone_id": "K2", "kind": "keepout", "layers": "all",
            "rect": {"x_min": 0.0, "y_min": 8.8, "x_max": 10.0,
                     "y_max": 10.0}}]
    parts = [_part("PT-A", (3.0, 2.0), (3.0, 8.0)),
             _part("PT-B", (2.0, 5.0), (8.0, 5.0)),
             _part("PT-W", (4.9, 1.3), (5.1, 8.7), ptype="ROUTED")]
    nets = [_net("NA", ["PT-A"]), _net("NB", ["PT-B"]),
            _net("NW", ["PT-W"])]
    return _mk("f4-ripup-stillsealed", {"x_min": 0.0, "y_min": 0.0,
                                        "x_max": 10.0, "y_max": 10.0},
               parts, nets, zones=kos)


_BUILDERS = (_endpoint_seal_board, _partial_seal_board, _dense_first_board,
             _ripup_ok_board, _ripup_fail_board, _ripup_stillsealed_board)

_CACHE = {}


def _board(builder):
    if builder.__name__ not in _CACHE:
        _CACHE[builder.__name__] = builder()
    return _CACHE[builder.__name__]


# 改造前（executor/0.3.0）世界复制——对照断言的唯一事实源（旧 106 阶梯逐字
# 复制 + rip-up 关闭；monkeypatch 注入，F12 先例同款）。
def _legacy_attempt_plans():
    plans = [(v, 1.0, None) for v in ex._ATTEMPT_VARIANTS]
    plans += [(v, 0.5, None) for v in ex._ATTEMPT_VARIANTS]
    for scale in (1.0, 0.5):
        for side in ("start", "goal"):
            for rad in (1, 2, 3):
                for dx, dy in ex._ESCAPE_DIRS:
                    plans.append((ex._ESCAPE_VARIANT, scale,
                                  (side, (dx, dy), rad)))
    return plans


@pytest.fixture()
def legacy_world(monkeypatch):
    monkeypatch.setattr(ex, "_attempt_plans", _legacy_attempt_plans)
    monkeypatch.setattr(ex, "_ripup_retry",
                        lambda *a, **k: (None, None, 0))


# ---------------------------------------------------------------- F4a 契约

def test_f4a_ladder_contract():
    """F4a/F4b 阶梯契约：总预算 106/网（确定性再分配，不放宽）；既有位
    1..10 与 0.3.0 逐位相同（④「attempt6 细化 0.125 过门」钉零翻转的
    前提）；新细档追加在既有阶段之后；预算再分配表（40+40+4+12）钉死。"""
    legacy = _legacy_attempt_plans()
    plans = _attempt_plans()
    assert len(legacy) == 106 and len(plans) == 106
    assert plans[:10] == legacy[:10]          # 既有位逐位不动
    assert len(plans) <= 106                  # 预算纪律（不放宽）
    # 阶段序=追加在既有阶段之后：位 91..106 全部是新细档
    assert all(p[1] == 0.25 for p in plans[90:])
    assert all(p[1] != 0.25 for p in plans[:90])
    # 再分配：两逃逸块 48→40（r3 修剪），新细档 4+12
    assert sum(1 for p in plans if p[2] is None) == 14
    assert sum(1 for p in plans if p[2] is not None) == 92
    assert plans == _attempt_plans()          # 确定性


def test_f4a_fine_window_lattice():
    """细档限域窗口：确定性、覆盖端点与吸附锚点、夹紧工作区；栅格相位仍锚
    定工作区原点（同一 lattice——窗口只是子矩形剪枝，非换 lattice）。"""
    board = _board(_partial_seal_board)
    view = _Context(board).view
    a, b = (1.0625, 2.0625), (7.0, 2.0)
    w1 = ex._fine_window(view, a, b, a, b)
    assert w1 == ex._fine_window(view, a, b, a, b)
    x0, y0, x1, y1 = view.workspace
    assert x0 <= w1[0] and y0 <= w1[1] and w1[2] <= x1 and w1[3] <= y1
    assert w1[0] <= a[0] and w1[1] <= a[1] and w1[2] >= b[0] and w1[3] >= b[1]
    # 外扩=1.0mm（运行时守门：全板细搜 16× 代价裁剪为窗口局部细化）
    assert w1[0] == pytest.approx(a[0] - _FINE_WINDOW_MARGIN_MM)
    # 逃逸锚点平移后窗口随之平移（覆盖锚点）
    w2 = ex._fine_window(view, a, b, (a[0] - 0.0625, a[1]), b)
    assert w2[0] == pytest.approx(a[0] - 0.0625 - _FINE_WINDOW_MARGIN_MM)


def test_f4c_budget_constants_disclosed():
    """F4c/R2 预算常量（披露于 executor docstring 与本钉）：每网 ≤5 轮
    （R2 W-1：0.6.1 值 2）、每候选全局 ≤12（0.6.1 值 8；带值扫描候选 12/16
    缺省待主审复核裁定）、被 rip 网重布前缀 30（0.6.1 值 20）、探针预算
    B=3（R2 W-4）、联合因子 2（R2 W-2）、逃逸邻域 reach 0.75、细档窗口
    外扩 1.0。"""
    assert _RIPUP_MAX_ROUNDS_PER_NET == 5
    assert _RIPUP_MAX_TOTAL_PER_CANDIDATE == 12
    assert _RIPUP_REROUTE_MAX_PLANS == 30
    assert ex._RIPUP_PROBE_BUDGET == 3
    assert ex._RIPUP_JOINT_COST_FACTOR == 2
    assert _RIPUP_ESCAPE_REACH_MM == 0.75
    assert _FINE_WINDOW_MARGIN_MM == 1.0


# ---------------------------------------------------------------- ① 端点全封

def test_f4_endpoint_seal_prefix_world_reproduction(legacy_world):
    """改造前复现对照（承重证明）：旧 106 阶梯 + 无 rip-up → ①板 FAILED、
    exhaustion-cause=endpoint-sealed——证明修后布通确为 F4a/F4b 细档所致
    而非板巧合。"""
    res = execute_candidate(_board(_endpoint_seal_board),
                            _cand(_board(_endpoint_seal_board)))
    assert res["verdict"] == "FAILED" and res["routes"] is None
    causes = [l for l in res["negotiation_log"]
              if "exhaustion-cause=" in l]
    assert causes == ["net=NA partition=PT-A exhaustion-cause="
                      "endpoint-sealed（端点吸附节点出边全封，逃逸/细化类）"]
    assert not any("ripup" in l for l in res["negotiation_log"])


def test_f4_endpoint_seal_fixed_routes_via_fine_tier():
    """修后：①板 ROUTED——提交计划落在 0.0625 细档（F4a 细化/F4b 细档逃逸，
    追加在既有阶段之后的阶段组），全链 feasible（route_check 判定零改动）。"""
    board = _board(_endpoint_seal_board)
    res = execute_candidate(board, _cand(board))
    assert res["verdict"] == "ROUTED" and res["routes"] is not None
    committed = [l for l in res["negotiation_log"] if "committed attempt" in l]
    assert any("pitch=0.0625" in l for l in committed)
    assert check_routes(board, res["routes"])["feasible"] is True
    by_net = {pn["net_id"]: pn for pn in res["per_net"]}
    assert by_net["NA"]["status"] == "routed"
    # negotiation_log 向后兼容：既有行格式（partition committed fixed-shape）
    assert any(l.startswith("partition=PT-L committed fixed-shape (ribbon)")
               for l in res["negotiation_log"])


# ---------------------------------------------------------------- ② 部分段被封

def test_f4_partial_seal_prefix_world_reproduction(legacy_world):
    """改造前复现对照：旧阶梯 → ②板 FAILED 且日志含 stm32 签名串
    「端点→首栅格部分段被封（F.Cu）」（attempt 逐条留痕）。"""
    res = execute_candidate(_board(_partial_seal_board),
                            _cand(_board(_partial_seal_board)))
    assert res["verdict"] == "FAILED"
    partial = [l for l in res["negotiation_log"] if "部分段被封" in l]
    assert partial
    assert all("attempt=" in l and "F.Cu" in l for l in partial)
    assert not any("ripup" in l for l in res["negotiation_log"])


def test_f4_partial_seal_fixed_routes_at_fine_refine():
    """修后：②板 ROUTED 且提交=位 91（新细化@0.0625 首计划，F4a 主解）；
    全链 feasible。"""
    board = _board(_partial_seal_board)
    res = execute_candidate(board, _cand(board))
    assert res["verdict"] == "ROUTED"
    by_net = {pn["net_id"]: pn for pn in res["per_net"]}
    assert by_net["NS"]["status"] == "routed"
    assert by_net["NS"]["attempts"] == 91      # 位 91 = 新细化档首计划
    committed = [l for l in res["negotiation_log"] if "committed attempt" in l]
    assert any(l.startswith("net=NS partition=PT-S committed attempt=91 "
                            "variant=prefer+r2-near+via-priced pitch=0.0625")
               for l in committed)
    assert check_routes(board, res["routes"])["feasible"] is True


# ---------------------------------------------------------------- ③ 稠密首网

def test_f4_dense_first_net_exhaustion_honest_attribution(legacy_world,
                                                          monkeypatch):
    """改造前复现对照 + 修后如实归因（③「修或如实归因均可但归因串须精确」）：
    首网 GND 在稠密多焊盘场中全阶梯耗尽（新旧世界一致 FAILED——③的修复
    通道是 F4c rip-up，而首网无已布网可 rip，阻塞集空、零开销直落）；
    归因串精确=obstacle-dense 兜底类；无任何 ripup 行。

    V5-EXECUTOR-ENG-R1 翻新披露（2026-10-02）：本板焊盘场分区 56 个端点行
    被 W-1 SC-1 事前判定为真密封（route_order 首封=PT-P6/ep1；独立
    distance_to 复核全部点位 <R5−EPS；判定器关停后 PT-P6 首位 106 阶梯仍
    耗尽=伪证测试在案）——默认路径在 PT-P6 短路收口（板级 FAILED 不变、
    GND 穷举面不再可达），GND obstacle-dense 归因钉改以判定器关停
    （_preflight_seal_shortcircuit no-op）跑原断言。"""
    board = _board(_dense_first_board)
    # 默认路径（0.9.0）：SC-1 事前短路收口（首封=route_order 序 PT-P6）
    res = execute_candidate(board, _cand(board))
    assert res["verdict"] == "FAILED" and res["routes"] is None
    by_net = {pn["net_id"]: pn for pn in res["per_net"]}
    assert by_net["NP6"]["status"] == "failed"
    assert by_net["NP6"]["attempts"] == 0
    assert any("net=NP6 partition=PT-P6 "
               "exhaustion-cause=sealed-short-circuit" in l
               for l in res["negotiation_log"])
    # 判定器关停（0.8.0 穷举路径）：GND 如实归因原钉值逐字保留
    monkeypatch.setattr(ex, "_preflight_seal_shortcircuit",
                        lambda *a, **k: None)
    res = execute_candidate(board, _cand(board))
    assert res["verdict"] == "FAILED" and res["routes"] is None
    by_net = {pn["net_id"]: pn for pn in res["per_net"]}
    assert by_net["GND"]["status"] == "failed"
    # 阶梯全量耗尽（吸附等价计划去重不计 attempts：新旧世界 92/94）
    assert by_net["GND"]["attempts"] >= 90
    causes = [l for l in res["negotiation_log"] if "exhaustion-cause=" in l]
    assert causes == ["net=GND partition=PT-G exhaustion-cause="
                      "obstacle-dense（障碍稠密兜底类）"]
    assert not any("ripup" in l for l in res["negotiation_log"])


# ---------------------------------------------------------------- ④ rip-up

def test_f4_ripup_prefix_world_reproduction(legacy_world):
    """改造前复现对照（④a）：旧世界无 rip-up → A 布通、B 常规耗尽 FAILED
    （零 ripup 行）——证明修后双网布通确为 F4c 所致。"""
    res = execute_candidate(_board(_ripup_ok_board),
                            _cand(_board(_ripup_ok_board)))
    assert res["verdict"] == "FAILED" and res["routes"] is None
    by_net = {pn["net_id"]: pn for pn in res["per_net"]}
    assert by_net["NA"]["status"] == "routed"
    assert by_net["NB"]["status"] == "failed"
    assert by_net["NB"]["attempts"] == 106
    assert not any("ripup" in l for l in res["negotiation_log"])


def test_f4_ripup_success_routes_both_nets():
    """④a 修后（rip-up 承重主场景）：B 耗尽 → 阻塞集确定性选中 A → rip 后
    B 布通、A 按原序重布布通 → 双网 ROUTED；rip 事件逐条入日志；工件过
    route_check；per_net 合同（attempts 总额、negotiated=attempts>1）。"""
    board = _board(_ripup_ok_board)
    res = execute_candidate(board, _cand(board))
    assert res["verdict"] == "ROUTED" and res["routes"] is not None
    assert check_routes(board, res["routes"])["feasible"] is True
    by_net = {pn["net_id"]: pn for pn in res["per_net"]}
    assert by_net["NA"]["status"] == "routed"
    assert by_net["NB"]["status"] == "routed"
    assert by_net["NA"]["attempts"] == 2          # 初始 1 + 重布 1
    assert by_net["NB"]["attempts"] == 2          # 初始 106 阶梯内计 1 + 重布 1
    for pn in by_net.values():
        assert pn["negotiated"] == (pn["attempts"] > 1)
    log = res["negotiation_log"]
    assert any("ripup round=1 ripped=['NA']" in l for l in log)
    assert any("ripup round=1 committed" in l for l in log)
    # A 网重布后让位：两网铜 R5 分离由 route_check 可行性保证（已断言）


def test_f4_ripup_reroute_failed_honest_failed():
    """④b：rip 后 B 布通但 A 重布（30 计划前缀）被东西禁布墙封死 → 回滚
    ×5 轮 → 如实 FAILED + 新归因类 ripup-reroute-failed（被 rip 网+cause）。
    R2 翻转披露（0.6.1→0.7.0）：轮 2→5、前缀 20→30、W-3 波次+档位双导引序
    （单网阻塞集两序同形）；被 rip 网 attempts 失败不计入 N（0.6.1 口径）。"""
    board = _board(_ripup_fail_board)
    res = execute_candidate(board, _cand(board))
    assert res["verdict"] == "FAILED" and res["routes"] is None
    by_net = {pn["net_id"]: pn for pn in res["per_net"]}
    assert by_net["NA"]["status"] == "routed"     # 回滚恢复 A 原布线
    assert by_net["NB"]["status"] == "failed"
    assert by_net["NB"]["attempts"] == 116        # 106 + 5 轮×2 序×(N 重布 1 布通)
    log = res["negotiation_log"]
    causes = [l for l in log if "exhaustion-cause=" in l]
    assert causes == ["net=NB partition=PT-B exhaustion-cause="
                      "ripup-reroute-failed（被 rip 网 NA 重布失败：A* 搜索"
                      "空间耗尽（障碍/容量/敏感约束下无路））"]
    assert len([l for l in log if "ripped=['NA']" in l]) == 5
    assert len([l for l in log if "reroute of ripped net NA failed" in l]) == 10
    # W-3：导引序池逐序留痕（单网 wave/tier 同形；每轮各 1 行）
    assert len([l for l in log if "guide-order channel=wave" in l]) == 5
    assert len([l for l in log if "guide-order channel=tier" in l]) == 5
    # 回滚纪律：FAILED 行格式向后兼容（下游解析串）
    assert any(l.startswith("net=NB partition=PT-B FAILED after 116 attempts: ")
               for l in log)


def test_f4_ripup_budget_exhausted_honest_failed():
    """④c：真阻断=固定斜墙；可 rip 的 A 非根因 → rip 后 B 仍耗尽 → 每网
    5 轮轮尽 → 如实 FAILED + 新归因类 ripup-exhausted（N 全程 attempts
    总额 106+5×106 逐条留痕）。R2 翻转披露：轮 2→5（0.6.1=106+2×106=318）。"""
    board = _board(_ripup_stillsealed_board)
    res = execute_candidate(board, _cand(board))
    assert res["verdict"] == "FAILED" and res["routes"] is None
    by_net = {pn["net_id"]: pn for pn in res["per_net"]}
    assert by_net["NB"]["status"] == "failed"
    assert by_net["NB"]["attempts"] == 636        # 106 + 5×106 重布耗尽
    log = res["negotiation_log"]
    causes = [l for l in log if "exhaustion-cause=" in l]
    assert causes == ["net=NB partition=PT-B exhaustion-cause="
                      "ripup-exhausted（rip-up 5 轮仍耗尽，阻塞集=['NA']）"]
    assert any(l.startswith("net=NB partition=PT-B FAILED after 636 attempts: ")
               for l in log)


# ---------------------------------------------------------------- F4c 单元

def _commit_run(ctx, net_id, pid, layer, pts, k=0):
    entry = {"partition_id": pid, "net_id": net_id, "layer": layer,
             "polyline": [list(p) for p in pts], "width": 0.2,
             "transition_vias": [], "return_vias": []}
    copper = _RouteCopper(net_id, "route:%s:%s#%d" % (net_id, pid, k),
                          layer, pid, entry["polyline"], 0.2)
    ctx.commit_entries([entry], [copper])


def test_f4c_rip_net_and_snapshot_restore():
    """ctx.rip_net：route 铜/条目/障碍/孔点摘除 + 账本按固定铜基账重建；
    snapshot→rip→restore 后状态指纹与快照前逐字节一致（F4c 回滚底座；
    snapshot 升级为列表副本恢复——rip 收缩列表截断不可逆）。"""
    board = _board(_ripup_ok_board)
    ctx = _Context(board)
    _commit_run(ctx, "NA", "PT-A", "F.Cu", [(5.0, 1.5), (5.0, 8.5)])
    _commit_run(ctx, "NB", "PT-B", "F.Cu", [(2.0, 5.0), (8.0, 5.0)], k=1)
    assert len(ctx.route_coppers) == 2
    assert ctx.rip_net("NA") == 1
    assert len(ctx.route_coppers) == 1
    assert all(cu.net_id != "NA" for cu in ctx.route_coppers)
    assert all(e["net_id"] != "NA" for e in ctx.entries)
    assert all(vp[0] != "NA" for vp in ctx.via_points)
    assert all(ob.cu.net_id != "NA" for ob in ctx.obstacles
               if ob.cu.cid.startswith("route:"))
    state_before = ctx.state_key()
    snap = ctx.snapshot()
    ctx.rip_net("NB")
    assert len(ctx.route_coppers) == 0
    ctx.restore(snap)
    assert len(ctx.route_coppers) == 1
    assert ctx.state_key() == state_before
    # 幂等边界：无铜网 rip 返回 0
    assert ctx.rip_net("NA") == 0


def test_f4c_blocker_selection_deterministic():
    """阻塞集确定性（R2 W-2 翻转披露：提交序决胜废止→(联合评估分, id 字典序)
    冻结序）+ N 自身排除 + 失败走廊命中判定（直连段 width/2+R5 带）+ 重复
    求值逐项相等；区域外网不入集。NM1/NM2 同段数→字典序；NFAR 区域外
    （既非 hit 也非上位替代者——重布走廊无交叠）不入集。"""
    board = _board(_ripup_ok_board)
    ctx = _Context(board)
    # 提交序：先 M2 后 M1（0.6.1 提交序决胜的构造在 0.7.0 冻结序下=字典序）
    _commit_run(ctx, "NM2", "PT-A", "F.Cu", [(4.9, 4.0), (4.9, 6.0)])
    _commit_run(ctx, "NM1", "PT-B", "F.Cu", [(5.1, 4.0), (5.1, 6.0)], k=1)
    _commit_run(ctx, "NFAR", "PT-A", "F.Cu", [(0.5, 9.5), (1.0, 9.5)], k=2)
    got, geo = ex._ripup_blocker_ids(ctx, "NX", 0.2,
                                     (2.0, 5.0), (8.0, 5.0),
                                     ex._RIPUP_ESCAPE_REACH_MM)
    assert got == ["NM1", "NM2"]   # (cost,id) 冻结序；NFAR 区域外不入集
    assert set(geo) == {"NM1", "NM2"}
    again, geo2 = ex._ripup_blocker_ids(ctx, "NX", 0.2,
                                        (2.0, 5.0), (8.0, 5.0),
                                        ex._RIPUP_ESCAPE_REACH_MM)
    assert got == again and geo == geo2
    # W-2 联合重排退化开关：joint_factor=0 → 纯贪心 hits（同集同序）
    g0, _ = ex._ripup_blocker_ids(ctx, "NX", 0.2, (2.0, 5.0), (8.0, 5.0),
                                  ex._RIPUP_ESCAPE_REACH_MM, joint_factor=0)
    assert g0 == ["NM1", "NM2"]


# ---------------------------------------------------------------- 确定性

@pytest.mark.parametrize("builder", _BUILDERS)
def test_f4_double_run_byte_equal(builder):
    """确定性红线：六夹具同输入双跑 canonical 字节等（含 rip-up 路径与
    FAILED 世界）。"""
    board = _board(builder)
    r1 = execute_candidate(board, _cand(board))
    r2 = execute_candidate(board, _cand(board))
    assert r1["verdict"] == r2["verdict"]
    assert canonical.canonical_json(r1) == canonical.canonical_json(r2)
    assert r1["negotiation_log"] == r2["negotiation_log"]
    assert r1["per_net"] == r2["per_net"]


# ---------------------------------------------------------------- 日志兼容

@pytest.mark.parametrize("builder", _BUILDERS)
def test_f4_negotiation_log_backward_compat(builder):
    """negotiation_log 行格式向后兼容（只加不改）：每行均为 str；既有解析串
    「FAILED after N attempts」/「exhaustion-cause=」/「committed attempt=」
    「attempt=N variant=…」在出现处保持既有前缀格式；ripup 行为纯新增族。"""
    res = execute_candidate(_board(builder), _cand(_board(builder)))
    log = res["negotiation_log"]
    assert all(isinstance(l, str) for l in log)
    for l in log:
        if "exhaustion-cause=" in l:
            assert l.startswith("net=") and " partition=" in l
        if "FAILED after" in l:
            assert l.startswith("net=") and " attempts: " in l
        if "ripup" in l:
            assert l.startswith("net=") and " partition=" in l
    if res["verdict"] == "ROUTED":
        assert any(l.startswith("final route_check feasible=True")
                   for l in log)
