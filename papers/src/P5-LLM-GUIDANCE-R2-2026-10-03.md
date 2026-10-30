# 篇五《提案权归模型、度量权归引擎——LLM 导引布线的合成域正结果与真实板零终解增量》R2 定稿

<div class="release-note">

**发布说明（2026-10-30 收线归档）**：本文是 pcbflow 项目的中文技术报告（R2 内部定稿），**未经同行评审，未投稿**。文中形如 `<ENGINE_ROOT>/out/...`、`<WORKSPACE>/...` 的证据路径指向作者本机的实验证据目录，这部分没有公开；代码与核心板设计见仓库 `engine/`、`tools/`、`design/`。"主审""席位"等术语见 `TERMINOLOGY.md`。作者：赵丹琪。许可：CC BY 4.0。

</div>

---

## 摘要

LLM 参与组合优化求解器的工程问题，不是「能不能提提案」，而是「提案权应放在哪、度量权应放在哪、提案的价值落在哪个自由度上」。本文在 PCB 布线域给出一条完整的两极证据链：**架构原则**（提案权归模型、度量权归引擎；裁决价值必须落在求解器自己不动的自由度——排序/分配/层计划；基线臂恒在）＋**合成域正结果链**（五实验：多轮探针导引 4/5 oracle、档位/波次双 viable 各 5/5、n8 全枚举证明探针所得 474.5 为真全局最优并证伪模拟退火下界、四层板档位通道天花板=全序逐值相等 9/9 且模型 4/4 命中含一例反超全序臂、波次缩放 7/8 场景闭环 1.0）＋**真实板负结果链**（三批一致：多轮机制真实激活——轮级提升 9/24 与 9/18 全在 FAILED 域、FAILED 域 A/B 通道区分度 3/4、唯一提升轮恰为 tier 轮——但**终解增量三批全零**：③==② canonical 字节等，会话波 14/14、RESTORE 14/14、SUPPLEMENT 7/7；候选回声率 0.96）。结论的双面性是本文核心交付：**导引通道在合成域的价值真实且有机制（探针环：28 发→13 informative→5 优于主序→2 兑现）；在真实板上，A4 终选兜底使任何轮内搜索增益都无法穿透到终解**——价值若存在，在「探针环轮内增益×A4 终选」的接缝处，而不在「多轮迭代」本身。据此席位 B 维持 shadow advisory（D002 终局）。方法学交付：天花板判前枚举（通道表达力在判读前钉死）、过渡带人口验收三条件（基线 SAT＋headroom≥2.0＋30 条种子随机序 SAT 率∈[0.10,0.90]）、token 双轨护栏。

**关键词**：LLM 导引；PCB 布线；提案-度量分权；消融实验；预注册；负结果

---

## 1 Introduction

自动布线引擎的解质量对「求解器自己不主动搜索的自由度」敏感——网布线顺序（排序）、批次划分（波次）、层分配（层计划）。这些自由度恰好是 LLM 可以提案、引擎可以廉价度量的接口。本项目（pcbflow V5）围绕一个架构问题做了一组连续受控实验（架构前提＝五条收敛共识，2026-09-13 定调；五实验与席位 B 三批在 2026-09-16~23 连续窗口内执行收口）：**把提案权交给模型、度量权留给引擎，能走多远？**

答案分两极，且两极都是本文的交付：

- **合成域（结构可推理的小板）**：走得很远。多轮探针导引 4/5 oracle；粗粒度通道（档位/波次）双 viable 各 5/5；探针发现的 474.5 被 n8 全枚举（40,320 排列）证明为真全局最优，同时证伪了模拟退火的「下界」宣称；四层板上档位通道天花板与全序逐值相等 9/9、模型 TIER 臂 4/4 全 oracle 命中（cceil=1.0），其中 fc-06 一例反超全序臂（266 vs 272）；网数放大到 n=16 时波次通道 7/8 场景闭环 1.0。
- **真实板**：走不到终解。三批（单轮会话波 14 板、多轮恢复批 24 轮、补充批 18 轮）一致显示：多轮机制真实激活（轮级提升、FAILED 域区分度、tier 轮效应），但**终解增量全零**——③==② canonical 字节等，A4 终选把轮内一切增益兜底回基线。

三个研究问题：RQ1 导引通道在合成域的价值与机制是什么；RQ2 真实板上终解为何零增量；RQ3 席位 B 的正确形态是什么。

本篇与篇六构成**席位范式的两极**：本篇「提案权归模型、度量权归引擎」（模型只提案、引擎度量与终选）；篇六「直接操作席位」（模型亲手逐动作构造几何、验证器逐动作裁决）。两极对照的合流结论互为前提——本篇的零终解增量负结果（§5）与篇六的「可完成工作但有硬天花板」正结果（篇六 §9–§10）共同给出席位范式完整地图，引用请并读。

## 2 架构原则与前置负结果

### 2.1 五条收敛共识（架构前提，2026-09-13 定调）

1. **裁决价值必须落在求解器自己不动的自由度**（排序/分配/层计划）——它是 V4.2 线「删除-回填零改进定理」的直接推论：V4.2 r1/r2 双双机判登记 `no_capturable_value_at_current_stack`（模型直接掌选择权时，r1 M2 拥挤域配对净收益 **−2.754%**（0 胜/2 平/6 负，p=0.031）、M3 +0.0%；r2 会话驱动形态 M2′ 处理臂 objective 平均劣化 **2.375%**、M3′ 空提案全域 0% 增益，S-M2′ 再触发同判）——模型插手求解器已在搜索的自由度是净损失。
2. **符号规则层≠固定解**：三层拆分=不变量地板（电流-宽度/clearance/回流物理，不可让渡）＋软先验（可被模型覆写，经校准域门授权）＋验证器（只当裁判产出测量不当选手）。
3. **模型权重三分**：覆盖面＋提案权拉满、选择权归测量（基线臂恒在对照组）。
4. **硬约束**：harness-only（席位=无工具纯会话数据内嵌）、支出门。
5. 宽度先验=电流→保守最小值＋容量饱和（协商区间），校准骨架语料配对行=0 须先物化。

### 2.2 前置负结果：SEAT-AB-R1a（16 场景，v4cmp cal 域）

席位可行性预判（37 块真实语料板无 solve 接线，先用 cal 场景）：H1=`not_captured`（movable 集 5 场景中位 oracle 命中 **0/5**，G1 附注 with_regression，cal-f4-14 +3.9%）；H2 GLM=`iteration_value`（S3 增益 2/5、零丢失）——**唯一正信号=迭代形态**；H2 DSF=iteration_inconclusive（S4 全坚持基线）。单发两模型均 0/5，反馈迭代仅 GLM/f4 族局部信号；不能支持独立排序席位结论。该负主判决按任务书回填 V5.0（席位 B 默认 shadow advisory），并直接催生 GUIDE 线：把 R1a 唯一正信号（迭代）走到底。

## 3 导引通道定义（五通道）

模型可提案的通道与引擎侧支撑（v4exp `solve_board` 原生支持逐网层硬约束与走廊途经点——层计划/走廊类通道零引擎改动）：

| 通道 | 粒度 | 内容 | 状态 |
|---|---|---|---|
| 全序 | 细 | 每网完整排序 | 天花板参照 |
| 档位（TIER） | 粗 | 网分档（如时钟/电源/信号）＋档间序 | 主选（n≤12） |
| 波次（WAVE） | 粗 | 有序块（≤3 块）分区布线 | 大 n 主选候选 |
| 层计划 | 中 | 逐网层偏好 | 已关闭（见 §4.4） |
| 探针环 | 元 | 模型点名候选排列→引擎代测→回传实测值再决策 | 跨通道叠加件 |

## 4 合成域五实验（正结果链）

### 4.1 PILOT-R1：多轮探针导引 4/5 oracle

人口=R1a movable 5 场景；GUIDE-1×1（全序引导）＋GUIDE-2×5（单场景＋每轮 ≤3 探针引擎代测）；预注册冻结先于模型会话（sha16 `00c23809998e79b4`，本批重算一致）。**终判 pilot_positive**：G2 探针臂 **4/5 oracle 最优**（f2-15 235.5/f4-16 167.5/f4-13 126.0/f4-15 133.5）＋f2-13 295.0（收掉剩余 gap 50%，压线过冻结门 ≤295.0）；G1 纯序引导一次修复后全程静止（f2-15 停 246.0 看不见 235.5）。**机制账**：探针 28 发→informative 13→优于当轮主序 5，其中 3 发产生实际处置=兑现升级 2（f2-15 直达 oracle、f2-13 压线过门）＋纠偏 1（「无过孔方案」理论被实测推翻回翻）。对照 R1a：盲提 0/5、单步迭代 2/5→多轮探针 4/5+295.0。实耗 1,838,944 tokens（用户豁免用量，全 harness 配额）。

### 4.2 PILOT-R2：档位/波次双 viable，层计划天花板判前枚举

三臂对照（档位/层计划/波次，各 5/5 场景）。**判前通道天花板枚举（引擎侧，关键方法）**：档位/波次在 M 集 5 场景天花板=全序 oracle 5/5（粗粒度不丢表达力）；层计划天花板=基线（2 层小板零咬合面，2^6 计划空间中仅 32 可布、无一优于基线，f2-13 一半计划不可布）——判前即知层计划在本语料无空间。终局：**G3 档位与 G5 波次双 viable_positive**（G3 R1 即 3/5 oracle 含 f2-13 284.5——R1 全序臂 4 轮未达，R2 即 5/5；G5 三轮到 5/5 并守住）；**G4 层计划 not_viable=天花板判定的兑现**（机制全通：硬约束注入/fail-stop/失败反馈按设计工作，被试从钉层致断跑中一轮即回退——失败=表达力零余量，非通道故障）。对照：粗通道比全序更快触顶（小假设空间＋探针实测=更高模型搜索效率；多 oracle 序并存降低精度要求）[1][2]。token 合计 3,752,487（G3 1,319,293/G4 1,025,191/G5 1,408,003）。落点：档位（主选）＋波次入 P3 shadow 通道清单，全序留作天花板参照。

### 4.3 SCALE-R1：n8 全枚举证真 474.5、证伪 SA 下界

规模放大双臂消融（4 造景 scl-n08/10/12/16，人口三次迭代定型=宽缝墙+封边+抖动）。**机制账（真正产出）**：

- **n8 全枚举 40,320 排列（oracle 件 sha16 `d481ff2553e0ec7e`，本批重算一致）**：证明 SB-n08 探针发现的 **474.5 为真全局最优**（最优序 n1,n2,n3,n4,**n6,n5**,n7,n8——正是探针发现并采纳的那一序）；直方图仅 474.5/475.5 两值（各 20,160）——整板排序效应就是 n5/n6 一对的先后。**SA-n08「475.5 已是结构下界」被完全枚举证伪**。
- SB-n16 探针验证 gambit 摸到 **1489.5=null_min=参照顶**（比基线 1515.5 改善 1.71%；在 400 序抽样仅 17 序可行的 hard mode 上——约 96% 排列致死）。
- SB-n10 探针检出致死序（进约束模型）；「孤立好序」板不解决覆盖（n10 的 702.5 系 400 序抽样所得、双臂定向 ~30 序未中）。
- **人口教训（进方法学）**：排序余量与可布性此消彼长——**引导价值区在过渡带**（中等 UNSAT 率＋结构陷阱）；零余量板无增益无害、全余量板无需引导。
- 判据面：G-S1 scale_value（含诚实条款：n12 系等值匹配，分母上「严格打败基线且低于 null_min」未发生）＋G-S2 inconclusive（零余量板两臂同价）→终判 **scale_partial**；token 2,918,095。

**图 1**（`figs/FIG-P5-01-SCALE-R1-N8-HIST-N16-GAMBIT.png`，生成脚本 `figs/scripts/FIG-P5-01-SCALE-R1-N8-HIST-N16-GAMBIT.py` 直读机器件 `oracle-scl-n08.json`/`null-summary.json`/`state/{SA,SB}.json`，sha16 断言重算）——(a) scl-n08 全枚举 40,320 排列 objective 直方图仅两值 474.5/475.5（各 20,160），全局最优 474.5 的最优序 n1,n2,n3,n4,n6,n5,n7,n8 即探针臂发现并采纳的那一序；(b) scl-n16 hard mode 双臂轨迹：无探针臂（SA）四轮不低基线 1515.5，探针臂（SB）R3 结构性 gambit 实测 1489.5＝null_min 参照顶（400 序抽样仅 17 序可行，约 96% 排列致死）。

### 4.4 EXP-S1：四层板档位天花板 9/9＋层计划通道物理性关闭

- **引擎侧 H1 终判 h1_negative**：`router.py:146-158` 焊盘层不变式⇒钉层=纯限制通道（永不能把网推离焊盘层）；四轮语料设计迭代全零咬合，n=4 razor 窗口 **625 案全枚举精确证明 min=基线**——**PILOT-R2 的 G4 not_viable 非两层伪影，是通道物理**。层计划通道关闭（除非引擎语义变更）。
- **引擎侧正结果**：TIER 天花板=FULL oracle 逐值相等 **9/9**（粗通道表达力四层零损失）；排序咬合 4/9≥预注册派发线 3/9⇒dispatch。
- **模型结果**（18 agent×4 轮，≈3.8M tokens）：**TIER R4 全部咬合场景 oracle 命中（cceil=1.0）**——96/123/191/87/122/183/134/166/**266**；**fc-06 反超全序臂**（266 vs 272：全序四轮未达 oracle，TIER 靠探针晋升 R2 即中）；FULL 3/4。G-Q1 双臂零回退；G-Q3 mechanism_active（探针 63 发 informative 23=36.5%≥25% 阈值，PILOT-R2 三臂 weak 的情势在本线逆转）。**主判据=transfers**（R2 粗通道结论外推 4 层板成立）。

**图 2**（`figs/FIG-P5-02-EXP-S1-FC06-REVERSAL.png`，脚本 `figs/scripts/FIG-P5-02-EXP-S1-FC06-REVERSAL.py`）——fc-06 场景档位臂反超全序臂的逐轮轨迹：全序臂四轮未达 oracle（止 272），档位臂靠探针晋升 R2 即中 oracle 266——粗通道（档位）以更小的假设空间＋探针实测获得比全序更快的收敛，是「档位为主选（n≤12）」通道选型读数的机制样本[3][4]。

### 4.5 EXP-S2：波次通道过门（S-V5-1 决策点；本批补齐细读数）

夜窗批（3 通道×8 场景×4 轮=96 次 submit 全入账，无停臂无时钟触发；参照=min(基线, null_best_30, hillclimb_600) 非 oracle 诚实口径；人口验收三条件：基线 SAT＋headroom≥2.0＋30 条种子随机序 SAT 率∈[0.10,0.90]，9 构造 8 验收，s2-n08-b 难度悬崖 void_by_population 如实登记）。终判 **scale_partial**，细读数（终判件=GUIDE-EXP-S2-VERDICT-2026-09-20.md，主审独立复核与夜班机械报告逐位一致）：

| 口径 | TIER | WAVE | FULL |
|---|---|---|---|
| closure 均值 | 0.5332 | **0.9464** | 0.9861 |
| 闭环 1.0 场景数 | 4/8 | **7/8**（唯一非顶 n12-b=0.5714） | 7/8（n16-b=0.889） |
| n16 档 | **0/3**（全停基线） | 3/3 闭环 1.0 | 3/3 闭环 1.0 |

- **H1 配对方向检验**（d=closure_粗−closure_FULL）：H1_TIER 三档全负且随网数单调恶化（n08 −0.031/n12 −0.224/n16 −0.963）；H1_WAVE 部分成立（n08 0.000 平/n12 −0.143/n16 **+0.037 反超**）。
- **通道拆分**：波次通道=通过（7/8 场景闭环 1.0，平均早 FULL 约 0.5–0.7 轮触顶）；**档位通道 n16 不过（0/3）——机制=展开粒度而非表达力**[5][6][7]（日班引擎侧已证 TIER 抽样天花板=参照顶 8/8；档位展开无法表达「同档内 n2 先于 n1」类改动，波次可用「n2 独占 wave-1」平凡表达）。
- 机制面：探针 186 发/informative 69（37.1%）/beat_main 43/**晋升 17**，G-Q3 mechanism_active；H2 全序退化无信号、H3 探针预算 B=3 充足。
- **S-V5-1 过门口径（预注册冻结枚举）**：scale_viable 或 scale_partial（H1 在 n≥12 至少一档成立且非全 partial）⇒ **EXP-S2 过门**，席位 B 真实板全量恢复前置达成（R1b 兜底因此销账）。「大 n 波次升主选/档位限 n≤12」为带值定案呈用户裁决项，主审未自行改清单。
- token：编排台账 `orchestration/ledger.json` 分项 TIER 5,275,233/WAVE 6,724,104/FULL 5,504,123=**17,503,460**（完成通知级计量，含 max reasoning；预注册 1.2M/臂防燃线为字节口径，差 5×+ 根因=子代理默认深思+大网包体，非失控——白天/计费窗口适用性挂用户裁决）。

### 4.6 五实验小结

| 实验 | 判决 | 关键读数 |
|---|---|---|
| PILOT-R1 | pilot_positive | 4/5 oracle＋295.0；28→13→5→2 漏斗 |
| PILOT-R2 | G3/G5 双 viable_positive；G4 not_viable | 各 5/5 触顶；层计划天花板=基线 |
| SCALE-R1 | scale_partial | 474.5 真最优（40,320 全枚举）；1489.5=null_min；SA 下界证伪 |
| EXP-S1 | transfers＋h1_negative | TIER 9/9=FULL；cceil=1.0；fc-06 266 vs 272；625 案 |
| EXP-S2 | scale_partial（波次过门） | WAVE 7/8 闭环 1.0；TIER n16 0/3=展开粒度 |

## 5 真实板三批（负结果链）

### 5.1 批一：A 层会话波单轮（14 板，⑥后世界）

arm③ 模型席位单轮提案 vs arm② 基线（14 终态板=6 SAT+8 FAILED）：**③==② 字节等 14/14**——理念增益 0/14、模型增量 0/14；复述度 0.960（注入板 12/14）/1.000（未注入板 2/14：thunderbolt 合同违约、stm32 展开不合）——模型把引擎候选高度回声。席位 B 提案合同违约被引擎拦截（thunderbolt，wave 覆盖 3/表全集→注入丢弃）=fail-closed 消费面证据。三路投票 N=3 全勤（席位 C，见篇二 §8）。

### 5.2 批二：SEAT-B-RESTORE 多轮恢复批（14 板 24 轮，⑥后世界）

D002 形态（≤3 轮×≤3 探针，tier 点名两板做 A/B）。**正负并存**：

- **机制真实激活**：轮级提升 9/24=0.3750、板级 6/14=0.4286（可提升域 6/8，**全在 8 块 FAILED 板**；SAT 6/6 全零=引擎对粗通道序不敏感）；轮间提案方差均值 0.3319（n=10 对，区间 [0.0,0.6429]）、高漂移板与提升板同向（i2c24io 0.643/stm32 0.556/usb 0.455）。
- **终解增量 0/14**：③==② canonical 字节等、G4 model_increment 0/14、echo 0.96 均一——多轮迭代未改变 A4 终选下的终局，与会话波单轮一致。
- A/B 通道对照无区分度（两点名板 badgeleds/tmp108 均序不敏感 SAT 轻板——任务书设计巧合）。
- 主审复核 ACCEPT 零红线违反（LEAD-REVIEW 12 复核面：24/24 轮独立复算零偏差、序数封印 10/10 回执逐字内嵌+零数值泄漏〔关键词命中 48 全为预授权规则文本〕、跨运行 ② sha 与会话波 g4-table 14/14 一致=引擎确定性跨日三重坐实）。token 总字段 3,765,414、分项加总 3,665,414，**Δ100,000 不闭合瑕疵如实携带**（LEAD-REVIEW 瑕疵非阻断）——后续立规「total=分项加总」硬校验。

### 5.3 批三：SEATB-SUPPLEMENT 补充批（7 板 18 轮，D8 世界）

用户令「三项都补跑，当前的数据量不足以证实」驱动三目标全落地：

- **FAILED 域 A/B 区分度 3/4**（分母 4＝FAILED 域 5 板剔除 om-flexgrid——om 17 表条目＞12 上限＝wave only、不进 A/B 双臂对照面〔`SEATB-SUPPLEMENT-REPORT.md:32`〕；stm32=秩分布+终案序数两维、m2/usb=三维全异）；**usb/m2 的提升只发生在 tier 轮**——正式线「A/B 无区分度」在其点名面（两 SAT 板）复现、扩面 FAILED 域后被推翻，**用户的「数据量不足」判断获数据支持**；无区分度=2 SAT 轻板＋dc-scm（表条目 2 自由度天花板）。
- **om 换案回退复现计数=1**（r3 终案序数 [False,1]<板内已见最优 [False,8]，轮内仍有提升 0→1；与正式线同形态——封印下不可见绝对水位）。
- **终解增量复测 ③==②=7/7**（②源 7/7 命中 D8 现树 execute canonical 档、轮换兜底零启用）——多轮+tier 扩面+9 提升轮（轮级 9/18、板级 4/7、FAILED 域 4/5——此分母 5＝全 FAILED 域〔含 om〕，与上行区分度分母 4 面不同：om 入轮级提升面、不入 A/B 对照面，dc-scm 两面均无）仍零终解增量，三批方向一致。
- 主审复核=**ACCEPT_WITH_NONBLOCKING_DEFECTS**（12 面＋3 专项全过：18/18 轮独立复算零偏差、A/B 三维逐板一致、③==② 7/7 且 arm2_sha 逐板==主审独立复算 D8 现树 canonical、双跑 2/2、封印面 18 prompt 零序数泄漏；四缺陷全非阻断——含 token 台账分项和 1,300,642 vs 总字段 1,300,850 的 Δ208 不闭合，与正式线 Δ100,000 同类连续两批复现；报告 §5 漂移归属句错误（0.625 属 badgeleds r1→r2 非 stm32）以 LEAD-REVIEW 件为准）。

### 5.4 V5-R2 单轮 execute 内重布序：如实负结果

合成导引对照（R2 批内）：合成 9 格＋esp32 3 格双轴零敏感（306 attempts/85 轮/committed=0 同值）——**EXP-S2 正结论的适用域=多轮提案迭代，非单轮 execute 内重布序**。

**图 3**（`figs/FIG-P5-03-SEATB-THREE-BATCH-ZERO-INCREMENT.png`，脚本 `figs/scripts/FIG-P5-03-SEATB-THREE-BATCH-ZERO-INCREMENT.py`）——席位 B 真实板三批零终解增量对照：三批（会话波单轮 14 板／RESTORE 多轮 24 轮／SUPPLEMENT 扩面 18 轮）在「轮级提升真实激活」（9/24、9/18 全在 FAILED 域、tier 轮效应）与「终解增量全零」（③==② canonical 字节等 14/14、14/14、7/7）两轴上的并列呈现——机制在轮内、增益不进终解，三批跨两个世界锚方向一致。

## 6 价值在哪（RQ2/RQ3 的机制综合）

1. **合成域价值的机制=探针环**（模型点名→引擎代测→回传实测）：PILOT-R1 的 28→13→5→2 漏斗、EXP-S1 的 36.5% informative 率、EXP-S2 的 37.1%+17 晋升、fc-06 的「探针晋升 R2 即中」——模型贡献的不是序的知识而是**采样的智能**：在 40,320 排列里把好的那一片找出来让引擎标价[8][9][10]。
2. **真实板零终解的机制=A4 终选兜底**：三批一致形态=轮内有提升（9/24、9/18）但终解与基线字节等——A4 按 canonical 指纹全局择优，轮内任何「改善」若不优于基线指纹即被丢弃。这不是失败，是**分权设计的直接推论**：度量权归引擎时，模型必须产出严格更优的候选才能穿透终选。
3. **接缝假设（D002 收口的开放点）**：导引价值若存在，在「探针环轮内搜索增益×A4 终选」的接缝处——例如允许模型用探针实测值构造**基线不包含的新候选**（而非只在基线候选集上排序）。该假设未测，属后续形态。
4. **通道物理（负知识也是知识）**：层计划通道被焊盘层不变式物理性关闭（625 案全枚举）；档位/波次通道天花板=全序（表达力无损）、档位在 n16 的崩塌=展开粒度而非表达力——通道选型的判前枚举方法可直接迁移。

## 7 Threats to Validity

1. 合成域场景小板、结构可推理（人口设计三次迭代本身说明人口敏感性）；「引导价值区在过渡带」来自 SCALE-R1 单批教训，未做第二次独立采样。
2. n16 hard mode（约 96% 排列致死）不入成本门分母（描述性）。
3. 真实板三批跨世界（会话波/RESTORE=⑥后世界，SUPPLEMENT=D8 世界）——终解增量零的结论跨世界一致（其稳健性反而因此增强），但轮级提升率不可跨世界直接比较。
4. tier 点名面小（正式线 2 板、补充批 6 板）；「唯一提升轮恰为 tier 轮」系观察非检验。
5. 席位=纯会话数据内嵌（无工具）；模型家族以 GLM-5.3F 为主、DSF/千问/GPT6 参与重放（篇二）——跨模型结论不外推。
6. token 预算纪律运营事件如实登记：PILOT-R2 合法修订 600k→1.2M/臂（派发前）；SCALE-R1 用户取消上限；EXP-S2 真实 token 17.5M vs 防燃线字节口径差 5×+（计费口径差非失控）[11][12]；**席位 B 管线 token 台账不闭合连续两批**（RESTORE Δ100,000、SUPPLEMENT Δ208，均只记不拦不改结论）——已立规「total=逐场加总」硬校验。
7. echo 0.96 的「回声」读数依赖候选 id Jaccard 口径——模型可能提同义不同 id 候选，该口径下会低估原创性（口径限制如实登记）。
8. SUPPLEMENT 报告 §5 漂移归属句错误（0.625 属 badgeleds 非 stm32）经 LEAD-REVIEW D-2 更正，本文不引用该单板漂移数。

## 8 Conclusion

**RQ1**：合成域导引价值真实且有机制——多轮探针 4/5 oracle、粗通道双 viable 各 5/5、n8 全枚举证真 474.5 并证伪 SA 下界、四层 TIER cceil=1.0 含反超全序臂一例、波次缩放 7/8 闭环 1.0 过门。**RQ2**：真实板终解零增量的机制=A4 终选兜底（分权设计的直接推论），三批跨世界一致；轮内增益与通道区分度真实存在（FAILED 域 3/4、tier 轮效应）。**RQ3**：席位 B 维持 shadow advisory（D002 终局）；价值探索转向接缝假设（探针实测值构造基线外新候选）。方法学交付：天花板判前枚举、过渡带人口验收三条件、探针机制漏斗记账、token 双轨护栏。

**Future work**：①接缝假设的预注册检验（模型构造基线外候选）；②档位臂 n16 展开粒度修复后复测；③tier 通道的 FAILED 域扩面（诊断性价值是否可机制化）；④与篇六（直接操作席位）的范式对照消费。

---

## 附录 A　AI 参与披露段（本篇线；口径承披露正本 v4——`out/v4-exec/paper-ai-disclosure-r4.md`（2026-09-19 签发）；r1–r3 及修正层承前零改写）

### A.1 执行窗口与模型构成

| 窗 | 日期 | 形态 | 读数 | token 实测（口径） |
|---|---|---|---|---|
| SEAT-AB-R1a | 09-13 | 子智能体四席（v4cmp cal 域 16 场景） | H1 not_captured 0/5；H2 GLM iteration_value 2/5 | 台账见 R1a 件（本篇只引结论） |
| GUIDE-PILOT-R1 | 09-16/17 | 子智能体 6 agent×4 轮 | 4/5 oracle＋295.0 | 1,838,944（usage 逐轮；用户豁免 300k 停机线） |
| GUIDE-PILOT-R2 | 09-17 | 子智能体三臂×4 轮 | 双 viable 各 5/5 | 3,752,487（G3 1,319,293/G4 1,025,191/G5 1,408,003） |
| GUIDE-SCALE-R1 | 09-17 | 子智能体双臂×4 轮 | scale_partial | 2,918,095（R1 395,065/R2 710,230/R3 857,343/R4 955,457） |
| GUIDE-EXP-S1 | 09-17 | 子智能体 18 agent×4 轮 | transfers+h1_negative | ≈3.8M（72 会话 usage 汇总量级） |
| GUIDE-EXP-S2 | 09-19/20 夜窗 | 子智能体 24 位×4 轮 | scale_partial（波次过门） | 17,503,460（ledger 分项 TIER 5,275,233/WAVE 6,724,104/FULL 5,504,123；完成通知级含 max reasoning） |
| 会话波（席位 B/C） | 09-21 | 子智能体 14 场＋投票三路 | ③==② 14/14 | 席位 B ≈1.4–2.8M（估算披露）＋席位 C 1,160,419（P1 503,465/P2 410,165/P3 246,789） |
| SEAT-B-RESTORE | 09-21/22 | 子智能体 24 场多轮 | 终解 0/14 | 总字段 3,765,414（分项加总 3,665,414，Δ100,000 不闭合随件） |
| SEATB-SUPPLEMENT | 09-22/23 | 子智能体 18 场多轮 | 终解 ③==② 7/7 | 总字段 1,300,850（分项加总 1,300,642，Δ208 不闭合随件） |

模型构成：GLM-5.3F 子智能体（GUIDE 五实验＋席位 B 会话）；deepseek-flash 与 GLM-5.3（席位 C 投票 P2/P3）。全部经 harness 子智能体通道，零 harness 外 LLM 直呼（各批红线自查 PASS 在案）；席位=无工具纯会话数据内嵌。全纲领 token 聚合口径（多口径并记、「total=分项加总」硬校验、gap 与散失登记）见 `<ENGINE_ROOT>/out/paper-program-r2/TOKEN-LEDGER-AGGREGATE.md`（本篇各数与其 §5.1/§5.3 对账一致；EXP-S2 分项以 ledger 权威值 FULL=5,504,123 口径为准，见该表 §8-4）。

### A.2 incident 与勘误（本篇线，append-only）

1. **PILOT-R1**：执行器状态机 bug 执行期修复（冻结版 `f02cbf3d…`→编排修复版 `be283348…`，仅状态机/结果命名，零影响测量与判据）；「哈希占位笔误第二次发生」→加严纪律=进日志前必须先跑 hashlib。
2. **PILOT-R2**：报告期 cmd_report 硬编码第 4 轮取值→改为按臂 state.round 取终轮（纯报告口径修复，零影响数据）。
3. **SCALE-R1**：时限兜底件 automation-41a003a3 未触发即收口、任务完成后删除（登记在案）。
4. **EXP-S1** 三项 erratum：①ceilings 首跑展开器包装 bug（LP/TIER 全 None）→修机器重跑；②fc-04/fc-06 快照曾被 razor 探针覆写→gen 恢复并以重测为准；③report 首跑 KeyError→收紧只读派发臂。「hash 先算后写」再犯一次（时间戳占位先登 hash），以 DISPATCH-LOG 更正行收口。
5. **EXP-S2**：ERRATUM N-1（WAVE|s2-n08-a r4 回复 00:44 到达后 submit 漏执行，机械完成度门按设计拦截，06:00 从回复原文逐字重建补 submit，数据零污染）；5 位 round-2 续跑静默死亡（04:35 前，TaskOutput 活性探针判死+全数重建）；首选嵌套编排不可用（子代理工具集无 Agent/SendMessage）降级督导单编排者；真实 token 与防燃线字节口径差 5×+（§4.5，白天/计费窗口适用性挂用户裁决）。
6. **会话波**：渲染像素级复核通道全窗失效（EXP-ZCODE-008）→降级结构校验（12/12）+双跑字节等；arm3-summary 曾被五板重跑覆写→自 14 板分档重建（规范口径=分档件）。
7. **RESTORE**：批 1 四会话并行返回乱序反板（驱动表 id 预检当轮拦截、交换重跑）；tmp108 r2 一处抄写笔误当轮修正——两起均执行体落盘环节、零污染；token Δ100,000 不闭合（见 A.1）。
8. **SUPPLEMENT**：om r3 会话 JSON 单字符缺失（probes 数组闭合括号，+1 字符修复经结构断言验证后重落，当轮拦截零污染）；token Δ208 不闭合+里程碑归属标注不实（LEAD-REVIEW D-1）；报告 §5 漂移归属句错误（D-2，本文 §7-8）；packs-summary 只登记 2/7 板（D-3）；修复前原文未存档（D-4）。
9. **立规**：席位 B 管线 token「total=逐场加总」硬校验条款（D002-FOLLOWUP-NOTE 2026-09-23 立）。

### A.3 边界声明

全部模型输出恒 untrusted：席位提案一律经引擎合同校验（违例即 CONTRACT_FAIL 落证丢弃，不炸驱动）、经引擎确定性代测与 A4 终选；判读全部在冻结判据下机械判定，零模型自评入判。预注册冻结先于模型会话（五实验 prereg sha256 全部本批程序化重算一致：`00c23809…/f362e721…/0fc57eba…/30db9a1c…/845913ec…`）。负结果原样入账（§5 三批、§2 前置负结果、V4.2 定理）。

---

## 修订注记（R2 对账定稿批 2026-10-03）

- 本稿=P5 草稿批（2026-10-03 v1）经任务书 §A-3 全项对账后的 R2 修订稿。对账范围：①GUIDE 四实验 VERDICT 逐件读数核对＋sha256 程序化重算（PILOT-R1 `701623e0`/PILOT-R2 `530a5eb2`/SCALE-R1 `b3201482`/EXP-S1 `26585516` 全部命中；EXP-S2 VERDICT 本批实测 `eb15bd65`）；②EXP-S2 终判件补引细读数（SUPPLEMENTS §A-5 对账项 resolve：7/8 场景闭环 1.0、closure 均值 0.9464、H1 逐档 d、判决 scale_partial、token 17,503,460）；③席位 B 三批台账机器件核对（g4-table.json/lead-review-checks.json/lead-review-checks-supplement.json/token-ledger 等）。
- 本批修订四处：§2.1 V4.2 r2 数字按 `state/v42-model-seat.md` 修正（草稿「M2′ +0%」→「M2′ 处理臂 objective 平均劣化 2.375%」；+0.0% 系 r1 M3 口径）；§4.5 由挂账口径改写为细读数全量入表（「7/8 档过门、迭代闭环率 1.0」→「7/8 场景闭环 1.0」并补三臂对照）；§5.2/§5.3 token 与主审复核措辞按机器件精确化（ACCEPT_WITH_NONBLOCKING_DEFECTS＋四缺陷；RESTORE token 总/分项双数并记）；§7 新增威胁 8（SUPPLEMENT D-2 漂移归属更正）。
- 对账中发现并如实登记、不改正文数字的两项：EXP-S2 VERDICT 头部 night-log sha 登记值与当前字节不符（详见对账明细）；EXP-S2 VERDICT §7 token 括号分项 FULL=5,231,278 为夜班旧值、与 ledger.json 权威分项 FULL=5,504,123 不一致（本稿以 ledger 为准）。
- 零实验、零模型调用、零历史证据件改动（route-v5 根与 out/v5-p5/ 只读）。

## References

> 本篇按大纲 §5 章节大纲不设相关工作章，正文实验结论不依赖外部文献；下表为投稿用文献表（原占位节「待纲领文献检索批统一补齐」于本批回写）。**条目全部取自纲领文献检索批 P5 候选池**（`<ENGINE_ROOT>/out/paper-program-r2/litsearch-r3/refs/P5-candidates.jsonl`），题名/作者/年份/venue/DOI/arXiv/链接逐字段原样转录，**标识符零补造**；候选池中 doi 与 arxiv_id 皆空者只列题名+作者+年份+venue+链接。
> 编号说明：[1]–[12] 为正文内联引用点实际所挂条目（出现顺序即正文行序）；[13]–[24] 为同主题补充件，正文未挂，投稿时按需取用。篇一 [W1]–[W5] 仍为共用引用面，本篇不展开。
> 池内重复登记一件：「Self-Consistency from Only Two Samples」在 r2/r3 两批各一条（同一 arXiv:2604.17433，作者表长度不同），此处按 r3 记录（作者更全）取一条，不重复编号。
> 字段登记：24 条的 venue 字段候选池均有值，无空缺；候选池 doi 为空者已在条目内就地标注「（候选池 doi 为空）」并保留 arXiv 链接（[3][8][10][14][18]），[24] 候选池未登记 doi、[12] 无 arXiv。 [19] 作者字段候选池原样为「Li, Yiwei」（疑姓名解析错位），按原样转录未擅改。条目格式：题名｜作者｜年份｜venue｜DOI/arXiv｜链接。

[1] Learning When to Think: Adaptive Reasoning for Test-Time Compute Allocation｜Gijs Kassenaar; Zhao Yang; Vincent François-Lavet｜2026｜arXiv (Cornell University)｜DOI 10.48550/arxiv.2608.20256；arXiv:2608.20256｜https://arxiv.org/pdf/2608.20256

[2] CODA: Difficulty-Aware Compute Allocation for Adaptive Reasoning｜Siye Wu; Jian Xie; Yikai Zhang｜2026｜arXiv (Cornell University)｜DOI 10.48550/arxiv.2603.08659；arXiv:2603.08659｜https://arxiv.org/pdf/2603.08659

[3] ARES: Adaptive Reasoning-Effort Steering for PPA- and Cost-Aware RTL Optimization with LLM Agents｜Stef Cuyckens; Mihaela Jivanescu; Jun Yin; Chao Fang; Marian Verhelst｜2026｜arXiv preprint｜arXiv:2607.27879（候选池 doi 为空）｜https://arxiv.org/pdf/2607.27879

[4] DiffAdapt: Difficulty-Adaptive Reasoning for Token-Efficient LLM Inference｜Xiang Liu; Xuming Hu; Xiaowen Chu｜2025｜arXiv (Cornell University)｜DOI 10.48550/arxiv.2510.19669；arXiv:2510.19669｜https://arxiv.org/pdf/2510.19669

[5] How Much Thinking is Enough? Quantifying and Understanding Redundancy in LLM Reasoning｜Zhiyuan Zhai; 游信凱; Wenjing Yan｜2026｜arXiv (Cornell University)｜DOI 10.48550/arxiv.2605.23926；arXiv:2605.23926｜https://arxiv.org/pdf/2605.23926

[6] Limited Reasoning Space: The cage of long-horizon reasoning in LLMs｜Zhenyu Li; Guanlin Wu; Cheems Wang｜2026｜arXiv (Cornell University)｜DOI 10.48550/arxiv.2602.19281；arXiv:2602.19281｜https://arxiv.org/pdf/2602.19281

[7] More Test-Time Compute Can Hurt: Overestimation Bias in LLM Beam Search｜Gal Dalal; Assaf Hallak; Gal Chechik｜2026｜arXiv (Cornell University)｜DOI 10.48550/arxiv.2603.15377；arXiv:2603.15377｜https://arxiv.org/pdf/2603.15377

[8] Self-Consistency Improves Chain of Thought Reasoning in Language Models｜Xuezhi Wang; Jason Wei; Dale Schuurmans; Quoc Le; Ed Chi; Sharan Narang; Aakanksha Chowdhery; Denny Zhou｜2022｜arXiv preprint｜arXiv:2203.11171（候选池 doi 为空）｜https://arxiv.org/pdf/2203.11171

[9] Escape Sky-high Cost: Early-stopping Self-Consistency for Multi-step Reasoning｜Yiwei Li; Peiwen Yuan; Shaoxiong Feng｜2024｜arXiv (Cornell University)｜DOI 10.48550/arxiv.2401.10480；arXiv:2401.10480｜https://arxiv.org/pdf/2401.10480

[10] Optimal Self-Consistency for Efficient Reasoning with Large Language Models｜Austin Feng; Marius Alonso; Ambroise Odonnat; Vasilii Feofanov; Ievgen Redko｜2025｜arXiv preprint｜arXiv:2511.12309（候选池 doi 为空）｜https://arxiv.org/pdf/2511.12309

[11] The Shadow Price of Reasoning: Economic Perspective on Optimal Budget Allocation for LLMs｜Xu Wan; Speed Zhu; Jianwei Cai｜2026｜arXiv (Cornell University)｜DOI 10.48550/arxiv.2606.03092；arXiv:2606.03092｜https://arxiv.org/pdf/2606.03092

[12] Test-Time Compute and Budget (“Reasoning Effort”): An Underrecognized Methodologic Variable in Medical Large Language Model Research｜Dong Kyun Kim; Joon‐Yong Jung｜2026｜Korean Journal of Radiology｜DOI 10.3348/kjr.2026.0643（候选池无 arXiv）｜http://kjronline.org/Synapse/Data/PDFData/0068KJR/kjr-27-e57.pdf

[13] Adaptive Test-Time Compute Allocation for Reasoning LLMs via Constrained Policy Optimization｜Zhiyuan Zhai; Bingcong Li; Bingnan Xiao｜2026｜arXiv (Cornell University)｜DOI 10.48550/arxiv.2604.14853；arXiv:2604.14853｜https://arxiv.org/pdf/2604.14853

[14] A Survey of Test-Time Compute: From Intuitive Inference to Deliberate Reasoning｜Yixin Ji; Juntao Li; Yang Xiang; Hai Ye; Kaixin Wu; Kai Yao; Jia Xu; Linjian Mo; Min Zhang｜2025｜arXiv preprint｜arXiv:2501.02497（候选池 doi 为空）｜https://arxiv.org/pdf/2501.02497

[15] What If We Allocate Test-Time Compute Adaptively?｜Ahsan Bilal; Ahmed Mohsin; Muhammad Umer; Ali Subhan; Hassan Rizwan｜2026｜arXiv (Cornell University)｜DOI 10.48550/arxiv.2602.01070；arXiv:2602.01070｜https://arxiv.org/pdf/2602.01070

[16] Uncertainty-Aware Budget Allocation for Adaptive Test-Time Reasoning｜Manh Nguyen; Sunil Gupta; Hung Le｜2026｜arXiv (Cornell University)｜DOI 10.48550/arxiv.2605.26849；arXiv:2605.26849｜https://arxiv.org/pdf/2605.26849

[17] Reasoning Aware Self-Consistency: Leveraging Reasoning Paths for Efficient LLM Sampling｜Guangya Wan; Yuqi Wu; Jie Chen｜2025｜Conference of the Nations of the Americas Chapter of the Association for Computational Linguistics: Human Language Technologies (NAACL)｜DOI 10.18653/v1/2025.naacl-long.184；arXiv:2408.17017｜https://aclanthology.org/2025.naacl-long.184.pdf

[18] Self-Consistency from Only Two Samples: CoT-PoT Ensembling for Efficient LLM Reasoning｜Raman Saparkhan; Majd Hawasly; Md Rizwan Parvez; Mohammad Raza｜2026｜arXiv preprint｜arXiv:2604.17433（候选池 doi 为空）｜https://arxiv.org/pdf/2604.17433

[19] Make Every Penny Count: Difficulty-Adaptive Self-Consistency for Cost-Efficient Reasoning｜Xinglin Wang; Shaoxiong Feng; Li, Yiwei｜2024｜arXiv (Cornell University)｜DOI 10.48550/arxiv.2408.13457；arXiv:2408.13457｜https://arxiv.org/pdf/2408.13457

[20] The Impact of LLM Self-Consistency and Reasoning Effort on Automated Scoring Accuracy and Cost｜Scott Frohn｜2026｜arXiv (Cornell University)｜DOI 10.48550/arxiv.2604.26954；arXiv:2604.26954｜https://arxiv.org/pdf/2604.26954

[21] SynAct: A Reasoning-Acting Large Language Model Agent for Adaptive Synthesis Optimization｜Fangzhou Liu; Peiyi Han; Jiawei Liu｜2026｜arXiv (Cornell University)｜DOI 10.48550/arxiv.2608.12751；arXiv:2608.12751｜https://arxiv.org/pdf/2608.12751

[22] The Reasoning Tax: Token Economics of LLM Reasoning Across Task Types and Deployment Contexts｜Sachin Gopal Wani; Ajay Dholakia; David D. Ellison｜2026｜arXiv (Cornell University)｜DOI 10.48550/arxiv.2608.26235；arXiv:2608.26235｜https://arxiv.org/pdf/2608.26235

[23] Star Elastic: Many-in-One Reasoning LLMs with Efficient Budget Control｜Ali Taghibakhshi; Ruisi Cai; Saurav Muralidharan｜2026｜arXiv (Cornell University)｜DOI 10.48550/arxiv.2605.07182；arXiv:2605.07182｜https://arxiv.org/pdf/2605.07182

[24] Budget-Aware Anytime Reasoning with LLM-Synthesized Preference Data｜Xuanming Zhang; Shwan Ashrafi; Aziza Mirsaidova｜2026｜arXiv (Cornell University)｜DOI 空（候选池未登记）；arXiv:2601.11038｜https://arxiv.org/pdf/2601.11038

## 统稿批注记（2026-10-03，纲领 R2 统稿席）

按大纲 §8 顺序过稿的统稿动作（数字零改动，均属术语/引用/图位层）：①头部术语句改分层口径（证书层三态 SAT/UNSAT/UNKNOWN＋运行层终态 FAILED，原句将 FAILED 并入三态列举，按 TERMINOLOGY §1.1「FAILED 不是三态之一」修正）并挂接术语表与门号命名空间声明；②§1 补席位范式两极互引（↔篇六）；③挂接三张新图（图 1 SCALE-R1／图 2 EXP-S1 fc-06／图 3 三批零终解增量对照，路径 `figs/`、生成脚本直读机器证据 JSON＋sha16 断言，本批已抽验图 1 脚本断言层与 §4.3 正文读数逐项一致）；④附录 A.1 挂接全纲领 token 聚合总表并钉死 EXP-S2 FULL 分项以 ledger 权威值 5,504,123 为准。
- 读审处置批追加（同日）：§1「两年」改为可核时间线（2026-09-13 定调、09-16~23 执行窗——全纲领可核时间线无「两年」支撑）；§5.3 两处 FAILED 域分母调和（区分度 3/4 面=5 板剔 om〔wave only〕、轮级提升 4/5 面=全 5 板，om 入此不入彼、dc-scm 两面均无——机器件 `SEATB-SUPPLEMENT-REPORT.md:13,32`）；补 References 占位节（#31）。
