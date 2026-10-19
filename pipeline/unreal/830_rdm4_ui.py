"""random_dungeonmagic_level4's painted interface: imports the pieces and gives them to the level and its menu.

    830_rdm4_ui.py <export_dir>

<export_dir> is what pipeline/blender_numpy/rdm4_ui_cut.py --export wrote: <piece>.png and layout.json (each
piece's stretch border and a frame's open inside; which icon each item and each hero's weapon shows). Each
picture becomes /Game/RandomDungeon/UI/T_RDM4_<piece> (a UI texture: no mipmaps, never streamed, full colour
with alpha), replaced if it is there. Then:
- random_dungeonmagic_level4: the generator's UIArt (piece -> texture, border, inner), its Items' Icon and
  each hero's weapons' Icon (layout's _icons and _weapons; a weapon by "<hero>/<weapon name>");
- random_dungeonmagic_level4_select: the ARDHeroSelect's UIArt and its heroes' weapons' Icon.
Both levels are saved; the editor ends on random_dungeonmagic_level4. The HUDs draw a piece where UIArt has
it and their plain boxes where it has not.
"""
import json, os, sys
import unreal

SRC = sys.argv[1]
L = json.load(open(os.path.join(SRC, "layout.json")))
DEST = "/Game/RandomDungeon/UI"
LEVEL = "/Game/RandomDungeon/Maps/random_dungeonmagic_level4"
SELECT = "/Game/RandomDungeon/Maps/random_dungeonmagic_level4_select"
EAL = unreal.EditorAssetLibrary

# ---- the textures
names = [k for k in L if not k.startswith("_")]
tasks = []
for n in names:
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", os.path.abspath(os.path.join(SRC, n + ".png")))
    t.set_editor_property("destination_path", DEST)
    t.set_editor_property("destination_name", "T_RDM4_" + n)
    t.set_editor_property("replace_existing", True)
    t.set_editor_property("automated", True)
    t.set_editor_property("save", False)
    tasks.append(t)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
tex = {}
for n in names:
    a = unreal.load_asset(f"{DEST}/T_RDM4_{n}")
    if not a:
        raise SystemExit(f"830: {n} was not imported")
    a.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    a.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
    a.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    a.set_editor_property("never_stream", True)
    a.set_editor_property("srgb", True)
    a.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP)
    a.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
    EAL.save_loaded_asset(a, False)
    tex[n] = a
print("830 textures:", len(tex))


def art_map():
    out = {}
    for n in names:
        e = L[n]
        art = unreal.RDUIArt()
        art.set_editor_property("texture", tex[n])
        art.set_editor_property("border", unreal.Vector4(*[float(v) for v in e["border"]]))
        art.set_editor_property("inner", unreal.Vector4(*[float(v) for v in e["inner"]]))
        out[n] = art
    return out


def heroes_with_icons(heroes):
    out = []
    for h in heroes:
        ws = []
        for w in h.get_editor_property("weapons"):
            key = f"{h.get_editor_property('name')}/{w.get_editor_property('name')}"
            w.set_editor_property("icon", L["_weapons"].get(key, "None"))
            if key not in L["_weapons"]:
                print("830: no icon for", key)
            ws.append(w)
        h.set_editor_property("weapons", ws)
        out.append(h)
    return out


les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ELS = unreal.EditorLevelLibrary


def actors(cls):
    return [a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if isinstance(a, cls)]


# ---- the menu
unreal.EditorLoadingAndSavingUtils.load_map(SELECT)
sel = actors(unreal.RDHeroSelect)
if not sel:
    raise SystemExit("830: no RDHeroSelect in the menu level")
sel = sel[0]
sel.set_editor_property("ui_art", art_map())
sel.set_editor_property("heroes", heroes_with_icons(list(sel.get_editor_property("heroes"))))
les.save_current_level()
print("830 menu:", len(sel.get_editor_property("ui_art")), "pieces")

# ---- the dungeon
unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
gen = actors(unreal.RDDungeonGenerator)[0]
gen.set_editor_property("ui_art", art_map())
items = []
for it in gen.get_editor_property("items"):
    n = str(it.get_editor_property("name"))
    if n not in L["_icons"]:
        print("830: no icon for item", n)
    it.set_editor_property("icon", L["_icons"].get(n, "None"))
    items.append(it)
gen.set_editor_property("items", items)
gen.set_editor_property("heroes", heroes_with_icons(list(gen.get_editor_property("heroes"))))
les.save_current_level()

# read back
ua = gen.get_editor_property("ui_art")
miss = [n for n in names if n not in [str(k) for k in ua.keys()]]
icons = {str(i.get_editor_property("name")): str(i.get_editor_property("icon")) for i in gen.get_editor_property("items")}
wicons = {f"{h.get_editor_property('name')}/{w.get_editor_property('name')}": str(w.get_editor_property("icon"))
          for h in gen.get_editor_property("heroes") for w in h.get_editor_property("weapons")}
print("830 dungeon:", len(ua), "pieces, missing", miss)
print("830 item icons:", sum(1 for v in icons.values() if v != "None"), "of", len(icons))
print("830 weapon icons:", wicons)
del sel, gen, tex, ua, items
