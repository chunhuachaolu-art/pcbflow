# PROVENANCE.md — datasets/corpus-r2-r1/ 跨板学习线语料 r2 入库登记

- 日期常量（登记/采集声明）: **2026-09-12**
- designation: 31 板 = **train/val-candidate**；6 板 = **holdout-expansion-pool（预冻结，永不参与调参）**（H1–H6）；3 板另带 **never-holdout** 标注（TinyTapeout 系 ×2 + OtterCastAudioV2）
- 本目录为 datasets/ 首个经逐板授权的新增子树；其余四棵既有子树（pcbbenchmarks-r1 / pcbench-r1 / kicad-demos-r1 / holdout-candidates-r1）全程**只读零触碰**
- **37 板终态**（36 主批 + H5 补录，见 §4）；manifest 与本文件均已按 37 板口径更新

## 1. 采集链（可复现性）

1. **审计两轮**（零写入）：
   - 主审轮 24 仓 71 份板文件 → `out/v3-corpus-r2-research/candidate-inventory-r1.json` + `CORPUS-R2-AUDIT-REPORT.md`；
   - OSHWA 深审轮（3,418 项认证 → 24 项 KiCad → 20 源仓）→ `candidate-inventory-r2-addendum.json` + 主报告 §10/§11。
2. **pinned SHA 快照**：逐仓取 default branch HEAD commit SHA，经 GitHub Git Trees API + Git Blobs API（`Accept: application/vnd.github.raw`）逐文件取原文，字节数与 tree 记录逐一核对；快照落 `out/v3-corpus-r2-research/downloads/<org>__<repo>/`（含 tree.json / files.tsv / HEAD.txt / repo.json）。**本批零网络下载**（全部复用已审计快照；无缺失/损坏文件，未触发 Blobs 补采例外）。
3. **入库前逐文件复核**（本批执行）：36 份 .kicad_pcb 逐一与同目录 tree.json 的 `size` 字段比对 + 与 inventory `evidence.file_bytes` 比对，**36/36 全等**；sha256 重算记入各板 metadata.json（`evidence.file_sha256` + `evidence.git_blob_sha`）。
4. **拷贝**：快照 → `raw/<org>__<board-id>/`（保留原文件名，扁平化）；拷贝后逐文件 sha256 复验 = 快照哈希。license 原文从 `out/v3-corpus-r2-research/licenses/` 拷入 `licenses/`（39 份，含 board 引用件与同仓补充件），board 引用件 sha256 与 inventory `license.sha256` 逐一相符。

## 2. 批准链

- **R22**（`out/v3-obs/ADJUDICATION-2026-09-12.md` §5）：语料 r2 留存与 holdout 池全按审计报告批准；holdout 池 H1–H5 入池、H6 jetson-nano-baseboard 知情入池（同厂商同产品线亲和性警示随池携带）。
- **CORPUS-R2-APPROVAL-2026-09-12.md** §1–4：留存集（强留存 + 条件留存 + 备选候补池）、预冻结池 6 槽、裁决③（先深审后入库）、裁决④（老格式板含入、按版本 token 分桶过转换验证门）、裁决⑤（CM5 MINIMA REV3 重评批准）、OSHWA 深审轮结果登记。
- **本会话（2026-09-12 ingestion 批）**：用户批准 datasets/ 写入新目录 `corpus-r2-r1/`，36 板（disposition ∈ retain / retain-conditional / optional 的 leader 板）全量授权。这是 datasets/ 历史上首次授权写入新目录。

## 3. 两门证据（先门后写；门全过后落盘）

### 门 1 — 去重复验：**PASS（36/36 零碰撞）**

- 名册基准：pcbench-r1/raw 81 板 + kicad-demos-r1/raw 15 目录 + pcbbenchmarks-r1/raw 2 板 + holdout-candidates-r1 5 板（Easyduino 3 + SparkFun 2），共 103 个既有板目录。
- 方法：目录名/板名归一化比对（小写、去分隔符）；命名嫌疑者做文件级 sha256 比对。
- 家族级标记（非文件重复，字节级证伪同文件）：
  - `ottercast-audio-v2` vs 语料 `kitspace_OtterCastAmp`：sha256 不同（87e560e5… ≠ 1464bebf…）——姊妹产品，never-holdout 标注；
  - `tinytapeout-demo` vs 语料 `kicad-demos-r1/raw/tiny_tapeout`：sha256 不同（773a0e29… ≠ 0d26bf9b…）——同产品线新旧版，never-holdout 标注；
  - `jetson-nano-baseboard` vs 语料 `jetson-agx-thor-baseboard`：sha256 不同（8fc7b361… ≠ e61179b6…）——同厂商不同代际，H6 亲和警示随池；
  - `axiom-micro-mainboard` vs `pcbench-r1/cat-trainer_teensy_base_pcb`：归一化误命中（双方板名 token 均含 "pcb"），sha256 不同（02514f4f… ≠ 6bed0cce…），确认为零碰撞。

### 门 2 — 老格式转换验证门：**PASS（36/36 主批 + H5 补录复验 = 37/37）**

版本 token 分桶（37 板）：`20171114`×1、`20171130`×9、`20210424`×1、`20211014`×5、`20221018`×9、`20241229`×7、`20260206`×4、`(version 4)`×1。

- 全部 37 板经 **pcbflow `sexpr_min.parse`** 结构解析通过（kicad_pcb 根唯一；H5 scalenode 于补录时按同口径补跑，PASS 留痕）；
- `20171130` 桶 9 板经 **pcbflow `corpus_convert.parse_kicad5_board`**（KiCad 5 读取器，纯函数）实跑通过；
- 老格式非 20171130 桶（`20171114` TERES Rev.C、`(version 4)` iCE40 Rev_B、`20210424` stm32-ds2480-emu）按裁决④口径记"文本自检通过 + 桶号"（pcbflow KiCad5 读取器版本边界外，读取器按设计 refuse 并留痕）；
- 逐板证据计数复核：segments/vias/zones/footprints（正则口径）+ copper_layers/net_count（audit 解析器 `_tools/parse_kicad_pcb.py` 口径）与 inventory 声明**37/37 全等**；
- 零渲染、零 kicad-cli、零图像；门失败标准（解析失败/token 不一致/证据不符）零触发，无 GATE_CONVERT_FAIL 剔除。

## 4. 口径冲突注记与 H5 补录（已闭合）

- 批准文件侧（R22 + APPROVAL §2 + 审计报告 §5A/§7）：**H5 scalenode-cm4 已批准入池**（4L 工业节点基板）。
- inventory JSON 侧：`candidate-inventory-r1.json` 中该板曾被标 `disposition: "variant"`。
- **根因（主审验收时查实）**：`out/v3-corpus-r2-research/_tools/build_inventory.py` 编写时即漏配 scalenode 的 REPO_META/DECISIONS 条目（grep 零命中可复核），致该板落入 variant 兜底；审计报告 §5A/§7 的表格按意图值手写故未暴露。ingestion 批按 JSON 机械过滤得 36 板（不含 scalenode），池落盘 5/6，冲突由此顶出。
- **处置（2026-09-12 主审补录）**：按批准链（R22 §2 + APPROVAL §2 均批 H5 入池）补录为**第 37 板**——拷贝 pinned 快照（@`77f5bf2`，字节数 9,824,235 与 tree/inventory 三方全等，sha256 `e20413ed…`），metadata/manifest/licenses 同口径登记，`sexpr_min.parse` 复验 PASS；`candidate-inventory-r1.json` 该条目同步修正为 retain+H5（note 留痕），builder 漏项在 `_tools/h5_addendum.py` 头注记录。全局分母 136→**137**。

## 5. 红线声明

- **既有子树零触碰**：pcbbenchmarks-r1 / pcbench-r1 / kicad-demos-r1 / holdout-candidates-r1 及 datasets/ 下其余既有文件零写入、零移动、零删除（收工以 `find datasets -type f -newer <marker>` 自证，marker 时点先于本批首笔写入）。
- **零渲染**：全程未运行 kicad-cli、未生成任何图像/3D/渲染件；holdout 池 6 板（H1–H6）额外执行零读图纪律——全部接触仅限文本级（字节计数、sha256、S 表达式解析、正则计数）。
- **防杂散**：本目录仅含 .kicad_pcb / metadata.json / license 原文 / manifest.json / 本文件；无 .kicad_prl、无 .bak、无 *-bak*、无 kicad-cli 副产物。
- **provenance 就地**：本批全部 provenance 与产物仅落 `datasets/corpus-r2-r1/`；`out/` 只读零写入（引用路径除外）。
- **分母口径**：全局设计板 100 → **137**（+37）；其中 holdout 预冻结池 6 槽（H1–H6）全部落盘，池一经冻结永不参与调参；TinyTapeout 系（tt06-fpga-ice40up5k、tinytapeout-demo）与 OtterCastAudioV2 永不 holdout。

## 6. 本批接触方式（holdout 池板逐板）

| 池 | 板 | 接触 |
|---|---|---|
| H1 | kria-k26-devboard | 字节计数/tree 比对、sha256、sexpr 解析、正则计数（零读图） |
| H2 | sdi-mipi-bridge | 同上 |
| H3 | hackrf-one | 同上 |
| H4 | pslab-v6 | 同上 |
| H5 | scalenode-cm4-baseboard | 同上（补录板，2026-09-12：字节数三方核对、sha256、sexpr 解析 PASS） |
| H6 | jetson-nano-baseboard | 同上（亲和警示：与语料 jetson-agx-thor 同厂商同产品线，任何 holdout 结果解读必须携带） |

## 7. 执行侧注记补录（2026-09-12）

> 本节为入库当日执行侧收尾补录，仅新增 count-neutral 注记与只读调查登记，**§1–§6 无任何改动**；manifest.json 未动，板文件/license 未动。

### 7.1 CERN-OHL 互惠义务注记（16 板，count-neutral）

闭合 APPROVAL §3 遗留执行侧待办"USB-GIGABIT CERN-OHL-1.2 仅 PDF 留档与 CERN-OHL-S-2.0 互惠注明"（扩大到全部 CERN-OHL 板）。逐板在 `raw/<org>__<board>/metadata.json` 新增顶层键 `license_obligation`（一句话义务级别 + "reuse 前查原文"）；Apache-2.0 / MIT / CC-BY-SA-4.0 / GPL-3.0 板不加。USB-GIGABIT 原 note（"license 为 CERN-OHL-1.2 且仅 PDF 存档"）保留，义务注记内另带 PDF-only 提示。

| spdx | 义务级别（注记口径） | 板 |
|---|---|---|
| CERN-OHL-S-2.0 ×5 | 强互惠：衍生板必须同样开源 | 6mil-Labs__tmp108、Open-Muscle__om-flexgrid-v4-rigid-pcb、apertus-open-source-cinema__axiom-micro-mainboard、arithmaldor__vga-panel-breakout、piecol__cm5-minima-rev3 |
| CERN-OHL-W-2.0 ×3 | 弱互惠：仅对该板文件的修改开源 | Anthilla__anthc、Pealie__thin-pod、RobotStudyCompanion__torxhat |
| CERN-OHL-1.2 ×6 | 互惠：类似强互惠，按 CERN-OHL-1.2 条款 | OLIMEX__usb-gigabit-rev-e（含 PDF-only 提示）、alitekin2fx__stm32-ds2480-emu、fm4dd__pmod-bme280、fm4dd__pmod-crypto、fm4dd__pmod-i2c24io、oshwabadge2020__badge-pcb |
| CERN-OHL-P-2.0 ×2 | 宽松：可闭源须保留声明 | greatscottgadgets__hackrf-one、greatscottgadgets__throwing-star-pro |

复核：37 份 metadata.json 补录后 `json.load` 全部通过；37 份 .kicad_pcb sha256 与 manifest `board_file_sha256` 逐一相符、目录内容与 manifest `files` 列表逐一相符（板文件字节未动、无增删文件）；补录前已验证 37 份 metadata.json 经 `json.dumps(indent=1)` 往返字节全等（唯一例外 scalenode 无末尾换行，已按原状保留）。

### 7.2 AnthC zones=1011 语义审查（只读调查）

**结论一句**：`evidence.zones=1011` = 板文件内顶层 `(zone` 对象数（kicad_pcb 直接子节点，与 `_tools/parse_kicad_pcb.py:118` 正则口径及全语料一致，数值无需修正），其中 990 个为 KiCad 10 自动生成的 teardrop 逐 pad/via 独立 zone、21 个为手画区（16 铜皮 + 5 keepout），`filled_polygon`=1091 为另一口径；入库 note 中"逐层逐 net 展开"表述不准确，gate 无影响，但跨板 zone 复杂度统计需拆 teardrop 口径。

详见 `out/v3-corpus-r2-research/ANTHC-ZONES-REVIEW-2026-09-12.md`（计数方法、6 板同口径重算对照、文本行摘录、影响评估、解析器增强建议——仅建议未实施）。

## §7.3 收口校准批（2026-09-12，执行侧五工后主审落锤）

- license_obligation 注记 16 板（见 §7.1）；AnthC metadata note 措辞修正： zones=1011 表述由"逐层逐 net 展开"改为 teardrop 逐 pad/via 物化（佐证=out/v3-corpus-r2-research/ANTHC-ZONES-REVIEW-2026-09-12.md）。
- ice40hx1k-evb-rev-b layers 2→4（metadata+manifest boards[] 同步；根因=审计层名正则不识带引号自定义铜层名 In1(GND).Cu/In2(PWR).Cu）；counts.by_layers → 2L×16/4L×15。
- manifest 残留补登（H5 批次漏项收尾）：licenses[] 补 scalenode 行（40/40，与盘面、37 板 metadata 并集三方全等）；转换门措辞 36→37（H5 补录含内）。
- 快照刷新：D 批 16 板 metadata 注记致 boards[].bytes 漂移，逐板重测 + total_bytes 不动点收敛终值 181,803,601（data 181,741,882 + root 61,719）；tests/test_corpus_r2_r1_reconcile.py 回精确等式 8/8。
- net_count 口径定型（数值不改，模式标签保留）：numbered-named 与 37 板实测 33 板有差——现代桶普遍 +1（裸声明 (net 0) 不入模式口径）、20171130 桶缺口为不带引号网名（TERES 285 vs 板自述 general.nets=475）；后续真值以 corpus_convert（k5/k9）+ corpus_convert_legacy 三解析器声明计数为准。
- throwing-star-pro 层表为古典名 (0 Front signal)/(31 Back signal)，layers=2 核实无误；37 板全量重扫（三解析器层表判据）后 layers 误计仅 ice40 一板。
