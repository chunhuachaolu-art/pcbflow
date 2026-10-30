# 校准评估协议 v1（evaluation-protocol-v1；纠偏词 P3-B 冻结）

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
