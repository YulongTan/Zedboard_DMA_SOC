# `kws_engine.c` 按行解析

> 行号基于当前仓库版本（v3 权重格式）。

## 头文件与常量（L1-L58）
- L1-L10 引入引擎头文件、`xil_printf` 日志、FatFs、`math.h` 以及标准库，支撑 SD 读写与三角/对数运算。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L1-L10】
- L12-L33 定义权重文件魔数、版本枚举及 FFT / Mel 频谱尺寸。`KWS_DECIMATION_FACTOR` 由源、目标采样率比值得到，可支持 96 kHz→16 kHz 等场景。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L12-L33】

## 权重布局与缓存结构（L35-L96）
- `KwsWeightHeader`（L35-L40）描述二进制文件头；`KwsWeightLayout`（L42-L47）附带四个卷积层的输出通道数，为 v3 新增字段。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L35-L47】
- `KwsModel`（L49-L60）保存类别数、每层通道信息及权重指针。注意当前网络只存卷积与最终全连接的权重，不再折叠 BatchNorm。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L49-L60】
- `KwsScratch`（L62-L74）缓存对数 Mel 输入、单声道缓冲、FFT 功率谱以及四个卷积阶段、中间 GAP、logits。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L62-L74】
- `KwsFeatureTables`（L82-L88）在首次初始化时生成 Hann 窗、sin/cos 表和 Mel 滤波器，后续调用直接复用。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L82-L88】

## 全局状态与函数声明（L90-L132）
- L90-L97 维护 FatFs、模型、工作区与状态位 `gEngineReady`、`gHasResult`。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L90-L97】
- L98-L132 列出内部静态函数，包括权重加载、Scratch 分配、特征提取、卷积/池化/全连接算子等，为后续实现做好声明。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L98-L132】

## 对外 API（L134-L247）
- `KwsEngine_Initialize`（L134-L165）挂载 SD、加载权重、分配工作区并构建特征表，任何失败都会清理资源后返回 `XST_FAILURE`。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L134-L165】
- `KwsEngine_Shutdown` 与 `KwsEngine_IsReady`（L167-L178）负责复位状态、释放内存和查询引擎状态。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L167-L178】
- `KwsEngine_MountSd`（L180-L183）提供显式挂载入口，方便在 Demo 初始化阶段提前检查 SD 状态。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L180-L183】
- `KwsEngine_ProcessRecording`（L185-L236）校验缓冲区长度，调用 `extract_logmel` 生成 40×98 输入，再通过 `run_network` 得到 logits，使用 Softmax 的“max trick”计算置信度。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L185-L236】
- `KwsEngine_GetLogits`（L238-L247）在最近一次推理成功后返回 logits 指针及类别数，便于上层记录详细分数。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L238-L247】

## 资源管理与文件操作（L249-L411）
- `free_model` / `free_scratch`（L249-L271）逐项释放模型权重与工作区，避免悬挂指针。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L249-L271】
- `mount_sd_if_needed`（L273-L287）在首次调用时执行 `f_mount`，并缓存挂载状态供后续复用。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L273-L287】
- `read_exact`（L289-L300）封装 `f_read`，确保一次性读取指定字节，若读取量不足则返回 `FR_INT_ERR`。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L289-L300】
- `load_weights`（L302-L411）解析 v3 权重文件：
  1. 校验魔数/版本/类别数；
  2. 读取 `KwsWeightLayout` 并更新每层通道数；
  3. 根据通道配置分配卷积/FC 权重缓冲；
  4. 顺序读入 `conv1`→`conv4`→`fc` 权重，任一失败都会打印错误并返回 `XST_FAILURE`。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L302-L411】

## Scratch 分配与特征表（L413-L522）
- `conv_out_dim`（L413-L420）根据卷积核/步长/填充推导输出空间尺寸，是多个函数的共享工具。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L413-L420】
- `allocate_scratch`（L422-L452）计算四个卷积阶段的空间尺寸，分配输入张量、FFT、卷积输出、GAP、logits 等缓存。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L422-L452】
- `init_feature_tables`（L454-L522）仅在首次初始化时执行：生成 Hann 窗、每个频点的 sin/cos 表，以及 40 组 Mel 滤波器三角窗。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L454-L522】

## 特征提取（L524-L585）
- `extract_logmel` 先将多声道数据按 `KWS_DECIMATION_FACTOR` 下采样为 1 秒单声道波形，再逐帧做 Hann 窗 FFT 和 Mel 滤波，最后写入对数能量矩阵。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L524-L585】

## 基础算子实现（L587-L702）
- `activate_scalar` 与 `apply_activation` 实现 Sign/ReLU 激活；`conv2d_forward`、`adaptive_avg_pool`、`dense_forward` 分别对应 3×3 卷积、
  自适应平均池化和全连接矩阵乘。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L587-L702】

## 前向推理流程（L704-L788）
- `run_network` 按顺序执行四层 3×3 卷积（带 Sign 激活、部分层额外加 1.0f 偏移）、最终 Sign、1×1 自适应平均池化和线性分类头，输出 logits 供 Softmax 使用。【F:sdk_appsrc/Zedboard_DMA/src/kws/kws_engine.c†L704-L788】

通过以上拆解，可将 SD 权重加载、Mel 特征提取与 BNN 前向逻辑逐一对应，便于在移植或调试时快速定位问题。 
