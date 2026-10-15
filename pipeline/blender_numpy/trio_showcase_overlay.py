"""Tripo trio showcase: titles and captions over the Movie Render Queue frames of LS_Tripo_Trio_Showcase, from 660's plan
(SourceArt/tripo_trio/plan.json): the reel's title over the opening shot, then for each character her name and what is
shown (the turntable; her attacks or her spells), the music named in a corner, and the closing title.
Optionally writes the sound track too: the first seconds of a music file, faded in and out (a 16 bit WAV).
Usage: trio_showcase_overlay.py frames_dir out_dir [music.wav out_track.wav]"""
import sys, os, json, glob, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
src, dst = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
PLAN = json.load(open(os.path.join(HERE, "..", "..", "claude_ue5", "SourceArt", "tripo_trio", "plan.json")))
FPS = PLAN["fps"]; W, H, K = 1920, 1080, 2
F = r"C:\Windows\Fonts"
def font(name, size):
    for n in (name, "segoeui.ttf", "arial.ttf"):
        try: return ImageFont.truetype(os.path.join(F, n), int(size * K))
        except OSError: pass
    return ImageFont.load_default()
f_title, f_sub, f_head, f_line, f_note = font("segoeuib.ttf", 46), font("segoeui.ttf", 26), font("seguisb.ttf", 32), font("segoeui.ttf", 24), font("seguisym.ttf", 22)
MUSIC = "Epic Fantasy Music Pack, track 6 (Battle Action)"
def fade(t, t0, t1, fin=0.4, fout=0.5):
    if t < t0 or t > t1: return 0.0
    return min(1.0, (t - t0) / fin, (t1 - t) / fout)
def overlay(f):
    t = f / FPS; o = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0)); d = ImageDraw.Draw(o, "RGBA")
    a = fade(t, 0.3, 3.0, 0.5, 0.5)
    if a > 0:
        d.text((W * K / 2, 120 * K), "THREE TRIPO CHARACTERS", font=f_title, fill=(255, 255, 255, int(240 * a)), anchor="mm", stroke_width=2 * K, stroke_fill=(0, 0, 0, int(140 * a)))
        d.text((W * K / 2, 178 * K), "jrpg-fem5-tripo  \u00b7  girl-caster-tripo  \u00b7  girl-darkcaster-tripo  \u00b7  turntable, attacks and magic in Unreal Engine 5.8",
               font=f_sub, fill=(236, 240, 244, int(230 * a)), anchor="mm", stroke_width=2 * K, stroke_fill=(0, 0, 0, int(140 * a)))
    for c in PLAN["captions"]:
        k = fade(t, c["t0"], c["t1"])
        if k <= 0: continue
        lines = c["lines"]; y = (H - 70 - 36 - 34 * len(lines)) * K
        wd = max([d.textlength(c["head"], font=f_head)] + [d.textlength(s, font=f_line) for s in lines])
        d.rounded_rectangle((32 * K, y - 14 * K, 64 * K + wd, (H - 52) * K), 12 * K, fill=(12, 11, 9, int(175 * k)))
        d.text((50 * K, y - 4 * K), c["head"], font=f_head, fill=(255, 226, 150, int(255 * k)))
        for i, s in enumerate(lines): d.text((54 * K, y + (44 + 34 * i) * K), s, font=f_line, fill=(240, 244, 248, int(240 * k)))
    m = fade(t, 1.0, 59.5, 0.8, 0.8)
    if m > 0:
        s = "\u266b  " + MUSIC; tw = d.textlength(s, font=f_note)
        d.text(((W - 36) * K - tw, 34 * K), s, font=f_note, fill=(230, 234, 240, int(200 * m)), stroke_width=K, stroke_fill=(0, 0, 0, int(120 * m)))
    if t < 0.4: d.rectangle((0, 0, W * K, H * K), fill=(0, 0, 0, int(255 * max(0.0, 1.0 - t / 0.4))))
    if t > 59.2: d.rectangle((0, 0, W * K, H * K), fill=(0, 0, 0, int(255 * min(1.0, (t - 59.2) / 0.8))))
    return o.resize((W, H), Image.LANCZOS)
os.makedirs(dst, exist_ok=True)
frames = sorted(glob.glob(os.path.join(src, "*.png")))
for i, p in enumerate(frames):
    im = Image.open(p).convert("RGBA")
    if im.size != (W, H): im = im.resize((W, H), Image.LANCZOS)
    Image.alpha_composite(im, overlay(i)).convert("RGB").save(os.path.join(dst, f"triohud.{i:04d}.png"), compress_level=1)
print("wrote", len(frames), "frames to", dst)
if len(sys.argv) > 4:
    with wave.open(sys.argv[3], "rb") as r:
        ch, sw, sr = r.getnchannels(), r.getsampwidth(), r.getframerate(); x = np.frombuffer(r.readframes(r.getnframes()), dtype="<i2").reshape(-1, ch).astype(np.float64)
    n = int(PLAN["seconds"] * sr); x = x[:n]
    if len(x) < n: x = np.vstack([x, np.zeros((n - len(x), ch))])
    fi, fo = int(0.6 * sr), int(2.5 * sr)
    x[:fi] *= np.linspace(0, 1, fi)[:, None]; x[-fo:] *= (np.cos(np.linspace(0, np.pi, fo)) * 0.5 + 0.5)[:, None]
    with wave.open(sys.argv[4], "wb") as w_:
        w_.setnchannels(ch); w_.setsampwidth(2); w_.setframerate(sr); w_.writeframes(np.clip(x, -32768, 32767).astype("<i2").tobytes())
    print("track", sys.argv[4], "%.1f s" % (n / sr))
