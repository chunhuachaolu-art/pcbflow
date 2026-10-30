#!/usr/bin/env python
"""S26-R1：人工批准登记（r4 bundle）+ 校准域状态 v3 + 评估协议 v1 冻结
落盘（纠偏词 P3-B 执行包 R1）。

库侧 pcbflow/approvals_r4.py 纯函数构造；本脚本只做磁盘实读对账 +
canonical 落盘（byte-exact 可重跑；已存在则校验一致后退出不覆写）：

- out/v3-approvals/approvals-bundle-r4.json（bundle；含 ledger_verify/
  checkpoint 投影与 threshold_baseline）
- out/v3-approvals/decision-ledger-r4.jsonl（1 条 disposition entry；
  与 r1/r2/r3 账本独立）
- out/v3-approvals/disposition-APR-0011-calibration-threshold-\
provisional-adoption.json（处置记录单件）
- out/v3-tl2/calibration/calibration-domain-v3.json（域状态 v3；基于
  盘上实读 domain-v2 纯函数构造）
- out/v3-tl2/calibration/evaluation-protocol-v1.md（评估协议 v1 冻结，
  纠偏词 P3-B）

红线：out/ 只读，例外仅限上述五件新文件；domain-v2 先验锚 hash 不符
即中止（防覆写 fail-closed）；两轮实测数值先对盘复核再写入域 v3；
datasets/ 只读；零子进程；无 wall-clock（日期=人工会话声明常量
2026-09-06）；canonical JSON byte-exact；gate_write_scan 必须全空、
链 verify+checkpoint 复核后方可落盘；收尾打印新件 sha256 前 8。
门状态：本包零翻转——critic_calibration_in_range 实测评估仍 False
（当前两轮实测未达标），自动分流仍 blocked（BL-4+TD5 合取）。

用法：python scripts/s26_approvals_r4.py   （仓库根执行）
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from pcbflow import approvals_r4, hashing, ledger  # noqa: E402

OUT_APR = REPO / "out" / "v3-approvals"
OUT_CAL = REPO / "out" / "v3-tl2" / "calibration"

S26_DATE = "2026-09-06"  # 人工会话声明日期（非 wall-clock；=APPROVAL_DATE_R4）

# 先验锚：被取代域状态文件（supersedes 对象；不符即中止——防覆写 fail-closed）
FROZEN_DOMAIN_V2_SHA256 = (
    "6e5b2437252c116a242ed1bddd8854a18c53d1b954d60f3c3507e36340253c9e")

# 两轮实测先验值（先对盘复核再进域 v3 in_calibrated_range_basis）
MEASURED_RUN_V2 = {"gt_recall": 0.25,
                   "reader_precision_vs_seed_gt": 0.142857}
MEASURED_RUN_V3_R2 = {"gt_recall": 0.25,
                      "seed_match_rate": 0.142857,
                      "abstain_rate": 0.533333}

# 评估协议 v1 冻结文本（纠偏词 P3-B；byte-exact 落盘的唯一口径）
EVALUATION_PROTOCOL_V1_MD = """# 校准评估协议 v1（evaluation-protocol-v1；纠偏词 P3-B 冻结）

- protocol_id: evaluation-protocol-v1
- 声明日期（人工声明常量，非机器 wall-clock）: 2026-09-06
- 域: TL-2 Critic 校准（APR-0008 线；种子域=calibration-domain-v1/v2/v3）
- 度量: calibration-metric-v3（匹配规则/命名约束/abstain 口径=calibration-process-v2 §2/§4/§5）
- 达标线: APR-0011 暂时采纳基线（provisional_supersedable；见 calibration-domain-v3 的 threshold_baseline 块）

> **状态行：本协议自本轮起冻结（metric=calibration-metric-v3；后续修订=新版本文件，不回写）。**
>
> 冻结对象=本文件全部条款；对既有冻结产物零回写（v1/v2 度量、run 件、process 文件字节不动）。

## 1. 三集分域（评估数据分域声明）

1. **development**：Rev-C 种子域——4 条种子 GT（development 比较器用；**不宣称独立完整人工标注**）。
2. **calibration**：同域后续轮——GT 扩样在此域积累（扩样走新版本 GT 文件，既有 GT 冻结不动）。
3. **frozen evaluation**：独立留出板集——**未建立，TBD；建立须人工批准+独立裁定**。
4. 「同板不同渲染≠独立板」（process-v2 §4）：同一语料板的多轮盲读/多批渲染只能作为同一样本的重复观察联合评价（连续性要求，process-v1 §5），不得当作独立样本累计达标次数或拼凑样本量；**跨板评测集≠种子域**。

## 2. 独立裁定要求（种子外 GT 化门槛）

- 种子外模型输出的 GT 化必须经**人工或独立合格裁定**（正例/负例/难例+类别覆盖）。
- 模型不得自造「人工确认」标签；无裁定→保持 pending，**不得为凑表生成新 GT**。

## 3. 达标评估规则（APR-0011 暂时采纳基线；联合评价）

同时满足下列各项（**联合评价**：任一不满足即未达标）：

1. `gt_recall ≥ 0.75`；
2. `seed_match_rate ≥ 0.5`——命名对账：process-v1 §5 提案的「precision≥0.5」出处=reader_precision_vs_seed_gt，度量 v3 已将其更名 seed_match_rate（同测量、口径同一）；**caveat 保留**：seed 匹配率=相对种子 GT 的诊断值，禁称完整 precision/FPR（种子为部分覆盖判例，框命中不证明电气事实）；
3. `abstain_rate ≤ 0.5`（abstain_rate 定义见度量 v3 abstain 块 / process-v2 §5：单位=旗标条数，分母=本次运行该板发出的全部旗标；弃权率与 recall/seed_match_rate 联合评价，**不单独优化**）；
4. **连续 2 轮**（不同渲染批）同时达标；
5. **GT ≥ 12**（有效分母：一对一匹配后 GT 侧计数，排除不可见性未声明的条目）。

- **达标≠自动分流**：BL-4（Critic 校准域+正式模型）+ TD5 分诊合取约束仍在，自动分流恒 blocked 直至其条件实际满足。

## 4. 版本冻结与预注册

- 每轮盲读前冻结：reader 协议（五键 flag_id/category/confidence/abstain/frame_box_pct + location_evidence 位置证据；度量仅取五键投影，location_evidence 供人工核对与裁定）、模型/提示词版本、度量版本、GT 集——**轮次开始后不得增删**。
- 若根据某批评测结果调整协议/度量/GT：**该批整体降级为 development 证据，不得冒充未见留出**。

## 5. 视角标注（process-v2 §3 细化）

- 自 r3 轮起盲读按视图分派（top/bottom 各一独立盲读），编排侧以 `flag_views` 注入 compare_v3（`view_check=full`）。
- 历史轮 not_applicable 保持原状（禁止把 not_applicable/partial 表述为已做视角检查）。

## 6. 命名约束重申（process-v2 §4）

- `seed_match_rate` 禁称 precision/FPR、禁作任何误报率结论；`reader_unmatched_ids` 语义=unmatched/unadjudicated，不得据此计算误报率。
- 框命中不构成电气事实（coverage_caveat v3 增补）。
"""


def _fail(msg: str) -> None:
    print(f"[s26-apr4] FAIL: {msg}")
    sys.exit(1)


def _write_if_absent_or_equal(path: Path, expected: bytes) -> str:
    """byte-exact 可重跑：已存在则逐字节校验一致（不一致 fail），否则落盘。

    返回文件 sha256（十六进制全串）。任何路径都**不覆写**既有字节。
    """
    if path.exists():
        actual = path.read_bytes()
        if actual != expected:
            _fail(f"{path.name} 已存在且字节与本次构造不一致"
                  f"（byte-exact 校验失败；不覆写）")
        print(f"[s26-apr4] 已存在且一致（不覆写）：{path.name}")
    else:
        path.write_bytes(expected)
        print(f"[s26-apr4] 新增落盘：{path.name}")
    return hashing.sha256_bytes(expected)


def _check_measured_values(run_v2: dict, run_v3: dict) -> None:
    """两轮实测先验值对盘复核（不符即中止——域 v3 如实转录磁盘事实）。"""
    for key, expected in MEASURED_RUN_V2.items():
        actual = run_v2.get(key)
        if actual != expected:
            _fail(f"run-v2 实测对账失败：{key} 盘上={actual!r} "
                  f"先验={expected!r}")
    report = run_v3.get("report") or {}
    if report.get("metric_version") != "calibration-metric-v3":
        _fail("run-v3-on-r2 metric_version 非 calibration-metric-v3")
    abstain_block = report.get("abstain") or {}
    actuals = {"gt_recall": report.get("gt_recall"),
               "seed_match_rate": report.get("seed_match_rate"),
               "abstain_rate": abstain_block.get("abstain_rate")}
    for key, expected in MEASURED_RUN_V3_R2.items():
        actual = actuals.get(key)
        if actual != expected:
            _fail(f"run-v3-on-r2 实测对账失败：{key} 盘上={actual!r} "
                  f"先验={expected!r}")


def main() -> None:
    # 0) 先验锚：被取代域状态文件（supersedes 对象完整性）
    v2_path = OUT_CAL / "calibration-domain-v2.json"
    if hashing.sha256_file(str(v2_path)) != FROZEN_DOMAIN_V2_SHA256:
        _fail("calibration-domain-v2.json 先验锚 hash 不符"
              "（文件漂移；fail-closed 中止）")

    # 1) evidence 磁盘实读（fail-closed）
    hashes, errors = approvals_r4.collect_evidence_hashes(str(REPO))
    if errors:
        _fail(f"evidence 磁盘实读缺失（fail-closed）：{errors}")

    # 2) 两轮实测数值对盘复核（先于域 v3 构造）
    run_v2 = json.loads((OUT_CAL / "calibration-run-v2.json")
                        .read_text(encoding="utf-8"))
    run_v3 = json.loads((OUT_CAL / "calibration-run-v3-on-r2-inputs.json")
                        .read_text(encoding="utf-8"))
    _check_measured_values(run_v2, run_v3)

    # 3) bundle（纯函数构造 + 门写扫描/链校验/checkpoint 复核）
    bundle = approvals_r4.build_approvals_bundle_r4(hashes)
    if bundle["ledger_verify"]["chain_errors"] \
            or bundle["ledger_verify"]["supersedes_errors"]:
        _fail(f"r4 账本校验失败：{bundle['ledger_verify']}")
    for scan_apr, scan in bundle["gate_write_scan"].items():
        if scan:
            _fail(f"{scan_apr} 门写扫描非空（不可落盘）")
    ckpt_errors = ledger.verify_against_checkpoint(
        bundle["ledger_entries"], bundle["ledger_checkpoint"])
    if ckpt_errors:
        _fail(f"checkpoint 复核失败：{ckpt_errors}")

    # 4) 评估协议 v1 字节实算（先于域 v3 构造绑定其 hash）
    protocol_bytes = EVALUATION_PROTOCOL_V1_MD.encode("utf-8")
    protocol_sha = hashing.sha256_bytes(protocol_bytes)

    # 5) 域状态 v3（纯函数构造；输入 v2 dict 零变异）
    domain_v2 = json.loads(v2_path.read_text(encoding="utf-8"))
    domain_v3 = approvals_r4.build_calibration_domain_v3(
        domain_v2, evidence_hashes=hashes, protocol_sha256=protocol_sha)
    # 门状态自证：构造内无任何置真路径（显式断言）
    if domain_v3["in_calibrated_range_current"] is not False:
        _fail("域 v3 in_calibrated_range_current 非 False（禁止）")
    if domain_v3["auto_triage"] != "blocked":
        _fail("域 v3 auto_triage 非 blocked（禁止）")
    if domain_v3["supersedes"]["sha256"] != hashes["domain_v2"]:
        _fail("域 v3 supersedes hash 与磁盘实读 v2 不符")

    # 6) 目标五件（byte-exact 可重跑；已存在则校验一致，不覆写）
    ledger_bytes = approvals_r4.ledger_file_bytes(bundle["ledger_entries"])
    if hashing.sha256_bytes(ledger_bytes) != bundle["ledger_file_sha256"]:
        _fail("decision-ledger-r4.jsonl 字节与 bundle 声明不符")
    rec = next(d for d in bundle["dispositions"]
               if d["disposition_id"] == "APR-0011")
    targets = [
        (OUT_APR / approvals_r4.disposition_filename(
            approvals_r4.APPROVAL_SPECS_R4[0]),
         hashing.canonical_json_bytes(rec)),
        (OUT_APR / "approvals-bundle-r4.json",
         hashing.canonical_json_bytes(bundle)),
        (OUT_APR / "decision-ledger-r4.jsonl", ledger_bytes),
        (OUT_CAL / "calibration-domain-v3.json",
         hashing.canonical_json_bytes(domain_v3)),
        (OUT_CAL / "evaluation-protocol-v1.md", protocol_bytes),
    ]
    written: dict = {}
    for path, expected in targets:
        written[path] = _write_if_absent_or_equal(path, expected)

    # 7) 落盘复读校验（账本链 + 域 v3 关键键）
    disk_entries = [json.loads(line) for line in
                    (OUT_APR / "decision-ledger-r4.jsonl")
                    .read_text(encoding="utf-8").splitlines()]
    if ledger.verify_chain(disk_entries) != [] or len(disk_entries) != 1:
        _fail("账本落盘复读校验失败")
    disk_v3 = json.loads((OUT_CAL / "calibration-domain-v3.json")
                         .read_text(encoding="utf-8"))
    if disk_v3["status"] != approvals_r4.DOMAIN_V3_STATUS \
            or disk_v3["in_calibrated_range_current"] is not False \
            or disk_v3["auto_triage"] != "blocked":
        _fail("域 v3 落盘复读校验失败")

    # 8) 收尾：打印新件 sha256 前 8 + 门状态
    print("[s26-apr4] --- 新件 sha256（前 8）---")
    for path in sorted(written):
        print(f"[s26-apr4]   {path.relative_to(REPO).as_posix()}: "
              f"{written[path][:8]}")
    print(f"[s26-apr4] ledger: {len(disk_entries)} entry | "
          f"checkpoint={bundle['ledger_checkpoint']['checkpoint_id']} | "
          f"head={bundle['ledger_checkpoint']['ledger_head_sha256'][:8]}…")
    print("[s26-apr4] APR-0011 登记完成（r4 批次；r1/r2/r3 字节不动）| "
          "门状态零翻转：in_calibrated_range_current=False、"
          "auto_triage=blocked")


if __name__ == "__main__":
    main()
