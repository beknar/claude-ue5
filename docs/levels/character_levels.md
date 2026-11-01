# The character levels

[README](../../README.md) · [Levels](../../README.md#levels) · [Documentation](../../README.md#documentation)

## What's in it

| Level | Character | What's in it |
|---|---|---|
| `L_Fig4_Studio` | `fig4`, a MetaHuman conformed to a 3D scan | Photo-studio cyclorama, plinth, studio and MegaLights lighting, strand hair groom, refitted scanned outfit |
| `L_Fig4_Meadow` | fig4 (`BP_Fig4Character`) | Outdoor meadow: procedural Nanite terrain, rocks and grass. Heel-stance locomotion retargeted from the UE mannequin |
| `L_Meshy_Meadow` | Meshy AI biped (`BP_MeshyCharacter`); the JRPG characters (`BP_JRPGFem1Character` … `BP_JRPGFem5Character`) | Same meadow; 18 moves on input actions plus a sprint. Also the stage of the JRPG characters, whose scripts set the meadow's game mode to the one built last: Fem1 (a Meshy rig playing the soldier's retargeted set, or the FF showcase set), Fem3 and Fem4 (Meshy meshes; one that comes unrigged, such as Fem3, is given a skeleton by `jrpg_autorig.py`), Fem5 (`jrpg-fem5-tripo`, an animated Tripo GLB playing her own idle / walk / run: the player of every later level) |
| `soldier_level` | Dystopia Soldier 02 (`BP_SoldierCharacter`) | Same meadow; Unity-sourced soldier with retargeted locomotion |
| `ff_level` | Tripo anime female (`BP_FFCharacter`) | Same meadow; static GLB rigged onto a UE4-mannequin skeleton |
| `ff2_level` | Animated Tripo anime female (`BP_FF2Character`) | Same meadow; clips fixed on the sole contacts so she doesn't float or slide |

## Rebuild

**JRPG and Tripo characters** (`500`–`540`, `600`–`650`; they play in `L_Meshy_Meadow`):
- A rigged Meshy character (Fem1): `blender_numpy/jrpg_build.py model.glb out_dir name` (a real `root` bone, centimetre rig, textures), `500_jrpg_import.py Fem1`, `510_jrpg_retarget.py` (the soldier's whole set retargeted onto her, speeds measured from her stance foot), `520_jrpg_character.py soldier|ff Fem1` (`540_jrpg_ff_anims.py` first for the `ff` set).
- An unrigged Meshy mesh (Fem3): `blender_numpy/jrpg_autorig.py model.glb out_dir name [height_cm]` finds the joints in the mesh (arm line, armpits, crotch, slice centroids) and skins it to a mannequin-named skeleton; then as above.
- Clips a Tripo GLB lacks are made by a clip maker given to `tripo_build.py` (its last argument): `summoner_clips.py` (the Summoner: the Mage's clips retargeted onto her rig, bone by bone as the Mage's bones point, her flinch and death from FBX exports of the Mage's), `caster_clips.py` (girl-caster-tripo: an idle and three casts; preview of its key poses with `blender -b -P caster_clips.py -- model.glb out_prefix`) and `darkcaster_clips.py` (girl-darkcaster-tripo: the right hand closed on a hilt in all her clips, two left-hand casts, three sword cuts; its preview prints where the blade points against where it was meant to). They are imported as `Caster` and `DarkCaster` through `600`–`620` (`620_tripo_character.py <CH> 85 keepmeadow`: the meadow keeps its game mode).
- An animated Tripo character (Fem5): `blender_numpy/tripo_build.py model.glb out_dir name tag [height_cm]` (the models are in `ai models/`, under CC BY 4.0: Fem5 is `Warrior.glb`, formerly jrpg-fem5-tripo.glb) (the mesh and its clips as two FBX files), `600_tripo_import.py Fem5`, `610_tripo_anim.py Fem5` (the template's state machine with her own idle / walk / run), `615_tripo_ground.py Fem5` (Tripo pins the hips: each clip is lowered until the planted foot is on the ground), `620_tripo_character.py Fem5` (her arms are lengthened in the build, `blender_numpy/tripo_proportions.py`; after a build of the Warrior or the Warlock, `860_hero_arm_lengths.py` brings the mesh into Unreal without remaking her clips and Blueprints); showcase with `640_tripo_demo.py Fem5` and `650_tripo_sequence.py Fem5`.
