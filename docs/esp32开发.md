# 简单学习以下这个开发板

## 板子上的按钮和usb口
- 1. rst,相当于断电再上电,会使得我的程序从头开始跑
- 2. boot,控制GPIO0引脚,控制是否进入下载模式(按下就会进入下载模式)

- 3. usb对应的typec口:连上就是我设置的usb设备
- 4. com口: 对应烧录代码

```txt

/dev/ttyUSB0
------------
Hardware ID: USB VID:PID=0403:6001 SER=A5069RR4 LOCATION=1-2
Description: FT232R USB UART - FT232R USB UART

/dev/ttyACM0
------------
Hardware ID: USB VID:PID=303A:1001 SER=E072A1D35AF0 LOCATION=1-3:1.1
Description: Espressif ESP32-S3-DevKitC-1-N8 (8 MB QD, No PSRAM) - TinyUSB CDC
```
- /dev/ttyUSB0（VID:PID 0403:6001）
  - 来自板载 FT232 USB-UART 芯片，是调试通道,上面写着COM,这个是烧代码的地方
  - 

- /dev/ttyACM0,
  - 对应USB口


## esp32的运行逻辑
- 首先有一个引导,引导之后取跑我的setup函数里面对应的代码
  - 之后调用loop函数一直循环运行
- 指令集似乎是risc-v!
- 他有自己的操作系统!arduio对应的是freeRTOS,运行之后会创建主任务执行setup,其他模块创建对应的线程维护
- 可以创建线程(他叫他任务,我认为是linux fork的简单实现)

## 烧录相关的

- 两个USB都插上的时候他有时候会自动选择USB口去烧代码,然后就会失败...
```txt
Archiving .pio/build/esp32-s3-devkitc-1/libFrameworkArduino.a
Indexing .pio/build/esp32-s3-devkitc-1/libFrameworkArduino.a
Linking .pio/build/esp32-s3-devkitc-1/firmware.elf
Retrieving maximum program size .pio/build/esp32-s3-devkitc-1/firmware.elf
Checking size .pio/build/esp32-s3-devkitc-1/firmware.elf
Advanced Memory Usage is available via "PlatformIO Home > Project Inspect"
RAM:   [==        ]  17.4% (used 57128 bytes from 327680 bytes)
Flash: [==        ]  22.3% (used 745785 bytes from 3342336 bytes)
Building .pio/build/esp32-s3-devkitc-1/firmware.bin
esptool.py v4.11.0
Creating esp32s3 image...
Merged 2 ELF sections
Successfully created esp32s3 image.
Configuring upload protocol...
AVAILABLE: cmsis-dap, esp-bridge, esp-builtin, esp-prog, espota, esptool, iot-bus-jtag, jlink, minimodule, olimex-arm-usb-ocd, olimex-arm-usb-ocd-h, olimex-arm-usb-tiny-h, olimex-jtag-tiny, tumpa
CURRENT: upload_protocol = esptool
Looking for upload port...

Warning! Please install `99-platformio-udev.rules`. 
More details: https://docs.platformio.org/en/latest/core/installation/udev-rules.html

Auto-detected: /dev/ttyACM0
Uploading .pio/build/esp32-s3-devkitc-1/firmware.bin
esptool.py v4.11.0
Serial port /dev/ttyACM0
Connecting......................................

A fatal error occurred: Failed to connect to ESP32-S3: No serial data received.
For troubleshooting steps visit: https://docs.espressif.com/projects/esptool/en/latest/troubleshooting.html
*** [upload] Error 2
=========================================================== [FAILED] Took 13.76 seconds ===========================================================
make: *** [Makefile:13：upload] 错误 1
hitcrt@hitcrt-OMEN:~/0cheating/esp_keyboard$ 
```
- 解决方式是制定使用COM口,不知道那个是COM口的话就先看一下devices
```bash
/dev/ttyUSB0
------------
Hardware ID: USB VID:PID=0403:6001 SER=A5069RR4 LOCATION=1-2
Description: FT232R USB UART - FT232R USB UART

/dev/ttyACM0
------------
Hardware ID: USB VID:PID=303A:1001 SER=E0:72:A1:D3:5A:F0 LOCATION=1-3:1.0
Description: USB JTAG/serial debug unit
```
- 看到`FT232R`就是烧录代码的部分,这个似乎是主控的芯片名字?
