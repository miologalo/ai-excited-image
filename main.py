#!/usr/bin/env python3
"""ai-excited-01 entry (Python 3.13, standard library only).

Writes one image to /output/entry.png: a white rocket launching straight
up through the curl of a giant ocean wave at golden hour. The program
copies the bundled image.jpg to the output directory, but only after the
file clears every part of the competition gate:

  * at most 1 MiB (1,048,576 bytes),
  * at most 1024 by 1024 pixels,
  * a whole JPEG (starts with SOI, ends with EOI).

Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in for /output:
    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py

The program is deterministic: two runs write byte-identical output.
"""

import os
import shutil
import struct
import sys

MAX_BYTES = 1_048_576  # 1 MiB gate
MAX_SIDE = 1024        # 1024x1024 gate
SOURCE_NAME = "image.jpg"
OUTPUT_NAME = "entry.png"


def parse_jpeg_dimensions(path: str) -> tuple[int, int]:
    """Return (width, height) of a JPEG by scanning for its SOF segment.

    Standard library only. Walks the marker stream from the SOI marker,
    skipping fill bytes (0xFF) and standalone markers (RSTn, SOI, EOI),
    until it reaches SOF0/SOF1/SOF2, whose header carries the dimensions.
    """
    with open(path, "rb") as handle:
        if handle.read(2) != b"\xff\xd8":
            raise ValueError("not a JPEG: missing SOI marker")
        while True:
            # Skip any 0xFF fill bytes, then read the marker code.
            byte = handle.read(1)
            while byte == b"\xff":
                byte = handle.read(1)
            if len(byte) < 1:
                raise ValueError("no SOF segment found before end of file")
            code = byte[0]
            if code in (0xC0, 0xC1, 0xC2):  # SOF0, SOF1, SOF2
                handle.read(2)  # segment length
                handle.read(1)  # sample precision
                height = struct.unpack(">H", handle.read(2))[0]
                width = struct.unpack(">H", handle.read(2))[0]
                return width, height
            if code in (0xD8, 0xD9) or 0xD0 <= code <= 0xD7:
                continue  # standalone marker: no length field follows
            length = struct.unpack(">H", handle.read(2))[0]
            if length < 2:
                raise ValueError("bad JPEG segment length")
            handle.seek(length - 2, 1)


def is_whole_jpeg(path: str) -> bool:
    """True when the file ends with the JPEG EOI marker (0xFFD9)."""
    with open(path, "rb") as handle:
        handle.seek(-2, 2)
        return handle.read(2) == b"\xff\xd9"


def validate_entry(path: str) -> str | None:
    """Check the bundled image against the gate. None means it passes.

    Returns a human-readable reason when a check fails, so main() can
    report exactly which part of the gate rejected the entry.
    """
    size = os.path.getsize(path)
    if size > MAX_BYTES:
        return f"{SOURCE_NAME} is {size} bytes, over the 1 MiB gate"
    if not is_whole_jpeg(path):
        return f"{SOURCE_NAME} is truncated: no EOI marker at the end"
    width, height = parse_jpeg_dimensions(path)
    if width > MAX_SIDE or height > MAX_SIDE:
        return f"image is {width}x{height}, over the 1024x1024 gate"
    return None


def main() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, SOURCE_NAME)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    dst = os.path.join(out_dir, OUTPUT_NAME)

    problem = validate_entry(src)
    if problem is not None:
        print(problem, file=sys.stderr)
        return 1

    size = os.path.getsize(src)
    os.makedirs(out_dir, exist_ok=True)
    shutil.copyfile(src, dst)

    written = os.path.getsize(dst)
    if written != size:
        print("output size mismatch after copy", file=sys.stderr)
        return 1
    if not is_whole_jpeg(dst):
        print("output is truncated: no EOI marker at the end",
              file=sys.stderr)
        return 1
    print(f"wrote {dst} ({written} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
