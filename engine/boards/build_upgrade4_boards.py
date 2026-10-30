# -*- coding: utf-8 -*-
"""升级件④ D 层复现夹具构造器（三件；boards/d/；禁入任何验收门）。

三块板对应 P5② 批量暴露的三类 exec FAILED 失败模式（DISPATCH-LOG 2026-09-14），
全部为 D 层合成复现件（失败模式只从任务书描述复现，零 A 层接触）：

- d4-degenerate.kicad_pcb   模式A「端点退化重合」：两个单 pad 网（KiCad
  unconnected-(Fx-PadN) 占位网型，adapter 既定抽象=两端重合退化分区）+ 一条
  正常双 pad 网 SIG（其直连路线从其中一个退化焊盘点上穿过——钉住 route_check
  零长缝的「零铜展宽=无间距交互」语义：若退化 entry 被构造成点铜，SIG 直连线
  与该点 gap=0 < R5 0.5 判 infeasible；零长缝下 feasible）。
- d4-tight-door.board.v1.json    模式B「A* 搜索空间耗尽」根因=栅格分辨率：
  横墙留门，门净宽 1.2mm，R5=0.5 下可布中心线窗口 x∈[10.76,10.96]（宽 0.2），
  0.25mm 基线栅格在该窗口内无任何节点（10.75/11.0 均在窗外），0.125mm 细化
  栅格有节点 10.875——细化前无路、细化后可过（能力件：栅格细化阶梯）。
- d4-escape-seal.board.v1.json   模式C「焊盘逃逸被封」：分区端点邻域被既布铜
  封坏环合围（四段墙，仅右侧留 1.1mm 薄门——端点与所有墙保持 ≥0.6 距离，即
  端点阴影外存在物理绕行解），基线与相位栅格均无可过门中心线 ⇒ 5 变体全耗尽
  （改造前 FAILED）；升级件④尝试阶梯以细化栅格（0.125）从门中穿出布通
  （能力件：栅格细化 + 逃逸半径渐进/方向枚举阶梯披露）。

契约（对齐 boards/build_adversarial_boards.py 惯例）：
  - board 文件字节 = v5.canonical.canonical_json；board_sha256 先算好填；
    provenance：source_type=synthetic / adapter=hand /
    source_uri=boards/build_upgrade4_boards.py#<board_id> /
    source_sha256=构造函数源码文本 sha256（确定性披露）。
  - 确定性：无 wall-clock、无随机、无主机路径；双跑字节相等（tests 覆盖）。

用法：
  python boards/build_upgrade4_boards.py             # 写入 boards/d/
  python boards/build_upgrade4_boards.py <out_dir>   # 写入指定目录（测试用 tmp_path）
"""
import hashlib
import inspect
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from v5 import canonical                    # noqa: E402
from v5.board import compute_board_sha256   # noqa: E402

# V2 默认硬规则（取值照 tests/fixtures_v2.py 转录；按纪律不 import 之）
HARD_RULES = {
    "R1": {"floor_mm": 0.3, "k_a": 0.4},
    "R2": {"max_parallel_mm": 5.0, "min_distance_mm": 3.0},
    "R3": {"unsplittable": True},
    "R4": {"max_distance_mm": 2.0, "return_via_required": True},
    "R5": {"min_clearance_mm": 0.5},
    "R6": {"keepout_zones_forbidden": True, "plane_forbidden": True},
}

SIG = [{"id": "F.Cu", "kind": "signal", "preferred_direction": "any",
        "available": True}]


def _part(pid, a, b, ptype="MISC", layer="F.Cu", width=0.2, note=None):
    p = {"partition_id": pid, "ptype": ptype, "layer_policy": layer,
         "planned_width": width, "current_a": 0,
         "geometry": {"endpoints": [list(a), list(b)]},
         "speed_class": "low_speed",
         "width_prior": {"w_min": width, "w_max": 1.0}}
    if note is not None:
        p["note"] = note
    return p


def _net(nid, pids):
    return {"net_id": nid, "net_class": "MISC", "partitions": list(pids)}


def _finish(board):
    board["provenance"]["board_sha256"] = compute_board_sha256(board)
    return board


def build_tight_door_board():
    """模式B 夹具：栅格分辨率根因的 A* 耗尽（横墙 + 1.15mm 门）。

    几何核算（R5=0.5，中心线口径）：
    - 墙 L 折线 (0,8)→(10.33,8)、墙 R 折线 (11.48,8)→(20,8)：门净宽 1.15mm；
    - 过门中心线 x 须满足 x-10.33 ≥ 0.5 且 11.48-x ≥ 0.5 ⇒ x∈[10.83,10.98]；
    - 基线栅格 0.25（workspace 从 0 起）：节点 10.75/11.0 均在窗外；相位 0.5 变体
      （栅格平移 0.0625）节点 10.8125/11.0625 同样在窗外（对角边端点距墙端
      <0.5 亦被封）⇒ 5 变体全耗尽；
    - 细化栅格 0.125：节点 10.875 ∈ 窗口（两侧余量 0.545/0.605）⇒ 可布。
    """
    board = {
        "schema_version": "v5.board.v1",
        "board_id": "d4-tight-door",
        "stackup": SIG,
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 20.0, "y_max": 16.0},
        "zones": [],
        "partitions": [
            _part("PT-SIG", (5.0, 3.0), (15.0, 13.0)),
            _part("PT-WALL-L", (0.0, 8.0), (10.33, 8.0), ptype="ROUTED",
                  note="fixture: barrier wall left of door"),
            _part("PT-WALL-R", (11.48, 8.0), (20.0, 8.0), ptype="ROUTED",
                  note="fixture: barrier wall right of door"),
        ],
        "nets": [
            _net("SIG", ["PT-SIG"]),
            _net("WALL_L", ["PT-WALL-L"]),
            _net("WALL_R", ["PT-WALL-R"]),
        ],
        "hard_rules": HARD_RULES,
        "principle_registry": [],
        "provenance": {"source_type": "synthetic", "adapter": "hand",
                       "source_uri": "boards/build_upgrade4_boards.py#d4-tight-door",
                       "source_sha256": ""},
    }
    return _finish(board)


def build_escape_seal_board():
    """模式C 夹具：焊盘逃逸被封（端点邻域封坏环 + 单侧 1.1mm 薄门）。

    几何核算（R5=0.5；端点 a=(10.0,10.1) 吸附基线栅格点 p0=(10.0,10.0)）：
    - 封坏环（F.Cu 既布铜，四段合围、右侧留门）：
      W_B  (9.35,9.3)→(10.7,9.3)   封 下/下左/下右（0.45）
      W_L  (9.35,9.3)→(9.35,10.7)  封 左/上左/下左（0.4）
      W_T  (9.35,10.7)→(10.7,10.7) 封 上/上左/上右（0.45）
      W_RL (10.7,9.3)→(10.7,9.6)   门下唇（封右向低位出边）
      门 = x=10.7 线上 y∈(9.6,10.7) 净宽 1.1mm；
    - 基线栅格过门中心线窗口 y∈[10.1,10.2]，0.25 节点 10.0/10.25 均距门唇
      <0.5（0.403/0.453）、对角边同样被封；相位 0.5 变体（栅格平移 0.0625）
      节点 10.0625/10.3125 距门唇 0.476/0.4035 亦被封 ⇒ 5 变体全耗尽
      （改造前行为 = 「A* 搜索空间耗尽」，即焊盘逃逸方向单一被封的耗尽类）；
    - 细化栅格 0.125：水平边 y=10.125 过门（距下唇 0.5274/上唇 0.5799）⇒ 可布；
    - 端点 a 与所有墙距离 ≥0.6（a 阴影外——物理上存在经门绕行解）。
    """
    board = {
        "schema_version": "v5.board.v1",
        "board_id": "d4-escape-seal",
        "stackup": SIG,
        "workspace": {"x_min": 0.0, "y_min": 0.0, "x_max": 20.0, "y_max": 20.0},
        "zones": [],
        "partitions": [
            _part("PT-SIG", (10.0, 10.1), (14.0, 14.0)),
            _part("PT-W-B", (9.35, 9.3), (10.7, 9.3), ptype="ROUTED",
                  note="fixture: seal ring bottom"),
            _part("PT-W-L", (9.35, 9.3), (9.35, 10.7), ptype="ROUTED",
                  note="fixture: seal ring left"),
            _part("PT-W-T", (9.35, 10.7), (10.7, 10.7), ptype="ROUTED",
                  note="fixture: seal ring top"),
            _part("PT-W-RL", (10.7, 9.3), (10.7, 9.6), ptype="ROUTED",
                  note="fixture: seal ring door lower lip"),
        ],
        "nets": [
            _net("SIG", ["PT-SIG"]),
            _net("W_B", ["PT-W-B"]),
            _net("W_L", ["PT-W-L"]),
            _net("W_T", ["PT-W-T"]),
            _net("W_RL", ["PT-W-RL"]),
        ],
        "hard_rules": HARD_RULES,
        "principle_registry": [],
        "provenance": {"source_type": "synthetic", "adapter": "hand",
                       "source_uri": "boards/build_upgrade4_boards.py#d4-escape-seal",
                       "source_sha256": ""},
    }
    return _finish(board)


# 模式A 夹具：KiCad 源文本（numbered 网表；两个单 pad「unconnected-」占位网 +
# 一个双 pad 网 SIG；SIG 直连路线从 U3 退化焊盘点 (10,12) 上穿过，钉零长缝）。
D4_DEGENERATE_KICAD = """(kicad_pcb (version 20171130) (host pcbnew "(5.1.0)-1")
  (general (thickness 1.6))
  (layers (0 F.Cu signal) (31 B.Cu signal))
  (net 0 "")
  (net 1 "unconnected-(U2-Pad11)")
  (net 2 "unconnected-(U3-Pad2)")
  (net 3 "SIG")
  (module M:U2 (layer F.Cu) (at 10 10)
    (pad 11 smd rect (at 0 0) (size 1 1) (layers F.Cu) (net 1)))
  (module M:U3 (layer F.Cu) (at 10 12)
    (pad 2 smd rect (at 0 0) (size 1 1) (layers F.Cu) (net 2)))
  (module M:U1 (layer F.Cu) (at 0 0)
    (pad 1 smd rect (at 2 12) (size 1 1) (layers F.Cu) (net 3))
    (pad 2 smd rect (at 18 12) (size 1 1) (layers F.Cu) (net 3)))
)
"""


def main(out_dir=None):
    out_dir = out_dir or os.path.join(_ROOT, "boards", "d")
    os.makedirs(out_dir, exist_ok=True)
    written = []

    door = build_tight_door_board()
    seal = build_escape_seal_board()
    for board in (door, seal):
        src = inspect.getsource(globals()["build_%s_board"
                                          % board["board_id"][3:].replace("-", "_")])
        board["provenance"]["source_sha256"] = hashlib.sha256(
            src.encode("utf-8")).hexdigest()
        board["provenance"]["board_sha256"] = compute_board_sha256(board)
        path = os.path.join(out_dir, "%s.board.v1.json" % board["board_id"])
        with open(path, "wb") as f:
            f.write(canonical.canonical_json(board))
        written.append(path)

    path = os.path.join(out_dir, "d4-degenerate.kicad_pcb")
    with open(path, "wb") as f:
        f.write(D4_DEGENERATE_KICAD.encode("utf-8"))
    written.append(path)

    for path in written:
        print("wrote %s (%d bytes)" % (path, os.path.getsize(path)))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
