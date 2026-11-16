#!/usr/bin/env python3
"""Entry program for make.fun ai-excited-01 (Python 3.13, stdlib only).

Writes a single image to /output/entry.png: a white rocket launching
straight up through the curl of a giant ocean wave at golden hour.

The bundled image.jpg is copied verbatim, but only after the raw bytes
pass every gate the competition sets:

  * at most 1 MiB (1,048,576 bytes),
  * at most 1024 by 1024 pixels,
  * a complete JPEG (starts with SOI, ends with EOI).

Run it twice to prove determinism:
    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
Both runs write the same bytes, because the copy is byte-for-byte.
"""

import os
import sys

SOURCE = "image.jpg"
TARGET = "entry.png"
BYTE_LIMIT = 1_048_576
SIDE_LIMIT = 1024

START_MARK = b"\xff\xd8"  # SOI
END_MARK = b"\xff\xd9"    # EOI


class GateError(Exception):
    """Raised when the bundled image fails one of the competition gates."""


def read_segments(blob):
    """Yield (marker, payload) pairs from a JPEG byte string.

    Skips padding 0xFF bytes, treats standalone markers (SOI, EOI,
    RST0-RST7) as having no payload, and slices every other segment
    by its declared length. Stops cleanly at the end of the data.
    """
    cursor = 2  # past the SOI marker
    while cursor < len(blob):
        if blob[cursor] != 0xFF:
            raise GateError("marker expected at byte %d" % cursor)
        while cursor < len(blob) and blob[cursor] == 0xFF:
            cursor += 1
        if cursor >= len(blob):
            return
        marker = blob[cursor]
        cursor += 1
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            yield marker, b""
            continue
        if cursor + 2 > len(blob):
            raise GateError("segment length cut off")
        size = (blob[cursor] << 8) | blob[cursor + 1]
        if size < 2:
            raise GateError("segment length %d is impossible" % size)
        payload = blob[cursor + 2:cursor + size]
        if len(payload) != size - 2:
            raise GateError("segment runs past the end of the file")
        yield marker, payload
        cursor += size


def measure(blob):
    """Return the (width, height) of a JPEG from its first frame header."""
    if blob[:2] != START_MARK:
        raise GateError("missing SOI marker at the start")
    for marker, payload in read_segments(blob):
        if marker in (0xC0, 0xC1, 0xC2):
            # Frame header: precision (1), height (2), width (2).
            if len(payload) < 5:
                raise GateError("frame header is too short")
            height = (payload[1] << 8) | payload[2]
            width = (payload[3] << 8) | payload[4]
            return width, height
    raise GateError("no frame header (SOF) found")


def passes_gates(blob):
    """Check the competition gates; raise GateError with the reason."""
    if not blob:
        raise GateError("%s is empty" % SOURCE)
    if len(blob) > BYTE_LIMIT:
        raise GateError(
            "%s is %d bytes, above the 1 MiB limit" % (SOURCE, len(blob)))
    if blob[:2] != START_MARK or blob[-2:] != END_MARK:
        raise GateError("not a complete JPEG (SOI/EOI missing)")
    width, height = measure(blob)
    if width > SIDE_LIMIT or height > SIDE_LIMIT:
        raise GateError(
            "dimensions %dx%d exceed the 1024x1024 limit" % (width, height))


def run():
    base = os.path.dirname(os.path.abspath(__file__))
    source_path = os.path.join(base, SOURCE)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    target_path = os.path.join(out_dir, TARGET)

    with open(source_path, "rb") as handle:
        blob = handle.read()

    try:
        passes_gates(blob)
    except GateError as problem:
        print(str(problem), file=sys.stderr)
        return 1

    os.makedirs(out_dir, exist_ok=True)
    with open(target_path, "wb") as handle:
        handle.write(blob)

    with open(target_path, "rb") as handle:
        copied = handle.read()
    if copied != blob:
        print("written file differs from the source", file=sys.stderr)
        return 1
    try:
        passes_gates(copied)
    except GateError as problem:
        print("written file fails the gate: " + str(problem),
              file=sys.stderr)
        return 1

    print("wrote %s (%d bytes)" % (target_path, len(copied)))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
