#!/usr/bin/env python
"""S32-R1：P4-C 路线图边界修订采纳登记（r6 bundle；disposition 域；
与 s28 r5 批次同构模式）。

2026-09-06 用户（human authority）经结构化提问批准
V3-ROADMAP-BOUNDARY-PROPOSAL.md §6 全部六项变更（裁决原文语义见
USER_DECISIONS_R6 与各 disposition rationale_text）：

- APR-0017（C1，裁决=路径 A 解环）：V2-b 进入条件中的「TL-3 证据链」
  限定为外部分析支路已齐（真实外部 DFM/SI/PI 报告入账，required 级
  authority）；回板实测支路明确由 V2-d 回填（与路线图 §3 映射表
  「V2-d 消解 BL-2」一致）；V2-b↔V2-c/V2-d 依赖成环解除；
- APR-0018（C2+C3）：V2-a「冻结原理图」扩为「冻结包」（+BOM 基线
  hash+逐项差异清单、固件基线 sha256 同源证明、测试环境口径、治具
  兼容初检；每项 hash 在案、冻结后只读）；V2-c 进入条件增列「叠层/
  制造装配两项已核验」+治具兼容检查（候选门附加检查）；
- APR-0019（C4）：§2 启动前置 #1 追加——非确定性后端必须在
  qualification 前预先冻结重复实验协议（次数 N≥3、汇总口径
  median-vs-median、min_runs=3 fail-closed、全部运行留痕含失败），
  不得事后挑选最优一次；协议冻结时点=qualification 包开工前
  （预注册纪律）；
- APR-0020（C5+C6）：§0 现状锚点更新（ASM-7 已收口 DONE；TL-2 校准
  多轮实测在案——纯文档状态同步，零门语义）；两类基线具名写入路线
  图术语位置（流程冻结基线 vs 实物性能基线；ASM DONE 不替代后者）。

落地=对 VERIFICATION-ROADMAP.md 的追加式修订（2026-09-06 修订块/
注记七处，原文保留标注历史语义，参照 APR-0002 追加式先例）+本提案
状态翻转 proposal→adopted；本脚本只登记批准（disposition 域）。

同构不变量（与 s28 r5 批次逐字同模式）：每项批准=一条
disposition_record（kind=accept、scope=adoption）+ 一条 ledger entry
（entry_kind=disposition、authority=human、trust_level=untrusted——
处置是决定不是事实，恒不可升级）；validate_no_gate_write 对全部记录
强制（零门/零谓词翻动）；evidence=两份落地文档（修订后路线图+采纳态
提案）sha256（磁盘实读对账，缺文件 fail-closed）；批准日期=人工声明
常量 S32_DATE="2026-09-06"（非机器 wall-clock）；evidence 一律仓库
相对 POSIX 路径；批准只能被后续 supersedes 追加式取代，不可回写；
r1–r5 批次登记文件字节不动（本批全部为新文件）。

账本续链（与 s28 同构，含一处如实声明的机制差异）：r5 末条
（APR-E-0016，entry_sha256 前 8=59dd4b37）prev 非空（=a5c9fdcb…，
r5 文件内第 6 条）、entry_seq=5——逐字拷贝为 decision-ledger-r6.jsonl
首行后**自带其 prev/seq，非 Genesis**。ledger.verify_chain 对文件内
首条强制 Genesis prev=null 且 entry_seq=文件位，故 r6 全文件不适用
直接 verify_chain（如实声明，不绕不藏）；验证=三重锚：
① r5 源文件全链 verify_chain（6 条）可验（续接行出自已验链）；
② r6 首行与 r5 末行逐字节等式（拷贝零改写）；
③ verify_continuation_chain：entry[0] 与 r5 盘上末条 dict 等式+
   body-hash 重算，其后 4 条新 entry 逐条执行 verify_chain 同款检查
   （entry_seq=文件位 1..4、prev=前条 entry_sha256、
   ledger_head_sha256=sha256_text(prev_head+":"+entry_sha256)——首条
   新 entry 的 head 以 r5 head a7a4b7aa… 为 prev_head 跨文件续链、
   body hash 重算、schema、TRUST_POLICY 白名单、human 仅限
   disposition 类）。新 entry 构造用 ledger.make_entry（=append 去
   Genesis 校验；s28 同款链式机制，仅因续接行非 Genesis 而跳过对
   续接行的位置断言）。checkpoint 不变量保持：last_seq==count-1
   （4==5-1）。

落盘（byte-exact 可重跑；已存在则重建比对一致后退出不覆写，不一致=
fail；全部为 out/v3-approvals/ r6 新文件）：
- approvals-bundle-r6.json
- decision-ledger-r6.jsonl（5 行：r5 末条逐字续入 + APR-0017..0020）
- disposition-APR-0017-c1-dependency-cycle-path-a.json
- disposition-APR-0018-c2c3-freeze-package-and-v2c-prereq.json
- disposition-APR-0019-c4-reproducibility-pre-frozen-protocol.json
- disposition-APR-0020-c5c6-doc-sync-and-baseline-naming.json

机制：canonical JSON；零子进程；零网络；无 wall-clock；datasets/ 只读；
零门/零谓词翻动（gate_write_scan 全空 + frozen_machine_gate_status
显式声明）。收尾打印新件 sha256 前 8。

用法：python scripts/s32_p4c_adopt_approvals.py   （仓库根执行）
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import config, disposition, hashing, ledger, schemas  # noqa: E402

OUT_APR = REPO / "out" / "v3-approvals"

S32_DATE = "2026-09-06"  # 人工会话声明日期（非 wall-clock；=APPROVAL_DATE_R6）
APPROVER = "user"
APPROVER_ROLE = "human_authority"
APPROVALS_REVISION_R6 = "v3-approvals-r6"
CHECKPOINT_ID_R6 = "CKPT-V3-APPROVALS-R6"
SCHEMA_VERSION = schemas.SCHEMA_V3

REL_R5_LEDGER = "out/v3-approvals/decision-ledger-r5.jsonl"
REL_R5_BUNDLE = "out/v3-approvals/approvals-bundle-r5.json"
REL_ROADMAP = "VERIFICATION-ROADMAP.md"
REL_PROPOSAL = "V3-ROADMAP-BOUNDARY-PROPOSAL.md"

# 先验锚（盘上实测入账；不配即中止——防篡改/防覆写，fail-closed）
FROZEN_SHA256 = {
    REL_R5_LEDGER: "448b0c705c3b582014901c5c81eb9a0cc6a69e88b9a6c3dfe3d5dacdaaa7e5fc",
    REL_R5_BUNDLE: "382c8f6e151b2a07cd4de5aebc860e61b5d25570f914f3a63fd1ef7845d45707",
    REL_ROADMAP: "f7b6943b41d9dbacaafcbb49322217f3cc4e1eb3c61306454c796e38c24b9640",
    REL_PROPOSAL: "f406b72fdd53412ca5eeda0eb3377f2ca3e7bb4b9824b82bb4650db48e9c13c6",
}

# r5 末条（续链锚，落盘前与 r5 文件实读复核）
R5_HEAD_SHA256 = "a7a4b7aa3188f96d8eb2c480cde63ea87bec18f0c121c50f49928c08040f9902"
R5_LAST_ENTRY_SHA256 = "59dd4b3794282b7810d7092f02a0ce0fc645667b666cae38090468b6b92c7422"
R5_LAST_ENTRY_SEQ = 5
R5_LAST_PREV_SHA256 = "a5c9fdcbf72fbdfe933a362d999ec434c86f024c50eef186f96b78ebfacaa25a"

# evidence 逻辑名 → 仓库相对 POSIX 路径（磁盘实读；输出无主机路径）
EVIDENCE_FILES_R6 = (
    ("roadmap_revised", REL_ROADMAP),
    ("proposal_adopted", REL_PROPOSAL),
)

# 用户裁决原文语义（2026-09-06 结构化提问四项裁决；日期=人工声明常量）
USER_DECISIONS_R6 = {
    "APR-0017": {
        "decision_label": "路径A（解环）",
        "decision_quote": ("「路径A（解环）」——V2-b 进入条件中的「TL-3 "
                           "证据链」限定为外部分析支路已齐（真实外部 "
                           "DFM/SI/PI 报告入账，required 级 authority）；"
                           "回板实测支路明确由 V2-d 回填（与路线图 §3 "
                           "映射表「V2-d 消解 BL-2」一致）。"),
        "decided_date": S32_DATE,
    },
    "APR-0018": {
        "decision_label": "冻结包扩展+V2-c前置增列",
        "decision_quote": ("「C2+C3=冻结包扩展+V2-c前置增列」——V2-a 从"
                           "「冻结原理图」扩为「冻结包」（+BOM 基线 hash+"
                           "逐项差异清单、固件基线 sha256 同源证明、测试"
                           "环境口径、治具兼容初检；每项 hash 在案、冻结后"
                           "只读）；V2-c 进入条件加「叠层/制造装配两项已"
                           "核验」+治具兼容检查（候选门附加检查）。"),
        "decided_date": S32_DATE,
    },
    "APR-0019": {
        "decision_label": "重现性预冻结协议",
        "decision_quote": ("「C4=重现性预冻结协议」——非确定性后端必须在 "
                           "qualification 前预先冻结重复实验协议（次数 "
                           "N≥3、汇总口径 median-vs-median、min_runs=3 "
                           "fail-closed、全部运行留痕含失败），不得事后"
                           "挑选最优一次；协议冻结时点=qualification 包"
                           "开工前（预注册纪律）。"),
        "decided_date": S32_DATE,
    },
    "APR-0020": {
        "decision_label": "文档同步+两类基线具名",
        "decision_quote": ("「C5+C6=文档同步+两类基线具名」——§0 现状锚点"
                           "更新（ASM-7 已收口 DONE；TL-2 校准多轮实测在"
                           "案——纯文档状态同步，零门语义）；两类基线具名"
                           "写入路线图术语位置——流程冻结基线（ASM-7 收口+"
                           "语料参考态验证）vs 实物性能基线（仅来自 V2-c/"
                           "V2-d），ASM DONE 不替代后者。"),
        "decided_date": S32_DATE,
    },
}

# 语义边界字段（每份 disposition rationale_text 必含，大意逐条写明）
_SEMANTIC_BOUNDARY_CLOSING = (
    "语义边界：①本批准只落在 disposition/文档域，不翻转任何机器门谓词"
    "（零门/零谓词翻动，机器门由机器谓词计算，人工不可直写）；②层次二"
    "启动仍受 BL-1（布线引擎决策或等效外部后端 qualification）与逐阶段"
    "显式用户批准硬约束；③不修改任何既有 out/ 产物与批准记录（r1–r5 批"
    "次登记文件字节不动，本批全部为新文件）；④本批准可被后续 supersedes "
    "追加式取代，不可回写。")

# 一项批准定义（数据即账：语义限定逐条对应 2026-09-06 人工裁决）
APPROVAL_SPECS_R6 = (
    {
        "approval_id": "APR-0017",
        "entry_id": "APR-E-0017",
        "slug": "c1-dependency-cycle-path-a",
        "subject": ("C1 路径 A（解环）：V2-b 进入条件中「TL-3 证据链」限定"
                    "为外部分析支路已齐；回板实测支路由 V2-d 回填"),
        "kind": "accept",
        "scope": "adoption",
        "rationale_code": "c1_dependency_cycle_path_a_adopted",
        "rationale_text": (
            "用户人工批准 @2026-09-06（human authority，裁决原文语义："
            "「路径A（解环）」）。语义：①V2-b 进入条件中的「TL-3 证据链」"
            "限定为外部分析支路已齐（真实外部 DFM/SI/PI 报告入账，"
            "required 级 authority）；②回板实测支路明确由 V2-d 回填（与 "
            "VERIFICATION-ROADMAP §3 映射表「V2-d 消解 BL-2」一致）；"
            "③V2-b↔V2-c/V2-d 依赖成环解除（若证据链被强读为必须含回板实"
            "测，则 V2-b 依赖 V2-c/V2-d 产物而 V2-c 依赖 V2-b 候选布局，"
            "循环）。落地=路线图 §2 启动前置 #2 追加修订注：2026-09-05 原"
            "文保留并标注历史语义（追加式修订，参照 APR-0002 先例），§3 "
            "映射表附近加解环注。V2-b 质量门（不低于 Rev-C 对照基线）不"
            "依赖 TL-3/TL-6，语义不变。" + _SEMANTIC_BOUNDARY_CLOSING),
        "fact_refs": ["VERIFICATION-ROADMAP",
                      "V3-ROADMAP-BOUNDARY-PROPOSAL", "APR-0009"],
        "evidence": ("roadmap_revised", "proposal_adopted"),
    },
    {
        "approval_id": "APR-0018",
        "entry_id": "APR-E-0018",
        "slug": "c2c3-freeze-package-and-v2c-prereq",
        "subject": ("C2+C3：V2-a「冻结原理图」扩为「冻结包」（+BOM/固件/"
                    "测试环境/治具初检）；V2-c 进入条件增列叠层/制造装配"
                    "核验+治具兼容检查"),
        "kind": "accept",
        "scope": "adoption",
        "rationale_code": "c2c3_freeze_package_and_v2c_prereq_adopted",
        "rationale_text": (
            "用户人工批准 @2026-09-06（human authority，裁决原文语义："
            "「C2+C3=冻结包扩展+V2-c前置增列」）。C2 语义：V2-a 从「冻结"
            "原理图」扩为「冻结包」——增列 BOM 基线 hash+逐项差异清单、固"
            "件基线 sha256 与 Rev-C 基线同源证明、测试环境口径（测试激励/"
            "观测点/仪器配置/环境温度记录口径）、治具兼容初检；每项 hash "
            "在案、冻结后只读；原 V2-a 阶段表保留 2026-09-05 历史语义，扩"
            "展范围以修订块为准。C3 语义：V2-c 进入条件增列「叠层/制造装"
            "配两项已核验」（板厂最终叠层与 Rev-C 一致性声明；制造/装配"
            "厂工艺能力、FEEDER/钢网同源核验）+治具兼容检查（Rev-C "
            "bring-up 治具对 Rev-D 机械/电气兼容清单，作为 Rev-D 候选门附"
            "加检查）。" + _SEMANTIC_BOUNDARY_CLOSING),
        "fact_refs": ["VERIFICATION-ROADMAP",
                      "V3-ROADMAP-BOUNDARY-PROPOSAL"],
        "evidence": ("roadmap_revised", "proposal_adopted"),
    },
    {
        "approval_id": "APR-0019",
        "entry_id": "APR-E-0019",
        "slug": "c4-reproducibility-pre-frozen-protocol",
        "subject": ("C4：§2 启动前置 #1 追加——非确定性后端 qualification "
                    "前预冻结重复实验协议（N≥3、median-vs-median、"
                    "min_runs=3 fail-closed、全部运行留痕含失败）"),
        "kind": "accept",
        "scope": "adoption",
        "rationale_code": "c4_reproducibility_pre_frozen_protocol_adopted",
        "rationale_text": (
            "用户人工批准 @2026-09-06（human authority，裁决原文语义："
            "「C4=重现性预冻结协议」）。语义：层次二启动前置 #1（BL-1 项）"
            "追加——非确定性后端必须在 qualification 前预先冻结重复实验"
            "协议（次数 N≥3、汇总口径 median-vs-median、min_runs=3 "
            "fail-closed、全部运行留痕含失败），不得事后挑选最优一次；协"
            "议冻结时点=qualification 包开工前（预注册纪律，与校准线同"
            "构）。口径即 S12 已落地的 A/B 统计口径升格为前置强制（D19(b)"
            " kicad-cli 双 severity 跨运行计数不稳、D20(b') JVM 非确定性"
            "死锁两次真实教训入账为动机）。" + _SEMANTIC_BOUNDARY_CLOSING),
        "fact_refs": ["VERIFICATION-ROADMAP",
                      "V3-ROADMAP-BOUNDARY-PROPOSAL",
                      "D19(b)", "D20(b')"],
        "evidence": ("roadmap_revised", "proposal_adopted"),
    },
    {
        "approval_id": "APR-0020",
        "entry_id": "APR-E-0020",
        "slug": "c5c6-doc-sync-and-baseline-naming",
        "subject": ("C5+C6：§0 现状锚点更新（ASM-7 已收口 DONE；TL-2 校准"
                    "多轮实测在案——纯文档状态同步）+两类基线具名写入术语"
                    "（流程冻结基线 vs 实物性能基线）"),
        "kind": "accept",
        "scope": "adoption",
        "rationale_code": "c5c6_doc_sync_and_baseline_naming_adopted",
        "rationale_text": (
            "用户人工批准 @2026-09-06（human authority，裁决原文语义："
            "「C5+C6=文档同步+两类基线具名」）。C5 语义：路线图 §0 追加 "
            "2026-09-06 现状更新注——ASM-7 已收口 DONE（A-4 已批）、TL-2 "
            "校准多轮实测在案（盘上实测=v1/v2/r3/r4/r5 五轮；提案 §6 C5 "
            "行「四轮」为历史笔误，按盘上实值落笔）；2026-09-05 原文保留"
            "标注历史语义；纯文档状态同步、零门语义，open blocker 状态不"
            "因本注变动。C6 语义：两类基线具名写入路线图术语位置——**流"
            "程冻结基线**（ASM-7 收口+corpus 参考态验证：「工具算得对」的"
            "可审计工程产物链，ASM DONE 属此类）vs **实物性能基线**（「工"
            "具生成的布局/布线在物理板上能用」：仅来自 V2-c/V2-d，当前不"
            "具备）；两者必须具名区分、禁止互相替代；**ASM DONE 不替代实"
            "物性能基线**，任何「ASM DONE/参考态 17/17/TL-5 pass」不得被"
            "引用为工具生成物的实物性能证据。" + _SEMANTIC_BOUNDARY_CLOSING),
        "fact_refs": ["VERIFICATION-ROADMAP",
                      "V3-ROADMAP-BOUNDARY-PROPOSAL", "ASM-7", "TL-2"],
        "evidence": ("roadmap_revised", "proposal_adopted"),
    },
)

FROZEN_MACHINE_GATE_STATUS_R6 = (
    "本登记不重算、不改写任何机器门与谓词：TL-3-G1/TL-4-G/TL-5-G 既有"
    "裁决与分母不变；TL-6 readiness 投影不回写、production_signoff_ready"
    "=false 维持（实物性能基线尚不存在，ASM DONE 不替代）；TL-2 达标线"
    "（APR-0011 暂时采纳）与自动分流 blocked 语义不变；qualification 重走"
    "要求（BL-1 项）本体不变，C4 仅为其追加预注册纪律。层次二启动仍受 "
    "BL-1 与逐阶段显式用户批准硬约束。本批四项批准只落 disposition/文档"
    "域（L6 事实/处置/门分离）：路线图边界修订采纳=文档语义登记，不构成"
    "任何质量结论、门输入或自动分流资格。"
)


def _fail(msg: str) -> None:
    print(f"[s32-apr6] FAIL: {msg}")
    sys.exit(1)


def _sha(rel: str) -> str:
    path = REPO.joinpath(*rel.split("/"))
    if not path.is_file():
        _fail(f"输入缺失（fail-closed）: {rel}")
    return hashing.sha256_file(str(path))


def disposition_filename(spec: dict) -> str:
    """批准处置记录落盘文件名（out/v3-approvals/ 编排口径）。"""
    return f"disposition-{spec['approval_id']}-{spec['slug']}.json"


def _ledger_bytes(entries) -> bytes:
    """账本落盘字节（编排侧写 decision-ledger-r6.jsonl 的唯一口径）。"""
    return "".join(
        json.dumps(e, ensure_ascii=config.JSON_ENSURE_ASCII,
                   sort_keys=config.JSON_SORT_KEYS) + "\n"
        for e in entries).encode(config.ENCODING)


def verify_continuation_chain(entries, anchor: dict) -> list:
    """r6 跨文件续链校验（verify_chain 同款检查，续接锚如实声明）。

    ledger.verify_chain 对文件内首条强制 Genesis prev=null 且
    entry_seq=文件位；r6 首行=r5 末条逐字续入（自带 prev/seq，非
    Genesis），故全文件 verify_chain 不适用。本函数：entry[0] 与 r5
    盘上末条 dict 等式 + body-hash 重算（其 prev/head/seq 真值由 r5
    源文件全链 verify_chain 保证）；entry[1:] 逐条执行 verify_chain
    同款检查（seq=文件位、prev/head 链、body hash、schema、trust 白
    名单、human 仅限 disposition 类）。
    """
    errors: list = []
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"entry[{i}]: 非 dict（{type(entry).__name__}）")
            continue
        for e in schemas.validate("decision_ledger_entry", entry):
            errors.append(f"entry[{i}]: {e}")
        if entry.get("entry_sha256") != ledger.entry_body_sha256(entry):
            errors.append(f"entry[{i}]: entry_sha256 重算不一致")
        if i == 0:
            if entry != anchor:
                errors.append("entry[0]: 与 r5 末条续接锚不等（逐字拷贝"
                              "被改写，禁止）")
            continue
        prev = entries[i - 1]
        if entry.get("entry_seq") != i:
            errors.append(f"entry[{i}]: entry_seq 应为 {i}（0 起连续，"
                          f"续接行后按文件位），得到 {entry.get('entry_seq')!r}")
        if entry.get("prev_entry_sha256") != prev.get("entry_sha256"):
            errors.append(
                f"entry[{i}]: prev_entry_sha256 与上一条 entry_sha256 "
                f"不一致（期望 {str(prev.get('entry_sha256'))[:12]}…，"
                f"得到 {str(entry.get('prev_entry_sha256'))[:12]}…）")
        expected_head = hashing.sha256_text(
            str(prev.get("ledger_head_sha256")) + ":" +
            str(entry.get("entry_sha256")))
        if entry.get("ledger_head_sha256") != expected_head:
            errors.append(f"entry[{i}]: ledger_head_sha256 重算不一致")
        authority = entry.get("authority")
        trust = entry.get("trust_level")
        allowed = ledger.TRUST_POLICY.get(authority)
        if allowed is None:
            errors.append(f"entry[{i}]: 未知 authority {authority!r}")
        elif trust not in allowed:
            errors.append(
                f"entry[{i}]: authority {authority!r} 不允许 trust_level "
                f"{trust!r}（白名单 {sorted(allowed)}）")
        if authority == "human":
            if entry.get("entry_kind") not in ledger.HUMAN_AUTHORITY_ENTRY_KINDS:
                errors.append(
                    f"entry[{i}]: human authority 只允许出现在 "
                    f"{list(ledger.HUMAN_AUTHORITY_ENTRY_KINDS)} 类 entry")
    return errors


def _read_r5_anchor() -> tuple:
    """读 r5 账本（续链基座；r5 文件字节不动）：返回 (全 entries, 末条)。"""
    lines = (OUT_APR / "decision-ledger-r5.jsonl") \
        .read_text(encoding="utf-8").splitlines()
    if len(lines) != 6:
        _fail(f"r5 ledger 行数非 6: {len(lines)}")
    entries = [json.loads(line) for line in lines]
    if ledger.verify_chain(entries) != []:
        _fail("r5 源文件全链校验失败（续链基座不可信）")
    anchor = entries[-1]
    if anchor.get("entry_id") != "APR-E-0016" \
            or anchor.get("entry_sha256") != R5_LAST_ENTRY_SHA256 \
            or anchor.get("ledger_head_sha256") != R5_HEAD_SHA256 \
            or anchor.get("entry_seq") != R5_LAST_ENTRY_SEQ \
            or anchor.get("prev_entry_sha256") != R5_LAST_PREV_SHA256:
        _fail("r5 末条与先验锚 59dd4b37/a7a4b7aa 不符")
    return entries, anchor


def build_approvals_bundle_r6(evidence_hashes: dict) -> dict:
    """构造 r6 完整登记 bundle（纯函数；同输入 byte-exact）。

    evidence_hashes 必须覆盖 EVIDENCE_FILES_R6 全部逻辑名（缺一
    fail-closed ValueError）。
    """
    missing = [name for name, _ in EVIDENCE_FILES_R6
               if not evidence_hashes.get(name)]
    if missing:
        raise ValueError(
            f"evidence 缺失（fail-closed 拒绝构造批准）: {missing}")
    hashes = dict(evidence_hashes)

    # r5 末条实读复核（续链基座；r5 文件字节不动）
    r5_entries, anchor = _read_r5_anchor()

    dispositions: list = []
    entries: list = [anchor]  # 首行=r5 末条逐字续入（自带 prev/seq）
    gate_write_scan: dict = {}
    for spec in APPROVAL_SPECS_R6:
        record = disposition.build_disposition(
            disposition_id=spec["approval_id"],
            fact_refs=spec["fact_refs"],
            kind=spec["kind"],
            scope=spec["scope"],
            rationale_code=spec["rationale_code"],
            rationale_text=spec["rationale_text"],
            approver=APPROVER,
            approver_role=APPROVER_ROLE)
        scan = disposition.validate_no_gate_write(record)
        if scan:
            raise ValueError(f"{spec['approval_id']} 触发门写禁区: {scan}")
        gate_write_scan[spec["approval_id"]] = scan
        dispositions.append(record)
        # make_entry=append 去 Genesis 校验（续接行非 Genesis；链式机制
        # 照抄 s28：seq=当前表长、prev=前条 entry_sha256、head 续算）
        entry = ledger.make_entry(
            entries,
            entry_kind="disposition",
            schema_validation=ledger.make_schema_validation(
                "disposition_record"),
            authority="human",
            trust_level="untrusted",
            entry_id=spec["entry_id"],
            actor=APPROVER,
            actor_role=APPROVER_ROLE,
            disposition_refs=[spec["approval_id"]],
            payload_ref=hashing.sha256_bytes(
                hashing.canonical_json_bytes(record)),
            artifact_hashes={name: hashes[name]
                             for name in spec["evidence"]},
            snapshot_revision=APPROVALS_REVISION_R6)
        entries.append(entry)

    # 续链语义自证：首条新 entry 的 prev 锚 r5 末条 entry_sha256，
    # head 以 r5 head a7a4b7aa… 为 prev_head 跨文件续链
    first_new = entries[1]
    expected_head = hashing.sha256_text(
        R5_HEAD_SHA256 + ":" + first_new["entry_sha256"])
    if first_new["ledger_head_sha256"] != expected_head or \
            first_new["prev_entry_sha256"] != anchor["entry_sha256"]:
        _fail("续链锚定失败（head 未以 r5 head a7a4b7aa 续链）")
    cont_errors = verify_continuation_chain(entries, anchor)
    if cont_errors:
        _fail(f"r6 续链校验失败：{cont_errors}")
    if ledger.verify_supersedes(entries) != [] or len(entries) != 5:
        _fail("r6 账本 supersedes/条数校验失败")

    bundle = {
        "schema_version": SCHEMA_VERSION,
        "approval_date": S32_DATE,
        "approver": {"actor": APPROVER, "actor_role": APPROVER_ROLE},
        "revision": APPROVALS_REVISION_R6,
        "approval_count": len(APPROVAL_SPECS_R6),
        "supersedes_note": (
            "r6 为追加批次：不取代、不改写 r1（APR-0001–0006）、"
            "r2（APR-0007–0009）、r3（APR-0010）、r4（APR-0011）、"
            "r5（APR-0012–0016）；out/v3-approvals/ 既有文件字节不动。"
            "本批四项批准均可被后续 supersedes 追加式取代，不可回写。"),
        "prev_batch_anchor": {
            "revision": "v3-approvals-r5",
            "ledger_file_rel": REL_R5_LEDGER,
            "ledger_file_sha256": hashes["_r5_ledger_file"],
            "checkpoint_id": "CKPT-V3-APPROVALS-R5",
            "ledger_head_sha256": R5_HEAD_SHA256,
            "last_entry_sha256": anchor["entry_sha256"],
            "anchor_semantics": (
                "r6 账本为跨文件续链：decision-ledger-r6.jsonl 首行=r5 末"
                "条 entry（APR-E-0016）逐字拷贝（只读复制，r5 文件字节不"
                "动），自带其 prev_entry_sha256（=a5c9fdcb…，r5 文件内第 "
                "6 条）与 entry_seq=5——续接行非 Genesis。其后 4 条新 "
                "entry（APR-0017..0020）的 prev_entry_sha256 锚定 r5 末条 "
                "entry_sha256（59dd4b37…）；首条新 entry 的 "
                "ledger_head_sha256=sha256_text(\"a7a4b7aa…\" + \":\" + "
                "entry_sha256)——head 链以 r5 head a7a4b7aa 为 prev_head "
                "跨文件续链。与 s28 r5 批次的机制差异（如实声明）：r4 末条"
                "恰为 Genesis（prev=null、seq=0），r5 全文件 verify_chain "
                "可验；r6 续接行非 Genesis 且 entry_seq≠文件位，"
                "ledger.verify_chain 对文件首条的 Genesis/位置断言不适用，"
                "验证改为三重锚——①r5 源文件全链 verify_chain（6 条）可"
                "验；②r6 首行与 r5 末行逐字节等式；③"
                "verify_continuation_chain（entry[0] 锚等式+body hash 重"
                "算，entry[1:] 逐条 verify_chain 同款检查，entry_seq=文件"
                "位 1..4）。checkpoint 不变量保持：last_seq==count-1"
                "（4==5-1）。新 entry 构造用 ledger.make_entry（=append "
                "去 Genesis 校验，链式机制照抄 s28）。"),
        },
        "user_decisions": USER_DECISIONS_R6,
        "dispositions": dispositions,
        "ledger_entries": entries,
        "ledger_file_sha256": hashing.sha256_bytes(_ledger_bytes(entries)),
        "ledger_verify": {
            "chain_errors": verify_continuation_chain(entries, anchor),
            "supersedes_errors": ledger.verify_supersedes(entries),
            "r5_source_chain_errors": ledger.verify_chain(r5_entries),
        },
        "ledger_checkpoint": ledger.make_checkpoint(entries,
                                                   CHECKPOINT_ID_R6),
        "gate_write_scan": gate_write_scan,
        "evidence_registry": [
            {"name": name, "path": path, "sha256": hashes[name]}
            for name, path in EVIDENCE_FILES_R6],
        "disposition_files": {spec["approval_id"]:
                              disposition_filename(spec)
                              for spec in APPROVAL_SPECS_R6},
        "frozen_machine_gate_status": FROZEN_MACHINE_GATE_STATUS_R6,
        "notes": [
            "四项人工批准（2026-09-06，P4-C 路线图边界修订采纳）："
            "APR-0017 C1 路径 A 解环（V2-b 的 TL-3 证据链=外部分析支路已"
            "齐，回板实测由 V2-d 回填）；APR-0018 C2+C3 冻结包扩展（BOM/"
            "固件/测试环境/治具初检逐项 hash 在案、冻结后只读）+V2-c 前置"
            "增列（叠层/制造装配核验+治具兼容检查）；APR-0019 C4 重现性预"
            "冻结协议（N≥3、median-vs-median、min_runs=3 fail-closed、全"
            "部运行留痕含失败，qualification 包开工前冻结，预注册纪律）；"
            "APR-0020 C5+C6 文档状态同步（ASM-7 收口 DONE、TL-2 校准实测"
            "在案，零门语义）+两类基线具名（流程冻结基线 vs 实物性能基线，"
            "ASM DONE 不替代后者）。",
            "落地方式=对 VERIFICATION-ROADMAP.md 的追加式修订（七处修订"
            "块/注记，2026-09-05 原文保留标注历史语义）+本提案状态翻转 "
            "proposal→adopted；每处修订带 APR 编号与日期。",
            "本账本为 disposition 域续链账本 r6 批次（r5 末条逐字续入+4 条"
            "新 entry），不改写既有 out/v3-approvals/ r1–r5 文件与任何 "
            "out/ 冻结产物；datasets/ 只读；实板零写入。",
            "scope 取值：disposition_record schema 的 scope 枚举含 "
            "adoption 项，本批四项均取 scope=adoption（边界修订/范围扩展/"
            "前置增列/措辞纪律采纳登记），如实映射。",
            "批准日期为人工声明常量（非机器 wall-clock）；evidence hash "
            "为生成时磁盘实读值，可用 sha256sum 对仓库文件复核。",
        ],
    }
    return bundle


def main() -> None:
    # 0) 先验锚：全部输入文件磁盘实读对账（fail-closed）
    hashes = {}
    for name, rel in EVIDENCE_FILES_R6:
        hashes[name] = _sha(rel)
    for rel, want in FROZEN_SHA256.items():
        actual = _sha(rel)
        if actual != want:
            _fail(f"输入 hash 与先验锚不符: {rel} {actual[:8]}…"
                  f"≠{want[:8]}…")
        if rel == REL_R5_LEDGER:
            hashes["_r5_ledger_file"] = actual

    # 1) bundle（纯函数构造 + 续链校验/门写扫描/checkpoint 复核）
    bundle = build_approvals_bundle_r6(hashes)
    verify = bundle["ledger_verify"]
    if verify["chain_errors"] or verify["supersedes_errors"] \
            or verify["r5_source_chain_errors"]:
        _fail(f"r6 账本校验失败：{verify}")
    for apr, scan in bundle["gate_write_scan"].items():
        if scan:
            _fail(f"{apr} 门写扫描非空（不可落盘）")
    ckpt_errors = ledger.verify_against_checkpoint(
        bundle["ledger_entries"], bundle["ledger_checkpoint"])
    if ckpt_errors:
        _fail(f"checkpoint 复核失败：{ckpt_errors}")

    # 2) 目标六件（byte-exact 可重跑；已存在则校验一致，不覆写）
    ledger_bytes = _ledger_bytes(bundle["ledger_entries"])
    if hashing.sha256_bytes(ledger_bytes) != bundle["ledger_file_sha256"]:
        _fail("decision-ledger-r6.jsonl 字节与 bundle 声明不符")
    targets = [
        (OUT_APR / "approvals-bundle-r6.json",
         hashing.canonical_json_bytes(bundle)),
        (OUT_APR / "decision-ledger-r6.jsonl", ledger_bytes),
    ]
    for spec in APPROVAL_SPECS_R6:
        rec = next(d for d in bundle["dispositions"]
                   if d["disposition_id"] == spec["approval_id"])
        targets.append(
            (OUT_APR / disposition_filename(spec),
             hashing.canonical_json_bytes(rec)))

    written: dict = {}
    for path, expected in targets:
        if path.exists():
            actual = path.read_bytes()
            if actual != expected:
                _fail(f"{path.name} 已存在且字节与本次构造不一致"
                      f"（byte-exact 校验失败；不覆写）")
            print(f"[s32-apr6] 已存在且一致（不覆写）：{path.name}")
        else:
            path.write_bytes(expected)
            print(f"[s32-apr6] 新增落盘：{path.name}")
        written[path] = hashing.sha256_bytes(expected)

    # 3) 落盘复读校验（续链 + 首行逐字等式 + r1–r5 台账/锚文件字节未动）
    disk_lines = (OUT_APR / "decision-ledger-r6.jsonl") \
        .read_text(encoding="utf-8").splitlines()
    r5_lines = (OUT_APR / "decision-ledger-r5.jsonl") \
        .read_text(encoding="utf-8").splitlines()
    if len(disk_lines) != 5:
        _fail(f"r6 账本行数非 5: {len(disk_lines)}")
    if disk_lines[0] != r5_lines[-1]:
        _fail("r6 首行与 r5 末行非逐字等式（拷贝被改写，禁止）")
    disk_anchor = json.loads(disk_lines[0])
    disk_entries = [json.loads(line) for line in disk_lines]
    if verify_continuation_chain(disk_entries, disk_anchor) != []:
        _fail("账本落盘复读续链校验失败")
    for rel, want in FROZEN_SHA256.items():
        if _sha(rel) != want:
            _fail(f"既有文件字节被改（禁止）: {rel}")

    # 4) 收尾：打印新件 sha256 前 8 + 门状态
    print("[s32-apr6] --- 新件 sha256（前 8）---")
    for path in sorted(written):
        print(f"[s32-apr6]   {path.relative_to(REPO).as_posix()}: "
              f"{written[path][:8]}")
    print(f"[s32-apr6] ledger: {len(disk_entries)} entries（r5 末条逐字续入+"
          f"APR-0017..0020）| checkpoint={bundle['ledger_checkpoint']['checkpoint_id']}"
          f" | head={bundle['ledger_checkpoint']['ledger_head_sha256'][:8]}…")
    print("[s32-apr6] APR-0017..0020 登记完成（r6 批次；r1–r5 字节不动）| "
          "零门/零谓词翻动")


if __name__ == "__main__":
    main()
