# Showcase reels and stills

[README](../README.md) · [Levels](../README.md#levels) · [Documentation](../README.md#documentation)

What each level's reels show is listed under **Demo reels** in [capabilities.md](capabilities.md); each level's own reel steps are in its rebuild notes.

## Making a reel

Most levels have a `*_Cine` copy (`MoviePipelineGameMode` with an AI demo character) for their `LS_*_Showcase` sequence; the JRPG characters use the meadow's. `starship_level`, `random_dungeoncombat_level` and the magic levels have none: their reels are rendered on the level itself, a pilot script playing the game through its own inputs while the Movie Render Queue renders the player's view. `L_Fig4_Studio` (stills) and `fantasy_castle_level` have no reel.

**Showcase videos:**
- Build the sequence with the level's `*_sequence.py`.
- Render with `75_render_locomotion.py <out_dir> preview|final <level> <sequence> <prefix>`.
- Encode with `pipeline/blender_numpy/encode_video.py <frames_dir> <out.mp4> 36 30`. The `36` drops the warm-up frames (the procedural levels' reels encode from 0).
- Every reel is kept in two sizes in `renders/`: `<Name>_Showcase.mp4` (1080p, CRF 16) and `<Name>_Showcase_20MB.mp4`, a two-pass encode at a fixed video bitrate: `encode_video.py <frames_dir> <out.mp4> <start> 30 <track.wav or -> <video_kbps>` (45 s at 3300 kbps with a 128 kbps sound track is about 18.5 MB).
- The reels so far: fig4 locomotion, Meshy biped, Dystopia soldier, FF, FF2, castle interiors and furnishing, JRPG Fem5 in the meadow, the sci-fi city, random_level, random_dungeon_level, random_isometric_village_level, the starship fighter, three of random_dungeoncombat_level (combat; blood, wounds and sound; music), random_dungeonmagic_level (the caster), random_dungeonmagic_level2 (the dark caster, fire and sword), random_dungeonmagic_level3 (the Rogue: daggers, crossbow and roll), random_dungeonmagic_level4 (the choice of hero, 3 min: each of the four chosen in the menu, then her run: containers, her inventory, a fight in her own style, a section generated; and again with the painted interface, 3 min, the same runs with the generated boards, bars, plates and pictures; and with the game's lettering, Cinzel, Alegreya and Alegreya SC), random_dungeonmagic_level5 (the Summoner's face, 30 s: eight expressions in close shots, with her retargeted casts, flinch and fall; and again with her MetaHuman face, 30 s: eleven expressions written from FACS action units; and the Summoner's armour, about 100 s: chosen in the five-hero menu, she opens the great hall's chests and puts on the five sets in turn with the camera going round her, then takes a monster's blows in plate; the weapons table and the tiers, 127 s: the Warrior with the found weapons, one that breaks, and tier 3 opening; the four heroes and the weapons table, 4 min: each picked in the menu, what she may wield and what she is refused; and again with armour by weight, about 4.5 min: the Warrior in plate, the Warlock and the Rogue in light armour and refused the heavy, the Mage refused any), mistward_castle (the four heroes in the castle, 4:38: shields, the torch, traps, prisoners, teleporters, a boss, a guarded ring, rooms of other shapes, her things where she falls), the Tripo trio showcase (turntables and fights of the three Tripo characters, 60 s) and the Tripo quartet showcase (the four, with the Rogue's roll, crossbow and daggers, 78 s).

## The Tripo trio and quartet showcases

**Tripo trio showcase** (`660`–`662`; after the three characters, `790`, `810` and `817`): `660_tripo_trio_stage.py` builds `L_Tripo_Trio_Showcase` (the photo studio's cyclorama and lacquer plinth, a light rig, fixed exposure) and `LS_Tripo_Trio_Showcase` (60 s: the three together, then for each a turntable on the plinth and a fight: Fem5's sword, spear and axe on a troll; the caster's six casts at a mutant; the dark caster's two casts at a daemon that walks up to her and falls to her sword; the three again). Characters and monsters are skeletal mesh actors on the sequence's animation tracks (sections blended over 0.12 s), the weapons static mesh actors on their hands with the grips of `790` / `817`; the blow and release times are the measured ones. The fire is spawned by `661_tripo_trio_pilot.py` at the times of `SourceArt/tripo_trio/plan.json` while `662_tripo_trio_render.py <out_dir> preview|final` renders. Titles, captions and the music with `pipeline/blender_numpy/trio_showcase_overlay.py <frames> <out_dir> [music.wav track.wav]`, then `encode_video.py`.

**Tripo quartet showcase** (`663`, with `661` / `662`; after the trio's and `822`): `663_tripo_quartet_stage.py` builds `L_Tripo_Quartet_Showcase` and `LS_Tripo_Quartet_Showcase` (78 s): the trio's three segments as before, then the Rogue's: a turntable with the daggers in her hands and the crossbow on her back, then a horned beast swings at her, she rolls back out of the blow (her roll clip while the sequence carries her `RollDistance` over 0.82 of it, as the game does), draws the crossbow and puts two bolts in it, draws the daggers as it comes on and kills it with three strikes; the four again at the end. The weapons she does not hold hang where the game carries them (`822`'s holsters); the next bolt lies on the crossbow until the release and again after the reload. Two bolt actors placed by `663` are flown by the pilot from the crossbow's muzzle to the beast at the crossbow's speed, with the level's bolt trail, and the pack's impact where they land. Render: `661_tripo_trio_pilot.py render quartet`, then `662_tripo_trio_render.py <out_dir> preview|final quartet quartet`; overlay: `trio_showcase_overlay.py quartet <frames> <out_dir> [music.wav track.wav]`. The Warlock's and the Rogue's close shots look from the left of the pair, into the backdrop (the trio's saw past its left edge).

## Early results

Stills from the showcase videos: 1080p Movie Render Queue renders of each level's `*_Cine` copy, with the demo character running its recorded route.

**FF — Tripo anime female** (`ff_level`). A static GLB rigged onto a UE4-mannequin skeleton, with locomotion retargeted from the template.

| Idle | Run | Close-up |
|---|---|---|
| ![FF idle](images/ff_idle.jpg) | ![FF run](images/ff_run.jpg) | ![FF close-up](images/ff_front.jpg) |

**FF2 — animated Tripo anime female** (`ff2_level`). Her own clips, grounded on the sole contacts so she doesn't float or slide.

| Jump | Boxing | Casting |
|---|---|---|
| ![FF2 jump](images/ff2_jump.jpg) | ![FF2 boxing](images/ff2_box.jpg) | ![FF2 casting](images/ff2_spell.jpg) |

**Dystopia Soldier 02** (`soldier_level`). Converted from a Unity-format Fab pack, with per-part PBR materials and retargeted locomotion.

| Idle | Flamethrower | Close-up |
|---|---|---|
| ![Soldier idle](images/soldier_idle.jpg) | ![Soldier flamethrower](images/soldier_flamethrower.jpg) | ![Soldier close-up](images/soldier_front.jpg) |
