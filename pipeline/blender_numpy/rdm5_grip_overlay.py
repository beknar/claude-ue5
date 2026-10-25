"""random_dungeonmagic_level5's two-handed grip close up (815's way "grip", the Warrior with the Plate Knight's Sword): the
captions over the Movie Render Queue's frames, from the pilot's record (SourceArt/random_dungeon_magic5/cine_grip_<hero>.json):
the title for the first seconds, then for each cut its clip, what it is and the speed it plays at (full, or a third: her
own time dilation). Lettering: level 4's painted interface's (Cinzel for the heads, Alegreya for the text), Segoe UI
without it.
Usage (a Python with Pillow): rdm5_grip_overlay.py <frames_dir> <out_dir> [hero]"""
import sys, os, glob, json
from PIL import Image, ImageDraw, ImageFont
src, dst = sys.argv[1], sys.argv[2]
HERO = sys.argv[3] if len(sys.argv) > 3 else "Warrior"
HERE = os.path.dirname(os.path.abspath(__file__)); SA = os.path.join(HERE, "..", "..", "claude_ue5", "SourceArt")
R = json.load(open(os.path.join(SA, "random_dungeon_magic5", f"cine_grip_{HERO.lower()}.json"), encoding="utf-8"))
FPS = R["fps"]; CUTS = [e for e in R["events"] if e["kind"] == "cut" and e.get("clip")]
W, H = 1920, 1080
FD = os.path.join(SA, "random_dungeon_magic4", "fonts")
def font(name, size, fallback):
    for p in (os.path.join(FD, name + ".ttf"), os.path.join(r"C:\Windows\Fonts", fallback)):
        try: return ImageFont.truetype(p, size)
        except OSError: pass
    return ImageFont.load_default()
f_title, f_head, f_line = font("Cinzel-700", 46, "segoeuib.ttf"), font("Cinzel-700", 30, "segoeuib.ttf"), font("Alegreya-500", 27, "segoeui.ttf")
NAMES = {"1": "the diagonal cut", "2": "the overhead chop", "3": "the horizontal sweep"}
# (what each is, as the frames show it: the chop is raised to her forehead (16 cm above the base of her neck), not above
# her head: with her short arms the forearms would hang in front of her face)
WHAT = {"1": "from over her right shoulder, down across to her left", "2": "raised over her head, elbows out, brought down in front of her",
        "3": "from her right side round to her left, her waist turning with it"}
def fade(t, t0, t1, a=0.25, b=0.35): return max(0.0, min(1.0, (t - t0) / a, (t1 - t) / b))
def caption(f):
    t = f / FPS; o = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(o)
    k = fade(t, 0.2, 3.4)
    if k > 0:
        d.text((44, 36), "random_dungeonmagic_level5", font=f_title, fill=(255, 255, 255, int(235 * k)), stroke_width=2, stroke_fill=(0, 0, 0, int(140 * k)))
        d.text((46, 96), "the %s's two-handed grip, close up: the Plate Knight's Sword" % HERO.lower(), font=f_line, fill=(236, 238, 242, int(230 * k)),
               stroke_width=2, stroke_fill=(0, 0, 0, int(140 * k)))
    for i, e in enumerate(CUTS):
        t0 = e["frame"] / FPS; t1 = (CUTS[i + 1]["frame"] / FPS - 0.05) if i + 1 < len(CUTS) else t0 + 6.0
        k = fade(t, t0 - 0.1, t1)
        if k <= 0: continue
        n = e["clip"][-1]; slow = e.get("speed", 1.0) < 0.9
        head = "%s  ·  %s" % (NAMES.get(n, e["clip"]).upper(), "A THIRD OF THE SPEED" if slow else "FULL SPEED")
        lines = [WHAT.get(n, e.get("what", "")), "both fists on the hilt, a fist apart; the hands below the blade, the blade rising out of the fists"]
        wd = max([d.textlength(head, font=f_head)] + [d.textlength(s, font=f_line) for s in lines])
        y = H - 64 - 36 - 36 * len(lines)
        d.rounded_rectangle((32, y - 16, 64 + wd, H - 48), 12, fill=(12, 11, 9, int(185 * k)))
        d.text((50, y - 6), head, font=f_head, fill=(255, 226, 150, int(255 * k)))
        for j, s in enumerate(lines): d.text((54, y + 42 + 36 * j), s, font=f_line, fill=(240, 244, 248, int(240 * k)))
    if t < 0.4: d.rectangle((0, 0, W, H), fill=(0, 0, 0, int(255 * max(0.0, 1.0 - t / 0.4))))
    return o
os.makedirs(dst, exist_ok=True)
frames = sorted(glob.glob(os.path.join(src, "*.png")))
for i, p in enumerate(frames):
    im = Image.open(p).convert("RGBA")
    if im.size != (W, H): im = im.resize((W, H), Image.LANCZOS)
    Image.alpha_composite(im, caption(i)).convert("RGB").save(os.path.join(dst, "grip.%04d.png" % i), compress_level=1)
print("wrote", len(frames), "frames to", dst, "|", len(CUTS), "cuts:", ", ".join("%s at %.1f s (%s)" % (e["clip"], e["frame"] / FPS, e.get("speed")) for e in CUTS))
