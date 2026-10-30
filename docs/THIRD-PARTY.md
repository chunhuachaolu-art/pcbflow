# 第三方材料与依赖审计

## 1. 不随仓库分发的材料

| 材料 | 原因 | 怎么获取 |
|---|---|---|
| 145 块实验语料板 | 各有许可证，部分为 CC-BY-SA 或 CERN-OHL-S 等互惠许可 | [`docs/DATASETS.md`](DATASETS.md) |
| 由语料板派生的 board profile（逐板图结构 / 几何派生件，共 91 份） | 属于第三方板的派生物 | 下载语料后，用 pcbflow 的 profile 生成脚本重建 |
| KiCad QA DRC 测试板（`qa/tests/pcbnew/drc/`，10 块） | KiCad 源码，GPL-3.0-or-later | KiCad 源码树；测试 `engine/canvas/tests/test_qa_drc.py` 缺少夹具时跳过 |
| KiCad 官方 demo 测试夹具（pic_programmer、ecc83、constraints） | 同上 | KiCad 源码树 `demos/` |
| 存储器数据手册（ISSI IS42S16160J、Winbond W9825G6KH） | 厂商版权 | 厂商官网 |
| 统一文献库（1540 份论文 PDF） | 出版方版权 | 报告参考文献里给出了 DOI |

仓库里**保留**了两块自建测试板（`boards/d/` 下的合成板，以及 `d4-degenerate.kicad_pcb`），它们由本项目脚本生成，适用 Apache-2.0。

## 2. 依赖审计（GPL 检查）

审计范围是全部 `.py` 文件的 import 和仓库内全部许可证声明：

| 依赖 | 许可证 | 用法 | 结论 |
|---|---|---|---|
| Python 标准库 | PSF | 核心 | — |
| pytest、jsonschema | MIT | 测试 | ✓ |
| numpy、scipy、scikit-learn、matplotlib、Pillow、networkx | BSD / PSF 系 | 实验脚本、作图 | ✓ |
| PyMuPDF（`fitz`） | **AGPL-3.0** | 仅 `docs/paper2-protocol/render` 和少数作图脚本 | 可选依赖，核心不导入；如需分发 SaaS 或二进制，请换渲染后端 |
| kicad-python（`kipy`） | MIT | 可选，KiCad IPC | ✓ |
| KiCad `pcbnew` / `kicad-cli` | GPL-3.0-or-later | 作为外部程序 / 外部模块调用，不随仓库分发 | ✓ |
| Freerouting | GPL-3.0 | 对照实验中作为外部 jar 调用，不随仓库分发 | ✓ |

**结论：仓库内没有 vendored 的 GPL 代码**（`grep` 检查了 GPL / AGPL 许可头和 vendor 目录，命中的只有语料清单里对第三方板许可证的记录文字）。核心包 `pcbflow` 声明零第三方运行时依赖。
