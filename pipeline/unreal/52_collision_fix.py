"""Full-precision Nanite fallback (used for complex collision) on terrain + rocks; re-probe ground heights."""
import json, unreal
W = "/Game/Fig4/World/Meshes"
for k in ("SM_Terrain", "SM_Rock_A", "SM_Rock_B", "SM_Rock_C"):
    sm = unreal.load_asset(f"{W}/{k}/StaticMeshes/{k}")
    ns = sm.get_editor_property("nanite_settings")
    print(k, "before", ns.export_text()[:300])
    for p, v in (("fallback_relative_error", 0.0), ("fallback_percent_triangles", 1.0)):
        try: ns.set_editor_property(p, v)
        except Exception as e: print(p, e)
    try: ns.set_editor_property("fallback_target", unreal.NaniteFallbackTarget.RELATIVE_ERROR)
    except Exception as e: print("target", e)
    sm.set_editor_property("nanite_settings", ns)
    unreal.EditorAssetLibrary.save_loaded_asset(sm)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
PL = json.load(open(r"E:\code\claude-ue5\claude_ue5\SourceArt\terrain\placements.json"))
for px, py, pz in PL["probe"] + [[0, 0, PL["start_z"]], [2500, 400 * 0.841, 0]]:
    hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(px, py, 20000), unreal.Vector(px, py, -20000),
                                                 unreal.TraceTypeQuery.ECC_VISIBILITY, True, [], unreal.DrawDebugTrace.NONE, True)
    t = hit.to_tuple() if hit else None
    print("probe", px, py, "pred", round(pz, 1), "trace", round(t[4].z, 1) if t else None, t[9].get_actor_label() if t and t[9] else "")
