#!/usr/bin/env python3
"""ai-excited-01 entry (Python 3.13, standard library only).

Writes one image to /output/entry.png: a rocket launching straight up
through the curl of a giant ocean wave at golden hour. The program copies
the bundled image.jpg to the output directory and validates the gate
limits (at most 1 MiB, at most 1024 by 1024 pixels) before it writes.

Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in for /output:
    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import os
import shutil
import struct
import sys

MAX_BYTES = 1_048_576  # 1 MiB
MAX_SIDE = 1024


def jpeg_dimensions(path: str) -> tuple[int, int]:
    """Return (width, height) of a baseline/progressive JPEG, stdlib only."""
    with open(path, "rb") as f:
        data = f.read(2)
        if data != b"\xff\xd8":
            raise ValueError("not a JPEG (missing SOI marker)")
        while True:
            marker = f.read(2)
            if len(marker) < 2 or marker[0] != 0xFF:
                raise ValueError("bad JPEG marker")
            code = marker[1]
            if code in (0xC0, 0xC1, 0xC2):  # SOF0/SOF1/SOF2
                f.read(2)  # segment length
                f.read(1)  # precision
                height = struct.unpack(">H", f.read(2))[0]
                width = struct.unpack(">H", f.read(2))[0]
                return width, height
            if code in (0xD8, 0xD9) or 0xD0 <= code <= 0xD7:
                continue
            length = struct.unpack(">H", f.read(2))[0]
            f.seek(length - 2, 1)


def main() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "image.jpg")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    dst = os.path.join(out_dir, "entry.png")

    size = os.path.getsize(src)
    if size > MAX_BYTES:
        print(f"image.jpg is {size} bytes, over the 1 MiB gate", file=sys.stderr)
        return 1

    width, height = jpeg_dimensions(src)
    if width > MAX_SIDE or height > MAX_SIDE:
        print(f"image is {width}x{height}, over the 1024x1024 gate",
              file=sys.stderr)
        return 1

    os.makedirs(out_dir, exist_ok=True)
    shutil.copyfile(src, dst)

    written = os.path.getsize(dst)
    if written != size or written > MAX_BYTES:
        print("output size mismatch or over the gate", file=sys.stderr)
        return 1
    print(f"wrote {dst} ({written} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
