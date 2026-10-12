"""random_isometric_village_level_Cine: start Simulate and record Demo_IV_Fem5 (783), the house she is in, the sections the
generator adds and, at the end, the village map data (buildings, roads, patches, trees, props of every section), from the
first frame (armed before the game world exists). Writes SourceArt/random_isometric_village/cine_demo_path.json for 785
and the reel overlay, logs 'IVPATH saved' (or 'IVREC failed'). Stop Simulate afterwards. Keeps its namespace (tick callback)."""
import unreal, json
__keep__ = True
G = {}
S = {"rows": [], "ev": [], "known": set()}
END = 31.0
OUT = r"E:\code\claude-ue5\claude_ue5\SourceArt\random_isometric_village\cine_demo_path.json"
def arm(dt):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is None: return
    unreal.unregister_slate_post_tick_callback(S["arm"])
    G["w"] = w
    G["demo"] = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Character) if a.get_actor_label() == "Demo_IV_Fem5")
    G["gen"] = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.IVVillageGenerator)[0]
    S["known"] = {(c.x, c.y) for c in G["gen"].get_section_coords()}
    unreal.log("IVREC armed at %.2f, %d sections" % (unreal.GameplayStatics.get_time_seconds(w), len(S["known"])))
    S["h"] = unreal.register_slate_post_tick_callback(tick)
def tick(dt):
    try: body()
    except Exception as e:
        import traceback
        unreal.unregister_slate_post_tick_callback(S["h"]); G.clear(); unreal.log_error("IVREC failed: " + str(e) + traceback.format_exc())
def name(e): return str(e).split(".")[-1].split(":")[0].strip("<> ")
def mapdata():
    out = []
    for c, m in G["gen"].get_editor_property("map_data").items():
        out.append({"coord": [c.x, c.y], "start": bool(m.start), "generated": round(m.generated_time, 3),
                    "buildings": [{"c": [round(b.center.x), round(b.center.y)], "half": [round(b.half.x), round(b.half.y)], "yaw": round(b.yaw, 1), "wall": round(b.wall_height), "roof": round(b.roof_height),
                                   "ridge_y": bool(b.ridge_along_y), "tower": round(b.tower_height), "style": name(b.style), "kind": name(b.kind)} for b in m.buildings],
                    "roads": [{"pts": [[round(p.x), round(p.y)] for p in r.points], "hw": round(r.half_width), "type": int(r.type)} for r in m.roads],
                    "patches": [{"pts": [[round(p.x), round(p.y)] for p in q.points], "type": int(q.type)} for q in m.patches],
                    "trees": [[round(t.p.x), round(t.p.y), round(t.radius), round(t.height), int(t.type)] for t in m.trees],
                    "props": [[round(p.p.x), round(p.p.y), round(p.yaw), int(p.type)] for p in m.props]})
    return out
def body():
    gen = G["gen"]
    t = unreal.GameplayStatics.get_time_seconds(G["w"])
    a = G["demo"]; l = a.get_actor_location(); v = a.get_velocity()
    cur, cs = gen.get_current_building()
    S["rows"].append([round(t, 3), round(l.x, 1), round(l.y, 1), round(l.z, 1), round(a.get_actor_rotation().yaw, 1), round((v.x ** 2 + v.y ** 2) ** 0.5), cur])
    now = {(c.x, c.y) for c in gen.get_section_coords()}
    for c in sorted(now - S["known"]): S["ev"].append({"t": round(t, 3), "section": list(c), "at": [round(l.x), round(l.y)]})
    S["known"] = now
    for e in S["ev"]:
        if "built_at" not in e:
            sec = gen.get_section(unreal.IntPoint(*e["section"]))
            if sec and not sec.is_building():
                e.update({"built_at": round(t, 3), "built_her": [round(l.x), round(l.y)], "buildings": sec.get_num_buildings(), "doors": sec.get_num_doors(), "containers": sec.get_num_containers(),
                          "instances": sec.get_editor_property("num_instances"), "ms": round(sec.get_editor_property("generate_ms"))})
    if t > END:
        unreal.unregister_slate_post_tick_callback(S["h"])
        json.dump({"rows": S["rows"], "events": S["ev"], "map": mapdata(), "section_size": gen.get_editor_property("section_size"),
                   "iso_yaw": gen.get_editor_property("iso_yaw"), "iso_pitch": gen.get_editor_property("iso_pitch")}, open(OUT, "w"))
        unreal.log("IVPATH saved %d rows | %s" % (len(S["rows"]), " | ".join(f"{e['section']} at {e['t']:.2f}s built {e.get('built_at')}" for e in S["ev"])))
        G.clear()
S["arm"] = unreal.register_slate_post_tick_callback(arm)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_play_simulate()
print("simulate requested, recorder armed")
