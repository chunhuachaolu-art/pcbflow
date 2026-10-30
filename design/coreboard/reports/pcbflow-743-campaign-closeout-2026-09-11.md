# 743 核心板"受控反馈解锁"战役收档（2026-09-11）

> 本文档是 2026-09-11 战役的唯一恢复入口。当日会话记忆锚：S41–S45
> （`~/.zcode/cli/memories/.../pcb-routing-workflow-architecture.md`）。
> 状态性质：`sealed`——所有决策已执行或如实否证，遗留项全部挂账待用户。

## 一、终态快照

| 项 | 开工 | 收档 |
|---|---|---|
| live 板 sha256 | `8029f5ff…` | **`dbfea089…`** |
| unconnected | 57 | **55**（3V3、GPIO_PE2 已落线） |
| violations（refill 权威口径） | 135 | **135**（零新增；norefill 口径 141=zone 重灌债） |
| severity-error | 10 | 10（零新增） |
| 测试套件 | 1989 passed | **2151 passed / 5F / 49E**（54 条 known-open=冻结件耦合锚，见 §四） |
| 受保护文件 | config=f515c348、toolchain=d43dad89 | 不变；cli.py=0a738047（copper-loop 改写，用户已裁决接纳） |
| 回滚锚 | — | `snapshots/live-apply2-pre/`（=8029f5ff，逐字节） |

## 二、当日决策与结果时间线

1. **四步计划**（用户批"反改上游"）：①WIN-1 13 条 UNKNOWN→13 张 verified UNSAT 证书（61 行表=8 SAT/53 UNSAT/0 UNKNOWN）；②FB-1 三臂 55/56/**60**/61（p3 代，解锁 ripup+③重放零新增 error）；③锚件/keepout 包条件不满足跳过；④LIVE-1 诚实零写入（live 5 网被他网铜墙堵）。
2. **A/B 线并行**：RIPUP-1（A，live 受控 ripup）0/6 诚实负结果；LIVE2B-S1 6 网全窗重解 6/6 verified UNSAT；LIVE2B-S2 **3V3 零拆线 SAT 收口**（搜索窗 margin 根因）+布局提案 0/5 负结果。
3. **APPLY-1**（用户批"1，2 全落"）：**首次真实 live 落线**——3V3（44 段）+GPIO_PE2（66 段+3 埋孔），DRC 三读数 135/57→10 err(new=0)→**135/55**。
4. **DESIGN-1**（用户批"3 走设计级"）：29 候选=4 SAT/22 UNKNOWN/3 UNSAT；GNDA/FMC_SDNE0 口袋墙剥除 SAT（条件式）；U1 平移被 UNSAT 否证；端点三网死路。
5. **VERIFY-1**（用户批"1 前置验证"）：**两个条件 SAT 双双否证**（VDDA 再入口孔与 witness 孔同点=坐标级互斥；FMC 义务 4/7）；副产品=**引擎缺陷立案：route_one 假闭合**（ETH_REF_CLK，端点落异层铜）。
6. **JUMPER-1**（用户批"飞线+跳线设计"）：**跳线否证**——0Ω 旁路只破端点自锁，破不了异网铜连续墙（LTDC_VSYNC/VBAT 真实形态）；**SWDIO 飞线工单交付**：J4.13 (2.63,26.11) ↔ U1.124 (47.675,16.15)，AWG30 60±5mm。
7. **MAINT-1**（用户批"接纳 copper-loop+pin 现刷"）：35 条锚已刷新（17 copper→0a738047+18 板态 pin→dbfea089 实测），copper-loop 三模块接纳入账（157 自测全过）；54 条 known-open 见 §四。

## 三、剩余 5 行断点的最终状态矩阵

| 行 | 网 | 状态 | 证据指针 |
|---|---|---|---|
| RPL-019 | 3V3 | **已关闭（落线）** | out/coreboard-apply1/ |
| RPL-043 | GPIO_PE2 | **已关闭（落线）** | out/coreboard-apply1/ |
| RPL-054 | SWDIO | **飞线工单就绪**（装配执行） | out/coreboard-jumper1/evidence/jumper1-results.json |
| RPL-039/RPL-038 | GNDA/FMC_SDNE0 | 条件 SAT 已否证；**联合重解线索在案**（witness 出口+VDDA 逃逸坐标级） | out/coreboard-verify1/ |
| RPL-052/RPL-056 | LTDC_VSYNC/VBAT | **墙级死路**（路由/端点/跳线三路证书级否证）→ waive 或下版修订 | out/coreboard-live2b-s1/+verify1/+jumper1/ |

## 四、挂账清单（全部待用户拍板，无一在途）

1. **GNDA/FMC_SDNE0 联合重解战役**——剩余 5 行中唯一可能再收 2 行的路，成败未知。
2. **LTDC_VSYNC/VBAT waive 拍板**（LTDC_VSYNC=LCD 时序失效，建议下版加跳线位；VBAT=馈针无效、板内域经 R9.2-CRTC.1 连通）。
3. **54 条冻结耦合锚重注册工作包**——钉冻结 out/ 历史件（r24/r25/holdout/cas/fd 等嵌旧板态 8029f5ff 或旧 cli hash），防覆写护栏属设计行为；批准后套件才能完全回绿。
4. **zone 重灌**（制造前必须；norefill 口径 +6 违规已备案，`--refill-zones --save-board` 或 KiCad 手工）。
5. **route_one 假闭合引擎缺陷修复**（pcbagent 端点盲点，ETH_REF_CLK 案例）。
6. copper-loop 深度代码审查（可选；接纳登记已完成）。

## 五、产物索引（供仓库整理）

**out/coreboard-*（合计约 610MB）**：win1 269M（板级证书运行，可再生）/ live2b-s1 186M（同） / verify1 46M / live2b-s2 36M（workspace/scratch 23MB 内存板副本可重建）/ design1 21M / fb1 17M / ripup1 15M / jumper1 8.0M / apply1 7.6M / pa1 7.8M / live-apply1 3.0M / maint1 132K。
**新代码**（tools/pcbflow/pcbflow/）：win1_window / fb1_experiment / live2s1_experiment / live2s2_proposal / ripup1_campaign / design1_proposal + scripts/（win1_run、fb1_arm_orchestrate、live2s1_run、live2s2_run、design1_run、ripup1_orchestrate、apply1_orchestrate、jumper1_orchestrate、v1_orchestrate）。
**新测试**：test_win1_window / test_fb1_*×3 / test_live2s1_pure / test_live2s2_proposal / test_ripup1_campaign / test_design1_proposal / test_verify1_campaign / test_jumper1_batch / test_apply1_batch（均已入套件）。
**报告**（design/coreboard/reports/）：pcbflow-vs-headless-comparison、pcbflow-live-apply1、pcbflow-live-ripup1、pcbflow-live-apply2、pcbflow-design1、pcbflow-jumper1、pcbflow-maint1（均 2026-09-10/11，配 JSON）。
**非本战役并行产物**：out/copper-loop-r1-*×5 目录 + pcbflow/copper_loop|copper_model|copper_patch.py（外来工作流，已接纳登记，深审未做）。

## 五-2、整理仓库提示

- `workspace/scratch/`、`workspace/staging/`、`drc-input/` 均为可再生 staging 内容，可整体删除（结论已全部落 REPORT/results JSON）。
- 各 out 目录的权威结论文件：`*-results.json` / `three-arm-summary.json` / `REPORT.md` / `run-manifest.json`——保留这些即可恢复证据链，其余副本类可瘦身。
- 冻结历史 out/（revc-*、v3-*）**不可移动/改名**——54 条 known-open 测试与冻结件 hash 绑定，移动前先做 §四-3 重注册。

（完）
