"""random_dungeon_level_Cine: start Simulate and record Demo_RD_Fem5 (773), the sections the generator adds, the dungeon
map data and the monsters near her, from the first frame (armed before the game world exists). Writes
SourceArt/random_dungeon/cine_demo_path.json for 775 and the reel overlay, logs 'RDPATH saved' (or 'RDREC failed').
Stop Simulate afterwards. Keeps its namespace (tick callback)."""
import unreal, json
__keep__ = True
G = {}
S = {"rows": [], "ev": [], "mon": [], "known": set()}
END = 21.0
OUT = r"E:\code\claude-ue5\claude_ue5\SourceArt\random_dungeon\cine_demo_path.json"
def arm(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    unreal.unregister_slate_post_tick_callback(S["arm"])
    G["w"] = w
    G["demo"] = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Character) if a.get_actor_label() == "Demo_RD_Fem5")
    G["gen"] = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.RDDungeonGenerator)[0]
    S["known"] = {(c.x, c.y) for c in G["gen"].get_section_coords()}
    unreal.log("RDREC armed at %.2f, %d sections" % (unreal.GameplayStatics.get_time_seconds(w), len(S["known"])))
    S["h"] = unreal.register_slate_post_tick_callback(tick)
def tick(dt):
    try: body()
    except Exception as e:
        unreal.unregister_slate_post_tick_callback(S["h"]); G.clear(); unreal.log_error("RDREC failed: " + str(e))
def mapdata():
    out = []
    for c, m in G["gen"].get_editor_property("map_data").items():
        rects = [[r.min.x, r.min.y, r.max.x, r.max.y, str(r.kind).split(".")[-1], bool(r.corridor)] for r in m.rects]
        out.append({"coord": [c.x, c.y], "rects": rects, "doors": [[round(d.x), round(d.y)] for d in m.doors], "start": bool(m.start)})
    return out
def body():
    t = unreal.GameplayStatics.get_time_seconds(G["w"])
    a = G["demo"]; l = a.get_actor_location(); v = a.get_velocity()
    S["rows"].append([round(t, 3), round(l.x, 1), round(l.y, 1), round(l.z, 1), round(a.get_actor_rotation().yaw, 1), round((v.x ** 2 + v.y ** 2) ** 0.5)])
    if len(S["rows"]) % 3 == 0:
        S["mon"].append([round(t, 3)] + [[round(m.get_actor_location().x), round(m.get_actor_location().y)] for m in G["gen"].get_monsters()
                                        if (m.get_actor_location() - l).length() < 4000])
    now = {(c.x, c.y) for c in G["gen"].get_section_coords()}
    for c in sorted(now - S["known"]):
        sec = G["gen"].get_section(unreal.IntPoint(*c))
        S["ev"].append({"t": round(t, 3), "section": list(c), "at": [round(l.x), round(l.y)], "rooms": sec.get_num_rooms(),
                        "doors": sec.get_num_doors()})
    S["known"] = now
    for e in S["ev"]:
        if "monsters" not in e:
            sec = G["gen"].get_section(unreal.IntPoint(*e["section"]))
            if sec and not sec.is_building():
                e.update({"monsters": len(sec.get_editor_property("spawned_monsters")), "containers": sec.get_num_containers(), "doors": sec.get_num_doors(),
                          "instances": sec.get_editor_property("num_instances"), "lights": sec.get_editor_property("num_lights"), "built_at": round(t, 3)})
    if t > END:
        unreal.unregister_slate_post_tick_callback(S["h"])
        json.dump({"rows": S["rows"], "events": S["ev"], "monsters": S["mon"], "map": mapdata(), "tile": G["gen"].get_editor_property("tile_size"),
                   "section_tiles": G["gen"].get_editor_property("section_tiles")}, open(OUT, "w"))
        unreal.log("RDPATH saved %d rows | %s" % (len(S["rows"]), " | ".join(f"{e['section']} at {e['t']:.2f}s built {e.get('built_at')}" for e in S["ev"])))
        G.clear()
S["arm"] = unreal.register_slate_post_tick_callback(arm)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_play_simulate()
print("simulate requested, recorder armed")
