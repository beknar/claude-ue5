"""Per-pixel masks from the Meshy base color: R = skin, G = cloth (fuzz), B = dark hair/nylon.
Usage: meshy_masks.py texture_0.png out.png"""
import sys, numpy as np
from PIL import Image, ImageFilter
a = np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(np.float32) / 255
r, g, b = a[..., 0], a[..., 1], a[..., 2]
mx, mn = a.max(-1), a.min(-1); v = mx; s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
hue = np.zeros_like(v)
d = np.maximum(mx - mn, 1e-6)
hue = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
skin = (v > 0.55) & (s > 0.06) & (s < 0.42) & ((hue < 40) | (hue > 340)) & (r > b + 0.04)
dark = (v < 0.22)
cloth = ~skin & ~dark & (v > 0.05)
def soft(m, rad):
    return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(rad))).astype(np.float32) / 255
out = np.stack([soft(skin, 2.0), soft(cloth, 1.5), soft(dark, 1.5)], -1)
Image.fromarray((out * 255 + 0.5).astype(np.uint8)).save(sys.argv[2])
print("skin %.1f%% cloth %.1f%% dark %.1f%%" % (100 * skin.mean(), 100 * cloth.mean(), 100 * dark.mean()))
