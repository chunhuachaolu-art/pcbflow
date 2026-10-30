"""pcbflow.v4_1.costmodel -- via 分层真实成本模型（E3；堵 K3 半侧）。

v1 冻结口径：每 via 恒 8.0mm（v4exp.router.OBJ_VIA / VIA_COST_CELLS=32），
与跨度无关——E2 遗留②：扁平成本使 A* 就近取 In1，深内层（In2）无成本
梯度，利用率恒 0。

本模块把 via 成本一般化为跨度函数 cost(from_layer, to_layer)，参数可配：

    cost_mm = THROUGH_MM                     若跨度覆盖全栈（贯通孔）
    cost_mm = min(ADJACENT_BLIND_MM
                  + PER_EXTRA_GAP_MM*(gaps-1),
                  THROUGH_MM)                 否则（盲/埋，gaps=栈序跳数）

默认参数（依据落 prereg-e3.json → cost_model_defaults）：

    THROUGH_MM        = 8.0   v1 冻结 objective 锚点；2 层栈唯一跨度即贯通
                              → 112 场景域逐字节退化为 v1（G3.2 连续性根）
    ADJACENT_BLIND_MM = 4.0   贯通锚一半：参考 4 层栈上盲孔桶身/足迹占
                              2/4 层，资源占用与信号桩长减半
    PER_EXTRA_GAP_MM  = 1.5   每多跨一个层对的边际成本（中间层走廊阻塞 +
                              桩长增量）；4 层栈 gap2=5.5 < 贯通 8.0 =
                              两相邻盲 8.0 → 单深盲严格优于堆叠双盲，
                              In2 单跳可达
    部分跨度封顶 THROUGH_MM（≥6 层栈防超出贯通锚，保持可替代性）

层序语义：跨度/跳数经 layerstack.LayerStack（栈序闭区间，E2 冻结语义）
判定；fail-closed（未知层/非铜层/参数非法抛 CostModelError）。

零 IO、零子进程、零网络、零 wall-clock。
"""

from __future__ import annotations

import math

from .layerstack import LayerStack

__all__ = [
    "CostModelError", "ViaCostModel", "FLAT_VIA_MM",
    "DEFAULT_COST_PARAMS", "via_span_class",
]

#: v1 冻结常数（v4exp.router.OBJ_VIA；扁平模型唯一参数）
FLAT_VIA_MM = 8.0

#: 默认分层参数（依据见模块 docstring 与 prereg-e3.json）
DEFAULT_COST_PARAMS = {
    "through_mm": 8.0,
    "adjacent_blind_mm": 4.0,
    "per_extra_gap_mm": 1.5,
    "clamp_partial_to_through": True,
}


class CostModelError(ValueError):
    """成本模型 fail-closed（参数非法/层名非法）。"""


def _positive_finite(name, v):
    if (isinstance(v, bool) or not isinstance(v, (int, float))
            or not math.isfinite(float(v)) or float(v) <= 0.0):
        raise CostModelError("参数 %s 非法（须为正有限数）: %r" % (name, v))
    return float(v)


class ViaCostModel:
    """via 分层成本模型：cost_mm(from, to) 按跨度分类计价。

    与 v4exp.router 的 A* 合同换算：格点成本（cells）= cost_mm / 0.25。
    格点换算只接受整数格值（默认参数全部 0.25 整倍数；非整倍数时
    cells_cost 抛错——搜索成本必须整型确定性，fail-closed 不取整）。
    """

    def __init__(self, copper_layers, params=None, flat=False):
        """copper_layers：栈序铜层列表（layerstack 口径）。

        flat=True 时忽略 params，恒返回 FLAT_VIA_MM（v1 等价退化臂，
        消融对照用；2 层栈上与分层默认臂逐字节等价）。
        """
        self.stack = LayerStack(copper_layers)  # fail-closed 校验层栈
        self.flat = bool(flat)
        if self.flat:
            self.params = {"flat_via_mm": FLAT_VIA_MM}
        else:
            src = dict(DEFAULT_COST_PARAMS if params is None else params)
            if "flat_via_mm" in src:
                raise CostModelError("分层模型不接受 flat_via_mm 键（用 flat=True）")
            self.through_mm = _positive_finite("through_mm", src.get("through_mm"))
            self.adjacent_blind_mm = _positive_finite(
                "adjacent_blind_mm", src.get("adjacent_blind_mm"))
            per = src.get("per_extra_gap_mm", 0.0)
            if (isinstance(per, bool) or not isinstance(per, (int, float))
                    or not math.isfinite(float(per)) or float(per) < 0.0):
                raise CostModelError("参数 per_extra_gap_mm 非法（须为非负有限数）")
            self.per_extra_gap_mm = float(per)
            self.clamp_partial_to_through = bool(
                src.get("clamp_partial_to_through", True))
            if self.adjacent_blind_mm > self.through_mm:
                raise CostModelError(
                    "单调性破坏：adjacent_blind_mm(%.6f) > through_mm(%.6f)"
                    % (self.adjacent_blind_mm, self.through_mm))
            self.params = {
                "through_mm": self.through_mm,
                "adjacent_blind_mm": self.adjacent_blind_mm,
                "per_extra_gap_mm": self.per_extra_gap_mm,
                "clamp_partial_to_through": self.clamp_partial_to_through,
            }

    # ------------------------------------------------------------ 查询

    def gaps(self, from_layer, to_layer):
        """跨度跳数 = 栈序索引差（相邻层对=1）。"""
        return abs(self.stack.index_of(from_layer) - self.stack.index_of(to_layer))

    def is_through(self, from_layer, to_layer):
        """跨度是否覆盖全栈（贯通孔）。"""
        return self.gaps(from_layer, to_layer) == self.stack.count - 1

    def cost_mm(self, from_layer, to_layer):
        """该跨度 via 的成本（mm 等效；与冻结 objective 同量纲）。"""
        if self.flat:
            # 层名仍需在栈内（fail-closed 校验，成本本身与跨度无关）
            self.stack.index_of(from_layer)
            self.stack.index_of(to_layer)
            return FLAT_VIA_MM
        g = self.gaps(from_layer, to_layer)
        if self.is_through(from_layer, to_layer):
            return self.through_mm
        cost = self.adjacent_blind_mm + self.per_extra_gap_mm * (g - 1)
        if self.clamp_partial_to_through:
            cost = min(cost, self.through_mm)
        return cost

    def cost_cells(self, from_layer, to_layer, grid_mm=0.25):
        """A* 格点成本（cells）；非整格值 fail-closed（整型确定性合同）。"""
        mm = self.cost_mm(from_layer, to_layer)
        cells = mm / float(grid_mm)
        if abs(cells - round(cells)) > 1e-9:
            raise CostModelError(
                "via 成本 %.6fmm 非格点整倍数（grid=%.3f）——搜索成本须整型确定"
                % (mm, grid_mm))
        return int(round(cells))

    def via_costs_table_cells(self, grid_mm=0.25):
        """全层对成本表（cells；栈序对；确定性诊断/测试用）。"""
        table = {}
        names = self.stack.names
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                table["%s|%s" % (names[i], names[j])] = self.cost_cells(
                    names[i], names[j], grid_mm)
        return table

    def objective_via_cost_mm(self, via):
        """求解输出 via dict（from_layer/to_layer）-> 该 via 分层成本。"""
        return self.cost_mm(str(via["from_layer"]), str(via["to_layer"]))

    def as_dict(self):
        return {
            "flat": self.flat,
            "copper_layers": list(self.stack.names),
            "params": dict(self.params),
        }


def via_span_class(from_layer, to_layer, copper_layers):
    """跨度分类（消融报告口径；layerstack 栈序闭区间语义）。

    through         覆盖全栈（含两端外层）
    blind_adjacent  外层起 1 gap（F..In1 型）
    blind_deep      外层起 >=2 gap（F..In2 型）
    buried          内层间跨度（In1..In2 型；不含外层）
    """
    stack = LayerStack(copper_layers)
    a = stack.index_of(from_layer)
    b = stack.index_of(to_layer)
    lo, hi = min(a, b), max(a, b)
    n = stack.count
    if hi - lo == n - 1:
        return "through"
    outer = {0, n - 1}
    if lo in outer and hi not in outer:
        return "blind_adjacent" if hi - lo == 1 else "blind_deep"
    if hi in outer and lo not in outer:
        return "blind_adjacent" if hi - lo == 1 else "blind_deep"
    return "buried"
