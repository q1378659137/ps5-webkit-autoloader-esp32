#!/usr/bin/env python3
"""按端口打开以来经过的时间，逐行打印串口日志。

固件日志是 UTF-8 字节流，所以这里先把 Windows 控制台代码页切到 65001，
再按 UTF-8 解码；碰到坏字节（比如一行被按字节截断在多字节字符中间）
就降级成 `?`，不抛异常、也不打出乱码。

    python debug/serial_timestamp.py COM4
    python debug/serial_timestamp.py /dev/ttyACM0 115200
    python debug/serial_timestamp.py --self-test
"""

import argparse
import sys
import time


def setup_console() -> None:
    """让 stdout 能直接输出 UTF-8（Windows 控制台尤其需要）。"""
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        except Exception:
            pass
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def decode(raw: bytes) -> str:
    """按 UTF-8 解码；坏字节降级成 `?`，绝不抛异常。"""
    return raw.decode("utf-8", "replace").replace("\ufffd", "?")


def stamp(seconds: int) -> str:
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"[{hours:02d}:{minutes:02d}:{secs:02d}] "


def self_test() -> int:
    """三条样例：纯英文、中文、被截断的多字节字符。"""
    samples = [
        ("英文行", b"READY\n", "[00:00:00] READY\n"),
        ("中文行", "准备就绪\n".encode("utf-8"), "[00:00:00] 准备就绪\n"),
        ("截断的多字节字符", "准备\n".encode("utf-8")[:4] + b"\n", "[00:00:00] 准?\n"),
    ]
    bad = 0
    for name, raw, expected in samples:
        got = stamp(0) + decode(raw)
        ok = got == expected
        print(f"[{'  OK  ' if ok else ' FAIL '}] {name}: {got!r}")
        if not ok:
            print(f"         期望: {expected!r}")
            bad += 1
    print("\n自检通过" if not bad else f"\n{bad} 条样例不对")
    return 1 if bad else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("port", nargs="?",
                        help="串口，比如 COM4 或 /dev/ttyACM0")
    parser.add_argument("baud", nargs="?", type=int, default=115200,
                        help="波特率，默认 115200")
    parser.add_argument("--self-test", action="store_true",
                        help="不打开串口，只跑编码自检")
    args = parser.parse_args()

    setup_console()

    if args.self_test:
        return self_test()
    if not args.port:
        parser.error("需要指定串口，或者用 --self-test 跑自检")

    import serial  # 只在真要用串口时才导入，自检不依赖 pyserial

    with serial.Serial(args.port, args.baud, timeout=0.2) as port:
        started = time.monotonic()
        pending = bytearray()

        def emit(line):
            elapsed = int(time.monotonic() - started)
            sys.stdout.write(stamp(elapsed) + decode(line))
            sys.stdout.flush()

        print(f"正在监视 {args.port}（{args.baud} 波特率）；按 Ctrl+C 退出", file=sys.stderr)
        try:
            while True:
                pending.extend(port.read(256))
                while (newline := pending.find(b"\n")) >= 0:
                    line = bytes(pending[: newline + 1])
                    del pending[: newline + 1]
                    emit(line)
                if len(pending) > 8192:
                    emit(bytes(pending) + b"\n")
                    pending.clear()
        except KeyboardInterrupt:
            if pending:
                emit(bytes(pending) + b"\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
