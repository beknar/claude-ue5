"""Survey of the asset directories on this machine that are not Unreal content: the asset library's folders on
I:\\game assets that docs/assets.md does not name (2D and pixel-art packs, sound and music, fonts, AI-made material)
and other download folders given on the command line. For each: its size, how many files of each kind it holds
(images, sound, 3D models, fonts, archives, Unity and Godot files, documents), the most common file types, the
newest file. Writes asset_survey/asset_dirs.json and prints the table rows docs/assets.md takes ("Other asset
libraries on disk").
Usage: asset_dirs_survey.py [extra_dir ...]      (a Python 3 without other packages)"""
import os, re, sys, json, collections, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DOC = open(os.path.join(ROOT, "docs", "assets.md"), encoding="utf-8").read()
# (what the doc names elsewhere: its own section and the rows it gave the directories list are left out, so that a re-run
# surveys the same folders again and any new ones)
if "## Other asset libraries on disk" in DOC:
    i = DOC.index("## Other asset libraries on disk"); j = DOC.index("\n## ", i + 5)
    DOC = DOC[:i] + DOC[j:]
DOC = "\n".join(l for l in DOC.splitlines() if "(not Unreal content; see above)" not in l).lower()
LIB = r"I:\game assets"
KINDS = {"image": {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tga", ".psd", ".webp", ".aseprite", ".ase", ".tif", ".tiff", ".svg", ".kra", ".xcf"},
         "sound": {".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aif", ".aiff", ".wma", ".opus", ".mid", ".midi"},
         "3D model": {".fbx", ".obj", ".mtl", ".glb", ".gltf", ".blend", ".dae", ".3ds", ".max", ".stl", ".ply", ".usd", ".usdz", ".vox"},
         "font": {".ttf", ".otf", ".fnt", ".woff", ".woff2", ".bdf"},
         "archive": {".zip", ".rar", ".7z", ".tar", ".gz"},
         "Unity": {".unitypackage", ".unity", ".prefab", ".meta", ".mat", ".anim", ".controller"},
         "Godot": {".tscn", ".tres", ".gd", ".godot", ".import"},
         "Tiled map": {".tmx", ".tsx", ".tmj", ".tsj"},
         "document": {".pdf", ".txt", ".md", ".html", ".htm", ".docx", ".rtf"},
         "video": {".mp4", ".mov", ".avi", ".webm", ".mkv"}}
KIND_OF = {e: k for k, es in KINDS.items() for e in es}


def survey(d):
    n = collections.Counter(); ext = collections.Counter(); size = 0; newest = 0.0; files = 0
    for r, _, fs in os.walk(d):
        for f in fs:
            p = os.path.join(r, f)
            try: st = os.stat(p)
            except OSError: continue
            e = os.path.splitext(f)[1].lower()
            n[KIND_OF.get(e, "other")] += 1; ext[e or "(none)"] += 1
            size += st.st_size; newest = max(newest, st.st_mtime); files += 1
    return {"dir": d, "files": files, "gb": round(size / 1e9, 3), "mb": round(size / 1e6, 1), "kinds": dict(n.most_common()), "top_types": ext.most_common(6),
            "newest": datetime.datetime.fromtimestamp(newest).strftime("%Y-%m-%d") if newest else None}


def what(s):
    """a line on what a folder holds, from its counts"""
    k = s["kinds"]; tot = max(s["files"], 1)
    parts = []
    for kind in ("image", "sound", "3D model", "font", "archive", "Tiled map", "Godot", "Unity", "video", "document"):
        if k.get(kind):
            word = {"image": "pictures", "sound": "sound files", "3D model": "3D models", "font": "fonts", "archive": "archives",
                    "Tiled map": "Tiled maps", "Godot": "Godot files", "Unity": "Unity files", "video": "videos", "document": "documents"}[kind]
            if k[kind] == 1: word = word.replace("files", "file").rstrip("s") if not word.endswith("files") else word.replace("files", "file")
            parts.append("%s %s" % ("{:,}".format(k[kind]), word))
    main = max((x for x in k if x != "other"), key=k.get, default="other")
    lead = {"image": "2D art", "sound": "sound and music", "3D model": "3D models", "font": "fonts", "archive": "archives not unpacked", "Godot": "a Godot project",
            "Unity": "Unity files", "video": "video", "document": "documents", "Tiled map": "tile maps", "other": "other files"}[main]
    if main == "image" and k.get("Tiled map"): lead = "2D tiles and tile maps"
    return "%s: %s" % (lead, ", ".join(parts[:5]) or "empty")


def main():
    dirs = []
    if os.path.isdir(LIB):
        for a in sorted(os.listdir(LIB)):
            pa = os.path.join(LIB, a)
            if not os.path.isdir(pa): continue
            if pa.lower() in DOC or (pa.lower() + "\\") in DOC: continue          # (the doc names it, or a place in it)
            dirs.append(pa)
    dirs += [os.path.abspath(x) for x in sys.argv[1:]]
    out = []
    for d in dirs:
        s = survey(d); s["what"] = what(s); out.append(s)
        print("%-70s %7d files %8.2f GB  %s" % (d, s["files"], s["gb"], s["what"]), file=sys.stderr)
    js = os.path.join(ROOT, "asset_survey", "asset_dirs.json")
    json.dump({"made": datetime.date.today().isoformat(), "dirs": out}, open(js, "w", encoding="utf-8"), indent=1)
    for s in out:
        types = ", ".join("%s %s" % (e, "{:,}".format(c)) for e, c in s["top_types"][:4])
        sz = ("%.1f GB" % s["gb"]) if s["gb"] >= 1.0 else ("%.0f MB" % s["mb"]) if s["mb"] >= 1.0 else "under 1 MB"
        print("| `%s` | %s | %s | %s | %s |" % (s["dir"], s["what"], types, sz, s["newest"]))
    print("wrote", js, file=sys.stderr)


main()
