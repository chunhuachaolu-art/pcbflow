"""TL-5 语料合同（TD8）：source 调研、dataset manifest、泄漏/去重审计。

SPEC-v3.0-PROPOSAL §2 TD8：PCBWorld、OmniEDA、PCB-Bench 是候选来源，
不是已接入语料；网页/论文声称的 679、1,681、170+ 不能直接写成当前可用
分母。本模块只做三件事：

1. SOURCE_RESEARCH——2026-09-03 S5 会话的源调研记录（数据即账：URI/
   形态/规模声称/license+scope/获取方式/哈希可得性/可达性实测/结论）。
   结论枚举：get（已合规获取）|not_available|blocked；
2. dataset manifest 构建（build_dataset_manifest）——TD8 逐字段合同，
   schema 没有的字段如实 "not_available"，不编造；manifest_sha256=
   canonical JSON 的 sha256（排除自身，自引循环禁）；
3. 泄漏/去重审计（audit_leakage）——纯函数：内容去重（空白归一指纹）、
   拓扑去重（net/footprint/pad/via/track 计数+net 名多重集签名）、
   同源变体检测（同 project_group 不同 board）、split 交叉检查
   （板恰好属于一个角色；holdout 冻结只读；同源组不跨 train/holdout）。

生成器纪律：纯函数、零子进程、零自身落盘、零网络、零 wall-clock
（COLLECTION_DATE 为声明常量）、零主机路径（记录一律仓库相对 POSIX
路径；datasets/ 内外部文件由编排侧读盘传入 hash）。审计 fail-closed：
输入缺字段/含主机路径即 ValueError，不猜。
"""

from __future__ import annotations

import hashlib
import json
import re

from . import hashing

SCHEMA_VERSION = "v3.0"
TRACK = "tl5-corpus-r1"

#: 调研/采集声明日期（人工会话声明，非机器 wall-clock）
COLLECTION_DATE = "2026-09-03"

#: TL-5 出口门状态（本包只做语料研究与获取；两非 Rev-C profile 主路径
#: 未跑——诚实 partial，禁止宣称 TL-5 门通过或泛化能力）
TL5_GATE_STATUS = "partial"
TL5_GATE_BLOCKERS = (
    "两个非 Rev-C profile 主路径（Manifest→compile→enum→audit→"
    "feedforward→route/check）未执行",
    "获取语料仅 2 板（bm1/bm11），分母远小于任何可用训练/回测规模",
    "DRC_baseline/conversion/normalized_hash 未产生（下一包）",
)

# ---------------------------------------------------------------------------
# 1. source 调研记录（S5 会话实测；规模声称≠可用分母）
# ---------------------------------------------------------------------------

SOURCE_RESEARCH = (
    {
        "source_id": "SRC-PCBBENCHMARKS",
        "name": "PCBBenchmarks (ASP-DAC submission, unblinded-adjacent)",
        "uri": "https://github.com/aspdac-submission-pcb-layout/PCBBenchmarks",
        "content_form": "KiCad .kicad_pcb（unrouted+routed）+ Specctra .dsn；"
                        "11 个 benchmark 板（bm1–bm11）",
        "claimed_scale": "11 boards（仓库树实测；README 无规模声明）",
        "license": "板级逐板：bm1=CC-BY-SA（Arduino，license.txt 在库内）；"
                   "bm11=CC-BY-SA（Adafruit，license.txt 在库内）；"
                   "bm2–bm10 无 license 文件（README 自述：盲审剥离，"
                   "unblinded 仓库才有全量引用）",
        "license_scope": {
            "bm1": {"redistribution_allowed": True,
                    "derivative_allowed": True, "attribution": True,
                    "share_alike": True,
                    "note": "CC-BY-SA：再分发/派生须署名+同许可传递"},
            "bm11": {"redistribution_allowed": True,
                     "derivative_allowed": True, "attribution": True,
                     "share_alike": True,
                     "note": "CC-BY-SA（Adafruit 红线：再分发须含原文声明）"},
            "bm2_bm10": {"license": "unknown", "usable": False,
                         "reason": "盲审剥离 license 文本，库内无据可审"},
        },
        "acquisition": "codeload tarball（refs/heads/master）",
        "hash_availability": "GitHub 无发布哈希；归档/逐文件 sha256 本地实算",
        "reachability": "ok（api.github.com/codeload 实测可达）",
        "outcome": "get",
        "outcome_detail": "仅获取 bm1+bm11（许可明确子集）；bm2–bm10 "
                          "license_unknown→not_available（不留存）",
    },
    {
        "source_id": "SRC-DAC2020-PCB-BENCHMARKS",
        "name": "PCB-Benchmarks (DAC 2020 Submission 1703)",
        "uri": "https://github.com/DAC-2020-Submission-1703/PCB-Benchmarks",
        "content_form": "仅 routed .kicad_pcb（bm1–bm11，无 dsn/unrouted）",
        "claimed_scale": "11 boards（仓库树实测）",
        "license": "仓库无任何 LICENSE/license.txt（git tree 实测）",
        "license_scope": "not_available",
        "acquisition": "git/tarball 可达",
        "hash_availability": "同上，本地实算",
        "reachability": "ok",
        "outcome": "not_available",
        "outcome_detail": "license 不明=不留存（红线：不先用后审）；"
                          "aspdac 仓库 README 所指 unblinded 库即此库，"
                          "但仍缺逐板 license 文本",
    },
    {
        "source_id": "SRC-PCBWORLD",
        "name": "PCBWorld / PCBWorld-Bench (LG AI Research)",
        "uri": "https://arxiv.org/abs/2607.05915",
        "content_form": "KiCad .kicad_pcb 路由环境+三个板集（两个合成生成器"
                        "+声称 679 真实开源板）",
        "claimed_scale": "论文声称 679 real boards（不可当当前可用分母）",
        "license": "论文 arXiv 存档=CC0（论文文本）；代码/数据仓库 license "
                   "未定位（论文 HTML 内未见自属 repo URL）",
        "license_scope": "not_available",
        "acquisition": "代码仓库 URL 未定位（arXiv HTML 全文 grep 实测）",
        "hash_availability": "not_available",
        "reachability": "arxiv.org ok；自属 repo 不可达/未定位",
        "outcome": "blocked",
        "outcome_detail": "代码/数据入口未定位+许可不明：not_available；"
                          "679 声称不写入任何分母字段",
    },
    {
        "source_id": "SRC-OMNIEDA",
        "name": "OmniEDA / OmniLayout (EMNLP 2026)",
        "uri": "https://www.omnieda.com/",
        "content_form": "schematic-coupled PCB layout 多模态基准（声称 "
                        "1,681 工业级布局；QA/推理任务形态）",
        "claimed_scale": "论文 v2 声称 1,681 layouts / 77.24K 放置实例"
                         "（不可当当前可用分母）",
        "license": "论文 v2 文本声称 CC-BY-4.0；项目页无 license 文本，"
                   "分发=Google Drive 两个文件（Sample Data/Visualize Code），"
                   "分发点未随附许可原文",
        "license_scope": "claimed_cc_by_4.0_unverified_at_distribution",
        "acquisition": "Google Drive（curl 直取不可靠，需交互确认页）",
        "hash_availability": "not_available（无发布哈希）",
        "reachability": "omnieda.com ok；drive.google.com 未尝试交互下载",
        "outcome": "blocked",
        "outcome_detail": "许可声称与分发物未绑定（分发点无许可文本随附）；"
                          "本包不下载（许可不明=不留存；时间预算不允许"
                          "完成下载+许可核验双闭环）",
    },
    {
        "source_id": "SRC-PCB-BENCH-DIGILAB",
        "name": "PCB-Bench (ICLR 2026, digailab)",
        "uri": "https://github.com/digailab/PCB-Bench",
        "content_form": "LLM/MLLM PCB 放置+布线推理 QA 任务集（3 任务目录；"
                        "非原生 .kicad_pcb 板库）",
        "claimed_scale": "仓库 ~106MB（GitHub API size=106009KB）；"
                         "论文侧声称 170+ 板（不可当当前可用分母）",
        "license": "GitHub API license=null；仓库根实测无 LICENSE 文件"
                   "（README/index.html/任务目录/figs）",
        "license_scope": "not_available",
        "acquisition": "git/zip 可达",
        "hash_availability": "not_available",
        "reachability": "ok",
        "outcome": "not_available",
        "outcome_detail": "仓库无 license 文件=许可不明，不留存；"
                          "形态为 QA 评测而非板级原始文件，与 TL-5 "
                          "profile 转换需求不直接匹配",
    },
    {
        "source_id": "SRC-KICAD-DEMO",
        "name": "KiCad 官方 demo/测试集（候选）",
        "uri": "not_available",
        "content_form": "not_available",
        "claimed_scale": "not_available",
        "license": "not_available",
        "license_scope": "not_available",
        "acquisition": "not_available",
        "hash_availability": "not_available",
        "reachability": "not_evaluated（本会话时间预算未覆盖 GitLab 官方"
                        "demo 仓库逐项核验）",
        "outcome": "not_available",
        "outcome_detail": "下一包候选：官方 demo 若逐板 license 明确"
                          "（CC-BY-SA 等）可扩充分母；未核验前不声称",
    },
)

# ---------------------------------------------------------------------------
# 2. dataset manifest（TD8 逐字段；缺=not_available）
# ---------------------------------------------------------------------------

#: TD8 必填字段序（canonical 输出顺序=字段声明序，保证 byte-exact）
TD8_FIELDS = (
    "dataset_id", "version", "manifest_sha256",
    "source_uri_or_archive_sha256", "license", "license_scope",
    "redistribution_allowed", "derivative_allowed", "attribution",
    "collection_date", "board_ids", "revision_ids", "project_groups",
    "topology_groups", "vendor_groups", "consent_or_provenance",
    "conversion_script", "kicad_version", "raw_hash", "normalized_hash",
    "conversion_log", "field_missingness", "DRC_baseline",
    "dataset_splits", "excluded_boards", "source_research_ref",
)

NA = "not_available"


def _require_relative(path: str, what: str) -> str:
    """仓库相对 POSIX 路径强制（禁主机路径，红线 5）。"""
    if not isinstance(path, str) or "\\" in path or re.match(
            r"^[A-Za-z]:", path) or path.startswith("/"):
        raise ValueError(f"{what}: host/absolute path forbidden: {path!r}")
    return path


def aggregate_raw_hash(files: list) -> str:
    """raw_hash=sorted(repo-relative path, sha256) 的 canonical JSON sha256。

    files: [{"path": repo-relative-posix, "sha256": 64hex}, ...]；
    路径有主机形态/重复/缺 sha256 即 ValueError（fail-closed）。
    """
    seen = set()
    norm = []
    for f in sorted(files, key=lambda x: x["path"]):
        p = _require_relative(f["path"], "raw file path")
        if p in seen:
            raise ValueError(f"duplicate path: {p}")
        seen.add(p)
        if not re.fullmatch(r"[0-9a-f]{64}", f.get("sha256", "")):
            raise ValueError(f"bad sha256 for {p}")
        norm.append({"path": p, "sha256": f["sha256"]})
    return hashing.sha256_bytes(hashing.canonical_json_bytes(norm))


def build_dataset_manifest(record: dict) -> dict:
    """按 TD8 字段序构建 manifest；manifest_sha256 自引豁免后实算。

    record 至少含 dataset_id/version/license/board_ids/dataset_splits/
    raw_files（供 raw_hash）。TD8 中本包无据的字段必须显式传 NA
    （调用方如实声明），不得静默填充。
    """
    for key in ("dataset_id", "version", "license", "board_ids",
                "dataset_splits", "raw_files", "license_scope",
                "consent_or_provenance"):
        if key not in record:
            raise ValueError(f"missing required key: {key}")
    if record["dataset_id"] != record["dataset_id"].lower():
        raise ValueError("dataset_id must be lowercase")
    raw_hash = aggregate_raw_hash(record["raw_files"])
    m = {k: record.get(k, NA) for k in TD8_FIELDS}
    m["manifest_sha256"] = NA  # 占位：排除自身后实算
    m["raw_hash"] = raw_hash
    body = {k: v for k, v in m.items() if k != "manifest_sha256"}
    m["manifest_sha256"] = hashing.sha256_bytes(
        hashing.canonical_json_bytes(body))
    return m


# ---------------------------------------------------------------------------
# 3. 泄漏/去重审计（纯函数）
# ---------------------------------------------------------------------------

_WS = re.compile(r"\s+")


def content_fingerprint(text: str) -> str:
    """内容去重指纹：剔除全部空白后 sha256（s-expr 空白无语义，
    消除缩进/换行/尾随空白差异；仅用于等价检测，不用于正确性）。"""
    return hashlib.sha256(
        _WS.sub("", text).encode("utf-8")).hexdigest()


def topology_signature(kicad_pcb_text: str) -> dict:
    """拓扑签名：net/footprint/pad/via/track 计数 + net 名多重集 hash。

    s-expr 一阶计数（不解析语义；用于同拓扑检测，不用于布线正确性）。
    KiCad 5.x 板文件用 `(module`、KiCad 6+ 用 `(footprint`——同名实体
    取并集计数（格式版本容忍）。
    """
    def count(tok: str) -> int:
        return len(re.findall(r"\(" + tok + r"\s", kicad_pcb_text))
    footprint_count = count("module") + count("footprint")
    nets = re.findall(r'\(net\s+\d+\s+(?:"([^"]*)"|([^\s)]+))\)',
                      kicad_pcb_text)
    net_names = sorted(next(g for g in n if g) for n in nets
                       if any(g for g in n))
    return {
        "net_count": count("net"),
        "footprint_count": footprint_count,
        "pad_count": count("pad"),
        "via_count": count("via"),
        "segment_count": count("segment"),
        "named_net_count": len(net_names),
        "net_name_multiset_sha256": hashing.sha256_text("\n".join(net_names)),
    }


def audit_content_dedup(items: list) -> dict:
    """内容去重：items=[{board_id, file_role, content_sha256}] →
    duplicate_groups（同 content_sha256 的跨板组；同板不同文件角色
    相同=变体线索不豁免，如实列出）。"""
    by_hash = {}
    for it in items:
        by_hash.setdefault(it["content_sha256"], []).append(
            {"board_id": it["board_id"], "file_role": it["file_role"]})
    dupes = [{"content_sha256": h, "members": sorted(
        v, key=lambda x: (x["board_id"], x["file_role"]))}
        for h, v in sorted(by_hash.items()) if len(v) > 1]
    return {"duplicate_groups": dupes,
            "duplicate_group_count": len(dupes)}


def audit_same_source_variants(items: list) -> dict:
    """同源变体：同 project_group 出现多个 board_id（潜在同板变体/
    改版泄漏源）；同板多 revision（file_role 变体）单列。"""
    groups = {}
    for it in items:
        groups.setdefault(it["project_group"], set()).add(it["board_id"])
    cross_board = {g: sorted(b) for g, b in sorted(groups.items())
                   if len(b) > 1}
    by_board = {}
    for it in items:
        by_board.setdefault(
            (it["project_group"], it["board_id"]), set()).add(
                it.get("revision_id", NA))
    multi_rev = {f"{g}/{b}": sorted(r) for (g, b), r in sorted(
        by_board.items()) if len(r) > 1}
    return {"same_group_cross_board": cross_board,
            "same_board_multi_revision": multi_rev,
            "variant_flag_count": len(cross_board) + len(multi_rev)}


def audit_split_cross(dataset_splits: dict, board_groups: list) -> dict:
    """split 交叉检查：每板恰好一角色；角色合法；同 project_group
    不得跨 train/validation 与 holdout/external_eval（防同源泄漏）；
    holdout/external_eval 必须声明 frozen_readonly=true。"""
    valid_roles = ("train", "validation", "holdout", "external_eval")
    violations = []
    assign = {}
    for role in valid_roles:
        for b in dataset_splits.get(role, []):
            if b in assign:
                violations.append({"kind": "board_in_multiple_roles",
                                   "board_id": b, "roles": sorted(
                                       [assign[b], role])})
            assign[b] = role
    gmap = {b: g for b, g in board_groups}
    hold_side = ("holdout", "external_eval")
    train_side = ("train", "validation")
    seen_group = {}
    for b, role in sorted(assign.items()):
        if b not in gmap:
            violations.append({"kind": "board_without_group", "board_id": b})
            continue
        g = gmap[b]
        side = hold_side if role in hold_side else train_side
        if g in seen_group and seen_group[g] != side:
            violations.append({"kind": "group_crosses_holdout_boundary",
                               "project_group": g})
        seen_group[g] = side
    for b, _ in board_groups:
        if b not in assign:
            violations.append({"kind": "board_unassigned", "board_id": b})
    frozen = {}
    for role in hold_side:
        if dataset_splits.get(role):
            frozen[role] = bool(dataset_splits.get(role + "_frozen_readonly",
                                                   False))
            if not frozen[role]:
                violations.append({"kind": "holdout_not_frozen", "role": role})
    return {"assignment_count": len(assign), "violations": violations,
            "violation_count": len(violations), "frozen_flags": frozen,
            "result": "fail" if violations else "pass"}


def audit_topology_dedup(signatures: list) -> dict:
    """拓扑去重：signatures=[{board_id, **topology_signature}] →
    同 net_name_multiset_sha256 且同 net/footprint/pad 计数的板组。"""
    key = lambda s: (s["net_count"], s["footprint_count"], s["pad_count"],
                     s.get("net_name_multiset_sha256", ""))
    by_key = {}
    for s in signatures:
        by_key.setdefault(key(s), []).append(s["board_id"])
    dupes = [{"signature": {"net_count": k[0], "footprint_count": k[1],
                            "pad_count": k[2],
                            "net_name_multiset_sha256": k[3]},
              "board_ids": sorted(v)} for k, v in sorted(by_key.items(),
                                                         key=lambda x: str(
                                                             x[0]))
             if len(v) > 1]
    return {"topology_duplicate_groups": dupes,
            "topology_duplicate_group_count": len(dupes)}


def audit_leakage(dataset_splits: dict, board_groups: list, content_items: list,
                  variant_items: list, topology_signatures: list) -> dict:
    """泄漏/去重审计总装：split 交叉 + 内容去重 + 同源变体 + 拓扑去重。

    result=pass 仅当 split_cross pass 且三个去重组均无跨板重复
    （同板多 revision 变体不算泄漏，但如实入账）。
    """
    split = audit_split_cross(dataset_splits, board_groups)
    content = audit_content_dedup(content_items)
    variants = audit_same_source_variants(variant_items)
    topo = audit_topology_dedup(topology_signatures)
    leak_like = (content["duplicate_group_count"]
                 + topo["topology_duplicate_group_count"])
    return {
        "track": TRACK, "audit_date": COLLECTION_DATE,
        "split_cross": split, "content_dedup": content,
        "same_source_variants": variants, "topology_dedup": topo,
        "result": "pass" if split["result"] == "pass" and leak_like == 0
        else "fail",
    }


def dumps_canonical(obj) -> str:
    """编排侧统一出口：canonical JSON 文本（零落盘由调用方保证）。"""
    return hashing.json_dumps(obj)
