"""A picture imported as a UI texture, as the HUD draws the interface's pictures (883's settings): shared by 923's purse and 926's
scenery things."""
import unreal
eal = unreal.EditorAssetLibrary


def ui_texture(png, dest, name):
    """a picture as a UI texture (883's settings: no mips, never streamed, sRGB, clamped)"""
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", png); t.set_editor_property("destination_path", dest); t.set_editor_property("destination_name", name)
    t.set_editor_property("replace_existing", True); t.set_editor_property("automated", True); t.set_editor_property("save", False)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    a = unreal.load_asset(f"{dest}/{name}")
    assert a, f"{png} was not imported"
    a.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    a.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
    a.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    a.set_editor_property("never_stream", True); a.set_editor_property("srgb", True)
    a.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP); a.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
    eal.save_loaded_asset(a, False)
    return a
