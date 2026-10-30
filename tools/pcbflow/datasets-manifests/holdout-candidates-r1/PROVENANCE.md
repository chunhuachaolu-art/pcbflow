# PROVENANCE.md — datasets/holdout-candidates-r1/ 留出集 Tier 2 采集登记

- 日期常量（登记/下载声明）: **2026-09-07**
- 计划文件: `out/v3-tl2/holdout/HOLDOUT-PLAN.md`（路径 C；本目录=其 Tier 2 下载项）
- designation: 全部条目 = **holdout-candidate**（一次性纪律：正式 holdout 运行前不接触任何渲染件）
- 本目录之外的 datasets/ 子树（kicad-demos-r1、pcbbenchmarks-r1、pcbench-r1）严格只读，本次零写入
- 接触纪律: **零渲染零读图**。对下述板做过的全部"接触"仅限文件级检查：.kicad_pcb 头部 version 字段、layers 声明块查看、图层 token 的 grep -c 计数、LICENSE/README 文本阅读

## 采集方法（可复现性）

- 下载快照方式：**GitHub Git Blobs API 按 pinned commit SHA 逐文件取原始内容**（`Accept: application/vnd.github.raw`），逐文件校验字节数与 tree 记录一致。未使用 git clone（环境内 raw.githubusercontent.com DNS 不可达；API 通道可用）。目录内不含 .git。
- 每板选材原则：只取设计文件（.kicad_pcb / .kicad_pro / .kicad_sch / readme / lib-table / LICENSE），**刻意不取** Outputs/Gerbers、Photos、STEP/3D、Datasheets PDF（控制体积且避免引入非解析工件）。

---

## A. Easyduino — 已收（3 板）

- 源 repo: <https://github.com/Hanqaqa/Easyduino>（作者 Marco Vazquez Madero，GitHub: Hanqaqa；Adafruit 博客 2026-04-28 推荐）
- 许可证: **CERN-OHL-P-2.0**（顶层 `License.txt`，已随附于 `easyduino/License.txt`）
- 快照: master HEAD commit `53b14b66d64f25c55f88971c1c1b51656126bd30`（提交时间 2026-06-28T21:05:45Z）；下载日期常量 2026-09-07
- repo 共 6 板、约 233MB；按计划只取 3 块代表性板（STM32 系必备 + 两块其他 MCU 板，MCU 多样性：STM32 / ESP32-S3 / RP2040）。三块板 .kicad_pcb 头均为 `(version 20260206)`（KiCad 10 系格式，generator pcbnew）。
- 三板 layers 声明块均含 4 铜层（F.Cu / In1.Cu / In2.Cu / B.Cu），In 层 token 计数极低（4~12）说明主要布线在表层的 4 层叠层。

| 板 | 源路径 | 本地路径 | version | "F.Cu" | "B.Cu" | "In1.Cu" | "In2.Cu" | F.SilkS | F.CrtYd | B.CrtYd |
|---|---|---|---|---|---|---|---|---|---|---|
| STM32F103 Bluepill | `STM32F103 Bluepill/Easyduino_STM32F103.kicad_pcb` | `easyduino/STM32F103-Bluepill/` | 20260206 | 643 | 158 | 4 | 4 | 145 | 99 | 9 |
| ESP32-S3 | `ESP32S3/Easyduino_ESP32S3.kicad_pcb` | `easyduino/ESP32S3/` | 20260206 | 699 | 507 | 4 | 4 | 188 | 81 | 1 |
| RP2040 (Pico) | `Raspberry Pi Pico 2040/Easyduino_RP2040.kicad_pcb` | `easyduino/RP2040-Pico/` | 20260206 | 817 | 203 | 4 | 12 | 211 | 105 | 3 |

计数口径：对本地 .kicad_pcb 文件逐 token `grep -c`；带引号 token 为 layers 声明+逐对象 layer 字段的合并计数；F.SilkS/F.CrtYd/B.CrtYd 为无引号子串计数。仅此文件级检查，无任何渲染。

- 未收但 repo 内合格（非质量问题，仅配额取舍）: Arduino Uno / Nano（Atmega328p）、ESP32（经典 WROOM）——同许可证 CERN-OHL-P-2.0，可后续按需补收。
- 备注: `STM32F103 Bluepill/` 目录在源 repo 即无 `sym-lib-table`（其余两板有），已照实落盘为"缺失"，非下载遗漏。

## B. SparkFun — 已收（2 板，均 KiCad 原生）

- 源 org: <https://github.com/sparkfun>；筛选方法：org 内搜索 "kicad"，逐候选 repo 查树确认存在 `.kicad_pcb` + LICENSE 文件。
- 许可证: 两 repo 的 `LICENSE.md`（已随附）均为 SparkFun 标准双许可文本——硬件 **CC-BY-SA-4.0**（Creative Commons Attribution-ShareAlike 4.0 International），代码另按其开源代码许可。GitHub license 字段显示 NOASSERTION（未自动识别），以 LICENSE.md 文本为准。
- 下载日期常量: 2026-09-07；快照方式同上（Blobs API at pinned SHA）。

| 板 | repo | HEAD SHA（提交时间） | .kicad_pcb 源路径 | version | 层数 | "F.Cu" | "B.Cu" | F.SilkS | F.CrtYd | B.CrtYd |
|---|---|---|---|---|---|---|---|---|---|---|
| Qwiic ADC breakout | `sparkfun/SparkFun_Qwiic_ADC_ADS1219` | `de0f42821a29a3d36fa2ad246ed3274344f4e731`（2026-06-05T16:09:10Z） | `Hardware/Qwiic_ADC_ADS1219.kicad_pcb` | 20241229（generator_version 9.0） | 2（F/B，无 In） | 292 | 217 | 105 | 54 | 12 |
| Qwiic 电流传感 breakout | `sparkfun/SparkFun_Qwiic_Current_Sensor_INA2XX` | `313d3e2c03218f00eb5fb051d5594f05c95abecf`（2026-07-23T22:20:39Z） | `Hardware/SparkFun_Qwiic_Current_Sensor_INA2XX.kicad_pcb` | 20241229（generator_version 9.0） | 2（F/B，无 In） | 227 | 125 | 128 | 50 | 9 |

- 本地路径: `sparkfun/qwiic-adc-ads1219/`、`sparkfun/qwiic-current-sensor-ina2xx/`（各含 .kicad_pcb/.kicad_pro/.kicad_sch/LICENSE.md/README.md，扁平化映射自源 repo 的 Hardware/ 与根目录）。
- 已核查未下载的合格备选（同 CC-BY-SA-4.0、各有 1 个 .kicad_pcb）: `SparkFun_Qwiic_Navigation_Switch`、`SparkFun_RFID_USB-C_Reader`。配额按计划 1–2 块执行，其余可后续补收。

## C. Adafruit — 未收（格式受阻）

- 结论: **Eagle 格式未收，转换路径待定**。
- 查证（2026-09-07，GitHub API）: adafruit org 内 `kicad in:name,description` 搜索仅命中 1 个 repo = `adafruit/kicad2fritzing`（转换工具，非板）。抽查官方板 repo `Adafruit-Feather-RP2040-PCB` 文件树: `.brd` x3、`.sch` x3、`.kicad_pcb` x0——设计文件为 Eagle 原生。与其历来惯例一致（大多数板为 Eagle .brd）。
- 代表 repo 链接: <https://github.com/adafruit/Adafruit-Feather-RP2040-PCB>
- 纳入前提（后续可选）: Eagle→KiCad 转换有损，须先过转换验证门再议；本次不下载。

## D. BeagleBone Black — 未收（格式受阻）

- 官方链接: <https://github.com/beagleboard/beaglebone-black>（BeagleBoard.org Foundation；fork 自 CircuitCo/BeagleBone-Black）
- 许可证: **CC-BY-SA** 系——HOLDOUT-PLAN.md 2026-09-07 查证记为 CC-BY-SA-3.0；OSHWA 认证 #US000236 证书页（README 官方链接） Documentation 字段 = "CC BY-SA"，Hardware/Software 字段 = "Other"。
- 格式受阻说明: 原生 PCB 设计为 **Cadence OrCAD/Allegro**（repo 含 `ALLEGRO/` 目录），另有 `MFG/` 制造输出与 `BBB-SCH.pdf` 原理图 PDF；无 KiCad 原生文件，Cadence→KiCad 转换有损 → **不下载**，仅作格式对照登记（TI 生态开放代表）。

---

## 收录汇总

| 项 | 状态 | 板数 | 许可证 | KiCad 版本 |
|---|---|---|---|---|
| A Easyduino | 收（STM32F103 / ESP32S3 / RP2040） | 3 | CERN-OHL-P-2.0 | 20260206 |
| B SparkFun | 收（ADS1219 / INA2XX） | 2 | CC-BY-SA-4.0 | 20241229（KiCad 9.0） |
| C Adafruit | 未收 | 0 | （未适用；惯例 CC 系） | Eagle .brd，转换待定 |
| D BeagleBone Black | 未收 | 0 | CC-BY-SA（证书页）/ 3.0（计划查证） | Cadence Allegro，受阻 |

## 越界声明

- 本次采集仅写入 `datasets/holdout-candidates-r1/`；`datasets/` 其余子树、pcbflow 仓库其余部分、`out/` 均零写入。
- 零渲染零读图：未运行 kicad-cli / pcbflow render，未生成或查看任何图像；全部接触限于上述文件级文本检查。
