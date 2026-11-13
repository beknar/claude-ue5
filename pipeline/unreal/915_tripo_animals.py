"""The list of 2026-11-10 (docs/improvements10.txt), its fifth phase: the Tripo farm animals and the riding horse ("replace the
chickens in the game with the chicken model in ai models/chicken.glb and animate it", the riding horse, the goats, the rabbits and the
pigs the same; the cow's model was not given: the Blender cow stays). Steps (all by default, or name some):
  import   pipeline/blender_numpy/tripo_animals.py's SK_Tripo_<Animal>.fbx (claude_ue5/SourceArt/brokenspire/tripo_animals: the Tripo
           mesh and texture on farm_animals.py's skeleton of the kind, its clips) into /Game/RandomDungeon/Town/Animals/Tripo/<Animal>,
           its material and texture with it; its clips at the lengths Blender built (Interchange reads 30 fps at its own rate)
  level    brokenspire: the pens' animals (TownAnimals; the farmsteads take theirs from them) the Tripo chicken, pig, goat and rabbit
           (the cow and its colourings kept), the wilds' hare (WildFauna's "Hare", made from the rabbit as 890 makes it) and the
           stable's horse (HorseDef: both its meshes the Tripo horse, its clips and their ground speeds)
Blender first: -b -P pipeline/blender_numpy/tripo_animals.py -- claude_ue5/SourceArt/brokenspire/tripo_animals. Args: [import] [level]"""
import os, sys, json, unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary
SA = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "claude_ue5", "SourceArt", "brokenspire", "tripo_animals"))
STEPS = [a for a in sys.argv[1:] if a in ("import", "level")] or ["import", "level"]
DT = "/Game/RandomDungeon/Town/Animals/Tripo"
J = json.load(open(os.path.join(SA, "tripo_animals.json"), encoding="utf-8"))
KINDS = [k for k in ("Chicken", "Pig", "Goat", "Rabbit", "Horse") if k in J]
PEN = {"Chicken": (5, 8), "Rabbit": (4, 6), "Goat": (3, 4), "Pig": (2, 3), "Cow": (2, 3)}
REPORT = []


def fbx_task(path, dest):
    o = unreal.FbxImportUI()
    o.set_editor_property("import_mesh", True); o.set_editor_property("import_as_skeletal", True)
    o.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    # (imported over an existing skeleton its bones' rest places are taken anew: tripo_animals.py's fit moves them (860's lesson))
    o.skeletal_mesh_import_data.set_editor_property("update_skeleton_reference_pose", True)
    o.set_editor_property("import_animations", True); o.set_editor_property("import_materials", False); o.set_editor_property("import_textures", False)          # (the material is made from the PNG: material_for)
    t = unreal.AssetImportTask(); t.filename = path; t.destination_path = dest
    t.automated = True; t.replace_existing = True; t.save = True; t.options = o
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    return [unreal.load_asset(p) for p in t.imported_object_paths]


def material_for(name, d):
    """the Tripo texture (T_Tripo_<Animal>.png beside the FBX) and a material of its own: the FBX's embedded image is not unpacked
    by the import (its material came with no texture)"""
    png = os.path.join(SA, J[name].get("texture") or f"T_Tripo_{name}.png")
    if not os.path.exists(png): return None, "no texture file"
    t = unreal.AssetImportTask(); t.filename = png; t.destination_path = d; t.destination_name = f"T_Tripo_{name}"
    t.automated = True; t.replace_existing = True; t.save = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    tex = unreal.load_asset(f"{d}/T_Tripo_{name}")
    if not tex: return None, "the texture did not import"
    mp = f"{d}/M_Tripo_{name}"
    if eal.does_asset_exist(mp): eal.delete_asset(mp)
    m = unreal.AssetToolsHelpers.get_asset_tools().create_asset(f"M_Tripo_{name}", d, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    ts = mel.create_material_expression(m, unreal.MaterialExpressionTextureSample, -400, 0); ts.texture = tex
    mel.connect_material_property(ts, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    r = mel.create_material_expression(m, unreal.MaterialExpressionConstant, -400, 250); r.r = 0.8
    mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    m.set_editor_property("used_with_skeletal_mesh", True)
    mel.recompile_material(m); eal.save_loaded_asset(m, only_if_is_dirty=False)
    return m, tex.get_name()


def assets_of(name):
    d = f"{DT}/{name}"
    a = [unreal.load_asset(p.split(".")[0]) for p in eal.list_assets(d, recursive=True)] if eal.does_directory_exist(d) else []
    mesh = next((x for x in a if isinstance(x, unreal.SkeletalMesh)), None)
    seqs = {x.get_name().split("_")[-1]: x for x in a if isinstance(x, unreal.AnimSequence)}
    return mesh, seqs, a


def import_takes(name, d, mesh, want):
    """the FBX's takes `want` imported on their own, onto the mesh's skeleton, and moved into the kind's folder under the names the
    import gives (the saved levels find them by path). The list of 2026-11-12: imported with an existing mesh, the FBX neither
    refreshed the takes it had made (the horse's Walk and Run kept the old clips' keys, 1.1 and 0.6 s long, only their rate_scale
    set to the new lengths: in play its hooves slid 39 and 69 % of its speed) nor made a new one (its Canter); imported alone
    into the mesh's own folder Interchange found "nothing to import": into a scratch folder of its own it takes them all"""
    tmp = f"{d}/_takes"
    if eal.does_directory_exist(tmp): eal.delete_directory(tmp)
    o = unreal.FbxImportUI()
    o.set_editor_property("import_mesh", False); o.set_editor_property("import_as_skeletal", True)
    o.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION)
    o.set_editor_property("skeleton", mesh.get_editor_property("skeleton"))
    o.set_editor_property("import_animations", True); o.set_editor_property("import_materials", False); o.set_editor_property("import_textures", False)
    t = unreal.AssetImportTask(); t.filename = os.path.join(SA, J[name]["fbx"]); t.destination_path = tmp
    t.automated = True; t.replace_existing = True; t.save = True; t.options = o
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    got = []
    for p in eal.list_assets(tmp, recursive=True):
        x = unreal.load_asset(p.split(".")[0])
        k = x.get_name().split("_")[-1] if isinstance(x, unreal.AnimSequence) else None
        if k in want:
            n = x.get_name(); x = None
            eal.rename_asset(p.split(".")[0], f"{d}/{n}"); got.append(k)
    eal.delete_directory(tmp)
    return got


if "import" in STEPS:
    for name in KINDS:
        d = f"{DT}/{name}"
        # (the mesh imported over what is there: the level's pens, hare and horse keep pointing at the same assets (PR #42's review:
        # deleted first, a run of this step alone left the level's references to nothing); its clips are imported again under
        # their paths below)
        fbx_task(os.path.join(SA, J[name]["fbx"]), d)
        mesh, seqs, a = assets_of(name)
        if not mesh: REPORT.append(f"import {name}: NO MESH"); continue
        # (Interchange samples at 30 a second: a clip of another rate comes in up to a frame short; a clip further off than that
        # is not the one Blender built)
        def is_stale(k, s):
            L = float(J[name]["clips"].get(k, {}).get("length_s", s.get_play_length()))
            return L > 0 and abs(s.get_play_length() - L) > 1.0 / 30.0 + 0.005
        # (every clip, not only those of another length: the whole-frame strides came out as long as the old ones' imports, to
        # within a frame, with the old keys)
        old = list(seqs)
        want = old + [k for k in J[name].get("clips", {}) if k not in seqs]
        if want:
            # (an import keeps a clip asset that is there: the kind's clips are deleted with an empty level open (none of the maps
            # holds them then) and imported again under their paths; the level step points the pens, hare and horse at them)
            if old and not ues.get_editor_world().get_path_name().startswith("/Game/RandomLevel/Test/rl_scratch."):
                unreal.EditorLoadingAndSavingUtils.load_map("/Game/RandomLevel/Test/rl_scratch")
            paths = [seqs[k].get_path_name().split(".")[0] for k in old]
            seqs = None; a = None
            import gc; gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")
            for p in paths: eal.delete_asset(p)
            got = import_takes(name, d, mesh, want)
            mesh, seqs, a = assets_of(name)
            REPORT.append(f"import {name}: {sorted(got)} imported again")
        stale = []
        for k, s in seqs.items():
            L = float(J[name]["clips"].get(k, {}).get("length_s", s.get_play_length()))
            if is_stale(k, s): stale.append(f"{k} {s.get_play_length():.3f} s for {L:.3f}")
            s.set_editor_property("rate_scale", s.get_play_length() / L if L > 0 and abs(s.get_play_length() - L) > 0.002 else 1.0)
            eal.save_loaded_asset(s, only_if_is_dirty=False)
        missing = [k for k in J[name].get("clips", {}) if k not in seqs]
        assert not stale and not missing, f"915: {name}'s clips are not the FBX's: {stale}, missing {missing}"
        mat, tex = material_for(name, d)
        if mat:
            ms = list(mesh.get_editor_property("materials"))
            for k in range(len(ms)): ms[k].set_editor_property("material_interface", mat)
            mesh.modify(); mesh.set_editor_property("materials", ms); eal.save_loaded_asset(mesh, only_if_is_dirty=False)
        mats = [m.get_editor_property("material_interface").get_name() if m.get_editor_property("material_interface") else None for m in mesh.get_editor_property("materials")]
        REPORT.append(f"import {name}: clips {sorted(seqs)}, materials {mats}, textures {tex}")

if "level" in STEPS:
    MAP = "/Game/RandomDungeon/Maps/brokenspire"
    if not ues.get_editor_world().get_path_name().startswith(MAP + "."):
        les.load_level(MAP); unreal.SystemLibrary.execute_console_command(None, "obj gc")
    g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    # the pens' animals: the kinds Tripo made replaced (their Blender colourings with them), the cow kept
    old = list(g.get_editor_property("town_animals"))
    # (the cow's first colouring alone: the pens take the list's kinds in turn, and with its second the cow had a third of them
    # (PR #42's review); before, two of eleven)
    kept = [t for t in old if str(t.name).split("_")[0] not in KINDS and "_" not in str(t.name)]
    made = []
    for name in KINDS:
        if name == "Horse": continue
        mesh, seqs, _a = assets_of(name)
        if not mesh or "Idle" not in seqs: REPORT.append(f"level {name}: not imported"); continue
        R = J[name]; sz = R["size_cm"]
        ad = unreal.RDTownAnimalDef()
        ad.set_editor_property("name", name); ad.set_editor_property("mesh", mesh)
        ad.set_editor_property("idle", seqs.get("Idle")); ad.set_editor_property("graze", seqs.get("Graze", seqs.get("Idle"))); ad.set_editor_property("walk", seqs.get("Walk", seqs.get("Idle")))
        ad.set_editor_property("walk_speed", float(R.get("walk_speed_cm_s", 40.0))); ad.set_editor_property("scale", 1.0); ad.set_editor_property("mesh_yaw", 0.0)
        ad.set_editor_property("half_size", unreal.Vector2D(sz["length_x"] * 0.5, sz["width_y"] * 0.5))
        ad.set_editor_property("pen_min", PEN[name][0]); ad.set_editor_property("pen_max", PEN[name][1])
        made.append(ad)
    order = ["Chicken", "Pig", "Goat", "Cow", "Rabbit"]
    new = made + kept
    new.sort(key=lambda a: ("_" in str(a.get_editor_property("name")), order.index(str(a.get_editor_property("name")).split("_")[0]) if str(a.get_editor_property("name")).split("_")[0] in order else 9))
    g.set_editor_property("town_animals", new)
    REPORT.append(f"pens: {[str(a.name) for a in new]} (was {[str(a.name) for a in old]})")
    # the wilds' hare: from the rabbit, as 890 makes it
    rab = next((a for a in made if str(a.name) == "Rabbit"), None)
    fa = list(g.get_editor_property("wild_fauna"))
    hi = next((i for i, f in enumerate(fa) if str(f.name) == "Hare"), -1)
    if rab and hi >= 0:
        F = fa[hi]
        F.mesh = rab.mesh; F.idle = rab.idle; F.eat = rab.graze; F.walk = rab.walk; F.run = rab.walk
        F.scale = rab.scale * 1.15; F.mesh_yaw = rab.mesh_yaw
        F.walk_speed = max(rab.walk_speed, 30.0); F.walk_clip_speed = max(rab.walk_speed, 1.0) / max(rab.scale, 0.1)
        F.run_clip_speed = 140.0 / max(rab.scale, 0.1) * (rab.walk_speed / 35.26)          # (890's 140 for a clip of 35 cm/s, this clip's share of it)
        fa[hi] = F; g.set_editor_property("wild_fauna", fa)
        REPORT.append(f"hare: the Tripo rabbit, walk clip {F.walk_clip_speed:.1f} cm/s")
    # the stable's horse
    if "Horse" in KINDS:
        mesh, seqs, _a = assets_of("Horse")
        if mesh:
            d = g.get_editor_property("horse_def")
            d.set_editor_property("mesh", mesh); d.set_editor_property("mesh_b", mesh)
            for k in ("Idle", "Walk", "Run", "Canter"): d.set_editor_property(k.lower(), seqs.get(k))
            d.set_editor_property("walk_clip_speed", float(J["Horse"]["walk_speed_cm_s"])); d.set_editor_property("run_clip_speed", float(J["Horse"].get("run_speed_cm_s", 260.0)))
            # (the list of 2026-11-12: the canter, from 4 m/s; the gallop from 13 (913's numbers))
            d.set_editor_property("canter_clip_speed", float(J["Horse"].get("canter_speed_cm_s", 650.0)))
            d.set_editor_property("canter_from", 400.0); d.set_editor_property("gallop_from", 1300.0 if seqs.get("Canter") else 250.0)
            d.set_editor_property("saddle_bone", "saddle")
            g.set_editor_property("horse_def", d)
            REPORT.append(f"horse: {mesh.get_name()}, clips {sorted(seqs)}, walk {J['Horse']['walk_speed_cm_s']} / canter {J['Horse'].get('canter_speed_cm_s')} / run {J['Horse'].get('run_speed_cm_s')} cm/s, saddle {J['Horse']['fit'].get('saddle_top_cm')} cm")
    g.modify(); les.save_current_level()
    del g, old, kept, made, new, rab, fa
print("TRIPO " + " | ".join(REPORT))
for _n in ("mesh", "seqs", "a", "mat", "tex", "d", "F", "_a", "s", "ad", "ms"):
    globals().pop(_n, None)
import gc
gc.collect()
