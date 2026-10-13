# claude-ue5

An Unreal Engine 5.8 project built almost entirely from scripts. The scripts drive the running editor over Python remote execution, and Blender + numpy prepare the source art. The project has several playable character showcase levels: third-person controls, a recorded demo route and a Movie Render Queue showcase video for each.

This repository is **source only**: the pipeline scripts, project config and small data files. Unreal assets (`Content/`), source art binaries, renders and the third-party packs they come from stay local. See [What's not in the repo](#whats-not-in-the-repo).

## Early results

Stills from the showcase videos: 1080p Movie Render Queue renders of each level's `*_Cine` copy, with the demo character running its recorded route.

**FF — Tripo anime female** (`ff_level`). A static GLB rigged onto a UE4-mannequin skeleton, with locomotion retargeted from the template.

| Idle | Run | Close-up |
|---|---|---|
| ![FF idle](docs/images/ff_idle.jpg) | ![FF run](docs/images/ff_run.jpg) | ![FF close-up](docs/images/ff_front.jpg) |

**FF2 — animated Tripo anime female** (`ff2_level`). Her own clips, grounded on the sole contacts so she doesn't float or slide.

| Jump | Boxing | Casting |
|---|---|---|
| ![FF2 jump](docs/images/ff2_jump.jpg) | ![FF2 boxing](docs/images/ff2_box.jpg) | ![FF2 casting](docs/images/ff2_spell.jpg) |

**Dystopia Soldier 02** (`soldier_level`). Converted from a Unity-format Fab pack, with per-part PBR materials and retargeted locomotion.

| Idle | Flamethrower | Close-up |
|---|---|---|
| ![Soldier idle](docs/images/soldier_idle.jpg) | ![Soldier flamethrower](docs/images/soldier_flamethrower.jpg) | ![Soldier close-up](docs/images/soldier_front.jpg) |

## Levels

| Level | Character | What's in it |
|---|---|---|
| `L_Fig4_Studio` | `fig4`, a MetaHuman conformed to a 3D scan | Photo-studio cyclorama, plinth, studio and MegaLights lighting, strand hair groom, refitted scanned outfit |
| `L_Fig4_Meadow` | fig4 (`BP_Fig4Character`) | Outdoor meadow: procedural Nanite terrain, rocks and grass. Heel-stance locomotion retargeted from the UE mannequin |
| `L_Meshy_Meadow` | Meshy AI biped (`BP_MeshyCharacter`) | Same meadow; 18 moves on input actions plus a sprint |
| `soldier_level` | Dystopia Soldier 02 (`BP_SoldierCharacter`) | Same meadow; Unity-sourced soldier with retargeted locomotion |
| `ff_level` | Tripo anime female (`BP_FFCharacter`) | Same meadow; static GLB rigged onto a UE4-mannequin skeleton |
| `ff2_level` | Animated Tripo anime female (`BP_FF2Character`) | Same meadow; clips fixed on the sole contacts so she doesn't float or slide |
| `castle_level` | FF2 | The Medieval Fantasy Village pack's map with walk-in houses: doors, chests, trunks, wardrobes and barrels open with **F**. Interiors are furnished by building purpose (tavern, manor, homes, bakery, stable, barn, storehouse, smithy) with lofts, attics and lighting. Water splashes in the river |
| `sf-city-level` | jrpg-fem5-tripo (`BP_SFC_Fem5Character`: her own idle/walk/run, foot IK) | The Open World Science fiction City with the Monolith Megastructure streamed in beside it, joined by a 200 m bridge road. Four structures with furnished rooms behind automatic sci-fi blast doors: Port Authority (office + armory), neon noodle bar, hab apartment (living room + bedroom), excavation lab (relic lab + server room). Invisible barrier walls along every drop into the void, a fall guard, and a scripted walk test (`709`/`710`) |
| `random_level` | jrpg-fem5-tripo (`BP_SFC_Fem5Character`) | Procedural medieval town (C++ `ARTTownGenerator`). Starts as a 500 m x 500 m square built with a fixed seed; whenever she nears the edge of town heading outward, the next 250 m of terrain, cobbled streets, furnished buildings, props and foliage is generated ahead of her (fresh seed each play, never saved). Each new cell is marked as it appears: a glowing curtain rises on its border and a scan wave sweeps across it, the cell drawn as a cyan ghost until the wave passes. Buildings: the Modular Medieval Town packs' furnished docks houses, tavern (fireplace, dining tables, chairs, bar), stores and Sherwood cabins, streamed in as level instances and turned to face the street. Doors swing open as she approaches; bedroom chests, wardrobes and crates open with **F** |
| `random_dungeon_level` | jrpg-fem5-tripo (`BP_SFC_Fem5Character`) | Procedural dungeon (C++ `ARDDungeonGenerator`). A 252 m x 252 m start section of 49 interconnected rooms (fixed seed, saved), with hallways leaving every edge; walking toward the edge generates the next section (fresh seed each play, never saved) with random_level's reveal effect. Rooms have a purpose with matching furniture and lighting: great hall, barracks, prison cells, torture chamber, storeroom, armory, kitchen, library, chapel, crypt, treasury, guard room, forge; hallways are guard passages, supply passages or catacomb tunnels. Doors (crypt double doors, cell doors) and every container (chests, trunks, wardrobes, barrels, crates) open with **F**. Minimap of generated / discovered rooms, full map on **M**. Monsters from Creatures_Pack (troll, daemon, horned demon, ripper dog, spider, mutant) in 40% of the rooms wander from room to room |
| `random_dungeoncombat_level` | jrpg-fem5-tripo (`BP_SFC_Fem5Character`) with three melee weapons | `random_dungeon_level` with fighting (the generator's `bCombat`). She has 100 hit points and a sword (22 damage a blow), a spear (17, long reach) and an axe (36, slower, wide arc) from the Medieval_Weapons pack, the first two with a shield; she wields each with attack, flinch and death clips of a Fab animation pack made for it, retargeted to her. Monsters in 30% of the rooms notice her, give chase over the tile grid, attack with their own attack clips, flinch when hit and die. In the start section (the first 252 m square) the average monster has 50 hit points and does 11 a blow; in every section generated in play it is on a par with her (100 hit points, 25 a blow: her average). Out of a fight her hit points come back; at 0 she falls and stands up again in the middle of the start section. HUD: a status panel in the bottom right corner (hit points, the three weapons with their damage, kills), a bar over each monster in the fight, damage numbers; the minimap (top right) and the **M** map are a miniature of the dungeon (stone floors coloured by room, walls, doors, chests, torches), with every room named on the M map. She starts in the middle of the start section; generated sections are never saved. **Blood:** a blow throws a burst of drops and spray from where it landed (from her too when she is hit); the drops fall, and leave marks on the floor, walls and furniture; a pool spreads under a body. **Wounds:** every blow leaves a wound on that monster alone, on its skin where the weapon met it (stain, torn flesh, a dark open middle, blood running down), and the worse off it is the more of it is bloodied. **Sound** (from a local sound library): her footsteps (walking and running), her breath and her voice when she is hurt or falls, the swing and the weapon landing; each monster kind's footsteps, growl, roar when it notices her, cry when hurt and death; torches, braziers and hearths as she comes near, doors and chests opening and closing, the rumble of a section being generated, a quiet room tone. Everything that is not her own is heard from where it is and fades with its distance to her |
| `random_isometric_village_level` | jrpg-fem5-tripo (`BP_SFC_Fem5Character`) | Procedural nucleated village seen from a fixed isometric camera (C++ `AIVVillageGenerator`). One village around one hub: a cobbled market square (fountain, well, stalls) with the church, tavern, smithy, bakery, store and elder's hall facing it, ring streets closing around it and short lanes staggered between the rings, three main roads winding out. Houses stand along the streets with gardens, orchards and fields behind, thinning into farmsteads away from the square. The 250 m x 250 m start section is built with a fixed seed and saved; walking toward the edge generates the next 250 m section (fresh seed each play, never saved) on the same rings and lanes, with random_level's reveal effect. Houses are assembled from the House Forge kit (thatch / timber / stone) and furnished by purpose (cottage, farmhouse, tavern, smithy, bakery, store, carpenter, barn, storehouse, church, elder's hall); indoors the roof and the camera-side walls are cut away, and her silhouette shows through anything that hides her. Doors and every container open with **F**. Unarmed villagers (townsfolk, peasants, youths, a servant pair, the elder, a physician, a lady: three for every ten buildings of each 250 m section, in play only) wander the streets and the square, give way to her and step aside. **Q** / **E** turn the view in 45° steps (the cutaway and the maps turn with it) and the view zooms in to a close view of her. A stylised miniature of the village is the minimap; **M** opens the big map with every building labelled |
| `starship_level` | A space fighter (C++ `ASSFighter`) | Outer space: a 5 km x 5 km x 5 km combat area round a space station, seen from a chase camera behind the fighter. The fighter is a kitbash of pack meshes in the style of a Colonial Viper (a white-and-red delta hull with two engines, stub wings, a third engine with a tail fin, wing-tip cannons, four missiles under the wings; engine flames that follow the throttle and a ribbon contrail from each engine). Two weapons: cannons (fast bolts) and homing missiles that lock on to the target nearest the nose; both destroy asteroids (big ones break up), drifting cargo containers and target drones that fly patrol circles and are replaced in waves. The station is built from Mega_City and Red_Echo modules (hub drums, landing decks, tower clusters, spokes, pylons, docking pads, hologram signs) with parked ships, a cargo ship, a gate course of six ring tunnels to fly through, a jump gate, relay satellites, a wreck field and five asteroid belts around it. The fighter bounces off what it hits (hull damage; destroyed at 0 and launched again) and is turned back at the edge of the area. HUD: nose crosshair and mouse aim point, target brackets with range, lead mark, scope, speed / throttle / hull / missiles, score |

Each level except `starship_level` has a `*_Cine` copy (`MoviePipelineGameMode` with an AI demo character) for its `LS_*_Showcase` sequence. `starship_level`'s reel is rendered on the level itself: a pilot script flies the fighter through the game's own keyboard and mouse inputs while the Movie Render Queue renders the player's view.

**Controls:**
- WASD and mouse: move and look (`random_isometric_village_level`: WASD or the arrow keys move in 8 screen directions and never turn the view; Q / E turn it left / right in 45° steps; the mouse wheel zooms, down to a close view of her)
- Space: jump
- Shift: run
- Ctrl: sprint (Meshy)
- F: open/close in `castle_level`; open/close chests, wardrobes and crates in `random_level` (doors open by themselves); open/close doors and containers in `random_dungeon_level` and `random_isometric_village_level`
- Left mouse button (X or RT on a controller): attack in `random_dungeoncombat_level`; 1 / 2 / 3 (D-pad left / up / right): sword / spear / axe
- M: full dungeon map in `random_dungeon_level` and `random_dungeoncombat_level`; village map in `random_isometric_village_level`
- Xbox controller (`random_isometric_village_level`): left stick or D-pad move (snapped to 8 directions; half deflection walks), A or X open/close, Y or View map, B closes the map, LB / RB turn the view, right stick up / down zooms, LT walk
- `starship_level`: W / S throttle, A / D roll, the mouse points the nose (it moves an aim point that the nose follows at up to 240° a second, against 95° on the stick; `[` / `]` change the mouse sensitivity), left button or Space cannons, right button or Ctrl missile, Shift afterburner, Tab next target, mouse wheel camera distance, I invert pitch, R restart, H help, Esc quit. Xbox controller: left stick throttle and roll, right stick points the nose, RT cannons, LT or RB missile, A or left stick click afterburner, Y next target, D-pad up / down camera distance, View restart, Menu help
- Extra move/action inputs on Meshy, FF and FF2: see their input scripts (`110`, `150`, `214`, `260`)

## Requirements

- **Unreal Engine 5.8**, expected at `E:\Program Files\Epic Games\UE_5.8`. Enabled plugins: PythonScriptPlugin (with `bRemoteExecution=True`), EditorScriptingUtilities, EditorToolset, ModelContextProtocol, MetaHuman, HairStrands, MovieRenderPipeline, HDRIBackdrop (the sci-fi city's sky).
- **C++ toolchain** for the `claude_ue5` module (`claude_ue5/Source`, the random_level town generator): Visual Studio 2022/2026 C++ build tools (MSVC 14.38+) and a Windows 10/11 SDK. Build with the editor closed: `pipeline\build_cpp.ps1`. UE 5.8's build rules also want a .NET Framework SDK (4.6+); without one the script points UnrealBuildTool at a stand-in for that build only (installing the .NET Framework 4.8.x Developer Pack removes the need). Plugin ProceduralMeshComponent is enabled in the `.uproject`.
- **Blender 5.1**, run headless: `blender -b -P script.py -- args`.
- **Python 3.11+** with `numpy`, `scipy`, `imageio-ffmpeg` and `Pillow`, for the numpy tools, the remote-exec client and video encoding.
- The local asset packs listed below.

## Layout

```
claude_ue5/              UE project (claude_ue5.uproject, Config/; Content/ is local only)
  Source/claude_ue5/RT/  C++ procedural town for random_level: ARTTownGenerator, ARTCell, ARTBuilding
  Source/claude_ue5/RD/  C++ procedural dungeon for random_dungeon_level and random_dungeoncombat_level: ARDDungeonGenerator, ARDSection, ARDMonster, ARDHUD, URDCombatComponent, URDBloodComponent
  Source/claude_ue5/IV/  C++ procedural village for random_isometric_village_level: AIVVillageGenerator, AIVSection, AIVVillager, AIVPlayerController, AIVHUD
  Source/claude_ue5/SS/  C++ space fighter for starship_level: ASSFighter, ASSMissile, ASSArena, ASSTarget, ASSPlayerController, ASSHUD, ASSGameMode, USSFXLibrary
  SourceArt/             exported/converted source art (only small JSON data is committed)
pipeline/
  unreal/                numbered editor scripts (NNN_name.py), run inside the editor
  blender_numpy/         Blender scripts (-b -P), numpy/scipy tools, ue_exec.py, encode_video.py, rl_reel_overlay.py, rd_reel_overlay.py, iv_reel_overlay.py, ss_reel_overlay.py, rdc_reel_overlay.py, rdc_sound_prep.py, rdc_sound_check.py
asset_survey/            survey of the local Fab library: UE5 usability, animation compatibility
local-packs.md           rig/animation summary of the local Fab packs
.mcp.json                MCP server config (UE ModelContextProtocol plugin on 127.0.0.1:8765)
```

## Running the pipeline

With the editor open on `claude_ue5.uproject`:

```powershell
python pipeline\blender_numpy\ue_exec.py pipeline\unreal\290_castle_level.py -2450 -1250 45   # script + args (sys.argv in the editor)
python pipeline\blender_numpy\ue_exec.py -c "import unreal; print(unreal.SystemLibrary.get_engine_version())"
python pipeline\blender_numpy\ue_exec.py --ping
```

The Blender stages write UE-ready FBX into `claude_ue5/SourceArt/...`:

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" -b -P pipeline\blender_numpy\ff2_build.py -- <args>
```

Scripts are numbered roughly in build order. Each one's docstring states its purpose and arguments.

| Range | Stage |
|---|---|
| `01`–`25` | fig4: scan import, MetaHuman conform/look/build, studio level, groom, outfit, render setup |
| `31`–`95` | fig4 locomotion: retargeting, heel stance, character BP, meadow world (`50`, `51_level_outdoor.py level_path [cine] pawn=… gm=…`), demo, cinematic, render (`75`) |
| `100`–`154` | Meshy biped: import, Substrate material, retarget, moves, sprint, demo, sequence |
| `160`–`189` | Dystopia soldier |
| `200`–`230` | FF (Tripo, static) |
| `240`–`289` | FF2 (Tripo, animated): import, AnimBP, character, grounding and foot-contact fixes |
| `290`–`383` | castle_level: village copy, interactive pieces, door/container/wardrobe BPs, splashes, populate, furniture kit, furnishing, grass mask, cinematic |
| `700`–`714` | sf-city-level: map copies, Monolith strip/stream, bridge road, world-aligned materials, sci-fi door BP, structures + interiors, player/fall guard, barrier walls, walk-test planner and PIE walk test, foot IK, cinematic (demo paths, Simulate recorder, sequence) |
| `750`–`761` | random_level: building templates (docks level instances, Sherwood cabins), ground material, level + generator setup, generation indicator, cinematic (demo path, Simulate recorder, one-camera sequence), PIE walk test |
| `770`–`775` | random_dungeon_level: level + piece catalogue + monsters + game mode/HUD + start section (`770`), PIE walk test (`771` driven by `772_rd_walk.ps1`), cinematic (demo run, Simulate recorder, one-camera sequence) |
| `790`–`799` | random_dungeoncombat_level: her weapons, grips and retargeted clips (`790`), the level copy and its combat set-up (`791`), PIE combat test (`792` driven by `793_rdc_combat.ps1`), demo reel: its sequence (`794`), the pilot that plays and records it (`795`), its Movie Render Queue job (`796`); sound: import and the generator's sound table (`797`); blood, wound and decal materials (`798`); the sound self test (`799_rdc_sound_test.ps1`) |
| `780`–`787` | random_isometric_village_level: piece catalogue + materials + level + game mode + start section (`780`), PIE walk test (`781` driven by `782_iv_walk.ps1`), cinematic (demo route, Simulate recorder, isometric one-camera sequence with the view turns), villager models (`786`, run by `780` and `783`), render recorder for the reel's maps (`787`) |
| `800`–`806` | starship_level: materials + effects + level + arena + fighter kitbash (`800`), station + clutter + targets (`801`), PIE flight test (`802` driven by `803_ss_flight.ps1`), demo reel: its sequence (`804`), the pilot that flies and records it (`805`), its Movie Render Queue job (`806`) |

**sf-city-level rebuild order** (needs the HDRIBackdrop plugin, enabled in the .uproject):
1. `700_sfc_maps.py city`, restart the editor, `700_sfc_maps.py monolith`, restart
2. `701_sfc_monolith_strip.py`, `702_sfc_assemble.py`, `703_sfc_road.py`
3. `704_sfc_materials.py`, `705_sfc_door_bp.py`, `706_sfc_structures.py`
4. `707_sfc_player.py`, `711_sfc_foot_ik.py`, `708_sfc_safety.py` (flood fill + barrier walls; re-run after any layout change)
5. Walk test: `709_sfc_walk_plan.py`, then during PIE `710_sfc_walk_test.py route|probes <from> <to> <tag>` (results in `SourceArt/sf_city/walk_<tag>.json`)
6. Showcase: `700_sfc_maps.py cine`, restart, open `sf-city-level_Cine`; `712_sfc_cine_setup.py`; `713_sfc_cine_record.py` (Simulate; stop it after "SFCPATH saved"); `714_sfc_sequence.py`; render `LS_SFC_Showcase` with `75` (no warm-up frames to drop: encode from 0)

**random_level** (`750`–`761`, C++ in `claude_ue5/Source/claude_ue5/RT`; packs: Modular Medieval Town "Sherwood" `Hive_Sherwood`, Modular Medieval Town Docks `Hivemind/Medieval_Docks`, Village Collection, the castle furniture kit):
1. Build the C++ module (`pipeline\build_cpp.ps1`, editor closed), relaunch.
2. `750_rl_templates.py` (opens a scratch level first: random_level holds these maps as level instances) (docks buildings: footprint, entry floor, doors + closed orientation, crate lids, added bedroom chests / wardrobes / washstands, interior walk paths; run it twice right after an editor restart: collision cooks asynchronously), `750b_rl_cabin_templates.py` (Sherwood houses) -> `SourceArt/random_level/templates.json`.
3. `751_rl_ground_material.py`, then `752_rl_level.py` (level, lighting, far ground, generator config, start square, PlayerStart, game mode; saved), then `753_rl_reveal.py` (generation indicator: post-process scan wave + border curtain materials, assigned to the generator).
4. Walk test: `761_rl_walk.ps1 "<plan>" <tag>` (PIE + `760_rl_walk_test.py`), e.g. `"expand:+x:400,visit:new:6,expand:-y:400,visit:new:4,visit:start:8,home"`; results in `SourceArt/random_level/walk_<tag>.json`.
5. Showcase: Save As `random_level_Cine` (`EditorLoadingAndSavingUtils.save_map`), restart, open it; `754_rl_cine_setup.py` (demo character + path, generator follows her with a fixed seed); `755_rl_cine_record.py` (Simulate; stop it after "RLPATH saved"); `756_rl_sequence.py` (one continuous camera: MRQ warms up at every camera cut, which would stall her); render `LS_RL_Showcase` with `75`; HUD with `pipeline/blender_numpy/rl_reel_overlay.py <frames> <out_dir> claude_ue5/Saved/Logs/claude_ue5.log` (reads the render's generation events from the log, so run it before the next PIE session), then encode from 0.

**random_dungeon_level** (`770`–`775`, C++ in `claude_ue5/Source/claude_ue5/RD`; packs: Dungeon Builder top-down kit `MysticDungeon`, Modular Dungeon kits `HallowedDepths` / `DarkHalls`, `Gothic_Props`, `Medieval_Weapons`, `Creatures_Pack`, castle_level's furniture kit and openable barrels / crates; reveal materials from random_level's `753`):
1. Build the C++ module (`pipeline\build_cpp.ps1`, editor closed), relaunch.
2. `770_rd_level.py` (pieces normalised to the dungeon frame, monsters with measured walk speeds, `BP_RD_GameMode` + `RDHUD`, level, start section, PlayerStart in the great hall; saved). Re-run after changing the generator's layout or furnishing code.
3. Walk test: `772_rd_walk.ps1 "<plan>" <tag>` (PIE + `771_rd_walk_test.py`), e.g. `"rooms:3,expand:+x,rooms:2,map:a,expand:-y,home"`; results in `SourceArt/random_dungeon/walk_<tag>.json`. `Config/DefaultEditorSettings.ini` keeps the editor at full speed in the background (otherwise PIE runs at ~3 fps while a script drives it).
4. Showcase: Save As `random_dungeon_level_Cine`, restart, open it; `773_rd_cine_setup.py` (demo character running east along a lane through the chapel and prison into the next section; generator follows her with a fixed seed, opens doors in front of her, 12 m trigger); `774_rd_cine_record.py` (Simulate; stop it after "RDPATH saved"; also records the map data); `775_rd_sequence.py` (one camera, doorway / ceiling clearance checks); render `LS_RD_Showcase` with `75`; HUD with `pipeline/blender_numpy/rd_reel_overlay.py <frames> <out_dir> claude_ue5/Saved/Logs/claude_ue5.log` (run it before the next PIE session), then encode from 0.

**random_dungeoncombat_level** (`790`–`799`, C++ in `claude_ue5/Source/claude_ue5/RD`: `URDCombatComponent`, `URDBloodComponent`, the fighting, wounds and voice of `ARDMonster`, the sound part of `ARDDungeonGenerator`, the stylised maps and combat panel of `ARDHUD`; a local sound library for the sounds (`SourceArt/random_dungeon_combat/sounds.json` names the files; they are not in the repository); packs: random_dungeon_level's, plus the mask textures of `HallowedDepths/RealisticBlood` (blood decals and spray), plus `Medieval_Weapons` (sword, spear, axe, shield), `Weapon_Shield_Animations`, `Spear_And_Shield_Animations`, `Animations_Warrior` (her clips) and the attack / hit / death clips of `Creatures_Pack`):
1. Build the C++ module, relaunch; random_dungeon_level must exist (`770`).
2. `790_rdc_weapons.py` (an IK rig for each animation pack's mannequin, a retargeter onto her rig, the clips retargeted to `/Game/RandomDungeon/Combat/Anims` and root locked; the blow time of every attack clip, where her weapon hand moves fastest; the grips, computed from her reference pose since her skeleton has no fingers; writes `SourceArt/random_dungeon_combat/weapons.json`).
3. `791_rdc_level.py`: the first run saves random_dungeon_level as `random_dungeoncombat_level` (Save As) and stops: restart the editor, run it again. The second run opens the copy and sets up its generator: `bCombat`, the weapons, the monsters' attack / flinch / death clips with their blow times and factors, 30% coverage, the two tiers, `bStylizedMap`, the PlayerStart in the middle of the start section; it prints every kind's hit points and damage in both tiers. Re-run it after `790` or after changing the numbers.
4. Combat test: `793_rdc_combat.ps1 "<plan>" <tag>` (PIE + `792_rdc_combat_test.py`), e.g. `"setup,weapons,monsters,kill:3,hurt,tier,death,regen,map"`: where she starts, each weapon in her hand and its attack, the coverage and the start tier against her, kills blow by blow, a monster hurting her, the tier of a generated section, death and return, regeneration, the map data; `blood` (a burst on a blow, drops in the air, marks where they land, a burst from her when she is hit), `wounds` (a wound a blow on that monster's skin in an overlay material of its own, nothing on any other monster, a pool when it dies) and `sounds` (her steps and breath, a door, the fire voices by a torch, the falloff of the placed sets, a monster's roar / cry / death, the rumble of a generated section: counted by occasion); results in `SourceArt/random_dungeon_combat/test_<tag>.json`.
5. Blood and wounds: `798_rdc_gore.py` (materials in `/Game/RandomDungeon/Combat/Materials`: the drops, the spray sprites, the decals with one instance per mask of the RealisticBlood pack, and `M_RDC_Wounds`, the overlay material whose `Wound0`..`Wound9` parameters are spheres in the mesh's reference pose; sets the generator's gore properties). The pack's own decal material is not used: it does not compile with Substrate.
6. Sound: edit `SourceArt/random_dungeon_combat/sounds.json` (the library's root, which files are played for which occasion, each set's level, volume, pitch and falloff, the master volume); `pipeline/blender_numpy/rdc_sound_prep.py` (a Python with numpy and imageio-ffmpeg) converts them into `SourceArt/random_dungeon_combat/audio` (mono 44.1 kHz, silence trimmed, levelled); `797_rdc_sounds.py` imports them into `/Game/RandomDungeon/Audio` and fills the generator's `Sounds` and the monsters' `SoundSet` / `StepLength` (`797_rdc_sounds.py noimport` after changing only numbers). `799_rdc_sound_test.ps1 [out_dir] [python]` starts the level as a game of its own with `-RDSoundTest`: the generator records the audio device's output while it plays one flat sound and the same placed sound 2 m ahead, 4 m right, 4 m left, 12 m and 25 m ahead, and `rdc_sound_check.py` reads the recording (is the placed sound there, louder on its side, quieter with distance?).
7. Showcase (on the level itself, no Cine copy; with sound: start the editor with `-deterministicaudio`, or the job's `.wav` is missing): `794_rdc_reel_sequence.py` (`LS_RDC_Showcase`: 45 s, no tracks); `795_rdc_reel_pilot.py` right before `796_rdc_reel_render.py <out_dir> preview|final` (the pilot waits for the render's world, restarts the dungeon with a fixed session seed on the first frame, plays her with movement input and the combat component's functions, turns her camera and records the play; wait for "RDCREEL saved"; `795_rdc_reel_pilot.py rehearse` plays the same in a running PIE session). The record also holds every sound the game played and every blood burst. HUD (minimap, status panel, monster bars, damage numbers, captions, what is heard written out) with `pipeline/blender_numpy/rdc_reel_overlay.py <frames> <out_dir>`, then `encode_video.py <out_dir> out.mp4 0 30 <frames>\rdc.MasterSubmixDefault.wav [video_kbps]` (the queue's `.wav` is the game's own mix; in a render the placed sounds are centred: the engine's non-realtime audio device loses spatialised sources, so the generator plays them without direction there).

**random_isometric_village_level** (`780`–`787`, C++ in `claude_ue5/Source/claude_ue5/IV`; packs: House Forge modular house kit `HouseForge_01` and its Viking village props, the castle furniture kit and castle_level's openable barrels / crates, Medieval Docks, Village / Castle / War Camp collections, Modular Church props, Sherwood and Old Windmill foliage; villagers from NPC_Characters_Pack, NPC_Kids_Pack, NPC_Beggars_Pack and NPC_King_And_Queen; reveal materials from random_level's `753`; `r.CustomDepth=3` in `DefaultEngine.ini` for the silhouette):
1. Build the C++ module (`pipeline\build_cpp.ps1`, editor closed), relaunch.
2. `780_iv_level.py` (pieces normalised to the village frame, `M_IV_Ground` / `M_IV_Silhouette`, `BP_IV_GameMode` with `IVPlayerController` + `IVHUD`, level, start section, PlayerStart in the middle of the square; saved; prints the number of doors / containers that cannot be reached: must be 0; runs `786_iv_villagers.py`, which fills the generator's villager models and coverage: run `786` on its own after changing only that list). Re-run after changing the plan or the furnishing code. The first run builds the kit's Nanite meshes (slow, once).
3. Walk test: `782_iv_walk.ps1 "<plan>" <tag>` (PIE + `781_iv_walk_test.py`), e.g. `"input,rotate,villagers:25,houses:3:turn,map:a,expand:+x,villagers:15,houses:2,expand:-y,home"`: the 8 directions (keys and scripted stick), turning the view, the villagers of every section (count, walking, never on a blocked cell), doors and containers with F, the cutaway (with `:turn` from all 8 view directions), generation across each edge; results in `SourceArt/random_isometric_village/walk_<tag>.json`.
4. Showcase: Save As `random_isometric_village_level_Cine`, restart, open it; `783_iv_cine_setup.py` (rebuilds the start section for its nav grid; demo character starting in a house on a main road, route out along the road across the border, a stop in the new part for the big map; generator follows her with a fixed seed and opens doors for her); `784_iv_cine_record.py` (Simulate; stop it after "IVPATH saved"); `785_iv_sequence.py` (orthographic camera at the game's pitch: its position, its width and the view turns of Q / E are keyed, and the generator's `ViewYawOffset` with them, so the cutaway follows); `787_iv_render_record.py` right before rendering `LS_IV_Showcase` with `75` (it records the render itself: her path, the villagers, the generation, the map data; wait for "IVREND saved"); HUD (minimap, big map, key caps, captions) with `pipeline/blender_numpy/iv_reel_overlay.py <frames> <out_dir>`, then encode from 0.

**starship_level** (`800`–`806`, C++ in `claude_ue5/Source/claude_ue5/SS`; packs: Red_Echo (fighter hull, pylons, docking pads, portal, antennas, rocks), Spaceship_Kit (stars, sun, planets, cannon barrels, reactor, engine flame, ships, rocks), Sci-Fi Flying Cargo Ship (wings, containers, cargo ship, wreck modules), Mega_City (station hub, decks, towers, spokes, holograms, ring gates, drones), SciFi_Cliff (rocks), Military_Drone (missile mesh), Medieval_Weapons `P_ArrowTrail` (the ribbon the contrails are made from), StarterContent `P_Explosion`):
1. Build the C++ module (`pipeline\build_cpp.ps1`, editor closed), relaunch.
2. `800_ss_level.py` (materials, contrail effects tuned by `USSFXLibrary`, level with stars / sun / planets / lights / fixed exposure, `SS_Arena`, `SS_Fighter` with its parts, muzzles, missile rails and thrusters; saved). `800_ss_level.py fighter` only rebuilds the fighter and the effects in the open level (the fighter stays where it is).
3. `801_ss_station.py` (station, parked ships, cargo ship, the gate course, jump gate, satellites, wrecks, big asteroids; the gates use `/Game/Starship/Meshes/SM_SS_Gate`, a copy of the pack's tunnel without the black disc that closes one of its ends, which `801` makes; `801` also moves the fighter from `800`'s start corner onto the first gate's axis, 228 m before it and facing it, so that flying straight on goes through the first two gates and clear of the rest; the arena's asteroid / container fields, keep-out spheres, drone types and patrol volumes; saved). Re-run it after `800` without `fighter` (which clears the level).
4. Flight test: `803_ss_flight.ps1 "<plan>" <tag>` (PIE + `802_ss_flight_test.py`), e.g. `"input,agile,camera,cannon:3,missile:2,edge,collide,tour:20"`: every control on keyboard, mouse and controller through the controller's scripted inputs, the mouse's turn rates against the stick's (`agile`), the chase camera, cannon and missile kills, the turn-back at the edge, a collision, a lap round the station; results in `SourceArt/starship/flight_<tag>.json`.
5. Showcase (on `starship_level` itself, no Cine copy): `804_ss_reel_sequence.py` (`LS_SS_Showcase`: 30 s, no tracks); `805_ss_reel_pilot.py` right before `806_ss_reel_render.py <out_dir> preview|final` (the pilot waits for the render's world, flies the fighter with scripted keys and mouse, moves the camera and records the flight; wait for "SSREEL saved"; `805_ss_reel_pilot.py rehearse` flies the same plan in a running PIE session). The preview (640 x 360) and the final render are the same flight: the pilot has the arena spawn its targets again on the first frame and the render steps the game at a fixed rate. HUD (crosshair, aim point, target brackets, speed, score, the keys and mouse of the pilot, captions) with `pipeline/blender_numpy/ss_reel_overlay.py <frames> <out_dir>`, then encode from 0.
6. Standalone game: `pipeline\package_starship.ps1 [-Test]` (editor closed; about 15 minutes) builds the Shipping game target, cooks `starship_level` and what it refers to, and archives a self-contained directory to `builds\starship_level\Windows` (about 2.3 GB, ignored by git: it holds cooked pack content). `claude_ue5.exe` in it starts the level; the Visual C++ and Universal C runtime DLLs lie next to the executable, so nothing has to be installed (it needs 64-bit Windows 10 or 11 and a DirectX 12 graphics card). The script swaps the project's default map and game mode for the cook and puts `DefaultEngine.ini` back. `-Test` runs the packaged game's self test: `claude_ue5.exe -RenderOffScreen -SSSelfTest=12 -SSSelfTestOut=<dir>` flies for 12 s without a window, writes `selftest.txt` and `selftest.png` and quits.

**castle_level rebuild order:**
1. `290_castle_level.py -2450 -1250 45`
2. `340_castle_populate.py`
3. `383_grass_mask.py`
4. `380_castle_furnish.py`

**Showcase videos:**
- Build the sequence with the level's `*_sequence.py`.
- Render with `75_render_locomotion.py <out_dir> preview|final <level> <sequence> <prefix>`.
- Encode with `pipeline/blender_numpy/encode_video.py <frames_dir> <out.mp4> 36 30`. The `36` drops the warm-up frames.

## What's not in the repo

These are excluded for size (about 10 GB, with single files over 1 GB) and licensing:

- **Unreal content** (`claude_ue5/Content/`), including third-party packs:
  - [Medieval Fantasy Village](https://www.fab.com/) (LAYA DESIGN) and Fantasy Castle Environment (DanStudios), both from Fab
  - Monolith megastructure
  - Megascans scans (Saloon Interior pack)
  - MetaHuman assets and the UE template mannequins
- **Source characters:**
  - the Tripo anime female GLBs
  - the Meshy AI biped zip
  - the Dystopia Soldiers pack (Fab, Unity format)
  - the fig4 scan
- **Source art binaries:** FBX, GLB, Alembic, DNA and textures.
- **Renders and showcase videos** (`renders/`).
- **Per-machine folders:** `Saved/`, `Intermediate/`, `DerivedDataCache/`.

To rebuild a level you need the same packs locally:
1. Add the Fab packs to the project through the Epic Games Launcher.
2. Put the character sources where the build scripts expect them.
3. Run the scripts in order.
