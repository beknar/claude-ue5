"""random_isometric_village_level_Cine: record the Movie Render Queue render of LS_IV_Showcase while it runs, for the
reel overlay's maps. Run it right before 75 (it waits for the render's world and its sequence player). Per sequence
frame: Demo_IV_Fem5 (position, yaw, speed, the house she is in); every third frame the villagers (they are not on the
sequence clock: their walks differ from one run to the next, so the overlay must show the ones of this render); the
sections the generator adds (frame triggered, frame built, counts) and, at the end, the village map data of every
section. Frame 0 is the last tick of MRQ's warm-up. Writes SourceArt/random_isometric_village/cine_render.json and logs
'IVREND saved' (or 'IVREND failed'). Keeps its namespace (tick callback); a recorder left armed by an earlier run is
dropped."""
import unreal, json
__keep__ = True
OUT = "E:\\code\\claude-ue5\\claude_ue5\\SourceArt\\random_isometric_village\\cine_render.json"
FPS, LAST, VSTEP = 30, 897, 3
G = {}
S = {"rows": [], "vill": [], "ids": {}, "ev": [], "known": set(), "frame": -1, "saved": False}
if getattr(unreal, "_iv_rend", None) is not None:
    try: unreal.unregister_slate_post_tick_callback(unreal._iv_rend)
    except Exception: pass
def stop():
    unreal.unregister_slate_post_tick_callback(unreal._iv_rend); unreal._iv_rend = None; G.clear()
def tick(dt):
    try: body()
    except Exception as e:
        import traceback
        stop(); unreal.log_error("IVREND failed: " + str(e) + traceback.format_exc())
def name(e): return str(e).split(".")[-1].split(":")[0].strip("<> ")
def mapdata():
    out = []
    for c, m in G["gen"].get_editor_property("map_data").items():
        sec = G["gen"].get_section(c)
        out.append({"coord": [c.x, c.y], "start": bool(m.start), "villagers": sec.get_num_villagers() if sec else 0,
                    "buildings": [{"c": [round(b.center.x), round(b.center.y)], "half": [round(b.half.x), round(b.half.y)], "yaw": round(b.yaw, 1), "wall": round(b.wall_height), "roof": round(b.roof_height),
                                   "ridge_y": bool(b.ridge_along_y), "tower": round(b.tower_height), "style": name(b.style), "kind": name(b.kind), "visited": bool(b.visited)} for b in m.buildings],
                    "roads": [{"pts": [[round(p.x), round(p.y)] for p in r.points], "hw": round(r.half_width), "type": int(r.type)} for r in m.roads],
                    "patches": [{"pts": [[round(p.x), round(p.y)] for p in q.points], "type": int(q.type)} for q in m.patches],
                    "trees": [[round(t.p.x), round(t.p.y), round(t.radius), round(t.height), int(t.type)] for t in m.trees],
                    "props": [[round(p.p.x), round(p.p.y), round(p.yaw), int(p.type)] for p in m.props]})
    return out
def save():
    gen = G["gen"]
    json.dump({"fps": FPS, "rows": S["rows"], "vill_step": VSTEP, "vill": S["vill"], "events": S["ev"], "map": mapdata(), "section_size": gen.get_editor_property("section_size"),
               "iso_yaw": gen.get_editor_property("iso_yaw"), "iso_pitch": gen.get_editor_property("iso_pitch")}, open(OUT, "w"), separators=(",", ":"))
    S["saved"] = True
    unreal.log("IVREND saved %d frames, %d villagers | %s" % (len(S["rows"]), len(S["ids"]), " | ".join(f"{e['section']} at frame {e['frame']} built {e.get('built')}" for e in S["ev"])))
def body():
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if "gen" not in G:
        if w is None: return
        lsa = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.LevelSequenceActor)
        gens = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.IVVillageGenerator)
        if not lsa or not gens or lsa[0].get_editor_property("sequence_player") is None: return
        G["w"] = w; G["gen"] = gens[0]; G["player"] = lsa[0].get_editor_property("sequence_player")
        G["demo"] = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Character) if a.get_actor_label() == "Demo_IV_Fem5")
        S["known"] = {(c.x, c.y) for c in G["gen"].get_section_coords()}
        unreal.log("IVREND armed, %d sections" % len(S["known"]))
    if w is None:
        if not S["saved"]: unreal.log_error("IVREND failed: the render ended at frame %d, before frame %d" % (S["frame"], LAST))
        stop(); return
    if S["saved"]: return
    gen = G["gen"]
    f = int(unreal.TimeManagementLibrary.conv_qualified_frame_time_to_seconds(G["player"].get_current_time()) * FPS + 1e-3)
    if f < 0 or (f == S["frame"] and f != 0): return
    a = G["demo"]; l = a.get_actor_location(); v = a.get_velocity()
    cur, cs = gen.get_current_building()
    row = [round(f / FPS, 4), round(l.x, 1), round(l.y, 1), round(l.z, 1), round(a.get_actor_rotation().yaw, 1), round((v.x ** 2 + v.y ** 2) ** 0.5), cur]
    vs = None
    if f % VSTEP == 0:
        vs = [None] * len(S["ids"])
        for vg in gen.get_villagers():
            i = S["ids"].setdefault(vg.get_name(), len(S["ids"]))
            if i >= len(vs): vs.append(None)
            p = vg.get_actor_location(); vs[i] = [round(p.x), round(p.y)]
    if f == S["frame"]:                                   # (still in the warm-up: frame 0 again)
        S["rows"][-1] = row; S["vill"][-1] = vs
    else:
        S["rows"].append(row)
        if vs is not None: S["vill"].append(vs)
    S["frame"] = f
    now = {(c.x, c.y) for c in gen.get_section_coords()}
    for c in sorted(now - S["known"]): S["ev"].append({"frame": f, "section": list(c), "at": [round(l.x), round(l.y)]})
    S["known"] = now
    for e in S["ev"]:
        if "built" not in e:
            sec = gen.get_section(unreal.IntPoint(*e["section"]))
            if sec and not sec.is_building():
                m = gen.get_editor_property("map_data").get(unreal.IntPoint(*e["section"]))
                e.update({"built": f, "buildings": sec.get_num_buildings(), "doors": sec.get_num_doors(), "containers": sec.get_num_containers(), "villagers": sec.get_num_villagers(),
                          "trees": len(m.trees) if m else 0, "instances": sec.get_editor_property("num_instances"), "ms": round(sec.get_editor_property("generate_ms"))})
    if f >= LAST: save()
unreal._iv_rend = unreal.register_slate_post_tick_callback(tick)
print("render recorder armed")
