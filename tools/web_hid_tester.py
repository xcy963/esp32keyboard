#!/usr/bin/env python3
import argparse
import socket
import struct
from flask import Flask, jsonify, request

MAGIC = b"\xA5\x5A"
TYPE_KEYBOARD = 0x01
TYPE_TOUCHPAD = 0x02
TYPE_PING = 0x03
TYPE_RELEASE_ALL = 0x04

KEY_A = 0x04
KEY_B = 0x05
KEY_C = 0x06
KEY_ENTER = 0x28
KEY_SPACE = 0x2C
KEY_DELETE = 0x4C

MOD_LCTRL = 0x01
MOD_LSHIFT = 0x02
MOD_LALT = 0x04

app = Flask(__name__)
DEFAULT_PORT = 5000
SCREEN_WIDTH = 2560
SCREEN_HEIGHT = 1440


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


def with_device(ip: str, port: int, fn):
    with socket.create_connection((ip, port), timeout=2.0) as sock:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        fn(sock)


def pixel_to_hid(px: int, py: int, width: int = SCREEN_WIDTH, height: int = SCREEN_HEIGHT):
    px = max(0, min(width - 1, int(px)))
    py = max(0, min(height - 1, int(py)))
    hx = int(round(px * 32767 / (width - 1)))
    hy = int(round(py * 32767 / (height - 1)))
    return hx, hy


@app.get("/")
def index():
    return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>ESP32 HID Tester</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; margin: 16px; background:#f5f7fb; }
    .card { background:#fff; border-radius:12px; padding:16px; box-shadow:0 2px 10px rgba(0,0,0,.08); max-width:780px; margin:auto; }
    h1 { margin:0 0 12px; font-size:22px; }
    .row { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:10px; }
    input { padding:10px; border:1px solid #cbd5e1; border-radius:8px; font-size:16px; }
    button { padding:10px 12px; border:0; border-radius:8px; background:#0f766e; color:#fff; font-size:15px; }
    button.secondary { background:#475569; }
    button.warn { background:#b91c1c; }
    #log { white-space:pre-wrap; background:#0b1020; color:#d1e7ff; padding:10px; border-radius:8px; min-height:120px; }
  </style>
</head>
<body>
  <div class="card">
    <h1>ESP32 HID 网页测试</h1>
    <div class="row">
      <input id="ip" placeholder="ESP32 IP，如 192.168.43.113" style="flex:1; min-width:220px" />
      <input id="port" value="5000" style="width:100px" />
      <button onclick="saveTarget()">保存目标</button>
      <button class="secondary" onclick="act('ping')">Ping</button>
    </div>

    <div class="row">
      <button onclick="act('key_a')">按 A</button>
      <button onclick="act('shift_b')">按 Shift+B</button>
      <button onclick="act('enter')">按 Enter</button>
      <button onclick="act('ctrl_alt_del')">Ctrl+Alt+Del</button>
      <button class="warn" onclick="act('release_all')">Release All</button>
    </div>

    <div class="row">
      <button onclick="act('mouse_center')">鼠标到中心</button>
      <button onclick="act('mouse_tl')">鼠标到左上</button>
      <button onclick="act('mouse_br')">鼠标到右下</button>
      <button onclick="act('left_click_center')">中心左键单击</button>
    </div>

    <div class="row">
      <input id="px" value="1280" style="width:120px" />
      <input id="py" value="720" style="width:120px" />
      <button onclick="movePixel()">移动到像素(2560x1440)</button>
    </div>

    <div id="log"></div>
  </div>

<script>
const ipEl = document.getElementById('ip');
const portEl = document.getElementById('port');
const pxEl = document.getElementById('px');
const pyEl = document.getElementById('py');
const logEl = document.getElementById('log');

ipEl.value = localStorage.getItem('esp_ip') || '';
portEl.value = localStorage.getItem('esp_port') || '5000';

function log(msg){
  const t = new Date().toLocaleTimeString();
  logEl.textContent = `[${t}] ${msg}\n` + logEl.textContent;
}

function target(){
  return { ip: ipEl.value.trim(), port: parseInt(portEl.value || '5000', 10) };
}

function saveTarget(){
  const t = target();
  localStorage.setItem('esp_ip', t.ip);
  localStorage.setItem('esp_port', String(t.port));
  log(`已保存目标 ${t.ip}:${t.port}`);
}

async function act(name){
  const t = target();
  if(!t.ip){ log('请先输入 ESP32 IP'); return; }
  try{
    const res = await fetch('/api/action', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ action: name, ip: t.ip, port: t.port })
    });
    const data = await res.json();
    if(data.ok){ log(`OK: ${name}`); }
    else { log(`ERR: ${data.error || 'unknown'}`); }
  } catch (e){
    log(`ERR: ${e}`);
  }
}

async function movePixel(){
  const t = target();
  if(!t.ip){ log('请先输入 ESP32 IP'); return; }
  const px = parseInt(pxEl.value || '0', 10);
  const py = parseInt(pyEl.value || '0', 10);
  try{
    const res = await fetch('/api/action', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ action: 'mouse_pixel', ip: t.ip, port: t.port, x: px, y: py })
    });
    const data = await res.json();
    if(data.ok){ log(`OK: mouse_pixel (${px}, ${py}) -> HID (${data.hid_x}, ${data.hid_y})`); }
    else { log(`ERR: ${data.error || 'unknown'}`); }
  } catch (e){
    log(`ERR: ${e}`);
  }
}
</script>
</body>
</html>"""


@app.post("/api/action")
def api_action():
    data = request.get_json(silent=True) or {}
    action = str(data.get("action", "")).strip()
    ip = str(data.get("ip", "")).strip()
    port = int(data.get("port", DEFAULT_PORT))
    req_x = data.get("x", 0)
    req_y = data.get("y", 0)

    if not ip:
        return jsonify(ok=False, error="missing ip"), 400

    def do_action(sock: socket.socket):
        if action == "ping":
            ping(sock)
            return
        if action == "release_all":
            release_all(sock)
            return
        if action == "key_a":
            send_keyboard(sock, keys=[KEY_A])
            send_keyboard(sock, keys=[])
            return
        if action == "shift_b":
            send_keyboard(sock, modifiers=MOD_LSHIFT, keys=[KEY_B])
            send_keyboard(sock, keys=[])
            return
        if action == "enter":
            send_keyboard(sock, keys=[KEY_ENTER])
            send_keyboard(sock, keys=[])
            return
        if action == "ctrl_alt_del":
            send_keyboard(sock, modifiers=MOD_LCTRL | MOD_LALT, keys=[KEY_DELETE])
            send_keyboard(sock, keys=[])
            return
        if action == "mouse_center":
            send_touchpad(sock, 16384, 16384, buttons=0, contact=1)
            return
        if action == "mouse_tl":
            send_touchpad(sock, 0, 0, buttons=0, contact=1)
            return
        if action == "mouse_br":
            send_touchpad(sock, 32767, 32767, buttons=0, contact=1)
            return
        if action == "left_click_center":
            send_touchpad(sock, 16384, 16384, buttons=1, contact=1)
            send_touchpad(sock, 16384, 16384, buttons=0, contact=1)
            send_touchpad(sock, 16384, 16384, buttons=0, contact=0)
            return
        if action == "mouse_pixel":
            hid_x, hid_y = pixel_to_hid(req_x, req_y)
            send_touchpad(sock, hid_x, hid_y, buttons=0, contact=1)
            return hid_x, hid_y
        raise ValueError(f"unsupported action: {action}")

    try:
        result = {"hid_x": None, "hid_y": None}

        def runner(sock):
            ret = do_action(sock)
            if isinstance(ret, tuple) and len(ret) == 2:
                result["hid_x"], result["hid_y"] = ret

        with_device(ip, port, runner)
        return jsonify(ok=True, hid_x=result["hid_x"], hid_y=result["hid_y"])
    except Exception as exc:
        return jsonify(ok=False, error=str(exc)), 500


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flask web tester for ESP32 TCP HID gateway")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host, use 0.0.0.0 for LAN access")
    parser.add_argument("--port", type=int, default=8080, help="Web server port")
    args = parser.parse_args()
    app.run(host=args.host, port=args.port, debug=False)
