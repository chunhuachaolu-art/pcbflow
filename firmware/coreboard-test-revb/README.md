# STM32H743 Coreboard Rev-B bring-up firmware

## Status

This directory intentionally contains no generated firmware yet. It is the reserved location for the complete, versioned STM32CubeMX Rev-B project after U2 and the FMC pin map have been verified.

Do not copy the current `firmware/coreboard-test` SDRAM parameters into this project. That directory names a different x32 SDRAM part and 16 MiB geometry, while the copied Rev-B hardware baseline has an unresolved U2 identity/package/pin-map gate.

## Entry criteria for generated code

Before committing an `.ioc` or generated CubeMX files here, close the U2 closure package in `../../design/coreboard/reports/revb-decision-record.md` and record:

1. Exact SDRAM part, package, pin map, capacity and timing.
2. FMC bus width, row/column configuration, refresh count and target clock.
3. Pin-multiplexing audit, including the historical PG2/FMC_A12 conflict.
4. USB FS VBUS sensing disposition for PA9/USART1 coexistence.
5. MPU/D-cache policy for SDRAM shared with DMA or LTDC.

## Required first validation sequence

1. SWD, HSE, UART and LED.
2. USB FS enumeration; explicitly enable HSI48 if it is the selected USB clock source.
3. SDRAM initialization followed by a 16-bit direct-access test, then aligned 32-bit AHB access.
4. SDRAM frequency sweep at 50 MHz, 75 MHz and 100 MHz; run retention and soak tests.
5. Validate MPU/D-cache behavior before allocating any DMA or LTDC buffers in SDRAM.

Any SDRAM self-test failure must enter an observable `BOARD_FAIL` state and stop normal application progress.
