"""random_dungeonmagic_level4's lettering: fetches its three Google Fonts (SIL Open Font License) as static TrueType files.

    rdm4_fonts.py [out_dir]     (default claude_ue5/SourceArt/random_dungeon_magic4/fonts; the files are ignored by git)

- Cinzel (Roman inscription capitals): titles, banners, hero names, weapon names, keys, numbers that stand alone;
- Alegreya (old-style serif, sturdy when small): every line of text;
- Alegreya SC (its small capitals): labels (MANA BACK, KILLS, KEY ...), drawn as "Mana Back" so the capitals stay
  full and the rest are small capitals.
The Google Fonts CSS API gives one static file per weight (the repository's files are variable fonts, which Unreal's
font cache and Pillow would draw at their default weight). Each family's licence (OFL.txt) is saved beside its files.
830 imports them for the game (UIFonts); rdm_reel_overlay.py and rdm4_reel_assemble.py draw the reel's text with them.
"""
import os, re, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "claude_ue5", "SourceArt", "random_dungeon_magic4", "fonts")
OUT = os.path.abspath(OUT)
# family -> (the repository folder of its licence, weights)
FAMILIES = {"Cinzel": ("cinzel", [400, 600, 700]),
            "Alegreya": ("alegreya", [400, 500, 700]),
            "Alegreya SC": ("alegreyasc", [500, 700])}
# (an agent without WOFF2 support: the API answers with TrueType)
UA = {"User-Agent": "Mozilla/4.0"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


os.makedirs(OUT, exist_ok=True)
for fam, (folder, weights) in FAMILIES.items():
    css = get("https://fonts.googleapis.com/css2?family=%s:wght@%s" % (fam.replace(" ", "+"), ";".join(map(str, weights)))).decode()
    blocks = re.findall(r"@font-face\s*{([^}]*)}", css)
    got = {}
    for b in blocks:
        w = int(re.search(r"font-weight:\s*(\d+)", b).group(1))
        u = re.search(r"url\((https://[^)]+)\)\s*format\('truetype'\)", b)
        if not u:
            raise SystemExit("rdm4_fonts: %s %d is not TrueType in the API's answer" % (fam, w))
        got[w] = u.group(1)
    for w in weights:
        if w not in got:
            raise SystemExit("rdm4_fonts: %s has no weight %d" % (fam, w))
        data = get(got[w])
        if data[:4] not in (b"\x00\x01\x00\x00", b"true", b"OTTO"):
            raise SystemExit("rdm4_fonts: %s %d is not a font file" % (fam, w))
        p = os.path.join(OUT, "%s-%d.ttf" % (fam.replace(" ", ""), w))
        open(p, "wb").write(data)
        print("rdm4_fonts: %-22s %7d bytes" % (os.path.basename(p), len(data)))
    lic = get("https://raw.githubusercontent.com/google/fonts/main/ofl/%s/OFL.txt" % folder)
    open(os.path.join(OUT, "OFL_%s.txt" % fam.replace(" ", "")), "wb").write(lic)
print("rdm4_fonts: done ->", OUT)
