"""random_level_Cine: start Simulate and record Demo_RL_Fem5 (754) and the cells the generator adds, from the first frame
(armed before the game world exists). Writes SourceArt/random_level/cine_demo_path.json for 756 and logs
'RLPATH saved' (or 'RLREC failed'). Stop Simulate afterwards. Keeps its namespace (tick callback)."""
import unreal, json
__keep__ = True
G = {}
S = {"rows": [], "ev": [], "known": set()}
END = 21.0
OUT = r"E:\code\claude-ue5\claude_ue5\SourceArt\random_level\cine_demo_path.json"
def arm(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    unreal.unregister_slate_post_tick_callback(S["arm"])
    G["w"] = w
    G["demo"] = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Character) if a.get_actor_label() == "Demo_RL_Fem5")
    G["gen"] = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.RTTownGenerator)[0]
    S["known"] = {(c.x, c.y) for c in G["gen"].get_cell_coords()}
    unreal.log("RLREC armed at %.2f, %d cells" % (unreal.GameplayStatics.get_time_seconds(w), len(S["known"])))
    S["h"] = unreal.register_slate_post_tick_callback(tick)
def tick(dt):
    try: body()
    except Exception as e:
        unreal.unregister_slate_post_tick_callback(S["h"]); G.clear(); unreal.log_error("RLREC failed: " + str(e))
def body():
    t = unreal.GameplayStatics.get_time_seconds(G["w"])
    a = G["demo"]; l = a.get_actor_location(); v = a.get_velocity()
    S["rows"].append([round(t, 3), round(l.x, 1), round(l.y, 1), round(l.z, 1), round(a.get_actor_rotation().yaw, 1), round((v.x ** 2 + v.y ** 2) ** 0.5)])
    now = {(c.x, c.y) for c in G["gen"].get_cell_coords()}
    for c in sorted(now - S["known"]):
        cell = G["gen"].get_cell(unreal.IntPoint(*c))
        S["ev"].append({"t": round(t, 3), "cell": list(c), "at": [round(l.x), round(l.y)], "buildings": cell.get_num_buildings(),
                        "instances": cell.get_editor_property("num_instances"), "blocks": list(cell.get_editor_property("block_types")),
                        "ms": round(cell.get_editor_property("generate_ms"))})
    S["known"] = now
    if t > END:
        unreal.unregister_slate_post_tick_callback(S["h"])
        json.dump({"rows": S["rows"], "events": S["ev"], "start_cells": sorted(S["known"] - {tuple(e["cell"]) for e in S["ev"]})}, open(OUT, "w"))
        unreal.log("RLPATH saved %d rows | %s" % (len(S["rows"]), " | ".join(f"{e['cell']} at {e['t']:.2f}s ({e['buildings']} bld, {e['ms']} ms)" for e in S["ev"])))
        G.clear()
S["arm"] = unreal.register_slate_post_tick_callback(arm)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_play_simulate()
print("simulate requested, recorder armed")
