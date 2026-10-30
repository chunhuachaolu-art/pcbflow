# -*- coding: utf-8 -*-
"""test_exec_r3_pilot —— EXEC-R3 R3-1 第二刀回归（pilot 几何常数单源化）。

G1 applyConditions 对账面（GATE-G1-RULING.md §八 R3-1，applyConditions
R31-02/03/05）:
- R31-02 别名单源: TRACK_HALF_MM 由 adapter DEFAULT_WIDTH_PRIOR 的
  w_min/2.0 派生（IEEE754 /2 精确: 0.3/2.0 与 0.15 逐位相等）、
  EDGE_MARGIN_MM/HOLE_TO_HOLE_MM 为 v5.drc 单源别名; 板无关 VIA_RADIUS_MM
  第二源已删（符号不存在）。
- R31-03 via 半径携带: _obstacles 经 v5.kicad_export.via_model_params 单点
  取得并写入 obs["via_radius_mm"]; 他网 via 投影与 _via_blocked_at 候选
  半径消费同源同值、无 0.3 回退; 端点孔豁免 1e-6→1e-9（逐轴比较保持、
  via 面零豁免保持）。
- R31-05 合成验证: 1e-9 边界两侧豁免行为（(1e-9,1e-6] 带不再豁免）;
  默认板副本 + 实际他网 via + via_model{drill_mm 0.5, annular_mm 0.2} →
  半径/投影/候选阻挡消费同为 0.45，而旧实现为 0.3——**修真 bug 的非零
  漂移，单列不隐去、不宣称全板零漂移**; 默认板（无 via_model）半径仍
  0.3（缺省板零漂移）。

运行前提: 仓库根含 out/v5-p5/boards/badgeleds-do-electronics（默认板）。
"""
import copy
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from net_agent_pilot import pilot                    # noqa: E402

BOARD_DEFAULT = os.path.join(ROOT, "out", "v5-p5", "boards",
                             "badgeleds-do-electronics", "board.json")


# ---------------------------------------------------------------- R31-02 别名

def test_constants_are_single_source_aliases():
    """三个几何常数=活树单源引用（同值且派生逐位），板无关第二源已删。"""
    from v5 import drc
    from v5.adapters.kicad_adapter import DEFAULT_WIDTH_PRIOR
    assert pilot.TRACK_HALF_MM == DEFAULT_WIDTH_PRIOR["w_min"] / 2.0
    assert pilot.TRACK_HALF_MM == 0.15
    assert float(pilot.TRACK_HALF_MM).hex() == float(0.15).hex()  # 逐位
    assert pilot.EDGE_MARGIN_MM == drc.EDGE_CLEARANCE_MM == 0.2
    assert pilot.HOLE_TO_HOLE_MM == drc.HOLE_TO_HOLE_MM == 0.25
    # R31-02: 板无关 VIA_RADIUS_MM 第二源删除（符号不再可解析）
    assert not hasattr(pilot, "VIA_RADIUS_MM")


# ---------------------------------------------------------------- R31-03 携带

class _StubState(object):
    """最小态桩——只喂 _obstacles/_via_blocked_at 的孔豁免与 via 半径面
    （无焊盘/已布段/via; board 仅带 holes 与可选 via_model）。"""

    def __init__(self, board, net_eps):
        self.board = board
        self._net_eps = {k: [tuple(e) for e in v] for k, v in net_eps.items()}
        self.segs = {}
        self.vias = {}

    def net_partitions(self, net_id):
        return [net_id] if net_id in self._net_eps else []

    def known_partitions(self):
        return sorted(self._net_eps)

    def board_partition(self, pid):
        return {"geometry": {"pad_terminals": []}}

    def effective_endpoint_mm(self, pid):
        return list(self._net_eps[pid])


def _board_with_holes(hole_positions, drill_mm=0.6, via_model=None):
    board = {"holes": [{"pos_mm": [x, y], "drill_mm": drill_mm}
                       for x, y in hole_positions]}
    if via_model is not None:
        board["via_model"] = via_model
    return board


def _loop_state(board):
    from canvas.integration import build_state, make_loop_state
    return make_loop_state(build_state(
        board, BOARD_DEFAULT, board["provenance"]["board_sha256"]))


def test_exemption_tolerance_sites_all_1e9():
    """两处端点孔豁免（_obstacles 与 cmd_scan census）同步 1e-9 逐轴口径。"""
    src_path = os.path.join(ROOT, "net_agent_pilot", "pilot.py")
    with open(src_path, encoding="utf-8") as f:
        src = f.read()
    assert src.count("<= 1e-9 and abs(") == 2     # 两处同式
    assert "1e-6 and abs(" not in src             # 旧 1e-6 口径零残留


def test_endpoint_hole_exemption_1e9_boundary_two_sides():
    """R31-05: 1e-9 边界两侧合成——逐轴口径下 (1e-9,1e-6] 带不再豁免。"""
    holes_xy = [
        (5e-10, 0.0),    # 双轴 ≤1e-9 → 仍豁免（边界内）
        (0.0, 5e-10),    # 同上（y 轴）
        (1e-8, 0.0),     # x 轴入带 (1e-9,1e-6] → 不再豁免（旧 1e-6 会豁免）
        (0.0, 1e-8),     # y 轴入带
        (1e-8, 1e-8),    # 双轴入带
        (1e-8, 5e-10),   # x 入带、y 边界内 → 逐轴 AND → 不豁免
        (5.0, 5.0),      # 远离 → 从不豁免
    ]
    st = _StubState(_board_with_holes(holes_xy), {"N1": [(0.0, 0.0)]})
    obs = pilot._obstacles(st, "N1")
    assert obs["via_radius_mm"] == 0.3            # 桩板无 via_model → 缺省
    assert len(obs["holes_all"]) == 7             # 全量孔不过滤（via 面用）
    kept = {(h[0], h[1]) for h in obs["holes"]}
    assert len(kept) == 5
    for xy in [(1e-8, 0.0), (0.0, 1e-8), (1e-8, 1e-8),
               (1e-8, 5e-10), (5.0, 5.0)]:
        assert xy in kept                          # 带内/远离 → 走线面计入
    for xy in [(5e-10, 0.0), (0.0, 5e-10)]:
        assert xy not in kept                      # ≤1e-9 → 仍豁免


def test_via_face_zero_exemption_at_own_endpoint_hole():
    """R31-03: via 面零豁免保持——本网端点孔豁免只及走线面。"""
    st = _StubState(_board_with_holes([(0.0, 0.0)]), {"N1": [(0.0, 0.0)]})
    obs = pilot._obstacles(st, "N1")
    assert obs["holes"] == []                      # 走线面: 端点孔豁免
    assert len(obs["holes_all"]) == 1
    assert obs["via_radius_mm"] == 0.3
    assert pilot._via_blocked_at((0.0, 0.0), obs, "F.Cu", 0.5) == "hole"


def test_via_blocked_at_consumes_carried_radius():
    """R31-05: 候选 via 半径消费只读携带值——0.45 板判阈漂移单证。

    判阈 r+c+via_r: 新（携带 0.45）= 1.4，旧（字面 0.3）= 1.1；
    候选距 1.25 落在 (1.1, 1.4) → 非零漂移带（修真 bug 方向）。
    """
    c = 0.5
    obs = {"pads": [], "segs": [], "vias": [((0.0, 0.0), 0.45)],
           "holes": [], "holes_all": [], "zones": [],
           "via_radius_mm": 0.45}
    assert pilot._via_blocked_at((1.25, 0.0), obs, "F.Cu", c) == "via"
    assert not (1.25 < 0.3 + c + 0.3)              # 旧 0.3 阈不拦（机械账）
    assert pilot._via_blocked_at((1.45, 0.0), obs, "F.Cu", c) is None
    obs30 = dict(obs, vias=[((0.0, 0.0), 0.3)], via_radius_mm=0.3)
    assert pilot._via_blocked_at((1.25, 0.0), obs30, "F.Cu", c) is None


# ------------------------------------------------- R31-05 真板 via_model 探针

def test_default_board_via_radius_zero_drift():
    """默认板（无 via_model）: 半径缺省推导 0.3 == 旧 VIA_RADIUS_MM 字面量。"""
    board, _sha, _bp = pilot.load_board(BOARD_DEFAULT)
    assert "via_model" not in board
    st = _loop_state(board)
    obs = pilot._obstacles(st, "Net-(C1-Pad2)")
    assert obs["via_radius_mm"] == 0.3             # 零漂移（同值同源推导）
    assert obs["vias"] == []                       # 初始态无他网 via


def test_via_model_045_carried_radius_and_projection():
    """R31-05: 默认板副本 + via_model{drill 0.5, annular 0.2} + 实际他网 via:
    半径单源携带 0.45、他网 via 投影同值（旧实现 0.3——非零漂移单列披露）。"""
    board, _sha, _bp = pilot.load_board(BOARD_DEFAULT)
    board = copy.deepcopy(board)
    board["via_model"] = {"drill_mm": 0.5, "annular_mm": 0.2}
    st = _loop_state(board)
    net, foreign = "Net-(C1-Pad2)", "VCC"
    grid = tuple(st.effective_anchors(st.net_partitions(foreign)[0])[0])
    st._st.vias["r31-test-via"] = {"shape_id": "r31-test-via",
                                   "net_id": foreign, "grid": list(grid)}
    mm = st.lattice.to_mm(*grid)
    obs = pilot._obstacles(st, net)
    assert obs["via_radius_mm"] == 0.45            # drill/2+annular = 0.45
    assert obs["vias"] == [((mm[0], mm[1]), 0.45)]  # 投影半径=携带值（旧 0.3）
