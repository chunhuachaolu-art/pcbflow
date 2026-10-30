"""toolchain lock 生成器：stdin 读探测 JSON → stdout 出 lock。

探测由会话在 shell 中执行（pcbflow .py 零子进程/零落盘，Mimosa 钩子）：
  "F:/kicad/bin/kicad-cli.exe" version
  "F:/kicad/bin/python.exe" --version
  "F:/kicad/bin/python.exe" -c "import pcbnew; print(pcbnew.GetBuildVersion())"
  ... 等，见 toolchain.REQUIRED_PROBES

用法：
  echo '{"kicad_cli_version": "...", ...}' | \
    python scripts/probe_toolchain.py > toolchain_lock.json
"""

from __future__ import annotations

import json
import sys

from pcbflow import hashing, toolchain


def main() -> int:
    probes = json.load(sys.stdin)
    lock = toolchain.make_lock(probes)
    sys.stdout.buffer.write(hashing.canonical_json_bytes(lock))
    return 0


if __name__ == "__main__":
    sys.exit(main())
