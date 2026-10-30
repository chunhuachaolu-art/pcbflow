/**
 * @file    sdram_test.c
 * @brief   STM32H743 核心板 IS42S32800G SDRAM 自测模块实现
 *
 * @details
 *   实现 5 类内存测试 + 1 个汇总函数。所有 SDRAM 访问都通过指向
 *   SDRAM_BASE_ADDR 的 volatile uint32_t* 指针完成，确保编译器不会把
 *   对实际外设内存的读写优化掉。
 *
 *   每个测试函数的约定：
 *     - 入口：若 err != NULL，先把 err 清零，再记录起始 tick。
 *     - 出口：把本次耗时写入 err->duration_ms（若 err != NULL）。
 *     - 发现首个错误：填好 fail_addr/expected/actual，error_count 累计，
 *       立即返回 SDRAM_TEST_FAIL（不再继续扫描，省时间）。
 *     - 全部通过：err->error_count = 0，返回 SDRAM_TEST_PASS。
 *
 *   注意：HAL_GetTick() 由 CMSIS / HAL 提供，返回毫秒计数值。
 *   若不使用 HAL，调用者可在本文件顶部把 HAL_GetTick() 宏替换成自己的时基。
 */

#include "sdram_test.h"

/*
 * 若工程未使用 STM32 HAL，请在此处提供等价的毫秒级时基实现，
 * 例如 #define HAL_GetTick()  my_sys_ticks()。
 * 默认假定工程里已包含 stm32h7xx_hal.h（在 main.c 中 include），
 * 因此 HAL_GetTick() 可用。这里不直接 include HAL 头文件，以保持
 * 本模块与具体 HAL 版本解耦。
 */
extern uint32_t HAL_GetTick(void);

/* ===================================================================== */
/*                          内部辅助宏与函数                              */
/* ===================================================================== */

/** 获取指向 SDRAM 第 i 个 32-bit 字的 volatile 指针 */
#define SDRAM_WORD_PTR(i)   ((volatile uint32_t *)(SDRAM_BASE_ADDR + ((uint32_t)(i)) * 4U))

/**
 * @brief  记录一处错误并返回失败
 * @note   仅在 err != NULL 时填写字段，调用者据此提前返回。
 *         宏内部不 return，由调用方紧跟 return SDRAM_TEST_FAIL;。
 */
#define SDRAM_RECORD_FAIL(err_ptr, addr_idx, exp_val, act_val)              \
    do {                                                                    \
        if ((err_ptr) != (sdram_test_error_t *)0) {                         \
            (err_ptr)->fail_addr  = (uint32_t)(addr_idx);                   \
            (err_ptr)->expected   = (uint32_t)(exp_val);                    \
            (err_ptr)->actual     = (uint32_t)(act_val);                    \
            (err_ptr)->error_count++;                                       \
        }                                                                   \
    } while (0)

/**
 * @brief  32-bit Galois 线性反馈移位寄存器（LFSR）伪随机数推进
 *
 * 采用多项式 x^32 + x^22 + x^2 + x^1 + 1 的 Galois 实现。
 * 特点：
 *   - 完全确定：相同种子产生相同序列，因此写入与校验用相同种子重放即可。
 *   - 周期 2^32 - 1，对 16MB（4M 字）的 SDRAM 远超所需。
 *   - 仅用移位与异或，无库依赖，可移植。
 *
 * @param  state  指向当前 LFSR 状态（不可为 0；0 会停留在 0）
 * @return        推进后的新 32-bit 伪随机值
 */
static uint32_t sdram_lfsr_next(uint32_t *state)
{
    uint32_t s    = *state;
    uint32_t lsb  = s & 1U;        /* 必须在右移前取出最低位 */

    /* taps: 32, 22, 2, 1 -> 多项式 x^32 + x^22 + x^2 + x^1 + 1 */
    s >>= 1U;
    if (lsb != 0U) {
        s ^= 0x80200003U;          /* Galois 反馈掩码 */
    }

    *state = s;
    return s;
}

/**
 * @brief  统一的 err 初始化 + 起始 tick 记录
 */
static uint32_t sdram_test_begin(sdram_test_error_t *err)
{
    if (err != (sdram_test_error_t *)0) {
        err->fail_addr   = 0U;
        err->expected    = 0U;
        err->actual      = 0U;
        err->error_count = 0U;
        err->duration_ms = 0U;
    }
    return HAL_GetTick();
}

/**
 * @brief  统一的耗时记录（tick 溢出也按 32 位回绕差值计算，约 49 天内正确）
 */
static void sdram_test_end(sdram_test_error_t *err, uint32_t start_tick)
{
    uint32_t elapsed = HAL_GetTick() - start_tick;
    if (err != (sdram_test_error_t *)0) {
        err->duration_ms = elapsed;
    }
}

/* ===================================================================== */
/*                              测试 1                                   */
/*                  固定模式测试（0xAA55AA55 / 0x55AA55AA）               */
/* ===================================================================== */

sdram_test_result_t sdram_test_fixed_pattern(sdram_test_error_t *err)
{
    volatile uint32_t *p;
    uint32_t i;
    uint32_t start;
    const uint32_t pattern = 0xAA55AA55U;

    start = sdram_test_begin(err);

    /* 阶段一：全片写入固定模式 0xAA55AA55 */
    p = SDRAM_WORD_PTR(0);
    for (i = 0U; i < SDRAM_WORDS; ++i) {
        p[i] = pattern;
    }

    /* 阶段二：逐字读回校验 */
    p = SDRAM_WORD_PTR(0);
    for (i = 0U; i < SDRAM_WORDS; ++i) {
        if (p[i] != pattern) {
            SDRAM_RECORD_FAIL(err, i, pattern, p[i]);
            sdram_test_end(err, start);
            return SDRAM_TEST_FAIL;
        }
    }

    sdram_test_end(err, start);
    return SDRAM_TEST_PASS;
}

/* ===================================================================== */
/*                              测试 2                                   */
/*                  地址线测试（每字写入其地址索引值）                    */
/* ===================================================================== */

sdram_test_result_t sdram_test_address_bus(sdram_test_error_t *err)
{
    volatile uint32_t *p;
    uint32_t i;
    uint32_t start;

    start = sdram_test_begin(err);

    /* 阶段一：addr[i] = i */
    p = SDRAM_WORD_PTR(0);
    for (i = 0U; i < SDRAM_WORDS; ++i) {
        p[i] = i;
    }

    /* 阶段二：读回比对，应为索引本身。
     * 若某根地址线粘连/开路，物理寻址错位，读回值会不等于索引。 */
    p = SDRAM_WORD_PTR(0);
    for (i = 0U; i < SDRAM_WORDS; ++i) {
        if (p[i] != i) {
            SDRAM_RECORD_FAIL(err, i, i, p[i]);
            sdram_test_end(err, start);
            return SDRAM_TEST_FAIL;
        }
    }

    sdram_test_end(err, start);
    return SDRAM_TEST_PASS;
}

/* ===================================================================== */
/*                              测试 3                                   */
/*          反模式测试（相邻字交替 0x55AA55AA / 0xAA55AA55）              */
/* ===================================================================== */

sdram_test_result_t sdram_test_checkerboard(sdram_test_error_t *err)
{
    volatile uint32_t *p;
    uint32_t i;
    uint32_t start;
    const uint32_t pat_a = 0x55AA55AAU;
    const uint32_t pat_b = 0xAA55AA55U;

    start = sdram_test_begin(err);

    /* 阶段一：写入交替棋盘格模式 */
    p = SDRAM_WORD_PTR(0);
    for (i = 0U; i < SDRAM_WORDS; ++i) {
        p[i] = ((i & 1U) == 0U) ? pat_a : pat_b;
    }

    /* 阶段二：读回校验。
     * 对数据线串扰、相邻单元短路、I/O 大幅翻转下的保持失效敏感。 */
    p = SDRAM_WORD_PTR(0);
    for (i = 0U; i < SDRAM_WORDS; ++i) {
        uint32_t expect = ((i & 1U) == 0U) ? pat_a : pat_b;
        if (p[i] != expect) {
            SDRAM_RECORD_FAIL(err, i, expect, p[i]);
            sdram_test_end(err, start);
            return SDRAM_TEST_FAIL;
        }
    }

    sdram_test_end(err, start);
    return SDRAM_TEST_PASS;
}

/* ===================================================================== */
/*                              测试 4                                   */
/*                      走步测试（Marching / March）                     */
/* ===================================================================== */

sdram_test_result_t sdram_test_marching(sdram_test_error_t *err)
{
    volatile uint32_t *p;
    uint32_t i;
    uint32_t start;

    start = sdram_test_begin(err);

    /*
     * 采用简化的 March 测试（March-like）：
     *   1) 正向：写全 1
     *   2) 正向：读应为 1，若错即记
     *   3) 反向：读应为 1，写 0（每读一个就翻转）
     *   4) 反向：读应为 0，若错即记
     * 该序列对 stuck-at、状态耦合、相邻干扰均有较好覆盖。
     */

    /* (1) 正向写全 1 */
    p = SDRAM_WORD_PTR(0);
    for (i = 0U; i < SDRAM_WORDS; ++i) {
        p[i] = 0xFFFFFFFFU;
    }

    /* (2) 正向读校验 1 */
    p = SDRAM_WORD_PTR(0);
    for (i = 0U; i < SDRAM_WORDS; ++i) {
        if (p[i] != 0xFFFFFFFFU) {
            SDRAM_RECORD_FAIL(err, i, 0xFFFFFFFFU, p[i]);
            sdram_test_end(err, start);
            return SDRAM_TEST_FAIL;
        }
    }

    /* (3) 反向读 1 并写 0 */
    p = SDRAM_WORD_PTR(0);
    /* i 为无符号，使用 i > 0 配合末尾处理 i == 0 的字 */
    i = SDRAM_WORDS;
    while (i > 0U) {
        --i;
        if (p[i] != 0xFFFFFFFFU) {
            SDRAM_RECORD_FAIL(err, i, 0xFFFFFFFFU, p[i]);
            sdram_test_end(err, start);
            return SDRAM_TEST_FAIL;
        }
        p[i] = 0x00000000U;
    }

    /* (4) 反向再读校验 0 */
    p = SDRAM_WORD_PTR(0);
    i = SDRAM_WORDS;
    while (i > 0U) {
        --i;
        if (p[i] != 0x00000000U) {
            SDRAM_RECORD_FAIL(err, i, 0x00000000U, p[i]);
            sdram_test_end(err, start);
            return SDRAM_TEST_FAIL;
        }
    }

    sdram_test_end(err, start);
    return SDRAM_TEST_PASS;
}

/* ===================================================================== */
/*                              测试 5                                   */
/*                  随机数据测试（LFSR 伪随机序列）                       */
/* ===================================================================== */

sdram_test_result_t sdram_test_random(sdram_test_error_t *err)
{
    volatile uint32_t *p;
    uint32_t i;
    uint32_t start;
    uint32_t seed;
    const uint32_t LFSR_SEED = 0x12345678U;   /* 固定种子，保证可重现 */

    start = sdram_test_begin(err);

    /* 阶段一：用 LFSR 序列写入整片 SDRAM */
    seed = LFSR_SEED;
    p = SDRAM_WORD_PTR(0);
    for (i = 0U; i < SDRAM_WORDS; ++i) {
        uint32_t v = sdram_lfsr_next(&seed);
        p[i] = v;
    }

    /* 阶段二：用相同种子重放序列，逐字比对 */
    seed = LFSR_SEED;
    p = SDRAM_WORD_PTR(0);
    for (i = 0U; i < SDRAM_WORDS; ++i) {
        uint32_t expect = sdram_lfsr_next(&seed);
        if (p[i] != expect) {
            SDRAM_RECORD_FAIL(err, i, expect, p[i]);
            sdram_test_end(err, start);
            return SDRAM_TEST_FAIL;
        }
    }

    sdram_test_end(err, start);
    return SDRAM_TEST_PASS;
}

/* ===================================================================== */
/*                          汇总：依次执行 5 项测试                       */
/* ===================================================================== */

sdram_test_result_t sdram_test_run_all(sdram_test_error_t *err)
{
    sdram_test_result_t res;
    uint32_t start;

    /* 初始化：error_count 用于累计已执行的测试编号（失败时即为失败项编号） */
    start = HAL_GetTick();
    if (err != (sdram_test_error_t *)0) {
        err->fail_addr   = 0U;
        err->expected    = 0U;
        err->actual      = 0U;
        err->error_count = 0U;
        err->duration_ms = 0U;
    }

    /* 测试 1：固定模式 */
    if (err != (sdram_test_error_t *)0) { err->error_count = 1U; }
    res = sdram_test_fixed_pattern(err);
    if (res != SDRAM_TEST_PASS) {
        if (err != (sdram_test_error_t *)0) {
            err->duration_ms = HAL_GetTick() - start;
        }
        return SDRAM_TEST_FAIL;
    }

    /* 测试 2：地址线 */
    if (err != (sdram_test_error_t *)0) { err->error_count = 2U; }
    res = sdram_test_address_bus(err);
    if (res != SDRAM_TEST_PASS) {
        if (err != (sdram_test_error_t *)0) {
            err->duration_ms = HAL_GetTick() - start;
        }
        return SDRAM_TEST_FAIL;
    }

    /* 测试 3：反模式 */
    if (err != (sdram_test_error_t *)0) { err->error_count = 3U; }
    res = sdram_test_checkerboard(err);
    if (res != SDRAM_TEST_PASS) {
        if (err != (sdram_test_error_t *)0) {
            err->duration_ms = HAL_GetTick() - start;
        }
        return SDRAM_TEST_FAIL;
    }

    /* 测试 4：走步 */
    if (err != (sdram_test_error_t *)0) { err->error_count = 4U; }
    res = sdram_test_marching(err);
    if (res != SDRAM_TEST_PASS) {
        if (err != (sdram_test_error_t *)0) {
            err->duration_ms = HAL_GetTick() - start;
        }
        return SDRAM_TEST_FAIL;
    }

    /* 测试 5：随机 */
    if (err != (sdram_test_error_t *)0) { err->error_count = 5U; }
    res = sdram_test_random(err);
    if (res != SDRAM_TEST_PASS) {
        if (err != (sdram_test_error_t *)0) {
            err->duration_ms = HAL_GetTick() - start;
        }
        return SDRAM_TEST_FAIL;
    }

    /* 全部通过：error_count 归 0，记录总耗时 */
    if (err != (sdram_test_error_t *)0) {
        err->error_count = 0U;
        err->duration_ms = HAL_GetTick() - start;
    }
    return SDRAM_TEST_PASS;
}
