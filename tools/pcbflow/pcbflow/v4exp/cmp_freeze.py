"""pcbflow.v4exp.cmp_freeze -- v4cmp 冻结点存证（hash 清单）。

CLI（stdin JSON -> stdout canonical JSON；无写盘、无 argv、无时钟）：
  {"root": "out/v4-comparative-experiment",
   "repo": ".",
   "code_globs": ["pcbflow/v4exp/cmp_patch.py", ...],
   "extra_files": ["V4-COMPREHENSIVE-...md"]}

产出 `freeze-inputs.json` 的内容：
* protocol 文件哈希（experiment-plan.json / hash-contract / taskbook）；
* v4cmp 代码文件哈希（本轮实现，冻结点后不得再改）；
* 数据集哈希（scenario-manifest 与全部 board-snapshot）；
* planner 输入与响应哈希（存在多少记多少，缺失不隐藏）；
* 环境声明（python 版本、PIL 版本；PNG 为非 canonical 投影）。

注意：本模块只读文件与报告版本，不做任何几何或实验判定。
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import sys


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _rel(repo: str, path: str) -> str:
    return os.path.relpath(path, repo).replace("\\", "/")


def hash_list(repo: str, paths: list) -> dict:
    out = {}
    for p in paths:
        full = p if os.path.isabs(p) else os.path.join(repo, p)
        if os.path.exists(full):
            out[_rel(repo, full)] = sha256_file(full)
        else:
            out[_rel(repo, full)] = None
    return out


def _glob_with(repo: str, prefix: str, suffix: str) -> list:
    d = os.path.join(repo, os.path.dirname(prefix))
    base = os.path.basename(prefix)
    if not os.path.isdir(d):
        return []
    return sorted(os.path.join(d, n) for n in os.listdir(d)
                  if n.startswith(base) and n.endswith(suffix))


def build(root: str, repo: str, code_files: list, extra_files: list) -> dict:
    boards = _glob_with(repo, os.path.join(root, "board-snapshot-"), ".json")
    inputs = _glob_with(repo, os.path.join(root, "p2", "inputs",
                                           "planner-input-"), ".json")
    responses = _glob_with(repo, os.path.join(root, "p2", "responses",
                                              "planner-response-"), ".json")
    pngs = _glob_with(repo, os.path.join(root, "p2", "png",
                                         "route-preview-"), ".png")
    protocol_files = [
        os.path.join(root, "protocol", "experiment-plan.json"),
        os.path.join(root, "p0", "hash-contract-v1.json"),
        os.path.join(root, "p0", "prior-g4-correction-v1.json"),
        os.path.join(root, "p0", "metric-recompute.json"),
        os.path.join(root, "scenario-manifest.json"),
        os.path.join(root, "scenario-hash-dedup.json"),
    ] + extra_files
    try:
        from PIL import __version__ as pil_version
    except Exception:
        pil_version = None
    return {
        "schema": "pcbflow.v4cmp.freeze-inputs/1",
        "freeze_id": "v4cmp-freeze-20260910-v1",
        "root": root,
        "protocol_files_sha256": hash_list(repo, protocol_files),
        "code_files_sha256": hash_list(repo, code_files),
        "dataset": {
            "board_snapshot_count": len(boards),
            "board_snapshot_sha256": hash_list(repo, boards),
        },
        "planner_artifacts": {
            "inputs_count": len(inputs),
            "inputs_sha256": hash_list(repo, inputs),
            "responses_count": len(responses),
            "responses_sha256": hash_list(repo, responses),
        },
        "png_projection": {
            "count": len(pngs),
            "note": "PNG 是视觉投影，非 canonical 核心产物；其字节依赖渲染器/"
                    "PIL 版本，因此仅留证不参与重放一致性判定。",
            "sha256": hash_list(repo, pngs),
        },
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "pil": pil_version,
        },
        "freeze_rule": "本清单生成后，protocol 与 cmp_* 代码不得再修改；"
                       "任何后续改动必须写入 deviations 并在报告中显式声明。",
    }


def main():
    payload = json.loads(sys.stdin.read())
    out = build(payload["root"], payload.get("repo", "."),
                payload["code_files"], payload.get("extra_files", []))
    sys.stdout.write(json.dumps(out, sort_keys=True, ensure_ascii=False)
                     + "\n")


if __name__ == "__main__":
    main()
