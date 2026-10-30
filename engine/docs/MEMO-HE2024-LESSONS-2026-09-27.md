# 决策备忘录：He2022→He2024 教训对 pcbflow 的五条借鉴

- 日期: 2026-09-27；来源: He2024 博士论文领读会话（原文 PDF 已逐字核对关键数字；外部旁证含库内 PCBWorld/OmniRouting）
- 性质: 决策备忘录，不改动任何现役件。落地动作待主审裁量后另立任务书。
- 相关: 综述线（paper-library `ml-rl-routing/`=综述 §3 主干引文）、`freerouting-baseline-r1/REPORT.md`、`CANVAS-PILOT-R1-TASKBOOK-2026-09-24.md`

## 背景一页纸

He2022（VLSI-DAT 会议版）: DRL+MCTS 端到端布线，30×30 单层合成题成功率 100% vs 顺序 A* 75%。
He2024（同作者博士论文第 4 章）: 自建 PCBench（1182 块真实板，多数双层+真实 DRC）复测自家方法——**RL-MCTS 仅布通 2/1182（0.17%）**，且该 2 块耗时 32772s/38349s；FreeRouting 72.5%、pad-focused（第 3 章）48.1%、PcbRouter 43.5%。作者归因: 逐板冷启动无迁移 + 搜索空间爆炸致失败无对比信号；结论转向有监督/生成式。同章自证: 第 3 章在 10 块板上赢 FreeRouting 的结论，放到 1182 块上反转（输 24 个百分点）。

## 五条借鉴

### 1. 综述引用链: He2022 的 100% 必须连着 He2024 的 0.17% 一起讲

只引会议版数字=传播已被作者本人推翻的结论。综述 §3 把 HeBao2020→He2022→He2024 写成"评测方法学演进"线（无公开基准时代各测各的十块板 → PCBench 时代结论反转），同时支撑论文一"评测公平性"论点。

### 2. FreeRouting 实力线已有本地印证，用作外部锚点

He2024: FreeRouting 1182 块真实板 72.5%；本项目基线臂: 8 块 P0 板 6 块零未连通（量级吻合）。用途: ①论文一引"最强启发式仍挂约 1/4 真实板"立论问题空间开放；②v5/画板成绩单统一以此线定位，不另立参照系。

### 3. 画板形态结构性规避 RL-MCTS 两大死穴——论文一可明写，但须自证"失败可分辨"

LLM 席位天然跨板 zero-shot（无冷启动）；CANVAS-PILOT 三问之③（拒收原因直方图、逐轮连通曲线）正是 He 缺失的观测。**自查义务**: pilot 分析时单列"整轮全拒收"占比——若模型也大面积整轮失败，"无对比信号"将在 LLM 身上复发，该形态的核心卖点即不成立，须如实报告。

### 4. 对照实验补两防: 预算口径写死 + 终态分账

He2024 基准的三不公: 默认参数硬跑、各布线器迭代上限不同、"跑不动"与"布错"混算一个成功率。落地: ①v5/画板 vs FreeRouting 对照的轮数/超时预算在 prereg 冻结并对齐披露（基线臂现口径=-mt 1 + 10min，v5 侧同须写死）；②台账终态码把"预算耗尽"与"DRC 脏/未连通"分开——He 的 0.17% 混算两种死法，本项目 PASS/FAIL 纪律应做得更干净。

### 5. CANVAS 无搜索纯度守住；FAIL 退路参照 He 第 3 章

画板"无 A*/无绕行/无推挤——搜索负担归模型"是被测假设本身，小题阶段不掺引擎搜索稀释假设（He2022 教训）。若 pilot FAIL，退路=两阶段但接口焊死: He 第 3 章动态重划分（已布走线成为后续可见屏障）与画板盲包"已落铜+违例标记"同思想，盲包设计在两形态间迁移成本低。

### 附: 第三类贡献别埋没

DSN 转换器定位的"三处 v5 世界模型与真实布线器互操作缺口"（见 freerouting-baseline-r1/REPORT.md）性质上等同于 He 靠 PCBench 拿到的基准/工具/缺口类贡献——比布线器本身更可发表，应进论文一素材清单而非止步于基线报告。

## 引文定位

- He2022: `paper-library/ml-rl-routing/He2022_MCTS-DeepRL-CircuitRouting_VLSI-DAT.pdf`（5 页，译文在 translations/）
- He2024: 同目录 `He2024_TowardsAutomatedPCBRouting_PhDthesis_IowaState.pdf`（关键数字在第 4 章 PDF p.88-89，已核对）
- 旁证: `paper-library/paper1-llm-eda-routing/2607.05915_PCBWorld_…pdf`（摘要原话 "learning-based methods still lag behind rule-based routers"；其 PPO 合成板预训练+zero-shot 小板胜、大板仍负于 FreeRouting——印证"死穴是冷启动而非 RL 本身"）
- 领读记录: `paper-library/reading-sessions/2026-09-27_He2024_直接讲_工具调用记录.md`
