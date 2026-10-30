"""P4-C 路线图边界修订采纳包测试（P4C-ADOPT-R1）：r6 批准批次
（APR-0017..0020）+ VERIFICATION-ROADMAP.md 追加式修订（C1–C6）+
提案状态翻转 proposal→adopted。

覆盖：
- r6 账本续接正确性：首行=r5 末行逐字拷贝（自带 prev/seq=5，非
  Genesis——ledger.verify_chain 对文件首条强制 Genesis prev=null，
  故全文件验证走 s32.verify_continuation_chain 三重锚：r5 源链可验+
  首行逐字等式+新 entry 逐条 verify_chain 同款检查）；r5 文件零改动
  （448b0c70）；哈希链可验证（prev 锚 r5 末条 59dd4b37、head 以 r5
  head a7a4b7aa 续链、checkpoint last_seq==count-1）；
- 4 份 disposition 存在性+APR 编号+schema 合法（hash 09dd31fd 不变）+
  user_decisions 裁决语义在场+语义边界字段逐条在场（disposition/文档
  域、零门谓词翻动、BL-1+逐阶段显式用户批准、不修改既有 out/ 产物与
  批准记录、supersedes 追加式）；
- VERIFICATION-ROADMAP.md 含 C1–C6 关键修订语句（抽查特征短语+APR
  编号+日期）与原文历史语义标注保留（§2 前置 #2 原文、V2-a 原表、
  APR-0009 批准块原文）；
- 提案文件状态=adopted 且含 APR-0017..0020 引用、执行方式披露段原文
  保留、§6 原表内容保留；
- 受保护三文件+r1–r5 批准工件 sha256 与开工实测逐一比对（零改动）。

生成器模式：纯内存构造+磁盘实读复验、零子进程、零写盘、零网络、无
wall-clock（断言值均来自落盘件/脚本常量）。
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pcbflow import hashing, ledger, schemas  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(REPO, "scripts", f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


s32 = _load_script("s32_p4c_adopt_approvals")

REL_R5_LEDGER = "out/v3-approvals/decision-ledger-r5.jsonl"
REL_R5_BUNDLE = "out/v3-approvals/approvals-bundle-r5.json"
REL_R6_BUNDLE = "out/v3-approvals/approvals-bundle-r6.json"
REL_R6_LEDGER = "out/v3-approvals/decision-ledger-r6.jsonl"
REL_ROADMAP = "VERIFICATION-ROADMAP.md"
REL_PROPOSAL = "V3-ROADMAP-BOUNDARY-PROPOSAL.md"

R5_HEAD = "a7a4b7aa3188f96d8eb2c480cde63ea87bec18f0c121c50f49928c08040f9902"
R5_LAST_ENTRY = "59dd4b3794282b7810d7092f02a0ce0fc645667b666cae38090468b6b92c7422"
R5_LEDGER_SHA = "448b0c705c3b582014901c5c81eb9a0cc6a69e88b9a6c3dfe3d5dacdaaa7e5fc"
R5_BUNDLE_SHA = "382c8f6e151b2a07cd4de5aebc860e61b5d25570f914f3a63fd1ef7845d45707"
R6_DATE = "2026-09-06"
R6_APRS = ["APR-0017", "APR-0018", "APR-0019", "APR-0020"]

# 开工实测入账（收尾零改动断言依据；受保护三文件+r1–r5 批准工件）
UNCHANGED_FILES = {
    "pcbflow/cli.py":
        "3bfc940701d1be82029877583a0a41f49741228f2e89a321b7dafa98d179aae8",  # M1 refresh: accept copper-loop baseline 6ed4f3fd...->0a738047...; value source = measured sha256(pcbflow/cli.py) (2026-09-11)
    "pcbflow/config.py":
        "8ad12b3fab12f19546034b5421aa77053f4115b91b36b87b9dfabc9075fdcf82",  # REPAIR-P4 W-1 (G0): authorized change f515c348->acdfac49, registered at out/repair-p4/anchor-hashes-post-g0.json (2026-09-23); REPAIR-G1+ W-1/W-2 (2026-09-24): authorized change config acdfac49->7b4974d8 / cli 0a738047->3bfc9407, registered at out/repair-g1plus-r1/anchor-hashes-post-g1plus.json; G2G3 refresh (2026-09-25): authorized change config 7b4974d8->cbe90c4d, registered at out/repair-g2g3/anchor-hashes-post-g2g3.json; align-r1 (2026-09-25): authorized change config cbe90c4d->8ad12b3f (O-1/D-3 None-input structured reject), registered at out/align-r1/anchor-hashes-post-align.json
    "toolchain_lock.json":
        "d43dad89c1559ff034abd1ac01b2c95fdd9141faa48b0e7afd896d9301690b3d",
    "out/v3-approvals/approvals-bundle.json":
        "96013156e32ab1227f51917c5d811a0aefafbf90bb281779c6fbb6a65bb8b36d",
    "out/v3-approvals/approvals-bundle-r2.json":
        "6d35b70f64753404df32edeb3b2f697bdf06f916fc36da34a45f3c65a9fcfa2b",
    "out/v3-approvals/approvals-bundle-r3.json":
        "7696c5d88c4086094394e2160aa170805dbe0bf7d2e6c8237bfd47bbd1c49042",
    "out/v3-approvals/approvals-bundle-r4.json":
        "a9e74e8b1efbd72979e9295ae6971ceed43c39803ed126a5c3d10b25c7ad8bb2",
    "out/v3-approvals/approvals-bundle-r5.json":
        "382c8f6e151b2a07cd4de5aebc860e61b5d25570f914f3a63fd1ef7845d45707",
    "out/v3-approvals/decision-ledger.jsonl":
        "12db3b031c8b5f0a71ea9a85ff1ee0e576f7be02f8f0d57695de736085cdd1df",
    "out/v3-approvals/decision-ledger-r2.jsonl":
        "b33964d0de8bb67a3a567a3333640f7b99abf7fae1f1a49efe500a704f7abe48",
    "out/v3-approvals/decision-ledger-r3.jsonl":
        "27a4a3fb9097f63831215ea416738e280aef75b6141867d9f4d070be3bf481ac",
    "out/v3-approvals/decision-ledger-r4.jsonl":
        "c7420b9e98fcacc31ba93130fe27551cfd5fe1fec61be763a42d2094190b712e",
    "out/v3-approvals/decision-ledger-r5.jsonl":
        "448b0c705c3b582014901c5c81eb9a0cc6a69e88b9a6c3dfe3d5dacdaaa7e5fc",
    "out/v3-approvals/disposition-APR-0001-tl0-gate-scope.json":
        "cc76e5451948e9c207c5284f9a439dcf9d4d5cce810b2657835dfcba09a8c840",
    "out/v3-approvals/disposition-APR-0002-tl1-schema-baseline.json":
        "4c122e0ee8dad91e05449611cf76b505ea61f30ab8ac938bb21e18a2f536bb96",
    "out/v3-approvals/disposition-APR-0003-tl3-required-scope.json":
        "5aa7c5876fa8a6a6733f6504e1c7e4f9a26eca66680a379d33ac9978e04f64ba",
    "out/v3-approvals/disposition-APR-0004-tl4-adoption-disposition.json":
        "d983e2f6983d77a7054c6e878f7b17e4b739178d8da192516d1c78dd499a77d7",
    "out/v3-approvals/disposition-APR-0005-critic-duty-level.json":
        "c1ce1b601d125338f64da5bb4ff8b66dd978b91c50a1a2e1d66b2f923e29ee52",
    "out/v3-approvals/disposition-APR-0006-tl5-corpus-authorization.json":
        "c15174fb27574fff1d2e495bc26434c6fd01f72e602d814be1c835e4974c53df",
    "out/v3-approvals/disposition-APR-0007-item-run-r1-disposition.json":
        "2a3b985a300c72fcfd7fea232422f26c272b2b269752a454c1574e7ca74284a3",
    "out/v3-approvals/disposition-APR-0008-calibration-domain-seed.json":
        "3a3c8d58549ba134b84496b06e150dbd87031c33f41b77fccc9c46db80766690",
    "out/v3-approvals/disposition-APR-0009-verification-roadmap-tiers.json":
        "7f6561e45e14b27802236510cb4e7f931a17a1fba271448ce1efe4d9280734ca",
    "out/v3-approvals/disposition-APR-0010-item-run-r2-disposition.json":
        "4eb45dc44bb11bd7696cc51b840bac0f499f160e8a5c449d6ab1c6facba67883",
    "out/v3-approvals/disposition-APR-0011-calibration-threshold-"
    "provisional-adoption.json":
        "47a52b4576f38fcb036286d13381a49d93b91741520a96fdb415acbf81db0d1f",
    "out/v3-approvals/disposition-APR-0012-schema-registration.json":
        "d809def268e3cd70da3b8aed567bfa49bcbc6c991b865868c0341b7bfc5030cd",
    "out/v3-approvals/disposition-APR-0013-capability-enum-finalization.json":
        "05e1406ee6a06929e67dc435aada5853d51d3b528116c3a6792b7fb9a78c71aa",
    "out/v3-approvals/disposition-APR-0014-staging-binding-and-"
    "s21-retroactive-declaration.json":
        "1869dcb9ce532e522b1201b8442bc1846eaccedff513955908808329cad726a0",
    "out/v3-approvals/disposition-APR-0015-role-naming-finalization.json":
        "9528c0573801f5dafbab880b95bcbbc738a6ab836c2ce2f2c0f794bf757312ca",
    "out/v3-approvals/disposition-APR-0016-source-check-scope-nullable.json":
        "353c8509953bdd4eb09fb4174475efb0a43048d6126d38408172e9951a81b0eb",
}


def _repo_rel(rel: str) -> str:
    return os.path.join(REPO, *rel.split("/"))


def _read_bytes(rel: str) -> bytes:
    with open(_repo_rel(rel), "rb") as fh:
        return fh.read()


def _read_text(rel: str) -> str:
    return _read_bytes(rel).decode("utf-8")


def _read_ledger(rel: str) -> list:
    return [json.loads(line) for line in
            _read_text(rel).splitlines()]


def _collect_evidence_hashes() -> dict:
    hashes = {name: hashing.sha256_file(str(_repo_rel(rel)))
              for name, rel in s32.EVIDENCE_FILES_R6}
    hashes["_r5_ledger_file"] = hashing.sha256_file(str(_repo_rel(REL_R5_LEDGER)))
    return hashes


# ---------------------------------------------------------------------------
# ① r6 账本续接正确性（首行=r5 末行逐字、r5 零改动、哈希链可验证）
# ---------------------------------------------------------------------------

def test_r6_ledger_first_line_verbatim_from_r5_and_r5_untouched():
    r5_lines = _read_text(REL_R5_LEDGER).splitlines()
    r6_lines = _read_text(REL_R6_LEDGER).splitlines()
    assert len(r5_lines) == 6 and len(r6_lines) == 5
    # 首行=r5 末行逐字拷贝（字节级；r5 文件本身零改动）
    assert r6_lines[0] == r5_lines[-1]
    assert hashing.sha256_file(str(_repo_rel(REL_R5_LEDGER))) == R5_LEDGER_SHA
    # r5 源文件自链可验（续接行出自已验链）
    r5_entries = _read_ledger(REL_R5_LEDGER)
    assert ledger.verify_chain(r5_entries) == []
    # 续接行自带其 prev/seq（非 Genesis——如实声明的跨文件续链语义）
    anchor = json.loads(r6_lines[0])
    assert anchor["entry_id"] == "APR-E-0016"
    assert anchor["entry_sha256"] == R5_LAST_ENTRY
    assert anchor["ledger_head_sha256"] == R5_HEAD
    assert anchor["entry_seq"] == 5
    # 续接行非 Genesis：prev=a5c9fdcb…（r5 文件内第 6 条），逐字保留
    assert anchor["prev_entry_sha256"] == \
        "a5c9fdcbf72fbdfe933a362d999ec434c86f024c50eef186f96b78ebfacaa25a"


def test_r6_ledger_continuation_chain_verifiable():
    r5_entries = _read_ledger(REL_R5_LEDGER)
    entries = _read_ledger(REL_R6_LEDGER)
    anchor = entries[0]
    # 三重锚之③：新 entry 逐条 verify_chain 同款检查（seq=文件位 1..4）
    assert s32.verify_continuation_chain(entries, anchor) == []
    # prev 锚定 r5 末条 entry_sha256；head 以 r5 head 为 prev_head 续链
    first_new = entries[1]
    assert first_new["prev_entry_sha256"] == R5_LAST_ENTRY
    assert first_new["ledger_head_sha256"] == hashing.sha256_text(
        R5_HEAD + ":" + first_new["entry_sha256"])
    # 逐条链内一致性 + trust 政策（human 处置恒 untrusted）
    assert [e["entry_seq"] for e in entries[1:]] == [1, 2, 3, 4]
    assert [e["disposition_refs"][0] for e in entries[1:]] == R6_APRS
    assert [e["entry_id"] for e in entries[1:]] == \
        ["APR-E-0017", "APR-E-0018", "APR-E-0019", "APR-E-0020"]
    for e in entries[1:]:
        assert e["authority"] == "human" and e["trust_level"] == "untrusted"
        assert e["entry_kind"] == "disposition"
        assert e["snapshot_revision"] == "v3-approvals-r6"
        assert schemas.validate("decision_ledger_entry", e) == []
        assert e["entry_sha256"] == ledger.entry_body_sha256(e)
        assert e["schema_validation"]["schema_sha256"] == \
            schemas.schema_hash("disposition_record")
    assert ledger.verify_supersedes(entries) == []
    # checkpoint 一致（不变量保持：last_seq==count-1 → 4==5-1）
    bundle = json.loads(_read_text(REL_R6_BUNDLE))
    ckpt = bundle["ledger_checkpoint"]
    assert ckpt["checkpoint_id"] == "CKPT-V3-APPROVALS-R6"
    assert ckpt["entry_count"] == 5 and ckpt["entry_seq"] == 4
    assert ledger.verify_against_checkpoint(entries, ckpt) == []


# ---------------------------------------------------------------------------
# ② r6 bundle byte-exact 重跑 + user_decisions
# ---------------------------------------------------------------------------

def test_r6_bundle_byte_exact_rerun():
    bundle1 = s32.build_approvals_bundle_r6(_collect_evidence_hashes())
    bundle2 = s32.build_approvals_bundle_r6(_collect_evidence_hashes())
    assert hashing.canonical_json_bytes(bundle1) == \
        hashing.canonical_json_bytes(bundle2)
    assert _read_bytes(REL_R6_BUNDLE) == hashing.canonical_json_bytes(bundle1)
    assert _read_bytes(REL_R6_LEDGER) == s32._ledger_bytes(
        bundle1["ledger_entries"])
    assert bundle1["approval_count"] == 4
    assert bundle1["revision"] == "v3-approvals-r6"
    assert bundle1["approval_date"] == R6_DATE
    assert bundle1["gate_write_scan"] == {apr: [] for apr in R6_APRS}
    assert bundle1["ledger_verify"] == {"chain_errors": [],
                                       "supersedes_errors": [],
                                       "r5_source_chain_errors": []}
    # user_decisions：四项裁决原文语义+日期常量（非 wall-clock）
    labels = {"APR-0017": "路径A（解环）",
              "APR-0018": "冻结包扩展+V2-c前置增列",
              "APR-0019": "重现性预冻结协议",
              "APR-0020": "文档同步+两类基线具名"}
    assert set(bundle1["user_decisions"]) == set(R6_APRS)
    for apr, ud in bundle1["user_decisions"].items():
        assert ud["decision_label"] == labels[apr]
        assert ud["decided_date"] == R6_DATE
        assert ud["decision_quote"]
    # prev_batch_anchor：r5 锚点全值在场+机制差异如实声明
    pba = bundle1["prev_batch_anchor"]
    assert pba["ledger_head_sha256"] == R5_HEAD
    assert pba["last_entry_sha256"] == R5_LAST_ENTRY
    assert pba["ledger_file_sha256"] == R5_LEDGER_SHA
    assert pba["checkpoint_id"] == "CKPT-V3-APPROVALS-R5"
    assert "非 Genesis" in pba["anchor_semantics"]
    assert "verify_continuation_chain" in pba["anchor_semantics"]
    # 零门/零谓词翻动显式声明（状态文本措辞：不改写任何机器门与谓词）
    assert "不改写任何机器门与谓词" in bundle1["frozen_machine_gate_status"]
    assert "production_signoff_ready=false 维持" in \
        bundle1["frozen_machine_gate_status"]


# ---------------------------------------------------------------------------
# ③ 4 份 disposition：存在性+APR 编号+语义边界字段
# ---------------------------------------------------------------------------

def test_r6_dispositions_schema_valid_with_semantic_boundary():
    bundle = json.loads(_read_text(REL_R6_BUNDLE))
    codes = {"APR-0017": "c1_dependency_cycle_path_a_adopted",
             "APR-0018": "c2c3_freeze_package_and_v2c_prereq_adopted",
             "APR-0019": "c4_reproducibility_pre_frozen_protocol_adopted",
             "APR-0020": "c5c6_doc_sync_and_baseline_naming_adopted"}
    by_id = {}
    filenames = {"APR-0017":
                 "disposition-APR-0017-c1-dependency-cycle-path-a.json",
                 "APR-0018":
                 "disposition-APR-0018-c2c3-freeze-package-and-"
                 "v2c-prereq.json",
                 "APR-0019":
                 "disposition-APR-0019-c4-reproducibility-"
                 "pre-frozen-protocol.json",
                 "APR-0020":
                 "disposition-APR-0020-c5c6-doc-sync-and-"
                 "baseline-naming.json"}
    for rec in bundle["dispositions"]:
        apr = rec["disposition_id"]
        by_id[apr] = rec["rationale_text"]
        # 存在性：落盘独立文件与 bundle 内记录逐字段一致
        fname = bundle["disposition_files"][apr]
        assert fname == filenames[apr], apr
        disk = json.loads(_read_text(os.path.join(
            "out/v3-approvals", fname)))
        assert disk == rec
        # schema 合法（disposition_record，hash 09dd31fd 未变）
        assert schemas.validate("disposition_record", rec) == []
        assert rec["kind"] == "accept"
        assert rec["scope"] == "adoption"
        assert rec["approver"] == "user"
        assert rec["approver_role"] == "human_authority"
        assert rec["rationale_code"] == codes[apr]
        assert bundle["user_decisions"][apr]["decision_label"] \
            in rec["rationale_text"]
    # 语义边界字段：每份必含（大意逐条写明）
    for apr, text in by_id.items():
        assert "只落在 disposition/文档域" in text, apr
        assert "不翻转任何机器门谓词" in text, apr
        assert "BL-1" in text, apr
        assert "逐阶段" in text and "显式用户批准" in text, apr
        assert "不修改任何既有 out/ 产物与批准记录" in text, apr
        assert "supersedes" in text and "不可回写" in text, apr
    # 各项语义要点抽查
    assert "外部分析支路已齐" in by_id["APR-0017"]
    assert "V2-d 回填" in by_id["APR-0017"]
    assert "成环解除" in by_id["APR-0017"]
    assert "冻结包" in by_id["APR-0018"]
    assert "BOM 基线 hash" in by_id["APR-0018"]
    assert "治具兼容" in by_id["APR-0018"]
    assert "median-vs-median" in by_id["APR-0019"]
    assert "min_runs=3 fail-closed" in by_id["APR-0019"]
    assert "N≥3" in by_id["APR-0019"]
    assert "流程冻结基线" in by_id["APR-0020"]
    assert "实物性能基线" in by_id["APR-0020"]
    assert "ASM DONE 不替代" in by_id["APR-0020"]


# ---------------------------------------------------------------------------
# ④ VERIFICATION-ROADMAP.md：C1–C6 修订语句在场+原文历史语义保留
# ---------------------------------------------------------------------------

def test_roadmap_contains_c1_to_c6_revisions_with_apr_refs():
    text = _read_text(REL_ROADMAP)
    assert "2026-09-06" in text
    # C6：两类基线具名定义（术语位置）
    assert "两类基线具名区分" in text
    assert "**流程冻结基线**" in text and "**实物性能基线**" in text
    assert "ASM DONE 不替代实物" in text
    # C5：§0 现状更新注（纯文档状态同步、零门语义）
    assert "2026-09-06 现状更新注（APR-0020/C5" in text
    assert "ASM-7 已收口 **DONE**" in text
    assert "零门语义" in text
    # C4：启动前置 #1 预冻结重复实验协议
    assert "APR-0019/C4" in text
    assert "预先冻结重复实验协议" in text
    assert "median-vs-median" in text
    assert "min_runs=3 fail-closed" in text
    assert "全部运行" in text and "留痕含失败" in text
    # C1：启动前置 #2 路径 A 修订注
    assert "APR-0017/C1" in text and "路径 A 解环" in text
    assert "限定为外部分析支路已齐" in text
    assert "明确由 V2-d 回填" in text
    # C2：V2-a 冻结包扩展
    assert "APR-0018/C2" in text and "冻结包" in text
    assert "BOM 基线 hash+逐项差异清单" in text
    assert "固件基线 sha256 与 Rev-C 基线同源证明" in text
    assert "治具兼容初检" in text
    assert "每项 hash 在案" in text and "冻结后只读" in text
    # C3：V2-c 进入条件增列
    assert "APR-0018/C3" in text
    assert "叠层/制造装配两项已核验" in text
    assert "治具兼容检查" in text
    # §3 映射表注：成环解除
    assert "依赖成环已解除" in text


def test_roadmap_preserves_original_text_and_apr0009_block():
    text = _read_text(REL_ROADMAP)
    # 文件头状态行（2026-09-05 批准）不动
    assert "status: approved（2026-09-05 用户批准 Tier 1+2 立项" in text
    # §2 启动前置 #2 原文保留（历史语义，追加注记而非改写）
    assert "**TL-3 真实物理证据链**——required 级 authority 证据（外部分析/\n" \
           "   回板实测）；screening 级合成数据已如实 fail（对应 BL-2）。" in text
    assert "历史语义" in text
    # V2-a 原表保留（原退出产物行逐字在场）
    assert "### 阶段 V2-a：冻结 Rev-C 原理图" in text
    assert "| 退出产物 | 原理图冻结记录（hash+版本+来源） |" in text
    # V2-c 原进入条件行保留
    assert "| 进入条件 | V2-b 候选门通过；用户批准投产（预算/数量 2–5 片裁决） |" in text
    # §5 APR-0009 批准块原文不动
    assert "## 5. 批准块（2026-09-05，S17 入账）" in text
    assert "disposition-APR-0009-verification-roadmap-tiers.json" in text
    assert "**批准≠门翻转**" in text
    # §0 原锚点行保留（2026-09-05 历史语义）
    assert "**ASM-7 待 A-4**" in text


# ---------------------------------------------------------------------------
# ⑤ 提案状态翻转 adopted + 披露段/§6 原表保留
# ---------------------------------------------------------------------------

def test_proposal_status_adopted_with_apr_refs_and_disclosure_kept():
    text = _read_text(REL_PROPOSAL)
    # 头部状态=adopted，附 APR 引用与日期
    assert "**状态**：`adopted`" in text
    for apr in R6_APRS:
        assert apr in text
    assert R6_DATE in text
    assert "`proposal`" in text   # 历史语义标注在场（保留原文表述）
    # 执行方式披露段（主智能体成文披露）原文保留
    assert "**执行方式披露**：本提案因派发通道持续故障（并发超限" in text
    assert "由主智能体亲笔成文，偏离\"子智能体执行\"常规模式；内容为纯" in text
    assert "设计文档、零代码零门，风险面与该偏离相称" in text
    # §6 表头改为已采纳表述（原「全部待批，采纳前零执行」保留为历史语义）
    assert "## §6 精确变更清单（2026-09-06 已采纳" in text
    assert "全部待批，采纳前零执行」为历史语义" in text
    # §6 原表内容保留（C1..C6 行逐字抽查）
    assert "| C1 | VERIFICATION-ROADMAP §2 启动前置 #2 |" in text
    assert "| C2 | VERIFICATION-ROADMAP V2-a |" in text
    assert "| C3 | VERIFICATION-ROADMAP V2-c 进入条件 |" in text
    assert "| C4 | VERIFICATION-ROADMAP §2 启动前置 #1 |" in text
    assert "| C5 | VERIFICATION-ROADMAP §0 现状锚点 |" in text
    assert "| C6 | 两类基线具名区分（§1） |" in text
    # §7 落地方式与文尾不动
    assert "追加式修订" in text and "（完）" in text


# ---------------------------------------------------------------------------
# ⑥ 受保护三文件 + r1–r5 批准工件零改动
# ---------------------------------------------------------------------------

def test_protected_files_and_prior_approval_artifacts_unchanged():
    for rel, want in UNCHANGED_FILES.items():
        assert hashing.sha256_file(_repo_rel(rel)) == want, rel
