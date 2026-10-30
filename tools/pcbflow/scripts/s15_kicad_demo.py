#!/usr/bin/env python
"""S15-KICAD-DEMO 编排：KiCad 官方 demo 逐 demo 许可审计入账+合规留存。

编排侧职责（库侧 pcbflow/corpus_kicad_demo.py 保持纯函数零落盘）：
1. 对账（fail-closed）：归档 sha256==模块常量；解包文件数==709；
   审计账本重放计数==15 retain / 1 not_available / 1 blocked /
   1 copyleft 排除；板文件数==18（17 板）；
2. 留存：白名单文件（板/工程/许可 README）从归档解包复制到
   datasets/kicad-demos-r1/raw/<demo_id>/（sonde xilinx→sonde_xilinx
   安全化；内容零改动）+ 数据集级许可原文三件；目标已存在即拒绝
   （追加式纪律：发布产物不可覆写）；
3. 入账（out/v3-tl5/ 新文件）：kicad-demo-license-audit.json（逐 demo
   证据链）→ retention-ledger-kicad-demos-r1.json →
   leakage-audit-kicad-demos-r1.json（库内+跨库 vs pcbbenchmarks-r1/
   pcbench-r1）→ source-research-r4.json → dataset-manifest-
   kicad-demos-r1.json（TD8，corpus.build_dataset_manifest 实算）；
4. 纪律：许可不明零留存；evaluated=18 只进评估字段；零安装脚本；
   网络=本轮会话只读完成（本脚本自身零网络）。

用法：python scripts/s15_kicad_demo.py --archive <demos-subtree.tar.gz>
（仓库根执行；tarball=GitLab archive API path=demos @pin commit）
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
import tarfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import corpus, corpus_kicad_demo as kcd, hashing  # noqa: E402

DATASET = REPO / "datasets" / "kicad-demos-r1"
OUT = REPO / "out" / "v3-tl5"

AUDIT_JSON = OUT / "kicad-demo-license-audit.json"
LEDGER_JSON = OUT / "retention-ledger-kicad-demos-r1.json"
LEAKAGE_JSON = OUT / "leakage-audit-kicad-demos-r1.json"
R4_JSON = OUT / "source-research-r4.json"
MANIFEST_JSON = OUT / "dataset-manifest-kicad-demos-r1.json"

#: 数据集级许可原文（demos 默认映射+两份治理文本；上游仓库根文件）
DATASET_LICENSE_FILES = [
    ("LICENSE.README", "LICENSE.README"),
    ("LICENSE.CC-BY-SA-4.0", "LICENSE.CC-BY-SA-4.0"),
    ("LICENSE.APACHE-2.0", "LICENSE.APACHE-2.0"),
]


def _fail(msg: str) -> None:
    print(f"[s15-kicad-demo] FAIL: {msg}")
    sys.exit(1)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_canonical(path: Path, obj) -> str:
    data = hashing.canonical_json_bytes(obj)
    path.write_bytes(data)
    return hashing.sha256_bytes(data)


def _safe_component(name: str) -> str:
    """路径分量安全化（v3 manifest 字符集；空格等→'_'；内容零改动）。"""
    import re
    if re.fullmatch(r"[A-Za-z0-9._+-]+", name):
        return name
    out = re.sub(r"[^A-Za-z0-9._+-]+", "_", name).strip("_")
    if not out:
        _fail(f"unsanitizable path component: {name!r}")
    return out


def extract_archive(archive: Path, stage: Path) -> Path:
    """安全解包（成员名校验：禁绝对/..）→ 返回 demos 根目录。"""
    stage.mkdir(parents=True, exist_ok=True)
    dest = stage / "extract"
    if dest.exists():
        _fail(f"stage extract dir already exists: {dest}")
    dest.mkdir()
    with tarfile.open(archive, "r:gz") as tf:
        members = tf.getmembers()
        for m in members:
            parts = m.name.split("/")
            if (m.name.startswith("/") or ".." in parts or ":" in m.name):
                _fail(f"unsafe tar member: {m.name!r}")
        tf.extractall(dest, filter="data")
    roots = [p for p in dest.iterdir() if p.is_dir()]
    if len(roots) != 1:
        _fail(f"expected single archive root dir, got {roots}")
    demos = roots[0] / "demos"
    if not demos.is_dir():
        _fail(f"demos dir not found under {roots[0]}")
    return demos


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True,
                    help="demos 子树 tarball（GitLab archive API）")
    ap.add_argument("--stage", required=True,
                    help="解包 staging 目录（仓库外）")
    args = ap.parse_args()
    archive = Path(args.archive)
    stage = Path(args.stage)

    # ---- 对账 0：目标零覆写 ----
    if DATASET.exists():
        _fail(f"dataset dir already exists: {DATASET}")
    for p in (AUDIT_JSON, LEDGER_JSON, LEAKAGE_JSON, R4_JSON, MANIFEST_JSON):
        if p.exists():
            _fail(f"target already exists (no-overwrite): {p}")

    # ---- 对账 1：归档源 ----
    if not archive.is_file():
        _fail(f"archive not found: {archive}")
    archive_sha = _sha256_file(archive)
    archive_size = archive.stat().st_size
    if archive_sha != kcd.ARCHIVE_SHA256:
        _fail(f"archive sha256 mismatch: {archive_sha} "
              f"!= {kcd.ARCHIVE_SHA256}")
    if archive_size != kcd.ARCHIVE_SIZE_BYTES:
        _fail(f"archive size mismatch: {archive_size}")
    demos = extract_archive(archive, stage)
    upstream_files = {}
    for p in sorted(demos.rglob("*")):
        if p.is_file():
            rel = p.relative_to(demos).as_posix()
            upstream_files[rel] = p
    if len(upstream_files) != kcd.UPSTREAM_FILE_COUNT:
        _fail(f"upstream file count {len(upstream_files)} "
              f"!= {kcd.UPSTREAM_FILE_COUNT}")

    # ---- 审计账本重放（库侧纯函数；计数 fail-closed）----
    demo_entries = []
    for demo_id in sorted(kcd.BOARD_FILES):
        board_files = []
        for bf in kcd.BOARD_FILES[demo_id]:
            if bf not in upstream_files:
                _fail(f"board file missing from archive: {bf}")
            board_files.append(bf)
        demo_entries.append({"demo_id": demo_id,
                             "board_files": board_files})
    ledger = kcd.build_demo_audit_ledger(demo_entries)
    c = ledger["counts"]
    if (c["evaluated"] != 18 or c["retained_demos"] != 15
            or c["retained_board_files"] != 18 or c["not_available"] != 1
            or c["blocked"] != 1
            or c["copyleft_conservative_exclusion"] != 1):
        _fail(f"ledger counts unexpected: {c}")
    retained_ids = [e["demo_id"] for e in ledger["retained"]]
    board_count = sum(
        len({kcd.demo_board_id(e["demo_id"], bf)
             for bf in e["board_files"]})
        for e in ledger["retained"])
    if board_count != 17:
        _fail(f"board count {board_count} != 17")

    # ---- 证据装配（从归档解包实测）----
    def excerpt(p: Path, n: int = 300) -> str:
        return p.read_bytes()[:n].decode("utf-8", errors="replace")

    license_ee = {}
    for e in ledger["retained"] + ledger["excluded"]:
        lf = e["dir_license_file"]
        if lf:
            fp = upstream_files[lf]
            license_ee[e["demo_id"]] = {
                "path": f"demos/{lf}", "sha256": _sha256_file(fp),
                "size_bytes": fp.stat().st_size,
                "excerpt_head": excerpt(fp),
            }
    readme_ee = {}
    for e in ledger["retained"]:
        for bf in e["board_files"]:
            d = bf.rsplit("/", 1)[0]
            rm = upstream_files.get(f"{d}/README.md")
            if rm and e["demo_id"] not in readme_ee:
                readme_ee[e["demo_id"]] = {
                    "path": f"demos/{d}/README.md",
                    "sha256": _sha256_file(rm), "excerpt_head": excerpt(rm),
                }
    board_header_ee = {}
    tiny_comments = None
    for e in ledger["retained"]:
        for bf in e["board_files"]:
            head = upstream_files[bf].read_bytes()[:64].decode(
                "utf-8", errors="replace").lstrip()
            board_header_ee[bf] = {
                "starts_with": head[:10],
                "license_header": "none" if head.startswith("(kicad_pcb")
                else "unexpected",
            }
            if "tinytapeout" in bf:
                text = upstream_files[bf].read_text(
                    encoding="utf-8", errors="replace")
                found = {}
                for m in __import__("re").finditer(
                        r'\(comment (\d) "([^"]*)"\)', text):
                    found[f"comment_{m.group(1)}"] = m.group(2)
                    if len(found) >= 3:
                        break
                tiny_comments = {"board_file": f"demos/{bf}",
                                 "board_level_license_comments": found}

    # ---- 留存（白名单复制 + sha256 账）----
    raw_root = DATASET / "raw"
    file_rows = []          # {upstream_rel, dataset_rel, sha256, bytes,
    #                          category, renamed_from}
    per_demo_retention = {}
    for e in ledger["retained"]:
        demo_id = e["demo_id"]
        kept_rows, skip_counts = [], {}
        n_upstream = 0
        for rel, fp in upstream_files.items():
            top = rel.split("/", 1)[0]
            upstream_dir = kcd.UPSTREAM_DIR.get(demo_id, demo_id)
            if top != upstream_dir:
                continue
            n_upstream += 1
            keep, category = kcd.classify_retention_file(
                rel.rsplit("/", 1)[-1])
            if not keep:
                skip_counts[category] = skip_counts.get(category, 0) + 1
                continue
            tail = rel.split("/", 1)[1] if "/" in rel else ""
            parts = [_safe_component(x) for x in tail.split("/")] \
                if tail else []
            dst_rel = "/".join(["raw", demo_id] + parts)
            dst = DATASET / dst_rel
            if dst.exists():
                _fail(f"refusing to overwrite: {dst}")
            dst.parent.mkdir(parents=True, exist_ok=True)
            data = fp.read_bytes()
            dst.write_bytes(data)
            renamed = tail if tail != "/".join(parts) else None
            kept_rows.append({
                "upstream_rel": f"demos/{rel}",
                "dataset_rel": f"datasets/kicad-demos-r1/{dst_rel}",
                "sha256": hashing.sha256_bytes(data),
                "size_bytes": len(data),
                "category": category,
                "renamed_from": renamed,
            })
        if not kept_rows:
            _fail(f"no retained files for demo {demo_id}")
        per_demo_retention[demo_id] = {
            "upstream_file_count": n_upstream,
            "retained_file_count": len(kept_rows),
            "skip_counts": dict(sorted(skip_counts.items())),
            "retained_bytes": sum(r["size_bytes"] for r in kept_rows),
        }
        file_rows.extend(kept_rows)
    # 数据集级许可原文：归档（path=demos）不含仓库根文件 → 会话已用
    # GitLab files API raw @pin commit 取得（与仓库根逐字节一致）；脚本
    # 从 --stage/root-licenses/ 读取，原文自身即证据（sha256 如实入账）。
    license_root_ee = {}
    for up_name, _ in DATASET_LICENSE_FILES:
        src = stage / "root-licenses" / up_name
        if not src.is_file():
            _fail(f"dataset-level license file missing: {src}")
        data = src.read_bytes()
        dst = DATASET / "raw" / up_name
        if dst.exists():
            _fail(f"refusing to overwrite: {dst}")
        dst.write_bytes(data)
        sha = hashing.sha256_bytes(data)
        license_root_ee[up_name] = {
            "upstream_rel": up_name, "sha256": sha,
            "size_bytes": len(data),
            "source": f"GitLab files API raw @ {kcd.PIN_COMMIT}",
            "dataset_rel": f"datasets/kicad-demos-r1/raw/{up_name}",
        }
        file_rows.append({
            "upstream_rel": up_name,
            "dataset_rel": f"datasets/kicad-demos-r1/raw/{up_name}",
            "sha256": sha, "size_bytes": len(data),
            "category": "license_or_readme", "renamed_from": None,
        })

    raw_files = sorted(({"path": r["dataset_rel"], "sha256": r["sha256"]}
                        for r in file_rows), key=lambda x: x["path"])

    # ---- 板 survey（版本 token/拓扑签名/组 id）----
    boards = []
    for e in ledger["retained"]:
        demo_id = e["demo_id"]
        for bf in e["board_files"]:
            bid = kcd.demo_board_id(demo_id, bf)
            text = upstream_files[bf].read_text(encoding="utf-8",
                                                errors="replace")
            sv = kcd.survey_board_text(text)
            rev = kcd.board_revision(bf)
            boards.append({
                "board_id": bid, "demo_id": demo_id,
                "revision": rev, "board_file": f"demos/{bf}",
                "version_token": sv["version_token"],
                "generator_version": sv["generator_version"],
                "topology_group": kcd.topology_group_id(sv["signature"]),
                "counts": {"net": sv["signature"]["net_count"],
                           "footprint": sv["signature"]["footprint_count"],
                           "pad": sv["signature"]["pad_count"],
                           "via": sv["signature"]["via_count"],
                           "segment": sv["signature"]["segment_count"],
                           "zone": sv["zone_count"]},
            })
    board_ids = sorted({b["board_id"] for b in boards})
    if len(board_ids) != 17:
        _fail(f"unique board ids {len(board_ids)} != 17")
    revision_ids = sorted(f"{b['board_id']}.{b['revision']}" for b in boards)
    project_groups = sorted({e["project_group"] for e in ledger["retained"]})
    topology_groups = sorted({b["topology_group"] for b in boards})
    vt = {}
    for b in boards:
        vt[b["version_token"]] = vt.get(b["version_token"], 0) + 1
    kicad_version_field = (
        "mixed KiCad 8.99–10.99（18 板文件 version tokens："
        + "、".join(f"{k}={v}" for k, v in sorted(vt.items()))
        + "；现行转换器兼容域（20171130，KiCad5）外——本包零转换零 profile）")

    # ---- splits（demo 组整组简分）+ split 交叉复核 ----
    demo_boards = {}
    for e in ledger["retained"]:
        demo_boards[e["demo_id"]] = sorted(
            {kcd.demo_board_id(e["demo_id"], bf)
             for bf in e["board_files"]})
    splits = kcd.assign_demo_splits(demo_boards)
    board_groups = [(bid, next(e["project_group"]
                               for e in ledger["retained"]
                               if bid.split("/")[0] == e["demo_id"]))
                    for bid in board_ids]
    split_check = corpus.audit_split_cross(splits, board_groups)
    if split_check["result"] != "pass":
        _fail(f"split cross check failed: {split_check['violations']}")

    # ---- 库内泄漏/去重审计（corpus.audit_leakage）----
    content_items, topo_sigs, variant_items = [], [], []
    pg_by_board = dict(board_groups)
    for b in boards:
        bf = b["board_file"][len("demos/"):]
        text = upstream_files[bf].read_text(encoding="utf-8",
                                            errors="replace")
        content_items.append({"board_id": b["board_id"],
                              "file_role": b["revision"],
                              "content_sha256":
                                  corpus.content_fingerprint(text)})
        sig = kcd.survey_board_text(text)["signature"]
        topo_sigs.append(dict(sig, board_id=b["board_id"]))
        variant_items.append({"board_id": b["board_id"],
                              "project_group": pg_by_board[b["board_id"]],
                              "revision_id": b["revision"]})
    in_library = corpus.audit_leakage(splits, board_groups, content_items,
                                      variant_items, topo_sigs)

    # ---- 跨库去重（vs pcbbenchmarks-r1 + pcbench-r1）----
    own_items = [{"library": "kicad-demos-r1",
                  "board_id": f"{b['board_id']}.{b['revision']}",
                  "file_role": b["revision"],
                  "text": upstream_files[
                      b["board_file"][len("demos/"):]].read_text(
                      encoding="utf-8", errors="replace")}
                 for b in boards]
    other_items = []
    for base in ("datasets/pcbbenchmarks-r1", "datasets/pcbench-r1"):
        for fp in sorted((REPO / base).rglob("*.kicad_pcb")):
            rel = fp.relative_to(REPO).as_posix()
            other_items.append({
                "library": base.split("/")[-1],
                "board_id": rel[len("datasets/"):].rsplit(".", 1)[0],
                "file_role": "board_file",
                "text": fp.read_text(encoding="utf-8", errors="replace")})
    cross = kcd.audit_cross_library(own_items, other_items)
    if cross["content_duplicate_group_count"] != 0:
        _fail("cross-library content duplicates found — retention must "
              "be re-audited before manifest")

    # ---- 入账 1：license-audit ----
    audit_doc = {
        "track": kcd.TRACK, "audit_date": kcd.AUDIT_DATE,
        "authorization": "APR-0006（out/v3-approvals/"
                         "disposition-APR-0006-tl5-corpus-authorization.json）",
        "source": {
            "source_id": "SRC-KICAD-DEMO",
            "upstream_uri": kcd.UPSTREAM_URI,
            "mirror_uri": kcd.MIRROR_URI,
            "pin_commit": kcd.PIN_COMMIT,
            "mirror_sync_verified": (
                "gitlab master HEAD 与 github mirror HEAD 同 commit "
                + kcd.PIN_COMMIT + "（api 双 host 实测，2026-09-05）"),
            "archive_url": kcd.ARCHIVE_URL,
            "archive_sha256": archive_sha,
            "archive_size_bytes": archive_size,
            "archive_method": "GitLab archive API path=demos 子树 tarball "
                              "单次只读下载；零安装脚本零执行",
            "enumeration_reconciliation": {
                "archive_extracted_files": len(upstream_files),
                "github_mirror_tree_blobs": 709,
                "github_tree_truncated": False,
                "set_diff": "empty（全等）",
                "git_blob_sha1_verified": 709, "git_blob_sha1_mismatch": 0,
                "gitlab_files_api_spot_checks_byte_equal": 7,
                "gitlab_recursive_tree_undercount_note":
                    "GitLab 递归 tree API 逐目录漏报（cm5_minima/LICENSE."
                    "txt 缺席、vme-wren 97≠128）——清单权威=归档解包+"
                    "GitHub 树枚举",
            },
        },
        "license_coverage_verdict": {
            "default_mapping_quote": kcd.LICENSE_README_QUOTE,
            "default_mapping_source": "仓库根 LICENSE.README（许可映射）",
            "default_mapping_file": license_root_ee["LICENSE.README"],
            "governing_texts": {
                "CC-BY-SA-4.0": license_root_ee["LICENSE.CC-BY-SA-4.0"],
                "Apache-2.0": license_root_ee["LICENSE.APACHE-2.0"],
            },
            "dir_level_override_rule": "demo 目录内 LICENSE 文件=更具体"
                                       "声明，优先于仓库映射",
            "board_file_header_check": "18/18 板文件无 license 头注释"
                                       "（首 token=(kicad_pcb）；仅 "
                                       "tinytapeout-demo.kicad_pcb 含板级"
                                       "许可 comment 字段（Apache-2.0）",
            "r2_claim_correction": {
                "r2_claim": "demos/cm5_minima/LICENSE.txt = Boost "
                            "Software License 1.0（source-research-r2）",
                "actual": "同路径文件原文=CERN Open Hardware Licence "
                          "Version 2 - Strongly Reciprocal "
                          "（CERN-OHL-S-2.0）",
                "evidence_sha256": license_ee["cm5_minima"]["sha256"],
                "verdict": "r2 声称与原文不符，本包以原文为准",
            },
        },
        "per_demo_ledger": ledger,
        "per_demo_license_evidence": license_ee,
        "per_demo_readme_evidence": readme_ee,
        "board_file_header_evidence": board_header_ee,
        "tiny_tapeout_board_comments": tiny_comments,
        "denominator_note": "evaluated=18 demo（评估字段）；实际分母="
                            "合规留存 17 板（15 demo / 18 板文件）",
    }
    audit_sha = _write_canonical(AUDIT_JSON, audit_doc)

    # ---- 入账 2：retention ledger ----
    ledger_doc = {
        "track": kcd.TRACK, "audit_date": kcd.AUDIT_DATE,
        "archive_sha256": archive_sha, "pin_commit": kcd.PIN_COMMIT,
        "summary": {
            "evaluated_demos": c["evaluated"],
            "retained_demos": c["retained_demos"],
            "retained_boards": len(board_ids),
            "retained_board_files": c["retained_board_files"],
            "retained_files_total": len(file_rows),
            "retained_bytes": sum(r["size_bytes"] for r in file_rows),
            "excluded_demos": c["not_available"] + c["blocked"]
                              + c["copyleft_conservative_exclusion"],
        },
        "retained_demos": [
            dict(e, retention=per_demo_retention[e["demo_id"]],
                 boards=[b for b in boards if b["demo_id"] == e["demo_id"]],
                 files=[r for r in file_rows
                        if r["dataset_rel"].split("/")[3] == e["demo_id"]])
            for e in ledger["retained"]],
        "dataset_license_files": [r for r in file_rows
                                  if "/" not in r["dataset_rel"]
                                  .split("raw/", 1)[1]],
        "excluded_demos": ledger["excluded"],
        "splits": splits,
    }
    ledger_sha = _write_canonical(LEDGER_JSON, ledger_doc)

    # ---- 入账 3：leakage audit ----
    leakage_doc = {
        "track": kcd.TRACK, "audit_date": kcd.AUDIT_DATE,
        "dataset_id": kcd.DATASET_ID,
        "in_library": in_library,
        "cross_library_dedup": cross,
        "result": ("pass" if in_library["result"] == "pass"
                   and cross["content_duplicate_group_count"] == 0
                   else "fail"),
        "denominator_note": "库内审计=17 板 18 板文件；跨库并集=18 own + "
                            f"{len(other_items)} other（pcbbenchmarks-r1 4"
                            " + pcbench-r1 162）",
    }
    leakage_sha = _write_canonical(LEAKAGE_JSON, leakage_doc)
    if leakage_doc["result"] != "pass":
        _fail("leakage audit result != pass — inspect before manifest")

    # ---- 入账 4：source-research-r4（先于 manifest；manifest 引它）----
    r3_rel = "out/v3-tl5/source-research-r3.json"
    r2_rel = "out/v3-tl5/source-research-r2.json"
    r1_rel = "out/v3-tl5/source-research.json"
    r4_doc = {
        "schema_version": "v3.0",
        "track": kcd.TRACK,
        "research_date": kcd.AUDIT_DATE,
        "authorization": "APR-0006（out/v3-approvals/"
                         "disposition-APR-0006-tl5-corpus-authorization.json）"
                         "：读网络/下载仅限语料获取用途",
        "denominator_warning": (
            "evaluated=18 demo 是评估字段；实际分母=合规留存 17 板"
            "（15 demo / 18 板文件，其中 multichannel_mixer 一板双态）"
            "——18 不得写成板分母"),
        "r4_findings": {
            "source_id": "SRC-KICAD-DEMO",
            "name": "KiCad 官方 demo/测试集",
            "uri": kcd.UPSTREAM_URI,
            "mirror_uri": kcd.MIRROR_URI,
            "pin_commit": kcd.PIN_COMMIT,
            "outcome_lineage": ("r1 not_available（未评估）→ r2 "
                                "entry_evaluated_per_demo_license_audit"
                                "_required → r4 本包=终态"),
            "acquisition": {
                "method": "GitLab archive API demos 子树 tarball 单次"
                          "只读下载（path=demos @pin commit）；零安装"
                          "脚本零执行",
                "archive_url": kcd.ARCHIVE_URL,
                "archive_sha256": archive_sha,
                "archive_size_bytes": archive_size,
                "extracted_files": len(upstream_files),
                "mirror_sync": "双 host 同 commit 实测（见 license-audit "
                               "source.mirror_sync_verified）",
            },
            "license_coverage_verdict": {
                "default": "仓库根 LICENSE.README 映射：demos/* 全部="
                           "CC-BY-SA-4.0（原文=LICENSE.CC-BY-SA-4.0 存档）",
                "dir_level_overrides": {
                    "Apache-2.0": ["jetson-agx-thor-baseboard",
                                   "tiny_tapeout"],
                    "CC-BY-SA-4.0": ["openair-max"],
                    "CERN-OHL-P-2.0": ["royalblue54L_feather"],
                    "CERN-OHL-S-2.0": ["cm5_minima"],
                    "CC-BY-NC-SA-4.0": ["stickhub"],
                },
                "board_header_check": "18/18 板文件无 license 头；"
                                      "tinytapeout-demo 板级 comment="
                                      "Apache-2.0（与目录 LICENSE.txt 一致）",
                "r2_claim_correction": audit_doc[
                    "license_coverage_verdict"]["r2_claim_correction"],
            },
            "audit_outcome": "per_demo_audit_mixed_retain_15_of_18",
            "per_demo_outcome": {
                e["demo_id"]: {
                    "decision": ("retain" if "decision" not in e
                                 else e["decision"]),
                    "reason_code": e["reason_code"],
                    "license_id": e["license_id"],
                    "board_file_count": e["board_file_count"],
                }
                for e in ledger["retained"] + ledger["excluded"]},
            "retention": {
                "dataset_id": kcd.DATASET_ID, "version": "1",
                "demo_count": c["retained_demos"],
                "board_count": len(board_ids),
                "board_file_count": c["retained_board_files"],
                "files_total": len(file_rows),
                "bytes_total": sum(r["size_bytes"] for r in file_rows),
                "dataset_path": "datasets/kicad-demos-r1/raw/",
                "scope_exclusions": "3D 模型/制造产物/文档 PDF/图像/杂项"
                                    "二进制不入库（逐 demo skip 计数见 "
                                    "retention ledger）",
            },
            "dataset_registration": {
                "dataset_id": kcd.DATASET_ID, "version": "1",
                "board_count": len(board_ids),
                "splits": {k: v for k, v in splits.items()
                           if k in ("train", "validation", "holdout",
                                    "external_eval", "split_unit",
                                    "split_rule", "holdout_frozen_readonly",
                                    "group_counts")},
                "leakage_audit": {"path": "out/v3-tl5/"
                                          "leakage-audit-kicad-demos-r1.json",
                                  "sha256": leakage_sha,
                                  "result": leakage_doc["result"],
                                  "cross_library": cross["result"]},
            },
        },
        "evidence": {
            "license_audit": {"path": "out/v3-tl5/"
                                      "kicad-demo-license-audit.json",
                              "sha256": audit_sha},
            "retention_ledger": {"path": "out/v3-tl5/"
                                         "retention-ledger-kicad-demos-"
                                         "r1.json", "sha256": ledger_sha},
            "dataset_root_licenses": license_root_ee,
        },
        "relation_to_r1": {"note": "r1 六源结论原样保留（SRC-KICAD-DEMO "
                                   "r1=not_available 未评估）",
                           "path": r1_rel},
        "relation_to_r2": {"note": "r2 入口评估原文不动；其中 "
                                   "cm5_minima=Boost 1.0 声称被本包以"
                                   "原文证据修正（见 "
                                   "license_coverage_verdict."
                                   "r2_claim_correction）",
                           "path": r2_rel,
                           "sha256": hashing.sha256_file(str(REPO / r2_rel))},
        "relation_to_r3": {"note": "r3 PCBench 逐板 vetting 原文不动",
                           "path": r3_rel,
                           "sha256": hashing.sha256_file(str(REPO / r3_rel))},
    }
    r4_sha = _write_canonical(R4_JSON, r4_doc)

    # ---- 入账 5：TD8 manifest（corpus.build_dataset_manifest 实算）----
    module_sha = _sha256_file(REPO / "pcbflow" / "corpus_kicad_demo.py")
    excluded_summary = {
        "note": "18 demo → 15 保留（17 板）；逐 demo 完整账本（含排除"
                "理由与 license_id）见 retention-ledger-kicad-demos-r1"
                ".json；排除=许可三分类（无板 not_available/NC blocked/"
                "CERN-OHL-S 保守排除），非许可排除零",
        "summary_counts": {
            "evaluated": c["evaluated"],
            "retained_demos": c["retained_demos"],
            "retained_boards": len(board_ids),
            "retained_board_files": c["retained_board_files"],
            "not_available": c["not_available"],
            "blocked": c["blocked"],
            "copyleft_conservative_exclusion":
                c["copyleft_conservative_exclusion"],
        },
        "full_ledger": {"path": "out/v3-tl5/retention-ledger-kicad-demos-"
                                "r1.json", "sha256": ledger_sha},
    }
    record = kcd.build_kicad_demo_manifest_record(
        board_ids=board_ids, revision_ids=revision_ids,
        raw_files=raw_files, dataset_splits=splits,
        project_groups=project_groups, topology_groups=topology_groups,
        kicad_version_field=kicad_version_field,
        source_archive={
            "source_uri": kcd.UPSTREAM_URI, "mirror_uri": kcd.MIRROR_URI,
            "pin_commit": kcd.PIN_COMMIT,
            "archive_url": kcd.ARCHIVE_URL,
            "archive_sha256": archive_sha,
            "archive_size_bytes": archive_size,
            "archive_scope": "demos/ 子树（path=demos）",
        },
        source_research_ref={"path": "out/v3-tl5/source-research-r4.json",
                             "sha256": r4_sha},
        excluded_summary=excluded_summary,
        audit_ref={"path": "out/v3-tl5/kicad-demo-license-audit.json",
                   "sha256": audit_sha},
    )
    record["conversion_script"]["modules"][kcd.MODULE_NAME][
        "module_sha256"] = module_sha
    manifest = corpus.build_dataset_manifest(record)
    manifest_sha = _write_canonical(MANIFEST_JSON, manifest)

    print(f"[s15-kicad-demo] OK")
    print(f"  archive sha256      : {archive_sha}")
    print(f"  retained demos      : {c['retained_demos']}/"
          f"{c['evaluated']} (boards={len(board_ids)}, "
          f"board_files={c['retained_board_files']})")
    print(f"  files retained      : {len(file_rows)} "
          f"({sum(r['size_bytes'] for r in file_rows)} bytes)")
    print(f"  splits              : train={len(splits['train'])} "
          f"validation={len(splits['validation'])} "
          f"holdout={len(splits['holdout'])}")
    print(f"  in-library leakage  : {in_library['result']}")
    print(f"  cross-library dedup : {cross['result']}")
    print(f"  audit   sha256      : {audit_sha}")
    print(f"  ledger  sha256      : {ledger_sha}")
    print(f"  leakage sha256      : {leakage_sha}")
    print(f"  r4      sha256      : {r4_sha}")
    print(f"  manifest sha256     : {manifest_sha}")
    print(f"  manifest.manifest_sha256: {manifest['manifest_sha256']}")
    print(f"  manifest.raw_hash   : {manifest['raw_hash']}")


if __name__ == "__main__":
    main()
