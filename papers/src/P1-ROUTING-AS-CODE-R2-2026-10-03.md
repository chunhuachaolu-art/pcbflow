# 篇一《Routing as Code——LLM 辅助 PCB 布线的表示、预算与规划器位置的受控实证研究》定稿 R2

<div class="release-note">

**发布说明（2026-10-30 收线归档）**：本文是 pcbflow 项目的中文技术报告（R2 内部定稿），**未经同行评审，未投稿**。文中形如 `<ENGINE_ROOT>/out/...`、`<WORKSPACE>/...` 的证据路径指向作者本机的实验证据目录，这部分没有公开；代码与核心板设计见仓库 `engine/`、`tools/`、`design/`。"主审""席位"等术语见 `TERMINOLOGY.md`。作者：赵丹琪。许可：CC BY 4.0。

</div>

---

## 摘要

大语言模型（LLM）参与 PCB 布线面临两个结构性缺口：闭源工具的性能声明不可复现（可验证性缺口），模型参与缺乏可指认的审计载体（审计链路缺口）。本文提出 **route package**——以 SVG 源码为 canonical 载体、携带机器身份字段与五具名 hash 合同的代码化布线表达——并在等信息、等预算（K=8）、同校核的受控条件下，以五臂对照（稳定序基线/确定性局部搜索/JSON 几何/SVG 源码/SVG+PNG，LLM 子智能体为被试）系统检验表示方式与规划器位置的价值。主要结果：（1）**载体可靠性**：身份恢复 50/50、负向突变拦截 80/80、局部编辑合同七门全过、双跑重放字节一致；在真实板 STM32H743 上 fail-closed 治理链完成「拦截→根因定位→精确回归→旧近似退役」四步闭环。（2）**优化收益**：等信息等预算下，主方法 SVG 臂提案合法率 11.8%，远低于确定性局部搜索的 44.6%（6/51 vs 100/224；比例差未做显著性检验），主目标相对变化 +0.048%，预注册九门四败；holdout 补覆盖至 32/32 全分母池化复判后结论维持。（3）**规划层价值**：「模型可捕获排序缺口」假设被受控检验证伪（f4-07 capture_M=0.0）；「合法率低＝接口摩擦」假设经两形态直接检验均未获支持。（4）**真实板窗与修复-排序纠缠**（本稿新增贡献）：15 窗规划序实验给出「修复即规划序替代者」的初始读数（w5/w6 字典序直接 SAT）后，家族诊断批将 55 条 shorts 家族的成因定位于载体侧建模缺陷（grid pad 循环单层阻挡漏 PTH 全层铜）而非排序自由度本身；全层阻挡修复（R55-3′）使 w5/w6 shorts 55→0 且 SAT 保持、16 个既有窗世界两臂逐窗零劣化、31 组同进程双跑字节等，E5R3 批 G1（窗 SAT 门，非本篇 P1/P2 批 G1）由 9/11 改判**全过 11/11**。同批发现引擎 `ripup_count` 恒 0 硬编码——顺序布线一锤子买卖，此前全序通过依赖旧窗世界端点互不挡与字典序运气。全部偏差追加式登记。结论：route package 使 LLM 参与布线可审计、可回滚、可重放（RQ1=是）；等信息等预算下表示方式不带来显著优化收益（RQ2=否）；优化价值不被模型在排序/分解规划层捕获（RQ3=证伪）；真实板窗的表观排序效应与载体建模缺陷纠缠，修复建模缺陷后 SAT 缺口闭合（RQ4=修复优先于排序）——模型座位应从「优化执行位」转向「治理与诊断位」。

**关键词**：大语言模型；PCB 布线；EDA；route package；fail-closed 校验；预注册实验；受控实证研究；修复-排序纠缠

---

## 1 Introduction

LLM-for-EDA 正成为热点，但布线（routing，在 PCB 上为每个电气网络生成满足间距/层/连通约束的导线几何）场景存在两个结构性缺口。其一，**可验证性缺口**：闭源 ML 布线器（如 Quilter 类产品 [W1]）的性能声明是黑盒自报，第三方既无法复现也无法审计。其二，**审计链路缺口**：即便让 LLM 参与布线，业界缺少「模型改了哪条线、哪一段、依据什么、如何退回」的可指认记录——模型输出天然不可信，而没有身份化的载体，「不可信」就无法落地为工程约束。

本文不问「LLM 能否布好线」，而问一个更可检验的问题：**LLM 应该坐在 PCB 布线管线的哪个位置？**我们把布线表达为带机器身份与 hash 链的 SVG 代码化对象（route package），在等信息、等预算、同校核的受控条件下，让 LLM 规划器与确定性算法对照。四个研究问题：

- **RQ1**：布线能否成为机器可校核的代码化对象——AI 的每次参与是否可审计、可回滚、可重放？
- **RQ2**：等信息等预算下，表示方式（SVG 源码 / JSON 几何 / PNG 图像）是否给规划器带来优化优势？
- **RQ3**：优化价值存在于管线哪一层（几何提案层还是排序/分解规划层）？
- **RQ4**（本稿新增）：真实板窗上观察到的「排序自由度效应」，有多少属于排序本身、多少属于载体建模缺陷？

贡献（与证据映射，详见 §6）：

1. **C1（正结果）**：带机器身份与 hash 链的 SVG route package 使模型参与布线可审计、可回滚、可重放——E0 四验证全过（身份恢复 50/50=100%、round-trip 最大误差 0.000000000 mm、负向突变拦截 80/80；`out/v4-experiment/e0/e0-results.json`）；P1 七门全过（`out/v4-comparative-experiment/p1/gates-p1.json`）；fail-closed 证据链在真实板完成**四步闭环**（拦截→根因定位→精确回归→旧近似退役，§6.5）。
2. **C2（负结果，本工作核心交付之一）**：等信息等预算下，**表示方式不带来显著优化收益**，且模型提案合法率远低于确定性局部搜索（比例差未做显著性检验）——P2 九门四败（C1 合法率 11.8% vs A1 44.6%；主目标相对变化 +0.048%），32/32 全分母池化复判维持（§6.3）。
3. **C3（证伪性负结果）**：「优化价值存在于规划层、可由模型捕获」的方向性假设被受控检验证伪——E5 中 f4-07 的 16.5 序空间价值对模型排序臂完全不可见（capture_M=0.0），对确定性局部搜索亦仅 1.0%（§6.4）。
4. **C4（修复-排序纠缠，本稿新增）**：真实板 15 窗规划序实验的「修复即规划序替代者」初始读数，经家族诊断批与全层阻挡修复批三段检验后修正——55 条 shorts 家族的成因是载体侧 keepout 建模缺陷（grid pad 单层阻挡漏 PTH 全层铜），修复后 G1 改判全过 11/11；「排序自由度」的表观效应大部分应归还给建模面。同批机械发现引擎 `ripup_count` 恒 0（§6.7）。
5. **评估协议**：预注册门＋fail-closed 校验＋配对统计（10,000 重采样 paired bootstrap＋双侧精确符号检验）＋双跑字节一致重放；全部偏差追加式登记。

**贡献的边界（与正结果同等醒目）**：本文是受控实证研究，不是系统性能论文。C2 的负结果是核心交付；本文不宣称「自动布线成功」或「模型布线优于算法」。V4.1 工程轨终局（`not_viable_for_full_board`）按 CLOSEOUT 对外披露义务进入本文（§6.6）。真实板实验（P3）的贡献定位是**治理链在真实板上被验证会正确拦截与回滚**，不是真板布线改进成功。

## 2 Related Work

- **确定性布线器**：KiCad 内置 push-and-shove 与 Freerouting 是开源生态两条主线 [W2]；本项目对 Freerouting v2.3.0 的 qualification 实测（TD7：0.75× 减宽边界、JVM 死锁）作为「外部引擎质量不可默认信任」的工程佐证（详见纲领篇三 §6，此处只引结论）。
- **ML/RL 布线器**：Quilter [W1]、DeepPCB [W3] 等厂商声明不可复现，构成本文「受控对照＋全链审计」动机的对照面。
- **LLM-for-EDA**：逻辑综合、RTL 生成、placement hints 等方向 [W4]。
- **人机协同治理与预注册方法学**：[W5]。
- **姊妹篇边界**：视觉判读校准全部归篇二（载体测量学）；引擎体系与等价性保持优化归篇三；不可布性归因归篇四；LLM 导引席位归篇五。本文仅在评测协议层面互引。

**本轮扩写（litsearch-r3 候选池 `litsearch-r3/refs/P1-candidates.jsonl`，2026-10-06 回写）**——下列条目全部取自候选池，题名/作者/年份/venue/DOI/arXiv/链接字段原样抄自池内 JSON，不新增池外条目，不改写上列 [W1]–[W5]：

- **（a）代码原生 EDA 工具线（Routing as Code 的工程谱系）**：tscircuit 以 TypeScript/React 描述真实电子设计 [W6]；atopile 是声明式 `.ato` 编译器，卖点是设计复用、校验与版本控制 [W7]；SKiDL 以 Python 库书写电路 [W8]；netlistsvg 由 JSON 网表直接生成 SVG 原理图 [W9]——与本文 SVG canonical 载体最接近的公开先例，但其 SVG 只承担原理图绘制，未承载布线对象身份与 hash 合同；tscircuit-autorouter 是少数开源 PCB 布线器实现 [W10]；EDACurry 是多语言网表创建/转换/改写框架 [W11]。本文的增量在于把「电路即代码」从可 diff、可复用推到**机器身份＋双跑重放一致**的合同层。
- **（b）PCB 与布线基准/工程件**：PCBSchemaGen 用奖励引导的 LLM 代码合成做 PCB 原理图设计并配结构化验证 [W12]；BenchPCNP 是 PCB 网表处理基准数据集 [W13]；tscircuit 公开 200 例 autorouting 基准问题集 [W14]。与本文的差别在评测对象——它们评网表/原理图生成，本文评「布线表示 × 规划器位置」，且把布线几何的合法性判据交给确定性 authority。
- **（c）ML/RL 布线与可布性预测**：SAAP 是面向并行布线的空间感知解析划分 [W15]；网表级 FPGA 预布局可布性机器学习预测 [W16] 与人工网表生成器驱动的早期可布性预测框架 [W17]，二者同属「引擎开跑前先判可布」的前置判据形态（与本文 §5.5 选窗可布性感知同族）；模拟 IC 布线的网表分解与候选生成 [W18]。这条线的读数多以自报精度给出，本文以预注册门＋双跑重放作读数口径。
- **（d）LLM-for-EDA 与「文本→结构」桥**：Schemato 把网表转原理图交给 LLM [W19]；Weave 以分层图布局做可验证的网表→原理图转换 [W20]；SynAlign 做网表与源代码的对齐 [W21]，是「代码↔结构双向可追踪」的直接先例；HINT 提出面向 LLM 驱动 RTL 生成的可执行硬件意图表示层 [W22]。与本文同题不同层：它们把 LLM 放在生成位，本文把 LLM 放在受治理的规划位且其原始响应恒为 untrusted 证物。
- **（e）受控评测与验证治理方法学**：NetlistBench 以 2342 例 24 类任务评 LLM 在 SPICE 网表识别与改写上的可靠性 [W23]，支持本文「文本载体不等于可校核载体」的判断；AgentRTL-Bench 主张成本感知 Pareto 评测，并直指 pass@1 对 agentic 场景是错指标 [W24]；RTL-BenchMT 以 agent 辅助分析动态维护基准、防污染 [W25]，与本文预注册门＋偏差追加式登记同向。

## 3 The SVG Route Package Contract

route package 是布线的代码化表达，其合同包含三层：

- **机器身份字段**：每个几何对象（route/via）携带 `route_id / net_id / relation_id / parent_id / layer / line_type / state / source` 身份与精确 mm 几何；颜色与线型只是 versioned legend，不承载机器事实。
- **双通道表示**：SVG 源码为 canonical（可 diff、可 hash、可重放）；PNG 投影为非 canonical 留证（字节依赖渲染器版本，显式声明不进重放链）。
- **五具名 hash 合同**（`out/v4-comparative-experiment/p0/hash-contract-v1.json`，sha256 前缀 `42fad6bd63318524`）：每个 hash 写明被哈希对象、排除字段与使用位置，显式禁止用未限定的 `manifest_sha256` 指代多个对象。

**Table 1 五具名 hash 合同**

| hash | 被哈希对象 | 排除字段 | 使用位置 |
|---|---|---|---|
| board_snapshot_sha256 | 板快照 canonical JSON | — | 冻结输入/候选基线锚 |
| reference_manifest_payload_sha256 | 参考布线 manifest payload | 渲染字段 | 对照基线 |
| candidate_geometry_sha256 | 候选几何 payload | 渲染字段 | patch 绑定/回滚校验 |
| planner_response_sha256 | planner 原始响应 | — | 证物（untrusted） |
| validated_action_sha256 | 校验后动作 | — | solver 桥唯一消费物 |

一致性由三方校验闭环保证：SVG ↔ manifest ↔ board snapshot 逐对象身份与几何比对，E0 实测零误差（浮点 1e-9 口径全字段相等、round-trip 最大误差 0.000000000 mm ≤ 容差 0.001mm）。

## 4 Governed Planning Pipeline

信任模型＝「模型恒 untrusted，机器事实只能来自确定性链」：

- **planner 响应合同**：严格 JSON、动作白名单（patch 子集 `replace_subpath / move_vertex / insert_via_candidate / reject_route_patch`；规划动作集另含 `set_route_order / prefer_corridor / prefer_layer / lock_routes / flag_suspect_region / suggest_ripup_reroute`）。
- **fail-closed 校验器**：verdict 仅 accepted/blocked；任一 patch 非法则整份响应作废——结构上不给下游留「部分可用」的消费物。
- **solver 桥**：确定性 solver 只消费 `validated_actions`，绝不触碰模型原始输出。
- **独立 checker**：候选几何经独立 cell 级 DRC；P3 真板实验中升级为 kicad-cli DRC 作为唯一几何 authority（§6.5）。
- **staging 隔离与回滚**：一切写操作发生在快照副本上，live 板零写入，批前/批后 hash＋整批回滚能力预演练。

## 5 Study Design

### 5.1 场景生成器与目标函数

- **8 个拓扑族 f1–f8**（简单点对点/拥挤通道/总线+时钟/keepout 迷宫/确定性 UNSAT/交错双层墙/层级关系/交错竖墙挤流）；板 40×30mm 双层，grid 0.25mm、clearance 0.3mm；线宽 default 0.3mm、clock 0.4mm。
- **确定性**：全部随机性由 seed=sha256(scenario_id) 派生，同 id 重生成字节一致（112/112 验证）。
- **目标函数（冻结常量）**：`objective = 1.0·length_mm + 8.0·via + 0.5·bend`；exact optimum 由 ≤4 net 穷举排列给出（证书 `exhaustive_over_permutations_v1`）。

### 5.2 数据集（两轮）

第一轮 50 场景（5 族×10）；第二轮 112 场景（dev 60/cal 20/holdout 32，含未见族 f6–f8）。两轮 serial 关系按实测口径披露：cal 与 holdout 错开，**dev serial 01–06 两轮复用同板**（同 seed，sha 实测相同）——dev 只用于冻结前试跑与合同测试，不进 holdout 结论，但分布重叠如实披露（§8）。

### 5.3 五臂定义与等预算

**Table 2 五臂定义**（holdout 覆盖经 P1-2 补覆盖后均 32/32）

| 臂 | 模型臂 | 输入表示 |
|---|---|---|
| A0 | 否 | 稳定序单次基线 |
| A1 | 否 | 确定性八方向局部搜索 |
| B1 | 是 | JSON 几何 |
| C1（主方法） | 是 | SVG 源码＋对象摘要 |
| D1 | 是 | C1＋PNG |

等预算 K=8＝每轮 ≤4 patch × 最多 2 轮；A1 获同样 8 次候选评估、同 validator/checker、同「严格改善才接受」贪心。公平性：同 board snapshot、同初始候选（A0 产出）、同硬约束。未运行臂 B0/C0/D0（单次无反馈整臂未运行，偏差 D5）——轮次反馈贡献无法分离，入 §8。

### 5.4 统计与预注册

配对统计：paired bootstrap percentile CI（10,000 重采样，确定性 PRNG 构造，种子冻结）＋双侧二项精确符号检验。预注册：P1 七门、P2 九门先于运行冻结（`protocol/experiment-plan.json`，sha 前缀 `2b9adc3d0af8f126`）；偏差 D1–D5＋U1 追加式登记，「原草案字节不改……不得用于事后放宽门槛」。

### 5.5 真实板窗研究（E4/E5，R2 增量引入）

**术语（窗世界）**：本节起「窗世界」＝窗实验的冻结载体配置（载体管线版本＋router/grid 版本＋零包代码的冻结组合，如「E4-R2 五修后」窗世界）；b1 整板与 15 个窗共构成 16 个窗世界单元——与篇三 V5 线「世界」（＝代码四树哈希＋板集＋门判据的冻结组合）**同词不同物**，本篇一律写「窗世界」以区分（TERMINOLOGY §1.4/C-1）。

- **载体**：真实 KiCad 板经 staging 链（copy→剥线→snapshot 0.1mm 网格＋keepout 阻挡建模→SVG/manifest/PNG→fail-closed validator→v4exp solver→候选写回→独立连通检查→kicad-cli 10.0.5 DRC→paired record）。
- **E4 选题**：起点锚定区豁免与选窗可布性感知（b1/b2/b3 三板）。
- **E5 选题**：**15 窗**配对实验（窗＝真实板上选出的网子集），臂＝基线序（A，字典序）vs 规划器选序（C，planner 序）；**簇键** `(board_source, frozenset(picked 网名集))` 冻结（`out/v4-e5-r3/prereg-e5-r3.md` §1，R-20 §1.4），实测 12 簇——求解等价的窗（同解复本）按簇去重后进判据，杜绝把「同一难题的两个名字」当两个数据点（w7/w8 与 w1/w2 同簇为立规首例、r3 批另发现 w10/w11 同簇复本；prereg 预写 13 簇、实测 12 簇＝D-11，判据未修订、预估数按实测修正）。
- **E4-R2 五修**（commit 268c631，主审复核 ACCEPT；批名消歧：五修落批＝E4-R2 修复批〔名目见 `REPORT-e4-r2.md` §1 五行表〕，E5R3＝五修后 15 窗重跑批、其世界＝「五修后窗世界」——§6.7(a) 同批名）：D1 绝对角判据（pad at 第三元＝**绝对角**，旧公式 `(rot+fang)%180` 重复计入 fp 旋转，六类 rot/fang 组合中四类错）/D2 keepout=铜矩形∩**solver 可达工作区**相交（裸 bbox 相交仍丢 pad77 实测定论）/D3 分离常量 3 格＋dilate 默认值重绑/D4 段级 uuid/**E5-D3** C 分支豁免补标（五修名目按 `out/v4-e4-r2/REPORT-e4-r2.md` §1 与 commit 268c631 口径）。（编号消歧：本篇三套 D 号并存各属其批——P2 批偏差 D1–D5＋U1〔§5.4〕／E4-R2 五修名目 D1–D4〔本行批内编号〕／E5R3 批偏差 D-9/D-10/D-11〔§6.7〕，互不对齐。）

## 6 Results

### 6.1 E0：载体可靠性（四验证全过）

**Table 3 E0 四验证**（`out/v4-experiment/e0/e0-results.json`）

| 验证 | 结果 |
|---|---|
| 身份恢复 | 50/50=100%（300/300 项检查通过） |
| manifest↔SVG↔snapshot 一致＋round-trip | 全字段相等（1e-9）；mm→SVG→mm 最大误差 0.000000000 mm |
| 负向突变拦截 | 80/80 blocked（未知 net_id/层错配/width 错配/坐标篡改/重复 route_id/删 endpoint/hash 错误/未知 line_type） |
| 多分辨率盲读 | 多模态子智能体不读 manifest 读 PNG，route_id 集合与 manifest 逐字符全等（3/3、8/8、5/5、8/8、10/10）；1200px 与 2400px 零差异 |

另：改色正向对照 10/10 facts 不变；整树重放双跑字节一致（含 402 文件聚合哈希）。**H1 成立：SVG 可成为可靠的代码化布线载体。**

### 6.2 P1：SVG 代码化局部编辑合同（七门全过）

**Table 4 P1 七门**（`p1/gates-p1.json`，verdict=p1_pass）

| 门 | 结果 |
|---|---|
| G1 程序生成动作被接受 | 12/12（含 2 例诚实弃权） |
| G2 非法动作拦截 | 81/81 |
| G3 身份错配拦截 | 18/18 |
| G4 rollback 哈希恢复 | 12/12 逐字节 |
| G5 未声明对象零变更 | pass |
| G6 重放字节一致 | pass（双跑 canonical 哈希 `ef2cacd43bd0ff66` 相同） |
| G7 视觉-only 不可绕过 | pass（改色后机器字段与 manifest hash 逐项不变） |

结论：SVG 作为可执行局部编辑载体的合同成立——只证明「改得对、改得住、可回滚」，**不证明「改得值」**。

### 6.3 P2 主对照：九门四败（C2 负结果核心）

**Table 5 P2 九门**（`p2/holdout/gates.json`，main_method=C1，baseline=A1）

| 门 | 判定 | 关键数字 |
|---|---|---|
| G1 候选全部独立硬校核 | pass | violations 全 0 |
| **G2 主方法合法率 ≥ A1** | **fail** | C1 **0.117647**（6/51）vs A1 **0.446429** |
| **G3 主目标改善 ≥5% 或搜索 −20%** | **fail** | 配对均值相对变化 **+0.048%** |
| G4 无关键非目标回退 | pass | — |
| G5 过半场景非 tie | pass | 非 tie 6/11 |
| **G6 跨族方向一致** | **fail** | 已见族 meanΔ +1.172（n=5）vs 未见族 −0.795（n=6） |
| **G7 模型相对 A1 净收益** | **fail** | +0.048% |
| G8 重放字节一致 | pass | run1=run2 |
| G9 无事后改门/删样本 | pass | — |

**提案级合法率**：A1 100/224=44.6%；B1 17/56=30.4%；C1 6/51=**11.8%**；D1 15/50=30.0%。配对统计（首批 n=11）：B1 meanΔ −2.333（CI95 [−4.681,−0.175]，p=0.289）、C1 +0.099（CI 含 0）、D1 −3.562（CI95 [−6.550,−0.764]，p=0.289）——B1/D1 均值更优但不显著；A0 vs A1 阳性对照显著（+0.956，p=0.0039）证明协议能检出真实差异。

**全分母池化复判（P1-2，32/32；`out/v4-comparative-experiment/p1-2-coverage/`，主审复核 ACCEPT）**：门定义逐字沿首批不放宽，优化门重判 PG-G2 0.0625 vs 0.446429（FAIL）、PG-G3 +0.28%<5%（FAIL）、PG-G5 非 tie 11/28（FAIL）、PG-G6 族方向不一致（FAIL）、PG-G7 净收益不成立（FAIL）——**首批结论在全分母上确认，非翻案**。池化配对：C1 4/17/7、meanΔ +0.573、CI95 [−0.159,+1.441]（含 0）、p=0.549；B1 CI 不含 0 但 p=0.607 不显著且批次分层后新批 win=3/17——仅描述性并列，不构成 B1 优势结论。批次异质性如实披露（首批模型版本/采样参数 100% 未记录 vs 新批 harness 实报，两批不可做跨批能力归因）。

**互补性观察（不作胜出声明）**：模型臂收益集中在未见族与拥挤族（D1 相对 A1 改善 4.8–12.7），A1 在简单族明显更好——G6 方向不一致失败的来源同时是互补性证据。

### 6.4 E1 与 f4-07 规划缺口、E5 受控排序位证伪（C3）

- **E1 主判定**：H2 not_supported——SVG+PNG 规划未带来改善（配对 n=8，objective +0.66%、search_nodes +38%）；纯文本 +11.03% 劣化；仅像素 10/10 被 fail-closed 拦截。
- **P0 计量纠偏**：「协议字面」与「工程主目标」分列——bend 分支字面满足（−5.769%）而工程主目标 +0.662% 变差；历史判定不翻转、不授予 executor 资格。「局部指标改善不得解释为整体优化胜出」的方法学素材。
- **f4-07 规划缺口**：cal-f4-07 存在 exact optimum **171.5**（穷举证书），A/B/C 全组产出 188.5，gap +9.9%，未被任何规划臂捕获——「规划层可捕获的价值」客观存在。（口径注：+9.9%＝router 口径 gap 17.0＝188.5−171.5；E5 的「16.5 序空间价值」＝cmp 空间口径 gap_S＝S 臂基线 188.0−OPT 171.5＝9.62%——两口径并存、混用即失效〔DEV-E5-001：f4-07 A0=188.5 router vs 188.0 cmp〕。）
- **E5 受控排序位检验**（12 件 exact-optimum 全集；臂 M 模型排序/S 稳定序/A1 局部搜索/OPT 冻结件）：**capture_M=0.0**（f4-07 的 16.5 序空间价值对模型排序臂完全不可见，M≡S——预提交策略坍缩为字典序）；capture_A1=0.0104；M vs A1 0win/0tie/8loss（p=0.0078，排序位不替代局部搜索）；capture_mean_M=0.875（已达最优场景全部保持，排序位至少不劣化）。形态边界如实登记：planner 为执行者自身分轮降级形态＋单策略点估计＋prereg 前污染披露——不外推「模型排序必然坍缩」，但**在本受控检验内排序位假设未获任何支持且主读数为零**。配套投影消融 G5.1=not_separable_at_n8（PROJ/SVG 合法率 0.3191/0.3191 全同）。
- **C3 终版表述**：排序位「模型可捕获缺口」假设已被受控检验证伪；f4-07 缺口在几何提案层与排序规划层均未被任何臂捕获；余下可陈述的只有缺口存在性与互补性观察。

### 6.5 P3：真实板治理链实证（STM32H743 Rev-C）

框架定位：贡献是**治理链在真实板上被验证会正确拦截与回滚**（fail-closed 首次真板实证）。

- **设置**：板快照副本（192 网/2372 段/358 via〔V4 staging 快照口径，基底 v2 §6.5 登记〕；live 只读，pre/post hash 相等；口径调和〔caliber-r1 C-1 定论，2026-10-05 回写〕：同板同网表两口径——192＝全量网（含 32 个 unconnected- 前缀 NC 焊盘网）、160＝具名网〔`state/archive/pcb-routing-history-2026-09-27.md:43,104`〕，192＝160+32；机器登记＝pcbflow `out/revc-a1/coverage.json` totals＋SN-2（2026-08-29 起在案，非新发现），原「快照展开」措辞证伪删除）；net 白名单=预注册确定性规则，冻结规则产出 1 批 6 网；kicad-cli DRC 唯一 authority；判据=零新增 severity-error＋连通不劣化。
- **结果（如实=blocked）**：确定性倒角候选 6 件全部通过 advisory 预检并落板文本，kicad-cli 判 **+1 新增 severity-error**（clearance 0.1571<0.2mm，error 220→221）→ 协议 fail-closed：整批 blocked＋回滚＋不修补不重试；连通不劣化成立（55→55）；回滚后 staging==live。
- **四步闭环**：①真板拦截（如上）→②根因定位（advisory 预检 pad=min(w,h)/2 近似漏掉长条焊盘长轴半程）→③精确内核回归（Minkowski 核精确焊盘几何，预测 0.157043 vs kicad-cli 0.1571，差 5.7e-05≤容差 0.01；独立 checker 双引擎交叉零分歧；**负对照**：旧近似对同几何放行——漏报复现）→④旧近似退役（预检点替换为 v4_1 `check_patch`，旧函数删除＋防回退测试，历史 patch 在链上被判违例，全链零「旧拦新放」反向松弛）。
- **处置账本**：5 条 entry 链式验证零错误；真实处置=DIS-P3R-04（reject，human_authority）+DIS-P3R-05（known_open）；机器事实不受处置翻转——+1 clearance 旗恒在，reject 是人工权威对机器事实的处置确认、非清旗。
- **方法学素材**：advisory 恒不能替代 authority 的正面实证；DRC 违例重锚定效应（「计数差」与「违例身份差」须分开报告）；baseline 非干净板只看零新增。
- **治理链工程佐证（V4.1 E2，只读引用）**：22 用例多层合成板对拍，v4_1 双引擎与 kicad-cli 判定一致 22/22、数值 max diff 0.0mm。

### 6.6 V4.1 工程轨终局（只读引用）

- **E7 外部板 paired**：2 板 8 批（ADC 2+RP2040 6）**全部 rollback、零 commit、零板面残留**。challenger 在候选层有行闭合能力，但**每一条候选闭合都伴随新增 severity-error**，双口径 commit 硬门零放行；对照 freerouting v2.3.0 archived（RP2040：新增 error +648/+50、unconnected −66——连通性收益同样不满足「零新增 error」工程标准；ADC DSN 导出被静默阻断 not_comparable）。判读按 prereg 对账式：challenger error 口径反优、unconnected 口径劣 ⇒ `differential_worse_than_freerouting=true`。
- **S2 停机规则完整触发-驳回-再触发-接受史（强制披露义务）**：①主支触发（E4：rip-up 五级穷尽后全板归属改善 0/57=0.0%<10%；编号消歧：此 E4＝**V4.1 工程轨** rip-up 探针批，非 §6.7 v4exp 线「真实板首个 SAT 窗」的 E4，两者为不同引擎线——V4.1 细格点求解器有五级 rip-up，而 v4exp 树 `ripup_count` 恒 0〔§6.7(d)〕；行口径＝Rev-C 51 行残网（`state/archive/pcb-routing-history-2026-09-27.md:183` 原文「Rev-C 51 行五级穷尽改善 0/57」，51=残网行、57=五级穷尽改善检查面计数，两项计数在档案原文并存；构成定论〔caliber-r1 C-2，2026-10-05 回写〕：57−51＝2+4——2＝APPLY-1 封存战役先落（3V3＋GPIO_PE2 两行，非本支功劳、prereg 预注册另列）、4＝GND 行按 opens.csv 65=61+4 先例排除〔E4R-031..034〕，数字不变））→②用户驳回（R32：用户裁定权对预注册停机规则的显式例外，非计算错误翻案）→③备用支再触发（E7 差分劣于 freerouting）→④接受（R38：登记 `not_viable_for_full_board`，终局收缩为审计局部编辑工具＋模型排序/诊断位）。**任何对外证据引述 V4.1 全板结论必须并引完整四步史。**
- **对本文的方法学意义**：失败终局本身=可证伪方法学贡献——预注册停机规则在真实工程线上被触发两次、驳回一次、接受一次的全链裁决史，是「负结果与预注册纪律」主张的最强工程轨例证。

### 6.7 真实板窗：规划序、家族诊断与全层阻挡修复（C4，R2 增量主体）

本节是基底 v2 之后闭合的证据链，按时间三段呈现。全部数字已对账（对账明细见 `recon/P1-RECON.md`）。

**（a）E4：真实板首个 SAT 窗与五修**

E4 r1（起点锚定区豁免 opt-in＋选窗可布性感知，`out/v4-e4-r1/REPORT-e4-r1.md`）：**b1 10/15→SAT 15/15=真实板首个 SAT**（sn 1,480,122→320,847）；b2 起点零展开死解除（搜索节点 0→189）。E4-R2 五修批（268c631，主审 ACCEPT，`out/v4-e4-r2/REPORT-e4-r2.md`）：**b1=首个 SAT＋DRC shorts=0 的真实板窗**（57→0，逐类吻合 diag-shorts57：旋转判据 31＋中心点收录 18＋分离常量 8；`out/v4-e4-r1/diag-shorts57/DIAG-SHORTS57-2026-09-24.md` §0/§3）——五修逐一对应 57 条 shorts 的三类成因，修复面与诊断面逐类对账（D1 消 31〔n007×U50 pad6/7/8〕＋D2 消 18〔n015×U56 pad77〕＋D3 消 8〔n012/n013 贴 2 格并行〕＝57，与实测清零逐类吻合）。w5 解锁未保持/w6 保持如实（REPORT-e4-r2 §5）。

**图 1**（`figs/FIG-P1-B1-SHORTS57-FAMILY-R1.png`，脚本 `figs/scripts/FIG-P1-B1-SHORTS57-FAMILY-R1.py` 直读 `items-classified.json`＋两版 `drc-baseline-summary.json`/`solver-run-baseline.json`，断言层验证 57=31+18+8 类分解与修复前后 SAT 保持）——b1 真实板窗 DRC shorts 家族分解：57 条 shorts 按成因三族（旋转判据 31／中心点收录 18／分离常量 8）与五组明细呈现，五修（D1/D2/D3）逐类消解后 57→0 且 b1 保持 SAT。

**（b）E5R3：15 窗重跑与「修复即规划序替代者」初始读数**

五修后 15 窗重跑（`out/v4-e5-r3/REPORT-e5-r3.md`，prereg sha16 `98b29726c6e631b9` 数据产生前冻结；主审复核 ACCEPT＝commit `ec2a748`，十二面独立复算全过，`exec/LEAD-REVIEW-E5R3-2026-09-25.md`）：

- **E5R3-G1（窗 SAT 门）部分过 9/11**：9 窗 SAT 且 shorts 归零（b1=0）；w5/w6 两窗 SAT 但带 55 条 shorts 新家族——按预注册判据 FAIL，移交诊断（后续见 (c)）。形态＝窗南界 y≈80.8 走廊走线×U14 密排 PTH 焊盘（E5R3 报告 D-10 时按「非选中 PTH」描述；经 familydiag 诊断与勘误，终版口径＝**picked 网端点 pad**——U14＝F15 连接器，其涉案 pad 恰为各自 picked 网的端点 pad 本身，本板 picked 网全为恰 2-pad 网；措辞更正史＝D-10 原文「非选中」→2026-09-28「picked 网非端点 PTH」→同日勘误终版「端点 pad」，见 `REPORT-FAMILYDIAG-R1.md` §3.4/§7.1 与 `out/v4-r55-1/ABANDONMENT-r55-1.md`）。
- **死窗两型分化**：**全封型出局**（beergauge：A 臂松动 0→3–6、C 臂三窗全 SAT——预收紧并非不可布，而是当时的建模面过度封锁）；**毒网型保持**（anthc 26/27/25 无一 SAT，换窗世界稳固）。
- **修复即规划序替代者（初始读数）**：w5/w6 字典序直接 SAT（r2 时需 planner 解锁 failed→SAT，r3 字典序直接 SAT）⇒ staging 保真度×排序可相互替代——修复载体缺陷与改变规划序两条路在当时读数下等价。
- **w4 劣化跨窗世界稳固**（A 23→C 7，r2 同构 20→7）：排序自由度的负向实例——换序既能解锁也能劣化。
- **簇级去重立规**：w7/w8 求解等价复本（r2 发现）⇒ 簇键 `(board_source, frozenset(picked))` 冻结、实测 12 簇（prereg 预写 13、实测 12＝D-11）；G5 prompt 逐字零改动（附录复刻 sha 同）。
- **G1 分母推导（读者可复算）**：prereg G1 定义＝「**全 SAT 窗** DRC shorts=0」（`prereg-e5-r3.md` §2）——15 窗中 w4（failed@n008）与 anthc 三窗 w13–w15（毒网型全 failed）共 4 窗为 failed、不入「SAT 窗归零」分母，SAT 窗恰 11（9 归零＋w5/w6 两窗）；b1 整板另列亲证归零（shorts=0/310）。

**（c）familydiag-r1：55 家族的成因定案**

诊断批（动态工作流 `v4-e5-family-diag`，prereg sha16 `8aa9280feaacd032`，110/110 归因 verified，用户 2026-09-28 四裁追认；`out/v4-e5-familydiag-r1/REPORT-FAMILYDIAG-R1.md`）：

- **H3 主成因成立**：keepout 生成规则 `:460` 网∈picked⇒不生成 keepout——picked 网端点 pad 零 keepout，他网走线可整排穿越，55 条 shorts 全部归属该规则面（110/110 逐条 verified；组计数 w5/w6×U14 pad6/7/8＝18/19/18×2，`items-classified.json` row_count=110）。
- **H1 不支持**（反事实封锁预证：ko 在位即挡）；**H2 支持但带口径冲突**（格宇宙窗 ±7 vs 收录域窗 ±2 环带盲区，另立 R55-2 加固批）。
- **勘误边界（如实披露）**：familydiag §7 勘误使「修复侧推论」（端点集收紧可归零）作废——本板 picked 网全为恰 2-pad 网、端点=全集，R55-1 冒烟实证 no-op；**机械检验面不受影响**（H3 规则识别、110/110 归因、H1/H2 判定均维持）。

**（d）R55 修复批链：三停两成与机制级真根因**（`out/v4-r55-1/REPORT-R55-1C.md`）

- R55-1 端点集收紧=**no-op 废冻**（picked 网全 2-pad 端点=全集，「非端点」前提作废，keepout 116→116 零变化，`ABANDONMENT-r55-1.md`）。
- R55-1b 全 pad keepout：封锁生效（w5 shorts 55→0）但**自端点死锁**（锚区豁免仅本体格）；R55-1c 豁免环放大：逃逸通但**容量级联**（≈7/13 网、PH4-first 探针换序只换谁死）⇒ **全局 keepout 路线架构性不成立**。
- **机制级真根因**：snapshot 的 grid pad 循环**单层阻挡漏 PTH 全层铜**（snapshot 无 thru 字段）——keepout 建模在层维度上错了，不是「要不要豁免」的参数问题。
- R55-3（thru-only 版）确定性 SMOKE FAIL（prereg sha16 `a33ecddd8c767cde`）：F55 连接器 14 支全 SMD（thru=False），B.Cu 区开放后早期网改道吃掉 PH4 走廊（三种子同果 sn=1,890,120，确定性非混沌；`deviations-r55-3p.md`）。
- **重量级机械发现**：`router.py` 的 `ripup_count` **恒 0 硬编码**（`:414`/`:479`，本稿对账时亲验原文在位）——引擎无任何 ripup 机制，顺序布线一锤子买卖；E5R3 全序通过=旧窗世界端点互不挡＋字典序运气，而非引擎具备冲突化解能力（该缺口移交纲领篇三/篇四的 ripup 工程批议程）。

**（e）R55-3′ 终修与 G1 改判全过**（`out/v4-r55-1/REPORT-R55-3P.md`）

修复=**一切 pad（含 SMD）全层阻挡＋按网豁免＋声明层锚区豁免**（载体运行时方法替换，包文件零改动，keepout 语义=E5R3 原样；prereg sha16 `5a11fcb495e442be`）：

- **四判据门全过**（SMOKE/G-R1/G-R2/G-3）**＋PRE 机械预检全过**：w5/w6 shorts 55→0 且 SAT 保持（w5 sat/27 路由、w6 sat/18 路由）；**16 个既有窗世界×两臂 vs E5R3 逐窗零劣化**（sat→sat/failed→failed 全同构、原零窗保持 0——修复没有靠放宽任何既有难题，`compare-e5r3.json` 16 行、G-R2 sat_regressions 空）；31 组同进程双跑全字节等（`double-run-records.json` 31 条全 byte_equal=true）。
- **E5R3-G1 改判全过 11/11＋D-10 闭账**（2026-09-28 深夜用户裁定「双双落账」，收口件 REPORT-R55-3P；呈裁项清单见其 §4）。

**图 2**（`figs/FIG-P1-R55-3P-FOUR-GATES-R1.png`，脚本 `figs/scripts/FIG-P1-R55-3P-FOUR-GATES-R1.py` 直读 `compare-e5r3.json`/`double-run-records.json`/w5/w6 门读数件，prereg sha16 `5a11fcb495e442be` 程序化重算断言）——R55-3′ 修复批四门读数：(a) w5/w6 短路 55→0 且 SAT 保持（w5 sat/27 路由、w6 sat/18 路由）；(b) G-R2 十六窗世界零劣化矩阵（sat→sat/failed→failed 全同构，sat_regressions 空）；(c) G-3 三十一组同进程双跑字节等条带（byte_equal 全过）。

**（f）C4 判读：修复-排序纠缠的修正叙事**

- E5R3 时代的「修复即规划序替代者」在修复链闭合后获得更准确的读法：**表观排序效应大部分应归还给建模面**——w5/w6 的 SAT 缺口主因是 keepout 建模缺陷（H3 规则面＋层维度单层阻挡）而非「需要更聪明的序」；修复建模缺陷后全部 11 窗 SAT，无需任何排序智能。
- 该修正**不触及** C3 的证伪（f4-07 capture_M=0.0 在合成场景受控检验内成立）与 C2 的负结果（P2 合成域表示无收益）——三组实验对象不同（合成场景 vs 真实板窗），各自结论独立。
- **毒网型死窗（anthc 26/27/25）在修复后窗世界保持零 SAT**——真·板固有死窗的首个跨修复对照证据，其归因（板固有/引擎/规则）移交纲领篇四的三分类体系。
- 方法论收束：**先修建模、再谈智能**——在载体建模存在已知缺陷时，任何「规划层自由度」读数都携带建模混淆；受控修复批（16 窗世界零劣化门＋双跑字节等门）是把混淆剥离出来的仪器。

## 7 Discussion

**表示可靠 ≠ 便于消费，接口摩擦假设未获支持。**C1 弱在 planner 需从 SVG `d` 属性复原 polyline 并做帧换算——「接口摩擦而非模型能力」的解释假设经两形态直接检验均未获支持：工具辅助降级形态（G5.1 投影消融）not_separable_at_n8（PROJ/SVG 合法率全同 0.3191）；真 spawn 形态（p01-respawn-r1，8 独立子智能体）双口径均不支持且方向反转（letter=marginal）。历史 C1 11.8% 低合法率的成因仍无已证解释。

**互补性**：模型赢未见/拥挤族、确定性赢简单族——混合管线是预注册方向；族分层显著性已测但不构成结论（批次异质＋符号检验不显著）。

**修复-排序纠缠（新增）**：C4 链给出一个可迁移的实验设计教训——「换序能救」类读数必须先过「建模缺陷剥离」门（既有窗世界零劣化＋等价保持），否则排序自由度会被系统性高估。E5R3 若停在初始读数，本文会错误宣称「修复与排序可相互替代」；诊断批把功劳正确归还给 H3 规则面，修复批链再把规则面归因深化到层维度建模——**两级归因（规则面→层维度）本身是「表象归因须经机制级复核」的例证**。

**治理成本**：模型臂每 12 场景约 0.7–2.0M subagent tokens；P1-2 补覆盖批 token=51,889,016（用户裁定不设上限）；P3 真板 DRC 6/30、1.5h——治理开销可控但非零，须与收益主张一同披露。本篇线 token 全口径（P1-2 两轮分项、锚点 Phase 双臂、历史臂量级 gap）见 `<ENGINE_ROOT>/out/paper-program-r2/TOKEN-LEDGER-AGGREGATE.md` §2。

**f4-07 启示**：16.5 序空间价值客观存在但当前无任何已测臂能捕获；当前动作子集不支持跨层多段链重构（每 via 固定 8mm 成本是最大残余浪费）。

## 8 Threats to Validity（主动全披露）

1. **模型臂 holdout 覆盖（已解除）**：首批 12/32 降功效判定；P1-2 补覆盖后 32/32 全分母，优化门池化重判维持 FAIL（§6.3）。批次异质性披露：首批模型版本/采样参数 100% 未记录 vs 新批 harness 实报——不可做跨批能力归因。
2. **场景主体为合成**（P1/P2/E1/E5 合成部分）；真实板证据=P3 治理链＋E4/E5R3 真实板窗，且后者在 §6.7 证明其初始读数携带建模混淆（已修复并改判）。
3. **数据集措辞**：dev serial 01–06 两轮复用同板（如实披露）。
4. **模型身份披露**：历史实验 planner 模型版本/provider/采样参数 100% 未记录（27/27 缺失）；固定模型锚点复现件（锚点 Phase，126 calls/2,728,073 tokens，GLM-5.3/GLM-5.3-Flash 双臂）只证明「冻结协议＋固定具名模型」形态的可复现性，不补历史记录缺口；执行形态（harness 外 API 直呼、时点先于 R46 全项目 harness-only 政策）随引述如实披露。
5. **两轮制单反馈环；单一 planner wrapper**；B0/C0/D0 未运行（D5）。
6. **配对可比 n**：首批 n=11、池化 n=28（4 个 unsat 诚实弃权）。
7. **执行环境**：LLM-agent-as-subject；AI 参与披露现行 v4（INC 台账至 27）。
8. **E5R3 初始读数的建模混淆（新增）**：本稿 §6.7 已完整呈现「初始读数→诊断→修复→改判」链；引用 E5R3 任何中间读数时必须并引 (c)(d)(e) 三段，不得单独引用「修复即规划序替代者」初始结论。
9. **R55-3′ 修复的边界（新增）**：修复批只覆盖 keepout 建模面（全层阻挡），不触碰引擎 ripup 缺口（`ripup_count` 恒 0 在修复后依然在案）；「16 窗世界零劣化」的门定义见 prereg `5a11fcb495e442be`，不能外推为「修复对所有未来窗世界零劣化」。
10. **55 家族形态描述的措辞演进（本稿对账新增披露）**：E5R3 报告原文（D-10）以「非选中 PTH」描述该走廊形态，familydiag 批两跳更正为「picked 网端点 pad」（U14＝F15 连接器，涉案 pad 恰为 picked 网端点 pad 本身）；E5R3 报告为冻结件零回写，本稿按勘误终版口径书写并随文保留更正史（§6.7(b)）。

## 9 Conclusion

**RQ1=是**——route package 使模型参与布线可审计、可回滚、可重放（E0/P1 全门＋P3 真板治理链四步闭环＋真实处置落账）。**RQ2=否**——等信息等预算下表示方式不带来显著优化收益（11.8% vs 44.6%；+0.048%；32/32 池化维持）。**RQ3=负**——排序位「模型可捕获缺口」假设被证伪（capture_M=0.0）。**RQ4=修复优先于排序**——真实板窗的表观排序效应经诊断批定位为载体建模缺陷（grid pad 单层阻挡漏 PTH 全层铜）；全层阻挡修复后 w5/w6 shorts 55→0、16 窗世界零劣化、E5R3-G1 改判 11/11——在建模缺陷未剥离时，排序自由度读数被系统性高估。模型座位应从「优化执行位」转向「治理与诊断位」；引擎侧的 ripup 缺口（`ripup_count` 恒 0）与毒网型板固有死窗分别移交纲领篇三、篇四。

**Future work**：①接口摩擦假设的完整包直接检验；②动作空间扩展至多段链重构；③R55-2 收录域加固批（格宇宙全域对齐，任务书在案）；④真 ripup 工程批（引擎面）——③④两批的执行排序截至 2026-10-03 待用户裁（用户 09-28 裁定的后续排序「R55-2→真 ripup」在案，任务书 §F-5 口径）；⑤毒网型死窗的三分类归因（篇四承接）。

## 10 Artifacts、许可与披露

- License：代码 Apache-2.0；板（STM32H743 Rev-C）CERN-OHL-P-2.0；DOI=Zenodo+GitHub（发布动作待项目所有者执行）。
- 板开源归档：`artifact-release/revc-board/` 19 文件；README 依 PR-3 如实写 `production_signoff_ready=false`。
- 脱敏与外发扫描：S2 critical=0；P1-1C 75 条发现全分类。
- AI 参与披露：现行 v4（`out/v4-exec/paper-ai-disclosure-r4.md`，INC 台账至 INC-27）；LLM-agent-as-subject 执行形态、模型身份缺口、人工批准点清单全部进 artifact README 与本文尾部披露段。
- **R2 增量产物面**（本节路径均为 pcbflow 仓 `<WORKSPACE>/tools/pcbflow/` 下绝对位置）：`out/v4-e4-r1/`（含 `diag-shorts57/DIAG-SHORTS57-2026-09-24.md`＋`items-classified.json` 57 行）、`out/v4-e4-r2/`（五修，REPORT+deviations+tests）、`out/v4-e5-r3/`（REPORT+prereg sha16 `98b29726c6e631b9`+paired-summary.json+15 窗产物）、`out/v4-e5-familydiag-r1/`（REPORT+prereg sha16 `8aa9280feaacd032`+hypothesis-verdicts.json+items-classified.json 110 行+check_1..7）、`out/v4-r55-1/`（REPORT-R55-1C/R55-3P、ABANDONMENT-r55-1、prereg-r55-1{,b,c}.md 与 -3.md/-3p.md 及 sha16 台账、compare-e5r3.json、double-run-records.json、deviations-r55-1c/3p.md）；主审复核件 `exec/LEAD-REVIEW-E4-R1/E4R2/E5R3-2026-09-2*.md`（E5R3 复核 ACCEPT 入库 commit `ec2a748`）；引擎代码锚 `pcbflow/v4exp/router.py:414/:479`（ripup_count 恒 0）。
- 可复现性素材：freeze-inputs 全量 hash、四组双跑重放字节一致、G8/G9「无事后改动」门、deviations 追加式台账。

## References（沿用基底 v2 检索级核对）

- [W1] Quilter (quilter.ai). Fully Autonomous PCB Layout. https://www.quilter.ai/
- [W2] KiCad Project. PCB Editor Documentation. https://docs.kicad.org/ ；Freerouting. https://github.com/freerouting/freerouting
- [W3] InstaDeep. DeepPCB: AI PCB Routing. https://deeppcb.ai/
- [W4] R. Zhong et al. LLM4EDA. arXiv:2401.12224, 2024.（勘误：原稿标注 2023 与 arXiv 编号 2401〔2024-01〕不一致，按编号年份改 2024）
- [W5] B. A. Nosek et al. The preregistration revolution. PNAS 115(11), 2018.；Y. Chang et al. A Survey on Evaluation of Large Language Models. ACM TIST 15(3), 2024.

**扩写条目（litsearch-r3 候选池 `litsearch-r3/refs/P1-candidates.jsonl`，2026-10-06 回写；题名/作者/年份/venue/DOI/arXiv/链接逐字段原样取自池内 JSON，池内 doi 与 arxiv_id 皆空者只写题名+作者+年份+venue，不造标识符）**：

- [W6] tscircuit. tscircuit/tscircuit — Create real electronics with Typescript and React. GitHub repository (engineering), 2024.
- [W7] atopile. atopile/atopile — Design circuit boards with code! Get software-like design reuse, validation, version control and collaboration in hardware; starting with electronics. GitHub repository (engineering), 2023.
- [W8] devbisme. devbisme/skidl — SKiDL is a library that lets you design electronic circuits using Python. GitHub repository (engineering), 2016.
- [W9] nturley. nturley/netlistsvg — draws an SVG schematic from a JSON netlist. GitHub repository (engineering), 2016.
- [W10] tscircuit contributors. tscircuit/tscircuit-autorouter (open-source MIT PCB autorouter). GitHub (TypeScript), 2026.
- [W11] Nicola Dall'Ora, Enrico Fraccaroli, Renaud Gillon, Franco Fummi. EDACurry: A Multi-Language Framework to Create, Translate, and Manipulate Transistor-Level Netlists. 2025. DOI: 10.36227/techrxiv.174741927.75152825/v1. https://www.techrxiv.org/doi/pdf/10.36227/techrxiv.174741927.75152825/v1
- [W12] Huanghaohe Zou, Peng Han, Emad Nazerian, Mafu Zhang, Zhicheng Guo. PCBSchemaGen: Reward-Guided LLM Code Synthesis for Printed Circuit Boards (PCB) Schematic Design with Structured Verification. arXiv:2602.00510, 2026. DOI: 10.48550/arxiv.2602.00510. https://arxiv.org/pdf/2602.00510
- [W13] 杰 杨. BenchPCNP: Benchmark Dataset for Printed Circuit Board Netlist Processing. Figshare, 2025. DOI: 10.6084/m9.figshare.30020125.v2.
- [W14] tscircuit. tscircuit/autorouting-dataset-01 (200 tscircuit autorouting benchmark problems). GitHub (benchmark dataset), 2026.
- [W15] Chen Liu, Hongxin Kong, Lang Feng, Wenchao Qian, Wuxi Li. SAAP: An Efficient Spatial-Aware Analytic Partitioning Algorithm of VLSI Netlists for Parallel Routing. arXiv:2604.16357, 2026. DOI: 10.48550/arxiv.2604.16357. https://arxiv.org/pdf/2604.16357
- [W16] Seif Orabi, Dina Tantawy, Ashraf Salem. Netlist-Based Pre-Placement FPGA Routability Prediction via Machine Learning. SSRN Electronic Journal, 2026. DOI: 10.2139/ssrn.7091261.
- [W17] Daeyeon Kim, Hyunjeong Kwon, Sung-Yun Lee. Machine Learning Framework for Early Routability Prediction with Artificial Netlist Generator. Design, Automation, and Test in Europe (DATE), 2021. DOI: 10.23919/date51398.2021.9473966.
- [W18] Vaishnavi Venkatesh. Netlist Decomposition and Candidate Generation for Analog IC Routing. OakTrust (Texas A&M University Libraries), 2019. https://hdl.handle.net/1969.1/186249
- [W19] Ryoga Matsuo, Stefan Uhlich, Arun Venkitaraman, Andrea Bonetti, Chia-Yu Hsieh. Schemato -- An LLM for Netlist-to-Schematic Conversion. arXiv:2411.13899, 2024. DOI: 10.48550/arxiv.2411.13899. https://arxiv.org/pdf/2411.13899
- [W20] Gulgonul, Senol. Weave: Verified Netlist-to-Schematic Conversion via Layered Graph Layout. arXiv:2607.03835, 2026. DOI: 10.48550/arxiv.2607.03835. https://arxiv.org/pdf/2607.03835
- [W21] Sakshi Garg, Jose Renau. Aligning Netlist to Source Code using SynAlign. arXiv:2501.00921, 2025. DOI: 10.48550/arxiv.2501.00921. https://arxiv.org/pdf/2501.00921
- [W22] Tairan Cheng, Yi Liu, Dongsheng Zuo, Zhengyuan Shi, Hongji Zhang. HINT: Toward an Executable Hardware-Intent Representation Layer for LLM-Driven RTL Generation. arXiv:2608.07625, 2026. DOI: 10.48550/arxiv.2608.07625. https://arxiv.org/pdf/2608.07625
- [W23] Jiarui Ma, Jianghan Wang, Yuheng Ma. NetlistBench: Evaluating LLM Reliability in SPICE Netlist Recognition and Manipulation. arXiv:2608.12197, 2026. DOI: 10.48550/arxiv.2608.12197. https://arxiv.org/pdf/2608.12197
- [W24] Mysore supreeth. AgentRTL-Bench: Cost-Aware Pareto Evaluation of Multi-Agent RTL Generation. MLArchSys 2026 Poster, 2026. https://openreview.net/pdf?id=IjdFUDnm6s
- [W25] Jing Wang, Shang Liu, Hangan Zhou. RTL-BenchMT: Dynamic Maintenance of RTL Generation Benchmark Through Agent-Assisted Analysis and Revision. arXiv:2605.15537, 2026. DOI: 10.48550/arxiv.2605.15537. https://arxiv.org/pdf/2605.15537

**r4 中文轴补充条目（2026-10-06 litsearch-r4·浏览器批回写）**：以下 [C1]–[C12] 为中文文献编号，与本篇既有文献编号命名空间并行（同号不同物，承 r3 批同类声明）。条目全部取自 r4 中文候选池 `litsearch-r3/refs/P1-r4-cn.jsonl`（源＝《计算机辅助设计与图形学学报》站点检索接口题录，r4 批 60 检索词枚举 1762 条去重后按轴打分唯一分配；PDF 全部落盘、sha16 逐件对账、fitz 首页题名核验 OK/OK_PARTIAL，52 件 CMap 损坏件未入池待 OCR）；题名/作者/年份/卷期页原样转录池字段（题名含期刊平台 HTML 标记者去标记、文字不变），池未给 DOI 者如实标注、不造标识符。

**组一·高层次综合/行为建模/工艺映射**——中文侧的「代码→电路」自动化代际谱：VHDL 行为建模（1999）、高级综合优化（2017）、RTL 工艺映射（2002）与逻辑综合约简（2018）——与本篇代码原生 EDA 主张同域不同代。
- [C1] 石峰, 刘明业. 1999. 多级流水线结构高层次VHDL语言行为模型的研究[J]. 计算机辅助设计与图形学学报, 1999, 11(4): 320-323.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=3ee92dce-692b-4220-8092-ffef955496eb（r4 中文轴）
- [C2] 卫丽华, 朱鹏程, 管致锦. 2018. 基于L-ESOP约简的量子线性电路逻辑综合算法[J]. 计算机辅助设计与图形学学报, 2018, 30(8): 1579-1588.｜DOI：10.3724/SP.J.1089.2018.16567｜https://www.jcad.cn/cn/article/exportPdf?id=19a02398-5989-44f8-aa15-289c9f176e6c（r4 中文轴）
- [C3] 马磊, 刘强, 徐松. 2017. 基于代码转换的Zynq-SoC高级综合优化方法[J]. 计算机辅助设计与图形学学报, 2017, 29(7): 1372-1379.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=c14ea023-b947-4dfa-a28e-50c09d493b47（r4 中文轴）
- [C4] 周海峰, 林争辉. 2002. 基于规则的寄存器传输级ALU工艺映射算法的研究[J]. 计算机辅助设计与图形学学报, 2002, 14(4): 289-291,305.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=f39d1ead-0a4d-461c-b74d-303bb46bc77e（r4 中文轴）

**组二·SoC/系统级设计方法与验证**——SoC 设计方法学（电源/地网络优化、软硬件协同建模、结构自动划分、测试调度、IP 激励验证、BDD 底层技术）——设计流程自动化的中文方法学邻域（题录级定位、未做全文复核）。
- [C5] 李巍, 蔡懿慈, 洪先龙. 2003. SOC设计中的浮动压焊块电源/地线网络设计和优化[J]. 计算机辅助设计与图形学学报, 2003, 15(3): 249-254.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=519996db-d5b7-4872-b3aa-384baf8582df（r4 中文轴）
- [C6] 崔小乐, 程伟. 2009. SoC测试访问机制和测试壳的蚁群联合优化[J]. 计算机辅助设计与图形学学报, 2009, 21(4): 461-466.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=ac54f4e7-fba9-4cca-8318-2863db2240ae（r4 中文轴）
- [C7] 邵晶波, 马光胜, 刘晓晓. 2009. SoC测试调度的进程代数模型[J]. 计算机辅助设计与图形学学报, 2009, 21(4): 493-499.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=69d77dc7-ede2-4879-800b-029cb11e8b4a（r4 中文轴）
- [C8] 王大伟, 熊志辉, 李思昆. 2004. 基于OCP通信的SoC虚部件级软硬件协同建模方法[J]. 计算机辅助设计与图形学学报, 2004, 16(11): 1557-1561.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=885d30a6-ca9a-4c5b-84f8-4ecf12b9802a（r4 中文轴）
- [C9] 李达, 侯义斌, 黄樟钦, 肖春华. 2011. 面向MPSoC系统多特征的模糊动态调度算法[J]. 计算机辅助设计与图形学学报, 2011, 23(8): 1447-1454.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=4596d2ce-130e-4669-85d4-5f3027784e23（r4 中文轴）
- [C10] 殷燎, 黄凯, 张欣, 孟建熠, 葛海通, 严晓浪. 2010. 基于虚拟SoC平台的IP正交激励验证方法[J]. 计算机辅助设计与图形学学报, 2010, 22(8): 1399-1405.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=923246dd-f9cc-426e-960c-5146d2603736（r4 中文轴）
- [C11] 韩睦华, 刘雷波, 魏少军. 2009. 基于模板的SoC结构自动划分方法[J]. 计算机辅助设计与图形学学报, 2009, 21(5): 680-687.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=27af12b2-cfe3-40be-a944-529322c7956b（r4 中文轴）
- [C12] 张镭, 林争辉, 吕宗伟. 2002. 利用不等BDD检测对称变量[J]. 计算机辅助设计与图形学学报, 2002, 14(2): 101-104.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=3139b6c4-bde5-4136-a35b-b1d522a25ba8（r4 中文轴）

**r4 加厚补充条目（2026-10-06 litsearch-r4b，用户裁「全面加厚」）**：[C13]–[C38] 续接上段编号；题录全部原样取自增量池 `litsearch-r3/out/r4b-additions.jsonl`（镜像 `refs/P1-r4b-cn.jsonl`；阈值 2.0、封顶上调后的最优轴唯一分配；题名含平台 HTML 标记者去标记、文字不变，未给 DOI 如实标注）；verdict=OK_OCR 者为 r4 批 CMap/扫描件经本地 RapidOCR 题名对账（覆盖度≥0.75）升级件。

**组一（续）·高层次综合/行为建模/工艺映射**
- [C13] 王伦耀, 夏银水, 陈偕雄. 2012. 逻辑函数的双逻辑综合与优化[J]. 计算机辅助设计与图形学学报, 2012, 24(7): 961-967.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=f30ac24e-a579-4653-abc4-5fe3598e62f5（组一（续）·高层次综合/行为建模/工艺映射；OK_OCR）
- [C14] 徐明强, 管致锦, 倪丽惠. 2012. 基于关联选择的可逆逻辑综合算法[J]. 计算机辅助设计与图形学学报, 2012, 24(9): 1218-1225.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=4fac5c08-5f8c-48d4-b885-1058069f5129（组一（续）·高层次综合/行为建模/工艺映射；OK_OCR）

**组二（续）·SoC/系统级设计方法与验证**
- [C15] 储著飞, 夏银水, 王伦耀, 翟军. 2014. 多电压SoC引线压焊供电引脚分配及电源网络拓扑优化[J]. 计算机辅助设计与图形学学报, 2014, 26(9): 1501-1508.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=871e6e9e-f95f-4e66-9282-7fe4e1a9b1eb（组二（续）·SoC/系统级设计方法与验证；OK_OCR）
- [C16] 闫佳琪, 骆祖莹, 唐亮, 赵国兴. 2013. 考虑温度对漏电流功耗影响的MPSoC结构级热分析方法[J]. 计算机辅助设计与图形学学报, 2013, 25(11): 1767-1774.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=4478f116-cab2-47c6-bdb1-2d36398cf7a3（组二（续）·SoC/系统级设计方法与验证；OK_OCR）
- [C17] 张广飞, 汪文祥, 蒋毅飞, 苏孟豪. 2011. 高性能多媒体SoC分组访存调度算法[J]. 计算机辅助设计与图形学学报, 2011, 23(9): 1585-1592.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=c4951c00-7083-491c-a299-47b6e64e5a16（组二（续）·SoC/系统级设计方法与验证；OK_OCR）
- [C18] 曾献君, 孙绪红, 曾芷德. 1999. 长临界组合通路的重构算法[J]. 计算机辅助设计与图形学学报, 1999, 11(4): 309-312.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=25b7bff3-a294-4f1d-8fd6-4a2292143606（组二（续）·SoC/系统级设计方法与验证）
- [C19] 吕宗伟, 林争辉, 张镭. 2001. 基于二分图完美匹配的布尔匹配算法[J]. 计算机辅助设计与图形学学报, 2001, 13(11): 961-965.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=d107570b-1b37-4c18-9454-c61ad067b8d2（组二（续）·SoC/系统级设计方法与验证）
- [C20] 谢巍, 刘明业. 2001. 控制流综合中省略状态化简的可行性[J]. 计算机辅助设计与图形学学报, 2001, 13(8): 679-683.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=af6557bd-dfe6-48d9-a493-bc5eff1cdae1（组二（续）·SoC/系统级设计方法与验证）
- [C21] 来金梅, 章勇, 姚庆栋. 2000. 视频编码器片上系统集成中软硬件协同设计方法的研究[J]. 计算机辅助设计与图形学学报, 2000, 12(6): 468-472.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=0379ac24-5ecf-426a-9e57-8e45a4038d6c（组二（续）·SoC/系统级设计方法与验证）
- [C22] 郑赟, 黄国勇. 2002. 通过遗传算法进行系统级软硬件划分[J]. 计算机辅助设计与图形学学报, 2002, 14(8): 731-734.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=e0703db3-ca59-4124-9819-10d7b162d817（组二（续）·SoC/系统级设计方法与验证）
- [C23] 王云峰, 刘志鹏, 边计年. 2006. 高层次综合与布图规划相结合的方法与技术[J]. 计算机辅助设计与图形学学报, 2006, 18(9): 1438-1445.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=a7c60b07-4582-482c-84f6-7f0dfb0bef04（组二（续）·SoC/系统级设计方法与验证）
- [C24] 王克胜, 唐璞山. 2002. 一种采用规划方法的宏模块布局算法[J]. 计算机辅助设计与图形学学报, 2002, 14(5): 413-416.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=3e78e188-4774-4c29-bc64-d83f8a30861a（组二（续）·SoC/系统级设计方法与验证）
- [C25] 欧阳一鸣, 韩倩倩, 梁华国, 黄正峰, 汪秀敏. 2014. 面向非全互连3D NoC可靠通信的分布式路由算法[J]. 计算机辅助设计与图形学学报, 2014, 26(3): 502-510.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=743e7353-b9fc-4ee6-90c3-f3d86d12723b（组二（续）·SoC/系统级设计方法与验证）
- [C26] 王佳文, 李丽, 易伟, 潘红兵, 张宇昂, 侯宁, 张荣. 2011. 3D NoC映射问题的动态蚁群算法[J]. 计算机辅助设计与图形学学报, 2011, 23(9): 1614-1620.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=54dd4eb2-5ea6-434c-84f0-64ed0ceb9110（组二（续）·SoC/系统级设计方法与验证）
- [C27] 常政威, 熊光泽, 桑楠, 江维. 2009. 基于电压岛的能量和可靠性感知NoC映射[J]. 计算机辅助设计与图形学学报, 2009, 21(1): 19-26.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=66a7fe50-3fa2-4c16-9d9a-e6256da8306d（组二（续）·SoC/系统级设计方法与验证）
- [C28] 何寒娜, 方芳, 王伟, 陈田, 郭金良, 任福继. 2019. 改进模拟退火遗传算法的3D NoC低功耗映射[J]. 计算机辅助设计与图形学学报, 2019, 31(4): 681-688.｜DOI：10.3724/SP.J.1089.2019.17157｜https://www.jcad.cn/cn/article/exportPdf?id=221168ed-be7a-4bc8-bd5a-2f114aea8494（组二（续）·SoC/系统级设计方法与验证）
- [C29] 来金梅, 林争辉, 李珂. 1999. 树状结构多芯片组件互连网络延迟的研究[J]. 计算机辅助设计与图形学学报, 1999, 11(1): 85-88.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=dfa37b18-9e6f-4436-b577-44f34201996d（组二（续）·SoC/系统级设计方法与验证）
- [C30] 戴斌华, 陆涛涛, 王泽毅, 洪先龙. 2004. 3D互连电容快速提取的新途径——介质积木库法[J]. 计算机辅助设计与图形学学报, 2004, 16(3): 343-347.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=e4b4557d-5477-49f5-9483-1e4a06035a7e（组二（续）·SoC/系统级设计方法与验证）
- [C31] 古江春, 王泽毅, 洪先龙. 2000. 层次式直接边界元计算VLSI三维互连电容[J]. 计算机辅助设计与图形学学报, 2000, 12(8): 635-640.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=6b04c15a-c55a-4873-afb8-cae79def0e73（组二（续）·SoC/系统级设计方法与验证）
- [C32] 古江春, 王泽毅, 洪先龙. 2000. 互连寄生电容器中屏蔽导体的快速判断[J]. 计算机辅助设计与图形学学报, 2000, 12(10): 721-725.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=80b0c206-2de3-4e9d-9ed4-a9c8ee6541bc（组二（续）·SoC/系统级设计方法与验证）
- [C33] 方蜀州, 汤小波, 王泽毅, 洪先龙. 2000. 集成电路矩形互连线二维电容及随频率变化电感的联合计算方法[J]. 计算机辅助设计与图形学学报, 2000, 12(12): 887-890.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=32bf7a56-cc04-4d32-b018-c245afef9f28（组二（续）·SoC/系统级设计方法与验证）
- [C34] 刘德彦, 喻文健, 王泽毅. 2003. 复杂3D寄生电容器的虚拟多介质切割[J]. 计算机辅助设计与图形学学报, 2003, 15(2): 180-186.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=19cd1db1-737a-43ec-9383-97d77c2f0ca6（组二（续）·SoC/系统级设计方法与验证）
- [C35] 周强, 蔡琪, 洪先龙, 蔡懿慈. 2003. PhyD-XML:VLSI物理设计数据标记语言设计与实现[J]. 计算机辅助设计与图形学学报, 2003, 15(7): 773-777.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=f43ebc7b-e9f0-4226-86a7-70de1e5c17f8（组二（续）·SoC/系统级设计方法与验证）
- [C36] 马雪娇, 夏银水, 尹浩凯. 2018. 基于AXIG重构的功耗优化[J]. 计算机辅助设计与图形学学报, 2018, 30(12): 2344-2352.｜DOI：10.3724/SP.J.1089.2018.17141｜https://www.jcad.cn/cn/article/exportPdf?id=c810362e-1e3f-4461-a8cc-dce5c350497c（组二（续）·SoC/系统级设计方法与验证）
- [C37] 赵思思, 夏银水, 张骏立, 厉琼莹. 2017. AXIG及其基于双逻辑的面积优化[J]. 计算机辅助设计与图形学学报, 2017, 29(7): 1380-1388.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=a905b985-62c7-4530-8758-543ea985834b（组二（续）·SoC/系统级设计方法与验证）
- [C38] 郝亚男, 杨海钢, 路宝珠, 崔秀海, 张茉莉. 2012. 改进的基于属性不变量生成和数学归纳法的时序逻辑优化算法[J]. 计算机辅助设计与图形学学报, 2012, 24(9): 1232-1240.｜DOI：候选池未给｜https://www.jcad.cn/cn/article/exportPdf?id=cdc0798a-ac3a-4ba9-80c3-927c93487db4（组二（续）·SoC/系统级设计方法与验证；OK_OCR）



---

## 修订注记（R2 对账定稿 2026-10-03）

- 本稿=论文纲领 R2 篇一对账定稿：以 r1 草稿（2026-10-03，冻结）为底，按任务书 §A-1 完成增量节全量对账后修订。对账结论：25 项核对通过、3 处按机器件修订、1 处口径澄清、零 gap；逐项明细（含机器件路径+JSON 键/行号）见 `<ENGINE_ROOT>/out/paper-program-r2/recon/P1-RECON.md`。
- 三处修订：①摘要/§6.7(b) 55 家族形态措辞按 familydiag 勘误终版更新为「picked 网端点 pad」并在 §8.10 新增披露条目（D-10 措辞两跳更正史随文保留）；②§5.5 五修第五项「D5」→「E5-D3」（`REPORT-e4-r2.md` §1 与 commit 268c631 口径）；③§5.5 D1 括注「pad at 第三元=fang」→「pad at 第三元=绝对角」（REPORT-e4-r2 §1 权威表述；commit 268c631 消息中「=fang 坐实」为 U50 单例巧合表述、非一般规律，U56 即 fang=0/rot=90 反例）。一处澄清：§6.7(e) 门结构写明「SMOKE/G-R1/G-R2/G-3 四判据门＋PRE 机械预检」（prereg-r55-3p §2 口径）。
- prereg sha 锚四个均程序化重算吻合（python hashlib sha256 前 16 位）：familydiag `8aa9280feaacd032`、R55-3′ `5a11fcb495e442be`、R55-3 `a33ecddd8c767cde`、E5R3 `98b29726c6e631b9`。
- 基底 v2 的附录 A（逐主张证据映射）与 13 组负载承重数字抽查记录按任务书口径继续有效，本稿不重复。
- Future work ③④ 排序按任务书 §F 口径标注「截至 2026-10-03 待用户裁」，未代裁。
- 零实验、零模型调用、零历史证据件改动（r1 与 state 档案零回改）。

## 统稿批注记（2026-10-03，纲领 R2 统稿席）

统稿动作（数字零改动）：①TERMINOLOGY C-1 落地——§5.5 新增「窗世界」首现定义（与篇三 V5 世界合同同词不同物），全文 15 处「世界」按 V4 语境改齐「窗世界」（16 个既有窗世界/跨窗世界稳固/旧窗世界/修复后窗世界等）；②头部新增术语行（窗世界/臂号与门号命名空间/V4 窗级 sat-failed 引证口径）并挂接 `TERMINOLOGY.md`；③挂接两张新图（图 1 b1 shorts 57 家族分解、图 2 R55-3′ 四门读数，路径 `figs/`、脚本直读机器证据 JSON＋断言，本批已抽验两脚本断言层与 §6.7(a)(e) 正文读数一致）；④§7 治理成本段挂接全纲领 token 聚合总表。
- 读审处置批追加（同日，独立读审 44 条中涉本篇 9 条全部处置）：①摘要/C2 删「显著低于」（比例差无显著性检验，改「远低于」并注检验缺失）；②摘要/§6.7/§9 裸「G1」加 E5R3 批前缀（与本篇 P1/P2 批 G1 同号不同物）；③§6.4 补 f4-07 双口径注（gap 17.0=router 口径 188.5−171.5=+9.9%；16.5=cmp 口径 188.0−171.5=9.62%，DEV-E5-001）；④§5.5 五修批名改「E4-R2 五修」（机器件=REPORT-e4-r2 §1+commit 268c631）并补三套 D 号编号消歧；⑤§6.7(b) 补 G1 分母 11 推导（prereg「全 SAT 窗」：15−w4−anthc 三窗=11）；⑥§6.5 补 192 网/160 网口径调和注〔后经 caliber-r1 C-1 定论闭合：192＝160+32 同板同网表两口径、原「快照展开」措辞不成立——§6.5 现行注已按定论改写（2026-10-05）〕；⑦§6.6 补两个 E4（V4.1 工程轨 vs v4exp）与 51 行/57 计数消歧；⑧[W4] arXiv 2401 年份改 2024。

---

## AI 参与披露（篇一专项段）

**口径来源**：现行披露正本 v4（2026-09-19 批内签发，`<WORKSPACE>/tools/pcbflow/out/v4-exec/paper-ai-disclosure-r4.md`；r1/r2/r3 承前零改写，冲突处以 v4 为现行口径）。以下按 v4 框架＋篇一线（V4/V4.1/E4/E5R3/familydiag/R55，v4 签发之后 2026-09-24~28 闭合的增量）如实登记。

**一、执行形态**。本文全部实验由 AI 智能体基础设施执行（planner=LLM 子智能体，「LLM-agent-as-subject」），主智能体派发＋独立复核（LEAD-REVIEW 亲跑脚本复算，非转述）。E5R3 的 planner 作答=ZCode 主会话亲执（r1/r2 先例沿续，prompt v1 逐字冻结）；familydiag-r1=动态工作流执行（run dwfrun-75700aa7，判读/检验/落盘在工作流内完成、主审收口在会话内复核补产）。

**二、模型身份缺口**。历史实验 planner 模型版本/provider/采样参数 100% 未记录（27/27 缺失），固定模型锚点复现件只证明「冻结协议＋固定具名模型」形态的可复现性、不补历史记录缺口（v4 §框架承前，详见基底 v2 §8.4）。

**三、incident 台账（v4 承前至 INC-27，篇一线增量如实开列）**。v4 之后篇一线新增的事件按机器件登记如下（未编 INC 号、以各批 deviations/勘误件为准，吸收进下一版披露汇编时统一编号）：

1. **E5R3 两处非阻断叙事瑕疵（E-1/E-2，2026-09-25 主审复核发现）**：E-1＝报告 §4.5/D-11「w10/w11 解非逐位等」失实（实测两臂 candidate+routes 全等，仅 sn 差 0.17%，误报方向=低估复本强度）；E-2＝D-9「r2 同窗 152」参照标错（r2 实测 129、152=五修后窗世界正确值）。两处勘误随 `exec/LEAD-REVIEW-E5R3-2026-09-25.md` 入档，E5R3 报告为批产物冻结件不回改。
2. **familydiag-r1 过程偏差三条（2026-09-28 用户四裁追认，`deviations-familydiag-r1.md`）**：①冻结未重呈——呈裁门单轮结构致用户未在冻结前见过完整判据文本，事后核验+追认兜底（工作流呈裁门须支持多轮的教训）；②产物目录/清单偏离冻结件（原始输出滞留工作流会话内，追认后主审补产齐套）；③prereg 授权行占位符未回填（冻结件零回写、原状登记）。
3. **familydiag §7 勘误四件（2026-09-28「授权全套」裁定）**：成因链「非端点」→「端点」、修复推论作废（R55-1 no-op 实证）、check_4 结论边界补注、D-10 措辞二次更正。
4. **DEV-4 红线事故（R55-1C 批，2026-09-28）**：探针未绑 OUT 覆写 `out/v4-e4-r2/w5/` 三件，跨进程不可恢复（求解器跨进程哈希种子敏感、双再生 sha 不等实证；损失=字节级非结论级，原终态已载 REPORT-e4-r2 §2.3）；RESTORATION-INCIDENT 注记＋E5R3 参照指针在案＋用户追认；教训=ad-hoc 必经驱动、探针走 tmp 沙箱。
5. **R55-3′ PRE 门首跑失手（非事故，如实记录）**：预检脚本选错网验 F55-1（本是 PG5 自家 pad），补丁正确性经解剖证实后改判（`deviations-r55-3p.md`）——「预检断言的网-pad 归属先从 area-selection 实读、勿凭记忆」。

**四、人工批准点（篇一线 09-24~28 裁定链）**。R-15（diag-shorts57 只读诊断授权）→R-18（E4-R2 修复批）→R-20（E5R3 任务书冻结 sha16 `5a42d410e3e4693b`）→familydiag 立项呈裁＋prereg 冻结→四裁追认（追认/R55-1 立项/R55-2 立项/deviations 触碰授权）→R55 链「废冻重立 1b」「先补序探针」「授权全套」→R55-3′ 立项（选项文本含修复定义）→「双双落账」（G1 改判全过 11/11＋D-10 闭账）→后续排序裁定「R55-2→真 ripup」。全部裁定有登记件在案（USER-RULINGS/收口件/ABANDONMENT）。

**五、token 与成本面**。本稿（R2 对账批）零模型调用、零实验；对账所涉 token=复核侧会话成本（不入实验台账）。E5R3/familydiag/R55 各批均为机械执行（零 LLM 调用面：familydiag 七检验为脚本双跑+独立确认员，R55 链零 LLM/git/网络）。

**六、负结果与偏差同权重披露**。E5R3 G1 部分过（9/11）如实申报、w5/w6 未归零移交；R55 链三停（1 no-op/1b 死锁/1c 级联/3 SMD 分岔）全量归档；全部 deviations 追加式登记、冻结件零回写。
