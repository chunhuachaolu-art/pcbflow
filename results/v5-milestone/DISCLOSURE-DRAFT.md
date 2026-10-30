# PCBFLOW V5 发布披露档（草案）· DISCLOSURE-DRAFT

- 批次：PCBFLOW-V5-EVIDENCE-R1（C5）；生成 2026-10-19；阶段=draft-1（两段式第一段=内部定格版草案；不 tag 不外发）。
- 口径：M0 批复原文从 exec-release-review/DISPATCH-LOG.md「M0 批复登记」节机读逐字嵌入（不改写裁决语义）；一切数值自正本机读注入；窄域主张零外推。

---

## 0. G3 结构性豁免（置顶·M0 批复原文）

V5.0 立项验收门「≥5 板 DRC-clean」数字上差 1 且属**结构性**——R1 世界 SAT 恰 4 板、可布域 4/4 全净、差口不指向任何脏板。用户已于 2026-10-17 深夜 M0 批复裁=**案 C 结构性豁免**；立项目标按「未达-结构性」口径定格。批复原文（机读逐字，不得改写）：

> ## M0 批复登记｜2026-10-17 深夜｜用户四项文字批复=定义门闭合
> 
> - 用户批复原话：「1, 2, 3,按推荐来，4采纳」（对主审深夜文字清单四项；AENG E1 弹窗未答后转文字清单，未重发）。
> - **①AENG E1（帽-对象）=案 a**：重裁 per-run 帽至授权带 ≥40373.051s、跑 A:orig 单组双跑（恰 2 跑；双跑×2 任何帽下不可行=R1 E2 一并收窄）。→ **EXEC-AENG-R2 立即派发**（per-run 实取 43200s=授权带内技术定值、超最坏观测 40373.051s 留 ~7% 余量；批帽 86400s 维持恰容单组双跑 93.5%）；里程碑链 C2 恢复在飞。
> - **②G3=案 C 结构性豁免**：≥5 板门原文不动；「R1 世界 SAT 恰 4 板、可布域 4/4 全净、差口不指向任何脏板=结构性」入披露档置顶+manifest 门读数面板；立项目标按「未达-结构性」口径定格。→ **M2 板面门即闭合**（裁决落册=本节）；C4 清面。案 B（扩板集）作后续批候选登记、不阻断本里程碑（C+B 组合之 B 侧另裁另排）。
> - **③发布形态=案三两段式**：先形态一（内部定格收口叙事+route-v5 本仓 annotated tag+workspace 证据仓 tag+发布件全套，零外发零 push）；公开前置件四件（D-5 GPL 依赖审计／引擎外泄解禁裁决／语料板源许可审计／holdout 红线处置）并行清障；公开时点另行裁决。→ C8 第一段定形、公开段待前置件批。
> - **④sign-off 前置链 C1..C9 采纳**：L1 里程碑／L2 production／L3 judge 三层分离口径生效；C4/C8 两点已随本批答复（②③）；C9 签署面=「M1..M5 全绿+披露档定稿」（设计件建议口径，签署时仍呈裁）。
> - **M0 定义门=闭合**。链序推进：C1（PYFIX-R1 在飞）∥C2（AENG-R2 本夜派发）∥C3（R9-E4 在飞）→C5（证据包执行批，待三批收口后立）∥C7（状态同步小批，可并入 C5 批）→C6（治理提交面呈裁，PYFIX 收口后）→C8 第一段（tag+发布件）→C9（sign-off 签署呈裁）。
> - 裁决正本=本节（用户原话逐字+四项映射）；设计件正本（sha256=b364732c…a7ba4）§2.2/§3/§5 建议面与本批复一致（②=建议 C／③=建议三／④=建议采纳）。

### 三锚引据（机读行文）

1. **立项验收门原文**（route-v5 `V5.0-DEV-TASKBOOK-2026-09-13.md` :13）：
   > 把「提案权归模型、度量权归引擎」落成一条可跑的端到端管线：**模型只在排序/分配/层计划这类求解器自己不会动的自由度上给序数提案；引擎做全部几何、容量、宽度先验与成本计算，对提案逐一测量后终选**。验收=真实语料 **holdout 板**上同时过**成功率门**（≥5 板 DRC-clean）与**失败证据门**（全部失败附合规失败证书）；证书解释失败、**不折算成功率**。每个模型介入点有可审计证据链。
2. **DIAG 台账**（`PCBFLOW-OPTI-PKG-DIAG-R1-2026-10-07.md` :939）：
   > | **V5.0（R 仓主线）** | 「提案权归模型、度量权归引擎」端到端管线；验收=holdout 板同时过成功率门（≥5 板 DRC-clean）+失败证据门（R:`V5.0-DEV-TASKBOOK-2026-09-13.md`:11-13） | P0–P5 全收口（D8 世界换版后五门首次满 PASS，R:`DISPATCH-LOG.md`:961-963）；R1 重定基 B 版主值 **SAT 4/4**（R:`DISPATCH-LOG.md`:2826-2831）；executor 0.10.0 | **成功率门「≥5 板 DRC-clean」未达且属结构性**：R1 世界 SAT 恰 4 板，判据二干净板 4<5（R:`DISPATCH-LOG.md`:2788, :2830）——立项目标数字上仍差 1 |
   （:1024-1031 七裁+bme280 裁(c) 节：主值 4/4、处置名册 10 板、差口不再指向任何脏板；git 证物=dispositions-r1-2026-09-28.json/R1-SCOREBOARD-REBASE-2026-09-28B。）
3. **FINAL-ROADMAP**（`FINAL-ROADMAP-2026-10-08.md` :308）：
   > | V5.0 主线 | holdout 至少 5 板 DRC-clean，并有失败证据门。 | R1 记分牌主值可布域 SAT 4/4，六板并记 4/6；S5 分母闭合 PASS。 | 按 ≥5 板目标，当前主值少 1 板；且成功率必须绑定 world/board/hash。 | **值得补**：OPT-01、04、05、07、08、09、10；先解决版本漂移和搜索面，不能直接补数字。 |
4. **MECH-VERIFY 重算**（`MECH-VERIFY-REPORT.md` :97）：
   > | R1 判据二干净板（微段豁免后） | 4/5 | 4/5 | OK |

manifest 门读数面板登记口径：判据一 4/5（并记 4/4 主值/4/6 六板全量）、判据二干净板 4/5、可布域 4/4——数字门未达=结构性，非缺陷；案 B（扩板集）作后续批候选登记、不阻断本里程碑（C+B 组合之 B 侧另裁另排）。

---

## 1. G8 · OPT-15=UNCLOSED（E4 终读更新口径）

台账行（正本 §2 机读）：

> | G8 | OPT-15 状态=UNCLOSED（VERDICT published 是 E2C 交付态而非项级闭合；E3 J1 正结果指向术后校正器、E4 在飞）——发布叙事不得声称传导矩阵收益闭合 | R9-E2C VERDICT（UNCLOSED 明文）+R9-E3 收口节红线 | S2 | 发布披露按 UNCLOSED 口径；R9-E4 收口后按其 verdict 更新 | R9-E4 |

R9-E4（2026-10-17/19 收口）终读，机读 JSON 注入：

- **J1 机制复现=TRUE**：PASS (arm k8: final<=10 AND d_rows=-13<=+20 AND failed=0/ok=16; E3 arm-6 form value-identical)
- **J2 C 板无害=FAIL（负结果合法收档）**：FAIL (branch B revert: rows 137->31 fixed BUT final 1->4 degraded; negative archived)
- J3 自动提取一致性：PASS reading: D_hat_k8 == E3 manual D_reg, Jaccard=1.0 (6/6 hits); k4 prefix Jaccard=0.4
- J5 负结果收档：触发（由 J2）；机理定位+v1 修正方向挂账
- 无害性边界（机理登记）：pure engine-rows regression on a no-hard-regression board must NOT trigger revert (pipeline face degrades); activation gate must require failed(L)>0 or pipeline-face re-verification with rollback
- 预算敏感负结果：K=4 partial set degrades rows (+118 vs L); B-board probe floor = full routed candidate coverage (8)
- 盲对照：disp-top-6 also passes J1 conjunction on B (multi-exit regression basin); extraction specificity evidenced by J3 device-level match and k4 degradation, not by J1 alone
- **v1 修正方向挂账**（待批，不在本批）：①激活门收紧为 failed(L)>0（硬回归限定）；②回植后管线面复验（final/s1 不劣化才接受，否则回滚）。
- **UNCLOSED 不外推红线维持**：E2C VERDICT published 是交付态非项级闭合；E3「不作全局外推」；E4 负结果进一步划定边界（校正目标面必须含管线面）。发布叙事**不得声称传导矩阵收益闭合**。

---

## 2. G11 · OPT-14 未立项口径

台账行（正本 §2 机读）：

> | G11 | OPT-14 缓立（GUIDE 证书触发化未立；failcert n=2 证据薄） | 用户 10-16 裁③；R6 收口 fail_n=0 维持 n=2 | S3 | 维持缓立攒证据；发布叙事按「未立项」口径 | — |

披露口径：**未立项（缓立维持）**——GUIDE 证书触发化未立项；failcert 证据薄（n=2：R5-C bme280 n=2+R6 fail_n=0）；用户 2026-10-16 裁③维持缓立。发布叙事不得把 OPT-14 计入已闭合或进行中工程面。

---

## 3. G12 · OPT-17 partial 口径

台账行（正本 §2 机读）：

> | G12 | OPT-17 v1/partial：canonical score schema 旧报告全量迁移出批未做、不得标全闭合 | R4 GATE-G1 R4C-04 裁定原文 | S3 | 后续批或按发布范围明示 partial 口径 | — |

披露口径：**只收 v1/partial**——canonical score schema 旧报告全量迁移出批未做（R4 GATE-G1 R4C-04 裁定原文：「未完成不得标全 OPT-17 闭合」）。发布叙事按 partial 口径，不得标全闭合。


---

## 4. G13 · OPT-04/09/10 残留刀口逐项

台账行（正本 §2 机读）：

> | G13 | OPT-04/09/10 残留刀口：第三刀逐案差异数据面／真实板停线路径未验证跑触发／zone-keepout 接通未做——窄域主张不受阻断但不得外推 | R2/R3 残留清单（state 档案各批残留节） | S3 | 留案；发布范围若触及相关主张须逐项披露边界 | — |

逐项披露（发布范围触及处）：

1. **OPT-04 第三刀**：逐案差异数据面未做（第一刀 R2+第二刀 R3 已落地，残留登记）——对「逐案差异」的任何主张不得外推到未做面。
2. **OPT-09 真实板停线路径**：未验证跑触发——「停线路径」主张限锚点登记面，真实板触发面未验证。
3. **OPT-10 zone-keepout 接通**：未做——zone-keepout 相关能力主张零外推。

窄域主张不受阻断，但上述三刀口的边界必须随相关主张逐项披露。

---

## 5. 窄域主张零外推措辞清单（发布叙事措辞纪律）

| 主张面 | 允许的窄域措辞 | 禁止的外推 |
|---|---|---|
| OPT-08 有效性 | 「合格板 1/17（R8-E2C 窄域诚实答案）」 | 推广到板池其余 16 板或任意未测板 |
| OPT-15 传导矩阵 | 「机制复现 TRUE（B 板端到端）+C 板无害性负结果；UNCLOSED」 | 「传导矩阵收益已闭合/已验证有效」 |
| OPT-12 judge 线 | 「qualified（R7-E3 五门 all_passed=true）但 judge 线 sign-off=false 维持」 | 「judge 线已签核/已转正为签核态」 |
| OPT-17 评分迁移 | 「v1/partial」 | 「评分面全量迁移完成」 |
| OPT-04/09/10 | 「残留刀口逐项披露（§4）」 | 把残留面并入已闭合叙事 |
| R2 可布域 6/6 | 「09-23 旧引擎世代历史对照（OPT-01 纪律）」 | 挪用为现状读数或补数依据 |
| 布局线 LAYOUT/A6 | 「保留续开登记（USER-RULINGS-2026-10-06:117-118）」 | 宣称布局线已收口 |

---

## 6. production sign-off 永久分离段（L2）

milestone sign-off（L1，链 C1..C9）与 production sign-off（L2）**永久分离**——L2=外部 SI/PI/热/EMC/DFM+板厂叠层+实物 bring-up（V2 层次二线从未启动面），**永不折入本里程碑**；manifest sign-off 面板按 false+原因披露（W `tools/pcbflow/STATUS.md`:9/:34 实测锚：`| Rev-C 主轨（⓪–⑥ 编译器闭环） | **DONE**（2026-08-30；production_signoff_ready=false 维持——外部 SI/PI/热/EMC/DFM 与板厂叠层未接） | `NEXT.md`、`…`）。L3 工具线（judge）已随 R7-E3 qualified 但 sign-off=false 维持，按线披露不进链。

