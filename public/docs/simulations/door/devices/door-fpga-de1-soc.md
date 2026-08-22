Door DE1-SoC I/O mappings
=========================

All signals are active high. GPIO numbers refer to the LabsLand virtual GPIO
bus; in VHDL, for example, GPIO 28 is `V_GPIO(28)`.

| Runtime signal | Meaning | Type | GPIO |
|---|---|---|---|
| `doorOpened` | Door is at the fully open limit | FPGA input | GPIO 28 (`V_GPIO(28)`) |
| `doorClosed` | Door is at the fully closed limit | FPGA input | GPIO 29 (`V_GPIO(29)`) |
| `personSensor` | A person is waiting at the door | FPGA input | GPIO 30 (`V_GPIO(30)`) |
| `open` | Drive the door toward the open limit | FPGA output | GPIO 26 (`V_GPIO(26)`) |
| `close` | Drive the door toward the closed limit | FPGA output | GPIO 27 (`V_GPIO(27)`) |

Do not assert `open` and `close` at the same time. Deassert `open` when
`doorOpened` becomes high, and deassert `close` when `doorClosed` becomes
high.
