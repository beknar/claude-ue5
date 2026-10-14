"""Object gallery for docs/objects.md: three pictures of every weapon and item of the Fab library listed in
SourceArt/object_gallery/objects.json (name, pack, meshes, section, the clip of its third picture). Shot in the scratch
level /Game/RandomLevel/Test/rl_scratch, left empty, as the vehicle gallery (903) is: each object on a floor of its own,
lifted so its lowest point touches it, every shot a show-only list of the object and its floor.
The views follow the object's own box, since a sword may be modelled upright, a rifle along X or Y, a shield lying flat:
  <id>_side.png     looking at its broad face (along its thinnest axis), level, or from above if it lies flat
  <id>_quarter.png  turned 35 degrees about its length, from above
  <id>_third.png    a skeletal object with a clip: a frame of that clip (a reload, a shot, a lid opening); otherwise the
                    other three-quarter view, from the far side
A model of several meshes (the flamethrower's gun, hose and tank; the riot shield and club) is one actor per mesh.
The near clipping plane is 0.5 cm: a coin is shot from a few centimetres.
One mode per call:
  stage [start count] | stage ids <id,...>   the objects (or a batch), lights, the capture camera; texture streaming off
  shoot dir [ids]   (play-in-editor running) dir/<id>_side.png, _quarter.png, _third.png
  clear             the staged actors removed (the level saved empty), texture streaming on
Args: mode [dir] [ids] | stage start count | stage ids <id,id,...>"""
import sys, os, re, json, math, unreal
MODE = sys.argv[1]
V = unreal.Vector; ML = unreal.MathLibrary; GS = unreal.GameplayStatics
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
ar = unreal.AssetRegistryHelpers.get_asset_registry()
DATA = r"E:\code\claude-ue5\claude_ue5\SourceArt\object_gallery\objects.json"
SCRATCH = "/Game/RandomLevel/Test/rl_scratch"
TAG = unreal.Name("object_gallery"); ORIGIN = V(0, 0, 200000.0)
FLOOR = "/Game/ObjectGallery/MI_OBJ_Floor"
W_PX, H_PX, FOV = 960, 600, 30.0


def load_data(): return json.load(open(DATA, encoding="utf-8"))["objects"]


def cleanup():
    import gc
    for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
    gc.collect()


def find_clip(folder, name):
    for ad in ar.get_assets_by_path("/Game/" + folder, True):
        if str(ad.asset_name) == name and str(ad.asset_class_path.asset_name) == "AnimSequence": return unreal.load_asset(str(ad.package_name))
    raise KeyError((folder, name))


def mesh_box(m):
    if isinstance(m, unreal.StaticMesh):
        b = m.get_bounding_box(); return b.min, b.max
    b = m.get_bounds(); o, e = b.origin, b.box_extent
    return V(o.x - e.x, o.y - e.y, o.z - e.z), V(o.x + e.x, o.y + e.y, o.z + e.z)


def unit(v):
    n = math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z); return V(v.x / n, v.y / n, v.z / n)


def views(lo, hi):
    """the three directions from the object to the camera: side, quarter, far quarter"""
    ext = [hi.x - lo.x, hi.y - lo.y, hi.z - lo.z]; order = sorted(range(3), key=lambda k: ext[k])
    t, m = order[0], order[1]
    E = [V(1, 0, 0), V(0, 1, 0), V(0, 0, 1)]
    def lift(v, zmin):
        if v.z < zmin: v = V(v.x, v.y, zmin)
        return unit(v)
    if t == 2:                                                      # (lying flat: its face is seen from above)
        side = unit(V(E[m].x * 0.25, E[m].y * 0.25, 1.0))
        q = lift(V(E[m].x * math.sin(math.radians(55)), E[m].y * math.sin(math.radians(55)), math.cos(math.radians(55))), 0.3)
        f = lift(V(-E[m].x * math.sin(math.radians(55)), -E[m].y * math.sin(math.radians(55)), math.cos(math.radians(55))), 0.3)
        return side, q, f
    c, s = math.cos(math.radians(35)), math.sin(math.radians(35))
    side = lift(V(E[t].x, E[t].y, 0.1), 0.1)
    q = lift(V(E[t].x * c + E[m].x * s, E[t].y * c + E[m].y * s, E[t].z * c + E[m].z * s + 0.35), 0.3)
    f = lift(V(-E[t].x * c + E[m].x * s, -E[t].y * c + E[m].y * s, -E[t].z * c + E[m].z * s + 0.35), 0.3)
    return side, q, f


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
    key = spawn(unreal.DirectionalLight, ORIGIN + V(0, 0, 1000), unreal.Rotator(roll=0, pitch=-50, yaw=-115)); key.light_component.set_intensity(6.0)
    fill = spawn(unreal.DirectionalLight, ORIGIN + V(0, 0, 1000), unreal.Rotator(roll=0, pitch=-15, yaw=-55)); fill.light_component.set_intensity(2.2); fill.light_component.set_cast_shadows(False)
    rim = spawn(unreal.DirectionalLight, ORIGIN + V(0, 0, 1000), unreal.Rotator(roll=0, pitch=-25, yaw=80)); rim.light_component.set_intensity(3.0); rim.light_component.set_cast_shadows(False)
    sky = spawn(unreal.SkyLight, ORIGIN + V(0, 0, 500)); sky.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    sky.light_component.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
    sky.light_component.set_editor_property("cubemap", unreal.load_asset("/Engine/EngineResources/GrayLightTextureCube")); sky.light_component.set_intensity(1.3)
    spawn(unreal.SceneCapture2D, ORIGIN, tags=("O_CAP",))
    floor_mat = unreal.load_asset(FLOOR)                            # (a plain mid grey: the engine's grid is noise behind a coin, and the white
    if not floor_mat:                                               #  basic material drove the capture's exposure down: the weapons came out black)
        floor_mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(FLOOR.rsplit("/", 1)[1], FLOOR.rsplit("/", 1)[0], unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        floor_mat.set_editor_property("parent", unreal.load_asset("/Engine/BasicShapes/BasicShapeMaterial"))
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(floor_mat, "Color", unreal.LinearColor(0.12, 0.12, 0.12, 1.0))
    unreal.MaterialEditingLibrary.update_material_instance(floor_mat); unreal.EditorAssetLibrary.save_loaded_asset(floor_mat, only_if_is_dirty=False)
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
        if clip and not any(isinstance(m, unreal.SkeletalMesh) and m.skeleton == clip.get_editor_property("skeleton") for m in meshes):
            report.append(("clip on another skeleton", h["id"])); clip = None          # (a pack's reload may be on the bare gun's skeleton, not the full gun's)
        for c in (("N", "P") if clip else ("N",)):
            x += max(size * 3, 300.0)
            at = V(ORIGIN.x + x - (lo.x + hi.x) / 2, ORIGIN.y - (lo.y + hi.y) / 2, ORIGIN.z - lo.z)
            fl = spawn(unreal.StaticMeshActor, V(ORIGIN.x + x, ORIGIN.y, ORIGIN.z), tags=("O_%03d_%s_F" % (i, c),))
            fl.static_mesh_component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Plane")); fl.set_actor_scale3d(V(max(size * 8, 200.0) / 100.0, max(size * 8, 200.0) / 100.0, 1))
            fl.static_mesh_component.set_material(0, floor_mat)
            for j, m in enumerate(meshes):
                if isinstance(m, unreal.StaticMesh):
                    a = spawn(unreal.StaticMeshActor, at, tags=("O_%03d_%s_%d" % (i, c, j),)); a.static_mesh_component.set_static_mesh(m)
                else:
                    a = spawn(unreal.SkeletalMeshActor, at, tags=("O_%03d_%s_%d" % (i, c, j),)); smc = a.skeletal_mesh_component
                    smc.set_skinned_asset_and_update(m)
                    smc.set_editor_property("visibility_based_anim_tick_option", unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
                    if c == "P" and m.skeleton == clip.get_editor_property("skeleton"):
                        t = unreal.AnimationLibrary.get_sequence_length(clip) * float(h.get("t", 0.5))
                        smc.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE); smc.override_animation_data(clip, False, False, t, 0.0)
        report.append((h["id"], round(size, 1)))
    print("OBJGAL staged", len(report), "objects:", report)

elif MODE == "shoot":
    OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
    ONLY = set(sys.argv[3].split(",")) if len(sys.argv) > 3 else None
    w = ues.get_game_world(); assert w, "play-in-editor is not running"
    H = load_data()
    acts = {}
    for a in GS.get_all_actors_with_tag(w, TAG):
        for t in a.tags:
            if str(t).startswith("O_"): acts[str(t)] = a
    cap = acts["O_CAP"]; comp = cap.capture_component2d
    rt = unreal.RenderingLibrary.create_render_target2d(w, W_PX, H_PX, unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
    comp.texture_target = rt; comp.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
    comp.capture_every_frame = False; comp.capture_on_movement = False; comp.always_persist_rendering_state = True
    comp.fov_angle = FOV; comp.primitive_render_mode = unreal.SceneCapturePrimitiveRenderMode.PRM_USE_SHOW_ONLY_LIST
    comp.set_editor_property("override_custom_near_clipping_plane", True); comp.set_editor_property("custom_near_clipping_plane", 0.5)
    TH = math.tan(math.radians(FOV / 2)); TV = TH * H_PX / W_PX
    def group(prefix): return [a for t, a in acts.items() if t.startswith(prefix + "_") and not t.endswith("_F")]
    def corners(actors):
        lo = hi = None
        for a in actors:
            o, e = a.get_actor_bounds(False)
            l = V(o.x - e.x, o.y - e.y, o.z - e.z); u = V(o.x + e.x, o.y + e.y, o.z + e.z)
            lo = l if lo is None else V(min(lo.x, l.x), min(lo.y, l.y), min(lo.z, l.z)); hi = u if hi is None else V(max(hi.x, u.x), max(hi.y, u.y), max(hi.z, u.z))
        return lo, hi
    def shoot(name, actors, floor, u):
        """the camera on the side `u` of the objects' box (a unit vector from it), as close as the box allows"""
        lo, hi = corners(actors); c = V((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, (lo.z + hi.z) / 2)
        d = V(-u.x, -u.y, -u.z)
        hz = math.sqrt(d.x * d.x + d.y * d.y)
        right = V(-d.y / hz, d.x / hz, 0) if hz > 1e-3 else V(1, 0, 0)
        up = V(d.y * right.z - d.z * right.y, d.z * right.x - d.x * right.z, d.x * right.y - d.y * right.x)
        D = 0.0
        for px in (lo.x, hi.x):
            for py in (lo.y, hi.y):
                for pz in (lo.z, hi.z):
                    k = V(px - c.x, py - c.y, pz - c.z); depth = k.x * d.x + k.y * d.y + k.z * d.z
                    D = max(D, abs(k.x * right.x + k.y * right.y + k.z * right.z) / TH - depth, abs(k.x * up.x + k.y * up.y + k.z * up.z) / TV - depth)
        D = max(D * 1.1, 2.0)
        cam = V(c.x + u.x * D, c.y + u.y * D, c.z + u.z * D)
        cap.set_actor_location(cam, False, False); cap.set_actor_rotation(ML.find_look_at_rotation(cam, c), False)
        comp.clear_show_only_components()
        for a in actors + [floor]: comp.show_only_actor_components(a, False)
        for _ in range(6): comp.capture_scene()
        unreal.RenderingLibrary.export_render_target(w, rt, OUT, name)
    n = 0
    for i, h in enumerate(H):
        if (ONLY and h["id"] not in ONLY) or not group("O_%03d_N" % i): continue
        N = group("O_%03d_N" % i); F = acts["O_%03d_N_F" % i]
        side, q, far = views(*corners(N))
        shoot("%s_side.png" % h["id"], N, F, side)
        shoot("%s_quarter.png" % h["id"], N, F, q)
        P = group("O_%03d_P" % i)
        if P: shoot("%s_third.png" % h["id"], P, acts["O_%03d_P_F" % i], q)
        else: shoot("%s_third.png" % h["id"], N, F, far)
        n += 1
    print("OBJGAL shot", n, "objects")

elif MODE == "clear":
    w = ues.get_editor_world()
    if w.get_path_name().startswith(SCRATCH + "."):
        for a in eas.get_all_level_actors():
            if TAG in a.tags: eas.destroy_actor(a)
        les.save_current_level()
    unreal.SystemLibrary.execute_console_command(w, "r.TextureStreaming 1")
    print("OBJGAL cleared")
cleanup()
