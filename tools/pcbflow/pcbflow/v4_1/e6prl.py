"""pcbflow.v4_1.e6prl -- kicad-cli 封装调用器（prl 卫生制度化；E6 G6.2）。

任务书 §3 E6：把 E1 的 prl_hygiene.check_and_restore 上升为制度化工具——
kicad-cli 每次调用后自动 sidecar 检查。事故锚=holdout-r1 红线首破
（kicad-cli 在 datasets/ 受保护目录留下 3 个 .kicad_prl；V3-NEXT L54：
板 sha 零变化、已删复原+聚合哈希复验，教训=渲染后查 prl）。

制度化路径（prereg g62.wiring_choice）：**封装调用器**——既有调用点为
编排侧 Bash（仓内无可接线的 Python 调用点），故零既有文件 diff；E6 自身
全部 kicad-cli 调用一律经本 guard（本包先吃自己的狗食）。

KicadCliGuard.call(argv, cwd) 契约：

1. cwd + watch_dirs 逐目录 inventory（调用前基线）；
2. 受保护目录既有 .kicad_prl 字节快照（变更复原依据）；
3. subprocess 执行 kicad-cli（子命令白名单 pcb/sch/version；cwd=cwd；
   本地子进程，零网络）；
4. 逐目录 prl_hygiene.check_and_restore（新建 sidecar 删除、变更
   sidecar 字节还原、无快照=blocked 不吞）；
5. protected_dirs 零 prl 断言（datasets 红线：任何 .kicad_prl 存在
   即复原/阻断）；
6. 台账追加（JSONL 单行 canonical；调用序号/argv 相对路径/逐目录
   verdict/returncode；无 wall-clock、无主机绝对路径）；
7. 事故（restored/unrestored 任一非空）= 复原**之后** raise
   PrlHygieneIncident（fail-closed：链必须停，不得继续用该调用产物）。

CLI：python -m pcbflow.v4_1.e6prl --cwd DIR [--watch DIR ...]
       [--protected DIR ...] --ledger FILE [--cap N] -- <kicad-cli args...>
退出码：kicad-cli 原码；事故复原后=90；不可复原=91；guard 自身错误=2。

零模型、零网络；kicad-cli 路径默认读 toolchain_lock.json（只读）。
"""

from __future__ import annotations

import json
import os
import subprocess

from . import DECLARED_DATE
from .canonical import dumps_canonical
from .prl_hygiene import (PRL_SUFFIX, check_and_restore, inventory)

__all__ = ["KicadCliGuard", "PrlHygieneIncident", "load_kicad_cli_path",
           "GUARD_SCHEMA", "EXIT_INCIDENT_RESTORED", "EXIT_BLOCKED"]

GUARD_SCHEMA = "pcbflow.v4_1.e6-kicad-cli-guard/1"

#: 事故语义退出码（复原后 fail-closed / 不可复原 blocked）
EXIT_INCIDENT_RESTORED = 90
EXIT_BLOCKED = 91

#: kicad-cli 子命令白名单（防误用 guard 执行任意命令）
_ALLOWED_SUBCOMMANDS = ("pcb", "sch", "version", "sym", "fp", "job")


class PrlHygieneIncident(RuntimeError):
    """kicad-cli 调用引发 prl 副作用（已复原或不可复原）。

    fail-closed：调用链必须停；record 属性携带完整卫生记录供登记。
    """

    def __init__(self, message, record):
        super().__init__(message)
        self.record = record


def load_kicad_cli_path(lock_path="toolchain_lock.json"):
    """toolchain_lock.json（只读）-> kicad-cli 可执行路径。

    缺失/无 kicad_cli 条目 -> ValueError（fail-closed，不猜测路径）。
    """
    try:
        with open(lock_path, "r", encoding="utf-8") as f:
            lock = json.load(f)
    except OSError as exc:
        raise ValueError("toolchain_lock.json 不可读（fail-closed）: %s"
                         % exc)
    entry = (lock or {}).get("kicad_cli") or {}
    path = entry.get("path")
    if not path:
        raise ValueError("toolchain_lock.json 无 kicad_cli.path"
                         "（fail-closed，不猜测路径）")
    return path


class KicadCliGuard:
    """kicad-cli 封装调用器（自动 prl 卫生；E6 制度化主体）。"""

    def __init__(self, ledger_path, kicad_cli=None, watch_dirs=(),
                 protected_dirs=(), call_cap=40):
        self.ledger_path = ledger_path
        self.kicad_cli = kicad_cli or load_kicad_cli_path()
        self.watch_dirs = [d for d in watch_dirs]
        self.protected_dirs = [d for d in protected_dirs]
        self.call_cap = int(call_cap)
        self._seq = 0
        # 台账文件初始化（append-only；不覆盖既有内容）
        led = os.path.dirname(os.path.abspath(ledger_path)) \
            if os.path.dirname(ledger_path) else "."
        if not os.path.isdir(led):
            raise ValueError("台账目录不存在（fail-closed）: %r" % (led,))

    # ------------------------------------------------------------ 内部

    def _watched(self, cwd):
        seen = []
        for d in [cwd] + self.watch_dirs + self.protected_dirs:
            if d not in seen:
                seen.append(d)
        return seen

    def _append_ledger(self, entry):
        line = json.dumps(entry, ensure_ascii=False, sort_keys=True)
        with open(self.ledger_path, "a", encoding="utf-8",
                  newline="\n") as f:
            f.write(line + "\n")

    def _prl_snapshot(self, directory):
        """目录内既有 .kicad_prl -> {名: bytes}（变更复原依据）。"""
        out = {}
        for name in sorted(os.listdir(directory)):
            if name.endswith(PRL_SUFFIX):
                with open(os.path.join(directory, name), "rb") as f:
                    out[name] = f.read()
        return out

    # ------------------------------------------------------------ 主入口

    def call(self, argv, cwd, cwd_role="staging"):
        """执行一次受卫生监护的 kicad-cli 调用。

        返回 (returncode, stdout_text, record)。事故在复原与台账落盘
        **之后** raise PrlHygieneIncident（record 同样可得）。
        """
        if not argv or argv[0] not in _ALLOWED_SUBCOMMANDS:
            raise ValueError("kicad-cli 子命令不在白名单（fail-closed）: %r"
                             % ((argv or [])[:1],))
        if not os.path.isdir(cwd):
            raise ValueError("cwd 不存在（fail-closed）: %r" % (cwd,))
        self._seq += 1
        if self._seq > self.call_cap:
            raise ValueError("kicad-cli 调用数触顶 cap=%d（fail-closed "
                             "停；登记 deviations 后可评估）"
                             % self.call_cap)
        watched = self._watched(cwd)
        before = {}
        prl_snapshots = {}
        for d in watched:
            before[d] = inventory(d)
            prl_snapshots[d] = self._prl_snapshot(d)
        proc = subprocess.run([self.kicad_cli] + list(argv), cwd=cwd,
                              capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
        hygiene = {}
        restored_any = False
        unrestored_any = False
        protected_violation = False
        for d in watched:
            role = ("cwd" if d == cwd else
                    "protected" if d in self.protected_dirs else "watch")
            snap = prl_snapshots[d]
            # check_and_restore 单文件快照口径：逐 sidecar 分别处理
            sub_rec = self._check_dir(d, before[d], snap)
            sub_rec["role"] = role
            hygiene[os.path.basename(d) or d] = sub_rec
            restored_any = restored_any or bool(sub_rec["restored"])
            unrestored_any = unrestored_any or bool(sub_rec["unrestored"])
            if role == "protected":
                leftover = [n for n in inventory(d)
                            if n.endswith(PRL_SUFFIX)]
                if leftover:
                    protected_violation = True
                    sub_rec["protected_zero_prl"] = {
                        "assert": "violated", "files": sorted(leftover)}
                else:
                    sub_rec["protected_zero_prl"] = {"assert": "held"}
        verdict = "clean"
        if unrestored_any or protected_violation:
            verdict = "blocked"
        elif restored_any:
            verdict = "incident_restored"
        record = {
            "schema": GUARD_SCHEMA,
            "declared_date": DECLARED_DATE,
            "call_seq": self._seq,
            "argv": list(argv),
            "cwd_role": cwd_role,
            "returncode": proc.returncode,
            "hygiene": hygiene,
            "verdict": verdict,
        }
        self._append_ledger(record)
        if verdict != "clean":
            msg = ("prl 卫生事故（verdict=%s，已复原=%s，不可复原=%s）"
                   % (verdict, restored_any, unrestored_any))
            raise PrlHygieneIncident(msg, record)
        return proc.returncode, proc.stdout, record

    def _check_dir(self, directory, before, prl_snapshots):
        """单目录卫生检查+复原（逐 sidecar 快照还原）。"""
        base = check_and_restore(directory, before)
        restored = list(base["restored"])
        unrestored = list(base["unrestored"])
        # check_and_restore 无快照路径只登记 unrestored；guard 持有逐文件
        # 快照 -> 补齐字节还原（guard 语义：调用窗口内变化必可复原）
        still = [u["file"] for u in unrestored]
        for name in still:
            data = prl_snapshots.get(name)
            if data is None:
                continue  # 调用前不存在的变更 sidecar：保持 blocked 登记
            with open(os.path.join(directory, name), "wb") as f:
                f.write(data)
            unrestored = [u for u in unrestored if u["file"] != name]
            restored.append({"file": name, "action": "bytes_restored"
                             "_by_guard"})
        final_ok = all(inventory(directory).get(n) == before.get(n)
                       for n in [r["file"] for r in restored]
                       + [u["file"] for u in unrestored])
        return {
            "diff": base["diff"],
            "prl_created": base["prl_created"],
            "prl_changed": base["prl_changed"],
            "restored": restored,
            "unrestored": unrestored,
            "post_restore_matches_before": final_ok,
        }


# ---------------------------------------------------------------- CLI

def main(argv=None):
    """CLI 入口（--cwd/--watch/--protected/--ledger/--cap -- args）。"""
    import argparse
    import sys
    ap = argparse.ArgumentParser(
        prog="pcbflow.v4_1.e6prl",
        description="kicad-cli 封装调用器：自动 prl 卫生检查+复原+台账")
    ap.add_argument("--cwd", required=True)
    ap.add_argument("--watch", action="append", default=[],
                    help="额外监护目录（可重复）")
    ap.add_argument("--protected", action="append", default=[],
                    help="受保护零 prl 目录（可重复；如 datasets/）")
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--cap", type=int, default=40)
    ap.add_argument("cli_args", nargs=argparse.REMAINDER,
                    help="-- 之后为 kicad-cli 参数")
    ns = ap.parse_args(argv)
    rest = ns.cli_args
    if rest and rest[0] == "--":
        rest = rest[1:]
    if not rest:
        ap.error("缺 kicad-cli 参数（-- <args>）")
    guard = KicadCliGuard(ns.ledger, watch_dirs=ns.watch,
                          protected_dirs=ns.protected, call_cap=ns.cap)
    try:
        rc, _stdout, _rec = guard.call(rest, ns.cwd)
    except PrlHygieneIncident as exc:
        rec = exc.record
        code = (EXIT_BLOCKED if rec["verdict"] == "blocked"
                else EXIT_INCIDENT_RESTORED)
        sys.stderr.write("%s\nledger=%s call_seq=%d\n"
                         % (exc, ns.ledger, rec["call_seq"]))
        return code
    sys.stdout.write("clean call_seq=%d returncode=%d\n"
                     % (_rec["call_seq"], rc))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
