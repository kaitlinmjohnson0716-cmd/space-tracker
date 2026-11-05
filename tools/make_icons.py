"""Draw the app icons (a small planet with a ring) with the standard library."""
import struct
import sys
import zlib


def png(size, path):
    cx = cy = size / 2
    r = size * 0.26
    rows = []
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            dx, dy = x - cx, y - cy
            px = (11, 16, 38)                                  # background
            d = (dx * dx + dy * dy) ** 0.5
            ring = abs((dx / 1.0) ** 2 / (size * 0.42) ** 2 + (dy / 0.42) ** 2 / (size * 0.42) ** 2 - 1)
            if d < r:
                px = (96, 165, 250)                            # planet
            elif ring < 0.06 and dy > -r * 0.2:
                px = (251, 191, 36)                            # ring
            row += bytes(px)
        rows.append(bytes(row))
    raw = b"".join(rows)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


if __name__ == "__main__":
    for s in (192, 512):
        png(s, "icon-%d.png" % s)
    print("icons written", file=sys.stderr)
