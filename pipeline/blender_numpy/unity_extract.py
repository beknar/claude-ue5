"""Extract the models, textures and Unity materials of a Fab pack in Unity format (a .unitypackage: a gzipped tar of
<guid>/asset + <guid>/pathname) into out_dir/<the path it has in the Unity project>, e.g. out_dir/Assets/<Pack>/...
Animations, prefabs, scenes and scripts are left out. Used for packs that come only in Unity format (900 imports two
of them for the monster gallery). Run with python -I: the package is untrusted data and nothing in it is executed.
Usage: unity_extract.py package.unitypackage out_dir"""
import sys, os, tarfile
pkg, out = sys.argv[1], sys.argv[2]
KEEP = (".fbx", ".png", ".tga", ".jpg", ".jpeg", ".psd", ".tif", ".tiff", ".mat")
entries = {}
with tarfile.open(pkg, "r:gz") as t:
    for m in t:
        if not m.isfile(): continue
        guid, _, leaf = m.name.partition("/")
        if leaf in ("asset", "pathname"): entries.setdefault(guid, {})[leaf] = m
    names = {}
    for g, e in entries.items():
        if "pathname" in e: names[g] = t.extractfile(e["pathname"]).read().decode("utf-8", "replace").splitlines()[0].strip()
n = 0
with tarfile.open(pkg, "r:gz") as t:
    for m in t:
        guid, _, leaf = m.name.partition("/")
        if leaf != "asset" or guid not in names: continue
        p = names[guid]
        if not p.lower().endswith(KEEP): continue
        dst = os.path.normpath(os.path.join(out, p.replace("/", os.sep)))
        assert dst.startswith(os.path.normpath(out)), p                 # (no path escapes the output folder)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "wb") as f: f.write(t.extractfile(m).read())
        n += 1
print("extracted", n, "files to", out)
