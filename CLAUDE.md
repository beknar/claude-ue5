# CLAUDE.md

Guidance for Claude Code in this repository. See README.md for what the project is, its level table and its Documentation section; what it can do is in `docs/capabilities.md`, each level's description and how it was built (its rebuild notes) in `docs/levels/<level>.md`, the stage ranges in `docs/pipeline.md`.

## Goals

- **Everything is built by script.** A level, a character or an effect exists because a numbered script (or the C++ module plus the script that fills its data) builds it; nothing is arranged by hand in the editor. A change is finished when the script that makes it is in `pipeline/`.
- **Each world is a game, not a backdrop.** The newer levels are played: generated in play, with doors, containers, creatures, fighting, sound and music. A new feature for one of them comes with a step in that level's scripted test, and the level's document (`docs/levels/<level>.md`: its row of the level table and its rebuild notes) says what it does.
- **A feature is shown in a demo reel.** When asked for a reel: the same kind as the level's earlier ones (45 s for the dungeon fight, 30 s for the fighter), rendered at 1080p, and delivered in two files in `renders/`: `<Name>_Showcase.mp4` and `<Name>_Showcase_20MB.mp4` (20 MB or less: `encode_video.py`'s `video_kbps` argument). Earlier reels are kept; a new one gets a new name.
- **Measured, not assumed.** A claim in a report is one a test, a recording or a rendered frame showed. A test must measure the thing itself, not a number that stands for it (a container's open value said nothing about where its lid was). What could not be checked is said so: nobody here hears a sound or watches a video, so sounds and music are chosen by name and measurement and verified by recordings.

## Environment

| What | Where |
|---|---|
| Unreal Engine 5.8 | `E:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe` |
| Project file | `E:\code\claude-ue5\claude_ue5\claude_ue5.uproject` |
| Blender 5.1 | `C:\Program Files\Blender Foundation\Blender 5.1\blender.exe -b -P script.py -- args` |
| Editor log (actual Python/Blueprint errors) | `claude_ue5/Saved/Logs/claude_ue5.log` |
| Fab vault (launcher downloads) | `C:\Users\kestanol\Documents\code-godot\epicgames media packs\VaultCache` |
| Asset library (sound effects, music, the Fab library surveyed in `asset_survey/`) | `I:\game assets` (read only: licensed, never copied into the repository) |
| Showcase videos, packaged games | `renders/`, `builds/` (both ignored) |

- **Shell:** Windows PowerShell 5.1. When writing a .py file from PowerShell, use `[IO.File]::WriteAllText(path, text, (New-Object Text.UTF8Encoding $false))`; `Set-Content -Encoding utf8` adds a BOM that the editor's Python rejects. In an array literal the comma binds tighter than `+`: `@('a', 'b' + $x)` is `('a', 'b') + $x`, so a find / replace pair built that way silently replaces with the wrong text (it dropped a line from two files): patch files with a Python script that asserts each match.
- **Python in the editor:** `python pipeline\blender_numpy\ue_exec.py <script.py> [args]`, where the args become `sys.argv`; `-c "code"` runs a snippet and `--ping` checks for an editor. The editor needs PythonScriptPlugin remote execution (enabled in `Config/DefaultEngine.ini`).
- **Python outside the editor:** the overlays, `encode_video.py`, `rdc_sound_prep.py` and `rdc_sound_check.py` need numpy, scipy, Pillow and imageio-ffmpeg. On this machine none of the system Pythons has imageio-ffmpeg and `UE_PY` is not set: `C:\Users\kestanol\Documents\code\amv-maker\venv\Scripts\python.exe` has them all. The PowerShell test drivers (`761`, `772`, `782`, `793`, `803`) call `python`, or the interpreter in the `UE_PY` environment variable; `799` takes one as its second argument.
- **MCP:** an `unreal-mcp` server (UE ModelContextProtocol plugin, `http://127.0.0.1:8765/mcp`) is configured in `.mcp.json`.

## Conventions

- **Script names:** editor scripts are `pipeline/unreal/NNN_name.py`, numbered in build order. Each starts with a docstring giving its purpose and arguments. New stages get the next free number in their range (see `docs/pipeline.md`). `790`-`799` (random_dungeoncombat_level) is full, `800`-`806` is starship_level and `810`-`820` the two magic levels: `821` switches every dungeon level's tactical maps on, `822`-`823` are random_dungeonmagic_level3 (the Rogue) and `824`-`831` random_dungeonmagic_level4 (the choice of hero; `829` its reel's menu pilot, `830` its painted interface, `831` its menu first) and `832`-`841` random_dungeonmagic_level5 (the Summoner and her face; `835` / `836` its face reel; `837`-`840` her MetaHuman face, `841` its reel; `842`-`848` Summoner2; `849`-`853` the level rebuilt from level 4 with Summoner3 and the armour, `853` its test; `854`-`855` the weapons table and the five tiers of rooms; `856` armour by weight; `857` the armour table, loot table and crafting; `858` spells, rings, tomes, the containers' chance, corpses, the Escape menu; `859` monsters by tier; `860` the Warrior's and the Warlock's arms lengthened, in every level; `861` the chop test of Warrior2.glb; `862` Warrior3, level 5's Warrior), `863`-`868` mistward_castle (`863` the level, `864` its themes' pieces, `865` its items, traps, prisoners and switches, `866` the monsters' heights, `867` its pictures, `868` its test, `869` its materials' usage flags for a packaged game; `pipeline/package_mistward.ps1` packages it; `870` the user's third list on it and on level 5: trap outlines, inventory tabs, quick slots, the helmet, the block, start gear, armory pickups, eight special rooms, boss slashes; `871` the Mage's mana pool from the Null Sanctum and Apocalypse tomes, on both; `872` the Martial Artist (MartialArtist2.glb) on mistward_castle and martial_arts, `873` martial_arts, her one-room level; `874` her chi attacks' and abilities' pictures on both; `875` the user's list of 2026-10-30 on mistward_castle: harvests, recipes by tier, scrolls, any equipment broken down, Wood Glue, the fires' volume; `876` the Summoner (Summoner4.glb), its sixth hero; `877` the parts', scrolls' and summons' pictures; `878` the user's list of 2026-10-31 on mistward_castle: the Escape menu's Options page, the hero menu's QUIT GAME, summoned allies kept apart, the summons panel, allies on the maps; `879` the list of 2026-10-31b on mistward_castle: monsters that shoot, meaningful names, the arena locked and its audience, autoplay, ceilings of more shapes): further dungeon stages start at `880`.
- **One-off probes:** keep them out of `pipeline/` (use a scratch directory) unless they become a pipeline stage.
- **Idempotent:** scripts delete what they previously generated (by tag, label or asset path) and rebuild it. Spawned actors are tagged:
  - `castle_gen`: `340` (doors, floors, containers)
  - `castle_furn`: `380` (furniture)
  - sf-city-level: `sfc_road` (`703`), `sfc_struct` (`706`), `sfc_start` (`707`), `sfc_safety` (`708` barrier walls)
- **Cinematic copies:** each level has a `*_Cine` copy. Demo characters run on the Level Sequence clock (`SeqTime`/`DemoStartTime`), so Simulate (game time) and Movie Render Queue renders match.
- **Coordinates:**
  - UE = Blender (x, −y, z) for FBX round trips.
  - The furniture kit's front is UE +Y.
  - Kit sizes are in cm; the Blender scene uses `scale_length` 0.01.
- **End of big scripts:** delete the module globals and run `gc.collect()`. Lingering actor references caused python311 access violations on the next PIE start or map load. `ue_exec.py` now runs each script in a fresh namespace and clears it afterwards, also when the script raises (an exception's traceback otherwise keeps its actors alive). Scripts that leave a tick callback running must set `__keep__ = True` (their functions still need their globals) and drop their actor references when the callback finishes.
- **C++ module** (`claude_ue5/Source/claude_ue5`: `RT` town, `RD` dungeon and its combat / blood / sound, `IV` village, `SS` fighter): build with `pipeline\build_cpp.ps1` while the editor is closed, then relaunch. Unity builds merge the .cpp files: give file-local helpers and constants a module prefix (`IVPickSign`, `RDPickSign`, `IVCyan`, `SSGreen`), or adding a file can make two of them collide. No .NET Framework SDK is installed, so the script points UnrealBuildTool at a stand-in NETFXSDK (UE_SDKS_ROOT) for that build only. Python sees UPROPERTY bools without the `b` prefix (`bCollision` -> `collision`).
- **Scripted PIE needs the editor unthrottled:** with the window in the background the editor drops to ~3 fps ("Use Less CPU when in Background", `config=EditorSettings`, a per-user global ini). `Config/DefaultEditorSettings.ini` turns it off for this project only.
- **Hand-formatted JSON** (`heroes.json`, one entry per line): edit the text in place; `json.dump` rewrote its layout (a 300-line diff for a 6-line change).
- **Level 5's tables from data:** the level 5 tables in `docs/levels/random_dungeonmagic_level5.md` (heroes, armour, weapons, loot, recipes, spells, rings, breakdown, monsters) are written by `pipeline/blender_numpy/rdm5_tables_doc.py`; re-run it after changing `heroes.json`, `summoner_hero.json`, `armour.json`, `loot_table.json` or `weapons_table.json` (and `857` / `855` for the game).
- **Never run two editors on the project.** After the crash a relaunch was checked with `-match "NODE"`, which (case-insensitive) matched ue_exec's `no remote nodes found`; a second editor was started, and remote commands went to either one: stages landed in one, play started in the other, batches shot nothing or the previous batch. Check `Get-Process UnrealEditor` before launching and test ue_exec's ping with `-cmatch "^NODE"`.

## Area notes (`.claude/rules/`)

Each area's lessons are in a rules file that loads when a file of that area is read or edited. Running a script from the shell does not load it: **read the area's file before working there.**

- `.claude/rules/dungeon.md`: random_dungeon_level and random_dungeoncombat_level (every dungeon level is a copy of these)
- `.claude/rules/dungeon-magic.md`: the magic levels 1 to 3 (casters, the Rogue, the tactical maps, clips made in Blender, the Warlock's hair)
- `.claude/rules/dungeon-heroes.md`: random_dungeonmagic_level4 and random_dungeonmagic_level5 (the choice of hero, the interface, the Summoner and her faces, armour, weapons, tiers)
- `.claude/rules/mistward.md`: mistward_castle (themes, shaped rooms and their sizes, tidy furniture, the tiers' share rule, bosses and guarded rings, shields, the torch, traps, teleporters, cells, death drops, monster heights, the mouse and input as the devices send it, its icons, test and reel; the Martial Artist and martial_arts; harvests, scrolls, recipes by tier and the Summoner; the Options page, allies kept apart, the Martial Artist's guard; shooting monsters, the arena's audience, autoplay, vaulted ceilings)
- `.claude/rules/town-village.md`: random_level (the town) and random_isometric_village_level
- `.claude/rules/starship.md`: starship_level
- `.claude/rules/sequencer.md`: Sequencer and Movie Render Queue from Python
- `.claude/rules/galleries.md`: the galleries (docs/monsters.md, vehicles.md, objects.md, heroes.md, humanoid_enemies.md)
- `.claude/rules/editor-pitfalls.md`: editor pitfalls (maps, Blueprint DSL, asset edits, retargeting, materials, castle_level, sf-city-level)

## Working rules

- **Commit and push only when the user asks.** Finished work stays uncommitted until then, and the report says so.
- **Leave the editor usable:** on a playable level (not a `*_Cine` copy), play stopped, started without `-deterministicaudio` (that switch is for a render with sound only; relaunch without it afterwards).
- **Scratch stays out of the repository:** probes, intermediate renders and test recordings go to the session's scratch directory.

## Safety

- **No full-desktop screenshots:** one exposed private windows, including credentials. Verify visually with editor-viewport `HighResShot`, Movie Render Queue frames or `SceneCapture2D` (`pipeline/unreal/capture.py`) only.
- **Fab downloads:** acquiring or downloading Fab content needs the user in the Epic Games Launcher. Don't automate the launcher UI.
- **System software:** installing anything on the machine (an SDK, a runtime, a codec) needs the user's go-ahead first.

## Git

The remote (`github.com/beknar/claude-ue5`) is **public** and the repo is **source only**:
- Never commit `Content/`, `.uasset`/`.umap`, source-art binaries, media (`.png`, `.mp4`, `.wav`, …), archives, `Saved/` / `Intermediate/` / `DerivedDataCache/`, `renders/` or `builds/` (a packaged game holds cooked pack content).
- Third-party packs (Fab, Megascans, MetaHuman, UE mannequins) and the sound and music library must not be redistributed. `SourceArt/random_dungeon_combat/audio/` (files converted from the library) is ignored; `sounds.json`, which only names the files, is committed.
- `.gitignore` enforces this. Check `git status` before committing: a new kind of generated file needs its ignore rule first.
- `ai models/*.glb` (the project's own Tripo characters, CC BY 4.0: `ai models/LICENSE` and `README.md`) is the one model exception: the user licensed them free to use. `old models/` (deprecated) stays ignored. The files were renamed: jrpg-fem5-tripo -> `Warrior.glb`, girl-caster-tripo -> `Mage.glb`, girl-darkcaster-tripo -> `Warlock.glb`; scripts, docs and Unreal assets keep the old names and tags (`Fem5`, `Caster`, `DarkCaster`).
- The galleries' pictures (`docs/images/monsters/*.jpg`, `docs/images/heroes/*.jpg`, `docs/images/enemies/*.jpg`, `docs/images/vehicles/*.jpg`, `docs/images/objects/*.jpg`) are allowed by the user, like the stills in `docs/images/` (shown in the level documents and `docs/reels.md`).
- Commit or push only when asked (see Working rules). Small data that a script reads or a test wrote (`SourceArt/**/*.json`) is committed; a test record replaces the one before it.
