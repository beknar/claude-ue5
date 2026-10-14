"""Vehicle gallery for docs/vehicles.md: three pictures of every vehicle, mount and beast-drawn cart of the Fab library
that is in this project. The list is SourceArt/vehicle_gallery/vehicles.json (name, pack, meshes, category, the clip
of its motion picture). Shot in the scratch level /Game/RandomLevel/Test/rl_scratch, left empty.
Pictures (960 x 600): <id>_quarter.png (three-quarter view), <id>_side.png (side view) and <id>_third.png: for a
skeletal mesh with a clip, a frame of that clip ("in motion"); otherwise the model from above, from the other corner.
A model of several meshes (the armoured car's body, wheels and gun; the ballista's frame and wheels) is one actor per
mesh at the same place, all framed together. Each model stands on a floor of its own, lifted so its lowest point
touches it, and every shot shows only that model and its floor (a show-only list), since models from a 1 m drone to a
115 m cargo ship are staged in one row. Animations show only during play-in-editor (see 901): stage, then shoot in PIE.
One mode per call:
  stage [start count] | stage ids <id,...>   the models (or a batch), lights, the capture camera; texture streaming off
  shoot dir [ids]   (play-in-editor running) dir/<id>_quarter.png, _side.png, _third.png
  clear             the staged actors removed (the level saved empty), texture streaming on
Args: mode [dir] [ids] | stage start count | stage ids <id,id,...>"""
import sys, os, re, json, math, unreal
MODE = sys.argv[1]
V = unreal.Vector; ML = unreal.MathLibrary; GS = unreal.GameplayStatics
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
ar = unreal.AssetRegistryHelpers.get_asset_registry()
DATA = r"E:\code\claude-ue5\claude_ue5\SourceArt\vehicle_gallery\vehicles.json"
SCRATCH = "/Game/RandomLevel/Test/rl_scratch"
TAG = unreal.Name("vehicle_gallery"); ORIGIN = V(0, 0, 200000.0)
W_PX, H_PX, FOV = 960, 600, 30.0


def load_data(): return json.load(open(DATA, encoding="utf-8"))["vehicles"]


def cleanup():
    import gc
    for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
    gc.collect()


def find_clip(folder, name):
    for ad in ar.get_assets_by_path("/Game/" + folder, True):
        if str(ad.asset_name) == name and str(ad.asset_class_path.asset_name) == "AnimSequence": return unreal.load_asset(str(ad.package_name))
    raise KeyError((folder, name))


def mesh_box(m):
    """lowest point and horizontal size of a static or skeletal mesh in its own frame (reference pose)"""
    if isinstance(m, unreal.StaticMesh):
        b = m.get_bounding_box(); return b.min, b.max
    b = m.get_bounds(); o, e = b.origin, b.box_extent
    return V(o.x - e.x, o.y - e.y, o.z - e.z), V(o.x + e.x, o.y + e.y, o.z + e.z)


# ================================================================================================ modes
if MODE == "stage":
    if not ues.get_editor_world().get_path_name().startswith(SCRATCH + "."): les.load_level(SCRATCH)
    w = ues.get_editor_world(); assert w.get_path_name().startswith(SCRATCH + "."), w.get_path_name()
    for a in eas.get_all_level_actors():
        if TAG in a.tags: eas.destroy_actor(a)
    unreal.SystemLibrary.execute_console_command(w, "r.TextureStreaming 0")
    def spawn(cls, loc, rot=None, tags=()):
        a = eas.spawn_actor_from_class(cls, loc, rot or unreal.Rotator()); a.tags = [TAG] + [unreal.Name(t) for t in tags]; return a
    H = load_data(); report = []
    IDS = set(sys.argv[3].split(",")) if len(sys.argv) > 3 and sys.argv[2] == "ids" else None
    B0 = int(sys.argv[2]) if len(sys.argv) > 2 and not IDS else 0; BN = int(sys.argv[3]) if len(sys.argv) > 3 and not IDS else len(H)
    key = spawn(unreal.DirectionalLight, ORIGIN + V(0, 0, 1000), unreal.Rotator(roll=0, pitch=-38, yaw=-115)); key.light_component.set_intensity(6.0)
    key.light_component.set_editor_property("dynamic_shadow_distance_movable_light", 120000.0)
    fill = spawn(unreal.DirectionalLight, ORIGIN + V(0, 0, 1000), unreal.Rotator(roll=0, pitch=-15, yaw=-55)); fill.light_component.set_intensity(2.2); fill.light_component.set_cast_shadows(False)
    rim = spawn(unreal.DirectionalLight, ORIGIN + V(0, 0, 1000), unreal.Rotator(roll=0, pitch=-25, yaw=80)); rim.light_component.set_intensity(3.0); rim.light_component.set_cast_shadows(False)
    sky = spawn(unreal.SkyLight, ORIGIN + V(0, 0, 500)); sky.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    sky.light_component.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
    sky.light_component.set_editor_property("cubemap", unreal.load_asset("/Engine/EngineResources/GrayLightTextureCube")); sky.light_component.set_intensity(1.3)
    spawn(unreal.SceneCapture2D, ORIGIN, tags=("V_CAP",))
    x = 0.0
    for i, h in enumerate(H):
        if not B0 <= i < B0 + BN or (IDS and h["id"] not in IDS): continue
        meshes = [unreal.load_asset(p) for p in h["meshes"]]; assert all(meshes), h["meshes"]
        lo = hi = None
        for m in meshes:
            l, u = mesh_box(m)
            lo = l if lo is None else V(min(lo.x, l.x), min(lo.y, l.y), min(lo.z, l.z)); hi = u if hi is None else V(max(hi.x, u.x), max(hi.y, u.y), max(hi.z, u.z))
        size = max(hi.x - lo.x, hi.y - lo.y, hi.z - lo.z)
        clip = find_clip(h["folder"], h["clip"]) if h.get("clip") else None
        copies = ("N", "P") if clip else ("N",)
        for c in copies:
            x += size * 1.5 + 2000.0
            at = V(ORIGIN.x + x - (lo.x + hi.x) / 2, ORIGIN.y - (lo.y + hi.y) / 2, ORIGIN.z - lo.z)        # (centred over its floor, lowest point on it)
            fl = spawn(unreal.StaticMeshActor, V(ORIGIN.x + x, ORIGIN.y, ORIGIN.z), tags=("V_%03d_%s_F" % (i, c),))
            fl.static_mesh_component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Plane")); fl.set_actor_scale3d(V(max(size * 6, 3000.0) / 100.0, max(size * 6, 3000.0) / 100.0, 1))
            for j, m in enumerate(meshes):
                if isinstance(m, unreal.StaticMesh):
                    a = spawn(unreal.StaticMeshActor, at, tags=("V_%03d_%s_%d" % (i, c, j),)); a.static_mesh_component.set_static_mesh(m)
                else:
                    a = spawn(unreal.SkeletalMeshActor, at, tags=("V_%03d_%s_%d" % (i, c, j),)); smc = a.skeletal_mesh_component
                    smc.set_skinned_asset_and_update(m)
                    smc.set_editor_property("visibility_based_anim_tick_option", unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
                    if c == "P":
                        t = unreal.AnimationLibrary.get_sequence_length(clip) * float(h.get("t", 0.5))
                        smc.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE); smc.override_animation_data(clip, False, False, t, 0.0)
        report.append((h["id"], round(size / 100.0, 1)))
    print("VEHGAL staged", len(report), "vehicles:", report)

elif MODE == "shoot":
    OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
    ONLY = set(sys.argv[3].split(",")) if len(sys.argv) > 3 else None
    w = ues.get_game_world(); assert w, "play-in-editor is not running"
    H = load_data()
    acts = {}
    for a in GS.get_all_actors_with_tag(w, TAG):
        for t in a.tags:
            if str(t).startswith("V_"): acts[str(t)] = a
    cap = acts["V_CAP"]; comp = cap.capture_component2d
    rt = unreal.RenderingLibrary.create_render_target2d(w, W_PX, H_PX, unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
    comp.texture_target = rt; comp.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
    comp.capture_every_frame = False; comp.capture_on_movement = False; comp.always_persist_rendering_state = True
    comp.fov_angle = FOV; comp.primitive_render_mode = unreal.SceneCapturePrimitiveRenderMode.PRM_USE_SHOW_ONLY_LIST
    TH = math.tan(math.radians(FOV / 2)); TV = TH * H_PX / W_PX
    def group(prefix):
        return [a for t, a in acts.items() if t.startswith(prefix + "_") and not t.endswith("_F")]
    def corners(actors):
        lo = hi = None
        for a in actors:
            o, e = a.get_actor_bounds(False)
            l = V(o.x - e.x, o.y - e.y, o.z - e.z); u = V(o.x + e.x, o.y + e.y, o.z + e.z)
            lo = l if lo is None else V(min(lo.x, l.x), min(lo.y, l.y), min(lo.z, l.z)); hi = u if hi is None else V(max(hi.x, u.x), max(hi.y, u.y), max(hi.z, u.z))
        return lo, hi
    def shoot(name, actors, floor, yaw_deg, pitch_deg):
        """the camera looking at the models' box from yaw / pitch (degrees), as close as the box allows"""
        lo, hi = corners(actors); c = V((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, (lo.z + hi.z) / 2)
        y, p = math.radians(yaw_deg), math.radians(pitch_deg)
        d = V(-math.cos(p) * math.cos(y), -math.cos(p) * math.sin(y), -math.sin(p))            # (the view direction)
        right = V(-math.sin(y), math.cos(y), 0); up = V(d.y * right.z - d.z * right.y, d.z * right.x - d.x * right.z, d.x * right.y - d.y * right.x)
        D = 0.0
        for px in (lo.x, hi.x):
            for py in (lo.y, hi.y):
                for pz in (lo.z, hi.z):
                    k = V(px - c.x, py - c.y, pz - c.z); depth = k.x * d.x + k.y * d.y + k.z * d.z
                    D = max(D, abs(k.x * right.x + k.y * right.y) / TH - depth, abs(k.x * up.x + k.y * up.y + k.z * up.z) / TV - depth)
        D *= 1.1
        cam = V(c.x - d.x * D, c.y - d.y * D, c.z - d.z * D)
        cap.set_actor_location(cam, False, False); cap.set_actor_rotation(ML.find_look_at_rotation(cam, c), False)
        comp.clear_show_only_components()
        for a in actors + [floor]: comp.show_only_actor_components(a, False)
        for _ in range(6): comp.capture_scene()
        unreal.RenderingLibrary.export_render_target(w, rt, OUT, name)
    n = 0
    for i, h in enumerate(H):
        if (ONLY and h["id"] not in ONLY) or not group("V_%03d_N" % i): continue
        N = group("V_%03d_N" % i); F = acts["V_%03d_N_F" % i]
        lo, hi = corners(N); along_x = h["axis"] == "x" if h.get("axis") else (hi.x - lo.x) >= (hi.y - lo.y)
        base = 0.0 if along_x else 90.0          # (the long side is seen from the side; `axis` says it where the wings are longer than the body)
        shoot("%s_quarter.png" % h["id"], N, F, base + 90 - 38, 16)
        shoot("%s_side.png" % h["id"], N, F, base + 90, 6)
        P = group("V_%03d_P" % i)
        if P: shoot("%s_third.png" % h["id"], P, acts["V_%03d_P_F" % i], base + 90 + 38, 14)
        else: shoot("%s_third.png" % h["id"], N, F, base - 90 + 40, 48)
        n += 1
    print("VEHGAL shot", n, "vehicles")

elif MODE == "clear":
    w = ues.get_editor_world()
    if w.get_path_name().startswith(SCRATCH + "."):
        for a in eas.get_all_level_actors():
            if TAG in a.tags: eas.destroy_actor(a)
        les.save_current_level()
    unreal.SystemLibrary.execute_console_command(w, "r.TextureStreaming 1")
    print("VEHGAL cleared")
cleanup()
