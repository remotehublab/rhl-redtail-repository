Door STM32 Nucleo WB55RG I/O mappings
=====================================

All signals are active high. The direction shown is relative to the STM32.

| Runtime signal | Meaning | Type | GPIO | STM32 HAL name |
|---|---|---|---|---|
| `doorOpened` | Door is at the fully open limit | STM32 input | PC_13 | `GPIOC`, `GPIO_PIN_13` |
| `doorClosed` | Door is at the fully closed limit | STM32 input | PA_6 | `GPIOA`, `GPIO_PIN_6` |
| `personSensor` | A person is waiting at the door | STM32 input | PB_9 | `GPIOB`, `GPIO_PIN_9` |
| `open` | Drive the door toward the open limit | STM32 output | PC_4 | `GPIOC`, `GPIO_PIN_4` |
| `close` | Drive the door toward the closed limit | STM32 output | PD_0 | `GPIOD`, `GPIO_PIN_0` |

Do not assert `open` and `close` at the same time. Deassert `open` when
`doorOpened` becomes high, and deassert `close` when `doorClosed` becomes
high.
