# AI models

The characters this project uses in its current and future scenes, made with [Tripo](https://www.tripo3d.ai/).

| Model | Former name | What it is | Used in |
|---|---|---|---|
| `Warrior.glb` | `jrpg-fem5-tripo.glb` | JRPG heroine (sword, shield, spear, axe) | random_level, random_dungeon_level, random_isometric_village_level, random_dungeoncombat_level, the Tripo trio and quartet showcases |
| `Warrior2.glb` | (none) | The Warrior's mesh, weights and texture with Tripo's clips: `chop`, `slash` (the same motion) and a horizontal two-handed sweep | random_dungeonmagic_level5's chop test only (character `Warrior2`, script `861`); the heroes do not use it |
| `Warrior3.glb` | (none) | The Warrior of random_dungeonmagic_level5 since 2026-10-26: a new Tripo model (her own proportions) with Tripo's clips: idle, walk, run, slash, five hit reactions, two boxing moves, a kick, a clap, a dance, a wave | random_dungeonmagic_level5 (character `Warrior3`, script `862`: the hero "Warrior"; her slash for two-handed swords) and its reels |
| `Mage.glb` | `girl-caster-tripo.glb` | Fire caster | random_dungeonmagic_level, the Tripo trio and quartet showcases |
| `Warlock.glb` | `girl-darkcaster-tripo.glb` | Dark caster (spell in the left hand, sword in the right) | random_dungeonmagic_level2, the Tripo trio and quartet showcases |
| `Rogue.glb` | (none) | Hooded rogue (two daggers, a crossbow) | random_dungeonmagic_level3 (tag `Rogue`), the Tripo quartet showcase; the source of the Rogue's attacks carried onto `Rogue2.glb` |
| `Rogue2.glb` | (none) | Rogue in a long coat, rigged (80 bones), with Tripo's clips: walk, run, idle, five hit reactions | The Rogue of every map since 2026-11-11 (character `Rogue`, script `918`: her own walk, run, idle and hits, her stabs, crossbow shot, rolls and bow draw carried from `Rogue.glb` by `martialartist3_retarget.py`) |
| `Summoner5.glb` | (none) | Witch-hatted summoner in a long cloak, rigged (80 bones), with Tripo's walk and run | The Summoner of every map since 2026-11-11 (character `Summoner4`, script `918`: her idle made by `summoner5_idle.py`, her cloak given bones of its own by `summoner5_cloak.py`, her casts, knife stabs and flinch carried from `Summoner4.glb`) |
| `Summoner.glb` | (none) | Twin-tailed summoner (the Mage's spells; a face that shows expressions) | the first random_dungeonmagic_level5 (character `Summoner`, scripts `832`-`841`) and its face reels |
| `Summoner2.glb` | (none) | Realistic summoner (made from two AI-generated pictures), fitted with a whole MetaHuman | the Summoner2 version of random_dungeonmagic_level5 (scripts `842`-`848`; set aside) |
| `Summoner3.glb` | (none) | Summoner (the Mage's spells; wears the armour she finds) | random_dungeonmagic_level5 (character `Summoner3`, the fifth hero; off the hero menu since 2026-10-26) and its armour showcase |
| `Summoner4.glb` | (none) | Summoner, rigged (61 bones), with Tripo's clips: walk, run, three boxing moves, a front kick, a chop, a slash, a spell cast, five hit reactions, a dance | The Summoner of mistward_castle since 2026-10-30 (character `Summoner4`, script `876`: her walk, run and hit reactions; her idle, bolt cast, knife stabs and five summoning casts made for her by `summoner4_clips.py`) |
| `MartialArtist.glb` | (none) | Martial artist, rigged (61 bones), with Tripo's clips: idle, two boxing moves, two front kicks, four hit reactions (body, side, head) | not used yet |
| `Aurorim Low.glb` | (none) | Aurorim, an angel of four wings in white and gold robes with a halo, rigged (65 Mixamo bones, no wing bones), with Tripo's clips: three boxing moves, a front kick, walk, run, five hit reactions | The final boss of mistward_castle's tier 5 since 2026-11-03 (character `Aurorim`, scripts `889` and `blender_numpy/aurorim_build.py`: wing bones added, his idle, flight, lance throw, light-calling cast and death made for him; his punches and flinch his own) |
| `MartialArtist2.glb` | (none) | Martial artist, rigged (61 bones), with Tripo's clips: walk, run, running upstairs, three boxing moves, two front kicks, a dance | The Martial Artist of mistward_castle and martial_arts until 2026-11-10 (character `MartialArtist`, scripts `872` / `873`: her walk, run, boxing and kicks; her idle, knife stabs, roll, dash and ten chi attacks made for her by `martialartist_clips.py`) |
| `MartialArtist3.glb` | (none) | Martial artist, rigged (80 bones: five spine, two neck, twist bones, metacarpals), with MartialArtist2's clips and the clips made for her on it (`blender_numpy/martialartist3_retarget.py`) | The Martial Artist of every map since 2026-11-10 (character `MartialArtist`, script `917`: her asset names kept; her flinch and death retargeted, her grips and blows measured on her own hands and clips) |
| `chicken.glb`, `goat.glb`, `pig.glb`, `rabbit.glb` | (none) | Farm animals, Tripo's own rigs (the pig's 7 bones), no clips | Brokenspire's pens and the wilds' farmsteads since 2026-11-10 (the rabbit also the wilds' hare): their meshes and textures on `farm_animals.py`'s skeletons and clips by `blender_numpy/tripo_animals.py`, script `915` |
| `ridinghorse.glb` | (none) | A saddled paint horse, Tripo's rig, no clips | The stable's horse since 2026-11-10 (the same way; its Walk and Run, the `saddle` bone on its saddle's top) |

## Renamed models

The models were renamed: jrpg-fem5-tripo is now **Warrior**, girl-caster-tripo is now **Mage** and
girl-darkcaster-tripo is now **Warlock**. Only the files were renamed. The project's scripts, docs and
Unreal assets still use the old names (and the characters' tags `Fem5`, `Caster` and `DarkCaster`), so
the levels built from them keep working. The former names in the table above are those names.

## License

These models are free to use, by anyone and for any purpose, commercial included. You may copy,
share, modify and build on them, as long as you give credit.

They are licensed under the [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/) (CC BY 4.0);
the full legal text is in [LICENSE](LICENSE).

Copyright (c) 2026 beknar

All of the models in this directory were generated on a paid Tripo plan, under which the generated
models belong to the user who made them, with full rights to use, modify, distribute and license them
(commercial use included). That is what allows them to be published here under CC BY 4.0.

Suggested credit:

> "Mage" by beknar (https://github.com/beknar/claude-ue5), licensed under CC BY 4.0.

The license covers only the model files in this directory. The project's Unreal content (the Fab, Epic and
other third-party packs, the weapons, the animations' source packs, the sounds and the music) is not part of it
and is not in this repository.
