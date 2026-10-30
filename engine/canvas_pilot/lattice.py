# -*- coding: utf-8 -*-
"""lattice —— 画板整数格点阵定义（画板垄断坐标的单源）。

- pitch 缺省 0.5mm（任务书 §3: 由板 clearance 规则推导；R5.min_clearance_mm
  =0.5 → 单轨道 0.5 中心距下异网相邻轨不可布（0.3 线宽边距 0.2<0.5），隔一
  轨 1.0mm 边距 0.7≥0.5 可行——排序余量与可布性的张力即被测难度本体）。
- origin=workspace 下界外对齐 pitch 整数倍（floor），格点域覆盖板框。
- 端点锚: 分区端点 mm → 最近格点（snap）; 构造期检测锚冲突（fail-closed）。
"""
import math


class LatticeError(ValueError):
    pass


class Lattice(object):
    def __init__(self, pitch_mm, x0, y0, i_max, j_max):
        if not (pitch_mm > 0.0):
            raise LatticeError("pitch 须为正（得到 %r）" % (pitch_mm,))
        self.pitch = float(pitch_mm)
        self.x0 = float(x0)
        self.y0 = float(y0)
        self.i_max = int(i_max)
        self.j_max = int(j_max)

    @classmethod
    def from_board(cls, board, pitch_mm):
        ws = board["workspace"]
        x0 = math.floor(ws["x_min"] / pitch_mm) * pitch_mm
        y0 = math.floor(ws["y_min"] / pitch_mm) * pitch_mm
        i_max = int(math.floor((ws["x_max"] - x0) / pitch_mm))
        j_max = int(math.floor((ws["y_max"] - y0) / pitch_mm))
        return cls(pitch_mm, x0, y0, i_max, j_max)

    def to_mm(self, i, j):
        return (self.x0 + int(i) * self.pitch, self.y0 + int(j) * self.pitch)

    def snap(self, ex, ey):
        return (int(round((float(ex) - self.x0) / self.pitch)),
                int(round((float(ey) - self.y0) / self.pitch)))

    def in_bounds(self, i, j):
        return 0 <= int(i) <= self.i_max and 0 <= int(j) <= self.j_max

    def as_dict(self):
        return {"pitch_mm": self.pitch, "origin_mm": [self.x0, self.y0],
                "i_max": self.i_max, "j_max": self.j_max}

    @classmethod
    def from_dict(cls, d):
        return cls(d["pitch_mm"], d["origin_mm"][0], d["origin_mm"][1],
                   d["i_max"], d["j_max"])


def anchor_map(board, lattice):
    """partition_id -> [[i,j] 端点0锚, [i,j] 端点1锚]（最近格点）。

    锚冲突（不同分区端点同锚格点）fail-closed 抛 LatticeError——板在该
    pitch 下画板化不可行，属数据源事实，不静默换 pitch。"""
    out = {}
    seen = {}
    for p in board["partitions"]:
        pid = p["partition_id"]
        anchors = []
        for k, (ex, ey) in enumerate(p["geometry"]["endpoints"]):
            a = lattice.snap(ex, ey)
            key = tuple(a)
            if key in seen and seen[key][0] != pid:
                raise LatticeError(
                    "锚冲突 %s 与 %s#%d 同锚 %s（pitch=%r 不可行）"
                    % (seen[key], pid, k, list(a), lattice.pitch))
            seen[key] = (pid, k)
            if not lattice.in_bounds(*a):
                raise LatticeError("端点锚越界 %s %s" % (pid, list(a)))
            anchors.append(list(a))
        out[pid] = anchors
    return out
