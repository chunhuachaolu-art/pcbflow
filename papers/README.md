# 技术报告（中文，R2 内部定稿，未经同行评审）

| # | PDF | 题目 | 一句话 |
|---|---|---|---|
| 一 | [P1-ROUTING-AS-CODE.pdf](P1-ROUTING-AS-CODE.pdf) | Routing as Code：LLM 辅助 PCB 布线的表示、预算与规划器位置的受控实证研究 | 布线可以代码化、可审计；但在等信息、等预算的条件下，表示方式不带来优化收益，模型座位应从"优化执行位"转向"治理与诊断位" |
| 二 | [P2-CARRIER-METROLOGY.pdf](P2-CARRIER-METROLOGY.pdf) | 缺陷诊断席位的载体测量学：渲染图盲读与结构化盲包的两半 | 渲染图盲读 24 轮召回始终低于 0.31，跨板 GT 复检 0/19；同类判读换成结构化盲包后全部成立——价值取决于载体和任务是否匹配，而不是多模态本身 |
| 三 | [P3-V5-ENGINE.pdf](P3-V5-ENGINE.pdf) | pcbflow V5 确定性布线引擎：世界合同、版本换血、等价性保持优化与分层管线 | 引擎架构、世界合同、字节等价的提速与分层管线 |
| 四 | [P4-ROUTABILITY-ATTRIBUTION.pdf](P4-ROUTABILITY-ATTRIBUTION.pdf) | PCB 可布性归因与不可布性证明：(a)/(b)/(c) 三分类、witness、进场预测与真实板证书收口 | 把"布不通"归因为板固有、引擎缺口或规则带值三类，为归因型基准提供候选 |
| 五 | [P5-LLM-GUIDANCE.pdf](P5-LLM-GUIDANCE.pdf) | 提案权归模型、度量权归引擎：LLM 导引布线的合成域正结果与真实板零终解增量 | 合成场景里导引有效，真实板终解增量为 0 |
| 六 | [P6-DIRECT-MANIPULATION.pdf](P6-DIRECT-MANIPULATION.pdf) | 直接操作席位：画板直绘与直布线的动作合同、验证闭环与经济学 | 模型直接画铜：能过 DRC，但全连通 0/3；拆线重布的经济学；撤除顺序零效应 |

- Markdown 源、术语表（`TERMINOLOGY.md`）和全部图件都在 `src/`。作图脚本在 `src/figs/scripts/`，它们读取的证据目录没有公开。
- 这六篇写于 10-03（R2），比之后的批次（自改进实验、Freerouting 对照、引擎提速、V4 拆线重布）早。后续结果见 `../docs/RESEARCH-SUMMARY.md`。
- 许可：CC BY 4.0（见 `LICENSE`）。
