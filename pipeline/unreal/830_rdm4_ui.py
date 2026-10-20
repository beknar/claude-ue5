"""random_dungeonmagic_level4's painted interface: imports the pieces and gives them to the level and its menu.

    830_rdm4_ui.py <export_dir> [fonts_dir]

<export_dir> is what pipeline/blender_numpy/rdm4_ui_cut.py --export wrote: <piece>.png and layout.json (each
piece's stretch border and a frame's open inside; which icon each item and each hero's weapon shows). Each
picture becomes /Game/RandomDungeon/UI/T_RDM4_<piece> (a UI texture: no mipmaps, never streamed, full colour
with alpha), replaced if it is there. Then:
- random_dungeonmagic_level4: the generator's UIArt (piece -> texture, border, inner), its Items' Icon and
  each hero's weapons' Icon (layout's _icons and _weapons; a weapon by "<hero>/<weapon name>");
- random_dungeonmagic_level4_select: the ARDHeroSelect's UIArt and its heroes' weapons' Icon.
And the lettering: the fonts that pipeline/blender_numpy/rdm4_fonts.py fetched (fonts_dir, by default
SourceArt/random_dungeon_magic4/fonts) become /Game/RandomDungeon/UI/Fonts/FF_RDM4_<file> (font faces), and both
levels' UIFonts get them by role (FONTS: the face and its size against the engine's Roboto, so that the HUD's scales
give letters as tall as before: Alegreya's are smaller at the same point size).
Both levels are saved; the editor ends on random_dungeonmagic_level4. The HUDs draw a piece where UIArt has
it and their plain boxes where it has not.
"""
import json, os, sys
import unreal

SRC = sys.argv[1]
FONT_DIR = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "claude_ue5", "SourceArt", "random_dungeon_magic4", "fonts")
# role -> (file, size against Roboto, where its capitals start below its line's top in em): Cinzel for titles, names,
# keys and numbers alone; Alegreya for the text; Alegreya SC for labels. Measured with FreeType (Pillow): Roboto's
# x-height is 0.53 em, Alegreya's 0.47, Alegreya SC's small capitals 0.52, Cinzel's capitals Roboto's height; Roboto's
# capitals start 0.217 em below its line's top, Cinzel's 0.276, Alegreya's 0.369, Alegreya SC's 0.367. The HUD draws a
# face higher by the difference (Lift, in Roboto's em) so that its capitals are where Roboto's were.
FONTS = {"title": ("Cinzel-700", 1.0, 0.276), "text": ("Alegreya-500", 1.12, 0.369), "label": ("AlegreyaSC-700", 1.05, 0.367)}
ROBOTO_CAP_TOP = 0.217
FDEST = "/Game/RandomDungeon/UI/Fonts"
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

# ---- the fonts
ftasks = []
for role, (fn, size, cap) in FONTS.items():
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", os.path.abspath(os.path.join(FONT_DIR, fn + ".ttf")))
    t.set_editor_property("destination_path", FDEST)
    t.set_editor_property("destination_name", "FF_RDM4_" + fn.replace("-", "_"))
    t.set_editor_property("replace_existing", True)
    t.set_editor_property("automated", True)
    t.set_editor_property("save", False)
    ftasks.append(t)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(ftasks)
faces = {}
for role, (fn, size, cap) in FONTS.items():
    a = unreal.load_asset(f"{FDEST}/FF_RDM4_{fn.replace('-', '_')}")
    if not isinstance(a, unreal.FontFace):
        raise SystemExit(f"830: {fn} was not imported as a font face ({a})")
    EAL.save_loaded_asset(a, False)
    faces[role] = (a, size, cap * size - ROBOTO_CAP_TOP)
print("830 fonts:", {r: f[0].get_name() for r, f in faces.items()})


def font_map():
    out = {}
    for role, (face, size, rise) in faces.items():
        f = unreal.RDUIFont()
        f.set_editor_property("face", face)
        f.set_editor_property("size", float(size))
        f.set_editor_property("lift", float(rise))
        out[role] = f
    return out


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
sel.set_editor_property("ui_fonts", font_map())
sel.set_editor_property("heroes", heroes_with_icons(list(sel.get_editor_property("heroes"))))
les.save_current_level()
print("830 menu:", len(sel.get_editor_property("ui_art")), "pieces")

# ---- the dungeon
unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
gen = actors(unreal.RDDungeonGenerator)[0]
gen.set_editor_property("ui_art", art_map())
gen.set_editor_property("ui_fonts", font_map())
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
print("830 dungeon fonts:", {str(k): (v.get_editor_property("face").get_name(), round(v.get_editor_property("size"), 3), round(v.get_editor_property("lift"), 3)) for k, v in gen.get_editor_property("ui_fonts").items()})
print("830 item icons:", sum(1 for v in icons.values() if v != "None"), "of", len(icons))
print("830 weapon icons:", wicons)
del sel, gen, tex, ua, items, faces
