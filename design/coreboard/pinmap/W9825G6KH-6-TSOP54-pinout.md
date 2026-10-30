# W9825G6KH-6 TSOP-54 引脚映射（权威核验版）

来源：Winbond 官方数据表 W9825G6KH series Rev A03 (2016-06-01)，§4 Pin Configuration + §5 Pin Description 两页交叉核验一致。数据表版权归 Winbond 所有、不随本仓库分发，请从 Winbond 官方渠道获取。

| 脚 | 信号 | 本板网络 | | 脚 | 信号 | 本板网络 |
|---|---|---|---|---|---|---|
| 1 | VDD | 3V3 | | 28 | VSS | GND |
| 2 | DQ0 | FMC_D0 | | 29 | A4 | FMC_A4 |
| 3 | VDDQ | 3V3 | | 30 | A5 | FMC_A5 |
| 4 | DQ1 | FMC_D1 | | 31 | A6 | FMC_A6 |
| 5 | DQ2 | FMC_D2 | | 32 | A7 | FMC_A7 |
| 6 | VSSQ | GND | | 33 | A8 | FMC_A8 |
| 7 | DQ3 | FMC_D3 | | 34 | A9 | FMC_A9 |
| 8 | DQ4 | FMC_D4 | | 35 | A11 | FMC_A11 |
| 9 | VDDQ | 3V3 | | 36 | **A12** | **FMC_A12** |
| 10 | DQ5 | FMC_D5 | | 37 | CKE | FMC_SDCKE0 |
| 11 | DQ6 | FMC_D6 | | 38 | CLK | FMC_SDCLK |
| 12 | VSSQ | GND | | 39 | UDQM | FMC_NBL1 |
| 13 | DQ7 | FMC_D7 | | 40 | NC | —（悬空） |
| 14 | VDD | 3V3 | | 41 | VSS | GND |
| 15 | LDQM | FMC_NBL0 | | 42 | DQ8 | FMC_D8 |
| 16 | WE | FMC_SDNWE | | 43 | VDDQ | 3V3 |
| 17 | CAS | FMC_SDNCAS | | 44 | DQ9 | FMC_D9 |
| 18 | RAS | FMC_SDNRAS | | 45 | DQ10 | FMC_D10 |
| 19 | CS | FMC_SDNE0 | | 46 | VSSQ | GND |
| 20 | BS0 | FMC_BA0 | | 47 | DQ11 | FMC_D11 |
| 21 | BS1 | FMC_BA1 | | 48 | DQ12 | FMC_D12 |
| 22 | A10/AP | FMC_A10 | | 49 | VDDQ | 3V3 |
| 23 | A0 | FMC_A0 | | 50 | DQ13 | FMC_D13 |
| 24 | A1 | FMC_A1 | | 51 | DQ14 | FMC_D14 |
| 25 | A2 | FMC_A2 | | 52 | VSSQ | GND |
| 26 | A3 | FMC_A3 | | 53 | DQ15 | FMC_D15 |
| 27 | VDD | 3V3 | | 54 | VSS | GND |

关键核验点（对照 Rev-A 错误教训）：
- 行地址 A0–A12（13 位，8192 行）✓；列地址 A0–A8；A10 复用 Auto-Precharge。
- 容量 4M×4bank×16bit = 256Mb = 32MiB ✓；刷新 8K/64ms；-6 = 166MHz；3.3V±0.3V。
- 封装 TSOP-II 54（22.35×10.29×1.05mm，0.8mm 脚距，400mil 体宽）——免 BGA 逃逸工艺。
- 与 IS42S16160J（BGA 版）地址映射一致：FMC_A12 直接落到 TSOP 的 36 脚。
- 采购替补：ESMT M12L2561616A-75（同封装同映射）。
