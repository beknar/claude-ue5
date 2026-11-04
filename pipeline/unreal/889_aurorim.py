"""mistward_castle's final boss, Aurorim (the user's spec of 2026-11-03): his monster and the final boss's switches on the
open mistward_castle (play stopped). Run after 600_tripo_import.py Aurorim (his mesh, clips and material from
blender_numpy/aurorim_build.py's SourceArt/jrpg_aurorim), and after anything that writes the castle's monsters anew (859,
866, 879: they keep a monster they do not know only if they copy the table; run this again after them).

His monster (FRDMonsterDef "Aurorim"; tier 6: never one of a tier's own, only the final boss):
  - his clips: Idle (hovering), Fly (his walk), Box_01 / Box_03 / Box_02 (punches: hit times from build.json), Hit_to_body_01,
    Death; Throw (the lance), Cast (the light from above)
  - his hit points and blows: the last tier's strongest kind's factors (the tier's boss's BossHealth, BossDamage on top, as
    PlaceFinalBoss spawns him); his voice: the Titan's
  - long range (13 to 32 m): a thrown lance (Knights_Pack's Knight_04 spear flying, point first), a gust where it leaves him
    and a lightning burst where it lands
  - middle range (3.5 to 13 m): a beam of light from above: Loot Drops' blue ring where she stands, 0.9 s later MysticDungeon's
    light rays and the holy shield's burst there (230 cm round)
  - melee: his punches with wind round both fists: the Martial Artist's Straight Punch's own look (StylizedShields' wind
    shield and Magic Projectiles' wind, as 872 tuned them for her fist), on his LeftHand and RightHand
  - he levitates 45 cm over the floor, bobbing 8 cm
The final boss's switches: on, his kind, 6 to 10 of the last tier's monsters round him, 2500 gold, the door (Crownfall's arch
SM_S_ArchDoorV1 3.8 m tall, Castle of Eternal Mist's grating SM_Door_01 in it while sealed, MysticDungeon's light rays in it
once open)."""
import unreal, json, os

LEVEL = "/Game/RandomDungeon/Maps/mistward_castle"
SRC = r"E:\code\claude-ue5\claude_ue5\SourceArt\jrpg_aurorim"
A = "/Game/JRPG/AurorimAnims/AS_Aurorim_"
FX = {"ray": "/Game/MysticDungeon/VFX/NS_LightRayFX_01", "holy": "/Game/StylizedShieldsVol1/Particles/NiagaraSystems/NS_Shield_Holy_01",
      "ring": "/Game/LootDropsV2/Particles/NiagaraSystems/LootDrop02/NS_LootDrop02_lvl3_blue",
      "gust": "/Game/MagicProjectilesVol5/Particles/NiagaraSystems/Muzzles/NS_Muzzle_Wind01",
      "bolt": "/Game/StylizedSlashesV2/Particles/NiagaraSystems/NS_SlashImpact_Lightning"}
SPEAR = "/Game/Knights_Pack/Meshes/Knight_04/Weapon/SM_Knight_04_Spear"
DOOR_FRAME = "/Game/Crownfall/Assets/NaveAssets/SM_S_ArchDoorV1"
DOOR_GATE = "/Game/CastleofEternalMist/Meshes/Grating/SM_Door_01"

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
w = ues.get_editor_world()
if not w.get_path_name().startswith(LEVEL + "."): les.load_level(LEVEL); w = ues.get_editor_world()
gen = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.RDDungeonGenerator)[0]
info = json.load(open(os.path.join(SRC, "build.json")))
ld = lambda p: unreal.load_asset(p)
def need(p):
    a = ld(p)
    assert a, "missing " + p
    return a

mons = list(gen.get_editor_property("monsters"))
mons = [m for m in mons if str(m.name) != "Aurorim"]
t5 = [m for m in mons if m.tier == 5]
titan = next((m for m in t5 if "Titan" in str(m.name) or "Titan" in str(m.title)), t5[0] if t5 else None)
d = unreal.RDMonsterDef()
d.name = "Aurorim"; d.title = "Aurorim"
d.mesh = need("/Game/JRPG/Character/SK_JRPG_Aurorim")
d.idle = need(A + "Idle"); d.walk = need(A + "Fly")
d.walk_speed = 300.0; d.walk_clip_speed = 300.0
d.capsule_radius = 45.0; d.capsule_half_height = 96.0
d.mesh_z = -96.0; d.mesh_yaw = -90.0; d.scale = 1.0
ht = info["hit_times"]
d.attacks = [need(A + "Box_01"), need(A + "Box_03"), need(A + "Box_02")]
d.hit_times = [ht["Box_01"], ht["Box_03"], ht["Box_02"]]
d.get_hit = need(A + "Hit_to_body_01"); d.death = need(A + "Death")
# (the last tier's strongest kind's factors: the tier's boss is its strongest kind)
d.health_factor = max(m.health_factor for m in t5) if t5 else 1.2
d.damage_factor = max(m.damage_factor for m in t5) if t5 else 1.2
d.reach = 150.0; d.attack_interval = 1.5
if titan: d.sound_set = titan.sound_set; d.step_length = titan.step_length
d.tier = 6
# long range: the lance
d.shoots = True; d.ranged_range = 3200.0; d.ranged_min = 1300.0; d.ranged_damage = 0.75; d.ranged_cooldown = 3.5; d.ranged_speed = 2400.0
d.ranged_clip = need(A + "Throw"); d.ranged_release = float(info["throw_release"])
d.ranged_fx = None; d.ranged_muzzle_fx = need(FX["gust"]); d.ranged_hit_fx = need(FX["bolt"]); d.ranged_fx_scale = 0.7
d.ranged_theme = "a thrown lance"
d.ranged_mesh = need(SPEAR); d.ranged_mesh_scale = 1.0; d.ranged_mesh_rot = unreal.Rotator(roll=0.0, pitch=-90.0, yaw=0.0)
# middle range: the light from above
d.sky_beam = True; d.beam_min = 350.0; d.beam_max = 1300.0; d.beam_damage = 1.0; d.beam_radius = 230.0; d.beam_delay = 0.9; d.beam_cooldown = 5.5
d.beam_clip = need(A + "Cast"); d.beam_release = float(info["cast_release"])
d.beam_fx = need(FX["ray"]); d.beam_mark_fx = need(FX["ring"]); d.beam_hit_fx = need(FX["holy"])
d.beam_fx_scale = 0.35; d.beam_mark_scale = 1.8
d.beam_fx_user_scale = False; d.beam_mark_user_scale = False; d.beam_hit_user_scale = True
# melee: the Martial Artist's Straight Punch's wind, on both fists
look = []
for h in gen.get_editor_property("heroes"):
    if "Martial" not in str(h.name): continue
    for wdef in list(h.weapons) + list(h.locked_weapons):
        if str(wdef.name) == "Straight Punch":
            look = [(l.fx, l.scale, l.user_scale) for l in wdef.limb_fx if l.fx and l.stop_at > l.start_at]
if not look:
    look = [(need("/Game/StylizedShieldsVol1/Particles/NiagaraSystems/NS_Shield_Wind_01"), 0.2, True),
            (need("/Game/MagicProjectilesVol5/Particles/NiagaraSystems/Projectiles/NS_Projectile_Wind01"), 0.7, False)]
d.fist_fx = [l[0] for l in look]; d.fist_fx_scale = [float(l[1]) for l in look]; d.fist_fx_user_scale = [bool(l[2]) for l in look]
d.fist_bones = ["LeftHand", "RightHand"]
# he levitates
d.hover_height = 45.0; d.hover_bob = 8.0; d.hover_period = 1.8
mons.append(d)
gen.set_editor_property("monsters", mons)
# the final boss's switches
gen.set_editor_property("final_boss_on", True)
gen.set_editor_property("final_boss_kind", "Aurorim")
gen.set_editor_property("final_boss_minions", unreal.IntPoint(6, 10))
gen.set_editor_property("final_boss_gold", 2500)
gen.set_editor_property("final_boss_scale", 1.0)
gen.set_editor_property("final_door_frame", need(DOOR_FRAME))
gen.set_editor_property("final_door_gate", need(DOOR_GATE))
gen.set_editor_property("final_door_fx", need(FX["ray"]))
gen.set_editor_property("final_door_height", 380.0)
gen.set_editor_property("final_door_fx_scale", 0.3)
unreal.EditorLoadingAndSavingUtils.save_map(w, LEVEL)
back = [m for m in gen.get_editor_property("monsters") if str(m.name) == "Aurorim"]
print("AURORIM", len(back), "health", round(d.health_factor, 2), "damage", round(d.damage_factor, 2), "sound", d.sound_set, "fist", [(l[0].get_name(), l[1], l[2]) for l in look],
      "hit", d.hit_times, "final", gen.get_editor_property("final_boss_on"), str(gen.get_editor_property("final_boss_kind")), "max tier", gen.get_editor_property("max_tier"))
