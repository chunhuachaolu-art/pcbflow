# STM32H743 核心板 Rev-B 引脚分配工作稿

> **状态（发布时点）：本文件为 Rev-B 阶段工作稿，作为设计输入与核验记录随仓库发布；发布板为 Rev-C。U2/FMC 设计输入已核实；PCB electrical closure、CubeMX、采购、制板与装配在发布时点均未完成（发布状态见 README，production_signoff_ready=false）。** 本文件由 Rev-A pinmap 演进而来，只有本轮经 U2 原始数据表与 BGA 球位表核实的 SDRAM 项被提升为工程真源；其余候选复用仍须在最终 `.ioc` 与 Rev-B ERC 中重新验证。
>
> **已关闭的 U2 设计差异：** `IS42S16160J-6BLI` 是 16M×16 / 256Mbit / 32MiB 的 54-ball TF-BGA（8×8mm、0.8mm pitch），不是 Rev-A 中错误使用的 TSOP-II-54。x16 组织需要 A0–A12 行地址、A0–A8 列地址、BA0/BA1、8K/64ms refresh；`FMC_A12` 已从 PG2 连接到 U2/G1，J4-26 不再导出 PG2。
>
> **发布时点仍未关闭的事项：** 授权供应商的当期库存/订单、reel label 与元件顶标、PCB 完整重布局/布线、DRC/ERC 收敛、制造能力和实际 `.ioc`（当前发布状态与已知断点见 README）。
>
> **继承的系统方向，仅供复核：** 保持显示优先的架构思路，板载 USB 为 FS Type-C、FDCAN2 裁剪、音频候选为 SAI2。

---

## 1. 文档说明

| 项目 | 内容 |
| --- | --- |
| MCU 型号 | **STM32H743IIT6**（LQFP176） |
| 原理图 | Rev-B 工程未随本仓库发布（发布板为 Rev-C，见 `kicad/stm32h743-coreboard-revc/`）；Rev-B 阶段 KiCad 10.0.5 ERC 有 1 条 U3 `lib_symbol_mismatch` warning（Rev-C 上同样存在，见 README） |
| 架构形态 | SoM 核心板，4× 2×20 排针（J1~J4）引出 |
| 引脚来源 | STMicroelectronics/STM32_open_pin_data 官方 XML + ST 官方板 .ioc 交叉验证 |

---

## 2. 引脚分配总表（按外设）

### 2.1 电源与系统（板载）

| 信号 | MCU 引脚 | 说明 |
| --- | --- | --- |
| VDD ×14 / VDD33_USB / PDR_ON | 物理脚 15,23,36,49,62,72,82,91,103,114,127,136,149,159,172 / **171(PDR_ON 必须拉高)** | 全部接 3V3；每脚旁 100nF 去耦 |
| VSS ×12 / VSSA | 14,22,48,61,71,90,102,113,126,135,148,158 / 37 | VSSA 经 0Ω(R12) 单点接 GND |
| VDDA | 39 | LP5907-3.3 独立 LDO 供电（U4） |
| VREF+ | 38 | VDDA 经磁珠 FB1 + 1µF |
| VCAP1 / VCAP2 | 81 / 125 | **各 1×2.2µF 低 ESR** 接地（注意：LQFP176 有两个 VCAP） |
| VBAT | 6 | 3V3→BAT54J→220Ω→0.22F 超级电容，并引出 J4-20 |
| NRST | 31 | 10k 上拉 + 100nF，引出 J4-18 |
| BOOT0 | 166 | 10k 下拉，引出 J4-19 |
| HSE 25MHz | PH0 / PH1 | 2×18pF 负载电容 |
| LSE 32.768kHz | PC14 / PC15 | 2×18pF |
| SWD | PA13(SWDIO) / PA14(SWCLK) | 引出 J4-13/14 |
| USB FS | PA11(DM) / PA12(DP) | 板载 Type-C（经 USBLC6 + 22Ω 串阻） |
| USART1 | PA9(TX) / PA10(RX) | 调试串口，引出 J4-15/16。**注意：固件需关闭 USB VBUS sensing**（PA9 与 VBUS 检测复用） |
| LED 用户灯 | PG9（高电平点亮，1k 限流） | |
| 按键 | PC13（按下接地，内部上拉） | |

### 2.2 FMC SDRAM 16 位总线（板载，不引出，**U2 引脚已核实**）

U2 是 `IS42S16160J-6BLI`，使用 54-ball TF-BGA（8×8mm、0.8mm pitch）。其 x16 组织为 4M×16×4 bank：行地址 A0–A12、列地址 A0–A8、BA0/BA1、DQ0–DQ15、DQML/DQMH；commercial/industrial refresh 为 8K/64ms。信号到 BGA 球位的映射见下表，来源为 ISSI Rev.C4 数据表第 6 页。

| 信号 | MCU 引脚 | U2 BGA 球位 | 信号 | MCU 引脚 | U2 BGA 球位 |
| --- | --- | --- | --- | --- | --- |
| FMC_D0 | PD14 | A8 | FMC_A0 | PF0 | H7 |
| FMC_D1 | PD15 | B9 | FMC_A1 | PF1 | H8 |
| FMC_D2 | PD0 | B8 | FMC_A2 | PF2 | J8 |
| FMC_D3 | PD1 | C9 | FMC_A3 | PF3 | J7 |
| FMC_D4 | PE7 | C8 | FMC_A4 | PF4 | J3 |
| FMC_D5 | PE8 | D9 | FMC_A5 | PF5 | J2 |
| FMC_D6 | PE9 | D8 | FMC_A6 | PF12 | H3 |
| FMC_D7 | PE10 | E9 | FMC_A7 | PF13 | H2 |
| FMC_D8 | PE11 | E1 | FMC_A8 | PF14 | H1 |
| FMC_D9 | PE12 | D2 | FMC_A9 | PF15 | G3 |
| FMC_D10 | PE13 | D1 | FMC_A10 | PG0 | H9 |
| FMC_D11 | PE14 | C2 | FMC_A11 | PG1 | G2 |
| FMC_D12 | PE15 | C1 | FMC_A12 | PG2 | G1 |
| FMC_D13 | PD8 | B2 | FMC_BA0 | PG4 | G7 |
| FMC_D14 | PD9 | B1 | FMC_BA1 | PG5 | G8 |
| FMC_D15 | PD10 | A2 | FMC_SDCLK | PG8 | F2 |
| FMC_NBL0 | PE0 | E8 (DQML) | FMC_SDNCAS | PG15 | F7 |
| FMC_NBL1 | PE1 | F1 (DQMH) | FMC_SDNRAS | PF11 | F8 |
| | | | FMC_SDNWE | PH5 | F9 |
| | | | FMC_SDNE0 | PH3 | G9 |
| | | | FMC_SDCKE0 | PH2 | F3 |

> PG2 is now reserved for `FMC_A12`; J4 pin 26 is deliberately unconnected in Rev-B and must not be re-exported as GPIO. The final `.ioc`, schematic and PCB must retain this same mapping.

### 2.3 QSPI（引出 J1）

| 信号 | MCU 引脚 | | 信号 | MCU 引脚 |
| --- | --- | --- | --- | --- |
| QUADSPI_CLK | PB2 | | QUADSPI_BK1_IO2 | PF7 |
| QUADSPI_BK1_NCS | PB10 | | QUADSPI_BK1_IO3 | PF6 |
| QUADSPI_BK1_IO0 | PF8 | | | |
| QUADSPI_BK1_IO1 | PF9 | | | |

### 2.4 SDMMC1 eMMC / SDMMC2 SD 卡（引出 J1）

| 信号 | MCU 引脚 | | 信号 | MCU 引脚 |
| --- | --- | --- | --- | --- |
| SDMMC1_CK | PC12 | | SDMMC2_CK | PD6 |
| SDMMC1_CMD | PD2 | | SDMMC2_CMD | PD7 |
| SDMMC1_D0~D3 | PC8/PC9/PC10/PC11 | | SDMMC2_D0~D3 | PB14/PB15/PB3/PB4 |
| EMMC_VSEL | PE3（GPIO） | | SD_CD | PE4（GPIO） |

### 2.5 RMII 以太网（引出 J2，9 根）

| 信号 | MCU 引脚 | 说明 |
| --- | --- | --- |
| ETH_REF_CLK | PA1 | 50MHz 由扩展板 PHY 提供（PHY 自带晶振），未用 MCO |
| ETH_MDIO / ETH_MDC | PA2 / PC1 | |
| ETH_CRS_DV | PA7 | |
| ETH_RXD0 / RXD1 | PC4 / PC5 | |
| ETH_TX_EN / TXD0 / TXD1 | PB11 / PB12 / PB13 | TX 走 PB 口（与 LTDC 的 PG12~PG14 让位） |
| ~~ETH_RXER~~ | 无可用引脚 | PB10 与 SDMMC2 冲突已用；RMII 可不接 RXER，错误由 CRC 处理 |

### 2.6 LTDC RGB565（引出 J3，20 根，全部落定）

> 采用**高位对齐**：屏侧 R[4:0]=MCU R3~R7，G[5:0]=MCU G2~G7，B[4:0]=MCU B3~B7。扩展板接线按此映射。

| 信号 | MCU 引脚 | | 信号 | MCU 引脚 |
| --- | --- | --- | --- | --- |
| LTDC_PCLK | PG7 | | LTDC_G4 | PH15 |
| LTDC_HSYNC | PI10 | | LTDC_G5 | PI0 |
| LTDC_VSYNC | PI9 | | LTDC_G6 | PI1 |
| LTDC_DE | PF10 | | LTDC_G7 | PI2 |
| LTDC_R3 | PH9 | | LTDC_B3 | PA8 |
| LTDC_R4 | PH10 | | LTDC_B4 | PI4 |
| LTDC_R5 | PH11 | | LTDC_B5 | PI5 |
| LTDC_R6 | PH12 | | LTDC_B6 | PI6 |
| LTDC_R7 | PG6 | | LTDC_B7 | PI7 |
| LTDC_G2 | PH13 | | | |
| LTDC_G3 | PH14 | | | |

### 2.7 SAI2 音频 + I2C（引出 J3）

| 信号 | MCU 引脚 | 说明 |
| --- | --- | --- |
| SAI2_SCK_A / FS_A / SD_A | PD13 / PD12 / PD11 | 3 线；**MCLK 由音频扩展板有源晶振自供**（SAI1 引脚被 LTDC 占用） |
| I2C1_SCL / SDA | PB6 / PB7 | 控制 Codec / 触摸 |

### 2.8 FDCAN（引出 J4，仅 CAN1）

| 信号 | MCU 引脚 | 说明 |
| --- | --- | --- |
| FDCAN1_TX / RX | PB9 / PB8 | **FDCAN2 已取消**：TX 仅 PB6/PB13、RX 仅 PB5/PB12，均被 I2C1/以太网/ULPI 占用（官方复用表核实无解） |

### 2.9 ADC（引出 J4，4 路）

| 信号 | MCU 引脚 | ADC 通道（CubeMX 自动识别） |
| --- | --- | --- |
| ADC_A0 | PA0 | ADC1/2_INP16 |
| ADC_A1 | PA3 | ADC1/2_INP15 |
| ADC_A2 | PA5 | ADC1/2_INP19 |
| ADC_A3 | PA6 | ADC1/2_INP3 |

### 2.10 通用 GPIO（引出排针的空闲脚）

| 排针 | 引脚 |
| --- | --- |
| J2 | PA4, PA15, PB0, PB1, PB5, PC0, PC2_C, PC3_C, PC7, PD3 |
| J3 | PE5, PE6（显示板备用） |
| J4 | PD4, PD5, PE2, PG2, PG3, PG11, PG12, PG13, PG14, PH4, PH6, PH7, PH8, PI3, PI8 |
| 板内未用 | PG10（NC），PI11（NC） |

---

## 3. 排针物理引脚表（2×20，脚位 1~20 左列 / 21~40 右列）

### J1 存储（QSPI + eMMC + SD）

| Pin | 网络 | Pin | 网络 |
| --- | --- | --- | --- |
| 1 | 3V3 | 21 | 5V_HDR |
| 2 | QSPI_CLK | 22 | SDMMC2_D1 |
| 3 | GND | 23 | GND |
| 4 | QSPI_NCS | 24 | SDMMC2_D2 |
| 5 | QSPI_IO0 | 25 | SDMMC2_D3 |
| 6 | QSPI_IO1 | 26 | EMMC_VSEL |
| 7 | GND | 27 | GND |
| 8 | QSPI_IO2 | 28 | SD_CD |
| 9 | QSPI_IO3 | 29 | NC |
| 10 | SDMMC1_CK | 30 | NC |
| 11 | SDMMC1_CMD | 31 | NC |
| 12 | GND | 32 | GND |
| 13 | SDMMC1_D0 | 33 | NC |
| 14 | SDMMC1_D1 | 34 | NC |
| 15 | SDMMC1_D2 | 35 | NC |
| 16 | SDMMC1_D3 | 36 | NC |
| 17 | GND | 37 | GND |
| 18 | SDMMC2_CK | 38 | NC |
| 19 | SDMMC2_CMD | 39 | NC |
| 20 | SDMMC2_D0 | 40 | NC |

### J2 通信（RMII + 通用 GPIO）

| Pin | 网络 | Pin | 网络 |
| --- | --- | --- | --- |
| 1 | 3V3 | 21 | 5V_HDR |
| 2 | ETH_REF_CLK | 22 | GPIO_PC2C |
| 3 | GND | 23 | GND |
| 4 | ETH_MDIO | 24 | GPIO_PC3C |
| 5 | ETH_MDC | 25 | GPIO_PC7 |
| 6 | ETH_CRS_DV | 26 | GPIO_PD3 |
| 7 | GND | 27 | GND |
| 8 | ETH_RXD0 | 28 | NC |
| 9 | ETH_RXD1 | 29 | NC |
| 10 | ETH_TX_EN | 30 | NC |
| 11 | ETH_TXD0 | 31 | NC |
| 12 | GND | 32 | GND |
| 13 | ETH_TXD1 | 33 | NC |
| 14 | GPIO_PA4 | 34 | NC |
| 15 | GPIO_PA15 | 35 | NC |
| 16 | GPIO_PB0 | 36 | NC |
| 17 | GND | 37 | GND |
| 18 | GPIO_PB1 | 38 | NC |
| 19 | GPIO_PB5 | 39 | NC |
| 20 | GPIO_PC0 | 40 | NC |

### J3 显示/音频（LTDC + SAI2 + I2C）

| Pin | 网络 | Pin | 网络 |
| --- | --- | --- | --- |
| 1 | 3V3 | 21 | GND |
| 2 | LTDC_PCLK | 22 | LTDC_B3 |
| 3 | GND | 23 | GND |
| 4 | LTDC_HSYNC | 24 | LTDC_B4 |
| 5 | LTDC_VSYNC | 25 | LTDC_B5 |
| 6 | LTDC_DE | 26 | LTDC_B6 |
| 7 | GND | 27 | GND |
| 8 | LTDC_R3 | 28 | LTDC_B7 |
| 9 | LTDC_R4 | 29 | SAI2_SCK_A |
| 10 | LTDC_R5 | 30 | SAI2_FS_A |
| 11 | LTDC_R6 | 31 | SAI2_SD_A |
| 12 | GND | 32 | GND |
| 13 | LTDC_R7 | 33 | I2C1_SCL |
| 14 | LTDC_G2 | 34 | I2C1_SDA |
| 15 | LTDC_G3 | 35 | GPIO_PE5 |
| 16 | LTDC_G4 | 36 | GPIO_PE6 |
| 17 | GND | 37 | GND |
| 18 | LTDC_G5 | 38 | NC |
| 19 | LTDC_G6 | 39 | NC |
| 20 | LTDC_G7 | 40 | NC |

### J4 CAN/ADC/调试/系统

| Pin | 网络 | Pin | 网络 |
| --- | --- | --- | --- |
| 1 | 3V3 | 21 | GND |
| 2 | FDCAN1_TX | 22 | GPIO_PD4 |
| 3 | GND | 23 | GND |
| 4 | FDCAN1_RX | 24 | GPIO_PD5 |
| 5 | VDDA | 25 | GPIO_PE2 |
| 6 | VREF+ | 26 | GPIO_PG2 |
| 7 | GND | 27 | GND |
| 8 | ADC_A0 | 28 | GPIO_PG3 |
| 9 | ADC_A1 | 29 | GPIO_PG11 |
| 10 | ADC_A2 | 30 | GPIO_PG12 |
| 11 | ADC_A3 | 31 | GPIO_PG13 |
| 12 | GND | 32 | GND |
| 13 | SWDIO | 33 | GPIO_PG14 |
| 14 | SWCLK | 34 | GPIO_PH4 |
| 15 | USART1_TX | 35 | GPIO_PH6 |
| 16 | USART1_RX | 36 | GPIO_PH7 |
| 17 | GND | 37 | GND |
| 18 | NRST | 38 | GPIO_PH8 |
| 19 | BOOT0 | 39 | GPIO_PI3 |
| 20 | VBAT | 40 | GPIO_PI8 |

---

## 4. CubeMX 生成输入与前置条件（Rev-B）

> U2 的 SDRAM geometry、BGA 球位和 PG2/A12 复用已核实；完整 `.ioc` 仍需在 PCB electrical closure 前创建并纳入版本控制。

1. FMC → SDRAM：Bank1 / SDNE0 / SDCKE0，**16-bit**，4 bank，行地址 **A0–A12（13 bit）**，列地址 **A0–A8（9 bit）**，BA0/BA1。数据表为 256Mbit / 32MiB 的 x16 组织；不得复用 Rev-A 的 12 行地址、4096 refresh 行或 16 MiB 参数。
2. Refresh：commercial/industrial grade 为 **8K / 64ms**。最终 `.ioc` 必须记录实际 FMC clock、CubeMX refresh count、计算公式和数据表页号；不得使用 Rev-A 的 64ms/4096 行数值。
3. Timing：`-6` 速度档为 166MHz maximum、CL3 6ns minimum clock period。当前 100MHz FMC 目标仍需用数据表 AC timing 表和实际板级 SI 复核，不能只依靠速度档名。
4. USB_OTG_FS：保持 Device_Only 候选方案；PA9 与 USART1_TX 共存时，必须在最终 `.ioc` 中明确关闭或正确处置 VBUS sensing。若 USB 时钟使用 HSI48，必须显式启用 HSI48 并以枚举测试佐证。
5. Pin mux：PG2 固定为 `FMC_A12`，J4-26 不导出 GPIO。最终 `.ioc` 必须证明所有剩余排针/GPIO 无冲突；CubeMX 全绿不能替代原理图、PCB 和 BGA 球位审核。
6. Cache/DMA：生成工程必须包含 MPU/D-cache 策略。任何由 LTDC 或 DMA 与 CPU 共享的 FMC SDRAM 区域都需要经过一致性压力测试。

## 5. 遗留风险与备注

- **FDCAN2 / USB HS(ULPI) / RXER 已裁剪**（官方复用表核实物理互斥无解），后续如需恢复须重排架构。
- SDRAM 16 位带宽 ≈200MB/s @100MHz，跑 RGB565(800×480@60≈46MB/s) 充裕。
- VDDA 用 LP5907 独立供电；VSSA 经 0Ω 单点接地——PCB 布线时模拟区独立铺铜、单点回流。
-超级电容充电链（BAT54J+220Ω）充电约 1 分钟，掉电后 RTC 可维持数小时~数天（0.22F × 3V ÷ RTC 1~2µA）。

## 6. PCB 预布局（历史预布局记录）

### 6.1 文件与叠层

| 项 | 值 |
|---|---|
| PCB 文件 | 本节为历史预布局记录；发布板见 `kicad/stm32h743-coreboard-revc/stm32h743-coreboard-revc.kicad_pcb` |
| 板尺寸 | 70 × 70 mm 矩形（四边各容纳 1 条 2×20 排针，跨距 50.8mm） |
| 叠层 | 4 层：F.Cu 信号 / **In1.Cu 完整 GND 平面**（已铺） / In2.Cu 电源（预留给 3V3 主平面，布线阶段铺） / B.Cu 信号+GND（已铺） |
| 网表同步 | 以 `kicad/stm32h743-coreboard-revc/revc.netlist` 与板文件为准（本节计数为历史预布局时点记录） |
| 设计规则 | 间距 0.2 / 默认线宽 0.25 / 最小线宽 0.15 / 过孔 0.6-0.3（最小 0.45-0.2），兼容 JLC 4 层工艺 |

### 6.2 布局分区（坐标原点=左上角，单位 mm）

```
J2 通信排针(顶边 y≈3.7)  [Y1/Y2晶振 x≈11-20] [顶部去耦电容阵 x≈26-44]  SW1/R1-R4
J4 CAN/ADC/DBG          U1 MCU (35,35) LQFP176居中                      右上去耦
排针(左边 x≈3.7)                                                        U4 LP5907
                        U2 SDRAM (35,56) 横放                            Q1/Q2 ORing
CRTC/D1/R9                                                            U3 TPS62085+L1
VBAT链(左下 x≈9-21)                                                     +R10/R11+C27/C29
J1 存储排针(底边 y≈66.3, x≈2.9-51)      U6 USBLC6(51.8,61) F1(54.8,66)  J5 USB-C(62,68.5)
```

- **U2 SDRAM** (35,56) 转 90° 横放，卡在 U1 与 J1 之间：FMC 数据线（PD/PE，U1 左/下侧）与地址线（PF/PG，U1 右侧）两侧等距，In1 参考平面完整。
- **去耦电容**：U1 顶部 5 列交错阵列（x=26.5~42.5，对应顶边 VDD 引脚密集区）；左侧一列纵队（x≈17-19，y=22-50）服务 U1 左侧电源脚；U2 与电源岛各自就近。
- **四排针几何中心**已精确居中于四边（J1/J2 旋转 90°）。注意 KiCad 排针封装原点在第 1 脚而非几何中心，坐标已按实测偏移校正。
- **TPS62085 封装** `coreboard:Texas-VSON-7-HR`：取自 LSF 开源库（LSF 立方星在飞验证），焊盘与 TI 数据手册 RLT 封装一致（1-4 脚左侧 0.5 间距小焊盘，5-7 脚 GND/SW/VIN 右侧大电流焊盘带钢网分割）。

### 6.3 布局遗留事项（布线阶段处理）

1. **覆铜区未填充**：In1/B.Cu 的 GND zone 已画好但未 fill——KiCad GUI 打开后按 `B` 键填充。
2. In2.Cu 建议铺 3V3 大平面 + 5V 局部（电源岛下方区域）。
3. SDMMC/ETH 相对等长（±1mm 量级）；FMC 时钟 PG8 与数据线参考同一 In1 平面即可满足 100MHz。
4. 未布安装孔：SoM 靠 160 根排针机械固定，如底板需要可后续四角加 M2。
5. USB 差分对 PA11/PA12：J5→U6→22Ω→U1 走 F.Cu 短线，90Ω 差分阻抗控制可选。
