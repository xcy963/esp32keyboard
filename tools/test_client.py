#!/usr/bin/env python3
import socket
import struct
import time
import argparse

MAGIC = b"\xA5\x5A"
TYPE_KEYBOARD = 0x01
TYPE_TOUCHPAD = 0x02
TYPE_PING = 0x03
TYPE_RELEASE_ALL = 0x04

# Common USB HID keycodes
KEY_A = 0x04
KEY_B = 0x05
KEY_C = 0x06
KEY_ENTER = 0x28
KEY_SPACE = 0x2C
MOD_LCTRL = 0x01
MOD_LSHIFT = 0x02
MOD_LALT = 0x04
MOD_LGUI = 0x08

def make_frame(msg_type: int, payload: bytes = b"") -> bytes:
    if len(payload) > 255:
        raise ValueError("payload too long")
    data = bytearray(MAGIC)
    data.append(msg_type & 0xFF)
    data.append(len(payload) & 0xFF)
    data.extend(payload)
    checksum = 0
    for b in data:
        checksum ^= b
    data.append(checksum)
    return bytes(data)

def send_keyboard(sock: socket.socket, modifiers: int = 0, keys=None):
    keys = list(keys or [])[:6]
    payload = bytearray(8)
    payload[0] = modifiers & 0xFF
    for i, key in enumerate(keys):
        payload[2 + i] = key & 0xFF
    sock.sendall(make_frame(TYPE_KEYBOARD, bytes(payload)))

def send_touchpad(sock: socket.socket, x: int, y: int, buttons: int = 0, contact: int = 1):
    x = max(0, min(32767, int(x)))
    y = max(0, min(32767, int(y)))
    payload = struct.pack("<BHHB", buttons & 0x07, x, y, 1 if contact else 0)
    sock.sendall(make_frame(TYPE_TOUCHPAD, payload))

def release_all(sock: socket.socket):
    sock.sendall(make_frame(TYPE_RELEASE_ALL))

def ping(sock: socket.socket):
    sock.sendall(make_frame(TYPE_PING))

def demo(ip: str, port: int):
    with socket.create_connection((ip, port), timeout=3) as sock:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        print("Connected. Sending keyboard demo: a, Shift+b, Enter")
        send_keyboard(sock, keys=[KEY_A])
        time.sleep(0.08)
        send_keyboard(sock, keys=[])
        time.sleep(0.08)

        send_keyboard(sock, modifiers=MOD_LSHIFT, keys=[KEY_B])
        time.sleep(0.08)
        send_keyboard(sock, keys=[])
        time.sleep(0.08)

        send_keyboard(sock, keys=[KEY_ENTER])
        time.sleep(0.08)
        send_keyboard(sock, keys=[])
        time.sleep(0.3)

        print("Sending absolute touchpad diagonal movement")
        for i in range(120):
            x = int(i / 119 * 32767)
            y = int(i / 119 * 32767)
            send_touchpad(sock, x, y, buttons=0, contact=1)
            time.sleep(0.008)

        print("Sending left click at center")
        send_touchpad(sock, 16384, 16384, buttons=1, contact=1)
        time.sleep(0.08)
        send_touchpad(sock, 16384, 16384, buttons=0, contact=1)
        time.sleep(0.08)
        send_touchpad(sock, 16384, 16384, buttons=0, contact=0)

        release_all(sock)
        print("Done")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ESP32-S3 TCP HID gateway test client")
    parser.add_argument("ip", help="ESP32 IP address")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    demo(args.ip, args.port)
