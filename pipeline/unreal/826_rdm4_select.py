"""random_dungeonmagic_level4: the menu level before the dungeon, /Game/RandomDungeon/Maps/random_dungeonmagic_level4_select.
A studio (the trio showcase's cyclorama, plinth and light rig, 660 / 663) with a turntable: the plinth and the hero on it
turn (ARDHeroSelect, C++); the other heroes wait hidden. Each hero is her own skeletal mesh with her character's animation
Blueprint (standing: her idle; the Warlock's hair swings as she turns) and her starting weapons as the dungeon has them
(the heroes of random_dungeonmagic_level4's generator, 825): the first one in her hands (the Warrior's sword and shield, the
Warlock's sword, the Rogue's two daggers), the others where she carries them (the Rogue's crossbow on her back); the Mage
has spells only. The HUD (ARDHeroSelectHUD) shows her card: hit points, mana, abilities, armour, what she starts with.
The game mode is ARDHeroSelectGameMode (no pawn: the view is the studio camera); START opens random_dungeonmagic_level4
with ?Hero=<name>. Play this level to play random_dungeonmagic_level4 with a hero of your choice.
Run after 825. Idempotent (actors tagged rdm4_select).
With the argument 5 it makes random_dungeonmagic_level5's menu instead (random_dungeonmagic_level5_select: its five
heroes, 852; START opens random_dungeonmagic_level5), its painted pieces and lettering those 830 gave level 4's menu.
Args: [4 | 5]"""
import sys, unreal
LV = sys.argv[1] if len(sys.argv) > 1 else "4"
eal = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
V = unreal.Vector; Rot = unreal.Rotator
DUNGEON = "/Game/RandomDungeon/Maps/random_dungeonmagic_level" + LV; LEVEL = DUNGEON + "_select"
TAG = unreal.Name(f"rdm{LV}_select")
UIART = UIFONTS = None
if LV != "4":
    # (the painted menu as level 4's has it: 830 gave its HeroSelect the pieces and the lettering)
    les.load_level("/Game/RandomDungeon/Maps/random_dungeonmagic_level4_select")
    s4 = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDHeroSelect))
    # (as text: the maps Python hands back point into that actor, which is gone once another level is loaded; set from
    # them, the editor hung)
    UIART = {str(k): v.export_text() for k, v in s4.get_editor_property("ui_art").items()}
    UIFONTS = {str(k): v.export_text() for k, v in s4.get_editor_property("ui_fonts").items()}
    del s4
L = lambda p: unreal.load_asset(p.split(".")[0])
# ---- the heroes, as the dungeon has them (as text: nothing of that level is kept once this one is opened)
if not ues.get_editor_world().get_path_name().startswith(DUNGEON + "."): les.load_level(DUNGEON)
gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
HTXT = [h.export_text() for h in gen.get_editor_property("heroes")]; assert len(HTXT) >= 4, len(HTXT)
del gen
# ---- the level
if eal.does_asset_exist(LEVEL): les.load_level(LEVEL)
else: les.new_level(LEVEL)
w = ues.get_editor_world(); assert w.get_path_name().startswith(LEVEL + "."), w.get_path_name()
for a in eas.get_all_level_actors():
    if TAG in a.tags or a.get_class().get_name() in ("StaticMeshActor", "SkeletalMeshActor", "RectLight", "PointLight", "SkyLight", "PostProcessVolume", "CineCameraActor",
                                                     "ExponentialHeightFog", "RDHeroSelect", "PlayerStart"):
        eas.destroy_actor(a)
def spawn(cls, loc, rot=(0, 0, 0), label=None):
    a = eas.spawn_actor_from_class(cls, V(*loc), Rot(pitch=rot[0], yaw=rot[1], roll=rot[2])); assert a, cls
    a.tags = [TAG]
    if label: a.set_actor_label(label)
    return a
def mesh_actor(path, loc, label=None, scale=1.0):
    a = spawn(unreal.StaticMeshActor, loc, label=label); a.static_mesh_component.set_static_mesh(L(path)); a.set_actor_scale3d(V(scale, scale, scale))
    a.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE); return a
def aim(a, target): a.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(a.get_actor_location(), V(*target)), False)
# ---- the studio (660 / 663's rig, aimed at the turntable)
P0, PZ = (0.0, -40.0), 6.0           # the plinth's middle, its top
mesh_actor("/Game/Fig4/Studio/Meshes/SM_Cyclorama/StaticMeshes/SM_Cyclorama", (0, 0, 0), label="Cyclorama")
plinth = mesh_actor("/Game/Fig4/Studio/Meshes/SM_Plinth/StaticMeshes/SM_Plinth", (P0[0], P0[1], 0), label="Turntable")
def rect(label, loc, target, wdt, hgt, cd, temp, barn=45, att=3000):
    a = spawn(unreal.RectLight, loc, label=label); c = a.light_component
    for k, v in (("intensity_units", unreal.LightUnits.CANDELAS), ("intensity", cd), ("source_width", wdt), ("source_height", hgt), ("barn_door_angle", barn),
                 ("barn_door_length", 30), ("use_temperature", True), ("temperature", temp), ("attenuation_radius", att)):
        c.set_editor_property(k, v)
    aim(a, target); return a
FIG = (P0[0], P0[1], 100.0)
rect("Key", (-380, 420, 420), FIG, 160, 120, 260, 5400)
rect("Fill", (460, 460, 220), FIG, 220, 180, 55, 5800, barn=10)
rect("Rim_L", (-420, -420, 300), FIG, 40, 200, 300, 6800, barn=60)
rect("Rim_R", (420, -420, 300), FIG, 40, 200, 280, 6800, barn=60)
rect("Top", (0, -80, 420), (P0[0], P0[1], 0), 80, 60, 70, 5000)
rect("Floor_Wash", (0, 700, 520), (0, 100, 0), 400, 200, 18, 4800, barn=20)
sky = spawn(unreal.SkyLight, (0, 0, 500), label="Sky"); sc = sky.light_component
sc.set_editor_property("intensity", 0.18); sc.set_editor_property("lower_hemisphere_is_black", True); sc.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_CAPTURED_SCENE)
ppv = spawn(unreal.PostProcessVolume, (0, 0, 100), label="PPV"); ppv.set_editor_property("unbound", True); s = ppv.settings
for k, v in (("dynamic_global_illumination_method", unreal.DynamicGlobalIlluminationMethod.LUMEN), ("reflection_method", unreal.ReflectionMethod.LUMEN),
             ("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL), ("auto_exposure_apply_physical_camera_exposure", False), ("auto_exposure_bias", -2.0),
             ("bloom_intensity", 0.45), ("vignette_intensity", 0.7), ("film_grain_intensity", 0.05)):
    try: s.set_editor_property("override_" + k, True)
    except Exception: pass
    s.set_editor_property(k, v)
ppv.set_editor_property("settings", s)
# ---- the camera: the turntable right of the middle (her card is on the left of the screen)
CAM, LOOK = (-95.0, 420.0, 118.0), (-95.0, -40.0, 100.0)
cam = spawn(unreal.CineCameraActor, CAM, label="Select_Camera"); aim(cam, LOOK)
cc = cam.get_cine_camera_component()
fb = cc.get_editor_property("filmback"); fb.sensor_width = 36.0; fb.sensor_height = 20.25; cc.set_editor_property("filmback", fb)
cc.set_editor_property("current_focal_length", 35.0); cc.set_editor_property("current_aperture", 5.6)
fs = cc.get_editor_property("focus_settings"); fs.focus_method = unreal.CameraFocusMethod.MANUAL
fs.set_editor_property("manual_focus_distance", abs(CAM[1] - P0[1])); cc.set_editor_property("focus_settings", fs)
# ---- the heroes on the turntable, each with her weapons
heroes = []
for t in HTXT:
    h = unreal.RDHeroDef(); h.import_text(t); heroes.append(h)
figures = []
for h in heroes:
    pawn = unreal.get_default_object(h.pawn_class)
    m = pawn.get_editor_property("mesh")
    sk = m.get_skeletal_mesh_asset() if hasattr(m, "get_skeletal_mesh_asset") else m.get_editor_property("skeletal_mesh")
    fig = spawn(unreal.SkeletalMeshActor, (P0[0], P0[1], PZ), label=f"Hero_{h.name}")
    c = fig.skeletal_mesh_component
    c.set_skeletal_mesh_asset(sk) if hasattr(c, "set_skeletal_mesh_asset") else c.set_editor_property("skeletal_mesh", sk)
    c.set_mobility(unreal.ComponentMobility.MOVABLE)
    # (her character's own animation Blueprint: her idle where she stands, the Warlock's hair after it)
    c.set_editor_property("animation_mode", unreal.AnimationMode.ANIMATION_BLUEPRINT)
    c.set_editor_property("anim_class", m.get_editor_property("anim_class"))
    c.set_editor_property("visibility_based_anim_tick_option", unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
    # (a Tripo mesh faces +Y: at the turntable's yaw 0 she looks at the camera)
    def hold(mesh, bone, grip, what):
        if mesh is None or str(bone) in ("", "None"): return None
        a = mesh_actor(mesh.get_path_name(), (0, 0, 0), label=f"Hero_{h.name}_{what}")
        a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        a.attach_to_component(c, bone, unreal.AttachmentRule.SNAP_TO_TARGET, unreal.AttachmentRule.SNAP_TO_TARGET, unreal.AttachmentRule.KEEP_WORLD, False)
        a.set_actor_relative_transform(grip, False, False); return a
    drawn = next((i for i, d in enumerate(h.weapons) if not d.alongside), -1)
    for i, d in enumerate(h.weapons):
        if i == drawn:
            hold(d.mesh, d.hand_bone, d.grip, f"{d.name}_Hand"); hold(d.off_hand_mesh, d.off_hand_bone, d.off_hand_grip, f"{d.name}_OffHand")
        else:
            hold(d.mesh, d.holster_bone, d.holster_grip, f"{d.name}_Carried"); hold(d.off_hand_mesh, d.off_hand_holster_bone, d.off_hand_holster_grip, f"{d.name}_OffCarried")
    fig.set_actor_hidden_in_game(len(figures) > 0)
    figures.append(fig)
sel = spawn(unreal.RDHeroSelect, (0, 0, 0), label="HeroSelect")
sel.set_editor_property("heroes", heroes); sel.set_editor_property("figures", figures)
sel.set_editor_property("turntable", plinth); sel.set_editor_property("camera", cam)
sel.set_editor_property("target_level", DUNGEON); sel.set_editor_property("front_yaw", 0.0); sel.set_editor_property("turn_rate", 28.0)
if UIART is not None:
    def back(d, cls):
        out = {}
        for k, txt in d.items():
            v = cls(); v.import_text(txt); out[unreal.Name(k)] = v
        return out
    sel.set_editor_property("ui_art", back(UIART, unreal.RDUIArt)); sel.set_editor_property("ui_fonts", back(UIFONTS, unreal.RDUIFont))
ps = spawn(unreal.PlayerStart, (0, 300, 100), label="Select_PlayerStart")
ws = w.get_world_settings(); ws.set_editor_property("default_game_mode", unreal.RDHeroSelectGameMode.static_class())
les.save_current_level()
print(f"RDM{LV}SELECT", LEVEL, "| heroes", [str(h.name) for h in sel.heroes], "| figures", [f.get_actor_label() for f in sel.figures],
      "| anim", [str(f.skeletal_mesh_component.get_editor_property("anim_class").get_name()) if f.skeletal_mesh_component.get_editor_property("anim_class") else None for f in figures],
      "| attached", [len(f.get_attached_actors()) for f in figures], "| game mode", ws.get_editor_property("default_game_mode").get_name())
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
