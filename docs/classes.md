# The classes and their abilities

[README](../README.md) · [The secondary abilities](secondary.md) · [The tiers](tiers.md) · [Hero balance](hero-balance.md) · [Mistward Castle](levels/mistward_castle.md) · [The hero gallery](heroes.md)

The six heroes of the game (Warrior, Mage, Warlock, Rogue, Martial Artist, Summoner), every ability each one has, how each grows, what it does, and which clips and effects it shares with other abilities.

**Where the numbers come from.** Everything here was read on 2026-11-10 from the data the game plays (`mistward_castle`'s generator: its `Heroes`, `Spells`, `Secondaries`, `Slashes`, `Items` and block settings) and from the C++ that uses it (`RDCombat.cpp`, `RDSpells.cpp`, `RDSecondary.cpp`, `RDMistward6.cpp`, `RDDungeonGenerator.cpp`). Stages `910` and `911` write the same tables onto every map of the game, so the castle's data stands for all of them. The clip and effect names are the assets the data points at. This page was not checked in play: whether an effect is clearly seen, or how a clip looks, was not looked at for it.

**The numbers are base numbers**, before her growth, her rings, a shrine's blessing or a monster's weakening, unless a column says otherwise. Damage is hit points taken off a monster.

## How abilities grow

There are two kinds of growth:
- **Primary abilities have no ranks.** They grow with the tiers she has opened (below), and new ones are unlocked: by tomes, by bosses, or by finding weapons.
- **Secondary abilities have six ranks.** Each rank costs one Angel Token (three Seraph Feathers and a Hallowed Stone, made at an anvil); the first rank learns the ability. See [secondary.md](secondary.md) for the tokens.

| What | How it grows | Ranks |
|---|---|---|
| Her own weapons and spells (the ones she starts with), chi attacks, scrolls, tome spells | By her growth tier: each tier opened past the first adds her hero's share (table below), up to tier 5. Past tier 5 it is x 1.12 a tier, compounding. The growth tier is the deepest tier she has opened in any dungeon (`GrowthAt`, `TierSpellMul`, `TierOwnWeaponMul`). | none |
| Found weapons | By the tier and quality of the weapon itself: 8 + 3 x its damage rating, x its tier's power (x 1, 1.3, 1.65, 2.05, 2.5 for tiers 1 to 5, then x 1.12 a tier). The Fine, Masterwork, Exalted and Celestial copies are found in the later dungeons. Her growth does not apply. | none |
| New chi attacks (Martial Artist) | Two unlocked each time she kills a tier's boss, in a fixed order. | none |
| New summonings (Summoner) | One unlocked each time she kills a tier's boss. | none |
| New spells (Mage, Warlock) | One tome spell for each of the 30 dungeon tiers (Mistward's 1 to 5, Vel Morrath's 6 to 10 ... Heaven's 26 to 30). A tome teaches it to a hero who learns its type. | none |
| Abilities earned after Mistward (Rogue, Martial Artist, Summoner) | One for each later dungeon, given when its tier-5 boss falls. Each is a stronger copy of one she already has. | none |
| Secondary abilities | Angel Tokens, rank 1 to 6. | 6 |
| Summons | The open tier's monster numbers x a factor for the summoning's tier (0.8, 0.85, 0.9, 0.95, 1.0 for tiers 1 to 5; 1.04 to 1.2 for tiers 6 to 10). Minion Health, Minion Damage and Frenzy multiply on top. | none (the secondaries have 6) |

### Growth by hero

Each tier opened past the first adds these shares (additive up to tier 5). Past tier 5, power is x 1.12 a tier and hit points and mana x 1.09 a tier, for every hero.

| Hero | Hit points a tier | Spell and chi damage a tier | Her own weapons a tier | Mana a tier | Mana back a second |
|---|---|---|---|---|---|
| Warrior | +18 % | - | - (x 1.12 a tier past 5) | - | - |
| Mage | +15 % | +12 % | - | - | 2.5 % of her pool |
| Warlock | +25 % | +20 % | +30 % | - | 2.5 % of her pool |
| Rogue | +20 % | - | +8 % | - | - |
| Martial Artist | +20 % | +12 % | +12 % (her fists) | - | 2 % of her pool |
| Summoner | +25 % | +15 % | - | +10 % | 4 % of her pool |

What that gives at growth tiers 1, 5, 10 and 25:

| Hero | Hit points | Spell and chi multiplier | Own weapon multiplier | Mana pool (before rings) |
|---|---|---|---|---|
| Warrior | 140 / 241 / 371 / 1350 | - | 1 / 1 / 1.76 / 9.65 | none |
| Mage | 70 / 112 / 172 / 628 | 1 / 1.48 / 2.61 / 14.28 | - | 100 / 100 / 154 / 560 |
| Warlock | 100 / 200 / 308 / 1121 | 1 / 1.80 / 3.17 / 17.36 | 1 / 2.20 / 3.88 / 21.22 | 60 / 60 / 92 / 336 |
| Rogue | 100 / 180 / 277 / 1009 | - | 1 / 1.32 / 2.33 / 12.73 | none |
| Martial Artist | 140 / 252 / 388 / 1412 | 1 / 1.48 / 2.61 / 14.28 | 1 / 1.48 / 2.61 / 14.28 | 100 / 100 / 154 / 560 |
| Summoner | 85 / 170 / 262 / 953 | 1 / 1.60 / 2.82 / 15.43 | - | 60 / 84 / 129 / 471 |

The Mage's pool is also raised to at least 220 once she knows Null Sanctum, and 300 once she knows Apocalypse (`TomeMana`).

## The heroes at a glance

| Hero | Hit points (tier 1) | Mana | Armour | Rings | Bonuses | Starts with | Gains new primary abilities by | Secondary abilities |
|---|---|---|---|---|---|---|---|---|
| Warrior | 140 | none | light, medium, heavy | Health | +30 % melee | a dagger (never breaks or drops), no shield | found weapons and shields; slashes from bosses | 6 |
| Mage | 70 | 100 | none | Magic | - | Fire, Dark Fire | tomes (all four spell types); scrolls | 6 |
| Warlock | 100 | 60 | light, medium | Magic, Health | - | an arming sword, Fire | found weapons; tomes (offense and curse); scrolls | 6 |
| Rogue | 100 | none (100 dexterity energy) | light | Dexterity | +30 % ranged | two daggers, a crossbow | found daggers, bows and crossbows; later dungeons' bosses | none |
| Martial Artist | 140 | 100 | light | Health, Dexterity | +30 % with knives and daggers | fists and feet, two chi attacks | tier bosses (chi attacks); later dungeons' bosses; found knives | 5 |
| Summoner | 85 | 60 | none | Magic | - | Fire, Dark Fire, Summon Tier 1 | tier bosses (summonings); later dungeons' bosses; found daggers; scrolls | 5 |

A Dexterity ring adds to a ranged weapon's bolts; on the Martial Artist it also adds to her fists and knives, never to her chi attacks. A Health ring adds hit points, a Magic ring mana.

---

## Warrior

She fights with what she finds. Her own dagger stays the weakest weapon on purpose.

### Primary abilities

| Ability | Use | What it does | Base numbers | Grows by | Clips | Effects |
|---|---|---|---|---|---|---|
| Dagger | attack | melee blow, three swings in turn | 11 (14.3 with her +30 %), reach 1.5 m | her own weapon growth (none to tier 5, then x 1.12 a tier): 14.3 / 14.3 / 25.2 / 138 at tiers 1 / 5 / 10 / 25 | `Anim_Weapon_Shield_Attack_01`, `_03`, `_08` (`_Warrior3`) | none |
| Found one-handed weapons (daggers, short swords, one-handed, curved and eastern swords) | attack | melee blows | the weapon's own, +30 % | the weapon's tier and quality | the same three as her dagger | none (a slash adds its own) |
| Found two-handed swords | attack | melee blows | the weapon's own, +30 % | the weapon's tier and quality | `AS_Warrior3_Slash` | none |
| Found bows | attack | a bolt that flies straight at the monster she faces | the weapon's own (the +30 % is melee only) | the weapon's tier and quality | `AS_Warrior3_W5_Bow` | `P_RDM3_BoltTrail`, `P_Impact` |
| Found crossbows | attack | as the bow | the weapon's own | the weapon's tier and quality | `AS_Warrior3_W5_Shoot` | `P_RDM3_BoltTrail`, `P_Impact` |
| Shield block | right mouse or LB held, with a shield in her hand | the shield takes its share of a blow + 30 %; she walks only ahead (90 cm/s) or back (72), turns at 120 °/s, cannot swing; the shield wears 5 times as fast | +30 % | the shield's own share (found shields) | `AS_Warrior3_BlockLunge`, held as an upper-body layer over her walk | none |
| Slashes | put on a weapon | a boss's reward: one of its tier (only the Warrior takes them). Its swing effect plays on every swing and its bonus and effect land with every hit | below | a better slash from a deeper tier | (the weapon's) | `NS_Slash_<x>` on the swing, `NS_SlashImpact_<x>` on the hit |

**The slashes** (`Slashes`, 4 a tier):

| Tier | Slash | Bonus a hit | Effect | Shares its effect with |
|---|---|---|---|---|
| 1 | Ember Slash | 6 fire | burns: 50 % more over 3 s | the Martial Artist's Smashing Strike (`NS_SlashImpact_Fire`) |
| 1 | Frost Slash | 5 frost | slows 25 % for 2 s | - |
| 1 | Venom Slash | 4 poison | poison: 12 over 4 s | - |
| 1 | Gale Slash | 5 physical | her speed +10 % for 4 s after a hit | Straight Punch (`NS_SlashImpact_Wind`) |
| 2 | Blood Slash | 9 blood | 30 % of the damage back to her | - |
| 2 | Wave Slash | 9 water | pushes the monster 3 m | - |
| 2 | Verdant Slash | 8 nature | 1.5 hit points a second for 5 s | - |
| 2 | Petal Slash | 8 physical | 15 % of blows on her miss for 3 s | - |
| 3 | Crystal Slash | 14 crystal | absorbs her next blow taken (once every 6 s) | - |
| 3 | Storm Slash | 15 lightning | chains to 2 more monsters within 5 m at half damage | Side Kick (`NS_SlashImpact_Lightning`); Spinning Kick and Heaven's Gale (`NS_Slash_Lightning` on her leg) |
| 3 | Ink Slash | 13 dark | blinds: 40 % of the monster's blows miss for 3 s | Roundhouse Kick (`NS_SlashImpact_Ink`) |
| 3 | Tide Slash | 14 water | sweeps an arc: slows 20 % and pushes 4 m | - |
| 4 | Inferno Slash | 24 fire | explodes within 2.5 m, burns 40 % more over 4 s | - |
| 4 | Shadow Slash | 22 shadow | ignores armour; the monster takes 25 % more for 5 s | - |
| 4 | Neon Slash | 20 arcane | her attack speed +20 % for 5 s | - |
| 4 | Pulse Slash | 20 energy | 25 % of blows on her turned back on the attacker for 4 s | - |
| 5 | Magma Slash | 36 fire | burning ground 3 m round, 10 a second for 4 s | - |
| 5 | Void Slash | 34 void | pulls monsters within 5 m to the target and slows them 25 % | Chain Punch and Crashing Wave (`NS_SlashImpact_Cosmic`) |
| 5 | Overload Slash | 38 energy | stuns the monster 1 s (once every 8 s a monster) | - |
| 5 | Prismatic Slash | 32 all | each hit adds a random effect: burn, slow, poison or drain | - |

### Secondary abilities

The Warrior's six have no cooldown change by rank; only their strength grows. Reach and cooldown are ours (the user's list gave none).

| Ability | Kind | Rank 1 → 6 | Cooldown (s) | Reach | What it does in the game |
|---|---|---|---|---|---|
| Shield Bash | active | stun 5 / 6 / 7 / 8 / 9 / 10 s | 14 | 3.5 m, 60 ° either side of her front | stuns every monster she can see within reach in front of her |
| Grapple | active | hold 5 → 10 s | 12 | 2.5 m | slows the monster before her to a stop: it still turns and strikes |
| Trip | active | prone 5 → 10 s | 12 | 2.5 m | stuns the monster before her: no move, no blow |
| Blinding Strike | active | blind 5 → 10 s | 12 | 2.5 m | her drawn weapon's damage (none with a bow or crossbow drawn) and every blow of the monster misses |
| Sweeping Push | active | 20 / 21 / 22 / 23 / 24 / 25 m | 16 | 4 m all round | pushes every monster she can see within reach that far, swept (walls stop it); stunned while it flies |
| Pulling Attack | active | 40 / 41 / 42 / 43 / 44 / 45 m | 12 | its own length, 25 ° either side | pulls one monster from up to that far into her reach; stunned while it flies |

---

## Mage

She fights from afar with spells and learns every type from tomes.

### Primary abilities

| Ability | Use | What it does | Base numbers | Grows by | Clips | Effects |
|---|---|---|---|---|---|---|
| Fire (Fire Bolt) | attack | a seeking fire bolt; half its damage to others within 1.7 m of the burst | 25, 8 mana, 14 m | spell growth: 25 / 37 / 65 / 357 at tiers 1 / 5 / 10 / 25 | `AS_Caster_Cast1`, `2`, `3` in turn | `NS_Muzzle_Fireball01` (hand), `NS_Projectile_Fireball01` (bolt), `NS_Hit_Fireball01` (burst) |
| Dark Fire | attack | a seeking bolt of black flame that also burns for 60 % more over 4 s and gives 30 % of the burn back to her | 38, 14 mana, 14 m | spell growth: 38 / 56 / 99 / 543 | the same three as Fire | `NS_Muzzle_Orb02`, `NS_Projectile_Orb02`, `NS_Hit_Orb02` |
| Tome spells | learned from a tome, then cast like a weapon | any of the 30 spells of [the spell table](#the-spell-table), every type | the spell's | spell growth; Spell Boost (her secondary) | the same three cast clips as Fire, for every one of them | the spell's own |
| Scrolls | read from the inventory | casts a spell once, at no mana (all four types) | the spell's | spell growth | the same three cast clips | the spell's own |

### Secondary abilities

| Ability | Kind | Rank 1 → 6 | Cooldown (s), rank 1 → 6 | What it does in the game |
|---|---|---|---|---|
| Mana Swarm | active | one light for every 20 / 18 / 16 / 14 / 12 / 10 mana she has | 15 / 13 / 11 / 9 / 7 / 6 | spends that mana on seeking lights at one monster within 20 m before her, one every 0.07 s; each does 0.34 of her first spell's blow (so it grows with her) |
| Mana Recharge Shield | active | 5 / 10 / 15 / 20 / 25 / 30 s | 15 → 6 | each blow that reaches her becomes mana instead |
| Ablation Shield | active | 1 / 2 / 3 / 4 / 5 / 6 layers for 5 → 30 s | 15 → 6 | each blow peels a layer and strikes its maker for the blow's whole damage |
| Misty Step | active | 10 / 15 / 20 / 25 / 30 / 35 m | 15 → 6 | teleports her to the floor farthest from her foes, in sight of where she stood (16 ways, down to a fifth of its length) |
| Spell Boost | passive | x 1.2 / 1.3 / 1.4 / 1.5 / 1.6 / 1.7 | - | one spell she chooses at rank 1 does that much more damage |
| Second Spell Boost | passive | x 1.2 → 1.7 | - | a second spell, not the first one's |

---

## Warlock

A sword in one hand and fire in the other; she learns offense and curse spells only.

### Primary abilities

| Ability | Use | What it does | Base numbers | Grows by | Clips | Effects |
|---|---|---|---|---|---|---|
| Sword (arming sword) | attack | melee blows | 22, reach 1.7 m | her own weapon growth: 22 / 48 / 85 / 467 at tiers 1 / 5 / 10 / 25 | `AS_DarkCaster_Slash1`, `2`, `3` | none |
| Fire | right mouse or E (the pad's LB), with the sword still drawn | a seeking fire bolt from her left hand | 25, 10 mana, 14 m | spell growth: 25 / 45 / 79 / 434 | `AS_DarkCaster_CastL1`, `L2` | the same three as the Mage's Fire |
| Found melee weapons (daggers, short, one-handed, curved and two-handed swords) | attack | melee blows | the weapon's own | the weapon's tier and quality | the same three as her sword, for every type | none |
| Found bows / crossbows | attack | a straight bolt | the weapon's own | the weapon's tier and quality | `AS_DarkCaster_W5_Bow` / `AS_DarkCaster_W5_Shoot` | `P_RDM3_BoltTrail`, `P_Impact` |
| Tome spells | learned from a tome | the offense and curse spells of [the spell table](#the-spell-table) (18 of the 30 tome spells) | the spell's | spell growth | her fire's two clips (`CastL1`, `L2`) for every one | the spell's own |
| Scrolls | read | an offense or curse spell, once | the spell's | spell growth | the same two | the spell's own |

### Secondary abilities

| Ability | Kind | Rank 1 → 6 | Cooldown (s), rank 1 → 6 | What it does in the game |
|---|---|---|---|---|
| Mana Shield | active | 5 / 10 / 15 / 20 / 25 / 30 s | 15 / 13 / 11 / 9 / 7 / 6 | her mana takes blows instead of her, point for point |
| Curse Shield | active | 5 → 30 s | 15 → 6 | every monster she can see within 2 m is cursed twice a second: it takes 25 % more and strikes for less |
| Blinding Shield | active | 5 → 30 s | 15 → 6 | every monster within 2 m is blinded: its blows miss |
| Misty Transfer | active | 40 / 50 / 60 / 70 / 80 / 90 m | 15 → 6 | sends the monster before her (within 15 m) to the floor farthest from her, in sight of where it stood; it is stunned 0.6 s |
| Bleeding Shield | active | 5 → 30 s | 15 → 6 | every monster within 2 m bleeds 6 a second, times her spell growth |
| Mana Blade | toggle | x 2.0 / 2.4 / 2.8 / 3.2 / 3.6 / 4.0 | - | while on, each melee blow that lands takes 6 mana and does that many times 6 more damage (12 to 24) |

---

## Rogue

Stealth, daggers and the crossbow. She has no secondary abilities: the user's list named none for her.

### Primary abilities

| Ability | Use | What it does | Base numbers | Grows by | Clips | Effects |
|---|---|---|---|---|---|---|
| Daggers (two) | attack | melee stabs | 13, reach 1.5 m | her own weapon growth: 13 / 17.2 / 30 / 166 at tiers 1 / 5 / 10 / 25 | `AS_Rogue_Stab1`, `2`, `3` | none |
| Crossbow | attack | a bolt that flies straight at the monster she faces and sticks in walls | 26 (33.8 with her +30 %), 26 m | her own weapon growth: 33.8 / 44.6 / 79 / 430 | `AS_Rogue_Shoot` | `P_RDM3_BoltTrail`, `P_Impact`; the bolt is a mesh (`SM_Arrow_Var1`) |
| Stealth | Q, LB or its quick slot | unseen by monsters and traps for 8 s, for 40 of her 100 dexterity energy (1.5 back a second, none while hidden). Her first blow or bolt out of it does +75 % and ends it. Pressed again: out of it. A speed potion fills the energy. | 8 s, 40 energy, +75 % | does not grow | none | Shadow Veil's dark aura (`NS_Shield_Shadow_01`) round her |
| Uncanny dodge | B | a roll 4.2 m along the way she pushes (backward roll for a way behind her). Blows are meant to miss her during it, but on these maps its window reads 1 to 1 of the roll: see [Things worth knowing](#things-worth-knowing) | 4.2 m, 0.25 s between | does not grow | `AS_Rogue_RollF`, `AS_Rogue_RollB` | none |
| Found daggers | attack | melee | the weapon's own | the weapon's tier and quality | the same three stabs | none |
| Found bows / crossbows | attack | a straight bolt, +30 % | the weapon's own | the weapon's tier and quality | `AS_Rogue_W5_Bow` / `AS_Rogue_Shoot` | `P_RDM3_BoltTrail`, `P_Impact` |

**Earned after Mistward** (a later dungeon's tier-5 boss each; they grow with her own weapon growth and take her +30 % on bolts):

| Earned in | Ability | Copy of | Base damage | What changes | Clips | Effects |
|---|---|---|---|---|---|---|
| Vel Morrath | Barbed Bolt | Crossbow | 37.7 (x 1.45) | damage only | `AS_Rogue_Shoot` | the crossbow's |
| The War Engine | Incendiary Bolt | Crossbow | 44.2 (x 1.7) | bursts: half damage within 2.2 m | `AS_Rogue_Shoot` | `P_RDM3_BoltTrail`, burst `NS_GroundExplosion_09` (the summons' arrival burst) |
| The Sewers | Shadow Fangs | Daggers | 26 (x 2.0) | reach 1.7 m | the three stabs | none |
| Kethrys Spire | Storm Bolt | Crossbow | 59.8 (x 2.3) | bursts: half damage within 3.2 m | `AS_Rogue_Shoot` | bolt `NS_Projectile_Lightning01` (Chain Lightning's), `P_Impact` |
| Heaven | Death's Kiss | Daggers | 36.4 (x 2.8) | reach 1.8 m | the three stabs | none |

---

## Martial Artist

Fists, feet and chi. Her chi attacks are spells: they cost mana, take her spell growth, and a Dexterity ring does not add to them.

### Primary abilities

| Ability | Use | What it does | Base numbers | Grows by | Clips | Effects |
|---|---|---|---|---|---|---|
| Fists and feet | attack | melee blows | 44, reach 1.6 m | her own weapon growth: 44 / 65 / 115 / 628 at tiers 1 / 5 / 10 / 25; a Dexterity ring adds | `AS_MartialArtist_Box_01`, `AS_MartialArtist_Front_kick_02` | none |
| Chi attacks (below) | attack, once drawn | a strike that bursts on the nearest monster within 4 m: that monster takes the damage, others within the burst's radius half. Refused with no monster within 4 m. | damage = 23 x (mana / 7) ^ 0.75 | spell growth (x 1.48 at tier 5, 2.61 at 10, 14.28 at 25) | one clip each (below) | effects on her limbs while it plays, and a burst |
| Dash | V or right mouse (the pad's RT) | a dash of 5 m forward into a strike; looks for a monster up to 9 m ahead | 5 m, 0.8 s between | does not grow | `AS_MartialArtist_Dash` | none |
| Dodge | B | a roll, as the Rogue's (with the same dodge window) | 4.2 m | does not grow | `AS_MartialArtist_RollF`, `AS_MartialArtist_RollB` | none |
| Found knives and daggers | attack | melee, +30 % (her "short blades"), and a Dexterity ring adds | the weapon's own | the weapon's tier and quality | `AS_MartialArtist_Stab1`, `2`, `3` | none |

**Her chi attacks.** She starts with the first two and unlocks two more each time she kills a tier's boss, in this order:

| Unlocked | Chi attack | Mana | Base damage | Burst (m) | Clip | Effects on her | Burst effect |
|---|---|---|---|---|---|---|---|
| start | Straight Punch | 7 | 23 | 1.2 | `AS_MartialArtist_Chi_StraightPunch` | right hand: `NS_Shield_Wind_01`, `NS_Projectile_Wind01`, `NS_Muzzle_Wind01` | `NS_SlashImpact_Wind` |
| start | Side Kick | 17 | 45 | 1.2 | `AS_MartialArtist_Chi_SideKick` | right calf and foot: `NS_Projectile_Lightning01`, `NS_Muzzle_Lightning01` | `NS_SlashImpact_Lightning` |
| 1st tier boss | Smashing Strike | 27 | 63 | 1.6 | `AS_MartialArtist_Chi_SmashingStrike` | both hands: `NS_Shield_Fire_01` | `NS_SlashImpact_Fire` |
| 1st tier boss | Roundhouse Kick | 37 | 80 | 1.6 | `AS_MartialArtist_Chi_RoundhouseKick` | right calf and foot: `NS_Shield_Ink_01` | `NS_SlashImpact_Ink` |
| 2nd tier boss | Chain Punch | 47 | 96 | 2.0 | `AS_MartialArtist_Chi_ChainPunch` | right hand: `NS_SlashImpact_Cosmic` (at each punch) | `NS_SlashImpact_Cosmic` |
| 2nd tier boss | Rear Kick | 57 | 111 | 2.0 | `AS_MartialArtist_Chi_RearKick` | right thigh, calf, foot: `NS_LootDrop08_lvl3_blue` | `NS_Hit_RotatingSpheres_V1` |
| 3rd tier boss | Piercing Palm | 67 | 125 | 2.5 | `AS_MartialArtist_Chi_PiercingPalm` | both hands: `NS_Projectile_Rod_V1`, `NS_Muzzle_Rod` | rods fly: `NS_Projectile_Rod_V1`, burst `NS_Hit_Rod_V1` |
| 3rd tier boss | Axe Kick | 68 | 127 | 2.5 | `AS_MartialArtist_Chi_AxeKick` | right foot: `NS_Hit_Fireworks01` | `NS_Hit_Fireworks01` |
| 4th tier boss | Meteor Fist | 78 | 140 | 3.0 | `AS_MartialArtist_Chi_MeteorFist` | right hand: `NS_Projectile_Fireball01` | `NS_Hit_Fireball01` |
| 4th tier boss | Spinning Kick | 88 | 154 | 3.0 | `AS_MartialArtist_Chi_SpinningKick` | right thigh, calf, foot: `NS_Projectile_Lightning01`, `NS_Shield_Lightning_01`, `NS_Slash_Lightning` | `NS_Hit_Lightning01` |

**Earned after Mistward** (each a copy of a chi attack: the same mana, clip and effects, more damage):

| Earned in | Ability | Copy of | Mana | Base damage |
|---|---|---|---|---|
| Vel Morrath | Crashing Wave | Chain Punch | 47 | 192 (x 2.0) |
| The War Engine | Thunder Step | Axe Kick | 68 | 279 (x 2.2) |
| The Sewers | Dragon Palm | Piercing Palm | 67 | 313 (x 2.5) |
| Kethrys Spire | Comet Fist | Meteor Fist | 78 | 364 (x 2.6) |
| Heaven | Heaven's Gale | Spinning Kick | 88 | 447 (x 2.9) |

### Secondary abilities

| Ability | Kind | Rank 1 → 6 | Cooldown (s) | What it does in the game |
|---|---|---|---|---|
| Wall Run | active | a leap of up to 10 / 20 / 30 / 40 / 50 / 60 m | 8 | launches her to the farthest floor along her way within its length, up to half its length higher, with the arc clear |
| Flash Steps | active | a dash of up to 10 → 60 m | 8 | carries her straight ahead through monsters; only walls stop it |
| Water Walk | active | up to 10 → 60 m | 10 | only in the wilds: from water within 8 m before her she runs on its face for that length; off it she falls in |
| Parry | active | 5 / 10 / 15 / 20 / 25 / 30 s | 15 / 13 / 11 / 9 / 7 / 6 | every blow from in front of her is turned aside and its maker stunned 1.5 s |
| Iron Skin | active | 10 / 20 / 30 / 40 / 50 / 60 % weaker for 8 s | 20 | every blow that reaches her is that much weaker (at most 90 %) |

Not the same as the Mage's tome spell **Iron Skin** (40 % for 12 s, its own rock shield effect): two abilities share the name.

---

## Summoner

Her summons fight for her; her own spells are the Mage's first two.

### Primary abilities

| Ability | Use | What it does | Base numbers | Grows by | Clips | Effects |
|---|---|---|---|---|---|---|
| Fire | attack | as the Mage's | 25, 8 mana | spell growth: 25 / 40 / 70 / 386 at tiers 1 / 5 / 10 / 25 | `AS_Summoner4_CastBolt` | the Mage's Fire's three |
| Dark Fire | attack | as the Mage's (burn and drain) | 38, 14 mana | spell growth: 38 / 61 / 107 / 587 | `AS_Summoner4_CastBolt` | the Mage's Dark Fire's three |
| Summonings (below) | cast | calls a monster that fights at her side until it falls; she leads at most the summoning's number of each | half her mana pool a cast | the open tier (see [How abilities grow](#how-abilities-grow)); her secondaries | `AS_Summoner4_Summon1` to `Summon5` | `NS_Muzzle_Sun01` (hand), `NS_Explosion_05_Anticipation` and `NS_GroundExplosion_09` where it arrives |
| Found daggers | attack | melee (never enchanted) | the weapon's own | the weapon's tier and quality | `AS_Summoner4_Stab1`, `2`, `3` | none |
| Scrolls | read | a spell once (all four types) | the spell's | spell growth | `AS_Summoner4_CastBolt` | the spell's own |

She learns no tome spells on the castle (her `Learns` is empty there); she reads every type of scroll.

**Her summonings.** She starts with the first and unlocks the next each time she kills a tier's boss; the later five come from the later dungeons' tier-5 bosses.

| Summoning | Unlocked | Monster | At most | Strength factor | Clip |
|---|---|---|---|---|---|
| Summon Tier 1 | start | Rotting Soldier | 2 | 0.80 | `AS_Summoner4_Summon1` |
| Summon Tier 2 | 1st tier boss | Grave Gunner | 3 | 0.85 | `AS_Summoner4_Summon2` |
| Summon Tier 3 | 2nd tier boss | Orc Skirmisher | 4 | 0.90 | `AS_Summoner4_Summon3` |
| Summon Tier 4 | 3rd tier boss | Alien Defender | 5 | 0.95 | `AS_Summoner4_Summon4` |
| Summon Tier 5 | 4th tier boss | Giant Spider | 3 | 1.00 | `AS_Summoner4_Summon5` |
| Summon Tier 6 | Vel Morrath | Iron Golem | 3 | 1.04 | `AS_Summoner4_Summon5` |
| Summon Tier 7 | The War Engine | Cyber Soldier | 4 | 1.08 | `AS_Summoner4_Summon5` |
| Summon Tier 8 | The Sewers | Captain of the Tide | 3 | 1.12 | `AS_Summoner4_Summon5` |
| Summon Tier 9 | Kethrys Spire | Lich of the Black Tower | 3 | 1.16 | `AS_Summoner4_Summon5` |
| Summon Tier 10 | Heaven | Kratos Field Commander | 3 | 1.20 | `AS_Summoner4_Summon5` |

A summon has the open tier's monster hit points and blows times its factor (a tier-1 Soldier at tier 1: 40 hit points, 9 a blow; a tier-5 Spider at tier 5: 340 and 55), and it grows when a new tier opens. Summon Tier 5's line in the game says "5 at most", but its number is 3 (cut by `880`'s balance of 2026-11-06).

### Secondary abilities

| Ability | Kind | Rank 1 → 6 | Cooldown (s) | What it does in the game |
|---|---|---|---|---|
| Minion Health | passive | x 1.2 / 1.3 / 1.4 / 1.5 / 1.6 / 1.7 | - | her summons' hit points |
| Minion Damage | passive | x 1.2 → 1.7 | - | her summons' blows |
| Summon Healing | active | 10 / 20 / 30 / 40 / 50 / 60 % | 20 | heals each summon by that share of its hit points |
| Frenzy | passive | x 1.2 → 1.7 | - | her summons strike that much more often (their wait between blows divided) |
| Soul Harvest | passive | heals 10 → 60 %, blows x 1.2 → 1.7 for 10 s | - | each monster dying within 25 m of her heals her summons and strengthens their blows |

---

## The spell table

The tome spells, plus the two every caster starts with. A tome found in a dungeon's tier teaches the spell of that tier's place. The Mage learns every type; the Warlock offense and curse (18 of the 30 tome spells). Mana, cooldown, damage, duration and radius are the table's base numbers; the caster's spell growth multiplies the damage. Every spell a hero learns is cast with her own cast clips (the Mage's `AS_Caster_Cast1` to `3`, the Warlock's `AS_DarkCaster_CastL1` and `L2`, the Summoner's `AS_Summoner4_CastBolt` for scrolls): no spell has a clip of its own.

| Tome found in | Spell | Type | Kind | Mana | Cooldown (s) | Damage | Lasts (s) | Radius (m) | The game's line | Effects (cast · bolt · impact · area · shield) |
|---|---|---|---|---|---|---|---|---|---|---|
| start | Fire Bolt | Offense | Bolt | 7 | 0 | 23 | - | - | Fast single fire projectile | `NS_Muzzle_Fireball01` · `NS_Projectile_Fireball01` · `NS_Hit_Fireball01` |
| start | Dark Fire | Offense | Bolt | 12 | 0 | 34 | 4 | - | Black flames that burn and drain life over time | `NS_Muzzle_Orb02` · `NS_Projectile_Orb02` · `NS_Hit_Orb02` |
| Mistward 1 | Frost Shard | Offense | Bolt | 14 | 0 | 31 | 2 | - | Piercing ice projectile that slows (40 %) | `NS_Muzzle_Icicle01` · `NS_Projectile_Icicle01` · `NS_Hit_Icicle01` |
| Mistward 2 | Ash Ward | Protection | Ward | 15 | 10 | - | 8 | - | Small barrier that absorbs a few hits (3) | `NS_Shield_Fire_01` |
| Mistward 3 | Shadow Lash | Offense | Lash | 18 | 2 | 46 | - | 1.5 | Whip of darkness that strikes an arc and knocks back | `NS_Muzzle_Slash01` · `NS_Hit_Slash01` |
| Mistward 4 | Bone Spear | Offense | Bolt | 20 | 0 | 50 | - | - | Bone spear that pierces a line of enemies | `NS_Muzzle_Arrow05` · `NS_Projectile_Arrow05` · `NS_Hit_Arrow05` |
| Mistward 5 | Iron Skin | Protection | Skin | 22 | 15 | - | 12 | - | Hardens flesh for a large armor bonus (40 % off blows) | `NS_Shield_Rock_01` |
| Vel Morrath 1 | Life Drain | Offense | Drain | 24 | 3 | 19 | 3 | - | Channeled beam that steals health (60 %) | `NS_Muzzle_Ghostly01` · `NS_Projectile_Ghostly01` · `NS_Hit_Ghostly01` |
| Vel Morrath 2 | Dispel Hex | Protection | Dispel | 25 | 12 | - | 3 | - | Cleanses curses, poisons and other debuffs | `NS_Hit_Wind01` · `NS_Shield_Water_01` |
| Vel Morrath 3 | Blood Nova | Offense | Nova | 28 | 8 | 64 | - | 5 | Spends your health (15 %) to release a ring of blood magic | `NS_Hit_ExplosiveBullet` · `NS_Shield_Blood_01` |
| Vel Morrath 4 | Chain Lightning | Offense | Bolt | 30 | 0 | 68 | - | 7 | Lightning that jumps between enemies (4) | `NS_Muzzle_Lightning01` · `NS_Projectile_Lightning01` · `NS_Hit_Lightning01` |
| Vel Morrath 5 | Bone Armor | Protection | Ward | 35 | 20 | - | 15 | - | Orbiting bones that each absorb one hit (5) | `NS_Hit_RotatingSpheres_V4` · `NS_Shield_Ink_01` |
| War Engine 1 | Plague Cloud | Offense | Cloud | 38 | 6 | 13.5 | 6 | 3.5 | Lingering toxic mist that poisons an area | `NS_Muzzle_PoisonDart01` · `NS_Hit_PoisonDart01` (impact and area) |
| War Engine 2 | Shadow Veil | Protection | Veil | 40 | 25 | - | 4 | - | Brief invisibility and high evasion (75 %) | `NS_SmokePuff_02` · `NS_Shield_Shadow_01` |
| War Engine 3 | Curse of Frailty | Curse | Curse | 42 | 10 | - | 8 | 5 | Enemies in an area take more damage (35 %) and hit weaker | `NS_Muzzle_Spiral01` · `NS_Hit_Spiral01` (impact and area) |
| War Engine 4 | Fireball | Offense | Bolt | 45 | 4 | 91 | - | 3.5 | Exploding sphere of heavy area fire damage | `NS_Muzzle_Sun01` · `NS_Projectile_Sun01` · `NS_ExplosionFire_01` |
| War Engine 5 | Raise Dead | Summon | Raise | 55 | 20 | - | 30 | - | Reanimates fallen enemies (3) as temporary minions | `NS_Muzzle_YinYang01` · `NS_Hit_YinYang01` · `NS_GroundExplosion_07` |
| Sewers 1 | Rune of Warding | Protection | Rune | 60 | 30 | - | 10 | 4 | Glyph on the ground that cuts damage taken (50 %) by allies inside it | `NS_Muzzle_Sun01` · `NS_Shield_Light_01` |
| Sewers 2 | Soul Rend | Offense | Bolt | 65 | 6 | 121 | - | - | Spirit damage that ignores armor | `NS_Muzzle_Ghostly01` · `NS_Projectile_Ghostly01` · `NS_Hit_Ghostly01` |
| Sewers 3 | Mirror of Retribution | Protection | Mirror | 70 | 35 | - | 5 | - | Reflects projectiles and spells back at attackers | `NS_Muzzle_Shard_V1` · `NS_Shield_Cyber_02` |
| Sewers 4 | Corpse Explosion | Offense | Corpse | 75 | 3 | 134 | - | 4 | Detonates corpses (4) for massive area damage | `NS_BigExplosion_01` |
| Sewers 5 | Blizzard | Offense | Cloud | 80 | 12 | 17.6 | 8 | 5 | Sustained ice storm over a wide area (slows 50 %) | `NS_Muzzle_Arrow03` (cast and area) · `NS_Hit_Shard_V1` |
| Kethrys Spire 1 | Spectral Bulwark | Protection | Ward | 100 | 60 | - | 10 | - | Huge shield that absorbs damage for the whole party | `NS_Shield_Wind_01` |
| Kethrys Spire 2 | Hellfire Pillar | Offense | Pillar | 110 | 15 | 179 | 6 | 3.5 | Column of infernal flame that leaves burning ground | `NS_UpwardFire_01` · `NS_SmallFire_01` |
| Kethrys Spire 3 | Void Rift | Offense | Rift | 120 | 20 | 47.5 | 4 | 6 | Tear in reality that pulls enemies in and crushes them | `NS_GroundExplosion_10` · `NS_Muzzle_Wind01` |
| Kethrys Spire 4 | Undying Pact | Protection | Pact | 150 | 180 | - | 60 | - | Cheats death once, reviving you at partial health (40 %) | `NS_Shield_Blood_01` · `NS_Hit_ShootingStar01` · `NS_Shield_Cosmic_01` |
| Kethrys Spire 5 | Summon Abyssal Knight | Summon | Knight | 160 | 90 | - | - | - | Permanent demonic or undead champion | `NS_Muzzle_Sun01` · `NS_Explosion_05_Anticipation` · `NS_GroundExplosion_09` |
| Heaven 1 | Meteor Storm | Offense | Meteors | 200 | 45 | 98 | 5 | 6 | Burning meteors (12) rain across the battlefield | `NS_Projectile_Rock_V1` · `NS_GroundExplosion_04` |
| Heaven 2 | Null Sanctum | Protection | Sanctum | 220 | 120 | - | 4 | 4 | Zone where allies are briefly immune to all damage | `NS_Shield_Holy_01` |
| Heaven 3 | Apocalypse | Offense | Apocalypse | 300 | 300 | 380 | - | - | Ultimate that devastates every enemy on screen (25 m) | `NS_ExplosionAir_05_Anticipation` · `NS_Nuke_03` · `NS_Explosion_07` |
| Heaven 4 | Starfall | Offense | Meteors | 240 | 45 | 147 | 5 | 6 | Meteor Storm's, x 1.2 mana and x 1.5 damage | Meteor Storm's |
| Heaven 5 | Singularity | Offense | Rift | 144 | 20 | 76 | 4 | 6 | Void Rift's, x 1.2 mana and x 1.6 damage | Void Rift's |

The heroes' own Fire and Dark Fire are weapons with their own numbers (the Mage's Fire 25 for 8 mana, the Warlock's 25 for 10), which the table's Fire Bolt and Dark Fire lines only give their effects and their burn.

---

## What shares animations

Read from the clips each ability plays. No clip is shared between two heroes: each hero has her own rig and her own clips.

| Clip(s) | Played by |
|---|---|
| Warrior: `Anim_Weapon_Shield_Attack_01`, `_03`, `_08` | her dagger and every found one-handed weapon (daggers, short swords, one-handed, curved and eastern swords) |
| Warrior: `AS_Warrior3_Slash` | every found two-handed sword |
| Mage: `AS_Caster_Cast1`, `2`, `3` | Fire, Dark Fire, every tome spell and every scroll |
| Warlock: `AS_DarkCaster_Slash1`, `2`, `3` | her sword and every found melee weapon, two-handed swords included |
| Warlock: `AS_DarkCaster_CastL1`, `L2` | Fire, every tome spell and every scroll |
| Rogue: `AS_Rogue_Stab1`, `2`, `3` | her daggers, found daggers, Shadow Fangs, Death's Kiss |
| Rogue: `AS_Rogue_Shoot` | her crossbow, found crossbows, Barbed Bolt, Incendiary Bolt, Storm Bolt |
| Martial Artist: one `AS_MartialArtist_Chi_<name>` clip each | Chain Punch and Crashing Wave share one; Axe Kick and Thunder Step; Piercing Palm and Dragon Palm; Meteor Fist and Comet Fist; Spinning Kick and Heaven's Gale. The other five chi attacks have a clip of their own. |
| Summoner: `AS_Summoner4_CastBolt` | Fire, Dark Fire and every scroll |
| Summoner: `AS_Summoner4_Summon5` | Summon Tier 5 to Summon Tier 10 (Tier 1 to 4 have a clip each) |
| Rogue and Martial Artist | each has her own pair of roll clips (forward, back) for the dodge |
| **No clip at all** | every secondary ability (the Warrior's Shield Bash, Trip and Blinding Strike included: their effect lands at once, with no swing), the Rogue's stealth. A stunned, tripped, bashed or parried monster plays its own flinch clip. |

## What shares effects

Every visual effect (Niagara or Cascade system) used by more than one ability:

| Effect | Used by |
|---|---|
| `NS_Muzzle_Fireball01`, `NS_Projectile_Fireball01`, `NS_Hit_Fireball01` | Fire (Mage, Warlock, Summoner), Fire Bolt, the Mage's Mana Swarm (its lights are Fire Bolt's bolts); the last two also Meteor Fist and Comet Fist (the bolt on her fist, the hit as the burst) |
| `NS_Muzzle_Orb02`, `NS_Projectile_Orb02`, `NS_Hit_Orb02` | Dark Fire (Mage, Summoner) |
| `NS_Muzzle_Ghostly01`, `NS_Projectile_Ghostly01`, `NS_Hit_Ghostly01` | Life Drain, Soul Rend |
| `NS_Projectile_Lightning01` | Chain Lightning's bolt, the Rogue's Storm Bolt, the Martial Artist's Side Kick, Spinning Kick and Heaven's Gale (on her leg) |
| `NS_Muzzle_Lightning01` | Chain Lightning, Side Kick (on her foot) |
| `NS_Hit_Lightning01` | Chain Lightning, Spinning Kick, Heaven's Gale |
| `NS_Slash_Lightning` | Storm Slash's swing, Spinning Kick and Heaven's Gale (on her leg) |
| `NS_SlashImpact_Wind` | Gale Slash, Straight Punch |
| `NS_SlashImpact_Lightning` | Storm Slash, Side Kick |
| `NS_SlashImpact_Fire` | Ember Slash, Smashing Strike |
| `NS_SlashImpact_Ink` | Ink Slash, Roundhouse Kick |
| `NS_SlashImpact_Cosmic` | Void Slash, Chain Punch, Crashing Wave |
| `NS_Shield_Fire_01` | Ash Ward, Smashing Strike (on her hands) |
| `NS_Shield_Ink_01` | Bone Armor, Roundhouse Kick (on her leg) |
| `NS_Shield_Wind_01` | Spectral Bulwark, Straight Punch (on her hand) |
| `NS_Muzzle_Wind01` | Void Rift, Singularity, Straight Punch (on her hand) |
| `NS_Shield_Blood_01` | Blood Nova, Undying Pact |
| `NS_Shield_Shadow_01` | Shadow Veil, the Rogue's Stealth |
| `NS_Muzzle_Sun01` | Fireball, Rune of Warding, Summon Abyssal Knight, every Summon Tier |
| `NS_Explosion_05_Anticipation` | Summon Abyssal Knight, every Summon Tier |
| `NS_GroundExplosion_09` | Summon Abyssal Knight, every Summon Tier, the Rogue's Incendiary Bolt |
| `NS_Projectile_Rock_V1`, `NS_GroundExplosion_04` | Meteor Storm, Starfall |
| `NS_GroundExplosion_10` | Void Rift, Singularity |
| `NS_Projectile_Rod_V1`, `NS_Hit_Rod_V1`, `NS_Muzzle_Rod` | Piercing Palm, Dragon Palm |
| `NS_Hit_Fireworks01` | Axe Kick, Thunder Step |
| `P_RDM3_BoltTrail`, `P_Impact` | every crossbow and bow, of every hero; Barbed Bolt; Storm Bolt (its impact); Incendiary Bolt (its trail) |
| `NS_ExplosionsCircle_03` (the teleport effect) | Misty Step, Misty Transfer, the teleport rings and pads, the boss's teleporter |

Effects of one ability only: Frost Shard's icicles, Shadow Lash's slash, Bone Spear's arrow, Iron Skin's rock shield, Dispel Hex, Bone Armor's spheres, Plague Cloud, Curse of Frailty, Fireball's sun and explosion, Raise Dead, Rune of Warding's light shield, Mirror of Retribution, Corpse Explosion, Blizzard, Hellfire Pillar, Null Sanctum, Apocalypse, Rear Kick, Spinning Kick's lightning shield, and the slashes not named above.

**Secondary abilities show almost nothing.** Apart from Mana Swarm (Fire Bolt's look) and the two misty moves (the teleport effect), none has an effect: a shield or mode is shown only by the green frame on its quick-bar slot, a cooldown by the slot going dark.

## Things worth knowing

- **Two abilities called Iron Skin:** the Mage's tome spell (40 % off blows for 12 s, a rock shield on her) and the Martial Artist's secondary (10 to 60 % for 8 s, no effect).
- **Copies look the same as what they copy.** The Rogue's Barbed Bolt, Shadow Fangs and Death's Kiss, and the Martial Artist's five later chi attacks, have the clips and effects of the ability they copy; only their numbers differ. Incendiary Bolt and Storm Bolt have a burst or bolt of their own.
- **Summon Tier 5's line** says "5 at most"; it allows 3.
- **The Summoner learns no tomes on the castle**, though she reads scrolls of every type.
- **Blinding Strike** is described as "a blow of her weapon", but no swing plays: the damage and the blindness land at once.
- **The roll's dodge window is (1, 1) on every map past magic level 3.** A blow misses her only while her roll is between the window's two shares (`RollDodge`, `URDCombatComponent::IsDodging`). Magic level 3, where the roll was made, has 0.05 to 0.75; level 5, Mistward Castle, martial_arts, Brokenspire and Vel Morrath read 1 to 1, so the Rogue's and the Martial Artist's rolls move them but dodge nothing until the very end. `825` copies the value from level 3 to level 4; where it became (1, 1) was not traced (level 4 was not read). No test measures a blow missing her during a roll there (`868 quickbar` counts the roll only), and it was not checked in play.
