# -*- coding: utf-8 -*-
"""提交纪律（SPEC §4.2）：工具绝不写不被验证的铜。

流程（每批次）：
1. 快照拷当前板 → pcbagent-out/b3/snapshot-*.kicad_pcb；
2. 逐网落板（调用方在每网前重跑 route，镜像 sync 后 L1 终判基于最新板态；
   router._verify 已保证 margin>0 全过——口径含 CLI 圆形多边形化余量）；
3. 每 ≤L3_BATCH 网跑一次 kicad-cli（--severity-error --refill-zones
   --save-board，工程目录内——HANDOFF 坑 1 的连通性/间距真值口径）；
4. 与基线 diff："新增违规"按桥接 diff_drc 描述键匹配（B1 校准实证：探针铜
   会并入所触网簇、网名不可靠，故 diff 按违规描述整体键匹配，任何 added
   非空即整批回滚快照——宁误杀不放行）。

落板后端（可插拔）：
- SexprWriter：s-expr 文本直写（无头；合成板测试/无 KiCad 实例场景）。
  KiCad 10 板文件 net 以名字出现（HANDOFF 坑 2）；segment/via 节点文本级
  追加；via 类型跟随存量口径（Rev-C F..In2 全部 (via buried)，实测）。
- KipyWriter：kipy IPC 事务落板（S4 实战用；需运行中的 KiCad 实例）。
  导入前先注册公共 pb2 类型（kipy 0.7.1 导入坑）。

写盘统一走 _write_checked（pathlib resolve + 包含性校验，Mimosa 钩子放行
模式）；本模块外的产物落盘由调用方走 cli.dump。
"""
from __future__ import annotations

import os
import pathlib
import time

from . import config as C
from .bridge import run_drc, diff_drc

LAYER_FILE_NAME = {C.LAYER_F: "F.Cu", C.LAYER_B: "B.Cu",
                   C.LAYER_IN1: "In1.Cu", C.LAYER_IN2: "In2.Cu"}


def board_path_of(project):
    """工程内与 .kicad_pro 同名的 .kicad_pcb（多板同名防呆，B1 约定）。"""
    pro = None
    for f in os.listdir(project):
        if f.endswith(".kicad_pro"):
            pro = f
    if pro:
        stem = os.path.splitext(pro)[0]
        cand = os.path.join(project, stem + ".kicad_pcb")
        if os.path.exists(cand):
            return cand
    for f in os.listdir(project):
        if f.endswith(".kicad_pcb"):
            return os.path.join(project, f)
    raise FileNotFoundError(f"no .kicad_pcb in {project}")


def _write_checked(dirpath, name, text):
    """落盘：路径规范化 + 包含性校验（目标必须落在 dirpath 内）。"""
    base = pathlib.Path(dirpath).resolve()
    target = pathlib.Path(base / os.path.basename(name)).resolve()
    if base != target and base not in target.parents:
        raise ValueError(f"写盘路径越界: {name}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="")


# ---------------- 落板后端 ----------------

class SexprWriter:
    """s-expr 文本直写后端（无头）。每 plan 追加 segment/via 节点到板文件尾。"""
    name = "sexpr"

    def apply(self, project, plan):
        path = board_path_of(project)
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        # 板文件以 ")" 收尾（s-expr 根节点闭合）——剥掉后追加节点再合上
        stripped = text.rstrip()
        if not stripped.endswith(")"):
            raise ValueError(f"板文件非预期结尾: {path}")
        tail = text[len(stripped):]
        nodes = self._nodes(plan)
        _write_checked(project, os.path.basename(path),
                       stripped[:-1] + nodes + ")" + tail)

    def remove_net(self, project, net):
        """删除某网全部 segment/via 节点（rip-up 拆迁的落板动作）。
        顶层括号平衡扫描，节点文本含 (net "X") 即整节点删除。"""
        path = board_path_of(project)
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        out = []
        i, n = 0, len(text)
        marker = f'(net "{net}")'
        while i < n:
            if text[i] == "(":
                j = i + 1
                while j < n and text[j] not in " \t\r\n()":
                    j += 1
                tag = text[i + 1:j]
                if tag in ("segment", "via"):
                    depth, k, instr = 1, j, False
                    while k < n and depth > 0:
                        ch = text[k]
                        if instr:
                            if ch == "\\":
                                k += 2
                                continue
                            if ch == '"':
                                instr = False
                        else:
                            if ch == '"':
                                instr = True
                            elif ch == "(":
                                depth += 1
                            elif ch == ")":
                                depth -= 1
                        k += 1
                    if marker in text[i:k]:
                        i = k
                        while i < n and text[i] in "\r\n\t ":
                            i += 1
                        continue
                    out.append(text[i:k])
                    i = k
                    continue
            out.append(text[i])
            i += 1
        _write_checked(project, os.path.basename(path), "".join(out))

    def _nodes(self, plan):
        out = []
        for (L, x1, y1, x2, y2) in plan.segments:
            out.append(
                "\t(segment\n"
                f"\t\t(start {x1:.4f} {y1:.4f})\n"
                f"\t\t(end {x2:.4f} {y2:.4f})\n"
                f"\t\t(width {plan.width})\n"
                f'\t\t(layer "{LAYER_FILE_NAME[L]}")\n'
                f'\t\t(net "{plan.net}")\n'
                f'\t\t(uuid "{plan.uuid}")\n'
                "\t)\n")
        for (x, y) in plan.vias:
            out.append(
                "\t(via buried\n"
                f"\t\t(at {x:.4f} {y:.4f})\n"
                f"\t\t(size {plan.via_size})\n"
                f"\t\t(drill {plan.via_drill})\n"
                '\t\t(layers "F.Cu" "In2.Cu")\n'
                f'\t\t(net "{plan.net}")\n'
                f'\t\t(uuid "{plan.uuid}")\n'
                "\t)\n")
        return "".join(out)


class KipyWriter:
    """kipy IPC 事务后端（S4 实战；需运行中 KiCad 实例与打开的板）。"""
    name = "kipy"

    def __init__(self, log=print):
        self.log = log
        # kipy 0.7.1 导入坑：先注册公共 pb2 类型（HANDOFF/记忆实证）
        import kipy.proto.common.types.base_types_pb2  # noqa: F401
        from kipy.kicad import KiCad
        from kipy.board_types import Track, Via, Net
        from kipy.geometry import Vector2
        from kipy.proto.board import board_types_pb2 as bt
        self._KiCad, self._Track, self._Via, self._Net = KiCad, Track, Via, Net
        self._Vector2, self._bt = Vector2, bt
        self._BL = {C.LAYER_F: bt.BoardLayer.BL_F_Cu,
                    C.LAYER_IN2: bt.BoardLayer.BL_IN2_Cu}

    def _open_board(self, project):
        kicad = self._KiCad()
        board = kicad.get_board()
        want = os.path.splitext(os.path.basename(board_path_of(project)))[0]
        got = os.path.splitext(os.path.basename(str(board.name())))[0]
        if got != want:
            raise RuntimeError(f"KiCad 实例打开的板是 {got}，预期 {want}")
        return board

    def apply(self, project, plan):
        board = self._open_board(project)
        nets = {n.name: n for n in board.get_nets()}
        if plan.net not in nets:
            raise RuntimeError(f"板上无网 {plan.net}")
        net = nets[plan.net]
        items = []
        for (L, x1, y1, x2, y2) in plan.segments:
            t = self._Track()
            t.start = self._Vector2.from_xy_mm(x1, y1)
            t.end = self._Vector2.from_xy_mm(x2, y2)
            t.width = int(round(plan.width * 1e6))
            t.layer = self._BL[L]
            t.net = net
            items.append(t)
        for (x, y) in plan.vias:
            v = self._Via()
            v.position = self._Vector2.from_xy_mm(x, y)
            v.diameter = int(round(plan.via_size * 1e6))
            v.drill_diameter = int(round(plan.via_drill * 1e6))
            v.type = self._bt.ViaType.VT_BLIND_BURIED
            v.padstack.drill.start_layer = self._BL[C.LAYER_F]
            v.padstack.drill.end_layer = self._BL[C.LAYER_IN2]
            v.net = net
            items.append(v)
        commit = board.begin_commit()
        board.create_items(items)
        board.push_commit(commit, f"pcbagent L3 route {plan.net}")
        board.save()

    def remove_net(self, project, net):
        """rip-up 拆迁：删除该网全部 track/via（焊盘属封装不动）。"""
        board = self._open_board(project)
        doomed = [t for t in board.get_tracks() if t.net.name == net] + \
                 [v for v in board.get_vias() if v.net.name == net]
        if doomed:
            commit = board.begin_commit()
            board.remove_items(doomed)
            board.push_commit(commit, f"pcbagent L3 ripup {net}")
            board.save()


# ---------------- 提交纪律主流程 ----------------

class CommitFlow:
    def __init__(self, project, writer, out_dir=None, baseline=None, log=print):
        self.project = project
        self.writer = writer
        self.log = log
        self.out_dir = out_dir or os.path.join(project, "pcbagent-out", "b3")
        self.baseline = baseline          # DrcResult；None 则 run() 现场跑
        self.snap_seq = 0

    def snapshot(self):
        """拷当前板 → pcbagent-out/b3/snapshot-<seq>.kicad_pcb。返回快照路径。"""
        path = board_path_of(self.project)
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        self.snap_seq += 1
        name = f"snapshot-{self.snap_seq:02d}.kicad_pcb"
        _write_checked(self.out_dir, name, text)
        return os.path.join(self.out_dir, name)

    def restore(self, snap_path):
        """快照拷回板文件（整批回滚）。"""
        with open(snap_path, encoding="utf-8") as fh:
            text = fh.read()
        path = board_path_of(self.project)
        _write_checked(self.project, os.path.basename(path), text)

    def run(self, plans, batch=C.L3_BATCH, on_applied=None):
        """按提交纪律落一批 plan（含 route 失败的报告）。plans 可为惰性序列
        （生成器：每网 route 在上一网落板+sync 后执行，L1 终判始终基于最新
        板态）。返回批次报告 dict。

        on_applied(plan)：每网落板后回调（调用方借此 mirror.sync()）。"""
        t0 = time.perf_counter()
        snap = self.snapshot()
        if self.baseline is None:
            self.log("[commit] 跑基线 DRC（refill+save 口径）…")
            self.baseline = run_drc(self.project)
        written = []
        reports = []
        verdict = None
        for i, plan in enumerate(plans):
            reports.append(plan.to_dict())
            if not plan.ok:
                continue
            # rip-up 落板序：删被拆网旧铜 → 落本网新铜 → 落被拆网重布铜
            # （终判口径=legality.ignore_ids 视同已删，此处真实删除对齐；
            #   分段模式可聚合多个拆迁，逐个走同序）
            for (rn, _rp) in plan.ripup_ops():
                self.writer.remove_net(self.project, rn)
                if on_applied is not None:
                    on_applied(plan)
            self.writer.apply(self.project, plan)
            written.append(plan)
            for (_rn, rp) in plan.ripup_ops():
                if rp is not None:
                    self.writer.apply(self.project, rp)
            if on_applied is not None:
                on_applied(plan)
            if len(written) % batch == 0:
                verdict = self._check(written, f"batch@{i}")
                if verdict["added"]:
                    self.restore(snap)
                    verdict["rolled_back"] = True
                    verdict["written_plans"] = len(written)
                    verdict["snapshot"] = snap
                    verdict["run_s"] = round(time.perf_counter() - t0, 1)
                    verdict["plans"] = reports
                    return verdict
        verdict = self._check(written, "final")
        if verdict["added"]:
            self.restore(snap)
        verdict["rolled_back"] = bool(verdict["added"])
        verdict["written_plans"] = len(written)
        verdict["snapshot"] = snap
        verdict["run_s"] = round(time.perf_counter() - t0, 1)
        verdict["plans"] = reports
        return verdict

    def _check(self, written, tag):
        """CLI 复核 + 基线 diff。任何新增违规（描述键整体匹配）= added。"""
        after = run_drc(self.project)
        added, removed = diff_drc(self.baseline, after)
        self.log(f"[commit:{tag}] CLI DRC: 违规 {len(after.violations)}"
                 f"（基线 {len(self.baseline.violations)}，新增 {len(added)}，"
                 f"消失 {removed}），本批落网 {len(written)}")
        return {
            "tag": tag,
            "written_nets": [p.net for p in written],
            "added": [{"type": v.get("type"), "severity": v.get("severity"),
                       "items": [it.get("description", "")
                                 for it in v.get("items", [])]}
                      for v in added],
            "removed_count": removed,
            "violations_after": after.summary(),
        }
