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

打开：

```text
src/main.cpp
```

找到：

```cpp
static constexpr uint16_t USB_VID = 0x303A;
static constexpr uint16_t USB_PID = 0x4008;

static const char* USB_MANUFACTURER = "Generic";
static const char* USB_PRODUCT      = "USB Input Device";
static const char* USB_SERIAL       = "HID-GATEWAY-001";
```

你可以改成自己的合法信息，例如：

```cpp
static constexpr uint16_t USB_VID = 0x303A;
static constexpr uint16_t USB_PID = 0x4008;

static const char* USB_MANUFACTURER = "My Keyboard Lab";
static const char* USB_PRODUCT      = "USB Keyboard Touchpad";
static const char* USB_SERIAL       = "DEV-0001";
```

## 为什么不能直接写 Logitech？

Logitech 的 VID/PID 和品牌名属于第三方。冒用它们可能带来商标、合规和安全审计问题。本工程保留了完整的自定义接口，但默认使用通用名称。

## 如果函数编译报错怎么办？

如果出现类似：

```text
class USB_ has no member named VID
```

请升级 PlatformIO 的 espressif32 平台，或者使用较新的 Arduino-ESP32 core。推荐先在 PlatformIO 中执行：

```bash
pio pkg update
```

必要时在 `platformio.ini` 里指定较新的 espressif32 平台版本。
