---
paths:
  - "pipeline/unreal/90*.py"
  - "pipeline/blender_numpy/*_doc.py"
  - "docs/*.md"
  - "claude_ue5/SourceArt/*_gallery/**"
---

# The galleries (docs/monsters.md, vehicles.md, objects.md, heroes.md, humanoid_enemies.md)

<!-- moved from CLAUDE.md (2026-10-23) to load only when these files are opened -->

## Monster gallery (`docs/monsters.md`, `900`)

- The ranking is data (`SourceArt/monster_gallery/monsters.json`); `monster_doc.py` writes the page and the strips from it. Edit the JSON, not the page.
- **The user allowed committing the gallery's pictures** (`docs/images/monsters/*.jpg`: renders of pack models, not the models). The packs themselves, their textures and the Unity files unpacked into `SourceArt/fab_unity` stay local.
- **Shoot after the shaders are ready.** A `SceneCapture2D` loop inside one Python call cannot wait for anything: materials still compiling are drawn with the engine's grey checker placeholder, and textures with their low mips. That made most of the first gallery grey. `900` stages the monsters, then puts the variant material on every one (`warm`: each kind of skinned mesh needs its own shader permutation), and shoots in a later call with `r.TextureStreaming 0`.
- Python details:
  - `MaterialEditingLibrary.get_used_textures` takes a `Material` only; read an instance's own textures from `texture_parameter_values`.
  - A `SceneCaptureComponent2D`'s `show_only_actors` cannot be set from Python ("cannot be edited on templates"): use `show_only_actor_components`.
  - The scratch level is left empty and saved: a dirty level makes the next map load ask, and the editor waits for the answer.

## Vehicle gallery (`docs/vehicles.md`, `903`)

- The list, uses and descriptions are data (`SourceArt/vehicle_gallery/vehicles.json`); `vehicle_doc.py` writes the page, its sizes and animation notes come from `902`. Its pictures are allowed in git like the other galleries'.
- Models from 0.6 m to 115 m stand in one row: each gets a floor of its own, and every shot uses a show-only list (the model and its floor), or the neighbours fill the background. The camera distance is fitted to the model's box corners for the view direction; the "side" is the long side, unless `axis` says otherwise (the dragon's wingspan is longer than its body).
- **A long session of galleries ran the editor out of memory** (texture streaming off, hundreds of packs' textures loaded): it crashed staging the first vehicles. Restart the editor before a big gallery; after the restart the first `load_level` of the scratch level did not take for play-in-editor (PIE played the startup map): load it with `EditorLoadingAndSavingUtils.load_map` and check the PIE world's name.
- Right after play-in-editor stops, `get_editor_world()` can return None for a few seconds: a batch driver must wait for it before the next stage, check that play has started on the level it staged (`UEDPIE_0_<level>`) before shooting, and that it has stopped before staging again.

## Weapons and items gallery (`docs/objects.md`, `904`)

- The list, uses and descriptions are data (`SourceArt/object_gallery/objects.json`: `section`, `group`, `kind` for the third-person sets that hold it, `fp` for its first-person arm clips); `object_doc.py` writes the page. Its pictures are allowed in git like the other galleries'.
- An FPS pack's shot and reload clips are often on the bare gun's skeleton (`*_Basic`), not the full gun's: `904` uses a clip only if one of the entry's meshes is on its skeleton, otherwise the third picture is the far three-quarter view.
- **Armour** comes in pieces skinned to a character's skeleton; an armour set is all of one character's pieces (picked by name: armour, helmet, mask, crown, pads... never the bare body or arms under them) on one spot, an empty suit in the reference pose. Its note names the wearer (`wearer`). Armour sets carry full-size character textures: with texture streaming off, 8 sets in one batch ran a long-lived editor out of memory. Stage 4 at a time and restart the editor every 40 or so.
- The claims of the third-person table (`WIELD` in `object_doc.py`) were checked against `902`'s libraries: there are no third-person bow, crossbow, staff, knife or throwing clips for the UE4 mannequin here (the Dark Fantasy Weapons pack aims a bow and a crossbow on the UE5 mannequin). Check them again after importing animations.

## Hero and enemy galleries (`docs/heroes.md`, `docs/humanoid_enemies.md`, `901`, `902`)

- The lists, roles and descriptions are data (`SourceArt/hero_gallery/heroes.json`, `SourceArt/enemy_gallery/enemies.json`); `hero_doc.py` and `enemy_doc.py` write the pages. Their pictures are allowed in git like the monster gallery's. An enemy that is also a hero (`hero`) shows the hero's pictures and is not shot again.
- Each entry's animation note and the Animations section come from `902` (`SourceArt/character_animations/animations.json`: clips grouped by skeleton, each character's rig by its bone names) through `anim_text.py`; the Fab download's clips that were never imported come from `asset_survey/fab_animations.csv`. Re-run `902` after importing animations.
- **Framing an action pose:** a skeletal mesh's bounds in play are not where its posed body is: a crawl clip moves the root away from them, and some packs' bounds are far bigger than the body (the post-apocalypse zombie came out a speck). `901` frames the action shot on the bone positions (plus the weapon) whenever the bounds disagree with them.
- **Models of several meshes** (the crawlers: body, head, guts; a fish-man's shell): one actor per mesh, all on the same clip; a part on a skeleton of its own (Half Creature 01's eye) is left out of the posed copy, since the clip would not move it.
- **Action poses:** a one-frame AnimSequence made with the animation controller (`add_bone_curve`, `set_bone_track_keys`) on the hero's own skeleton: another pack's clip's local bone rotations at one frame, on the hero's bone lengths. It works between UE4-mannequin rigs (same bone names and axes); FF2's (Tripo) spell laid the body on the floor.
- **Pose frame:** the right frame differs per clip. An axe at its overhead wind-up turned the body away from the camera; a punch is the frame the fist is farthest forward, not farthest from the hips (the drunk man's swing then had the arms out like a T).
- **Where animations show:** the editor world does not evaluate a single-node animation on a `SkeletalMeshActor` (`set_update_animation_in_editor` did not help): stage in the editor, shoot during play-in-editor, which copies the staged actors.
- **Batch sizes:** with `r.TextureStreaming 0`, 100 staged characters ran the machine out of memory (the editor crashed) and 12 heavy ones hung the GPU (a D3D12 timeout, the editor stuck on an error dialog). Stage 6 to 10 at a time.
- After a crash the editor may stop on a **Restore Packages** dialog, which waits for an answer before remote execution comes up. `Saved/Autosaves/PackageRestoreData.json` lists the packages. Set it aside only if you know they are not wanted, as with a pack material that was never edited.
