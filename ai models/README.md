# AI models

The characters this project uses in its current and future scenes, made with [Tripo](https://www.tripo3d.ai/).

| Model | Former name | What it is | Used in |
|---|---|---|---|
| `Warrior.glb` | `jrpg-fem5-tripo.glb` | JRPG heroine (sword, shield, spear, axe) | random_level, random_dungeon_level, random_isometric_village_level, random_dungeoncombat_level, the Tripo trio and quartet showcases |
| `Warrior2.glb` | (none) | The Warrior's mesh, weights and texture with Tripo's clips: `chop`, `slash` (the same motion) and a horizontal two-handed sweep | random_dungeonmagic_level5's chop test only (character `Warrior2`, script `861`); the heroes do not use it |
| `Warrior3.glb` | (none) | The Warrior of random_dungeonmagic_level5 since 2026-10-26: a new Tripo model (her own proportions) with Tripo's clips: idle, walk, run, slash, five hit reactions, two boxing moves, a kick, a clap, a dance, a wave | random_dungeonmagic_level5 (character `Warrior3`, script `862`: the hero "Warrior"; her slash for two-handed swords) and its reels |
| `Mage.glb` | `girl-caster-tripo.glb` | Fire caster | random_dungeonmagic_level, the Tripo trio and quartet showcases |
| `Warlock.glb` | `girl-darkcaster-tripo.glb` | Dark caster (spell in the left hand, sword in the right) | random_dungeonmagic_level2, the Tripo trio and quartet showcases |
| `Rogue.glb` | (none) | Hooded rogue (two daggers, a crossbow) | random_dungeonmagic_level3 (tag `Rogue`), the Tripo quartet showcase |
| `Summoner.glb` | (none) | Twin-tailed summoner (the Mage's spells; a face that shows expressions) | the first random_dungeonmagic_level5 (character `Summoner`, scripts `832`-`841`) and its face reels |
| `Summoner2.glb` | (none) | Realistic summoner (made from two AI-generated pictures), fitted with a whole MetaHuman | the Summoner2 version of random_dungeonmagic_level5 (scripts `842`-`848`; set aside) |
| `Summoner3.glb` | (none) | Summoner (the Mage's spells; wears the armour she finds) | random_dungeonmagic_level5 (character `Summoner3`, the fifth hero; off the hero menu since 2026-10-26) and its armour showcase |

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
