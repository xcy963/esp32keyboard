# ESP32-S3 USB HID 网关：USB 描述符自定义说明


## 重要说明

本工程支持自定义 USB 设备描述符中的：

- VID
- PID
- Manufacturer 字符串
- Product 字符串
- Serial Number 字符串


## Windows 上会显示成什么？

烧录后插入 Windows，普通设备管理器列表通常会看到：

- HID Keyboard Device
- HID-compliant mouse
- HID-compliant device

在“属性 -> 详细信息 -> 硬件 ID”里会看到 VID/PID；在部分工具里也可能看到 Manufacturer/Product 字符串。

## 在哪里修改？

- 板子reset的时候都会重新连接wifi,然后在串口打印对应的ip

## 串口日志监听（自定义 monitor）

- 脚本：`tools/usb_monitor.py`
- 依赖安装：`pip install pyserial`
- 默认监听：`/dev/ttyUSB0`，波特率 `115200`

示例：

```bash
python3 tools/usb_monitor.py
python3 tools/usb_monitor.py -p /dev/ttyUSB0 -b 115200
python3 tools/usb_monitor.py -p /dev/ttyUSB0 --no-timestamp
```

按下板子 `RESET` 后，可以看到类似：

- `Connecting to WiFi...`
- `WiFi connected. IP: 192.168.x.x`
- `TCP HID gateway listening on port 5000`

## Flask 网页测试 HID

新增脚本：`tools/web_hid_tester.py`

安装依赖：

```bash
pip install flask
```

启动（允许手机访问）：

```bash
python3 tools/web_hid_tester.py --host 0.0.0.0 --port 8080
```

然后在手机浏览器访问：

```text
http://你的PC局域网IP:8080
```

页面里填入 ESP32 的 IP（例如 `192.168.43.113`）和端口（默认 `5000`），点击按钮即可发送键盘/鼠标测试指令。

## Flask 网页测试 HID

新增脚本：`tools/web_hid_tester.py`

安装依赖：

```bash
pip install flask
```

启动（允许手机访问）：

```bash
python3 tools/web_hid_tester.py --host 0.0.0.0 --port 8080
```

然后在手机浏览器访问：

```text
http://你的PC局域网IP:8080
```

页面里填入 ESP32 的 IP（例如 `192.168.43.113`）和端口（默认 `5000`），点击按钮即可发送键盘/鼠标测试指令。
