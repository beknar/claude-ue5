# Emotional content: faces that move during play

The question: can the characters' faces show expression during actions in the game, such as a grimace on a swing, a wince when hit, a roar when a monster spots her, or pain on death? This page records what the models can do now and every way found to add expressions. It also covers where the expressions would be seen and how they would be tested.

**What was built since** (random_dungeonmagic_level5, the Summoner; its [rebuild notes](levels/random_dungeonmagic_level5.md#rebuild)):
- way 7 first: shapes made in Blender and patches painted on her texture, eight expressions (`832`-`836`);
- then way 9, which replaced it in play: a MetaHuman face (Epic's preset Aera in her colouring, rigged by Epic's cloud service) set on her body under her own hair, her painted face cut away by her material, sixteen expressions written as MetaHuman control curves from FACS action units, moved by RigLogic (`837`-`841`). It is heavy (858 blend shapes, strand brows and lashes) and stays a different style from her anime body: a realistic face under anime hair. Fitting the MetaHuman to her anime head (Mesh to MetaHuman) gave a grotesque, so the face is a preset.

When this page was written nothing on it was built. The rig facts and the jaw angles were measured with read-only probes:
- the hero `.glb` files were read directly;
- the imported meshes and clips were read in the editor with `AnimPoseExtensions` and `get_all_morph_target_names`.

The results of the transfers and texture patches described below are expectations that no render has checked yet.

## Short answer

- **Monsters:** the Troll and the Ripper dog already move their jaws in their clips. Each monster kind also has a roar clip (`Anim_<Kind>_Shout`) that the game never plays. That is the cheapest visible gain.
- **Heroes** (Warrior, Mage, Warlock, Rogue): their faces have no rig at all. They are painted on the texture of one mesh with one `head` bone. An expression has to be built for them first, as shapes, as texture patches, or both.
- **MysticDungeon's modular humans** have a full face rig of 144 morph targets. They ship no face animation, and Unreal's retargeter cannot carry morph targets to another mesh. The shapes could be transferred to the heroes in Blender: the ones that slide the skin would work, but blinks and an open mouth would not.

## What the models have

| Models | Face rig | Measured |
|---|---|---|
| Heroes: `Warrior.glb` / `SK_JRPG_Fem5`, `Mage.glb` / `SK_JRPG_Caster`, `Warlock.glb` / `SK_JRPG_DarkCaster`, `Rogue.glb` / `SK_JRPG_Rogue` | None | One mesh, one texture, 0 morph targets, a single `head` bone. The Warlock's other bones are her hair chains. The eyes, brows and mouth are painted. 3,086 to 4,417 vertices are weighted mostly to the head, hair included. |
| Troll (`SK_Troll`) | Jaw (`Bind_Jaw1`, `Bind_Jaw2`) and eyes | The jaw turns in every clip (table below). |
| Ripper dog (`SK_Ripper_dog`) | Jaw (`Jaw1_M`), eyes, ears | The jaw turns in every clip (table below). |
| Daemon, Horned, Spider | Eye bones only | No jaw |
| Mutant | `Bind_Head` only | No jaw |
| MysticDungeon modular humans (`SK_Female_Body`, `SK_Female_Body02`, `SK_Male_Body`, `SK_Male_Body02`, `SK_MaleOldBody`; skeleton `SKEL_Human`) | 144 morph targets and 4 face bones (`FaceJoint_M`, `EyeJoint_L`/`_R`, `unrealJaw_M`) | See "MysticDungeon's face rig" below. |
| fig4 (the MetaHuman, `L_Fig4_Studio`) | The full MetaHuman face rig | Not used in any game level. |

How far the jaw turns in each monster clip, in degrees, sampled at 31 frames per clip:

| Clip | Troll: from rest | Troll: within the clip | Ripper dog: from rest | Ripper dog: within the clip |
|---|---|---|---|---|
| Attack (the largest of its attacks) | 21.5 | 13.7 | 39.2 | 39.2 |
| GetHit | 18.5 | 16.0 | 18.5 | 18.5 |
| Death | 13.2 | 10.1 | 24.2 | 24.2 |
| Shout (never played) | 19.9 | 16.1 | 43.2 | 43.2 |
| Idle | 6.9 | 6.9 | 9.0 | 9.0 |
| Walk | 6.4 | 10.6 | 5.5 | 5.5 |

The monsters play their clips in single-node mode (`RDMonster.cpp`: `PlayAnimation` for the idle, walk, attacks, get-hit and death). `ARDMonster::Roar()` (`RDMonster.cpp:495`) only plays the `Monster.<Kind>.Roar` sound.

## MysticDungeon's face rig

The kit is in `Content/MysticDungeon/ModularCharacter` ([Fab listing](https://www.fab.com/listings/10cbf8dd-ef59-48f8-bbea-606a2b66774d)). Every body mesh carries the same 144 morph targets:

- **The ARKit set** (52 names, the iPhone face-tracking standard): `eyeBlinkLeft`, `eyeSquintLeft`, `eyeWideLeft`, `eyeLook*`, `jawOpen`, `jawForward`, `mouthSmileLeft`, `mouthFrownLeft`, `mouthPucker`, `mouthFunnel`, `browInnerUp`, `browDownLeft`, `browOuterUpLeft`, `cheekPuff`, `cheekSquintLeft`, `noseSneerLeft`...
- **Mouth shapes for speech** (15): `aaa_M`, `eh_M`, `ahh_M`, `ohh_M`, `uuu_M`, `iee_M`, `rrr_M`, `www_M`, `sss_M`, `fff_M`, `tth_M`, `mbp_M`, `ssh_M`, `schwa_M`, `gk_M`, `lntd_M`.
- **Whole emotions on one dial each** (7): `happy_M`, `angry_M`, `sad_M`, `surprise_M`, `fear_M`, `disgust_M`, `contempt_M`.
- **Finer controls:** brows (`brow_innerRaiser_R`...), eyes (`blink_R`, `squint_R`, `ctrlEyetranslate*`), cheeks, nose, and many mouth controls (`mouth_upperPressIn_M`, `mouth_jawSideOut_M`...).

The kit has no face animation:
- its 12 clips (idles, walk, run, jumps, and the bow, dance, sit and wave emotes) carry no face curves;
- its demo sets the morph targets live from widgets: `WBP_FacialRigControl`, `WBP_FacialRigPresets` with the `Enum_FacialExpressionPreset` enum, `WBP_ManualFaceControlEyes` / `EyeBrows` / `Mouth`, and `WBP_LipSyncPanel`.

## The ways to do it

### 1. Monsters roar with their own clip

Play `Anim_<Kind>_Shout` when a monster first sees her (in `Roar()`, beside its sound), the way the get-hit and attack clips are already played.

- **Troll and Ripper dog:** a visible open-mouthed roar. Their shout opens the jaw 20 and 43 degrees.
- **The others:** a roar of the head and body without a jaw.
- **Cost:** a small C++ change, plus `RDMonsterDef` and `791` taking a `Shout` clip as they take `GetHit` and `Death`. Fight timing has to allow for it: a 3.3 to 4.7 s roar is a long pause before the charge, so it may need cutting short or blending out early.

### 2. More monster jaw on top of the clips

Turn the jaw bone further from code on events: a wider gape when hurt, the jaw hanging open on death.
- **How:** the monsters use single-node animation, so this needs a small AnimBP (a "Transform (Modify) Bone" node on the jaw, its alpha set from C++) or a post-process AnimBP on the mesh.
- **Who it works for:** only the two monsters with jaws.

### 3. Monster eyes

The Daemon, Horned, Spider, Troll and Ripper dog have eye bones. Scaling or turning them (wide eyes on the charge, eyes tracking her) is possible in the same AnimBP.
- **Not checked:** whether their eyes are separate geometry that moves with those bones or part of the head's surface.
- **A glow on the eyes** (anger) would need the eye area in the material: a mask on the texture, also unchecked.

### 4. Hero shapes made in Blender

Add shape keys to each Tripo mesh in Blender: brow furrow, brow raise, squint or wince, cheek raise, sneer, mouth corners down for a grimace.
- **Moving the painted features:** moving the brow vertices moves the painted brow with them.
- **The hero's clips can carry the expression:**
  - the strike, cast and roll clips are already made in Blender (`caster_clips.py`, `darkcaster_clips.py`, and `rogue_clips.py` with the roll);
  - those scripts could key a grimace on the strike or a wince on the roll;
  - Unreal imports shape-key animation as curves that drive the morph targets of the same name, so it would play with the clip without game code.
- **The risk:** the eyes are painted. A blink made by pulling the upper face down would stretch the painted eye, not close it. Use way 6 for blinks.

### 5. MysticDungeon's shapes transferred to the heroes

The same result as way 4, but the shapes are taken from MysticDungeon's sculpted set instead of made by hand. The steps:
1. Export one MysticDungeon body with its morph targets as FBX, to a scratch folder.
2. In Blender, line its face up with the hero's using landmarks: eye corners, mouth corners, nose tip and chin. The hero's are painted features, so their positions come from the texture.
3. Bind the hero's face to it (a Surface Deform style transfer) and copy each shape key across under the same ARKit name.
4. Re-import the hero with the new shape keys.

How each kind of shape would come out:

| Shapes | Expected result | Why |
|---|---|---|
| `browDown*`, `browInnerUp`, `browOuterUp*`, `eyeSquint*`, `cheekSquint*`, `noseSneer*`, `mouthSmile*`, `mouthFrown*`, `mouthStretch*`, `mouthPress*`; `angry_M`, `sad_M`, `fear_M`, `disgust_M` | Good | They slide the skin, and the painted features move with it. |
| `eyeBlink*`, `eyeWide*`, `eyeLook*`, `blink_*` | Poor | MysticDungeon closes lids over modelled eyeballs. The heroes' eyes are paint on the surface, so a blink stretches the painting. |
| `jawOpen`, the speech shapes, `surprise_M`, a shout | Poor | The heroes have no inside to the mouth: opening it stretches the lips or opens a gap onto nothing. |

Other limits:
- **Proportions:** the heroes have stylised large-eyed faces and MysticDungeon's are realistic. Without a careful landmark warp, the shapes land in slightly the wrong places.
- **Density:** 3,000 to 4,400 head vertices, hair included, carry broad expressions but not fine mouth shapes.
- **What the shared names allow:** once the heroes carry the ARKit names, any ARKit-style source could drive them. The ones that come to mind are a Live Link Face recording made on an iPhone, or Unreal's audio-driven face animation. Neither has been tried here.

### 6. Painted face patches in the texture

Paint the face area again as variants (eyes shut, eyes screwed up in pain, a grimace, an open shouting mouth) and let the material blend a patch in.
- **What this does best:** blinks and an open mouth, which the mesh cannot do.
- **How:** a face mask in the texture's UV space, and a scalar parameter per patch, set from C++ (`SetScalarParameterValueOnMaterials`) or by material curves keyed in the clips.
- **Painting:** the variants could be painted by the InvokeAI server from the existing face. The interface art's lessons apply (positive prompts only, check each sheet by eye). Using a Fab pack's pictures as references is not allowed (see `CLAUDE.md`).
- **Limit:** a patch changes the picture, not the shape, so it looks flat when the face turns past three-quarters.

### 7. Ways 4 to 6 together

Use shapes for the brows, cheeks and mouth corners (way 4 or 5) and patches for the eyes and the open mouth (way 6). That gives the full range: a wince on a hit, a grimace on a strike or a cast, anger in a fight, eyes shut in pain, a cry and a death face.

### 8. Swap the heroes onto MysticDungeon's bodies

Build the heroes from MysticDungeon's parts, whose face rig works as made.
- **Cost:** replaces the project's own characters (the Tripo models and their clips, grips, hair and tests). Far more work, and the heroes would no longer be the project's own CC BY models.
- **A better use of the kit:** humanoid enemies or townsfolk, if any are added. The kit's parts are already on one skeleton with UE4-mannequin bone names.

### 9. MetaHuman faces

A MetaHuman has the richest face rig (fig4 has one), but it is far too heavy for four dungeon heroes and would replace the characters too. It is listed only for completeness.

## When the expressions play

| Occasion | Hero | Monster |
|---|---|---|
| Idle | random blinks (way 6), a calm resting face | idle clip (the jaw moves 7 to 9 degrees already) |
| Spotting her / start of a fight | brows down, `angry_M` up | the roar (way 1) |
| Swing or strike | grimace, keyed in the strike clip | attack clip (the jaw moves already) |
| Spell cast | brows down, eyes narrowed, keyed in the cast clip | none |
| Roll | wince, keyed in the roll clip | none |
| Hit | wince, eyes screwed shut, with her cry (`Player.Hurt`) | get-hit clip, a wider gape (way 2) |
| Low health | `fear_M` / `sad_M` held up a little | none |
| Death | eyes shut, mouth slack | death clip, jaw hanging (way 2) |
| Picking up loot, opening a chest | a short `happy_M` | none |

**Who sets them:**
- **Clip-borne** expressions (strike, cast, roll) need no game code.
- **Event-driven** ones (hit, low health, death, loot, the start of a fight) would be set in `URDCombatComponent` and `ARDMonster`. They would fade in and out over a tenth of a second or so rather than switch.
- **Random blinks** need a timer of their own. Like sound and blood, they must draw from a random stream of their own, never from the play's, or a reel stops repeating.

## Where they would be seen

The camera follows her from behind, so her face is mostly out of view in play. That is reasoned from the camera set-up, not measured.

Her expressions would show in:
- the hero-selection menu of random_dungeonmagic_level4;
- the demo reels' close shots;
- any portrait added to the HUD.

The monsters face the camera as they charge her, which makes the monster roar (way 1) the most visible gain for its cost.

## How it would be tested

Following the project's rule that a test measures the thing itself:
- **Driving:** a step in the level's scripted test triggers each occasion (a strike, a hit, a roll, a death, a monster spotting her). It reads that the morph targets or material parameters reach their values and fall back.
- **Moving vertices:** a morph's weight says nothing about whether the face moved. The test also skins a few face vertices on the CPU (as the wounds do with `GetSkinnedVertexPosition`) and measures their movement.
- **The monster roar:** measured as the jaw angle during the shout.
- **Looks:** judged in close renders at the level's own exposure, especially:
  - transferred blinks and mouth shapes (way 5);
  - patch seams (way 6).

## Licence

The MysticDungeon shapes are part of a Fab pack.
- Anything derived from them (shapes transferred onto the heroes, way 5) stays in `Content/`, which is not committed. It never goes into `ai models/*.glb`: those files are public under CC BY.
- Shapes made by hand in Blender (way 4) and patches painted by the project's own image server (way 6) carry no such limit.

## Suggested order

1. The monster roar (way 1): small, and the most visible.
2. One hero, one blink and one grimace, made both ways (shapes, way 4 or 5; and patches, way 6), compared in a close render.
3. The winning way on all four heroes, the occasions table wired up, and the test step added.
4. If wanted: the monster jaw and eye extras (ways 2 and 3).
