Wiper (one-bit) STM32 Nucleo WB55RG I/O mappings
===============================================

All signals are active high. The direction shown is relative to the STM32.

| Runtime signal | Meaning | Type | GPIO | STM32 HAL name |
|---|---|---|---|---|
| `rainSensor` | Rain is active | STM32 input | PC_13 | `GPIOC`, `GPIO_PIN_13` |
| `rightSensor` | Wiper is at the right-hand limit (minimum angle) | STM32 input | PA_6 | `GPIOA`, `GPIO_PIN_6` |
| `leftSensor` | Wiper is at the left-hand limit (maximum angle) | STM32 input | PB_9 | `GPIOB`, `GPIO_PIN_9` |
| `mButton` | The interface's M button is being pressed | STM32 input | PB_8 | `GPIOB`, `GPIO_PIN_8` |
| `pButton` | The interface's P button is being pressed | STM32 input | PC_12 | `GPIOC`, `GPIO_PIN_12` |
| `move` | Enable wiper movement | STM32 output | PC_4 | `GPIOC`, `GPIO_PIN_4` |

When `move` is high, the simulation moves the wiper and reverses its direction
automatically at each endpoint. When `move` is low, it stops at its current
position. Between the endpoints, both endpoint sensors can be low. The
simulation's error control deliberately makes both endpoint sensors high so
that controller error handling can be tested.
