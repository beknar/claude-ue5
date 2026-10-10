# claude-ue5

An Unreal Engine 5.8 project built almost entirely from scripts. The scripts drive the running editor over Python remote execution, and Blender + numpy prepare the source art. The project has several playable character showcase levels: third-person controls, a recorded demo route and a Movie Render Queue showcase video for each.

This repository is **source only**: the pipeline scripts, project config and small data files. Unreal assets (`Content/`), source art binaries, renders and the third-party packs they come from stay local. See [What's not in the repo](#whats-not-in-the-repo).

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

Each level has a `*_Cine` copy (`MoviePipelineGameMode` with an AI demo character) for its `LS_*_Showcase` sequence.

**Controls:**
- WASD and mouse: move and look
- Space: jump
- Shift: run
- Ctrl: sprint (Meshy)
- F: open/close in `castle_level`
- Extra move/action inputs on Meshy, FF and FF2: see their input scripts (`110`, `150`, `214`, `260`)

## Requirements

- **Unreal Engine 5.8**, expected at `E:\Program Files\Epic Games\UE_5.8`. Enabled plugins: PythonScriptPlugin (with `bRemoteExecution=True`), EditorScriptingUtilities, EditorToolset, ModelContextProtocol, MetaHuman, HairStrands, MovieRenderPipeline.
- **Blender 5.1**, run headless: `blender -b -P script.py -- args`.
- **Python 3.11+** with `numpy`, `scipy`, `imageio-ffmpeg` and `Pillow`, for the numpy tools, the remote-exec client and video encoding.
- The local asset packs listed below.

## Layout

```
claude_ue5/              UE project (claude_ue5.uproject, Config/; Content/ is local only)
  SourceArt/             exported/converted source art (only small JSON data is committed)
pipeline/
  unreal/                numbered editor scripts (NNN_name.py), run inside the editor
  blender_numpy/         Blender scripts (-b -P), numpy/scipy tools, ue_exec.py, encode_video.py
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
