"""The animation text of docs/heroes.md and docs/humanoid_enemies.md: what each character can play, and the animation
libraries of the project, from SourceArt/character_animations/animations.json (pipeline/unreal/902) and the Fab
library survey (asset_survey/fab_animations.csv: the clips of the downloaded packs, imported here or not)."""
import os, io, re, csv, json, collections
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DATA = os.path.join(ROOT, "claude_ue5", "SourceArt", "character_animations", "animations.json")
CSV = os.path.join(ROOT, "asset_survey", "fab_animations.csv")
ASSETS = os.path.join(ROOT, "docs", "assets.md")
KINDS = [("attacks", r"attack|punch|kick|slash|strike|combo|stab|swing|bite|boom|shot|shoot|fire"),
         ("deaths", r"dead|death|die"),
         ("hit reactions", r"hit|react|damage"),
         ("idles", r"idle"),
         ("jumps and falls", r"jump|fall|land"),
         ("moves", r"walk|run|jog|sprint|strafe|turn|rotat|move|crawl|fly|flight|swim|step|_back|left|right|fwd|bwd|forward")]


def kind(clip):
    n = clip.lower()
    if n.startswith("sk_") or "all_animations" in n: return "all"
    for k, rx in KINDS:
        if re.search(rx, n): return k
    return "other"


def tidy(clip, prefix=""):
    """a clip's name without the Anim_ prefix, the pack's own word (`prefix`) and the _Anim suffix, for the 'other' examples"""
    n = re.sub(r"^(Anim_|AS_|A_|MM_|MF_)", "", clip); n = re.sub(r"_Anim$", "", n)
    if prefix and n.lower().startswith(prefix + "_"): n = n[len(prefix) + 1:]
    return n.replace("_", " ").lower()


def prefix(clips):
    """the word most of a set's clip names start with after Anim_ (Anim_Drinker_Attack_1: drinker), if most do"""
    w = collections.Counter(re.sub(r"^(Anim_|AS_|A_)", "", x).split("_")[0].lower() for x in clips)
    if not w: return ""
    t, k = w.most_common(1)[0]
    return t if k >= 0.6 * len(clips) and t not in ("attack", "idle", "walk", "run", "dead") else ""


def counts(clips):
    c = collections.Counter(kind(x) for x in clips); out = []; p = prefix(clips)
    for k, _ in KINDS + [("other", None)]:
        if c[k]: out.append("%d %s" % (c[k], k if c[k] > 1 or k in ("moves",) else {"attacks": "attack", "deaths": "death", "hit reactions": "hit reaction",
                                                                                         "idles": "idle", "jumps and falls": "jump or fall", "other": "other"}[k]))
    if c["all"]: out.append("all of them on one timeline")
    other = sorted({re.sub(r"\s+", " ", re.sub(r"\s*\d+$", "", tidy(x, p))).strip() for x in clips if kind(x) == "other"})
    s = ", ".join(out)
    if other: s += " (%s)" % ", ".join(other[:5] + (["..."] if len(other) > 5 else []))
    return s


def norm(t): return re.sub(r"[^a-z0-9]", "", re.sub(r"\(pack\)|\bpack\b", "", t.lower()))


def listings():
    """pack folder -> (listing title, uid), from docs/assets.md"""
    out = {}
    for line in io.open(ASSETS, encoding="utf-8"):
        m = re.search(r"\[((?:[^\[\]]|\[[^\]]*\])+)\]\(https://www\.fab\.com/listings/([0-9a-f-]+)\)", line)      # (a title may hold [Nanite])
        if not m: continue
        for f in re.findall(r"`([A-Za-z0-9_-]+)`", line) + re.findall(r"\| ([A-Za-z0-9_-]+) \(imported by", line): out.setdefault(f, (m.group(1), m.group(2)))
    return out


class Anims:
    def __init__(self):
        D = json.load(io.open(DATA, encoding="utf-8"))
        self.libs = D["libraries"]; self.chars = D["characters"]; self.lst = listings()
        self.cache = collections.defaultdict(list)                  # normalised pack title -> UE-mannequin clips in the Fab download
        for r in csv.DictReader(io.open(CSV, encoding="utf-8")):
            if r["rig"] == "UE Mannequin-style" and not r["models"]: self.cache[norm(r["pack"])].append(r["clip"])

    def line(self, mesh, pack):
        """the **Animations:** paragraph of one character"""
        c = self.chars.get(mesh)
        if not c: return "not surveyed"
        own = c["own"]
        if c["rig"] != "own":                       # (a pack may keep its clips on a second copy of the mannequin's skeleton)
            folder = mesh.split("/")[2]
            own = sorted(set(own) | {x for l in self.libs if l["folder"] == folder and l["rig"] == c["rig"] for x in l["clips"]})
        demo = all(re.match(r"(Anim_)?(ThirdPerson|MM_)", x) for x in own)
        if c["rig"] == "own":
            s = "a rig of its own (%d bones, not the mannequin's): its pack's %d clips only, %s. Other animations need an IK rig and the retargeter." % (c["bones"], len(own), counts(own)) if own \
                else "a rig of its own (%d bones) and no clips." % c["bones"]
            return s
        rig = "UE4-mannequin rig" if c["rig"] == "ue4" else "UE5-mannequin rig"
        if own and not demo: s = "%s; its pack's own %d clips: %s." % (rig, len(own), counts(own))
        elif own: s = "%s; of its own only the template's idle, walk, run and jump that came with the pack." % rig
        else: s = "%s; no clips of its own." % rig
        cache = self.cache.get(norm(pack), [])
        if cache and not any(kind(x) == "attacks" for x in own) and any(kind(x) == "attacks" for x in cache):
            s += " The Fab download has %d more clips for it that are not imported here: %s." % (len(cache), counts(cache))
        if c["rig"] == "ue4": s += " Plays every UE4-mannequin library below as it is."
        else: s += " Plays the UE5 mannequin's clips as they are and the UE4 libraries through the retargeter."
        return s

    def section(self, level="##"):
        """the Animations section: the libraries that UE4-mannequin characters share, grouped by pack"""
        seen = {}; rows = []; demo = {"ue4": set(), "ue5": set()}
        for l in self.libs:
            if l["rig"] == "own" or FIRST_PERSON.match(l["folder"]) or not l["skeleton"].startswith("/Game/"): continue     # (not a plugin's MetaHuman)
            clips = [x for x in l["clips"] if not CONTROL.match(x)]
            if all(DEMO.match(x) for x in clips): demo[l["rig"]].add(l["folder"]); continue
            key = (l["rig"], tuple(clips))
            if key in seen: seen[key].append(l["folder"]); continue
            seen[key] = [l["folder"]]; rows.append((dict(l, clips=clips), seen[key]))
        out = ["%s Animations\n\n" % level,
               "Each entry says which rig the character has and which clips come with it. Most of these characters share the **UE4 mannequin's bone names** "
               "(pelvis, spine_01..03, neck_01, head, the arm and leg chains) and the mannequin's bone axes, so a clip made for one plays on all of them as it is "
               "(the action poses on these pages were made that way). The UE5 mannequin's clips (Manny and Quinn) play on them through the IK retargeter, and a "
               "rig of its own (3ds Max CAT, Maya AdvancedSkeleton, a custom one) plays its own clips only.\n\n",
               "The UE4-mannequin libraries in the project (the same set that came with several packs is listed once):\n\n",
               "| Library | Pack folder | Clips | What is in it |\n|---|---|---|---|\n"]
        for rig in ("ue4", "ue5"):
            for l, folders in sorted([r for r in rows if r[0]["rig"] == rig], key=lambda r: -len(r[0]["clips"])):
                if len(l["clips"]) < 3: continue
                f0 = sorted(folders, key=lambda f: ("Animations" not in f, f))[0]       # (an animation pack names the set before a character pack)
                t = self.lst.get(f0)
                name = "[%s](https://www.fab.com/listings/%s)" % t if t else NAMES.get(f0, f0.replace("_", " "))
                if rig == "ue5": name += " (UE5 mannequin: retargeted)"
                fl = "`%s`" % f0 + (" and %d more" % (len(folders) - 1) if len(folders) > 1 else "")
                out.append("| %s | %s | %d | %s |\n" % (name, fl, len(l["clips"]), counts(l["clips"])))
            if demo[rig]:
                out.append("| the %s template's demo set (idle, walk, run, jump) | %d packs | 3 to 7 | in nearly every character pack%s |\n" %
                           ("Third Person (UE4)" if rig == "ue4" else "UE5 mannequin", len(demo[rig]), "" if rig == "ue4" else "; retargeted"))
        out.append("\nLeft out: the first-person packs (arms only: `FPS_*`, `Sci_Fi_Hands*`, `Automatic_Gun`), whose clips move a camera rig's arms, not a body.\n")
        return "".join(out)


NAMES = {"Characters": "the UE5 template's mannequin clips (Manny and Quinn)", "Girl": "Girl (an NPC pack)"}
FIRST_PERSON = re.compile(r"FPS_|Sci_Fi_Hands|Automatic_Gun")
CONTROL = re.compile(r"(Anim_)?(Manny|Quinn)_\w+_Anim$|MHC_|mhc_", re.I)          # (a control rig's per-bone helper clips, a MetaHuman's face ranges)
DEMO = re.compile(r"(Anim_)?(ThirdPerson|MM_(Fall_Loop|Idle|Jump|Land|Run_Fwd|Walk_Fwd|Walk_InPlace|T_Pose)$)")
