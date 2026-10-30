"""corpus-r2-r1 数据集对账断言（仿 tests/test_tl5_kicad_demo.py 真实库回放模式）。

datasets/ 只读：全部断言基于盘面递归清单 + 37 份 metadata.json 全量重算
（sha256 逐板复算、不抽样），与 datasets/corpus-r2-r1/manifest.json 的
counts 对账。口径要点（读自 manifest counts_note 与盘面实测）：

- total_files = raw 板文件(.kicad_pcb) + metadata + licenses 原文，不含根登记
  文件（manifest.json / PROVENANCE.md）；本 manifest 中 raw_files 与
  total_files 同为 114（= raw/ 74 + licenses/ 40）。
- total_files_with_root = total_files + 根登记文件 2 个 = 116。
- total_bytes 按 counts_note "含根登记文件"。2026-09-12 收口校准批
  （五工执行侧 + H5 残留补登 + 快照刷新）之后为「数据文件实和 + root
  实和」精确等式（181,803,029），无快照豁免（见
  test_total_bytes_reconciles）。
"""

from __future__ import annotations

import collections
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbflow import hashing

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DS = os.path.join(REPO, "datasets", "corpus-r2-r1")
MANIFEST = os.path.join(DS, "manifest.json")

# total_bytes 口径见 test_total_bytes_reconciles：2026-09-12 收口校准批
# 后为「数据文件实和 + 根登记文件实和」的精确等式，无快照豁免常量。

_META_CACHE: dict = {}


def _manifest():
    with open(MANIFEST, encoding="utf-8") as f:
        return json.load(f)


def _metadata(dir_name):
    """读取 raw/<dir>/metadata.json（带缓存）。"""
    if dir_name not in _META_CACHE:
        with open(os.path.join(DS, "raw", dir_name, "metadata.json"),
                  encoding="utf-8") as f:
            _META_CACHE[dir_name] = json.load(f)
    return _META_CACHE[dir_name]


def _walk_rel():
    """数据集目录递归文件清单（相对路径，/ 分隔，排序）。"""
    out = []
    for dirpath, _, files in os.walk(DS):
        for fn in files:
            rel = os.path.relpath(os.path.join(dirpath, fn), DS)
            out.append(rel.replace(os.sep, "/"))
    return sorted(out)


def _board_dirs():
    return sorted(d for d in os.listdir(os.path.join(DS, "raw"))
                  if os.path.isdir(os.path.join(DS, "raw", d)))


# ---------------- 1. counts vs 盘面文件清单 ----------------

def test_counts_files_match_disk_inventory():
    m = _manifest()
    c = m["counts"]
    all_rel = _walk_rel()
    root_rel = sorted(p for p in all_rel if "/" not in p)
    data_rel = [p for p in all_rel if p not in root_rel]

    # 根登记文件：manifest 声明与盘面一致（2 个，且不含子目录杂物）
    assert sorted(c["root_files"]) == root_rel == ["PROVENANCE.md",
                                                   "manifest.json"]

    # boards / board_dirs：37 板、37 目录，manifest boards[] 与盘面目录一一对应
    disk_dirs = _board_dirs()
    assert c["boards"] == c["board_dirs"] == len(disk_dirs) == 37
    assert len(m["boards"]) == 37
    assert sorted(b["dir"].split("/")[-1] for b in m["boards"]) == disk_dirs
    assert len({b["board_id"] for b in m["boards"]}) == 37

    # raw/ 每板恰 1 个 .kicad_pcb + 1 个 metadata.json，无其他杂物
    raw_rel = [p for p in data_rel if p.startswith("raw/")]
    pcb_rel = [p for p in raw_rel if p.endswith(".kicad_pcb")]
    meta_rel = [p for p in raw_rel if p.endswith("metadata.json")]
    assert len(raw_rel) == 2 * 37 and len(pcb_rel) == 37
    assert len(meta_rel) == 37
    # boards[].files 声明与 raw/ 盘面完全一致（74 个）
    declared = sorted(b["dir"] + "/" + f
                      for b in m["boards"] for f in b["files"])
    assert declared == sorted(raw_rel)
    # boards[].bytes == 该板目录逐文件 stat 求和
    for b in m["boards"]:
        d = os.path.join(DS, b["dir"])
        on_disk = sum(os.path.getsize(os.path.join(d, f))
                      for f in os.listdir(d))
        assert b["bytes"] == on_disk, b["board_id"]

    # license_files：盘面 licenses/ 40 个
    lic_rel = [p for p in data_rel if p.startswith("licenses/")]
    assert c["license_files"] == len(lic_rel) == 40

    # total_files（counts_note：板文件+metadata+licenses，不含根登记文件）
    assert c["total_files"] == len(data_rel) == 114
    # raw_files 与 total_files 同值：= raw/ 74 + licenses/ 40 个数据文件
    assert c["raw_files"] == len(data_rel) == 114

    # total_files_with_root = total_files + 根登记文件数 = 全目录递归总数
    assert c["total_files_with_root"] \
        == c["total_files"] + len(root_rel) == len(all_rel) == 116


def test_manifest_license_evidence_entries_match_disk():
    """manifest['licenses'] 证据表逐条对账（40 条全部与盘面相符）。"""
    m = _manifest()
    seen = set()
    for e in m["licenses"]:
        fp = os.path.join(DS, e["file"])
        assert os.path.isfile(fp), e["file"]
        assert os.path.getsize(fp) == e["bytes"], e["file"]
        assert hashing.sha256_file(fp) == e["sha256"], e["file"]
        seen.add(os.path.basename(e["file"]))
    assert len(seen) == 40
    # 2026-09-12 收口校准批补登 H5 scalenode 的 LICENSE 后，证据表与
    # 盘面/37 板 metadata 的 license_files_archived 并集三方全等（40）。
    archived = set()
    for d in _board_dirs():
        md = _metadata(d)
        archived.update(md.get("license_files_archived", []))
    disk_lic = {os.path.basename(p)
                for p in _walk_rel() if p.startswith("licenses/")}
    assert archived == disk_lic == seen and len(disk_lic) == 40


# ---------------- 2. total_bytes ----------------

def test_total_bytes_reconciles():
    m = _manifest()
    c = m["counts"]
    root_rel = set(c["root_files"])
    data_sum = root_sum = 0
    for rel in _walk_rel():
        size = os.path.getsize(os.path.join(DS, rel))
        if rel in root_rel:
            root_sum += size
        else:
            data_sum += size
    # 语义（counts_note：total_bytes 含根登记文件）：数据文件实和 +
    # 根登记文件实和。2026-09-12 收口校准批已把快照刷新至当前盘面
    # （181,803,029），此断言回到无豁免的精确等式（任一侧漂移即红）。
    assert data_sum + root_sum == c["total_bytes"]
    assert root_sum > 0


# ---------------- 3. 逐板 sha256 全覆盖（37 板，不抽样） ----------------

def test_board_pcb_and_license_hashes_full_coverage():
    m = _manifest()
    by_id = {b["board_id"]: b for b in m["boards"]}
    assert len(by_id) == 37
    checked = 0
    for d in _board_dirs():
        md = _metadata(d)
        # .kicad_pcb：盘面 sha256/bytes == metadata.evidence
        pcb_fp = os.path.join(DS, "raw", *md["raw"].split("/"))
        assert os.path.isfile(pcb_fp), md["raw"]
        assert os.path.getsize(pcb_fp) == md["evidence"]["file_bytes"], d
        assert hashing.sha256_file(pcb_fp) \
            == md["evidence"]["file_sha256"], d
        # license 原文：存在且 sha256 == metadata.license_sha256
        lic_fp = os.path.join(DS, *md["license_file"].split("/"))
        assert os.path.isfile(lic_fp), md["license_file"]
        assert hashing.sha256_file(lic_fp) == md["license_sha256"], d
        # 补充对账：manifest boards[] 同板条目与 metadata/盘面一致
        b = by_id[md["board_id"]]
        assert b["dir"].split("/")[-1] == d
        assert b["board_file_sha256"] == md["evidence"]["file_sha256"]
        assert b["license"]["sha256"] == md["license_sha256"]
        assert b["license"]["spdx"] == md["licenses"][0]["spdx_id"]
        checked += 1
    assert checked == 37


def test_h5_addendum_verified_fields_match_disk():
    """H5 scalenode 补录的 verified 哈希与盘面/meta 三方一致。"""
    m = _manifest()
    h5 = m["h5_addendum"]
    md = _metadata("antmicro__scalenode-cm4-baseboard")
    pcb_fp = os.path.join(DS, "raw", *md["raw"].split("/"))
    assert os.path.getsize(pcb_fp) == h5["verified"]["pcb_bytes"]
    assert hashing.sha256_file(pcb_fp) == h5["verified"]["pcb_sha256"]
    lic_fp = os.path.join(DS, *md["license_file"].split("/"))
    assert hashing.sha256_file(lic_fp) \
        == h5["verified"]["license_sha256"]


# ---------------- 4. 分桶重算 vs counts ----------------

def test_bucket_counts_recomputed_from_metadata():
    m = _manifest()
    c = m["counts"]
    metas = [_metadata(d) for d in _board_dirs()]
    assert len(metas) == 37
    tier = collections.Counter(x["tier_designation"] for x in metas)
    spdx = collections.Counter(x["licenses"][0]["spdx_id"] for x in metas)
    bucket = collections.Counter(x["kicad_version_token"] for x in metas)
    layers = collections.Counter(str(x["layers"]) for x in metas)
    assert dict(tier) == c["by_tier"]
    assert dict(spdx) == c["by_license_spdx"]
    assert dict(bucket) == c["by_version_bucket"]
    assert dict(layers) == c["by_layers"]
    assert sum(c["by_tier"].values()) == 37
    assert sum(c["by_license_spdx"].values()) == 37
    assert sum(c["by_version_bucket"].values()) == 37
    assert sum(c["by_layers"].values()) == 37
    # manifest boards[] 条目与同板 metadata 在分桶四维上一致
    by_id = {b["board_id"]: b for b in m["boards"]}
    for x in metas:
        b = by_id[x["board_id"]]
        assert b["tier_designation"] == x["tier_designation"]
        assert b["kicad_version_token"] == x["kicad_version_token"]
        assert b["layers"] == x["layers"]


# ---------------- 5. holdout 池与永不 holdout ----------------

def test_holdout_pool_boards_on_disk_with_single_pcb():
    m = _manifest()
    c = m["counts"]
    pool = c["holdout_pool"]
    assert len(pool) == 6
    by_id = {b["board_id"]: b for b in m["boards"]}
    seen_ids = set()
    for entry in pool:
        pool_id, board_id = entry.split(":", 1)
        seen_ids.add(pool_id)
        # 盘面在板，且目录内恰 1 个 .kicad_pcb
        board_dir = os.path.join(DS, "raw")
        d = [x for x in _board_dirs() if by_id[board_id]["dir"]
             == "raw/" + x]
        assert len(d) == 1, board_id
        pcbs = [f for f in os.listdir(os.path.join(board_dir, d[0]))
                if f.endswith(".kicad_pcb")]
        assert len(pcbs) == 1, board_id
        # 三方同指同一池位：counts / manifest boards[] / metadata
        b = by_id[board_id]
        assert b["holdout"]["pool_id"] == pool_id
        assert b["tier_designation"] == "holdout-pool"
        md = _metadata(d[0])
        assert md["tier_designation"] == "holdout-pool"
        assert md["holdout_pool"]["pool_id"] == pool_id
    assert seen_ids == {"H1", "H2", "H3", "H4", "H5", "H6"}
    # 池外 31 板均为 train/val-candidate 且不入池
    pool_board_ids = {e.split(":", 1)[1] for e in pool}
    assert len(pool_board_ids) == 6
    for b in m["boards"]:
        if b["board_id"] not in pool_board_ids:
            assert b["tier_designation"] == "train/val-candidate"
            assert b["holdout"] is None


def test_never_holdout_boards_registered_and_on_disk():
    m = _manifest()
    c = m["counts"]
    by_id = {b["board_id"]: b for b in m["boards"]}
    assert len(c["never_holdout"]) == 3
    for board_id in c["never_holdout"]:
        b = by_id[board_id]
        assert b["never_holdout"] is True
        assert b["tier_designation"] == "train/val-candidate"
        d = b["dir"].split("/")[-1]
        assert os.path.isdir(os.path.join(DS, "raw", d)), board_id
        md = _metadata(d)
        assert md["never_holdout"], board_id
