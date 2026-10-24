"""random_dungeonmagic_level5's armour, step 1: the five sets' pieces (SourceArt/summoner3/armour.json: the gallery's Plate
Armour, Bear Warrior's Armour, Tiefling's Armour, Demonic Armour and Orc Veteran's Armour, Fab packs, each skinned to the UE4
mannequin's skeleton in its own character's bind pose) exported as FBX, one per piece, to SourceArt/summoner3/armour_src/
<set>/<piece>.fbx, for blender_numpy/summoner3_armour.py, which refits them to Summoner3. Writes armour_src/materials.json:
each piece's material slots (slot name -> material path), which 851 gives back to the refitted meshes. Also exports
Summoner3's mesh (SK_JRPG_Summoner3, its rig and skin weights in Unreal's units) for the refit.
Args: none (the pieces and Summoner3), or "heroes" and the meshes' names (Fem5, DarkCaster, Rogue ...): only those heroes'
meshes, SK_JRPG_<name>.fbx beside hers, for the sets fitted to the other heroes (the armour's weights, 856); or "sets" and
sets' keys: only those sets' pieces (materials.json keeps the other sets' slots)."""
import json, os, sys, unreal
HEROES = sys.argv[2:] if len(sys.argv) > 1 and sys.argv[1] == "heroes" else None
ONLY = set(sys.argv[2:]) if len(sys.argv) > 1 and sys.argv[1] == "sets" else None
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\summoner3"
J = json.load(open(os.path.join(SA, "armour.json"), encoding="utf-8"))
OUT = os.path.join(SA, "armour_src"); os.makedirs(OUT, exist_ok=True)
def export(obj, path):
    t = unreal.AssetExportTask(); t.object = obj; t.filename = path; t.automated = True; t.prompt = False; t.replace_identical = True
    o = unreal.FbxExportOption(); o.level_of_detail = False; o.collision = False; o.export_morph_targets = False; o.vertex_color = False; o.ascii = False
    t.options = o
    return unreal.Exporter.run_asset_export_task(t)
MP = os.path.join(OUT, "materials.json")
mats = json.load(open(MP)) if ONLY and os.path.exists(MP) else {}
for s in ([] if HEROES else J["sets"]):
    if ONLY and s["key"] not in ONLY: continue
    d = os.path.join(OUT, s["key"]); os.makedirs(d, exist_ok=True); n = 0
    for p in s["pieces"]:
        m = unreal.load_asset(p); assert m, p
        ok = export(m, os.path.join(d, p.split("/")[-1] + ".fbx")); n += bool(ok)
        mats[p] = {str(x.get_editor_property("material_slot_name")): (x.get_editor_property("material_interface").get_path_name() if x.get_editor_property("material_interface") else None)
                   for x in m.get_editor_property("materials")}
    print(f"ARMEXPORT {s['key']}: {n} of {len(s['pieces'])} pieces")
if not HEROES: json.dump(mats, open(MP, "w"), indent=1)
for n in ([] if ONLY else (HEROES or ["Summoner3"])):
    print("ARMEXPORT mesh", n, export(unreal.load_asset(f"/Game/JRPG/Character/SK_JRPG_{n}"), os.path.join(OUT, f"SK_JRPG_{n}.fbx")))
