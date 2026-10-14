# claude-ue5

An Unreal Engine 5.8 project built almost entirely from scripts. The scripts drive the running editor over Python remote execution, Blender + numpy prepare the source art, and a C++ module holds the games that generate themselves in play. The project has fourteen levels: a photo studio and five character showcases, three hand-built worlds with walk-in buildings, three procedural worlds (a town, a dungeon, an isometric village), the dungeon again with melee combat, blood, sound and music, and a space fighter. Most have a recorded demo route or a scripted test, and a Movie Render Queue showcase video.

This repository is **source only**: the pipeline scripts, the C++ source, project config and small data files. Unreal assets (`Content/`), source art binaries, sounds, renders and the third-party packs they come from stay local. See [What's not in the repo](#whats-not-in-the-repo).

## Capabilities

What the project does today. Everything here is built by the scripts in this repository and can be rebuilt from the local packs; the [Levels](#levels) table has the detail.

**Characters and animation**
- A MetaHuman conformed to a 3D scan (`fig4`): face and body fitted to the scan, a strand hair groom, the scanned outfit refitted to her, studio lighting.
- Characters from six kinds of source on the same third-person controls: the MetaHuman, a Meshy AI biped with 18 moves of its own, a Unity-format Fab soldier, a static Tripo GLB rigged in Blender, animated Tripo GLBs playing their own clips, and Meshy JRPG characters (one of them an unrigged mesh whose skeleton is worked out from its shape).
- IK rigs and retargeters built from Python: UE5 mannequin and soldier animation onto the other characters, three Fab weapon animation packs onto the player of the dungeon.
- Feet that stay put: walk and run speeds measured from the stance foot, clips grounded on the sole contacts, root locking, foot IK on uneven ground.

**Worlds**
- Hand-built from pack maps: a meadow (procedural Nanite terrain, rocks, grass), a photo studio, a medieval village and a castle with a lake village whose houses were opened up and furnished by purpose, a sci-fi city joined to a megastructure with furnished rooms behind automatic doors.
- Procedural, in C++ (`ARTTownGenerator`, `ARDDungeonGenerator`, `AIVVillageGenerator`): a start area built from a fixed seed and saved; walking toward its edge generates the next area ahead of her, spread over several frames, with a reveal effect (a scan wave and a glowing border). Rooms and houses have a purpose and are furnished and lit for it; every door and container can be reached and opened.
- Things to do in them: doors, chests, wardrobes, barrels and crates that open; a minimap and a full map of what has been generated and discovered; monsters that wander the dungeon; villagers who walk the village streets and give way.
- Views: third person; a fixed isometric camera that turns in 45° steps and zooms, with roofs and camera-side walls cut away indoors and her silhouette shown through what hides her; a chase camera behind a fighter.

**Combat** (`random_dungeoncombat_level`)
- Three melee weapons with their own attack, flinch and death clips; monsters that notice her, give chase, attack, flinch and die; hit points and damage set by tier so the first area is easier than what is generated in play; regeneration, death and return.
- Blood: bursts of drops and spray from where a blow lands, marks where the drops fall, a pool under a body.
- Wounds: each blow leaves a wound on that one monster, on its skin where the weapon met it.
- Sound placed in the world and fading with distance: her footsteps and voice, each monster kind's steps, growl, roar, cry and death, fires, doors, chests, the rumble of a new section.
- Music: a wandering track over a room tone; a battle track over a tenser atmosphere when a monster comes at her, another one each fight; the wandering track resumes where it left off.

**Space flight** (`starship_level`)
- A fighter kitbashed from pack meshes in a 5 km combat area round a station: cannons, homing missiles with lock-on, destructible asteroids, containers and drones, collisions with hull damage, a gate course, engine flames and contrails, a full HUD.
- A standalone Windows package of it that needs nothing installed.

**Input:** keyboard and mouse everywhere; an Xbox controller in the village, the fighter and for attacks in the dungeon.

**Tests**
- A scripted play-in-editor test for the sci-fi city, the three procedural worlds, the dungeon fight and the fighter, driven from PowerShell by a plan string and written out as JSON: walk tests (routes, doors, containers and where their lids and doors are, generation across each edge, falls, clipping, stuck legs), the combat test (15 steps, from each weapon's blow to the music changing and the flames burning), the flight test (every control, kills, collisions, a lap through the gates).
- A sound self test that records what the audio device puts out while sounds play at known places, and measures it: is the sound there, on the correct side, quieter with distance.
- A packaged game's own self test, run without a window: a report and a picture.

**Demo reels**
- 1080p Movie Render Queue renders. Recorded routes on `*_Cine` copies run on the sequence clock, so a preview and the final render match; for the dungeon fight and the fighter a pilot script plays the game itself through its inputs while the queue renders the player's view, and two renders log the same events.
- The HUD, maps, captions and key presses are drawn over the frames from the recording of the render itself; the sound track is the game's own mix.
- Each reel is encoded twice: full size, and a two-pass copy of 20 MB or less.

**Tooling**
- `ue_exec.py` runs a script or a snippet in the running editor; an MCP server exposes the editor's own toolsets.
- `build_cpp.ps1` builds the C++ module without a .NET Framework SDK installed; `package_starship.ps1` packages a level as a game.
- Shared builders: `interior_lib.py` (rooms, furniture, openables, lights for any building), `mat_lib.py` (textures and Substrate materials from Python), `capture.py` (a picture of the editor world from any camera).
- A survey of the local Fab library: what is usable in UE5 and which animations drive which models (`asset_survey/`, `local-packs.md`).
- A hero gallery, [docs/heroes.md](docs/heroes.md): the library's 100 possible heroes and player characters in ten categories, each with a suggested role and three pictures (full body, upper body and head, an action pose copied from another pack's attack clip onto its own skeleton, with a sword, axe, spear, rifle or bare fists).
- A monster gallery, [docs/monsters.md](docs/monsters.md): the library's 107 monsters ranked by looks from easiest to toughest, each pictured in its own colours and in three recoloured versions (infernal, venom, frost) made by one material that recolours the model's own texture and adds a pattern that follows the body. Packs that exist only in Unity format are unpacked and imported for it.

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
| `L_Meshy_Meadow` | Meshy AI biped (`BP_MeshyCharacter`); the JRPG characters (`BP_JRPGFem1Character` … `BP_JRPGFem5Character`) | Same meadow; 18 moves on input actions plus a sprint. Also the stage of the JRPG characters, whose scripts set the meadow's game mode to the one built last: Fem1 (a Meshy rig playing the soldier's retargeted set, or the FF showcase set), Fem3 and Fem4 (Meshy meshes; one that comes unrigged, such as Fem3, is given a skeleton by `jrpg_autorig.py`), Fem5 (`jrpg-fem5-tripo`, an animated Tripo GLB playing her own idle / walk / run: the player of every later level) |
| `soldier_level` | Dystopia Soldier 02 (`BP_SoldierCharacter`) | Same meadow; Unity-sourced soldier with retargeted locomotion |
| `ff_level` | Tripo anime female (`BP_FFCharacter`) | Same meadow; static GLB rigged onto a UE4-mannequin skeleton |
| `ff2_level` | Animated Tripo anime female (`BP_FF2Character`) | Same meadow; clips fixed on the sole contacts so she doesn't float or slide |
| `castle_level` | FF2 | The Medieval Fantasy Village pack's map with walk-in houses: doors, chests, trunks, wardrobes and barrels open with **F**. Interiors are furnished by building purpose (tavern, manor, homes, bakery, stable, barn, storehouse, smithy) with lofts, attics and lighting. Water splashes in the river |
| `fantasy_castle_level` | FF2 (`BP_FF2Character`, with a higher step and a steeper walkable slope for the pack's rock) | The Fantasy Castle Environment's map with the Medieval Lake Village streamed into its lake. The pack meshes collide with their real triangles instead of one convex hull each, so doorways, arches and the bridge can be walked. A stone stair links the castle's east terrace to the island bridge, and a road runs from the bridge down the island, over a wooden causeway and into the walled village. Three castle buildings had a doorway cut into their shell and got interiors (great hall, armory, barracks); the village's hollow houses were measured by flood fill and furnished by purpose (tavern, fisherman's house, farmhouse, weaver's cottage, smithy, barn, storehouse). Doors and chests open with **F**. No showcase video |
| `sf-city-level` | jrpg-fem5-tripo (`BP_SFC_Fem5Character`: her own idle/walk/run, foot IK) | The Open World Science fiction City with the Monolith Megastructure streamed in beside it, joined by a 200 m bridge road. Four structures with furnished rooms behind automatic sci-fi blast doors: Port Authority (office + armory), neon noodle bar, hab apartment (living room + bedroom), excavation lab (relic lab + server room). Invisible barrier walls along every drop into the void, a fall guard, and a scripted walk test (`709`/`710`) |
| `random_level` | jrpg-fem5-tripo (`BP_SFC_Fem5Character`) | Procedural medieval town (C++ `ARTTownGenerator`). Starts as a 500 m x 500 m square built with a fixed seed; whenever she nears the edge of town heading outward, the next 250 m of terrain, cobbled streets, furnished buildings, props and foliage is generated ahead of her (fresh seed each play, never saved). Each new cell is marked as it appears: a glowing curtain rises on its border and a scan wave sweeps across it, the cell drawn as a cyan ghost until the wave passes. Buildings: the Modular Medieval Town packs' furnished docks houses, tavern (fireplace, dining tables, chairs, bar), stores and Sherwood cabins, streamed in as level instances and turned to face the street. Doors swing open as she approaches; bedroom chests, wardrobes and crates open with **F** |
| `random_dungeon_level` | jrpg-fem5-tripo (`BP_SFC_Fem5Character`) | Procedural dungeon (C++ `ARDDungeonGenerator`). A 252 m x 252 m start section of 49 interconnected rooms (fixed seed, saved), with hallways leaving every edge; walking toward the edge generates the next section (fresh seed each play, never saved) with random_level's reveal effect. Rooms have a purpose with matching furniture and lighting: great hall, barracks, prison cells, torture chamber, storeroom, armory, kitchen, library, chapel, crypt, treasury, guard room, forge; hallways are guard passages, supply passages or catacomb tunnels. Doors (crypt double doors, cell doors) and every container (chests, trunks, wardrobes, barrels, crates) open with **F**. Minimap of generated / discovered rooms, full map on **M**. Monsters from Creatures_Pack (troll, daemon, horned demon, ripper dog, spider, mutant) in 40% of the rooms wander from room to room |
| `random_dungeoncombat_level` | jrpg-fem5-tripo (`BP_SFC_Fem5Character`) with three melee weapons | `random_dungeon_level` with fighting (the generator's `bCombat`). She has 100 hit points and a sword (22 damage a blow), a spear (17, long reach) and an axe (36, slower, wide arc) from the Medieval_Weapons pack, the first two with a shield; she wields each with attack, flinch and death clips of a Fab animation pack made for it, retargeted to her. Monsters in 30% of the rooms notice her, give chase over the tile grid, attack with their own attack clips, flinch when hit and die. In the start section (the first 252 m square) the average monster has 50 hit points and does 11 a blow; in every section generated in play it is on a par with her (100 hit points, 25 a blow: her average). Out of a fight her hit points come back; at 0 she falls and stands up again in the middle of the start section. HUD: a status panel in the bottom right corner (hit points, the three weapons with their damage, kills), a bar over each monster in the fight, damage numbers; the minimap (top right) and the **M** map are a miniature of the dungeon (stone floors coloured by room, walls, doors, chests, torches), with every room named on the M map. She starts in the middle of the start section; generated sections are never saved. **Blood:** a blow throws a burst of drops and spray from where it landed (from her too when she is hit); the drops fall, and leave marks on the floor, walls and furniture; a pool spreads under a body. **Wounds:** every blow leaves a wound on that monster alone, on its skin where the weapon met it (stain, torn flesh, a dark open middle, blood running down), and the worse off it is the more of it is bloodied. **Sound** (from a local sound library): her footsteps (walking and running: nothing else of her moving) and her voice when she is hurt or falls, the swing and the weapon landing; each monster kind's footsteps, growl, roar when it notices her, cry when hurt and death; torches, braziers and hearths as she comes near, doors and chests opening and closing, the rumble of a section being generated. Everything that is not her own is heard from where it is and fades with its distance to her. **Music:** while she wanders, an atmospheric track over a quiet room tone; when a monster comes at her the music turns to a battle track (another one each fight) over a tenser atmosphere, and a few seconds after the fight the wandering track comes back where it left off |
| `random_isometric_village_level` | jrpg-fem5-tripo (`BP_SFC_Fem5Character`) | Procedural nucleated village seen from a fixed isometric camera (C++ `AIVVillageGenerator`). One village around one hub: a cobbled market square (fountain, well, stalls) with the church, tavern, smithy, bakery, store and elder's hall facing it, ring streets closing around it and short lanes staggered between the rings, three main roads winding out. Houses stand along the streets with gardens, orchards and fields behind, thinning into farmsteads away from the square. The 250 m x 250 m start section is built with a fixed seed and saved; walking toward the edge generates the next 250 m section (fresh seed each play, never saved) on the same rings and lanes, with random_level's reveal effect. Houses are assembled from the House Forge kit (thatch / timber / stone) and furnished by purpose (cottage, farmhouse, tavern, smithy, bakery, store, carpenter, barn, storehouse, church, elder's hall); indoors the roof and the camera-side walls are cut away, and her silhouette shows through anything that hides her. Doors and every container open with **F**. Unarmed villagers (townsfolk, peasants, youths, a servant pair, the elder, a physician, a lady: three for every ten buildings of each 250 m section, in play only) wander the streets and the square, give way to her and step aside. **Q** / **E** turn the view in 45° steps (the cutaway and the maps turn with it) and the view zooms in to a close view of her. A stylised miniature of the village is the minimap; **M** opens the big map with every building labelled |
| `starship_level` | A space fighter (C++ `ASSFighter`) | Outer space: a 5 km x 5 km x 5 km combat area round a space station, seen from a chase camera behind the fighter. The fighter is a kitbash of pack meshes in the style of a Colonial Viper (a white-and-red delta hull with two engines, stub wings, a third engine with a tail fin, wing-tip cannons, four missiles under the wings; engine flames that follow the throttle and a ribbon contrail from each engine). Two weapons: cannons (fast bolts) and homing missiles that lock on to the target nearest the nose; both destroy asteroids (big ones break up), drifting cargo containers and target drones that fly patrol circles and are replaced in waves. The station is built from Mega_City and Red_Echo modules (hub drums, landing decks, tower clusters, spokes, pylons, docking pads, hologram signs) with parked ships, a cargo ship, a gate course of six ring tunnels to fly through, a jump gate, relay satellites, a wreck field and five asteroid belts around it. The fighter bounces off what it hits (hull damage; destroyed at 0 and launched again) and is turned back at the edge of the area. HUD: nose crosshair and mouse aim point, target brackets with range, lead mark, scope, speed / throttle / hull / missiles, score |

Most levels have a `*_Cine` copy (`MoviePipelineGameMode` with an AI demo character) for their `LS_*_Showcase` sequence; the JRPG characters use the meadow's. `starship_level` and `random_dungeoncombat_level` have none: their reels are rendered on the level itself, a pilot script playing the game through its own inputs while the Movie Render Queue renders the player's view. `L_Fig4_Studio` (stills) and `fantasy_castle_level` have no reel.

**Controls:**
- WASD and mouse: move and look (`random_isometric_village_level`: WASD or the arrow keys move in 8 screen directions and never turn the view; Q / E turn it left / right in 45° steps; the mouse wheel zooms, down to a close view of her)
- Space: jump
- Shift: run
- Ctrl: sprint (Meshy)
- F: open/close in `castle_level` and `fantasy_castle_level`; open/close chests, wardrobes and crates in `random_level` (doors open by themselves); open/close doors and containers in `random_dungeon_level` and `random_isometric_village_level`
- Left mouse button (X or RT on a controller): attack in `random_dungeoncombat_level`; 1 / 2 / 3 (D-pad left / up / right): sword / spear / axe
- M: full dungeon map in `random_dungeon_level` and `random_dungeoncombat_level`; village map in `random_isometric_village_level`
- Xbox controller (`random_isometric_village_level`): left stick or D-pad move (snapped to 8 directions; half deflection walks), A or X open/close, Y or View map, B closes the map, LB / RB turn the view, right stick up / down zooms, LT walk
- `starship_level`: W / S throttle, A / D roll, the mouse points the nose (it moves an aim point that the nose follows at up to 240° a second, against 95° on the stick; `[` / `]` change the mouse sensitivity), left button or Space cannons, right button or Ctrl missile, Shift afterburner, Tab next target, mouse wheel camera distance, I invert pitch, R restart, H help, Esc quit. Xbox controller: left stick throttle and roll, right stick points the nose, RT cannons, LT or RB missile, A or left stick click afterburner, Y next target, D-pad up / down camera distance, View restart, Menu help
- Extra move/action inputs on Meshy, FF and FF2: see their input scripts (`110`, `150`, `214`, `260`)

## Requirements

- **Unreal Engine 5.8**, expected at `E:\Program Files\Epic Games\UE_5.8`. Enabled plugins: PythonScriptPlugin (with `bRemoteExecution=True`), EditorScriptingUtilities, EditorToolset, ConfigSettingsToolset, ModelContextProtocol, ModelingToolsEditorMode, MetaHuman (with MetaHumanCharacter and MetaHumanGenerator), HairStrands, AlembicHairImporter, MovieRenderPipeline, CascadeToNiagaraConverter (the dungeon pack's torch flame was converted with it and needs its scripts: without the plugin the flame does not compile and torches, braziers and hearths give light without fire), HDRIBackdrop (the sci-fi city's sky), ProceduralMeshComponent. The project renders with Substrate (`r.Substrate=True`): pack materials written for the old shading models may not compile.
- **C++ toolchain** for the `claude_ue5` module (`claude_ue5/Source`: the town, dungeon and village generators, the combat, blood and sound of the dungeon, the space fighter): Visual Studio 2022/2026 C++ build tools (MSVC 14.38+) and a Windows 10/11 SDK. Build with the editor closed: `pipeline\build_cpp.ps1`. UE 5.8's build rules also want a .NET Framework SDK (4.6+); without one the script points UnrealBuildTool at a stand-in for that build only (installing the .NET Framework 4.8.x Developer Pack removes the need). The module depends on ProceduralMeshComponent, Niagara, EnhancedInput, RenderCore and AudioMixer.
- **Blender 5.1**, run headless: `blender -b -P script.py -- args`.
- **Python 3.11+** with `numpy`, `scipy`, `imageio-ffmpeg` and `Pillow`, for the numpy tools, the remote-exec client, the reel overlays, the sound conversion and check, and video encoding. The PowerShell test drivers call `python`, or the interpreter named by the `UE_PY` environment variable.
- The local asset packs listed below, and for `random_dungeoncombat_level`'s sound a local sound-effect and music library (`sounds.json` names its root and files).

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
  blender_numpy/         Blender scripts (-b -P), numpy/scipy tools, ue_exec.py, encode_video.py, rl_reel_overlay.py, rd_reel_overlay.py, iv_reel_overlay.py, ss_reel_overlay.py, rdc_reel_overlay.py, rdc_sound_prep.py, rdc_sound_check.py, unity_extract.py, monster_doc.py, hero_doc.py
  build_cpp.ps1          builds the C++ module (editor closed)
  package_starship.ps1   packages starship_level as a standalone Windows game
asset_survey/            survey of the local Fab library: UE5 usability, animation compatibility
docs/                    monsters.md, heroes.md (the galleries), assets.md (attribution); images/: the README's stills and the galleries' pictures
local-packs.md           rig/animation summary of the local Fab packs
.mcp.json                MCP server config (UE ModelContextProtocol plugin on 127.0.0.1:8765)
CLAUDE.md                working rules and pitfalls for Claude Code in this repository
renders/, builds/        showcase videos and packaged games (local only)
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
| `290`–`383` | castle_level: village copy, interactive pieces (`blender_numpy/mfv_interactive_build.py`; `mfv_lid_caps.py <dir>` then `320_castle_import.py _lid` gives the lids' cut underside its wood face), door/container/wardrobe BPs, splashes, populate, furniture kit, furnishing, grass mask, cinematic |
| `400`–`421` | fantasy_castle_level: map copies, Lake Village strip / stream, triangle collision, road and causeway, PlayerStart, terrace-to-bridge link, FF2's movement on rugged ground, castle survey / doorway cuts / interiors, world-aligned materials, door leaves, village survey / interiors |
| `500`–`540` | JRPG characters (Meshy): import, soldier retarget, character + game mode, the FF showcase animation set |
| `600`–`650` | Animated Tripo characters (`jrpg-fem5-tripo`), generalised from FF2: import, AnimBP on her own clips, grounding, character, demo routine, sequence |
| `700`–`714` | sf-city-level: map copies, Monolith strip/stream, bridge road, world-aligned materials, sci-fi door BP, structures + interiors, player/fall guard, barrier walls, walk-test planner and PIE walk test, foot IK, cinematic (demo paths, Simulate recorder, sequence) |
| `750`–`761` | random_level: building templates (docks level instances, Sherwood cabins), ground material, level + generator setup, generation indicator, cinematic (demo path, Simulate recorder, one-camera sequence), PIE walk test |
| `770`–`775` | random_dungeon_level: level + piece catalogue + monsters + game mode/HUD + start section (`770`), PIE walk test (`771` driven by `772_rd_walk.ps1`), cinematic (demo run, Simulate recorder, one-camera sequence) |
| `780`–`787` | random_isometric_village_level: piece catalogue + materials + level + game mode + start section (`780`), PIE walk test (`781` driven by `782_iv_walk.ps1`), cinematic (demo route, Simulate recorder, isometric one-camera sequence with the view turns), villager models (`786`, run by `780` and `783`), render recorder for the reel's maps (`787`) |
| `790`–`799` | random_dungeoncombat_level: her weapons, grips and retargeted clips (`790`), the level copy and its combat set-up (`791`), PIE combat test (`792` driven by `793_rdc_combat.ps1`), demo reel: its sequence (`794`), the pilot that plays and records it (`795`), its Movie Render Queue job (`796`); sound: import and the generator's sound table (`797`); blood, wound and decal materials (`798`); the sound self test (`799_rdc_sound_test.ps1`). `790_rdc_weapons.py grips` computes only the grips again (then `791`). The range is full: further stages for this level start at `810` |
| `800`–`806` | starship_level: materials + effects + level + arena + fighter kitbash (`800`), station + clutter + targets (`801`), PIE flight test (`802` driven by `803_ss_flight.ps1`), demo reel: its sequence (`804`), the pilot that flies and records it (`805`), its Movie Render Queue job (`806`) |
| `900` | Monster gallery for `docs/monsters.md`: `unity` (imports the Unity-only monster packs after `blender_numpy/unity_extract.py` has unpacked them into `SourceArt/fab_unity`), `materials` (`M_MON_Variant`), `stage`, `warm`, `shoot <dir>`, `clear`, all in the scratch level `rl_scratch`; then `blender_numpy/monster_doc.py <dir>` writes the strips and the page from `SourceArt/monster_gallery/monsters.json` |
| `901` | Hero gallery for `docs/heroes.md`: `stage <start> <count>` or `stage ids <id,...>` (pose animations on each hero's skeleton, weapons in hand), `shoot <dir>` during play-in-editor (the editor world does not evaluate animations), `clear`; then `blender_numpy/hero_doc.py <dir>` writes the pictures and the page from `SourceArt/hero_gallery/heroes.json` |
| no number | Shared modules and probes: `interior_lib.py` (rooms, furniture, openables and lights for any building), `container_check.py` (measures in play where every container's lid or doors are against its body, for the tests), `mat_lib.py` (textures and Substrate materials), `capture.py` (a `SceneCapture2D` picture of the editor world), `state.py`, `save_all.py`, and the fig4 probes (`probe_*`, `inspect_*`, `body_*`) |

**JRPG and Tripo characters** (`500`–`540`, `600`–`650`; they play in `L_Meshy_Meadow`):
- A rigged Meshy character (Fem1): `blender_numpy/jrpg_build.py model.glb out_dir name` (a real `root` bone, centimetre rig, textures), `500_jrpg_import.py Fem1`, `510_jrpg_retarget.py` (the soldier's whole set retargeted onto her, speeds measured from her stance foot), `520_jrpg_character.py soldier|ff Fem1` (`540_jrpg_ff_anims.py` first for the `ff` set).
- An unrigged Meshy mesh (Fem3): `blender_numpy/jrpg_autorig.py model.glb out_dir name [height_cm]` finds the joints in the mesh (arm line, armpits, crotch, slice centroids) and skins it to a mannequin-named skeleton; then as above.
- An animated Tripo character (Fem5): `blender_numpy/tripo_build.py model.glb out_dir name tag [height_cm]` (the mesh and its clips as two FBX files), `600_tripo_import.py Fem5`, `610_tripo_anim.py Fem5` (the template's state machine with her own idle / walk / run), `615_tripo_ground.py Fem5` (Tripo pins the hips: each clip is lowered until the planted foot is on the ground), `620_tripo_character.py Fem5`; showcase with `640_tripo_demo.py Fem5` and `650_tripo_sequence.py Fem5`.

**fantasy_castle_level** (`400`–`421`; packs: Fantasy Castle Environment, Medieval Lake Village, castle_level's furniture kit and door / container Blueprints):
1. `400_fcl_maps.py castle`, restart the editor, `400_fcl_maps.py lake`, restart.
2. `401_fcl_lake_strip.py` (the village copy loses its own sky, lights, backdrop and water), `402_fcl_assemble.py` (streams it into the castle's lake; game mode FF2), `403_fcl_collision.py` (triangle collision on the terrain and architecture meshes), `407_ff2_rugged_movement.py`.
3. `404_fcl_road.py` (A* over traced heights from the bridge to the village, the pack's road spline, a two-span causeway), `406_fcl_castle_link.py` (ramp, slab and stair from the terrace to the bridge), `405_fcl_player.py`.
4. Castle interiors: `410_fcl_castle_survey.py`, then `blender_numpy/fcl_castle_rooms.py` and `fcl_castle_open.py` (room frames and the doorway cut into each shell), `411_fcl_castle_open.py`, `412_fcl_materials.py`, `blender_numpy/fcl_leaf_pivot.py` and `414_fcl_door_leaves.py` (door leaves hinged at the origin), `415_fcl_castle_interiors.py`.
5. Village interiors: `420_fcl_village_survey.py`, `421_fcl_village_interiors.py` (rooms by flood fill, the static doors replaced by ones that open, furniture by purpose through `interior_lib.py`).

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
2. `770_rd_level.py` (pieces normalised to the dungeon frame, monsters with measured walk speeds, `BP_RD_GameMode` + `RDHUD`, level, start section, PlayerStart in the great hall; saved). Re-run after changing the generator's layout or furnishing code. `770_rd_level.py pieces` only rewrites the piece table in the generator of whichever dungeon level is open, builds its start section again from it (same seed: the same rooms) and saves: run it on the Cine copy and on random_dungeoncombat_level, which each carry a piece table and a start section of their own and whose generators have settings `770` knows nothing of. The broken walls of the prison, torture chamber and crypt come in five pieces (`Wall_Rough`, `Wall_Rough_2` … `_5`): a section gives each wall segment one of them, never the one beside or under it.
3. Walk test: `772_rd_walk.ps1 "<plan>" <tag>` (PIE + `771_rd_walk_test.py`), e.g. `"rooms:3,expand:+x,rooms:2,map:a,expand:-y,home"`; results in `SourceArt/random_dungeon/walk_<tag>.json`. At the end it measures every container of every section (`container_check.py`): a closed lid lies on its body, a closed wardrobe's doors stand on its front, an opened lid stands up at the back, opened doors out in front. `Config/DefaultEditorSettings.ini` keeps the editor at full speed in the background (otherwise PIE runs at ~3 fps while a script drives it).
4. Showcase: Save As `random_dungeon_level_Cine`, restart, open it; `773_rd_cine_setup.py` (demo character running east along a lane through the chapel and prison into the next section; generator follows her with a fixed seed, opens doors in front of her, 12 m trigger); `774_rd_cine_record.py` (Simulate; stop it after "RDPATH saved"; also records the map data); `775_rd_sequence.py` (one camera, doorway / ceiling clearance checks); render `LS_RD_Showcase` with `75`; HUD with `pipeline/blender_numpy/rd_reel_overlay.py <frames> <out_dir> claude_ue5/Saved/Logs/claude_ue5.log` (run it before the next PIE session), then encode from 0.

**random_dungeoncombat_level** (`790`–`799`, C++ in `claude_ue5/Source/claude_ue5/RD`: `URDCombatComponent`, `URDBloodComponent`, the fighting, wounds and voice of `ARDMonster`, the sound part of `ARDDungeonGenerator`, the stylised maps and combat panel of `ARDHUD`; a local sound library for the sounds (`SourceArt/random_dungeon_combat/sounds.json` names the files; they are not in the repository); packs: random_dungeon_level's, plus the mask textures of `HallowedDepths/RealisticBlood` (blood decals and spray), plus `Medieval_Weapons` (sword, spear, axe, shield), `Weapon_Shield_Animations`, `Spear_And_Shield_Animations`, `Animations_Warrior` (her clips) and the attack / hit / death clips of `Creatures_Pack`):
1. Build the C++ module, relaunch; random_dungeon_level must exist (`770`).
2. `790_rdc_weapons.py` (an IK rig for each animation pack's mannequin, a retargeter onto her rig, the clips retargeted to `/Game/RandomDungeon/Combat/Anims` and root locked; the blow time of every attack clip, where her weapon hand moves fastest; the grips, computed from her reference pose since her skeleton has no fingers, and checked against the mesh: where her hand closes the weapon must be a round, thin handle, and its business end is the longer part from there (the sword's mesh origin is the tip of its blade); writes `SourceArt/random_dungeon_combat/weapons.json`).
3. `791_rdc_level.py`: the first run saves random_dungeon_level as `random_dungeoncombat_level` (Save As) and stops: restart the editor, run it again. The second run opens the copy and sets up its generator: `bCombat`, the weapons, the monsters' attack / flinch / death clips with their blow times and factors, 30% coverage, the two tiers, `bStylizedMap`, the PlayerStart in the middle of the start section; it prints every kind's hit points and damage in both tiers. Re-run it after `790` or after changing the numbers.
4. Combat test: `793_rdc_combat.ps1 "<plan>" <tag>` (PIE + `792_rdc_combat_test.py`), e.g. `"setup,weapons,monsters,kill:3,hurt,tier,death,regen,map"`: where she starts, each weapon in her hand and its attack, the coverage and the start tier against her, kills blow by blow, a monster hurting her, the tier of a generated section, death and return, regeneration, the map data; `blood` (a burst on a blow, drops in the air, marks where they land, a burst from her when she is hit), `wounds` (a wound a blow on that monster's skin in an overlay material of its own, nothing on any other monster, a pool when it dies) and `sounds` (her steps, a door, the fire voices by a torch, the falloff of the placed sets, a monster's roar / cry / death, the rumble of a generated section: counted by occasion) and `music` (the wandering track and atmosphere, the battle pair from the track's start when a monster comes at her, the wandering track resumed after the fight, another battle track in the next fight) and `containers` (all 984 containers of the start section measured closed, four of each kind opened and measured, closed again) and `look` (flame particles alive at a torch and a brazier, the broken walls' pieces in every section, the wood face under each container lid); `weapons` also measures that her hand is on each weapon's handle and that the shield's top is up; results in `SourceArt/random_dungeon_combat/test_<tag>.json`.
5. Blood and wounds: `798_rdc_gore.py` (materials in `/Game/RandomDungeon/Combat/Materials`: the drops, the spray sprites, the decals with one instance per mask of the RealisticBlood pack, and `M_RDC_Wounds`, the overlay material whose `Wound0`..`Wound9` parameters are spheres in the mesh's reference pose; sets the generator's gore properties). The pack's own decal material is not used: it does not compile with Substrate.
6. Sound: edit `SourceArt/random_dungeon_combat/sounds.json` (the library's root, which files are played for which occasion, each set's level, volume, pitch and falloff, the master volume; the music: `Music.Explore` / `Music.Combat` tracks and the `Atmos.Explore` / `Atmos.Combat` beds, flat stereo loops, a battle track's start past its lead-in, `music_volume`); `pipeline/blender_numpy/rdc_sound_prep.py` (a Python with numpy and imageio-ffmpeg) converts them into `SourceArt/random_dungeon_combat/audio` (mono 44.1 kHz, silence trimmed, levelled); `797_rdc_sounds.py` imports them into `/Game/RandomDungeon/Audio` and fills the generator's `Sounds` and the monsters' `SoundSet` / `StepLength` (`797_rdc_sounds.py noimport` after changing only numbers). `799_rdc_sound_test.ps1 [out_dir] [python]` starts the level as a game of its own with `-RDSoundTest`: the generator records the audio device's output while it plays one flat sound and the same placed sound 2 m ahead, 4 m right, 4 m left, 12 m and 25 m ahead, and `rdc_sound_check.py` reads the recording (is the placed sound there, louder on its side, quieter with distance?).
7. Showcase (on the level itself, no Cine copy; with sound: start the editor with `-deterministicaudio`, or the job's `.wav` is missing): `794_rdc_reel_sequence.py` (`LS_RDC_Showcase`: 45 s, no tracks); `795_rdc_reel_pilot.py` right before `796_rdc_reel_render.py <out_dir> preview|final` (the pilot waits for the render's world, restarts the dungeon with a fixed session seed on the first frame, plays her with movement input and the combat component's functions, turns her camera and records the play; wait for "RDCREEL saved"; `795_rdc_reel_pilot.py rehearse` plays the same in a running PIE session). The record also holds every sound the game played and every blood burst. HUD (minimap, status panel, monster bars, damage numbers, captions, what is heard written out, the music playing) with `pipeline/blender_numpy/rdc_reel_overlay.py <frames> <out_dir>`, then `encode_video.py <out_dir> out.mp4 0 30 <frames>\rdc.MasterSubmixDefault.wav [video_kbps]` (the queue's `.wav` is the game's own mix; in a render the placed sounds are centred: the engine's non-realtime audio device loses spatialised sources, so the generator plays them without direction there).

**random_isometric_village_level** (`780`–`787`, C++ in `claude_ue5/Source/claude_ue5/IV`; packs: House Forge modular house kit `HouseForge_01` and its Viking village props, the castle furniture kit and castle_level's openable barrels / crates, Medieval Docks, Village / Castle / War Camp collections, Modular Church props, Sherwood and Old Windmill foliage; villagers from NPC_Characters_Pack, NPC_Kids_Pack, NPC_Beggars_Pack and NPC_King_And_Queen; reveal materials from random_level's `753`; `r.CustomDepth=3` in `DefaultEngine.ini` for the silhouette):
1. Build the C++ module (`pipeline\build_cpp.ps1`, editor closed), relaunch.
2. `780_iv_level.py` (pieces normalised to the village frame, `M_IV_Ground` / `M_IV_Silhouette`, `BP_IV_GameMode` with `IVPlayerController` + `IVHUD`, level, start section, PlayerStart in the middle of the square; saved; prints the number of doors / containers that cannot be reached: must be 0; runs `786_iv_villagers.py`, which fills the generator's villager models and coverage: run `786` on its own after changing only that list). Re-run after changing the plan or the furnishing code. The first run builds the kit's Nanite meshes (slow, once). `780_iv_level.py containers` only rewrites the container pieces in the open level's generator, as `770`'s does (the level and its Cine copy).
3. Walk test: `782_iv_walk.ps1 "<plan>" <tag>` (PIE + `781_iv_walk_test.py`), e.g. `"input,rotate,villagers:25,houses:3:turn,map:a,expand:+x,villagers:15,houses:2,expand:-y,home"`: the 8 directions (keys and scripted stick), turning the view, the villagers of every section (count, walking, never on a blocked cell), doors and containers with F, the cutaway (with `:turn` from all 8 view directions), generation across each edge, and at the end where every container's lid or doors are (`container_check.py`); results in `SourceArt/random_isometric_village/walk_<tag>.json`.
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
- Encode with `pipeline/blender_numpy/encode_video.py <frames_dir> <out.mp4> 36 30`. The `36` drops the warm-up frames (the procedural levels' reels encode from 0).
- Every reel is kept in two sizes in `renders/`: `<Name>_Showcase.mp4` (1080p, CRF 16) and `<Name>_Showcase_20MB.mp4`, a two-pass encode at a fixed video bitrate: `encode_video.py <frames_dir> <out.mp4> <start> 30 <track.wav or -> <video_kbps>` (45 s at 3300 kbps with a 128 kbps sound track is about 18.5 MB).
- The reels so far: fig4 locomotion, Meshy biped, Dystopia soldier, FF, FF2, castle interiors and furnishing, JRPG Fem5 in the meadow, the sci-fi city, random_level, random_dungeon_level, random_isometric_village_level, the starship fighter, and three of random_dungeoncombat_level (combat; blood, wounds and sound; music).

## What's not in the repo

[docs/assets.md](docs/assets.md) lists every visual and sound asset the project uses, with its author or store listing.

These are excluded for size (the project's `Content/` is about 450 GB with all the packs, and single files exceed 1 GB) and licensing:

- **Unreal content** (`claude_ue5/Content/`), including third-party packs:
  - Medieval Fantasy Village and Fantasy Castle Environment, both from Fab
  - Monolith megastructure
  - Megascans scans (Saloon Interior pack)
  - the packs named in each level's rebuild notes above (the sci-fi city, the dungeon, town, village and space kits, the creature, villager, weapon and animation packs)
  - MetaHuman assets and the UE template mannequins
- **Source characters:**
  - the Tripo anime female GLBs
  - the Meshy AI biped zip
  - the Dystopia Soldiers pack (Fab, Unity format)
  - the fig4 scan
- **Source art binaries:** FBX, GLB, Alembic, DNA and textures.
- **Sound:** the sound-effect and music library that `random_dungeoncombat_level` plays from, and the files converted from it (`SourceArt/random_dungeon_combat/audio/`). Only `sounds.json`, which names the files, is committed.
- **Renders and showcase videos** (`renders/`).
- **Packaged games** (`builds/`): they hold cooked pack content.
- **Per-machine folders:** `Saved/`, `Intermediate/`, `DerivedDataCache/`.

To rebuild a level you need the same packs locally:
1. Add the Fab packs to the project through the Epic Games Launcher.
2. Put the character sources where the build scripts expect them.
3. Build the C++ module (`pipeline\build_cpp.ps1`).
4. Run the scripts in order.
