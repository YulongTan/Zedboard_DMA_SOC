# 
# Usage: To re-create this platform project launch xsct with below options.
# xsct D:\Vitis\USERS\10_Zedboard_audio_in\Zedboard-DMA-2018.2-1\sdk_appsrc\Zedboard-DMA\platform.tcl
# 
# OR launch xsct and run below command.
# source D:\Vitis\USERS\10_Zedboard_audio_in\Zedboard-DMA-2018.2-1\sdk_appsrc\Zedboard-DMA\platform.tcl
# 
# To create the platform in a different location, modify the -out option of "platform create" command.
# -out option specifies the output directory of the platform project.

platform create -name {Zedboard-DMA}\
-hw {D:\Vitis\USERS\10_Zedboard_audio_in\Zedboard-DMA-2018.2-1\hw\design_1_wrapper.xsa}\
-proc {ps7_cortexa9_0} -os {standalone} -out {D:/Vitis/USERS/10_Zedboard_audio_in/Zedboard-DMA-2018.2-1/sdk_appsrc}

platform write
platform generate -domains 
platform active {Zedboard-DMA}
platform generate
