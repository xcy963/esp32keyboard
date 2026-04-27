# TCP Protocol

## Frame format

```text
+--------+--------+------+--------+----------+----------+
| 0xA5   | 0x5A   | Type | Length | Payload  | Checksum |
+--------+--------+------+--------+----------+----------+
```

- `Type`: 1 byte
- `Length`: 1 byte, payload length, 0 to 255
- `Checksum`: XOR of all bytes from `0xA5` through the last payload byte

TCP is stream-based, so the ESP32 parser can handle frames split across packets or multiple frames in one packet.

## Message types

```text
0x01 Keyboard report
0x02 Absolute touchpad report
0x03 Ping
0x04 Release all
```

## Keyboard report payload

Length: 8 bytes

```text
byte0: modifier bits
byte1: reserved, normally 0
byte2: keycode 1
byte3: keycode 2
byte4: keycode 3
byte5: keycode 4
byte6: keycode 5
byte7: keycode 6
```

Modifier bits:

```text
bit0 Left Ctrl
bit1 Left Shift
bit2 Left Alt
bit3 Left GUI
bit4 Right Ctrl
bit5 Right Shift
bit6 Right Alt
bit7 Right GUI
```

Common HID keycodes:

```text
A = 0x04
B = 0x05
C = 0x06
1 = 0x1E
2 = 0x1F
3 = 0x20
Enter = 0x28
Esc = 0x29
Backspace = 0x2A
Tab = 0x2B
Space = 0x2C
```

To release all keyboard keys, send a keyboard report with all 8 bytes set to zero, or send `Release all`.

## Absolute touchpad report payload

Length: 6 bytes

```text
byte0: buttons
byte1: x low
byte2: x high
byte3: y low
byte4: y high
byte5: contact
```

- X and Y are unsigned little-endian 16-bit values.
- Valid coordinate range is 0 to 32767.
- `contact = 1`: finger touching
- `contact = 0`: finger released

Button bits:

```text
bit0 left button
bit1 right button
bit2 middle button
```

## Example keyboard frame

Press key `A`:

```text
Payload: 00 00 04 00 00 00 00 00
Frame:   A5 5A 01 08 00 00 04 00 00 00 00 00 F2
```

Release keyboard:

```text
Payload: 00 00 00 00 00 00 00 00
Frame:   A5 5A 01 08 00 00 00 00 00 00 00 00 F6
```

## Example touchpad frame

Move/contact at center `(16384, 16384)`, no buttons:

```text
Payload: 00 00 40 00 40 01
```
