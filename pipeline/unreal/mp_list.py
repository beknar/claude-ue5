import unreal
print([p for p in dir(unreal.MaterialProperty) if p.startswith("MP_")])
m = unreal.Material()
print([p for p in ("enable_tessellation", "displacement_scaling", "displacement_fade_range", "max_world_position_offset_displacement",
                   "two_sided", "blend_mode", "is_thin_surface", "used_with_hair_strands") ])
for p in dir(m):
    if "isplac" in p or "tessel" in p or "thin" in p.lower():
        print("  prop", p)
