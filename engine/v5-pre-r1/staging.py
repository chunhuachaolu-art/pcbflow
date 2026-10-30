# -*- coding: utf-8 -*-
"""staging/rollback 基础设施（任务书 §3.4 证据原子提交 + L6/L7 事务）。

- 整份齐全后一次性提交进 evidence，禁止半成品证据目录（append-only）。
- 中断注入→自动回滚到一致点、无残留（P0 单测）。
- 提交后不可变（append-only）：同事务二次提交/回滚抛错。
"""
import json
import os
import shutil

JOURNAL_NAME = "_journal.json"


class StagingError(RuntimeError):
    pass


class StagingTransaction:
    """原子提交事务：staging 目录积累 → commit() 一次性 os.replace 进 final。

    用法：
        tx = StagingTransaction(staging_root, final_root, name)
        tx.write_bytes("a.json", b"...")
        tx.commit()          # 或 tx.rollback()
    中断恢复：recover(staging_root, final_root) 清理全部残留 staging（final 不动）。
    """

    def __init__(self, staging_root, final_root, name):
        self.staging_root = staging_root
        self.final_root = final_root
        self.name = name
        self.staging_dir = os.path.join(staging_root, name)
        self.final_dir = os.path.join(final_root, name)
        self._committed = False
        self._rolled_back = False
        self._files = []
        os.makedirs(self.staging_dir, exist_ok=True)
        self._write_journal("open")

    def _write_journal(self, state):
        with open(os.path.join(self.staging_dir, JOURNAL_NAME), "w", encoding="utf-8") as f:
            json.dump({"name": self.name, "state": state,
                       "files": self._files}, f, ensure_ascii=False, indent=1)

    def write_bytes(self, rel_path, data: bytes):
        if self._committed:
            raise StagingError("事务已提交，禁止再写: %s" % rel_path)
        if self._rolled_back:
            raise StagingError("事务已回滚，禁止再写: %s" % rel_path)
        if rel_path.startswith("/") or ".." in rel_path.replace("\\", "/").split("/"):
            raise StagingError("非法相对路径: %s" % rel_path)
        target = os.path.join(self.staging_dir, rel_path)
        os.makedirs(os.path.dirname(target) or self.staging_dir, exist_ok=True)
        with open(target, "wb") as f:
            f.write(data)
        if rel_path not in self._files:
            self._files.append(rel_path)
            self._write_journal("writing")
        return target

    def write_json(self, rel_path, obj):
        from . import canonical
        return self.write_bytes(rel_path, canonical.canonical_json(obj))

    def commit(self):
        if self._committed:
            raise StagingError("重复提交: %s" % self.name)
        if self._rolled_back:
            raise StagingError("已回滚事务不可提交: %s" % self.name)
        if not self._files:
            raise StagingError("空事务不可提交: %s" % self.name)
        self._write_journal("committing")
        os.makedirs(self.final_dir, exist_ok=True)
        for rel in sorted(self._files):
            src = os.path.join(self.staging_dir, rel)
            dst = os.path.join(self.final_dir, rel)
            os.makedirs(os.path.dirname(dst) or self.final_dir, exist_ok=True)
            os.replace(src, dst)
        self._write_journal("committed")
        shutil.rmtree(self.staging_dir)
        self._committed = True

    def rollback(self):
        if self._committed:
            raise StagingError("已提交事务不可回滚: %s" % self.name)
        if os.path.isdir(self.staging_dir):
            shutil.rmtree(self.staging_dir)
        self._rolled_back = True

    @property
    def committed(self):
        return self._committed

    @property
    def rolled_back(self):
        return self._rolled_back


def recover(staging_root, final_root):
    """崩溃恢复：清空 staging_root 全部残留（含半开 journal）；final_root 不动。

    返回清理的 staging 目录名列表。final_root 中已提交产物不受影响（os.replace 原子性）。
    """
    cleaned = []
    if not os.path.isdir(staging_root):
        return cleaned
    for name in sorted(os.listdir(staging_root)):
        shutil.rmtree(os.path.join(staging_root, name))
        cleaned.append(name)
    return cleaned


def assert_no_residue(staging_root):
    """rollback 后 staging_root 必须无该事务残留（P0 门：无残留测试）。"""
    if not os.path.isdir(staging_root):
        return True
    residue = [n for n in os.listdir(staging_root)]
    if residue:
        raise StagingError("staging 残留: %s" % residue)
    return True


def evidence_list(final_root):
    """final 目录已提交产物清单（append-only 视图）。"""
    if not os.path.isdir(final_root):
        return []
    out = []
    for name in sorted(os.listdir(final_root)):
        d = os.path.join(final_root, name)
        if os.path.isdir(d):
            out.extend("%s/%s" % (name, f) for f in sorted(os.listdir(d)))
        else:
            out.append(name)
    return out
