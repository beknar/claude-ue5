---
paths:
  - "claude_ue5/Source/claude_ue5/RD/RDMistward*"
  - "claude_ue5/Source/claude_ue5/RD/RDTraps.cpp"
  - "claude_ue5/Source/claude_ue5/RD/RDGear.cpp"
  - "claude_ue5/Source/claude_ue5/RD/RDInputSim*"
  - "pipeline/unreal/86*.py"
  - "pipeline/unreal/868_mistward_test.ps1"
  - "pipeline/blender_numpy/mw_*.py"
  - "claude_ue5/SourceArt/mistward/**"
---

# mistward_castle (`863`-`868`; the user's list of 2026-10-26, `docs/improvements.txt`)

Level 5's Save As copy with the castle's rules (and the user's second list of 2026-10-27). Every rule is a switch on the generator ("Mistward" category), off on the other levels: level 5 itself must stay as it was. Its test is `868_mistward_test.ps1`; its reel is 815 / 816 / 829 with level `mw` (`mwselect` for the menu) and `rdm_reel_overlay.py ... mw`.

## Building it

- **Medieval Castle's wall pieces have doorways and windows through them**: the castle keep's walls are Castle of Eternal Mist's blind arches, faced `+y` (`864`'s `CASTLE_FRONT`; `-y` showed the flat backs). Judge a theme in play, not in an editor capture (shaders still compiling there drew blank pictures).
- **Python**: `unreal.Rotator`'s positional order is roll, pitch, yaw: give keywords (a camera looked at the sky). A bool UFUNCTION with out parameters returns a tuple of the outs. A mesh's vertices: `ProceduralMeshLibrary.get_section_from_static_mesh`. A skeletal shield has no bounding box from Python: `865` makes a static copy with Geometry Script.
- **A shield's face is measured** (the thin axis, the bulge of its middle against its rim); six shields' painted faces are dished or flat and came out reversed: `shields.json`'s `flip`. Look at all 22 on her arm from her side and in `867`'s contact sheet: a shield seen from behind shows its grip bar or its boss's hole.
- **Python cannot spawn actors into a play world here**: `867` shoots in the editor world. Material and transform changes made in one Python call reach the renderer only at the end of the frame (every capture of a batch came out with the last state): shoot over frames from a tick callback. With texture streaming on, the first pictures of a long batch were blurred (low mips): `r.TextureStreaming 0` while shooting.
- **Monster heights** (`866`): measured in play as the lowest 1 % of the body's skinned vertices (a weapon or a tail skewed the very lowest). Clips can disagree: the Insect bobs in its idle and walks 25 cm lower, so `RAISE` lifts it. `866 apply` sets MeshZ from the MeshZ recorded when measured: running it twice does not move a kind twice.

## Rules that went wrong first

- **A container's index and its key are different numbers**: the index is its place in the set as built, the key stays when the set is built again (`ForcedLoot`, the looted test). `PlaceRingGuard` used one for the other: the ring's place came from another container.
- **Every container of a room already opened** (the debug clear opens them all): the guarded ring lies on the floor as a loot pile that is not hers (`ARDLootPile::bHers` false: not her things on the map, not in the death text).
- **Marks beyond the map's edge** were not drawn: the boss and the guarded ring 80 m away were never on the screen. They are pinned to the edge, the way to them.
- **A dart flies 65 cm a frame**: its end point alone passed her by; it strikes along its whole way in the frame (`PointDistToSegment`).
- **A monster set free from its cell had no tile path to her** and stood in the open cell: it walks to the cell's exit first (`ARDMonster::CellExit`), then at her.
- **...through the door's gap, not the front's middle**: the door is the cell's right half of the front (`RDMCellWay`: 73 cm right of the middle). Walking straight from the cell's middle it pressed into the bars' end; the first test passed on a blow struck through the bars. The prisoner too (she walked through the bars: moved without collision).
- **A cell at a row's end with its door against the room's wall**: the broken wall's seal stood 30 cm into the doorway, and with the hay inside nothing could get out (the test's sweep found the seal, a hidden `Cube`). Such a cell is barred all across; the hay lies on the barred half. Measure a way out with a capsule sweep and overlaps along it, not by the door's open value (it was 1).
- **The start section's furniture is saved with the map**: the copy of level 5 kept level 5's (no tidy furniture, the old cells). `865` builds it again under the castle's switches.
- **The test's cells**: stand on the line out of the door's gap (a line from the cell's middle through the hinge left the room at a row's end); a prisoner with no caged monster within 6.5 m, a monster with no other within 9 m; it must be 1.6 m out of its cell.
- **`RestartPlay` left the extra monsters** (a boss's band, guards, those a teleport trap brought) standing in the kept start set: after a few runs 60 of them, and a debug clear that leaves "the nearest N" kept every planned one. It destroys every monster without a `SpawnIndex` now.
- **A killing blow also wears the shield**: a test's blow of a million broke the Warrior's starting shield before she fell, so it was not among what she kept.
- **A reference into `TrapList` dies when the list grows**: the teleport trap's glyphs can go into its own set's list, and a `Reserve` before adding them is itself the move. Read `TrapList[I]` again after adding traps, never the reference taken before (the PR review's find).
- **A trap is recorded spent when it goes off** (`FireTrap`, wards excepted: they set themselves again), not only when it finishes: a set dropped while a lingering or teleport trap was still going off laid it armed again.
- **A guarded ring's pile is not hers**: its prompt and message name the ring ("take the ..."), not "your things". Taking a pile back never wears a set she carries once (`bArmourStacks` off) below what it is.
- **Name new UFUNCTIONs off the engine's**: `TeleportTo(int32)` hid `AActor::TeleportTo` (C4263/C4264) and took Python's `teleport_to` (the engine's `K2_TeleportTo`): `TeleportToTier`.
- **Footprints**: a piece's nominal size can be smaller than its mesh (a table's top over a wardrobe's way in): `ARDSection::FootOf` takes the mesh's box where it is bigger, centred where the box is. Pieces touch by at most 1 cm (0.5 cm under their sizes on each side, so pieces set by their sizes fit; 6 cm until 2026-10-27).

## The user's second list (2026-10-27)

- **Ask which level the user played**: the user reported "the FPS counter is missing, held keys don't scroll, beds and chests intersect, the cells hold a rock, containers close" while every one of those was on in Mistward: the editor's log showed they had played `random_dungeonmagic_level5` (`RDSELECT start: ...level5?Hero=`), where the castle's switches are off. Read the log's `RDSELECT start` / `Created PIE world` lines before chasing a report. They chose Mistward only.
- **Input the way the devices send it** (`RDInputSim`, the generator's and the menu's `SlateKey` / `SlateMouseMove` / `SlateMouseButton` / `SlateWheel`): into Slate, which hands it to the viewport, which hands it to the player controller. `SimulateKey` starts at the player controller and skips focus, capture and where the pointer is. They refuse (and say why) when the game's viewport does not have the keyboard focus or the point is not over it.
- **A floating Message Log covered the game's view** (it opens at start-up for the Kitchen Asset Kit's unloadable textures): Slate sent the clicks to it. `SlateClearView` hides the editor's windows over the view while a test runs and `SlateRestoreView` (or `RDDungeonGenerator.slate_restore_any_view()`, the driver's) shows them again. The editor here is on a high-DPI screen: PowerShell's window rectangles are scaled down (the view is 2440 x 1616 pixels).
- **The pointer**: the game's own input mode captures the mouse and hides it on a click: with the pointer up the mode is game-and-UI (`HideCursorDuringCapture` off, no lock), and the game's own mode is set back when the list closes, when the menu opens the dungeon and when her combat component is made (or the camera turned only with a button held). A hit box that takes a click (`AddHitBox(..., true)`) keeps it from the player controller's keys: the castle's menu keeps its buttons itself (`ARDHeroSelect::Buttons`). A row chosen by the pointer holds the list where it is: following the cursor, a long list re-centred on the row and slid another row under the pointer (the click chose instead of using). The probe on a short list passed: test on a list longer than the screen.
- **RestartPlay doubled the start set's monsters**: `ActivateForPlay` spawned them again beside the ones standing (28 of 14 after one restart; the debug clear then kept the wrong ones and the tiers step saw "11 of 14 killed" at its first kill). The castle's sections destroy theirs first; the other levels still double them (tests and reels only: normal play never restarts).
- **A container's way in is checked at its whole size**: `FootFree` took 3 cm off each side, and a shelf stood 5 cm into a barrel's way. That slack is 0.5 cm now (`RDFootSlack`; the test allows 1.5): at 3 cm a chest could stand 6 cm into a bed's foot board, which reads as one set into the other. A barracks chest goes 10 cm past the bed's front as its mesh measures (`FootOf`), not its nominal size.
- **Room sizes** come from a stream of their own (small chambers 3-4 tiles, galleries the block's length by 3-4, the largest), so the layout's stream is unchanged; the start section's furniture is saved: run `865` again after a change to the plan (it rebuilds it).
- **The torch's light is measured in pictures**: 640 x 360 `HighResShot`s lit and put out, read with `zlib` (the editor's Python has no image library): 136 against 98.

## The test (`868`)

- Put her on a trap and it goes off before the test reads her hit points: read them first, then put her on it, from a floor point of its own room (4 m east of a trap was inside a wall once).
- A set of rooms still being built is skipped by the traps' tick: wait for `is_building()` to be false, not only for its progress record.
- Sets far from her are dropped and built again as she moves: read the traps' lines again for each trial; which kinds exist depends on the sets generated (the chain and the lingering trap are tier 3's): generate tier 3 sets until all twelve are there.
- `bLogTraps` (the generator) logs what the traps' tick sees once a second (`RDTRAPTICK`).
- The share rule (50 % since 2026-10-27, 75 % before) is checked kill by kill (the debug clear leaving fewer each time, once every planned monster of the start set stands): the tier opens at the first share of 50 % or more, and was shut at the kill before.
- Wardrobes: two doors, two containers, one body: count the body once.

## The reel (815 `mw ... mistward`, `rdm_reel_overlay.py ... mw`)

- **The pilot's scripted-only mode blocks held keys**: the inventory held-key beat turns it off for the hold.
- **`open_chest` fights whatever it sees** on the way, even with the monsters quiet: not while `G["quiet"]`.
- **A disarm can fumble** (15 %, from a stream seeded by the session seed): the render repeats the rehearsal's outcome; pick a seed whose disarm works (the Rogue's 13422).
- **A caged monster next to the prisoner's cell breaks out** as she frees the prisoner: the pilot picks a prisoner with no monster's cell within 6.5 m and a monster's cell 9 m or more away.
- The overlay draws the castle's pictures from `blender_numpy/mw_ui_art.py`'s folder (the painted interface plus `867`'s pictures).
- The frame rate the HUD shows in a render is the render's own tick, not play's (383 FPS in the second reel).
- **The second reel (2026-10-27)**: at 50 % the shortcut opened tier 2 at the first debug clear, in the tick the pilot asked for the encounters, and the guarded ring (put a tick later) was missed: the pilot waits for it. The ring lay in a chest of a 4 x 4 guard room: `mw_near_point`'s sweep went all the way into the chest and refused every stand point (she was left 88 m off): it sweeps to 1.2 m short of it, and tries nearer distances for the castle's small rooms. Read each run's events (`cine_mw_<hero>.json`: at_ring's distance, fights, ring_taken) before the overlays.
