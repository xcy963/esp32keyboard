#include <Arduino.h>
#include <WiFi.h>
#include "USB.h"
#include "USBHID.h"

// ============================================================
// User configuration
// ============================================================

const char* WIFI_SSID = "HITSZ2";
const char* WIFI_PASS = "123456789";

const uint16_t TCP_PORT = 5000;

// Optional: disconnect inactive client and release all keys/buttons.
const uint32_t CLIENT_TIMEOUT_MS = 3000;

// ============================================================
// USB device identity configuration
// ============================================================
// 说明：
// 1. 不要在产品/公开环境中冒用 Logitech、Apple、Microsoft 等公司的 VID/PID 或商标。
// 2. 下面默认使用 Espressif 的开发 VID/PID，配合自定义字符串，Windows 设备管理器
//    通常会显示为通用 HID 键盘/鼠标，而不是在普通列表中直接显示 ESP32。
// 3. 如果你有自己合法申请/授权的 VID/PID，把 USB_VID 和 USB_PID 改成你的值即可。
// 4. 如果你的 Arduino-ESP32 版本不支持 USB.VID()/USB.PID()/USB.manufacturerName()
//    这些函数，请升级 espressif32 平台和 Arduino-ESP32 core。

static constexpr uint16_t APP_USB_VID = 0x303A;  // Espressif 开发 VID；请替换为你合法拥有/授权的 VID
static constexpr uint16_t APP_USB_PID = 0x4008;  // 示例 PID；请替换为你合法拥有/授权的 PID

static const char* APP_USB_MANUFACTURER = "Generic";
static const char* APP_USB_PRODUCT      = "USB Input Device";
static const char* APP_USB_SERIAL       = "HID-GATEWAY-001";

// ============================================================
// TCP protocol
// ============================================================

static constexpr uint8_t MAGIC_1 = 0xA5;
static constexpr uint8_t MAGIC_2 = 0x5A;

static constexpr uint8_t TYPE_KEYBOARD    = 0x01;
static constexpr uint8_t TYPE_TOUCHPAD    = 0x02;
static constexpr uint8_t TYPE_PING        = 0x03;
static constexpr uint8_t TYPE_RELEASE_ALL = 0x04;

// Frame format:
//   A5 5A TYPE LENGTH PAYLOAD... XOR
// XOR is calculated over A5 5A TYPE LENGTH PAYLOAD.

// Keyboard payload, 8 bytes, standard boot keyboard report:
//   byte0: modifier bits
//   byte1: reserved
//   byte2-byte7: up to 6 HID keycodes
//
// Touchpad payload, 6 bytes:
//   byte0: buttons, bit0 left, bit1 right, bit2 middle
//   byte1: x low
//   byte2: x high
//   byte3: y low
//   byte4: y high
//   byte5: contact, 0 released, 1 touched
// Coordinates are 0..32767.

// ============================================================
// USB HID
// ============================================================

USBHID HID;

// Composite HID descriptor:
//   Report ID 1: keyboard
//   Report ID 2: absolute-position mouse/touchpad
static const uint8_t hidReportDescriptor[] = {
  // ---------- Keyboard ----------
  0x05, 0x01,        // Usage Page Generic Desktop
  0x09, 0x06,        // Usage Keyboard
  0xA1, 0x01,        // Collection Application
  0x85, 0x01,        //   Report ID 1

  0x05, 0x07,        //   Usage Page Keyboard
  0x19, 0xE0,        //   Usage Minimum Left Control
  0x29, 0xE7,        //   Usage Maximum Right GUI
  0x15, 0x00,        //   Logical Minimum 0
  0x25, 0x01,        //   Logical Maximum 1
  0x75, 0x01,        //   Report Size 1
  0x95, 0x08,        //   Report Count 8
  0x81, 0x02,        //   Input Data,Var,Abs modifier

  0x95, 0x01,        //   Report Count 1
  0x75, 0x08,        //   Report Size 8
  0x81, 0x03,        //   Input Const reserved

  0x95, 0x06,        //   Report Count 6
  0x75, 0x08,        //   Report Size 8
  0x15, 0x00,        //   Logical Minimum 0
  0x25, 0x65,        //   Logical Maximum 101
  0x05, 0x07,        //   Usage Page Keyboard
  0x19, 0x00,        //   Usage Minimum 0
  0x29, 0x65,        //   Usage Maximum 101
  0x81, 0x00,        //   Input Data,Array

  0xC0,              // End Collection

  // ---------- Absolute Mouse / Touchpad ----------
  0x05, 0x01,        // Usage Page Generic Desktop
  0x09, 0x02,        // Usage Mouse
  0xA1, 0x01,        // Collection Application
  0x85, 0x02,        //   Report ID 2
  0x09, 0x01,        //   Usage Pointer
  0xA1, 0x00,        //   Collection Physical

  0x05, 0x09,        //     Usage Page Button
  0x19, 0x01,        //     Usage Minimum Button 1
  0x29, 0x03,        //     Usage Maximum Button 3
  0x15, 0x00,        //     Logical Minimum 0
  0x25, 0x01,        //     Logical Maximum 1
  0x95, 0x03,        //     Report Count 3
  0x75, 0x01,        //     Report Size 1
  0x81, 0x02,        //     Input Data,Var,Abs

  0x95, 0x01,        //     Report Count 1
  0x75, 0x05,        //     Report Size 5
  0x81, 0x03,        //     Input Const padding

  0x05, 0x01,        //     Usage Page Generic Desktop
  0x09, 0x30,        //     Usage X
  0x09, 0x31,        //     Usage Y
  0x16, 0x00, 0x00,  //     Logical Minimum 0
  0x26, 0xFF, 0x7F,  //     Logical Maximum 32767
  0x75, 0x10,        //     Report Size 16
  0x95, 0x02,        //     Report Count 2
  0x81, 0x02,        //     Input Data,Var,Abs

  0xC0,              //   End Collection
  0xC0               // End Collection
};

class CompositeHIDDevice : public USBHIDDevice {
public:
  CompositeHIDDevice() {
    HID.addDevice(this, sizeof(hidReportDescriptor));
  }

  uint16_t _onGetDescriptor(uint8_t* buffer) override {
    memcpy(buffer, hidReportDescriptor, sizeof(hidReportDescriptor));
    return sizeof(hidReportDescriptor);
  }
};

CompositeHIDDevice compositeHIDDevice;

struct __attribute__((packed)) KeyboardReport {
  uint8_t modifiers;
  uint8_t reserved;
  uint8_t keys[6];
};

struct __attribute__((packed)) TouchpadReport {
  uint8_t buttons;
  uint16_t x;
  uint16_t y;
};

// ============================================================
// TCP server and parser
// ============================================================

WiFiServer server(TCP_PORT);
WiFiClient client;
uint32_t lastClientByteMs = 0;

enum RxState {
  WAIT_MAGIC1,
  WAIT_MAGIC2,
  WAIT_TYPE,
  WAIT_LENGTH,
  WAIT_PAYLOAD,
  WAIT_CHECKSUM
};

RxState rxState = WAIT_MAGIC1;
uint8_t rxType = 0;
uint8_t rxLength = 0;
uint8_t rxPayload[255];
uint8_t rxIndex = 0;
uint8_t rxXor = 0;

void releaseAll() {
  KeyboardReport keyboard = {};
  TouchpadReport touchpad = {};
  HID.SendReport(1, &keyboard, sizeof(keyboard));
  HID.SendReport(2, &touchpad, sizeof(touchpad));
}

void sendKeyboardReport(const uint8_t* payload, uint8_t len) {
  if (len != 8) return;

  KeyboardReport report = {};
  report.modifiers = payload[0];
  report.reserved = payload[1];
  memcpy(report.keys, payload + 2, 6);

  HID.SendReport(1, &report, sizeof(report));
}

void sendTouchpadReport(const uint8_t* payload, uint8_t len) {
  if (len != 6) return;

  TouchpadReport report = {};
  report.buttons = payload[0] & 0x07;
  report.x = static_cast<uint16_t>(payload[1]) | (static_cast<uint16_t>(payload[2]) << 8);
  report.y = static_cast<uint16_t>(payload[3]) | (static_cast<uint16_t>(payload[4]) << 8);

  const bool contact = payload[5] != 0;
  if (!contact) {
    report.buttons = 0;
  }

  if (report.x > 32767) report.x = 32767;
  if (report.y > 32767) report.y = 32767;

  HID.SendReport(2, &report, sizeof(report));
}

void sendPong() {
  if (!client || !client.connected()) return;

  uint8_t data[5];
  data[0] = MAGIC_1;
  data[1] = MAGIC_2;
  data[2] = TYPE_PING;
  data[3] = 0;
  data[4] = data[0] ^ data[1] ^ data[2] ^ data[3];
  client.write(data, sizeof(data));
}

void handleFrame(uint8_t type, const uint8_t* payload, uint8_t len) {
  switch (type) {
    case TYPE_KEYBOARD:
      sendKeyboardReport(payload, len);
      break;

    case TYPE_TOUCHPAD:
      sendTouchpadReport(payload, len);
      break;

    case TYPE_PING:
      sendPong();
      break;

    case TYPE_RELEASE_ALL:
      releaseAll();
      break;

    default:
      break;
  }
}

void resetParser() {
  rxState = WAIT_MAGIC1;
  rxType = 0;
  rxLength = 0;
  rxIndex = 0;
  rxXor = 0;
}

void parseByte(uint8_t b) {
  switch (rxState) {
    case WAIT_MAGIC1:
      if (b == MAGIC_1) {
        rxXor = b;
        rxState = WAIT_MAGIC2;
      }
      break;

    case WAIT_MAGIC2:
      if (b == MAGIC_2) {
        rxXor ^= b;
        rxState = WAIT_TYPE;
      } else if (b == MAGIC_1) {
        rxXor = b;
        rxState = WAIT_MAGIC2;
      } else {
        resetParser();
      }
      break;

    case WAIT_TYPE:
      rxType = b;
      rxXor ^= b;
      rxState = WAIT_LENGTH;
      break;

    case WAIT_LENGTH:
      rxLength = b;
      rxIndex = 0;
      rxXor ^= b;
      rxState = rxLength == 0 ? WAIT_CHECKSUM : WAIT_PAYLOAD;
      break;

    case WAIT_PAYLOAD:
      rxPayload[rxIndex++] = b;
      rxXor ^= b;
      if (rxIndex >= rxLength) {
        rxState = WAIT_CHECKSUM;
      }
      break;

    case WAIT_CHECKSUM:
      if (b == rxXor) {
        handleFrame(rxType, rxPayload, rxLength);
      }
      resetParser();
      break;
  }
}

void connectWifi() {
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print('.');
  }
  Serial.println();
  Serial.print("WiFi connected. IP: ");
  Serial.println(WiFi.localIP());
}

void setup() {
  Serial.begin(115200);
  delay(800);

  // 先设置 USB 设备描述符，再启动 HID 和 USB。
  // Windows 高级详情里会看到这些字符串和 VID/PID。
  // 请勿冒用第三方品牌；如需商业化，请使用自己合法申请或授权的 VID/PID。
  USB.VID(APP_USB_VID);
  USB.PID(APP_USB_PID);
  USB.manufacturerName(APP_USB_MANUFACTURER);
  USB.productName(APP_USB_PRODUCT);
  USB.serialNumber(APP_USB_SERIAL);

  HID.begin();
  USB.begin();

  connectWifi();

  server.begin();
  server.setNoDelay(true);

  Serial.print("TCP HID gateway listening on port ");
  Serial.println(TCP_PORT);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    releaseAll();
    connectWifi();
  }

  if (!client || !client.connected()) {
    if (client) {
      client.stop();
      releaseAll();
    }

    client = server.available();
    if (client) {
      client.setNoDelay(true);
      lastClientByteMs = millis();
      resetParser();
      Serial.print("Client connected: ");
      Serial.println(client.remoteIP());
    }
  }

  if (client && client.connected()) {
    while (client.available()) {
      uint8_t b = static_cast<uint8_t>(client.read());
      lastClientByteMs = millis();
      parseByte(b);
    }

    if (millis() - lastClientByteMs > CLIENT_TIMEOUT_MS) {
      Serial.println("Client timeout, releasing all HID states.");
      client.stop();
      releaseAll();
      resetParser();
    }
  }
}
