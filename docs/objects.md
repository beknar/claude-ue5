# Weapons and items of the Fab library

The weapons and the handheld or wearable items in the local Fab library cache (`I:\game assets\3d epicgames media packs\VaultCache\FabLibrary` and the environment packs downloaded through it), in four parts: fantasy weapons, modern weapons, futuristic weapons and non-weapon items. All 231 are in this project. Each is shown three times, rendered in Unreal Engine:

- **side view:** its broad face, level (or from above if it lies flat);
- **three-quarter view;**
- a **frame of its own clip** for the 21 that have one (a gun's reload or shot, a can's lid, a syringe's plunger), or the **far three-quarter view** for the rest.

## About the pictures and notes

- **Sizes:** each entry gives the object's three extents in centimetres, from its bounds; every picture is framed to fill, from a 2 cm coin to a 1.5 m flamethrower.
- **Kept together:** the flamethrower (gun, hose, tank) and the riot shield with its club are several meshes, shown as they sit in their packs.
- **Variants:** many packs have several versions of a weapon (silencers, sights, paint, the ten knives of the FPS Starter Pack, eight pistols and revolvers in `Safehouse`); one of each kind is shown.
- **Animations:** each entry says what clips the object has of its own, which first-person arm clips were made for it (the FPS packs: arms only, a camera rig's), and which third-person animation sets in the project hold that kind of weapon on a UE4-mannequin character (see [heroes.md](heroes.md#animations) for those sets). Bows, crossbows, staves, knives and grenades have no third-person clips here.
- **Uses:** a use is a suggestion from the object's looks.

The list is `claude_ue5/SourceArt/object_gallery/objects.json`; the pictures come from `pipeline/unreal/904_object_gallery.py` and `pipeline/blender_numpy/object_doc.py`, the sizes and animation notes from `pipeline/unreal/902_character_animations.py`. The sellers and listings of the packs are in [assets.md](assets.md).

## Contents

- [Fantasy weapons](#fantasy-weapons) (89)
  - [Swords and daggers](#swords-and-daggers) (19)
  - [Axes, hammers, maces and clubs](#axes-hammers-maces-and-clubs) (33)
  - [Spears and polearms](#spears-and-polearms) (10)
  - [Primitive weapons](#primitive-weapons) (6)
  - [Bows, crossbows and staves](#bows-crossbows-and-staves) (7)
  - [Shields](#shields) (14)
- [Modern weapons](#modern-weapons) (44)
  - [Rifles, machine guns and shotguns](#rifles-machine-guns-and-shotguns) (13)
  - [Sniper rifles and launchers](#sniper-rifles-and-launchers) (5)
  - [Pistols and revolvers](#pistols-and-revolvers) (7)
  - [Knives, melee weapons and grenades](#knives-melee-weapons-and-grenades) (19)
- [Futuristic weapons](#futuristic-weapons) (23)
  - [Energy and sci-fi guns](#energy-and-sci-fi-guns) (13)
  - [Energy blades and shields](#energy-blades-and-shields) (10)
- [Non-weapon items](#non-weapon-items) (75)
  - [Food and drink](#food-and-drink) (21)
  - [Potions and medicine](#potions-and-medicine) (9)
  - [Tools and devices](#tools-and-devices) (20)
  - [Treasure, keys and books](#treasure-keys-and-books) (15)
  - [Helmets and masks](#helmets-and-masks) (10)
- [Not included](#not-included)

## Fantasy weapons

Swords, axes, maces, polearms, bows and shields of medieval and fantasy packs: knights, Vikings, samurai, orcs, dwarves, demons and cavemen.

### Swords and daggers

#### Arming Sword

[Dark Fantasy Weapons](https://www.fab.com/listings/244607ad-e819-4320-bbc7-687b844b5bed) · **Use:** one-handed sword · model `SM_Sword_1` · 88 × 18 × 4 cm

A dark, ornate sword with a winged crossguard and a pommel spike.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves); the two-handed ones by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/medieval_weapons_arming_sword_side.jpg" width="280" alt="Arming Sword, side view"> <img src="images/objects/medieval_weapons_arming_sword_quarter.jpg" width="280" alt="Arming Sword, three-quarter view"> <img src="images/objects/medieval_weapons_arming_sword_third.jpg" width="280" alt="Arming Sword, far three-quarter view">

#### Broadsword

[Dark Fantasy Weapons](https://www.fab.com/listings/244607ad-e819-4320-bbc7-687b844b5bed) · **Use:** boss sword · model `SM_Sword_2` · 84 × 22 × 4 cm

A black, jagged blade sprouting spikes from its guard: an evil-looking greatsword.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves); the two-handed ones by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/medieval_weapons_broadsword_side.jpg" width="280" alt="Broadsword, side view"> <img src="images/objects/medieval_weapons_broadsword_quarter.jpg" width="280" alt="Broadsword, three-quarter view"> <img src="images/objects/medieval_weapons_broadsword_third.jpg" width="280" alt="Broadsword, far three-quarter view">

#### Longsword

[Dark Fantasy Weapons](https://www.fab.com/listings/244607ad-e819-4320-bbc7-687b844b5bed) · **Use:** one-handed sword · model `SM_Sword_3` · 93 × 23 × 3 cm

A long bronze-tinted blade with a plain cross guard.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves); the two-handed ones by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/medieval_weapons_longsword_side.jpg" width="280" alt="Longsword, side view"> <img src="images/objects/medieval_weapons_longsword_quarter.jpg" width="280" alt="Longsword, three-quarter view"> <img src="images/objects/medieval_weapons_longsword_third.jpg" width="280" alt="Longsword, far three-quarter view">

#### Dagger

[Dark Fantasy Weapons](https://www.fab.com/listings/244607ad-e819-4320-bbc7-687b844b5bed) · **Use:** dagger · model `SM_Dagger` · 34 × 6 × 2 cm

A narrow dagger with a spiked guard and a wrapped grip.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** No third-person knife clips in the project; the first-person ones are in FPS Pistol And Knife, the FPS Starter Pack and Sci-Fi Hands With Knife.

<img src="images/objects/medieval_weapons_dagger_side.jpg" width="280" alt="Dagger, side view"> <img src="images/objects/medieval_weapons_dagger_quarter.jpg" width="280" alt="Dagger, three-quarter view"> <img src="images/objects/medieval_weapons_dagger_third.jpg" width="280" alt="Dagger, far three-quarter view">

#### Templar Sword

[Knights (Pack)](https://www.fab.com/listings/6907d3d8-d0db-43c0-bf9c-8ad43c70e7b3) · **Use:** knight's sword · model `SM_Knight_01_Sword` · 109 × 23 × 5 cm

A long plain arming sword with a down-curved guard.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves); the two-handed ones by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/knights_pack_templar_sword_side.jpg" width="280" alt="Templar Sword, side view"> <img src="images/objects/knights_pack_templar_sword_quarter.jpg" width="280" alt="Templar Sword, three-quarter view"> <img src="images/objects/knights_pack_templar_sword_third.jpg" width="280" alt="Templar Sword, far three-quarter view">

#### Eastern Sabre

[Knights (Pack)](https://www.fab.com/listings/6907d3d8-d0db-43c0-bf9c-8ad43c70e7b3) · **Use:** sabre · model `SM_Knight_02_Sword` · 115 × 24 × 5 cm

A long, deeply curved sabre.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves); the two-handed ones by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/knights_pack_eastern_sabre_side.jpg" width="280" alt="Eastern Sabre, side view"> <img src="images/objects/knights_pack_eastern_sabre_quarter.jpg" width="280" alt="Eastern Sabre, three-quarter view"> <img src="images/objects/knights_pack_eastern_sabre_third.jpg" width="280" alt="Eastern Sabre, far three-quarter view">

#### Plate Knight's Sword

[Knights (Pack)](https://www.fab.com/listings/6907d3d8-d0db-43c0-bf9c-8ad43c70e7b3) · **Use:** two-handed sword · model `SM_Knight_03_Sword` · 141 × 28 × 7 cm

A flamberge: a long twisted blade with a ringed guard.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves); the two-handed ones by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/knights_pack_plate_knight_s_sword_side.jpg" width="280" alt="Plate Knight's Sword, side view"> <img src="images/objects/knights_pack_plate_knight_s_sword_quarter.jpg" width="280" alt="Plate Knight's Sword, three-quarter view"> <img src="images/objects/knights_pack_plate_knight_s_sword_third.jpg" width="280" alt="Plate Knight's Sword, far three-quarter view">

#### Paladin's Sword

[Knights (Pack)](https://www.fab.com/listings/6907d3d8-d0db-43c0-bf9c-8ad43c70e7b3) · **Use:** two-handed sword · model `SM_Knight_05_Sword` · 159 × 24 × 4 cm

A gilded, forked blade over an ornate silver guard.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves); the two-handed ones by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/knights_pack_paladin_s_sword_side.jpg" width="280" alt="Paladin's Sword, side view"> <img src="images/objects/knights_pack_paladin_s_sword_quarter.jpg" width="280" alt="Paladin's Sword, three-quarter view"> <img src="images/objects/knights_pack_paladin_s_sword_third.jpg" width="280" alt="Paladin's Sword, far three-quarter view">

#### Dark Knight's Sword

[Fantasy Warriors (Pack)](https://www.fab.com/listings/df8194f9-ec63-49f6-a885-6feb7a94fcb1) · **Use:** two-handed sword · model `SM_Dark_Knight_02_Sword` · 158 × 32 × 13 cm

A long steel greatsword with curled quillons.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves); the two-handed ones by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/warriors_pack_dark_knight_s_sword_side.jpg" width="280" alt="Dark Knight's Sword, side view"> <img src="images/objects/warriors_pack_dark_knight_s_sword_quarter.jpg" width="280" alt="Dark Knight's Sword, three-quarter view"> <img src="images/objects/warriors_pack_dark_knight_s_sword_third.jpg" width="280" alt="Dark Knight's Sword, far three-quarter view">

#### Demonic Blade

[Fantasy Warriors (Pack)](https://www.fab.com/listings/df8194f9-ec63-49f6-a885-6feb7a94fcb1) · **Use:** boss sword · model `SM_Demonic_Warrior_Sword` · 148 × 32 × 6 cm

A huge cleaver-like blade covered in glowing runes.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves); the two-handed ones by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/warriors_pack_demonic_blade_side.jpg" width="280" alt="Demonic Blade, side view"> <img src="images/objects/warriors_pack_demonic_blade_quarter.jpg" width="280" alt="Demonic Blade, three-quarter view"> <img src="images/objects/warriors_pack_demonic_blade_third.jpg" width="280" alt="Demonic Blade, far three-quarter view">

#### Katana

[SAMURAI](https://www.fab.com/listings/5f4c90b7-a282-45fc-89df-61468afc867b) · **Use:** katana · model `SM_Samurai_Sword_01` · 133 × 12 × 11 cm

A curved katana with a red-wrapped grip.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves); the two-handed ones by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/samurai_katana_side.jpg" width="280" alt="Katana, side view"> <img src="images/objects/samurai_katana_quarter.jpg" width="280" alt="Katana, three-quarter view"> <img src="images/objects/samurai_katana_third.jpg" width="280" alt="Katana, far three-quarter view">

#### Wakizashi

[SAMURAI](https://www.fab.com/listings/5f4c90b7-a282-45fc-89df-61468afc867b) · **Use:** short sword · model `SM_Samurai_Sword_02` · 102 × 11 × 11 cm

The katana's shorter companion.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** No third-person knife clips in the project; the first-person ones are in FPS Pistol And Knife, the FPS Starter Pack and Sci-Fi Hands With Knife.

<img src="images/objects/samurai_wakizashi_side.jpg" width="280" alt="Wakizashi, side view"> <img src="images/objects/samurai_wakizashi_quarter.jpg" width="280" alt="Wakizashi, three-quarter view"> <img src="images/objects/samurai_wakizashi_third.jpg" width="280" alt="Wakizashi, far three-quarter view">

#### Viking Sword

[Viking (Customized)](https://www.fab.com/listings/e814c3a3-11ba-4316-a07a-b0980fd016ef) · **Use:** one-handed sword · model `SM_Viking_Sword_01` · 109 × 29 × 4 cm

A plain Viking sword with a brass guard.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves); the two-handed ones by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/vikings_viking_sword_side.jpg" width="280" alt="Viking Sword, side view"> <img src="images/objects/vikings_viking_sword_quarter.jpg" width="280" alt="Viking Sword, three-quarter view"> <img src="images/objects/vikings_viking_sword_third.jpg" width="280" alt="Viking Sword, far three-quarter view">

#### Viking Shortsword

[Viking (Customized)](https://www.fab.com/listings/e814c3a3-11ba-4316-a07a-b0980fd016ef) · **Use:** short sword · model `SM_Viking_Knife_01` · 66 × 15 × 4 cm

A narrow blade with a knobbed, ringed hilt.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves); the two-handed ones by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/vikings_viking_seax_side.jpg" width="280" alt="Viking Shortsword, side view"> <img src="images/objects/vikings_viking_seax_quarter.jpg" width="280" alt="Viking Shortsword, three-quarter view"> <img src="images/objects/vikings_viking_seax_third.jpg" width="280" alt="Viking Shortsword, far three-quarter view">

#### Veteran's Sword

[Fantasy Characters (Pack)](https://www.fab.com/listings/f5816915-86d9-4bef-b8f3-921408ae240b) · **Use:** one-handed sword · model `SM_Sword` · 146 × 27 × 4 cm

A long, worn arming sword.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves); the two-handed ones by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/fantasy_pack_veteran_s_sword_side.jpg" width="280" alt="Veteran's Sword, side view"> <img src="images/objects/fantasy_pack_veteran_s_sword_quarter.jpg" width="280" alt="Veteran's Sword, three-quarter view"> <img src="images/objects/fantasy_pack_veteran_s_sword_third.jpg" width="280" alt="Veteran's Sword, far three-quarter view">

#### Orc Cleaver

[14 Orcs Pack](https://www.fab.com/listings/3c224616-e998-433c-910b-32901d426103) · **Use:** orc blade · model `SM_Gira_Sword` · 110 × 9 × 3 cm

A crude curved blade with a rope-wrapped grip.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves); the two-handed ones by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/orcs_pack_orc_cleaver_side.jpg" width="280" alt="Orc Cleaver, side view"> <img src="images/objects/orcs_pack_orc_cleaver_quarter.jpg" width="280" alt="Orc Cleaver, three-quarter view"> <img src="images/objects/orcs_pack_orc_cleaver_third.jpg" width="280" alt="Orc Cleaver, far three-quarter view">

#### Sherwood Sword

[Modular Medieval Town](https://www.fab.com/listings/720ccb75-32a9-4130-acab-532239760d22) · **Use:** short sword · model `SM_Sword_01` · 79 × 14 × 5 cm

A short, broad iron sword with a square guard.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves); the two-handed ones by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/hive_sherwood_sherwood_sword_side.jpg" width="280" alt="Sherwood Sword, side view"> <img src="images/objects/hive_sherwood_sherwood_sword_quarter.jpg" width="280" alt="Sherwood Sword, three-quarter view"> <img src="images/objects/hive_sherwood_sherwood_sword_third.jpg" width="280" alt="Sherwood Sword, far three-quarter view">

#### Camel Rider's Sheathed Sword

[Fantasy Animal (Pack)](https://www.fab.com/listings/4878a5f0-f82b-4530-b50d-a3f880ef4665) · **Use:** sidearm · model `SK_Camel_Sword` · 101 × 32 × 31 cm

A curved sword in a carved, studded scabbard.

**Animations.** **Own:** a part skinned to its character's skeleton (35 bones): it moves with that character's clips. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves); the two-handed ones by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/animals_pack_camel_rider_s_scimitar_side.jpg" width="280" alt="Camel Rider's Sheathed Sword, side view"> <img src="images/objects/animals_pack_camel_rider_s_scimitar_quarter.jpg" width="280" alt="Camel Rider's Sheathed Sword, three-quarter view"> <img src="images/objects/animals_pack_camel_rider_s_scimitar_third.jpg" width="280" alt="Camel Rider's Sheathed Sword, far three-quarter view">

#### Leaf-Blade Knife

[House Forge: Modular House Building Kit](https://www.fab.com/listings/277b975e-2158-41ef-908a-ef08bc26a409) · **Use:** knife · model `SM_WeaponKnife_01a` · 42 × 12 × 4 cm

A stone-grey knife with a pierced, leaf-shaped blade.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** No third-person knife clips in the project; the first-person ones are in FPS Pistol And Knife, the FPS Starter Pack and Sci-Fi Hands With Knife.

<img src="images/objects/houseforge_01_hunting_knife_side.jpg" width="280" alt="Leaf-Blade Knife, side view"> <img src="images/objects/houseforge_01_hunting_knife_quarter.jpg" width="280" alt="Leaf-Blade Knife, three-quarter view"> <img src="images/objects/houseforge_01_hunting_knife_third.jpg" width="280" alt="Leaf-Blade Knife, far three-quarter view">

### Axes, hammers, maces and clubs

#### Battle Axe

[Dark Fantasy Weapons](https://www.fab.com/listings/244607ad-e819-4320-bbc7-687b844b5bed) · **Use:** two-handed axe · model `SM_Axe` · 91 × 37 × 7 cm

A double-bladed axe with a winged head and a spiked butt.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/medieval_weapons_battle_axe_side.jpg" width="280" alt="Battle Axe, side view"> <img src="images/objects/medieval_weapons_battle_axe_quarter.jpg" width="280" alt="Battle Axe, three-quarter view"> <img src="images/objects/medieval_weapons_battle_axe_third.jpg" width="280" alt="Battle Axe, far three-quarter view">

#### Double Axe

[Dark Fantasy Weapons](https://www.fab.com/listings/244607ad-e819-4320-bbc7-687b844b5bed) · **Use:** one-handed axe · model `SM_ThrowingAxe` · 57 × 32 × 5 cm

A short double-bitted axe with a heavy, wrapped haft.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves).

<img src="images/objects/medieval_weapons_throwing_axe_side.jpg" width="280" alt="Double Axe, side view"> <img src="images/objects/medieval_weapons_throwing_axe_quarter.jpg" width="280" alt="Double Axe, three-quarter view"> <img src="images/objects/medieval_weapons_throwing_axe_third.jpg" width="280" alt="Double Axe, far three-quarter view">

#### Mace

[Dark Fantasy Weapons](https://www.fab.com/listings/244607ad-e819-4320-bbc7-687b844b5bed) · **Use:** mace · model `SM_Mace` · 83 × 18 × 17 cm

A spiked iron ball on a ringed shaft.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves).

<img src="images/objects/medieval_weapons_mace_side.jpg" width="280" alt="Mace, side view"> <img src="images/objects/medieval_weapons_mace_quarter.jpg" width="280" alt="Mace, three-quarter view"> <img src="images/objects/medieval_weapons_mace_third.jpg" width="280" alt="Mace, far three-quarter view">

#### Bearded Axe

[Viking (Customized)](https://www.fab.com/listings/e814c3a3-11ba-4316-a07a-b0980fd016ef) · **Use:** one-handed axe · model `SM_Viking_Axe_01` · 69 × 22 × 3 cm

A Viking axe with a long, leather-wrapped haft.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves).

<img src="images/objects/vikings_bearded_axe_side.jpg" width="280" alt="Bearded Axe, side view"> <img src="images/objects/vikings_bearded_axe_quarter.jpg" width="280" alt="Bearded Axe, three-quarter view"> <img src="images/objects/vikings_bearded_axe_third.jpg" width="280" alt="Bearded Axe, far three-quarter view">

#### Dane Axe

[Viking (Customized)](https://www.fab.com/listings/e814c3a3-11ba-4316-a07a-b0980fd016ef) · **Use:** two-handed axe · model `SM_Viking_Axe_02` · 115 × 45 × 6 cm

A double-bitted Viking axe on a long haft.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/vikings_dane_axe_side.jpg" width="280" alt="Dane Axe, side view"> <img src="images/objects/vikings_dane_axe_quarter.jpg" width="280" alt="Dane Axe, three-quarter view"> <img src="images/objects/vikings_dane_axe_third.jpg" width="280" alt="Dane Axe, far three-quarter view">

#### Viking Mace

[Viking (Customized)](https://www.fab.com/listings/e814c3a3-11ba-4316-a07a-b0980fd016ef) · **Use:** mace · model `SM_Viking_Club_01` · 73 × 20 × 20 cm

A copper ball with spikes on a wooden haft.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves).

<img src="images/objects/vikings_viking_club_side.jpg" width="280" alt="Viking Mace, side view"> <img src="images/objects/vikings_viking_club_quarter.jpg" width="280" alt="Viking Mace, three-quarter view"> <img src="images/objects/vikings_viking_club_third.jpg" width="280" alt="Viking Mace, far three-quarter view">

#### Dwarven Axe

[Fantasy Characters (Pack)](https://www.fab.com/listings/f5816915-86d9-4bef-b8f3-921408ae240b) · **Use:** two-handed axe · model `SM_Dwarf_Axe` · 109 × 49 × 11 cm

A round double axe with glowing runes, on a pale haft with a ring.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/fantasy_pack_dwarven_axe_side.jpg" width="280" alt="Dwarven Axe, side view"> <img src="images/objects/fantasy_pack_dwarven_axe_quarter.jpg" width="280" alt="Dwarven Axe, three-quarter view"> <img src="images/objects/fantasy_pack_dwarven_axe_third.jpg" width="280" alt="Dwarven Axe, far three-quarter view">

#### Knight's Poleaxe

[Fantasy Characters (Pack)](https://www.fab.com/listings/f5816915-86d9-4bef-b8f3-921408ae240b) · **Use:** polearm · model `SM_Knight_Axe` · 193 × 24 × 6 cm

A slim axe head on a long red pole.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/fantasy_pack_knight_s_axe_side.jpg" width="280" alt="Knight's Poleaxe, side view"> <img src="images/objects/fantasy_pack_knight_s_axe_quarter.jpg" width="280" alt="Knight's Poleaxe, three-quarter view"> <img src="images/objects/fantasy_pack_knight_s_axe_third.jpg" width="280" alt="Knight's Poleaxe, far three-quarter view">

#### Northman's Axe

[Fantasy Characters (Pack)](https://www.fab.com/listings/f5816915-86d9-4bef-b8f3-921408ae240b) · **Use:** two-handed axe · model `SM_Viking_Axe` · 73 × 31 × 6 cm

A heavy bearded double axe on a wrapped haft.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/fantasy_pack_northman_s_axe_side.jpg" width="280" alt="Northman's Axe, side view"> <img src="images/objects/fantasy_pack_northman_s_axe_quarter.jpg" width="280" alt="Northman's Axe, three-quarter view"> <img src="images/objects/fantasy_pack_northman_s_axe_third.jpg" width="280" alt="Northman's Axe, far three-quarter view">

#### Barbarian Axe

[Fantasy Characters (Pack)](https://www.fab.com/listings/f5816915-86d9-4bef-b8f3-921408ae240b) · **Use:** two-handed axe · model `SM_Fantasy_Barbarian_Weapon_01` · 92 × 23 × 5 cm

A single crescent blade on a long black-and-gold haft.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/fantasy_pack_barbarian_axe_side.jpg" width="280" alt="Barbarian Axe, side view"> <img src="images/objects/fantasy_pack_barbarian_axe_quarter.jpg" width="280" alt="Barbarian Axe, three-quarter view"> <img src="images/objects/fantasy_pack_barbarian_axe_third.jpg" width="280" alt="Barbarian Axe, far three-quarter view">

#### Barbarian's Spiked Mace

[Fantasy Characters (Pack)](https://www.fab.com/listings/f5816915-86d9-4bef-b8f3-921408ae240b) · **Use:** two-handed mace · model `SM_Fantasy_Barbarian_Weapon_02` · 92 × 28 × 25 cm

A flanged, spiked iron head on a black wrapped shaft.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/fantasy_pack_barbarian_cleaver_side.jpg" width="280" alt="Barbarian's Spiked Mace, side view"> <img src="images/objects/fantasy_pack_barbarian_cleaver_quarter.jpg" width="280" alt="Barbarian's Spiked Mace, three-quarter view"> <img src="images/objects/fantasy_pack_barbarian_cleaver_third.jpg" width="280" alt="Barbarian's Spiked Mace, far three-quarter view">

#### Troll's Spiked Maul

[Fantasy Characters (Pack)](https://www.fab.com/listings/f5816915-86d9-4bef-b8f3-921408ae240b) · **Use:** two-handed maul · model `SK_Cudgel` · 173 × 66 × 66 cm

A black four-pointed iron head on a red-bound handle.

**Animations.** **Own:** a skeletal mesh (3 bones) without clips of its own. **Third person:** Held by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/fantasy_pack_troll_s_cudgel_side.jpg" width="280" alt="Troll's Spiked Maul, side view"> <img src="images/objects/fantasy_pack_troll_s_cudgel_quarter.jpg" width="280" alt="Troll's Spiked Maul, three-quarter view"> <img src="images/objects/fantasy_pack_troll_s_cudgel_third.jpg" width="280" alt="Troll's Spiked Maul, far three-quarter view">

#### Executioner's Axe

[Fantasy Enemies (Pack)](https://www.fab.com/listings/79f79e3e-570b-4d96-bc3f-f62107178169) · **Use:** polearm · model `SM_Executioner_Axe` · 179 × 36 × 9 cm

A blood-stained bearded axe on a tall pole.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/fantasy_enemies_pack_executioner_s_axe_side.jpg" width="280" alt="Executioner's Axe, side view"> <img src="images/objects/fantasy_enemies_pack_executioner_s_axe_quarter.jpg" width="280" alt="Executioner's Axe, three-quarter view"> <img src="images/objects/fantasy_enemies_pack_executioner_s_axe_third.jpg" width="280" alt="Executioner's Axe, far three-quarter view">

#### Demon Axe

[Fantasy Enemies (Pack)](https://www.fab.com/listings/79f79e3e-570b-4d96-bc3f-f62107178169) · **Use:** two-handed axe · model `SM_Demon_Axe` · 167 × 54 × 10 cm

A golden double axe on a long bone-studded shaft.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/fantasy_enemies_pack_demon_axe_side.jpg" width="280" alt="Demon Axe, side view"> <img src="images/objects/fantasy_enemies_pack_demon_axe_quarter.jpg" width="280" alt="Demon Axe, three-quarter view"> <img src="images/objects/fantasy_enemies_pack_demon_axe_third.jpg" width="280" alt="Demon Axe, far three-quarter view">

#### Troll's Morning Star

[Fantasy Enemies (Pack)](https://www.fab.com/listings/79f79e3e-570b-4d96-bc3f-f62107178169) · **Use:** two-handed mace · model `SM_Troll_Axe` · 99 × 52 × 45 cm

A rusty spiked ball on a stout handle.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/fantasy_enemies_pack_troll_axe_side.jpg" width="280" alt="Troll's Morning Star, side view"> <img src="images/objects/fantasy_enemies_pack_troll_axe_quarter.jpg" width="280" alt="Troll's Morning Star, three-quarter view"> <img src="images/objects/fantasy_enemies_pack_troll_axe_third.jpg" width="280" alt="Troll's Morning Star, far three-quarter view">

#### Befouler's Weapon

[Fantasy Enemies (Pack)](https://www.fab.com/listings/79f79e3e-570b-4d96-bc3f-f62107178169) · **Use:** two-handed axe · model `SM_Befouler_Weapon` · 116 × 39 × 11 cm

A blood-red hooked blade on a bound bone haft.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/fantasy_enemies_pack_befouler_s_weapon_side.jpg" width="280" alt="Befouler's Weapon, side view"> <img src="images/objects/fantasy_enemies_pack_befouler_s_weapon_quarter.jpg" width="280" alt="Befouler's Weapon, three-quarter view"> <img src="images/objects/fantasy_enemies_pack_befouler_s_weapon_third.jpg" width="280" alt="Befouler's Weapon, far three-quarter view">

#### Dwarf Axe

[Dwarfs Pack](https://www.fab.com/listings/80643e93-5d54-438c-ae9d-7717242e5a16) · **Use:** two-handed axe · model `SM_Axe` · 94 × 55 × 10 cm

A broad dwarven double axe with gilded fittings.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/dwarf_pack_dwarf_axe_side.jpg" width="280" alt="Dwarf Axe, side view"> <img src="images/objects/dwarf_pack_dwarf_axe_quarter.jpg" width="280" alt="Dwarf Axe, three-quarter view"> <img src="images/objects/dwarf_pack_dwarf_axe_third.jpg" width="280" alt="Dwarf Axe, far three-quarter view">

#### Bedvar's Warhammer

[Dwarfs Pack](https://www.fab.com/listings/80643e93-5d54-438c-ae9d-7717242e5a16) · **Use:** warhammer · model `SM_Dwarf_Bedvar_Hammer_Mesh` · 87 × 46 × 19 cm

A great gilded hammer with stone-faced heads and a red-wrapped grip.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/dwarf_pack_bedvar_s_warhammer_side.jpg" width="280" alt="Bedvar's Warhammer, side view"> <img src="images/objects/dwarf_pack_bedvar_s_warhammer_quarter.jpg" width="280" alt="Bedvar's Warhammer, three-quarter view"> <img src="images/objects/dwarf_pack_bedvar_s_warhammer_third.jpg" width="280" alt="Bedvar's Warhammer, far three-quarter view">

#### Hammer in the Stone

[House Forge: Modular House Building Kit](https://www.fab.com/listings/277b975e-2158-41ef-908a-ef08bc26a409) · **Use:** quest item / warhammer · model `SM_ThorHammer_01a` · 266 × 253 × 225 cm

A war hammer driven into a rock.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves).

<img src="images/objects/houseforge_01_thor_s_hammer_side.jpg" width="280" alt="Hammer in the Stone, side view"> <img src="images/objects/houseforge_01_thor_s_hammer_quarter.jpg" width="280" alt="Hammer in the Stone, three-quarter view"> <img src="images/objects/houseforge_01_thor_s_hammer_third.jpg" width="280" alt="Hammer in the Stone, far three-quarter view">

#### Sherwood Axe

[Modular Medieval Town](https://www.fab.com/listings/720ccb75-32a9-4130-acab-532239760d22) · **Use:** hatchet · model `SM_Axe_01` · 56 × 21 × 5 cm

A plain woodcutter's hatchet.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves).

<img src="images/objects/hive_sherwood_sherwood_axe_side.jpg" width="280" alt="Sherwood Axe, side view"> <img src="images/objects/hive_sherwood_sherwood_axe_quarter.jpg" width="280" alt="Sherwood Axe, three-quarter view"> <img src="images/objects/hive_sherwood_sherwood_axe_third.jpg" width="280" alt="Sherwood Axe, far three-quarter view">

#### Headsman's Axe

[NPC King And Queen](https://www.fab.com/listings/cf92a409-cb02-460f-a4e1-27039c0e2a99) · **Use:** two-handed axe · model `SM_UE4_NPC_Executioner_Axe` · 123 × 30 × 6 cm

A bearded executioner's axe on a long wooden haft.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/npc_king_and_queen_headsman_s_axe_side.jpg" width="280" alt="Headsman's Axe, side view"> <img src="images/objects/npc_king_and_queen_headsman_s_axe_quarter.jpg" width="280" alt="Headsman's Axe, three-quarter view"> <img src="images/objects/npc_king_and_queen_headsman_s_axe_third.jpg" width="280" alt="Headsman's Axe, far three-quarter view">

#### Orc Axe

[14 Orcs Pack](https://www.fab.com/listings/3c224616-e998-433c-910b-32901d426103) · **Use:** two-handed axe · model `SM_Orc_01_Weapon` · 103 × 49 × 19 cm

A spiked axe head with a long spike on top.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/orcs_pack_orc_axe_side.jpg" width="280" alt="Orc Axe, side view"> <img src="images/objects/orcs_pack_orc_axe_quarter.jpg" width="280" alt="Orc Axe, three-quarter view"> <img src="images/objects/orcs_pack_orc_axe_third.jpg" width="280" alt="Orc Axe, far three-quarter view">

#### Orc Spiked Club

[14 Orcs Pack](https://www.fab.com/listings/3c224616-e998-433c-910b-32901d426103) · **Use:** club · model `SM_Orc_02_Weapon` · 102 × 19 × 17 cm

A thick wooden club ringed with iron spikes.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/orcs_pack_orc_glaive_side.jpg" width="280" alt="Orc Spiked Club, side view"> <img src="images/objects/orcs_pack_orc_glaive_quarter.jpg" width="280" alt="Orc Spiked Club, three-quarter view"> <img src="images/objects/orcs_pack_orc_glaive_third.jpg" width="280" alt="Orc Spiked Club, far three-quarter view">

#### Orc Bone Club

[14 Orcs Pack](https://www.fab.com/listings/3c224616-e998-433c-910b-32901d426103) · **Use:** club · model `SM_Orc_05_Weapon` · 98 × 33 × 14 cm

A curved club studded with fangs and a skull.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/orcs_pack_orc_bone_club_side.jpg" width="280" alt="Orc Bone Club, side view"> <img src="images/objects/orcs_pack_orc_bone_club_quarter.jpg" width="280" alt="Orc Bone Club, three-quarter view"> <img src="images/objects/orcs_pack_orc_bone_club_third.jpg" width="280" alt="Orc Bone Club, far three-quarter view">

#### Orc Warhammer

[14 Orcs Pack](https://www.fab.com/listings/3c224616-e998-433c-910b-32901d426103) · **Use:** warhammer · model `SM_Orc_06_Weapon_01` · 92 × 33 × 24 cm

A blocky iron hammer head on a ringed shaft.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves).

<img src="images/objects/orcs_pack_orc_hand_axe_side.jpg" width="280" alt="Orc Warhammer, side view"> <img src="images/objects/orcs_pack_orc_hand_axe_quarter.jpg" width="280" alt="Orc Warhammer, three-quarter view"> <img src="images/objects/orcs_pack_orc_hand_axe_third.jpg" width="280" alt="Orc Warhammer, far three-quarter view">

#### Azrak's Weapon

[14 Orcs Pack](https://www.fab.com/listings/3c224616-e998-433c-910b-32901d426103) · **Use:** club · model `SK_Azrak_Weapon` · 108 × 38 × 12 cm

A gnarled, horn-spiked wooden club.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/orcs_pack_azrak_s_weapon_side.jpg" width="280" alt="Azrak's Weapon, side view"> <img src="images/objects/orcs_pack_azrak_s_weapon_quarter.jpg" width="280" alt="Azrak's Weapon, three-quarter view"> <img src="images/objects/orcs_pack_azrak_s_weapon_third.jpg" width="280" alt="Azrak's Weapon, far three-quarter view">

#### Magur's Weapon

[14 Orcs Pack](https://www.fab.com/listings/3c224616-e998-433c-910b-32901d426103) · **Use:** mace · model `SK_Magur_Weapon` · 124 × 58 × 28 cm

A huge bone shaft topped with a horned skull.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/orcs_pack_magur_s_weapon_side.jpg" width="280" alt="Magur's Weapon, side view"> <img src="images/objects/orcs_pack_magur_s_weapon_quarter.jpg" width="280" alt="Magur's Weapon, three-quarter view"> <img src="images/objects/orcs_pack_magur_s_weapon_third.jpg" width="280" alt="Magur's Weapon, far three-quarter view">

#### Ursag's Horn Blade

[14 Orcs Pack](https://www.fab.com/listings/3c224616-e998-433c-910b-32901d426103) · **Use:** two-handed blade · model `SK_Ursag_Weapon` · 89 × 44 × 11 cm

A great curved horn blade on a bone-wrapped grip.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/orcs_pack_ursag_s_weapon_side.jpg" width="280" alt="Ursag's Horn Blade, side view"> <img src="images/objects/orcs_pack_ursag_s_weapon_quarter.jpg" width="280" alt="Ursag's Horn Blade, three-quarter view"> <img src="images/objects/orcs_pack_ursag_s_weapon_third.jpg" width="280" alt="Ursag's Horn Blade, far three-quarter view">

#### Shaman's Totem Staff

[14 Orcs Pack](https://www.fab.com/listings/3c224616-e998-433c-910b-32901d426103) · **Use:** staff · model `SK_Orc_04_Weapon` · 196 × 34 × 31 cm

A tall staff topped with a skull and hung with charms.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** No staff or spell-casting clips in the project; a staff can borrow [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/orcs_pack_shaman_s_totem_staff_side.jpg" width="280" alt="Shaman's Totem Staff, side view"> <img src="images/objects/orcs_pack_shaman_s_totem_staff_quarter.jpg" width="280" alt="Shaman's Totem Staff, three-quarter view"> <img src="images/objects/orcs_pack_shaman_s_totem_staff_third.jpg" width="280" alt="Shaman's Totem Staff, far three-quarter view">

#### Bear Warrior's Weapon

[Animals Warrior Pack](https://www.fab.com/listings/be0d1014-cd06-4fc8-a442-b107ee75b81f) · **Use:** two-handed axe · model `SM_Bear_Weapon` · 109 × 39 × 39 cm

A dark double axe with spiked wings.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/animals_warrior_pack_bear_warrior_s_weapon_side.jpg" width="280" alt="Bear Warrior's Weapon, side view"> <img src="images/objects/animals_warrior_pack_bear_warrior_s_weapon_quarter.jpg" width="280" alt="Bear Warrior's Weapon, three-quarter view"> <img src="images/objects/animals_warrior_pack_bear_warrior_s_weapon_third.jpg" width="280" alt="Bear Warrior's Weapon, far three-quarter view">

#### Minotaur's Axe

[Animals Warrior Pack](https://www.fab.com/listings/be0d1014-cd06-4fc8-a442-b107ee75b81f) · **Use:** two-handed axe · model `SM_Bull_Weapon_Mesh` · 111 × 47 × 9 cm

A heavy steel labrys with a skull at its centre.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/animals_warrior_pack_minotaur_s_axe_side.jpg" width="280" alt="Minotaur's Axe, side view"> <img src="images/objects/animals_warrior_pack_minotaur_s_axe_quarter.jpg" width="280" alt="Minotaur's Axe, three-quarter view"> <img src="images/objects/animals_warrior_pack_minotaur_s_axe_third.jpg" width="280" alt="Minotaur's Axe, far three-quarter view">

#### Crocodile's Spear

[Animals Warrior Pack](https://www.fab.com/listings/be0d1014-cd06-4fc8-a442-b107ee75b81f) · **Use:** spear · model `SM_Crocodile_Weapon_Mesh` · 180 × 17 × 16 cm

A bone-hung spear with skulls on its shaft.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/animals_warrior_pack_crocodile_s_weapon_side.jpg" width="280" alt="Crocodile's Spear, side view"> <img src="images/objects/animals_warrior_pack_crocodile_s_weapon_quarter.jpg" width="280" alt="Crocodile's Spear, three-quarter view"> <img src="images/objects/animals_warrior_pack_crocodile_s_weapon_third.jpg" width="280" alt="Crocodile's Spear, far three-quarter view">

#### Elephant's Trident

[Animals Warrior Pack](https://www.fab.com/listings/be0d1014-cd06-4fc8-a442-b107ee75b81f) · **Use:** polearm · model `SM_Elephant_Weapon` · 172 × 33 × 7 cm

A black three-pronged polearm.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/animals_warrior_pack_elephant_s_weapon_side.jpg" width="280" alt="Elephant's Trident, side view"> <img src="images/objects/animals_warrior_pack_elephant_s_weapon_quarter.jpg" width="280" alt="Elephant's Trident, three-quarter view"> <img src="images/objects/animals_warrior_pack_elephant_s_weapon_third.jpg" width="280" alt="Elephant's Trident, far three-quarter view">

### Spears and polearms

#### Spear

[Dark Fantasy Weapons](https://www.fab.com/listings/244607ad-e819-4320-bbc7-687b844b5bed) · **Use:** spear · model `SM_Spear` · 244 × 18 × 4 cm

A long dark spear with a barbed head.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/medieval_weapons_spear_side.jpg" width="280" alt="Spear, side view"> <img src="images/objects/medieval_weapons_spear_quarter.jpg" width="280" alt="Spear, three-quarter view"> <img src="images/objects/medieval_weapons_spear_third.jpg" width="280" alt="Spear, far three-quarter view">

#### War Scythe

[Dark Fantasy Weapons](https://www.fab.com/listings/244607ad-e819-4320-bbc7-687b844b5bed) · **Use:** scythe · model `SM_Scythe` · 82 × 37 × 8 cm

A black, toothed scythe blade on a short ornate haft.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/medieval_weapons_war_scythe_side.jpg" width="280" alt="War Scythe, side view"> <img src="images/objects/medieval_weapons_war_scythe_quarter.jpg" width="280" alt="War Scythe, three-quarter view"> <img src="images/objects/medieval_weapons_war_scythe_third.jpg" width="280" alt="War Scythe, far three-quarter view">

#### Halberd

[Knights (Pack)](https://www.fab.com/listings/6907d3d8-d0db-43c0-bf9c-8ad43c70e7b3) · **Use:** halberd · model `SM_Knight_01_Halberd` · 234 × 29 × 5 cm

A halberd: axe blade, hook and spike on a long wooden pole.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/knights_pack_halberd_side.jpg" width="280" alt="Halberd, side view"> <img src="images/objects/knights_pack_halberd_quarter.jpg" width="280" alt="Halberd, three-quarter view"> <img src="images/objects/knights_pack_halberd_third.jpg" width="280" alt="Halberd, far three-quarter view">

#### Banner Spear

[Knights (Pack)](https://www.fab.com/listings/6907d3d8-d0db-43c0-bf9c-8ad43c70e7b3) · **Use:** spear · model `SM_Knight_01_Banner_Spear` · 307 × 9 × 4 cm

A plain spear with a pennon fitting.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/knights_pack_banner_spear_side.jpg" width="280" alt="Banner Spear, side view"> <img src="images/objects/knights_pack_banner_spear_quarter.jpg" width="280" alt="Banner Spear, three-quarter view"> <img src="images/objects/knights_pack_banner_spear_third.jpg" width="280" alt="Banner Spear, far three-quarter view">

#### Lady Knight's Spear

[Knights (Pack)](https://www.fab.com/listings/6907d3d8-d0db-43c0-bf9c-8ad43c70e7b3) · **Use:** spear · model `SM_Knight_04_Spear` · 220 × 29 × 7 cm

An ornate silver-and-white spear with a broad, winged head.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/knights_pack_lady_knight_s_spear_side.jpg" width="280" alt="Lady Knight's Spear, side view"> <img src="images/objects/knights_pack_lady_knight_s_spear_quarter.jpg" width="280" alt="Lady Knight's Spear, three-quarter view"> <img src="images/objects/knights_pack_lady_knight_s_spear_third.jpg" width="280" alt="Lady Knight's Spear, far three-quarter view">

#### Viking Spear

[Viking (Customized)](https://www.fab.com/listings/e814c3a3-11ba-4316-a07a-b0980fd016ef) · **Use:** spear · model `SM_Viking_Spear_01` · 266 × 16 × 4 cm

A long Viking spear with a lugged head.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/vikings_viking_spear_side.jpg" width="280" alt="Viking Spear, side view"> <img src="images/objects/vikings_viking_spear_quarter.jpg" width="280" alt="Viking Spear, three-quarter view"> <img src="images/objects/vikings_viking_spear_third.jpg" width="280" alt="Viking Spear, far three-quarter view">

#### Desert Spear

[Fantasy Warriors (Pack)](https://www.fab.com/listings/df8194f9-ec63-49f6-a885-6feb7a94fcb1) · **Use:** spear · model `SM_Fantasy_Hero_02_Spear` · 211 × 4 × 4 cm

A dark spear wrapped in leather bands.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/warriors_pack_desert_spear_side.jpg" width="280" alt="Desert Spear, side view"> <img src="images/objects/warriors_pack_desert_spear_quarter.jpg" width="280" alt="Desert Spear, three-quarter view"> <img src="images/objects/warriors_pack_desert_spear_third.jpg" width="280" alt="Desert Spear, far three-quarter view">

#### Broddi's Spear

[Dwarfs Pack](https://www.fab.com/listings/80643e93-5d54-438c-ae9d-7717242e5a16) · **Use:** spear · model `SM_Dwarf_BroddI_Spear_Dwarf_Broddi_Spear_Mesh` · 249 × 14 × 5 cm

A short dwarven spear with metal bands.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/dwarf_pack_broddi_s_spear_side.jpg" width="280" alt="Broddi's Spear, side view"> <img src="images/objects/dwarf_pack_broddi_s_spear_quarter.jpg" width="280" alt="Broddi's Spear, three-quarter view"> <img src="images/objects/dwarf_pack_broddi_s_spear_third.jpg" width="280" alt="Broddi's Spear, far three-quarter view">

#### Sherwood Spear

[Modular Medieval Town](https://www.fab.com/listings/720ccb75-32a9-4130-acab-532239760d22) · **Use:** spear · model `SM_Spear_01` · 211 × 9 × 5 cm

A simple wooden spear.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/hive_sherwood_sherwood_spear_side.jpg" width="280" alt="Sherwood Spear, side view"> <img src="images/objects/hive_sherwood_sherwood_spear_quarter.jpg" width="280" alt="Sherwood Spear, three-quarter view"> <img src="images/objects/hive_sherwood_sherwood_spear_third.jpg" width="280" alt="Sherwood Spear, far three-quarter view">

#### Stone Spear

[Primitive Characters (Pack)](https://www.fab.com/listings/3ce14ea2-e944-46b1-afec-e10c50e7fa96) · **Use:** spear · model `SM_Primitive_Weapon_01` · 223 × 7 × 4 cm

A stone-tipped wooden spear.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/primitive_characters_pack_stone_spear_side.jpg" width="280" alt="Stone Spear, side view"> <img src="images/objects/primitive_characters_pack_stone_spear_quarter.jpg" width="280" alt="Stone Spear, three-quarter view"> <img src="images/objects/primitive_characters_pack_stone_spear_third.jpg" width="280" alt="Stone Spear, far three-quarter view">

### Primitive weapons

#### Bone Club

[Primitive Characters (Pack)](https://www.fab.com/listings/3ce14ea2-e944-46b1-afec-e10c50e7fa96) · **Use:** club · model `SM_Primitive_Weapon_02` · 50 × 23 × 7 cm

A wooden club with stones bound to its head.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/primitive_characters_pack_bone_club_side.jpg" width="280" alt="Bone Club, side view"> <img src="images/objects/primitive_characters_pack_bone_club_quarter.jpg" width="280" alt="Bone Club, three-quarter view"> <img src="images/objects/primitive_characters_pack_bone_club_third.jpg" width="280" alt="Bone Club, far three-quarter view">

#### Obsidian Knife

[Primitive Characters (Pack)](https://www.fab.com/listings/3ce14ea2-e944-46b1-afec-e10c50e7fa96) · **Use:** knife · model `SM_Primitive_Weapon_03` · 28 × 6 × 4 cm

A black obsidian blade on a bound handle.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** No third-person knife clips in the project; the first-person ones are in FPS Pistol And Knife, the FPS Starter Pack and Sci-Fi Hands With Knife.

<img src="images/objects/primitive_characters_pack_stone_axe_side.jpg" width="280" alt="Obsidian Knife, side view"> <img src="images/objects/primitive_characters_pack_stone_axe_quarter.jpg" width="280" alt="Obsidian Knife, three-quarter view"> <img src="images/objects/primitive_characters_pack_stone_axe_third.jpg" width="280" alt="Obsidian Knife, far three-quarter view">

#### Bone Blade

[Primitive Characters (Pack)](https://www.fab.com/listings/3ce14ea2-e944-46b1-afec-e10c50e7fa96) · **Use:** knife · model `SM_Primitive_Weapon_04` · 32 × 6 × 3 cm

A long bone blade with a leather grip.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** No third-person knife clips in the project; the first-person ones are in FPS Pistol And Knife, the FPS Starter Pack and Sci-Fi Hands With Knife.

<img src="images/objects/primitive_characters_pack_stone_hammer_side.jpg" width="280" alt="Bone Blade, side view"> <img src="images/objects/primitive_characters_pack_stone_hammer_quarter.jpg" width="280" alt="Bone Blade, three-quarter view"> <img src="images/objects/primitive_characters_pack_stone_hammer_third.jpg" width="280" alt="Bone Blade, far three-quarter view">

#### Bone Pick

[Primitive Characters (Pack)](https://www.fab.com/listings/3ce14ea2-e944-46b1-afec-e10c50e7fa96) · **Use:** pick · model `SM_Primitive_02_Weapons_01` · 61 × 37 × 12 cm

A bone pick with a horn point.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves).

<img src="images/objects/primitive_characters_pack_cavewoman_s_weapon_side.jpg" width="280" alt="Bone Pick, side view"> <img src="images/objects/primitive_characters_pack_cavewoman_s_weapon_quarter.jpg" width="280" alt="Bone Pick, three-quarter view"> <img src="images/objects/primitive_characters_pack_cavewoman_s_weapon_third.jpg" width="280" alt="Bone Pick, far three-quarter view">

#### Toothed Bone Sword

[Primitive Characters (Pack)](https://www.fab.com/listings/3ce14ea2-e944-46b1-afec-e10c50e7fa96) · **Use:** blade · model `SM_Primitive_03_Weapon_01` · 56 × 11 × 5 cm

A bloodied bone blade set with teeth.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves); the two-handed ones by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/primitive_characters_pack_elder_s_staff_side.jpg" width="280" alt="Toothed Bone Sword, side view"> <img src="images/objects/primitive_characters_pack_elder_s_staff_quarter.jpg" width="280" alt="Toothed Bone Sword, three-quarter view"> <img src="images/objects/primitive_characters_pack_elder_s_staff_third.jpg" width="280" alt="Toothed Bone Sword, far three-quarter view">

#### Shaman's Staff

[Primitive Characters (Pack)](https://www.fab.com/listings/3ce14ea2-e944-46b1-afec-e10c50e7fa96) · **Use:** staff · model `SM_Primitive_04_Weapon` · 200 × 49 × 21 cm

A crooked staff topped with a ring of bone charms.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** No staff or spell-casting clips in the project; a staff can borrow [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/primitive_characters_pack_shaman_s_staff_side.jpg" width="280" alt="Shaman's Staff, side view"> <img src="images/objects/primitive_characters_pack_shaman_s_staff_quarter.jpg" width="280" alt="Shaman's Staff, three-quarter view"> <img src="images/objects/primitive_characters_pack_shaman_s_staff_third.jpg" width="280" alt="Shaman's Staff, far three-quarter view">

### Bows, crossbows and staves

#### Longbow

[Dark Fantasy Weapons](https://www.fab.com/listings/244607ad-e819-4320-bbc7-687b844b5bed) · **Use:** bow · model `SM_Bow` · 122 × 32 × 10 cm

A dark recurve bow with gold ornament.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** No bow clips for the UE4 mannequin; the Dark Fantasy Weapons pack (`Medieval_Weapons`) has UE5-mannequin clips that aim a bow (retargeted).

<img src="images/objects/medieval_weapons_longbow_side.jpg" width="280" alt="Longbow, side view"> <img src="images/objects/medieval_weapons_longbow_quarter.jpg" width="280" alt="Longbow, three-quarter view"> <img src="images/objects/medieval_weapons_longbow_third.jpg" width="280" alt="Longbow, far three-quarter view">

#### Crossbow

[Dark Fantasy Weapons](https://www.fab.com/listings/244607ad-e819-4320-bbc7-687b844b5bed) · **Use:** crossbow · model `SM_Crossbow` · 89 × 85 × 12 cm

A gilded crossbow with blade-tipped limbs.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** No crossbow clips for the UE4 mannequin; the Dark Fantasy Weapons pack has UE5-mannequin clips that aim a crossbow (retargeted).

<img src="images/objects/medieval_weapons_crossbow_side.jpg" width="280" alt="Crossbow, side view"> <img src="images/objects/medieval_weapons_crossbow_quarter.jpg" width="280" alt="Crossbow, three-quarter view"> <img src="images/objects/medieval_weapons_crossbow_third.jpg" width="280" alt="Crossbow, far three-quarter view">

#### Arrow

[Dark Fantasy Weapons](https://www.fab.com/listings/244607ad-e819-4320-bbc7-687b844b5bed) · **Use:** ammunition · model `SM_Arrow_Var1` · 88 × 6 × 1 cm

A dark arrow with a barbed head and black fletching.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/medieval_weapons_arrow_side.jpg" width="280" alt="Arrow, side view"> <img src="images/objects/medieval_weapons_arrow_quarter.jpg" width="280" alt="Arrow, three-quarter view"> <img src="images/objects/medieval_weapons_arrow_third.jpg" width="280" alt="Arrow, far three-quarter view">

#### Wizard's Staff

[Dark Fantasy Weapons](https://www.fab.com/listings/244607ad-e819-4320-bbc7-687b844b5bed) · **Use:** mage's staff · model `SM_Staff` · 106 × 17 × 9 cm

An ornate staff topped with a glowing blue gem.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** No staff or spell-casting clips in the project; a staff can borrow [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/medieval_weapons_wizard_s_staff_side.jpg" width="280" alt="Wizard's Staff, side view"> <img src="images/objects/medieval_weapons_wizard_s_staff_quarter.jpg" width="280" alt="Wizard's Staff, three-quarter view"> <img src="images/objects/medieval_weapons_wizard_s_staff_third.jpg" width="280" alt="Wizard's Staff, far three-quarter view">

#### Viking Bow

[House Forge: Modular House Building Kit](https://www.fab.com/listings/277b975e-2158-41ef-908a-ef08bc26a409) · **Use:** bow · model `SM_WeaponBow_01a` · 129 × 25 × 8 cm

A plain wooden longbow.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** No bow clips for the UE4 mannequin; the Dark Fantasy Weapons pack (`Medieval_Weapons`) has UE5-mannequin clips that aim a bow (retargeted).

<img src="images/objects/houseforge_01_viking_bow_side.jpg" width="280" alt="Viking Bow, side view"> <img src="images/objects/houseforge_01_viking_bow_quarter.jpg" width="280" alt="Viking Bow, three-quarter view"> <img src="images/objects/houseforge_01_viking_bow_third.jpg" width="280" alt="Viking Bow, far three-quarter view">

#### Dwarf Crossbow

[Dwarfs Pack](https://www.fab.com/listings/80643e93-5d54-438c-ae9d-7717242e5a16) · **Use:** crossbow · model `SK_Crossbow` · 109 × 100 × 23 cm

A heavy wooden crossbow with a stirrup.

**Animations.** **Own:** a skeletal mesh (73 bones) without clips of its own. **Third person:** No crossbow clips for the UE4 mannequin; the Dark Fantasy Weapons pack has UE5-mannequin clips that aim a crossbow (retargeted).

<img src="images/objects/dwarf_pack_dwarf_crossbow_side.jpg" width="280" alt="Dwarf Crossbow, side view"> <img src="images/objects/dwarf_pack_dwarf_crossbow_quarter.jpg" width="280" alt="Dwarf Crossbow, three-quarter view"> <img src="images/objects/dwarf_pack_dwarf_crossbow_third.jpg" width="280" alt="Dwarf Crossbow, far three-quarter view">

#### Witch's Hooked Staff

[Fantasy Warriors (Pack)](https://www.fab.com/listings/df8194f9-ec63-49f6-a885-6feb7a94fcb1) · **Use:** staff · model `SM_Witch_Weapon` · 181 × 17 × 5 cm

A twisted dark staff with a hooked top.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** No staff or spell-casting clips in the project; a staff can borrow [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/warriors_pack_witch_s_weapon_side.jpg" width="280" alt="Witch's Hooked Staff, side view"> <img src="images/objects/warriors_pack_witch_s_weapon_quarter.jpg" width="280" alt="Witch's Hooked Staff, three-quarter view"> <img src="images/objects/warriors_pack_witch_s_weapon_third.jpg" width="280" alt="Witch's Hooked Staff, far three-quarter view">

### Shields

#### Heater Shield

[Dark Fantasy Weapons](https://www.fab.com/listings/244607ad-e819-4320-bbc7-687b844b5bed) · **Use:** shield · model `SM_Shield_1` · 76 × 60 × 13 cm

An ornate gold-and-iron shield with a monster's face in relief.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Carried by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves) and [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/medieval_weapons_heater_shield_side.jpg" width="280" alt="Heater Shield, side view"> <img src="images/objects/medieval_weapons_heater_shield_quarter.jpg" width="280" alt="Heater Shield, three-quarter view"> <img src="images/objects/medieval_weapons_heater_shield_third.jpg" width="280" alt="Heater Shield, far three-quarter view">

#### Beast Shield

[Dark Fantasy Weapons](https://www.fab.com/listings/244607ad-e819-4320-bbc7-687b844b5bed) · **Use:** shield · model `SM_Shield_2` · 69 × 67 × 14 cm

A shield shaped like a horned beast's face.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Carried by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves) and [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/medieval_weapons_round_shield_side.jpg" width="280" alt="Beast Shield, side view"> <img src="images/objects/medieval_weapons_round_shield_quarter.jpg" width="280" alt="Beast Shield, three-quarter view"> <img src="images/objects/medieval_weapons_round_shield_third.jpg" width="280" alt="Beast Shield, far three-quarter view">

#### Kite Shield

[Dark Fantasy Weapons](https://www.fab.com/listings/244607ad-e819-4320-bbc7-687b844b5bed) · **Use:** shield · model `SM_Shield_3` · 90 × 57 × 25 cm

A dark kite shield with a demonic face.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Carried by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves) and [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/medieval_weapons_kite_shield_side.jpg" width="280" alt="Kite Shield, side view"> <img src="images/objects/medieval_weapons_kite_shield_quarter.jpg" width="280" alt="Kite Shield, three-quarter view"> <img src="images/objects/medieval_weapons_kite_shield_third.jpg" width="280" alt="Kite Shield, far three-quarter view">

#### Heraldic Shield

[Knights (Pack)](https://www.fab.com/listings/6907d3d8-d0db-43c0-bf9c-8ad43c70e7b3) · **Use:** shield · model `SM_Knight_01_Shield` · 79 × 52 × 13 cm

A heater shield painted with a gold lion on black and gold stripes.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Carried by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves) and [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/knights_pack_templar_shield_side.jpg" width="280" alt="Heraldic Shield, side view"> <img src="images/objects/knights_pack_templar_shield_quarter.jpg" width="280" alt="Heraldic Shield, three-quarter view"> <img src="images/objects/knights_pack_templar_shield_third.jpg" width="280" alt="Heraldic Shield, far three-quarter view">

#### Eastern Shield

[Knights (Pack)](https://www.fab.com/listings/6907d3d8-d0db-43c0-bf9c-8ad43c70e7b3) · **Use:** shield · model `SM_Knight_02_Shield` · 77 × 77 × 20 cm

A round, domed shield in black and gold filigree.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Carried by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves) and [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/knights_pack_eastern_shield_side.jpg" width="280" alt="Eastern Shield, side view"> <img src="images/objects/knights_pack_eastern_shield_quarter.jpg" width="280" alt="Eastern Shield, three-quarter view"> <img src="images/objects/knights_pack_eastern_shield_third.jpg" width="280" alt="Eastern Shield, far three-quarter view">

#### Plate Knight's Shield

[Knights (Pack)](https://www.fab.com/listings/6907d3d8-d0db-43c0-bf9c-8ad43c70e7b3) · **Use:** shield · model `SM_Knight_03_Shield` · 108 × 48 × 13 cm

A tall shield with fleurs-de-lis and red stripes.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Carried by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves) and [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/knights_pack_plate_knight_s_shield_side.jpg" width="280" alt="Plate Knight's Shield, side view"> <img src="images/objects/knights_pack_plate_knight_s_shield_quarter.jpg" width="280" alt="Plate Knight's Shield, three-quarter view"> <img src="images/objects/knights_pack_plate_knight_s_shield_third.jpg" width="280" alt="Plate Knight's Shield, far three-quarter view">

#### Lady Knight's Shield

[Knights (Pack)](https://www.fab.com/listings/6907d3d8-d0db-43c0-bf9c-8ad43c70e7b3) · **Use:** shield · model `SM_Knight_04_Shield` · 103 × 53 × 22 cm

A black-and-gold shield with purple gems.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Carried by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves) and [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/knights_pack_lady_knight_s_shield_side.jpg" width="280" alt="Lady Knight's Shield, side view"> <img src="images/objects/knights_pack_lady_knight_s_shield_quarter.jpg" width="280" alt="Lady Knight's Shield, three-quarter view"> <img src="images/objects/knights_pack_lady_knight_s_shield_third.jpg" width="280" alt="Lady Knight's Shield, far three-quarter view">

#### Viking Round Shield

[Viking (Customized)](https://www.fab.com/listings/e814c3a3-11ba-4316-a07a-b0980fd016ef) · **Use:** shield · model `SM_Viking_Shield_01` · 66 × 66 × 11 cm

A round wooden shield painted with green knotwork and a steel boss.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Carried by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves) and [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/vikings_viking_round_shield_side.jpg" width="280" alt="Viking Round Shield, side view"> <img src="images/objects/vikings_viking_round_shield_quarter.jpg" width="280" alt="Viking Round Shield, three-quarter view"> <img src="images/objects/vikings_viking_round_shield_third.jpg" width="280" alt="Viking Round Shield, far three-quarter view">

#### Painted Viking Shield

[Viking (Customized)](https://www.fab.com/listings/e814c3a3-11ba-4316-a07a-b0980fd016ef) · **Use:** shield · model `SM_Viking_Shield_03` · 66 × 66 × 11 cm

A round shield quartered red and white.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Carried by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves) and [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/vikings_painted_viking_shield_side.jpg" width="280" alt="Painted Viking Shield, side view"> <img src="images/objects/vikings_painted_viking_shield_quarter.jpg" width="280" alt="Painted Viking Shield, three-quarter view"> <img src="images/objects/vikings_painted_viking_shield_third.jpg" width="280" alt="Painted Viking Shield, far three-quarter view">

#### Desert Shield

[Fantasy Warriors (Pack)](https://www.fab.com/listings/df8194f9-ec63-49f6-a885-6feb7a94fcb1) · **Use:** shield · model `SM_Fantasy_Hero_02_Shield` · 82 × 82 × 16 cm

A round bronze shield with gold arabesques.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Carried by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves) and [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/warriors_pack_desert_shield_side.jpg" width="280" alt="Desert Shield, side view"> <img src="images/objects/warriors_pack_desert_shield_quarter.jpg" width="280" alt="Desert Shield, three-quarter view"> <img src="images/objects/warriors_pack_desert_shield_third.jpg" width="280" alt="Desert Shield, far three-quarter view">

#### Broddi's Shield

[Dwarfs Pack](https://www.fab.com/listings/80643e93-5d54-438c-ae9d-7717242e5a16) · **Use:** tower shield · model `SM_Dwarf_BroddI_Shield_Dwarf_Broddi_Sheld_Mesh` · 136 × 78 × 13 cm

A tall stone-grey dwarven tower shield.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Carried by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves) and [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/dwarf_pack_broddi_s_shield_side.jpg" width="280" alt="Broddi's Shield, side view"> <img src="images/objects/dwarf_pack_broddi_s_shield_quarter.jpg" width="280" alt="Broddi's Shield, three-quarter view"> <img src="images/objects/dwarf_pack_broddi_s_shield_third.jpg" width="280" alt="Broddi's Shield, far three-quarter view">

#### Village Shield

[House Forge: Modular House Building Kit](https://www.fab.com/listings/277b975e-2158-41ef-908a-ef08bc26a409) · **Use:** shield · model `SM_VikingShield_01a` · 78 × 78 × 18 cm

A round plank shield painted blue and white.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Carried by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves) and [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/houseforge_01_village_shield_side.jpg" width="280" alt="Village Shield, side view"> <img src="images/objects/houseforge_01_village_shield_quarter.jpg" width="280" alt="Village Shield, three-quarter view"> <img src="images/objects/houseforge_01_village_shield_third.jpg" width="280" alt="Village Shield, far three-quarter view">

#### Dock Shield

[Modular Medieval Town, Docks](https://www.fab.com/listings/9bec871e-2d9b-4261-aa26-868d4300f81a) · **Use:** shield · model `SM_Shield_01` · 78 × 78 × 13 cm

A plain round iron-rimmed wooden shield.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Carried by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves) and [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/hivemind_dock_shield_side.jpg" width="280" alt="Dock Shield, side view"> <img src="images/objects/hivemind_dock_shield_quarter.jpg" width="280" alt="Dock Shield, three-quarter view"> <img src="images/objects/hivemind_dock_shield_third.jpg" width="280" alt="Dock Shield, far three-quarter view">

#### War Camp Shield

[[Nanite] Medieval War Camp Kit](https://www.fab.com/listings/3cc08b13-9cb1-46a5-9bd2-47d743ee82b9) · **Use:** shield · model `SM_Shield` · 88 × 88 × 10 cm

A round shield quartered blue and white.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Carried by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves) and [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/warcamp_collection_war_camp_shield_side.jpg" width="280" alt="War Camp Shield, side view"> <img src="images/objects/warcamp_collection_war_camp_shield_quarter.jpg" width="280" alt="War Camp Shield, three-quarter view"> <img src="images/objects/warcamp_collection_war_camp_shield_third.jpg" width="280" alt="War Camp Shield, far three-quarter view">

## Modern weapons

Firearms from flintlock-era revolvers to sniper rifles, the FPS packs' guns (skeletal, with their own shot and reload clips), and knives, clubs and grenades.

### Rifles, machine guns and shotguns

#### Bullpup Rifle (FPS)

[FPS Automatic Rifle 02 (Animations)](https://www.fab.com/listings/4b9f847b-b641-47b8-acc5-fdefc54d7912) · **Use:** assault rifle · model `SK_AutoRifle_Full` · 81 × 36 × 10 cm

A black and tan bullpup rifle with a long scope.

**Animations.** **Own:** a skeletal mesh (14 bones) with 2 clips of its own: reload, shot. **First person:** First-person arm clips: 26 in FPS Automatic Rifle 02: 5 attacks, 3 idles, 4 jumps and falls, 9 moves, 5 other (get weapon, hide, inspection cartridge, inspection weapon, reload). **Third person:** Held by UE4-mannequin clips with a long gun: the Aliens Warrior pack's 47 (3 shots, a reload, aims in eight directions, moves), the Sci-Fi Characters pack's fire, crouch-walk and sprint with iron sights, and the rifle jog, sprint and crouch-walk that came with the Military, Cyber Characters and Monsters Underwater packs; and the UE5 template's rifle equip and reload (retargeted).

<img src="images/objects/fps_automatic_rifle_02_assault_rifle_fps_side.jpg" width="280" alt="Bullpup Rifle (FPS), side view"> <img src="images/objects/fps_automatic_rifle_02_assault_rifle_fps_quarter.jpg" width="280" alt="Bullpup Rifle (FPS), three-quarter view"> <img src="images/objects/fps_automatic_rifle_02_assault_rifle_fps_third.jpg" width="280" alt="Bullpup Rifle (FPS), a frame of its clip">

#### Carbine (FPS)

[FPS Automatic Rifle 01 Animations](https://www.fab.com/listings/65791a45-5921-48c9-b683-1740fe51b674) · **Use:** carbine · model `SK_Automatic_Rifle_01_Basic` · 92 × 21 × 8 cm

A tan carbine on a rail-covered handguard, without sights.

**Animations.** **Own:** a skeletal mesh (12 bones) with 2 clips of its own: reload without arms, shot without arms. **First person:** First-person arm clips: 27 in FPS Automatic Rifle 01: 6 attacks, 1 hit reaction, 5 idles, 4 jumps and falls, 6 moves, 5 other (rifle 01 get weapon, rifle 01 hide weapon, rifle 01 inspection cartridge, rifle 01 reload, rifle 01 weapon inspection). **Third person:** Held by UE4-mannequin clips with a long gun: the Aliens Warrior pack's 47 (3 shots, a reload, aims in eight directions, moves), the Sci-Fi Characters pack's fire, crouch-walk and sprint with iron sights, and the rifle jog, sprint and crouch-walk that came with the Military, Cyber Characters and Monsters Underwater packs; and the UE5 template's rifle equip and reload (retargeted).

<img src="images/objects/fps_automatic_rifle_01_carbine_fps_side.jpg" width="280" alt="Carbine (FPS), side view"> <img src="images/objects/fps_automatic_rifle_01_carbine_fps_quarter.jpg" width="280" alt="Carbine (FPS), three-quarter view"> <img src="images/objects/fps_automatic_rifle_01_carbine_fps_third.jpg" width="280" alt="Carbine (FPS), a frame of its clip">

#### Submachine Gun (FPS)

[FPS Automatic Gun Animations](https://www.fab.com/listings/49622a89-4fae-4fe4-8ce4-47724f0e8aed) · **Use:** submachine gun · model `SK_FPS_Automatic_Gun_Full` · 67 × 24 × 11 cm

A compact black SMG with a red-dot sight and a long silencer.

**Animations.** **Own:** a skeletal mesh (28 bones) with 2 clips of its own: reload, shot. **First person:** First-person arm clips: 23 in FPS Automatic Gun: 4 attacks, 1 hit reaction, 4 idles, 4 jumps and falls, 5 moves, 5 other (gun get weapon, gun hide, gun inspection cartridge, gun inspection weapon, gun reload). **Third person:** Held by UE4-mannequin clips with a long gun: the Aliens Warrior pack's 47 (3 shots, a reload, aims in eight directions, moves), the Sci-Fi Characters pack's fire, crouch-walk and sprint with iron sights, and the rifle jog, sprint and crouch-walk that came with the Military, Cyber Characters and Monsters Underwater packs; and the UE5 template's rifle equip and reload (retargeted).

<img src="images/objects/automatic_gun_submachine_gun_fps_side.jpg" width="280" alt="Submachine Gun (FPS), side view"> <img src="images/objects/automatic_gun_submachine_gun_fps_quarter.jpg" width="280" alt="Submachine Gun (FPS), three-quarter view"> <img src="images/objects/automatic_gun_submachine_gun_fps_third.jpg" width="280" alt="Submachine Gun (FPS), far three-quarter view">

#### Automatic Shotgun (FPS)

[FPS Automatic-Shotgun Animations](https://www.fab.com/listings/4a25f93c-ec5d-4e98-81b4-c08390724e58) · **Use:** shotgun · model `SK_Automatic_Shotgun_Full` · 80 × 27 × 8 cm

A black magazine-fed combat shotgun with a skeleton stock.

**Animations.** **Own:** a skeletal mesh (22 bones) with 1 clip of its own: shotgun shot. **First person:** First-person arm clips: 30 in FPS Automatic-Shotgun: 30 attacks. **Third person:** Held by UE4-mannequin clips with a long gun: the Aliens Warrior pack's 47 (3 shots, a reload, aims in eight directions, moves), the Sci-Fi Characters pack's fire, crouch-walk and sprint with iron sights, and the rifle jog, sprint and crouch-walk that came with the Military, Cyber Characters and Monsters Underwater packs; and the UE5 template's rifle equip and reload (retargeted) (a shotgun has no third-person clips of its own).

<img src="images/objects/fps_automatic_shotgun_automatic_shotgun_fps_side.jpg" width="280" alt="Automatic Shotgun (FPS), side view"> <img src="images/objects/fps_automatic_shotgun_automatic_shotgun_fps_quarter.jpg" width="280" alt="Automatic Shotgun (FPS), three-quarter view"> <img src="images/objects/fps_automatic_shotgun_automatic_shotgun_fps_third.jpg" width="280" alt="Automatic Shotgun (FPS), far three-quarter view">

#### Assault Rifle

[Military Base Megapack](https://www.fab.com/listings/61202d6c-1bc2-4e5d-b2d5-d005ea8b7c67) · **Use:** assault rifle · model `SM_Gun_AssaultRifle` · 112 × 30 × 9 cm

A classic black assault rifle with a carry handle.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by UE4-mannequin clips with a long gun: the Aliens Warrior pack's 47 (3 shots, a reload, aims in eight directions, moves), the Sci-Fi Characters pack's fire, crouch-walk and sprint with iron sights, and the rifle jog, sprint and crouch-walk that came with the Military, Cyber Characters and Monsters Underwater packs; and the UE5 template's rifle equip and reload (retargeted).

<img src="images/objects/mc_environment_assault_rifle_side.jpg" width="280" alt="Assault Rifle, side view"> <img src="images/objects/mc_environment_assault_rifle_quarter.jpg" width="280" alt="Assault Rifle, three-quarter view"> <img src="images/objects/mc_environment_assault_rifle_third.jpg" width="280" alt="Assault Rifle, far three-quarter view">

#### Pump Shotgun

[Military Base Megapack](https://www.fab.com/listings/61202d6c-1bc2-4e5d-b2d5-d005ea8b7c67) · **Use:** shotgun · model `SM_Gun_Shotgun` · 105 × 20 × 6 cm

A plain black pump-action shotgun.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by UE4-mannequin clips with a long gun: the Aliens Warrior pack's 47 (3 shots, a reload, aims in eight directions, moves), the Sci-Fi Characters pack's fire, crouch-walk and sprint with iron sights, and the rifle jog, sprint and crouch-walk that came with the Military, Cyber Characters and Monsters Underwater packs; and the UE5 template's rifle equip and reload (retargeted) (a shotgun has no third-person clips of its own).

<img src="images/objects/mc_environment_pump_shotgun_side.jpg" width="280" alt="Pump Shotgun, side view"> <img src="images/objects/mc_environment_pump_shotgun_quarter.jpg" width="280" alt="Pump Shotgun, three-quarter view"> <img src="images/objects/mc_environment_pump_shotgun_third.jpg" width="280" alt="Pump Shotgun, far three-quarter view">

#### Marine Rifle

[Military Pack](https://www.fab.com/listings/295db2f7-fb2e-4f28-9a6c-dcd8ab724747) · **Use:** battle rifle · model `SK_Rifle_05_Body` · 118 × 27 × 8 cm

A long black rifle with a rail handguard.

**Animations.** **Own:** a skeletal mesh (9 bones) without clips of its own. **Third person:** Held by UE4-mannequin clips with a long gun: the Aliens Warrior pack's 47 (3 shots, a reload, aims in eight directions, moves), the Sci-Fi Characters pack's fire, crouch-walk and sprint with iron sights, and the rifle jog, sprint and crouch-walk that came with the Military, Cyber Characters and Monsters Underwater packs; and the UE5 template's rifle equip and reload (retargeted).

<img src="images/objects/military_pack_marine_rifle_side.jpg" width="280" alt="Marine Rifle, side view"> <img src="images/objects/military_pack_marine_rifle_quarter.jpg" width="280" alt="Marine Rifle, three-quarter view"> <img src="images/objects/military_pack_marine_rifle_third.jpg" width="280" alt="Marine Rifle, far three-quarter view">

#### Tactical Rifle

[Female Soldiers (Pack)](https://www.fab.com/listings/ecdc02f6-a5e4-4ee2-8b16-1cd2112b543e) · **Use:** assault rifle · model `SK_Woman_05_Weapon_Full_01` · 101 × 40 × 9 cm

A tan-and-black rifle with a scope.

**Animations.** **Own:** a skeletal mesh (14 bones) without clips of its own. **Third person:** Held by UE4-mannequin clips with a long gun: the Aliens Warrior pack's 47 (3 shots, a reload, aims in eight directions, moves), the Sci-Fi Characters pack's fire, crouch-walk and sprint with iron sights, and the rifle jog, sprint and crouch-walk that came with the Military, Cyber Characters and Monsters Underwater packs; and the UE5 template's rifle equip and reload (retargeted).

<img src="images/objects/female_soldier_pack_riot_gun_side.jpg" width="280" alt="Tactical Rifle, side view"> <img src="images/objects/female_soldier_pack_riot_gun_quarter.jpg" width="280" alt="Tactical Rifle, three-quarter view"> <img src="images/objects/female_soldier_pack_riot_gun_third.jpg" width="280" alt="Tactical Rifle, far three-quarter view">

#### Dystopian Machine Gun

[Dystopia Soldiers (Pack)](https://www.fab.com/listings/3be8756a-724d-4fca-a67f-8442a1fcb833) · **Use:** heavy machine gun · model `SK_Machine_Gun_Full` · 86 × 47 × 40 cm

A twin-barrelled gun on a drum and tank housing.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by UE4-mannequin clips with a long gun: the Aliens Warrior pack's 47 (3 shots, a reload, aims in eight directions, moves), the Sci-Fi Characters pack's fire, crouch-walk and sprint with iron sights, and the rifle jog, sprint and crouch-walk that came with the Military, Cyber Characters and Monsters Underwater packs; and the UE5 template's rifle equip and reload (retargeted).

<img src="images/objects/dystopia_pack_dystopian_machine_gun_side.jpg" width="280" alt="Dystopian Machine Gun, side view"> <img src="images/objects/dystopia_pack_dystopian_machine_gun_quarter.jpg" width="280" alt="Dystopian Machine Gun, three-quarter view"> <img src="images/objects/dystopia_pack_dystopian_machine_gun_third.jpg" width="280" alt="Dystopian Machine Gun, far three-quarter view">

#### Dystopian Rifle

[Dystopia Soldiers (Pack)](https://www.fab.com/listings/3be8756a-724d-4fca-a67f-8442a1fcb833) · **Use:** submachine gun · model `SK_Weapon` · 83 × 26 × 9 cm

A short gun with a folding stock and a sling.

**Animations.** **Own:** a skeletal mesh (22 bones) without clips of its own. **Third person:** Held by UE4-mannequin clips with a long gun: the Aliens Warrior pack's 47 (3 shots, a reload, aims in eight directions, moves), the Sci-Fi Characters pack's fire, crouch-walk and sprint with iron sights, and the rifle jog, sprint and crouch-walk that came with the Military, Cyber Characters and Monsters Underwater packs; and the UE5 template's rifle equip and reload (retargeted).

<img src="images/objects/dystopia_pack_dystopian_rifle_side.jpg" width="280" alt="Dystopian Rifle, side view"> <img src="images/objects/dystopia_pack_dystopian_rifle_quarter.jpg" width="280" alt="Dystopian Rifle, three-quarter view"> <img src="images/objects/dystopia_pack_dystopian_rifle_third.jpg" width="280" alt="Dystopian Rifle, far three-quarter view">

#### Tommy Gun

[Old Gangster](https://www.fab.com/listings/0f896299-3dbd-447d-93b1-98da85ea2f81) · **Use:** submachine gun · model `SM_UE4_NPC_Old_gangster_Submachine_gun` · 86 × 23 × 17 cm

A drum-fed tommy gun with a wooden stock.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by UE4-mannequin clips with a long gun: the Aliens Warrior pack's 47 (3 shots, a reload, aims in eight directions, moves), the Sci-Fi Characters pack's fire, crouch-walk and sprint with iron sights, and the rifle jog, sprint and crouch-walk that came with the Military, Cyber Characters and Monsters Underwater packs; and the UE5 template's rifle equip and reload (retargeted).

<img src="images/objects/npc_old_gangster_tommy_gun_side.jpg" width="280" alt="Tommy Gun, side view"> <img src="images/objects/npc_old_gangster_tommy_gun_quarter.jpg" width="280" alt="Tommy Gun, three-quarter view"> <img src="images/objects/npc_old_gangster_tommy_gun_third.jpg" width="280" alt="Tommy Gun, far three-quarter view">

#### Double-Barrel Shotgun

[Customized Post Apocalyptic Characters](https://www.fab.com/listings/2f9e8f01-d369-4d32-939a-e22f4d3d60e8) · **Use:** shotgun · model `SM_Rifle` · 42 × 10 × 4 cm

A side-by-side shotgun with a blue-taped grip.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by UE4-mannequin clips with a long gun: the Aliens Warrior pack's 47 (3 shots, a reload, aims in eight directions, moves), the Sci-Fi Characters pack's fire, crouch-walk and sprint with iron sights, and the rifle jog, sprint and crouch-walk that came with the Military, Cyber Characters and Monsters Underwater packs; and the UE5 template's rifle equip and reload (retargeted) (a shotgun has no third-person clips of its own).

<img src="images/objects/megapost_character_scavenger_rifle_side.jpg" width="280" alt="Double-Barrel Shotgun, side view"> <img src="images/objects/megapost_character_scavenger_rifle_quarter.jpg" width="280" alt="Double-Barrel Shotgun, three-quarter view"> <img src="images/objects/megapost_character_scavenger_rifle_third.jpg" width="280" alt="Double-Barrel Shotgun, far three-quarter view">

#### Lever-Action Shotgun

[Post-Apocalyptic Characters (Pack)](https://www.fab.com/listings/3e123c6d-c51c-4fb6-b787-1e386d637143) · **Use:** shotgun · model `SM_Weapon` · 79 × 18 × 3 cm

A long lever-action shotgun with a red wooden stock.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by UE4-mannequin clips with a long gun: the Aliens Warrior pack's 47 (3 shots, a reload, aims in eight directions, moves), the Sci-Fi Characters pack's fire, crouch-walk and sprint with iron sights, and the rifle jog, sprint and crouch-walk that came with the Military, Cyber Characters and Monsters Underwater packs; and the UE5 template's rifle equip and reload (retargeted) (a shotgun has no third-person clips of its own).

<img src="images/objects/post_apocalypse_pack_wasteland_rifle_side.jpg" width="280" alt="Lever-Action Shotgun, side view"> <img src="images/objects/post_apocalypse_pack_wasteland_rifle_quarter.jpg" width="280" alt="Lever-Action Shotgun, three-quarter view"> <img src="images/objects/post_apocalypse_pack_wasteland_rifle_third.jpg" width="280" alt="Lever-Action Shotgun, far three-quarter view">

### Sniper rifles and launchers

#### Large-Calibre Sniper Rifle (FPS)

[FPS Sniper Rifle Large Calibre (Animations)](https://www.fab.com/listings/9860c746-58de-4c1c-8cdf-70a267c8aa6d) · **Use:** anti-materiel rifle · model `SK_Sniper_Rifle_Full` · 166 × 33 × 13 cm

A long tan .50-calibre rifle with a big scope and muzzle brake.

**Animations.** **Own:** a skeletal mesh (18 bones) with 1 clip of its own: rifle shot. **First person:** First-person arm clips: 22 in FPS Sniper Rifle Large Calibre: 4 attacks, 4 idles, 4 jumps and falls, 5 moves, 5 other (hands sniper rifle get weapon, hands sniper rifle hide, hands sniper rifle inspection cartridge, hands sniper rifle inspection weapon, hands sniper rifle reload). **Third person:** Held by UE4-mannequin clips with a long gun: the Aliens Warrior pack's 47 (3 shots, a reload, aims in eight directions, moves), the Sci-Fi Characters pack's fire, crouch-walk and sprint with iron sights, and the rifle jog, sprint and crouch-walk that came with the Military, Cyber Characters and Monsters Underwater packs; and the UE5 template's rifle equip and reload (retargeted) (no third-person sniper clips).

<img src="images/objects/fps_sniper_rifle_large_calibre_sniper_rifle_fps_side.jpg" width="280" alt="Large-Calibre Sniper Rifle (FPS), side view"> <img src="images/objects/fps_sniper_rifle_large_calibre_sniper_rifle_fps_quarter.jpg" width="280" alt="Large-Calibre Sniper Rifle (FPS), three-quarter view"> <img src="images/objects/fps_sniper_rifle_large_calibre_sniper_rifle_fps_third.jpg" width="280" alt="Large-Calibre Sniper Rifle (FPS), a frame of its clip">

#### Camouflaged Sniper Rifle (FPS)

[FPS Sniper Rifle 03 (Animations)](https://www.fab.com/listings/296631a1-03df-44d1-b494-9a8a1a167708) · **Use:** sniper rifle · model `SK_Sniper_Rifle_03_Full` · 143 × 34 × 16 cm

A sniper rifle wrapped in ghillie strips.

**Animations.** **Own:** a skeletal mesh (12 bones) with 1 clip of its own: rifle 03 shot. **First person:** First-person arm clips: 24 in FPS Sniper Rifle 03: 5 attacks, 4 idles, 4 jumps and falls, 6 moves, 5 other (rifle 03 get weapon, rifle 03 hide, rifle 03 inspection cartridge, rifle 03 inspection weapon, rifle 03 reload). **Third person:** Held by UE4-mannequin clips with a long gun: the Aliens Warrior pack's 47 (3 shots, a reload, aims in eight directions, moves), the Sci-Fi Characters pack's fire, crouch-walk and sprint with iron sights, and the rifle jog, sprint and crouch-walk that came with the Military, Cyber Characters and Monsters Underwater packs; and the UE5 template's rifle equip and reload (retargeted) (no third-person sniper clips).

<img src="images/objects/fps_sniper_rifle_03_camouflaged_sniper_rifle_fps_side.jpg" width="280" alt="Camouflaged Sniper Rifle (FPS), side view"> <img src="images/objects/fps_sniper_rifle_03_camouflaged_sniper_rifle_fps_quarter.jpg" width="280" alt="Camouflaged Sniper Rifle (FPS), three-quarter view"> <img src="images/objects/fps_sniper_rifle_03_camouflaged_sniper_rifle_fps_third.jpg" width="280" alt="Camouflaged Sniper Rifle (FPS), a frame of its clip">

#### Bipod Sniper Rifle

[Sniper Soldier](https://www.fab.com/listings/70c21220-f9a1-4c3c-8bc2-699508be793f) · **Use:** sniper rifle · model `SK_Sniper_Rifle` · 143 × 34 × 12 cm

A long green rifle with a bipod, scope and silencer.

**Animations.** **Own:** a skeletal mesh (12 bones) without clips of its own. **Third person:** Held by UE4-mannequin clips with a long gun: the Aliens Warrior pack's 47 (3 shots, a reload, aims in eight directions, moves), the Sci-Fi Characters pack's fire, crouch-walk and sprint with iron sights, and the rifle jog, sprint and crouch-walk that came with the Military, Cyber Characters and Monsters Underwater packs; and the UE5 template's rifle equip and reload (retargeted) (no third-person sniper clips).

<img src="images/objects/sniper_ghillie_sniper_rifle_side.jpg" width="280" alt="Bipod Sniper Rifle, side view"> <img src="images/objects/sniper_ghillie_sniper_rifle_quarter.jpg" width="280" alt="Bipod Sniper Rifle, three-quarter view"> <img src="images/objects/sniper_ghillie_sniper_rifle_third.jpg" width="280" alt="Bipod Sniper Rifle, far three-quarter view">

#### Hunting Rifle

[Adventure Characters (Pack)](https://www.fab.com/listings/db81464d-fcb5-43a8-b309-5555c392be3a) · **Use:** marksman rifle · model `SK_Sniper_Rifle_Full` · 136 × 29 × 8 cm

A scoped rifle with a thumbhole stock and rag-wrapped barrel.

**Animations.** **Own:** a skeletal mesh (12 bones) without clips of its own. **Third person:** Held by UE4-mannequin clips with a long gun: the Aliens Warrior pack's 47 (3 shots, a reload, aims in eight directions, moves), the Sci-Fi Characters pack's fire, crouch-walk and sprint with iron sights, and the rifle jog, sprint and crouch-walk that came with the Military, Cyber Characters and Monsters Underwater packs; and the UE5 template's rifle equip and reload (retargeted) (no third-person sniper clips).

<img src="images/objects/adventures_pack_hunting_rifle_side.jpg" width="280" alt="Hunting Rifle, side view"> <img src="images/objects/adventures_pack_hunting_rifle_quarter.jpg" width="280" alt="Hunting Rifle, three-quarter view"> <img src="images/objects/adventures_pack_hunting_rifle_third.jpg" width="280" alt="Hunting Rifle, far three-quarter view">

#### Rocket Launcher (FPS)

[FPS Rocket Launcher Animations](https://www.fab.com/listings/93bd04a5-1ea9-4d26-98d8-80577c201ec5) · **Use:** rocket launcher · model `SK_Rocket_Launcher` · 103 × 34 × 14 cm

A shoulder-fired RPG launcher with a wooden heat guard.

**Animations.** **Own:** a skeletal mesh (8 bones) without clips of its own. **First person:** First-person arm clips: 23 in FPS Rocket Launcher: 5 attacks, 4 idles, 4 jumps and falls, 6 moves, 4 other (launcher get weapon, launcher hide, launcher inspection weapon, launcher reload). **Third person:** Held by [Launcher Animations](https://www.fab.com/listings/8556b5ba-9c44-4004-a0b5-7366e57ec888) (59 third-person clips with a shoulder launcher: attacks, reloads, moves).

<img src="images/objects/fps_rocket_launcher_rocket_launcher_fps_side.jpg" width="280" alt="Rocket Launcher (FPS), side view"> <img src="images/objects/fps_rocket_launcher_rocket_launcher_fps_quarter.jpg" width="280" alt="Rocket Launcher (FPS), three-quarter view"> <img src="images/objects/fps_rocket_launcher_rocket_launcher_fps_third.jpg" width="280" alt="Rocket Launcher (FPS), far three-quarter view">

### Pistols and revolvers

#### Pistol (FPS)

[FPS Pistol (Single)](https://www.fab.com/listings/fd81af73-be14-4b89-894d-fb3cfd5e2b67) · **Use:** pistol · model `SK_Pistol` · 23 × 17 × 5 cm

A green-framed polymer pistol (the Tarantula).

**Animations.** **Own:** a skeletal mesh (14 bones) with 3 clips of its own: get weapon, reload, shot. **First person:** First-person arm clips: 36 in FPS Pistol (Single): 8 attacks, 1 hit reaction, 6 idles, 4 jumps and falls, 8 moves, 9 other (single get weapon, single hands up, single hide, single inspection cartridge, single lie down on the ground, ...). **Third person:** Held by the UE5 template's pistol clips (`MF_Pistol_*`, `MM_Pistol_*`: idle, aim, fire, reload; retargeted).

<img src="images/objects/fps_pistol_single_pistol_fps_side.jpg" width="280" alt="Pistol (FPS), side view"> <img src="images/objects/fps_pistol_single_pistol_fps_quarter.jpg" width="280" alt="Pistol (FPS), three-quarter view"> <img src="images/objects/fps_pistol_single_pistol_fps_third.jpg" width="280" alt="Pistol (FPS), far three-quarter view">

#### Service Pistol

[Military Base Megapack](https://www.fab.com/listings/61202d6c-1bc2-4e5d-b2d5-d005ea8b7c67) · **Use:** pistol · model `SM_Gun_Pistol` · 19 × 13 × 3 cm

A worn black service pistol.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by the UE5 template's pistol clips (`MF_Pistol_*`, `MM_Pistol_*`: idle, aim, fire, reload; retargeted).

<img src="images/objects/mc_environment_service_pistol_side.jpg" width="280" alt="Service Pistol, side view"> <img src="images/objects/mc_environment_service_pistol_quarter.jpg" width="280" alt="Service Pistol, three-quarter view"> <img src="images/objects/mc_environment_service_pistol_third.jpg" width="280" alt="Service Pistol, far three-quarter view">

#### Silenced Revolver

[Adventure Characters (Pack)](https://www.fab.com/listings/db81464d-fcb5-43a8-b309-5555c392be3a) · **Use:** revolver · model `SK_Gun_Full` · 49 × 19 × 6 cm

A revolver with a wrapped grip and a long perforated silencer.

**Animations.** **Own:** a skeletal mesh (10 bones) without clips of its own. **Third person:** Held by the UE5 template's pistol clips (`MF_Pistol_*`, `MM_Pistol_*`: idle, aim, fire, reload; retargeted).

<img src="images/objects/adventures_pack_adventurer_s_pistol_side.jpg" width="280" alt="Silenced Revolver, side view"> <img src="images/objects/adventures_pack_adventurer_s_pistol_quarter.jpg" width="280" alt="Silenced Revolver, three-quarter view"> <img src="images/objects/adventures_pack_adventurer_s_pistol_third.jpg" width="280" alt="Silenced Revolver, far three-quarter view">

#### Long-Barrel Revolver

[NPC Sailor (Adventure)](https://www.fab.com/listings/e33244ec-02db-4d09-a96f-9cb11ec5f69a) · **Use:** revolver · model `SM_UE4_NPC_Sailor_custom_Gun` · 31 × 17 × 5 cm

A long-barrelled revolver with a white grip.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by the UE5 template's pistol clips (`MF_Pistol_*`, `MM_Pistol_*`: idle, aim, fire, reload; retargeted).

<img src="images/objects/npc_sailor_custom_flintlock_pistol_side.jpg" width="280" alt="Long-Barrel Revolver, side view"> <img src="images/objects/npc_sailor_custom_flintlock_pistol_quarter.jpg" width="280" alt="Long-Barrel Revolver, three-quarter view"> <img src="images/objects/npc_sailor_custom_flintlock_pistol_third.jpg" width="280" alt="Long-Barrel Revolver, far three-quarter view">

#### Flare Pistol

[Customized Post Apocalyptic Characters](https://www.fab.com/listings/2f9e8f01-d369-4d32-939a-e22f4d3d60e8) · **Use:** signal pistol · model `SM_Gun_02` · 27 × 20 × 4 cm

A short, wide-bored flare pistol.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by the UE5 template's pistol clips (`MF_Pistol_*`, `MM_Pistol_*`: idle, aim, fire, reload; retargeted).

<img src="images/objects/megapost_character_sawn_off_side.jpg" width="280" alt="Flare Pistol, side view"> <img src="images/objects/megapost_character_sawn_off_quarter.jpg" width="280" alt="Flare Pistol, three-quarter view"> <img src="images/objects/megapost_character_sawn_off_third.jpg" width="280" alt="Flare Pistol, far three-quarter view">

#### Old Revolver

[Safe House VOL.1 - Supplies and Guns (Nanite and Low Poly)](https://www.fab.com/listings/46c37125-b9e2-48f1-a5a2-a432959da27f) · **Use:** revolver · model `SM_Pistol_34a` · 21 × 11 × 3 cm

A worn revolver with a wooden grip.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by the UE5 template's pistol clips (`MF_Pistol_*`, `MM_Pistol_*`: idle, aim, fire, reload; retargeted).

<img src="images/objects/safehouse_semi_automatic_pistol_side.jpg" width="280" alt="Old Revolver, side view"> <img src="images/objects/safehouse_semi_automatic_pistol_quarter.jpg" width="280" alt="Old Revolver, three-quarter view"> <img src="images/objects/safehouse_semi_automatic_pistol_third.jpg" width="280" alt="Old Revolver, far three-quarter view">

#### Magnum Revolver

[Safe House VOL.1 - Supplies and Guns (Nanite and Low Poly)](https://www.fab.com/listings/46c37125-b9e2-48f1-a5a2-a432959da27f) · **Use:** revolver · model `SM_Revolver_12a` · 27 × 17 × 5 cm

A heavy revolver with a checkered wooden grip.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by the UE5 template's pistol clips (`MF_Pistol_*`, `MM_Pistol_*`: idle, aim, fire, reload; retargeted).

<img src="images/objects/safehouse_revolver_side.jpg" width="280" alt="Magnum Revolver, side view"> <img src="images/objects/safehouse_revolver_quarter.jpg" width="280" alt="Magnum Revolver, three-quarter view"> <img src="images/objects/safehouse_revolver_third.jpg" width="280" alt="Magnum Revolver, far three-quarter view">

### Knives, melee weapons and grenades

#### Scrap Club

[Post-Apocalyptic Characters (Pack)](https://www.fab.com/listings/3e123c6d-c51c-4fb6-b787-1e386d637143) · **Use:** club · model `SM_Weapon_01` · 92 × 35 × 6 cm

A rag-wrapped club with a blade bound on, a ring at its end.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Swung by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs), or one-handed by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves).

<img src="images/objects/post_apocalypse_pack_scrap_gun_side.jpg" width="280" alt="Scrap Club, side view"> <img src="images/objects/post_apocalypse_pack_scrap_gun_quarter.jpg" width="280" alt="Scrap Club, three-quarter view"> <img src="images/objects/post_apocalypse_pack_scrap_gun_third.jpg" width="280" alt="Scrap Club, far three-quarter view">

#### Combat Knife (FPS)

[FPS Pistol And Knife Animations](https://www.fab.com/listings/daffc36a-8fb6-4b0b-9b1a-75bb72020184) · **Use:** knife · model `SM_Knife` · 37 × 8 × 3 cm

A fighting knife with a stacked-leather grip.

**Animations.** **Own:** a static mesh, no clips of its own. **First person:** First-person arm clips: 31 in FPS Pistol And Knife: 8 attacks, 1 hit reaction, 5 idles, 4 jumps and falls, 6 moves, 7 other (knife get weapon, knife hide, knife inspect cartridge, knife reload, knife weapon inspection). **Third person:** No third-person knife clips in the project.

<img src="images/objects/fps_pistol_knife_combat_knife_fps_side.jpg" width="280" alt="Combat Knife (FPS), side view"> <img src="images/objects/fps_pistol_knife_combat_knife_fps_quarter.jpg" width="280" alt="Combat Knife (FPS), three-quarter view"> <img src="images/objects/fps_pistol_knife_combat_knife_fps_third.jpg" width="280" alt="Combat Knife (FPS), far three-quarter view">

#### Survival Knife (FPS)

[FPS STARTER (PACK)](https://www.fab.com/listings/afe92192-dd5c-4bb0-a476-0c09646d897d) · **Use:** knife · model `SM_Knife_01` · 36 × 7 × 2 cm

A dark drop-point knife with a contoured grip.

**Animations.** **Own:** a static mesh, no clips of its own. **First person:** First-person arm clips: 14 in FPS Starter Pack (knife): 5 attacks, 1 hit reaction, 2 idles, 1 jump or fall, 2 moves, 3 other (knife block, knife down, knife up). **Third person:** No third-person knife clips in the project.

<img src="images/objects/fps_starter_pack_kitchen_knife_fps_side.jpg" width="280" alt="Survival Knife (FPS), side view"> <img src="images/objects/fps_starter_pack_kitchen_knife_fps_quarter.jpg" width="280" alt="Survival Knife (FPS), three-quarter view"> <img src="images/objects/fps_starter_pack_kitchen_knife_fps_third.jpg" width="280" alt="Survival Knife (FPS), far three-quarter view">

#### Tactical Axe (FPS)

[FPS STARTER (PACK)](https://www.fab.com/listings/afe92192-dd5c-4bb0-a476-0c09646d897d) · **Use:** axe · model `SM_Axe_01` · 48 × 19 × 3 cm

A black tactical tomahawk.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Swung by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs), or one-handed by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves).

<img src="images/objects/fps_starter_pack_fire_axe_fps_side.jpg" width="280" alt="Tactical Axe (FPS), side view"> <img src="images/objects/fps_starter_pack_fire_axe_fps_quarter.jpg" width="280" alt="Tactical Axe (FPS), three-quarter view"> <img src="images/objects/fps_starter_pack_fire_axe_fps_third.jpg" width="280" alt="Tactical Axe (FPS), far three-quarter view">

#### Ice Axe (FPS)

[FPS STARTER (PACK)](https://www.fab.com/listings/afe92192-dd5c-4bb0-a476-0c09646d897d) · **Use:** axe · model `SM_Ice_Axe` · 55 × 33 × 3 cm

A curved red ice axe.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Swung by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs), or one-handed by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves).

<img src="images/objects/fps_starter_pack_ice_axe_fps_side.jpg" width="280" alt="Ice Axe (FPS), side view"> <img src="images/objects/fps_starter_pack_ice_axe_fps_quarter.jpg" width="280" alt="Ice Axe (FPS), three-quarter view"> <img src="images/objects/fps_starter_pack_ice_axe_fps_third.jpg" width="280" alt="Ice Axe (FPS), far three-quarter view">

#### Nail Bat (FPS)

[FPS STARTER (PACK)](https://www.fab.com/listings/afe92192-dd5c-4bb0-a476-0c09646d897d) · **Use:** club · model `SM_Bita` · 80 × 18 × 16 cm

A wooden bat studded with nails.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Swung by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs), or one-handed by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves).

<img src="images/objects/fps_starter_pack_baseball_bat_fps_side.jpg" width="280" alt="Nail Bat (FPS), side view"> <img src="images/objects/fps_starter_pack_baseball_bat_fps_quarter.jpg" width="280" alt="Nail Bat (FPS), three-quarter view"> <img src="images/objects/fps_starter_pack_baseball_bat_fps_third.jpg" width="280" alt="Nail Bat (FPS), far three-quarter view">

#### Stun Gun (FPS)

[FPS STARTER (PACK)](https://www.fab.com/listings/afe92192-dd5c-4bb0-a476-0c09646d897d) · **Use:** stun gun · model `SK_Stun_Gun` · 36 × 12 × 5 cm

A black handheld stun gun with a wrist strap.

**Animations.** **Own:** a skeletal mesh (5 bones) without clips of its own. **First person:** First-person arm clips: 12 in FPS Starter Pack (stun gun): 3 attacks, 1 hit reaction, 3 idles, 1 jump or fall, 2 moves, 2 other (stun gun down, stun gun up). **Third person:** Swung by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs), or one-handed by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves).

<img src="images/objects/fps_starter_pack_stun_gun_fps_side.jpg" width="280" alt="Stun Gun (FPS), side view"> <img src="images/objects/fps_starter_pack_stun_gun_fps_quarter.jpg" width="280" alt="Stun Gun (FPS), three-quarter view"> <img src="images/objects/fps_starter_pack_stun_gun_fps_third.jpg" width="280" alt="Stun Gun (FPS), far three-quarter view">

#### Riot Shield and Club (FPS)

[FPS STARTER (PACK)](https://www.fab.com/listings/afe92192-dd5c-4bb0-a476-0c09646d897d) · **Use:** shield and club · model `SK_Shield_Full` and 1 more meshes · 122 × 48 × 29 cm

A canvas-covered riot shield with a viewport (its club alongside).

**Animations.** **Own:** a skeletal mesh (1 bone) without clips of its own. **First person:** First-person arm clips: 13 in FPS Starter Pack (shield and club): 5 attacks, 1 hit reaction, 2 idles, 1 jump or fall, 2 moves, 2 other (shield and club down, shield and club up). **Third person:** Carried by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves) and [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/fps_starter_pack_riot_shield_and_club_fps_side.jpg" width="280" alt="Riot Shield and Club (FPS), side view"> <img src="images/objects/fps_starter_pack_riot_shield_and_club_fps_quarter.jpg" width="280" alt="Riot Shield and Club (FPS), three-quarter view"> <img src="images/objects/fps_starter_pack_riot_shield_and_club_fps_third.jpg" width="280" alt="Riot Shield and Club (FPS), far three-quarter view">

#### Ballistic Shield (FPS)

[FPS ANIMATIONS PISTOL (TACTICAL SHIELD)](https://www.fab.com/listings/9f81d42c-fbe9-49e6-aa6b-a227edb3f36f) · **Use:** ballistic shield · model `SK_Shield_Full` · 121 × 48 × 29 cm

A khaki ballistic shield with a window and lights.

**Animations.** **Own:** a skeletal mesh (1 bone) without clips of its own. **First person:** First-person arm clips: 24 in FPS Pistol (Tactical Shield): 6 attacks, 1 hit reaction, 5 idles, 1 jump or fall, 6 moves, 5 other (shield get weapon, shield hide, shield reload, shield weapon inspection). **Third person:** Carried by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves) and [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/fps_pistol_shield_ballistic_shield_fps_side.jpg" width="280" alt="Ballistic Shield (FPS), side view"> <img src="images/objects/fps_pistol_shield_ballistic_shield_fps_quarter.jpg" width="280" alt="Ballistic Shield (FPS), three-quarter view"> <img src="images/objects/fps_pistol_shield_ballistic_shield_fps_third.jpg" width="280" alt="Ballistic Shield (FPS), far three-quarter view">

#### Baseball Bat

[Old Gangster](https://www.fab.com/listings/0f896299-3dbd-447d-93b1-98da85ea2f81) · **Use:** club · model `SM_UE4_NPC_Old_gangster_Baseball_bat` · 71 × 6 × 6 cm

A blood-stained wooden baseball bat.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Swung by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs), or one-handed by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves).

<img src="images/objects/npc_old_gangster_baseball_bat_side.jpg" width="280" alt="Baseball Bat, side view"> <img src="images/objects/npc_old_gangster_baseball_bat_quarter.jpg" width="280" alt="Baseball Bat, three-quarter view"> <img src="images/objects/npc_old_gangster_baseball_bat_third.jpg" width="280" alt="Baseball Bat, far three-quarter view">

#### Butcher's Cleaver

[Old Gangster](https://www.fab.com/listings/0f896299-3dbd-447d-93b1-98da85ea2f81) · **Use:** cleaver · model `SM_UE4_NPC_Old_gangster_Cleaver` · 55 × 16 × 2 cm

A large meat cleaver.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Swung by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs), or one-handed by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves).

<img src="images/objects/npc_old_gangster_butcher_s_cleaver_side.jpg" width="280" alt="Butcher's Cleaver, side view"> <img src="images/objects/npc_old_gangster_butcher_s_cleaver_quarter.jpg" width="280" alt="Butcher's Cleaver, three-quarter view"> <img src="images/objects/npc_old_gangster_butcher_s_cleaver_third.jpg" width="280" alt="Butcher's Cleaver, far three-quarter view">

#### Baton

[Adventure Characters (Pack)](https://www.fab.com/listings/db81464d-fcb5-43a8-b309-5555c392be3a) · **Use:** baton · model `SM_Club` · 68 × 4 × 4 cm

A black police baton.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Swung by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs), or one-handed by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves).

<img src="images/objects/adventures_pack_spiked_club_side.jpg" width="280" alt="Baton, side view"> <img src="images/objects/adventures_pack_spiked_club_quarter.jpg" width="280" alt="Baton, three-quarter view"> <img src="images/objects/adventures_pack_spiked_club_third.jpg" width="280" alt="Baton, far three-quarter view">

#### Crowbar

[Post-Apocalyptic Characters (Pack)](https://www.fab.com/listings/3e123c6d-c51c-4fb6-b787-1e386d637143) · **Use:** crowbar · model `SM_Crazy_Weapon` · 84 × 19 × 4 cm

A red crowbar.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Swung by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs), or one-handed by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves).

<img src="images/objects/post_apocalypse_pack_crazy_s_weapon_side.jpg" width="280" alt="Crowbar, side view"> <img src="images/objects/post_apocalypse_pack_crazy_s_weapon_quarter.jpg" width="280" alt="Crowbar, three-quarter view"> <img src="images/objects/post_apocalypse_pack_crazy_s_weapon_third.jpg" width="280" alt="Crowbar, far three-quarter view">

#### Bloody Cleaver

[Post-Apocalyptic Characters (Pack)](https://www.fab.com/listings/3e123c6d-c51c-4fb6-b787-1e386d637143) · **Use:** cleaver · model `SM_Backsword` · 43 × 12 × 3 cm

A blood-smeared cleaver.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Swung by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs), or one-handed by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves).

<img src="images/objects/post_apocalypse_pack_backsword_side.jpg" width="280" alt="Bloody Cleaver, side view"> <img src="images/objects/post_apocalypse_pack_backsword_quarter.jpg" width="280" alt="Bloody Cleaver, three-quarter view"> <img src="images/objects/post_apocalypse_pack_backsword_third.jpg" width="280" alt="Bloody Cleaver, far three-quarter view">

#### Kukri

[Military Pack](https://www.fab.com/listings/295db2f7-fb2e-4f28-9a6c-dcd8ab724747) · **Use:** knife · model `SM_Knife` · 54 × 8 × 3 cm

A curved black kukri.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** No third-person knife clips in the project.

<img src="images/objects/military_pack_military_knife_side.jpg" width="280" alt="Kukri, side view"> <img src="images/objects/military_pack_military_knife_quarter.jpg" width="280" alt="Kukri, three-quarter view"> <img src="images/objects/military_pack_military_knife_third.jpg" width="280" alt="Kukri, far three-quarter view">

#### Sniper's Knife

[Sniper Soldier](https://www.fab.com/listings/70c21220-f9a1-4c3c-8bc2-699508be793f) · **Use:** knife · model `SM_Sniper_Knife_02` · 33 × 5 × 2 cm

A plain combat knife with a leather grip.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** No third-person knife clips in the project.

<img src="images/objects/sniper_sniper_s_knife_side.jpg" width="280" alt="Sniper's Knife, side view"> <img src="images/objects/sniper_sniper_s_knife_quarter.jpg" width="280" alt="Sniper's Knife, three-quarter view"> <img src="images/objects/sniper_sniper_s_knife_third.jpg" width="280" alt="Sniper's Knife, far three-quarter view">

#### Frag Grenade

[Military Pack](https://www.fab.com/listings/295db2f7-fb2e-4f28-9a6c-dcd8ab724747) · **Use:** grenade · model `SM_Grenade_Mesh` · 14 × 8 × 8 cm

An olive fragmentation grenade.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** No throwing clips in the project.

<img src="images/objects/military_pack_frag_grenade_side.jpg" width="280" alt="Frag Grenade, side view"> <img src="images/objects/military_pack_frag_grenade_quarter.jpg" width="280" alt="Frag Grenade, three-quarter view"> <img src="images/objects/military_pack_frag_grenade_third.jpg" width="280" alt="Frag Grenade, far three-quarter view">

#### Stick Grenade

[Dystopia Soldiers (Pack)](https://www.fab.com/listings/3be8756a-724d-4fca-a67f-8442a1fcb833) · **Use:** grenade · model `SM_Grenade` · 31 × 7 × 7 cm

A green stick grenade with a wooden handle.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** No throwing clips in the project.

<img src="images/objects/dystopia_pack_dystopian_grenade_side.jpg" width="280" alt="Stick Grenade, side view"> <img src="images/objects/dystopia_pack_dystopian_grenade_quarter.jpg" width="280" alt="Stick Grenade, three-quarter view"> <img src="images/objects/dystopia_pack_dystopian_grenade_third.jpg" width="280" alt="Stick Grenade, far three-quarter view">

#### Rocket

[Military Pack](https://www.fab.com/listings/295db2f7-fb2e-4f28-9a6c-dcd8ab724747) · **Use:** ammunition · model `SM_Rocket_Rocket_mesh` · 42 × 7 × 7 cm

A white rocket with a yellow nose.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/military_pack_rocket_side.jpg" width="280" alt="Rocket, side view"> <img src="images/objects/military_pack_rocket_quarter.jpg" width="280" alt="Rocket, three-quarter view"> <img src="images/objects/military_pack_rocket_third.jpg" width="280" alt="Rocket, far three-quarter view">

## Futuristic weapons

Sci-fi guns, arm cannons, energy blades and shields of the sci-fi, alien and dystopian packs.

### Energy and sci-fi guns

#### Defender's Cannon

[Sci-Fi Characters (Pack) Vol.2](https://www.fab.com/listings/d919d2b9-72be-4f86-a715-b8ce18e415f1) · **Use:** heavy gun · model `SK_Defender_Weapon` · 140 × 72 × 54 cm

A bulky black-and-yellow arm cannon.

**Animations.** **Own:** a skeletal mesh (6 bones) with 1 clip of its own: rotation. **Third person:** Held by UE4-mannequin clips with a long gun: the Aliens Warrior pack's 47 (3 shots, a reload, aims in eight directions, moves), the Sci-Fi Characters pack's fire, crouch-walk and sprint with iron sights, and the rifle jog, sprint and crouch-walk that came with the Military, Cyber Characters and Monsters Underwater packs; and the UE5 template's rifle equip and reload (retargeted).

<img src="images/objects/sci_fi_characters_pack_vol_2_defender_s_cannon_side.jpg" width="280" alt="Defender's Cannon, side view"> <img src="images/objects/sci_fi_characters_pack_vol_2_defender_s_cannon_quarter.jpg" width="280" alt="Defender's Cannon, three-quarter view"> <img src="images/objects/sci_fi_characters_pack_vol_2_defender_s_cannon_third.jpg" width="280" alt="Defender's Cannon, far three-quarter view">

#### Bounty Hunter's Pistol

[Sci-Fi Mercenaries Pack](https://www.fab.com/listings/e0efc01c-ad86-428c-9103-d1f92c80db40) · **Use:** heavy pistol · model `SK_Head_Hunter_Gun` · 36 × 17 × 5 cm

A gold-engraved revolver-blaster.

**Animations.** **Own:** a skeletal mesh (5 bones) without clips of its own. **Third person:** Held by the UE5 template's pistol clips (`MF_Pistol_*`, `MM_Pistol_*`: idle, aim, fire, reload; retargeted).

<img src="images/objects/sci_fi_mercenary_pack_bounty_hunter_s_pistol_side.jpg" width="280" alt="Bounty Hunter's Pistol, side view"> <img src="images/objects/sci_fi_mercenary_pack_bounty_hunter_s_pistol_quarter.jpg" width="280" alt="Bounty Hunter's Pistol, three-quarter view"> <img src="images/objects/sci_fi_mercenary_pack_bounty_hunter_s_pistol_third.jpg" width="280" alt="Bounty Hunter's Pistol, far three-quarter view">

#### Marauder Rifle

[Sci-Fi Mercenaries Pack](https://www.fab.com/listings/e0efc01c-ad86-428c-9103-d1f92c80db40) · **Use:** rifle · model `SK_Marauder_Rifle_Full` · 89 × 37 × 22 cm

A chunky yellow-and-grey rifle with a big magazine.

**Animations.** **Own:** a skeletal mesh (8 bones) without clips of its own. **Third person:** Held by UE4-mannequin clips with a long gun: the Aliens Warrior pack's 47 (3 shots, a reload, aims in eight directions, moves), the Sci-Fi Characters pack's fire, crouch-walk and sprint with iron sights, and the rifle jog, sprint and crouch-walk that came with the Military, Cyber Characters and Monsters Underwater packs; and the UE5 template's rifle equip and reload (retargeted).

<img src="images/objects/sci_fi_mercenary_pack_marauder_rifle_side.jpg" width="280" alt="Marauder Rifle, side view"> <img src="images/objects/sci_fi_mercenary_pack_marauder_rifle_quarter.jpg" width="280" alt="Marauder Rifle, three-quarter view"> <img src="images/objects/sci_fi_mercenary_pack_marauder_rifle_third.jpg" width="280" alt="Marauder Rifle, far three-quarter view">

#### Robot's Arm Guns

[Sci-Fi Mercenaries Pack](https://www.fab.com/listings/e0efc01c-ad86-428c-9103-d1f92c80db40) · **Use:** twin guns · model `SK_Robot_Weapons` · 156 × 75 × 32 cm

Two camouflaged gun barrels for a robot's arms.

**Animations.** **Own:** a part skinned to its character's skeleton (68 bones): it moves with that character's clips. **Third person:** Held by UE4-mannequin clips with a long gun: the Aliens Warrior pack's 47 (3 shots, a reload, aims in eight directions, moves), the Sci-Fi Characters pack's fire, crouch-walk and sprint with iron sights, and the rifle jog, sprint and crouch-walk that came with the Military, Cyber Characters and Monsters Underwater packs; and the UE5 template's rifle equip and reload (retargeted).

<img src="images/objects/sci_fi_mercenary_pack_robot_s_arm_guns_side.jpg" width="280" alt="Robot's Arm Guns, side view"> <img src="images/objects/sci_fi_mercenary_pack_robot_s_arm_guns_quarter.jpg" width="280" alt="Robot's Arm Guns, three-quarter view"> <img src="images/objects/sci_fi_mercenary_pack_robot_s_arm_guns_third.jpg" width="280" alt="Robot's Arm Guns, far three-quarter view">

#### Alien Sniper Rifle

[Aliens Warrior (Pack)](https://www.fab.com/listings/a683cdf2-a1b1-4c35-b788-eeae62c2ed37) · **Use:** sniper rifle · model `SK_Sci_Fi_Automatic_Sniper_Rifle_Full` · 114 × 27 × 7 cm

A long black-and-gold sniper rifle with a scope.

**Animations.** **Own:** a skeletal mesh (8 bones) without clips of its own. **Third person:** Held by UE4-mannequin clips with a long gun: the Aliens Warrior pack's 47 (3 shots, a reload, aims in eight directions, moves), the Sci-Fi Characters pack's fire, crouch-walk and sprint with iron sights, and the rifle jog, sprint and crouch-walk that came with the Military, Cyber Characters and Monsters Underwater packs; and the UE5 template's rifle equip and reload (retargeted) (no third-person sniper clips).

<img src="images/objects/aliens_warrior_pack_alien_sniper_rifle_side.jpg" width="280" alt="Alien Sniper Rifle, side view"> <img src="images/objects/aliens_warrior_pack_alien_sniper_rifle_quarter.jpg" width="280" alt="Alien Sniper Rifle, three-quarter view"> <img src="images/objects/aliens_warrior_pack_alien_sniper_rifle_third.jpg" width="280" alt="Alien Sniper Rifle, far three-quarter view">

#### Alien Blaster

[Aliens Warrior (Pack)](https://www.fab.com/listings/a683cdf2-a1b1-4c35-b788-eeae62c2ed37) · **Use:** rifle · model `SM_UE4_Alien_Weapon_01` · 119 × 40 × 17 cm

A sleek green alien rifle with vents along its barrel.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by UE4-mannequin clips with a long gun: the Aliens Warrior pack's 47 (3 shots, a reload, aims in eight directions, moves), the Sci-Fi Characters pack's fire, crouch-walk and sprint with iron sights, and the rifle jog, sprint and crouch-walk that came with the Military, Cyber Characters and Monsters Underwater packs; and the UE5 template's rifle equip and reload (retargeted).

<img src="images/objects/aliens_warrior_pack_alien_blaster_side.jpg" width="280" alt="Alien Blaster, side view"> <img src="images/objects/aliens_warrior_pack_alien_blaster_quarter.jpg" width="280" alt="Alien Blaster, three-quarter view"> <img src="images/objects/aliens_warrior_pack_alien_blaster_third.jpg" width="280" alt="Alien Blaster, far three-quarter view">

#### Future Assault Rifle

[Soldier Future 01](https://www.fab.com/listings/74bb0b33-bccb-4e35-b996-3fac2ad6960c) · **Use:** assault rifle · model `SK_Automatic_Rifle_Full` · 148 × 39 × 11 cm

A long tan rifle with a suppressor and optics.

**Animations.** **Own:** a skeletal mesh (14 bones) without clips of its own. **Third person:** Held by UE4-mannequin clips with a long gun: the Aliens Warrior pack's 47 (3 shots, a reload, aims in eight directions, moves), the Sci-Fi Characters pack's fire, crouch-walk and sprint with iron sights, and the rifle jog, sprint and crouch-walk that came with the Military, Cyber Characters and Monsters Underwater packs; and the UE5 template's rifle equip and reload (retargeted).

<img src="images/objects/soldier_future_01_future_assault_rifle_side.jpg" width="280" alt="Future Assault Rifle, side view"> <img src="images/objects/soldier_future_01_future_assault_rifle_quarter.jpg" width="280" alt="Future Assault Rifle, three-quarter view"> <img src="images/objects/soldier_future_01_future_assault_rifle_third.jpg" width="280" alt="Future Assault Rifle, far three-quarter view">

#### Rocket-Propelled Grenade

[Soldier Future 03](https://www.fab.com/listings/75bde62a-fbe4-432f-99b2-00130b03e2a0) · **Use:** ammunition · model `SK_Rocket` · 61 × 10 × 10 cm

A tan RPG warhead.

**Animations.** **Own:** a skeletal mesh (2 bones) without clips of its own.

<img src="images/objects/soldier_future_03_future_rocket_launcher_side.jpg" width="280" alt="Rocket-Propelled Grenade, side view"> <img src="images/objects/soldier_future_03_future_rocket_launcher_quarter.jpg" width="280" alt="Rocket-Propelled Grenade, three-quarter view"> <img src="images/objects/soldier_future_03_future_rocket_launcher_third.jpg" width="280" alt="Rocket-Propelled Grenade, far three-quarter view">

#### Space Marine's Gun

[Astronauts (Pack)](https://www.fab.com/listings/69267151-497d-494f-9592-551cd39246a2) · **Use:** arm-mounted gun · model `SK_Astronaut_Soldier_Weapon_Full` · 192 × 136 × 80 cm

A white articulated gun mount with fittings.

**Animations.** **Own:** a skeletal mesh (10 bones) with 6 clips of its own: close, open, rotation 45 left, rotation 45 right, rotation 90 down, rotation 90 up. **Third person:** Held by UE4-mannequin clips with a long gun: the Aliens Warrior pack's 47 (3 shots, a reload, aims in eight directions, moves), the Sci-Fi Characters pack's fire, crouch-walk and sprint with iron sights, and the rifle jog, sprint and crouch-walk that came with the Military, Cyber Characters and Monsters Underwater packs; and the UE5 template's rifle equip and reload (retargeted).

<img src="images/objects/astronauts_pack_space_marine_s_gun_side.jpg" width="280" alt="Space Marine's Gun, side view"> <img src="images/objects/astronauts_pack_space_marine_s_gun_quarter.jpg" width="280" alt="Space Marine's Gun, three-quarter view"> <img src="images/objects/astronauts_pack_space_marine_s_gun_third.jpg" width="280" alt="Space Marine's Gun, far three-quarter view">

#### Cyber Rifle

[Cyber Characters Pack](https://www.fab.com/listings/f4631e9d-bea1-4258-a5fa-ead7247dc461) · **Use:** rifle · model `SM_Weapon` · 121 × 38 × 14 cm

A black and silver cyberpunk rifle.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by UE4-mannequin clips with a long gun: the Aliens Warrior pack's 47 (3 shots, a reload, aims in eight directions, moves), the Sci-Fi Characters pack's fire, crouch-walk and sprint with iron sights, and the rifle jog, sprint and crouch-walk that came with the Military, Cyber Characters and Monsters Underwater packs; and the UE5 template's rifle equip and reload (retargeted).

<img src="images/objects/cybercharacter_pack_cyber_rifle_side.jpg" width="280" alt="Cyber Rifle, side view"> <img src="images/objects/cybercharacter_pack_cyber_rifle_quarter.jpg" width="280" alt="Cyber Rifle, three-quarter view"> <img src="images/objects/cybercharacter_pack_cyber_rifle_third.jpg" width="280" alt="Cyber Rifle, far three-quarter view">

#### Flamethrower

[Dystopia Soldiers (Pack)](https://www.fab.com/listings/3be8756a-724d-4fca-a67f-8442a1fcb833) · **Use:** flamethrower · model `SK_Firegun_Base` and 2 more meshes · 148 × 139 × 86 cm

A flamethrower gun on a hose to twin fuel tanks.

**Animations.** **Own:** a part skinned to its character's skeleton (73 bones): it moves with that character's clips. **Third person:** Held by UE4-mannequin clips with a long gun: the Aliens Warrior pack's 47 (3 shots, a reload, aims in eight directions, moves), the Sci-Fi Characters pack's fire, crouch-walk and sprint with iron sights, and the rifle jog, sprint and crouch-walk that came with the Military, Cyber Characters and Monsters Underwater packs; and the UE5 template's rifle equip and reload (retargeted).

<img src="images/objects/dystopia_pack_flamethrower_side.jpg" width="280" alt="Flamethrower, side view"> <img src="images/objects/dystopia_pack_flamethrower_quarter.jpg" width="280" alt="Flamethrower, three-quarter view"> <img src="images/objects/dystopia_pack_flamethrower_third.jpg" width="280" alt="Flamethrower, far three-quarter view">

#### Alien Wrist Cannons

[Aliens Warrior (Pack)](https://www.fab.com/listings/a683cdf2-a1b1-4c35-b788-eeae62c2ed37) · **Use:** arm cannons · model `SK_Alien_Weapon_04_Full_01` · 80 × 75 × 65 cm

Twin mechanical wrist-mounted cannons with claw guards.

**Animations.** **Own:** a skeletal mesh (28 bones) with 17 clips of its own: warrior 04 rotation 45 down, warrior 04 rotation 45 l, warrior 04 rotation 45 r, warrior 04 rotation 45 up, warrior 04 shot, warrior 04 shot rotation 45 down, warrior 04 shot rotation 45 l, warrior 04 shot rotation 45 r, warrior 04 shot rotation 45 up, weapon 04 rotation 45 45 down l, weapon 04 rotation 45 45 down r, weapon 04 rotation 45 45 up l, weapon 04 rotation 45 45 up r, weapon 04 shot rotation 45 45 down l, weapon 04 shot rotation 45 45 down r, weapon 04 shot rotation 45 45 up l, weapon 04 shot rotation 45 45 up r. **Third person:** Held by UE4-mannequin clips with a long gun: the Aliens Warrior pack's 47 (3 shots, a reload, aims in eight directions, moves), the Sci-Fi Characters pack's fire, crouch-walk and sprint with iron sights, and the rifle jog, sprint and crouch-walk that came with the Military, Cyber Characters and Monsters Underwater packs; and the UE5 template's rifle equip and reload (retargeted).

<img src="images/objects/aliens_warrior_pack_alien_wrist_cannons_side.jpg" width="280" alt="Alien Wrist Cannons, side view"> <img src="images/objects/aliens_warrior_pack_alien_wrist_cannons_quarter.jpg" width="280" alt="Alien Wrist Cannons, three-quarter view"> <img src="images/objects/aliens_warrior_pack_alien_wrist_cannons_third.jpg" width="280" alt="Alien Wrist Cannons, a frame of its clip">

#### Magma Alien's Weapon

[Aliens Warrior (Pack)](https://www.fab.com/listings/a683cdf2-a1b1-4c35-b788-eeae62c2ed37) · **Use:** arm gun · model `SM_Alien_Warrior_05_Weapon` · 126 × 59 × 37 cm

A heavy mechanical gun with pipes and pistons.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by UE4-mannequin clips with a long gun: the Aliens Warrior pack's 47 (3 shots, a reload, aims in eight directions, moves), the Sci-Fi Characters pack's fire, crouch-walk and sprint with iron sights, and the rifle jog, sprint and crouch-walk that came with the Military, Cyber Characters and Monsters Underwater packs; and the UE5 template's rifle equip and reload (retargeted).

<img src="images/objects/aliens_warrior_pack_magma_alien_s_weapon_side.jpg" width="280" alt="Magma Alien's Weapon, side view"> <img src="images/objects/aliens_warrior_pack_magma_alien_s_weapon_quarter.jpg" width="280" alt="Magma Alien's Weapon, three-quarter view"> <img src="images/objects/aliens_warrior_pack_magma_alien_s_weapon_third.jpg" width="280" alt="Magma Alien's Weapon, far three-quarter view">

### Energy blades and shields

#### Sci-Fi Staff Weapon

[Sci-Fi Characters (Pack)](https://www.fab.com/listings/2079cbeb-ec9f-425e-b5c9-feb92d96321c) · **Use:** staff / polearm · model `SK_Sci_Fi_Character_05_Weapon` · 226 × 57 × 18 cm

A long black staff with a fan of blades at its head.

**Animations.** **Own:** a skeletal mesh (5 bones) with 2 clips of its own: close, open. **Third person:** Held by [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/sci_fi_characters_pack_sci_fi_rifle_side.jpg" width="280" alt="Sci-Fi Staff Weapon, side view"> <img src="images/objects/sci_fi_characters_pack_sci_fi_rifle_quarter.jpg" width="280" alt="Sci-Fi Staff Weapon, three-quarter view"> <img src="images/objects/sci_fi_characters_pack_sci_fi_rifle_third.jpg" width="280" alt="Sci-Fi Staff Weapon, far three-quarter view">

#### Guard's Halberd

[Sci-Fi Characters (Pack) Vol.2](https://www.fab.com/listings/d919d2b9-72be-4f86-a715-b8ce18e415f1) · **Use:** polearm · model `SM_Guard_Weapon` · 227 × 23 × 12 cm

A black polearm with a forked red-and-silver head.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/sci_fi_characters_pack_vol_2_guard_s_rifle_side.jpg" width="280" alt="Guard's Halberd, side view"> <img src="images/objects/sci_fi_characters_pack_vol_2_guard_s_rifle_quarter.jpg" width="280" alt="Guard's Halberd, three-quarter view"> <img src="images/objects/sci_fi_characters_pack_vol_2_guard_s_rifle_third.jpg" width="280" alt="Guard's Halberd, far three-quarter view">

#### Energy Knife (FPS)

[Sci-Fi Hands With Knife (Animation)](https://www.fab.com/listings/57215d02-5be7-4c74-bcfb-f1ae30012a7a) · **Use:** knife · model `SM_Sci_Fi_Knife` · 31 × 7 × 3 cm

A black serrated tactical knife.

**Animations.** **Own:** a static mesh, no clips of its own. **First person:** First-person arm clips: 34 in Sci-Fi Hands With Knife: 8 attacks, 2 hit reactions, 5 idles, 8 jumps and falls, 6 moves, 5 other (fi hands knife get, fi hands knife hide, fi hands knife inspection, fi hands knife shield get, fi hands knife shield hide). **Third person:** No third-person knife clips in the project.

<img src="images/objects/sci_fi_hands_knife_energy_knife_fps_side.jpg" width="280" alt="Energy Knife (FPS), side view"> <img src="images/objects/sci_fi_hands_knife_energy_knife_fps_quarter.jpg" width="280" alt="Energy Knife (FPS), three-quarter view"> <img src="images/objects/sci_fi_hands_knife_energy_knife_fps_third.jpg" width="280" alt="Energy Knife (FPS), far three-quarter view">

#### Arm Shield (FPS)

[FPS Sci-Fi Hands Empty](https://www.fab.com/listings/1c1fbb6f-1a9a-42d7-b0c2-80837c55c564) · **Use:** energy shield · model `SK_Sci_Fi_Shield` · 55 × 55 × 8 cm

A folded arm device that opens into a round blue energy shield.

**Animations.** **Own:** a skeletal mesh (32 bones) with 2 clips of its own: close, open. **First person:** First-person arm clips: 27 in FPS Sci-Fi Hands Empty: 5 attacks, 2 hit reactions, 6 idles, 4 jumps and falls, 6 moves, 4 other (fi hands empty get, fi hands empty hide, fi hands empty shield get, fi hands empty shield hide). **Third person:** Carried by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves) and [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/sci_fi_hands_arm_shield_fps_side.jpg" width="280" alt="Arm Shield (FPS), side view"> <img src="images/objects/sci_fi_hands_arm_shield_fps_quarter.jpg" width="280" alt="Arm Shield (FPS), three-quarter view"> <img src="images/objects/sci_fi_hands_arm_shield_fps_third.jpg" width="280" alt="Arm Shield (FPS), a frame of its clip">

#### Sci-Fi Sword

[Sci-Fi Characters (Pack)](https://www.fab.com/listings/2079cbeb-ec9f-425e-b5c9-feb92d96321c) · **Use:** energy sword · model `SM_Sci_Fi_Sword` · 119 × 5 × 3 cm

A sword with a glowing blue blade.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves); the two-handed ones by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/sci_fi_characters_pack_sci_fi_sword_side.jpg" width="280" alt="Sci-Fi Sword, side view"> <img src="images/objects/sci_fi_characters_pack_sci_fi_sword_quarter.jpg" width="280" alt="Sci-Fi Sword, three-quarter view"> <img src="images/objects/sci_fi_characters_pack_sci_fi_sword_third.jpg" width="280" alt="Sci-Fi Sword, far three-quarter view">

#### Sci-Fi Blade

[Sci-Fi Characters (Pack)](https://www.fab.com/listings/2079cbeb-ec9f-425e-b5c9-feb92d96321c) · **Use:** energy blade · model `SM_Sci_Fi_Sword_02` · 160 × 34 × 8 cm

A black blade outlined in orange light.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves); the two-handed ones by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/sci_fi_characters_pack_sci_fi_blade_side.jpg" width="280" alt="Sci-Fi Blade, side view"> <img src="images/objects/sci_fi_characters_pack_sci_fi_blade_quarter.jpg" width="280" alt="Sci-Fi Blade, three-quarter view"> <img src="images/objects/sci_fi_characters_pack_sci_fi_blade_third.jpg" width="280" alt="Sci-Fi Blade, far three-quarter view">

#### Reaper's Scythe

[Sci-Fi Characters (Pack) Vol.2](https://www.fab.com/listings/d919d2b9-72be-4f86-a715-b8ce18e415f1) · **Use:** scythe · model `SM_Scythe` · 197 × 83 × 8 cm

A black scythe with a curved blade.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves).

<img src="images/objects/sci_fi_characters_pack_vol_2_reaper_s_scythe_side.jpg" width="280" alt="Reaper's Scythe, side view"> <img src="images/objects/sci_fi_characters_pack_vol_2_reaper_s_scythe_quarter.jpg" width="280" alt="Reaper's Scythe, three-quarter view"> <img src="images/objects/sci_fi_characters_pack_vol_2_reaper_s_scythe_third.jpg" width="280" alt="Reaper's Scythe, far three-quarter view">

#### Wrist Blade

[Dystopia Soldiers (Pack)](https://www.fab.com/listings/3be8756a-724d-4fca-a67f-8442a1fcb833) · **Use:** wrist blade · model `SM_Sword_Full` · 84 × 29 × 10 cm

A twin blade mounted on an armoured gauntlet.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves); the two-handed ones by [92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs).

<img src="images/objects/dystopia_pack_dystopian_sword_side.jpg" width="280" alt="Wrist Blade, side view"> <img src="images/objects/dystopia_pack_dystopian_sword_quarter.jpg" width="280" alt="Wrist Blade, three-quarter view"> <img src="images/objects/dystopia_pack_dystopian_sword_third.jpg" width="280" alt="Wrist Blade, far three-quarter view">

#### Alien Mace

[Aliens Warrior (Pack)](https://www.fab.com/listings/a683cdf2-a1b1-4c35-b788-eeae62c2ed37) · **Use:** mace · model `SM_UE4_Alien_Warrior_02_Mace` · 135 × 46 × 46 cm

A spiked metal ball on a long staff.

**Animations.** **Own:** a static mesh, no clips of its own. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves).

<img src="images/objects/aliens_warrior_pack_alien_mace_side.jpg" width="280" alt="Alien Mace, side view"> <img src="images/objects/aliens_warrior_pack_alien_mace_quarter.jpg" width="280" alt="Alien Mace, three-quarter view"> <img src="images/objects/aliens_warrior_pack_alien_mace_third.jpg" width="280" alt="Alien Mace, far three-quarter view">

#### Alien Claw Blades

[Aliens Warrior (Pack)](https://www.fab.com/listings/a683cdf2-a1b1-4c35-b788-eeae62c2ed37) · **Use:** claws · model `SK_UE4_Alien_Warrior_04_Weapon` · 210 × 65 × 51 cm

A pair of long curved blades worn on the forearms.

**Animations.** **Own:** a part skinned to its character's skeleton (68 bones): it moves with that character's clips. **Third person:** Held by [Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves).

<img src="images/objects/aliens_warrior_pack_alien_claw_blades_side.jpg" width="280" alt="Alien Claw Blades, side view"> <img src="images/objects/aliens_warrior_pack_alien_claw_blades_quarter.jpg" width="280" alt="Alien Claw Blades, three-quarter view"> <img src="images/objects/aliens_warrior_pack_alien_claw_blades_third.jpg" width="280" alt="Alien Claw Blades, far three-quarter view">

## Non-weapon items

Food and drink, medicine, tools and devices, treasure, keys and books, and wearable helmets and masks: pickups, quest items and props for hands.

### Food and drink

#### Chocolate Bar

[FPS STARTER (PACK)](https://www.fab.com/listings/afe92192-dd5c-4bb0-a476-0c09646d897d) · **Use:** food · model `SK_Chocolate_01` · 18 × 8 × 1 cm

A bar of milk chocolate in an orange wrapper.

**Animations.** **Own:** a skeletal mesh (4 bones) with 1 clip of its own: 01 hide. **First person:** First-person arm clips: 2 in FPS Starter Pack (chocolate): 2 other (chocolate 01 eat, chocolate 02 eat).

<img src="images/objects/fps_starter_pack_chocolate_bar_side.jpg" width="280" alt="Chocolate Bar, side view"> <img src="images/objects/fps_starter_pack_chocolate_bar_quarter.jpg" width="280" alt="Chocolate Bar, three-quarter view"> <img src="images/objects/fps_starter_pack_chocolate_bar_third.jpg" width="280" alt="Chocolate Bar, a frame of its clip">

#### Canned Sardines

[FPS STARTER (PACK)](https://www.fab.com/listings/afe92192-dd5c-4bb0-a476-0c09646d897d) · **Use:** food · model `SK_Sardines` · 9 × 9 × 5 cm

A blue tin of sardines with a ring-pull lid.

**Animations.** **Own:** a skeletal mesh (10 bones) with 1 clip of its own: open. **First person:** First-person arm clips: 1 in FPS Starter Pack (sardines): 1 other (sardines eat).

<img src="images/objects/fps_starter_pack_canned_sardines_side.jpg" width="280" alt="Canned Sardines, side view"> <img src="images/objects/fps_starter_pack_canned_sardines_quarter.jpg" width="280" alt="Canned Sardines, three-quarter view"> <img src="images/objects/fps_starter_pack_canned_sardines_third.jpg" width="280" alt="Canned Sardines, a frame of its clip">

#### Canned Sprats

[FPS STARTER (PACK)](https://www.fab.com/listings/afe92192-dd5c-4bb0-a476-0c09646d897d) · **Use:** food · model `SK_Sprats` · 18 × 10 × 3 cm

An oval tin of sprats in oil.

**Animations.** **Own:** a skeletal mesh (10 bones) with 1 clip of its own: open. **First person:** First-person arm clips: 1 in FPS Starter Pack (sprats): 1 other (sprats eat).

<img src="images/objects/fps_starter_pack_canned_sprats_side.jpg" width="280" alt="Canned Sprats, side view"> <img src="images/objects/fps_starter_pack_canned_sprats_quarter.jpg" width="280" alt="Canned Sprats, three-quarter view"> <img src="images/objects/fps_starter_pack_canned_sprats_third.jpg" width="280" alt="Canned Sprats, a frame of its clip">

#### Canned Meatballs

[FPS STARTER (PACK)](https://www.fab.com/listings/afe92192-dd5c-4bb0-a476-0c09646d897d) · **Use:** food · model `SK_Meatball` · 20 × 20 × 6 cm

A foil tray of beef meatballs.

**Animations.** **Own:** a skeletal mesh (18 bones) with 1 clip of its own: open. **First person:** First-person arm clips: 1 in FPS Starter Pack (meatballs): 1 other (meatball eat).

<img src="images/objects/fps_starter_pack_canned_meatballs_side.jpg" width="280" alt="Canned Meatballs, side view"> <img src="images/objects/fps_starter_pack_canned_meatballs_quarter.jpg" width="280" alt="Canned Meatballs, three-quarter view"> <img src="images/objects/fps_starter_pack_canned_meatballs_third.jpg" width="280" alt="Canned Meatballs, a frame of its clip">

#### Porridge

[FPS STARTER (PACK)](https://www.fab.com/listings/afe92192-dd5c-4bb0-a476-0c09646d897d) · **Use:** food · model `SK_Porridge_Plate` · 20 × 18 × 6 cm

A sealed pot of porridge.

**Animations.** **Own:** a skeletal mesh (8 bones) with 1 clip of its own: plate open. **First person:** First-person arm clips: 1 in FPS Starter Pack (porridge): 1 other (porridge eat).

<img src="images/objects/fps_starter_pack_porridge_side.jpg" width="280" alt="Porridge, side view"> <img src="images/objects/fps_starter_pack_porridge_quarter.jpg" width="280" alt="Porridge, three-quarter view"> <img src="images/objects/fps_starter_pack_porridge_third.jpg" width="280" alt="Porridge, a frame of its clip">

#### Canned Stew

[FPS STARTER (PACK)](https://www.fab.com/listings/afe92192-dd5c-4bb0-a476-0c09646d897d) · **Use:** food · model `SK_Jar` · 13 × 10 × 10 cm

A tin of stewed meat with a green label.

**Animations.** **Own:** a skeletal mesh (10 bones) with 1 clip of its own: open. **First person:** First-person arm clips: 1 in FPS Starter Pack (jar): 1 other (jar of food eat).

<img src="images/objects/fps_starter_pack_jar_of_food_side.jpg" width="280" alt="Canned Stew, side view"> <img src="images/objects/fps_starter_pack_jar_of_food_quarter.jpg" width="280" alt="Canned Stew, three-quarter view"> <img src="images/objects/fps_starter_pack_jar_of_food_third.jpg" width="280" alt="Canned Stew, a frame of its clip">

#### Soda Can

[FPS STARTER (PACK)](https://www.fab.com/listings/afe92192-dd5c-4bb0-a476-0c09646d897d) · **Use:** drink · model `SK_Soda` · 17 × 9 × 9 cm

A red and orange soda can.

**Animations.** **Own:** a skeletal mesh (6 bones) with 1 clip of its own: open close. **First person:** First-person arm clips: 1 in FPS Starter Pack (soda): 1 other (soda drink).

<img src="images/objects/fps_starter_pack_soda_can_side.jpg" width="280" alt="Soda Can, side view"> <img src="images/objects/fps_starter_pack_soda_can_quarter.jpg" width="280" alt="Soda Can, three-quarter view"> <img src="images/objects/fps_starter_pack_soda_can_third.jpg" width="280" alt="Soda Can, a frame of its clip">

#### Juice Carton

[FPS STARTER (PACK)](https://www.fab.com/listings/afe92192-dd5c-4bb0-a476-0c09646d897d) · **Use:** drink · model `SK_Juce` · 22 × 9 × 8 cm

A fruit juice carton.

**Animations.** **Own:** a skeletal mesh (4 bones) with 1 clip of its own: open close. **First person:** First-person arm clips: 1 in FPS Starter Pack (juice): 1 other (juce drink).

<img src="images/objects/fps_starter_pack_juice_carton_side.jpg" width="280" alt="Juice Carton, side view"> <img src="images/objects/fps_starter_pack_juice_carton_quarter.jpg" width="280" alt="Juice Carton, three-quarter view"> <img src="images/objects/fps_starter_pack_juice_carton_third.jpg" width="280" alt="Juice Carton, a frame of its clip">

#### Lemonade Bottle

[FPS STARTER (PACK)](https://www.fab.com/listings/afe92192-dd5c-4bb0-a476-0c09646d897d) · **Use:** drink · model `SK_Lemonade_Bottle` · 31 × 7 × 7 cm

A brown swing-top bottle.

**Animations.** **Own:** a skeletal mesh (8 bones) with 1 clip of its own: bottle open close. **First person:** First-person arm clips: 1 in FPS Starter Pack (lemonade): 1 other (lemonade bottle drink).

<img src="images/objects/fps_starter_pack_lemonade_bottle_side.jpg" width="280" alt="Lemonade Bottle, side view"> <img src="images/objects/fps_starter_pack_lemonade_bottle_quarter.jpg" width="280" alt="Lemonade Bottle, three-quarter view"> <img src="images/objects/fps_starter_pack_lemonade_bottle_third.jpg" width="280" alt="Lemonade Bottle, a frame of its clip">

#### Coffee Mug

[FPS STARTER (PACK)](https://www.fab.com/listings/afe92192-dd5c-4bb0-a476-0c09646d897d) · **Use:** drink · model `SK_Mug` · 15 × 10 × 10 cm

A dark enamel mug of coffee.

**Animations.** **Own:** a skeletal mesh (4 bones) with 1 clip of its own: rotation. **First person:** First-person arm clips: 1 in FPS Starter Pack (coffee): 1 other (coffe drink).

<img src="images/objects/fps_starter_pack_coffee_mug_side.jpg" width="280" alt="Coffee Mug, side view"> <img src="images/objects/fps_starter_pack_coffee_mug_quarter.jpg" width="280" alt="Coffee Mug, three-quarter view"> <img src="images/objects/fps_starter_pack_coffee_mug_third.jpg" width="280" alt="Coffee Mug, a frame of its clip">

#### Sausage

[FPS STARTER (PACK)](https://www.fab.com/listings/afe92192-dd5c-4bb0-a476-0c09646d897d) · **Use:** food · model `SK_Sausage` · 62 × 6 × 5 cm

A sausage on a roasting stick.

**Animations.** **Own:** a skeletal mesh (4 bones) with 1 clip of its own: sausage marshmallows hide. **First person:** First-person arm clips: 1 in FPS Starter Pack (fish, sausage, marshmallows): 1 other (fish sausage marshmallows eat).

<img src="images/objects/fps_starter_pack_sausage_side.jpg" width="280" alt="Sausage, side view"> <img src="images/objects/fps_starter_pack_sausage_quarter.jpg" width="280" alt="Sausage, three-quarter view"> <img src="images/objects/fps_starter_pack_sausage_third.jpg" width="280" alt="Sausage, far three-quarter view">

#### Fish

[FPS STARTER (PACK)](https://www.fab.com/listings/afe92192-dd5c-4bb0-a476-0c09646d897d) · **Use:** food · model `SK_Fish` · 71 × 10 × 5 cm

A small fish on a roasting stick.

**Animations.** **Own:** a skeletal mesh (4 bones) with 1 clip of its own: sausage marshmallows hide. **First person:** First-person arm clips: 1 in FPS Starter Pack (fish, sausage, marshmallows): 1 other (fish sausage marshmallows eat).

<img src="images/objects/fps_starter_pack_fish_side.jpg" width="280" alt="Fish, side view"> <img src="images/objects/fps_starter_pack_fish_quarter.jpg" width="280" alt="Fish, three-quarter view"> <img src="images/objects/fps_starter_pack_fish_third.jpg" width="280" alt="Fish, far three-quarter view">

#### Loaf of Bread

[(Nanite) Medieval Food & Dining Kit - Food Props](https://www.fab.com/listings/a694f62c-fe40-4227-b556-d9e17652e69e) · **Use:** food · model `SM_Bread_Var1` · 24 × 24 × 14 cm

A round crusty loaf.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/diner_colection_loaf_of_bread_side.jpg" width="280" alt="Loaf of Bread, side view"> <img src="images/objects/diner_colection_loaf_of_bread_quarter.jpg" width="280" alt="Loaf of Bread, three-quarter view"> <img src="images/objects/diner_colection_loaf_of_bread_third.jpg" width="280" alt="Loaf of Bread, far three-quarter view">

#### Cheese Wheel

[(Nanite) Medieval Food & Dining Kit - Food Props](https://www.fab.com/listings/a694f62c-fe40-4227-b556-d9e17652e69e) · **Use:** food · model `SM_Cheese_Var1` · 32 × 32 × 7 cm

A cheese wheel with a wedge cut out.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/diner_colection_cheese_wheel_side.jpg" width="280" alt="Cheese Wheel, side view"> <img src="images/objects/diner_colection_cheese_wheel_quarter.jpg" width="280" alt="Cheese Wheel, three-quarter view"> <img src="images/objects/diner_colection_cheese_wheel_third.jpg" width="280" alt="Cheese Wheel, far three-quarter view">

#### Apple

[(Nanite) Medieval Food & Dining Kit - Food Props](https://www.fab.com/listings/a694f62c-fe40-4227-b556-d9e17652e69e) · **Use:** food · model `SM_Fruit_Apple` · 7 × 7 × 7 cm

A red apple.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/diner_colection_apple_side.jpg" width="280" alt="Apple, side view"> <img src="images/objects/diner_colection_apple_quarter.jpg" width="280" alt="Apple, three-quarter view"> <img src="images/objects/diner_colection_apple_third.jpg" width="280" alt="Apple, far three-quarter view">

#### Steak

[(Nanite) Medieval Food & Dining Kit - Food Props](https://www.fab.com/listings/a694f62c-fe40-4227-b556-d9e17652e69e) · **Use:** food · model `SM_PieceMeat` · 28 × 16 × 6 cm

A raw steak.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/diner_colection_joint_of_meat_side.jpg" width="280" alt="Steak, side view"> <img src="images/objects/diner_colection_joint_of_meat_quarter.jpg" width="280" alt="Steak, three-quarter view"> <img src="images/objects/diner_colection_joint_of_meat_third.jpg" width="280" alt="Steak, far three-quarter view">

#### Wine Bottle

[(Nanite) Medieval Food & Dining Kit - Food Props](https://www.fab.com/listings/a694f62c-fe40-4227-b556-d9e17652e69e) · **Use:** drink · model `SM_WineBottles_Var1` · 34 × 10 × 10 cm

A dark, faceted wine bottle.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/diner_colection_wine_bottle_side.jpg" width="280" alt="Wine Bottle, side view"> <img src="images/objects/diner_colection_wine_bottle_quarter.jpg" width="280" alt="Wine Bottle, three-quarter view"> <img src="images/objects/diner_colection_wine_bottle_third.jpg" width="280" alt="Wine Bottle, far three-quarter view">

#### Wooden Tankard

[(Nanite) Medieval Food & Dining Kit - Food Props](https://www.fab.com/listings/a694f62c-fe40-4227-b556-d9e17652e69e) · **Use:** drink · model `SM_WoodCup_SM_WoodCup` · 20 × 18 × 13 cm

A faceted wooden tankard.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/diner_colection_wooden_cup_side.jpg" width="280" alt="Wooden Tankard, side view"> <img src="images/objects/diner_colection_wooden_cup_quarter.jpg" width="280" alt="Wooden Tankard, three-quarter view"> <img src="images/objects/diner_colection_wooden_cup_third.jpg" width="280" alt="Wooden Tankard, far three-quarter view">

#### Silver Goblet

[(Nanite) Medieval Food & Dining Kit - Food Props](https://www.fab.com/listings/a694f62c-fe40-4227-b556-d9e17652e69e) · **Use:** drink / treasure · model `SM_SilverCup` · 26 × 13 × 13 cm

A tall silver goblet.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/diner_colection_silver_cup_side.jpg" width="280" alt="Silver Goblet, side view"> <img src="images/objects/diner_colection_silver_cup_quarter.jpg" width="280" alt="Silver Goblet, three-quarter view"> <img src="images/objects/diner_colection_silver_cup_third.jpg" width="280" alt="Silver Goblet, far three-quarter view">

#### Chalice

[Medieval Furniture Props](https://www.fab.com/listings/aa584fda-82a3-4f6f-8675-e2f8fab14daf) · **Use:** drink / treasure · model `SM_Prop_Chalice_A` · 14 × 6 × 6 cm

An embossed bronze chalice.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/gothic_props_chalice_side.jpg" width="280" alt="Chalice, side view"> <img src="images/objects/gothic_props_chalice_quarter.jpg" width="280" alt="Chalice, three-quarter view"> <img src="images/objects/gothic_props_chalice_third.jpg" width="280" alt="Chalice, far three-quarter view">

#### Flatbread

[Bazaar](https://www.fab.com/listings/ccde8d34-48fc-4876-b1cd-1658af34ffbb) · **Use:** food · model `SM_His_Baz_Food_Bread_Naan_01` · 26 × 26 × 3 cm

A round naan flatbread (a Megascans scan).

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/scene_bazaar_vol1_flatbread_side.jpg" width="280" alt="Flatbread, side view"> <img src="images/objects/scene_bazaar_vol1_flatbread_quarter.jpg" width="280" alt="Flatbread, three-quarter view"> <img src="images/objects/scene_bazaar_vol1_flatbread_third.jpg" width="280" alt="Flatbread, far three-quarter view">

### Potions and medicine

#### Vaccine Gun

[FPS STARTER (PACK)](https://www.fab.com/listings/afe92192-dd5c-4bb0-a476-0c09646d897d) · **Use:** healing item · model `SK_Syringe_01` · 20 × 17 × 4 cm

A pistol-grip injector with a vial on top.

**Animations.** **Own:** a skeletal mesh (2 bones) with 1 clip of its own: 01 push. **First person:** First-person arm clips: 3 in FPS Starter Pack (syringes): 3 other (syringe 01 using, syringe 02 using, syringe 03 using).

<img src="images/objects/fps_starter_pack_syringe_side.jpg" width="280" alt="Vaccine Gun, side view"> <img src="images/objects/fps_starter_pack_syringe_quarter.jpg" width="280" alt="Vaccine Gun, three-quarter view"> <img src="images/objects/fps_starter_pack_syringe_third.jpg" width="280" alt="Vaccine Gun, a frame of its clip">

#### Syringe

[FPS STARTER (PACK)](https://www.fab.com/listings/afe92192-dd5c-4bb0-a476-0c09646d897d) · **Use:** healing item · model `SK_Syringe_02` · 24 × 8 × 3 cm

A black syringe.

**Animations.** **Own:** a skeletal mesh (4 bones) with 1 clip of its own: 02 push. **First person:** First-person arm clips: 3 in FPS Starter Pack (syringes): 3 other (syringe 01 using, syringe 02 using, syringe 03 using).

<img src="images/objects/fps_starter_pack_auto_injector_side.jpg" width="280" alt="Syringe, side view"> <img src="images/objects/fps_starter_pack_auto_injector_quarter.jpg" width="280" alt="Syringe, three-quarter view"> <img src="images/objects/fps_starter_pack_auto_injector_third.jpg" width="280" alt="Syringe, a frame of its clip">

#### Dosing Syringe

[FPS STARTER (PACK)](https://www.fab.com/listings/afe92192-dd5c-4bb0-a476-0c09646d897d) · **Use:** healing item · model `SK_Syringe_03` · 22 × 20 × 3 cm

A blue dosing syringe with a vial and finger loops.

**Animations.** **Own:** a skeletal mesh (4 bones) with 1 clip of its own: 03 push. **First person:** First-person arm clips: 3 in FPS Starter Pack (syringes): 3 other (syringe 01 using, syringe 02 using, syringe 03 using).

<img src="images/objects/fps_starter_pack_stim_syringe_side.jpg" width="280" alt="Dosing Syringe, side view"> <img src="images/objects/fps_starter_pack_stim_syringe_quarter.jpg" width="280" alt="Dosing Syringe, three-quarter view"> <img src="images/objects/fps_starter_pack_stim_syringe_third.jpg" width="280" alt="Dosing Syringe, a frame of its clip">

#### Canteen

[FPS STARTER (PACK)](https://www.fab.com/listings/afe92192-dd5c-4bb0-a476-0c09646d897d) · **Use:** drink · model `SK_Flask` · 25 × 19 × 12 cm

A water canteen in a khaki cover.

**Animations.** **Own:** a skeletal mesh (6 bones) with 1 clip of its own: open close. **First person:** First-person arm clips: 1 in FPS Starter Pack (flask): 1 other (flask drink).

<img src="images/objects/fps_starter_pack_hip_flask_side.jpg" width="280" alt="Canteen, side view"> <img src="images/objects/fps_starter_pack_hip_flask_quarter.jpg" width="280" alt="Canteen, three-quarter view"> <img src="images/objects/fps_starter_pack_hip_flask_third.jpg" width="280" alt="Canteen, a frame of its clip">

#### Potion

[(Nanite) Medieval Food & Dining Kit - Food Props](https://www.fab.com/listings/a694f62c-fe40-4227-b556-d9e17652e69e) · **Use:** potion · model `SM_Potions_Var1` · 18 × 11 × 11 cm

A dark purple potion in a round corked bottle.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/diner_colection_potion_side.jpg" width="280" alt="Potion, side view"> <img src="images/objects/diner_colection_potion_quarter.jpg" width="280" alt="Potion, three-quarter view"> <img src="images/objects/diner_colection_potion_third.jpg" width="280" alt="Potion, far three-quarter view">

#### Tall Potion

[(Nanite) Medieval Food & Dining Kit - Food Props](https://www.fab.com/listings/a694f62c-fe40-4227-b556-d9e17652e69e) · **Use:** potion · model `SM_Potions_Var2` · 16 × 8 × 8 cm

A green potion in a square corked bottle.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/diner_colection_tall_potion_side.jpg" width="280" alt="Tall Potion, side view"> <img src="images/objects/diner_colection_tall_potion_quarter.jpg" width="280" alt="Tall Potion, three-quarter view"> <img src="images/objects/diner_colection_tall_potion_third.jpg" width="280" alt="Tall Potion, far three-quarter view">

#### Pill

[Abandoned Hospital Mortuary Environment](https://www.fab.com/listings/ef1e3661-2b7d-47ec-af8f-a7c402433bbb) · **Use:** healing item · model `SM_Pill_01` · 2 × 2 × 0 cm

A round white tablet scored with a cross.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/abandoned_hospital_pill_bottle_side.jpg" width="280" alt="Pill, side view"> <img src="images/objects/abandoned_hospital_pill_bottle_quarter.jpg" width="280" alt="Pill, three-quarter view"> <img src="images/objects/abandoned_hospital_pill_bottle_third.jpg" width="280" alt="Pill, far three-quarter view">

#### Medical Bag

[Hospital Props VOL.1 - Interior & Emergency Equipment](https://www.fab.com/listings/af2570f1-b718-4f43-ad0c-f0d7444032ee) · **Use:** healing item · model `SM_MedicalBag_01a` · 82 × 55 × 42 cm

A red emergency first-aid bag.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/hospital_vol1_medical_bag_side.jpg" width="280" alt="Medical Bag, side view"> <img src="images/objects/hospital_vol1_medical_bag_quarter.jpg" width="280" alt="Medical Bag, three-quarter view"> <img src="images/objects/hospital_vol1_medical_bag_third.jpg" width="280" alt="Medical Bag, far three-quarter view">

#### Witch's Flasks

[Fantasy Warriors (Pack)](https://www.fab.com/listings/df8194f9-ec63-49f6-a885-6feb7a94fcb1) · **Use:** potions · model `SK_Witch_Flasks` · 20 × 19 × 14 cm

A bandolier of five glowing green flasks.

**Animations.** **Own:** a part skinned to its character's skeleton (68 bones): it moves with that character's clips.

<img src="images/objects/warriors_pack_witch_s_flasks_side.jpg" width="280" alt="Witch's Flasks, side view"> <img src="images/objects/warriors_pack_witch_s_flasks_quarter.jpg" width="280" alt="Witch's Flasks, three-quarter view"> <img src="images/objects/warriors_pack_witch_s_flasks_third.jpg" width="280" alt="Witch's Flasks, far three-quarter view">

### Tools and devices

#### Lighter

[FPS STARTER (PACK)](https://www.fab.com/listings/afe92192-dd5c-4bb0-a476-0c09646d897d) · **Use:** tool · model `SK_Lighter` · 11 × 8 × 2 cm

A brushed-steel flip lighter, its lid opening.

**Animations.** **Own:** a skeletal mesh (2 bones) with 2 clips of its own: close, open. **First person:** First-person arm clips: 9 in FPS Starter Pack (lighter): 2 attacks, 1 hit reaction, 2 idles, 2 moves, 2 other (lighter down, lighter up).

<img src="images/objects/fps_starter_pack_lighter_side.jpg" width="280" alt="Lighter, side view"> <img src="images/objects/fps_starter_pack_lighter_quarter.jpg" width="280" alt="Lighter, three-quarter view"> <img src="images/objects/fps_starter_pack_lighter_third.jpg" width="280" alt="Lighter, a frame of its clip">

#### Binoculars

[FPS STARTER (PACK)](https://www.fab.com/listings/afe92192-dd5c-4bb0-a476-0c09646d897d) · **Use:** tool · model `SM_Binoculars` · 24 × 23 × 12 cm

A pair of rugged black binoculars.

**Animations.** **Own:** a static mesh, no clips of its own. **First person:** First-person arm clips: 9 in FPS Starter Pack (binoculars): 2 attacks, 1 idle, 1 jump or fall, 2 moves, 3 other (binoculars down, binoculars up, binoculars watch).

<img src="images/objects/fps_starter_pack_binoculars_side.jpg" width="280" alt="Binoculars, side view"> <img src="images/objects/fps_starter_pack_binoculars_quarter.jpg" width="280" alt="Binoculars, three-quarter view"> <img src="images/objects/fps_starter_pack_binoculars_third.jpg" width="280" alt="Binoculars, far three-quarter view">

#### Handheld Candle

[FPS STARTER (PACK)](https://www.fab.com/listings/afe92192-dd5c-4bb0-a476-0c09646d897d) · **Use:** light · model `SM_Candle` · 18 × 14 × 12 cm

A candle in a tin chamberstick with a ring handle.

**Animations.** **Own:** a static mesh, no clips of its own. **First person:** First-person arm clips: 10 in FPS Starter Pack (candle): 2 attacks, 1 hit reaction, 2 idles, 1 jump or fall, 2 moves, 2 other (candle down, candle up).

<img src="images/objects/fps_starter_pack_handheld_candle_side.jpg" width="280" alt="Handheld Candle, side view"> <img src="images/objects/fps_starter_pack_handheld_candle_quarter.jpg" width="280" alt="Handheld Candle, three-quarter view"> <img src="images/objects/fps_starter_pack_handheld_candle_third.jpg" width="280" alt="Handheld Candle, far three-quarter view">

#### Torch

[FPS STARTER (PACK)](https://www.fab.com/listings/afe92192-dd5c-4bb0-a476-0c09646d897d) · **Use:** light / club · model `SM_Torch` · 63 × 10 × 10 cm

A rag-wrapped torch on a wooden stick.

**Animations.** **Own:** a static mesh, no clips of its own. **First person:** First-person arm clips: 26 in FPS Starter Pack (lantern and torch): 7 attacks, 2 hit reactions, 4 idles, 3 jumps and falls, 4 moves, 6 other (lantern 01 down, lantern 02 block, lantern 02 down, lantern 02 knife down, lantern 02 knife up, ...).

<img src="images/objects/fps_starter_pack_torch_side.jpg" width="280" alt="Torch, side view"> <img src="images/objects/fps_starter_pack_torch_quarter.jpg" width="280" alt="Torch, three-quarter view"> <img src="images/objects/fps_starter_pack_torch_third.jpg" width="280" alt="Torch, far three-quarter view">

#### Camcorder

[FPS Devices](https://www.fab.com/listings/cd0ce7d0-a66b-42bf-afbb-0f195c41d320) · **Use:** device · model `SK_Camera` · 23 × 17 × 9 cm

A handheld camcorder with a flip-out screen.

**Animations.** **Own:** a skeletal mesh (4 bones) without clips of its own. **First person:** First-person arm clips: 12 in FPS Devices (camera): 1 hit reaction, 1 idle, 4 jumps and falls, 2 moves, 4 other (get, hide, video, watching video).

<img src="images/objects/fps_devices_camcorder_side.jpg" width="280" alt="Camcorder, side view"> <img src="images/objects/fps_devices_camcorder_quarter.jpg" width="280" alt="Camcorder, three-quarter view"> <img src="images/objects/fps_devices_camcorder_third.jpg" width="280" alt="Camcorder, far three-quarter view">

#### Smartphone

[FPS Devices](https://www.fab.com/listings/cd0ce7d0-a66b-42bf-afbb-0f195c41d320) · **Use:** device · model `SM_Phone` · 20 × 10 × 2 cm

A rugged smartphone.

**Animations.** **Own:** a static mesh, no clips of its own. **First person:** First-person arm clips: 19 in FPS Devices (phone): 1 hit reaction, 4 idles, 4 jumps and falls, 4 moves, 6 other (action, get, hide, video end, video loop, ...).

<img src="images/objects/fps_devices_smartphone_side.jpg" width="280" alt="Smartphone, side view"> <img src="images/objects/fps_devices_smartphone_quarter.jpg" width="280" alt="Smartphone, three-quarter view"> <img src="images/objects/fps_devices_smartphone_third.jpg" width="280" alt="Smartphone, far three-quarter view">

#### Walkie-Talkie

[FPS Devices](https://www.fab.com/listings/cd0ce7d0-a66b-42bf-afbb-0f195c41d320) · **Use:** device · model `SM_Walkie_Talkie` · 35 × 9 × 6 cm

A walkie-talkie with a keypad and antenna.

**Animations.** **Own:** a static mesh, no clips of its own. **First person:** First-person arm clips: 15 in FPS Devices (walkie-talkie): 1 hit reaction, 3 idles, 4 jumps and falls, 7 moves.

<img src="images/objects/fps_devices_walkie_talkie_side.jpg" width="280" alt="Walkie-Talkie, side view"> <img src="images/objects/fps_devices_walkie_talkie_quarter.jpg" width="280" alt="Walkie-Talkie, three-quarter view"> <img src="images/objects/fps_devices_walkie_talkie_third.jpg" width="280" alt="Walkie-Talkie, far three-quarter view">

#### Listening Device

[FPS Devices](https://www.fab.com/listings/cd0ce7d0-a66b-42bf-afbb-0f195c41d320) · **Use:** device · model `SM_Listening_Device` · 46 × 38 × 36 cm

A pistol-grip directional microphone.

**Animations.** **Own:** a static mesh, no clips of its own. **First person:** First-person arm clips: 16 in FPS Devices (listening device): 2 attacks, 1 hit reaction, 3 idles, 4 jumps and falls, 3 moves, 3 other (device action, device get, device hide).

<img src="images/objects/fps_devices_listening_device_side.jpg" width="280" alt="Listening Device, side view"> <img src="images/objects/fps_devices_listening_device_quarter.jpg" width="280" alt="Listening Device, three-quarter view"> <img src="images/objects/fps_devices_listening_device_third.jpg" width="280" alt="Listening Device, far three-quarter view">

#### Military Radio

[Military Base Megapack](https://www.fab.com/listings/61202d6c-1bc2-4e5d-b2d5-d005ea8b7c67) · **Use:** device / prop · model `SM_MilitaryRadio` · 68 × 63 × 56 cm

A stacked green military radio set.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/mc_environment_military_radio_side.jpg" width="280" alt="Military Radio, side view"> <img src="images/objects/mc_environment_military_radio_quarter.jpg" width="280" alt="Military Radio, three-quarter view"> <img src="images/objects/mc_environment_military_radio_third.jpg" width="280" alt="Military Radio, far three-quarter view">

#### Handheld Radio

[Sniper Soldier](https://www.fab.com/listings/70c21220-f9a1-4c3c-8bc2-699508be793f) · **Use:** device · model `SM_Sniper_Radio_Set02` · 26 × 9 × 6 cm

A black handheld radio.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/sniper_radio_set_side.jpg" width="280" alt="Handheld Radio, side view"> <img src="images/objects/sniper_radio_set_quarter.jpg" width="280" alt="Handheld Radio, three-quarter view"> <img src="images/objects/sniper_radio_set_third.jpg" width="280" alt="Handheld Radio, far three-quarter view">

#### Rugged Tablet

[Military Pack](https://www.fab.com/listings/295db2f7-fb2e-4f28-9a6c-dcd8ab724747) · **Use:** device · model `SK_Elite_Soldier_Laptop_Mesh` · 16 × 13 × 12 cm

A rugged tablet computer.

**Animations.** **Own:** a part skinned to its character's skeleton (74 bones): it moves with that character's clips.

<img src="images/objects/military_pack_field_laptop_side.jpg" width="280" alt="Rugged Tablet, side view"> <img src="images/objects/military_pack_field_laptop_quarter.jpg" width="280" alt="Rugged Tablet, three-quarter view"> <img src="images/objects/military_pack_field_laptop_third.jpg" width="280" alt="Rugged Tablet, far three-quarter view">

#### Candelabrum

[Medieval Furniture Props](https://www.fab.com/listings/aa584fda-82a3-4f6f-8675-e2f8fab14daf) · **Use:** light / treasure · model `SM_Prop_CandleStand_A` · 298 × 153 × 136 cm

A tall brass candelabrum.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/gothic_props_candlestick_side.jpg" width="280" alt="Candelabrum, side view"> <img src="images/objects/gothic_props_candlestick_quarter.jpg" width="280" alt="Candelabrum, three-quarter view"> <img src="images/objects/gothic_props_candlestick_third.jpg" width="280" alt="Candelabrum, far three-quarter view">

#### Pitchfork

[(Nanite) Medieval Village Kit - Village Props](https://www.fab.com/listings/f9df4890-75d6-4f7e-a0b2-6774ba87c641) · **Use:** tool · model `SM_Pitchfork` · 193 × 38 × 10 cm

A wooden pitchfork with iron tines.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/village_collection_pitchfork_side.jpg" width="280" alt="Pitchfork, side view"> <img src="images/objects/village_collection_pitchfork_quarter.jpg" width="280" alt="Pitchfork, three-quarter view"> <img src="images/objects/village_collection_pitchfork_third.jpg" width="280" alt="Pitchfork, far three-quarter view">

#### Shovel

[(Nanite) Medieval Village Kit - Village Props](https://www.fab.com/listings/f9df4890-75d6-4f7e-a0b2-6774ba87c641) · **Use:** tool · model `SM_Shovel` · 151 × 31 × 9 cm

A long-handled spade.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/village_collection_shovel_side.jpg" width="280" alt="Shovel, side view"> <img src="images/objects/village_collection_shovel_quarter.jpg" width="280" alt="Shovel, three-quarter view"> <img src="images/objects/village_collection_shovel_third.jpg" width="280" alt="Shovel, far three-quarter view">

#### Pickaxe

[Old Mine](https://www.fab.com/listings/dc4dc139-f3a3-4375-875f-d1831506953e) · **Use:** tool · model `SM_His_Med_Tools_Pickaxe_Metal_Old_03` · 87 × 50 × 7 cm

An old pickaxe (a Megascans scan).

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/scene_oldmine_pickaxe_side.jpg" width="280" alt="Pickaxe, side view"> <img src="images/objects/scene_oldmine_pickaxe_quarter.jpg" width="280" alt="Pickaxe, three-quarter view"> <img src="images/objects/scene_oldmine_pickaxe_third.jpg" width="280" alt="Pickaxe, far three-quarter view">

#### Claw Hammer

[Modular Medieval Town, Docks](https://www.fab.com/listings/9bec871e-2d9b-4261-aa26-868d4300f81a) · **Use:** tool · model `SM_Hammer` · 39 × 19 × 4 cm

A claw hammer with a wooden handle.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/hivemind_smith_s_hammer_side.jpg" width="280" alt="Claw Hammer, side view"> <img src="images/objects/hivemind_smith_s_hammer_quarter.jpg" width="280" alt="Claw Hammer, three-quarter view"> <img src="images/objects/hivemind_smith_s_hammer_third.jpg" width="280" alt="Claw Hammer, far three-quarter view">

#### Forge Tongs

[Dwarfs Pack](https://www.fab.com/listings/80643e93-5d54-438c-ae9d-7717242e5a16) · **Use:** tool · model `SM_Tools_For_Animations_Forge_Forceps_Mesh001` · 130 × 41 × 12 cm

A smith's long forge tongs.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/dwarf_pack_forge_tongs_side.jpg" width="280" alt="Forge Tongs, side view"> <img src="images/objects/dwarf_pack_forge_tongs_quarter.jpg" width="280" alt="Forge Tongs, three-quarter view"> <img src="images/objects/dwarf_pack_forge_tongs_third.jpg" width="280" alt="Forge Tongs, far three-quarter view">

#### Duct Tape

[Safe House VOL.1 - Supplies and Guns (Nanite and Low Poly)](https://www.fab.com/listings/46c37125-b9e2-48f1-a5a2-a432959da27f) · **Use:** crafting item · model `SM_Tool_Kit_01a` · 16 × 16 × 6 cm

A roll of grey duct tape.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/safehouse_tool_kit_side.jpg" width="280" alt="Duct Tape, side view"> <img src="images/objects/safehouse_tool_kit_quarter.jpg" width="280" alt="Duct Tape, three-quarter view"> <img src="images/objects/safehouse_tool_kit_third.jpg" width="280" alt="Duct Tape, far three-quarter view">

#### Jerrycan

[Warehouse](https://www.fab.com/listings/a3149fab-3906-4043-b6ee-3937b752a06c) · **Use:** fuel · model `SM_Ind_War_Container_Jerrycan_Metal_Red_03` · 38 × 26 × 23 cm

A rusty red jerrycan (a Megascans scan).

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/scene_warehouse_jerrycan_side.jpg" width="280" alt="Jerrycan, side view"> <img src="images/objects/scene_warehouse_jerrycan_quarter.jpg" width="280" alt="Jerrycan, three-quarter view"> <img src="images/objects/scene_warehouse_jerrycan_third.jpg" width="280" alt="Jerrycan, far three-quarter view">

#### Pocket Watch

[Anemoia Manor](https://www.fab.com/listings/5ff66818-b91e-4705-8a7a-652c771885a9) · **Use:** treasure / tool · model `SM_Watch_01a` · 14 × 10 × 3 cm

A gold pocket watch.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/anemoia_pocket_watch_side.jpg" width="280" alt="Pocket Watch, side view"> <img src="images/objects/anemoia_pocket_watch_quarter.jpg" width="280" alt="Pocket Watch, three-quarter view"> <img src="images/objects/anemoia_pocket_watch_third.jpg" width="280" alt="Pocket Watch, far three-quarter view">

### Treasure, keys and books

#### Gold Coin

[Medieval Castle Kit - Medieval Castle Props](https://www.fab.com/listings/8da1c211-3eca-4c8e-93a3-22796f3b0b87) · **Use:** currency · model `SM_Coin_var1` · 2 × 2 × 0 cm

An embossed gold coin.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/castle_collection_gold_coin_side.jpg" width="280" alt="Gold Coin, side view"> <img src="images/objects/castle_collection_gold_coin_quarter.jpg" width="280" alt="Gold Coin, three-quarter view"> <img src="images/objects/castle_collection_gold_coin_third.jpg" width="280" alt="Gold Coin, far three-quarter view">

#### Coin Pile

[Crownfall: Modular Cathedral Megapack](https://www.fab.com/listings/ef310a60-0412-41fa-822a-ba4e719f6c90) · **Use:** currency · model `SM_S_CoinPack` · 40 × 39 × 2 cm

A scattered pile of silver coins.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/crownfall_coin_purse_side.jpg" width="280" alt="Coin Pile, side view"> <img src="images/objects/crownfall_coin_purse_quarter.jpg" width="280" alt="Coin Pile, three-quarter view"> <img src="images/objects/crownfall_coin_purse_third.jpg" width="280" alt="Coin Pile, far three-quarter view">

#### Gem

[Medieval Castle Kit - Medieval Castle Props](https://www.fab.com/listings/8da1c211-3eca-4c8e-93a3-22796f3b0b87) · **Use:** treasure · model `SM_Gem_Var1` · 7 × 5 × 2 cm

A blue faceted gem.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/castle_collection_gem_side.jpg" width="280" alt="Gem, side view"> <img src="images/objects/castle_collection_gem_quarter.jpg" width="280" alt="Gem, three-quarter view"> <img src="images/objects/castle_collection_gem_third.jpg" width="280" alt="Gem, far three-quarter view">

#### Cut Gem

[Medieval Castle Kit - Medieval Castle Props](https://www.fab.com/listings/8da1c211-3eca-4c8e-93a3-22796f3b0b87) · **Use:** treasure · model `SM_Gem_Var2` · 7 × 7 × 2 cm

A green square-cut gem.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/castle_collection_cut_gem_side.jpg" width="280" alt="Cut Gem, side view"> <img src="images/objects/castle_collection_cut_gem_quarter.jpg" width="280" alt="Cut Gem, three-quarter view"> <img src="images/objects/castle_collection_cut_gem_third.jpg" width="280" alt="Cut Gem, far three-quarter view">

#### Iron Key

[Medieval Castle Kit - Medieval Castle Props](https://www.fab.com/listings/8da1c211-3eca-4c8e-93a3-22796f3b0b87) · **Use:** key · model `SM_Key_Var1` · 11 × 4 × 1 cm

A large iron key with an ornate bow.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/castle_collection_iron_key_side.jpg" width="280" alt="Iron Key, side view"> <img src="images/objects/castle_collection_iron_key_quarter.jpg" width="280" alt="Iron Key, three-quarter view"> <img src="images/objects/castle_collection_iron_key_third.jpg" width="280" alt="Iron Key, far three-quarter view">

#### Brass Key

[Anemoia Manor](https://www.fab.com/listings/5ff66818-b91e-4705-8a7a-652c771885a9) · **Use:** key · model `SM_Key_01a` · 11 × 4 × 1 cm

A brass skeleton key with a scrolled bow.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/anemoia_brass_key_side.jpg" width="280" alt="Brass Key, side view"> <img src="images/objects/anemoia_brass_key_quarter.jpg" width="280" alt="Brass Key, three-quarter view"> <img src="images/objects/anemoia_brass_key_third.jpg" width="280" alt="Brass Key, far three-quarter view">

#### Leather Pouch

[Medieval Castle Kit - Medieval Castle Props](https://www.fab.com/listings/8da1c211-3eca-4c8e-93a3-22796f3b0b87) · **Use:** container · model `SM_LeatherSmallBag` · 13 × 9 × 9 cm

A small tied leather pouch.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/castle_collection_leather_pouch_side.jpg" width="280" alt="Leather Pouch, side view"> <img src="images/objects/castle_collection_leather_pouch_quarter.jpg" width="280" alt="Leather Pouch, three-quarter view"> <img src="images/objects/castle_collection_leather_pouch_third.jpg" width="280" alt="Leather Pouch, far three-quarter view">

#### Gold Lion Statuette

[Medieval Castle Kit - Medieval Castle Props](https://www.fab.com/listings/8da1c211-3eca-4c8e-93a3-22796f3b0b87) · **Use:** treasure · model `SM_GoldLionStatue` · 215 × 184 × 148 cm

A golden statuette of a seated lion.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/castle_collection_gold_lion_statuette_side.jpg" width="280" alt="Gold Lion Statuette, side view"> <img src="images/objects/castle_collection_gold_lion_statuette_quarter.jpg" width="280" alt="Gold Lion Statuette, three-quarter view"> <img src="images/objects/castle_collection_gold_lion_statuette_third.jpg" width="280" alt="Gold Lion Statuette, far three-quarter view">

#### Dwarf King's Crown

[Dwarfs Pack](https://www.fab.com/listings/80643e93-5d54-438c-ae9d-7717242e5a16) · **Use:** treasure / wearable · model `SK_Dwarf_King_Crown` · 27 × 23 × 20 cm

A spiked iron crown with gold scales.

**Animations.** **Own:** a part skinned to its character's skeleton (83 bones): it moves with that character's clips.

<img src="images/objects/dwarf_pack_dwarf_king_s_crown_side.jpg" width="280" alt="Dwarf King's Crown, side view"> <img src="images/objects/dwarf_pack_dwarf_king_s_crown_quarter.jpg" width="280" alt="Dwarf King's Crown, three-quarter view"> <img src="images/objects/dwarf_pack_dwarf_king_s_crown_third.jpg" width="280" alt="Dwarf King's Crown, far three-quarter view">

#### King's Crown

[NPC King And Queen](https://www.fab.com/listings/cf92a409-cb02-460f-a4e1-27039c0e2a99) · **Use:** treasure / wearable · model `SK_UE4_NPC_King_Crown` · 23 × 21 × 17 cm

A jewelled gold crown over a red velvet cap.

**Animations.** **Own:** a part skinned to its character's skeleton (68 bones): it moves with that character's clips.

<img src="images/objects/npc_king_and_queen_king_s_crown_side.jpg" width="280" alt="King's Crown, side view"> <img src="images/objects/npc_king_and_queen_king_s_crown_quarter.jpg" width="280" alt="King's Crown, three-quarter view"> <img src="images/objects/npc_king_and_queen_king_s_crown_third.jpg" width="280" alt="King's Crown, far three-quarter view">

#### Leather Book

[Medieval Castle Kit - Medieval Castle Props](https://www.fab.com/listings/8da1c211-3eca-4c8e-93a3-22796f3b0b87) · **Use:** book · model `SM_Book_Var1` · 35 × 30 × 4 cm

A leather-bound book with gold tooling.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/castle_collection_leather_book_side.jpg" width="280" alt="Leather Book, side view"> <img src="images/objects/castle_collection_leather_book_quarter.jpg" width="280" alt="Leather Book, three-quarter view"> <img src="images/objects/castle_collection_leather_book_third.jpg" width="280" alt="Leather Book, far three-quarter view">

#### Book of Eddrick

[Crownfall: Modular Cathedral Megapack](https://www.fab.com/listings/ef310a60-0412-41fa-822a-ba4e719f6c90) · **Use:** book / quest item · model `SM_S_BookOfEddrick` · 39 × 32 × 10 cm

A thick tooled-leather tome titled 'Book of Eddrick'.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/crownfall_book_of_eddrick_side.jpg" width="280" alt="Book of Eddrick, side view"> <img src="images/objects/crownfall_book_of_eddrick_quarter.jpg" width="280" alt="Book of Eddrick, three-quarter view"> <img src="images/objects/crownfall_book_of_eddrick_third.jpg" width="280" alt="Book of Eddrick, far three-quarter view">

#### Witch's Spellbook

[Fantasy Warriors (Pack)](https://www.fab.com/listings/df8194f9-ec63-49f6-a885-6feb7a94fcb1) · **Use:** spellbook · model `SK_Witch_Book` · 21 × 18 × 12 cm

A chained 'Witchcraft' book with a blue gem.

**Animations.** **Own:** a part skinned to its character's skeleton (68 bones): it moves with that character's clips.

<img src="images/objects/warriors_pack_witch_s_spellbook_side.jpg" width="280" alt="Witch's Spellbook, side view"> <img src="images/objects/warriors_pack_witch_s_spellbook_quarter.jpg" width="280" alt="Witch's Spellbook, three-quarter view"> <img src="images/objects/warriors_pack_witch_s_spellbook_third.jpg" width="280" alt="Witch's Spellbook, far three-quarter view">

#### Ink Bottle

[Victorian Office Environment](https://www.fab.com/listings/2e874e30-de1d-4123-b6cf-c0a4a512c182) · **Use:** item · model `SM_inkBottle` · 15 × 7 × 7 cm

A small black ink bottle.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/victorianoffice_ink_bottle_side.jpg" width="280" alt="Ink Bottle, side view"> <img src="images/objects/victorianoffice_ink_bottle_quarter.jpg" width="280" alt="Ink Bottle, three-quarter view"> <img src="images/objects/victorianoffice_ink_bottle_third.jpg" width="280" alt="Ink Bottle, far three-quarter view">

#### Chess Set

[Victorian Office Environment](https://www.fab.com/listings/2e874e30-de1d-4123-b6cf-c0a4a512c182) · **Use:** game · model `SM_chess` · 110 × 110 × 15 cm

A chess board with its pieces on a marble slab.

**Animations.** **Own:** a static mesh, no clips of its own.

<img src="images/objects/victorianoffice_chess_set_side.jpg" width="280" alt="Chess Set, side view"> <img src="images/objects/victorianoffice_chess_set_quarter.jpg" width="280" alt="Chess Set, three-quarter view"> <img src="images/objects/victorianoffice_chess_set_third.jpg" width="280" alt="Chess Set, far three-quarter view">

### Helmets and masks

#### Viking Helmet

[Viking (Customized)](https://www.fab.com/listings/e814c3a3-11ba-4316-a07a-b0980fd016ef) · **Use:** helmet · model `SK_Viking_Helmet_01` · 39 × 31 × 31 cm

A banded nasal helm with a mail aventail.

**Animations.** **Own:** a part of its character, skinned to the character's skeleton: it plays whatever the character plays.

<img src="images/objects/vikings_viking_helmet_side.jpg" width="280" alt="Viking Helmet, side view"> <img src="images/objects/vikings_viking_helmet_quarter.jpg" width="280" alt="Viking Helmet, three-quarter view"> <img src="images/objects/vikings_viking_helmet_third.jpg" width="280" alt="Viking Helmet, far three-quarter view">

#### Great Helm

[Knights (Pack)](https://www.fab.com/listings/6907d3d8-d0db-43c0-bf9c-8ad43c70e7b3) · **Use:** helmet · model `SK_Knight_01_Helmet` · 31 × 26 × 22 cm

A flat-topped great helm with a cross.

**Animations.** **Own:** a part of its character, skinned to the character's skeleton: it plays whatever the character plays.

<img src="images/objects/knights_pack_great_helm_side.jpg" width="280" alt="Great Helm, side view"> <img src="images/objects/knights_pack_great_helm_quarter.jpg" width="280" alt="Great Helm, three-quarter view"> <img src="images/objects/knights_pack_great_helm_third.jpg" width="280" alt="Great Helm, far three-quarter view">

#### Kabuto

[SAMURAI](https://www.fab.com/listings/5f4c90b7-a282-45fc-89df-61468afc867b) · **Use:** helmet · model `SK_Samurai_Helmet_01` · 40 × 34 × 27 cm

A samurai kabuto with crescent horns.

**Animations.** **Own:** a part of its character, skinned to the character's skeleton: it plays whatever the character plays.

<img src="images/objects/samurai_kabuto_side.jpg" width="280" alt="Kabuto, side view"> <img src="images/objects/samurai_kabuto_quarter.jpg" width="280" alt="Kabuto, three-quarter view"> <img src="images/objects/samurai_kabuto_third.jpg" width="280" alt="Kabuto, far three-quarter view">

#### Samurai War Mask

[SAMURAI](https://www.fab.com/listings/5f4c90b7-a282-45fc-89df-61468afc867b) · **Use:** mask · model `SK_Samurai_Mask` · 18 × 18 × 17 cm

A red menpo war mask with teeth and a moustache.

**Animations.** **Own:** a part of its character, skinned to the character's skeleton: it plays whatever the character plays.

<img src="images/objects/samurai_samurai_war_mask_side.jpg" width="280" alt="Samurai War Mask, side view"> <img src="images/objects/samurai_samurai_war_mask_quarter.jpg" width="280" alt="Samurai War Mask, three-quarter view"> <img src="images/objects/samurai_samurai_war_mask_third.jpg" width="280" alt="Samurai War Mask, far three-quarter view">

#### Plague Doctor's Mask

[NPC King And Queen](https://www.fab.com/listings/cf92a409-cb02-460f-a4e1-27039c0e2a99) · **Use:** mask · model `SK_UE4_NPC_Plague_doctor_Mask` · 42 × 24 × 19 cm

A leather plague doctor's beak mask with goggles.

**Animations.** **Own:** a part of its character, skinned to the character's skeleton: it plays whatever the character plays.

<img src="images/objects/npc_king_and_queen_plague_doctor_s_mask_side.jpg" width="280" alt="Plague Doctor's Mask, side view"> <img src="images/objects/npc_king_and_queen_plague_doctor_s_mask_quarter.jpg" width="280" alt="Plague Doctor's Mask, three-quarter view"> <img src="images/objects/npc_king_and_queen_plague_doctor_s_mask_third.jpg" width="280" alt="Plague Doctor's Mask, far three-quarter view">

#### Wizard's Hat

[Dungeon Builder: Modular Top Down RPG Environment Kit](https://www.fab.com/listings/10cbf8dd-ef59-48f8-bbea-606a2b66774d) · **Use:** hat · model `SK_MaleWizard_Hat01` · 55 × 54 × 43 cm

A floppy brown wizard's hat.

**Animations.** **Own:** a part of its character, skinned to the character's skeleton: it plays whatever the character plays.

<img src="images/objects/mysticdungeon_wizard_s_hat_side.jpg" width="280" alt="Wizard's Hat, side view"> <img src="images/objects/mysticdungeon_wizard_s_hat_quarter.jpg" width="280" alt="Wizard's Hat, three-quarter view"> <img src="images/objects/mysticdungeon_wizard_s_hat_third.jpg" width="280" alt="Wizard's Hat, far three-quarter view">

#### Gas Mask

[Tactical Masks](https://www.fab.com/listings/2362889e-5c63-4a0b-9391-7ca1b0b9c72f) · **Use:** mask · model `SK_UE4_Gas_mask_01` · 40 × 39 × 22 cm

A grey rubber gas mask with a filter.

**Animations.** **Own:** a part of its character, skinned to the character's skeleton: it plays whatever the character plays.

<img src="images/objects/tactical_masks_gas_mask_side.jpg" width="280" alt="Gas Mask, side view"> <img src="images/objects/tactical_masks_gas_mask_quarter.jpg" width="280" alt="Gas Mask, three-quarter view"> <img src="images/objects/tactical_masks_gas_mask_third.jpg" width="280" alt="Gas Mask, far three-quarter view">

#### Tactical Mask

[Tactical Masks](https://www.fab.com/listings/2362889e-5c63-4a0b-9391-7ca1b0b9c72f) · **Use:** mask · model `SK_UE4_Tactical_mask_01` · 28 × 27 × 18 cm

A black tactical face mask on straps.

**Animations.** **Own:** a part of its character, skinned to the character's skeleton: it plays whatever the character plays.

<img src="images/objects/tactical_masks_tactical_mask_side.jpg" width="280" alt="Tactical Mask, side view"> <img src="images/objects/tactical_masks_tactical_mask_quarter.jpg" width="280" alt="Tactical Mask, three-quarter view"> <img src="images/objects/tactical_masks_tactical_mask_third.jpg" width="280" alt="Tactical Mask, far three-quarter view">

#### Pilot's Helmet

[Astronauts (Pack)](https://www.fab.com/listings/69267151-497d-494f-9592-551cd39246a2) · **Use:** helmet · model `SK_Astronaut_Pilot_Helmet` · 35 × 34 × 31 cm

A white flight helmet with a visor.

**Animations.** **Own:** a part of its character, skinned to the character's skeleton: it plays whatever the character plays.

<img src="images/objects/astronauts_pack_pilot_s_helmet_side.jpg" width="280" alt="Pilot's Helmet, side view"> <img src="images/objects/astronauts_pack_pilot_s_helmet_quarter.jpg" width="280" alt="Pilot's Helmet, three-quarter view"> <img src="images/objects/astronauts_pack_pilot_s_helmet_third.jpg" width="280" alt="Pilot's Helmet, far three-quarter view">

#### VR Headset

Geek Room · **Use:** wearable · model `SK_UE4_Girl_for_room_Virtual_reality_helmet` · 30 × 25 × 24 cm

A bulky home-made VR headset.

**Animations.** **Own:** a part of its character, skinned to the character's skeleton: it plays whatever the character plays.

<img src="images/objects/girl_vr_headset_side.jpg" width="280" alt="VR Headset, side view"> <img src="images/objects/girl_vr_headset_quarter.jpg" width="280" alt="VR Headset, three-quarter view"> <img src="images/objects/girl_vr_headset_third.jpg" width="280" alt="VR Headset, far three-quarter view">

## Not included

- **Parts:** magazines, cartridges, bullets, sleeves, sights, silencers, flashlights, scabbards and holsters, sold with the guns and blades as separate meshes.
- **Duplicates and variants:** the same weapon in several volumes or colours, the fake toy weapons of `HOLIDAY`, a pack's second and third version of a shield, sword or spear.
- **Scenery:** tables, racks and shelves with weapons on them (`Safehouse`'s gunsmith tables), weapon statues, spike barriers, the `Crownfall` spear-knight statues; furniture, lamps, food stalls and other set dressing.
- **Clothing:** bags, belts, backpacks and armour pieces that only make sense on their character; a few helmets and masks are shown as wearable items.
- **The project's own:** the castle furniture kit's props (the tankard, the cart), modelled for this project.
