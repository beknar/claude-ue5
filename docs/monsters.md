# Monsters of the Fab library, ranked by looks

Every monster in the local Fab library cache (`I:\game assets\3d epicgames media packs\VaultCache\FabLibrary`), ranked from the one that looks easiest to defeat (1) to the one that looks toughest to beat (107). **Looks only**: nothing here comes from hit points, animations or any game data, just what the model looks like standing in front of you.

What counts as tougher-looking: size and bulk; armour, shells and plates; blades, claws, scythes, spikes and horns; extra limbs; teeth. What counts as easier: small, thin, legless or crippled, trapped, unarmed, or drawn as a cartoon.

## How the list was made

- **Which packs:** every pack in the cache whose models are creatures rather than people, props or rooms: the packs tagged *Monster* or *Creature* in their listing data, plus the orcs, zombies, aliens and beast warriors.
- **Rendering:** every model was rendered in this project in its reference pose (arms out), with its own textures. A 180 cm post stands beside it for scale (it is cut off in the pictures of small creatures).
- **Unity-only packs:** the Creatures Insects Pack and the Humanoids Monsters Pack exist only in Unity format, so they were unpacked (`pipeline/blender_numpy/unity_extract.py`) and imported for this (`pipeline/unreal/900_monster_gallery.py unity`).
- **Heights:** the height column is the model's bounding box in that pose, in cm. Most humanoids come out at about 180–200 cm whatever their build, so bulk matters more than the number. For models holding something up (a staff, horns, wings), the item is included.

## The pictures

Each monster is shown four times, left to right:

- **original:** its own textures and colours.
- **infernal:** charred red-black skin with ember highlights; a cracked-stone pattern, some of whose cracks glow.
- **venom:** sickly green to yellow, with scales.
- **frost:** pale ice-blue and glossier, with crystal facets and a cold glint along their edges.

The three alternates come from one material (`M_MON_Variant`). It keeps the model's own normal map, and maps the brightness of its own colour texture onto the scheme's dark, middle and light colours, so the original's painted detail survives. It then adds a pattern computed from the position on the body, so it covers every model the same way and stays put however the monster moves.

Pictures and this page are made by `pipeline/unreal/900_monster_gallery.py` (`stage`, `warm`, `shoot`) and `pipeline/blender_numpy/monster_doc.py`. The ranking itself is `claude_ue5/SourceArt/monster_gallery/monsters.json`.

## Tier 1: pushovers

| # | Monster | Pack | Model | Height | Looks | original · infernal · venom · frost |
|---|---|---|---|---|---|---|
| 1 | Rat | Cartoon Zombies (Pack) | `SK_Rat` | 50 | A cartoon rat, knee high | ![Rat](images/monsters/001_rat.jpg) |
| 2 | Half Creature 04 | Creeping Creatures Pack | `Half_Creatures_04` | 94 | A torso with no legs, dragging itself along on its arms | ![Half Creature 04](images/monsters/002_half_creature_04.jpg) |
| 3 | Parasite Slider | Parasites Pack | `SK_Parasite_Slider` | 88 | A man's upper body on a slug's tail; slow by the look of it | ![Parasite Slider](images/monsters/003_parasite_slider.jpg) |
| 4 | Man In Gut | Creeping Creatures Pack | `SK_Man_In_Gut` | 251 | A body hanging head down in a sack of gut: trapped, not fighting | ![Man In Gut](images/monsters/004_man_in_gut.jpg) |
| 5 | Half Creature 05 | Creeping Creatures Pack | `Half_Creatures_05` | 96 | A legless torso trailing its innards; long thin clawed arms, but waist high | ![Half Creature 05](images/monsters/005_half_creature_05.jpg) |
| 6 | Drinker | Cartoon Zombies (Pack) | `SK_Drinker` | 188 | Skinny cartoon zombie in shorts, bulging eyes | ![Drinker](images/monsters/006_drinker.jpg) |
| 7 | Medic | Cartoon Zombies (Pack) | `SK_Medic` | 181 | Skinny, skull-faced, in a gown | ![Medic](images/monsters/007_medic.jpg) |
| 8 | Boy | Cartoon Zombies (Pack) | `SK_Boy` | 212 | A cartoon kid | ![Boy](images/monsters/008_boy.jpg) |
| 9 | Chicken | Cartoon Zombies (Pack) | `SK_Chicken` | 199 | A zombie in a chicken costume | ![Chicken](images/monsters/009_chicken.jpg) |
| 10 | Soldier | Cartoon Zombies (Pack) | `SK_Soldier` | 180 | Scrawny cartoon zombie in a helmet, unarmed | ![Soldier](images/monsters/010_soldier.jpg) |
| 11 | Half Creature 01 | Creeping Creatures Pack | `Half_Creatures_01` | 188 | An upper body hanging over a trail of guts, no legs | ![Half Creature 01](images/monsters/011_half_creature_01.jpg) |
| 12 | Half Creature 03 | Creeping Creatures Pack | `Half_Creatures_03` | 184 | An emaciated torso on a chain | ![Half Creature 03](images/monsters/012_half_creature_03.jpg) |
| 13 | Half Creature 02 | Creeping Creatures Pack | `Half_Creatures_02` | 189 | A legless torso in a tactical vest, guts for a lower body | ![Half Creature 02](images/monsters/013_half_creature_02.jpg) |

## Tier 2: weak but unpleasant

| # | Monster | Pack | Model | Height | Looks | original · infernal · venom · frost |
|---|---|---|---|---|---|---|
| 14 | Sufferer | 14 Orcs Pack | `SK_Sufferer_Full` | 188 | Robed and barefoot; no armour, no weapon | ![Sufferer](images/monsters/014_sufferer.jpg) |
| 15 | Fat | Cartoon Zombies (Pack) | `SK_Fat` | 201 | Huge belly and a cap: slow | ![Fat](images/monsters/015_fat.jpg) |
| 16 | Mask | Cartoon Zombies (Pack) | `SK_Mask` | 182 | Chubby, in a gas mask | ![Mask](images/monsters/016_mask.jpg) |
| 17 | Monster | Cartoon Zombies (Pack) | `SK_Monster` | 179 | Hunched, ape-like cartoon brute with a big grin | ![Monster](images/monsters/017_monster.jpg) |
| 18 | Gunner | Cartoon Zombies (Pack) | `SK_Gunner` | 178 | Stocky, carries a big launcher, cartoon proportions | ![Gunner](images/monsters/018_gunner.jpg) |
| 19 | Fat | Parasites Pack | `SK_Fat` | 185 | A fat man with tentacles bursting from his shoulder | ![Fat](images/monsters/019_fat.jpg) |
| 20 | Parasit | Parasites Pack | `SK_Parasit` | 180 | A man with a creature erupting from his chest and head, one claw | ![Parasit](images/monsters/020_parasit.jpg) |
| 21 | Creature 01 | Sci-Fi Line With 3 Creatures | `SK_UE4_Creatures_01_Full` | 188 | Skinned, thin humanoid with a swollen belly | ![Creature 01](images/monsters/021_creature_01.jpg) |
| 22 | Creature 03 | Sci-Fi Line With 3 Creatures | `SK_UE4_Creatures_03_Full` | 185 | Skinned and thin, with a split, crested head | ![Creature 03](images/monsters/022_creature_03.jpg) |
| 23 | Creature 05 | Humanoids Creatures Pack | `SK_Creature_05` | 186 | Lean, long ridged skull, nothing to fight with | ![Creature 05](images/monsters/023_creature_05.jpg) |
| 24 | Monster Underwater 04 | Monsters Underwater Pack | `SK_Monster_Underwater_04` | 200 | Lean fish-man with a fin crest and small hands | ![Monster Underwater 04](images/monsters/024_monster_underwater_04.jpg) |
| 25 | Orc 03 | 14 Orcs Pack | `SK_Orc_03_Full` | 186 | A skinny orc in a spiked cage helmet and light leg armour | ![Orc 03](images/monsters/025_orc_03.jpg) |

## Tier 3: an even fight

| # | Monster | Pack | Model | Height | Looks | original · infernal · venom · frost |
|---|---|---|---|---|---|---|
| 26 | Magur | 14 Orcs Pack | `SK_Magur_Full` | 181 | Very fat, barely armoured, a little creature on his head | ![Magur](images/monsters/026_magur.jpg) |
| 27 | Azrak | 14 Orcs Pack | `SK_Azrak_Full` | 184 | Big-bellied, loincloth, a spiked mask | ![Azrak](images/monsters/027_azrak.jpg) |
| 28 | Alien Warrior 03 | Aliens Warrior Pack | `SK_UE4_Alien_Warrior_03_Full_01` | 183 | The most human-looking alien: long coat, belt pouches | ![Alien Warrior 03](images/monsters/028_alien_warrior_03.jpg) |
| 29 | Warrior 02 (the leopard) | Animals Warrior Pack | `SK_Warrior_02_Full_01` | 185 | Hooded leopard-man in cloth and light armour | ![Warrior 02 (the leopard)](images/monsters/029_warrior_02_the_leopard.jpg) |
| 30 | Kanit | 14 Orcs Pack | `SK_Kanit_Full` | 186 | Hooded orc with spiked bracers | ![Kanit](images/monsters/030_kanit.jpg) |
| 31 | Gnur | 14 Orcs Pack | `SK_Gnur_Full` | 184 | Robed orc, spikes on the shoulders | ![Gnur](images/monsters/031_gnur.jpg) |
| 32 | Dardan | 14 Orcs Pack | `SK_Dardan_Full` | 182 | Tusked, bone necklace, spiked greaves | ![Dardan](images/monsters/032_dardan.jpg) |
| 33 | Costalmed | 14 Orcs Pack | `SK_Orc_Costalmed_Full` | 189 | Half armoured: heavy leg plates and a shoulder guard | ![Costalmed](images/monsters/033_costalmed.jpg) |
| 34 | Orc 05 | 14 Orcs Pack | `SK_Orc_05_Full` | 190 | Fat but armoured: belt plate, greaves, a mask | ![Orc 05](images/monsters/034_orc_05.jpg) |
| 35 | Orc 06 | 14 Orcs Pack | `SK_Orc_06_Full` | 188 | Lean, spiked shoulder and arm armour | ![Orc 06](images/monsters/035_orc_06.jpg) |
| 36 | Creature 02 | Sci-Fi Line With 3 Creatures | `SK_UE4_Creatures_02_Full` | 188 | Skinned and muscular, one arm a long blade | ![Creature 02](images/monsters/036_creature_02.jpg) |
| 37 | Alien | Creatures Mega Pack | `SK_Alien` | 200 | Tall and gangly, long arms, small head | ![Alien](images/monsters/037_alien.jpg) |
| 38 | Devourer | Creatures Mega Pack | `SK_Devourer` | 202 | Lanky, a wide mouth, long clawed arms | ![Devourer](images/monsters/038_devourer.jpg) |
| 39 | Insect | Creatures Mega Pack | `SK_Insect` | 182 | A man-sized winged insect on thin legs | ![Insect](images/monsters/039_insect.jpg) |
| 40 | Creepy | Creatures Mega Pack | `SK_Creepy` | 168 | A low, flat crawler with long reaching limbs and a toothy maw | ![Creepy](images/monsters/040_creepy.jpg) |
| 41 | Pangolin | Creatures Mega Pack | `SK_Pangolin` | 171 | Four-legged, toothy, a spiked tail | ![Pangolin](images/monsters/041_pangolin.jpg) |
| 42 | Monster Underwater 02 | Monsters Underwater Pack | `SK_Monster_Underwater_02_Body` + `_Shell` | 185 | Muscular fish-man with a gaping, toothy head | ![Monster Underwater 02](images/monsters/042_monster_underwater_02.jpg) |
| 43 | Monster Underwater 03 | Monsters Underwater Pack | `SK_Monster_Underwater_03` | 179 | Muscular, a hammerhead bar across the head | ![Monster Underwater 03](images/monsters/043_monster_underwater_03.jpg) |
| 44 | Creature 03 | Humanoids Creatures Pack | `SK_Creature_03` | 189 | Lumpy, spiny skin, a crown of horns | ![Creature 03](images/monsters/044_creature_03.jpg) |
| 45 | Creature 02 | Humanoids Creatures Pack | `SK_Creature_02` | 208 | A tentacled head on a man's body in a vest and trousers | ![Creature 02](images/monsters/045_creature_02.jpg) |
| 46 | Creature 07 | 10 Creatures (Pack) | `SK_Creature_07` | 188 | Lean demon, small crested head, no weapon | ![Creature 07](images/monsters/046_creature_07.jpg) |
| 47 | Creature 02 | 10 Creatures (Pack) | `SK_Creature_02` | 186 | Lean demon with ram horns | ![Creature 02](images/monsters/047_creature_02.jpg) |
| 48 | Creature 03 | 10 Creatures (Pack) | `SK_Creature_03` | 186 | Lean demon with a crown of tendrils | ![Creature 03](images/monsters/048_creature_03.jpg) |
| 49 | Tank | Cartoon Zombies (Pack) | `SK_Tank_Mesh` | 180 | A cartoon zombie driving a toy-like tank with a cannon: armoured, but silly | ![Tank](images/monsters/049_tank.jpg) |
| 50 | Monster 04 | Humanoids Monsters Pack | `SK_Monster_04` | 182 | Lean, pinkish, ribbed belly, a skull of a face | ![Monster 04](images/monsters/050_monster_04.jpg) |
| 51 | Monster 05 | Humanoids Monsters Pack | `SK_Monster_05` | 181 | Grey and lean, a long flat skull, small claws | ![Monster 05](images/monsters/051_monster_05.jpg) |
| 52 | Creature Insect 02 | Creatures Insects Pack | `SK_Creature_Insect_02` | 223 | Thin golden grasshopper-man with huge eyes and long antennae | ![Creature Insect 02](images/monsters/052_creature_insect_02.jpg) |
| 53 | Creature Insect 05 | Creatures Insects Pack | `SK_Creature_Insect_05` | 218 | Thin pale-green mantis-man with pink eyes | ![Creature Insect 05](images/monsters/053_creature_insect_05.jpg) |
| 54 | Monster 03 | Humanoids Monsters Pack | `SK_Monster_03` | 193 | Grey-blue and pink, a toothy crested head, spines on the forearms | ![Monster 03](images/monsters/054_monster_03.jpg) |
| 55 | Creature Insect 04 | Creatures Insects Pack | `SK_Creature_Insect_04` | 206 | Copper carapace, branching antlers, clawed fingers | ![Creature Insect 04](images/monsters/055_creature_insect_04.jpg) |
| 56 | Monster 01 | Humanoids Monsters Pack | `SK_Monster_01` | 195 | Bulky, orange and lumpy, curled horns | ![Monster 01](images/monsters/056_monster_01.jpg) |
| 57 | Monster 02 | Humanoids Monsters Pack | `SK_Monster_02` | 192 | Orange-gold, a sweeping crown of horns, spiked shoulders | ![Monster 02](images/monsters/057_monster_02.jpg) |
| 58 | Creature Insect 01 | Creatures Insects Pack | `SK_Creature_Insect_01` | 213 | Blue armoured beetle-man with a great horn | ![Creature Insect 01](images/monsters/058_creature_insect_01.jpg) |
| 59 | Creature Insect 03 | Creatures Insects Pack | `SK_Creature_Insect_03` | 186 | Heavy dark carapace, a frilled head, long curved blades for arms | ![Creature Insect 03](images/monsters/059_creature_insect_03.jpg) |

## Tier 4: dangerous

| # | Monster | Pack | Model | Height | Looks | original · infernal · venom · frost |
|---|---|---|---|---|---|---|
| 60 | Orc 01 | 14 Orcs Pack | `SK_Orc_01_Full` | 186 | Armoured, spiked arm guards, tusks, skull on the belt | ![Orc 01](images/monsters/060_orc_01.jpg) |
| 61 | Orc 02 | 14 Orcs Pack | `SK_Orc_02_Full` | 184 | Full spiked armour, blade-edged gauntlets | ![Orc 02](images/monsters/061_orc_02.jpg) |
| 62 | Ursag | 14 Orcs Pack | `SK_Ursag_Full` | 197 | Antlered helm, fur and bone armour | ![Ursag](images/monsters/062_ursag.jpg) |
| 63 | Orc 04 | 14 Orcs Pack | `SK_Orc_04_Full` | 239 | A shaman under a totem of skulls | ![Orc 04](images/monsters/063_orc_04.jpg) |
| 64 | Bear Warrior | Animals Warrior Pack | `SK_Bear_Full` | 182 | Bear-man in a shaggy pelt | ![Bear Warrior](images/monsters/064_bear_warrior.jpg) |
| 65 | Bull Warrior | Animals Warrior Pack | `SK_Bull_Full` | 196 | Horned bull-man in plate armour | ![Bull Warrior](images/monsters/065_bull_warrior.jpg) |
| 66 | Crocodile Warrior | Animals Warrior Pack | `SK_Crocodile_Full` | 185 | Crocodile head, armour, trophies on the belt | ![Crocodile Warrior](images/monsters/066_crocodile_warrior.jpg) |
| 67 | Elephant Warrior | Animals Warrior Pack | `SK_Elephant_Full` | 187 | Elephant-man in full plate | ![Elephant Warrior](images/monsters/067_elephant_warrior.jpg) |
| 68 | Alien Warrior 05 | Aliens Warrior Pack | `SK_UE4_Alien_Warrior_05_Full_01` | 183 | Lean and muscular, crested head | ![Alien Warrior 05](images/monsters/068_alien_warrior_05.jpg) |
| 69 | Alien Warrior 01 | Aliens Warrior Pack | `SK_UE4_Alien_Warrior_01_Full_01` | 188 | Hunched and broad, armour plates | ![Alien Warrior 01](images/monsters/069_alien_warrior_01.jpg) |
| 70 | Alien Warrior 02 | Aliens Warrior Pack | `SK_UE4_Alien_Warrior_02_Full_01` | 185 | Bulky, heavy armour | ![Alien Warrior 02](images/monsters/070_alien_warrior_02.jpg) |
| 71 | Alien Warrior 04 | Aliens Warrior Pack | `SK_UE4_Alien_Warrior_04_Full_01` | 185 | Long claw blades on both hands | ![Alien Warrior 04](images/monsters/071_alien_warrior_04.jpg) |
| 72 | Creature 01 | Humanoids Creatures Pack | `SK_Creature_01` | 228 | A huge horn-like growth curling up from the shoulder | ![Creature 01](images/monsters/072_creature_01.jpg) |
| 73 | Creature 04 | Humanoids Creatures Pack | `SK_Creature_04` | 203 | Head swollen into a mass of tumours, lumpy body | ![Creature 04](images/monsters/073_creature_04.jpg) |
| 74 | Monster Underwater 01 | Monsters Underwater Pack | `SK_Monster_Underwater_01` | 187 | A spear-like snout across the head, spiny legs | ![Monster Underwater 01](images/monsters/074_monster_underwater_01.jpg) |
| 75 | Creature 08 | 10 Creatures (Pack) | `SK_Creature_08` | 191 | Broad-shouldered demon, wide horned head | ![Creature 08](images/monsters/075_creature_08.jpg) |
| 76 | Creature 10 | 10 Creatures (Pack) | `SK_Creature_10` | 190 | Skull face, ram horns, heavy build | ![Creature 10](images/monsters/076_creature_10.jpg) |
| 77 | Creature 01 | 10 Creatures (Pack) | `SK_Creature_01` | 192 | Horned, spiked shoulders, clawed feet | ![Creature 01](images/monsters/077_creature_01.jpg) |
| 78 | Creature 09 | 10 Creatures (Pack) | `SK_Creature_09` | 186 | Ripped, a crown of tendrils and tusks | ![Creature 09](images/monsters/078_creature_09.jpg) |
| 79 | Creature 06 | 10 Creatures (Pack) | `SK_Creature_06` | 206 | A huge fat horned bulk | ![Creature 06](images/monsters/079_creature_06.jpg) |
| 80 | Creature 04 | 10 Creatures (Pack) | `SK_Creature_04` | 199 | Horned, a blade for one arm and a hooked scythe in the other | ![Creature 04](images/monsters/080_creature_04.jpg) |
| 81 | Creature 05 | 10 Creatures (Pack) | `SK_Creature_05` | 184 | Two long blades for arms | ![Creature 05](images/monsters/081_creature_05.jpg) |
| 82 | Exterminator | Creatures Mega Pack | `SK_Exterminator` | 202 | Hulking brute | ![Exterminator](images/monsters/082_exterminator.jpg) |
| 83 | Shell | Creatures Mega Pack | `SK_Shell` | 200 | Pale armoured brute with big claws | ![Shell](images/monsters/083_shell.jpg) |
| 84 | Bug | Creatures Mega Pack | `SK_Bug` | 200 | Blue armoured insect-man, spiked forearms | ![Bug](images/monsters/084_bug.jpg) |
| 85 | Horned | Creatures Mega Pack | `SK_Horned` | 207 | Horned devil, long clawed arms | ![Horned](images/monsters/085_horned.jpg) |
| 86 | Mutant | Creatures Mega Pack | `SK_Mutant` | 201 | Muscular, one arm a long tentacle | ![Mutant](images/monsters/086_mutant.jpg) |
| 87 | Ripper dog | Creatures Mega Pack | `SK_Ripper_dog` | 194 | A big snarling hound with quills on its back | ![Ripper dog](images/monsters/087_ripper_dog.jpg) |
| 88 | Daemon | Creatures Mega Pack | `SK_Daemon` | 219 | Tall, bat-eared, clawed | ![Daemon](images/monsters/088_daemon.jpg) |
| 89 | Troll | Creatures Mega Pack | `SK_Troll` | 201 | Heavily muscled and tusked | ![Troll](images/monsters/089_troll.jpg) |
| 90 | Executioner | Fantasy Enemies (Pack) | `SK_Executioner_Full` | 185 | Big armoured man, spiked shoulders | ![Executioner](images/monsters/090_executioner.jpg) |
| 91 | Monster Underwater 05 | Monsters Underwater Pack | `SK_Monster_Underwater_05` | 184 | Crab claws, spiked shell armour, horned head | ![Monster Underwater 05](images/monsters/091_monster_underwater_05.jpg) |
| 92 | Monster For Capsule | Monster In Capsule | `SK_UE4_Monster_For_Capsule_Full` | 201 | Horned, long blade claws on both hands | ![Monster For Capsule](images/monsters/092_monster_for_capsule.jpg) |
| 93 | Parasite Spider | Parasites Pack | `SK_Parasite_Spider` | 199 | A human body on spider legs | ![Parasite Spider](images/monsters/093_parasite_spider.jpg) |
| 94 | Fantasy Animal (raptor mount) | Fantasy Animal (Pack) | `SK_Fantasy_Animal_Full` | 205 | Saddled raptor: jaws and clawed feet | ![Fantasy Animal (raptor mount)](images/monsters/094_fantasy_animal_raptor_mount.jpg) |

## Tier 5: bosses

| # | Monster | Pack | Model | Height | Looks | original · infernal · venom · frost |
|---|---|---|---|---|---|---|
| 95 | Alfa | Parasites Pack | `SK_Alfa` | 217 | Fanged, hulking, one arm a giant scythe | ![Alfa](images/monsters/095_alfa.jpg) |
| 96 | Demon | Fantasy Enemies (Pack) | `SK_Demon_Full` | 202 | Horned, in layered armour | ![Demon](images/monsters/096_demon.jpg) |
| 97 | Befouler | Fantasy Enemies (Pack) | `SK_Befouler_Full_01` | 200 | Giant curved horns, skulls carried on its back | ![Befouler](images/monsters/097_befouler.jpg) |
| 98 | Devil | Fantasy Enemies (Pack) | `SK_Devil_Full` | 197 | Horned, spikes all over | ![Devil](images/monsters/098_devil.jpg) |
| 99 | Troll | Fantasy Enemies (Pack) | `SK_Troll_Full_01` | 198 | Bristling with spikes and armour plates | ![Troll](images/monsters/099_troll.jpg) |
| 100 | Spider | Creatures Mega Pack | `SK_Spider` | 250 | Scythe legs, an open ribcage of a chest | ![Spider](images/monsters/100_spider.jpg) |
| 101 | Rock | Creatures Mega Pack | `SK_Rock` | 330 | Spines on its back, long claws | ![Rock](images/monsters/101_rock.jpg) |
| 102 | Titan | Creatures Mega Pack | `SK_Titan` | 250 | Massive clawed arms | ![Titan](images/monsters/102_titan.jpg) |
| 103 | Hunter | Creatures Mega Pack | `SK_Hunter` | 253 | A giant hulk on its knuckles | ![Hunter](images/monsters/103_hunter.jpg) |
| 104 | Nasty | Creatures Mega Pack | `SK_Nasty` | 270 | A giant spider, 6.7 m long | ![Nasty](images/monsters/104_nasty.jpg) |
| 105 | Fantasy Elephant | Fantasy Animal (Pack) | `SK_Fantasy_Elephant_Full` | 705 | A 7 m war elephant, armoured, spikes on the tusks | ![Fantasy Elephant](images/monsters/105_fantasy_elephant.jpg) |
| 106 | Fantasy Elephant with a tower | Fantasy Animal (Pack) | `SK_Fantasy_Elephant_Build_Full` | 1070 | The war elephant carrying a fortified tower | ![Fantasy Elephant with a tower](images/monsters/106_fantasy_elephant_with_a_tower.jpg) |
| 107 | Fantasy Dragon | Fantasy Animal (Pack) | `SK_Fantasy_Dragon_Full` | 308 | A dragon with a 12 m wingspan | ![Fantasy Dragon](images/monsters/107_fantasy_dragon.jpg) |

## Not ranked

- **Pack animals:** the camel (`SK_Camel_Full`) and the laden buffalo (`SK_Bull_Fantasy_Full`) of the Fantasy Animal (Pack). They carry baggage; they are not monsters.
- **Creatures Mega Pack models that are not imported:** `Fat`, `Organic_trap`, `Poisonous_claw`, `Cocoon` and `Character_01` are in the cached pack but not in this project, so they could not be seen on their own.
- **Not creatures:**
  - Baby In Capsule: a human baby.
  - Sci-FI Creocapsule: a capsule prop overgrown with organic matter.
  - Sci-Fi Experimental: a lab with a specimen lying on the table, with no character model.
  - The scientist (`NPC_Scientist`) of Monster In Capsule.
