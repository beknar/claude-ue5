"""random_dungeonmagic_level5's face reel (30 s): the captions over the render of LS_RDM5_Faces (pipeline/unreal/836), and
its sound. Each caption (SourceArt/summoner/reel_plan.json, written by 835: an expression's name, what shows it in play,
what makes it) is drawn in the lower left in the level 4 lettering (Cinzel for the name, Alegreya for the lines;
rdm4_fonts.py's files), on a dark box, fading in and out; the reel fades in from black and out to it. The sound: a music
track from the library (chosen by its name, "Emotional Main Theme": nobody here hears it), from its start for the reel's
length, levelled to an RMS of 0.1 with half a second in and two seconds out. The second face reel (841, her MetaHuman
face) passes its own plan: reel_plan_mh.json.
Usage: rdm5_face_reel.py <frames_dir> <out_dir> <music.wav> <out_track.wav> [plan.json]"""
import sys, os, glob, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
SRC, OUT, MUSIC, TRACK = sys.argv[1:5]
HERE = os.path.dirname(os.path.abspath(__file__))
SA = os.path.join(HERE, "..", "..", "claude_ue5", "SourceArt")
P = json.load(open(sys.argv[5] if len(sys.argv) > 5 else os.path.join(SA, "summoner", "reel_plan.json")))
FD = os.path.join(SA, "random_dungeon_magic4", "fonts")
FPS = P["fps"]; W, H, K = 1920, 1080, 2
f_head = ImageFont.truetype(os.path.join(FD, "Cinzel-700.ttf"), 40 * K)
f_line = ImageFont.truetype(os.path.join(FD, "Alegreya-500.ttf"), 27 * K)
def fade(t, t0, t1, fin=0.35, fout=0.45):
    if t < t0 or t > t1: return 0.0
    return min(1.0, (t - t0) / fin, (t1 - t) / fout)
def overlay(f):
    t = f / FPS
    o = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0)); d = ImageDraw.Draw(o, "RGBA")
    for c in P["captions"]:
        k = fade(t, c["t0"], c["t1"])
        if k <= 0: continue
        lines = c["lines"]; y = (H - 70 - 40 * len(lines) - 48) * K
        wd = max([d.textlength(c["head"], font=f_head)] + [d.textlength(s, font=f_line) for s in lines])
        box = Image.new("RGBA", o.size, (0, 0, 0, 0)); ImageDraw.Draw(box).rounded_rectangle((40 * K, y - 18 * K, 76 * K + wd, (H - 52) * K), 14 * K, fill=(10, 9, 12, int(170 * k)))
        o.alpha_composite(box); d = ImageDraw.Draw(o, "RGBA")
        d.text((58 * K, y - 4 * K), c["head"], font=f_head, fill=(255, 226, 160, int(255 * k)))
        for i, s in enumerate(lines): d.text((60 * K, y + (54 + 40 * i) * K), s, font=f_line, fill=(240, 238, 246, int(240 * k)))
    # (in from black, out to black)
    edge = min(t / 0.5, (P["seconds"] - t) / 0.8)
    if edge < 1.0: d.rectangle((0, 0, W * K, H * K), fill=(0, 0, 0, int(255 * (1.0 - max(0.0, edge)))))
    return o.resize((W, H), Image.LANCZOS)
os.makedirs(OUT, exist_ok=True)
frames = sorted(glob.glob(os.path.join(SRC, "*.png")))
for i, p in enumerate(frames):
    im = Image.open(p).convert("RGBA")
    if im.size != (W, H): im = im.resize((W, H), Image.LANCZOS)
    Image.alpha_composite(im, overlay(i)).convert("RGB").save(os.path.join(OUT, f"faces.{i:04d}.png"), compress_level=1)
# ---- the sound
sr, x = wavfile.read(MUSIC)
x = x.astype(np.float32) / (32768.0 if x.dtype == np.int16 else (2 ** 31 if x.dtype == np.int32 else 1.0))
if x.ndim == 1: x = np.stack([x, x], 1)
n = int(P["seconds"] * sr); x = x[:n]
if len(x) < n: x = np.concatenate([x, np.zeros((n - len(x), 2), np.float32)])
x *= 0.1 / max(float(np.sqrt((x ** 2).mean())), 1e-6)
env = np.ones(n, np.float32); a = int(0.5 * sr); b = int(2.0 * sr)
env[:a] = np.linspace(0, 1, a); env[-b:] = np.linspace(1, 0, b); x *= env[:, None]
x = np.clip(x, -0.98, 0.98)
wavfile.write(TRACK, sr, (x * 32767).astype(np.int16))
print("wrote", len(frames), "frames to", OUT, "| track", TRACK, round(n / sr, 2), "s, peak", round(float(np.abs(x).max()), 3))
