"""What the tests that run in the editor share (884, 888): a PNG read in pure Python (the editor's Python has no image library) and the
frames a second counted over real time (PR #114's reviews: one decoder and one frame counter, not copies drifting apart).
"""
import struct
import time
import zlib


def lumas(path, box=(0.0, 0.0, 1.0, 1.0), every=2):
    """(x share, y share, luma) of every <every>th row and every 4th pixel of the box (shares of the width and height) of a PNG"""
    data = open(path, "rb").read(); pos = 8; w = h = 0; ct = 6; idat = b""
    while pos + 8 <= len(data):
        ln, typ = struct.unpack(">I4s", data[pos:pos + 8]); body = data[pos + 8:pos + 8 + ln]; pos += 12 + ln
        if typ == b"IHDR": w, h, bd, ct = struct.unpack(">IIBB", body[:10])
        elif typ == b"IDAT": idat += body
        elif typ == b"IEND": break
    bpp = 4 if ct == 6 else 3; raw = zlib.decompress(idat); stride = w * bpp
    prev = bytearray(stride); x0, y0, x1, y1 = int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)
    i = 0
    for y in range(h):
        f = raw[i]; line = bytearray(raw[i + 1:i + 1 + stride]); i += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0; b = prev[x]; c = prev[x - bpp] if x >= bpp else 0
            if f == 1: line[x] = (line[x] + a) & 255
            elif f == 2: line[x] = (line[x] + b) & 255
            elif f == 3: line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                p_ = a + b - c; pa, pb, pc = abs(p_ - a), abs(p_ - b), abs(p_ - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        prev = line
        if y0 <= y < y1 and y % every == 0:
            for x in range(x0, x1, 4):
                o = x * bpp
                yield ((x - x0) / max(x1 - x0, 1), (y - y0) / max(y1 - y0, 1), 0.2126 * line[o] + 0.7152 * line[o + 1] + 0.0722 * line[o + 2])


def pixels(path, box_px):
    """the luma of every pixel of a box given in pixels (x0, y0, x1, y1) of a PNG, as rows"""
    data = open(path, "rb").read(); pos = 8; w = h = 0; ct = 6; idat = b""
    while pos + 8 <= len(data):
        ln, typ = struct.unpack(">I4s", data[pos:pos + 8]); body = data[pos + 8:pos + 8 + ln]; pos += 12 + ln
        if typ == b"IHDR": w, h, bd, ct = struct.unpack(">IIBB", body[:10])
        elif typ == b"IDAT": idat += body
        elif typ == b"IEND": break
    bpp = 4 if ct == 6 else 3; raw = zlib.decompress(idat); stride = w * bpp
    x0, y0, x1, y1 = [int(v) for v in box_px]; x1 = min(x1, w); y1 = min(y1, h)
    prev = bytearray(stride); out = []; i = 0
    for y in range(min(h, y1)):
        f = raw[i]; line = bytearray(raw[i + 1:i + 1 + stride]); i += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0; b = prev[x]; c = prev[x - bpp] if x >= bpp else 0
            if f == 1: line[x] = (line[x] + a) & 255
            elif f == 2: line[x] = (line[x] + b) & 255
            elif f == 3: line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                p_ = a + b - c; pa, pb, pc = abs(p_ - a), abs(p_ - b), abs(p_ - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        prev = line
        if y >= y0:
            out.append([0.2126 * line[x * bpp] + 0.7152 * line[x * bpp + 1] + 0.0722 * line[x * bpp + 2] for x in range(x0, x1)])
    return out


def shifted_diff(a, b, reach=3, margin=6, hole=0):
    """the least mean absolute luma difference between two equal boxes of pixels (rows) over whole-pixel shifts of b within reach, the
    box's margin left out, and a square hole of that half size at its middle (what is drawn at a fixed place on the screen, the minimap's
    arrow): (difference, dx, dy)"""
    best = None
    h, w = len(a), len(a[0]) if a else 0
    hx0, hx1, hy0, hy1 = w // 2 - hole, w // 2 + hole, h // 2 - hole, h // 2 + hole
    for dy in range(-reach, reach + 1):
        for dx in range(-reach, reach + 1):
            s = 0.0; n = 0
            for y in range(margin, h - margin, 1):
                ra, rb = a[y], b[y + dy]
                for x in range(margin, w - margin, 1):
                    if hole and hx0 <= x < hx1 and hy0 <= y < hy1: continue
                    s += abs(ra[x] - rb[x + dx]); n += 1
            d = s / max(n, 1)
            if best is None or d < best[0]: best = (d, dx, dy)
    return best


def grid(path, box=(0.0, 0.0, 1.0, 1.0), nx=8, ny=6, every=2):
    """the mean luma of each of nx x ny cells over the box"""
    S = [[0.0] * nx for _ in range(ny)]; N = [[0] * nx for _ in range(ny)]
    for u, v, l in lumas(path, box, every):
        gx, gy = min(nx - 1, int(u * nx)), min(ny - 1, int(v * ny))
        S[gy][gx] += l; N[gy][gx] += 1
    return [[S[j][k] / max(N[j][k], 1) for k in range(nx)] for j in range(ny)]


def stats(path, box=(0.0, 0.0, 1.0, 1.0), every=4):
    """the mean and standard deviation of the luma (0-255) over the box"""
    vals = [l for _, _, l in lumas(path, box, every)]
    m = sum(vals) / max(len(vals), 1)
    return m, (sum((v - m) ** 2 for v in vals) / max(len(vals), 1)) ** 0.5


def luma_diff(a_path, b_path, nx=8, ny=6):
    """the mean of the cells' absolute luma differences between two pictures"""
    a, b = grid(a_path, nx=nx, ny=ny, every=4), grid(b_path, nx=nx, ny=ny, every=4)
    return round(sum(abs(a[j][i] - b[j][i]) for j in range(ny) for i in range(nx)) / float(nx * ny), 2)


def frames(sec=10.0):
    """a generator stepped once a frame by the test's tick: the frames a second over sec of real time, and the 95th percentile frame
    time (the first three frames left out)"""
    n = 0; t0 = time.time(); last = t0; dts = []
    while time.time() - t0 < sec:
        yield; t_ = time.time(); dts.append((t_ - last) * 1000.0); last = t_; n += 1
    dts = sorted(dts[3:]) or [0.0]
    return {"fps": round(n / (time.time() - t0), 1), "p95_ms": round(dts[min(len(dts) - 1, int(len(dts) * 0.95))], 1)}
