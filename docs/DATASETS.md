# 实验语料（第三方板）

pcbflow 的实验用了 145 块第三方开源 KiCad 板。为尊重各自的许可证，这些板**不随本仓库分发**。仓库里只保留：

- [`tools/pcbflow/datasets-manifests/SOURCES.json`](../tools/pcbflow/datasets-manifests/SOURCES.json)：逐板记录来源仓库、固定 commit、仓内路径、许可证，以及实验当时所用文件的 sha256（如有）；
- `corpus-r2-r1/manifest.json` 和两份 `PROVENANCE.md`：原始的采集与审批登记；
- [`fetch_corpus.py`](../tools/pcbflow/datasets-manifests/fetch_corpus.py)：从原仓库的固定 commit 下载，并按 sha256 校验。

| 子集 | 板数 | 来源 | 用途 |
|---|---|---|---|
| `corpus-r2-r1` | 37 | GitHub 上的各开源硬件项目（OLIMEX、antmicro、TinyTapeout、fossasia 等），逐板固定 commit 和 sha256 | 跨板学习线；V5 真实板主语料；其中 H1–H6 为预冻结的 holdout 池 |
| `pcbench-r1` | 81 | PCBench 集合（逐板标注上游仓库） | V3 训练环；train 57 / validation 13 / holdout 11 |
| `kicad-demos-r1` | 15 套 / 20 个文件 | KiCad 源码树 `demos/`，commit `10fd7155…` | 格式转换与 profile；stickhub（NC 许可）和 cm5_minima（CERN-OHL-S）已排除 |
| `holdout-candidates-r1` | 5 | Easyduino ×3（CERN-OHL-P-2.0）、SparkFun Qwiic ×2（CC-BY-SA-4.0） | 留出候选 |
| `pcbbenchmarks-r1` | 2 | PCBBenchmarks（ASP-DAC 2021），bm1 / bm11 | 早期基准 |

```bash
cd tools/pcbflow/datasets-manifests
python fetch_corpus.py --list                    # 看全部来源和许可证
python fetch_corpus.py                           # 下载 corpus-r2-r1 和 holdout-candidates-r1
```

下载结果落在 `tools/pcbflow/datasets/<子集>/`，这个目录已被 `.gitignore` 忽略。

**注意**

- 实验期间 holdout 板执行"零渲染零读图"纪律。项目收线后这条纪律解除，对应的结果数据和报告正常公开。
- `fetch_corpus.py` 没有在打包环境里联网实测（打包环境禁止外网）。如果上游仓库删除或改写了历史，下载会失败或 sha256 不匹配；脚本会明确报错，不会静默替换文件。
- PCBench、KiCad demos、PCBBenchmarks 三个子集没有逐文件固定的 GitHub 路径，脚本只列出来源，需要按各自的条款手动获取。
- 每块板的许可证以原仓库为准。下载即表示接受原作者的许可，而不是本项目的许可。
