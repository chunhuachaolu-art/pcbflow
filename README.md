# pcbflow：一次 LLM for EDA 的个人尝试（终版归档）

[![DOI](https://zenodo.org/badge/1439661232.svg)](https://zenodo.org/badge/latestdoi/1439661232)

> **English abstract.** pcbflow is a solo research project (Sep–Oct 2026) that asked one question:
> *where, if anywhere, does a large language model actually help in a PCB routing pipeline?*
> It contains a from-scratch deterministic router (**V5 engine**), a seven-stage KiCad design-flow
> compiler (**pcbflow**), an STM32H743 4-layer core board used as the hard test case, about a hundred
> pre-registered experiment batches, and six Chinese technical reports.
> **Main conclusion:** across every placement we tried, the LLM was most useful as an
> **evaluator of routing results** (reading structured verdict data and attributing failures).
> Almost every other role, such as proposing net order, guiding the router, drawing copper directly, or acting as a routing
> agent, produced **negative or null results** under matched controls. The negative results are
> published on purpose. The project is **closed**; this repository is a frozen archive, not a maintained tool.

---

## 一句话结论

**在布线流水线里，LLM 最适合做"布线结果的评估者"；让它出主意、指挥引擎或直接画铜，在对照实验里几乎都是负结果或零结果。**

这个结论来自约 100 个预注册实验批次。每批都在执行前冻结判据和哈希，结果由确定性代码和 KiCad DRC 机械核验。负结果和正结果一样入档、一样公开。

## 这是什么

起点很朴素：拿 KiCad 的推挤式布线器（A* 系）当对照基线，试试 LLM 能不能在 PCB 布线里帮上忙。两个月下来，项目长成了下面这几块：

| 目录 | 内容 | 状态 |
|---|---|---|
| [`engine/`](engine/) | **V5 布线引擎**（从零写的确定性布线器：协商式布线、拆线重布、失败证书、KiCad 导出/DRC 适配），以及 V6 画板直绘、V7 分层布线、V8 席位外派这几条实验线的代码 | 冻结于 executor 0.13.0 |
| [`tools/pcbflow/`](tools/pcbflow/) | **pcbflow 七级设计流编译器**：⓪约束编译 → ①结构枚举 → ②可布性预检 → ③协同布局 → ④布线 → ⑤检查 → ⑥签核；另含 V4 实验引擎（`pcbflow/v4exp`） | 冻结 |
| [`tools/pcbagent/`](tools/pcbagent/) | pcbflow 依赖的布线/检查 agent 底座 | 冻结 |
| [`design/coreboard/`](design/coreboard/) | **STM32H743 SoM 核心板 Rev-C**：70×70 mm、4 层、KiCad 10，含原理图、PCB、网表、BOM、引脚表。整个项目最难的那块真实板 | 未投产，见下文 |
| [`firmware/`](firmware/) | 核心板上电自检固件（SDRAM 测试等） | 未上板验证 |
| [`papers/`](papers/) | **六篇中文技术报告**（PDF + Markdown 源 + 图） | R2 稿，未投稿 |
| [`docs/`](docs/) | 研究过程总结、V5 里程碑披露、复现说明、语料与第三方材料说明 | — |
| [`results/`](results/) | 关键机读结果：V5 里程碑证据清单、Freerouting 对照、自改进实验预注册与总报告 | — |

## 主要发现

完整论证见 [`docs/RESEARCH-SUMMARY.md`](docs/RESEARCH-SUMMARY.md) 和 `papers/`。下面每条都有预注册判据和机械复核。

**LLM 作评估者：正结果**

- **表示层效应**：同一个"读懂布线失败"的任务，给模型结构化意图包（多层占用图 + 网表邻接 + 约束清单）时召回率 0.82，给 SVG 图时只有 0.03。两次独立批次复现，差值分别为 +0.79 和 +0.70，CI95 都不含零。**瓶颈在表示，不在模型。**
- 模型能可靠地**读判据、做归因**（解释某条网为什么布不通），但**自评自己的作品系统性偏高**：27 个席位全部自报满额，实际只完成 1–8/N。所以评估要读外部判据，不能读模型的自我报告。

**LLM 作提案者 / 指挥者 / 画手：负结果或零结果**

- 让模型直接掌握网序选择：配对净收益 −2.75% 和 +0.0%。两代席位是同一个画像：读得懂，但不敢用。
- 多轮反馈席位：14 块板终局增量为 0。迭代改进只出现在已经失败的板上，最终解没有变。
- 逐板配置预测器（自改进实验 E1）：47/47 块板退化成同一个配置，没有打过随机固定配置基线（0.56 对 0.56）。
- 模型直接在画板上画铜（V6）：能画出第一块通过 KiCad DRC 的板，同板连通度也从 0/9 提到 8/9；但三块板没有一块全连通。
- SVG 盲图判读（V4 E1）：holdout 配对下没有检出增益。*这只说明"这种表示 + 这一代模型"没有增益，**不等于视觉通道没有价值**。更强的模型和更好的视觉表示都没有测过。*

**引擎和方法学上的机制发现**

- **删除-回填零改进定理**：在顺序布线得到的 DRC-clean 解上，删掉一条网再重布，87/87 次改进都是 0。改进只能来自重排序。这决定了 V5 的分权："提案权归模型，度量权归引擎。"
- **撤除顺序零效应**（1802 臂穷举）：累积撤网的终态和撤除顺序无关，价值全在"撤哪些网"（也就是归因）上。
- **拆线重布经济学**：在中等封锁的几何下，拆线重布严格优于绕行（绕行溢价 +24%）。
- 布局传导：分层管线中，布局侧信号把布线终态冲突行数降低了 88.6%，端点全保。
- 方法学教训："判据 bug 会伪装成实验失败"在项目里实录了五例；kicad-cli DRC 存在非确定性，外部权威判据必须钉死运行口径。

## 诚实边界：这个仓库**不**声称什么

- **V5 没有达到立项门。** 立项门是"真实 holdout 板上 ≥5 块 DRC-clean"，实测**可布域 4/4 全净、六板全量 4/6**，差 1 块，而且差距是结构性的（详见 [`docs/V5-MILESTONE.md`](docs/V5-MILESTONE.md)）。"中等规模板正常跑出可用板子"这个目标没有实现。
- **核心板没有投产。** `production_signoff_ready = false`：没有送板厂，没有制造、装配和上电。基线 DRC 为 220 个 error、55 处未连接，原样公开。根因是 U1↔U2 通道只有 1.07 mm，属于布局问题。见 [`design/coreboard/README.md`](design/coreboard/README.md)。
- **与 Freerouting 的对照里，V5 不占优**：3 块可比板上，Freerouting 线长短 8–12%、过孔少 70–97%、速度快几个数量级。V5 名义上的完成率缺口，大部分来自分母口径（单焊盘退化网计入了分母）。
- **测试套件**在作者机器上全绿（编译器 3884 项：3880 passed + 4 xfailed）。但完整复现依赖约 1.5 GB 的实验证据目录（`out/`），这部分**没有公开**。干净克隆下，引擎和编译器分别有 13 和 48 项失败或错误，原因都已归类，见 [`docs/REPRODUCING.md`](docs/REPRODUCING.md)。
- **原始过程档案不公开**：逐批调度日志、任务书、逐项裁决记录共数百份，只以摘要形式出现在 [`docs/RESEARCH-SUMMARY.md`](docs/RESEARCH-SUMMARY.md)。[`results/`](results/) 收录了几份关键的机读结果：V5 里程碑证据清单、Freerouting 对照、自改进实验总报告。

## 快速上手

```bash
# Python ≥ 3.12；核心零第三方依赖，测试需要 pytest、jsonschema
pip install pytest jsonschema numpy

export PYTHONPATH=$PWD/tools   # 公开快照插件：缺证据文件的测试记为 skip 并写明缺什么

# V5 引擎测试（公开快照实测：2153 passed / 169 skipped / 13 failed）
cd engine && python -m pytest -q -p no:cacheprovider -p pcbflow_public_archive

# pcbflow 编译器测试（公开快照实测：2589 passed / 986 skipped / 44 failed / 4 errors）
cd ../tools/pcbflow && python -m pytest -q -p no:cacheprovider -p pcbflow_public_archive -o addopts="" --basetemp=/tmp/pft
```

剩下的失败都已逐条归类（Windows 专用、冻结哈希、脱敏后的板文件等），见 [`docs/REPRODUCING.md`](docs/REPRODUCING.md)。

真实板实验还需要 **KiCad 10.0.5**（`kicad-cli`）和第三方语料板。语料板不随仓库分发，按 [`docs/DATASETS.md`](docs/DATASETS.md) 从原仓库的固定 commit 下载。

## 第三方材料与许可证

| 部分 | 许可证 |
|---|---|
| 代码（`engine/`、`tools/`、`firmware/`、脚本） | [Apache-2.0](LICENSE) |
| 核心板设计文件（`design/coreboard/kicad/`、`bom/`、`pinmap/`） | [CERN-OHL-P-2.0](design/coreboard/LICENSE.BOARD) |
| 技术报告与文档（`papers/`、`docs/`） | [CC BY 4.0](papers/LICENSE) |

- 实验用到的第三方开源板（OLIMEX、SparkFun、PCBench、KiCad 官方 demo 等 100+ 块）**不重新分发**，仓库里只给来源链接、固定 commit 和逐板许可证清单（`tools/pcbflow/datasets-manifests/`）。基于这些板得到的结果数据照常公开。
- KiCad QA 测试板（GPL-3.0）、数据手册（厂商版权）同样只给链接，见 [`docs/THIRD-PARTY.md`](docs/THIRD-PARTY.md)。
- 依赖审计：仓库里没有 vendored 的 GPL 代码。KiCad（`pcbnew`/`kicad-cli`）和 Freerouting 只作为外部程序调用。可选渲染依赖 PyMuPDF 是 AGPL-3.0，只在渲染脚本里使用，不安装也不影响核心功能。

## AI 参与声明

这个项目本身就是在研究 LLM。绝大部分代码、实验驱动和报告初稿由多个 LLM 编码代理在作者的编排下完成。作者负责立项、判据、逐项裁决和终审；模型负责实现和执行。每一批都有冻结的预注册件和机械复核，任何结论都不以模型的自我报告为准。具体协作方式见 [`docs/RESEARCH-SUMMARY.md`](docs/RESEARCH-SUMMARY.md) §5。

## 引用

见 [`CITATION.cff`](CITATION.cff)。Zenodo DOI：[10.5281/zenodo.23805537](https://doi.org/10.5281/zenodo.23805537)（v1.0.0）。

## 状态

**项目已收线（2026-10-30）。** 不接受功能请求；issue 仅用于勘误。

作者：赵丹琪（黑龙江工程学院 机电工程学院 机器人工程专业）· GitHub [@chunhuachaolu-art](https://github.com/chunhuachaolu-art)
