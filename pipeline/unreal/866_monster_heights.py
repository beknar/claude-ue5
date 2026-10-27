"""The monsters' height (the user's of 2026-10-26: "Half Creature 05 is invisible"). 859 set each kind's MeshZ from its
mesh's bounds in the reference pose; a crawler's clips hold its body far lower than that pose (Half Creature 05 was drawn 6
to 54 cm under the floor: invisible), and others' higher (the Rat 49 cm, the Parasite Slider 38 cm in the air). Measured
in play instead: each kind spawned on the floor of the great hall, its idle playing, the lowest of its skinned vertices as
drawn (ARDMonster::GetDrawnBottom) against the bottom of its capsule; its MeshZ moved by that much (a crawler's lowest point
on the floor, a standing one's soles).
Two steps: "measure" (play-in-editor running: spawns the kinds a batch at a time, a second of idle each, writes
SourceArt/mistward/monster_heights.json and logs "MHEIGHT done"), then "apply <map>" (the editor world: the level's
generator's Monsters get MeshZ = the MeshZ they had when measured - the bottom measured + RAISE: the same result however
often it is run; for mistward_castle and random_dungeonmagic_level5).
RAISE: kinds whose other clips hold the body lower than the idle measured: the Insect (a winged insect) bobs -17 to +7 cm
in its idle and walks 25 cm under the floor (868's heights step, sampled over 6 s): raised by 25, it walks on the floor and
hovers in its idle.
Args: measure | apply <map>"""
import unreal, sys, json, os
__keep__ = True
OUT = r"E:\code\claude-ue5\claude_ue5\SourceArt\mistward\monster_heights.json"
RAISE = {"Insect": 25.0}
MODE = sys.argv[1] if len(sys.argv) > 1 else "measure"
if MODE == "apply":
    MAP = sys.argv[2]
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not ues.get_editor_world().get_path_name().startswith(MAP + "."): les.load_level(MAP)
    gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    M = json.load(open(OUT))["kinds"]
    ms = list(gen.get_editor_property("monsters")); n = 0
    for d in ms:
        k = str(d.name)
        if k in M and "bottom" in M[k] and (abs(M[k]["bottom"]) > 1.5 or k in RAISE):
            d.mesh_z = round(M[k]["mesh_z"] - M[k]["bottom"] + RAISE.get(k, 0.0), 2); n += 1
    gen.set_editor_property("monsters", ms)
    les.save_current_level()
    print("MHEIGHT applied", n, "kinds of", len(ms), "on", MAP)
    __keep__ = False
    raise SystemExit
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
w = UES.get_game_world(); assert w is not None, "PIE is not running"
gen = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.RDDungeonGenerator)[0]
kinds = [str(d.name) for d in gen.get_editor_property("monsters") if d.mesh]
c = gen.get_start_room_center()
G = {"i": 0, "t": 0.0, "live": [], "res": {}, "aggro": gen.get_editor_property("aggro_distance")}
gen.set_editor_property("aggro_distance", 0.0)
BATCH = 8
def spawn_batch():
    G["live"] = []
    for j in range(BATCH):
        if G["i"] >= len(kinds): break
        k = kinds[G["i"]]; G["i"] += 1
        at = unreal.Vector(c.x - 900 + (j % 4) * 600, c.y - 600 + (j // 4) * 900, 0)
        m = gen.spawn_monster_named(k, at, 1, 1.0, 1.0, 1.0)
        if m: G["live"].append((k, m))
def tick(dt):
    try:
        G["t"] += dt
        if not G["live"] and G["t"] > 0.2:
            if G["i"] >= len(kinds): finish(); return
            spawn_batch(); G["t"] = 0.0; return
        if G["live"] and G["t"] > 1.6:
            for k, m in G["live"]:
                try:
                    G["res"][k] = {"bottom": round(m.get_drawn_bottom(), 2), "mesh_z": round(m.get_component_by_class(unreal.SkeletalMeshComponent).get_editor_property("relative_location").z, 2)}
                    # (out of the way: put far off and stilled (destroy_actor from Python left them standing))
                    m.set_actor_hidden_in_game(True); m.set_actor_tick_enabled(False); m.set_actor_location(unreal.Vector(1e6, 1e6, -1e5), False, True)
                except Exception as e:
                    G["res"][k] = {"error": str(e)}
            G["live"] = []; G["t"] = 0.0
    except Exception as e:
        import traceback; unreal.log_error("MHEIGHT error " + str(e) + traceback.format_exc()); finish()
def finish():
    unreal.unregister_slate_post_tick_callback(unreal._mheight)
    gen.set_editor_property("aggro_distance", G["aggro"])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"_note": "866: each kind's lowest drawn point against its capsule's bottom in its idle (cm), and its MeshZ then", "kinds": G["res"]}, open(OUT, "w"), indent=1)
    bad = {k: v["bottom"] for k, v in G["res"].items() if "bottom" in v and abs(v["bottom"]) > 1.5}
    errs = [k for k, v in G["res"].items() if "error" in v]
    (unreal.log_error if errs else unreal.log)("MHEIGHT done | %d kinds | %d errors %s | off by more than 1.5 cm: %s" % (len(G["res"]), len(errs), errs[:5], json.dumps(bad)))
unreal._mheight = unreal.register_slate_post_tick_callback(tick)
print("MHEIGHT measuring", len(kinds), "kinds")
