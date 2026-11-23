"""The rules for which materials Nanite can draw and which ones move their vertices: one place for the stage that makes meshes
Nanite (944) and the test that checks it (888 nanite16) (PR #114's second review: the test's copy of the blend rule could drift
from the stage's).
"""
import unreal

DRAWN = (unreal.BlendMode.BLEND_OPAQUE, unreal.BlendMode.BLEND_MASKED)


def blend_of(m):
    """the blend mode a material is drawn with: an instance's own override (up its parents) before its base material's"""
    x = m
    while isinstance(x, unreal.MaterialInstance):
        try:
            o = x.get_editor_property("base_property_overrides")
            if o.get_editor_property("override_blend_mode"): return o.get_editor_property("blend_mode")
        except Exception:
            pass
        x = x.get_editor_property("parent")
    b = m.get_base_material()
    return b.get_editor_property("blend_mode") if b else unreal.BlendMode.BLEND_OPAQUE


def see_through(mats):
    """a material drawn translucent (or additive, modulate): Nanite cannot draw it"""
    return any(m and blend_of(m) not in DRAWN for m in mats)


def moves_vertices(m):
    """whether a material's base offsets its vertices (world position offset connected). A base built on material attributes cannot
    be read this way: it counts as moving (a bound on a still material costs only a larger box; none on a swaying one gets it culled)"""
    b = m.get_base_material() if m else None
    if not b: return False
    try:
        if b.get_editor_property("use_material_attributes"): return True
        return unreal.MaterialEditingLibrary.get_material_property_input_node(b, unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET) is not None
    except Exception:
        return True


def shape_of(voxel):
    return unreal.NaniteShapePreservation.VOXELIZE if voxel else unreal.NaniteShapePreservation.NONE


def is_voxel(mesh):
    """Nanite with the voxel shape preservation (Nanite foliage); None when the setting cannot be read"""
    ns = mesh.get_editor_property("nanite_settings")
    try:
        return ns.enabled and ns.get_editor_property("shape_preservation") == unreal.NaniteShapePreservation.VOXELIZE
    except Exception:
        return None
