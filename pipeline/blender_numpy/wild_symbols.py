"""The wilderness map's symbols (the user's spec of 2026-11-03: "points of interest are represented by stylized symbols, like
villages, towns, major cities, camps, lone houses in the wilderness, spawn points, ruins, ancient ritual sites, caves, monster
lairs"): drawn by this script (our own designs: ivory figures with a dark outline and a soft shadow), 256 px each, as
wmap_<kind>.png, and the map's fog (wmap_fog.png, a tiling cloud) and her cursor ring (wmap_select.png).
    python wild_symbols.py <out_dir>      (Pillow, numpy)
887_wilderness.py symbols <out_dir> imports them into brokenspire's UIArt."""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

S = 1024                    # drawn at 4x, reduced to 256
IVORY = (236, 228, 208, 255); INK = (34, 30, 27, 255); SHADE = (196, 186, 160, 255)
W = max(10, S // 34)        # the outline's width


def canvas():
    return Image.new("RGBA", (S, S), (0, 0, 0, 0))


def finish(fig):
    """an outline round the figure (its alpha grown), a shadow under it, reduced"""
    a = np.array(fig)[..., 3]
    grown = Image.fromarray(a).filter(ImageFilter.MaxFilter(2 * W + 1))
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    sh = Image.new("RGBA", (S, S), (0, 0, 0, 0)); sh.putalpha(grown.filter(ImageFilter.GaussianBlur(S // 40)).point(lambda v: int(v * 0.55)))
    out.alpha_composite(sh, (S // 60, S // 45))
    ink = Image.new("RGBA", (S, S), INK); ink.putalpha(grown)
    out.alpha_composite(ink)
    out.alpha_composite(fig)
    return out.resize((256, 256), Image.LANCZOS)


def poly(d, pts, fill=IVORY):
    d.polygon([(x * S, y * S) for x, y in pts], fill=fill)


def rect(d, x0, y0, x1, y1, fill=IVORY):
    d.rectangle([x0 * S, y0 * S, x1 * S, y1 * S], fill=fill)


def ell(d, x0, y0, x1, y1, fill=IVORY):
    d.ellipse([x0 * S, y0 * S, x1 * S, y1 * S], fill=fill)


def cut(fig, draw_fn):
    """holes through the figure (doors, windows): drawn on a mask and taken out of the alpha"""
    m = Image.new("L", (S, S), 0); draw_fn(ImageDraw.Draw(m))
    a = np.array(fig); a[..., 3] = np.where(np.array(m) > 0, 0, a[..., 3]); return Image.fromarray(a)


def town():
    f = canvas(); d = ImageDraw.Draw(f)
    rect(d, 0.18, 0.48, 0.82, 0.86)                                    # the wall
    for i in range(6): rect(d, 0.18 + i * 0.112, 0.42, 0.18 + i * 0.112 + 0.07, 0.49)   # its crenels
    for x0 in (0.12, 0.70):                                            # two towers with pointed roofs
        rect(d, x0, 0.34, x0 + 0.18, 0.86); poly(d, [(x0 - 0.03, 0.35), (x0 + 0.09, 0.12), (x0 + 0.21, 0.35)])
    return finish(cut(f, lambda m: m.chord([0.40 * S, 0.58 * S, 0.60 * S, 0.98 * S], 180, 360, fill=255) or m.rectangle([0.40 * S, 0.78 * S, 0.60 * S, 0.86 * S], fill=255)))


def city():
    f = canvas(); d = ImageDraw.Draw(f)
    rect(d, 0.10, 0.56, 0.90, 0.88)
    for i in range(8): rect(d, 0.10 + i * 0.1, 0.51, 0.10 + i * 0.1 + 0.06, 0.57)
    rect(d, 0.36, 0.22, 0.64, 0.88)                                    # the keep
    for i in range(3): rect(d, 0.36 + i * 0.1, 0.17, 0.36 + i * 0.1 + 0.07, 0.23)
    for x0 in (0.06, 0.76):
        rect(d, x0, 0.40, x0 + 0.18, 0.88); poly(d, [(x0 - 0.03, 0.41), (x0 + 0.09, 0.22), (x0 + 0.21, 0.41)])
    rect(d, 0.495, 0.04, 0.515, 0.18); poly(d, [(0.515, 0.04), (0.66, 0.08), (0.515, 0.12)])     # its banner
    f = cut(f, lambda m: m.chord([0.43 * S, 0.66 * S, 0.57 * S, 0.98 * S], 180, 360, fill=255) or m.rectangle([0.43 * S, 0.82 * S, 0.57 * S, 0.88 * S], fill=255))
    return finish(f)


def house_at(d, x, y, s):
    rect(d, x - 0.16 * s, y - 0.12 * s, x + 0.16 * s, y + 0.18 * s)
    poly(d, [(x - 0.22 * s, y - 0.10 * s), (x, y - 0.34 * s), (x + 0.22 * s, y - 0.10 * s)])


def village():
    # three houses, each outlined on its own (drawn together their outlines ran into one blob)
    out = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    for x, y, s in ((0.50, 0.40, 0.95), (0.26, 0.66, 0.9), (0.74, 0.66, 0.9)):
        f = canvas(); house_at(ImageDraw.Draw(f), x, y, s); out.alpha_composite(finish(f))
    return out


def house():
    f = canvas(); d = ImageDraw.Draw(f)
    rect(d, 0.62, 0.20, 0.72, 0.44)                                   # its chimney
    house_at(d, 0.50, 0.58, 1.6)
    f = cut(f, lambda m: m.rectangle([0.44 * S, 0.66 * S, 0.56 * S, 0.87 * S], fill=255))
    return finish(f)


def farmstead():
    # (the list of 2026-11-10: "the small farm holdings should be noted on the large map"): a barn with its gambrel roof over three
    # rows of a field
    f = canvas(); d = ImageDraw.Draw(f)
    rect(d, 0.22, 0.36, 0.78, 0.66)                                    # the barn
    poly(d, [(0.16, 0.38), (0.28, 0.20), (0.50, 0.10), (0.72, 0.20), (0.84, 0.38)])   # its roof
    for k in range(3): rect(d, 0.10, 0.72 + k * 0.075, 0.90, 0.72 + k * 0.075 + 0.04)  # the field's rows
    f = cut(f, lambda m: (m.rectangle([0.42 * S, 0.46 * S, 0.58 * S, 0.66 * S], fill=255), m.rectangle([0.44 * S, 0.22 * S, 0.56 * S, 0.30 * S], fill=255)))
    return finish(f)


def camp():
    f = canvas(); d = ImageDraw.Draw(f)
    poly(d, [(0.10, 0.84), (0.42, 0.24), (0.74, 0.84)])                # a tent
    rect(d, 0.405, 0.16, 0.435, 0.30)
    poly(d, [(0.70, 0.86), (0.80, 0.56), (0.86, 0.68), (0.92, 0.50), (0.96, 0.86)])   # its fire
    return finish(cut(f, lambda m: m.polygon([(0.34 * S, 0.84 * S), (0.42 * S, 0.54 * S), (0.50 * S, 0.84 * S)], fill=255)))


def spawn():
    # three claw slashes, tapered at both ends
    out = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    for k in range(3):
        f = canvas(); d = ImageDraw.Draw(f); o = (k - 1) * 0.22
        poly(d, [(0.30 + o, 0.10), (0.37 + o, 0.16), (0.78 + o * 0.6, 0.86), (0.72 + o * 0.6, 0.90), (0.62 + o * 0.6, 0.78)])
        out.alpha_composite(finish(f))
    return out


def ruins():
    f = canvas(); d = ImageDraw.Draw(f)
    rect(d, 0.16, 0.30, 0.32, 0.86); rect(d, 0.12, 0.24, 0.36, 0.31)   # a column
    poly(d, [(0.48, 0.86), (0.48, 0.48), (0.55, 0.42), (0.60, 0.50), (0.64, 0.46), (0.64, 0.86)])   # a broken one
    poly(d, [(0.62, 0.86), (0.92, 0.78), (0.94, 0.86)])                 # its fallen piece
    rect(d, 0.08, 0.86, 0.94, 0.92)
    return finish(f)


def ritual():
    f = canvas(); d = ImageDraw.Draw(f)
    for x, h in ((0.14, 0.50), (0.38, 0.70), (0.62, 0.70), (0.86, 0.50)):
        d.rounded_rectangle([(x - 0.08) * S, (0.88 - h) * S, (x + 0.08) * S, 0.88 * S], radius=int(0.06 * S), fill=IVORY)
    rect(d, 0.28, 0.16, 0.72, 0.23)                                     # a lintel over the middle pair
    return finish(f)


def cave():
    f = canvas(); d = ImageDraw.Draw(f)
    poly(d, [(0.04, 0.88), (0.20, 0.46), (0.36, 0.38), (0.52, 0.16), (0.70, 0.30), (0.84, 0.44), (0.96, 0.88)])
    return finish(cut(f, lambda m: m.chord([0.32 * S, 0.50 * S, 0.68 * S, 1.24 * S], 180, 360, fill=255)))


def lair():
    f = canvas(); d = ImageDraw.Draw(f)
    ell(d, 0.24, 0.26, 0.76, 0.74)                                      # a skull
    rect(d, 0.34, 0.62, 0.66, 0.84)
    poly(d, [(0.26, 0.40), (0.04, 0.10), (0.36, 0.30)]); poly(d, [(0.74, 0.40), (0.96, 0.10), (0.64, 0.30)])   # its horns
    f = cut(f, lambda m: (m.ellipse([0.32 * S, 0.40 * S, 0.46 * S, 0.54 * S], fill=255), m.ellipse([0.54 * S, 0.40 * S, 0.68 * S, 0.54 * S], fill=255),
                          [m.rectangle([(0.37 + k * 0.09) * S, 0.72 * S, (0.41 + k * 0.09) * S, 0.84 * S], fill=255) for k in range(3)]))
    return finish(f)


def select():
    f = canvas(); d = ImageDraw.Draw(f)
    d.ellipse([0.08 * S, 0.08 * S, 0.92 * S, 0.92 * S], outline=(250, 214, 120, 255), width=int(0.06 * S))
    return f.filter(ImageFilter.GaussianBlur(4)).resize((256, 256), Image.LANCZOS)


def fog():
    # a tiling cloud: a few octaves of smoothed noise, wrapped
    rng = np.random.default_rng(20261103); n = 512; acc = np.zeros((n, n))
    for o, amp in ((8, 1.0), (16, 0.5), (32, 0.25), (64, 0.12)):
        g = rng.random((o, o)); im = Image.fromarray((g * 255).astype(np.uint8)).resize((n, n), Image.BICUBIC)
        acc += amp * (np.array(im) / 255.0)
    acc = (acc - acc.min()) / (acc.max() - acc.min())
    rgb = np.stack([200 + acc * 40, 192 + acc * 38, 172 + acc * 34, 255 * np.ones_like(acc)], -1).clip(0, 255).astype(np.uint8)
    return Image.fromarray(rgb)


if __name__ == "__main__":
    out = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "wild_symbols")
    os.makedirs(out, exist_ok=True)
    for name, fn in (("town", town), ("city", city), ("village", village), ("house", house), ("camp", camp), ("spawn", spawn), ("ruins", ruins),
                     ("ritual", ritual), ("cave", cave), ("lair", lair), ("farmstead", farmstead), ("select", select), ("fog", fog)):
        fn().save(os.path.join(out, f"wmap_{name}.png"))
    # a contact sheet to look at
    names = ["town", "city", "village", "house", "camp", "spawn", "ruins", "ritual", "cave", "lair", "farmstead"]
    sheet = Image.new("RGBA", (256 * 5, 256 * 3), (120, 126, 110, 255))
    for i, n in enumerate(names): sheet.alpha_composite(Image.open(os.path.join(out, f"wmap_{n}.png")), ((i % 5) * 256, (i // 5) * 256))
    sheet.save(os.path.join(out, "_sheet.png"))
    print("WILDSYM", out, len(names) + 2)
