# Zedboard DMA 音频演示程序解析

本文面向希望快速理解 `sdk_appsrc/Zedboard_DMA` 目录中演示程序的开发者，结合源码说明整体结构、关键数据结构以及各模块之间的调用关系。与随附的《demo_line_by_line_zh.md》互补：本篇关注系统层级视角，后者提供逐句对照。 【F:sdk_appsrc/Zedboard_DMA/demo_line_by_line_zh.md†L1-L55】

## 工程结构概览

演示程序围绕 `demo.c` 的主循环展开，并通过下列功能模块实现音频的采集与回放：

- `audio/`：封装 ADAU1761 编解码器的寄存器配置、DMA 传输和输入输出路径切换。 【F:sdk_appsrc/Zedboard_DMA/src/audio/audio.c†L621-L783】
- `dma/`：提供 AXI DMA 初始化和中断处理函数，负责驱动 DDR 与 I²S 之间的数据搬运。 【F:sdk_appsrc/Zedboard_DMA/src/dma/dma.c†L25-L173】
- `intc/`：负责可移植的中断控制器初始化与向量表安装。 【F:sdk_appsrc/Zedboard_DMA/src/intc/intc.c†L25-L176】
- `iic/`：初始化 I²C 控制器并异步读取板载 EEPROM 中的 MAC 地址。 【F:sdk_appsrc/Zedboard_DMA/src/iic/iic.c†L76-L193】
- `userio/`：管理按键、开关与 LED 的 GPIO 中断，转换为演示逻辑可消费的事件。 【F:sdk_appsrc/Zedboard_DMA/src/userio/userio.c†L64-L206】

主程序在 `demo.c` 中包含上述模块的头文件，并保有它们所需的设备实例。`ivt[]` 中断向量表将不同外设的中断函数统一注册，确保初始化顺序与中断启用一致。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L33-L161】

## 核心状态结构 `sDemo_t`

`sDemo_t` 集中记录演示过程中使用的标志位和状态字段。下表列出每个成员的含义与产生者： 【F:sdk_appsrc/Zedboard_DMA/src/demo.h†L94-L116】

| 字段 | 作用 | 典型写入位置 |
| --- | --- | --- |
| `u8Verbose` | 控制串口输出冗余度，当前作为保留位。 | `main()` 初始化。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L168-L176】 |
| `fUserIOEvent` | 指示是否存在新的按键事件。 | `fnUserIOIsr`。 【F:sdk_appsrc/Zedboard_DMA/src/userio/userio.c†L146-L190】 |
| `fAudioRecord` | 录音任务进行中。 | `main()` 在收到 `'u'`/`'r'` 后置 1，DMA 完成后清零。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L294-L368】 |
| `fAudioPlayback` | 回放任务进行中。 | `main()` 在 `'d'`/`'l'` 按键后置 1，DMA 完成后清零。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L316-L373】 |
| `fDmaError` | DMA ISR 发现错误。 | `fnS2MMInterruptHandler`/`fnMM2SInterruptHandler`。 【F:sdk_appsrc/Zedboard_DMA/src/dma/dma.c†L63-L113】 |
| `fDmaS2MMEvent` / `fDmaMM2SEvent` | 录音/播放 DMA 完成。 | DMA 中断服务。 【F:sdk_appsrc/Zedboard_DMA/src/dma/dma.c†L51-L99】 |
| `chBtn` | 最近一次按键编码。 | `fnUserIOIsr`。 【F:sdk_appsrc/Zedboard_DMA/src/userio/userio.c†L146-L190】 |
| 其余链路相关字段 | 预留给视频/网络 demo，共享同一结构体以便扩展。 | 在本示例中保持默认值。 |

## `main` 函数执行流程

`main()` 负责平台初始化、打印控制提示，并在无限循环中根据状态标志驱动业务逻辑：

1. 初始化顺序：中断控制器、I²C、用户 IO、DMA、音频 I²S，若任一步骤失败则提前返回。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L182-L212】
2. 注册中断：通过 `fnEnableInterrupts` 将向量表中的 I²C、DMA 和 GPIO 中断处理函数逐一连接到控制器。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L216-L218】
3. 主循环：
   - 监视 DMA 完成或错误标志，必要时关闭 I²S 控制寄存器并清除状态。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L241-L288】
   - 处理用户 IO 事件，根据按键选择录音或播放路径（麦克风/线路输入、耳机/线路输出），并调用音频模块发起 DMA 传输。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L289-L377】

## 音频数据流与任务时序

1. **录音（S2MM）路径**
   - 用户按下 `BTNU` 或 `BTNR`，GPIO 中断将 `Demo.chBtn` 设置为 `'u'` / `'r'` 并置 `fUserIOEvent`。 【F:sdk_appsrc/Zedboard_DMA/src/userio/userio.c†L146-L190】
   - 主循环检测到事件后，调用 `fnSetMicInput` 或 `fnSetLineInput` 切换 ADAU1761 输入路由，再调用 `fnAudioRecord`。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L294-L359】
   - `fnAudioRecord` 复位 S2MM 通道、配置 `XAxiDma_SimpleTransfer`，并打开 I²S 接收与流控寄存器。 【F:sdk_appsrc/Zedboard_DMA/src/audio/audio.c†L621-L653】
   - 录音完成时 DMA 中断设置 `fDmaS2MMEvent`，主循环据此停掉 I²S 输出并清除录音标志。 【F:sdk_appsrc/Zedboard_DMA/src/dma/dma.c†L51-L84】【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L243-L260】

2. **播放（MM2S）路径**
   - 用户按下 `BTND` 或 `BTNL`，GPIO ISR 将 `Demo.chBtn` 设置为 `'d'` / `'l'`。 【F:sdk_appsrc/Zedboard_DMA/src/userio/userio.c†L146-L190】
   - 主循环调用 `fnSetHpOutput` 或 `fnSetLineOutput` 选择输出路由，然后触发 `fnAudioPlay`。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L316-L373】
   - `fnAudioPlay` 配置 MM2S 传输长度，打开 I²S 发送方向并启动流控。 【F:sdk_appsrc/Zedboard_DMA/src/audio/audio.c†L663-L694】
   - DMA 完成后设置 `fDmaMM2SEvent`，主循环关闭流控并清除播放标志。 【F:sdk_appsrc/Zedboard_DMA/src/dma/dma.c†L85-L114】【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L262-L276】

3. **错误恢复**
    - 如 DMA ISR 发现错误，会复位通道并置位 `fDmaError`。主循环收到后停止所有音频路径，等待重新触发。 【F:sdk_appsrc/Zedboard_DMA/src/dma/dma.c†L63-L113】【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L278-L288】

## 中断协同细节

- `intc/intc.c` 根据 `ivt[]` 中的描述逐一调用 `XScuGic_Connect`（或 `XIntc_Connect`) 并在最后开启全局中断。这样可确保所有外设在主循环运行前已经注册好回调。 【F:sdk_appsrc/Zedboard_DMA/src/intc/intc.c†L56-L176】
- `iic/iic.c` 在初始化时设置 I²C 时钟、允许重复启动，并提供异步读取 MAC 地址的接口，虽然音频演示未直接使用 MAC 结果，但该模块负责对 ADAU1761 的寄存器读写。 【F:sdk_appsrc/Zedboard_DMA/src/iic/iic.c†L76-L193】
- `userio/userio.c` 把四个方向键转换为 `'u'`/`'d'`/`'r'`/`'l'` 字符，并在 ISR 中更新 LED 状态，从而在调试时直观显示当前按键。 【F:sdk_appsrc/Zedboard_DMA/src/userio/userio.c†L136-L206】

## 移植提示

- **包含路径**：若 BSP 迁移到新版 Vitis，确保 `.cproject` 或 CMake 中包含新的 BSP 头文件目录，避免出现找不到 `xil_io.h` 等错误。 【F:sdk_appsrc/Zedboard_DMA/.cproject†L47-L110】
- **缓存控制**：代码中提供了 `Xil_DCacheFlushRange` / `Xil_DCacheInvalidateRange` 的注释示例，在启用数据缓存的系统上需根据实际情况打开，以免录音/播放出现陈旧数据。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L255-L266】
- **中断优先级**：在多任务环境下，可根据需要调整 GIC 优先级或在 ISR 中缩短处理时间，确保音频 DMA 不被其他外设打断。

## 总结

演示程序通过 `sDemo_t` 共享状态连接主循环与各外设中断，利用 AXI DMA 和 ADAU1761 的协同实现音频数据从 I²S 到 DDR、再回放到 I²S 的完整链路。GPIO 中断将按键事件转化为高层命令，I²C 保证编解码器与 EEPROM 访问正常，中断控制器则为所有外设提供统一的分发机制。阅读本文并结合逐句解析，可帮助快速理解在 Zedboard 上构建 DMA 音频链路所需的硬件抽象层调用顺序与关键注意事项。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L28-L388】
