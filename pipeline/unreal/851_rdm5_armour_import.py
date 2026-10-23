"""random_dungeonmagic_level5's armour, step 3: the five sets refitted to Summoner3 (blender_numpy/summoner3_armour.py:
SourceArt/summoner3/armour_fit/<set>.fbx, each set one mesh skinned to her skeleton in her rest pose) imported onto her
skeleton (SK_JRPG_Summoner3's) as /Game/JRPG/Summoner3Armour/SK_S3_<set>, each material slot given back the pack's
material of its name (849's materials.json; the Blender names carry .001 ... suffixes). Prints each mesh's bones and slots.
Args: none (Summoner3, every set), or a hero's mesh name (Fem5, DarkCaster, Rogue ...) and the sets' keys: armour_fit/
<name>/<set>.fbx onto SK_JRPG_<name>'s skeleton as /Game/JRPG/HeroArmour/<name>/SK_<name>_<set>."""
import json, os, re, sys, unreal
HERO = sys.argv[1] if len(sys.argv) > 1 else "Summoner3"; KEYS = set(sys.argv[2:])
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\summoner3"
J = json.load(open(os.path.join(SA, "armour.json"), encoding="utf-8"))
MATS = json.load(open(os.path.join(SA, "armour_src", "materials.json")))
byname = {}
for slots in MATS.values():
    for p in slots.values():
        if p: byname[p.split(".")[-1]] = p
D = "/Game/JRPG/Summoner3Armour" if HERO == "Summoner3" else f"/Game/JRPG/HeroArmour/{HERO}"; eal = unreal.EditorAssetLibrary
PRE = "SK_S3_" if HERO == "Summoner3" else f"SK_{HERO}_"; FIT = os.path.join(SA, "armour_fit", *([] if HERO == "Summoner3" else [HERO]))
skel = unreal.load_asset(f"/Game/JRPG/Character/SK_JRPG_{HERO}").get_editor_property("skeleton")
def setp(obj, name, val):
    try: obj.set_editor_property(name, val)
    except Exception as e: print("  (skip)", name, str(e)[:80])
for s in J["sets"]:
    if KEYS and s["key"] not in KEYS: continue
    f = os.path.join(FIT, s["key"] + ".fbx"); dst = f"{D}/{PRE}{s['key']}"
    pipe = unreal.InterchangeGenericAssetsPipeline()
    setp(pipe.common_skeletal_meshes_and_animations_properties, "skeleton", skel)
    mp = pipe.mesh_pipeline
    setp(mp, "import_skeletal_meshes", True); setp(mp, "import_static_meshes", False); setp(mp, "create_physics_asset", False)
    setp(pipe.animation_pipeline, "import_animations", False); setp(pipe.material_pipeline, "import_materials", False)
    setp(pipe.common_meshes_properties, "force_all_mesh_as_type", unreal.InterchangeForceMeshType.IFMT_SKELETAL_MESH)
    src = unreal.InterchangeManager.create_source_data(f)
    prm = unreal.ImportAssetParameters(); prm.is_automated = True; prm.replace_existing = True
    prm.override_pipelines.append(unreal.SoftObjectPath(pipe.get_path_name()))
    try: unreal.InterchangeManager.get_interchange_manager_scripted().import_asset(D + "/" + s["key"], src, prm)
    except RuntimeError as e: print("ARMIMPORT (non-fatal)", str(e)[:160])
    sk = next((unreal.load_asset(a.split(".")[0]) for a in eal.list_assets(D + "/" + s["key"], recursive=False)
               if isinstance(unreal.load_asset(a.split(".")[0]), unreal.SkeletalMesh)), None)
    assert sk, "nothing imported for " + s["key"]
    if eal.does_asset_exist(dst): eal.delete_asset(dst)
    eal.rename_asset(sk.get_path_name().split(".")[0], dst); sk = unreal.load_asset(dst)
    mats = []; missing = []
    for slot in sk.get_editor_property("materials"):
        n = str(slot.get_editor_property("material_slot_name")); base = re.sub(r"\.\d+$|_\d{3}$", "", n)
        p = byname.get(base) or byname.get(n)
        m = unreal.load_asset(p.split(".")[0]) if p else None
        if not m: missing.append(n)
        slot.set_editor_property("material_interface", m); mats.append(slot)
    # (a slot the FBX left unnamed, Fbx_Default_Material_0: the set's most used material)
    found = [x.get_editor_property("material_interface") for x in mats if x.get_editor_property("material_interface")]
    if found:
        common = max(set(found), key=found.count)
        for x in mats:
            if not x.get_editor_property("material_interface"): x.set_editor_property("material_interface", common)
    sk.set_editor_property("materials", mats); sk.modify(); eal.save_loaded_asset(sk, only_if_is_dirty=False)
    n_b = sk.get_editor_property("skeleton").get_name()
    print(f"ARMIMPORT {s['key']}: {dst} | skeleton {n_b} | slots {len(mats)}, without a name match {missing} (given the set's most used)")
