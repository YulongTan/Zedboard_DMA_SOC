#ifndef KWS_ENGINE_H_
#define KWS_ENGINE_H_

#include <stddef.h>

#include "xil_types.h"
#include "xstatus.h"

#ifdef __cplusplus
extern "C" {
#endif

/* FatFs 默认把第一块 SD 卡挂载为 "0:"，因此若权重位于根目录需保留该前缀。
 * 如需调整目录结构，可修改此处的默认路径。
 */
#define KWS_SD_MOUNT_POINT      "0:/"
#define KWS_DEFAULT_WEIGHT_PATH "0:/bnn_weights_binary_new.bin"

#define KWS_SOURCE_SAMPLE_RATE   16000U
#define KWS_SOURCE_CHANNELS      1U
#define KWS_TARGET_SAMPLE_RATE   16000U
#define KWS_INPUT_ROWS           40U
#define KWS_INPUT_COLS           98U
#define KWS_INPUT_DEPTH          1U
#define KWS_CONV1_OUT_CH         32U
#define KWS_CONV2_OUT_CH         64U
#define KWS_CONV3_OUT_CH         64U
#define KWS_CONV4_OUT_CH         64U
#define KWS_FC_IN_UNITS          64U

#define KWS_GAP_ROWS             1U
#define KWS_GAP_COLS             1U

XStatus KwsEngine_Initialize(const char *weight_file_path);
void    KwsEngine_Shutdown(void);
int     KwsEngine_IsReady(void);
XStatus KwsEngine_MountSd(void);
XStatus KwsEngine_ProcessRecording(const int32_t *source_buffer,
                                   size_t frames_per_channel,
                                   u32 *out_class_index,
                                   float *out_confidence);
const float *KwsEngine_GetLogits(u32 *num_classes);

#ifdef __cplusplus
}
#endif

#endif /* KWS_ENGINE_H_ */
