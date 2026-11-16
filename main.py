#!/usr/bin/env python3
"""ai-excited-01 entry program (Python 3.13, standard library only).

It writes one image to /output/entry.png: a white rocket launching
straight up through the curl of a giant ocean wave at golden hour.

The bundled image.jpg is copied to the output directory unchanged, but
only after it clears the competition gate, checked from the raw bytes:

  * no more than 1 MiB (1,048,576 bytes),
  * no more than 1024 by 1024 pixels,
  * a whole JPEG (SOI at the start, EOI at the end).

Local check:
    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py

The copy is byte-for-byte, so two runs write identical output.
"""

import os
import sys

MAX_BYTES = 1_048_576
MAX_SIDE = 1024
SOURCE_NAME = "image.jpg"
OUTPUT_NAME = "entry.png"
SOI = b"\xff\xd8"
EOI = b"\xff\xd9"


def jpeg_dimensions(data: bytes) -> tuple[int, int]:
    """Return (width, height) by scanning the JPEG marker stream in memory.

    Walks the segments starting after the SOI marker. Fill bytes (0xFF)
    are skipped; standalone markers (RSTn, SOI, EOI) carry no length, so
    they are passed over; every other segment is skipped by its length
    until a SOF0/SOF1/SOF2 header is found, which holds the dimensions.
    """
    if data[:2] != SOI:
        raise ValueError("not a JPEG: missing SOI marker")
    pos = 2
    while pos < len(data):
        if data[pos] != 0xFF:
            raise ValueError("bad JPEG marker at offset %d" % pos)
        while pos < len(data) and data[pos] == 0xFF:
            pos += 1
        if pos >= len(data):
            break
        code = data[pos]
        pos += 1
        if code in (0xC0, 0xC1, 0xC2):
            # SOF segment: length (2), precision (1), height (2), width (2).
            if pos + 7 > len(data):
                raise ValueError("truncated SOF segment")
            height = (data[pos + 3] << 8) | data[pos + 4]
            width = (data[pos + 5] << 8) | data[pos + 6]
            return width, height
        if code in (0xD8, 0xD9) or 0xD0 <= code <= 0xD7:
            continue
        if pos + 2 > len(data):
            raise ValueError("truncated segment length")
        length = (data[pos] << 8) | data[pos + 1]
        if length < 2:
            raise ValueError("bad JPEG segment length")
        pos += length
    raise ValueError("no SOF segment found")


def check_gate(data: bytes) -> str | None:
    """Return None when the image clears the gate, else a reason string."""
    if len(data) > MAX_BYTES:
        return "%s is %d bytes, over the 1 MiB gate" % (SOURCE_NAME, len(data))
    if data[:2] != SOI or data[-2:] != EOI:
        return "%s is not a whole JPEG (missing SOI or EOI)" % SOURCE_NAME
    width, height = jpeg_dimensions(data)
    if width > MAX_SIDE or height > MAX_SIDE:
        return "image is %dx%d, over the 1024x1024 gate" % (width, height)
    return None


def main() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, SOURCE_NAME)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    dst = os.path.join(out_dir, OUTPUT_NAME)

    with open(src, "rb") as handle:
        data = handle.read()

    problem = check_gate(data)
    if problem is not None:
        print(problem, file=sys.stderr)
        return 1

    os.makedirs(out_dir, exist_ok=True)
    with open(dst, "wb") as handle:
        handle.write(data)

    with open(dst, "rb") as handle:
        written = handle.read()
    if written != data:
        print("output differs from source after write", file=sys.stderr)
        return 1
    problem = check_gate(written)
    if problem is not None:
        print("output fails the gate after write: " + problem,
              file=sys.stderr)
        return 1
    print("wrote %s (%d bytes)" % (dst, len(written)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
