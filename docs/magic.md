# Magic: casters, spell effects and spell sounds

What the asset libraries hold for a mage or spell-caster character and for spell casting. The sources searched:
- the galleries' data (heroes, enemies, monsters, objects);
- the project's imported content;
- the Unreal vault cache in `I:\game assets\3d fab library data cache` (191 packs);
- the sound and 2D libraries in `I:\game assets`.

The search went by asset names. **Nothing on this page has been rendered or played yet.** The effects are listed by their names; whether each one looks like a spell has not been checked.

## Short answer

- **Casters:** yes. The best are the Mystic Dungeon pack's wizards and skeleton mages, which are imported but in no gallery yet. Several characters already in the galleries also fit.
- **Spell effects:** the 3D library has no magic effects pack. A few fire, light, spark and portal effects from environment packs could stand in for spells.
- **Spell sounds:** well covered, with two spell sound libraries.
- **Spell-casting clips:** none for third-person characters. A caster needs a spell animation pack from Fab.

## Humanoid casters

### Mystic Dungeon's character kit (not in the galleries)

[Dungeon Builder: Modular Top Down RPG Environment Kit](https://www.fab.com/listings/10cbf8dd-ef59-48f8-bbea-606a2b66774d) (`MysticDungeon`) comes with a character kit, imported in `Content/MysticDungeon/ModularCharacter`. The kit comes as separate parts rather than whole figures, and the hero and enemy galleries skipped parts packs, so it was missed.

| Caster | Parts |
|---|---|
| Male Wizard | robe (long or short sleeves), two cloaks, two hats, beard, trousers, two pairs of shoes; two colour variants (`MI_Male_Wizard`, `MI_Male_Wizard2`) |
| Elder Wizard | the wizard's outfit on an old man's body (`SK_MaleOldBody`), with a material of its own (`MI_Male_ElderWizard`) |
| Female Wizard | dress (long or short sleeves), belt, trousers, shoes; two colour variants (`MI_Female_Wizard`, `MI_Female_Wizard2`) |
| Skeleton Mage (male and female) | a skeleton body (`SK_Male_Skeleton`, `SK_Female_Skeleton`) with robe, hood, arm and shoulder pieces; the male has a cloak variant. It would make a good enemy caster. The pack also has a skeleton boss Blueprint (`BP_Skeleton_01_Boss`). |

**Animations:**
- All the parts are on one skeleton (`SKEL_Human`, 72 bones) with UE4-mannequin bone names, so the UE4-mannequin clips would carry over, as they did for the other heroes.
- The kit's own 12 clips are idles, a walk and a run, jumps, and four emotes (bow, dance, sit, wave).

**Building a wizard:** each wizard has to be put together from parts. The pack's outfit table (`DT_Equipment_Items`) and its demo character (`BP_AdvancedModularCharacter`) can do that.

### Already in the galleries

| Character | Page | Why it works |
|---|---|---|
| Witch Hunter ([Fantasy Warriors](https://www.fab.com/listings/df8194f9-ec63-49f6-a885-6feb7a94fcb1)) | [heroes.md](heroes.md) | Has her own Witch's Hooked Staff, Spellbook and Flasks. The pack names her `Fantasy_Witch`: she could be a witch rather than a witch hunter. |
| Tiefling Hero ([Fantasy Warriors](https://www.fab.com/listings/df8194f9-ec63-49f6-a885-6feb7a94fcb1)) | [heroes.md](heroes.md) | Already listed as "warlock / duelist". |
| Shaman ([Primitive Characters](https://www.fab.com/listings/3ce14ea2-e944-46b1-afec-e10c50e7fa96)) | [heroes.md](heroes.md) | Deer-skull headdress and robe; comes with the Shaman's Staff. |
| Tribal Elder ([Primitive Characters](https://www.fab.com/listings/3ce14ea2-e944-46b1-afec-e10c50e7fa96)) | [heroes.md](heroes.md) | Listed as "support / sage". |
| Orc Shaman ([14 Orcs Pack](https://www.fab.com/listings/3c224616-e998-433c-910b-32901d426103)) | [humanoid_enemies.md](humanoid_enemies.md) | Hooded, with a totem of skulls; the pack has a Shaman's Totem Staff. |
| Medusa Fiend ([10 Creatures](https://www.fab.com/listings/0094617c-9eba-433a-8a5e-d3e0aba5735b)) | [humanoid_enemies.md](humanoid_enemies.md) | Listed as a "caster" enemy. |
| Squid-Face ([Monsters Underwater Pack](https://www.fab.com/listings/abbee71a-8ed4-4cc9-afe1-fd92b3028683)) | [humanoid_enemies.md](humanoid_enemies.md) | Listed as a "caster" enemy. |
| Antlered Insect ([Creatures Insects Pack](https://www.fab.com/listings/0c0ba07e-09b6-4cc7-bf2b-a7f5f77d7554)) | [humanoid_enemies.md](humanoid_enemies.md) | Listed as a "caster" enemy. |

### Caster props

These are in [objects.md](objects.md):
- **Staffs:** Wizard's Staff (Dark Fantasy Weapons), Witch's Hooked Staff, Shaman's Staff, Shaman's Totem Staff.
- **Clothing:** Wizard's Hat (Mystic Dungeon).
- **Books and potions:** Witch's Spellbook, Leather Book, Book of Eddrick, Witch's Flasks, Potion, Tall Potion.

### The missing piece: spell-casting clips

- The project has no third-person spell or staff clips.
- The only cast clip is FF2's own (`AS_FF2_CastSpell`). Copying it onto another rig laid the body on the floor.
- objects.md lends staffs the spear clips of Spear And Shield Animations, which are thrusts and blocks, not spells.
- A caster will need a spell animation pack from Fab.

## Spell effects

**What the packs hold:** the 3D library's effects are all environmental: fire, candles, smoke, dust, fog, leaves, birds and fireflies. The Unity packages in `I:\game assets\3d epicgames media packs\VaultCache\FabLibrary` were not searched in full: they are mostly the same character packs, and any particle effects in them would work only in Unity.

**Possible stand-ins:** these could pass for spells. None has been watched playing.

| Effect | Pack | Possible use |
|---|---|---|
| `NS_FireEye`, `NS_FireWings`, `NS_FirePool` | [Modular Dungeon](https://www.fab.com/listings/0ff28c1f-790d-4a1b-92be-04617439270b) (`DarkHalls`, imported) | fire spells, a fire aura, a burning ground spell |
| `NS_PassageFX_01`, `NS_LightRayFX_01`, `BP_MagicStone` | [Dungeon Builder](https://www.fab.com/listings/10cbf8dd-ef59-48f8-bbea-606a2b66774d) (`MysticDungeon`, imported) | a glowing passage or portal, a beam of light, a glowing rune stone |
| `NS_TeleportRing` | [Dark Fantasy Weapons](https://www.fab.com/listings/244607ad-e819-4320-bbc7-687b844b5bed) (`Medieval_Weapons`, imported) | a teleport circle. It comes from the pack's VR template and may look like interface graphics. |
| `NS_Electric_Damaged_01a`, `TX_Lightning_01a` | [Meridian 1988: 14 Widow Street](https://www.fab.com/listings/25f80505-7c6c-40a5-a656-69a8b5db3fc5) (`MERIDIAN`, imported) | lightning or shock sparks |
| `NS_sparks` | [Dragon Graveyard Kit](https://www.fab.com/listings/9ee42cda-1455-4539-b5a9-ba6c9682a6dd) (`Dragon_graveyard`, imported) | impact sparks |
| `P_Sparks`, `P_Explosion` | Epic's Starter Content, in [House On A Hill](https://www.fab.com/listings/92f85d39-8e3a-4241-a0d6-e636052b6618) (`Feather`, imported) | fireball hits, impacts |
| `BP_portal_01`–`03` | [Alien Desert Station](https://www.fab.com/listings/22e6a6da-15a4-469d-a661-3c86f70aef7d) (`Red_Echo`, imported) | sci-fi portals |
| magic wolf variants (blue, fel, frost, molten, white) | Wildlands (in the vault cache, not imported) | summoned spirit wolves. The wolves are animated (walk, run, attacks, idles) and have glowing materials of their own. |

### Making spell effects

- **No Niagara from Python:** the project cannot write a Niagara system from Python. Custom spell effects would have to be built by hand in the editor, or made as tuned copies of Cascade effects, as the starship's contrails were (`USSFXLibrary.tune_particle_system`).
- **The practical route:** a magic effects pack from Fab.

## Spell sounds

**Spell sound libraries:** these cover spells far better than the visuals do. All are in `I:\game assets\complete rpg creator bundle`.

| Library | What it has |
|---|---|
| Elemental Spells Vol 1 (Khron Studio, in `monster and magic bundle`) | 200 sounds sorted into dark, fire, ice, lightning, poison, rock, water and wind. Each element has spell, hit, buff and whoosh sounds and an aura loop, plus a few extras (`Dark_Resurrection`, `Fire_Earthquake`, `Ice_conjure`). |
| Spells Variations Vols 1–4 (Khron Studio, `spells variations complete collection 2`) | 1,268 named spell sounds, such as Arc Pulse, Blazing Impact, Celestial Mend, Cyclone Wrath, Ethereal Rejuvenation and Frostveil Aura. |
| Fantasy Magic Weapons Vol 1 (Khron Studio, in `monster and magic bundle`) | 346 sounds for enchanted weapons. |
| Old magician voice pack (The Sound Guild) | a magician's voice lines. |

The Monster & Magic Bundle's monster libraries are already in use in random_dungeoncombat_level (see [assets.md](assets.md)).

## 2D material

These are not 3D, but could help:
- **[Kenney](https://kenney.nl) Particle Pack** (`I:\game assets\kenney-particle-pack-*`): 96 flat sprite textures: flames, flares, lights, sparks, smoke, stars, twirls, slashes, traces, symbols and magic shapes. They could be built into simple spell particles.
- **Spell icons and spellbook interface art:** in `complete rpg creator bundle`:
  - `spells and ability icons_windows`;
  - `fantasy spellbook`;
  - `magic runes pixel art asset pack`;
  - the spell slots and spell book pages of the RPG interface kits.

## Used in the project

`random_dungeonmagic_level` and `random_dungeonmagic_level2` (see [levels/magic_levels_1-3.md](levels/magic_levels_1-3.md)) have a fire spell built from this page.
- **Bolt:** `NS_FirePool`.
- **Burst:** `P_Explosion` with `NS_FireWings`.
- **Charge on her hand:** `P_Sparks`.
- **Sounds:** from Elemental Spells Vol 1.
- **Warm copies:** the DarkHalls systems are used in copies that start warm.

Tried and left out:
- **`NS_FireEye`:** at the dungeon's exposure it is only a few embers.
- **Sprite sizes:** `NS_FirePool`'s sprites do not shrink with the component's scale, so the bolt stays about a metre across.

The casts, and the dark caster's sword cuts, were made for the two Tripo characters in Blender (`pipeline/blender_numpy/caster_clips.py`, `darkcaster_clips.py`). A spell animation pack is still missing for the Fab characters.

## Next steps

- Add the Mystic Dungeon wizards and skeleton mages to [heroes.md](heroes.md) and [humanoid_enemies.md](humanoid_enemies.md), with pictures.
- Render the candidate effects, to see which ones actually look like spells.
- Get a spell animation pack and a magic effects pack from Fab. Acquiring Fab content needs you in the Epic Games Launcher.
