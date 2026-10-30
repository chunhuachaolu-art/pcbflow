"""pcbflow.v4_1.prl_hygiene -- .kicad_prl sidecar 卫生（E6 纪律提前生效；
任务书 §4：E6 中 prl 卫生项自 E1 起生效）。

事故锚：holdout-r1 红线首破（.kicad_prl sidecar 意外生成/污染，见任务书
§1 K7）。纪律：kicad-cli 每次调用前后目录盘点，发现 sidecar 新增/变更即
登记并复原。

用法（编排侧；本模块只提供可测试的纯函数与记录结构）：

    before = inventory(staging_dir)
    <kicad-cli 调用（由 Bash 侧执行；本包零子进程红线不破）>
    rec = check_and_restore(staging_dir, before)

check_and_restore 返回：sidecar_created/sidecar_changed 清单、复原动作
（删除新建 sidecar / 还原变更 sidecar 字节）、live 板目录与 datasets/
零 prl 断言的采集点。
"""

from __future__ import annotations

import hashlib
import os

from . import DECLARED_DATE

__all__ = ["inventory", "diff_inventories", "check_and_restore",
           "PRL_SUFFIX", "DATASETS_ZERO_PRL_ASSERT"]

PRL_SUFFIX = ".kicad_prl"
DATASETS_ZERO_PRL_ASSERT = ("datasets/ 零 .kicad_prl（红线；盘点由编排侧"
                            "对 <repo>/datasets 执行 inventory 后断言空）")

_HYGIENE_SCHEMA = "pcbflow.v4_1.prl-hygiene/1"


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def inventory(directory):
    """目录盘点 -> {相对名: {"size": n, "sha256": h}}（确定性：名字排序）。

    仅文件（跳过子目录）；目录不存在 -> ValueError（fail-closed）。
    """
    if not os.path.isdir(directory):
        raise ValueError("盘点目录不存在（fail-closed）: %r" % (directory,))
    out = {}
    for name in sorted(os.listdir(directory)):
        p = os.path.join(directory, name)
        if os.path.isfile(p):
            out[name] = {"size": os.path.getsize(p),
                         "sha256": _sha256_file(p)}
    return out


def diff_inventories(before, after):
    """两次盘点差分 -> created/changed/removed（相对名列表）。"""
    created = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(n for n in set(before) & set(after)
                     if before[n] != after[n])
    return {"created": created, "changed": changed, "removed": removed}


def check_and_restore(directory, before, snapshot_bytes=None):
    """kicad-cli 调用后卫生检查 + 复原。

    - 新建 .kicad_prl -> 删除（复原）；
    - 变更 .kicad_prl：若给出 snapshot_bytes（调用前字节）-> 字节还原；
      未给出 -> 登记 unrestored（blocked 语义）；
    - 其余新建/变更文件：不自动处置，登记（供人工裁决）。
    返回 canonical-ready 记录 dict。
    """
    after = inventory(directory)
    diff = diff_inventories(before, after)
    prl_created = [n for n in diff["created"]
                   if n.endswith(PRL_SUFFIX)]
    prl_changed = [n for n in diff["changed"]
                   if n.endswith(PRL_SUFFIX)]
    restored, unrestored = [], []
    for n in prl_created:
        os.remove(os.path.join(directory, n))
        restored.append({"file": n, "action": "deleted_new_sidecar"})
    for n in prl_changed:
        if snapshot_bytes is not None:
            with open(os.path.join(directory, n), "wb") as f:
                f.write(snapshot_bytes)
            restored.append({"file": n, "action": "bytes_restored"})
        else:
            unrestored.append({"file": n,
                               "action": "unrestored_no_snapshot",
                               "status": "blocked"})
    final = inventory(directory)
    final_ok = all(final.get(n) == before.get(n)
                   for n in prl_created + prl_changed)
    return {
        "schema": _HYGIENE_SCHEMA,
        "declared_date": DECLARED_DATE,
        "directory_role": "staging",
        "diff": diff,
        "prl_created": prl_created,
        "prl_changed": prl_changed,
        "restored": restored,
        "unrestored": unrestored,
        "post_restore_matches_before": final_ok,
        "datasets_zero_prl_assert": DATASETS_ZERO_PRL_ASSERT,
        "verdict": "clean" if not (prl_created or prl_changed) else (
            "restored" if final_ok and not unrestored else "blocked"),
    }
