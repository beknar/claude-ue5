---
paths:
  - "pipeline/unreal/6*.py"
  - "pipeline/unreal/*sequence*.py"
  - "pipeline/unreal/*render*.py"
  - "pipeline/unreal/*cine*.py"
  - "pipeline/unreal/*reel*.py"
---

# Sequencer and Movie Render Queue from Python

<!-- moved from CLAUDE.md (2026-10-23) to load only when these files are opened -->

- **Sequencer from Python** (`660` / `663`, the Tripo trio and quartet showcases):
  - To look at a sequence before rendering it: open it (`LevelSequenceEditorBlueprintLibrary.open_level_sequence`), `set_current_time`, and `pilot_level_actor` the camera of that cut with the game view on; `set_lock_camera_cut_to_viewport` from Python left the viewport where it was. Close the sequence and eject the pilot before a render.
  - In 5.8 a skeletal animation section's play rate is a `MovieSceneTimeWarpVariant` (`set_fixed_play_rate`), not a float. A section's easing is set from text (`import_text("(bManualEaseIn=True,...)")`): `manual_ease_out` cannot be set by name.
  - Two transform keys on the same frame (the end of a linear turn and the jump to the next place) made her slide off the plinth through the whole turn: the last key of a movement goes a frame before the next one.
  - `delete_asset` on a sequence that is still loaded, then `create_asset` under its name, gives None: empty it instead (remove its bindings and tracks). `814` did that and left the reel's sequence deleted for the session.
  - A frame that no animation section covers shows the mesh's T-pose: the trio and quartet reels flashed it in every pause between two casts, shots or blows (nobody saw it for two reels). `660` / `663`'s `animate()` now bridges each pause (an action clip plays on as far as it has frames, then its last frame is held: a section that runs past its clip starts it again), puts each section on a row where it overlaps nothing (two on one row: Unreal trims one), makes the blends whole frames that start on the next section's first frame (a frame apart, blend out + blend in dipped to 0.83: a twitch toward the T-pose), and sets the ranges a second time (a section followed by one of the same clip came out ending where that one starts). Both read the sequence back and measure it (each frame's summed section weight, ease in x ease out; clips played past their end): their last line says `animation on every frame: yes`.
  - Python cannot spawn actors into a play world here (no deferred spawn): what a pilot moves in a render (the spell light) is placed in the level and found by its tag; effects are spawned as components (`spawn_system_at_location`, `spawn_emitter_attached`).
  - The studio's exposure bias (9.5) was set for fig4's dim MegaLights rig; with ordinary rect lights the stage needed -1.5. Tune it with captures at a row of biases before rendering.
- **MRQ warm-up runs at every camera cut:** world time advances while the sequence is frozen, so a demo character steered on the sequence clock stops and restarts at each cut, and time-based effects jump ahead. Shoot runtime-driven scenes as one camera cut (random_level's `756`).
