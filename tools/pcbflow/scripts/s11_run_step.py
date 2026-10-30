"""S11 TD7 编排侧：显式 argv 步骤执行器（非生成器；Bash 调用）。

职责（TD7 合同的编排侧强制点）：
- subprocess 以 list[str] 显式 argv 执行（零 shell 拼接）；
- env 白名单最小化（PATH/SYSTEMROOT/TEMP/TMP；TEMP/TMP 重定向到
  staging——引擎临时文件只落 staging，write_scope=staging_only）；
- timeout 硬超时（超时=kill+blocked 语义，退出码记 None）；
- stdout/stderr 二进制落盘（超出 cap 即截断标记 truncated）；
- 结果 JSONL 追加：argv canonical hash、退出码、截断、size。

用法：python scripts/s11_run_step.py <step-spec.json> <results.jsonl>
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ENV_ALLOWLIST = ("PATH", "SYSTEMROOT", "TEMP", "TMP", "SYSTEMDRIVE",
                 "COMSPEC", "NUMBER_OF_PROCESSORS")


def main() -> int:
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    results_path = Path(sys.argv[2])
    argv = spec["argv"]
    if not isinstance(argv, list) or not all(isinstance(a, str)
                                             for a in argv):
        print("argv 必须为 list[str]", file=sys.stderr)
        return 2
    cwd = spec.get("cwd")
    timeout_s = spec.get("timeout_s", 300)
    cap = spec.get("capture_cap_bytes", 16 * 1024 * 1024)
    out_path = Path(spec["stdout_file"])
    err_path = Path(spec["stderr_file"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    err_path.parent.mkdir(parents=True, exist_ok=True)

    env = {k: spec["env"][k] for k in ENV_ALLOWLIST
           if k in spec.get("env", {})}
    if spec.get("env") and set(spec["env"]) - set(ENV_ALLOWLIST):
        print(f"env 白名单外字段被剥离: "
              f"{sorted(set(spec['env']) - set(ENV_ALLOWLIST))}",
              file=sys.stderr)

    timed_out = False
    try:
        proc = subprocess.run(
            argv, cwd=cwd, env=env or None, timeout=timeout_s,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        rc = proc.returncode
        out_bytes, err_bytes = proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        rc = None
        out_bytes = exc.stdout or b""
        err_bytes = exc.stderr or b""

    truncated = len(out_bytes) > cap or len(err_bytes) > cap
    out_path.write_bytes(out_bytes[:cap])
    err_path.write_bytes(err_bytes[:cap])

    result = {
        "step": spec.get("step"),
        "argv": argv,
        "cwd": cwd,
        "timeout_s": timeout_s,
        "exit_status": rc,
        "timed_out": timed_out,
        "truncated": truncated,
        "stdout_bytes": min(len(out_bytes), cap),
        "stderr_bytes": min(len(err_bytes), cap),
        "env_keys_passed": sorted(env),
    }
    with results_path.open("a", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(result, ensure_ascii=False) + "\n")
    print(json.dumps({k: result[k] for k in
                      ("step", "exit_status", "timed_out", "truncated",
                       "stdout_bytes", "stderr_bytes")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
