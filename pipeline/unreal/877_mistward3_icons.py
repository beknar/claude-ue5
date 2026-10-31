"""mistward_castle's pictures for the user's list of 2026-10-30 (docs/improvements3.txt): the harvested parts (harvest_<part>),
the scrolls by their spell's type (scroll_<type>) and the Summoner's five summons (summon_1 .. summon_5), painted by
blender_numpy/rdm4_ui_gen.py (ui_art.json's elements of those names) and cut by rdm4_ui_cut.py --export into <dir>.

    877_mistward3_icons.py <dir> [<more dirs>]     (play stopped)

Each <dir>/<name>.png of those prefixes (and, from any other dir given, 874's chi_ / ability_ / ma_ pictures: 826 mistward
makes the menu's UIArt again from level 4's and drops them) becomes /Game/RandomDungeon/UI/T_RDM4_<name> (a UI texture, as
874's) and an entry of that name in the UIArt of mistward_castle's generator (875 names the items' and scrolls' Icon, 876 the
summons') and of its menu's ARDHeroSelect (the Summoner's card: her weapons' pictures). Saves both maps; ends on
mistward_castle."""
import unreal, sys, os
DIRS = [os.path.abspath(d) for d in sys.argv[1:]]
assert DIRS, "877: give the folder of the cut pictures"
PREFIX = ("harvest_", "scroll_", "summon_", "chi_", "ability_", "ma_")
MAP = "/Game/RandomDungeon/Maps/mistward_castle"; SEL = "/Game/RandomDungeon/Maps/mistward_castle_select"
DEST = "/Game/RandomDungeon/UI"
EAL = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
src = {}
for d in DIRS:
    for f in sorted(os.listdir(d)):
        if f.endswith(".png") and f.startswith(PREFIX): src.setdefault(f[:-4], os.path.join(d, f))
assert any(n.startswith(PREFIX[:3]) for n in src), "877: no harvest_ / scroll_ / summon_ pictures in " + ", ".join(DIRS)
tasks = []
for n, p in src.items():
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", p); t.set_editor_property("destination_path", DEST)
    t.set_editor_property("destination_name", "T_RDM4_" + n); t.set_editor_property("replace_existing", True)
    t.set_editor_property("automated", True); t.set_editor_property("save", False); tasks.append(t)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
tex = {}
for n in src:
    a = unreal.load_asset(f"{DEST}/T_RDM4_{n}")
    if not a: raise SystemExit(f"877: {n} was not imported")
    a.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    a.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
    a.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    a.set_editor_property("never_stream", True); a.set_editor_property("srgb", True)
    a.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP); a.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
    EAL.save_loaded_asset(a, False); tex[n] = a
def put(ua):
    for n, a in tex.items():
        art = unreal.RDUIArt(); art.set_editor_property("texture", a)
        art.set_editor_property("border", unreal.Vector4(0, 0, 0, 0)); art.set_editor_property("inner", unreal.Vector4(0, 0, 1, 1))
        ua[unreal.Name(n)] = art
    return ua
if not ues.get_editor_world().get_path_name().startswith(MAP + "."): les.load_level(MAP)
gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
gen.set_editor_property("ui_art", put(gen.get_editor_property("ui_art"))); gen.modify(); les.save_current_level()
have = {str(k) for k in gen.get_editor_property("ui_art").keys()}
want = {str(i.icon) for i in gen.get_editor_property("items") if i.kind in (unreal.RDItemKind.SCROLL, unreal.RDItemKind.COMPONENT)}
want |= {str(w.icon) for h in gen.get_editor_property("heroes") for w in list(h.weapons) + list(h.locked_weapons)}
print(f"877 mistward_castle: {len(tex)} pictures | items' and heroes' icons without one: {sorted(i for i in want if i not in have and i != 'None')}")
del gen
if EAL.does_asset_exist(SEL):
    les.load_level(SEL)
    sel = next((a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDHeroSelect)), None)
    if sel is not None:
        sel.set_editor_property("ui_art", put(sel.get_editor_property("ui_art"))); sel.modify(); les.save_current_level()
        print(f"877 mistward_castle_select: {len(tex)} pictures | heroes {[str(h.name) for h in sel.get_editor_property('heroes')]}")
        del sel
les.load_level(MAP)
import gc
del tex
gc.collect()
