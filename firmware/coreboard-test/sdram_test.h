/**
 * @file    sdram_test.h
 * @brief   STM32H743 核心板 IS42S32800G SDRAM 自测模块接口
 *
 * @details
 *   目标硬件：STM32H743 (LQFP176) 核心板
 *   SDRAM   ：IS42S32800G-6BLI，16MB，32-bit 数据宽度，100MHz
 *             通过 FMC Bank5/6 映射到 0xC0000000 起始的地址空间。
 *
 *   本模块假设 FMC + SDRAM 控制器已在系统初始化阶段（main.c，由 CubeMX 生成）
 *   完成配置并已使能。FMC 把 SDRAM 映射为一段普通内存，因此测试代码只需通过
 *   普通 32 位指针读写即可，不依赖任何特定的 HAL SDRAM 接口函数。
 *
 *   模块设计原则：
 *     - 测试函数内部不做任何 printf/UART 输出，结果通过返回值与 err 结构体传出，
 *       由调用者决定如何呈现（保持模块独立、可复用）。
 *     - 通过 volatile 指针访问 SDRAM，避免编译器把读写优化掉。
 *     - 发现首个错误即记录并立即返回 FAIL，以节省扫描时间。
 *
 * @note    兼容 Keil MDK 与 STM32CubeIDE，仅使用标准 C（C99）。
 */

#ifndef SDRAM_TEST_H
#define SDRAM_TEST_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>

/* ===================================================================== */
/*                          SDRAM 存储区参数                              */
/* ===================================================================== */

/** FMC Bank5 起始地址（SDRAM 映射基地址） */
#define SDRAM_BASE_ADDR   ((uint32_t)0xC0000000U)

/** SDRAM 总容量：16MB（IS42S32800G-6BLI） */
#define SDRAM_SIZE        (16U * 1024U * 1024U)

/** SDRAM 按 32-bit 字计的总字数 */
#define SDRAM_WORDS       (SDRAM_SIZE / 4U)

/* ===================================================================== */
/*                            结果与错误类型                              */
/* ===================================================================== */

/** 测试结果：通过 / 失败 */
typedef enum {
    SDRAM_TEST_PASS = 0,   /**< 测试通过 */
    SDRAM_TEST_FAIL = 1    /**< 测试失败（至少发现一处错误） */
} sdram_test_result_t;

/**
 * @brief  SDRAM 测试错误信息结构体
 *
 * 用于记录一次测试中首个发现的错误细节，以及整体统计。
 * 当测试函数的 err 形参为 NULL 时，这些字段不会被填写。
 */
typedef struct {
    uint32_t fail_addr;    /**< 出错地址的“字索引”偏移（0 ~ SDRAM_WORDS-1） */
    uint32_t expected;     /**< 期望读到的值 */
    uint32_t actual;       /**< 实际读到的值 */
    uint32_t error_count;  /**< 本次测试累计发现 / run_all 累计失败的测试项数 */
    uint32_t duration_ms;  /**< 本次测试耗时（ms） */
} sdram_test_error_t;

/* ===================================================================== */
/*                            单项测试接口                                */
/* ===================================================================== */

/**
 * @brief   测试1：固定模式测试（0xAA55AA55）
 * @details 向整个 SDRAM 写入固定模式 0xAA55AA55，再逐字读回校验。
 *          最基本的测试，能快速发现严重焊接缺陷、数据线整体开/短路、
 *          时钟未生效、SDRAM 未正确初始化等灾难性问题。
 *
 * @param   err  输出错误信息，可为 NULL
 * @return  SDRAM_TEST_PASS / SDRAM_TEST_FAIL
 */
sdram_test_result_t sdram_test_fixed_pattern(sdram_test_error_t *err);

/**
 * @brief   测试2：地址线测试（写入地址索引值）
 * @details 向第 i 个 32-bit 字写入值 i（addr[0]=0, addr[1]=1, ...），读回校验。
 *          若某根地址线开路/短路/粘连，会导致寻址错位：写入的位置与读回的位置
 *          不一致，表现为读到的值与索引不符。可定位地址线级故障。
 *
 * @param   err  输出错误信息，可为 NULL
 * @return  SDRAM_TEST_PASS / SDRAM_TEST_FAIL
 */
sdram_test_result_t sdram_test_address_bus(sdram_test_error_t *err);

/**
 * @brief   测试3：反模式测试（相邻字交替 0x55AA55AA / 0xAA55AA55）
 * @details 相邻字写入互补的交替模式，读回校验。对数据线串扰、
 *          相邻存储单元短路、I/O 翻转速率问题敏感。
 *
 * @param   err  输出错误信息，可为 NULL
 * @return  SDRAM_TEST_PASS / SDRAM_TEST_FAIL
 */
sdram_test_result_t sdram_test_checkerboard(sdram_test_error_t *err);

/**
 * @brief   测试4：走步测试（Marching / March Test）
 * @details 经典 March 类算法：正向遍历写“全1”并读校验，再反向遍历写“全0”并读校验。
 *          覆盖性最强，对固定型故障（stuck-at）、状态耦合故障（coupling fault）、
 *          相邻单元相互干扰均有较高检出率。
 *
 * @param   err  输出错误信息，可为 NULL
 * @return  SDRAM_TEST_PASS / SDRAM_TEST_FAIL
 */
sdram_test_result_t sdram_test_marching(sdram_test_error_t *err);

/**
 * @brief   测试5：随机数据测试（LFSR 伪随机序列）
 * @details 使用 32-bit LFSR 生成一段确定的伪随机序列写入整片 SDRAM，
 *          再以相同种子重放序列读出校验。数据图样不规律，对时序敏感的
 *          间歇性故障、特定数据依赖失效较为有效。
 *
 * @param   err  输出错误信息，可为 NULL
 * @return  SDRAM_TEST_PASS / SDRAM_TEST_FAIL
 */
sdram_test_result_t sdram_test_random(sdram_test_error_t *err);

/* ===================================================================== */
/*                            汇总测试接口                                */
/* ===================================================================== */

/**
 * @brief   依次执行全部 5 项 SDRAM 测试
 * @details 按 1->5 的顺序执行各项测试。任意一项失败即立即停止后续测试，
 *          并把该项错误信息写入 *err（若 err 非 NULL），error_count 记录到
 *          失败时为止已完成的测试编号。
 *
 * @param   err  输出错误信息，可为 NULL
 * @return  SDRAM_TEST_PASS（全部通过）/ SDRAM_TEST_FAIL（某项失败）
 */
sdram_test_result_t sdram_test_run_all(sdram_test_error_t *err);

#ifdef __cplusplus
}
#endif

#endif /* SDRAM_TEST_H */
