---
paths:
  - "pipeline/unreal/**"
---

# Editor pitfalls (maps, Blueprint DSL, asset edits, retargeting, materials, castle_level, sf-city-level)

<!-- moved from CLAUDE.md (2026-10-23) to load only when these files are opened -->

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


- **sf-city-level safety:** after changing anything walkable, re-run `708` (flood fill + barrier walls) and check it reports 0 remaining fall edges; the walk test (`709` plan, `710` in PIE) reports clipping, falls, doors and stuck legs.
