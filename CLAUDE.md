# CLAUDE.md

Guidance for Claude Code in this repository. See README.md for what the project is and how the levels were built.

## Environment

| What | Where |
|---|---|
| Unreal Engine 5.8 | `E:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe` |
| Project file | `E:\code\claude-ue5\claude_ue5\claude_ue5.uproject` |
| Blender 5.1 | `C:\Program Files\Blender Foundation\Blender 5.1\blender.exe -b -P script.py -- args` |
| Editor log (actual Python/Blueprint errors) | `claude_ue5/Saved/Logs/claude_ue5.log` |
| Fab vault (launcher downloads) | `C:\Users\kestanol\Documents\code-godot\epicgames media packs\VaultCache` |

- **Shell:** Windows PowerShell 5.1. When writing a .py file from PowerShell, use `[IO.File]::WriteAllText(path, text, (New-Object Text.UTF8Encoding $false))`; `Set-Content -Encoding utf8` adds a BOM that the editor's Python rejects.
- **Python in the editor:** `python pipeline\blender_numpy\ue_exec.py <script.py> [args]`, where the args become `sys.argv`; `-c "code"` runs a snippet and `--ping` checks for an editor. The editor needs PythonScriptPlugin remote execution (enabled in `Config/DefaultEngine.ini`).
- **MCP:** an `unreal-mcp` server (UE ModelContextProtocol plugin, `http://127.0.0.1:8765/mcp`) is configured in `.mcp.json`.

## Conventions

- **Script names:** editor scripts are `pipeline/unreal/NNN_name.py`, numbered in build order. Each starts with a docstring giving its purpose and arguments. New stages get the next free number in their range (see README).
- **One-off probes:** keep them out of `pipeline/` (use a scratch directory) unless they become a pipeline stage.
- **Idempotent:** scripts delete what they previously generated (by tag, label or asset path) and rebuild it. Spawned actors are tagged:
  - `castle_gen`: `340` (doors, floors, containers)
  - `castle_furn`: `380` (furniture)
- **Cinematic copies:** each level has a `*_Cine` copy. Demo characters run on the Level Sequence clock (`SeqTime`/`DemoStartTime`), so Simulate (game time) and Movie Render Queue renders match.
- **Coordinates:**
  - UE = Blender (x, −y, z) for FBX round trips.
  - The furniture kit's front is UE +Y.
  - Kit sizes are in cm; the Blender scene uses `scale_length` 0.01.
- **End of big scripts:** delete the module globals and run `gc.collect()`. Lingering actor references caused python311 access violations on the next PIE start or map load.

## Editor pitfalls

**Maps**
- Never `duplicate_asset` a map. Use `EditorLoadingAndSavingUtils.save_map` (Save As), then restart the editor (`unreal.SystemLibrary.quit_editor()` and relaunch) before opening the copy.
- Save As fails ("Unable to overwrite existing package") when the target map was loaded earlier in the session. Quit, move the old `.umap` out of `Content/`, relaunch and Save As again.
- Never reload the currently open map from Python.
- Before stopping PIE, wait a couple of seconds after `HighResShot`; once the editor asserted on `GameViewport.IsUnique()`.

**Blueprint DSL** (`editor_toolset` `write_graph_dsl`)
- `elif` nests as the last form of the previous branch.
- FText pins take no literals; enum pins take quoted names (`:Channel "ECC_Pawn"`).
- `Utilities|IsValid` is a macro with no bool output.
- One bad form leaves an empty graph. Read the graph back and check `LogScript: Warning` in the log.

**Asset edits**
- Struct arrays such as SkeletalMesh materials and BlendSpace samples are copies. Rebuild the whole array, call `modify()`, then `save_loaded_asset(..., only_if_is_dirty=False)` and verify after a reload.

**Retargeting**
- `add_default_ops()` leaves the Root Motion op without bones. Set root/pelvis yourself.
- Keep the template `CR_Mannequin_FootIK` alpha at 0 on UE4-style skeletons.
- CharacterMovement floats the capsule about 2.2 cm, so drop the mesh by that much.
- Tripo clips pin the hips; ground them per clip (FF2 scripts `275`–`289`).

**Materials**
- A TextureSample on an sRGB-off grayscale texture needs `SAMPLERTYPE_LINEAR_GRAYSCALE`. Otherwise the compile fails silently: `MaterialEditingLibrary.get_statistics(m).num_pixel_shader_instructions == 0`.
- The landscape grass mask (`383`) must be `never_stream` with no mipmaps. After changing it, run `grass.FlushCache`.

**castle_level**
- Run `340` before `380`.
- `340`'s traces skip pack foliage and props (`trace_to`).
- Interiors need their own capped-exposure PostProcessVolume.
- The scanned barrels (`SM_Scan_Barrel*`) render as a grey patchwork; use the pack's `SM_barrel_01/02`.

## Safety

- **No full-desktop screenshots:** one exposed private windows, including credentials. Verify visually with editor-viewport `HighResShot`, Movie Render Queue frames or `SceneCapture2D` (`pipeline/unreal/capture.py`) only.
- **Fab downloads:** acquiring or downloading Fab content needs the user in the Epic Games Launcher. Don't automate the launcher UI.

## Git

The remote (`github.com/beknar/claude-ue5`) is **public** and the repo is **source only**:
- Never commit `Content/`, `.uasset`/`.umap`, source-art binaries, media (`.png`, `.mp4`, …), archives, or `Saved/` / `Intermediate/` / `DerivedDataCache/`.
- Third-party packs (Fab, Megascans, MetaHuman, UE mannequins) must not be redistributed.
- `.gitignore` enforces this. Check `git status` before committing.
