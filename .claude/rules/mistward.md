---
paths:
  - "claude_ue5/Source/claude_ue5/RD/RDMistward*"
  - "claude_ue5/Source/claude_ue5/RD/RDTraps.cpp"
  - "claude_ue5/Source/claude_ue5/RD/RDGear.cpp"
  - "pipeline/unreal/86*.py"
  - "pipeline/unreal/868_mistward_test.ps1"
  - "pipeline/blender_numpy/mw_*.py"
  - "claude_ue5/SourceArt/mistward/**"
---

# mistward_castle (`863`-`868`; the user's list of 2026-10-26, `docs/improvements.txt`)

Level 5's Save As copy with the castle's rules. Every rule is a switch on the generator ("Mistward" category), off on the other levels: level 5 itself must stay as it was. Its test is `868_mistward_test.ps1`; its reel is 815 / 816 / 829 with level `mw` (`mwselect` for the menu) and `rdm_reel_overlay.py ... mw`.

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
- **`RestartPlay` left the extra monsters** (a boss's band, guards, those a teleport trap brought) standing in the kept start set: after a few runs 60 of them, and a debug clear that leaves "the nearest N" kept every planned one. It destroys every monster without a `SpawnIndex` now.
- **A killing blow also wears the shield**: a test's blow of a million broke the Warrior's starting shield before she fell, so it was not among what she kept.
- **Footprints**: a piece's nominal size can be smaller than its mesh (a table's top over a wardrobe's way in): `ARDSection::FootOf` takes the mesh's box where it is bigger, centred where the box is. Pieces still touch by up to 6 cm (3 cm under their sizes on each side, so pieces set by their sizes fit).

## The test (`868`)

- Put her on a trap and it goes off before the test reads her hit points: read them first, then put her on it, from a floor point of its own room (4 m east of a trap was inside a wall once).
- A set of rooms still being built is skipped by the traps' tick: wait for `is_building()` to be false, not only for its progress record.
- Sets far from her are dropped and built again as she moves: read the traps' lines again for each trial; which kinds exist depends on the sets generated (the chain and the lingering trap are tier 3's): generate tier 3 sets until all twelve are there.
- `bLogTraps` (the generator) logs what the traps' tick sees once a second (`RDTRAPTICK`).
- The 75 % rule is checked kill by kill (the debug clear leaving fewer each time): the tier opens at the first share of 75 % or more.
- Wardrobes: two doors, two containers, one body: count the body once.

## The reel (815 `mw ... mistward`, `rdm_reel_overlay.py ... mw`)

- **The pilot's scripted-only mode blocks held keys**: the inventory held-key beat turns it off for the hold.
- **`open_chest` fights whatever it sees** on the way, even with the monsters quiet: not while `G["quiet"]`.
- **A disarm can fumble** (15 %, from a stream seeded by the session seed): the render repeats the rehearsal's outcome; pick a seed whose disarm works (the Rogue's 13422).
- **A caged monster next to the prisoner's cell breaks out** as she frees the prisoner: the pilot picks a prisoner with no monster's cell within 6.5 m and a monster's cell 9 m or more away.
- The overlay draws the castle's pictures from `blender_numpy/mw_ui_art.py`'s folder (the painted interface plus `867`'s pictures).
- The frame rate the HUD shows in a render is the render's own tick, not play's.
