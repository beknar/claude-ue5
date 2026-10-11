"""sf-city-level_Cine: start Simulate and record the three demo actors (712) and the two timed doors from the first frame
(armed before the game world exists). Logs 'SFCPATH saved' (or 'SFCREC failed') and writes
SourceArt/sf_city/cine_demo_path.json for 714. Stop Simulate afterwards. Keeps its namespace (tick callback)."""
import unreal, json
__keep__ = True
G = {}
S = {"rows": [], "ev": [], "seen": set()}
END = 21.2
def arm(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    unreal.unregister_slate_post_tick_callback(S["arm"])
    G["w"] = w
    G["demo"] = sorted([a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Character) if a.get_actor_label().startswith("Demo_")], key=lambda a: a.get_actor_label())
    G["doors"] = [a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor) if a.get_class().get_name() == "BP_SciFiDoor_C" and a.get_editor_property("AutoOpenAt") >= 0]
    unreal.log("SFCREC armed at %.2f, demos %s" % (unreal.GameplayStatics.get_time_seconds(w), [a.get_actor_label() for a in G["demo"]]))
    S["h"] = unreal.register_slate_post_tick_callback(tick)
def tick(dt):
    try: body()
    except Exception as e:
        unreal.unregister_slate_post_tick_callback(S["h"]); G.clear(); unreal.log_error("SFCREC failed: " + str(e))
def body():
    t = unreal.GameplayStatics.get_time_seconds(G["w"])
    row = [round(t, 3)]
    for a in G["demo"]:
        l = a.get_actor_location(); v = a.get_velocity()
        row.append([round(l.x, 1), round(l.y, 1), round(l.z, 1), round(a.get_actor_rotation().yaw, 1), round((v.x ** 2 + v.y ** 2) ** 0.5), round(v.z), a.get_editor_property("hidden")])
    row.append([round(d.get_editor_property("Alpha"), 3) for d in G["doors"]])
    S["rows"].append(row)
    for d in G["doors"]:
        if d.get_editor_property("Alpha") > 0.9 and d.get_actor_label() not in S["seen"]: S["seen"].add(d.get_actor_label()); S["ev"].append(f"{d.get_actor_label()} open at {t:.2f}")
    if t > END:
        unreal.unregister_slate_post_tick_callback(S["h"])
        json.dump({"labels": [a.get_actor_label() for a in G["demo"]], "doors": [d.get_actor_label() for d in G["doors"]], "rows": S["rows"], "events": S["ev"]},
                  open(r"E:\code\claude-ue5\claude_ue5\SourceArt\sf_city\cine_demo_path.json", "w"))
        unreal.log("SFCPATH saved %d rows | %s" % (len(S["rows"]), " | ".join(S["ev"])))
        G.clear()
S["arm"] = unreal.register_slate_post_tick_callback(arm)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_play_simulate()
print("simulate requested, recorder armed")
