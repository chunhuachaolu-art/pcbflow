"""pcbflow.v4_1.layerstack -- 多层层栈/层对/贯通孔跨度语义（E2；堵 K2）。

KiCad 语义建模（≥4 层：F.Cu / In1.Cu / In2.Cu / B.Cu 起步）：

1. 层栈顺序：板文件 (layers ...) 节点内铜层按栈序列出（KiCad 序列化
   不变量：F.Cu 最前、B.Cu 最后、In*.Cu 居中按内层序）——board_parse
   的 copper_layers 列表即栈序，本模块以该序为权威；
2. 贯通孔（via）跨度语义：via (layers l1 l2) 的铜障碍集 = 栈序中 l1
   与 l2 之间（**含两端**）的全部铜层：
   - 贯通孔 (F.Cu B.Cu) = 全部铜层（E1 既有行为，本模块一般化）；
   - 盲孔 (F.Cu In2.Cu) 在 4 层栈 = {F.Cu, In1.Cu, In2.Cu}——中间层
     In1.Cu 同为障碍（E1 旧实现只取两端点=多层语义缺口，E2 修复）；
   - 埋孔 (In1.Cu In2.Cu) = {In1.Cu, In2.Cu}；
   - 跨度两端写出顺序无关（规范化为栈序区间）；
3. 层对（layer pair）：相邻铜层对（F/In1、In1/In2、In2/B）——层切换
   视图与 via 跨度合法性判定的基元。

E1 兼容性：via (F.Cu B.Cu) 展开行为与 E1 逐字节一致（全铜层）；E1 的
96 用例零改动（改动仅影响非 F.Cu..B.Cu 的部分跨度，E1 域内无此形态）。

fail-closed：未知层名/非铜层名/重复层/空栈/跨度端点不在栈内均抛
LayerStackError，不静默。

零 IO、零子进程、零网络、零 wall-clock。
"""

from __future__ import annotations

__all__ = [
    "LayerStackError", "LayerStack", "via_span_layers",
    "is_copper_layer_name", "DEFAULT_STACK_4",
]

#: E2 起步层栈（任务书 §3 E2：F.Cu / In1 / In2 / B.Cu）
DEFAULT_STACK_4 = ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu")

_COPPER_SUFFIX = ".Cu"


class LayerStackError(ValueError):
    """层栈语义 fail-closed（未知层/非铜层/重复/空栈/跨度非法）。"""


def is_copper_layer_name(name):
    """层名是否为铜层（*.Cu；'*.Cu' 通配符不是具体层名）。"""
    return (isinstance(name, str) and name.endswith(_COPPER_SUFFIX)
            and name != "*%s" % _COPPER_SUFFIX and name != "Edge.Cuts")


def via_span_layers(start, end, copper_layers):
    """via 跨度 (start, end) -> 覆盖铜层列表（栈序，含两端，闭区间）。

    - (F.Cu, B.Cu)（或任何首末层对）= 全部铜层（E1 行为一般化）；
    - 部分跨度展开为栈序闭区间（盲孔含中间层——KiCad 桶身穿过全部
      中间层，annular ring 在跨度每层均为铜障碍）；
    - fail-closed：端点不在栈内/非铜层名/栈非法。
    """
    stack = LayerStack(copper_layers)
    return stack.via_span(start, end)


class LayerStack:
    """铜层栈（只读；栈序 = 解析器 copper_layers 列表序）。"""

    __slots__ = ("_names", "_index")

    def __init__(self, copper_layers):
        names = list(copper_layers)
        if not names:
            raise LayerStackError("铜层栈为空（fail-closed）")
        seen = set()
        for n in names:
            if not is_copper_layer_name(n):
                raise LayerStackError(
                    "非铜层名入栈（fail-closed）: %r（栈=%r）" % (n, names))
            if n in seen:
                raise LayerStackError(
                    "铜层重复入栈（fail-closed）: %r（栈=%r）" % (n, names))
            seen.add(n)
        self._names = tuple(names)
        self._index = {n: i for i, n in enumerate(self._names)}

    # ------------------------------------------------------------ 查询

    @property
    def names(self):
        return self._names

    @property
    def count(self):
        return len(self._names)

    def __contains__(self, name):
        return name in self._index

    def index_of(self, name):
        if name not in self._index:
            raise LayerStackError(
                "层 %r 不在铜层栈（fail-closed；栈=%r）" % (name, self._names))
        return self._index[name]

    def is_outer(self, name):
        """外层（F.Cu / 栈末层）。"""
        i = self.index_of(name)
        return i == 0 or i == len(self._names) - 1

    def is_inner(self, name):
        return not self.is_outer(name)

    # ------------------------------------------------------------ via 跨度

    def via_span(self, start, end):
        """跨度两端的栈序闭区间（含中间层；写出顺序无关）。"""
        ia, ib = self.index_of(start), self.index_of(end)
        lo, hi = (ia, ib) if ia <= ib else (ib, ia)
        return list(self._names[lo:hi + 1])

    def via_spans_all(self, start, end):
        """跨度是否覆盖全部铜层（贯通孔）。"""
        span = self.via_span(start, end)
        return len(span) == len(self._names)

    # ------------------------------------------------------------ 层对

    def adjacent_pairs(self):
        """相邻铜层对列表（栈序）：[(F,In1), (In1,In2), ..., (InN,B)]。"""
        return [(self._names[i], self._names[i + 1])
                for i in range(len(self._names) - 1)]

    def layers_between(self, a, b):
        """两铜层间的层列表（不含端点；供层切换走廊分析）。"""
        ia, ib = self.index_of(a), self.index_of(b)
        lo, hi = (ia, ib) if ia <= ib else (ib, ia)
        return list(self._names[lo + 1:hi])

    def as_dict(self):
        return {
            "copper_layers": list(self._names),
            "layer_count": len(self._names),
            "outer_layers": [self._names[0], self._names[-1]],
            "inner_layers": list(self._names[1:-1]),
            "adjacent_pairs": [[a, b] for (a, b) in self.adjacent_pairs()],
        }
