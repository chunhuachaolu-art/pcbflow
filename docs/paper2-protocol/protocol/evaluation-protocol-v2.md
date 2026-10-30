# 校准评估协议 v2（evaluation-protocol-v2；独立 holdout 评估协议冻结件）

- protocol_id: evaluation-protocol-v2
- version: v2
- status: frozen（自本文件落盘起冻结；修订=新版本文件，不回写本件）
- declared_date（人工声明常量，非机器 wall-clock）: 2026-09-10
- 域: TL-2 Critic 质量独立评估（APR-0008 线；治理血统=evaluation-protocol-v1）
- 批准依据: 用户 2026-09-10 指令「按 V3-RECOMMENDATIONS-2026-09-09.md 继续之后的工作」；该文档 §7 最终建议原文：「完成 R20 close，随后冻结评估协议并准备独立 holdout」。R20 close 已于 2026-09-09/10 完成（calibration-run-r20.json=6573a59a、round20-dev-record.json=80e3e9e2 在盘），本件执行其后续项（§6 交付顺序「R20 close → 冻结 holdout 协议」）。

## 0. 承继与取代关系（supersedes）

1. **v2 只治理未来的独立 holdout 评估**（frozen holdout 域的评估协议）；本件不追溯、不改写任何既往轮次证据。
2. **v1 原文零字节保留**（evaluation-protocol-v1.md，sha256 22dc7337bb0774bf3bab6be86879d2bae46f62a624ed5d438f123201b11e798e，实测在盘）：v1 继续承载 R1–R22 历史口径（三集分域/独立裁定/联合评价/预注册降级/按视图盲读）；对 v1 冻结产物零回写。
3. **v1.1 多实例聚合口径与 v1.2 工具行为规约被 v2 继承**：多实例协议（n=3 实例×视角、实例主记录+视角层三分列聚合，r11 确立）与工具行为规约（判读只允许以 Read 工具查看原图、禁止对图像做任何程序化处理，r11–r22 十轮沿用）作为 v2 下 holdout 评估的执行口径原样继承，不另立新版本。
4. v2 与 v1 的分工：development/calibration 域的轮次评估继续按 v1 口径在案执行（含 v1 §4 预注册降级纪律）；凡进入 frozen holdout 域的评估，一律按本件 P2 九条执行。

## 1. P2 九条规范条款（独立 holdout 评估的强制条款）

以下九条为 frozen holdout 评估的强制规范条款，逐条编号冻结；任一不满足的 holdout 结果不得作为独立质量证据入账。

- **P2-1（三集按板隔离）** development、calibration、frozen holdout 三集按板或项目组隔离：holdout 板自入库起 designation=holdout-candidate，不得进入任何 development 迭代轮的渲染/盲读/指引调整；来源：V3-RECOMMENDATIONS-2026-09-09.md §3 P2。
- **P2-2（reader 盲读）** reader 只看渲染输入，不看 GT：任何 GT 坐标/类别提示/期望缺陷描述/诊断报告内容不得进入 reader 上下文；来源：V3-RECOMMENDATIONS-2026-09-09.md §3 P2。
- **P2-3（一对一匹配）** reader-to-GT 一对一匹配：每条 reader 旗标至多匹配一条 GT、每条 GT 至多被一条旗标匹配；来源：V3-RECOMMENDATIONS-2026-09-09.md §3 P2。
- **P2-4（重复旗标单列）** 重复旗标单列，不重复计入 precision：同板同位置的多实例/多视角重复观察按联合评价处理，不得当作独立样本累计；来源：V3-RECOMMENDATIONS-2026-09-09.md §3 P2。
- **P2-5（三分口径）** `unmatched`（无 GT 对应）、`unadjudicated`（尚无人工裁定）与真实 false positive（经裁定确认为误报）三分分开登记，未经裁定不得计入任何一侧；来源：V3-RECOMMENDATIONS-2026-09-09.md §3 P2。
- **P2-6（指标分列）** precision、recall、FPR、FNR、abstain、confidence calibration 分开计算与报告，不得合并为单一分数；来源：V3-RECOMMENDATIONS-2026-09-09.md §3 P2。
- **P2-7（逐旗标人工裁定）** 至少一部分结果有逐旗标人工裁定（正例/负例/难例+类别覆盖）；无裁定的旗标保持 pending（v1 §2 独立裁定要求延续）；来源：V3-RECOMMENDATIONS-2026-09-09.md §3 P2。
- **P2-8（阈值不晋升）** 不因满足暂定阈值就自动晋升模型：暂定阈值达标（development 评估线）不构成翻转正式谓词的充分条件；来源：V3-RECOMMENDATIONS-2026-09-09.md §3 P2。
- **P2-9（缺证即 blocked）** 任何缺 hash、stale、执行记录、独立 DRC 或有效配对的候选必须 blocked；来源：V3-RECOMMENDATIONS-2026-09-09.md §5（治理红线，本条经本协议并入九条款清单；§3 P2 原列八条，第九条为红线并入条款——装配事实如实登记）。

## 2. holdout 一次性纪律（继承，不改动）

1. 纪律源=HOLDOUT-PLAN.md（out/v3-tl2/holdout/HOLDOUT-PLAN.md，sha256 a4b80193ac9c15cb0ecba0208737a0adea343e5e3990b4d730141c56d2ed33a9，实测在盘）：候选板自该文件落盘起 designation=holdout-candidate；**正式 holdout 运行前，任何盲读、任何指引/协议迭代不得接触其渲染件**；渲染只在正式运行时做（冻结渲染管线一次成型）。
2. 用途边界照旧继承：外部语料只评弃权率/旗标产量稳定性，零 GT 主张；正式 holdout 报告不得出现 GT recall 字样（N/A+纪律引用）。
3. **运行时机=用户判断的独立人工点**：v2 冻结不构成启动指令；建议触发条件（开发线收敛后）照 HOLDOUT-PLAN.md 原文，由用户拍板。

## 3. 现状登记（R17–R22 收口实测，fail-closed 装载）

1. **r19（marginal）**：字母裁决=marginal（round19-dev-record.json=0e2fdd69 在盘）；M 四元组=(0.461538, 0.571429, 4, 0.211111)。
2. **r20（reject，G1 分岔）**：字母裁决=reject（calibration-run-r20.json=6573a59a、round20-dev-record.json=80e3e9e2 在盘）；M1=0.636364；守门 G1（bottom courtyard 非弃权 0/0/0 维持）字面破坏（实测 2/0/0，触发旗 R20B-003/R20B-006）经 reject_guards 支命中，而触发源=负责任报告（(iii-a) 间隙支）——条款按设计工作与预注册字母的字面冲突同时显形（g1_bifurcation_record 单列，字母不改写）。
3. **按 RECOMMENDATIONS §3 P1 表的处置（R20=reject 行）**：「reject → 停止同一调参轴，保留负向证据」；R21 全组合**不做**（round20-dev-record 已登记「R21 不做」；axis-experiment-plan-r17-r20.json=b6ec6467 冻结件预留的 R21 条件位因 early_stop 未触发永久留空；r22 跳号与其无涉）。r20 的 G1 破坏同时落在「同一调参轴（组合指引轴）停止」的处置范围——G1 破坏源即该组合指引的 (iii-a) 间隙支。
4. **r22（regressed，G2 分岔，M1 带内复现）**：同指引重复轮（收敛归因）；字母裁决=regressed（calibration-run-r22.json=80a12c05、round22-dev-record.json=b4b8fbe9 在盘）；M 四元组=(0.390244, 0.2, 4, 0.104545)，M1=0.390244（16/41）落复制带 [0.361538, 0.561538]（r19±0.10）内=带内复现；守门 G2（top 几何门面积比出局条目）R19=0→R22=2 破坏经 regressed_guards 支命中——字母=regressed（唯一正式裁决）与 M1 带内复制事实两账分列（g2_bifurcation_record 单列）；G2 出局条目指针：R22T-002（area_ratio=16.406371）、R22T-013（area_ratio=16.369542），逐条摘录在 round22-dev-record.json g2_bifurcation_record.rejected_entries_excerpt。
5. **胜出配置的双账定性（guidance-r19）**：三轴实验收束=收益最大配置=轴3 单变量（observation-guidance-r19.md=8633bda5，M1=0.461538 历史最佳、r16 基线 0.771429）；其归因状态=「M1 量级在新鲜实例群复现（r22 带内，机制方向支持）但守门字面降级（r22 预注册字母=regressed）」——两账并列、不合并、不改写；「胜出」仅此描述性定性，不构成采纳、不构成晋升。
6. 下一候选三选项已如实单列（round22-dev-record.json next_candidate_suggestion，由用户拍板、不预写决策）：(a) 接受发展域现状收束训练环、留出集时机由用户判断；(b) 对 G2 的 2 条出局条目做机制归因（须新预注册轮）；(c) 再一轮同指引重复轮（三样本，须预注册）。

## 4. 边界声明（v2 不改变的事项）

1. **TL 门零改动**：TL-0–TL-6 各门定义与通过状态不被本件触碰。
2. **APR-0011 零改动**：暂时采纳基线（gt_recall≥0.75、seed_match_rate≥0.5、abstain_rate≤0.5、连续 2 轮、GT≥12）保持 provisional_supersedable 原文，阈值零改动。
3. **in_calibrated_range 恒 False**：直到正式采纳（须人工批准），任何轮次/评估不得写 True。
4. **自动分流恒 blocked**：BL-4+TD5 分诊合取约束仍在；暂定阈值达标（P2-8）不翻转。
5. **v2 生效≠holdout 启动**：本件冻结只建立「未来独立 holdout 评估按什么规则评」；是否启动、何时启动=独立的人工决策点（§2.3）。
6. **V4-SVG 属独立路线**：per V3-RECOMMENDATIONS-2026-09-09.md §3 P4，V4.0-SVG 以新版本、新 schema、新实验目录进入开发（v4exp 外部工作流已在盘登记：pcbflow/v4exp 模块与 out/v4-experiment 实验产物在案），不修改 V3 门定义、不写入 V3 历史产物、非本协议对象。
7. 「GT≥12、覆盖≥3 类、连续两轮达标」保留为 development 评估线，不是单独翻转正式谓词的充分条件（RECOMMENDATIONS §3 P2 原文）。

## 5. 与 §5 治理红线的对齐声明

本件与 V3-RECOMMENDATIONS-2026-09-09.md §5 全部红线对齐：不覆盖历史 JSON、校准轮、状态摘要和冻结 render manifest（v1 原文零字节保留即其执行）；不修改已批准 schema、TL 门、waiver 或生产条件来换取 pass（§4.1/4.2）；不把视觉结果写成 DRC/solver/physics/生产结论（§4.6）；缺 hash/stale/配对不完整候选 blocked（P2-9）；新增核心产物保持 canonical、可重放、无 wall-clock 和主机路径，运行元数据与核心事实分离（登记件=s79 纯函数+canonical JSON 生成，日期=声明常量 2026-09-10）。

（完）
