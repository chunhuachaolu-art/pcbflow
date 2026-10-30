"""REPAIR-P1 W-5 冻结夹具板助手（铜环案 R4 三步法②）。

铜族测试的精确期望值（counts 2372/358/2、bytes 1445179、copper_sha256
c4a46878…、identity_map 2732、消歧 217/210/7、zone uuid/fill_points、
pads 564 等）原是 2026-09-11 时点 live 板实测（注释标记「M1 刷新」），
钉在可变 live 板上、下次板变更必炸（与 09-12 4F 案同构）。按
archive/copper-loop/COPPER-LOOP-ADJUDICATION-2026-09-11.md §8.2 ② R4
三步法，把该板字节冻结副本收进 tests/fixtures/（授权原文：「把一份
…收进 tests/fixtures/，或自造小而全的合成板」），精确值改钉夹具板；
live 板各文件另留一条不变量用例（R4③）。

只读纪律：本模块与使用它的测试对 design/ 真实板零写入；夹具板自身
漂移由 fixture_board() 的 fail-closed sha 断言检出。
"""

import hashlib
import os

_BOARD_BASENAME = "stm32h743-coreboard-revc.kicad_pcb"
FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "fixtures", "revc-live-dbfea089")
FIXTURE_BOARD = os.path.join(FIXTURE_DIR, _BOARD_BASENAME)

# 登记锚：2026-09-11 APPLY-1/ripup1 落线后的 live 板全量 sha256
# （design/coreboard/kicad/stm32h743-coreboard-revc/stm32h743-coreboard-revc.kicad_pcb
#  时点实测；铜环案裁定书与 v4.1 redesign-report P1 在案）。
FIXTURE_BOARD_SHA256 = (
    "dbfea0895301ade8209701ef93545b26ca35ef49a9b7116032d917db79e1a791")


def fixture_board():
    """返回夹具板绝对路径；fail-closed：字节 sha 必须等于登记锚。"""
    p = os.path.normpath(FIXTURE_BOARD)
    with open(p, "rb") as f:
        got = hashlib.sha256(f.read()).hexdigest()
    assert got == FIXTURE_BOARD_SHA256, (
        "冻结夹具板自身漂移: got %s want %s" % (got[:8], FIXTURE_BOARD_SHA256[:8]))
    return p


def fixture_board_text():
    """夹具板文本（newline='' 原样保留行尾，与铜族测试的读板口径一致）。"""
    with open(fixture_board(), encoding="utf-8", newline="") as f:
        return f.read()


def duplicate_first_segment(text):
    """结构化篡改（负对照用）：复制第一个平衡的 (segment …) 块并换新 uuid。

    板内 segment 为 tab 缩进多行平衡块；按括号深度切出整块后原位复制，
    且副本内 uuid 首位十六进制字符翻转（否则副本与原块 uuid+几何全同，
    会被身份折叠、计数不动）。解析计数恰好 +1 segment。用于证明 M1
    精确计数断言仍随板内容 fire（R28「不得弱化回归检测能力」硬约束
    的检出证明）。
    """
    lines = text.splitlines(keepends=True)
    start = next(i for i, ln in enumerate(lines)
                 if ln.startswith("\t(segment"))
    depth = 0
    end = None
    for j in range(start, len(lines)):
        depth += lines[j].count("(") - lines[j].count(")")
        if depth == 0:
            end = j + 1
            break
    assert end is not None, "segment 块未闭合（篡改器假设失效）"
    block = "".join(lines[start:end])
    head, _, tail = block.partition('(uuid "')
    assert tail, "segment 块内未找到 (uuid …)（篡改器假设失效）"
    uuid_hex = tail.split('"', 1)[0]
    flip = "1" if uuid_hex[0] != "1" else "0"
    block2 = head + '(uuid "' + flip + uuid_hex[1:] + '"' + tail[len(uuid_hex) + 1:]
    assert block2 != block
    return "".join(lines[:end]) + block2 + "".join(lines[end:])
