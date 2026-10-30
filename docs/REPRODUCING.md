# 复现与测试现状

## 1. 两种口径

| 口径 | 环境 | V5 引擎（`engine/`） | pcbflow 编译器（`tools/pcbflow/`） |
|---|---|---|---|
| **作者机器**（全部证据目录在位） | Windows、KiCad 10.0.5、约 1.5 GB 的 `out/` 证据目录、145 块语料板 | 全绿（收线前最后一次全量记录的口径） | **3884 collected = 3880 passed + 4 xfailed，0F/0E**（V5 里程碑记录） |
| **公开快照**（本仓库干净克隆，Linux / Python 3.13） | 没有证据目录和语料板，没有 KiCad | **2153 passed、169 skipped、13 failed** | **2589 passed、986 skipped、4 xfailed、44 failed、4 errors** |

公开快照这一行是打包时在干净的 Linux 容器里实测的。逐条失败清单在 `docs/test-results/`。

## 2. 为什么有 skip

很多测试会对照冻结的实验证据（`out/` 下按哈希锚定的报告、台账、板快照）或第三方语料板做断言。公开快照不带这些文件。

`tools/pcbflow_public_archive.py` 是一个 pytest 插件：如果测试**只是**因为 `FileNotFoundError` 找不到证据文件而失败，就把它记为 skip，并在原因里写明缺的是哪个路径。其他失败（断言错误、值不对、其他异常）一律照常报失败，插件不会掩盖。

```bash
export PYTHONPATH=$PWD/tools          # 让 pytest 找到插件
cd engine && python -m pytest -q -p no:cacheprovider -p pcbflow_public_archive
cd ../tools/pcbflow && python -m pytest -q -p no:cacheprovider -p pcbflow_public_archive -o addopts="" --basetemp=/tmp/pft

PCBFLOW_STRICT=1 python -m pytest ...  # 关掉插件，看原始结果
```

## 3. 公开快照里剩下的失败是什么

**V5 引擎（13 个）**

- `test_k2_authority`（5 个）：测试用 `.bat` 伪造 kicad-cli，只能在 Windows 上运行。
- `test_opt09_watchdog`（6 个）：进程看门狗按 Windows 的进程与计时语义写，Linux 上判定窗口不同。
- `test_diag_replay_r1_contract`（1 个）：依赖 `out/` 下的 `run_diag` 模块，抛的是 ImportError，不是 FileNotFoundError，所以没有被识别为缺证据。
- `test_sidecar::test_allowed_root_is_route_v5_out`（1 个）：断言写入根的目录名是 `route-v5`；公开仓库里这个目录改名为 `engine/`。写入根现在按文件位置解析，可以用 `PCBFLOW_ENGINE_ROOT` 覆盖。

**pcbflow 编译器（44 个失败 + 4 个错误）**，主要是以下几类：

- 目录与文件计数断言：语料派生 profile 只保留了 3 个（原有 94 个）；数据集目录有文件数和聚合哈希对账。
- 冻结件哈希断言：公开版的核心板文件做过脱敏（网表和库表的路径、BOM 的价格列），与原始冻结哈希不一致。
- 依赖 Windows 路径或 KiCad 环境的测试。
- 测试基线快照（`baseline.json`）对应的是作者机器的完整套件。

## 4. 真实板实验

1. 安装 KiCad 10.0.5，保证 `kicad-cli` 在 PATH 里。注意：部分历史脚本里写死了 `F:/kicad/bin/kicad-cli.exe`。
2. 下载语料：`python tools/pcbflow/datasets-manifests/fetch_corpus.py`（见 `docs/DATASETS.md`）。
3. 引擎入口在 `engine/v5/`（`harness.py`、`executor.py`、`adapters/kicad_adapter.py`），各实验驱动在 `engine/tools/` 和 `engine/experiments/`。

**路径占位符**：历史实验脚本、文档和报告里的本机绝对路径，已替换为 `<ENGINE_ROOT>`（即 `engine/`）、`<WORKSPACE>`（即本仓库根）、`<HOME>`、`<DATA_ROOT>`。这些脚本是当时一次性运行的记录，不保证开箱可跑。核心模块不依赖这些占位符。

## 5. 版本

| 组件 | 冻结版本 |
|---|---|
| V5 executor | `v5.executor/0.13.0` |
| KiCad 适配器 | v0.6.0（双版本串，兼容 v0.5.0） |
| pcbflow 包 | 0.1.0 |
| 参照工具链 | KiCad / kicad-cli 10.0.5，Freerouting 2.4.1，Python 3.12+ |
