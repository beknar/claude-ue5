"""Writes docs/all3dassets.md: every 3D asset on the project owner's machine in four places, with its path and what it is.
  1. the project (E:\\code\\claude-ue5): claude_ue5/Content's folders, the pack projects opened in the repository's root,
     `ai models`, `old models` and the 3D files under claude_ue5/SourceArt
  2. I:\\game assets\\3d cgaxis models: the CGAxis volumes (read from the zips' file lists: nothing is extracted)
  3. I:\\game assets\\3d fab library data cache: the Fab downloads (VaultCache/<pack>/manifest), the library's listings
     (VaultCache/FabLibrary/<listing>/unreal-engine/manifest) and the loose zips
  4. C:\\Users\\kestanol\\AppData\\Roaming\\kitbash3d\\kits: the KitBash3D kits
Counts of skeletal meshes, static meshes, clips, effects... are by the packs' naming (SK_, SM_, A_ / an Animations folder, NS_ ...):
approximate. A pack's title, tags, store link and engine versions come from its own manifest; a download's binary manifest
has none of them, and they come from its listing.
Run: python asset_survey/all3d_survey.py   (pdftotext on the PATH for the CGAxis interiors' descriptions; optional)"""
import os, re, json, zipfile, struct, subprocess, collections, datetime, zlib

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONTENT = os.path.join(REPO, "claude_ue5", "Content")
CG = r"I:\game assets\3d cgaxis models"
FAB = r"I:\game assets\3d fab library data cache"
VAULT = os.path.join(FAB, "VaultCache")
KB = r"C:\Users\kestanol\AppData\Roaming\kitbash3d\kits"
OUT = os.path.join(REPO, "docs", "all3dassets.md")
GB = 1024.0 ** 3

# the CGAxis volumes' titles: cgaxis.com's product pages (1-87), the complete.cgaxis.com pages (61, 66), the Complete 6-10
# catalogues in the folders (88-105: their headings, or "catalogue" where named from the order of its descriptions), the zips'
# own names (106-120). 52, 56 and 58-60 were found nowhere.
CG_TITLES = {
    1: "Plants", 2: "Bathrooms", 3: "Doors", 4: "Electronics", 5: "Trees", 6: "Flowers", 7: "Furniture", 8: "Food",
    9: "Lighting Collection", 10: "Kitchen Appliances", 11: "Office Furniture", 12: "Office Appliances", 13: "Party Collection",
    14: "Trees II (25 trees)", 15: "Exotic Plants", 16: "Lights II", 17: "Furniture (32 models)", 18: "Electronics II",
    19: "Garden Plants", 20: "Home & Kitchen Appliances", 21: "Plants II", 22: "Bathrooms", 23: "Books", 24: "Aquariums",
    25: "Furniture III", 26: "Flowers II", 27: "Bedrooms", 28: "Trees III", 29: "Food II", 30: "Street Equipment",
    31: "Music Studio", 32: "Supermarket", 33: "Kitchen Appliances II", 34: "Trees IV", 35: "Lights III", 36: "Fences",
    37: "Gadgets", 38: "Furniture IV", 39: "Christmas", 40: "Toys", 41: "Electronics III", 42: "Stairs", 43: "Books II",
    44: "Street Equipment II", 45: "Fireplaces", 46: "Windows", 47: "Blinds", 48: "Modern Furniture", 49: "Bedrooms II",
    50: "Plants III", 51: "Garden Furniture", 53: "Books III", 54: "Trees V", 55: "Medical", 57: "Gym Equipment",
    61: "Kitchen Appliances", 62: "Trees VI", 63: "Flowers III", 64: "Supermarket III", 65: "Gadgets II",
    66: "Garden Plants II", 67: "Trees VII", 68: "Furniture V", 69: "Trees VIII", 70: "Supermarket IV", 71: "Food V",
    72: "Trees IX", 73: "Food VI", 74: "Electronics V", 75: "Furniture VI", 76: "Trees X", 77: "Electronics VI",
    78: "Furniture VII", 79: "Doors II", 80: "Office Furniture II", 81: "Lights IV", 82: "Windows II", 83: "Decorations",
    84: "Bathrooms III", 85: "Exotic Plants II", 86: "Kitchen Furniture", 87: "Bar Equipment",
    88: "Sport Equipment (catalogue)", 89: "Hedges and Shrubs (catalogue)", 90: "Home Electronic Devices (catalogue)",
    91: "Wild Plants", 92: "Kitchen Accessories (catalogue)", 93: "Garden Furniture II (catalogue)",
    94: "Exterior Lamps (catalogue)", 95: "Fruit Trees", 96: "Kids Furniture", 97: "Leather Furniture (catalogue)",
    98: "Conifer Trees (catalogue)", 99: "Restaurant (catalogue)", 100: "Trees XI", 101: "Beauty Salon",
    102: "Reception and Waiting Room (catalogue)", 103: "Interior Decorations (catalogue)", 104: "Wall Panels",
    105: "Fruit Trees II", 106: "Furniture", 107: "Mall Equipment", 108: "Garden Decorations", 109: "Trees",
    110: "Palm Trees", 111: "Interior Plants", 112: "Supermarket Equipment", 113: "Street Equipment",
    114: "Interior Lights", 115: "Autumn Trees", 116: "Kitchen Appliances", 117: "Photo Studio Equipment",
    118: "Kiosks and Stalls", 119: "Green Energy", 120: "North American Trees",
}
KB_TITLES = {"kb3d_futureslums": "Future Slums", "kb3d_scifiindustrial": "Sci-Fi Industrial", "kb3d_sovietblocks": "Soviet Blocks"}


def md(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def gb(b):
    return f"{b / GB:.2f} GB" if b >= GB else f"{b / 1024 / 1024:.0f} MB"


# ------------------------------------------------------------------------------------------------ what a file name is
def kind_of(path):
    p = path.replace("\\", "/")
    base = p.rsplit("/", 1)[-1]
    stem, ext = (base.rsplit(".", 1) + [""])[:2]
    ext = ext.lower(); u = stem.upper(); pl = p.lower()
    if ext == "umap": return "map"
    if ext in ("fbx", "obj", "glb", "gltf", "usd", "usda", "usdc", "blend", "abc", "dae", "3ds", "max", "c4d"): return "source"
    if ext == "vdb": return "vdb"
    if ext in ("wav", "ogg", "mp3", "flac"): return "sound"
    if ext != "uasset": return None
    if u.startswith(("SK_", "SKM_", "SKEL_MESH")): return "skeletal"
    if u.startswith(("SKEL_", "SK_SKELETON")) or u.endswith("_SKELETON") or u.startswith(("PHYS_", "PA_", "ABP_", "BS_", "IK_", "RTG_", "AM_", "AO_")): return "rig"
    if u.startswith("SM_"): return "static"
    if u.startswith(("A_", "AN_", "ANIM_", "AS_", "MM_")) or ("/animation" in pl and not u.startswith(("M_", "T_", "MI_"))): return "anim"
    if u.startswith(("NS_", "P_", "NE_", "NF_", "FX_", "VFX_")): return "fx"
    if u.startswith(("MI_", "M_", "MF_", "MAT_", "MLB_")): return "material"
    if u.startswith(("T_", "TX_", "TEX_")): return "texture"
    if u.startswith(("BP_", "B_", "WBP_", "W_")): return "blueprint"
    if u.startswith(("SC_", "SW_", "SFX_", "CUE_")) or u.endswith("_CUE") or "/sound" in pl or "/audio" in pl: return "sound"
    if "/mesh" in pl or "/geometry" in pl or "/props/" in pl: return "skeletal" if "skelet" in pl or "/character" in pl else "static"
    if "/texture" in pl: return "texture"
    if "/material" in pl: return "material"
    return "other"


KINDS = [("skeletal", "skeletal meshes"), ("static", "static meshes"), ("anim", "clips"), ("fx", "effects"),
         ("vdb", "VDB volumes"), ("source", "source models (FBX/OBJ/USD)"), ("blueprint", "blueprints"),
         ("sound", "sounds"), ("map", "maps")]
ONE = {"skeletal meshes": "skeletal mesh", "static meshes": "static mesh", "clips": "clip", "effects": "effect",
       "VDB volumes": "VDB volume", "source models (FBX/OBJ/USD)": "source model (FBX/OBJ/USD)", "blueprints": "blueprint",
       "sounds": "sound", "maps": "map"}


def summary(cnt):
    parts = [f"{cnt[k]} {ONE[name] if cnt[k] == 1 else name}" for k, name in KINDS if cnt.get(k)]
    if cnt.get("material") or cnt.get("texture"): parts.append(f"{cnt.get('material', 0)} materials, {cnt.get('texture', 0)} textures")
    return ", ".join(parts) or "no assets counted"


# ------------------------------------------------------------------------------------------------ the Fab manifests
def size_of(f):
    t = 0
    for c in f.get("FileChunkParts", []):
        s = c.get("Size", "")
        t += sum(int(s[i:i + 3]) << (8 * (i // 3)) for i in range(0, len(s), 3))
    return t


class _Rd:
    def __init__(self, b): self.b = b; self.i = 0
    def u8(self): v = self.b[self.i]; self.i += 1; return v
    def u32(self): v = struct.unpack_from("<I", self.b, self.i)[0]; self.i += 4; return v
    def i32(self): v = struct.unpack_from("<i", self.b, self.i)[0]; self.i += 4; return v
    def s(self):
        n = self.i32()
        if n == 0: return ""
        if n < 0:
            v = self.b[self.i:self.i - 2 * n].decode("utf-16-le", "replace"); self.i -= 2 * n
        else:
            v = self.b[self.i:self.i + n].decode("latin-1"); self.i += n
        return v.rstrip("\x00")


def read_binary_manifest(raw):
    """the launcher's binary manifest (magic 0x44BEC00C): its header, then (zlib) the meta, the chunk list, the file list and
    the custom fields, each led by its own size. Only the app name, the files' names and sizes and the custom fields are read."""
    magic, hsize, usize, csize = struct.unpack_from("<IIII", raw, 0)
    stored = raw[36]
    body = raw[hsize:hsize + csize]
    if stored & 1: body = zlib.decompress(body)
    r = _Rd(body)
    st = r.i; msize = r.u32(); r.u8(); r.u32(); r.u8(); r.u32(); app = r.s(); r.i = st + msize
    st = r.i; csz = r.u32(); r.i = st + csz                                   # (the chunk list)
    st = r.i; fsz = r.u32(); r.u8(); count = r.u32()
    names = [r.s() for _ in range(count)]
    for _ in range(count): r.s()                                              # (symlink targets)
    r.i += 20 * count + count                                                 # (hashes, flags)
    for _ in range(count):                                                    # (install tags)
        for _ in range(r.u32()): r.s()
    sizes = []
    for _ in range(count):
        t = 0
        for _ in range(r.u32()):
            ps = r.i; psz = r.u32(); r.i += 16; r.u32(); t += r.u32(); r.i = ps + psz
        sizes.append(t)
    r.i = st + fsz
    cf = {}
    try:
        r.u32(); r.u8(); n = r.u32()
        keys = [r.s() for _ in range(n)]; vals = [r.s() for _ in range(n)]
        cf = dict(zip(keys, vals))
    except Exception:
        pass
    files = [{"Filename": a, "_size": b} for a, b in zip(names, sizes)]
    return {"AppNameString": app, "CustomFields": cf, "FileManifestList": files}


def read_manifest(path):
    try:
        with open(path, "rb") as fh: raw = fh.read()
        if raw[:4] == b"\x0c\xc0\xbe\x44": j = read_binary_manifest(raw)
        else: j = json.loads(raw.decode("utf-8", "replace"))
    except Exception as e:
        print("MANIFEST not read:", path, type(e).__name__, str(e)[:80])
        return None
    cf = j.get("CustomFields", {}) or {}
    files = j.get("FileManifestList", []) or []
    cnt = collections.Counter(); tops = collections.Counter(); size = 0
    for f in files:
        n = f.get("Filename", ""); size += f["_size"] if "_size" in f else size_of(f)
        k = kind_of(n)
        if k: cnt[k] += 1
        parts = n.replace("\\", "/").split("/")
        if len(parts) > 2 and parts[0] == "Content": tops[parts[1]] += 1
        elif len(parts) > 1 and parts[0] != "Content": tops["(" + parts[0] + ")"] += 1
    apps = [a for a in (cf.get("CompatibleApps", "") or "").split(",") if a]
    return {
        "app": j.get("AppNameString", ""),
        "title": cf.get("Vault.TitleText") or j.get("AppNameString", "?"),
        "id": cf.get("CatalogItemId", ""), "url": cf.get("Vault.ActionURL", ""),
        "tags": cf.get("Vault.Tags") or cf.get("Vault.Filters") or "", "type": cf.get("Vault.Type", ""),
        "apps": apps, "files": len(files), "size": size, "cnt": cnt,
        "tops": [t for t, _ in tops.most_common() if not t.startswith("__")],
    }


def ue_range(apps):
    v = [a.replace("UE_", "") for a in apps if a.startswith("UE_")]
    if not v: return ""
    key = lambda s: tuple(int(x) for x in re.findall(r"\d+", s))
    v.sort(key=key)
    return v[0] if len(v) == 1 else f"{v[0]}-{v[-1]}"


def fab_packs():
    down, listing = {}, {}
    for d in sorted(os.listdir(VAULT)):
        full = os.path.join(VAULT, d)
        if d == "FabLibrary" or not os.path.isdir(full): continue
        m = read_manifest(os.path.join(full, "manifest"))
        if not m: continue
        m["dir"] = full; m["downloaded"] = os.path.isdir(os.path.join(full, "data"))
        down[d] = m                                                          # (one pack can have two versions here)
    lib = os.path.join(VAULT, "FabLibrary")
    if os.path.isdir(lib):
        for d in sorted(os.listdir(lib)):
            if not os.path.isdir(os.path.join(lib, d)): continue
            mp = os.path.join(lib, d, "unreal-engine", "manifest")
            m = read_manifest(mp) if os.path.isfile(mp) and os.path.getsize(mp) >= 100 else None
            if m:
                m["dir"] = os.path.join(lib, d)
                listing[m["id"] or d] = m
            else:
                listing.setdefault(d, {"title": re.sub(r"-[0-9a-f]{8}$", "", d).replace("__", " ").replace("_", " "), "id": "", "url": "",
                                       "tags": "", "type": "", "apps": [], "files": 0, "size": 0, "cnt": collections.Counter(),
                                       "tops": [], "app": "", "dir": os.path.join(lib, d), "unread": True})
    # (a download's binary manifest carries no title, link or tags: they come from its listing, by the launcher's app name,
    # else by the folder it adds to Content)
    by_app = {m["app"]: m for m in listing.values() if m.get("app")}
    by_top = {}
    for m in listing.values():
        for t in m["tops"]: by_top.setdefault(t.lower(), m)
    for m in down.values():
        if m["id"] and m["url"]: continue
        src = by_app.get(m["app"]) or next((by_top[t.lower()] for t in m["tops"] if t.lower() in by_top), None)
        if src:
            if m["title"] == m["app"]: m["title"] = src["title"]
            for k in ("id", "url", "tags", "type", "apps"): m[k] = m[k] or src[k]
    return down, listing


def zip_listing(path):
    try:
        z = zipfile.ZipFile(path)
    except Exception:
        return None
    cnt = collections.Counter(); tops = collections.Counter(); ext = collections.Counter()
    for i in z.infolist():
        if i.is_dir() or i.filename.startswith("__MACOSX"): continue
        k = kind_of(i.filename)
        if k: cnt[k] += 1
        e = i.filename.rsplit(".", 1)[-1].lower() if "." in i.filename.rsplit("/", 1)[-1] else ""
        ext[e] += 1
        parts = i.filename.split("/")
        if len(parts) > 2 and parts[0].lower() != "content": tops[parts[0]] += 1
        elif len(parts) > 2: tops[parts[1]] += 1
    return {"cnt": cnt, "tops": [t for t, _ in tops.most_common(4)], "ext": ext}


# ------------------------------------------------------------------------------------------------ the project
def scan_dir(root):
    cnt = collections.Counter(); size = 0; n = 0
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if not d.startswith("__External")]
        for f in fn:
            n += 1
            try: size += os.path.getsize(os.path.join(dp, f))
            except OSError: pass
            k = kind_of(os.path.join(dp, f))
            if k: cnt[k] += 1
    return cnt, size, n


def glb_info(path):
    try:
        with open(path, "rb") as fh:
            magic, ver, length = struct.unpack("<III", fh.read(12))
            clen, ctype = struct.unpack("<II", fh.read(8))
            j = json.loads(fh.read(clen))
    except Exception:
        return "not read"
    skins = j.get("skins", []); anims = j.get("animations", [])
    joints = max((len(s.get("joints", [])) for s in skins), default=0)
    names = [a.get("name", "?") for a in anims]
    nm = len(j.get("meshes", []))
    s = f"{nm} mesh" + ("es" if nm != 1 else "")
    s += f", rigged ({joints} bones)" if skins else ", not rigged"
    if names: s += f", {len(names)} clip" + ("s" if len(names) != 1 else "") + ": " + ", ".join(names[:12]) + (" ..." if len(names) > 12 else "")
    else: s += ", no clips"
    return s


# ------------------------------------------------------------------------------------------------ CGAxis
FMT_WORDS = [("unreal", "Unreal"), ("fbx", "FBX"), ("obj", "OBJ"), ("c4d_vray", "C4D V-Ray"), ("c4d-vray", "C4D V-Ray"),
             ("c4d", "C4D"), ("corona", "3ds Max Corona"), ("mentalray", "3ds Max Mental Ray"), ("mental_ray", "3ds Max Mental Ray"),
             ("scanline", "3ds Max Scanline"), ("maya-vray", "Maya V-Ray"), ("maya", "Maya"), ("vrmesh", "V-Ray proxy"),
             ("vray", "3ds Max V-Ray"), ("lxo", "Modo"), ("maps", "texture maps")]


def fmt_of(name):
    n = name.lower()
    for w, f in FMT_WORDS:
        if w in n: return f
    return None


def natural(s):
    return [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", s)]


def cgaxis():
    vols = collections.defaultdict(lambda: {"fbx": set(), "fmts": set(), "zips": set(), "ue": 0, "where": set()})
    inter = collections.defaultdict(lambda: {"fmts": set(), "zips": set(), "ue": 0})
    extra = []; bad = []
    for folder in sorted(os.listdir(CG), key=natural):
        fd = os.path.join(CG, folder)
        for f in sorted(os.listdir(fd)):
            p = os.path.join(fd, f)
            if not f.lower().endswith(".zip"):
                if not f.lower().endswith(".pdf"): bad.append((p, os.path.getsize(p)))
                continue
            if "preview" in f.lower(): continue
            try: z = zipfile.ZipFile(p)
            except Exception:
                bad.append((p, os.path.getsize(p))); continue
            names = [i.filename for i in z.infolist() if not i.filename.startswith("__MACOSX")]
            fl = f.lower()
            if "texture" in fl or "hdri" in fl or "exteriors" in fl:
                dirs = {n.split("/")[1] for n in names if n.count("/") >= 2}
                hdr = sum(1 for n in names if n.lower().endswith(".hdr"))
                extra.append((f, p, os.path.getsize(p), len(dirs), hdr, names))
                continue
            for n in names:
                nl = n.lower()
                m = re.search(r"interiors_(\d\d)_(\d\d)", n, re.I)
                if m:
                    e = inter[(int(m.group(1)), int(m.group(2)))]
                    e["zips"].add(p)
                    if nl.endswith(".uasset"): e["ue"] += 1; e["fmts"].add("Unreal")
                    elif nl.endswith(".fbx"): e["fmts"].add("FBX")
                    elif nl.endswith(".obj"): e["fmts"].add("OBJ")
                    elif nl.endswith(".max"): e["fmts"].add("3ds Max")
                    elif nl.endswith(".c4d"): e["fmts"].add("C4D")
                    continue
                if "interiors" in nl: continue
                m = re.search(r"volume_?(\d+)", n, re.I) or re.search(r"Volume(\d+)_", n)
                if not m: continue
                e = vols[int(m.group(1))]
                e["zips"].add(p); e["where"].add(folder)
                seg = n.split("/")[1] if n.count("/") >= 2 else f
                ff = fmt_of(seg) or fmt_of(f.replace("Complete-", ""))
                if ff: e["fmts"].add(ff)
                if nl.endswith(".fbx"): e["fbx"].add(n.rsplit("/", 1)[-1].lower())
                if nl.endswith(".uasset"): e["ue"] += 1; e["fmts"].add("Unreal")
    return vols, inter, extra, bad


def interior_texts():
    """the Complete 6-10 catalogues' descriptions of the interiors scenes (FILENAME:CGAXIS_INTERIORS_xx_yy); most of their text
    lost its spaces in the PDF: those are left out"""
    out = {}
    for folder in os.listdir(CG):
        fd = os.path.join(CG, folder)
        for f in os.listdir(fd):
            if not f.lower().endswith(".pdf"): continue
            try: t = subprocess.run(["pdftotext", os.path.join(fd, f), "-"], capture_output=True, timeout=120).stdout.decode("utf-8", "replace")
            except Exception: return out
            for line in t.splitlines():
                m = re.search(r"^(.*?)\s*Total\s*polygon\s*count.*FILENAME:\s*CGAXIS_INTERIORS_(\d\d)_(\d\d)", line, re.I)
                if m and m.group(1).strip().count(" ") >= 2:
                    out[(int(m.group(2)), int(m.group(3)))] = m.group(1).strip()
    return out


# ------------------------------------------------------------------------------------------------ the document
OWN = {"RandomDungeon": "the project's own: the dungeons', towns' and wilderness's generated assets, clips made in Blender, the farm animals and the horse",
       "RandomIsoVillage": "the project's own (the isometric village)", "RandomLevel": "the project's own (the town level)",
       "SFCityLevel": "the project's own (sf-city-level)", "Starship": "the project's own (starship_level)",
       "JRPG": "the project's own: the Tripo heroes imported (meshes, rigs, retargeted and Blender-made clips)",
       "HeroGallery": "the project's own (gallery)", "MonsterGallery": "the project's own (gallery)", "ObjectGallery": "the project's own (gallery)",
       "Levels": "the project's maps", "LevelSequence": "the project's sequences", "Materials": "the project's materials",
       "Meshes": "the project's meshes", "Textures": "the project's textures", "Blueprints": "the project's blueprints",
       "Input": "input actions and contexts", "ThirdPerson": "the engine's third-person template", "StarterContent": "the engine's starter content",
       "Characters": "the engine's mannequins (template)", "MetaHumans": "MetaHuman characters (Summoner2, the Summoner's face)",
       "Meshy": "Meshy test characters", "Collections": "editor collections", "Developers": "editor developer folders"}


def main():
    L = []
    w = L.append
    today = datetime.date.today().isoformat()
    down, listing = fab_packs()
    allm = list(down.values()) + list(listing.values())
    by_top = {}
    for m in allm:
        for t in m["tops"]: by_top.setdefault(t.lower(), m)

    w("# All 3D assets on the machine")
    w("")
    w(f"A survey of the 3D assets in four places, made {today} by `asset_survey/all3d_survey.py` (run it again to bring this file up to date). "
      "[assets.md](assets.md) says which of them the levels use and credits them; this file lists everything that is there, with its path.")
    w("")
    w("- **How it was read:** nothing was extracted or opened in an editor. The Fab packs from their own manifests (title, tags, store link, engine versions, file list), "
      "the CGAxis volumes from their zips' file lists and the catalogues beside them, the KitBash3D kits and the project's folders from their files on disk.")
    w("- **Counts** of skeletal meshes, static meshes, clips (animations), effects and the rest are counted from the asset names "
      "(`SK_`, `SM_`, `A_` or an Animations folder, `NS_`...): they are approximate, as each pack names things its own way.")
    w("- **Licences:** the Fab packs under the Fab licence (`I:\\game assets\\3d fab library data cache\\FAB STANDARD LICENSE AGREEMENT.pdf`), "
      "CGAxis under its royalty-free licence (in a game, credit \"models by CGAXIS.com\"), the KitBash3D kits under KitBash3D's. None of them may be put in the repository.")
    w("")
    w("## Contents")
    w("")
    w("1. [The project](#1-the-project-ecodeclaude-ue5)")
    w("2. [CGAxis models](#2-cgaxis-models-igame-assets3d-cgaxis-models)")
    w("3. [The Fab library](#3-the-fab-library-igame-assets3d-fab-library-data-cache)")
    w("4. [KitBash3D kits](#4-kitbash3d-kits-cuserskestanolappdataroamingkitbash3dkits)")
    w("")

    # ---------------------------------------------------------------- 1. the project
    w("## 1. The project (`E:\\code\\claude-ue5`)")
    w("")
    w("### The project's own models (`ai models`, `old models`)")
    w("")
    w("Characters and animals made with Tripo (and, in `old models`, the first Tripo and Meshy tests), the one model content the repository holds "
      "(`ai models/*.glb`, CC BY 4.0: [ai models/README.md](../ai%20models/README.md)). Rig and clips read from each file.")
    w("")
    w("| File | Size | What the file holds | Path |")
    w("|---|---|---|---|")
    for folder in ("ai models", "old models"):
        fd = os.path.join(REPO, folder)
        if not os.path.isdir(fd): continue
        for f in sorted(os.listdir(fd), key=str.lower):
            if not f.lower().endswith((".glb", ".gltf", ".fbx")): continue
            p = os.path.join(fd, f)
            note = glb_info(p) if f.lower().endswith(".glb") else ""
            if folder == "old models": note += " (deprecated, ignored by git)"
            w(f"| `{md(f)}` | {gb(os.path.getsize(p))} | {md(note)} | `{p}` |")
    w("")

    w("### Packs and folders in `claude_ue5/Content`")
    w("")
    w("Each folder under `E:\\code\\claude-ue5\\claude_ue5\\Content` (its path is `E:\\code\\claude-ue5\\claude_ue5\\Content\\<folder>`); "
      "the Fab pack whose manifest adds that folder, else the project's own or a pack not in the vault.")
    w("")
    w("| Folder | Fab pack (store) | Kind | Contents | Files | Size |")
    w("|---|---|---|---|---|---|")
    for d in sorted(os.listdir(CONTENT), key=str.lower):
        full = os.path.join(CONTENT, d)
        if not os.path.isdir(full) or d.startswith("__"): continue
        cnt, size, n = scan_dir(full)
        m = by_top.get(d.lower())
        sharers = sorted({x["title"] for x in allm if d.lower() in [q.lower() for q in x["tops"]]})
        if len(sharers) > 1: src = f"shared by {len(sharers)} packs: " + "; ".join(md(s) for s in sharers); kind = md(m["tags"])
        elif m: src = f"[{md(m['title'])}]({m['url']})" if m["url"] else md(m["title"]); kind = md(m["tags"])
        elif d in OWN: src = OWN[d]; kind = "project"
        else: src = "not in the Fab vault's manifests"; kind = ""
        w(f"| `{md(d)}` | {src} | {kind} | {summary(cnt)} | {n} | {gb(size)} |")
    w("")

    w("### Pack projects opened in the repository's root")
    w("")
    w("Fab packs downloaded as whole projects (a `.uproject` beside their `Content`) into the repository's root, ignored by git; their content is copied into `claude_ue5/Content` when used.")
    w("")
    w("| Folder | Fab pack (store) | Its Content folders | Contents | Size | Path |")
    w("|---|---|---|---|---|---|")
    for d in sorted(os.listdir(REPO), key=str.lower):
        full = os.path.join(REPO, d)
        if not os.path.isdir(full) or d == "claude_ue5": continue
        cdir = os.path.join(full, "Content")
        up = [f for f in os.listdir(full) if f.endswith(".uproject")]
        if not (up or d == "CityScooterRigged"): continue
        cnt, size, n = scan_dir(full)
        tops = [t for t in os.listdir(cdir) if not t.startswith("__") and t != "Splash"] if os.path.isdir(cdir) else os.listdir(full)
        key = re.sub(r"[^a-z0-9]", "", d.lower())
        m = next((x for x in down.values() if re.sub(r"[^a-z0-9]", "", x["title"].lower()).startswith(key)), None) \
            or next((by_top.get(t.lower()) for t in tops if by_top.get(t.lower())), None)
        src = f"[{md(m['title'])}]({m['url']})" if m and m["url"] else "not in the Fab vault's manifests"
        w(f"| `{md(d)}` | {src} | {', '.join('`' + md(t) + '`' for t in tops)} | {summary(cnt)} | {gb(size)} | `{full}` |")
    w("")

    w("### 3D files under `claude_ue5/SourceArt`")
    w("")
    w("The files the pipeline's scripts made or converted (the Blender scripts' FBX, the heroes' and creatures' sources, the armour fits). Folders with no 3D file are left out.")
    w("")
    w("| Folder | 3D files | Kinds | Size | Path |")
    w("|---|---|---|---|---|")
    sa = os.path.join(REPO, "claude_ue5", "SourceArt")
    for d in sorted(os.listdir(sa), key=str.lower):
        full = os.path.join(sa, d)
        if not os.path.isdir(full): continue
        ext = collections.Counter(); size = 0
        for dp, dn, fn in os.walk(full):
            for f in fn:
                e = f.rsplit(".", 1)[-1].lower() if "." in f else ""
                if e in ("fbx", "glb", "gltf", "obj", "blend", "usd", "abc"):
                    ext[e] += 1; size += os.path.getsize(os.path.join(dp, f))
        if not ext: continue
        w(f"| `{md(d)}` | {sum(ext.values())} | {', '.join(f'{v} .{k}' for k, v in ext.most_common())} | {gb(size)} | `{full}` |")
    w("")

    # ---------------------------------------------------------------- 2. CGAxis
    vols, inter, extra, bad = cgaxis()
    itexts = interior_texts()
    w("## 2. CGAxis models (`I:\\game assets\\3d cgaxis models`)")
    w("")
    w("CGAxis's Complete collections 1-13 as zips (one zip per format for Complete 1-10, one zip per volume for 11-13). Realistic, high-polygon models made for "
      "architectural rendering (3ds Max, Cinema 4D, Maya and V-Ray scenes, with FBX and OBJ copies; Unreal assets from volume 101 on). None is game-ready: no LODs, "
      "no collision, and up to millions of polygons a scene. The models' files are numbered (`cgaxis_models_<volume>_<n>`), so a volume's subject is its title. "
      "A preview zip (one PDF a volume) or a catalogue PDF sits beside each set.")
    w("")
    w("### The models volumes")
    w("")
    w("Titles: cgaxis.com's product pages, the complete.cgaxis.com pages, the catalogue PDFs (\"catalogue\": named from the catalogue's description), "
      "the zips' names. Models: the volume's FBX files in its zips.")
    w("")
    w("| Volume | Subject | Models (FBX) | Formats | Folder | Zips |")
    w("|---|---|---|---|---|---|")
    for v in sorted(vols):
        e = vols[v]
        t = CG_TITLES.get(v, "title not found (not in the local files; cgaxis.com has no page under its number)")
        zl = sorted(os.path.basename(z) for z in e["zips"])
        zips = "<br>".join(f"`{z}`" for z in zl) if len(zl) <= 2 else f"`{re.sub(r'-[A-Z][A-Z0-9-]*[.]zip$', '', zl[0])}-<format>.zip` (one a format, {len(zl)})"
        w(f"| {v} | {md(t)} | {len(e['fbx'])} | {', '.join(sorted(e['fmts']))} | `{CG}\\{sorted(e['where'])[0]}` | {zips} |")
    w("")
    w("### The interiors volumes (ready-to-render rooms)")
    w("")
    w("Whole rooms set up for rendering (lights, cameras, materials), one scene a file: 3ds Max and Cinema 4D with V-Ray, FBX and OBJ copies, and Unreal for volume 5. "
      "Descriptions from the catalogues where their text could be read.")
    w("")
    w("| Scene | Description | Formats | Zips |")
    w("|---|---|---|---|")
    for k in sorted(inter):
        e = inter[k]; zs = sorted(e["zips"])
        w(f"| `cgaxis_interiors_{k[0]:02d}_{k[1]:02d}` | {md(itexts.get(k, 'in the catalogue PDF beside its zips'))} | {', '.join(sorted(e['fmts']))} | "
          + "<br>".join(f"`{os.path.basename(z)}`" for z in zs) + f" (in `{os.path.dirname(zs[0])}`) |")
    w("")
    w("### Textures, skies and exteriors")
    w("")
    w("| Zip | What it holds | Size | Path |")
    w("|---|---|---|---|")
    for f, p, size, dirs, hdr, names in extra:
        fl = f.lower()
        if "hdri" in fl: what = f"{hdr} HDRI skies (.hdr, with .jpg previews)"
        elif "texture" in fl:
            sets = sorted({n.split('/')[1] for n in names if n.count('/') >= 2})
            what = f"{dirs} PBR texture sets (colour, normal, roughness... a set): " + ", ".join(sets[:10]).replace("_", " ") + (" ..." if len(sets) > 10 else "")
        else: what = f"{dirs} exterior scenes (3ds Max and Cinema 4D, V-Ray proxies)"
        w(f"| `{md(f)}` | {md(what)} | {gb(size)} | `{p}` |")
    for p, size in bad:
        w(f"| `{md(os.path.basename(p))}` | an unfinished download (not a zip) | {gb(size)} | `{p}` |")
    w("")

    # ---------------------------------------------------------------- 3. Fab
    w("## 3. The Fab library (`I:\\game assets\\3d fab library data cache`)")
    w("")
    w("The Epic Games Launcher's vault cache: each downloaded Fab pack in `VaultCache\\<pack>` (its `manifest` and its `data\\Content`), "
      "and the library's listings in `VaultCache\\FabLibrary\\<listing>\\unreal-engine\\manifest` (a listing's manifest names every file of the pack, downloaded or not). "
      "\"In the project\" names the `claude_ue5/Content` folder when the pack's folder is there.")
    w("")
    content_dirs = {d.lower() for d in os.listdir(CONTENT)}
    def inproj(m):
        return ", ".join(f"`{t}`" for t in m["tops"] if t.lower() in content_dirs)
    w(f"### Downloaded packs ({len(down)})")
    w("")
    w("| Pack (store) | Kind | Contents | Engine | Size | Folder in Content | In the project | Path |")
    w("|---|---|---|---|---|---|---|---|")
    for m in sorted(down.values(), key=lambda m: m["title"].lower()):
        t = f"[{md(m['title'])}]({m['url']})" if m["url"] else md(m["title"])
        note = "" if m["downloaded"] else " (manifest only, no data)"
        w(f"| {t} | {md(m['tags'] or m['type'])} | {summary(m['cnt'])} | {ue_range(m['apps'])} | {gb(m['size'])} | "
          f"{', '.join('`' + md(x) + '`' for x in m['tops'][:3])} | {inproj(m)} | `{m['dir']}`{note} |")
    w("")
    have = {m["id"] for m in down.values() if m["id"]} | {m["title"].lower() for m in down.values()}
    only = {k: m for k, m in listing.items() if m["id"] not in have and m["title"].lower() not in have}
    w(f"### In the library, not downloaded ({len(only)} of the {len(listing)} listings)")
    w("")
    w("Listings whose manifest is in `FabLibrary` but whose pack is not in the vault cache: their contents are known from the manifest; downloading one needs the launcher.")
    w("")
    w("| Pack (store) | Kind | Contents | Engine | Size | Folder in Content | In the project | Manifest |")
    w("|---|---|---|---|---|---|---|---|")
    for m in sorted(only.values(), key=lambda m: m["title"].lower()):
        t = f"[{md(m['title'])}]({m['url']})" if m["url"] else md(m["title"])
        w(f"| {t} | {md(m['tags'] or m['type'])} | {summary(m['cnt'])} | {ue_range(m['apps'])} | {gb(m['size'])} | "
          f"{', '.join('`' + md(x) + '`' for x in m['tops'][:3])} | {inproj(m)} | `{m['dir']}`"
          + (" (its manifest is not a manifest: an expired-token note)" if m.get("unread") else "") + " |")
    w("")
    w("### Loose zips")
    w("")
    w("| Zip | Contents | Its folders | Size | Path |")
    w("|---|---|---|---|---|")
    for f in sorted(os.listdir(FAB)):
        p = os.path.join(FAB, f)
        if not f.lower().endswith(".zip"): continue
        z = zip_listing(p)
        if not z: w(f"| `{md(f)}` | not read | | {gb(os.path.getsize(p))} | `{p}` |"); continue
        what = summary(z["cnt"])
        if z["ext"].get("exe"): what = "a packaged Windows demo (exe, pak): no editable assets"
        w(f"| `{md(f)}` | {what} | {', '.join('`' + md(t) + '`' for t in z['tops'])} | {gb(os.path.getsize(p))} | `{p}` |")
    w("")

    # ---------------------------------------------------------------- 4. KitBash3D
    w("## 4. KitBash3D kits (`C:\\Users\\kestanol\\AppData\\Roaming\\kitbash3d\\kits`)")
    w("")
    w("The KitBash3D app's downloads: each kit's models as USD files (a folder a model, with its LOD and material files), its materials and PNG / EXR textures. "
      "Unreal imports USD through its USD Importer plugin.")
    w("")
    w("| Kit | Version | Models | Materials | Textures | Size | Path |")
    w("|---|---|---|---|---|---|---|")
    kb_models = {}
    for k in sorted(os.listdir(KB)):
        kd = os.path.join(KB, k)
        for ver in sorted(os.listdir(kd)):
            vd = os.path.join(kd, ver)
            models = sorted(os.listdir(os.path.join(vd, "Models"))) if os.path.isdir(os.path.join(vd, "Models")) else []
            mats = os.listdir(os.path.join(vd, "Materials")) if os.path.isdir(os.path.join(vd, "Materials")) else []
            tex = 0; size = 0
            for dp, dn, fn in os.walk(vd):
                for f in fn:
                    size += os.path.getsize(os.path.join(dp, f))
                    if f.lower().endswith((".png", ".exr", ".jpg")): tex += 1
            kb_models[k] = models
            w(f"| {KB_TITLES.get(k, k)} (`{k}`) | {ver} | {len(models)} | {len(mats)} | {tex} | {gb(size)} | `{vd}` |")
    w("")
    for k, models in kb_models.items():
        groups = collections.Counter()
        for mname in models:
            base = re.sub(r"^KB3D_[A-Z]+_", "", mname)
            base = re.sub(r"_[A-Z0-9]+$", "", base) if "_" in base else base
            groups[base] += 1
        w(f"**{KB_TITLES.get(k, k)}, its models** ({len(models)}, by name, variants counted): " +
          ", ".join(f"{g} ({c})" if c > 1 else g for g, c in sorted(groups.items())) + ".")
        w("")

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("ALL3D wrote", OUT, "| fab downloaded", len(down), "listings", len(listing), "not downloaded", len(only),
          "| cgaxis volumes", len(vols), "interiors", len(inter))


if __name__ == "__main__":
    main()
