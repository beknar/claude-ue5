"""random_dungeonmagic_level5's sword close up (815's way "grip", the Warrior or the Warlock with the Plate Knight's Sword;
wielded as her one-handed sword with no shield, or with the older two-handed cuts): the
captions over the Movie Render Queue's frames, from the pilot's record (SourceArt/random_dungeon_magic5/cine_grip_<hero>.json):
the title for the first seconds, then for each cut its clip, what it is and the speed it plays at (full, or a third: her
own time dilation). Lettering: level 4's painted interface's (Cinzel for the heads, Alegreya for the text), Segoe UI
without it.
The hero "Warrior2": the chop test of ai models/Warrior2.glb (815's way "chop2", record cine_chop2_warrior2.json): her own
chop, the whole clip at its own speed and its swing at a third.
Usage (a Python with Pillow): rdm5_grip_overlay.py <frames_dir> <out_dir> [hero]"""
import sys, os, glob, json
from PIL import Image, ImageDraw, ImageFont
src, dst = sys.argv[1], sys.argv[2]
HERO = sys.argv[3] if len(sys.argv) > 3 else "Warrior"
HERE = os.path.dirname(os.path.abspath(__file__)); SA = os.path.join(HERE, "..", "..", "claude_ue5", "SourceArt")
W2 = HERO == "Warrior2"
R = json.load(open(os.path.join(SA, "random_dungeon_magic5", "cine_chop2_warrior2.json" if W2 else f"cine_grip_{HERO.lower()}.json"), encoding="utf-8"))
FPS = R["fps"]; CUTS = [e for e in R["events"] if e["kind"] == "cut" and e.get("clip")]
W, H = 1920, 1080
FD = os.path.join(SA, "random_dungeon_magic4", "fonts")
def font(name, size, fallback):
    for p in (os.path.join(FD, name + ".ttf"), os.path.join(r"C:\Windows\Fonts", fallback)):
        try: return ImageFont.truetype(p, size)
        except OSError: pass
    return ImageFont.load_default()
f_title, f_head, f_line = font("Cinzel-700", 46, "segoeuib.ttf"), font("Cinzel-700", 30, "segoeuib.ttf"), font("Alegreya-500", 27, "segoeui.ttf")
# (each clip: its name and what it is, as the rendered frames show it. Level 5 wields a two-handed sword with her
# one-handed sword's clips and nothing in the other hand; the W5_TwoHand cuts' words stay for the older reels)
CLIPS = {
    "Anim_Weapon_Shield_Attack_01_Fem5": ("the high cut", "raised high over her right shoulder, brought down in front of her as she leans into it"),
    "Anim_Weapon_Shield_Attack_03_Fem5": ("the low lunge", "she stoops forward into a lunge, the blade swept low in front of her, then rises"),
    "Anim_Weapon_Shield_Attack_08_Fem5": ("the round cut", "the blade swung flat round over her head, then down across to her left"),
    "AS_DarkCaster_Slash1": ("the wide slash", "the arm swung out to her right and up, then cut across in front of her, down to her left"),
    "AS_DarkCaster_Slash2": ("the falling cut", "raised high over her right shoulder, brought down past her right side"),
    "AS_DarkCaster_Slash3": ("the low sweep", "swept low from her right across to her left, then held point down in front of her"),
}
TWO_HAND = {"1": ("the diagonal cut", "from over her right shoulder, down across to her left"),
            "2": ("the overhead chop", "raised over her head, elbows out, brought down in front of her"),
            "3": ("the horizontal sweep", "from her right side round to her left, her waist turning with it")}
ONE_HAND = not any("TwoHand" in e["clip"] for e in CUTS)
# (Warrior2's chop test: Tripo's clip as it is, but for its pelvis)
W2_PARTS = {"whole": ("the chop, the whole clip", "Tripo's chop as made: the sword raised over her head, brought down as she bends into it"),
            "swing": ("the chop's swing", "its frames 20 to 92: from the wind-up to standing again")}
# (Warrior3, the Warrior since 2026-10-26: her own slash for every two-handed sword)
W3 = any(e["clip"] == "AS_Warrior3_Slash" for e in CUTS)
W3_SLASH = ("the slash", "her own clip: both fists raised over her head, brought down as she bends into it, the blade ending forward")
def clip_words(e):
    if e["clip"] == "AS_Warrior3_Slash": return W3_SLASH
    if e["clip"].endswith("Warrior2_Chop"): return W2_PARTS.get(e.get("part"), ("the chop", ""))
    if e["clip"] in CLIPS: return CLIPS[e["clip"]]
    if "TwoHand" in e["clip"]: return TWO_HAND.get(e["clip"][-1], (e["clip"], e.get("what", "")))
    return (e["clip"], e.get("what", ""))
TITLE = "Warrior3, the warrior: the Plate Knight's Sword, her own two-handed slash" if W3 else "Warrior2's chop test: her own clip on her own rig, the Plate Knight's Sword" if W2 else ("the %s's Plate Knight's Sword in one hand, no shield, close up" if ONE_HAND else "the %s's two-handed grip, close up: the Plate Knight's Sword") % HERO.lower()
HOLD = "Tripo's clip in Warrior3.glb, at the weapon's speed; the sword in her right hand, the left hand where the clip puts it" if W3 else "only its pelvis set right (Tripo's clip dragged her hips to the floor); the left hand where the clip puts it" if W2 else ("the two-handed sword wielded as her one-handed sword: in her right hand alone, the left hand empty" if ONE_HAND
        else "both fists on the hilt, a fist apart; the hands below the blade, the blade rising out of the fists")
def fade(t, t0, t1, a=0.25, b=0.35): return max(0.0, min(1.0, (t - t0) / a, (t1 - t) / b))
def caption(f):
    t = f / FPS; o = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(o)
    k = fade(t, 0.2, 3.4)
    if k > 0:
        d.text((44, 36), "random_dungeonmagic_level5", font=f_title, fill=(255, 255, 255, int(235 * k)), stroke_width=2, stroke_fill=(0, 0, 0, int(140 * k)))
        d.text((46, 96), TITLE, font=f_line, fill=(236, 238, 242, int(230 * k)),
               stroke_width=2, stroke_fill=(0, 0, 0, int(140 * k)))
    for i, e in enumerate(CUTS):
        t0 = e["frame"] / FPS; t1 = (CUTS[i + 1]["frame"] / FPS - 0.05) if i + 1 < len(CUTS) else t0 + 6.0
        k = fade(t, t0 - 0.1, t1)
        if k <= 0: continue
        name, what = clip_words(e); slow = e.get("speed", 1.0) < 0.9
        head = "%s  ·  %s" % (name.upper(), ("A THIRD OF ITS SPEED" if slow else "ITS OWN SPEED") if W2 else ("A THIRD OF THE SPEED" if slow else "FULL SPEED"))
        lines = [what, HOLD]
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
