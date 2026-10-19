"""random_dungeonmagic_level4's painted interface drawn with Pillow, the way the game's HUD draws it (C++
FRDUIDraw in Source/claude_ue5/RD/RDUIArt.cpp): the reel overlay draws the HUD over the rendered frames with
it, and rdm4_ui_cut.py's previews use it.

    ui = UIArt(export_dir)            # rdm4_ui_cut.py --export's pictures and layout.json
    ui.nine(img, "panel_wide", (x0, y0), (x1, y1), px)      # stretched, its border at px screen px a picture px
    ui.fit(img, "w_crossbow", (x0, y0), (x1, y1))           # fitted without changing its shape
    ui.bar(img, "bar_health", "fill_health", a, b, px, 0.6) # a frame with its fill inside up to 60 %

`img` is an RGBA Image drawn on in place (each piece composited over it). A tint multiplies the piece's
colour (values over 1 brighten) and its alpha (the fourth value).
"""
import json, os
import numpy as np
from PIL import Image


class UIArt:
    def __init__(self, export_dir):
        self.L = json.load(open(os.path.join(export_dir, "layout.json")))
        self.img = {}
        for n, e in self.L.items():
            if n.startswith("_"):
                continue
            p = os.path.join(export_dir, n + ".png")
            if os.path.exists(p):
                self.img[n] = Image.open(p).convert("RGBA")
        self.icons = self.L.get("_icons", {})
        self.weapons = self.L.get("_weapons", {})

    def has(self, n):
        return n in self.img

    @staticmethod
    def _tinted(im, tint):
        if tint is None or tuple(tint) == (1, 1, 1, 1):
            return im
        a = np.asarray(im).astype(np.float32)
        t = list(tint) + [1.0] * (4 - len(tint))
        a[..., :3] = np.clip(a[..., :3] * np.array(t[:3], np.float32), 0, 255)
        a[..., 3] *= t[3]
        return Image.fromarray(a.astype(np.uint8))

    def _tile(self, canvas, im, x, y, w, h, box, tint):
        # box: (u0, v0, u1, v1) in the picture's pixels; drawn to (x, y, w, h) on the canvas
        if w < 1 or h < 1:
            return
        u0, v0, u1, v1 = box
        flip = u1 < u0
        if flip:
            u0, u1 = u1, u0
        if u1 - u0 < 1 or v1 - v0 < 1:
            return
        piece = im.crop((int(round(u0)), int(round(v0)), int(round(u1)), int(round(v1))))
        if flip:
            piece = piece.transpose(Image.FLIP_LEFT_RIGHT)
        piece = piece.resize((max(1, int(round(w))), max(1, int(round(h)))), Image.LANCZOS)
        piece = self._tinted(piece, tint)
        x, y = int(round(x)), int(round(y))
        # (clipped to the canvas)
        cx0, cy0 = max(0, -x), max(0, -y)
        cx1, cy1 = min(piece.width, canvas.width - x), min(piece.height, canvas.height - y)
        if cx1 <= cx0 or cy1 <= cy0:
            return
        piece = piece.crop((cx0, cy0, cx1, cy1))
        canvas.alpha_composite(piece, (x + cx0, y + cy0))

    def _sizes(self, n, a, b, px):
        im, bd = self.img[n], self.L[n]["border"]
        tw, th = im.size
        l, t, r, bo = bd[0] * tw * px, bd[1] * th * px, bd[2] * tw * px, bd[3] * th * px
        w, h = b[0] - a[0], b[1] - a[1]
        if l + r > w * 0.98 and l + r > 0:
            k = w * 0.98 / (l + r); l *= k; r *= k
        if t + bo > h * 0.98 and t + bo > 0:
            k = h * 0.98 / (t + bo); t *= k; bo *= k
        return l, t, r, bo

    def nine(self, canvas, n, a, b, px, tint=None):
        if n not in self.img or b[0] <= a[0] or b[1] <= a[1]:
            return False
        im, bd = self.img[n], self.L[n]["border"]
        tw, th = im.size
        l, t, r, bo = self._sizes(n, a, b, px)
        xs = [a[0], a[0] + l, b[0] - r, b[0]]
        ys = [a[1], a[1] + t, b[1] - bo, b[1]]
        us = [0, bd[0] * tw, (1 - bd[2]) * tw, tw]
        vs = [0, bd[1] * th, (1 - bd[3]) * th, th]
        for j in range(3):
            for i in range(3):
                self._tile(canvas, im, xs[i], ys[j], xs[i + 1] - xs[i], ys[j + 1] - ys[j], (us[i], vs[j], us[i + 1], vs[j + 1]), tint)
        return True

    def fit_box(self, n, a, b):
        tw, th = self.img[n].size
        k = min((b[0] - a[0]) / max(tw, 1), (b[1] - a[1]) / max(th, 1))
        cx, cy = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        return (cx - tw * k / 2, cy - th * k / 2), (cx + tw * k / 2, cy + th * k / 2)

    def fit(self, canvas, n, a, b, tint=None, flip=False):
        if n not in self.img:
            return False
        (x0, y0), (x1, y1) = self.fit_box(n, a, b)
        tw, th = self.img[n].size
        self._tile(canvas, self.img[n], x0, y0, x1 - x0, y1 - y0, (tw, 0, 0, th) if flip else (0, 0, tw, th), tint)
        return True

    def inner_box(self, n, a, b, px):
        if n not in self.img:
            return a, b
        l, t, r, bo = self._sizes(n, a, b, px)
        bd, inn = self.L[n]["border"], self.L[n]["inner"]

        def m(s, s0, s1, p0, p1, n0, n1):
            if s <= s0:
                return p0 + (s / s0 if s0 > 0 else 0) * n0
            if s >= 1 - s1:
                return p1 - ((1 - s) / s1 if s1 > 0 else 0) * n1
            mid = 1 - s0 - s1
            return (p0 + n0) + ((s - s0) / mid if mid > 0 else 0) * ((p1 - n1) - (p0 + n0))
        return ((m(inn[0], bd[0], bd[2], a[0], b[0], l, r), m(inn[1], bd[1], bd[3], a[1], b[1], t, bo)),
                (m(inn[2], bd[0], bd[2], a[0], b[0], l, r), m(inn[3], bd[1], bd[3], a[1], b[1], t, bo)))

    def bar(self, canvas, frame, fill, a, b, px, frac, fill_tint=None, frame_tint=None):
        if frame not in self.img:
            return False
        (x0, y0), (x1, y1) = self.inner_box(frame, a, b, px)
        dark = Image.new("RGBA", (max(1, int(x1 - x0)), max(1, int(y1 - y0))), (4, 3, 3, 235))
        canvas.alpha_composite(dark, (int(x0), int(y0)))
        f = min(max(frac, 0.0), 1.0)
        if fill in self.img and f > 0:
            fw, fh = self.img[fill].size
            self._tile(canvas, self.img[fill], x0, y0, (x1 - x0) * f, y1 - y0, (0, 0, fw * f, fh), fill_tint)
        return self.nine(canvas, frame, a, b, px, frame_tint)

    def height_px(self, n, h):
        return h / max(self.img[n].size[1], 1) if n in self.img else 0

    def board(self, canvas, n, a, b, ext, tint=None):
        """a panel's board reaching ext beyond a..b, its frame 1.6 ext thick (ARDHUD::Board)"""
        if n not in self.img:
            return False
        fp = max(self.L[n]["border"][0] * self.img[n].size[0], 1)
        return self.nine(canvas, n, (a[0] - ext, a[1] - ext), (b[0] + ext, b[1] + ext), ext * 1.6 / fp, tint)

    def strip(self, canvas, n, a, b, tint=None):
        """stretched along a..b at the box's height, its ends kept (ARDHUD::Strip)"""
        return self.nine(canvas, n, a, b, self.height_px(n, b[1] - a[1]), tint)
