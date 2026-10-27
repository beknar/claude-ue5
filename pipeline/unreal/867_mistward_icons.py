"""mistward_castle: inventory pictures for its 22 shields, the torch and the 29 weapons of the weapons table (after 865).

    867_mistward_icons.py shoot <dir> [--only icon,icon] [--light k]   (play stopped: shot in the editor world, which is left as it was and saved)
    867_mistward_icons.py import <dir>   (play stopped)

shoot: each shield (its face toward the camera, its wide end up: the frame 865 measured, shields.json's flip / turn)
the torch (leaning, its head up right) and each found weapon (its blade's flat face to the camera, leaning up right: the
frame 854 measured on its mesh, weapon_frames.json) is put far below the dungeon with two lights of its own and taken twice by
a SceneCapture2D that sees only it: lit (final colour) and as a mask (every slot a plain white material, base colour).
Writes <dir>/<icon>_rgb.png and <icon>_mask.png; pipeline/blender_numpy/mw_icons.py makes <icon>.png from the pair
(its colour where the mask is, cut to the thing, 256 x 256).
import: <dir>/<icon>.png -> /Game/RandomDungeon/UI/T_RDM4_<icon> (UI textures, as 830's) and the generator's UIArt
entries of those names (the items' Icon was set by 865: mw_<objects id>, mw_torch); the weapons' items and their fits get
mw_w_<name> (they had none: a found weapon showed no picture in the inventory or a loot pile). Saves the level."""
import unreal, sys, os, json, math
ARGS = sys.argv[1:]
MODE, OUT = ARGS[0], os.path.abspath(ARGS[1])
# (--only a,b: just those icons; --light k: the lights' strength times k)
ONLY = ARGS[ARGS.index("--only") + 1].split(",") if "--only" in ARGS else None
LIGHT = float(ARGS[ARGS.index("--light") + 1]) if "--light" in ARGS else 1.0
V = unreal.Vector; ML = unreal.MathLibrary
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
SH = json.load(open(SA + r"\mistward\shields.json", encoding="utf-8"))
FLIP = {s["name"]: (s.get("flip", False), s.get("turn", False)) for s in SH["shields"]}
WF = {w["mesh"].split(".")[0]: w for w in json.load(open(SA + r"\random_dungeon_magic5\weapon_frames.json", encoding="utf-8"))["weapons"].values()}
def wicon(name): return "mw_w_" + "".join(ch if ch.isalnum() else "_" for ch in name.lower()).strip("_").replace("__", "_")
MAP = "/Game/RandomDungeon/Maps/mistward_castle"
KP = unreal.ProceduralMeshLibrary
AX = {"x": V(1, 0, 0), "y": V(0, 1, 0), "z": V(0, 0, 1)}


def verts_of(m):
    vs = []
    for s in range(m.get_num_sections(0)):
        vs += [(v.x, v.y, v.z) for v in KP.get_section_from_static_mesh(m, 0, s)[0]]
    return vs


def shield_frame(m, flip=False, turn=False):
    """as 865's: mesh -> the shield's frame (its face toward +Y, its wide end +Z, centred)"""
    b = m.get_bounding_box(); vs = verts_of(m)
    mn = [b.min.x, b.min.y, b.min.z]; mx = [b.max.x, b.max.y, b.max.z]; size = [mx[i] - mn[i] for i in range(3)]
    thin = min(range(3), key=lambda i: size[i]); others = [i for i in range(3) if i != thin]
    up = max(others, key=lambda i: size[i]); side = [i for i in others if i != up][0]
    if turn: up, side = side, up
    lo, hi = mn[up], mx[up]
    def width(a, c): s = [v[side] for v in vs if a <= v[up] <= c]; return (max(s) - min(s)) if s else 0.0
    up_sign = 1.0 if width(hi - 0.2 * (hi - lo), hi) >= width(lo, lo + 0.2 * (hi - lo)) - 1.0 else -1.0
    cs, cu = (mn[side] + mx[side]) / 2, (lo + hi) / 2
    rad = lambda v: max(abs(v[side] - cs) / (size[side] / 2 + 1e-3), abs(v[up] - cu) / (size[up] / 2 + 1e-3))
    rim = [v[thin] for v in vs if rad(v) > 0.85]; mid = [v[thin] for v in vs if rad(v) < 0.3]
    f_sign = 1.0 if (sum(mid) / max(len(mid), 1)) >= (sum(rim) / max(len(rim), 1)) else -1.0
    if flip: f_sign = -f_sign
    u = AX["xyz"[up]] * up_sign; f = AX["xyz"[thin]] * f_sign; s = f.cross(u)
    c2m = unreal.Transform(V(0, 0, 0), ML.make_rotation_from_axes(s, f, u), V(1, 1, 1))
    center = V((mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, (mn[2] + mx[2]) / 2)
    return ML.compose_transforms(unreal.Transform(center * -1.0, unreal.Rotator(0, 0, 0), V(1, 1, 1)), c2m.inverse()), size


if MODE == "shoot":
    os.makedirs(OUT, exist_ok=True)
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if ues.get_game_world() is not None: raise SystemExit("867 shoot: stop play first")
    if not ues.get_editor_world().get_path_name().startswith(MAP + "."): unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    w = ues.get_editor_world()
    gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    made = []
    def spawn(cls, xf):
        a = eas.spawn_actor_from_class(cls, xf.translation, xf.rotation.rotator(), True); made.append(a); return a
    # (a plain white material for the mask)
    WHITE = "/Game/RandomDungeon/Mistward/M_RD_IconMask"
    if not unreal.EditorAssetLibrary.does_asset_exist(WHITE):
        MEL = unreal.MaterialEditingLibrary
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset("M_RD_IconMask", "/Game/RandomDungeon/Mistward", unreal.Material, unreal.MaterialFactoryNew())
        mat.set_editor_property("two_sided", True)
        c = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -300, 0)
        c.set_editor_property("constant", unreal.LinearColor(1, 1, 1, 1))
        MEL.connect_material_property(c, "", unreal.MaterialProperty.MP_BASE_COLOR)
        MEL.recompile_material(mat); unreal.EditorAssetLibrary.save_loaded_asset(mat, only_if_is_dirty=False)
    white = unreal.load_asset(WHITE)
    O = gen.get_actor_location() + V(0, 0, -30000.0)
    things = []
    for it in gen.get_editor_property("items"):
        if it.kind == unreal.RDItemKind.SHIELD:
            m = it.weapon_fits[0].weapon.off_hand_mesh
            fl, tu = FLIP.get(str(it.name), (False, False))
            frame, size = shield_frame(m, fl, tu)
            # (turned a little toward the camera's right: a face with some depth)
            look = unreal.Transform(V(0, 0, 0), unreal.Rotator(roll=0, pitch=0, yaw=-18), V(1, 1, 1))
            things.append((str(it.icon), m, ML.compose_transforms(frame, look), max(size)))
        elif it.kind == unreal.RDItemKind.WEAPON and len(it.weapon_fits) and it.weapon_fits[0].weapon.mesh:
            m = it.weapon_fits[0].weapon.mesh; f = WF.get(m.get_path_name().split(".")[0])
            b = m.get_bounding_box(); size = [b.max.x - b.min.x, b.max.y - b.min.y, b.max.z - b.min.z]
            ctr = V((b.min.x + b.max.x) / 2, (b.min.y + b.max.y) / 2, (b.min.z + b.max.z) / 2)
            if f:
                # (its frame: x the blade's way, y the edge's, z square to them -> the blade up, the edge across, the flat face
                # to the camera (+Y); then leaning 40 degrees: its point up right)
                F = unreal.Transform(V(0, 0, 0), ML.make_rotation_from_axes(V(*f["x"]), V(*f["y"]), V(*f["z"])), V(1, 1, 1))
                C = unreal.Transform(V(0, 0, 0), ML.make_rotation_from_axes(V(0, 0, 1), V(1, 0, 0), V(0, 1, 0)), V(1, 1, 1))
                rot = ML.compose_transforms(ML.compose_transforms(F.inverse(), C), unreal.Transform(V(0, 0, 0), unreal.Rotator(roll=0, pitch=-40, yaw=0), V(1, 1, 1)))
            else:
                rot = unreal.Transform(V(0, 0, 0), unreal.Rotator(roll=0, pitch=-40, yaw=0), V(1, 1, 1))
            things.append((wicon(str(it.name)), m, ML.compose_transforms(unreal.Transform(ctr * -1.0, unreal.Rotator(0, 0, 0), V(1, 1, 1)), rot), max(size)))
        elif it.kind == unreal.RDItemKind.TORCH:
            m = it.weapon_fits[0].weapon.off_hand_mesh
            b = m.get_bounding_box(); size = [b.max.x - b.min.x, b.max.y - b.min.y, b.max.z - b.min.z]
            ctr = V((b.min.x + b.max.x) / 2, (b.min.y + b.max.y) / 2, (b.min.z + b.max.z) / 2)
            # (its long axis is z, its head up (865): leaning 35 degrees to the right, seen from -... +Y)
            lean = unreal.Transform(V(0, 0, 0), unreal.Rotator(roll=0, pitch=-35, yaw=0), V(1, 1, 1))
            things.append((str(it.icon), m, ML.compose_transforms(unreal.Transform(ctr * -1.0, unreal.Rotator(0, 0, 0), V(1, 1, 1)), lean), max(size)))
    cap = spawn(unreal.SceneCapture2D, unreal.Transform(O, unreal.Rotator(0, 0, 0), V(1, 1, 1))); comp = cap.capture_component2d
    rt = unreal.RenderingLibrary.create_render_target2d(w, 512, 512, unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
    comp.texture_target = rt; comp.fov_angle = 20.0; comp.capture_every_frame = False; comp.capture_on_movement = False
    comp.primitive_render_mode = unreal.SceneCapturePrimitiveRenderMode.PRM_USE_SHOW_ONLY_LIST
    pp = comp.post_process_settings
    pp.override_auto_exposure_min_brightness = True; pp.auto_exposure_min_brightness = 1.0
    pp.override_auto_exposure_max_brightness = True; pp.auto_exposure_max_brightness = 1.0
    pp.override_auto_exposure_bias = True; pp.auto_exposure_bias = 0.0
    pp.override_bloom_intensity = True; pp.bloom_intensity = 0.0
    pp.override_vignette_intensity = True; pp.vignette_intensity = 0.0
    comp.post_process_settings = pp; comp.post_process_blend_weight = 1.0
    lights = []
    for off, inten, col in ((V(-120, 220, 160), 120.0, (1.0, 0.93, 0.82)), (V(160, 160, -40), 45.0, (0.75, 0.85, 1.0)), (V(0, -200, 120), 60.0, (1, 1, 1))):
        L = spawn(unreal.PointLight, unreal.Transform(O + off, unreal.Rotator(0, 0, 0), V(1, 1, 1)))
        lc = L.point_light_component; lc.set_mobility(unreal.ComponentMobility.MOVABLE)
        lc.set_intensity(inten * LIGHT); lc.set_attenuation_radius(1500.0); lc.set_light_color(unreal.LinearColor(*col, 1.0)); lc.set_cast_shadows(False)
        lights.append(L)
    # (each thing twice: with its materials and all in white, far apart until its turn; a change reaches the renderer at
    # the end of a frame, so the shots are taken over frames by a tick callback, each thing a first time to compile its
    # shaders and a second time for the picture)
    if ONLY: things = [x for x in things if x[0] in ONLY]
    pairs = []
    for k, (icon, m, xf, big) in enumerate(things):
        two = []
        for white_ in (False, True):
            a = spawn(unreal.StaticMeshActor, unreal.Transform(O + V(5000, 3000 * k, 0), unreal.Rotator(0, 0, 0), V(1, 1, 1)))
            c = a.static_mesh_component; c.set_mobility(unreal.ComponentMobility.MOVABLE); c.set_static_mesh(m)
            for i in range(c.get_num_materials()): c.set_material(i, white if white_ else m.get_material(i))
            two.append(a)
        pairs.append(two)
    Oxf = unreal.Transform(O, unreal.Rotator(0, 0, 0), V(1, 1, 1))
    st = {"i": 0, "pass": 0, "f": -240, "shots": []}
    def place(k):
        icon, m, xf, big = things[k]
        for a in pairs[k]: a.set_actor_transform(ML.compose_transforms(xf, Oxf), False, False)
        d = big * 0.62 / math.tan(math.radians(10.0)); cam = O + V(0, d, 0)
        cap.set_actor_location(cam, False, False); cap.set_actor_rotation(ML.find_look_at_rotation(cam, O), False)
    def away(k):
        for a in pairs[k]: a.set_actor_location(O + V(5000, 3000 * k, 0), False, False)
    def shot(k, white_, name):
        comp.clear_show_only_components(); comp.show_only_actor_components(pairs[k][1 if white_ else 0], False)
        comp.capture_source = unreal.SceneCaptureSource.SCS_BASE_COLOR if white_ else unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
        comp.capture_scene()
        if name: unreal.RenderingLibrary.export_render_target(w, rt, OUT, name)
    def finish():
        unreal.unregister_slate_post_tick_callback(st["h"])
        unreal.SystemLibrary.execute_console_command(w, "r.TextureStreaming 1")
        for a in made:
            try: eas.destroy_actor(a)
            except Exception: pass
        made.clear(); pairs.clear()
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        print("ICONS shot", len(st["shots"]), st["shots"])
    def tick(dt):
        try:
            st["f"] += 1; f = st["f"]
            if f < 0: return
            k = st["i"]; icon = things[k][0]; final = st["pass"] == 1
            # frame 0: placed; 1-12: lit shots (the last kept); 13-16: mask shots (the last kept); 17: moved away
            if f == 0: place(k)
            elif 1 <= f <= 12: shot(k, False, f"{icon}_rgb.png" if final and f == 12 else None)
            elif 13 <= f <= 16: shot(k, True, f"{icon}_mask.png" if final and f == 16 else None)
            elif f >= 17:
                away(k)
                if final: st["shots"].append(icon)
                st["i"] += 1; st["f"] = -1
                if st["i"] >= len(things):
                    if final: finish(); return
                    st["pass"] = 1; st["i"] = 0; st["f"] = -60
        except Exception as e:
            print("ICONS failed", e); finish()
    # (every texture at full size: with streaming on, the first shields of a long batch were shot with their low mips)
    unreal.SystemLibrary.execute_console_command(w, "r.TextureStreaming 0")
    st["h"] = unreal.register_slate_post_tick_callback(tick)
    __keep__ = True
    print("ICONS started", len(things))

elif MODE == "import":
    EAL = unreal.EditorAssetLibrary; DEST = "/Game/RandomDungeon/UI"
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if not ues.get_editor_world().get_path_name().startswith(MAP + "."): unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    names = sorted(f[:-4] for f in os.listdir(OUT) if f.endswith(".png") and not f.endswith(("_rgb.png", "_mask.png")))
    tasks = []
    for n in names:
        t = unreal.AssetImportTask()
        t.set_editor_property("filename", os.path.join(OUT, n + ".png")); t.set_editor_property("destination_path", DEST)
        t.set_editor_property("destination_name", "T_RDM4_" + n); t.set_editor_property("replace_existing", True)
        t.set_editor_property("automated", True); t.set_editor_property("save", False); tasks.append(t)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    gen = next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    ua = gen.get_editor_property("ui_art")
    for n in names:
        a = unreal.load_asset(f"{DEST}/T_RDM4_{n}")
        if not a: raise SystemExit(f"867: {n} was not imported")
        a.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
        a.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
        a.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        a.set_editor_property("never_stream", True); a.set_editor_property("srgb", True)
        a.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP); a.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
        EAL.save_loaded_asset(a, False)
        art = unreal.RDUIArt(); art.set_editor_property("texture", a)
        art.set_editor_property("border", unreal.Vector4(0, 0, 0, 0)); art.set_editor_property("inner", unreal.Vector4(0, 0, 1, 1))
        ua[unreal.Name(n)] = art
    gen.set_editor_property("ui_art", ua)
    # (the found weapons: their items and every fit of them)
    its = []
    for it in gen.get_editor_property("items"):
        if it.kind == unreal.RDItemKind.WEAPON and wicon(str(it.name)) in names:
            it.icon = unreal.Name(wicon(str(it.name))); fits = []
            for fx in it.weapon_fits:
                wd = fx.weapon; wd.icon = it.icon; fx.weapon = wd; fits.append(fx)
            it.weapon_fits = fits
        its.append(it)
    gen.set_editor_property("items", its)
    les.save_current_level()
    have = [str(k) for k in gen.get_editor_property("ui_art").keys()]
    want = sorted({str(i.icon) for i in gen.get_editor_property("items") if i.kind in (unreal.RDItemKind.SHIELD, unreal.RDItemKind.TORCH, unreal.RDItemKind.WEAPON)})
    print("ICONS imported", len(names), "| items without a picture:", [n for n in want if n not in have])
    del gen, ua
