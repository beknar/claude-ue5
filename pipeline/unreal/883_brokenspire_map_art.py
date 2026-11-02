"""Brokenspire's papyrus map (docs/brokenspire.txt: "the overhead map has a papyrus or scroll look with stylized icons that look
like the actual buildings and labels on those icons of what the buildings do"): the sheet of papyrus (map_papyrus) and a
picture of each kind of building and outdoor thing (mapicon_<kind>), painted by blender_numpy/rdm4_ui_gen.py from
SourceArt/brokenspire/map_art.json and cut by rdm4_ui_cut.py --export into <dir>.

    883_brokenspire_map_art.py <dir>     (play stopped)

The colour set (2026-11-02, the Fairhill reference's look; SourceArt/brokenspire/map_art_colour.json: mapc_*) the same way;
with mapc_grass and mapc_parchment there, DrawTownMap draws the colour map (DrawTownMapColour).
Each <dir>/map_papyrus.png, <dir>/mapicon_*.png and <dir>/mapc_*.png becomes /Game/RandomDungeon/UI/Brokenspire/T_BS_<name> (a UI texture)
and an entry of that name in the UIArt of Brokenspire's generator (ARDHUD's DrawTownMap and DrawTownMinimap draw them).
Saves the map."""
import unreal, sys, os
D = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else None
assert D and os.path.isdir(D), "883: give the folder of the cut pictures"
MAP = "/Game/RandomDungeon/Maps/brokenspire"; DEST = "/Game/RandomDungeon/UI/Brokenspire"
EAL = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
src = {f[:-4]: os.path.join(D, f) for f in sorted(os.listdir(D)) if f.endswith(".png") and (f.startswith(("mapicon_", "mapc_")) or f == "map_papyrus.png")}
# (the ink set: map_papyrus and mapicon_*; the colour set of 2026-11-02 (map_art_colour.json, the Fairhill reference's look):
# mapc_*, whose ground textures (grass, earth, cobbles, the wall's stone) repeat over the map, mirrored)
assert ("map_papyrus" in src or "mapc_parchment" in src) and len(src) > 10, f"883: pictures missing in {D}: {sorted(src)}"
WRAP = {"mapc_grass", "mapc_dirt", "mapc_cobble", "mapc_wallstone"}
tasks = []
for n, p in src.items():
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", p); t.set_editor_property("destination_path", DEST)
    t.set_editor_property("destination_name", "T_BS_" + n); t.set_editor_property("replace_existing", True)
    t.set_editor_property("automated", True); t.set_editor_property("save", False); tasks.append(t)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
tex = {}
for n in src:
    a = unreal.load_asset(f"{DEST}/T_BS_{n}")
    if not a: raise SystemExit(f"883: {n} was not imported")
    a.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    a.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
    a.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    a.set_editor_property("never_stream", True); a.set_editor_property("srgb", True)
    # (mirrored: the painted textures' edges do not match, mirrored they meet)
    ad = unreal.TextureAddress.TA_MIRROR if n in WRAP else unreal.TextureAddress.TA_CLAMP
    a.set_editor_property("address_x", ad); a.set_editor_property("address_y", ad)
    EAL.save_loaded_asset(a, False); tex[n] = a
if not ues.get_editor_world().get_path_name().startswith(MAP + "."): les.load_level(MAP)
gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
ua = gen.get_editor_property("ui_art")
for n, a in tex.items():
    art = unreal.RDUIArt(); art.set_editor_property("texture", a)
    art.set_editor_property("border", unreal.Vector4(0, 0, 0, 0)); art.set_editor_property("inner", unreal.Vector4(0, 0, 1, 1))
    ua[unreal.Name(n)] = art
gen.set_editor_property("ui_art", ua); gen.modify(); les.save_current_level()
print(f"883 brokenspire: {len(tex)} pictures: {sorted(tex)}")
import gc
del gen, tex, ua
gc.collect()
