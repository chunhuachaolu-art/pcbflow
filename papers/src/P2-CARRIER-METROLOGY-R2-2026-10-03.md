# 篇二《缺陷诊断席位的载体测量学——渲染图盲读与结构化盲包的两半》定稿 R2

<div class="release-note">

**发布说明（2026-10-30 收线归档）**：本文是 pcbflow 项目的中文技术报告（R2 内部定稿），**未经同行评审，未投稿**。文中形如 `<ENGINE_ROOT>/out/...`、`<WORKSPACE>/...` 的证据路径指向作者本机的实验证据目录，这部分没有公开；代码与核心板设计见仓库 `engine/`、`tools/`、`design/`。"主审""席位"等术语见 `TERMINOLOGY.md`。作者：赵丹琪。许可：CC BY 4.0。

</div>

---

## 摘要

让大模型担任 PCB 缺陷诊断席位（判读者，reader；r8 底稿中亦作 critic），工程界默认的问法是「模型行不行」。本文把问题改写为**载体问题**：同一类诊断任务，交给模型的输入是渲染图还是结构化盲包，结论会系统性分岔。我们报告同一项目内两条平行证据链：**图像载体半**——24 轮预注册盲读发展域＋冻结 holdout 双窗＋跨板 GT 复检与三连 reject 负结果链：联合达标线从未满足（recall 始终 <0.31，union 峰值 0.307692），跨板 19 条 GT 复检零命中（0/19，类别门主导 17/19），类别→几何→语义三轮修订全部 reject（gt-semantic 双口径 0/19 与框移校正 1/19=marginal 并记），渲染图上的缺陷检出体系与 DRC-GT 体系**未建立可用映射**；**盲包载体半**——同一时期、同类判读能力，在结构化文本盲包（合成板 6 裁决项/真实板 4 缺陷重放/11 板投票）上全部成立：裁决首演 3 独立会话 5/6/6.5 且被试抓出任务书自身 4 处几何 bug（advisory 价值实锤）、五模型重放多数票聚出缺陷族（GT1–GT3 各 4/5、4/5、3/5 席命中）、真实板投票 N=3 零票面违约并系统发现引擎证书完备性缺口（cert-completeness 五板点名）。两半合流的结论：**advisory 价值依赖载体-任务匹配而非多模态本身**——渲染图利于全局观察但其现象体系与规则级 GT 不可映射；结构化盲包牺牲全局性换来规则级缺陷归类的可判定性；第三极（SVG 代码载体，纲领篇一 E0）证明代码化载体可以两者兼得身份与可校核性。方法学交付：预注册盲读协议五版本、字母/机制/教训三分账、弃权分型 rubric、双口径检出度量、载体-任务匹配矩阵与测量设计迁移清单。

**关键词**：LLM 评审；PCB 缺陷检测；载体测量学；预注册；弃权分型；多数票；advisory 席位

---

## 1 Introduction

AI 审查者正在进入工程设计流程。但在把 critic 放进流程之前有一个更根本的问题——**如何评判判读者本身（judging the judge）**，以及一个被更少追问的问题——**把什么交给它读**。本项目（pcbflow）在 2026-09 同时维护了两条判读者实验线，输入载体截然不同：

- **渲染图盲读线**（V3 critic 校准线，论文二正本 r8 承前）：reader=独立子智能体，输入=单张 PCB 渲染 PNG＋冻结判读指引，零 GT、零历史。24 轮发展域＋冻结 holdout 双窗＋GT 扩样复检＋三轮修订轮，构成一条完整的**负结果链**。
- **结构化盲包线**（V5 席位 A/C 线）：判读者输入=结构化文本盲包（合成板裁决任务书/缺陷重放包/真实板终态包），同样是纯会话、零工具、预注册判读。构成一条完整的**正结果链**。

本文把两半合成一篇的理由不是「都做了」，而是**双载体对照本身是结论**：同项目、同纪律（预注册、fail-closed、字母裁决、LEAD-REVIEW 独立复核）、同一批模型家族，唯一的系统性差异是载体——结论分岔到 0/19 与 6/6 的量级。（可比性限定如实声明：「同一批模型家族」系工作口径而非可核事实——图像半 26 个记录单元与 S54 三会话的模型身份均 100% 未随档落盘〔§10.2〕，跨半严格同一性不可核；本篇主张落在「同代 GLM 家族为主的同类判读能力」层面。）这把「模型能不能当诊断席位」改写成「**什么任务该用什么载体喂给模型**」。

三个研究问题：

- **RQ1（图像半）**：渲染图上，判读者的缺陷检出能否被校准到可用？——24 轮＋双 holdout 的回答：**不能**（联合达标线从未满足；跨板零命中；三连 reject）。
- **RQ2（盲包半）**：结构化盲包上，判读者能否产出可消费的缺陷判定？——三批的回答：**能**（裁决/重放/投票全成立，且发现任务与引擎自身的缺陷）。
- **口径提示（主对照「0/19 vs 6/6」的 6/6）**：6/6＝席位 A N=5 规范化多数票聚出全部 6 条**规范缺陷**（3 条播种＋GT1–GT3 族；GT4 族 0/5 全漏不计入「聚出」分母——§7.2、§10.7），与 S54 判分「5/6/6.5（满分 7）」是两个不同度量，勿混读。
- **RQ3（合流）**：载体差异是不是两半分岔的主因？——以第三极（SVG 代码载体，篇一 E0：身份恢复 100%、负向拦截 80/80）与仪器测量学证据（呈现层上限、类别门机制）为中介，给出载体-任务匹配矩阵。

## 2 Related Work

- **LLM/多模态评估方法学**：模型校准、选择性预测/弃权、LLM-as-judge 可靠性（Wen 2025 TACL；Kadavath 2022；Zheng 2023 NeurIPS D&B；Wang 2024 ACL）。本文差异：弃权作为一等测量对象（分型 rubric＋链回放 fail-closed）；且把「载体」作为受控变量。
- **预注册在 ML/SE**：逐轮粒度预注册（Nosek 2018 PNAS；Pineau 2021 JMLR）。
- **PCB 视觉检测**：AOI 与人工目检人因研究（Soukup 2010；Lv 2024）；本文 reader 即「AI 检验员」，GT 双裁决链和禁称 precision/FPR 的口径比多数 AOI 文献更保守。
- **LLM-for-EDA 的 review/copilot 线**（Liu 2024 DAC；He 2024 TCAD）。
- **结构化输入与 agent 评审**：盲包=把「规则级缺陷归类」任务从像素空间搬到符号空间——与代码审查中 LLM 消费 AST/IR 而非截图同构（本纲领内证据，无外部综述槽）。

**载体（harness）文献线（检索批 r2/r3 回写，编号 [11]–[30] 接文末 References）**——七组按与本篇主题的相关度排序：

1. **载体的定义与披露纪律**：agent harness 的必要充分条件刻画 [12] 与 agent loop 的控制策略/技能/harness 谱系综述 [13]，使「载体」从工程俗称变为可下操作定义的对象；方法论侧已有「比较 LLM agent 必须披露 harness」的明文立论 [11]；失败归因侧把「模型还是 harness」立为交互中心分类轴 [14]。本文差异：上述文献底物为通用软件任务，本文把载体对照限定在「规则级缺陷判定」这一可核 GT 任务上，产出的是载体-任务匹配矩阵而非单因子优劣排序（§9.2、§10.5）。
2. **载体作为受控自变量**：分层隔离评测把确定性 scaffold（载体层）与模型层分离归因 [15]；三因子设计（模型／载体／工具契约）分解重复副作用的归属 [16]；harness 的度量与优化被证明可独立于提示词层进行 [17]。本文差异：这些工作分解的是**执行期行为**；本文的载体变量是**输入表示形态**（渲染图／结构化盲包／代码），须在零 GT、fail-closed 与预注册纪律下测「同一判读能力在不同载体上的可达上限」，故本文拒绝把载体效应写成因果结论（§10.5）。
3. **载体形态可编辑与可演化——正反两面**：不改模型只改运行时界面（harness）的自适应 [18]、从失败轨迹诊断并修复 harness 缺陷 [19] 为正证据；「自改进 harness 修复从未发生的失败」[20] 为反面案例——载体自改写会引入归因幻觉。这与本文「席位输出恒 untrusted、消费前必经独立复核」的纪律同向：载体本身是可能出错的一方，须单独立账而非默认正确。
4. **上下文工程**：少上下文胜长程 tool-use agent [21]、上下文管理被证明是长程 agent 的承重结构 [22]、上下文的「策略承载完整性」被提出为可测指标 [23]。本文差异：本文的载体变量是信息的**表示形态**而非信息**长度**——盲包的信息面直接决定可判上限（GT4 族 0/N 即 pad 级几何信息未随盲包下发的直接后果，§7.2、§10.7）。
5. **tool-use 协议与 agent 评测基准**：工具调用表示/数据/评测的统一 [24]、MCP 工具协议下的真实任务基准 [25]。本文差异：本文席位的工具面恒为零（纯会话、零工具，§3.2），故这两类协议层工作对本文是**反例对照**——若给判读者挂上工具与检索，其载体将是第三种形态；本文把该变体列为 future work，而非据文献外推的结论。
6. **弃权与 coding agent 评测**：「agent 是否知道何时不该行动」的弃权评测 [26] 与本文弃权分型 rubric 同题；coding agent 侧已有把推理开销、effort、harness 设计并列为端到端成本归因因子的拆解 [27]，以及长程原始工程任务的 frontier 评测 [28]。本文差异：本文的弃权是被**计量**的一等对象（分型到「不可负责任确认」族、链回放 fail-closed），且载体形态与弃权行为的关系被单独立账（渲染图侧弃权率 vs 呈现层上限，§4.1）。
7. **多智能体席位与失败归因**：按任务难度自适应调整席位数量的多智能体脚手架 [29] 是席位配额的直接对应件；多智能体失败归因基准 [30] 把「归因到模型还是归因到编排/载体」做成可评测对象。本文差异：本文的多数票席位是**同载体下的重复读数聚合**（席位 A/C，§7.2、§8.2），其成立范围被限定在共识域（§9.2）；席位数量作为自变量本文尚未测量，故不给该维度结论。

## 3 图像载体·发展域 24 轮（r8 上半压缩重构）

### 3.1 测试床与 GT

测试床=Rev-C 板（STM32H743 核心板，已列开源计划 CERN-OHL-P-2.0）两设计状态×top/bottom 双视。渲染链：kicad-cli `pcb export pdf`→PyMuPDF dpi 640→（r14 起 bottom 配色重建）。确定性以重渲染 witness 守证（PDF 矢量重放逐字节一致 12/12；r14b 配色管线跨会话像素级确定性 395,916/20,071,249 逐位一致）。GT 只能从**真实判例**确定性派生（DRC 终检＋装配核对台账双裁决链；框=锚点 bbox±1.0mm），**反循环铁律**：禁止从 reader 观察反推 GT（gt-audit-r1 把 bottom/reroute 两候选判例源以「无源」关闭）。发展域 13 条 GT（courtyard_crowding 12/13）＋跨板扩样 19 条/4 板（courtyard 10.5%）。

### 3.2 协议（五版本 append-only）

reader 隔离：独立子智能体、上下文仅指引＋单图、零 GT 零历史；输出恒 untrusted。预注册：每轮三分支判据先于盲读冻结；轮后调整整批降级 development。字母裁决逐轮定义；**三分账**＝字母裁决/机制观察/度量教训。指标：gt_recall（一对一匹配六条件）、多实例 union/agreement 双口径并列、seed_match_rate（**禁称 precision/FPR**）、abstain_rate（零旗→None 不冒充 0/1）。联合门（APR-0011）：gt_recall≥0.75 ∧ seed_match≥0.5 ∧ abstain≤0.5、连续 2 轮、GT≥12。

### 3.3 24 轮轨迹与四条叙事弧

逐轮总表沿用 r8 表 3（26 个记录单元：24 发展域轮〔无 r21，跳号声明〕＋holdout-r1/r2 双窗），要点：

- **仪器弧**：r4 3D→2D 复合变更→r5 dpi 640 首个框级命中→r14 配色重建（混淆性弃权 14/14 被 reject 支捕获）→r17 dpi 1280（M1＝top 视全旗聚合弃权率〔r8 表 3 注定义，本篇主仪器指标〕，0.88 reject；呈现层约 1000px 降采样抵消原生增益=vision-encoder 上限机制观察）。仪器侧可钉住的已钉住，仪器增益存在呈现层上限。
- **判据可操作化弧**：r8 存在性判据三路出口→r13 量化版（bottom courtyard 非弃权 18/0/0→0/0/0、极差 18→0）→r19 可操作分辨条款（M1=0.461538 历史最佳）→r25 三问条款（M4＝r8 度量族之三问条款度量，1.0；定义见 r8 §5）。判据措辞是强杠杆，但不改变实例间离散。
- **假设检验范式弧**：r7 确立「预注册＋三分账；正确测出无效同样是有效证据」；null result 如实入账两例（r9 刺激缺席、r12 方差爆拉）。
- **守门-判据冲突弧**：r20 G1 字面破坏、r22 G2 0→2——处置=字母照判＋分岔教训单列，守门修订须新预注册轮。

### 3.4 三条经验观察（有界条件内）

1. **实例异质性**：单实例/轮读数受实例群方差主导（同指引 r8→r9→r10 弃权 0.222→0.727→0.286）；聚合稳与个体散并存（r24 n=6：split_half=0.018640 vs 12 格极差 0.888889）。
2. **弃权主导结构（分型口径）**：r13–r16 全部 132 条弃权旗分型——existence_other 36.4%/existence_blackdot 32.6%/contact 28.8%，三族合计 129/132=**97.7%** 属「不可负责任确认」（r8 原文口径＝按旗计数比；三族百分比之和 97.8% 系各占比独立舍入的表面差，以计数比为准）；分型器可跨语料 fail-closed 复用（注册链重放逐旗 132/132 相等）。限定：度量的是理由与判据语义的一致性，**不是**相对独立正确性标准的验证。
3. **三轴归因收束**：轴1 仪器（dpi）/轴2 仪器注记/轴3 判据内容逐一受控排除（r17/r18 reject；r23 confounded；r24 not_instance_dominated；r25 not_criterion_dominated）——残余离散=模型/输出侧固有（排除法剩余结论，非因果证明）。

**诚实定调**：24 轮联合达标线**从未满足**（recall 始终 <0.31）；in_calibrated_range 恒 False；自动分流恒 blocked——「测量未过关的判读者不应获得放行权限」是正确设计而非失败。

## 4 图像载体·holdout 与负结果链

### 4.1 冻结 holdout（mixed）

3 块外部板×2 视×n=3：letters@0.2（letters＝稳定性字母判定〔stable/mixed/unstable〕，@0.2＝按 cell〔板×视〕间弃权率极差 0.2 阈值划界——极差大＝实例间不一致＝失稳侧）——top 三板 0.8/1.0/1.0 全失稳、bottom 三 cell 全 0.0 全稳 ⇒ **mixed**（既非 stable 也非 unstable）；M1_pool=0.735294（描述性、不进门）。零 GT 纪律下只评稳定性。holdout-r2 配色版（P2-2，受控单变量）：bottom 弃权 1.0→1.0=**NOT_SUPPORTED**（预期带外）、top MAINTAINED、「bottom 高弃权=默认配色局限」方向性假设未获支持——holdout 盲读弃权行为主因不在渲染配色，在判据语义映射＋实例/组织异质性。

### 4.2 跨板 GT 复检：零命中（P2-1 recheck-r1）

19 条扩样 GT、4 新板、每格 n=3：**gt_recall=0.0（0/19，跨实例 union 亦 0）**；seed_match=0/71；abstain top=0.336。分通道重放（预注册后执行、确定性零模型）：**类别门主导 17/19**（other_advisory GT 所在板 top 非弃权旗中零 other_advisory 类旗——类别完全不交、未进几何比较）、几何门 2/19（同类别旗与 GT 框零交集）、面积比 0/19；近邻描述：10/19 GT 的最近旗是弃权旗。执行侧事故（图像通道故障死循环 19.8M token、两格实质 n=2）与 token 总账 ~32.6M 如实披露。

### 4.3 三连 reject：类别→几何→语义

- **gt-mapping-r1（类别映射修订轮）**：letter=REJECT（类别门 0/19）——类别生产侧部分打开（other_advisory 旗 0→3）但每条 GT 的同类别旗与 GT 框**全部零相交**；残余阻断转为「类别少量相交＋几何不重合」。
- **gt-mapping-r2（几何锚定轮）**：letter=REJECT——处理臂 containment 命中 0/10、对照亦 0 ⇒ H-geom 不支持、H-deep 成立=残余阻断在语义层。
- **gt-mapping-r3（发展域判据族穷举）**：letter=reject_dev_ceiling——27 配置（3 类别映射×9 空间判据）×蒙特卡洛 N=200 随机基线，双底物（原 pct/光栅锚点校正）均无任何配置达 union recall≥5/13 且 lift≥2；全族最高 recall=2/13——**即便 oracle 看数据调参，发展域可达上限 1–3/13 量级**；M1 恒等映射稳定优于 M2/M3（类别词表不是瓶颈，约束在空间/语义锚定）。
- **gt-semantic-r1（语义粒度对照轮）**：letter=reject 终局——GT-v3 现象域盒（±3mm）×对照臂 12 派：主判据 0/19、GT-v2 对照亦 0 ⇒ 在本研究有界对照内，reader 现象体系与 DRC-GT 体系**未建立可用映射**。框移校正复算（2026-09-19，仪器缺陷 +354px 发现后）：校正后 **1/19=marginal**（唯一命中，其余 18 条最大重叠 0.154 断崖）——**两口径并记纪律**：已发布 reject 维持、实质结论不翻转、引用处一律双口径。

### 4.4 reader 侧锚点与仪器分解（负结果链的机制补强）

- **anchor-reader-r1**（公开 API 双臂 glm-4.6v/4.5v，394,941 tokens；执行形态披露：公开 API 直呼＝harness 外调用形态、时点先于 R46 全项目 harness-only 政策〔2026-09-13〕，与篇一 §8.4 锚点 Phase 同口径——威胁 3「图像半执行环境＝ZCode 子智能体」指发展域/holdout/recheck 主链，锚点批另属公开 API 形态，两者并存不矛盾）：大臂 **12/12 全零旗** vs 小臂 12 旗——描述性并列锚点，为历史「模型身份 100% 未记录」缺口提供具名形态对照。
- **zero-flag-formal-r1**（36/36 call，461,470 tokens）：**R1=YES**（r1 重建装配 12 call 全零——r1 的 12/12 零旗形态可复现）；**R2=仪器包装块=载荷因子**（有/无包装块 0 vs 6 旗，单因子隔离）；**R3=P0 装配束足以出旗**（P0 装配束＝zero-probe-r1 批的消息装配形态基线代号）；**R4=残差主要在包装块**——zero-probe 的「指引×保守性交互」归因细化为「包装块＋指引组合装配」。
- **decompose-r1**（response_format 探针）：json_schema 严格形态对 GLM 不施加约束解码（marker 探针 0/3）且截断机理定版（推理吃满 max_tokens）——仪器口径=公开 API 形态用 `json_object`、禁 json_schema 严格形态跑嵌套 schema。
- **锚点 Phase（planner 侧）**：两模型 6 win 全未复现、accepted 全臂=0——与图像半互证「描述性锚点不补历史缺口」。

## 5 仪器测量学（两半共享的地基）

1. **渲染确定性复现**：同输入跨会话像素级一致（witness＋PIL 独立重算）——「图片本身」成为受控变量而非噪声源。
2. **+354px 框移缺陷与光栅实测锚点纪律**：recheck-r1 渲染件矢量/光栅框移缺陷被 V3.3 仪器批发现（主审独立像素复测逐点证实）——**凡「零命中」类几何判定，判前先验仪器**；板界基准必须用 Edge.Cuts 矢量 bbox 光栅实测交叉断言。
3. **V3.3 双层网格＋术语表**：BRIDGE-R1 24 派判定 instrument=**PARTIAL**（判定规则原文＝`PASS=D∧S∧F; PARTIAL=D≥0.9∧(S∨F不过); FAIL=D<0.9`〔bridge-r1/eval/metrics.json〕：D＝双层网格旗坐标机械可解码率、S＝同臂同板跨实例稳定性〔|Δ|≤1 阈值〕、F＝新伪影类计数——D=1.0 可解码、S 不过=网格臂弃权 Δ+0.39/+0.51、F=0）、G-PARTIAL（网格仅限 GT 派生用、术语表仅作裁决辅助）——仪器升级的降级口径如实登记；two-era 纪元记账（bare-era 26 单元 vs grid-era，跨纪元比较须持桥接数据）。
4. **哨兵门**：单图哨兵硬门（首探不呈现像素即停机零派发）在 P2-2 首次实战拦截环境级图像通道故障：三探针 97,455 token vs 无门期 19.8M 无效消耗——前置防线价值一次兑现。
5. **成本模型按组织方式分列**：单板双视组织 ~128K/格 vs 多图组织 top 207K/bottom 563K——预注册类任务成本模型勿以单点外推。

## 6 盲包载体·裁决器首演（S54）

### 6.1 设计

合成板（50×40mm、4 层，K1/K2 全层禁布区夹唯一通道 C1 容量 4.3、ANA 敏感区；K1/K2/C1/J1–J6/ANA 及 §6.2 网名 P3–P7 均为 S54 场景内部命名，非本纲领篇号或他篇臂号）7 分区 6 裁决项（J1–J6）＋严格 JSON 合同（decisions{action 枚举 detour|layer_change|narrow|no_action、options_considered≥2、reason_codes 枚举}/joint_solution_J2_J3/routing_order/data_consistency_notes，全项必答）。被试=3 个独立子智能体会话（n=1/会话；会话模型身份未随档落盘，见 §10.2）。

### 6.2 结果：5/6/6.5 与「被试抓 bug」

- 判分（满分 7）：5/6/6.5，三取二 ≥6 条件性通过。判分键 bug 双账披露 5 处（键路线 10.9 非最优 9.38；P5 垂直罚漏算——联合最优实为 ≈31.2 vs 次优 33.25，余量 ~2 非 6.5；措辞歧义；平票无规则；场景潜伏 bug ≥4 处）。
- **被试抓 bug=advisory 价值实锤**：三个会话合计抓出任务/场景自身的几何缺陷 4 处（P3 直线贴 ANA 违规、y=4 走廊穿 P3 焊盘＋P4 起端、P4↔P7 夹缝 0.6mm 封死北回引、P3↔P7 间距 ~0.45<0.5）——**V3 整板渲染 critic 24 轮没做到的「规则级缺陷归类」在结构化盲包上成立**。
- **归因分布**：克制力 0 误报（J5/J6 六中六）、规则应用强（J4 全对＋排序 2/3 精确）、联合结构 3/3 看见翻转；**弱项=基数算术**（无一会话逐项全对）。
- **架构产出**（并入纲领篇五的架构前提）：精确验证「提案权归模型、度量权归引擎」分界——V2 合同改**序数排序**（基数成本一律引擎算）；开**双通道输出**=成本最优提案＋principle_objection 注记（会话 1 以 SI 否决成本最优=人手工程师行为，应显式消费非压制）。
- caveat：纯文本/合成小板/同日 3 实例（实例群方差老教训）。

## 7 盲包载体·五模型重放与多数票（席位 A）

### 7.1 设计

V5 P3 席位 A 盲包＝结构化板描述，内嵌 **3 条播种显性缺陷（D1/D1b/D2）＋ 4 条未播种潜在缺陷（GT1–GT4）**；五模型（GLM-5.3F×2 席、DSF、千问 3.8F、GPT6）各自重放，fail-closed ingest（同型枚举违例整包拒收——首跑各 1/4 互不重叠＋违例被拒即其机制证）。词表 1.0.1（顿号措辞追加）规范化后计票。

### 7.2 结果

- 单席：GLM#1 3/4、GLM#2 2/4、DSF 3/4、千问 3.8F 3/4（播种 D1/D1b/D2 全中）、GPT6 **0/4**（仅中播种——pad 级几何盲区）。席位 A 门口径 (a)（任务书原文 V2 口径单席 run≥3）PASS 定案。
- **N=3 多数票（tally-n3.json）**：GT 映射多数＝GT1 3/3、GT2 3/3、GT3 2/3（由 N=2 期升入多数）、GT4 0/3 三席全漏；席位 4=千问单独 3/4 过席位 A 门口径 (a)。
- **N=5 计票扩编**（VALID_N=(2,3,5)，门=n//2+1=3，正式口径 N=3 不变，用户裁定授权）：**规范化多数门聚出全部 6 条规范缺陷**（tally-n5.json normalized_tally：3 条播种族 5/5＋3 条未播种族；词表 1.0.1）——GT 族多数＝**GT1 4/5、GT2 4/5、GT3 3/5、GT4 0/5 全漏**；席位排名 DSF=GLM#1=千问 3/4 ＞ GLM#2 2/4 ＞ GPT6 0/4——席位 A 门口径 (a) PASS 不变且证据链最厚。
- **GT4 0/N 稳定盲区**：五席全漏的缺陷型（pad 级几何）在投票下不可恢复——多数票放大共识面，不制造新知；盲包必须携带该类缺陷的可见信息（v5 盲包无焊盘几何〔endpoint_disclosure〕故 GT4 重放必须用 V2 原文信息量）。
- 运营证据：外部模型进出实验目录前后做目录快照（席位 4 环境越权删除盲包两件，从会话内逐字节副本重建＋哈希核销；另主审曾整树误删重放自存证件、四席重存核销恢复——两起均已恢复，详见尾部披露段）。

## 8 盲包载体·真实板投票（席位 C）

### 8.1 设计

V5 P5 收口 A 层席位 C：14 终态板（P5 收口时点世界＝⑥波对齐后、D8 换版前）终态盲包 N=3 投票（三路跨模型路由——通道代号 P1=GLM-5.3-Flash、P2=deepseek-flash、P3=GLM-5.3 独立二 pass，**非纲领篇号 P1–P6**；全部经 ZCode 子智能体通道），闭集词表（10 类）产出多数缺陷清单供差口归因消费。零票面违约=合同遵守证据。

### 8.2 结果

- **3 洁净板＋11 板共 20 条多数缺陷**（badgeleds/thin-pod/tmp108 洁净；defect-ledger 22 条=20 多数＋2 条席位 B 合同违约/展开偏差交叉入账）；全勤零票面违约；token 实测 1.16M（P1 503,465＋P2 410,165＋P3 246,789＝1,160,419）。
- **hole_to_hole-genuine 3/3 ×三板（pmod-bme280/pmod-crypto/thatmicpre-v2）**——与 wave6 判据二 genuine 行逐板吻合：投票席位独立复现了引擎侧 kicad-cli 对照发现的同一缺陷族（两证据链交叉验证）。
- **cert-completeness 五板点名 UNKNOWN 缺口**（pmod-i2c24io/om-flexgrid/stm32-ds2480-emu 各 2/3、thunderbolt-pcie-adapter/usb-gigabit-rev-e 各 3/3；投票员一致点名 selection_verdict=UNKNOWN 与 budget_tried=4/n_candidates=24 的证据缺口）——投票席位系统发现**引擎失败证书的完备性缺口**（哪块板该有证书而没有）：advisory 席位反哺引擎治理的首例。（注：会话波报告与 P5 收口件行文作「六板」，经本批对账程序化复核，机器件 vote-tally.json 与 defect-ledger.jsonl 一致为五板，以机器件为准；详见对账明细。）
- 教训（检查席也会错，跨线互证）：V6 画板线 m3 批一检查席的 bme280 SVG 缺点主张被程序化复核推翻（`state/canvas-toolchain.md:54` 运营教训条登记；篇六 §4.4 已同步补引）——席位输出恒 untrusted、消费前必经独立复核，本线与图像半同纪律。

## 9 双载体对照分析

### 9.1 主对照：0/19 vs 6/6

| 维度 | 渲染图盲读 | 结构化盲包 |
|---|---|---|
| 任务形态 | 从像素现象自由报告缺陷 | 对给定结构化对象的规则级判定 |
| GT 对齐 | 现象体系与 DRC-GT **未建立可用映射**（三连 reject） | 判定即规则语义，天然对齐 |
| 检出（对齐后） | 0/19（类别门 17/19） | 首演 5/6/6.5；重放 6 规范缺陷聚出；投票 20 条多数缺陷 |
| 弱项 | 呈现层 ~1000px 上限、类别语义映射 | pad 级几何盲区（GT4 0/N、GPT6 0/4）、基数算术 |
| 独特价值 | 全局观察（布局性拥挤、题材转移可见） | 抓 bug（任务/引擎自身缺陷）、证书完备性缺口 |
| 合同修正 | —（判据措辞杠杆） | 序数合同＋双通道输出 |

**图 1**（`figs/fig-p2-carrier-contrast.png`，另有 PDF 版 `figs/fig-p2-carrier-contrast.pdf`；生成脚本 `figs/scripts/make_fig_p2_carrier_contrast.py`）——双载体对照主图：同一项目、同一批模型家族、同纪律（预注册/fail-closed/字母裁决/独立复核）下，渲染图载体负结果链（24 轮校准联合达标线从未满足、跨板 GT 复检 0/19、三连 reject）与结构化盲包正结果链（裁决首演 5/6/6.5、五模型多数票聚出 6 条规范缺陷、真实板投票 20 条多数缺陷）的分岔呈现——结论分岔到 0/19 与 6/6 的量级，载体-任务匹配矩阵（§9.2）为其机制解释。

### 9.2 载体-任务匹配矩阵（RQ3 的回答）

- **规则级缺陷归类/裁决/审计** → 结构化盲包（或代码载体）。像素到规则语义的映射缺口是结构性的（三连 reject 的机制：DRC 判例语义落入 catch-all 类而 reader 产具体类别旗或弃权，类别完全不交）。
- **全局观察/布局级题材** → 渲染图（用户立场「图像利于全局观察」在本项目内的落点：E1 只测过判读任务、全局诊断为未测新角色——该边界如实保留，不外推）。
- **身份化与可校核** → 代码载体（篇一 E0 第三极：SVG 源码 100% 身份恢复、80/80 拦截——载体的机器可校核性与模型消费它是两回事）。
- **多数票** → 仅在共识域有效（盲包重放成立；画板**动作**生成域票荒见纲领篇六 §4.1——V6 票荒系动作级多数票在冷启动整板生成域失效，非「图像」生成域，跨载体互证口径以此为准）。

本篇结论在纲领六篇中的位置：载体-任务匹配是席位范式的前置选择问题——判读者席位（本篇）之外，提案席位归篇五（真实板零终解增量）、直接操作席位归篇六（可完成工作但有硬天花板），三者共享「席位输出恒 untrusted、消费前独立复核」的信任边界；本篇第三极（SVG 代码载体）的可靠性与治理链证据归篇一 E0/P3。

### 9.3 对部署的含义

advisory-only＋fail-closed 路由被两半共同正当化：图像半（校准不达标→自动分流恒 blocked 是正确设计）；盲包半（席位输出恒 untrusted、消费前独立复核）。**给对通道比给高分辨率有效**（r14/r15 配色无图例反致混淆性弃权 vs 盲包直接可判定）。

## 10 Threats to Validity

1. 单板 GT（发展域 13 条全来自 Rev-C 两状态；courtyard 主导）——扩样后跨板零命中本身构成新测量事实。
2. reader 模型身份：图像半 26 个记录单元模型名/版本/provider 100% 未记录（历史缺口事实不变）；锚点批（anchor-reader/zero-flag-formal）只提供具名形态对照与机制分解；盲包半 S54 首演三会话模型身份亦未随档落盘（同缺口跨载体并存，席位 A/C 五席身份有 tally 落盘对照）。
3. 图像半执行环境=ZCode 子智能体（LLM-agent-as-subject）；图像通道间歇性/窗口性故障（哨兵门防线的有效性与残余风险并存，跨环境复现前不外推）。
4. 盲包半规模：首演 3 会话同日（实例群方差）；重放 5 模型单 run；投票 N=3——正结果的量级主张以「该三批内成立」为界。
5. 载体对照非同任务同被试的受控实验：两半任务不同（自由报告 vs 给定判定）——本文主张是**载体-任务匹配**（矩阵），不是「同任务下盲包优于图像」的因果断言；该因果检验属 future work。
6. vme-wren（外部 holdout 板名）触碰史（图像半五次测量事件）沿 r8 §7.4 全文有效——三「不得」纪律＝不得合并引用、不得以纯外部板口径引用、不得回溯解释（r8 §7.4 原文），延伸适用于全部事件对。
7. GT4 盲区：五席全漏的缺陷型说明盲包信息面本身决定可判上限——「多数票聚出全部 6 缺陷」的准确口径=6 条规范缺陷（3 播种＋GT1–GT3 族）全部聚出、GT4 族 0/5 全漏。
8. 字母语义逐轮定义；禁称 precision/FPR——r8 全部度量纪律本稿同等遵守。
9. 文书-机器件读数分歧的处置先例：cert-completeness 板数在报告/收口件作「六板」、机器件为五板，本稿按「机器件为准」纪律修订（§8.2 注）——advisory 链自身的读数也须经机器件对账，与席位输出恒 untrusted 同一纪律。

## 11 Conclusion

图像半：渲染图上的缺陷判读可被测得很准（协议、分型、归因全套方法学），但**校准不到可用**——联合达标线从未满足，跨板零命中，现象体系与 DRC-GT 体系未建立可用映射（三连 reject＋仪器缺陷双口径）。盲包半：同类判读能力在结构化载体上**全部成立**——裁决首演抓 bug、五模型重放多数票、真实板投票发现证书完备性缺口。合流：**advisory 价值依赖载体-任务匹配而非多模态本身**；判读者的部署决策应从「选模型」前移到「选载体」。方法学交付：预注册盲读协议（五版本 append-only）、三分账裁决、弃权分型 rubric、双口径检出度量、仪器测量学纪律（确定性 witness/光栅实测锚点/哨兵门/呈现层上限）、序数合同与双通道输出、载体-任务匹配矩阵。

**Future work**：①同任务同被试的载体受控对照（§10.5 因果检验）；②reader 体系自建 GT 路线（reader-native，前两轮 reject 在案）；③盲包信息面工程（pad 级几何嵌入能否关闭 GT4 盲区）；④critic 消费 route package 复查包的联合闭环（与篇一合流点）。

---

## AI 参与披露（本篇）

> 口径承现行披露正本 v4（`<WORKSPACE>/tools/pcbflow/out/v4-exec/paper-ai-disclosure-r4.md`＋机读 sidecar `ai-disclosure-r4.json`；2026-09-19 批内签发，r1/r2/r3 与修正层 F-1..F-6 零改写承前，冲突处以 v4 为准）。本段只登记本篇两半的执行模式、token、审计链与 incident 增量；图像半全部窗的逐窗台账（zero-probe/anchor-reader/gt-mapping/gt-semantic/reader-native v1-v2/BRIDGE-R1/decompose-r1/zero-flag-formal-r1 及 INC-24..27）以 v4 为准，不在此复制。

### 1. 执行模式与 token（盲包半三批）

| 批 | 日期 | 形态 | 读数 | token（口径） |
|---|---|---|---|---|
| S54 裁决首演 | 2026-09-13 | 3 独立子智能体会话（n=1/会话） | 判分 5/6/6.5（满分 7）；判分键 bug 5 处双账披露（§6.2） | 未单列台账（09-13 时点判读会话未逐场计量，如实标「台账未单列」不编造） |
| 席位 A 五席重放 | 2026-09-13~14 | 5 席（GLM-5.3F×2/DSF/千问 3.8F/GPT6）×run | 单席 3/4、2/4、3/4、3/4、0/4；tally-n3/n5.json 落盘 | 未单列台账（同上；GPT6=用户粘贴主审代存 fallback 口径） |
| 席位 C 真实板投票 | 2026-09-21 | N=3 三路子智能体投票（14 板） | 20 条多数缺陷；零票面违约 | **实测 1,160,419**＝P1 503,465＋P2 410,165＋P3 246,789（run usage，SESSION-WAVE-REPORT §7） |

三批全部经 ZCode 子智能体/工作流通道，零 harness 外 LLM 直呼（SESSION-WAVE-REPORT §9 红线自查 PASS）。全纲领 token 聚合口径（多口径并记、「total=分项加总」硬校验、gap 与事故窗登记）见 `<ENGINE_ROOT>/out/paper-program-r2/TOKEN-LEDGER-AGGREGATE.md`（本篇两半各窗读数与其 §3 对账一致；S54/席位 A 无遥测为其 §9-G5）。

### 2. 审计链

- 席位 A 计票：tally-n3.json／tally-n5.json（generator=v5.seat-replay-tally 0.1.0；board_sha256/pkg_sha256 随件）；词表 1.0.1 只增不改。
- 席位 C 计票：component_b_tally.py 确定性聚合（≥2/3 多数门、tie-break P1>P2>P3）→ vote-tally.json＋defect-ledger.jsonl（advisory）；输入全集 sha256=8db1b6dd…（SET-SHA256.json，三路逐字同输入）。
- sha256 锚程序化重算（本批 R2 对账）：P5-SESSION-WAVE-TASKBOOK（1657f66e…）全等；PREREG-APPENDIX sha16（e685fd94…）全等；input-docs set_sha256（8db1b6dd…）全等。
- 负结果与瑕疵原样入账：N=3 规范化聚簇读数未随 tally-n3.json 落盘（以档案记载为据）；tally-n5.json verdict 字段「DSF 4/4」与其 per_seat 数据 3/4 不一致（生成器文案笔误，以数据字段为准）。

### 3. incident 台账（盲包半增量）

- **INC-P2-A1（席位 A·证据误删）**：主审整树 rm -rf out/v5-p3 误删席位重放自存证件——四席续跑重存＋逐项核销恢复。立规：构建器产物外的证据目录绝不整树擦。
- **INC-P2-A2（席位 A·外部环境越权删除）**：席位 4（千问）运行窗口前后 replay 盲包两件从 seat-a-replay/ 消失（用户排除人为）——从会话内逐字节副本重建＋哈希核销（8c7d84ef… 与登记全等）。立规：外部模型进出实验目录前后做目录快照（清单＋哈希）。
- **INC-P2-A3（席位 A·GPT6 代存）**：GPT6 用户过早派发未自存→粘贴主审代存（fallback 口径），判 0/4——仅中播种，逐字性以粘贴为准。
- **INC-P2-C1（席位 C·图像通道）**：会话波图像通道全窗失效（EXP-ZCODE-008），L7/L8 像素级人眼复核降级为结构校验（12/12）＋双跑字节等。
- **INC-P2-C2（席位 C·文书层读数笔误）**：会话波报告/P5 收口件/state 档案三处行文「cert-completeness 六板」，机器件（vote-tally.json＋defect-ledger.jsonl）程序化一致=五板——本批 R2 对账发现并按「机器件为准」修订正文；文书原件零回改，更正随本件与对账明细呈主审收口。
- S54 判分键 bug 5 处＝任务/判分键自身缺陷，正文 §6.2 双账披露（负面结果不隐藏）。

### 4. 信任边界与人工批准点（盲包半）

- 全部席位输出恒 untrusted：不进门、不改判据、零 GT 回写；消费前必经独立复核（席位 C 清单=advisory 供差口归因）。
- 人工批准点：席位 A 门口径 (a)＝用户 2026-09-14 裁定；N=5 计票扩编＝用户裁定授权（正式口径 N=3 不变）；U10 N=3 阵容＝用户裁定；席位 C 三路路由与 token 不设限里程碑报数＝P5 四裁定（2026-09-14）落账。
- 图像半信任边界（reader 恒 untrusted/身份落盘缺口与对照/26 记录单元口径）承披露 v4 §5。

---

## 修订注记（R2 对账定稿批 2026-10-03）

- 本稿=篇二草稿批（2026-10-03 v1）的 R2 对账定稿：上半沿 r8 已核数字（本批自抽 2 项自检通过：渲染确定性 395,916/20,071,249、P2-1 recheck 读数组，另顺带自检哨兵门 97,455 vs 19.8M 与成本分列 128K/207K/563K）；下半逐项对机器件核验（对账明细=recon/P2-RECON.md）。
- R2 修订 7 处（均按「机器件为准」纪律）：①摘要与 §8.2「cert-completeness 六板」→**五板**（vote-tally.json majority_issues 与 defect-ledger.jsonl 程序化一致 5 板；报告/收口件/state 三处「六板」为同源笔误）；②§7.1「4 条种子缺陷（GT1–GT4）」→「3 条播种显性缺陷（D1/D1b/D2）＋4 条未播种潜在缺陷（GT1–GT4）」（tally 件 seeded/unsown 两分语义）；③§8.1「D8 后世界」→「P5 收口时点世界＝⑥波对齐后、D8 换版前」（会话波执行窗 2026-09-21，D8 换版 2026-09-22）；④§7.2 N=3「聚簇 6 规范缺陷」表述重定位至 N=5（tally-n5.json normalized_tally=6 项实证；tally-n3.json 无聚簇读数，N=3 聚簇以档案记载为据）；⑤§6.1 删「GLM-5.3」模型名（S54 三会话模型身份未随档落盘，§10.2 同缺口披露）；⑥§8.2 bme280 SVG 教训句标注跨线归属（V6 canvas 线 m3，出处 canvas-toolchain.md）；⑦§10 新增威胁 9（文书-机器件读数分歧处置先例）。
- 零实验、零模型调用、零历史证据件改动；r1 草稿与 r8 原件封存零改动；state 档案零回改（cert-completeness 笔误等档案层更正建议留主审收口）。

## References（正文括注文献汇编；[1]–[10] 书目待补，[11]–[30] 为检索批 r2/r3 回写条目）

- [1] Wen et al. 2025. TACL.（§2 LLM/多模态评估方法学）
- [2] Kadavath et al. 2022.（§2 模型校准/选择性预测）
- [3] Zheng et al. 2023. NeurIPS Datasets & Benchmarks.（§2 LLM-as-judge）
- [4] Wang et al. 2024. ACL.（§2 同上族）
- [5] Nosek et al. 2018. PNAS.（§2 预注册）
- [6] Pineau et al. 2021. JMLR.（§2 预注册在 ML）
- [7] Soukup 2010.（§2 AOI/人工目检人因）
- [8] Lv et al. 2024.（§2 PCB 视觉检测）
- [9] Liu et al. 2024. DAC.（§2 LLM-for-EDA review/copilot）
- [10] He et al. 2024. TCAD.（§2 同上族）

**[11]–[30]＝本篇检索批新增条目**（题名｜作者｜年份｜venue｜DOI/arXiv｜链接；标识符原样取自 `litsearch-r3/refs/P2-candidates.jsonl`，未手工补写；候选池未给 DOI 者如实留空）：

- [11] Zhang Y., Wang J., Ge Y. 2026. Stop Comparing LLM Agents Without Disclosing the Harness. arXiv (Cornell University)｜arXiv:2605.23950｜https://arxiv.org/pdf/2605.23950（§2 组 1 载体的定义与披露纪律；候选池未给 DOI）
- [12] de Macedo S. O. 2026. What makes a harness a harness: necessary and sufficient conditions for an agent harness. arXiv (Cornell University)｜DOI 10.48550/arxiv.2606.10106｜arXiv:2606.10106｜https://arxiv.org/pdf/2606.10106（§2 组 1）
- [13] Lee J., Park C. 2026. The Agent Loop: A Survey of Control Strategies, Skills, and Harnesses for LLM Agents. SSRN Electronic Journal｜DOI 10.2139/ssrn.7186738｜https://papers.ssrn.com/sol3/Delivery.cfm/7186738.pdf?abstractid=7186738&mirid=1（§2 组 1；候选池未给 arXiv）
- [14] Raj H., Gupta V., Mahmoud A., Dumitru R.-G., Yi D. 2026. Model or Harness? An Interaction-Centric Taxonomy for Localizing Agent Failures. arXiv (Cornell University)｜DOI 10.48550/arxiv.2607.28802｜arXiv:2607.28802｜https://arxiv.org/pdf/2607.28802（§2 组 1）
- [15] Zhang S., Wang A., Sophie L. 2026. Layer-Isolated Evaluation: Gating the Deterministic Scaffold of a Production LLM Agent with a No-LLM, Regression-Locked Test Harness. arXiv (Cornell University)｜DOI 10.48550/arxiv.2606.11686｜arXiv:2606.11686｜https://arxiv.org/pdf/2606.11686（§2 组 2 载体作为受控自变量）
- [16] Li J. 2026. Where Does Exactly-Once Live? Model, Harness, and Tool-Contract Effects on Duplicate Side Effects in LLM Agents. arXiv (Cornell University)｜DOI 10.48550/arxiv.2609.29095｜arXiv:2609.29095｜https://arxiv.org/pdf/2609.29095（§2 组 2）
- [17] Cen, Zhao, Chen W. 2026. Beyond Prompts: Measuring and Optimizing LLM Tool-Agent Harnesses. arXiv (Cornell University)｜DOI 10.48550/arxiv.2609.05736｜arXiv:2609.05736｜https://arxiv.org/pdf/2609.05736（§2 组 2）
- [18] Xu T., Wen H., Li M. 2026. Adapting the Interface, Not the Model: Runtime Harness Adaptation for Deterministic LLM Agents. arXiv (Cornell University)｜DOI 10.48550/arxiv.2605.22166｜arXiv:2605.22166｜https://arxiv.org/pdf/2605.22166（§2 组 3 载体形态可编辑与可演化）
- [19] Chen M., Wang J., Liu Z. 2026. From Failed Trajectories to Reliable LLM Agents: Diagnosing and Repairing Harness Flaws. arXiv (Cornell University)｜DOI 10.48550/arxiv.2606.06324｜arXiv:2606.06324｜https://arxiv.org/pdf/2606.06324（§2 组 3）
- [20] Wang S., Qian P., Lin Y., Xu J., Chen Y., Jiang X. 2026. Phantom Guardrails: When Self-Improving Agent Harnesses Fix Failures That Never Happened. arXiv｜arXiv:2607.13083｜https://arxiv.org/pdf/2607.13083（§2 组 3 反面案例；候选池未给 DOI）
- [21] Lodha A., Varnosfaderani M. P., Chakraborty A. 2026. Less Context, Better Agents: Efficient Context Engineering for Long-Horizon Tool-Using LLM Agents. arXiv (Cornell University)｜DOI 10.48550/arxiv.2606.10209｜arXiv:2606.10209｜https://arxiv.org/pdf/2606.10209（§2 组 4 上下文工程）
- [22] Mehta A., Datta A. 2026. Plans Don't Persist: Why Context Management Is Load Bearing for LLM Agents. arXiv (Cornell University)｜DOI 10.48550/arxiv.2606.22953｜arXiv:2606.22953｜https://arxiv.org/pdf/2606.22953（§2 组 4）
- [23] Santos-Grueiro I. 2026. Ghost in the Context: Policy-Carriage Integrity in LLM Agents. arXiv (Cornell University)｜DOI 10.48550/arxiv.2605.12535｜arXiv:2605.12535｜https://arxiv.org/pdf/2605.12535（§2 组 4）
- [24] Liang Y., Chen X., Ge Y. 2026. UniToolCall: Unifying Tool-Use Representation, Data, and Evaluation for LLM Agents. arXiv (Cornell University)｜DOI 10.48550/arxiv.2604.11557｜arXiv:2604.11557｜https://arxiv.org/pdf/2604.11557（§2 组 5 tool-use 协议与评测基准）
- [25] Liu W. P., Liu Z., Dai E. 2025. MCPAgentBench: A Real-world Task Benchmark for Evaluating LLM Agent MCP Tool Use. arXiv (Cornell University)｜DOI 10.48550/arxiv.2512.24565｜arXiv:2512.24565｜https://arxiv.org/pdf/2512.24565（§2 组 5）
- [26] Liu X., Zhang Y. E., Kasprova V. 2026. AgentAbstain: Do LLM Agents Know When Not to Act? arXiv (Cornell University)｜DOI 10.48550/arxiv.2607.10059｜arXiv:2607.10059｜https://arxiv.org/pdf/2607.10059（§2 组 6 弃权与 coding agent 评测）
- [27] Weinberger S., Hozez A. 2026. Prompt-Induced Waste in Coding Agents: Reasoning, Effort, Harness Design, and End-to-End Cost. arXiv preprint｜arXiv:2608.01347｜https://arxiv.org/pdf/2608.01347（§2 组 6；候选池未给 DOI）
- [28] Huang W. E. I.-X., Lee C., Tng L., Ge S. 2026. DeepSWE: Measuring Frontier Coding Agents on Original, Long-Horizon Engineering Tasks. arXiv (Cornell University)｜DOI 10.48550/arxiv.2607.07946｜arXiv:2607.07946｜https://arxiv.org/pdf/2607.07946（§2 组 6）
- [29] Chen Y., Ahmad A., Zhou Y., Jabbarvand R. 2026. Unlocking Model Potentials Through Adaptive Multi-Agent Scaffolding for Efficient Issue Resolution. arXiv preprint｜arXiv:2606.25514｜https://arxiv.org/pdf/2606.25514（§2 组 7 多智能体席位与失败归因；候选池未给 DOI）
- [30] Chen M., Wang J., Mu F. 2026. Seeing the Whole Elephant: A Benchmark for Failure Attribution in LLM-based Multi-Agent Systems. arXiv (Cornell University)｜arXiv:2604.22708｜https://arxiv.org/pdf/2604.22708（§2 组 7；候选池未给 DOI）

（[1]–[10]＝§2 正文括注原样汇编，完整书目信息仍待纲领文献检索批补齐；[11]–[30]＝本批检索回写条目，题名/作者/年份/venue/标识符/链接全部原样取自候选池，未给 DOI 者留空未补写。）

## 统稿批注记（2026-10-03，纲领 R2 统稿席）

按大纲 §8 顺序过稿的统稿动作（数字零改动）：①头部新增术语行（判读者/席位/结构化盲包/advisory-authority/三态分层＋门号命名空间）并挂接 `TERMINOLOGY.md`；②TERMINOLOGY C-4 冲突落地——「口径(a)」4 处统一改「席位 A 门口径 (a)」（与篇四归因类 (a) 板固有同符异义，防跨篇误读）；③摘要判读者首现定义（reader/critic 归一，S-1）；④§9.1 挂双载体对照主图（`figs/fig-p2-carrier-contrast.png`）；⑤§9.2 补六篇席位范式地图互引（篇一 E0 第三极/篇五提案席位/篇六直接操作席位）；⑥披露段挂接全纲领 token 聚合总表。
- 读审处置批追加（同日，独立读审 44 条中涉本篇 8 条全部处置）：①§1「同一批模型家族」加可比性限定（跨半严格同一性不可核，§10.2）；②§1 补「0/19 vs 6/6」的 6/6 口径提示（N=5 规范化多数、GT4 不入分母）；③§3.4 97.7% 补计数比口径注（129/132；百分比和 97.8% 系独立舍入）；④§3.3/§4.1/§4.4/§5/§10.6 补 M1/M4/letters@0.2/D-S-F/P0 装配束/vme-wren 三「不得」首现定义；⑤§8.1 投票路由 P1/P2/P3 与 §6 场景内部命名消歧；⑥§4.4 anchor-reader 补公开 API 执行形态披露（先于 R46，承篇一 §8.4，与威胁 3 调和）；⑦§8.2 bme280 SVG 教训改引 `state/canvas-toolchain.md:54`（篇六 §4.4 已补同源互证句，断链修复）；⑧§9.2「图像生成域」改「画板动作生成域」；⑨补 References 汇编节（§2 括注重排、零新增）。
