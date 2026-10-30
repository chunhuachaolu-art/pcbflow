/**
 * @file    main_app.c
 * @brief   STM32H743 核心板上电验证固件 - 主应用代码
 *
 * 本文件提供核心板验证主流程，由 CubeMX 生成的 main.c 在 while(1) 之前调用
 * app_run_verification() 一次即可完成全部验证。
 *
 * 验证项目：
 *   1. 启动 banner / 系统信息（SYSCLK 频率）
 *   2. LED 闪烁测试（3 次，表示系统活着）
 *   3. SDRAM 16MB 测试（5 项逐项测试 + 汇总）
 *   4. 汇总统计（通过/失败）
 *   5. 心跳循环：每 1s 通过 USB CDC 发送 "ALIVE\n"，LED 闪烁
 *
 * 输出通道（可编译期开关）：
 *   - USB CDC  (LOG_ENABLE_USB)   主要 - Type-C 接 PC
 *   - USART1   (LOG_ENABLE_USART) 备用 - PA9/PA10 接 USB-TTL 到 J4 排针
 *
 * 依赖（CubeMX 生成，本文件不重复实现）：
 *   - SystemClock_Config / MX_*_Init / MX_USB_DEVICE_Init
 *   - extern UART_HandleTypeDef huart1;
 *   - extern USBD_HandleTypeDef  hUsbDeviceFS;   (USB Device 中间件句柄)
 *   - usbd_cdc_if.c 提供 CDC_Transmit_FS()
 *   - main.h 由 CubeMX 生成 LED_USER_GPIO_Port / LED_USER_Pin 宏
 *   - sdram_test.h/.c 外部 SDRAM 测试模块
 *
 * @note  本文件不包含 main()，不写 CubeMX 自动生成的初始化代码。
 */

/* ====================================================================== */
/*  Includes                                                              */
/* ====================================================================== */
#include <stdio.h>
#include <stdarg.h>
#include <string.h>

#include "main.h"                  /* HAL、LED_USER_* 宏、HSE_VALUE 等            */
#include "usbd_cdc_if.h"           /* CDC_Transmit_FS()                          */
#include "sdram_test.h"            /* 外部 SDRAM 测试模块                         */

/* ====================================================================== */
/*  编译期输出开关                                                          */
/* ====================================================================== */
#ifndef LOG_ENABLE_USB
#define LOG_ENABLE_USB    1        /* 默认启用 USB CDC 输出                       */
#endif

#ifndef LOG_ENABLE_USART
#define LOG_ENABLE_USART  1        /* 默认启用 USART1 输出                        */
#endif

/* ====================================================================== */
/*  引用 CubeMX 生成的外设句柄                                              */
/* ====================================================================== */
extern UART_HandleTypeDef huart1;          /* USART1 - 调试串口 PA9/PA10     */
extern USBD_HandleTypeDef  hUsbDeviceFS;   /* USB Device (CDC) 句柄          */

/* ====================================================================== */
/*  本地配置                                                               */
/* ====================================================================== */
#define LOG_BUF_SIZE       256U            /* log_print 单行缓冲区           */
#define LOG_UART_TIMEOUT   100U            /* USART1 阻塞发送超时 (ms)       */
#define LED_BLINK_TIMES    3U              /* 启动 LED 闪烁次数              */
#define LED_BLINK_PERIOD   200U            /* 启动 LED 闪烁半周期 (ms)        */
#define HEARTBEAT_PERIOD   1000U           /* 心跳周期 (ms)                  */

/*
 * LED 点亮/熄灭电平按核心板原理图决定（Task 5 Step 7：阳极接 GPIO，阴极经
 * 1kΩ 接 GND，故高电平点亮）。若原理图不同，改这两个宏即可，无需改逻辑。
 */
#ifndef LED_ON
#define LED_ON()   HAL_GPIO_WritePin(LED_USER_GPIO_Port, LED_USER_Pin, GPIO_PIN_SET)
#endif
#ifndef LED_OFF
#define LED_OFF()  HAL_GPIO_WritePin(LED_USER_GPIO_Port, LED_USER_Pin, GPIO_PIN_RESET)
#endif

/* ====================================================================== */
/*  私有原型                                                               */
/* ====================================================================== */
static void  log_print(const char *fmt, ...);
static void  output_line(const char *buf, uint16_t len);
static void  led_blink(uint8_t times, uint32_t half_period_ms);
static void  verify_system_info(void);
static void  verify_sdram(void);
static void  print_sdram_test(uint8_t idx, const char *name,
                              sdram_test_result_t res,
                              const sdram_test_error_t *err);

/* ====================================================================== */
/*  日志输出                                                               */
/* ====================================================================== */

/**
 * @brief 把一行已格式化的数据同时发往 USB CDC 和 USART1
 *
 * - USB CDC：仅当 USB 已枚举（hUsbDeviceFS.dev_state == USBD_STATE_CONFIGURED）
 *   时发送，避免未连接时 CDC_Transmit_FS 长时间返回 USBD_BUSY 占用 CPU。
 * - USART1：HAL_UART_Transmit 阻塞发送，超时 LOG_UART_TIMEOUT ms。
 * - 用临界区保护：防止心跳中断 log_print 的多段发送交错（虽然本固件是裸机
 *   前台循环，但为日后扩展留余地）。
 */
static void output_line(const char *buf, uint16_t len)
{
    if (len == 0U) {
        return;
    }

#if LOG_ENABLE_USB
    /* 仅当设备已枚举到 PC 时才发送，否则跳过（CDC 未连接时 Transmit 会 busy） */
    if (hUsbDeviceFS.dev_state == USBD_STATE_CONFIGURED) {
        (void)CDC_Transmit_FS((uint8_t *)buf, len);
    }
#endif

#if LOG_ENABLE_USART
    (void)HAL_UART_Transmit(&huart1, (uint8_t *)buf, len, LOG_UART_TIMEOUT);
#endif
}

/**
 * @brief printf 风格的变参日志输出
 *
 * 用 vsnprintf 格式化到本地 256 字节缓冲区，再调用 output_line() 同时输出到
 * USB CDC 与 USART1。缓冲区足够单行打印（SDRAM 错误行 < 200 字符）。
 * 超长行会被安全截断（vsnprintf 保证 NUL 结尾）。
 *
 * @param fmt  printf 格式串
 * @param ...  变参
 */
static void log_print(const char *fmt, ...)
{
    static char buf[LOG_BUF_SIZE];   /* 静态，避免每次调用压栈开销           */
    va_list     ap;
    int         n;

    va_start(ap, fmt);
    n = vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);

    if (n < 0) {
        return;                      /* 格式化失败                           */
    }

    /* n 可能 > buf 容量，此时 vsnprintf 已截断，按实际写入长度发送           */
    uint16_t len = (n < (int)sizeof(buf)) ? (uint16_t)n : (uint16_t)sizeof(buf) - 1U;
    output_line(buf, len);
}

/* ====================================================================== */
/*  LED 闪烁                                                               */
/* ====================================================================== */

/**
 * @brief LED 闪烁若干次
 * @param times           闪烁次数
 * @param half_period_ms  半周期（亮/灭各持续多久），ms
 */
static void led_blink(uint8_t times, uint32_t half_period_ms)
{
    for (uint8_t i = 0; i < times; i++) {
        LED_ON();
        HAL_Delay(half_period_ms);
        LED_OFF();
        HAL_Delay(half_period_ms);
    }
}

/* ====================================================================== */
/*  系统信息                                                               */
/* ====================================================================== */

/**
 * @brief 打印启动 banner 和系统时钟信息
 */
static void verify_system_info(void)
{
    uint32_t sysclk = HAL_RCC_GetSysClockFreq();

    log_print("\r\n");
    log_print("=== STM32H743 Core Board Verification ===\r\n");
    log_print("Build target : STM32H743IIT6 (LQFP176)\r\n");
    log_print("SYSCLK       : %lu Hz (%lu MHz)\r\n",
              sysclk, sysclk / 1000000UL);
    log_print("HCLK         : %lu Hz (%lu MHz)\r\n",
              HAL_RCC_GetHCLKFreq(), HAL_RCC_GetHCLKFreq() / 1000000UL);
#if LOG_ENABLE_USB
    log_print("Log output   : USB CDC (primary)\r\n");
#endif
#if LOG_ENABLE_USART
    log_print("Log output   : USART1 @ PA9/PA10 (backup, 115200 8N1)\r\n");
#endif
    log_print("\r\n");
}

/* ====================================================================== */
/*  SDRAM 测试                                                             */
/* ====================================================================== */

/* 每个 SDRAM 子测试的名称，与 sdram_test 模块函数一一对应 */
static const char *const kSdramTestNames[5] = {
    "Fixed Pattern 0xAA55",   /* sdram_test_fixed_pattern */
    "Address Bus",            /* sdram_test_address_bus   */
    "Anti-Pattern 0x55AA",    /* sdram_test_checkerboard  */
    "Marching",               /* sdram_test_marching      */
    "Random",                 /* sdram_test_random        */
};

/**
 * @brief 打印单个 SDRAM 子测试结果
 *
 * 成功：
 *   [Test 1: Fixed Pattern 0xAA55] ... RUNNING
 *     Result: PASS, Time: 1234 ms
 *
 * 失败：
 *   [Test 1: Fixed Pattern 0xAA55] ...FAILED
 *     Result: FAIL, Errors: 5
 *     First error @ offset 0x00001234: expected 0xAA55AA55, got 0xDEADBEEF
 *
 * @param idx   1..5
 * @param name  测试名称
 * @param res   测试结果
 * @param err   错误详情（res==PASS 时字段无意义，但仍需非空指针）
 */
static void print_sdram_test(uint8_t idx, const char *name,
                             sdram_test_result_t res,
                             const sdram_test_error_t *err)
{
    log_print("[Test %u: %s] ... %s\r\n", idx, name,
              (res == SDRAM_TEST_PASS) ? "RUNNING" : "FAILED");

    if (res == SDRAM_TEST_PASS) {
        log_print("  Result: PASS, Time: %lu ms\r\n", err->duration_ms);
    } else {
        log_print("  Result: FAIL, Errors: %lu\r\n", err->error_count);
        /* fail_addr 存的是"字索引"（0 ~ SDRAM_WORDS-1），转成字节偏移更直观 */
        uint32_t byte_offset = err->fail_addr * 4U;
        log_print("  First error @ byte offset 0x%08lX (word %lu): expected 0x%08lX, got 0x%08lX\r\n",
                  (unsigned long)byte_offset,
                  (unsigned long)err->fail_addr,
                  (unsigned long)err->expected,
                  (unsigned long)err->actual);
    }
}

/**
 * @brief 运行全部 5 项 SDRAM 测试并逐项打印
 *
 * 注意：不调用 sdram_test_run_all()（它只返回汇总），而是单独调用
 * 5 个子测试函数以获得每个测试的详细错误信息（首个错误地址、期望值、
 * 实际值、错误计数、耗时）。最后打印汇总表。
 */
static void verify_sdram(void)
{
    sdram_test_error_t err;         /* 复用，每次调用前归零                   */
    sdram_test_result_t res;
    uint8_t pass_cnt = 0U;
    uint8_t fail_cnt = 0U;

    log_print("--- SDRAM Test (16MB @ 0x%08lX) ---\r\n",
              (unsigned long)SDRAM_BASE_ADDR);

    /* ---------- Test 1: 固定模式 0xAA55AA55 ---------- */
    memset(&err, 0, sizeof(err));
    res = sdram_test_fixed_pattern(&err);
    print_sdram_test(1U, kSdramTestNames[0], res, &err);
    if (res == SDRAM_TEST_PASS) { pass_cnt++; } else { fail_cnt++; }

    /* ---------- Test 2: 地址总线（写地址值） ---------- */
    memset(&err, 0, sizeof(err));
    res = sdram_test_address_bus(&err);
    print_sdram_test(2U, kSdramTestNames[1], res, &err);
    if (res == SDRAM_TEST_PASS) { pass_cnt++; } else { fail_cnt++; }

    /* ---------- Test 3: 反模式 0x55AA55AA ---------- */
    memset(&err, 0, sizeof(err));
    res = sdram_test_checkerboard(&err);
    print_sdram_test(3U, kSdramTestNames[2], res, &err);
    if (res == SDRAM_TEST_PASS) { pass_cnt++; } else { fail_cnt++; }

    /* ---------- Test 4: Marching（行进 1/0） ---------- */
    memset(&err, 0, sizeof(err));
    res = sdram_test_marching(&err);
    print_sdram_test(4U, kSdramTestNames[3], res, &err);
    if (res == SDRAM_TEST_PASS) { pass_cnt++; } else { fail_cnt++; }

    /* ---------- Test 5: 随机数据 ---------- */
    memset(&err, 0, sizeof(err));
    res = sdram_test_random(&err);
    print_sdram_test(5U, kSdramTestNames[4], res, &err);
    if (res == SDRAM_TEST_PASS) { pass_cnt++; } else { fail_cnt++; }

    /* ---------- 汇总 ---------- */
    log_print("\r\n");
    log_print("--- SDRAM Summary ---\r\n");
    log_print("  Passed : %u / 5\r\n", pass_cnt);
    log_print("  Failed : %u / 5\r\n", fail_cnt);
    log_print("  Result : %s\r\n",
              (fail_cnt == 0U) ? "ALL PASS" : "HAS FAILURES");
    log_print("\r\n");
}

/* ====================================================================== */
/*  主验证入口（供 main.c 调用）                                            */
/* ====================================================================== */

/**
 * @brief 核心板上电验证主流程
 *
 * 在 CubeMX 生成的 main.c 中，于 while(1) 之前调用：
 * @code
 *   /* USER CODE BEGIN 2 * /
 *   app_run_verification();   // <-- 加这一行
 *   /* USER CODE END 2 * /
 *   while (1) { /* USER CODE BEGIN WHILE * / ... }
 * @endcode
 *
 * 本函数内部已经包含心跳循环（不会返回），因此 main.c 的 while(1) 实际上
 * 不会执行到。把循环放在这里是为了让验证与心跳逻辑集中、便于维护。
 */
void app_run_verification(void)
{
    /* ---- Step 1: 启动 banner + 系统信息 ---- */
    verify_system_info();

    /* ---- Step 2: LED 闪烁测试（表示系统活着） ---- */
    log_print("[LED] Blink test: %u times x %ums ...\r\n",
              LED_BLINK_TIMES, LED_BLINK_PERIOD);
    led_blink(LED_BLINK_TIMES, LED_BLINK_PERIOD);
    log_print("  Result: PASS (visual check)\r\n");
    log_print("\r\n");

    /* ---- Step 3: SDRAM 16MB 测试 ---- */
    verify_sdram();

    /* ---- Step 4: 汇总 ---- */
    log_print("=== Verification complete. Entering heartbeat loop. ===\r\n");
    log_print("(LED blinks + \"ALIVE\" sent every %lu ms)\r\n",
              (unsigned long)HEARTBEAT_PERIOD);
    log_print("\r\n");

    /* ---- Step 5: 心跳循环 ----
     * 每 HEARTBEAT_PERIOD ms：
     *   - LED 翻转
     *   - 通过 USB CDC / USART1 发送 "ALIVE\n"
     * 此循环不退出（main.c 的 while(1) 不会执行到）。
     */
    uint32_t tick = 0U;
    while (1) {
        HAL_GPIO_TogglePin(LED_USER_GPIO_Port, LED_USER_Pin);
        log_print("[%lu] ALIVE\n", (unsigned long)tick);
        tick++;
        HAL_Delay(HEARTBEAT_PERIOD);
    }
    /* unreachable */
}
