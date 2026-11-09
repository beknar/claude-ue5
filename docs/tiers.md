# The tiers from Brokenspire to Heaven

[README](../README.md) · [Mistward Castle](levels/mistward_castle.md) · [The wilderness](levels/wilderness.md) · [Vel Morrath](levels/vel_morrath.md) · [Ashenreach](levels/ashenreach.md) · [Graymourne](levels/graymourne.md) · [Kethrys Spire](levels/kethrys_spire.md) · [Heaven](levels/heaven.md) · [TODO](../TODO.md)

The rebalance to tier 25: the fifth phase of the user's list of 2026-11-08b ([docs/improvements9.txt](improvements9.txt)). It covers four things:
- The Mage gains one spell a tier, and two new spells fill the last places.
- The Summoner, the Rogue and the Martial Artist earn new abilities in the dungeons after Mistward.
- The gear is spread over the other five dungeons, in quality copies.
- The monsters are spread from Brokenspire to Heaven.

The dungeons' own bosses come later (the user's words: "the dungeon bosses will be created later").

The data is `claude_ue5/SourceArt/balance/tier25.json`. Stage `910` writes it onto every map of the game, and `905` writes each dungeon's base and cap into the chain. The game's side is `RD/RDTier25.cpp`, and every tier read in the game goes through `GlobalTier`.

## The game's tiers

Each dungeon keeps its own five tiers of sets of rooms. A level's base (`DungeonTierBase`) and cap (`DungeonTierCap`) map them into the game's 25:

| Dungeon | Town | Its tiers in the game's | Base | Cap |
|---|---|---|---|---|
| Mistward Castle | Brokenspire | 1-5 | 0 | |
| the Catacombs of Vel Morrath | Vel Morrath | 6-10 | 5 | |
| the War Engine | Ashenreach | 11-15 | 10 | |
| the Sewers of Graymourne | Graymourne | 16-20 | 15 | |
| the Black Tower of Kethrys Spire | Kethrys Spire | 21-25 | 20 | |
| Kratos Aurorim Research | Heaven | 25 (its first tier 24 + 1, the rest held at 25) | 24 | 25 |

The game's tier (`GameGlobalTier`) is the deepest one opened in any dungeon of the chain. It sets the town's prices: 1 to 8 over the first five tiers as before, then about 17 % a tier, so 17.5 at tier 10 and 185 at tier 25.
- **Gold:** a kill and a container pay by the game's tier of where she earned them: x the tier over the first five, then growing as the prices do (5 x the price factor over 8: about 11 at tier 10, 115 at tier 25).
- **Healer:** prices a point of her hit points and mana down by her growth past tier 5, so a whole heal costs as many kills as before. It also sets the tier she grows by (`GrowthTier`): at least the deepest she has opened anywhere, so a new dungeon never sets her back to tier 1.

## Strength by tier

Past tier 5 the monsters' hit points grow by 1.12 a tier and their blows by 1.09. Their speed, pace and ability stay at tier 5's. The hero grows the same way: her power (blows, spells, chi) by 1.12 a tier and her hit points and mana by 1.09 (`tier25.json`'s `power_growth` and `health_growth`, which `910` writes as `TierGrowthPower` and `TierGrowthHealth`). From tier 5 on, a fight takes as many blows each way as at tier 5. What she finds of the higher tiers is her edge.

| Game tier | Monsters' hit points (x the reference) | Monsters' blows | Her power (x tier 5's) | Her hit points (x tier 5's) | Prices (x tier 1's) |
|---|---|---|---|---|---|
| 1 | 0.5 | 0.45 | | | 1 |
| 5 | 3.4 | 2.2 | 1 | 1 | 8 |
| 6 | 3.81 | 2.40 | 1.12 | 1.09 | 9.4 |
| 10 | 5.99 | 3.38 | 1.76 | 1.54 | 17.5 |
| 15 | 10.56 | 5.21 | 3.11 | 2.37 | 38.5 |
| 20 | 18.61 | 8.01 | 5.47 | 3.64 | 84.3 |
| 25 | 32.80 | 12.33 | 9.65 | 5.60 | 185 |

The Summoner's summons grow to tier 10 of her summonings (`SummonTierStrength`: 0.8 to 1.0 over the first five, then up to 1.2).

## The Mage's spells: one a tier

Each tome spell has one place among the dungeons' 30 tiers (`FRDSpellDef::Slot`). A tome found in a tier of a dungeon is the spell of that tier's place. The places are the chain's index times 5 plus the tier.
- **Order:** the 28 spells found before keep their old order (by tier, then by mana).
- **Starting spells:** Fire Bolt and Dark Fire are no tome's.
- **Made up:** two spells fill the last two places.
  - Starfall: Meteor Storm's, at 1.2 times its mana and 1.5 times its damage.
  - Singularity: Void Rift's, at 1.2 times its mana and 1.6 times its damage.

The tome items carry their place's game tier.

| Dungeon | Tier 1 | Tier 2 | Tier 3 | Tier 4 | Tier 5 |
|---|---|---|---|---|---|
| Mistward Castle | Frost Shard | Ash Ward | Shadow Lash | Bone Spear | Iron Skin |
| Vel Morrath | Life Drain | Dispel Hex | Blood Nova | Chain Lightning | Bone Armor |
| the War Engine | Plague Cloud | Shadow Veil | Curse of Frailty | Fireball | Raise Dead |
| the Sewers | Rune of Warding | Soul Rend | Mirror of Retribution | Corpse Explosion | Blizzard |
| Kethrys Spire | Spectral Bulwark | Hellfire Pillar | Void Rift | Undying Pact | Summon Abyssal Knight |
| Heaven | Meteor Storm | Null Sanctum | Apocalypse | Starfall | Singularity |

## The abilities earned after Mistward

Each later dungeon's last tier's boss gives the Summoner, the Rogue and the Martial Artist one ability (`FRDHeroDef::LaterWeapons`). The game keeps it through the counter `<dungeon>:bossdone:5`, so it is hers from then on, also through a death and in the town.

Each ability is a copy of one of her own, made stronger:

| Earned in | Summoner | Rogue | Martial Artist |
|---|---|---|---|
| Vel Morrath | Summon Tier 6: an Iron Golem (3 at most) | Barbed Bolt (the crossbow x 1.45) | Crashing Wave (Chain Punch x 2.0) |
| the War Engine | Summon Tier 7: a Cyber Soldier (4) | Incendiary Bolt (x 1.7, a 2.2 m blast) | Thunder Step (Axe Kick x 2.2) |
| the Sewers | Summon Tier 8: the Captain of the Tide (3) | Shadow Fangs (the daggers x 2.0, 1.7 m reach) | Dragon Palm (Piercing Palm x 2.5) |
| Kethrys Spire | Summon Tier 9: a Lich of the Black Tower (3) | Storm Bolt (x 2.3, lightning, a 3.2 m blast) | Comet Fist (Meteor Fist x 2.6) |
| Heaven | Summon Tier 10: a Kratos Field Commander (3) | Death's Kiss (the daggers x 2.8, 1.8 m reach) | Heaven's Gale (Spinning Kick x 2.9) |

## The gear in every dungeon

The castle's tiered weapons, armour, shields and rings come again in each later dungeon at their tier there, each in a quality:

| Quality | Dungeon | Damage | Armour, block | A ring's bonus | Durability |
|---|---|---|---|---|---|
| Fine | Vel Morrath | by the tiers' power | +0.04 | x 1.3 | x 1.25 |
| Masterwork | the War Engine | (a found weapon of tier t: tier 5's x 1.12 per tier past 5) | +0.08 | x 1.6 | x 1.5 |
| Exalted | the Sewers | | +0.12 | x 1.9 | x 1.75 |
| Celestial | Kethrys Spire and Heaven | | +0.16 (at most 0.85) | x 2.2 | x 2.0 |

Each quality has 108 copies. A copy's damage follows `880`'s rule for found weapons: 8 + 3 × its damage rating, times the power of its first tier (`balance6.json` for tiers 1 to 5, then × 1.12 a tier). The Viking Shortsword, for example, does 20 at tier 1; its Fine copy does 56 (tier 6), Masterwork 99, Exalted 174 and Celestial 307. The potions, food and scrolls are found in every dungeon at their rank.

Every reader of an item's tiers goes through one rule (`ItemOfTier`: no tiers, or the game's tier of the level's among them). What the rules put in a container stays in the game's tiers too:
- **Guarded ring:** past the castle, the ring of the tier before in the game's tiers, the weaker of its two (`PlaceRingGuard`).
- **Vaults:** the tier above.
- **Gauntlets:** their own tier.
- **Prisoners' gifts and armory tables:** their tier.
- **The final boss's reward:** its tier.

The bosses' slashes and the harvests (essences, parts) stay on each dungeon's own tiers 1 to 5: their tables have five tiers, and the later dungeons give their own tiers' slashes and harvests as Mistward does.

## The monsters from Brokenspire to Heaven

Every map now carries every dungeon's kinds: 88 kinds, weight 0 except on their own map. That lets the Summoner call them anywhere, and the wilds meet them. Each kind has a band of the wilderness's tiers (`WildTierMin`, `WildTierMax`); a lair or spawn point of tier t holds kinds whose band holds t, at tier t's strength.

| Kinds | Wild tiers |
|---|---|
| the castle's tier k (shared with Vel Morrath) | 2k - 1 and 2k (1-10) |
| the War Engine's machines, tier k | 10 + k (11-15) |
| the drowned of the Sewers, tier k | 15 + k (16-20) |
| the casters of the Black Tower, tier k | 20 + k (21-25) |
| Heaven's defenders | 23-25 |
| Aurorim | never |

## The tests

`868 tier25` runs on Vel Morrath (`-lv vel_morrath`, `test_t25e.json`).
- **Tiers:** the level's tiers are the game's 6-10.
- **Monster strength:** the start set's 19 monsters were spawned on the same seed without the level's base and with it. Every one came out 7.62 times the hit points and 5.33 times the blows (whole points, each end within half a point), as the tables say.
- **Hero strength:** her hit points went from 140 to 262 (tier 6's growth).
- **Loot:** every container's random draw in the start set and a tier-2 set, over 40 session seeds, held only things of the game's tier. That was 25,355 things, 9,217 of them Fine and none of another quality or a plain tiered piece of the castle's.
- **Rules' loot:** what the rules put first held only things of the set's tier or the tier above.
- **Tomes:** each tome was its tier's one spell (Life Drain, Dispel Hex).
- **Later abilities:** the tier-5 boss slain gave the Martial Artist Crashing Wave, the Rogue Barbed Bolt and the Summoner Summon Tier 6, and none of the next dungeon's.
- **Later abilities, saved:** the abilities come from the game instance's saved counter (`<dungeon>:bossdone:5`). The Rogue's and the Summoner's were read after a restart as each hero.
- **Boss gold:** the boss paid 471 gold, at least `BossGold` x the gold factor of game tier 10 (438).
- **Summon Tier 6:** cast, it called an Iron Golem (396 hit points, blows of 62) holding the game's tier she grows by (6).

`888 wild25` runs on Brokenspire (`-Light`, `test_w25b.json`). It visited lairs and spawn points of tiers 2, 6, 11, 16, 22 and 25 along the roads:
- **What was there:** Half Creatures, Costalmeds, Scrap Hounds, Drowned Sailors, Skeleton Witches and Kratos Tanks, each kind of its place's tier and inside its band.
- **Strength:** their hit points rose from 116 to 4830, each kind measured against the mean of the kinds met at its tier.

The castle's own steps the rebalance touches still pass on Mistward Castle (`test_r25c.json` after PR #34's review: `summoner`, `growth`, `allyspace`, `martial`, `tiers`, `rooms`, `pickups`, `cells`; `test_r25b.json`, and `tiers`, `martial`, `summoner`, `recipes`, `rooms`, `pickups`, `scrolls` in the batch before it): `growth` and `tomemana` now take the castle's own tiers' gear, not the quality copies. `884 keys9` passes on Brokenspire (`test_k25a.json`).

## Rebuild

1. Build the C++ (`pipeline\build_cpp.ps1`).
2. Run `910_tier25.py` (all seven maps; or name some). Run it after anything that writes the levels' heroes, spells, items or monsters anew (`855`, `857`, `858`, `859`, `871`, `872`, `876`, `880`, `895`, `897`, `907`, `909`): those stages write the castle's tables, and `910` builds the rest from them.
3. Run `905_dungeon_keys.py`, which writes the chain's tier bases from `tier25.json`.
