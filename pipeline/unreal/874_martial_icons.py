"""The Martial Artist's pictures (the user's of 2026-10-29: "change the attack icons to reflect the kind of attack it is"): her
ten chi attacks (chi_<move>: the wind round a fist, lightning round a leg, ...) and the quick bar's two abilities
(ability_dash, ability_dodge) and her fists (ma_fists), painted by blender_numpy/rdm4_ui_gen.py (ui_art.json's elements of those names) and cut by
rdm4_ui_cut.py --export into <dir>.

    874_martial_icons.py <dir>     (play stopped)

Each <dir>/<name>.png becomes /Game/RandomDungeon/UI/T_RDM4_<name> (a UI texture, as 830's and 867's) and an entry of that
name in the generator's UIArt on mistward_castle and martial_arts (872 names the chi weapons' Icon chi_<move>; the HUD draws
an ability's slot from ability_<name>). Saves both maps; the editor ends on mistward_castle."""
import unreal, sys, os
DIR = os.path.abspath(sys.argv[1])
MAPS = ["/Game/RandomDungeon/Maps/mistward_castle", "/Game/RandomDungeon/Maps/martial_arts"]
DEST = "/Game/RandomDungeon/UI"
EAL = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
names = sorted(f[:-4] for f in os.listdir(DIR) if f.endswith(".png") and f.startswith(("chi_", "ability_", "ma_")))
assert names, "no chi_ / ability_ pictures in " + DIR
tasks = []
for n in names:
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", os.path.join(DIR, n + ".png")); t.set_editor_property("destination_path", DEST)
    t.set_editor_property("destination_name", "T_RDM4_" + n); t.set_editor_property("replace_existing", True)
    t.set_editor_property("automated", True); t.set_editor_property("save", False); tasks.append(t)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
tex = {}
for n in names:
    a = unreal.load_asset(f"{DEST}/T_RDM4_{n}")
    if not a: raise SystemExit(f"874: {n} was not imported")
    a.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    a.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
    a.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    a.set_editor_property("never_stream", True); a.set_editor_property("srgb", True)
    a.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP); a.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
    EAL.save_loaded_asset(a, False); tex[n] = a
for MAP in MAPS:
    if not EAL.does_asset_exist(MAP): print("874 (no", MAP, ")"); continue
    if not ues.get_editor_world().get_path_name().startswith(MAP + "."): les.load_level(MAP)
    gen = next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    ua = gen.get_editor_property("ui_art")
    for n, a in tex.items():
        art = unreal.RDUIArt(); art.set_editor_property("texture", a)
        art.set_editor_property("border", unreal.Vector4(0, 0, 0, 0)); art.set_editor_property("inner", unreal.Vector4(0, 0, 1, 1))
        ua[unreal.Name(n)] = art
    gen.set_editor_property("ui_art", ua); gen.modify(); les.save_current_level()
    have = {str(k) for k in gen.get_editor_property("ui_art").keys()}
    hero = next((h for h in gen.get_editor_property("heroes") if str(h.name) == "MartialArtist"), None)
    icons = [str(w.icon) for w in list(hero.weapons) + list(hero.locked_weapons)] if hero else []
    print(f"874 {MAP.rsplit('/', 1)[1]}: {len(names)} pictures in UIArt | her weapons' icons without one: {[i for i in icons if i not in have and i != 'None']}")
    del gen, ua
# (the castle's menu: its turntable's card shows her weapons with their pictures (826 copies the heroes there))
SEL = "/Game/RandomDungeon/Maps/mistward_castle_select"
if EAL.does_asset_exist(SEL):
    les.load_level(SEL)
    sel = next((a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if isinstance(a, unreal.RDHeroSelect)), None)
    if sel is not None:
        ua = sel.get_editor_property("ui_art")
        for n, a in tex.items():
            art = unreal.RDUIArt(); art.set_editor_property("texture", a)
            art.set_editor_property("border", unreal.Vector4(0, 0, 0, 0)); art.set_editor_property("inner", unreal.Vector4(0, 0, 1, 1))
            ua[unreal.Name(n)] = art
        sel.set_editor_property("ui_art", ua); sel.modify(); les.save_current_level()
        print(f"874 mistward_castle_select: {len(names)} pictures in the menu's UIArt | heroes {[str(h.name) for h in sel.get_editor_property('heroes')]}")
        del sel, ua
if not ues.get_editor_world().get_path_name().startswith(MAPS[0] + "."): les.load_level(MAPS[0])
import gc
del tex
gc.collect()
