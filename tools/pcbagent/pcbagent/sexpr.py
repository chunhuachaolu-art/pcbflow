# -*- coding: utf-8 -*-
"""极简 KiCad s-expr 解析器（只读）。

节点 = list，首元素为 tag 字符串，其余为子节点/原子（全部 str；数值不自动转换）。
约定辅助：num(x) 把原子转 float；walk(root, tag) 深度遍历取节点。
"""
from __future__ import annotations


def parse(text: str) -> list:
    """解析 s-expr 文本为嵌套 list。顶层返回整个文件节点。"""
    n = len(text)
    i = 0
    stack: list[list] = []
    root: list | None = None

    def push_atom(buf: list[str]):
        if buf:
            stack[-1].append("".join(buf))
            buf.clear()

    buf: list[str] = []
    while i < n:
        c = text[i]
        if c == '"':
            # 带引号字符串，支持 \" 与 \\ 转义
            i += 1
            out: list[str] = []
            while i < n:
                ch = text[i]
                if ch == "\\" and i + 1 < n:
                    out.append(text[i + 1])
                    i += 2
                    continue
                if ch == '"':
                    i += 1
                    break
                out.append(ch)
                i += 1
            if stack:
                stack[-1].append("".join(out))
            else:
                raise ValueError("string outside list")
            continue
        if c == "(":
            node: list = []
            if stack:
                push_atom(buf)
                stack[-1].append(node)
            else:
                if root is not None:
                    raise ValueError("multiple roots")
                root = node
            stack.append(node)
            i += 1
            continue
        if c == ")":
            push_atom(buf)
            if not stack:
                raise ValueError("unbalanced )")
            stack.pop()
            i += 1
            continue
        if c in " \t\r\n":
            push_atom(buf)
            i += 1
            continue
        buf.append(c)
        i += 1
    if stack:
        raise ValueError("unbalanced (")
    if root is None:
        raise ValueError("empty")
    return root


def num(x) -> float:
    return float(x)


def children(node: list, tag: str) -> list[list]:
    """node 的直接子节点里 tag 匹配者。"""
    return [c for c in node[1:] if isinstance(c, list) and c and c[0] == tag]


def child(node: list, tag: str) -> list | None:
    for c in node[1:]:
        if isinstance(c, list) and c and c[0] == tag:
            return c
    return None


def walk(root: list, tag: str):
    """深度优先遍历所有 tag 匹配节点（含 root 以下）。"""
    stack = [root]
    while stack:
        nd = stack.pop()
        for c in nd[1:]:
            if isinstance(c, list) and c:
                if c[0] == tag:
                    yield c
                stack.append(c)


def atoms(node: list) -> list[str]:
    return [a for a in node[1:] if isinstance(a, str)]
