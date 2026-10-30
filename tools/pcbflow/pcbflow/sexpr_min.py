"""最小 s-expr 只读读取器（A 期 fallback，SPEC §0/§4）。

pcbagent adapter 未就绪时的自带读取器。只读、纯文本、确定性。
能力与保真度必须随产物声明（CAPABILITY/FIDELITY/FALLBACK_REASON），
不冒充 pcbagent adapter。

支持 KiCad s-expr：token、带引号字符串（含 \\" 转义）、任意空白/缩进、
括号嵌套。不支持：多行字符串字面量之外的转义语义、注释。
"""

from __future__ import annotations

# 能力矩阵（随产物声明，SPEC §0.2 fallback 记录字段）
BACKEND = "pcbflow.sexpr_min"
CAPABILITIES = [
    "read_kicad_netlist_nets",   # (net (code)(name)(node(ref)(pin)))
    "read_kicad_board_nets",     # (net (ordinal)(name))
    "read_kicad_board_footprints",  # (footprint (at)(property ...)(pad ...))
    "text_level_only",           # 无几何求值/无 DRC/无写回
]
FIDELITY = "text_structure_only"  # 不解析语义单位（坐标换算等后续级再做）
FALLBACK_REASON = "pcbagent read adapter not ready at A-stage; SPEC §0 allows minimal s-expr reader with declared fidelity"


class SexprError(ValueError):
    pass


def parse(text: str):
    """解析 s-expr 文本 → 嵌套 [name, child...] 列表。字符串为 str 叶子。"""
    n = len(text)
    i = 0
    stack: list = []
    top: list = []
    while i < n:
        c = text[i]
        if c in " \t\r\n":
            i += 1
        elif c == "(":
            node: list = []
            if stack:
                stack[-1].append(node)
            else:
                top.append(node)
            stack.append(node)
            i += 1
        elif c == ")":
            if not stack:
                raise SexprError(f"unbalanced ')' at offset {i}")
            stack.pop()
            i += 1
        elif c == '"':
            j = i + 1
            buf = []
            while j < n:
                d = text[j]
                if d == "\\" and j + 1 < n:
                    buf.append(text[j + 1])
                    j += 2
                elif d == '"':
                    break
                else:
                    buf.append(d)
                    j += 1
            else:
                raise SexprError(f"unterminated string at offset {i}")
            if not stack:
                raise SexprError(f"bare string outside node at offset {i}")
            stack[-1].append("".join(buf))
            i = j + 1
        else:
            j = i
            while j < n and text[j] not in ' \t\r\n()"':
                j += 1
            if not stack:
                raise SexprError(f"bare token outside node at offset {i}")
            stack[-1].append(text[i:j])
            i = j
    if stack:
        raise SexprError("unbalanced '(' — unexpected EOF")
    return top


def load_file(path: str, encoding: str = "utf-8"):
    with open(path, "r", encoding=encoding) as f:
        return parse(f.read())


def find_all(node, name: str, results: list | None = None) -> list:
    """深度优先收集所有名为 name 的子节点（pre-order，与历史递归版同序）。

    迭代栈实现（SEC-PERF 2026-09-19）：消除逐节点递归调用与 node[1:]
    切片拷贝；输出序与旧递归版逐位一致（差分对拍 EQUIV-PROVEN，
    226 板 datasets 全量 + 边界用例，tools/_r5_scratch/secperf_equiv_sexpr.py）。
    """
    if results is None:
        results = []
    top_it = iter(node)
    next(top_it, None)          # 跳过 node[0]，等价 node[1:] 但零拷贝
    stack = [top_it]
    append = results.append
    push = stack.append
    pop = stack.pop
    while stack:
        for child in stack[-1]:
            if not isinstance(child, list):
                continue
            if child and child[0] == name:
                append(child)
            it = iter(child)
            next(it, None)
            push(it)
            break
        else:
            pop()
    return results


def find_first(node, name: str):
    """首个 pre-order 命中（= find_all(...)[0]，命中即早退）。"""
    top_it = iter(node)
    next(top_it, None)
    stack = [top_it]
    push = stack.append
    pop = stack.pop
    while stack:
        for child in stack[-1]:
            if not isinstance(child, list):
                continue
            if child and child[0] == name:
                return child
            it = iter(child)
            next(it, None)
            push(it)
            break
        else:
            pop()
    return None


def get_str(node, index: int = 1):
    """取子位置上的字符串叶子（如 (name "X") → get_str 传入该节点）。"""
    if node is None or len(node) <= index:
        return None
    v = node[index]
    return v if isinstance(v, str) else None


def build_index(node, index: dict | None = None) -> dict:
    """一次 pre-order 遍历建 name→nodes 索引（root 级多键重复查询加速）。

    索引值[k] 与逐次 find_all(node, k) 结果逐位一致（同 pre-order 序、
    同「list 后代且首 token==k」判据；node 自身不计入——与 find_all 从
    children 起查的口径一致）。align-r1（2026-09-25）：corpus 线 root
    级多键查询/计数改吃本索引，替代多次全树走查；子树级小查询仍走
    find_all/find_first（索引仅对构建时的根有效）。

    返回的列表为共享只读视图——消费方勿 mutate（需要改就先 copy）。
    """
    if index is None:
        index = {}
    # 初始层与子层都逆序 push（栈=LIFO，pop 得 pre-order 正序）
    stack = [c for c in reversed(node) if isinstance(c, list)]
    push = stack.append
    pop = stack.pop
    get = index.get
    while stack:
        cur = pop()
        name = cur[0] if cur else None
        # find_all 判据 child[0]==name（str）；非 str 首 token 不入索引
        # （查询键恒 str，等价跳过），但其后代仍遍历（同 find_all 深入）。
        if type(name) is str or isinstance(name, str):
            lst = get(name)
            if lst is None:
                index[name] = [cur]
            else:
                lst.append(cur)
        for child in reversed(cur):
            if isinstance(child, list):
                push(child)
    return index


def index_first(index: dict, name: str):
    """索引侧 find_first 等价：index[name][0]（pre-order 首个命中）。"""
    lst = index.get(name)
    return lst[0] if lst else None


def index_all(index: dict, name: str) -> list:
    """索引侧 find_all 只读视图（共享列表；空命中返回新空表）。"""
    return index.get(name) or []
