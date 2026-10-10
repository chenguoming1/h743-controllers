# Stock Nexus F7 UART pin-swap verification

Reviewed 2026-10-10. **Supported at source level for all three stock pairs.** Rotorflight automatically detects the reversed native TX/RX assignments and programs the peripheral SWAP bit. These assignments do not require a board or firmware change.

Firmware: `ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94`. Target: `1d9cb4dc6f85c7895c2b089f4b8aa776ca3d3bd3`.

| Peripheral | Logical TX / MCU source | Logical RX / MCU receiver | AF | Derived SWAP |
|---|---|---|---|---|
| USART3 | PB11 / U1.29 / PORT_C_TX_MCU | PB10 / U1.28 / PORT_C_RX_MCU | AF7 | Enabled |
| UART4 | PA1 / U1.15 / PORT_A_TX_MCU | PA0 / U1.14 / PORT_A_RX_MCU | AF8 | Enabled |
| USART6 | PC7 / U1.38 / PORT_B_TX_MCU | PC6 / U1.37 / PORT_B_RX_MCU | AF8 | Enabled |

Directions describe the MCU in ordinary separate-pin UART operation. U1 pad IDs and net names come from the retained schematic pinmap; they were not independently requalified here.

## Operational source chain

1. The [pinned target resources](https://github.com/rotorflight/rotorflight-targets/blob/1d9cb4dc6f85c7895c2b089f4b8aa776ca3d3bd3/configs/RDMS-NEXUS_F7.config#L19-L26) select these six pins. The [STM32F7X2 build](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/target/STM32_UNIFIED/target.h#L109-L124) enables UART3, UART4 and UART6.
2. [Hardware startup](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/fc/init.c#L512-L514) calls uartPinConfigure with the serial pin configuration. [Its detection logic](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/drivers/serial_uart_pinconfig.c#L47-L85) recognizes logical TX on a native RX pin and logical RX on a native TX pin, selects each matching pin/AF descriptor, and sets pinSwap=true.
3. Native tables cover [USART3](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/drivers/serial_uart_stm32f7xx.c#L125-L133), [UART4](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/drivers/serial_uart_stm32f7xx.c#L158-L171) and [USART6](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/drivers/serial_uart_stm32f7xx.c#L236-L242). [GPIO setup](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/drivers/serial_uart_stm32f7xx.c#L358-L379) uses the selected descriptors. [Opening the UART](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/drivers/serial_uart.c#L118-L141) invokes reconfiguration.
4. [Rotorflight's HAL glue](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/drivers/serial_uart_hal.c#L79-L91) selects UART_ADVFEATURE_SWAP_INIT and SWAP_ENABLE, [before normal or half-duplex initialization](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/src/main/drivers/serial_uart_hal.c#L120-L137). [SWAP_ENABLE equals USART_CR2_SWAP](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/lib/main/STM32F7/Drivers/STM32F7xx_HAL_Driver/Inc/stm32f7xx_hal_uart.h#L519-L525).
5. Both [normal initialization](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/lib/main/STM32F7/Drivers/STM32F7xx_HAL_Driver/Src/stm32f7xx_hal_uart.c#L338-L341) and [half-duplex initialization](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/lib/main/STM32F7/Drivers/STM32F7xx_HAL_Driver/Src/stm32f7xx_hal_uart.c#L405-L408) apply advanced features. The [HAL implementation writes CR2.SWAP](https://github.com/rotorflight/rotorflight-firmware/blob/ba6c7e3e328b91a549bf6ca87c9eadd7006b6d94/lib/main/STM32F7/Drivers/STM32F7xx_HAL_Driver/Src/stm32f7xx_hal_uart.c#L2793-L2798).

This establishes an implemented source path beyond resource-name equality. It applies when the pinned target configuration is loaded and the relevant UART is opened; assigning a resource alone does not activate a port or select a protocol.

## Identity and limits

[source-index.json](source-index.json) records nine freshly retrieved pinned sources, exact upstream Git blob IDs and line links, all three pin pairs, and the rechecked local schematic pinmap SHA-256. Firmware evidence was read directly from the pinned repositories. This bundle includes no firmware or vendor source copies and claims no local firmware-snapshot normalization check.

The installed binary, live configuration, peripheral registers and physical UART behavior remain unverified. Bench confirmation on the actual loaded target is still required. No build, simulation, board geometry or electrical qualification was performed. No board or firmware files were modified.
