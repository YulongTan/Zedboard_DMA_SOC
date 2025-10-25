Zedboard DMA Demo
====================

Description
-----------

This project demonstrates how to use the Zedboard's Audio Codec and RAM to record samples of audio and play them back. Vivado is used to build the demo's hardware platform, and Xilinx SDK is used to program the bitstream onto the board and to build and deploy a C application.

Community Greeting
------------------

你好！欢迎查阅本项目的资源。此文档主要以英文编写，建议按照下文的步骤逐步体验演示流程，如需更多帮助可访问结尾提供的支持链接。

Troubleshooting when migrating to Vitis 2022
--------------------------------------------

When the software workspace is opened in Vitis 2022 without regenerating the
board support package (BSP), the application build can fail with the error
`fatal error: xil_io.h: No such file or directory`. The application sources do
include `xil_io.h` directly, so the failure is not caused by unused code or
conditional compilation.【F:sdk_appsrc/demo.h†L31-L43】 The header is still present
in the repository under the legacy SDK 2018 layout at
`ps7_cortexa9_0/standalone_domain/bsp/ps7_cortexa9_0/include/xil_io.h`.【F:sdk_appsrc/Zedboard-DMA/ps7_cortexa9_0/standalone_domain/bsp/ps7_cortexa9_0/include/xil_io.h†L1-L41】

However, Vitis 2022 expects a generated aggregation directory named
`bspinclude` inside the BSP. The pre-generated SDK 2018 tree stored with this
repository only contains the older `bsp` directory, so the include path that
Vitis 2022 adds (`standalone_domain/bspinclude/include`) does not actually
exist.【3b3174†L1-L2】 As a result the compiler cannot locate `xil_io.h` until the
platform is re-exported (or the include search path is updated manually) using
Vivado/Vitis 2022 so that the new `bspinclude` folder is created alongside the
updated BSP binaries.

To use this demo, the Zedboard must be connected to a computer over MicroUSB, which must be running a serial terminal. For more information on how to set up and use a serial terminal, such as Tera Term or PuTTY, refer to [this tutorial](https://reference.digilentinc.com/learn/programmable-logic/tutorials/tera-term).

The audio demo records a 5 second sample from microphone(J12) or line in (J13) and plays it back on headphone out(J10) or line out (J12). Recording and playback are controlled by push buttons  from a usb uart serial menu as shown below.

|  Button  | Function             |
| -------- | -------------------- |
|  BTNL    |  play on line out    |
|  BTNU    |  record from mic in  |
|  BTND    |  play on hph out     |
|  BTNR    |  record from line in |


Requirements
------------
* **Zedboard**: To purchase a Zedboard, see the [Digilent Store](https://store.digilentinc.com/zedboard-zynq-7000-arm-fpga-soc-development-board/).
* **Vivado 2018.2 Installation with Xilinx SDK**: To set up Vivado, see the [Installing Vivado and Digilent Board Files Tutorial](https://reference.digilentinc.com/vivado/installing-vivado/start).
* **Serial Terminal Emulator**: 
* **MicroUSB Cable**
* **Audio cables**

Demo Setup
----------

1. Download the most recent release ZIP archive ("Zedboard-DMA-2018.2-*.zip") from the repo's [releases page](https://github.com/Digilent/Zedboard-DMA/releases).
2. Extract the downloaded ZIP.
3. Open the XPR project file, found at \<archive extracted location\>/vivado_proj/Zedboard-DMA.xpr, included in the extracted release archive in Vivado 2018.2.
4. In the toolbar at the top of the Vivado window, select **File -> Export -> Export Hardware**. Select **\<Local to Project\>** as the Exported Location and make sure that the **Include bitstream** box is checked, then click **OK**.
5. In the toolbar at the top of the Vivado window, select **File -> Launch SDK**. Select **\<Local to Project\>** as both the workspace location and exported location, then click **OK**.
6. With Vivado SDK opened, wait for the hardware platform exported by Vivado to be imported.
7. In the toolbar at the top of the SDK window, select **File -> New -> Application Project**.
8. Fill out the fields in the first page of the New Application Project Wizard as in the table below. Most of the listed values will be the wizard's defaults, but are included in the table for completeness.

| Setting                                 | Value                             |
| --------------------------------------- | --------------------------------- |
| Project Name                            | Zedboard-DMA                      |
| Use default location                    | Checked box                       |
| OS Platform                             | standalone                        |
| Target Hardware: Hardware Platform      | design_1_wrapper_hw_platform_0    |
| Target Hardware: Processor              | ps7_cortexa9_0                    |
| Target Software: Language               | C                                 |
| Target Software: Board Support Package  | Create New (Zedboard-DMA_bsp)     |

9. Click **Next**.
10. From the list of template applications, select "Empty Application", then click **Finish**.
11. In the Project Explorer pane to the left of the SDK window, expand the new application project (named "Zedboard-DMA").
12. Right click on the "src" subdirectory of the application project and select **Import**.
13. In the "Select an import wizard" pane of the window that pops up, expand **General** and select **File System**. Then click **Next**.
14. Fill out the fields of the "File system" screen as in the table below. Most of the listed values will be the defaults, but are included in the table for completeness.

| Setting                                                | Value                                      |
| -                                                      | -                                          |
| From directory                                         | \<archive extracted location\>/sdk_appsrc  |
| Files to import pane: sdk_appsrc                       | Checked box                                |
| Into folder                                            | Zedboard-DMA/src                           |
| Options: Overwrite existing resources without warning  | Checked box                                |
| Options: Create top-level folder                       | Unchecked box                              |

15. Click **Finish**.

<Note for maintainers: This project does not require any additional configuration of application or bsp projects. Projects that require any of this configuration should have the steps required to do so described here.>

16. Plug in a test circuit to the Zedboard's analog input pins.
17. Open a serial terminal application (such as TeraTerm FIXME LINK) and connect it to the Zedboard's serial port, using a baud rate of 115200.
18. In the toolbar at the top of the SDK window, select **Xilinx -> Program FPGA**. Leave all fields as their defaults and click "Program".
19. In the Project Explorer pane, right click on the "Zedboard-DMA" application project and select "Run As -> Launch on Hardware (System Debugger)".
20. The application will now be running on the Zedboard. It can be interacted with as described in the first section of this README.

Next Steps
----------
This demo can be used as a basis for other projects by modifying the hardware platform in the Vivado project's block design or by modifying the SDK application project.

Check out the Zedboard's [Resource Center](https://reference.digilentinc.com/reference/programmable-logic/zedboard/start) to find more documentation, demos, and tutorials.

For technical support or questions, please post on the [Digilent Forum](forum.digilentinc.com).

Additional Notes
----------------
For more information on how this project is version controlled, refer to the [digilent-vivado-scripts repo](https://github.com/digilent/digilent-vivado-scripts).