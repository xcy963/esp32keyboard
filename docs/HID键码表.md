# HID 键码表（适配本项目）

本表基于 USB HID Usage Tables 的 Keyboard/Keypad Page (`0x07`)。

在本项目协议中：

- `byte0`：修饰键位（modifier bits）
- `byte2 ~ byte7`：最多 6 个普通键键码

## 1. 修饰键位（byte0）

```text
bit0 Left Ctrl   (左 Ctrl)
bit1 Left Shift  (左 Shift)
bit2 Left Alt    (左 Alt)
bit3 Left GUI    (左 Win / 左 Command)
bit4 Right Ctrl  (右 Ctrl)
bit5 Right Shift (右 Shift)
bit6 Right Alt   (右 Alt)
bit7 Right GUI   (右 Win / 右 Command)
```

示例：

- `byte0 = 0x02` 表示按下左 Shift
- `byte0 = 0x05` 表示按下左 Ctrl + 左 Alt

## 2. 字母键（A-Z）

```text
A 0x04  B 0x05  C 0x06  D 0x07  E 0x08  F 0x09
G 0x0A  H 0x0B  I 0x0C  J 0x0D  K 0x0E  L 0x0F
M 0x10  N 0x11  O 0x12  P 0x13  Q 0x14  R 0x15
S 0x16  T 0x17  U 0x18  V 0x19  W 0x1A  X 0x1B
Y 0x1C  Z 0x1D
```

## 3. 数字键（主键盘区）

```text
1 0x1E  2 0x1F  3 0x20  4 0x21  5 0x22
6 0x23  7 0x24  8 0x25  9 0x26  0 0x27
```

## 4. 常用控制键

```text
Enter      0x28
Esc        0x29
Backspace  0x2A
Tab        0x2B
Space      0x2C
- _        0x2D
= +        0x2E
[ {        0x2F
] }        0x30
\\ |       0x31
; :        0x33
' "        0x34
` ~        0x35
, <        0x36
. >        0x37
/ ?        0x38
CapsLock   0x39
```

## 5. 功能键（F1-F12）

```text
F1  0x3A  F2  0x3B  F3  0x3C  F4  0x3D
F5  0x3E  F6  0x3F  F7  0x40  F8  0x41
F9  0x42  F10 0x43  F11 0x44  F12 0x45
```

## 6. 导航与编辑键

```text
Insert     0x49
Home       0x4A
PageUp     0x4B
Delete     0x4C
End        0x4D
PageDown   0x4E
Right      0x4F
Left       0x50
Down       0x51
Up         0x52
```

## 7. 小键盘（Numpad）常用

```text
NumLock    0x53
KP /       0x54
KP *       0x55
KP -       0x56
KP +       0x57
KP Enter   0x58
KP 1       0x59
KP 2       0x5A
KP 3       0x5B
KP 4       0x5C
KP 5       0x5D
KP 6       0x5E
KP 7       0x5F
KP 8       0x60
KP 9       0x61
KP 0       0x62
KP .       0x63
```

## 8. 发送规则与示例

- 按下某键：在 `byte2~byte7` 填入对应键码
- 释放全部：发送 8 字节全 0（或发送协议里的 `Release all`）
- 组合键：修饰键放 `byte0`，普通键放 `byte2~byte7`

示例：`Ctrl + Alt + Delete`

- `byte0 = 0x05`（左 Ctrl + 左 Alt）
- `byte2 = 0x4C`（Delete）

键盘 payload：

```text
05 00 4C 00 00 00 00 00
```
