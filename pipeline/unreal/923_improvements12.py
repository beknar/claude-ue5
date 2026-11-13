"""The user's list of 2026-11-12 (docs/improvements12.txt), in phases (the user's choices: memory improvements12-plan).
Steps (name them; several in one run):
  icons <dir>  the purse's picture, icon_gold (ui_art.json's, painted by rdm4_ui_gen.py --only icon_gold and exported by
           rdm4_ui_cut.py --export <dir>): /Game/RandomDungeon/UI/T_RDM4_icon_gold, named in every game map's UIArt (the
           inventory draws it beside her gold)
C++ first (RD/RDList12.cpp: the pointer over the big map, rd.MapTeleport's click; RDHUD.cpp's DrawMenuGrid: the saves as cards;
RDWildHUD.cpp: the wilds' map drawn only inside the scroll's edge, at the insets bs_scroll.py measures on its picture).
Args: steps [dir]"""
import os, sys, unreal
eal = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
STEPS = [s for a in sys.argv[1:] if not os.path.isabs(a) for s in a.split(",") if s]
DIRS = [a for a in sys.argv[1:] if os.path.isabs(a)]
REPORT = []


def ui_texture(png, dest, name):
    """a picture as a UI texture (883's settings: no mips, never streamed, sRGB, clamped)"""
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", png); t.set_editor_property("destination_path", dest); t.set_editor_property("destination_name", name)
    t.set_editor_property("replace_existing", True); t.set_editor_property("automated", True); t.set_editor_property("save", False)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    a = unreal.load_asset(f"{dest}/{name}")
    assert a, f"923: {png} was not imported"
    a.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    a.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
    a.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    a.set_editor_property("never_stream", True); a.set_editor_property("srgb", True)
    a.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP); a.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
    eal.save_loaded_asset(a, False)
    return a


GAME_MAPS = ("mistward_castle", "martial_arts", "brokenspire", "vel_morrath", "war_engine", "sewers", "kethrys_spire", "heaven_fortress")


def each_map(maps, fn, what):
    """fn(gen) on each map that has a generator, saved; its report (918's way)"""
    for m in maps:
        p = "/Game/RandomDungeon/Maps/" + m
        if not eal.does_asset_exist(p): REPORT.append(f"{what} {m}: no map"); continue
        if not ues.get_editor_world().get_path_name().startswith(p + "."): les.load_level(p)
        gen = next((a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator)), None)
        if not gen: REPORT.append(f"{what} {m}: no generator"); continue
        r = fn(gen)
        gen.modify(); les.save_current_level()
        REPORT.append(f"{what} {m}: {r}")
        gen = None
        import gc; gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")


def step_icons():
    # (the list of 2026-11-12: "amount of gold should show up in the inventory screen": it was there, small, beside her title,
    # and the purse's picture it asks for (icon_gold) had never been made: painted (ui_art.json's icon_gold, rdm4_ui_gen.py /
    # rdm4_ui_cut.py --export <dir>) and named in every map's UIArt)
    D = next((d for d in DIRS if os.path.exists(os.path.join(d, "icon_gold.png"))), None)
    assert D, "923 icons <dir with icon_gold.png> (rdm4_ui_cut.py --export)"
    tex = ui_texture(os.path.join(D, "icon_gold.png"), "/Game/RandomDungeon/UI", "T_RDM4_icon_gold")
    def icons(g):
        ua = g.get_editor_property("ui_art")
        art = unreal.RDUIArt(); art.set_editor_property("texture", tex)
        art.set_editor_property("border", unreal.Vector4(0, 0, 0, 0)); art.set_editor_property("inner", unreal.Vector4(0, 0, 1, 1))
        ua[unreal.Name("icon_gold")] = art
        g.set_editor_property("ui_art", ua)
        return "icon_gold"
    each_map(GAME_MAPS, icons, "icons")


for s in STEPS:
    {"icons": step_icons}[s]()
print("923 " + " | ".join(REPORT))
import gc
gc.collect()
