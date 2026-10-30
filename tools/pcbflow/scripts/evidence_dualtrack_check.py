# -*- coding: utf-8 -*-
"""外部证据双轨 manifest 对账脚本（EVIDENCE-R1 脚手架；提案 r1 §6.2/§6.4 双轨对账门）。

依据：tools/pcbflow/exec/EXTERNAL-EVIDENCE-INTERFACE-PROPOSAL-2026-09.md（r1 adopted，§1+§6）
＋ exec/EVIDENCE-R1-SCAFFOLD-DISPATCH-2026-09-24.md 工作项 3
＋ exec/USER-RULINGS-2026-09-24.md R-6（双轨）/R-7（DFM 并入 stackup 类）。

双轨口径：
- 原始件轨 out/revc-evidence-r1/（不入 git）+ 摘录件轨 tools/pcbflow/evidence/revc-r1/（入 git）；
- manifest 双写同构；任一轨哈希不符 => 该条目 not_available。

校验项（任何 FAIL => 退出码 1；fail-closed）：
  E1  两 manifest 存在且 JSON 可解析；
  E2  六类别齐全无重复（stackup/si/pi/thermal/emc/power；stackup=板厂叠层+DFM 并类，R-7），
      各类 excerpt_file 合提案 §2 表；
  E3  双轨逐类登记一致（excerpt_file/status/reason/excerpt_mirror_path_repo）；
  E4  模板态（status=not_available）：reason 非空、excerpt_sha256/derived_from 为 null、
      git 镜像中不得存在该摘录件（占位文件冒充=失败）；originals.path 非 null 时须在盘且
      sha256 与登记一致（登记必须真实）；
  E5  接入态（status=available）：摘录件在 git 镜像在盘且 sha256==excerpt_sha256；
      derived_from 非 null；其引用原始件在盘且 sha256 匹配。

非目标：不复核外部结论（pass/fail 判定原文照登，提案 §2 尾注）；不翻任何 gate/section 状态；
不写任何文件（对两轨只读）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]  # tools/pcbflow

# 提案 §2 表（R-7 后 stackup 含 DFM）的机器可读固化：类别 -> 摘录件名。
EXPECTED_CATEGORIES = {
    "stackup": "stackup/fabricator-stackup.json",
    "si": "si/si-report.json",
    "pi": "pi/pi-report.json",
    "thermal": "thermal/thermal-report.json",
    "emc": "emc/emc-report.json",
    "power": "power/measured-power.json",
}
VALID_STATUS = ("not_available", "available")
TRACK = "revc"
REV = "r1"

failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)
    print(f"  [FAIL] {msg}")


def ok(msg: str) -> None:
    print(f"  [PASS] {msg}")


def sha256_file(path: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def load_manifest(path: Path) -> dict | None:
    if not path.is_file():
        fail(f"E1 manifest 缺件: {path}")
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"E1 manifest 解析失败: {path} ({exc})")
        return None
    if not isinstance(data, dict) or not isinstance(data.get("categories"), list):
        fail(f"E1 manifest 结构不符（缺 categories 列表）: {path}")
        return None
    return data


def check_categories(out_m: dict, git_m: dict, git_root: Path) -> None:
    cats_out = out_m["categories"]
    names_out = [c.get("category") for c in cats_out if isinstance(c, dict)]
    # E2：类别集合
    if len(names_out) != len(cats_out):
        fail("E2 存在缺 category 键的条目")
    dup = {n for n in names_out if names_out.count(n) > 1}
    if dup:
        fail(f"E2 类别重复: {sorted(dup)}")
    if set(names_out) != set(EXPECTED_CATEGORIES):
        fail(f"E2 类别集合不符: 期望 {sorted(EXPECTED_CATEGORIES)} 实得 {sorted(set(names_out))}")
    else:
        ok(f"E2 六类别齐全: {sorted(EXPECTED_CATEGORIES)}")
    # E2：excerpt_file 合表
    for c in cats_out:
        if not isinstance(c, dict):
            continue
        name, xf = c.get("category"), c.get("excerpt_file")
        want = EXPECTED_CATEGORIES.get(name)
        if want and xf != want:
            fail(f"E2 {name} excerpt_file 不符: 期望 {want} 实得 {xf}")
    if not failures:
        ok("E2 各类 excerpt_file 合提案 §2 表")
    # E3：双轨逐类一致
    git_by_name = {c.get("category"): c for c in git_m["categories"] if isinstance(c, dict)}
    consistent = True
    for c in cats_out:
        if not isinstance(c, dict) or c.get("category") not in git_by_name:
            continue
        g = git_by_name[c["category"]]
        for key in ("excerpt_file", "status", "reason", "excerpt_mirror_path_repo"):
            if c.get(key) != g.get(key):
                consistent = False
                fail(f"E3 双轨不一致 [{c.get('category')}].{key}: out={c.get(key)!r} git={g.get(key)!r}")
    if consistent:
        ok("E3 双轨 manifest 逐类登记一致（excerpt_file/status/reason/mirror_path）")
    # E4/E5：逐类状态自洽
    for c in cats_out:
        if not isinstance(c, dict):
            continue
        check_one_category(c, git_root)


def check_one_category(cat: dict, git_root: Path) -> None:
    name = cat.get("category") or "<unnamed>"
    status = cat.get("status")
    if status not in VALID_STATUS:
        fail(f"E4/E5 {name} status 非法: {status!r}（合法={VALID_STATUS}）")
        return
    mirror_rel = cat.get("excerpt_mirror_path_repo") or f"tools/pcbflow/evidence/{TRACK}-{REV}/{EXPECTED_CATEGORIES.get(name, '')}"
    # excerpt_mirror_path_repo 为 repo 相对路径，git_root 即仓库根。
    excerpt_path = git_root / mirror_rel
    if status == "not_available":
        if not str(cat.get("reason") or "").strip():
            fail(f"E4 {name} not_available 但 reason 为空（缺件必须带原因，fail-closed）")
        if cat.get("excerpt_sha256") is not None or cat.get("derived_from") is not None:
            fail(f"E4 {name} not_available 但 excerpt_sha256/derived_from 非 null（登记自相矛盾）")
        if excerpt_path.is_file():
            fail(f"E4 {name} not_available 但摘录件已在 git 镜像在盘（占位冒充）: {excerpt_path}")
        # originals 登记（若有 path）必须真实
        for orig in cat.get("originals") or []:
            if not isinstance(orig, dict) or orig.get("path") is None:
                continue
            op = Path(str(orig["path"]))
            if not op.is_file():
                fail(f"E4 {name} 原始件登记在案但缺件: {op}")
            elif orig.get("sha256") and sha256_file(op) != orig["sha256"]:
                fail(f"E4 {name} 原始件 sha256 不符: {op}")
    else:  # available：未来接入态
        if not excerpt_path.is_file():
            fail(f"E5 {name} available 但摘录件缺件: {excerpt_path}")
        else:
            actual = sha256_file(excerpt_path)
            if cat.get("excerpt_sha256") != actual:
                fail(f"E5 {name} 摘录件 sha256 不符: manifest={cat.get('excerpt_sha256')} 实测={actual}")
        df = cat.get("derived_from")
        if not isinstance(df, dict) or not df.get("path") or not df.get("sha256"):
            fail(f"E5 {name} available 但 derived_from 缺 path/sha256（摘录件必须注明派生关系）")
        else:
            dp = Path(str(df["path"]))
            if not dp.is_file():
                fail(f"E5 {name} derived_from 源原始件缺件: {dp}")
            elif sha256_file(dp) != df["sha256"]:
                fail(f"E5 {name} derived_from 源原始件 sha256 不符: {dp}")
        for orig in cat.get("originals") or []:
            if not isinstance(orig, dict) or orig.get("path") is None:
                fail(f"E5 {name} available 但存在未登记 path 的原始件条目")
                continue
            op = Path(str(orig["path"]))
            if not op.is_file():
                fail(f"E5 {name} 原始件缺件: {op}")
            elif not orig.get("sha256") or sha256_file(op) != orig["sha256"]:
                fail(f"E5 {name} 原始件 sha256 不符/未登记: {op}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="evidence_dualtrack_check.py",
        description=(
            "外部证据双轨（out/ 原始件 + git 摘录件）manifest 对账：校验六类别登记一致性与 "
            "摘录件/原始件 sha256 逐条对账。现阶段空骨架=全 not_available 自洽即绿（退出码 0）；"
            "任何登记不符/占位冒充/哈希不符 => 退出码 1（fail-closed）。"
        ),
        epilog=(
            "依据: exec/EXTERNAL-EVIDENCE-INTERFACE-PROPOSAL-2026-09.md (r1 adopted §6.2/§6.4)；"
            "轨道=revc, 证据轮=r1。默认路径锚定脚本所在仓库布局。"
        ),
    )
    ap.add_argument(
        "--out-manifest",
        type=Path,
        default=REPO / "out" / f"{TRACK}-evidence-{REV}" / "manifest.json",
        help="原始件轨 manifest（默认: tools/pcbflow/out/revc-evidence-r1/manifest.json）",
    )
    ap.add_argument(
        "--git-manifest",
        type=Path,
        default=REPO / "evidence" / f"{TRACK}-{REV}" / "manifest.json",
        help="git 摘录件轨 manifest（默认: tools/pcbflow/evidence/revc-r1/manifest.json）",
    )
    ap.add_argument(
        "--repo-root",
        type=Path,
        default=REPO.parent,
        help="仓库根（解析 excerpt_mirror_path_repo 相对路径用；默认: 脚本位置上两级）",
    )
    args = ap.parse_args(argv)

    print(f"== evidence_dualtrack_check: track={TRACK} rev={REV} ==")
    print(f"  out manifest : {args.out_manifest}")
    print(f"  git manifest : {args.git_manifest}")
    print("E1 双 manifest 存在性与可解析性")
    out_m = load_manifest(args.out_manifest)
    git_m = load_manifest(args.git_manifest)
    if out_m is None or git_m is None:
        print(f"\n对账失败：{len(failures)} 项（fail-closed，缺 manifest 无法继续）")
        return 1
    ok("E1 双 manifest 在盘且可解析")

    print("E2/E3/E4/E5 类别/双轨一致性/状态自洽")
    check_categories(out_m, git_m, args.repo_root)

    n_not_avail = sum(
        1 for c in out_m["categories"] if isinstance(c, dict) and c.get("status") == "not_available"
    )
    n_avail = sum(
        1 for c in out_m["categories"] if isinstance(c, dict) and c.get("status") == "available"
    )
    print(f"\n汇总: available={n_avail} not_available={n_not_avail} "
          f"(骨架态期望 0/6) FAIL={len(failures)}")
    if failures:
        print("对账失败（fail-closed）：", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("对账通过：双轨 manifest 一致，骨架自洽（全 not_available，无占位冒充）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
