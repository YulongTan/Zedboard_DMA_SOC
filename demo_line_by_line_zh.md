# `demo.c` 主流程逐句解析

本文紧跟 `sdk_appsrc/Zedboard_DMA/src/demo.c` 的实际行号，对每个语句块给出功能说明，帮助在调试或迁移时快速定位关键逻辑。

## L28-L67：公共头文件
- `#include "demo.h"`：引入演示所需的公共常量、结构体以及全局状态声明。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L28-L31】
- `#include "./audio/audio.h"` 至 `#include "./iic/iic.h"`：导入音频编解码、AXI DMA、按键 GPIO 与 I²C 驱动接口，使主程序可直接调用各模块的初始化与业务函数。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L33-L38】
- `#include "xaxidma.h"`、`#include "xparameters.h"`、`#include "xil_exception.h"` 等：包含 Xilinx 提供的硬件抽象层头文件，保证能访问底层驱动 API 与寄存器定义。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L42-L59】
- 条件包含部分根据平台区分 MicroBlaze+XIntc 和 Cortex-A9+GIC，确保能使用正确的中断控制器与延时函数实现。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L61-L70】

## L74-L112：常量与全局对象
- 录音/播放时间、采样率与总样本数常量为 DMA 缓冲配置提供参数。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L78-L94】
- `static XIic sIic;`、`static XAxiDma sAxiDma;`、`static XGpio sUserIO;`：在文件作用域内保留各外设驱动实例，避免在函数间频繁传参。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L114-L122】
- `volatile sDemo_t Demo = {0};`：定义演示状态单例，标志位在主循环与中断服务例程间共享。`volatile` 确保状态随中断更新即时可见。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L124-L124】
- `static INTC sIntc;` 结合条件编译确保中断控制器对象符合目标平台类型。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L126-L133】
- `const ivt_t ivt[]` 初始化中断向量表：每项记录一个中断源 ID、对应处理函数及上下文指针。稍后统一注册，实现集中式配置。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L137-L161】

## L164-L224：`main` 函数入口与初始化
- `int Status;`：保存每步初始化返回值，便于统一错误处理。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L168-L170】
- `Demo.u8Verbose = 1;`：打开详细打印开关（当前仅预留扩展）。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L172-L172】
- 串口打印启动信息，方便区分运行阶段。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L176-L176】
- 依次调用 `fnInitInterruptController`、`fnInitIic`、`fnInitUserIO`、`fnConfigDma`、`fnInitAudio`；任意步骤失败即打印错误并返回 `XST_FAILURE`，确保未正确配置的外设不会继续执行。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L182-L212】
- `fnEnableInterrupts(&sIntc, &ivt[0], sizeof(ivt)/sizeof(ivt[0]))`：在所有驱动初始化完成后，一次性启用 I²C、DMA、GPIO 的中断处理函数。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L216-L218】
- 打印控制说明，明确四个按键对应的录音/播放通路。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L223-L230】

## L234-L288：DMA 事件轮询
- 主循环 `while(1)` 维持演示常驻。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L234-L236】
- `if (Demo.fDmaS2MMEvent)`：检测录音（Stream-to-Memory）通道完成标志，提示“Recording Done…”，关闭 I²S 流控并清除录音状态。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L243-L260】
- `if (Demo.fDmaMM2SEvent)`：检测播放（Memory-to-Stream）完成标志，提示“Playback Done…”，同样关闭流控并复位播放状态。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L262-L276】
- `if (Demo.fDmaError)`：如 DMA 中断报告错误，输出提示并清零录音/播放标志，等待用户重新触发。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L278-L288】

## L290-L377：按键事件调度
- `if (Demo.fUserIOEvent)`：仅在 GPIO ISR 设置事件标志时进入处理逻辑。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L290-L292】
- `switch (Demo.chBtn)`：根据最近一次按键字符决定动作：
  - `'u'`：若空闲则切换麦克风输入、调用 `fnAudioRecord` 启动录音，否则提示仍在忙。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L294-L315】
  - `'d'`：空闲时切换到耳机输出、调用 `fnAudioPlay` 回放缓存。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L316-L337】
  - `'r'`：选择线路输入后开始录音。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L338-L359】
  - `'l'`：选择线路输出后播放。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L360-L373】
  - 默认分支忽略未知值。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L374-L375】
- 成功发起任务时设置 `Demo.fAudioRecord` 或 `Demo.fAudioPlayback`，防止并发触发；忙碌时维持当前状态。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L300-L368】
- 每次处理完事件后清除 `Demo.chBtn` 与 `Demo.fUserIOEvent`，以便下一次中断更新。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L377-L380】

## L382-L388：保留的退出路径
- `xil_printf("--- Exiting main() ---")` 和 `return XST_SUCCESS;` 理论上不会执行，但保留以便未来在需要时安全退出主循环。 【F:sdk_appsrc/Zedboard_DMA/src/demo.c†L382-L388】

通过上述逐句解析，可在阅读源码时快速将串口输出、DMA 中断与按键事件关联到具体语句位置，降低排查和移植的时间成本。
