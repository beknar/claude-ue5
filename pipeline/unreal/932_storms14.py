"""The user's list of 2026-11-16 (docs/improvements14.txt; the plan docs/improvements14_plan.md), its tenth phase (item 19): storms
by strength and lightning ("the medium and stronger storms should have varying degrees of lightning and thunder, and if lightning
hits someone, that someone should get damaged"). C++: RD/RDList14j.cpp.

Parts (args):
  sounds  the thunder: SourceArt/wilderness/storms14.json's sets, converted first by
          `rdc_sound_prep.py SourceArt/wilderness/storms14.json SourceArt/wilderness/audio_storm`, imported into
          /Game/RandomDungeon/Audio/Storm as brokenspire's Weather.Thunder and Weather.ThunderFar (flat: the game sets their volume
          by the strike's distance).
  look    the bolt's material M_RD_Lightning14 (unlit, additive, a pale blue glow) and its mesh (the engine's cylinder) on brokenspire.
  data    brokenspire: bLightning14 on, the strengths' weights and scales, the strikes' rates, hurt, damage and distances.
Idempotent: the sets and material made again, the data set anew.
"""
import json, os, sys, gc
import unreal

SA = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "SourceArt")
J = json.load(open(os.path.join(SA, "wilderness", "storms14.json"), encoding="utf-8"))
eal = unreal.EditorAssetLibrary
at = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MAPS = "/Game/RandomDungeon/Maps/"
MAT = "/Game/RandomDungeon/Wild14/M_RD_Lightning14"
REPORT = []


def each(maps, fn, label):
    for m in maps:
        if not eal.does_asset_exist(MAPS + m): REPORT.append(f"{label}: no map {m}"); continue
        les.load_level(MAPS + m); unreal.SystemLibrary.execute_console_command(None, "obj gc")
        g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
        what = fn(g)
        g.modify(); les.save_current_level()
        g = None; gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")
        REPORT.append(f"932 {label} {m}: {what}")


def sounds():
    aud = os.path.join(SA, "wilderness", "audio_storm"); idx = os.path.join(aud, "index.json")
    assert os.path.exists(idx), "run rdc_sound_prep.py SourceArt/wilderness/storms14.json SourceArt/wilderness/audio_storm first"
    I = json.load(open(idx, encoding="utf-8"))
    dest = "/Game/RandomDungeon/Audio/Storm"
    if not eal.does_directory_exist(dest): eal.make_directory(dest)
    made = {}
    for key, spec in J["sets"].items():
        waves = []
        for f in I.get(key, {}).get("files", []):
            t = unreal.AssetImportTask(); t.set_editor_property("filename", os.path.join(aud, f)); t.set_editor_property("destination_path", dest)
            t.set_editor_property("destination_name", "SW_" + f[:-4]); t.set_editor_property("replace_existing", True); t.set_editor_property("automated", True)
            at.import_asset_tasks([t])
            w = unreal.load_asset(f"{dest}/SW_{f[:-4]}")
            if w: w.set_editor_property("looping", False); eal.save_loaded_asset(w, False); waves.append(w)
        assert waves, f"932 sounds: no files for {key}"
        made[key] = (waves, spec)
    def fn(g):
        snd = g.get_editor_property("sounds")
        for key, (waves, spec) in made.items():
            s = unreal.RDSoundSet(); s.set_editor_property("sounds", waves)
            s.set_editor_property("volume", float(spec.get("volume", 1.0))); s.set_editor_property("pitch", float(spec.get("pitch", 1.0)))
            s.set_editor_property("pitch_variation", float(spec.get("pitch_var", 0.05))); s.set_editor_property("inner_radius", float(spec.get("inner", 200.0)))
            s.set_editor_property("falloff_distance", float(spec.get("falloff", 2500.0))); s.set_editor_property("b2d", bool(spec.get("flat", False)))
            snd[unreal.Name(key)] = s
        g.set_editor_property("sounds", snd)
        return ", ".join(f"{k} {len(v[0])} ({', '.join(str(round(w.get_editor_property('duration'), 1)) + ' s' for w in v[0])})" for k, v in made.items())
    each(J["maps"], fn, "sounds")


def material():
    # (unlit, additive, two-sided: a pale blue glow; its strength a parameter)
    folder, name = MAT.rsplit("/", 1)
    if not eal.does_directory_exist(folder): eal.make_directory(folder)
    m = unreal.load_asset(MAT)
    if not m: m = at.create_asset(name, folder, unreal.Material, unreal.MaterialFactoryNew())
    mel.delete_all_material_expressions(m)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
    m.set_editor_property("two_sided", True)
    c = mel.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -500, 0); c.set_editor_property("constant", unreal.LinearColor(0.72, 0.84, 1.0, 1.0))
    p = mel.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -500, 200); p.set_editor_property("parameter_name", "Intensity"); p.set_editor_property("default_value", 80.0)
    mul = mel.create_material_expression(m, unreal.MaterialExpressionMultiply, -250, 100)
    assert mel.connect_material_expressions(c, "", mul, "A") and mel.connect_material_expressions(p, "", mul, "B"), "the bolt's material: a connection failed"
    assert mel.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR), "the bolt's material: emissive not connected"
    print("932 MATERIAL compile (the half-built states' failures before this line are not real)")
    mel.recompile_material(m); eal.save_loaded_asset(m, False)
    return m


def look():
    m = material()
    cyl = unreal.load_asset("/Engine/BasicShapes/Cylinder"); assert cyl
    def fn(g):
        g.set_editor_property("lightning_material14", m); g.set_editor_property("lightning_mesh14", cyl)
        return f"{m.get_name()} on {cyl.get_name()}, {mel.get_statistics(m).num_pixel_shader_instructions} pixel instructions"
    each(J["maps"], fn, "look")


def data_fn(g):
    S, L = J["strengths"], J["lightning"]
    g.set_editor_property("lightning14", True)
    g.set_editor_property("storm_strength_weights14", [float(x) for x in S["storm"]])
    g.set_editor_property("rain_strength_weights14", [float(x) for x in S["rain"]])
    g.set_editor_property("dry_strong_share14", float(S["dry_strong_share"]))
    g.set_editor_property("strength_scale14", [float(x) for x in S["scale"]])
    g.set_editor_property("strikes_per_minute14", [float(x) for x in L["per_minute"]])
    g.set_editor_property("strike_hurt_share14", [float(x) for x in L["hurt_share"]])
    g.set_editor_property("lightning_damage14", [float(x) for x in L["damage"]])
    g.set_editor_property("strike_near_share14", float(L["near_share"]))
    g.set_editor_property("strike_near_cm14", float(L["near_m"]) * 100.0)
    g.set_editor_property("strike_far_cm14", float(L["far_m"]) * 100.0)
    g.set_editor_property("strike_radius_cm14", float(L["radius_m"]) * 100.0)
    g.set_editor_property("thunder_near_cm14", float(L["thunder_near_m"]) * 100.0)
    g.set_editor_property("lightning_sky_boost14", float(L["sky_boost"]))
    return f"lightning on: {L['per_minute']} strikes a minute by strength"


args = sys.argv[1:]
if "sounds" in args: sounds()
if "look" in args: look()
if "data" in args: each(J["maps"], data_fn, "data")
for line in REPORT: print(line)
gc.collect()
