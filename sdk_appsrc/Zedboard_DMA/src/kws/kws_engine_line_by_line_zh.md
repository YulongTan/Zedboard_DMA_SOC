# `kws_engine.c` 按行解析

> 行号基于当前仓库版本，便于与源码交叉参考。

## 头文件与宏常量（L1-L53）
- L1 引入自身头文件 `kws_engine.h`，导出 API 与常量定义。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L1】
- L3-L11 包含 Vitis 控制台 `xil_printf`、FatFs `ff.h` 以及 `math.h`、`float.h` 等标准库，用于文件系统访问和数学运算。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L3-L11】
- L13-L37 设定魔数、采样率、FFT、Mel 频带等常量，直接对应 Python 训练脚本中的参数：窗长 400、步长 160、Mel 滤波器数量 40、帧数 98 等，保证推理端与训练端一致。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L13-L37】
- L39-L47 根据输入尺寸推导三次池化后的空间尺寸以及全局平均池化的目标大小（5×5），为后续 scratch 缓冲区的空间分配提供尺寸参考。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L39-L47】

## 权重 / Scratch 结构体（L49-L110）
- L49-L55 `KwsWeightHeader` 描述 SD 卡权重文件的头部，含魔数、版本与类别数。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L49-L55】
- L57-L79 `KwsModel` 保存全部权重指针（卷积核、BN 参数、全连接层权重与偏置），初始化时逐段分配内存并填充。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L57-L79】
- L81-L103 `KwsScratch` 是推理阶段的工作空间，包括输入张量、单声道缓冲、FFT 功率谱、各层输出等，避免重复分配。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L81-L103】
- L105-L109 `KwsFeatureTables` 缓存 Hann 窗、余弦/正弦表以及 Mel 滤波器矩阵，只在第一次初始化时计算一次。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L105-L109】

## 全局状态与前向声明（L111-L147）
- L111-L117 定义 FatFs 全局对象、模型/缓存句柄和状态标志，`gEngineReady` 标识权重和 scratch 是否就绪，`gHasResult` 说明是否已有最新推理结果。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L111-L117】
- L119-L147 列出所有内部静态函数，包括权重加载、特征提取、卷积/池化/Dense 前向等，便于在文件后方逐一实现。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L119-L147】

## 初始化 / 关闭接口（L149-L193）
- `KwsEngine_Initialize`（L149-L189）按顺序挂载 SD 卡、读取权重、分配 scratch、初始化特征表；失败时依次释放已分配资源并返回 `XST_FAILURE`。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L149-L189】
- 成功后设置 `gEngineReady=1`、`gHasResult=0` 并打印类别数量，供外部确认。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L181-L189】
- `KwsEngine_Shutdown`（L191-L197）清除状态并释放所有权重/缓存，适合在程序退出或需要重新加载新模型时调用。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L191-L197】
- `KwsEngine_IsReady`（L199-L203）简单返回 `gEngineReady`，供主循环判断是否可以进入推理阶段。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L199-L203】

## 处理录音与取回结果（L205-L246）
- `KwsEngine_ProcessRecording`（L205-L246）是对外的主推理函数：
  - L209-L224 进行参数合法性检查（引擎是否 ready、缓冲指针是否为空、帧数是否满足 decimation 后的 1 秒长度）。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L205-L224】
  - L226-L229 调用 `extract_logmel` 把立体声采样转换为 40×98 的对数 Mel 频谱；若失败打印提示。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L226-L229】
  - L231 调用 `run_network` 执行卷积/全连接推理，输出 logits 向量。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L231】
  - L233-L241 遍历 logits 找到最大值与类别索引。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L233-L241】
  - L243-L245 用 `expf(logit - max_logit)` 计算 Softmax 分母，并把 `1/sum` 作为“置信度”输出；同时置位 `gHasResult` 并回写给调用者。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L243-L245】
- `KwsEngine_GetLogits`（L248-L256）在最新结果可用时返回 logits 指针，并可选写出类别数量，用于调试或上层进一步处理。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L248-L256】

## 资源管理与文件系统（L258-L353）
- `free_model`（L258-L275）和 `free_scratch`（L277-L295）逐项释放权重和工作区内存，并把全局结构清零，防止悬挂指针。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L258-L295】
- `mount_sd_if_needed`（L297-L311）利用 FatFs 的 `f_mount` 一次性挂载 SD 卡，重复调用会直接返回成功，失败时打印错误码。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L297-L311】
- `read_exact`（L313-L323）封装 `f_read`，确保读满指定字节数，否则返回内部错误，方便权重加载函数使用。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L313-L323】
- `load_weights`（L325-L399）完成权重文件解析：
  - L327-L347 打开文件并校验头部魔数/版本/类别数，若异常立即返回。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L325-L347】
  - L349-L375 依据网络结构计算每层参数数量，逐段 `malloc`/`calloc` 对应数组，并检查分配是否成功。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L349-L375】
  - L377-L397 用 `read_exact` 依次读入卷积、BN、全连接权重与偏置；任一读操作失败都会在关闭文件后返回错误。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L377-L399】

## Scratch 分配与特征表（L401-L466）
- `allocate_scratch`（L401-L434）根据各层输出尺寸分配工作缓冲，包括单声道数据、FFT 功率谱、三次卷积/池化结果、全连接输入/输出等；任一指针为空即视为失败。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L401-L434】
- `init_feature_tables`（L436-L466）只执行一次：
  - L440-L443 构造 Hann 窗系数。
  - L445-L449 预先计算每个 FFT bin 与窗样本的余弦/正弦值，供后续手写 FFT 使用。
  - L451-L465 依据 Mel 公式建立滤波器组，先换算 Mel 标尺，再生成三角滤波权重矩阵。
  - 最后把 `initialized` 标志设为 1，避免重复计算。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L436-L466】

## 特征提取（L468-L526）
- `extract_logmel` 分三步：
  - L472-L482 通过 `KWS_DECIMATION_FACTOR` 做平均抽取，把 96 kHz 立体声压缩为 16 kHz 单声道，并归一化到 `[-1,1]` 浮点值。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L468-L482】
  - L484-L497 对每个时间帧手动计算 DFT：乘 Hann 窗后与预先缓存的 sin/cos 累乘求出功率谱 `fft_power`。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L484-L497】
  - L499-L506 将功率谱与 Mel 滤波器做点积，避免对数域出现 `log(0)`，最后写入 `out_tensor[mel, frame]`。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L499-L506】

## 推理算子实现（L508-L597）
- `conv2d_forward`（L508-L544）实现 3×3 SAME 卷积并叠加 BN 偏移，根据 `KwsActivation` 选择 ReLU 或二值 Sign 激活，输出维度与输入空间尺寸一致。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L508-L544】
- `maxpool2d`（L546-L569）执行 2×2、步长 2 的最大池化，遍历输入窗口取最大值，输出尺寸由宏 `POOL_OUT_DIM` 推导。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L546-L569】
- `adaptive_avg_pool`（L571-L595）按输出网格平均汇聚，使用 `floorf/ceilf` 计算输入窗口范围并求均值，实现与 PyTorch `AdaptiveAvgPool2d(5,5)` 相同的行为。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L571-L595】
- `dense_forward`（L597-L613）完成全连接矩阵乘并施加 BN/激活；内部使用 `double` 累加降低量化误差，然后根据激活类型选择 ReLU、Sign 或线性输出。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L597-L613】

## 整体前向流程（L615-L652）
- `run_network` 串联上述算子：
  - L617-L632：Conv1 + ReLU + MaxPool，特征图从 1×40×98 提升到 32×20×49。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L615-L632】
  - L634-L648：二值卷积层 conv2/conv3 与 Sign 激活之间穿插 MaxPool，把通道数扩展到 128 并逐步减小空间尺寸。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L634-L648】
  - L650-L654：`adaptive_avg_pool` 压缩为 5×5，并 `memcpy` 到展平缓冲。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L650-L655】
  - L656-L665：`dense_forward` 生成 256 维隐藏向量，施加 Sign 激活后输入最终全连接层，加上偏置得到 logits。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L656-L665】
- 输出的 `logits` 与 Python 侧模型一致，可直接做 Softmax/Top-1 判断。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L656-L665】

---
通过以上逐段解析，可以把 KWS 推理流程与原先 Python 训练代码建立一一对应关系，方便调试、优化或移植到其他平台。
