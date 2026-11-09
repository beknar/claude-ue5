# The secondary abilities

[README](../README.md) · [The tiers](tiers.md) · [Mistward Castle](levels/mistward_castle.md) · [The wilderness](levels/wilderness.md) · [TODO](../TODO.md)

This is the sixth phase of the user's list of 2026-11-08b ([docs/improvements9.txt](improvements9.txt)): "earned in the wilderness by gathering materials and making Angel Tokens".
- **Who has them:** the Warrior and the Mage have six each, as do the Warlock; the Summoner and the Martial Artist have five each. The Rogue has none, because the list names none for her.
- **Ranks:** each ability has six ranks. An Angel Token raises one ability one rank, and the first rank learns it.
- **Data and code:** the data is `claude_ue5/SourceArt/balance/secondary.json`, which stage `911` writes onto every map of the game. The game's side is `RD/RDSecondary.cpp`.

## Angel Tokens

- **What a token is made of:** three Seraph Feathers and a Hallowed Stone, at an anvil, in the town or in a dungeon.
- **Seraph Feathers:** the wilderness's monsters drop them, at 45 % a kill, as a pile where the monster fell.
- **Hallowed Stones:** one lies at each ruin, ritual site and cave of the wilds, near where the place stands. Once taken it never comes back (the game's `WildKilled`, saved).
- **Using a token:** used from the inventory, it opens a list of her hero's abilities with each one's rank and what the next rank gives. A spell boost's first rank then asks for one of the spells she knows; the second boost cannot take the first's spell.
- **Learning an active ability:** it goes on the quick bar's first free slot.
- **What she keeps:** her ranks travel with her between the town, the wilds and the dungeons, are saved, and stay through a death. A new game starts without them.

## The abilities

Active abilities are made from the quick bar (`@<Name>`: a number key, or made ready on the D-pad and then the attack button). A cooldown darkens the slot, and a green frame shows while a shield or mode is on her. A toggle goes on and off there. Passive abilities always hold once learned.

The table's numbers run from rank 1 to rank 6, as the list gives them. Where the list gives none, the numbers are ours, marked in the data (`ours`):
- the Warrior's cooldowns and reaches;
- the cooldowns of the Summoner's healing and of the Martial Artist's movements and iron skin;
- all of the Warlock's mana blade's numbers;
- iron skin's 8 s;
- the soul harvest's 10 s and 25 m;
- the ablation's blow back (the blow's own);
- the parry's stagger (1.5 s).

### Warrior

| Ability | Kind | What it does (rank 1 to 6) | Cooldown (s) |
|---|---|---|---|
| Shield Bash | active | stuns every enemy within reach in front of her for 5 to 10 s | 14 |
| Grapple | active | holds the enemy before her where it stands for 5 to 10 s (it still strikes) | 12 |
| Trip | active | throws the enemy before her prone for 5 to 10 s: it neither moves nor strikes | 12 |
| Blinding Strike | active | a blow of her weapon that blinds the enemy before her for 5 to 10 s (its blows miss) | 12 |
| Sweeping Push | active | pushes every enemy within reach 20 to 25 m away from her | 16 |
| Pulling Attack | active | pulls an enemy up to 40 to 45 m away before her into her reach | 12 |

### Mage

| Ability | Kind | What it does (rank 1 to 6) | Cooldown (s) |
|---|---|---|---|
| Mana Swarm | active | seeking points of light at one enemy: one for every 20 to 10 mana she has left, each a third of a fire bolt | 15 to 6 |
| Mana Recharge Shield | active | for 5 to 30 s each blow that reaches her becomes mana instead of hurting her | 15 to 6 |
| Ablation Shield | active | for 5 to 30 s, 1 to 6 layers: each blow peels a layer away and strikes its maker back | 15 to 6 |
| Misty Step | active | steps up to 10 to 35 m away from her foes, to a safe place | 15 to 6 |
| Spell Boost | passive | one spell she chooses does 1.2 to 1.7 times its damage, for good | - |
| Second Spell Boost | passive | a second spell she chooses does 1.2 to 1.7 times its damage, for good | - |

### Warlock

| Ability | Kind | What it does (rank 1 to 6) | Cooldown (s) |
|---|---|---|---|
| Mana Shield | active | for 5 to 30 s her mana takes the blows instead of her, a point for a point | 15 to 6 |
| Curse Shield | active | for 5 to 30 s every enemy within 2 m of her is cursed (it takes 25% more and strikes for less) | 15 to 6 |
| Blinding Shield | active | for 5 to 30 s every enemy within 2 m of her is blinded (its blows miss) | 15 to 6 |
| Misty Transfer | active | sends the enemy before her 40 to 90 m away, elsewhere in the area | 15 to 6 |
| Bleeding Shield | active | for 5 to 30 s every enemy within 2 m of her bleeds 6 a second | 15 to 6 |
| Mana Blade | toggle | while on, each blow that lands takes 6 mana and does 2 to 4 times that more damage | - |

### Summoner

| Ability | Kind | What it does (rank 1 to 6) | Cooldown (s) |
|---|---|---|---|
| Minion Health | passive | her summons have 1.2 to 1.7 times their hit points | - |
| Minion Damage | passive | her summons strike 1.2 to 1.7 times as hard | - |
| Summon Healing | active | heals each of her summons by 10 to 60% of its hit points | 20 |
| Frenzy | passive | her summons strike 1.2 to 1.7 times as often | - |
| Soul Harvest | passive | each enemy dying near her heals her summons by 10 to 60% and makes their blows 1.2 to 1.7 times as hard for 10 s | - |

### Martial Artist

| Ability | Kind | What it does (rank 1 to 6) | Cooldown (s) |
|---|---|---|---|
| Wall Run | active | a leap of up to 10 to 60 m: up walls and across gaps without climbing gear | 8 |
| Flash Steps | active | a dash of up to 10 to 60 m that passes through enemies | 8 |
| Water Walk | active | runs across water for up to 10 to 60 m | 10 |
| Parry | active | for 5 to 30 s each blow from in front of her is turned aside and staggers its maker | 15 to 6 |
| Iron Skin | active | for 8 s every blow that reaches her is 10 to 60% weaker | 20 |

How each one works in the game:
- **Blocking a blow:** the shields and modes take a blow before her ward, armour and shield do. The order is parry, then ablation, then recharge, then mana shield, then iron skin. A blow taken whole brings no poison, weakness or slowness with it.
- **Through walls:** the abilities that reach all around her (the bash, the push, the Warlock's shields) take only monsters she can see.
- **Grapple:** it slows the monster to a stop, so it still turns and strikes. Trip stuns it: no move and no blow.
- **The push and the pull:** both move the monster tick by tick and are swept, so walls stop them.
- **The mana swarm:** its lights are Fire Bolt's bolts aimed at the target, one every 0.07 s. Each light does a third of her first spell's blow, so it grows with her.
- **Misty Step:** it picks, out of 16 ways and distances down to a fifth of its length, the floor farthest from her foes, in sight of where she stood. It never goes through a wall into a vault, a cell or past the arena's bars (PR #35's review).
- **Misty Transfer:** it picks the floor farthest from her, in sight of where the monster stood, so a hall gives less than its length.
- **The leap (Wall Run):** it lands on the farthest floor along her way within its length, up to half its length higher, with the arc clear. It is a launch, so she flies it.
- **Flash Steps:** it ignores pawns for its length, so only the walls stop it.
- **Water Walk:** only in the wilds. From the shore she runs onto the water within 8 m before her, and is held on its face for its length; off it, she falls in.
- **The parry:** it takes only blows from in front of her. The list's "perfectly timed" is the mode itself: no timing of a key is asked.
- **The Summoner's passives:**
  - Her summons' health and damage are part of their strength, and they grow with them.
  - Frenzy divides their wait between blows.
  - Soul harvest works for a death within 25 m of her.

## The tests

`868 secondary` runs on Mistward Castle (`test_sc4.json` after PR #35's review):
- **The token:** 3 feathers and a stone made a token at the anvil. Used, its list showed the Warrior's six, and Shield Bash became rank 1 and went on the quick bar; the token was used up.
- **Warrior:**
  - Shield Bash stunned two monsters in front of her, still at 4.7 s and over at 5.7 s, and a second use was refused.
  - Grapple held a monster (it was not stunned and did not move as she walked 6 m off).
  - Trip stunned it.
  - Blinding Strike hurt it and blinded it.
  - Sweeping Push pushed two monsters away as far as the room let them.
  - Pulling Attack pulled one from 15 m to under 3 m.
- **Mage:**
  - Mana Swarm sent five lights for her 100 mana, all of it spent; the monster lost 51, the five lights' worth.
  - Spell Boost made Fire Bolt 30 against 25.
  - The ablation's two layers took two blows and struck their maker for 40; the third blow hurt her.
  - The recharge turned a blow of 30 into 30 mana.
  - Misty Step took her 10 m from two monsters at 2 m to 11.6 m from the nearest.
- **Warlock:**
  - The mana shield took a blow of 20 from her mana.
  - The curse (25 %), blinding (100 %) and bleeding (11 in 2 s) shields worked on a monster within 2 m.
  - Misty Transfer sent a monster 16 m, as far as the great hall's sight lines let it.
  - The mana blade added 12 to a blow (22 to 34) for its 6 mana. The 3.5 mana read was less: her mana came back over the 2 s.
- **Summoner:** a Soldier called before the passives grew to 1.2 times its hit points and blow and 1.2 times its pace. Summon Healing healed 10 % of its hit points, and a kill near her healed it and boosted its blows 1.2 times for 10 s.
- **Martial Artist:**
  - The leap and Flash Steps moved her their planned lengths, the flash past a monster in her way.
  - Water Walk was refused in the castle (no water).
  - The parry took a blow from in front, staggered its maker and refused a second use.
  - Iron Skin made a blow 10 % weaker.

`888 secondary9` runs on Brokenspire (`-Light`, `test_sw3.json`):
- **The stone:** a Hallowed Stone at the Old Watchtower; F took it, and it was not laid again when its chunk was made again. The captain's patrol quest there still counted no kill (the stone's key is out of the places' kill range: PR #35's review). `quests` passes on its own (`test_sq1.json`); in one session after `secondary9` it fails, because that step killed the den's pack.
- **The feathers:** the Mill Road Den's four monsters dropped two Seraph Feathers.
- **Water Walk:** from a lake's shore the Martial Artist ran 10 m over the water, her feet 1 to 2 cm over its face the whole way.

The castle's steps the abilities touch still pass (`test_r26a.json`: `inventory`, `tabs`, `slots`, `death`, `martial`, `summoner`, `growth`, `shields`, `scrolls`, `recipes`), and so does `quickbar` on `martial_arts` (`test_r26b.json`).

## Rebuild

1. Build the C++ (`pipeline\build_cpp.ps1`).
2. Run `911_secondary.py` (all seven maps). Run it again after anything that writes the levels' items or recipes anew (`857`, `875`, `910`).