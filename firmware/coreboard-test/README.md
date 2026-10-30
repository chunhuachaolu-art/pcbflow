# STM32H743 核心板 - 上电验证固件 (coreboard-test)

> 核心板（SoM）焊接完成后的第一份固件。插 Type-C 上电即可逐项验证核心板硬件是否正常：
> LED、USART1、USB CDC、FMC SDRAM。全部 PASS 即代表核心板可投入后续载板/扩展板开发。

---

## 1. 固件用途

本固件用于 **STM32H743IIT6（LQFP176）核心板** 的上电自检（Power-On Self Test），覆盖核心板全部板载功能：

| 验证项 | 验证目标 | 通过判据 |
| --- | --- | --- |
| 系统时钟 | HSE 25MHz 晶振 + PLL 起振，SYSCLK 正常 | 打印 `SYSCLK = 480 MHz`、`HCLK = 240 MHz` |
| LED | 用户 LED GPIO 与焊接 | LED 肉眼可见闪烁 3 次 |
| USART1 | PA9/PA10 调试串口（J4 排针） | 串口助手 @115200 8N1 收到日志 |
| USB CDC | Type-C（PA11/PA12）USB OTG-FS | Windows 设备管理器出现 `COMx`，收到日志 |
| SDRAM | 板载 16MB FMC SDRAM（Bank5/6, 32-bit） | 5 项内存测试全部 PASS，errors=0 |

> 本固件 **不测** 排针引出的扩展信号（QSPI/SDMMC/ULPI/RMII/LTDC 等）——
> 那些属于扩展板/载板的职责，排针连通性用万用表逐脚测（见 plan Task 19）。

**核心板功能范围**（本固件覆盖）：MCU + SDRAM(16MB) + USB FS(Type-C CDC) + 电源 + 25MHz 晶振。

---

## 2. 前置条件

### 2.1 硬件前置

- 核心板已焊接完成，目检无桥连/短路（plan 阶段 5 / Task 15 G15 通过）
- Type-C 供电正常：`VDD_3V3 = 3.3V ±2%`，`VDDA_3V3 = 3.3V`（Task 13 G13）
- SWD 能连接 MCU（Task 14 G14）—— 烧录用
- 25MHz HSE 晶振起振（示波器测 PH0/PH1）

### 2.2 STM32CubeMX 配置

基于 `design/coreboard/pinmap/stm32h743-coreboard.ioc`（plan Task 1 产出），需在 CubeMX 中启用以下外设：

| 外设 | CubeMX 配置 | 引脚 | 说明 |
| --- | --- | --- | --- |
| **RCC / Clock** | HSE = Crystal 25MHz；PLL1: M=5,N=96,P=1 → SYSCLK=480MHz，HCLK=240MHz；USB FS 取 48MHz；FMC_SDCLK ≤ 100MHz | PH0/PH1 (HSE) | 时钟树无红色告警（plan Task 2 G2） |
| **USB_OTG_FS** | Mode = `Device_Only` | PA11 (DM), PA12 (DP) | 板载 Type-C，**不引出排针** |
| **USB_DEVICE** | Middleware → Class = `Communication Device Class (Virtual Port Com)` | — | 生成 `usbd_cdc_if.c`，提供 `CDC_Transmit_FS()` |
| **USART1** | Mode = `Asynchronous`，Baud = 115200, 8N1 | PA9 (TX), PA10 (RX) | 调试串口，引出到 J4 |
| **FMC** | Mode = `SDRAM`，Bank5/6，32-bit，CAS=3, tRCD=3, tRP=3，Refresh=64ms/8192 行 | FMC_D0~31 / A0~11 / 控制信号 / NBL0~3 | 见 §2.4 时序参数 |
| **GPIO (LED)** | 1 个 Output（Push-Pull, High, Pull-No） | 见 pinmap §3.14 `LED_USER`（CubeMX 生成 `LED_USER_GPIO_Port` / `LED_USER_Pin`） | 用户 LED，高电平点亮（按原理图） |
| **GPIO (按键)** | 1 个 Input（可选，本固件未用） | 见 pinmap §3.14 `BTN_USER` | 预留 |

引脚分配以 [`design/coreboard/pinmap/pinmap-reference.md`](../../design/coreboard/pinmap/pinmap-reference.md) 为准。

### 2.3 USB CDC 中间件说明

CubeMX 启用 `USB_DEVICE → CDC` 后会生成：
- `usbd_cdc_if.c` / `usbd_cdc_if.h` —— 提供 `CDC_Transmit_FS(uint8_t* Buf, uint16_t Len)`
- `usbd_device.c` —— 提供 `hUsbDeviceFS` 句柄（本固件 `extern` 引用）

本固件 `main_app.c` **直接调用** `CDC_Transmit_FS`，不依赖 `printf` 重定向，无需改写 `_write` / `fputc`。

### 2.4 SDRAM 时序参数与初始化序列（关键）

板载 SDRAM：**IS42S32800G-6BLI，4M×32-bit = 16MB**，挂 FMC Bank5（`SDNE0/SDCKE0`）。

CubeMX `MX_FMC_Init()` **只配置了 FMC 寄存器**，不会发送 SDRAM Mode Register 设置命令。
**必须在 `MX_FMC_Init()` 之后手动执行 SDRAM 初始化序列**，否则 SDRAM 无法正常读写。

| 参数 | 值 |
| --- | --- |
| 容量 | 16MB (4M × 32-bit) |
| 数据总线 | 32-bit (FMC_D0~D31, NBL0~NBL3) |
| FMC Bank | Bank5 (`SDNE0/SDCKE0`，基地址 `0xC0000000`) |
| CAS Latency | 3 |
| tRCD (RAS-to-CAS) | 3 |
| tRP (Precharge) | 3 |
| 刷新周期 | 64ms / 8192 行（每行 7.8125μs） |
| FMC_SDCLK | ≤ 100MHz（H743 FMC 分频后） |

**SDRAM 初始化序列**（参考 ST 官方 `BSP_SDRAM_Initialization_sequence`，需用户在工程中实现并在 `MX_FMC_Init()` 后调用）：

```c
/* 伪代码：完整实现见 ST 例程 STM32H743I-EVAL/Utilities */
#define SDRAM_MODEREG_BURST_LENGTH_1    (0x0 << 0)
#define SDRAM_MODEREG_BURST_TYPE_SEQUENTIAL (0x0 << 3)
#define SDRAM_MODEREG_CAS_LATENCY_3     (0x3 << 4)
#define SDRAM_MODEREG_WRITEBURST_MODE_SINGLE (0x0 << 9)

static void BSP_SDRAM_Initialization_sequence(void)
{
    FMC_SDRAM_CommandTypeDef cmd = {0};

    /* Step 1: 时钟使能命令 */
    cmd.CommandMode            = FMC_SDRAM_CMD_CLK_ENABLE;
    cmd.CommandTarget          = FMC_SDRAM_CMD_TARGET_BANK1;   /* Bank5 */
    cmd.AutoRefreshNumber      = 1;
    cmd.ModeRegisterDefinition = 0;
    HAL_SDRAM_SendCommand(&hsdram1, &cmd, 0xFFFF);

    /* Step 2: 100us 延时（SDRAM 上电稳定） */
    HAL_Delay(1);

    /* Step 3: 对所有 bank 预充电 */
    cmd.CommandMode = FMC_SDRAM_CMD_PALL;
    HAL_SDRAM_SendCommand(&hsdram1, &cmd, 0xFFFF);

    /* Step 4: 自动刷新 2 次 */
    cmd.CommandMode       = FMC_SDRAM_CMD_AUTOREFRESH_MODE;
    cmd.AutoRefreshNumber = 8;
    HAL_SDRAM_SendCommand(&hsdram1, &cmd, 0xFFFF);

    /* Step 5: 加载 Mode Register */
    cmd.CommandMode            = FMC_SDRAM_CMD_LOAD_MODE;
    cmd.AutoRefreshNumber      = 1;
    cmd.ModeRegisterDefinition = SDRAM_MODEREG_BURST_LENGTH_1
                               | SDRAM_MODEREG_BURST_TYPE_SEQUENTIAL
                               | SDRAM_MODEREG_CAS_LATENCY_3
                               | SDRAM_MODEREG_WRITEBURST_MODE_SINGLE;
    HAL_SDRAM_SendCommand(&hsdram1, &cmd, 0xFFFF);

    /* Step 6: 设置自刷新率（64ms/8192 行 → 计数器值，按 SDCLK 折算） */
    extern SDRAM_HandleTypeDef hsdram1;
    HAL_SDRAM_ProgramRefreshRate(&hsdram1, REFRESH_RATE_COUNT);
}
```

> 调用时机：`main.c` 中 `MX_FMC_Init();` 之后、`app_run_verification();` 之前。
> `hsdram1`、`REFRESH_RATE_COUNT` 按 CubeMX 生成的句柄名与时钟频率折算。

---

## 3. 集成步骤

### Step 1: CubeMX 生成工程

基于 `stm32h743-coreboard.ioc`，按 §2.2 配置好外设后，生成 HAL 工程（选 MDK-ARM 或 STM32CubeIDE）。
工程根目录即 `firmware/coreboard-test/`。

### Step 2: 加入本固件文件

把以下文件加入工程（拖入 IDE 工程 / 加入编译列表）：

| 文件 | 作用 |
| --- | --- |
| `main_app.c` | 验证主流程、`log_print`、`app_run_verification()`（**本固件**） |
| `sdram_test.h` / `sdram_test.c` | 5 项 SDRAM 测试（外部模块，接口见头部注释） |

> `main_app.c` 通过 `#include "usbd_cdc_if.h"`、`#include "sdram_test.h"`、`extern huart1/hUsbDeviceFS`
> 引用 CubeMX 生成物，无需修改 CubeMX 文件。

### Step 3: 在 main.c 中调用验证入口

打开 CubeMX 生成的 `main.c`，在 `USER CODE BEGIN 2` / `END 2` 区块（`while(1)` 之前）加：

```c
/* USER CODE BEGIN 2 */
BSP_SDRAM_Initialization_sequence();   /* §2.4 SDRAM 初始化序列（必做）*/
app_run_verification();                /* 核心板验证入口，内部含心跳循环，不返回 */
/* USER CODE END 2 */

/* Infinite loop */
/* USER CODE BEGIN WHILE */
while (1)
{
    /* app_run_verification() 内部已含心跳循环，不会走到这里 */
    /* USER CODE END WHILE */
    /* USER CODE BEGIN 3 */
}
/* USER CODE END 3 */
```

> `app_run_verification()` 内部已包含心跳死循环（每 1s 发 `ALIVE` + LED 翻转），故 `main.c` 的 `while(1)`
> 实际不会执行。这样设计是为了把验证与心跳逻辑集中维护。

### Step 4: 日志输出（已在 main_app.c 处理）

`log_print()` 内部已同时调用 `CDC_Transmit_FS` 和 `HAL_UART_Transmit(&huart1)`，**无需再重定向 `printf`**。

若要关闭某一路输出，在编译选项（Keil: Options → C/C++ → Define；CubeIDE: 项目属性 → C build → Settings → Preprocessor）里加宏：

| 宏 | 作用 |
| --- | --- |
| `LOG_ENABLE_USB=0` | 关闭 USB CDC 输出（仅 USART1） |
| `LOG_ENABLE_USART=0` | 关闭 USART1 输出（仅 USB CDC） |

默认两者都启用。

### Step 5: 编译下载

- 编译工程（见 §6 编译说明）
- 通过 SWD（DAP-Link / ST-Link）烧录到核心板
- Type-C 上电（或保持 SWD 供电），观察 LED + 串口/CDC 输出

---

## 4. 预期输出（验证成功示例）

> Type-C 接 PC（USB CDC）或 USB-TTL 接 J4 的 USART1（PA9/PA10，115200 8N1），均可看到以下输出。
> 带时间戳的 `[N]` 是心跳计数。

```
=== STM32H743 Core Board Verification ===
Build target : STM32H743IIT6 (LQFP176)
SYSCLK       : 480000000 Hz (480 MHz)
HCLK         : 240000000 Hz (240 MHz)
Log output   : USB CDC (primary)
Log output   : USART1 @ PA9/PA10 (backup, 115200 8N1)

[LED] Blink test: 3 times x 200ms ...
  Result: PASS (visual check)

--- SDRAM Test (16MB @ 0xC0000000) ---
[Test 1: Fixed Pattern 0xAA55] ... RUNNING
  Result: PASS, Time: 842 ms
[Test 2: Address Bus] ... RUNNING
  Result: PASS, Time: 1105 ms
[Test 3: Anti-Pattern 0x55AA] ... RUNNING
  Result: PASS, Time: 878 ms
[Test 4: Marching] ... RUNNING
  Result: PASS, Time: 4521 ms
[Test 5: Random] ... RUNNING
  Result: PASS, Time: 1290 ms

--- SDRAM Summary ---
  Passed : 5 / 5
  Failed : 0 / 5
  Result : ALL PASS

=== Verification complete. Entering heartbeat loop. ===
(LED blinks + "ALIVE" sent every 1000 ms)

[0] ALIVE
[1] ALIVE
[2] ALIVE
...
```

**全部判据**：
- SYSCLK = 480 MHz（晶振 + PLL 正常）
- LED 肉眼闪烁 3 次后持续心跳闪烁
- 5 项 SDRAM 测试全部 `PASS`，`Failed : 0 / 5`
- 之后每秒收到 `[N] ALIVE`

只要以上满足，即 **核心板核心功能验证通过**（plan Task 18 G18），可投入 Phase 2 载板开发。

---

## 5. 故障排查表

> 对应 plan Task 16-18 的常见失败场景。按现象 → 可能原因 → 排查动作 组织。

### 5.1 LED 不闪 / 不亮

| 可能原因 | 排查动作 |
| --- | --- |
| GPIO 未在 CubeMX 配置为 Output | 检查 `LED_USER_GPIO_Port`/`LED_USER_Pin` 宏是否在 `main.h` 生成 |
| LED 极性反（阴极接 GPIO，需低电平点亮） | 改 `main_app.c` 的 `LED_ON()`/`LED_OFF()` 宏的电平（SET↔RESET 互换） |
| 焊接虚焊/桥连 | 万用表测 LED 两端电压翻转时是否变化；放大镜复查焊接 |
| GPIO 与其他外设复用冲突 | CubeMX 引脚面板是否红色告警（plan Task 1 Step 11） |
| 固件没烧进去 / 没运行 | SWD 单步调试，确认 `app_run_verification()` 被调用 |

### 5.2 USART1 无输出（PA9/PA10）

| 可能原因 | 排查动作 |
| --- | --- |
| 波特率不对 | 串口助手必须 **115200 8N1 无流控** |
| PA9/PA10 焊接虚焊 | 万用表/示波器测 PA9 有无数据波形 |
| USB-TTL 接线错误 | USB-TTL 的 **RXD 接 PA9(TX)**，**TXD 接 PA10(RX)**，**GND 共地** |
| HCLK 实际频率与配置不符 → 波特率偏差 | 确认 SYSCLK=480MHz/HCLK=240MHz；若晶振没起振会用 HSI，波特率会错 |
| `LOG_ENABLE_USART` 被关闭 | 检查编译宏是否误加 `LOG_ENABLE_USART=0` |
| USART1 在 CubeMX 未启用 | CubeMX 中 USART1 Mode = Asynchronous |

### 5.3 USB CDC 不枚举 / 枚举后无数据

| 可能原因 | 排查动作 |
| --- | --- |
| D+/D- 焊接虚焊/桥连 | 示波器测 PA11/PA12 上电瞬间的枚举波形 |
| 22Ω 串阻缺焊/阻值错 | 检查 D+/D- 上的 22Ω 串联电阻（Task 4 Step 4） |
| ESD 二极管方向焊反/短路 | 检查 USBLC6-2SC6 焊接 |
| Type-C CC1/CC2 下拉电阻缺焊 | 各 5.1kΩ 下拉到 GND（设备端配置，Task 4 Step 4） |
| VBUS 没到 5V | Type-C 是否插入供电端；保险丝是否断 |
| USB_DEVICE CDC 中间件未启用 | CubeMX 中 USB_DEVICE → Class = CDC |
| `hUsbDeviceFS.dev_state` 一直非 CONFIGURED | CDC 未枚举成功时本固件会跳过 USB 发送（避免 busy）—— 先解决枚举 |
| 数据线只供电不传数据 | 换一根能传数据的 Type-C 线（部分廉价线只走电源） |

### 5.4 SDRAM 测试失败（核心板成败关键）

| 可能原因 | 排查动作 |
| --- | --- |
| FMC 时序参数错（CAS/tRCD/tRP） | 核对 §2.4 与 pinmap-reference §5：CAS=3, tRCD=3, tRP=3 |
| **SDRAM 初始化序列未执行** | 必须在 `MX_FMC_Init()` 后调用 `BSP_SDRAM_Initialization_sequence()`（§2.4） |
| Mode Register 设置命令错 | 检查 `FMC_SDRAM_CMD_LOAD_MODE` 的 CAS 位 |
| 刷新计数器没设/算错 | `HAL_SDRAM_ProgramRefreshRate()`，按 64ms/8192 行 + SDCLK 折算 |
| SDRAM 焊接桥连/虚焊 | 放大镜复查 IS42S32800G（TSOP-54, 0.5mm）每脚；万用表测数据线相邻脚有无短路 |
| FMC 数据/地址线走线等长不足 | 若 DIY 焊接自画板，**先把 FMC_SDCLK 降到 50MHz 重测**（plan 风险提示 1） |
| 数据总线位宽配置错 | 必须 32-bit + NBL0~3（4 个字节屏蔽位），pinmap §3.2 |
| Bank 选错（Bank1/2 vs Bank5/6） | SDRAM 在 Bank5/6（`0xC0000000`），NOR/SRAM 才在 Bank1 |
| `SDRAM_BASE_ADDR` 与实际 Bank 不符 | `sdram_test.h` 应定义 `0xC0000000`（Bank5 起始） |
| 部分 cell 固定失败（行/列地址线粘连） | 看 `[Test 2: Address Bus]` 是否单独 FAIL —— 它专测地址线粘连 |
| 固定型故障（某位恒 0/1） | 看 `[Test 1/3]` FAIL 且 `got` 值有固定为 0 或 1 的 bit → 对应数据线短路/断路 |

> **降频排查法**：若时序失败且怀疑走线，在 CubeMX 把 FMC kernel clock 分频加大（如 SDCLK 降到 50MHz），
> 重新生成 + 跑测试。若降频后 PASS，基本可定位为走线等长/信号完整性问题（plan Task 11 G11）。

---

## 6. 编译说明

支持两种主流工具链。任选其一。

### 6.1 Keil MDK-ARM

1. CubeMX 生成工程时选 **MDK-ARM V5.32**（或更新）
2. 打开 `firmware/coreboard-test/MDK-ARM/stm32h743-coreboard.uvprojx`
3. Project → Manage Project Items → Groups，把 `main_app.c`、`sdram_test.c` 加入 `Application/User` 组
4. Options for Target → C/C++ → Include Paths，加入 `sdram_test.h` 所在目录
5. （可选）Options → C/C++ → Define 加 `LOG_ENABLE_USB=1, LOG_ENABLE_USART=1`（默认已开）
6. Build (F7) → 下载 (F8)
7. 需安装 STM32H7xx DFP（Device Family Pack）

### 6.2 STM32CubeIDE

1. CubeMX 生成工程时选 **STM32CubeIDE**
2. 打开 `firmware/coreboard-test/.cproject` / `.project`
3. 右键工程 → Properties → C/C++ Build → Settings → MCU GCC Compiler → Include paths，加入 `sdram_test.h` 目录
4. 把 `main_app.c`、`sdram_test.c` 拖入 `Application/User` 文件夹（自动加入编译）
5. （可选）Properties → C/C++ Build → Settings → Preprocessor → Defined symbols 加宏
6. Project → Build (Ctrl+B) → Run/Debug 下载

### 6.3 通用注意事项

- 本固件依赖 HAL 库（CubeMX 默认生成），不依赖 RTOS
- 编译器优化建议 **-O0 或 -Og**（验证固件优先可观测性）
- 若链接报 `undefined reference to huart1 / hUsbDeviceFS`：确认 CubeMX 已启用 USART1 和 USB_DEVICE CDC，
  这些句柄在 `usart.c` / `usbd_device.c` 中由 CubeMX 定义
- 若报 `undefined reference to CDC_Transmit_FS`：确认 `usbd_cdc_if.c` 已加入编译（CubeMX 启用 CDC 后自动生成）

---

## 附：文件清单

| 文件 | 说明 |
| --- | --- |
| `firmware/coreboard-test/main_app.c` | **本固件**：验证主流程、log_print、app_run_verification |
| `firmware/coreboard-test/sdram_test.h` | SDRAM 测试模块头文件（外部，接口见 main_app.c 注释） |
| `firmware/coreboard-test/sdram_test.c` | SDRAM 测试模块实现（外部） |
| `firmware/coreboard-test/README.md` | 本文档 |
| CubeMX 生成 | `main.c` / `usart.c` / `usbd_*.c` / `fmc.c` / `stm32h7xx_it.c` 等 |

> 验证通过后，参考 plan Task 20 把本目录与测试报告一并归档（`docs/coreboard-test-report.md`）。
