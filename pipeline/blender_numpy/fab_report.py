"""Build the UE5-usability / animation-compatibility report from unity_scan.json (+ Megascans summary).
Usage: fab_report.py unity_scan.json out_dir"""
import os, re, sys, json, csv, collections
scan = json.load(open(sys.argv[1], encoding="utf-8")); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
TEX = {".tga", ".png", ".psd", ".jpg", ".jpeg", ".tif", ".tiff", ".exr", ".bmp"}
UNITY_ONLY = {".mat", ".prefab", ".controller", ".anim", ".unity", ".shader", ".shadergraph", ".asset", ".overridecontroller", ".mask", ".physicmaterial", ".lighting"}
def classify(bones):
    """rig family from bone names (refines the scanner's label)"""
    s = set(b.lower() for b in bones); n = " ".join(bones)
    legs = sum(1 for b in s if "leg" in b or "thigh" in b or "calf" in b or "knee" in b)
    if any(b.startswith("mixamorig") for b in bones): return "Mixamo"
    if {"pelvis", "spine_01", "clavicle_l", "thigh_l"} <= s: return "UE Mannequin-style"
    if "Bip001" in n or "Bip01" in n: return "3ds Max Biped"
    if "CATRig" in n:
        if "CATRigTail1" in n or "CATRigLLegDigit11" in n and "CATRigLArmPalm" not in n: return "3ds Max CAT (creature)"
        return "3ds Max CAT (humanoid)" if "CATRigLArmPalm" in n or "CATRigLArmCollarbone" in n else "3ds Max CAT (creature)"
    if any(b.endswith("_M") for b in bones) and any(b.endswith("_L") for b in bones): return "Maya AdvancedSkeleton"
    if any(b.startswith("CC_Base_") for b in bones): return "Character Creator"
    if {"hips", "spine", "leftupleg", "rightupleg"} <= s: return "Humanoid (Mixamo-style names)"
    if all("weapon" in b or "gun" in b or b.startswith("b_") for b in s): return "Weapon/prop rig"
    if any(k in n.lower() for k in ("arm", "hand")) and legs == 0: return "Arms-only (FPS)"
    return "Custom"
RETARGET = {"UE Mannequin-style": "auto-retargets with UE5 mannequin animations",
            "Mixamo": "auto-retargets (UE5 recognises Mixamo)", "Humanoid (Mixamo-style names)": "auto-retargets",
            "3ds Max Biped": "retarget via manual IK-rig chains", "3ds Max CAT (humanoid)": "retarget via manual IK-rig chains",
            "Maya AdvancedSkeleton": "retarget via manual IK-rig chains", "Character Creator": "auto-retargets (CC preset)",
            "3ds Max CAT (creature)": "own animations only", "Arms-only (FPS)": "own animations only (first-person arms)",
            "Weapon/prop rig": "own animations only", "Custom": "own animations only"}
for _p in scan:
    for _f in _p.get("fbx", []):
        if _f.get("bones"): _f["rig"] = classify(_f["bones"])
def nice(pack): return re.sub(r"-[0-9a-f]{8}$", "", pack).replace("__", " ").replace("_", " ").strip()
def clip_name(path):
    b = os.path.splitext(os.path.basename(path))[0]
    return b.split("@", 1)[1] if "@" in b else b
def is_anim_file(f):
    p = f["path"].replace("\\", "/")
    return f.get("animated") and ("@" in os.path.basename(p) or "/anim" in p.lower())
sig_packs = collections.defaultdict(lambda: {"models": set(), "anims": set(), "rig": "", "bones": 0})
packs = []
for p in sorted(scan, key=lambda r: nice(r["pack"]).lower()):
    if "error" in p: packs.append({"name": nice(p["pack"]), "error": p["error"]}); continue
    ex = p["exts"]
    models, statics, anims = [], [], collections.defaultdict(list)
    for f in p["fbx"]:
        if is_anim_file(f):
            for_clip = clip_name(f["path"])
            anims[f.get("sig", "")].append(for_clip)
            if f.get("sig"): sig_packs[f["sig"]]["anims"].add(nice(p["pack"]))
        elif f.get("meshes", 0) > 0 and f.get("bones"):
            models.append(f)
            sig_packs[f["sig"]]["models"].add(nice(p["pack"]))
        elif f.get("meshes", 0) > 0:
            statics.append(f)
        if f.get("sig"):
            sig_packs[f["sig"]]["rig"] = f.get("rig"); sig_packs[f["sig"]]["bones"] = len(f.get("bones", []))
    groups = []
    model_sigs = collections.defaultdict(list)
    for m in models: model_sigs[m["sig"]].append(os.path.splitext(os.path.basename(m["path"]))[0])
    for sig in sorted(set(model_sigs) | set(anims)):
        rig = next((f.get("rig") for f in p["fbx"] if f.get("sig") == sig), "")
        nb = next((len(f.get("bones", [])) for f in p["fbx"] if f.get("sig") == sig), 0)
        groups.append({"sig": sig, "rig": rig, "bones": nb, "models": sorted(set(model_sigs.get(sig, []))),
                       "clips": sorted(set(anims.get(sig, [])))})
    packs.append({"name": nice(p["pack"]), "fbx": len(p["fbx"]), "tex": sum(v for k, v in ex.items() if k in TEX),
                  "unity_only": {k: v for k, v in ex.items() if k in UNITY_ONLY}, "unity_anims": len(p["unity_anims"]),
                  "unity_anim_names": [os.path.splitext(os.path.basename(a))[0] for a in p["unity_anims"]][:40],
                  "models": len(models), "statics": len(statics), "static_names": sorted({os.path.splitext(os.path.basename(s["path"]))[0] for s in statics})[:30],
                  "clips": sum(len(set(v)) for v in anims.values()), "groups": groups})
# ---- markdown ----
L = ["# Fab library: what works in UE5, and which animations drive which models", "",
     "Source: `I:\\game assets\\3d epicgames media packs\\VaultCache\\FabLibrary`. Unity packages were read in place (no extraction).",
     "**UE5-usable:** FBX (skeletal meshes, static meshes, animations) and textures (TGA/PNG/PSD/JPG). "
     "**Unity-only:** .mat/.prefab/.controller/.anim/.unity - materials must be rebuilt in UE5; Unity .anim clips need conversion.", ""]
L += ["## Packs at a glance", "", "| Pack | Skinned models | Static meshes | FBX anim clips | Unity-only .anim | Textures | Rig(s) |", "|---|---|---|---|---|---|---|"]
for p in packs:
    if "error" in p: L.append(f"| {p['name']} | scan error: {p['error'][:60]} | | | | | |"); continue
    rigs = ", ".join(sorted({g['rig'] for g in p['groups'] if g['rig']})) or "-"
    L.append(f"| {p['name']} | {p['models']} | {p['statics']} | {p['clips']} | {p['unity_anims']} | {p['tex']} | {rigs} |")
# ---- compatibility by bone overlap: an animation set fits a model when >=90% of the animated bones exist in it ----
bones_of = {}
for _p in scan:
    for _f in _p.get("fbx", []):
        if _f.get("sig"): bones_of[_f["sig"]] = set(_f["bones"])
MODELS = [(p["name"], m, g["sig"], g["rig"]) for p in packs for g in p.get("groups", []) for m in g["models"]]
def fits(anim_sig, model_sig, thr):
    a, m = bones_of.get(anim_sig, set()), bones_of.get(model_sig, set())
    return bool(a) and len(a & m) / len(a) >= thr and len(a & m) >= 4
for p in packs:
    p["anim_sets"] = []
    for g in p.get("groups", []):
        if not g["clips"]: continue
        own = sorted({m for (pk, m, s, r) in MODELS if pk == p["name"] and fits(g["sig"], s, 0.90)})
        # cross-pack: only full-body sets onto full-body models (small weapon/prop sets fit everything trivially)
        other = collections.Counter(pk for (pk, m, s, r) in MODELS if pk != p["name"] and len(bones_of.get(g["sig"], ())) >= 40
                                    and len(bones_of.get(s, ())) >= 40 and "Hands" not in m and fits(g["sig"], s, 0.95))
        p["anim_sets"].append({"sig": g["sig"], "rig": g["rig"], "bones": g["bones"], "clips": g["clips"], "plays_on": own, "also_fits": dict(other)})
    animated = {m for a in p["anim_sets"] for m in a["plays_on"]}
    p["unanimated"] = sorted({m for g in p.get("groups", []) for m in g["models"]} - animated)
L += ["", "## Per pack: models, and which animations drive them", "",
      "An animation set **plays on** a model when at least 90% of its animated bones exist in that model's skeleton "
      "(import the clips onto that model's skeleton in UE5). `UE Mannequin-style` models without their own clips can use "
      "any UE5 mannequin animation through the IK Retargeter (auto chain mapping).", ""]
for p in packs:
    if "error" in p:
        L += [f"### {p['name']}", f"- **Could not be read:** {p['error']} - the download is incomplete; re-download it from Fab.", ""]; continue
    if not p.get("groups") and not p["statics"]: continue
    L.append(f"### {p['name']}")
    by_rig = collections.defaultdict(list)
    for g in p["groups"]:
        for m in g["models"]: by_rig[g["rig"]].append(m)
    for rig, ms in sorted(by_rig.items()):
        L.append(f"- **{rig}** models ({len(ms)}; {RETARGET.get(rig, '')}): {', '.join(sorted(set(ms)))}")
    for a in p["anim_sets"]:
        tgt = ", ".join(a["plays_on"]) if a["plays_on"] else "_no model in this pack shares this skeleton_"
        also = "; also fits models in: " + ", ".join(f"{k} ({v})" for k, v in sorted(a["also_fits"].items())) if a["also_fits"] else ""
        L.append(f"- **{len(a['clips'])} clips** ({a['rig']}, {a['bones']} bones) -> plays on: {tgt}{also}")
        L.append(f"  - {', '.join(a['clips'])}")
    if p["unanimated"]: L.append(f"- No clips of their own: {', '.join(p['unanimated'])}")
    if p["statics"]: L.append(f"- Static meshes ({p['statics']}): {', '.join(p['static_names'])}{' ...' if p['statics'] > 30 else ''}")
    if p["unity_anims"]: L.append(f"- Unity-only .anim clips ({p['unity_anims']}): {', '.join(p['unity_anim_names'])}")
    L.append("")
open(os.path.join(out, "fab_library_ue5_survey.md"), "w", encoding="utf-8").write("\n".join(L))
with open(os.path.join(out, "fab_animations.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["pack", "skeleton", "rig", "bones", "models", "clip"])
    for p in packs:
        for g in p.get("groups", []):
            for c in g["clips"]: w.writerow([p["name"], g["sig"], g["rig"], g["bones"], "; ".join(g["models"]), c])
json.dump({"packs": packs, "shared": {k: {"rig": v["rig"], "bones": v["bones"], "models": sorted(v["models"]), "anims": sorted(v["anims"])} for k, v in sig_packs.items()}},
          open(os.path.join(out, "fab_survey.json"), "w", encoding="utf-8"), indent=1)
print("packs", len(packs), "| total skinned models", sum(p.get("models", 0) for p in packs), "| static", sum(p.get("statics", 0) for p in packs),
      "| FBX clips", sum(p.get("clips", 0) for p in packs), "| unity-only anims", sum(p.get("unity_anims", 0) for p in packs))
print("rigs:", collections.Counter(g["rig"] for p in packs for g in p.get("groups", []) if g["models"]).most_common())
