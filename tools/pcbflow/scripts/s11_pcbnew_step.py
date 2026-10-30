"""S11 TD7 编排侧：pcbnew DSN 导出 / 未布线推导 / SES 应用
（F:\\kicad\\bin\\python.exe 执行）。

- unrouted_derive <raw.kicad_pcb> <out.kicad_pcb> <expect_sha256>
    datasets raw 参考 routed 态（只读源）→ staging 未布线板：
    删除全部 track/via/arc（保留 footprint/zone/edge/文本），SaveBoard
    （KiCad 10 格式升级=staging 内确定性重写）。zone 保留口径：DSN
    导出把 zone 作为 conduction area（ASM-8 同构），freerouting 的任务
    =信号布线，不受 pour 义务惩罚。
- dsn_export <board.kicad_pcb> <out.dsn> <expect_sha256>
- ses_apply  <board.kicad_pcb> <run.ses> <out.kicad_pcb> <board_sha256>

ASM-8 先例：kicad-cli 10 无 DSN 子命令，DSN 导出=pcbnew
ExportSpecctraDSN；SES 应用=pcbnew ImportSpecctraSES（kicad 10.0.5
python API 实测在册）。输入板 sha256 逐字节预验（fail-closed）。
"""

from __future__ import annotations

import hashlib
import sys

import pcbnew


def sha256_file(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def derive_unrouted(src: str, out: str) -> dict:
    board = pcbnew.LoadBoard(src)
    assert board is not None, f"LoadBoard 失败: {src}"
    counts = {"tracks": 0, "vias": 0, "arcs": 0, "zones_kept": 0}
    for track in list(board.GetTracks()):
        kind = track.TypeName() if hasattr(track, "TypeName") else ""
        if "Via" in kind:
            counts["vias"] += 1
        elif "Arc" in kind:
            counts["arcs"] += 1
        else:
            counts["tracks"] += 1
        board.Remove(track)
    counts["zones_kept"] = len(list(board.Zones()))
    pcbnew.SaveBoard(out, board)
    return counts


def main() -> int:
    mode = sys.argv[1]
    if mode == "unrouted_derive":
        src, out, expect = sys.argv[2], sys.argv[3], sys.argv[4]
        got = sha256_file(src)
        assert got == expect, f"board sha256 不符: {got} != {expect}"
        counts = derive_unrouted(src, out)
        print("UNROUTED_DERIVE_OK", sha256_file(out)[:16],
              counts)
        return 0
    if mode == "dsn_export":
        src, out, expect = sys.argv[2], sys.argv[3], sys.argv[4]
        got = sha256_file(src)
        assert got == expect, f"board sha256 不符: {got} != {expect}"
        board = pcbnew.LoadBoard(src)
        assert board is not None, f"LoadBoard 失败: {src}"
        pcbnew.ExportSpecctraDSN(board, out)
        print("DSN_EXPORT_OK", sha256_file(out)[:16])
        return 0
    if mode == "ses_apply":
        src, ses, out, expect = (sys.argv[2], sys.argv[3], sys.argv[4],
                                 sys.argv[5])
        got = sha256_file(src)
        assert got == expect, f"board sha256 不符: {got} != {expect}"
        board = pcbnew.LoadBoard(src)
        assert board is not None, f"LoadBoard 失败: {src}"
        pcbnew.ImportSpecctraSES(board, ses)
        pcbnew.SaveBoard(out, board)
        print("SES_APPLY_OK", sha256_file(out)[:16])
        return 0
    print(f"unknown mode {mode}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
