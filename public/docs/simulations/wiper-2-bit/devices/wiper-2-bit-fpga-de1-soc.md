Wiper (two-bit) DE1-SoC I/O mappings
====================================

All signals are active high. GPIO numbers refer to the LabsLand virtual GPIO
bus; in VHDL, for example, GPIO 28 is `V_GPIO(28)`.

| Runtime signal | Meaning in the current simulation | Type | GPIO |
|---|---|---|---|
| `rainSensor` | Rain is active | FPGA input | GPIO 28 (`V_GPIO(28)`) |
| `rightSensor` | Wiper is at the **left-hand** limit | FPGA input | GPIO 29 (`V_GPIO(29)`) |
| `leftSensor` | Wiper is at the **right-hand** limit | FPGA input | GPIO 30 (`V_GPIO(30)`) |
| `mButton` | The interface's M button is being pressed | FPGA input | GPIO 23 (`V_GPIO(23)`) |
| `pButton` | The interface's P button is being pressed | FPGA input | GPIO 24 (`V_GPIO(24)`) |
| `move1` | First movement-control signal | FPGA output | GPIO 26 (`V_GPIO(26)`) |
| `move2` | Second movement-control signal | FPGA output | GPIO 27 (`V_GPIO(27)`) |

The command pair is written in `(move1, move2)` order:

| `move1` / GPIO 26 | `move2` / GPIO 27 | Result |
|---|---|---|
| 0 | 0 | Stop |
| 0 | 1 | Move toward the right-hand limit |
| 1 | 0 | Move toward the left-hand limit |
| 1 | 1 | Error state |

The current two-bit simulation publishes the endpoint channels with their
runtime names reversed: `rightSensor` reports the physical left-hand limit and
`leftSensor` reports the physical right-hand limit. This is different from the
one-bit Wiper. Use the endpoint meanings in the table above when implementing a
controller. Between the endpoints, both endpoint sensors can be low.
