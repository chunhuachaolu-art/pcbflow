# 发布前审计记录（2026-10-30）

本文记录公开快照打包时做过的检查。这是打包者的自查，**不是**独立第三方审查。

## 1. 收录范围

| 来源（作者机器） | 收录 | 排除 |
|---|---|---|
| route-v5 工作仓 | `v5/`、`v5-pre-r1/`、`canvas*/`、`net_agent_pilot/`、`tools/`、`tests/`、`schemas/`、`boards/`（自建合成板）、`docs/`、实验驱动脚本（取工作树现状，含 10-21 之后未提交的 0.12 / 0.13 提速） | `out/`（约 1.5 GB 证据目录）、全部任务书 / 调度日志 / 裁决记录、编排工作流草稿、KiCad QA 测试板 |
| pcbflow-workspace 仓 | `tools/pcbflow/`（包、测试、脚本、3 个自有 profile）、`tools/pcbagent/`（不含 `out/`）、`firmware/` | 语料派生 profile（91 份）、数据集原件、`exec/`、`archive/`、各类状态 / 交接文档、Rev-B 与早期版本板、数据手册 |
| 核心板发布包 `artifact-release/revc-board` | 全部（已于 10-24 单独脱敏核验） | — |
| 核心板原工程 | 编译器读取的规格与快照（`reports/*-spec-v1.md`、`snapshots/p3-placement-gates-pass/`、`placement.csv`、`opens.csv`、`length-report.py`）、交付报告、经验记录 | 其余中间件、日志、会话与 DSN/SES 交换文件 |
| 论文纲领 R2 | 六篇正文、术语表、图件及作图脚本 | 文献检索台账、对账件、席位记录 |

## 2. 脱敏

- 本机用户目录（含用户名）和数据盘布局，替换为 `<HOME>` / `<WORKSPACE>` / `<ENGINE_ROOT>` / `<DATA_ROOT>`，脚本见打包记录。
  - **例外**：带哈希链的数据件（board JSON、测试基线、测试夹具生成器），以及只含盘符、不含用户名的代码路径，保持原样，避免破坏哈希链。这些路径只暴露 `E:/ZCodeData/...` 这样的目录布局，不含个人信息。
- 扫描结果（不计 `.kicad_pcb` 坐标、PDF 二进制和 PNG）：
  - 用户名：0 处真实命中（3 处假阳性：DOI 链接中的数字、PCB 坐标数字）；
  - 邮箱：0；
  - 密钥（`sk-` / `ghp_` / `api_key=` 等）：0；
  - 中转站或计费渠道名：0；
  - 他人姓名：0（只有作者本人署名，以及参考文献作者）。
- 六份 PDF 的文本层另做了一遍扫描，没有命中。
- 核心板 PCB 文件的 sha256 为 `dbfea0895301ade8209701ef93545b26ca35ef49a9b7116032d917db79e1a791`，与板 README 的声明逐位一致。

## 3. 许可

- 依赖审计见 `docs/THIRD-PARTY.md`：没有 vendored 的 GPL 代码；PyMuPDF（AGPL-3.0）只是可选依赖。
- 第三方语料板一律不分发，只给来源清单（`SOURCES.json`，145 行）。
- 删除了 KiCad 来源的测试夹具：QA DRC 板 10 块、demo 板 3 块。

## 4. 测试

见 `docs/REPRODUCING.md`。打包时在干净的 Linux 容器里实测：

- 引擎：2153 passed / 169 skipped / 13 failed；
- 编译器：2589 passed / 986 skipped / 44 failed / 4 errors。

## 5. 为公开快照做的代码改动（全部）

1. `engine/v5/sidecar.py`、`engine/v5-pre-r1/sidecar.py`：写入根从写死的本机路径，改为按文件位置解析（可用 `PCBFLOW_ENGINE_ROOT` 覆盖）。
2. `engine/canvas/tests/test_qa_drc.py`：缺少车道提取器和 GPL 夹具时，整模块跳过。
3. `design/coreboard/kicad/.../length-report.py`：板文件路径改为相对路径。
4. `tools/pcbflow/tests/test_asm_inventory.py`：测试样本字符串里的用户名换成 `alice`。
5. 新增 `tools/pcbflow_public_archive.py`（pytest 插件）、`tools/pcbflow/datasets-manifests/{SOURCES.json, fetch_corpus.py}`。

除此之外，代码与作者机器上收线时的工作树逐字节相同，只有注释、文档字符串和历史脚本里的路径被替换为占位符。
