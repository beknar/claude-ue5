# Hero balance

[README](../README.md) · [Mistward Castle](levels/mistward_castle.md) · [The wilderness](levels/wilderness.md) · [TODO](../TODO.md)

How the six heroes are balanced against each other and against what they fight. The first attempt covers the five tiers of the Mistward Castle dungeon only. The continent round Brokenspire will need balancing attempts of its own later: see [Continent-wide balancing considerations](#continent-wide-balancing-considerations).

## Preliminary balancing attempt

The user's list of 2026-11-01 (`docs/improvements6.txt`) asked for the six heroes to be balanced against each other tier by tier, each playing differently (not the same hero six times). It was built by `880_mistward6.py` (C++ `RD/RDMistward6.cpp`, the generator's `bTierGrowth`; the numbers in `SourceArt/mistward/balance6.json`) and measured by `868_mistward_test.ps1 balance` (the trials) and `868 growth` (each hero's numbers with tiers 2 to 5 open).

The tables below are a snapshot of 2026-11-01 (the record `SourceArt/mistward/test_b.json`). The castle's document keeps the live tables, written from the game's data by `pipeline/blender_numpy/mw_balance.py`: [mistward_castle: the list of 2026-11-01](levels/mistward_castle.md#mistward_castle-the-castle).

### What it fixed

Before it:

- A weapon did the same at tier 5 as at tier 1. The best found weapon did 38 a blow against monsters with 6.8 times tier 1's hit points.
- The Mage's mana came back at 2 a second, whatever her pool.
- The dearer chi attacks did less for their mana than the cheapest: the Spinning Kick did 32 for 88 mana, the Straight Punch 23 for 7.

Now each tier opened past the first makes her stronger her own way ("Tier 3 opens: you grow stronger (…)").

### The content: monsters by tier

Each tier's rooms hold the monster gallery's monsters of that tier ([docs/monsters.md](monsters.md)). Their numbers are set against a reference hero of 100 hit points and a 25-damage blow, whichever hero is played (`MonsterReferenceHealth` / `MonsterReferenceBlow`). Each kind is 0.8 to 1.2 times its tier's numbers by its rank in the gallery.

| Tier | Hit points / damage | Speed | Time between blows | Abilities (weaken, poison or slow) |
|---|---|---|---|---|
| 1 | 50 / 11.2 | x 1 | x 1.15 | none |
| 2 | 100 / 25 | x 1.05 | x 1 | none |
| 3 | 160 / 33.8 | x 1.1 | x 0.92 | x 1 |
| 4 | 240 / 43.8 | x 1.15 | x 0.85 | x 1.4 |
| 5 | 340 / 55 | x 1.2 | x 0.78 | x 1.8 |

From tier 1 to tier 5 a monster's hit points grow 6.8 times and its damage 4.9 times.

- **Opening a tier:** a tier opens when the tier before has half of its rooms explored, half of its monsters killed and half of its chests and trunks looted.
- **The boss:** each opening puts the new tier's strongest kind in a room of the tier before that she has explored. It is 1.35 times bigger, has 3 times the hit points, hits 1.6 times as hard and has 3 to 6 monsters of the new tier round it.
- **The final boss:** once tier 5 itself reaches the share, Aurorim waits in a room of it, scaled above tier 5's boss as the dungeon's boss (its strongest kind's factors, then 1.5 times a tier boss's hit points and 1.25 times its blows: 4.5 times the hit points and 2 times the blows) with 6 to 10 escorts; his lance (9 to 32 m, 0.75 of a blow), his light from above (3.5 to 13 m, a full blow, 230 cm round), both recharging a quarter faster, and his punches; he flinches at most once every 3 s. Not yet in the trials: he is not among the bosses each hero fought there.
- **The guarded ring:** if she has found neither magic potency ring of the tier before, one is put in a container there, guarded by 4 monsters of the new tier.

### The heroes: how each grows

| Hero | Hit points with tiers 1 / 2 / 3 / 4 / 5 open | Mana (back a second) | Each tier opened past the first | Her way |
|---|---|---|---|---|
| Warrior | 140 / 165 / 190 / 216 / 241 | none | +18 % hit points | By what she finds: found weapons carry their tier's power (x 1, 1.3, 1.65, 2.05, 2.5), with heavy armour, shields, HP rings and slashes. Her own dagger stays the worst weapon on purpose. +30 % melee. |
| Mage | 70 / 81 / 91 / 102 / 112 | 100 (2.5: 2.5 % of her pool) | +15 % hit points, +12 % spell damage | By her spells: the tomes she reads, magic rings. She fights from afar and steps back from what comes close. |
| Warlock | 100 / 125 / 150 / 175 / 200 | 60 (1.5: 2.5 % of her pool) | +25 % hit points, +20 % spell damage, +30 % to her own weapons | By her pact blade and fire; found medium armour, rings of both kinds. |
| Rogue | 100 / 120 / 140 / 160 / 180 | none | +20 % hit points, +8 % to her own weapons | By stealth, rings and crossbows: 8 s unseen by monsters and traps for 40 of 100 dexterity energy, her first blow out of it +75 %; Dexterity rings on her bolts; found crossbows' tiers. +30 % ranged. |
| Martial Artist | 140 / 168 / 196 / 224 / 252 | 100 (2: 2 % of her pool) | +20 % hit points, +12 % chi, +12 % to her fists | By her body: chi attacks' damage follows their mana (23 x (mana / 7) ^ 0.75); HP and Dexterity rings worn together. +30 % short blades. |
| Summoner | 85 / 106 / 128 / 149 / 170 | 50 (2: 4 % of her pool) | +25 % hit points, +15 % spell damage | By her summons: each tier's boss gives the next, stronger kind; they stay with her until they fall. A summon takes half her pool. |

### Her own weapons and spells

Damage with her melee, ranged and type bonuses, no ring.

| Hero | Weapon or spell (mana) | Damage a hit, tiers 1 / 3 / 5 | A second, tier 1 / tier 5 |
|---|---|---|---|
| Warrior | Dagger | 14.3 / 14.3 / 14.3 | 26 / 26 |
| Mage | Fire (8) | 25 / 31 / 37 | 33 / 49 |
| Mage | Dark Fire (14) | 38 / 47 / 56 | 50 / 75 |
| Warlock | Sword | 22 / 35 / 48 | 34 / 74 |
| Warlock | Fire (10) | 25 / 35 / 45 | 33 / 60 |
| Rogue | Daggers | 13 / 15.1 / 17.2 | 27 / 36 |
| Rogue | Crossbow | 34 / 39 / 45 | 36 / 47 |
| Martial Artist | Fists | 44 / 55 / 65 | 28 / 42 |
| Martial Artist | Straight Punch (7) | 23 / 29 / 34 | 37 / 55 |
| Martial Artist | Side Kick (17) | 45 / 56 / 67 | 56 / 83 |
| Martial Artist | Roundhouse Kick (37, unlocked by a boss) | 80 / 99 / 118 | 100 / 148 |
| Martial Artist | Spinning Kick (88, unlocked by a boss) | 154 / 191 / 228 | 134 / 198 |
| Summoner | Fire (8) | 25 / 33 / 40 | 26 / 42 |
| Summoner | Dark Fire (14) | 38 / 49 / 61 | 40 / 64 |

The found weapons: a weapon's damage is 8 + 3 x its rating, times its tier's power. Examples: the Arming Sword (tier 1) 26; the Templar Sword (tier 2) 42, from 32; the Dark Knight's Sword (tier 3) 63, from 38; the Dwarf Crossbow (tiers 4 and 5) 53, from 26; Ursag's Horn Blade (tiers 4 and 5) 78, from 38. The whole list is in [the castle's document](levels/mistward_castle.md#mistward_castle-the-castle).

### The trials

Each hero at each tier is played by autoplay:

- **Her kit:** what she typically carries arriving at that tier, with two of each potion of the tier. The kits are `balance6.json`'s `kits`: for example the Warrior at tier 5 has Ursag's Horn Blade, the Dark Knight's Armour, HP Potency Ring 8 and the Crystal Slash; the Summoner has Magic Potency Ring 8 and two of her best summons called.
- **The fights:** three monsters of the tier coming at her from 9 m, then the tier's strongest kind as a boss (3 times its hit points, 1.6 times its blows), fought twice.
- **How autoplay plays her:**
  - the Rogue hides to strike first, or to get away when hurt;
  - the Mage, the Summoner and the Rogue with her crossbow step back from what comes close;
  - the Summoner calls her summons first;
  - every hero uses only her best near and best far weapon.

| Hero | Fight | Tier 1 | Tier 2 | Tier 3 | Tier 4 | Tier 5 |
|---|---|---|---|---|---|---|
| Warrior | three of the tier | won, 11.6 s, 89 % left | won, 14.1 s, 60 % left | won, 8.6 s, 74 % left | won, 17.6 s, 100 % left | won, 24 s, 72 % left |
|  | its boss | won 2 of 2 (9.1 / 9.2 s, 94 / 94 % left) | won 2 of 2 (14.6 / 14.6 s, 55 / 55 % left) | won 2 of 2 (11 / 11 s, 49 / 49 % left) | won 2 of 2 (22 / 21 s, 61 / 93 % left) | won 2 of 2 (25 / 25 s, 46 / 46 % left) |
| Mage | three of the tier | won, 4.5 s, 100 % left | won, 8.1 s, 94 % left | won, 11.8 s, 100 % left | won, 8.7 s, 100 % left | won, 18.6 s, 70 % left |
|  | its boss | won 2 of 2 (4.7 / 4.7 s, 100 / 100 % left) | won 2 of 2 (7.6 / 7.6 s, 100 / 100 % left) | won 2 of 2 (10.2 / 10.2 s, 100 / 100 % left) | won 2 of 2 (11.1 / 11.2 s, 100 / 100 % left) | won 2 of 2 (13.4 / 13.5 s, 100 / 100 % left) |
| Warlock | three of the tier | won, 6.8 s, 100 % left | won, 16.6 s, 64 % left | won, 9.1 s, 100 % left | won, 14.2 s, 93 % left | won, 17.6 s, 58 % left |
|  | its boss | won 2 of 2 (6.4 / 6.5 s, 100 / 100 % left) | won 2 of 2 (11.5 / 11.5 s, 86 / 86 % left) | won 2 of 2 (11.4 / 11.4 s, 65 / 65 % left) | won 2 of 2 (17.5 / 21 s, 88 / 77 % left) | won 2 of 2 (24 / 24 s, 77 / 77 % left) |
| Rogue | three of the tier | won, 6.1 s, 100 % left | won, 7.3 s, 60 % left | won, 10.4 s, 77 % left | won, 12.2 s, 70 % left | won, 11.7 s, 63 % left |
|  | its boss | won 2 of 2 (4.5 / 4.5 s, 100 / 100 % left) | won 2 of 2 (7.4 / 7.4 s, 100 / 100 % left) | won 2 of 2 (8.2 / 8.2 s, 100 / 100 % left) | won 2 of 2 (10 / 9.9 s, 100 / 100 % left) | won 2 of 2 (9.8 / 9.9 s, 100 / 100 % left) |
| Martial Artist | three of the tier | won, 6.5 s, 96 % left | won, 9.2 s, 88 % left | won, 9.9 s, 89 % left | won, 15.9 s, 62 % left | won, 26 s, 56 % left |
|  | its boss | won 2 of 2 (4.8 / 5.4 s, 94 / 94 % left) | won 2 of 2 (7.1 / 7.1 s, 90 / 90 % left) | won 2 of 2 (11.6 / 11.6 s, 58 / 58 % left) | won 2 of 2 (13.2 / 12.7 s, 100 / 100 % left) | won 2 of 2 (24 / 41 s, 81 / 44 % left) |
| Summoner | three of the tier | won, 5.4 s, 100 % left | won, 10.3 s, 77 % left | won, 14 s, 77 % left | won, 14.1 s, 98 % left | won, 23 s, 100 % left |
|  | its boss | won 2 of 2 (4.6 / 4.7 s, 100 / 100 % left) | won 2 of 2 (10.3 / 10.3 s, 100 / 100 % left) | won 2 of 2 (11.4 / 13.9 s, 100 / 100 % left) | won 2 of 2 (14.4 / 13.9 s, 100 / 100 % left) | won 2 of 2 (21 / 17.9 s, 100 / 100 % left) |

### What the trials say

- **Every hero wins** every pack and both fights with every tier's boss. At each tier the slowest pack win is within 2.6 times the quickest.
- **Each wins her own way:**
  - the Warrior and the Martial Artist stand in the blows (they lose the most hit points, and have the most);
  - the Mage and the Summoner are hardly hit (she keeps her distance; the summons take the blows), but have the fewest hit points when something reaches them;
  - the Rogue kills quickest (10 s for tier 5's boss against the Warrior's 25) but wears light armour only;
  - the Warlock sits between.
- **The hardest fight** is tier 3's boss, the Zombie Tank (a cannon and a slowing blow): it once left the Warlock with less than 1 %.
- **Monsters outgrow the heroes' hit points:** a monster's damage grows about 5 times from tier 1 to tier 5, the heroes' hit points 1.6 to 2 times. A tier-5 blow (55) is half the Mage's hit points before armour. Keeping her distance, armour and the summons carry the difference.

### How it got here

This was the third run. The first run's numbers were these:

- the Mage's spells +20 % a tier;
- less hit point growth for the heroes in light armour;
- an ambush +150 %;
- the Summoner with no summons called;
- the autoplay pilot not yet keeping after a monster that had lost the Rogue.

In that run four of the six heroes fell to tier 3's boss, the Summoner fell to tier 5's pack and the Rogue to tier 5's boss, while the Mage lost under 10 % anywhere. The second run made the Rogue the strongest by far: a tier-5 boss in 7.6 s with nothing lost.

### Its limits

- **Assumed kits:** the kits are what she typically carries, not what a game hands her. A real game's loot varies by seed.
- **Few fights:** each pack was fought once and each boss twice, by autoplay, not by a player.
- **No full game measured:** nobody has played a game from tier 1 to tier 5 on found loot only.
- **Fixed monsters:** the monsters' numbers follow the reference hero, not the one played. The heroes with few hit points depend on their way of playing to keep up.

## Continent-wide balancing considerations

The first attempt balanced the castle's five tiers only. The wilderness round Brokenspire ([the wilderness](levels/wilderness.md)) and five more cities with dungeons of their own need balancing attempts of their own. This section is a plan (2026-11-03), not a measurement. The proposed numbers are extended from the measured ones above and are to be checked by trials before anything is built on them.

### Where it starts

- **The monsters:** 55 usable kinds of the monster gallery's 107 ([docs/monsters.md](monsters.md)): 8 in tier 1, 8 in tier 2, 14 in tier 3, 19 in tier 4 and only 6 in tier 5. All are dungeon creatures (orcs, zombies, aliens, insects): there is almost no wildlife. The other 52 lack clips that walk, attack, flinch and die.
- **The wilderness's tiers go by distance from Brokenspire:** tier 1 within 25 km, one more tier every 25 km, tier 5 from 100 km on (`FRDWildWorld::TierAt`). Ashenreach (70 km) stands in tier 3; Vel Morrath (115 km) and Graymourne (197 km) in tier 5.
- **The land in each band**, estimated from a simplified shape of the continent (a rounded square, not the world model's own coast):

  | Tier | Share of the land |
  |---|---|
  | 1 | about 3 % |
  | 2 | about 10 % |
  | 3 | about 14 % |
  | 4 | about 16 % |
  | 5 | about 56 % |

  More than half the continent is tier 5, the tier with the fewest kinds.
- **Her growth comes from the castle's tiers she has opened** (`GetOpenTier`). A hero who walks far from Brokenspire before opening them meets tier-5 monsters at tier-1 strength.
- **The heroes already fall behind the monsters:** in the trials, kill times about doubled from tier 1 to tier 5 (the Warrior's pack 11.6 s to 24 s, the Mage's 4.5 s to 18.6 s). That is about 19 % longer fights per tier. Over 15 more tiers fights would last about 13 times longer.
  - **The cause:** the heroes' hit points grow by a fixed share of their start per tier (the Warrior's +18 %), while the monsters' numbers multiply.
- **Out there she has fought only in tests:** the lairs' and spawn points' monsters, and fast travel's refusal in a fight. There are no trials yet, no loot tables or kits for the wilds, and nothing for the small towns' services and prices.

### Tiers for five more cities with dungeons

**Proposed: 20 tiers in all, 15 more than today.** Each city's dungeon is a whole climb of 5 tiers and overlaps the dungeon before it by 2 tiers, so a new city is a step up, not a cliff:

| Dungeon | Tiers | The land round its city |
|---|---|---|
| Mistward Castle (Brokenspire) | 1-5 | tier 1 |
| City 2 | 4-8 | tier 4 |
| City 3 | 7-11 | tier 7 |
| City 4 | 10-14 | tier 10 |
| City 5 | 13-17 | tier 13 |
| City 6 | 16-20 | tier 16 |

The alternatives:

- **No overlap (30 tiers):** a harder jump at each city, and more content to fill.
- **Every dungeon at tiers 1 to 5:** no new tiers, but the cities become side trips rather than progress.

**The wilderness tiered by zone, not by distance:** the land round each city at its dungeon's first tier, the roads between cities climbing from one to the next. The extreme regions (arctic, peaks, volcanoes) can stand 2 tiers above their zone as optional dangerous country. This also ends "most of the continent is tier 5".

### Monster kinds and their distribution

**The dungeons:**

- **Slots:** at least 8 kinds per tier, 160 slots over 20 tiers.
- **Each kind spans 3 tiers:** a weaker pack monster below its own tier, a regular at it, an elite above it. Their numbers already come from the tier, so only the art must look right at each.
- **About 55 kinds would be in use at any time,** but the top tiers need the toughest-looking models: ranked by looks across 20 tiers, that is 5 or 6 distinct models per tier.
- **So about 50 more models (a roster of about 110),** most of them at the top. The gallery's 52 unusable models are the first source: their clips made in Blender, as the heroes' were.

**The wilderness:**

- **The 28 templates grouped into about 8 families:**
  - open land (grasslands, meadows, farms, plains, hills);
  - forest;
  - wetland;
  - cold;
  - arid (savannahs, canyons, mesas);
  - volcanic;
  - coast;
  - mountain.
- **About 6 kinds per family, 48 roles in all:**
  - 3 common kinds that come in packs;
  - 1 tough kind;
  - 1 lair beast;
  - 1 rare wanderer.
- **About half of them can be dungeon kinds recoloured:** the gallery's variant material already makes three looks: *infernal* for volcanic country, *venom* for the marshes, *frost* for the cold lands.
- **That leaves about 25 new beasts and animals** (wolves, bears, scorpions, ice trolls and the like), which the library mostly lacks.

**Within a tier:**

- **In a dungeon:** about 5 common kinds that come in packs, 2 tough ones that come in pairs, and 1 strong enough to be the boss.
- **In the wilds:** spawn points hold packs of the common kinds; lairs hold one lair beast and its young. The open land between places needs wanderers too; today it has none.

**In all: about 75 new kinds** (about 50 for the dungeons, about 25 for the wilderness).

### What each hero needs to keep up

**The rule:** keep a fight's length steady from tier to tier.

- Her damage must grow as fast as the monsters' hit points.
- Her survival (hit points, armour, healing together) must grow as fast as the monsters' damage.
- Both must **multiply** per tier, not add a fixed share.

**A proposed monster curve for tiers 6 to 20:**

- **Hit points and damage:** +25 % hit points and +18 % damage a tier. At tier 20 a monster has about 9,600 hit points and hits for about 850.
- **Caps:**
  - monster speed stays below her run, or the Mage, the Summoner and the Rogue can no longer keep their distance;
  - slow and weaken stay capped (for example slow at most 40 %, weaken at most 30 %).

**Each hero then needs about x 1.25 damage and x 1.18 survival a tier, from her own sources:**

| Hero | Her damage from | Her survival from | To add |
|---|---|---|---|
| Warrior | found weapons' tier power (on past x 2.5), slashes | hit points, heavy armour, shields | armour that takes a fixed amount off a blow per tier (a share cannot grow: hers stops at 50 %) |
| Mage | spell ranks from higher tiers' tomes, magic rings | her distance, wards | new tomes every 2 or 3 tiers; mana and spell costs growing together; crowd control that keeps up with faster monsters |
| Warlock | her pact blade's growth, fire | hit points, medium armour | life drain for sustain; curses that weaken by a share |
| Rogue | crossbow tiers, Dexterity rings, the +75 % ambush | stealth, dodging | stealth energy and length growing per tier; a dodge chance in armour's place |
| Martial Artist | fists and chi growth, chi attacks unlocked by bosses | hit points, dodging | her 8 locked chi attacks spread over the 20 tiers, not 5; her chi pool growing |
| Summoner | her summons | her summons take the blows | summons that take the open tier's monster numbers times a factor, so they keep up by themselves; a new summon kind every 3 or 4 tiers (5 kinds today) |

**Her growth:** still by the tiers opened, counting the highest tier she has opened in any dungeon, so a tier opened in one city counts everywhere.

### What a continent-wide attempt needs

- **Trials at each zone:** the castle's trials repeated with the tiers and kits she would have by then, for all six heroes.
- **The wilderness's loot:** measured against the castle's.
- **Travel times:** set against her growth.
- **The proposed curves checked:** the monsters' growth and caps, and each hero's growth, measured in trials before the new tiers are built.
