#!/usr/bin/env python3
import argparse
import datetime as dt
import sys
import time

try:
    import serial
except ImportError:
    print("Missing dependency: pyserial")
    print("Install with: pip install pyserial")
    sys.exit(1)


def timestamp_now() -> str:
    return dt.datetime.now().strftime("[%H:%M:%S.%f]")[:-3] + "]"


def run_monitor(port: str, baud: int, timeout: float, show_ts: bool, reconnect: bool) -> int:
    while True:
        try:
            with serial.Serial(
                port=port,
                baudrate=baud,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=timeout,
            ) as ser:
                print(f"Listening on {port} @ {baud} (8N1). Press Ctrl+C to stop.")

                buf = bytearray()
                while True:
                    chunk = ser.read(256)
                    if not chunk:
                        continue
                    buf.extend(chunk)

                    while True:
                        # 找到\n才输出,所以行为其实是不一样的
                        idx = buf.find(b"\n")
                        if idx < 0:
                            break

                        line = bytes(buf[:idx + 1])
                        del buf[:idx + 1]
                        # 使用utf-8解码然后输出
                        text = line.decode("utf-8", errors="replace").rstrip("\r\n")
                        if show_ts:
                            print(f"{timestamp_now()} {text}")
                        else:
                            print(text)

        except KeyboardInterrupt:
            print("\nStopped.")
            return 0
        except serial.SerialException as exc:
            print(f"Serial error on {port}: {exc}")
            if not reconnect:
                return 2
            print("Retrying in 1s...")
            time.sleep(1)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Simple ESP32 serial monitor (similar to pio monitor output)"
    )
    parser.add_argument("-p", "--port", default="/dev/ttyUSB0", help="Serial port path")
    parser.add_argument("-b", "--baud", type=int, default=115200, help="Baud rate")
    parser.add_argument("--timeout", type=float, default=0.2, help="Read timeout in seconds")
    parser.add_argument("--no-timestamp", action="store_true", help="Disable timestamp prefix")
    parser.add_argument("--reconnect", action="store_true", help="Auto reconnect if port is temporarily unavailable")
    args = parser.parse_args()

    return run_monitor(
        port=args.port,
        baud=args.baud,
        timeout=args.timeout,
        show_ts=not args.no_timestamp,
        reconnect=args.reconnect,
    )


if __name__ == "__main__":
    raise SystemExit(main())
